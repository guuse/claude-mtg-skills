---
name: mtg-edh-primer
description: >-
  Generate a comprehensive, publish-ready **primer** for an existing 100-card Magic: The Gathering
  Commander (EDH) deck — a deep "how this deck works and how to pilot it" guide, plus a role-tagged
  Moxfield import. Use this skill whenever the user wants to explain, document, or write up a Commander
  deck rather than build, upgrade, or merely rate one: "generate a primer", "write a primer for my deck",
  "create a deck guide", "explain how my deck works / how do I win with it", "how do I pilot this", "tag
  my deck by role", "make a Moxfield primer", or "document my <commander> deck". The user gives a deck
  either by **slug** (a deck already in the workspace, `.mtg/decks/edh/<slug>/import.txt`) or by **pasting
  a list inline**. The skill reads every card's Oracle text from the local Scryfall database, infers the
  deck's win conditions and theme, classifies every card into role + theme tags (mana dork, sac outlet,
  fatty, draw, drain, recursion, removal, finisher, land, …), explains each card in one tight line in the
  context of the deck, writes an early/mid/late play guide with a mulligan note and common-misplays
  callout, and awards a ★ rating shown beside the deck's power Bracket. Outputs two files —
  `primer.md` (the publish-ready primer) and `moxfield-import.txt` (the tagged import) — and never
  touches the deck's `deck.md`/`import.txt`. For Commander/EDH; explains a deck rather than building
  (`mtg-edh-build`), swapping cards (`mtg-edh-upgrade`), or only scoring it (`mtg-edh-analyze`).
---

# MTG Commander Deck Primer Generator

This skill turns an existing Commander deck into a **primer**: the document you'd publish so anyone — or
future-you — can understand *how the deck wins* and *how to pilot it*, card by card. It is the **explain/teach**
counterpart to the suite: it doesn't build (`mtg-edh-build`), swap cards (`mtg-edh-upgrade`), or just score
(`mtg-edh-analyze`) — it **reads the deck and explains it**, then hands the score back via the same rating
rubric.

Two principles keep it honest:

1. **Read the cards, don't guess from names.** Win conditions, a card's real job, and the theme all live in the
   **Oracle text** — which `scripts/analyze_deck.py` pulls from the local Scryfall database. The wincon read and
   the per-card lines must reflect actual text, not vibes.
2. **Every card earns its place on the page.** The primer's value is that it explains *each* card *in the
   context of this deck* — one tight, purposeful line — and groups them by the job they do.

## Start here: get the deck

The user gives the deck one of two ways:

- **By slug** — a deck already in the workspace. Read `.mtg/decks/edh/<slug>/import.txt`. (Run
  `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --paths` to resolve the `decks/` location; honours
  `$MTG_HOME`.) This is the common path and means the primer lands in the right folder automatically.
- **Pasted inline** — a Moxfield/Archidekt export or a `1 Card Name` list. Write it to a temp file (e.g.
  `.mtg/decks/edh/<slug>/import.txt` if you're creating the folder, or any temp path).
- **By link** — a Moxfield/Archidekt URL: run `scripts/import_deck.py <url>` to pull the list via the site
  JSON API (it falls back to asking for a paste if the deck is private/unreachable; never invents a list),
  then write its output to a temp file as above.

Identify the **commander** (a Commander-section/`*CMDR*` card, or ask) and confirm the **target bracket (1–5)**
the deck is meant for — if unsure, rate at the bracket the deck looks like, and say so. If the list isn't ~100
cards or the commander is ambiguous, say what you found and confirm before writing.

## The `.mtg` workspace, the database, and syncing

Same backbone as the other deck skills:

- **Workspace** resolves via `$MTG_HOME` → nearest `.mtg/` → `./.mtg/`. `scripts/scryfall_search.py --paths`
  prints the resolved `decks/`/`database/` paths as JSON and creates nothing. Decks live under
  `.mtg/decks/edh/<slug>/`.
- **Database**: the scripts read the local Scryfall SQLite DB (`.mtg/database/cards.sqlite`), **built
  automatically on first use** by the shared library (the **mtg-db** skill). If it reports the data is **stale
  (>30 days)**, tell the user prices/sets may have moved and offer to refresh.
- **Syncing** (if the workspace is a synced git repo): invoke **mtg-sync** to **pull** before reading and to
  **push** after writing the primer (`--push -m "primer: <commander>"`). Best-effort — if it reports
  `skipped`/`FAILED`, note it in one line and continue; the files are saved locally.

## Run the analysis

Run the bundled analyzer to get the objective data the primer is built from:

```
python "${CLAUDE_SKILL_DIR}/scripts/analyze_deck.py" <import.txt> --commander "<name>" --json
```

It returns, per card: **Oracle text**, type line, mana value, EUR price, EDHREC rank — plus deck aggregates:
card/land count, **mana curve**, average MV, **EDHREC-rank staple signal**, **Game Changer count**,
**off-color-identity** cards, total price, and any cards not found. You do the reading and judging on top.

## Build the primer (the method)

### Step 1 — Infer the win conditions and theme
Read the commander + every card's Oracle text and match the deck to one or more patterns in
`references/win-patterns.md` (use `references/synergy.md`'s read→extract→intersect method). Name the
**1–4 real, repeatable** win conditions, each with its **key enabling cards**, the primary plan vs backups, and
any **two-card combo** (matters for bracket). Note the deck's speed (from curve + ramp) — it sets the play
guide's turn bands.

### Step 2 — Tag every card (one or more tags, ordered tiers)
Using `references/tags.md`, tag each non-commander card with **every category it genuinely belongs to** — a
card that does several jobs gets several tags (e.g. an evasive creature that's also a draw engine *and*
removal). Build tags in **two ordered tiers**: a **numbered engine** (`1) … 2) … 3) …`) naming *how this deck
wins* in execution order, in the **flavour of the deck** (tasteful, never cringe — `3) Ninjutsu - Targets`,
not `3) Sneaky Backstab Bois`), and the **lettered support pillars** (`A) Mana Advantage`, `B) Card Advantage`,
`C) Interaction`, `D) Resilience`, `E) Lands`) for the universal jobs, lands last. The prefixes force
Moxfield's Group-by-Tag view to render in deliberate order. **Never tag the commander** — Moxfield labels it in
its own zone, so the commander line gets no tag.

### Step 3 — Write the per-card lines
**One tight line per card, in the context of *this* deck** — its job here, not its generic Oracle text. Give
**marquee/engine cards 2–3 lines**. Every nonland card and every nonbasic/utility land gets a line; **collapse
basic lands to one summary line** (`6 Forest · 6 Swamp — fixing`), never one line per basic. In the prose,
group each card under its **most-defining** category (prefer the engine tier when a card spans both tiers).

**Card names are Moxfield card links, never code blocks.** Every time a card is named *anywhere* in
`primer.md` — per-card lines, "How it wins", the play guide, the rating's cheapest-fixes note, weaknesses,
everywhere — wrap the exact card name in double square brackets: `[[Sheoldred, Whispering One]]`, **not**
`` `Sheoldred, Whispering One` `` and not bare text. Moxfield renders `[[Name]]` as a hover-preview link to the
card image; backticks render as dead monospace and waste the feature. The text inside the brackets must be the
real card name including punctuation (matching is case-insensitive); keep any annotation outside the brackets —
`[[Guardian Project]] (€2)`. Reserve backticks for things that are **not** card names: mana costs (`{2}{U}{B}`),
the basic-land summary line, and literal file/code snippets.

### Step 4 — Write the play guide
- **Mulligan / opening hand** — what to keep, what to ship.
- **Early / Mid / Late** — three phases with **deck-tuned turn bands** (default ≈T1–4 / T4–8 / T8+; shift them
  for a fast or slow deck). Each phase covers: *what to prioritise · your lines & options · what to watch out
  for · counterplay vs other players* (multiplayer politics, board wipes, archenemy heat).
- **Common misplays** — a short callout of the traps specific to piloting this deck.

### Step 5 — Rate it (★ scorecard at the top of the primer)
**Every primer includes a rating — there are no exceptions.** Score the deck against its **target bracket**
with the five-dimension rubric in `references/rating.md` (structure & consistency, synergy density, staples &
card quality, win conditions, bracket calibration) — do **not** restate the rubric here, follow it — using the
`analyze_deck.py` numbers + `references/brackets.md`. This is the same rubric the **mtg-edh-analyze** skill
uses; the primer reports a **compact summary** of it, not a full analysis.

Render the result as a **Rating block placed right after the header**, in three parts:

1. A **one-line headline**, e.g. `Rating: ★★★★☆ (4/5) — strong Bracket 3` (use half-stars; state the deck's
   *actual* bracket if it differs from the target).
2. A **compact per-dimension scorecard table** — the five dimensions, each with its stars **and the numbers
   behind the score** (e.g. `Structure ★★★★ — 37 lands, 11 ramp, 13 draw, 9 removal + 3 wipes`). One row each;
   keep it tight.
3. **One line** naming the **biggest gaps + their cheapest fixes** (e.g. "Thin draw (9, want 12+) and only one
   wipe — cheapest fixes: Guardian Project (€2), Blasphemous Act (€1).").

Always pair the stars with the bracket and state this rule plainly beside them:

> **★ ≠ bracket.** The stars rate how good the deck is *within its bracket*; the bracket is its absolute power
> tier. A **2★ Bracket 4** deck is more powerful than a **5★ Bracket 2** deck.

If the deck is mis-bracketed (e.g. Game Changers above its bracket's cap, or an early infinite combo), say so
and report the bracket it actually sits at. Keep the whole block short — it's the primer's summary scorecard,
not the full report `mtg-edh-analyze` would write.

## The deliverables

Write two files into `.mtg/decks/edh/<slug>/`, and **never modify `deck.md` or `import.txt`** (those are
build/upgrade's status + plain-list outputs):

1. **`primer.md`** — the publish-ready primer, in this order:
   - **Header:** deck name + commander; the **`Rating: ★★★★☆ (4/5) — strong Bracket 3`** headline + the
     ★≠bracket note; colors; total value.
   - **Rating** *(right after the header — Step 5)* — the compact per-dimension scorecard table (each dimension's
     stars + the numbers behind it) and the one-line biggest-gaps + cheapest-fixes note. Short; it's the
     summary, not a full analysis.
   - **TL;DR** — 2–3 sentences: archetype, how it plays, how it wins.
   - **How it wins** — the named win conditions (Step 1).
   - **Card roles & tags** — a one-line legend naming the deck's **numbered engine tiers** and the lettered
     support pillars, then cards grouped by their most-defining tag with one-line explanations (Step 3). State
     that the **same tags (one or more per card)** are in `moxfield-import.txt`, and that **the tags only take
     effect via Moxfield's Bulk Edit — not the Import/netdeck screen** (see below); once applied, group by Tag
     in Moxfield to read the deck in deliberate order.
   - **Play guide** — mulligan, early/mid/late, common misplays (Step 4).
   - **Strengths & weaknesses** — and how to play around the weaknesses.
   It's plain Markdown that pastes straight into Moxfield's Notes/Primer tab. **Every card name is a
   `[[Card Name]]` link** (Step 3), so the published primer shows a hover preview of each card.
2. **`moxfield-import.txt`** — the 100-card list where each non-commander card carries **one or more**
   deck-defining tags (see `references/tags.md`): a **numbered engine** (`1) … 2) …`, deck-flavoured, in
   execution order) plus the **lettered support pillars** (`A) … E) Lands`), each tag written `#…` (no
   quoting — Moxfield ends a tag at the next `#`) and ordered by tier on the line. Built from `import.txt` so
   each card line — name **and** its exact
   `(SET) collector#` printing — stays byte-for-byte identical (only the trailing `#…` tags are appended).
   **The commander comes first and carries no tag** (Moxfield labels it in its own zone), then a blank line,
   then the 99. Include a short usage note in `primer.md` explaining that Moxfield's **Import/netdeck screen
   ignores the `#Tags`** — paste this file into Moxfield's **Bulk Edit** box instead to apply them.

Use the file-presentation tool to share both once written.

## Quality bar

- **Grounded:** every win condition and per-card line reflects the actual Oracle text (from `analyze_deck.py`),
  not the card name.
- **Hover-linked cards:** every card name in `primer.md` is wrapped as a `[[Card Name]]` Moxfield link (never a
  backtick code block), so each renders as a hover-preview card; backticks are reserved for mana costs, the
  basic-land summary, and literal snippets.
- **Complete & tagged:** every nonland card + notable land has a line; basics are summarised; **every
  non-commander card in `moxfield-import.txt` carries one or more fitting tags (numbered engine + lettered
  pillars, written `#…` unquoted), the commander line carries none**, and each line (name + `(SET) collector#`
  printing) matches `import.txt` exactly (it still sums to 100). The Bulk-Edit-not-Import workflow is stated in
  the primer.
- **Honest rating:** the primer opens with the rating — a one-line headline, the compact per-dimension
  scorecard with the numbers behind each score, and the biggest-gaps + cheapest-fixes line — scored against the
  rubric at the stated bracket, with the ★≠bracket rule shown and mis-bracketing called out.
- **Non-destructive:** `deck.md` and `import.txt` are untouched; only `primer.md` and `moxfield-import.txt` are
  written.
