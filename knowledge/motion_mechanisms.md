# Motion & mechanisms — designing things that move on purpose

Read when: anything articulates — arms, linkages, hinges, sliders, pan/tilt,
grippers. Component-level topics: bearings_rotation.md, gears_drives.md.
This file is the SYSTEM level: degrees of freedom, torque budgets, slop,
and range-of-motion proof.

## Degrees of freedom — count before you draw

- Write down the DOF the function needs (a gripper: 1; pan-tilt: 2; the
  robot arm: 5). Every joint beyond the needed DOF is slop, mass, and a
  servo you'll pay for; every missing DOF is a function that can't happen.
- Each joint gets exactly one moving DOF; kill the other five explicitly
  (bearing pair for moment, thrust shoulder for axial, clamped inner race
  for radial — bearings_rotation.md). "It's a bit wobbly" = a DOF nobody
  killed.
- Prefer serial simplicity (each joint carries the next) for reach;
  parallel linkages (4-bar) when the payload needs stiffness or a fixed
  orientation — a 4-bar keeps an end effector level with zero extra
  actuators.

## Torque budget — do the arithmetic, every actuated joint

For each servo/motor, worst-case hold torque:

    T = Σ (mass_i × g × horizontal_arm_i)   at the worst POSE

- Include the downstream servos' own mass — it dominates arm designs.
- Dynamic margin: ×2 on the static number for smooth moves, ×3 if it
  starts/stops fast or catches loads.
- Compare against the servo's STALL torque derated ×0.5 (hobby ratings are
  optimistic; holding near stall cooks them). SG90 ≈ 1.4 kg·cm stall →
  budget ≤ 0.7 kg·cm ≈ 0.07 N·m held.
- The budget lives in the assembly spec (Loads section) as a small table:
  joint | worst pose | arm | mass | T_required | T_available | margin.
  A joint with margin < 1 is a redesign (shorter arm, counterweight,
  spring assist, bigger servo) BEFORE any geometry.
- Counterbalance where possible: a spring or mass behind the pivot buys
  more margin than any servo upgrade (and unloads the gears at rest).

## Slop stack-up — why mechanisms feel cheap

End-effector wobble = Σ (each joint's clearance × its distance to the
tip). 0.2 mm of slop at a shoulder 200 mm from the tip is 0.2 mm × lever
ratio at the fingertip — chase slop at the joints FARTHEST from the tip
first. Weapons against slop, in order of cost:
1. bearings instead of printed pivots (kills most of it)
2. preload: axial spring washer / nyloc snugged to light drag
3. wider joint stance (two bearings far apart beat one perfect bearing)
4. tighter fit class only LAST — it buys friction along with precision.
Related: tolerance_stackup.md for the static (non-moving) version.

## Range of motion — prove the sweep, not the pose

- Model checks at BOTH extremes and the worst mid-pose, not neutral:
  `_check_fit.py` measures clearances with the joint parameter set to
  min, max, and the pose that brings parts closest.
- Sweep the moving part's envelope (bbox at N poses via script) against
  every static part + cables (cable_management.md — route through the
  axis).
- Mechanical end stops IN THE PRINT (a boss that lands on a face) at both
  ends of travel — never trust the servo's electronic limit to protect
  the structure; the stop takes the crash, sized like an impact load
  (loads_strength.md).
- Servo horn splines: model the horn from its real spline position after
  centering (ask for a photo/measure at 1500 µs); a horn mounted one
  spline-tooth off rotates the whole calibrated range.

## Linkages & transmission choices

- 4-bar for level-keeping and force amplification near toggle; slider-
  crank for linear motion from rotation; leadscrew (bought) for slow
  precise linear; belt (GT2) for fast linear. Printed linkage rules:
  steel pins/bolts at every pivot (MIN_PIN_DIA_MM floor if ever printed),
  link cross-sections per loads_strength.md (they see bending near
  toggle positions).
- Keep transmission ratios OUT of printed gears when torque matters —
  buy the reduction (servo/gearmotor), print the structure. gears_drives.md
  has the printed-gear exception rules.

## Friction & wear honesty

Printed-on-printed sliding surfaces gall under load and shed layer ridges:
acceptable for occasional adjustment, not for service motion. For service
motion: bearing, bought bushing (bronze/PTFE), or a smooth insert (steel
pin in a printed bore, the bore being the wear part — replaceable, cheap).
State the expected duty (cycles/day) in the spec; it drives the choice.
