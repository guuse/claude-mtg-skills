"""Tier-2 deterministic tests (no network, no bulk download).

Covers the areas the engine smoke test (test_mtg_scryfall.py) leaves out:
- Arena wildcard math + import parsing (mtg_scryfall.arena)
- the streaming bulk-JSON parser at awkward buffer boundaries
- database status / staleness boundary
- simplify_api (via a canned card dict — no Scryfall call)
- additional query operators (c:, id>=, guild nicknames, pow, rarity abbrev,
  t:permanent, nested or/parens, kw:)
"""

import json
import os
import sys
import tempfile
import unittest

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import arena, build, query, status  # noqa: E402

# Shared crafted DB for the operator tests (a few colors/types/keywords/rarities).
from test_mtg_scryfall import SAMPLE  # reuse the same sample cards  # noqa: E402


# --------------------------------------------------------------------------- #
# Arena wildcard math + parsing                                               #
# --------------------------------------------------------------------------- #

_FAKE = {
    "Sheoldred, the Apocalypse": {"rarity": "mythic", "color_identity": "B"},
    "Llanowar Elves": {"rarity": "common", "color_identity": "G"},
    "Cut Down": {"rarity": "uncommon", "color_identity": "B"},
    "The Wandering Emperor": {"rarity": "mythic", "color_identity": "W"},
}


def _lookup(name):
    return _FAKE.get(name)


class ArenaTests(unittest.TestCase):
    def test_parse_deck_sections_and_annotations(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "arena.txt")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("Deck\n"
                     "4 Llanowar Elves (DMU) 168\n"   # Arena set annotation must be stripped
                     "2 Cut Down\n"
                     "\n"
                     "Sideboard\n"
                     "3 Sheoldred, the Apocalypse\n")
        got = list(arena.parse_deck(p))
        self.assertEqual(got, [
            (4, "Llanowar Elves", "main"),
            (2, "Cut Down", "main"),
            (3, "Sheoldred, the Apocalypse", "side"),
        ])

    def test_tally_counts_and_caps(self):
        entries = [
            (4, "Sheoldred, the Apocalypse", "main"),  # mythic x4
            (4, "Llanowar Elves", "main"),             # common x4
            (2, "Cut Down", "main"),                   # uncommon x2
            (10, "Swamp", "main"),                     # basic (free)
            (2, "Cut Down", "side"),                   # uncommon x2 (counted)
        ]
        r = arena.tally_wildcards(entries, tier=3, lookup=_lookup)
        self.assertEqual(r["main"], 20)
        self.assertEqual(r["side"], 2)
        self.assertEqual(r["basics"], 10)
        self.assertEqual(r["totals"], [4, 4, 0, 4])  # C,U,R,M
        # Tier 3 caps 16/10/6/3 -> mythic 4 over by 1 (hard); rest fine.
        myth = next(row for row in r["rows"] if row["rarity"] == "mythic")
        self.assertEqual(myth["over"], 1)
        self.assertTrue(myth["hard"])
        self.assertFalse(r["fits"])

    def test_tally_fits_when_within_caps(self):
        entries = [(3, "Sheoldred, the Apocalypse", "main")]  # mythic x3 == tier 3 cap
        r = arena.tally_wildcards(entries, tier=3, lookup=_lookup)
        self.assertTrue(r["fits"])
        myth = next(row for row in r["rows"] if row["rarity"] == "mythic")
        self.assertTrue(myth["at_cap"])
        self.assertEqual(myth["over"], 0)

    def test_tally_tier5_unlimited(self):
        entries = [(40, "Sheoldred, the Apocalypse", "main")]
        r = arena.tally_wildcards(entries, tier=5, lookup=_lookup)
        self.assertTrue(r["fits"])
        self.assertTrue(all(row["over"] == 0 for row in r["rows"]))

    def test_tally_offcolor_and_identity(self):
        entries = [(4, "Sheoldred, the Apocalypse", "main"),  # B
                   (4, "Llanowar Elves", "main")]             # G -> off-color for mono-B
        r = arena.tally_wildcards(entries, tier=3, lookup=_lookup, allowed_colors="b")
        self.assertEqual(r["deck_color_identity"], "BG")
        self.assertEqual(r["allowed"], "B")
        self.assertEqual([n for n, _ in r["offcolor"]], ["Llanowar Elves"])

    def test_tally_unknown_card(self):
        entries = [(1, "Definitely Not A Real Card", "main")]
        r = arena.tally_wildcards(entries, tier=2, lookup=_lookup)
        self.assertEqual(r["unknown"], ["Definitely Not A Real Card"])
        self.assertEqual(r["totals"], [0, 0, 0, 0])


# --------------------------------------------------------------------------- #
# Streaming bulk-JSON parser at awkward boundaries                            #
# --------------------------------------------------------------------------- #

class StreamingParserTests(unittest.TestCase):
    def _roundtrip(self, objs, text=None, bufsize=4):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "bulk.json")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text if text is not None else json.dumps(objs))
        # Tiny bufsize forces objects to span multiple chunk reads.
        return list(build.iter_bulk_objects(p, bufsize=bufsize))

    def test_objects_split_across_chunks(self):
        objs = [{"oracle_id": str(i), "name": "x" * 50, "n": i} for i in range(7)]
        got = self._roundtrip(objs, bufsize=8)  # far smaller than one object
        self.assertEqual([o["n"] for o in got], list(range(7)))

    def test_pretty_printed_with_whitespace(self):
        objs = [{"a": 1}, {"b": 2}, {"c": 3}]
        got = self._roundtrip(objs, text=json.dumps(objs, indent=4), bufsize=5)
        self.assertEqual(got, objs)

    def test_empty_array(self):
        self.assertEqual(self._roundtrip([], text="[]"), [])

    def test_single_object(self):
        self.assertEqual(self._roundtrip([{"only": True}], bufsize=3), [{"only": True}])


# --------------------------------------------------------------------------- #
# Status / staleness                                                          #
# --------------------------------------------------------------------------- #

class StatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.db = os.path.join(cls.dir, "cards.sqlite")
        jp = os.path.join(cls.dir, "b.json")
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump(SAMPLE, fh)
        build.build_from_json(jp, cls.db)

    def _set_built_at(self, iso):
        meta = os.path.join(os.path.dirname(self.db), "meta.json")
        with open(meta, "w", encoding="utf-8") as fh:
            json.dump({"built_at": iso, "unique_cards": 6, "bulk_id": "x"}, fh)

    def test_fresh_not_stale(self):
        self._set_built_at("2099-01-01T00:00:00Z")  # "built" in the future -> age ~0
        st = status.database_status(self.db)
        self.assertTrue(st["exists"])
        self.assertFalse(st["stale"])

    def test_old_is_stale(self):
        self._set_built_at("2000-01-01T00:00:00Z")
        st = status.database_status(self.db)
        self.assertTrue(st["stale"])
        self.assertGreater(st["age_days"], status.STALE_AFTER_DAYS)

    def test_missing_db(self):
        st = status.database_status(os.path.join(self.dir, "nope.sqlite"))
        self.assertFalse(st["exists"])
        self.assertTrue(st["stale"])  # absent counts as needing a build

    def test_ensure_without_build_reports_unavailable(self):
        res = status.ensure_database(os.path.join(self.dir, "absent.sqlite"),
                                     build_if_missing=False)
        self.assertFalse(res["available"])
        self.assertEqual(res["reason"], "missing")

    def test_ensure_present_is_available_without_rebuild(self):
        self._set_built_at("2099-01-01T00:00:00Z")
        res = status.ensure_database(self.db)
        self.assertTrue(res["available"])
        self.assertFalse(res["built"])


# --------------------------------------------------------------------------- #
# simplify_api — canned card dict, no network                                 #
# --------------------------------------------------------------------------- #

class SimplifyApiTests(unittest.TestCase):
    def test_simple_card(self):
        card = {
            "name": "Sol Ring", "cmc": 1.0, "type_line": "Artifact",
            "oracle_text": "{T}: Add {C}{C}.", "mana_cost": "{1}",
            "color_identity": [], "colors": [], "rarity": "uncommon",
            "keywords": [], "game_changer": True, "edhrec_rank": 1,
            "legalities": {"commander": "legal"}, "games": ["paper", "mtgo"],
            "prices": {"eur": "0.90", "usd": "1.10"}, "scryfall_uri": "u",
        }
        d = query.simplify_api(card)
        self.assertEqual(d["name"], "Sol Ring")
        self.assertEqual(d["color_identity"], "C")  # colorless -> 'C'
        self.assertTrue(d["game_changer"])
        self.assertAlmostEqual(d["eur"], 0.90)
        self.assertFalse(d["arena"])
        self.assertTrue(d["mtgo"])

    def test_double_faced_joins_faces(self):
        card = {
            "name": "Valki, God of Lies // Tibalt, Cosmic Impostor", "cmc": 2.0,
            "color_identity": ["B", "R"], "rarity": "mythic", "games": ["paper", "arena"],
            "prices": {"eur": "3.90"},
            "card_faces": [
                {"type_line": "Legendary Creature — God", "oracle_text": "Front.",
                 "mana_cost": "{1}{B}", "colors": ["B"]},
                {"type_line": "Legendary Planeswalker — Tibalt", "oracle_text": "Back.",
                 "mana_cost": "{5}{B}{R}", "colors": ["B", "R"]},
            ],
        }
        d = query.simplify_api(card)
        self.assertIn("//", d["type_line"])     # faces joined
        self.assertIn("Front.", d["oracle_text"])
        self.assertEqual(d["color_identity"], "BR")
        self.assertTrue(d["arena"])


# --------------------------------------------------------------------------- #
# Additional query operators                                                  #
# --------------------------------------------------------------------------- #

class OperatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.db = os.path.join(cls.dir, "cards.sqlite")
        jp = os.path.join(cls.dir, "b.json")
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump(SAMPLE, fh)
        build.build_from_json(jp, cls.db)

    def names(self, q, **kw):
        return sorted(c["name"] for c in query.search(q, db_path=self.db, limit=50, **kw))

    def test_color_contains(self):
        # c:b -> colors containing black: Sheoldred (B) and Valki (colors=B).
        got = self.names("c:b")
        self.assertIn("Sheoldred, the Apocalypse", got)
        self.assertNotIn("Llanowar Elves", got)

    def test_identity_superset(self):
        got = self.names("id>=B")  # identity contains black
        self.assertIn("Sheoldred, the Apocalypse", got)
        self.assertIn("Valki, God of Lies // Tibalt, Cosmic Impostor", got)  # B/R
        self.assertNotIn("Llanowar Elves", got)

    def test_guild_nickname_esper(self):
        # id<=esper (WUB): mono-B + colorless ok; green and B/R excluded.
        got = self.names("id<=esper")
        self.assertIn("Sheoldred, the Apocalypse", got)
        self.assertIn("Sol Ring", got)
        self.assertNotIn("Llanowar Elves", got)  # green
        self.assertNotIn("Valki, God of Lies // Tibalt, Cosmic Impostor", got)  # R off-color

    def test_wedge_nickname_jund(self):
        # id<=jund (BRG): black, green, and B/R all fit.
        got = self.names("id<=jund")
        self.assertIn("Sheoldred, the Apocalypse", got)
        self.assertIn("Llanowar Elves", got)
        self.assertIn("Valki, God of Lies // Tibalt, Cosmic Impostor", got)

    def test_power_compare(self):
        self.assertEqual(self.names("pow<=1 t:creature"), ["Llanowar Elves"])

    def test_rarity_abbreviation(self):
        self.assertIn("Reprinted Thing", self.names("r:r"))  # r -> rare

    def test_type_permanent(self):
        got = self.names("t:permanent")
        self.assertIn("Sol Ring", got)         # artifact
        self.assertIn("Llanowar Elves", got)   # creature
        self.assertIn("Reprinted Thing", got)  # enchantment

    def test_nested_or_and_parens(self):
        got = self.names("(t:artifact or t:creature) id<=B")
        self.assertEqual(got, ["Sheoldred, the Apocalypse", "Sol Ring"])

    def test_keyword(self):
        self.assertEqual(self.names("kw:deathtouch"), ["Sheoldred, the Apocalypse"])


if __name__ == "__main__":
    unittest.main()
