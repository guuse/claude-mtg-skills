"""Bulk-file format handling: JSONL, legacy JSON array, gzipped or not.

Scryfall serves bulk data as gzipped JSONL. It used to serve a single top-level JSON
array, and `iter_bulk_objects()` was written for that shape only. Fed a JSONL file the
old reader did not raise: it found the first `[` inside a card's `"multiverse_ids"`
value and decoded from the middle of that record, yielding an int and then stopping.
A silently near-empty database is worse than a crash, so these are regression tests
rather than nice-to-haves.

Run:  python -m unittest discover -s tests
"""

import gzip
import json
import os
import sys
import tempfile
import unittest

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import api, build  # noqa: E402


def _card(i):
    """A card object carrying the array-valued fields that broke the old reader."""
    return {
        "object": "card",
        "oracle_id": f"oid-{i}",
        "id": f"pid-{i}",
        "name": f"Test Card {i}",
        "layout": "normal",
        "cmc": float(i),
        "type_line": "Creature - Dinosaur",
        "oracle_text": "Trample",
        "mana_cost": "{G}",
        "colors": ["G"],
        "color_identity": ["G"],
        "multiverse_ids": [600000 + i],
        "keywords": ["Trample"],
        "rarity": "rare",
        "set": "tst",
        "collector_number": str(i),
        "released_at": "2026-01-01",
        "legalities": {"standard": "legal"},
        "games": ["arena", "paper"],
        "prices": {"usd": "1.00", "eur": "0.90"},
    }


CARDS = [_card(i) for i in range(1, 6)]


def _write(path, data, compress=False):
    opener = (lambda p: gzip.open(p, "wt", encoding="utf-8")) if compress else \
             (lambda p: open(p, "w", encoding="utf-8"))
    with opener(path) as fh:
        fh.write(data)
    return path


class BulkFormatTests(unittest.TestCase):
    """iter_bulk_objects() must read every shape Scryfall has shipped."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _path(self, name):
        return os.path.join(self.tmp, name)

    def _assert_reads_all(self, path):
        got = list(build.iter_bulk_objects(path))
        self.assertEqual(len(got), len(CARDS),
                         f"expected {len(CARDS)} objects from {os.path.basename(path)}, "
                         f"got {len(got)}: {got[:3]}")
        for obj in got:
            self.assertIsInstance(obj, dict, f"yielded a {type(obj).__name__}, not a card object")
        self.assertEqual([c["name"] for c in got], [c["name"] for c in CARDS])

    def test_jsonl(self):
        body = "\n".join(json.dumps(c) for c in CARDS) + "\n"
        self._assert_reads_all(_write(self._path("cards.jsonl"), body))

    def test_jsonl_gzipped(self):
        body = "\n".join(json.dumps(c) for c in CARDS) + "\n"
        self._assert_reads_all(_write(self._path("cards.jsonl.gz"), body, compress=True))

    def test_jsonl_gzip_detected_from_magic_not_extension(self):
        """build_database() streams into a tempfile whose suffix says nothing useful."""
        body = "\n".join(json.dumps(c) for c in CARDS) + "\n"
        self._assert_reads_all(_write(self._path("tmpXXXX.json"), body, compress=True))

    def test_jsonl_with_blank_lines_and_no_trailing_newline(self):
        body = "\n\n".join(json.dumps(c) for c in CARDS)
        self._assert_reads_all(_write(self._path("ragged.jsonl"), body))

    def test_legacy_json_array_still_works(self):
        self._assert_reads_all(_write(self._path("cards.json"), json.dumps(CARDS)))

    def test_legacy_json_array_gzipped(self):
        self._assert_reads_all(
            _write(self._path("cards.json.gz"), json.dumps(CARDS), compress=True))

    def test_legacy_json_array_pretty_printed(self):
        self._assert_reads_all(
            _write(self._path("pretty.json"), json.dumps(CARDS, indent=2)))

    def test_jsonl_first_bracket_is_inside_a_record(self):
        """The exact regression: a bare `[` appears before any real array start.

        The old reader sliced at that bracket and yielded the multiverse id as an int.
        """
        got = list(build.iter_bulk_objects(
            _write(self._path("regress.jsonl"),
                   "\n".join(json.dumps(c) for c in CARDS))))
        self.assertNotIn(600001, got, "sliced into multiverse_ids instead of reading records")
        self.assertTrue(all(isinstance(o, dict) for o in got))
        self.assertEqual(len(got), len(CARDS))

    def test_build_from_json_end_to_end_on_jsonl(self):
        src = _write(self._path("full.jsonl"),
                     "\n".join(json.dumps(c) for c in CARDS) + "\n")
        db = self._path("cards.sqlite")
        stats = build.build_from_json(src, db)
        self.assertEqual(stats["unique_cards"], len(CARDS))
        self.assertTrue(os.path.exists(db))


class BulkDescriptorFieldTests(unittest.TestCase):
    """Scryfall renamed download_uri -> jsonl_download_uri and size -> compressed_size."""

    CURRENT = {
        "object": "bulk_data", "type": "default_cards",
        "updated_at": "2026-08-15T21:05:41.265+00:00",
        "jsonl_download_uri": "https://data.scryfall.io/default-cards/x.jsonl.gz",
        "compressed_size": 77518797,
    }
    LEGACY = {
        "object": "bulk_data", "type": "default_cards",
        "updated_at": "2025-01-01T00:00:00.000+00:00",
        "download_uri": "https://data.scryfall.io/default-cards/x.json",
        "size": 540000000,
    }

    def test_uri_from_current_field(self):
        self.assertEqual(api.bulk_uri(self.CURRENT), self.CURRENT["jsonl_download_uri"])

    def test_uri_from_legacy_field(self):
        self.assertEqual(api.bulk_uri(self.LEGACY), self.LEGACY["download_uri"])

    def test_uri_prefers_current_when_both_present(self):
        both = dict(self.LEGACY, **self.CURRENT)
        self.assertEqual(api.bulk_uri(both), self.CURRENT["jsonl_download_uri"])

    def test_uri_raises_clearly_when_absent(self):
        with self.assertRaises(RuntimeError) as ctx:
            api.bulk_uri({"object": "bulk_data", "type": "default_cards"})
        self.assertIn("download uri", str(ctx.exception))

    def test_size_from_either_field(self):
        self.assertEqual(api.bulk_size(self.CURRENT), 77518797)
        self.assertEqual(api.bulk_size(self.LEGACY), 540000000)

    def test_size_defaults_to_zero(self):
        self.assertEqual(api.bulk_size({}), 0)


if __name__ == "__main__":
    unittest.main()
