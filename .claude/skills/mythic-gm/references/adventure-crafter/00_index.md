# The Adventure Crafter — rules index

Complete book bundled at **`references/canon/The-Adventure-Crafter.md`** (the full Plot Point Table — 5 Themes — and all tables verbatim). Use it for Plot Point text; the engine rolls the structure honestly.

## How it plugs into Mythic (default: Mythic 2e rules, which supersede the AC book's older advice)
- **Threads = Threads** (interchangeable). Use Mythic 2e List rules.
- Used for the **First Scene** (1–3 Turning Points) and to **replace the Random Event at Interrupt Scenes** (Crafter mode). Altered Scenes stay pure Mythic.
- Invoked Threads/Characters are added to the Lists **during** Plot-Point generation (weighted ≤3).

## Mechanics → engine
| Piece | In canon | Engine |
|---|---|---|
| Turning Point (roll Thread → 2–5 Plot Points) | "Turning Points And Plot Points" | `adventure_crafter.py turning-point` |
| Plot Point Theme Table (1d10 → priority) | "Plot Point Theme Table" | `data/adventure_crafter/plot_point_theme.json` |
| Plot Point Table (1d100 under a Theme) | "Roll On The Plot Point Table" | rolled by `adventure_crafter.py`; **text read from canon** |
| Themes / Theme Translation | "Adventure Themes" | `data/adventure_crafter/themes.json` |
| Threads & Characters Lists, "List Is Full" | "Lists And The Adventure Sheet" | `oracle.py thread-list/character-list` |
| Character Crafting (Descriptors/Identity/Special Trait) | "Character Crafting" | read from canon when adding a Character |

Verified integration detail: `references/playloop.md` (Part 5).
