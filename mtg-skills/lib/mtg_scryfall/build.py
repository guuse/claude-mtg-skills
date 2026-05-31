"""Build `cards.sqlite` from Scryfall's Default Cards bulk file.

Default Cards has one object per *printing*. We collapse to one row per `oracle_id`
(docs/adr/0001): oracle-level fields come from the most recent printing; price is the
cheapest across printings; availability flags (arena/paper/mtgo) and `funny` are ORed.
"extra" objects (tokens, emblems, art series, …) are dropped so normal searches don't
surface them — matching Scryfall's default of hiding extras.

Memory-safe: the bulk array is streamed object-by-object into a staging table, then
collapsed with SQL (no giant in-memory list, no full json.load of ~150 MB).
"""

import json
import os
import sqlite3
import tempfile

from . import api
from .paths import meta_path_for

# Layouts that are "extra" cards Scryfall hides from default search results.
EXTRA_LAYOUTS = {
    "token", "double_faced_token", "emblem", "art_series",
    "vanguard", "scheme", "planar", "augment", "host",
}
RARITY_RANK = {"common": 1, "uncommon": 2, "rare": 3, "mythic": 4, "special": 5, "bonus": 5}
WUBRG = "WUBRG"


def _canon_colors(arr):
    """['B','W'] -> 'WB' (canonical WUBRG order). Empty list -> ''."""
    s = set(arr or [])
    return "".join(c for c in WUBRG if c in s)


def _face_join(card, key):
    top = card.get(key)
    if top:
        return top
    faces = card.get("card_faces") or []
    parts = [f.get(key, "") for f in faces if f.get(key)]
    return " // ".join(parts)


def card_to_row(card):
    """Map a raw Scryfall card object to a staging-table tuple, or None to skip."""
    if card.get("layout") in EXTRA_LAYOUTS:
        return None
    oracle_id = card.get("oracle_id")
    if not oracle_id:
        return None  # tokens/some promos lack an oracle_id

    faces = card.get("card_faces") or [{}]
    prices = card.get("prices") or {}
    games = set(card.get("games") or [])
    rarity = card.get("rarity") or ""

    def num(v):
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    power = card.get("power")
    toughness = card.get("toughness")
    if power is None and faces:
        power = faces[0].get("power")
    if toughness is None and faces:
        toughness = faces[0].get("toughness")

    return (
        oracle_id,
        card.get("name") or "",
        card.get("cmc"),
        _face_join(card, "type_line"),
        _face_join(card, "oracle_text"),
        _face_join(card, "mana_cost"),
        _canon_colors(card.get("color_identity")),
        _canon_colors(card.get("colors") or (faces[0].get("colors") if faces else None)),
        power,
        toughness,
        rarity,
        RARITY_RANK.get(rarity, 0),
        ",".join((card.get("keywords") or [])).lower(),
        "".join(c for c in WUBRG if c in set(card.get("produced_mana") or [])),
        1 if card.get("game_changer") else 0,
        card.get("edhrec_rank"),
        json.dumps(card.get("legalities") or {}),
        card.get("layout") or "",
        card.get("scryfall_uri") or "",
        card.get("released_at") or "",
        card.get("set") or "",
        num(prices.get("eur")),
        num(prices.get("eur_foil")),
        num(prices.get("usd")),
        num(prices.get("usd_foil")),
        1 if "arena" in games else 0,
        1 if "paper" in games else 0,
        1 if "mtgo" in games else 0,
        1 if card.get("set_type") == "funny" or card.get("border_color") == "silver" else 0,
    )


_STAGING_COLS = [
    "oracle_id", "name", "cmc", "type_line", "oracle_text", "mana_cost",
    "color_identity", "colors", "power", "toughness", "rarity", "rarity_rank",
    "keywords", "produced_mana", "game_changer", "edhrec_rank", "legalities",
    "layout", "scryfall_uri", "released_at", "set_code",
    "eur", "eur_foil", "usd", "usd_foil", "arena", "paper", "mtgo", "funny",
]


def iter_bulk_objects(path, bufsize=1 << 20):
    """Yield each object from a top-level JSON array file without loading it all.

    Uses JSONDecoder.raw_decode over a sliding text buffer so peak memory is roughly
    one chunk plus one card object.
    """
    dec = json.JSONDecoder()
    with open(path, encoding="utf-8") as f:
        buf = ""
        # Advance to the opening bracket.
        while "[" not in buf:
            chunk = f.read(bufsize)
            if not chunk:
                return
            buf += chunk
        buf = buf[buf.index("[") + 1:]
        while True:
            buf = buf.lstrip()
            while buf[:1] == ",":
                buf = buf[1:].lstrip()
            if not buf:
                chunk = f.read(bufsize)
                if not chunk:
                    return
                buf += chunk
                continue
            if buf[:1] == "]":
                return
            try:
                obj, idx = dec.raw_decode(buf)
            except json.JSONDecodeError:
                chunk = f.read(bufsize)
                if not chunk:
                    return  # truncated/end
                buf += chunk
                continue
            yield obj
            buf = buf[idx:]


def _schema(con):
    con.executescript(
        """
        DROP TABLE IF EXISTS staging;
        CREATE TABLE staging (
            oracle_id TEXT, name TEXT, cmc REAL, type_line TEXT, oracle_text TEXT,
            mana_cost TEXT, color_identity TEXT, colors TEXT, power TEXT, toughness TEXT,
            rarity TEXT, rarity_rank INTEGER, keywords TEXT, produced_mana TEXT,
            game_changer INTEGER, edhrec_rank INTEGER, legalities TEXT, layout TEXT,
            scryfall_uri TEXT, released_at TEXT, set_code TEXT,
            eur REAL, eur_foil REAL, usd REAL, usd_foil REAL,
            arena INTEGER, paper INTEGER, mtgo INTEGER, funny INTEGER
        );
        """
    )


def _collapse(con):
    """Collapse staging (per-printing) into `cards` (per oracle_id)."""
    # Latest-printing oracle fields: a single MAX(released_at) lets SQLite's documented
    # "bare columns follow the min/max row" behaviour pull the rest from that printing.
    # Price/availability aggregates are computed separately and joined on oracle_id.
    con.executescript(
        """
        DROP TABLE IF EXISTS cards;

        CREATE TABLE latest AS
            SELECT *, MAX(released_at) AS _latest FROM staging GROUP BY oracle_id;

        CREATE TABLE agg AS
            SELECT oracle_id,
                   MIN(eur)      AS min_eur,
                   MIN(eur_foil) AS min_eur_foil,
                   MIN(usd)      AS min_usd,
                   MIN(usd_foil) AS min_usd_foil,
                   MAX(arena)    AS arena,
                   MAX(paper)    AS paper,
                   MAX(mtgo)     AS mtgo,
                   MAX(funny)    AS funny,
                   MIN(edhrec_rank) AS edhrec_rank,
                   GROUP_CONCAT(DISTINCT set_code) AS set_codes
            FROM staging GROUP BY oracle_id;

        CREATE TABLE cards AS
            SELECT l.oracle_id, l.name, l.cmc, l.type_line, l.oracle_text, l.mana_cost,
                   l.color_identity, l.colors, l.power, l.toughness,
                   l.rarity, l.rarity_rank, l.keywords, l.produced_mana,
                   l.game_changer, a.edhrec_rank, l.legalities, l.layout, l.scryfall_uri,
                   l.released_at, a.set_codes,
                   a.min_eur, a.min_eur_foil, a.min_usd, a.min_usd_foil,
                   a.arena, a.paper, a.mtgo, a.funny
            FROM latest l JOIN agg a ON a.oracle_id = l.oracle_id;

        DROP TABLE latest;
        DROP TABLE agg;
        DROP TABLE staging;

        CREATE INDEX idx_name  ON cards(name);
        CREATE INDEX idx_ci    ON cards(color_identity);
        CREATE INDEX idx_cmc   ON cards(cmc);
        CREATE INDEX idx_rank  ON cards(edhrec_rank);
        CREATE INDEX idx_rare  ON cards(rarity_rank);
        """
    )
    con.commit()


def build_from_json(json_path, db_path, progress=None, batch=5000):
    """Build `db_path` from an already-downloaded bulk JSON file at `json_path`."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    tmp_db = db_path + ".tmp"
    if os.path.exists(tmp_db):
        os.remove(tmp_db)
    con = sqlite3.connect(tmp_db)
    try:
        con.execute("PRAGMA journal_mode=OFF")
        con.execute("PRAGMA synchronous=OFF")
        _schema(con)
        placeholders = ",".join("?" * len(_STAGING_COLS))
        insert = f"INSERT INTO staging ({','.join(_STAGING_COLS)}) VALUES ({placeholders})"
        rows, seen, kept = [], 0, 0
        for obj in iter_bulk_objects(json_path):
            seen += 1
            row = card_to_row(obj)
            if row is None:
                continue
            rows.append(row)
            kept += 1
            if len(rows) >= batch:
                con.executemany(insert, rows)
                rows.clear()
                if progress:
                    progress("staged", kept)
        if rows:
            con.executemany(insert, rows)
        con.commit()
        if progress:
            progress("collapsing", kept)
        _collapse(con)
        unique = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    finally:
        con.close()
    os.replace(tmp_db, db_path)
    return {"printings_seen": seen, "rows_staged": kept, "unique_cards": unique}


def build_database(dest=None, force=False, progress=None, keep_json=False):
    """Download the Default Cards bulk file and build `cards.sqlite` at `dest`.

    `dest` is the target SQLite path (default: `.mtg/database/cards.sqlite`). Returns a
    meta dict (also written to `meta.json` beside the DB). `force` is accepted for API
    symmetry; the download always fetches the current bulk file.
    """
    from .paths import default_db_path
    db_path = dest or default_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    meta_entry = api.bulk_metadata("default_cards")
    if progress:
        size_mb = (meta_entry.get("size") or 0) / 1e6
        progress("downloading", f"{size_mb:.0f} MB")

    fd, json_path = tempfile.mkstemp(suffix=".json", dir=os.path.dirname(os.path.abspath(db_path)))
    os.close(fd)
    try:
        def dl_progress(done, total):
            if progress and total:
                progress("download_pct", int(done * 100 / total))
        api.download_to(meta_entry["download_uri"], json_path, progress=dl_progress)
        if progress:
            progress("building", None)
        stats = build_from_json(json_path, db_path, progress=progress)
    finally:
        if not keep_json and os.path.exists(json_path):
            os.remove(json_path)

    meta = {
        "source": "scryfall/default_cards",
        "bulk_id": meta_entry.get("id"),
        "bulk_updated_at": meta_entry.get("updated_at"),
        "bulk_size": meta_entry.get("size"),
        "built_at": _utcnow_iso(),
        "unique_cards": stats["unique_cards"],
        "printings_seen": stats["printings_seen"],
    }
    with open(meta_path_for(db_path), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    if keep_json:
        meta["json_path"] = json_path
    return meta


def _utcnow_iso():
    # Imported lazily so the rest of the module stays import-time pure.
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
