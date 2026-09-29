# grip — the J6 gripper head (replaces the pruner)

Scripts: `grip_body.py` ×1, `grip_jaw.py` ×2, `grip_finger.py` ×2 (TPU),
`gripper_pinion.py` ×1 (reused unchanged). Numbers: `lib/grip.py`.
Gates: `_check_grip.py` (stroke, with the rods), `_check_head_sweep.py` (J4/J5 vs forearm).
Bought: 4 × Ø3 × 59 ground steel rod.

Jonathan, 2026-09-27: "finish the gripper … it needs a pretty huge redesign",
"doesn't need to have cutter", "keep the SG90".
2026-09-29 (v3): "the gripper mechanism just seems so poorly designed - could
you go out and research what the best designs are and come back and do a
revision"; "I like arms that are more circular with poliagonal lines for
texture". Chose: rod-guided rack & pinion, rods, ~64 mm head.

## What the research said
| source | what we took |
|---|---|
| [SSG-48 (Source Robotics)](https://source-robotics.github.io/SSG48-gripper-docs/page1_about_the_gripper/) | rack & pinion, centred parallel jaws — and the jaws ride on real linear guides, not printed channels |
| [Techniccontroller SG90 parallel gripper](https://techniccontroller.com/3d-printed-parallel-gripper/) | same SG90 + one pinion + two racks layout; linear stroke per degree, no arcing jaws |
| [SO-ARM100 grippers](https://deepwiki.com/TheRobotStudio/SO-ARM100/2.4.3-grippers-and-end-effectors) | compliant TPU finger option on a hobby-servo arm |
| [Fin Ray gripper (G. Manek)](https://www.gauravmanek.com/blog/2025/fin-ray-gripper/), [XLeRobot fin-ray PR](https://github.com/PickNikRobotics/moveit_pro_example_ws/pull/929) | fin ray TPU fingers wrap odd shapes with a weak servo — kept |
| [Robotiq finger explainer](https://blog.robotiq.com/bid/55922/how-do-fingers-on-the-2-finger-adaptive-robot-gripper-work) | parallel pinch + compliant finger is the working compromise |

The common failure of cheap printed grippers is **guidance**: a printed rack
sliding in a printed channel binds, wears, and lifts off the pinion under load.

## What it is (v3)
One SG90 turns a 12T pinion on its spline; it drives two racks in opposite
directions. **Each rack bar rides on two Ø3 steel rods**, one each side of the
pinion, so its centre distance to the pinion is fixed by steel and it cannot
roll into or out of mesh. The body is **one 12-sided cup** round the roll axis
(the base's dodecagon again), open at the front; everything goes in from the front.

| | |
|---|---|
| opening at the fingers | 0 → **38 mm** (touch at s = 1.0) |
| stroke per jaw | 20 mm = 127° of the SG90 |
| head | 12-gon, **65.2** across vertices / 63.0 across flats × 46.6 deep, 8 mm taper to the Ø36 rotator |
| reach past the rotator face | 97 mm to the finger tips |
| printed mass | ~64.6 g (PETG + TPU) + rods 13.1 g + SG90 9 g + screws (v2 was ~39.5 g printed) |

## v2 → v3
| v2 problem | v3 fix |
|---|---|
| rack slid plastic-on-plastic in a printed channel | two Ø3 steel rods per rack through Ø3.5 bores; nothing slides on plastic |
| a pull on the finger could rock the rack off the pinion | two rods either side of the pinion fix the rack's pitch line |
| two-part clamshell + clamp bolts | one-piece body, open front cup, no clamp bolts |
| 8-tooth rack | 6 teeth = stroke + one pitch of mesh at each end; every mm of rack is head width |
| boxy 53 × 34 shell | round 12-gon with a faceted rim and back taper, lightened by two lunes + side pocket (101.6 → 60.6 cm³) |

## Interfaces
| to | contract |
|---|---|
| wrist_rotator | 4 × M3 × 8 at (±11, ±9) into its inserts, heads 3.2 deep, driven through Ø6.2 access bores from the cup |
| SG90 | tab ledge y −11.10; 2 × M2 × 8 into Ø1.8 pilots; lead out an 8 × 8 side slot at y −24.7 |
| gripper_pinion | back face y −4.0 = seat 7.10 up the servo; gr_offset 9.20 asserted |
| rods | y ±7.85, z ±9.95; slip Ø3.5 one side wall, press Ø3.0 the other, 0.2 below both faces |
| finger | 2 × M3 × 16 from the arm back into nuts in the finger; grip face 1.0 proud |

## Assembly
1. Press two M3 nuts into each finger; bolt each finger to a jaw (M3 × 16).
2. Bolt the empty body to the rotator: 4 × M3 × 8 down the access bores with a long 2.5 key.
3. SG90 into its pocket, plug out through the side slot; 2 × M2 × 8 through the tabs.
4. Pinion onto the spline (servo centred), screw + washer.
5. Both jaws in from the front at the same opening; push the 4 rods in through the side walls (slip side first) and press flush.

## Print
| part | qty | material | orientation |
|---|---|---|---|
| grip_body | 1 | PETG green | back face down, cup up, no support |
| grip_jaw | 2 | PETG white | bar top down, no support |
| gripper_pinion | 1 | PETG white | back face down |
| grip_finger | 2 | **TPU 95A** | flat, 20–25 mm/s |

## ASSUMED / open
- Rod bores are drawn Ø3.5 (slip) and Ø3.0 (press). This printer runs small
  holes 0.1–0.3 under (gauge_broach_v2). If the jaw drags, run a Ø3.5 drill
  through the jaw bores; if a rod is loose in its press hole, a drop of CA.
- SG90 plug passes an 8 × 8 slot — ASSUMED, not measured.
- SG90 horn screw stack 2.6 (washer 0.8 + head 1.8) sets the arm's standoff.
- Fin ray section (1.6 grip beam, 1.0 ribs, TPU 95A) is HANDBOOK; grip force
  not measured. Print one finger first and squeeze it.
- `_check_loads` still budgets the old pruner head, not this one.
