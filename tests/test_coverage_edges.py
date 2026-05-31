"""Edge/error-branch tests to push coverage to the target.

Mostly hit error and fallback branches that the happy-path tests don't: malformed
queries (which must route to the API by returning None from to_sql), API-fallback paths
in search/named, status staleness edge cases, validator lookup paths, and the small
progress/HTTP-error branches. All offline.
"""

import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import query, status, validate, arena, cli, api, build  # noqa: E402
from test_mtg_scryfall import SAMPLE  # noqa: E402


def _http(code):
    return urllib.error.HTTPError("http://x", code, "e", {}, None)


class ToSqlEdgeTests(unittest.TestCase):
    """Malformed/unsupported queries must route to the API (to_sql -> None);
    valid-but-rare forms must translate (to_sql -> not None)."""

    ROUTES_TO_API = [
        "mv<=3 )",        # unbalanced (extra close paren)
        "(t:creature",    # missing close paren
        "id<=xyz",        # unknown color spec
        "mv<=abc",        # non-numeric comparison
        "id!=w",          # unsupported identity operator
        "r>=banana",      # bad rarity for ordering
        "game:xbox",      # unknown game
        "is:reserved",    # unsupported is: flag
        "function:ramp",  # Tagger
        "set:dmu",        # per-printing, dropped in collapse
    ]
    STAYS_LOCAL = [
        'o:"unterminated',          # unterminated quote tolerated
        "",                          # empty query
        "()",                        # empty group
        "- t:creature",              # lone-dash negation
        "Goblin",                    # bareword -> name contains
        "id=wb",                     # exact identity
        "c:colorless", "c:m", "c<=wu",
        "t:spell",
        "t:creature order=name",     # order hint
        "t:creature unique:cards",   # ignored non-filter
        "is:permanent",
    ]

    def test_routes_to_api(self):
        for q in self.ROUTES_TO_API:
            with self.subTest(q=q):
                self.assertIsNone(query.to_sql(q))

    def test_stays_local(self):
        for q in self.STAYS_LOCAL:
            with self.subTest(q=q):
                self.assertIsNotNone(query.to_sql(q))


class RowAndSimplifyEdgeTests(unittest.TestCase):
    def test_row_to_dict_bad_legalities(self):
        row = ["Name", 1.0, "Artifact", "txt", "{1}", "B", "B", "1", "1", "rare",
               "", 0, None, "{not valid json", "uri",
               None, None, None, None, 0, 1, 0, 0]
        d = query._row_to_dict(tuple(row))
        self.assertEqual(d["legalities"], {})  # malformed JSON -> {}

    def test_simplify_api_non_numeric_price(self):
        d = query.simplify_api({"name": "X", "prices": {"eur": "not-a-number"}})
        self.assertIsNone(d["eur"])


class SearchNamedFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.db = os.path.join(cls.dir, "cards.sqlite")
        jp = os.path.join(cls.dir, "b.json")
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump(SAMPLE, fh)
        build.build_from_json(jp, cls.db)

    def test_search_routes_unsupported_to_api(self):
        with mock.patch.object(query.api, "search",
                               return_value=[{"name": "From API", "prices": {}}]):
            out = query.search("function:ramp", db_path=self.db)
        self.assertEqual(out[0]["name"], "From API")

    def test_named_db_miss_falls_back_to_api(self):
        with mock.patch.object(query.api, "named",
                               return_value={"name": "Fuzzy Hit", "prices": {}}):
            card = query.named("Definitely Not In DB", db_path=self.db)
        self.assertEqual(card["name"], "Fuzzy Hit")

    def test_named_api_returns_none(self):
        with mock.patch.object(query.api, "named", return_value=None):
            self.assertIsNone(query.named("Nope Nope", db_path=self.db))


class StatusEdgeTests(unittest.TestCase):
    def _db_with_meta(self, meta):
        d = tempfile.mkdtemp()
        db = os.path.join(d, "cards.sqlite")
        with open(db, "w") as fh:
            fh.write("x")
        if meta is not None:
            with open(os.path.join(d, "meta.json"), "w") as fh:
                json.dump(meta, fh)
        return db

    def test_missing_meta_treated_as_stale(self):
        db = self._db_with_meta(None)  # db file exists, no meta.json
        st = status.database_status(db)
        self.assertTrue(st["exists"])
        self.assertTrue(st["stale"])
        self.assertIsNone(st["age_days"])

    def test_malformed_built_at(self):
        db = self._db_with_meta({"built_at": "not-a-date", "bulk_id": "x"})
        st = status.database_status(db)
        self.assertIsNone(st["age_days"])
        self.assertTrue(st["stale"])

    def test_check_remote_swallows_errors(self):
        db = self._db_with_meta({"built_at": "2099-01-01T00:00:00Z", "bulk_id": "x"})

        def boom(kind="default_cards"):
            raise api.ScryfallUnreachable("offline")

        with mock.patch.object(api, "bulk_metadata", boom):
            st = status.database_status(db, check_remote=True)
        self.assertIsNone(st["remote_newer"])

    def test_refresh_calls_build(self):
        called = {}

        def fake_build(dest=None, progress=None, force=False, **kw):
            called["force"] = force
            return {"unique_cards": 1}

        with mock.patch.object(status, "build_database", fake_build):
            status.refresh(db_path="/tmp/whatever/cards.sqlite")
        self.assertTrue(called["force"])


class ValidatorLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.db = os.path.join(cls.dir, "cards.sqlite")
        sample = [
            {"oracle_id": "cmd", "name": "Red Boss", "layout": "normal", "cmc": 3.0,
             "type_line": "Legendary Creature — Goblin", "color_identity": ["R"],
             "rarity": "rare", "set": "x", "released_at": "2024-01-01",
             "games": ["paper"], "prices": {}},
            {"oracle_id": "red", "name": "Red Spell", "layout": "normal", "cmc": 1.0,
             "type_line": "Instant", "color_identity": ["R"], "rarity": "common",
             "set": "x", "released_at": "2024-01-01", "games": ["paper"], "prices": {}},
            {"oracle_id": "grn", "name": "Green Creature", "layout": "normal", "cmc": 1.0,
             "type_line": "Creature — Elf", "color_identity": ["G"], "rarity": "common",
             "set": "x", "released_at": "2024-01-01", "games": ["paper"], "prices": {}},
        ]
        jp = os.path.join(cls.dir, "b.json")
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump(sample, fh)
        build.build_from_json(jp, cls.db)

    def test_commander_validation_uses_db_lookup(self):
        # No explicit lookup -> _resolve_lookup falls back to the DB via db_path.
        text = ("1 Red Boss\n1 Red Spell\n1 Green Creature\n1 Made Up Card\n")
        r = validate.validate_commander_import(text, commander="Red Boss", db_path=self.db)
        self.assertTrue(any("off-identity: Green Creature" in e for e in r["errors"]))
        self.assertTrue(any("Made Up Card" in w for w in r["warnings"]))

    def test_entries_skip_blanks_and_headers(self):
        text = "Commander\n1 Red Boss\n\nDeck\n1 Red Spell\n"
        r = validate.validate_commander_import(text, lookup=lambda n: {"color_identity": "R"})
        self.assertEqual(r["total"], 2)  # blank + section headers skipped

    def test_arena_entries_with_sections_blank_and_commander(self):
        text = "Commander\n1 Red Boss\n\nDeck\n60 Mountain\n"
        r = validate.validate_arena_import(text)
        self.assertEqual(r["main"], 61)  # commander section counts toward main


class ArenaEdgeTests(unittest.TestCase):
    def test_parse_deck_commander_section(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "a.txt")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("Commander\n1 Krenko, Mob Boss\nDeck\n4 Mountain\n")
        got = list(arena.parse_deck(p))
        self.assertIn((1, "Krenko, Mob Boss", "commander"), got)

    def test_tally_no_tier(self):
        r = arena.tally_wildcards([(4, "X", "main")],
                                  lookup=lambda n: {"rarity": "rare", "color_identity": "R"})
        self.assertIsNone(r["caps"])
        self.assertIsNone(r["fits"])
        self.assertEqual([row["count"] for row in r["rows"]], [0, 0, 4, 0])

    def test_tally_unknown_rarity(self):
        r = arena.tally_wildcards([(1, "Weird", "main")], tier=2,
                                  lookup=lambda n: {"rarity": "bonus", "color_identity": ""})
        self.assertIn("Weird", r["unknown"])

    def test_tally_default_lookup(self):
        # lookup=None -> arena imports query.named; patch it so no DB/network is touched.
        with mock.patch.object(query, "named",
                               return_value={"rarity": "rare", "color_identity": "R"}):
            r = arena.tally_wildcards([(2, "Anything", "main")], tier=3, lookup=None)
        self.assertEqual(r["totals"][2], 2)  # counted as rare


class CliProgressTests(unittest.TestCase):
    def test_progress_branches(self):
        buf = io.StringIO()
        for stage, info in [("downloading", "540 MB"), ("download_pct", 50),
                            ("building", None), ("collapsing", 1234),
                            ("download_pct", 33)]:  # 33 not in {25,50,75,100} -> no print
            cli._progress(stage, info, buf)
        out = buf.getvalue()
        self.assertIn("downloading Scryfall bulk data (540 MB)", out)
        self.assertIn("…50%", out)
        self.assertIn("building local SQLite database", out)
        self.assertIn("collapsing 1234 printings", out)
        self.assertNotIn("33%", out)


class ApiErrorBranchTests(unittest.TestCase):
    def test_search_reraises_non_404(self):
        with mock.patch("urllib.request.urlopen", side_effect=_http(500)):
            with self.assertRaises(urllib.error.HTTPError):
                api.search("x", limit=3)

    def test_named_reraises_non_404_on_exact(self):
        with mock.patch("urllib.request.urlopen", side_effect=_http(500)):
            with self.assertRaises(urllib.error.HTTPError):
                api.named("Sol Ring")

    def test_bulk_metadata_missing_type(self):
        payload = {"data": [{"type": "oracle_cards", "id": "o"}]}

        def fake_urlopen(req, timeout=None):
            class R(io.BytesIO):
                headers = {}
                def __enter__(self): return self
                def __exit__(self, *a): return False
            return R(json.dumps(payload).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            with self.assertRaises(RuntimeError):
                api.bulk_metadata("default_cards")


if __name__ == "__main__":
    unittest.main()
