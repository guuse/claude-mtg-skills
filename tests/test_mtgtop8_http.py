"""Offline tests for the mtgtop8 fetcher and the shared `http.get_text` fetcher.

`mtgtop8` is pure parsing around `http.get_text`, so we mock `http.get_text` with crafted
HTML/plain-text fixtures. For `http.get_text` itself we mock `urllib.request.urlopen`
(matching `test_api.py`) and patch `time.sleep` so retry/backoff paths run instantly.
No network, deterministic.
"""

import io
import os
import sys
import unittest
import urllib.error
from unittest import mock

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import http, mtgtop8  # noqa: E402


class FakeResp(io.BytesIO):
    """Minimal urlopen() return: a context manager with .read()."""
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code):
    return urllib.error.HTTPError("https://x", code, "err", {}, None)


# --- fixtures matching the production regexes -------------------------------------------

META_HTML = (
    "<a href=archetype?a=207&meta=50&f=ST>UR Aggro</a></span><span>25.0 %</span>\n"
    "<a href=archetype?a=42&amp;meta=50&amp;f=ST>Mono Black</a></span><span>10.5 %</span>\n"
    "<a href=archetype?a=207&meta=50&f=ST>UR Aggro dup</a></span><span>9.0 %</span>\n"
    "<a href=archetype?a=99&meta=50&f=ST>Bad Share</a></span><span>1.2.3 %</span>\n"
)

ARCHETYPE_HTML = (
    "<a href=/event?e=86946&d=860074&f=ST>Izzet Prowess</a></td>"
    "<td><a class=player href=/search?player=Arianne>Arianne</a></td>"
    "<td><a href=/event?e=86946&f=ST>MTGO Challenge 32</a></td>\n"
    "<a href=/event?e=86947&d=860075&f=ST>Mono Red</a></td>\n"
    "<a href=/event?e=86946&d=860074&f=ST>Izzet dup</a></td>\n"
)

EXPORT_TEXT = "4 Mountain\n2 Lightning Bolt\n\nSideboard\n2 Abrade\n"


class GetTextTests(unittest.TestCase):
    """Cover http.get_text: success, non-HTTPS, HTTP error, transient retry, URLError."""

    def test_success_with_headers_and_delay(self):
        with mock.patch("urllib.request.urlopen", lambda req, timeout=None: FakeResp(b"hello world")), \
             mock.patch("time.sleep"):
            out = http.get_text("https://example.com/x", headers={"X-Test": "1"}, delay=0.05)
        self.assertEqual(out, "hello world")

    def test_refuses_non_https(self):
        with self.assertRaises(http.FetchError):
            http.get_text("http://insecure.example.com")

    def test_permanent_http_error_raises_with_status(self):
        def boom(req, timeout=None):
            raise _http_error(404)
        with mock.patch("urllib.request.urlopen", boom), mock.patch("time.sleep"):
            with self.assertRaises(http.FetchError) as ctx:
                http.get_text("https://example.com/missing", retries=0)
        self.assertEqual(ctx.exception.status, 404)

    def test_transient_status_retries_then_succeeds(self):
        calls = {"n": 0}

        def flaky(req, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _http_error(503)
            return FakeResp(b"recovered")

        with mock.patch("urllib.request.urlopen", flaky), mock.patch("time.sleep"):
            out = http.get_text("https://example.com/x", retries=2, backoff=0)
        self.assertEqual(out, "recovered")
        self.assertEqual(calls["n"], 2)

    def test_urlerror_retries_then_raises(self):
        def unreachable(req, timeout=None):
            raise urllib.error.URLError("name resolution failed")
        with mock.patch("urllib.request.urlopen", unreachable), mock.patch("time.sleep"):
            with self.assertRaises(http.FetchError):
                http.get_text("https://example.com/x", retries=1, backoff=0)


class MtgTop8ParseTests(unittest.TestCase):
    """Cover the pure parsers: _unescape, fetch_meta, fetch_archetype_decks, _parse_export."""

    def test_unescape(self):
        self.assertEqual(mtgtop8._unescape("Jadar &amp; co &#39;n&quot; &eacute;"), 'Jadar & co \'n" é')

    def test_fetch_meta_parses_dedupes_sorts(self):
        with mock.patch("mtg_scryfall.http.get_text", lambda url: META_HTML):
            meta = mtgtop8.fetch_meta("ST")
        # dup archetype 207 dropped → 3 entries; sorted by share desc; bad share → 0.0
        self.assertEqual([m["archetype_id"] for m in meta], [207, 42, 99])
        self.assertEqual(meta[0]["name"], "UR Aggro")
        self.assertAlmostEqual(meta[0]["share"], 25.0)
        self.assertEqual(meta[-1]["share"], 0.0)  # "1.2.3" -> ValueError -> 0.0

    def test_fetch_archetype_decks_dedupes(self):
        with mock.patch("mtg_scryfall.http.get_text", lambda url: ARCHETYPE_HTML):
            decks = mtgtop8.fetch_archetype_decks(207, "ST")
        self.assertEqual([d["deck_id"] for d in decks], [860074, 860075])  # dup dropped
        self.assertEqual(decks[0]["event_id"], 86946)

    def test_fetch_archetype_decks_respects_limit(self):
        with mock.patch("mtg_scryfall.http.get_text", lambda url: ARCHETYPE_HTML):
            decks = mtgtop8.fetch_archetype_decks(207, "ST", limit=1)
        self.assertEqual(len(decks), 1)

    def test_parse_export_splits_main_and_sideboard(self):
        main, side = mtgtop8._parse_export(EXPORT_TEXT)
        self.assertEqual(main, [{"quantity": 4, "name": "Mountain"},
                                {"quantity": 2, "name": "Lightning Bolt"}])
        self.assertEqual(side, [{"quantity": 2, "name": "Abrade"}])


class MtgTop8FetchDeckTests(unittest.TestCase):
    def test_fetch_deck_ok(self):
        with mock.patch("mtg_scryfall.http.get_text", lambda url: EXPORT_TEXT):
            deck = mtgtop8.fetch_deck(860074)
        self.assertEqual(deck["deck_id"], 860074)
        self.assertEqual(len(deck["maindeck"]), 2)
        self.assertEqual(len(deck["sideboard"]), 1)

    def test_fetch_deck_empty_raises(self):
        with mock.patch("mtg_scryfall.http.get_text", lambda url: "Sideboard\n"):
            with self.assertRaises(http.FetchError):
                mtgtop8.fetch_deck(999)


def _route(url):
    if "format?f=" in url:
        return META_HTML
    if "archetype?a=" in url:
        return ARCHETYPE_HTML
    if "mtgo?d=" in url:
        return EXPORT_TEXT
    raise http.FetchError("unexpected url", url=url)


class TopDecklistsTests(unittest.TestCase):
    def test_happy_path(self):
        with mock.patch("mtg_scryfall.http.get_text", _route):
            out = mtgtop8.top_decklists("ST", archetypes=2, per_archetype=1)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["archetype"], "UR Aggro")
        self.assertTrue(out[0]["decks"])           # at least one real decklist
        self.assertIn("maindeck", out[0]["decks"][0])

    def test_archetype_fetch_failure_is_swallowed(self):
        def route(url):
            if "archetype?a=" in url:
                raise http.FetchError("archetype page down", url=url)
            return _route(url)
        with mock.patch("mtg_scryfall.http.get_text", route):
            out = mtgtop8.top_decklists("ST", archetypes=1, per_archetype=1)
        self.assertEqual(out[0]["decks"], [])      # included, but empty

    def test_deck_fetch_failure_is_skipped(self):
        def route(url):
            if "mtgo?d=" in url:
                raise http.FetchError("export down", url=url)
            return _route(url)
        with mock.patch("mtg_scryfall.http.get_text", route):
            out = mtgtop8.top_decklists("ST", archetypes=1, per_archetype=1)
        self.assertEqual(out[0]["decks"], [])      # each deck skipped


class ToImportLinesTests(unittest.TestCase):
    def test_with_sideboard(self):
        deck = {"maindeck": [{"quantity": 4, "name": "Mountain"}],
                "sideboard": [{"quantity": 2, "name": "Abrade"}]}
        self.assertEqual(mtgtop8.to_import_lines(deck),
                         ["4 Mountain", "", "Sideboard", "2 Abrade"])

    def test_without_sideboard(self):
        deck = {"maindeck": [{"quantity": 4, "name": "Mountain"}], "sideboard": []}
        self.assertEqual(mtgtop8.to_import_lines(deck), ["4 Mountain"])


if __name__ == "__main__":
    unittest.main()
