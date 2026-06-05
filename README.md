<div align="center">

<img src="assets/logo.png" alt="claude-mtg-skills" width="180">

# claude-mtg-skills

<hr>

### 🃏 Build, brew, and tune real Magic: The Gathering decks — right from your terminal. 🤖

[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white)](https://code.claude.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](#requirements)
[![SQLite](https://img.shields.io/badge/SQLite-local%20db-003B57?logo=sqlite&logoColor=white)](#skills)
[![Data: Scryfall](https://img.shields.io/badge/data-Scryfall-635994)](https://scryfall.com)
[![coverage](https://img.shields.io/badge/coverage-%E2%89%A595%25-3fb950)](.github/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-3fb950)](LICENSE)

</div>

---

A public collection of **Magic: The Gathering skills for [Claude Code](https://code.claude.com)**.
Install once and let Claude build, brew, and tune real decks for you — grounded in proven card
data and priced from live sources. No spreadsheets, no 40 browser tabs — just ask. 🪄

The repo is set up as a **Claude Code plugin marketplace**, so installing is a two-line command
(no cloning required). Manual install is documented below as a fallback.

## Skills

| Skill | What it does |
|-------|--------------|
| **mtg-edh-build** | Builds a complete, balanced **100-card Commander (EDH) deck** around any commander you name. Pulls proven cards from EDHREC and mtgdecks.net, fills gaps and prices everything via Scryfall (Cardmarket EUR), and applies a disciplined 7-step methodology — correct ramp, card advantage, interaction, land count, curve, and real win conditions. Produces an **annotated decklist** (grouped by role, per-card reasons + prices, total cost) and a **plain importable list** (`1 Card Name`, ready to paste into Moxfield / Archidekt / mtggoldfish). Bracket- and budget-aware. |
| **mtg-std-build** | Builds a **60-card Standard deck for MTG Arena**, centerpiece-first and tuned against the current ladder meta (untapped.gg / mtggoldfish). Verifies Standard legality, rarity, and Arena availability via Scryfall, and costs the deck in **Arena wildcards** against a budget tier (1–5) and your owned collection. Produces an **annotated decklist** (roles, rarity per card, mana curve, wildcard-cost breakdown, meta plan) and an **Arena import list** ready to paste in-client. Supports BO1 ladder and BO3 + sideboard. |
| **mtg-edh-upgrade** | **Improves an existing Commander deck** you paste in. Diagnoses the list against the same 7-step methodology (land count, card advantage, ramp, interaction, curve, win cons), then recommends the highest-impact **swaps** within a budget — which, because it's an upgrade, can be far smaller than building from scratch. Outputs an upgraded annotated decklist with a **Changes** section (cut → add, reasons, EUR cost) and a ready-to-import list. Color-identity- and bracket-aware. |
| **mtg-std-upgrade** | **Improves an existing Arena Standard deck** you paste in. Diagnoses curve, mana base, consistency, and meta matchups, then recommends **swaps** built from cards you already own (via your collection export) and costed in a (usually low) wildcard tier. Outputs an upgraded annotated decklist with a **Changes** section (cut → add, rarity, owned/craft cost) and an Arena import list. BO1 / BO3. |
| **mtg-db** | Builds and refreshes the **local Scryfall card database** (`.mtg/database/cards.sqlite`) that the four deckbuilding skills read from instead of calling the Scryfall API on every query. Downloads Scryfall's "Default Cards" bulk file once, collapses it to one row per unique card (cheapest EUR/USD price, Arena availability, rarity, legalities, Game Changer flag, EDHREC rank), and stores it as SQLite — sharply cutting API calls and avoiding rate limits. You rarely run it directly: the deck skills **auto-build it on first use** and prompt you to refresh it when it's stale. |

## Install

### Option A — Plugin marketplace (recommended)

Run these inside Claude Code:

```text
/plugin marketplace add guuse/claude-mtg-skills
/plugin install mtg-skills@claude-mtg-skills
```

That's it. Verify with `/plugin` → **Installed** tab, where you'll see `mtg-skills`. The skill
auto-triggers when you ask for a Commander deck, or you can invoke it explicitly:

```text
/mtg-skills:mtg-edh-build
```

To pull future updates:

```text
/plugin marketplace update claude-mtg-skills
```

### Option B — Manual copy (no plugins)

Clone the repo and copy the skill folder into your skills directory. Use `~/.claude/skills/`
for a **personal** skill (available in every project) or `<your-project>/.claude/skills/` for a
**project** skill (shared with your team via git).

The deckbuilding skills share a small Python library (`mtg_scryfall`) that lives at
`mtg-skills/lib/` in the plugin layout. When you copy a single skill out on its own, that layout
is gone, so **also drop the library next to the skill's script** — the helper looks for a
`mtg_scryfall` package beside it. (The plugin-marketplace install in Option A handles this for you.)

**macOS / Linux:**

```bash
git clone https://github.com/guuse/claude-mtg-skills.git
mkdir -p ~/.claude/skills
cp -r claude-mtg-skills/mtg-skills/skills/mtg-edh-build ~/.claude/skills/
# bundle the shared library next to the skill's script:
cp -r claude-mtg-skills/mtg-skills/lib/mtg_scryfall ~/.claude/skills/mtg-edh-build/scripts/
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/guuse/claude-mtg-skills.git
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse "claude-mtg-skills\mtg-skills\skills\mtg-edh-build" "$HOME\.claude\skills\"
# bundle the shared library next to the skill's script:
Copy-Item -Recurse "claude-mtg-skills\mtg-skills\lib\mtg_scryfall" "$HOME\.claude\skills\mtg-edh-build\scripts\"
```

Claude Code discovers the skill on the next session start. If you added it mid-session, run
`/reload-plugins`. With this method the skill is invoked as `/mtg-edh-build`
(no plugin namespace). The first build downloads card data into `.mtg/database/` (one-time).

## Usage

Just ask, in plain language — the right skill triggers automatically. For example:

> Build me a Bracket 3 Atraxa, Praetors' Voice deck under €150.

> Build me a Standard mono-red aggro deck for Arena at wildcard tier 3.

To **upgrade an existing deck**, paste your current list right into the prompt:

> Here's my Commander list, upgrade it for about €30: \<paste decklist\>

> Improve this Standard deck against the meta, tier 2: \<paste Arena export\>

Claude confirms the few parameters it needs — power bracket and budget for Commander, or
centerpiece/collection, wildcard tier, and BO1/BO3 for Arena Standard (upgrades just ask for a
budget, usually a small one) — then works through the methodology and hands back two files: an
annotated decklist and a ready-to-import list. You can also start a skill explicitly, e.g.
`/mtg-skills:mtg-edh-build`, `/mtg-skills:mtg-std-build`,
`/mtg-skills:mtg-edh-upgrade`, or `/mtg-skills:mtg-std-upgrade`.

### Output & your collection

Builds are written into a `.mtg/` folder in your current working directory (already covered by
this repo's [`.gitignore`](.gitignore)):

- **`.mtg/decks/`** — each deck gets its own folder here (e.g.
  `.mtg/decks/atraxa-praetors-voice/`) holding its two files, `deck.md` (annotated) and
  `import.txt` (ready to paste).
- **`.mtg/collection/`** — drop a collection export here (a Moxfield / Archidekt / MTGGoldfish CSV,
  or a plain `1 Card Name` list) and the builder will prefer cards you already own and flag what you
  still need to buy.
- **`.mtg/database/`** — the **local Scryfall card database** (`cards.sqlite` + `meta.json`), built
  automatically on first use (a one-time ~540 MB download that becomes a ~170 MB SQLite file). Skills
  query this instead of the Scryfall API, so builds are fast and don't get rate-limited. It's refreshed
  when you ask, and the skills offer to update it once it's more than 30 days old.

## Requirements

- **Claude Code** (any recent version with plugin/skill support).
- **Network access** to `api.scryfall.com`, `edhrec.com`, and `mtgdecks.net` for card data and
  pricing. The first build downloads Scryfall's bulk card file (~540 MB) once into a local SQLite
  database; after that, card lookups are local and only `function:` tag queries and refreshes hit the
  network. If your environment blocks these domains, the skill says so and can fall back to Claude's
  own MTG knowledge (with a caveat that prices and the newest cards won't be verified).
- **Python 3** for the bundled helpers and the shared `mtg_scryfall` library — **standard library
  only, no `pip install` required** (`sqlite3` and `json` ship with Python). Code execution is needed
  to build the local database; without it, the skills fall back to live Scryfall via web search/fetch.
- **Disk space** for the local card database (~170 MB) under `.mtg/database/`.

## Contributing

New MTG skills are welcome. Add one as a folder under `mtg-skills/skills/<your-skill-name>/`
with a `SKILL.md` (and optional `references/` and `scripts/` subdirs). Because everything lives
in the single `mtg-skills` plugin, users get new skills automatically on their next
`/plugin marketplace update` — no re-install needed. Bump the `version` in
[`mtg-skills/.claude-plugin/plugin.json`](mtg-skills/.claude-plugin/plugin.json) and
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) when you publish changes.

## License

[MIT](LICENSE).
