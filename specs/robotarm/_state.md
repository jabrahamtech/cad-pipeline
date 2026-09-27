# robotarm — state

Written so the project survives losing whoever is holding it in their head.
If you are picking this up cold, read this then `_assembly.md`, `_style.md`,
`pruner.md`, and `fusion/PLAYBOOK.md` in that order.

## What this is

A 3D-printed 6-DOF desktop arm that **prunes house plants**. It was a gripper
arm until the effector was changed to a bypass shear; the gripper still
builds and is kept as a swappable head on the same 4 × M3 pattern.

Inventory: **2 × MG995 (one 360° continuous, J1)**, SG90s for J3–J6, plus 608ZZ bearings. (Was 1 × MG995, 2 × MG90S, 3 × SG90 — see `_sg90_migration.md` and `base_platter.md`.)
That one-big-five-small split is the binding constraint on the whole design
and the reason no donor arm fits (see "Donor arms" below).

## 2026-09-27 — J1 → MG995 360°, new base

Read `specs/robotarm/base_platter.md` first. J1 drive contract moved to `lib/j1_drive.py` (was typed into three scripts). New parts: `base_platter`, rewritten `base_lid`. Changed: `turntable_stator` (rollers rotated, 4-screw MG995 pad, loom window az 210, hall post), `j1_hub` (7.90 tall, MG995 spline), `shoulder_bracket` (centre bore Ø5.4 → Ø6.4 only — drill a printed one). Gate: `_check_base.py` PASS with positive control. The J1 section below describes the SG90 era.

## Joints

| # | joint | servo | member shape |
|---|---|---|---|
| J1 | base yaw | **MG995 360° (continuous)** since 2026-09-27 | turntable on 3 × 608ZZ on the NEW `base_platter` — rollers at az 30/150/270, hall home sensor at az 330. Contract: `lib/j1_drive.py`. Spec: `base_platter.md` |
| J2 | shoulder pitch | MG995 | bracket FORKS, upper arm is a BLOCK — built |
| J3 | elbow pitch | MG90S | forearm FORKS, upper arm is a BLOCK — built |
| J4 | wrist pitch | MG90S | forearm FORKS, roll housing is a BLOCK — built |
| J5 | wrist roll | SG90 | inline rotator — built |
| J6 | pruner | SG90 | rack and pinion — built |

**Forks and blocks alternate.** A fork carries two `wrist_hub` journals; a
block takes a hex socket in each end face. This is not stylistic: the forearm
CANNOT be straddled at one end and fork at the other (the two clearance zones
do not touch — see `forearm.py`). Everything else followed from that.

## The joint contract (`wr_*`), identical in every file that uses it

| | | |
|---|---|---|
| `wr_pivot_af` | 16.0 | hex across flats |
| `wr_straddle` | 24.0 | width a fork straddles |
| `wr_sweep_r` | 25.4 | roll housing sweep about J4 |
| `wr_hub_d` | 20.0 | journal collar — **must exceed the hex across CORNERS, 18.24** |
| `wr_journal` | 5.0 | collar length |
| `wr_flange_d` / `_t` | 24.0 / 2.0 | retaining flange |
| `wr_reach` | 3.8 | hex length = gap 0.4 + socket 3.4 |

## The turntable contract (`tt_*`) — full block in `turntable_stator.py`

Each file defines only the members it consumes; every member is defined
*identically* wherever it appears. Frame: origin on the J1 yaw axis at the
**printed platter's rim top** (its own z 42.00 — see `base_platter_measured.md`).

| | | |
|---|---|---|
| `tt_post_r` | 45.0 | **MEASURED.** 3 × M3 inserts, az 120/180/240. The only fixing the platter offers |
| `tt_roller_r` / `_od` / `_w` | 27.0 / 22.0 / 7.0 | 3 × 608ZZ, axles RADIAL and horizontal |
| `tt_axle_z` | 12.0 | bearing bottom clears the lid by 1.0 |
| `tt_race_z` | 23.0 | **derived** = axle_z + od/2. Never type it |
| `tt_disc_d` / `_t` | 76.0 / 5.0 | the rotor rim the ring hooks over |
| `tt_boss_d` / `_h` | 68.0 / 4.4 | **the journal** — turns in the ring's bore, locates the arm radially. `boss_h` = ring_lift + ring_t so the ring finishes flush |
| `tt_ring_t` / `_or` / `_lift` | 4.0 / 50.0 / 0.40 | the retainer |
| `tt_horn_*` / `screw_bore` | 32.0 / 2.0 / 1.8 / 6.0 | SG90 cross pocket in the rotor underside |

**The rotor is `shoulder_bracket`'s underside.** There is no separate disc part.

## Parts

Built and gated — `models/robotarm/`:

| part | printed g | notes |
|---|---|---|
| `gripper_pinion` | 1.0 | m1.5, 12T — reused UNCHANGED by the pruner |
| `pruner_blade` ×2 | 3.2 | one design, second turned over |
| `pruner_rack` ×2 | 6.6 | rack + forward drive pin |
| `pruner_shell` ×2 | 25.8 | clamshell + cheeks carrying the blade pivot |
| `wrist_hub` ×6 | ~7.8 | one design, six copies, two joints |
| `wrist_roll` | 12.2 | J5 housing, keel silhouette |
| `wrist_rotator` | 5.3 | J5 disc |
| `forearm` | 20.6 | L2 = 65, forks both ends, box beam |
| `upper_arm` | 26.7 | L1 = 85, block both ends, duct-hollowed |
| `shoulder_hub` | ~1.8 | `wrist_hub` with a three-step MG995 horn relief |
| `shoulder_bracket` | ~52.9 | J2 fork + MG995 mount + **J1 rotor disc**, NOT lightened |
| `turntable_stator` | ~34.7 | J1 fixed half — SG90, 3 roller cheeks, 3 posts |
| `turntable_ring` | ~15.2 | retainer + the Ø68 radial journal |
| `servo_adapter` | ~2.5 | small servo into a big servo's mount |
| gripper (3 parts) | 31.7 | superseded head, still builds |

Not built: `forearm_cover`. No J1 gate yet. **`base_platter` and `base_lid` are PRINTED and kept** — see `base_platter_measured.md`.

## Gates

- `_check_fit.py` — gripper, PASS
- `_check_wrist.py` — J4/J5 sweep, PASS
- `_check_shoulder.py` — J2 sweep −40°..+160°, PASS (interference 0.000, gap 0.400 held). **Run twice**: `REBUILD=True` then `False`.
- `_check_ledger.py` — **the whole-project gate. PASS, 13 parts, 0.000 drift.** Rebuilds everything into ONE FRESH document and compares volumes at the END against `specs/robotarm/_volumes.json`. **Run three times**: `BATCH = 0, 1, 2`. It is the only check that can see one file reaching into another; the other three each rebuild only what they need and are blind to the rest.
- `_check_pruner.py` — the head. **Run twice**: `REBUILD=True` then `False`; four parts plus interference exceeds the 60 s MCP limit in one call.
- `tests/test_pruner_linkage.py` — 16 tests, all passing, plain Python

## Load budget — the one number that governs everything

**The elbow MG90S at 1.00 kg·cm duty is the binding constraint.** Measured,
not estimated: 0.874 kg·cm, **87 %**. Empty it is 55 %. The head is 38 % of
the moment on its own. Every gram at the head costs 1.12 % of elbow duty.

The shoulder MG995 has 5.0 kg·cm and is nowhere near its limit — which is
why L1 (85) is longer than L2 (65).

## Traps that have already cost time

Full detail in `fusion/PLAYBOOK.md`. The expensive ones:

1. `val()` returns **centimetres**; `createByString` reads a bare number as **millimetres**. Ten-times-too-small geometry, no error.
2. Fusion keeps **one Python session** — `lib` goes stale in `sys.modules` unless purged.
3. Angle parameters come back in **radians**, not degrees.
4. A CUT with no `participantBodies` eats **every other component**.
5. Rename a component **before** deleting its last occurrence or the name is never released.
6. Volumes that touch exactly are non-manifold; overlap by a wall.
7. **Redefining a SHARED parameter reshapes every part already built.** A fillet stores a live *reference* to `sty_radius`, not its value. `turntable_clip.py` set it to 3.0 because 3.0 suits a small part, and silently re-cut pruner_shell (+1352 mm³), the forearm (+209) and the shoulder bracket (+220) — no error, every body still `isValid True`, every part still printing its own correct volume because each prints *before* the next script moves the parameter. Note the direction: volumes went **UP**, which reads like a missing cut and sends you hunting in the wrong file. A file may define a shared param only with the value everyone else gives it; if this part needs a different number, it is not that parameter — give it a local one.

## J2, settled

- **The servo runs DOWN.** Pointing it up leaves the outer tab 33.9 mm above the pitch axis — a free-standing ear needing support and cantilevering 55 g. Down lands that tab inside the base plate, so the pad is one unbroken web from boss to base.
- **`sb_lobe_t` = `tab_below_top + tab_thk` = 10.0 is not a chosen number.** It is tab-underside to case top. The tabs bear on the pad's OUTER face, screws go inboard from there, and the case top then lands flush on `sb_plate_out`. Model it the other way round and the servo appears buried in the arm.
- **Nothing in `shoulder_bracket` is lightened, on purpose.** It sits BELOW J2, so its mass loads no pitch joint — only J1, whose axis is vertical. What it does carry is the whole arm's bending moment through two 7.5 mm plates.
- **`shoulder_hub`'s relief is a three-step pocket.** 16.4 mouth × 2.5 (swallows the Ø13 output boss AND passes the trimmed horn arms), cross slot 2.5→5.1 at r 8.0, then a 12.15 press bore to 7.6. Sized on the boss alone the mouth would be 13.4 and the servo could never be fitted. Binding wall 1.80 mm.
- **The horn goes in BLADE TOWARD THE SERVO.** Flipped, its blade sits 5 mm deeper — inside the hex — and the arm tips break out through the flats.
- **J2 down-pitch is limited to −45.5° by the arm reaching this bracket's own base plate.** Scanned in `shoulder_bracket.py`, declared as −40 with margin. Every mm of `sb_base_y` and every mm off `sb_stand_h` costs travel here.

## J1, settled — REDESIGNED around the printed platter

Jonathan has printed the legacy base. Its **platter is kept** (the control
unit: electronics bay, ESP32, breadboard, switch, DC jack, yaw servo column).
Its **turret is not** — `turret_cap` and `turntable_clip` are in
`legacy/models/robotarm/superseded/`.

- **The platter's own spec is wrong about its rim height** (says 30, the STEP says 42.00). `specs/robotarm/base_platter_measured.md` is the file to trust.
- **The whole interface is three M3 on a Ø90 circle** at az 120/180/240. Everything above is ours.
- **Three screws hold the turret.** One M3 (~40 long) per post runs ring → post → platter insert. The legacy needed eleven fasteners and four printed parts for the same three jobs.
- **Three constraints, three features**: weight down on 3 × 608ZZ radial rollers; radial location by the rotor's Ø68 boss turning in the ring's bore; uplift by the ring hooking over the Ø76 rim. The legacy had no radial location at all.
- **Nothing caps rotation** — J1 gets the servo's full 180°.
- **The axles are RADIAL.** The rotor moves tangentially over each roller, so a tangential axle scrubs instead of rolling and wears a flat on the outer race. Looks equally plausible either way; only one is right.
- **The race collar (0.5 mm) is what makes it roll.** Without it the outer race touches the cheek and the roller rubs.
- **J1 is an SG90** — both MG90S are spoken for at J3/J4. `lib/servo.py` puts SG90 `case_w` at 12.6 against a 12.45 printed column: **0.15 mm interference, measure before assuming.**
- **J2's down-pitch fell from 45.5° to 27.0°.** The old base was a 40 mm rectangular plate; the turntable is a Ø100 ring, and a circle has no azimuth that buys travel. That is the price of the printed base.

## BOM — what has to be bought or found before the arm prints

- **3 × M3 penny washer Ø9** — ONLY if the printed `roller_cap` fails. A standard M3 washer is Ø7 and the 608 bore is Ø8; it falls through.
- **3 × M3 × 40 socket head** — one per turret post, running ring → post → platter insert. Longer than a typical assortment holds.
- **3 × M3 × 12** — the roller axle screws.
- **M3 heat-set inserts** — only if any tier-2/3 fix is taken up. The platter already has its own.
- 3 × 608ZZ (have 6), 1 × MG995, 2 × MG90S, 3 × SG90 (all in hand).

## Open risks

- **10 N/mm of stem is a rule of thumb.** The pruner's whole capability claim rests on it. One stem, one scissor edge, one kitchen scale settles it. Nothing else is this cheap to de-risk.
- Servo dimensions are DATASHEET, not measured. The two MG995 vendor drawings **disagreed** — hence slots, not holes. **The MG995 in hand has still not been measured, and J2 is now cut from those numbers.** The horn hub (12.0), output boss (13.0) and tab pitch (47.8) are the three that would each force a rebuild.
- **THE GAUGE EXISTS AND IS THE NEXT THING TO PRINT.** `models/robotarm/_gauge_fits.py` -> `exports/robotarm/gauge_fits_v1.3mf`. Procedure in `specs/robotarm/_gauge_sheet.md`, reduction in `lib/gauge_reduce.py`. Until it is printed and measured, every fit in this project is a handbook number and the 22 mm tip-error budget is theoretical.
- **J1 has no gate yet.** The cap, the clip and the 608 have never been assembled in Fusion, so nothing has checked that the roller crown actually meets the track or that a lug clears the lip through 154°.
- The head has had a style pass; the links have not been checked against each other for family resemblance.

## Donor arms — settled, do not redo

PAROL6 was downloaded and measured (`~/Downloads/PAROL6_unpacked/`). It is a
**stepper** machine: 6 × NEMA17, 20:1 and 10:1 planetaries, HTD3 belts, some
joints geared 60:1. **181 g of plastic hangs past its elbow** — 1.6 kg·cm on
a joint where an MG90S holds 1.0.

Scaling does not rescue it. Torque goes as k⁴ so the plastic scales away
nicely (~0.88 fits an MG90S), but bearings, belts and screws do not scale —
at 0.88 the HR32906J wants a 26.4 mm bore and HTD3 wants a 2.64 mm pitch.
Neither exists. And a 180° servo through a 60:1 reduction gives **three
degrees** of joint travel.

What PAROL6 IS good for: its **covers**. They carry no load and touch no
bought part, so scaling them is legitimate. That is the honest route to the
reference photo's look.
