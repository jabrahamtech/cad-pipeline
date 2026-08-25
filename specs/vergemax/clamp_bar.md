# Verge Max clamp bar — spec

Project: `models/vergemax/clamp_bar.py`
Status: MODELED

## Function
Adapter that mounts on a Neewer ST-200 light stand (92–200 cm, 8 kg capacity;
5/8" stud with 1/4"-20 threaded tip) and presents a horizontal "desk edge"
plate that the amaran Verge Lock
Desk Clamp Stand (included with the Verge Max) grips. The metal amaran clamp
continues to carry the light; this part only has to be a rigid fake desk edge
locked to the stand.

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Neewer stud diameter (5/8") | Ø15.9 mm | MEASURED |
| Neewer 5/8" stud length (below threaded tip, incl. base collar) | 31 mm | MEASURED |
| Stud base collar | Ø21 × 4 mm — counterbore in lib/stand_socket | MEASURED |
| 1/4"-20 tip: thread length | 5 mm | MEASURED |
| 1/4"-20 hex nut (captive): AF 11.11, thick 5.6 | COTS | DATASHEET |
| amaran clamp jaw range (desk thickness) | 20–70 mm | DATASHEET |
| amaran clamp throat depth (how far jaws reach in) | ASSUMED ≤ 80 mm — plate made deeper than any plausible throat | ASSUMED |
| amaran clamp pad footprint (width × depth) | ASSUMED ≤ 100 × 70 mm — plate oversized to cover | ASSUMED |
| Verge Max weight (load) | ~3.6 kg (8 lb) | DATASHEET |
| Stud-to-socket fit | sliding, 0.25 mm clearance | design rule |

## Loads & environment
Static indoor. ~3.6 kg light cantilevered via the amaran clamp; the bar sees
the clamp's squeeze force plus a bending moment at the stud socket. No
vibration, room temperature.

## Print plan
PETG (functional mount, sustained clamp load — PLA creeps). Print plate-side
down so clamp squeeze and stud bending load within layers, not across them.
Dual not needed if geometry stays self-supporting. Infill ≥40%, 5+ walls.

## Design sketch
- Horizontal plate sized to the clamp pads + margin, thickness in the middle
  of the clamp's jaw range (mimics a desk edge).
- Boss underneath with 5/8" socket (sliding fit) over the stand stud; the
  1/4"-20 tip passes through and is clamped by a recessed 1/4"-20 nut on the
  plate top (COTS nut — not printed thread), pulling the bar down onto the
  stud shoulder. Socket depth takes the bending moment.
- Anti-rotation: nut clamp force + knurled washer face if needed after test.

## Gauge
`clamp_bar_gauge` (same generator, plate_width=40) prints in PLA to verify
every fit before the PETG production run: socket, nut pocket, web
engagement, jaw bite at 30 mm, throat/boss clearance. PLA→PETG shrinkage
differs slightly — a snug PLA socket may want +0.1 mm clearance in PETG.

## Acceptance
- [ ] invariant tests pass
- [ ] fits the real object (sliding fit on stud; clamp grips plate mid-range)
- [ ] printed and verified — date, measured result, deviations

On ACCEPTED: record measured fit deviations in `calibration/`.
