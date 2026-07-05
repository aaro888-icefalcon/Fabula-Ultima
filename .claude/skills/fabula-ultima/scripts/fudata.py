#!/usr/bin/env python3
"""
fudata.py — shared data + state layer for the fabula-ultima scripts.

- loads the data/*.json ruleset (rules, damage, statuses, classes, spells,
  equipment, npc_design, bestiary shards) with small fuzzy finders,
- reads/writes campaign state under campaign/ (points, clocks, sheets),
- provides a stdlib-only YAML *subset* good enough to round-trip our own
  character sheets (block maps, nested maps, block sequences of scalars or
  maps, and inline [flow] scalar lists). It is NOT a general YAML parser.

No randomness here — that all lives in engine.py.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CAMPAIGN = os.path.join(ROOT, "campaign")


# ------------------------------------------------------------------ data load
_CACHE = {}


def load(name):
    """Load data/<name>.json (cached)."""
    if name not in _CACHE:
        with open(os.path.join(DATA, name + ".json"), encoding="utf-8") as fh:
            _CACHE[name] = json.load(fh)
    return _CACHE[name]


def load_bestiary():
    """Merge all bestiary shards into {key: entry}."""
    if "_bestiary" not in _CACHE:
        idx = {}
        for f in sorted(glob.glob(os.path.join(DATA, "bestiary", "*.json"))):
            for e in json.load(open(f, encoding="utf-8")).get("entries", []):
                idx[e["key"]] = e
        _CACHE["_bestiary"] = idx
    return _CACHE["_bestiary"]


def _fuzzy(query, names):
    q = query.strip().lower()
    low = {n.lower(): n for n in names}
    if q in low:
        return low[q]
    for test in (lambda n: n.startswith(q), lambda n: q in n):
        hits = [orig for l, orig in low.items() if test(l)]
        if len(hits) == 1:
            return hits[0]
        if hits:
            return sorted(hits, key=len)[0]
    return None


def find(kind, query):
    """Find one record by fuzzy name/key. kind: creature|weapon|armor|shield|
    status|spell|class|npc_skill. Returns the dict or None."""
    if kind == "creature":
        idx = load_bestiary()
        m = _fuzzy(query, list(idx) + [v["name"] for v in idx.values()])
        if m in idx:
            return idx[m]
        for v in idx.values():
            if v["name"].lower() == (m or "").lower():
                return v
        return None
    tables = {
        "weapon": ("equipment", "weapons"),
        "armor": ("equipment", "armor"),
        "shield": ("equipment", "shields"),
        "status": ("statuses", "statuses"),
        "spell": ("spells", "entries"),
        "class": ("classes", "entries"),
        "npc_skill": ("npc_design", "npc_skills"),
    }
    if kind not in tables:
        raise ValueError(f"unknown kind {kind!r}")
    fname, key = tables[kind]
    rows = load(fname).get(key, [])
    by_key = {r.get("key", r.get("name")): r for r in rows}
    by_name = {r.get("name"): r for r in rows}
    m = _fuzzy(query, list(by_key) + list(by_name))
    return by_key.get(m) or by_name.get(m)


# --------------------------------------------------------------- campaign io
def _campaign_path(rel):
    return os.path.join(CAMPAIGN, rel)


def ensure_campaign():
    os.makedirs(os.path.join(CAMPAIGN, "sheets"), exist_ok=True)


def read_state(name, default):
    p = _campaign_path(name)
    if not os.path.isfile(p):
        return json.loads(json.dumps(default))
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def write_state(name, obj):
    ensure_campaign()
    with open(_campaign_path(name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# ------------------------------------------------------------- minimal YAML
def _scalar_out(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or any(c in s for c in ":#[]{},&*!|>'\"%@`") or s.strip() != s \
            or s.lower() in ("null", "true", "false", "yes", "no") or s[:1] in "-?":
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _flow_list_ok(v):
    return isinstance(v, list) and all(
        not isinstance(x, (list, dict)) for x in v)


def yaml_dump(obj, indent=0):
    """Emit our sheet-subset YAML."""
    pad = "  " * indent
    out = []
    if isinstance(obj, dict):
        if not obj:
            return pad + "{}\n"
        for k, v in obj.items():
            if isinstance(v, dict) and v:
                out.append(f"{pad}{k}:")
                out.append(yaml_dump(v, indent + 1).rstrip("\n"))
            elif isinstance(v, list) and v and not _flow_list_ok(v):
                out.append(f"{pad}{k}:")
                for item in v:
                    if isinstance(item, dict):
                        block = yaml_dump(item, indent + 1).rstrip("\n").split("\n")
                        first = block[0].strip()
                        out.append(f"{pad}  - {first}")
                        for ln in block[1:]:
                            out.append(f"{pad}    {ln.strip()}")
                    else:
                        out.append(f"{pad}  - {_scalar_out(item)}")
            elif isinstance(v, list) and _flow_list_ok(v):
                inner = ", ".join(_scalar_out(x) for x in v)
                out.append(f"{pad}{k}: [{inner}]")
            else:
                out.append(f"{pad}{k}: {_scalar_out(v)}")
    return "\n".join(out) + "\n"


def _scalar_in(s):
    s = s.strip()
    if s == "" or s == "~" or s.lower() == "null":
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar_in(x) for x in _split_flow(inner)] if inner else []
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def _split_flow(s):
    out, buf, q = [], "", None
    for c in s:
        if q:
            buf += c
            if c == q:
                q = None
        elif c in "\"'":
            q = c
            buf += c
        elif c == ",":
            out.append(buf)
            buf = ""
        else:
            buf += c
    if buf.strip():
        out.append(buf)
    return out


def yaml_load(text):
    """Parse our sheet-subset YAML into Python objects."""
    raw = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    lines = [(len(ln) - len(ln.lstrip(" ")), ln.strip()) for ln in raw]
    pos = [0]

    def parse(indent):
        if lines[pos[0]][1].startswith("- "):
            return parse_seq(indent)
        return parse_map(indent)

    def parse_map(indent):
        node = {}
        while pos[0] < len(lines):
            ind, content = lines[pos[0]]
            if ind < indent or content.startswith("- "):
                break
            if ind > indent:            # defensive: skip over-indented noise
                pos[0] += 1
                continue
            key, _, rest = content.partition(":")
            key = key.strip()
            rest = rest.strip()
            pos[0] += 1
            if rest == "":
                if pos[0] < len(lines) and lines[pos[0]][0] > indent:
                    node[key] = parse(lines[pos[0]][0])
                else:
                    node[key] = None
            else:
                node[key] = _scalar_in(rest)
        return node

    def parse_seq(indent):
        seq = []
        while pos[0] < len(lines):
            ind, content = lines[pos[0]]
            if ind < indent or not content.startswith("- "):
                break
            item = content[2:].strip()
            if ":" in item and not (item.startswith("[") or item.startswith('"')):
                # sequence of mappings: rewrite this line as a map line at ind+2
                lines[pos[0]] = (ind + 2, item)
                seq.append(parse_map(ind + 2))
            else:
                seq.append(_scalar_in(item))
                pos[0] += 1
        return seq

    return parse(0) if lines else {}


# --------------------------------------------------------------- sheet io
def sheet_path(name):
    return os.path.join(CAMPAIGN, "sheets", name.lower().replace(" ", "_") + ".yaml")


def load_sheet(name_or_path):
    p = name_or_path if os.path.isfile(name_or_path) else sheet_path(name_or_path)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return yaml_load(fh.read())


def save_sheet(sheet):
    ensure_campaign()
    p = sheet_path(sheet["name"])
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(yaml_dump(sheet))
    return p
