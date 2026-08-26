# pruner — spec

The effector, replacing the gripper. Bolts to `wrist_rotator`'s 4 × M3
pattern (±11, ±9), so the gripper stays a swappable alternative head and
none of that work is thrown away.

Not yet built. This spec is written first, deliberately — the forearm was
not, and it cost two rebuilds.

## Function

A **bypass pruning shear** for house-plant stems. The plant is held in a
fixture on the bench; the arm positions the head, closes it, and cuts.

**Bypass, not anvil.** An anvil cutter needs roughly half the force for the
same stem and is much easier to build — one edge against a flat. It also
crushes the stem it cuts. On a living plant that is a wound that heals badly
and invites rot. Bypass costs force and is the horticulturally correct
answer, so bypass it is, and the force has to be found elsewhere.

**The reaction is internal.** Blade acts against counter-blade; both are on
the tool. The arm feels the head's weight and whatever it takes to seat the
stem in the throat, not the ~50 N of the cut. This is the whole reason a
1.0 kg·cm elbow can drive a cutter at all. A **drag** cutter — a blade
pulled along a line — would react straight back through J3 and J2 and is
not possible on this arm at any size.

## The force problem

Everything below is at the effector SG90: 1.6 kg·cm stall, `gr_r_pitch` 9.0,
mesh and horn efficiency taken at 0.7.

| | |
|---|---|
| rack force, 0.5 × stall (holding) | 6.1 N |
| rack force, 0.7 × stall (cutting) | 8.5 N |
| sharp bypass blade in green tissue | ≈ 10 N per mm of stem |
| so, as built, parallel jaws cut | **0.85 mm** |

**0.7 × stall is a deliberate departure** from the ×0.5 in
`knowledge/motion_mechanisms.md`. That derate is for holding a load
indefinitely; a cut is a brief event. The cost is thermal: an SG90 held
against a stem it cannot cut will cook in tens of seconds. **A stall
timeout in the controller is a safety requirement of this design, not a
nicety** — see Acceptance.

### Why not just angle the blades and skip the lever

Because it does not reach. Angled bypass blades bolted to the jaws that
already exist are ONE new part, reuse a gated shell and pinion, and were the
first thing tried on paper. With no mechanical advantage they deliver 8.5 N
and rely entirely on scissor progression:

| progression | effective | stem |
|---|---|---|
| ×2 | 17.1 N | 1.7 mm |
| ×3 | 25.6 N | 2.6 mm |
| ×4 | 34.2 N | 3.4 mm |

Even taking the optimistic ×4 that is a seedling, not a house plant. The
lever is not optional.

### The lever, solved rather than sketched

`lib/pruner_linkage.py` searches pivot position, tail length and sweep
against four hard constraints — the tail clears the pinion by ≥ 1.0 mm
through the whole sweep, the tail stays inside the clamshell, the throat
opens ≥ 10 mm, and rack travel fits the 20.0 mm the gripper already uses.
61 layouts survive. `CHOSEN` is the one with the most advantage at the
throat root, and `tests/test_pruner_linkage.py` holds it to all four.

| | |
|---|---|
| blade pivot | common post at (0, +42) — true scissors |
| **edge offset from the pivot** | **3.5 mm — the cut-or-crush parameter** |
| drive pin | 26.0 mm back down the tail, at y = +16 |
| sweep | 0 → 40°, one-sided |
| mouth opening | 7.0 mm (= 2 × edge offset) |
| rack travel | 21.8 mm — 139° of the SG90's 180° |
| drive slot | radial, r 26.00 → 33.94 |

### The first build would have crushed, not cut

Both cutting edges lay **on** the pivot. Two straight lines through one point
meet at that point and nowhere else, and at closure they go coincident along
their entire length in one instant. There is no travelling contact: the whole
stem section shears at once. That is a V-pinch with a nice pivot, and the
×2–×4 "scissor progression" this spec had been crediting was **×1** — 26 N
against the ~50 N a 5 mm stem wants.

Offsetting each edge from the pivot by `a` is what makes it a scissor, and is
how real scissors are built. The two edges then cross at exactly **one** point,
at `r = a / sin θ`, which sweeps **in from the tip** as the blades close. At
θ = 0 they are parallel and 2a apart — that is the mouth, and it does not
taper.

### Force, and why it is a curve not a number

Advantage climbs as the crossing sweeps inward: at the cut, `gap = 0` so
`a = r sin θ`, and `MA = tail_r / (r cos²θ)`.

| cut at r | θ | MA | force | stem ×2 / ×3 |
|---|---|---|---|---|
| 16.0 | 12.6° | 1.71 | 14.6 N | 2.9 / 4.4 mm |
| 12.0 | 17.0° | 2.37 | 20.2 N | 4.0 / 6.1 mm |
| 8.5 | 24.3° | 3.68 | 31.5 N | 6.3 / 9.4 mm |
| 7.5 | 27.8° | 4.43 | 37.9 N | 7.6 / 11.4 mm |
| **6.5** | 32.6° | **5.63** | **48.1 N** | **9.6 / 14.4 mm** |

**Deep in the throat it makes 48 N**, which clears a basic house plant even on
the pessimistic progression. At the tip it makes 15 N and will crush. `pb_hub_r`
is 6.0 rather than 7.0 for exactly this reason: the hub fills the throat inside
its own radius, so every millimetre of it is force given up.

**Advantage falls off 3.3× from throat to tip, and that is deliberate.**
Every bypass pruner ever made behaves this way. It is a technique
instruction, not a defect: *push the stem all the way into the throat.* A
stem cut at the blade tip gets 11 N and will be crushed rather than severed.
The test asserts the falloff, because if it ever inverts, the pivot and the
throat have swapped and the geometry is wrong.

## What it can and cannot cut

| | |
|---|---|
| soft herbaceous stems to ~5 mm — basil, coleus, pothos, tomato suckers, spent flower stems | **yes** |
| semi-woody to ~3 mm — young pelargonium, fuchsia | **probably**, sharp blades only |
| woody 5 mm+ — ficus, jade, rubber plant | **no.** Needs 2–3× more; wants a ratchet or a bigger servo |
| anything needing a cut along a line rather than through a throat | **no**, and never will on this arm |

Reach is ~150 mm from the shoulder at `fa_l2` = 65. That reaches the near
side of a small plant standing on the bench. It is not a tree pruner.

## The blades are steel, and that is the one addition

Printed PETG will not hold a cutting edge on plant tissue for more than a
few cuts — it crushes rather than severs and dulls immediately. The head
carries **two 9 mm snap-off cutter blade segments** clamped in printed
carriers, edges facing, offset in Z so they bypass.

Chosen because they are 0.4–0.5 mm thick, ground sharp, cost pennies, are
in every toolbox, and are *replaceable* — a pruner blade is a consumable
and designing as though it is not is a mistake. Each segment gives ~9 mm of
usable edge, which bounds stem diameter well below the force limit anyway.

A scissor needs its two edges in light rubbing contact at the cut point.
Preload comes from tension in the pivot screw plus flex in the carriers.
**This is the least certain part of the design** and wants a gauge print
before anything else.

## Mechanism — candidates

Frame: X = jaw opening, Y = forward out of the hand, Z = rack separation.
The pinion axis is +Y; the two racks sit at z = ±`gr_offset` and translate
in ±X. Pinion, racks and shell internals are reused unchanged.

**THE TAIL RUNS FORWARD OF THE PINION, NOT AROUND IT.** This is the whole
trick and it took three failed layouts to find.

Each blade pivots on a post fixed to the shell and reaches in toward the
centreline; its tail runs back to a pin carried by the rack, through a short
slot that absorbs 2.34 mm of radial travel. The blades shear at z ≈ 0 —
which is exactly where the pinion is. So:

- a **straight tail** reaching back to the rack has to cross the pinion disc;
- a **dog-legged tail** routed outboard fails too, and less obviously: the knee sits at a radius from the pivot, so it sweeps with the blade and swings itself back into the disc;
- pushing the **pivot outboard** far enough for a straight tail to miss the disc drops the advantage to 2.7.

The pinion occupies y ∈ [−8, 0] only. Put the pivot at y = +24 and the drive
pin at y = +4 and the entire tail lives forward of it, where there is
nothing to dodge. No cam, no linkage, no knee — one rigid printed arm per
blade, pivoting on a post.

The rack needs a small forward bracket to carry its pin at y = +4, z = ±9.2,
reaching down to the blade plane. That bracket is the only addition to the
rack.

The counter-blade needs a **hook** — a curve that traps the stem in the
throat. Without one the blade pushes the stem out ahead of the edge and
polishes it instead of cutting.

## Interfaces

| what | value | why |
|---|---|---|
| effector bolts | 4 × M3 at ±11, ±9 | `asm_eff_bolt_x/z`, unchanged from the gripper |
| servo | SG90 | `gs_*` bay reused as-is |
| pinion | m1.5, 12T, r 9.0 | `gripper_pinion` reused UNCHANGED |
| blade | 9 mm snap-off segment | 0.5 nominal thickness, clamped, one M2 each |
| throat opening | 15–20 mm target | more than a house-plant stem needs; the rest of the stroke goes to the cam |

## Loads

Built, not budgeted. Printed mass at 0.6 × solid PETG:

| head part | g printed |
|---|---|
| `pruner_shell` × 2 | 25.8 |
| `pruner_rack` × 2 | 6.6 |
| `pruner_blade` × 2 | 3.2 |
| `gripper_pinion` (reused) | 1.0 |
| 2 × steel segment | 1.5 |
| **total** | **37.0** |

**That is 3.5 g over the 33.5 g this spec budgeted, and the elbow goes from
82 % to 86 %.** Still inside duty with no payload, but the margin is spent.

All of the overrun is shell. The gripper's clamshell pair is 18.0 g printed;
this one is 26.1. The extra 8.1 g is the roof over the mouth and the cheeks —
and there is no way to trim it back to 33.5 without deleting the pivot
carrier, because the base shell was already 18 g. If the elbow needs the
margin back, the lever is a lighter shell, not a lighter cheek.

**The cheek is a plate, not a block.** Carried at full shell height it would
be 10.8 g per half. The `blade_sweep` void under it is what makes it 2.6 g,
and forgetting that cut once cost 4.3 g of plastic sitting exactly where the
blades travel.

## Acceptance

- interference gate over the full closing stroke, as `_check_fit` does for the gripper
- blade edges bypass with 0.05–0.15 mm of side clearance at every point of the stroke
- a mechanical hard stop before the servo reaches its rotation limit
- **stall timeout in the controller**, asserted in the firmware spec, not here — the thermal case is the servo held at 0.7 × stall against an uncuttable stem
- blades shrouded as far as the mechanism allows — see below

**The working edge cannot be shrouded, and neither can the tails.** The nose
is the mouth you feed a stem into; covering it would stop the tool working.
The tails swing to |x| = 22.4 mm inside the cheek's own band at full sweep,
which is wider than any cheek that would still clear them. What the design
does do: the steel stands only `pb_steel_proud` 1.5 mm past its carrier, only
along the intended edge, and the cheek covers the blades from above through
their whole travel. Treat the head as a live blade whenever the servo is
powered — that is a handling instruction, not something geometry can fix.

Gated by `_check_pruner.py`, which is committed and reproducible:

- a 5.0 mm stem **fits the 7.0 mm mouth** at θ = 0 — interference 0.000
- the crossing **sweeps r 13.52 → 5.45** while the stem occupies r 6.00–11.00, so the cut enters beyond it and finishes inside it
- the bite grows monotonically: 0 → 10.7 → 29.0 → 44.0 → 56.8 mm³
- whole head, 7 bodies, **0.00 mm³** interference

Before printing: **blade-pocket gauge** (segment thickness and clamp screw),
**bypass-preload gauge** (two carriers on one pivot, checking edge contact
along the stroke), and the existing rack/pinion mesh gauge.

## ASSUMED / unverified

- **10 N per mm of stem is a rule of thumb**, not a measurement. It is the single number the whole capability claim rests on. Measure it: pull a stem through a kitchen scissor edge on a kitchen scale before committing to blade geometry.
- 0.7 efficiency through horn, mesh and channel is assumed.
- The progression multiplier (×2 / ×3 / ×4) is an estimate. The mechanism is now a real scissor rather than a pinch, so it is at least greater than 1 — but its size is not known.
- Snap-off segment dimensions are nominal, not measured off the blades in hand.
- Nothing here has been printed.
