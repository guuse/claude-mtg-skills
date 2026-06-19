---
name: mtg-std-build
description: >-
  Build a 60-card Standard-format deck for MTG Arena (MTGA), centerpiece-first, tuned against the current
  ladder meta, and costed in Arena wildcards by rarity. Use whenever the user wants to build, brew, or
  netdeck a Standard deck for Arena, names a card and asks to build a Standard deck around it, wants a deck
  for the BO1 ladder or BO3 with a sideboard, asks what to craft for a budget number of wildcards, or wants
  a deck that beats the current Standard meta. Triggers on phrases like "build me a Standard deck", "MTGA
  deck for [card]", "brew around [card] in Standard", "budget Arena Standard deck", "what should I craft",
  or any request pairing Standard/Arena with deckbuilding. Every card is labeled with its rarity and the
  build respects a wildcard budget tier (1-5). Verifies legality and rarity via Scryfall, and starts from
  the live competitive metagame and real, current decklists pulled from mtgtop8.com — building
  meta-relevant, cohesive decks by adapting proven tournament lists to the user's collection and wildcard
  budget rather than brewing a 60 from scratch — then outputs an Arena import list plus an annotated
  wildcard-cost breakdown. Starts by asking for the user's MTG Arena collection export and, when given one,
  builds primarily from cards they already own — spending wildcards only to upgrade or fill gaps. For 60-card
  Standard, NOT 100-card Commander/EDH.
---

# MTG Arena Standard Deck Builder

This skill builds a 60-card **Standard** deck for **MTG Arena** that is **meta-relevant and cohesive** —
because it starts from **real, current tournament decklists** (pulled from mtgtop8.com), then adapts a proven
list to the player: their **centerpiece or chosen archetype**, the **current ladder meta** it must beat, what
they already **own**, and what they can **afford in wildcards**. Building from proven lists rather than
assembling 60 cards from scratch is the whole point — it's what keeps the deck's ratios, mana base, and game
plan intact instead of producing something basic that falls apart on ladder. A pet card gets **grafted into
the proven shell that best supports it** rather than spawning a from-scratch brew.

Two things make this different from paper deckbuilding, and both are first-class here:
- **Rarity is shown on every card.** In Arena you craft cards with wildcards of matching rarity, so the
  rarity *is* the cost. Always label each card C / U / R / M.
- **Budget is measured in wildcards, not money.** The user picks a tier (1-5) that caps how many commons,
  uncommons, rares, and mythics the deck may require. See `references/wildcard-budget.md`.

**Build it with the user, not just for them.** After you've settled the centerpiece and the synergy
direction, check in on the **plan** before committing to a full 60, and present the near-final list for
reaction before writing files — invite them to swap in cards they own/love, spend more or fewer wildcards,
or change the angle. Don't hand over a finished list as the first thing they see. Keep it light (fewer
check-ins than an upgrade) but never one-shot: confirm the plan, then confirm the list.

## The deliverable

Always produce **two files** (the user wants both):

1. **Annotated decklist** (`deck.md`) — cards grouped by role (Centerpiece/Payoffs,
   Creatures, Removal/Interaction, Card Advantage, Other Spells, Lands; plus Sideboard for BO3). Every
   line shows count, card name, **rarity (C/U/R/M)**, and a one-line reason. Include the mana curve, the
   land count, the **wildcard-cost breakdown** (commons/uncommons/rares/mythics required vs the tier cap),
   the target tier, the match type (BO1/BO3), a short "how the deck wins + meta plan" paragraph, and a
   **Deck Rating** section — an overall ★ rating (out of 5) for the deck on the current ladder at its tier,
   plus the per-dimension scorecard (see "Step 9 — Rank the finished deck").
2. **Arena import list** (`arena.txt`) — exact MTG Arena import format: a `Deck` header, then
   `<count> <Card Name>` per line; a blank line then `Sideboard` and 15 cards if BO3. Generate this *from*
   the annotated list so they can't drift.

Use `present_files` to share both, and **save them in their own folder under `.mtg/decks/std/`** in the
user's current working directory: `.mtg/decks/std/<deck-slug>/deck.md` and
`.mtg/decks/std/<deck-slug>/arena.txt`. Create the folder if it doesn't exist. (MTG Arena Standard decks
live under `decks/std/`; Commander/EDH decks live under `decks/edh/`.) The slug is a short
kebab-case deck name (the centerpiece or archetype, e.g. `.mtg/decks/std/mono-red-aggro/` or
`.mtg/decks/std/dimir-bounce/`); add a distinguishing suffix for variants so existing decks aren't
overwritten. See "The `.mtg` workspace" below.

## The `.mtg` workspace

All of this skill's file I/O lives in one **workspace** directory holding three subfolders —
`database/`, `decks/`, and `collection/`. It is resolved in this order:

1. **`$MTG_HOME`**, if that environment variable is set — the user's portable data location (e.g. a
   private `mtg-data` git repo they clone on each machine so decks + collection follow them
   everywhere; see the repo's `SYNCING.md`). Use it even if some subfolders don't exist yet — create them.
2. Otherwise the nearest **`.mtg/`** at or above the current working directory (conventionally
   git-ignored: built output and personal data, not source).

To see the resolved locations any time, run **`python scripts/scryfall_search.py --paths`** — it prints
the `decks/`, `collection/`, and `database/` paths as JSON (honouring `$MTG_HOME`) and creates nothing.
The `.mtg/…` paths written elsewhere in this skill are shorthand for "inside the resolved workspace."

**If `$MTG_HOME` is unset and there's no clear working directory to write to** — e.g. an interactive chat
with no project folder — **ask the user where the workspace should live** (prompt for a path, or suggest
they set `$MTG_HOME`) before reading or writing anything, and use that location for the rest of the session.

The subdirectories:

- **`.mtg/decks/`** — where built decks are written, **split by format**: MTG Arena Standard under
  `.mtg/decks/std/` and Commander/EDH under `.mtg/decks/edh/`. **Each deck gets its own subfolder** —
  for this skill, `.mtg/decks/std/<deck-slug>/`, holding that deck's two files (`deck.md` and
  `arena.txt`). Create the directories if they're missing. This is the same decks folder the other
  deckbuilding skills use.
- **`.mtg/collection/`** — the user's **Arena collection** (which cards, and how many, they own),
  as a **`.txt`**, **`.csv`**, or **`.json`** export (e.g. `mtga_collection.txt`). This is the
  **starting inventory for every build** and the single biggest lever on deck quality — see "First:
  load the user's Arena collection" below for how to obtain, confirm, and use it (it's loaded with the
  bundled `--collection` helper, which accepts any of those formats). A card the user already owns the
  needed copies of costs **0 wildcards**; the wildcard budget pays only for the gaps you fill by crafting.

### Keeping decks in sync across machines (mtg-sync)

Decks live in the user's `mtg-data` git repo, and the user wants **every build to pull at the start
and push at the end** — the same way card data comes from mtg-db. **Don't try to judge whether
syncing is set up before acting — always run the sync commands and let the helper tell you.**
`sync.py` returns `skipped` when the workspace isn't a git repo, so an unconditional call is safe
everywhere; guessing whether to run it is exactly what makes pushing flaky.

- **At the start**, before loading the Arena collection or writing anything, invoke **mtg-sync** to
  pull (`--pull`). This first brings down decks/collection built on another machine.
- **As the final action of the build** (see **Final step — always commit & push** at the end of this
  skill), invoke **mtg-sync** to push (`--push -m "<archetype>"`), so the new deck lands on the repo's
  main branch and is available everywhere. This push runs **every time**, not only when you think sync
  is configured.

**Only the *result* is best-effort.** If the push reports `skipped` (syncing isn't set up) or
`FAILED` (e.g. offline), note it in one line and continue — the deck is saved locally and can be
pushed later. Never skip the *attempt*. To set syncing up the first time, use the **mtg-sync** skill
(`--bootstrap`).

## First: load the user's Arena collection

**Before anything else, get the user's MTG Arena collection.** The deck is built primarily from
cards they already own, so this is the single biggest lever on deck quality — say so plainly: an
up-to-date export lets the builder construct a deck the user can play *today* and spend wildcards
only where they truly move the needle.

The export lives in **`.mtg/collection/`** and can be any of the three shapes the common Arena
exporters produce — **`.txt`** (a plain `<count> Card Name` list), **`.csv`** (a header row with
name/quantity columns, e.g. Moxfield's `Count,Name,…`), or **`.json`** (an array of `{name, quantity}`
objects, or a `{name: count}` map). **Don't hand-parse it** — run the bundled helper, which finds the
file (whichever extension) and normalises it to a clean `<count> Card Name` list regardless of format:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --collection
```

(Pass an explicit path — `--collection <file>` — if the export lives elsewhere.) Handle two cases:

- **The helper reports no file found** → ask the user to drop an export into `.mtg/collection/`
  (any of `.txt`/`.csv`/`.json`), and recommend the free exporter
  **https://github.com/NthPhantom10/MTGA-collection-exporter**. Make clear it's strongly recommended:
  without it you build from the whole Standard pool and cost every non-basic card in wildcards from
  zero, which is far less tailored. If the user declines, proceed without it and note the trade-off.
- **A collection is found** → the helper prints the card total and the format it parsed. If it prints
  a `NOTE:` (e.g. a JSON export keyed only by Arena IDs it can't map to names), relay it and ask for a
  name-based export. Ask the user whether it's **up to date** and whether to **use it** for this build;
  if it's stale, offer a re-export. Once confirmed, use the normalised list as the inventory.

**Whenever a collection is available, use it for every build** and treat it as the starting
inventory for all steps below.

## Before you build: confirm three things

1. **Centerpiece or archetype.** What's the deck built around — a specific card the user loves, or a
   known meta archetype they want tuned/personalized? If they only gave a vibe ("aggro", "tokens"), help
   them pick a centerpiece card in Step 1.
2. **Wildcard budget tier (1-5).** Caps how many wildcards of each rarity the deck may require. Defaults
   and the full table live in `references/wildcard-budget.md`. If unsure, suggest Tier 3.
3. **Match type.** Ask each build: **BO1 ladder** (60 cards, no sideboard — the default ladder experience
   and what the BO1 ladder meta reflects) or **BO3** (60 + a 15-card sideboard). This changes whether
   you build a sideboard and how much you can lean on game-1 meta-teching in the maindeck.

## The method (netdeck-anchored, then personalized)

Full detail and the reasoning behind each step is in `references/methodology.md` — read it before building.
The single biggest change from naive brewing, and the reason earlier builds came out basic and incohesive:
**a Standard deck has to be a real, current, cohesive meta list — so start from proven decklists pulled from
mtgtop8 and adapt them to the user, rather than assembling 60 cards from scratch.** From-scratch synergy
brewing (the `references/synergy.md` loop) is now a **tool for grafting a pet card into a proven shell and for
picking flex slots** — not the primary way you build.

**Build from the collection, but never at the cost of cohesion.** When a collection is loaded, prefer the
cards the user already owns *to fill the proven list's slots* — keep their copies, count only the gaps as
crafts. Deviate from the netdeck only when an owned card is a genuine **like-for-like** (same role and roughly
the same power) or a deliberate centerpiece choice. Resist random "I own this instead" substitutions and
extra pet cards — that swap-by-swap drift is exactly what breaks a netdeck's ratios and makes it underperform.
Order of preference per slot: **proven card the user owns → craft the proven card → owned like-for-like swap →
cheaper proven-role substitute.** (With no collection loaded, build the proven list and cost every non-basic.)

### Step 1 — Pull the live meta and real decklists (do this first)
Run the bundled fetcher to see the actual current field and grab proven lists to build from:

```
python "${CLAUDE_SKILL_DIR}/scripts/mtgtop8_fetch.py" --meta             # current archetypes + shares + ids
python "${CLAUDE_SKILL_DIR}/scripts/mtgtop8_fetch.py" --archetype <id>   # recent decklists for one archetype
python "${CLAUDE_SKILL_DIR}/scripts/mtgtop8_fetch.py" --deck <id>        # one decklist, importable lines
python "${CLAUDE_SKILL_DIR}/scripts/mtgtop8_fetch.py" --top --per 2      # meta + a few real lists per top archetype
```

**mtgtop8.com is the one bot-fetchable source of current decklists** — untapped.gg, mtggoldfish, mtgdecks,
and aetherhub all Cloudflare-block automated fetches, but mtgtop8 serves plain HTML and a plain-text export
(see `references/data-sources.md`). The lists are real tournament results from the last couple of weeks. If
the fetch fails, **say mtgtop8 was unavailable**, fall back to your own meta knowledge **flagged UNVERIFIED**,
and invite the user to paste a netdeck (a Moxfield/Archidekt link works via `scripts/import_deck.py <url>`).
Never invent a metagame percentage or a decklist.

### Step 2 — Choose the archetype (or place the centerpiece in a real shell)
- **Meta deck (the default):** pick the archetype from the live meta — by name, by colors, by "what beats the
  field", or by what their collection/budget is closest to. The archetype *is* the centerpiece; the whole
  deck already exists to do one thing well.
- **Pet card / "build around X":** find the **real archetype that already plays X**, or the closest proven
  shell its colors and role fit, from the meta you just pulled (plus your knowledge). The plan is to **graft X
  into that cohesive shell**, not invent a deck around it. Only a genuinely fringe card with no existing home
  falls back to from-scratch brewing (`references/methodology.md`) — and you tell the user plainly that it's
  experimental and usually weaker than a tuned meta deck.

### Step 3 — Build the backbone from the consensus of 2–3 real lists
Pull **2–3 recent lists** for the chosen archetype (`--archetype <id>` then `--deck <id>`, or `--top`). The
cards that appear in (almost) every copy are the archetype's **load-bearing core** — take them at the counts
the lists run (4-ofs stay 4-ofs). Where the lists disagree are the **flex slots** — choose among those by the
meta read and the user's budget/collection. This consensus is what gives the deck its cohesion and correct
ratios; **keep the proven counts unless you have a concrete reason to change one.**

**Interrogate the centerpiece only for the graft.** When slotting a pet card into a shell, use the deep-read
habit from `references/methodology.md` (which ability to lean on, hidden axes, rules-text subtleties) and the
`references/synergy.md` scoring loop to decide **what it replaces and the 2–3 cheap enablers it needs** to pull
its weight. Be surgical — change the fewest proven cards required, so the result is still a real list.

**Check in on the direction here.** Before building the full 60, tell the user the plan in a couple of
sentences — the archetype, which real lists you're anchoring to (name the players/events from mtgtop8), how it
wins, and any centerpiece graft — and ask if that's the deck they want. This is the cheapest moment to change
course (different archetype, lean harder on owned cards, spend fewer wildcards). Adjust, then build.

### Step 4 — Don't overbuild (avoid win-more)
Resist stapling a second payoff onto an engine that's already sufficient, or padding the proven list with extra
pet cards. A redundant bomb you cast when you're already winning is wasted slots and tempo; spend those slots on
consistency and answers instead. One robust engine beats two fragile ones — and the proven list already made
these cuts, so respect them.

### Step 5 — Tech against the rest of the field (answers + sideboard)
You pulled the meta in Step 1 — now use it. Note the top 2–3 decks you must beat (typically a fast aggro deck,
a control deck, and a midrange or combo deck) and make sure the list answers them, picking answers that don't
hurt your own plan:
- vs **aggro** → cheap early removal, a sweeper or two, and life gain.
- vs **midrange/discard** → card advantage to refuel after they strip your hand.
- vs **go-wide/auras/ward** → sweepers, enchantment removal, ways around ward.
- vs **graveyard/reanimator** → graveyard hate (instant-speed exile, a static "exile graveyards" piece).
- **Match the sweeper to your own board** — a tokens deck runs a clean wrath rather than a "lock down cheap
  permanents" effect that catches its own tokens. Look for removal that pairs (one card cleans up another's
  side effect). The maindeck answers in the proven lists already reflect the field — start from theirs.
- **Sideboard (BO3):** the real 15s on the mtgtop8 lists are your starting point — adapt them to your exact
  build and the matchups you care about, don't reinvent them from scratch.

### Step 6 — Keep the proven mana base (adjust only for budget)
Start from the **mana base of the lists you anchored to** — counts, duals, utility/creature-lands and all.
A netdeck's mana is tuned to its curve and colors; that's most of what makes it run. Only change it to fit the
wildcard budget or the user's collection:
- premium duals/creature-lands are often **rare**, so at low tiers swap the least important ones for
  basics or common/uncommon taplands and pain lands, keeping the colored-source counts as close as you can.
- if a card the user owns shifts the curve or colors slightly, re-balance sources to match.
Sanity-check against the archetype's speed (≈17–20 lands hyper-aggro, ~24 midrange, ~26 control) but trust the
proven base over a theoretical count.

### Step 7 — Assemble, cost, and fit the tier
Build to exactly 60 (plus 15 sideboard for BO3) from the consensus core + flex picks — **owned copies first**,
then the crafts needed to complete the proven list. Then compute the **wildcard cost**, counting only the
copies the user does **not** already own (owned copies are free; basics are always free) against the tier caps.
If it's over, downgrade the most expensive **non-core** flex cards first — to an owned like-for-like, then to a
cheaper proven-role substitute, then trim copies. **Protect the load-bearing core**; cut from flex and the mana
base before you touch the cards that define the archetype. See `references/wildcard-budget.md`.

### Step 8 — Present the list and refine before writing files
**Show the user the finished list before you save anything.** Walk them through it briefly — the archetype and
which real lists it's based on, how it wins, the meta plan, the mana base, and the **wildcard cost / what they'd
need to craft** — and call out any close calls. Invite changes: owned cards they want to use instead (flag any
that weaken cohesion), a lower wildcard spend, a different answer for a matchup they care about. Make the swaps
they ask for (re-checking the 60-card count, legality, and the tier each time) and keep going until they're
happy. **Only then** run the quality checks below, rank the deck (Step 9), and write the two files.

### Step 9 — Rank the finished deck (★ rating)
Once the list is locked, **rate it before writing files** and embed the result in `deck.md`. Apply the
**five-dimension rubric in `references/rating.md`** — consistency & curve, mana base, synergy/payoff density
(via `references/synergy.md`), meta resilience, and wildcard efficiency — rating the deck *for the current
ladder at its tier and match type* (BO1/BO3). Use the data you already gathered: the curve and land count from
Step 6, the wildcard tally from `--deck --tier`, the color audit from `--colors`, the meta read from Steps 1/5,
and **how close the build stayed to its proven source** (a faithful meta list should rate well; heavy deviation
that broke cohesion should cost it). Write a **Deck Rating** section into `deck.md`: the headline (e.g.
`★★★★☆ (4/5) — a strong Tier-3 BO1 ladder deck`), the per-dimension scorecard with the numbers/reasons behind
each, and one line on the deck's biggest remaining weakness. A healthy build should rate well — if a dimension
scores low (e.g. soft to mono-red, or a mana base fighting the curve), fix it before delivering rather than
shipping a low score.

## Data sources

- **Scryfall** — the source of truth for **Standard legality**, **rarity**, **Arena availability**, mana
  cost, type, and oracle text. Key filters (full cookbook in `references/scryfall-syntax.md`):
  `legal:standard` (legal *and* not banned), `game:arena` (exists on Arena), `r:rare` / `r:mythic` etc.
  Every card object has a `rarity` field — surface it for every card.
- **Standard / Arena meta & decklists** — pull the live field and **real, current decklists** from
  **mtgtop8.com** with `scripts/mtgtop8_fetch.py` (`--meta`, `--archetype <id>`, `--deck <id>`, `--top`).
  It's the one **bot-fetchable** source: untapped.gg, mtggoldfish, mtgdecks, and aetherhub all Cloudflare-
  block automated fetches and **must not be scraped**, but mtgtop8 serves plain HTML and a plain-text deck
  export. The lists are real tournament results from the last couple of weeks; exact metagame **shares** lag
  the very latest ladder a little, so treat the percentages as approximate while trusting the lists. If
  mtgtop8 is unreachable, fall back to the model's own meta knowledge **flagged unverified** and invite the
  user to paste a meta snapshot or a netdeck (a **Moxfield/Archidekt link** works via
  `scripts/import_deck.py <url>`). Never present an invented metagame percentage or decklist as fact. See
  `references/data-sources.md`.

**Scryfall reads come from the local card database.** `scripts/scryfall_search.py` queries a **local
SQLite database** (`.mtg/database/cards.sqlite`, built from Scryfall bulk data — see the
**mtg-db** skill) instead of the API. It's built **automatically on first use** (one-time
~540 MB download); just call the script. At the **start**, if it reports the data is **stale (>30 days)**,
tell the user and **ask** whether to refresh before continuing (for Arena this matters less — only rarity,
Arena availability, and Standard legality are used, and those move only when a set releases). Any
`function:`/`otag:` (Tagger) query routes to the live API automatically.

**Retrieval mechanics (use what's available, in order):**
- **Code execution with network** → run `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" "<query>" --limit 30` to search
  (reads the local DB, auto-builds on first use; Standard-legal + Arena by default, rarity shown), and
  `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --deck <import>.txt --tier <N>` to tally the wildcard cost of a
  finished list and check it against the tier caps. Run `--help` for options.
- **No code-exec network, but web tools** → `web_fetch` the Scryfall search page for card data, **and
  `web_fetch` mtgtop8.com for the meta and decklists** — the format page `mtgtop8.com/format?f=ST`, an
  archetype page `mtgtop8.com/archetype?a=<id>&f=ST`, and a list via the plain-text export
  `mtgtop8.com/mtgo?d=<deckid>` (prompt for the verbatim list). Do **not** `web_fetch`
  untapped.gg/mtggoldfish/mtgdecks/aetherhub — they're Cloudflare-protected and 403. No DB can be built
  here — that's the expected fallback.
- **Neither** → tell the user the environment needs network to `api.scryfall.com`, and offer to proceed
  from known knowledge with the caveat that legality, rarity, and the current meta are unverified
  (important: Standard rotates and Arena availability varies, so flag this clearly).

When a collection is in use, the wildcard breakdown must reflect it: count only the cards/copies the user
does not already own, and list exactly what they need to craft. Re-read the owned list when reconciling
the two files so nothing the user already has is mistakenly counted as a craft.

## Quality bar before you hand it over

- **Reconcile the two files.** Generate the Arena `.txt` from the annotated list, then verify it sums to
  exactly **60** (main) and **15** (sideboard, if BO3), with at most 4 of any non-basic card. Quick check:
  `awk '/^Sideboard/{s=1} /^[0-9]/{if(s)sb+=$1; else md+=$1} END{print "main",md,"side",sb}' <file>.txt`.
- **Legality & Arena availability:** every non-basic card is `legal:standard` and on Arena. No banned cards.
- **Colors — double-check castability:** every nonland card is castable in the deck's colors. Vet
  candidates with color identity `id<=<colors>` (NOT `c:`, which also matches multicolor cards you can't
  cast), and run the audit `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --deck <file>.txt --colors <wubrg>` — it must
  print `COLOR CHECK ✓` with zero off-color cards (this catches e.g. a B/U or B/R card slipped into mono-black).
- **Wildcard budget:** **rare and mythic** totals are within the tier's caps (the hard gate) — or the
  user has okayed an overage. Count only the copies the user still needs to craft (owned copies from
  `.mtg/collection/` cost nothing); count from zero if no collection is present. **Common and uncommon**
  are soft targets (cheap, usually
  owned): report the totals but don't block on them. Always show the breakdown.
- **Meta plan:** the deck has real answers for the top 2-3 ladder decks, and the mana base matches its
  speed. Curve and land count are sensible for the archetype.
- Rarity is labeled on every card in the annotated list.
- **Rating included:** `deck.md` carries the **Deck Rating** section from Step 9 (overall ★ for the ladder
  at its tier + the per-dimension scorecard).

Then present both files.

## Final step — always commit & push (every build ends here)

This is the step that gets missed, so treat it as part of the deliverable, not an afterthought.
**After the two files are written and presented, the last thing you do — every single time — is push
them** by invoking the **mtg-sync** skill: `--push -m "<archetype>"`.

Run it **unconditionally**. Do *not* first reason about whether the workspace is a synced repo — just
run it. The helper handles every case and reports back:

- **`ok` (committed + pushed)** → confirm in one line that the deck was pushed to the `mtg-data` repo's
  main branch.
- **`skipped`** → the workspace isn't a synced git repo; say so in one line and stop (offer
  `--bootstrap` via mtg-sync if they'd like syncing set up).
- **`FAILED`** → e.g. offline or an auth issue; say so in one line — the deck is committed/saved
  locally and can be pushed later.

Only the *handling of that result* is best-effort. The **attempt is mandatory** — never end a build
without running the push.
