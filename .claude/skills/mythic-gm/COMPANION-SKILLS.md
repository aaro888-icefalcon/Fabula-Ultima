# Building a Companion RPG Skill for mythic-gm

**Read this if you are pairing mythic-gm with a specific RPG, setting, or set of generators.**

mythic-gm is the **engine**: it runs the scene/Chaos/Fate/Random-Event/Turning-Point loop, the discipline, and all Mythic + Adventure Crafter tables. A **companion skill** is a content pack (an RPG ± setting ± generators) that ships a **`bridge/`** folder filling the engine's *hooks*. The engine never holds RPG content; the companion never re-implements the oracle. **All randomness still runs through the engine's scripts** — honest, shown, cited. A partial bridge is valid: any hook you don't fill uses the engine default, so the engine always plays.

---

## 1. The hook set (the contract surface)

| Hook | Engine asks | Default (standalone) | Bridge file that overrides |
|---|---|---|---|
| `resolve` | did this action/combat succeed? death? | Fate Question | `system-profile.md` |
| `generate:character` | a new NPC/PC | AC Character Crafter | `generators/` (index, mode) |
| `generate:<element>` | location / faction / item / creature / … | Mythic Elements | `generators/` (index, mode) |
| `meaning` | how to read a result here; how NPCs act | literal | `interpretation.md` |
| `chaos` | CF start / volatility / floor / flavor | start 5, **standard chart** | `chaos-tendency.md` |
| `themes` | the adventure's theme priorities | style-weighted roll | `theme-weights.md` (**fixed per RPG**) |
| `world-tick` | what advances at bookkeeping | offscreen clocks | `subsystems.md` |
| `seeds` | candidates for upcoming beats | Meaning words | `seeds.md` (+ generators + canon) |
| `adventure-ingest` | run a module | — | `adventures/` (clusters + fragments) |

## 1.5 Make overrides actually FIRE (the enforcement contract)

A hook you override does nothing if its rule never reaches the GM at the moment of action. Wiring is
not enough — pointers lose to convenient tooled moves under load. So every override must be **surfaced
as an imperative** and, where possible, **enforced by a tool**:

- **Write a `## Operative` block** at the top of each overridden hook's file — 2–4 lines of
  *imperative* (do this / not that), plus, for `resolve`, the **trigger list** (the WHEN: which PC
  skill/trait/passion/save/contest go to the system check, not a Fate Question), and for `world-tick`,
  "fire `tick.py` every bookkeeping" + the companion bookkeeping (Glory, XP, trait-debt…).
- **Boot loads contents, not names:** `bridge.py brief <bridge>` prints those Operative blocks; the
  engine reads it at session start. `summary` (names only) is not enough.
- **Inline the brief into the companion's always-loaded SKILL.md.** Paste `bridge.py brief <bridge>
  --markdown` between `<!-- BRIDGE-BRIEF -->` markers in your companion SKILL.md and regenerate it when
  the bridge changes. That puts the imperatives in *always-on* context, not a file the GM must remember
  to open.
- **Lean on the tool forcing-functions the engine already ships:** `dice.py fate` prints a guard
  ("PC task/trait/passion? → the RPG resolves it, not a Fate Question"); `tick.py` emits the mandatory
  end-of-scene checklist; `state.py render` keeps the Lists a *generated* view (never hand-synced).
- **`bridge.py validate` warns** when an overridden hook has no `## Operative` digest — fix those, or
  the override will silently not fire in play.

## 2. The bridge folder

```
bridge/
├── bridge.md            # manifest: which hooks you override + file map (machine block)
├── system-profile.md    # resolve
├── interpretation.md    # meaning + GM/NPC guidance
├── chaos-tendency.md    # chaos
├── theme-weights.md     # themes (fixed for the whole campaign)
├── generators/
│   ├── registry.md      # the routing index (need → when → table → mode)
│   └── *.json           # pure tables (built/verified like Mythic's)
├── subsystems.md        # world-tick registry
├── seeds.md             # seed-deck sources + size (30–40) + refresh (each bookkeeping)
├── setting-canon.md     # ground-truth lore
└── adventures/*.md      # optional: ingested modules (clusters + fragments)
```

Copy `mythic-gm/assets/bridge-templates/*` as your starting point. Validate with `python3 mythic-gm/scripts/bridge.py validate <path-to-bridge>`.

## 3. File specs (the essentials)

- **bridge.md** — prose + one fenced ```json block: `{ "companion": "...", "engine": "mythic-gm>=2", "overrides": [...hooks...], "files": {...} }`. `bridge.py` reads this.
- **system-profile.md** — dice convention + how to express a roll for `dice.py roll`; core resolution (vs-DC / opposed / PbtA / pool); degrees of success?; stats/skills; combat; death; **NPC-stat units**; routing default (what the RPG resolves vs Fate Questions).
- **interpretation.md** — *not a reskin table.* Broad GM-craft: how literally/dramatically to read the oracle here; **how this world's NPCs/factions think, want, and act** (so NPC interpretations are setting-true and competent); genre pacing/stakes. Read on every interpretation/NPC moment.
- **chaos-tendency.md** — `start` (5), `volatility` (normal), optional per-region `floor`, `flavor` (standard default).
- **theme-weights.md** — fixed AC theme weights for the setting (Action/Tension/Mystery/Social/Personal) + optional fixed First-Priority theme. Used by **every** adventure.
- **generators/** — see §4.
- **subsystems.md** — a table of `name · cadence (every scene / every N / on trigger) · advance-by`. `tick.py` fires the due ones at bookkeeping.
- **seeds.md** — the deck's **sources** (canon near the PC; live world state; random rolls on listed generators), **size 30–40**, **refresh each bookkeeping**. The main AI populates it inline; the optional Scout agent can offload it.
- **setting-canon.md** — ground truth; overrides recollection.
- **adventures/** — see §5.

## 4. Generators = a routing **index** (pure tables, Mythic defaults)

`generators/registry.md` is an index, **not** a blanket override. Each row: *need · when it's called · table(s) · mode*:

| need | when called | table(s) | mode |
|---|---|---|---|
| new NPC (generic) | any new Character | AC Character Crafter **+** `npc_role.json` | **conjunction** |
| new NPC (faction) | NPC tied to a faction | `faction_member.json` | replace |
| location | a scene needs a place | `region.json` | replace |
| generic inspiration | Discover Meaning, no specific need | Mythic Elements | **default** |

- **mode** = `replace` (companion table), `conjunction` (companion table layered on the AC/Mythic core), `default` (fall through to Mythic/AC).
- Anything not in the index → Mythic/AC. So companions add/replace *occasionally and specifically*.
- Each `*.json` is a `list_d100`/`list_d10` table in the engine's schema (see `assets/bridge-templates/generators/`). Add them to `build_data.py`'s companion pass so they're **verified** like Mythic's, and roll them with `dice.py table <path>`.

**`registry.md` is the human index; the engine reads the machine-readable `generators_map` in `bridge.md`.** Today the **`character`** key is wired to **auto-fire**: every **NEW CHARACTER** result — a two-stage `character-list` rolling NEW, an Event Focus of *New NPC*, or an AC Plot Point that calls for a new Character — automatically runs the character generator. Default is the AC Character Crafter; a bridge entry `"generators_map": {"character": {"mode": "replace|conjunction", "table": "generators/npc_role.json", "note": "<lore>"}}` (with `generate:character` in `overrides`) swaps in or layers on your companion-native generator and lore. `replace` = companion only; `conjunction` = companion **and** the AC Crafter; omit it → AC Crafter. Pass `--bridge <dir>` to the roller scripts so the override is seen (the loop does this automatically). Other `generators_map` keys are reserved for when the engine grows more auto-fire hooks; until then non-`character` generators are rolled on demand via `dice.py table`.

## 5. Adventure ingestion = pure sandbox, clusters + fragments

A module is chopped into **clusters** (authored scenes/nodes), each with a scene-level description and member **fragments** (atomic plot points), all tagged and cited. See `references/ingest-adventure.md` for the process and `assets/bridge-templates/adventures/` for the schema. Behavior:
- **Pure sandbox** — no forced order, no climax, no Plot Armor. Authored content surfaces only by contextual relevance.
- **Content bias: medium** — prefer an authored fragment when reasonably relevant, else roll a random Plot Point.
- **Weighted-random** draw with an un-used-fragment lean + a usage ledger (organic coverage, no railroad).
- **Expected Scenes draw a whole cluster** when one fits the context (then Scene-Tested).
- **Cluster cohesion:** if a Turning Point draws one fragment from cluster X, prefer X's siblings for the rest; leftover slots roll random.
- Fragments also seed the Lists, the seed deck, and Random-Event invokes.

## 6. Two build paths

- **Bottom-up (new companion):** write your RPG/setting/generators; copy the templates into `bridge/`; fill them; convert tables to JSON; declare `bridge/` in your SKILL.md; validate.
- **Sync (retrofit an existing RPG skill):** map what's there — rules→`system-profile`, tables→`generators`, gazetteer→`setting-canon`, clocks→`subsystems`, genre→`theme-weights`/`interpretation`/`chaos-tendency`, modules→`adventures`. Mostly pointers + a few config values + table conversion. Unmapped hooks defer to the engine. (See `CONVERSION.md` for converting a whole repo.)

## 7. Conformance & what stays the engine's
- `bridge.py validate <bridge>` checks structure, roll-tests generator tables, reports overrides vs defaults, **and warns on enforcement gaps** (an overridden hook with no `## Operative` digest). `bridge.py brief <bridge>` prints the operative rules the GM must hold — boot loads this. Discovery: the engine looks for a `bridge/` declared in the companion's SKILL.md. Precedence: **companion > engine default**.
- **Hands off (the engine owns these):** scenes, the Scene Test, Chaos math, Fate Questions, Random Events, Turning Points, the seed/list machinery, and the no-softening discipline. Companions supply the *world*, not the *engine*.
