# Data sources & fallbacks (shared reference)

Every MTG skill that pulls outside data follows the same rules. The goal: **prefer
stable, public, structured JSON endpoints; never scrape sites that block automation;
and when a source fails, fall back to the next one and TELL THE USER** — never fabricate
decklists, prices, or meta.

All fetching goes through the shared `mtg_scryfall` library, which sends a descriptive
`User-Agent` and `Accept: application/json`, uses HTTPS only, adds a small polite delay,
and **retries transient failures (network errors, HTTP 429/5xx) with exponential
backoff**. A permanent miss (403/404, non-JSON) raises `FetchError`, which the bundled
scripts surface as a clear, **non-fatal** message — the build proceeds on local data,
flagged as **reduced confidence**.

## Authoritative source per data type

| Data type | Authoritative source | Endpoint shape | Fallback order |
|---|---|---|---|
| Card data, legality, rarity, Arena availability, **prices** (EUR/Cardmarket), bulk | **Scryfall** | local SQLite DB built from `api.scryfall.com/bulk-data`; live `api.scryfall.com/cards/search` for `function:`/`otag:` | local DB → live API → model knowledge (flag prices/newest cards unverified) |
| Commander staples, high-synergy cards, themes, budget lists, **average decklists** | **EDHREC JSON** | `json.edhrec.com/pages/...` (see below) | EDHREC JSON → local Scryfall DB (`order=edhrec` + `is:gamechanger`/`function:`) + model knowledge (flag "proven inclusions" reduced) |
| A specific user's online decklist | **Archidekt / Moxfield JSON APIs** | `archidekt.com/api/decks/<id>/`, `api2.moxfield.com/v3/decks/all/<publicId>` | site API → ask the user to **paste** the list |
| Standard / Arena meta **+ real decklists** | **mtgtop8.com** (plain HTML + plain-text export) | `format?f=ST`, `archetype?a=<id>&f=ST`, `mtgo?d=<deckid>` via `scripts/mtgtop8_fetch.py` | mtgtop8 → model meta knowledge (flag unverified) + ask user to paste a netdeck |

## Scryfall — the backbone

- Local DB: `.mtg/database/cards.sqlite`, built on first use from the **Default Cards**
  bulk file. Read it with `scripts/scryfall_search.py`. `function:`/`otag:` (Tagger) and
  unsupported operators route to the live API automatically.
- Prices: every card carries `prices.eur` (Cardmarket EUR, cheapest printing) — use it
  for deck totals and budget trimming.

## EDHREC JSON — proven Commander inclusions

Use `scripts/edhrec_fetch.py` (it slugifies the commander name and calls these):

```
https://json.edhrec.com/pages/commanders/<slug>.json          # staples, high-synergy, top, themes
https://json.edhrec.com/pages/commanders/<slug>/<theme>.json  # one theme's cards (<theme> from .themes)
https://json.edhrec.com/pages/commanders/<slug>/budget.json   # the budget build
https://json.edhrec.com/pages/average-decks/<slug>.json        # a literal ~100-card average decklist
```

Slug = lowercase, drop `' , .`, every other run of non-alphanumerics → `-`
(*Atraxa, Praetors' Voice* → `atraxa-praetors-voice`). Request pattern: `User-Agent`
+ `Accept: application/json`, HTTPS. **Do NOT** fetch the HTML at `edhrec.com` or the
`json.edhrec.com/pages/themes/*` / `commanders.json` index pages — they 403 for bots.
If a page 403s/404s, fall back to the local Scryfall DB ordered by EDHREC rank and say
EDHREC was unavailable.

## Archidekt / Moxfield — a specific user's decklist

Use `scripts/import_deck.py <url-or-id>` (detects the site, normalises to `<qty> <name>`
lines, commanders first):

```
https://archidekt.com/api/decks/<id>/                 # cards[].card.oracleCard.name + .quantity; "Commander" category
https://api2.moxfield.com/v3/decks/all/<publicId>     # boards.<board>.cards{}.card.name + .quantity (needs a real UA)
```

`<publicId>` is the last segment of a Moxfield deck URL. If the deck is private or the
API errors, **ask the user to paste the list** — never invent one.

## Standard / Arena meta + decklists — use mtgtop8

**mtgtop8.com is bot-fetchable** — it serves plain HTML to a descriptive User-Agent and
exposes a plain-text decklist export, so (unlike the blocked sites below) it can be fetched
through the shared `http.get_text`. It is the source the Standard skills **build from**:
start from real, current tournament lists, then adapt. Use `scripts/mtgtop8_fetch.py`:

```
mtgtop8.com/format?f=ST            # metagame breakdown: archetypes, shares, ids   (--meta)
mtgtop8.com/archetype?a=<id>&f=ST  # recent decklists under one archetype          (--archetype <id>)
mtgtop8.com/mtgo?d=<deckid>        # one decklist as plain-text <qty> <name>        (--deck <id>)
```

**untapped.gg, mtggoldfish, mtgdecks, and aetherhub are Cloudflare-protected and 403
automated fetches — do NOT scrape them.** mtgtop8's metagame **shares** lag the very latest
ladder a little (treat percentages as approximate); the **decklists are real** recent
results. If mtgtop8 is unreachable:

1. Use Scryfall (`legal:standard`, `game:arena`) for what *exists and is legal*.
2. Describe the current meta from your own knowledge, **explicitly flagged as unverified
   / may be out of date**, and invite the user to paste a meta snapshot or a specific
   netdeck (which `import_deck.py` can ingest if it's a Moxfield/Archidekt link).
3. Never present a scraped or invented metagame percentage or decklist as fact.

## Fallback wording (always tell the user)

When a source fails, state plainly which one and what you used instead, e.g.:
> *EDHREC returned 403, so proven-inclusion data is from the local Scryfall database
> (ordered by EDHREC rank) plus general knowledge — treat the staples list as
> lower-confidence.*
