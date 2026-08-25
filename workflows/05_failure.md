# Workflow 05 — Failure response (a part broke, wore, warped, or loosened)

Entry: routed by 00_intake when physical damage/degradation is reported.
Knowledge core: failure_analysis.md (the mode table lives there).
Discipline: mode FIRST, fix SECOND, system update ALWAYS.

## Steps

1. **Gather evidence** — ask (one batch): photo of the break faces / worn
   surface, when it failed (immediately / after N days / after N cycles),
   what it was doing (load, temperature, pose), which version + material
   was printed. Don't propose fixes yet.
   *Gate: enough to attempt mode identification.*

2. **Identify the mode** — match against the failure_analysis.md table
   (layer split / overload / stress concentration / creep / fatigue /
   impact / boss-insert / pull-out / wear / warp / preload loss). State
   the mode and the evidence for it. Two candidate modes → say both and
   what observation separates them.

3. **Check the arithmetic** — reproduce the failure location in the
   model: script-measure the section, recompute stress with the
   now-known real load (loads_strength.md). State whether the design
   math predicted it (load model wrong vs factor ignored vs rule
   missing). Update the spec's Loads section with reality.

4. **Fix by mode** — apply the mode's fix from failure_analysis.md, not
   reflex thickening. Execute as workflows/03_revision.md (parameter
   edits, diff, re-gate) — or, if the mode indicts the CONCEPT (third
   failure of the same function, or a printed part doing a COTS part's
   job), stop and present the honest alternatives per CLAUDE.md before
   modeling anything.

5. **Re-verify the mode's specific risk** — the review lines + checks
   that mode touches: layer split → orientation statement re-argued;
   fatigue → cyclic factor shown; wear → duty/bearing decision; stack/
   preload → steel path shown. Assemblies: `_check_fit.py` re-run if
   geometry moved.

6. **Feed the system (same commit)** — per failure_analysis.md step 4:
   dated calibration/ failure entry; HANDBOOK corrections; knowledge-file
   edits if a rule was missing; a design_rules constant or lint idea if
   the mode has now appeared twice across projects.

7. **Reprint plan** — new version exported (03 step 7), what to observe on
   the reprint stated (the specific thing that failed, plus a duty check
   date if creep/fatigue was the mode: "check the clamp in 2 weeks").

## Exit criteria
Mode named with evidence; fix traced to the mode; spec/calibration/rules
updated in the same commit; reprint exported with an observation plan.
