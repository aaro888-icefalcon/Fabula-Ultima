# Adapt character creation → `character-sheet.md`

Turn the RPG's char-gen into a guided flow and a filled sheet in the engine's state shape.

## Steps
1. **Walk the player through creation** using the system's rules (point-buy, rolled stats, playbook, lifepath…). Make real choices; don't auto-generate unless asked.
2. **Record into `assets/templates/character-sheet.md`:** name/concept, the stats & skills the System Profile references, derived values (HP/defense/etc.), gear, special abilities, and starting **conditions/resources** the loop tracks.
3. **Seed the adventure.** Pull 1–2 Threads (goals/bonds) and any tied NPCs from the backstory onto the Lists at Session Zero.
4. **Keep it honest.** If creation involves rolls, roll them via `dice.py roll` and keep the results.

For rules-light play, a concept + a few descriptive traits + whatever the genre needs is enough; resolve specifics with Fate Questions as they come up.
