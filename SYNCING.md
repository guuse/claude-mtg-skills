# Syncing your decks & collection across machines

Your built **decks** (each `deck.md` guide + import list) and your **collection** exports are the
irreplaceable part of using these skills — the card database is just a rebuildable cache. By default
they're written to a `.mtg/` folder in whatever directory you run from, which is git-ignored and never
leaves that machine. This guide makes them follow you **everywhere — your Mac, a Windows PC, and your
phone — and always**.

> **The easy path: the `mtg-sync` skill.** Everything below is automated by the bundled **mtg-sync**
> skill — just say *"set up syncing for my decks"* and it asks for your repo, clones it, scaffolds it,
> and tells you the `MTG_HOME` line to set. After that the deck skills **pull before** and **push after**
> every build automatically. This document is the manual reference for what that skill does under the hood.

## How it works in one sentence

Point the skills at one workspace directory with the **`MTG_HOME`** environment variable, keep that
directory in a **free private Git repo**, and `git pull` / `git push` to sync it across machines (the
**mtg-sync** skill runs those pulls/pushes for you, around each build).

The skills resolve their workspace in this order: **`$MTG_HOME` → nearest `.mtg/` → `./.mtg/`**. Set
`MTG_HOME` and that's the single source of truth; leave it unset and nothing changes from today.

```
$MTG_HOME/               ← your private "mtg-data" repo, cloned on each machine
├── decks/               ← versioned: every deck.md guide + import.txt / arena.txt   (synced)
├── collection/          ← versioned: your Moxfield / Arena / Archidekt exports       (synced)
└── database/            ← cards.sqlite + meta.json — rebuilt per machine;            (synced on demand
                            optionally shared via Git LFS                              via --push/--pull-database)
```

By default the big `cards.sqlite` (~170 MB) stays out of git — it's rebuilt from Scryfall on each
machine in ~30 s, so routine syncs only move your decks and collection. If you'd rather **share the
built database** than rebuild it everywhere, the dedicated `--push-database` / `--pull-database`
commands sync it via **Git LFS** — see [Optionally syncing the card database](#optionally-syncing-the-card-database-git-lfs) below.

> **Why git and not Moxfield/Archidekt directly?** Those are the natural *human* home for MTG decks, but
> neither offers a free, supported write-API a tool can rely on, so the skills can't read your collection
> or push decks to them automatically without fragile, ToS-risky scraping. Git is free (unlimited private
> repos), works offline, runs on every OS and on mobile, and the skills already emit exactly the right
> files. Use **Moxfield as an optional pretty mirror** (see the last section) — git stays the source of truth.

---

## One-time setup

### Quick start (recommended) — one command

With the plugin installed (or this repo handy), the **mtg-sync** skill seeds the whole thing in one go:

```bash
python <mtg-sync>/scripts/sync.py --bootstrap
```

It creates a private `mtg-data` repo (via the `gh` CLI; clones it instead if it already exists),
scaffolds the full layout — `decks/`, `collection/`, a `.gitignore` that excludes the rebuildable
`database/`, a `README`, and the **`.claude/settings.json` that auto-installs the skills** — migrates
any decks/collection from your current workspace, commits, and pushes. Useful flags:
`--repo <name|owner/name|url>`, `--dest <path>`, `--public`, `--from <path>`, `--no-push`. It's
**idempotent**, so run the same command on each machine. Then finish with steps **2** and **3** below
(set `MTG_HOME`, build the database once). Or just ask Claude: *"set up syncing for my decks."*

The steps below are the **manual equivalent** of what `--bootstrap` does — use them if you'd rather set
things up by hand or don't have the `gh` CLI.

### 1. Create a free private data repo

GitHub free accounts get **unlimited private repositories** — this costs nothing.

```bash
# on github.com: New repository → name it "mtg-data" → Private → Create.
# then, locally:
git clone https://github.com/<you>/mtg-data.git ~/mtg-data
cd ~/mtg-data
```

Give it this minimal structure so the layout is committed but the database is ignored:

**`~/mtg-data/.gitignore`**

```gitignore
# Large, rebuildable Scryfall cache — kept out of routine syncs (the mtg-db skill
# force-adds cards.sqlite via Git LFS only when you opt in with --push-database).
database/
# OS/editor noise
.DS_Store
Thumbs.db
```

If you want the optional database-over-LFS flow (below), also add a `.gitattributes`:

```gitattributes
database/cards.sqlite filter=lfs diff=lfs merge=lfs -text
```

**`~/mtg-data/README.md`** (optional, but handy on GitHub mobile)

```markdown
# mtg-data
My Magic: The Gathering decks & collection, synced across machines for the
claude-mtg-skills plugin. Set `MTG_HOME` to this folder on each machine.
```

Create the two tracked folders (the `.keep` files just let empty dirs be committed):

```bash
mkdir -p decks collection
touch decks/.keep collection/.keep
git add . && git commit -m "Initialize mtg-data workspace" && git push
```

### 2. Point the skills at it with `MTG_HOME`

Set `MTG_HOME` to the absolute path of your clone. Make it permanent so every shell — and Claude Code —
sees it.

**macOS / Linux** (zsh — adjust for bash with `~/.bashrc`):

```bash
echo 'export MTG_HOME="$HOME/mtg-data"' >> ~/.zshrc
source ~/.zshrc
```

**Windows** — clone wherever you like (the different filesystem doesn't matter; you set the path here):

```powershell
# clone first, e.g. to your user folder:
git clone https://github.com/<you>/mtg-data.git $HOME\mtg-data
# set MTG_HOME permanently for your user (new terminals pick it up):
setx MTG_HOME "$HOME\mtg-data"
```

> On Windows, also tell git not to rewrite line endings in your deck files:
> `git config --global core.autocrlf input` (run once). The skills only write UTF-8 text, so this keeps
> diffs clean across OSes.

### 3. Verify and build the database once per machine

```bash
# from anywhere, confirm the skills now resolve into your data repo:
python <skill>/scripts/scryfall_search.py --paths
# → "from_env": true, and home/decks/collection all under your mtg-data clone.

# build the local card cache into $MTG_HOME/database/ (one-time, ~30 s):
python <skill-or-database-skill>/scripts/build_database.py
```

Or just ask Claude to build a deck — it auto-builds the database on first use, now inside `MTG_HOME`.

---

## The daily loop

With the **mtg-sync** skill set up, **there is no manual loop** — the deck skills pull before they
build and push after they save, automatically. Build a deck on your laptop, and it's on your other PC
and phone the next time you pull there.

Under the hood, that's just:

```bash
python <mtg-sync>/scripts/sync.py --pull           # before a build (the deck skill runs this)
# ... build/upgrade a deck; deck.md + import list land in $MTG_HOME/decks/<slug>/ ...
python <mtg-sync>/scripts/sync.py --push -m "Add Atraxa superfriends deck"   # after (deck skill runs this)
```

…which is equivalent to a `git pull --rebase` then `git add decks collection && git commit && git push`
in `$MTG_HOME`. Best-effort: if you're offline it's a no-op and the deck is still saved locally — push it
later with `python <mtg-sync>/scripts/sync.py --push`, or just *"sync my decks"*. Because each deck lives
in its own folder, conflicts are practically impossible.

---

## Optionally syncing the card database (Git LFS)

The card database is a rebuildable cache, so by default it's git-ignored and **not** synced — each
machine rebuilds it in ~30 s and routine deck syncs stay small. But you can also **share the exact
built `cards.sqlite`** across machines, so a second computer fetches it instead of re-downloading
540 MB from Scryfall and rebuilding (and so prices stay identical everywhere).

Because `cards.sqlite` is ~170 MB — over GitHub's **100 MB** per-file limit on plain git — it's
stored with **[Git LFS](https://git-lfs.com)**. The setup is automatic: `--bootstrap` / `--init`
write a `.gitattributes` rule tracking `database/cards.sqlite` and, if the `git-lfs` extension is
installed, run `git lfs install` for you. Install Git LFS once per machine (`git lfs install`, or
`brew install git-lfs` / your package manager).

```bash
# After you (re)build the database, ship it (the mtg-db skill offers to do this):
python <mtg-sync>/scripts/sync.py --push-database -m "Refresh card data (2026-06)"

# On another / a new machine, fetch the shared database instead of rebuilding:
python <mtg-sync>/scripts/sync.py --pull-database
```

- `--push-database` force-adds `cards.sqlite` + `meta.json` past the `database/` ignore rule, commits,
  and pushes them through LFS. It's **best-effort**: if the workspace isn't a synced repo, or `git-lfs`
  isn't installed, it prints `skipped` and the database simply stays local and rebuildable.
- The heavy file ships **only** through these two commands — never on a routine deck `--push` — so
  building a deck never re-uploads 170 MB.
- If you `--pull-database` (or clone) on a machine **without** `git-lfs`, `cards.sqlite` lands as a tiny
  LFS *pointer* stub rather than the real file. The skills detect that and rebuild the database locally
  instead of trying to read the stub, so nothing breaks — install Git LFS and re-run `--pull-database`
  to get the shared copy.

---

## On each environment

| Environment | What you do | Result |
|---|---|---|
| **This Mac** | `MTG_HOME` set in `~/.zshrc`; clone at `~/mtg-data` | Full build + sync |
| **Windows PC** | `setx MTG_HOME`; clone anywhere | Full build + sync — path differences don't matter |
| **Mobile** | Clone `mtg-data` cleanly (e.g. **Working Copy** on iOS, or just read it on the GitHub app) | Browse every `deck.md` guide; they render as formatted Markdown. Building new decks isn't expected on a phone — viewing is |

Cloning the skills repo "cleanly" on any of these stays clean: your personal data lives in the **separate**
`mtg-data` repo, never in this open-source one.

---

## Optional: Moxfield as a pretty mirror

When you want the native MTG experience on a phone — nice card images, the deck playtester, sharing —
mirror a deck into Moxfield by hand (a 30-second copy/paste, no API needed):

1. **Create the deck:** New deck → **Import** → paste the contents of `decks/<slug>/import.txt`
   (Commander) or `arena.txt` (Standard).
2. **Carry the guide over:** paste `decks/<slug>/deck.md` into the deck's **Description / primer** field —
   Moxfield renders Markdown, so your annotated guide shows up formatted.
3. Set the deck **Private** or **Unlisted** if you don't want it public.

Your collection export *comes from* Moxfield (or Arena / Archidekt) in the first place — export it and drop
the file into `collection/` so the skills can build from what you own. Git remains the source of truth; the
Moxfield copy is just the view.
