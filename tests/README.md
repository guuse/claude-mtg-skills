# Tests

Offline smoke tests for the shared `mtg_scryfall` library (used by all the deckbuilding
skills). They live here, **outside** `mtg-skills/`, so they're never shipped with a
published skill or the plugin.

```bash
python -m unittest discover -s tests -v
```

No network and no bulk download. Two files:

**`test_mtg_scryfall.py`** — the engine smoke test. Builds a small crafted card set into a
temporary SQLite database and checks:

- the build/collapse logic — one row per `oracle_id`, cheapest-printing price, latest
  printing's rarity, dropped tokens, hidden funny/un-cards;
- the Scryfall→SQL query translator — color-identity subsets, oracle/type/numeric filters,
  rarity ordering, `legal:`/`game:`/`eur:` filters, negation, and `named()` for split/DFC names;
- the routing rule — `function:`/`otag:`/`set:`/unknown operators make `to_sql()` return
  `None` so the caller falls back to the live Scryfall API.

**`test_tier2.py`** — broader deterministic coverage:

- Arena wildcard math + import parsing (`mtg_scryfall.arena`): tier caps, over/hard/soft,
  off-color flagging, basics, unknown cards;
- the streaming bulk-JSON parser at awkward buffer boundaries (objects split across chunks);
- database status / 30-day staleness boundary and the auto-build availability paths;
- `simplify_api` via a canned card dict (no Scryfall call), including double-faced cards;
- additional query operators — `c:`, `id>=`, guild/wedge nicknames, `pow`, rarity abbrev,
  `t:permanent`, nested `or`/parens, `kw:`.

CI runs the suite across Python **3.9, 3.12, 3.13** (see `.github/workflows/ci.yml`) — the
latest two plus a 3.9 floor (macOS/older-distro system Python). The skills are stdlib-only,
so there are no dependencies to install.

On pull requests a separate `coverage` job measures line coverage of the shared library,
posts it as a sticky PR comment, and **fails if coverage drops below 95%**
(`coverage report --fail-under=95`). Run it locally with:

```bash
pip install coverage
coverage run --source=mtg-skills/lib/mtg_scryfall -m unittest discover -s tests
coverage report -m
```
