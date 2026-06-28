# Tag vocabulary

A **canonical, controlled list of tag names** so every primer tags the same job the same way
(`ManaDork`, never `Dork`/`Elf`/`Mana-Elf`). It is a **menu, not a checklist** — tag a card **only when the
tag actually fits**. Nothing is universal: a mono-white deck has no `ManaDork`, a deck with no sweepers has no
`BoardWipe`. Never invent a role that isn't on the battlefield.

Tags are organised into **two ordered tiers**, and every card carries **one *or more*** of them — **every
category it genuinely belongs to** (a card that both ramps and is a land gets both; a creature that is an
evasive enabler *and* a draw engine gets both). Tag honestly: only where the job is actually present, but
don't force a card into a single box when it does several jobs.

**Tier 1 — the engine (numbered `1)`, `2)`, `3)`…).** The deck's **core game plan**: the 2–5 steps of *how
this deck actually wins*, named in the **flavour of the deck** and **ordered as the plan executes**. These are
**deck-specific** — derived from the deck's identity, not a fixed list. A ninjutsu deck's engine might be
`1) Unblockables` → `2) Ninjutsu` → `3) Ninjutsu - Targets` → `4) Extra Turns`; a reanimator deck's might be
`1) Discard Outlets` → `2) Fatties` → `3) Reanimation`. Name them with **taste** — descriptive and evocative
of the deck, **never cringe** (`3) Ninjutsu - Targets`, not `3) Sneaky Backstab Bois`).

**Tier 2 — the support pillars (lettered `A)`, `B)`, `C)`…).** The near-universal jobs every EDH deck needs,
**after** the engine and in this fixed order: `A) Mana Advantage` (ramp/dorks/cost-reduction), `B) Card
Advantage` (draw), `C) Interaction` (removal, wipes, counters, taxes), `D) Resilience` (protection, recursion,
saves), `E) Lands` (always last). Use only the pillars the deck actually has, keep the letter order, and let
`Lands` be the final letter.

**Why the prefixes:** Moxfield's *Group-by-Tag* view sorts tags **alphanumerically**, so the `1) … A) …`
prefixes force the groups to render in a **deliberate reading order** — the engine first (in execution
sequence), then the support pillars — instead of a meaningless A–Z scramble. The role/theme vocabulary below
is the **menu of jobs** that feed these categories, not the literal tag names.

Cards land in multiple groups, and that's intended — Group-by-Tag then reads like a guided tour of the deck.
In `primer.md`, explain each card **once**, under its **most-defining** category (prefer the engine tier when a
card is both an engine piece and a support piece). **The commander is never tagged** — Moxfield already labels
it in its own zone.

## The job menu (what feeds each category)

These are the **jobs** a card can do — the raw material you sort into the tiers above, **not** the literal tag
text. A job usually maps to a support pillar (`Ramp`/`ManaDork`→`A) Mana Advantage`, `Draw`→`B) Card
Advantage`, `Removal`/`BoardWipe`/counters→`C) Interaction`, `Protection`/`Recursion`→`D) Resilience`,
`Land`→`E) Lands`); the **theme** jobs below typically become the deck's **numbered engine** categories.
(There is no `Commander` tag — the commander line carries no tag at all.)

| Job | Meaning |
|---|---|
| `Ramp` | Non-creature mana acceleration — rocks, rituals, land-ramp, cost reduction. |
| `ManaDork` | A creature that taps for mana. (Sub-role of ramp; use when the deck leans on dorks.) |
| `Draw` | Net-positive card advantage (a one-shot rummage/loot is *not* advantage). |
| `Tutor` | Searches a card out of the library. |
| `Removal` | Targeted/spot interaction — destroy/exile/bounce a permanent. |
| `BoardWipe` | Mass removal / sweeper. |
| `Protection` | Hexproof, indestructible, counter-magic, regeneration, flash-save. |
| `Recursion` | Returns cards from the graveyard (reanimation, regrowth, recur-loops). |
| `Finisher` | A *repeatable, real* way to actually close the game (not win-more). |
| `Land` | Any land. |
| `Utility` | A flex/value piece that doesn't fit a sharper role. Use sparingly. |

## Theme tags (derive from the deck — examples, not a fixed set)

Pick the handful that describe *this* deck. Examples by archetype:

- **Aristocrats / sacrifice:** `SacOutlet`, `SacFodder`, `Drain`, `Lifegain`, `DeathTrigger`, `TokenMaker`.
- **+1/+1 counters:** `Counters`, `Proliferate`, `CounterPayoff`.
- **Reanimator / big-mana:** `Fatty`, `Reanimate`, `Discard`, `Cheat`, `XSpell`, `BigMana`.
- **Tokens / go-wide:** `TokenMaker`, `Anthem`, `Overrun`.
- **Spellslinger:** `Spellslinger`, `SpellCopy`, `Storm`, `MagecraftPayoff`.
- **Voltron:** `Voltron`, `Aura`, `Equipment`, `Evasion`.
- **Lands:** `Landfall`, `LandRamp`, `LandRecur`.
- **Stax / control:** `Stax`, `TaxEffect`, `Pillowfort`.
- **Combo:** `ComboPiece`, `ComboEnabler`.

If you coin a new theme tag, define it in one line in the primer's tag legend so the reader knows what it means.

## How tags appear in `import.txt`

The tags live **on the deck's `import.txt`** — that one file is both the importable list and the Moxfield tag
source (there is no separate `moxfield-import.txt`). Each non-commander line carries **one or more** tags. Each
tag is written `#` immediately followed by its name (prefix included); **Moxfield ends a tag at the next `#`**,
so multi-word, space-containing tags need **no quoting** — just separate tags with a space: `#3) Ninjutsu -
Targets`. Use **deck-specific** tags (`#…`), not global ones (`#!…`). **Never use the `&` character in a tag
name — Moxfield does not allow it.** Write the word `and`, or rephrase: `#Sac and Drain` or `#SacDrain`, never
`#Sac & Drain`. This applies to **every** tag — engine tiers, support pillars, and coined theme tags alike.
**The commander line (first) carries no tag:**

```
1 Satoru Umezawa

1 Dauthi Voidwalker #1) Unblockables #B) Card Advantage #C) Interaction
1 Silver-Fur Master #2) Ninjutsu #A) Mana Advantage
1 Sol Ring #A) Mana Advantage
10 Island #E) Lands
```

Order the tags on each line in tier order (`1)…2)…` then `A)…B)…`) so the file reads consistently. Append them
to the deck's existing card lines (commander first, blank line, then the 99) — keep each card **name and its
exact `(SET) collector#` printing** (if present) byte-for-byte identical, only adding the trailing ` #…` tags.
(See https://moxfield.com/help/adding-cards — line format `<qty> <name> (SET) *F* *A* <#> #tag #!globaltag`.)

**Applying the tags — Bulk Edit, not Import.** Moxfield's **Import / netdeck** screen *ignores* `#Tags`, so
pasting `import.txt` there gets you the cards with **no** tags. To apply them, open the deck →
**More → Bulk Edit** and paste `import.txt` into the Bulk Edit box (or build the deck first via
Import, then re-paste the tagged list into Bulk Edit). Then **group by Tag** to see the deck in deliberate
order — the numbered engine groups first, then the lettered support pillars. This is background for *how the
tagged `import.txt` is meant to be used* — **do not** reproduce it as a usage note/box in `primer.md`; the
primer is the deck guide only.

## Card links in `primer.md`

In `primer.md`, write every card name as a **Moxfield card link** — `[[Card Name]]` (double square brackets,
exact card name). Moxfield renders these as hover-preview links when the primer is pasted into a deck's
Notes/Primer tab. Link the **commander** too (e.g. `[[Meren of Clan Nel Toth]]`). Use the card's full name; for
double-faced cards the front-face name is enough (`[[Bala Ged Recovery]]`).
