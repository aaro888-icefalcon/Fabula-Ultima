#!/usr/bin/env python3
"""
statgen.py — build a Fabula Ultima NPC / villain / monster from the design math in
data/npc_design.json (Designing NPCs, Core p.302). The formulas are the same ones
the Bestiary was built with, so a soldier built here reproduces the book's numbers.

  statgen.py npc --level 20 --array specialized --species demon [--order MIG,DEX,INS,WLP]
                 [--rank soldier|elite|champion --n 3]
  statgen.py villain --level 30 --array super --species monster --rank major
                 [--danger champion --n 3]        # villain rank = Ultima Points; danger = turns
  statgen.py monster <bestiary-key> [--rank elite|champion --n N]   # take a book creature up a rank

Pure functions (base_scores / apply_danger) are unit-tested against the book.
No randomness here.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fudata as F

ARRAYS = {
    "jack": [8, 8, 8, 8], "standard": [10, 8, 8, 6],
    "specialized": [10, 10, 6, 6], "super": [12, 8, 6, 6],
}
ATTRS = ["DEX", "INS", "MIG", "WLP"]


def base_scores(level, array_dice, order=None):
    """Soldier-rank secondary scores. `order` maps array positions to attributes
    (default DEX,INS,MIG,WLP). Returns a dict."""
    order = order or ATTRS
    attrs = {order[i]: array_dice[i] for i in range(4)}
    # level-20/40/60 die upgrades are applied by the caller if desired; base here.
    max_hp = 2 * level + 5 * attrs["MIG"]
    max_mp = level + 5 * attrs["WLP"]
    dmg_bonus = 0
    for band in (60, 40, 20):
        if level >= band:
            dmg_bonus = {20: 5, 40: 10, 60: 15}[band]
            break
    return {
        "level": level,
        "attributes": {a: attrs[a] for a in ATTRS},
        "max_hp": max_hp,
        "crisis": max_hp // 2,
        "max_mp": max_mp,
        "initiative": (attrs["DEX"] + attrs["INS"]) // 2,
        "defense": attrs["DEX"],
        "magic_defense": attrs["INS"],
        "check_bonus": max(0, level // 10),
        "damage_bonus": dmg_bonus,
        "turns_per_round": 1,
        "extra_skills": 0,
        "rank": "soldier",
    }


def apply_danger(scores, rank, n=None):
    """Promote a soldier to elite or champion(N). Mutates a copy, returns it."""
    s = dict(scores)
    s["attributes"] = dict(scores["attributes"])
    if rank == "soldier":
        return s
    if rank == "elite":
        s["max_hp"] *= 2
        s["crisis"] = s["max_hp"] // 2
        s["initiative"] += 2
        s["turns_per_round"] = 2
        s["extra_skills"] = 1
        s["rank"] = "elite"
    elif rank == "champion":
        if not n or n < 2:
            raise ValueError("champion needs --n >= 2 (soldiers replaced)")
        s["max_hp"] *= n
        s["crisis"] = s["max_hp"] // 2
        s["max_mp"] *= 2
        s["initiative"] += n
        s["turns_per_round"] = n
        s["extra_skills"] = n
        s["rank"] = f"champion({n})"
    else:
        raise ValueError(f"unknown danger rank {rank!r}")
    return s


def villain_ultima(rank):
    for r in F.load("npc_design").get("villain_ranks", []):
        if r["key"] == rank:
            return r.get("ultima_points")
    return None


def _species_rules(species):
    for sp in F.load("npc_design").get("species", []):
        if sp["key"] == species:
            return sp
    return None


def _print_block(s, species=None, villain_rank=None):
    a = s["attributes"]
    print(f"  Level {s['level']} · {s['rank']}"
          + (f" · {species.upper()}" if species else ""))
    print(f"  DEX d{a['DEX']}  INS d{a['INS']}  MIG d{a['MIG']}  WLP d{a['WLP']}")
    print(f"  HP {s['max_hp']} (Crisis {s['crisis']})   MP {s['max_mp']}")
    print(f"  Init {s['initiative']}   DEF {s['defense']} (+DEX die)   M.DEF {s['magic_defense']} (+INS die)")
    print(f"  Accuracy/Magic check bonus +{s['check_bonus']}   Extra attack/spell damage +{s['damage_bonus']}")
    if s["turns_per_round"] > 1:
        print(f"  Turns/round: {s['turns_per_round']}   Bonus skills to choose: {s['extra_skills']}")
    if species:
        sp = _species_rules(species)
        if sp:
            print(f"  Species: {sp['starting_skills']} starting Skills — {sp['rules_text']}")
    if villain_rank is not None:
        up = villain_ultima(villain_rank)
        print(f"  VILLAIN [{villain_rank}]: {up} Ultima Points"
              f" (Ultima Points do NOT grant extra turns — make it elite/champion for that)")


def cmd_npc(a, villain_rank=None):
    if a.array not in ARRAYS:
        sys.exit(f"--array must be one of {', '.join(ARRAYS)}")
    order = a.order.split(",") if a.order else None
    if order and (sorted(order) != sorted(ATTRS)):
        sys.exit(f"--order must be a permutation of {','.join(ATTRS)}")
    s = base_scores(a.level, ARRAYS[a.array], order)
    danger = a.danger if villain_rank else a.rank
    if danger and danger != "soldier":
        s = apply_danger(s, danger, a.n)
    print(f"🧬 {'VILLAIN' if villain_rank else 'NPC'} STAT BLOCK  (array: {a.array})")
    _print_block(s, a.species, villain_rank)
    print(f"  Basic attack profile: 【Attr+Attr】 · 【HR+5】 (type)   [npc_design]")
    if a.save:
        _save(s, a.save, a.species, "villain" if villain_rank else "npc")
    return 0


def cmd_villain(a):
    if a.rank not in ("minor", "major", "supreme"):
        sys.exit("villain --rank must be minor|major|supreme")
    return cmd_npc(a, villain_rank=a.rank)


def cmd_monster(a):
    c = F.find("creature", a.key)
    if not c:
        sys.exit(f"no bestiary creature '{a.key}'")
    s = {
        "level": c["level"], "attributes": c["attributes"],
        "max_hp": c["hp"], "crisis": c.get("crisis", c["hp"] // 2),
        "max_mp": c["mp"], "initiative": c["initiative"],
        "defense": c["defense"], "magic_defense": c["magic_defense"],
        "check_bonus": max(0, c["level"] // 10), "damage_bonus": 0,
        "turns_per_round": 1, "extra_skills": 0, "rank": c.get("rank", "soldier"),
    }
    if a.rank and a.rank != "soldier":
        s = apply_danger(s, a.rank, a.n)
    print(f"🧬 {c['name']}  ({c['species']})")
    _print_block(s, c["species"])
    if c.get("affinities"):
        print(f"  Affinities: " + ", ".join(f"{k}:{v}" for k, v in c["affinities"].items()))
    for atk in c.get("attacks", []):
        print(f"  • {atk['name']}: {atk.get('accuracy','')} · {atk.get('damage','')}")
    return 0


def _save(s, name, species, kind):
    sheet = {
        "name": name, "kind": kind, "level": s["level"],
        "species": species or "", "rank": s["rank"],
        "attributes": s["attributes"],
        "max_hp": s["max_hp"], "hp": s["max_hp"], "crisis": s["crisis"],
        "max_mp": s["max_mp"], "mp": s["max_mp"],
        "defense": s["defense"], "magic_defense": s["magic_defense"],
        "initiative": s["initiative"], "statuses": [], "notes": "",
    }
    p = F.save_sheet(sheet)
    print(f"  saved → {p}")


def build_parser():
    p = argparse.ArgumentParser(prog="statgen.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("npc", "villain"):
        s = sub.add_parser(name)
        s.add_argument("--level", type=int, required=True)
        s.add_argument("--array", default="standard")
        s.add_argument("--species")
        s.add_argument("--order")
        s.add_argument("--save")
        if name == "npc":
            s.add_argument("--rank", default="soldier")
            s.add_argument("--n", type=int)
            s.set_defaults(fn=cmd_npc)
        else:
            s.add_argument("--rank", required=True)     # villain tier (ultima pts)
            s.add_argument("--danger", default="soldier")  # soldier/elite/champion (turns)
            s.add_argument("--n", type=int)
            s.set_defaults(fn=cmd_villain)
    s = sub.add_parser("monster"); s.add_argument("key")
    s.add_argument("--rank"); s.add_argument("--n", type=int); s.set_defaults(fn=cmd_monster)
    return p


def main(argv):
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
