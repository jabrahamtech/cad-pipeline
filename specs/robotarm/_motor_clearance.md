# GATE motor_clearance — the joints against the motor hardware

Driver: `models/robotarm/_check_motor_clearance.py`. Results:
`specs/robotarm/_motor_clearance.json`.

> "the joints dont have clearance where the motor bits are"
> — Jonathan, printed parts in hand, 2026-09-02

**THIS DOCUMENT WAS WRITTEN WITHOUT RUNNING THE GATE.** The Fusion bridge was
down. Everything below is arithmetic on the library and the part scripts, and
every number in it is a PREDICTION the gate exists to confirm or destroy.
Nothing here is a measurement and nothing here proves a clearance.

---

## 1. Why the existing gates say the opposite

GATE `servo_fit` reads **7/7 clear**, every station `case_mm3 = 0.00`. That is
not a lie; it is an answer to a smaller question. `servo_fit` drops the servo
solid into the host that **carries** it, **at rest**, and measures overlap.

Four things are outside that question, and all four are "motor bits":

| # | Not modelled anywhere | Why it matters |
|---|---|---|
| 1 | **The other half of the joint** | A servo can sit perfectly in its own pocket and be struck by the link that swings past it. `servo_fit` never builds that part. |
| 2 | **The lead bundle vs the moving half** | `_check_leads` tests the bundle against the **host** only. A cable that escapes its own pocket and is then guillotined by the swinging link reads CLEAR in both gates. |
| 3 | **The tab screw heads** | `servo_body.py` *cuts* the tab holes and models no screw. Every mount here recesses the flange exactly `tab_thk` deep, so the tab finishes **flush** and the steel head is the highest thing on the servo. |
| 4 | **The retaining screw + washer** | Since the horn came out, every driven part bores onto the spline and is held by the servo's screw through a washer (`lib/servo_hub.spline_hub()` — "not optional"). Six parts check that **they** clear it. Nothing checks what **sweeps past** it. |

A fifth thing turned up while writing this: **two of the seven placements in
`_check_leads.MOUNTS` no longer match the parts they describe.** See §4.

---

## 2. What moves relative to each servo

Joint transforms are `_preview_arm.py`'s, which owns them; placements are
`_check_leads.MOUNTS`, which owns those. Nothing below is re-derived.

| Joint | Servo | Host (fixed half) | What swings past it | Joint axis | Travel |
|---|---|---|---|---|---|
| J1 yaw | SG90 | `turntable_stator` | `shoulder_bracket` — the whole turret, on `j1_hub` | host **+Z** through the origin | 180° (nothing caps it) |
| J2 shoulder | MG995 | `shoulder_bracket` | `upper_arm`, pitching | host **+X** through the origin | 180° servo; the DOWN stop is smaller |
| J3 elbow | MG90S | `j3_servo_cap` | `j3_gear` (36T) — **and `upper_arm`, not swept** | ∥ cap **+Z**, offset **27.20 mm** (the pair's centre distance) | **90°** = 180/`J3_PAIR.ratio` |
| J4 wrist | MG90S | `forearm` | `wrist_roll`, pitching | host **+X** through the origin | 180° |
| J5 roll | SG90 | `wrist_roll` | `wrist_rotator`, rolling | host **+Y** through the origin | 180° |
| gripper | SG90 | `gripper_shell` | `gripper_rack_jaw`, **sliding** | prismatic along host **+X** | 20.0 mm (`gr_stroke`) |
| effector | SG90 | `pruner_shell` | `pruner_rack`, **sliding** | prismatic along host **+X** | 20.0 mm |

J3 is the only joint whose travel is not the servo's: the 2:1 halves it, and
the figure is **imported** from `lib/gears.J3_JOINT_TRAVEL_DEG` rather than
halved here — that constant is the one this project's J3 row already went
stale against once.

---

## 3. Predicted minimum clearances

Distances are to the nearest **motor** feature, in the host's frame.

| Joint | Nearest motor feature | Predicted min clearance | Verdict |
|---|---|---|---|
| J1 yaw | retaining **screw head**, Ø5.00 × 1.75, on the axis | see §4.1 — bore is Ø5.40, **0.20/side** | **TIGHT** |
| J2 shoulder | tab screw heads at host x 24.30 | **11.90 mm** to the straddle at x 12.40 | clear |
| J3 elbow | **near tab screw head** under the 36T | **2.00 mm axial**, with **2.15 mm of plan overlap** | **closest in the arm** |
| J4 wrist | tab screw heads at host x 21.90 | **9.50 mm** to `wrist_roll` at x 12.40 | clear |
| J5 roll | tab screw heads at host y 8.80 | **4.20 mm** to the rotator hub at y 13.00 | clear |
| gripper | retaining stack, Ø6.25, host y 0.20…2.75 | unknown — needs `gr_r_pitch` | **gate must measure** |
| effector | retaining stack, Ø6.25, host y 0.20…2.75 | unknown | **gate must measure** |

The retaining stack is only an obstacle where the driven hub does **not**
counterbore for it. Read from the parts, not judged here:

| Driven part | `access_d`? | Washer | Consequence |
|---|---|---|---|
| `shoulder_hub` (J2) | yes | recessed at the spline top | not an obstacle |
| `wrist_hub` (J4) | yes | recessed | not an obstacle |
| `wrist_rotator` (J5) | yes | recessed | not an obstacle |
| `j1_hub` | **no** | **removed at assembly** (see §4.1) | screw head only |
| `j3_pinion` (J3) | **no** | **proud**, Ø6.35 | obstacle |
| `gripper_pinion` | **no** | **proud**, Ø6.25 | obstacle |

---

## 4. What I expect to fail, and the fix for each

### 4.1 J1 — the placement is stale by **+2.40 mm**, and the washer must come out

`turntable_stator.py` builds the yaw deck by one subtraction it spells out in
a comment: `deck_z = tt_race_z − tt_hub_h − tt_hub_seat_z` =
`24.10 − 6.80 − 7.10` = **10.20**. Its tab-screw pilots start at that deck, so
the deck **is** the tab plane. `MOUNTS` says `shaft=(0, 0, 12.60)`.

**Delta +2.40 mm.** The J1 servo has moved three times in that part's own
history ("deepening the old horn pocket raised this servo 1.0", "the seating
gap lowered it 0.4", "dropping the horn altogether has now lowered it 3.0
more") and the table did not follow. Every gate that imports `MOUNTS` —
`leads`, `servo_fit`, and this one — places that servo 2.40 mm too high.

Separately, the washer at J1 is **not** in the running machine, and modelling
it as an obstacle would invent a strike. `j1_hub.py` calls it "ASSEMBLY AID
ONLY … pull the hub down WHILE the spline broaches"; `shoulder_bracket.py`
explains why it cannot stay ("the hub's top face IS the face bolted to the
rotor") and bores `tt_screw_bore` **Ø5.40**, which passes the Ø5.00 head and
will not pass the Ø6.25 washer. What remains is the **head**, at
**0.20 mm per side** in that bore — exactly the `free` fit, and the tightest
running clearance at J1.

**Fix.** Correct the J1 row to `shaft=(0, 0, 10.20)` — better, have
`turntable_stator.py` publish the deck as a shared datum and have `MOUNTS`
read it, so it cannot go stale a fourth time. Then confirm the bore's **depth**
from `tt_race_z` exceeds the 1.75 mm head height; nothing asserts that today.

### 4.2 J4 — the placement is stale by **−0.40 mm**

`forearm.py` prints its own answer: the tab plane is
`fa_plate_out + fa_j4_lobe_t` = `19.90 + 5.90` = **25.80**. `MOUNTS` says
`shaft=(25.4, 0, 0)` — `19.90 + 5.50`, the **pre-horn-migration** lobe.

The 0.40 is exactly `fa_j4_standoff`, the running gap added when `wrist_hub`
moved off the horn onto the spline. It buries the servo 0.40 mm into the
flange-recess floor. **`servo_fit` cannot see it**: its lattice is 1.50 mm and
a 0.40 mm sliver falls between samples, which is precisely how a sampled gate
reports 0.00 mm³ for a part that does not fit.

Confirming the same 0.40: with `shaft.x = 25.80` the `wrist_hub` seat lands on
`fa_plate_out` = 19.90, which is where `forearm.py` says it must land ("puts
the hub's seating face back exactly on `fa_plate_out`"). With 25.40 it lands
at 19.50 and the whole wrist stack is 0.40 out.

**Fix.** `shaft=(25.8, 0.0, 0.0)`.

### 4.3 J3 — the near tab screw head sits under the 36T gear

In the cap's frame the near tab screw head is at **x −10.35, r 2.00**, topping
out at **z 9.40**. The 36T gear turns about **x −27.20** with a tip radius of
**19.00**, in the band **z 11.40…21.40**.

- In plan the head is **16.85** from the gear axis: **2.15 mm inside** the tip
  circle.
- The only thing keeping them apart is **2.00 mm of axial gap**.

Nothing in this project models that head, so nothing has ever checked those
2.00 mm — and the gear's **journal collar** runs toward the plate from the
tooth band, which may reach lower than 11.40. This is the closest unguarded
approach in the arm.

**Fix, if the gate confirms it.** Cheapest first: a counterbore in
`j3_servo_cap`'s flange recess at the inboard tab only, sinking that head
flush. Failing that, raise `fa_j3_standoff` — but that is arm width, and
`lib/gears.py` derives it, so it is not a free edit.

### 4.4 J3 — the upper arm is not swept, and it should be

The gate sweeps `j3_gear` only. `upper_arm` turns about the same axis, its
fork straddles the forearm on the far side of the standoff, and the J3 servo
now hangs **outboard** on a 10.80 mm standoff — the most exposed motor in the
arm. Its pose needs the J2 chain, which the gate's document does not carry.
**This is the first thing to extend.**

### 4.5 gripper / effector — genuinely unknown

Both pinions leave the retaining stack **proud** (Ø6.25 washer + Ø5.00 head,
2.55 mm) and `gripper_pinion.py` says the shell "must leave the screw head and
the Ø6.25 washer clear above the top". The rack meshes at `gr_r_pitch`; if
that is under 3.13 mm the rack sweeps straight through the washer. These two
rows also have the least-certain poses in the table, which is why each station
carries a **frame self-check** (§6) that will disown the row rather than
report a confident wrong number.

---

## 5. What the gate models that `servo_fit` does not

1. **The moving half**, stepped through travel in `SWEEP_STEPS` positions.
2. **Exact clearance**, via `measureMinimumDistance` — not just sampled
   volume. A 0.30 mm graze is invisible at any lattice and is the complaint.
3. **The tab screw heads**, as solids on the tab **top**, at
   `2.0 × screw Ø` — the ratio `lib/servo_hub.horn_bolt()` already uses. The
   screw size is derived from `tab_hole_dia` (Ø2.1 → M2, Ø4.8 → M4), not
   chosen. **Graded ASSUMED — caliper before cutting a part to them.**
4. **The retaining screw and washer**, placed on the face they actually bear
   on: the top of the broach where the hub counterbores, the hub's top face
   where it does not, and omitted where the part says it is removed.
5. **The lead bundle against the moving half** — already in the case body from
   `servo_body.py`'s lead phase, and the gate **asserts** it is there rather
   than trusting it.
6. **The placement audit** — every row re-derived from the host's own
   parameters. This is what found §4.1 and §4.2.

---

## 6. The controls

**Positive control, per station.** No direction is chosen; one is
**measured**. `measureMinimumDistance` returns the two witness points of
closest approach — one on the moving body, one on the motor. The moving part
is translated along the vector **from its own witness point to the servo's**,
by that gap **plus** `CONTROL_OVERDRIVE_MM`. Landing its nearest point past
the other body's nearest point is contact **by construction**. Three checks,
any one of which fails the gate:

- **(a) they move together** — `dot(unit, servo_centre − moving_centre) > 0`.
  This is the check `servo_fit`'s first control lacked; a backwards control
  fails here, loudly, before it can report a comfortable zero.
- **(b) they are touching** — the re-measured gap after the shift is ~0.
- **(c) the sampler can see it** — control volume > `JAM_MM3`.

**Control on the audit itself.** `shoulder_bracket.py` states in its own
docstring that its `MOUNTS` row is right and is not to be touched. J2's delta
must therefore read **0.00**. It does (`19.90 + 9.70 = 29.60`). If it ever
does not, the audit is wrong and every other delta it prints is noise — which
is what makes the +2.40 and −0.40 worth acting on.

**Frame self-check, per station.** At travel zero the two halves are mating
parts on running fits, so the moving half must not be inside the host. A large
number there means the **pose** is wrong, not the part, and the station is
reported as measuring nothing. Same guard `_check_leads` calls SEATED.

---

## 7. Limits

- One mover per joint (§4.4).
- The loom is not modelled. Nothing models it.
- Every part is rigid. A 125 mm upper arm on a 2:1 elbow is not.
- Assembly **order** is `GATE leads`' question, not this one.
- Screw head sizes are **ASSUMED**.
- The servo solid is only as right as `lib/servo.py`, whose own docstring
  rates cheap-servo datasheet dimensions as weak.

A clear result here means the project no longer disagrees with **itself**
about its own motors. It is not the bench, and the bench is what raised this.
