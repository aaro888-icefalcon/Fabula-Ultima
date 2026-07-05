# Using Mythic + The Adventure Crafter together (routing)

Default = **Mythic 2e** rules (they supersede the older Adventure Crafter book guidance). **Thread = Thread.** Use Mythic 2e Lists. The PC is *not* on the Characters List but may be Chosen on a blank.

## Where the Adventure Crafter plugs in
- **First Scene:** generate 1–3 Turning Points → seed Threads (Threads) & Characters.
- **Interrupt Scenes (crafter mode):** replace the Random Event with a **Turning Point** (`adventure_crafter.py turning-point`). Altered Scenes stay pure Mythic.
- Invoked elements are added to the Lists **during** Plot-Point generation (weighted ≤3), then edited normally in Bookkeeping.

## Event Focus → List invoke (hard-coded in `oracle.py` FOCUS_ROUTING; run `oracle.py event`)
When a Random Event's Focus references a List, the engine auto-rolls it and chains a Meaning pair:

| Event Focus | Invoke | Then |
|---|---|---|
| NPC Action / NPC Negative / NPC Positive | Characters List | Meaning pair = what happens |
| Move Toward / Move Away / Close A Thread | Threads List | (Close = Thread **Conclusion** → end & remove the Thread) |
| New NPC | — | generate via Character Crafter (`oracle.py character`) |
| Remote Event / Ambiguous / PC Negative/Positive / Current Context | — | Meaning pair only |

When combining with the Adventure Crafter, all PC/NPC references on the Event Focus become just **Characters** (roll the Characters List — PCs are added to it in that mode); the rest of the Focus result still applies.

## Rolling on a List — two modes (hard-coded in `oracle.py roll_list`)
- **Mythic Random Event** (`oracle.py thread-list/character-list --campaign <dir>`): die scales to fullness → usually hits an entry; a blank → **Choose Most Logical** or roll again.
- **Adventure Crafter Plot-Point invoke** (`adventure_crafter.py`, full 1d25): blanks are common → **New Thread/Character** or **Choose Most Logical**. A New Character → Character Crafter (Special Trait + Identity + Descriptors).

## Themes
Assemble the adventure's 5 Theme priorities (`adventure_crafter.py themes --style …`, weighted by RPG style). If you also use a Mythic genre Theme, set it as First Priority via the Theme Translation Table (Mythic **Horror** ↔ AC **Tension**); roll the rest.

## Conclusion plot point
If an Altered/Interrupt Turning Point yields **Conclusion** (1–8) on the Plot Points Table, the invoked Thread/Thread ends this scene — engineer the ending and remove it from the List in Bookkeeping.
