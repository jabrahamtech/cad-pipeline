# Workflow 04 — Calibration (measured reality updates the rules)

Entry: a print-fit report arrives ("28.7 snug, 29.1 loose"); a gauge is
needed (01 step 8 / 02 step 6); a project uses a NEW material for
critical fits; a HANDBOOK value is about to carry a critical fit.
This is the loop that makes every print improve the next one.

## A — designing a gauge (when one is owed)

1. **Isolate the question** — ONE interface, the minimum geometry that
   answers it: the thread, the pocket ring, the clamp jaw, the two-piece
   corner joint. Target < 20 min print, < 10 g.
2. **Step the unknown** — when the true value is uncertain, print 3–5
   candidates in ONE gauge (stepped bores, labeled ladder) so a single
   print answers it. Label each step IN THE PLASTIC (embossed value).
3. Gauge scripts are real parts: `models/<project>/<part>_gauge.py`,
   spec optional but the target interface's spec row is referenced in
   the docstring. Export as any part; note "gauge" in the summary.
4. Tell Jonathan exactly what to test and report: "which step threads on
   snug by hand", "does the bearing press in with thumb pressure and not
   fall out" — a gauge without a defined pass observation is decoration.

## B — recording a result (measured reality arrives)

1. **Write the entry** — `calibration/YYYY-MM-DD-<project>-<what>.md`:
   what was printed (part/gauge + version + MATERIAL + orientation of the
   fit), what was measured/observed, numbers, and the conclusion.
2. **Trace the implication:**
   - confirms current rule → note "confirms", done
   - contradicts a HANDBOOK value → update `lib/design_rules.py`, tag the
     constant CALIBRATED with the date, mirror CLAUDE.md headline list if
     it's a headline value
   - contradicts a CALIBRATED value → flag loudly; only change with
     Jonathan's confirmation (per the standing rule) — the discrepancy
     might be material/orientation, not the rule (step B3)
   - implicates an ASSUMED spec value → fix the spec row (→ MEASURED),
     then run workflows/03_revision.md on the part.
3. **Scope the rule correctly** — a fit is calibrated PER material family
   and orientation (materials.md fit-shift row). A new result in ASA does
   not overwrite the PLA/PETG number: extend the rule with a scoped
   value (comment or dict entry) rather than clobbering.
4. **Propagate** — parts currently in flight that used the corrected
   value: list them, revise the ones not yet printed (03), flag the ones
   already printed.

## C — new-material onboarding (first critical fit in a material)

1. Print the standard fit ladder in that material: press/sliding/
   bearing-pocket rings + an M3 insert boss (one plate, ~30 min).
2. Record per B; add scoped values; note chamber/plate settings that
   produced them (they're part of the calibration).
3. Only then run 01/02 exports for critical-fit parts in that material.

## Exit criteria
calibration/ entry committed; design_rules/spec updated with correct
scope and provenance tags; affected in-flight parts listed and routed.
