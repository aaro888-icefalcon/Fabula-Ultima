#!/usr/bin/env python3
"""
build_data.py — derive verified, machine-rollable JSON tables from the bundled
canon Markdown (references/canon/*.md). Single source of truth = the Markdown.
Emits data/**/*.json + manifest.json and runs a verification gate.

Run:  python3 scripts/build_data.py
"""
import json, os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CANON = os.path.join(ROOT, "references", "canon")
DATA = os.path.join(ROOT, "data")
MYTHIC = open(os.path.join(CANON, "Mythic-GME.md"), encoding="utf-8").read()
AC = open(os.path.join(CANON, "The-Adventure-Crafter.md"), encoding="utf-8").read()

errors, warnings, built = [], [], []
def err(m): errors.append(m)
def warn(m): warnings.append(m)
def sha(s): return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
def L(t): return t.split("\n")

def write(relpath, obj):
    p = os.path.join(DATA, relpath)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    built.append(relpath)

# ---------------------------------------------------------------- Fate Chart
ODDS = ["Certain","Nearly Certain","Very Likely","Likely","50/50",
        "Unlikely","Very Unlikely","Nearly Impossible","Impossible"]
def parse_fate_chart():
    lines = L(MYTHIC); grid = {}
    for i, ln in enumerate(lines):
        if ln.strip() == "FATE CHART" and i+1 < len(lines) and lines[i+1].strip().startswith("Certain"):
            for label in ODDS:
                row = next((r for r in lines[i:i+14] if r.strip().startswith(label+" ") and re.search(r"\d", r)), None)
                if not row: err(f"fate_chart missing {label}"); continue
                vals = [0 if t.upper()=="X" else int(t) for t in row.strip()[len(label):].split()]
                if len(vals) != 27: err(f"fate_chart {label}: {len(vals)} vals"); continue
                grid[label] = [{"exc_yes_max":vals[c*3],"yes_max":vals[c*3+1],
                                "exc_no_min":vals[c*3+2] or 101} for c in range(9)]
            break
    if len(grid)==9:
        write("mythic/fate_chart.json",{"id":"mythic.fate_chart","title":"Fate Chart","type":"grid_fate_chart",
            "dice":"1d100","source":"references/canon/Mythic-GME.md#fate-chart","odds":ODDS,
            "chaos_factor":list(range(1,10)),"grid":grid,"checksum":sha(str(grid))})
    return grid

# --------------------------------------------- generic code-block range table
def parse_range_block(text, title):
    lines = L(text)
    for i, ln in enumerate(lines):
        if ln.strip() == title:
            entries = []
            for r in lines[i+1:i+45]:
                if r.strip()=="```" and entries: break
                if r.strip() in ("```","") or "RESULT" in r.upper() or r.strip().startswith("1d"): continue
                m = re.match(r"^\s*(\d+)\s*[-–]\s*(\d+)\s+(.+?)\s*$", r) or re.match(r"^\s*(\d+)\s+([A-Za-z].+?)\s*$", r)
                if not m:
                    if entries: break
                    continue
                if m.lastindex==3: entries.append({"min":int(m.group(1)),"max":int(m.group(2)),"value":m.group(3).strip()})
                else: entries.append({"min":int(m.group(1)),"max":int(m.group(1)),"value":m.group(2).strip()})
            return entries
    return None

def build_range(title, relpath, tid, total, dice, anchor):
    e = parse_range_block(MYTHIC, title)
    if not e: err(f"{tid}: not parsed"); return
    cov = sum(x["max"]-x["min"]+1 for x in e)
    if cov != total: err(f"{tid}: coverage {cov}/{total}")
    write(relpath, {"id":tid,"title":title.title(),"type":"list_d%d"%(100 if total==100 else 10),
        "dice":dice,"source":f"references/canon/Mythic-GME.md#{anchor}","entries":e,"checksum":sha(str(e))})

# --------------------------------------------------- Meaning: Actions/Descriptors
def parse_meaning(name, header_idx):
    lines = L(MYTHIC); pairs = {}
    for r in lines[header_idx: header_idx+30]:
        if "|" not in r:
            if pairs: break
            continue
        flat = r.replace("|"," ")
        for m in re.finditer(r"\*\*(\d+):\*\*\s*([A-Za-z][A-Za-z /'\-]*)", flat):
            n=int(m.group(1)); w=m.group(2).strip()
            if 1<=n<=100 and w: pairs.setdefault(n,w)
    if len(pairs)!=100: warn(f"meaning {name}: {len(pairs)}/100")
    entries=[{"min":n,"max":n,"value":pairs[n]} for n in sorted(pairs)]
    write(f"mythic/meaning_{name}.json",{"id":f"mythic.meaning.{name}","title":f"Meaning — {name}",
        "type":"list_d100","dice":"1d100","source":f"references/canon/Mythic-GME.md","entries":entries,
        "complete":len(pairs)==100,"checksum":sha(str(entries))})
    return len(pairs)

# ------------------------------------------------- Meaning: 45 Elements tables
def slug(name): return re.sub(r"[^a-z0-9]+","_",name.lower()).strip("_")

# The Character Identity/Motivations/Personality block is badly line-wrapped in the PDF.
# Recover it by flattening each printing and assigning pairs by column (mod 6), then fill the
# handful of values the wrap mangles (read directly from canon).
CHAR_FILLS = {
    "character_identity":    {17:"Crafter", 26:"Enforcer", 33:"Farmer"},
    "character_motivations": {18:"Diminish", 23:"Escape"},
    "character_personality": {17:"Calm", 28:"Creative", 33:"Devoted", 34:"Disagreeable", 39:"Fastidious", 68:"Optimistic"},
}
def build_character_triple():
    names = ["character_identity","character_motivations","character_personality"]
    merged = {n:{} for n in names}
    lines = L(MYTHIC)
    anchors = [i for i,ln in enumerate(lines)
               if "|" in ln and all(k in ln.upper() for k in ("IDENTITY","MOTIVATIONS","PERSONALITY"))]
    # multiple overlapping windows per printing: a misalignment in one is corrected by another
    for a in anchors:
        for (s, e) in [(a, a+109), (a, a+84), (a+24, a+109), (a, a+115), (a, a+75)]:
            flat = " ".join(lines[s:e]).replace("|"," ")
            for k,(nv,w) in enumerate(re.findall(r"\*\*(\d+):\*\*\s*([A-Za-z][A-Za-z /'\-]*)", flat)):
                c = (k % 6)//2; n = int(nv)
                if 0 <= c < 3 and 1 <= n <= 100: merged[names[c]].setdefault(n, w.strip())
    out = []
    for n in names:
        merged[n].update(CHAR_FILLS[n])
        if len(merged[n]) == 100:
            entries = [{"min":i,"max":i,"value":merged[n][i]} for i in range(1,101)]
            write(f"mythic/elements/{n}.json",{"id":f"mythic.elements.{n}",
                "title":f"Elements — {n.replace('_',' ').title()}","type":"list_d100","dice":"1d100",
                "source":"references/canon/Mythic-GME.md#meaning-tables-elements","entries":entries,
                "checksum":sha(str(entries))})
            out.append(n)
        else:
            err(f"{n}: {len(merged[n])}/100 after fills")
    return out
def parse_elements():
    """Elements tables are side-by-side 2-column (1-50/51-100) blocks. A 'names row'
    has bold tokens grouped by empty cells; each data row has 2 number:word pairs per table."""
    lines = L(MYTHIC)
    region = lines        # scan the whole book; MERGE each table across all reprints (fills page-break gaps)
    tables = {}                 # name -> {n: word}
    order = []
    cur_tokens = []             # raw bold tokens from the last names row (in column order)
    POLLUTE = ("MEANING","TABLES","ELEMENTS","DESCRIPTIONS","TRIGGER","EVENT","SCENE","COUNT","ROLL","RESULT","FATE","CHAOS","THREADS","LIST")
    def even_split(tokens, n):
        if n <= 0 or not tokens: return []
        base, extra = divmod(len(tokens), n)
        out, i = [], 0
        for k in range(n):
            size = base + (1 if k < extra else 0)
            out.append(" ".join(tokens[i:i+size]) if size else f"table_{k+1}"); i += size
        return out
    ALLOW = {"characters","character_actions_combat","character_actions_general","character_appearance",
        "character_background","character_conversations","character_descriptors","character_identity",
        "character_motivations","character_personality","character_skills","character_traits_flaws",
        "locations","objects","adventure_tone","alien_species_descriptors","animal_actions",
        "army_descriptors","cavern_descriptors","city_descriptors","civilization_descriptors",
        "creature_abilities","creature_descriptors","cryptic_message","curses","domicile_descriptors",
        "dungeon_descriptors","dungeon_traps","forest_descriptors","gods","legends","magic_item_descriptors",
        "mutation_descriptors","names","noble_house","plot_twists","powers","scavenging","smells","sounds",
        "spell_effects","starship_descriptors","terrain_descriptors","undead_descriptors","visions_dreams"}
    allow_seqs = sorted([(s.split("_"), s) for s in ALLOW], key=lambda x: -len(x[0]))
    def resolve_names(tokens, num):
        # greedy-match the names row against the canonical 45 (handles run-together page-break headers)
        words = []
        for t in tokens: words += re.findall(r"[a-z]+", t.lower())
        names, i = [], 0
        while i < len(words):
            hit = None
            for seq, s in allow_seqs:
                if words[i:i+len(seq)] == seq: hit = s; i += len(seq); break
            if hit: names.append(hit)
            else: i += 1
        return names if len(names) == num else even_split(tokens, num)
    for ln in region:
        if "|" not in ln:
            continue            # prose / page-header interruption — keep the current block's table set
        has_num = bool(re.search(r"\*\*\d+:\*\*", ln))
        if not has_num:
            toks = [m.group(1).strip() for m in re.finditer(r"\*\*([A-Za-z][A-Za-z &,'/-]*)\*\*", ln)]
            toks = [t for t in toks if not any(s in t.upper() for s in POLLUTE)]
            if toks: cur_tokens = toks
            continue
        # data row: derive the table count from the data itself, then label from tokens
        if not cur_tokens: continue
        flat = ln.replace("|"," ")
        prs = re.findall(r"\*\*(\d+):\*\*\s*([A-Za-z][A-Za-z /'\-]*)", flat)
        if len(prs) < 2 or len(prs) % 2: continue
        num = len(prs) // 2
        names = resolve_names(cur_tokens, num)
        for ti, nm in enumerate(names):
            if nm not in tables: tables[nm] = {}; order.append(nm)
            for (numv, word) in (prs[2*ti], prs[2*ti+1]):
                n = int(numv); w = word.strip()
                if 1 <= n <= 100 and w: tables[nm].setdefault(n, w)
    # ALLOW (the canonical 45) is defined above and drives both name-resolution and the write filter.
    complete=[]; missing=[]
    written=set()
    for nm in order:
        d = tables[nm]; s = slug(nm)
        if s in ALLOW and len(d) == 100 and s not in written:
            entries=[{"min":n,"max":n,"value":d[n]} for n in sorted(d)]
            write(f"mythic/elements/{s}.json",{"id":f"mythic.elements.{s}",
                "title":f"Elements — {nm.title()}","type":"list_d100","dice":"1d100",
                "source":"references/canon/Mythic-GME.md#meaning-tables-elements","entries":entries,
                "checksum":sha(str(entries))})
            complete.append(s); written.add(s)
    complete += build_character_triple()          # the 3 page-wrapped character tables
    written |= set(complete)
    missing = sorted(ALLOW - written)
    partial = [(m, 0) for m in missing]
    # index of element tables for the engine (all 45 should be hard-coded now)
    write("mythic/elements/_index.json",{"id":"mythic.elements.index","hardcoded":sorted(set(complete)),
        "canon_fallback":missing,"count_hardcoded":len(set(complete)),"count_total":len(set(complete))+len(missing)})
    return complete, partial

# ----------------------------------------- small hand-verified structured tables
def build_static():
    write("mythic/fate_check.json",{"id":"mythic.fate_check","title":"Fate Check (2d10)","type":"modifier_lookup",
        "dice":"2d10","source":"references/canon/Mythic-GME.md#the-fate-check",
        "odds_mod":{"Certain":5,"Nearly Certain":4,"Very Likely":2,"Likely":1,"50/50":0,"Unlikely":-1,
                    "Very Unlikely":-2,"Nearly Impossible":-4,"Impossible":-5},
        "cf_mod":{str(c):m for c,m in zip(range(9,0,-1),[5,4,2,1,0,-1,-2,-4,-5])},
        "answers":[{"min":18,"max":20,"value":"Exceptional Yes"},{"min":11,"max":17,"value":"Yes"},
                   {"min":5,"max":10,"value":"No"},{"min":2,"max":4,"value":"Exceptional No"}]})
    for tid,title,ans in [
      ("npc_behavior","NPC Behavior Table",{"yes":"The NPC does what you expect, or continues their ongoing action.",
        "no":"The NPC does the next most expected behavior. If unsure, roll a Meaning Table.",
        "exc_yes":"The expected/ongoing action with greater intensity.",
        "exc_no":"The opposite of what you expected, or the next-expected behavior intensified. If unsure, roll a Meaning Table and intensify.",
        "random_event":"Roll a Meaning Table for an additional action from the NPC."}),
      ("npc_statistics","NPC Statistics Table",{"yes":"The value is what you expect.","exc_yes":"About 25% higher.",
        "no":"About 25% lower.","exc_no":"About 50% lower.","random_event":"A special condition tied to this statistic."}),
      ("discovery_fate_question","Discovery Fate Question",{"yes":"Roll on the Thread Discovery Check Table.",
        "no":"Nothing useful is found.","exc_yes":"Roll twice on the Thread Discovery Check Table, combining results.",
        "exc_no":"Nothing found; no further Discovery Check this Scene."})]:
        write(f"mythic/{tid}.json",{"id":f"mythic.{tid}","title":title,"type":"answer_keyed",
            "source":"references/canon/Mythic-GME.md","answers":ans})
    write("mythic/scene_test.json",{"id":"mythic.scene_test","title":"Testing the Expected Scene","type":"logic",
        "dice":"1d10","source":"references/canon/Mythic-GME.md#testing-the-expected-scene",
        "rule":{"over_cf":"Expected Scene","within_cf_odd":"Altered Scene","within_cf_even":"Interrupt Scene"}})

# --------------------------------------------------- Adventure Crafter tables
def build_ac():
    # Plot Point Theme Table (1d10 -> priority slot)
    write("adventure_crafter/plot_point_theme.json",{"id":"ac.plot_point_theme","title":"Plot Point Theme Table",
        "type":"list_d10","dice":"1d10","source":"references/canon/The-Adventure-Crafter.md#plot-point-theme-table",
        "entries":[{"min":1,"max":4,"value":"First Priority"},{"min":5,"max":7,"value":"Second Priority"},
                   {"min":8,"max":9,"value":"Third Priority"},{"min":10,"max":10,"value":"Fourth Priority (cycle to Fifth)"}]})
    # Random Themes Table (1d10) — uniform default; RPG style can reweight at runtime
    THEMES=["Action","Tension","Mystery","Social","Personal"]
    write("adventure_crafter/random_themes.json",{"id":"ac.random_themes","title":"Random Themes Table",
        "type":"list_d10","dice":"1d10","source":"references/canon/The-Adventure-Crafter.md#random-themes-table",
        "entries":[{"min":2*i+1,"max":2*i+2,"value":THEMES[i]} for i in range(5)],"themes":THEMES})
    # Theme translation (Mythic -> AC), default genre weight presets
    write("adventure_crafter/themes.json",{"id":"ac.themes","title":"Adventure Crafter Themes","type":"reference",
        "source":"references/canon/The-Adventure-Crafter.md#themes","themes":THEMES,
        "theme_translation":{"Action":"Action","Horror":"Tension","Mystery":"Mystery","Social":"Social",
                             "Personal":"Personal","Tension":"Tension"},
        "style_weights":{"action":{"Action":4,"Tension":2,"Mystery":1,"Social":1,"Personal":1},
            "horror":{"Tension":4,"Mystery":2,"Personal":2,"Action":1,"Social":1},
            "mystery":{"Mystery":4,"Tension":2,"Social":1,"Personal":1,"Action":1},
            "intrigue":{"Social":4,"Personal":2,"Mystery":2,"Tension":1,"Action":1},
            "drama":{"Personal":3,"Social":3,"Tension":1,"Mystery":1,"Action":1},
            "balanced":{t:1 for t in THEMES}}})
    # Plot Point Table — mechanical structure hard-coded; specific titles read from canon.
    write("adventure_crafter/plot_point_structure.json",{"id":"ac.plot_point_structure",
        "title":"Plot Point Table — structure","type":"themed_d100","dice":"3d10",
        "source":"references/canon/The-Adventure-Crafter.md#plot-points-table",
        "note":"Roll the theme (plot_point_theme), then 1d100 in that theme's column; read the title from canon.",
        "universal":{ "conclusion":{"min":1,"max":8,"value":"Conclusion (ends the Thread if an Advancement)"},
            "none":{"min":9,"max":24,"value":"None (no Plot Point this slot)"},
            "meta":{"min":96,"max":100,"value":"Roll on the Meta Plot Points Table"}},
        "themes":THEMES})
    # Character Special Trait (AC) — hand-encoded from canon p.49
    write("adventure_crafter/character_special_trait.json",{"id":"ac.character_special_trait",
        "title":"Character Special Trait","type":"list_d100","dice":"1d100",
        "source":"references/canon/The-Adventure-Crafter.md#character-special-trait",
        "entries":[
            {"min":1,"max":50,"value":"The Character is an Individual"},
            {"min":51,"max":57,"value":"The Character is an Organization"},
            {"min":58,"max":64,"value":"The Character is an Object"},
            {"min":65,"max":71,"value":"Connected to this Thread"},
            {"min":72,"max":78,"value":"Not Connected to this Thread"},
            {"min":79,"max":85,"value":"Assists in Resolving this Thread"},
            {"min":86,"max":92,"value":"Hinders Resolving this Thread"},
            {"min":93,"max":100,"value":"Connected to an Existing Character (roll on Characters List; New→Choose Most Logical)"}]})

# --------------------------------------- Adventure Crafter Plot Point Table (183)
def build_plot_points():
    """Built from the hand-transcribed, verified table in scripts/_plot_points_data.py
    (the PDF prints it as wrapped two-column text that won't scrape losslessly). Each
    Theme column is checked for exact 25-95 coverage; structural ranges are added here."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ppd", os.path.join(HERE, "_plot_points_data.py"))
    ppd = importlib.util.module_from_spec(spec); spec.loader.exec_module(ppd)
    THEMES = ["Action","Tension","Mystery","Social","Personal"]   # canon column order ACT TEN MYS SOC PER
    def rng(s):
        if s == "-": return None
        a, b = (s.split("-")+[None])[:2]; return int(a), int(b if b is not None else a)
    tt = {t: {} for t in THEMES}
    for row in ppd.PLOT_POINTS:
        name = row[0]
        for ci, t in enumerate(THEMES):
            r = rng(row[ci+1])
            if not r: continue
            for n in range(r[0], r[1]+1):
                if n in tt[t]: err(f"plot_points {t}: {n} dup ({tt[t][n]} / {name})")
                tt[t][n] = name
    for t in THEMES:
        d = tt[t]
        body_gap = [n for n in range(25, 96) if n not in d]
        if body_gap: err(f"plot_points {t}: gaps {body_gap[:8]}")
        for n in range(1, 9):    d[n] = "Conclusion (ends the Thread if an Advancement)"
        for n in range(9, 25):   d[n] = "None"
        for n in range(96, 101): d[n] = "Roll on the Meta Plot Points Table"
        entries = []; n = 1
        while n <= 100:
            v = d.get(n); j = n
            while j+1 <= 100 and d.get(j+1) == v: j += 1
            e = {"min": n, "max": j, "value": v}
            if v in ppd.CHAR_PLOT_POINTS: e["char"] = True   # invokes the Characters List
            entries.append(e); n = j+1
        write(f"adventure_crafter/plot_points_{t.lower()}.json", {"id": f"ac.plot_points.{t.lower()}",
            "title": f"Plot Point Table — {t}", "type": "list_d100", "dice": "1d100",
            "source": "references/canon/The-Adventure-Crafter.md#plot-points-table", "entries": entries,
            "note": "1-8 Conclusion (if advancement); 9-24 None; 96-100 Meta. Names hand-verified from canon. "
                    "entries with char=true invoke the Characters List.",
            "checksum": sha(str(entries))})

# ------------------------------------------- Meta Plot Points Table (hard-coded)
def build_meta_plot_points():
    """The 96-100 "Meta Plot Point" sub-table (The Adventure Crafter p.~). Each result
    edits the Characters List or combines Threads. Ranges are contiguous 1-100, verbatim."""
    entries = [
        {"min":1,  "max":18, "value":"Character Exits The Adventure",
         "effect":"A Character active in the adventure leaves it. Roll the Characters List to pick who (New→Choose Most Logical); remove ALL their lines."},
        {"min":19, "max":27, "value":"Character Returns",
         "effect":"A Character who previously exited the adventure comes back. Re-add them to the Characters List (weight 1)."},
        {"min":28, "max":36, "value":"Character Steps Up",
         "effect":"A Character becomes more important/active. Add one extra line (raise weight, max 3). Roll the Characters List for who."},
        {"min":37, "max":55, "value":"Character Steps Down",
         "effect":"A Character becomes less important/active. Remove one line (lower weight; if it hits 0, they exit). Roll the Characters List for who."},
        {"min":56, "max":73, "value":"Character Downgrade",
         "effect":"A Character is weakened in power, status, or capability (but stays in the adventure). Roll the Characters List for who."},
        {"min":74, "max":82, "value":"Character Upgrade",
         "effect":"A Character is strengthened in power, status, or capability. Roll the Characters List for who."},
        {"min":83, "max":100,"value":"Thread Combo",
         "effect":"Two Threads merge or are revealed connected. Roll the Threads List twice (New→Choose Most Logical) and combine those Threads into one."}]
    for e in entries:                              # every Meta result but Thread Combo invokes a Character
        e["char"] = not e["value"].startswith("Thread")
        if e["value"].startswith("Thread"): e["thread2"] = True
    cov = sum(e["max"]-e["min"]+1 for e in entries)
    if cov != 100: err(f"meta_plot_points: coverage {cov}/100")
    write("adventure_crafter/meta_plot_points.json",{"id":"ac.meta_plot_points",
        "title":"Meta Plot Points Table","type":"list_d100","dice":"1d100",
        "source":"references/canon/The-Adventure-Crafter.md#meta-plot-points-table",
        "note":"Rolled when a Plot Point lands 96-100. Alters the Characters List or combines Threads.",
        "entries":entries,"checksum":sha(str(entries))})

# ---------------------------------------------------------------- verification
def verify(fate):
    try:
        if fate["50/50"][4]!={"exc_yes_max":10,"yes_max":50,"exc_no_min":91}:
            err(f"SPOT fate 50/50@CF5={fate['50/50'][4]}")
    except Exception as e: err(f"SPOT fate:{e}")
    try:
        ef=json.load(open(os.path.join(DATA,"mythic/event_focus.json")))
        if not any(x["min"]==21 and "NPC Action" in x["value"] for x in ef["entries"]): err("SPOT event_focus 21")
    except Exception as e: err(f"SPOT event_focus:{e}")
    try:
        a1=json.load(open(os.path.join(DATA,"mythic/meaning_actions_1.json")))
        if a1["entries"][0]["value"]!="Abandon": err(f"SPOT actions_1#1={a1['entries'][0]}")
    except Exception as e: err(f"SPOT actions_1:{e}")
    # ranges contiguous check for all list tables
    import glob
    for f in glob.glob(os.path.join(DATA,"**","*.json"), recursive=True):
        t=json.load(open(f))
        if t.get("type","").startswith("list_") and "entries" in t:
            cov=sum(e["max"]-e["min"]+1 for e in t["entries"])
            need=100 if t["type"]=="list_d100" else 10
            if cov!=need and t.get("complete",True): warn(f"{t['id']}: coverage {cov}/{need}")

def main():
    fate=parse_fate_chart()
    build_range("RANDOM EVENT FOCUS TABLE","mythic/event_focus.json","mythic.event_focus",100,"1d100","random-event-focus-table")
    build_range("SCENE ADJUSTMENT TABLE","mythic/scene_adjustment.json","mythic.scene_adjustment",10,"1d10","scene-adjustment-table")
    build_static(); build_ac(); build_plot_points(); build_meta_plot_points()
    mc={n:parse_meaning(n,idx) for n,idx in {"actions_1":1458,"actions_2":1478,"descriptors_1":1504,"descriptors_2":1525}.items()}
    complete, partial = parse_elements()
    manifest={"tables_built":sorted(built),"meaning_counts":mc,
        "elements_complete":len(complete),"elements_partial":{n:c for n,c in partial},
        "canon":{"mythic":sha(MYTHIC),"adventure_crafter":sha(AC)}}
    json.dump(manifest,open(os.path.join(DATA,"manifest.json"),"w"),indent=1)
    verify(fate)
    print(f"BUILT {len(built)} table files")
    print(f"Meaning core: {mc}")
    print(f"Elements complete: {len(complete)} / partial: {len(partial)}")
    if partial: print("  partial:", {n:c for n,c in partial})
    if warnings: print("\nWARNINGS:"); [print("  !",w) for w in warnings[:30]]
    if errors: print("\nERRORS:"); [print("  X",e) for e in errors]; sys.exit(1)
    print("\nVERIFICATION PASSED ✓")

if __name__=="__main__": main()
