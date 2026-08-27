# _gauge_slim — measurement sheet

Print `exports/robotarm/gauge_slim_v2.3mf`, then work through this in order.
**Step 1 is not optional and everything else is read through it.**

Four pieces, 171 × 150 mm on the bed, 77,281 mm³ ≈ 64 g of PETG.

| Piece | What it is |
|---|---|
| `gauge_slim_plate` | every female feature, plus the truth row and the stubs |
| `gauge_slim_lever` | the ONE hex probe. Its 10.00 arm is also the sliding-fit probe |
| `gauge_slim_plug` | the ONE journal probe, a true Ø20.00 collar |
| `roller_cap` | the printed bearing retainer — use it for the spin test |

This supersedes `_gauge_fits` (117,941 mm³, 3h10m). Same answers, 65% of the
plastic. The difference: stations whose answer is a *dimension* were collapsed
to one feature and are now **derived** by `lib/gauge_reduce.py` from the truth
row. Stations whose answer is an angle, a spin, a droop or a destructive feel
are still swept, because no amount of calipering one feature gets you there.

## Print it the way the arm will be printed

A gauge printed on a different profile is measuring a different machine.

| | |
|---|---|
| Material | **the same spool the arm will use.** See the note below |
| Layers | 0.2 mm |
| Walls | 3 |
| Infill | 15–20 % |
| Support | **OFF. Not "auto", OFF.** |
| Brim | on — the plate is 2.4 mm and 96 × 150 |
| Orientation | plate flat, engraved face UP; lever hex-face DOWN; plug collar DOWN; cap flange DOWN |

**On PLA vs PETG.** `knowledge/materials.md` claims the PLA→PETG fit shift is
"≈ same", but that is handbook, and `calibration/2026-08-14-verge-pole-thread-fit.md`
says from an actual print that PETG runs slightly tighter. So gauging in one and
printing the arm in the other puts every clearance in this project on an
unmeasured assumption — which is the exact thing this plate exists to remove.
**Decide the arm's material first, then print the gauge in it.** The arm is
specced PETG because it holds poses under sustained load (PLA creeps), because
a stalled pruner is a hard stop (PLA is brittle), and because the MG995 sits
inside `shoulder_bracket` (PLA softens near 50 °C).

**Supports off matters more than anything else on this page.** The two
lying-down stubs (`FLAT`, `S11FLAT`) are horizontal Ø7.9 cylinders bridging off
a wall with nothing under them — exactly how `turntable_stator` prints its
roller axles. Their undersides *will* droop, and **that droop is the
measurement**. Let the slicer prop them up and the test tells you nothing.

Note the spool and profile in the calibration entry. If either changes, every
number below stops applying.

---

## Step 1 — machine truth

Top row and the small pad beside it. Caliper each twice, 90° apart, average.

| Feature | Nominal | Measured |
|---|---|---|
| `D20` boss, outside diameter | 20.00 | ______ |
| `D8` boss, outside diameter | 8.00 | ______ |
| `B20` bore, inside diameter | 20.00 | ______ |
| `B8` bore, inside diameter | 8.00 | ______ |
| `B4` bore, inside diameter | 4.00 | ______ |
| `BLOCK` length (Y, the long axis) | 20.00 | ______ |
| `BLOCK` width (X) | 10.00 | ______ |
| `BLOCK` height (Z) | 5.00 | ______ |
| plate outline, X (across the hex bar) | 96.00 | ______ |
| plate outline, Y (the long edge) | 150.00 | ______ |

**How to hold the calipers.**

- **Bosses: measure at mid-height, not at the base.** `D20` and `D8` grow from
  the bed and carry elephant foot on their first few tenths. `BLOCK` sits on
  top of the plate and does not. Comparing `D20` against `BLOCK`'s X and Y is
  therefore a free read on how much elephant foot this profile leaves —
  `ELEPHANT_FOOT_CHAMFER_MM` is 0.4 in `design_rules.py` and has never been
  re-checked on this spool.
- **`B4` is at the limit of caliper inside-jaws.** If yours will not sit
  square in a Ø4 hole, use pin gauges or the shanks of drill bits — find the
  largest that enters without force and record that. An unreliable `B4` is
  worse than a missing one, because the derived Ø4 insert leans on it.
- **The plate outline is two readings on a part already in your hand,** and it
  is the only measurement here that can separate a constant offset from a
  scale error. Measure across a flat run of edge, not through a lifted corner.
  Section 1b of `gauge_reduce` does the rest.

**Why the plate's own edges matter.** The published outside error on these
machines is shrinkage-dominated, and shrinkage is *proportional* — 20 mm loses
0.1, 100 mm loses 0.4. The truth-row bosses only span Ø8 to Ø20, which is far
too short a baseline to see that: a scale error reads as a small constant.
The distinction decides where the fix goes. A constant offset lands on FITS
and is fixed in `design_rules.py`. A scale error is nearly invisible on a
12 mm press fit but moves a joint centre by a millimetre on a 200 mm link, and
is fixed with the slicer's filament "Shrinking" percentage — applying it to
clearances instead would wreck every fit on the plate.

**Why five features and not two.** A fit is the difference between two printed
features, so the bias lands on every clearance in the project at once. The old
plate took that bias from one pair, which was enough when every fit also had
its own three-way sweep to fall back on. This plate has no such fallback — so
it needs to know whether the bias is the *same* at Ø4 as at Ø20. Usually it is
not: a small hole loses more to the perimeter pulling inward. Three bores give
`gauge_reduce` a curve to interpolate along, and if the curve is not straight
the script says so and marks the derived numbers as indicative instead of
quietly reporting a confident wrong answer.

**Before section 2 tells you anything, section 1 now tells you whether to
believe it.** `gauge_reduce` compares each reading against the published band
for this class of machine (`knowledge/materials.md`, "Expected dimensional bias
— the PRIOR"). If a reading falls outside it, that is a *configuration* signal,
not a design one — shrinkage compensation, flow, a stray X-Y hole compensation,
or nozzle wear — and the script names the likely cause. Fix it and reprint the
plate rather than absorbing it into `design_rules.py`, because everything else
on this sheet is derived from these eight numbers.

Two slicer traps worth knowing before you compensate anything: Bambu Studio's
X-Y hole compensation takes a **radius**, not a diameter (a 0.10 diameter error
needs 0.05 entered), and it **ignores open holes** — so the `SL10.25` slot and
every cable channel in the arm have to be right in CAD regardless.

Paste all eight into `MEASURED` in `lib/gauge_reduce.py` and run it. Section 2
prints the seven collapsed stations with a verdict on each. **Stop and read
section 2 before doing anything else** — if it flags a station TIGHT or LOOSE,
that is a 10-minute single-feature reprint, not a rebuild of the arm.

## Step 2 — the hex

Four sockets, engraved `10` `20` `30` `40` (hundredths of a mm of clearance).
Socket depth is **3.4 mm, which is what the arm actually uses** — `_gauge_fits`
used 4.0 and so measured a deeper, stiffer joint than the one being shipped.

1. Caliper the lever's hex across the flats. Nominal 15.80.
2. Lie the plate **flat on a table** and hold it down. Plate flex reads as
   backlash and there is no way to tell the two apart afterwards.
3. Drop the lever into the `10` socket. Push the tip one way until it stops,
   mark; push the other way, mark. **Measure between the marks in mm.**
4. Repeat for `20`, `30`, `40`.

The `20` station **is the arm as it ships** — same 15.80 boss, same 16.00
socket. It is the control.

| Socket | Tip travel (mm) | |
|---|---|---|
| `10` | ______ | |
| `20` | ______ | ← today |
| `30` | ______ | |
| `40` | ______ | |

A socket that will not accept the lever is not a candidate however tight it
looks; record 0.00 and `gauge_reduce` will exclude it. The tip sits at r = 63,
so 1.28° of play reads as 1.41 mm of travel — comfortably measurable.

## Step 3 — the bearing seats

You need three real 608ZZ bearings and the `roller_cap`.

Three seats engraved `S10` `S11` `S12` — a 0.5 mm shoulder of that diameter
under a Ø7.90 axle.

**DO NOT ASK "DOES IT SPIN FREELY".** A new 608ZZ is packed with grease and
does not free-spin in anyone's fingers — every seat fails that question and the
row tells you nothing. Found the hard way on 2026-08-26, where all three read
as dragging and the bearing turned out to drag identically in free air.

Run it as a COMPARISON instead:

1. Hold a 608 by its inner ring, off the plate, and flick the outer ring.
   **That feel is your baseline.** Register it before touching the plate.
2. Put the SAME bearing on each seat in turn and ask one question only:
   *does this feel worse than the baseline?*
3. If grease masks the difference — likely — degrease one bearing in IPA and
   repeat. You have six, and a clean bearing makes a light rub obvious.

| Seat | Spins freely? | |
|---|---|---|
| `S10` | ______ | |
| `S11` | ______ | ← `turntable_stator` uses this |
| `S12` | ______ | |

Only the inner race face (the annulus Ø8.0–Ø12.0) may be touched. Wider than
12.0 and the seat reaches over the gap toward the ZZ shield, which is fixed to
the **outer** race — so it drags. `turntable_stator` shipped 12.5 until that
was caught by arithmetic; this row settles it by experiment.

Then the two lying-down stubs:

| Feature | What to do | Result |
|---|---|---|
| `FLAT` | caliper it. Nominal 7.90. Measure the vertical axis *and* the horizontal — a drooped cylinder is not round | ______ / ______ |
| `S11FLAT` | put a 608 on it and spin | ______ |

If `S11` spins standing up and `S11FLAT` drags lying down, the droop is the
problem and not the seat diameter. That distinction is the whole reason both
are on the plate.

## Step 4 — the pilots

Eight holes on the small pad, `M3` (2.4 / 2.5 / 2.6 / 2.8) and `M2`
(1.6 / 1.7 / 1.8 / 2.0), smallest on the left. Drive a real screw into each
by hand.

The fourth value on each row is deliberately on the LARGE side. Every
published figure says a small hole prints under nominal, so a drawn 1.6 may
arrive at 1.3 and split the boss — a sweep of 1.6/1.7/1.8 could plausibly come
back "all three too tight", which costs a reprint and answers nothing.

Looking for: the screw cuts its own thread, goes fully home, and the boss does
**not** split or bulge. This test consumes the hole — that is why these are
still swept and not derived.

| | Best value |
|---|---|
| M3 self-tapping pilot | ______ |
| M2 servo screw pilot | ______ |

## Step 5 — the collapsed stations, if you want to confirm one

These are single features at today's value. `gauge_reduce` derives what they
*should* measure; caliper any you want to check the derivation against.

| Engraving | What it is | Drawn |
|---|---|---|
| `J35 P05` | journal bore / 608 pocket, stacked on one pad | 20.35 / 22.05 |
| `MG12.15` | the MG995 horn press — holds the whole arm up at J2 | 12.15 |
| `SL10.25` | sliding fit; the lever's own 10.00 arm is the probe | 10.25 |
| `SG90` | SG90 horn hub press | 7.15 |
| `INS` | M3 heat-set insert | 4.00 |
| `STUB` | vertical axle into a 608 bore | 7.90 |

The plug drops into `J35`; push it out with a rod through the Ø10 hole in the
floor. The lever's arm slides into `SL10.25`.

## Step 6 — write it down

Fill in `MEASURED` in `lib/gauge_reduce.py`, run it, and paste the whole report
into a dated note in `calibration/`. Then, and only then, change values in
`lib/design_rules.py` — and afterwards run `models/robotarm/_check_ledger.py`,
because a shared fit value touches all thirteen parts and the ledger is what
proves that changing one did not quietly reshape another.
