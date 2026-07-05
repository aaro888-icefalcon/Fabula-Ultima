#!/usr/bin/env python3
"""
sheet.py — Fabula Ultima character sheets (PC / companion) as YAML under campaign/sheets/.

  sheet.py new <name> --level 5 --class rogue:3 --class elementalist:2 \
                 --dex 10 --ins 8 --mig 6 --wlp 8 [--identity ".." --theme ".." --origin ".."]
  sheet.py validate <name>          # class/level/skill legality (FU multiclass rules)
  sheet.py render <name>            # pretty-print
  sheet.py levelup <name> --class rogue [--skill dodge]   # invest one level + a skill

PC secondary scores (Core p.~40):
  Max HP = level + 5×base MIG die (+ class free-benefit HP)   Crisis = ⌊HP/2⌋
  Max MP = level + 5×base WLP die (+ class free-benefit MP)
  DEF = DEX die   M.DEF = INS die   Initiative = 0   Inventory Points = 6
No randomness here.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fudata as F

ATTRS = ["DEX", "INS", "MIG", "WLP"]
MAX_CLASS_LEVEL = 10
CHAR_MIN, CHAR_MAX = 5, 50


# ---------------------------------------------------------------- pure logic
def class_index():
    return {c["key"]: c for c in F.load("classes")["entries"]}


def class_free_bonuses(class_keys):
    """Flat HP/MP granted by a class's FREE BENEFITS (gained once per class)."""
    idx = class_index()
    hp = mp = 0
    for ck in class_keys:
        c = idx.get(ck)
        if not c:
            continue
        for fb in c.get("free_benefits", []):
            m = re.search(r"maximum Hit Points by (\d+)", fb)
            if m:
                hp += int(m.group(1))
            m = re.search(r"maximum Mind Points by (\d+)", fb)
            if m:
                mp += int(m.group(1))
    return hp, mp


def pc_scores(level, attrs, class_keys):
    hp_b, mp_b = class_free_bonuses(class_keys)
    max_hp = level + 5 * attrs["MIG"] + hp_b
    max_mp = level + 5 * attrs["WLP"] + mp_b
    return {
        "max_hp": max_hp, "crisis": max_hp // 2, "max_mp": max_mp,
        "defense": attrs["DEX"], "magic_defense": attrs["INS"],
        "initiative": 0, "inventory_points": 6,
        "class_hp_bonus": hp_b, "class_mp_bonus": mp_b,
    }


def legality(sheet):
    """Return (errors, warnings) for FU multiclass/skill rules."""
    errs, warns = [], []
    idx = class_index()
    classes = sheet.get("classes", []) or []
    skills = sheet.get("skills", []) or []
    level = sheet.get("level")

    if not (CHAR_MIN <= (level or 0) <= CHAR_MAX):
        warns.append(f"character level {level} outside typical {CHAR_MIN}-{CHAR_MAX}")

    class_levels = {}
    for c in classes:
        ck, cl = c.get("name"), c.get("level", 0)
        if ck not in idx:
            errs.append(f"unknown class '{ck}'")
        if not (1 <= cl <= MAX_CLASS_LEVEL):
            errs.append(f"class '{ck}' level {cl} out of 1..{MAX_CLASS_LEVEL}")
        class_levels[ck] = cl

    if level is not None and sum(class_levels.values()) != level:
        errs.append(f"class levels sum to {sum(class_levels.values())} ≠ character level {level}")

    # skills: SL caps + acquisitions-per-class == class level
    per_class_sl = {ck: 0 for ck in class_levels}
    for sk in skills:
        ck, name, sl = sk.get("class"), sk.get("name"), sk.get("sl", 0)
        if ck not in class_levels:
            errs.append(f"skill '{name}' belongs to class '{ck}' the character doesn't have")
            continue
        cdef = idx.get(ck, {})
        sdef = next((x for x in cdef.get("skills", [])
                     if x["key"] == sk.get("key") or x["name"].lower() == (name or "").lower()), None)
        if not sdef:
            warns.append(f"skill '{name}' not found in class '{ck}' (custom?)")
        elif sl > sdef["sl_max"]:
            errs.append(f"skill '{name}' SL {sl} exceeds cap SL {sdef['sl_max']}")
        per_class_sl[ck] = per_class_sl.get(ck, 0) + sl

    for ck, cl in class_levels.items():
        got = per_class_sl.get(ck, 0)
        if got > cl:
            errs.append(f"class '{ck}': skill SLs sum to {got} but class level is only {cl} "
                        f"(each level = one Skill acquisition)")
        elif got < cl:
            warns.append(f"class '{ck}': {cl - got} Skill acquisition(s) not yet assigned "
                         f"({got}/{cl})")
    return errs, warns


# ---------------------------------------------------------------- commands
def _parse_classes(specs):
    out = []
    for s in specs or []:
        name, _, lvl = s.partition(":")
        out.append({"name": name.strip(), "level": int(lvl) if lvl else 1})
    return out


def cmd_new(a):
    attrs = {}
    if a.dex or a.ins or a.mig or a.wlp:
        attrs = {"DEX": a.dex or 8, "INS": a.ins or 8, "MIG": a.mig or 8, "WLP": a.wlp or 8}
    else:
        attrs = {"DEX": 8, "INS": 8, "MIG": 8, "WLP": 8}
    classes = _parse_classes(a.cls)
    sc = pc_scores(a.level, attrs, [c["name"] for c in classes])
    sheet = {
        "name": a.name, "kind": a.kind, "level": a.level,
        "identity": a.identity or "", "theme": a.theme or "", "origin": a.origin or "",
        "attributes": attrs,
        "max_hp": sc["max_hp"], "hp": sc["max_hp"], "crisis": sc["crisis"],
        "max_mp": sc["max_mp"], "mp": sc["max_mp"],
        "defense": sc["defense"], "magic_defense": sc["magic_defense"],
        "initiative": sc["initiative"], "inventory_points": sc["inventory_points"],
        "fabula_points": 3, "zenit": 500,
        "classes": classes, "skills": [], "bonds": [], "statuses": [],
        "equipment": [], "notes": "",
    }
    p = F.save_sheet(sheet)
    print(f"📝 created {a.name} → {p}")
    print(f"   HP {sc['max_hp']} (Crisis {sc['crisis']}) · MP {sc['max_mp']} "
          f"· DEF {sc['defense']} · M.DEF {sc['magic_defense']} "
          f"· class bonuses +{sc['class_hp_bonus']}HP/+{sc['class_mp_bonus']}MP")
    if not sheet["skills"]:
        print("   note: pick Skills with `sheet.py levelup` (one per character level).")
    return 0


def cmd_validate(a):
    sh = F.load_sheet(a.name)
    if not sh:
        sys.exit(f"no sheet '{a.name}'")
    errs, warns = legality(sh)
    print(f"🔎 {sh['name']} — legality")
    for w in warns:
        print("   ! ", w)
    if errs:
        print("   INVALID:")
        for e in errs:
            print("     ✗", e)
        return 1
    print("   LEGAL ✓")
    return 0


def cmd_render(a):
    sh = F.load_sheet(a.name)
    if not sh:
        sys.exit(f"no sheet '{a.name}'")
    a_ = sh["attributes"]
    print(f"╔ {sh['name']}  (L{sh.get('level')} {sh.get('kind','pc')})")
    if sh.get("identity"):
        print(f"║ {sh.get('identity')} · {sh.get('theme','')} · {sh.get('origin','')}")
    print(f"║ DEX d{a_['DEX']}  INS d{a_['INS']}  MIG d{a_['MIG']}  WLP d{a_['WLP']}")
    print(f"║ HP {sh.get('hp')}/{sh.get('max_hp')} (Crisis {sh.get('crisis')})  "
          f"MP {sh.get('mp')}/{sh.get('max_mp')}  IP {sh.get('inventory_points','-')}")
    print(f"║ DEF {sh.get('defense')}  M.DEF {sh.get('magic_defense')}  "
          f"Init {sh.get('initiative')}  FP {sh.get('fabula_points','-')}")
    if sh.get("classes"):
        print("║ Classes: " + ", ".join(f"{c['name']} {c['level']}" for c in sh["classes"]))
    for sk in sh.get("skills", []):
        print(f"║   • {sk.get('name')} (SL {sk.get('sl')}) [{sk.get('class')}]")
    for b in sh.get("bonds", []):
        print(f"║ Bond → {b.get('toward')} (str {b.get('strength')}): {', '.join(b.get('emotions',[]))}")
    if sh.get("statuses"):
        print("║ Statuses: " + ", ".join(sh["statuses"]))
    print("╚" + "═" * 40)
    return 0


def cmd_levelup(a):
    sh = F.load_sheet(a.name)
    if not sh:
        sys.exit(f"no sheet '{a.name}'")
    idx = class_index()
    if a.cls not in idx:
        sys.exit(f"unknown class '{a.cls}'")
    classes = sh.setdefault("classes", [])
    row = next((c for c in classes if c["name"] == a.cls), None)
    if row:
        if row["level"] >= MAX_CLASS_LEVEL:
            sys.exit(f"'{a.cls}' already at max class level {MAX_CLASS_LEVEL}")
        row["level"] += 1
    else:
        classes.append({"name": a.cls, "level": 1})
    sh["level"] = sum(c["level"] for c in classes)
    if a.skill:
        cdef = idx[a.cls]
        sdef = next((x for x in cdef["skills"]
                     if x["key"] == a.skill or x["name"].lower() == a.skill.lower()), None)
        if not sdef:
            sys.exit(f"class '{a.cls}' has no skill '{a.skill}'. "
                     f"options: {', '.join(x['key'] for x in cdef['skills'])}")
        skills = sh.setdefault("skills", [])
        srow = next((s for s in skills if s.get("key") == sdef["key"]), None)
        if srow:
            if srow["sl"] >= sdef["sl_max"]:
                sys.exit(f"skill '{sdef['name']}' already at cap SL {sdef['sl_max']}")
            srow["sl"] += 1
        else:
            skills.append({"class": a.cls, "key": sdef["key"], "name": sdef["name"], "sl": 1})
    # recompute HP/MP from new level
    sc = pc_scores(sh["level"], sh["attributes"], [c["name"] for c in classes])
    for k in ("max_hp", "crisis", "max_mp", "defense", "magic_defense"):
        sh[k] = sc[k]
    F.save_sheet(sh)
    print(f"⬆️  {sh['name']} → L{sh['level']}  ({a.cls} "
          f"{next(c['level'] for c in classes if c['name']==a.cls)})")
    errs, warns = legality(sh)
    print("   legality:", "LEGAL ✓" if not errs else "ISSUES: " + "; ".join(errs))
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="sheet.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new")
    s.add_argument("name"); s.add_argument("--kind", default="pc")
    s.add_argument("--level", type=int, default=5)
    s.add_argument("--class", dest="cls", action="append")
    for at in ("dex", "ins", "mig", "wlp"):
        s.add_argument(f"--{at}", type=int)
    s.add_argument("--identity"); s.add_argument("--theme"); s.add_argument("--origin")
    s.set_defaults(fn=cmd_new)
    for name, fn in (("validate", cmd_validate), ("render", cmd_render)):
        s = sub.add_parser(name); s.add_argument("name"); s.set_defaults(fn=fn)
    s = sub.add_parser("levelup"); s.add_argument("name")
    s.add_argument("--class", dest="cls", required=True); s.add_argument("--skill")
    s.set_defaults(fn=cmd_levelup)
    return p


def main(argv):
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
