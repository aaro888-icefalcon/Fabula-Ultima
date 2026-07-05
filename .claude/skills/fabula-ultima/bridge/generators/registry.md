# Generators — Fabula Ultima  (routing index for generate:* hooks)

## Operative
- On a **NEW CHARACTER** result (two-stage character-list NEW, an Event Focus of *New NPC*, or an AC Plot Point calling for a Character), the engine auto-fires this generator: roll `generators/npc_role.json` **and** the AC Character Crafter (mode: conjunction), then flesh the NPC as a native of `setting-canon.md` per `interpretation.md` — give them a want, a faction/place, and a Bond hook to a PC. For a recurring antagonist also roll `villain_drive.json` and build a Villain (Ultima Points via `statgen.py villain`).
- Everything else is rolled **on demand** with `dice.py table <path>` (or the listed script), not auto-fired. Anything not in this index falls through to Mythic/AC.

| need | when called | table(s) / tool | mode |
|---|---|---|---|
| new NPC | any new Character | `npc_role.json` **+** AC Character Crafter | conjunction |
| villain agenda | a recurring antagonist appears | `villain_drive.json` → `statgen.py villain --rank minor\|major\|supreme` | conjunction |
| creature stats | a fight needs numbers | `lookup.py monster <name>` (Bestiary) or `statgen.py npc\|monster` | replace |
| dungeon / site | exploring a themed location | `dungeon_theme.json` + engine location generator | conjunction |
| scene complication | a Turning Point / twist needs an edge | `complication.json` | replace |
| Atlas adventure hook | a High/Natural/Techno-flavored world needs a seed | `atlas_hook.json` (+ `data/atlas/<atlas>.json`) | conjunction |
| generic inspiration | Discover Meaning, no specific need | Mythic Elements | default |

Tables are engine-schema `list_d100` / `list_d10` files, roll-tested by `bridge.py validate` and `build_data.py`. The machine-readable routing lives in `bridge.md` (`generators_map`).
