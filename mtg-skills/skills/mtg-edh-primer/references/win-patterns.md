# Win patterns

A menu of the common ways an EDH deck actually closes a game, to keep win-condition spotting **consistent and
complete**. A win condition can't be read off card names or types — it lives in the **Oracle text** and in how
pieces interlock, so read the text (use `references/synergy.md`'s read → extract → intersect method) and match
the deck to one or more patterns below.

**Name only *real, repeatable* wins** — finishers that close from the deck's *normal* board, resilient to a
single answer. A card that only helps when you're already winning (win-more) is not a win condition. Most decks
have **1–4**; name each, and list the **key enabling cards** for it (these become `#Finisher` + the relevant
theme tags).

## The patterns

| Pattern | How it kills | Tells in the text |
|---|---|---|
| **Combat / big creatures** | Attack for lethal — trample, evasion, doubled damage. | high power, trample/flying/menace, "double", extra combats |
| **Voltron** | One big evasive creature + auras/equipment + commander damage (21). | "attach", "equipped/enchanted creature gets", hexproof/protection |
| **Go-wide / tokens** | Many tokens + an anthem or overrun effect. | "create … token", "creatures you control get +X", "for each creature" |
| **Aristocrats / drain** | Sacrifice creatures; death/lifegain triggers drain the table. | "whenever a creature dies", "each opponent loses", "whenever you gain life" |
| **Big-mana X / burn** | Ramp into a huge `X` spell or repeatable ping for lethal. | `{X}` in cost "each opponent loses/​deals X", mana doublers |
| **Combo (often infinite)** | Assemble 2–3 pieces → infinite mana/tokens/damage/mill → win. | "untap", "whenever ~ enters/dies", cost-reducers, a payoff that scales |
| **Mill** | Empty opponents' libraries. | "mill", "puts the top … into graveyard" |
| **Alt-win** | A card that says "you win the game" / "that player loses". | explicit win/lose text, poison/infect |
| **Stax / grind-out** | Lock the table with taxes/denial, win slowly with any of the above. | "players can't", "costs more", "skip", "doesn't untap" |

## Writing the "How it wins" section

For each named win condition: one short paragraph — *the line* (concrete sequence), the *key cards*, and what
it needs to come online. Then state the **primary plan** vs **backups**, and call out any **two-card combo** (it
matters for bracket — see `references/brackets.md`). If the deck's mana value and ramp say it's fast or slow,
note the realistic turn it can threaten the win — this feeds the play guide's deck-tuned turn bands.
