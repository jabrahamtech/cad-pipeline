# nasbay — external 3.5" drive tower

A stackable drive tower for a home NAS built on an existing ATX i7-8700K
in a Fractal Meshify. The Meshify cannot hold the drives — the AX1200i PSU
(200 mm) occupies the space the HDD cage needs — so every drive lives out
here, in a hall or cupboard, reached over one external SAS cable.

Expansion is the point: one printed module per drive, stacked and clamped
by four M4 rods.

## Status
| Part | File | Status |
|---|---|---|
| Bay module (1 drive) | `models/nasbay/bay_module.py` | MODELED, v1 exported |
| Base module (PSU, SAS bulkhead, ESP32) | — | not started, needs PSU + ESP32 dims |
| Top module (120 mm fan + lid) | — | not started |
| 2.5"-in-3.5" sled (shucked One Touch) | — | not started, needs the shucked drive measured |

## Printed parts
| Part | Qty | Material | Orientation | Notes |
|---|---|---|---|---|
| `bay_module_v1` | 1 per drive | PETG | Floor flat on the bed, walls up | ~140 g, ~4 h, no support, single nozzle. PLA creeps under sustained compression in a warm cupboard — do not substitute. |

Bay pitch 40 mm; module 120.2 × 161.0 × 43.0 mm.

## Bought parts
| Item | Qty | Why | Rough cost |
|---|---|---|---|
| LSI 9200-8e or 9207-8e HBA (used, IT mode) | 1 | 8 drives over two external SFF-8088 ports; lets the tower sit in another room | £30 |
| SFF-8088 to SFF-8088 cable, 2–3 m | 1–2 | Case to tower | £15 ea |
| SFF-8088 → SFF-8087 bulkhead adapter | 1–2 | Brings the SAS lanes inside the tower | £15 ea |
| SFF-8087 → 4× SATA forward breakout | 1–2 | Fans out to the drives | £12 ea |
| M4 threaded rod | 1 m | Stack clamp. 1 m covers 24 bays; cut to `40 × bays + 25` mm | £4 |
| M4 nut + washer | 8 | Rod ends | £2 |
| 6-32 UNC × 1/4" pan head screw | 4 per drive | Drive side mount. **1/4" only** — see below | £5/100 |
| ATX PSU, 450 W+ | 1 | 12 V + 5 V for the drives. Spare unit is fine | £0–35 |
| 120 mm PWM fan | 1–2 | Front-to-back airflow through the stack | £10 ea |
| ESP32 dev board | 1 | Fan PWM, drive-bay temperature, and PS_ON power sequencing for the tower PSU | £6 |

## Things that will bite you
1. **Never use a 6-32 screw longer than 1/4" (6.35 mm).** SFF-8300 allows
   2.38–3.02 mm of screw into the drive's side hole; the 8.8 mm wall is
   counterbored so a 1/4" screw lands at 2.75 mm. A 5/16" screw would go
   3.9 mm in and can reach the platter casting on a 5-disk drive.
2. **Shucked WD drives and the 3.3 V pin.** WD white-label drives from
   Elements/My Book enclosures treat SATA power pin 3 as a reset line and
   will not spin up on a normal ATX PSU. Tape over pin 3, or power them
   through a Molex→SATA adapter.
3. **The One Touch 5 TB is SMR.** Fine as a backup target or in a mirror;
   painful in a RAIDZ rebuild, where resilver can take days. Do not build a
   parity array around it.
4. **Buy CMR for expansion.** The cheap-per-TB play is shucking a WD
   Elements or My Book 12–18 TB desktop drive — ~£12/TB, CMR helium, versus
   ~£25/TB for the 2.5" One Touch. That is the answer to "cheaper drives
   than the One Touch".
5. **Stagger spin-up.** Eight 3.5" drives starting together pull ~16 A at
   12 V. Enable staggered spin-up on the HBA, or let the ESP32 sequence
   PS_ON so the tower powers before the host boots.

## Assembly
1. Print one bay module per drive.
2. Drop each drive into a module and fix it with four 6-32 × 1/4" screws
   through the counterbored side holes. The drive floats — it should not
   touch the floor.
3. Stack the modules; the Ø4 pins on each wall top locate the module above.
4. Pass four M4 rods down through the corner bores, washer and nut each end,
   and tighten evenly until the stack is rigid. Do not overtighten — the
   joint carries load in compression, the rods only hold it together.
5. Connectors and cables exit the open rear of each bay.
