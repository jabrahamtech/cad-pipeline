# _gauge_broach — the broach-interference coupon

One coupon, 122 × 129 mm, ~27,400 mm³, **≈ 22.7 g of PETG**. It answers one
question, and it is the question every driven joint in the arm now stands on:

> `lib/servo.py` line 426
> ```python
> SPLINE_BROACH_INTERFERENCE_MM = 0.25   # ASSUMED - bore = spline_dia - this
> ```
> **ASSUMED.** Never cut, never pressed, never twisted. Six printed hubs and
> two more scripts derive their bore from it.

When you are done, **you change that one line** and every broached hub in the
arm moves with it. The last section of this sheet is exactly how.

---

## Why a caliper cannot do this

Every other number in this project is a clearance — a gap you can measure.
This one is a **negative** gap. The bore is cut *smaller* than the steel
spline and the spline cuts its own form into the plastic on first assembly.
Whether 0.25 mm of interference **displaces** PETG or **splits** it is not a
dimension. It depends on the plastic, the layer bond, the hoop around the
bore and the shape of the spline teeth, and the only way to find out is to
press one on and twist it until something gives.

So this is a **destructive** gauge. Every station you test is used up. There
are 21 of them and you will not need all 21.

---

## Print it the way the arm will be printed

| | |
|---|---|
| Material | **the same spool the arm will use.** PETG. A gauge in PLA measures a different material — `calibration/2026-08-14-verge-pole-thread-fit.md` already records PETG running tighter here |
| Layers | 0.2 mm |
| Walls | 3 |
| Infill | 15–20 % |
| Support | **OFF. Not "auto". OFF.** |
| Orientation | **flat on the bed, labels UP, every bore VERTICAL** |

**The orientation is part of the test, not a slicer preference.** Every
broached hub in the arm prints bore-vertical, and `j1_hub.py` and
`shoulder_bracket.py` both record *refusing* to put a broach bore in a part
that stands on edge. Two reasons, and they both bite:

1. A hole printed on its side comes out **out-of-round and undersize**
   (`design_rules.HOLE_DIA_COMP_MM`, and the reason this project reaches for
   teardrops in XY). The interference under test would not be the
   interference designed, and it would not even be *one* number — it would
   vary around the hole.
2. Broaching loads the bore in **hoop tension**. In a vertical bore that hoop
   runs *within* a layer, in the strong direction. Lying down it runs *across*
   layers at `Z_TENSILE_FACTOR` = 0.5, so the hub splits at roughly half the
   interference and the answer you carry back to `lib/servo.py` is wrong by a
   factor of two.

Supports off matters because the only thing a slicer could support is the
inside of the bores, and the bores *are* the measurement.

---

## What is on it

21 stations — three splines × seven interferences, 0.10 → 0.40 in 0.05.
Every station is its own round boss on its own lever, hanging off the comb
spine by a **1.6 mm breakaway neck**. Snap one off, destroy it, and the other
twenty are untouched: there is 3 mm of air between neighbours, so a split
boss cannot reach the one beside it.

| Column | Servo | Spline | Bores (Ø, mm) | Boss OD | Grip length | Lever |
|---|---|---|---|---|---|---|
| `S10`…`S40` | SG90 | Ø4.9, 20T | 4.80 → 4.50 | ≈13.9 | 2.50 | 21.5 mm |
| `M10`…`M40` | MG90S | Ø5.0, 20T | 4.90 → 4.60 | ≈14.0 | 4.00 | 21.5 mm |
| `G10`…`G40` | MG995 | Ø5.9, 25T | 5.80 → 5.50 | ≈14.9 | 3.60 | 30.0 mm |

The **label is the interference in hundredths of a millimetre**, raised
beside its own bore. It is raised rather than engraved because a 0.6 mm
groove in a 3.1 mm lever is a fifth of the section, and that lever is
deliberately loaded to the servo's stall torque. Read the label *after* the
test: once a bore has been broached it is no longer round and no longer
measurable, so the station has to say what it was.

**`S25` / `M25` / `G25` are the control** — that is exactly what the arm
ships today, on all three servos.

**SG90 and MG90S are swept separately on purpose.** `lib/servo.py` records
Ø4.9 and Ø5.0 — a tenth of a millimetre apart, which is 40 % of the smallest
interference on this coupon. Three joints run on SG90s (J1, J5 roll, J6
pruner) and two on MG90S (J3 elbow, J4 wrist). If the two want different
numbers, the arm needs a per-servo table and not a constant, and the last
section says how to make that change.

**The wall is the arm's own wall.** Every boss carries **4.55 mm** of PETG
around its bore, which is `j3_pinion.py`'s own reported `hub_wall`
(`J3_PAIR.r_root(18)` 7.75 − half `J3_HUB.boss_clear_d` 3.20), derived in the
script, never typed. It is also *thinner* than the thinnest wall any real
part presents at its broach section (gripper_pinion's 4.80), so **the coupon
splits before the arm does.** That is the direction the error is allowed to
run in.

**The mouth of every bore is relieved** by 0.4 mm per side over the first
0.6 mm, and each station is that much taller to compensate. The first few
layers of a printed hole are squeezed inward by elephant's foot; on a 0.10 mm
interference that squash *is* most of the measurement. The relief throws it
away and doubles as the lead-in the spline needs to start.

---

## How much tooth each station actually bites

The interference is **diametral**, so the radial bite is half of it, read
against the height of one spline tooth (addendum taken as one module,
`m = spline_dia / teeth` — ESTIMATED, no drawing of these splines exists).

| Station | Radial bite | as a fraction of a tooth |
|---|---|---|
| `x10` | 0.050 mm | ≈ 20 % |
| `x20` | 0.100 mm | ≈ 40 % |
| `x25` (today) | 0.125 mm | ≈ 51 % |
| `x30` | 0.150 mm | ≈ 61 % |
| `x40` | 0.200 mm | ≈ 82 % |

That is the real span of the question. At the bottom the steel *planes* the
bore smooth and leaves no index at all; at the top the 4.55 mm hoop is being
asked to swallow most of a tooth per side.

---

## At the bench

You need: the coupon, one SG90, one MG90S, the MG995, side cutters, a fine
marker pen, a small vice or a pair of pliers with flat jaws, a kitchen scale
that reads to at least 1 kg (3.5 kg for the MG995 column — a luggage scale
does), and the servos' own bagged retaining screws plus a washer of about
Ø6.4 (see step 6).

**Work loose → tight. Never start at `x40`.** A station that will not go on
can be forced far enough to strip the servo's own gear train, and the SG90's
is plastic. Going up the sweep, the first one that fails tells you where the
ceiling is before you have wrecked anything.

### 1 — check it came off the bed in one piece

Every station should still be attached at its neck. If a neck broke in
removal, that station is still usable — you just lost the "snap it yourself"
step.

### 2 — caliper three bores BEFORE you press anything

Measure the bores at `S25`, `M25` and `G25` (caliper jaw tips, or a pin
gauge if you have one), twice each, 90° apart. Write them down.

This is the only non-destructive reading on the coupon and it is the one that
tells you whether the whole sweep has shifted. Designed `S25` is Ø4.65. If it
comes out at 4.55, this printer is putting 0.10 mm of extra interference into
*every* bore and the station labelled `S25` is really an `S35`. Record the
designed value **and** the measured one; the constant you change at the end
is the **designed** one, but you cannot interpret the result without knowing
the offset.

If you have already run `_gauge_slim`, its truth row gives you the same bias
as a curve and this step is a cross-check rather than the source.

### 3 — snap one station off

Side cutters at the neck, or twist it off. The neck (1.6 × 2.0 mm) is
deliberately the weakest section on the coupon so it lets go long before the
4.55 mm hoop does. Trim the stub flush so it cannot foul the servo case.

### 4 — start it by hand

Sit the station squarely on the spline. The bore only meets the spline; the
underside lands on the servo's **output collar** below it.

> Sanity check built into the design: at the loose end the SG90's bore is
> Ø4.80 against a Ø5.00 collar. That is only 0.20 mm of shoulder. If an `S10`
> station drops straight past the spline and sits on the case, this printer
> is running bores oversize and step 2 will already have told you so.

Push down with thumb pressure. **Whether it starts by hand is data** — write
it down.

### 5 — press it home

Support the servo body on the bench, hold the case, and press **straight
down**. A small vice with the servo on its back and the station under the jaw
is ideal; flat-jawed pliers work. Do not lever it on at an angle — a cocked
station splits for reasons that have nothing to do with the interference.

Press until the station bottoms on the output collar. **Listen.** A crack is
audible and it is the answer.

### 6 — mark the spline through the open bore

Before anything else: the station is 0.6 mm taller than the spline, so you
are looking down the bore at the end of the spline with the coupon's top face
just proud of it. Put a fine pen mark **across the spline end and onto the
coupon's top face**, one continuous line.

That mark is what separates the two things that both look like "it turned":
the servo's unpowered gearbox back-driving (mark stays aligned, whole shaft
turned — **not a failure**) and the bore slipping on the spline (**mark
breaks — that is the failure you are looking for**).

Leave the screw out for the twist test. Axial hold is step 8.

### 7 — twist it to the servo's own stall torque

Lay the servo on its side on the bench so the lever sweeps in a vertical
plane. Press the **lever tip** straight down onto the kitchen scale, slowly,
watching the mark.

| Column | Push the tip to | which is | = the servo's conservative stall |
|---|---|---|---|
| `S…` SG90 | **≈ 745 g** | 7.3 N at 21.5 mm | 1.6 kg·cm |
| `M…` MG90S | **≈ 930 g** | 9.1 N at 21.5 mm | 2.0 kg·cm |
| `G…` MG995 | **≈ 3130 g** | 30.7 N at 30.0 mm | 9.4 kg·cm |

The MG995 lever is capped at 30 mm to keep the coupon a coupon, which is why
its number is heavy — clamp that servo rather than holding it.

The levers are sized against bending at the **full** stall torque with a
safety factor of 2, so the lever is not supposed to be what fails. If a lever
snaps before the mark moves, note it — that station passed the torque test
and you have a spare answer.

### 8 — the axial check (do this once, on the winner)

Fit the servo's own retaining screw with a washer of about **Ø6.4** (the
broach bore plus 1.6 — `spline_hub()` calls this `washer_d` and says it is
**not optional**: the screw head is near Ø5 and the bore is Ø4.75, so without
a washer the head sits almost entirely over the hole with nothing to clamp).
Draw it down. It should pull the station the last fraction home and stay
there. **If the screw strips before the station seats, that interference is
too tight regardless of what the twist test said** — the arm assembles with
that screw.

---

## Reading it: correct vs too loose vs too tight

Concretely, and in this order.

**TOO LOOSE** — any one of:
- it slides on with thumb pressure and no resistance at all;
- you can turn it on the spline by hand, with no lever;
- **the mark breaks before the scale reaches the target** in step 7;
- it comes off again without a tool.

**CORRECT** — all of:
- it needs firm, steady axial force to seat — a vice or the screw drawing it
  down, not a thumb;
- it seats fully, on the collar, with no crack heard and no white line
  radiating from the bore;
- **the mark does not move at the full stall figure** in step 7;
- the screw in step 8 pulls it home without stripping;
- pull it off (that takes a tool) and you can see **20 clean tooth marks**
  (25 on the MG995) cut into the bore wall, all the way around and all the way down the grip
  length. Partial marks, or marks on only one side, mean the station went on
  cocked — redo it.

**TOO TIGHT** — any one of:
- an audible crack while pressing;
- a white stress line, or a visible split, running from the bore to the
  outside of the boss;
- the boss visibly bulges or goes oval;
- it will not seat at all, or the retaining screw strips trying to draw it
  down;
- it survives the press and then splits under the twist.

**The answer is the SMALLEST interference that passes every CORRECT bullet.**
Not the largest that survives — the smallest that holds. Everything above it
is hoop stress you are storing in a part that has to live in the arm for
years, and PETG creeps.

Then take **one step of margin only if the next station up also passed
without splitting.** If `x25` holds and `x30` splits, the answer is 0.25 and
it has no margin — say so in the calibration note, because that is a finding
in itself.

---

## Record it

Make `calibration/YYYY-MM-DD-gauge-broach.md` and put the spool, the printer
profile and this table in it. If the spool or the profile changes, none of it
applies any more.

```
Spool / profile:
Measured bores (step 2):  S25 ____   M25 ____   G25 ____   (designed 4.65 / 4.75 / 5.65)

| stn | hand start? | pressed | cracked? | mark held to (g) | verdict |
|-----|-------------|---------|----------|------------------|---------|
| S10 |             |         |          |                  |         |
| S15 |             |         |          |                  |         |
| S20 |             |         |          |                  |         |
| S25 |             |         |          |                  |         |
| S30 |             |         |          |                  |         |
| S35 |             |         |          |                  |         |
| S40 |             |         |          |                  |         |
| M10 … M40 |       |         |          |                  |         |
| G10 … G40 |       |         |          |                  |         |

SG90 answer: ____    MG90S answer: ____    MG995 answer: ____
Screw+washer seated the winner without stripping?  Y / N
```

---

## THE EDIT — one line, and it reaches every joint

### If all three servos agree (within one step)

Open `lib/servo.py`. Go to **line 426**:

```python
SPLINE_BROACH_INTERFERENCE_MM = 0.25   # ASSUMED - bore = spline_dia - this
```

Change **the number**, and change **`ASSUMED`** — that word is what every
other file in this project quotes when it says "gauge it before trusting a
gear to it":

```python
SPLINE_BROACH_INTERFERENCE_MM = 0.30   # MEASURED 2026-09-xx on the bench,
                                       # calibration/2026-09-xx-gauge-broach.md
                                       # bore = spline_dia - this
```

Then update the paragraph immediately above it (lines 421–425), which
currently ends *"0.25 is the starting figure and it is ASSUMED - print the
sweep before committing a gear to it."* The sweep has now been printed; say
what it found, including what the failures either side of the answer looked
like.

**That is the whole change.** Nothing else needs editing, because nothing
else types the number:

```
lib/servo.py:426  SPLINE_BROACH_INTERFERENCE_MM
   └─ lib/servo.py:430  spline_bore_d(spec)          ← the only reader
        └─ lib/servo_hub.py:432  spline_hub()  → broach_d, and washer_d
                                                  (= broach_d + 1.6)
             ├─ lib/gears.py:419      J3_HUB   → models/robotarm/j3_pinion.py
             ├─ models/robotarm/gripper_pinion.py     (J6 pruner, SG90)
             ├─ models/robotarm/wrist_rotator.py      (J5 roll, SG90)
             ├─ models/robotarm/wrist_hub.py          (J4 wrist, MG90S)
             ├─ models/robotarm/shoulder_hub.py       (J2 shoulder, MG995)
             └─ models/robotarm/j1_hub.py     J1_HUB  (J1 yaw, SG90)
                  └─ mirrored as tt_hub_broach_d by turntable_stator.py
                     and shoulder_bracket.py
```

Re-run those part scripts, then the gates: `_check_j1`, `_check_shoulder`,
`_check_wrist`, `_check_servo_fit`.

### Two knock-ons to look for when you re-run

- **`j1_hub`'s broach lead-in.** That chamfer is capped by the step between
  the Ø5.40 boss bore and the broach bore — `(5.40 − bore) / 2`, which is
  0.375 mm today. The file already records Fusion *refusing* a 0.5 chamfer
  there. A **looser** answer (smaller interference, bigger bore) shrinks that
  step and the chamfer has to shrink with it; `j1_hub.py` derives it, but
  check the printed value.
- **`_check_shoulder.py` reads the constant directly** (line 80 imports it,
  line 258 computes `broach_d` from it). It is the one file that does not go
  through `spline_bore_d()`, so it will follow a scalar change but not a
  table change — see below.

### If the three servos DISAGREE by more than one step

Then one constant cannot express the answer and you must change the
**function**, not just the number. At `lib/servo.py:430`:

```python
SPLINE_BROACH_INTERFERENCE_MM = {"SG90": 0.30, "MG90S": 0.25, "MG995": 0.35}

def spline_bore_d(spec, interference=None):
    """Bore diameter for a printed hub the servo spline broaches into."""
    i = (SPLINE_BROACH_INTERFERENCE_MM[spec.name]
         if interference is None else interference)
    return spec.spline_dia - i
```

Every part reaches the number through `spline_bore_d(spec)` or through
`spline_hub(servo, …)`, so they all pick this up unchanged. **The one
exception is `models/robotarm/_check_shoulder.py`**, which imports the
constant and does the subtraction itself at line 258 — that line has to
become `spline_bore_d(MG995)` or the gate will fail on a dict.

Expect disagreement between the **micro pair and the MG995** more readily
than between SG90 and MG90S: 25 teeth on Ø5.9 is a slightly finer tooth than
20 on Ø4.9, and the MG995 carries five times the torque into it.

---

## What this coupon does not answer

- **Creep.** It tells you the joint holds stall torque today. It does not
  tell you it still holds after the arm has sat in a pose for a week. That is
  a hold test, not a gauge, and it wants the real part.
- **Re-assembly.** Every station here is broached **once**. A hub that is
  pulled off and pressed back on is running in a bore the spline already cut,
  and it will be looser. If the arm is going to be taken apart, note it — the
  answer for a serviceable joint is not the answer for a one-shot one.
- **The MG995's own numbers.** `lib/servo.py` still grades the MG995 block as
  DATASHEET, unconfirmed against the servo in hand. If its spline is not
  really Ø5.9, this whole column is offset — caliper the spline itself while
  you have it out.
