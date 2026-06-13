---
name: mtg-card-finder
description: >-
  Collaboratively find the right Magic the Gathering cards for a player by brainstorming with them and
  researching card text deeply. Use this skill whenever the user wants help finding cards rather than
  building a whole deck — when they want to pick a commander, fill a specific gap in a deck, add a category
  (more card advantage, ramp, removal, a finisher, protection), find synergy pieces for a theme or combo, or
  solve a problem their deck has ("my deck can't close games", "I keep running out of cards", "I die to board
  wipes", "what's the best removal in these colors"). Triggers on phrases like "help me find cards for…",
  "what commander should I play", "I need more card draw in my deck", "find me cards that synergize with X",
  "what should I add to fix Y", "best cards for this strategy", "recommend cards that do Z", or any open-ended
  card-discovery or deck-problem-solving request that is NOT a full build/upgrade. The skill starts by
  pinning down the *purpose*, gathers tailored context by brainstorming, then researches Scryfall Oracle text
  and typings exhaustively to surface cohesive, high-synergy cards — pinpointing what the user actually needs,
  not just what they asked for. Prices via Scryfall (Cardmarket EUR).
---

# MTG Card Finder & Deck Problem-Solver

This skill helps a player **find the right cards** — and figure out which cards those even are. It is not a
deckbuilder (that's `mtg-edh-build` / `mtg-std-build`) and not a full-list upgrader (`mtg-edh-upgrade` /
`mtg-std-upgrade`). It is the **consultative step before or beside those**: a focused, conversational search
for the cards a specific player needs for a specific purpose — a commander to build around, the missing piece
in a category, the synergy engine for a theme, or the fix for a problem a deck keeps running into.

Two ideas drive everything here:

1. **Brainstorm to find the *real* need, not the stated one.** Players usually arrive with a guess at the
   solution ("I need more removal", "I need a bigger finisher"). Often the guess is wrong — the deck dies to
   board wipes because it overcommits, not because it lacks protection; it "can't close" because it runs out
   of cards three turns before the kill, not because the finisher is too small. **Your job is to diagnose the
   underlying need by talking with the user**, then find cards for *that*. Treat the opening request as a
   symptom to investigate, not a spec to fulfill.
2. **Research card text exhaustively to find cohesion.** Great recommendations come from reading the actual
   **Oracle text and type lines** of many cards and noticing which ones share *multiple* points of contact
   with the user's deck and with each other. A card that touches the theme three different ways is worth ten
   that touch it once. The whole value of this skill over a generic "good cards" list is that it reads the
   wording closely and finds the cards that genuinely cohere.

**This is a conversation, not a one-shot lookup.** Don't dump a list and leave. Pin the purpose, brainstorm
the context, research, then present a *shortlist with reasoning* and refine it with the user. Default to
asking a sharp question over assuming.

## The shape of a session

Work through these phases in order. Phases 1–2 (purpose + brainstorm) are what make the recommendations
*theirs*; Phase 3 (deep card research) is what makes them *good*. Full detail and the diagnostic playbook
live in `references/methodology.md` — **read it before recommending anything** — and the synergy-scoring
loop that decides which cards make the cut is in `references/synergy.md` (**read this too; it is the core
craft**). The Scryfall query cookbook is in `references/scryfall-syntax.md`.

### Phase 1 — Establish the purpose

Before anything else, find out **what kind of card-finding this is.** Ask the user (or infer from their
prompt and confirm) which of these they're after — these are the modes the skill serves:

- **Find a commander** — they want a legendary creature (or other commander) to build a deck around, by
  vibe/playstyle rather than a named card.
- **Fill a gap** — an existing deck is short in a specific area they can name (not enough lands, thin on
  ramp, no board wipes, weak mana fixing) and they want the best cards to fill it.
- **Add / improve a category** — they want the best **card advantage**, **ramp**, **removal**,
  **counterspells**, **protection**, **recursion**, or **finishers** in a given color identity / format.
- **Find synergy pieces** — they have a theme, engine, combo, or a specific card and want cards that
  **synergize** with it (this is the deep-research sweet spot).
- **Solve a problem** — a symptom, not a category: "I run out of cards", "I can't close games", "I flood /
  screw constantly", "I lose to a particular table/deck", "my deck is too slow / too fragile". **This mode
  needs the most brainstorming**, because the stated symptom rarely names the real fix.

If the request spans several modes, that's fine — name them and handle them in priority order. If you can't
tell which mode it is, **ask**. Keep this light: one or two sentences to lock the purpose, then move on.

### Phase 2 — Gather context by brainstorming (branch by mode)

Now gather the context the search needs — **as a brainstorm, not an intake form.** Ask a few pointed
questions, react to the answers, and follow the interesting threads. The goal is to understand the player
and the deck well enough to find cards *they* will love and that *fit*. Tailor the questions to the mode:

**Finding a commander — ask about the player, not just the deck:**
- **Playstyle** — do they like to attack, grind value, control the table, combo off, go wide with tokens,
  go tall with one big threat, play politics/group-hug, durdle and build an engine?
- **What they enjoy and what they hate** — favorite past decks and *why*; play patterns they find boring or
  miserable (mana screw, durdling, getting archenemy'd, non-games).
- **Gimmicks and pet themes** — a tribe, a mechanic (sacrifice, +1/+1 counters, lifegain, mill, spellslinger,
  reanimator, blink, artifacts, lands-matter), an aesthetic, a character they love.
- **Colors** — preferred colors or color count, or "surprise me"; how much they mind a hard 3–5-color mana
  base.
- **Constraints** — budget, power bracket/table level, whether they want something off-meta or proven, and
  any "don't be that guy" lines (no stax, no MLD, no infinite combo) — see `references/brackets.md`.
- Then **propose a few candidate commanders by the rule of cool** (most fun for *this* player) tempered by
  "don't pick something that stops the table playing", with the exact Oracle text and what each would *play
  like*, and let them react. Narrowing to the right commander is itself the deliverable here.

**Filling a gap / adding a category / finding synergy / solving a problem — anchor on the deck:**
- **Get the deck.** Ask them to **paste the decklist** if they have one (a Moxfield/Archidekt export or a
  `1 Card Name` list) — or if they give a Moxfield/Archidekt **link**, run `scripts/import_deck.py <url>`
  to pull it via the site JSON API (falls back to asking for a paste if the deck is private/unreachable).
  Otherwise have them describe the commander/archetype, colors, and game plan. Pull the
  commander's (and any keystone card's) real Oracle text from Scryfall so you work from exact wording.
- **Understand the engine and game plan** — what the deck is *trying to do*, how it currently wins, what its
  best turns look like. You can't judge cohesion without knowing the machine you're adding to.
- **Probe the actual symptom (especially in problem-solving mode).** Don't accept the first diagnosis. Ask
  *when* it goes wrong and *against what*: which turns feel bad, what the board looks like when they lose,
  whether it's a consistency problem (happens every game) or a matchup problem (one table). Trace the symptom
  to a cause before naming cards — see the diagnostic playbook in `references/methodology.md`.
- **Constraints** — color identity (hard limit), format/legality, budget (Cardmarket EUR), power
  bracket/table level, pet cards to keep, and cards already tried that didn't work.

**Pinpoint the real need before you search.** Reflect back what you heard as a crisp problem statement —
*"so the real issue is you have plenty of threats but no way to refuel after a wipe, and you want cheap,
repeatable card advantage that survives a board reset"* — and get the user to confirm or correct it. If your
read differs from their opening request, **say so and explain why**, and let them decide. Only search once
you both agree on what you're actually looking for.

### Phase 3 — Research the card pool deeply (synergy scoring)

This is the skill's craft, and it follows one disciplined loop — **read → extract → map → search →
intersect → score** — documented in full in `references/synergy.md`. **Read that file; it is the heart of
this skill.** The non-negotiable rule it enforces: **every card you recommend must share at least 2–3
synergies ("points of contact") with the deck/commander and ideally with the other cards — and the more
points of contact, the better.** Rank candidates by synergy count and take the densest.

1. **Read the card (this is the irreplaceable, Claude-only step).** Pull the **exact Oracle text and type
   line** of the commander/centerpiece and every serious candidate (`--named "Card Name"`). *You* interpret
   what the card actually does — a tag search can't decide what matters; it only finds what you tell it to.
2. **Extract the key elements** — every actionable concept the card produces or rewards: triggers (*enters,
   attacks, a creature dies, landfall, lifegain*), actions (*sacrifice, create a token, +1/+1 counter, draw,
   blink, recur*), the **types/subtypes** it cares about, **keywords**, and numeric axes. This list is the
   deck's **synergy vocabulary** / shopping list.
3. **Map each element to a Scryfall handle.** Prefer the most specific that exists: curated **Tagger tags**
   `function:` / `otag:` for well-known roles (`otag:sacrifice-outlet`, `function:card-advantage`,
   `otag:token-maker`, `function:ramp`, `otag:flicker`); **oracle text** `o:"…"` for specific phrases;
   **types** `t:…`; **keywords** `keyword:…`. Tags are curated to catch a *role* across different wordings —
   the fast path — and route to the live API automatically; when a tag is thin, union it with the `o:"…"`
   phrasing. (See the mapping table in `references/synergy.md`.)
4. **Search each element within the color identity, then INTERSECT.** Combine handles in one query
   (`id<=BG (o:"whenever a creature" o:"dies") function:card-advantage`) or run them separately and
   cross-reference recurring names. The cards that appear in *several* pools at once are the multi-synergy
   finds — exactly what this skill exists to surface.
5. **Score by points of contact and apply the ≥2–3 floor.** +1 per vocabulary element a card hits, +1 per
   *other* card it specifically combos with. Drop anything scoring below 2–3 (it's a "good card", not an
   engine card). For problem/category work, translate the *cause* into mechanics first (e.g. "refuel after a
   wipe" → repeatable draw / recursion / draw that triggers off something surviving the wipe), then score the
   same way.

**Source proven inclusions first, then fill:** for Commander, start from **EDHREC's JSON API**
(`scripts/edhrec_fetch.py "<commander>"` — its high-"synergy" ranking is gold here), then use **Scryfall**
to fill gaps and dig up spicy multi-synergy cards the aggregate buries; for other formats, lean on Scryfall
plus the model's meta knowledge (flagged unverified). **Vet color
identity and legality as you go** — `id<=<identity>` (NOT `c:`, which matches off-identity multicolor cards),
glance at the **CI** column; one off-identity pip makes a card illegal in a Commander deck.

### Phase 4 — Present a shortlist with reasoning, then refine

Hand back a **focused shortlist** (not a data dump) — usually **5–15 cards**, or **a handful of commanders**
in commander-finding mode — each with:

- the **card name, mana value, type line, color identity, and Cardmarket EUR price**;
- a **one-to-two-line reason** that names the *specific* synergy or problem it addresses — the points of
  contact you found, e.g. *"hits both your 'creature dies' and 'sacrifice' triggers, and refuels after a
  wipe — three points of contact"*;
- where useful, **what it would replace or how it slots in**, and any **trade-off** (fragile, slow, pricey).

Group the shortlist by the need it serves, and **lead with the cards that address the real (diagnosed) need**
— if that differs from the user's opening ask, show both but explain the reorder. Where there's a genuine
choice, offer **2–3 options with the trade-off** rather than dictating one (e.g. budget vs. premium, fast vs.
resilient). Then **invite reaction** — too expensive, already own it, want spicier/safer, want to go deeper
on one thread — and iterate. Re-query and refine until the user has the cards they actually want.

## The deliverable

The primary deliverable is the **refined shortlist in the conversation** — this skill is a search, and most
sessions end when the user has the cards they wanted. **Don't write files unless the user asks** (or the
shortlist is large enough that they'd clearly want to keep it).

When they do want it saved, write a single findings file and share it with the `present_files` tool:
`.mtg/finds/<slug>.md` in the resolved workspace (slug = the commander/theme/problem, kebab-case). It should
contain the **problem statement you agreed on**, the **shortlist grouped by need** (name · MV · type · CI ·
EUR · reason), the **total price** of the picks, and a short "how these fit" note. If the user instead wants
these cards turned into a full deck or slotted into an existing list, **hand off to the appropriate
deckbuilding skill** (`mtg-edh-build` / `mtg-edh-upgrade` / `mtg-std-build` / `mtg-std-upgrade`) carrying the
context you gathered — don't rebuild a whole deck inside this skill.

## The `.mtg` workspace

This skill only writes when the user asks for a saved findings file; even so, its I/O lives in the same
**workspace** the other MTG skills use, resolved in this order:

1. **`$MTG_HOME`**, if set — the user's portable data location (e.g. a private `mtg-data` git repo; see the
   repo's `SYNCING.md`). Use it even if subfolders don't exist yet — create them.
2. Otherwise the nearest **`.mtg/`** at or above the current working directory (conventionally git-ignored).

Run **`python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" --paths`** to print the resolved
`decks/`/`collection/`/`database/` paths as JSON (it creates nothing); findings go in a sibling `finds/`
folder. **If `$MTG_HOME` is unset and there's no clear working directory** and the user *does* want a file
saved, ask where the workspace should live first. (Pure search sessions that write nothing don't need this.)
Reading a `collection/` file, if one exists, is a nice touch — prefer cards the user already owns when two
picks are otherwise close, and flag which shortlisted cards they'd need to buy.

## How to drive the data sources

Same backbone as the deckbuilding skills — **EDHREC's JSON API** (`scripts/edhrec_fetch.py`) for proven
inclusions, **Scryfall** for deep text/type search, color-identity vetting, and **pricing** (`prices.eur` =
Cardmarket EUR). Full endpoint/fallback table: `references/data-sources.md`. EDHREC is fetched from
`json.edhrec.com` with a descriptive UA + retry/backoff — never the Cloudflare HTML; on 403/404 fall back
to the local Scryfall DB ordered by EDHREC rank and say so.

**Scryfall reads come from the local card database.** `scripts/scryfall_search.py` queries a **local SQLite
database** (`.mtg/database/cards.sqlite`, built from Scryfall bulk data — see the **mtg-db** skill) instead
of the API. It's built **automatically on first use** (one-time ~540 MB download); just call the script. If
it reports the data is **stale (>30 days)**, mention prices may have moved and **ask** whether to refresh
before continuing. `function:`/`otag:` (Tagger) tags route to the live API automatically. Retrieval, in order
of preference:

- **Code execution with network** → `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" "<query>"
  --limit 30` (reads the local DB, auto-builds on first use; prints name, MV, type, CI, cheapest-printing
  EUR; `--named "Sol Ring"` for one card's full text + price). Fastest path; `function:` queries use the live
  API transparently. **Use `--named` liberally here** — reading exact Oracle text is the core of Phase 3.
- **No code-exec network, but web tools** → `web_fetch` the **JSON** endpoints directly
  (`https://json.edhrec.com/pages/commanders/<slug>.json`) and the Scryfall search page; `web_search`
  first if `web_fetch` needs a search-sourced URL. No DB can be built here — that's the expected fallback.
- **Neither** → tell the user the environment needs network to `api.scryfall.com` and `json.edhrec.com`,
  and offer to proceed from known MTG knowledge with the caveat that prices, proven inclusions, and the
  newest cards won't be verified.

## Quality bar before you recommend

- **The recommendations target the *diagnosed* need**, not just the literal opening request — and if those
  differ, you said so and the user agreed on the direction.
- **Every recommended card clears the ≥2–3 synergy floor** (except pure structural utility — lands/ramp/
  catch-all removal), and its reason **names the specific points of contact** it hits, drawn from its actual
  Oracle text / type line — no vague "it's a good card". You read the wording and counted the contacts.
- **Color identity & legality check out** for every pick (vet with `id<=`, glance at the **CI** column; one
  off-identity pip makes a card illegal in a Commander deck), and prices are shown (Cardmarket EUR; note
  `null` prices rather than guessing).
- **The list is a shortlist, not a dump** — focused, grouped by need, with trade-offs and a couple of
  genuine choices where they exist — and you've invited the user to push back and refine.
