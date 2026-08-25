# base_platter — spec

Project: `models/robotarm/base_platter.py`
Status: MODELED (2026-08-22)

## Function
Rounded base platter: MG90S base-yaw servo in a centre column, electronics
bay (ESP32 + 400-pt breadboard) beside it, toggle switch + DC cable strain
relief + LED holes on the opposite rim arc. Flat lid (base_lid) recessed
flush into the rim; the rounded look comes from the filleted platter rim.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Breadboard footprint | 85.5 × 55.5 mm (ridge incl; board 83.9 × 54.1) | MEASURED |
| Breadboard height | 9.3 board / 16.1 with ESP32 + wiring headroom above | MEASURED |
| Toggle switch thread Ø | 13.1 → Ø13.35 hole, rim wall 3.0 panel | MEASURED (panel thickness capacity ASSUMED ≥3) |
| DC cable outer Ø | 9.7 → Ø9.95 pass-through + zip-tie strain block | MEASURED |
| Base servo column | MG90S: rectangular, 12.45 × 23.05 inner (case + sliding clearance), 4 mm walls | DATASHEET |
| MG90S below-flange depth | 15.9 mm — case bottom lands at z=26.1, well clear of the floor | DATASHEET |
| MG90S shaft offset | 5.5 mm from the case centre | DATASHEET (race band absorbs ±3) |
| LED holes | 2 × Ø4.85 (Ø5 − press clearance) radial in the rim | DATASHEET |
| Lid interface | shelf at z=27, lid Ø171.75 sits flush; 4 × M3 heat-set boss at r=78 | design_rules |
| Turret cap interface | 3 × M3 heat-set boss at r=45, az 120/180/240 (all at x<11.5, clear of the breadboard) | derived |
| Overall | Ø176 × 30 rim height (breadboard corners r=79.5 < inner wall r=84.0) | derived |

## Loads & environment
Static + base-servo reaction torque; indoor. The Ø176 footprint resists
tipping with the arm extended — most of the mass (base, electronics) sits in
this part, low down.

## Print plan
PETG · flat, cavity up, no support (short ~20 mm internal bridge over the
column cavity is fine) · single nozzle · 25 % infill, 4 walls at the column.

## Acceptance
- [ ] invariant tests pass
- [ ] base servo drops into the column, flange screws bite; breadboard
      slides in against the column and side posts; switch nut clamps the rim;
      cable held by the floor zip ties
- [ ] printed and verified — date, measured result, deviations
