# _flange — the J4 servo flange, and which of two statements is false

Status: **DECISION REQUIRED — no geometry changed by this document.**
Written 2026-08-31 by the agent repairing the horn-era gates. It may edit
`_check_shoulder`, `_gauge_horn`, `_check_j1`, `_gauge_verify` and
`_check_leads`; it may not edit `forearm.py`, and the fix is in `forearm.py`.

`GATE servo_fit` (`models/robotarm/_check_servo_fit.py`,
`specs/robotarm/_servo_fit.json`) measures **195.75 mm³** of MG90S inside the
forearm at J4, spanning host **x 23.40..24.90, y −19.95..10.05, z −4.70..5.80**.
This file works out what that is, decides which of two contradictory
statements about J4 is false, and prices the two ways of fixing it.

## The contradiction, as the project states it

1. **`forearm.py`**, `fa_lobe_t`: *"derived lobe thickness: the tabs bear on
   its outer face and the case top sits flush with the plate outer face."*
   The lobe's outer face is x 25.40 and its material runs inboard from there,
   so host material is at **x < 25.40**.
2. **`_check_leads.MOUNTS`**, row `J4 wrist`: `shaft=(25.40, 0, 0)`,
   `za=('x', −1)` — servo **+Z maps to host −X**. `lib/servo.py` puts 2.50 mm
   of mounting flange and then 3.00 mm more of case **above** the tab plane,
   so both of them land at **x < 25.40** as well, in the same material.

Both cannot be true. A mount that clamps a servo's tab plane must have its
material on the far side of that plane from the flange, and the forearm's
lobe is on the same side as the flange.

## The geometry, worked

All of it derives from `lib/servo.py` `MG90S` and `forearm.py`; nothing below
is typed.

    fa_plate_in  = wr_straddle/2 + fa_gap          = 12.00 + 0.40 = 12.40
    fa_plate_t   = wr_journal + wr_flange_t + 0.50 =  5.00 + 2.50 =  7.50
    fa_plate_out = 12.40 + 7.50                                   = 19.90
    fa_lobe_t    = tab_below_top + tab_thk         =  3.00 + 2.50 =  5.50
    tab plane    = 19.90 + 5.50                                   = 25.40   ← MOUNTS shaft.x

The lobe is joined from `fa_plate_out − fa_lobe_over` and cut to
`fa_plate_out + fa_lobe_t`: **material x 18.90 .. 25.40**. The servo window is
cut through the whole of it, `x 19.90 .. 25.40`, at
`case_l + fa_srv_clear` × `case_w + fa_srv_clear` = **23.80 × 13.40**.

With `za=('x', −1)`, host x = 25.40 − servo z:

| servo feature | servo z | host x | in the part? |
|---|---:|---:|---|
| spline top | +15.50 | **9.90** | inside the straddle |
| output boss top | +11.50 | **13.90** | inside the straddle |
| case top | +5.50 | **19.90** | = `fa_plate_out`, exactly as the comment says |
| tab (flange) top | +2.50 | **22.90** | **inside lobe material** |
| **TAB PLANE** | 0.00 | **25.40** | the lobe's outer face |
| case bottom | −18.50 | **43.90** | free air, outboard |

Across the arm, `xa=('y', −1)` puts host y = −servo x:

| | host y | length |
|---|---|---:|
| case | −16.80 .. +6.00 | 22.80 |
| **window** | −17.30 .. +6.50 | 23.80 |
| **flange** | −21.45 .. +10.65 | 32.10 |

The flange overhangs the window by **4.15 mm at each end**, over the full
12.40 of `case_w` — which is entirely inside the window's 13.40 in Z, so the
whole overhang lands on solid lobe. Two ears, each 4.15 × 12.40 × 2.50:

    2 × 128.65 = 257.3 mm³ gross, less the lead keyway and the two tab pilots

against **195.75 mm³ measured** on a 1.50 mm sample grid whose own docstring
calls the volume an estimate. The measured band `x 23.40..24.90` is two
sample planes inside the flange band **22.90 .. 25.40**; `y −19.95..10.05`
falls in the two ears; `z −4.70..5.80` is inside ±6.20. **The clash is the
flange, exactly, and nothing else.**

## Which statement is false: `MOUNTS` is RIGHT, the lobe is WRONG

`za=('x', −1)` is not a sign that can be flipped, because it is the sign that
makes J4 a joint at all. Flipping it to `+1` puts host x = 25.40 + servo z:

| | za = −1 (today) | za = +1 |
|---|---:|---:|
| output boss top | x **13.90** | x 36.90 |
| spline top | x **9.90** | x 40.90 |
| case bottom | x 43.90 (free air) | x **6.90** |

- **The spline would drive nothing.** `wrist_hub.py` is the J4 driven part —
  *"the wrist MG90S's OWN OUTPUT SPLINE drives this hub"* — and it declares
  `wh_seat_z` **5.90**, i.e. its seating face at host x 25.40 − 5.90 =
  **19.50**, four tenths inboard of the fork plate's outer face at 19.90.
  With `za = −1` the spline runs x 13.90..9.90, crossing `fa_plate_in` 12.40
  into the straddle where the roll housing is: it reaches the hub. With
  `za = +1` it tops out at x 40.90, **15.5 mm outboard of the lobe**, in air.
- **The case would go through the fork plate.** At `za = +1` the case runs
  x 6.90..25.40 — through the 5.50 window, then into 7.50 mm of solid fork
  plate (bored only Ø20.35 on the J4 axis) and out into the straddle. That is
  hundreds of mm³ against a Ø20.35 bore, not 195.75 mm³ in a 2.50 mm band.
- **The measurement itself rules it out.** The clash is 1.50 mm wide in X and
  30 mm long in Y at a plane 2.5 mm inside 25.40. That is a 2.50 mm plate
  32.10 long. It is not a 24.00 mm case ploughing through a 7.50 mm plate.

So the false statement is `fa_lobe_t`'s comment, and specifically its **first
half**. The second half is right: the case top does sit flush with
`fa_plate_out`, and 5.50 is the correct total, because 5.50 is exactly how
much MG90S sits above its own tab plane.

**What the comment misses is that those 5.50 mm are two different things.**
Reading up from `fa_plate_out`: 3.00 mm of bare case (`tab_below_top`), then
2.50 mm of flange (`tab_thk`) that is **9.30 mm wider on each side** than the
case. The lobe cuts one window for the whole 5.50, sized for the narrow half.
The tabs cannot bear on x 25.40 because at x 25.40 the tab **underside** is
level with the lobe's outer face and the tab **body** is already 2.50 mm
inside it.

## The fix, and what it costs

### Fix A — a flange recess in the lobe's outer face (RECOMMENDED)

Cut the lobe in two steps instead of one, in `forearm.py`:

| | from x | to x | size | today |
|---|---:|---:|---|---|
| case window | 19.90 | 22.90 | 23.80 × 13.40 | 19.90 → 25.40, same size |
| **flange recess** | 22.90 | 25.40 | `tab_span + clear` × `case_w + clear` ≈ 32.60 × 12.90 | does not exist |
| tab pilots | 19.90 | 22.90 | Ø1.80, from the **recess floor** | from the outer face |

Costs, all of them:

1. **`fa_lobe_pad` 3.50 → 4.15.** The recess reaches 16.30 from the case mid;
   the lobe reaches `tab_pitch/2 + lobe_pad` = 17.25. That leaves **0.95 mm**
   of end wall against `MIN_WALL_MM` 1.60, so the recess breaks out of both
   ends of the lobe as drawn. `lobe_pad` must be at least
   `16.30 − 13.75 + 1.60 = 4.15`. Cost: **+0.65 mm of lobe at each end in Y**.
   Across the width it passes untouched: `fa_lobe_z` 8.80 against a 6.45
   half-recess leaves 2.35 of wall.
2. **`fa_pilot_depth` 3.50 → 3.00.** Drilled from the recess floor at 22.90,
   3.50 deep reaches x 19.40 — 0.50 past `fa_plate_out` and inside the J4
   flange counterbore (Ø24.35, i.e. r 12.175; the pilot at y +8.35 is well
   within it). `forearm.py` already asserts against exactly this. The
   available depth becomes `tab_below_top` = 3.00, which is not a coincidence:
   the material under the flange **is** `tab_below_top`. Cost: **0.50 mm of
   self-tap engagement**, on a screw that has 3.00.
3. **~254 mm³ of new pocket**, which is the volume currently in collision.
   Nothing else moves: `fa_lobe_t` stays 5.50, the servo does not move,
   `wh_seat_z` does not move, the `wr_` contract is untouched, and the arm
   does not get wider.
4. **The bearing face changes from the tab underside to the tab top.** The
   screw head lands on the underside at x 25.40, flush with the lobe's outer
   face; the tab is clamped between that head and the recess floor at 22.90.
   That is a sound joint, but `lib/servo.py` says *"THE DATUM IS THE TAB
   PLANE, NOT THE CASE — the underside of the tabs, the face a bracket
   clamps."* Under Fix A the forearm clamps the other face. Either that
   sentence grows a second case, or `MOUNTS`' J4 `shaft.x` moves to 22.90 and
   `fa_lobe_t` is re-derived from it. **Do not leave both as they are** — this
   whole document exists because a datum drifted from its consumer.

### Fix B — stand the lobe off, so the tabs really do bear on an outer face

Put lobe material **outboard** of the tab plane (x 25.40 → 25.40 + t) on a
standoff spanning the 5.50 the case top and flange occupy, exactly as the J3
lobe already does with `fa_j3_standoff`.

Costs: **+5.50 mm of arm width on the +X side at the wrist** — the joint with
the least room, and `fa_l2` is called "the single highest-leverage number in
the arm"; a standoff web to fillet, and `fa_lobe_radius_j3`'s own comment
records that the J3 lobe's fillet had to come down from 6.00 to 4.50 for
precisely that reason; and the servo's 18.50 mm of case then hangs 5.50 mm
further outboard still. It buys a textbook panel mount. It is the more
expensive fix by an order of magnitude.

### Not a fix — widening the window to 32.60 for all 5.50

Proposed early because it is one number. It leaves nothing for the tabs to
bear on and no material for the pilots: the servo falls through its own hole.

## What must NOT change

**`_check_leads.MOUNTS['J4 wrist']['za']` stays `('x', −1)`.** It is correct,
`_check_servo_fit` imports it, and flipping it would silently reverse which
way the spline drives the wrist as well as inventing an 18.50 mm crash into
the fork plate. No edit has been made to `_check_leads.py`.

## The same fault at J2, and it is already measured

`GATE servo_fit` reports J2 shoulder **243.0 mm³** of case at host **x 28.30**,
y −8.60..9.40, z −35.95..15.05. `sb_plate_out` 19.90 + `sb_lobe_t` 9.70 puts
the J2 tab plane at **29.60** — which is `MOUNTS`' `shaft.x` for that row —
so the MG995 flange band is **x 27.10 .. 29.60** and 28.30 is a sample plane
inside it. The measured y span matches `case_w` 20.20 and the z span matches
`tab_span` 54.00. **It is the same signature: the tab plate overhanging the
case window onto pad material.** `shoulder_bracket` cuts Ø2.50 × 5.60 screw
slots there, which remove part of it and were never meant to be a flange
recess. Whatever is decided for J4 should be decided for J2 in the same pass.

## Open, and touching this stack

- **`wrist_hub.py` and `forearm.py` disagree about `fa_lobe_t` today**, before
  any flange work. `wrist_hub` declares `wh_seat_z` 5.90 and says outright
  that *"forearm.py has to stand the J4 servo off by 0.40 more than it does
  today"*; `fa_lobe_t` is still `tab_below_top + tab_thk` = 5.50 with no
  `case_gap` term. Under Fix A the whole stack resolves in one edit —
  `2.50` recess + `3.00` window + `0.40` gap = **5.90** — so settle it there
  rather than twice.
- **`_check_leads.py` cannot see any of this and never could.** Its `case`
  envelope is built from `(tab_top − case_h) .. tab_top` in servo Z: the case
  only. The flange is not in it, at any station. That is why J4 and J2 both
  read `CLEAR` from that gate while `GATE servo_fit` — which builds the whole
  solid from `servo_body.py` — measures 195.75 and 243.0 mm³. Adding the
  flange to that envelope would make `_check_leads` report `FRAME WRONG` at
  both stations, which is true but is the decision above, not a repair, so it
  has deliberately been left alone.

## Grading

| number | grade |
|---|---|
| `fa_plate_out` 19.90, `fa_lobe_t` 5.50, tab plane 25.40 | **DERIVED** from `forearm.py` |
| MG90S `tab_span` 32.10, `tab_thk` 2.50, `tab_below_top` 3.00, `case_w` 12.40 | **DATASHEET** — TowerPro table; `tab_thk` is ASSUMED micro-family and `tab_hole_pitch` 27.5 is DERIVED, both flagged in `lib/servo.py`. Caliper before cutting a recess to them. |
| 195.75 / 243.0 mm³ and their spans | **MEASURED** by `GATE servo_fit` at a 1.50 mm sample pitch — the volume is an estimate, the spans are not |
| 4.15 overhang, 257.3 mm³ gross, 0.95 end wall, 254 mm³ recess | **DERIVED** here from the two rows above |
| `fa_lobe_pad` 4.15, `fa_pilot_depth` 3.00 | **DERIVED** — floors set by `MIN_WALL_MM` and by the flange counterbore, not chosen |
