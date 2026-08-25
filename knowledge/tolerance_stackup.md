# Tolerance stack-up — why chains of good parts still don't fit

Read when: three or more dimensions/interfaces stand between two features
that must align; a multi-piece assembly; anything with a lid that "almost"
closes. Companion: joints_tolerances.md (single-fit rules),
dimensioning.md (datum discipline).

## The failure this prevents

Each printed dimension is good to about ±0.15 mm (X2D, calibrated, in-
plane; ±0.25 across layers/large parts — HANDBOOK, gauge to confirm).
Five features chained end-to-end can therefore disagree by ±0.75 mm
worst case — more than an entire sliding fit. Parts that each pass their
gauge still jam as a set when nobody budgeted the chain.

## Method (do this in the assembly spec, it's 10 lines)

1. **Draw the loop:** from feature A to feature B, list every dimension
   crossed, with sign (+/−), including CLEARANCES as dimensions.
2. **Worst case:** gap = Σ nominals ± Σ |tolerances|. Use ±0.15 per
   printed dim (±0.25 across layers), COTS tolerance from datasheet,
   0 for a machined reference.
3. **Check both failure directions:** minimum gap ≥ 0 (no jam) AND
   maximum gap ≤ what the function allows (no rattle/misalignment).
4. If the worst case fails but barely, statistical (RSS) view:
   √(Σ t²) — legitimate for 4+ independent dims on non-safety fits;
   say which basis you used.

## Fixing a failing stack — in order of preference

1. **Shorten the chain:** re-datum so both features measure from the SAME
   face/bore (dimensioning.md). The best stack-up is two dimensions long.
2. **One-piece the chain:** merge the parts the chain crosses (envelope
   permitting) — a printed monolith has no assembly stack.
3. **Add a compliant element:** one slot, one oversized hole, a TPU
   washer, a foam pad — ONE deliberately loose spot absorbs the whole
   stack; the pin+slot rule is this principle applied to 2D.
4. **Adjustability:** slotted mount + lock after fitting; set-at-assembly
   beats print-perfect for long chains (state it in assembly order).
5. **Tighten tolerances LAST** — it means gauging every dim in the chain
   per material; expensive, do it only for the one dim that dominates.

## Printed-specific stack contributors people forget

- First-layer squish: bottom faces sit ~0.1–0.2 proud/wide (elephant
  chamfer handles edges, not face height) — a Z-stack of N printed faces
  grows ~0.1·N.
- Seam bumps: outer-wall seams add ~0.1–0.3 locally — keep seams off
  mating faces (slicer note in the print plan) or add relief grooves.
- Warp: long parts bow; a stack across 200 mm of PETG can carry 0.3+ of
  banana. Relieve the middle, register at pads near the ends.
- Material change: a stack budgeted in PLA does not transfer to ABS/PA
  (materials.md fit-shift row) — re-gauge the dominant dim.

## Where it lands in the workflow

The assembly spec's joint-contract table gets a "stack" line for every
alignment that crosses ≥ 3 dims: the loop, the basis (WC/RSS), the
result, and which fix above was applied. `_check_fit.py` then measures
the REAL modelled gap at nominal — if the model's nominal gap differs
from the loop arithmetic, a dimension isn't coming from the shared
parameters (coupling bug — find it before printing).
