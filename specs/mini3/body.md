# mini3 body — spec

Project: `models/mini3/body.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->
Model mass: 29.7 cm³ → 31.8 g in ASA (budget ≤ 40 g). Exported v1 2026-08-08.

## Function
Unibody structural frame (hub + 4 fixed arms) for a 3-inch, sub-250 g AUW
quadcopter in the DJI Mini weight class. Carries a 25.5×25.5 whoop-class AIO
flight controller, four 1404 motors, and a top-strapped 2S battery. This part
is the frame only — 249 g is the *all-up* target including electronics; the
frame's mass budget is ≤ 40 g. A DJI-style canopy/shell is a separate
follow-on part (v2), not this one.

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Wheelbase (motor-to-motor diagonal) | 140 mm | USER DECISION (3″ props) |
| Motor mount pattern (×4) | 4× Ø2.4 mm thru on 9×9 mm square, M2 screws | DATASHEET (1404 class: BETAFPV/GEPRC SpeedX2 1404) |
| Motor base diameter (pad size) | Ø19 mm pad for ~Ø18 mm base | ASSUMED (typical 1404 base; verify against purchased motor) |
| Motor shaft relief | Ø5 mm center hole per pad | ASSUMED (bell shaft/circlip protrusion, common practice) |
| FC mount | 4× Ø2.4 mm thru on 25.5×25.5 mm grid, M2 hardware from below, heads counterbored Ø4.4×1.5 | DATASHEET (whoop AIO standard) |
| FC board keep-out | ≥ 36.5 × 36.5 mm clear above deck | DATASHEET (largest common 25.5-pattern boards) |
| Battery | 2S 650 mAh LiPo class, ~60 × 30 × 16 mm, strapped over FC stack | ASSUMED (brand-nominal; strap mount tolerates variation) |
| Battery strap slots | 4× slots 14 × 3.2 mm for a 12 mm strap, two straps | ASSUMED (standard 12 mm strap) |
| Prop clearance | 3″ (Ø76.2) props; plan-view clearance prop-tip→battery corner ≈ 1 mm, vertical clearance ≈ motor height. Battery packs wider than 32 mm risk prop strike | DERIVED |
| M2 screws, standoffs, straps | bought hardware (COTS) | — |

## Loads & environment
Flight loads: motor thrust bending on arms, crash impact, continuous
vibration. Outdoor, sun exposure. Printed flat so bending stress in arms
stays in-plane with layers (layer-adhesion rule).

## Print plan
ASA · flat on the deck's underside (arms/hub in one plane; loads in-plane
with layers) · single nozzle, no supports (only bridges are the shallow
FC counterbores) · 6 walls / ~40 % gyroid — frames want walls over infill.
Heated chamber on (X2D handles ASA). 0.4 mm elephant's-foot chamfer on
bottom edges.

## Acceptance
- [ ] invariant tests pass
- [ ] fits the real objects: motors bolt on 9×9 M2, FC on 25.5 grid (clearance fit)
- [ ] frame mass ≤ 40 g printed
- [ ] printed and verified — date, measured result, deviations

On ACCEPTED: record any measured fit deviations in `calibration/` — that is
what updates the design rules, not guesses.
