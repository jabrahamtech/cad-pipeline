# hand_body — spec

Project: `models/robotarm/fusion/hand_body.py` (Fusion MCP authored)
Status: DRAFT (2026-08-24)

Supersedes `hand_base` + `hand_finger` (the two-servo claw) AND absorbs
`wrist_rotator`. One printed part now does three jobs.

## Function
The whole stationary half of a one-servo hand. Its back face IS the wrist
roll joint's moving half — a journal skirt running on the forearm tip's Ø39
boss with a cross-horn pocket for the wrist servo — so the hand bolts
straight to the wrist servo and rolls with it. Forward of that it carries the
grip SG90 on an upright, and the FIXED jaw (an anvil blade) that the moving
jaw (`hand_jaw.md`) closes onto.

## Frame
    z = 0   front face of the Ø44.5 disc; the part grows +Z, forward along
            the arm. Wrist features are at z < 0.
    x       the jaw closes along X, toward the anvil face at x = −17.
    y       the grip servo's shaft runs +Y; its case hangs behind the
            upright at −Y and the jaw swings in a plane at +Y.
    Roll axis = Z through the origin.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Journal bore | Ø39.5 = WRIST_BOSS_R 19.5 ×2 + 0.25 sliding | `_frame` + design_rules |
| Journal skirt | 2.5 wall → Ø44.5 OD, 10.0 long, z −14..−4 | `_frame` ROTATOR_SKIRT_* |
| Disc | Ø44.5 × 4.0 thick, z −4..0 | `_frame` ROTATOR_T |
| Wrist horn mount | cross-horn pocket, 4-arm, 32.4 × 7.4 × 1.8 deep in the back face | lib/servo (span 32.0 + 0.4, arm 7.0 + 0.4, thick 1.6 + 0.2) |
| Horn screw access | Ø6.0 bore on the roll axis, z −4..+4; horn's own screw + washer retains the hand | `wrist_rotator` |
| Grip servo | SG90, shaft at (x 13.0, z 24.0), axis +Y, long axis along Z | ASSUMED placement |
| Servo aperture | case + 0.25 sliding, through the upright, lead notches both faces | lib/servo.case_pocket |
| Servo tab pilots | 2 × Ø1.8 at z 15.6 and 43.4 (shaft_offset 5.5 ± 13.9) | lib/servo.tab_holes |
| Upright | x 4..22, y −2..+2, z 4..47.4; 2.8 mm of wall beside the aperture | derived from the outer tab hole |
| Anvil face | x = −17.0, flat, z 22..56, y 11..24 | ASSUMED width/height |
| Anvil blade | x −22..−17 at the top, tapering to −25..−17 at the root | ASSUMED |
| Anvil foot | x −22..−8, y 4..24, z 0..4, blending onto the disc | ASSUMED |
| Jaw plane | y 15.1..19.6 = UPRIGHT_FACE_Y 2.0 + mount_to_horn 13.1 | `_hand` FINGER_PLANE_Y |
| Opening | 0 → 40.3 mm, over 110° of jaw sweep | derived, R = 30.0 |

## Why the wrist rotator is absorbed rather than bolted to
Bolting to `wrist_rotator`'s Ø22 circle costs 12 g and 14 mm at the very tip
of a 150 mm arm, and buys interchangeability this hand no longer needs once
it is the only effector. Putting the journal skirt on the hand itself keeps
the roll joint supported on the Ø39 plain bearing, so the wrist horn's four
M2 screws still see torque only — never bending from the payload.

The cost, stated plainly: effectors no longer swap. `scissor_cradle` still
carries the Ø22 bolt circle and now has nothing to bolt to; it needs either
its own skirt or `wrist_rotator` kept alive as an adapter.

## Why the aperture leaves only 2.8 mm of wall
The upright is half-width 9 rather than hand_base's 10, because the Ø6 horn
screw bore has to stay clear on the roll axis — a driver cannot come down x = 0
if the upright starts there. 2.8 mm is 7 perimeters at 0.4 mm, still well over
MIN_WALL 1.6.

## Loads & environment
Grip reaction only. 0.60 kgf at stall / 0.30 kgf at the 50 % duty limit,
applied to the anvil face. Anvil in bending about Y: σ ≈ 4 MPa against PETG's
~45 MPa, tip deflection ≈ 0.35 mm. Indoor, static.

## Print plan
PETG · disc flat on the bed, part growing up · upright and anvil are vertical
walls; the servo aperture is a through-slot whose top is a 12.5 mm bridge ·
no support · 35 % infill, 4 walls · 0.4 mm first-layer chamfer on the disc.

## ASSUMED — first suspects if it does not fit
- grip servo shaft position (13.0, 24.0) and R = 30.0 — chosen to give the
  requested 40 mm opening at a 110° sweep; not measured against a real object
- anvil face height 22..56 and width y 11..24
- anvil blade taper and foot outline
- 110° of usable SG90 travel

## Acceptance
- [ ] invariant tests pass
- [ ] skirt is a running fit on the forearm's Ø39 boss
- [ ] wrist horn seats; horn screw + washer reachable down the Ø6 bore
- [ ] grip SG90 seats WITH its lead on; both pilots take the screws
- [ ] jaw sweeps 0–110° clear of the upright, the disc and the servo
- [ ] opening measures 40 ± 1 mm at full sweep
- [ ] printed and verified — date, measured result, deviations
