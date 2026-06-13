"""Tests for the external data layer — WITHOUT network.

Covers the shared robust fetcher (mtg_scryfall.http), the EDHREC JSON client
(mtg_scryfall.edhrec) and the Archidekt/Moxfield deck importer (mtg_scryfall.decks).
`urllib.request.urlopen` (for http) and `http.get_json` (for the higher layers) are
mocked, so retry/backoff, HTTPS enforcement, slug/URL parsing and response shaping are
exercised deterministically and offline. `time.sleep` is patched so retries don't wait.
"""

import io
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import http, edhrec, decks  # noqa: E402


class FakeResp(io.BytesIO):
    def __init__(self, data=b"", headers=None):
        super().__init__(data)
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code):
    return urllib.error.HTTPError("https://x", code, "err", {}, None)


class HttpTests(unittest.TestCase):
    def test_rejects_non_https(self):
        with self.assertRaises(http.FetchError):
            http.get_json("http://insecure.example/x.json")

    def test_get_json_success_and_headers(self):
        seen = {}

        def fake_urlopen(req, timeout=None):
            seen["ua"] = req.headers.get("User-agent")
            seen["accept"] = req.headers.get("Accept")
            return FakeResp(json.dumps({"ok": True}).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            out = http.get_json("https://api.example/x.json", delay=0)
        self.assertEqual(out, {"ok": True})
        self.assertIn("ClaudeMTGSkills", seen["ua"])
        self.assertEqual(seen["accept"], "application/json")

    def test_404_raises_with_status_no_retry(self):
        calls = []

        def fake_urlopen(req, timeout=None):
            calls.append(1)
            raise http_error(404)

        with mock.patch("urllib.request.urlopen", fake_urlopen), \
                mock.patch("time.sleep"):
            with self.assertRaises(http.FetchError) as ctx:
                http.get_json("https://api.example/missing.json")
        self.assertEqual(ctx.exception.status, 404)
        self.assertEqual(len(calls), 1)  # 4xx is permanent — no retry

    def test_transient_retries_then_succeeds(self):
        calls = []

        def fake_urlopen(req, timeout=None):
            calls.append(1)
            if len(calls) < 3:
                raise http_error(503)
            return FakeResp(json.dumps({"ok": 1}).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen), \
                mock.patch("time.sleep") as slept:
            out = http.get_json("https://api.example/x.json", delay=0)
        self.assertEqual(out, {"ok": 1})
        self.assertEqual(len(calls), 3)         # 2 failures + 1 success
        self.assertEqual(slept.call_count, 2)   # backed off twice

    def test_transient_exhausts_retries(self):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("boom")

        with mock.patch("urllib.request.urlopen", fake_urlopen), \
                mock.patch("time.sleep"):
            with self.assertRaises(http.FetchError):
                http.get_json("https://api.example/x.json", retries=2)

    def test_non_json_body_raises(self):
        def fake_urlopen(req, timeout=None):
            return FakeResp(b"<html>nope</html>")

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            with self.assertRaises(http.FetchError):
                http.get_json("https://api.example/x.json", delay=0)

    def test_custom_headers_and_polite_delay(self):
        seen = {}

        def fake_urlopen(req, timeout=None):
            seen["accept"] = req.headers.get("Accept")
            seen["x"] = req.headers.get("X-test")
            return FakeResp(json.dumps({"ok": 1}).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen), \
                mock.patch("time.sleep") as slept:
            http.get_json("https://api.example/x.json", headers={"X-Test": "1"})
        self.assertEqual(seen["x"], "1")
        self.assertEqual(seen["accept"], "application/json")  # default still present
        slept.assert_called_once()  # the polite post-fetch delay fired

    def test_oserror_retries_then_raises(self):
        def fake_urlopen(req, timeout=None):
            raise OSError("connection reset")

        with mock.patch("urllib.request.urlopen", fake_urlopen), \
                mock.patch("time.sleep"):
            with self.assertRaises(http.FetchError):
                http.get_json("https://api.example/x.json", retries=1)


class EdhrecTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(edhrec.slugify("Atraxa, Praetors' Voice"), "atraxa-praetors-voice")
        self.assertEqual(edhrec.slugify("Urza, Lord High Artificer"), "urza-lord-high-artificer")
        self.assertEqual(edhrec.slugify("Light-Paws, Emperor's Voice"), "light-paws-emperors-voice")
        self.assertEqual(edhrec.slugify("Esika, God of the Tree // The Prismatic Bridge"),
                         "esika-god-of-the-tree")

    def test_commander_parses_cardlists_and_themes(self):
        page = {
            "num_decks_avg": 100,
            "avg_price": 500,
            "panels": {"taglinks": [
                {"value": "Infect", "slug": "infect", "count": 5},
                {"slug": None},  # skipped
            ]},
            "container": {"json_dict": {"cardlists": [
                {"header": "Top Cards", "cardviews": [
                    {"name": "Sol Ring", "synergy": 0.1, "num_decks": 9},
                    {"name": None},  # skipped
                ]},
                {"header": None, "cardviews": []},  # skipped
            ]}},
        }
        with mock.patch.object(edhrec.http, "get_json", return_value=page):
            out = edhrec.commander("Atraxa, Praetors' Voice")
        self.assertEqual(out["slug"], "atraxa-praetors-voice")
        self.assertEqual([t["slug"] for t in out["themes"]], ["infect"])
        self.assertEqual(out["cardlists"]["Top Cards"][0]["name"], "Sol Ring")

    def test_average_deck_returns_lines(self):
        page = {"deck": ["1 Sol Ring", "1 Atraxa, Praetors' Voice"], "deck_size": 99}
        with mock.patch.object(edhrec.http, "get_json", return_value=page) as g:
            out = edhrec.average_deck("Atraxa, Praetors' Voice")
        self.assertEqual(out["cards"][0], "1 Sol Ring")
        self.assertIn("average-decks/atraxa-praetors-voice.json", g.call_args[0][0])

    def test_theme_and_budget_urls(self):
        page = {"container": {"json_dict": {"cardlists": []}}, "panels": {}}
        with mock.patch.object(edhrec.http, "get_json", return_value=page) as g:
            t = edhrec.theme("Atraxa, Praetors' Voice", "infect")
        self.assertEqual(t["theme"], "infect")
        self.assertIn("commanders/atraxa-praetors-voice/infect.json", g.call_args[0][0])

        with mock.patch.object(edhrec.http, "get_json", return_value=page) as g:
            b = edhrec.budget("Atraxa, Praetors' Voice")
        self.assertEqual(b["slug"], "atraxa-praetors-voice")
        self.assertIn("commanders/atraxa-praetors-voice/budget.json", g.call_args[0][0])

    def test_fetch_error_propagates(self):
        with mock.patch.object(edhrec.http, "get_json",
                               side_effect=http.FetchError("403", status=403)):
            with self.assertRaises(http.FetchError):
                edhrec.commander("Nobody")


class DecksTests(unittest.TestCase):
    def test_parse_deck_ref(self):
        self.assertEqual(decks.parse_deck_ref("https://archidekt.com/decks/7000000/x"),
                         ("archidekt", "7000000"))
        self.assertEqual(decks.parse_deck_ref("https://www.moxfield.com/decks/aB3_xY"),
                         ("moxfield", "aB3_xY"))
        self.assertEqual(decks.parse_deck_ref("7000000"), ("archidekt", "7000000"))
        self.assertEqual(decks.parse_deck_ref("aB3xYz"), ("moxfield", "aB3xYz"))
        with self.assertRaises(ValueError):
            decks.parse_deck_ref("!!")

    def test_from_archidekt(self):
        data = {
            "name": "Edgar", "deckFormat": 3,
            "cards": [
                {"quantity": 1, "categories": ["Commander"],
                 "card": {"oracleCard": {"name": "Edgar Markov"}}},
                {"quantity": 4, "categories": ["Creature"],
                 "card": {"oracleCard": {"name": "Vampire Token Maker"}}},
                {"quantity": 1, "categories": [], "card": {"displayName": "Sol Ring"}},
                {"quantity": 1, "categories": [], "card": {}},  # no name -> skipped
            ],
        }
        with mock.patch.object(decks.http, "get_json", return_value=data):
            out = decks.from_archidekt("1")
        self.assertEqual(out["source"], "archidekt")
        self.assertEqual(out["format"], "commander")
        self.assertEqual(out["commanders"], ["Edgar Markov"])
        self.assertEqual(len(out["cards"]), 2)  # nameless entry dropped

    def test_from_moxfield(self):
        data = {
            "name": "Living End", "format": "modern",
            "boards": {
                "commanders": {"cards": {}},
                "mainboard": {"cards": {
                    "a": {"quantity": 4, "card": {"name": "Street Wraith"}},
                    "b": {"quantity": 1, "card": {"name": "Living End"}},
                }},
                "sideboard": {"cards": {"c": {"quantity": 2, "card": {"name": "Ignore Me"}}}},
            },
        }
        with mock.patch.object(decks.http, "get_json", return_value=data):
            out = decks.from_moxfield("xyz")
        self.assertEqual(out["source"], "moxfield")
        self.assertEqual({c["name"] for c in out["cards"]}, {"Street Wraith", "Living End"})
        self.assertEqual(out["commanders"], [])  # sideboard excluded, no commander

    def test_fetch_deck_dispatch_and_import_lines(self):
        data = {"name": "X", "deckFormat": 3,
                "cards": [{"quantity": 1, "categories": ["Commander"],
                           "card": {"oracleCard": {"name": "Edgar Markov"}}},
                          {"quantity": 2, "categories": [],
                           "card": {"oracleCard": {"name": "Sol Ring"}}}]}
        with mock.patch.object(decks.http, "get_json", return_value=data):
            deck = decks.fetch_deck("https://archidekt.com/decks/1/x")
        lines = decks.to_import_lines(deck)
        self.assertEqual(lines, ["1 Edgar Markov", "2 Sol Ring"])

    def test_fetch_deck_moxfield_branch(self):
        data = {"name": "X", "format": "modern",
                "boards": {"mainboard": {"cards": {
                    "a": {"quantity": 1, "card": {"name": "Island"}}}}}}
        with mock.patch.object(decks.http, "get_json", return_value=data):
            deck = decks.fetch_deck("https://moxfield.com/decks/abcDEF")
        self.assertEqual(deck["source"], "moxfield")
        self.assertEqual(decks.to_import_lines(deck), ["1 Island"])


if __name__ == "__main__":
    unittest.main()
