"""Offline smoke tests for the shared mtg_scryfall library.

No network and no 540 MB download: a small crafted card set is built into a temporary
SQLite database, then the build/collapse logic and the Scryfall->SQL query translator
are exercised against it. The one thing that genuinely needs the network — routing
`function:`/`otag:` and unsupported operators to the live API — is tested at the
to_sql() boundary (it must return None), not by actually calling Scryfall.

Run:  python -m unittest discover -s tests
"""

import json
import os
import sys
import tempfile
import unittest

# Make the shared library importable: <repo>/mtg-skills/lib/mtg_scryfall
_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import build, query  # noqa: E402


def _card(oracle_id, name, **kw):
    """A minimal raw-Scryfall-shaped card object with sensible defaults."""
    base = {
        "oracle_id": oracle_id, "name": name, "layout": "normal", "cmc": 0.0,
        "type_line": "Artifact", "oracle_text": "", "mana_cost": "",
        "color_identity": [], "colors": [], "power": None, "toughness": None,
        "rarity": "common", "keywords": [], "produced_mana": [], "game_changer": False,
        "edhrec_rank": None, "legalities": {}, "set": "tst", "set_type": "expansion",
        "scryfall_uri": "https://scryfall.test", "released_at": "2020-01-01",
        "games": ["paper"], "prices": {},
    }
    base.update(kw)
    return base


# A crafted set covering the tricky collapse + query cases.
SAMPLE = [
    # Sol Ring: two printings -> cheapest price wins (0.90), it's a Game Changer.
    _card("sol", "Sol Ring", cmc=1.0, oracle_text="{T}: Add {C}{C}.", rarity="uncommon",
          produced_mana=["C"], game_changer=True, edhrec_rank=1, set="c21",
          released_at="2021-04-23", games=["paper", "mtgo"], prices={"eur": "1.50", "usd": "1.80"}),
    _card("sol", "Sol Ring", cmc=1.0, oracle_text="{T}: Add {C}{C}.", rarity="uncommon",
          produced_mana=["C"], game_changer=True, edhrec_rank=1, set="cmm",
          released_at="2024-01-01", games=["paper"], prices={"eur": "0.90", "usd": "1.10"}),
    # Reprint whose rarity changed across printings: latest (2024, rare) must win over 2018 common.
    _card("rep", "Reprinted Thing", cmc=2.0, type_line="Enchantment", rarity="common",
          set="old", released_at="2018-01-01", prices={"eur": "0.10"}),
    _card("rep", "Reprinted Thing", cmc=2.0, type_line="Enchantment", rarity="rare",
          set="new", released_at="2024-06-01", prices={"eur": "0.20"}),
    # Sheoldred: mono-black, mythic, NOT standard-legal, Arena-available, priced.
    _card("sheo", "Sheoldred, the Apocalypse", cmc=4.0,
          type_line="Legendary Creature — Phyrexian Praetor",
          oracle_text="Whenever you draw a card, gain 2 life.", mana_cost="{2}{B}{B}",
          color_identity=["B"], colors=["B"], power="4", toughness="5", rarity="mythic",
          keywords=["Deathtouch"], edhrec_rank=50,
          legalities={"standard": "not_legal", "commander": "legal"},
          set="dmu", released_at="2022-09-09", games=["paper", "arena", "mtgo"],
          prices={"eur": "60.0", "usd": "70.0"}),
    # Llanowar Elves: mono-green, common, standard-legal, Arena, cheap.
    _card("llan", "Llanowar Elves", cmc=1.0, type_line="Creature — Elf Druid",
          oracle_text="{T}: Add {G}.", mana_cost="{G}", color_identity=["G"], colors=["G"],
          power="1", toughness="1", rarity="common", produced_mana=["G"], edhrec_rank=120,
          legalities={"standard": "legal", "commander": "legal"},
          set="dom", released_at="2018-04-27", games=["paper", "arena", "mtgo"],
          prices={"eur": "0.30", "usd": "0.40"}),
    # A token printing — must be dropped entirely (layout=token).
    _card("tok", "Treasure", layout="token", type_line="Token Artifact", set="ttst"),
    # A funny/un-card — hidden by default, found only with is:funny.
    _card("funny", "Kindslaver", cmc=6.0, oracle_text="funny stuff", rarity="rare",
          set_type="funny", border_color="silver", released_at="2004-11-19",
          prices={"eur": "5.0"}),
    # A DFC whose full name has a // — named() should still resolve "front" name.
    _card("valki", "Valki, God of Lies // Tibalt, Cosmic Impostor", cmc=2.0,
          type_line="Legendary Creature — God // Legendary Planeswalker — Tibalt",
          color_identity=["B", "R"], colors=["B"], rarity="mythic", set="khm",
          released_at="2021-02-05", prices={"eur": "3.90"}),
]


class MtgScryfallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="mtgtest_")
        jp = os.path.join(cls.dir, "bulk.json")
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump(SAMPLE, fh)
        cls.db = os.path.join(cls.dir, "cards.sqlite")
        cls.stats = build.build_from_json(jp, cls.db)

    def names(self, q, **kw):
        return sorted(c["name"] for c in query.search(q, db_path=self.db, limit=50, **kw))

    # ---- build / collapse ------------------------------------------------- #
    def test_token_dropped_and_unique_count(self):
        # sol, rep, sheo, llan, funny, valki = 6 unique; token dropped.
        self.assertEqual(self.stats["unique_cards"], 6)
        self.assertNotIn("Treasure", self.names("t:artifact"))
        self.assertNotIn("Treasure", self.names("name:treasure"))

    def test_cheapest_printing_price(self):
        sol = query.named("Sol Ring", db_path=self.db)
        self.assertAlmostEqual(sol["eur"], 0.90)  # not 1.50 from the older printing

    def test_latest_printing_rarity_wins(self):
        rep = query.named("Reprinted Thing", db_path=self.db)
        self.assertEqual(rep["rarity"], "rare")  # 2024 printing, not 2018 common

    # ---- identity / color ------------------------------------------------- #
    def test_identity_subset_includes_colorless(self):
        # id<=B: mono-black + colorless artifacts, but not green/multicolor.
        got = self.names("id<=B")
        self.assertIn("Sheoldred, the Apocalypse", got)
        self.assertIn("Sol Ring", got)             # colorless fits any identity
        self.assertNotIn("Llanowar Elves", got)    # green
        self.assertNotIn("Valki, God of Lies // Tibalt, Cosmic Impostor", got)  # B/R

    def test_identity_colorless_exact(self):
        got = self.names("id:c t:artifact")
        self.assertIn("Sol Ring", got)
        self.assertNotIn("Sheoldred, the Apocalypse", got)

    # ---- text / type / numeric ------------------------------------------- #
    def test_oracle_and_mv(self):
        self.assertEqual(self.names('o:"add" mv<=1'), ["Llanowar Elves", "Sol Ring"])

    def test_type_and_power(self):
        self.assertEqual(self.names("t:creature pow>=4"), ["Sheoldred, the Apocalypse"])

    # ---- flags / availability / legality / price ------------------------- #
    def test_gamechanger(self):
        self.assertEqual(self.names("is:gamechanger"), ["Sol Ring"])

    def test_legal_standard(self):
        got = self.names("legal:standard")
        self.assertIn("Llanowar Elves", got)
        self.assertNotIn("Sheoldred, the Apocalypse", got)  # not_legal

    def test_game_arena(self):
        self.assertEqual(self.names("game:arena"),
                         ["Llanowar Elves", "Sheoldred, the Apocalypse"])

    def test_rarity_ordering(self):
        self.assertNotIn("Llanowar Elves", self.names("r>=rare"))   # common excluded
        self.assertIn("Sheoldred, the Apocalypse", self.names("r>=rare"))

    def test_price_filter_excludes_nulls(self):
        cheap = self.names("eur<=1")
        self.assertIn("Sol Ring", cheap)        # 0.90
        self.assertIn("Llanowar Elves", cheap)  # 0.30
        self.assertNotIn("Sheoldred, the Apocalypse", cheap)  # 60.0

    # ---- negation / or / funny default ----------------------------------- #
    def test_negation(self):
        self.assertNotIn("Sheoldred, the Apocalypse",
                         self.names("t:creature -t:legendary"))

    def test_funny_hidden_by_default(self):
        self.assertNotIn("Kindslaver", self.names("t:artifact"))
        self.assertEqual(self.names("is:funny"), ["Kindslaver"])

    def test_oracle_funny_text_does_not_disable_filter(self):
        # o:"funny" must NOT surface the funny un-card.
        self.assertEqual(self.names('o:"funny"'), [])

    # ---- named / DFC ----------------------------------------------------- #
    def test_named_dfc_front_name(self):
        c = query.named("Valki, God of Lies", db_path=self.db)
        self.assertIsNotNone(c)
        self.assertTrue(c["name"].startswith("Valki, God of Lies"))

    # ---- routing to the live API ----------------------------------------- #
    def test_unsupported_operators_route_to_api(self):
        for q in ("function:ramp", "otag:removal", "set:dmu",
                  "id<=B function:ramp", "frobnicate:yes"):
            self.assertIsNone(query.to_sql(q), f"{q!r} should route to the API")

    def test_supported_query_stays_local(self):
        self.assertIsNotNone(query.to_sql('id<=WB o:"draw" mv<=3 is:gamechanger'))


if __name__ == "__main__":
    unittest.main()
