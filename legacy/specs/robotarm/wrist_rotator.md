# wrist_rotator — spec

Project: `models/robotarm/wrist_rotator.py`
Status: MODELED (2026-08-24) — replaces `wrist_bracket`

## Function
The moving half of the wrist ROLL joint. The wrist servo now sits nose-first
in the forearm's tip with its shaft pointing forward down the arm; this disc
is what that shaft turns, and the effector bolts flat to its face.

The wrist used to PITCH, which needed a yoke straddling a drum, an idler
stub, a 608ZZ and a twin-lug clevis — nine features to get right. A roll
joint needs two parts and no hardware.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Wrist horn mount | MG90S cross-horn pocket, 4-arm, in the back face | DATASHEET |
| Horn screw access | Ø6 through-bore on the axis; the horn's own screw + a washer retains the disc | design |
| Journal | Ø44.5 skirt, 2.5 wall, running on the forearm's Ø39 boss | `_frame` |
| Running clearance | 0.25 mm radial (sliding fit) | design_rules |
| Journal engagement | 7.3 mm of lap | derived, checked |
| Effector interface | 4 × M3 heat-set, Ø22 bolt circle at 45/135/225/315° | `_frame` |
| Insert depth | 8 mm, into bosses on the BACK face | design_rules |
| Overall | Ø44.5 × 14.0, 9.4 cm³, 12.0 g PETG | measured |

## Why the bolt circle is only Ø22
The inserts have to bottom out somewhere, and the only room is in bosses on
the back face. Those bosses must sit inside the journal boss's bore (r 17)
AND miss the horn's four arms. At r = 11 a Ø8.8 boss spans r 6.6–15.4 and
±24° about its own centre, so bosses at 45/135/225/315° clear arms at
0/90/180/270° (half-width 16.5° at that radius) with about 5° to spare.

## Why there is a skirt at all
Without it the whole effector hangs off the MG90S's 4.8 mm output shaft.
The skirt runs on a boss that is part of the forearm's flange, so the load
path is effector → skirt → boss → forearm and the servo only ever sees
torque. `models/robotarm/_check_wrist.py` measures the lap rather than
assuming it.

The boss is cut flat above 45° from the axis so it prints without support,
which leaves it a V-journal open top and bottom. The skirt is a full ring,
so the pair still constrains the disc in every direction.

## Loads & environment
Torque only, and very little of it: gravity does almost no work about a roll
axis because the hand is symmetric about it. `_check_loads` puts the wrist at
3 % of stall with the payload 20 mm off-axis. Indoor.

## Print plan
PETG · FRONT face down on the bed exactly as modelled — skirt, insert bosses
and horn pocket all open upward · **no support** · 40 % infill, 3 walls. The
one face that has to be flat, the effector mounting face, is the bed face.

## Acceptance
- [ ] invariant tests pass
- [ ] horn seats in the pocket; disc turns freely on the boss with no rock
- [ ] four inserts go in square and the hand bolts on without forcing
- [ ] printed and verified — date, measured result, deviations
