# turret_cap — spec

Project: `models/robotarm/turret_cap.py`
Status: MODELED (2026-08-22)

## Function
Drum bolted to the top of base_platter. Carries the MG90S base-yaw servo
(flange down on its top face, case hanging through into the platter column)
and the three 608ZZ rollers the shoulder turntable rides on.

Exists as a separate part for one reason: the servo column must stay ~20 mm
wide through the electronics bay so the breadboard clears it, while the
roller race must be Ø104. Flaring one into the other inside a single part
means a >50° overhang; as two parts, both print flat with no support.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| 608ZZ bearing | Ø22 × 7, bore 8, inner race OD ~12 | DATASHEET (user has 6) |
| Roller axles | M8 × 30 bolt + M8 nyloc, one per roller | COTS |
| Fork gap | 7.9 mm with 0.4 clamp pads → grips the inner race only | design |
| Axle bore | Ø8.4 (bolt runs free in the fork, clamped by the nut) | design |
| Roller pitch radius | 36.0 mm, azimuths 90/210/330° | derived |
| Roller AXLE direction | RADIAL — points at the hub | kinematics |
| MG90S case opening | 12.45 × 23.05 (case + sliding clearance) | DATASHEET |
| MG90S flange pilots | 2 × Ø1.8, 27.8 pitch, 12 deep | DATASHEET |
| Cap bolts | 3 × M3 clearance Ø3.4 + Ø6.5 counterbore, r=45, az 120/180/240 | design |
| Overall | Ø104 × 19.2 (12 plate + fork above it) | derived |

## Why the axles are radial
The disc's surface moves TANGENTIALLY over each roller, so the roller's axis
has to be perpendicular to that — radial — for it to roll, exactly like the
rollers in a thrust bearing or a car's wheels going round a roundabout. A
tangential axle looks perfectly plausible and is completely wrong: the contact
then tries to travel radially while the disc goes the other way, so the
bearing scrubs instead of rolling and wears a flat on its outer race. The
first version of this part had it wrong; `tests/test_robotarm.py` now probes
the built solid to make sure the fork walls sit fore-and-aft along the radius.

## Loads & environment
Carries the whole arm's weight and overturning moment through the rollers;
indoor. Roller loads are low (arm < 500 g at ~200 mm), well inside a 608's
rating — the bearings are there for stiffness and zero slop, not capacity.

## Print plan
PETG · flat on the bottom face, forks up · no support (fork slots are
open-ended vertical channels; the Ø8.4 axle holes are short bridges) ·
25 % infill, 4 walls.

## Acceptance
- [ ] invariant tests pass
- [ ] 608ZZ drops between the fork pads and spins freely once the M8 nyloc
      is tight; flange pilots catch the supplied servo screws
- [ ] printed and verified — date, measured result, deviations
