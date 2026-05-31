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
