"""Pull the live competitive metagame and real decklists from mtgtop8.com.

Standard/Arena meta has no free JSON API, and untapped.gg / mtggoldfish / mtgdecks /
aetherhub all sit behind Cloudflare and 403 automated fetches. **mtgtop8.com does not** —
it serves plain HTML to a descriptive User-Agent and exposes a plain-text decklist export
at `mtgo?d=<id>`. That makes it the one reliable, bot-fetchable source of *proven, current*
decklists, so the Standard skills build by adapting real meta lists instead of brewing a
60 from scratch (which is what made earlier builds basic and incohesive).

Three things this module gives you (all through the shared polite/retrying fetcher):

    fetch_meta(fmt)               -> [{"name","share","archetype_id"}, ...]   # the metagame breakdown
    fetch_archetype_decks(a, fmt) -> [{"deck_id","event_id","name","player","event"}, ...]
    fetch_deck(deck_id)           -> {"deck_id","maindeck":[{qty,name}],"sideboard":[...]}

`fmt` is mtgtop8's format code — "ST" Standard, "PI" Pioneer, "MO" Modern, "PAU" Pauper,
"LE" Legacy, "VI" Vintage, "EDH" Commander, "EXP" Explorer, "HISTORIC" Historic. The
Standard skills only ever pass "ST".

A miss raises `FetchError`; callers fall back (model meta knowledge, flagged unverified)
and say mtgtop8 was unavailable. We never fabricate a decklist or a metagame share.

Stdlib only — no pip install required.
"""

import re

from . import http

BASE = "https://www.mtgtop8.com"
META_URL = BASE + "/format?f={fmt}"
ARCHETYPE_URL = BASE + "/archetype?a={a}&meta=50&f={fmt}"
DECK_EXPORT_URL = BASE + "/mtgo?d={d}"


def _unescape(s):
    """Minimal HTML entity cleanup for the card/archetype names mtgtop8 emits."""
    return (
        s.replace("&amp;", "&").replace("&#39;", "'").replace("&#039;", "'")
        .replace("&quot;", '"').replace("&eacute;", "é").replace("&ouml;", "ö")
        .strip()
    )


# A metagame entry: <a href=archetype?a=207&meta=50&f=ST>UR Aggro</a> ... >25 %<
_META_RE = re.compile(
    r"archetype\?a=(\d+)&(?:amp;)?meta=\d+&(?:amp;)?f=(?:ST|PI|MO|PAU|LE|VI|EDH|EXP|HISTORIC)>"
    r"([^<]+)</a>.*?>\s*([\d.]+)\s*%",
    re.DOTALL,
)


def fetch_meta(fmt="ST"):
    """Return the current metagame breakdown, biggest share first.

    Each entry is {"name": str, "share": float (percent), "archetype_id": int}. The
    archetype_id feeds `fetch_archetype_decks`.
    """
    html = http.get_text(META_URL.format(fmt=fmt))
    out, seen = [], set()
    for a_id, name, share in _META_RE.findall(html):
        a_id = int(a_id)
        if a_id in seen:
            continue
        seen.add(a_id)
        try:
            pct = float(share)
        except ValueError:
            pct = 0.0
        out.append({"name": _unescape(name), "share": pct, "archetype_id": a_id})
    out.sort(key=lambda d: d["share"], reverse=True)
    return out


# A decklist row on an archetype page:
#   <a href=/event?e=86946&d=860074&f=ST>Izzet Prowess</a></td>
#   <td><a class=player href=/search?player=Arianne>Arianne</a></td>
#   <td><a href=/event?e=86946&f=ST>MTGO Challenge 32</a></td>
_DECK_ROW_RE = re.compile(
    r"event\?e=(\d+)&(?:amp;)?d=(\d+)&(?:amp;)?f=\w+>([^<]+)</a>"
    r"(?:.*?player=[^>]*>([^<]+)</a>)?"
    r"(?:.*?event\?e=\d+&(?:amp;)?f=\w+>([^<]+)</a>)?",
    re.DOTALL,
)


def fetch_archetype_decks(archetype_id, fmt="ST", limit=None):
    """Return recent decklists filed under an archetype, most recent first.

    Each entry is {"deck_id": int, "event_id": int, "name": str, "player": str|None,
    "event": str|None}. Pass the deck_id to `fetch_deck`. `limit` trims the list.
    """
    html = http.get_text(ARCHETYPE_URL.format(a=archetype_id, fmt=fmt))
    out, seen = [], set()
    for ev, dk, name, player, event in _DECK_ROW_RE.findall(html):
        dk = int(dk)
        if dk in seen:
            continue
        seen.add(dk)
        out.append({
            "deck_id": dk,
            "event_id": int(ev),
            "name": _unescape(name),
            "player": _unescape(player) if player else None,
            "event": _unescape(event) if event else None,
        })
        if limit and len(out) >= limit:
            break
    return out


def _parse_export(text):
    """Split mtgtop8's plain-text `mtgo?d=` export into maindeck + sideboard.

    The export is `<qty> <Card Name>` lines, a literal `Sideboard` line, then the
    sideboard. Returns (maindeck, sideboard) as lists of {"quantity","name"}.
    """
    main, side, cur = [], [], None
    cur = main
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower() == "sideboard":
            cur = side
            continue
        m = re.match(r"(\d+)\s+(.+)", line)
        if m:
            cur.append({"quantity": int(m.group(1)), "name": _unescape(m.group(2))})
    return main, side


def fetch_deck(deck_id):
    """Fetch one decklist by its mtgtop8 deck id via the plain-text export.

    Returns {"deck_id": int, "maindeck": [{quantity,name}], "sideboard": [...]}.
    """
    text = http.get_text(DECK_EXPORT_URL.format(d=deck_id))
    main, side = _parse_export(text)
    if not main:
        raise http.FetchError(
            f"mtgtop8 export for deck {deck_id} had no parseable cards", url=DECK_EXPORT_URL.format(d=deck_id)
        )
    return {"deck_id": int(deck_id), "maindeck": main, "sideboard": side}


def top_decklists(fmt="ST", archetypes=4, per_archetype=2):
    """Convenience: the metagame plus a few real decklists for each top archetype.

    Returns [{"archetype","share","archetype_id","decks":[fetch_deck(...) , ...]}, ...]
    for the `archetypes` biggest shares, each with up to `per_archetype` recent lists.
    Best-effort per archetype: an archetype whose decks fail to fetch is included with an
    empty `decks` list rather than aborting the whole call.
    """
    meta = fetch_meta(fmt)
    out = []
    for entry in meta[:archetypes]:
        decks = []
        try:
            refs = fetch_archetype_decks(entry["archetype_id"], fmt, limit=per_archetype)
            for ref in refs:
                try:
                    d = fetch_deck(ref["deck_id"])
                    d.update(name=ref["name"], player=ref["player"], event=ref["event"])
                    decks.append(d)
                except http.FetchError:
                    continue
        except http.FetchError:
            pass
        out.append({
            "archetype": entry["name"],
            "share": entry["share"],
            "archetype_id": entry["archetype_id"],
            "decks": decks,
        })
    return out


def to_import_lines(deck, include_sideboard=True):
    """Render a fetched deck as plain `<qty> <name>` lines (Arena/MTGO importable)."""
    lines = [f"{c['quantity']} {c['name']}" for c in deck.get("maindeck", [])]
    if include_sideboard and deck.get("sideboard"):
        lines.append("")
        lines.append("Sideboard")
        lines += [f"{c['quantity']} {c['name']}" for c in deck["sideboard"]]
    return lines
