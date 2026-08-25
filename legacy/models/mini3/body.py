"""mini3 body — unibody frame for a 3-inch sub-250 g quad.

Spec: specs/mini3/body.md. Printed flat; arm bending loads stay in-plane
with the layers. X is forward, Z is up, deck top at z = body_thickness.
"""

import math
from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Circle,
    Part,
    Pos,
    Rectangle,
    Rot,
    SlotOverall,
    chamfer,
    extrude,
    fillet,
)

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM

PART_METADATA = {"expected_solids": 1}

# Interface constants from the spec (DATASHEET) — not tunables.
MOTOR_HOLE_GRID_MM = 9.0  # 1404 class: 4x M2 on a 9x9 square
FC_HOLE_GRID_MM = 25.5    # whoop AIO standard mounting pattern


def build(
    wheelbase: float = 140.0,
    body_thickness: float = 6.0,
    arm_width: float = 10.0,
    hub_length: float = 74.0,
    hub_width: float = 38.0,
    motor_pad_dia: float = 19.0,      # spec: ASSUMED ~Ø18 motor base
    m2_clearance_dia: float = 2.4,
    motor_shaft_relief_dia: float = 5.0,  # spec: ASSUMED
    fc_head_bore_dia: float = 4.4,
    fc_head_bore_depth: float = 1.5,
    strap_slot_length: float = 14.0,  # spec: ASSUMED, 12 mm strap
    strap_slot_width: float = 3.2,
    strap_slot_x: float = 26.0,  # outboard of FC counterbores (keep ≥1.6 mm web)
    strap_slot_y: float = 15.5,
    junction_fillet: float = 4.0,
    pad_fillet: float = 2.5,
) -> Part:
    motor_xy = wheelbase / 2 / math.sqrt(2)  # motor center at (±motor_xy, ±motor_xy)

    # --- phase 1: base shape — hub + arms + motor pads, one extrusion
    profile = Rectangle(hub_length, hub_width)
    for sx in (1, -1):
        for sy in (1, -1):
            angle = math.degrees(math.atan2(sy, sx))
            arm_len = math.hypot(motor_xy, motor_xy)
            profile += Pos(sx * motor_xy / 2, sy * motor_xy / 2) * Rot(
                Z=angle
            ) * Rectangle(arm_len, arm_width)
            profile += Pos(sx * motor_xy, sy * motor_xy) * Circle(motor_pad_dia / 2)

    body = extrude(profile, body_thickness)

    # --- phase 3a: vertical-edge fillets (before holes so hole edges stay sharp)
    # OCC rejects hub corners + arm junctions in a single fillet call, so
    # select each family analytically and fillet in sequence.
    hx, hy = hub_length / 2, hub_width / 2
    arm_off = arm_width / 2 * math.sqrt(2)  # arm edge crossings on the hub side

    def pick(shape, kind: str) -> list:
        out = []
        for e in shape.edges().filter_by(Axis.Z):
            c = e.center()
            ax, ay = abs(c.X), abs(c.Y)
            if kind == "corner" and abs(ax - hx) < 0.1 and abs(ay - hy) < 0.1:
                out.append(e)
            elif (
                kind == "arm"
                and abs(ay - hy) < 0.1
                and (abs(ax - (hy - arm_off)) < 0.1 or abs(ax - (hy + arm_off)) < 0.1)
            ):
                out.append(e)
            elif kind == "pad" and math.hypot(c.X, c.Y) > motor_xy + 2:
                out.append(e)
        return out

    body = fillet(pick(body, "corner"), junction_fillet)
    body = fillet(pick(body, "arm"), junction_fillet)
    body = fillet(pick(body, "pad"), pad_fillet)

    # --- phase 2: features (all cut through)
    cuts = []
    hole_half = MOTOR_HOLE_GRID_MM / 2
    for sx in (1, -1):
        for sy in (1, -1):
            angle = math.degrees(math.atan2(sy, sx))
            at_motor = Pos(sx * motor_xy, sy * motor_xy) * Rot(Z=angle)
            cuts.append(at_motor * Circle(motor_shaft_relief_dia / 2))
            for hx in (hole_half, -hole_half):
                for hy in (hole_half, -hole_half):
                    cuts.append(
                        at_motor * Pos(hx, hy) * Circle(m2_clearance_dia / 2)
                    )

    fc_half = FC_HOLE_GRID_MM / 2
    for hx in (fc_half, -fc_half):
        for hy in (fc_half, -fc_half):
            cuts.append(Pos(hx, hy) * Circle(m2_clearance_dia / 2))

    for sx_ in (strap_slot_x, -strap_slot_x):
        for sy_ in (strap_slot_y, -strap_slot_y):
            cuts.append(Pos(sx_, sy_) * SlotOverall(strap_slot_length, strap_slot_width))

    # nose zip-tie slots (camera / antenna lashing)
    for sy_ in (8.0, -8.0):
        cuts.append(Pos(30.0, sy_) * Rot(Z=90) * SlotOverall(8.0, strap_slot_width))

    for c in cuts:
        body -= extrude(c, body_thickness)

    # FC screw-head counterbores from below, so the belly lands flush
    for hx in (fc_half, -fc_half):
        for hy in (fc_half, -fc_half):
            body -= extrude(
                Pos(hx, hy) * Circle(fc_head_bore_dia / 2), fc_head_bore_depth
            )

    # --- phase 3b: elephant's-foot chamfer on all bottom edges
    bottom = body.edges().group_by(Axis.Z)[0]
    body = chamfer(bottom, ELEPHANT_FOOT_CHAMFER_MM)

    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "mini3"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "body_v1.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "body_v1.3mf"))
    bb = part.bounding_box()
    print(f"volume {part.volume / 1000:.1f} cm^3, "
          f"mass(ASA) {part.volume / 1000 * 1.07:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
