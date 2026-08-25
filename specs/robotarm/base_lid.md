# base_lid — spec

Project: `models/robotarm/base_lid.py`
Status: MODELED (2026-08-22)

## Function
Flat lid closing the electronics bay, recessed flush into the platter rim.
The turret_cap clamps its middle, so it does not need to be stiff on its own.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Lid Ø | 171.75 = OUTER_DIA − 2×LID_WALL − sliding clearance | derived |
| Thickness | 3.0 mm, sits on the 2.0 mm shelf at z=27, flush at z=30 | derived |
| Column opening | Ø60 (column half-diagonal is 28.2) | derived |
| Cap-boss clearances | 3 × Ø9.5 at r=45 — bosses pass THROUGH the lid so the cap bolts land on the column, not on a 3 mm lid | design |
| Lid screws | 4 × Ø3.4 + Ø6.5 × 1.2 counterbore at r=78, into M3 inserts | design_rules |
| Vents | 12 × Ø4.0 at r=62 | design |

## Loads & environment
Static, indoor; hands rest on it. Clamped at the centre and at 4 points.

## Print plan
PETG · flat, either face down · no support · 15 % infill, 3 walls.

## Acceptance
- [ ] invariant tests pass
- [ ] drops onto the shelf without rock; boss holes clear; cap seats on top
- [ ] printed and verified
