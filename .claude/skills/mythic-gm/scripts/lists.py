#!/usr/bin/env python3
"""
lists.py — JSON-backed Threads / Characters Lists + the two-stage List roll, shared
by adventure_crafter.py and oracle.py. The JSON files are the machine-rollable source
of truth (campaign-state.md keeps a human-readable snapshot). Nothing here invents
results — callers roll and show the dice.

Files (in the campaign folder):
  threads.json     {"kind":"thread",    "entries":[{"name":..., "weight":1..3}, ...]}
  characters.json  {"kind":"character", "entries":[{"name":..., "weight":1..3}, ...]}
  adventure.json   {"theme_order":[5 themes], "tens":int, "style":str}

THE TWO-STAGE ROLL (replaces the old raw 1d100→line lookup; same distribution when the
list fits in 25, and rolls over the FULL list when it is longer):
  Stage 1 — category: roll 1dL where L = max(25, total weighted slots S).
       r ≤ S            → PRE-EXISTING   (an existing entry is invoked)
       r in S+1..25     → that blank line's printed default: NEW or CHOOSE MOST LOGICAL
       (when S ≥ 25 there are no blanks → always PRE-EXISTING; the full list rolls over)
  Stage 2 — which one: if PRE-EXISTING, roll 1dS weighted by entry weight to pick the entry.
  This reproduces canon exactly for S ≤ 25: P(invoke e) = weight_e/25, and generalises
  past 25 without truncating the list.
"""
import json, os, random

# Printed "New …" default lines on the 25-line Lists (Adventure Crafter, p.101/115).
THREAD_NEW_LINES = {2, 6, 10, 14, 18, 22}
CHAR_NEW_LINES   = {1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 17, 21, 25}
KIND_FILE = {"thread": "threads.json", "character": "characters.json"}
KIND_NEWLINES = {"thread": THREAD_NEW_LINES, "character": CHAR_NEW_LINES}
WEIGHT_CAP = 3
LIST_CAP = 25

def d(n): return random.randint(1, n)

# ----------------------------------------------------------------- JSON load/save
def _path(campaign, fname): return os.path.join(campaign, fname)

def load_list(campaign, kind):
    p = _path(campaign, KIND_FILE[kind])
    if os.path.exists(p):
        obj = json.load(open(p, encoding="utf-8"))
        obj.setdefault("kind", kind); obj.setdefault("entries", [])
        for e in obj["entries"]:
            e.setdefault("weight", 1)
        return obj
    return {"kind": kind, "entries": []}

def save_list(campaign, obj):
    p = _path(campaign, KIND_FILE[obj["kind"]])
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return p

def load_adventure(campaign):
    p = _path(campaign, "adventure.json")
    if os.path.exists(p):
        obj = json.load(open(p, encoding="utf-8"))
    else:
        obj = {}
    obj.setdefault("theme_order", ["Action", "Tension", "Mystery", "Social", "Personal"])
    obj.setdefault("tens", 0)
    obj.setdefault("style", "balanced")
    return obj

def save_adventure(campaign, obj):
    json.dump(obj, open(_path(campaign, "adventure.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

# --------------------------------------------------------------- list mutation
def total_weight(entries): return sum(int(e.get("weight", 1)) for e in entries)

def _find(entries, name):
    key = name.strip().lower()
    for e in entries:
        if e["name"].strip().lower() == key: return e
    return None

def add_entry(obj, name, bump=True):
    """Add a new entry, or +1 its weight (capped). bump=False just ensures it exists."""
    e = _find(obj["entries"], name)
    if e is None:
        if total_weight(obj["entries"]) >= LIST_CAP:
            return "FULL", obj   # canon "The List Is Full" — caller must remove something first
        obj["entries"].append({"name": name.strip(), "weight": 1}); return "added", obj
    if bump and e["weight"] < WEIGHT_CAP:
        if total_weight(obj["entries"]) >= LIST_CAP: return "FULL", obj
        e["weight"] += 1; return "weighted", obj
    return "noop", obj

def remove_entry(obj, name):
    e = _find(obj["entries"], name)
    if e is None: return "missing", obj
    obj["entries"] = [x for x in obj["entries"] if x is not e]
    return "removed", obj

# --------------------------------------------------------------- the two roll stages
def weighted_pick(entries):
    """Stage 2: roll 1dS weighted by weight; return (roll, S, name)."""
    S = total_weight(entries)
    if S <= 0: return None, 0, None
    r = d(S); acc = 0
    for e in entries:
        acc += int(e.get("weight", 1))
        if r <= acc: return r, S, e["name"]
    return r, S, entries[-1]["name"]

def two_stage(entries, kind):
    """Full two-stage roll. Returns a dict with category, pick, and both rolls."""
    new_lines = KIND_NEWLINES[kind]
    S = total_weight(entries)
    if S <= 0:
        return {"category": "NEW", "pick": None, "r1": None, "L": LIST_CAP, "S": 0,
                "r2": None, "S2": 0, "overfull": False}
    L = max(LIST_CAP, S)
    r1 = d(L)
    if r1 <= S:
        cat = "PRE-EXISTING"
    else:                                   # r1 in S+1..25 (only when S<25): a blank line
        cat = "NEW" if r1 in new_lines else "CHOOSE MOST LOGICAL"
    r2 = S2 = pick = None
    if cat == "PRE-EXISTING":
        r2, S2, pick = weighted_pick(entries)
    return {"category": cat, "pick": pick, "r1": r1, "L": L, "S": S,
            "r2": r2, "S2": S2, "overfull": S > LIST_CAP}

def describe(res, kind):
    """One-line human summary of a two_stage result."""
    K = kind.capitalize()
    if res["S"] == 0:
        return f"{K} List empty → automatic NEW {K.upper()}"
    head = f"Stage 1: 1d{res['L']}={res['r1']} (S={res['S']} weighted slot(s)" + \
           (", list OVERFULL — full list rolls over" if res["overfull"] else "") + ")"
    if res["category"] == "PRE-EXISTING":
        return (f"{head} → PRE-EXISTING.  Stage 2: 1d{res['S2']}={res['r2']} (weighted) "
                f"→ invoke **{res['pick']}**")
    return f"{head} → {res['category']} {K.upper()}"
