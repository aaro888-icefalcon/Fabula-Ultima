# System Profile — Fabula Ultima  (hook: resolve)

## Operative
- When a PC or NPC **attempts something**, resolve it with `scripts/fu.py` — NOT a Fate Question. Trigger list (the WHEN → the CLI):
  - Any attribute Check (GM names 2 of DEX/INS/MIG/WLP + a DL of 7/10/13/16) → `fu.py check <dieA> <dieB> --dl N [--bond N] [--mod N] [--sit ±2]`
  - Attack → `fu.py attack --weapon <key> --attrs <dieA> <dieB> --target <creature>`  (DL = target Defense)
  - Offensive spell / Ritual → `fu.py spell <key> --attrs <INS-die> <WLP-die> --target <creature>`  (DL = Magic Defense)
  - Contest / race / clash of wills → `fu.py opposed <dieA> <dieB> --vs <dieC> <dieD>` ; cooperation → `fu.py group …` ; lore/search with no DL → `fu.py check` (omit --dl, read the Result band)
  - Apply harm → `fu.py damage <target> <amount> <type>` (auto affinity + Crisis) ; afflict → `fu.py status <sheet> +<status>`
- **Crit** = the two dice match AND show ≥6 → automatic success + an opportunity. **Fumble** = double 1 → automatic failure, the PC gains 1 Fabula Point, opposition gets an opportunity. **HR** (higher die) drives damage/effect size.
- A **Fate Question** answers world/NPC uncertainty the rules don't cover — NEVER a PC's own skill, attack, spell, save, or contest.
- At **0 HP**, `fu.py damage` prints the **Surrender / Sacrifice** fork verbatim — the choice is the player's; never auto-kill a PC.
- Bond dice and Fabula rerolls are declared **before** the reveal (`--bond`); they cannot be retconned after seeing the dice.

## Dice & resolution
Two dice per Check (the two chosen Attributes' dice, each d6–d12), summed + modifiers vs the DL. Difficulty ladder: 7 Easy · 10 Normal · 13 Hard · 16 Very Hard (when unsure, use 10). Situational edge = ±2. Success is never re-rolled to "confirm"; multi-step tasks use a Clock (`fu.py clock`).

## Stats & combat units
Attributes are die sizes (d6/d8/d10/d12). Defense = current DEX die (+armor; martial armor sets a fixed value); Magic Defense = current INS die (+bonuses). Damage is `HR + N` of a type; the target's Affinity (Vulnerable ×2 / Resistant ½ / Immune 0 / Absorb heals) is applied by `fu.py damage`. A creature at ≤ half max HP is in **Crisis**.

## NPC stat units & death
NPCs/villains are built with the design math (`scripts/statgen.py`, data/npc_design.json): all are **soldiers** unless promoted to **elite** (2× HP, 2 turns) or **champion(N)** (N× HP, N turns). Villains hold **Ultima Points** (minor 5 / major 10 / supreme 15), spent visibly via `fu.py points ultima`. NPCs simply die at 0 HP; only PCs get the Surrender/Sacrifice choice. Defeat, Limit-style Theme changes on Surrender, and permanent death (Sacrifice) are real.
