# mtg-skills

A Claude Code plugin bundling **Magic: The Gathering** skills.

## Bundled skills

- **[mtg-edh-build](skills/mtg-edh-build/SKILL.md)** — builds a tuned,
  priced 100-card Commander (EDH) deck around any commander, **grounded in comparable proven
  decklists** (EDHREC average/top/theme/budget). It assembles a solid reference deck for the target
  bracket ignoring budget first, then **budgets down by role-preserving swaps**; Scryfall handles
  gap-filling and Cardmarket (EUR) pricing. Reports the deck's actual (strict) bracket + how to move up.
- **[mtg-std-build](skills/mtg-std-build/SKILL.md)** — builds a 60-card
  MTG Arena **Standard** deck that's **meta-relevant and cohesive**: it starts from **real, current
  tournament decklists pulled from mtgtop8.com** and adapts a proven list to your centerpiece/archetype,
  the live ladder meta, your owned collection, and a wildcard budget tier — rather than brewing a 60 from
  scratch. Costed in **Arena wildcards** by rarity; supports BO1 and BO3 + sideboard.
- **[mtg-edh-upgrade](skills/mtg-edh-upgrade/SKILL.md)** — improves an
  **existing** Commander deck you paste in: diagnoses it against the same methodology and **comparable
  proven lists**, then recommends the highest-impact **role-preserving** swaps within a budget (usually
  much smaller than a fresh build), priced in EUR. Reports the deck's actual bracket before→after.
- **[mtg-std-upgrade](skills/mtg-std-upgrade/SKILL.md)** — improves an
  **existing** Arena Standard deck you paste in: diagnoses curve, mana, and meta matchups, **diffs it against
  the proven version of its archetype on mtgtop8.com** (which staples it's missing, which counts are off),
  and recommends swaps built from cards you already own and costed in a (usually low) wildcard tier.
- **[mtg-card-finder](skills/mtg-card-finder/SKILL.md)** — a consultative **card finder & deck
  problem-solver**: brainstorms with you to pin down what you actually need (a commander to build
  around, a gap to fill, a category to deepen, synergy pieces, or the fix for a problem your deck
  keeps hitting), then researches Scryfall Oracle text and typings deeply to surface cohesive,
  high-synergy picks — priced in EUR. Finds cards, not whole decks.
- **[mtg-edh-analyze](skills/mtg-edh-analyze/SKILL.md)** — **strictly star-rates an existing Commander
  deck** against a target bracket: measures land count, curve, ramp/draw/interaction density, the
  EDHREC-rank staple signal, Game Changer count, and color legality via the local database, reads Oracle
  text and **comparable real lists** to score synergy and staples (rounding down when evidence is thin —
  a deck that merely functions is 3★). Returns an overall ★ rating with a per-dimension scorecard, the
  bracket the deck **actually is** (a tuned deck with 0 Game Changers/no combos/no MLD is Bracket 2, not 3),
  what would move it up or down, and the highest-impact fixes (handing off to mtg-edh-upgrade to apply them).
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
