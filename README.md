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
| **mtg-edh-build** | Builds a complete, balanced **100-card Commander (EDH) deck** around any commander you name. **Grounds the build in comparable proven decklists** (EDHREC average/top/theme/budget pages, optionally top Archidekt/Moxfield lists), assembles a **solid reference deck for the target bracket ignoring budget first**, then **budgets down by role-preserving swaps** (most-expensive-first; cheaper card, same role/synergy). Prices everything via Scryfall (Cardmarket EUR). Produces an **annotated decklist** (grouped by role, per-card reasons + prices, the reference base, every swap, total cost) and a **plain importable list** (ready to paste into Moxfield / Archidekt / mtggoldfish). Reports the deck's **actual (strictly determined) bracket** with a *what's-needed-to-go-up* note; if a budget can't hold the bracket, it says so and steps down. **Every finished deck ships with a strict, evidence-based ★ rating** (a deck that merely functions is 3★; per-dimension scorecard in `deck.md`). |
| **mtg-std-build** | Builds a **60-card Standard deck for MTG Arena**, centerpiece-first and tuned against the current ladder meta (from the model's knowledge — no bot-fetchable meta source; blocked sites are never scraped). Verifies Standard legality, rarity, and Arena availability via Scryfall, and costs the deck in **Arena wildcards** against a budget tier (1–5) and your owned collection. Produces an **annotated decklist** (roles, rarity per card, mana curve, wildcard-cost breakdown, meta plan) and an **Arena import list** ready to paste in-client. Supports BO1 ladder and BO3 + sideboard. **Every finished deck ships with a ★ rating** (ladder-and-tier scorecard in `deck.md`). |
| **mtg-edh-upgrade** | **Improves an existing Commander deck** you paste in. Diagnoses the list against the same methodology **and against comparable proven lists** (inclusion rates), then recommends the highest-impact **swaps** within a budget — which, because it's an upgrade, can be far smaller than building from scratch — making **role-preserving** substitutions and stopping honestly (or stepping down a bracket) when the budget can't reach the target. Outputs an upgraded annotated decklist with a **Changes** section (cut → add, shared role, EUR cost), the deck's **actual bracket** + *what's-needed-to-go-up* note, and a ready-to-import list. Color-identity- and bracket-aware. **Output carries a strict ★ rating** (3★ = merely functions; before→after scorecard in `deck.md`). |
| **mtg-std-upgrade** | **Improves an existing Arena Standard deck** you paste in. Diagnoses curve, mana base, consistency, and meta matchups, then recommends **swaps** built from cards you already own (via your collection export) and costed in a (usually low) wildcard tier. Outputs an upgraded annotated decklist with a **Changes** section (cut → add, rarity, owned/craft cost) and an Arena import list. BO1 / BO3. **Output carries a ★ rating** (before→after scorecard in `deck.md`). |
| **mtg-card-finder** | A consultative **card finder & deck problem-solver** — for when you want the *right cards*, not a whole deck. It starts by pinning down the **purpose** (pick a commander, fill a gap, deepen a category like card advantage/ramp/removal, find synergy pieces, or solve a problem like "I can't close games"), then **brainstorms** tailored context with you — playstyle/gimmicks/colors for commanders, the deck and its real pain points for everything else — to pinpoint what you *actually* need rather than what you first asked for. It then researches **Oracle text and type lines exhaustively** via Scryfall (plus EDHREC's JSON API for proven picks), ranking candidates by **cohesion** (how many ways a card touches your deck and itself) to surface genuinely synergistic cards. Hands back a focused, priced (Cardmarket EUR) **shortlist with reasoning**, then refines it with you. Hands off to the build/upgrade skills when you want those cards turned into a list. |
| **mtg-edh-analyze** | **Rates an existing Commander deck out of five stars** against a target power bracket — **strictly and honestly**. Paste your list and name a bracket (1–5); it measures the hard stats via the local Scryfall database — land count, mana curve, ramp/draw/interaction density, the **EDHREC-rank staple signal**, Game Changer count, color-identity legality, total EUR — **reads every card's Oracle text** for synergy, and **scores Staples/Synergy against comparable real lists** (inclusion rates), rounding down when evidence is thin. A deck that merely **functions is 3★**, not 4; 4–5 must beat the comparable lists. It awards an overall **★ rating** with a transparent per-dimension scorecard, **determines the bracket the deck actually sits at** from concrete signals (a tuned deck with 0 Game Changers / no combos / no MLD is **Bracket 2**, not 3), tells you what would move it up or down a bracket, and names the highest-impact, cheapest-first fixes — offering to hand off to **mtg-edh-upgrade** to make them. Evaluates a deck; doesn't change it. |
| **mtg-edh-primer** | Generates a comprehensive, **publish-ready primer** for an existing Commander deck — given a deck **slug** in your workspace or a **pasted list**. Reads every card's Oracle text via the local Scryfall database to infer the deck's **win conditions** and theme, tags every card with its **one most-defining role** (mana dork, sac outlet, fatty, draw, drain, recursion, removal, finisher, …), explains each in **one tight line in the context of the deck**, and writes an **early/mid/late play guide** with a mulligan note and common-misplays callout. **Opens with a ★ rating scorecard beside the power Bracket** (★ rates the deck *within* its bracket, so a 2★ B4 deck beats a 5★ B2 one). Outputs `primer.md` (paste straight into Moxfield's Notes/Primer tab) and a `moxfield-import.txt` carrying **exactly one tag per card** (the commander untagged) for Moxfield's **Bulk Edit**; never touches your `deck.md`. Explains a deck rather than building, swapping, or only scoring it. |
| **mtg-db** | Builds and refreshes the **local Scryfall card database** (`.mtg/database/cards.sqlite`) that the four deckbuilding skills read from instead of calling the Scryfall API on every query. Downloads Scryfall's "Default Cards" bulk file once, collapses it to one row per unique card (cheapest EUR/USD price, Arena availability, rarity, legalities, Game Changer flag, EDHREC rank), and stores it as SQLite — sharply cutting API calls and avoiding rate limits. You rarely run it directly: the deck skills **auto-build it on first use** and prompt you to refresh it when it's stale. |
| **mtg-export** | One-shot **MTG Arena collection exporter**. Reads your owned cards directly out of the running MTG Arena process's memory — no anchor cards, no manual steps — and writes them to your workspace as `collection/MTGA-export-<date>.csv` (Moxfield format), the exact file the Arena deck skills read to prefer cards you already own. Card names come from the **local Scryfall database** (mtg-db), so it never downloads or builds its own card data; MTG Arena's own bundled card files are merged in best-effort for anything newer than the database. After writing, it pushes the collection via **mtg-sync**. Cross-platform: Windows (via `pymem`) and macOS (via Mach APIs — needs `sudo`); needs MTG Arena installed and running. (Requires `numpy`, plus `pymem` on Windows — the one skill that isn't stdlib-only.) |
| **mtg-sync** | Keeps your **decks and collection in a private git repo** so the same data follows you across your Mac, another PC, and your phone. Sets syncing up the first time (clones your private `mtg-data` repo and scaffolds it), then **pulls before** and **pushes after** every deck build/upgrade — invoked automatically by the deck skills, the same way they rely on mtg-db for card data. Best-effort: if git or the network isn't available, it says so and the build proceeds with the local workspace. The rebuildable card database stays out of routine syncs, but can optionally be shared across machines via Git LFS (`--push-database` / `--pull-database`). See **[SYNCING.md](SYNCING.md)**. |

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

To **find cards or solve a deck problem** (not build a whole deck), just describe what you're after —
the **mtg-card-finder** skill brainstorms it with you:

> Help me pick a commander — I love sacrifice decks and going wide, but hate durdling.

> My Atraxa deck keeps running out of gas after a board wipe — what should I add?

> Find me the best budget removal for a Golgari deck, and cards that synergize with +1/+1 counters.

To **rate an existing Commander deck**, paste it and name a bracket — the **mtg-edh-analyze** skill scores
it out of five stars and tells you what to fix:

> Rate my deck out of 5 at Bracket 3, and tell me what bracket it actually is: \<paste decklist\>

Claude confirms the few parameters it needs — power bracket and budget for Commander, or
centerpiece/collection, wildcard tier, and BO1/BO3 for Arena Standard (upgrades just ask for a
budget, usually a small one) — then works through the methodology and hands back two files: an
annotated decklist and a ready-to-import list. You can also start a skill explicitly, e.g.
`/mtg-skills:mtg-edh-build`, `/mtg-skills:mtg-std-build`,
`/mtg-skills:mtg-edh-upgrade`, `/mtg-skills:mtg-std-upgrade`, `/mtg-skills:mtg-card-finder`, or
`/mtg-skills:mtg-edh-analyze`.

### Output & your collection

Builds are written into a **workspace** directory — by default a `.mtg/` folder in your current
working directory (already covered by this repo's [`.gitignore`](.gitignore)). Set the **`MTG_HOME`**
environment variable to put that workspace anywhere you like — point it at a private `mtg-data` git
repo and your decks + collection follow you across your Mac, a Windows PC, and your phone. Run any
skill's `scripts/scryfall_search.py --paths` to see where the workspace currently resolves.

**Sync across machines in one command.** Ask Claude to *"set up syncing for my decks"* (or run the
**mtg-sync** skill's `scripts/sync.py --bootstrap`): it creates a private `mtg-data` repo, scaffolds it
— including a `.claude/settings.json` that **auto-installs these skills** on any machine that opens it —
migrates any decks/collection you already have, and pushes. Then set `MTG_HOME` to the printed path.
See **[SYNCING.md](SYNCING.md)** for the full story (and the optional Moxfield mirror).

The workspace holds three subfolders:

- **`.mtg/decks/`** — built decks, **split by format**: Commander/EDH under `.mtg/decks/edh/` and
  MTG Arena Standard under `.mtg/decks/std/`. Each deck gets its own folder there (e.g.
  `.mtg/decks/edh/atraxa-praetors-voice/`) holding its two files, `deck.md` (annotated) and
  `import.txt` / `arena.txt` (ready to paste).
- **`.mtg/collection/`** — drop a collection export here and the builder will prefer cards you
  already own and flag what you still need to buy. Any common shape works — a **`.txt`** list
  (`1 Card Name` / `4 Lightning Bolt`), a **`.csv`** with name/quantity columns (Moxfield / Archidekt /
  MTGGoldfish / Arena exporters), or a **`.json`** export — the skills parse all three automatically.
- **`.mtg/database/`** — the **local Scryfall card database** (`cards.sqlite` + `meta.json`), built
  automatically on first use (a one-time ~540 MB download that becomes a ~170 MB SQLite file). Skills
  query this instead of the Scryfall API, so builds are fast and don't get rate-limited. It's refreshed
  when you ask, and the skills offer to update it once it's more than 30 days old. It's rebuilt per
  machine by default, but can optionally be **shared across machines via Git LFS** (`sync.py
  --push-database` / `--pull-database`) so a second computer fetches it instead of rebuilding — see
  [SYNCING.md](SYNCING.md).

## Requirements

- **Claude Code** (any recent version with plugin/skill support).
- **Network access** to `api.scryfall.com` (card data + pricing) and `json.edhrec.com` (proven
  Commander inclusions); optionally `archidekt.com` / `api2.moxfield.com` to import a deck by link.
  All requests use a descriptive User-Agent, prefer structured JSON endpoints, and retry transient
  failures with backoff; blocked HTML sites are never scraped. The first build downloads Scryfall's
  bulk card file (~540 MB) once into a local SQLite database; after that, card lookups are local and
  only `function:` tag queries and refreshes hit the network. If your environment blocks these domains,
  the skills say which source failed and fall back to the local database and Claude's own MTG knowledge
  (flagged as reduced confidence — prices and the newest cards won't be verified). See each skill's
  `references/data-sources.md` for the authoritative source and fallback order per data type.
- **Python 3** for the bundled helpers and the shared `mtg_scryfall` library — **standard library
  only, no `pip install` required** (`sqlite3` and `json` ship with Python). Code execution is needed
  to build the local database; without it, the skills fall back to live Scryfall via web search/fetch.
  The one exception is **mtg-export**, which reads the live MTG Arena process and therefore needs
  `numpy` (and `pymem` on Windows) — see its `scripts/requirements.txt`.
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
