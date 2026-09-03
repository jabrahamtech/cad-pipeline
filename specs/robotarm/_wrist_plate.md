# The wrist plate — one print, the whole wrist

`models/robotarm/_export_plates.py`, `ONLY_PLATES = 'wrist'`
→ `exports/robotarm/plates/plate_wrist_v7.3mf`

Five printed pieces: **the whole J4 pitch / J5 roll assembly**, on one bed,
one profile, supports off, no brim. Nothing on it needs a per-object
override, which is the point of grouping it this way — the wrist is now a
sub-assembly you can print, build and hang off the forearm on its own.

> **NOT BUILT.** The Fusion add-in is out of this session, so the script has
> not been run and no 3MF exists yet. Every number below is **DERIVED** from
> the parts' own user parameters or **MEASURED** off the volume ledger, and
> is marked as such. Nothing here is a claim that the plate exports, packs or
> prints.

> **BLOCKER, read before running.** `specs/robotarm/_volumes.json` still
> holds **13352.026 mm³** for `wrist_roll`, which is the **monolith** — the
> ledger has not been rewritten since the part became a clamshell half. The
> exporter's volume assert will fail on `wrist_roll` until
> `_check_ledger` BATCH 1 has been re-run and the ledger rewritten from a run
> someone has read. That failure is correct and must not be worked around:
> the assert is the only thing between this plate and exporting geometry no
> gate has seen.

---

## 1. What is on the plate, and what is not

| piece | qty | why it is here |
|---|---|---|
| `wrist_roll` | **2** | the J4/J5 housing, split on x = 0 into a clamshell. One design, **the second copy mirrored** — see §3 |
| `wrist_hub` | 2 | the J4 pivot pair, one driven off the MG90S spline and one idling in the opposite fork plate |
| `wrist_rotator` | 1 | J5. The disc on the SG90's own spline that the hand bolts to |

**Out, and why** — the boundary is `models/robotarm/_check_wrist.py`'s
`PARTS`, which is the wrist gate's own definition of the joint:

- **`forearm`** — in `_check_wrist.PARTS`, but it is the *arm segment that
  carries* the wrist, not part of it. It is 13 g, it is the only part in the
  project that wants supports, and `NEVER_TOGETHER` keeps it away from
  `turntable_stator`. It stays on plate 2.
- **`j3_axle`** — J3 is the **elbow**. It is not in `_check_wrist.PARTS`, it
  is not in `ORIENT`, and it is in `_check_ledger` batch 4 with the rest of
  the J3 reduction. Nothing about it is a wrist piece.
- **The J3 `wrist_hub` pair.** `wrist_hub` is used five times across the arm
  (J2 −X, J3 ±X, J4 ±X). Only the **J4 pair** is the wrist's, which is what
  `_assembly.md` means by "`wrist_hub` × 2 (J4)". The other three ride with
  the joints they belong to. The parts are interchangeable, so this is a
  bookkeeping boundary and not a fit one.
- **Fasteners and servos** — bought, never modelled (CLAUDE.md). They are the
  BOM in §6, not bodies on the bed.

## 2. Orientation of each piece, and why

Orientations are **baked into the 3MF**. If you auto-arrange in the slicer,
keep rotation locked.

| piece | on the bed | `ORIENT` spec | why this way up |
|---|---|---|---|
| `wrist_roll` ×2 | **outer side face** (x = `wro_half_x` = 12.0) | `('y', 90)` | see below — it is the whole reason the part was split |
| `wrist_hub` ×2 | **flange face**, hex up | `None` | the part's own printability gate: "flange face on the bed, built +Z". Ø24 flange = ~452 mm² of first layer against the hex's 216, and every cross-section shrinks going up. The hex flats end up loaded *within* layers, which is the direction J4's torque runs |
| `wrist_rotator` | **front face**, Ø36 disc down, hub up | `('x', 180)` | turned over from the old back-face-down: the disc is then the first layer (~950 mm² against the hub's 64) and the section only ever shrinks going up |

### `wrist_roll`: outer face down, built −X — **not** split-face-down

The part's local frame has the origin on the J4 pitch axis, +X along it, and
this half occupies x ≥ 0. The **split face is x = 0** and the **outer side
face is x = `wro_half_x`**. "Outer face on the bed, built −X" is therefore
exactly *"local +X points straight down"*, and that is what the exporter
asserts, against `wro_half_x` read out of the document rather than a typed
12.0.

`gripper_shell` and `pruner_shell` print **split-face-down** and this one
does not. The rule the three actually share is *"pockets open at the top of
the build"*, not *"split face on the bed"* — their cavities are cut up from
z = 0 and this one's are not. Split-face-down here re-roofs everything the
split just opened: the servo bay becomes a **618 mm² ceiling on a 22.9 mm
bridge**, both tab slots and the lead keyway get roofs of their own, and the
Ø11 rotator half-bore becomes an arch over `MAX_OVERHANG_DEG` for its top
1.29 mm. That is the print the bench has already rejected **twice**.

Outer-face-down inverts all of it. Every cavity opens at the **top** face,
the half-bore only ever widens going up so it needs no teardrop, and the
entire outer form is one prism along the build axis — so **no outer face can
be an overhang by construction**. Build height 12.0 mm, the shortest piece
on the plate.

`wrist_rotator`'s row in `ORIENT` said `None` ("back face down") until this
pass, which stood the part on its Ø10.5 hub for ~64 mm² of bed contact —
`wrist_rotator.py` was turned over and the table never followed it.
`wrist_roll`'s row said `('x', 90)` ("back face down, built +Y"), which was
the **monolith's** orientation. Both were stale, both are corrected here, and
both are now asserted rather than described.

## 3. The mirrored pair — **the two `wrist_roll` bodies are not the same part**

One printed design, two copies, **the second one a mirror image**. Not a
turn-over: the YZ silhouette has a **keel** below and a **crest** above, so
the part is *chiral*. `gripper_shell` and `pruner_shell` are clamshells whose
halves are the same solid rotated; this one is not, and only a genuine
reflection produces the other half.

**How the exporter proves it is a mirror and not a 180° turn.** A rotation
preserves handedness (determinant **+1**); a reflection inverts it
(determinant **−1**). `check3()` takes the determinant of the matrix that is
actually handed to `addExistingComponent` — per piece, in both the measuring
pass and the build pass — and asserts it against what that copy is supposed
to be. **A 180° turn about any axis scores +1 and cannot pass as the
mirror.** The same function asserts the matrix is rigid (`m·mᵀ = I`, so
"determinant −1" means a reflection and not a squash) and that the face the
print orientation put on the bed is *still* on the bed after the mirror and
after any packing yaw.

The mirror is applied in the **bed's** x, after the print rotation — a
slicer's *Mirror* button. That is not a convenience: a mirror in global x
moves nothing in z, so it **cannot** change which face is on the bed. It is
also exactly the half that is wanted, because

    MIRROR_X(global) · R_y(90)  ≡  R_y(−90) · MIRROR_X(local)

and the right-hand side is, literally, *"reflect the part in its own split
plane, then stand the result on its outer face"*. (Any reflection of a solid
is congruent to any other by a rigid motion, so *which* plane is reflected in
never changes what comes off the bed — only the handedness does. That is why
the determinant is the complete test.)

### Telling them apart once they are printed — do this at the printer

They are the same size, the same mass, the same silhouette. **Mark them
before they leave the bed**, because once they are in a tray with the hubs
they are genuinely hard to sort.

**On the bed.** Both halves sit outer-face-down with their cavities open
upward, side by side on the plate's single shelf. As the script places them,
the **as-drawn** half is the **left** of the two (lower X) and the **mirror**
is to its right — the run prints both coordinates, so check the output rather
than trusting this sentence.

**In the hand, if they are already mixed.** Hold a half with the **hollow
side facing you** and the **crest up, keel down** — the keel is the long
bevelled wedge along one edge and it is the deepest part; the crest is the
small raised pad on the opposite edge. Now look at which side the **front
face** is on. The front face is the one carrying the half of the **Ø11
rotator bore** — a semicircular notch — and it is nearer the crest.

| half | front face / rotator notch is on the | goes on |
|---|---|---|
| **as drawn** (`x ≥ 0`) | **RIGHT** | the arm's **+X** side — the same side the J4 MG90S hangs on |
| **mirrored** (`x ≤ 0`) | **LEFT** | the arm's **−X** side |

That test is a straight consequence of the frame: looking at the split face
of the as-drawn half means looking along +X with +Z up, and +Y (front, toward
the hand) is then on the right. For its mirror you are looking along −X and
+Y is on the left. **DERIVED.**

**Marking.** A dot of marker on the *outer* face — the one that was on the
bed — of the +X half. Do not mark the split face: it is the sealing face and
it carries the `split_face_chamfer` relief.

## 4. Plate layout and mass

Bed **256 × 256** (`ENVELOPE_SINGLE`), `MARGIN` 6.0, `GAP` 4.0. Footprints
**DERIVED** from each part's own parameters (`wro_half_x` 12.0,
`wro_y_back/​y_front` −14.0/17.0, `wro_z_bot/​crest_top` −23.20/12.70;
`wr_flange_d` 24.0 and the 5.0 + 2.0 + 3.8 hub stack; `wrt_disc_d` 36.0 and
the 4.0 + 6.0 rotator stack).

| piece | footprint mm | height mm | solid mm³ | mass g |
|---|---|---|---|---|
| `wrist_rotator` | 36.0 × 36.0 | 10.0 | 5524.234 (MEASURED, ledger) | **4.56** |
| `wrist_roll` (as drawn) | 35.9 × 31.0 | 12.0 | ~7277 (**ESTIMATED**) | **~6.01** |
| `wrist_roll` (MIRRORED) | 35.9 × 31.0 | 12.0 | ~7277 (**ESTIMATED**) | **~6.01** |
| `wrist_hub` | 24.0 × 24.0 | 10.8 | 2815.994 (MEASURED, ledger) | **2.32** |
| `wrist_hub` | 24.0 × 24.0 | 10.8 | 2815.994 (MEASURED, ledger) | **2.32** |
| | | | | **≈ 21.2 g total** |

Mass = solid mm³ × 1.27 g/cm³ (PETG, **DATASHEET**) × 0.65 (walls + infill,
**ASSUMED** — the project's standing factor) ÷ 1000.

**The two `wrist_roll` figures are estimates and they are the weakest numbers
on this page.** The ledger row is the monolith, so there is no measured
volume for the half. 7277 mm³ is the monolith's 13352.026 scaled by the
**+9 %** the `_printability.md` addendum gives for the pair, halved — and
that +9 % was itself computed, not built. The script reports the real number
the moment it runs, because it measures the body and cross-checks the ledger.
Do not quote 6.01 g anywhere it matters until it has.

**Everything lands on one shelf**, `X 6.0…177.8, Y 6.0…42.0` — a
**171.8 × 36.0 mm** band, **7.1 %** of the bed, no yaw needed on any piece.
Tallest piece 12.0 mm, well under `TALL_MM` 40, so there is no knock-off risk
to place at the back.

## 5. Slicer settings

- **SUPPORTS: OFF.** Every piece here. Not a preference on any of them:
  - `wrist_roll` — **nothing over `MAX_OVERHANG_DEG` 50.0**. Two bridges
    remain: the J4 hex socket floor, a **18.48 mm** span (across corners)
    over a pocket that opens at the bed, anchored on all six walls —
    **46 % of `MAX_BRIDGE_MM`** — and three **4.85 mm** annular fastener-seat
    shoulders 2.4 mm up. The socket floor is a **datum as well as a bridge**:
    the hub's hex boss bottoms on it and *that* locates J4 axially. 0.2 mm of
    droop pushes the hub 0.2 mm outboard, which `HEX_PIVOT.cbore_extra` has
    0.5 mm of slack for, and **both halves droop equally**.
  - `wrist_hub` — every cross-section shrinks going up.
  - `wrist_rotator` — sections shrink going up. The price of the flip is four
    **Ø4.0 circular bridges** under 0.50 mm of disc skin (the M3 insert holes,
    now blind at the top) and one **1.00 mm annular step** at the top of the
    broach bore. Four small bridges a slicer will not even flag.
- **BRIM: none.** `base_lid` is the only part in the project that needs one
  and it is not on this plate.
- **Profile: the same one the gauge plate was printed on**, or the fits stop
  meaning anything. PETG, 0.2 mm layers.
- **Unresolved, flagged not decided:** `_print_plan.md` says 3 walls /
  15–20 % infill for the arm; `wrist_hub.md`'s own print plan says **4 walls /
  40 % infill**, and the 0.65 mass factor sits between the two. Pick one for
  the whole plate before slicing and record which — do not let two pieces off
  one bed disagree about their own wall count.

## 6. Fasteners to have ready — J4 and J5

Not printed, not on the plate. Sizes from `lib/design_rules.FASTENER_MM`,
`lib/servo.py` and `lib/servo_hub.py`.

### The clamshell — `wrist_roll` × 2

| item | qty | note |
|---|---|---|
| M2 socket head cap screw × 20 | **3** | see the length warning below |
| M2 plain hex nut (ISO 4032, 1.6 thick) | **3** | drops into the 4.20 af seat; it cannot spin |

**M2, not the arm's M3, and that is a real wart** — a second hex key in the
kit. The one-design-mirrored trick needs **one recess that takes either end
of the bolt**, because a mirrored half does not know whether it is the head
side or the nut side. M2's Ø3.80 head fits inside a 4.20-af nut pocket; M3's
Ø6.00 head does not fit inside 5.70, so M3 would need two different recesses,
two mirror-image scripts, and the duplicated 30-parameter servo block that
`lib/joints.py` exists to prevent. M3 also does not fit the keel at all
without breaking `wr_sweep_r`.

> **LENGTH IS TIGHT AND IT IS NOT CLEANLY SOLVED — DERIVED, FLAGGED.**
> The seat is 2.4 deep, cut from each half's outer face; assembled the pair is
> 24.0 across, so both seat floors are at x = ±9.6. The nut bears on the far
> floor and spans 9.6 → 11.2. **Full nut engagement needs 20.8 mm under the
> head; anything past 21.6 mm stands proud of the outer face**, into the
> 0.40 mm `HEX_PIVOT.gap` the fork plate runs in — and anything proud there
> fouls the wrist at full pitch. No standard M2 length falls in that 0.8 mm
> window. **M2 × 20 leaves 0.8 mm of the 1.6 mm nut engaged**; M2 × 22 stands
> 0.4 mm proud. Buy **M2 × 20**, and either accept two threads of engagement
> or face 1.2 mm off an M2 × 22. This is `wrist_roll.py`'s to settle, not
> this plate's.

### J4 — wrist pitch

| item | qty | note |
|---|---|---|
| MG90S servo | 1 | drive side; `wrist_hub` bores straight onto its spline |
| Servo mounting screw, 1.8 pilot | 2 | MG90S into the forearm, as supplied |
| MG90S retaining screw, Ø2.5 | 1 | as supplied with the servo |
| Flat washer, **OD ≥ 6.35** | **1** | **NOT OPTIONAL.** `wh_washer_d`. The Ø2.5 screw's ~Ø5 head passes straight into the Ø4.75 broach bore and clamps nothing; without the washer the hub walks up the spline |
| M3 socket screw | 1 | idler side, down the same Ø6.75 `wh_access_d` bore |

### J5 — roll

| item | qty | note |
|---|---|---|
| SG90 servo | 1 | laid into the open bay, not threaded into a blind hole — that is what the split bought |
| Servo mounting screw, 1.8 pilot | 2 | through the two tab slots, now open pockets |
| SG90 retaining screw, Ø2.5 | 1 | as supplied |
| Flat washer, **OD ≥ 6.3** | **1** | **NOT OPTIONAL**, `wrt_washer_d`, same failure as J4: without it the disc walks up the spline and the hand droops |
| M3 heat-set insert, Ø4.0 | **4** | into `wrist_rotator` from the front face — a vertical hole, which is the orientation inserts want |
| M3 × 12 socket screw | **4** | the effector onto `wrist_rotator`. This is the arm's swap point: pull four screws and the hand comes off |

**Assembly order the fasteners imply.** The SG90's retaining screw and its
washer are driven down `wrt_access_d` from the **rotator's front face**, so
the screw goes in **before** the effector does. That path is forward of
`wro_y_front`; both `wrist_roll` halves stop behind it and the crest stops at
`wro_crest_y1`, so **the wrist stays serviceable assembled** — you do not
have to split the clamshell to get at the J5 screw.

## 7. What this page does not settle

- The plate has **never been exported**, and neither has the split
  `wrist_roll` ever been built. No geometry here is verified.
- The ledger blocker at the top is a hard stop on running the exporter.
- The M2 bolt length has no clean standard answer (§6).
- The wall/infill disagreement between `_print_plan.md` and `wrist_hub.md`
  (§5) is flagged, not resolved.
- Bridging *behaviour* is not verified anywhere: the spans and angles are
  computed from the polygons the scripts draw. Slice the plate with support
  off and **look at the preview** before committing filament.
