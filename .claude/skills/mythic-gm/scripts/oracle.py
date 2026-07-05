#!/usr/bin/env python3
"""
oracle.py — Mythic event/meaning oracle. ALL rolls honest, shown, and cited.
The full Random Event chain (Focus → List invoke → Meaning) is hard-coded here.

Commands:
  event [--threads N] [--characters M] [--crafter]
        FULL Random Event: roll Event Focus → (auto-roll the right List if the focus
        invokes one) → roll a Meaning pair → print the assembled prompt to interpret.
        --crafter routes an Interrupt to an Adventure Crafter Turning Point instead.
  event-focus                 Just the Event Focus roll (1d100)
  meaning <table>             One Meaning Table (1d100): actions_1|actions_2|descriptors_1|descriptors_2
  pair actions|descriptors    Both columns → a word pair (the usual oracle)
  elements "<Table Name>"     Honest 1d100 for an Elements table; reads the row from JSON if
                              hard-coded, else from bundled canon (one indexed lookup)
  list <filled> [--new]       Weighted List invoke (legacy count-based 1d25 over the 25-line List).
  thread-list --campaign DIR  Two-stage Thread invoke on threads.json (NEW / PRE-EXISTING / CHOOSE),
  character-list --campaign DIR  …and the same for characters.json (a NEW result auto-generates the
                              Character). Covers the FULL list, any length.
  character [--campaign DIR] [--bridge DIR]   Generate a NEW Character. Default = AC Character Crafter;
                              a companion bridge's generate:character override (replace/conjunction +
                              a generator table and/or lore note) is used when present.
  answer <table> <yes|no|exc_yes|exc_no|random_event>
  (Most commands accept --campaign DIR to roll the JSON Lists, and --bridge DIR for companion overrides.)
"""
import glob, json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lists, bridge as bridgemod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
def load(name): return json.load(open(os.path.join(DATA, name), encoding="utf-8"))
def has(name): return os.path.exists(os.path.join(DATA, name))
def d(n): return random.randint(1, n)
def lookup(entries, r):
    for e in entries:
        if e["min"] <= r <= e["max"]: return e["value"]

# ---- Event Focus → how to resolve (the combined-use routing, hard-coded) ----
# list: 'characters' | 'threads' | None ; new: generate a new Character ; note: extra step
FOCUS_ROUTING = {
    "Remote Event":        {"list": None,         "note": "an event elsewhere; PC not directly involved yet"},
    "Ambiguous Event":     {"list": None,         "note": "neither clearly good nor bad — an opening to explore"},
    "New NPC":             {"list": None, "new": True, "note": "introduce/generate a new Character (Character Crafter)"},
    "NPC Action":          {"list": "characters", "note": "the invoked Character takes an action"},
    "NPC Negative":        {"list": "characters", "note": "something negative happens to/around the invoked Character"},
    "NPC Positive":        {"list": "characters", "note": "something positive happens to/around the invoked Character"},
    "Move Toward A Thread":{"list": "threads",    "note": "progress toward the invoked Thread"},
    "Move Away From A Thread":{"list": "threads", "note": "a setback on the invoked Thread"},
    "Close A Thread":      {"list": "threads",    "note": "the invoked Thread concludes (Thread Conclusion)"},
    "PC Negative":         {"list": None,         "note": "something negative happens to the PC"},
    "PC Positive":         {"list": None,         "note": "something positive happens to the PC"},
    "Current Context":     {"list": None,         "note": "about the current situation"},
}

CHAR_NEW_LINES = {1,2,3,5,6,7,9,10,11,13,17,21,25}   # Characters List lines whose printed default is "New Character"
def roll_list(filled, allow_new=False, mode="mythic"):
    """Invoke on the 25-line List. Weighted naturally (repeats occupy more slots).
    mode 'mythic' (Random Events): die scales to fullness → fewer blanks.
    mode 'crafter' (AC Plot-Point invoke): roll 1d100 on the 25-line list, line=ceil(roll/4);
      a blank line gives its printed default (New Character / Choose Most Logical Character).
    Returns (text, is_blank)."""
    filled = int(filled)
    if filled <= 0:
        return ("List empty → use Current Context (no roll)", True)
    if mode == "crafter":
        r = d(100); line = (r - 1)//4 + 1
        if line <= filled:
            return (f"1d100={r} → line {line} → INVOKE the Character on line {line} (re-add it, max 3×)", False)
        default = "NEW CHARACTER" if line in CHAR_NEW_LINES else "CHOOSE MOST LOGICAL CHARACTER"
        return (f"1d100={r} → line {line} (blank) → {default}", True)
    sides = 10 if filled <= 10 else 20 if filled <= 20 else 25      # Mythic Random Event invoke
    r = d(sides)
    if r <= filled:
        return (f"slot {r} (1d{sides}={r}) → read that entry off the List", False)
    opt = "Choose Most Logical, or Add a New element" if allow_new else "Choose Most Logical, or roll again"
    return (f"BLANK line (1d{sides}={r} > {filled} filled) → {opt}", True)

def invoke_two_stage(kind, campaign, bridge_dir=None, auto_generate=True, _print=True):
    """Campaign-aware List invoke: two-stage roll over the full JSON List (any length).
    A NEW CHARACTER result auto-invokes the character generator (AC Crafter by default,
    or the companion's generate:character override from the bridge)."""
    if not campaign: sys.exit("This command needs --campaign DIR (the campaign folder with the JSON Lists).")
    obj = lists.load_list(campaign, kind)
    res = lists.two_stage(obj["entries"], kind)
    text = lists.describe(res, kind)
    if _print: print(f"📃 {kind.capitalize()} List invoke → {text}")
    if auto_generate and kind == "character" and res["category"] == "NEW":
        print("   ↳ NEW CHARACTER — generating:")
        cmd_character(campaign=campaign, bridge_dir=bridge_dir, indent="   ")
    return res, text

def cmd_event_focus(_print=True):
    t = load("mythic/event_focus.json"); r = d(100); v = lookup(t["entries"], r)
    if _print: print(f"🎯 EVENT FOCUS  1d100={r} → {v}   [src mythic.event_focus]")
    return v, r

def cmd_pair(which, _print=True):
    cols = {"actions": ("actions_1","actions_2"), "descriptors": ("descriptors_1","descriptors_2")}[which]
    out = []
    for c in cols:
        t = load(f"mythic/meaning_{c}.json"); r = d(100); out.append((lookup(t["entries"], r), r))
    if _print:
        print(f"📖 MEANING PAIR ({which}): " + "  ·  ".join(f"{w} (d100={r})" for w, r in out))
    return out

def cmd_event(threads=0, characters=0, crafter=False, campaign=None, bridge_dir=None):
    print("⚡ RANDOM EVENT")
    focus, fr = cmd_event_focus()
    route = FOCUS_ROUTING.get(focus, {"list": None, "note": ""})
    print(f"   Focus: {focus} — {route['note']}")
    if crafter:
        print("   (Crafter mode: an Interrupt is built as a Turning Point — run "
              "adventure_crafter.py turning-point instead of a plain event.)")
    if route.get("new"):                      # Event Focus = New NPC → generate one now
        cmd_character(campaign=campaign, bridge_dir=bridge_dir, indent="   ")
    elif route["list"] in ("characters", "threads"):
        kind = "character" if route["list"] == "characters" else "thread"
        if campaign:
            invoke_two_stage(kind, campaign, bridge_dir=bridge_dir)  # NEW char auto-generates
        else:
            text, blank = roll_list(characters if kind == "character" else threads, allow_new=True)
            print(f"   {kind.capitalize()}s List invoke → {text}")
    pair = cmd_pair("actions")
    print(f"   Meaning (actions): {pair[0][0]}  ·  {pair[1][0]}")
    print("   → interpret Focus + invoked element + word pair into the Event. "
          "Add any new Thread/Character to the Lists (weight ≤3).")

def cmd_meaning(table):
    t = load(f"mythic/meaning_{table}.json"); r = d(100)
    print(f"📖 {t['title']}  1d100={r} → {lookup(t['entries'], r)}   [src {t['id']}]")

def cmd_elements(name):
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    p = f"mythic/elements/{slug}.json"
    if not has(p):
        avail = sorted(os.path.basename(x)[:-5] for x in glob.glob(os.path.join(DATA, "mythic/elements/*.json"))
                       if not x.endswith("_index.json"))
        sys.exit(f"No Elements table '{name}'. Available: {', '.join(avail)}")
    t = load(p); r = d(100)
    print(f"📖 Elements — {name}: 1d100={r} → {lookup(t['entries'], r)}   [src {t['id']}]")

def cmd_list(filled, allow_new=False, mode="mythic"):
    text, _ = roll_list(filled, allow_new, mode)
    print(f"📃 LIST invoke ({mode}) → {text}")

def roll_table_file(path):
    t = json.load(open(path, encoding="utf-8"))
    sides = 100 if t.get("type") == "list_d100" else 10
    r = d(sides); return t, r, sides, lookup(t.get("entries", []), r)

def _ac_crafter(indent=""):
    """The Adventure Crafter Character Crafter: Special Trait + Identity + Descriptors."""
    st = load("adventure_crafter/character_special_trait.json"); r = d(100)
    print(f"{indent}   Special Trait: 1d100={r} → {lookup(st['entries'], r)}   [src ac.character_special_trait]")
    for label, slug in [("Identity","character_identity"),("Descriptors","character_descriptors")]:
        t = load(f"mythic/elements/{slug}.json"); rr = d(100)
        print(f"{indent}   {label}: 1d100={rr} → {lookup(t['entries'], rr)}   [src {t['id']}]")

def cmd_character(threads=0, characters=0, campaign=None, bridge_dir=None, indent=""):
    """Generate a NEW Character. Default = AC Character Crafter. A companion bridge can
    override via generate:character (mode replace = companion only; conjunction = both)."""
    cfg = bridgemod.char_gen(bridge_dir)
    mode = (cfg or {}).get("mode", "default")
    print(f"{indent}🧬 NEW CHARACTER" + (f"  [bridge generate:character · {mode}]" if cfg else "  [AC Character Crafter]"))
    used_companion = False
    if cfg and mode in ("replace", "conjunction"):
        if cfg.get("table") and os.path.exists(cfg["table"]):
            t, r, sides, val = roll_table_file(cfg["table"])
            print(f"{indent}   {t.get('title', os.path.basename(cfg['table']))}: 1d{sides}={r} → {val}   [bridge {os.path.basename(cfg['table'])}]")
            used_companion = True
        if cfg.get("note"):
            print(f"{indent}   Lore: {cfg['note']}"); used_companion = True
    # AC Crafter runs as the default and in conjunction; skipped only on a working 'replace'
    if not (cfg and mode == "replace" and used_companion):
        _ac_crafter(indent)
    print(f"{indent}   → name the Character, then add it:  state.py char add <campaign> \"<name>\"")

def cmd_answer(table, key):
    t = load(f"mythic/{table}.json"); v = t.get("answers", {}).get(key)
    if v is None: sys.exit(f"No answer '{key}' in {table}: keys {list(t.get('answers',{}))}")
    print(f"📐 {t['title']} [{key}]: {v}   [src {t['id']}]")

def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h","--help"): print(__doc__); return
    def opt(f, dv=0): return int(a[a.index(f)+1]) if f in a else dv
    campaign = (a[a.index("--campaign")+1] if "--campaign" in a else None)
    bridge_dir = (a[a.index("--bridge")+1] if "--bridge" in a else None)
    c = a[0]
    try:
        if c == "event": cmd_event(opt("--threads"), opt("--characters"), "--crafter" in a, campaign, bridge_dir)
        elif c == "event-focus": cmd_event_focus()
        elif c == "meaning": cmd_meaning(a[1])
        elif c == "pair": cmd_pair(a[1])
        elif c == "elements": cmd_elements(a[1])
        elif c == "list": cmd_list(a[1], "--new" in a, "crafter" if "--crafter" in a else "mythic")
        elif c == "thread-list": invoke_two_stage("thread", campaign, bridge_dir=bridge_dir)
        elif c == "character-list": invoke_two_stage("character", campaign, bridge_dir=bridge_dir)
        elif c == "character": cmd_character(campaign=campaign, bridge_dir=bridge_dir)
        elif c == "answer": cmd_answer(a[1], a[2])
        else: sys.exit(f"Unknown command '{c}'. See --help.")
    except IndexError:
        sys.exit("Missing argument. See --help.")

if __name__ == "__main__":
    main()
