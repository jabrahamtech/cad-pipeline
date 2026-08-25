# turntable_clip — spec

Project: `models/robotarm/turntable_clip.py`  ·  PRINT THREE
Status: MODELED (2026-08-23)

## Function
Stops the shoulder turntable lifting off its rollers. Bolts to turret_cap
after the disc is in place and reaches in over the disc's rim.

## Why it exists
The three 608ZZ rollers only push UP. With the arm extended, the combined
centre of mass of bracket + MG995 + arm leaves the 36 mm roller circle —
45.7 mm out with no payload, 60.4 mm with 40 g — so the disc tips onto two
rollers and lifts off the third. Without a hold-down the only thing resisting
that is the base servo's horn screw, putting ~2.2 N of axial pull into the
very output shaft the rollers were fitted to unload, and any lift shows up as
rock multiplied about 4× by the time it reaches the gripper.

Fitted afterwards rather than moulded into the cap: fixed hooks would need a
bayonet slot in the rim, and that would cap base rotation at about ±50°.

The screw is RADIAL because the annulus between the Ø96 disc and the Ø104 cap
is only 4 mm wide — no room for an M3 boss on the top face — while the cap
plate is 12 mm of solid material edge-on. That also lets an already-printed
cap take the clips by drilling three holes, with no reprint.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Bolt | 1 × M3 RADIAL into a heat-set insert in the cap's outer face, 6 mm below its top | design |
| Azimuths | 30 / 150 / 270° — between rollers, cap bolts and the wire pass | derived |
| Post inner face | clear of the Ø96 disc rim by 1.0 mm | derived |
| Tongue | reaches to r = 44, overlapping the rim by 4.0 mm | design |
| Lift clearance | 0.4 mm above the disc top | design |

## Loads & environment
~2.2 N of uplift shared between three clips, worst case. Indoor.

## Print plan
PETG · on its side, L-profile flat on the bed, so the tongue is not an
overhang · no support · 40 % infill, 3 walls.

## Acceptance
- [ ] invariant tests pass
- [ ] turntable still turns freely by hand with all three fitted, and does
      not rock when the arm is extended
- [ ] printed and verified
