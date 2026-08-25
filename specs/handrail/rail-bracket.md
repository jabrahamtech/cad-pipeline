# rail-bracket — spec

Project: `models/handrail/rail_bracket.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
Replacement for a chrome wall-mounted wardrobe-rail bracket (IMG_9979): wall
plate screwed to the wall, projecting stem, closed obround saddle loop the rail
passes through. Holds a clothes rail; one of several brackets on the rail.
Rail must be slid through the loop from the end at install (user chose closed
loop).

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Rail cross-section | rounded-edge rectangle, 30.0 × 16.0 mm; long axis HORIZONTAL (pointing away from wall) | USER (v6 correction: 30 mm, was 35 from the sketch) |
| Rail end-arc radius | 7.0 mm (was ASSUMED 4.0 — pole wouldn't enter) | USER (v4 fit correction, still not caliper-measured) |
| Saddle bore | 16.5 tall × 30.5 deep mm, 7.25 mm tip arcs (sliding fit, +0.25 mm/side) | design_rules |
| Overall projection, wall face → tip | 74.0 mm | MEASURED (user, sketch) |
| Wall plate | 60 × 26 mm, 6 mm thick, rounded corners | CHOSEN (user: "doesn't matter", sized for PETG) |
| Screws | 2 × 4 mm countersunk wood screws (4×40 + wall plugs), 40 mm c-c vertical | CHOSEN (user: "whatever is best") |
| Screw holes | Ø4.5 thru, countersink Ø9 × 90° | derived from screw |
| Saddle ring wall | 4.0 mm; outer corners follow bore radius | CHOSEN (strength) |
| Stem-to-ring neck | 7 mm tangent arc (v3, user request) | USER |
| Stem position | flush with one plate edge along the rail axis, centred vertically (v5 — prints flat, no support; reverted v3's centring) | USER |
| Ring/stem depth along rail | 12 mm | CHOSEN (strength) |
| Stem section | 14 tall × 12 wide mm (v2: shortened to fit the rotated ring's flat face) | CHOSEN (strength) |

## Loads & environment
Clothes rail: sustained static load, est. 50–100 N per bracket at 74 mm
cantilever (~5–7 N·m at the plate). Indoor, room temp. Bending stress in the
stem ≈ 10 MPa — comfortable for PETG *within* layers, so layers must run along
the stem axis.

## Print plan
PETG, 4+ perimeters, 40% infill. Printed lying flat on its flush side face
(plate, stem and saddle all touch the bed) — layers lie in the plate-height
× projection plane, so stem bending is carried within layers.
Self-supporting; single nozzle. Elephant-foot chamfer on the bed face.

## Acceptance
- [x] invariant tests pass
- [x] rail slides through saddle — bore validated by saddle_gauge_v2 print
      (2026-08-09, see calibration/)
- [ ] plate sits flat, screws seat flush in countersinks
- [ ] printed and verified — date, measured result, deviations
