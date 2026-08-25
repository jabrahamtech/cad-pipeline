# shim_gauge — spec

Project: `models/deskmount/shim_gauge.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
4 mm-wide slices of clamp_shim (shared `build()` — cannot drift) to
confirm measured clamp/desk dimensions before committing to the 3 h full
print. v4 is a slot-gap sweep plate: three slices at 22.0 / 22.5 /
23.0 mm gap (v3 nominal 23.5 felt loose), gap value debossed on each.
Each slice also re-verifies the 79 mm throat and the clamp jaw stack.

## Interfaces — the dimensions that matter
Identical to `specs/deskmount/clamp_shim.md` — the gauge imports the
shim's `build()` with `width=4`. Slot gap is swept (GAP_SWEEP_MM in the
model) for calibration; all other dimensions identical to the shim.

## Loads & environment
Hand-tight clamp check only; not a structural part. Discard or keep as a
setup gauge after v2 is confirmed.

## Print plan
Any loaded filament (PLA fine — no sustained load). Same orientation as
the shim: profile flat on the bed, 4 mm tall, no supports. 10 % infill,
2 perimeters. Sweep plate: 3 bodies, ~15 g, ~20 min.

## Acceptance
- [ ] invariant tests pass
- [ ] one sweep slice is a snug slide on the desk edge — note WHICH gap
- [ ] clamp closes hand-tight on a slice; pad fully on the bottom plate
