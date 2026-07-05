"""Pure resolution math for fu.py, statgen.py, sheet.py — no randomness, no I/O."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import fudata as F
import fu
import statgen
import sheet


# ----------------------------------------------------------------- fu: checks
def test_crit_requires_matching_and_ge_6():
    assert fu.check_math([6, 6])["crit"] is True
    assert fu.check_math([7, 7])["crit"] is True
    assert fu.check_math([12, 12])["crit"] is True
    assert fu.check_math([5, 5])["crit"] is False      # matching but < 6
    assert fu.check_math([6, 7])["crit"] is False      # >=6 but not matching


def test_fumble_is_double_one():
    assert fu.check_math([1, 1])["fumble"] is True
    assert fu.check_math([1, 2])["fumble"] is False
    assert fu.check_math([1, 1])["crit"] is False


def test_high_roll_and_total():
    o = fu.check_math([8, 10], modifier=3)
    assert o["hr"] == 10 and o["total"] == 21


def test_crit_auto_success_fumble_auto_fail_override_dl():
    assert fu.check_math([6, 6], dl=20)["success"] is True     # crit beats a high DL
    assert fu.check_math([1, 1], dl=2)["success"] is False     # fumble fails a met DL
    assert fu.check_math([10, 4], dl=10)["success"] is True
    assert fu.check_math([3, 4], dl=10)["success"] is False


# --------------------------------------------------------------- fu: affinity
def test_reduce_affinity_conflicts():
    assert fu.reduce_affinity(["vulnerable", "resistant"]) is None
    assert fu.reduce_affinity(["immune", "vulnerable"]) == "immune"
    assert fu.reduce_affinity(["absorb", "immune", "vulnerable"]) == "absorb"
    assert fu.reduce_affinity(["resistant"]) == "resistant"
    assert fu.reduce_affinity([]) is None


def test_affinity_delta_matrix():
    assert fu.affinity_delta(10, None) == -10
    assert fu.affinity_delta(10, "vulnerable") == -20
    assert fu.affinity_delta(11, "resistant") == -5     # half, rounded down
    assert fu.affinity_delta(10, "immune") == 0
    assert fu.affinity_delta(10, "absorb") == +10       # heals


# --------------------------------------------------------------- fu: statuses
def test_status_downgrade_cumulative_and_floor():
    statuses = F.load("statuses")
    base = {"DEX": 10, "INS": 8, "MIG": 6, "WLP": 8}
    assert fu.effective_attributes(base, [], statuses) == base
    assert fu.effective_attributes(base, ["slow"], statuses)["DEX"] == 8
    two = fu.effective_attributes(base, ["slow", "enraged"], statuses)
    assert two["DEX"] == 6 and two["INS"] == 6          # slow+enraged: DEX -2, INS -1
    floored = fu.effective_attributes({"DEX": 6, "INS": 6, "MIG": 6, "WLP": 6}, ["slow", "enraged"], statuses)
    assert floored["DEX"] == 6                           # cannot drop below d6


def test_crisis_helpers():
    assert fu.is_crisis(35, 35) is True
    assert fu.is_crisis(36, 35) is False
    assert fu.crisis_crossed(70, 30, 35) is True
    assert fu.crisis_crossed(30, 10, 35) is False        # already in crisis
    assert fu.crisis_crossed(40, 36, 35) is False


# ----------------------------------------------------------------- statgen
def test_base_scores_reproduce_book_formula():
    s = statgen.base_scores(5, [10, 8, 8, 6], order=["MIG", "DEX", "INS", "WLP"])
    assert s["attributes"]["MIG"] == 10
    assert s["max_hp"] == 60          # 2*5 + 5*10  (cf. Cutterpillar)
    assert s["max_mp"] == 35          # 5 + 5*6
    assert s["crisis"] == 30 and s["defense"] == 8 and s["magic_defense"] == 8


def test_damage_bonus_bands():
    assert statgen.base_scores(5, [8, 8, 8, 8])["damage_bonus"] == 0
    assert statgen.base_scores(20, [8, 8, 8, 8])["damage_bonus"] == 5
    assert statgen.base_scores(40, [8, 8, 8, 8])["damage_bonus"] == 10
    assert statgen.base_scores(60, [8, 8, 8, 8])["damage_bonus"] == 15


def test_elite_and_champion_scaling():
    base = statgen.base_scores(10, [10, 8, 10, 6], order=["DEX", "INS", "MIG", "WLP"])
    elite = statgen.apply_danger(base, "elite")
    assert elite["max_hp"] == base["max_hp"] * 2
    assert elite["turns_per_round"] == 2 and elite["initiative"] == base["initiative"] + 2
    champ = statgen.apply_danger(base, "champion", n=3)
    assert champ["max_hp"] == base["max_hp"] * 3
    assert champ["max_mp"] == base["max_mp"] * 2
    assert champ["turns_per_round"] == 3 and champ["initiative"] == base["initiative"] + 3


def test_villain_ultima_points():
    assert statgen.villain_ultima("minor") == 5
    assert statgen.villain_ultima("major") == 10
    assert statgen.villain_ultima("supreme") == 15


# ------------------------------------------------------------------- sheet
def test_camilla_worked_example():
    # Core p.~40: Camilla L5, MIG d6, WLP d8, Weaponmaster(+5 HP) + Orator(+5 MP) → 40 HP / 50 MP
    sc = sheet.pc_scores(5, {"DEX": 8, "INS": 8, "MIG": 6, "WLP": 8}, ["weaponmaster", "orator"])
    assert sc["max_hp"] == 40 and sc["max_mp"] == 50 and sc["crisis"] == 20


def test_pc_scores_without_classes():
    sc = sheet.pc_scores(5, {"DEX": 8, "INS": 10, "MIG": 8, "WLP": 6}, [])
    assert sc["max_hp"] == 5 + 5 * 8 and sc["max_mp"] == 5 + 5 * 6


def test_legality_accepts_legal_sheet():
    legal = {"name": "X", "level": 5,
             "classes": [{"name": "weaponmaster", "level": 3}, {"name": "orator", "level": 2}],
             "skills": [{"class": "weaponmaster", "key": "bladestorm", "name": "Bladestorm", "sl": 1},
                        {"class": "weaponmaster", "key": "melee_weapon_mastery", "name": "Melee Weapon Mastery", "sl": 2},
                        {"class": "orator", "key": "persuasive", "name": "Persuasive", "sl": 2}]}
    errs, _ = sheet.legality(legal)
    assert errs == []


def test_legality_flags_violations():
    bad = {"name": "Y", "level": 5,
           "classes": [{"name": "weaponmaster", "level": 11}],
           "skills": [{"class": "weaponmaster", "key": "bladestorm", "name": "Bladestorm", "sl": 9}]}
    errs, _ = sheet.legality(bad)
    assert any("out of 1..10" in e for e in errs)
    assert any("exceeds cap" in e for e in errs)
    assert any("≠ character level" in e for e in errs)
