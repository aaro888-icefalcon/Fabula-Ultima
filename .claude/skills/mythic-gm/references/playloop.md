# Mythic-GM — Verified Play Loop & RPG Integration

_Companion spec to the build plan. Every mechanic below is checked against the converted **Mythic GME 2e** text; page references are to the book. This is the backbone the `SKILL.md` operating manual will encode._

---

## Part 1 — Verification result

**Method.** Cross-checked the play-loop sketch in the plan against `Mythic-GME.md` (Scenes, Fate Questions, Random Events, Chaos Factor chapters).

**Confirmed correct:**

| Mechanic | Rule (verified) | Source |
|---|---|---|
| Chaos Factor range/seed | Value **1–9**, starts at **5**. | Fate Questions ch. (p. 20–21) |
| Chaos Factor adjustment | End of scene: PC **mostly in control → −1**; scene **chaotic/out of control → +1**; clamp 1–9 (ignore overflow). | p. 20–21 |
| Scene Test | Roll **1d10** vs current CF. **Over CF → Expected Scene.** **≤ CF → changed scene.** | Testing the Expected Scene (p. 67) |
| Random Event trigger (Fate Q) | On the d100 (or 2d10 Fate Check), a **doubles** result (11, 22, …) whose **digit ≤ CF** fires a Random Event. The roll **still answers** the question. | Fate Questions (p. 24); Random Events (p. 36) |
| Random Event trigger points | Two only: **when a Fate Question is asked**, and **when a Scene is generated** (an Interrupt). | Random Events (p. 35) |
| First Scene | **Not tested** — created directly (Inspired Idea / Random Event / Meaning Tables / 4W); seed the Lists. | The First Scene (p. 63–66) |
| Lists | **Threads** (objectives) + **Characters** (NPCs); updated end of scene; used as **random tables** for Random Events. | Lists (p. 12, 60) |

**Correction found (important).** The Scene-Test odd/even mapping is the opposite of the intuitive guess and the sketch left it unspecified:

> ≤ CF and the d10 is **ODD (1,3,5,7,9) → ALTERED Scene**; ≤ CF and **EVEN (2,4,6,8) → INTERRUPT Scene**. (p. 67)

(The natural assumption "odd = interrupt" is **wrong**.) Verified by the book's own example: test roll of **2**, CF 4 → Interrupt (2 is even, 2 ≤ 4). The scripts must encode odd→Altered / even→Interrupt.

**Under-specification fixed.** The sketch folded the first scene into the same numbered loop; the real procedure special-cases it (no test). And it didn't distinguish the **two modes of Fate Question** (narrative vs. rule-replacement), which is central to RPG integration (Part 3).

**Adventure Crafter & preset content — re-checked (Parts 5–6).** Two further corrections from the source:
- The Scene-Test *within-CF* branch is **mode-dependent**: with the Adventure Crafter, an Interrupt is generated as a **Turning Point** (not a Mythic Random Event); with a prepared adventure, you use **neither Altered nor Interrupt** — a within-CF roll instead **adds** a Random Event to the Expected Scene. The earlier spec applied the pure-Mythic branch universally.
- Mythic 2e's "Using The Adventure Crafter With Mythic" **supersedes** the older rules printed in The Adventure Crafter (e.g., 2e uses the Crafter only for the First Scene and Interrupts, and uses Mythic 2e's List rules). The skill must default to the 2e rules, not the AC book's.

**Conclusion:** the loop's structure was sound; it is now concrete, corrected (odd/even; first-scene special-casing; two Fate-Question modes), and made **mode-aware** for the Adventure Crafter and preset/prepared content (Parts 5–6).

---

## Part 2 — The concrete play loop (executable)

### A. Once per campaign — Session Zero & First Scene
1. **Set up.** Chaos Factor = **5**. Create the Lists (Threads, Characters; **+ Adventure Features** if a prepared adventure). Choose genre/stakes vocabulary; load (or adapt) the RPG system profile and setting canon. **Select the Adventure Source mode — Pure Mythic / Adventure Crafter / Prepared Adventure** (Part 6); record any Keyed Scenes. Create the PC (via the RPG — see Part 3).
2. **First Scene (not tested).** Build it per the mode: **Pure Mythic** → Inspired Idea / a Random Event / Meaning-Table word pairs / 4W; **Adventure Crafter** → 1–3 Turning Points; **Prepared Adventure** → the module's starting point (Inspired-Idea approach). **Seed the Lists** from it. Then play it out (step C onward).

### B. Begin each subsequent Scene — frame & test
3. **Frame the Expected Scene** — what you think happens next, usually driven by what the PC intends to do.
4. **Scene Test** — `dice.py scene <CF> --mode <pure|crafter|prepared>` rolls 1d10; the **within-CF branch depends on the Adventure Source mode** (full table in Part 6):
   - **roll > CF →** Expected Scene runs as framed (all modes).
   - **roll ≤ CF and ODD → Altered Scene** (Pure Mythic & Crafter): begin in the next-most-expected way — Next Expectation (default), a Tweak, a Fate Question, Meaning-Table inspiration, or `dice.py scene-adjust` (1d10 Scene Adjustment Table: add/remove Character, increase/reduce Activity, add/remove Object, or 7–10 = make 2 adjustments).
   - **roll ≤ CF and EVEN → Interrupt Scene** (Pure Mythic & Crafter): discard the expectation and open the scene on **a Random Event (step F) in Pure Mythic**, or **an Adventure Crafter Turning Point in Crafter mode** (Part 5).
   - **Prepared Adventure mode:** **no Altered/Interrupt** — a within-CF roll instead generates a Random Event that is **added to** the Expected Scene as extra content (Part 6b).

### C. Play the Scene — the moment-to-moment loop
5. Describe the situation; **surface only what the PC can perceive.**
6. **"What do you do?" → STOP and WAIT.** Never resolve the player's decision for them.
7. When the player declares an action, **route the uncertainty** (the integration seam, Part 3):
   - **The RPG covers it** (attack, skill check, save, spell) → resolve with the **system profile** via `system.py`: *pre-commit the stakes, roll, lock the outcome in a bracketed block, then narrate.*
   - **The RPG is silent** (is the door locked? does the guard believe me? is there a back way? did reinforcements come?) → **Fate Question** (step D).
8. **NPC behavior — NPCs act to win.** When an NPC acts: trivial action → follow expectation; **consequential action → frame it as a Fate Question** ("Does the NPC do X / continue?") or roll a Meaning Table if you have no idea, then read the **NPC Behavior Table** (Yes = as expected · No = next-most-expected · Exc Yes = expected, intensified · Exc No = opposite/intensified · Random Event = extra action from a Meaning Table). Never default to the *convenient* expectation for anything that matters; consult **setting canon** before inventing; voice briefly.

### D. Fate Question procedure (narrative mode)
9. Phrase a yes/no question; assign **Odds** (Impossible … 50/50 … Certain).
10. `dice.py fate <odds> <CF>` → reads the **Fate Chart** at the current CF, returns **Yes / No** and **Exceptional Yes / Exceptional No** (extreme rolls).
11. **State the raw result first**, then interpret (offer 1–2 readings), then integrate.
12. **Check for a Random Event:** the d100 was **doubles** and **digit ≤ CF** → also run step F (the answer still stands).

### E. Meaning Tables (inspiration on demand)
13. For any open-ended "what/who/where" need, `oracle.py meaning <table>` rolls a word pair from Actions / Descriptors / Elements (e.g., Characters, Locations, Objects…) and returns the exact entries for interpretation.

### F. Random Event procedure
14. `oracle.py event-focus` → the **Event Focus** (e.g., Remote Event, NPC Action, Introduce/Move-Toward/Away a Thread, NPC Positive/Negative, PC Positive/Negative, Ambiguous, Current Context, etc.). If the focus targets a List, `oracle.py thread-list/character-list --campaign <dir>` rolls on it (two-stage).
15. `oracle.py meaning actions` (and others as needed) → word pair(s) → **interpret in context** and fold into the scene.

### G. End-of-Scene bookkeeping (every scene)
**End the scene** when one fires: the **primary action resolves**, a **narrative shift**, **mood** (it's run out of steam), or a chosen **auto-Interrupt** next. Then:
16. **Adjust Chaos Factor:** PC mostly in control → **−1**; scene was chaotic → **+1** (clamp 1–9). `state.py chaos ±1`.
17. **Update Lists:** add/remove Threads and Characters (in **Crafter** mode, Invoked elements were already added *during* Turning-Point generation — don't double-add; in **Prepared** mode, also maintain the Adventure Features List).
18. **Check overlays:** **Keyed Scenes** — `dice.py keyed-check` evaluates every active Trigger (per-scene die rolls, Counts, tallies, real-time); fires flag the **next** scene (Part 6a). **Thread Progress Track** (if a Focus Thread is active) — mark Progress/Flashpoint (+2 each), force a phase Flashpoint if due, honor **Plot Armor** (the Focus Thread can't resolve early), and run a **Discovery Check** if stalled (see the Workflow Review, A2).
19. **Advance offscreen clocks** (factions/threats). *(Note: the Adventure Crafter is the Interrupt-Scene generator in Crafter mode, not a generic bookkeeping advance; its "generate-ahead outline" is a Session-Zero option that becomes a Prepared Adventure.)*
20. **Run the SELF-AUDIT gate** (did dice decide every uncertainty? stakes pre-committed? nothing softened? did something real move?).
21. **Overwrite `campaign-state.md`** (Chaos, Lists, Keyed-Scene Counts, active Turning Point, mode). → back to step 3.

### What is scripted vs. judgment
**Always scripted (honest RNG, shown):** Scene Test, Fate Chart/Check, the doubles/Random-Event check, Event Focus, every Meaning-Table and List roll, Scene Adjustment, Turning Points, and all RPG dice. **Claude's judgment:** framing the Expected Scene, phrasing questions and assigning Odds, interpreting results, voicing NPCs, deciding "in control?" for the CF shift — each gated by the discipline spine.

---

## Part 3 — Integration with a pre-existing RPG ruleset

### 3.1 The core seam (the book's own model)
> "If you're using Mythic with another role-playing game, then Mythic will act as the Game Master by answering your questions while you use the rules of your chosen RPG to handle the situations they cover, such as combat and skill resolution." — *Mythic With Another RPG* (p. 73)

So the division of labor is fixed:

| The **RPG ruleset** owns | **Mythic** owns |
|---|---|
| Character creation & advancement | What scene happens; pacing (Chaos Factor) |
| Task/skill resolution, attacks, saves, damage | Any yes/no the rules don't cover |
| Combat math, initiative, HP/conditions | The unexpected (Random Events, Interrupts) |
| Spells/powers mechanics | NPC intentions, reactions, the "GM call" |

### 3.2 The Mythic ↔ mechanics spectrum
Integration is a **dial**, not a switch (*Using Mythic as an RPG*, p. 29): full RPG rules at one end, pure Mythic at the other. A campaign can sit anywhere — keep a system's combat but resolve its sanity subsystem with Fate Questions; take only a setting and replace all mechanics; or learn a new system by replacing the parts you don't know yet with Fate Questions. The skill captures the chosen position in the **system profile** so it's applied consistently.

### 3.3 The routing rule (how the engine decides each time)
At every uncertain moment:
1. **Does the system profile define a mechanic for this?** → resolve with the RPG (`system.py`). Pre-commit stakes, roll, lock, narrate.
2. **No?** → **Fate Question** (narrative mode: real CF, honor Exceptional & Random Events).
3. **The player would rather not look up / use the rule?** → **Fate Question in rule-replacement mode** (next section).
Overlap is expected and fine; the profile records the default lean so play is consistent rather than ad hoc.

### 3.4 Two modes of Fate Question (the key subtlety)
The same Fate Chart is read two different ways depending on whether the question is **story** or **stand-in for a rule** (*Chaos, Events, and Exceptional Answers*, p. 30; table "Fate Questions as RPG Rules"):

| | **Narrative Fate Question** | **Rule-replacement Fate Question** |
|---|---|---|
| Chaos Factor | use the **real CF** | **treat CF as 5** (consistency, not tension) |
| Exceptional results | **honored** (degrees of success) | **collapse to plain Yes/No** unless the replaced rule has degrees |
| Random Events (doubles ≤ CF) | **honored** | **usually ignored** (judgment call; honor only if it fits) |

`dice.py fate <odds> --mode rule` forces CF 5 and flags Exceptional/Event suppression, so the engine never has to "remember" to switch — it's encoded.

### 3.5 NPCs, statting on the fly
When the RPG needs an NPC's numbers you don't have, don't stop to stat them: **decide the expected value** (from context + PC power level), then ask a Fate Question — "Does the NPC have a [stat] of X?" — and read the **NPC Statistics Table** (*Determining NPC Statistics*, p. 127): **Yes** = as expected; **Exceptional Yes** ≈ **+25%**; **No** ≈ **−25%**; **Exceptional No** = markedly lower. Output is expressed in the **RPG's own units** (AC, damage dice, HP). The system profile stores the convention so results land in-system.

### 3.6 Combat and subsystems
Combat runs on the **RPG's** loop (initiative, to-hit, damage, conditions) — Claude executes it via `system.py` with honest dice and pre-committed stakes. **Mythic rides alongside:** within the fight, narrative unknowns become Fate Questions ("does the bridge hold?", "does the captain call a retreat?"), and a **doubles-≤-CF** result on any in-combat Fate Question can fire a Random Event mid-battle. Bespoke subsystems (sanity, hacking, chases) are either run by the RPG or **ported as Fate Questions "following the tone and intent of the original rules"** — recorded in the profile.

### 3.7 Character creation, sourcebooks, lore, adventures
- **Char-gen** uses the RPG's rules (adapted to a guided flow by `adapt-character-creation.md`); the sheet is written into `campaign-state.md` in the shape the system profile references.
- **Sourcebooks / bestiaries** (the RPG's published content) become **fodder for the Lists and oracle** — drop a faction/monster/location onto the Lists and let Random Events surface it (*Getting the Most Out of Sourcebooks*, p. 128).
- **Setting lore** → `setting-canon.md` (ground truth over invention).
- **Published adventures** → **Keyed Scenes** + Threads + canon (*Using Mythic With Prepared Adventures*, p. 156; **anti-railroad** — keyed scenes trigger on conditions, the oracle still decides). The **Adventure Crafter** can also *generate* the spine: each Turning Point's Plot Points become Threads the Mythic loop plays out (*Using The Adventure Crafter With Mythic*, p. 171).

### 3.8 Where this lives in the skill
The whole seam is encoded in the per-campaign **system profile** (produced by `references/adapting/adapt-ruleset.md`): the dice convention and core resolution, what the RPG resolves vs. what defers to Fate Questions (3.3), the NPC-stat convention (3.5), combat/death handling, and any subsystems ported as Fate Questions (3.6). The engine reads it every turn — so "integrate with any RPG" reduces to "fill the profile," and the play loop above runs unchanged on top of it.

---

## Part 4 — Worked micro-turn (the seam in motion)

> PC (a fantasy warlock, using a tabletop RPG's rules) attempts a risky summoning.
> 1. **RPG resolves the mechanic:** `system.py` rolls the casting check → **fails badly.** The RPG says "the GM devises a mishap."
> 2. **No GM, so Mythic fills the gap:** narrative Fate Question — "Does something unexpected happen from the failed spell?", Odds **Nearly Certain**, real CF. `dice.py fate nearly_certain <CF>` → **Yes**, and the d100 came up **doubles ≤ CF** → **Random Event.**
> 3. **Random Event:** `oracle.py event-focus` → *Introduce a New NPC*; `oracle.py meaning actions` → "Recruit / Outside." Interpretation: the botched spell pulls in **a stranger from the future**, not a demon.
> 4. **Bookkeeping:** the scene was chaotic → **CF +1**; add Thread "Who is the time-stranger?" and a Characters-List entry; self-audit passes (real dice, real stakes, something moved); write state.

This is the engine working as intended: **the RPG decides the mechanical fact, Mythic decides everything the rules leave open, honest dice drive both, and nothing is softened.** (Adapted from the book's own example, p. 74.)

---

## Part 5 — Integration with **The Adventure Crafter**

**Verification note.** Two sources give *different* combine rules: The Adventure Crafter (2018) and Mythic 2e's own "Using The Adventure Crafter With Mythic" (p. 171–175), which **explicitly updates and supersedes** the older advice ("This section updates those rules…"). **The skill defaults to the Mythic 2e rules** below; the older AC variant (AC also generates Altered Scenes; AC's own List-weighting) is offered only as an opt-in. My earlier spec was too loose here (it had the Adventure Crafter firing at generic "end-of-scene bookkeeping"); the verified seam is more specific.

**The shared seam:** **Adventure Crafter Threads = Mythic Threads** — interchangeable. When combining, use **Mythic 2e List rules** (not the AC book's). The PC is **not** on the Characters List (Mythic rule) but can be Chosen on a blank.

**Two ways to use it — both supported:**
- **(a) Live / interleaved (default).** The Adventure Crafter supplies the **First Scene** and **replaces the Random Event at Interrupt Scenes**. It does **not** drive Altered Scenes (those stay pure Mythic, for speed).
- **(b) Preset outline (generate-ahead).** Pre-generate a chain of Turning Points as an adventure **outline**, then run it as a **prepared adventure** (Part 6). This is the Adventure Crafter's native "build the structure first, from the outside in" mode.

**Concrete live mechanics (mode = Adventure Crafter):**
1. **First Scene:** `adventure_crafter.py turning-point` generates **1** Turning Point (or **2–3** for a richer opening). Its Threads → Threads List; its Characters → Characters List.
2. **Scene Test → Interrupt (even ≤ CF):** instead of a Mythic Random Event, generate an **AC Turning Point** as the Interrupt (more moving parts ⇒ bigger, more dramatic swings). **Altered (odd ≤ CF) stays pure Mythic.**
3. **Turning Point procedure:** roll the **Thread** (1d100 on Threads List → existing / **New Thread** / **Choose Most Logical**); then **2–5 Plot Points** (`3d10`: one die picks the **Theme** via the Plot Point Theme Table, the other two are a d100 on the **Plot Point Table** under that Theme), **Invoking Characters** as Plot Points require. Use **fewer Plot Points (1–4)** if it slows play.
4. **Invoked elements are added to the Lists *during* Plot Point generation** (not in bookkeeping) so later Plot Points in the same Turning Point can reference them — added once per scene, weighted up to **3** entries.
5. **Rolling a List for a Plot-Point Invoke** uses the **full** List (`2d10`: 1st die = section, 2nd = line) regardless of fill, so **blanks are common**. On a blank: **Choose** an existing element **or Add** a new Thread/Character (generate the NPC's Trait/Identity/Descriptors from the AC character tables).
6. **Plot Point = "Conclusion"** ⇒ that Thread/Thread **ends this scene**; remove it from the List afterward.
7. **Themes:** assemble the adventure's AC Themes (Action / Tension / Mystery / Social / Personal); if also using a Mythic themed Event Focus, align them via the **Theme Translation Table** (note: Mythic **Horror** ↔ AC **Tension**).

`adventure_crafter.py` performs every roll (Thread, Theme, Plot Points, list invokes, new-character tables); `campaign-state.md` stores the Threads & Characters Lists, the active Turning Point, and the Theme priority.

---

## Part 6 — Preset & prepared content ("preset rolls"): Keyed Scenes + Prepared Adventures

Two systems inject **pre-set** content into the live loop. Both are **overlays** — they ride on top of the Part 2 loop rather than replacing it.

### 6a. Keyed Scenes — the preset trigger-rolls (p. 149–153)
A **Keyed Scene** is a **Trigger (If) → Event (Then)** pair you set up in advance (or add mid-play), recorded in state on the **Keyed Scenes Record Sheet** (Count · Trigger · Event).
- **Triggers are usually *preset rolls*:** "roll **1–3 on 1d10 each Scene**," a **Count** reaching N, "**X Scenes without Y**," real-time elapsed, or compound conditions. `dice.py keyed-check` rolls **every** active trigger honestly during end-of-scene bookkeeping (or, for the optional "surprise" variant, early in the next scene).
- **On a fire:** the **Event happens at the start of the next Scene**, woven into whatever that scene already is (Expected / Altered / Interrupt). A conceptual Event ("zombie attack," "boss fight") is realized via a **Random Event with Event Focus = Current Context**.
- **Counts / frequency / randomizers / nullification:** triggers may be one-shot, repeatable, reset-on-fire, or **nullified** if the intended thing already happened naturally. Counts live in state.
- This is the most literal reading of **"preset rolls"** — preset If/Then dice checks evaluated each scene; the engine must roll them, never hand-wave them.

### 6b. Prepared (published) adventures (p. 156–165)
- **Roles & priority:** the module owns **structure and detail and has priority**; Mythic steps back to **co-GM** — arbiter of events, answerer of Questions.
- **No Altered/Interrupt Scenes.** Instead, **test the Expected Scene; if the roll is within CF, generate a Random Event that is *added* to the Expected Scene** (extra content), rather than replacing it. (Contrast with an Interrupt, where the Random Event *is* the scene.)
- **A third List — Adventure Features:** module-specific encounters that could surface (wandering-monster tables, recurring visions, the villain's hit-and-run, "a guide finds you"). Seed Threads, Characters, **and** Features from the intro text.
- **Targeting module content:** the special **Prepared-Adventure Event Focus Table** includes **Adventure Features** as a focus, so Random Events point at the module; the **Adventure Features List Sheet** (d4/d6/d8/d10 → 1–25) selects which feature.
- **Scaling for solo:** choose a **Diminisher Value** (½, ⅓, ¼, ⅕) from PC-power-vs-group and apply it to challenge stats as you meet them.
- **One detail at a time:** read only as much module text as the PC is currently encountering; everything unread stays "potential" until met.
- **First Scene** from the module's starting point (Inspired-Idea approach).

### The unifying control — **Adventure Source mode**
Picked at Session Zero and stored in `campaign-state.md`, the mode changes **only** how the Scene Test's *within-CF* branch resolves and how the First Scene / Random Events behave. Everything else — Fate Questions, Chaos Factor, RPG resolution, bookkeeping, the discipline spine — is **identical** across modes. **Keyed Scenes overlay any mode.**

| Adventure Source | Roll **over** CF | Roll **within** CF | First Scene |
|---|---|---|---|
| **Pure Mythic** | Expected Scene | **odd →** Altered (Mythic) · **even →** Interrupt = **Random Event** | Inspired Idea / Random Event / Meaning Tables / 4W |
| **Adventure Crafter** | Expected Scene | **odd →** Altered (Mythic) · **even →** Interrupt = **AC Turning Point** | 1–3 AC Turning Points |
| **Prepared Adventure** | Expected Scene | **Random Event *added* to the Expected Scene** (no Altered/Interrupt) | the module's start (Inspired Idea) |

`dice.py scene <CF> --mode <pure|crafter|prepared>` returns the branch already resolved to the right behavior, so the engine never has to "remember" which integration is active — it reads the mode and routes.

### Worked micro-checks (the overlays in motion)
- **Keyed Scene:** zombie campaign, Trigger "3 Scenes without an attack, then roll 1–5 on 1d10." After the 3rd quiet scene, bookkeeping rolls `dice.py keyed-check` → fires → next scene opens with a **Current-Context Random Event** = the zombies are at the shelter door. Count resets per the Trigger's rule.
- **Adventure Crafter Interrupt:** Scene Test rolls **2** (even, ≤ CF 4) → Interrupt. In Crafter mode, `adventure_crafter.py turning-point` yields Plot Point "A Character Is Incapacitated"; the engine Invokes a new NPC (added to the List mid-generation), and the scene becomes a rescue — bigger swing than a single Random Event.
- **Prepared adventure:** Expected Scene "descend into the catacombs"; test rolls within CF → **add** a Random Event (PC Negative · "Decrease/Freedom") = fierce stairwell winds threatening the torch — a complication layered onto the module's scene, not a replacement.
