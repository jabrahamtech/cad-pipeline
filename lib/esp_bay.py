"""The ESP32 carrier bay in base_platter, and the pcb_keeper that clips onto it.

Two parts read these numbers, so they live here - base_platter cuts the
corner fences from them and pcb_keeper grips those fences. A fence that
grows by 0.2 in one file and not the other is a keeper that falls off or
one that will not go on.

Provenance per line. The board is Jonathan's carrier PCB, 2026-09-27.
"""

PCB_W_MM = 50.0          # MEASURED - along X in the base
PCB_L_MM = 70.0          # MEASURED - along Y
PCB_T_MM = 1.3           # MEASURED ("probably 1.3mm")
ESP_H_MM = 30.0          # MEASURED ("about 30") - PCB + ESP32 + cables, both faces

ESP_CLEAR_MM = 1.0       # CHOSEN - insertion play, total, board to fences
FENCE_T_MM = 3.0         # CHOSEN - corner fence wall, both legs of the L
FENCE_LEG_MM = 8.0       # CHOSEN - long leg's run along the board's long edge
LEDGE_MM = 2.5           # CHOSEN - ledge under the corner; also the short leg's run
FENCE_OVER_MM = 3.0      # CHOSEN - fence height above the board's top face

# pcb_keeper - the L clip that pushes down over each corner fence
KEEPER_TONGUE_MM = 1.5   # CHOSEN - how far it laps onto the board's top face.
                         # Keep the outer 1.5 x 2.5 of each board corner clear.
KEEPER_PRELOAD_MM = 0.2  # ASSUMED - modelled interference with the board top,
                         # so it bears on the board whatever the PCB tolerance
