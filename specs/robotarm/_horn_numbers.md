# Horn numbers on file — bench check-sheet (2026-08-27 horn audit)

Every horn dimension the CAD now believes, where it came from, and what it
drives. Caliper your actual horns (they came in the servo bags) and write
the measured value beside each. Anything off by more than ~0.2 mm: tell the
session which line, and the parts re-derive. Grades: **T** = TowerPro
official table, **M** = measured community CAD model (FreeCAD lib / Futaba
25T family), **D** = derived from other numbers, **A** = assumed, **U** =
user-supplied drawing.

## Micro horns — SG90 and MG90S (same accessory family on file)

| # | dimension | on file | grade | drives | measured |
|---|---|---|---|---|---|
| 1 | hub outer Ø | 8.00 | M | press pockets 8.15 in wrist_hub, wrist_rotator, gripper_pinion; gauge HUB bores 7.2/8.0/8.8 | ______ |
| 2 | hub height (below blade) | 3.00 | M | stator deck height (J1 horn seat), wrist relief depths 3.1/9.1 | ______ |
| 3 | blade thickness | 2.00 | M | every arm-slot depth 2.1; turret pocket depth 2.4; gauge TAB comb 2.0 slot | ______ |
| 4 | total height (hub+blade) | 5.00 | M | sanity: #2 + #3 | ______ |
| 5 | arm width near hub (r ≈ 6) | 5.50 | M | arm slots 5.65 wide in the three wrist parts; gauge ARM comb | ______ |
| 6 | arm width, outer half | 3.00 | M | turret cross pocket width 3.4 | ______ |
| 7 | 1-arm horn: centre → outermost hole | 17.00 | M | nothing yet (pin-drive reserve) | ______ |
| 8 | hole Ø | 1.40 | M | nothing structural yet | ______ |
| 9 | hole pitch along arm | 2.00 | M (two sources) | nothing structural yet | ______ |
| 10 | 4-arm cross, LONG axis tip-to-tip | 33.50 | M | turret pocket span 32.8 = trim spec (cable window caps it) | ______ |
| 11 | 4-arm cross, SHORT axis tip-to-tip | 16.00 | M | proves the cross is asymmetric; short arms float in the long slots | ______ |
| 12 | retaining screw Ø | 2.50 | A | screw bores 5.5 driver access | ______ |
| 13 | output boss Ø / height (servo, not horn) | SG90 5.0/4.2 · MG90S 6.0/6.0 | A | relief depths; MG90S total-height conflict noted in lib (official A 32.5 reads 1.5 shorter) | ______ |

## MG995 horn (Futaba 25T family — ALL of this wants the caliper before the shoulder prints)

| # | dimension | on file | grade | drives | measured |
|---|---|---|---|---|---|
| 14 | hub outer Ø | 13.80 | M | shoulder_hub clearance 14.2; the 2.0 J2 standoff exists because of this number | ______ |
| 15 | hub height | 3.80 | M | shoulder_hub bore depth 6.9; J2 stack | ______ |
| 16 | blade thickness | 2.50 | U/M | shoulder arm-slot depth 2.6 | ______ |
| 17 | arm width at r ≈ 8 | 6.50 | M | shoulder arm slots 6.65 wide, arms trimmed to r 7.6 | ______ |
| 18 | centre → outermost hole | 16.50 | M | nothing yet | ______ |
| 19 | hole Ø / pitch | 1.50 / 2.30 | M | nothing yet | ______ |
| 20 | output boss Ø / height (servo) | 13.0 / 3.0 | U | shoulder mouth 15.6 clears it; J2 stack | ______ |
| 21 | spline Ø (25T) | 5.90 | U | nothing printed touches the spline | ______ |
| 22 | Ø22 aluminium disc horn | Ø22 × 3.0, hub 8.0 total, BC Ø16, 4 holes | U | NOT USED — cannot pass the Ø20.35 fork bore; kept for reference | ______ |

## How to measure without the 0.01 caliper

Lines 1, 5, 6, 14, 17 have printed stations on **gauge_flange_v2** (HUB
bores, ARM comb, TAB comb's 2.0 slot) — drop tests beat the 0.1 mm caliper
there. Lines 2/3/4/15/16 are flat stacks: caliper across, 0.1 resolution
is enough at the tolerances involved. Lines 10, 11, 18: lay the horn on
paper, tick the tips, rule it. deshipu's warning applies to everything
here: horn dimensions vary BY BATCH — your bag is the authority, not any
datasheet, not this file.
