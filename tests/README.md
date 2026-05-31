# Tests

Offline smoke tests for the shared `mtg_scryfall` library (used by all the deckbuilding
skills). They live here, **outside** `mtg-skills/`, so they're never shipped with a
published skill or the plugin.

```bash
python -m unittest discover -s tests -v
```

No network and no bulk download: `test_mtg_scryfall.py` builds a small crafted card set
into a temporary SQLite database and checks:

- the build/collapse logic — one row per `oracle_id`, cheapest-printing price, latest
  printing's rarity, dropped tokens, hidden funny/un-cards;
- the Scryfall→SQL query translator — color-identity subsets, oracle/type/numeric filters,
  rarity ordering, `legal:`/`game:`/`eur:` filters, negation, and `named()` for split/DFC names;
- the routing rule — `function:`/`otag:`/`set:`/unknown operators make `to_sql()` return
  `None` so the caller falls back to the live Scryfall API.

CI runs the same suite across Python 3.9–3.13 (see `.github/workflows/ci.yml`). The skills
are stdlib-only, so there are no dependencies to install.
