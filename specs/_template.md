# <part name> — spec

Project: `models/<project>/<part>.py`
Status: DRAFT <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
One or two sentences: what it does, what it attaches to, where it lives.
Part of an assembly? Name the `specs/<project>/_assembly.md` row it fulfils.

## Interfaces — the dimensions that matter
Every value the part must match. Source is MEASURED (calipers), DATASHEET,
STEP (vendor file), or ASSUMED. ASSUMED values must be listed in the
delivery summary and are first suspects when a print doesn't fit.
Joint names a type from `lib/design_rules.py` JOINT_FIT_MM (press /
locational / sliding / rotating / free / bearing_pocket) — the clearance
comes from there, never invented (knowledge/joints_tolerances.md).

| Interface | Value | Source | Joint / fit |
|---|---|---|---|
| e.g. board outline | 65.2 × 30.1 mm | MEASURED | locational (0.20) |
| e.g. mounting holes | Ø3.2 on 58 × 24 grid | DATASHEET | M3 clearance |
| e.g. bearing seat | 608ZZ Ø22 × 7 | DATASHEET | bearing_pocket (0.05, gauge) |

## Loads & environment
Static / vibration / impact; temperature; indoor / outdoor. One line is fine
("static, indoor, no load" is a valid answer).

## Cables & service <!-- delete section only if truly unpowered -->
Where wires enter, exit, and live; strain relief at each entry; which
connectors must stay reachable (knowledge/cable_management.md). "n/a —
unpowered" is a valid answer.

## Print plan
Material · orientation (and why, re layer adhesion) · single or dual nozzle
· rough infill.

## Acceptance
- [ ] script lint passes; design review checklist run (knowledge/design_review.md)
- [ ] fits the real object (which fit: press / sliding / clearance)
- [ ] printed and verified — date, measured result, deviations

On ACCEPTED: record any measured fit deviations in `calibration/` — that is
what updates the design rules, not guesses.
