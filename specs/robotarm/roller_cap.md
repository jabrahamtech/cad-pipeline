# roller_cap — the 608 retainer (print 3)

Script: `models/robotarm/roller_cap.py` · gate: `_check_base.py` · export: `plates/plate_bits_white_v1.3mf`, `roller_cap_v1`

## Interface
| to | contract | source |
|---|---|---|
| 608ZZ inner race | Ø11 face lands on the Ø8–Ø12 inner-race annulus only | `lib/bearings.B608ZZ`, asserted here |
| stator stub end | Ø8.3 × 1.3 pocket swallows the stub's 1.0 proud end (+0.3) | `lib/j1_drive.ROLLER_CAP_*`, asserted in the stator |
| M3 × 8 socket cap | Ø3.4 bore; bites 6.0 into the Ø2.5 × 7.0 stub pilot (≥ 2 d, 1.0 short of bottoming) | `ROLLER_SCREW_L_MM`, asserted in the stator |
| j1_hub cable cup | cap top z 18.6 decides the cup skirt height (skirt bottom 19.0) | `J1_CUP_SKIRT_Z_MM` derived from `ROLLER_CAP_TOP_Z_MM` |

## Why not the gauge cap
The `roller_cap` body on `gauge_fits_v4` has a Ø7.6 spigot INTO the bore. On the
stator the stub already fills that bore and stands 1.0 proud — the spigot lands
on the stub and clamps nothing. Do not use the gauge copy on the stator.

## Assembly
Rollers and caps go on BEFORE the MG995: the hex key reaches the screws radially
from the axis, which the servo occupies once fitted.

## Gate
`_check_base` places all three on their stubs with a 608 dummy and an M3 head
dummy each: 0 mm³ against the stator, the hub cup, the rotor and the ring.
