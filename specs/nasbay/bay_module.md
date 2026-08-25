# nasbay bay_module — spec

Project: `models/nasbay/bay_module.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
One stackable bay for a single 3.5" SATA hard drive, in an external
drive tower that sits in a hall/closet and connects to the main machine
(ATX, i7-8700K, Fractal Meshify) over a single external SAS cable.

The Meshify cannot hold the drives: the AX1200i PSU (200 mm) occupies the
space the HDD cage needs. So *all* drives leave the case and live in this
tower. Expansion = print one more module and bolt it on top.

Each module is a U-channel: a floor plus two side walls. The drive is held
only by four 6-32 side screws and floats with an air gap above and below,
so cooling air passes over both faces. Module N's floor is module N-1's
ceiling — the stack closes itself, which is why nothing in a single module
needs a bridge or support.

Not in this part (separate parts, later): base module (PSU + SFF-8088
bulkhead + ESP32 controller), top module (120 mm fan + lid), 2.5"-in-3.5"
sled for the shucked One Touch drive.

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| 3.5" drive width (A3) | 101.60 mm | DATASHEET — SFF-8301 rev 1.6 |
| 3.5" drive length (A2) | 147.00 mm max | DATASHEET — SFF-8301 rev 1.6 |
| 3.5" drive height (A1) | 26.10 mm max | DATASHEET — SFF-8301 rev 1.6 |
| Dimensional tolerance (A11) | ±0.25 mm | DATASHEET — SFF-8301 rev 1.6 |
| Side hole 1 from connector face (A8) | 28.50 ±0.50 mm | DATASHEET — SFF-8301 rev 1.6 |
| Side hole 2 from connector face (A9) | 101.60 ±0.25 mm | DATASHEET — SFF-8301 rev 1.6 |
| Side hole height above drive base (A10) | 6.35 ±0.25 mm | DATASHEET — SFF-8301 rev 1.6 |
| Side hole thread | 6-32 UNC-2B | DATASHEET — SFF-8300 rev 1.2 |
| Side screw min thread engagement | 2.38 mm | DATASHEET — SFF-8300 rev 1.2 |
| Side screw MAX penetration | 3.02 mm | DATASHEET — SFF-8300 rev 1.2 |
| Drive side clearance (per side) | 0.50 mm = sliding fit 0.25 + drive tol 0.25 | design rule |
| Stack fastener | M4 threaded rod through Ø5.0 bores | design choice |
| Register pin/pocket fit | Ø4.0 pin, 0.25 mm diametral (sliding) | design rule |
| Pin surround / min wall | 2.4 mm / 1.6 mm | design rule |
| Shucked One Touch (2.5", 15 mm) | 100.45 × 69.85 × 15.0 mm | ASSUMED — SFF-8201; needs an adapter sled, separate part |

The 6-32 penetration window is the tightest constraint in the part. Only
2.38–3.02 mm of screw may enter the drive. With a standard 6-32 × 1/4"
(6.35 mm) case screw, the material left at the hole must be 3.33–3.97 mm.
`screw_seat_wall = 3.6 mm` sits in the middle of that window, produced by
counterboring the 8.8 mm side wall from the outside. `build()` raises if a
parameter change pushes penetration outside the window.

## Loads & environment
Static indoor, hall/closet. Each drive ~700 g; a full 8-high stack loads
the bottom module with ~6 kg through the wall tops in pure compression.
Occasional handling load when the tower is carried. Rotational vibration
from the drives themselves. Ambient up to ~30 °C in a closed cupboard;
PLA creeps under sustained compression at that temperature, PETG does not.

## Print plan
PETG. Floor flat on the bed, walls pointing up. Every feature then prints
upward: the only overhangs are the Ø4.25 register pockets in the bed face
(4.25 mm bridge), the horizontal 6-32 bores and counterbores (self-supporting
arcs), and the wall vents — which are stadium-shaped precisely so their tops
are semicircular arches rather than a 25 mm flat bridge. No support material,
single nozzle. Compressive stack load runs along the wall Z axis, across
layers, but an 8-high stack loads the bottom module at ~0.06 MPa — three
orders of magnitude below PETG's layer-adhesion limit. 4 walls, 25 % infill.
~4 h and ~140 g per bay.

## Design sketch
- Floor 120.2 × 161 × 4.0 mm with 5 stadium vent slots for convection when
  the fan is off.
- Two side walls 8.8 mm thick, 36 mm tall, pierced by 6 stadium vents per
  wall placed automatically wherever they clear a fastener — the gaps in
  the grille are where the screws are, which is why the pattern is a rule
  in code and not a layout.
- Drive floats 5.0 mm above the floor with 4.9 mm of air above it, so
  front-to-back airflow crosses both faces.
- Stack: 4 × M4 threaded rods run the full height of the tower, nutted top
  and bottom, making the column one pre-tensioned beam. Load path is wall
  top → floor in compression. Ø4.0 printed pins (2 per wall) locate each
  module; the Ø5.0 rod bores are deliberately loose so accumulated stacking
  tolerance over 8+ modules cannot bind the rods.
- Bay pitch 40.0 mm. Module bbox 120.2 × 161.0 × 43.0 mm — comfortably
  inside the X2D single-nozzle envelope. 8 bays = 320 mm of stack, plus
  base and fan modules.

## Verified numerically (v1)
| Check | Result |
|---|---|
| Material inside the drive envelope | 0.000 mm³ |
| Material in the slide-in path | 0.000 mm³ |
| 6-32 × 1/4" penetration into drive | 2.75 mm (SFF-8300 window 2.38–3.02) |
| Counterbore Ø7.0 × 5.2 clear for the pan head | yes, both holes |
| Thinnest wall (Ø5 rod bore in 8.8 wall) | 1.90 mm (min 1.6) |
| Solid volume / mass | 138.8 cm³ / 176 g PETG solid, ~140 g as printed |
| Guards fire on bad params | screw_seat_wall, wall_thickness, drive_lift ✓ |

## Acceptance
- [ ] invariant tests pass
- [ ] fits the real object (drive slides in with clearance; 6-32 screws
      engage without bottoming; two modules stack and bolt square)
- [ ] printed and verified — date, measured result, deviations

On ACCEPTED: record measured fit deviations in `calibration/`.
