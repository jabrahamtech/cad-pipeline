# shoulder_bracket — spec

Project: `models/robotarm/shoulder_bracket.py`
Status: MODELED (2026-08-22)

## Function
The turntable and the shoulder drum. A Ø96 disc whose flat underside rides on
the three 608ZZ rollers, driven by the base servo's horn, carrying the
shoulder MG995 inside a cylindrical housing raised on a pedestal.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Race face | flat underside, contact ring r=36 ±3 | derived |
| Base servo horn | cross pocket, MG90S/SG90 horn 32 span × 1.6 + 0.4 | DATASHEET |
| Horn screw access | Ø6.0 bore up the disc centre | design |
| Drum radius | 35.5 (MG995 case reaches 32.2 from its shaft + 3 wall) | derived |
| Drum width | 32.0 = MG995 below-flange depth, y ∈ [−16, +16] | derived |
| Case aperture | 40.95 × 19.95 in the near cap, offset by shaft_offset | DATASHEET |
| Flange pilots | 4 × Ø3.2 on a 49.5 × 10 grid, in the near cap | DATASHEET |
| Idler bore | Ø8.25 in the FAR cap — upper_arm's stub, double shear | design |
| Shoulder axis height | 44 mm above the disc top | design |
| Shoulder axis offset | 0 — the drum fits the disc, so no offset is needed | derived |
| Arm skirt | upper_arm laps r 36.5–39.0 over this drum | _frame contract |

## Why a drum
The member holding the servo CASE carries the drum; the member driven by the
HORN carries a concentric skirt. Because both are concentric with the axis,
the joint stays visually closed at EVERY angle and neither part sweeps
anything new. A flat cover cannot do this — inside the joint's sweep radius
it jams at every angle, which is exactly what the first attempt did.

The sizing closes on its own: the MG995's below-flange depth (32.0) is the
drum width, and the horn then seats 22.9 mm from the drum centre, which is
the arm's channel half-width (46/2 = 23).

## Loads & environment
The whole arm's weight and overturning moment pass through the disc into the
rollers. Shoulder torque peaks at 2.31 kg·cm (21 % of the MG995's stall).

## Print plan
PETG · disc DOWN, drum up · no support · 40 % infill, 4 walls.
Do not print on its side: the race face must come off the bed flat.

## Acceptance
- [ ] invariant tests pass
- [ ] disc spins on the rollers without rock; MG995 seats in the drum and its
      screws bite; upper_arm's skirt turns freely over the drum
- [ ] printed and verified — date, measured result, deviations
