# Workflow 03 — Revision (change an existing part safely)

Entry: routed by 00_intake for "doesn't fit / board changed / tweak X".
Skill `revise-part` is the trigger; THIS file is the order. The failure
this prevents: regenerate-and-drift (eval S6).

## Steps

1. **Diagnose the request class:**
   - dimension/feature change → continue here
   - "it doesn't fit" from a PRINT → suspect ASSUMED values then
     clearances; the fix may be a calibration event
     (workflows/04_calibration.md) not a geometry edit
   - part is DAMAGED → workflows/05_failure.md instead
   *Gate: class stated; for fit problems, the suspected value named.*

2. **Capture BEFORE** — re-run the current script (idempotent) from
   `models/<project>/<part>.py`; record diagnostics: volume, bbox,
   bodies, plus interface feature positions from the spec (read-only
   measure script if needed). For assembly members, also the relevant
   `_check_fit.py` lines.

3. **Edit parameters, not geometry** — the change must be a user-parameter
   expression change. If it can't be, the model wasn't parametric enough:
   FIRST refactor to parameters, re-run, verify diagnostics IDENTICAL to
   step 2, then apply the value change. Touch only parameters the
   revision names; shared `asm_` parameters change in the assembly
   contract too (both scripts, same edit).
   *Gate: the diff between scripts is parameter lines only (plus any
   verified-identical refactor).*

4. **Update the spec in the same edit** — interface row value + source
   (a new measurement upgrades ASSUMED → MEASURED), Loads if the change
   is structural (loads_strength.md re-check when sections shrank).

5. **Diff AFTER vs BEFORE** — re-run; every diagnostic delta must be
   explained by the requested change; an unexplained delta is a coupling
   bug — stop, find it, fix the contract. Assemblies: re-run
   `_check_fit.py`, same standard, including motion extremes if a moving
   part changed.
   *Gate: clean explained diff, stated in the summary.*

6. **Re-gate** — the design_review lines the change touches (a wall
   change re-checks walls; a joint change re-checks that joint + its
   stack line); `.venv/bin/pytest tests/ -q` green.

7. **Version and export** — `_v{n+1}` via the export template; NEVER
   overwrite a printed version. `docs/<project>/README.md` notes which
   version is current; assembly proven-together table gets the new set.

8. **Close** — summary: what changed, the before/after diff, what did NOT
   change (interface positions preserved), and whether a reprint of
   mating parts is needed (a clearance change moves BOTH sides' truth).

## Exit criteria
New version exported; script+spec committed together; diff explained;
mating-part impact stated.
