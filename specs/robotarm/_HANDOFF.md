# robotarm — handoff

Rewritten 2026-08-30, amended later the same day (see §9). Supersedes the
2026-08-26 version entirely. **The repo
is the state; this file is the index to it.** Read this top to bottom before
touching Fusion — sections 2 and 3 are the ones that will cost you a session
if you skip them.

---

## 1. What this is

A 6-DOF 3D-printed robot arm whose job is pruning house plants held in a
fixture on the bench. Fusion-360-only CAD pipeline, driven entirely through
the Autodesk Fusion MCP. **Every part is a Python script in
`models/robotarm/`.** There is no hand-modelling. The document is
disposable; the scripts are the design.

| joint | axis | servo | part that carries it |
|---|---|---|---|
| J1 | base yaw | SG90 | `turntable_stator` + `turntable_ring` + `shoulder_bracket` (rotor) |
| J2 | shoulder pitch | MG995 | `shoulder_bracket` fork, `shoulder_hub` drive, `wrist_hub` idler |
| J3 | elbow pitch | MG90S | `forearm` fork, **2:1 gear train, in progress** |
| J4 | wrist pitch | MG90S | `forearm` fork, `wrist_hub` ×2 |
| J5 | wrist roll | SG90 | `wrist_roll` + `wrist_rotator` |
| J6 | pruner | SG90 | `pruner_shell` ×2, `pruner_rack` ×2, `pruner_blade` ×2, `gripper_pinion`, `gripcut_finger` ×2 |

L1 = 125 mm, L2 = 45 mm. Inventory is used exactly: 1 × MG995, 2 × MG90S,
3 × SG90, no spare. **608ZZ is the only bearing Jonathan has** — three are
in the turntable, spare count UNKNOWN and worth asking about. The small
sizes in `lib/bearings.py` are datasheet nominals nothing has printed
against; do not design around them.

Printer: Bambu Lab X2D, bed 256 × 256 × 260. PETG, and printed mass is
solid volume × **1.27 g/cm³ × 0.65**, never Fusion's PET density.

**Measured duty, 2026-08-30, arm straight out with 25 g gripped:**

| joint | required | duty limit | at |
|---|---|---|---|
| J2 | 2.81 kg·cm | 4.70 | 60 % |
| J3 | 0.87 kg·cm | 1.00 | **87 %** |
| J4 | 0.36 kg·cm | 1.00 | 36 % |

The elbow is the bottleneck and has been since L2 went to 65. That is the
entire reason the J3 reduction exists.

---

## 2. LANDMINES — read before running anything

**THERE ARE THREE UNSAVED "Untitled" FUSION DOCUMENTS AND ONLY ONE IS
CURRENT.** They hold 40, 37 and 27 occurrences. The live one is the
**27-occurrence** document. Identify it by fingerprint, never by tab order
or occurrence count alone:

```python
# the working document is the one whose shoulder_hub is 1907.043 mm3.
# the stale two still hold the pre-fix 2182 mm3 hub.
for i in range(app.documents.count):
    doc = app.documents.item(i)
    des = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if des is None or des.rootComponent.occurrences.count == 0:
        continue
    for j in range(des.allComponents.count):
        c = des.allComponents.item(j)
        if (c.name == 'robotarm_shoulder_hub' and c.bRepBodies.count
                and abs(c.bRepBodies.item(0).volume * 1000 - 1907.043) < 1.0):
            target = doc
target.activate()
```

This already bit once: `_check_loads` ran against the 40-occurrence document
and overwrote `specs/robotarm/_mass_properties.json` with stale geometry.
**The cleanest fix is not to fight it — rebuild into a fresh document from
the scripts** (section 5). Then close the other three.

There are also **15 named STEP documents** open, saved in Fusion's Default
Project under "robotarm STEP editable". Those are DUMB SOLIDS Jonathan asked
for so he could direct-edit. They are not the source, they do not feed any
gate, and nothing you do to them reaches the scripts.

### Fusion API traps, all of them paid for

- **`val()` returns CENTIMETRES.** Angle parameters return RADIANS. Every
  print in this project multiplies by 10 for a reason.
- **A CUT without `inp.participantBodies` eats every other component in the
  document.** Always set it.
- **Rename first, then delete.** Deleting a component's last occurrence
  orphans it — it drops out of `allComponents` still holding its name, and
  the rebuild is handed `robotarm_x (1)`. Every later lookup misses. Rename
  the outgoing component to a stale prefix, THEN delete, THEN assert the new
  one actually got the name.
- **`SketchText` carries no profiles.** Call `.explode()` before extruding.
- **Features will not modify bodies created inside a `BaseFeature`.** Use
  `copyPasteBodies` for parametric copies.
- **3MF export walks GLOBAL visibility.** A hidden source occurrence exports
  as an empty ~1.7 KB file with NO error. Unhide everything in
  `root.allOccurrences` before any export.
- **`TemporaryBRepManager.booleanOperation` silently returns an empty body
  here.** It reports success and a zero volume, which reads as "no
  interference" and proves nothing. Use `body.pointContainment` instead, and
  **always include a positive control** that must register a hit. Two real
  bugs in this project hid behind a blind boolean.
- Calls die at ~60 s. For anything longer, redirect stdout to
  `.fusion_log.txt` with `buffering=1` via a `Tee` class, then poll from
  `device_bash` with a sleep loop.

### The Mac bridge

- `device_bash` runs in a Linux VM on Jonathan's machine; the repo is at
  `$HOME/mnt/cad-pipeline`. It HAS network and git.
- **It cannot unlink files on the mount.** So `git clone` into the repo
  fails (it needs to remove lock files) — clone to `$HOME` scratch and
  `cp -R` across. And before every commit:
  `mkdir -p _to_delete/git_locks && mv .git/*.lock _to_delete/git_locks/`
- Background jobs do not survive between calls. Each call is a fresh
  `bash -c`. Do long work in the foreground with a raised `timeout_ms`.
- Fusion MCP scripts run natively on the Mac, so their paths are
  `/Users/jonothanabraham/Documents/GitHub/cad-pipeline`, NOT the `mnt` path.

---

## 3. The ethic, which is not decoration

Honest engineering. Never invent a number silently. Everything is gated in
Fusion before it is believed. Grades are stated: **MEASURED / DERIVED /
ASSUMED / DATASHEET / MODEL**, and a downgrade is written into the file that
carries it.

**The project's recurring failure, in one line: _a datum in a shared library
which only one file reads is a decoration, not a contract._** It has been hit
on `shaft_from_end`, `lead_bundle_dia`, horn widths, gauge constants, the
lead datum, colour in seventeen files, and `sb_arm_l1`. When you add a shared
number, make more than one file read it and make the consumers assert
against it.

Two 2026-08-30 findings in the same family, both now gated:

- **`shoulder_hub` as first printed could not be installed at all.** The
  wr_ contract retains every hub with a Ø24 flange too big to pass its own
  Ø20.35 bore — but on the J2 drive side the MG995 pad is bolted over the
  counterbore, so the flange must also clear the pad's 20.4-wide case
  window, and tilting a Ø24 disc far enough costs 21.8 mm of a 12.2 mm gap.
  Fixed by deleting the flange; retention is the arm socket inboard and the
  servo case 0.5 mm outboard. `GATE hub_installs` in `_check_shoulder.py`
  now measures the bracket's clear radius along the axis. **Pose
  interference could never have caught this — every pose was fine, it was
  the journey that was blocked.**
- `_check_loads` counted the two-piece `pruner_shell` once. J3 was 88 %, not
  77 %.

---

## 4. Where it stands

### Built, gated, in the ledger — 18 parts

`specs/robotarm/_volumes.json` is the ledger. Gates last run all PASS:
`hub_installs`, `interference (J2) 0.000 across −25°…160°`, `clearances`,
`leads 6/6`, `loads duty`, `loads sections`, `j3_mesh`.

### Printed already

Everything below the wrist, plus the six-hub plate (marked 2H, 2, 3, 3, 4, 4).
**As of 2026-08-30 the printed `forearm` is scrap and the printed `upper_arm`
is one Ø3.4 hole short of usable** — see §6.5.
**The `shoulder_hub` on that plate is scrap** — it is the un-installable
flanged one. A corrected flangeless one is on the remaining plate.

### To print

`exports/robotarm/plates/plate_remaining_v7.3mf` — 12 pieces, 51 g, 24 % of
the bed, supports OFF, no brim: `pruner_shell` ×2, `pruner_blade` ×2,
`pruner_rack` ×2, `gripcut_finger` ×2, `wrist_roll`, `wrist_rotator`,
`gripper_pinion`, `shoulder_hub`. Orientations are baked in — if you
auto-arrange in the slicer, lock rotation or `gripcut_finger` and
`pruner_rack` will flip.

**The J3 gear parts are NOT on that plate.** They post-date it.

### The J3 reduction — built but not integrated

`lib/gears.py` holds `J3_PAIR` and the involute generator both gears trace.
Module 1.25, 18T/36T, 20°, face 8.0, centre distance 33.950, contact ratio
1.593, root stress 5.64 MPa of the 8.75 MPa cyclic allowable. 18T is the
undercut floor (2/sin²20 = 17.1) and it is asserted, not commented.
`GATE j3_mesh: PASS` — 0 of 420 flank points buried across a full tooth
pitch, with a control that buries 116 when deliberately mis-phased.
**This is now `models/robotarm/_check_elbow.py` and can be re-run.** It was
prose here and nothing else: the script that first produced it was never
committed, `lib/gears.py` had named a consumer that did not exist, and an
ungated number in this project is a decoration. `_check_elbow` also carries
`GATE j3_contract`, which reads each shared elbow number from the side that
did NOT define it — including `B608ZZ.inner_race_od` from both ends, since
the forearm shoulder must bear OUTSIDE the inner race and the axle collar
INSIDE it, and either one backwards locks the joint solid.

Three new parts build and gate: `j3_gear` (36T on the elbow axis),
`j3_pinion` (18T on the MG90S horn), `j3_axle` (idler side, runs in a
**608ZZ**; the Ø11 thrust collar exists because a hex face at 18.24 across
corners would bear on the OUTER race and lock the joint).

**What it costs:** J3 travel 180° → 90°. J3 duty 87 % → ~44 %, rated payload
25 g → roughly 60 g, both to be confirmed once the forearm moves and
`_check_loads` re-runs.

---

## 5. Rebuilding the arm from scratch

This is the reliable way out of the three-stale-documents mess.

1. In Fusion, **File → New Design**. Note its name.
2. Run `models/robotarm/_check_ledger.py` with `mod.BATCH = 0`, then 1, 2,
   3, 4 in sequence. Batch 0 opens the fresh document; the last batch prints
   the comparison table against `_volumes.json`. Eighteen parts will not fit
   in one 60 s call, which is why it batches. Running them out of order is
   caught, not guessed at.
3. Batches, in build order (order matters — a shared-parameter fault only
   shows downstream of the file that causes it):
   - 0 `gripper_pinion, pruner_blade, gripcut_finger, pruner_rack, pruner_shell`
   - 1 `wrist_hub, wrist_rotator, wrist_roll, forearm`
   - 2 `upper_arm, shoulder_hub, shoulder_bracket`
   - 3 `turntable_stator, turntable_ring, base_lid`
   - 4 `j3_pinion, j3_gear, j3_axle`
4. Then the joint gates: `_check_shoulder` (two passes — it builds on the
   first and measures with `REBUILD = False` on the second), `_check_wrist`,
   `_check_j1`, `_check_leads`, `_check_fit`, `_check_gripcut`,
   `_check_loads`, `_check_pruner`.
5. `_retheme.py` applies colour as a separate pass — colour is not geometry
   and lives in `lib/palette.py`, not in seventeen part files.

To run a part script from the MCP, exec it against the repo rather than
pasting it — the files import `lib.*`:

```python
ROOT = '/Users/jonothanabraham/Documents/GitHub/cad-pipeline'
if ROOT not in sys.path: sys.path.insert(0, ROOT)
for m in [k for k in list(sys.modules) if k == 'lib' or k.startswith('lib.')]:
    del sys.modules[m]                      # or you get a stale lib
src = open(ROOT + '/models/robotarm/<part>.py').read()
g = {'__name__': 'build'}
exec(compile(src, '<part>.py', 'exec'), g)
g['run'](_context)
```

---

## 6. Open, in the order things block each other
1. ~~DECIDE THE J3 DRIVE.~~ **DECIDED 2026-08-30: the offset spur pair.**
   Belt and coaxial planetary are both dropped. See §9 for what that
   decision actually costs, which is not what §7 priced it at.
2. ~~`forearm.py` rework~~ **DONE 2026-08-30, on option 1.** Servo lobe at
   y −11.05 on a 9.60 mm standoff; gear (r 24.15) and pinion (r 12.90)
   clearance both CUT out of that block rather than drawn around it; 608ZZ
   pocket Ø21.98 × 7.0 from the plate inner face with a 0.50 shoulder bored
   Ø13.0; J3 drive-side flange counterbore deleted (`j3_gear` has no flange,
   and leaving it would cut the journal's bearing length from 7.5 to 5.0
   against a hub built for the full plate). forearm 15887.767 → 18322.471 mm³,
   −X extent 25.40 → 35.00. **`GATE j3_mesh` and `GATE j3_contract` both
   PASS**, 8 contract terms checked and 0 absent.

   Two probed ceilings MOVED and both are recorded in the file:
   `fa_lobe_radius_j3` is a new LOCAL 4.5 (J4 keeps sty_radius 6.0 — 6.0
   fails ASM_INCONS_FACE on the J3 lobe, 5.5 and 5.0 fail ASM_BL_CAP_COMPLEX),
   and `fa_facet` drops 1.50 → **1.00**, because the standoff now blends into
   the −X plate face and 1.50 and 1.25 both fail ASM_INCONS_FACE there.
3. ~~`upper_arm.py` needs one Ø3.4 hole~~ **DONE 2026-08-30.** The bore runs
   the full width on the J3 axis, through the cable duct; upper_arm 45299.852
   → 45207.244 mm³. Swept with `pointContainment`, 0 of 96 stations blocked,
   against a control 6 mm off-axis that finds solid at 69 of 96. The M3 is
   now one datum across three files — `lib/design_rules.py FASTENER_MM`, read
   by `j3_gear` (clearance), `upper_arm` (clearance, and it asserts j3_gear
   agrees) and `j3_axle` (pilot). **`ja_tap_d` was 2.5 while its own comment
   cited design_rules, which says 2.6**; it reads the table now. **Buy M3 × 40** —
   33.7 mm from the head underside to the tap, printed by the build.
4. ~~Re-run `_check_loads`~~ **DONE 2026-08-30 — and the load model did not
   know the reduction existed.** `lib/arm_loads.py`, `lib/arm_budget.py` and
   `_check_loads.py` contained no mention of the ratio: the gear train was
   built, gated and installed, and this model would have gone on reporting
   the elbow at 87 % while the hardware sat at half that. §3's failure for
   the fourth time. `lib/arm_loads.py` now imports `J3_PAIR` and carries a
   `REDUCTION` table; six new tests in `tests/test_arm_loads.py` hold it.

   | joint | required | duty at the joint | of duty | drive |
   |---|---|---|---|---|
   | J2 | 2.84 kg·cm | 4.70 | 60 % | direct |
   | J3 | 0.89 kg·cm | **1.80** | **49 %** | 2:1 × 90 % eff, 90° travel |
   | J4 | 0.36 kg·cm | 1.00 | 36 % | direct |

   **J3 87 % → 49 %**, margin 2.03. `GATE loads duty` and `GATE loads
   sections` both PASS, and `GATE ledger` passes on all 18 parts at 0.000
   delta in a fresh document.

   **Rated payload 103 g at the jaws, not the ~60 g estimated — and J2 binds
   it now, not J3.** Per joint: J2 103 g, J3 106 g, J4 119 g. `_check_loads`
   computes and prints this; it used to be a number in `_assembly.md` that
   nothing derived. **The elbow is no longer the bottleneck; the shoulder
   is.** `PAYLOAD_G` is still 25 — raising it is a decision, not a
   consequence, and the figure is static with no slew, stop or impact.

   The one weak number: `MESH_EFFICIENCY = 0.90` is ASSUMED for a printed
   PETG spur pair running dry, not measured. It is deliberately pessimistic.
5. **Re-export the plates — and TWO ALREADY-PRINTED PARTS ARE NOW STALE.**
   This is the only open item left, and it needs a decision first:

   - **`forearm` 15887.767 → 18322.471 mm³.** It is 9.60 mm wider on −X and
     carries the whole gear train. The printed one is scrap; there is no
     modifying it. **Reprint.**
   - **`upper_arm` 45299.852 → 45207.244 mm³** — the difference is the one
     Ø3.4 elbow bolt bore. Either reprint ~42 g of PETG, or drill the
     printed one: it is on the J3 axis through the cable duct, and the two
     Ø16 hex sockets at either end are a usable guide for getting it
     concentric. Drilling is the cheap answer if the sockets guide it
     honestly; that is a bench judgement, not a CAD one.

   Then the new plate is `plate_remaining_v7`'s 12 pieces **plus** `j3_gear`,
   `j3_pinion`, `j3_axle`, `forearm`, and `upper_arm` if it is not drilled.
   The full-build plates in `exports/robotarm/plates/plate_[12]_v6.3mf` also
   came from a document where `shoulder_bracket` still had the old arm
   length — geometry is identical and the ledger passes, but they are worth
   regenerating rather than trusted.

~~Also standing: how many spare 608ZZ does Jonathan actually have?~~
**ANSWERED 2026-08-30: three or more spare**, beyond the three in the
turntable. The geared elbow needs one. No longer a constraint.

---

## 7. What the reference arms say — and it is not what we built

`reference/` (gitignored, 380 MB, see `reference/INDEX.md`) holds complete
file sets for three published arms, downloaded 2026-08-30:

- `reference/thor/` — AngelLM's Thor. 6-DOF printed serial arm, printed
  gears + GT2 belts, 49 STEP + 49 STL. CC-BY-SA 4.0.
- `reference/so-arm101/` — TheRobotStudio SO-ARM100/101, closest to our
  scale, STEP + STL + BOM + print settings + URDF. Apache 2.0.
- `reference/ar4/` — Annin AR4 MK3: full manual, STL pack, Teensy firmware,
  HMI source, standard and modified DH parameter sheets.

**The finding that should inform decision 1:** Thor gears J1, J2 and J4 but
drives its ELBOW with a belt and a sprung tensioner (`Art3Pulley`,
`Art3TensionerBody`, `Art3TensionerPulley`). AR4 uses belts on four of its
six axes. Two independent projects reached for a belt exactly where we put
a printed spur pair — because a belt takes up its own backlash and tolerates
centre-distance error, and a printed spur pair does neither. Our 33.95 mm
centre distance has to come off the printer right or the mesh is tight or
sloppy, and there is no adjustment in it.

Nothing in `reference/` is a drop-in model for this arm. Every complete open
arm either stays direct-drive on hobby servos or steps up to steppers once it
wants joint reductions. A PWM-hobby-servo 6-DOF serial arm WITH external
per-joint reduction has no published equivalent. Lift pieces, not designs.

---

## 8. Older context still worth knowing

- **Any z in the turret you remember from before 2026-08-26 is 1.1 mm low.**
  `tt_axle_z` moved 12.0 → 13.1 and `tt_race_z` 23.00 → 24.10 when the J1
  roller fault was fixed.
- **The output shaft is not in the middle of the case.** `turntable_stator`
  centred the SG90's *case* on J1, putting the *shaft* 5.2 mm off axis — the
  horn would have driven the rotor as a 5.2 mm crank. See `_assembly.md`.
- **The lead keyway was on the wrong wall in five parts.** The bundle leaves
  the SHORT END FACE, centred across the width. `lib/servo.py` now names the
  face in its first sentence and asserts `lead_x == -shaft_from_end`.
- **The J2 preview bearings were 90° out** — tangential axles instead of
  radial. `_preview_arm.py` now asserts the face normal.
- `base_lid` is ours; the printed legacy platter has no central opening at
  all, measured not assumed.

---

## 9. Amendment, 2026-08-30 — what the spur pair actually costs

The decision in §6.1 was taken on a number this file got wrong, and the
correction is large enough to be worth its own section.

### The standoff was never free to choose

§7 priced the offset spur pair at "~7 mm of forearm width". It is not a
parameter. Three facts solve for it:

- a servo's horn seat is a fixed height above the tab plane its mount clamps
  (MG90S: `tab_below_top + tab_thk + boss_h` = 11.5 mm),
- the pinion's tooth band must coincide with the gear's,
- the gear's band is fixed by the fork plate it journals in (−20.30 … −28.30).

Solved, the tab plane lands at **−39.80** against −25.40 today: **14.40 mm**
of extra forearm width on the −X side only, not 7. It costs no elbow torque —
the growth is along the joint axis — but the arm becomes asymmetric and the
servo case hangs out to −58.30.

**Cut to 9.60 mm** by boring `j3_pinion` straight through at the hub press
diameter instead of blind-pocketing it, so the servo's own Ø6 output boss
passes freely up the bore and the seat face drops from 11.5 to 6.70. The
press is unchanged — the 6.8 hub still presses over its full 3.0, now at
4.80…7.80 along the bore — and the part got lighter, 2654 → 2257 mm³.

Thickening the pinion to swallow the boss in a *blind* pocket was priced
first and does **not** work: the swallowed depth comes out of the pinion's
own thickness, the pinion is bounded inboard by the fork plate, and it
finishes 2.70 mm inside it needing a Ø25.4 relief that breaks into the J4
flange counterbore.

`lib/gears.py J3_MOUNT` now solves all of this from `lib/servo.py` and
`J3_PAIR`, and asserts each failure mode rather than describing it. Six
typed-in horn numbers used to live in `j3_pinion.py`, whose real consumer
was always `forearm.py` — §3's recurring failure with the serial numbers
filed off.

### THE OPEN QUESTION: the standoff cannot be a solid block

Relocating the J3 lobe to the pinion axis puts it at y −11.05, spanning
y −22.90 … 11.60, z ±8.80. Two clearance cylinders then live inside the
9.60 mm standoff band:

| about | radius | why |
|---|---|---|
| the ELBOW (y −45) | 24.15 | the 36T gear turns here |
| the PINION (y −11.05) | 12.90 | the 18T pinion turns here — **inside the lobe's own footprint** |

The pinion circle is r 12.90 and the lobe is only 8.80 tall, so **it cuts the
standoff clean through, top to bottom.** Inside the lobe height the only
material still joining the lobe back to the fork plate is a web at the WRIST
end, y −1.62 … 11.60 — 9.75 mm wide on the centreline, 13.22 mm at the
lobe's top and bottom edges. The elbow-side remainder is inside the gear
circle and is cut away too.

**So the J3 servo hangs off the J4 end of the forearm**, carrying its own
2.0 kg·cm stall reaction across a 9.60 mm standoff on a ~10 mm web. That is
a real change to the part's load path — but see the pricing below: the web
is stiff enough by a wide margin, and this reads worse than it is.

Going over the top of the pinion does not obviously rescue it: the pinion
circle only clears at |z| ≥ 12.90, `fa_waist_z` is 12.0, and the silhouette
at that station reaches roughly 12.9 — there is no room for a strap without
growing the link's outline.

### Priced 2026-08-30: option 1 is fine, and "cantilever" overstated it

The web is not a thin unsupported finger. The pinion circle never reaches
y ≥ 1.85 **at any z**, so the web is full height there, and the J4 boss
(r 13.78 about y 0) backs the whole span. It is a short stubby prism —
b 9.75 (Y) × h 17.60 (Z) × L 9.60 (X) — loaded in TORSION about its own long
axis, which is the stiffest way a block that shape can be loaded.

At the MG90S's **stall** 2.0 kg·cm, not its duty limit:

| | value | against | margin |
|---|---|---|---|
| peak shear | 0.281 MPa | ~20 MPa PETG interlayer | **71×** |
| twist | 0.0164° | — | — |
| lost motion at the pinion pitch radius | 0.0032 mm | 0.20 mm designed backlash | **1.6 %** |

Interlayer is the right allowable to check: the forearm builds along +X, so
the layers lie normal to X and this loading is across them — the weak
direction. β/α are the handbook rectangular-torsion coefficients for
h/b = 1.5 used at h/b = 1.81, which understates J and α and so **overstates**
both the twist and the stress.

FIRST-ORDER, NOT A GATE. E 1700 MPa and ~20 MPa interlayer are book values
for PETG, not measured on this printer, and the web is idealised as one
prism when the real one tapers into the lobe. But it is not close: the
decision does not turn on a factor of two, or of ten.

**Recommendation: take option 1.** Options 2 and 3 buy stiffness that is
already 60× more than the joint can use, and both cost real geometry.

**TAKEN 2026-08-30 and built — see §6.2.** Both elbow gates pass.

Three ways out:

1. **Accept the web as it falls** and add a gate that measures it — priced
   above, and it passes with room to spare. Nothing else changes. The word
   "cantilever" below was mine and it was alarmist; the physics does not
   support it.
2. **Grow the silhouette at the J3 station** so a strap passes over and
   under the pinion, making the standoff a closed yoke instead of a
   cantilever. Costs mass on the forearm, which §4's `fa_l2` comment calls
   the single highest-leverage number in the arm.
3. **Put the centre distance in Z rather than Y** — servo directly above or
   below the elbow instead of along the link. The gravity moment about J3
   goes to roughly zero with the arm horizontal, better than the +45 g·cm
   the Y placement costs. But the standoff then has to reach the lobe around
   the OUTSIDE of the r 24.15 gear circle and the fork plate only reaches
   r 13.775 at that station. Not obviously buildable; not yet drawn.

Pick one before touching `forearm.py`. Everything else in §6 is unblocked.
