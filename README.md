# Fabula Ultima — solo / GM-less play, configured for Claude Code

This repository is set up to **play [Fabula Ultima](https://www.needgames.it/fabula-ultima-en/)**
(the JRPG-inspired tabletop RPG) solo or GM-less, with Claude Code as your Game Master.
Everything is wired so that opening this repo in Claude Code — in the terminal or on
[the web](https://claude.ai/code) — lets you start a game immediately.

## How it's built: an engine + a companion

Two Claude Code skills live under [`.claude/skills/`](.claude/skills) and are
auto-discovered when you open the repo:

| Skill | Role |
|---|---|
| **[`mythic-gm`](.claude/skills/mythic-gm)** | The **engine** — the solo scene loop, the Mythic GME 2e oracle, The Adventure Crafter, honest scripted dice, and the "no softening" discipline. System-agnostic. |
| **[`fabula-ultima`](.claude/skills/fabula-ultima)** | The **companion** — the full Fabula Ultima ruleset (Checks, classes, spells, equipment, statuses, bestiary) as `data/*.json` behind CLIs in `scripts/`, plus a `bridge/` that fills the engine's hooks (resolution, JRPG interpretation, theme weights, chaos, world-tick, seeds). |

`fabula-ultima` **requires** `mythic-gm`: every die is delegated to the engine's
`dice.py` (via `scripts/engine.py`), so all randomness is honest, shown, and never
fudged. The companion supplies the *world and rules*; the engine owns the *dice and loop*.

## Start playing

Just tell Claude what you want, e.g.:

- *"Be my GM for Fabula Ultima."*
- *"Let's play Fabula Ultima — run Press Start / world creation."*
- *"Continue my Fabula Ultima campaign."*

Claude will:

1. Load the `fabula-ultima` skill (which boots the `mythic-gm` engine).
2. If there's no campaign yet, run **Session Zero / Press Start** — world, then group,
   then characters — via `scripts/worldgen.py run`.
3. Run the engine's scene loop, resolving anything a PC or NPC *attempts* through
   `scripts/fu.py` (Checks, attacks, spells, contests, damage, Crisis) and asking Fate
   Questions only for world/NPC facts the rules don't cover.

## The command surface (what the GM calls under the hood)

You don't need to run these yourself — Claude drives them — but they're the machinery:

```
scripts/engine.py where | selftest          # locate / prove the mythic-gm dice link
scripts/fu.py check <dA> <dB> --dl N         # attribute Check (crit/fumble/High Roll)
scripts/fu.py attack --weapon K --attrs dA dB --target C   # accuracy + damage + affinity
scripts/fu.py spell K --attrs dINS dWLP --target C         # spell + Magic Check vs M.DEF
scripts/fu.py damage <t> <amt> <type> | status <sheet> +<s>
scripts/fu.py points fabula +1 --owner PC | ultima -N --reason "..."   # audited ledgers
scripts/fu.py clock ... | init ... | rest | crisis <t> | tick <scene#>
scripts/sheet.py new <name> --level L --class rogue:3 | validate | render | levelup
scripts/statgen.py npc | villain | monster ...              # build NPCs from the design math
scripts/lookup.py class|spell|skill|weapon|monster|status <name>   # one compact rules card
scripts/worldgen.py steps | run [--genre core|high|natural|techno]
scripts/gen.py npc|villain|monster|faction|front|world      # emergent, genre-aware generation
scripts/state.py init|show|list|get                         # the atomized campaign store
scripts/build_data.py [--strict]                            # validate the ruleset vs schemas
```

(Full detail lives in [`.claude/skills/fabula-ultima/SKILL.md`](.claude/skills/fabula-ultima/SKILL.md).)

## Saving & resuming a campaign

Play state is written under **`.claude/skills/fabula-ultima/campaign/`** (world, entities,
fronts, clocks, points, character sheets). That path is **not** git-ignored on purpose:
**commit it to save your campaign**, so you can resume it in a later session — important on
the web, where each session runs in a fresh, ephemeral container.

## Readiness check on every session

[`.claude/settings.json`](.claude/settings.json) registers a `SessionStart` hook
([`.claude/hooks/session-start.sh`](.claude/hooks/session-start.sh)) that, on each session,
verifies Python 3 is present, rolls one real die through the engine (proving the
companion → engine link), and validates the Fabula Ultima ruleset. There are **no
third-party dependencies to install** — the skills are stdlib-only Python 3.

## Content note

The `mythic-gm` engine bundles the Mythic GME 2e and The Adventure Crafter tables
(© Tana Pigeon / Word Mill Games) for personal use, and `fabula-ultima` bundles the
Fabula Ultima rules data. Keep this repository private for personal play.
