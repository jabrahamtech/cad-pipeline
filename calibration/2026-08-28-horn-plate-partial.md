# Horn plate v1 — bench session, PARTIAL (2026-08-28, Jonathan)

Plate: `gauge_horn_v1.3mf`, PETG, printed. Servos/horns: the bench clones.
Status: CROSS station done, MG995 stations BLOCKED on what horns the big
servo actually ships with. Everything below is MEASURED unless said otherwise.

## CROSS station — FAILED, and the failure is the point

The SG90 4-arm cross horn does not enter the rotor cross pocket at all.
Reported as "shape doesn't match"; the caliper says it is WIDTH, and the
shape reads as a mismatch because nothing seats.

| what | model said | MEASURED | delta |
|---|---|---|---|
| long axis, tip to tip | 33.5 | **34.4** | +0.9 |
| short axis, tip to tip | 16.0 | **17 (16–18)** | ~+1 |
| long-arm width at the hub (first hole) | 5.5 | **5.7** | +0.2 |
| long-arm width at the tip (last hole) | 3.0 | **4.0** | **+1.0** |

**The arm is 4.0 wide at its NARROWEST.** The turret slot is `tt_horn_w`
3.4 (= the old 3.0 + 0.4 clearance). A 4.0 arm cannot enter a 3.4 slot,
anywhere along its length — so the horn sits on the pad and the station
reads as "doesn't fit at all". The photo-derived estimate (~4.7–5.0 at
the tip) agreed in direction; the community model's 3.0 was the wrong
number, and it was the one everything downstream trusted.

Photo cross-check, scaled off the pad's own Ø6.0 screw bore: long span
~39.6 (caliper 34.4 — the photo is off ~15 %, oblique angle and the horn
sitting proud of the scale plane, so the CALIPER governs); short span and
the width taper agreed within ~0.5.

### What this changes (not yet applied)

- `tt_horn_w` 3.4 → **4.4** (4.0 + 0.4), and the pocket span/root relief
  re-checked against a 34.4 long axis and 5.7 roots.
- micro `horn_arm_w` 5.65 → **5.85** (5.7 + 0.15): at 5.65 the slot is
  0.05 UNDER the real arm — interference, not a press fit. Affects
  wrist_hub, wrist_rotator, gripper_pinion.
- `MICRO_HORN_ARM_W_OUTER` 3.0 → 4.0, `MICRO_HORN_ARM_W_AT_6` 5.5 → 5.7,
  `MICRO_HORN_CROSS_LONG` 33.5 → 34.4, `_CROSS_SHORT` 16.0 → 17.0 in
  lib/servo.py, all promoted MODEL → MEASURED.

## SESSION 2 — the hub sweeps, and both hubs were badly over-modelled

Every bore in BOTH hub rows accepted its hub loosely on the first drop.
A sweep that overshoots entirely is still an answer, and a fast one.

| what | model | MEASURED | note |
|---|---|---|---|
| micro horn hub Ø | 8.0 | **6.8** | the PRE-audit value was 7.0 — the "correction" made it worse |
| MG995 horn hub Ø | 13.8 | **8.7** | 5.1 mm out |
| MG995 arm width @ r8 | 6.5 | **6.5** | the one model number the bench confirmed |
| MG995 blade thickness | 2.5 | **2.2** | BL comb, middle slot |
| MG995 disc horn Ø | 22.0 (drawing) | **20.6** | plastic clone, not the alu disc |

### THE STANDOFF WAS DODGING A HUB THAT DOES NOT EXIST

`sb_horn_standoff` 2.0 was invented on 2026-08-27 because a Ø13.95 relief
left 0.93 mm of wall to the 16.0 af hex flats. At the real Ø8.7 the bore
is 9.10 and the wall is **5.45 mm**. The standoff is retired to 0.0 (kept
as a named zero so the history stays legible) and the shoulder gets its
2 mm of width back.

Retiring it moved the servo 2 mm inboard, which pushed the output boss
2 mm deeper into shoulder_hub than its mouth was cut for — `_check_shoulder`
caught that immediately as 75.59 mm³ of `MG995_output^shoulder_hub`, and
`sh_boss_depth` went back to 2.5 with `sh_horn_hub_depth` to 6.40.

### Applied, and all gates re-run

wrist_hub / wrist_rotator / gripper_pinion hub pockets 8.15 → **6.95**
(at 8.15 they were 1.35 loose — no press at all); shoulder_hub bore
14.2 → **9.10**, blade slot 2.6 → **2.30**; `_check_j1`'s hub envelope
8.0 → **6.8**.

**J1 is no longer BLOCKED.** That gate has reported on a guessed hub
diameter since the day it was written — first an invented 6.30, then a
community-model 8.0. It now runs on 6.8 MEASURED: full sweep 0.000 mm³,
PASS. Shoulder PASS all eight pitches, wrist PASS, pruner PASS, leads
6/6 CLEAR. Turret exported **v5**.

## MG995 horns — the bag, photographed 2026-08-28

FOUR horns ship with it: a 4-arm cross, a 6-arm star, a long double arm,
and a ROUND DISC. The disc is why the MG995 STACK station read as
impossible: that station is an arm-in-slot interface and a disc has no
arms. The station is wrong for the disc, not the servo.

| what | on file | MEASURED |
|---|---|---|
| disc horn outer Ø | 22.0 (drawing) | **20.6** — the black plastic clone disc, not the alu one |

Arm-horn numbers for the MG995 were settled in session 2 above. The ONE
horn number still model-grade anywhere in the project is the **hub
HEIGHT** (micro 3.0, MG995 3.8) — it sets how deep the reliefs go, not
whether anything fits, so it is a comfort item rather than a blocker.

## THE STRUCTURAL LESSON, and it is bigger than one number

Every arm slot in this project was cut from a MODELLED arm width, and
the model was 1.0 mm narrow. The measured taper is now known:

    w(r) ≈ 5.7 − 0.121·(r − 6)      micro horn, r 6 … 17

The turret's cross pocket engages r 6.5 … 16.4, over which the real arm
runs **5.64 down to 4.44**. No CONSTANT-width slot fits that: 3.4 (what
shipped) fits nowhere, and even a corrected 4.4 would only accept the
arm outboard of r ≈ 13.5. The pocket needs one of:

  (a) a TAPERED slot cut to the measured taper + 0.4 — full engagement,
      matches the arm exactly, small modelling change;
  (b) SHORT engagement — trim the arms to r 8 and cut a 6.0 constant
      slot over r 6.5…8, accepting ~1.5 mm of bearing per arm (the yaw
      SG90 only carries 0.8 kg·cm, so this is not obviously too little);
  (c) BOLT THROUGH THE HOLES instead of slotting the arms at all —
      batch-independent, zero backlash, and every horn in the bag has
      holes. Costs a redesign of the rotor's horn interface.

**DECIDED (a), same session.** The slots are now cut from
`lib.servo.micro_arm_w()` — 6.04 wide at r 6.5, tapering to 4.84 at the
r 16.4 trim line — so the pocket follows the measured arm instead of a
retyped constant, and a re-measured horn moves it on the next rebuild.
shoulder_bracket imports the function rather than copying its output.
J1 full sweep re-run: 0.000 mm³, PASS, `horn^rotor` 0.000. Turret
re-exported **v4** — v1/v2/v3 all carry a pocket no real horn enters.
gauge_horn **v2** carries the tapered CROSS station so the fix gets the
same drop test that caught the fault.

## Applied from this session
- lib/servo.py micro horn: arm width 5.5→**5.7** at r 6, 3.0→**4.0** at
  r 17, cross long 33.5→**34.4**, short 16.0→**17.0**, all MODEL→MEASURED;
  new `micro_arm_w(r)` so slots are cut at their own engagement radius.
- MG995_DISC_HORN disc_dia 22.0 → **20.6** MEASURED.
- micro arm slots 5.65 → **5.85** in wrist_hub, wrist_rotator,
  gripper_pinion (they trim at r 6, where the arm is 5.7).

## Not yet run
MG995 STACK with an arm horn, both HUB sweeps, BLADE comb, PIN pairs,
and every flange-plate station.


## SESSION 3 — THE SERVO CANNOT BE FITTED. Found on the flange plate.

Trying to seat the MG90S in the flange plate's lobe station (window
12.6 x 23.0, the forearm's own window, through a 5.5 stack that IS
fa_lobe_t): **the servo will not pass through, because of its cable.**

This is not a gauge artefact. `forearm.py` cuts that same window, so a
servo that cannot pass the gauge cannot be fitted to the arm either.

### The blind spot it exposes

`_check_leads` models the lead as a cylinder leaving the case's far END
FACE and running 8 mm outward, and asks whether that path is solid. It
therefore checks the lead's **resting** position and never its
**assembly** path. A window sized to the bare case passes that check
and still cannot be assembled, because the cable has to get through the
window too - and once the case is home, the cable is pinched between
the case and the window wall with nowhere to sit.

Every servo pocket in the project was cut to case + loc. The same
question now hangs over the SG90 pockets (wrist_roll, pruner_shell,
turntable_stator) and the MG995 pad, and only pruner_shell has ever cut
a deliberate lead notch.

### What is NOT yet known, and blocks the fix

Where the cable actually leaves the case. `lib/servo.py` has carried
this as an explicit ASSUMED since the file was written - "the leads
exit the FAR END FACE, centred across the case width and one lead
diameter up from the case bottom... IT IS NOT MEASURED." The notch
cannot be placed until that is settled, and placing it wrong is worse
than not placing it: it would weaken the lobe in the wrong spot AND
still pinch the cable.

**ALL THREE SERVOS DO THIS** (Jonathan, same session). So it is not one
servo's quirk and not one part's bug - it is the same fault repeated in
every pocket the project cuts.

### Where the cable must be, for this to happen at all

Worth reasoning through, because it narrows the fix. The lobe is only
5.5 thick and the case is 24 tall: the case's TOP 5.5 mm sits in the
window, the tabs land on the lobe's outer face, and the remaining
~18.5 mm hangs in free air outboard. A cable leaving the case near its
BOTTOM would therefore hang clear and never touch the window.

It jams anyway - so the cable must leave the case within roughly the
top 5.5 mm, i.e. up at the OUTPUT SHAFT end, inside the band the window
grips. That also matches the photo. lib/servo.py's written assumption
("far end face, one lead-diameter up from the case bottom") is wrong at
BOTH ends of the description: wrong face, wrong height.

### Consequence for _check_leads

The gate probes from the case's far end face at the bottom. If the real
exit is the shaft end, every probe in that file is in the wrong place
and its 6/6 CLEAR is measuring nothing. The J1 lead groove cut into
turntable_stator on 2026-08-27 was sized and sited from that same wrong
assumption.

NOT FIXED. NOTHING WITH A SERVO POCKET SHOULD PRINT until the cable
exit is measured and every pocket gets a lead relief. That is the
forearm, wrist_roll, turntable_stator, gripper_shell and the MG995
pad - pruner_shell is the only part already carrying one, and its notch
was placed from the same bad assumption.


## SESSION 4 — the cable exit, pinned. And why every pocket jams.

Jonathan, in words then a sketch: the bundle leaves at the **SHAFT END**
(the same end as the flange nearest the horn), **near the case BOTTOM**.
I first read his description as tab height; the sketch corrected it. The
END was right, the HEIGHT was not.

`lib/servo.py` previously said "the FAR END FACE, one lead diameter up
from the case bottom". The HEIGHT was right all along. The END was
wrong, and the end is what matters.

### The arithmetic, which needed no gate to see

| servo | case width | + bundle | window cut at |
|---|---|---|---|
| SG90 | 12.2 | **15.6** | 12.4 |
| MG90S | 12.4 | **15.8** | 12.6 |
| MG995 | 20.0 | **24.2** | 20.2 |

The whole case passes through its mounting window during assembly - the
tabs land on the FAR face, so the case travels the full window depth and
keeps going. At the height the cable leaves, the servo is ~3.4 mm wider
than the window it must pass. Every pocket in the project is cut to
case + 0.2. **None of the three servos can be installed in any of them.**

This was arithmetic available from day one. No sweep was needed and no
sweep would have found it, because every gate models the servo as its
CASE ENVELOPE and the cable is not part of that envelope.

### The fix, chosen

Snug pocket everywhere, with one channel down the inside of the window
at the shaft end - a keyway for the cable to slide in as the case goes
through. Sized lead_bundle_dia + clearance, cut the full depth of the
lobe/wall so the cable can travel. Nothing else loosens, all four walls
keep locating the case.

Parts needing it: forearm (x2, J3 and J4), wrist_roll, turntable_stator,
gripper_shell, and the MG995 pad on shoulder_bracket. pruner_shell has a
notch already but it was sited from the far-end assumption and must be
re-placed to the shaft end.
