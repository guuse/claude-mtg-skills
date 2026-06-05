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
  lower than building from scratch. Verifies legality and rarity via Scryfall; reads the live meta from
  untapped.gg/mtggoldfish. For 60-card Standard, NOT 100-card Commander/EDH.
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
format with a `Deck` header and optional `Sideboard`, but a plain `<count> <Card Name>` list is fine).
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
cost wildcards where it matters. The collection lives at **`.mtg/collection/mtga_collection.txt`** (a plain
`<count> <Card Name>` export):

- **No collection file present** → ask the user to export to `.mtg/collection/mtga_collection.txt`, and
  recommend the free exporter **https://github.com/NthPhantom10/MTGA-collection-exporter**. Make clear it's
  strongly recommended — with it, any upgrade card they already own costs **0 wildcards**, which often means
  the best upgrade is free. If they decline, proceed and cost added cards from zero.
- **Collection file present** → ask whether it's **up to date** and whether to **use it**; offer a
  re-export with the same tool if stale. Once confirmed, read it fully.

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

Always produce **two files**, saved in their own folder under `.mtg/decks/` in the user's current working
directory: `.mtg/decks/<deck-slug>/deck.md` and `.mtg/decks/<deck-slug>/arena.txt` (create the folder if
missing; slug = a short kebab-case deck name, with a suffix like `-upgraded` if a folder already exists).
See "The `.mtg` workspace" below.

1. **An annotated, upgraded decklist** (`deck.md`) — the full improved 60 (+ sideboard for BO3), cards
   grouped by role (Centerpiece/Payoffs, Creatures, Removal/Interaction, Card Advantage, Other Spells,
   Lands; plus Sideboard). Every line shows count, card name, **rarity (C/U/R/M)**, and a one-line reason.
   Include the mana curve, land count, the **wildcard-cost breakdown** of the *changes* (commons / uncommons
   / rares / mythics the user must craft vs the tier cap, owned cards excluded), the match type, and the
   meta plan. **Open with a "Changes" section** — each change as **— Cut `<card>` → Add `<card>` (rarity;
   reason; "owned" or "craft 1 R")**, grouped by the problem it fixes, plus the **total wildcards to craft
   vs the tier**.
2. **An Arena import list** (`arena.txt`) — exact MTG Arena import format: a `Deck` header, then
   `<count> <Card Name>` per line; a blank line then `Sideboard` and 15 cards if BO3. Generate it *from* the
   upgraded annotated list so they can't drift.

Use the `present_files` tool to share both — but **only at the end**, once the user has agreed to the
changes through the interactive method below. The files are the record of a conversation, not its opening
move.

## The `.mtg` workspace

All of this skill's file I/O lives in a `.mtg/` directory in the user's current working directory,
conventionally git-ignored (built output and personal collection data, not source).

**If there's no clear working directory to write to** — e.g. you're running in an interactive chat with no
project folder — **ask the user where the `.mtg/decks/` and `.mtg/collection/` directories should live**
(prompt for a path) before reading or writing anything, and use that location for the rest of the session.

The subdirectories:

- **`.mtg/decks/`** — where upgraded decks are written. **Each deck gets its own subfolder**,
  `.mtg/decks/<deck-slug>/`, holding `deck.md` and `arena.txt`. Same decks folder the other skills use.
- **`.mtg/collection/mtga_collection.txt`** — the user's Arena collection (owned cards), the inventory that
  makes owned upgrades free. See "Load the user's Arena collection" above.

(The pasted decklist is taken from the prompt, not a file.)

## The method (diagnose, then upgrade)

Full reasoning is in `references/methodology.md`; the Scryfall recipes are in `references/scryfall-syntax.md`;
the tier/wildcard logic is in `references/wildcard-budget.md`. Work in this order:

### Step 1 — Diagnose the current list, then talk it through with the user
Read the deck for the things that lose games: **rotated/illegal cards**, an inconsistent or wrong-speed
**mana base** (too few/many lands, taplands in an aggro deck, missing fixing), a **clunky curve**, **weak
or redundant** cards (win-more, off-plan filler), and **thin answers**. Note the biggest problems.

Then **share a short, readable diagnosis** and reconcile it with what the user told you in "Ask what's
wrong": where do their complaints and your read agree, and where does your read surface something they
didn't raise? **Agree on the top 2–3 priorities together before proposing any cards.**

### Step 2 — Read the meta and find the bad matchups
Pull the current Standard ladder meta (untapped.gg BO1, mtggoldfish) and identify the top decks. Ask which
matchups the user is losing. The upgrade should improve the worst real matchups, not just add power in a
vacuum.

### Step 3 — Rank upgrades by impact per wildcard, owned-first
For each problem, gather candidate fixes from the meta sites and Scryfall (`references/scryfall-syntax.md`).
**Scan the collection first** — an owned card that fixes the problem is the best upgrade because it costs
nothing. Reach for un-owned cards when they're clearly better and worth a wildcard. Favor cheaper-by-rarity
cards that do most of the job (a common/uncommon answer over a premium rare when close).

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
then** assemble the final 60 (+sideboard), run the quality checks below, and write the two files.

## Data sources

Same as the builder. **Scryfall** is the source of truth for Standard legality, rarity, Arena availability,
and oracle text (`legal:standard`, `game:arena`, `r:rare`/`r:mythic`; every card has a `rarity` field).
**untapped.gg** (`https://mtga.untapped.gg/constructed/standard`) for the BO1 ladder meta; **mtggoldfish**
(`https://www.mtggoldfish.com/metagame/standard`) for metagame %s and netdecks.

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
- **No code-exec network, but web tools** → `web_search` then `web_fetch` (web_fetch only takes URLs from a
  prior search). No DB can be built here — that's the expected fallback.
- **Neither** → tell the user the environment needs network to `api.scryfall.com`, `untapped.gg`, and
  `mtggoldfish.com`, and offer to proceed from known knowledge with the caveat that legality, rarity, and
  the current meta are unverified (Standard rotates and Arena availability varies — flag this clearly).

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
  matches the deck's speed, and each change has a clear reason. Only then present the files.
