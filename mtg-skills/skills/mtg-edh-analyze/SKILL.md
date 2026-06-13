---
name: mtg-edh-analyze
description: >-
  Analyze and star-rate an existing 100-card Magic the Gathering Commander (EDH) deck that the user pastes
  in, judged against a target power bracket. Use this skill whenever the user wants their Commander deck
  rated, scored, graded, reviewed, or assessed — "how good is my deck", "rate my EDH deck", "give my deck a
  score out of 5", "how does this deck stack up at Bracket 3", "analyze my commander deck", "is this deck any
  good", "what bracket is my deck", or any request to evaluate a Commander list rather than build or upgrade
  one. The user pastes their current decklist inline and names (or is asked for) a target bracket (1–5). The
  skill measures the deck's hard stats (land count, mana curve, ramp/draw/interaction density, EDHREC-rank
  staple signal, Game Changer count, color-identity legality, price) via the local Scryfall database, reads
  every card's Oracle text to score synergy density, then awards an overall ★ rating (with a per-dimension
  scorecard) for how well the deck performs *at its bracket* — covering performance fundamentals, synergy,
  staples/card quality, win conditions, and bracket fit — and names the highest-impact fixes. For diagnosing
  and scoring a deck; to then change cards, it hands off to mtg-edh-upgrade.
---

# MTG Commander Deck Analyzer & Star Rating

This skill takes a Commander deck the user pastes in and **rates it out of five stars against a target
bracket**, with a transparent scorecard and concrete next steps. It is the *evaluation* counterpart to the
deckbuilding skills: it doesn't build (`mtg-edh-build`) or swap cards (`mtg-edh-upgrade`) — it **measures and
judges**, then points at what to fix.

Two principles keep the rating honest:

1. **The bracket is the benchmark.** Five stars means "an excellent deck *for this bracket*", not "a cEDH
   deck". A tuned Bracket 2 list and a sharp Bracket 4 list can both earn ★★★★★ at their own level. Always
   report the stars **and** where the deck actually sits on the 1–5 bracket scale — and if those disagree,
   say so plainly (a deck stuffed with Game Changers is not a five-star "Bracket 2" deck; it's mis-bracketed).
2. **The score is built from evidence, not vibes.** Every dimension is scored against the explicit rubric in
   `references/rating.md`, backed by hard numbers from `scripts/analyze_deck.py` and by **reading the actual
   Oracle text** of the cards (the synergy score can't be faked from names). The rating's whole value is that
   it points at *exactly* what's strong and what to fix.

## Start here: paste your decklist and name a bracket

- The user provides their **decklist inline** (a Moxfield/Archidekt export, a `1 Card Name` list, or a rough
  list), or a **Moxfield/Archidekt link** — for a link, run `scripts/import_deck.py <url>` to pull it via
  the site JSON API (it falls back to asking for a paste if the deck is private/unreachable; never invents
  a list). To analyze, **write the list to a temp file and run the analyzer** (see below) — the parser
  tolerates counts or no counts, `1x`, `(SET) 123` and `*CMDR*` markers, and section headers.
- Confirm the **target bracket (1–5)** — the power level to judge the deck *against*. If the user doesn't
  give one, **ask**, and offer to also tell them which bracket the deck actually looks like. Default to
  rating at the deck's apparent bracket if they're unsure. See `references/brackets.md`.
- Identify the **commander** (a `*CMDR*`/Commander-section card, or ask) and its **color identity** — needed
  for the legality check and for reading synergy against the right card.

If the pasted list isn't ~100 cards, is malformed, or the commander is ambiguous, say what you found and
confirm with the user before rating.

## How to run the analysis

The bundled **`scripts/analyze_deck.py`** does the measuring; **you** do the judging.

1. Save the pasted list to a temp file (e.g. `.mtg/analysis/<slug>-input.txt`, or any temp path).
2. Run `python "${CLAUDE_SKILL_DIR}/scripts/analyze_deck.py" <file> --commander "<name>" --json` (add
   `--identity <letters>` if you already know it). It looks every card up in the local Scryfall database and
   returns: total cards, land count, **mana curve**, average MV, **EDHREC-rank staple signal** (premier
   ≤500 / staple ≤1500 / played ≤4000 counts + median rank + unranked count), **Game Changer count**,
   **off-color-identity** cards, total price (Cardmarket EUR), any **cards not found**, and the **full
   per-card data including Oracle text and type line**.
3. **Read the per-card Oracle text** to classify each card's role (land / ramp / card advantage / interaction
   / board wipe / synergy / wincon) and to **score synergy** — `analyze_deck.py` gives the objective stats,
   but classification and synergy are judgment calls that need the wording. Use `scryfall_search.py` for
   anything extra: `--named "Card"` for a card's exact text, `function:ramp id<=<colors>` / `function:removal
   …` / `is:gamechanger id<=<colors>` to spot staples the deck is *missing*.

If the database can't be built or reached, fall back to `web_search`/`web_fetch` of Scryfall pages (and say
prices/newest cards are unverified), or to known MTG knowledge — but prefer the local DB; it's what makes the
staple and curve signals reliable.

## Score it: the five-dimension rubric

Apply the rubric in **`references/rating.md`** (read it). Score each dimension 1–5 (half-stars allowed), then
combine by weight and apply the gates:

1. **Structure & consistency** *(30%)* — lands ~37–38, ramp ~10–11, **≥12 net-positive card advantage**, ~10
   interaction + 2–4 wipes, a curve with only 3–4 cards at MV 6+. The fundamentals that win games.
2. **Synergy density** *(25%)* — via `references/synergy.md`: what fraction of non-structural cards clear the
   **≥2–3 points of contact** bar, the average contact count, and whether engines reinforce each other.
3. **Staples & card quality** *(20%)* — the EDHREC-rank signal plus judgment on whether the right efficient,
   on-theme cards are present and which obvious ones are missing. Scaled to bracket (B1–2 lenient, B3–5
   demanding).
4. **Win conditions & closing power** *(15%)* — 3–4 real, repeatable, resilient ways to actually end the
   game from a normal board.
5. **Bracket calibration** *(10%, partial gate)* — Game Changer count vs. the bracket cap, combos, fast mana,
   tutors, MLD. A deck that **violates** its target bracket is mis-bracketed: report its real bracket and cap
   the score. See `references/brackets.md`.

`overall = 0.30·structure + 0.25·synergy + 0.20·staples + 0.15·wincons + 0.10·bracket`, rounded to the
nearest half-star, then capped by the gates in `references/rating.md` (a dimension at 1, a missing
fundamental, or a mis-bracket all cap the headline).

## The deliverable

Hand back a **rating report** in the conversation:

1. **Headline** — e.g. `★★★★☆ (4/5) — a strong Bracket 3 deck`, plus the **actual bracket** if it differs.
2. **Scorecard** — the five dimensions, each with its stars and the **numbers behind it** (show the
   analyzer's stats: "Structure ★★★★ — 37 lands, 11 ramp, 13 draw, 9 interaction + 3 wipes; curve fine").
3. **Strengths (2–3)** and **weaknesses (2–3)** — concrete, each tied to a dimension.
4. **Highest-impact fixes (3–5)** — cheapest-first changes that would raise the score most, and an **offer to
   hand off to `mtg-edh-upgrade`** to actually make the swaps (carry over the diagnosis).

Keep it honest and specific — "card advantage is thin (9, want 12+)" beats "could be better".

**Saving the report is optional — write a file only if the user asks.** When they do, save it as
`.mtg/analysis/<deck-slug>.md` in the resolved workspace (slug = commander name, kebab-case) and share it with
`present_files`. Don't write decks or import lists here — that's the upgrade skill's job.

## The `.mtg` workspace

This skill mostly reads; it writes only the temp input file and (on request) a report. Its I/O lives in the
same **workspace** the other MTG skills use, resolved in this order:

1. **`$MTG_HOME`**, if set — the user's portable data location (e.g. a private `mtg-data` git repo; see
   `SYNCING.md`). Use it even if subfolders don't exist yet — create them.
2. Otherwise the nearest **`.mtg/`** at or above the current working directory (conventionally git-ignored).

Run `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --paths` to print the resolved paths; analysis
files go in a sibling `analysis/` folder. If `$MTG_HOME` is unset and there's no clear working directory and
the user wants a file saved, ask where the workspace should live first; a pure in-chat rating that writes only
a temp file doesn't need this. If a `collection/` file exists, you can note which suggested fixes the user
already owns.

**Scryfall reads come from the local card database** (`scripts/analyze_deck.py` and `scripts/scryfall_search.py`
both read `.mtg/database/cards.sqlite`, built from Scryfall bulk data — see the **mtg-db** skill; built
automatically on first use, one-time ~540 MB). If it reports the data is **stale (>30 days)**, mention prices
and the staple signal may have shifted and **ask** whether to refresh first. `function:`/`otag:` (Tagger)
queries route to the live API automatically.

## Quality bar before you hand it over

- **Every dimension score is backed by the analyzer's numbers and by Oracle text you actually read** — the
  synergy score in particular names specific high-contact and zero-contact cards, not a guess.
- **The headline rating is consistent with the rubric and the gates** (`references/rating.md`) — a deck
  missing a fundamental or breaking its bracket isn't quietly handed four stars.
- **Bracket is reported two ways** when they differ: the rating *as the target bracket*, and the deck's
  *actual* bracket placement.
- **Color identity is checked** — `analyze_deck.py` flags off-identity cards; surface any (one off-identity
  pip makes a card illegal in the deck) and any cards not found in the database (so the user can fix typos).
- **The fixes are concrete, prioritized, and cheapest-first**, with an offer to hand off to `mtg-edh-upgrade`.
