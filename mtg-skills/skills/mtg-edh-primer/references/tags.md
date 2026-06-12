# Tag vocabulary

A **canonical, controlled list of tag names** so every primer tags the same job the same way
(`ManaDork`, never `Dork`/`Elf`/`Mana-Elf`). It is a **menu, not a checklist** — tag a card **only when the
tag actually fits**. Nothing is universal: a mono-white deck has no `ManaDork`, a deck with no sweepers has no
`BoardWipe`. Never invent a role that isn't on the battlefield.

Two kinds of tag, both drawn from this vocabulary:

- **Role tags** — what a card *mechanically does*, format-agnostic. Common, but applied only where present.
- **Theme tags** — how a card serves *this deck's* engine. Derived from the deck's identity; coin a new one
  when the deck's strategy isn't covered, **preferring an existing name when it fits**.

A card may carry **several tags** in the import (Moxfield supports it). In `primer.md`, explain each card
**once, under its primary tag** (its main job in the deck).

## Role tags (use when present)

| Tag | Meaning |
|---|---|
| `Commander` | The commander. |
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

Moxfield bulk-import takes **space-delimited** tags per line, so **PascalCase, no spaces** (`#SacOutlet`,
not `#sac outlet`). Use **deck-specific** tags (`#Tag`), not global (`#!Tag`):

```
1 Ghalta, Primal Hunger #Fatty #Finisher
1 Llanowar Elves #ManaDork #SacFodder
6 Forest #Land
```

Build the file from the deck's `import.txt` (commander first, blank line, then the 99) and append the tags —
the card names must stay byte-for-byte identical to `import.txt`. Group the deck **by Tag** in Moxfield to
see the roles. (See https://moxfield.com/help/adding-cards — bulk format
`<qty> <name> (SET) *F* *A* <#> #tag #!globaltag`.)
