# antler trellis — spec

Project: `models/trellis/antler_hub.py`, `models/trellis/antler_upper.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
Vine-support trellis (tomatoes, beans) shaped as two reindeer antlers joined
at a Ø50 mm ring. The ring's stem slots into a Ø50 mm port hole on a vertical
aeroponic tower; a flexible "gyrocup" (OD ≈ 50 mm) is then pushed inside the
ring bore and its outward spring wedges the trellis in the port. Each antler
is 500 mm long (measured along the beam path) with six branches for tying /
winding vines.

Total assembly exceeds the print envelope → 3 printed pieces:
1. `antler_hub` — ring + flange + both lower antler halves (mirrored pair)
2. `antler_upper` ×2 (right + mirrored left) — press-fit spigot joint + glue

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Tower port hole | Ø50.0 mm | ASSUMED (user-stated nominal, not measured) |
| Stem OD into port | 49.75 mm (Ø50 − sliding fit 0.25) | design rule |
| Gyrocup OD | ≈ 50 mm, flexible body | ASSUMED (not measured) |
| Ring bore ID (cup wedges in) | 45.5 mm → ~4.5 mm diametral squeeze on the cup | ASSUMED (depends on cup flexibility) |
| Stem insertion depth | 45 mm | ASSUMED (port depth unknown) |
| Port axis orientation | horizontal (perpendicular to tower wall) | ASSUMED — if the tower ports are angled up 30–45°, say so and the antlers get a compensating tilt |
| Flange seat on tower wall | flat annulus, Ø58 | ASSUMED (wall assumed locally flat) |
| Antler length along beam path | 500 mm each | user |
| Branches per antler | 6 | user |
| Segment joint | spigot Ø8.0 × 20 into socket Ø8.15 × 22 (press fit 0.15) + CA glue | design rule |

## Loads & environment
Growing vine load, increasing over the season; cantilevered from the port on
one Ø50 socket. Wet (aeroponics), possibly sunlit. Cyclic light wind loads if
outdoors. **Material is PLA at the user's choice — creep under sustained
cantilever load and UV embrittlement are known risks; keep vine weight modest
and re-tie main load near the hub.** Moment capacity is limited by the
gyrocup wedge in the port, not the plastic — heavy one-sided load may rotate
the trellis in the port.

## Print plan
PLA (user choice) · dual-nozzle mode with support filament (envelope
235.5 × 256 × 256) · all pieces print "lying down" (assembly-Y vertical:
hub with stem tube pointing down, plate horizontal, antlers fanned low —
max height ≈ 143 mm) so beam axes stay in-plane → bending loads run within
layers, not across them · organic 3D branches need support in this or any
orientation, which the aux nozzle earns here · 20 % gyroid infill, 4 walls
(thin beams are mostly walls anyway).

## Acceptance
- [ ] invariant tests pass
- [ ] stem slides into tower port (sliding fit), gyrocup wedges in ring bore
- [ ] spigot joints press together, glued
- [ ] printed and verified — date, measured result, deviations

On ACCEPTED: record any measured fit deviations in `calibration/`.
