#!/usr/bin/env python3
"""
merge_atlas.py — fold the staged Atlas mechanical content (data/atlas/staging/<atlas>/
{classes,heroic,spells}.json) into the core data files, tagging each merged record with
its `source` (high/natural/techno). Idempotent: records are deduped by `key`, so re-running
never double-adds. The Atlas *setting toolkit* stays in data/atlas/<atlas>.json (loaded
separately); only classes/spells/heroic skills are merged so sheet.py / lookup.py see them.

Usage: python3 scripts/merge_atlas.py [--dry-run]
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STAGE = os.path.join(DATA, "atlas", "staging")

# staging filename  ->  (core file, source-tag default)
TARGETS = {
    "classes.json": "classes.json",
    "heroic.json": "heroic_skills.json",
    "spells.json": "spells.json",
}


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv):
    dry = "--dry-run" in argv
    report = []
    for atlas_dir in sorted(glob.glob(os.path.join(STAGE, "*"))):
        atlas = os.path.basename(atlas_dir)
        for stage_name, core_name in TARGETS.items():
            sp = os.path.join(atlas_dir, stage_name)
            if not os.path.isfile(sp):
                continue
            stage = _load(sp)
            core_path = os.path.join(DATA, core_name)
            core = _load(core_path)
            have = {e.get("key") for e in core["entries"]}
            added = skipped = 0
            for e in stage.get("entries", []):
                e.setdefault("source", atlas)
                if e.get("key") in have:
                    skipped += 1
                    continue
                core["entries"].append(e)
                have.add(e.get("key"))
                added += 1
            report.append((atlas, stage_name, core_name, added, skipped))
            if not dry and added:
                with open(core_path, "w", encoding="utf-8") as fh:
                    json.dump(core, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    print(f"{'DRY-RUN ' if dry else ''}merge_atlas:")
    for atlas, stage, core, added, skipped in report:
        print(f"  {atlas:8} {stage:13} → {core:20} +{added} added, {skipped} already present")
    # final tallies
    for core_name in ("classes.json", "heroic_skills.json", "spells.json"):
        doc = _load(os.path.join(DATA, core_name))
        by_src = {}
        for e in doc["entries"]:
            by_src[e.get("source", "core")] = by_src.get(e.get("source", "core"), 0) + 1
        print(f"  {core_name}: {len(doc['entries'])} total  {by_src}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
