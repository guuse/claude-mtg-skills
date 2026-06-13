# Deckbuilding Methodology — Detail and Reasoning (upgrade)

This is the full version of the process the SKILL.md summarizes. Read it before diagnosing or upgrading. The
numbers here are guidelines tuned from experience, not laws — but deviating far from them usually breaks the
deck, so deviate deliberately and know why.

The single most important idea: **a Commander deck is a machine, not a top-99 list.** Cards earn their slot by
reinforcing the commander *and each other*. A useful north star — *could this deck win even if you never cast
your commander?* If yes, the 99 are synergizing properly and the deck is resilient to having its commander
removed.

For an upgrade, the second governing idea is: **diagnose against comparable real decklists, then make
role-preserving swaps that respect the budget and the deck's actual bracket.** An upgrade is not a rebuild — a
few well-chosen swaps often improve a deck far more than their cost suggests.

---

## Phase A — Ground the diagnosis in comparable real decklists (do this FIRST)

Before judging the deck, **pull the comparable proven decklists for this commander** and keep them open. They
are the benchmark the current list is measured against, and the source of upgrade candidates.

Pull (see `references/data-sources.md`, `scripts/edhrec_fetch.py`):

- the **EDHREC average deck** (`--average`),
- the **top / staple + high-synergy cards** (`edhrec_fetch.py "<commander>"`) with **inclusion rates / ranks**,
- the relevant **theme** (`--theme <slug>`) and **budget** (`--budget`) pages,
- **optionally** one or two top published lists via `scripts/import_deck.py <url>`.

**Every add must be justified** by its inclusion-rate in the comparables *or* a named synergy reason
(`references/synergy.md`). Every **gap** in the current deck is "the comparable lists run X, this one
doesn't." If EDHREC is unreachable, fall back to the local Scryfall DB by EDHREC rank, say the proven-inclusion
data is lower-confidence, and lean on explicit synergy justification.

---

## The target shape (what you diagnose against)

- **Step 1 — Commander.** Confirm the commander, its **color identity** (the only colors legal in the 99), and
  its engine; pull the real Oracle text (`--named`). Don't impose a new plan — sharpen the existing one unless
  the user asks to re-pivot.
- **Step 2 — Synergy engine.** Run the **synergy-scoring loop in `references/synergy.md`** (read → extract →
  map to Scryfall tags → search → intersect → score). Every *themed* card must clear **≥2–3 points of
  contact**; a one-note card is a cut candidate. (Structural slots — lands, generic ramp, catch-all
  interaction — are exempt, but prefer the version that also synergizes.)
- **Step 3 — Card advantage.** **≥12** net-positive pieces (replace themselves *and* draw more); ~8 at MV ≤ 3,
  ~4 at MV ≥ 4 drawing explosively. Loot/rummage doesn't count.
- **Step 4 — Ramp.** **~10–11** efficient pieces (rocks/dorks/land ramp), cheaper-is-better, + a few explosive.
- **Step 5 — Interaction.** **~10** dedicated + **2–4** board wipes; scale efficiency to the bracket.
- **Step 6 — Lands.** **~37–38** (36–37 only with a low curve + cheap draw); color-fixing majority in
  multicolor decks.
- **Step 7 — Win conditions.** **3–4** real, repeatable, resilient closers that win from a normal board.

The **mana-value rubric** still governs which cards earn slots: MV 6+ must dramatically swing the board the
turn it lands; MV 5 a dramatic immediate advantage; MV 4 powerful *and* synergistic; MV 1–3 repeatable engine
pieces.

---

## Step A — Diagnose: where is the deck below the comparable shape?

Tally the current list against the targets above and against the comparables' inclusion rates. Note the
**biggest gaps** — too few lands, thin card advantage, not enough/inefficient interaction, a top-heavy curve,
no clear closer, or low-inclusion filler where the proven lists run high-inclusion staples. Reconcile this
with what the user told you they struggle with, and **agree the top 2–3 priorities together** before proposing
cards. Their lived pain points outrank your tally where they conflict — but raise anything your tally surfaces
that they didn't mention.

## Step B — Determine the deck's ACTUAL bracket (before and after)

Using the determination logic in `references/brackets.md`, compute the bracket the **current** list actually
is — the **floor set by its most powerful signals** (Game Changer count, early two-card combos, MLD, chained
extra turns, fast mana + tutor density), not a vibe. A tuned, optimized deck with **0 Game Changers, no early
combo, no MLD** is **Bracket 2**, not 3 — don't inflate it. Compare to the user's **target** bracket and state
any difference plainly. After the swaps, recompute the actual bracket so the upgrade doesn't silently push the
deck past (or pull it below) where the user wants it.

## Step C — Choose adds, then role-preserving cuts

For each gap, gather candidates **from the comparable lists first**, then fill with Scryfall for budget- and
bracket-appropriate options (`references/scryfall-syntax.md`). Favor cards that fix a real weakness *and*
synergize. For every **add**, name the **cut**: the weakest card serving the same or a lower-priority role
(off-theme filler, an overcosted card the curve doesn't need, a win-more card, a strictly-worse duplicate).
Keep the deck at exactly **100**. Don't cut the user's flagged favorites unless they're clearly hurting the
deck — and if so, explain and offer the choice.

## Step D — Respect the budget by role-preserving substitution

Keep the running upgrade spend under the cap. When a high-impact add would blow the budget, **find a cheaper
card serving the SAME role/synergy** — same function, same color identity, comparable effect, ideally also
seen in the comparable lists (`function:<role> id<=<colors>` filtered by `eur<X`/`usd<X`). Record each swap as
**cut `<card>` (€X) → add `<card>` (€Y)** with the **shared role**. If no adequate cheaper substitute exists
without weakening the deck's function or bracket, **leave the current card and move to the next priority** —
don't swap in something worse just to spend the budget.

### When the target can't be reached within the budget (the honest stop)

If the upgrade budget **cannot** lift the deck to a solid version of the target bracket — every remaining
high-impact fix is load-bearing with no adequate cheaper substitute — **STOP and tell the user plainly.** Then
either propose a larger budget for the specific cards that would do it, or **target one bracket lower**,
explain why the original wasn't reachable at that spend, and re-evaluate there (a lower bracket's
card-quality demands are lower, so cheaper substitutes that were inadequate at B3 may be fine at B2). Never
silently ship an upgrade that claims a bracket the deck doesn't actually reach.

## Step E — Re-check and report

Re-check the category counts and the actual bracket after the swaps. Report: the **before → after** shape, the
**Changes** (cut → add, reason, €cost, running spend vs. cap), the **final actual bracket** with Game-Changer
count and combo/MLD/extra-turn confirmation, and the **move-up / move-down** note (`brackets.md`). Then the ★
rating before → after (`references/rating.md`) — remember a deck that merely *functions* is 3 stars; 4–5 must
be earned against the comparable lists.

---

## Sanity checklist (run before delivering)

- [ ] Diagnosis grounded in **comparable real decklists** (inclusion rates / ranks); gaps named against them.
- [ ] **Actual bracket** determined before and after (`brackets.md`); stated vs. the target; not inflated for
      being "tuned."
- [ ] Every add justified by inclusion-rate or a named synergy reason; every themed add clears **≥2–3 points
      of contact**.
- [ ] Budget respected by **role-preserving swaps** (or the honest stop / step-down was reported).
- [ ] Exactly **100** cards including the commander; cuts and adds net to zero.
- [ ] **~38** lands; **≥12** net-positive card advantage; **~10–11** ramp; **~10** interaction + **2–4** wipes;
      **3–4** win conditions; sensible curve (only 3–4 at MV 6+).
- [ ] Every card inside the commander's **color identity**.
- [ ] **Move-up / move-down** note included; ★ rating shown before → after.
