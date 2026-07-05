# mythic-gm

A standalone solo-RPG **Game Master engine** for Claude, powered by the *Mythic Game Master Emulator 2e* and *The Adventure Crafter* (all tables **fully hard-coded**). Claude runs the whole game — rolling every die honestly through scripts, asking Fate Questions, firing Random Events, generating Turning Points (the Adventure Crafter is always on), voicing NPCs, and tracking state — under a hardcore "no softening" discipline.

**Engine + companions.** mythic-gm is the engine; a **companion skill** supplies a specific RPG (ruleset + setting + generators) via a `bridge/` that fills the engine's hooks. See **`COMPANION-SKILLS.md`** to build/sync one and **`CONVERSION.md`** to migrate a repo. The engine plays standalone (rules-light) using defaults when no bridge is present.

## What's inside
- `SKILL.md` — the operating manual (play loop, discipline, routing, commands).
- `scripts/` — honest RNG & helpers: `dice.py`, `oracle.py`, `adventure_crafter.py`, `state.py`, `system.py`, `build_data.py`.
- `data/` — verified, machine-rollable JSON tables (Fate Chart, Event Focus, Meaning Tables, etc.), built from canon and checked by `build_data.py`.
- `references/` — the play-loop spec, discipline spine, rules indexes, the adaptation guide, genre packs, and the **full Mythic + Adventure Crafter books** (`references/canon/`).
- `assets/templates/` — `campaign-state.md` (source of truth) and the system/character/setting/session-zero templates.

## Quick start
Install the skill, then say e.g. *"Be my GM — let's play a solo grimdark survival game"* or *"Run a solo D&D 5e dungeon crawl."* Claude takes it from Session Zero.

To rebuild/verify the table data after editing canon: `python3 scripts/build_data.py`.

## Note on content
The Mythic 2e and Adventure Crafter tables are bundled for **personal use** (they're © Tana Pigeon / Word Mill Games). To share the engine without the copyrighted tables, replace `references/canon/` + `data/` with your own copies and rebuild.
