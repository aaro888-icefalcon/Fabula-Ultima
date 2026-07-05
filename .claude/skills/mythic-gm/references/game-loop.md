# mythic-gm — The Game Loop, front to bottom

A complete trace of how a turn runs, with every **📄 markdown** read and every **⚙️ script** invoked called out at the step where it happens. Reads are "load into context as needed"; scripts are the honest-RNG/logic the engine *must* call rather than improvise.

Legend: **📄** = markdown reference/template read · **⚙️** = hard-coded script run · **🎲** = a die is rolled (only ever inside a ⚙️).

---

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PHASE A — LOAD & ROUTE   (runs at the top of EVERY turn)                  ║
╚═══════════════════════════════════════════════════════════════════════════╝
   │
   ├─ A1. Restate the Creed (anti-softening spine; decays if not re-held)
   │       📄 SKILL.md  (Mandatory First Actions + the Creed at the foot)
   │       📄 references/discipline/creed.md
   │
   ├─ A2. Read the live state
   │       📄 <campaign>/campaign-state.md      ← the source of truth
   │       ⚙️ python3 scripts/state.py validate <campaign>/campaign-state.md   (optional integrity check)
   │
   └─ A3. Route on state
           • state ABSENT  → go to PHASE B (Session Zero)
           • state PRESENT → recap last beat in 2–3 sentences → go to PHASE C (The Turn)

╔═══════════════════════════════════════════════════════════════════════════╗
║  PHASE B — SESSION ZERO   (one-time, only when no state exists)            ║
╚═══════════════════════════════════════════════════════════════════════════╝
   │   📄 assets/templates/session-zero-checklist.md   (the checklist driving B1–B8)
   │
   ├─ B1. Confirm hardcore play (honest dice, real consequences, no rescues)
   │       📄 references/discipline/creed.md · softening-tells.md
   │
   ├─ B2. Ruleset → System Profile   (skip for rules-light = Fate-Questions-only)
   │       📄 references/adapting/00_overview.md · adapt-ruleset.md · compatibility-spec.md
   │       📄 assets/templates/system-profile.md  → write <campaign>/system-profile.md
   │       ⚙️ python3 scripts/system.py route        (prints the RPG↔Mythic seam rule)
   │
   ├─ B3. Setting / lore → canon
   │       📄 references/adapting/adapt-lore.md → assets/templates/setting-canon.md → <campaign>/setting-canon.md
   │
   ├─ B4. Genre & stakes vocabulary
   │       📄 references/genres/<grimdark-survival|noir-mystery|cozy|_genre-template>.md
   │
   ├─ B5. Adventure THEMES (rolled, weighted by RPG style)
   │       ⚙️ python3 scripts/adventure_crafter.py themes --style <action|horror|mystery|intrigue|drama|balanced>
   │            🎲 weighted draw over data/adventure_crafter/themes.json (+ random_themes.json)
   │
   ├─ B6. Create the PC
   │       📄 references/adapting/adapt-character-creation.md → assets/templates/character-sheet.md → <campaign>/character-sheet.md
   │       ⚙️ python3 scripts/dice.py roll <NdM±K>          (only if the system rolls stats)
   │
   ├─ B7. Set Chaos Factor = 5; create empty Threads & Characters Lists (+ Adventure Features if prepared)
   │       ⚙️ python3 scripts/state.py init <campaign>     (copies campaign-state.md template)
   │
   └─ B8. FIRST SCENE  (never tested — built directly), per Adventure-Source mode:
           • Pure Mythic    → ⚙️ oracle.py pair actions | oracle.py event | (Inspired Idea / 4W)
           • Adventure Crafter → ⚙️ adventure_crafter.py turning-point --campaign <dir>   (1–3 of them)
           • Prepared Adventure → 📄 references/adapting/adapt-adventure.md (the module's start)
           → seed the Lists → describe → "What do you do?" → STOP → write campaign-state.md → PHASE C

╔═══════════════════════════════════════════════════════════════════════════╗
║  PHASE C — THE TURN   (the repeating play loop)                           ║
║  detail: 📄 references/playloop.md   ·   AC seam: 📄 references/combined-use.md ║
╚═══════════════════════════════════════════════════════════════════════════╝
   │
   ├─ C1. FRAME THE EXPECTED SCENE
   │        from the current adventure's open Threads + active Turning Point + player intent
   │        📄 campaign-state.md (the Lists)
   │
   ├─ C2. SCENE TEST                                   ⚙️ python3 scripts/dice.py scene <CF> --mode <pure|crafter|prepared>
   │        🎲 1d10 vs Chaos Factor   (data/mythic/scene_test.json)
   │        ├─ roll > CF            → EXPECTED scene (run as framed)
   │        ├─ ≤ CF & ODD           → ALTERED scene
   │        │     resolve by: Next-Expectation · Tweak · a Fate Question (C4) ·
   │        │     ⚙️ dice.py table scene_adjustment        🎲 1d10 (data/mythic/scene_adjustment.json)
   │        └─ ≤ CF & EVEN          → INTERRUPT scene
   │              • pure/prepared   → a Random Event (C5)
   │              • crafter mode    → ⚙️ adventure_crafter.py turning-point …   (Turning Point replaces the event)
   │        (prepared mode: no Altered/Interrupt — a within-CF roll ADDS a Random Event to the Expected scene)
   │
   ├─ C3. PLAY THE SCENE — describe what the PC perceives → "What do you do?" → STOP & WAIT
   │        then resolve each declared action by routing it:
   │
   │     ┌─ C4. WORLD QUESTION (rules silent) → FATE QUESTION
   │     │       ⚙️ python3 scripts/dice.py fate <odds> <CF> [--mode rule] [--campaign <dir>]
   │     │       🎲 1d100 on the Fate Chart (data/mythic/fate_chart.json) → Yes/No/Exceptional
   │     │       • --mode rule = stand in for an RPG rule (CF treated as 5, Exceptional collapsed)
   │     │       • alt resolution: ⚙️ dice.py check <odds> <CF>   🎲 2d10 (data/mythic/fate_check.json)
   │     │       • IF the d100 is doubles & digit ≤ CF → RANDOM EVENT auto-chains here ↓ (C5)
   │     │
   │     ├─ C5. RANDOM EVENT  (auto-fired by C4, or by an Interrupt in C2)
   │     │       ⚙️ python3 scripts/oracle.py event --campaign <dir> [--crafter]
   │     │         🎲 Event Focus      (data/mythic/event_focus.json)
   │     │         → routing (hard-coded oracle.py FOCUS_ROUTING; see 📄 combined-use.md):
   │     │             NPC Action/±        → 🎲 Characters-List invoke
   │     │             Move/Close a Thread → 🎲 Threads-List invoke (Close = Thread Conclusion)
   │     │             New NPC             → Character Crafter (C7)
   │     │             Remote/Ambiguous/PC±/Current Context → no list
   │     │         🎲 Meaning pair (data/mythic/meaning_actions_1+2.json) → interpret
   │     │
   │     ├─ C6. RPG-MECHANICAL ACTION (combat, skill, save, attack) → the System Profile
   │     │       📄 <campaign>/system-profile.md   ·   ⚙️ python3 scripts/system.py route
   │     │       ⚙️ python3 scripts/dice.py roll <NdM±K> [adv|dis]    🎲 (pre-commit stakes → roll → lock → narrate)
   │     │       NPC stats you lack → a Fate Question (C4) + ⚙️ oracle.py answer npc_statistics <key>
   │     │
   │     ├─ C7. NPC BEHAVIOR / NEW NPC
   │     │       behavior → a Fate Question (C4) + ⚙️ oracle.py answer npc_behavior <yes|no|exc_yes|exc_no|random_event>
   │     │       new NPC  → ⚙️ python3 scripts/oracle.py character
   │     │                   🎲 Special Trait (data/adventure_crafter/character_special_trait.json)
   │     │                   🎲 Identity + Descriptors (data/mythic/elements/*.json if hard-coded, else canon read)
   │     │
   │     ├─ C8. DETAIL / INSPIRATION (no yes/no needed) → Discover Meaning
   │     │       ⚙️ oracle.py pair actions|descriptors · oracle.py meaning <t> · oracle.py elements "<Table Name>"
   │     │       🎲 1d100 (31 Elements in data/mythic/elements/; the other 14 = honest roll + 📄 references/canon read)
   │     │
   │     └─ C9. ADVANCE THE PLOT (crafter mode, when a Thread is due)
   │             ⚙️ python3 scripts/adventure_crafter.py turning-point --campaign <dir> [--existing]
   │             🎲 Thread (Threads-List invoke) → 🎲 2–5 Plot Points (theme die + 1d100)
   │                Conclusion / None / Meta ranges hard-coded (data/adventure_crafter/plot_point_structure.json)
   │                Plot Point title read from 📄 references/canon/The-Adventure-Crafter.md
   │                Invoked Characters → ⚙️ oracle.py character-list --campaign <dir>  (a New result → C7 Character Crafter)
   │
   ├─ C10. END THE SCENE  (trigger: primary action resolves · narrative shift · mood · chosen auto-interrupt)
   │
   └─ C11. BOOKKEEPING
   │        ├ Chaos Factor:  ⚙️ python3 scripts/state.py chaos <-1 if PC in control | +1 if chaotic> <CF>   (clamp 1–9)
   │        ├ Update Lists (add weighted ≤3 / remove dead) — 📄 campaign-state.md
   │        ├ Overlays:
   │        │     Keyed Scenes      → ⚙️ python3 scripts/dice.py keyed 1d10 <target>   🎲
   │        │     Thread Progress   → ⚙️ python3 scripts/dice.py thread-discovery <points>   🎲 (Plot Armor; Discovery Check)
   │        ├ LORE HARVEST (if canon/sourcebook/module loaded)
   │        │     📄 references/lore-harvest.md  → spawn a Task-tool subagent over setting-canon.md + the scene
   │        │     → returns new Characters/Threads/Features to add to the Lists
   │        ├ SELF-AUDIT GATE (silent)   📄 references/discipline/self-audit.md
   │        │     a scene may not be sent unless something real was risked/moved; else add an edge
   │        └ Overwrite <campaign>/campaign-state.md
   │
   ├─ NEW-ADVENTURE CHECK
   │     IF the active Threads List is empty (main Thread concluded) → PHASE D
   │     ELSE → back to C1   (next turn begins at PHASE A)
   ▼

╔═══════════════════════════════════════════════════════════════════════════╗
║  PHASE D — NEW ADVENTURE   (sub-loop; a campaign is a series of these)      ║
╚═══════════════════════════════════════════════════════════════════════════╝
   ├ Archive the concluded adventure's Lists; carry forward only still-relevant Characters/Threads
   ├ ⚙️ adventure_crafter.py themes --style <…>      (roll fresh Theme priorities)
   ├ Start fresh per-adventure Threads & Characters Lists (campaign roster persists)  — 📄 campaign-state.md
   └ Build a new First Scene (B8) → PHASE C
```

---

## Full inventory

### ⚙️ Scripts (all randomness + mechanics live here)
| Script | Commands invoked in play | Rolls / does |
|---|---|---|
| `scripts/dice.py` | `fate`, `check`, `scene`, `roll`, `table`, `thread-discovery`, `keyed` | Fate Chart/Check, Scene Test, generic & table rolls; **auto-chains the Random Event** on a triggered Fate Question |
| `scripts/oracle.py` | `event`, `event-focus`, `pair`, `meaning`, `elements`, `list`, `character`, `answer` | Full Random-Event chain (Focus→List→Meaning), weighted List invoke, Character Crafter, answer-keyed tables |
| `scripts/adventure_crafter.py` | `themes`, `theme`, `turning-point` | Style-weighted Themes; Turning Point with Plot Points (Conclusion/None/Meta hard-coded) |
| `scripts/state.py` | `init`, `chaos`, `validate` | Copy state template; clamp Chaos 1–9; validate the state file |
| `scripts/system.py` | `route`, `show` | Print the RPG↔Mythic routing rule / the campaign's System Profile |
| `scripts/build_data.py` | *(offline)* | Rebuild & verify all JSON tables from canon (not called during play) |

### 🗃️ Data the scripts roll on (`data/`)
- **mythic core (12):** `fate_chart`, `fate_check`, `event_focus`, `scene_adjustment`, `scene_test`, `npc_behavior`, `npc_statistics`, `discovery_fate_question`, `meaning_actions_1`, `meaning_actions_2`, `meaning_descriptors_1`, `meaning_descriptors_2`
- **mythic elements (31 hard-coded + 14 canon-fallback):** `data/mythic/elements/*.json` (Locations, Characters, Objects, …) + `_index.json`
- **adventure_crafter (5):** `plot_point_theme`, `random_themes`, `themes`, `plot_point_structure`, `character_special_trait`
- `data/manifest.json` (build report + checksums)

### 📄 Markdown read during play
| When | File(s) |
|---|---|
| Every turn (spine) | `SKILL.md`, `references/discipline/{creed,softening-tells,self-audit}.md` |
| The loop in detail | `references/playloop.md` |
| AC ↔ Mythic seam | `references/combined-use.md` |
| Lore subagent | `references/lore-harvest.md` |
| Rules lookups | `references/mythic/00_index.md`, `references/adventure-crafter/00_index.md`, `references/canon/{Mythic-GME,The-Adventure-Crafter}.md` |
| Session Zero / adaptation | `references/adapting/{00_overview,adapt-ruleset,adapt-character-creation,adapt-adventure,adapt-lore,compatibility-spec}.md` |
| Genre tone | `references/genres/*.md` |
| Templates → campaign files | `assets/templates/{campaign-state,character-sheet,system-profile,setting-canon,session-zero-checklist}.md` |
| Deep reference | `references/workflow-and-tables.md` |

### 📝 Live campaign files (written, not shipped)
`campaign-state.md` (source of truth) · `system-profile.md` · `character-sheet.md` · `setting-canon.md` · `keyed-scenes.md` · `archive.md`

---

### One-line summary of the cycle
**Load state & Creed → frame scene → ⚙️ Scene Test → play & "what do you do?" → resolve via ⚙️ Fate Question (auto-chaining a ⚙️ Random Event) or the ⚙️ System Profile or a ⚙️ Turning Point → ⚙️ adjust Chaos + update Lists + lore-harvest + self-audit + write state → new adventure when Threads conclude → repeat.**
