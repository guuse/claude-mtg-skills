"""mtg_scryfall — shared card-data layer for the MTG deckbuilding skills.

The skills read card data from a local SQLite database built from Scryfall's
"Default Cards" bulk file (see docs/adr/0001) instead of calling the Scryfall API
for everything the bulk data supports. Queries that use `function:`/`otag:` (Tagger)
tags, or any operator the local translator can't serve, are routed whole to the live
Scryfall API instead of being answered incorrectly from the database.

Public API:
    search(query, limit, order, raw, db_path) -> list[dict]   # DB-first, API fallback
    named(name, db_path) -> dict | None                       # DB-first, API fallback
    arena_lookup(db_path) -> dict                             # {arena_id: {name,set,collector_number}}
    arena_table_present(db_path) -> bool                      # does the DB carry the Arena-id map?
    build_database(dest, force, progress) -> dict             # download + build SQLite
    database_status(db_path) -> dict                          # exists / age / staleness
    ensure_database(db_path, progress, ask) -> dict           # auto-build-on-demand
    default_db_path() -> str | None                           # <workspace>/database/cards.sqlite
    workspace_paths() -> dict                                 # resolved decks/collection/db dirs
    load_collection(path) -> dict | None                      # parse a txt/csv/json owned-card export
    sync.status()/pull()/push(msg)/init(url) -> dict          # git-backed workspace sync
    sync.push_database()/pull_database() -> dict              # sync cards.sqlite via Git LFS
    edhrec.commander/average_deck/theme/budget(name) -> dict  # EDHREC JSON (proven inclusions)
    decks.fetch_deck(url_or_id) -> dict                       # import an Archidekt/Moxfield list
    mtgtop8.fetch_meta/fetch_deck/top_decklists(fmt) -> ...   # live metagame + real decklists
    get_json(url) -> obj ; get_text(url) -> str ; FetchError  # robust HTTPS fetch (UA, retry)

All external HTTP goes through the same polite, retrying, HTTPS-only fetcher (mtg_scryfall.http);
a miss raises FetchError so callers fall back to local data and tell the user which source failed.

Stdlib only — no pip install required.
"""

# Every bundled script is a CLI tool that prints status with Unicode glyphs (✓ ✗ → • ★)
# and card names with accents (é, ö, …), and they all import this package before printing.
# On a non-UTF-8 console — notably Windows' default cp1252 — that raises UnicodeEncodeError
# mid-output and crashes the run. Force UTF-8 on stdout/stderr at import time so output is
# never lossy or fatal. Guarded: under pytest or other wrappers the streams are replaced by
# objects without `.reconfigure` (or that reject it), where we simply leave them as-is.
import sys as _sys

for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # Python 3.7+ TextIOWrapper
    except (AttributeError, ValueError, OSError):
        pass

from .paths import default_db_path, find_mtg_dir, workspace_paths
from .query import (
    search, named, to_sql, SUPPORTED_FALLBACK, arena_lookup, arena_table_present,
)
from .build import build_database, build_from_json
from .status import database_status, ensure_database, STALE_AFTER_DAYS
from .cli import ensure_ready
from .arena import TIER_CAPS, BASICS, parse_deck, tally_wildcards
from .collection import find_collection_file, parse_collection, load_collection
from .validate import validate_commander_import, validate_arena_import
from .http import FetchError, get_json, get_text
from . import sync
from . import edhrec
from . import decks
from . import mtgtop8

__all__ = [
    "default_db_path",
    "find_mtg_dir",
    "workspace_paths",
    "search",
    "named",
    "to_sql",
    "SUPPORTED_FALLBACK",
    "arena_lookup",
    "arena_table_present",
    "build_database",
    "build_from_json",
    "database_status",
    "ensure_database",
    "ensure_ready",
    "STALE_AFTER_DAYS",
    "TIER_CAPS",
    "BASICS",
    "parse_deck",
    "tally_wildcards",
    "find_collection_file",
    "parse_collection",
    "load_collection",
    "validate_commander_import",
    "validate_arena_import",
    "FetchError",
    "get_json",
    "get_text",
    "sync",
    "edhrec",
    "decks",
    "mtgtop8",
]
