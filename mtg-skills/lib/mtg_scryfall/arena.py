"""MTG Arena wildcard accounting — shared, pure computation.

The *numbers and facts* both Arena skills must agree on live here: the wildcard tier
cap table, Arena-import parsing, and the wildcard tally + cap/color evaluation. The
*rendering* of a tally (the ✓/✗ lines, tips, color-check wording) stays in each skill's
wrapper, since that's presentation and may legitimately differ between build and upgrade.

`tally_wildcards` takes an injectable `lookup` (defaulting to mtg_scryfall.named), so it's
testable with a dict-backed fake — no database and no network.
"""

import re

# Wildcard tier caps as (common, uncommon, rare, mythic).
TIER_CAPS = {
    1: (8, 4, 0, 0),
    2: (12, 6, 2, 1),
    3: (16, 10, 6, 3),
    4: (20, 14, 12, 6),
    5: (float("inf"),) * 4,
}
RARITY_INDEX = {"common": 0, "uncommon": 1, "rare": 2, "mythic": 3}
RARITY_LABELS = ["Common", "Uncommon", "Rare", "Mythic"]
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes",
          "snow-covered plains", "snow-covered island", "snow-covered swamp",
          "snow-covered mountain", "snow-covered forest"}

# "4 Card Name" optionally followed by an Arena set annotation like "(DMU) 107".
LINE_RE = re.compile(r"^(\d+)\s+(.+?)(?:\s+\([^)]+\)\s+\S+)?\s*$")


def parse_deck(path):
    """Yield (count, name, section) from an MTG Arena import file.

    Sections: 'main', 'side', 'commander', 'companion'. Lines like "Deck",
    "Sideboard", etc. switch the active section.
    """
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


def tally_wildcards(entries, tier=None, lookup=None, allowed_colors=None):
    """Compute the wildcard cost of a deck. Pure given `lookup`.

    `entries`    : iterable of (count, name, section) — e.g. from parse_deck().
    `tier`       : 1–5 to evaluate against TIER_CAPS, or None for totals only.
    `lookup`     : name -> card dict (with 'rarity' and 'color_identity'), or None.
                   Defaults to mtg_scryfall.named. A name that resolves to None is
                   reported under 'unknown'.
    `allowed_colors` : WUBRG letters the deck means to cast; any non-basic whose color
                   identity isn't a subset is flagged in 'offcolor'.

    Returns a dict (see module docstring) with totals, per-rarity rows, fit flag,
    deck color identity, off-color cards, and unresolved names. No printing.
    """
    if lookup is None:
        from .query import named as lookup  # lazy: avoid import cycle at module load

    totals = [0, 0, 0, 0]
    main = side = basics = 0
    unknown = []
    allowed = {ch for ch in (allowed_colors or "").upper() if ch in "WUBRG"}
    deck_colors, offcolor = set(), []

    for count, name, section in entries:
        if section == "main":
            main += count
        elif section == "side":
            side += count
        if name.lower() in BASICS:
            basics += count
            continue
        card = lookup(name)
        if not card:
            unknown.append(name); continue
        ci = (card.get("color_identity") or "").replace("C", "").upper()
        deck_colors |= set(ci)
        if allowed_colors and not set(ci) <= allowed:
            offcolor.append((name, ci or "C"))
        idx = RARITY_INDEX.get(card.get("rarity"))
        if idx is None:
            unknown.append(name); continue
        totals[idx] += count

    caps = TIER_CAPS.get(tier) if tier is not None else None
    rows = []
    fits = None
    if caps is not None:
        fits = True
        for i, label in enumerate(RARITY_LABELS):
            cap = caps[i]
            over = max(0, totals[i] - cap) if cap != float("inf") else 0
            hard = i >= 2  # rare, mythic are the binding wildcards
            if over and hard:
                fits = False
            rows.append({
                "label": label, "rarity": ["common", "uncommon", "rare", "mythic"][i],
                "count": totals[i], "cap": cap, "over": over, "hard": hard,
                "at_cap": cap != float("inf") and totals[i] == cap,
            })
    else:
        rows = [{"label": RARITY_LABELS[i], "rarity": ["common", "uncommon", "rare", "mythic"][i],
                 "count": totals[i], "cap": None, "over": 0, "hard": i >= 2, "at_cap": False}
                for i in range(4)]

    return {
        "main": main, "side": side, "basics": basics,
        "totals": totals, "tier": tier, "caps": caps, "rows": rows, "fits": fits,
        "deck_color_identity": "".join(c for c in "WUBRG" if c in deck_colors) or "C",
        "allowed": ("".join(c for c in "WUBRG" if c in allowed) or "C") if allowed_colors else None,
        "offcolor": offcolor,
        "unknown": unknown,
    }
