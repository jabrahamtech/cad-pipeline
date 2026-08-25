"""neo65 canopy — camera pod + FC cover, mounts on the FC screws.

Spec: specs/neo65/canopy.md. Origin shares the frame's XY center; z = 0 is
the FC-top mounting plane (top of board/grommets). Holds the C03 camera at
a fixed uptilt in a front pod. Pod width and front corners are prop-limited:
the front duct bores pass within ~1 mm of the pod — verify clearance with
models/neo65/check_assembly.py before changing pod geometry.
Printed legs-down; roof and pod need support material.
"""

import math
from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Box,
    Circle,
    Part,
    Pos,
    Rectangle,
    Rot,
    Sketch,
    chamfer,
    extrude,
)

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM, PRESS_FIT_CLEARANCE_MM

PART_METADATA = {"expected_solids": 1, "needs_support_material": True}

# Interface constants from the spec — not tunables.
FC_HOLE_GRID_MM = 25.5      # whoop AIO standard
CAM_W_MM = 14.1             # BetaFPV C03 body: 11 x 14.1 x 13.5
CAM_D_MM = 11.0
CAM_H_MM = 13.5


def build(
    leg_dia: float = 5.0,
    leg_hole_dia: float = 2.4,          # M2 clearance
    roof_underside_z: float = 6.5,      # clears FC USB / VTX (ASSUMED)
    roof_thickness: float = 1.6,
    roof_size: float = 28.0,
    roof_corner_cut: float = 20.0,      # octagon: |x|+|y| <= this (prop keep-out)
    wall_thickness: float = 1.6,
    cam_tilt_deg: float = 15.0,
    cam_lens_window_dia: float = 10.5,  # ASSUMED lens barrel position/size
    pod_rear_x: float = 3.0,
    pod_floor_z: float = 1.0,           # floats above the FC board edge
    pod_corner_chamfer: float = 3.0,    # prop/duct keep-out — do not shrink
) -> Part:
    fc_half = FC_HOLE_GRID_MM / 2
    roof_top = roof_underside_z + roof_thickness

    # --- phase 1: legs + octagonal roof
    octagon = cast(
        Sketch,
        Rectangle(roof_size, roof_size)
        & Rot(Z=45) * Rectangle(roof_corner_cut * math.sqrt(2), roof_corner_cut * math.sqrt(2)),
    )
    body = Pos(0, 0, roof_underside_z) * extrude(octagon, roof_thickness)
    leg_r = math.hypot(fc_half, fc_half)
    for hx in (fc_half, -fc_half):
        for hy in (fc_half, -fc_half):
            body += Pos(hx, hy) * extrude(Circle(leg_dia / 2), roof_top)
            # spoke joining the leg to the octagon roof (stays below the props)
            spoke = cast(
                Sketch,
                Rot(Z=math.degrees(math.atan2(hy, hx)))
                * Pos((leg_r + roof_corner_cut / math.sqrt(2)) / 2, 0)
                * Rectangle(leg_r - roof_corner_cut / math.sqrt(2) + leg_dia, 6.0),
            )
            body += Pos(0, 0, roof_underside_z) * extrude(spoke, roof_thickness)

    # --- phase 1: camera pod, tilted up, floor above the FC front edge.
    # Local pod frame: x rear->front, z floor->top; rotated about Y for uptilt.
    pocket_w = CAM_W_MM + PRESS_FIT_CLEARANCE_MM
    pod_w = pocket_w + 2 * wall_thickness
    pod_d = CAM_D_MM + 0.3 + wall_thickness          # front wall only; rear open
    pod_h = wall_thickness + CAM_H_MM + 0.3
    place = Pos(pod_rear_x, 0, pod_floor_z) * Rot(Y=-cam_tilt_deg)

    pod = Pos(pod_d / 2, 0, pod_h / 2) * Box(pod_d, pod_w, pod_h)
    # pocket: open at rear (extends past x=0) and open top
    pod -= Pos((pod_d - wall_thickness) / 2 - 5, 0, wall_thickness + (pod_h + 5) / 2) * Box(
        pod_d - wall_thickness + 10, pocket_w, pod_h + 5
    )
    # lens window through the front wall
    lens_z = wall_thickness + CAM_H_MM / 2
    pod -= Pos(pod_d - wall_thickness / 2, 0, lens_z) * Rot(Y=90) * extrude(
        Circle(cam_lens_window_dia / 2), wall_thickness * 2, both=True
    )
    front_verticals = [
        e
        for e in pod.edges().filter_by(Axis.Z)
        if abs(e.center().X - pod_d) < wall_thickness and abs(abs(e.center().Y) - pod_w / 2) < 0.1
    ]
    pod = chamfer(front_verticals, pod_corner_chamfer)
    body += place * pod

    # Corner notches: the front duct ring walls sweep through the pod's
    # upper corners (world z 14-16.2). Camera body and lens clear; only
    # pod shell corners above z 8 must go — see _check_assembly.py.
    for sy in (1, -1):
        body -= Pos(17.6, sy * 10.6, 15.0) * Box(15, 8.8, 14)

    # --- phase 2: leg holes
    for hx in (fc_half, -fc_half):
        for hy in (fc_half, -fc_half):
            body -= Pos(hx, hy) * extrude(Circle(leg_hole_dia / 2), roof_top)

    # --- phase 3: elephant's-foot chamfer on bed-contact edges (leg bottoms)
    bottom = body.edges().group_by(Axis.Z)[0]
    body = chamfer(bottom, ELEPHANT_FOOT_CHAMFER_MM)

    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "neo65"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "canopy_v1.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "canopy_v1.3mf"))
    bb = part.bounding_box()
    print(f"volume {part.volume / 1000:.1f} cm^3, "
          f"mass(ASA) {part.volume / 1000 * 1.07:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
