# Scryfall Cookbook — Standard / Arena / Rarity

Scryfall is the source of truth for Standard legality, rarity, and Arena availability. Run queries with the
bundled script (`python scripts/scryfall_search.py "<query>" --limit 30`) when code execution has network,
or via `web_search` → `web_fetch` of the Scryfall page otherwise.

Search endpoint: `https://api.scryfall.com/cards/search?q=<url-encoded query>&order=edhrec`
Named lookup:   `https://api.scryfall.com/cards/named?exact=<name>` (full card incl. `rarity`, legality)

## Always-on filters for this skill

Put these on essentially every search so results are legal, Arena-available, and current:

```
legal:standard game:arena
```

- `legal:standard` — legal in Standard **and not banned** (banned cards report as not_legal).
- `game:arena` — the card actually exists on MTG Arena (some paper cards don't; this matters a lot here).

Standard rotates, so don't hardcode a set list — `legal:standard` always reflects the current pool. To
sanity-check what's in Standard right now, see untapped.gg's "What's in Standard" or filter by it directly.

## Rarity

| Filter | Meaning |
|---|---|
| `r:common` | Commons (alias `rarity:`) |
| `r:uncommon` | Uncommons |
| `r:rare` | Rares |
| `r:mythic` | Mythics |
| `r<=uncommon` | Commons and uncommons (budget-friendly) |
| `r>=rare` | Rares and mythics (the expensive wildcards) |

Every card object has a `rarity` field — the script prints it as the `R` column (c/u/r/m). Surface it for
every card in the annotated decklist.

## Core operators

| Operator | Meaning | Example |
|---|---|---|
| `c:rg` / `id<=rg` | Color / color identity | `c:r` mono-red, `c:wu` |
| `t:type` | Type / subtype | `t:creature`, `t:instant`, `t:land` |
| `o:"text"` | Oracle text phrase | `o:"when ~ enters"`, `o:"landfall"` |
| `mv<=2` | Mana value | `mv<=1`, `mv=3` |
| `pow<=2` | Power / toughness (for stat-threshold combos) | `pow<=2 t:creature` |
| `function:removal` | Curated function tag | `function:removal`, `function:counterspell`, `function:board-wipe` |
| `is:permanent` / `t:token` | Misc | |
| `-` | Negation | `-t:land` |
| `or` | Either | `(o:"draw a card" or o:"draws a card")` |
| `order=edhrec` | Popularity sort (still useful in Standard) | append to query |

## Recipes by step

Add `legal:standard game:arena` to all of these (omitted below for brevity).

**Step 2-3 — synergy web around a centerpiece.** Translate the centerpiece's axes into oracle searches:
- ETB value: `o:"when ~ enters" t:creature mv<=3`
- Attack triggers: `o:"whenever ~ attacks" t:creature`
- Death / sacrifice payoffs: `o:"whenever a creature you control dies"`, sac outlets `o:"sacrifice a creature:"`
- Landfall (an ETB trigger!): `o:landfall`
- +1/+1 counter support: `o:"+1/+1 counter"`
- ETB/trigger doublers: `(o:"trigger an additional time" or o:"copy that triggered ability")`
- Stat-threshold combo pieces: `o:"power 2 or less"` (find the doublers), then check your centerpiece's power

**Step 6 — interaction / answers.** Filter by rarity to respect budget:
- Cheap removal: `function:removal mv<=2 r<=uncommon`
- Sweepers: `function:board-wipe` (read which ones spare your own board)
- Counterspells: `function:counterspell mv<=2`
- Graveyard hate: `o:"exile" o:"graveyard" (t:enchantment or t:instant)`
- Life gain vs aggro: `o:"gain" o:"life" function:removal` (removal that also gains life)
- Enchantment/aura removal: `o:"destroy target enchantment" or o:"exile target enchantment"`

**Step 7 — mana base by speed:**
- Fast lands (aggro): search the current fast-land cycle by name, or `t:land o:"enters tapped unless you control two or fewer other lands"`
- Pain lands: `t:land o:"deals 1 damage to you"`
- Creature-lands (midrange/control): `t:land o:"becomes a" o:"creature"` (e.g. the Restless cycle)
- Theme utility lands (colorless): `id:c t:land o:token`, `id:c t:land o:artifact`, etc.
- Budget base (low tier): add `r<=uncommon` to keep lands cheap

**Budget swaps (fit the tier).** When a rare is too expensive for the tier, find a cheaper role-twin:
`function:<role> r<=uncommon mv<=<same> c:<colors>` then compare effects.

## Pricing / cost note

This skill costs decks in **wildcards (rarity), not money** — so you don't need `eur`/`usd` price fields.
Rarity x copies is the whole cost model (basics free). If a user also wants paper/Cardmarket pricing, the
card objects do carry `prices.eur`/`prices.usd`, but that's secondary here.

## Etiquette

Small delay between API calls (the script handles it). Prefer one good query over many redundant ones;
Standard is a small pool, so a few well-aimed searches usually surface everything relevant.
