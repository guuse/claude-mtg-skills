#!/usr/bin/env python3
"""analyze_deck.py — ingest a Commander decklist and emit the objective stats a
deck rating is built from.

This does the *measuring*, not the *judging*. It looks every card up in the local
Scryfall database (see scryfall_search.py / the mtg-db skill) and reports the hard
numbers: card count, land count, mana curve, average mana value, EDHREC-rank
distribution (the staple signal), Game Changer count, color-identity outliers, total
price, and the raw per-card data (including full Oracle text and type line) so the
skill can read wording and score synergy. The star rating itself — performance,
synergy density, staples, bracket fit — is the model's job, using this data plus
references/synergy.md and references/brackets.md.

Usage:
    python analyze_deck.py <decklist.txt> [--commander "Name"] [--identity BG] [--json]

Input format: one card per line, tolerant of the common exports —
    "1 Sol Ring", "1x Sol Ring", "Sol Ring", "1 Sol Ring (C21) 263", "1 Sol Ring *CMDR*"
Section headers ("Commander", "Deck", "Sideboard"), blank lines, and # comments are
handled. A card on a line under a "Commander" header (or marked *CMDR*), or passed via
--commander, is recorded as the commander and used to derive color identity if
--identity is not given.

Output: a human-readable summary by default; --json emits the full structure (per-card
records + aggregates) for the skill to consume.
"""

import argparse
import json
import os
import re
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
    import mtg_scryfall
    from mtg_scryfall import api
    from mtg_scryfall.arena import BASICS
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)

# EDHREC-rank thresholds for the "staple" signal (lower rank = more widely played).
PREMIER_RANK = 500     # premier format staples (Sol Ring territory)
STAPLE_RANK = 1500     # widely-played staples
PLAYED_RANK = 4000     # commonly played

# A line like "1 Sol Ring", "1x Sol Ring", or bare "Sol Ring", with an optional
# trailing set/collector tag "(C21) 263" or marker "*CMDR*"/"*F*".
_LINE_RE = re.compile(
    r"^\s*(?:(?P<count>\d+)\s*[xX]?\s+)?"        # optional leading count / "Nx"
    r"(?P<name>.+?)"                              # card name (non-greedy)
    r"(?:\s+\((?P<set>[^)]+)\)\s*\S*)?"           # optional "(SET) 123"
    r"(?:\s+\*(?P<marker>[^*]+)\*)?\s*$"          # optional "*CMDR*" / "*F*"
)
_HEADERS = {"deck", "maindeck", "main", "sideboard", "side", "commander",
            "companion", "maybeboard", "tokens"}


def parse_lines(path):
    """Yield (count, name, is_commander) from a tolerant Commander-list parse."""
    section = "main"
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            s = raw.strip()
            if not s or s.startswith("#") or s.startswith("//"):
                continue
            low = s.lower().rstrip(":")
            if low in _HEADERS:
                section = low
                continue
            if low.startswith("sb:"):  # Moxfield sideboard prefix — skip
                continue
            m = _LINE_RE.match(s)
            if not m:
                continue
            count = int(m.group("count")) if m.group("count") else 1
            name = m.group("name").strip()
            marker = (m.group("marker") or "").lower()
            is_cmd = section == "commander" or marker in ("cmdr", "commander")
            yield count, name, is_cmd


def _ci_letters(s):
    return set((s or "").replace(" ", "").upper()) & set("WUBRG")


def analyze(path, commander=None, identity=None):
    mtg_scryfall.ensure_ready()

    cards = []        # per-card records
    unfound = []      # names not found in the DB
    commanders = []   # detected commander name(s)

    for count, name, is_cmd in parse_lines(path):
        try:
            card = mtg_scryfall.named(name)
        except api.ScryfallUnreachable:
            card = None
        if not card:
            unfound.append(name)
            continue
        rec = {
            "name": card["name"], "count": count,
            "mv": card.get("mv"), "type_line": card.get("type_line") or "",
            "color_identity": card.get("color_identity") or "",
            "edhrec_rank": card.get("edhrec_rank"),
            "game_changer": bool(card.get("game_changer")),
            "eur": card.get("eur"), "keywords": card.get("keywords"),
            "oracle_text": card.get("oracle_text") or "",
            "is_commander": is_cmd,
        }
        cards.append(rec)
        if is_cmd:
            commanders.append(card["name"])

    if commander and commander not in commanders:
        commanders.append(commander)

    total = sum(c["count"] for c in cards)
    lands = [c for c in cards if "land" in c["type_line"].lower()]
    land_count = sum(c["count"] for c in lands)
    nonland = [c for c in cards if c not in lands]

    # Mana curve over nonland cards (by mana value bucket 0..6, 7+).
    curve = {str(i): 0 for i in range(7)}
    curve["7+"] = 0
    mv_vals = []
    for c in nonland:
        mv = c["mv"]
        if mv is None:
            continue
        mv_vals.append(mv * c["count"])
        bucket = "7+" if mv >= 7 else str(int(mv))
        curve[bucket] += c["count"]
    nonland_castable = sum(c["count"] for c in nonland if c["mv"] is not None)
    avg_mv = round(sum(mv_vals) / nonland_castable, 2) if nonland_castable else None

    # Staple signal from EDHREC rank.
    ranks = [c["edhrec_rank"] for c in cards if c["edhrec_rank"] is not None]
    ranks_sorted = sorted(ranks)
    median_rank = ranks_sorted[len(ranks_sorted) // 2] if ranks_sorted else None
    staples = {
        "ranked": len(ranks),
        "unranked": sum(c["count"] for c in cards) - sum(
            c["count"] for c in cards if c["edhrec_rank"] is not None),
        "premier_le500": sum(c["count"] for c in cards
                             if c["edhrec_rank"] is not None and c["edhrec_rank"] <= PREMIER_RANK),
        "staple_le1500": sum(c["count"] for c in cards
                             if c["edhrec_rank"] is not None and c["edhrec_rank"] <= STAPLE_RANK),
        "played_le4000": sum(c["count"] for c in cards
                             if c["edhrec_rank"] is not None and c["edhrec_rank"] <= PLAYED_RANK),
        "median_rank": median_rank,
    }

    game_changers = sorted({c["name"] for c in cards if c["game_changer"]})

    # Color identity: union across the deck, and outliers vs. the commander identity.
    deck_ci = set()
    for c in cards:
        deck_ci |= _ci_letters(c["color_identity"])
    if not identity and commanders:
        cmd_ci = set()
        for c in cards:
            if c["is_commander"] or c["name"] in commanders:
                cmd_ci |= _ci_letters(c["color_identity"])
        identity = "".join(x for x in "WUBRG" if x in cmd_ci) if cmd_ci else None
    id_letters = _ci_letters(identity) if identity else None
    off_identity = []
    if id_letters is not None:
        for c in cards:
            extra = _ci_letters(c["color_identity"]) - id_letters
            if extra:
                off_identity.append(f"{c['name']} ({c['color_identity']})")

    total_eur = round(sum(float(c["eur"]) * c["count"]
                          for c in cards if c["eur"]), 2)

    return {
        "deck": {
            "total_cards": total,
            "lands": land_count,
            "nonland": total - land_count,
            "avg_mv_nonland": avg_mv,
            "curve": curve,
            "total_eur": total_eur,
            "color_identity": "".join(x for x in "WUBRG" if x in deck_ci) or "C",
            "commander_identity": identity,
            "commanders": commanders,
        },
        "game_changers": game_changers,
        "game_changer_count": len(game_changers),
        "staples": staples,
        "off_identity": off_identity,
        "unfound": unfound,
        "cards": cards,
    }


def print_summary(a):
    d = a["deck"]
    print(f"Commander(s): {', '.join(d['commanders']) or '(not identified)'}"
          f"   identity: {d['commander_identity'] or '?'}")
    print(f"Total cards: {d['total_cards']}   Lands: {d['lands']}   "
          f"Nonland: {d['nonland']}   Avg MV (nonland): {d['avg_mv_nonland']}")
    print(f"Deck color identity: {d['color_identity']}   "
          f"Total price: EUR {d['total_eur']} (Cardmarket, via Scryfall)")
    print("Mana curve (nonland): " + "  ".join(
        f"{k}:{a['deck']['curve'][k]}" for k in
        ["0", "1", "2", "3", "4", "5", "6", "7+"]))
    s = a["staples"]
    print(f"Staple signal (EDHREC rank): premier(<=500) {s['premier_le500']}  "
          f"staple(<=1500) {s['staple_le1500']}  played(<=4000) {s['played_le4000']}  "
          f"median {s['median_rank']}  unranked {s['unranked']}")
    print(f"Game Changers: {a['game_changer_count']}"
          + (f" — {', '.join(a['game_changers'])}" if a["game_changers"] else ""))
    if a["off_identity"]:
        print(f"OFF color identity ({len(a['off_identity'])}): "
              + ", ".join(a["off_identity"]))
    if a["unfound"]:
        print(f"NOT FOUND in database ({len(a['unfound'])}): "
              + ", ".join(a["unfound"]))
    print("\n(Per-card data incl. Oracle text available with --json — read it to score "
          "synergy and apply the star rubric; see references/synergy.md & brackets.md.)")


def main():
    ap = argparse.ArgumentParser(
        description="Ingest a Commander decklist and emit the stats a star rating is built from.")
    ap.add_argument("deckfile", help="Path to the decklist (one card per line).")
    ap.add_argument("--commander", help="Commander name, if not marked in the list.")
    ap.add_argument("--identity", help="Color identity letters (e.g. BG) to vet legality against.")
    ap.add_argument("--json", action="store_true", help="Emit full JSON instead of a summary.")
    args = ap.parse_args()

    if not os.path.isfile(args.deckfile):
        ap.error(f"decklist not found: {args.deckfile}")

    try:
        a = analyze(args.deckfile, commander=args.commander, identity=args.identity)
    except api.ScryfallUnreachable as e:
        print(f"ERROR: no local database and could not reach api.scryfall.com ({e}).",
              file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    else:
        print_summary(a)


if __name__ == "__main__":
    main()
