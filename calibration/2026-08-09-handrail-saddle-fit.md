# Saddle bore fit — confirmed via saddle_gauge_v2 (2026-08-09)

Printed: saddle_gauge_v2, PETG, flat on bed, 0.4 mm nozzle.
Result: user reports well fitted — passes over the rail ends and slides.

Validated values:
- Rail interface: 16.0 × 30.0 mm rounded rectangle, 7.0 mm end arcs
  (user-corrected values; arcs and 30 mm height were never caliper-measured,
  now confirmed by print instead)
- SLIDING_FIT_CLEARANCE_MM = 0.25 per side held for this obround bore shape
  in PETG — consistent with the existing design rule, no change proposed.

Applies to: models/handrail/rail_bracket.py (bore_dims) and saddle_gauge.
