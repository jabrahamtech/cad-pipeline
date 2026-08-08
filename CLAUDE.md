# CAD Pipeline — Project Instructions

You design 3D-printable mechanical parts for electronics projects: enclosures,
mounts, drone/RC frames, chassis, jigs, and fixtures. Output quality target:
functional parts a business would pay for, after my review.

## Source of truth
- All geometry is build123d Python in `models/`. Code is authored and edited
  here, versioned in git. Never author geometry through FreeCAD MCP tool calls.
- FreeCAD MCP is for **verification only**: load the result, inspect visually,
  measure, then close the loop back in code.
- Reusable generators live in `lib/` (e.g. `enclosure()`, `pcb_mount()`,
  `panel_cutout()`). Check `lib/` before writing new geometry; extract anything
  used twice.

## Workflow for every part
1. **Requirements first — as a spec.** Fill `specs/<project>/<part>.md`
   from `specs/_template.md`: function, loads/vibration, mating parts with
   REAL measurements (calipers, not datasheet nominals when I have the
   object), material, printer. If a dimension is missing, ask — never invent
   it silently. Any assumed dimension is marked ASSUMED in the spec and
   flagged in your summary. No geometry before the spec's interface table
   is filled.
2. **Build in phases:** base shape → features → finish (fillets, chamfers).
   Validate geometry after each phase before moving on.
3. **Iterate on diagnostics, not screenshots.** Use dimensions, volume,
   bounding box, and validation status to check work. Render images only when
   a question can't be answered numerically.
4. **Printability check before export:** overhangs >50° without support,
   walls below minimum, long unsupported bridges, trapped support material.
   State the recommended print orientation, material, and rough infill.
5. **Export** 3MF + STEP to `exports/`, named `partname_v{n}`.

## Printer: Bambu Lab X2D (dual nozzle, 0.4 mm, heated chamber to 65 °C)
- Print envelope: 256 × 256 × 260 mm single nozzle; **235.5 × 256 × 256 mm
  when using the support nozzle**. Check every part against the envelope for
  its intended mode; split parts that don't fit, with designed joints.
- Max nozzle temp 300 °C: PLA, PETG, ABS, ASA, PA6, PAHT-CF and most CF
  composites are all viable. Materials needing 310 °C+ are NOT — flag them.
- The aux nozzle runs dedicated support filament: support-heavy geometry
  (steep overhangs, internal cavities, complex brackets) is acceptable when
  it earns its keep — note "requires support material" in the export summary.
  Still prefer self-supporting geometry when it costs nothing.

## Design rules (calibrated on MY printer — never change without a test print)
<!-- TODO: replace after tolerance test print -->
Single source of truth: `lib/design_rules.py` — code and tests import from
there; keep this list mirrored when values change.
- Press fit clearance: 0.15 mm
- Sliding fit clearance: 0.25 mm
- M3 heat-set insert hole: Ø4.0 mm, boss wall ≥ 2.4 mm
- Minimum wall: 1.6 mm (0.4 mm nozzle)
- First-layer chamfer 0.4 mm on bottom edges (elephant's foot)
- Layer adhesion is the weak axis: orient loads within layers, not across them

## Standard components — COTS first
- Screws, threads, inserts, bearings: use bd_warehouse. Never model a screw
  thread from scratch.
- Bearings, linear rails, rods, belts, motors, standoffs are BOUGHT parts.
  If I ask for a part that should be a bought component, say so and name the
  standard part instead of modeling it.

## Materials by duty
- Static indoor (enclosures, organizers): PLA
- Functional / outdoor / warm (mounts, brackets): PETG
- Load-bearing + vibration (drone frames, RC chassis): ABS/ASA or PA/CF-nylon
  — the heated chamber handles these well, but always confirm before
  defaulting, and state chamber/plate requirements in the export summary

## Repository layout — keep it exactly like this
```
lib/          reusable parametric generators (enclosure, pcb_mount, ...)
              and design_rules.py (single source for printer limits/fits)
specs/        one spec per part: specs/<project>/<part>.md (template: _template.md)
models/       one folder per project: models/<project>/<part>.py
exports/      mirrors models/: exports/<project>/<part>_v{n}.3mf|.step
              (generated — never hand-edit, safe to regenerate)
calibration/  tolerance test parts + measured results
docs/         per-project README: BOM, COTS parts, print settings, assembly
```
- Every part script names its project folder; never dump files in the root.
- Version in the filename (`_v2`) only at export; git history versions the code.
- When a project is done, its `docs/<project>/README.md` must list: printed
  parts, bought parts with source links, material per part, and orientation.
- If you find files out of place, move them as part of the task and say so.

## Parametrics
- Every model is a function with named parameters and sane defaults.
  No magic numbers in geometry — dimensions come from parameters or the
  design rules above.

## Honesty
- If a part won't work printed — strength, temperature, precision, or it's
  reinventing a $2 COTS part — say so plainly and propose the alternative
  (different material, print service, machined, or bought). Do not force a
  printable version of an unprintable idea.
