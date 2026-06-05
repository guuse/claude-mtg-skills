---
name: mtg-sync
description: >-
  Keep the user's MTG decks and collection in a private git repo so the same data follows
  them across machines and mobile. Use this skill to set up syncing the first time (ask for
  the user's private "mtg-data" repo and clone it), to pull the latest decks/collection
  before building or upgrading a deck, and to push newly built decks afterwards. The deck
  skills (mtg-edh-build, mtg-edh-upgrade, mtg-std-build, mtg-std-upgrade) invoke this
  automatically before and after they run — pull before, push after — the same way they rely
  on the mtg-db skill for card data. Syncing is best-effort: if git, a repo, or the network
  isn't available it reports that and the build proceeds with the local workspace. Triggers on
  "sync my decks", "store my decks somewhere", "set up my mtg-data repo", "use my decks on my
  other PC / phone", or any cross-machine deck/collection persistence request.
---

# MTG Sync

This skill keeps the **decks** and **collection** in the [MTG workspace](../mtg-db/SKILL.md)
in a **private git repo**, so they're the same on the user's Mac, their other PC, and their
phone. It is the companion to **mtg-db**: mtg-db rebuilds the (git-ignored, disposable) card
database on each machine, while mtg-sync moves the irreplaceable, human-made data — deck guides,
import lists, collection exports — between machines via git.

**The workspace is resolved by `$MTG_HOME` → nearest `.mtg/` → `./.mtg/`** (see the mtg-db skill).
Syncing works when that workspace is a git repo — normally a clone of the user's private
`mtg-data` repo, with `$MTG_HOME` pointing at it. The full rationale and setup live in the repo's
**[SYNCING.md](../../../SYNCING.md)**.

All operations go through the bundled helper:

```bash
python scripts/sync.py --bootstrap         # ONE-COMMAND first-time setup (create repo, scaffold, migrate, push)
python scripts/sync.py --status            # where the workspace is + repo state
python scripts/sync.py --pull              # before a build: fetch the latest decks/collection
python scripts/sync.py --push -m "Add Atraxa deck"   # after a build: commit + push
python scripts/sync.py --init <repo-url> [--path DIR]  # clone an existing repo + scaffold
```

## The before/after contract (how the deck skills use this)

The four deckbuilding skills call this skill at the edges of their run — **exactly like they
auto-build the database with mtg-db**:

1. **Before** reading decks/collection or building anything → run `python scripts/sync.py --pull`.
   This brings down decks/collection built on another machine first, so you never fork history.
2. **After** writing the deck's files (`deck.md` + import/arena list) → run
   `python scripts/sync.py --push -m "<short description of the deck>"`. This commits and pushes
   so the new deck is available everywhere.

**Best-effort, never blocking.** If `--pull`/`--push` reports `skipped` (no git, or the workspace
isn't a repo) or `FAILED` (e.g. offline), **say so in one line and continue** — the deck is still
saved in the local workspace and can be pushed later. Do **not** ask the user to fix syncing
mid-build; just note it and move on. Only **--init** failures are worth pausing on, because the
user explicitly asked to set syncing up.

## First-time setup — one command

When the user asks to "store my decks somewhere" / "use them on my other machine", or when
`--status` shows the workspace isn't a git repo, run **`--bootstrap`**. It does the whole setup in
one shot and is safe to re-run (idempotent):

```bash
python scripts/sync.py --bootstrap
```

That single command:
1. **Creates the repo** (default `mtg-data`, **private**) via the `gh` CLI — GitHub free accounts get
   unlimited private repos, so this is free. If the repo already exists it clones it; if `gh` isn't
   available, pass an existing clone URL instead: `--bootstrap --repo <url>`.
2. **Scaffolds it fully** — `decks/`, `collection/`, a `.gitignore` that excludes the rebuildable
   `database/`, a `README.md`, and **`.claude/settings.json` that auto-installs this plugin** on any
   machine that opens the repo (so the skills come along for free).
3. **Migrates existing data** — copies any decks/collection from the current workspace (e.g. a local
   `.mtg/`) into the repo, skipping the database and any nested tool checkouts.
4. **Commits and pushes.**

Useful flags: `--repo <name|owner/name|url>`, `--dest <path>` (default `~/<name>`), `--public`,
`--from <path>` (migrate from a specific workspace), `--no-push`.

**After it runs, do two things:**
- **Set `MTG_HOME`** to the path it prints (it shows the exact line). macOS/Linux:
  `echo 'export MTG_HOME="$HOME/mtg-data"' >> ~/.zshrc && source ~/.zshrc`; Windows:
  `setx MTG_HOME "%USERPROFILE%\mtg-data"` (then a new terminal; also run once
  `git config --global core.autocrlf input`). Offer to append the export line for them.
- **Build a deck** (the card database auto-builds on first use). Done.

**On each additional machine:** just `--bootstrap` again (it clones the existing repo and sets the
same layout) and set `MTG_HOME`. The skills auto-install from the marketplace when the repo is
opened; the database rebuilds locally per machine.

If the user would rather not use git at all, that's fine — leave `MTG_HOME` unset (or pointed at a
plain folder). Everything still works locally; it just won't sync. Don't push git on them.

### `--init` (clone an existing repo only)

If the user already has a data repo and just wants to clone + scaffold it (no create/migrate/push),
`python scripts/sync.py --init <repo-url> [--path DIR]` does that narrower job.

## On mobile

Cloning the `mtg-data` repo on a phone (e.g. **Working Copy** on iOS, or reading it in the GitHub
app) shows every `deck.md` guide as formatted Markdown. Building decks on a phone isn't expected —
viewing is. For the native MTG experience, mirror a deck into **Moxfield** by hand (paste the import
list, drop `deck.md` into the deck's description/primer). Git stays the source of truth; Moxfield is
just the pretty view. See [SYNCING.md](../../../SYNCING.md).

## What syncs (and what doesn't)

- **Synced (committed):** `decks/<slug>/` (each `deck.md` guide + `import.txt`/`arena.txt`) and
  `collection/` (Moxfield / Arena / Archidekt exports).
- **Not synced (git-ignored):** `database/` — the ~170 MB `cards.sqlite` is a rebuildable Scryfall
  cache. Each machine rebuilds it locally in ~30 s (mtg-db); there's no reason to ship it.

## Troubleshooting

- **`--status` says "not a git repo"** → run first-time setup, or set `$MTG_HOME` to a cloned repo.
- **`pull: FAILED` / `push: FAILED`** → usually offline or an auth/remote issue. Decks are safe
  locally; retry `--push` later (it will commit + push then). For HTTPS auth prompts, an SSH remote
  or a cached credential helper avoids interactive prompts in non-interactive runs.
- **Merge/rebase conflict on pull** → rare, since each deck lives in its own folder. If it happens,
  it's an ordinary git conflict in the `mtg-data` repo; resolve it there.
