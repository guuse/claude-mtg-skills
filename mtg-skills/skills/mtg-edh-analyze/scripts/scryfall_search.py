#!/usr/bin/env python3
"""scryfall_search.py — card search & pricing for Commander deckbuilding.

Reads from the **local Scryfall database** (`.mtg/database/cards.sqlite`) instead of
calling the Scryfall API for everything the bulk data supports. The database is built
automatically on first use (one-time ~540 MB download); `function:`/`otag:` (Tagger)
queries and any operator the local engine can't serve are routed to the live API
automatically. See the mtg-db skill and repo docs/adr/0001.

Two modes:
  Search:  python scryfall_search.py "<query>" [--limit N] [--order edhrec] [--json]
  Named:   python scryfall_search.py --named "Sol Ring" [--json]

Output (table by default) shows, for each card: name, mana value (mv), type, color
identity, and Cardmarket price in EUR (cheapest printing). Use --json for the full list.

Every search row shows CI (color identity) — ALWAYS check it matches your commander's
identity; use `id<=<identity>`, NOT `c:` (`c:b` matches off-identity multicolor cards).

Scryfall query syntax (see references/scryfall-syntax.md):
  id<=WB  color identity coverage      o:"sacrifice"  oracle text
  t:creature  type                     mv<=3  mana value
  function:ramp  curated tag (live API)  is:gamechanger  Game Changers list
  order=edhrec  popularity sort (default)
"""

import argparse
import json
import os
import sys

# Find the shared mtg_scryfall library. Plugin layout puts it at mtg-skills/lib
# (../../../lib from here); the other candidates let a manually-copied skill find a
# `lib/` (or `mtg_scryfall/`) dropped beside or just above it.
_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = None
for _rel in ("../../../lib", "../../lib", "../lib", "lib", "."):
    _cand = os.path.normpath(os.path.join(_HERE, _rel))
    if os.path.isdir(os.path.join(_cand, "mtg_scryfall")):
        _LIB = _cand
        break
if _LIB and _LIB not in sys.path:
    sys.path.insert(0, _LIB)

try:
    import mtg_scryfall
    from mtg_scryfall import api
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)


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
    ap.add_argument("--paths", action="store_true",
                    help="Print the resolved MTG workspace paths (decks/collection/database) "
                         "as JSON and exit. Honours $MTG_HOME; see SYNCING.md.")
    args = ap.parse_args()

    if args.paths:
        print(json.dumps(mtg_scryfall.workspace_paths(), indent=2))
        return

    if not args.query and not args.named:
        ap.error("provide a search query or --named NAME")

    # Build the local DB if missing (one-time), warn if stale; harmless if it then
    # routes to the live API anyway.
    mtg_scryfall.ensure_ready()

    try:
        if args.named:
            card = mtg_scryfall.named(args.named)
            cards = [card] if card else []
        else:
            cards = mtg_scryfall.search(args.query, limit=args.limit, order=args.order)
    except api.ScryfallUnreachable as e:
        print(f"ERROR: no local database and could not reach api.scryfall.com ({e}).",
              file=sys.stderr)
        print("Fall back to web_search + web_fetch of the Scryfall page, or note that "
              "prices/newest cards are unverified.", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(cards, indent=2, ensure_ascii=False))
    else:
        print_table(cards)


if __name__ == "__main__":
    main()
