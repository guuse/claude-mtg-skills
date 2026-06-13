# Tag vocabulary

A **canonical, controlled list of tag names** so every primer tags the same job the same way
(`ManaDork`, never `Dork`/`Elf`/`Mana-Elf`). It is a **menu, not a checklist** — tag a card **only when the
tag actually fits**. Nothing is universal: a mono-white deck has no `ManaDork`, a deck with no sweepers has no
`BoardWipe`. Never invent a role that isn't on the battlefield.

Two kinds of tag, both drawn from this vocabulary:

- **Role tags** — what a card *mechanically does*, format-agnostic. Common, but applied only where present.
- **Theme tags** — how a card serves *this deck's* engine. Derived from the deck's identity; coin a new one
  when the deck's strategy isn't covered, **preferring an existing name when it fits**.

Each card carries **exactly one** tag in the import — its single **most-defining role** in this deck. When a
card does several jobs, pick the **primary** one. (One tag per card keeps the Tag-grouped view in Moxfield
readable: every card lands in exactly one group.) That same primary tag decides which section explains the
card **once** in `primer.md`. **The commander is never tagged** — Moxfield already labels it in its own zone.

## Role tags (use when present)

(There is no `Commander` tag — the commander line carries no tag at all.)

| Tag | Meaning |
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

## How tags appear in `moxfield-import.txt`

Each line takes a **single** tag, **PascalCase, no spaces** (`#SacOutlet`, not `#sac outlet`). Use a
**deck-specific** tag (`#Tag`), not a global one (`#!Tag`). **The commander line (first) carries no tag:**

```
1 Atraxa, Praetors' Voice (NCC) 2

1 Ghalta, Primal Hunger (RIX) 130 #Finisher
1 Llanowar Elves (M19) 314 #ManaDork
6 Forest (DOM) 266 #Land
```

Build the file from the deck's `import.txt` (commander first, blank line, then the 99) and append **one** tag
per non-commander line. Each line — the card **name and its exact `(SET) collector#` printing** — must stay
byte-for-byte identical to `import.txt`; you only append the trailing ` #Tag`. (See
https://moxfield.com/help/adding-cards — line format `<qty> <name> (SET) *F* *A* <#> #tag #!globaltag`.)

**Applying the tags — Bulk Edit, not Import.** Moxfield's **Import / netdeck** screen *ignores* `#Tags`, so
pasting `moxfield-import.txt` there gets you the cards with **no** tags. To apply them, open the deck →
**More → Bulk Edit** and paste `moxfield-import.txt` into the Bulk Edit box (or build the deck first via
Import, then re-paste the tagged list into Bulk Edit). Then **group by Tag** to see each card in its one role
group. Tell the user this in the primer's Moxfield usage note.
