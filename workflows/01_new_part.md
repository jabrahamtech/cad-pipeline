# Workflow 01 — New part (single printable piece)

Entry: routed here by 00_intake, or as the per-piece loop inside
02_assembly. Skill `new-part` is the trigger; THIS file is the order.
Each step has a gate — do not start a step until the previous gate holds.

## Steps

1. **Spec** — `specs/<project>/<part>.md` from `specs/_template.md`.
   Interface table complete: every row has Value + Source
   (knowledge/dimensioning.md) + Joint type (knowledge/joints_tolerances.md).
   Loads section filled — including the ESTIMATED worst-case load and
   duty (static/cyclic/impact) because step 3 sizes against it
   (knowledge/loads_strength.md). Cables section filled or "n/a".
   *Gate: no ASSUMED value that Jonathan hasn't declined to measure.*

2. **Knowledge routing** — read the `knowledge/` files whose triggers the
   part hits (CLAUDE.md router table). Note in one line which apply:
   e.g. "fasteners + bearings + stack-up". This is where bearing choice,
   fastener sizes, gear buy-vs-print, and material
   (knowledge/materials.md step-3 sequence) get DECIDED — before geometry.
   *Gate: material + every COTS component named; torque/strength
   arithmetic done if loaded (one paragraph, in the spec).*

3. **Plan the build** — decide print orientation FIRST (strength beats
   convenience — loads within layers; then shortest height,
   knowledge/dfm_optimization.md), show faces, support strategy, and the
   phase list: base shape → features → finish. Identify the riskiest
   interface and whether it needs a gauge BEFORE the full part
   (uncalibrated/HANDBOOK fit on a critical joint ⇒ yes).
   *Gate: orientation stated; gauge decision made.*

4. **Script phase-by-phase** — from `fusion/templates/part_scaffold.py`,
   per `fusion/PLAYBOOK.md`: apiDocumentation lookups first; user
   parameters with provenance comments; idempotent component
   `<project>_<part>`; one `fusion_mcp_execute` per phase; after each
   phase check printed bbox/volume/bodies/isValid against expectation.
   Half-worked phase → undo, fix, re-run.
   *Gate per phase: diagnostics match expectation before the next phase.*

5. **Finish pass** — fillets at loaded junctions (≥ MIN_FILLET_LOADED_MM),
   chamfers on mating edges + bottom edges (elephant foot), lead-ins,
   cosmetic faces (dfm_optimization.md).
   *Gate: diagnostics still valid; volume delta explained.*

6. **Design review** — run `knowledge/design_review.md` line by line;
   compact pass/fail/n-a block goes in the summary. Fix fails, re-run.
   *Gate: all lines pass or n/a.*

7. **Lint + persist** — save script to `models/<project>/<part>.py`;
   `.venv/bin/pytest tests/ -q` green; commit script + spec together.

8. **Gauge first if step 3 said so** — export/print the gauge, wait for
   the measured result (04_calibration handles it), THEN export the part
   with the confirmed value.

9. **Export** — `fusion/templates/export_part.py` → 
   `exports/<project>/<part>_v{n}.step|.3mf`. Never overwrite a printed
   version.

10. **Close out** — spec Status → MODELED; summary: orientation, material,
    infill, support y/n, ASSUMED list, gauge plan, which design rules got
    stress-tested. Update `docs/<project>/README.md` if the project table
    changed. New API quirk → PLAYBOOK.md; new engineering lesson → the
    matching knowledge file.

## Exit criteria
Exported files + committed script/spec + review block in the summary +
follow-up (gauge or print) explicitly stated.
