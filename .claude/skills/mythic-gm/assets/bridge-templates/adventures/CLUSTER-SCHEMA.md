# Ingested Adventure — <Module>   (hook: adventure-ingest; pure sandbox)
fidelity: light

## Clusters (authored scenes/nodes) → each with a scene description + member fragments
### cluster: <id> — "<scene name>"   (source: module p.NN)
scene: <the authored scene framing, kept ~whole>
threads: [<T1>]   characters: [<NPC>]   elements: [<location/object>]   themes: [<Tension>]
gate: <optional soft precondition, else none>
fragments:
  - plot_point: "<a beat within this scene>"   themes: [Tension]   weight: 1
  - plot_point: "<another beat>"               themes: [Mystery]   weight: 1

## Seed the Lists from all clusters: Threads (objectives), Characters (NPCs), Adventure Features (locations/hazards).
## Diminisher (solo scaling): <1/2 | 1/3 | 1/4>
