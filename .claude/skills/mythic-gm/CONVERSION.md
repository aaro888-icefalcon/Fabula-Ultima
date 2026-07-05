# CONVERSION — migrating a repo to the engine + bridge schema

Use this when you have a **Claude Code repository** that contains an **old mythic-gm skill** and an **old RPG skill** (built before the companion contract), and you want to reorganize both to the v2 schema: mythic-gm as the **engine**, the RPG skill as a **companion** with a `bridge/`.

Place this `CONVERSION.md` (and the v2 `mythic-gm/`) into the repo, then follow the steps.

---

## Target layout (what you're converting *to*)

```
repo/
├── mythic-gm/                  # the ENGINE (v2) — identical across every RPG
│   ├── SKILL.md  COMPANION-SKILLS.md  CONVERSION.md
│   ├── scripts/  data/  references/  assets/  agents/
├── <rpg-skill>/                # the COMPANION (content + bridge)
│   ├── SKILL.md                # the RPG's own skill (rules text, setting prose, generators)
│   └── bridge/                 # NEW — fills the engine hooks (see COMPANION-SKILLS.md §2)
│       ├── bridge.md  system-profile.md  interpretation.md  chaos-tendency.md
│       ├── theme-weights.md  subsystems.md  seeds.md  setting-canon.md
│       ├── generators/{registry.md, *.json}
│       └── adventures/*.md
└── campaign/                   # live play state (per campaign)
    ├── campaign-state.md  character-sheet.md  seeds.md  archive.md
```

The engine is **content-free and shared**; each RPG is a companion folder; play state lives in `campaign/`.

---

## Step 1 — Replace the old mythic-gm skill with v2
1. Delete the old `mythic-gm/` (or rename to `mythic-gm.old/`).
2. Drop in this v2 `mythic-gm/`.
3. Sanity-check: `python3 mythic-gm/scripts/build_data.py` → `VERIFICATION PASSED`. (All Mythic/AC tables are hard-coded; nothing to migrate.)
4. Anything the old engine had that was *RPG-specific* (house tables, setting notes, custom resolution) does **not** belong in the engine — it moves to the companion bridge in Step 2.

## Step 2 — Convert the old RPG skill into a companion (the **sync** path)
Create `<rpg-skill>/bridge/` by copying `mythic-gm/assets/bridge-templates/*`, then **map** the RPG skill's existing content into it — you're pointing/condensing, not rewriting:

| In the old RPG skill… | → bridge file | how |
|---|---|---|
| resolution rules (dice, combat, death, char-gen) | `system-profile.md` | summarize the resolution + NPC-stat units + routing |
| random tables / generators (NPC, location, encounter, faction…) | `generators/*.json` + `registry.md` | convert each table → JSON (engine schema); register *need → table → mode* |
| setting / gazetteer / lore | `setting-canon.md` | condense to ground truth (or point at the skill's lore file) |
| clocks, faction turns, sandbox/region rules | `subsystems.md` | one row each: name · cadence · advance-by |
| genre tone, "how to GM this", NPC feel | `interpretation.md` | the GM/NPC lens (not a reskin table) |
| chaos/volatility feel | `chaos-tendency.md` | start 5 / volatility / floors / flavor (standard default) |
| genre theme bias | `theme-weights.md` | fixed weights (+ optional First-Priority theme) |
| published adventures / modules | `adventures/*.md` | ingest into clusters + fragments (`references/ingest-adventure.md`) |
| seed sources | `seeds.md` | which canon/world/generators feed the 30–40 deck |

Then write the **manifest** `bridge/bridge.md` (the ```json block) listing the hooks you actually filled, and add one line to the RPG skill's `SKILL.md`: *"Companion bridge for mythic-gm: `./bridge/`."*

**Anything you don't map defers to the engine default** — a partial bridge is valid. Start with `system-profile`, `interpretation`, `theme-weights`, and the top few generators; add the rest later.

## Step 2.5 — Surface the operative rules (or the overrides won't fire)
Wiring a hook is not enough. In a long, summarized session a *correct-but-pointed-to* rule loses to a
convenient tooled move made every turn (the Fate Question) — the override silently never fires (e.g. the
RPG's skill/trait/passion checks get replaced by Fate Questions; `tick.py` never runs and Glory/clocks
stall). Close the gap structurally:

1. **Write a `## Operative` block** at the top of every overridden bridge file — the *imperative*, not a
   description. For `resolve`, include the **trigger list** (which PC actions go to the system check, not
   a Fate Question). For `world-tick`, "fire `tick.py` every bookkeeping" + the companion bookkeeping
   (Glory/XP/trait-debt). The engine templates already carry these blocks — fill them in.
2. **Inline them into the always-loaded orchestration doc** (the companion's SKILL.md): paste
   `bridge.py brief <bridge> --markdown` between `<!-- BRIDGE-BRIEF -->` markers and regenerate when the
   bridge changes. A pointer you don't follow is invisible; put the imperatives in always-on context.
3. **Boot opens the door:** the engine boot runs `bridge.py brief` (contents), not just `summary`
   (names). Make sure your companion SKILL.md says so.
4. **Trust the forcing functions:** `dice.py fate` prints the rung-1 guard, `tick.py` emits the mandatory
   bookkeeping checklist, `state.py render` keeps the Lists a generated view (no hand-synced snapshot).
5. **Check it:** `bridge.py validate` warns when an overridden hook has no `## Operative` digest, and
   `state.py validate` warns on dual-source Lists. Resolve every warning before you ship.

## Step 3 — Convert the RPG's tables to verified JSON
For each random table you moved to `generators/`, use the engine schema (`{id,title,type:"list_d100"|"list_d10",dice,entries:[{min,max,value}]}`). To get the same verification Mythic's tables get, add a small companion build step (copy the pattern from `mythic-gm/scripts/build_data.py`) or just ensure ranges are contiguous — `bridge.py validate` roll-tests coverage.

## Step 4 — Validate & smoke-test
```
python3 mythic-gm/scripts/bridge.py validate <rpg-skill>/bridge
python3 mythic-gm/scripts/bridge.py summary  <rpg-skill>/bridge      # overrides vs defaults
python3 mythic-gm/scripts/dice.py table <rpg-skill>/bridge/generators/<x>.json   # rolls honestly
```
Then run one turn: `dice.py scene 5` → `adventure_crafter.py turning-point --themes <order>` → resolve via the system-profile → `tick.py <bridge> <scene#>` at bookkeeping.

## Step 5 — Reorganize & commit
- Move play state into `campaign/`.
- Keep `mythic-gm/` untouched per-RPG (it's shared). To support multiple RPGs in one repo, give each its own `<rpg>/bridge/`; the engine loads whichever campaign points to.
- Delete `mythic-gm.old/` and any RPG-specific content that now lives in the bridge.

---

## Mapping cheat-sheet (old → new)
| Old world | New home |
|---|---|
| engine ran the RPG's rules inline | `bridge/system-profile.md` (+ `system.py route`) |
| RPG skill's d100 tables | `bridge/generators/*.json` (rolled by `dice.py table <path>`) |
| "prepared adventure" mode | ingested clusters/fragments in `bridge/adventures/` (pure sandbox) |
| per-adventure `--style` theme roll | fixed `bridge/theme-weights.md` |
| lore-harvest subagent | the optional `mythic-scout` agent + `seeds.md` deck |
| ad-hoc "interpret in this genre" | `bridge/interpretation.md` |
| canon-read tables | none — every engine table is hard-coded JSON now |

Result: one shared engine, any number of RPG companions, each a thin declarative `bridge/` over its own content.
