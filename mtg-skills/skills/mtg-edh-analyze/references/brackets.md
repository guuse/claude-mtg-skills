# Commander Brackets — Official Determination (strict, not vibes)

The Commander Brackets system (WotC's Commander format panel; beta launched **February 2025**, refined
**April 2025**, **October 2025**, and into **2026**) is the official shared language for deck power on a
**1–5** scale. This file encodes the **official determination logic** — how a deck's bracket is actually
decided — not a loose paraphrase. Use it to report the bracket a deck *actually is*, then talk about targets.

> **Sources to verify against (the rules and the Game Changers list both change over time):**
> - WotC Commander Brackets announcements on `magic.wizards.com` — "Introducing Commander Brackets (Beta)"
>   and the **Apr 22 2025 / Oct 21 2025 / Feb 9 2026** updates.
> - Moxfield's help article: `https://moxfield.com/help/help-articles/commander-brackets`.
> - The **Game Changers list** is maintained by WotC and shifts between updates. **Never hardcode a stale
>   list** — identify Game Changers in a deck with Scryfall's `is:gamechanger` (in the commander's identity:
>   `is:gamechanger id<=<colors>`). When precision matters, `web_search` the current announcement first.

## The five brackets — exact official restrictions

These are the hard, checkable lines a deck must **not** cross to *stay* in a bracket:

| Bracket | Game Changers | Two-card infinite combos | Mass land denial | Extra-turn cards | Tutors | Game length |
|---|---|---|---|---|---|---|
| **1 — Exhibition** | **0** | none (no intentional) | none | **none** | sparse | ends slowly, long |
| **2 — Core** | **0** | none (no intentional) | none | low quantity, **not chained/looped** | sparse | ~9+ turns |
| **3 — Upgraded** | **≤ 3** | none that go off **cheaply within ~the first six turns** (late/conditional combos OK) | **none** | low quantity, not chained/looped | no hard cap (Oct 2025 removed the tutor count) — density is still a *power signal* | a turn or two faster than B2 |
| **4 — Optimized** | unlimited | unlimited | unlimited | unlimited | unlimited | can end quickly |
| **5 — cEDH** | unlimited | unlimited | unlimited | unlimited | unlimited | can end any turn; metagame-tuned |

Brackets **4 and 5 have no deck-construction restrictions beyond the banned list**; the difference is intent
and tuning (B5 is built to beat the *competitive* metagame). Brackets **2–3 are by far the most common**.

## How a deck's bracket is DETERMINED (the actual logic)

WotC's framing is "play where you belong by the descriptions," but determination is **not** a feeling — it is
a **floor set by the deck's most powerful signals**. Compute the bracket a deck *actually is* by taking the
**maximum** floor that any of these signals forces:

1. **Game Changer count** (`is:gamechanger` over the 99 + commander):
   - **0** → raises no floor (deck can be B1/B2).
   - **1–3** → floor is **Bracket 3**. *Any single Game Changer makes the deck at least B3.*
   - **4+** → floor is **Bracket 4**.
2. **Two-card infinite combos.** A combo that assembles **cheaply and can go off within ~the first six
   turns** → floor **Bracket 4**. A combo that only comes online late (big board / lots of mana / many
   pieces) is allowed at B3 and does **not** raise the floor by itself.
3. **Mass land denial** — any intentional MLD (Armageddon / Jokulhaups / Winter Orb–style land stax /
   repeatable land-destruction loops) → floor **Bracket 4** (B1–3 forbid it).
4. **Chained / looped extra turns** — extra-turn cards beyond *low quantity*, or built to chain/loop → floor
   **Bracket 4**. A lone Time Warp as a value card is fine at B2–3.
5. **Fast mana + tutor density** (judgment signal, not a hard count). Sol Ring is ubiquitous and fine, but a
   stack of fast mana (Mana Crypt / Mana Vault / Grim Monolith / rituals) **plus** a dense tutor package that
   makes the deck play the *same* powerful line every game pushes toward **B4** even under the 3–Game-Changer
   cap. A deck that *consistently goldfishes a turn-3–4 win* is **B4**, whatever its Game Changer count.

**The deck's ACTUAL bracket is the highest floor any signal forces.** If every signal is at the bottom —
**0 Game Changers, no early combo, no MLD, no chained extra turns, light tutoring/fast mana** — the deck is
**Bracket 2** (or **Bracket 1** only if it's genuinely ultra-casual / theme-first with sub-standard win cons).

### Tuning does NOT raise the bracket

A deck full of efficient staples, a perfect mana base, and tight synergy but with **none** of the five signals
above is **still Bracket 2**. "Optimized within Bracket 2's rules" is a real, common, *strong* deck — **do not
relabel it Bracket 3 just because it is good.** Power *within* a bracket is what the ★ rating measures (see
`rating.md`); the bracket itself is set only by the signals above.

> **Worked example — a tuned Gruul lands deck.** Heavy ramp, Cultivate-style value, big landfall payoffs, a
> crisp curve, 38 lands, premium-but-legal staples, and it wins reliably around turn 8–9 by going over the
> top. It runs **0 Game Changers, no two-card infinite combo, no mass land destruction, no chained extra
> turns, and only a couple of tutors.** Its actual bracket is **Bracket 2 — not Bracket 3.** Being
> well-tuned is not a B3 signal. It would *rate highly as a Bracket 2 deck.* It only becomes B3 if you add
> Game Changers (e.g. a couple of the green/red ones) or a compact win.

## Always report ACTUAL vs target, and how to move

Whenever you state a bracket:

1. **Report the bracket the deck ACTUALLY is** by the rule above, naming the signal that sets the floor
   (e.g. *"Bracket 2 — 0 Game Changers, no combos, no MLD, light tutoring; nothing forces a higher floor"*,
   or *"Bracket 4 — a turn-4 Thoracle/Consultation line forces it, regardless of the rest"*).
2. Only present a **higher target** bracket if the deck genuinely meets that bracket's power, and **state
   plainly when target and actual differ** — *"you asked for B3, but as built this is B2; here's why, and
   here's exactly what would make it a real B3."*
3. **Always tell the user what moves it UP one bracket and what moves it DOWN**, concretely, in cards:
   - **B2 → B3:** add **up to 3 Game Changers** in-identity (`is:gamechanger id<=<colors>`) and/or a
     **compact (but not early-cheap) two-card win**, tighten the tutor package, and run cheaper/faster
     interaction. Adding even **one** Game Changer is enough to cross the line.
   - **B3 → B4:** add an **early (≤~turn 6) cheap two-card infinite combo**, exceed **3** Game Changers, add
     **mass land denial** or **chained extra turns**, or stack **fast mana + tutors** into a consistent fast
     kill.
   - **Down a bracket (e.g. B3 → B2):** cut Game Changers to **0**, remove any early combo and all MLD, thin
     tutors/fast mana, and lean on win cons that close over several turns.

## Enforcing a bracket while building or upgrading

- Pull the current Game Changers in-identity (`is:gamechanger id<=<colors>`) and count them against the cap
  (B1–2: **0**; B3: **≤3**; B4–5: unlimited). If a default card is a Game Changer the target forbids/limits,
  swap to a non-Game-Changer with the **same role** (`function:` tag, drop `is:gamechanger`).
- For B1–3, keep any combo **late and conditional** — never an early cheap two-card infinite.
- **No MLD and no chained/looped extra turns below B4.**
- Scale interaction efficiency and fast mana to the bracket.

When you deliver, state the **actual** bracket, the **Game Changer count**, that the combo / MLD / extra-turn
limits are respected, and the **move-up / move-down** note, so the user can represent the deck honestly at a
table.
