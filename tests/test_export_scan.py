"""Tests for the mtg-export memory scan — no MTGA process needed.

A fake process exposes one memory region laid out like MTGA's collection map: a .NET
`Dictionary<int,int>` entry array of (hashCode, next, key, value) uint32 quads. Skipped
when numpy (the exporter's one hard dependency) isn't installed, as on CI.
"""

import importlib.util
import os
import unittest
from unittest import mock

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

_SCRIPT = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "mtg-skills", "skills", "mtg-export", "scripts",
    "export_collection.py"))


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_collection", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FakeProcess:
    def __init__(self, data):
        self.data = data

    def read_bytes(self, base, size):
        return self.data[base:base + size]


def _entries(pairs):
    """(grpId, count) pairs -> Dictionary entry quads; next = -1 like an unchained slot."""
    out = []
    for gid, cnt in pairs:
        out += [gid, 0xFFFFFFFF, gid, cnt]
    return out


@unittest.skipIf(np is None, "numpy not installed")
class ScanCollectionTests(unittest.TestCase):
    def setUp(self):
        self.ex = _load_exporter()
        known_a = [(1000 + i, 1 + i % 4) for i in range(100)]
        unknown = [(9000 + i, 1) for i in range(40)]   # a run longer than the old GAP of 32
        known_b = [(2000 + i, 1 + i % 4) for i in range(100)]
        words = [0] * 64 + _entries(known_a + unknown + known_b) + [0] * 64
        self.data = np.array(words, dtype=np.uint32).tobytes()
        self.db = {gid: {"name": f"Card {gid}", "set": "TST"} for gid, _ in known_a + known_b}
        self.logged = []
        patches = [
            mock.patch.object(self.ex, "iter_readable_regions",
                              lambda pm: [(0, len(self.data))]),
            mock.patch.object(self.ex, "print_progress", lambda *a, **k: None),
            mock.patch.object(self.ex, "log", self.logged.append),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_default_gap_bridges_unknown_run(self):
        owned, dropped = self.ex.scan_collection(_FakeProcess(self.data), self.db)
        self.assertEqual(len(owned), 200)
        self.assertEqual(owned[1001], 2)
        self.assertEqual(owned[2099], 4)
        self.assertEqual(len(dropped), 40)
        self.assertFalse(any("[warning]" in m for m in self.logged))

    def test_small_gap_splits_and_warns(self):
        owned, _ = self.ex.scan_collection(_FakeProcess(self.data), self.db, gap=32)
        self.assertEqual(len(owned), 100)
        warnings = [m for m in self.logged if "[warning]" in m]
        self.assertEqual(len(warnings), 1)
        self.assertIn("--gap 32", warnings[0])


if __name__ == "__main__":
    unittest.main()
