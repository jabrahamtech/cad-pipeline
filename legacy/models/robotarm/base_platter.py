"""robotarm base_platter — rounded base drum: electronics bay, MG995 column,
rim I/O (toggle switch, DC cable, LEDs).

Spec: specs/robotarm/base_platter.md. Frame: models/robotarm/_frame.py — the
origin is the centre of this part's bottom face, Z up, MG995 shaft on +Z.

Layout logic: the MG995 column is a RECTANGLE (27.95 x 48.95), not a round
turret, because the 85.5 x 55.5 breadboard has to clear it inside a sane base
diameter. With the case long axis along Y the column is only ~14 mm wide in
+X, so the breadboard sits tangentially at x >= 14.5 and its far corners land
at r = 82.0, inside the 84.0 mm bay wall. The wide roller race that the arm
turns on is a separate part (turret_cap) that bolts to the column top —
flaring 28 mm to 104 mm inside one part would mean a >50 deg overhang.

Print: flat on the bottom face, bay opening up. No support: the only internal
overhangs are the boss tops and the rim holes, all self-supporting or short
bridges. PETG, 25 % infill, 4 walls (mass sits low, which is what keeps an
extended arm from tipping it).
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Align,
    Box,
    Cone,
    Cylinder,
    GeomType,
    Part,
    Pos,
    Rotation,
    chamfer,
    fillet,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    M3_INSERT_BOSS_WALL_MM,
    M3_INSERT_HOLE_DIA_MM,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    BAY_H,
    BREADBOARD,
    BREADBOARD_X0,
    CAP_BOLT_AZ,
    CAP_BOLT_R,
    COLUMN_INNER_X,
    COLUMN_INNER_Y,
    COLUMN_OUTER_X,
    COLUMN_OUTER_Y,
    COLUMN_Y,
    DC_CABLE_DIA,
    FLOOR_T,
    INNER_R,
    LEAD_RELIEF_D,
    LEAD_RELIEF_W,
    LED_HOLE_DIA,
    LID_SCREW_AZ,
    LID_SCREW_R,
    LID_WALL,
    OUTER_DIA,
    SWITCH_HOLE_DIA,
    WALL,
    Z_LID,
    Z_RIM,
)

PART_METADATA = {"expected_solids": 1}

BOSS_DIA = M3_INSERT_HOLE_DIA_MM + 2 * M3_INSERT_BOSS_WALL_MM   # 8.8
INSERT_DEPTH = 8.0

# rim I/O azimuths (deg): all on the -X half, away from the breadboard
SWITCH_AZ = 180.0
CABLE_AZ = 205.0
LED_AZ = (20.0, 340.0)


def _radial(az: float, radius: float, z: float, dia: float,
            length: float) -> Part:
    """Cylinder lying along the radius at `az`, centred at `radius`."""
    return cast(
        Part,
        Rotation(0, 0, az) * Pos(radius, 0, z) * Rotation(0, 90, 0)
        * Cylinder(dia / 2, length),
    )


def _post(x: float, y: float, size: tuple[float, float], height: float) -> Part:
    return cast(
        Part,
        Pos(x, y, FLOOR_T + height / 2) * Box(size[0], size[1], height),
    )


def build(
    outer_dia: float = OUTER_DIA,
    wall: float = WALL,
    floor_thickness: float = FLOOR_T,
    rim_height: float = Z_RIM,
    lid_wall: float = LID_WALL,
    lid_shelf_z: float = Z_LID,
    boss_dia: float = BOSS_DIA,
    insert_hole_dia: float = M3_INSERT_HOLE_DIA_MM,
    board_post: float = 6.0,
    board_post_h: float = 12.0,
    switch_dia: float = SWITCH_HOLE_DIA,
    cable_dia: float = DC_CABLE_DIA,
    led_dia: float = LED_HOLE_DIA,
    rim_fillet: float = 1.2,
    plinth_flare: float = 5.0,           # extra radius at the very bottom
    plinth_height: float = 10.0,
) -> Part:
    outer_r = outer_dia / 2
    inner_r = outer_r - wall

    # --- phase 1: base shape — drum on a flared plinth, bay cavity, lid
    # recess. The plinth is a cone that NARROWS going up, so it prints with
    # no overhang at all, and it visually plants the base instead of leaving
    # it looking like a tub.
    body = cast(Part, Pos(0, 0, rim_height / 2) * Cylinder(outer_r, rim_height))
    if plinth_flare > 0:
        body = cast(Part, body + Cone(
            outer_r + plinth_flare, outer_r, plinth_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN)))
    bay_h = rim_height - floor_thickness
    body = cast(Part, body - Pos(0, 0, floor_thickness + bay_h / 2)
                * Cylinder(inner_r, bay_h))
    lid_recess_h = rim_height - lid_shelf_z
    body = cast(Part, body - Pos(0, 0, lid_shelf_z + lid_recess_h / 2)
                * Cylinder(outer_r - lid_wall, lid_recess_h))

    # --- phase 2: MG995 column, hollow, floor to rim; wired out to the bay
    body = cast(Part, body + Pos(0, COLUMN_Y, rim_height / 2)
                * Box(COLUMN_OUTER_X, COLUMN_OUTER_Y, rim_height))
    cavity_h = rim_height - floor_thickness
    body = cast(Part, body - Pos(0, COLUMN_Y, floor_thickness + cavity_h / 2)
                * Box(COLUMN_INNER_X, COLUMN_INNER_Y, cavity_h))
    # the servo's lead runs down the side of the case, so relieve both side
    # faces of the column for its full depth
    for side in (-1.0, 1.0):
        body = cast(Part, body - Pos(
            side * (COLUMN_INNER_X / 2 + LEAD_RELIEF_D / 2), COLUMN_Y,
            floor_thickness + cavity_h / 2)
            * Box(LEAD_RELIEF_D + 0.02, LEAD_RELIEF_W, cavity_h))
    wire_slot = (14.0, 8.0)
    body = cast(Part, body - Pos(-COLUMN_OUTER_X / 2, COLUMN_Y,
                                 floor_thickness + 1.0 + wire_slot[1] / 2)
                * Box(COLUMN_OUTER_X, wire_slot[0], wire_slot[1]))

    # --- phase 3: features — bosses for the turret cap and the lid
    bosses: list[Part] = []
    holes: list[Part] = []
    for az in CAP_BOLT_AZ:
        p = Rotation(0, 0, az) * Pos(CAP_BOLT_R, 0, 0)
        x, y = p.position.X, p.position.Y
        h = rim_height - floor_thickness
        bosses.append(cast(Part, Pos(x, y, floor_thickness + h / 2)
                           * Cylinder(boss_dia / 2, h)))
        bosses.append(cast(Part, Pos(x, y, floor_thickness + 2.5)
                           * Cylinder(boss_dia / 2 + 2.5, 5.0)))
        holes.append(cast(Part, Pos(x, y, rim_height - INSERT_DEPTH / 2)
                          * Cylinder(insert_hole_dia / 2, INSERT_DEPTH)))
    for az in LID_SCREW_AZ:
        p = Rotation(0, 0, az) * Pos(LID_SCREW_R, 0, 0)
        x, y = p.position.X, p.position.Y
        h = lid_shelf_z - floor_thickness
        bosses.append(cast(Part, Pos(x, y, floor_thickness + h / 2)
                           * Cylinder(boss_dia / 2, h)))
        holes.append(cast(Part, Pos(x, y, lid_shelf_z - INSERT_DEPTH / 2)
                          * Cylinder(insert_hole_dia / 2, INSERT_DEPTH)))
    body = cast(Part, body + bosses)

    # --- phase 3b: breadboard retention — the bay wall stops it at the far
    # edge (r 82.0 vs 84.0), so only the sides and the inboard edge need posts
    bw, bl = BREADBOARD[0], BREADBOARD[1]
    side_y = bl / 2 + board_post / 2 + 0.5
    for x in (BREADBOARD_X0 + bw * 0.3, BREADBOARD_X0 + bw * 0.85):
        for sy in (-1.0, 1.0):
            body = cast(Part, body + _post(x, sy * side_y,
                                           (board_post, board_post),
                                           board_post_h))
    # no inboard post: the column's own outer wall stands 0.5 mm from the
    # breadboard's near edge and stops it there

    # --- phase 4: rim I/O — switch, DC cable + strain-relief zip ties, LEDs
    pierce = wall * 4
    holes.append(_radial(SWITCH_AZ, outer_r - wall / 2,
                         floor_thickness + BAY_H / 2, switch_dia, pierce))
    holes.append(_radial(CABLE_AZ, outer_r - wall / 2, floor_thickness + 7.0,
                         cable_dia, pierce))
    for az in LED_AZ:
        holes.append(_radial(az, outer_r - wall / 2,
                             floor_thickness + BAY_H * 0.75, led_dia, pierce))
    for r in (INNER_R - 14.0, INNER_R - 22.0):
        holes.append(cast(Part, Rotation(0, 0, CABLE_AZ)
                          * Pos(r, 0, floor_thickness / 2)
                          * Box(3.2, 1.8, floor_thickness * 2)))
    body = cast(Part, body - holes)

    # --- phase 5: finish — round the rim crown, chamfer the bed edge
    crown = [
        e for e in body.edges().filter_by(GeomType.CIRCLE)
        if abs(e.center().Z - rim_height) < 0.01
        and e.radius > outer_r - lid_wall + 0.5  # type: ignore[attr-defined]
    ]
    if crown:
        body = cast(Part, fillet(crown, rim_fillet))
    bed = [
        e for e in body.edges().filter_by(GeomType.CIRCLE)
        if abs(e.center().Z) < 0.01
        and e.radius > outer_r - 0.5  # type: ignore[attr-defined]
    ]
    if bed:
        body = cast(Part, chamfer(bed, ELEPHANT_FOOT_CHAMFER_MM))
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"base_platter: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.0f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
