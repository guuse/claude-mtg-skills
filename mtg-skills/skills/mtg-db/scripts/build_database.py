#!/usr/bin/env python3
"""build_database.py — build / refresh / inspect the local Scryfall card database.

Thin CLI over the shared `mtg_scryfall` library (mtg-skills/lib/). The library does the
real work: download Scryfall's "Default Cards" bulk file (~540 MB), collapse it to one
row per unique card, and store it as `.mtg/database/cards.sqlite` (~170 MB). Skills read
that database instead of calling the Scryfall API.

Usage:
  python scripts/build_database.py                 # build if missing; else print status
  python scripts/build_database.py --status        # status only (+ remote freshness)
  python scripts/build_database.py --refresh       # force a rebuild from latest bulk
  python scripts/build_database.py --path PATH      # use an explicit database location
  python scripts/build_database.py --json           # machine-readable output

`--path` covers the "no clear working directory" case: when running in an interactive
chat with no project folder, ask the user where `.mtg/database/` should live and pass
that location here. If code execution / a writable filesystem isn't available at all,
the database can't be built — the deck skills then fall back to the live Scryfall API.
"""

import argparse
import json
import os
import sys

# Locate the shared library: plugin layout puts it at mtg-skills/lib (../../../lib);
# the other candidates let a manually-copied skill find a `lib/` dropped beside it.
_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = None
for _rel in ("../../../lib", "../../lib", "../lib", "lib", "."):
    _cand = os.path.normpath(os.path.join(_HERE, _rel))
    if os.path.isdir(os.path.join(_cand, "mtg_scryfall")):
        _LIB = _cand
        break
if _LIB and _LIB not in sys.path:
    sys.path.insert(0, _LIB)

try:
    from mtg_scryfall import (
        build_database, database_status, default_db_path, ensure_database,
    )
    from mtg_scryfall import api
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)


def _fmt_status(st):
    if not st["exists"]:
        return "No local card database found."
    age = st.get("age_days")
    age_s = "unknown age" if age is None else f"{age:.0f} day(s) old"
    line = (f"Database: {st['db_path']}\n"
            f"  {st.get('unique_cards')} unique cards · built {st.get('built_at')} "
            f"({age_s}{', STALE' if st['stale'] else ''})")
    if st.get("remote_newer") is True:
        line += "\n  A newer card data set is available from Scryfall."
    elif st.get("remote_newer") is False:
        line += "\n  Card data is up to date with Scryfall's latest bulk."
    return line


def _progress(stage, info):
    if stage == "downloading":
        print(f"  downloading Scryfall bulk data ({info})…", file=sys.stderr, flush=True)
    elif stage == "download_pct" and info in (25, 50, 75, 100):
        print(f"  …{info}%", file=sys.stderr, flush=True)
    elif stage == "building":
        print("  building SQLite database…", file=sys.stderr, flush=True)
    elif stage == "collapsing":
        print(f"  collapsing {info} printings to unique cards…", file=sys.stderr, flush=True)


def main():
    ap = argparse.ArgumentParser(description="Build/refresh the local Scryfall card database.")
    ap.add_argument("--path", help="Explicit database path (default: ./.mtg/database/cards.sqlite).")
    ap.add_argument("--status", action="store_true", help="Show status only; don't build.")
    ap.add_argument("--refresh", action="store_true", help="Force a rebuild from the latest bulk file.")
    ap.add_argument("--json", action="store_true", help="Emit JSON.")
    args = ap.parse_args()

    db_path = args.path or default_db_path()

    if args.status:
        st = database_status(db_path, check_remote=True)
        print(json.dumps(st, indent=2) if args.json else _fmt_status(st))
        return

    if args.refresh or not os.path.exists(db_path):
        if not os.path.exists(db_path) and not args.refresh:
            print("No local card database found — building it now (one-time setup).",
                  file=sys.stderr)
        try:
            meta = build_database(dest=db_path, progress=_progress, force=args.refresh)
        except api.ScryfallUnreachable as e:
            print(f"ERROR: could not reach api.scryfall.com ({e}). "
                  "Without network access the database can't be built; skills will fall "
                  "back to the live Scryfall API via web tools.", file=sys.stderr)
            sys.exit(2)
        except OSError as e:
            print(f"ERROR: could not write the database ({e}). If there's no writable "
                  "working directory, re-run with --path pointing somewhere writable.",
                  file=sys.stderr)
            sys.exit(2)
        if args.json:
            print(json.dumps(meta, indent=2))
        else:
            print(f"Built {meta['unique_cards']} unique cards -> {db_path}")
        return

    # DB already present and no refresh requested: report status.
    st = database_status(db_path, check_remote=True)
    print(json.dumps(st, indent=2) if args.json else _fmt_status(st))


if __name__ == "__main__":
    main()
