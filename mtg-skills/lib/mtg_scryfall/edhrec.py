"""EDHREC JSON client — the "what comparable decks actually run" source.

EDHREC publishes structured JSON at **json.edhrec.com** that mirrors its public pages.
We use that (never the Cloudflare-protected HTML at edhrec.com) for a commander's
staples, high-synergy cards, theme/budget lists, and its **average decklist**. This is
the primary source for proven Commander inclusions; Scryfall stays the backbone for
card data, legality and pricing.

Confirmed-working endpoint shapes (verified June 2026 — EDHREC changes these
occasionally, so callers must treat a miss as non-fatal):

    {BASE}/commanders/<slug>.json           staples, high-synergy, top cards, themes
    {BASE}/commanders/<slug>/<theme>.json   one theme's cards (<theme> from .themes)
    {BASE}/commanders/<slug>/budget.json    the budget build's cards
    {BASE}/average-decks/<slug>.json        a literal ~100-card average decklist

Everything routes through `http.get_json` (descriptive UA, retry/backoff). A miss
raises `FetchError`, which the caller turns into a "fell back to the local Scryfall
database" message — we never fabricate inclusions.

Stdlib only — no pip install required.
"""

import re

from . import http

BASE = "https://json.edhrec.com/pages"


def slugify(name):
    """Turn a commander name into the EDHREC URL slug.

    "Atraxa, Praetors' Voice" -> "atraxa-praetors-voice". Apostrophes/commas/periods
    vanish; every other run of non-alphanumerics becomes a single hyphen. A partner /
    background / split name ("A // B") slugs on its first face, which is how EDHREC
    routes the canonical page.
    """
    s = name.strip().lower()
    s = s.split("//")[0].strip()
    s = re.sub(r"[',.’]", "", s)        # ' , . and the curly apostrophe drop out
    s = re.sub(r"[^a-z0-9]+", "-", s)        # everything else -> hyphen
    return re.sub(r"-+", "-", s).strip("-")


def _cardviews(cardlist):
    """Normalise one EDHREC cardlist section into plain {name, synergy, num_decks}."""
    out = []
    for cv in cardlist.get("cardviews", []) or []:
        name = cv.get("name")
        if not name:
            continue
        out.append({
            "name": name,
            "synergy": cv.get("synergy"),
            "num_decks": cv.get("num_decks"),
            "potential_decks": cv.get("potential_decks"),
        })
    return out


def _parse_page(page):
    """Pull the categorised cardlists + theme links out of a commander/theme page."""
    jd = (page.get("container") or {}).get("json_dict") or {}
    cardlists = {}
    for cl in jd.get("cardlists", []) or []:
        header = cl.get("header")
        if header:
            cardlists[header] = _cardviews(cl)
    themes = [
        {"value": t.get("value"), "slug": t.get("slug"), "count": t.get("count")}
        for t in (page.get("panels") or {}).get("taglinks", []) or []
        if t.get("slug")
    ]
    return {
        "cardlists": cardlists,
        "themes": themes,
        "num_decks": page.get("num_decks_avg"),
        "avg_price": page.get("avg_price"),
    }


def commander(name, slug=None):
    """Fetch a commander's main EDHREC page.

    Returns {slug, cardlists, themes, num_decks, avg_price}, where `cardlists` maps
    section headers ("Top Cards", "High Synergy Cards", "Game Changers", by type, ...)
    to lists of {name, synergy, num_decks}. Raises `FetchError` if EDHREC is unreachable
    or has no page for this commander.
    """
    slug = slug or slugify(name)
    page = http.get_json(f"{BASE}/commanders/{slug}.json")
    result = _parse_page(page)
    result["slug"] = slug
    return result


def theme(name, theme_slug, slug=None):
    """Fetch one theme's cardlists for a commander (theme_slug from commander().themes)."""
    slug = slug or slugify(name)
    page = http.get_json(f"{BASE}/commanders/{slug}/{theme_slug}.json")
    result = _parse_page(page)
    result["slug"] = slug
    result["theme"] = theme_slug
    return result


def budget(name, slug=None):
    """Fetch the budget build's cardlists for a commander."""
    slug = slug or slugify(name)
    page = http.get_json(f"{BASE}/commanders/{slug}/budget.json")
    result = _parse_page(page)
    result["slug"] = slug
    return result


def average_deck(name, slug=None):
    """Fetch a commander's average decklist.

    Returns {slug, cards, deck_size}, where `cards` is a list of "<qty> <name>" strings
    (EDHREC's own `deck` array) ready to paste or to feed analyze_deck.py. Raises
    `FetchError` if there is no average-deck page for this commander.
    """
    slug = slug or slugify(name)
    page = http.get_json(f"{BASE}/average-decks/{slug}.json")
    cards = page.get("deck") or []
    return {"slug": slug, "cards": cards, "deck_size": page.get("deck_size")}
