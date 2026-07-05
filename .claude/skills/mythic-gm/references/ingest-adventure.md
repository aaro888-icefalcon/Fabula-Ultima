# Ingesting a prepared adventure (hook: adventure-ingest)
Goal: keep the module WHOLE while running it in the always-on Adventure Crafter, **pure sandbox**.
The module supplies WHAT (authored beats, NPCs, locations); the AC supplies WHEN + the connective tissue.

## Process (done once at load — a good subagent job)
1. Read the module **one section at a time**. Chop it into **clusters** = authored scenes/nodes.
2. For each cluster write: a scene-level description (kept ~whole) + member **fragments** (atomic plot points),
   all **tagged** (themes / threads / characters / elements / location) and **cited to source**. Optional soft `gate`.
   Use the schema in `assets/bridge-templates/adventures/CLUSTER-SCHEMA.md` → write `bridge/adventures/<module>.md`.
3. Seed the Lists from all clusters: objectives → **Threads**, NPCs/forces → **Characters**, locations/hazards → **Adventure Features**.
4. Note the **Diminisher** (solo scaling) and any module random tables → make them `generators/` JSON.

## How it runs (default: light + pure sandbox)
- **No forced order, no climax, no Plot Armor.** Authored content surfaces only by contextual relevance.
- **Content bias: medium** — prefer an authored fragment when reasonably relevant, else roll a random Plot Point.
- **Weighted-random** draw among relevant candidates; keep a **usage ledger** and lean toward **un-used** fragments (organic coverage, never railroad).
- **Expected Scene:** if a cluster fits the current context, frame the Expected Scene as that cluster's described scene (then Scene-Test it as normal — it may Alter/Interrupt).
- **Turning Point plot points (cluster cohesion):** when a Turning Point draws one fragment from cluster X, prefer X's other fragments for the remaining slots; fill leftovers from the random Plot Point Table (`adventure_crafter.py turning-point`).
- Fragments/clusters also feed the **seed deck** and **Random-Event invokes**.

The result: the module's whole content is available and reassembles where relevant; everything between is live Mythic/AC.
