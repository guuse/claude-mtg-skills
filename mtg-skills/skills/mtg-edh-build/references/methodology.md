# Deckbuilding Methodology — Detail and Reasoning

This is the full version of the 7-step process the SKILL.md summarizes. Read it before building. The
numbers here are guidelines tuned from experience, not laws — but deviating far from them usually breaks
the deck, so deviate deliberately and know why.

The single most important idea: **a Commander deck is a machine, not a top-99 list.** Cards earn their
slot by reinforcing the commander *and each other*. A useful north star — *could this deck win even if you
never cast your commander?* If the answer is yes, your 99 are synergizing properly and the deck is
resilient to having its commander removed.

---

## Step 1 — Pick / confirm the commander

The commander is the most impactful single choice because it sets two things:

- **Color identity** — the set of colors (W/U/B/R/G) appearing in the commander's mana cost *or* rules
  text. Every other card in the deck must fit inside that identity. A mono-color commander unlocks tons of
  basics and colorless utility; a 3–5 color commander forces a fixing-heavy land base.
- **The engine** — what the deck *does* turn to turn to generate advantage and eventually win.

Two selection rules, in tension, both matter:
1. **Rule of cool** — pick what's genuinely fun for the user (favorite character, art, play pattern). Fun
   is the actual goal of the format.
2. **Don't be oppressive** — avoid commanders/strategies that stop opponents from playing (hard stax,
   heavy land destruction, fast non-interactive combo) unless the table wants that. Oppressive decks get
   focused and you stop having fun too.

Always pull the commander's real Oracle text (Scryfall `--named`) so Step 2 works from exact wording.

---

## Step 2 — Find the themed cards (the synergy engine)

This is where decks are won or lost. It runs through the **synergy-scoring loop in `references/synergy.md`**
(read → extract → map to Scryfall tags → search → intersect → score), which enforces the rule that **every
themed card share at least 2–3 points of contact** with the commander and the rest of the deck. The method
below is that loop applied to a build:

**A. Break the commander into keywords (extract its vocabulary).** Read each ability and extract every
actionable concept. Example — a commander that says *"Whenever this enters or attacks, you may sacrifice
another creature or artifact; if you do, put two +1/+1 counters on it,"* and *"When it leaves the
battlefield, put its counters on target creature you control,"* yields keywords: **enters, attacks,
sacrifice creature, sacrifice artifact, +1/+1 counters, leaves the battlefield, counters, target creature
you control.** That's the shopping list. **Map each to a Scryfall handle** — a curated Tagger tag
(`otag:sacrifice-outlet`, `otag:token-maker`, `function:card-advantage`) where one fits, otherwise `o:"…"`
oracle text, `t:…` types, or `keyword:…` — so each keyword becomes a real query.

**B. Hunt for multiple overlapping synergies (intersect and score).** Don't add a card because it hits *one*
keyword — thousands do. Add cards that hit **several** and that also play well with other cards you're
adding. Search each handle and **intersect**: a card surfacing under multiple handles has multiple synergies.
Score each by its **points of contact** (+1 per vocabulary element it hits, +1 per other card it specifically
combos with) and **keep only those scoring ≥ 2–3**, densest first. The more points of contact a card has, the
more often it does something great, and the more the deck "comes alive" with emergent interactions.

  *Example of multi-synergy:* an enchantment that (a) flickers a creature when it enters, (b) tracks your
  creatures entering with counters, and (c) periodically exiles-and-returns one of your creatures hits
  *enters*, *leaves the battlefield*, and re-trigger-your-ETB all at once — three points of contact.

  *(Structural slots — lands, generic ramp, catch-all interaction — fill required roles and are exempt from
  the 2–3 rule, but prefer the version that also synergizes; see `references/synergy.md`.)*

**C. Source proven cards first, then fill.** Start from **EDHREC's JSON API** via `scripts/edhrec_fetch.py`
(top cards and high-"synergy" cards for this commander; `--average` for a full sample 100, `--theme`/`--budget`
for variants). These reflect what actually wins. (See `references/data-sources.md` — never scrape EDHREC's
HTML; on a 403/404 fall back to the local Scryfall DB ordered by EDHREC rank and say so.) Then use **Scryfall** to (1) fill keyword gaps the popular lists underweight, (2) find
budget/bracket-appropriate swaps, and (3) discover spicy multi-synergy cards the aggregate data buries.

**D. First-pass cut by the mana-value rubric.** Apply this as you gather (~40 candidates):

- **MV 6+** — must *dramatically* change the board the turn it lands or give an near-insurmountable
  advantage within one turn. A dead 6-drop in hand is the worst feeling in the deck. No exceptions.
- **MV 5** — must provide a dramatic immediate advantage, or be a threat that runs away with the game in a
  few turns if unanswered.
- **MV 4** — must be powerful *and* highly synergistic; a piece that shifts the deck into overdrive or
  sets up a huge next few turns.
- **MV 1–3** — should be repeatable **engine** pieces that keep giving value turn after turn, not just the
  turn they're cast.

Keep ~40 themed candidates after this pass. You will cut to fit in Step 6. Also cut anything that reads as
"too rude" for the table/bracket.

---

## Step 3 — Card advantage (the hidden engine)

The most underrated lever. Three rules: **density, synergy, curve.**

**Density.** At least **12** cards dedicated to card advantage; strong decks often run 16–17. "Dedicated"
means the card's job is to net you cards.

**What counts.** Only *net-positive* advantage. A card must replace itself **and** draw at least one more —
minimum +1 net, i.e. it sees you two cards. *Faithless Looting* (draw 2, discard 2) is card *filtering*,
not advantage; it puts you down a card. Loot/rummage/impulse effects are fine in the deck but don't count
toward the 12.

**Synergy.** Prefer advantage that also ties into the theme (e.g. in a sacrifice deck, "draw a card
whenever a creature dies"). You extract value twice and it's more fun to pilot.

**Curve.** Of ~12 pieces, aim for **~8 at MV ≤ 3** and **~4 at MV ≥ 4**. The cheap ones are steady drip
(draw 1–2, or "draw a card each turn"); the expensive ones must draw **explosively** (5–6+ at once) to
justify the cost. Card advantage keeps the deck flowing — you always have gas, answers, and options.

---

## Step 4 — Ramp

Ramp accelerates your mana beyond the one-land-per-turn baseline, letting you deploy bigger threats sooner.
Because Commander starts at 40 life, games run long and ramping early compounds hard — if opponents ramp
and you don't, you fall behind.

**Normal ramp: ~10–11 pieces minimum.** Three common kinds: **mana rocks** (artifacts), **mana dorks**
(creatures), **land tutors/ramp** (fetch lands to the battlefield). Bias toward **efficiency** — a 1-MV
rock beats a 2-MV rock beats a 3-MV rock, all else equal. Run more than 11 if the commander/curve is
expensive or the bracket is higher. Exceptions to "cheaper is better": a pricier piece with strong theme
synergy, or a deck that genuinely wants big mana.

**Explosive ramp: a few pieces.** Effects that *multiply* a turn's mana — doublers/triplers, rituals,
mass treasure, free-cast enablers, mass-land-into-play. Each color does this differently (green: dorks,
doublers, land floods; red: rituals/treasure; black: rituals, pay-life, special lands; blue: free-cast
enchantments; white: more setup-heavy but exists). Normal ramp carries the early game; explosive ramp
helps close. For higher brackets, run 3–4 explosive pieces instead of 1–2.

---

## Step 5 — Interaction

Interaction is what stops you from dying and stops opponents from winning. More (and more efficient)
interaction makes a stronger deck — but *too much* makes games miserable for everyone, so balance to the
bracket.

Four kinds:
- **Removal** — destroy/exile a permanent (e.g. exile a creature).
- **Interruption** — counterspells; stop something before it resolves.
- **Protection** — shield you or your key pieces (hexproof, indestructible, fogs).
- **Board wipes** — mass removal that resets the table.

**Counts:** ~**10 dedicated** interaction pieces + **2–4 board wipes.** If the theme provides incidental
interaction (e.g. removal stapled to your creatures' ETBs), reduce the dedicated count by 1–2 so you don't
flood. Higher brackets → more and more-efficient interaction (cheap instant-speed answers, free spells).
Lower brackets (1–3) → you can run more synergistic/situational interaction that's fun over pure
efficiency.

---

## Step 6 — Lands, then cut to exactly 100

**Land count: ~37–38.** This feels high to newer builders, but missing land drops is devastating to win
rate. Hold the line at ~38 unless the deck has an unusually low curve and lots of cheap card draw/ramp, in
which case 36–37 can be fine.

**Basics vs non-basics** depends on colors:
- **Mono-color:** mostly basics + a healthy package of **colorless utility lands** (lands that do things).
- **Two colors:** a fixing core (duals, taplands) + basics.
- **Three to five colors:** the **majority** of lands must be color-fixing; you still run ~38. Budget caps
  bite hardest here — premium duals are where the money is, so substitute taplands/basics under a cap.

**Then cut to 100.** Tally every fixed category (commander + lands + ramp + card advantage + interaction).
Subtract from 100 to learn how many **themed cards** survive. Sort the themed pile by mana value and cut:
- **Curve first** — keep only **3–4** truly expensive (MV 6+) cards; drawing multiple uncastable bombs is
  miserable. Push the rest of the curve low. Consider the commander's own cost and play pattern: if you'll
  usually cast the commander instead of another 3-drop, lighten the 3s and add 2s/4s. If the commander is
  a setup piece you want *out* before you do things, load the 1–3 slots so the board is ready when it lands.
- **Affinity second** — when torn between two comparable cards, keep the one with **more synergy with the
  rest of the deck**. Affinity beats raw power for fun and consistency. If one card is just too cool to
  cut, slam it; one indulgence is fine.

---

## Step 7 — Goldfish and lock in win conditions

"Goldfishing" = playing the deck solo, no opponent, making realistic plays (don't pretend a 1/1 always
connects). Play to ~**turn 7** and read the board.

Ask two questions:
1. **With this typical board and hand, could I actually win?**
2. If not, **is there a single card I could draw next turn that wins from here?**

If the answer to both is "not really," the deck lacks a closer for its own best board state. Use Scryfall
to find one: search the deck's **payoff keywords** (e.g. for a counters/sacrifice deck:
`o:"loses life" o:power`, `o:"each opponent"`, artifact/aristocrat finishers) within the color identity,
and slot the perfect closer in for the weakest themed card.

Keep goldfishing until you understand the deck's lines and have **3–4 win conditions** — cards that, given
the deck's normal big board, very likely end the game. Multiple win cons make the deck resilient to having
one answered. Common closers: a finisher that drains all opponents off your board's size, a big evasive
threat plus a counter-doubler, a mill/overrun payoff, or a combo the bracket allows.

---

## Sanity checklist (run before delivering)

- [ ] Exactly **100** cards including the commander.
- [ ] **~38** lands (36–38 acceptable; justify anything lower).
- [ ] **≥12** net-positive card-advantage pieces, ~8 cheap / ~4 expensive.
- [ ] **~10–11** ramp pieces + a few explosive; efficient curve.
- [ ] **~10** dedicated interaction + **2–4** board wipes.
- [ ] **3–4** genuine win conditions.
- [ ] Every **themed/synergy** card clears **≥2–3 points of contact** (structural utility exempt) — see
      `references/synergy.md`.
- [ ] Every card inside the commander's **color identity**.
- [ ] **Bracket** rules satisfied (Game Changer count, combo/MLD limits — see `brackets.md`).
- [ ] Within **budget** if a cap was set; total price shown.
- [ ] Curve sensible: only 3–4 cards at MV 6+.
