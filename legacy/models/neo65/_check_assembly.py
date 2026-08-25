"""neo65 assembly interference check — run after any geometry change.

Not a printed part (leading underscore keeps it out of test discovery).
Verifies, by boolean intersection, that:
  1. canopy does not touch the frame (pod corners pass ~1 mm from the ducts)
  2. prop swept volumes touch neither frame nor canopy
  3. the battery fits its channel

Run:  .venv/bin/python models/neo65/_check_assembly.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from build123d import Box, Circle, Part, Pos, extrude

from models.neo65.canopy import build as build_canopy
from models.neo65.frame import (
    BATTERY_H_MM,
    BATTERY_W_MM,
    build as build_frame,
)

FC_TOP_WORLD_Z = 5.5   # post top 4.0 + board/grommet ~1.5 (ASSUMED)
PROP_R = 31.0 / 2
BLADE_Z = (14.5, 19.5)  # world z band swept by blades (ASSUMED motor stack)
MOTOR_XY = 65.0 / 2 / math.sqrt(2)


def main() -> None:
    frame = build_frame()
    canopy = Part() + Pos(0, 0, FC_TOP_WORLD_Z) * build_canopy()

    props = Part()
    for sx in (1, -1):
        for sy in (1, -1):
            props += Pos(sx * MOTOR_XY, sy * MOTOR_XY, BLADE_Z[0]) * extrude(
                Circle(PROP_R), BLADE_Z[1] - BLADE_Z[0]
            )

    battery = Pos(0, 0, -0.1 - BATTERY_H_MM / 2) * Box(62, BATTERY_W_MM, BATTERY_H_MM)

    checks = {
        "canopy ∩ frame": (canopy & frame).volume,
        "props ∩ frame": (props & frame).volume,
        "props ∩ canopy": (props & canopy).volume,
        "battery ∩ frame": (battery & frame).volume,
    }
    ok = True
    for name, vol in checks.items():
        good = vol < 1e-6
        ok &= good
        print(f"{'PASS' if good else 'FAIL'}  {name}: {vol:.4f} mm^3")
    if not ok:
        raise SystemExit(1)
    print("assembly clear")


if __name__ == "__main__":
    main()
