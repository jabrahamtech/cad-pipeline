---
name: new-part
description: Design a new 3D-printable part end to end — spec first, then build123d model, invariant tests, export. Use whenever the user asks to design, model, or create a part, enclosure, mount, bracket, jig, or fixture.
---

# New part workflow

## 1. Spec before geometry
Copy `specs/_template.md` to `specs/<project>/<part>.md` and fill it in.
Every interface dimension needs a Source (MEASURED / DATASHEET / STEP /
ASSUMED). If a dimension that affects fit is missing, ask for it — one
batched question, not a drip. Only proceed with ASSUMED values if the user
declines to measure, and say so in the summary. Do not write geometry
until the spec's Interfaces table is complete.

## 2. Don't model what exists
In order, before writing new geometry:
1. `lib/` — reuse an existing generator if one fits.
2. `bd_warehouse` — fasteners, HeatSetNut, threads, bearings, gears,
   sprockets, o-rings, V-slot extrusion. Never hand-model these.
3. Vendor STEP file — for boards/components, ask for or fetch the
   manufacturer STEP and design around it.
4. COTS check — if the requested part is a bought part, say so and name it
   (CLAUDE.md "Standard components").

## 3. Build in phases, verify numerically
Base shape → features → finish. After each phase check volume, bbox, solid
count against expectation. Render only when a question can't be answered
numerically. Follow `lib/design_rules.py` values — no magic numbers;
every dimension traces to a spec interface, a design rule, or a named
parameter with a default.

## 4. Gate, export, close out
1. `.venv/bin/pytest tests/ -v` must pass.
2. Printability check: overhangs, walls, bridges, trapped support;
   state orientation + material + infill.
3. Export 3MF + STEP to `exports/<project>/<part>_v1.*`.
4. Update spec Status to MODELED; summary lists all ASSUMED values.

## 5. Improve the system on the way out
- Pattern used for the second time → extract into `lib/` now.
- When the user later confirms the printed fit, set spec Status to
  ACCEPTED and log measured deviations in `calibration/` — propose a
  design-rule change only from measured data.
