# robotarm — handoff

Rewritten 2026-08-30. Supersedes the 2026-08-26 version entirely. **The repo
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
pitch, with a control that buries 102 when deliberately mis-phased.

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

1. **DECIDE THE J3 DRIVE.** Nothing else in the elbow can proceed. Three
   live options:
   - **Offset spur pair as built.** 2:1, 90° of travel, done and gated.
     Costs: the servo moves 33.95 mm off the elbow to y −11.05, ~7 mm of
     forearm width, a new r 23.75 clearance cylinder about J3, and +45 g·cm
     on J3 from the servo mass moving outboard.
   - **Coaxial planetary at ~3.6:1.** Servo stays on the elbow axis, so the
     entire forearm rework disappears. Costs 51° of travel and 8 printed
     parts on plain pins. A true 2:1 needs the STAR form (fixed carrier,
     ring output) at sun 34T / planet 17T / ring 68T, ring OD ~75 — a
     normal ring-fixed planetary CANNOT do 2:1 at all, since the ratio is
     `1 + Zr/Zs` and that is strictly greater than 2.
   - **Belt.** See section 7 — this is what both reference arms actually
     did, and it is the option with the least evidence against it.
2. **`forearm.py` rework**, whichever drive wins. Servo lobe relocation,
   the r 23.75 gear clearance cylinder, and the 608ZZ pocket (Ø22 × 7.0
   from the plate's inner face, 0.5 shoulder outboard with a Ø13 bore) in
   place of the flange counterbore.
3. **`upper_arm.py` needs one Ø3.4 hole** on the elbow axis, through the
   cable duct, for the M3 that clamps `j3_gear` + upper arm + `j3_axle`
   into one rotating group. The gear cannot be flange-trapped — both its
   stops are inboard.
4. **Re-run `_check_loads`** and confirm the 87 % → ~44 % and the payload.
5. **Re-export the plates.** The J3 parts are on none of them, and the
   full-build plates in `exports/robotarm/plates/plate_[12]_v6.3mf` came
   from a document where `shoulder_bracket` still had the old arm length —
   geometry is identical and the ledger passes, but they are worth
   regenerating rather than trusted.

Also standing: **how many spare 608ZZ does Jonathan actually have?** The
geared elbow needs one beyond the three in the turntable.

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
