---
name: mtg-export
description: >-
  Export the user's MTG Arena (MTGA) collection straight from the running game into their
  MTG workspace as collection/MTGA-export-<date>.csv, then sync it. Use this skill when the
  user wants to export, dump, capture, back up, or refresh their MTG Arena collection /
  owned cards, or asks "what do I own in Arena", or wants their collection available to the
  deckbuilding skills (mtg-std-build / mtg-std-upgrade prefer cards you already own). It is a
  one-shot: it reads the owned-card list out of the live MTGA process memory (no anchor
  cards, no manual steps), names the cards from the local Scryfall database built by the
  mtg-db skill (never downloading its own card data), writes a Moxfield-format CSV into the
  collection folder, and pushes it via mtg-sync. Works on Windows (via pymem) and macOS (via
  Mach APIs; needs sudo). Requires MTG Arena installed and running.
---

# MTG Arena Collection Export

This skill captures the user's **owned MTG Arena collection** and drops it into their
[MTG workspace](../mtg-db/SKILL.md) as `collection/MTGA-export-<YYYY-MM-DD>.csv` — the exact
shape the **mtg-std-build** and **mtg-std-upgrade** skills read to prefer cards the user
already owns. It runs in **one shot**, with no anchor cards and no manual data entry: it reads
the collection directly out of the running game's memory and translates the Arena card ids to
names using the **local Scryfall database** (`mtg-db`), so it never downloads or builds its own
card data.

## How it works

MTG Arena keeps the owned collection in memory as a map of **`arena_id` → owned count**. The
bundled scanner (`scripts/export_collection.py`) attaches to the live MTGA process, finds that
map anchor-free (it keeps the largest contiguous block of valid `arena_id → count` entries,
validated against the card database), and writes the result as CSV. Card names/sets come from
the `arena_cards` table in `<workspace>/database/cards.sqlite` (built by **mtg-db**); MTGA's own
bundled card files, if present, are merged in best-effort so cards from a set newer than the
database still resolve.

- **Platforms:** Windows (reads memory via `pymem`) and macOS (via Mach `task_for_pid` — needs
  `sudo`; works for the native Steam app and CrossOver/Wine). Linux is not supported.
- **Dependencies:** `numpy` (both platforms) and `pymem` (Windows only). See
  `scripts/requirements.txt`. These are the one exception to the repo's stdlib-only rule —
  reading another process's memory requires them.

## Prerequisites (tell the user, once)

1. **MTG Arena is installed and running.**
2. In-game, open the **Collection** or **Decks** tab and **scroll through the cards** for ~30s
   so the whole collection is loaded into memory. (If the export comes back partial or empty,
   this is almost always why — scroll and re-run.)
3. The **local Scryfall database exists** with the Arena map. If the database is missing or was
   built before this skill existed, build/refresh it first via **mtg-db** (see below).

## How to drive it (the one-shot)

Two steps — make sure the card data is ready, then run the exporter with `--sync` so the
collection is captured **and** pushed in a single invocation:

1. **Ensure the local Scryfall database exists and carries the Arena-id map** (the
   `arena_cards` table). Do this via the **mtg-db** skill: check its status and, if the
   database is missing or was built before this skill existed, refresh it (a one-time
   ~540 MB download, ~30 s). The deck skills auto-build this database too, so on a machine
   that has already built a deck it's usually present — it just needs a refresh if it predates
   the Arena map.

2. **Export and sync** with the bundled script:

   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/export_collection.py" --sync
   ```

   `--sync` writes the CSV and then pushes the collection through the **mtg-sync** skill — one
   shot, no human input. If the exporter exits with *"No Arena card map in the Scryfall
   database"*, the database predates this skill: refresh it via **mtg-db** and re-run.

On **macOS** the scanner needs root to read game memory, so run it with `sudo`:

```bash
sudo python3 "${CLAUDE_SKILL_DIR}/scripts/export_collection.py" --sync
```

(When installed via the plugin marketplace, `${CLAUDE_SKILL_DIR}` resolves to this skill's
directory. The script locates the shared `mtg_scryfall` library and the sibling **mtg-sync**
script itself, so a manually-copied layout works too as long as the skills sit side by side.)

### Flags

```
--sync               After writing the CSV, push the collection via the mtg-sync skill.
--db PATH            Use an explicit cards.sqlite (default: the resolved workspace database).
--out-dir DIR        Write the CSV somewhere other than <workspace>/collection/.
--process NAME       Override the MTGA process name (default: MTGA.exe / MTGA / mtga).
```

The script prints progress to **stderr** and the single written CSV path to **stdout**. Exit
codes: `0` success · `2` setup/dependency problem (numpy missing, no Arena map in the DB) ·
`3` could not locate the collection (game not running, or cards not loaded — scroll and retry).

## Output

- **`<workspace>/collection/MTGA-export-<YYYY-MM-DD>.csv`** — Moxfield-format CSV with the
  columns `Count, Name, Edition, Condition, Language, Foil, Tag` (Condition `Near Mint`,
  Language `English`). One row per (name, set), counts summed. This is exactly what the Arena
  deckbuilding skills look for under `collection/`.

The workspace is resolved the usual way: **`$MTG_HOME` → nearest `.mtg/` → `./.mtg/`** (see the
mtg-db and mtg-sync skills). Point `MTG_HOME` at a synced `mtg-data` repo and the export lands
there directly.

## Sync (run after every export)

With `--sync`, the exporter invokes the **mtg-sync** skill to push once the CSV is written,
committing and pushing the collection so it's available on the user's other machines
and to the deckbuilding skills. This is **best-effort**, exactly like the deck skills' push step:
if the workspace isn't a git repo, `git` isn't installed, or the network is down, it reports that
in one line and the CSV still sits in the local workspace to be pushed later — the export itself
still succeeds. If you'd rather drive sync yourself (e.g. with a custom commit message), skip
`--sync` and invoke the **mtg-sync** skill to push the collection afterwards.

## Troubleshooting

- **"Collection not found" / partial export** → MTGA wasn't fully loaded. Open the
  Collection/Decks tab, scroll through the whole collection, then re-run.
- **macOS "Cannot access game memory"** → re-run with `sudo`.
- **Windows permission error** → run the terminal as Administrator.
- **"No Arena card map in the Scryfall database"** → the database predates this skill (or is
  missing). Run `mtg-db` with `--refresh` to rebuild it with the `arena_cards` table.
- **macOS process not found** → ensure MTGA is open (Steam or CrossOver); the scanner looks for
  `MTGA`, `MTGA.exe`, and `mtga`. Override with `--process` if needed.
- **Unsupported platform** → only Windows and macOS can be scanned; Linux is not supported.
