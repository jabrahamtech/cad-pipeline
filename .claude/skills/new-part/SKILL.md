---
name: new-part
description: Design a new 3D-printable part end to end through the Fusion MCP — spec first, then a parametric Fusion API script, static lint, numeric verification, design review, export. Use whenever the user asks to design, model, or create a part, enclosure, mount, bracket, jig, or fixture.
---

# New part workflow (Fusion MCP)

**Order of record: `workflows/01_new_part.md`** — this skill is the
trigger and summary; on step order and gates, the workflow file wins.
Every request first passes `workflows/00_intake.md` triage.

Multi-piece request (machine, mechanism, enclosure with guts)? Run the
**plan-assembly** skill FIRST — no per-part spec before the assembly
contract exists.

## 1. Spec before geometry
Copy `specs/_template.md` to `specs/<project>/<part>.md` and fill it in.
Every interface dimension needs a Source (MEASURED / DATASHEET / STEP /
ASSUMED — protocol: `knowledge/dimensioning.md`) AND a joint type whose
clearance comes from `JOINT_FIT_MM` (`knowledge/joints_tolerances.md`).
If a dimension that affects fit is missing, ask for it — one batched
question, not a drip. Only proceed with ASSUMED values if the user
declines to measure, and say so in the summary. Do not write geometry
until the spec's Interfaces table is complete.

## 2. Don't model what exists — and read the topic in play
1. COTS check — screws, threads, inserts, bearings, gearboxes, rails are
   BOUGHT (CLAUDE.md "Standard components"). If the requested part IS a
   bought part, say so and name it.
2. Route through `knowledge/` per the CLAUDE.md table before modeling the
   matching feature: fasteners_inserts, bearings_rotation, gears_drives,
   cable_management — these encode the failures already paid for.
3. Vendor STEP file — for boards/components, ask for or fetch the
   manufacturer STEP, import it, and design around it.
4. An existing part script in `models/` that can be parameterized further.

## 3. Script it — never click it
- Read `fusion/PLAYBOOK.md`; start from `fusion/templates/part_scaffold.py`.
- Query `fusion_mcp_read` apiDocumentation for any API you're not sure of
  BEFORE running the script.
- Every dimension is a Fusion user parameter with a provenance comment;
  shared assembly dimensions use the shared `asm_`-style parameters from
  _assembly.md. Component named `<project>_<part>`; script idempotent;
  no try/except.
- Build in phases: base shape → features → finish. One `fusion_mcp_execute`
  run per phase; check printed bbox/volume/body-count/isValid against
  expectation before the next phase. A half-worked phase is undone
  (`fusion_mcp_update` undo) and re-run fixed — never patched.
- Screenshot (named view directions) only when numbers can't answer.

## 4. Gate, export, close out
1. Save the final script to `models/<project>/<part>.py`;
   `.venv/bin/pytest tests/ -q` must pass (static script lint).
2. Run the design review checklist (`knowledge/design_review.md`) — state
   pass/fail/n-a compactly in the summary. Assemblies additionally need
   `_check_fit.py` clean (zero unexpected interference) before ANY export.
3. Export STEP + 3MF via `fusion/templates/export_part.py` to
   `exports/<project>/<part>_v1.*`.
4. Update spec Status to MODELED; summary lists all ASSUMED values.

## 5. Improve the system on the way out
- Before any large print, offer a gauge for the risky interface — minutes
  of printing instead of hours. HANDBOOK clearances used on a critical fit
  MUST be gauged.
- New API quirk learned the hard way → append to `fusion/PLAYBOOK.md` now;
  new engineering lesson → the matching `knowledge/` file.
- When the user confirms the printed fit, set spec Status to ACCEPTED and
  log measured deviations in `calibration/` — design-rule changes (and
  HANDBOOK → CALIBRATED promotions) only from measured data.
