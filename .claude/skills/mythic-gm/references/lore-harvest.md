# End-of-scene Lore Harvest (subagent)

When a setting bible, sourcebook, or published module is loaded, established lore should keep feeding the adventure — new Characters and Threads should surface from the canon as play touches it, not only from random rolls. At the end of each scene (Bookkeeping), spawn a subagent (Task tool) to do this harvest so the main loop stays lean.

## When to run
- A `setting-canon.md`, sourcebook, or prepared module is in the campaign folder, **and**
- the scene introduced, approached, or implicated something in that lore (a place, faction, named NPC, event).

## Subagent prompt (fill the brackets)
> You are a lore scout for a solo Mythic campaign. **Inputs:** (1) the setting/sourcebook/module canon at <paths>; (2) the current Threads List: <list>; (3) the current Characters List: <list>; (4) what just happened this scene: <2–4 sentence recap>.
> **Task:** From the canon that is *relevant to what just happened* (and that the PC could plausibly have encountered), propose up to 3 new **Characters** and up to 2 new **Threads** to add to the Lists, plus any **Adventure Features** (module mode). For each, give a one-line reason tied to the scene and a canon citation. **Do not invent beyond the canon.** Respect Player-vs-PC knowledge: only surface things the PC could now know. Return a short list; add nothing the loop hasn't earned.

## Applying the result
- Add accepted Characters/Threads to the **current adventure's** Lists (weighted ≤3). Recurring cross-adventure figures also go on the campaign roster.
- These additions make later Random Events and List invokes draw on real lore, tying the procedural engine to the established world.
- Keep it disciplined: this *enriches* the Lists; it does not script outcomes. The dice still decide what those elements do.
