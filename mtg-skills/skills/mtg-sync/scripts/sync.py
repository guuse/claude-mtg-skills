#!/usr/bin/env python3
"""sync.py — keep the MTG workspace (decks + collection) in a private git repo.

Thin CLI over `mtg_scryfall.sync`. Operates on the resolved workspace ($MTG_HOME, else
the nearest .mtg/). The card database lives there too but is git-ignored — only decks and
collection sync. See the repo's SYNCING.md for the full cross-machine setup.

Modes:
  Status:  python sync.py --status [--json]
  Pull:    python sync.py --pull               # before a build: get the latest decks/collection
  Push:    python sync.py --push [-m "msg"]     # after a build: commit + push new decks
  Init:    python sync.py --init <repo-url> [--path DIR]   # clone the private data repo + scaffold

All operations are best-effort: if git isn't installed, the workspace isn't a repo, or the
network is down, the command says so and exits non-zero — the calling skill should report the
note and carry on with the local workspace. (Init failure is the one case worth stopping on.)
"""

import argparse
import json
import os
import sys

# Find the shared mtg_scryfall library (same bootstrap as the deck skills' scripts).
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
    from mtg_scryfall import sync, workspace_paths
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)


def _print_status(as_json):
    st = sync.status()
    if as_json:
        print(json.dumps(st, indent=2))
        return 0
    print(f"workspace : {st['home']}  ({'from $MTG_HOME' if st['from_env'] else 'default .mtg/'})")
    if not st["git"]:
        print("git       : not installed — syncing unavailable; decks stay local.")
        return 0
    if not st["is_repo"]:
        print("repo      : workspace is NOT a git repo.")
        print("            → run:  python sync.py --init <your-private-repo-url>")
        print("            (or set $MTG_HOME to an already-cloned data repo; see SYNCING.md)")
        return 0
    print(f"remote    : {st['remote'] or '(none)'}")
    print(f"branch    : {st['branch'] or '(unknown)'}")
    ab = []
    if st["ahead"]:
        ab.append(f"{st['ahead']} to push")
    if st["behind"]:
        ab.append(f"{st['behind']} to pull")
    print(f"state     : {'dirty (uncommitted changes)' if st['dirty'] else 'clean'}"
          + (f"; {', '.join(ab)}" if ab else ""))
    return 0


def _print_result(verb, res):
    """Render a pull/push result; return a shell exit code (0 ok/skipped, 1 failed)."""
    if res.get("skipped"):
        print(f"{verb}: skipped — {res['reason']}")
        print("      (decks are safe locally; set up syncing when you can — see SYNCING.md)")
        return 1
    if res.get("ok"):
        extra = ""
        if verb == "push":
            extra = " (committed + pushed)" if res.get("committed") else " (already up to date)"
        msg = res.get("message") or "done"
        print(f"{verb}: ok{extra} — {msg}")
        return 0
    print(f"{verb}: FAILED — {res.get('reason')}: {res.get('message')}", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description="Sync the MTG workspace (decks + collection) via git.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--status", action="store_true", help="Show the workspace's sync state.")
    g.add_argument("--pull", action="store_true", help="Pull latest decks/collection (before a build).")
    g.add_argument("--push", action="store_true", help="Commit + push new decks/collection (after a build).")
    g.add_argument("--init", metavar="REPO_URL", help="Clone the private data repo and scaffold the layout.")
    ap.add_argument("-m", "--message", help="Commit message for --push.")
    ap.add_argument("--path", help="With --init: where to clone (default ~/mtg-data).")
    ap.add_argument("--json", action="store_true", help="Machine-readable output (with --status).")
    args = ap.parse_args()

    if args.status:
        return _print_status(args.json)
    if args.pull:
        return _print_result("pull", sync.pull())
    if args.push:
        return _print_result("push", sync.push(args.message))
    if args.init:
        res = sync.init(args.init, args.path)
        if not res["ok"]:
            print(f"init: FAILED — {res['reason']}", file=sys.stderr)
            return 1
        where = res["path"]
        verb = "cloned" if res.get("cloned") else "ready"
        print(f"init: {verb} at {where}")
        wp = workspace_paths()
        if os.path.abspath(wp["paths"]["home"]) != os.path.abspath(where):
            print("\nNow point the skills at it by setting MTG_HOME (make it permanent in your shell):")
            print(f'  macOS/Linux : echo \'export MTG_HOME="{where}"\' >> ~/.zshrc && source ~/.zshrc')
            print(f'  Windows     : setx MTG_HOME "{where}"   (then open a new terminal)')
        print("\nNext: build the card database once (mtg-db skill), then build a deck.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
