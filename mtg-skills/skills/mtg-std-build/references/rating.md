# The Star Rating Rubric — Standard (MTG Arena)

This is the explicit, repeatable rubric for star-rating a 60-card Standard deck, so a "★★★★☆" means the same
thing every time. Standard has no Commander brackets, Game Changers, or EDHREC staple ranks — so unlike the
EDH rubric, the benchmark here is **the current ladder meta and the deck's wildcard tier and match type**.
Five stars means "an excellent deck *for the current ladder at this tier*", judged on whether it can actually
win games on the ladder it's built for — not raw card power in a vacuum. A clean budget Tier-2 aggro deck and
a polished Tier-5 control deck can both earn ★★★★★ at their own level.

Use **half-stars** (e.g. ★★★½). Score each of the five dimensions 1–5, then combine by the weights below.

---

## The five dimensions

### 1. Consistency & curve — *weight 30%* (does it do its thing every game?)

Does the deck execute its plan reliably? Check: the **mana curve matches the archetype's speed**, key cards
are **4-ofs** (or close), the core plan has **redundancy** (multiple copies/effects so it shows up most
games), and the **land count fits the speed** — ~16–18 for hyper-aggro, ~23–24 for midrange, ~25–26 for
control. A deck that does its thing turn 3 every game beats one with a higher ceiling and a shaky floor.

Scoring guide: **5** = tight curve, redundant core, right land count, draws its plan consistently. **3** = one
real consistency issue (clunky curve, too many 1-ofs, slightly off land count). **1** = inconsistent pile that
rarely assembles its plan.

### 2. Mana base — *weight 20%* (the quiet game-loser)

Does the fixing match the deck's colors **and** speed? Aggro wants lands that enter **untapped** early (fast
lands, pain lands) and pays little tempo tax; control/midrange can afford some taplands and wants **utility
lands** (creature-lands, value lands). More colors = harder mana; the fixing must keep pace. Too many
taplands in an aggro deck, or too little fixing for a three-color deck, costs games.

Scoring guide: **5** = fixing matched to colors and speed, minimal tempo loss. **3** = workable but with a
real wart (a couple of taplands an aggro deck hates, or thin fixing). **1** = the mana actively fights the
game plan.

### 3. Synergy / payoff density — *weight 20%*

Run the method in `references/synergy.md`. For a **synergy/payoff** deck, score how many payoff cards give a
real **2-for-1 with the plan and 2–3 points of contact** with the rest of the deck, and whether the pieces
reinforce each other. For a **pure aggro/efficiency or "good-stuff" midrange** deck where synergy is
deliberately light, judge instead whether every card **pulls toward one coherent plan** (no anti-synergy, no
filler) — such a deck can still score well here by being focused, even if it isn't combo-synergistic.

Scoring guide: **5** = a tight synergy web, or a perfectly focused aggro/tempo plan with zero filler. **3** = a
theme plus some off-plan cards. **1** = a pile of unrelated cards pulling different directions.

### 4. Meta resilience — *weight 20%* (can it survive the ladder?)

The deck must beat the **current field**, not just goldfish. Using the current meta (from your own
knowledge — no bot-fetchable meta source; never scrape untapped.gg/mtggoldfish, see
`references/data-sources.md`), check it has real **answers for the top 2–3 ladder decks**: cheap removal/sweepers and lifegain
vs. aggro, card advantage vs. midrange/discard, sweepers/enchantment removal vs. go-wide, graveyard hate vs.
reanimator. For **BO3**, the **15-card sideboard** must turn the bad matchups around. Answers should not
actively hurt the deck's own plan (a clean wrath for a tokens deck, not one that catches its own board).

Scoring guide: **5** = answers (and a sideboard, in BO3) for the whole top field, well-matched to its plan.
**3** = covers some matchups, soft to one major meta deck. **1** = no real interaction; folds to the field.

### 5. Wildcard efficiency — *weight 10%* (is the power well spent?)

Does the deck make good use of its **wildcard tier** (`references/wildcard-budget.md`)? Reward decks that hit
their goal **within tier**, lean on **owned cards**, and don't burn rares/mythics on marginal upgrades when a
common/uncommon does the job. This rewards smart, affordable building, not just expensive cards.

Scoring guide: **5** = strong deck at or under tier, efficient rarity spend, owned-cards-first. **3** = a
little over-spent for the gain. **1** = badly over the tier, or premium cards wasted on marginal slots.

---

## Combining into the overall score

`overall = 0.30·consistency + 0.20·manabase + 0.20·synergy + 0.20·meta + 0.10·wildcard`

Round to the nearest half-star. Then apply the **gates** (a strong average can't hide a deck that loses
games):

- Any dimension at **1** caps the overall at **★★★ (3)** until fixed.
- A **mana base that fights the plan** (wrong land count for the speed, or fixing that can't cast the deck)
  caps the overall at **★★½** — these lose games regardless of how good the spells are.
- A deck **over its wildcard tier** is rated for what it is, but the report must state the overage and the
  in-tier rating it *would* earn.

Translate the final number to words: **★ "needs work" · ★★ "rough" · ★★★ "solid/functional" · ★★★★ "strong
on the ladder" · ★★★★★ "excellent for its tier".**

---

## The report (embed it in deck.md)

1. **Headline:** `★★★★☆ (4/5) — a strong Tier-3 BO1 ladder deck.`
2. **Scorecard:** the five dimensions, each with its stars and the **numbers/reasons behind it** (e.g.
   "Consistency ★★★★ — 17 lands, low curve, 4-of core; Mana ★★★ — two taplands the aggro plan dislikes").
3. **Top strengths** (2–3) and **biggest weaknesses** (2–3), each concrete and tied to a dimension.
4. **Highest-impact fixes:** the 3–5 changes (cheapest in wildcards first) that would raise the score most —
   and offer to hand off to **mtg-std-upgrade** to make them.

Be honest and specific. "Soft to mono-red — wants two more cheap removal spells or a sweeper" beats "could be
better". The value of the rating is that it points at exactly what to fix.
