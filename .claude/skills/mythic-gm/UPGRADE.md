# UPGRADE — updating an existing repo from the old mythic-gm skill

Drop this file (and the new `mythic-gm/`) into a repository that already contains an **older
mythic-gm skill**, and follow the steps. It lists every change in this revision and exactly how to
apply it. Nothing here changes the Mythic/Adventure-Crafter *rules* — it makes the Lists, Plot
Points, and character generation correct and machine-driven.

> Already on the engine+bridge schema? This is a **version bump** of the engine. If your repo still
> has an *old monolithic* mythic-gm + a separate RPG skill, do `CONVERSION.md` first (schema), then
> this (version). The two are independent and can be done in either order.

---

## What changed (this revision)

1. **`Plotline` → `Thread` everywhere.** Mythic 2e's own term is *Thread*; the Adventure Crafter
   called the same thing a *Plotline*. They are now one word — `Thread` — across all scripts, docs,
   templates, and JSON values. (Canon book text under `references/canon/` is left verbatim.) The
   Meta result formerly "Plotline Combo" is now **"Thread Combo."**

2. **Meta Plot Points Table is hard-coded and wired.** New `data/adventure_crafter/meta_plot_points.json`
   (the 7 results, contiguous 1–100). A Plot Point that rolls **96–100** now *auto-rolls* the Meta
   table and prints the effect (Character Exits/Returns/Steps Up/Steps Down/Downgrade/Upgrade, or
   Thread Combo) instead of just saying "Meta."

3. **Plot Point names cleaned & verified.** The Plot Points Table is no longer scraped from the
   wrapped two-column PDF text (which bled names between neighbors). It is now a hand-transcribed,
   verified data module (`scripts/_plot_points_data.py`, 183 plot points). `build_data.py` checks
   that **every Theme column covers 25–95 with no gaps, dupes, or out-of-range** before writing.

4. **Threads & Characters Lists are JSON, with a two-stage roll.** Each campaign now stores
   `threads.json` / `characters.json` (entries with a `weight` 1–3). The List roll is two stages:
   **Stage 1** = category (NEW / PRE-EXISTING / CHOOSE MOST LOGICAL); **Stage 2**, if PRE-EXISTING,
   a weighted pick of which entry. It reproduces canon exactly for ≤25 weighted slots
   (`P(invoke e)=weight/25`) **and rolls over the full list when it's longer than 25** (no more
   truncation). Managed with `state.py thread|char add|weight|remove|show`.

5. **Theme order + Tens-cycle counter persist in `adventure.json`.** `adventure_crafter.py
   turning-point --campaign <dir>` reads the Theme priority and **auto-saves** the tens counter — no
   more passing `--themes`/`--tens` by hand. Set/inspect with `adventure_crafter.py themes
   --campaign <dir>` and `state.py adventure show|set-themes`.

6. **NEW characters auto-invoke the character generator, with a bridge override.** Any **NEW
   CHARACTER** result — a `character-list` rolling NEW, an Event Focus of *New NPC*, or an AC Plot
   Point that needs a Character — now **automatically** generates one. Default is the AC Character
   Crafter; a companion bridge can replace or augment it (see step 4 below).

7. **Context-enforcement — overrides now actually fire in play.** Fixes a real failure mode where a
   companion's `resolve`/`world-tick` overrides were correctly wired but never fired across a long
   session (every uncertain moment went to a Mythic Fate Question; `tick.py` never ran, so Glory/clocks
   stalled). The cause: the operative rules lived in non-auto-loaded bridge files that the orchestration
   doc only *pointed* to, and boot loaded a hook *summary* (names), not the rules. The fixes:
   - **`## Operative` digest blocks** in every bridge template (the imperative + a `resolve` **trigger
     list** of which PC skill/trait/passion/save go to the system check, not a Fate Question).
   - **`bridge.py brief <dir>`** — prints those operative rules; **boot now loads `brief`, not just
     `summary`**, and companions inline `brief --markdown` into their always-loaded SKILL.md.
   - **Forcing functions in tooling:** `dice.py fate` prints a rung-1 guard; **`tick.py` is now a
     mandatory end-of-scene checklist** (world-tick + Chaos + List render + seeds + resolve-debt);
     the `resolve` template ships the trigger list.
   - **Dual-source drift killed:** the Markdown Lists are a **generated** view — new `state.py render`
     regenerates them from JSON between `<!-- LISTS:* -->` markers; the template no longer says "keep
     roughly in sync."
   - **`bridge.py validate`** warns when an overridden hook has no `## Operative` digest; **`state.py
     validate`** warns on dual-source Lists.
   - Principle: *an instruction is only as strong as its presence at the moment of action* — inline
     imperatives into always-on context, convert policy into forcing functions, generate (don't sync)
     duplicated state.

New/changed files: `scripts/lists.py` (new), `scripts/_plot_points_data.py` (new),
`data/adventure_crafter/meta_plot_points.json` (new), `assets/bridge-templates/generators/EXAMPLE_npc_role.json`
(new), `assets/bridge-templates/generators/EXAMPLE_region.json`; rewired
`scripts/{adventure_crafter,oracle,dice,state,build_data,bridge,tick}.py` (new commands: `bridge.py brief`,
`state.py render`, `state.py migrate`); updated `SKILL.md`, `COMPANION-SKILLS.md`, `CONVERSION.md`,
all `assets/bridge-templates/*` (now carry `## Operative` blocks), `assets/templates/campaign-state.md`,
and the `references/` command strings.

---

## How to implement

### Step 1 — Swap in the new engine
1. Back up the old skill: `mv mythic-gm mythic-gm.old` (or commit first).
2. Drop the new `mythic-gm/` into the repo.
3. Build & verify the data layer (regenerates all JSON from the hand-verified sources):
   ```
   python3 mythic-gm/scripts/build_data.py        # expect: VERIFICATION PASSED ✓
   ```
   This alone gives you changes **1, 2, 3** (rename, Meta table, clean Plot Point names).

### Step 2 — Migrate each existing campaign's state (changes 4 & 5)
Old campaigns kept their Threads/Characters Lists as numbered Markdown lines in `campaign-state.md`.
Convert each campaign folder once:
```
python3 mythic-gm/scripts/state.py migrate <campaign_dir>
```
This reads the old `campaign-state.md` and writes `threads.json`, `characters.json`, and
`adventure.json` — preserving **weight = repetition** (a name on N lines → weight N, capped at 3),
the **Theme priority** line, and the **Tens-cycle counter** line. It is idempotent (skips any JSON
that already exists). After migrating, the JSON is the source of truth and the Markdown Lists become
a human-readable snapshot. Verify:
```
python3 mythic-gm/scripts/state.py list-count <campaign_dir>
python3 mythic-gm/scripts/state.py thread show <campaign_dir>
```
> Brand-new campaigns need nothing special: `state.py init <campaign_dir>` now scaffolds the three
> JSON files automatically.

### Step 3 — Update your play commands (changes 4 & 5)
Replace the old count-based flags with `--campaign` (the scripts read the JSON Lists themselves):

| Old | New |
|---|---|
| `dice.py fate <odds> <CF> --threads N --characters M` | `dice.py fate <odds> <CF> --campaign <dir>` |
| `oracle.py event --threads N --characters M` | `oracle.py event --campaign <dir>` |
| `oracle.py list <filled> [--new]` | `oracle.py thread-list \| character-list --campaign <dir>` |
| `adventure_crafter.py turning-point --threads N --characters M [--existing]` | `adventure_crafter.py turning-point --campaign <dir> [--existing]` |

(The legacy `--threads/--characters` count path still works if you pass no `--campaign`, so old
automation won't break — but `--campaign` is the supported path now.)

### Step 4 — (Optional) Give a companion a native character generator (change 6)
By default NEW characters use the AC Character Crafter — no action needed. To swap in or layer on a
companion-native generator, add a **`generators_map.character`** entry to that companion's
`bridge/bridge.md` manifest and keep `generate:character` in `overrides`:
```json
"generators_map": {
  "character": { "mode": "conjunction", "table": "generators/npc_role.json",
                 "note": "flesh the NPC from setting-canon factions" }
}
```
- `mode: "replace"` → companion generator **instead of** the AC Crafter; `"conjunction"` → **both**;
  omit the entry → AC Crafter only.
- `table` is a `list_d100`/`list_d10` JSON in the bridge (see
  `assets/bridge-templates/generators/EXAMPLE_npc_role.json`); `note` is lore the GM applies.
- Pass `--bridge <bridge_dir>` to the roller scripts so the override is seen (the play loop does this
  for you). Validate the bridge: `python3 mythic-gm/scripts/bridge.py validate <bridge_dir>`.

### Step 5 — Close the enforcement gap for each companion (change 7)
For every companion `bridge/` in the repo:
1. **Add `## Operative` blocks** to the overridden hook files (copy the structure from the updated
   `mythic-gm/assets/bridge-templates/*`): the imperative + (for `system-profile.md`) the trait/passion
   **trigger list**, and (for `subsystems.md`) "fire `tick.py` every bookkeeping" + companion bookkeeping.
2. **Validate** and fix every enforcement warning:
   ```
   python3 mythic-gm/scripts/bridge.py validate <bridge_dir>     # warns on hooks with no Operative digest
   python3 mythic-gm/scripts/bridge.py brief    <bridge_dir>     # the rules boot will load
   ```
3. **Inline the brief into the companion's always-loaded SKILL.md** — paste the output of
   `bridge.py brief <bridge_dir> --markdown` between `<!-- BRIDGE-BRIEF -->` markers (regenerate when the
   bridge changes). This is the fix that makes the override actually fire under load.
4. **Adopt the bookkeeping commands in your loop:** at every scene end run
   `python3 mythic-gm/scripts/tick.py <bridge_dir> <scene#> <campaign>` (the mandatory checklist) then
   `python3 mythic-gm/scripts/state.py render <campaign>` (regenerate the Lists snapshot). Pass
   `--bridge <bridge_dir>` to `dice.py fate` / `oracle.py` so the resolve guard and overrides are seen.
5. For migrated campaigns, run `state.py render <campaign>` once so the Markdown Lists become a generated
   block; `state.py validate <campaign>/campaign-state.md` should then report no dual-source warning.

### Step 6 — Smoke-test one turn, then delete the backup
```
python3 mythic-gm/scripts/bridge.py brief <bridge_dir>                  # operative rules load at boot
python3 mythic-gm/scripts/dice.py scene 5
python3 mythic-gm/scripts/adventure_crafter.py turning-point --campaign <dir> --existing
python3 mythic-gm/scripts/oracle.py character-list --campaign <dir>     # a NEW result auto-generates
python3 mythic-gm/scripts/tick.py <bridge_dir> 5 <dir>                  # end-of-scene checklist fires
```
When it looks right: `rm -rf mythic-gm.old`.

---

## Rollback
Everything is contained in the `mythic-gm/` directory plus the per-campaign JSON files. To roll back:
restore `mythic-gm.old` → `mythic-gm`, and delete the generated `threads.json` / `characters.json` /
`adventure.json` in each campaign folder (the old Markdown Lists in `campaign-state.md` were never
removed, so no game state is lost).
