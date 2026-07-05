#!/usr/bin/env python3
"""
state.py — the canonical, atomized campaign store (memo §2, fork A3).

  campaign/state.json          index: scene, chaos, genre, entity ids, front ids, seed deck
  campaign/entities/<id>.json  one actor per file (pc/companion/npc/villain/monster)
  campaign/fronts/<id>.json    one antagonist/threat agenda per file (a clock + drive)

PCs authored via sheet.py stay YAML but are READABLE here as entities (adapter), so gen.py,
fu.py, and tick.py can treat every actor uniformly. clocks.json / points.json keep working
(fu.py owns them); state.json owns scene/chaos/genre and the entity/front indexes — one home
per datum. No randomness here.

CLI:
  state.py init [--genre core|high|natural|techno]
  state.py show | list [pc|npc|villain|monster|companion] | get <id>
  state.py import-sheets           # register existing campaign/sheets/*.yaml as pc entities
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fudata as F

ENTITIES = os.path.join(F.CAMPAIGN, "entities")
FRONTS = os.path.join(F.CAMPAIGN, "fronts")
STATE = os.path.join(F.CAMPAIGN, "state.json")

DEFAULT_STATE = {"scene": 0, "chaos": 5, "genre": "core",
                 "entities": [], "fronts": [], "seeds": []}


def slug(name):
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-").replace("--", "-")


def ensure():
    os.makedirs(ENTITIES, exist_ok=True)
    os.makedirs(FRONTS, exist_ok=True)


def load_state():
    if not os.path.isfile(STATE):
        return dict(DEFAULT_STATE)
    return json.load(open(STATE, encoding="utf-8"))


def save_state(st):
    ensure()
    json.dump(st, open(STATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def _write(path, obj):
    ensure()
    json.dump(obj, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


# ------------------------------------------------------------------ entities
def entity_path(eid):
    return os.path.join(ENTITIES, eid + ".json")


def save_entity(e):
    _write(entity_path(e["id"]), e)
    st = load_state()
    if e["id"] not in st["entities"]:
        st["entities"].append(e["id"])
        save_state(st)
    return e["id"]


def load_entity(eid):
    """Load a stored entity; if it's a PC id/name with only a YAML sheet, adapt that."""
    p = entity_path(eid)
    if os.path.isfile(p):
        return json.load(open(p, encoding="utf-8"))
    # PC-sheet adapter: 'pc.valea' or 'valea' → campaign/sheets/valea.yaml
    name = eid.split(".", 1)[1] if "." in eid else eid
    sh = F.load_sheet(name)
    if sh:
        e = dict(sh)
        e.setdefault("id", "pc." + slug(sh["name"]))
        e.setdefault("kind", sh.get("kind", "pc"))
        e["_sheet"] = F.sheet_path(sh["name"])   # marker: writes go back to the YAML
        return e
    return None


def list_entities(kind=None):
    out = []
    for p in sorted(glob.glob(os.path.join(ENTITIES, "*.json"))):
        e = json.load(open(p, encoding="utf-8"))
        if kind is None or e.get("kind") == kind:
            out.append(e)
    return out


def persist_entity(e):
    """Write an entity back to wherever it lives (entity file, or its PC sheet)."""
    if e.get("_sheet"):
        sh = {k: v for k, v in e.items() if not k.startswith("_") and k not in ("id",)}
        F.save_sheet(sh)
    else:
        save_entity(e)


# -------------------------------------------------------------------- fronts
def front_path(fid):
    return os.path.join(FRONTS, fid + ".json")


def save_front(f):
    _write(front_path(f["id"]), f)
    st = load_state()
    if f["id"] not in st["fronts"]:
        st["fronts"].append(f["id"])
        save_state(st)
    return f["id"]


def load_front(fid):
    p = front_path(fid)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else None


def list_fronts(include_resolved=False):
    out = []
    for p in sorted(glob.glob(os.path.join(FRONTS, "*.json"))):
        f = json.load(open(p, encoding="utf-8"))
        if include_resolved or not f.get("resolved"):
            out.append(f)
    return out


# ------------------------------------------------------- unified target resolve
def resolve_target(ref):
    """Resolve a combat/target ref to (record, persist_callable_or_None).
    Order: stored entity → PC sheet → bestiary template (stateless)."""
    e = load_entity(ref)
    if e:
        return e, (lambda x=e: persist_entity(x))
    # bestiary template (stateless — instance it with gen.py monster to persist)
    c = F.find("creature", ref)
    if c:
        return dict(c), None
    return None, None


# ------------------------------------------------------------------------- CLI
def cmd_init(a):
    st = load_state()
    if a.genre:
        st["genre"] = a.genre
        # seed chaos from genre.json
        for g in F.load("genre")["genres"]:
            if g["key"] == a.genre:
                st["chaos"] = g["chaos"]["start"]
    save_state(st)
    print(f"🗂️  state initialized — genre {st['genre']}, chaos {st['chaos']}, scene {st['scene']}")
    return 0


def cmd_show(_a):
    st = load_state()
    print(f"🗂️  scene {st['scene']} · chaos {st['chaos']} · genre {st['genre']}")
    print(f"   entities: {len(st['entities'])}  fronts: {len(list_fronts())} open  seeds: {len(st.get('seeds',[]))}")
    for f in list_fronts():
        c = f["clock"]
        print(f"   ⚔ front {f['id']}  [{c['filled']}/{c['size']}]  {f['name']}")
    return 0


def cmd_list(a):
    for e in list_entities(a.kind):
        extra = f" L{e.get('level')}" if e.get("level") else ""
        print(f"   {e['id']:28} {e.get('kind',''):9}{extra}  {e['name']}")
    return 0


def cmd_get(a):
    e = load_entity(a.id) or load_front(a.id)
    print(json.dumps(e, indent=2, ensure_ascii=False) if e else f"no entity/front '{a.id}'")
    return 0


def cmd_import(_a):
    n = 0
    for p in glob.glob(os.path.join(F.CAMPAIGN, "sheets", "*.yaml")):
        sh = F.yaml_load(open(p, encoding="utf-8").read())
        e = dict(sh)
        e["id"] = ("pc." if sh.get("kind", "pc") in ("pc", "companion") else "npc.") + slug(sh["name"])
        e.setdefault("kind", sh.get("kind", "pc"))
        save_entity(e)
        n += 1
    print(f"imported {n} sheet(s) as entities")
    return 0


def main(argv):
    p = argparse.ArgumentParser(prog="state.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("--genre"); i.set_defaults(fn=cmd_init)
    sub.add_parser("show").set_defaults(fn=cmd_show)
    l = sub.add_parser("list"); l.add_argument("kind", nargs="?"); l.set_defaults(fn=cmd_list)
    g = sub.add_parser("get"); g.add_argument("id"); g.set_defaults(fn=cmd_get)
    sub.add_parser("import-sheets").set_defaults(fn=cmd_import)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
