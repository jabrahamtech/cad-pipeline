# robotarm — bench build guide

Written 2026-08-30. **This is the document `_assembly.md` promised and never
wrote:** its own order section stops at step 7 with *"steps 8–24, written once
the piece geometry exists"*. The geometry exists.

Scope, stated up front so you know what you are trusting:

- **The elbow steps are gate-backed.** Every journey in §4 steps 4–9 is
  measured by `GATE j3_installs` in `_check_elbow.py`, against a control that
  must find material. That gate exists because the geared elbow **could not be
  assembled at all** when it was first drawn — see `_HANDOFF.md` §10.
- **The rest is not.** Steps 1–3 and 10–14 are written from the geometry and
  walked on paper. Nothing measures them. Treat them as a considered proposal,
  not a proven order, and correct this file at the bench.

---

## 1. What is already printed, and what today made scrap

| part | off | mm³ each | printed g | status |
|---|---|---|---|---|
| `base_lid` | 1 | 60840 | 50.22 | printed, still good |
| `forearm` | 1 | 17618 | 14.54 | REPRINT - geared elbow: +9.60 mm of standoff, 15887.767 -> 17618.081 |
| `gripcut_finger` | 2 | 1036 | 1.71 | TO PRINT |
| `gripper_pinion` | 1 | 1609 | 1.33 | TO PRINT |
| `j3_axle` | 1 | 1092 | 0.90 | TO PRINT |
| `j3_gear` | 1 | 15565 | 12.85 | TO PRINT |
| `j3_pinion` | 1 | 2257 | 1.86 | TO PRINT |
| `j3_servo_cap` | 1 | 1748 | 1.44 | TO PRINT |
| `pruner_blade` | 2 | 1688 | 2.79 | TO PRINT |
| `pruner_rack` | 2 | 3562 | 5.88 | TO PRINT |
| `pruner_shell` | 2 | 13695 | 22.61 | TO PRINT |
| `shoulder_bracket` | 1 | 55812 | 46.07 | printed, still good |
| `shoulder_hub` | 1 | 1907 | 1.57 | REPRINT - the flanged one could not be installed (2026-08-30) |
| `turntable_ring` | 1 | 15438 | 12.74 | printed, still good |
| `turntable_stator` | 1 | 35594 | 29.38 | printed, still good |
| `upper_arm` | 1 | 45207 | 37.32 | DRILL or reprint - one O3.4 elbow bolt bore, or reprint |
| `wrist_hub` | 4 | 2816 | 9.30 | printed, still good |
| `wrist_roll` | 1 | 13352 | 11.02 | TO PRINT |
| `wrist_rotator` | 1 | 5524 | 4.56 | TO PRINT |

**To print or reprint: 83 g of PETG.**

`shoulder_hub` on the six-hub plate is the flanged one that cannot be
installed. `forearm` changed twice today and the printed one is scrap — there
is no modifying it, it grew 9.60 mm of standoff. `upper_arm` differs by
exactly one Ø3.4 hole; **drilling it is the cheap answer** (§5).

`exports/robotarm/plates/plate_remaining_v7.3mf` predates all of this and is
now wrong. Re-export before printing.

## 2. Bought parts

| item | qty | for |
|---|---|---|
| MG995 | 1 | J2 shoulder |
| MG90S | 2 | J3 elbow, J4 wrist |
| SG90 | 3 | J1 yaw, J5 roll, J6 pruner |
| 608ZZ | **4** | 3 in the turntable, **1 new** on the elbow idler |
| M3 × 40 | 1 | elbow retention, down the J3 axis |
| M3 × 16 | 2 | `j3_servo_cap` to the standoff web |
| M3 × 35 + nyloc | 2 | pruner shells |
| servo screws | 10 | 2 per servo, into Ø1.8 pilots |

The 608ZZ count went from 3 to 4. You confirmed three or more spare, so this
is not a constraint.

## 3. Sub-assemblies, built off the arm

**The elbow drive.** Do this at the bench with the parts in your hand — it is
the whole reason `j3_servo_cap` is a separate part.

1. **Trim the J3 MG90S horn's arms to r 6.0** and file the hub flush with the
   blade. Do this FIRST. The arms are 17.0 long and the pinion's root circle
   is 9.69 — an untrimmed arm breaks straight out through the teeth.
2. Press `j3_pinion` onto the trimmed horn. The bore is Ø6.95 straight
   through; the hub presses over 4.80–7.80 along it and the servo's own Ø6.0
   output boss passes freely below.
3. Drop the horn-and-pinion onto the servo spline and drive the horn's
   retaining screw **through the pinion's bore** — that is what the through
   bore buys you.
4. Fit the servo into `j3_servo_cap` from the outside, case through the
   window, tabs bearing on the outer face, two servo screws into the Ø1.8
   pilots. **Feed the lead through the keyway in the end wall as the case goes
   in**, not after.

Set the whole thing aside. It goes on last.

## 4. The build, in order

**Base and turret** — carried over from `_assembly.md`, not re-verified here.

1. Three 608ZZ onto their stub axles in `turntable_stator`; `turntable_ring`
   over them. The rotor rides on these bearings and touches the stator
   nowhere.
2. `base_lid`, and the J1 SG90 in its well. Route its lead before anything
   covers it.
3. `shoulder_bracket` onto the turret; MG995 in its pad; `shoulder_hub` on the
   drive side and a `wrist_hub` on the idler side.

**The elbow** — every step below is measured by `GATE j3_installs`.

4. **The 608ZZ goes into the forearm FIRST, before the upper arm.** It is
   pocketed from the plate's INNER face, so it is carried in along the arm
   inside the straddle and then pressed outward into its Ø21.98 pocket —
   0.010 mm of interference per side. Once the upper arm is in the fork there
   is no room to do this.
5. `j3_axle` through the bearing from the far side, its Ø11 collar landing
   inside the inner race. **The collar is not decoration:** the hex is 18.24
   across corners and the race stops at Ø12, so a flat hex face would bear on
   the OUTER race and lock the joint.
6. Upper arm into the fork, entering from behind the elbow, its +X socket
   taking `j3_axle`'s hex.
7. `j3_gear` in through the −X plate bore, its Ø20 journal in the bore and its
   hex into the upper arm's socket. Aperture on this path is clear to r 40
   against a gear of r 23.75 — **but only with the cap off.**
8. **M3 × 40 down the elbow axis** — head in the gear's counterbore, through
   the upper arm's cable duct, into `j3_axle`'s tap. Tighten it now. Nothing
   else holds the rotating group together: both of the gear's stops are
   inboard, so without this bolt the group walks apart and pulls a 3.8 hex out
   of a 3.4 socket. **With the cap on there is 1.20 mm of driver clearance and
   a bit needs 25.**
9. The elbow sub-assembly from §3 onto the standoff web, **2 × M3 × 16**,
   heads counterbored flush. Rotate the servo output to phase the pinion into
   the gear's teeth as it goes on. The heads must finish flush — the servo's
   tab plate lands on that face and spans them.

**Wrist and head** — carried over, not re-verified.

10. J4 MG90S into the forearm's +X pad; `wrist_hub` ×2 at J4.
11. `wrist_roll` in the fork; `wrist_rotator` and the J5 SG90.
12. Pruner head per `_assembly.md` steps 1–7 (it is written and proven there).
13. Route every lead into the duct and zip-tie before any cover goes on.
14. Check J3 by hand through its **90°** of travel before powering anything.
    The 2:1 halves the servo's 180°.

## 5. Trip hazards

- **Drilling the printed `upper_arm`.** Ø3.4 on the J3 axis, through the cable
  duct. The two Ø16 hex sockets at either end are the guide — if they do not
  hold the bit concentric, reprint instead. 42 g of PETG against a joint that
  comes apart.
- **The lead bundle leaves the SHORT END FACE**, at the shaft end, centred
  across the width. Five parts were notched on the wrong wall before this was
  measured.
- **J3 now swings 90°, not 180°**, and the servo sits 33.95 mm toward the
  wrist rather than on the elbow axis. Any firmware that assumes otherwise
  will drive the arm into itself.
- **Rated payload is 92 g at the jaws**, and **J2 binds it now, not J3** — the
  elbow reduction moved the bottleneck to the shoulder. `PAYLOAD_G` is still
  set to 25.

## 6. What this document does not know

- **Whether an escaped lead can reach the duct.** `_check_leads` says so
  itself. For J3 the lead now emerges at forearm (−19.90, −17.05, 0) — on the
  plate's OUTER face, 9.60 mm out from where it used to — and nothing models
  its route from there into the duct.
- **Whether the horn's arms can be found in the pinion's cross slot by feel.**
  §3 step 2 is done off the arm with clear sight of it, which is the best case,
  and it is still a press fit into a slot you cannot see the bottom of.
- **Steps 1–3 and 10–14.** Written from the geometry, walked on paper, gated
  by nothing.
- **Mesh efficiency.** `MESH_EFFICIENCY = 0.90` is assumed for a dry printed
  PETG pair. Every duty figure downstream of it moves if the real pair differs.
