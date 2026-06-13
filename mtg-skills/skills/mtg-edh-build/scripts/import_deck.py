#!/usr/bin/env python3
"""import_deck.py — pull a decklist from an Archidekt or Moxfield URL.

When the user gives a deck link instead of pasting the list, fetch it from the site's
JSON API (never by scraping the Cloudflare-protected HTML) through the shared
polite/retrying fetcher. Prints a clean "<qty> <name>" list — commander(s) first — ready
to save to a temp file and feed to analyze_deck.py / the build flow.

Usage:
    python import_deck.py https://moxfield.com/decks/m8dC4ckt20eR2uXDyzlwlg
    python import_deck.py https://archidekt.com/decks/7000000/my-deck
    python import_deck.py 7000000            # bare Archidekt id
    python import_deck.py --json <url>       # full normalised JSON

If the deck is private or the site is unreachable (403/404/transient), the script exits
non-zero with a clear message naming the site — the calling skill then asks the user to
**paste the list** instead. It never fabricates a decklist.
"""

import argparse
import json
import os
import sys

# Shared mtg_scryfall library discovery — identical shim to scryfall_search.py.
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
    from mtg_scryfall import decks
    from mtg_scryfall.http import FetchError
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description="Import an Archidekt/Moxfield decklist via JSON API.")
    ap.add_argument("ref", help="Deck URL (Archidekt or Moxfield) or a bare deck id.")
    ap.add_argument("--json", action="store_true", help="Emit the full normalised JSON.")
    args = ap.parse_args()

    try:
        source, _ = decks.parse_deck_ref(args.ref)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        deck = decks.fetch_deck(args.ref)
    except FetchError as e:
        status = f" (HTTP {e.status})" if e.status else ""
        print(f"ERROR: {source} fetch failed{status}: {e}", file=sys.stderr)
        print(f"The deck may be private, or {source} may be unreachable. ASK THE USER "
              "TO PASTE the decklist instead — do not invent one.", file=sys.stderr)
        sys.exit(3)

    if args.json:
        print(json.dumps(deck, indent=2, ensure_ascii=False))
        return

    title = deck.get("name") or "(untitled)"
    fmt = deck.get("format") or "?"
    print(f"# {title} — {deck['source']} ({fmt})")
    for line in decks.to_import_lines(deck):
        print(line)


if __name__ == "__main__":
    main()
