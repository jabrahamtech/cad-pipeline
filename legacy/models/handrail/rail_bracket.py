"""handrail rail-bracket — replacement wall bracket for an oval wardrobe rail.

Spec: specs/handrail/rail-bracket.md. Wall plate + stem + closed obround
saddle the rail slides through. Plate, stem and saddle share one flush side
face (v5): the part prints lying flat on that face, so layers lie in the
vertical/projection plane (stem bending stays within layers) and no support
material is needed.

Frame: X along rail, Y vertical, Z projection away from wall (wall at z=0).
"""

from pathlib import Path
from typing import cast

from build123d import (
    Align,
    Axis,
    Circle,
    Cone,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Sketch,
    chamfer,
    extrude,
    fillet,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    SLIDING_FIT_CLEARANCE_MM,
)

PART_METADATA = {"expected_solids": 1}

# Interface constants from the spec — not tunables.
RAIL_W_MM = 16.0          # rail width, horizontal (MEASURED)
RAIL_H_MM = 30.0          # rail long dimension (user correction, was 35)
RAIL_CORNER_R_MM = 7.0    # rail end-arc radius (user, v4 fit correction)
PROJECTION_MM = 74.0      # wall face -> bracket tip (MEASURED)
SCREW_HOLE_DIA_MM = 4.5   # thru hole for 4 mm countersunk wood screw
SCREW_CS_DIA_MM = 9.0     # countersink surface diameter, 90 deg cone


def bore_dims(rail_long_axis: str = "horizontal") -> tuple[float, float, float]:
    """Saddle bore (height_y, depth_z, corner_r): rail + sliding clearance.

    Shared with the saddle fit gauge so bore geometry cannot drift between
    the bracket and its prototype.
    """
    if rail_long_axis not in ("vertical", "horizontal"):
        raise ValueError("rail_long_axis must be 'vertical' or 'horizontal'")
    rail_y, rail_z = ((RAIL_H_MM, RAIL_W_MM) if rail_long_axis == "vertical"
                      else (RAIL_W_MM, RAIL_H_MM))
    return (
        rail_y + 2 * SLIDING_FIT_CLEARANCE_MM,
        rail_z + 2 * SLIDING_FIT_CLEARANCE_MM,
        RAIL_CORNER_R_MM + SLIDING_FIT_CLEARANCE_MM,
    )


def build(
    plate_height: float = 60.0,
    plate_width: float = 26.0,        # along the rail
    plate_thickness: float = 6.0,
    plate_corner_r: float = 8.0,
    screw_spacing: float = 40.0,      # vertical, centre to centre
    stem_height: float = 14.0,
    ring_depth: float = 12.0,         # stem + saddle width along the rail
    ring_wall: float = 4.0,
    junction_fillet: float = 4.0,     # at the plate root (highest stress)
    ring_fillet: float = 7.0,         # neck arc radius, stem into ring
    rail_long_axis: str = "horizontal",  # rail 35 mm axis: "vertical" | "horizontal"
    projection_align: str = "flush",  # stem+ring on plate: "flush" | "center"
) -> Part:
    if projection_align not in ("flush", "center"):
        raise ValueError("projection_align must be 'flush' or 'center'")
    bore_y, bore_z, bore_r = bore_dims(rail_long_axis)
    ring_out_y = bore_y + 2 * ring_wall
    ring_out_z = bore_z + 2 * ring_wall
    # outer corner radius follows the bore; the neck arc in the 2D profile
    # may land tangent on this corner arc, so it needs no stem-height guard
    ring_out_r = bore_r + ring_wall
    ring_z = PROJECTION_MM - ring_out_z / 2              # ring centre, Z
    flush_x = -plate_width / 2
    stem_x0 = flush_x if projection_align == "flush" else -ring_depth / 2
    stem_x1 = stem_x0 + ring_depth
    stem_z0 = plate_thickness

    # --- phase 1: base — plate, plus stem + saddle ring as ONE extruded YZ
    # profile (both are ring_depth deep), so the stem-to-ring neck is a
    # designed tangent arc in the profile, not a 3D edge fillet
    body = extrude(RectangleRounded(plate_width, plate_height, plate_corner_r),
                   plate_thickness)
    neck_2d = cast(
        Sketch,
        Pos(0, ring_z) * RectangleRounded(ring_out_y, ring_out_z, ring_out_r)
        + Pos(0, (stem_z0 + ring_z) / 2)
        * Rectangle(stem_height, ring_z - stem_z0),
    )
    neck_vertices = neck_2d.vertices().filter_by(
        lambda v: abs(abs(v.X) - stem_height / 2) < 0.01 and v.Y > stem_z0 + 1
    )
    neck_2d = cast(Sketch, fillet(neck_vertices, ring_fillet))
    profile = cast(
        Sketch,
        neck_2d - Pos(0, ring_z) * RectangleRounded(bore_y, bore_z, bore_r),
    )
    body += Pos(stem_x0, 0, 0) * extrude(Plane.YZ * profile, ring_depth)

    # --- phase 2: features — screw holes + countersinks (heads face away
    # from the wall, on the z = plate_thickness face)
    cs_depth = (SCREW_CS_DIA_MM - SCREW_HOLE_DIA_MM) / 2   # 90 deg cone
    for sy in (1, -1):
        y = sy * screw_spacing / 2
        body -= Pos(0, y) * extrude(Circle(SCREW_HOLE_DIA_MM / 2),
                                    plate_thickness)
        body -= Pos(0, y, plate_thickness - cs_depth) * Cone(
            SCREW_HOLE_DIA_MM / 2,
            SCREW_CS_DIA_MM / 2,
            cs_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # --- phase 3: finish — plate-root fillet, then elephant's foot on the
    # bed face (x = flush_x). Junction edges surround the stem at z = stem_z0:
    # along X at the stem sides, along Y at the stem faces (a flush stem face
    # is coplanar with the plate edge, so that Y edge simply doesn't exist).
    plate_junction = [
        e for e in body.edges().filter_by(Axis.X)
        if abs(e.center().Z - stem_z0) < 0.01
        and abs(abs(e.center().Y) - stem_height / 2) < 0.01
        and stem_x0 + 0.1 < e.center().X < stem_x1 - 0.1 + 1e-6
    ]
    plate_junction += [
        e for e in body.edges().filter_by(Axis.Y)
        if abs(e.center().Z - stem_z0) < 0.01
        and min(abs(e.center().X - stem_x0), abs(e.center().X - stem_x1)) < 0.01
        and abs(e.center().Y) < stem_height / 2
    ]
    body = fillet(plate_junction, junction_fillet)

    bed_edges = body.edges().group_by(Axis.X)[0]
    body = chamfer(bed_edges, ELEPHANT_FOOT_CHAMFER_MM)

    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "handrail"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "rail_bracket_v6.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "rail_bracket_v6.3mf"))
    bb = part.bounding_box()
    print(f"volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
