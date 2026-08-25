# neo65 canopy — spec

Project: `models/neo65/canopy.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->
Model mass: 2.5 cm³ → 2.7 g in ASA (budget ≤ 4 g). Exported v1 2026-08-09.
Pod upper corners are notched (open at the top corners) to clear the front
duct ring walls — camera retention is floor + front wall + lower side walls.

## Function
Camera pod + FC cover for the neo65 frame. Holds the BetaFPV C03 FPV camera
at a fixed uptilt in a front pod, roofs over the AIO FC, and mounts by its
four legs on the FC mounting screws (long M2: canopy leg → FC grommet →
frame post). The C03's video stream is the tracking + recording feed
(recorded on the lab PC — no separate recording camera is carried; a 39 g
action cam exceeds the whole aircraft's payload).

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Leg holes | 4× Ø2.4 thru on 25.5 × 25.5 grid | DATASHEET (whoop AIO standard) |
| Leg height (FC-top plane → roof underside) | 7 mm (clears USB/VTX) | ASSUMED (verify on purchased FC) |
| Camera body | C03: 11 × 14.1 × 13.5 mm, 1.45 g | DATASHEET (BetaFPV C03) |
| Camera pocket | 14.25 wide (0.15 press fit), open top, Ø10.5 lens window | DERIVED / lens Ø ASSUMED |
| Camera uptilt | 15° (slow indoor tracking flight) | USER-TUNABLE parameter |
| Prop keep-out | all canopy geometry ≥ 16 mm from every motor axis below duct-top height (props sweep Ø31 at 32.5 mm from frame center); pod front corners chamfered for this | DERIVED — do not widen the pod |
| Rear opening | FC USB + battery lead + VTX antenna exit clear | DESIGN |

## Loads & environment
Crash impact only; camera must not eject. Indoor, room temperature.

## Print plan
ASA · printed legs-down (pod tip is above the roof plane, so roof-down
cannot sit flat) · dual nozzle, support material under roof plate and pod
· 3 walls, solid (part is thin-shell). 0.4 mm elephant's-foot chamfer on
bed-contact edges (leg feet).

## Acceptance
- [ ] invariant tests pass
- [ ] C03 press-fits, lens window unobstructed at 15°
- [ ] legs land on FC grommets, M2 screws reach frame posts
- [ ] props do not touch canopy at full deflection (visual spin check)
- [ ] printed and verified — date, measured result, deviations
