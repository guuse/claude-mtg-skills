# Claude MTG Skills

A Claude Code plugin of Magic: The Gathering deckbuilding skills (Commander/EDH and
MTG Arena Standard, build + upgrade). All card data ultimately comes from Scryfall.

## Language

**Scryfall database** (a.k.a. _the database_, _local database_):
A local **SQLite** file (`.mtg/database/cards.sqlite`) of card data, built from
Scryfall's **Default Cards** bulk file (one entry per printing, carrying per-printing
EUR prices and Arena availability). Skills read from it instead of calling the
Scryfall API for everything the bulk data supports. The one exception is `function:`/
`otag:` (Tagger) queries, which are not in any bulk file and still hit the live API.
A `meta.json` alongside it records the source bulk version and download date.
_Avoid_: cache, dump, mirror.

**Bulk file**:
A single large JSON file Scryfall publishes for download. "Default Cards" is the one
this plugin uses. Distinct from the Scryfall HTTP API (per-query, rate-limited).

**Primer** (`primer.md`):
The **publish-ready** write-up of a deck — how it wins, every card's role, and an
early/mid/late play guide — meant to be shared (e.g. pasted into Moxfield's Notes/Primer
tab). Produced by the EDH **build**, **upgrade**, and **primer** skills. Distinct from
`deck.md`. _Avoid_: guide, writeup.

**`deck.md`**:
The owner's **private status** doc for a deck — budget, owned-vs-needed, buylists, and
upgrade tracking. Written by the build/upgrade skills; the personal counterpart to the
public `primer.md`. A deck with several **budget variants** keeps **one** shared `deck.md`
covering the whole ladder. _Avoid_: using it as the published primer.

**Role tag** vs **Theme tag**:
Both label a card's job in a deck and come from a single **canonical tag vocabulary**
(consistent names across decks). A **role tag** is what a card mechanically does
(`Ramp`, `Draw`, `Removal`, `Recursion`, `Finisher`, `Land`); a **theme tag** is how it
serves *this* deck's engine (`SacOutlet`, `Drain`, `Counters`, `Tokens`). Tags are applied
**only where they fit** — none is universal (a mono-white deck has no `ManaDork`).

**Star rating (★)** vs **Bracket**:
The **bracket** (1–5) is a deck's **absolute power tier**. The **star rating** (★–★★★★★)
is how good the deck is **within its bracket**. They are independent: a **2★ Bracket 4**
deck is more powerful than a **5★ Bracket 2** deck. Always show the ★ *beside* the bracket
and never imply ★ measures power. _Avoid_: "5-star = strongest deck".

**Budget variant**:
One version of *the same deck* built to a specific spend level on its upgrade ladder
(e.g. **base** → €25 → €100). The cheapest version — typically just what the owner
already has — is the **base** variant; each costlier variant adds higher-impact cards.
Variants are produced **only when asked for** (a budget ladder / multiple price points /
a transition); a plain build stays a single deck. Distinct from **bracket** (a power tier)
and from Standard's **wildcard tier** (a 1–5 wildcard-budget cap). _Avoid_: "tier" (it
already means bracket / wildcard tier — say *budget variant*).

**Buylist**:
The list of cards the owner still needs to **buy** to assemble a deck (or a budget
variant) from what they already own, with prices. It is the **price floor** (cheapest
copy of each card), not a placed order — a real single-seller/optimised cart costs more
once shipping and per-seller pricing are counted. Distinct from the deck's full card list
and from `deck.md`. _Avoid_: cart, order.
