#!/usr/bin/env python3
"""
fu.py — the Fabula Ultima play CLI (rung 1 of the oracle ladder: anything a PC or
NPC *attempts to do* resolves HERE, not with a Fate Question). Every die is rolled
through engine.py → mythic-gm/dice.py, so all randomness is engine-honest and shown.

  fu.py check d10 d8 --dl 10 [--bond N] [--mod N] [--sit +2|-2]
  fu.py opposed d10 d8 --vs d12 d12
  fu.py group d10 d8 --dl 13 [--support-successes K] [--bond N]
  fu.py attack --weapon steel_dagger --attrs d10 d8 --target giant_rat
  fu.py spell fulgur --attrs d10 d10 --target skeletal_soldier
  fu.py damage <target> 14 fire [--affinity vulnerable] [--hp H --maxhp M --crisis C]
  fu.py status <sheet> +slow            # or -slow, or `status show <sheet>`
  fu.py clock new "Ritual of the Eclipse" 8 | fu.py clock tick <id> 2 | fu.py clock list
  fu.py points fabula +1 --owner Valea --reason "fumble" | fu.py points ultima -2 --reason "..."
  fu.py init "Valea:9" "Bandit:7" --sides pc,npc
  fu.py rest [--sheet Valea]            # full rest: HP/MP to max, statuses cleared
  fu.py crisis <target>
  fu.py tick [scene#]                   # companion bookkeeping checklist

The pure resolution math (crit/fumble, affinity matrix, status downgrade, crisis)
is importable and unit-tested; the commands are thin wrappers over it + engine.py.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine
import fudata as F
import state as S

DIE_SIZES = [6, 8, 10, 12]
ATTR_FULL = {"Dexterity": "DEX", "Insight": "INS", "Might": "MIG", "Willpower": "WLP"}


# ============================================================ pure resolution
def parse_die(spec):
    """'d10' or '10' -> 10."""
    s = str(spec).lower().lstrip("d")
    return int(s)


def check_math(faces, modifier=0, dl=None):
    """Given the two attribute-die faces, return the FU check outcome.
    crit = both faces equal AND >= 6; fumble = both faces == 1."""
    a, b = faces[0], faces[1]
    crit = (a == b and a >= 6)
    fumble = (a == 1 and b == 1)
    hr = max(a, b)
    total = a + b + modifier
    out = {"faces": [a, b], "modifier": modifier, "total": total, "hr": hr,
           "crit": crit, "fumble": fumble}
    if dl is not None:
        if fumble:
            out["success"] = False
        elif crit:
            out["success"] = True
        else:
            out["success"] = total >= dl
        out["dl"] = dl
    return out


def reduce_affinity(affinities):
    """Collapse a set of affinities per the rules: absorb > immune;
    vulnerable+resistant cancel; else the lone affinity; else None."""
    s = set(affinities or [])
    if "absorb" in s:
        return "absorb"
    if "immune" in s:
        return "immune"
    if "vulnerable" in s and "resistant" in s:
        return None
    if "vulnerable" in s:
        return "vulnerable"
    if "resistant" in s:
        return "resistant"
    return None


def affinity_delta(amount, affinity):
    """Signed HP delta from `amount` incoming damage under `affinity`.
    negative = HP lost; positive = HP healed (absorb). Halving rounds down."""
    if affinity == "immune":
        return 0
    if affinity == "absorb":
        return +amount
    if affinity == "vulnerable":
        return -2 * amount
    if affinity == "resistant":
        return -(amount // 2)
    return -amount


def effective_attributes(base, active_statuses, statuses_data):
    """Apply status die-downgrades (cumulative, floor d6) to a {DEX,INS,MIG,WLP} map."""
    smap = {s["key"]: s for s in statuses_data["statuses"]}
    steps = {ab: 0 for ab in base}
    for st in active_statuses or []:
        s = smap.get(st)
        if not s:
            continue
        for full in s["downgrades"]:
            ab = ATTR_FULL.get(full, full)
            if ab in steps:
                steps[ab] += 1
    out = {}
    for ab, die in base.items():
        idx = DIE_SIZES.index(die) if die in DIE_SIZES else 0
        out[ab] = DIE_SIZES[max(0, idx - steps[ab])]
    return out


def is_crisis(hp, crisis):
    return hp <= crisis


def crisis_crossed(old_hp, new_hp, crisis):
    return old_hp > crisis and new_hp <= crisis


# ============================================================ command helpers
def _roll_pool(dice_sizes, label=""):
    res = engine.roll_pool(dice_sizes)
    shown = " + ".join(f"d{d['sides']}={d['face']}" for d in res["dice"])
    if label:
        print(f"   🎲 {label}: {shown}")
    return res["faces"]


def _fmt_check(o):
    tag = "  ⭐CRIT" if o["crit"] else ("  💥FUMBLE" if o["fumble"] else "")
    line = f"   result {o['total']} (HR {o['hr']}){tag}"
    if "success" in o:
        line += f"   vs DL {o['dl']} → {'SUCCESS' if o['success'] else 'FAILURE'}"
    return line


# ============================================================ commands
def cmd_check(a):
    dice = [parse_die(x) for x in a.dice]
    if len(dice) != 2:
        sys.exit("a check rolls exactly two dice, e.g. `check d10 d8`")
    mod = a.mod + (a.sit or 0) + (a.bond or 0)
    print(f"🎯 CHECK  [{'+'.join('d'+str(d) for d in dice)}]"
          + (f"  DL {a.dl}" if a.dl is not None else "  (open/opposed: no DL)"))
    faces = _roll_pool(dice, "roll")
    o = check_math(faces, mod, a.dl)
    bits = []
    if a.mod:
        bits.append(f"mod {a.mod:+d}")
    if a.sit:
        bits.append(f"situational {a.sit:+d}")
    if a.bond:
        bits.append(f"bond +{a.bond}")
    if bits:
        print("   " + ", ".join(bits))
    print(_fmt_check(o))
    if o["fumble"]:
        print("   → PC fumble: gain 1 Fabula Point; opposition gets an opportunity.  [rules.fumble]")
    elif o["crit"]:
        print("   → critical: automatic success + an opportunity.  [rules.critical]")
    return 0


def cmd_opposed(a):
    pc = [parse_die(x) for x in a.dice]
    foe = [parse_die(x) for x in a.vs]
    print(f"⚔️  OPPOSED CHECK")
    pf = _roll_pool(pc, "you")
    ff = _roll_pool(foe, "foe")
    po, fo = check_math(pf), check_math(ff)

    def rank(o):
        if o["crit"]:
            return (2, o["total"])
        if o["fumble"]:
            return (-1, 0)
        return (1, o["total"])
    pr, fr = rank(po), rank(fo)
    if pr == fr:
        winner = "TIE — repeat the check"
    else:
        winner = "YOU win" if pr > fr else "FOE wins"
    print(f"   you {po['total']}{' CRIT' if po['crit'] else (' FUMBLE' if po['fumble'] else '')}"
          f"  vs  foe {fo['total']}{' CRIT' if fo['crit'] else (' FUMBLE' if fo['fumble'] else '')}"
          f"  → {winner}  (ties to no one; repeat)")
    return 0


def cmd_group(a):
    dice = [parse_die(x) for x in a.dice]
    support = (a.support_successes or 0) + (a.bond or 0)
    print(f"👥 GROUP CHECK  leader [{'+'.join('d'+str(d) for d in dice)}]  DL {a.dl}")
    print(f"   support bonus +{support}  ({a.support_successes or 0} successful supports"
          f" +{a.bond or 0} highest bond)")
    faces = _roll_pool(dice, "leader")
    o = check_math(faces, support, a.dl)
    print(_fmt_check(o))
    return 0


def _attacker_dice(a, needed):
    """Resolve the two attribute die sizes for an accuracy/magic check."""
    if a.attrs:
        return [parse_die(x) for x in a.attrs]
    if a.sheet:
        sh = F.load_sheet(a.sheet)
        if not sh:
            sys.exit(f"no sheet '{a.sheet}'")
        base = sh["attributes"]
        eff = effective_attributes(base, sh.get("statuses", []), F.load("statuses"))
        return [eff[ab] for ab in needed]
    sys.exit("need --attrs d10 d8 (or --sheet with the attacker's sheet)")


def cmd_attack(a):
    w = F.find("weapon", a.weapon)
    if not w:
        sys.exit(f"no weapon '{a.weapon}'")
    acc = w["accuracy"]
    dice = _attacker_dice(a, acc["attributes"])
    tgt, tgt_persist = S.resolve_target(a.target) if a.target else (None, None)
    dl = a.dl if a.dl is not None else (tgt["defense"] if tgt else None)
    print(f"🗡️  ATTACK  {w['name']}  ["
          f"{'+'.join(acc['attributes'])}]{acc['bonus']:+d}"
          + (f"  vs {tgt['name']} DEF {dl}" if tgt else (f"  vs DEF {dl}" if dl is not None else "")))
    faces = _roll_pool(dice, "accuracy")
    o = check_math(faces, acc["bonus"] + a.acc_bonus, dl)
    print(_fmt_check(o))
    if "success" in o and not o["success"]:
        print("   miss — no damage.")
        return 0
    dmg = o["hr"] + w["damage"]["bonus"] + a.dmg_bonus
    dtype = w["damage"]["type"]
    print(f"   damage = HR {o['hr']} + {w['damage']['bonus'] + a.dmg_bonus} = {dmg} {dtype}")
    if tgt:
        aff = (tgt.get("affinities") or {}).get(dtype)
        delta = affinity_delta(dmg, aff)
        new_hp = _report_damage(tgt["name"], dmg, dtype, aff, delta, tgt.get("hp"), tgt.get("crisis"))
        if tgt_persist and new_hp is not None:      # persist the hit against a tracked entity
            tgt["hp"] = max(new_hp, 0)
            tgt_persist()
    return 0


def cmd_spell(a):
    sp = F.find("spell", a.spell)
    if not sp:
        sys.exit(f"no spell '{a.spell}'")
    print(f"✨ SPELL  {sp['name']}  [{sp['class']}]  MP {sp['mp_cost']}"
          f"  · target: {sp['target']}  · {sp['duration']}")
    print(f"   {sp['text'][:280]}{'…' if len(sp['text'])>280 else ''}  [spells.{sp['key']}]")
    if sp.get("offensive") and (a.attrs or a.sheet):
        tgt = F.find("creature", a.target) if a.target else None
        dl = a.dl if a.dl is not None else (tgt["magic_defense"] if tgt else None)
        dice = _attacker_dice(a, ["INS", "WLP"])
        print(f"   magic check vs {'M.DEF '+str(dl) if dl is not None else 'M.DEF'}:")
        faces = _roll_pool(dice, "magic")
        o = check_math(faces, a.acc_bonus, dl)
        print(_fmt_check(o))
    return 0


def _report_damage(name, amount, dtype, aff, delta, cur_hp=None, crisis=None):
    verb = "heals" if delta > 0 else "loses"
    print(f"   → {name} {verb} {abs(delta)} HP"
          + (f"  [{aff}]" if aff else "  [no affinity]") + f"  ({amount} {dtype} incoming)")
    if cur_hp is not None:
        new_hp = cur_hp + delta
        print(f"     HP {cur_hp} → {new_hp}", end="")
        if crisis is not None:
            if new_hp <= 0:
                print("   ‼ 0 HP")
            elif crisis_crossed(cur_hp, new_hp, crisis):
                print(f"   ⚠ enters CRISIS (≤ {crisis})")
            else:
                print()
        else:
            print()
        return new_hp
    return None


def cmd_damage(a):
    amount = int(a.amount)
    dtype = a.type
    aff = a.affinity
    cur_hp = a.hp
    crisis = a.crisis
    name = a.target
    # resolve against the campaign store: stored entity → PC sheet → bestiary template.
    # --hp forces the stateless path (ad-hoc target).
    rec, persist = (None, None) if a.hp is not None else S.resolve_target(a.target)
    if rec:
        name = rec.get("name", name)
        if aff is None:
            aff = (rec.get("affinities") or {}).get(dtype)
        if cur_hp is None:
            cur_hp = rec.get("hp")
        if crisis is None:
            crisis = rec.get("crisis", (rec.get("max_hp", 0) // 2) or None)
    delta = affinity_delta(amount, aff)
    print(f"💢 DAMAGE  {amount} {dtype} → {name}")
    new_hp = _report_damage(name, amount, dtype, aff, delta, cur_hp, crisis)
    if rec is not None and persist and new_hp is not None:
        rec["hp"] = max(new_hp, 0)
        persist()                                  # writes to the entity file or PC sheet
        if new_hp <= 0 and rec.get("kind") in ("pc", "companion"):
            z = F.load("rules")["zero_hp"]
            print("\n   ‼ 0 HIT POINTS — the choice is the player's:  [rules.zero_hp]")
            print("   SURRENDER: " + z.get("surrender", "").strip())
            print("   SACRIFICE: " + z.get("sacrifice", "").strip())
    return 0


def cmd_status(a):
    if a.sheet == "show" or (a.change and a.change.lower() == "show"):
        sys.exit("usage: fu.py status <sheet> +slow | -slow | show")
    sh, persist = S.resolve_target(a.sheet)
    if not sh:
        sys.exit(f"no target '{a.sheet}'")
    statuses = F.load("statuses")
    valid = {s["key"] for s in statuses["statuses"]}
    active = list(sh.get("statuses", []))
    if a.change and a.change != "show":
        op, key = a.change[0], a.change[1:]
        if key not in valid:
            sys.exit(f"unknown status '{key}'. valid: {', '.join(sorted(valid))}")
        if op == "+":
            if key in active:
                print(f"   {sh['name']} already {key} — no change (re-apply is a no-op).  [statuses.rules]")
            else:
                active.append(key)
        elif op == "-":
            if key in active:
                active.remove(key)
        else:
            sys.exit("change must start with + or -")
        sh["statuses"] = active
        if persist:
            persist()
    base = sh["attributes"]
    eff = effective_attributes(base, active, statuses)
    print(f"🩸 STATUS  {sh['name']}  active: {active or '—'}")
    print("   attributes: " + ", ".join(
        f"{ab} d{base[ab]}" + (f"→d{eff[ab]}" if eff[ab] != base[ab] else "") for ab in base))
    return 0


def cmd_clock(a):
    st = F.read_state("clocks.json", {"next_id": 1, "clocks": []})
    if a.op == "new":
        cid = st["next_id"]
        st["next_id"] += 1
        st["clocks"].append({"id": cid, "name": a.name, "size": int(a.size), "filled": 0})
        F.write_state("clocks.json", st)
        print(f"🕐 clock #{cid} '{a.name}'  [0/{a.size}]")
    elif a.op == "tick":
        for c in st["clocks"]:
            if c["id"] == int(a.name):
                c["filled"] = max(0, min(c["size"], c["filled"] + int(a.size or 1)))
                F.write_state("clocks.json", st)
                full = "  ✅ FILLED — resolve it now" if c["filled"] >= c["size"] else ""
                print(f"🕐 clock #{c['id']} '{c['name']}'  [{c['filled']}/{c['size']}]{full}")
                return 0
        sys.exit(f"no clock #{a.name}")
    else:  # list
        if not st["clocks"]:
            print("   (no clocks)")
        for c in st["clocks"]:
            print(f"   #{c['id']}  [{c['filled']}/{c['size']}]  {c['name']}")
    return 0


def cmd_points(a):
    st = F.read_state("points.json", {"balances": {}, "log": []})
    ledger = a.ledger
    delta = int(a.delta)
    if ledger == "fabula":
        owner = a.owner or "party"
        key = f"fabula:{owner}"
    elif ledger == "ultima":
        if not a.reason:
            sys.exit("ultima spends must carry a --reason (visible ledger).")
        owner = "GM"
        key = "ultima"
    else:
        sys.exit("ledger must be 'fabula' or 'ultima'")
    bal = st["balances"].get(key, 0) + delta
    if bal < 0:
        sys.exit(f"{key} cannot go below 0 (was {st['balances'].get(key,0)}, delta {delta}).")
    st["balances"][key] = bal
    st["log"].append({"ledger": ledger, "owner": owner, "delta": delta,
                      "reason": a.reason or "", "balance": bal})
    F.write_state("points.json", st)
    print(f"🎴 {ledger} [{owner}] {delta:+d} → {bal}"
          + (f'   ({a.reason})' if a.reason else ""))
    return 0


def cmd_init(a):
    combatants = []
    for spec in a.combatants:
        name, _, score = spec.partition(":")
        combatants.append((name.strip(), int(score or 0)))
    print("🏁 INITIATIVE")
    rolled = []
    for name, score in combatants:
        tie = engine.roll_die(20)
        rolled.append((score, tie, name))
        print(f"   {name}: init {score}  (+d20 tiebreak {tie})")
    rolled.sort(reverse=True)
    print("   order: " + " → ".join(n for _, _, n in rolled))
    return 0


def cmd_rest(a):
    print("🛏️  REST — recover all HP and MP; clear all status effects.  [rules.resting]")
    if a.sheet:
        sh = F.load_sheet(a.sheet)
        if not sh:
            sys.exit(f"no sheet '{a.sheet}'")
        sh["hp"] = sh.get("max_hp", sh.get("hp"))
        sh["mp"] = sh.get("max_mp", sh.get("mp"))
        sh["statuses"] = []
        F.save_sheet(sh)
        print(f"   {sh['name']}: HP {sh['hp']}/{sh.get('max_hp')} · MP {sh['mp']}/{sh.get('max_mp')} · statuses cleared")
    return 0


def cmd_crisis(a):
    rec, _ = S.resolve_target(a.target)
    if not rec:
        sys.exit(f"no target '{a.target}'")
    hp = rec.get("hp")
    crisis = rec.get("crisis", (rec.get("max_hp", 0) // 2) or None)
    print(f"🩹 {rec['name']}: HP {hp}, Crisis {crisis} → {'IN CRISIS' if is_crisis(hp, crisis) else 'stable'}")
    return 0


def cmd_tick(a):
    """End-of-scene bookkeeping. Delegates to the codified state machine (tick.py), which
    advances villain fronts, reseeds, reconciles the Fabula/Ultima economy, and judges Chaos."""
    import tick
    return tick.main([str(a.scene)] if a.scene else [])


# ============================================================ argparse
def build_parser():
    p = argparse.ArgumentParser(prog="fu.py", description="Fabula Ultima play CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("check"); s.add_argument("dice", nargs=2)
    s.add_argument("--dl", type=int); s.add_argument("--bond", type=int, default=0)
    s.add_argument("--mod", type=int, default=0); s.add_argument("--sit", type=int, default=0)
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("opposed"); s.add_argument("dice", nargs=2)
    s.add_argument("--vs", nargs=2, required=True); s.set_defaults(fn=cmd_opposed)

    s = sub.add_parser("group"); s.add_argument("dice", nargs=2)
    s.add_argument("--dl", type=int, required=True)
    s.add_argument("--support-successes", type=int, default=0)
    s.add_argument("--bond", type=int, default=0); s.set_defaults(fn=cmd_group)

    s = sub.add_parser("attack"); s.add_argument("--weapon", required=True)
    s.add_argument("--attrs", nargs=2); s.add_argument("--sheet")
    s.add_argument("--target"); s.add_argument("--dl", type=int)
    s.add_argument("--acc-bonus", type=int, default=0); s.add_argument("--dmg-bonus", type=int, default=0)
    s.set_defaults(fn=cmd_attack)

    s = sub.add_parser("spell"); s.add_argument("spell")
    s.add_argument("--attrs", nargs=2); s.add_argument("--sheet")
    s.add_argument("--target"); s.add_argument("--dl", type=int)
    s.add_argument("--acc-bonus", type=int, default=0); s.set_defaults(fn=cmd_spell)

    s = sub.add_parser("damage"); s.add_argument("target"); s.add_argument("amount")
    s.add_argument("type"); s.add_argument("--affinity")
    s.add_argument("--hp", type=int); s.add_argument("--maxhp", type=int); s.add_argument("--crisis", type=int)
    s.set_defaults(fn=cmd_damage)

    s = sub.add_parser("status"); s.add_argument("sheet"); s.add_argument("change", nargs="?")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("clock"); s.add_argument("op", choices=["new", "tick", "list"])
    s.add_argument("name", nargs="?"); s.add_argument("size", nargs="?")
    s.set_defaults(fn=cmd_clock)

    s = sub.add_parser("points"); s.add_argument("ledger", choices=["fabula", "ultima"])
    s.add_argument("delta"); s.add_argument("--owner"); s.add_argument("--reason")
    s.set_defaults(fn=cmd_points)

    s = sub.add_parser("init"); s.add_argument("combatants", nargs="+")
    s.add_argument("--sides"); s.set_defaults(fn=cmd_init)

    s = sub.add_parser("rest"); s.add_argument("--sheet"); s.set_defaults(fn=cmd_rest)
    s = sub.add_parser("crisis"); s.add_argument("target"); s.set_defaults(fn=cmd_crisis)
    s = sub.add_parser("tick"); s.add_argument("scene", nargs="?"); s.set_defaults(fn=cmd_tick)
    return p


def main(argv):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
