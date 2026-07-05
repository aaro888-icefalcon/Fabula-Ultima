#!/usr/bin/env python3
"""
brief.py — regenerate the <!-- BRIDGE-BRIEF --> … <!-- /BRIDGE-BRIEF --> block in SKILL.md
from bridge/, by delegating to the engine's `bridge.py brief <bridge> --markdown`. Run this
whenever bridge/ changes so the always-on operative rules in SKILL.md stay in sync.

  brief.py            # rewrite SKILL.md's brief block in place
  brief.py --print    # just print the regenerated block
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "SKILL.md")
BRIDGE = os.path.join(ROOT, "bridge")
START = "<!-- BRIDGE-BRIEF:"
END = "<!-- /BRIDGE-BRIEF -->"


def gen_brief():
    dice = engine.find_dice()                       # .../mythic-gm/scripts/dice.py
    bridge_py = os.path.join(os.path.dirname(dice), "bridge.py")
    if not os.path.isfile(bridge_py):
        sys.exit(f"engine bridge.py not found next to {dice}")
    out = subprocess.run([sys.executable, bridge_py, "brief", BRIDGE, "--markdown"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"bridge.py brief failed:\n{out.stderr or out.stdout}")
    return out.stdout.strip()


def main(argv):
    block = gen_brief()
    if "--print" in argv:
        print(block)
        return 0
    text = open(SKILL, encoding="utf-8").read()
    s, e = text.find(START), text.find(END)
    if s == -1 or e == -1:
        sys.exit("SKILL.md has no BRIDGE-BRIEF markers to replace.")
    new = text[:s] + block + text[e + len(END):]
    with open(SKILL, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"↻ updated BRIDGE-BRIEF in {SKILL}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
