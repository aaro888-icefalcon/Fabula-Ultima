#!/usr/bin/env python3
"""
dice.py — the honest RNG core for Mythic-GM. Every random resolution goes
through here; results are printed transparently (roll shown) and cite the table.

Commands:
  fate <odds> <cf> [--mode rule]      Fate Question on the Fate Chart (1d100)
  check <odds> <cf>                   Fate Check alternative (2d10 + modifiers)
  scene <cf> [--mode pure|crafter|prepared]   Test the Expected Scene (1d10)
  thread-discovery <points>           Thread Discovery Check (1d10 + Progress Points)
  keyed <expr> [target]               Roll a Keyed-Scene trigger, e.g. 'keyed 1d10 3' (fires on <=3)
  roll <NdM[+/-K]> [adv|dis]          Generic dice (system resolution); adv/dis rolls twice
Odds: Certain, "Nearly Certain", "Very Likely", Likely, 50/50, Unlikely,
      "Very Unlikely", "Nearly Impossible", Impossible
"""
import json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
def load(name): return json.load(open(os.path.join(DATA, name), encoding="utf-8"))
def d(n): return random.randint(1, n)

def _resolve_overridden(bridge_dir):
    """True if this campaign's bridge overrides the resolve hook (the RPG owns task resolution)."""
    try:
        import bridge as bridgemod
        man = bridgemod._manifest_safe(bridge_dir)
        return "resolve" in man.get("overrides", [])
    except Exception:
        return False

ODDS_ALIASES = {"certain":"Certain","nearly certain":"Nearly Certain","very likely":"Very Likely",
    "likely":"Likely","50/50":"50/50","5050":"50/50","fifty":"50/50","unlikely":"Unlikely",
    "very unlikely":"Very Unlikely","nearly impossible":"Nearly Impossible","impossible":"Impossible"}

def norm_odds(s):
    k = s.strip().lower()
    if k not in ODDS_ALIASES: sys.exit(f"Unknown odds '{s}'. See --help for the 9 odds.")
    return ODDS_ALIASES[k]

def event_check(roll, cf):
    """Random Event triggers on a doubles d100 whose digit <= CF (00/100 -> 10)."""
    tens, ones = roll // 10, roll % 10
    if roll == 100: return False, 10
    is_double = (tens == ones)
    digit = ones if ones != 0 else 10
    return (is_double and digit <= cf), digit

def cmd_fate(odds, cf, mode=None, threads=0, characters=0, campaign=None, bridge_dir=None):
    rule = (mode == "rule")
    chart = load("mythic/fate_chart.json")
    eff_cf = 5 if rule else cf
    odds = norm_odds(odds)
    cell = chart["grid"][odds][eff_cf - 1]
    r = d(100)
    if r <= cell["exc_yes_max"]: ans = "Exceptional Yes"
    elif r <= cell["yes_max"]: ans = "Yes"
    elif r >= cell["exc_no_min"]: ans = "Exceptional No"
    else: ans = "No"
    if rule and ans.startswith("Exceptional"): ans = ans.split()[-1]  # collapse
    ev, digit = event_check(r, eff_cf)
    if rule: ev = False
    print(f"🎲 FATE QUESTION  [{odds} @ Chaos {eff_cf}{' · rule-mode' if rule else ''}]")
    print(f"   1d100 = {r}   (Yes if ≤{cell['yes_max']}; ExcYes ≤{cell['exc_yes_max']}; ExcNo ≥{cell['exc_no_min']})")
    print(f"   ANSWER: {ans}")
    print(f"   [src mythic.fate_chart]")
    if not rule:                              # forcing function (fix C): stop rung-1 leakage
        guard = ("   GUARD — a Fate Question answers WORLD/NPC uncertainty the rules don't cover. "
                 "If this was a PC's own skill / trait / passion / attack / save, the RPG resolves "
                 "it (resolve hook), NOT this roll.")
        if bridge_dir and _resolve_overridden(bridge_dir):
            guard += "  [this campaign has an RPG resolve override — see `bridge.py brief`.]"
        print(guard)
    if ev:
        print(f"   ⚡ RANDOM EVENT (doubles, digit {digit} ≤ CF {eff_cf}) — the answer above still stands:")
        # hard-coded chain: run the full Random Event right here
        import importlib.util
        spec = importlib.util.spec_from_file_location("oracle", os.path.join(os.path.dirname(__file__), "oracle.py"))
        oracle = importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)
        oracle.cmd_event(threads, characters, campaign=campaign, bridge_dir=bridge_dir)

def cmd_check(odds, cf):
    fc = load("mythic/fate_check.json"); odds = norm_odds(odds)
    a, b = d(10), d(10); om = fc["odds_mod"][odds]; cm = fc["cf_mod"][str(cf)]
    total = a + b + om + cm
    if total >= 18: ans = "Exceptional Yes"
    elif total >= 11: ans = "Yes"
    elif total >= 5: ans = "No"
    else: ans = "Exceptional No"
    digit = a if a == b else None
    ev = (a == b and a <= cf)
    print(f"🎲 FATE CHECK  [{odds} @ Chaos {cf}]")
    print(f"   2d10 = {a}+{b}  modifiers: odds {om:+d}, chaos {cm:+d}  → total {total}")
    print(f"   ANSWER: {ans}  (≥18 ExcYes · ≥11 Yes · 5-10 No · 2-4 ExcNo)")
    if ev: print(f"   ⚡ RANDOM EVENT (doubles {a}, ≤ CF {cf})")
    print("   [src mythic.fate_check]")

def cmd_scene(cf):
    """Adventure Crafter is always on: both Altered and Interrupt generate a full Turning Point."""
    r = d(10)
    if r > cf:
        out = "EXPECTED SCENE (runs as framed)"; tp = False
    elif r % 2 == 1:  # odd
        out = "ALTERED SCENE → Turning Point (use the Expected Scene as its basis)"; tp = True
    else:             # even
        out = "INTERRUPT SCENE → Turning Point (an entirely new, unexpected scene)"; tp = True
    print(f"🎬 SCENE TEST  [Chaos {cf}]")
    print(f"   1d10 = {r}   ({'over CF' if r>cf else 'within CF, '+('odd' if r%2 else 'even')})")
    print(f"   RESULT: {out}")
    if tp:
        print("   → python3 scripts/adventure_crafter.py turning-point --campaign <dir> [--existing]")
    print("   [src mythic.scene_test]")

def cmd_thread_discovery(points):
    r = d(10); total = r + points
    print(f"🧵 THREAD DISCOVERY CHECK\n   1d10 = {r} + {points} Progress Points = {total}")
    print(f"   → consult Thread Discovery Check Table at {total} (Progress/Flashpoint band); then roll a Meaning Table.")

def cmd_keyed(expr, target=None):
    m = re.match(r"(\d*)d(\d+)", expr);
    if not m: sys.exit("keyed expects NdM, e.g. 1d10")
    n = int(m.group(1) or 1); sides = int(m.group(2))
    rolls = [d(sides) for _ in range(n)]; tot = sum(rolls)
    fired = (target is not None and tot <= int(target))
    print(f"🔑 KEYED-SCENE TRIGGER  {expr} = {rolls} (sum {tot})" +
          (f"  vs ≤{target} → {'FIRES — Event opens next Scene' if fired else 'no trigger'}" if target else ""))

def cmd_table(name):
    """Roll any built list table by name/slug: e.g. scene_adjustment, random_themes,
    plot_point_theme, or an elements slug. Picks 1d10 / 1d100 from the table type."""
    if os.path.isfile(name):                       # absolute/relative path → a companion bridge table
        t = json.load(open(name, encoding="utf-8"))
    else:
        cands = [f"mythic/{name}.json", f"adventure_crafter/{name}.json", f"mythic/elements/{name}.json"]
        path = next((c for c in cands if os.path.exists(os.path.join(DATA, c))), None)
        if not path: sys.exit(f"No table '{name}'. Try a slug (scene_adjustment, plot_points_action…) or a path to a .json.")
        t = load(path)
    sides = 100 if t.get("type") == "list_d100" else 10
    r = d(sides); val = None
    for e in t.get("entries", []):
        if e["min"] <= r <= e["max"]: val = e["value"]; break
    print(f"🎲 {t.get('title', name)}: 1d{sides}={r} → {val}   [src {t.get('id', name)}]")

def cmd_roll(expr, mod=None):
    m = re.match(r"(\d*)d(\d+)([+-]\d+)?$", expr.replace(" ", ""))
    if not m: sys.exit("roll expects NdM[+/-K], e.g. 2d6+3")
    n = int(m.group(1) or 1); sides = int(m.group(2)); k = int(m.group(3) or 0)
    def once(): return [d(sides) for _ in range(n)]
    if mod in ("adv", "dis"):
        r1, r2 = once(), once(); s1, s2 = sum(r1)+k, sum(r2)+k
        pick = max(s1, s2) if mod == "adv" else min(s1, s2)
        print(f"🎲 {expr} {mod}: {r1}={s1} / {r2}={s2} → {pick}")
    else:
        r = once(); print(f"🎲 {expr} = {r}{('%+d' % k) if k else ''} → {sum(r)+k}")

def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h","--help"): print(__doc__); return
    cmd = a[0]
    def opt(flag):
        return a[a.index(flag)+1] if flag in a else None
    mode = opt("--mode")
    th = int(opt("--threads") or 0); ch = int(opt("--characters") or 0)
    camp = opt("--campaign"); brg = opt("--bridge")
    pos = [x for i,x in enumerate(a[1:],1) if not (x.startswith("--") or (a[i-1].startswith("--")))]
    try:
        if cmd == "fate": cmd_fate(pos[0], int(pos[1]), mode, th, ch, camp, brg)
        elif cmd == "check": cmd_check(pos[0], int(pos[1]))
        elif cmd == "scene": cmd_scene(int(pos[0]))
        elif cmd == "table": cmd_table(pos[0])
        elif cmd == "thread-discovery": cmd_thread_discovery(int(pos[0]))
        elif cmd == "keyed": cmd_keyed(pos[0], pos[1] if len(pos)>1 else None)
        elif cmd == "roll": cmd_roll(pos[0], pos[1] if len(pos)>1 else None)
        else: sys.exit(f"Unknown command '{cmd}'. See --help.")
    except (IndexError, ValueError) as e:
        sys.exit(f"Bad arguments for '{cmd}': {e}\n{__doc__}")

if __name__ == "__main__":
    main()
