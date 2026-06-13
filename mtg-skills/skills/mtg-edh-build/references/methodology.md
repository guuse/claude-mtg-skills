# Deckbuilding Methodology — Detail and Reasoning

This is the full version of the process the SKILL.md summarizes. Read it before building. The numbers here
are guidelines tuned from experience, not laws — but deviating far from them usually breaks the deck, so
deviate deliberately and know why.

The single most important idea: **a Commander deck is a machine, not a top-99 list.** Cards earn their slot by
reinforcing the commander *and each other*. A useful north star — *could this deck win even if you never cast
your commander?* If yes, your 99 are synergizing properly and the deck is resilient to having its commander
removed.

The second idea, which governs *how* you choose cards and *how* you hit a budget: **build from comparable real
decklists, assemble a solid bracket-appropriate base ignoring budget, then budget down by role-preserving
swaps.** The rest of this file is those two ideas applied step by step.

---

## Phase A — Ground the build in comparable real decklists (do this FIRST)

Before you write a single card down, **pull the comparable proven decklists for this commander** and keep them
open as the build's backbone. This is what keeps the deck grounded in what actually wins instead of invention.

Pull (see `references/data-sources.md` for endpoints and `scripts/edhrec_fetch.py`):

- the **EDHREC average deck** (`--average`) — a literal ~100-card "what the typical list runs",
- the **top / staple + high-synergy cards** (default `edhrec_fetch.py "<commander>"`) — with their
  **inclusion rates and ranks**,
- the relevant **theme** page (`--theme <slug>`) and the **budget** page (`--budget`),
- **optionally** one or two top published lists via `scripts/import_deck.py <archidekt-or-moxfield-url>`.

**The rule for every inclusion from here on:** each card must be justified either by its **presence /
inclusion-rate in the comparable lists** *or* by a **clear, named synergy reason** (its points of contact —
`references/synergy.md`). "It seemed good" is not a justification. If EDHREC is unreachable, fall back to the
local Scryfall DB ordered by EDHREC rank, tell the user the proven-inclusion data is lower-confidence, and
lean harder on the explicit synergy justification.

---

## Step 1 — Pick / confirm the commander

The commander is the most impactful single choice because it sets two things:

- **Color identity** — the colors (W/U/B/R/G) in the commander's mana cost *or* rules text. Every other card
  must fit inside it. A mono-color commander unlocks tons of basics and colorless utility; a 3–5 color
  commander forces a fixing-heavy land base.
- **The engine** — what the deck *does* turn to turn to generate advantage and eventually win.

Two selection rules, in tension, both matter:
1. **Rule of cool** — pick what's genuinely fun for the user. Fun is the goal of the format.
2. **Don't be oppressive** — avoid commanders/strategies that stop opponents from playing (hard stax, heavy
   land destruction, fast non-interactive combo) unless the table wants that.

Always pull the commander's real Oracle text (Scryfall `--named`) so Step 2 works from exact wording.

---

## Step 2 — Find the themed cards (the synergy engine)

This is where decks are won or lost. It runs through the **synergy-scoring loop in `references/synergy.md`**
(read → extract → map to Scryfall tags → search → intersect → score), which enforces that **every themed card
share at least 2–3 points of contact** with the commander and the rest of the deck. The method below is that
loop applied to a build, **using the comparable lists from Phase A as the source pool.**

**A. Break the commander into keywords (extract its vocabulary).** Read each ability and extract every
actionable concept. Example — a commander that says *"Whenever this enters or attacks, you may sacrifice
another creature or artifact; if you do, put two +1/+1 counters on it,"* and *"When it leaves the battlefield,
put its counters on target creature you control,"* yields keywords: **enters, attacks, sacrifice creature,
sacrifice artifact, +1/+1 counters, leaves the battlefield, counters, target creature you control.** That's
the shopping list. **Map each to a Scryfall handle** — a curated Tagger tag (`otag:sacrifice-outlet`,
`otag:token-maker`, `function:card-advantage`) where one fits, otherwise `o:"…"` oracle text, `t:…` types, or
`keyword:…`.

**B. Hunt for multiple overlapping synergies (intersect and score).** Don't add a card because it hits *one*
keyword — thousands do. Add cards that hit **several** and that also play well with the other cards you're
adding. Search each handle and **intersect**: a card surfacing under multiple handles has multiple synergies.
Score each by its **points of contact** and **keep only those scoring ≥ 2–3**, densest first.

  *Example of multi-synergy:* an enchantment that (a) flickers a creature when it enters, (b) tracks your
  creatures entering with counters, and (c) periodically exiles-and-returns one of your creatures hits
  *enters*, *leaves the battlefield*, and re-trigger-your-ETB all at once — three points of contact.

  *(Structural slots — lands, generic ramp, catch-all interaction — fill required roles and are exempt from
  the 2–3 rule, but prefer the version that also synergizes; see `references/synergy.md`.)*

**C. Source from the comparable lists first, then fill.** Start from the Phase-A comparables — the average
deck, high-"synergy" cards, and theme list reflect what actually wins, and each carries an **inclusion rate**
you can cite. Then use **Scryfall** to (1) fill keyword gaps the popular lists underweight, (2) find
bracket-appropriate cards, and (3) discover spicy multi-synergy cards the aggregate data buries — but hold
those extras to the ≥2–3 contact bar.

**D. First-pass cut by the mana-value rubric.** Apply this as you gather:

- **MV 6+** — must *dramatically* change the board the turn it lands or give a near-insurmountable advantage
  within one turn. A dead 6-drop in hand is the worst feeling in the deck. No exceptions.
- **MV 5** — must provide a dramatic immediate advantage, or be a threat that runs away with the game in a few
  turns if unanswered.
- **MV 4** — must be powerful *and* highly synergistic.
- **MV 1–3** — should be repeatable **engine** pieces that keep giving value turn after turn.

Gather **more than you'll keep** (~40+ themed candidates) so the reference deck in Phase B has room. Also cut
anything that reads as "too rude" for the table/bracket.

---

## Step 3 — Card advantage (the hidden engine)

The most underrated lever. Three rules: **density, synergy, curve.**

**Density.** At least **12** cards dedicated to card advantage; strong decks often run 16–17.

**What counts.** Only *net-positive* advantage — a card must replace itself **and** draw at least one more.
*Faithless Looting* (draw 2, discard 2) is card *filtering*, not advantage; loot/rummage/impulse effects are
fine but don't count toward the 12.

**Synergy.** Prefer advantage that also ties into the theme (e.g. in a sacrifice deck, "draw a card whenever a
creature dies"). You extract value twice.

**Curve.** Of ~12 pieces, aim for **~8 at MV ≤ 3** and **~4 at MV ≥ 4**; the expensive ones must draw
**explosively** (5–6+ at once) to justify the cost.

---

## Step 4 — Ramp

**Normal ramp: ~10–11 pieces minimum** — mana rocks, mana dorks, land tutors/ramp. Bias toward **efficiency**
(a 1-MV rock beats a 2-MV rock beats a 3-MV rock, all else equal). Run more if the commander/curve is
expensive or the bracket is higher. Exceptions to "cheaper is better": a pricier piece with strong theme
synergy, or a deck that genuinely wants big mana.

**Explosive ramp: a few pieces** — doublers/triplers, rituals, mass treasure, free-cast enablers,
mass-land-into-play. Normal ramp carries the early game; explosive ramp helps close. For higher brackets, run
3–4 explosive pieces instead of 1–2. (Stacking fast mana is also a *bracket signal* — see `brackets.md`.)

---

## Step 5 — Interaction

Interaction is what stops you dying and stops opponents winning. More (and more efficient) interaction makes a
stronger deck — but *too much* makes games miserable, so balance to the bracket.

Four kinds: **removal** (destroy/exile a permanent), **interruption** (counterspells), **protection**
(hexproof, indestructible, fogs), **board wipes** (mass removal).

**Counts:** ~**10 dedicated** interaction pieces + **2–4 board wipes.** If the theme provides incidental
interaction, reduce the dedicated count by 1–2. Higher brackets → more and cheaper (instant-speed, free)
answers; lower brackets → more synergistic/situational interaction is fine.

---

## Step 6 — Lands, then cut to exactly 100

**Land count: ~37–38.** Missing land drops is devastating; hold the line at ~38 unless the deck has an
unusually low curve and lots of cheap draw/ramp, where 36–37 can be fine.

**Basics vs non-basics** depends on colors:
- **Mono-color:** mostly basics + a healthy package of **colorless utility lands**.
- **Two colors:** a fixing core (duals, taplands) + basics.
- **Three to five colors:** the **majority** of lands must be color-fixing; you still run ~38.

**Then cut to 100.** Tally every fixed category (commander + lands + ramp + card advantage + interaction),
subtract from 100 to learn how many **themed cards** survive, and cut by **curve first** (keep only 3–4 truly
expensive MV-6+ cards) and **affinity second** (when torn, keep the one with more synergy with the rest of the
deck).

---

## Step 7 — Goldfish and lock in win conditions

"Goldfish" the deck solo to ~**turn 7** making realistic plays, and ask: *with this typical board, could I
win?* and *is there a single card I could draw that wins from here?* If both are "not really," the deck lacks a
closer — find one with Scryfall (search the deck's payoff keywords in identity) and slot it in for the weakest
themed card. Keep going until the deck has **3–4 win conditions** resilient to one answer.

---

## Step 8 — Assemble the SOLID reference deck (ignore budget first)

Now commit the above into **one genuinely strong 100-card list for the target bracket, *ignoring budget
entirely***. This is the **reference deck** — the best honest version of the deck before money is a concern.

- **Allow a high ceiling.** If "solid" wants premium duals, the best rocks, and the strongest payoffs, include
  them — let the price run up (e.g. up to ~**€1000** if that's what a solid build of this commander costs).
  Don't pre-compromise; you can't budget down from a list you already weakened.
- **Keep it honest to the bracket.** The reference deck must obey the **target bracket's rules**
  (`brackets.md`): the Game-Changer cap (B1–2: 0, B3: ≤3), no early combos / MLD / chained extra turns below
  B4. A "solid B2 reference deck" is fully tuned *within B2's constraints* — it is not secretly a B3 deck.
- **Determine its ACTUAL bracket now** (`brackets.md` determination logic) and confirm it equals the target.
  If your "solid" build drifted above target (e.g. you slipped in a 4th Game Changer or an early combo), pull
  it back to target before proceeding — that's a bracket change, not a budget one.
- **Record the reference deck and its total price.** You will show it to the user as the pre-budget base.

If the user set **no budget cap**, the reference deck *is* the deliverable — skip to Step 10.

---

## Step 9 — Budget down from the reference deck (role-preserving swaps)

Only now bring in the budget cap. Reduce the reference deck to the user's budget by **iterating cards from
most expensive to least**, and for each, attempting a role-preserving swap:

1. **Sort the non-basic cards by price, descending.** Start at the top.
2. For the current expensive card, **find a cheaper card serving the SAME role/synergy** — same function, same
   color identity, comparable effect, and **ideally one that also appears in the comparable lists** from Phase
   A. (Land base is usually where the most money hides — premium duals → taplands/basics — so it yields the
   biggest savings first; then pricey rocks, payoffs, interaction.) Use `references/scryfall-syntax.md`:
   `function:<role> id<=<colors>` filtered by `usd<X`/`eur<X`.
3. **If an adequate cheaper substitute exists, swap it** (cut the expensive card → add the cheaper one) and
   **record the swap**: cut → add, both prices, and the **shared role/synergy** that makes them
   interchangeable. Re-check the category counts and the deck's actual bracket after each swap.
4. **If no adequate cheaper substitute exists** without weakening the deck's function or dropping it below the
   target bracket, **LEAVE that card and move to the next** most-expensive one. Do not swap in something that
   makes the deck worse just to hit a number.
5. **Repeat** down the price list **until the budget is met** or **no further beneficial swaps remain.**

**Each swap must preserve the deck's function and bracket.** A budget swap that quietly removes the deck's only
ramp, its only board wipe, or a card the bracket needs is not a valid swap — it's a downgrade. The point is the
*cheapest version that is still the same solid deck*, not the cheapest pile of cards.

### When the budget can't be met (the honest stop)

If you reach the bottom of the price list and **the deck still exceeds the budget while remaining solid at the
target bracket** — i.e. every remaining expensive card is load-bearing with no adequate cheaper substitute —
**STOP and tell the user plainly: it is not possible to build a solid Bracket-N deck for this commander at
that budget.** Then:

1. **Step DOWN one bracket** and **rebuild / re-evaluate the deck there** (a lower bracket has lower
   card-quality demands, so the cheaper substitutes that were "inadequate" at B3 may be perfectly fine at B2).
2. **Explain why** the original target wasn't reachable at that budget, and **what the lower bracket gets
   them** (and what it costs them — e.g. "no Game Changers, slower clock, but it's a genuinely good B2 deck at
   your budget").
3. Re-run Steps 8–9 at the lower bracket and report the result.

Never silently ship a deck that's weaker than the bracket claims just to fit a budget — report the trade-off
and let the user choose.

---

## Step 10 — Report the build honestly

Show the user, in this order:

1. **The reference (pre-budget) base** and its total price — the solid target-bracket deck before money.
2. **Every swap** made during budget-down: **cut `<card>` (€X) → add `<card>` (€Y)** with the **shared
   role/synergy**, grouped sensibly (lands, rocks, payoffs…), and the running spend.
3. **The final price** vs. the cap.
4. **The final ACTUAL bracket** (by the `brackets.md` determination — not just the target), with the Game
   Changer count and confirmation the combo/MLD/extra-turn limits hold.
5. **The "what's needed to go up one bracket" note** (and what would drop it), per `brackets.md`.
6. The **★ rating** (`references/rating.md`) — and remember a deck that merely *functions* is 3 stars; 4–5
   must be earned against the comparable lists.

---

## Sanity checklist (run before delivering)

- [ ] Build grounded in **comparable real decklists**; every inclusion justified by inclusion-rate or a named
      synergy reason.
- [ ] A **solid reference deck** was assembled ignoring budget, then **budgeted down** by role-preserving
      swaps (or budget couldn't be met → stepped down a bracket and said so).
- [ ] Exactly **100** cards including the commander.
- [ ] **~38** lands (36–38 acceptable; justify anything lower).
- [ ] **≥12** net-positive card-advantage pieces, ~8 cheap / ~4 expensive.
- [ ] **~10–11** ramp pieces + a few explosive; efficient curve.
- [ ] **~10** dedicated interaction + **2–4** board wipes.
- [ ] **3–4** genuine win conditions.
- [ ] Every **themed/synergy** card clears **≥2–3 points of contact** (structural utility exempt).
- [ ] Every card inside the commander's **color identity**.
- [ ] **Actual bracket** determined (`brackets.md`), equals the target (or the difference is stated), with the
      Game-Changer count and combo/MLD/extra-turn limits respected.
- [ ] **Move-up / move-down** note included.
- [ ] Within **budget** if a cap was set (or the honest stop was reported); reference base, swaps, and final
      price all shown.
- [ ] Curve sensible: only 3–4 cards at MV 6+.
