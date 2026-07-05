#!/usr/bin/env python3
"""
gen.py — the emergent generation composer (memo §4, forks C2 + D2).

Turns "I need a …" into a COMPLETE, PERSISTED, genre-appropriate JSON entity by composing
the pieces already in the skill: statgen (mechanics) + bridge/generators/*.json (seeds,
re-weighted by the active genre) + genre.json (filter/flavor) + a link to the world (a
Bond hook to a PC, a faction/home). Antagonists also get an agenda FRONT (a clock the tick
advances), so the world evolves without anyone authoring the next beat.

Every random choice is rolled through engine.py → mythic-gm/dice.py (honest, shown-able).
Scripts scaffold the skeleton, numbers, links, and agenda; the GM narrates the flesh.

  gen.py npc      [--genre G] [--near <pc>] [--faction F] [--level L] [--name X]
  gen.py villain  --rank minor|major|supreme [--genre G] [--vs <pc>] [--level L] [--name X]
  gen.py monster  --from <bestiary-key> | (--level L --species X) [--rank elite|champion --n N]
  gen.py faction  [--genre G] [--name X]
  gen.py front    "<name>" --size N [--drive D] [--genre G]
  gen.py world    [--genre G]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine
import fudata as F
import statgen
import state as S

GEN = os.path.join(F.ROOT, "bridge", "generators")

NAMES = ["Alira", "Bastien", "Cerise", "Doran", "Eira", "Fenn", "Giselle", "Halden",
         "Isolde", "Joren", "Kesia", "Lucan", "Mira", "Noll", "Oriel", "Perrin",
         "Quill", "Rhea", "Sable", "Tamsin", "Ulric", "Vesna", "Wren", "Xio",
         "Yarrow", "Zeph", "Corvin", "Nadia", "Ramis", "Valincor", "Toris", "Remora"]
TITLES = ["the Ashen", "of the Broken Crown", "the Undying", "Ninth Blade", "the Hollow",
          "of Quivira", "the Star-Witch", "Iron Regent", "the Devourer", "Lord-Extractor"]
WANTS = ["to protect someone they love", "to climb in status or power", "to settle an old score",
         "to hide a dangerous secret", "to survive the coming trouble", "to serve a hidden master",
         "to win the heroes' trust", "to profit from the situation", "to escape a debt or oath",
         "to prove themselves to a rival"]
EMOTIONS = ["admiration", "inferiority", "loyalty", "mistrust", "affection", "hatred"]


def _genre(key):
    for g in F.load("genre")["genres"]:
        if g["key"] == key:
            return g
    return F.load("genre")["genres"][0]


def _active_genre(arg):
    return arg or S.load_state().get("genre", "core")


def _pick(seq):
    """Uniform pick from a python list, via the engine (honest)."""
    if not seq:
        return None
    return seq[engine.roll_die(len(seq)) - 1]


def expand_pool(entries, biasmap):
    """Pure: expand a generator table's entries into a weighted pool. Base weight = the entry's
    die span; an entry whose value contains a bias key is multiplied by that key's weight."""
    pool = []
    for e in entries:
        span = e["max"] - e["min"] + 1
        mult = 1
        for bk, bm in (biasmap or {}).items():
            if bk.lower() in e["value"].lower():
                mult = max(mult, bm)
        pool += [e["value"]] * (span * mult)
    return pool


def weighted_table(table_name, biasmap):
    """Genre-weighted pick from a bridge generator table — a 1dN roll through the engine over
    the expanded pool (honest + weighted)."""
    import json
    t = json.load(open(os.path.join(GEN, table_name), encoding="utf-8"))
    pool = expand_pool(t["entries"], biasmap)
    return pool[engine.roll_die(len(pool)) - 1]


def _telegraph_ladder(drive, genre, n):
    base = [
        f"rumors and distant signs of {drive.lower()}",
        "a visible move against an ally, place, or resource the heroes value",
        "open action — the threat strikes in the light of day",
        "the agenda nears completion; the world reels",
        "the point of no return",
    ]
    return base[:max(2, min(n, len(base)))]


def _uid(prefix, name):
    base = f"{prefix}.{S.slug(name)}"
    if not os.path.isfile(S.entity_path(base)) and not os.path.isfile(S.front_path(base)):
        return base
    i = 2
    while os.path.isfile(S.entity_path(f"{base}-{i}")) or os.path.isfile(S.front_path(f"{base}-{i}")):
        i += 1
    return f"{base}-{i}"


def _prov(who, genre):
    return {"by": who, "genre": genre, "created_scene": S.load_state().get("scene", 0)}


# ---------------------------------------------------------------------- npc
def cmd_npc(a):
    gk = _active_genre(a.genre)
    g = _genre(gk)
    role = weighted_table("npc_role.json", g.get("generation_bias", {}).get("npc_role"))
    name = a.name or _pick(NAMES)
    want = _pick(WANTS)
    e = {"id": _uid("npc", name), "kind": "npc", "name": name, "genre": gk, "source": g["source"],
         "role": role, "want": want, "faction": a.faction or "", "home": "", "bonds": [],
         "statuses": [], "provenance": _prov("gen.py npc", gk)}
    if a.near:
        e["bonds"].append({"toward": a.near if "." in a.near else "pc." + S.slug(a.near),
                           "strength": 1, "emotions": [_pick(EMOTIONS)]})
    if a.level:                       # combat-capable NPC → soldier stats
        sp = _pick(g.get("featured_species") or ["humanoid"])
        sc = statgen.base_scores(a.level, statgen.ARRAYS["standard"])
        e.update({"species": sp, "level": a.level, "rank": "soldier",
                  "attributes": sc["attributes"], "hp": sc["max_hp"], "max_hp": sc["max_hp"],
                  "mp": sc["max_mp"], "max_mp": sc["max_mp"], "crisis": sc["crisis"],
                  "defense": sc["defense"], "magic_defense": sc["magic_defense"],
                  "initiative": sc["initiative"]})
    S.save_entity(e)
    print(f"🧑 NPC {e['id']}  ({role})")
    print(f"   {name} — wants {want}" + (f"; species {e.get('species')} L{a.level}" if a.level else ""))
    if e["bonds"]:
        print(f"   Bond → {e['bonds'][0]['toward']}: {e['bonds'][0]['emotions'][0]}")
    print(f"   [genre {gk}]  → GM: narrate the face, voice, and the twist behind the want.")
    return 0


# ------------------------------------------------------------------- villain
RANK_DEFAULTS = {"minor": (15, "elite", None), "major": (30, "champion", 2), "supreme": (45, "champion", 3)}
CLOCK_SIZE = {"minor": 6, "major": 8, "supreme": 10}


def cmd_villain(a):
    gk = _active_genre(a.genre)
    g = _genre(gk)
    drive = weighted_table("villain_drive.json", g.get("generation_bias", {}).get("villain_drive"))
    lvl, danger, dn = RANK_DEFAULTS[a.rank]
    lvl = a.level or lvl
    species = _pick(g.get("featured_species") or ["humanoid"])
    array = "super" if a.rank != "minor" else "specialized"
    sc = statgen.apply_danger(statgen.base_scores(lvl, statgen.ARRAYS[array]), danger, dn)
    name = a.name or (_pick(NAMES) + " " + _pick(TITLES))
    vid = _uid("villain", name)
    aff = {}
    if g.get("damage_flavor"):
        aff[_pick(g["damage_flavor"])] = "resistant"
    e = {"id": vid, "kind": "villain", "name": name, "genre": gk, "source": g["source"],
         "species": species, "level": lvl, "rank": f"{a.rank}/{sc['rank']}",
         "attributes": sc["attributes"], "hp": sc["max_hp"], "max_hp": sc["max_hp"],
         "mp": sc["max_mp"], "max_mp": sc["max_mp"], "crisis": sc["crisis"],
         "defense": sc["defense"], "magic_defense": sc["magic_defense"], "initiative": sc["initiative"],
         "affinities": aff, "statuses": [], "drive": drive, "ultima": statgen.villain_ultima(a.rank),
         "bonds": [], "provenance": _prov("gen.py villain", gk)}
    if a.vs:
        e["bonds"].append({"toward": a.vs if "." in a.vs else "pc." + S.slug(a.vs),
                           "strength": 2, "emotions": ["hatred", "inferiority"]})
    # the agenda front — this is what makes the villain emergent
    fname = f"{name}'s design"
    fid = _uid("front", fname)
    size = CLOCK_SIZE[a.rank]
    front = {"id": fid, "kind": "front", "name": fname, "drive": drive, "genre": gk,
             "owner": vid, "clock": {"size": size, "filled": 0}, "stage": 0,
             "telegraphs": _telegraph_ladder(drive, gk, size // 2), "linked_entities": [vid],
             "resolved": False}
    e["agenda_front"] = fid
    S.save_entity(e)
    S.save_front(front)
    print(f"👑 VILLAIN {vid}  [{a.rank} · {sc['rank']}]  {name}")
    print(f"   drive: {drive}   Ultima {e['ultima']}   L{lvl} {species}   HP {e['hp']} MP {e['mp']}")
    if e["bonds"]:
        print(f"   enmity → {e['bonds'][0]['toward']}")
    print(f"   front {fid}  clock [0/{size}]  telegraphs: {len(front['telegraphs'])}")
    print(f"   [genre {gk}]  → the tick advances this front; a filled clock is a Turning Point.")
    return 0


# ------------------------------------------------------------------- monster
def cmd_monster(a):
    gk = _active_genre(a.genre)
    if a.frm:
        c = F.find("creature", a.frm)
        if not c:
            sys.exit(f"no bestiary creature '{a.frm}'")
        sc = {"attributes": c["attributes"], "max_hp": c["hp"], "crisis": c.get("crisis", c["hp"] // 2),
              "max_mp": c["mp"], "initiative": c["initiative"], "defense": c["defense"],
              "magic_defense": c["magic_defense"], "rank": c.get("rank", "soldier")}
        name, species, level, aff, attacks = c["name"], c["species"], c["level"], c.get("affinities", {}), c.get("attacks", [])
    else:
        if not (a.level and a.species):
            sys.exit("need --from <key>  OR  --level L --species X")
        base = statgen.base_scores(a.level, statgen.ARRAYS["standard"])
        sc = {"attributes": base["attributes"], "max_hp": base["max_hp"], "crisis": base["crisis"],
              "max_mp": base["max_mp"], "initiative": base["initiative"], "defense": base["defense"],
              "magic_defense": base["magic_defense"], "rank": "soldier"}
        name, species, level, aff, attacks = f"{a.species} soldier", a.species, a.level, {}, []
    if a.rank and a.rank != "soldier":
        sc = statgen.apply_danger({**sc, "level": level, "check_bonus": 0, "damage_bonus": 0,
                                   "turns_per_round": 1, "extra_skills": 0}, a.rank, a.n)
    e = {"id": _uid("monster", name), "kind": "monster", "name": name, "genre": gk,
         "species": species, "level": level, "rank": sc["rank"],
         "attributes": sc["attributes"], "hp": sc["max_hp"], "max_hp": sc["max_hp"],
         "mp": sc["max_mp"], "max_mp": sc["max_mp"], "crisis": sc["crisis"],
         "defense": sc["defense"], "magic_defense": sc["magic_defense"], "initiative": sc["initiative"],
         "affinities": aff, "attacks": attacks, "statuses": [], "provenance": _prov("gen.py monster", gk)}
    S.save_entity(e)
    print(f"🐲 MONSTER {e['id']}  {name}  L{level} {species} [{sc['rank']}]  HP {e['hp']}/{e['max_hp']}")
    return 0


# --------------------------------------------------------------- faction/front
def cmd_faction(a):
    gk = _active_genre(a.genre)
    g = _genre(gk)
    drive = weighted_table("villain_drive.json", g.get("generation_bias", {}).get("villain_drive"))
    name = a.name or (_pick(["The", "House", "Order of the", "Syndicate of the"]) + " " + _pick(TITLES).replace("the ", ""))
    fid = _uid("front", name)
    front = {"id": fid, "kind": "front", "name": name, "drive": drive, "genre": gk,
             "clock": {"size": 8, "filled": 0}, "stage": 0,
             "telegraphs": _telegraph_ladder(drive, gk, 4), "linked_entities": [], "resolved": False}
    S.save_front(front)
    print(f"🏴 FACTION/front {fid}  {name}\n   agenda: {drive}   clock [0/8]  [genre {gk}]")
    return 0


def cmd_front(a):
    gk = _active_genre(a.genre)
    fid = _uid("front", a.name)
    front = {"id": fid, "kind": "front", "name": a.name, "drive": a.drive or "an unfolding threat",
             "genre": gk, "clock": {"size": a.size, "filled": 0}, "stage": 0,
             "telegraphs": _telegraph_ladder(a.drive or "the threat", gk, a.size // 2),
             "linked_entities": [], "resolved": False}
    S.save_front(front)
    print(f"⏳ FRONT {fid}  {a.name}  clock [0/{a.size}]  [genre {gk}]")
    return 0


def cmd_world(a):
    gk = a.genre or "core"
    S.cmd_init(argparse.Namespace(genre=gk))
    g = _genre(gk)
    theme = weighted_table  # seed a starting front from a genre conflict theme
    ct = g["conflict_themes"]
    pick = ct[engine.roll_die(len(ct)) - 1]["value"]
    fid = _uid("front", pick[:24])
    S.save_front({"id": fid, "kind": "front", "name": pick, "drive": pick, "genre": gk,
                  "clock": {"size": 8, "filled": 0}, "stage": 0,
                  "telegraphs": _telegraph_ladder(pick, gk, 4), "linked_entities": [], "resolved": False})
    print(f"🌍 world seeded — genre {gk}; opening front {fid}: {pick}")
    print(f"   → run `worldgen.py run --genre {gk}` for full world/group/character creation.")
    return 0


def main(argv):
    p = argparse.ArgumentParser(prog="gen.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("npc"); s.add_argument("--genre"); s.add_argument("--near"); s.add_argument("--faction")
    s.add_argument("--level", type=int); s.add_argument("--name"); s.set_defaults(fn=cmd_npc)
    s = sub.add_parser("villain"); s.add_argument("--rank", required=True, choices=["minor", "major", "supreme"])
    s.add_argument("--genre"); s.add_argument("--vs"); s.add_argument("--level", type=int); s.add_argument("--name")
    s.set_defaults(fn=cmd_villain)
    s = sub.add_parser("monster"); s.add_argument("--from", dest="frm"); s.add_argument("--level", type=int)
    s.add_argument("--species"); s.add_argument("--rank"); s.add_argument("--n", type=int); s.add_argument("--genre")
    s.set_defaults(fn=cmd_monster)
    s = sub.add_parser("faction"); s.add_argument("--genre"); s.add_argument("--name"); s.set_defaults(fn=cmd_faction)
    s = sub.add_parser("front"); s.add_argument("name"); s.add_argument("--size", type=int, default=6)
    s.add_argument("--drive"); s.add_argument("--genre"); s.set_defaults(fn=cmd_front)
    s = sub.add_parser("world"); s.add_argument("--genre"); s.set_defaults(fn=cmd_world)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
