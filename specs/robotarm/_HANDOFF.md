# robotarm — handoff

Written 2026-08-26 at the end of a long session. Everything a fresh
conversation needs in order to carry on. The repo is the state; this file is
the index to it.

## Where the project actually is

`GATE ledger : PASS` — 14 parts, 0.000 drift, `specs/robotarm/_volumes.json`.
`GATE interference (J2)` : PASS, 0.000 across −25°…+160°.

Run order for the whole-project gate: `models/robotarm/_check_ledger.py`
with `mod.BATCH = 0,1,2,3` in sequence. Batch 3 prints the table.

## READ THIS BEFORE TRUSTING ANY PRE-2026-08-26 Z NUMBER

`tt_axle_z` moved 12.0 → 13.1 and `tt_race_z` 23.00 → **24.10** when the J1
roller fault was fixed. Every z in the turret above the base plate rose 1.1 mm
with it. The gauge plate is unaffected — it tests bores, hexes and seats, none
of which reference the turret datum — but any z you remember from an earlier
session is 1.1 mm low.

## THE IMMEDIATE THING: the gauge print

`exports/robotarm/gauge_slim_v2.3mf` — 4 pieces, 171 × 150 mm, 77,281 mm³,
~2 h. Procedure: `specs/robotarm/_gauge_sheet.md`. Reduce with
`lib/gauge_reduce.py` (paste readings into `MEASURED`, run it).

**Nothing changed on 2026-08-26 invalidates this plate.** The day's work
moved `fa_elbow_clear`, `ua_drum_r`, both `waist_z`, added facets, cable
windows and `ts_shaft_off`. The gauge tests hex 15.80/16.00, journal 20.35,
608 pocket 22.05, MG995 horn 12.15, SG90 horn 7.15, slide 10.25, stub 7.90,
insert 4.00 and seats 10/11/12 — none of them touched. Print and measure.

Section 1 of `gauge_reduce` now checks the readings against a published
prior (`knowledge/materials.md`) BEFORE deriving anything, and names the
likely misconfiguration if they fall outside it. Read that before section 2.

## What was decided on 2026-08-26

- **L1 85→65, L2 65→45**, drums r11→r13, both links to a 24 mm section, to
  match the reference arm's proportions. J3 duty **80 % → 61 %**.
- Every printed mass in the project was **12 % high** — Fusion's PET density
  1.541 against PETG filament's 1.27, and 0.60 infill against a measured
  0.65. `lib/arm_budget.py` is the authority now and validates against the
  old figure to 0.5 g·cm.
- **Grip-and-cut head chosen** over the plain pruner. Mechanism solved in
  `lib/gripcut_finger.py`, written up in `specs/robotarm/gripcut.md`.
  Costs 1.0 g. **NOT MODELLED YET.**
- `base_lid` is now ours. The printed one has no central opening at all —
  measured, not assumed — so the SG90 could never have reached the platter.
- **`turntable_stator`'s yaw servo was 5.2 mm off the J1 axis.** See
  `_assembly.md`, "THE OUTPUT SHAFT IS NOT IN THE MIDDLE OF THE CASE".

## Open, roughly in order of what blocks what

1. **Print and reduce the gauge.** Everything tolerance-related waits on it.
2. **Model the grip-and-cut fingers.** Spec is written and solved; the CAD
   is not started. Two flexure leaves on the existing `pruner_blade`
   carriers, lead 2.0, t 1.2, L 29.1 folded.
3. **`forearm_cover` and `upper_arm_cover` do not exist.** Both links are
   box beams with an open cable duct and nothing closes them. They were
   always in `_assembly.md`'s part table and were never built.
4. ~~There is no J1 gate.~~ **DONE 2026-08-26 — and it FAILS.**
   `models/robotarm/_check_j1.py` sweeps −90°…+90° in 15° steps. Four faults,
   all of them in the FIXED half and all yaw-independent, which is why
   turning the model never showed them: **the three 608ZZ foul the stator's
   own 4 mm base plate by 218 mm³ each and cannot be fitted**; the az-90
   roller also fouls the servo pad; `base_lid`'s opening is centred while the
   servo well is offset +5.20; and `tt_boss_h` is declared 4.0 in two files
   and 4.4 in a third. Full write-up and the four options for the roller in
   `_assembly.md`, "J1 HAS A GATE NOW, AND IT FAILS".

   **ALL FOUR FIXED the same day**, 857.01 → 0.000 mm³, both gate lines PASS.
   `tt_axle_z` 12.0 → 13.1 with a MIN_WALL relief under each roller, the servo
   pad shortened to 16.4 and its end rounded, `bl_open_y` 31.0 at +2.00, and
   `tt_boss_h` 4.4 everywhere. `tt_race_z` 23.00 → 24.10 — **the turret is
   1.1 mm taller than anything printed before today.** Write-up in
   `_assembly.md`, "J1 GATE: FIXED, AND NOW BLOCKED ON ONE CALIPER READING".

   **The one thing left is a caliper reading**: the SG90 horn's hub diameter,
   modelled at Ø6.30 against `tt_screw_bore` Ø6.00. The gate reports BLOCKED
   rather than PASS until that is measured. Five minutes with a servo in hand.
5. **`_check_loads.py` still does not exist.** `_assembly.md` has promised it
   since it was written. `lib/arm_budget.py` is a parametric stand-in whose
   link masses are now measured but whose cluster offsets are assumed rigid.

## Unverified numbers that could still bite

- **The ring's 0.40 mm daylight over the rotor rim.** Two printed Z surfaces
  at ±0.25 each (`DIM_TOL_Z`). Stack them wrong and the ring clamps the rotor
  and J1 will not turn. Most likely single failure in the base. Mitigation is
  sanding or shimming at the three posts.
- **The platter's servo column, 12.45 × 23.05, is UNVERIFIED** and an SG90 is
  12.60 wide — 0.15 of interference. `base_platter_measured.md` says measure
  it. Still not measured. **Caliper this before printing the turntable.**
- **The SG90 horn's hub diameter is not in the project at all.** `_check_j1`
  models it at Ø6.30 as the only invented number in that file, and it is what
  decides whether the hub clears `tt_screw_bore` Ø6.00. Caliper it off a
  servo in hand; until then that gate's `horn ^ rotor` line proves nothing.
- **MG995 dimensions are DATASHEET**, never measured, and two vendor drawings
  disagree.
- **The ~50 N stem cutting force is unvalidated.** Kitchen scissors on a
  kitchen scale would settle it in five minutes.
- **`gripcut_finger`'s 1.0 % strain limit is HANDBOOK** and wants a flexure
  coupon on the next gauge plate. So is µ = 0.4 for PETG on a green stem.

## Traps this project has actually fallen into

`fusion/PLAYBOOK.md` is the running list. The two that keep recurring:

- **Units in assertions — five times.** `val()` returns CENTIMETRES.
  Convert once into `_mm` names; never compare a `val()` to a bare literal.
  The fifth one threw no error at all: a CUT built at the wrong scale removed
  nothing and reported success. **When a cut changes nothing, assert on the
  volume drop.**
- **A copy of another part's number with a comment saying "MUST TRACK".**
  Three of these went stale in one day. Read the live parameter when the
  other part is in the document, and assert. A comment is not a mechanism.

## Housekeeping

~~139 uncommitted files.~~ **Committed 2026-08-26** in four batches on
`fusion-only-pipeline`: the legacy freeze, the Fusion-only instructions and
lint, the part scripts and specs, and the renders and exports. Identity is
now set locally on the repo. Working tree clean.

**`.venv` is broken** — it points at a `python3.11` that is no longer on the
Mac, so `.venv/bin/pytest` dies with a bad-interpreter error. `.venv-lint/`
was made with the system python3 to run the lint; it has pytest but not
numpy, so `tests/test_mesh_paint.py` cannot collect there. Rebuild `.venv`
properly from `requirements.txt` when convenient.

**The lint has 19 pre-existing failures**, none of them new: mostly
`test_no_magic_numbers_in_geometry` across the robotarm parts, plus a
try/except in `_preview_j1.py` and three unused-parameter hits.
`_check_j1.py` passes clean.

Fusion documents: `Default Project / robotarm / ` holds
`robotarm_gauge_plates`, `robotarm_assembly_preview`, `robotarm_turntable_j1`.
Roughly a dozen other unsaved scratch documents are open and are all
regenerable from the scripts — safe to close without saving.
