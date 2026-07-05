#!/usr/bin/env python3
"""
lookup.py — print ONE ruleset record as a compact card, so the GM never has to load
a whole data file into context.

  lookup.py class darkblade | spell fulgur | skill dodge | heroic "powerful strike"
  lookup.py weapon "steel dagger" | armor brigandine | shield "runic shield"
  lookup.py monster drake | status slow | npc_skill "special attack"

Fuzzy, case-insensitive name/key matching. No randomness.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fudata as F


def _clip(s, n=600):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + "…"


def show_class(q):
    c = F.find("class", q)
    if not c:
        return f"no class '{q}'"
    out = [f"{c['name']}  [class]" + (f"   ALSO: {', '.join(c.get('also',[]))}" if c.get("also") else "")]
    if c.get("flavor"):
        out.append("  " + _clip(c["flavor"], 200))
    if c.get("free_benefits"):
        out.append("  Free benefits: " + "; ".join(c["free_benefits"]))
    if c.get("spellcasting"):
        sc = c["spellcasting"]
        out.append(f"  Spellcasting: {sc.get('discipline','')} · Magic Check {sc.get('magic_check','?')}")
    out.append("  Skills:")
    for sk in c.get("skills", []):
        out.append(f"    • {sk['name']} (SL max {sk['sl_max']}) — {_clip(sk['text'], 180)}")
    return "\n".join(out)


def show_spell(q):
    s = F.find("spell", q)
    if not s:
        return f"no spell '{q}'"
    head = (f"{s['name']}  [{s['class']} spell]  MP {s['mp_cost']} · target: {s['target']} "
            f"· {s['duration']}" + ("  · OFFENSIVE" if s.get("offensive") else ""))
    if s.get("damage_type"):
        head += f"  · {s['damage_type']}"
    lines = [head, "  " + _clip(s["text"])]
    if s.get("opportunity"):
        lines.append("  Opportunity: " + _clip(s["opportunity"], 200))
    return "\n".join(lines)


def show_skill(q):
    for c in F.load("classes")["entries"]:
        for sk in c.get("skills", []):
            if sk["key"] == q.lower() or sk["name"].lower() == q.lower():
                return f"{sk['name']}  [{c['name']} skill · SL max {sk['sl_max']}]\n  {_clip(sk['text'])}"
    # fuzzy fallback
    allsk = [(c["name"], sk) for c in F.load("classes")["entries"] for sk in c.get("skills", [])]
    m = F._fuzzy(q, [sk["name"] for _, sk in allsk])
    for cn, sk in allsk:
        if sk["name"] == m:
            return f"{sk['name']}  [{cn} skill · SL max {sk['sl_max']}]\n  {_clip(sk['text'])}"
    return f"no skill '{q}'"


def show_heroic(q):
    entries = F.load("heroic_skills")["entries"]
    m = F._fuzzy(q, [h["key"] for h in entries] + [h["name"] for h in entries])
    for h in entries:
        if h["key"] == m or h["name"] == m:
            return (f"{h['name']}  [heroic skill · {h.get('class','general')}]\n"
                    f"  Requires: {h.get('requirements','—')}\n  {_clip(h['text'])}")
    return f"no heroic skill '{q}'"


def show_equipment(kind, q):
    e = F.find(kind, q)
    if not e:
        return f"no {kind} '{q}'"
    if kind == "weapon":
        acc = e["accuracy"]
        return (f"{e['name']}  [{e.get('category','')} weapon · {'martial' if e['martial'] else 'basic'} · "
                f"{e['hands']}h · {e['range']}]  cost {e['cost']}z\n"
                f"  Accuracy 【{'+'.join(acc['attributes'])}】{acc['bonus']:+d} · "
                f"Damage 【HR+{e['damage']['bonus']}】 {e['damage']['type']}"
                + (f"\n  {_clip(e.get('qualities') or e.get('text',''))}" if (e.get('qualities') or e.get('text')) else ""))
    return (f"{e['name']}  [{kind} · {'martial' if e.get('martial') else 'basic'}]  cost {e.get('cost')}z\n"
            f"  DEF {e.get('defense')} · M.DEF {e.get('magic_defense')} · Init {e.get('initiative',0)}"
            + (f"\n  {_clip(e.get('qualities') or e.get('text',''))}" if (e.get('qualities') or e.get('text')) else ""))


def show_monster(q):
    c = F.find("creature", q)
    if not c:
        return f"no creature '{q}'"
    a = c["attributes"]
    lines = [f"{c['name']}  L{c['level']} · {c['species']}"
             + (f" · {c['rank']}" if c.get("rank") else ""),
             f"  DEX d{a['DEX']} INS d{a['INS']} MIG d{a['MIG']} WLP d{a['WLP']}",
             f"  HP {c['hp']} (Crisis {c.get('crisis','?')}) · MP {c['mp']} · Init {c['initiative']} "
             f"· DEF {c['defense']} · M.DEF {c['magic_defense']}"]
    if c.get("affinities"):
        lines.append("  Affinities: " + ", ".join(f"{k}:{v}" for k, v in c["affinities"].items()))
    for atk in c.get("attacks", []):
        lines.append(f"  • {atk['name']}: {atk.get('accuracy','')} · {atk.get('damage','')}")
    for sk in c.get("skills", []):
        lines.append(f"  ◦ {sk['name']}: {_clip(sk.get('text',''), 140)}")
    return "\n".join(lines)


def show_status(q):
    s = F.find("status", q)
    if not s:
        return f"no status '{q}'"
    return f"{s['name']}  [status]  downgrades: {', '.join(s['downgrades'])}\n  {_clip(s['text'])}"


def show_npc_skill(q):
    s = F.find("npc_skill", q)
    if not s:
        return f"no NPC skill '{q}'"
    return f"{s['name']}  [NPC skill{' · limited' if s.get('limited') else ''}]\n  {_clip(s['text'])}"


KINDS = {
    "class": show_class, "spell": show_spell, "skill": show_skill, "heroic": show_heroic,
    "weapon": lambda q: show_equipment("weapon", q),
    "armor": lambda q: show_equipment("armor", q),
    "shield": lambda q: show_equipment("shield", q),
    "monster": show_monster, "creature": show_monster,
    "status": show_status, "npc_skill": show_npc_skill,
}


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    kind = argv[0].lower()
    if kind not in KINDS:
        sys.exit(f"unknown kind '{kind}'. known: {', '.join(sorted(KINDS))}")
    if len(argv) < 2:
        sys.exit(f"usage: lookup.py {kind} <name>")
    print(KINDS[kind](" ".join(argv[1:])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
