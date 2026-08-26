# robotarm — handoff

Written 2026-08-26 at the end of a long session. Everything a fresh
conversation needs in order to carry on. The repo is the state; this file is
the index to it.

## Where the project actually is

`GATE ledger : PASS` — 14 parts, 0.000 drift, `specs/robotarm/_volumes.json`.
`GATE interference (J2)` : PASS, 0.000 across −25°…+160°.

Run order for the whole-project gate: `models/robotarm/_check_ledger.py`
with `mod.BATCH = 0,1,2,3` in sequence. Batch 3 prints the table.

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
4. **There is no J1 gate.** The turntable has never been swept in Fusion the
   way `_check_shoulder.py` sweeps J2. Every J1 clearance in this repo is
   arithmetic. Given what the shaft-offset bug turned out to be, this is the
   highest-value missing check in the project.
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

**139 uncommitted files.** I cannot `git commit` from the bridge — no
identity configured. This wants doing on the Mac before anything else is
built on top of it.

Fusion documents: `Default Project / robotarm / ` holds
`robotarm_gauge_plates`, `robotarm_assembly_preview`, `robotarm_turntable_j1`.
Roughly a dozen other unsaved scratch documents are open and are all
regenerable from the scripts — safe to close without saving.
