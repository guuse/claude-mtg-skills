"""Locate the `.mtg/database/` workspace.

All skill file I/O lives under a `.mtg/` directory in the user's current working
directory (the existing convention). The database lives at
`.mtg/database/cards.sqlite` with a sibling `meta.json`.

When there is no clear working directory to write to (e.g. an interactive chat with
no project folder), the caller should prompt the user for a path and pass it in
explicitly — these helpers only locate/derive the default layout.
"""

import os

DB_FILENAME = "cards.sqlite"
META_FILENAME = "meta.json"


def find_mtg_dir(start=None):
    """Return the nearest existing `.mtg` directory at or above `start`, else None.

    Walks up from `start` (default: cwd) looking for a `.mtg/` folder, so the skills
    find the same workspace whether invoked from the project root or a subdirectory.
    """
    cur = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(cur, ".mtg")
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def database_dir(mtg_dir=None, start=None):
    """Return `<.mtg>/database`, creating nothing. Falls back to `./.mtg/database`."""
    base = mtg_dir or find_mtg_dir(start) or os.path.join(os.path.abspath(start or os.getcwd()), ".mtg")
    return os.path.join(base, "database")


def default_db_path(start=None):
    """Path to `cards.sqlite` under the nearest `.mtg/` (existing or cwd-relative)."""
    return os.path.join(database_dir(start=start), DB_FILENAME)


def meta_path_for(db_path):
    """`meta.json` path sitting beside the given database file."""
    return os.path.join(os.path.dirname(db_path), META_FILENAME)
