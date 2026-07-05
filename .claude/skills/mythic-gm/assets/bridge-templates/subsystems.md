# World Subsystems — <Setting>   (hook: world-tick; fired by tick.py at bookkeeping)

## Operative
FIRE `tick.py <bridge> <scene#> [campaign]` AT EVERY BOOKKEEPING — not "when relevant." The world
moves whether or not the PC looks: advance the clocks below, roll due faction moves, and apply any
companion bookkeeping (e.g. <Glory awarded this scene; trait/passion checks owed; Thread pressure>).
If a subsystem stalls for several scenes, the engine has drifted — tick is mandatory, not optional.

## Registry
| subsystem        | cadence          | advance by |
|------------------|------------------|-----------|
| <War Front clock>| every scene      | tick +1; at full → roll <table> |
| <Salvage economy>| every scene      | draw 1 on <table> |
| <Faction move>   | every 3 scenes   | roll <faction.json> + a Move Toward/Away a Thread |
| <Glory / XP>     | every scene      | award per the RPG; record to character sheet |
