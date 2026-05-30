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

Just ask, in plain language — for example:

> Build me a Bracket 3 Atraxa, Praetors' Voice deck under €150.

Claude will confirm the **power bracket (1–5)** and **budget** if you haven't given them, then
work through the methodology and hand back two files: an annotated, priced decklist and a
ready-to-import `.txt`. You can also start it explicitly with `/mtg-skills:mtg-commander-deckbuilder`.

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
