# Adapt a ruleset → `system-profile.md`

Goal: extract only what the engine needs to resolve actions, from whatever the source is (an uploaded rulebook, a second skill's rules, or your knowledge of a named system). Fill `assets/templates/system-profile.md`. Confirm anything ambiguous with the player; leave gaps to be resolved by Fate Questions.

## Steps
1. **Dice & resolution.** Identify the core mechanic and write how to express a roll for `dice.py roll` (e.g. d20+mod vs DC; 2d6+stat with 6-/7-9/10+; Xd6 count ≥5). Note **whether it has degrees of success** — this decides whether Fate-Question Exceptional results map to anything in rule-mode.
2. **Stats / skills.** List the attributes/skills the loop and NPC-statting will reference.
3. **Combat & death.** Initiative, to-hit, damage, and how defeat resolves (death/maiming/capture). Keep the discipline: defeat is real.
4. **NPC stat convention.** The units to express NPC Statistics results in (AC, HP, damage dice…), so on-the-fly statting lands in-system.
5. **Routing default.** Note what the RPG resolves vs. what you'll defer to Fate Questions (combat/skills → RPG; world questions → Mythic).
6. **Subsystems.** Any sanity/hacking/chase systems you'd rather run as Fate Questions "in the tone and intent of the original."

## Precedence & gaps
System Profile > uploaded text > training knowledge. If you can't recall or find a rule mid-play, resolve it with a **rule-mode Fate Question** (`dice.py fate <odds> <CF> --mode rule`) and, if it recurs, write it into the profile so play stays consistent.

**Worked example (PbtA-style):** "Dice: 2d6 + the relevant stat (-1..+3). Resolution: 10+ full success, 7-9 partial/cost, 6- failure + a GM move. Degrees: yes (map ExcYes→10+ with a bonus, ExcNo→6- hard). Combat: fictional positioning + the same 2d6 moves; harm is narrative + a Harm clock. NPC stats: descriptive (no AC/HP) — use a Harm clock sized to threat. Route: all action → moves; world questions → Fate Questions."
