# Adapt a published adventure → keyed scenes + seeded Lists (not rails)

A module becomes **available content the oracle plays through honestly**, never a fixed sequence. Set Adventure Source mode = **Prepared Adventure**.

## Steps
1. **Read the intro only.** Pull the module's goals → **Threads List**; its NPCs/locations → **Characters List**; its set-pieces, wandering tables, recurring hazards → **Adventure Features List**. (Read the rest *one detail at a time*, as the PC reaches it.)
2. **Keyed scenes.** For anything the module says "must happen," write a `keyed-scenes.md` entry: a **Trigger** (often a per-scene die, `dice.py keyed 1d10 <target>`, or a Count/condition) → the **Event**. Check triggers in bookkeeping.
3. **Scaling.** Pick a **Diminisher Value** (½, ⅓, ¼, ⅕) from PC-power-vs-the-group-the-module-assumes; apply it to challenge stats as you meet them.
4. **Scene handling (prepared mode):** **no Altered/Interrupt.** Test the Expected Scene; **within CF → add a Random Event to the Expected Scene** (use the Prepared-Adventure Event Focus, which can point at an Adventure Feature). The module keeps priority; Mythic is co-GM.
5. **Anti-railroad (critical):** the dice still decide. If an honest result kills the module's "essential" NPC or skips its intended path, **adapt** — the module is a map, not a script. Apply **Player ≠ PC knowledge**: don't act on module facts the PC hasn't discovered.

## Adventure-Crafter "preset outline"
You can instead *generate* a module: roll a chain of Turning Points ahead of time (`adventure_crafter.py turning-point`) into an outline, then run it as a Prepared Adventure by the same rules.
