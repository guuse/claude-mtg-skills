# The Star Rating Rubric

This is the explicit, repeatable rubric the analyzer scores against, so a "★★★★☆" means the same thing
every time instead of being a vibe. **The rating is always *relative to the deck's target bracket*:** five
stars means "an excellent deck *for that bracket*", not "a cEDH deck". A tuned, coherent Bracket 2 deck and a
razor-sharp Bracket 4 deck can both earn five stars — at their own bracket. Always report the overall stars
**and** where the deck actually sits on the bracket scale (see `references/brackets.md`).

Use **half-stars** (e.g. ★★★½). Score each of the five dimensions 1–5, then combine by the weights below.

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

Scoring guide: **5** = every category on target, clean curve. **4** = one category slightly off. **3** = one
serious miss (e.g. 33 lands, or 7 pieces of draw) or two minor. **2** = two serious misses. **1** = the deck
is structurally broken (e.g. 30 lands and no card advantage). Scale interaction expectations up with bracket
(B4–5 want more, cheaper answers).

### 2. Synergy density — *weight 25%* (does the machine cohere?)

Run the method in `references/synergy.md`. For each **non-structural** card (exclude lands and generic
ramp/removal staples), count its **points of contact** with the commander/engine and the rest of the deck.
Look at: what fraction of themed cards clear the **≥2–3 points of contact** bar, the average contact count,
and whether multiple engines reinforce each other.

Scoring guide: **5** = nearly every themed card pulls 2–3+ jobs; clear reinforcing engines; the deck would
function even without the commander. **4** = mostly cohesive, a few one-note inclusions. **3** = a real theme
plus a noticeable "goodstuff" tax (several cards touching nothing). **2** = a loose pile with occasional
synergy. **1** = 99 unrelated good cards. *Name the high-contact stars and the zero-contact passengers.*

### 3. Staples & card quality — *weight 20%* (is it running the right cards?)

Use the EDHREC-rank signal from `analyze_deck.py` (premier ≤500 / staple ≤1500 / played ≤4000 counts, median
rank, unranked count) **plus judgment**: does the deck run the efficient, format- and color-defining pieces
its strategy wants (the right ramp rocks, premium removal, the on-theme payoffs), and is it missing obvious
ones? Check for glaring omissions with Scryfall (`function:ramp id<=<colors>`, `function:removal …`,
`is:gamechanger id<=<colors>`).

Scoring guide, **scaled to bracket**: at **B1–2**, staples matter less — a thematic, mid-rank deck can still
score 5. At **B3–5**, the bar rises: a 5 needs the deck to run the efficient staples its plan demands.
Penalize **missing fundamentals** (no Sol Ring/ramp, no real removal) hard at any bracket; a high *unranked*
count is fine if those cards are deliberate synergy picks, a red flag if they're just weak.

### 4. Win conditions & closing power — *weight 15%*

Are there **3–4 real, repeatable** ways to close — finishers that win from the deck's *normal* board, not a
dream scenario — and are they resilient to one answer? Win-more cards (that only help when already winning)
don't count.

Scoring guide: **5** = multiple resilient, on-plan win cons. **3** = one clear wincon, or several fragile
ones. **1** = no clear way to actually end the game.

### 5. Bracket calibration — *weight 10%, and a partial gate*

Compare the deck to its **target bracket** (`references/brackets.md`): Game Changer count vs. the cap (B1–2:
0, B3: ≤3, B4–5: unrestricted), early two-card infinite combos, mass land destruction, fast mana, heavy
tutoring.

- If the deck **fits** its target: score 5.
- If it's **under** the target (could be pushed up): note it; mild deduction only.
- If it **exceeds/violates** the target (e.g. 6 Game Changers in a "Bracket 2" deck, or an early infinite
  combo at B3): it is **mis-bracketed**. Report its *actual* bracket, and **cap the overall rating** — a deck
  that breaks its own bracket's rules cannot be a great deck *at that bracket*. Offer to re-rate it at the
  bracket it actually belongs to.

---

## Combining into the overall score

`overall = 0.30·structure + 0.25·synergy + 0.20·staples + 0.15·wincons + 0.10·bracket`

Round to the nearest half-star. Then apply the **gates** (a strong average can't hide a broken deck):

- Any dimension at **1** caps the overall at **★★★ (3)** until fixed.
- A **mis-bracketed** deck (dimension 5 violation) caps the overall at **★★★½** *as the claimed bracket*, with
  the real bracket stated.
- A deck **missing a fundamental** (≤34 lands, or <8 card advantage, or essentially no interaction) caps the
  overall at **★★½** — these lose games regardless of how spicy the rest is.

Translate the final number to words: **★ "needs work" · ★★ "rough" · ★★★ "solid/functional" · ★★★★ "strong" ·
★★★★★ "excellent for its bracket".**

---

## The report to hand back

1. **Headline:** `★★★★☆ (4/5) — a strong Bracket 3 deck.` Plus the **actual bracket** if it differs from the
   target.
2. **Scorecard:** the five dimensions, each with its stars and the **numbers behind it** (e.g. "Structure
   ★★★★ — 37 lands, 11 ramp, 13 draw, 9 interaction + 3 wipes, curve fine"). Show the analyzer's stats.
3. **Top strengths** (2–3) and **biggest weaknesses** (2–3), each concrete and tied to a dimension.
4. **Highest-impact fixes:** the 3–5 changes that would raise the score most, cheapest-first — and offer to
   hand off to **mtg-edh-upgrade** to actually make them.

Be honest and specific. "Card advantage is thin (9, want 12+); add cheap repeatable draw" beats "could be
better". The value of the rating is that it points at exactly what to fix.
