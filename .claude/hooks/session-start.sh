#!/bin/bash
# SessionStart hook — make sure this repo is ready to run games of Fabula Ultima.
#
# The play stack is TWO Claude Code skills under .claude/skills/:
#   - fabula-ultima  (the FABULA ULTIMA ruleset + bridge — the "content")
#   - mythic-gm      (the solo/GM-less scene+oracle+honest-dice engine)
# Both are stdlib-only Python 3, so there are NO dependencies to install.
# Instead of installing, this hook VERIFIES readiness (read-only, fast, idempotent):
#   1. python3 is available,
#   2. a real die rolls end-to-end through the mythic-gm engine (proves the
#      companion -> engine link), and
#   3. the Fabula Ultima ruleset validates against its schemas.
#
# It never blocks the session: every check reports and the hook still exits 0.
set -uo pipefail   # deliberately NO -e: a failed check must not abort the session

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
FU="$ROOT/.claude/skills/fabula-ultima/scripts"
ENGINE="$ROOT/.claude/skills/mythic-gm/scripts"
warn=0

if ! command -v python3 >/dev/null 2>&1; then
  echo "‼️  python3 not found — the fabula-ultima / mythic-gm scripts require Python 3." >&2
  exit 0
fi

# 1 + 2. Roll one real d10 through the engine: proves engine.py finds mythic-gm's
#        dice.py AND that the honest-dice round-trip actually executes.
if ! python3 "$FU/engine.py" die 10 >/dev/null 2>&1; then
  echo "‼️  Could not roll through the mythic-gm engine (engine.py die 10 failed)." >&2
  echo "    Fabula Ultima is a companion skill; it needs mythic-gm as a sibling under .claude/skills/." >&2
  warn=1
fi

# 3. Validate the Fabula Ultima ruleset (validate-only; writes nothing).
if ! python3 "$FU/build_data.py" --strict >/dev/null 2>&1; then
  echo "‼️  Fabula Ultima data validation failed (build_data.py --strict)." >&2
  warn=1
fi

if [ "$warn" -eq 0 ]; then
  echo "🎲 Fabula Ultima is ready to play — mythic-gm engine linked, ruleset validated."
  echo "   To begin, say e.g. \"be my GM for Fabula Ultima\" or \"let's play Fabula Ultima\";"
  echo "   the fabula-ultima skill runs Press Start (world creation) if there is no campaign yet,"
  echo "   then the scene loop. Every die is rolled honestly through the engine — never fudged."
fi
exit 0
