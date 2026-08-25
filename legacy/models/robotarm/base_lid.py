"""robotarm base_lid — flat lid that closes the electronics bay, recessed
flush into the platter rim.

Spec: specs/robotarm/base_lid.md. Frame: LOCAL — the lid's underside (which
lands on the platter's shelf at global Z_LID) is z = 0, Z up.

It is a plain disc on purpose: the rounded look comes from the platter rim,
and a flat lid prints in ~20 min with no support and stays stiff because the
turret_cap clamps its middle. The three large holes clear the platter's
cap-bolt bosses, which pass THROUGH the lid so the cap bolts land on the
column, not on a 3 mm lid.

Print: flat, either face down. PETG, 15 % infill, 3 walls.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Box,
    Cylinder,
    GeomType,
    Part,
    Pos,
    Rotation,
    chamfer,
)

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    CAP_BOLT_AZ,
    CAP_BOLT_R,
    COLUMN_OUTER_X,
    COLUMN_OUTER_Y,
    COLUMN_Y,
    LID_DIA,
    LID_SCREW_AZ,
    LID_SCREW_R,
    LID_T,
)

PART_METADATA = {"expected_solids": 1}

BOSS_CLEAR_DIA = 9.5        # slips over the platter's Ø8.8 cap-bolt bosses
M3_CLEAR_DIA = 3.4
M3_HEAD_DIA = 6.5
VENT_COUNT = 12
VENT_DIA = 4.0
VENT_R = 62.0


def _ring(radius: float, count: int, start: float = 0.0) -> list[tuple[float, float]]:
    out = []
    for i in range(count):
        p = Rotation(0, 0, start + i * 360.0 / count) * Pos(radius, 0, 0)
        out.append((p.position.X, p.position.Y))
    return out


def build(
    lid_dia: float = LID_DIA,
    lid_thickness: float = LID_T,
    column_clearance: float = 1.5,
    boss_clear_dia: float = BOSS_CLEAR_DIA,
    screw_clear_dia: float = M3_CLEAR_DIA,
    screw_head_dia: float = M3_HEAD_DIA,
    counterbore: float = 1.2,
    vent_dia: float = VENT_DIA,
    vent_count: int = VENT_COUNT,
    vent_r: float = VENT_R,
) -> Part:
    # --- phase 1: base shape
    body = cast(Part, Pos(0, 0, lid_thickness / 2)
                * Cylinder(lid_dia / 2, lid_thickness))

    # --- phase 2: features — column opening, boss clearances, screws, vents
    through = lid_thickness + 2.0
    # rectangular, not round, and centred on the column: the MG995 shaft sits
    # 10.35 mm off the case centre, so a hole centred on the base axis would
    # have to be Ø75 to clear the column's far corners
    cuts: list[Part] = [
        cast(Part, Pos(0, COLUMN_Y, lid_thickness / 2)
             * Box(COLUMN_OUTER_X + column_clearance,
                   COLUMN_OUTER_Y + column_clearance, through))
    ]
    for az in CAP_BOLT_AZ:
        p = Rotation(0, 0, az) * Pos(CAP_BOLT_R, 0, 0)
        cuts.append(cast(Part, Pos(p.position.X, p.position.Y,
                                   lid_thickness / 2)
                         * Cylinder(boss_clear_dia / 2, through)))
    for az in LID_SCREW_AZ:
        p = Rotation(0, 0, az) * Pos(LID_SCREW_R, 0, 0)
        x, y = p.position.X, p.position.Y
        cuts.append(cast(Part, Pos(x, y, lid_thickness / 2)
                         * Cylinder(screw_clear_dia / 2, through)))
        cuts.append(cast(Part, Pos(x, y, lid_thickness - counterbore / 2)
                         * Cylinder(screw_head_dia / 2, counterbore)))
    for x, y in _ring(vent_r, vent_count, start=15.0):
        cuts.append(cast(Part, Pos(x, y, lid_thickness / 2)
                         * Cylinder(vent_dia / 2, through)))
    body = cast(Part, body - cuts)

    # --- phase 3: finish — elephant's foot on the bed face
    bed = [
        e for e in body.edges().filter_by(GeomType.CIRCLE)
        if abs(e.center().Z) < 0.01
        and abs(e.radius - lid_dia / 2) < 0.01  # type: ignore[attr-defined]
    ]
    if bed:
        body = cast(Part, chamfer(bed, ELEPHANT_FOOT_CHAMFER_MM))
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"base_lid: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.0f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
