# robotarm — 5-DOF desktop arm with a swappable end effector

ESP32 + breadboard live inside a Ø186 × 42 base. The arm turns on three
608ZZ bearings, not on a servo shaft.

**Styling.** The body is shaped to read as a machine rather than a stack of
plates: the base sits on a flared plinth, the turret steps up on a tapered
skirt, and both links are scalloped to a waist instead of being punched with
lightening windows. Every one of those tapers narrows going up, so none of it
costs a gram of support material. Parts are tagged for a two-tone print —
dark base and turret, light arm — which the X2D's second nozzle handles in
the same job.

Specs: `specs/robotarm/`. Shared geometry: `models/robotarm/_frame.py`.

## Servo allocation — and why

| Joint | Servo | Stall | Worst case | Load |
|---|---|---|---|---|
| Base yaw | SG90 | 1.8 kg·cm | inertia only | vertical axis, no gravity work |
| Shoulder | **MG995** | 11 kg·cm | 2.31 kg·cm (21 %) | whole arm at the longest moment arm |
| Elbow | MG90S | 2.2 kg·cm | 1.17 kg·cm (53 %) | forearm + wrist + hand |
| Wrist pitch | MG90S | 2.2 kg·cm | 0.78 kg·cm (35 %) | holds the whole hand, continuously |
| Effector | SG90 | 1.8 kg·cm | grip only | |

The MG995 is at the **shoulder**, not the base. The shoulder is the only joint
where gravity acts on the whole arm at full extension: at 150 mm reach with a
50 g payload it needs 2.31 kg·cm, and an MG90S stalls at 2.2 — it could not
hold the arm horizontal, and even empty it would sit at 60 % of stall, which
means heat, buzzing and stripped gears. Keeping the MG995 at the base would
have forced the arm down to ~85 mm reach and a 25 g payload.

The base can take the weakest servo precisely because of the bearings: it
turns about a vertical axis so gravity does no work, and the three 608ZZ
rollers take the overturning moment off the shaft. Without them the arm's
whole tipping moment would land on that gear train.

The wrist gets the second MG90S rather than an SG90 for a subtler reason: it
holds the entire end effector out at ~55 mm **continuously**, which is 43 % of
an SG90's stall but 35 % of an MG90S's — and the MG90S's metal gears do not
creep under a sustained static load the way nylon ones do. The two servos are
dimensionally identical, so this choice costs no geometry at all.

Real masses now come from `_check_loads.py`, which rebuilds every part.

## The wrist ROLLS, on a bolt-on bracket

`wrist_mount` is a **saddle that slips over the forearm's tip** and takes two
M3 × 30 straight through it and both of the link's side plates. It holds the
wrist servo nose-first, shaft pointing forward down the arm; `wrist_rotator`
turns on that shaft and the effector bolts to it.

Bracket rather than built-in, because the wrist is the piece most likely to
change and it leaves the forearm's tip a plain channel — two walls and a
floor, no drum, no flange, no servo pocket. That alone took the link from
28.3 cm³ to **19.4 cm³**.

It used to pitch, which took a yoke straddling a drum, an idler stub, a
608ZZ and a twin-lug clevis. Rolling is also far cheaper to carry: gravity
does almost no work about a roll axis, so the wrist servo sits at **3 %** of
stall instead of 11 %, and **40 g came off the very tip of the arm**.

What holds the effector up is not the servo shaft — it is the rotator's
**skirt**, running on a Ø39 journal boss on the front of the bracket.
`_check_wrist.py` measures that lap (7.3 mm) rather than assuming it, and it
probes both through-bolts for material either side.

The saddle can only grip the **parallel** part of the tip. The link's plan
tapers, and the first saddle was longer than the parallel run — it fouled the
taper by 425 mm³.

## End effectors — two, one interface

Both bolt to `wrist_rotator` on the same **4 × M3, Ø22 bolt circle**, so they
swap without reprinting anything else.

- **claw** (default, plate 5) — **two servos, one per finger**, each finger
  bolted straight to its own horn. No gears, no rack, no linkage: two printed
  designs for the whole hand. Opens **0–43.3 mm** over 35° of travel,
  **0.25 kgf per finger** at the duty limit.

  **Both fingers are the same printed part**, and the second goes on TURNED
  OVER rather than turned round — flipping it is what swaps which edge grips.
  That is the reason its horn pocket is cut clean through, and the reason the
  horn's own screw needs a washer under the head.
  `test_finger_horn_pocket_goes_right_through` probes both faces for it.

  The pivots are 38 mm apart because each finger's root has to swallow the
  SG90's 32 mm cross horn, which makes it an 18 mm disc.
  `test_finger_roots_cannot_foul_each_other` guards that.

  What it costs, plainly: the fingers **rotate**, so their faces only meet
  flush at one opening and roll off anything wider or narrower. Shorten the
  reach for more force and less opening.
- **scissors** (plate 6) — `scissor_cradle` + `effector_lever` strap scissors
  in and squeeze one handle. **Incomplete: nothing drives the lever.** See
  step 19.

## Plates — one 3MF file each

Each plate is its own Bambu Studio project file, so you can slice, tune and
queue them independently.

| File | Contains | Filament |
|---|---|---|
| `robotarm_p1_base_v1.3mf` | base_platter | 252 g |
| `robotarm_p2_lid_v1.3mf` | base_lid | 84 g |
| `robotarm_p3_turret_v1.3mf` | turret_cap + shoulder_bracket | 230 g |
| `robotarm_p4_links_v1.3mf` | upper_arm + forearm + cover | 77 g |
| `robotarm_p5_hand_v1.3mf` | wrist_mount + wrist_rotator + the claw ×3 | 57 g |
| `robotarm_p6_scissors_v1.3mf` | scissor_cradle + effector_lever — **on hold** | 37 g |

Those are SOLID masses (volume × 1.27). At the infills in the table below
expect roughly 45 % of that on the spool — call it 300–350 g for the whole
arm. Individual STEP and 3MF files per part sit alongside them.

Two-tone assignment lives in `EXTRUDER` at the top of
`models/robotarm/plates.py`; set every entry to 1 for a single-colour print.

## Printed parts

| Part | Plate | Orientation | Infill | Notes |
|---|---|---|---|---|
| base_platter | 1 | flat, bay up | 25 %, 4 walls | the long print |
| base_lid | 2 | flat, either face | 15 %, 3 walls | |
| turret_cap | 3 | flat, forks up | 25 %, 4 walls | |
| shoulder_bracket | 3 | disc down, walls up | 40 %, 4 walls | do NOT print on its side — the race face must come off the bed flat |
| upper_arm | 4 | flat | 30 % | |
| forearm | 4 | flat | 25 % | |
| wrist_mount | 5 | flat, saddle opening up | 40 %, 4 walls | slides over the forearm's tip |
| wrist_rotator | 5 | FRONT face down as modelled | 40 %, 3 walls | the flat mounting face must be the bed face |
| hand_base | 5 | flat on the bed face | 35 %, 4 walls | uprights and gussets are vertical walls |
| hand_finger ×2 | 5 | flat, blade along the bed's X | 40 %, 4 walls | print two IDENTICAL copies — fit the second TURNED OVER |
| scissor_cradle | 6 | flat, trough up | 30 % | see the warning below |
| effector_lever | 6 | flat | 30 % | see the warning below |

PETG throughout — tougher than PLA at the joints and it doesn't creep in a
warm room. Bed 70–80 °C, no chamber heat needed. **No part needs support
material.**

## Bought parts

| Item | Qty | Where |
|---|---|---|
| MG995 servo | 1 | shoulder |
| MG90S servo | 2 | elbow, wrist pitch |
| SG90 servo | 3 (+1 spare) | base yaw, and one per claw finger |
| 608ZZ bearing | 5 of 6 | 3 turntable rollers, 2 idler journals |
| M8 × 30 bolt + M8 nyloc nut | 3 | roller axles |
| M3 heat-set insert (Ø4.0 hole) | 11 | 3 cap, 4 lid, 4 in the rotator |
| M3 × 10 socket screw | 7 | cap, lid |
| M3 × 8 socket screw | 4 | effector onto the rotator |
| M3 × 30 socket screw + M3 nyloc | 2 | wrist_mount, through the forearm |
| M3 × 10 self-tapper | 2 | upper arm cover |
| Servo screws | — | supplied with each servo |
| ESP32 dev board, 400-pt breadboard | 1 each | bay |
| Toggle switch, Ø13.1 thread | 1 | rim |
| DC power cable, Ø9.7 | 1 | rim, zip-tied to the floor |
| 5 mm LED | 2 | rim, press fit |
| Zip ties, 2.5 mm | ~6 | cable strain relief |

## Assembly order

Each step names the plate its parts come from. Nothing here needs support
material, and no part is glued — the arm comes apart again.

### Plate 1 + 2 — the base and its lid
1. **Heat-set 7 M3 inserts** into base_platter: three at r=45 (they take the
   turret cap) and four at r=78 (they take the lid). Do this first; it is far
   easier with the bay empty.
2. Fit the **toggle switch** (Ø13.35 hole), the **DC cable** (Ø9.95) and the
   two **5 mm LEDs** to the rim, then zip-tie the cable to the floor through
   the two slots beside it. That is the strain relief — do not skip it, or
   every tug lands on the switch.
3. Drop the **breadboard** into the bay. The servo column's wall stops it
   inboard and the four posts hold its sides; it needs nothing else.

### Plate 3 — the turret and the shoulder
4. Drop the **base SG90** down through turret_cap's rectangular opening from
   above and screw its flange to the cap's top face (2 screws).
5. Build the **three roller assemblies**: a 608ZZ between each fork's pads,
   an M8 × 30 bolt through, an M8 nyloc snug. Each bearing must still spin
   freely afterwards — the pads clamp the bearing's INNER race only, so the
   outer race never touches the fork. If a bearing is stiff, the nut is too
   tight or a pad printed proud.
6. Lay **base_lid** on its shelf. The three cap-bolt bosses pass up through
   it, which is deliberate: the bolts land on the column, not on a 3 mm lid.
7. Bolt **turret_cap** down onto those bosses with 3 M3 screws. The lid is
   now trapped between the two, with no fasteners of its own on show.
8. Press the base servo's cross horn into **shoulder_bracket**'s underside
   pocket, set the bracket down on the three rollers, and drive the horn's
   own retaining screw up through the Ø6 bore in the middle of the disc.
   The disc should turn smoothly on the bearings with no rock.
9. Slide the **shoulder MG995** into the bracket's drum through the aperture
   in its near cap and fix it with 4 screws. Route its lead out before you
   close anything.

### Plate 4 — the two links
10. **upper_arm** goes on next. Its driven plate seats on the MG995's horn
    (captured in the cross pocket, so torque goes through the horn's arms and
    not through the little horn screws), and its idler stub on the opposite
    plate enters the bore in the drum's FAR cap. That is what makes the
    shoulder double-shear — check the stub is home before you drive the horn
    screw, or you will be loading the servo shaft alone.
11. Fit the **elbow MG90S** into upper_arm's far drum, aperture side, 2
    screws.
12. **forearm** onto the elbow horn the same way: driven plate on the horn,
    idler stub into the far cap's bore.
13. **upper_arm_cover** clips over the upper arm's channel and takes 2 M3
    self-tappers through the link's flank. Fit it AFTER the servo leads are
    routed along the channel — that is what it is hiding.

### Plate 5 — the wrist bracket and the claw
14. **wrist_mount over the forearm's tip.** It only fits over the PARALLEL
    part of the tip, so push it home until it stops. Two **M3 × 30** through
    the saddle and both side plates, nylocs on the far side. Nip them up
    firm: those two bolts are the only thing holding the wrist on.
15. **Wrist MG90S into the bracket, nose-first.** Case behind the face,
    shaft forward down the arm, two screws through the face into its tabs.
    Route the lead back along the forearm's channel now.
16. **wrist_rotator.** Heat-set its four M3 inserts FIRST, from the flat
    face — they bottom out in bosses on the back and there is no getting at
    them later. Then drop the disc on so its skirt slides over the journal
    boss and the horn lands in the cross pocket, and drive the horn's own
    screw with a **washer under the head** through the Ø6 bore. It should
    spin smoothly with no rock: that skirt, not the servo's 4.8 mm shaft, is
    what carries the whole hand.
17. **Hand onto the rotator, THEN its servos.** Four M3 × 8 through the
    hand's flange into the rotator's inserts first — a driver cannot reach
    past a fitted servo case. Then an **SG90 into each upright** from the
    front, leads out the side, two screws each.
18. **The two fingers.** They are the SAME printed part. Fit the first one;
    fit the second **TURNED OVER, not turned round** — flipping it is what
    swaps which edge grips, and its pocket is cut through so either face
    meets the horn. Put a **washer under each horn screw**: there is no
    material above it to bear on.

    **Centre both servos first** and fit both fingers at the same angle, or
    the tips will not meet. Then set each servo's closed limit where the
    tips touch and not further — past that they just push against each other
    and both sit at stall.

### Plate 6 — the scissor effector (ON HOLD — read this)
19. The scissor cradle bolts to the rotator on the **same four M3** the hand
    uses, so the two effectors still swap without touching the arm. **But
    there is nothing to drive it yet:** the effector SG90 used to bolt to the
    old wrist_bracket, and the wrist has been rebuilt twice since. Siting
    that servo depends on the real handle height, thickness and sweep of your
    scissors, and all six of those numbers are still ASSUMED — so it has
    deliberately not been invented. Measure your scissors, put the numbers in
    `specs/robotarm/scissor_cradle.md`, and the mount follows.
    Until then, print plate 5 and leave plate 6 alone.

    Note the wrist rolls now, so the scissors would turn about their own long
    axis rather than pitching.

## Things to know before you print

- **The scissors are unmeasured, and plate 6 is on hold.** Every scissor
  dimension in `scissor_cradle.py` and `effector_lever.py` is a build()
  parameter with an assumed default (generic 170 mm office scissors), and
  because of that the effector servo's mount has deliberately not been
  designed — see step 19. Measure your pair first.
- **The wrist ROLLS.** It spins the hand about the arm's own axis; it does
  not tilt it up and down. If you need the gripper to aim downward, that now
  comes from the shoulder and elbow together, not from the wrist.
- **Shoulder swing is 110°, measured.** `_check_arm.py` mates upper_arm to the
  bracket and sweeps the joint: it clears from **95° above horizontal to 15°
  below**. Two things set that, and both are now enforced in code — the link's
  web may not bridge its channel inside `LINK_WEB_CLEAR_R` (41.5 mm) of the
  shoulder axis, and the link's tail behind the axis is capped to
  `SHOULDER_TAIL_R` so it clears the turntable as the arm lifts.
- **Shoulder axis offset.** The MG995's case is centred on the turntable, not
  its shaft, so the shoulder axis sits 10.35 mm off the yaw axis. That keeps
  the bracket walls inside the Ø96 disc; it is a harmless kinematic offset.
- **Base servo shaft offset is a datasheet value.** If it is off, the
  turntable ends up slightly eccentric — cosmetic only, because the roller
  contact band tolerates ±3 mm.

## How the turntable is held on

Three things, and it is worth understanding all three before assembly:

1. **The rollers carry the weight.** Three 608ZZ bearings on M8 axles in the
   turret cap bear on the flat underside of the shoulder bracket's disc.
   That 12 mm gap you can see between the cap and the disc is the bearings.
   Their **axles point at the hub** — radially. The disc's surface moves
   tangentially over each roller, so a radial axle is the only orientation
   that rolls; a tangential one scrubs and wears a flat on the outer race.

   Two more 608ZZ go in the **idler side of the shoulder and elbow**, pressed
   into the far cap of each drum, with the link's stub running through the
   race. That side used to be a printed stub in a printed bore — plastic on
   plastic, which binds and wears the bore oval. It costs almost nothing in
   load, because a bearing on a joint axis adds mass but no moment: the
   elbow's bearing contributes exactly zero elbow torque.
2. **The horn drives it.** The base servo's cross horn is captured in a
   pocket in the disc's underside, so drive torque goes through the horn's
   arms, not through its little screws.
3. **Three clips hold it DOWN.** The rollers only push up. With the arm
   extended the combined centre of mass leaves the 36 mm roller circle
   (45.7 mm bare, 60.4 mm with a payload), so the disc would tip onto two
   rollers and lift off the third — loading the servo shaft the rollers exist
   to unload. `turntable_clip` ×3 bolts to the cap after the disc is on and
   overlaps its rim with 0.4 mm of clearance: free to turn, cannot lift.

## Wiring — how the loom gets up the arm

Four servo leads (shoulder, elbow, wrist, effector) have to cross a joint
that rotates. The route:

    bay → up beside the base servo in the column
        → through the cap's Ø14 wire pass at r=24, zip-tied there
        → a slack loop in the 12 mm gap under the disc
        → up through the turntable's centre bore, ON the axis
        → into the shoulder drum and along the links

The centre bore does double duty: it is the screwdriver access for the base
horn screw AND the wire pass. Running the bundle up the axis means turning
the base **twists** the loom rather than dragging it round, which is why
twist — not travel — is what limits base rotation. **Keep base rotation to
±90° and leave that slack loop.** From the shoulder up, the leads run inside
the link channels; the gable cover closes the upper arm over them.

## Load budget — measured, not estimated

`_check_loads.py` rebuilds every part, takes its real volume and centre of
mass, lays the arm straight out horizontal (worst case for every joint) and
works out what each servo has to hold. Gated in the test suite.

| Joint | Servo | Stall | Held | Duty |
|---|---|---|---|---|
| Shoulder | MG995 | 11.0 kg·cm | 2.21 | 20 % |
| Elbow | MG90S | 2.2 kg·cm | 1.09 | **49 %** |
| Wrist roll | MG90S | 2.2 kg·cm | 0.06 | 3 % |

Arm mass beyond the shoulder is **142 g printed** (202 g if it were solid) —
34 g less than the yoke-and-four-bar version carried, despite the wrist
bracket being a separate bolt-on part.

The wrist is in that table for completeness only. It is a ROLL joint, so
gravity does almost no work about it; the 0.06 kg·cm is what it holds with
the payload gripped 20 mm off the roll axis.
The rule applied is that a hobby servo should hold a static load at or under
50 % of stall — stall is a peak rating, not a duty rating; above that they run
hot, buzz and strip.

**Rated payload is 35 g, set by the elbow** (28 g used for the table above,
for margin). Not the shoulder, which would allow 187 g.

That is well over the 22 g the yoke-and-clevis wrist managed, and the whole
difference is mass that came off the outboard end: 54 g of yoke and drum
became a 19 g bracket plus a 12 g rotator.

If you want more, the elbow is the joint to attack, and the cheapest fix by
far is to **put the spare MG995 on the elbow** instead of the MG90S: 11.0
kg·cm against 2.2 roughly triples the ceiling. Failing that, shorten the
forearm or lighten anything outboard of it.

The plastic is nowhere near a limit — bending stress is **0.02 MPa** at the
shoulder pedestal root and both drum walls, against a deliberately
conservative 12 MPa allowable for PETG loaded across its layers. That is a
500–670× margin. These sections are sized by printability minimums, not by
load, which is normal for a printed arm this size.

## Verify before exporting

```
.venv/bin/pytest tests/ -v
PYTHONPATH=. .venv/bin/python models/robotarm/_check_assembly.py
PYTHONPATH=. .venv/bin/python models/robotarm/plates.py
```

Three assembly checks run, and all three are gated in `tests/test_robotarm.py`
because none of them can be caught by testing parts one at a time:

- `_check_assembly.py` — stacks the four base parts at their real heights and
  asserts no shared volume, that the base servo clears the floor, that the
  breadboard fits the bay, and that the roller contact ring meets solid
  turntable.
- `_check_arm.py` — mates upper_arm to shoulder_bracket, measuring the link's
  plate faces and axis height by probing rather than trusting a docstring,
  then sweeps the joint for the swing envelope and checks idler engagement.
- `_check_wrist.py` — slips the real bracket over the real link, probes both
  through-bolts for material either side, pushes the real MG90S in WITH its
  horn on, turns the rotator a full circle, and measures how far the skirt
  actually laps the journal boss.
- `_check_hand.py` — places both real servos, both real fingers and the real
  base, sweeps the fingers closed to open, and checks they clear the base and
  each other, that the tips meet, that both sit in ONE plane, and that the
  placement agrees with `_hand`'s own kinematics.
- `_check_loads.py` — rebuilds every part for its real volume and centre of
  mass and works out what each servo holds; this is what sets the rated
  payload.
- `_check_fit.py` — pushes each servo into its pocket WITH its lead attached.

Three cheap guards worth knowing about, all in `tests/test_robotarm.py`:
`test_finger_horn_pocket_goes_right_through` (a blind pocket would put the
flipped finger's mount on the wrong face), `test_finger_roots_cannot_foul_
each_other` (the pivot spacing is set by the horn, not by taste), and
`test_both_effectors_share_the_rotator_bolt_circle`, which probes the built
rotator for all four insert holes.
