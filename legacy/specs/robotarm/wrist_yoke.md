# wrist_yoke — spec

Project: `models/robotarm/fusion/wrist_yoke.py` (Fusion MCP authored)
Status: MODELED (2026-08-24)

## Function
The link that CLIPS OVER the printed arm shell (dark-green print) from
outside and pitches with its SG90: one ear screws flat onto the servo horn
proud of the shell's outer face, the other carries a stub axle reaching
inward into the bearing in the far wall — double shear.

The roll joint is POWERED, kit-style: an open cradle on TOP of the bridge
holds the roll SG90 (dropped in shaft-up, its two tabs screwed to the end
wall tops with the supplied self-tappers, lead notches in both side walls).
The shaft sits on the arm centreline and the gripper bolts to the horn
above. Arm below, servo in the middle, gripper on top.

Revision history: inside-the-gap clevis → clip-over (Jonathan: bracket
wraps the arm; horn and bearing live on the shell's OUTER faces) → passive
roll spigot → servo-in-gripper fixed horn → top cradle (Jonathan: mount the
motor on top, gripper attaches to it, arm below). The cradle adds wrist
length but is the simplest to assemble and service, and nothing intrudes
into the shell's pitch sweep.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Shell outer width | 35.0 mm across the flats | USER (caliper pending) |
| Horn-side ear inner face | at horn top plane = 35/2 + standoff 4.0 + horn 1.6 | **ASSUMED** standoff |
| Horn attach | flat mount, 4 × Ø2.2 on Ø14 BCD (M2 into horn arm holes), Ø9 hub/screw bore | DATASHEET + design |
| Far-side bearing | 608ZZ, OD 22 × ID 8 × W 7, outer face flush with shell | **ASSUMED** |
| Bearing-side ear | inner face at 35/2 + 0.25 sliding, Ø8.2 through-hole | design_rules |
| Bearing axle | M8 × 20 bolt + M8 washer (BOUGHT), rides the 608 bore | COTS |
| Ear end radius | 18.0 about the pivot axis | **ASSUMED** |
| Pivot axis → front face | 22.0 (front bridge must clear the shell's end) | **ASSUMED** |
| Ears / bridge | 4.0 ears, 6.0 bridge, both 30 tall | design |
| Roll-servo cradle | FULL-WIDTH block flush with the ears (48.85 across); inner pocket 23.05 × 12.45 × 15.9 | DATASHEET + design_rules |
| Wire notches | 7 × 9 high, cut clear through both cradle flanks | design |
| Cradle shaft position | SG90 shaft on the arm centreline (case centre +5.5 off it) | lib/servo.py |
| Tab screw pilots | 2 × Ø1.8 × 6 in the end wall tops, at −8.4 / +19.4 from the shaft | lib/servo.tab_holes |
| Lead notches | 7 × 2.6 × 7 high, both side walls | lib/servo constants |
| Gripper interface | roll SG90 cross horn, ~29 above the bridge face | DATASHEET |

## Loads & environment
Carries gripper + payload (~60 g at ~50 mm) about the pitch axis; torque via
M2 screws in shear at r 7 — ~2.5 kgf total at SG90 stall, fine. Indoor.

## Print plan
PETG · cradle rim DOWN (part upside-down): cradle walls and both ears print
as vertical walls, every hole is in a vertical wall, ear round-offs are
top arcs · support only in the one 15.9 mm gap under the bridge face
(non-mating surface); the cradle's servo seat spans 12.5 mm between walls
and bridges cleanly · verified fit: SG90 case/tabs/horn sweep all 0.00 mm³
interference (2026-08-24) · 40 % infill, 4 walls.

M8 change (2026-08-24): printed stub axle replaced by an M8 × 20 bolt and
washer through a plain Ø8.2 ear hole — no more horizontal-cylinder
overhang, and the bearing surface is steel on steel instead of a printed
stub's support-side finish.

## Acceptance
- [ ] invariant tests pass
- [ ] ears straddle the shell with sliding fit; stub seats fully in the bearing
- [ ] horn screws land in horn arm holes at any 90° orientation
- [ ] full servo travel without the bridge fouling the shell end
- [ ] printed and verified — date, measured result, deviations
