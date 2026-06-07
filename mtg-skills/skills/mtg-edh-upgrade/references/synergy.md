# Synergy Scoring — the core method for picking cards that cohere

This is the shared, format-agnostic method every card choice in these skills runs through. The goal is
simple and strict: **every non-utility card you add must share at least 2–3 synergies ("points of contact")
with the deck's engine and, ideally, with the other cards you're already running. More points of contact is
always better — rank candidates by their synergy count and take the densest.**

A deck is a machine, not a pile of individually good cards. Synergy density is what makes the machine hum:
the more ways a card touches what the deck is doing, the more often it does something great, the more
emergent lines appear, and the more resilient and fun the deck is. This file is how you *measure* that
instead of eyeballing it.

---

## The loop: read → extract → map → search → intersect → score

Run this for the centerpiece/commander first (to define the deck's "synergy vocabulary"), then for every
candidate card you consider adding.

### 1. Read the card (Claude does this — it's the part a tag search can't)

Pull the **exact Oracle text and type line** (`scryfall_search.py --named "Card Name"`). Read the *wording*,
not the name or your memory of it. This is the irreplaceable step: **you (Claude) interpret what the card
actually does and cares about** — the curated tags only become useful once you've decided what to look for.

### 2. Extract the key elements

From the text and type line, list every **actionable concept** the card produces or rewards. These fall into
a handful of buckets:

- **Triggers / conditions** — *enters the battlefield, attacks, a creature dies, you cast a spell, end step,
  landfall, lifegain, you draw your second card.*
- **Actions / effects** — *sacrifice a creature, create a token, put a +1/+1 counter, draw a card, mill,
  exile and return (blink), return from graveyard, deal damage, gain life.*
- **Types / subtypes it cares about** — *Goblin, Artifact, Equipment, Aura, Vehicle, Saga, Dragon, "another
  creature", "a permanent".*
- **Keywords & evasion** — *flying, trample, deathtouch, lifelink, ward, convoke, affinity, prowess.*
- **Numeric/board axes** — *power ≤ 2, three or more counters, "for each creature", going wide vs. going
  tall, mana value matters.*

Write the list down — it's the card's **synergy vocabulary**. The commander's/centerpiece's vocabulary is
the deck's shopping list.

### 3. Map each element to a Scryfall handle

Every element becomes one or more searchable handles. Use the **most specific handle that exists**, in this
order of preference:

| Element kind | Best handle | Example |
|---|---|---|
| A well-known **function/role** | **Tagger tag** `function:` / `otag:` (curated; routes to the live API) | `function:ramp`, `otag:sacrifice-outlet`, `function:card-advantage`, `otag:token-maker`, `otag:aristocrats`, `function:tutor`, `otag:flicker`, `function:board-wipe` |
| A specific **rules phrase** | **Oracle text** `o:"…"` | `o:"whenever a creature you control dies"`, `o:"sacrifice a creature"`, `o:"+1/+1 counter"`, `o:"create a"` + `o:"token"` |
| A **type / subtype** | **Type** `t:…` | `t:goblin`, `t:artifact`, `t:equipment`, `t:saga` |
| A **keyword ability** | **Keyword** `keyword:…` (or `o:"…"`) | `keyword:flying`, `keyword:convoke`, `o:"trample"` |
| A **numeric axis** | comparison operators | `pow<=2`, `o:"for each"` |

Tagger tags (`function:`/`otag:`) are the fast path because they're **curated by humans** to capture a card's
*role* even when the wording varies (every sacrifice outlet, however worded, is `otag:sacrifice-outlet`).
They route to the live Scryfall API automatically (the local bulk DB doesn't carry them) — that's expected.
**Tag coverage isn't complete**, so when a tag returns too few results, fall back to the `o:"…"` phrasing for
the same concept and union the results. Confirm a tag exists by trying it; if it returns nothing useful, use
oracle text instead.

### 4. Search each element, then INTERSECT

Run one query per element within the deck's color identity (`id<=<colors>` for Commander; `legal:standard
game:arena` etc. for Arena — and **never `c:`**, which matches off-identity cards). You now have a candidate
pool per element. **The cards that matter are the ones that appear in *several* pools at once** — those are
the multi-synergy cards.

Two ways to find the intersection:
- **Combine handles in one query** (all terms AND by default): e.g.
  `id<=BG (o:"whenever a creature" o:"dies") o:"draw a card"` finds death-trigger card advantage in one shot
  — a card that's *already* two synergies (death payoff **and** card draw).
- **Run them separately and cross-reference** the names that recur across pools when a single query is too
  narrow or a tag and a phrase need unioning.

### 5. Score by points of contact, and apply the 2–3 minimum

For each candidate, count its **distinct points of contact**:

- **+1** for each of the deck's vocabulary elements its text/type hits.
- **+1** for each *other card already in the deck* it specifically combos with (not just shares a theme —
  actually makes better).

Then:

- **Keep only cards scoring ≥ 2–3.** A card with a single point of contact is a **cut candidate** — it's a
  "good card" doing one thing, not an *engine* card. Replace it with a higher-contact option unless nothing
  exists.
- **Rank by score and take the densest.** Between two cards, the one with more points of contact wins, even
  if it's individually "weaker" — affinity beats raw power for both consistency and fun.
- **State the contacts in the card's reason.** Every recommendation/inclusion should name *which* synergies
  it hits, e.g. *"hits **dies** and **sacrifice** triggers and **draws** — 3 points of contact."* If you
  can't name two, it probably doesn't belong.

A useful gut check: **would this card still be doing real work if your commander/centerpiece weren't on the
battlefield?** High-contact cards usually say yes, because they also wire into the *rest* of the deck.

---

## The one exception: structural utility cards

Pure **structural** slots — lands, generic mana ramp, generic catch-all removal, a board wipe — fill a
required role and are **not** held to the 2–3 synergy rule; a deck needs its ~38 lands and its interaction
regardless of theme. But even here, **prefer the version that also synergizes**: a sac-outlet that's also
ramp, a removal spell that also draws, a utility land that also makes a token or returns a creature. When two
options fill the same structural role equally, the one with extra points of contact wins.

Everything in the *themed / payoff / synergy* portion of the deck, though, must clear the bar.

---

## Worked example

Commander: *"Whenever a creature you control dies, draw a card. Sacrifice another creature: this gets +1/+1
until end of turn."*

**Vocabulary extracted:** `dies` (trigger), `sacrifice a creature` (cost/action), `creature tokens` (cheap
fodder to feed it), `+1/+1` (counter/pump axis), `recursion` (get the sacrificed creatures back).

**Handles:**
- `otag:sacrifice-outlet` / `o:"sacrifice a creature"`
- `otag:token-maker` / `(o:"create" o:"token") t:creature`
- `o:"whenever a creature" o:"dies"` / `otag:aristocrats`
- `function:card-advantage`
- `o:"from your graveyard" t:creature` (recursion)

**Scoring candidates:**
- A 2-mana creature that **makes two tokens when it dies** → tokens (fodder) **+** dies-trigger **+** is itself
  fodder → **3 contacts. Slam it.**
- An enchantment: *"whenever a creature you control dies, create a 1/1, and you may pay 1: draw a card"* →
  dies payoff **+** token-maker **+** card advantage → **3 contacts. Slam it.**
- A vanilla 4/4 for 4 with no text → **0 contacts. Cut**, however "fine" the stats — it does nothing the
  machine cares about.
- A premium removal spell (structural) → exempt from the rule, but if a same-cost removal spell *also* makes
  a token or draws, prefer that one.

The output is a deck where almost every card is pulling 2–3 jobs at once. That density — found by reading
text, mapping to tags, intersecting, and scoring — is the whole game.
