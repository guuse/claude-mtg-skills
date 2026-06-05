#!/usr/bin/env python3
"""scryfall_search.py — card helper for building MTG Arena Standard decks.

Reads from the **local Scryfall database** (`.mtg/database/cards.sqlite`) instead of
calling the Scryfall API for everything the bulk data supports. The database is built
automatically on first use (one-time ~540 MB download); `function:`/`otag:` (Tagger)
queries and any operator the local engine can't serve route to the live API
automatically. See the mtg-db skill and repo docs/adr/0001.

Modes:
  Search:  python scryfall_search.py "<query>" [--limit N] [--raw] [--json]
           Defaults to Standard-legal + Arena-available; shows rarity per card.
           Use --raw to send the query without auto-adding 'legal:standard game:arena'.
  Named:   python scryfall_search.py --named "Sheoldred, the Apocalypse" [--json]
  Deck:    python scryfall_search.py --deck <arena-import>.txt [--tier N] [--colors wubrg]
           Tallies wildcard cost by rarity (basics free) and checks the tier caps;
           with --colors, flags any card NOT castable in those colors.
  Collect: python scryfall_search.py --collection [PATH]
           Parse the user's owned-card export — .txt, .csv, or .json — into a normalized
           "<count> Card Name" list. With no PATH, auto-finds it in the workspace's
           collection/ folder. Use this to load the inventory before building.

Output includes a CI (color identity) column — sanity-check every card fits the deck.
Note: `c:b` matches any card *containing* black (incl. multicolor); use `id<=b`.

Wildcard tier caps (common, uncommon, rare, mythic):
  1: 8/4/0/0   2: 12/6/2/1   3: 16/10/6/3   4: 20/14/12/6   5: unlimited
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

# Wildcard tier caps, Arena-import parsing, and the tally math are shared, tested logic
# in mtg_scryfall.arena. Display glyphs and the rendering below stay local (presentation).
RARITY_LETTER = {"common": "C", "uncommon": "U", "rare": "R", "mythic": "M"}


def search(query, limit, raw):
    if not raw:
        query = f"{query} legal:standard game:arena"
    return mtg_scryfall.search(query, limit=limit, order="edhrec")


def print_table(cards):
    if not cards:
        print("No cards found.")
        return
    print(f"{'R':<2} {'CI':<5} {'MV':>3}  {'NAME':<34} TYPE")
    print("-" * 84)
    for c in cards:
        rl = RARITY_LETTER.get(c["rarity"], "?")
        mv = "" if c["mv"] is None else f"{c['mv']:.0f}"
        ci = c.get("color_identity") or "C"
        print(f"{rl:<2} {ci:<5} {mv:>3}  {(c['name'] or '')[:34]:<34} {(c['type_line'] or '')[:28]}")
    print("-" * 84)
    print(f"{len(cards)} cards (R = rarity: C/U/R/M; CI = color identity — must fit your deck's colors)")


def cost_deck(path, tier, colors=None):
    """Tally the deck's wildcard cost (shared lib) and render the report."""
    result = mtg_scryfall.tally_wildcards(
        mtg_scryfall.parse_deck(path), tier, allowed_colors=colors)
    render_wildcards(result)


def show_collection(path, as_json=False):
    """Load the owned-card collection (txt/csv/json) and print it normalized."""
    try:
        result = mtg_scryfall.load_collection(path or None)
    except (ValueError, OSError) as e:
        print(f"ERROR reading collection: {e}", file=sys.stderr)
        sys.exit(1)
    if result is None:
        cdir = mtg_scryfall.workspace_paths()["paths"]["collection"]
        print(f"No collection file found in {cdir}/ . Drop a .txt, .csv, or .json export "
              "there (see the skill's collection section).", file=sys.stderr)
        sys.exit(1)
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print(f"Collection: {result['total']} cards, {result['unique']} unique "
          f"(from {os.path.basename(result['path'])}, parsed as {result['format']})")
    if result["note"]:
        print(f"NOTE: {result['note']}")
    print("-" * 48)
    for name, count in sorted(result["cards"].items()):
        print(f"{count} {name}")


def render_wildcards(result):
    """Render a tally_wildcards() result. Presentation only — the numbers are the lib's."""
    print(f"Deck size: main {result['main']}, sideboard {result['side']}, "
          f"basics {result['basics']} (free)\n")
    caps = result["caps"]
    if caps:
        capstr = "/".join("∞" if c == float("inf") else str(c) for c in caps)
        print(f"Wildcard cost (Tier {result['tier']} caps: {capstr}):")
    else:
        print("Wildcard cost:")
    # Rare/mythic are the hard gate (scarce wildcards); common/uncommon are soft.
    for row in result["rows"]:
        mark = ""
        if caps:
            if row["over"] and row["hard"]:
                mark = f"  ✗ OVER cap by {row['over']} (hard — swap for cheaper role-twins or trim copies)"
            elif row["over"]:
                mark = f"  • over the {row['cap']} target (soft — commons/uncommons are cheap and often already owned)"
            elif row["at_cap"]:
                mark = "  ✓ (at cap)"
            else:
                mark = "  ✓"
        print(f"  {row['label']:<9} {row['count']:>3}{mark}")
    if caps:
        print("\n" + ("FITS the tier (rare/mythic within caps)." if result["fits"]
                      else "OVER the tier on rare/mythic — see ✗ rows; these are the binding wildcards."))

    print(f"\nDeck color identity (non-basics): {result['deck_color_identity']}")
    if result["allowed"] is not None:
        if result["offcolor"]:
            print(f"COLOR CHECK  ✗ — {len(result['offcolor'])} card(s) NOT castable in id<={result['allowed']}:")
            for n, ci in result["offcolor"]:
                print(f"      {n}  (color identity {ci})")
            print("  Fix: replace with on-color cards, or add the missing colors to the mana base.")
        else:
            print(f"COLOR CHECK  ✓ — every card is castable within {result['allowed']}.")
    else:
        print("(Tip: pass --colors <wubrg> to flag any card you can't cast, e.g. --colors b for mono-black.)")
    if result["unknown"]:
        print("\nCould not resolve (check spelling / Arena availability): " + ", ".join(result["unknown"]))


def main():
    ap = argparse.ArgumentParser(description="Scryfall helper for MTG Arena Standard decks.")
    ap.add_argument("query", nargs="?", help="Scryfall query (auto-adds 'legal:standard game:arena').")
    ap.add_argument("--named", help="Exact/fuzzy single-card lookup (shows rarity).")
    ap.add_argument("--deck", help="Arena import .txt to tally wildcard cost.")
    ap.add_argument("--tier", type=int, choices=[1, 2, 3, 4, 5], help="Tier to check --deck against.")
    ap.add_argument("--colors", help="With --deck: WUBRG letters of the deck's intended colors; flags any "
                    "card not castable in that color identity (e.g. --colors b for mono-black).")
    ap.add_argument("--collection", nargs="?", const="", metavar="PATH",
                    help="Parse the owned-card export (.txt/.csv/.json) into a normalized list. "
                         "Bare flag auto-finds it in the workspace's collection/ folder.")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--raw", action="store_true", help="Don't auto-add Standard/Arena filters.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--paths", action="store_true",
                    help="Print the resolved MTG workspace paths (decks/collection/database) "
                         "as JSON and exit. Honours $MTG_HOME; see SYNCING.md.")
    args = ap.parse_args()

    if args.paths:
        print(json.dumps(mtg_scryfall.workspace_paths(), indent=2))
        return

    # Collection parsing is pure file I/O — no database needed, so handle it before ensure_ready.
    if args.collection is not None:
        show_collection(args.collection, args.json)
        return

    if not (args.deck or args.named or args.query):
        ap.error("provide a query, --named NAME, --deck FILE, or --collection [PATH]")

    # Build the local DB if missing (one-time), warn if stale.
    mtg_scryfall.ensure_ready()

    try:
        if args.deck:
            cost_deck(args.deck, args.tier, args.colors)
            return
        if args.named:
            card = mtg_scryfall.named(args.named)
            if not card:
                print(f"Card not found: {args.named}", file=sys.stderr)
                sys.exit(1)
            print(json.dumps(card, indent=2, ensure_ascii=False) if args.json else
                  f"{RARITY_LETTER.get(card['rarity'], '?')}  {card['name']}  ({card['rarity']})  "
                  f"MV{card['mv']:.0f}  [CI {card['color_identity']}]  {card['type_line']}")
            return
        cards = search(args.query, args.limit, args.raw)
        if args.json:
            print(json.dumps(cards, indent=2, ensure_ascii=False))
        else:
            print_table(cards)
    except api.ScryfallUnreachable as e:
        print(f"ERROR: no local database and could not reach api.scryfall.com ({e}).",
              file=sys.stderr)
        print("Fall back to web_search + web_fetch of the Scryfall page. Note that legality, rarity, "
              "and Arena availability are then unverified (Standard rotates — flag this to the user).",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
