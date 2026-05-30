#!/usr/bin/env python3
"""
scryfall_search.py — query the Scryfall API for Commander deckbuilding.

Two modes:
  Search:  python scryfall_search.py "<query>" [--limit N] [--order edhrec] [--json]
  Named:   python scryfall_search.py --named "Sol Ring" [--json]

Output (table by default) shows, for each card: name, mana value (mv), type, color
identity, and Cardmarket price in EUR (Scryfall's prices.eur). Use --json for the
full structured list to parse programmatically.

Scryfall query syntax (see references/scryfall-syntax.md):
  id<=WB            color identity coverage (cards legal in a White/Black deck)
  o:"sacrifice"     oracle text contains phrase
  t:creature        type
  mv<=3             mana value
  function:ramp     curated function tag (ramp, removal, counterspell, board-wipe, card-advantage...)
  is:gamechanger    on the official Game Changers list
  order=edhrec      sort by popularity (passed via --order, default edhrec)

Stdlib only — no pip install required. Respects Scryfall etiquette with a small
delay between paginated requests and a descriptive User-Agent.

If the network can't reach api.scryfall.com, the script prints a clear message;
fall back to web_search + web_fetch of the Scryfall page, or proceed from known
card knowledge with a caveat that prices/newest cards are unverified.
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

API = "https://api.scryfall.com"
HEADERS = {
    # Scryfall asks for a descriptive User-Agent and an explicit Accept header.
    "User-Agent": "ClaudeCommanderDeckBuilder/1.0 (skill)",
    "Accept": "application/json",
}
DELAY_SECONDS = 0.1  # be polite between paginated calls


def _get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _oracle(card):
    """Oracle text, joining faces for double-faced/split cards."""
    if card.get("oracle_text"):
        return card["oracle_text"]
    faces = card.get("card_faces") or []
    return " // ".join(f.get("oracle_text", "") for f in faces if f.get("oracle_text"))


def _simplify(card):
    return {
        "name": card.get("name"),
        "mv": card.get("cmc"),
        "type_line": card.get("type_line"),
        "color_identity": "".join(card.get("color_identity") or []) or "C",
        "mana_cost": card.get("mana_cost")
        or " // ".join(f.get("mana_cost", "") for f in (card.get("card_faces") or [])),
        "eur": (card.get("prices") or {}).get("eur"),
        "eur_foil": (card.get("prices") or {}).get("eur_foil"),
        "oracle_text": _oracle(card),
        "scryfall_uri": card.get("scryfall_uri"),
    }


def search(query, limit, order):
    """Paginate Scryfall search results up to `limit` cards."""
    results = []
    params = {"q": query, "order": order, "unique": "cards"}
    url = f"{API}/cards/search?" + urllib.parse.urlencode(params)
    while url and len(results) < limit:
        try:
            data = _get(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:  # no cards matched
                break
            raise
        for card in data.get("data", []):
            results.append(_simplify(card))
            if len(results) >= limit:
                break
        url = data.get("next_page") if data.get("has_more") else None
        if url:
            time.sleep(DELAY_SECONDS)
    return results


def named(name):
    url = f"{API}/cards/named?" + urllib.parse.urlencode({"exact": name})
    try:
        return [_simplify(_get(url))]
    except urllib.error.HTTPError as e:
        if e.code == 404:  # try fuzzy
            url = f"{API}/cards/named?" + urllib.parse.urlencode({"fuzzy": name})
            return [_simplify(_get(url))]
        raise


def print_table(cards):
    if not cards:
        print("No cards found.")
        return
    print(f"{'MV':>3}  {'EUR':>7}  {'CI':<5} {'NAME':<34} TYPE")
    print("-" * 90)
    for c in cards:
        mv = "" if c["mv"] is None else f"{c['mv']:.0f}"
        eur = "  n/a" if not c["eur"] else f"{float(c['eur']):>7.2f}"
        name = (c["name"] or "")[:34]
        tline = (c["type_line"] or "")[:30]
        print(f"{mv:>3}  {eur:>7}  {c['color_identity']:<5} {name:<34} {tline}")
    priced = [float(c["eur"]) for c in cards if c["eur"]]
    if priced:
        print("-" * 90)
        print(f"{len(cards)} cards shown · {len(priced)} priced · "
              f"sum EUR {sum(priced):.2f} (Cardmarket, via Scryfall)")


def main():
    ap = argparse.ArgumentParser(description="Scryfall search/pricing helper for Commander decks.")
    ap.add_argument("query", nargs="?", help="Scryfall search query, e.g. 'id<=WB function:ramp mv<=2'")
    ap.add_argument("--named", help="Exact (or fuzzy) single-card lookup with full price.")
    ap.add_argument("--limit", type=int, default=30, help="Max cards to return (default 30).")
    ap.add_argument("--order", default="edhrec", help="Sort order (default edhrec = popularity).")
    ap.add_argument("--json", action="store_true", help="Emit full JSON instead of a table.")
    args = ap.parse_args()

    if not args.query and not args.named:
        ap.error("provide a search query or --named NAME")

    try:
        cards = named(args.named) if args.named else search(args.query, args.limit, args.order)
    except urllib.error.URLError as e:
        print(f"ERROR: could not reach api.scryfall.com ({e}).", file=sys.stderr)
        print("Fall back to web_search + web_fetch of the Scryfall page, or note that "
              "prices/newest cards are unverified.", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(cards, indent=2, ensure_ascii=False))
    else:
        print_table(cards)


if __name__ == "__main__":
    main()
