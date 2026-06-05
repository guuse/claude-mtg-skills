---
name: mtg-commander-deckupgrader
description: >-
  Improve an existing 100-card Magic the Gathering Commander (EDH) deck that the user pastes in. Use this
  skill whenever the user already has a Commander/EDH decklist and wants to upgrade, tune, optimize, fix, or
  "make it better" — rather than build a new deck from scratch. Triggers on phrases like "upgrade my
  commander deck", "improve this EDH deck", "here's my decklist, what should I change", "tune my Atraxa
  list", "what are the best upgrades for my deck", "help me cut/add cards", or any request that pastes or
  references an existing 100-card list and asks for improvements. The user pastes their current list inline.
  The skill diagnoses the deck against a proven 7-step methodology (land count, card advantage, ramp,
  interaction, curve, win conditions), then recommends the highest-impact swaps within a budget — and
  because this is an upgrade, the budget is usually much smaller than building a deck from scratch. Prices
  everything via Scryfall (Cardmarket EUR) and respects the deck's color identity and power bracket.
---

# MTG Commander Deck Upgrader

This skill takes a Commander deck the user **already has** and makes it meaningfully better. It uses the
same proven building methodology as the deckbuilder — the target shape of a functioning 100 (right land
count, enough card advantage, enough ramp, enough interaction, a sensible curve, real win conditions) — but
applies it as a **diagnosis-and-swap** pass: find where the current list is weakest, then spend a (usually
small) budget on the changes that fix the most for the least.

The core idea: **an upgrade is not a rebuild.** A few well-chosen swaps often improve a deck far more than
their cost suggests. Respect what the user already owns and likes; change what's actually holding the deck
back.

**Work interactively — this is a conversation, not a one-shot transform.** The user knows how their deck
actually plays; you know the card pool and the methodology. Combine them: ask what's wrong, react to what
they tell you, propose changes in digestible batches, and refine based on their feedback. Do **not** dump a
finished 100-card list and call it done. Talk through your reasoning, surface options, and only write the
final files once the user has agreed to the changes. Default to asking a question rather than assuming.

## Start here: paste your decklist

The user provides their **current decklist inline** in their prompt (pasted text — a Moxfield/Archidekt
export, a `1 Card Name` list, or even a rough list). Begin by parsing it:

- Identify the **commander** and its **color identity** (the only colors legal in the 99). Pull the real
  Oracle text from Scryfall.
- Read the **theme/engine** the deck is already going for — don't impose a new plan, sharpen the existing
  one (unless the user asks to re-pivot).
- **Price and categorize** every card via Scryfall (`prices.eur`, Cardmarket), tallying the current
  category counts (lands / ramp / card advantage / interaction / themed / win cons) and the total value.

If the pasted list is short of 100, malformed, or ambiguous, say what you found and ask the user to confirm
before proceeding.

## Ask what's wrong and what they want improved

Before you diagnose anything yourself, **ask the user what they think is wrong with the deck and what they
want it to do better.** They've played it; that's information you can't get from the list alone. Ask in
plain language (a few questions, not a wall) — for example:

- **What does it struggle with?** Slow starts / mana problems, runs out of cards, can't close games, folds
  to board wipes or removal, loses to a particular deck or player at your table.
- **What do you want it to do better?** Faster, grindier, more resilient, lean harder into the theme, hit a
  higher or lower power level.
- **What's off-limits or precious?** Pet cards you want to keep, cards you already own vs. won't buy, things
  you've tried that didn't work.

Let their answers steer the upgrade — **their lived pain points outrank your own read** when they conflict.
But if your tally later surfaces a problem they didn't mention (e.g. only 33 lands, or two pieces of card
advantage), **raise it and ask** whether they want it addressed rather than silently "fixing" it.

## Then confirm: bracket and upgrade budget

Two parameters, same as the builder — confirm them up front unless the user already stated both:

- **Power bracket (1–5)** — where the user wants the deck to land (it may differ from where it is now). See
  `references/brackets.md`. Default to keeping the deck at its current bracket if the user is unsure.
- **Upgrade budget cap** — a total spend in EUR (Cardmarket) for the changes, or "no cap". **Because this
  is an upgrade, the budget can be much lower than building from scratch** — even €10–30 of well-targeted
  swaps can noticeably improve a deck. Ask for their cap, suggest that a small budget is fine, and make the
  spend count: prioritize the cheapest changes that fix the biggest weaknesses first.

## The deliverable

Always produce **two files**, saved in their own folder under `.mtg/decks/` in the user's current working
directory: `.mtg/decks/<deck-slug>/deck.md` and `.mtg/decks/<deck-slug>/import.txt` (create the folder if
missing; slug = the commander name, kebab-case, with a suffix like `-upgraded` if a folder already exists).
See "The `.mtg` workspace" below.

1. **An annotated, upgraded decklist** (`deck.md`) — the full improved 100, cards grouped by role
   (Commander, Lands, Ramp, Card Advantage, Interaction, Synergy/Themed, Win Conditions), each line showing
   card name, mana value, a one-line reason, and Cardmarket EUR price. Include category counts, total deck
   value, and the target bracket. **Open with a "Changes" section** that is the heart of an upgrade: each
   change as **— Cut `<card>` → Add `<card>` (reason; €X)**, grouped by the weakness it fixes, plus the
   **total upgrade spend vs the budget cap** and a short "what these changes do" paragraph.
2. **A plain importable list** (`import.txt`) — the upgraded 100 as `1 Card Name`, commander on its own
   first line, ready to paste into Moxfield / Archidekt / mtggoldfish. Generate it *from* the upgraded
   annotated list so they can't drift.

Use the `present_files` tool to share both — but **only at the end**, once the user has agreed to the
changes through the interactive method below. The files are the record of a conversation, not its opening
move.

## The `.mtg` workspace

All of this skill's file I/O lives in one **workspace** directory holding `database/`, `decks/`, and
`collection/`. It is resolved in this order:

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
they set `$MTG_HOME`) before writing anything, and use that location for the rest of the session.

The subdirectory:

- **`.mtg/decks/`** — where upgraded decks are written. **Each deck gets its own subfolder**,
  `.mtg/decks/<deck-slug>/`, holding `deck.md` and `import.txt`. This is the same decks folder the other
  deckbuilding skills use. Create the directories if they're missing.

(The pasted decklist is taken from the prompt, not a file — there's no input file to read.)

## The method (diagnose, then upgrade)

The target shape of a functioning 100 and the reasoning behind every number live in
`references/methodology.md` — read it before diagnosing. The Scryfall query cookbook for finding upgrade
candidates is in `references/scryfall-syntax.md`. Work in this order:

### Step 1 — Diagnose the current list, then talk it through with the user
Tally the existing deck and compare it to the methodology's targets: ~37–38 lands, **12+ net-positive**
card-advantage pieces, ~10–11 ramp, ~10 interaction + 2–4 board wipes, 3–4 real win conditions, a sensible
curve, and color-identity legality. Note the **biggest gaps** — too few lands, thin card advantage,
not enough/inefficient interaction, a top-heavy curve, or no clear way to actually close the game.

Then **share a short, readable diagnosis** and reconcile it with what the user told you in "Ask what's
wrong": where do their complaints and your tally agree, and where does your tally reveal something they
didn't raise? **Agree on the top 2–3 priorities together before proposing any cards.** Don't proceed to
swaps until you and the user are aligned on what this upgrade is actually for.

### Step 2 — Rank upgrade candidates by impact per euro
For each gap, gather candidates **primarily from EDHREC and mtgdecks.net** for this commander (what proven
lists run that this deck lacks), then fill with **Scryfall** for budget- and bracket-appropriate options
(`references/scryfall-syntax.md`). Favor cards that fix a real weakness *and* synergize with the existing
theme. Cheaper-but-sufficient beats expensive-but-marginal — the goal is the most improvement within the
cap.

### Step 3 — Choose the swaps (what to cut)
For every add, name the **cut**: the weakest card serving the same or a lower-priority role (off-theme
filler, an overcosted card the curve doesn't need, a win-more card, a strictly worse duplicate effect).
Keep the deck at exactly **100**. Don't cut cards the user flagged as favorites unless they're clearly
hurting the deck — and if so, explain why and offer the choice.

### Step 4 — Respect budget and bracket
Keep the running spend under the cap; if a high-impact swap blows the budget, find a cheaper card that does
most of the same job (`references/scryfall-syntax.md`). Enforce bracket rules (Game Changer count, combo
restrictions — `references/brackets.md`): an upgrade must not silently push the deck past its target
bracket. Re-check the category counts after the swaps and adjust until the deck hits the target shape.

### Step 5 — Propose, discuss, and iterate (don't write files yet)
**Present the proposed swaps to the user for reaction before finalizing** — ideally in small batches by
priority (e.g. "first, the mana base", then "card advantage"), each as **Cut → Add, why, €cost**, with the
running spend. Invite them to veto, ask why, suggest their own cards, or push for cheaper/spicier options,
and **adjust accordingly**. Where there's a real choice, offer 2–3 options rather than dictating one. Keep
going until the user is happy with the full set of changes. **Only then** assemble the final 100, run the
quality checks below, and write the two files.

## How to drive the data sources

Same backbone as the deckbuilder — **EDHREC + mtgdecks.net** for proven inclusions, **Scryfall** to fill
gaps, enforce color identity, filter by mana value, and **price** every card (`prices.eur` = Cardmarket
EUR).

**Scryfall reads come from the local card database.** `scripts/scryfall_search.py` queries a **local
SQLite database** (`.mtg/database/cards.sqlite`, built from Scryfall bulk data — see the
**mtg-scryfall-database** skill) instead of the API. It's built **automatically on first use** (one-time
~540 MB download); just call the script. At the **start**, if it reports the data is **stale (>30 days)**,
tell the user prices may have moved and **ask** whether to refresh before continuing. `function:`/`otag:`
(Tagger) tags route to the live API automatically. Retrieval, in order of preference:

- **Code execution with network** → `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" "<query>" --limit 30` (reads the
  local DB, auto-builds on first use; color identity, cheapest-printing pricing; `--named "Sol Ring"` for
  one card). Fastest path. `function:` queries use the live API transparently.
- **No code-exec network, but web tools** → `web_search` for the Scryfall / EDHREC / mtgdecks page, then
  `web_fetch` the result (web_fetch only takes URLs from a prior search, so search first). No DB can be
  built here — that's the expected fallback.
- **Neither** → tell the user the environment needs network to `api.scryfall.com`, `edhrec.com`, and
  `mtgdecks.net`, and offer to proceed from known MTG knowledge with the caveat that prices and the newest
  cards won't be verified.

If there's no clear working directory to write the database to, prompt the user for a path for `.mtg/`
first.

## Quality bar before you hand it over

- **Reconcile the files and the changelog.** Generate `import.txt` from the upgraded annotated list. Verify
  it sums to exactly **100** with no duplicate non-basic names (`awk '{s+=$1} END{print s}' import.txt`
  prints `100`; `sed 's/^[0-9]* //' import.txt | sort | uniq -d` prints nothing). The **Changes** section's
  cuts and adds must net to zero card-count change, and every added card must appear in the final list and
  every cut must be gone.
- **Within budget & bracket:** total upgrade spend ≤ the cap (or the user okayed an overage); color
  identity legal for every card; bracket rules satisfied.
- **Double-check colors:** every card you add is within the commander's color identity — vet with
  `id<=<identity>` (NOT `c:`, which also matches off-identity multicolor cards) and check the search **CI**
  column. One off-identity pip makes a card illegal in the deck.
- **Real improvement:** the changes measurably move the deck toward the target shape (the gaps from Step 1
  are smaller), and each swap has a clear reason. Only then present the files.
