#!/usr/bin/env python3
"""
engine.py — the ONLY module in fabula-ultima that touches randomness.

Every random resolution in this companion is delegated to the mythic-gm engine's
`scripts/dice.py`, so all dice stay engine-honest, shown, and citable. fu.py,
statgen.py, worldgen.py, etc. must call THIS module and never `random.*`.

Fabula Ultima rolls mixed pools (e.g. a d10 and a d8 together). dice.py's `roll`
only takes a uniform NdM, so we roll each die separately through the engine and
reassemble the pool here — every single face still comes from dice.py.

CLI (used for the Phase-0 round-trip proof and ad-hoc rolls):
  engine.py where                 # print the resolved dice.py path
  engine.py die 10                # roll one d10 through the engine
  engine.py pool 10 8             # roll a d10 + d8 pool (a Fabula check's dice)
  engine.py roll 2d6+3            # pass-through generic roll
  engine.py table <path|slug>     # roll a built list table via dice.py
  engine.py selftest              # prove the round-trip end to end
"""
import os
import re
import subprocess
import sys

_DICE_CACHE = None


def _candidate_dice_paths():
    """Yield candidate locations of mythic-gm/scripts/dice.py, best guess first."""
    env = os.environ.get("MYTHIC_GM_DIR")
    if env:
        yield os.path.join(env, "scripts", "dice.py")
        yield os.path.join(env, "dice.py")

    here = os.path.dirname(os.path.abspath(__file__))       # .../fabula-ultima/scripts
    skill_root = os.path.dirname(here)                       # .../fabula-ultima
    p = skill_root
    # Walk up the tree; at each level look for a sibling mythic-gm, or one under a
    # (possibly hidden) skills root. Covers both the installed layout (skills siblings)
    # and dev layouts where the companion lives outside the skills dir.
    for _ in range(8):
        parent = os.path.dirname(p)
        yield os.path.join(parent, "mythic-gm", "scripts", "dice.py")
        yield os.path.join(p, "mythic-gm", "scripts", "dice.py")
        for sk in ("skills", ".claude/skills", ".config/claude/skills"):
            yield os.path.join(p, sk, "mythic-gm", "scripts", "dice.py")
            yield os.path.join(parent, sk, "mythic-gm", "scripts", "dice.py")
        p = parent

    for base in ("~/.claude/skills", "~/.config/claude/skills", "/mnt/skills",
                 "/mnt/user-data/skills", "/opt/skills"):
        yield os.path.join(os.path.expanduser(base), "mythic-gm", "scripts", "dice.py")


def find_dice():
    """Absolute path to the engine's dice.py, or exit with a clear message."""
    global _DICE_CACHE
    if _DICE_CACHE:
        return _DICE_CACHE
    for cand in _candidate_dice_paths():
        if cand and os.path.isfile(cand):
            _DICE_CACHE = os.path.abspath(cand)
            return _DICE_CACHE
    sys.exit(
        "engine.py: could not locate mythic-gm/scripts/dice.py.\n"
        "  Fabula Ultima is a companion skill — it needs the mythic-gm engine.\n"
        "  Set MYTHIC_GM_DIR=/path/to/mythic-gm, or install mythic-gm as a sibling skill."
    )


def _run_dice(args):
    """Invoke dice.py with args; return stdout. Raises on non-zero exit."""
    dice = find_dice()
    proc = subprocess.run(
        [sys.executable, dice, *args],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"dice.py {' '.join(args)} failed:\n{proc.stderr or proc.stdout}")
    return proc.stdout


_FACES_RE = re.compile(r"\[([0-9,\s]+)\]")
_TOTAL_RE = re.compile(r"→\s*(-?\d+)")


def roll_expr(expr, mode=None):
    """Delegate a generic NdM[+/-K] roll to dice.py. Returns
    {'expr','faces':[int],'total':int,'raw':str}. `mode` may be 'adv'/'dis'."""
    args = ["roll", expr] + ([mode] if mode else [])
    out = _run_dice(args)
    faces = []
    m = _FACES_RE.search(out)
    if m:
        faces = [int(x) for x in m.group(1).split(",") if x.strip()]
    t = _TOTAL_RE.search(out)
    total = int(t.group(1)) if t else (sum(faces) if faces else None)
    return {"expr": expr, "faces": faces, "total": total, "raw": out.strip()}


def roll_die(sides):
    """Roll ONE die of `sides` through the engine; return its integer face."""
    if sides not in (4, 6, 8, 10, 12, 20, 100):
        # FU attribute dice are d6/d8/d10/d12, but allow any positive size.
        if not isinstance(sides, int) or sides < 2:
            raise ValueError(f"bad die size {sides!r}")
    res = roll_expr(f"1d{sides}")
    if res["faces"]:
        return res["faces"][0]
    return res["total"]


def roll_pool(sides_list):
    """Roll a pool of individually-sized dice (e.g. [10, 8]) each through the
    engine. Returns {'dice':[{'sides','face'}], 'faces':[int]}."""
    dice = []
    for s in sides_list:
        face = roll_die(s)
        dice.append({"sides": s, "face": face})
    return {"dice": dice, "faces": [d["face"] for d in dice]}


def roll_table(path_or_slug):
    """Delegate a built list-table roll to dice.py. Returns {'roll','value','raw'}."""
    out = _run_dice(["table", path_or_slug])
    r = re.search(r"1d\d+\s*=\s*(\d+)", out)
    v = re.search(r"→\s*(.+?)\s*(?:\[src|$)", out)
    return {
        "roll": int(r.group(1)) if r else None,
        "value": v.group(1).strip() if v else None,
        "raw": out.strip(),
    }


def fate(odds, cf, bridge_dir=None):
    """Delegate a Fate Question to dice.py (world/NPC uncertainty only). Returns raw text."""
    args = ["fate", odds, str(cf)]
    if bridge_dir:
        args += ["--bridge", bridge_dir]
    return _run_dice(args).strip()


# --------------------------------------------------------------------------- CLI
def _main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "where":
        print(find_dice())
    elif cmd == "die":
        print(roll_die(int(argv[1])))
    elif cmd == "pool":
        res = roll_pool([int(x) for x in argv[1:]])
        print(res["faces"], "  ", res)
    elif cmd == "roll":
        print(roll_expr(argv[1], argv[2] if len(argv) > 2 else None)["raw"])
    elif cmd == "table":
        print(roll_table(argv[1])["raw"])
    elif cmd == "selftest":
        return _selftest()
    else:
        sys.exit(f"engine.py: unknown command {cmd!r}")
    return 0


def _selftest():
    print("engine.py self-test — proving the mythic-gm round-trip")
    print(f"  dice.py: {find_dice()}")
    ok = True

    r = roll_expr("2d6+3")
    print(f"  roll 2d6+3 -> faces={r['faces']} total={r['total']}")
    ok &= (len(r["faces"]) == 2 and r["total"] == sum(r["faces"]) + 3)

    faces = [roll_die(10) for _ in range(40)]
    print(f"  40x d10 -> min={min(faces)} max={max(faces)} (expect within 1..10)")
    ok &= (min(faces) >= 1 and max(faces) <= 10)

    pool = roll_pool([10, 8])
    print(f"  pool d10+d8 -> {pool['dice']}")
    ok &= (pool["dice"][0]["sides"] == 10 and pool["dice"][1]["sides"] == 8
           and 1 <= pool["faces"][0] <= 10 and 1 <= pool["faces"][1] <= 8)

    print("  RESULT:", "PASS ✓" if ok else "FAIL ✗")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
