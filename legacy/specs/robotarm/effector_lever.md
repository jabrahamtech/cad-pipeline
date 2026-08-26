# effector_lever — spec

Project: `models/robotarm/effector_lever.py`
Status: MODELED (2026-08-22)

## Function
Small arm on the effector SG90's horn that presses the free scissor handle to
close the blades. Part of the SCISSOR effector; not used with the gripper.

## Interfaces — the dimensions that matter
| Interface | Value | Source | Parameter |
|---|---|---|---|
| SG90 horn | form-fitting cross pocket, 32 span × 1.6 | DATASHEET | — |
| Lever reach | 25.0 mm servo axis → pad | design | `lever_length` |
| Free handle bar thickness | 6.0 mm (sizes the fork slot) | ASSUMED | `handle_thickness` |
| Fork | slot between the arm underside and the pad's retaining lip — captures the handle in the one direction it can escape | design | — |

## Loads & environment
SG90 stall 1.8 kg·cm → ~0.72 kgf at a 25 mm lever. If the scissors need a
firmer squeeze than that, shorten `lever_length` (more force, less travel)
before blaming anything else. Indoor.

## Print plan
PETG · horn-pocket face UP, pad post and lip building upward (the lip is a
2 mm radial overhang) · no support · 40 % infill.

## Acceptance
- [ ] invariant tests pass
- [ ] fork captures the free handle; lever closes the blades fully without
      stalling the servo
- [ ] printed and verified
