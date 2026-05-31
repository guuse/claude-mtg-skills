"""Tests for the path resolution and the auto-build/staleness glue — no network.

`build_database` and `api.bulk_metadata` are monkeypatched, so the ensure/refresh and
remote-freshness branches run without downloading anything.
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import paths, status, cli, api, build  # noqa: E402


class PathsTests(unittest.TestCase):
    def test_find_mtg_dir_walks_up(self):
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, ".mtg", "database"))
        deep = os.path.join(root, "a", "b", "c")
        os.makedirs(deep)
        self.assertEqual(paths.find_mtg_dir(deep), os.path.join(root, ".mtg"))

    def test_find_mtg_dir_absent(self):
        empty = tempfile.mkdtemp()
        self.assertIsNone(paths.find_mtg_dir(empty))

    def test_default_db_path_and_meta(self):
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, ".mtg"))
        db = paths.default_db_path(start=root)
        self.assertEqual(db, os.path.join(root, ".mtg", "database", "cards.sqlite"))
        self.assertEqual(paths.meta_path_for(db),
                         os.path.join(root, ".mtg", "database", "meta.json"))

    def test_default_db_path_when_no_mtg_uses_cwd(self):
        root = tempfile.mkdtemp()  # no .mtg here
        db = paths.default_db_path(start=root)
        self.assertEqual(db, os.path.join(root, ".mtg", "database", "cards.sqlite"))


def _fake_build(dest=None, progress=None, force=False, **kw):
    """Stand-in for build_database: write a tiny file + meta, no network."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as fh:
        fh.write("not really sqlite")
    meta = {"built_at": "2099-01-01T00:00:00Z", "unique_cards": 1, "bulk_id": "fake"}
    with open(paths.meta_path_for(dest), "w") as fh:
        json.dump(meta, fh)
    if progress:
        progress("building", None)
    return meta


class EnsureDatabaseTests(unittest.TestCase):
    def test_builds_when_missing(self):
        d = tempfile.mkdtemp()
        db = os.path.join(d, "cards.sqlite")
        with mock.patch.object(status, "build_database", _fake_build):
            res = status.ensure_database(db)
        self.assertTrue(res["available"])
        self.assertTrue(res["built"])
        self.assertTrue(os.path.exists(db))

    def test_no_build_when_disabled(self):
        d = tempfile.mkdtemp()
        res = status.ensure_database(os.path.join(d, "cards.sqlite"), build_if_missing=False)
        self.assertFalse(res["available"])
        self.assertEqual(res["reason"], "missing")

    def test_unreachable_degrades(self):
        d = tempfile.mkdtemp()

        def boom(**kw):
            raise api.ScryfallUnreachable("offline")

        with mock.patch.object(status, "build_database", boom):
            res = status.ensure_database(os.path.join(d, "cards.sqlite"))
        self.assertFalse(res["available"])
        self.assertIn("unreachable", res["reason"])

    def test_cannot_write_degrades(self):
        d = tempfile.mkdtemp()

        def boom(**kw):
            raise OSError("read-only fs")

        with mock.patch.object(status, "build_database", boom):
            res = status.ensure_database(os.path.join(d, "cards.sqlite"))
        self.assertFalse(res["available"])
        self.assertIn("cannot write", res["reason"])


class BuildDatabaseTests(unittest.TestCase):
    """Cover build_database's orchestration (metadata -> download -> build -> meta)
    with the network mocked: bulk_metadata returns a fake descriptor and download_to
    writes a crafted bulk JSON, then the real build_from_json runs."""

    SAMPLE = [
        {"oracle_id": "sol", "name": "Sol Ring", "layout": "normal", "cmc": 1.0,
         "type_line": "Artifact", "color_identity": [], "rarity": "uncommon",
         "set": "c21", "released_at": "2021-04-23", "games": ["paper"],
         "prices": {"eur": "1.10"}},
        {"oracle_id": "tok", "name": "Treasure", "layout": "token",
         "type_line": "Token Artifact", "set": "t", "games": ["paper"], "prices": {}},
    ]

    def test_build_database_end_to_end_offline(self):
        d = tempfile.mkdtemp()
        db = os.path.join(d, "database", "cards.sqlite")

        def fake_meta(kind="default_cards"):
            return {"id": "abc", "updated_at": "2026-05-31", "size": 999,
                    "download_uri": "https://x/default-cards.json"}

        def fake_download(url, dest, progress=None, chunk=1 << 20):
            with open(dest, "w", encoding="utf-8") as fh:
                json.dump(self.SAMPLE, fh)
            if progress:
                progress(999, 999)
            return dest

        with mock.patch.object(build.api, "bulk_metadata", fake_meta), \
             mock.patch.object(build.api, "download_to", fake_download):
            meta = build.build_database(dest=db)

        self.assertTrue(os.path.exists(db))
        self.assertEqual(meta["bulk_id"], "abc")
        self.assertEqual(meta["unique_cards"], 1)  # token dropped
        # meta.json written beside the db
        self.assertTrue(os.path.exists(paths.meta_path_for(db)))
        # the intermediate JSON download was cleaned up (only the sqlite + meta remain)
        leftovers = [f for f in os.listdir(os.path.dirname(db)) if f.endswith(".json")
                     and f != "meta.json"]
        self.assertEqual(leftovers, [])


class RemoteFreshnessTests(unittest.TestCase):
    def _existing_db(self, bulk_id="local"):
        d = tempfile.mkdtemp()
        db = os.path.join(d, "cards.sqlite")
        with open(db, "w") as fh:
            fh.write("x")
        with open(paths.meta_path_for(db), "w") as fh:
            json.dump({"built_at": "2099-01-01T00:00:00Z", "bulk_id": bulk_id,
                       "unique_cards": 5}, fh)
        return db

    def test_remote_newer_true_when_ids_differ(self):
        db = self._existing_db(bulk_id="old")
        with mock.patch.object(api, "bulk_metadata",
                               lambda kind="default_cards": {"id": "new", "updated_at": "2026-05-31"}):
            st = status.database_status(db, check_remote=True)
        self.assertTrue(st["remote_newer"])

    def test_remote_newer_false_when_ids_match(self):
        db = self._existing_db(bulk_id="same")
        with mock.patch.object(api, "bulk_metadata",
                               lambda kind="default_cards": {"id": "same"}):
            st = status.database_status(db, check_remote=True)
        self.assertFalse(st["remote_newer"])


class EnsureReadyTests(unittest.TestCase):
    # ensure_ready's default stream is bound at import, so pass our buffer explicitly.
    def test_missing_announces_and_builds(self):
        d = tempfile.mkdtemp()
        db = os.path.join(d, "cards.sqlite")
        buf = io.StringIO()
        with mock.patch.object(status, "build_database", _fake_build):
            res = cli.ensure_ready(db_path=db, stream=buf)
        self.assertTrue(res["available"])
        self.assertIn("Setting up the local card database", buf.getvalue())

    def test_stale_present_warns_but_proceeds(self):
        d = tempfile.mkdtemp()
        db = os.path.join(d, "cards.sqlite")
        with open(db, "w") as fh:
            fh.write("x")
        with open(paths.meta_path_for(db), "w") as fh:
            json.dump({"built_at": "2000-01-01T00:00:00Z", "bulk_id": "x",
                       "unique_cards": 5}, fh)
        buf = io.StringIO()
        res = cli.ensure_ready(db_path=db, stream=buf)
        self.assertTrue(res["available"])
        self.assertFalse(res["built"])
        self.assertIn("older than", buf.getvalue())

    def test_unavailable_notes_fallback(self):
        d = tempfile.mkdtemp()

        def boom(**kw):
            raise api.ScryfallUnreachable("offline")

        buf = io.StringIO()
        with mock.patch.object(status, "build_database", boom):
            res = cli.ensure_ready(db_path=os.path.join(d, "cards.sqlite"), stream=buf)
        self.assertFalse(res["available"])
        self.assertIn("live Scryfall API", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
