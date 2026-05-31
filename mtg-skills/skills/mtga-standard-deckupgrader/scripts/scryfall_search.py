#!/usr/bin/env python3
"""scryfall_search.py — card helper for building MTG Arena Standard decks.

Reads from the **local Scryfall database** (`.mtg/database/cards.sqlite`) instead of
calling the Scryfall API for everything the bulk data supports. The database is built
automatically on first use (one-time ~540 MB download); `function:`/`otag:` (Tagger)
queries and any operator the local engine can't serve route to the live API
automatically. See the mtg-scryfall-database skill and repo docs/adr/0001.

Modes:
  Search:  python scryfall_search.py "<query>" [--limit N] [--raw] [--json]
           Defaults to Standard-legal + Arena-available; shows rarity per card.
           Use --raw to send the query without auto-adding 'legal:standard game:arena'.
  Named:   python scryfall_search.py --named "Sheoldred, the Apocalypse" [--json]
  Deck:    python scryfall_search.py --deck <arena-import>.txt [--tier N] [--colors wubrg]
           Tallies wildcard cost by rarity (basics free) and checks the tier caps;
           with --colors, flags any card NOT castable in those colors.

Output includes a CI (color identity) column — sanity-check every card fits the deck.
Note: `c:b` matches any card *containing* black (incl. multicolor); use `id<=b`.

Wildcard tier caps (common, uncommon, rare, mythic):
  1: 8/4/0/0   2: 12/6/2/1   3: 16/10/6/3   4: 20/14/12/6   5: unlimited
"""

import argparse
import json
import os
import re
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

TIER_CAPS = {
    1: (8, 4, 0, 0),
    2: (12, 6, 2, 1),
    3: (16, 10, 6, 3),
    4: (20, 14, 12, 6),
    5: (float("inf"),) * 4,
}
RARITY_LETTER = {"common": "C", "uncommon": "U", "rare": "R", "mythic": "M"}
RARITY_INDEX = {"common": 0, "uncommon": 1, "rare": 2, "mythic": 3}
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes",
          "snow-covered plains", "snow-covered island", "snow-covered swamp",
          "snow-covered mountain", "snow-covered forest"}


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


LINE_RE = re.compile(r"^(\d+)\s+(.+?)(?:\s+\([^)]+\)\s+\S+)?\s*$")


def parse_deck(path):
    """Yield (count, name, section) from an Arena import file."""
    section = "main"
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            low = s.lower()
            if low in ("deck", "maindeck"):
                section = "main"; continue
            if low in ("sideboard", "side"):
                section = "side"; continue
            if low in ("commander", "companion"):
                section = low; continue
            m = LINE_RE.match(s)
            if m:
                yield int(m.group(1)), m.group(2).strip(), section


def cost_deck(path, tier, colors=None):
    totals = [0, 0, 0, 0]  # C, U, R, M
    main = side = 0
    unknown, basics = [], 0
    allowed = {ch for ch in (colors or "").upper() if ch in "WUBRG"}
    deck_colors, offcolor = set(), []  # union of identities; cards outside `allowed`
    for count, name, section in parse_deck(path):
        if section == "main":
            main += count
        elif section == "side":
            side += count
        if name.lower() in BASICS:
            basics += count
            continue
        card = mtg_scryfall.named(name)
        if not card:
            unknown.append(name); continue
        ci = (card.get("color_identity") or "").replace("C", "").upper()
        deck_colors |= set(ci)
        if colors and not set(ci) <= allowed:
            offcolor.append((name, ci or "C"))
        idx = RARITY_INDEX.get(card["rarity"])
        if idx is None:
            unknown.append(name); continue
        totals[idx] += count

    print(f"Deck size: main {main}, sideboard {side}, basics {basics} (free)\n")
    caps = TIER_CAPS.get(tier)
    labels = ["Common", "Uncommon", "Rare", "Mythic"]
    if caps:
        capstr = "/".join("∞" if c == float("inf") else str(c) for c in caps)
        print(f"Wildcard cost (Tier {tier} caps: {capstr}):")
    else:
        print("Wildcard cost:")
    # Rare/mythic are the hard gate (scarce wildcards, counted from zero).
    # Common/uncommon are soft (cheap, usually already owned) — reported, not failed.
    ok = True
    for i, lbl in enumerate(labels):
        mark = ""
        hard = i >= 2  # rare, mythic
        if caps:
            if totals[i] > caps[i]:
                if hard:
                    mark = f"  ✗ OVER cap by {totals[i] - caps[i]} (hard — swap for cheaper role-twins or trim copies)"
                    ok = False
                else:
                    mark = f"  • over the {caps[i]} target (soft — commons/uncommons are cheap and often already owned)"
            elif totals[i] == caps[i] and caps[i] != float("inf"):
                mark = "  ✓ (at cap)"
            else:
                mark = "  ✓"
        print(f"  {lbl:<9} {totals[i]:>3}{mark}")
    if caps:
        print("\n" + ("FITS the tier (rare/mythic within caps)." if ok
                      else "OVER the tier on rare/mythic — see ✗ rows; these are the binding wildcards."))

    di = "".join(c for c in "WUBRG" if c in deck_colors) or "C"
    print(f"\nDeck color identity (non-basics): {di}")
    if colors:
        allowed_str = "".join(c for c in "WUBRG" if c in allowed) or "C"
        if offcolor:
            print(f"COLOR CHECK  ✗ — {len(offcolor)} card(s) NOT castable in id<={allowed_str}:")
            for n, ci in offcolor:
                print(f"      {n}  (color identity {ci})")
            print("  Fix: replace with on-color cards, or add the missing colors to the mana base.")
        else:
            print(f"COLOR CHECK  ✓ — every card is castable within {allowed_str}.")
    else:
        print("(Tip: pass --colors <wubrg> to flag any card you can't cast, e.g. --colors b for mono-black.)")
    if unknown:
        print("\nCould not resolve (check spelling / Arena availability): " + ", ".join(unknown))


def main():
    ap = argparse.ArgumentParser(description="Scryfall helper for MTG Arena Standard decks.")
    ap.add_argument("query", nargs="?", help="Scryfall query (auto-adds 'legal:standard game:arena').")
    ap.add_argument("--named", help="Exact/fuzzy single-card lookup (shows rarity).")
    ap.add_argument("--deck", help="Arena import .txt to tally wildcard cost.")
    ap.add_argument("--tier", type=int, choices=[1, 2, 3, 4, 5], help="Tier to check --deck against.")
    ap.add_argument("--colors", help="With --deck: WUBRG letters of the deck's intended colors; flags any "
                    "card not castable in that color identity (e.g. --colors b for mono-black).")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--raw", action="store_true", help="Don't auto-add Standard/Arena filters.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not (args.deck or args.named or args.query):
        ap.error("provide a query, --named NAME, or --deck FILE")

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
