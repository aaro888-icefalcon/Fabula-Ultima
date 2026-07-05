#!/usr/bin/env python3
"""
system.py — apply the per-campaign System Profile for RPG task resolution.

The profile (campaign/system-profile.md, produced by references/adapting/adapt-ruleset.md)
describes the chosen RPG's dice and resolution in plain text. Claude reads it and
resolves actions with honest dice via dice.py. This helper just surfaces the profile
and routes a resolution so the routing is explicit and consistent.

Commands:
  show <campaign_dir>          Print the System Profile's resolution summary
  route <campaign_dir>         Print the seam rule (when the RPG resolves vs a Fate Question)
"""
import os, sys

SEAM = """ROUTING (per uncertain moment):
  1. The System Profile defines a mechanic for this?  → resolve with the RPG (dice.py roll …),
     pre-committing stakes, locking the result in a bracketed block, THEN narrate.
  2. No mechanic (world question)?                    → Fate Question (dice.py fate …, narrative mode).
  3. Player would rather not use the rule?            → Fate Question in rule-mode (dice.py fate … --mode rule).
Precedence: System Profile > uploaded rulebook > Claude's training knowledge.
NPC stats you don't have: decide the expected value, then a Fate Question; read NPC Statistics Table."""

def find_profile(dirpath):
    p = os.path.join(dirpath, "system-profile.md")
    return p if os.path.exists(p) else None

def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h","--help"): print(__doc__); return
    c = a[0]
    if c == "route":
        print(SEAM); return
    if c == "show":
        p = find_profile(a[1]) if len(a) > 1 else None
        if not p:
            print("No system-profile.md found. Create one from assets/templates/system-profile.md "
                  "using references/adapting/adapt-ruleset.md, or play rules-light with Fate Questions.")
            return
        print(open(p, encoding="utf-8").read())
    else:
        sys.exit(f"Unknown command '{c}'. See --help.")

if __name__ == "__main__":
    main()
