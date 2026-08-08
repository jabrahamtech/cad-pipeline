# <part name> — spec

Project: `models/<project>/<part>.py`
Status: DRAFT <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
One or two sentences: what it does, what it attaches to, where it lives.

## Interfaces — the dimensions that matter
Every value the part must match. Source is MEASURED (calipers), DATASHEET,
STEP (vendor file), or ASSUMED. ASSUMED values must be listed in the
delivery summary and are first suspects when a print doesn't fit.

| Interface | Value | Source |
|---|---|---|
| e.g. board outline | 65.2 × 30.1 mm | MEASURED |
| e.g. mounting holes | Ø3.2 on 58 × 24 grid | DATASHEET |

## Loads & environment
Static / vibration / impact; temperature; indoor / outdoor. One line is fine
("static, indoor, no load" is a valid answer).

## Print plan
Material · orientation (and why, re layer adhesion) · single or dual nozzle
· rough infill.

## Acceptance
- [ ] invariant tests pass
- [ ] fits the real object (which fit: press / sliding / clearance)
- [ ] printed and verified — date, measured result, deviations

On ACCEPTED: record any measured fit deviations in `calibration/` — that is
what updates the design rules, not guesses.
