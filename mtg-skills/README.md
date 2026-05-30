# mtg-skills

A Claude Code plugin bundling **Magic: The Gathering** skills.

## Bundled skills

- **[mtg-commander-deckbuilder](skills/mtg-commander-deckbuilder/SKILL.md)** — builds a tuned,
  priced 100-card Commander (EDH) deck around any commander, using EDHREC + mtgdecks.net for
  proven inclusions and Scryfall for gap-filling and Cardmarket (EUR) pricing.
- **[mtga-standard-deckbuilder](skills/mtga-standard-deckbuilder/SKILL.md)** — builds a 60-card
  MTG Arena **Standard** deck, centerpiece-first and tuned against the live ladder meta
  (untapped.gg / mtggoldfish), costed in **Arena wildcards** by rarity against a budget tier and
  your owned collection.
- **[mtg-commander-deckupgrader](skills/mtg-commander-deckupgrader/SKILL.md)** — improves an
  **existing** Commander deck you paste in: diagnoses it against the same methodology and recommends
  the highest-impact swaps within a budget (usually much smaller than a fresh build), priced in EUR.
- **[mtga-standard-deckupgrader](skills/mtga-standard-deckupgrader/SKILL.md)** — improves an
  **existing** Arena Standard deck you paste in: diagnoses curve, mana, and meta matchups and
  recommends swaps, built from cards you already own and costed in a (usually low) wildcard tier.

## Install

See the [repository README](../README.md) for install instructions. In short, from inside
Claude Code:

```text
/plugin marketplace add guuse/claude-mtg-skills
/plugin install mtg-skills@claude-mtg-skills
```
