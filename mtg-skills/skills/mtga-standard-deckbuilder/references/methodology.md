# Methodology — Centerpiece-First Standard Brewing

This is the long version of the building method SKILL.md summarizes. The throughline: **start from one card
you love, learn everything it can do, and build a synergy web around it — then make sure the result can
actually win on the Arena ladder.** Brewing is iterative and a little bit of a graveyard of failed
experiments; that's normal and good. One new card from a new set can unlock a deck you shelved months ago.

There is no single correct way to build. Two healthy entry points:
- **Original brew** — you pick a card that calls to you and build something creative around it.
- **Meta deck with your tweaks** — you take a known ladder archetype and adjust it to taste. Equally valid;
  most players do a mix.

---

## Step 1 — Pick the centerpiece

Choose the card the deck is *about*: the one that wins the game, or simply the one you most want to play.
Commit to it — usually as a 4-of so you see it consistently. Everything else in the deck exists to make
this card great. If the user is building a meta archetype rather than a pet card, the "centerpiece" is
that archetype's core engine (the thing the deck is named after).

Picking something you love matters: you'll play the deck more, learn its lines, and find the upgrades.

---

## Step 2 — Interrogate the centerpiece (find the hidden axes)

This is where good brews are born. The trap is reading a card once, grabbing the obvious synergy, and
stopping. Dig deeper — most cards can be exploited along **several** axes, and the non-obvious ones are
where originality lives.

Three things to do:

**A. Pick which ability to build around.** If the card has multiple modes/abilities, choose the one that's
most fun and powerful for your plan and *lean all the way in*, rather than half-supporting both. (A card
whose "+1" makes token copies and whose "+2" does something else: if you're building around the copies,
build around the copies.)

**B. Enumerate the hidden synergy axes.** A single ability usually touches more themes than it first
appears. Worked example — a card that makes **hasty token copies that are sacrificed at end of turn**:
- **ETB triggers** — every copy re-triggers enters-the-battlefield abilities (the obvious axis).
- **Attack triggers** — the copies have haste, so they attack immediately and re-trigger attack abilities.
- **Sacrifice / death** — the copies die at end of turn, which is *fuel*: sac outlets, death triggers,
  and "when a creature dies" payoffs all turn that downside into value.
That one card is simultaneously an ETB deck, an attack-trigger deck, and an aristocrats/sacrifice deck.
List every axis like this before choosing your support cards.

**C. Read the rules text, not just the keyword.** Subtle wording opens combos:
- **Keywords that are secretly ETB triggers** — "landfall" literally means "whenever a land enters the
  battlefield." So landfall is an enters trigger, and effects that *double* enters/triggered abilities
  copy it. Some cards have the landfall *keyword* without spelling out "when a land enters," so check.
- **Power/toughness thresholds** — an effect that doubles the triggered abilities of creatures with power
  2 or less will double the passive trigger of a 1-power creature you'd never think to combo with. The
  interaction lives in the stat line, not the obvious text.
The habit: look at the card from every angle and ask "what *else* does this enable that isn't written in
big letters?"

---

## Step 3 — Build the synergy web

Now find the support. Prioritize cards that give **two-for-ones** with the centerpiece along the axes from
Step 2, and that also work with *each other* (the more cross-synergies, the better and more replayable the
deck). Look especially for the non-obvious interaction that accelerates the plan dramatically — the kind
of thing that makes you go "if this works it'll be great," then you test it in a practice/bot game to
confirm before trusting it on ladder.

Worked example of a web around the token-copy card above: a value creature whose copy fetches extra lands
*and* draws on death; beaters with both ETB *and* attack triggers (double dip on the copies); a couple of
cheap sac outlets and death payoffs to monetize the end-of-turn sacrifices.

Use Scryfall oracle-text searches to find these (see `scryfall-syntax.md`). Standard is a small pool, so
you can read most of the relevant cards.

---

## Step 4 — Don't overbuild (avoid win-more)

A real discipline: once an engine is good enough to win, adding *another* payoff on top is usually
"win-more" — it shines only when you're already ahead and is dead weight otherwise, and it often costs
real tempo (an extra expensive card you didn't need). Spend those slots on **consistency** (more copies of
your enablers, smoother mana) and **answers** (interaction for the matchups that beat you) instead. One
robust engine beats two fragile ones stapled together.

---

## Step 5 — Read the meta

The deck has to *compete*. Before finalizing, look at the current Standard ladder field:
- **untapped.gg** BO1 constructed Standard — the live ladder meta by play rate.
- **mtggoldfish** Standard metagame — percentages and full lists (better for BO3).

Note the top few decks. The ladder usually has a fast aggro deck (frequently mono-red), one or two
midrange decks, and a control or go-wide deck. This is the gauntlet your brew must survive — an ambitious,
slow, multi-card-combo deck will get run over by aggro if you don't plan for it.

---

## Step 6 — Tech against the meta (a deck is its answers)

Especially for slower or controlling decks, the deck is only as good as its answers. For each major
matchup, make sure you have a plan, and choose answers that don't undercut your own:

- **vs aggro (e.g. mono-red):** cheap, efficient early removal; one or two sweepers; some life gain
  (lifelink, life-gain removal, or a life-gaining card-draw engine). You need to survive the first few
  turns and stabilize.
- **vs midrange / heavy discard (e.g. mono-black):** card advantage so you can refuel after your hand is
  stripped — recurring draw engines, card-advantage creatures, planeswalkers.
- **vs go-wide / auras / ward (e.g. Boros):** sweepers to punish wide boards, enchantment/aura removal,
  and ways around ward (cheap effects that don't pay the ward tax, or removal that exiles).
- **vs graveyard / reanimator / combo:** graveyard hate — a static "exile all graveyards" enchantment, or
  instant-speed graveyard exile to break up a key turn.

**Match the answer to your own board.** A tokens deck should run a clean board wipe rather than a
"detain/lock all cheap permanents" effect that would also disable its own tokens. And look for **removal
that pairs**: e.g. one removal spell that gives the opponent a small token, plus a second card that sweeps
up those tokens the next turn. Thoughtful pairings turn two decent cards into a clean answer package.

---

## Step 7 — Build the mana base to match the deck's plan

The hardest part of brewing, and the most common reason a list underperforms. Match the lands to the
deck's *speed*:

- **Aggro / low curve, plan to win by turn 3-4:** run lands that are **untapped early** — fast lands (come
  in untapped while you have few lands) — plus **pain lands**. You're fine taking the pain because the game
  is short; what you can't afford is a tapped land costing you a turn. Avoid most taplands. Land count can
  be low (~17-20).
- **Midrange / control / tokens, longer games:** you have time, so lean into **utility and synergy lands**
  — creature-lands (the Restless cycle: lands that become creatures, great as extra threats that dodge
  sorcery-speed removal), value lands (e.g. Fountainport, Mirrex), and **colorless lands that match your
  theme** (search Scryfall colorless lands for keywords like "token" or "artifact" to find on-theme
  utility). Some taplands and duals are acceptable. Land count ~24-26.
- **Color count:** every extra color makes the mana harder; commit to the best fixing your speed allows
  rather than splashing greedily. If a splash needs perfect mana to function, it may not be worth it.

**Wildcard reality:** premium dual/utility lands are frequently **rare**, so the mana base is often the
biggest chunk of a deck's rare-wildcard cost. At low budget tiers, build the base from basics plus
common/uncommon taplands and pain lands, and save your rare wildcards for the lands that matter most.

---

## Step 8 — Assemble, cost, and fit the tier

Build to exactly 60 maindeck (+15 sideboard for BO3). Use 4-ofs for cards you always want to draw, 3/2/1
for situational or legendary cards you don't want to clump. Then:
1. **Cost it.** Sum copies x rarity; basics are free. (`scripts/scryfall_search.py --deck` does this and
   checks the tier.)
2. **Fit the tier.** If over a rarity cap, swap the least essential rares/mythics for cheaper cards with a
   similar role, or trim copies. Your meta read tells you which pieces are load-bearing vs flex.
3. **Sideboard (BO3 only).** 15 cards aimed at the matchups your maindeck struggles with — extra sweepers
   vs aggro, graveyard hate vs reanimator, disenchant effects vs artifacts/enchantments, hand disruption
   vs control.

---

## Sanity checklist

- [ ] Exactly **60** maindeck (+ **15** sideboard if BO3); ≤4 of any non-basic card.
- [ ] Every non-basic card is **Standard-legal**, **not banned**, and **available on Arena**.
- [ ] **Rarity labeled** on every card.
- [ ] **Wildcard cost** within the tier caps (or overage acknowledged), breakdown shown.
- [ ] A clear **centerpiece** and a synergy web that supports it; no win-more bloat.
- [ ] **Answers** for the top 2-3 ladder decks; sweeper choice doesn't hurt your own board.
- [ ] **Mana base** matches the deck's speed; sensible land count and curve.
