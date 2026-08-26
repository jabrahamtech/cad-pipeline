# gripper_jaws — spec

Project: `models/robotarm/fusion/gripper_jaws.py` (Fusion MCP authored)
Status: DRAFT

## Function
CLAMSHELL hand, one motor (Jonathan: Koch-style, "more like a clam shell"):
the moving half is a curved shell about the grip servo's shaft — the clam
hinge — closing rim-to-rim onto the fixed shell that is part of
`gripper_base`. Flat-paddle and sector-gear pincher designs both retired.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Hinge axis | grip SG90 shaft at (0, +30 above the gripper plate), along Y | design |
| Shell | annulus r 27..30 about the hinge, sweep +2°..+85° (closed pose), 21 wide (y −4..17) | design |
| Carry | hub Ø20.25 on the horn plane (y 10.2..16.2) + web arm 15 wide along 45° | design |
| Horn mount | cross recess 32.4 × 7.4 × 1.8 in the hub back face; Ø6 screw bore, horn screw + washer | lib/servo |
| Mouth | meets the fixed shell's rim at ~0°, ~2 gap as modelled; servo swings it open ~80° | derived |
| Shell facets | arcs are 5°-faceted polygons — smooth in the finish pass if wanted | design note |

## Loads & environment
SG90 1.8 kg·cm stall → ~0.40 kgf at the tip; gear teeth see the same torque.
Module 1.5 PETG teeth are fine at this load. Indoor.

## Print plan
PETG · flat on the side face, gear teeth vertical → teeth print clean and
jaw bending load lands within layers · no support · 40 % infill, 4 walls.

## Acceptance
- [ ] invariant tests pass
- [ ] sectors mesh through full travel with no jam or slop-jump
- [ ] jaws meet flush at closed, parallel within ~1 mm over the faces
- [ ] printed and verified — date, measured result, deviations
