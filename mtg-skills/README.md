# mtg-skills

A Claude Code plugin bundling **Magic: The Gathering** skills.

## Bundled skills

- **[mtg-edh-build](skills/mtg-edh-build/SKILL.md)** — builds a tuned,
  priced 100-card Commander (EDH) deck around any commander, using EDHREC's JSON API for
  proven inclusions and Scryfall for gap-filling and Cardmarket (EUR) pricing.
- **[mtg-std-build](skills/mtg-std-build/SKILL.md)** — builds a 60-card
  MTG Arena **Standard** deck, centerpiece-first and tuned against the current ladder meta
  (from model knowledge — no bot-fetchable meta source; blocked sites are never scraped), costed
  in **Arena wildcards** by rarity against a budget tier and your owned collection.
- **[mtg-edh-upgrade](skills/mtg-edh-upgrade/SKILL.md)** — improves an
  **existing** Commander deck you paste in: diagnoses it against the same methodology and recommends
  the highest-impact swaps within a budget (usually much smaller than a fresh build), priced in EUR.
- **[mtg-std-upgrade](skills/mtg-std-upgrade/SKILL.md)** — improves an
  **existing** Arena Standard deck you paste in: diagnoses curve, mana, and meta matchups and
  recommends swaps, built from cards you already own and costed in a (usually low) wildcard tier.
- **[mtg-card-finder](skills/mtg-card-finder/SKILL.md)** — a consultative **card finder & deck
  problem-solver**: brainstorms with you to pin down what you actually need (a commander to build
  around, a gap to fill, a category to deepen, synergy pieces, or the fix for a problem your deck
  keeps hitting), then researches Scryfall Oracle text and typings deeply to surface cohesive,
  high-synergy picks — priced in EUR. Finds cards, not whole decks.
- **[mtg-edh-analyze](skills/mtg-edh-analyze/SKILL.md)** — **star-rates an existing Commander deck**
  against a target bracket: measures land count, curve, ramp/draw/interaction density, the EDHREC-rank
  staple signal, Game Changer count, and color legality via the local database, reads Oracle text to
  score synergy, and returns an overall ★ rating with a per-dimension scorecard, the deck's actual
  bracket, and the highest-impact fixes (handing off to mtg-edh-upgrade to apply them).
- **[mtg-export](skills/mtg-export/SKILL.md)** — one-shot **MTG Arena collection
  exporter**: reads your owned cards straight from the running game's memory (no anchors, no manual
  steps), names them from the local Scryfall database (mtg-db), writes
  `collection/MTGA-export-<date>.csv`, and pushes it via mtg-sync — so the Arena deck skills can
  prefer cards you already own. Windows + macOS (macOS needs `sudo`).

## Install

See the [repository README](../README.md) for install instructions. In short, from inside
Claude Code:

```text
/plugin marketplace add guuse/claude-mtg-skills
/plugin install mtg-skills@claude-mtg-skills
```

## Where your decks & collection live

Built decks and your collection go in a workspace directory — `.mtg/` in the current folder by
default, or wherever you point the **`MTG_HOME`** env var. Set `MTG_HOME` to a private `mtg-data`
git repo to sync decks + collection across machines and mobile; the bundled **mtg-sync** skill
sets that up and then pulls/pushes automatically around each build. See
[SYNCING.md](../SYNCING.md). Run any skill's `scripts/scryfall_search.py --paths` to see the
resolved locations.
