---
name: mtg-db
description: >-
  Build or refresh the local Scryfall card database (.mtg/database/cards.sqlite) that the
  MTG deckbuilding skills read from instead of calling the Scryfall API. Use this skill when
  the user wants to set up, build, refresh, or update their local MTG card data, when card
  prices or sets seem out of date, or as the one-time setup step before building or upgrading
  Commander/EDH or MTG Arena Standard decks. The deck skills also invoke this automatically
  when the database is missing or stale. It downloads Scryfall's "Default Cards" bulk file,
  collapses it to one row per unique card (cheapest EUR/USD price, Arena availability,
  rarity, legalities, Game Changer flag, EDHREC rank), and stores it as SQLite for fast,
  mostly-offline querying — sharply cutting Scryfall API calls and rate-limiting.
---

# MTG Scryfall Database

This skill creates and maintains the **local card database** the other MTG skills depend on.
Instead of every deck build hammering `api.scryfall.com`, the skills query a local SQLite file
built once from Scryfall's downloadable **bulk data**. This is faster, works mostly offline, and
keeps us well under Scryfall's rate limits.

**This is the foundation the deckbuilding skills build on.** A Commander or Arena build needs
card data before it can do anything, so the database must exist first. In practice you rarely run
this skill by hand — the deck skills **auto-build the database on demand** when it's missing (see
below). Run this skill directly when you want to set it up ahead of time, force a refresh, or check
how current the data is.

## What it builds

- **`.mtg/database/cards.sqlite`** — one row per unique card (`oracle_id`), carrying oracle text,
  type, mana value, color identity/colors, power/toughness, rarity, keywords, legalities, the
  **Game Changer** flag, **EDHREC rank**, **Arena/paper/MTGO** availability, and the **cheapest**
  EUR/USD price across all printings (Cardmarket via Scryfall for EUR).
- **`.mtg/database/meta.json`** — records the source bulk version and build date (used for the
  staleness check).

Source: Scryfall's **Default Cards** bulk file (the only bulk export carrying per-printing prices
and Arena availability). It's a **~540 MB download** that builds into a **~170 MB** SQLite file in
roughly half a minute. The raw JSON is discarded after the build; only the SQLite + meta remain.

## How to drive it

The work is done by `scripts/build_database.py`, a thin wrapper over the shared `mtg_scryfall`
library in `mtg-skills/lib/` (which the deckbuilding skills also use). Requires code execution with
network access to `api.scryfall.com`.

```
python "${CLAUDE_SKILL_DIR}/scripts/build_database.py"            # build if missing; otherwise print status
python "${CLAUDE_SKILL_DIR}/scripts/build_database.py" --status   # status + whether Scryfall has newer data
python "${CLAUDE_SKILL_DIR}/scripts/build_database.py" --refresh  # force a rebuild from the latest bulk file
python "${CLAUDE_SKILL_DIR}/scripts/build_database.py" --path P   # use an explicit database location (see no-FS case)
python "${CLAUDE_SKILL_DIR}/scripts/build_database.py" --json     # machine-readable output
```

## Sharing the database across machines (optional, via mtg-sync + Git LFS)

By default each machine builds its own copy of `cards.sqlite` — it's a rebuildable cache, so it's
git-ignored and doesn't travel with the synced decks/collection. If the user would rather **share the
exact built database** (e.g. to skip the 540 MB Scryfall download on a second machine, or to keep
prices identical across machines), the **mtg-sync** skill can ship it via **Git LFS**:

- **After you build or `--refresh`** the database, offer to push it by running the **mtg-sync** skill
  with `--push-database` (e.g. `-m "Refresh card data"`). It commits + pushes `cards.sqlite` +
  `meta.json` via LFS (force-added past the `database/` ignore rule). This is best-effort — if the
  workspace isn't a synced repo or `git-lfs` isn't installed, it reports `skipped` and the database
  just stays local.
- **On another machine**, instead of rebuilding, fetch the shared copy by running the **mtg-sync**
  skill with `--pull-database`.

Don't do this automatically on a plain local build — only when the user is using sync (an `mtg-data`
repo) and wants the database shared. The heavy file ships **only** through these dedicated commands,
never on a routine deck `--push`, so normal deck saves stay small.

## When the deck skills run

Each deckbuilding skill checks the database at the **start** of a build and behaves as follows:

- **Missing database → build it, don't ask.** Tell the user it's a one-time setup
  ("setting up the local card database — one-time ~540 MB download, ~30 s"), build it, then carry on
  with their request. This is what makes "the database always exists before any other skill runs"
  true without the user having to sequence anything.
- **Present but stale (older than 30 days) → ask first.** A usable database already exists, so
  re-downloading is optional: tell the user how old it is and that prices may have moved, and
  **ask** whether to refresh before continuing. Proceed either way per their answer.
- **Present and fresh → use it silently.**

The 30-day window is the default staleness threshold. For the Arena skills (which use only rarity,
Arena availability, and Standard legality — none of which move between set releases) staleness
matters little; for Commander, prices drift, so a refresh is worth offering past the window.

## When there's no writable filesystem

Two cases, handled differently:

1. **A filesystem exists, but there's no clear working directory** (e.g. an interactive chat with no
   project folder). If **`$MTG_HOME`** is set the database builds there automatically (under
   `$MTG_HOME/database/`) — nothing to ask. Otherwise **ask the user where the database should live**,
   then build there by passing `--path <their-path>/database/cards.sqlite`. Use that location for the
   rest of the session. (Setting `$MTG_HOME` is the durable fix — see the repo's `SYNCING.md`.)
2. **No filesystem and/or no code execution at all** (a pure-chat agent that can't run Python or
   write files). The database **cannot** be built — pointing it somewhere won't help. Tell the user
   plainly: "I can't build a local card database in this environment, so I'll query Scryfall live —
   slower and rate-limit-exposed; for the full experience, run me where I can execute code and write
   files." The deck skills then fall back to the live Scryfall API (their existing behavior).

Always store the database whenever storage is possible — that's the whole point (reduce Scryfall
API load and avoid rate-limiting us). Case 2 is the unavoidable exception, not a reason to skip it.

## What still calls Scryfall live

The local database serves everything the bulk data contains. The deliberate exception is
**`function:` / `otag:` (Scryfall Tagger) tags** — curated tags like `function:ramp`,
`function:removal`, `function:card-advantage` — which exist in no bulk file. Any query using those,
or any operator the local engine can't translate, is routed **whole** to the live Scryfall API by
the shared library, so results are never silently wrong. This is by design (see
`docs/adr/0001` in the repo): it removes the overwhelming majority of API calls (every card lookup,
price, identity/type/cost filter) while keeping the genuinely-unavailable Tagger queries accurate.
