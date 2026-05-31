"""Shared CLI preamble for the deck skills' search wrappers.

`ensure_ready()` implements the agreed startup behaviour once, for all skills:
- **Missing database** -> notify and build it (one-time setup), don't ask.
- **Present but stale** (older than STALE_AFTER_DAYS) -> print a non-blocking note that
  data may be out of date (the *asking* whether to refresh is the agent's job, per each
  SKILL.md). A usable DB still exists, so we proceed.
- **Build impossible** (no network / no writable FS) -> note that we'll use the live API.

Returns the ensure_database() result so the wrapper can decide messaging, but search()
and named() already fall back to the live API on their own when the DB is absent.
"""

import sys

from .status import database_status, ensure_database, STALE_AFTER_DAYS


def _progress(stage, info, stream):
    if stage == "downloading":
        print(f"  downloading Scryfall bulk data ({info})…", file=stream, flush=True)
    elif stage == "download_pct" and info in (25, 50, 75, 100):
        print(f"  …{info}%", file=stream, flush=True)
    elif stage == "building":
        print("  building local SQLite database…", file=stream, flush=True)
    elif stage == "collapsing":
        print(f"  collapsing {info} printings to unique cards…", file=stream, flush=True)


def ensure_ready(db_path=None, stream=sys.stderr, build_if_missing=True):
    st = database_status(db_path)
    if not st["exists"] and build_if_missing:
        print("Setting up the local card database — one-time ~540 MB download, ~30 s "
              "(skills read this instead of calling Scryfall each time)…",
              file=stream, flush=True)
    res = ensure_database(
        db_path, progress=lambda s, i: _progress(s, i, stream),
        build_if_missing=build_if_missing,
    )
    if not res["available"]:
        print(f"Note: no local card database available ({res['reason']}). "
              "Falling back to the live Scryfall API (slower, rate-limit-exposed).",
              file=stream, flush=True)
        return res
    final = res["status"]
    if final.get("stale") and not res["built"]:
        age = final.get("age_days")
        age_s = "of unknown age" if age is None else f"{age:.0f} days old"
        print(f"Note: local card data is {age_s} (older than {STALE_AFTER_DAYS} days). "
              "Prices/sets may have moved — refresh with the mtg-scryfall-database skill "
              "if you need current data.", file=stream, flush=True)
    return res
