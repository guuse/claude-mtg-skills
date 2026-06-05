"""Locate the MTG workspace (`database/`, `decks/`, `collection/`).

All skill file I/O lives under one workspace directory that holds three siblings:
`database/` (the built `cards.sqlite` + `meta.json`), `decks/` (built decks), and
`collection/` (the user's owned-card exports).

How the workspace is resolved, in order:

1. **`MTG_HOME` env var** — if set, that directory *is* the workspace. This is the knob
   for keeping your decks + collection in one place that follows you across machines
   (e.g. a private `mtg-data` git repo cloned on each computer; see SYNCING.md). Takes
   precedence everywhere and is honoured even if it doesn't exist yet — the build step
   creates the subdirectories.
2. **Nearest `.mtg/` at or above the cwd** — the original convention, so the skills find
   the same workspace whether invoked from the project root or a subdirectory.
3. **`./.mtg/`** — the cwd-relative default when nothing else is found.

When there is no clear working directory to write to (e.g. an interactive chat with no
project folder), the caller should prompt the user for a path (or have them set
`MTG_HOME`) and pass it in explicitly — these helpers only locate/derive the layout.
"""

import os

DB_FILENAME = "cards.sqlite"
META_FILENAME = "meta.json"


def mtg_home():
    """Return the workspace root from `MTG_HOME` (expanded, absolute), or None.

    An unset or empty/whitespace-only `MTG_HOME` is treated as "not configured" so a
    stray empty value never silently redirects file I/O to the filesystem root.
    """
    raw = os.environ.get("MTG_HOME")
    if not raw or not raw.strip():
        return None
    return os.path.abspath(os.path.expanduser(raw.strip()))


def find_mtg_dir(start=None):
    """Return the workspace directory: `MTG_HOME` if set, else the nearest `.mtg/`.

    Walks up from `start` (default: cwd) looking for a `.mtg/` folder. Returns None only
    when `MTG_HOME` is unset and no `.mtg/` exists at or above `start`.
    """
    home = mtg_home()
    if home:
        return home
    cur = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(cur, ".mtg")
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def _workspace(mtg_dir=None, start=None):
    """The workspace root to build subdirs from. Falls back to `./.mtg`."""
    return mtg_dir or find_mtg_dir(start) or os.path.join(
        os.path.abspath(start or os.getcwd()), ".mtg")


def database_dir(mtg_dir=None, start=None):
    """Return `<workspace>/database`, creating nothing."""
    return os.path.join(_workspace(mtg_dir, start), "database")


def decks_dir(mtg_dir=None, start=None):
    """Return `<workspace>/decks`, creating nothing."""
    return os.path.join(_workspace(mtg_dir, start), "decks")


def collection_dir(mtg_dir=None, start=None):
    """Return `<workspace>/collection`, creating nothing."""
    return os.path.join(_workspace(mtg_dir, start), "collection")


def default_db_path(start=None):
    """Path to `cards.sqlite` under the resolved workspace."""
    return os.path.join(database_dir(start=start), DB_FILENAME)


def meta_path_for(db_path):
    """`meta.json` path sitting beside the given database file."""
    return os.path.join(os.path.dirname(db_path), META_FILENAME)


def is_lfs_pointer(path):
    """True if `path` is an unmaterialized Git LFS pointer rather than real content.

    When the card database is synced via Git LFS (see sync.py / SYNCING.md) and a clone
    lands on a machine without the git-lfs extension installed, the working file is a tiny
    text stub beginning with the LFS spec URL — not the real SQLite bytes. Callers gate DB
    use on this so a pointer is never opened as SQLite; they fall back to fetching (git lfs
    pull) or rebuilding the database instead. A genuine `cards.sqlite` starts with the
    "SQLite format 3" magic, so this only ever matches real pointer stubs.
    """
    try:
        with open(path, "rb") as fh:
            return fh.read(64).startswith(b"version https://git-lfs.github.com/spec/")
    except OSError:
        return False


def workspace_paths(start=None):
    """Resolve the full workspace layout, for tooling that needs to report it.

    Returns a dict with the workspace root and its three siblings (plus the db file),
    each as an absolute path with an `_exists` flag, and `from_env` to show whether
    `MTG_HOME` drove the result. Creates nothing.
    """
    root = _workspace(start=start)
    db = os.path.join(root, "database", DB_FILENAME)
    layout = {
        "home": root,
        "database": os.path.join(root, "database"),
        "decks": os.path.join(root, "decks"),
        "collection": os.path.join(root, "collection"),
        "db_file": db,
    }
    return {
        "from_env": mtg_home() is not None,
        "paths": layout,
        "exists": {k: os.path.exists(v) for k, v in layout.items()},
    }
