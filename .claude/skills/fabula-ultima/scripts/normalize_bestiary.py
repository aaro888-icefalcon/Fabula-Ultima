#!/usr/bin/env python3
"""
normalize_bestiary.py — fix Defense / Magic Defense in the extracted bestiary.

FU stat blocks print (Studying an NPC, Core p.~300):
  • Defense (DEF): a BONUS added to the creature's current Dexterity die size —
    UNLESS it wears martial armor, in which case it's a FIXED number.
  • Magic Defense (M.DEF): ALWAYS a bonus added to the Insight die size.

The extraction captured the printed token as an integer, so `defense`/`magic_defense`
held the *bonus* (or the fixed martial number), not the usable score. This tool
computes the effective scores from each entry's own DEX/INS and rewrites them,
keeping the raw printed value in `defense_bonus` / `magic_defense_bonus`.

Rule for DEF bonus-vs-fixed: FU attribute dice are d6–d12 and DEF bonuses run 0–5,
while martial armor sets a fixed Defense of 10+. So a stored value >= 8 is a fixed
martial Defense (kept as-is); anything < 8 is a bonus (added to the DEX die).

Idempotent: entries that already carry `magic_defense_bonus` are left alone.
Usage: python3 scripts/normalize_bestiary.py [--dry-run]
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXED_DEF_MIN = 8


def main(argv):
    dry = "--dry-run" in argv
    rows = []
    changed_files = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "bestiary", "*.json"))):
        doc = json.load(open(f, encoding="utf-8"))
        touched = False
        for e in doc.get("entries", []):
            if "magic_defense_bonus" in e:
                continue  # already normalized
            attrs = e.get("attributes", {})
            dex, ins = attrs.get("DEX"), attrs.get("INS")
            raw_def, raw_mdef = e.get("defense"), e.get("magic_defense")

            if raw_mdef is not None and ins is not None:
                e["magic_defense_bonus"] = raw_mdef
                e["magic_defense"] = ins + raw_mdef

            if raw_def is not None and dex is not None:
                if raw_def >= FIXED_DEF_MIN:
                    e["defense_bonus"] = None
                    e["defense_fixed"] = True
                    eff_def = raw_def
                else:
                    e["defense_bonus"] = raw_def
                    eff_def = dex + raw_def
                e["defense"] = eff_def
                touched = True
                rows.append((e["key"], f"d{dex}", raw_def,
                             e["defense"], f"d{ins}", raw_mdef, e["magic_defense"]))
        if touched and not dry:
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            changed_files += 1

    print(f"{'DRY-RUN: ' if dry else ''}normalized {len(rows)} entries "
          f"across {changed_files} file(s)")
    print(f"{'key':22} {'DEX':4} {'defRaw':>6} {'DEF':>4}   {'INS':4} {'mdefRaw':>7} {'M.DEF':>5}")
    for r in rows:
        print(f"{r[0]:22} {r[1]:4} {str(r[2]):>6} {str(r[3]):>4}   "
              f"{r[4]:4} {str(r[5]):>7} {str(r[6]):>5}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
