"""Parse an MTG collection export into `{name: count}` — tolerant of format.

MTG Arena collections (and Moxfield/Archidekt exports) come out of third-party tools in
**several shapes**: a plain `.txt` deck-style list, a `.csv` with a header row, or a `.json`
array/object. The deck skills only need the same thing from all of them — *which cards the
user owns and how many* — so this module normalises any of the three into one merged
`{display_name: count}` mapping. Pure file/string parsing: no database, no network.

The entry points:

    find_collection_file(collection_dir=None) -> str | None   # locate the export in collection/
    parse_collection(path) -> dict                            # parse a specific file
    load_collection(path=None) -> dict | None                 # find (if needed) + parse

`parse_collection`/`load_collection` return:
    {"path", "format", "cards": {name: count}, "total", "unique", "note"}
where `cards` preserves first-seen display names, merges duplicates case-insensitively, and
`note` (str|None) flags partial results (e.g. a JSON export keyed only by Arena IDs we can't
map to names).
"""

import csv
import io
import json
import os
import re

# Recognised collection-export extensions, in the order we prefer them when auto-finding.
COLLECTION_EXTS = (".txt", ".csv", ".json")

# Filenames we treat as "the collection" before falling back to any matching extension.
_PREFERRED_STEMS = ("mtga_collection", "collection", "arena_collection", "mtga", "arena")

# "4 Card Name" optionally trailed by an Arena set annotation like "(DMU) 107" — shared with
# arena.parse_deck, kept local so this module has no import-time dependency on it.
_TXT_LINE_RE = re.compile(r"^(\d+)\s*[xX]?\s+(.+?)(?:\s+\([^)]+\)\s+\S+)?\s*$")
# Section/header lines an Arena export interleaves; not cards.
_TXT_SKIP = {"deck", "maindeck", "sideboard", "side", "commander", "companion",
             "about", "name"}

# Header tokens that name the quantity / card-name columns in a CSV, most-specific first.
_QTY_HEADERS = ("quantity", "count", "qty", "owned", "have", "copies", "amount",
                "number", "total", "nb")
_NAME_HEADERS = ("name", "card name", "cardname", "card_name", "card")
# JSON object keys carrying the same two facts.
_QTY_KEYS = ("quantity", "count", "qty", "owned", "have", "copies", "amount", "number")
_NAME_KEYS = ("name", "card name", "cardname", "card_name", "card", "title")
# JSON wrapper keys whose value holds the actual list/map of cards.
_CONTAINER_KEYS = ("cards", "collection", "library", "owned", "mainboard", "maindeck",
                   "deck", "data", "items", "list")


def _norm_key(name):
    """Case/space-insensitive key for merging the same card spelled slightly differently."""
    return re.sub(r"\s+", " ", str(name).strip()).casefold()


def _merge(cards, name, count):
    """Add `count` copies of `name` into the ordered `cards` dict, merging duplicates."""
    name = re.sub(r"\s+", " ", str(name).strip())
    if not name:
        return
    try:
        count = int(count)
    except (TypeError, ValueError):
        return
    if count <= 0:
        return
    key = _norm_key(name)
    if key in cards:
        cards[key] = (cards[key][0], cards[key][1] + count)
    else:
        cards[key] = (name, count)


def _result(path, fmt, cards, note=None):
    flat = {disp: cnt for disp, cnt in cards.values()}
    return {
        "path": path,
        "format": fmt,
        "cards": flat,
        "total": sum(flat.values()),
        "unique": len(flat),
        "note": note,
    }


# --------------------------------------------------------------------------- finders


def find_collection_file(collection_dir=None):
    """Return the path to a collection export under `collection/`, or None.

    Prefers well-known stems (`mtga_collection.*`, `collection.*`, …) over an arbitrary
    file, and `.txt` over `.csv` over `.json` when several exist. `.keep`/dotfiles are
    ignored. With no argument, resolves the workspace's `collection/` (honours `$MTG_HOME`).
    """
    if collection_dir is None:
        from .paths import collection_dir as _cdir
        collection_dir = _cdir()
    if not os.path.isdir(collection_dir):
        return None

    candidates = []
    for fn in os.listdir(collection_dir):
        if fn.startswith("."):
            continue
        stem, ext = os.path.splitext(fn)
        ext = ext.lower()
        if ext not in COLLECTION_EXTS:
            continue
        full = os.path.join(collection_dir, fn)
        if not os.path.isfile(full):
            continue
        try:
            empty = os.path.getsize(full) == 0
        except OSError:
            empty = True
        if empty:
            continue
        stem_rank = next((i for i, s in enumerate(_PREFERRED_STEMS)
                          if stem.lower() == s), len(_PREFERRED_STEMS))
        ext_rank = COLLECTION_EXTS.index(ext)
        candidates.append((stem_rank, ext_rank, fn.lower(), full))

    if not candidates:
        return None
    candidates.sort()
    return candidates[0][3]


# --------------------------------------------------------------------------- per-format


def _parse_txt(text):
    cards = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "//")):
            continue
        if s.lower() in _TXT_SKIP:
            continue
        m = _TXT_LINE_RE.match(s)
        if m:
            _merge(cards, m.group(2), m.group(1))
        # Lines without a leading count (a bare card name) count as a single copy.
        elif not s[0].isdigit():
            _merge(cards, s, 1)
    return cards


def _pick_column(headers, wanted):
    """Index of the first header matching any token in `wanted` (exact, then substring)."""
    low = [h.strip().lower() for h in headers]
    for token in wanted:
        if token in low:
            return low.index(token)
    for token in wanted:
        for i, h in enumerate(low):
            if token in h:
                return i
    return None


def _looks_like_header(row):
    """A row is a header if no cell is a bare integer (data rows carry a count)."""
    return not any(c.strip().isdigit() for c in row if c is not None)


def _parse_csv(text):
    rows = [r for r in csv.reader(io.StringIO(text)) if any((c or "").strip() for c in r)]
    if not rows:
        return {}, None
    cards = {}

    if _looks_like_header(rows[0]):
        headers = rows[0]
        name_i = _pick_column(headers, _NAME_HEADERS)
        qty_i = _pick_column(headers, _QTY_HEADERS)
        if name_i is None:
            # Header present but no recognisable name column — fall back to positional on the
            # data rows (skip the header so it isn't mistaken for a card).
            return _parse_csv_positional(rows[1:]), None
        for r in rows[1:]:
            if name_i >= len(r):
                continue
            count = r[qty_i] if (qty_i is not None and qty_i < len(r)
                                 and (r[qty_i] or "").strip().isdigit()) else 1
            _merge(cards, r[name_i], count)
        return cards, None

    return _parse_csv_positional(rows), None


def _parse_csv_positional(rows):
    """Headerless CSV: per row, the integer cell is the count, the longest text the name."""
    cards = {}
    for r in rows:
        cells = [(c or "").strip() for c in r]
        count = next((c for c in cells if c.isdigit()), None)
        names = [c for c in cells if c and not c.isdigit()]
        if not names:
            continue
        name = max(names, key=len)
        _merge(cards, name, count if count is not None else 1)
    return cards


def _extract_qty(obj):
    for k in obj:
        if k.lower() in _QTY_KEYS and str(obj[k]).strip().lstrip("-").isdigit():
            return int(obj[k])
    return 1


def _extract_name(obj):
    for k in obj:
        if k.lower() in _NAME_KEYS and isinstance(obj[k], str) and obj[k].strip():
            return obj[k]
    return None


def _parse_json(text):
    data = json.loads(text)
    cards = {}

    # Unwrap a single container key, e.g. {"collection": [...]}.
    if isinstance(data, dict):
        for k in data:
            if k.lower() in _CONTAINER_KEYS and isinstance(data[k], (list, dict)):
                data = data[k]
                break

    if isinstance(data, list):
        named = 0
        for obj in data:
            if isinstance(obj, dict):
                name = _extract_name(obj)
                if name is not None:
                    _merge(cards, name, _extract_qty(obj))
                    named += 1
            elif isinstance(obj, str):
                _merge(cards, obj, 1)
        note = None if (named or not data) else (
            "JSON entries had no recognisable card-name field (Arena IDs only?) — "
            "re-export with card names, or use a .txt/.csv export.")
        return cards, note

    if isinstance(data, dict):
        # {name: count} map — but a map keyed by numeric Arena IDs can't be resolved here.
        items = list(data.items())
        if items and all(str(k).strip().isdigit() for k, _ in items):
            return {}, ("JSON is keyed by Arena card IDs, which can't be mapped to names "
                        "offline — re-export with card names, or use a .txt/.csv export.")
        for k, v in items:
            if isinstance(v, dict):
                cnt = _extract_qty(v)
                _merge(cards, _extract_name(v) or k, cnt)
            else:
                _merge(cards, k, v)
        return cards, None

    return cards, None


# --------------------------------------------------------------------------- public


def parse_collection(path):
    """Parse a collection export at `path`, dispatching on extension (content for ambiguous).

    Raises FileNotFoundError if the path doesn't exist; ValueError if a `.json` file is
    malformed. Unknown extensions are sniffed (JSON if it parses, else CSV if comma-rich,
    else the plain text grammar).
    """
    with open(path, encoding="utf-8-sig") as fh:
        text = fh.read()
    ext = os.path.splitext(path)[1].lower()

    if ext == ".json":
        try:
            cards, note = _parse_json(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}: invalid JSON ({e})") from e
        return _result(path, "json", cards, note)
    if ext == ".csv":
        cards, note = _parse_csv(text)
        return _result(path, "csv", cards, note)
    if ext == ".txt":
        return _result(path, "txt", _parse_txt(text))

    # Unknown extension — sniff the content.
    stripped = text.lstrip()
    if stripped[:1] in ("[", "{"):
        try:
            cards, note = _parse_json(text)
            return _result(path, "json", cards, note)
        except (json.JSONDecodeError, ValueError):
            pass
    first_line = next((ln for ln in text.splitlines() if ln.strip()), "")
    if "," in first_line:
        cards, note = _parse_csv(text)
        return _result(path, "csv", cards, note)
    return _result(path, "txt", _parse_txt(text))


def load_collection(path=None):
    """Find (if `path` is None) and parse the collection. Returns the result dict or None.

    Returns None only when no export file exists; a file that parses to zero cards still
    returns a result (with `total` 0 and possibly a `note`), so callers can tell "no file"
    from "file we couldn't read".
    """
    if path in (None, ""):
        path = find_collection_file()
    if not path:
        return None
    return parse_collection(path)
