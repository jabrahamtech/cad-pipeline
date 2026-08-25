# Materials — engineering behavior, not just duty class

Read when: choosing or defending a material; a part warps, creeps, swells,
or lives outdoors/warm; a calibrated fit misbehaves in a new material.
CLAUDE.md "Materials by duty" gives the default; this file is why, and the
traps. All values HANDBOOK unless a calibration/ entry says otherwise.

## Working table (X2D, 0.4 nozzle, chamber to 65 °C)

| | PLA | PETG | ABS/ASA | PA6/PA-CF | TPU 95A |
|---|---|---|---|---|---|
| Use temp, sustained | ≤ 50 °C | ≤ 70 °C | ≤ 90 °C | ≤ 100 °C+ | ≤ 60 °C |
| Stiffness | highest | medium | medium | high (CF) | none |
| Ductility / impact | brittle | good | good | good | extreme |
| Creep under load | BAD | ok | good | best | n/a |
| Shrink / warp | ~0.3% low | ~0.5% low | 0.8–1.5% HIGH | 1–1.5% high + moisture | low |
| UV outdoors | fades, embrittles | ok | ASA best | ok | ok |
| Chamber needed | no (≤ 40 plate ok) | no | YES 50–65 °C | YES + dry | no |
| Fit shift vs PLA cal. | baseline | ≈ same | holes ~0.1 tighter | tighter + swell | n/a |

## The traps, per material

- **PLA:** creeps under sustained load in days (loads_strength.md) and
  goes soft in a parked car (55 °C+). Never for: clamps holding preload,
  outdoor brackets, anything near electronics that run warm. Annealing
  (~80 °C, 15 min) raises heat resistance but shrinks/warps the part
  ~1–2% — only for non-fit parts, or scale the model after a test piece.
- **PETG:** the functional default. Strings (calibrate retraction before a
  fit-critical print); loves adhering to smooth PEI too much (textured
  plate or release agent); slightly glossier layer lines. Bonds poorly
  with CA glue — use epoxy.
- **ABS/ASA:** shrinkage means the CALIBRATED fits (measured in PLA/PETG)
  DO NOT transfer — re-gauge every critical fit the first time a project
  uses them (workflows/04_calibration.md). Big flat parts need brims and the
  full chamber temp; corners lift first. ASA over ABS for anything
  outdoor. Acetone-smoothing seals surfaces but rounds dimensions.
- **PA / PA-CF:** hygroscopic to the point of failure — dry-box while
  printing, and the PART swells ~0.2–0.5% saturated: design fits at the
  wet size for parts living in normal air (gauge wet, not fresh off the
  plate). CF variants: stiff, dimensionally stable, abrasive (hardened
  nozzle installed?), and layer adhesion is their weak axis even more
  than usual.
- **TPU:** flexible parts (grommets, feet, seals, tires). Clearances:
  press fits work at ZERO or negative clearance (it squishes) — the
  JOINT_FIT_MM table does not apply; gauge everything. Print slow;
  bridges/overhangs poorly — design self-supporting.

## Choosing — the honest sequence

1. Duty class default (CLAUDE.md): static-indoor PLA / functional PETG /
   load+vibration ASA-or-PA. Confirm with Jonathan before defaulting to a
   chamber material.
2. Override triggers: sustained load → skip PLA; outdoor → ASA/PETG;
   > 70 °C → ASA/PA; sliding wear → PETG/PA over PLA; flexible → TPU;
   fit-precision jig → PLA (most dimensionally accurate) if loads allow.
3. State in the export summary: material, WHY, chamber/plate requirement,
   and whether the fits were calibrated in that material or carried over.

## Multi-material / dual nozzle notes

- Aux nozzle = support filament by default (CLAUDE.md envelope rules).
  Swapping it to a second color/material instead costs the support
  workflow — flag the trade.
- Material pairs that bond in-print: PLA+PLA, PETG+TPU (good), PLA+PETG
  (weak — use as intentional release/support interface). Mechanical
  interlocks (dovetail pockets) beat adhesion for dissimilar pairs.
- Bambu paint/multi-color 3MFs: lib/mesh_paint.py; color is cosmetic —
  never let a color seam land on a load path across layers.
