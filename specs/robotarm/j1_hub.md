# j1_hub — spec

Project: `models/robotarm/j1_hub.py` — **NOT WRITTEN.** This file is the
whole of the part; someone has to turn it into a script.
Status: DRAFT <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

Written by the agent that migrated J1 off the servo horn on 2026-08-31. It
could edit `turntable_stator.py` and `shoulder_bracket.py` only, and both of
those now cut an interface for a part that does not exist yet. Until this
script is written **J1 has no drive at all** — the horn geometry is gone from
both hosts and nothing has replaced it inside Fusion.

## Function

The one piece between the J1 SG90 and the arm. It is broached onto the
servo's own output spline and bolted flat to the underside of
`shoulder_bracket`'s turntable disc (the rotor) with three M3. It replaces
the stamped four-arm horn, which is out of this machine entirely.

## Why this part exists at all — direct broach vs bolted hub, priced

`j3_pinion` was migrated four commits earlier by boring the gear STRAIGHT
onto the MG90S spline, and the obvious move for J1 was to do the same to the
rotor. It was priced and rejected. Both options were costed at SG90 **stall**
— 1.6 kg·cm = **156.9 N·mm** (`lib/arm_loads.STALL_KGCM['J1']`) — because an
interface has to survive whatever the servo can produce, not what it is
asked for. Duty is half that.

| | broach into the rotor | separate bolted hub |
|---|---|---|
| torque radius | r 2.33 (the bore) | r 8.00 (the bolt circle) |
| bearing area | Ø4.65 × 2.50 = **11.6 mm²** | 3 × (Ø3.0 × 3.7) = **33.3 mm²** |
| bearing pressure | **5.81 MPa** | **0.59 MPa** per bolt |
| parts | 0 new | 1 new, ~3 g |
| height cost | 0.00 | **0.00** — the hub lives in space the horn used |

**And the honest half of that table: the bolted hub does not reduce the load
on the spline.** The broach still carries all 156.9 N·mm, because the servo
has exactly one output and everything leaves through it. What the bolt circle
buys is *where the 5.81 MPa lives* — in a 3 g consumable rather than in the
arm's largest structural part. Anyone reading the 10× as a strength win has
read the wrong column.

The decision was not made on stress at all. 5.81 MPa against PETG's 35 MPa
in-plane, derated ×0.5 across layers and ÷4 for cyclic, is 4.4 MPa allowable
— so a direct broach is *marginal on stress*, which is interesting but not
decisive. What decided it, in order:

1. **Print orientation, and this one is disqualifying.** `shoulder_bracket`
   prints −X face down; its own docstring says the disc therefore "stands on
   edge". A broach bore cut into that disc is an **XY-facing hole**, and
   `design_rules` says in as many words that XY-facing holes come out
   undersize and out-of-round and want a teardrop. A broach bore has to be
   round to a fraction of the 0.25 mm interference or it is not a fit, it is
   a lottery. `j3_pinion` could go direct *because* its bore prints vertical
   — it says so in its own print-orientation note. This hub prints the same
   way, flat with the bore vertical, and inherits the same argument.
2. **There is no assembly order for a direct broach.** Broaching is a press
   stroke of 0.25 mm diametral interference cutting twenty teeth into PETG.
   The rotor's height is set by three 608ZZ at r 27 and a ring hooked over
   its rim — once it is on the turntable there is no press stroke left, and
   pressing it on first makes the Ø68 journal impossible to enter afterwards.
3. **Iteration cost.** `SPLINE_BROACH_INTERFERENCE_MM` is graded **ASSUMED**
   and `lib/servo.py` says outright to print the sweep before committing a
   gear to it. Committing an ungauged press fit to the arm's largest
   structural part costs a full shoulder-bracket print per try. This costs
   minutes, and it is the piece that *should* wear out and be replaced.
4. **Service.** Every teardown that separates the arm from the base degrades
   a broach. With the hub separate, the arm comes off on three M3 and the
   broach is never disturbed.

**Why not bolt to the horn instead** (`lib/servo_hub.horn_bolt`, the route
J3 considered): it puts the gear plane 12.6 mm further out and keeps the horn
— a batch-varying stamping the bench has now failed to fit three times — in
the load path. Rejected for J1 for the same reasons it was rejected for J3.

## Interfaces — the dimensions that matter

Frame: **`lib/servo.py`'s servo frame** — origin on the SG90 output shaft
axis at the **tab plane**, +Z up out of the shaft. That is the frame
`spline_hub()` solves in, so nothing needs converting.

Everything in the first block is **DERIVED** by
`lib.servo_hub.spline_hub(CATALOG['SG90'], face=6.80)` and must be read from
there, not typed. `turntable_stator.py` and `shoulder_bracket.py` already
compute it that way and declare it as `tt_hub_*`; **this part must use the
same call and the same names.** If the three ever disagree the hub is bored
from one set of numbers and located by another.

| Interface | Value | Source | Fit |
|---|---|---|---|
| seat (underside), servo-z | **7.10** | `spline_hub().seat_z` — case top 6.70 + 0.40 running gap | — |
| total height (`face`) | **6.80** | DERIVED: `broach_to` 6.30 + `J1_HUB_OVERSHOOT_MM` 0.50 | — |
| top face, servo-z | **13.90** | 7.10 + 6.80 | bolts flat to the rotor |
| outer Ø | **21.80** | DERIVED: 2 × (8.00 + M3 pilot/2 + MIN_WALL) | — |
| boss clearance bore | **Ø5.40** × from z 7.10 to 10.90 | Ø5.0 collar + `free` 0.40 | free |
| **broach bore** | **Ø4.65** × from z 10.90 to 13.90 | `spline_dia` 4.9 − `SPLINE_BROACH_INTERFERENCE_MM` 0.25 | **ASSUMED interference — gauge it** |
| spline engaged | **2.50** | all an SG90 has (MG90S has 4.00) | — |
| bolt circle | **3 × M3, r 8.00, az 90 / 210 / 330** | `tt_hub_bolt_r`, `tt_hub_bolt_az` | self-tap pilot Ø2.6 |
| pilot depth | **3.70** | body 5.30 − MIN_WALL 1.60 | blind, from the TOP face |
| retaining washer | **Ø6.25** | `spline_hub().washer_d` | assembly aid only — see below |

Grading of everything that is not derived:

| | grade | note |
|---|---|---|
| SG90 case/boss/spline dimensions | **DATASHEET** | `lib/servo.py`, TowerPro drawings |
| `SPLINE_BROACH_INTERFERENCE_MM` 0.25 | **ASSUMED** | never gauged; this is the number to gauge first |
| `J1_HUB_OVERSHOOT_MM` 0.50 | **ASSUMED** | how far the bore runs past the spline top |
| bolt circle r 8.00 | **DERIVED** | boxed in: head counterbores must clear the rotor's Ø5.40 screw bore by MIN_WALL, and Ø21.80 must stay inside the connector gate at r 12.20 |
| M3 head Ø5.5 × 3.0 | **DATASHEET** | ISO 4762 socket cap |
| pilot Ø2.6 | **HANDBOOK** | `design_rules.FASTENER_MM['M3']['pilot']` |

## The two things that are easy to get wrong

**THE RETAINING SCREW IS NOT USED IN SERVICE.** This is the one place J1
deliberately differs from `j3_pinion` rather than copying it. `j3_pinion`
needs the screw and its washer because nothing else holds the pinion down on
the spline. This hub is bolted to a rotor that `turntable_ring` already
captures axially, so running the screw as well would be a **second axial
datum fighting the first** — which is precisely the over-constraint that had
the horn holding the turret off its own bearings. Use the screw and washer to
*pull the hub down while the spline broaches it*, then take both out before
the hub is bolted up. Do not design a washer recess into the top face: the
top face is the bolted joint, and a washer there is a 1 mm shim the rotor
would ride on.

**THERE IS NO REGISTER, AND THAT IS DELIBERATE.** The rotor's three holes are
**Ø4.40** — M3 clearance 3.40 plus **1.00 mm of intentional radial float**.
The hub is centred by the spline; the rotor is centred by its Ø68 journal in
the ring (itself a `rotating` fit with 0.35 mm of play); the joint takes up
whatever is left between the two axes when it is tightened. This is
`lib/servo_hub.py`'s radial-slot argument and `MG995_TAB_SLOT_X_MM`'s,
applied to a bolt circle. A tight register would have to be a round bore in a
disc that prints on edge — reason 1 above, all over again.

The joint carries torque by **friction first, bearing second**: three M3 at
r 8.00 hand-tight (~200 N each, µ ≈ 0.3 PETG on PETG) is ~1260 N·mm of
friction against 156.9 N·mm required, an 8× margin, and if it ever slips the
screws come into bearing at 0.59 MPa as the backstop.

## Loads & environment

J1 is a **yaw** axis, so gravity contributes nothing; `_assembly.md` records
the joint as friction- and inertia-limited with the SG90's 0.80 kg·cm of duty
"all spent". The overturning moment (0.162 N·m, worst roller 4.73 N) goes
into the three 608ZZ and the ring, **not** through this hub — which is why a
2.50 mm spline grip is tolerable here and would not be on a cantilevered
gear. The hub sees pure torque.

**Engagement is the tight number.** 2.50 mm is the whole spline; `tt_ring_lift`
lets the rotor float up 0.40 mm and the hub rises with it, leaving **2.10**
against `spline_hub()`'s 2.00 minimum. `turntable_stator.py` asserts this.
There is no margin to spend — do not add axial clearance anywhere in this
stack without re-running that assertion.

## Cables & service

Nothing routes through the hub; the loom crosses J1 through the rotor's
window and connector gate at r 12.2–18.0, outside the hub's r 10.90. The hub
is the designated wear item: three M3 from above (through the boss top,
between the fork legs, reachable with the turret fully assembled) release the
rotor from it, and the hub then lifts off the servo.

## Print plan

PETG · **flat, bore vertical, top face on the bed** · single nozzle ·
40 % infill, **5 walls** — the broach has to displace plastic without
splitting the hub, and walls are what resist that. No support. 0.4 mm
elephant-foot chamfer on the bed face; **0.5 mm lead-in chamfer on the broach
bore's lower mouth**, which is where the spline enters. Same orientation and
the same argument as `gripper_pinion` and `j3_pinion`.

## Acceptance

- [ ] script written, lints clean under `tests/test_fusion_scripts.py`
- [ ] reads `spline_hub(CATALOG['SG90'], face=6.80)` — no retyped numbers,
      and asserts its own `tt_hub_*` against the two host parts' copies
- [ ] **gauge the broach interference before printing this part.**
      `SPLINE_BROACH_INTERFERENCE_MM` 0.25 is ASSUMED and has never been cut
      in PETG on this printer. Sweep 0.15 / 0.20 / 0.25 / 0.30 on a stub and
      look for a bore that cuts cleanly without splitting. This blocks J1.
- [ ] measured: hub turns the rotor through 180° with no lost motion at the
      bolt circle
- [ ] measured: with the ring fitted, the rotor sits **on its rollers** —
      the failure this whole migration exists to fix. Feeler-gauge the race
      face at all three rollers.
- [ ] printed and verified — date, measured result, deviations

## Consequences elsewhere, for whoever picks this up

- `models/robotarm/_check_j1.py`, `_gauge_horn.py` and `_gauge_verify.py`
  still read `tt_horn_z`, `tt_horn_span`, `tt_horn_w*` and `sb_root_relief_d`.
  Those parameters no longer exist. Those three helpers will fail until they
  are rewritten against `tt_hub_*`.
- `specs/robotarm/_state.md` line ~60 still lists the `tt_horn_*` row.
- `specs/robotarm/_assembly.md` and `docs/robotarm/README.md` still carry the
  open question "whether the SG90 horn hub clears `tt_screw_bore` Ø6.00".
  It is closed by deletion: there is no horn hub, and the bore is Ø5.40.
