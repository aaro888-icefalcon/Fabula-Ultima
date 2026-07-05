#!/usr/bin/env python3
"""
tick.py — the end-of-scene bookkeeping STATE MACHINE (memo §5, fork B3).

Reads campaign/state.json + data/subsystems.json + data/genre.json and ADVANCES the world:
each due subsystem runs a codified op — front clocks advance (1 + a Chaos-scaled roll through
the engine), the seed deck is rebuilt, the Fabula/Ultima economy is reconciled, Chaos is
judged. It emits (a) a JSON changelog to campaign/tick_log.json and (b) surfacing directives
(telegraph / turning_point) to hand back to the mythic-gm engine. All stochastic advances go
through engine.py; nothing is fudged.

  tick.py [scene#]      # advance one scene of bookkeeping (defaults to state.scene + 1)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine
import fudata as F
import gen
import state as S


def genre_rec(key):
    for g in F.load("genre")["genres"]:
        if g["key"] == key:
            return g
    return F.load("genre")["genres"][0]


def target_stage(filled, size, n):
    """Pure: how many telegraphs should have surfaced at this clock fill."""
    return int(filled / size * n) if size and n else 0


def due(cadence, scene):
    if cadence == "every_scene":
        return True
    if cadence.startswith("every_"):
        try:
            return scene % int(cadence.split("_")[1]) == 0
        except ValueError:
            return False
    return False                      # on_trigger:* → GM-judged, not auto-fired


# ------------------------------------------------------------------- ops
def op_front_tick(st, genre, log):
    filled_any, surfaced = False, []
    for f in S.list_fronts():
        c = f["clock"]
        if c["filled"] >= c["size"] and f.get("climax_surfaced"):
            continue
        r = engine.roll_die(10)
        accel = r <= st["chaos"]                       # Chaos-scaled acceleration
        adv = 1 + (1 if accel else 0)
        c["filled"] = min(c["size"], c["filled"] + adv)
        tel = f.get("telegraphs", [])
        tstage = target_stage(c["filled"], c["size"], len(tel))
        while f.get("stage", 0) < tstage and f.get("stage", 0) < len(tel):
            msg = tel[f["stage"]]
            surfaced.append(("telegraph", f["id"], msg))
            log.append({"sub": "villain_fronts", "front": f["id"], "surface": "telegraph", "detail": msg})
            f["stage"] = f.get("stage", 0) + 1
        if c["filled"] >= c["size"] and not f.get("climax_surfaced"):
            f["climax_surfaced"] = True
            filled_any = True
            surfaced.append(("turning_point", f["id"], f["name"]))
            log.append({"sub": "villain_fronts", "front": f["id"], "surface": "turning_point", "detail": f["name"]})
        log.append({"sub": "villain_fronts", "front": f["id"], "advance": adv,
                    "clock": [c["filled"], c["size"]], "accel": accel})
        S.save_front(f)
    return filled_any, surfaced


def op_clock_tick(st, log):
    cl = F.read_state("clocks.json", {"clocks": []})
    for c in cl.get("clocks", []):
        if c["filled"] < c["size"]:
            log.append({"sub": "campaign_clocks", "clock": c["id"], "state": [c["filled"], c["size"]],
                        "name": c["name"], "note": "GM advances via fu.py clock tick if the fiction implies"})


def op_fabula(st, log):
    pts = F.read_state("points.json", {"balances": {}})
    zero = [k for k, v in pts.get("balances", {}).items() if k.startswith("fabula:") and v == 0]
    vult = {e["id"]: e.get("ultima") for e in S.list_entities("villain")}
    log.append({"sub": "fabula_economy", "zero_fp": zero,
                "ultima_ledger": pts.get("balances", {}).get("ultima", 0), "villain_ultima": vult})


def op_reseed(st, genre, log):
    seeds = []
    for e in S.list_entities("pc") + S.list_entities("companion"):
        for b in e.get("bonds", []):
            seeds.append(f"Bond: {e['name']} ↔ {b.get('toward')} ({', '.join(b.get('emotions', []))})")
        if e.get("theme"):
            seeds.append(f"Theme under pressure: {e['name']} — {e['theme']}")
    for f in S.list_fronts():
        seeds.append(f"Front: {f['name']} [{f['clock']['filled']}/{f['clock']['size']}]")
    for e in S.list_entities("npc") + S.list_entities("villain"):
        seeds.append(f"{e['kind'].title()} {e['name']}: {e.get('drive') or e.get('want') or 'unclear aim'}")
    ct = genre["conflict_themes"]
    for _ in range(3):
        seeds.append("Genre pull: " + ct[engine.roll_die(len(ct)) - 1]["value"])
    seeds.append("New face: " + gen.weighted_table("npc_role.json", genre.get("generation_bias", {}).get("npc_role")))
    seeds.append("Complication: " + gen.weighted_table("complication.json", None))
    # pad toward the 30-card floor from genre pulls + hooks when state is still sparse
    guard = 0
    while len(seeds) < 30 and guard < 60:
        seeds.append("Genre pull: " + ct[engine.roll_die(len(ct)) - 1]["value"])
        seeds.append("Hook: " + gen.weighted_table("atlas_hook.json", None))
        guard += 1
    # de-dup preserving order, cap at 40
    seen, deck = set(), []
    for s in seeds:
        if s not in seen:
            seen.add(s)
            deck.append(s)
    st["seeds"] = deck[:40]
    log.append({"sub": "seed_deck", "count": len(st["seeds"])})


def op_chaos(st, genre, filled_any, log):
    old = st["chaos"]
    if filled_any:
        st["chaos"] = min(9, st["chaos"] + 1)
    floor = genre.get("chaos", {}).get("floor")
    if floor:
        st["chaos"] = max(st["chaos"], floor)
    log.append({"sub": "chaos", "from": old, "to": st["chaos"]})


OPS = {"front_tick": None, "clock_tick": op_clock_tick, "project_tick": None,
       "reseed": None, "fabula_reconcile": op_fabula, "chaos_judge": None}


def main(argv):
    scene_arg = int(argv[0]) if argv and argv[0].lstrip("-").isdigit() else None
    st = S.load_state()
    scene = scene_arg if scene_arg is not None else st.get("scene", 0) + 1
    st["scene"] = scene
    genre = genre_rec(st.get("genre", "core"))
    subs = F.load("subsystems")["subsystems"]
    log, surfaced, filled_any = [], [], False

    print(f"🧾 TICK — scene {scene} · genre {st['genre']} · chaos {st['chaos']}")
    for row in subs:
        if not due(row["cadence"], scene):
            if row["cadence"].startswith("on_trigger"):
                print(f"  · {row['id']}: on trigger ({row['cadence'].split(':', 1)[1]}) — apply if it fits")
            continue
        op = row["advance"]
        if op == "front_tick":
            fa, su = op_front_tick(st, genre, log)
            filled_any = filled_any or fa
            surfaced += su
        elif op == "reseed":
            op_reseed(st, genre, log)
        elif op == "chaos_judge":
            op_chaos(st, genre, filled_any, log)
        elif OPS.get(op):
            OPS[op](st, log)
    S.save_state(st)

    print("  fronts:")
    for f in S.list_fronts(include_resolved=True):
        c = f["clock"]
        flag = "  ⚑ CLIMAX → Turning Point" if c["filled"] >= c["size"] else ""
        print(f"    {f['id']} [{c['filled']}/{c['size']}]{flag}")
    if surfaced:
        print("  ⚡ SURFACING (hand to the engine):")
        for kind, fid, msg in surfaced:
            tail = "  → run adventure_crafter.py turning-point" if kind == "turning_point" else ""
            print(f"    [{kind}] {fid}: {msg}{tail}")
    print(f"  seeds refreshed: {len(st.get('seeds', []))}  ·  chaos now {st['chaos']}")

    hist = F.read_state("tick_log.json", {"ticks": []})
    hist["ticks"].append({"scene": scene, "chaos": st["chaos"], "surfaced": len(surfaced), "changes": log})
    F.write_state("tick_log.json", hist)
    print("  changelog → campaign/tick_log.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
