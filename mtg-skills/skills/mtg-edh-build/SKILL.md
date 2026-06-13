---
name: mtg-edh-build
description: >-
  Build a complete, balanced 100-card Magic the Gathering Commander (EDH) deck around a chosen commander.
  Use this skill whenever the user wants to build, brew, design, or upgrade a Commander/EDH deck, names a
  legendary creature and asks "build a deck around X", asks for a decklist for a commander, wants help
  picking cards that synergize with a commander, or wants a Commander deck within a budget or at a specific
  power bracket. Triggers on phrases like "build me a commander deck", "EDH deck for [commander]", "brew
  around [legendary creature]", "100-card singleton deck", "help me build my Atraxa deck", or any request
  that pairs a commander name with deckbuilding. The skill grounds the build in comparable proven decklists
  (EDHREC average/top/theme/budget pages, optionally top Archidekt/Moxfield lists), assembles a solid
  reference deck for the target bracket ignoring budget first, then budgets down by role-preserving swaps —
  prices everything via Scryfall (Cardmarket EUR), reports the deck's ACTUAL (strictly determined) bracket
  with a what's-needed-to-go-up note, and applies a disciplined methodology to produce a tuned list.
---

# MTG Commander Deck Builder

This skill builds a complete, well-tuned 100-card Commander deck around any commander the user
chooses. It combines two things: **proven card data** (what real players actually run, from EDHREC
via its JSON API, priced through Scryfall) and a **disciplined building methodology** that turns a
pile of synergistic cards into a deck that actually functions — correct card-advantage density, enough
ramp, enough interaction, the right land count, a sensible curve, and real win conditions.

A deck is not a list of the 99 most powerful cards in a color. It is a machine where the parts reinforce
each other. The whole job of this skill is to build that machine.

**The build is grounded in comparable real decklists, and the budget is hit by reduction, not by starting
cheap.** First pull the comparable proven lists for the commander and justify every inclusion by its
presence/inclusion-rate there or a clear synergy reason. Then assemble a **solid reference deck for the
target bracket *ignoring budget*** (allow a high ceiling — up to ~€1000 if that's what "solid" takes), and
only then **budget down** by swapping expensive cards, most-expensive-first, for cheaper cards that fill the
**same role/synergy**. If the budget can't be met while keeping the deck solid at the target bracket, say so
and step down a bracket rather than shipping a deck weaker than it claims. Full detail in
`references/methodology.md` — read it. Always report the deck's **actual** bracket (strictly determined per
`references/brackets.md`), not just the target.

**Build it with the user, not just for them.** After you've settled the commander and found the synergy
engine, check in on the **direction** before committing to a full 99, and present the near-final list for
reaction before writing files — invite them to swap pet cards in, push the power up or down, or change the
plan. Don't hand over a finished list as the first thing they see. Keep it light (this is a fresh build, so
fewer check-ins than an upgrade) but never one-shot: confirm the plan, then confirm the list.

## The deliverable

Always produce **two files** at the end (the user expects both):

1. **An annotated decklist** (`<commander>-deck.md`) — cards grouped by role (Commander, Lands, Ramp,
   Card Advantage, Interaction, Synergy/Themed, Win Conditions), each line showing the card name, mana
   value, a one-line reason it's in the deck (its inclusion-rate in the comparable lists or its synergy
   points of contact), and its Cardmarket price in EUR. Include the category counts, the total deck price,
   a short "how the deck wins" paragraph, and these **build-transparency** sections:
   - **Reference (pre-budget) base** — the solid target-bracket deck before budgeting, with its total price.
     (Omit only if the user set no budget cap.)
   - **Budget swaps** — every reduction as **cut `<card>` (€X) → add `<card>` (€Y)** with the shared
     role/synergy, plus the final price vs. the cap. (Omit if no cap.)
   - **Actual bracket** — the bracket the deck *actually is* by `references/brackets.md` (with the Game
     Changer count and combo/MLD/extra-turn confirmation), stated against the target if they differ, and a
     **"what's needed to go up one bracket" (and what would drop it)** note.
   - **Deck Rating** — an overall ★ rating at its bracket plus the per-dimension scorecard (see "Step 10").
2. **A plain importable list** (`<commander>-import.txt`) — one card per line as `1 Card Name`, ready to
   paste into Moxfield / Archidekt / mtggoldfish. Put the commander on its own first line.

Use the `present_files` tool to share both, and **save them in their own folder under
`.mtg/decks/edh/`** in the user's current working directory: `.mtg/decks/edh/<deck-slug>/deck.md` and
`.mtg/decks/edh/<deck-slug>/import.txt`. Create the folder if it doesn't exist. (Commander/EDH decks
live under `decks/edh/`; MTG Arena Standard decks live under `decks/std/`.) The slug is the
commander name (lowercase, spaces→hyphens, punctuation dropped), e.g.
`.mtg/decks/edh/atraxa-praetors-voice/`. If the user already has a folder for that commander and wants a
different build, add a short distinguishing suffix (e.g. `atraxa-praetors-voice-superfriends`) so
existing decks aren't overwritten. See "The `.mtg` workspace" below.

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

- **`.mtg/decks/`** — where built decks are written, **split by format**: Commander/EDH decks go
  under `.mtg/decks/edh/` and MTG Arena Standard decks under `.mtg/decks/std/`. **Each deck gets its
  own subfolder** — for this skill, `.mtg/decks/edh/<deck-slug>/`, holding that deck's two deliverable
  files (`deck.md` and `import.txt`). Create the directories if they're missing.
- **`.mtg/collection/`** — where the user's **existing card collection** lives (the cards they
  already own), so decks can be built from — or biased toward — what they have. At the **start of a
  build, check whether `.mtg/collection/` exists and holds a collection file** (a Moxfield /
  Archidekt / MTGGoldfish CSV export, or a plain `1 Card Name` text list). If it does, read it and:
  prefer cards the user already owns when two choices are otherwise close, and in the annotated
  decklist flag which cards they still need to buy and the cost of just those. If it's absent or
  empty, build normally and let the user know they can drop a collection export into
  `.mtg/collection/` to get collection-aware builds next time.

### Keeping decks in sync across machines (mtg-sync)

Decks live in the user's `mtg-data` git repo, and the user wants **every build to pull at the start
and push at the end** — the same way card data comes from mtg-db. **Don't try to judge whether
syncing is set up before acting — always run the sync commands and let the helper tell you.**
`sync.py` returns `skipped` when the workspace isn't a git repo, so an unconditional call is safe
everywhere; guessing whether to run it is exactly what makes pushing flaky.

- **At the start**, before reading the collection or writing anything, invoke **mtg-sync** to pull
  (`--pull`). This first brings down decks/collection built on another machine.
- **As the final action of the build** (see **Final step — always commit & push** at the end of this
  skill), invoke **mtg-sync** to push (`--push -m "<commander / archetype>"`), so the new deck lands
  on the repo's main branch and is available everywhere. This push runs **every time**, not only when
  you think sync is configured.

**Only the *result* is best-effort.** If the push reports `skipped` (syncing isn't set up) or
`FAILED` (e.g. offline), note it in one line and continue — the deck is saved locally and can be
pushed later. Never skip the *attempt*. To set syncing up the first time, use the **mtg-sync** skill
(`--bootstrap`).

## Before you build: always confirm bracket and budget

Two parameters change almost every card choice, so confirm them up front (the user has asked that you
always ask, unless they already stated both):

- **Power bracket (1–5)** — the official Commander power framework. This governs how efficient the
  interaction is, how many (if any) Game Changers are allowed, and whether fast/infinite combos are okay.
  See `references/brackets.md` for the definitions and the **strict determination logic**. Default to
  **Bracket 2–3** if the user is unsure. Note this is the **target**; you will report the deck's **actual**
  bracket at the end (and they can differ — a well-tuned deck with 0 Game Changers / no combos / no MLD is
  **Bracket 2**, not 3, however optimized it is).
- **Budget cap** — a total deck budget in EUR (Cardmarket pricing), or "no cap". This decides whether you
  reach for staples or for budget substitutes, and it constrains the land base most of all.

If the commander is also unknown ("just build me something fun"), help them pick one first using Step 1.

## The steps

Work through these in order. **Phase A first:** before Step 1, pull the **comparable proven decklists** for
the commander (EDHREC average/top/theme/budget via `scripts/edhrec_fetch.py`, optionally a top
Archidekt/Moxfield list) and keep them open — they are the build's backbone, and every inclusion is justified
by its inclusion-rate there or a clear synergy reason. Steps 2 and 6 carry the most weight, and **Step 8 (build
the solid reference deck, then budget down)** is what makes the price honest. Full detail, rubrics, and the
reasoning behind every number live in `references/methodology.md`; read it before building. The
**synergy-scoring loop that governs Step 2** (read → extract → map to tags → intersect → score, with the
≥2–3-points-of-contact rule) is in `references/synergy.md` — read it too. The Scryfall query cookbook for
each step is in `references/scryfall-syntax.md`.

### Step 1 — Pick / confirm the commander
The commander defines the deck's **color identity** (the only colors allowed in the 99) and its core
engine. If the user already named one, confirm its color identity and read its abilities closely. If they
haven't, offer a few options by the "rule of cool" (most fun / coolest, per the user's taste) tempered by
"don't pick something oppressive that stops others playing." Pull the exact card text from Scryfall so you
are working from the real Oracle wording.

### Step 2 — Find the themed cards (the synergy engine)
This is where the deck is won or lost, and it runs through the **synergy-scoring loop in
`references/synergy.md` — read it.** The rule it enforces: **every themed card must share at least 2–3
synergies ("points of contact") with the commander and ideally with the other cards — and the more, the
better.** A card with one point of contact is a cut candidate, not an engine card.

The loop, briefly: **(1) Read** the commander's exact Oracle text and type line (`--named`) — *you* decide
what matters. **(2) Extract** its key elements into a synergy vocabulary: triggers ("enters", "attacks", "a
creature dies", "leaves the battlefield"), actions ("sacrifice a creature", "+1/+1 counter", "create a
token", "draw"), the types it cares about, and keywords. **(3) Map** each element to a Scryfall handle —
curated **Tagger tags** `function:`/`otag:` for roles (`otag:sacrifice-outlet`, `function:card-advantage`,
`otag:token-maker`), `o:"…"` for specific phrases, `t:…` for types, `keyword:…` for keywords. **(4) Search**
each within the commander's identity and **intersect** — cards appearing under several handles are the
multi-synergy hits. **(5) Score** each candidate by its points of contact and keep the densest.

A good test of the result: *could this deck win without ever casting the commander?* If yes, the 99 are
pulling their weight. Source candidates **from the Phase-A comparable lists first** (`scripts/edhrec_fetch.py`
— the average deck, top, and high-"synergy" cards, each with an inclusion-rate you can cite), then use
**Scryfall to fill gaps** and surface spicy multi-synergy cards the aggregate buries (held to the ≥2–3 contact
bar). Gather **more than you'll keep** (~40+ themed candidates) so the reference deck has room; you'll cut
later. Apply the mana-value rubric in `references/methodology.md` as a first filter (expensive cards must earn
their slot).

**Check in on the direction here.** Before sinking time into the full build, tell the user the plan in a
couple of sentences — the theme/engine you're leaning into, how the deck intends to win, and a handful of
signature cards — and ask if that's the deck they want. This is the cheapest moment to change course (lean
more aggressive, swap the wincon, go budget, lean into a pet card). Adjust to their answer, then build.

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

### Step 8 — Assemble the solid reference deck (ignore budget), then budget down
What you have after Steps 1–7, with the **best** cards the comparables and synergy point to and **budget set
aside**, is the **reference deck** — the strongest honest version for the target bracket (allow a high
ceiling, up to ~€1000 if that's what solid takes). **Determine its actual bracket** (`references/brackets.md`)
and confirm it equals the target; pull back anything that drifted above (e.g. a 4th Game Changer or an early
combo) — that's a bracket fix, not a budget one.

Then, **only if a budget cap was set, budget down** (full algorithm in `references/methodology.md`): sort the
non-basics most-expensive-first and, for each, find a **cheaper card serving the same role/synergy** (same
function, color identity, comparable effect, ideally also in the comparable lists) and swap it — recording
**cut (€X) → add (€Y)** and the shared role, re-checking counts and bracket each time. If no adequate cheaper
substitute exists without weakening the deck's function or bracket, **leave that card and move on.** Repeat
until the budget is met or no beneficial swaps remain. **If the budget cannot be met while keeping the deck
solid at the target bracket, STOP, tell the user plainly, then step DOWN one bracket and rebuild/re-evaluate
there**, explaining why and what the lower bracket gets them. Keep the reference base and the swap log to show.

### Step 9 — Present the list and refine before writing files
**Show the user the finished list before you save anything** — including the **reference base, the budget
swaps, the final price, the actual bracket, and the move-up note**. Walk them through it briefly (category
counts, how it wins, the priciest cards, close calls) and invite changes: pet cards, cuts, more/less power, a
tighter budget. Make the swaps they ask for (re-checking counts, budget, and bracket each time) and keep going
until they're happy. **Only then** run the quality checks below, rank the deck (Step 10), and write the files.

### Step 10 — Rank the finished deck (★ rating)
Once the list is locked, **rate it before writing files** and embed the result in `deck.md`. Run
`python "${CLAUDE_SKILL_DIR}/scripts/analyze_deck.py" <import>.txt --commander "<name>" --json` on the final
list to pull the objective stats (curve, land/ramp/draw/interaction counts you can reconcile against your
build, the **EDHREC-rank staple signal**, Game Changer count, off-identity check, total EUR), then apply the
**five-dimension rubric in `references/rating.md`** — structure & consistency, synergy density (via
`references/synergy.md`), staples & card quality, win conditions, and bracket calibration — to award an
overall ★ rating *at the deck's actual bracket*. The rubric is **strict and evidence-based**: a deck that
merely *functions* is **★★★ (3)**, not 4, and **4–5 must be earned against the comparable lists** (score the
Staples and Synergy dimensions off the inclusion-rate / rank data from Phase A, and round **down** when the
evidence is thin). This is the same method as the dedicated **mtg-edh-analyze** skill; defer to it if you
prefer. Write a **Deck Rating** section into `deck.md`: the headline (e.g. `★★★½ (3.5/5) — a solid Bracket 2
deck`), the per-dimension scorecard with the numbers/evidence behind each, and one line on the deck's biggest
remaining weakness. Don't inflate the score because you built the deck — if it only rates 3, say 3 and name
what a comparable top list does better.

## How to drive the data sources

**EDHREC (JSON) is the backbone** for proven inclusions and **Scryfall** fills gaps and prices everything.
Full endpoint/fallback table: `references/data-sources.md`. Concretely:

1. **EDHREC JSON** — the authoritative "what comparable decks run" source. Use the bundled
   `scripts/edhrec_fetch.py "<commander>"` for staples, high-synergy cards, and the list of themes;
   `--average` for a literal ~100-card average decklist, `--theme <slug>` for a theme build, `--budget`
   for the budget list. It reads `https://json.edhrec.com/pages/commanders/<slug>.json` (slug = lowercase,
   drop `' , .`, other non-alphanumerics → `-`, e.g. *Atraxa, Praetors' Voice* → `atraxa-praetors-voice`)
   with a descriptive User-Agent + `Accept: application/json` and retry/backoff. **Never** fetch the
   Cloudflare-protected HTML at `edhrec.com`. If EDHREC 403s/404s, the script exits non-zero with a clear
   message — **fall back** to the local Scryfall DB ordered by EDHREC rank and tell the user the
   proven-inclusion data is lower-confidence.
2. **A user's existing decklist** — if they give an Archidekt or Moxfield link, run
   `scripts/import_deck.py <url>` to pull it via the site's JSON API (Archidekt `api/decks/<id>/`,
   Moxfield `api2.moxfield.com/v3/decks/all/<publicId>`). If the deck is private or the site errors, the
   script says so — ask the user to **paste** the list instead. Never invent a decklist.
3. **Scryfall** — the workhorse for filling category gaps, enforcing color identity, filtering by mana
   value, finding cards by oracle text, and **pricing**. Every Scryfall card object carries
   `prices.eur` and `prices.eur_foil`, which are **Cardmarket** prices in euros — use `prices.eur` as the
   per-card price for the deck total and for budget trimming. The query cookbook
   (`references/scryfall-syntax.md`) gives ready-made searches for each step.

**Scryfall reads come from the local card database.** The bundled `scripts/scryfall_search.py`
queries a **local SQLite database** (`.mtg/database/cards.sqlite`) built from Scryfall's bulk data
instead of hammering the API — see the **mtg-db** skill. The database is built
**automatically on first use** (a one-time ~540 MB download), so you don't need to run anything
first; just call the script. At the **start of a build**, if the script reports the data is **stale
(older than 30 days)**, tell the user prices may have moved and **ask** whether to refresh it (via
the mtg-db skill) before continuing — proceed either way. `function:`/`otag:` (Tagger)
tags aren't in bulk data, so those queries are routed to the live Scryfall API automatically.

**Retrieval mechanics — use whatever is available, in this order of preference:**

- **Code execution with network access** → run the bundled helper:
  `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" "<query>" --limit 30`. It reads the local database (auto-building
  it on first use), enforces color identity, and prints each card's name, mana value, type, and EUR
  price (cheapest printing) as JSON or a table. This is the fastest, most reliable path. Run
  `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --help` for options. The script also fetches a single card's full
  details and price with `--named "Sol Ring"`. `function:` queries transparently use the live API.
- **No code-execution network, but web tools available** → `web_fetch` the **JSON** endpoints directly
  (they parse cleanly and don't need scraping): `https://json.edhrec.com/pages/commanders/<slug>.json`
  for staples/themes, `.../average-decks/<slug>.json` for the average list, and the Scryfall search page
  for card data. If `web_fetch` needs a URL from a prior search, `web_search` for the Scryfall query or
  the EDHREC commander page first. (No database can be built without code execution — that's expected,
  this is the fallback.)
- If neither has network to these domains, tell the user their environment needs network access to
  `api.scryfall.com` and `json.edhrec.com` (in Claude.ai/Code this may need enabling in settings, or an
  org owner may need to allow those domains), and offer to proceed from your own MTG knowledge with the
  caveat that prices, proven inclusions, and the latest cards won't be verified.

Once the database exists, queries are local and fast; only `function:` tags and a stale-data refresh
touch the network. If there's no clear working directory to write the database to, prompt the user for
a path for `.mtg/` first (see "The `.mtg` workspace" above).

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
  the deck total and show it in the annotated file — for both the **reference base** and the **final** deck.
- **Hit a budget cap by reducing the reference deck, not by starting cheap** (Step 8 / `methodology.md`):
  iterate the non-basics most-expensive-first and swap each for a **cheaper card serving the same
  role/synergy** (same function, color identity, comparable effect, ideally also in the comparable lists).
  The land base is usually where the most money hides (premium duals → taplands/basics), so the top of the
  price list yields the biggest savings first. If no adequate cheaper substitute exists without weakening the
  deck, **leave that card** and move on. If the cap can't be met while keeping the deck solid at the target
  bracket, **stop and step down a bracket** rather than shipping a weaker deck under a higher label.
- Show **every swap** as **cut `<card>` (€X) → add `<card>` (€Y)** with the shared role, plus final price vs.
  cap.
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
every card legal in the commander's color identity; the deck's **actual bracket** determined per
`references/brackets.md` (Game Changer count + combo/MLD/extra-turn limits) and matching the target (or the
difference stated); the **reference base, budget swaps, final price, actual bracket, and move-up note** all
present; within budget if a cap was set (or the honest stop reported). Only then present the files.

**Double-check colors:** confirm every card's color identity is within the commander's — vet with
`id<=<identity>` (NOT `c:`, which also matches off-identity multicolor cards) and glance at the search
**CI** column for each card. A single off-identity pip makes the card illegal in the deck.

**Include the rating:** `deck.md` must carry the **Deck Rating** section from Step 10 — the overall ★ rating
at the bracket and the per-dimension scorecard. Don't deliver a deck without it.

## Final step — always commit & push (every build ends here)

This is the step that gets missed, so treat it as part of the deliverable, not an afterthought.
**After the two files are written and presented, the last thing you do — every single time — is push
them** by invoking the **mtg-sync** skill: `--push -m "<commander / archetype>"`.

Run it **unconditionally**. Do *not* first reason about whether the workspace is a synced repo — just
run it. The helper handles every case and reports back:

- **`ok` (committed + pushed)** → confirm in one line that the deck was pushed to the `mtg-data` repo's
  main branch.
- **`skipped`** → the workspace isn't a synced git repo; say so in one line and stop (offer
  `--bootstrap` via mtg-sync if they'd like syncing set up).
- **`FAILED`** → e.g. offline or an auth issue; say so in one line — the deck is committed/saved
  locally and can be pushed later.

Only the *handling of that result* is best-effort. The **attempt is mandatory** — never end a build
without running the push.
