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
| J4 | wrist pitch | horizontal | MG90S | ±90° | fork straddling the roll housing |
| J5 | **wrist roll** | along the arm | SG90 | ±90° (loom twist) | inline rotator |
| J6 | **pruner** | rack & pinion | SG90 | 0–40 mm | rack channels |

**The effector is a cutter, not a hand.** The arm's job is pruning house
plants held in a fixture on the bench. The gripper is built, gated and kept
as a swappable head — same 4 × M3 pattern on `wrist_rotator` — but the
pruner is what the arm is now dimensioned around. See `pruner.md`.

This changes the arm's economics completely. **A shear's cutting force is
internal to the tool**, blade against counter-blade, so the ~50 N of the cut
never reaches J4, J3 or J2. And a cutter carries no payload. Payload was
40 % of the elbow moment; spending it on length instead is what took the
forearm from 40 mm to 65 mm and the reach from 125 mm to ~150 mm.

**Six DOF, and the roll is what makes the wrist buildable.** This was
5 DOF for most of the design, on the argument that a sixth joint costs
9–13 g at the end of the arm. That was true and beside the point: without a
roll joint, J4's fork has to straddle the **48 mm hand**, and every version
of that came out too wide, too heavy, or both — 94 mm and 95 g at worst.

Put a roll joint between the pitch and the hand and the fork straddles a
**24 mm roll housing** instead. The hand then bolts flat to the rotator's
face and needs no ears, trunnions or barrel at all. The sixth servo pays for
itself twice over in the part it deletes.

It also uses the inventory exactly: 1 × MG995, 2 × MG90S, 3 × SG90, no spare.

**What it costs is reach.** J3's MG90S is the bottleneck for the whole arm
and always has been:

| Forearm L2 | Reach | Payload | J3 |
|---|---|---|---|
| 40 mm | 125 mm | 25 g | 91 % |
| 55 mm | 140 mm | 18 g | 90 % |
| 65 mm | 150 mm | 12 g | 92 % |
| **65 mm** | **~150 mm** | **none - it cuts** | **82 %** |

**L2 = 65 mm is chosen and built**, on the last row. The first three are the
gripper arm and are kept for the record.

| item | printed g | r cm | g·cm |
|---|---|---|---|
| forearm | 20.6 | 2.84 | 58.5 |
| wrist_hub × 2 (J4) | 5.2 | 6.50 | 34.0 |
| wrist_roll | 12.2 | 6.73 | 82.2 |
| wrist_rotator | 5.3 | 8.48 | 45.1 |
| MG90S J4 servo | 13.4 | 5.90 | 79.1 |
| SG90 J5 roll servo | 9.0 | 6.50 | 58.5 |
| SG90 effector servo | 9.0 | 9.70 | 87.3 |
| pruner head + blades | 38.3 | ~11.2 | 429.0 |
| **total** | **113.0** | | **873.7** |

0.874 kg·cm against 1.00 — **87 %**. The four printed wrist parts' centres of mass are
**measured in assembly context**, not estimated. The head is a placeholder
at the gripper's mass and is the one soft number. **Every gram in the head
costs 1.12 % of elbow duty.**

The superseded L2 = 40 figure follows, for the record. The 91 % is no longer an estimate: it is
the moment of the built parts' own volumes, printed mass taken as 0.6 ×
solid PETG, about the J3 axis with the arm horizontal.

| item | printed g | r cm | g·cm |
|---|---|---|---|
| forearm | 13.8 | 2.0 | 27.6 |
| wrist_hub × 2 (J4) | 5.2 | 4.0 | 20.9 |
| wrist_roll | 12.2 | 4.2 | 50.7 |
| wrist_rotator | 5.3 | 6.0 | 31.9 |
| gripper, 5 parts | 31.7 | 8.5 | 269.5 |
| MG90S J4 servo | 13.4 | 3.4 | 45.6 |
| SG90 J5 roll servo | 9.0 | 4.0 | 36.0 |
| SG90 gripper servo | 9.0 | 7.0 | 63.0 |
| payload | 25.0 | 14.5 | 362.5 |
| **total** | **124.7** | | **907.7** |

0.908 kg·cm against a 1.00 kg·cm duty limit. Empty, it is 55 %. **The hand
and its payload are 70 % of that moment** — the arm's own structure is not
the problem and lightening it further buys almost nothing. The two levers
that matter are a lighter gripper and a second MG995.

The MG995 cannot move to the elbow: the shoulder always carries strictly
more than the elbow (everything the elbow carries, plus the elbow servo and
the upper arm, at a longer arm), so an MG90S there would not hold the arm up
at all. **A second MG995 is the single BOM change that would unlock full
reach at full payload** — it roughly quadruples J3's ceiling.

**J3 AND J4 are the same joint, built twice.** Both are forks straddling a
24 mm block, both journal a `wrist_hub` in a 20.35 bore, both retain it with
nothing but geometry — the hex bottoms in its socket at one end of the
travel and the flange cannot pass back through the bore at the other. Four
hubs, one design, no fasteners in either pivot. Deciding this once and
spending it twice is worth more than either joint being individually ideal.

**The forearm forks at BOTH ends, and that is forced.** The first layout had
it straddled at the elbow and forking at the wrist. It cannot be built.
Material inside the straddle has to clear the roll housing's 25.4 mm sweep
about J4, so it can only live at y < −25.4; material outboard has to clear
the upper arm's own prongs, so it can only live at y > −25.8. The two
regions do not touch, and nothing in the 0.4 mm running gap can bridge them.
Forking at both ends makes the side walls continuous from pivot to pivot.

**Both wrist servos hang outboard, staggered — J4 on +X, J3 on −X.** An
MG90S is 24.0 mm along its own shaft axis, so a servo driving an X axis
occupies 24 mm of X. Inboard is the straddle and it is spoken for. Hiding
J4's servo in the link behind a printed 1:1 spur pair was priced properly
and rejected on packaging, not on taste: its case would have had to start
28.6 mm behind the pitch axis to clear the housing's swing, putting its far
end **12.6 mm past the elbow axis**. There is no forearm short enough to
reach 125 mm and long enough to hide that servo.

The wrist is therefore **39.8 mm across the prongs, 47.8 mm across the
printed part, and 67.8 mm once the J4 servo's own body is on it**, against a
48 mm hand. That is the price of direct drive and it is
visible. Staggering the two lobes to opposite sides is what stops it reading
as a bracket bolted to one flank.

**Wrist order is pitch then roll**, which is what keeps the roll servo's
mass close to the pitch axis and lets the hand bolt to a flat face.

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
| J6 pruner | SG90 | 1.6 | 1.12 * | cutting force only | — | ~50 N at the throat |

\* the effector alone runs at 0.7 × stall, not 0.5. A cut is a brief event,
not a static hold. The cost is thermal and it is real: **a stall timeout in
the controller is a requirement of the design.** See `pruner.md`.

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

## THE OUTPUT SHAFT IS NOT IN THE MIDDLE OF THE CASE

Found 2026-08-26, on Jonathan noticing the stator's servo mounting "looked
way off" in a render. It was.

`lib/servo.py` carries `shaft_from_end` for every servo — "shaft axis to the
NEAR end of the case". Until this date **exactly one file read it**
(`servo_adapter.py`). Every other part positioned its servo by eye.

Three of the four got it right anyway:

| part | servo | case | shaft lands | |
|---|---|---|---|---|
| `shoulder_bracket` | MG995 | z −30.0 … 10.0 | z 0 | correct |
| `forearm` J4 | MG90S | y −18.0 … 6.0 | y 0 | correct |
| `forearm` J3 | MG90S | y −51.0 … −27.0 | y −45 | correct |
| `wrist_roll` | SG90 | z −16.5 … 6.1 | z 0 | correct |
| **`turntable_stator`** | **SG90** | **y ±11.3, centred** | **y +5.2** | **WRONG** |

The stator centred the *case* on J1, which puts the *shaft* 5.2 mm off the
axis. `shoulder_bracket`'s horn cross pocket is centred on the axis, so the
horn would have driven the rotor as a **5.2 mm crank** — it orbits and binds
rather than turning. This is why the base rotation "didn't make sense": as
drawn, it didn't.

Fixed by deriving `ts_shaft_off = case_l/2 − shaft_from_end` and offsetting
the aperture, the pilots and the servo pad by it, with an assertion that the
shaft lands within 1e-6 of the axis. The offset goes toward +Y, which also
moves the case away from the loom window at az 270 rather than into it.

**The lesson is not "check the servos".** It is that a datum in a shared
library which only one file reads is not a contract, it is a decoration.

## SUPERSEDED — the budget above is stale in two ways

Both found 2026-08-26 while pricing Jonathan's request to match the reference
arm's proportions. `lib/arm_budget.py` is now the authority; it reproduces the
873.7 g·cm figure above to within 0.5 g·cm, which is what makes the rest of
its output trustworthy.

**1. Every printed mass here is 12 % high.** They were computed as 0.6 ×
Fusion's "PET Plastic" density, which is 1.541 g/cm³. PETG *filament* is 1.27,
and the real solid fraction measured off an actual slice is 0.65, not 0.60 —
so 1.541 × 0.60 = 0.925 was used where the truth is 1.27 × 0.65 = 0.826.
Servos and payload are bought and unaffected. **J3 as built is 80 %, not
87 %.** Seven points of headroom were an arithmetic artefact.

**2. Shortening the links is far cheaper than this table implies, because
everything outboard of the elbow translates 1:1 with L2.** The head alone is
49 % of the elbow moment and it moves the full distance. The links themselves
are almost irrelevant — at L2 = 45 the section could go to **7.3 ×** its
current mass before J3 reaches 90 %.

| config | L1 | L2 | head | links | J3 | J2 | reach |
|---|---|---|---|---|---|---|---|
| as built, as shipped | 85 | 65 | 38.3 | 1.0× | 87 % | 44 % | 150 |
| as built, corrected | 85 | 65 | 38.3 | 1.0× | **80 %** | 41 % | 150 |
| reference proportions | 65 | 45 | 38.3 | 1.0× | 60 % | 30 % | 110 |
| **+ grip-and-cut head** | **65** | **45** | **55** | **3.0×** | **79 %** | **42 %** | **110** |

**The last row is the point.** Full reference proportions, triple-mass slab
links, and a head heavy enough to grip *and* cut, all land slightly under
where the arm sits today with thin links and a cutter that only cuts.
Working reach falls from 300 mm to 260 mm at the jaw faces.

**What this means for the design language.** `_style.md` rule 5 says "the
styling may not cost payload" and rejected cosmetic mass on the grounds that
the elbow was at 91 %. That constraint was real then and is not real now:
at L2 = 45 there is roughly 7× the link mass available. Chunky faceted links
are the *cheap* part of matching the reference. The expensive part is the
head, and the head is expensive whatever it looks like.

**Still unverified:** `UPPERARM_G_PER_MM` in `arm_budget.py` is an estimate —
`upper_arm` has never been massed. And the whole model assumes the outboard
cluster's offsets are rigid, which is true for the built parts and is an
assumption for any new head. `_check_loads.py`, which this spec has promised
since it was written, still does not exist; when it does it should replace
the constants at the top of `arm_budget.py` with real Fusion volumes and
centres of mass.

## Frame — the numbers every piece derives from

> **THIS TABLE WAS STALE IN FOUR OF ITS ROWS, found 2026-08-27.** `asm_l1`,
> `asm_l2`, `asm_eff_bolt_x` and `asm_eff_bolt_z` all disagreed with the code,
> by 20 mm, 20 mm, 5 mm and 3 mm. The parts were right and consistent with each
> other every time; only this table was wrong.
>
> That matters more than four numbers. A table headed *"the numbers every piece
> derives from"* that nothing verifies is the same failure this project has
> already paid for twice — `shaft_from_end` read by one file, `lead_bundle_dia`
> read by none. **Nothing checks these against the live Fusion parameters.**
> Until something does, treat the part scripts as authoritative and this table
> as a summary that can drift.

Shared as Fusion user parameters with the `asm_` prefix, defined
**identically** in every script that touches them
(knowledge/assembly_decomposition.md §2).

| Parameter | Value | Meaning |
|---|---|---|
| `asm_l1` | **65.0** | shoulder axis → elbow axis — was 85.0 here until 2026-08-27; the parts have built 65.0 since the link change. `ua_l1` is the live value. |
| `asm_l2` | **45.0** | elbow axis → wrist axis — was 65.0 here; `fa_l2` is the live value. |
| `asm_l3` | 68.0 | wrist axis → jaw faces at mid-opening |
| `asm_link_w` | 26.0 | outside width of both links (across the pitch axes) |
| `asm_chan_w` | 9.0 | cable channel width inside a link |
| `asm_chan_d` | 6.0 | cable channel depth |
| `asm_drum_r_j2` | 30.0 | shoulder drum outer radius |
| `asm_drum_r_j3` | 17.0 | elbow drum outer radius |
| `asm_drum_r_j4` | 17.0 | wrist drum outer radius |
| `asm_skirt_gap` | 0.40 | drum-to-skirt running clearance — `free` fit |
| `asm_eff_bolt_x` | **11.0** | effector bolt pattern, ± across the jaw axis — was 16.0 here; `gs_eff_bolt_x` and `wro_bolt_x` have both been 11.0 all along. |
| `asm_eff_bolt_z` | **9.0** | effector bolt pattern, ± across the shell split — was 12.0 here; `gs_eff_bolt_z` is 9.0. |
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

## J1 HAS A GATE NOW, AND IT FAILS — 2026-08-26

`models/robotarm/_check_j1.py`. Five parts plus three 608ZZ, an MG995 and an
SG90 as envelopes, swept −90° … +90° in 15° steps. Run `REBUILD = True`
first, then `BATCH = 0,1,2,3`; results accumulate in `_j1_sweep.json` and
batch 3 judges the whole sweep.

**Every fault it found is yaw-independent.** All four sit in the fixed half
and read identically at all thirteen poses. That is precisely why turning the
model in the viewport never showed them and why the arithmetic in the part
scripts could not: each script checked its own numbers against its own
neighbours, and no file ever held the bearing and the base plate at once.

### FAIL — the three 608ZZ foul the stator's own base plate. 218 mm³ each

`tt_axle_z` 12.0 with a Ø22 bearing puts the roller's lowest point at
**z 1.00**. `ts_plate_t` is 4.0 and the base plate spans **z 0…4**, solid
from r 10 to r 50. The lightening windows are at az 30/150/270; the rollers
are at az 90/210/330, over full plate. **The bearings cannot be fitted.**

The parameter's own comment is the tell: *"Set so the bearing clears the
platter top by 1.0 — any lower and a 608 fouls the lid."* It reasons about
the platter (z 0) and the lid (z −3…0) and never mentions the 4 mm plate the
axle is cantilevered off, which is the one thing actually in the way.

Four ways out, none free, and this is Jonathan's call:

| | change | cost |
|---|---|---|
| a | relief pocket under each roller | 3.0 deep in a 4.0 plate leaves 1.0 — under `MIN_WALL` 1.6. **Not viable as-is.** |
| b | raise `tt_axle_z` to ≥ 15.6 | bearing bottom 4.6. Moves `tt_race_z` to 26.6 and **re-datums the rotor, the ring and `sb_stand_h`**. |
| c | thin the plate to 1.6 under the roller band | keeps the datum; 1.6 of plate under a cantilevered axle carrying the whole arm. |
| d | move the windows to 90/210/330 | rollers drop through their own windows — but the cheeks stand at r 31…35, inside the window's r 22…37, so the window needs a shaped footing first. |

### FAIL — the az-90 roller also fouls the servo pad. +68 mm³

`ts_hub_y` 19.0 centred at y +5.20 puts the pad's far edge at **y +24.20**;
the az-90 roller spans r 23.5…30.5 on +Y. The stator asserts the *stub axle*
clears the pad corner and never checks the *bearing*.

### FAIL — `base_lid`'s opening is centred; the servo well is not. 132 mm³

`bl_open_y` 26.0 is cut about the origin, y **−13.0…+13.0**. `ts_shaft_off`
moved the well +5.20 on 2026-08-26, so the well now runs y **−6.20…+16.60**.
The lid masks it by 3.60 and the SG90 case fouls the lid by 3.50.

base_lid asserts `oy_mm >= STATOR_WELL_Y + 1.0` — the opening's **size**
against the well's **size**, never its **position**. The third part caught by
the same shaft-offset bug, and the first one a size-only assertion let past.

### FAIL — `tt_boss_h` is one shared parameter with two values

**4.0 mm** in `turntable_stator.py` and `turntable_ring.py`; **4.4 mm** in
`shoulder_bracket.py`, where it must equal `ring_lift + ring_t` or the ring
does not finish flush with the boss top. Nothing has ever errored because
every script that builds this stack happens to build the bracket **last**.
Rebuild the ring on its own after an edit and the rotor drops 0.4, the ring
clamps it, and J1 stops turning. PLAYBOOK, *"Redefining a SHARED user
parameter reshapes every part already built."*

### PASS — and these were worth the trip

| pair | measured | contract |
|---|---|---|
| rotor ^ roller | **0.000** at all 13 poses | it SITS on them — the crown maths is right |
| ring ^ rotor journal | **0.175** | `tr_rot` 0.35 diametral |
| MG995 ^ ring | **1.622** min | first geometric proof of `sb_stand_h`'s lower bound |
| rotor ^ stator | **1.500** | > 0 |
| MG995 ^ stator | 10.281 … 21.262 | > 0 |
| SG90 ^ rotor | 6.200 | > 0 |

**J1's full 180° is mechanically clear.** Nothing caps rotation and nothing
comes close to touching as it turns. That claim was arithmetic in three files
and is now measured. The ±90° limit stands on loom twist alone.

### ASSUMED, and so not evidence

The SG90 horn hub is modelled at **Ø6.30** because no parameter in this
project carries it, and it is what decides whether the hub clears
`tt_screw_bore` Ø6.00. The 3.02 mm³ `horn ^ rotor` reading is that guess, not
a finding. **Jonathan has SG90s in hand — caliper the hub.**


## J1 GATE: FIXED, AND NOW BLOCKED ON ONE CALIPER READING — 2026-08-26

All four faults closed. Worst interference **857.01 → 0.000 mm³**, both gate
lines PASS. What remains is 3.017 mm³ on a dimension I invented, which is a
different thing from a failure and is reported on its own line.

| | change | effect |
|---|---|---|
| `tt_axle_z` | 12.0 → **13.1** in all three files that declare it | roller bottom z 1.00 → 2.10, clear of a MIN_WALL floor with 0.50 daylight |
| `ts_relief_floor/clear/margin` | **new**, 1.6 / 0.5 / 1.0 | three arc pockets floor the plate to MIN_WALL under each roller and stop at `cheek_ir`, so the cheeks keep their whole footing |
| `ts_hub_y` | 19.0 → **16.4**, end rounded to `hub_x` | pad's furthest reach 25.82 (a corner) → 21.60 (on the axis), out of the roller band |
| `bl_open_y` / `bl_open_off_y` | 26.0 centred → **31.0 at +2.00** | contains the void union AND reaches 0.50 past the loom slot |
| `tt_boss_h` | 4.0 → **4.4** in stator and ring | one shared parameter, one value |

`tt_race_z` moves 23.00 → **24.10**, so the whole turret rises 1.1 mm. Stator
37457 → 35297 mm³ (−2160, the relief). Lid 61203 → 60901 mm³.

### The two assertions that had let it through

Both were the right idea aimed at the wrong thing.

```python
# turntable_stator: checked the bearing against the PLATTER top, z 0 ...
assert tval('axle_z') - tval('roller_od') / 2 >= 0.1
#   ... and called it "the lid", so this part's OWN 4 mm base plate,
#   sitting on that platter, was never in the comparison at all.

# base_lid: compared LENGTHS where it meant INTERVALS
assert oy_mm >= STATOR_WELL_Y + 1.0
#   26.0 >= 23.8, comfortably true, and the opening was centred while the
#   well sat at +5.20. A length cannot see an offset.
```

Both now compare the thing they meant to. `hub_r` was the third: it read
`hypot(hub_x, hub_y)` for a pad that is not centred, reporting r 21.02 for a
pad reaching 25.82.

### What the fix cost that nobody chose

Offsetting the lid opening dropped a **48 mm³ sliver** out of the lid — 1.8 mm
wide, between the opening's astern edge and the loom slot's inner radius. The
loom slot is an **arc**: its inner edge is r 13.0 on the centreline but only
y −10.65 at its angular ends, so a straight opening edge between those two
values frees the strip at the ends and leaves it standing in the middle. **A
1.8 mm rib would have passed a MIN_WALL check** — the rib was never the
problem, it was attached to nothing. A body count caught it; no dimension
would have. The rule is now a real overlap, never a wall.

### Blocked on

The SG90 horn hub, modelled at Ø6.30, against `tt_screw_bore` Ø6.00. **Caliper
a hub and re-run.** Nothing else in J1 is unmeasured geometry.


## THE LOAD GATE EXISTS — 2026-08-26

`models/robotarm/_check_loads.py`, split so the arithmetic is testable:
`lib/arm_loads.py` is pure Python with 16 headless tests, the Fusion half only
measures. It runs after `_check_ledger` batches 0–3 and **never mutates** — no
part script executes, nothing is built, no parameter is touched.

**Every mass in the table below is now read off the built body**, which is what
this spec promised when it was written.

| Joint | Required | Duty limit | of duty | margin |
|---|---|---|---|---|
| J2 shoulder | 1.66 kg·cm | 4.70 | **35 %** | 2.84 |
| J3 elbow | **0.77 kg·cm** | 1.00 | **77 %** | 1.29 |
| J4 wrist | 0.31 kg·cm | 1.00 | 31 % | 3.21 |

Total printed mass **211.8 g** across 14 parts. The measured pruner head is
**21.5 g** against the 38.3 g `arm_budget` assumes — there is more head budget
than this spec thought. Section stress is nowhere near anything: bracket legs
0 %, forearm beam 1 %, roller stub 4 %.

### The two link COMs are measured, and one estimate was already right

Both links put one joint on their origin and the other at −length in Y, so the
COM Fusion reports converts straight into a fraction:

| | was | measured | |
|---|---|---|---|
| `FOREARM_COM_FRAC` | 0.437, from the table above | **0.4686** | 7 % low |
| `UPPERARM_COM_FRAC` | 0.50, marked ESTIMATE | **0.5000** | exactly right |

Neither moves J3 much — the forearm link is 3 % of the elbow moment — but they
are facts now rather than table entries.

### J1 — what the rollers actually carry

Rotating mass **219.4 g**, overturning moment **16,556 g·mm** (which is J2's
own budget: the fork stands on the yaw axis, so what tips the turret is the
same sum).

| | |
|---|---|
| per roller, evenly shared | 73.1 g = 0.72 N |
| **worst roller, arm over it** | **481.9 g = 4.73 N** |

Three points on a circle do not share evenly when the arm reaches to one side.
The worst roller sees **6.6×** the even share, and that ratio is the finding —
a 608 is rated in kN so the bearing does not care, but it is the number the
stub axle and the cheeks have to be designed to.

### The 2026-08-26 relief, and a correction

The base plate was relieved to MIN_WALL under each roller so the 608s would fit
at all. That was called "a cantilevered axle on 1.6 mm of PETG" at the time and
**that framing was wrong.** The relief stops at `cheek_ir` — asserted in
`turntable_stator` — so the cheeks stand at r 31…35 on full 4.0 mm plate. The
thinned band is a web between the servo pad and the cheeks, loaded in shear and
bending, not a bearing pad. The stub axle root runs at 4 % of allowable.

### The cluster offsets are composed now, and they were already right

Section B0 assembles the wrist chain at the worst pose using `_check_wrist`'s
own placements, then reads each part's COM in the **assembly's** frame — so
the radius from J4 is the real distance, with no hand-derived rotation to get
backwards. That mattered: `_check_wrist`'s own hub placement went wrong exactly
that way once and put 81 mm³ of hub inside the housing at every pitch.

| part | composed | `arm_budget` declared | |
|---|---|---|---|
| `wrist_hub` | 0.00 | 0.00 | agrees |
| `wrist_roll` | 2.34 | 2.30 | agrees |
| `wrist_rotator` | 19.85 | 19.80 | agrees |

All three inside 0.05 mm. **The declared offsets were already COM-derived** —
the caveat that called them "the geometric model" overstated the problem. They
are derived rather than typed now, and they will follow the parts if a wrist
piece changes.

It places three occurrences to do this and deletes them: occurrence count and
timeline length both come back with a delta of zero, checked.

### What it deliberately does not do

No FEA. No dynamics — every figure is a static hold in the worst pose, and a
servo slewing the arm and stopping it sees more.

**The bought parts stay declared.** Three servos sit at typed offsets because
no model file contains them and there is no COM to read: 31.4 g of the 219.4 g
cluster. The pruner head is one lump at `HEAD_OFFSET_MM` 47.0 — its five pieces
are measured but not composed.


## J1 BEARING: THE ROLLERS ARE A CHOICE NOW, NOT AN INHERITANCE — 2026-08-27

Three 608ZZ on radial stub axles was carried over from the legacy build and had
**never been compared against a bought slewing bearing.** CLAUDE.md is explicit
that bearings are COTS and that the standard part should be named before one is
built out of printed geometry. A grep of the whole repo found no mention of a
slewing ring, Lazy Susan, thin-section bearing or crossed roller, ever. This
closes that.

**Decision: keep the three rollers.**

### The framing that decides it: J1 is FRICTION-limited, not load-limited

The yaw axis is vertical, so gravity contributes nothing. `_check_loads`
section D: rotating mass **219.4 g**, overturning moment **0.162 N·m**, worst
roller **4.73 N**. Those numbers are trivial for every option below — load
capacity does not discriminate at all.

What is tight is the servo. **An SG90 gives 0.80 kg·cm of duty** and spends all
of it on friction and inertia. So the selection criteria, in order:

1. **Drag** — the servo has no margin to give away.
2. **Slop** — 229 mm of reach multiplies any angular play at the base.
3. **Centre access** — 15 leads cross J1, and they cross at the axis because
   that is where twist per degree is smallest.
4. Height, cost, availability.

### The alternatives, and why each loses here

| | Drag | Slop | Height | Centre | Verdict |
|---|---|---|---|---|---|
| **3 × 608 track rollers** | **excellent** | good | ~24 mm | fully open | **KEPT** |
| Thin-section DGBB (6810-class) | excellent | **excellent** | **~7 mm** | Ø50 bore | best if starting fresh — but the platter is already printed |
| Two spaced bearings, hollow column | excellent | excellent | 40 mm+ | open if hollow | more height and parts for no gain at these loads |
| Printed race + 6 mm airsoft BBs | good | mediocre | ~12 mm | fully open | bigger circle helps moment, but adds slop and wear |
| Lazy Susan / stamped turntable | **poor, notchy** | **poor, 0.3–0.5 mm** | ~9 mm | open | **rejected first** — the two things this arm cannot absorb |
| PTFE thrust washer + journal | **bad** | good | ~3 mm | open | sliding friction would eat the SG90's budget |

**The thin-section bearing is the technically better answer on a blank sheet**
— 7 mm tall, real bearing tolerances instead of printed ones, and a Ø50 bore
that would swallow the SG90 *and* the loom, replacing rollers, ring and journal
with one bought part. It loses on a fact about this project rather than about
engineering: **the platter is printed and in hand**, with three M3 inserts fixed
at r 45, and the whole turret datums off it.

### Known weakness, and the retrofit for it

A 608's OD is a plain 7 mm cylinder pressing into a flat PETG face — **line
contact on plastic** at 4.73 N. The bearing is nowhere near its rating; the
*race face* is what will slowly groove. Purpose-made track rollers are crowned
or much wider and run on a hardened track.

**Fix, if it ever matters: bond a thin steel shim onto the race band**, turning
plastic-on-steel into steel-on-steel. Costs almost nothing and is retrofittable
after assembly, so it blocks nothing now.

### The one thing that could actually be frustrating

Not the bearing choice — **the ring's 0.40 mm lift stack**, built from two
printed Z surfaces at `DIM_TOL_Z` 0.25 each. If it comes out tight the ring
clamps the rotor and J1 will not turn. The mitigation is designed in: sand or
shim at the three posts. That is a twenty-minute annoyance once, not a
redesign, and the v1 turret print exists to find out.

### Numbers in here that are NOT measured

Every drag figure above is qualitative — no breakaway torque has been measured
for any option, **including the 608s**, which were found stiff with fresh
grease on 2026-08-26. The 6810 dimensions are from memory and want checking
against a supplier before anyone orders one.


## SERVO LEADS: `lead_bundle_dia` WAS A DECORATION — 2026-08-27

`lib/servo.py` has carried `lead_bundle_dia` for all three servos since it was
written — SG90 3.4, MG90S 3.4, MG995 4.2 — and **nothing in the project read
it.** Defined, documented, never used.

This spec already wrote the lesson, about a different field: *"a datum in a
shared library which only one file reads is not a contract, it is a
decoration."* `shaft_from_end` was read by exactly one file and the yaw servo
ended up 5.2 mm off the axis. `lead_bundle_dia` was read by none.
`models/robotarm/_check_leads.py` now reads it, which is what makes it a
contract.

### Result

| mount | host | servo | Ø lead | verdict |
|---|---|---|---|---|
| J1 yaw | `turntable_stator` | SG90 | 3.4 | **CLEAR** |
| J2 shoulder | `shoulder_bracket` | MG995 | 4.2 | **CLEAR** |
| J3 elbow | `forearm` | MG90S | 3.4 | TRAPPED — 39 % solid |
| J4 wrist | `forearm` | MG90S | 3.4 | TRAPPED — 39 % solid |
| J5 roll | `wrist_roll` | SG90 | 3.4 | TRAPPED — 81 % solid |
| effector | `pruner_shell` | SG90 | 3.4 | **CLEAR** — the control |

**Nothing in the turret print is affected.** J1 is clear: the SG90's lead
leaves below the stator's 0–4 base plate, into the platter bay.

### The control caught a wrong answer before it was believed

`pruner_shell` is the one part that already solved this — a deliberate 5.0 mm
`lead_notch` through its back wall, tagged `cable_management`. The first run of
this check reported **the effector as TRAPPED**, which is impossible if the
part is right.

It was the check that was wrong. The notch runs `z: 0 → case_w/2 + loc/2`, so
0…6.40 mm, and the probe was placed at z 8.0 — a per-part coordinate typed from
a general rule ("one lead diameter up from the case bottom") that does not hold
in a frame where the case's width lies along Z. It sat just above the notch, in
solid wall.

**Without a mount whose correct answer was already known, four false failures
would have been reported as four broken parts.** Same shape as the 608 seat row
on 2026-08-26, where a bearing held in free air was the only thing that stopped
a greasy bearing being recorded as a fault in the printing.

### What this does and does not establish

The control proves the **method**. It does not prove the other five
**placements** — each `across` coordinate is still typed per part from that
part's printed diagnostics. **A TRAPPED row means "go open that pocket", not
"that part is broken."**

Two things remain unmeasured:

- **Where the leads actually emerge.** `lib/servo.py`'s frame says the far end
  face, away from the shaft. Nobody has put a servo in hand and looked.
- **Whether an escaped lead can REACH the duct.** That is routing, and it needs
  the loom modelled. Nothing models it.

### Why the servos are outboard at all — already decided, worth restating

`forearm`'s own docstring prices the alternative: *"Hiding it in the link behind
a 1:1 gear pair was priced and rejected: the case would have had to start
28.6 mm behind the pitch axis and end 12.6 mm PAST the elbow."* And an MG995 at
40 × 20 × 36.5 cannot go inside a 26 mm link (`asm_link_w`) at any orientation.

The joints are not left open either — the **drum-and-skirt contract** covers
them at every angle. So the packaging question is settled; the gap was only ever
the last 20 mm of each lead.


## THE CONNECTOR GATE — 2026-08-27

The J1 cable route could pass wires but not the plugs on their ends. The
rotor's window is 3.4 mm wide radially (r 18.0 to `race_in` − wall) and a
standard servo plug is ~8.7 × 4.5 in cross-section — so the four leads from
servos mounted after turret assembly (J3, J4, J5, effector) could not be
threaded down to the bay without pulling the three M3s and lifting the arm
off its rollers.

**Fix: a 9.8 × 5.8 keyhole** merging with the window's inner edge at its
centre azimuth (az 270), r 12.2…18.0, cut in `shoulder_bracket`. Plugs pass
one at a time through the gate; the ribbons then lie in the 3.4 mm arc as
designed. Volume 57260 → 56760 mm³.

**The gate deliberately enters the horn-arm corridor.** The astern arm of the
horn cross pocket loses its side walls from r 12.2 to 16 — about 3.8 mm of
ONE of four arms, each of which bears over its full 16 mm. At the SG90's
0.8 kg·cm of duty the lost bearing area is nothing. Asserted in the script:
gate width vs plug +1.0, gate span vs plug +1.0, floor at the screw bore
wall, and width vs the fork plates so it cannot undercut a leg.

Re-gated after the cut: `_check_j1` full sweep 0.000 mm³ / PASS (still
BLOCKED only on the SG90 hub guess), `_check_shoulder` PASS at all eight
pitches.

**Assembly consequence, now written down:** thread each plug through the
rotor's gate top-down as its servo is installed, then drop the ribbon into
the arc window. The stator slot (7 mm wide) and the lid opening pass plugs
without help. Still unverified: the service-loop slack between the stator
and rotor windows over ±90° of yaw — the loom is not modelled.
