# forearm — printability, and the split

**2026-09-03.** Written because Jonathan printed this part and said:

> "the major issue is the forearm piece - where the motors attach it is also
> just impossible to print"

That is bench evidence and it outranks everything below it. The forearm is
now **four printed pieces** — `forearm_px`, `forearm_nx` and two copies of
`forearm_rail` — sharing one contract in `lib/forearm_split.py`. `forearm.py`
still builds the assembled reference and still owns every `fa_*` parameter.

## Provenance

| grade | meaning |
|---|---|
| MEASURED (bench) | Jonathan printed it |
| DERIVED (static) | computed from the scripts' own extrusion lists by voxelising at 0.25 mm outside Fusion — **not built, not printed** |
| DERIVED | parameter arithmetic out of `forearm.py` / `lib/` |
| HANDBOOK | `lib/design_rules.py`, `lib/arm_loads.py` |

**Nothing here was built in Fusion or printed.** Areas are good to a few
percent; *stations* are exact. Thresholds, HANDBOOK: `MAX_OVERHANG_DEG`
**50.0**, `MAX_BRIDGE_MM` **40.0**.

Support-needed area = horizontally-projected area whose local overhang
exceeds 50°. In every orientation considered here each such surface is a flat
**90° ceiling**, because every face in this part except the finish fillets is
prismatic along X. There is no middle ground.

## 1. The one-piece part, and why no orientation saves it

`forearm.py`'s docstring said **−X face down, built along +X**, and
`_export_plates.py:227` turns it `('y', -90)` — R_y(−90) maps local +X onto
bed +Z. **The two agree; the docstring was not stale.** It is also the least
bad of six. DERIVED (static):

| orientation | height | bed | support |
|---|---|---|---|
| −Y face down | 74.0 | **26 mm²** | 834 mm² |
| +Y face down | 74.0 | **26 mm²** | 941 mm² |
| +Z face down | 28.5 | 33 mm² | 2433 mm² |
| −Z face down | 28.5 | 4 mm² | 2453 mm² |
| **−X face down (as shipped)** | 56.5 | 330 mm² | **2802 mm²** |
| +X face down | 56.5 | 194 mm² | 2945 mm² |

The Y-down pair score best and are unbuildable — a 74 mm tower on 26 mm² of
bed — and every non-X orientation lays **all four journal bores on their
sides**. A horizontal Ø20.35 bore exceeds 50° for ±40° of arc either side of
its crown: a **13.1 mm** unsupported span sagging into a rotating fit.

### BEFORE, by station (−X down, 2802 mm²)

| x | mm² | feature | character |
|---|---|---|---|
| +12.40 | **918** | **+X plate inner face** | 72.4 × 27.8 slab floating 43.1 mm up on two rails |
| −19.90 | 686 | −X plate outer face | incl. the J3 boss disc, Ø27.6, floating 10.8 mm on nothing |
| −15.90 | 526 | link waist over the boss discs | bridges 17.5 → 37.8 mm |
| +19.40 | 231 | 608ZZ pocket roof | 4.49 mm annular ledge under a 0.50 shoulder |
| +18.90 | 189 | J4 lobe underside | overhangs its boss by 9.53 mm |
| +19.90 | 121 | J4 counterbore, roofed by the lobe | ~5.7 mm runs |
| −17.40 | 123 | −X counterbore roof | 2.0 mm ledge |

**The two-step J4 pocket is innocent** and it is worth recording so nobody
"simplifies" it back. Built along +X the case window and the flange recess
both open **upward**, and the recess (32.60) is *wider* than the window
(23.80), so the step is an upward-facing tab bed. Ceiling at the recess floor
and at the pilot tops: **0.00 mm² each**. The flange recess that fixed GATE
servo_fit costs nothing to print.

### `fa_lobe_seat` — a real defect, found on the way

Both servo blocks start one `fa_lobe_over` **1.00** inside `fa_plate_out`
19.90, i.e. at 18.90 — but the plate is `fa_plate_t` **only inside the boss
circles**. Elsewhere it is `fa_waist_t` **3.50**, ending at 15.90.

    18.90 − 15.90 = 3.00 mm of air under both servo blocks

`fa_lobe_over` assumed a plate that was not there. The J4 lobe overhung its
boss by 9.53 mm with **184.5 mm² of underside over nothing**, directly under
the servo the complaint names. `fa_lobe_seat` = `plate_t − waist_t +
lobe_over` puts the plate back at full thickness under each block. It is a
stiffness fix too: the J4 servo's stall couple was being carried by a 1.00 mm
lip. This stays, and both plates carry it.

## 2. Why the split is **not** at x = 0

The obvious plane is the middle, the way `wrist_roll` was split. **Measured,
it does not work.** With the seam at x = 0 each half still contains half the
straddle, so each half still floats its own plate:

| piece | best orientation | support |
|---|---|---|
| +X half, x 0…25.80 | tab plane down | **1194 mm²** |
| −X half, x −30.70…0 | standoff face down | **1083 mm²** |

Splitting in the middle halves the *drop* and fixes nothing.

## 3. What does work, and why there are three pieces

A side plate is a **horizontal slab** when it is built along X. A slab prints
perfectly when it is the **first layer** and impossibly when it is not. So
each plate is split off **at its own inner face** and printed inner-face-down
— 994 and 1048 mm² of first layer — and everything outboard of it (boss,
seat, servo block) is narrower than the plate and lands on it. Every pocket
that was a roof now opens at the top of the build, and all four journal bores
stay vertical.

**The third piece is forced by that, not chosen.** Nothing that reaches
across the straddle can belong to a plate that begins at its own inner face,
because "across the straddle" is "below the bed". The box-beam rails are the
only thing that does reach across, so they become their own piece — and a
prism along X, which prints with zero overhang.

**Both rails are one design.** The straddle is symmetric in Z (the outline,
both sweep cylinders, the elbow relief, the duct), and the piece is symmetric
in X, so the bottom rail is the top one **turned 180° about Y**. A rotation,
not a reflection — no handedness, no second file. `forearm_rail.py` asserts
the X symmetry against the built body rather than asserting the claim.

### The pieces

| file | contents | print |
|---|---|---|
| `forearm_px.py` | J4 journal + flange counterbore, **608ZZ idler pocket**, servo seat, **J4 servo lobe** (window, flange recess, keyway, tab pilots) | inner face down, x = +12.40 on the bed, built +X |
| `forearm_nx.py` | J4 journal + counterbore, **J3 drive bore** (no counterbore — `j3_gear` has no flange), servo seat, **J3 standoff web** + the `fa_cap_*` interface | inner face down, x = −12.40 on the bed, built −X |
| `forearm_rail.py` | the box-beam flange, cut from the outline by both sweeps | either end face down, built along X — **a prism** |
| `lib/forearm_split.py` | `Silhouette`, `Seat`, `Straddle`, `Seam`, `ServoBlock` — the derivations more than one script needs | — |

`lib/forearm_split.py` owns the **solve**, not the numbers: `forearm.py`
still declares every `fa_*`, because `wrist_hub.py`, `j3_servo_cap.py`,
`_check_leads.py` and `_check_servo_fit.py` read them out of the document by
name. Each script feeds what it read into the same solvers. `ServoBlock` in
particular replaces the **third** hand copy of the servo-placement
arithmetic; `forearm_px` would have been the fourth.

## 4. AFTER

DERIVED (static).

| piece | bed | height | volume | mass | support |
|---|---|---|---|---|---|
| `forearm_px` | 994 mm² | 13.5 mm | 7351 mm³ | **9.34 g** | 390.5 mm² |
| `forearm_nx` | 1048 mm² | 18.2 mm | 10120 mm³ | **12.85 g** | 369.6 mm² |
| `forearm_rail` ×2 | 69 mm² | 24.8 mm | 1708 mm³ ea | **2.17 g** ea | **0.0 mm²** |
| **assembly** | | | 20887 mm³ | **26.53 g** | **760.1 mm²** |

2802 → 2391 (seat) → **760 mm²**, a **73 %** reduction. Plus 8 × M3 × 12.

Where it went:

| x | one piece | split | feature |
|---|---|---|---|
| +12.40 | 918 | **0** | the +X plate inner face — it is the bed now |
| −19.90 | 686 | **0** | the −X plate outer face — the build runs the other way |
| −15.90 | 526 | **0** | the waist — thick→thin as the build rises |
| −17.40 | 123 | **0** | −X counterbore — opens upward |
| +19.40 | 231 | 231 | 608ZZ pocket roof — §7 |
| +19.90 | 121 | 121 | J4 counterbore under the lobe |
| −19.90 | (in 686) | 317 | J4 counterbore under the standoff block |
| +18.90 / −18.90 | 189 | 38 / 52 | seat ledges, 1.60 mm |

## 5. The seam

Four joints — two rails × two plates — **2 × M3 each, 8 total**. The screw is
a **clearance** fit in the plate and **self-taps** in the rail, so tightening
pulls the faces together instead of jacking them apart on a shared thread.
The rail's pilot is a **through** bore, tapped `fa_seam_engage` 8.0 from each
end with 8.80 of untapped bore between: a blind pocket would roof itself, and
the rail's whole claim is that it is a prism.

**Nothing about it is chosen.** `lib/forearm_split.Seam` solves it from four
things that each bind:

| binds | gives |
|---|---|
| the head must stay inside the link outline — it lands on the waist's outer face, in the empty band out to `fa_plate_out` | `fa_seam_z` = `waist_z − head_r − margin` = **8.90** |
| the pilot needs half a bore and one wall of floor under it | `fa_duct_z` = **6.00** (was a typed 9.00) → `fa_rail_z` **6.00** |
| the rail's length at that height comes from the two sweeps | y −34.98…−23.79, **11.19 mm** |
| three equal walls around two pilots | wall **2.00** ≥ 1.60 ✓, stations y **−31.685 / −27.087** |

Head clearance to the outline: **+0.181 mm** at the tighter station.
Duct left for the loom: **24.8 × 12.0 mm**.

### Load path, priced

Layers lie normal to X in all four pieces, so the beam's bending stress —
which runs along Y — is **in-plane**, the strong direction, in both plates
and in the rails. HANDBOOK section properties, `lib/arm_loads.py` masses:

    box section about X   I = 33062 mm4   (was 24581 with the 3.00 rail: +35 %)
                          S = 2755 mm3    flange centroid z = 9.00

    outboard mass         158.8 g  ->  V = 1.557 N
    gravity moment at J3  1250.8 g.cm = 122.7 N.mm
    J4 servo STALL        2.0 kg.cm  = 196.1 N.mm about X, on the +X plate alone
    bending stress        (196.1 + 122.7) / 2755 = 0.116 MPa

    worst screw:
      half the J4 stall couple crossing to the other plate,
        98.1 N.mm over an 18.0 mm lever   = 5.45 N / joint = 2.72 N / screw
      flange shear flow q = VQ/I = 0.0631 N/mm
        over the 8.34 mm joint            = 0.53 N / joint = 0.26 N / screw
      total 2.99 N  x SAFETY_FACTOR cyclic 4.0 = 11.95 N

    capacity of one M3:
      bearing, plate clearance hole  3.4 x 3.50 = 11.9 mm2 -> 1.00 MPa   45x
      bearing, rail pilot wall       2.6 x 8.00 = 20.8 mm2 -> 0.57 MPa   78x
      thread shear-out in the rail   pi x 3.0 x 8.0 = 75.4 mm2 @ 20 MPa = 1508 N

**45× on the binding mode, at cyclic safety factor 4.** The seam does not
need a keyed tongue or a bonded lap; the honest reason is that this beam is
nowhere near its section's capacity — 0.116 MPa against tens of MPa — so the
joint only ever has to carry a few newtons.

**What the split genuinely weakens is torsion about Y**, because a closed box
carries torsion as a continuous shear flow and eight bolts are not
continuous. It is affordable here because there is almost no torsion to
carry: the two MG90S sit on **opposite** sides (+4.34 and −4.73 N·mm) and
very nearly cancel, and the head is on the J4 axis at x ≈ 0. **If a future
payload is offset in X, re-open this.**

## 6. `_HANDOFF` §9's 71× is untouched

The margin is on the **J3 standoff web in torsion**, and every term survives:
the web stays **integral to `forearm_nx`** (only the servo *pad* left, as
`j3_servo_cap`, in §10); its prism is unchanged; and §9's allowable is chosen
because "the forearm builds along +X, so the layers lie normal to X and this
loading is across them". `forearm_nx` builds along **−X** — the same layer
planes, the same weak direction, the same allowable. Nothing in §9 moves.

## 7. The 608ZZ pocket roof — checked, and it does **not** go away

It was worth checking and the answer is no. `forearm_px` prints inner-face-
down, and the pocket is cut *from* the inner face, so it opens onto the bed
and its 0.50 mm shoulder roofs it: a **4.49 mm annular ledge, 231 mm²** — a
cantilever, not a bridge. Printing that plate outer-face-down would open it
to the sky, but the lobe protrudes 5.90 mm past the outer face, so that face
cannot be the bed.

Cutting the pocket from the **outer** face instead removes the ceiling
completely — and moves the retaining shoulder to the other side of the
bearing's inner race. `j3_axle.py`'s collar lands inside that race and
`_check_elbow.py` asserts both ends. **That is their contract, not this
pass's.** Flagged, not fixed.

## 8. GATE servo_fit — J4 preserved

The seat and the seam are entirely **inboard** of every servo surface.

    fa_plate_out                        = 19.90
    fa_j4_lobe_t = fa_lobe_t + fa_j4_standoff = 5.50 + 0.40 = 5.90  ( = wh_seat_z )
    tab plane    = 19.90 + 5.90         = 25.80   ( _check_leads MOUNTS )

    case window     x 19.90 -> 23.30    (fa_j4_lobe_t - fa_tab_thk = 3.40)
    flange recess   x 23.30 -> 25.80    (fa_tab_thk = 2.50)
    tab pilots      x 20.30 -> 23.30    (from the recess floor, 3.00 deep)
    MG90S case top  x 20.30             (fa_j4_standoff 0.40 off the plate)

    fa_lobe_seat spans x 14.90 -> 19.90 — it ENDS at fa_plate_out, 0.40 below
    the case top and 5.90 below the tab plane.
    fa_seam_* live at x 12.40 -> 15.90, inboard of everything.

Nothing moved: not the tab plane, not the window, recess, pilots, keyway, nor
`wh_seat_z`, `fa_j4_lobe_t`, `fa_j4_standoff`, `fa_cap_*` or `fa_lobe_pad`.
`forearm_px.py` asserts its own bounding box does not pass x 25.80.
**GATE servo_fit's J4 row must still read `case_mm3` 0.0 / `control_mm3`
351.0** — confirm on the next build; this pass did not run it.

The only parameters whose *values* changed are `fa_duct_z` 9.00 → 6.00 and
`fa_rail_z` 3.00 → 6.00, and both are forearm-local: nothing outside
`forearm.py` reads either.

## 9. What still needs support — the honest verdict

760 mm², in three kinds, measured against the repo's **two** rules:

| mm² | what | verdict |
|---|---|---|
| 438 | the J4 flange counterbore on both plates, roofed by the servo block above it (121 px + 317 nx) | **BRIDGES.** Max span 24.35 mm against `MAX_BRIDGE_MM` 40.0, with `fa_cbore_extra` 0.50 of designed clearance beneath, so sag touches nothing. **Passes** the repo's own rule. |
| 90 | the seat ledges, where each block oversails its seat by one `fa_wall` (38 px + 52 nx) | 1.60 mm — one nozzle line. Self-supporting in practice; strictly still 90°. |
| **231** | **the 608ZZ pocket shoulder** — a 4.49 mm ledge, 0.50 thick | **FAILS.** The one item the split does not fix, and §7 says why. |

So: **the rails meet "support off, nothing over 50°" exactly. The two plates
do not** — one by 231 mm² that needs another file's contract, and one by
90 mm² of one-wall ledges. I am not going to claim otherwise. The change that
matters is elsewhere: **none of the remaining 760 mm² is inside the straddle,
none is structural, and none touches a running face.** The 918 mm² that had
to be supported through a 24.8 mm slot 43 mm deep, scarring `fa_gap` 0.40 on
the way out, is gone.

## 10. Follow-ups this pass could not make

1. **`_export_plates.py` still has a row for `forearm`** — `PLATE_OF`,
   `ORIENT ('y', -90)` and `NEVER_TOGETHER ('forearm', 'turntable_stator')`.
   It knows nothing about the three pieces, and `forearm` must not be printed
   any more. The `NEVER_TOGETHER` entry exists *because* the forearm wanted
   supports; with the rails support-free and the plates needing none the
   slicer cannot help with, that constraint can probably go. **Not my file.**
2. **`j3_servo_cap.py` is silently unlinted.** Its docstring contains the
   word `tests/test_fusion_scripts.py` scans for, in a sentence about hex-key
   clearance — so `test_no_magic_numbers_in_geometry`,
   `test_no_unused_parameters` and `test_entities_are_named` all **skip** it.
   It is the only part script in the project in that state. Exactly the trap
   `forearm.py`'s docstring warns about at length. **Not my file.**
3. **The 608ZZ retention flip** — §7.
4. **`specs/robotarm/_assembly.md`** needs the new piece tree and an assembly
   order: rails to `forearm_nx` first (the standoff side has no obstruction),
   then `forearm_px` over the wrist hub, then `j3_servo_cap`.
5. `_HANDOFF.md` §10's `fa_cap_screw_y` 11.65 / `fa_cap_reach` 16.35 are
   **stale** — they are module-1.25 era. Today's solve gives **4.90** and
   **9.60**. Several param comments in `forearm.py` carry the same era's
   numbers in prose (`r 12.90`, "gear disc is 47.5", `seat_z` 6.70).
