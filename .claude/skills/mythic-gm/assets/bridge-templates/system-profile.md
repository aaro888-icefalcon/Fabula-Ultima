# System Profile — <RPG>   (hook: resolve)

## Operative
THE RPG RESOLVES PC ACTIONS — a Fate Question does NOT. Stop at rung 1 of the ladder: if the
system has a check for it, roll the system (`gm/roll.py` / `dice.py roll <expr>`), never a Fate
Question. Use the system's own check WHEN the PC:
- attempts a **skill / ability / stat** task with real stakes (climb, sneak, persuade, lore…)
- invokes a **trait / virtue / vice / passion / bond / drive** (roll it — it can inspire OR madden)
- **attacks / defends / takes a save** or resists harm
- opposes another character (opposed/contest), or pushes a **subsystem** the RPG models
Fate Questions are ONLY for world/NPC uncertainty the rules don't cover ("is the bridge guarded?").
Per scene: did every PC task/trait/passion go through the system check? If you reached for a Fate
Question on a PC's own competence, you broke this rule.

## Profile
- Dice convention: <e.g. d20+mod / 2d6+stat / Xd6 pool>
- Express a roll as: <dice.py roll string, e.g. 1d20+5  ·  or the companion's gm/roll.py call>
- Core resolution: <vs-DC / opposed / PbtA 6-,7-9,10+ / count ≥ N>
- Degrees of success?: <yes|no>  (drives Fate-Question Exceptional mapping in rule-mode)
- Stats / skills: <list>
- Traits / passions / virtues (and how a check on one works): <list + mechanic>
- Defenses / health: <AC, HP, saves, harm clock>
- Combat: initiative <…>; attack <…>; damage <…>; defeat/death <real: death/maiming/capture>
- NPC stat units: <AC / HP / damage dice / clock>  (for on-the-fly NPC Statistics)
- Routing default: RPG resolves <combat, skills, traits, passions, saves>; defer to Fate Questions
  ONLY for <world questions the rules don't model>
- Subsystems as Fate Questions: <sanity / hacking / none>
