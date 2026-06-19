---
name: mtg-std-upgrade
description: >-
  Improve an existing 60-card Standard deck for MTG Arena (MTGA) that the user pastes in. Use this skill
  whenever the user already has a Standard/Arena decklist and wants to upgrade, tune, optimize, or tech it
  against the current ladder meta — rather than build a new deck from scratch. Triggers on phrases like
  "upgrade my Standard deck", "improve this Arena deck", "here's my list, what should I swap", "tune my
  mono-red for the meta", "what cards should I craft to improve this", or any request that pastes or
  references an existing 60-card Arena list and asks for improvements. The user pastes their current list
  inline. The skill diagnoses the deck (curve, mana base, consistency, meta matchups), then recommends the
  highest-impact swaps — built from cards the user already owns first (via their Arena collection export),
  and costed in Arena wildcards against a budget tier that, because this is an upgrade, is usually much
  lower than building from scratch. Verifies legality and rarity via Scryfall, and reads the current
  Standard meta and **real, comparable decklists from mtgtop8.com** — so it tunes the deck against the live
  field and the *proven version of its archetype* (which staples it's missing, which counts are off), not
  from memory. For 60-card Standard, NOT 100-card Commander/EDH.
---

# MTG Arena Standard Deck Upgrader

This skill takes a Standard deck the user **already has on Arena** and makes it better and more competitive
— without rebuilding it. It uses the same method as the Standard deckbuilder (a deck must be legal now,
beat the current ladder meta, and be affordable in wildcards), but applies it as a **diagnosis-and-swap**
pass: find the weakest links and the worst matchups, then spend a (usually small) number of wildcards on
the changes that help the most.

Two things stay first-class, exactly as in the builder:
- **Rarity is shown on every card** — in Arena you craft with wildcards of matching rarity, so rarity *is*
  the cost. Label each card C / U / R / M.
- **Build from what you already own.** An upgrade is mostly about spending a handful of wildcards well, so
  the user's collection matters even more here than in a fresh build.

**Work interactively — this is a conversation, not a one-shot transform.** The user knows how their deck
actually plays and which matchups they keep losing; you know the meta and the card pool. Combine them: ask
what's wrong, react to what they tell you, propose swaps in digestible batches, and refine on their
feedback. Do **not** dump a finished 60 and call it done. Talk through your reasoning, surface options, and
only write the final files once the user has agreed to the changes. Default to asking rather than assuming.

## Start here: paste your decklist

The user provides their **current decklist inline** in their prompt (pasted text — ideally the Arena export
format with a `Deck` header and optional `Sideboard`, but a plain `<count> <Card Name>` list is fine). If
they give a **Moxfield/Archidekt link** instead, run `scripts/import_deck.py <url>` to pull it via the site
JSON API (it falls back to asking for a paste if the deck is private/unreachable; never invents a list).
Parse it: confirm it's **60** maindeck (+ up to 15 sideboard), identify the **archetype/centerpiece** and
colors, label each card's **rarity** via Scryfall, and verify every card is still `legal:standard` and on
Arena (flag anything rotated out or banned — that's often the first thing to fix).

If the list is malformed or not 60, say what you found and confirm with the user before proceeding.

## Ask what's wrong and what they want improved

Before you diagnose anything yourself, **ask the user what they think is wrong with the deck and what they
want it to do better.** They've played it on the ladder; that's information the list can't give you. Ask in
plain language (a few questions, not a wall) — for example:

- **What does it struggle with?** Mana screw/flood, slow or clunky draws, dead cards in hand, running out of
  gas, no way to close, folding to removal or sweepers.
- **Which matchups are you losing?** Be specific — "I get run over by mono-red", "control grinds me out",
  "I lose to the go-wide deck." This is what the meta-teching should target.
- **What do you want it to do better, and what's off-limits?** Faster/grindier/more resilient; cards you
  love and want to keep; how many wildcards you're willing to spend.

Let their answers steer the upgrade — **their lived experience outranks your own read** when they conflict.
But if your diagnosis surfaces a problem they didn't mention (a rotated card, a shaky mana base), **raise
it and ask** whether to address it rather than silently changing it.

## Load the user's Arena collection

As with the builder, get the user's collection so upgrades favor cards they can play **today** and only
cost wildcards where it matters. The export lives in **`.mtg/collection/`** and can be **`.txt`** (a plain
`<count> Card Name` list), **`.csv`** (name/quantity columns), or **`.json`** (`{name, quantity}` objects
or a `{name: count}` map). **Don't hand-parse it** — run the bundled helper, which finds the file in any of
those formats and normalises it to a clean `<count> Card Name` list:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --collection
```

(Add an explicit path — `--collection <file>` — if it lives elsewhere.) Then:

- **No file found** → ask the user to drop an export into `.mtg/collection/` (any of `.txt`/`.csv`/`.json`),
  and recommend the free exporter **https://github.com/NthPhantom10/MTGA-collection-exporter**. Make clear
  it's strongly recommended — with it, any upgrade card they already own costs **0 wildcards**, which often
  means the best upgrade is free. If they decline, proceed and cost added cards from zero.
- **A collection is found** → the helper prints the total and the format it parsed (relay any `NOTE:` it
  emits — e.g. an Arena-ID-only JSON it can't resolve — and ask for a name-based export). Ask whether it's
  **up to date** and whether to **use it**; offer a re-export if stale. Once confirmed, use the normalised
  list as the inventory.

When a collection is in use, treat it as the inventory: prefer owned upgrades, and count wildcard cost only
for the cards the user doesn't already own.

## Then confirm: budget tier and match type

- **Wildcard budget tier (1–5).** Caps how many wildcards of each rarity the upgrade may require (the full
  table is in `references/wildcard-budget.md`). **Because this is an upgrade, the tier is usually much lower
  than a fresh build** — you're spending a few wildcards, not crafting 60 cards. Suggest **Tier 1–2** for a
  light touch-up and make the spend count: prioritize the cheapest swaps that fix the biggest problems
  first. Count only the copies the user doesn't already own.
- **Match type.** **BO1 ladder** (60, no sideboard) or **BO3** (60 + 15-card sideboard). For BO3, sideboard
  upgrades are part of the job; for BO1, all the meta-teching lives in the maindeck.

## The deliverable

Always produce **two files**, saved in their own folder under `.mtg/decks/std/` in the user's current working
directory: `.mtg/decks/std/<deck-slug>/deck.md` and `.mtg/decks/std/<deck-slug>/arena.txt` (create the folder if
missing; slug = a short kebab-case deck name, with a suffix like `-upgraded` if a folder already exists).
(MTG Arena Standard decks live under `decks/std/`; Commander/EDH decks live under `decks/edh/`.)
See "The `.mtg` workspace" below.

1. **An annotated, upgraded decklist** (`deck.md`) — the full improved 60 (+ sideboard for BO3), cards
   grouped by role (Centerpiece/Payoffs, Creatures, Removal/Interaction, Card Advantage, Other Spells,
   Lands; plus Sideboard). Every line shows count, card name, **rarity (C/U/R/M)**, and a one-line reason.
   Include the mana curve, land count, the **wildcard-cost breakdown** of the *changes* (commons / uncommons
   / rares / mythics the user must craft vs the tier cap, owned cards excluded), the match type, and the
   meta plan. **Open with a "Changes" section** — each change as **— Cut `<card>` → Add `<card>` (rarity;
   reason; "owned" or "craft 1 R")**, grouped by the problem it fixes, plus the **total wildcards to craft
   vs the tier**. Close with a **Deck Rating** section — an overall ★ rating (out of 5) for the deck on the
   current ladder at its tier, plus the per-dimension scorecard, ideally **before → after** so the upgrade's
   impact on the score is visible (see "Step 6 — Rank the upgraded deck").
2. **An Arena import list** (`arena.txt`) — exact MTG Arena import format: a `Deck` header, then
   `<count> <Card Name>` per line; a blank line then `Sideboard` and 15 cards if BO3. Generate it *from* the
   upgraded annotated list so they can't drift.

Use the `present_files` tool to share both — but **only at the end**, once the user has agreed to the
changes through the interactive method below. The files are the record of a conversation, not its opening
move.

## The `.mtg` workspace

All of this skill's file I/O lives in one **workspace** directory holding three subfolders —
`database/`, `decks/`, and `collection/`. It is resolved in this order:

1. **`$MTG_HOME`**, if that environment variable is set — the user's portable data location (e.g. a
   private `mtg-data` git repo they clone on each machine so decks + collection follow them
   everywhere; see the repo's `SYNCING.md`). Use it even if some subfolders don't exist yet — create them.
2. Otherwise the nearest **`.mtg/`** at or above the current working directory (conventionally
   git-ignored: built output and personal data, not source).

To see the resolved locations any time, run **`python scripts/scryfall_search.py --paths`** — it prints
the `decks/`, `collection/`, and `database/` paths as JSON (honouring `$MTG_HOME`) and creates nothing.
The `.mtg/…` paths written elsewhere in this skill are shorthand for "inside the resolved workspace."

**If `$MTG_HOME` is unset and there's no clear working directory to write to** — e.g. an interactive chat
with no project folder — **ask the user where the workspace should live** (prompt for a path, or suggest
they set `$MTG_HOME`) before reading or writing anything, and use that location for the rest of the session.

The subdirectories:

- **`.mtg/decks/`** — where upgraded decks are written, **split by format**: MTG Arena Standard under
  `.mtg/decks/std/` and Commander/EDH under `.mtg/decks/edh/`. **Each deck gets its own subfolder** —
  for this skill, `.mtg/decks/std/<deck-slug>/`, holding `deck.md` and `arena.txt`. Same decks folder
  the other skills use.
- **`.mtg/collection/`** — the user's Arena collection (owned cards) as a `.txt`, `.csv`, or `.json`
  export, the inventory that makes owned upgrades free. Loaded via the bundled `--collection` helper (it
  accepts any of those formats). See "Load the user's Arena collection" above.

(The pasted decklist is taken from the prompt, not a file.)

### Keeping decks in sync across machines (mtg-sync)

Decks live in the user's `mtg-data` git repo, and the user wants **every upgrade to pull at the start
and push at the end** — the same way card data comes from mtg-db. **Don't try to judge whether
syncing is set up before acting — always run the sync commands and let the helper tell you.**
`sync.py` returns `skipped` when the workspace isn't a git repo, so an unconditional call is safe
everywhere; guessing whether to run it is exactly what makes pushing flaky.

- **At the start**, before loading the collection or writing anything, invoke **mtg-sync** to pull
  (`--pull`), bringing down any decks built on another machine first.
- **As the final action of the upgrade** (see **Final step — always commit & push** at the end of
  this skill), invoke **mtg-sync** to push (`--push -m "<archetype>"`), so the upgraded deck lands on
  the repo's main branch and is available everywhere. This push runs **every time**, not only when you
  think sync is configured.

**Only the *result* is best-effort.** If the push reports `skipped` (syncing isn't set up) or
`FAILED` (e.g. offline), note it in one line and continue — the deck is saved locally and can be
pushed later. Never skip the *attempt*. To set syncing up the first time, use the **mtg-sync** skill
(`--bootstrap`).

## The method (diagnose, then upgrade)

Full reasoning is in `references/methodology.md`; the **synergy-scoring loop** for choosing payoff/synergy
adds (read → extract → map to Scryfall tags → intersect → score, ≥2–3 points of contact) is in
`references/synergy.md`; the Scryfall recipes are in `references/scryfall-syntax.md`; the tier/wildcard logic
is in `references/wildcard-budget.md`. Work in this order:

### Step 1 — Diagnose the current list, then talk it through with the user
Read the deck for the things that lose games: **rotated/illegal cards**, an inconsistent or wrong-speed
**mana base** (too few/many lands, taplands in an aggro deck, missing fixing), a **clunky curve**, **weak
or redundant** cards (win-more, off-plan filler), and **thin answers**. Note the biggest problems.

Then **share a short, readable diagnosis** and reconcile it with what the user told you in "Ask what's
wrong": where do their complaints and your read agree, and where does your read surface something they
didn't raise? **Agree on the top 2–3 priorities together before proposing any cards.**

### Step 2 — Read the meta, and compare the deck to its proven version
Pull the live field and **real decklists** from mtgtop8 — it's the one bot-fetchable source (untapped.gg /
mtggoldfish / mtgdecks / aetherhub all Cloudflare-block automated fetches and must NOT be scraped):

```
python "${CLAUDE_SKILL_DIR}/scripts/mtgtop8_fetch.py" --meta                       # the current top decks
python "${CLAUDE_SKILL_DIR}/scripts/mtgtop8_fetch.py" --archetype <id> --limit 3   # then --deck <id>
```

Two jobs here, both high-signal for an upgrade:
1. **Identify the field** — the top 2–3 decks the user must beat, so the teching targets real matchups.
2. **Diff the deck against the proven version of its own archetype.** Pull 2–3 current lists for the user's
   archetype and compare: which **staples is their list missing**, which **counts are off** (a 2-of that the
   pros run as a 4-of), which **flex/pet cards are underperforming** versus what proven lists play. This
   "you're 3 cards off the stock list" read is often the single biggest, cheapest upgrade.

If mtgtop8 is unreachable, fall back to your own meta knowledge **flagged unverified** and ask the user to
confirm the field, which matchups they're losing, and to paste a meta snapshot or netdeck (a Moxfield/
Archidekt link pulls via `scripts/import_deck.py <url>`). Never invent a metagame percentage or decklist.
The upgrade should improve the worst real matchups and close the gap to the proven list, not add power in a
vacuum. See `references/data-sources.md`.

### Step 3 — Rank upgrades by impact per wildcard, owned-first
For each problem, gather candidate fixes from the **proven mtgtop8 lists for the archetype** (Step 2) and
Scryfall (`references/scryfall-syntax.md`) — the stock list is usually the best menu of fixes.
**Scan the collection first** — an owned card that fixes the problem is the best upgrade because it costs
nothing. Reach for un-owned cards when they're clearly better and worth a wildcard. Favor cheaper-by-rarity
cards that do most of the job (a common/uncommon answer over a premium rare when close).

When the add is a **payoff/synergy** card (not a structural answer or mana fix), run the synergy-scoring loop
from `references/synergy.md`: map the deck's centerpiece axes to Scryfall handles (`function:`/`otag:` tags,
`o:"…"`, `t:…`, `keyword:…`), intersect, and prefer cards giving a **2-for-1 with the plan and 2–3 points of
contact** with the rest of the deck. Structural fixes (lands, removal, sweepers, meta-tech) are exempt from
the rule, but prefer the version that also synergizes.

### Step 4 — Choose the swaps and fit the tier
For every add, name the **cut** (the weakest card in the same or a lower-priority role). Keep the deck at
exactly **60** (+15 sideboard for BO3), max 4 of any non-basic card. Compute the **wildcard cost of the
changes**, counting only un-owned copies, and keep it within the tier — if it's over, downgrade the most
expensive crafts to an owned card or a cheaper role-equivalent first, or trim copies. Match sweepers and
answers to the user's own board (don't add a wrath that kills your own go-wide plan).

### Step 5 — Propose, discuss, and iterate (don't write files yet)
**Present the proposed swaps to the user for reaction before finalizing** — ideally in small batches by
priority (e.g. "first, the mana base", then "the aggro matchup"), each as **Cut → Add, rarity, why,
owned/craft cost**, with the running wildcard tally. Invite them to veto, ask why, suggest their own cards,
or trade power for fewer wildcards, and **adjust accordingly**. Where there's a real choice, offer 2–3
options rather than dictating one. Keep going until the user is happy with the full set of changes. **Only
then** assemble the final 60 (+sideboard), run the quality checks below, rank the deck (Step 6), and write
the two files.

### Step 6 — Rank the upgraded deck (★ rating)
Before writing files, **rate the final list** and embed the result in `deck.md`. Apply the **five-dimension
rubric in `references/rating.md`** — consistency & curve, mana base, synergy/payoff density (via
`references/synergy.md`), meta resilience, and wildcard efficiency — rating the deck *for the current ladder
at its tier and match type*. Use the data you already have: curve and land count, the `--deck --tier`
wildcard tally, the `--colors` audit, and the meta read from Step 2. Write a **Deck Rating** section into
`deck.md` and, because this is an upgrade, show it as **before → after** when you can (rate the pasted
starting list too) so the changes' impact on the score is visible. If the rating shows the upgrade left the
deck's biggest weakness (e.g. still soft to the top aggro deck) unfixed, say so and propose the next swap
rather than shipping it quietly.

## Data sources

Same as the builder. **Scryfall** is the source of truth for Standard legality, rarity, Arena availability,
and oracle text (`legal:standard`, `game:arena`, `r:rare`/`r:mythic`; every card has a `rarity` field).
**Standard / Arena meta + real decklists come from mtgtop8.com** via `scripts/mtgtop8_fetch.py` (`--meta`,
`--archetype <id>`, `--deck <id>`) — the one bot-fetchable source; untapped.gg, mtggoldfish, mtgdecks, and
aetherhub are Cloudflare-protected and **must not be scraped**. Shares lag the very latest ladder a little
(treat as approximate); the lists are real recent results. If mtgtop8 is unreachable, fall back to model
meta knowledge (flagged unverified) and let the user paste a snapshot or a netdeck link (pull links with
`scripts/import_deck.py`). Full endpoint/fallback table: `references/data-sources.md`.

**Scryfall reads come from the local card database.** `scripts/scryfall_search.py` queries a **local
SQLite database** (`.mtg/database/cards.sqlite`, built from Scryfall bulk data — see the
**mtg-db** skill) instead of the API, built **automatically on first use** (one-time
~540 MB download). At the **start**, if it reports the data is **stale (>30 days)**, tell the user and
**ask** whether to refresh (for Arena this matters little — only rarity, Arena availability, and Standard
legality are used). `function:`/`otag:` (Tagger) queries route to the live API automatically.

**Retrieval (use what's available, in order):**
- **Code execution with network** → `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" "<query>" --limit 30` to search
  (reads the local DB, auto-builds on first use; Standard-legal + Arena, rarity shown), and
  `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --deck <arena>.txt --tier <N>` to tally a list's wildcard cost vs the
  tier. The script counts every non-basic card from zero — when a collection is loaded, subtract owned
  copies from its totals yourself.
- **No code-exec network, but web tools** → `web_fetch` the Scryfall search page for card data, **and
  `web_fetch` mtgtop8.com** for the meta and decklists — `mtgtop8.com/format?f=ST`,
  `mtgtop8.com/archetype?a=<id>&f=ST`, and a list via `mtgtop8.com/mtgo?d=<deckid>` (prompt for the verbatim
  list). Do **not** `web_fetch` untapped.gg/mtggoldfish/mtgdecks/aetherhub (Cloudflare — they 403). No DB
  can be built here — expected.
- **Neither** → tell the user the environment needs network to `api.scryfall.com`, and offer to proceed
  from known knowledge with the caveat that legality, rarity, and the current meta are unverified (Standard
  rotates and Arena availability varies — flag this clearly).

## Quality bar before you hand it over

- **Reconcile the files and the changelog.** Generate `arena.txt` from the upgraded annotated list; verify
  it sums to exactly **60** (main) and **15** (sideboard, if BO3), max 4 of any non-basic
  (`awk '/^Sideboard/{s=1} /^[0-9]/{if(s)sb+=$1; else md+=$1} END{print "main",md,"side",sb}' arena.txt`).
  The Changes section's cuts and adds must net to zero card-count change; every add appears in the final
  list and every cut is gone.
- **Legality & Arena availability:** every non-basic card is `legal:standard` and on Arena; no banned/rotated
  cards remain.
- **Colors — double-check castability:** every nonland card (especially anything you add) is castable in the
  deck's colors. Vet adds with color identity `id<=<colors>` (NOT `c:`, which also matches uncastable
  multicolor cards), and run `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --deck arena.txt --colors <wubrg>` — it must
  print `COLOR CHECK ✓` (catches e.g. a B/U or B/R card slipped into mono-black).
- **Wildcard budget:** the **rares and mythics the user must craft** (owned copies excluded) are within the
  tier's caps, or the user okayed an overage; commons/uncommons reported as soft. Show the breakdown of the
  *changes*.
- **Real improvement:** the swaps fix the Step 1 problems and improve the worst matchups, the mana base
  matches the deck's speed, and each change has a clear reason.
- **Rating included:** `deck.md` carries the **Deck Rating** section from Step 6 (overall ★ for the ladder at
  its tier + scorecard, before→after where possible). Only then present the files.

## Final step — always commit & push (every upgrade ends here)

This is the step that gets missed, so treat it as part of the deliverable, not an afterthought.
**After the two files are written and presented, the last thing you do — every single time — is push
them** by invoking the **mtg-sync** skill: `--push -m "<archetype>"`.

Run it **unconditionally**. Do *not* first reason about whether the workspace is a synced repo — just
run it. The helper handles every case and reports back:

- **`ok` (committed + pushed)** → confirm in one line that the deck was pushed to the `mtg-data` repo's
  main branch.
- **`skipped`** → the workspace isn't a synced git repo; say so in one line and stop (offer
  `--bootstrap` via mtg-sync if they'd like syncing set up).
- **`FAILED`** → e.g. offline or an auth issue; say so in one line — the deck is committed/saved
  locally and can be pushed later.

Only the *handling of that result* is best-effort. The **attempt is mandatory** — never end an upgrade
without running the push.
