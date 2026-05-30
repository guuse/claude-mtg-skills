# Commander Brackets and Game Changers

The Commander Brackets system (introduced by the Commander Format Panel / Wizards of the Coast in 2025,
still iterating) is the official shared language for deck power level, replacing the old fuzzy 1–10 scale.
Always confirm the user's target bracket before building, because it changes interaction efficiency,
combo choices, and which high-impact cards are allowed.

> The bracket definitions and especially the **Game Changers list change over time**. Treat the summary
> below as a working baseline, and when precision matters (e.g. the user wants a tight Bracket 3 build),
> verify the current rules and list — `web_search` "official Commander brackets update" and the current
> Wizards announcement, and use Scryfall's `is:gamechanger` filter to identify Game Changers in the
> commander's colors. Don't hardcode a stale list into a deck.

## The five brackets (working baseline)

**Bracket 1 — Exhibition.** Ultra-casual, theme/flavor over power. **No Game Changers.** Win conditions
are incremental and telegraphed; games run long (often 9+ turns). Think tribal flavor, group hug, joke
themes. Interaction is light and synergistic.

**Bracket 2 — Core.** The "average modern deck" level (roughly where an unmodified recent precon sits,
though precons vary). **No Game Changers.** No early two-card infinite combos; mass land destruction
avoided. Wins are telegraphed and disruptable; expect ~8+ turns. This is a great default for "fun but
functional." Run synergistic interaction, an honest ~10 + 2–3 wipes, no fast combos.

**Bracket 3 — Upgraded.** Tuned, high card-quality decks with strong synergy and real disruption. **Up to
3 Game Changers** allowed. Still **no early-game two-card infinite combos** and **no mass land
destruction**. Most "this is my good deck" brews actually live here. Interaction should be more efficient
and a bit denser; a couple of premium cards are fine within the Game Changer cap.

**Bracket 4 — Optimized.** High power, very consistent, lethal. **No card restrictions beyond format
legality** — any number of Game Changers, fast combos allowed. Build for speed, consistency, efficient
interaction, and tight combos/win cons. Not cEDH-meta-tuned, but close in raw power.

**Bracket 5 — cEDH.** Built to battle the competitive metagame: win fast or generate overwhelming
resources, using established cEDH tools and decklists. Maximum efficiency, heavy free interaction, tuned
mana, redundant combos.

(Brackets 2–4 are by far the most common; default to 2–3 if the user is unsure.)

## How to enforce a bracket while building

1. **Game Changer count.** Pull the current Game Changers within the commander's identity
   (`is:gamechanger id<=<colors>` on Scryfall). Then:
   - Brackets 1–2: include **zero**.
   - Bracket 3: include **at most 3**, and only if they earn it.
   - Brackets 4–5: unrestricted.
   If a default card choice is a Game Changer and the bracket forbids/limits it, swap to a
   non-Game-Changer with the same role (Scryfall: same `function:` tag, drop `is:gamechanger`).

2. **Combos.** For Brackets 1–3, avoid **early/easy two-card infinite combos** as win conditions. The
   methodology's win-condition step should lean on board-state finishers (drains, overruns, big evasive
   threats) rather than "assemble these two cards and win." Brackets 4–5 may build around combos freely.

3. **Mass land destruction.** Avoid in Brackets 1–3.

4. **Interaction efficiency & density.** Scale with bracket — higher brackets want cheaper, instant-speed,
   sometimes free interaction and a bit more of it; lower brackets tolerate slower, more synergistic
   answers.

5. **Tutors and fast mana.** Heavy tutoring and fast mana push a deck up in power; use them sparingly in
   low brackets and freely in 4–5. (Specific tutor restrictions have changed across updates — verify
   current rules if it matters for the build.)

When you deliver the deck, state the target bracket, how many Game Changers it contains, and confirm it
respects the combo/MLD limits for that bracket so the user can represent it honestly at a table.
