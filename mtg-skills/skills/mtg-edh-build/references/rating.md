# The Star Rating Rubric (strict, evidence-based)

This is the explicit, repeatable rubric the analyzer scores against, so a "★★★★☆" means the same thing every
time instead of being a vibe. Two hard principles keep it **honest and harsh**:

1. **Stars are relative to the deck's bracket, but the bar is high.** Five stars means *"matches or beats the
   comparable proven top lists for this commander at this bracket"* — **not** "it works." A deck that merely
   **functions** (legal, castable, has a coherent plan, no glaring holes) is **★★★ (3) — solid**, not four.
   **Reserve ★★★★–★★★★★ for decks shown by data to be at or above the comparable lists**, proven with
   evidence, not interpretation. A tuned Bracket 2 deck and a razor-sharp Bracket 4 deck can both earn five
   stars — but only by clearing the comparison bar at their own bracket.
2. **Score against comparison data, not opinion — and round DOWN when evidence is thin.** Staples and Synergy
   especially are scored against **actual evidence**: EDHREC inclusion rates / ranks and the comparable real
   decklists pulled for this commander (the build skill's "comparable decks" step; see `data-sources.md`).
   **When the evidence is thin, or you couldn't pull comparables, default to the LOWER score** — never round
   up on a hunch. "I think this is good" is not evidence.

Always report the overall stars **and** the deck's **actual bracket** (`brackets.md`, the determination
logic). If the user named a target bracket that differs from the actual one, say so plainly.

Use **half-stars** (e.g. ★★★½). Score each of the five dimensions 1–5, combine by the weights below, then
apply the gates.

---

## The five dimensions

### 1. Structure & consistency — *weight 30%* (the performance fundamentals)

Does the deck have the shape that actually wins games? Tally each category (read Oracle text to classify; use
`function:` tags to help) and compare to the target shape for a 100-card deck:

| Category | Target |
|---|---|
| Lands | ~37–38 (36 ok with a low curve + cheap draw) |
| Ramp | ~10–11 (+ a few explosive) |
| Card advantage (net-positive) | **≥12** (a rummage/loot is *not* advantage) |
| Interaction | ~10 dedicated **+ 2–4 board wipes** |
| Curve | only **3–4** cards at MV 6+; sensible average MV |

Scoring guide (strict): **3** = every category is *roughly* on target and the deck functions — this is the
default for a competent, unremarkable build. **4** = on target **and** measurably tighter than the comparable
lists (better curve, more efficient ramp/draw, no wasted slots). **5** = textbook structure that matches or
beats the best comparable lists. **2** = one serious miss (e.g. 33 lands, or 7 pieces of draw). **1** =
structurally broken (e.g. 30 lands and no card advantage). Scale interaction expectations up with bracket
(B4–5 want more, cheaper answers). **A deck only "having the right counts" earns a 3, not a 4.**

### 2. Synergy density — *weight 25%* (does the machine cohere?)

Run the method in `references/synergy.md`. For each **non-structural** card (exclude lands and generic
ramp/removal staples), count its **points of contact** with the commander/engine and the rest of the deck.
Look at: what fraction of themed cards clear the **≥2–3 points of contact** bar, the average contact count,
and whether multiple engines reinforce each other. **Cross-check against the comparable lists**: do the
proven lists run a denser, more cohesive engine than this deck?

Scoring guide (strict): **3** = a real theme is present but with a noticeable "goodstuff" tax (several cards
touching little) — typical of a deck that "works." **4** = mostly cohesive, few one-note inclusions, and as
dense as the comparable lists. **5** = nearly every themed card pulls 2–3+ jobs, reinforcing engines, the deck
would function even without the commander, and it is *denser* than the comparables. **2** = a loose pile with
occasional synergy. **1** = 99 unrelated good cards. *Name the high-contact stars and the zero-contact
passengers.* **If you can't measure synergy against comparables, cap this at 3.**

### 3. Staples & card quality — *weight 20%* (is it running the right cards, by the data?)

Score against **actual comparison data**, not taste: the EDHREC-rank signal from `analyze_deck.py` (premier
≤500 / staple ≤1500 / played ≤4000 counts, median rank, unranked count) **and**, where available, the
**inclusion rates** of the cards in the comparable lists for this commander. The question is concrete: *does
this deck run the high-inclusion, format- and color-defining pieces its strategy wants, at the rate the proven
lists do — and what high-inclusion cards is it missing?* Check omissions with Scryfall (`function:ramp
id<=<colors>`, `function:removal …`, `is:gamechanger id<=<colors>`).

Scoring guide (strict, **scaled to bracket**): **3** = runs most of the obvious staples but misses several
high-inclusion cards, or leans on low-inclusion picks without a synergy reason. **4** = runs nearly all the
high-inclusion staples its plan wants, omissions are deliberate and justified. **5** = staple coverage matches
or beats the comparable top lists. Penalize **missing fundamentals** (no Sol Ring / no ramp / no real removal)
hard at any bracket. At **B1–2** thematic mid-rank cards are fine; at **B3–5** the bar rises. **A high
*unranked* count is a red flag unless each such card has a named synergy reason — when in doubt, score lower.**

### 4. Win conditions & closing power — *weight 15%*

Are there **3–4 real, repeatable** ways to close — finishers that win from the deck's *normal* board, not a
dream scenario — and are they resilient to one answer? Win-more cards (that only help when already winning)
don't count.

Scoring guide (strict): **3** = one clear, repeatable wincon (the deck *can* close, unremarkably). **4** =
multiple resilient, on-plan win cons, as reliable as the comparable lists. **5** = multiple resilient win cons
plus a faster/cleaner closing plan than the comparables. **2** = only fragile / win-more finishers. **1** = no
clear way to actually end the game.

### 5. Bracket calibration — *weight 10%, and a partial gate*

Determine the deck's **actual** bracket from the signals in `references/brackets.md` (Game Changer count, early
two-card combos, MLD, chained extra turns, fast mana + tutor density) — this is a hard determination, not a
vibe. Then compare to the **target** bracket the user named.

- **Actual == target** → score 5.
- **Actual < target** (deck is weaker than claimed; e.g. a "B3" deck that's really B2 — 0 Game Changers, no
  combos): this is the common, honest case. Report the real bracket, score this dimension by how close it is,
  and **do not inflate** the other dimensions to compensate.
- **Actual > target / violates the target** (e.g. 6 Game Changers in a "Bracket 2" deck, or an early infinite
  combo at B3): the deck is **mis-bracketed**. Report its *actual* bracket and **cap the overall** (see
  gates). A deck that breaks its own bracket's rules cannot be a great deck *at that bracket*.

Always include the **move-up / move-down** note from `brackets.md` here.

---

## Combining into the overall score

`overall = 0.30·structure + 0.25·synergy + 0.20·staples + 0.15·wincons + 0.10·bracket`

Round to the nearest half-star. Then apply the **gates** (a strong average can't hide a weak deck):

- **The "it just functions" ceiling.** If you cannot point to comparison data showing the deck **matches or
  beats** comparable lists at its bracket, the overall is **capped at ★★★ (3)** — a working deck is solid, not
  strong. Four-plus stars must be *earned with evidence.*
- Any dimension at **1** caps the overall at **★★★ (3)** until fixed.
- A **mis-bracketed** deck (dimension 5 violation) caps the overall at **★★★ (3)** *as the claimed bracket*,
  with the real bracket stated.
- A deck **missing a fundamental** (≤34 lands, or <8 card advantage, or essentially no interaction) caps the
  overall at **★★½** — these lose games regardless of how spicy the rest is.

Translate the final number to words: **★ "needs work" · ★★ "rough" · ★★★ "solid/functional" · ★★★★ "strong —
matches the proven lists" · ★★★★★ "excellent — at or above the best comparable lists for its bracket."**

---

## The report to hand back

1. **Headline:** `★★★½ (3.5/5) — a solid Bracket 2 deck.` Plus the **actual bracket** if it differs from the
   target, stated plainly (e.g. *"you targeted B3; as built it's B2"*).
2. **Scorecard:** the five dimensions, each with its stars and the **numbers/evidence behind it** (e.g.
   "Structure ★★★ — 37 lands, 11 ramp, 13 draw, 9 interaction + 3 wipes, curve fine — on target but not
   tighter than the comparable lists, so 3"). Show the analyzer's stats and any inclusion-rate comparisons.
3. **Top strengths** (2–3) and **biggest weaknesses** (2–3), each concrete and tied to a dimension and, where
   possible, to comparison data.
4. **Move-up / move-down note:** what would raise the deck one bracket and what would drop it (`brackets.md`).
5. **Highest-impact fixes:** the 3–5 changes that would raise the score most, cheapest-first — and offer to
   hand off to **mtg-edh-upgrade** to actually make them.

Be honest and specific, and **err toward the lower score when the evidence is thin.** "Card advantage is thin
(9, want 12+); EDHREC lists average 14 — add cheap repeatable draw" beats "could be better." The value of the
rating is that it points at exactly what to fix and refuses to flatter a deck that only functions.
