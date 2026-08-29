# Print plan v1 - 2026-08-29

`exports/robotarm/print/*_v1.3mf` | 15 part types, **20 pieces**, ~245 g PETG

Settings: **the same profile the gauge plate was printed on**, or the fits
stop meaning anything. PETG, 0.2 layers, 3 walls, 15-20 % infill.
Supports only where noted.

## Print the gauge first

`exports/robotarm/gauge_verify_v2.3mf`, ~29 g, about an hour.

It settles five numbers these parts are cut to, four of which have never been
near a servo: the MG90S tab pitch is DERIVED (27.5, not the 29.0 a drawing
claimed), the MG995 bed was corrected on paper, the turret's cross pocket was
re-cut to a measured taper nobody has test-fitted, and the flexure leaf has
never been sprung.

If one of those is wrong, the reprint is `forearm`, `shoulder_bracket`,
`wrist_roll`, `turntable_stator` and `gripcut_finger` - most of the arm.

## Order, once the gauge passes

| # | Part | Qty | g | Why this order |
|---|---|---|---|---|
| 1 | turntable_stator | 1 | 29.4 | J1 is the riskiest open claim - that it turns at all |
| 2 | turntable_ring | 1 | 12.7 | pairs with it; the two settle J1 together |
| 3 | shoulder_bracket | 1 | 46.1 | J1's rotor AND J2's fork - the biggest single part |
| 4 | upper_arm | 1 | 37.4 | **now 125 mm** - check it fits your bed before slicing |
| 5 | forearm | 1 | 13.1 | needs support under the +X wall and both lobes |
| 6 | wrist_roll | 1 | 11.0 | |
| 7 | wrist_rotator | 1 | 4.6 | needs heat-set inserts |
| 8 | wrist_hub | **2** | 4.6 | |
| 9 | shoulder_hub | 1 | 1.8 | |
| 10 | pruner_shell | **2** | 22.6 | clamshell - one design, second turned over |
| 11 | pruner_blade | **2** | 2.8 | |
| 12 | pruner_rack | **2** | 5.9 | |
| 13 | gripper_pinion | 1 | 1.3 | |
| 14 | gripcut_finger | **2** | 1.7 | TOP FACE DOWN or the flexure does not work |
| 15 | base_lid | 1 | 50.2 | brim on; needed last, so print it while assembling |

Stop after 1-3 and check J1 turns before committing the rest. That is ~88 g
to answer the question the whole design rests on.

## Orientations that are not obvious

- **turntable_stator** - base down, cheeks and posts UP. The stub axles then
  bridge sideways off the cheeks. **Supports off**: that bridge is
  load-bearing and support scars it.
- **shoulder_bracket** - -X face down. Both journal bores come out vertical
  and round. The disc stands on edge, which is wrong for the race face and
  the O68 journal. If either proves out of round, split the part on the boss
  top plane and bolt it together.
- **gripcut_finger** - TOP FACE DOWN, z +9.55 on the bed. Layers then lie
  ALONG the leaf so bending stress is in-plane. Printed any other way the
  flexure delaminates.
- **pruner_rack** - back face down, not teeth down: teeth down needs support
  for the drive pin.
- **base_lid** - brim on. 171.75 across and 3 thick, it will warp without one.
- **turntable_ring** - the bore IS the J1 journal. Do not sand it.

## Bought parts

1 x MG995, 2 x MG90S, 3 x SG90, 3 x 608ZZ, M3 hardware, heat-set inserts for
`wrist_rotator`.

## What is NOT settled by any of this

The arm is 60 mm longer than the version any of these numbers were first
written for, and every load figure in the project is STATIC - no slew, no
stop, no impact, no FEA. Section stress at the loaded roots is 1 % of
allowable, so strength was never the limit. Stiffness is, and nothing models
it. The elbow also sits at 87 % of its duty limit, which only passes because
the load gate now counts the clamshell twice; anything added to the hand
comes out of that.
