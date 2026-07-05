# Adapting external RPG material to the engine

This standalone engine plays a full game on its own (rules-light, Fate-Questions-only). To run a **specific** ruleset, setting, or published adventure — typically supplied by a second skill or the user's files — rework that material into the fixed shapes in `compatibility-spec.md`, written into the campaign folder. Then the play loop runs unchanged on top.

**Order at Session Zero:**
1. **Ruleset** → `adapt-ruleset.md` → `system-profile.md` (skip for rules-light).
2. **Character creation** → `adapt-character-creation.md` → `character-sheet.md`.
3. **Lore** → `adapt-lore.md` → `setting-canon.md` (or generate a setting).
4. **Published adventure** (optional) → `adapt-adventure.md` → `keyed-scenes.md` + seeded Lists, set mode = Prepared Adventure.

Principle: convert messy source text into the few shapes the engine reads, **confirm ambiguous mechanics with the player**, and prefer a clean minimal profile over copying the whole rulebook. Anything unstated falls back to a Fate Question.
