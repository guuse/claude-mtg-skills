"""Tests for mtg_scryfall.sync — git-backed workspace sync, fully offline.

Every git call goes through sync._run, which these tests monkeypatch with a programmable
fake (matched by a substring of the joined argv), so no real repo or network is touched.
The workspace root is controlled by setting MTG_HOME to a tempdir.
"""

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


if __name__ == "__main__":
    unittest.main()
