---
name: mtg-commander-deckbuilder
description: >-
  Build a complete, balanced 100-card Magic the Gathering Commander (EDH) deck around a chosen commander.
  Use this skill whenever the user wants to build, brew, design, or upgrade a Commander/EDH deck, names a
  legendary creature and asks "build a deck around X", asks for a decklist for a commander, wants help
  picking cards that synergize with a commander, or wants a Commander deck within a budget or at a specific
  power bracket. Triggers on phrases like "build me a commander deck", "EDH deck for [commander]", "brew
  around [legendary creature]", "100-card singleton deck", "help me build my Atraxa deck", or any request
  that pairs a commander name with deckbuilding. The skill pulls proven cards from EDHREC and mtgdecks.net,
  fills gaps and prices everything via Scryfall (which carries Cardmarket EUR prices), and applies a
  disciplined 7-step methodology to produce a tuned list with per-card pricing and a budget/bracket target.
---

# MTG Commander Deck Builder

This skill builds a complete, well-tuned 100-card Commander deck around any commander the user
chooses. It combines two things: **proven card data** (what real players actually run, from EDHREC
and mtgdecks.net, priced through Scryfall) and a **disciplined 7-step building methodology** that turns a
pile of synergistic cards into a deck that actually functions — correct card-advantage density, enough
ramp, enough interaction, the right land count, a sensible curve, and real win conditions.

A deck is not a list of the 99 most powerful cards in a color. It is a machine where the parts reinforce
each other. The whole job of this skill is to build that machine.

## The deliverable

Always produce **two files** at the end (the user expects both):

1. **An annotated decklist** (`<commander>-deck.md`) — cards grouped by role (Commander, Lands, Ramp,
   Card Advantage, Interaction, Synergy/Themed, Win Conditions), each line showing the card name, mana
   value, a one-line reason it's in the deck, and its Cardmarket price in EUR. Include the category
   counts, the total deck price, the target bracket, and a short "how the deck wins" paragraph.
2. **A plain importable list** (`<commander>-import.txt`) — one card per line as `1 Card Name`, ready to
   paste into Moxfield / Archidekt / mtggoldfish. Put the commander on its own first line.

Use the `present_files` tool to share both, and **save them in their own folder under
`.mtg/decks/`** in the user's current working directory: `.mtg/decks/<deck-slug>/deck.md` and
`.mtg/decks/<deck-slug>/import.txt`. Create the folder if it doesn't exist. The slug is the
commander name (lowercase, spaces→hyphens, punctuation dropped), e.g.
`.mtg/decks/atraxa-praetors-voice/`. If the user already has a folder for that commander and wants a
different build, add a short distinguishing suffix (e.g. `atraxa-praetors-voice-superfriends`) so
existing decks aren't overwritten. See "The `.mtg` workspace" below.

## The `.mtg` workspace

All of this skill's file I/O lives in a `.mtg/` directory in the user's current working directory.
It is conventionally git-ignored (built output and personal collection data, not source):

- **`.mtg/decks/`** — where built decks are written. **Each deck gets its own subfolder**,
  `.mtg/decks/<deck-slug>/`, holding that deck's two deliverable files (`deck.md` and `import.txt`).
  Create the directories if they're missing.
- **`.mtg/collection/`** — where the user's **existing card collection** lives (the cards they
  already own), so decks can be built from — or biased toward — what they have. At the **start of a
  build, check whether `.mtg/collection/` exists and holds a collection file** (a Moxfield /
  Archidekt / MTGGoldfish CSV export, or a plain `1 Card Name` text list). If it does, read it and:
  prefer cards the user already owns when two choices are otherwise close, and in the annotated
  decklist flag which cards they still need to buy and the cost of just those. If it's absent or
  empty, build normally and let the user know they can drop a collection export into
  `.mtg/collection/` to get collection-aware builds next time.

## Before you build: always confirm bracket and budget

Two parameters change almost every card choice, so confirm them up front (the user has asked that you
always ask, unless they already stated both):

- **Power bracket (1–5)** — the official Commander power framework. This governs how efficient the
  interaction is, how many (if any) Game Changers are allowed, and whether fast/infinite combos are okay.
  See `references/brackets.md` for the definitions and how to enforce them. Default to **Bracket 2–3** if
  the user is unsure.
- **Budget cap** — a total deck budget in EUR (Cardmarket pricing), or "no cap". This decides whether you
  reach for staples or for budget substitutes, and it constrains the land base most of all.

If the commander is also unknown ("just build me something fun"), help them pick one first using Step 1.

## The seven steps

Work through these in order. Steps 2 and 6 carry the most weight — the synergy-finding in Step 2 is what
makes the deck *yours*, and the cutting in Step 6 is what makes it *function*. Full detail, rubrics, and
the reasoning behind every number live in `references/methodology.md`; read it before building. The
Scryfall query cookbook for each step is in `references/scryfall-syntax.md`.

### Step 1 — Pick / confirm the commander
The commander defines the deck's **color identity** (the only colors allowed in the 99) and its core
engine. If the user already named one, confirm its color identity and read its abilities closely. If they
haven't, offer a few options by the "rule of cool" (most fun / coolest, per the user's taste) tempered by
"don't pick something oppressive that stops others playing." Pull the exact card text from Scryfall so you
are working from the real Oracle wording.

### Step 2 — Find the themed cards (the synergy engine)
Break the commander's text into **keywords** (e.g. "enters", "attacks", "sacrifice a creature",
"+1/+1 counter", "leaves the battlefield"). The deck wants cards that share **multiple overlapping
synergies** with the commander — not one synergy, several — and that also synergize **with each other**.
A good test: *could this deck win without ever casting the commander?* If yes, the 99 are pulling their
weight.

Source the candidates **primarily from EDHREC and mtgdecks.net** for this commander (this is what real,
winning lists run), then use **Scryfall to fill gaps** the proven lists miss and to surface budget or
bracket-appropriate alternatives. Gather ~40 themed candidates; you'll cut later. Apply the mana-value
rubric in `references/methodology.md` as a first filter (expensive cards must earn their slot).

### Step 3 — Card advantage (the hidden engine)
Dedicate **12+ cards** to *net-positive* card advantage — cards that replace themselves **and** draw more
(a card that draws 2 then discards 2 is **not** advantage). Aim ~8 of these at MV ≤ 3 and ~4 at MV ≥ 4,
with the expensive ones drawing explosively (5–6+ cards). Prefer pieces that also synergize with the
theme. Getting this right is the single biggest predictor of whether the deck works.

### Step 4 — Ramp
Include **~10–11 efficient ramp pieces** (mana rocks, mana dorks, land tutors) — cheaper is better — plus
a few **"explosive ramp"** pieces (mana doublers, rituals, treasure makers) to close games. Add more ramp
if the commander or curve is expensive, or if targeting a higher bracket.

### Step 5 — Interaction
Include **~10 dedicated interaction pieces** (removal, counterspells, protection) plus **2–4 board wipes**.
If the deck already has incidental interaction in its theme cards, trim the dedicated count by 1–2. Higher
brackets need more, and more *efficient*, interaction; lower brackets can run more synergistic/situational
pieces.

### Step 6 — Lands, then cut to 100
Run **~37–38 lands** — missing land drops loses games, so do not skimp. Mono-color decks lean on basics
plus colorless utility lands; multicolor decks need a majority of color-fixing lands and still need ~38.
Then **tally every category** and cut the themed pile down so the whole deck is exactly 100. Cut by
**curve first** (keep only 3–4 truly expensive cards) and **affinity second** (when torn between two cards,
keep the one with more synergy with the rest of the deck).

### Step 7 — Goldfish and lock in win conditions
Mentally "goldfish" the deck to ~turn 7 (play it out solo) and ask: *with a typical board, could this deck
actually win?* Ensure **3–4 real win conditions** — cards that, with the deck's normal board state, very
likely close the game. If a win con is missing, use Scryfall (search the commander's payoff keywords:
power, "loses life", artifact, etc.) to find the perfect closer and swap it in. Iterate until the deck has
a clear, repeatable path to victory.

## How to drive the data sources

The user wants **EDHREC + mtgdecks.net as the backbone** (proven inclusions) and **Scryfall to fill gaps
and price everything**. Concretely:

1. **EDHREC** — get the commander's top cards and high-synergy cards. Page URL pattern:
   `https://edhrec.com/commanders/<commander-slug>` (slug = lowercase, spaces→hyphens, drop punctuation,
   e.g. *Atraxa, Praetors' Voice* → `atraxa-praetors-voice`). The JSON endpoint
   `https://json.edhrec.com/pages/commanders/<slug>.json` is easier to parse when reachable. EDHREC also
   has theme/budget pages (e.g. `.../<slug>/budget`) useful under a cap.
2. **mtgdecks.net** — sample full decklists for the commander to see complete, coherent 100s and common
   land bases: `https://mtgdecks.net/Commander` then the commander's page.
3. **Scryfall** — the workhorse for filling category gaps, enforcing color identity, filtering by mana
   value, finding cards by oracle text, and **pricing**. Every Scryfall card object carries
   `prices.eur` and `prices.eur_foil`, which are **Cardmarket** prices in euros — use `prices.eur` as the
   per-card price for the deck total and for budget trimming. The query cookbook
   (`references/scryfall-syntax.md`) gives ready-made searches for each step.

**Retrieval mechanics — use whatever is available, in this order of preference:**

- **Code execution with network access** → run the bundled helper:
  `python scripts/scryfall_search.py "<query>" --limit 30`. It handles pagination, rate limiting, color
  identity, and prints each card's name, mana value, type, and EUR price as JSON or a table. This is the
  fastest, most reliable path. Run `python scripts/scryfall_search.py --help` for options. The script also
  fetches a single card's full details and price with `--named "Sol Ring"`.
- **No code-execution network, but web tools available** → use `web_search` to surface the relevant
  Scryfall search page, EDHREC page, or mtgdecks list, then `web_fetch` the result. `web_fetch` only
  accepts URLs returned by a prior search, so search first (e.g. search `scryfall id<=WB function:ramp`),
  then fetch the page that comes back.
- If neither has network to these domains, tell the user their environment needs network access to
  `api.scryfall.com`, `edhrec.com`, and `mtgdecks.net` (in Claude.ai/Code this may need enabling in
  settings, or an org owner may need to allow those domains), and offer to proceed from your own MTG
  knowledge with the caveat that prices and the latest cards won't be verified.

Respect Scryfall's etiquette: small delay between calls (the script does this), and prefer one well-formed
query over many redundant ones.

## Putting it together — the target shape of a 100-card deck

Categories overlap (a treasure-making rock is ramp *and* sac fodder); count each card by its **primary**
role so the totals add to 100. A typical balanced build:

| Category | Count |
|---|---|
| Commander | 1 |
| Lands | 37–38 |
| Ramp | 10–12 |
| Card advantage (draw) | 12–13 |
| Interaction (incl. 2–4 board wipes) | 10–12 |
| Themed / synergy / payoffs / win conditions | remainder (~24–28) |

Adjust within these ranges for the commander and bracket, but treat large deviations (e.g. 30 lands, or 6
pieces of card advantage) as red flags to fix, not features.

## Budget and pricing

- Price every non-basic card with its Scryfall `prices.eur` (Cardmarket, EUR). Basics are free. Sum for
  the deck total and show it in the annotated file.
- If a budget cap is set and the draft list exceeds it, trim from the most expensive cards that are
  **not** load-bearing, and use Scryfall to find cheaper cards with the same role/synergy (e.g. swap an
  expensive dual land for a tapland or basic; swap a premium board wipe for a budget one). The land base
  is usually where the most money hides, so look there first.
- Note honestly that `prices.eur` is Cardmarket market price and can move; for an exact Cardmarket
  *average sell* on a specific pricey card, the user can check that card's Cardmarket page directly.

## Quality bar before you hand it over

**Reconcile the two files first.** Build the annotated list, then generate the import list *from it* —
don't assemble them independently, or they drift (e.g. a card you cut for bracket reasons sneaks back into
the import list). Before presenting, verify the import list sums to exactly 100 and contains the same
cards as the annotated list. A one-line check works:
`awk '{s+=$1} END{print s}' <import>.txt` must print `100`, and
`sed 's/^[0-9]* //' <import>.txt | sort | uniq -d` must print nothing (no duplicate names; Commander is
singleton). This catches the most common failure mode: a popular card you deliberately excluded (a Game
Changer, or a combo piece above the bracket) reappearing in the import list.

Then re-read `references/methodology.md` and confirm: exactly 100 cards including the commander; ~38 lands;
≥12 net-positive card-advantage pieces; ≥10 ramp; ~10 interaction + 2–4 wipes; 3–4 real win conditions;
every card legal in the commander's color identity; bracket rules satisfied (Game Changer count, combo
restrictions — see `references/brackets.md`); within budget if a cap was set. Only then present the files.
