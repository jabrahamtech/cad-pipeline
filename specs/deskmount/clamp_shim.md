# clamp_shim — spec

Project: `models/deskmount/clamp_shim.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
C-channel shim that wraps a thin (~22 mm) desk edge so a monitor-arm desk
clamp can grip it: raises effective thickness into the clamp's working
range, spreads the clamp foot and screw-pad pressure over a larger area,
and protects the desk surface. Carries an LG 34" ultrawide (~6.3 kg,
design for 8 kg) on the arm. v2: asymmetric plates — 4 mm top (foot is
already spread), thicker bottom (spreads the Ø10 pad). v3: throat 79 mm per gauge v2; plate depth 82 mm. v4: slot gap 22.5 mm from gauge sweep; bottom plate doubled to 12 mm at user request.

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Desk thickness | ~22 mm (slot gap 22.5 = 22.0 + sliding clearance) | GAUGE-FIT (v4 sweep: 22.5 snug; earlier estimates 20, 23 both wrong) |
| Rough shim envelope (user's mental model) | ~80 × 80 × 30 mm | ASSUMED (guidance only, not a constraint) |
| Clamp foot (top jaw) W × D | 60 × 60 mm | MEASURED |
| Screw pad (bottom) diameter | Ø10 mm | MEASURED |
| Clamp throat depth (desk edge → screw center) | 79 mm | GAUGE-OBSERVED (was 40 crude; pad fell ~10 mm past the 74 mm tip) |
| Clamp jaw opening | 10–80 mm (shimmed stack 38 mm sits mid-range) | MEASURED |
| Monitor + arm load | 6.3 kg monitor (LG 34WN80C-B class), design 8 kg | DATASHEET |
| Desk slot fit | sliding, 0.25 mm/side | design rule |

## Loads & environment
Static clamp preload (large) + cantilever moment from arm, indoor, room
temp. Clamp compression is the dominant load; layer orientation must put
compression through the plate faces, not across a bonded joint.

## Print plan
PETG (sustained clamp pressure — PLA creeps badly). Print standing on an
X end face — the C profile flat on the bed, 100 mm tall. No supports;
plate bending under clamp load stays within layers, clamp compression
crosses layers (compression is safe across layers). Single nozzle.
40 % gyroid infill, 4 perimeters, 5 top/bottom layers.

## Acceptance
- [ ] invariant tests pass
- [ ] fits the real object (sliding fit over desk edge; clamp closes in range)
- [ ] printed and verified — date, measured result, deviations
