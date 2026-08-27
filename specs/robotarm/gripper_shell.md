# gripper_shell — spec

Project: `models/robotarm/gripper_shell.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
One half of the gripper's clamshell body. It holds the gripper SG90, houses
half the pinion, carries one rack channel, and presents the flange that
bolts the whole hand to the wrist. Fulfils the "gripper split", "rack in
channel", "J5 servo mount" and "effector mount" rows of
`specs/robotarm/_assembly.md`.

**Print two, fit the second TURNED OVER** — rotated 180° about Y,
(x, y, z) → (−x, y, −z). Together they enclose the mechanism, trap the
servo, and trap the pinion axially.

## The two decisions worth explaining

**The servo mount is symmetric even though the servo is not.** An SG90's
shaft sits 6.1 mm from one end of a 22.6 mm case, so about the shaft its
tabs land at −11.0…−6.1 and +16.5…+21.4 — not mirror-symmetric. A shell
built around that outline could not be turned over. So the case pocket is
cut to the symmetric half-width 16.5 mm (the union of the layout and its
mirror) and only the **far** tab is slotted, on both sides. The servo drops
in either way round, the near tab lands in open pocket, and one design
serves both halves instead of a mirror-image pair. Cost: the case has
10.4 mm of slack in x — which is fine, because the **tabs are the datum,
not the case** (lib/servo.py).

**The servo takes no screws.** Its far tab is trapped in x and y by the
slot and in z by the two halves closing. That is stiffer than two
self-tappers into printed bosses, removes two fasteners, and means the
servo lifts straight out when the shells come apart.

## Interfaces — the dimensions that matter

| Interface | Value | Source | Joint / fit |
|---|---|---|---|
| rack channel floor | 14.70 mm from centre | derived `gr_offset + gr_rack_back + slide/2` | **sliding (0.25)** |
| rack channel half width | 4.125 mm | derived `gr_face/2 + slide/2` | sliding (0.25) |
| pinion recess radius | 10.90 mm | derived `gr_r_tip + free` | **free (0.40)** |
| pinion recess half width | 4.40 mm | derived `gr_face/2 + free` | free (0.40) |
| own arm sweep slot | x −1.0 … +26.4 mm | derived from `gr_stroke` | free (0.40) |
| other half's arm slot | x −26.4 … +1.0, to z 8.4 | derived from `gr_blade_half` | free (0.40) |
| SG90 case | 22.6 × 12.6 × 23.7 | DATASHEET | locational (0.20), symmetric pocket |
| SG90 tab span / thickness | 32.4 / 2.4 mm | DATASHEET | locational (0.20) |
| SG90 tab plane | 17.0 mm above the case bottom | DATASHEET | this is the datum |
| SG90 boss height | 4.2 mm | DATASHEET | sets the servo's y position |
| clamshell bolts | 4 × M3, x ±19, y −8 and −24 | design_rules FASTENER_MM | Ø3.4 clearance + nyloc |
| wrist flange bolts | 2 × M3 at (±11, +9), along Y | `asm_eff_bolt_x/z` | Ø3.4 clearance — was written ±16/+12 here; `gs_eff_bolt_x/z` in the script are 11.0/9.0 |
| shell half height | 16.30 mm | derived | — |

The bolts sit at y = −8 and −24 because a hole anywhere in |y| < 4.125
would pass straight through the rack channel — the channel runs the **full
width and is open at both ends**, since the rack is longer than the shell
and slides out past it at full open.

## Loads & environment
Static, indoor, low cycle. The only real load is the gear mesh's separating
force, 8.7 N × tan 20° = **3.2 N per rack**, pushing each rack against its
channel floor and so trying to part the two halves — 6.4 N total against
four M3 bolts. Not a limit by any margin; the shell is sized by printability
minimums and by the servo it has to swallow.

## Cables & service
The servo lead leaves through a 5 mm notch in the back wall, at the split
line so the two halves close around it without pinching. From there it runs
back along the forearm channel to the base. A zip-tie anchor at the wrist
bracket is the strain relief for this entry — the notch itself must never be
the thing taking a tug.

Service: four bolts and the hand opens. The servo, pinion and both racks
lift out with no other fastener touched.

## Print plan
PETG · **split face (z = 0) on the bed, built in +z** · single nozzle ·
30 % infill, 4 walls · **no support**.

Three bridges, all checked in the script against `MAX_BRIDGE_MM`:
channel floor 8.25 mm, servo bay roof 19.90 mm, and the pinion recess, which
is a semicircular arch narrowing as it rises and so self-supporting. The
0.4 mm elephant-foot chamfer goes on the split face, which is also the
mating face — so it doubles as clearance for the other half's chamfer.

## Acceptance
- [x] built and verified numerically; bridge spans asserted in the script
- [x] `_check_fit.py`: rack rides on exactly 0.125 mm each side (half the
      sliding fit) at every opening; 0.400 mm clear of the other half's rack;
      zero interference at 0/10/20/30/40 mm
- [x] `pytest tests/ -q` passes
- [ ] **gauge the SG90 tab plate first** — a 20 × 40 plate with the case
      aperture and the tab slot, 6 min. Every servo dimension here is
      DATASHEET, and five features depend on them.
- [ ] printed and verified — date, measured result, deviations

## ASSUMED / unverified
- every SG90 dimension is DATASHEET, from the vendor drawing rather than the
  servo in hand. First suspects if the servo will not seat: `gs_case_w`
  (sets the split-plane fit), `gs_tab_plane` (sets its y position),
  `gs_boss_h` (sets where the pinion lands on the horn).
- the `sliding` 0.25 channel fit is CALIBRATED but was proven in XY; this
  channel's floor is a Z-axis feature (joints_tolerances.md — a fit
  calibrated in XY is not calibrated in Z).
