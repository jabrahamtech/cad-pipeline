# upper_arm — spec

Project: `models/robotarm/upper_arm.py`
Status: MODELED (2026-08-22)

## Function
Tapered U-channel link from the shoulder MG995's horn to the elbow MG90S
body. 80 mm axis-to-axis. Straddles the shoulder bracket in double shear.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Shoulder horn mount | MG995 cross-horn pocket, span 54 | DATASHEET |
| Elbow MG90S pocket | 22.8 × 12.2 × 22.5 + press clearance | DATASHEET |
| Link length | 80 mm axis-to-axis (parameter) | design |
| Idler stub | Ø8 × 10 into the shoulder drum's FAR CAP (double shear) | derived |
| Near channel | SHOULDER_CHANNEL_W 51.8 = 2×(drum half 19 + horn seat 6.9) | derived |
| Near skirts | r 36.5–39.0, lapping the Ø71 shoulder drum by 6 | _frame contract |
| Far end | Ø42 elbow DRUM over ELBOW_DRUM_Y; far plates ARE its 3 mm caps | _frame contract |
| Web clearance | must not bridge inside LINK_WEB_CLEAR_R 41.5 of the shoulder axis, or the joint jams at every angle | VERIFIED by _check_arm.py |
| Tail radius | capped to SHOULDER_TAIL_R so it clears the turntable when lifted | VERIFIED |
| Swing envelope | −95° to +25° from horizontal | MEASURED |

## Loads & environment
Bending; indoor. Twin-plate or C-section so the horn side and idler side
share load.

## Print plan
PETG · flat on side · 30 % infill.

## Acceptance
- [ ] invariant tests pass
- [ ] horn screws engage; elbow servo press-seats
- [ ] printed and verified
