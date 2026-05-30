# Wildcard Budget Tiers

In MTG Arena you build cards by spending **wildcards** that match the card's **rarity**. One copy of a card
costs one wildcard of its rarity; four copies cost four. **Basic lands are free.** So a deck's "budget" in
Arena is just its wildcard cost broken out by rarity — and rares and mythics are the scarce, expensive
ones, while commons and uncommons accumulate quickly.

This skill caps the wildcard cost with a **tier (1-5)**. The tier limits how many wildcards of each rarity
the deck may *require* beyond what a typical account already owns (basics, plus the commonly-owned commons
from starter/new-player decks — "the rest from default cards").

## Tier table

| Tier | Common | Uncommon | Rare | Mythic | Feel |
|---|---|---|---|---|---|
| **1** | 8 | 4 | 0 | 0 | New-player. No rares/mythics at all — basics + owned commons + a few uncommons. |
| **2** | 12 | 6 | 2 | 1 | Budget brew with a single bomb and a couple of key rares. |
| **3** | 16 | 10 | 6 | 3 | Focused deck with a real rare core. A good default. |
| **4** | 20 | 14 | 12 | 6 | Near-meta; most of a tuned list is affordable. |
| **5** | ∞ | ∞ | ∞ | ∞ | No limit — full meta netdeck. |

Counts are **total wildcards of that rarity across the whole deck** (copies included), maindeck + sideboard.
If the user is unsure which tier they want, suggest **Tier 3**.

## How the caps actually bind (read this)

Not all four caps work the same way, because the Arena economy doesn't treat the rarities the same way:

- **Rare and Mythic are HARD caps.** These are the scarce, slow-to-earn wildcards and they are the real
  budget gate. A deck must come in at or under the tier's rare and mythic numbers. Count them **from what
  the user still needs to craft**: when a collection is loaded, copies they already own are free and don't
  count; with no collection, count from zero (the conservative gate). This is also where a centerpiece's
  cost shows up: a Rare legendary you run as a 2-of is 2 rare wildcards — unless the user already owns it.
- **Common and Uncommon are SOFT targets, counted as "crafts beyond what you already own."** Any 60-card
  Standard deck needs *far* more than a handful of uncommons (often 15-25) and a stack of commons, so the
  literal C/U numbers can't be a from-zero cap or no real deck would fit. Commons and uncommons are cheap,
  accumulate quickly from play, and a typical account already owns many from starter/event decks — that's
  the original "rest from default cards" idea. Treat the C/U numbers as a guide to how *wildcard-light* the
  build should feel, not a hard wall; report the actual C/U totals so the user knows the from-zero cost.

So when you check a finished deck: **pass/fail on Rare and Mythic; report-and-note on Common and Uncommon.**
The bundled script does exactly this (rare/mythic flagged with ✗ if over; C/U shown with a soft note).

## How to count

For each non-basic card: `copies x 1 wildcard of its rarity`. Sum per rarity. Basic lands (Plains, Island,
Swamp, Mountain, Forest, Wastes) cost nothing. The bundled script does this automatically:

```
python scripts/scryfall_search.py --deck <arena-import>.txt --tier 3
```

It looks up each card's rarity on Scryfall, prints the C/U/R/M totals, flags basics as free, and tells you
whether the list fits the tier (and by how much it's over, per rarity).

> Note on ownership: when a collection export is loaded (`.mtg/collection/mtga_collection.txt`), it is the
> **source of truth** for what the user owns — subtract owned copies from the craft count for **every**
> rarity, so the totals reflect what they must actually craft. The bundled script counts every non-basic
> card from zero (it doesn't read the collection), so when a collection is loaded, subtract owned copies
> from its totals yourself. With **no** collection loaded there's no public API for account ownership:
> count rares and mythics from zero (the conservative gate), report commons/uncommons from zero as soft
> (most are cheap or already owned), and exclude anything the user tells you they own.

## Optimizing within a tier

Rares and mythics are the real constraint; commons and uncommons are easy to acquire. So spend the scarce
wildcards where they matter most and economize everywhere else:

1. **Protect the centerpiece.** The card the deck is built around almost always deserves its rare/mythic
   wildcards. Cut cost elsewhere first.
2. **The mana base is usually the biggest rare sink.** Premium dual/utility lands are often rare. At low
   tiers, build the base from **basics + common/uncommon taplands and pain lands**, and spend rare
   wildcards on duals only if the deck's colors truly demand them. A two-color deck can often run a fine
   budget base with zero rare lands.
3. **Find cheaper role-equivalents.** If an expensive rare removal spell blows the budget, a common/uncommon
   removal spell that kills the same threats at a similar rate may cost you little in power. Use Scryfall
   `function:removal r<=uncommon legal:standard game:arena` to find them.
4. **Trim copies before cutting roles.** Going from 4 to 3 copies of a flex rare saves a wildcard while
   keeping the effect in the deck.
5. **Tier 1 specifically:** no rares or mythics, so the deck is commons/uncommons + basics. Favor efficient
   commons, aggressive or aggressive-tempo plans (which lean less on bomb rares), and avoid archetypes that
   *need* rare payoffs or rare mana bases to function (many control and ramp decks do).

When you present the deck, show the wildcard breakdown like (rare/mythic are the pass/fail; C/U informational):

```
Wildcard cost (Tier 3 — hard caps: 6 Rare / 3 Mythic; C/U are targets)
  Common:   15  • over the 16 target — fine (cheap / usually owned)
  Uncommon: 18  • over the 10 target — fine (cheap / usually owned)
  Rare:      6  ✓ (at cap)
  Mythic:    2  ✓
```

If a **rare or mythic** is over cap, list the specific cards driving it and the cheaper swaps you'd make
(`function:<role> r<=uncommon`), so the user can decide whether to craft up or stay on budget. If only the
common/uncommon totals are high, just note the from-zero craft cost — it isn't a real obstacle.
