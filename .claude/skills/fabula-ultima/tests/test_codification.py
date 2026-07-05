"""Tests for the codified generation / genre / bookkeeping layer (memo §§3–6).
All hermetic — no engine/dice dependency (the stochastic paths are exercised in the
scripted dry-run, not here)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import build_data as B
import fudata as F
import gen
import state as S
import tick

CLASS_KEYS = {c["key"] for c in F.load("classes")["entries"]}
DAMAGE_TYPES = {"physical", "air", "bolt", "dark", "earth", "fire", "ice", "light", "poison"}
THEME_KEYS = {"Personal", "Social", "Action", "Mystery", "Tension"}
ADVANCE_OPS = {"front_tick", "clock_tick", "project_tick", "reseed", "fabula_reconcile", "chaos_judge"}


# ---------------------------------------------------------------------- genre
def test_genre_is_complete_and_consistent():
    genres = F.load("genre")["genres"]
    assert {g["key"] for g in genres} == {"core", "high", "natural", "techno"}
    for g in genres:
        assert g["magic_level"] in {"none", "low", "medium", "high", "very_high"}
        assert g["tech_level"] in {"primitive", "low", "medium", "high", "very_high"}
        assert len(g["pillars"]) >= 3
        assert len(g["conflict_themes"]) >= 3
        for ck in g["featured_classes"]:
            assert ck in CLASS_KEYS, f"{g['key']}: featured class {ck}"
        for dt in g.get("damage_flavor", []):
            assert dt in DAMAGE_TYPES, f"{g['key']}: damage flavor {dt}"
        assert set(g["theme_weights"]) <= THEME_KEYS


# ----------------------------------------------------------------- subsystems
def test_subsystems_validate_and_use_known_ops():
    doc = F.load("subsystems")
    errs = B.validate(doc, B._schema("subsystems.schema.json"), "subsystems")
    assert errs == [], errs
    for row in doc["subsystems"]:
        assert row["advance"] in ADVANCE_OPS


# -------------------------------------------------------------- entity/front
def test_entity_schema_accepts_valid_and_rejects_bad():
    good = {"id": "villain.x", "kind": "villain", "name": "X", "level": 30,
            "attributes": {"DEX": 12, "INS": 8, "MIG": 6, "WLP": 6},
            "hp": 270, "ultima": 10, "affinities": {"dark": "resistant"}}
    assert B.validate(good, B._schema("entity.schema.json"), "e") == []
    bad = {"id": "x", "kind": "wizard", "name": "X", "attributes": {"DEX": 7}}  # bad kind + die
    assert B.validate(bad, B._schema("entity.schema.json"), "e")


def test_front_schema():
    f = {"id": "front.x", "kind": "front", "name": "X",
         "clock": {"size": 8, "filled": 0}, "telegraphs": ["a", "b"]}
    assert B.validate(f, B._schema("front.schema.json"), "f") == []


# ---------------------------------------------------------------- state store
def test_entity_roundtrip_isolated(tmp_path=None):
    d = tempfile.mkdtemp()
    old_e, old_f, old_s = S.ENTITIES, S.FRONTS, S.STATE
    S.ENTITIES = os.path.join(d, "entities"); S.FRONTS = os.path.join(d, "fronts")
    S.STATE = os.path.join(d, "state.json")
    try:
        e = {"id": "npc.tester", "kind": "npc", "name": "Tester", "want": "to be saved"}
        S.save_entity(e)
        back = S.load_entity("npc.tester")
        assert back == e
        assert "npc.tester" in S.load_state()["entities"]
    finally:
        S.ENTITIES, S.FRONTS, S.STATE = old_e, old_f, old_s


def test_resolve_target_precedence():
    rec, persist = S.resolve_target("drake")          # bestiary template → stateless
    assert rec and rec["name"] == "Drake" and persist is None
    assert S.resolve_target("definitely-not-a-thing") == (None, None)


# ------------------------------------------------------- pure generation math
def test_expand_pool_applies_genre_bias():
    entries = [{"min": 1, "max": 10, "value": "Mage, artificer"},
               {"min": 11, "max": 20, "value": "Farmer"}]
    plain = gen.expand_pool(entries, None)
    assert plain.count("Mage, artificer") == 10 and plain.count("Farmer") == 10
    biased = gen.expand_pool(entries, {"mage": 3})
    assert biased.count("Mage, artificer") == 30      # 10 span × 3 bias
    assert biased.count("Farmer") == 10               # unbiased


def test_target_stage_math():
    assert tick.target_stage(0, 8, 4) == 0
    assert tick.target_stage(4, 8, 4) == 2
    assert tick.target_stage(8, 8, 4) == 4
    assert tick.target_stage(2, 6, 3) == 1
    assert tick.target_stage(3, 0, 4) == 0            # guard div-by-zero
