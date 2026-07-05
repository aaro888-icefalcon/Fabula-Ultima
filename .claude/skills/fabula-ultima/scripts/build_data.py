#!/usr/bin/env python3
"""
build_data.py — the extraction verifier for fabula-ultima's data/ tree.

Std-lib only. Two jobs:
  1. SCHEMA CHECK — validate every data/*.json against its data/schema/*.json using a
     pragmatic JSON-Schema subset (type/enum/const/required/properties/items/
     additionalProperties/minItems/minimum/maximum). Enough to catch extraction slips
     without pulling in a dependency.
  2. CROSS-REF — the checks a schema can't express: every damage type named by a
     weapon/spell/attack/affinity exists in damage.json; every class skill has a real
     SL cap; bestiary species & affinity keys are legal; generator tables cover their range.

Usage:
  build_data.py [--strict] [--root <skill_dir>]
    default: validate all data files that exist; PASS if none FAIL.
    --strict: additionally FAIL if an expected data file is missing (final-gate mode).

Exit 0 on success, 1 on any failure.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DAMAGE_TYPES = {"physical", "air", "bolt", "dark", "earth", "fire", "ice", "light", "poison"}
SPECIES = {"beast", "construct", "demon", "elemental", "humanoid", "monster", "plant", "undead"}

# data file (relative to data/) -> schema file (relative to data/schema/)
FILE_SCHEMA = {
    "rules.json": "rules.schema.json",
    "statuses.json": "statuses.schema.json",
    "damage.json": "damage.schema.json",
    "equipment.json": "equipment.schema.json",
    "classes.json": "classes.schema.json",
    "heroic_skills.json": "heroic_skills.schema.json",
    "spells.json": "spells.schema.json",
    "npc_design.json": "npc_design.schema.json",
    "worldgen.json": "worldgen.schema.json",
    "genre.json": "genre.schema.json",
    "subsystems.json": "subsystems.schema.json",
}
GLOB_SCHEMA = {           # directories whose every *.json shares one schema
    "bestiary/*.json": "bestiary.schema.json",
    "atlas/*.json": "atlas.schema.json",
}


# --------------------------------------------------------------- schema subset
def _type_ok(inst, t):
    if isinstance(t, list):
        return any(_type_ok(inst, x) for x in t)
    if t == "object":
        return isinstance(inst, dict)
    if t == "array":
        return isinstance(inst, list)
    if t == "string":
        return isinstance(inst, str)
    if t == "integer":
        return isinstance(inst, int) and not isinstance(inst, bool)
    if t == "number":
        return isinstance(inst, (int, float)) and not isinstance(inst, bool)
    if t == "boolean":
        return isinstance(inst, bool)
    if t == "null":
        return inst is None
    return True


def validate(inst, schema, path="$"):
    """Return a list of human-readable error strings (empty == valid)."""
    errs = []
    if "type" in schema and not _type_ok(inst, schema["type"]):
        errs.append(f"{path}: expected type {schema['type']}, got {type(inst).__name__}")
        return errs                      # a wrong container type makes deeper checks noise
    if "const" in schema and inst != schema["const"]:
        errs.append(f"{path}: expected const {schema['const']!r}, got {inst!r}")
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: {inst!r} not in enum {schema['enum']}")

    if isinstance(inst, dict):
        for req in schema.get("required", []):
            if req not in inst:
                errs.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        addl = schema.get("additionalProperties", True)
        for k, v in inst.items():
            if k in props:
                errs += validate(v, props[k], f"{path}.{k}")
            elif isinstance(addl, dict):
                errs += validate(v, addl, f"{path}.{k}")
            elif addl is False:
                errs.append(f"{path}.{k}: additional property not allowed")

    if isinstance(inst, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for i, it in enumerate(inst):
                errs += validate(it, items, f"{path}[{i}]")
        if "minItems" in schema and len(inst) < schema["minItems"]:
            errs.append(f"{path}: needs >= {schema['minItems']} items, has {len(inst)}")

    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            errs.append(f"{path}: {inst} < minimum {schema['minimum']}")
        if "maximum" in schema and inst > schema["maximum"]:
            errs.append(f"{path}: {inst} > maximum {schema['maximum']}")
    return errs


# ------------------------------------------------------------------- helpers
def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _schema(name):
    return _load(os.path.join(ROOT, "data", "schema", name))


def _data_path(rel):
    return os.path.join(ROOT, "data", rel)


# ------------------------------------------------------------------- cross-ref
def cross_ref(present):
    """`present` maps data-rel-name -> parsed json (only files that exist). Returns
    (errors, warnings)."""
    errs, warns = [], []

    dmg_types = set(DAMAGE_TYPES)
    if "damage.json" in present:
        dmg_types = {t["key"] for t in present["damage.json"].get("types", [])}
        if dmg_types != DAMAGE_TYPES:
            warns.append(f"damage.json types {sorted(dmg_types)} differ from the canonical 9")

    class_keys = set()
    if "classes.json" in present:
        for c in present["classes.json"].get("entries", []):
            class_keys.add(c.get("key"))
            for sk in c.get("skills", []):
                if not isinstance(sk.get("sl_max"), int) or sk.get("sl_max", 0) < 1:
                    errs.append(f"classes.json: {c.get('key')}.{sk.get('key')} has bad sl_max {sk.get('sl_max')!r}")

    if "equipment.json" in present:
        for w in present["equipment.json"].get("weapons", []):
            dt = (w.get("damage") or {}).get("type")
            if dt and dt not in dmg_types:
                errs.append(f"equipment.json: weapon {w.get('key')} damage type '{dt}' not in damage types")

    if "spells.json" in present:
        for s in present["spells.json"].get("entries", []):
            dt = s.get("damage_type")
            if dt and dt not in dmg_types:
                errs.append(f"spells.json: spell {s.get('key')} damage_type '{dt}' not in damage types")
            if class_keys and s.get("class") and s["class"] not in class_keys:
                warns.append(f"spells.json: spell {s.get('key')} class '{s['class']}' has no matching class entry")

    if "heroic_skills.json" in present and class_keys:
        for h in present["heroic_skills.json"].get("entries", []):
            c = h.get("class")
            if c and c not in class_keys and c != "general":
                warns.append(f"heroic_skills.json: {h.get('key')} class '{c}' has no matching class entry")

    if "genre.json" in present and class_keys:
        for g in present["genre.json"].get("genres", []):
            for ck in g.get("featured_classes", []):
                if ck not in class_keys:
                    errs.append(f"genre.json: {g['key']} featured_class '{ck}' has no matching class entry")

    # bestiary shards
    for rel, doc in present.items():
        if not rel.startswith("bestiary/"):
            continue
        for e in doc.get("entries", []):
            if e.get("species") not in SPECIES:
                errs.append(f"{rel}: {e.get('key')} species '{e.get('species')}' invalid")
            for k in (e.get("affinities") or {}):
                if k not in dmg_types:
                    errs.append(f"{rel}: {e.get('key')} affinity key '{k}' is not a damage type")
    return errs, warns


def generator_coverage():
    """Range-check any bridge/generators/*.json list tables (d100/d10 fully covered)."""
    errs = []
    for f in glob.glob(os.path.join(ROOT, "bridge", "generators", "*.json")):
        try:
            t = _load(f)
        except Exception as e:
            errs.append(f"{os.path.basename(f)}: unreadable ({e})")
            continue
        typ = t.get("type", "")
        if typ.startswith("list_"):
            need = 100 if typ == "list_d100" else 10
            cov = sum(e["max"] - e["min"] + 1 for e in t.get("entries", []))
            if cov != need:
                errs.append(f"{os.path.basename(f)}: coverage {cov}/{need}")
    return errs


# ------------------------------------------------------------------- main
def main(argv):
    strict = "--strict" in argv
    fails, warns, checked, missing = [], [], 0, []
    present = {}

    targets = list(FILE_SCHEMA.items())
    for pattern, schema_name in GLOB_SCHEMA.items():
        for p in sorted(glob.glob(_data_path(pattern))):
            rel = os.path.relpath(p, _data_path("."))
            targets.append((rel, schema_name))

    for rel, schema_name in targets:
        p = _data_path(rel)
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        try:
            doc = _load(p)
        except Exception as e:
            fails.append(f"{rel}: invalid JSON — {e}")
            continue
        present[rel] = doc
        errs = validate(doc, _schema(schema_name), f"{rel}")
        checked += 1
        if errs:
            fails.append(f"{rel}: {len(errs)} schema error(s):")
            fails += [f"    - {e}" for e in errs[:40]]

    xerrs, xwarns = cross_ref(present)
    fails += xerrs
    warns += xwarns
    fails += generator_coverage()

    print(f"build_data: {checked} data file(s) validated", end="")
    if missing:
        print(f", {len(missing)} not yet extracted ({', '.join(missing)})")
    else:
        print()

    for w in warns:
        print("  ! ", w)

    if strict and missing:
        fails.append(f"--strict: {len(missing)} expected data file(s) missing: {', '.join(missing)}")

    if fails:
        print("\nFAIL ✗")
        for f in fails:
            print(" ", f)
        return 1
    print("PASS ✓" + (f"  ({len(warns)} warning(s))" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
