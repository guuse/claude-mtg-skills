"""Tests for the decklist validators (layer B) on fixture lists. No network.

The validators are deterministic and use an injectable lookup, so a dict-backed fake
stands in for the database.
"""

import os
import sys
import unittest

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import validate  # noqa: E402


# Fake card data: a mono-red commander deck. Everything is identity R, type Creature,
# except Mountain (a basic land) — enough to exercise identity + land-count checks.
def fake_lookup(name):
    low = name.lower()
    if low == "krenko, mob boss":
        return {"color_identity": "R", "type_line": "Legendary Creature — Goblin Warrior"}
    if low == "mountain":
        return {"color_identity": "R", "type_line": "Basic Land — Mountain"}
    if low == "llanowar elves":  # deliberately green — off-identity for a red commander
        return {"color_identity": "G", "type_line": "Creature — Elf Druid"}
    return {"color_identity": "R", "type_line": "Creature — Goblin"}


def commander_deck(nonland=62, mountains=37, dup=False, offcolor=False, total_override=None):
    """Build a Commander import list: 1 commander + N basics + unique spells = 100."""
    lines = ["1 Krenko, Mob Boss", f"{mountains} Mountain"]
    spells = nonland
    if dup:
        lines.append("2 Goblin Bushwhacker")  # non-singleton
        spells -= 2
    if offcolor:
        lines.append("1 Llanowar Elves")      # green in a red deck
        spells -= 1
    for i in range(spells):
        lines.append(f"1 Goblin Number {i}")
    return "\n".join(lines)


class CommanderValidatorTests(unittest.TestCase):
    def test_valid_deck(self):
        text = commander_deck(nonland=62, mountains=37)  # 1+37+62 = 100, 37 lands
        r = validate.validate_commander_import(text, commander="Krenko, Mob Boss",
                                               lookup=fake_lookup)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["total"], 100)
        self.assertEqual(r["warnings"], [])

    def test_wrong_count(self):
        text = commander_deck(nonland=61, mountains=37)  # 99
        r = validate.validate_commander_import(text, lookup=fake_lookup)
        self.assertFalse(r["ok"])
        self.assertTrue(any("expected exactly 100" in e for e in r["errors"]))

    def test_non_singleton(self):
        text = commander_deck(nonland=62, mountains=37, dup=True)  # still 100
        r = validate.validate_commander_import(text, lookup=fake_lookup)
        self.assertFalse(r["ok"])
        self.assertTrue(any("non-singleton" in e for e in r["errors"]))

    def test_off_identity(self):
        text = commander_deck(nonland=62, mountains=37, offcolor=True)
        r = validate.validate_commander_import(text, commander="Krenko, Mob Boss",
                                               lookup=fake_lookup)
        self.assertFalse(r["ok"])
        self.assertTrue(any("off-identity: Llanowar Elves" in e for e in r["errors"]))

    def test_land_count_warning(self):
        text = commander_deck(nonland=70, mountains=29)  # 1+29+70=100, only 29 lands
        r = validate.validate_commander_import(text, commander="Krenko, Mob Boss",
                                               lookup=fake_lookup)
        self.assertTrue(r["ok"])  # legal, just a smell
        self.assertTrue(any("lands" in w for w in r["warnings"]))


class ArenaValidatorTests(unittest.TestCase):
    def _deck(self, main_n=60, side_n=0, over_copies=False):
        lines = ["Deck"]
        if over_copies:
            lines.append("5 Cut Down")          # over the 4-copy limit
            main_n -= 5
        # fill the main with basics (exempt from the copy limit)
        lines.append(f"{main_n} Mountain")
        if side_n:
            lines.append("Sideboard")
            lines.append(f"{side_n} Duress")
        return "\n".join(lines)

    def test_valid(self):
        r = validate.validate_arena_import(self._deck(60, 0))
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["main"], 60)

    def test_below_minimum(self):
        r = validate.validate_arena_import(self._deck(58, 0))
        self.assertFalse(r["ok"])
        self.assertTrue(any("below the 60-card minimum" in e for e in r["errors"]))

    def test_oversized_sideboard(self):
        r = validate.validate_arena_import(self._deck(60, 16))
        self.assertFalse(r["ok"])
        self.assertTrue(any("sideboard" in e for e in r["errors"]))

    def test_over_copy_limit(self):
        r = validate.validate_arena_import(self._deck(60, 0, over_copies=True))
        self.assertFalse(r["ok"])
        self.assertTrue(any("Cut Down" in e and "4-copy" in e for e in r["errors"]))

    def test_oversized_main_is_warning(self):
        r = validate.validate_arena_import(self._deck(75, 0))
        self.assertTrue(r["ok"])
        self.assertTrue(any("more than 60" in w for w in r["warnings"]))


if __name__ == "__main__":
    unittest.main()
