# World Subsystems — Fabula Ultima  (hook: world-tick; fired by tick.py at bookkeeping)
# tick.py reads the cadence column: 'every scene' | 'every N scenes' | 'on trigger: …'

## Operative
- Fire `python3 scripts/fu.py tick <scene#>` every bookkeeping — it lists open Clocks and walks the FU duties below. Do NOT skip it.
- Companion bookkeeping each tick: advance every active **villain agenda** and **threat Clock** the world would push this scene; tick in-progress **Projects** and **Rituals**; run the **Fabula-point economy** (a PC with 0 FP starts the next session with 1; a villain who made an entrance granted each PC 1 FP; villains spend **Ultima Points** visibly via `fu.py points ultima`); refresh IP expectations after rests.
- Surface, don't just tick: telegraph a Clock before it fills; a **filled** Clock becomes a Turning Point (Conclusion) or a Random Event (Close a Thread) — never a silent fill.

| subsystem | cadence | advance by |
|---|---|---|
| Villain agenda Clocks | every ~scene of pressure (or on trigger) | advance the villain's goal Clock; on fill → Turning Point. Villains act even offscreen. |
| Threat / doom Clocks | every scene | advance sieges, rituals, pursuits the fiction implies (`fu.py clock tick <id>`). |
| Projects & Rituals | on trigger: downtime / rest | tick PC Projects (crafting, research) and cast Rituals toward completion. |
| Fabula economy | every scene / session bound | 0 FP at session start → +1; villain entrance → +1 to each PC; Surrender → +2. |
| Ultima Points | on villain power play | spend from the villain's pool visibly (`fu.py points ultima -N --reason …`). |
| Rest & resources | on trigger: full/short rest | `fu.py rest` restores HP/MP and clears statuses; recharge Inventory Points. |

# Campaign-specific Clocks (a specific siege, a sorcerer's working, a rival party) are seeded into
# campaign/clocks.json at session zero and tracked there, not hard-listed here.
