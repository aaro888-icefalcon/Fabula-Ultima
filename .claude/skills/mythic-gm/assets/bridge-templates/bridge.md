# Bridge manifest — <Companion Name>
Prose: one paragraph on what this companion supplies (RPG / setting / generators).

> **Every overridden hook needs a `## Operative` block** in its file (the imperative the GM must hold
> in play) — `bridge.py brief` surfaces these and boot loads them; `bridge.py validate` warns if one is
> missing. Optionally a manifest `"digests"` map can supply/override a hook's one-line digest directly.

```json
{
  "companion": "<Companion Name>",
  "engine": "mythic-gm>=2",
  "overrides": ["resolve","meaning","chaos","themes","generate:character","generate:location","world-tick","seeds"],
  "files": {
    "system_profile": "system-profile.md",
    "interpretation": "interpretation.md",
    "chaos": "chaos-tendency.md",
    "themes": "theme-weights.md",
    "generators": "generators/registry.md",
    "subsystems": "subsystems.md",
    "seeds": "seeds.md",
    "canon": "setting-canon.md"
  },
  "generators_map": {
    "character": { "mode": "conjunction", "table": "generators/npc_role.json",
                   "note": "flesh the NPC from setting-canon factions & the current scene" }
  }
}
```

`generators_map` is the **machine-readable** routing the engine actually reads (the prose
`generators/registry.md` is the human index). Each entry: `mode` = `replace` (companion
generator **instead of** the Mythic/AC default) · `conjunction` (companion **and** default) ·
`default` (ignore, use the engine default); optional `table` = a `list_d100`/`list_d10` JSON in
this bridge; optional `note` = lore the GM applies. Only `character` is wired to auto-fire today
(on any **NEW CHARACTER** result); add more keys as the engine grows hooks. Omit `generators_map`
entirely → every generation uses the engine default (AC Character Crafter for characters).
