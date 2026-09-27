# pcb_keeper — ESP32 carrier hold-down (print 4)

Script: `models/robotarm/pcb_keeper.py` · gate: `_check_base.py` · export: `plates/plate_bits_white_v1.3mf`

## Interface
| to | contract | source |
|---|---|---|
| base_platter corner fence | 3.0 fence gripped in a 2.85 slot (press 0.15), full 3.0 height | `lib/esp_bay` — base_platter now reads the same numbers |
| carrier PCB top face | tongue 1.5 in, 2.5 along each edge, modelled 0.2 into the board | `KEEPER_TONGUE_MM`, `KEEPER_PRELOAD_MM` (ASSUMED) |

Symmetric about the corner diagonal → one part fits all four corners.

## Cost to the board
The outer **1.5 × 2.5 mm of each board corner, top face**, must be free of parts.

## Gate
`_check_base` places four and requires the three designed overlaps to match the
analytic volumes within ±15 %: press film 16.56 mm³, preload 4.20 mm³, corner
lap in the board envelope 96.6 mm³ (measured: exact). Anything else = FAIL.
