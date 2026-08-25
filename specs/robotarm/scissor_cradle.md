# scissor_cradle — spec

Project: `models/robotarm/scissor_cradle.py`
Status: **INCOMPLETE (2026-08-24)** — the cradle mounts, the effector servo
has nowhere to live. See "What is missing" below.

## Function
Holds the scissors' fixed handle in a zip-tied trough with a V-post under
the pivot; the effector SG90's printed lever (effector_lever.py) presses the
free handle to close the blades; the hand-spring of the scissors reopens.
Bolts flat to `wrist_rotator` on the shared four-M3 bolt circle.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Scissors overall length | 170 mm generic office scissors | ASSUMED |
| Fixed handle loop outer | 45 × 30 × 6 mm | ASSUMED |
| Free handle travel at loop | ~30 mm closed→open | ASSUMED |
| Pivot boss Ø | 12 | ASSUMED |
| Trough width | 32 (loop 30 + 2 slack) | ASSUMED |
| Zip-tie slots | 2 pairs, 5 × 2.5 mm | design |
| Wrist interface | Ø32 flange normal to X on the proximal end | design |
| Bolt circle | 4 × Ø3.4 clearance, Ø22, at 45/135/225/315° | `_frame` |
| Roll axis height | 11.0 above the bed, so the lowest bolt clears it | derived |

## What is missing — read this before printing plate 6
The effector SG90 used to bolt to the old `wrist_bracket`. The wrist has been
rebuilt twice since — it is now a plain ROLL joint — so **the scissor lever's
servo has no mount**. The cradle and `effector_lever` are both correct,
printable parts and the cradle bolts to the rotator exactly like the hand
does, but nothing drives the lever yet.

Siting that servo is not a guess worth making: the lever has to swing in the
scissors' own plane, which puts the SG90's shaft along the cradle's Z, and the
free handle sits ~15 mm above the trough floor while the SG90's case is
15.9 mm deep below its own flange. Every candidate mount (a gantry over the
scissors, a tower on the +Y side, a well through the base) is decided by the
real handle height, thickness and sweep — and all six scissor numbers in the
table above are still ASSUMED.

Note the wrist rolls now, so the scissors would turn about their own long
axis rather than pitching. That is fine for cutting; it is not what the
original cradle was drawn around.

**To finish it:** measure the scissors (loop L × W × thickness, pivot boss Ø,
loop-centre-to-pivot, free-handle travel and its height above the fixed
handle), put them in the table, and the servo mount follows from them.

Until then: print plate 5 (the parallel-jaw hand), not plate 6.

## Loads & environment
SG90 stall ≈ 1.8 kg·cm → ~0.7 kg push at 25 mm lever. If the real scissors
need a firm squeeze, swap effector servo to the spare... note: spare is an
SG90 too — then shorten the lever (more force, less travel) or fit softer
scissors. First suspect if blades don't fully close.

## Print plan
PETG · flat on the bed face, trough up, no support (the only bridges are the
two wall sections over the zip-tie channels and the two Ø3.4 pin holes) ·
30 % infill. 30.4 cm³, 39 g.

## Acceptance
- [ ] invariant tests pass
- [ ] **effector servo mount designed** (blocked on measurements, above)
- [ ] flange bolts to wrist_rotator
- [ ] scissors zip-tie in; lever closes blades fully without stall
- [ ] printed and verified
