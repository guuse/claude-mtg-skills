"""Tests for mtg_scryfall.sync — git-backed workspace sync, fully offline.

Every git call goes through sync._run, which these tests monkeypatch with a programmable
fake (matched by a substring of the joined argv), so no real repo or network is touched.
The workspace root is controlled by setting MTG_HOME to a tempdir.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_LIB = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "mtg-skills", "lib"))
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from mtg_scryfall import sync  # noqa: E402


def make_fake(spec, default=(0, "", "")):
    """Build a fake `_run`. `spec` = list of (substring_of_joined_argv, (code,out,err)),
    checked in order; first match wins, else `default`. Records calls on `.calls`."""
    calls = []

    def fake(args, cwd=None):
        calls.append(list(args))
        joined = " ".join(args)
        for sub, resp in spec:
            if sub in joined:
                return resp
        return default

    fake.calls = calls
    return fake


VERSION_OK = ("--version", (0, "git version 2.40.0", ""))
IS_REPO = ("is-inside-work-tree", (0, "true", ""))


class SyncBasicsTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        self.home = tempfile.mkdtemp()
        os.environ["MTG_HOME"] = self.home

    def tearDown(self):
        self._env.stop()

    def test_workspace_root_follows_mtg_home(self):
        self.assertEqual(sync.workspace_root(), os.path.abspath(self.home))

    def test_git_available_true_false(self):
        with mock.patch.object(sync, "_run", make_fake([VERSION_OK])):
            self.assertTrue(sync.git_available())
        with mock.patch.object(sync, "_run", make_fake([("--version", (127, "", "not found"))])):
            self.assertFalse(sync.git_available())

    def test_is_git_repo_nonexistent_path(self):
        # No _run needed: a missing dir short-circuits to False.
        with mock.patch.object(sync, "_run", make_fake([IS_REPO])):
            self.assertFalse(sync.is_git_repo(os.path.join(self.home, "nope")))

    def test_is_git_repo_true_and_false(self):
        with mock.patch.object(sync, "_run", make_fake([IS_REPO])):
            self.assertTrue(sync.is_git_repo(self.home))
        with mock.patch.object(sync, "_run", make_fake([("is-inside-work-tree", (128, "", "fatal"))])):
            self.assertFalse(sync.is_git_repo(self.home))


class StatusTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        self.home = tempfile.mkdtemp()
        os.environ["MTG_HOME"] = self.home

    def tearDown(self):
        self._env.stop()

    def test_status_not_a_repo(self):
        fake = make_fake([VERSION_OK, ("is-inside-work-tree", (128, "", ""))])
        with mock.patch.object(sync, "_run", fake):
            st = sync.status()
        self.assertTrue(st["git"])
        self.assertTrue(st["from_env"])
        self.assertFalse(st["is_repo"])
        self.assertIsNone(st["remote"])

    def test_status_repo_with_ahead_behind(self):
        fake = make_fake([
            VERSION_OK, IS_REPO,
            ("remote get-url", (0, "git@github.com:me/mtg-data.git", "")),
            ("abbrev-ref", (0, "main", "")),
            ("status --porcelain", (0, " M decks/x/deck.md", "")),
            ("rev-list", (0, "2\t1", "")),  # behind=2, ahead=1
        ])
        with mock.patch.object(sync, "_run", fake):
            st = sync.status()
        self.assertTrue(st["is_repo"])
        self.assertEqual(st["remote"], "git@github.com:me/mtg-data.git")
        self.assertEqual(st["branch"], "main")
        self.assertTrue(st["dirty"])
        self.assertEqual((st["behind"], st["ahead"]), (2, 1))

    def test_status_repo_unparseable_revlist_leaves_none(self):
        fake = make_fake([
            VERSION_OK, IS_REPO,
            ("remote get-url", (0, "", "")),       # no remote
            ("abbrev-ref", (0, "main", "")),
            ("status --porcelain", (0, "", "")),   # clean
            ("rev-list", (0, "no-upstream", "")),  # unparseable
        ])
        with mock.patch.object(sync, "_run", fake):
            st = sync.status()
        self.assertIsNone(st["remote"])
        self.assertFalse(st["dirty"])
        self.assertIsNone(st["ahead"])
        self.assertIsNone(st["behind"])


class PullTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        self.home = tempfile.mkdtemp()
        os.environ["MTG_HOME"] = self.home

    def tearDown(self):
        self._env.stop()

    def test_pull_skipped_no_git(self):
        with mock.patch.object(sync, "_run", make_fake([("--version", (127, "", ""))])):
            res = sync.pull()
        self.assertTrue(res["skipped"])
        self.assertIn("git is not installed", res["reason"])

    def test_pull_skipped_not_a_repo(self):
        fake = make_fake([VERSION_OK, ("is-inside-work-tree", (128, "", ""))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.pull()
        self.assertTrue(res["skipped"])
        self.assertIn("not a git repo", res["reason"])

    def test_pull_success(self):
        fake = make_fake([VERSION_OK, IS_REPO, ("pull", (0, "Already up to date.", ""))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.pull()
        self.assertTrue(res["ok"])
        self.assertFalse(res["skipped"])
        self.assertEqual(res["message"], "Already up to date.")

    def test_pull_failure(self):
        fake = make_fake([VERSION_OK, IS_REPO, ("pull", (1, "", "could not resolve host"))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.pull()
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "pull failed")


class PushTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        self.home = tempfile.mkdtemp()
        os.environ["MTG_HOME"] = self.home

    def tearDown(self):
        self._env.stop()

    def test_push_skipped_not_a_repo(self):
        fake = make_fake([VERSION_OK, ("is-inside-work-tree", (128, "", ""))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.push("msg")
        self.assertTrue(res["skipped"])
        self.assertFalse(res["committed"])

    def test_push_nothing_to_commit_still_pushes(self):
        fake = make_fake([
            VERSION_OK, IS_REPO,
            ("diff --cached", (0, "", "")),      # nothing staged
            ("push", (0, "Everything up-to-date", "")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.push()
        self.assertTrue(res["ok"])
        self.assertFalse(res["committed"])

    def test_push_commits_and_pushes_and_stages_gitignore(self):
        # A .gitignore present must be staged so the database-ignore rule travels.
        with open(os.path.join(self.home, ".gitignore"), "w") as fh:
            fh.write("database/\n")
        fake = make_fake([
            VERSION_OK, IS_REPO,
            ("diff --cached", (0, "decks/atraxa/deck.md", "")),
            ("commit", (0, "1 file changed", "")),
            ("push", (0, "main -> main", "")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.push("Add Atraxa deck")
        self.assertTrue(res["ok"])
        self.assertTrue(res["committed"])
        self.assertIn(["git", "add", "--", ".gitignore"], fake.calls)

    def test_push_commit_failure(self):
        fake = make_fake([
            VERSION_OK, IS_REPO,
            ("diff --cached", (0, "decks/x/deck.md", "")),
            ("commit", (1, "", "nothing to commit?")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.push()
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "commit failed")

    def test_push_push_failure_after_commit(self):
        fake = make_fake([
            VERSION_OK, IS_REPO,
            ("diff --cached", (0, "decks/x/deck.md", "")),
            ("commit", (0, "committed", "")),
            ("push", (1, "", "rejected")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.push()
        self.assertFalse(res["ok"])
        self.assertTrue(res["committed"])
        self.assertIn("push failed", res["reason"])


class InitAndScaffoldTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()

    def tearDown(self):
        self._env.stop()

    def test_init_no_git(self):
        with mock.patch.object(sync, "_run", make_fake([("--version", (127, "", ""))])):
            res = sync.init("git@github.com:me/mtg-data.git",
                            os.path.join(tempfile.mkdtemp(), "dest"))
        self.assertFalse(res["ok"])
        self.assertIn("git is not installed", res["reason"])

    def test_init_clone_success_scaffolds(self):
        dest = os.path.join(tempfile.mkdtemp(), "mtg-data")  # does not exist yet
        fake = make_fake([VERSION_OK, ("clone", (0, "Cloning...", ""))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.init("git@github.com:me/mtg-data.git", dest)
        self.assertTrue(res["ok"])
        self.assertTrue(res["cloned"])
        self.assertTrue(os.path.exists(os.path.join(dest, "decks", ".keep")))
        self.assertTrue(os.path.exists(os.path.join(dest, "collection", ".keep")))
        with open(os.path.join(dest, ".gitignore")) as fh:
            self.assertIn("database/", fh.read())

    def test_init_clone_failure(self):
        dest = os.path.join(tempfile.mkdtemp(), "mtg-data")
        fake = make_fake([VERSION_OK, ("clone", (128, "", "Permission denied (publickey)"))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.init("git@github.com:me/private.git", dest)
        self.assertFalse(res["ok"])
        self.assertIn("Permission denied", res["reason"])

    def test_init_dest_exists_and_is_repo(self):
        dest = tempfile.mkdtemp()
        open(os.path.join(dest, "stuff"), "w").close()  # non-empty
        fake = make_fake([VERSION_OK, IS_REPO])
        with mock.patch.object(sync, "_run", fake):
            res = sync.init("git@github.com:me/mtg-data.git", dest)
        self.assertTrue(res["ok"])
        self.assertFalse(res["cloned"])
        self.assertTrue(os.path.exists(os.path.join(dest, "decks")))

    def test_init_dest_exists_not_repo(self):
        dest = tempfile.mkdtemp()
        open(os.path.join(dest, "stuff"), "w").close()  # non-empty, not a repo
        fake = make_fake([VERSION_OK, ("is-inside-work-tree", (128, "", ""))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.init("git@github.com:me/mtg-data.git", dest)
        self.assertFalse(res["ok"])
        self.assertIn("not an empty", res["reason"])

    def test_scaffold_preserves_existing_gitignore_without_dup(self):
        home = tempfile.mkdtemp()
        with open(os.path.join(home, ".gitignore"), "w") as fh:
            fh.write("database/\n*.tmp\n")
        sync._scaffold(home)
        with open(os.path.join(home, ".gitignore")) as fh:
            body = fh.read()
        self.assertEqual(body.count("database/"), 1)  # not appended again

    def test_scaffold_appends_when_missing_rule_no_trailing_newline(self):
        home = tempfile.mkdtemp()
        with open(os.path.join(home, ".gitignore"), "w") as fh:
            fh.write(".DS_Store")  # no trailing newline, no database/ rule
        sync._scaffold(home)
        with open(os.path.join(home, ".gitignore")) as fh:
            body = fh.read()
        self.assertIn("database/", body)
        self.assertIn(".DS_Store", body)


class NormalizeRepoTests(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(sync._normalize_repo(None)[0], "name")
        self.assertEqual(sync._normalize_repo("mtg-data"), ("name", "mtg-data", "mtg-data"))
        self.assertEqual(sync._normalize_repo("guuse/mtg-data"), ("slug", "guuse/mtg-data", "mtg-data"))
        k, _v, n = sync._normalize_repo("https://github.com/guuse/mtg-data.git")
        self.assertEqual((k, n), ("url", "mtg-data"))
        k, _v, n = sync._normalize_repo("git@github.com:guuse/mtg-data.git")
        self.assertEqual((k, n), ("url", "mtg-data"))


class ScaffoldExtrasTests(unittest.TestCase):
    def test_scaffold_writes_readme_and_settings(self):
        home = tempfile.mkdtemp()
        sync._scaffold(home)
        self.assertTrue(os.path.exists(os.path.join(home, "decks", ".keep")))
        self.assertTrue(os.path.exists(os.path.join(home, "README.md")))
        sj = os.path.join(home, ".claude", "settings.json")
        self.assertTrue(os.path.exists(sj))
        with open(sj) as fh:
            d = json.load(fh)
        self.assertIn(sync.MARKETPLACE_NAME, d["extraKnownMarketplaces"])
        self.assertTrue(d["enabledPlugins"][f"{sync.PLUGIN_NAME}@{sync.MARKETPLACE_NAME}"])
        self.assertIn("SessionStart", d["hooks"])

    def test_scaffold_is_nondestructive(self):
        home = tempfile.mkdtemp()
        os.makedirs(os.path.join(home, ".claude"))
        with open(os.path.join(home, ".claude", "settings.json"), "w") as fh:
            fh.write('{"mine": true}')
        with open(os.path.join(home, "README.md"), "w") as fh:
            fh.write("custom")
        sync._scaffold(home)
        with open(os.path.join(home, ".claude", "settings.json")) as fh:
            self.assertEqual(json.load(fh), {"mine": True})
        with open(os.path.join(home, "README.md")) as fh:
            self.assertEqual(fh.read(), "custom")


class MigrateTests(unittest.TestCase):
    def _src(self):
        s = tempfile.mkdtemp()
        os.makedirs(os.path.join(s, "decks", "atraxa"))
        open(os.path.join(s, "decks", "atraxa", "deck.md"), "w").close()
        os.makedirs(os.path.join(s, "collection"))
        open(os.path.join(s, "collection", "col.txt"), "w").close()
        os.makedirs(os.path.join(s, "collection", "tool", ".git"))  # nested repo = a tool
        open(os.path.join(s, "collection", "tool", "x.py"), "w").close()
        open(os.path.join(s, "decks", ".DS_Store"), "w").close()  # noise
        return s

    def test_copies_data_skips_nested_repo_and_noise(self):
        home = tempfile.mkdtemp()
        res = sync.migrate(self._src(), home)
        self.assertTrue(os.path.exists(os.path.join(home, "decks", "atraxa", "deck.md")))
        self.assertTrue(os.path.exists(os.path.join(home, "collection", "col.txt")))
        self.assertFalse(os.path.exists(os.path.join(home, "collection", "tool")))   # nested repo skipped
        self.assertFalse(os.path.exists(os.path.join(home, "decks", ".DS_Store")))   # noise skipped
        self.assertGreaterEqual(res["decks"], 1)

    def test_same_path_skipped(self):
        h = tempfile.mkdtemp()
        self.assertEqual(sync.migrate(h, h)["skipped"], "source is the destination")

    def test_missing_source_skipped(self):
        h = tempfile.mkdtemp()
        self.assertEqual(sync.migrate(os.path.join(h, "nope"), h)["skipped"], "source does not exist")


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        # Neutral workspace so _auto_source() doesn't pick up the real repo's .mtg.
        os.environ["MTG_HOME"] = tempfile.mkdtemp()

    def tearDown(self):
        self._env.stop()

    def _src_with_deck(self):
        s = tempfile.mkdtemp()
        os.makedirs(os.path.join(s, "decks", "d"))
        open(os.path.join(s, "decks", "d", "deck.md"), "w").close()
        return s

    def test_no_git(self):
        with mock.patch.object(sync, "_run", make_fake([("git --version", (127, "", ""))])):
            res = sync.bootstrap(repo="mtg-data")
        self.assertFalse(res["ok"])
        self.assertIn("git is not installed", res["reason"])

    def test_url_clone_happy(self):
        dest = os.path.join(tempfile.mkdtemp(), "ws")
        fake = make_fake([
            ("git --version", (0, "", "")),
            ("git clone", (0, "", "")),
            ("diff --cached", (0, "decks/d/deck.md", "")),
            ("commit", (0, "", "")),
            ("push", (0, "main -> main", "")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="https://github.com/guuse/mtg-data.git",
                                 dest=dest, source=self._src_with_deck())
        self.assertTrue(res["ok"])
        self.assertEqual(res["action"], "cloned")
        self.assertTrue(res["committed"] and res["pushed"])
        self.assertTrue(os.path.exists(os.path.join(dest, ".claude", "settings.json")))
        self.assertTrue(os.path.exists(os.path.join(dest, "decks", "d", "deck.md")))  # migrated

    def test_clone_failure(self):
        dest = os.path.join(tempfile.mkdtemp(), "ws")
        fake = make_fake([("git --version", (0, "", "")), ("git clone", (128, "", "boom"))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="https://x/y.git", dest=dest, source=None)
        self.assertFalse(res["ok"])
        self.assertIn("clone failed", res["reason"])

    def test_gh_create_happy(self):
        dest = os.path.join(tempfile.mkdtemp(), "mtg-data")
        fake = make_fake([
            ("git --version", (0, "", "")),
            ("gh --version", (0, "", "")),
            ("api user", (0, "guuse", "")),
            ("repo view", (1, "", "not found")),   # remote doesn't exist yet
            ("repo create", (0, "", "")),
            ("repo clone", (0, "", "")),
            ("diff --cached", (0, "decks/d/deck.md", "")),
            ("commit", (0, "", "")),
            ("push", (0, "ok", "")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="mtg-data", dest=dest, source=self._src_with_deck())
        self.assertTrue(res["ok"])
        self.assertTrue(res["created"])
        self.assertEqual(res["action"], "created + cloned")
        self.assertTrue(res["pushed"])

    def test_gh_missing_for_create(self):
        dest = os.path.join(tempfile.mkdtemp(), "mtg-data")
        fake = make_fake([("git --version", (0, "", "")), ("gh --version", (127, "", ""))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="mtg-data", dest=dest, source=None)
        self.assertFalse(res["ok"])
        self.assertIn("gh CLI", res["reason"])

    def test_dest_exists_nonempty_nonrepo(self):
        dest = tempfile.mkdtemp()
        open(os.path.join(dest, "x"), "w").close()
        fake = make_fake([("git --version", (0, "", "")), ("is-inside-work-tree", (128, "", ""))])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="mtg-data", dest=dest)
        self.assertFalse(res["ok"])
        self.assertIn("not empty", res["reason"])

    def test_reused_existing_repo(self):
        dest = tempfile.mkdtemp()
        os.environ["MTG_HOME"] = dest  # _auto_source → None (cand == dest)
        fake = make_fake([
            ("git --version", (0, "", "")),
            ("is-inside-work-tree", (0, "true", "")),
            ("diff --cached", (0, "", "")),     # nothing new to commit
            ("push", (0, "up to date", "")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="mtg-data", dest=dest, source=None)
        self.assertTrue(res["ok"])
        self.assertEqual(res["action"], "reused existing clone")
        self.assertFalse(res["committed"])
        self.assertTrue(res["pushed"])
        self.assertTrue(os.path.exists(os.path.join(dest, ".claude", "settings.json")))

    def test_push_failure_is_reported_but_ok(self):
        dest = os.path.join(tempfile.mkdtemp(), "ws")
        fake = make_fake([
            ("git --version", (0, "", "")), ("git clone", (0, "", "")),
            ("diff --cached", (0, "decks/d/deck.md", "")), ("commit", (0, "", "")),
            ("push", (1, "", "rejected")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="https://x/y.git", dest=dest, source=self._src_with_deck())
        self.assertTrue(res["ok"])
        self.assertFalse(res["pushed"])
        self.assertIn("push failed", res["reason"])

    def test_no_push_flag(self):
        dest = os.path.join(tempfile.mkdtemp(), "ws")
        fake = make_fake([
            ("git --version", (0, "", "")), ("git clone", (0, "", "")),
            ("diff --cached", (0, "decks/d/deck.md", "")), ("commit", (0, "", "")),
        ])
        with mock.patch.object(sync, "_run", fake):
            res = sync.bootstrap(repo="https://x/y.git", dest=dest,
                                 source=self._src_with_deck(), do_push=False)
        self.assertTrue(res["ok"])
        self.assertIsNone(res["pushed"])


if __name__ == "__main__":
    unittest.main()
