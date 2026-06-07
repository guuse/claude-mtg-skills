# Card-Finding Methodology — the diagnostic and the craft

This is the long version of what the SKILL.md summarizes. Read it before recommending cards. The skill has
two hard parts: **figuring out what the player actually needs** (the diagnostic) and **reading enough card
text to find the cards that genuinely cohere** (the craft). Everything below serves those two.

The north star: **the player should leave with cards they didn't know they needed, each of which earns its
slot by doing several things for the deck at once.** A list of individually "good" cards is a search engine's
job; finding the *cohesive* cards for *this* deck and *this* player is yours.

---

## Part 1 — Pin the purpose (Phase 1)

Five modes, and they ask for different things. Name the mode out loud so the user can correct you:

| Mode | What the user wants | Where the work is |
|---|---|---|
| **Find a commander** | A legend to build around, by vibe | Player profile → rule-of-cool candidates |
| **Fill a gap** | Best cards for a named hole (lands, ramp, wipes) | Category search within the deck's identity |
| **Add a category** | Best card advantage / removal / etc. in a color identity | Category search + curve/efficiency judgment |
| **Find synergy pieces** | Cards that combo/synergize with a theme or card | Deep Oracle-text + type research |
| **Solve a problem** | A symptom fixed ("can't close", "run out of cards") | Diagnosis first, then search |

Requests often blend modes (a problem turns into a category search). That's fine — name the pieces and order
them by impact. The only failure here is searching before you know which mode you're in.

---

## Part 2 — Brainstorm the context (Phase 2)

### Finding a commander: profile the player

You're matching a *person* to a play pattern, so ask about the person:

- **Playstyle axis.** Aggro (attack) ↔ control (answer) ↔ midrange (value) ↔ combo (assemble) ↔ political
  (deal). Go-wide (tokens/swarm) ↔ go-tall (one big threat). Proactive (do my thing) ↔ reactive (stop yours).
- **Joy and pain.** What past decks they loved and *why* (the "why" is the signal). What they find miserable
  — durdling, mana screw, getting archenemy'd, slow non-games, durdle-and-die. Don't recommend toward known
  pain.
- **Gimmick / theme.** A tribe, a mechanic (sacrifice, counters, lifegain, mill, spellslinger, reanimator,
  blink, artifacts, lands, voltron), an aesthetic, a beloved character. This is usually the seed.
- **Colors & complexity tolerance.** Preferred colors / count, and how much they mind a greedy 3–5c mana base.
- **Constraints.** Budget, bracket/table level (`brackets.md`), proven vs. off-meta, and hard "no"s (stax,
  MLD, infinite combo, oppressive lockouts).

Then propose **3–5 candidate commanders** by the **rule of cool** (most fun for *this* player), tempered by
**"don't pick something that stops the table playing."** For each: the exact Oracle text, what it would *play
like* turn to turn, its colors/budget/bracket fit, and one sentence on the deck it wants. Let the user react;
narrowing to the one that lights them up *is* the deliverable for this mode.

### Working on a deck: understand the machine, then the symptom

You cannot judge whether a card *coheres* without knowing what it's joining. Get, in order:

1. **The list or a faithful description.** Paste of the decklist, or commander + colors + archetype + game
   plan. Pull the commander's and any keystone card's **real Oracle text** from Scryfall — you'll mine it for
   keywords in Phase 3.
2. **The engine and win plan.** What the deck does on a good turn; how it actually wins today; what its
   nut-draw and its floor look like.
3. **The symptom, traced to a cause** (see the diagnostic playbook below).
4. **Constraints.** Color identity (hard), format/legality, budget (EUR), bracket, pet cards to keep, things
   already tried.

### The diagnostic playbook — symptom → likely real cause

**Players name solutions; you need causes.** Take the stated problem as a symptom and ask *when* and *against
what* it happens, then trace it. Common misreads:

- **"I can't close games."** Usually *not* "my finisher is too small." More often: runs out of gas before the
  kill (→ card advantage), can't push the last damage through (→ evasion/overrun/reach), or has no *repeatable*
  threat so one removal spell resets them (→ resilient/recursive win con). Ask what the board looks like the
  turn before they lose.
- **"I keep running out of cards."** Could be too little card advantage — but also too many one-shot effects,
  no engine, or simply dumping the hand too fast with no refuel. Distinguish *draw* from *net card advantage*
  (a rummage is not advantage). Ask if it's every game (consistency) or just grindy ones.
- **"I die to board wipes."** Rarely "I need more protection." Usually overcommitting into open mana, or no way
  to *rebuild* afterward. The fix is often post-wipe refuel (recursion, draw that doesn't need a board, a
  resilient threat) plus discipline — not just indestructible-granting.
- **"I flood / I screw."** Flood → too many lands or no mana sinks / card filtering; screw → too few lands, too
  few cheap plays, or a greedy curve. Look at land count and curve before adding "fixing".
- **"My deck is too slow."** Could be the curve (top-heavy), the mana (too many taplands), or the plan (no
  proactive early game). Ramp is one answer; a lower curve is often the better one.
- **"I lose to one specific deck/player."** A *matchup* problem, not a consistency problem — solve it with
  targeted interaction (hate cards, the right removal type) rather than rebuilding the engine.
- **"I need more removal."** Sometimes true. Often the deck has enough removal but the *wrong kind* (sorcery
  vs. instant, creature-only vs. catch-all, single vs. mass) for what's actually killing them. Find out what
  they keep failing to answer.

**Reflect the diagnosis back as a one-sentence problem statement and get agreement before searching.** If your
read differs from their opening ask, say so plainly and let them choose the direction. This single step — need
vs. stated request — is the most valuable thing the skill does.

---

## Part 3 — Research the card pool deeply (Phase 3)

This is the craft. Two principles: **read the wording**, and **rank by cohesion**. The exact loop —
**read → extract → map to Scryfall tags → search → intersect → score**, with the hard **≥2–3 points of
contact per card** rule — lives in `references/synergy.md`; this section is how it plays out in a
finding session. **Map each extracted element to a Scryfall handle** (curated `function:`/`otag:` Tagger
tags first, then `o:"…"` oracle text, `t:…` types, `keyword:…`) and intersect the results — cards that
surface under several handles are the multi-synergy finds.

### Decompose the need into queries

- **Synergy/gap/category work:** break the commander and the deck's keystones into **keywords and type
  interactions** — every actionable concept in the text. A commander that says *"whenever a creature you
  control dies, draw a card; sacrifice a creature: +1/+1 counter"* yields: *creature dies, sacrifice a
  creature, draw, +1/+1 counter*, plus the type lines it cares about (creatures, tokens, fodder). Each becomes
  one query (`references/scryfall-syntax.md`).
- **Problem/category work:** translate the *cause* into mechanics. "Refuel after a wipe" → repeatable draw
  engines, recursion, draw that triggers off something you'll still have post-wipe (lands, an enchantment, the
  commander). "Push the last points" → evasion, trample, "can't block", extra combats, reach/burn finishers.

### Source proven first, then fill, then dig

1. **EDHREC** (Commander) — the commander's top cards and, crucially, its **high-"synergy"** cards: the ones
   that show up far more in *this* deck than in the color pie at large. That synergy ranking is a gift for this
   skill. Theme and budget pages help under a cap.
2. **mtgdecks.net** — full sample lists to see complete, coherent shells and what the proven decks lean on.
3. **Scryfall** — the workhorse for what the aggregates miss: fill keyword gaps, find budget/bracket swaps,
   and surface spicy multi-synergy cards buried below the popularity fold. For non-Commander formats, lean on
   Scryfall plus current meta sources.

### Read the text — this is the differentiator

For every serious candidate, **read the Oracle text and the type line**, not just the name. Use `--named "X"`
to pull exact wording. You are hunting for cards whose *text or type* makes them quietly perfect in ways a
name-level list never shows:

- a removal spell that **also draws** (interaction *and* card advantage in one slot);
- a ramp rock that's **also a sac outlet** or a treasure-maker the aristocrats deck wants;
- a creature whose **type** fills a tribal/typal slot *and* whose **text** triggers the engine;
- an enchantment that **re-triggers your ETBs**, **tracks your tokens**, *and* **draws** — three contacts.

### Rank by cohesion — points of contact

Score candidates by **how many ways they touch the deck and each other**, not by raw power. A card with three
points of contact (hits two of the deck's keywords *and* shares a type it cares about) beats a more powerful
island. Explicitly note the **combinations** you find — "this plus the card you already run does X" — because
the emergent interactions are the most valuable part of a recommendation and the hardest for the user to find
alone. A good gut check, borrowed from deckbuilding: *would this card still be doing real work if the deck's
marquee card weren't on the battlefield?* The best finds say yes.

### Sanity filters as you go

- **Color identity / legality.** Vet with `id<=<identity>` (NOT `c:`, which matches off-identity multicolor
  cards) and glance at the **CI** column — one off-identity pip makes a card illegal in a Commander deck.
  Respect the format's legality otherwise.
- **Mana value discipline.** Expensive cards must earn it (MV 6+ should swing the game the turn they land; MV
  1–3 should be repeatable engine pieces). Don't recommend a top-heavy pile.
- **Bracket / table fit.** Keep recommendations inside the user's stated power level and "no" list
  (`references/brackets.md`) — don't slip a Game Changer or an infinite combo into a Bracket 2 ask.
- **Price.** Every card carries `prices.eur` (Cardmarket EUR); show it, keep the picks under any cap, and note
  `null` prices rather than guessing.

---

## Part 4 — Present and refine (Phase 4)

Hand back a **shortlist (≈5–15 cards; a few commanders in commander mode)**, grouped by the need each serves,
**leading with the diagnosed real need**. Each line: name · MV · type · CI · EUR · a one-to-two-line reason
that names the *specific* synergy or fix (the points of contact). Add the trade-off where there is one
(fragile, slow, pricey, needs setup) and, where there's a genuine choice, offer **2–3 options** (budget vs.
premium, fast vs. resilient) instead of dictating one.

Then **stop and invite reaction.** Too expensive, already own it, want spicier or safer, want to go deeper on
one candidate or one synergy thread — adjust and re-query. The session is done when the user has the cards
they actually wanted, not when you've produced a list. If they want these turned into a full or upgraded deck,
hand the context to the relevant deckbuilding skill rather than building it here.

## Quality checklist (run before recommending)

- [ ] You named the **mode/purpose** and the user agreed.
- [ ] You traced the request to a **diagnosed need** and confirmed it (flagged any divergence from the ask).
- [ ] You **read the Oracle text / type line** of every serious candidate (`--named` for the close calls).
- [ ] Each pick's reason names a **concrete synergy or fix** with its **points of contact** — no vague praise.
- [ ] **Color identity & legality** vetted (`id<=`, CI column); **prices** shown; within **budget/bracket**.
- [ ] The output is a **focused, grouped shortlist** with trade-offs and real choices — and you invited
      refinement rather than calling it done.
