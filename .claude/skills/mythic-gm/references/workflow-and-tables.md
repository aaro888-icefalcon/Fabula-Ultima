# Mythic-GM — Workflow Completeness Review & Table Integration Plan

_Final review pass over the whole engine. **Part A** audits every Mythic 2e + Adventure Crafter subsystem against the workflow (what's covered, what was missing and is now added, what the hardcore stance disables). **Part B** is the concrete plan for turning ~150 charts/tables into a verified, machine-rollable data layer the workflow calls._

---

# Part A — Workflow completeness review

## A1. Coverage matrix

Legend: **✅ already in the loop/integration spec** · **➕ gap, now added (A2)** · **◽ optional, selected at Session Zero** · **⛔ disabled/constrained by the hardcore discipline (A3)** · **🚫 out of scope (solo engine)**.

| Subsystem (source) | Status | Where it lives in the workflow |
|---|---|---|
| Fate Questions — narrative mode | ✅ | Loop D |
| Fate Questions — rule-replacement mode (CF=5, no Exceptional/Event) | ✅ | RPG integration 3.4 |
| Fate Chart · Example Odds · Fate Question Answers | ✅ | Loop D + tables |
| Exceptional Yes/No handling | ➕ | Now explicit in Loop D + NPC behavior |
| Fate Check (2d10 alt resolution) + modifiers | ◽ | Session-Zero resolution choice |
| Chaos Factor + end-of-scene adjustment (1–9, start 5) | ✅ | Loop G |
| Chaos flavors — Mid/Low/No-Chaos charts | ◽ | Session-Zero option |
| Random Events — trigger (doubles digit ≤ CF) + at Interrupt | ✅ | Loop D step 12, F |
| Event Focus Table + Event Meaning | ✅ | Loop F + tables |
| Choosing the Event Focus / "Choose Most Logical" | ⛔ | Player-only lever (A3) |
| Lists — Threads & Characters, weighting (≤3), removal | ✅ | Loop G + A2 detail |
| Lists as random tables (rolling on a List) | ✅ | Loop F + AC Part 5 |
| Meaning Tables — Actions / Descriptors / Elements (~45) | ✅ | Loop E + tables |
| Discovering Meaning (detail without a Fate Question) | ➕ | Now explicit, Loop E |
| First Scene (per Adventure-Source mode) | ✅ | Loop A |
| Expected Scene + Scene Test (over/odd/even, mode-aware) | ✅ | Loop B |
| Altered Scene + Scene Adjustment Table | ✅ | Loop B |
| Interrupt Scene | ✅ | Loop B + modes |
| Playing out the scene (Fate-Question flow) | ✅ | Loop C–D |
| **Scene-end strategies** (action done / narrative shift / mood / auto-interrupt) | ➕ | **Now added** — Loop C→G trigger |
| End-of-Scene Bookkeeping | ✅ | Loop G |
| **Generating NPC Behavior + NPC Behavior Table** | ➕ | **Now added** — Loop C step 8 |
| NPC Statistics + table (on-the-fly statting) | ✅ | RPG integration 3.5 (Exc No = −50%) |
| Using Fate Questions to Replace RPG Rules | ✅ | RPG integration 3.4 |
| Getting the Most Out of Sourcebooks | ✅ | RPG integration 3.7 |
| **Thread Progress Track** (Focus / Progress / Flashpoint / Track-Flashpoint / Plot Armor / Conclusion) | ➕ | **Now added** — optional overlay (A2) |
| **Discovery Check + Discovery Fate Q + Thread Discovery Check Table** | ➕ | **Now added** — with Thread Progress |
| Diversifying Threads / "crowding out" | ➕ | Now noted — List-curation guidance (A2) |
| **Player vs. PC Knowledge** (4 strategies) | ➕ | **Now added** — discipline policy (A3) |
| **Conclusive Adventure Conclusions** | ➕ | **Now added** — endgame (A2) |
| "What is a session" (pacing / save) | ✅ | State persistence (per-scene overwrite) |
| Keyed Scenes (+ Record Sheet) | ✅ | Part 6a |
| Prepared Adventures (scaling / Features / Event-Focus) | ✅ | Part 6b |
| Handling Complicated Campaigns (multi-Thread / multi-PC) | ➕ | Now noted — multiple Lists/Tracks (A2) |
| **Peril Points** / "decide the PC can't die" | ⛔ | **Disabled by default** (A3) |
| Using the Adventure Crafter with Mythic | ✅ | Part 5 |
| Adventure Journal / Adventure Lists (sheets) | ✅ | `campaign-state.md` |
| AC — Themes / Plot Point Theme / Random Themes / Theme Translation | ✅ | Part 5 + tables |
| AC — Plot Point Table (5 themes) + Reduced + Meta + Special Plot Points | ✅/➕ | Turning-point gen; Meta/Special handled in `adventure_crafter.py` (A2) |
| AC — Turning Points (advance / conclude) | ✅ | Part 5 |
| AC — Character Crafting (Descriptors / Identity / Special Trait) | ✅ | Used on "Add a Character" |
| AC — Paths (outline-ahead, backstory, history generators) | ➕ | Now noted — "preset outline" + generators (A2) |
| Group play / rotating Guide | 🚫 | Out of scope (solo, Claude-run) |

**Result:** the previously-specified loop covers the core correctly; **11 subsystems were under-specified or missing and are folded in below; 3 player-control features are constrained/disabled by the hardcore stance.** Nothing in either book is now unaccounted for.

## A2. Gaps now closed (concrete workflow additions)

1. **Generating NPC Behavior (Loop C, step 8 — "NPCs act to win").** When an NPC must act, resolve it the Mythic way: if trivial/unimportant, follow expectation; **if it matters, frame the intended action as a Fate Question** ("Does the NPC do X?" / "Does the NPC continue?") or **roll a Meaning Table** if you have no idea. Read the **NPC Behavior Table**: *Yes* = does/continues as expected · *No* = next-most-expected (or roll a Meaning Table) · *Exceptional Yes* = expected action, **greater intensity** · *Exceptional No* = opposite, or next-expected intensified · *Random Event* = roll a Meaning Table for an **additional** action. **Hardcore override:** never lazily default to the *convenient* expectation for anything consequential — phrase it as a Fate Question and let the dice (biased toward competence/ruthlessness) decide, so "NPCs act to win" is enforced, not narrated.
2. **Thread Progress Track (optional overlay, like Keyed Scenes).** Pick a **Focus Thread** and a Track (**10 / 15 / 20** points). **Progress** (a significant step) and a **Flashpoint** (a dramatic, important beat) each mark **+2**. Tracks split into **5-point phases**; if no Flashpoint occurred in a phase, the Track **forces** one — a Random Event (Focus = Current Context) that involves the Thread dramatically without resolving it. **Plot Armor:** while the Track runs, the Focus Thread **cannot be resolved by normal play** — any would-be resolution is reinterpreted to keep it alive until the Track completes, then a **Conclusion** Random Event ends it. **Discovery Check** (anti-stall): when out of ideas, "Is something discovered?", **Odds never below 50/50**; *Yes* → roll the **Thread Discovery Check Table** (`1d10 + Progress Points`); *Exc Yes* → roll twice; *No* → nothing; *Exc No* → no more Discovery Checks this scene. `state.py` tracks the Track; `dice.py thread-discovery <points>` and `oracle.py` handle the rolls.
3. **Scene-end strategies (Loop C→G trigger).** A scene ends on any of: the **primary action resolves**, a **narrative shift**, **mood** ("run out of steam"), or a chosen **automatic Interrupt** (start the next scene as an Interrupt without testing). The engine names which trigger fired before entering bookkeeping.
4. **Conclusive Adventure Conclusions (endgame).** To drive toward an ending, on an Interrupt the **player** may choose Event Focus = **Move Toward a Thread** (and choose the Thread) to refocus on the main goal; and at a Thread's conclusion, **"make it special"** — use the meta-Context to ramp interpretations up (a plain *Yes* on the final confrontation becomes the boss's signature move, not a basic attack). Endings are still honest (dice decide), just played at full intensity.
5. **Player vs. PC Knowledge — see A3 (it's a discipline policy).**
6. **List hygiene & complicated campaigns.** Curate the Threads List deliberately (a tight list = focused adventure; a long list = sandbox with detours). Multi-Thread / multi-adventure campaigns are supported by **multiple Threads on the List and parallel Thread Progress Tracks**; a second PC is just additional sheets in state. (Diversifying Threads, Handling Complicated Campaigns.)
7. **AC internals (Meta / Special Plot Points, Paths).** Meta Plot Points (which modify a Turning Point) and Special Plot Points are resolved inside `adventure_crafter.py` per the AC references; the AC **Paths** (generate an outline/backstory/history ahead of time) are the source of the **"preset outline" Adventure-Source mode** (Part 6) and of optional background generation.

## A3. Discipline resolutions — where the books offer softening, the hardcore engine doesn't

The books are written for *all* play styles, including narrative players who like to save their characters. The hardcore stance makes deliberate, explicit choices:

- **Peril Points → OFF by default.** The book literally defines them as the GM "quietly diverting your PC from certain doom" — the exact softening the spine forbids. The engine **does not** use them, and **never** invokes "decide ahead of time the PC can't die" Context plot-armor. *Opt-in escape hatch only:* a player may enable a scarce pool (default 2, non-replenishing) that **only the player** may spend, **announced out loud**, as an acknowledged exception — never something Claude does quietly. Default hardcore = none.
- **Choose-vs-roll.** Every "Choose the Event Focus / Choose Most Logical / choose a List element" option is a **narrative-control lever reserved for the player**, used sparingly (e.g., to refocus on the main Thread per A2.4). **Claude always rolls**; Claude may not use a "choose" option to steer toward a softer or tidier outcome.
- **NPC behavior.** Default to Fate-Question/Meaning-Table resolution for any action that matters (A2.1), so enemies don't get quietly played dumb.
- **Player vs. PC Knowledge → simulationist strategies.** Because Claude (running everything) inevitably "knows" more than the PC — especially inside a prepared module or after many Fate Questions — the engine adopts **"Test It, Ask It, Then It's Real"** and **"Reliable vs. Unreliable Information"**: facts the player/Claude knows but the PC hasn't earned are **only potential** and **may be wrong** until the PC discovers them in play. The engine will **not** act on, leak, or steer using un-earned knowledge (a railroading/softening vector). The "Going With It" omniscient style is explicitly **not** the default.
- **Thread Progress "Plot Armor" is allowed** — it only delays a *Thread's* resolution, not a character's death; it raises tension rather than removing it, so it's consistent with the spine.

## A4. Net

The loop is complete. The additions above are folded into the play-loop spec (NPC behavior in Loop C; scene-end trigger before Loop G; Thread Progress + Peril-Points-off as overlays alongside Keyed Scenes; Player-vs-PC knowledge in the discipline spine). The only intentionally-excluded content is group-play and the softening features, both by design.

---

# Part B — Table integration plan

## B1. Principles

1. **One canonical source:** the embedded, cleaned Markdown (full fidelity, human-readable) in `references/mythic/` and `references/adventure-crafter/`.
2. **One rollable derivative:** verified `data/*.json` produced from the Markdown by `build_data.py`. Scripts roll on JSON and **return the exact entry plus a citation** (`table_id` + roll), so Claude never reads a 100-row table "by eye."
3. **No silent divergence:** a verification pass diffs JSON back against the Markdown; the build fails if anything mismatches (B6).

## B2. Source formats — and the reconstruction problem

Two physical formats came out of the PDF conversion, with very different difficulty:

- **Pipe tables (already structured)** — most **Meaning Tables** (Actions, Descriptors, Elements) and many small tables. Number→entry is directly parseable. **Low risk.**
- **Image-extracted code blocks (flattened)** — the tables that were *pictures* in the book: **Fate Chart**, **Fate Check Modifiers**, **Event Focus Table**, **Scene Adjustment**, **NPC Behavior/Statistics**, **Thread Progress / Discovery**, and the Adventure Crafter **Plot Point Table**. Their text is exact (pulled from the text layer, not OCR) but **2-D/columnar structure is collapsed into reading order**. These need **deterministic reconstruction** into rows/columns using each table's known dimensions, then **must be verified cell-by-cell**. **High risk → explicit transcription + verification step.**

`build_data.py` carries a **per-format parser** and, for the high-risk tables, a **one-time structured transcription** (committed as JSON) rather than a fragile auto-parse.

## B3. Roll / lookup types (how each maps roll → entry)

| Type | Used by | Mechanism |
|---|---|---|
| `list_d100` | Meaning Tables (each column), Event Focus | roll **1d100** → entry whose range contains the roll; word-pairs = two independent d100 rolls |
| `grid_fate_chart` | Fate Chart (+ Mid/Low/No-Chaos) | index by **(Odds row, CF column)** → three thresholds; **1d100**: ≤ExcYes-ceil → Exceptional Yes · ≤Yes-ceil → Yes · ≥ExcNo-floor → Exceptional No · else No; then doubles-≤-CF check |
| `modifier_lookup` | Fate Check Modifiers | Odds→mod and CF→mod, summed onto **2d10**; banded to Yes/No/Exceptional |
| `list_d10` | Scene Adjustment, Random Themes, Plot Point Theme | roll **1d10** → entry (ranges allowed, e.g. 7–10) |
| `banded_modifier` | Thread Discovery Check | **1d10 + Progress Points** → banded result (Progress/Flashpoint +2/+3) |
| `answer_keyed` | NPC Behavior, NPC Statistics, Discovery Fate Q, Player-vs-PC | **no dice** — keyed by a Fate answer (`yes / no / exc_yes / exc_no / random_event`) → guidance text |
| `themed_d100` | AC Plot Point Table | **3d10**: one die → Theme (via `list_d10` Plot Point Theme Table), other two → **1d100** under that Theme's column → Plot Point |

## B4. Uniform JSON schema

```json
{
  "id": "mythic.meaning.actions_1",
  "title": "Meaning Tables — Actions 1",
  "source": "references/mythic/meaning-tables-actions.md#actions-1",
  "type": "list_d100",
  "dice": "1d100",
  "entries": [
    { "min": 1, "max": 1, "value": "Abandon" },
    { "min": 2, "max": 2, "value": "Accompany" }
    /* … 100 rows … */
  ],
  "checksum": "sha256:…"          // of the source block, for drift detection
}
```

Variants: `grid_fate_chart` carries `rows` (Odds) × `cols` (CF) of `{exc_yes, yes, exc_no}`; `answer_keyed` carries an `answers` map; `themed_d100` references the Theme table id + a column per Theme. Every table also stores `source` (md file + anchor) so a result can cite the book.

## B5. Build pipeline (`scripts/build_data.py`, run once / on change)

1. **Locate** each table in the Markdown by anchor (a manifest maps `table_id → md file + heading/fence).
2. **Parse** by format: pipe-table parser for structured tables; **structured-transcription loader** for the high-risk reconstructed tables (Fate Chart, Plot Points, etc.).
3. **Normalize** into the B4 schema; compute the source `checksum`.
4. **Emit** `data/**/*.json` + a `manifest.json` listing every table, type, and status.
5. **Verify** (B6); **fail the build** on any error.

## B6. Verification harness (the safety net — non-negotiable for the reconstructed tables)

- **Structural:** every manifest table present; ranges are **contiguous and complete** (1–100 or 1–10, no gaps/overlaps/dupes); grids are fully populated (9×9 Fate Chart; 5 Theme columns × 100 Plot Points).
- **Fidelity (round-trip):** re-render each JSON table back to text and **diff against the source Markdown block**; any mismatch fails.
- **Known-cell spot checks:** assert canonical values that must be exact — e.g., Fate Chart **50/50 @ CF 5 = 50 (Yes ceiling)**; **Likely @ CF 5**; **Action 1 #1 = "Abandon"**; Scene Adjustment **7–10 = "Make 2 Adjustments"**; Scene Test mapping odd→Altered / even→Interrupt. These catch reconstruction slips in the numbers.
- **Statistical:** roll each table 10⁵× and confirm a **uniform** distribution over entries (catches off-by-one ranges and weighting bugs).
- **Checksum drift:** if a source block's checksum changes, force a rebuild so Markdown edits can't silently desync the JSON.

## B7. How the workflow invokes tables

Every workflow step names the **table id** it calls; the engine resolves dice → entry → citation. Examples:

| Workflow moment | Call | Returns |
|---|---|---|
| Scene Test | `dice.py scene <CF> --mode …` | branch (Expected/Altered/Interrupt) |
| Fate Question | `dice.py fate <odds> <CF> [--mode rule]` | Yes/No/Exc + doubles-event flag (reads `grid_fate_chart`) |
| Random Event | `oracle.py event-focus` → `oracle.py meaning <table>` | focus + word pair, each cited |
| NPC behavior | `oracle.py meaning <npc-table>` / Fate Q | action seed |
| Scene Adjustment | `dice.py table scene_adjustment` | 1d10 result |
| Thread Discovery | `dice.py thread-discovery <points>` | banded result |
| AC Turning Point | `adventure_crafter.py turning-point` | thread + 2–5 plot points (uses `list_d10` + `themed_d100`) |

The discipline requirement — *all randomness scripted and shown* — is satisfied because **the only way to read a table is through a roll call that prints `table_id`, the roll, and the entry**.

## B8. Table manifest (groups, counts, risk)

- **Mythic — resolution (high-risk, reconstructed):** Fate Chart, Mid/Low/No-Chaos Fate Charts, Fate Check Modifiers, Fate Question/Check Answers, Example Odds. *(~7)*
- **Mythic — events & scenes (mixed):** Event Focus Table, Prepared-Adventure Event Focus Table, Scene Adjustment Table. *(~3)*
- **Mythic — Meaning Tables (low-risk, pipe):** Actions ×2, Descriptors ×2, Elements ~45. *(~49)*
- **Mythic — NPC/thread (answer-keyed + banded):** NPC Behavior, NPC Statistics, Thread Discovery Check, Discovery Fate Q, Player-vs-PC. *(~5)*
- **Adventure Crafter (high-risk, reconstructed):** Plot Point Table (5 Themes), Plot Points Reduced, Meta Plot Points, Plot Point Theme Table, Random Themes, Theme Translation, Character Descriptors/Identity/Special Trait. *(~9)*
- **Sheets (not rollable — state templates):** Adventure Journal, Adventure Lists, Keyed Scenes Record, Thread Progress Tracks, Adventure Features List, Adventure Sheet. *(~6 → `assets/templates/`, not `data/`)*

≈ **75 rollable tables** + the sheets. The ~10 **high-risk reconstructed** tables get the structured-transcription + full verification treatment; the rest parse directly.

## B9. Maintenance

Adding/fixing a table = edit the Markdown → `build_data.py` rebuilds + re-verifies → scripts pick up the new JSON. The manifest + checksums mean a stray edit can't silently break a roll. House-ruling a table (e.g., a custom Meaning Table for a setting) is the same flow in the campaign folder, layered over the engine defaults.

---

## Bottom line

**Workflow:** complete — 11 missing/under-specified subsystems folded in, the Peril-Points/Player-knowledge softening vectors closed by explicit rulings, only solo-incompatible and deliberately-softening content excluded. **Tables:** a single canonical Markdown source, a verified JSON derivative the scripts roll on, with a hard verification gate focused on the ~10 image-reconstructed tables where fidelity risk actually lives.
