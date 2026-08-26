# wrist_mount — spec

Project: `models/robotarm/wrist_mount.py`
Status: MODELED (2026-08-24)

## Function
The bracket that carries the wrist servo. A saddle slips over the forearm's
tip from outside and takes two M3 straight through it and both of the link's
side plates; a face on its front holds the MG90S with its shaft pointing
forward down the arm, and carries the journal boss `wrist_rotator` runs on.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Forearm tip | 22.0 wide over the plates + 0.25 sliding fit | `_frame` |
| Saddle | 27 long, 3.2 walls and floor, 24 tall | design |
| Through-bolts | 2 × M3 × 30 + nyloc, at −9 and −24 from the tip | `_frame` |
| Servo face | r 22.5 × 5.0, truncated at the bed | `_frame` |
| Servo | MG90S nose-first, tabs on the face's FRONT surface | DATASHEET |
| Journal boss | r 17.0–19.5, 12 long, cut flat above 45° from the axis | `_frame` |
| Roll axis | link centreline, LINK_AXIS_Z above the link's bed face | design |
| Overall | 46.5 × 45.0 × 39.7, 15.1 cm³, 19.2 g PETG | measured |

## Why the saddle is only 27 mm long
It may only grip the PARALLEL part of the tip. The forearm's plan tapers from
the elbow channel down to `FOREARM_TIP_CHANNEL_W` and does not finish until
`FOREARM_TAPER_END`, so a longer saddle simply will not go on — the first cut
of it fouled the taper by 425 mm³.

## Why bolt-on rather than built into the link
The wrist is the piece of this machine most likely to change, and a bracket
can be re-cut on its own without reprinting a 20 cm³ link. It also leaves the
forearm's tip as the easiest shape in the project to print: two vertical
walls and a floor, no drum, no flange, no servo pocket.

## Why the boss is cut flat above 45°
So every surface on it prints inside 45° of vertical. What is left is a
V-journal open top and bottom, which still constrains the rotator in both
directions — the skirt is a full ring. That cut is also what keeps the
servo's own mounting tabs clear of the boss wall: they reach r 21.75 at the
top of their span, well outside the r 17 bore.

## Loads & environment
Carries the whole effector: ~45 g at ~60 mm, plus the payload. The two M3 are
in double shear through the link's plates. Indoor.

## Print plan
PETG · flat on the bed as modelled, saddle opening up · **no support** (every
wall is vertical, the face is a truncated vertical disc, the boss is cut at
45°) · 40 % infill, 4 walls.

## Acceptance
- [ ] invariant tests pass
- [ ] slides onto the forearm's tip; both bolts pass straight through
- [ ] MG90S seats with its lead on; rotator turns freely on the boss
- [ ] printed and verified — date, measured result, deviations
