# mini3 — 3″ sub-250 g quad frame

Unibody structural frame (hub + 4 fixed arms) for a 3-inch, sub-250 g AUW
quadcopter in the DJI Mini weight class. Frame mass budget ≤ 40 g
(v1 modeled: 29.7 cm³ ≈ 31.8 g in ASA). Spec: `specs/mini3/body.md`.
Model source: `legacy/models/mini3/body.py` (build123d era — a Fusion
re-authoring gets a fresh script under `models/mini3/` if the design moves
again).

## Status

v1 exported (`exports/mini3/body_v1.3mf|.step`, 2026-08-08) — **not yet
printed**. A DJI-style canopy/shell is a planned follow-on part (v2).

## Printed parts

| Part | Version | Material | Orientation |
|---|---|---|---|
| body (frame) | v1 (not yet printed) | ASA (vibration + outdoor) | flat, arms in the XY plane — loads within layers |

## Bought parts (planned BOM)

- 4× 1404-class motors (BETAFPV / GEPRC SpeedX2 1404), M2 mount hardware
- 25.5 × 25.5 mm whoop-class AIO flight controller, M2 hardware
- 2S 650 mAh LiPo (~60 × 30 × 16 mm) + battery strap
- 3″ props

## Open items

- Verify motor base Ø and shaft relief against the purchased motors
  (ASSUMED in spec).
- Gauge print of one motor pad + FC counterbores before committing the
  full frame.
