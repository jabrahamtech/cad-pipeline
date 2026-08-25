# Dimensioning — finding, trusting, and recording every number

Read when: filling a spec's interface table; any dimension is missing,
suspicious, or derived; a print didn't fit.

## Source hierarchy — always tag the source

1. **MEASURED** — calipers on the real object Jonathan holds. The only
   source good enough for a critical fit.
2. **STEP** — vendor CAD of the mating part. Trust geometry, not tolerance;
   the physical sample can still differ (ask for one measurement to anchor).
3. **DATASHEET** — nominal. Fine for hole patterns and standards (25.5 mm
   FC grid, 9×9 motor pattern); weak for body dimensions of cheap parts.
4. **ASSUMED** — a guess. Allowed only when Jonathan declines to measure;
   flagged in the spec, in the delivery summary, AND in the Fusion user
   parameter's comment. First suspect when a print doesn't fit.

## Caliper protocol (what to ask Jonathan to do)

- Measure the actual sample, not the listing. Three readings, report the
  spread if > 0.05 mm — a spread means an out-of-round or tapered part.
- ODs: measure two axes 90° apart. Bores: use the knife-edge jaws, rock to
  the maximum. Depths: depth rod, zeroed on the rim.
- Center-to-center of two holes: measure edge-to-edge same-side, or
  (near-edge + far-edge)/2 when jaws don't fit.
- Ask in ONE batch — list every dimension needed, why each matters, and
  which are fit-critical so effort goes where it counts.

## Datum discipline

- One datum per part (a face + an axis, usually the mating face and the
  primary bore/axis). Every dimension chains from the datum, not from the
  previous feature — chained dims accumulate error.
- In Fusion this means: derived user parameters as EXPRESSIONS from the
  datum-anchored ones (`gb_hole_x = gb_board_w/2 - gb_hole_inset`), so one
  corrected measurement propagates.

## Sanity checks before geometry

- Units: everything into mm at the spec boundary; state converted values
  (2.5 in = 63.5 mm, never 63 or 64) for confirmation.
- Cross-check: does the sum of sub-dimensions equal the overall? Does the
  hole pattern fit inside the outline? Do datasheet and measurement agree
  within 0.3 mm — if not, the sample wins and say so.
- Anything cantilevered off an ASSUMED value: design a gauge for it
  (see knowledge/joints_tolerances.md, gauge-first).
