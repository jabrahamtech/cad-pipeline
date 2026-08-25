# neo65 frame — spec

Project: `models/neo65/frame.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->
Model mass: 13.1 cm³ → 14.0 g in ASA (budget ≤ 14 g). Exported v1 2026-08-09.
Assembly interference checks (canopy, props, battery): PASS —
`models/neo65/_check_assembly.py`.

## Function
Unibody ducted frame for a 65 mm-wheelbase 1S brushless whoop (~half a DJI
Neo footprint) used as an indoor autonomous follow-camera: the drone streams
FPV video to a lab PC which runs person tracking and sends commands back
(offboard autonomy — onboard tracking compute does not exist at this weight).
Full prop ducts are mandatory: it flies near a person. Carries a 25.5 × 25.5
whoop AIO FC, four 0802 motors, 31 mm props, an under-slung 1S 450 mAh pack,
and the C03 camera canopy (separate part, shares the FC screws).

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Wheelbase (motor-to-motor diagonal) | 65 mm | USER DECISION (standard 65 mm whoop class) |
| Props | Ø31 mm (Gemfan 1219 class), 1.0 mm shaft push-fit | DATASHEET |
| Duct inner Ø | 34.5 mm (≥1.75 mm tip clearance) | DERIVED |
| Motor mount (×4) | 3× Ø1.6 thru on Ø6.6 bolt circle, M1.4×4 screws from below | DATASHEET (0802 class; **verify on purchased motor before printing**) |
| Motor pad | Ø11.5 pad on 4 mm riser (props must clear FC + canopy legs), Ø4 center relief, Ø3.2 screw-head pockets from below so stock M1.4×4 screws reach through the 2 mm web | DATASHEET (0802 10.5×10.5×13.8 mm) / relief + pockets ASSUMED |
| Prop plane height | ~14–18 mm above deck (pad riser + 0802 bell/shaft stack); duct ring band spans 14–20 | ASSUMED (verify with motor+prop in hand; sets duct ring band height) |
| FC mount | 4× Ø1.7 self-tap for M2 on 25.5 × 25.5 grid, 2 mm posts | DATASHEET (whoop AIO standard) / self-tap Ø ASSUMED |
| FC keep-out | 32.5 × 32.5 mm clear above posts; tall components (USB/VTX) must sit centrally — board corners pass under prop discs with ~2 mm clearance | DATASHEET (largest 25.5-grid boards) |
| Battery | 1S 450 mAh BT2.0, 62 × 15.5 × 6.7 mm, slides into under-deck cradle from rear | DATASHEET (BetaFPV BT2.0 450) |
| Battery channel | 16.0 wide × 6.95 tall (sliding fit 0.25), bottom lips, front stop wall | DERIVED (design rules) |
| Canopy mount | shares the 4 FC screws (long M2 through canopy leg → grommet → post) | DESIGN |
| M1.4 / M2 screws, grommets, props, motors, FC, battery | bought (COTS) | — |

## Mass budget (flying weight — the whole point of this part)
| Item | g |
|---|---|
| frame (this part, ASA, budget) | ≤ 14 |
| canopy + camera mount (ASA) | ≤ 4 |
| 4× 0802 motor | 7.6 |
| 4× 31 mm prop | 1.6 |
| AIO FC (F4 1S 5A, ELRS RX + VTX on board) | 4.6 |
| C03 camera | 1.5 |
| 1S 450 mAh BT2.0 | 12.7 |
| wiring, screws, grommets | 2.5 |
| **AUW target** | **≤ 48** (modeled sum: 47.2) |

Thrust ≈ 4 × 30 g (0802 19500KV, 31 mm) → T/W ≈ 2.5. Printed frame is
~4× heavier than the $6 injection-moulded COTS equivalent (Meteor65, 2.7 g);
accepted because the custom canopy/camera integration is the project. If
flight time disappoints, the COTS frame is the fallback.

## Loads & environment
Flight vibration, crash impact (indoor, near a person — ducts are guards).
Indoor, room temperature. Ductic ring band carries prop-strike loads.

## Print plan
ASA (crash toughness; PLA too brittle at these wall thicknesses) · printed
flat, bed = rib-feet/battery-rail plane, so deck and arm bending loads stay
in-plane with layers · **dual nozzle, requires support material** under the
floating duct ring bands and the deck bridges · 4 walls, 100% (part is
almost all thin wall anyway). Heated chamber on. 0.4 mm elephant's-foot
chamfer on bed-contact edges.

## Acceptance
- [ ] invariant tests pass
- [ ] motor pads: press M1.4 screws align on real motors (bolt-circle check)
- [ ] battery sliding fit; FC screws bite; props spin free in ducts
- [ ] printed and verified — date, measured result, deviations
