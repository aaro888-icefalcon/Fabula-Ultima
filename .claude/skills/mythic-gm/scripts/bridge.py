#!/usr/bin/env python3
"""
bridge.py — discover / validate / summarize a companion bridge.

A bridge is a folder with a bridge.md manifest (containing a fenced ```json block)
that declares which engine hooks the companion overrides and where its files are.
The engine reads the manifest at load and uses an override where present, else the
Mythic/AC default.

Commands:
  summary <bridge_dir>     Print overrides-vs-defaults for the 9 hooks (names only)
  brief <bridge_dir>       Print each overridden hook's OPERATIVE digest — the imperatives the
                           GM must hold in play. Boot loads THIS (not just summary). --markdown
                           emits a paste-ready block for the companion's always-loaded SKILL.md.
  validate <bridge_dir>    Check manifest + files exist; roll-test tables; warn when an overridden
                           hook has no surfaced imperative (enforcement gap)
  manifest <bridge_dir>    Print the parsed JSON manifest
"""
import json, os, re, sys, glob

HOOKS = ["resolve","generate:character","generate:element","meaning","chaos",
         "themes","world-tick","seeds","adventure-ingest"]

# hook -> (files-map key, default filename). The OPERATIVE digest of each overridden hook
# is what must reach always-on context; brief surfaces it, validate checks it exists.
HOOK_FILE = {
    "resolve":            ("system_profile", "system-profile.md"),
    "meaning":            ("interpretation", "interpretation.md"),
    "chaos":              ("chaos",          "chaos-tendency.md"),
    "themes":             ("themes",         "theme-weights.md"),
    "world-tick":         ("subsystems",     "subsystems.md"),
    "seeds":              ("seeds",          "seeds.md"),
    "generate:character": ("generators",     "generators/registry.md"),
    "generate:element":   ("generators",     "generators/registry.md"),
    "adventure-ingest":   ("adventures",     "adventures/"),
}

def hook_path(man, bdir, hook):
    key, default = HOOK_FILE.get(hook, (None, None))
    if not default: return None
    rel = (man.get("files", {}) or {}).get(key, default)
    return os.path.join(bdir, rel)

def extract_operative(path):
    """Return the lines of a '## Operative' section (the always-load imperative), or None."""
    if not path or not os.path.isfile(path): return None
    out, grab = [], False
    for ln in open(path, encoding="utf-8"):
        s = ln.strip()
        if s.startswith("## "):
            grab = s.lower().startswith("## operative"); continue
        if grab:
            if s.startswith("#"): break
            if s: out.append(s.rstrip())
    return out or None

def hook_digest(man, bdir, hook):
    """The operative digest for a hook: an explicit manifest 'digests' entry wins, else the
    file's '## Operative' section. Returns (lines, source_path_or_'manifest', ok)."""
    dg = (man.get("digests", {}) or {}).get(hook)
    if dg:
        return ([dg] if isinstance(dg, str) else list(dg)), "manifest digests", True
    p = hook_path(man, bdir, hook)
    lines = extract_operative(p)
    return (lines or []), (p or "—"), bool(lines)

def read_manifest(bdir):
    p = os.path.join(bdir, "bridge.md")
    if not os.path.exists(p): sys.exit(f"No bridge.md in {bdir}")
    txt = open(p, encoding="utf-8").read()
    m = re.search(r"```json\s*(\{.*?\})\s*```", txt, re.DOTALL)
    if not m: sys.exit("bridge.md has no ```json manifest block")
    try: return json.loads(m.group(1))
    except Exception as e: sys.exit(f"manifest JSON error: {e}")

def _manifest_safe(bdir):
    """read_manifest without exiting — returns {} when there's no usable bridge."""
    try: return read_manifest(bdir)
    except SystemExit: return {}

def char_gen(bdir):
    """Resolve the companion's NEW-character generation override, or None for the engine
    default (AC Character Crafter). Reads manifest.generators_map.character:
      {"mode": "replace"|"conjunction"|"default", "table": "generators/x.json", "note": "<lore>"}
    'replace' uses the companion generator INSTEAD of the AC Crafter; 'conjunction' uses BOTH;
    a bare note (no table) = lore-based generation the GM performs from setting-canon. Table
    paths are returned absolute. Only honored when 'generate:character' is in overrides."""
    if not bdir: return None
    man = _manifest_safe(bdir)
    if not man: return None
    gm = (man.get("generators_map") or {}).get("character")
    if not gm or "generate:character" not in man.get("overrides", []): return None
    out = dict(gm); out.setdefault("mode", "conjunction")
    if out.get("table"): out["table"] = os.path.join(bdir, out["table"])
    return out

def cmd_summary(bdir):
    man = read_manifest(bdir); ov = set(man.get("overrides", []))
    print(f"Companion: {man.get('companion','?')}   engine: {man.get('engine','?')}")
    for h in HOOKS:
        hit = h in ov or any(o.startswith("generate:") for o in ov) if h.startswith("generate:") else h in ov
        print(f"  {'OVERRIDE' if h in ov else 'default ':8}  {h}")

def cmd_brief(bdir, markdown=False):
    """Print the OPERATIVE digest of every overridden hook — the imperatives the GM must keep
    salient in play. This is what boot should load (summary names hooks; brief opens them)."""
    man = read_manifest(bdir); ov = man.get("overrides", [])
    if markdown:
        print(f"<!-- BRIDGE-BRIEF: {man.get('companion','companion')} — regenerate with "
              f"`bridge.py brief <dir> --markdown`; do not hand-edit -->")
        print(f"### Active bridge — operative rules ({man.get('companion','companion')})")
    else:
        print(f"📋 BRIDGE BRIEF — {man.get('companion','?')}  (operative rules, hold these in play)")
    missing = []
    for h in ov:
        lines, src, ok = hook_digest(man, bdir, h)
        if ok:
            if markdown:
                print(f"- **{h}** — " + " ".join(lines))
            else:
                print(f"\n▸ {h}:")
                for ln in lines: print(f"    {ln}")
        else:
            missing.append((h, src))
            (print(f"- **{h}** — ⚠ NO OPERATIVE DIGEST (add a '## Operative' block)") if markdown
             else print(f"\n▸ {h}:  ⚠ no '## Operative' block in {os.path.basename(src)} — this rule will NOT reach play."))
    if markdown: print("<!-- /BRIDGE-BRIEF -->")
    if missing and not markdown:
        print(f"\n  {len(missing)} hook(s) override the engine but surface no imperative — "
              "they’ll be silently ignored under load. Add '## Operative' blocks.")

def cmd_validate(bdir):
    man = read_manifest(bdir); problems = []; warnings = []
    for key, rel in man.get("files", {}).items():
        if not os.path.exists(os.path.join(bdir, rel)):
            problems.append(f"missing file '{rel}' (declared as {key})")
    for h in man.get("overrides", []):
        if h not in HOOKS and not h.startswith("generate:"):
            problems.append(f"unknown hook '{h}'")
    # roll-test any generator tables
    tested = 0
    for f in glob.glob(os.path.join(bdir, "generators", "*.json")):
        try:
            t = json.load(open(f))
            if t.get("type","").startswith("list_"):
                cov = sum(e["max"]-e["min"]+1 for e in t["entries"])
                need = 100 if t["type"]=="list_d100" else 10
                if cov != need: problems.append(f"{os.path.basename(f)}: coverage {cov}/{need}")
                tested += 1
        except Exception as e:
            problems.append(f"{os.path.basename(f)}: {e}")
    # ENFORCEMENT (fix E): every overridden hook must surface an operative imperative, or it
    # will never reach always-on context and the override will silently not fire in play.
    surfaced = 0
    for h in man.get("overrides", []):
        if h == "adventure-ingest": continue           # not a per-turn imperative
        _, src, ok = hook_digest(man, bdir, h)
        if ok: surfaced += 1
        else:
            warnings.append(f"hook '{h}' is overridden but has no '## Operative' digest "
                            f"({os.path.basename(src)}) — it won't reach play. Add one, and inline "
                            "`bridge.py brief` into the companion's always-loaded SKILL.md.")
    if problems:
        print("INVALID:"); [print("  X", p) for p in problems]
        [print("  ! ", w) for w in warnings]; sys.exit(1)
    print(f"Bridge valid ✓  ({len(man.get('overrides',[]))} overrides, {surfaced} with operative digests, "
          f"{tested} generator tables roll-tested)")
    if warnings:
        print("WARNINGS (enforcement gaps — overrides that won't fire in play):")
        [print("  ! ", w) for w in warnings]

def cmd_manifest(bdir):
    print(json.dumps(read_manifest(bdir), indent=2))

def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h","--help"): print(__doc__); return
    if len(a) < 2: sys.exit("Need a bridge directory.")
    if a[0] == "brief": cmd_brief(a[1], "--markdown" in a)
    elif a[0] in ("summary","validate","manifest"):
        {"summary":cmd_summary,"validate":cmd_validate,"manifest":cmd_manifest}[a[0]](a[1])
    else: sys.exit(f"Unknown command '{a[0]}'")

if __name__ == "__main__":
    main()
