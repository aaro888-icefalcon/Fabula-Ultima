# Mythic GME 2e — rules index

The complete rulebook (every table verbatim) is bundled at **`references/canon/Mythic-GME.md`**. This index points you to the right section; the verified, rollable versions of the key tables are in `data/` (rolled via `scripts/`). Read canon for any detail not encoded in a script.

| Subsystem | In canon (`Mythic-GME.md`) | Engine touchpoint |
|---|---|---|
| Fate Questions, Fate Chart, Odds, Exceptional | "Fate Questions" chapter | `dice.py fate`; `data/mythic/fate_chart.json` |
| Fate Check (2d10 alt) + modifiers | "The Fate Check" | `dice.py check`; `data/mythic/fate_check.json` |
| Chaos Factor (1–9, start 5, ±1) | "Chaos Factor" | `state.py chaos` |
| Chaos flavors (Mid/Low/No) | "Choose Your Chaos Flavor" | canon (optional) |
| Random Events (doubles ≤ CF; Event Focus; Meaning) | "Random Events" | `oracle.py event-focus` / `pair` / `meaning` / `elements` |
| Meaning Tables — Actions, Descriptors | "Meaning Tables" | `data/mythic/meaning_*` (verified 100/100) |
| Meaning Tables — 45 Elements | "Meaning Tables: Elements" | `oracle.py elements "<name>"` → read from canon |
| Scenes: First / Expected / Test / Altered / Interrupt | "Scenes" | `dice.py scene`; `data/mythic/scene_test.json` |
| Scene Adjustment Table | "Altered Scenes" | `data/mythic/scene_adjustment.json` |
| Lists (Threads/Characters), weighting | "Lists" + "End of Scene Bookkeeping" | `oracle.py thread-list/character-list` |
| Generating NPC Behavior + table | "Generating NPC Behavior" | `oracle.py answer npc_behavior` |
| NPC Statistics | "Determining NPC Statistics" | `oracle.py answer npc_statistics` |
| Thread Progress Track / Discovery Check | "The Thread Progress Track" | `dice.py thread-discovery`; `oracle.py answer discovery_fate_question` |
| Player vs. PC Knowledge | "Resolving Character vs. Player Knowledge" | discipline policy (`references/discipline/softening-tells.md`) |
| Keyed Scenes | "Control Your Adventures With Keyed Scenes" | `dice.py keyed` |
| Prepared Adventures (scaling/features/event-focus) | "Using Mythic With Prepared Adventures" | `references/adapting/adapt-adventure.md` |
| Using Fate Questions to Replace RPG Rules | "Using Fate Questions to Replace RPG Rules" | `dice.py fate … --mode rule` |
| Using the Adventure Crafter with Mythic | "Using The Adventure Crafter With Mythic" | `references/adventure-crafter/` |

Full verified procedures with page cites: **`references/playloop.md`**. Completeness audit: **`references/workflow-and-tables.md`**.
