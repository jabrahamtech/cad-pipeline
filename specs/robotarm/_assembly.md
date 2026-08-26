# robotarm — assembly spec

Status: CONTRACTED — gripper pieces FIT-CHECKED
<!-- DRAFT → CONTRACTED → FIT-CHECKED → ASSEMBLED -->
Written BEFORE any piece is modelled (knowledge/assembly_decomposition.md).
Supersedes the frozen build123d arm now in `legacy/` — nothing here derives
from it. Reference image: a 5-DOF desktop arm on a drum turntable
(Jonathan, 2026-08-25).

## Function & envelope

A 5-DOF desktop arm with a parallel-jaw gripper, built from the servos
already in hand: **1 × MG995, 2 × MG90S, 3 × SG90** (one SG90 stays spare)
and **6 × 608ZZ** (3 used). Shoulder-to-wrist reach **150 mm**, rated
payload **25 g**. Electronics live in the base. Every servo lead runs
inside the links, through each joint axis, under a clip-on cover.

Overall: Ø150 base × ~330 mm tall folded, ~300 mm horizontal reach from the
yaw axis to the jaw faces. Every piece prints inside the X2D single-nozzle
envelope with room to spare; the split reasons are given per piece below.

### Joint layout

| # | Joint | Axis | Servo | Range | Carried on |
|---|---|---|---|---|---|
| J1 | base yaw | vertical | SG90 | ±90° (loom twist) | 3 × 608ZZ rollers |
| J2 | shoulder pitch | horizontal | MG995 | −15° to +95° | servo shaft + printed idler stub |
| J3 | elbow pitch | horizontal | MG90S | ±90° | servo shaft + printed idler stub |
| J4 | wrist pitch | horizontal | MG90S | ±90° | servo shaft + printed idler stub |
| J5 | gripper | rack & pinion | SG90 | 0–40 mm | rack channels |

**Why pitch at the wrist and not roll.** Pitch is what lets the jaws face
down at a table without the shoulder and elbow folding into a pose that
costs reach. Roll would be cheaper to hold (gravity does no work about it)
but the shoulder+elbow can already supply the pitch that roll cannot.

**Why only 5 DOF when 6 servos exist.** A sixth joint is 9–13 g added at
the far end of the chain, and the elbow is the binding constraint (below).
The spare SG90 is worth more in the drawer than bolted to the tip.

## Load budget — J3 sets the whole design

Masses below are ESTIMATED for this spec; `models/robotarm/_check_loads.py`
replaces them with real Fusion volumes and centres of mass before any
piece exports, and this table is regenerated from that.
Duty limit = stall × 0.5 (knowledge/motion_mechanisms.md — stall is a peak
rating; held above half of it they run hot, buzz and strip).

Worst pose: **arm laid straight out horizontal, payload gripped.**

| Joint | Servo | Stall | Duty limit | T required | of duty limit | margin |
|---|---|---|---|---|---|---|
| J1 base yaw | SG90 | 1.6 | 0.80 | inertia + friction only | — | n/a |
| J2 shoulder | MG995 | 9.4 | 4.70 | 1.98 kg·cm | 42 % | 2.37 |
| J3 elbow | MG90S | 2.0 | 1.00 | **0.91 kg·cm** | **91 %** | **1.10** |
| J4 wrist | MG90S | 2.0 | 1.00 | 0.32 kg·cm | 32 % | 3.13 |
| J5 gripper | SG90 | 1.6 | 0.80 | grip force only | — | 0.5 kgf/jaw |

J3 detail (elbow at origin, everything outboard, 25 g payload):

| Item | mass | arm | moment |
|---|---|---|---|
| forearm link | 14 g | 3.2 cm | 44.8 |
| wrist bracket | 10 g | 6.5 cm | 65.0 |
| wrist MG90S | 13.4 g | 6.8 cm | 91.1 |
| **gripper assembly (incl. its SG90)** | **39.2 g** | 9.5 cm | 372.4 |
| payload | 25 g | 13.5 cm | 337.5 |
| | | | **911 g·cm** |

The gripper's 39.2 g is now MEASURED, not estimated: `_check_fit.py` reports
50.3 g of solid PETG across the five printed pieces, which is 30.2 g at
40 % infill with 4 walls, plus a 9 g SG90. That is 5 g heavier than the
estimate this spec was written on, and it took the elbow from 86 % to 91 %
of its duty limit. Everything else here is still ESTIMATED until
`_check_loads.py` exists.

**Rated payload is 25 g, and the elbow is what sets it.** The hard limit —
where J3 reaches 100 % of its duty limit — is **31.6 g**. Above that the
MG90S is holding more than half its stall torque continuously, which is how
micro servos cook themselves.

Three honest ways to raise it, in order of cost:

1. **Shorten the forearm.** L2 65 → 55 mm takes J3 to 74 % and the rated
   payload to 40 g, at the price of 10 mm of reach.
2. **Put the MG995 on the elbow** and an MG90S on the shoulder. J3's
   ceiling roughly quadruples — but J2 then needs 1.98 kg·cm against an
   MG90S's 1.00 duty limit, so it would not hold the arm up at all. Only
   viable with a second MG995.
3. **Counterweight behind the elbow.** 30 g at 40 mm behind the axis
   cancels 120 g·cm — but every gram also loads J2 and J1.

The plastic is nowhere near a limit anywhere in this arm; the sections are
sized by printability minimums and by servo torque, not by stress.

## Frame — the numbers every piece derives from

Shared as Fusion user parameters with the `asm_` prefix, defined
**identically** in every script that touches them
(knowledge/assembly_decomposition.md §2).

| Parameter | Value | Meaning |
|---|---|---|
| `asm_l1` | 85.0 | shoulder axis → elbow axis |
| `asm_l2` | 65.0 | elbow axis → wrist axis |
| `asm_l3` | 68.0 | wrist axis → jaw faces at mid-opening |
| `asm_link_w` | 26.0 | outside width of both links (across the pitch axes) |
| `asm_chan_w` | 9.0 | cable channel width inside a link |
| `asm_chan_d` | 6.0 | cable channel depth |
| `asm_drum_r_j2` | 30.0 | shoulder drum outer radius |
| `asm_drum_r_j3` | 17.0 | elbow drum outer radius |
| `asm_drum_r_j4` | 17.0 | wrist drum outer radius |
| `asm_skirt_gap` | 0.40 | drum-to-skirt running clearance — `free` fit |
| `asm_eff_bolt_x` | 16.0 | effector bolt pattern, ± across the jaw axis |
| `asm_eff_bolt_z` | 12.0 | effector bolt pattern, ± across the shell split |
| `asm_yaw_roller_r` | 34.0 | 608ZZ contact circle on the turntable |
| `asm_base_r` | 75.0 | base plinth outer radius |

**The drum-and-skirt contract** (carried over from the frozen arm because
it is the only geometry that closes a servo joint at every angle): the
piece holding a servo's CASE carries a **drum** — a cylinder concentric
with the joint axis. The piece driven by the **horn** carries a **skirt**,
an annulus lapping over that drum with `asm_skirt_gap` of running
clearance. A flat cover inside a joint's sweep radius jams at some angle;
a concentric skirt cannot.

Each drum's far cap also carries the idler bore, which puts every pitch
joint into **double shear** instead of hanging off the servo's output shaft.

## Piece tree

| Piece (component) | Role | Split reason | Material | Orientation | Spec |
|---|---|---|---|---|---|
| `robotarm_gripper_shell` ×2 | clamshell body: rack channel, half the pinion housing, servo mount, wrist flange | **identical pair, second turned over** — one design; the split also lets every cavity print without support | PETG | split face down | gripper_shell.md |
| `robotarm_gripper_pinion` | 12T m1.5 pinion on the SG90 horn | separate part: it is the wear item and reprints in 6 min | PETG | flat, teeth in-layer | gripper_pinion.md |
| `robotarm_gripper_rack_jaw` ×2 | rack bar + jaw arm + gripping blade | **identical pair, second turned over** | PETG | flat, teeth in-layer | gripper_rack_jaw.md |
| `robotarm_wrist_bracket` | J4 skirt + gripper flange | driven by the wrist horn; iteration cost — effectors change, links should not | PETG | flange face down | wrist_bracket.md |
| `robotarm_forearm` | J3 skirt → J4 drum | orientation: bending runs along the link | PETG | flat, channel up | forearm.md |
| `robotarm_forearm_cover` | closes the forearm cable channel | service: leads go in before it closes | PETG | flat | forearm_cover.md |
| `robotarm_upper_arm` | J2 skirt → J3 drum | as forearm | PETG | flat, channel up | upper_arm.md |
| `robotarm_upper_arm_cover` | closes the upper-arm channel | service | PETG | flat | upper_arm_cover.md |
| `robotarm_shoulder_bracket` | turntable disc + J2 drum, holds MG995 | the disc's race face must come off the bed flat | PETG | disc down | shoulder_bracket.md |
| `robotarm_turret_cap` | 3 roller forks + base servo mount + wire pass | service: lifts off the base | PETG | flat, forks up | turret_cap.md |
| `robotarm_turntable_clip` ×3 | holds the disc down against tipping | 3 tiny parts vs one big one | PETG | flat | turntable_clip.md |
| `robotarm_base_shell` | plinth, electronics bay, servo column | the long print; everything else can be assembled while it runs | PETG | flat, bay up | base_shell.md |
| `robotarm_base_lid` | closes the bay | service | PETG | flat | base_lid.md |

Bought (COTS — CLAUDE.md standard components, never modelled):

| Item | Qty | Note |
|---|---|---|
| MG995 servo | 1 | J2 shoulder |
| MG90S servo | 2 | J3 elbow, J4 wrist |
| SG90 servo | 2 (+1 spare) | J1 base yaw, J5 gripper |
| 608ZZ bearing | 3 of 6 | turntable rollers |
| M8 × 30 bolt + M8 nyloc | 3 | roller axles |
| M3 heat-set insert, Ø4.0 | 15 | see joint table |
| M3 × 8 / 12 / 16 socket screw | 15 | |
| M3 × 35 socket screw + nyloc | 2 | gripper clamshell through-bolts |
| Servo screws (1.8 pilot) | as supplied | every servo |
| ESP32 dev board + 400-pt breadboard | 1 | base bay |
| Toggle switch, DC barrel jack | 1 each | base rim |
| Zip ties, 2.5 mm | ~10 | strain relief at every entry |

## Joint contracts — every piece-to-piece interface

Clearances from `JOINT_FIT_MM`; shared dims are shared `asm_` parameters.

| Joint | Pieces | Type (clearance) | Shared params | Fastening |
|---|---|---|---|---|
| gripper split | shell ↔ shell | locational (0.20) on 2 dowel pips | `asm_eff_bolt_x/z` | 2 × M3 × 35 + nyloc |
| rack in channel | shell ↔ rack_jaw | **sliding (0.25)** | `gr_rack_h`, `gr_rack_face` | none — captive |
| pinion mesh | pinion ↔ rack_jaw | m1.5, 20° PA, backlash 0.20 at centre | `gr_module`, `gr_pinion_z`, `gr_backlash` | none |
| pinion on horn | pinion ↔ SG90 horn | press (0.15) on the horn outline, through-cut | — | horn's own screw + washer |
| J5 servo mount | shell ↔ SG90 | locational (0.20) on the case nose; **tab plane is the datum** | `gr_servo_*` | 2 × servo screw, 1.8 pilot |
| effector mount | shell ↔ wrist_bracket | locational (0.20) spigot | `asm_eff_bolt_x/z` | 4 × M3 × 12 into inserts |
| J4 drum/skirt | forearm ↔ wrist_bracket | **free (0.40)** | `asm_drum_r_j4`, `asm_skirt_gap` | horn + idler stub |
| J4 idler | forearm far cap ↔ wrist_bracket stub | rotating (0.35) | `asm_stub_d` | captive |
| J3 drum/skirt | upper_arm ↔ forearm | free (0.40) | `asm_drum_r_j3`, `asm_skirt_gap` | horn + idler stub |
| J2 drum/skirt | shoulder_bracket ↔ upper_arm | free (0.40) | `asm_drum_r_j2`, `asm_skirt_gap` | horn + idler stub |
| link cover | link ↔ its cover | locational (0.20) tongue-in-groove | `asm_chan_w` | 2 × M3 × 8 into inserts |
| turntable race | turret_cap rollers ↔ shoulder_bracket disc | rolling contact at `asm_yaw_roller_r` | `asm_yaw_roller_r` | none — clips hold down |
| turntable clip | turret_cap ↔ clip ↔ disc rim | free (0.40) over the rim | `asm_disc_r` | 1 × M3 × 8 into insert, each |
| cap to base | base_shell ↔ turret_cap | locational (0.20) spigot | `asm_base_r` | 3 × M3 × 16 into inserts |
| lid seat | base_shell ↔ base_lid | locational (0.20) | `asm_base_r` | 4 × M3 × 8 into inserts |

### Stack-ups (alignment crossing ≥ 3 printed dims)

1. **Pinion axis → rack pitch line, through both shells.** Loop: shell A
   channel floor → split face → shell B channel floor. Three printed dims,
   each ±0.15 (DIM_TOL_MM) → WC ±0.45, RSS ±0.26 on the centre distance.
   That is 2× the design backlash of 0.20. **Fix applied:** the pinion
   axis is set by the *servo*, which is mounted in ONE shell, not by the
   split — so the loop reduces to one channel floor per rack, ±0.15, and
   each rack meshes independently. The split face carries no mesh dimension.
2. **Jaw faces meeting square at closure.** Loop: rack A channel → jaw arm
   → face; mirrored for B. Both are the SAME printed part, so their errors
   are correlated, not independent — they meet parallel and offset, never
   skewed. Any offset is absorbed by setting the servo's closed limit.
3. **Shoulder axis height above the turntable.** shoulder_bracket disc
   thickness → pedestal height → drum bore. WC ±0.45 in Z; harmless (a
   pure kinematic offset), and no mating part references it.

## Cable plan

Bundle: 4 leads (J2–J5) each ~3.4 mm → bundle Ø ≈ 1.2 × √4 × 3.4 = 8.2 mm.
Channel Ø ≥ 1.5 × 8.2 = **12.3 mm**, met by `asm_chan_w` × `asm_chan_d`
(9 × 6 = 54 mm², vs a 8.2 mm bundle's 53 mm²) — sized as an area, and the
channel is a U so a connector can be laid in rather than fished through.

    bay → up the base servo column
        → Ø14 wire pass in turret_cap at r = 24, zip-tied there
        → slack loop in the 12 mm gap under the disc
        → up the turntable's centre bore, ON the yaw axis
        → into the shoulder drum, along the upper-arm channel
        → across J3 on the elbow axis, along the forearm channel
        → across J4 on the wrist axis, into the gripper's rear entry

Every joint crossing runs **along its own rotation axis**, so the joint
twists the lead instead of dragging it. Twist, not travel, is what limits
J1 to ±90°. Zip-tie anchor (4 × 2 slot) at every entry; 1 mm radius on
every pass-through edge; ≥ 10 mm service loop at the board.

## Assembly order — walked, not assumed

Written to be walked before any geometry exists; each step names what must
physically reach its place and which driver axis must be clear IN THAT
STATE. Steps are re-walked and corrected at Phase A step 5 of workflow 02.

**Gripper (built and proven first)**
1. Press the SG90's stock horn into `gripper_pinion`'s through-pocket;
   drive the horn's own screw with a washer under the head.
2. Screw the SG90 into shell A's servo wall (2 servo screws, from behind).
3. Lay rack_jaw #1 into shell A's channel, teeth toward the pinion.
4. Fit the pinion onto the servo spline. Centre the servo FIRST — the
   whole stroke is set from here.
5. Lay rack_jaw #2 into shell B's channel — **turned over, not turned
   round** — and close shell B onto shell A over the two dowel pips.
6. 2 × M3 × 35 through both shells, nylocs on the far side.
7. Check the stroke by hand before the arm ever sees it: both jaws must
   reach the end stops without the pinion skipping.

**Arm, wrist down to base** — steps 8–24, written once the piece geometry
exists; the rule is that every servo lead is routed and zip-tied before the
cover that hides it goes on, and every link's idler stub is seated in its
drum's far cap before the horn screw is driven.

## Fit-check plan

`models/robotarm/_check_fit.py` must print, before ANY piece exports:

- interference across every mating pair; expected contact only
- **J5 swept at 0, 20 and 40 mm opening**: rack ↔ shell, jaw ↔ jaw,
  jaw ↔ pinion, rack tail ↔ shell end stop
- every drum/skirt lap measured present at −15°, 0°, +95° of its joint
- pinion/rack centre distance measured against `gr_module × (z + 2)/2`
- the base servo's clearance to the bay floor, and the breadboard in its bay
- driver access: a Ø6 × 30 cylinder on every screw axis, interference-checked
  against every other occurrence in the ASSEMBLED state
- per-piece bbox vs ENVELOPE_SINGLE

## Gauges — printed before any full piece

- [ ] **rack/pinion mesh gauge** — a 3-tooth rack stub and the real pinion
      on a pin axle at the design centre distance. 15 min. This is the
      riskiest contract in the arm: printed involute teeth at m1.5 on an
      uncalibrated backlash. Result → `calibration/`.
- [ ] **SG90 tab-plate gauge** — a 20 × 40 plate with the case aperture and
      the two tab pilots. 6 min. Proves the DATASHEET servo numbers before
      they are baked into five pieces.
- [ ] **MG995 tab gauge** — the two supplied drawings disagree (54.0/49.5
      vs 52.8/47.8 tab span / hole pitch). Mount is slotted for both;
      gauge it before `shoulder_bracket` prints.
- [ ] **608ZZ pocket gauge** — `bearing_pocket` 0.05 is HANDBOOK, never
      gauged in PETG on this printer.

## ASSUMED / unverified values carried into geometry

| Value | Status | First suspect if... |
|---|---|---|
| SG90, MG90S envelopes | DATASHEET (vendor drawings) | the servo won't sit on its tabs |
| MG995 tab span & hole pitch | **DATASHEET, CONFLICTING** | the shoulder servo won't bolt in |
| all servo horn dimensions | DATASHEET | the pinion won't press onto the horn |
| link/piece masses in the load table | **ESTIMATED** | replaced by `_check_loads.py` |
| ESP32 + breadboard footprint | ASSUMED | the bay is the wrong size |
| 608ZZ 22/8/7, race Ø12 | DRAWING-CONFIRMED | — |

## Proven-together versions

| Date | Piece versions | Result |
|---|---|---|
| 2026-08-25 | gripper_pinion, gripper_rack_jaw, gripper_shell — all pre-export | `_check_fit.py` PASS: zero interference at 0/10/20/30/40 mm opening; jaws meet at 0.000 and clear at 0.400; rack rides on 0.125 each side; mesh 0.063–0.068 |
