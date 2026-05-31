"""Translate a subset of Scryfall query syntax into SQL against `cards.sqlite`.

Supported operators are translated locally; **any** term the translator can't serve
(`function:`/`otag:` Tagger tags, `set:`, unknown fields, `include:`, etc.) makes the
whole query route to the live Scryfall API instead — guaranteeing we never silently
drop a constraint and return wrong results (docs/adr/0001).

Entry points:
    to_sql(query, order)  -> (sql, params) | None     # None => route to live API
    search(query, ...)    -> list[dict]                # DB-first, API fallback
    named(name, ...)      -> dict | None               # DB-first, API fallback
"""

import json
import os
import re
import sqlite3

from . import api
from .paths import default_db_path

SUPPORTED_FALLBACK = "function:/otag: and any unsupported operator route to the live Scryfall API"

WUBRG = "WUBRG"

# Guild / shard / wedge nicknames -> color letters.
NICKNAMES = {
    "colorless": "", "c": "",
    "white": "W", "blue": "U", "black": "B", "red": "R", "green": "G",
    "azorius": "WU", "dimir": "UB", "rakdos": "BR", "gruul": "RG", "selesnya": "GW",
    "orzhov": "WB", "izzet": "UR", "golgari": "BG", "boros": "RW", "simic": "GU",
    "bant": "GWU", "esper": "WUB", "grixis": "UBR", "jund": "BRG", "naya": "RGW",
    "abzan": "WBG", "jeskai": "URW", "sultai": "BGU", "mardu": "RWB", "temur": "GUR",
    "wubrg": "WUBRG", "five": "WUBRG", "rainbow": "WUBRG",
}
PERMANENT_TYPES = ("artifact", "creature", "enchantment", "land", "planeswalker", "battle")
RARITY_ABBR = {"c": "common", "u": "uncommon", "r": "rare", "m": "mythic"}
RARITY_RANK = {"common": 1, "uncommon": 2, "rare": 3, "mythic": 4, "special": 5, "bonus": 5}

# Columns selected for every DB query; row order matches _ROW_KEYS.
_SELECT = (
    "name, cmc, type_line, oracle_text, mana_cost, color_identity, colors, "
    "power, toughness, rarity, keywords, game_changer, edhrec_rank, legalities, "
    "scryfall_uri, min_eur, min_eur_foil, min_usd, min_usd_foil, arena, paper, mtgo, funny"
)
_ROW_KEYS = [
    "name", "mv", "type_line", "oracle_text", "mana_cost", "color_identity", "colors",
    "power", "toughness", "rarity", "keywords", "game_changer", "edhrec_rank", "legalities",
    "scryfall_uri", "eur", "eur_foil", "usd", "usd_foil", "arena", "paper", "mtgo", "funny",
]

_TERM_RE = re.compile(r"^(?P<field>[a-zA-Z]+)(?P<op><=|>=|!=|<|>|=|:)(?P<val>.*)$")


class Unsupported(Exception):
    """A term (or whole query) the local DB can't serve; route to the live API."""


# --------------------------------------------------------------------------- #
# Tokeniser + parser (recursive descent over implicit-AND / `or` / parens / -). #
# --------------------------------------------------------------------------- #

def _tokenize(q):
    tokens, cur, i, n = [], "", 0, len(q)
    while i < n:
        ch = q[i]
        if ch == '"':
            j = q.find('"', i + 1)
            if j == -1:
                cur += q[i:]
                break
            cur += q[i:j + 1]
            i = j + 1
            continue
        if ch in "() \t\n":
            if cur:
                tokens.append(cur)
                cur = ""
            if ch == "(":
                tokens.append("(")
            elif ch == ")":
                tokens.append(")")
            i += 1
            continue
        cur += ch
        i += 1
    if cur:
        tokens.append(cur)
    return tokens


class _Parser:
    def __init__(self, tokens, ctx):
        self.toks = tokens
        self.pos = 0
        self.ctx = ctx  # accumulates params + order hints

    def peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def next(self):
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def parse(self):
        frag = self.parse_or()
        if self.pos != len(self.toks):
            raise Unsupported("unbalanced query")
        return frag

    def parse_or(self):
        parts = [self.parse_and()]
        while self.peek() and self.peek().lower() == "or":
            self.next()
            parts.append(self.parse_and())
        parts = [p for p in parts if p]
        if not parts:
            return ""
        return "(" + " OR ".join(parts) + ")" if len(parts) > 1 else parts[0]

    def parse_and(self):
        parts = []
        while True:
            t = self.peek()
            if t is None or t == ")" or t.lower() == "or":
                break
            parts.append(self.parse_unary())
        parts = [p for p in parts if p]
        if not parts:
            return ""
        return "(" + " AND ".join(parts) + ")" if len(parts) > 1 else parts[0]

    def parse_unary(self):
        t = self.peek()
        if t == "-":  # lone '-'; apply to next
            self.next()
            return self._negate(self.parse_unary())
        if t == "(":
            self.next()
            frag = self.parse_or()
            if self.peek() != ")":
                raise Unsupported("missing )")
            self.next()
            return frag
        self.next()
        if t.startswith("-") and len(t) > 1:
            return self._negate(self._term(t[1:]))
        return self._term(t)

    @staticmethod
    def _negate(frag):
        return f"NOT ({frag})" if frag else ""

    def _term(self, tok):
        return _translate_term(tok, self.ctx)


# --------------------------------------------------------------------------- #
# Term translation                                                            #
# --------------------------------------------------------------------------- #

def _expand_identity(val):
    v = val.strip().lower().strip('"')
    if v in NICKNAMES:
        return set(NICKNAMES[v])
    letters = set(v.upper())
    if letters <= set(WUBRG + "C"):
        letters.discard("C")
        return letters
    raise Unsupported(f"unknown color spec {val!r}")


def _like_value(val):
    v = val.strip().strip('"')
    v = v.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{v.lower()}%"


def _like(col, val, params):
    params.append(_like_value(val))
    return f"COALESCE(lower({col}),'') LIKE ? ESCAPE '\\'"


def _num(val):
    try:
        return float(val.strip().strip('"'))
    except ValueError:
        raise Unsupported(f"non-numeric {val!r}")


_NUMOPS = {"<": "<", ">": ">", "<=": "<=", ">=": ">=", "=": "=", ":": "=", "!=": "!="}


def _translate_term(tok, ctx):
    params = ctx["params"]
    m = _TERM_RE.match(tok)
    if not m:
        # bareword -> name contains
        return _like("name", tok, params)
    field = m.group("field").lower()
    op = m.group("op")
    val = m.group("val")

    # ---- identity / color ------------------------------------------------- #
    if field in ("id", "identity"):
        if op in (":", "=") and val.lower().strip('"') in ("c", "colorless"):
            return "color_identity = ''"
        colors = _expand_identity(val)
        if op == "<=" or (op == ":" and field in ("id", "identity")):
            # subset: contains none of the disallowed colors
            disallowed = [c for c in WUBRG if c not in colors]
            return "(" + " AND ".join(f"instr(color_identity,'{c}')=0" for c in disallowed) + ")" if disallowed else "1=1"
        if op == ">=":
            return "(" + " AND ".join(f"instr(color_identity,'{c}')>0" for c in colors) + ")" if colors else "1=1"
        if op == "=":
            params.append("".join(s for s in WUBRG if s in colors))
            return "color_identity = ?"
        raise Unsupported(tok)

    if field in ("c", "color", "colors"):
        v = val.lower().strip('"')
        if v in ("c", "colorless"):
            return "colors = ''"
        if v in ("m", "multicolor"):
            return "length(colors) >= 2"
        colors = _expand_identity(val)
        if op == "<=":
            disallowed = [c for c in WUBRG if c not in colors]
            return "(" + " AND ".join(f"instr(colors,'{c}')=0" for c in disallowed) + ")" if disallowed else "1=1"
        # ':' and '>=' => contains all listed colors (Scryfall c: is "contains")
        return "(" + " AND ".join(f"instr(colors,'{c}')>0" for c in colors) + ")" if colors else "1=1"

    # ---- text ------------------------------------------------------------- #
    if field in ("o", "oracle", "fo"):
        return _like("oracle_text", val, params)
    if field in ("name", "n"):
        return _like("name", val, params)
    if field in ("kw", "keyword"):
        return _like("keywords", val, params)

    # ---- type ------------------------------------------------------------- #
    if field in ("t", "type"):
        v = val.lower().strip('"')
        if v == "permanent":
            return "(" + " OR ".join(f"lower(type_line) LIKE '%{p}%'" for p in PERMANENT_TYPES) + ")"
        if v == "spell":
            return "lower(type_line) NOT LIKE '%land%'"
        return _like("type_line", val, params)

    # ---- numeric ---------------------------------------------------------- #
    if field in ("mv", "cmc", "manavalue"):
        sqlop = _NUMOPS.get(op)
        if not sqlop:
            raise Unsupported(tok)
        params.append(_num(val))
        return f"cmc {sqlop} ?"
    if field in ("pow", "power", "tou", "toughness"):
        col = "power" if field in ("pow", "power") else "toughness"
        sqlop = _NUMOPS.get(op)
        if not sqlop:
            raise Unsupported(tok)
        params.append(_num(val))
        return f"({col} IS NOT NULL AND {col} != '' AND CAST({col} AS REAL) {sqlop} ?)"

    # ---- rarity ----------------------------------------------------------- #
    if field in ("r", "rarity"):
        v = val.lower().strip('"')
        v = RARITY_ABBR.get(v, v)
        if op in (":", "="):
            params.append(v)
            return "rarity = ?"
        rank = RARITY_RANK.get(v)
        sqlop = _NUMOPS.get(op)
        if rank is None or not sqlop:
            raise Unsupported(tok)
        params.append(rank)
        return f"rarity_rank {sqlop} ?"

    # ---- flags / availability / legality / price -------------------------- #
    if field in ("is", "has", "not"):
        v = val.lower().strip('"')
        frag = _is_flag(v, tok)
        return f"NOT ({frag})" if field == "not" else frag
    if field == "game":
        v = val.lower().strip('"')
        if v in ("arena", "paper", "mtgo"):
            return f"{v} = 1"
        raise Unsupported(tok)
    if field == "legal":
        fmt = val.lower().strip('"')
        params.append(f"$.{fmt}")
        return "json_extract(legalities, ?) IN ('legal','restricted')"
    if field in ("eur", "usd"):
        col = "min_eur" if field == "eur" else "min_usd"
        sqlop = _NUMOPS.get(op)
        if not sqlop:
            raise Unsupported(tok)
        params.append(_num(val))
        return f"({col} IS NOT NULL AND {col} {sqlop} ?)"

    # ---- ordering / non-filter hints -------------------------------------- #
    if field == "order":
        ctx["order"] = val.lower().strip('"')
        return ""
    if field in ("unique", "direction", "prefer"):
        return ""  # affects presentation only; ignore as a filter

    raise Unsupported(f"unsupported field {field!r}")


def _is_flag(v, tok):
    if v == "gamechanger":
        return "game_changer = 1"
    if v == "permanent":
        return "(" + " OR ".join(f"lower(type_line) LIKE '%{p}%'" for p in PERMANENT_TYPES) + ")"
    if v == "funny":
        return "funny = 1"
    raise Unsupported(tok)


_ORDER_SQL = {
    "edhrec": "edhrec_rank IS NULL, edhrec_rank ASC, name",
    "name": "name",
    "cmc": "cmc, name",
    "mv": "cmc, name",
    "eur": "min_eur IS NULL, min_eur ASC",
    "usd": "min_usd IS NULL, min_usd ASC",
    "rarity": "rarity_rank DESC, name",
    "released": "released_at DESC",
}


def to_sql(query, order="edhrec"):
    """Return (sql, params) for a DB query, or None if it must hit the live API."""
    ctx = {"params": [], "order": None}
    try:
        where = _Parser(_tokenize(query), ctx).parse()
    except Unsupported:
        return None
    clauses = [c for c in [where] if c]
    # Default: hide funny/un-cards unless the query explicitly asked about them
    # (is:funny / -is:funny / not:funny). A plain o:"funny" text search must NOT count.
    ql = query.lower()
    if "is:funny" not in ql and "not:funny" not in ql:
        clauses.append("funny = 0")
    where_sql = " AND ".join(clauses) if clauses else "1=1"
    order_key = (ctx["order"] or order or "edhrec").lower()
    order_sql = _ORDER_SQL.get(order_key, _ORDER_SQL["edhrec"])
    sql = f"SELECT {_SELECT} FROM cards WHERE {where_sql} ORDER BY {order_sql}"
    return sql, ctx["params"]


# --------------------------------------------------------------------------- #
# Row / card -> dict, and the public DB-first search/named                    #
# --------------------------------------------------------------------------- #

def _row_to_dict(row):
    d = dict(zip(_ROW_KEYS, row))
    d["color_identity"] = d["color_identity"] or "C"
    d["game_changer"] = bool(d["game_changer"])
    for k in ("arena", "paper", "mtgo", "funny"):
        d[k] = bool(d[k])
    try:
        d["legalities"] = json.loads(d["legalities"]) if d["legalities"] else {}
    except (TypeError, ValueError):
        d["legalities"] = {}
    return d


def simplify_api(card):
    """Map a raw Scryfall API card object to the same dict shape as a DB row."""
    faces = card.get("card_faces") or [{}]

    def face_join(key):
        return card.get(key) or " // ".join(f.get(key, "") for f in faces if f.get(key))

    prices = card.get("prices") or {}
    games = set(card.get("games") or [])
    ci = "".join(c for c in WUBRG if c in set(card.get("color_identity") or []))
    cols = "".join(c for c in WUBRG if c in set(card.get("colors") or (faces[0].get("colors") or [])))

    def num(v):
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "name": card.get("name"),
        "mv": card.get("cmc"),
        "type_line": face_join("type_line"),
        "oracle_text": face_join("oracle_text"),
        "mana_cost": face_join("mana_cost"),
        "color_identity": ci or "C",
        "colors": cols,
        "power": card.get("power") or (faces[0].get("power") if faces else None),
        "toughness": card.get("toughness") or (faces[0].get("toughness") if faces else None),
        "rarity": card.get("rarity"),
        "keywords": ",".join(card.get("keywords") or []).lower(),
        "game_changer": bool(card.get("game_changer")),
        "edhrec_rank": card.get("edhrec_rank"),
        "legalities": card.get("legalities") or {},
        "scryfall_uri": card.get("scryfall_uri"),
        "eur": num(prices.get("eur")),
        "eur_foil": num(prices.get("eur_foil")),
        "usd": num(prices.get("usd")),
        "usd_foil": num(prices.get("usd_foil")),
        "arena": "arena" in games,
        "paper": "paper" in games,
        "mtgo": "mtgo" in games,
        "funny": card.get("set_type") == "funny",
    }


def _run_db(db_path, sql, params, limit):
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(sql + " LIMIT ?", list(params) + [limit])
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def search(query, limit=30, order="edhrec", db_path=None, prefer_db=True):
    """Search cards, DB-first. Routes to the live API when the DB is absent or the
    query uses an operator the DB can't serve. Returns a list of card dicts."""
    db_path = db_path or default_db_path()
    if prefer_db and db_path and os.path.exists(db_path):
        translated = to_sql(query, order)
        if translated is not None:
            sql, params = translated
            return _run_db(db_path, sql, params, limit)
        # else: function:/unsupported operator -> fall through to live API
    return [simplify_api(c) for c in api.search(query, limit=limit, order=order)]


def named(name, db_path=None, prefer_db=True):
    """Exact (case-insensitive) single-card lookup, DB-first; API fuzzy fallback."""
    db_path = db_path or default_db_path()
    if prefer_db and db_path and os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        try:
            row = con.execute(
                f"SELECT {_SELECT} FROM cards WHERE lower(name)=lower(?) LIMIT 1", (name,)
            ).fetchone()
            if row:
                return _row_to_dict(row)
            # split/DFC full names like "Fire // Ice" — match either face's full name
            row = con.execute(
                f"SELECT {_SELECT} FROM cards WHERE lower(name) LIKE lower(?) LIMIT 1",
                (f"{name} //%",),
            ).fetchone()
            if row:
                return _row_to_dict(row)
        finally:
            con.close()
    card = api.named(name)
    return simplify_api(card) if card else None
