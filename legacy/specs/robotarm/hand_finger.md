# hand_finger — spec

Project: `models/robotarm/hand_finger.py`
Status: MODELED (2026-08-24)

## Function
One claw finger, straight onto a servo horn. **Print two identical copies.**

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Horn mount | SG90 cross-horn pocket, 4-arm, **cut right through** | DATASHEET |
| Root radius | 18.0 — set by the 32 mm horn span, not by taste | `_hand` |
| Reach | 36.0 pivot to tip centre, tip r 7.0 | `_hand` |
| Thickness | 4.5 | `_hand` |
| Grip grooves | 3 × 1.2 mm Vs in the −Y edge, near the tip | design |
| Sweep | 35°, from 70.5° (closed) to 105.5° | derived |
| Opening | 0 → 43.3 mm | derived |
| Grip force | 0.50 kgf at stall, 0.25 at the 50 % duty limit | derived |
| Overall | 61.0 × 36.0 × 4.5, 4.4 cm³, 5.6 g PETG | measured |

## Why the pocket goes clean through
Finger R is finger L **turned over** — 180° about its own blade axis. Not
simply rotated about the shaft: a plain rotation would leave its gripping
edge facing away from the other finger. Turning it over swaps which edge
grips, and the flipped copy then meets the horn on its *other* face. So the
pocket has to be a through-cut, and the horn's own retaining screw needs a
**washer** under its head — there is no material left above it to bear on.

`test_finger_horn_pocket_goes_right_through` probes both faces of the built
solid for it.

## Why the root is an 18 mm disc
It has to swallow the SG90's 32 mm cross horn. That in turn is what sets the
pivot spacing at ±19: two 18 mm discs cannot be closer than 36 mm apart.
`test_finger_roots_cannot_foul_each_other` guards it.

## What it costs, said plainly
The fingers ROTATE, so their faces only meet flush at one opening and roll
off anything wider or narrower. Grip force is servo torque over finger
radius — shorten the reach for more force and less opening. Both numbers are
far more than a 28 g payload needs.

## Loads & environment
Bending about the thickness axis from the grip reaction, ~0.25 kgf at the
tip. Indoor.

## Print plan
PETG · flat on the bed exactly as modelled — it is a plate with a slot in
it, no overhangs anywhere · **no support** · 40 % infill, 4 walls. Lay the
blade's length along the bed's X so the layers run the right way for bending.

## Acceptance
- [ ] invariant tests pass
- [ ] both copies push onto their horns; the flipped one seats the same
- [ ] tips meet on the centreline at the closed end
- [ ] printed and verified — date, measured result, deviations
