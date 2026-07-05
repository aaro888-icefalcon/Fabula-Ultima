"""Data-fidelity checks over the extracted ruleset: canonical enums, cross-references,
and the bestiary's HP/MP formula invariant (extraction fidelity vs the book's math)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import fudata as F

DAMAGE_TYPES = {"physical", "air", "bolt", "dark", "earth", "fire", "ice", "light", "poison"}
STATUS_KEYS = {"dazed", "enraged", "poisoned", "shaken", "slow", "weak"}
SPECIES = {"beast", "construct", "demon", "elemental", "humanoid", "monster", "plant", "undead"}


# --------------------------------------------------------------------- damage
def test_damage_types_and_affinity_multipliers():
    d = F.load("damage")
    assert {t["key"] for t in d["types"]} == DAMAGE_TYPES
    mult = {a["key"]: a["multiplier"] for a in d["affinities"]}
    assert mult == {"vulnerable": 2, "resistant": 0.5, "immune": 0, "absorb": -1}


# --------------------------------------------------------------------- status
def test_status_downgrades_match_book():
    smap = {s["key"]: s["downgrades"] for s in F.load("statuses")["statuses"]}
    assert set(smap) == STATUS_KEYS
    assert smap["dazed"] == ["Insight"]
    assert sorted(smap["enraged"]) == ["Dexterity", "Insight"]
    assert sorted(smap["poisoned"]) == ["Might", "Willpower"]
    assert smap["shaken"] == ["Willpower"]
    assert smap["slow"] == ["Dexterity"]
    assert smap["weak"] == ["Might"]
    assert F.load("statuses")["floor_die"] == 6


# ---------------------------------------------------------------------- rules
def test_rules_core_constants():
    r = F.load("rules")
    assert sorted(x["dl"] for x in r["difficulty_levels"]) == [7, 10, 13, 16]
    assert len(r["opportunities"]) >= 11
    assert r["fabula_points"]["starting"] == 3
    assert r["zero_hp"]["surrender"] and r["zero_hp"]["sacrifice"]


# -------------------------------------------------------------------- classes
def test_every_class_skill_has_valid_cap_and_text():
    entries = F.load("classes")["entries"]
    assert len(entries) >= 15
    for c in entries:
        assert c["free_benefits"], f"{c['key']} has no free benefits"
        for sk in c["skills"]:
            assert isinstance(sk["sl_max"], int) and sk["sl_max"] >= 1, f"{c['key']}.{sk['key']}"
            assert sk["text"].strip(), f"{c['key']}.{sk['key']} empty text"


# --------------------------------------------------------------------- spells
def test_spell_damage_types_are_canonical():
    for s in F.load("spells")["entries"]:
        if s.get("damage_type"):
            assert s["damage_type"] in DAMAGE_TYPES, f"{s['key']}: {s['damage_type']}"


# ------------------------------------------------------------------ equipment
def test_weapon_damage_and_accuracy_are_canonical():
    for w in F.load("equipment")["weapons"]:
        assert w["damage"]["type"] in DAMAGE_TYPES, w["key"]
        for a in w["accuracy"]["attributes"]:
            assert a in {"DEX", "INS", "MIG", "WLP"}, w["key"]


# ------------------------------------------------------------------- bestiary
def test_bestiary_hp_mp_follow_the_design_formula():
    """Every soldier's HP = 2*level + 5*MIG + 10k, MP = level + 5*WLP + 10k (k>=0).
    The +10k slack is the Improved HP / Spellcaster NPC skills. Any other value
    signals an extraction error."""
    b = F.load_bestiary()
    assert len(b) >= 50
    for k, c in b.items():
        a = c["attributes"]
        dhp = c["hp"] - (2 * c["level"] + 5 * a["MIG"])
        dmp = c["mp"] - (c["level"] + 5 * a["WLP"])
        assert dhp >= 0 and dhp % 10 == 0, f"{k}: HP {c['hp']} off-formula by {dhp}"
        assert dmp >= 0 and dmp % 10 == 0, f"{k}: MP {c['mp']} off-formula by {dmp}"


def test_bestiary_species_affinities_and_crisis():
    b = F.load_bestiary()
    for k, c in b.items():
        assert c["species"] in SPECIES, k
        for dt in (c.get("affinities") or {}):
            assert dt in DAMAGE_TYPES, f"{k}: affinity key {dt}"
        for dt, aff in (c.get("affinities") or {}).items():
            assert aff in {"vulnerable", "resistant", "immune", "absorb"}, f"{k}: {aff}"
        if "crisis" in c:
            assert c["crisis"] == c["hp"] // 2, f"{k}: crisis {c['crisis']} != hp//2"


def test_specific_creatures_match_exactly():
    b = F.load_bestiary()
    exact = {"cutterpillar": (60, 10), "giant-rat": (40, 12), "grey-howler": (50, 10), "drake": (70, 10)}
    for key, (hp, defense) in exact.items():
        assert b[key]["hp"] == hp, key
        assert b[key]["defense"] == defense, key
