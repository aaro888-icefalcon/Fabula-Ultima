---
name: fabula-ultima
description: >-
  Solo / GM-less companion for playing FABULA ULTIMA (the JRPG-inspired tabletop RPG) on
  the mythic-gm engine. Use when the user wants to play, run, start, or continue Fabula
  Ultima; create a Fabula Ultima character or villain; resolve a Fabula Ultima Check,
  attack, spell, or conflict; build an NPC/monster; or run world creation (Press Start).
  Triggers on "Fabula Ultima", "play Fabula Ultima", "be my GM for Fabula Ultima", "Fabula
  Points", "Bonds", "Ultima Points", "Press Start / world creation", class names (Arcanist,
  Darkblade, Elementalist, Guardian, Rogue, Weaponmaster, Tinkerer…), "DEX+INS check",
  "Crisis", "Villain". All rules live in data/*.json behind scripts/*; every die is rolled
  through the mythic-gm engine (honest, shown, never fudged). Requires the mythic-gm skill.
---

# Fabula Ultima — companion for mythic-gm

Fabula Ultima is the **content**; **mythic-gm is the engine** (scene loop, oracle, honest
dice, no-softening discipline). This companion supplies the full ruleset as `data/*.json`
behind a set of CLIs in `scripts/`, and a `bridge/` that wires FU onto the engine's hooks.
**All randomness is delegated to the engine's `dice.py` through `scripts/engine.py`** — this
companion never rolls its own dice.

## Boot (every session)
1. **Requires mythic-gm** (engine ≥ 2). If it isn't loaded, load it — the scene/Chaos/Fate/
   Turning-Point loop and all dice come from it. `scripts/engine.py where` proves the link.
2. **Declare the bridge** at `./bridge` and hold the operative rules in the BRIDGE-BRIEF block
   below (they are the always-on imperatives — resolve via `fu.py`, JRPG lens, theme weights,
   world-tick, seeds).
3. **World?** If `campaign/world.json` is missing, run session zero first:
   `python3 scripts/worldgen.py run` (world → group → characters). It writes the world and
   regenerates `bridge/setting-canon.md`. Fabula Ultima has no default setting.
4. **Play** the engine's scene loop. Resolve anything a PC/NPC *attempts* with `scripts/fu.py`
   (never a Fate Question). Fire `fu.py tick <scene#>` at every bookkeeping.

## The oracle ladder (precedence)
**FU rule (`fu.py`) → FU generator/table → engine Fate Question.** A PC's own skill, attack,
spell, contest, or save is rung 1 (always `fu.py`). A Fate Question is only for world/NPC
facts the rules don't cover. New characters auto-fire the FU generator (see the brief).

## CLI surface (what the GM calls)

| command | use |
|---|---|
| `engine.py where \| selftest` | locate / prove the mythic-gm dice round-trip |
| `fu.py check <dA> <dB> --dl N [--bond N] [--mod N] [--sit ±2]` | attribute Check (crit/fumble/HR) |
| `fu.py opposed <dA> <dB> --vs <dC> <dD>` · `fu.py group … --dl N` | contest · cooperative Check |
| `fu.py attack --weapon <k> --attrs <dA> <dB> --target <creature>` | accuracy + damage + affinity in one honest step |
| `fu.py spell <k> --attrs <dINS> <dWLP> --target <c>` | spell card + Magic Check vs Magic Defense |
| `fu.py damage <target> <amt> <type>` · `fu.py status <sheet> +<s>` | apply harm (affinity+Crisis) · afflict (die downgrade) |
| `fu.py clock new "…" N \| tick <id> M \| list` | Clocks (dungeons, threats, rituals) |
| `fu.py points fabula +1 --owner <PC> \| ultima -N --reason "…"` | Fabula / Ultima ledgers (audit trail) |
| `fu.py init … · rest [--sheet X] · crisis <t> · tick <scene#>` | turn order · rest · Crisis check · bookkeeping |
| `sheet.py new <name> --level L --class rogue:3 … \| validate \| render \| levelup` | PC/companion sheets (legality-checked) |
| `statgen.py npc \| villain \| monster …` | build NPCs/villains/monsters from the design math |
| `lookup.py class\|spell\|skill\|heroic\|weapon\|armor\|shield\|monster\|status\|npc_skill <name>` | one compact rules card (lean context) |
| `worldgen.py steps \| run [--genre core\|high\|natural\|techno]` | session-zero world/group/character creation (genre-defaulted) |
| `gen.py npc\|villain\|monster\|faction\|front\|world [--genre G] [--near\|--vs <pc>]` | emergent, genre-aware generation → a persisted `campaign/entities/*` (+ an agenda front for antagonists) |
| `state.py init --genre G \| show \| list \| get <id> \| import-sheets` | the atomized campaign store (entities + fronts + scene/chaos/genre index) |
| `tick.py [scene#]`  (also `fu.py tick`) | advancing end-of-scene bookkeeping: fronts advance (Chaos-scaled), reseed, Fabula/Ultima economy, Chaos judge → surfacing directives |
| `build_data.py [--strict]` | validate the data/ ruleset against its schemas + cross-refs |

## Where the rules live
`data/rules.json` (Checks, DLs, crit/fumble, Bonds, Fabula, resting, 0 HP) · `statuses.json`
· `damage.json` (affinity matrix) · `classes.json` + `heroic_skills.json` · `spells.json` ·
`equipment.json` · `npc_design.json` (+ `data/bestiary/*.json`) · `worldgen.json`. Don't load
a whole file into context — query one record with `lookup.py`.

## Solo & design notes
- **Companions** are full PC sheets (`sheet.py new <name> --kind companion`); their decisions
  come from the oracle, and their Fabula Points are spent only on oracle-offered, player-ratified
  moves.
- **Ultima Points** are a GM-side ledger (`fu.py points ultima`) — every villain spend is logged
  and visible.
- **0 HP** halts at the **Surrender / Sacrifice** fork printed verbatim by `fu.py damage`; the
  choice is the player's, and consequences tick via Clocks.
- **Bond dice / Fabula rerolls** are declared before the reveal (`--bond`), so they can't be
  retconned.
- Defeat, Surrender fallout (a forced Theme change), and Sacrifice (permanent death) are real —
  the engine's no-softening discipline applies.

<!-- BRIDGE-BRIEF: fabula-ultima — regenerate with `bridge.py brief <dir> --markdown`; do not hand-edit -->
### Active bridge — operative rules (fabula-ultima)
- **resolve** — - When a PC or NPC **attempts something**, resolve it with `scripts/fu.py` — NOT a Fate Question. Trigger list (the WHEN → the CLI): - Any attribute Check (GM names 2 of DEX/INS/MIG/WLP + a DL of 7/10/13/16) → `fu.py check <dieA> <dieB> --dl N [--bond N] [--mod N] [--sit ±2]` - Attack → `fu.py attack --weapon <key> --attrs <dieA> <dieB> --target <creature>`  (DL = target Defense) - Offensive spell / Ritual → `fu.py spell <key> --attrs <INS-die> <WLP-die> --target <creature>`  (DL = Magic Defense) - Contest / race / clash of wills → `fu.py opposed <dieA> <dieB> --vs <dieC> <dieD>` ; cooperation → `fu.py group …` ; lore/search with no DL → `fu.py check` (omit --dl, read the Result band) - Apply harm → `fu.py damage <target> <amount> <type>` (auto affinity + Crisis) ; afflict → `fu.py status <sheet> +<status>` - **Crit** = the two dice match AND show ≥6 → automatic success + an opportunity. **Fumble** = double 1 → automatic failure, the PC gains 1 Fabula Point, opposition gets an opportunity. **HR** (higher die) drives damage/effect size. - A **Fate Question** answers world/NPC uncertainty the rules don't cover — NEVER a PC's own skill, attack, spell, save, or contest. - At **0 HP**, `fu.py damage` prints the **Surrender / Sacrifice** fork verbatim — the choice is the player's; never auto-kill a PC. - Bond dice and Fabula rerolls are declared **before** the reveal (`--bond`); they cannot be retconned after seeing the dice.
- **meaning** — - Read every oracle result through a **JRPG / anime-fantasy** lens: high emotion, hope against despair, spectacle, personal stakes. Prefer the dramatic, character-first reading over the mundane one. - NPCs are **competent and self-interested**, and act from their **Bonds** (admiration/inferiority, loyalty/mistrust, affection/hatred) and their want — never as plot props. Give a named NPC a goal, a method, and a feeling toward a PC. - **Villains drive the world.** A villain pursues its agenda on a Clock even offscreen, makes an entrance (each PC gains 1 Fabula Point when it does), and spends **Ultima Points** for dramatic power plays — log every spend with `fu.py points ultima`. - Honor the **Fabula cycle**: hardship → resolve (Fabula Points) → growth. Press the heroes; let defeat and Surrender carry real, lasting consequences rather than softening them. - The active **genre** (`data/genre.json`, set at session zero, held in `campaign/state.json`) sharpens this lens: read its **pillars** and let its conflict themes + tech/magic level shape what's plausible — High (warring powers & hidden ancient magic), Natural (small-scale, seasons & spirits), Techno (soul-network & magitech). `gen.py` and `tick.py` already bias generation and world-advance by it; keep the narration consistent with it.
- **chaos** — - Start **Chaos Factor 5**; **volatility: normal** (standard Mythic chart). FU heroes are protagonists of their own story — the world pushes back hard but does not descend into pure randomness. - Raise CF when the heroes are overwhelmed, a villain's Clock advances, or resources run dry; lower it when they seize the initiative, resolve a threat Clock, or a Bond turns the tide. - No per-region floor by default; a besieged region or an active supreme-villain arc may set a floor of 6. start: 5 volatility: normal floor: (none by default) flavor: standard
- **themes** — - Use these **fixed** Adventure-Crafter theme weights for every adventure — Fabula Ultima is character- and Bond-driven JRPG drama, not a dungeon crawl: - **Personal: high**  · **Social: high**  · **Action: high**  · **Mystery: medium**  · **Tension: low** - **First-priority theme: Personal.** When a Turning Point is generated, lead with the heroes' Bonds, Themes, and relationships; let Action and Social carry the spectacle and intrigue; keep raw Tension/horror as seasoning. weights: Personal: 5 Social: 4 Action: 4 Mystery: 2 Tension: 1 first_priority: Personal
- **generate:character** — - On a **NEW CHARACTER** result (two-stage character-list NEW, an Event Focus of *New NPC*, or an AC Plot Point calling for a Character), the engine auto-fires this generator: roll `generators/npc_role.json` **and** the AC Character Crafter (mode: conjunction), then flesh the NPC as a native of `setting-canon.md` per `interpretation.md` — give them a want, a faction/place, and a Bond hook to a PC. For a recurring antagonist also roll `villain_drive.json` and build a Villain (Ultima Points via `statgen.py villain`). - Everything else is rolled **on demand** with `dice.py table <path>` (or the listed script), not auto-fired. Anything not in this index falls through to Mythic/AC. | need | when called | table(s) / tool | mode | |---|---|---|---| | new NPC | any new Character | `npc_role.json` **+** AC Character Crafter | conjunction | | villain agenda | a recurring antagonist appears | `villain_drive.json` → `statgen.py villain --rank minor\|major\|supreme` | conjunction | | creature stats | a fight needs numbers | `lookup.py monster <name>` (Bestiary) or `statgen.py npc\|monster` | replace | | dungeon / site | exploring a themed location | `dungeon_theme.json` + engine location generator | conjunction | | scene complication | a Turning Point / twist needs an edge | `complication.json` | replace | | Atlas adventure hook | a High/Natural/Techno-flavored world needs a seed | `atlas_hook.json` (+ `data/atlas/<atlas>.json`) | conjunction | | generic inspiration | Discover Meaning, no specific need | Mythic Elements | default | Tables are engine-schema `list_d100` / `list_d10` files, roll-tested by `bridge.py validate` and `build_data.py`. The machine-readable routing lives in `bridge.md` (`generators_map`).
- **generate:monster** — Creatures come from the Bestiary (data/bestiary/*.json via scripts/lookup.py monster <name>) or are built with scripts/statgen.py npc|monster --level L --species X [--rank elite|champion --n N]. Reskin a same-level bestiary entry before building from scratch. All NPCs are soldiers unless promoted.
- **generate:location** — Locations come from the created world (setting-canon.md) and, on demand, generators/dungeon_theme.json + the engine's location generator. Dungeons are traversed as Clocks (fu.py clock).
- **world-tick** — - Fire `python3 scripts/fu.py tick <scene#>` every bookkeeping — it lists open Clocks and walks the FU duties below. Do NOT skip it. - Companion bookkeeping each tick: advance every active **villain agenda** and **threat Clock** the world would push this scene; tick in-progress **Projects** and **Rituals**; run the **Fabula-point economy** (a PC with 0 FP starts the next session with 1; a villain who made an entrance granted each PC 1 FP; villains spend **Ultima Points** visibly via `fu.py points ultima`); refresh IP expectations after rests. - Surface, don't just tick: telegraph a Clock before it fills; a **filled** Clock becomes a Turning Point (Conclusion) or a Random Event (Close a Thread) — never a silent fill. | subsystem | cadence | advance by | |---|---|---| | Villain agenda Clocks | every ~scene of pressure (or on trigger) | advance the villain's goal Clock; on fill → Turning Point. Villains act even offscreen. | | Threat / doom Clocks | every scene | advance sieges, rituals, pursuits the fiction implies (`fu.py clock tick <id>`). | | Projects & Rituals | on trigger: downtime / rest | tick PC Projects (crafting, research) and cast Rituals toward completion. | | Fabula economy | every scene / session bound | 0 FP at session start → +1; villain entrance → +1 to each PC; Surrender → +2. | | Ultima Points | on villain power play | spend from the villain's pool visibly (`fu.py points ultima -N --reason …`). | | Rest & resources | on trigger: full/short rest | `fu.py rest` restores HP/MP and clears statuses; recharge Inventory Points. |
- **seeds** — - Keep a **30–40 card** seed deck and **refresh it each bookkeeping**. Draw seeds to feed Expected Scenes, Random Events, and Turning Points. - Sources, in priority order: (1) **canon near the party** — factions, NPCs, and threats from `setting-canon.md` and open `campaign/clocks.json`; (2) **live world state** — the PCs' Bonds and Themes, active villain agendas, unresolved consequences of past scenes (Surrender fallout, debts, promises); (3) **random rolls** on the generators (`generators/npc_role.json`, `villain_drive.json`, `dungeon_theme.json`, `complication.json`) when canon is thin. - Weight the deck toward the heroes' **Bonds and Themes** — Fabula Ultima runs on personal stakes. size: 30–40 refresh: each bookkeeping
<!-- /BRIDGE-BRIEF -->
