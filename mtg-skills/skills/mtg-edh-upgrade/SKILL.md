---
name: mtg-edh-upgrade
description: >-
  Improve an existing 100-card Magic the Gathering Commander (EDH) deck that the user pastes in. Use this
  skill whenever the user already has a Commander/EDH decklist and wants to upgrade, tune, optimize, fix, or
  "make it better" — rather than build a new deck from scratch. Triggers on phrases like "upgrade my
  commander deck", "improve this EDH deck", "here's my decklist, what should I change", "tune my Atraxa
  list", "what are the best upgrades for my deck", "help me cut/add cards", or any request that pastes or
  references an existing 100-card list and asks for improvements. The user pastes their current list inline.
  The skill diagnoses the deck against a proven methodology and comparable proven decklists (land count,
  card advantage, ramp, interaction, curve, win conditions, inclusion rates), determines the deck's actual
  power bracket, then recommends the highest-impact role-preserving swaps within a budget — and
  because this is an upgrade, the budget is usually much smaller than building a deck from scratch. Prices
  everything via Scryfall (Cardmarket EUR) and respects the deck's color identity and power bracket.
---

# MTG Commander Deck Upgrader

This skill takes a Commander deck the user **already has** and makes it meaningfully better. It uses the
same proven building methodology as the deckbuilder — the target shape of a functioning 100 (right land
count, enough card advantage, enough ramp, enough interaction, a sensible curve, real win conditions) — but
applies it as a **diagnosis-and-swap** pass: find where the current list is weakest, then spend a (usually
small) budget on the changes that fix the most for the least.

The core idea: **an upgrade is not a rebuild.** A few well-chosen swaps often improve a deck far more than
their cost suggests. Respect what the user already owns and likes; change what's actually holding the deck
back.

**Work interactively — this is a conversation, not a one-shot transform.** The user knows how their deck
actually plays; you know the card pool and the methodology. Combine them: ask what's wrong, react to what
they tell you, propose changes in digestible batches, and refine based on their feedback. Do **not** dump a
finished 100-card list and call it done. Talk through your reasoning, surface options, and only write the
final files once the user has agreed to the changes. Default to asking a question rather than assuming.

## Start here: paste your decklist

The user provides their **current decklist inline** in their prompt (pasted text — a Moxfield/Archidekt
export, a `1 Card Name` list, or even a rough list). Begin by parsing it:

- Identify the **commander** and its **color identity** (the only colors legal in the 99). Pull the real
  Oracle text from Scryfall.
- Read the **theme/engine** the deck is already going for — don't impose a new plan, sharpen the existing
  one (unless the user asks to re-pivot).
- **Price and categorize** every card via Scryfall (`prices.eur`, Cardmarket), tallying the current
  category counts (lands / ramp / card advantage / interaction / themed / win cons) and the total value.

If the pasted list is short of 100, malformed, or ambiguous, say what you found and ask the user to confirm
before proceeding.

## Ask what's wrong and what they want improved

Before you diagnose anything yourself, **ask the user what they think is wrong with the deck and what they
want it to do better.** They've played it; that's information you can't get from the list alone. Ask in
plain language (a few questions, not a wall) — for example:

- **What does it struggle with?** Slow starts / mana problems, runs out of cards, can't close games, folds
  to board wipes or removal, loses to a particular deck or player at your table.
- **What do you want it to do better?** Faster, grindier, more resilient, lean harder into the theme, hit a
  higher or lower power level.
- **What's off-limits or precious?** Pet cards you want to keep, cards you already own vs. won't buy, things
  you've tried that didn't work.

Let their answers steer the upgrade — **their lived pain points outrank your own read** when they conflict.
But if your tally later surfaces a problem they didn't mention (e.g. only 33 lands, or two pieces of card
advantage), **raise it and ask** whether they want it addressed rather than silently "fixing" it.

## Then confirm: bracket and upgrade budget

Two parameters, same as the builder — confirm them up front unless the user already stated both:

- **Power bracket (1–5)** — where the user wants the deck to land (it may differ from where it is now). See
  `references/brackets.md` for the **strict determination logic**. Default to keeping the deck at its current
  bracket if unsure. This is the **target**; you'll report the deck's **actual** bracket (before and after)
  determined from concrete signals — and a tuned deck with 0 Game Changers / no combos / no MLD is **Bracket
  2**, not 3, however optimized.
- **Upgrade budget cap** — a total spend in EUR (Cardmarket) for the changes, or "no cap". **Because this
  is an upgrade, the budget can be much lower than building from scratch** — even €10–30 of well-targeted
  swaps can noticeably improve a deck. Ask for their cap, suggest that a small budget is fine, and make the
  spend count: prioritize the cheapest changes that fix the biggest weaknesses first.

## The deliverable

Always produce **three files**, saved in their own folder under `.mtg/decks/edh/` in the user's current working
directory: `.mtg/decks/edh/<deck-slug>/import.txt`, `.mtg/decks/edh/<deck-slug>/primer.md`, and
`.mtg/decks/edh/<deck-slug>/deck.md` (create the folder if
missing; slug = the commander name, kebab-case, with a suffix like `-upgraded` if a folder already exists).
(Commander/EDH decks live under `decks/edh/`; MTG Arena Standard decks live under `decks/std/`.)
See "The `.mtg` workspace" below.

1. **The importable, role-tagged list** (`import.txt`) — the upgraded 100 as `1 Card Name`, commander first on
   its own line **with no tag**, blank line, then the 99, each non-commander card carrying its **two-tier role
   tags** (deck-flavoured numbered engine `#1) …` then lettered pillars `#A) … #E) Lands`, `#…` unquoted,
   tier-ordered) per `../mtg-edh-primer/references/tags.md`. This single file is both the import **and** the
   Moxfield tag source — no separate plain/tagged files. Generate it *from* the locked upgraded list so nothing
   drifts. (Moxfield's Import screen ignores `#tags`; apply them via **More → Bulk Edit** — say so in `primer.md`.)
2. **The publish-ready primer** (`primer.md`) — **always created** (public, Moxfield-pasteable): header + rating
   headline, TL;DR, how it wins, **card roles & tags** (the numbered-engine/lettered-pillar legend, then cards
   grouped by their most-defining tag with one-line explanations), play guide, strengths/weaknesses. **Link every
   card with Moxfield's `[[Card Name]]` syntax** (commander included). Follow `../mtg-edh-primer/SKILL.md`.
3. **Private status notes** (`deck.md`) — **private** working notes, *not* the public write-up. **Open with the
   "Changes" section** that is the heart of an upgrade: each change as **— Cut `<card>` (€X) → Add `<card>` (€Y)
   (shared role/reason)**, grouped by the weakness it fixes, plus the **total upgrade spend vs the budget cap**
   and a short "what these changes do" paragraph. Include an **Actual bracket** line — the bracket the upgraded
   deck *actually is* by `references/brackets.md` (with Game Changer count and combo/MLD/extra-turn confirmation),
   stated against the target if they differ, plus a **"what's needed to go up one bracket" (and what would drop
   it)** note. Close with a **Deck Rating** section — an overall ★ rating at the actual bracket plus the
   per-dimension scorecard, **before vs. after** (see "Step 6 — Rank the upgraded deck"). Keep per-card role
   explanations in `primer.md`, not here.

Use the `present_files` tool to share all three — but **only at the end**, once the user has agreed to the
changes through the interactive method below. The files are the record of a conversation, not its opening
move.

## Budget variants (only when asked)

The three files above are the default — **one** upgraded deck. Produce a **budget-variant ladder** *only* when
the user asks for one: an upgrade path at several spend levels (e.g. "what does €25 vs €100 of upgrades get
me"), or a transition that ladders. Never emit variants unasked.

When you do, follow the **same layout as `mtg-edh-build`** (see its "Budget variants" section): one set per
variant labelled by € budget — `import-<label>.txt`
(role-tagged), `primer-<label>.md` (public, `[[Card Name]]` links), `buylist-<label>.txt` (price-floor, with the
floor-vs-delivered caveat) — with the user's current list as the **`base`** variant (no buylist), a
`cuts-<from>-<to>.md` per consecutive step (the incremental cut→add list), and **one shared** private `deck.md`
for the whole ladder. The recommended variant may use the plain `import.txt`/`primer.md` alias. The term is
**budget variant**, never "tier" (see `CONTEXT.md`).

## The `.mtg` workspace

All of this skill's file I/O lives in one **workspace** directory holding `database/`, `decks/`, and
`collection/`. It is resolved in this order:

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
they set `$MTG_HOME`) before writing anything, and use that location for the rest of the session.

The subdirectory:

- **`.mtg/decks/`** — where upgraded decks are written, **split by format**: Commander/EDH under
  `.mtg/decks/edh/` and MTG Arena Standard under `.mtg/decks/std/`. **Each deck gets its own subfolder**
  — for this skill, `.mtg/decks/edh/<deck-slug>/`, holding `import.txt`, `primer.md`, and `deck.md`. This is the
  same decks folder the other deckbuilding skills use. Create the directories if they're missing.

(The pasted decklist is taken from the prompt, not a file — there's no input file to read.)

### Keeping decks in sync across machines (mtg-sync)

Decks live in the user's `mtg-data` git repo, and the user wants **every upgrade to pull at the start
and push at the end** — the same way card data comes from mtg-db. **Don't try to judge whether
syncing is set up before acting — always run the sync commands and let the helper tell you.**
`sync.py` returns `skipped` when the workspace isn't a git repo, so an unconditional call is safe
everywhere; guessing whether to run it is exactly what makes pushing flaky.

- **At the start**, before writing anything, invoke **mtg-sync** to pull (`--pull`),
  bringing down any decks built on another machine first.
- **As the final action of the upgrade** (see **Final step — always commit & push** at the end of
  this skill), invoke **mtg-sync** to push (`--push -m "<commander / archetype>"`), so the upgraded
  deck lands on the repo's main branch and is available everywhere. This push runs **every time**, not
  only when you think sync is configured.

**Only the *result* is best-effort.** If the push reports `skipped` (syncing isn't set up) or
`FAILED` (e.g. offline), note it in one line and continue — the deck is saved locally and can be
pushed later. Never skip the *attempt*. To set syncing up the first time, use the **mtg-sync** skill
(`--bootstrap`).

## The method (diagnose, then upgrade)

The target shape of a functioning 100 and the reasoning behind every number live in
`references/methodology.md` — read it before diagnosing. The **synergy-scoring loop** for choosing adds
(read → extract → map to tags → intersect → score, with the ≥2–3-points-of-contact rule) is in
`references/synergy.md` — read it too. The Scryfall query cookbook for finding upgrade candidates is in
`references/scryfall-syntax.md`. Work in this order:

### Step 1 — Diagnose the current list against comparable lists, then talk it through
First **pull the comparable proven decklists** for the commander (`scripts/edhrec_fetch.py "<commander>"` for
top/high-synergy with inclusion rates, `--average`, `--theme`/`--budget`) — they're the benchmark and the
source of candidates. Tally the existing deck and compare it to the methodology's targets *and* to those
inclusion rates: ~37–38 lands, **12+ net-positive** card-advantage pieces, ~10–11 ramp, ~10 interaction + 2–4
board wipes, 3–4 real win conditions, a sensible curve, color-identity legality. Note the **biggest gaps** —
too few lands, thin card advantage, inefficient interaction, a top-heavy curve, no clear closer, or
low-inclusion filler where the proven lists run high-inclusion staples.

**Also determine the deck's ACTUAL bracket now** from the signals in `references/brackets.md` (Game Changer
count, early two-card combos, MLD, chained extra turns, fast mana + tutor density) and compare it to the
target — don't inflate a tuned-but-vanilla deck to B3. Then **share a short, readable diagnosis** and
reconcile it with what the user told you in "Ask what's wrong": where do their complaints and your tally
agree, and where does your tally (or the bracket determination) reveal something they didn't raise? **Agree on
the top 2–3 priorities together before proposing any cards.**

### Step 2 — Rank upgrade candidates by impact per euro
For each gap, gather candidates **primarily from EDHREC's JSON API** (`scripts/edhrec_fetch.py "<commander>"`
— what proven lists run that this deck lacks), then fill with **Scryfall** for budget- and bracket-appropriate options
(`references/scryfall-syntax.md`). Favor cards that fix a real weakness *and* synergize with the existing
theme. Cheaper-but-sufficient beats expensive-but-marginal — the goal is the most improvement within the cap.

**Hold every *themed* add to the synergy bar in `references/synergy.md` (read it):** each must share at least
**2–3 points of contact** with the commander and the rest of the deck — more is better. Run the loop on the
existing deck's vocabulary: **read** the commander's Oracle text, **extract** its key elements, **map** each
to a Scryfall handle (curated `function:`/`otag:` Tagger tags first — `otag:sacrifice-outlet`,
`function:card-advantage`, `otag:token-maker` — then `o:"…"`, `t:…`, `keyword:…`), **search and intersect**,
and **score** candidates by points of contact, taking the densest. A swap that drops a one-note card for a
card pulling 2–3 jobs is exactly the kind of high-impact upgrade this skill is for. (Structural fixes —
lands, generic ramp, catch-all interaction — fill required roles and are exempt, but prefer the version that
also synergizes.)

### Step 3 — Choose the swaps (what to cut)
For every add, name the **cut**: the weakest card serving the same or a lower-priority role (off-theme
filler, an overcosted card the curve doesn't need, a win-more card, a strictly worse duplicate effect).
Keep the deck at exactly **100**. Don't cut cards the user flagged as favorites unless they're clearly
hurting the deck — and if so, explain why and offer the choice.

### Step 4 — Respect budget and bracket (role-preserving swaps; honest stop)
Keep the running spend under the cap. If a high-impact add blows the budget, find a **cheaper card serving the
same role/synergy** — same function, color identity, comparable effect, ideally also in the comparable lists
(`function:<role> id<=<colors>` filtered by `eur<X`; `references/scryfall-syntax.md`). If no adequate cheaper
substitute exists without weakening the deck, leave the current card and move to the next priority — don't
spend the budget on a downgrade. Enforce bracket rules (`references/brackets.md`) and **recompute the actual
bracket after the swaps** so the upgrade doesn't silently push the deck past (or pull it below) the target.
**If the budget can't lift the deck to a solid version of the target bracket**, say so plainly and either ask
for a larger budget for the specific cards that would do it, or **target one bracket lower** and re-evaluate
there, explaining the trade-off. Re-check category counts after the swaps and adjust until the deck hits the
target shape.

### Step 5 — Propose, discuss, and iterate (don't write files yet)
**Present the proposed swaps to the user for reaction before finalizing** — ideally in small batches by
priority (e.g. "first, the mana base", then "card advantage"), each as **Cut → Add, why, €cost**, with the
running spend. Invite them to veto, ask why, suggest their own cards, or push for cheaper/spicier options,
and **adjust accordingly**. Where there's a real choice, offer 2–3 options rather than dictating one. Keep
going until the user is happy with the full set of changes. **Only then** assemble the final 100, run the
quality checks below, rank the deck (Step 6), and write the three files.

### Step 6 — Rank the upgraded deck (★ rating)
Before writing files, **rate the final list** and embed the result in `deck.md`. Run
`python "${CLAUDE_SKILL_DIR}/scripts/analyze_deck.py" <import>.txt --commander "<name>" --json` to pull the
objective stats (curve, category counts, **EDHREC-rank staple signal**, Game Changer count, off-identity
check, total EUR), then apply the **five-dimension rubric in `references/rating.md`** — structure &
consistency, synergy density (via `references/synergy.md`), staples & card quality, win conditions, and
bracket calibration — for an overall ★ rating *at the deck's actual bracket*. The rubric is **strict and
evidence-based**: a deck that merely *functions* is **★★★ (3)**, not 4, and 4–5 must be earned against the
comparable lists (score Staples/Synergy off inclusion-rate/rank data, round **down** when evidence is thin).
This is the same method as the dedicated **mtg-edh-analyze** skill. Write a **Deck Rating** section into
`deck.md` and, because this is an upgrade, show it as **before → after** (rate the pasted starting list too)
so the changes' impact is visible. If the rating reveals the upgrade didn't move the deck's biggest weakness,
say so and propose the next swap rather than shipping it quietly.

## How to drive the data sources

Same backbone as the deckbuilder — **EDHREC's JSON API** for proven inclusions, **Scryfall** to fill
gaps, enforce color identity, filter by mana value, and **price** every card (`prices.eur` = Cardmarket
EUR). Full endpoint/fallback table: `references/data-sources.md`.

- **EDHREC** — `scripts/edhrec_fetch.py "<commander>"` (staples/high-synergy/themes; `--average`,
  `--theme <slug>`, `--budget`), reading `json.edhrec.com` with a descriptive UA + retry/backoff. Never
  scrape the `edhrec.com` HTML. On 403/404 the script exits non-zero — fall back to the local Scryfall DB
  ordered by EDHREC rank and tell the user proven-inclusion data is lower-confidence.
- **A user's current deck by link** — `scripts/import_deck.py <archidekt-or-moxfield-url>` pulls it via
  the site JSON API; if it's private or errors, ask the user to **paste** the list. Never invent one.

**Scryfall reads come from the local card database.** `scripts/scryfall_search.py` queries a **local
SQLite database** (`.mtg/database/cards.sqlite`, built from Scryfall bulk data — see the
**mtg-db** skill) instead of the API. It's built **automatically on first use** (one-time
~540 MB download); just call the script. At the **start**, if it reports the data is **stale (>30 days)**,
tell the user prices may have moved and **ask** whether to refresh before continuing. `function:`/`otag:`
(Tagger) tags route to the live API automatically. Retrieval, in order of preference:

- **Code execution with network** → `python "${CLAUDE_SKILL_DIR}/scripts/scryfall_search.py" "<query>" --limit 30` (reads the
  local DB, auto-builds on first use; color identity, cheapest-printing pricing; `--named "Sol Ring"` for
  one card). Fastest path. `function:` queries use the live API transparently.
- **No code-exec network, but web tools** → `web_fetch` the **JSON** endpoints directly
  (`https://json.edhrec.com/pages/commanders/<slug>.json`, `.../average-decks/<slug>.json`) and the
  Scryfall search page; `web_search` first if `web_fetch` needs a search-sourced URL. No DB can be built
  here — that's the expected fallback.
- **Neither** → tell the user the environment needs network to `api.scryfall.com` and `json.edhrec.com`,
  and offer to proceed from known MTG knowledge with the caveat that prices, proven inclusions, and the
  newest cards won't be verified.

If there's no clear working directory to write the database to, prompt the user for a path for `.mtg/`
first.

## Quality bar before you hand it over

- **Reconcile the files and the changelog.** Build `import.txt` (with role tags) from the locked upgraded list,
  and write `primer.md` and `deck.md` from that same list. Verify `import.txt`
  sums to exactly **100** with no duplicate non-basic names (`awk '{s+=$1} END{print s}' import.txt`
  prints `100`; `sed 's/^[0-9]* //;s/ #.*//' import.txt | sort | uniq -d` prints nothing). The **Changes** section's
  cuts and adds must net to zero card-count change, and every added card must appear in the final list and
  every cut must be gone.
- **Within budget & bracket:** total upgrade spend ≤ the cap (or the user okayed an overage, or the honest
  stop / step-down was reported); color identity legal for every card; the **actual bracket** recomputed
  (`references/brackets.md`) and matching the target (or the difference stated), with the **move-up /
  move-down** note included.
- **Double-check colors:** every card you add is within the commander's color identity — vet with
  `id<=<identity>` (NOT `c:`, which also matches off-identity multicolor cards) and check the search **CI**
  column. One off-identity pip makes a card illegal in the deck.
- **Real improvement:** the changes measurably move the deck toward the target shape (the gaps from Step 1
  are smaller), and each swap has a clear reason.
- **Rating included:** `deck.md` carries the **Deck Rating** section from Step 6 (overall ★ at the bracket +
  scorecard, before→after where possible). Only then present the files.

## Final step — always commit & push (every upgrade ends here)

This is the step that gets missed, so treat it as part of the deliverable, not an afterthought.
**After the three files are written and presented, the last thing you do — every single time — is push
them** by invoking the **mtg-sync** skill: `--push -m "<commander / archetype>"`.

Run it **unconditionally**. Do *not* first reason about whether the workspace is a synced repo — just
run it. The helper handles every case and reports back:

- **`ok` (committed + pushed)** → confirm in one line that the deck was pushed to the `mtg-data` repo's
  main branch.
- **`skipped`** → the workspace isn't a synced git repo; say so in one line and stop (offer
  `--bootstrap` via mtg-sync if they'd like syncing set up).
- **`FAILED`** → e.g. offline or an auth issue; say so in one line — the deck is committed/saved
  locally and can be pushed later.

Only the *handling of that result* is best-effort. The **attempt is mandatory** — never end an upgrade
without running the push.
