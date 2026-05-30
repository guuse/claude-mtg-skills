# claude-mtg-skills

A public collection of **Magic: The Gathering skills for [Claude Code](https://code.claude.com)**.
Install once and let Claude build, brew, and tune real decks for you — grounded in proven card
data and priced from live sources.

The repo is set up as a **Claude Code plugin marketplace**, so installing is a two-line command
(no cloning required). Manual install is documented below as a fallback.

## Skills

| Skill | What it does |
|-------|--------------|
| **mtg-commander-deckbuilder** | Builds a complete, balanced **100-card Commander (EDH) deck** around any commander you name. Pulls proven cards from EDHREC and mtgdecks.net, fills gaps and prices everything via Scryfall (Cardmarket EUR), and applies a disciplined 7-step methodology — correct ramp, card advantage, interaction, land count, curve, and real win conditions. Produces an **annotated decklist** (grouped by role, per-card reasons + prices, total cost) and a **plain importable list** (`1 Card Name`, ready to paste into Moxfield / Archidekt / mtggoldfish). Bracket- and budget-aware. |
| **mtga-standard-deckbuilder** | Builds a **60-card Standard deck for MTG Arena**, centerpiece-first and tuned against the current ladder meta (untapped.gg / mtggoldfish). Verifies Standard legality, rarity, and Arena availability via Scryfall, and costs the deck in **Arena wildcards** against a budget tier (1–5) and your owned collection. Produces an **annotated decklist** (roles, rarity per card, mana curve, wildcard-cost breakdown, meta plan) and an **Arena import list** ready to paste in-client. Supports BO1 ladder and BO3 + sideboard. |
| **mtg-commander-deckupgrader** | **Improves an existing Commander deck** you paste in. Diagnoses the list against the same 7-step methodology (land count, card advantage, ramp, interaction, curve, win cons), then recommends the highest-impact **swaps** within a budget — which, because it's an upgrade, can be far smaller than building from scratch. Outputs an upgraded annotated decklist with a **Changes** section (cut → add, reasons, EUR cost) and a ready-to-import list. Color-identity- and bracket-aware. |
| **mtga-standard-deckupgrader** | **Improves an existing Arena Standard deck** you paste in. Diagnoses curve, mana base, consistency, and meta matchups, then recommends **swaps** built from cards you already own (via your collection export) and costed in a (usually low) wildcard tier. Outputs an upgraded annotated decklist with a **Changes** section (cut → add, rarity, owned/craft cost) and an Arena import list. BO1 / BO3. |

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
/mtg-skills:mtg-commander-deckbuilder
```

To pull future updates:

```text
/plugin marketplace update claude-mtg-skills
```

### Option B — Manual copy (no plugins)

Clone the repo and copy the skill folder into your skills directory. Use `~/.claude/skills/`
for a **personal** skill (available in every project) or `<your-project>/.claude/skills/` for a
**project** skill (shared with your team via git).

**macOS / Linux:**

```bash
git clone https://github.com/guuse/claude-mtg-skills.git
mkdir -p ~/.claude/skills
cp -r claude-mtg-skills/mtg-skills/skills/mtg-commander-deckbuilder ~/.claude/skills/
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/guuse/claude-mtg-skills.git
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse "claude-mtg-skills\mtg-skills\skills\mtg-commander-deckbuilder" "$HOME\.claude\skills\"
```

Claude Code discovers the skill on the next session start. If you added it mid-session, run
`/reload-plugins`. With this method the skill is invoked as `/mtg-commander-deckbuilder`
(no plugin namespace).

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
`/mtg-skills:mtg-commander-deckbuilder`, `/mtg-skills:mtga-standard-deckbuilder`,
`/mtg-skills:mtg-commander-deckupgrader`, or `/mtg-skills:mtga-standard-deckupgrader`.

### Output & your collection

Builds are written into a `.mtg/` folder in your current working directory (already covered by
this repo's [`.gitignore`](.gitignore)):

- **`.mtg/decks/`** — each deck gets its own folder here (e.g.
  `.mtg/decks/atraxa-praetors-voice/`) holding its two files, `deck.md` (annotated) and
  `import.txt` (ready to paste).
- **`.mtg/collection/`** — drop a collection export here (a Moxfield / Archidekt / MTGGoldfish CSV,
  or a plain `1 Card Name` list) and the builder will prefer cards you already own and flag what you
  still need to buy.

## Requirements

- **Claude Code** (any recent version with plugin/skill support).
- **Network access** to `api.scryfall.com`, `edhrec.com`, and `mtgdecks.net` for live card data
  and pricing. If your environment blocks these, the skill says so and can fall back to Claude's
  own MTG knowledge (with a caveat that prices and the newest cards won't be verified).
- **Python 3** for the bundled `scryfall_search.py` helper — **standard library only, no
  `pip install` required**. (Optional: the skill also works via web search/fetch if code
  execution isn't available.)

## Contributing

New MTG skills are welcome. Add one as a folder under `mtg-skills/skills/<your-skill-name>/`
with a `SKILL.md` (and optional `references/` and `scripts/` subdirs). Because everything lives
in the single `mtg-skills` plugin, users get new skills automatically on their next
`/plugin marketplace update` — no re-install needed. Bump the `version` in
[`mtg-skills/.claude-plugin/plugin.json`](mtg-skills/.claude-plugin/plugin.json) and
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) when you publish changes.

## License

[MIT](LICENSE).
