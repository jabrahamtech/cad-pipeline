# forearm — spec

Project: `models/robotarm/forearm.py`
Status: MODELED (2026-08-24) — far end rebuilt for a ROLL wrist

## Function
U-channel link from the elbow MG90S's horn to the wrist. 70 mm axis-to-axis.

Its far end is now a PLAIN RECTANGULAR CHANNEL that stops square, with two
cross-drilled M3 through both side plates. `wrist_mount` is a saddle that
slips over it and carries the wrist servo. The wrist used to pitch; it rolls,
and it bolts on.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Elbow horn mount | MG90S single-arm horn | DATASHEET |
| wrist_mount bolts | 2 × Ø3.4 through both plates, at −9 and −24 from the tip | `_frame` |
| Elbow shear | DOUBLE shear — idler stub into the elbow drum's far cap | RESOLVED |
| Near channel | ELBOW_CHANNEL_W 47, skirts r 22.0–24.5 over the elbow drum | _frame contract |
| Far channel | FOREARM_TIP_CHANNEL_W 16.0, plates 3.0 → 22.0 over the outside | _frame contract |
| Taper ends | FOREARM_TAPER_END 40.0 — the saddle can only grip past this | _frame contract |
| Roll axis | on the link centreline, z = LINK_AXIS_Z 14.0 | design |
| Link length | 70 mm axis-to-axis (parameter) | design |

## Why the tip got simple
A pitch drum had to swallow a servo lying ACROSS the arm, so the far end was
a Ø42 cylinder with two caps and a bearing seat. With the wrist servo on a
bolt-on bracket, the tip is two vertical walls and a floor. The link went
from 28.3 cm³ to 19.4 cm³ — a third of its mass, all of it at the far end,
where it costs the elbow the most.

The taper must FINISH by `FOREARM_TAPER_END`, because `wrist_mount`'s saddle
can only grip the parallel part. That is a real constraint, not tidiness —
the first saddle was longer than the parallel run and fouled the taper by
425 mm³.

## Loads & environment
Bending, lighter than upper_arm; indoor.

## Print plan
PETG · flat on side · 25 % infill.

## Acceptance
- [ ] invariant tests pass
- [ ] fits elbow horn + wrist servo
- [ ] printed and verified
