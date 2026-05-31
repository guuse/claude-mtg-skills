"""Tests for the live Scryfall client (mtg_scryfall.api) — WITHOUT network.

`urllib.request.urlopen` is mocked, so these exercise pagination, the exact→fuzzy
fallback, bulk-metadata selection, streamed download, and the URLError→ScryfallUnreachable
mapping deterministically and offline.
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

from mtg_scryfall import api  # noqa: E402


class FakeResp(io.BytesIO):
    """Minimal urlopen() return: a context manager with .read() and .headers."""
    def __init__(self, data=b"", headers=None):
        super().__init__(data)
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _card(name, **kw):
    c = {"name": name, "object": "card"}
    c.update(kw)
    return c


def http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, None)


class ApiTests(unittest.TestCase):
    def test_search_paginates(self):
        page1 = {"data": [_card("A"), _card("B")], "has_more": True,
                 "next_page": "https://api.scryfall.com/cards/search?page=2"}
        page2 = {"data": [_card("C")], "has_more": False}

        def fake_urlopen(req, timeout=None):
            url = req.full_url
            body = page2 if "page=2" in url else page1
            return FakeResp(json.dumps(body).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            cards = api.search("t:creature", limit=10)
        self.assertEqual([c["name"] for c in cards], ["A", "B", "C"])

    def test_search_respects_limit(self):
        page1 = {"data": [_card("A"), _card("B"), _card("C")], "has_more": True,
                 "next_page": "https://api.scryfall.com/cards/search?page=2"}

        def fake_urlopen(req, timeout=None):
            return FakeResp(json.dumps(page1).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            cards = api.search("x", limit=2)
        self.assertEqual(len(cards), 2)  # stops at limit, never fetches page 2

    def test_search_404_returns_empty(self):
        def fake_urlopen(req, timeout=None):
            raise http_error(404)

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertEqual(api.search("nothing", limit=5), [])

    def test_named_exact(self):
        def fake_urlopen(req, timeout=None):
            assert "exact=" in req.full_url
            return FakeResp(json.dumps(_card("Sol Ring")).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertEqual(api.named("Sol Ring")["name"], "Sol Ring")

    def test_named_falls_back_to_fuzzy(self):
        def fake_urlopen(req, timeout=None):
            if "exact=" in req.full_url:
                raise http_error(404)
            return FakeResp(json.dumps(_card("Sol Ring")).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertEqual(api.named("sol rng")["name"], "Sol Ring")

    def test_named_not_found_returns_none(self):
        def fake_urlopen(req, timeout=None):
            raise http_error(404)  # both exact and fuzzy miss

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertIsNone(api.named("xyzzy not a card"))

    def test_bulk_metadata_selects_type(self):
        payload = {"data": [
            {"type": "oracle_cards", "id": "o", "download_uri": "u1"},
            {"type": "default_cards", "id": "d", "download_uri": "u2",
             "updated_at": "2026-01-01", "size": 123},
        ]}

        def fake_urlopen(req, timeout=None):
            return FakeResp(json.dumps(payload).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            meta = api.bulk_metadata("default_cards")
        self.assertEqual(meta["id"], "d")
        self.assertEqual(meta["download_uri"], "u2")

    def test_unreachable_maps_urlerror(self):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("name resolution failed")

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            with self.assertRaises(api.ScryfallUnreachable):
                api.get_json("https://api.scryfall.com/bulk-data")

    def test_download_to_streams_and_reports_progress(self):
        import tempfile
        data = b"x" * (3 * (1 << 20) + 7)  # a few MB to force multiple chunks

        def fake_urlopen(req, timeout=None):
            return FakeResp(data, headers={"Content-Length": str(len(data))})

        seen = []
        dest = os.path.join(tempfile.mkdtemp(), "out.bin")
        with mock.patch("urllib.request.urlopen", fake_urlopen):
            api.download_to("https://x/file", dest, progress=lambda d, t: seen.append((d, t)))
        self.assertEqual(os.path.getsize(dest), len(data))
        self.assertEqual(seen[-1][0], len(data))   # final progress == total bytes
        self.assertTrue(all(t == len(data) for _, t in seen))


if __name__ == "__main__":
    unittest.main()
