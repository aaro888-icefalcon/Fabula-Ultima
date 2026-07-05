#!/usr/bin/env python3
"""
tick.py — the MANDATORY end-of-scene bookkeeping step (hook: world-tick). Fire this at EVERY
bookkeeping, not "when relevant." It advances the companion's world subsystems AND emits the
full bookkeeping checklist, so the recurring duties (world-tick, Chaos, List sync, seeds, and the
resolve-debt check) can't silently decay across a long session.

Usage:  python3 scripts/tick.py <bridge_dir> <scene_number> [campaign_dir]
A subsystem row in <bridge>/subsystems.md is:  | name | cadence | advance by |
cadence: 'every scene' | 'every N scenes' | 'on trigger: …'
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def operative(path):
    if not os.path.isfile(path): return []
    out, grab = [], False
    for ln in open(path, encoding="utf-8"):
        s = ln.strip()
        if s.startswith("## "): grab = s.lower().startswith("## operative"); continue
        if grab:
            if s.startswith("#"): break
            if s: out.append(s)
    return out

def due_subsystems(p, scene):
    due = []
    if not os.path.exists(p): return due
    for ln in open(p, encoding="utf-8"):
        if not ln.strip().startswith("|"): continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in ("subsystem","name","") or set(cells[0]) <= set("-"): continue
        name, cadence, advance = cells[0], cells[1].lower(), cells[2]
        if "every scene" in cadence: due.append((name, advance, "DUE"))
        else:
            m = re.search(r"every\s+(\d+)", cadence)
            if m and scene % int(m.group(1)) == 0: due.append((name, advance, "DUE"))
            elif "trigger" in cadence: due.append((name, advance, "check trigger"))
    return due

def main():
    if len(sys.argv) < 3:
        print(__doc__); return
    bdir, scene = sys.argv[1], int(sys.argv[2])
    camp = sys.argv[3] if len(sys.argv) > 3 else "<campaign>"
    subs = os.path.join(bdir, "subsystems.md")
    due = due_subsystems(subs, scene)
    op = operative(subs)

    print(f"🧾 END-OF-SCENE BOOKKEEPING — scene {scene}  (complete EVERY item; do not skip)")
    print("  1. WORLD-TICK:")
    if not due and not os.path.exists(subs):
        print("       (no subsystems.md — advance Mythic's default offscreen clocks)")
    elif not due:
        print("       (nothing scheduled this scene — still advance offscreen clocks)")
    for name, advance, status in due:
        print(f"       • [{status}] {name} → {advance}")
    for ln in op:                                   # companion bookkeeping (Glory, trait-debt, …)
        print(f"       » {ln}")
    print(f"  2. CHAOS FACTOR: judge honestly (unsure → +1):  state.py chaos <+1|-1> <CF>")
    print(f"  3. LISTS: update then regenerate the snapshot:")
    print(f"       state.py thread|char add|weight|remove {camp} \"<name>\"   then   state.py render {camp}")
    print(f"  4. SEEDS: refresh the deck to 30–40 (canon + live world + generator rolls).")
    print(f"  5. RESOLVE-DEBT: did any PC task / trait / passion get a Fate Question instead of the")
    print(f"       RPG's own check this scene? If so, that was rung-1 leakage — correct it next scene.")

if __name__ == "__main__":
    main()
