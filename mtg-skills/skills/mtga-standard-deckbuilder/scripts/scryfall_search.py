#!/usr/bin/env python3
"""
scryfall_search.py — Scryfall helper for building MTG Arena Standard decks.

Modes:
  Search:  python scryfall_search.py "<query>" [--limit N] [--raw] [--json]
           Defaults to Standard-legal + Arena-available; shows rarity per card.
           Use --raw to send the query without auto-adding 'legal:standard game:arena'.

  Named:   python scryfall_search.py --named "Sheoldred, the Apocalypse" [--json]

  Deck:    python scryfall_search.py --deck <arena-import>.txt [--tier N] [--colors wubrg]
           Parses an MTG Arena import list, looks up each card's rarity, tallies the
           wildcard cost by rarity (basics are free), and checks it against the tier caps.
           Reports the deck's color identity; with --colors it flags any card that is NOT
           castable in those colors (e.g. --colors b catches a B/U or B/R card in mono-black).

Search and named output include a CI (color identity) column — ALWAYS sanity-check that every
card's colors fit the deck. Note: `c:b` matches any card *containing* black (incl. multicolor);
to find cards castable in a given color use color identity `id<=b`, not `c:b`.

Wildcard tier caps (common, uncommon, rare, mythic):
  1: 8/4/0/0   2: 12/6/2/1   3: 16/10/6/3   4: 20/14/12/6   5: unlimited

Stdlib only — no pip install. If the network can't reach api.scryfall.com, the script
says so; fall back to web_search + web_fetch of the Scryfall page, and note that
legality/rarity/Arena-availability are unverified (Standard rotates, so flag this).
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

API = "https://api.scryfall.com"
HEADERS = {"User-Agent": "ClaudeStandardDeckBuilder/1.0 (skill)", "Accept": "application/json"}
DELAY = 0.1

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


def _get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _oracle(card):
    if card.get("oracle_text"):
        return card["oracle_text"]
    return " // ".join(f.get("oracle_text", "") for f in (card.get("card_faces") or []))


def _simplify(card):
    return {
        "name": card.get("name"),
        "mv": card.get("cmc"),
        "type_line": card.get("type_line"),
        "rarity": card.get("rarity"),
        "color_identity": "".join(card.get("color_identity") or []) or "C",
        "oracle_text": _oracle(card),
    }


def search(query, limit, raw):
    if not raw:
        query = f"{query} legal:standard game:arena"
    results, url = [], f"{API}/cards/search?" + urllib.parse.urlencode(
        {"q": query, "order": "edhrec", "unique": "cards"})
    while url and len(results) < limit:
        try:
            data = _get(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                break
            raise
        for c in data.get("data", []):
            results.append(_simplify(c))
            if len(results) >= limit:
                break
        url = data.get("next_page") if data.get("has_more") else None
        if url:
            time.sleep(DELAY)
    return results


def named(name):
    try:
        return _simplify(_get(f"{API}/cards/named?" + urllib.parse.urlencode({"exact": name})))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return _simplify(_get(f"{API}/cards/named?" + urllib.parse.urlencode({"fuzzy": name})))
        raise


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
        try:
            card = named(name)
        except urllib.error.HTTPError:
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

    try:
        if args.deck:
            cost_deck(args.deck, args.tier, args.colors)
            return
        if args.named:
            card = named(args.named)
            print(json.dumps(card, indent=2, ensure_ascii=False) if args.json else
                  f"{RARITY_LETTER.get(card['rarity'], '?')}  {card['name']}  ({card['rarity']})  "
                  f"MV{card['mv']:.0f}  [CI {card['color_identity']}]  {card['type_line']}")
            return
        if not args.query:
            ap.error("provide a query, --named NAME, or --deck FILE")
        cards = search(args.query, args.limit, args.raw)
        if args.json:
            print(json.dumps(cards, indent=2, ensure_ascii=False))
        else:
            print_table(cards)
    except urllib.error.URLError as e:
        print(f"ERROR: could not reach api.scryfall.com ({e}).", file=sys.stderr)
        print("Fall back to web_search + web_fetch of the Scryfall page. Note that legality, rarity, "
              "and Arena availability are then unverified (Standard rotates — flag this to the user).",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
