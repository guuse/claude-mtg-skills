"""Deterministic decklist validators — the grader layer.

Pure checks on a finished import list: deck size, singleton/copy rules, color-identity
legality, and land count. They return structured `{ok, errors, warnings}` so they can be
unit-tested on fixture decklists today, used by the skills as a final quality gate, and
reused later as the exact grader for a model-in-the-loop behavioural eval.

Card lookups (for color identity and land counting) go through an injectable `lookup`
(defaulting to mtg_scryfall.named), so tests run with a dict-backed fake — no DB, no network.
"""

from .arena import LINE_RE, BASICS

# Cards exempt from the Commander singleton rule (may appear in any quantity).
# Basics are handled separately; this covers the well-known "any number of" cards.
ANY_NUMBER = {
    "relentless rats", "rat colony", "persistent petitioners", "dragon's approach",
    "seven dwarves", "shadowborn apostle", "slime against humanity", "templar knight",
    "nazgûl", "nazgul",
}


def _entries(text):
    """Yield (count, name) from an import list, skipping blanks and section headers."""
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.lower() in ("deck", "maindeck", "sideboard", "side", "commander", "companion"):
            continue
        m = LINE_RE.match(s)
        if m:
            yield int(m.group(1)), m.group(2).strip()


def _entries_with_sections(text):
    """Yield (count, name, section) — section in {'main','side','commander','companion'}."""
    section = "main"
    for line in text.splitlines():
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


def _resolve_lookup(lookup, db_path):
    if lookup is not None:
        return lookup
    from .query import named
    return lambda name: named(name, db_path=db_path)


def _identity(card):
    return set((card.get("color_identity") or "").replace("C", "").upper())


def validate_commander_import(text, commander=None, db_path=None, lookup=None):
    """Validate a 100-card singleton Commander import list.

    Errors (illegal decks): not exactly 100 cards; non-singleton non-basic cards;
    cards outside the commander's color identity (when `commander` is given).
    Warnings (smells, not illegal): land count outside the ~35–40 range.
    """
    entries = list(_entries(text))
    errors, warnings = [], []

    total = sum(c for c, _ in entries)
    if total != 100:
        errors.append(f"deck has {total} cards, expected exactly 100 (incl. commander)")

    for count, name in entries:
        low = name.lower()
        if count > 1 and low not in BASICS and low not in ANY_NUMBER:
            errors.append(f"non-singleton: {count}x {name} (Commander is singleton)")

    look = _resolve_lookup(lookup, db_path)

    if commander:
        cmd_card = look(commander)
        if not cmd_card:
            warnings.append(f"could not resolve commander {commander!r} to check color identity")
        else:
            allowed = _identity(cmd_card)
            for count, name in entries:
                card = look(name)
                if not card:
                    warnings.append(f"could not resolve {name!r} to verify color identity")
                    continue
                if not _identity(card) <= allowed:
                    ci = "".join(sorted(_identity(card))) or "C"
                    errors.append(f"off-identity: {name} ({ci}) not within "
                                  f"{''.join(sorted(allowed)) or 'C'}")

    # Land count (warning only): count cards whose type line includes 'Land'.
    if commander or db_path or lookup:
        lands = 0
        for count, name in entries:
            card = look(name)
            if card and "land" in (card.get("type_line") or "").lower():
                lands += count
        if lands and not (35 <= lands <= 40):
            warnings.append(f"{lands} lands — outside the usual ~37–38 (35–40) range")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "total": total}


def validate_arena_import(text, min_main=60, max_side=15, max_copies=4,
                          db_path=None, lookup=None):
    """Validate an MTG Arena (Standard) import list.

    Errors: main deck below `min_main`; sideboard above `max_side`; more than
    `max_copies` of any non-basic card (summed across main + sideboard).
    Warnings: main deck above `min_main` (legal but unusual for Standard).
    """
    errors, warnings = [], []
    main = side = 0
    copies = {}
    for count, name, section in _entries_with_sections(text):
        if section == "side":
            side += count
        else:
            main += count
        if name.lower() not in BASICS:
            copies[name] = copies.get(name, 0) + count

    if main < min_main:
        errors.append(f"main deck has {main} cards, below the {min_main}-card minimum")
    elif main > min_main:
        warnings.append(f"main deck has {main} cards (more than {min_main}; legal but unusual)")
    if side > max_side:
        errors.append(f"sideboard has {side} cards, over the {max_side}-card maximum")
    for name, n in copies.items():
        if n > max_copies:
            errors.append(f"{n}x {name} — over the {max_copies}-copy limit")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "main": main, "side": side}
