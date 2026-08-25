"""nasbay bay_module — one stackable bay for a single 3.5" SATA drive in an
external drive tower.

Spec: specs/nasbay/bay_module.md. The tower exists because an AX1200i PSU
(200 mm) blocks the HDD cage in the Fractal Meshify, so every drive leaves
the case and lives here, reached over one external SAS cable.

The module is a U-channel: a floor and two side walls. The drive is carried
only by four 6-32 screws through the side walls and floats with air above
and below it, so cooling air crosses both faces. Module N's floor is module
N-1's ceiling, which is why a single module needs no bridges and no top.

Frame: X centred on the drive, Y=0 at the module's front (air intake) face
running back to the open rear where the SATA connectors sit, Z=0 at the
floor underside — the bed face in print.

Print: floor flat on the bed, walls up. Every feature prints upward; the
only bridges are the 6.25 mm register pockets in the bed face. No support,
single nozzle, PETG.

Stack: four M4 threaded rods run the full height of the column, nutted at
the top and bottom, so the whole tower is one pre-tensioned beam and the
load path is wall-top to floor in compression. Printed Ø4 pins register
each module to the one below; the rods only clamp, so their bores are
deliberately loose (0.5 mm) and stacking tolerance cannot bind them.

Expansion: bolt another module on and fit a longer rod. Bay pitch is 44 mm,
so buy 1 m of M4 studding once and cut it again when you add drives.

Hardware per module (BOUGHT): 4x 6-32 UNC x 1/4" pan head (standard PC case
screw — NOT a longer one, see screw_seat_wall).
Hardware per tower (BOUGHT): 4x M4 studding, 44 x bays + 25 mm; 8x M4 nut;
8x M4 washer.
"""

from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Box,
    Cylinder,
    GeomType,
    Part,
    Pos,
    Rot,
    chamfer,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    M3_INSERT_BOSS_WALL_MM,
    MIN_WALL_MM,
    SLIDING_FIT_CLEARANCE_MM,
)

PART_METADATA = {"expected_solids": 1}

# SFF-8301 rev 1.6 / SFF-8300 rev 1.2 — interface constants, not tunables.
SIDE_SCREW_LEN_MM = 6.35        # 6-32 UNC x 1/4", the standard case screw
SIDE_PENETRATION_MIN_MM = 2.38  # SFF-8300 min thread engagement
SIDE_PENETRATION_MAX_MM = 3.02  # SFF-8300 max fastener penetration


def _stadium_y(width: float, length: float, depth: float) -> Part:
    """Rounded-end slot, `width` across X, `length` along Y (capped ends),
    `depth` through Z. Centred on the origin."""
    straight = length - width
    if straight <= 0:
        raise ValueError(f"slot length {length} must exceed width {width}")
    body = Box(width, straight, depth)
    for sy in (-1, 1):
        body += Pos(0, sy * straight / 2, 0) * Cylinder(width / 2, depth)
    return cast(Part, body)


def _stadium_z(width: float, height: float, depth: float) -> Part:
    """Rounded-end slot standing up: `width` along Y, `height` along Z
    (capped ends), `depth` through X. Centred on the origin.

    Capping the top with asemicircle is what keeps the wall vents printable
    with the walls vertical — a flat-topped window would bridge its full
    width unsupported.
    """
    straight = height - width
    if straight <= 0:
        raise ValueError(f"slot height {height} must exceed width {width}")
    body = Box(depth, width, straight)
    for sz in (-1, 1):
        body += Pos(0, 0, sz * straight / 2) * (
            Rot(0, 90, 0) * Cylinder(width / 2, depth)
        )
    return cast(Part, body)


def _vent_centres(span_lo: float, span_hi: float, pitch: float,
                  obstacles: list[float], keepout: float) -> list[float]:
    """Vent positions on a fixed pitch, dropping any that would break into a
    fastener. Placement is a rule, not a layout — the gaps are where the
    screws are."""
    centres = []
    y = span_lo
    while y <= span_hi:
        if all(abs(y - o) >= keepout for o in obstacles):
            centres.append(y)
        y += pitch
    return centres


def build(
    # --- drive envelope (SFF-8301 rev 1.6)
    drive_width: float = 101.60,
    drive_length: float = 147.00,
    drive_height: float = 26.10,
    side_hole_near: float = 28.50,    # A8, from the connector face
    side_hole_far: float = 101.60,    # A9, from the connector face
    side_hole_z: float = 6.35,        # A10, above the drive base
    side_clearance: float = 0.50,     # per side: sliding fit + drive tolerance
    # --- module structure
    floor_thickness: float = 4.0,
    wall_thickness: float = 8.8,      # set by three things at once: >=1.6 mm
                                      # around the Ø5 rod bore, >=2.4 mm around
                                      # the Ø4 register pin, and enough depth to
                                      # counterbore the 6-32 hole down to
                                      # screw_seat_wall
    wall_height: float = 36.0,    # drive_lift + drive + ~5 mm of air
    drive_lift: float = 5.0,          # air gap under the drive
    top_air_gap_min: float = 3.0,     # guard, not geometry
    front_margin: float = 6.0,        # floor ahead of the drive (intake)
    rear_margin: float = 8.0,         # floor behind it (connector shelf)
    # --- stack interface
    stack_rod_inset: float = 20.0,    # rod centres from each module end
    stack_rod_clear_dia: float = 5.0,  # loose on M4 — the rods clamp, the
                                       # pins locate
    pin_inset: float = 30.0,          # register pin centres from each end
    pin_dia: float = 4.0,
    pin_height: float = 3.0,
    # --- drive fasteners
    screw_clear_dia: float = 3.8,     # 6-32 clearance
    screw_cbore_dia: float = 7.0,
    screw_seat_wall: float = 3.6,     # material left at the hole; sets how far
                                      # the screw enters the drive
    # --- ventilation
    wall_vent_width: float = 8.0,
    wall_vent_pitch: float = 11.0,
    wall_vent_keepout: float = 10.5,
    floor_vent_width: float = 8.0,
    floor_vent_count: int = 5,
    floor_vent_pitch_x: float = 20.0,
) -> Part:
    # The drive's own standard is the binding constraint: too short a screw
    # never grips, too long a screw hits the platter casting.
    penetration = SIDE_SCREW_LEN_MM - screw_seat_wall
    if not SIDE_PENETRATION_MIN_MM <= penetration <= SIDE_PENETRATION_MAX_MM:
        raise ValueError(
            f"6-32 x 1/4in screw would penetrate the drive {penetration:.2f} mm "
            f"— SFF-8300 allows {SIDE_PENETRATION_MIN_MM}-"
            f"{SIDE_PENETRATION_MAX_MM} mm; adjust screw_seat_wall to "
            f"{SIDE_SCREW_LEN_MM - SIDE_PENETRATION_MAX_MM:.2f}-"
            f"{SIDE_SCREW_LEN_MM - SIDE_PENETRATION_MIN_MM:.2f} mm"
        )
    if screw_seat_wall >= wall_thickness:
        raise ValueError("screw_seat_wall must be less than wall_thickness")
    rod_wall = (wall_thickness - stack_rod_clear_dia) / 2
    pin_wall = (wall_thickness - pin_dia) / 2
    if pin_wall < M3_INSERT_BOSS_WALL_MM:
        raise ValueError(
            f"register pin leaves {pin_wall:.2f} mm of wall around it — "
            f"thicken wall_thickness or shrink pin_dia"
        )
    if rod_wall < MIN_WALL_MM:
        raise ValueError(
            f"rod bore leaves {rod_wall:.2f} mm of wall — below the "
            f"{MIN_WALL_MM} mm minimum; thicken wall_thickness"
        )
    top_gap = wall_height - drive_lift - drive_height
    if top_gap < top_air_gap_min:
        raise ValueError(
            f"only {top_gap:.1f} mm of air above the drive — raise wall_height"
        )

    cavity_w = drive_width + 2 * side_clearance
    outer_w = cavity_w + 2 * wall_thickness
    depth = front_margin + drive_length + rear_margin
    wall_cl_x = (cavity_w + wall_thickness) / 2       # wall centreline
    wall_out_x = cavity_w / 2 + wall_thickness        # outer face
    wall_top_z = floor_thickness + wall_height
    drive_base_z = floor_thickness + drive_lift
    connector_y = front_margin + drive_length

    rod_ys = [stack_rod_inset, depth - stack_rod_inset]
    pin_ys = [pin_inset, depth - pin_inset]
    screw_ys = [connector_y - side_hole_near, connector_y - side_hole_far]

    # --- phase 1: base — floor, two side walls, and the pins the module
    # above registers on
    body = Pos(0, depth / 2, floor_thickness / 2) * Box(
        outer_w, depth, floor_thickness
    )
    for sx in (-1, 1):
        body += Pos(sx * wall_cl_x, depth / 2, floor_thickness + wall_height / 2) * Box(
            wall_thickness, depth, wall_height
        )
        for py in pin_ys:
            body += Pos(sx * wall_cl_x, py, wall_top_z + pin_height / 2) * Cylinder(
                pin_dia / 2, pin_height
            )
    body = cast(Part, body)

    # --- phase 2: features — stack fasteners, drive screws, ventilation
    for sx in (-1, 1):
        # tie rods pass clean through floor and wall
        for ry in rod_ys:
            body -= Pos(sx * wall_cl_x, ry, wall_top_z / 2) * Cylinder(
                stack_rod_clear_dia / 2, wall_top_z + 2
            )
        # register pockets in the bed face, receiving the pins below
        pocket_d = pin_height + 0.2
        for py in pin_ys:
            body -= Pos(sx * wall_cl_x, py, pocket_d / 2) * Cylinder(
                (pin_dia + SLIDING_FIT_CLEARANCE_MM) / 2, pocket_d
            )

        # 6-32 side screws: through-hole plus an outside counterbore that
        # sets the penetration into the drive
        for sy in screw_ys:
            z = drive_base_z + side_hole_z
            body -= Pos(sx * wall_cl_x, sy, z) * (
                Rot(0, 90, 0) * Cylinder(screw_clear_dia / 2, wall_thickness + 4)
            )
            cbore_len = wall_thickness - screw_seat_wall + 1.0
            cbore_cx = sx * (wall_out_x + 1.0 - cbore_len / 2)
            body -= Pos(cbore_cx, sy, z) * (
                Rot(0, 90, 0) * Cylinder(screw_cbore_dia / 2, cbore_len)
            )

    vent_h = wall_height - 11.0        # 4 mm rail at the floor, 7 mm at the top
    vent_cz = floor_thickness + 4.0 + vent_h / 2
    obstacles = rod_ys + screw_ys
    for vy in _vent_centres(
        stack_rod_inset - 6.0, depth - stack_rod_inset + 6.0,
        wall_vent_pitch, obstacles, wall_vent_keepout,
    ):
        for sx in (-1, 1):
            body -= Pos(sx * wall_cl_x, vy, vent_cz) * _stadium_z(
                wall_vent_width, vent_h, wall_thickness + 4
            )

    floor_vent_len = depth - 2 * stack_rod_inset - 15.0
    for i in range(floor_vent_count):
        vx = (i - (floor_vent_count - 1) / 2) * floor_vent_pitch_x
        body -= Pos(vx, depth / 2, floor_thickness / 2) * _stadium_y(
            floor_vent_width, floor_vent_len, floor_thickness + 2
        )
    body = cast(Part, body)

    # --- phase 3: finish — lead-in on the pin tops so a module drops onto
    # the one below, elephant's foot on every bed-face edge
    body = chamfer(
        body.edges()
        .group_by(Axis.Z)[-1]
        .filter_by(
            lambda e: e.geom_type == GeomType.CIRCLE
            and abs(e.radius - pin_dia / 2) < 0.01
        ),
        0.6,
    )
    body = chamfer(body.edges().group_by(Axis.Z)[0], ELEPHANT_FOOT_CHAMFER_MM)
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "nasbay"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "bay_module_v1.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "bay_module_v1.3mf"))
    bb = part.bounding_box()
    print(
        f"volume {part.volume / 1000:.1f} cm^3, "
        f"mass(PETG solid) {part.volume / 1000 * 1.27:.0f} g, "
        f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
        f"solids {len(part.solids())}, valid {part.is_valid}"
    )
