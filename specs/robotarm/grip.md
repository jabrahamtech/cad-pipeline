# grip — the J6 gripper head (replaces the pruner)

Scripts: `grip_shell.py` ×2, `grip_jaw.py` ×2, `grip_finger.py` ×2 (TPU),
`gripper_pinion.py` ×1 (reused unchanged). Numbers: `lib/grip.py`.
Gates: `_check_grip.py` (stroke), `_check_head_sweep.py` (J4/J5 vs forearm).

Jonathan, 2026-09-27: "finish the gripper … it needs a pretty huge redesign",
"doesn't need to have cutter", "keep the SG90".

## What it is
A parallel gripper: the SG90 turns one 12T pinion bored onto its spline, which
drives two racks in opposite directions. Each rack carries a jaw arm standing
in front of the hand, and each arm carries a **TPU fin ray finger** that wraps
the object instead of pinching it at two points.

| | |
|---|---|
| opening at the fingers | 0 → **38 mm** (touch at s = 1.0; s = 0 squeezes 1 mm each) |
| stroke per jaw | 20 mm = 127° of the SG90 |
| hand | 53 wide × 34 tall × 41 deep, tapering to 44 at the wrist |
| reach past the rotator face | 92 mm to the finger tips |
| printed mass | ~39.5 g (PETG + TPU) + SG90 9 g + screws |

## What changed from the old gripper / pruner, and why
| problem in the old head | fix |
|---|---|
| rigid V-blade jaws hold only round stock | fin ray fingers conform to stems, pots, pens |
| an SG90 stalls against a rigid jaw and cooks | the finger deflects first — command a position, not a stall |
| channel had no front wall: a pull on the jaw could walk the rack off the pinion | the jaw arm stands **in front of** the shell and its tie reaches in through a slot, so a front lip runs under the teeth |
| the rotator screws could not be reached inside a closed clamshell | each half's back wall takes two, driven through Ø6.2 access bores from the front before the jaws go in |
| identical halves need a head recess and a nut trap at the same spot | one 5.7 af hex takes either an M3 nut or a Ø5.5 head |
| pruner pinion/rack band vs servo stack never gated | `_check_grip` places the SG90 from `lib/grip` and the pinion from `gp_seat_z`, and asserts the gr_ block |

## Interfaces
| to | contract |
|---|---|
| wrist_rotator | 4 × M3 × 8 at (±11, ±9) into its inserts; bite 4.4 of a 5.5 hole |
| SG90 | tab datum y −11.10; case y −28.10..−4.40; symmetric pocket; far tab trapped |
| gripper_pinion | back face y −4.0 = seat 7.10 up the servo; gr_offset 9.20 asserted |
| finger | 2 × M3 × 16 from the arm back into nuts in the finger; grip face 1.0 proud |

## Assembly
1. Press two M3 nuts into each finger's hex pockets; bolt each finger to a jaw (M3 × 16).
2. SG90 into one shell half, lead through the side notch; close with the other half; 2 × M3 × 30 + nuts.
3. Pinion onto the spline (servo at centre), SG90 screw + washer through the front access hole.
4. Offer the hand to the rotator; 4 × M3 × 8 through the front access bores with a long 2.5 key.
5. Slide each jaw in from its side at the same opening so both mesh symmetrically.

## Print
| part | qty | material | orientation |
|---|---|---|---|
| grip_shell | 2 | PETG green | split face down, no support |
| grip_jaw | 2 | PETG white | rack back down, no support |
| gripper_pinion | 1 | PETG white | back face down |
| grip_finger | 2 | **TPU 95A** | flat, 20–25 mm/s |

## ASSUMED / open
- SG90 horn screw stack 2.6 (washer 0.8 + head 1.8) sets the arm's 7.0 standoff.
- Fin ray section (1.6 grip beam, 1.0 ribs, TPU 95A) is HANDBOOK; grip force
  not measured. Print one finger first and squeeze it.
- Finger preload 0.2-style squeeze relies on commanding s = 0; add a stall
  timeout in firmware all the same.
