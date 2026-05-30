---
name: mtga-standard-deckbuilder
description: >-
  Build a 60-card Standard-format deck for MTG Arena (MTGA), centerpiece-first, tuned against the current
  ladder meta, and costed in Arena wildcards by rarity. Use whenever the user wants to build, brew, or
  netdeck a Standard deck for Arena, names a card and asks to build a Standard deck around it, wants a deck
  for the BO1 ladder or BO3 with a sideboard, asks what to craft for a budget number of wildcards, or wants
  a deck that beats the current Standard meta. Triggers on phrases like "build me a Standard deck", "MTGA
  deck for [card]", "brew around [card] in Standard", "budget Arena Standard deck", "what should I craft",
  or any request pairing Standard/Arena with deckbuilding. Every card is labeled with its rarity and the
  build respects a wildcard budget tier (1-5). Verifies legality and rarity via Scryfall, reads the live
  meta from untapped.gg/mtggoldfish, and outputs an Arena import list plus an annotated wildcard-cost
  breakdown. Starts by asking for the user's MTG Arena collection export and, when given one, builds
  primarily from cards they already own — spending wildcards only to upgrade or fill gaps. For 60-card
  Standard, NOT 100-card Commander/EDH.
---

# MTG Arena Standard Deck Builder

This skill brews a 60-card **Standard** deck for **MTG Arena**. It blends a creative, centerpiece-first
building method (pick a card you love, find everything it can do, build the synergy web around it) with
the practical reality of Arena: the deck has to **beat the current ladder meta**, it has to be **legal in
Standard right now**, and you have to be able to **afford it in wildcards**.

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
   the target tier, the match type (BO1/BO3), and a short "how the deck wins + meta plan" paragraph.
2. **Arena import list** (`arena.txt`) — exact MTG Arena import format: a `Deck` header, then
   `<count> <Card Name>` per line; a blank line then `Sideboard` and 15 cards if BO3. Generate this *from*
   the annotated list so they can't drift.

Use `present_files` to share both, and **save them in their own folder under `.mtg/decks/`** in the
user's current working directory: `.mtg/decks/<deck-slug>/deck.md` and
`.mtg/decks/<deck-slug>/arena.txt`. Create the folder if it doesn't exist. The slug is a short
kebab-case deck name (the centerpiece or archetype, e.g. `.mtg/decks/mono-red-aggro/` or
`.mtg/decks/dimir-bounce/`); add a distinguishing suffix for variants so existing decks aren't
overwritten. See "The `.mtg` workspace" below.

## The `.mtg` workspace

All of this skill's file I/O lives in a `.mtg/` directory in the user's current working directory,
conventionally git-ignored (built output and personal collection data, not source).

**If there's no clear working directory to write to** — e.g. you're running in an interactive chat with no
project folder — **ask the user where the `.mtg/decks/` and `.mtg/collection/` directories should live**
(prompt for a path) before reading or writing anything, and use that location for the rest of the session.

The subdirectories:

- **`.mtg/decks/`** — where built decks are written. **Each deck gets its own subfolder**,
  `.mtg/decks/<deck-slug>/`, holding that deck's two files (`deck.md` and `arena.txt`). Create the
  directories if they're missing. This is the same decks folder the other deckbuilding skills use.
- **`.mtg/collection/mtga_collection.txt`** — the user's **Arena collection** (which cards, and how
  many, they own), as a plain `<count> <Card Name>` export. This is the **starting inventory for
  every build** and the single biggest lever on deck quality — see "First: load the user's Arena
  collection" below for how to obtain, confirm, and use it. A card the user already owns the needed
  copies of costs **0 wildcards**; the wildcard budget pays only for the gaps you fill by crafting.

## First: load the user's Arena collection

**Before anything else, get the user's MTG Arena collection.** The deck is built primarily from
cards they already own, so this is the single biggest lever on deck quality — say so plainly: an
up-to-date export lets the builder construct a deck the user can play *today* and spend wildcards
only where they truly move the needle. The collection lives at
**`.mtg/collection/mtga_collection.txt`** (a plain `<count> <Card Name>` export). Handle two cases:

- **No collection file present** → ask the user to export their collection to
  `.mtg/collection/mtga_collection.txt`, and recommend the free exporter
  **https://github.com/NthPhantom10/MTGA-collection-exporter** (it produces exactly that
  `<count> <Card Name>` list from the MTGA client). Make clear it's strongly recommended: without it
  you build from the whole Standard pool and cost every non-basic card in wildcards from zero, which
  is far less tailored. If the user declines, proceed without it and note the trade-off.
- **Collection file present** → ask the user whether it's **up to date** and whether to **use it**
  for this build. If it's stale, offer to let them re-export with the same tool and replace the
  file. Once confirmed, read it fully.

**Whenever a collection is available, use it for every build** and treat it as the starting
inventory for all steps below.

## Before you build: confirm three things

1. **Centerpiece or archetype.** What's the deck built around — a specific card the user loves, or a
   known meta archetype they want tuned/personalized? If they only gave a vibe ("aggro", "tokens"), help
   them pick a centerpiece card in Step 1.
2. **Wildcard budget tier (1-5).** Caps how many wildcards of each rarity the deck may require. Defaults
   and the full table live in `references/wildcard-budget.md`. If unsure, suggest Tier 3.
3. **Match type.** Ask each build: **BO1 ladder** (60 cards, no sideboard — the default ladder experience
   and what untapped.gg's main meta reflects) or **BO3** (60 + a 15-card sideboard). This changes whether
   you build a sideboard and how much you can lean on game-1 meta-teching in the maindeck.

## The method (centerpiece-first brewing)

Full detail and the reasoning behind each step is in `references/methodology.md` — read it before building.
The Scryfall recipes for finding cards are in `references/scryfall-syntax.md`. The short version:

**Build from the collection first, then upgrade.** When a collection is loaded, work owned-cards-out:
for every slot in every step below, first look in the collection for the best card the user already
owns that fits the role, and build the deck from those. Only then *upgrade* — spend a wildcard to
replace an owned card when a better card meaningfully improves the deck for its goal and tier. If a
slot or gap has **no** suitable owned card, then of course add (craft) the card the deck needs.
Order of preference at every decision: **owned card that fits → craft to fill a real gap → craft to
upgrade**. The result is a deck the user can mostly play immediately, with wildcards spent only
where they matter. (With no collection loaded, build from the full Standard pool as normal.)

### Step 1 — Pick the centerpiece
Start from one card: the thing that wins the game or that the user loves. Commit to it (often a 4-of). If
they want a meta deck instead, the centerpiece is the archetype's core engine. The whole deck exists to
make this card great.

### Step 2 — Interrogate it deeply (find the hidden axes)
Don't stop at the obvious read. A card almost always has **several** exploitable axes, and the good brews
come from the non-obvious ones. Enumerate them:
- **Which ability to build around** — if a card has two modes, pick the one that's most fun/powerful and
  lean all the way in rather than splitting focus.
- **Hidden synergy axes** — e.g. a card that makes token copies isn't just "ETB value"; it's *also* attack
  triggers (haste tokens swing in) *and* sacrifice fodder (tokens that die feed death-triggers and sac
  outlets). List every angle.
- **Rules-text subtleties** — read the actual text, not just the keyword. "Landfall" literally means "when
  a land enters", so it's an ETB trigger that ETB-*doublers* can copy. Power/toughness thresholds open
  combos (an effect that doubles abilities of power-≤2 creatures will double a 1-power commander's passive
  trigger). These "breaks" are where original decks come from.

### Step 3 — Build the synergy web
Find cards that give **2-for-1s** with the centerpiece along the axes you listed, and that synergize with
*each other*. Hunt for the non-obvious interaction that speeds the deck up "tenfold." Use EDHREC-style
aggregators sparingly here (this is Standard, not EDH) — lean on the meta sites and Scryfall oracle-text
searches (`references/scryfall-syntax.md`). **With a collection loaded, scan it first** for cards that
fill each axis and build from those; reach into the wider pool only to upgrade an owned piece or to fill
a synergy slot the collection can't cover.

**Check in on the direction here.** Before building the full 60, tell the user the plan in a couple of
sentences — the centerpiece and the axis you're leaning into, how the deck wins, and a few signature cards
— and ask if that's the deck they want. This is the cheapest moment to change course (go more aggressive,
pick the other ability, stay closer to what they own, spend fewer wildcards). Adjust to their answer, then
build.

### Step 4 — Don't overbuild (avoid win-more)
Resist stapling a second payoff onto an engine that's already sufficient. A redundant bomb you cast when
you're already winning is wasted slots and tempo; spend those slots on consistency and answers instead.
One robust engine beats two fragile ones.

### Step 5 — Read the meta
The deck must *compete*, not just combo in a vacuum. Pull the current Standard ladder meta (untapped.gg
BO1, and mtggoldfish) and note the top decks — typically a fast aggro deck (often mono-red), one or two
midrange decks, and a control or go-wide deck. Knowing the field tells you what you must survive.

### Step 6 — Tech against the meta (answers)
For each major matchup, make sure the deck has answers, and pick answers that don't hurt your own plan:
- vs **aggro** → cheap early removal, a sweeper or two, and life gain.
- vs **midrange/discard** → card advantage to refuel after they strip your hand.
- vs **go-wide/auras/ward** → sweepers, enchantment removal, ways around ward.
- vs **graveyard/reanimator** → graveyard hate (instant-speed exile, a static "exile graveyards" piece).
- **Match the sweeper to your own board** — a tokens deck runs a clean wrath rather than a "lock down
  cheap permanents" effect that would also catch its own tokens. Look for removal that pairs (one card
  cleans up the side effect of another).

### Step 7 — Build the mana base to the deck's speed (the hard part)
The land base must match the curve and game plan:
- **Aggro / low curve (win by turn 3-4):** lands that enter untapped early (fast lands) plus pain lands —
  you accept the life loss because the game is short. Avoid taplands that cost you tempo.
- **Midrange / control / tokens (longer games):** utility and synergy lands — creature-lands (the
  Restless cycle), value lands (e.g. Fountainport, Mirrex), and colorless lands that match your theme
  (search Scryfall colorless lands by keyword like "token" or "artifact"). Some taplands/duals are fine.
- More colors = harder mana; commit to the best fixing for your speed. Typical land counts: ~17 lands
  for hyper-aggro, ~24 for midrange, ~26 for control. **Watch the wildcard cost here** — premium duals
  are often rare, so at low tiers the mana base leans on basics and common/uncommon lands.

### Step 8 — Assemble, cost, and fit the tier
Build to exactly 60 (plus 15 sideboard for BO3) — **owned cards first**, then the crafts needed to
upgrade or fill gaps. Use 4-ofs for the cards you always want, fewer for situational ones. Then compute
the **wildcard cost**, counting only the copies the user does **not** already own (owned copies are free;
basics are always free) against the tier caps. If it's over, first downgrade the most expensive
non-essential crafts back to a suitable **owned** card, then to a cheaper card that does a similar job, or
trim copies — lean on the meta knowledge so you cut the least important pieces. See
`references/wildcard-budget.md` for the optimization logic.

### Step 9 — Present the list and refine before writing files
**Show the user the finished list before you save anything.** Walk them through it briefly — how it wins,
the meta plan, the mana base, and the **wildcard cost / what they'd need to craft** — and call out any
close calls. Invite changes: cards they own and want to use instead, a lower wildcard spend, a different
answer for a matchup they care about. Make the swaps they ask for (re-checking the 60-card count, legality,
and the tier each time) and keep going until they're happy. **Only then** run the quality checks below and
write the two files.

## Data sources

- **Scryfall** — the source of truth for **Standard legality**, **rarity**, **Arena availability**, mana
  cost, type, and oracle text. Key filters (full cookbook in `references/scryfall-syntax.md`):
  `legal:standard` (legal *and* not banned), `game:arena` (exists on Arena), `r:rare` / `r:mythic` etc.
  Every card object has a `rarity` field — surface it for every card.
- **untapped.gg** (`https://mtga.untapped.gg/constructed/standard`) — the live **BO1 ladder meta** and
  "what's in Standard" set list. The primary read on the field you're teching against.
- **mtggoldfish** (`https://www.mtggoldfish.com/metagame/standard`) — Standard metagame %s and full
  netdeck lists; good for BO3 and for sample mana bases.

**Retrieval mechanics (use what's available, in order):**
- **Code execution with network** → run `python scripts/scryfall_search.py "<query>" --limit 30` to search
  (Standard-legal + Arena by default, rarity shown), and
  `python scripts/scryfall_search.py --deck <import>.txt --tier <N>` to tally the wildcard cost of a
  finished list and check it against the tier caps. Run `--help` for options.
- **No code-exec network, but web tools** → `web_search` for the Scryfall query / untapped.gg / mtggoldfish
  page, then `web_fetch` the result (web_fetch only takes URLs from a prior search, so search first).
- **Neither** → tell the user the environment needs network to `api.scryfall.com`, `untapped.gg`, and
  `mtggoldfish.com`, and offer to proceed from known knowledge with the caveat that legality, rarity, and
  the current meta are unverified (important: Standard rotates and Arena availability varies, so flag this
  clearly).

When a collection is in use, the wildcard breakdown must reflect it: count only the cards/copies the user
does not already own, and list exactly what they need to craft. Re-read the owned list when reconciling
the two files so nothing the user already has is mistakenly counted as a craft.

## Quality bar before you hand it over

- **Reconcile the two files.** Generate the Arena `.txt` from the annotated list, then verify it sums to
  exactly **60** (main) and **15** (sideboard, if BO3), with at most 4 of any non-basic card. Quick check:
  `awk '/^Sideboard/{s=1} /^[0-9]/{if(s)sb+=$1; else md+=$1} END{print "main",md,"side",sb}' <file>.txt`.
- **Legality & Arena availability:** every non-basic card is `legal:standard` and on Arena. No banned cards.
- **Wildcard budget:** **rare and mythic** totals are within the tier's caps (the hard gate) — or the
  user has okayed an overage. Count only the copies the user still needs to craft (owned copies from
  `.mtg/collection/` cost nothing); count from zero if no collection is present. **Common and uncommon**
  are soft targets (cheap, usually
  owned): report the totals but don't block on them. Always show the breakdown.
- **Meta plan:** the deck has real answers for the top 2-3 ladder decks, and the mana base matches its
  speed. Curve and land count are sensible for the archetype.
- Rarity is labeled on every card in the annotated list.

Then present both files.
