# trellis — reindeer-antler vine trellis for a vertical aeroponic tower

Two 500 mm reindeer-antler beams (6 tines each) joined at a Ø50 ring. The
stem tube slides into the tower's Ø50 port; the flexible gyrocup pushes into
the ring bore afterwards and wedges the trellis in place. Vines (tomato,
bean) get tied/wound onto the tines, which all climb ≥ ~45° with ball tips.

Spec: `specs/trellis/antler_trellis.md` (several ASSUMED dims — see spec).

## Printed parts

| Part | File | Material | Qty | Orientation |
|---|---|---|---|---|
| Hub (ring + lower antlers) | `exports/trellis/antler_hub_v3.3mf` | PLA | 1 | Lying down: stem tube pointing down, plate horizontal, antlers fanned low (~143 mm tall) |
| Upper antler, right | `exports/trellis/antler_upper_right_v3.3mf` | PLA | 1 | Lying flat on its back side |
| Upper antler, left | `exports/trellis/antler_upper_left_v3.3mf` | PLA | 1 | Lying flat on its back side |

All pieces **require support material** (organic 3D limbs) — dual-nozzle
mode, aux nozzle on support filament. 20 % gyroid infill, 4 walls.
~259 g PLA total plus supports.

v3: naturalistic geometry (`lib/limb.py::loft_limb` + wander/undulation in
`models/trellis/_antler_common.py`): C-swept spline beams with deterministic
centerline wander, radius undulation and knuckle swells at tine roots; oval
cross-sections with varying flatness; longitudinal spiral grooves (vascular
fluting) that fade at the polished tips; unevenly spaced tines, brow/bez
pointing forward, forked brow + crown; left antler's radii phase-shifted so
the pair isn't a perfect mirror clone. Modelled on a reindeer reference
photo.

The lying-down orientation keeps every beam axis in-plane, so bending loads
from the vines run within layers, not across them.

## Bought parts
None — the gyrocup and tower are the user's existing aeroponic system.

## Assembly
1. Dry-fit each upper antler spigot (Ø8) into its hub socket — press fit.
2. Apply CA glue to spigot and shoulder face, press home.
3. Slide the stem tube into the tower port.
4. Push the gyrocup through the ring bore (1.5 mm lead-in chamfer at the
   mouth) until its flex wedges the trellis tight.

## Notes
- PLA was chosen by the user; under sustained cantilever vine load and sun
  it will creep. Keep the load modest, tie the main vine weight near the
  hub, and expect to re-tension. PETG/ASA is the drop-in upgrade.
- Moment capacity is limited by the gyrocup wedge, not the plastic — heavy
  one-sided load can rotate the trellis in the round port.
