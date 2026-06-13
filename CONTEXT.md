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
tab). Produced by `mtg-edh-primer`. Distinct from `deck.md`. _Avoid_: guide, writeup.

**`deck.md`**:
The owner's **private status** doc for a deck — budget, owned-vs-needed, buylists, and
upgrade tracking. Written by the build/upgrade skills; the personal counterpart to the
public `primer.md`. _Avoid_: using it as the published primer.

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
