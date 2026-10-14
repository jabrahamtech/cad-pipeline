# as5600_4hole_clamp — spec

Project: `models/robotarm/_mesh_as5600_4hole_clamp.py` (mesh stopgap — Fusion MCP down 2026-10-14; a Fusion script is owed)
Status: MODELED

## Function
Converts the three existing AS5600 mounts (J3 plate, J4 plate, J2 cap lid) to hold the new 4-hole AS5600 board
by its holes, without drilling or reprinting the mount. The board still drops into the 23.4 pocket chip-down, so
the magnet-to-chip gap (1.0) is unchanged. Two halves per mount. Each half lays a bar over two of the board's holes:
pegs locate in the holes and Ø3 rings press the copper round them. A foot sits on the plate under the EXISTING M2 × 5 + washer
in the EXISTING pilot.

## Interfaces — the dimensions that matter

| Interface | Value | Source | Joint / fit |
|---|---|---|---|
| board outline | 23 × 23 | MEASURED (Jonathan 2026-10-14) | in the existing 23.4 pocket (locational) |
| board holes | 4 on a 15.5 × 15.5 square, chip centred | MEASURED | peg Ø1.8 = HOLE_D_MIN − LOC |
| board hole Ø | ≥ 2.0 | **ASSUMED** | locational on the peg |
| board thickness | 1.6 | **ASSUMED** (lib/cobot BOARD_T) | sets the preload |
| underside parts | chip only | MEASURED ("nothing" else) | — |
| pocket | 23.4 sq × 1.0 deep | lib/cobot BOARD_POCKET(_H) | — |
| clamp pilots | M2 pilot at (0, ±12.9) from the board axis | lib/cobot CLAMP_OFF | M2 clearance Ø2.4 |
| foot preload | foot 0.15 below plate-top + 0.6 board proud | CHOSEN | clamps the board on tightening |

## Loads & environment
Static: holds a 1–2 g board against arm motion. Indoor.

## Cables & service
Pads are soldered. Turn the board so its pin row lies along an edge PARALLEL to the line through the two clamp
screws: those edges only have the bar ends (u ±9.0) and rings (u ±9.25) near them. The other two edges have the web
crossing their middle 5 mm. On the J2 lid that matches the wire groove (az 153°).

## Print plan
PETG, top face on the bed (pegs and foot up), no supports, 100 % infill (0.2 g each). Six halves per plate
(3 mounts × 2): `exports/robotarm/cobot/cobot_plate_as5600_clamps_petg.3mf`.

## Acceptance
- [x] mesh watertight, one body; plan reach r 15.4 inside the forearm shell (FA_IN − LOC); lug clears the J4 standoffs by 0.93
- [ ] board thickness and hole Ø calipered: if thickness < 1.5 the foot gives no preload, so regenerate with the real BOARD_T
- [ ] printed and fitted on one mount: date, result
