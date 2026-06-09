"""Database status, staleness, and auto-build-on-demand.

Policy (see the design summary):
- Missing DB  -> notify and build (caller decides whether to ask; default is build).
- Present DB, older than STALE_AFTER_DAYS -> caller should *ask* before refreshing.
- A cheap `/bulk-data` check avoids re-downloading when Scryfall itself hasn't updated.
"""

import datetime
import json
import os

from . import api
from .build import build_database
from .paths import default_db_path, is_lfs_pointer, meta_path_for

STALE_AFTER_DAYS = 30


def _read_meta(db_path):
    try:
        with open(meta_path_for(db_path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _age_days(meta):
    built = meta.get("built_at")
    if not built:
        return None
    try:
        dt = datetime.datetime.strptime(built, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc
        )
    except ValueError:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    return (now - dt).total_seconds() / 86400.0


def database_status(db_path=None, check_remote=False):
    """Describe the local database.

    Returns a dict: {exists, db_path, age_days, stale, unique_cards, built_at,
    bulk_updated_at, remote_newer (only if check_remote)}.
    `check_remote=True` does one small `/bulk-data` call to see if Scryfall has a newer
    bulk than the local one (so a "stale" DB that matches the latest needn't re-download).
    """
    db_path = db_path or default_db_path()
    # An unfetched Git LFS pointer (git-lfs not installed on this clone) is a text stub,
    # not a real DB — treat it as absent so we rebuild/fetch rather than mis-read it.
    exists = os.path.exists(db_path) and not is_lfs_pointer(db_path)
    info = {"db_path": db_path, "exists": exists}
    if not info["exists"]:
        info.update({"age_days": None, "stale": True, "unique_cards": 0})
        return info
    meta = _read_meta(db_path)
    age = _age_days(meta)
    info.update(
        {
            "age_days": age,
            "stale": age is None or age > STALE_AFTER_DAYS,
            "unique_cards": meta.get("unique_cards"),
            "built_at": meta.get("built_at"),
            "bulk_updated_at": meta.get("bulk_updated_at"),
            "bulk_id": meta.get("bulk_id"),
        }
    )
    if check_remote:
        try:
            latest = api.bulk_metadata("default_cards")
            info["remote_newer"] = latest.get("id") != meta.get("bulk_id")
            info["remote_updated_at"] = latest.get("updated_at")
        except (api.ScryfallUnreachable, Exception):  # noqa: BLE001 - best-effort
            info["remote_newer"] = None
    return info


def ensure_database(db_path=None, progress=None, build_if_missing=True):
    """Make sure a usable database exists, building it if missing (and allowed).

    Returns a dict: {available: bool, built: bool, status: <database_status>, reason}.
    Does NOT auto-refresh a stale-but-present DB — that is a soft, ask-first action the
    caller handles (see refresh()). Build failures (no network / no FS) degrade to
    available=False so the caller can fall back to the live API.
    """
    db_path = db_path or default_db_path()
    st = database_status(db_path)
    if st["exists"]:
        return {"available": True, "built": False, "status": st, "reason": "present"}
    if not build_if_missing:
        return {"available": False, "built": False, "status": st, "reason": "missing"}
    try:
        build_database(dest=db_path, progress=progress)
    except api.ScryfallUnreachable as e:
        return {"available": False, "built": False, "status": st,
                "reason": f"unreachable: {e}"}
    except OSError as e:
        return {"available": False, "built": False, "status": st,
                "reason": f"cannot write database: {e}"}
    return {"available": True, "built": True, "status": database_status(db_path),
            "reason": "built"}


def refresh(db_path=None, progress=None):
    """Force a rebuild from the latest Scryfall bulk file. Returns the new meta."""
    return build_database(dest=db_path or default_db_path(), progress=progress, force=True)
