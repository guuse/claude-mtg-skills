"""Git-backed sync for the MTG workspace (decks + collection).

The workspace (resolved by `paths.py`, normally via `$MTG_HOME`) can be a clone of the
user's private `mtg-data` git repo. These helpers let the mtg-sync skill **pull** the
latest decks/collection before a build and **push** new ones after — so the same data
follows the user across machines. The card database lives in the same workspace but is
git-ignored (rebuildable), so it never syncs.

Design rules (mirroring how the database is best-effort, never blocking):
- Everything degrades gracefully: no git, no network, or a workspace that isn't a repo
  → return a `skipped`/failed result with a reason, **never raise**. The caller proceeds
  with the local workspace regardless.
- All git invocations go through `_run`, a thin wrapper that tests monkeypatch — so the
  logic is exercised without touching a real repo or the network.
"""

import os
import subprocess

from .paths import mtg_home, workspace_paths


def _run(args, cwd=None):
    """Run a command; return (returncode, stdout, stderr). Never raises.

    A missing executable (e.g. git not installed) comes back as code 127 rather than a
    FileNotFoundError, so callers have a single, uniform failure path.
    """
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except (FileNotFoundError, OSError) as e:  # pragma: no cover - exercised via _run mock
        return 127, "", str(e)


def git_available():
    """True if a `git` executable is callable."""
    code, _, _ = _run(["git", "--version"])
    return code == 0


def is_git_repo(path):
    """True if `path` exists and sits inside a git work tree."""
    if not path or not os.path.isdir(path):
        return False
    code, out, _ = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path)
    return code == 0 and out == "true"


def workspace_root():
    """The resolved workspace root (whether or not it exists yet)."""
    return workspace_paths()["paths"]["home"]


def status():
    """Describe the workspace's sync state. Creates nothing, never raises.

    Returns: {home, from_env, git, exists, is_repo, remote, branch, dirty, ahead, behind}.
    Fields past `is_repo` are populated only when the workspace is a usable git repo.
    """
    home = workspace_root()
    info = {
        "home": home,
        "from_env": mtg_home() is not None,
        "git": git_available(),
        "exists": os.path.isdir(home),
        "is_repo": False,
        "remote": None,
        "branch": None,
        "dirty": None,
        "ahead": None,
        "behind": None,
    }
    if not info["git"] or not is_git_repo(home):
        return info
    info["is_repo"] = True
    _, remote, _ = _run(["git", "remote", "get-url", "origin"], cwd=home)
    info["remote"] = remote or None
    _, branch, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=home)
    info["branch"] = branch or None
    _, dirty, _ = _run(["git", "status", "--porcelain"], cwd=home)
    info["dirty"] = bool(dirty)
    code, ab, _ = _run(
        ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"], cwd=home)
    if code == 0 and ab:
        parts = ab.replace("\t", " ").split()
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            info["behind"], info["ahead"] = int(parts[0]), int(parts[1])
    return info


def _guard(home):
    """Return a skip-result if syncing can't run here, else None."""
    if not git_available():
        return {"ok": False, "skipped": True, "reason": "git is not installed", "home": home}
    if not is_git_repo(home):
        return {"ok": False, "skipped": True,
                "reason": "workspace is not a git repo (run mtg-sync --init, or set "
                          "MTG_HOME to a cloned data repo — see SYNCING.md)",
                "home": home}
    return None


def pull():
    """`git pull --rebase --autostash` in the workspace. Best-effort."""
    home = workspace_root()
    skip = _guard(home)
    if skip:
        return skip
    code, out, err = _run(["git", "pull", "--rebase", "--autostash"], cwd=home)
    return {
        "ok": code == 0,
        "skipped": False,
        "home": home,
        "message": out or err,
        "reason": None if code == 0 else "pull failed",
    }


def push(message=None):
    """Stage decks/ + collection/, commit if needed, and push. Best-effort.

    Returns {ok, skipped, committed, home, message, reason}. With nothing new to commit
    it still attempts a push (to ship any local commits not yet upstream).
    """
    home = workspace_root()
    skip = _guard(home)
    if skip:
        skip["committed"] = False
        return skip

    # Stage only the user-data folders; the git-ignored database/ is left alone. Also stage
    # .gitignore when present so the "never sync the database" rule travels to every clone.
    _run(["git", "add", "--", "decks", "collection"], cwd=home)
    if os.path.exists(os.path.join(home, ".gitignore")):
        _run(["git", "add", "--", ".gitignore"], cwd=home)
    _, staged, _ = _run(["git", "diff", "--cached", "--name-only"], cwd=home)

    if not staged:
        code, out, err = _run(["git", "push"], cwd=home)
        return {
            "ok": code == 0,
            "skipped": False,
            "committed": False,
            "home": home,
            "message": out or err or "nothing to commit; workspace already up to date",
            "reason": None if code == 0 else "push failed",
        }

    msg = (message or "").strip() or "Update MTG decks & collection"
    code_c, out_c, err_c = _run(["git", "commit", "-m", msg], cwd=home)
    if code_c != 0:
        return {"ok": False, "skipped": False, "committed": False, "home": home,
                "message": err_c or out_c, "reason": "commit failed"}
    code_p, out_p, err_p = _run(["git", "push"], cwd=home)
    return {
        "ok": code_p == 0,
        "skipped": False,
        "committed": True,
        "home": home,
        "message": out_p or err_p,
        "reason": None if code_p == 0 else "push failed (commit is saved locally)",
    }


def _scaffold(home):
    """Ensure decks/ + collection/ exist and database/ is git-ignored inside `home`."""
    for sub in ("decks", "collection"):
        os.makedirs(os.path.join(home, sub), exist_ok=True)
        keep = os.path.join(home, sub, ".keep")
        if not os.path.exists(keep):
            with open(keep, "w", encoding="utf-8"):
                pass
    gi = os.path.join(home, ".gitignore")
    existing = ""
    if os.path.exists(gi):
        with open(gi, encoding="utf-8") as fh:
            existing = fh.read()
    if "database/" not in existing.split():
        with open(gi, "a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write("# Rebuildable Scryfall card cache — never sync it.\ndatabase/\n")


def init(url, path=None):
    """Clone the user's private data repo to `path` and scaffold the layout.

    Does NOT set `$MTG_HOME` (that must persist in the user's shell profile — the skill
    handles it). Returns {ok, path, cloned, reason}.
    """
    if not git_available():
        return {"ok": False, "reason": "git is not installed", "path": None, "cloned": False}
    dest = os.path.abspath(os.path.expanduser(path or os.path.join("~", "mtg-data")))

    if os.path.isdir(dest) and os.listdir(dest):
        if is_git_repo(dest):
            _scaffold(dest)
            return {"ok": True, "path": dest, "cloned": False,
                    "reason": "already cloned; ensured layout"}
        return {"ok": False, "path": dest, "cloned": False,
                "reason": f"{dest} exists and is not an empty dir / git repo"}

    code, out, err = _run(["git", "clone", url, dest])
    if code != 0:
        return {"ok": False, "path": dest, "cloned": False, "reason": err or out}
    _scaffold(dest)
    return {"ok": True, "path": dest, "cloned": True, "reason": None}
