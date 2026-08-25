# hand_base — spec

Project: `models/robotarm/hand_base.py`
Status: MODELED (2026-08-24) — rebuilt as a two-servo claw

## Function
The claw body: bolts flat to `wrist_rotator` and carries both finger servos.
A plate and two uprights, and nothing else. See also `hand_finger.md`.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Wrist interface | 4 × Ø3.4 clearance, Ø22 bolt circle at 45/135/225/315° | `_frame` |
| Servo pockets ×2 | SG90 case + sliding clearance, through each upright | DATASHEET |
| Pivots | x = ±19.0, z = 26.0 above the mounting face | `_hand` |
| Upright | 20 wide × 4 thick, 49.4 tall; 3.8 mm of wall beside the aperture | `_hand` |
| Tab face | +Y face of the uprights; the horn stands mount_to_horn proud | `_hand` |
| Gussets | 15 mm 45° ribs on each upright's outer edge | design |
| Overall | 58.0 × 33.0 × 49.4, 11.4 cm³, 14.5 g PETG | measured |

## Why one servo per finger
It is the whole mechanism: no gears, no rack, no linkage, two printed designs
for the hand instead of five. The cost is stated in `hand_finger.md` — the
fingers rotate, so they only meet flush at one opening.

## Why the uprights are 38 mm apart
Each finger's root has to swallow the SG90's 32 mm cross horn, which makes it
an 18 mm disc, and two of those cannot be closer than 36 mm without fouling
each other.

## Why both servos face the same way
Both shafts run +Y, so both bodies hang behind the uprights and both fingers
swing in ONE plane in front of them. That also balances the hand about the
roll axis: ~18 g of servo at y = −10 against ~11 g of finger at y = +17 puts
the centre of mass within a millimetre of the axis, which is what keeps the
wrist servo idle.

## Fit the flange screws FIRST
The four M3 go in from above and are clear of both uprights, but a driver
cannot reach past a fitted servo case. Bolt the hand to the rotator before
the servos go in.

## Loads & environment
Grip reaction only, ~0.25 kgf per finger; the uprights are gusseted against
bending in Y. Indoor.

## Print plan
PETG · flat on the bed face as modelled · **no support** (uprights and
gussets are vertical walls, the gussets' hypotenuses are 45°, the apertures
are through-slots) · 35 % infill, 4 walls.

## Acceptance
- [ ] invariant tests pass
- [ ] both SG90s seat WITH their leads on
- [ ] four flange screws go in before the servos
- [ ] both fingers sweep clear and meet on the centreline
- [ ] printed and verified — date, measured result, deviations
