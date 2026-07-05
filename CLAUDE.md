# CLAUDE.md — running games of Fabula Ultima in this repo

This repository exists to **play Fabula Ultima solo / GM-less**, with you as the Game Master.
The whole game runs through two skills under `.claude/skills/` (both auto-discovered):

- **`fabula-ultima`** — the Fabula Ultima ruleset + `bridge/` (the content).
- **`mythic-gm`** — the solo scene/oracle/honest-dice engine (the loop). `fabula-ultima`
  **requires** it.

## When the user wants to play

Invoke the **`fabula-ultima`** skill and follow its `SKILL.md` boot sequence. In short:

1. **Load the engine.** `fabula-ultima` runs on `mythic-gm`; load both. Prove the link with
   `python3 .claude/skills/fabula-ultima/scripts/engine.py where`.
2. **Hold the bridge brief.** The operative imperatives are inlined in the
   `<!-- BRIDGE-BRIEF -->` block of `fabula-ultima/SKILL.md` — keep them present in play.
3. **Session Zero if new.** If `.claude/skills/fabula-ultima/campaign/` has no world yet,
   run `python3 .claude/skills/fabula-ultima/scripts/worldgen.py run` (world → group →
   characters). Fabula Ultima has no default setting.
4. **Play the scene loop.** Resolve anything a PC/NPC *attempts* with `scripts/fu.py`
   (Checks, attacks, spells, contests, damage, Crisis) — never a Fate Question for a PC's
   own action. Fire `scripts/fu.py tick <scene#>` at every bookkeeping.

## Non-negotiables

- **Every die goes through the engine.** All randomness is delegated to `mythic-gm`'s
  `dice.py` via `fabula-ultima/scripts/engine.py`. Never invent, guess, or fudge a roll;
  always show it.
- **No softening.** Defeat, Surrender (a forced Theme change), and Sacrifice (permanent
  death) are real. Honor the engine's discipline.
- **Rules live in data, queried lean.** Read one record with `scripts/lookup.py`; don't load
  whole `data/*.json` files into context.

## Saving

Play state lives in `.claude/skills/fabula-ultima/campaign/` and is **not** git-ignored —
commit it to save/resume a campaign (essential on the ephemeral web containers).

## Validating the setup

- `python3 .claude/skills/fabula-ultima/scripts/engine.py selftest` — prove the dice round-trip.
- `python3 .claude/skills/fabula-ultima/scripts/build_data.py --strict` — validate the ruleset (read-only).
- `python3 .claude/skills/mythic-gm/scripts/bridge.py validate .claude/skills/fabula-ultima/bridge` — validate the bridge.
- Note: `mythic-gm/scripts/build_data.py` **regenerates** the engine's table files (it writes),
  so don't run it just to check — use it only after editing engine canon.
