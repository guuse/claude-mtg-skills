#!/usr/bin/env python3
"""mtgtop8_fetch.py — pull the live Standard metagame and real decklists from mtgtop8.com.

This is the source that makes Standard builds *meta-relevant and cohesive*: instead of
brewing a 60 from scratch, start from proven, current tournament lists. mtgtop8 serves
plain HTML to a descriptive User-Agent and exposes a plain-text decklist export, so —
unlike untapped.gg / mtggoldfish / mtgdecks / aetherhub (all Cloudflare-blocked) — it can
be fetched by a bot through the shared polite/retrying fetcher.

Usage:
    # 1) Current metagame — archetypes biggest-share first, with their archetype ids:
    python mtgtop8_fetch.py --meta

    # 2) Recent real decklists filed under one archetype (id from --meta):
    python mtgtop8_fetch.py --archetype 207 --limit 5

    # 3) One decklist by deck id (from --archetype), as importable lines:
    python mtgtop8_fetch.py --deck 860074

    # 4) One call: the metagame + a few real lists per top archetype (build backbone):
    python mtgtop8_fetch.py --top --archetypes 4 --per 2

Add --json to any mode for structured output. Standard ("ST") is the default format;
pass --format to target another (PI, MO, PAU, LE, VI, EDH, EXP, HISTORIC).

If mtgtop8 is unreachable the script prints a clear, non-fatal message and exits non-zero
— the calling skill then falls back to model meta knowledge (flagged unverified) or asks
the user to paste a netdeck. It never fabricates a decklist or a metagame share.
"""

import argparse
import json
import os
import sys

# Card names carry accents (é, ö, …) and we print em-dashes; force UTF-8 so output never
# mojibakes on a non-UTF-8 console (e.g. Windows cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # pragma: no cover - very old Pythons / odd streams
    pass

# Shared mtg_scryfall library discovery — identical shim to import_deck.py / scryfall_search.py.
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
    from mtg_scryfall import mtgtop8
    from mtg_scryfall.http import FetchError
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)


def _fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    print("mtgtop8 may be temporarily unreachable. Fall back to model meta knowledge "
          "(flagged UNVERIFIED) or ask the user to paste a netdeck — do not invent one.",
          file=sys.stderr)
    sys.exit(3)


def _print_deck(deck, as_json):
    if as_json:
        print(json.dumps(deck, indent=2, ensure_ascii=False))
        return
    header = deck.get("name") or f"deck {deck['deck_id']}"
    by = deck.get("player")
    ev = deck.get("event")
    tag = " — ".join(x for x in (header, by, ev) if x)
    print(f"# {tag}  (mtgtop8 d={deck['deck_id']})")
    for line in mtgtop8.to_import_lines(deck):
        print(line)


def main():
    ap = argparse.ArgumentParser(description="Fetch the live Standard metagame and decklists from mtgtop8.")
    ap.add_argument("--format", default="ST", help="mtgtop8 format code (default ST = Standard).")
    ap.add_argument("--meta", action="store_true", help="Print the current metagame breakdown.")
    ap.add_argument("--archetype", type=int, metavar="ID", help="List recent decklists for an archetype id.")
    ap.add_argument("--deck", type=int, metavar="ID", help="Print one decklist by deck id.")
    ap.add_argument("--top", action="store_true", help="Metagame + a few real lists per top archetype.")
    ap.add_argument("--archetypes", type=int, default=4, help="With --top: how many top archetypes (default 4).")
    ap.add_argument("--per", type=int, default=2, help="With --top: decklists per archetype (default 2).")
    ap.add_argument("--limit", type=int, default=8, help="With --archetype: max decklists to list (default 8).")
    ap.add_argument("--json", action="store_true", help="Structured JSON output.")
    args = ap.parse_args()

    if not (args.meta or args.archetype or args.deck or args.top):
        args.meta = True  # sensible default

    try:
        if args.deck:
            _print_deck(mtgtop8.fetch_deck(args.deck), args.json)
            return

        if args.archetype:
            decks = mtgtop8.fetch_archetype_decks(args.archetype, args.format, limit=args.limit)
            if args.json:
                print(json.dumps(decks, indent=2, ensure_ascii=False))
            else:
                print(f"# {len(decks)} recent decks under archetype a={args.archetype} ({args.format})")
                for d in decks:
                    by = f"  {d['player']}" if d['player'] else ""
                    ev = f"  @ {d['event']}" if d['event'] else ""
                    print(f"  d={d['deck_id']:<8} {d['name']}{by}{ev}")
                print("\nFetch a list with:  --deck <id>")
            return

        if args.top:
            data = mtgtop8.top_decklists(args.format, archetypes=args.archetypes, per_archetype=args.per)
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                for grp in data:
                    print(f"\n## {grp['archetype']} — {grp['share']}%  (a={grp['archetype_id']})")
                    for d in grp["decks"]:
                        _print_deck(d, False)
            return

        # --meta (default)
        meta = mtgtop8.fetch_meta(args.format)
        if args.json:
            print(json.dumps(meta, indent=2, ensure_ascii=False))
        else:
            print(f"# Current {args.format} metagame @ mtgtop8 (UNVERIFIED count, but real recent results)")
            for m in meta:
                print(f"  {m['share']:>5}%  {m['name']:<24} a={m['archetype_id']}")
            print("\nList an archetype's decks with:  --archetype <id>")
    except FetchError as e:
        status = f" (HTTP {e.status})" if e.status else ""
        _fail(f"mtgtop8 fetch failed{status}: {e}")


if __name__ == "__main__":
    main()
