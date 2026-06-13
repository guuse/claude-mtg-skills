#!/usr/bin/env python3
"""edhrec_fetch.py — proven Commander inclusions from EDHREC's JSON API.

EDHREC is the backbone for "what comparable decks actually run". This pulls a
commander's staples, high-synergy cards, themes, budget build, or its average
decklist from **json.edhrec.com** (never the Cloudflare-protected HTML) through the
shared polite/retrying fetcher in the mtg_scryfall library. Pair it with
scryfall_search.py, which prices and legality-checks the same cards from the local DB.

Usage:
    python edhrec_fetch.py "Atraxa, Praetors' Voice"            # staples + high-synergy + themes
    python edhrec_fetch.py "Atraxa, Praetors' Voice" --average  # the average ~100-card decklist
    python edhrec_fetch.py "Atraxa, Praetors' Voice" --budget   # the budget build's cards
    python edhrec_fetch.py "Atraxa, Praetors' Voice" --theme infect
    python edhrec_fetch.py "Atraxa, Praetors' Voice" --json     # full structured JSON

If EDHREC is unreachable or has no page (403/404/transient), the script exits non-zero
with a clear message naming the source — the calling skill then FALLS BACK to the local
Scryfall database (and the model's own knowledge), flagged as reduced confidence. It
never fabricates inclusions.
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
    from mtg_scryfall import edhrec
    from mtg_scryfall.http import FetchError
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)


def _print_cardlists(result):
    themes = result.get("themes") or []
    if themes:
        top = ", ".join(f"{t['value']} ({t['slug']})" for t in themes[:12])
        print(f"Themes: {top}\n")
    for header, cards in result.get("cardlists", {}).items():
        if not cards:
            continue
        print(f"== {header} ==")
        for c in cards[:25]:
            syn = c.get("synergy")
            syn_s = f"  syn {syn:+.2f}" if isinstance(syn, (int, float)) else ""
            print(f"  {c['name']}{syn_s}")
        print()


def main():
    ap = argparse.ArgumentParser(description="EDHREC proven-inclusion fetcher (JSON API).")
    ap.add_argument("commander", help="Commander name, e.g. \"Atraxa, Praetors' Voice\"")
    ap.add_argument("--average", action="store_true", help="Fetch the average ~100-card decklist.")
    ap.add_argument("--budget", action="store_true", help="Fetch the budget build's cards.")
    ap.add_argument("--theme", help="Fetch one theme's cards (slug from the themes list).")
    ap.add_argument("--json", action="store_true", help="Emit full JSON instead of a digest.")
    args = ap.parse_args()

    try:
        if args.average:
            result = edhrec.average_deck(args.commander)
        elif args.theme:
            result = edhrec.theme(args.commander, args.theme)
        elif args.budget:
            result = edhrec.budget(args.commander)
        else:
            result = edhrec.commander(args.commander)
    except FetchError as e:
        src = "EDHREC"
        status = f" (HTTP {e.status})" if e.status else ""
        print(f"ERROR: {src} fetch failed{status}: {e}", file=sys.stderr)
        print("FALL BACK to the local Scryfall database (scryfall_search.py) and known "
              "inclusions, and TELL THE USER EDHREC was unavailable so this build is "
              "lower-confidence on the 'proven inclusions' axis.", file=sys.stderr)
        sys.exit(3)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.average:
        print(f"# EDHREC average deck for {result['slug']} "
              f"({result.get('deck_size') or len(result['cards'])} cards)")
        for line in result["cards"]:
            print(line)
    else:
        _print_cardlists(result)


if __name__ == "__main__":
    main()
