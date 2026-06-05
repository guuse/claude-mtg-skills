"""Git-backed sync for the MTG workspace (decks + collection).

The workspace (resolved by `paths.py`, normally via `$MTG_HOME`) can be a clone of the
user's private `mtg-data` git repo. These helpers let the mtg-sync skill **pull** the
latest decks/collection before a build and **push** new ones after — so the same data
follows the user across machines.

The card database lives in the same workspace and is git-ignored by default so those
routine deck/collection syncs stay lean. It can *also* be synced on demand via
`push_database()` / `pull_database()`: because it's a >100 MB binary (over GitHub's
per-file limit) it's tracked with **Git LFS** and force-added past the ignore rule, and
shipped only when the mtg-db skill (re)builds it — not on every deck save.

Design rules (mirroring how the database is best-effort, never blocking):
- Everything degrades gracefully: no git, no network, or a workspace that isn't a repo
  → return a `skipped`/failed result with a reason, **never raise**. The caller proceeds
  with the local workspace regardless.
- All git invocations go through `_run`, a thin wrapper that tests monkeypatch — so the
  logic is exercised without touching a real repo or the network.
"""

import json
import os
import shutil
import subprocess

from .paths import mtg_home, workspace_paths

# The plugin this data repo auto-installs. Used to generate the repo's
# .claude/settings.json so a fresh clone wires up the skills with no manual steps.
MARKETPLACE_REPO = "guuse/claude-mtg-skills"
MARKETPLACE_NAME = "claude-mtg-skills"
PLUGIN_NAME = "mtg-skills"
DEFAULT_REPO_NAME = "mtg-data"

GITIGNORE_TEMPLATE = (
    "# Scryfall card cache. Ignored by default so routine deck/collection syncs stay lean;\n"
    "# the mtg-db skill force-adds cards.sqlite + meta.json via Git LFS only when you choose\n"
    "# to sync the database (sync.py --push-database).\n"
    "database/\n\n"
    "# OS / Python noise\n"
    ".DS_Store\n"
    "__pycache__/\n"
    "*.pyc\n"
)

# The card database is large (~170 MB) and binary, and GitHub rejects single files over
# 100 MB on regular git — so it's tracked via Git LFS when synced. Only the .sqlite needs
# LFS; the tiny meta.json stays as normal git. The dedicated --push-database command
# force-adds these (database/ build artifacts are otherwise git-ignored).
DB_LFS_PATTERN = "database/cards.sqlite"
GITATTRIBUTES_TEMPLATE = (
    "# Scryfall card database — large binary, stored via Git LFS (see SYNCING.md).\n"
    f"{DB_LFS_PATTERN} filter=lfs diff=lfs merge=lfs -text\n"
)
DB_SYNC_FILES = ("database/cards.sqlite", "database/meta.json")


def _settings_json():
    """The .claude/settings.json that makes a clone auto-install + auto-update the plugin."""
    hook = (
        f"claude plugin list 2>/dev/null | grep -q '{PLUGIN_NAME}@{MARKETPLACE_NAME}' "
        f"|| {{ claude plugin marketplace add {MARKETPLACE_REPO} >/dev/null 2>&1; "
        f"claude plugin install {PLUGIN_NAME}@{MARKETPLACE_NAME} --scope user >/dev/null 2>&1; }} || true"
    )
    data = {
        "extraKnownMarketplaces": {
            MARKETPLACE_NAME: {
                "source": {"source": "github", "repo": MARKETPLACE_REPO},
                "autoUpdate": True,
            }
        },
        "enabledPlugins": {f"{PLUGIN_NAME}@{MARKETPLACE_NAME}": True},
        "hooks": {
            "SessionStart": [
                {"matcher": "startup", "hooks": [{"type": "command", "command": hook}]}
            ]
        },
    }
    return json.dumps(data, indent=2) + "\n"


def _readme():
    """The data repo's README (written only if one doesn't already exist)."""
    return (
        f"# {DEFAULT_REPO_NAME}\n\n"
        f"My private Magic: The Gathering workspace for the "
        f"[{PLUGIN_NAME}](https://github.com/{MARKETPLACE_REPO}) plugin — decks, deck guides, and "
        "collection exports, synced across machines and mobile.\n\n"
        "Point **`MTG_HOME`** at this folder and the skills read/write here. The plugin "
        "**auto-installs** from the marketplace on session start (see `.claude/settings.json`), so a "
        "fresh clone is ready to build and tune decks with no manual setup.\n\n"
        "```\n"
        "decks/<slug>/   built decks (deck.md + import.txt / arena.txt)    synced\n"
        "collection/     collection exports (Archidekt / Arena / Moxfield) synced\n"
        "database/       cards.sqlite — Scryfall cache; rebuilt per machine, optionally\n"
        "                synced via Git LFS (sync.py --push-database / --pull-database)\n"
        "```\n\n"
        "```bash\n"
        'export MTG_HOME="$(pwd)"   # macOS/Linux;  Windows:  setx MTG_HOME "%CD%"\n'
        "```\n\n"
        "Decks/collection sync via the **mtg-sync** skill (pull before a build, push after). The card "
        "database is rebuilt locally by the **mtg-db** skill; you can also sync it across machines "
        "with **Git LFS** (`sync.py --push-database` / `--pull-database`) instead of rebuilding.\n"
    )


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


def lfs_available():
    """True if the Git LFS extension is installed (`git lfs version` succeeds).

    Required to *sync* the card database (it's >100 MB, over GitHub's per-file limit, so
    it lives in LFS). Everything else — decks/collection sync — works without it.
    """
    return _run(["git", "lfs", "version"])[0] == 0


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


# --------------------------------------------------------------------------- #
# Card-database sync (Git LFS). Kept separate from push()/pull() so routine deck #
# saves stay lean — the heavy (~170 MB) database ships only when the mtg-db skill #
# (re)builds it and explicitly asks to sync it.                                   #
# --------------------------------------------------------------------------- #

def _ensure_gitattributes(home):
    """Ensure `.gitattributes` tracks the card database via Git LFS. Non-destructive."""
    ga = os.path.join(home, ".gitattributes")
    if not os.path.exists(ga):
        with open(ga, "w", encoding="utf-8") as fh:
            fh.write(GITATTRIBUTES_TEMPLATE)
        return
    with open(ga, encoding="utf-8") as fh:
        existing = fh.read()
    if DB_LFS_PATTERN not in existing:
        with open(ga, "a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write(GITATTRIBUTES_TEMPLATE)


def _ensure_lfs(home):
    """Prepare `home` to store the card database via Git LFS. Best-effort.

    Writes the `.gitattributes` LFS rule and installs LFS hooks for this repo. Requires
    the git-lfs extension; if it's absent, return ok=False with a reason and the caller
    leaves the database local (it's rebuildable per machine, as always).
    Returns {ok, reason}.
    """
    if not lfs_available():
        return {"ok": False,
                "reason": "git-lfs is not installed — install the Git LFS extension "
                          "(https://git-lfs.com) to sync the card database"}
    _ensure_gitattributes(home)
    code, out, err = _run(["git", "lfs", "install", "--local"], cwd=home)
    if code != 0:
        return {"ok": False, "reason": f"git lfs install failed: {err or out}"}
    return {"ok": True, "reason": None}


def push_database(message=None):
    """Commit + push the built card database (cards.sqlite + meta.json) via Git LFS.

    Separate from push(): the heavy database ships only when explicitly requested (the
    mtg-db skill calls this after a build/refresh), so routine deck saves stay small. The
    files are force-added because database/ is git-ignored by default. Best-effort.
    Returns {ok, skipped, committed, home, message, reason}.
    """
    home = workspace_root()
    skip = _guard(home)
    if skip:
        skip["committed"] = False
        return skip

    lfs = _ensure_lfs(home)
    if not lfs["ok"]:
        return {"ok": False, "skipped": True, "committed": False, "home": home,
                "message": lfs["reason"], "reason": lfs["reason"]}

    present = [f for f in DB_SYNC_FILES if os.path.exists(os.path.join(home, f))]
    if not present:
        return {"ok": False, "skipped": True, "committed": False, "home": home,
                "message": "no built database to push — build it first (mtg-db skill)",
                "reason": "database not built"}

    # Stage the LFS rule plus the database files (force past the database/ ignore rule).
    if os.path.exists(os.path.join(home, ".gitattributes")):
        _run(["git", "add", "--", ".gitattributes"], cwd=home)
    _run(["git", "add", "-f", "--", *present], cwd=home)
    _, staged, _ = _run(["git", "diff", "--cached", "--name-only"], cwd=home)

    if not staged:
        code, out, err = _run(["git", "push"], cwd=home)
        return {"ok": code == 0, "skipped": False, "committed": False, "home": home,
                "message": out or err or "database already up to date",
                "reason": None if code == 0 else "push failed"}

    msg = (message or "").strip() or "Sync MTG card database"
    code_c, out_c, err_c = _run(["git", "commit", "-m", msg], cwd=home)
    if code_c != 0:
        return {"ok": False, "skipped": False, "committed": False, "home": home,
                "message": err_c or out_c, "reason": "commit failed"}
    code_p, out_p, err_p = _run(["git", "push"], cwd=home)
    return {"ok": code_p == 0, "skipped": False, "committed": True, "home": home,
            "message": out_p or err_p,
            "reason": None if code_p == 0 else "push failed (commit is saved locally)"}


def pull_database():
    """Pull the latest workspace and materialize the LFS-tracked card database.

    Use on another/new machine to fetch the shared database instead of rebuilding it from
    Scryfall. Best-effort. Returns {ok, skipped, home, message, reason}.
    """
    home = workspace_root()
    skip = _guard(home)
    if skip:
        return skip
    code, out, err = _run(["git", "pull", "--rebase", "--autostash"], cwd=home)
    if code != 0:
        return {"ok": False, "skipped": False, "home": home,
                "message": out or err, "reason": "pull failed"}
    msg = out or "up to date"
    if lfs_available():
        lc, lo, le = _run(
            ["git", "lfs", "pull", "--include", DB_LFS_PATTERN], cwd=home)
        if lc != 0:
            return {"ok": False, "skipped": False, "home": home,
                    "message": le or lo, "reason": "git lfs pull failed"}
        msg = f"{msg}; fetched database via LFS"
    else:
        msg = (f"{msg}; note: git-lfs isn't installed, so the database is still an "
               "unfetched pointer — install Git LFS and re-run, or rebuild it (mtg-db skill)")
    return {"ok": True, "skipped": False, "home": home, "message": msg, "reason": None}


def _scaffold(home):
    """Make `home` a complete, auto-install-ready data workspace. Non-destructive:
    creates only what's missing, never clobbers existing files.

    Ensures decks/ + collection/ (with .keep), a .gitignore that excludes the build
    artifacts under database/, a .gitattributes that tracks the card database via Git LFS,
    a README, and .claude/settings.json (which wires up plugin auto-install).
    """
    for sub in ("decks", "collection"):
        os.makedirs(os.path.join(home, sub), exist_ok=True)
        keep = os.path.join(home, sub, ".keep")
        if not os.path.exists(keep):
            with open(keep, "w", encoding="utf-8"):
                pass

    gi = os.path.join(home, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w", encoding="utf-8") as fh:
            fh.write(GITIGNORE_TEMPLATE)
    else:
        with open(gi, encoding="utf-8") as fh:
            existing = fh.read()
        if "database/" not in existing.split():
            with open(gi, "a", encoding="utf-8") as fh:
                if existing and not existing.endswith("\n"):
                    fh.write("\n")
                fh.write("# Scryfall card cache — ignored by default (force-added via LFS "
                         "on --push-database).\ndatabase/\n")

    # Track the (large, binary) card database via Git LFS so --push-database can ship it.
    _ensure_gitattributes(home)

    readme = os.path.join(home, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8") as fh:
            fh.write(_readme())

    claude_dir = os.path.join(home, ".claude")
    os.makedirs(claude_dir, exist_ok=True)
    settings = os.path.join(claude_dir, "settings.json")
    if not os.path.exists(settings):
        with open(settings, "w", encoding="utf-8") as fh:
            fh.write(_settings_json())


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


# --------------------------------------------------------------------------- #
# One-command bootstrap: create-or-reuse the repo, scaffold, migrate, push.    #
# --------------------------------------------------------------------------- #

def gh_available():
    """True if the GitHub CLI (`gh`) is callable — needed to *create* a repo."""
    return _run(["gh", "--version"])[0] == 0


def _normalize_repo(repo):
    """Classify the repo argument. Returns (kind, value, name).

    kind: 'url'  (clone an existing remote, no create),
          'slug' ('owner/name'), or
          'name' (bare name → create under the gh-authenticated user).
    """
    r = (repo or DEFAULT_REPO_NAME).strip()
    if "://" in r or r.startswith("git@") or r.endswith(".git"):
        name = r.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return "url", r, name
    if "/" in r:
        return "slug", r, r.split("/")[-1]
    return "name", r, r


def _ignore_noise(dirpath, names):
    """copytree ignore: drop VCS/OS noise and any *nested git repo* (a checked-out tool,
    e.g. a collection exporter — not the user's data)."""
    drop = set()
    for n in names:
        if n in (".git", ".DS_Store", "__pycache__"):
            drop.add(n)
            continue
        p = os.path.join(dirpath, n)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, ".git")):
            drop.add(n)
    return drop


def _count_data_files(d):
    n = 0
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in (".git", "__pycache__")]
        n += sum(1 for f in files if f not in (".keep", ".DS_Store"))
    return n


def migrate(source, home):
    """Copy decks/ + collection/ from `source` into `home` (merging, non-destructive).

    Skips OS noise and nested git repos. Returns {decks, collection, from, skipped}.
    """
    src = os.path.abspath(os.path.expanduser(source))
    dst = os.path.abspath(os.path.expanduser(home))
    result = {"decks": 0, "collection": 0, "from": src, "skipped": None}
    if src == dst:
        result["skipped"] = "source is the destination"
        return result
    if not os.path.isdir(src):
        result["skipped"] = "source does not exist"
        return result
    for sub in ("decks", "collection"):
        s = os.path.join(src, sub)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(dst, sub), dirs_exist_ok=True, ignore=_ignore_noise)
            result[sub] = _count_data_files(os.path.join(dst, sub))
    return result


def _auto_source(dest):
    """If the resolved workspace differs from `dest` and holds decks/collection, return it."""
    cand = os.path.abspath(os.path.expanduser(workspace_root()))
    if cand != dest and (os.path.isdir(os.path.join(cand, "decks"))
                         or os.path.isdir(os.path.join(cand, "collection"))):
        return cand
    return None


def bootstrap(repo=None, dest=None, private=True, source=None, do_push=True):
    """Seed the entire data repo in one shot. Best-effort, never raises.

    Steps: obtain a clone at `dest` (reuse if already a repo; clone if the remote exists;
    otherwise create it via `gh`), scaffold the full layout (incl. .claude/settings.json
    for plugin auto-install), migrate existing decks/collection, commit, and push.

    `repo`   : bare name (default 'mtg-data'), 'owner/name', or a clone URL.
    `dest`   : local path (default '~/<name>').
    `source` : workspace to migrate from (default: auto-detected current workspace).
    Returns a dict describing exactly what happened (and an `mtg_home` path to export).
    """
    if not git_available():
        return {"ok": False, "reason": "git is not installed"}

    kind, value, name = _normalize_repo(repo)
    dest = os.path.abspath(os.path.expanduser(dest or os.path.join("~", name)))
    slug = value if kind == "slug" else None
    url = value if kind == "url" else None
    created = False

    if is_git_repo(dest):
        action = "reused existing clone"
    elif os.path.isdir(dest) and os.listdir(dest):
        return {"ok": False, "path": dest,
                "reason": f"{dest} exists, is not empty, and is not a git repo"}
    else:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        if url:
            code, out, err = _run(["git", "clone", url, dest])
            if code != 0:
                return {"ok": False, "path": dest, "reason": f"clone failed: {err or out}"}
            action = "cloned"
        else:
            if not gh_available():
                return {"ok": False, "path": dest,
                        "reason": "the gh CLI isn't available to create the repo — install/auth "
                                  "`gh`, or pass an existing clone URL with --repo"}
            if slug is None:
                code, login, err = _run(["gh", "api", "user", "-q", ".login"])
                if code != 0 or not login:
                    return {"ok": False, "path": dest,
                            "reason": f"could not resolve your GitHub user via gh: {err or 'unknown'}"}
                slug = f"{login}/{name}"
            if _run(["gh", "repo", "view", slug])[0] == 0:
                code, out, err = _run(["gh", "repo", "clone", slug, dest])
                if code != 0:
                    return {"ok": False, "path": dest, "reason": f"gh clone failed: {err or out}"}
                action = "cloned existing remote"
            else:
                vis = "--private" if private else "--public"
                code, out, err = _run(
                    ["gh", "repo", "create", slug, vis,
                     "--description", "My MTG decks & collection (claude-mtg-skills)"])
                if code != 0:
                    return {"ok": False, "path": dest, "reason": f"gh repo create failed: {err or out}"}
                created = True
                code, out, err = _run(["gh", "repo", "clone", slug, dest])
                if code != 0:
                    return {"ok": False, "path": dest, "created": True,
                            "reason": f"created the repo but clone failed: {err or out}"}
                action = "created + cloned"

    _scaffold(dest)
    _ensure_lfs(dest)  # best-effort: ready the repo for database sync if git-lfs is present

    src = source if source is not None else _auto_source(dest)
    migrated = migrate(src, dest) if src else {"decks": 0, "collection": 0, "from": None, "skipped": "none"}

    _run(["git", "add", "-A"], cwd=dest)
    _, staged, _ = _run(["git", "diff", "--cached", "--name-only"], cwd=dest)
    committed = False
    if staged:
        cc = _run(["git", "commit", "-m",
                   "Seed MTG data workspace (decks, collection, skills auto-install)"], cwd=dest)
        if cc[0] != 0:
            return {"ok": False, "path": dest, "created": created, "migrated": migrated,
                    "reason": f"commit failed: {cc[2] or cc[1]} "
                              "(set git user.name/user.email, then re-run --bootstrap)"}
        committed = True

    pushed = None
    push_message = None
    if do_push:
        cp = _run(["git", "push", "-u", "origin", "HEAD"], cwd=dest)
        pushed = cp[0] == 0
        push_message = cp[1] or cp[2]

    return {
        "ok": True,
        "path": dest,
        "action": action,
        "created": created,
        "migrated": migrated,
        "committed": committed,
        "pushed": pushed,
        "push_message": push_message,
        "mtg_home": dest,
        "reason": None if (pushed in (None, True)) else f"push failed: {push_message}",
    }
