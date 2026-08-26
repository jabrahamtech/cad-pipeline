# gripper_base — spec

Project: `models/robotarm/fusion/gripper_base.py` (Fusion MCP authored)
Status: MODELED phase 1 (2026-08-24) — replaces the gripper_carrier collar
concept after the roll joint became a powered top cradle on `wrist_yoke`.

## Function
The stationary half of the CLAMSHELL hand — one part, three jobs
(Jonathan's layout): the WRIST CONNECTION (plate bolts onto the roll SG90's
horn, so the whole hand rolls), the MOTOR MOUNT (wall holding the grip
SG90 whose shaft is the clam hinge axis at (0, +30)), and the FIXED
clamshell half (annulus r 27..30 about the hinge, sweep −85°..−2°, 21
wide, foot joining it to the plate). The moving shell (gripper_jaws.md)
closes onto its rim.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Roll horn mount | cross recess 32.4 × 7.4 × 1.8 under the plate, Ø9 centre, 4 × Ø2.2 on Ø14 | DATASHEET (same kit as yoke ear) |
| Plate | 46 × 34 × 4 | design |
| Jaw wall | 46 × 4, 30 tall | design |
| Grip servo | SG90 behind the wall (wall 46 × 4, z 4..40), Ø13 shaft hole at (0, +30) = hinge axis | DATASHEET |
| Servo fixing | 2 × Ø1.8 pilots at −8.4 / +19.4 from the shaft (holes straddle case centre) | lib/servo.tab_holes |
| Servo lead | exits below the case, free air above the plate, open behind the wall | DATASHEET + design |
| Fixed shell | annulus r 27..30 about (0,30), sweep −85°..−2°, y −4..17; foot 4 × 21 × 6 to the plate | design |
| Moving shell plane | hub at y 10.2..16.2 on the horn top | derived (mount_to_horn) |

## Loads & environment
Grip reaction torque + gripper weight on the roll horn's M2 screws (shear,
r 7 — same margin as the pitch joint). Indoor.

## Print plan
PETG · plate flat on the bed, wall up · idler boss is a 4 mm horizontal
cylinder — small support or accept the sag on a non-bearing surface;
everything else self-supporting · 40 % infill, 4 walls.

## Acceptance
- [ ] invariant tests pass
- [ ] plate seats on the roll horn; M2 screws land at any 90° orientation
- [ ] grip SG90 shaft centres in the Ø13 hole; both pilots take the screws
- [ ] printed and verified — date, measured result, deviations
