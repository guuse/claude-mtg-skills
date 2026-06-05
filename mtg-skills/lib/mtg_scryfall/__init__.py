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
    sync.status()/pull()/push(msg)/init(url) -> dict          # git-backed workspace sync
    sync.push_database()/pull_database() -> dict              # sync cards.sqlite via Git LFS

Stdlib only — no pip install required.
"""

from .paths import default_db_path, find_mtg_dir, workspace_paths
from .query import (
    search, named, to_sql, SUPPORTED_FALLBACK, arena_lookup, arena_table_present,
)
from .build import build_database, build_from_json
from .status import database_status, ensure_database, STALE_AFTER_DAYS
from .cli import ensure_ready
from .arena import TIER_CAPS, BASICS, parse_deck, tally_wildcards
from .validate import validate_commander_import, validate_arena_import
from . import sync

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
    "validate_commander_import",
    "validate_arena_import",
    "sync",
]
