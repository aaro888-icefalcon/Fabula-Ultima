# Compatibility Spec — the shapes the engine consumes

"Mythic-compatible" means: arbitrary RPG material (rules, character creation, adventures, lore) is reworked into a small, fixed set of files the play loop reads. The engine never changes per game; only these campaign files do. Write them into the **campaign folder** (next to `campaign-state.md`).

| File | Produced by | The engine reads it for |
|---|---|---|
| `system-profile.md` | `adapt-ruleset.md` | task resolution & combat (the RPG seam) |
| `character-sheet.md` | `adapt-character-creation.md` | the PC's stats/resources the loop tracks |
| `setting-canon.md` | `adapt-lore.md` | world ground-truth (overrides invention) |
| `keyed-scenes.md` + Threads/Features seeded into state | `adapt-adventure.md` | a published module as trigger-based content (not rails) |

## `system-profile.md` — required fields
- **Dice convention** (e.g. d20, 2d6, dice pool) and how to express a roll for `dice.py roll`.
- **Core resolution:** how success/failure is decided (roll-vs-DC, opposed, PbtA 6-/7-9/10+, pool successes).
- **Degrees of success?** yes/no (drives whether Fate-Question Exceptional results map to anything).
- **Stats / skills** the loop and NPC-statting reference.
- **Combat:** initiative, attack, damage, defeat/death.
- **NPC stat convention:** the units NPC Statistics results are expressed in (AC, HP, damage dice…).
- **What the RPG resolves vs. what defers to a Fate Question** (the routing default).
- **Subsystems** ported as Fate Questions (sanity, hacking, chases), if any.

## `setting-canon.md` — shape
Places · factions · timeline/history · named NPCs (with wants) · tone · hard content lines. Canon is **ground truth over recollection**; consult before inventing.

## `keyed-scenes.md` — shape (prepared adventures)
Each entry: **Trigger** (a condition, often a per-scene die — `dice.py keyed 1d10 <target>`) → **Event** (what must happen). Plus: seed the module's goals onto the **Threads List**, its NPCs/locations onto **Characters**, and its set-pieces/hazards onto the **Adventure Features List**. The module is *available content the oracle plays through honestly*, never a forced order.

## Precedence
System Profile > uploaded rulebook text > Claude's training knowledge. When all are silent, a **Fate Question** decides and the result is recorded to canon/state.
