"""Import a user's online decklist from Archidekt or Moxfield via their JSON APIs.

Pasting a list always works, but users often just have a URL. Both sites block raw
HTML scraping behind Cloudflare; both expose a stable JSON API that returns the deck
cleanly when you send a real User-Agent. Confirmed-working shapes (verified June 2026):

    Archidekt:  https://archidekt.com/api/decks/<id>/
    Moxfield:   https://api2.moxfield.com/v3/decks/all/<publicId>

`fetch_deck(url_or_id)` detects the source, fetches through `http.get_json` (descriptive
UA, retry/backoff), and returns a normalised dict:

    {"source": "moxfield"|"archidekt", "name": str, "format": str|None,
     "commanders": ["Name", ...], "cards": [{"quantity": int, "name": str}, ...]}

A miss raises `FetchError`; the caller falls back to asking the user to paste the list
and says which site failed. We never fabricate a decklist.

Stdlib only — no pip install required.
"""

import re

from . import http

ARCHIDEKT_API = "https://archidekt.com/api/decks/{id}/"
MOXFIELD_API = "https://api2.moxfield.com/v3/decks/all/{id}"

# Archidekt encodes the format as an integer; map the common ones for display.
_ARCHIDEKT_FORMATS = {
    1: "standard", 2: "modern", 3: "commander", 4: "legacy", 5: "vintage",
    6: "pauper", 7: "custom", 8: "frontier", 9: "future-standard", 10: "penny",
    11: "1v1-commander", 12: "duel-commander", 13: "brawl", 14: "oathbreaker",
    15: "pioneer", 16: "historic", 17: "pauper-edh", 18: "alchemy", 19: "explorer",
    20: "historic-brawl", 21: "gladiator", 22: "premodern", 23: "predh",
    24: "timeless", 25: "standard-brawl",
}


def parse_deck_ref(ref):
    """Return ("archidekt"|"moxfield", id) from a URL or a bare id.

    Accepts full URLs (archidekt.com/decks/<id>-slug, moxfield.com/decks/<publicId>),
    API URLs, or a bare id. Raises ValueError if the source can't be determined.
    """
    ref = ref.strip()
    low = ref.lower()
    if "archidekt.com" in low:
        m = re.search(r"/decks/(\d+)", low)
        if m:
            return "archidekt", m.group(1)
    if "moxfield.com" in low:
        m = re.search(r"/decks/(?:all/)?([A-Za-z0-9_-]+)", ref)
        if m:
            return "moxfield", m.group(1)
    # Bare id: Archidekt ids are all digits, Moxfield public ids are mixed-case tokens.
    if re.fullmatch(r"\d+", ref):
        return "archidekt", ref
    if re.fullmatch(r"[A-Za-z0-9_-]{3,}", ref):
        return "moxfield", ref
    raise ValueError(f"could not recognise an Archidekt or Moxfield deck in {ref!r}")


def from_archidekt(deck_id):
    """Fetch and normalise an Archidekt deck by numeric id."""
    data = http.get_json(ARCHIDEKT_API.format(id=deck_id))
    commanders, cards = [], []
    for entry in data.get("cards", []) or []:
        card = entry.get("card") or {}
        name = (card.get("oracleCard") or {}).get("name") or card.get("displayName")
        if not name:
            continue
        qty = entry.get("quantity") or 1
        cats = entry.get("categories") or []
        if any(c.lower() == "commander" for c in cats):
            commanders.append(name)
        else:
            cards.append({"quantity": qty, "name": name})
    fmt = _ARCHIDEKT_FORMATS.get(data.get("deckFormat"))
    return {
        "source": "archidekt",
        "name": data.get("name"),
        "format": fmt,
        "commanders": commanders,
        "cards": cards,
    }


# Boards whose cards belong in the maindeck count (vs. sideboard/maybeboard).
_MOXFIELD_MAIN_BOARDS = ("mainboard",)
_MOXFIELD_COMMAND_BOARDS = ("commanders", "companions", "signatureSpells")


def from_moxfield(public_id):
    """Fetch and normalise a Moxfield deck by public id."""
    data = http.get_json(MOXFIELD_API.format(id=public_id))
    boards = data.get("boards") or {}

    def _cards(board_name):
        out = []
        for entry in (boards.get(board_name) or {}).get("cards", {}).values():
            name = (entry.get("card") or {}).get("name")
            if name:
                out.append({"quantity": entry.get("quantity") or 1, "name": name})
        return out

    commanders = [c["name"] for c in _cards("commanders")]
    cards = []
    for b in _MOXFIELD_MAIN_BOARDS:
        cards.extend(_cards(b))
    return {
        "source": "moxfield",
        "name": data.get("name"),
        "format": data.get("format"),
        "commanders": commanders,
        "cards": cards,
    }


def fetch_deck(ref):
    """Detect the source from `ref` (URL or id) and return the normalised deck."""
    source, deck_id = parse_deck_ref(ref)
    if source == "archidekt":
        return from_archidekt(deck_id)
    return from_moxfield(deck_id)


def to_import_lines(deck, include_commanders=True):
    """Render a normalised deck as plain "<qty> <name>" lines (commanders first)."""
    lines = []
    if include_commanders:
        for name in deck.get("commanders", []):
            lines.append(f"1 {name}")
    for c in deck.get("cards", []):
        lines.append(f"{c['quantity']} {c['name']}")
    return lines
