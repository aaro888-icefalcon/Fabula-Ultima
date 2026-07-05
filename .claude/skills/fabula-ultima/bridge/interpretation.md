# Interpretation — Fabula Ultima  (hook: meaning + NPC/villain craft)

## Operative
- Read every oracle result through a **JRPG / anime-fantasy** lens: high emotion, hope against despair, spectacle, personal stakes. Prefer the dramatic, character-first reading over the mundane one.
- NPCs are **competent and self-interested**, and act from their **Bonds** (admiration/inferiority, loyalty/mistrust, affection/hatred) and their want — never as plot props. Give a named NPC a goal, a method, and a feeling toward a PC.
- **Villains drive the world.** A villain pursues its agenda on a Clock even offscreen, makes an entrance (each PC gains 1 Fabula Point when it does), and spends **Ultima Points** for dramatic power plays — log every spend with `fu.py points ultima`.
- Honor the **Fabula cycle**: hardship → resolve (Fabula Points) → growth. Press the heroes; let defeat and Surrender carry real, lasting consequences rather than softening them.
- The active **genre** (`data/genre.json`, set at session zero, held in `campaign/state.json`) sharpens this lens: read its **pillars** and let its conflict themes + tech/magic level shape what's plausible — High (warring powers & hidden ancient magic), Natural (small-scale, seasons & spirits), Techno (soul-network & magitech). `gen.py` and `tick.py` already bias generation and world-advance by it; keep the narration consistent with it.

## How this world thinks
Fabula Ultima worlds are player-authored at session zero (`setting-canon.md`), so read NPCs and factions as natives of *that* world's magic, technology, and conflicts — not a generic setting. Bonds are the engine of drama: escalate them, threaten them, and let them be invoked. Themes (a PC's driving sentiment) are pressure points — a good scene puts a Theme to the test.

## Pacing & stakes
Conflicts should last ~3–4 rounds and cost resources (HP/MP/IP), then resolve toward a turn in the story. Between fights, spend time on Bonds, discovery, travel, and rest. Escalate Clocks visibly (telegraph before they fill). A filled villain/threat Clock is a Turning Point or a Random Event, never a silent tick.
