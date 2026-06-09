# Scryfall Query Cookbook

Scryfall is the workhorse for filling category gaps, enforcing color identity, and pricing. This file maps
the deckbuilding steps to ready-made queries. Run them with the bundled script
(`python scripts/scryfall_search.py "<query>" --limit 30`) when you have network in code execution, or via
`web_search` → `web_fetch` of the resulting Scryfall page otherwise.

Search endpoint: `https://api.scryfall.com/cards/search?q=<url-encoded query>&order=edhrec`
Named lookup:   `https://api.scryfall.com/cards/named?exact=<name>` (full card + prices)

## Core operators

| Operator | Meaning | Example |
|---|---|---|
| `id<=WB` | **Color identity coverage** — every card legal in a White/Black commander deck | `id<=WB` |
| `id<=esper` | Same, using guild/shard/wedge nicknames (azorius, bant, abzan, jund, sultai…) | `id<=jund` |
| `id:c` | Colorless identity (goes in any deck) | `id:c t:land` |
| `o:"text"` | Oracle (rules) text contains phrase | `o:"whenever a creature dies"` |
| `t:type` | Card type / supertype / subtype (partial ok) | `t:creature`, `t:artifact`, `t:legend` |
| `mv<=3` | Mana value comparisons (`>`, `<`, `=`, `>=`, `<=`, `!=`) | `mv>=6`, `mv=2` |
| `pow>=4` | Power / toughness | `pow>=5` |
| `function:ramp` | **Oracle function tags** (curated by Scryfall's Tagger; alias `otag:`) | see below |
| `keyword:flying` | **Keyword ability** the card has | `keyword:convoke`, `keyword:deathtouch` |
| `is:gamechanger` | Cards on the official Game Changers list (verify syntax if it misses) | `is:gamechanger id<=WB` |
| `-` prefix | Negation | `t:goblin -t:creature` |
| `or` | Either term | `(o:"draw two" or o:"draw three")` |
| `order=edhrec` | **Sort by popularity** — put the most-played, most-relevant cards first | append to any query |
| `usd<=2` / `eur<=2` | Price filters (eur = Cardmarket) | `eur<=1.5` |

Combine freely; all terms are AND by default. Always lead identity searches with `id<=<colors>` so results
are legal in the deck. Add `-is:funny -t:conspiracy` and, if you only want real paper cards,
`(game:paper)` to avoid digital-only/joke results. Use `order=edhrec` almost always — it surfaces the
cards real decks run.

⚠️ **Use `id<=`, never `c:`, to vet color legality.** `c:b` matches any card *containing* black —
including multicolor (B/U, B/R…) cards that are **illegal** outside their full color identity. Color
identity (`id<=`) is what determines deck legality. The search table prints a **CI (color identity)**
column for every card — glance at it and confirm each card fits the commander's identity before adding it.

## Finding multi-synergy cards (the intersection)

The synergy method (`references/synergy.md`) turns each of the commander's keywords into a Scryfall handle,
then looks for cards that hit **several at once**. Two ways to find that intersection:

- **AND handles in one query** (all terms are AND by default) — the fastest way to surface cards that are
  *already* multiple synergies. A death-trigger that also draws: `id<=BG (o:"whenever a creature" o:"dies")
  function:card-advantage`. A token-maker that's also fodder: `id<=GW otag:token-maker t:creature mv<=3`.
- **Run one query per keyword, then cross-reference the names that recur** across pools when a single
  combined query is too narrow (or when you need to union a thin Tagger tag with its `o:"…"` phrasing).

Rank what surfaces by how many of your handles each card matches — that count *is* its points-of-contact
score. Keep the densest; drop one-contact cards (see `references/synergy.md` for the ≥2–3 rule).

## Function tags (the fast path for categories)

Scryfall's `function:` (alias `otag:`) tags are curated and map cleanly onto the methodology. They're the
quickest way to fill a category within a color identity:

- Ramp: `function:ramp id<=<colors>`
- Card advantage / draw: `function:card-advantage id<=<colors>` (also `function:draw`)
- Removal: `function:removal id<=<colors>` (spot removal); `function:creature-removal`, `function:removal-multiple`
- Counterspells: `function:counterspell id<=<colors>`
- Board wipes: `function:board-wipe id<=<colors>` (also `function:mass-removal`)
- Tutors: `function:tutor id<=<colors>` (watch bracket restrictions on tutors)

Tag coverage isn't 100%, so combine with oracle-text searches when a tag returns too few results.

## Step-by-step query recipes

Replace `WB` with your commander's identity letters (or a nickname). Append `order=edhrec` to all.

**Step 2 — themed cards.** Build one query per commander keyword, then look for cards appearing across
several. For a sacrifice / +1/+1-counter / ETB commander in WB:
- Sac fodder / aristocrats: `id<=WB (o:"create a" o:"token") (t:creature or t:artifact) mv<=3`
- Sacrifice outlets: `id<=WB o:"sacrifice a creature" -o:"sacrifice a creature: " ` (repeatable outlets)
- Death payoffs: `id<=WB o:"whenever a creature you control dies"`
- +1/+1 counter synergy: `id<=WB o:"+1/+1 counter"`
- Re-trigger ETBs / flicker: `id<=WB (o:"exile" o:"return" o:"to the battlefield") t:permanent`
- Recursion from graveyard: `id<=WB o:"from your graveyard" (t:creature or t:permanent)`

**Step 3 — card advantage.** `function:card-advantage id<=WB mv<=3` for the cheap engine pieces;
`function:card-advantage id<=WB mv>=4` then keep only the explosive draws (read text for "draw X" where X
scales). Sanity-check it's *net positive* (replaces itself + more), not just "draw" in the text.

**Step 4 — ramp.** Cheap rocks/dorks: `function:ramp id<=WB mv<=2 order=edhrec`. Land ramp:
`id<=WB o:"search your library for" o:"land" o:"battlefield"`. Explosive: `id<=WB o:"add" o:"mana"`
combined with doublers `id<=WB o:"twice that much mana"` or treasure `id<=WB o:"create" o:"treasure"`.

**Step 5 — interaction.** Removal: `function:removal id<=WB mv<=3`. Counters:
`function:counterspell id<=WB`. Board wipes: `function:board-wipe id<=WB`. Protection:
`id<=WB (o:"hexproof" or o:"indestructible" or o:"protection") t:instant`.

**Step 6 — lands.** Mono-color utility: `id:c t:land` (colorless utility, fits any deck) and
`t:land id<=WB -t:basic` for fixing. For budget land bases filter price: `t:land id<=WB eur<=2`.

**Step 7 — win conditions.** Search the commander's payoff. Examples:
- Drain finishers: `id<=WB o:"each opponent loses" order=edhrec`
- Aristocrat/artifact finishers: `id<=WB o:"whenever" o:"sacrifice" o:"loses life"`
- Overrun-style: `id<=WB o:"creatures you control get +"`
Read candidates and keep the ones that win from the deck's *normal* board, not a dream scenario.

## Pricing

Every card object includes `prices.eur` and `prices.eur_foil` (Cardmarket, in euros). The bundled script
prints `eur` per card. Sum non-basics for the deck total; basics are free. `prices.eur` can be `null` for
cards with no Cardmarket listing (very new or paper-unavailable) — note those rather than guessing.

To price one specific card precisely: `python scripts/scryfall_search.py --named "Smothering Tithe"` or
fetch `https://api.scryfall.com/cards/named?exact=Smothering+Tithe`.

## Etiquette

Add a short delay between API calls (the script does ~100ms). Prefer one good query over many redundant
ones. Cache results you've already pulled within a build rather than re-querying.
