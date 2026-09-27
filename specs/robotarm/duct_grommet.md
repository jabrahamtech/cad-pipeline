# duct_grommet — upper-arm duct mouths (print 2)

Script: `models/robotarm/duct_grommet.py` · gate: `_check_bits.py` · export: `plates/plate_armstack_green_v9.3mf`

## The defect it exposed (fixed 2026-09-27)
`upper_arm`'s 14 × 19 duct was cut axis-to-axis only: both drums were solid past
their axes, so the "duct" was a sealed tunnel. `_check_bits` put a grommet in
each mouth and found it buried in solid. `upper_arm` now cuts the duct out
through both drum ends (−6174 mm³). **A printed upper_arm older than v3 has no
cable exit.**

## Interface
| to | contract |
|---|---|
| upper_arm duct | outer 14.15 × 19.15 = duct + 0.15 press; asserted equal to `ua_duct_*` when both are in one doc |
| forearm / shoulder_bracket clearance r 13.4 | outer end at 8.79 from the joint axis, where its corners meet the r 13.0 drum — nothing proud |
| M3 elbow bolt on the J3 axis | inner end 2.79 from the axis vs bolt bore r 1.70 |
| loom + zip tie | tie bar 1.6 × 2.4, 3.3 gap for a 2.5 mm tie; 11.05 open above the bar (6 mm sleeving) |

## Gate
Press film 56.06 mm³ vs analytic 59.67 (ratio 0.94 — the lead-in chamfer), bolt
dummy 0, positive control 45 mm³: PASS.
