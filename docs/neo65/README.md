# neo65 — half-Neo-scale autonomous lab follow-cam whoop

A 65 mm-wheelbase ducted 1S whoop (~84 × 84 mm footprint, ≈ half a DJI Neo's
130 × 157 mm) that streams FPV video to a lab PC; the PC runs person
tracking and flies it via ELRS/MAVLink (**offboard autonomy** — onboard
person-tracking compute does not exist at this weight class). The FPV
camera is the recording camera; the PC records the stream.

Status: MODELED — not yet printed. Verify all ASSUMED dims against real
parts (calipers) before printing: 0802 bolt circle, motor stack height /
prop plane, FC USB height, C03 lens position.

## Printed parts
| Part | File | Material | Mass | Orientation |
|---|---|---|---|---|
| frame | `exports/neo65/frame_v1.*` | ASA | 14.0 g | flat, rib-feet/rail plane on bed; **support material** under duct ring bands + deck bridges (dual nozzle) |
| canopy | `exports/neo65/canopy_v1.*` | ASA | 2.7 g | legs down; **support material** under roof + pod (dual nozzle) |

Print: heated chamber on, 4 walls, ~100 % (thin-shell parts), 0.4 mm
elephant's-foot chamfer modeled in.

## Bought parts (BOM)
| Item | Spec | ~Mass |
|---|---|---|
| Motors ×4 | BetaFPV 0802SE 19500KV (1S), M1.4×4 screws included | 7.6 g |
| Props ×4 | Gemfan 1219 / 31 mm, 1.0 mm shaft | 1.6 g |
| FC | whoop AIO, 25.5×25.5 M2: F4 1S 5A ESC + ELRS RX + analog VTX (e.g. BetaFPV F4 1S 5A AIO) | 4.6 g |
| Camera | BetaFPV C03 (11 × 14.1 × 13.5 mm) | 1.5 g |
| Battery | BetaFPV BT2.0 1S 450 mAh (62 × 15.5 × 6.7 mm) | 12.7 g |
| Hardware | 4× long M2 (canopy+FC), grommets, 12 mm strap (optional) | 2.5 g |

**AUW ≈ 47 g** · thrust ≈ 120 g → T/W ≈ 2.5 · expect ~3–4 min per pack.

## Assembly order
1. Motors into pads from below (heads in the counterbores), wires along arms.
2. Battery test-slide in the under-deck channel (from the rear, lips hold it).
3. FC on the 2 mm posts; camera into the canopy pod (press fit, lens in window).
4. Canopy legs over the FC holes; 4 long M2 through leg → grommet → post.

## Offboard tracking loop (software, not in this repo)
C03 → analog VTX → USB receiver on PC → person tracker (e.g. YOLO) →
ELRS TX module (or MAVLink over wifi with a compatible FC) → drone.
Anyone else in the lab should be told it records.
