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
python scripts/sync.py --status            # where the workspace is + repo state
python scripts/sync.py --pull              # before a build: fetch the latest decks/collection
python scripts/sync.py --push -m "Add Atraxa deck"   # after a build: commit + push
python scripts/sync.py --init <repo-url> [--path DIR]  # first-time clone + scaffold
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

## First-time setup (when syncing isn't configured yet)

Run this when the user asks to "store my decks somewhere" / "use them on my other machine", or
when `--status` shows the workspace isn't a git repo. Walk them through it:

1. **Ask for their private data repo.** They need a repo dedicated to their MTG data (decks +
   collection), separate from this open-source skills repo. Ask:
   - *"Do you already have a private repo for your MTG data, or should we make one?"*
   - **GitHub free accounts get unlimited private repos**, so this costs nothing. If they don't
     have one: have them create an empty private repo (e.g. on github.com, name it `mtg-data`),
     or, if the `gh` CLI is available and authenticated, offer to create it:
     `gh repo create mtg-data --private`.
   - Get the clone URL (SSH `git@github.com:<user>/mtg-data.git`, or HTTPS).
2. **Clone + scaffold:** `python scripts/sync.py --init <repo-url>` (defaults to `~/mtg-data`; pass
   `--path` to clone elsewhere). This clones the repo and ensures it has `decks/`, `collection/`,
   and a `.gitignore` that excludes the rebuildable `database/`.
3. **Point the skills at it with `MTG_HOME`.** The script prints the exact line. Make it permanent:
   - macOS/Linux: `echo 'export MTG_HOME="$HOME/mtg-data"' >> ~/.zshrc && source ~/.zshrc`
   - Windows: `setx MTG_HOME "%USERPROFILE%\mtg-data"` (open a new terminal afterwards).
     Also run once: `git config --global core.autocrlf input` (keeps deck-file line endings clean
     across OSes). The clone can live anywhere on Windows — `MTG_HOME` names the path, so the
     different filesystem doesn't matter.
4. **Confirm:** `python scripts/sync.py --status` should show `from $MTG_HOME`, the remote, and a
   branch. Then build the card database once (the **mtg-db** skill, or just build a deck — it
   auto-builds), and you're ready.
5. **Repeat on each machine:** clone the same repo, set `MTG_HOME`, build the database once. The
   decks/collection then sync via pull/push; the database is rebuilt locally per machine.

If the user would rather not use git at all, that's fine — leave `MTG_HOME` unset (or pointed at a
plain folder). Everything still works locally; it just won't sync. Don't push git on them.

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
