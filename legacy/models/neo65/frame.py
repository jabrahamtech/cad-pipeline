"""neo65 frame — unibody ducted frame for a 65 mm 1S brushless whoop.

Spec: specs/neo65/frame.md. Indoor follow-camera drone; full ducts because
it flies near a person. Printed flat, bed = rib-feet/battery-rail plane
(z = -(channel height + lip)), so deck and arm loads stay in-plane with
layers. Duct ring bands float on ribs → requires support material.
X is forward, Z is up, deck spans z = 0..deck_thickness.
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
    RectangleRounded,
    Rot,
    Sketch,
    SlotOverall,
    chamfer,
    extrude,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    SLIDING_FIT_CLEARANCE_MM,
)

PART_METADATA = {"expected_solids": 1, "needs_support_material": True}

# Interface constants from the spec — not tunables.
MOTOR_BOLT_CIRCLE_MM = 6.6     # 0802 class: 3x M1.4 (verify on purchased motor)
MOTOR_SCREW_HOLE_MM = 1.6
FC_HOLE_GRID_MM = 25.5         # whoop AIO standard
FC_SELF_TAP_DIA_MM = 1.7       # M2 self-tap into ASA (ASSUMED)
BATTERY_W_MM = 15.5            # BetaFPV BT2.0 1S 450 mAh
BATTERY_H_MM = 6.7


def build(
    wheelbase: float = 65.0,
    prop_dia: float = 31.0,
    duct_tip_clearance: float = 1.75,
    duct_wall_thickness: float = 1.6,
    duct_top_z: float = 20.0,        # above prop plane (~14-18, ASSUMED stack)
    ring_band_bottom_z: float = 14.0,  # full ring covers the blade plane
    rib_width: float = 5.0,
    deck_thickness: float = 2.0,
    hub_size: float = 32.0,          # covers FC posts at 25.5 grid
    arm_width: float = 7.0,
    motor_pad_dia: float = 11.5,     # 0802 base 10.5 mm
    motor_pad_riser: float = 4.0,    # lifts prop plane clear of FC + canopy legs
    motor_screw_head_bore: float = 3.2,  # M1.4 head pocket so 4 mm screws reach
    motor_shaft_relief_dia: float = 4.0,
    fc_post_dia: float = 5.0,
    fc_post_height: float = 2.0,
    batt_rail_length: float = 32.0,
    batt_lip_depth: float = 1.5,
    batt_lip_thickness: float = 1.6,
    strap_slot_length: float = 10.0,
    strap_slot_width: float = 3.2,
    strap_slot_y: float = 11.3,      # outboard of rails, inboard of hub edge
) -> Part:
    motor_xy = wheelbase / 2 / math.sqrt(2)   # motor centers (±motor_xy, ±motor_xy)
    duct_r_in = prop_dia / 2 + duct_tip_clearance
    duct_r_out = duct_r_in + duct_wall_thickness
    rib_r_mid = (duct_r_in + duct_r_out) / 2

    channel_w = BATTERY_W_MM + 2 * SLIDING_FIT_CLEARANCE_MM / 2  # 16.0 total
    channel_h = BATTERY_H_MM + SLIDING_FIT_CLEARANCE_MM
    z_bed = -(channel_h + batt_lip_thickness)   # lowest plane; sits on the bed
    rail_wall = duct_wall_thickness

    # --- phase 1: deck — hub + diagonal arms + motor pads, one extrusion
    profile = RectangleRounded(hub_size, hub_size, 3.0)
    arm_r0 = 10.0                                  # arms start inside the hub
    arm_r1 = wheelbase / 2 + rib_r_mid             # end merged into outer rib
    for sx in (1, -1):
        for sy in (1, -1):
            base_ang = math.degrees(math.atan2(sy, sx))
            profile += Rot(Z=base_ang) * Pos((arm_r0 + arm_r1) / 2, 0) * Rectangle(
                arm_r1 - arm_r0, arm_width
            )
            profile += Pos(sx * motor_xy, sy * motor_xy) * Circle(motor_pad_dia / 2)
    body = extrude(profile, deck_thickness)

    # motor pad risers — prop plane must clear FC components and canopy legs
    for sx in (1, -1):
        for sy in (1, -1):
            body += Pos(sx * motor_xy, sy * motor_xy, deck_thickness) * extrude(
                Circle(motor_pad_dia / 2), motor_pad_riser
            )

    # --- phase 1: ducts — ring band at the blade plane on 4 ribs per duct
    ring = cast(Sketch, Circle(duct_r_out) - Circle(duct_r_in))
    for sx in (1, -1):
        for sy in (1, -1):
            at = Pos(sx * motor_xy, sy * motor_xy)
            body += at * Pos(0, 0, ring_band_bottom_z) * extrude(
                ring, duct_top_z - ring_band_bottom_z
            )
            base_ang = math.degrees(math.atan2(sy, sx))
            # Rib placement is constrained twice over: nothing on the hub
            # diagonal (canopy leg-spoke corridor) and nothing over the
            # battery slide-in corridor (|y| below ~13 for any x) — see
            # _check_assembly.py. 135*s mirrors the hub-side rib away from
            # the battery channel in every quadrant.
            for d_ang in (0.0, 45.0, -45.0, 135.0 * sx * sy):
                rib = cast(
                    Sketch,
                    at
                    * Rot(Z=base_ang + d_ang)
                    * Pos(rib_r_mid, 0, z_bed)
                    * Rectangle(duct_wall_thickness, rib_width),
                )
                body += extrude(rib, ring_band_bottom_z - z_bed)

    # --- phase 1: battery cradle — side rails with bottom lips, under the hub
    for sy in (1, -1):
        rail = Pos(0, sy * (channel_w + rail_wall) / 2, z_bed) * Rectangle(
            batt_rail_length, rail_wall
        )
        body += extrude(rail, -z_bed)
        lip = Pos(
            0, sy * (channel_w / 2 - batt_lip_depth / 2), z_bed
        ) * Rectangle(batt_rail_length, batt_lip_depth)
        body += extrude(lip, batt_lip_thickness)

    # --- phase 1: FC posts
    fc_half = FC_HOLE_GRID_MM / 2
    for hx in (fc_half, -fc_half):
        for hy in (fc_half, -fc_half):
            body += Pos(hx, hy, deck_thickness) * extrude(
                Circle(fc_post_dia / 2), fc_post_height
            )

    # --- phase 2: features (cuts)
    pad_top = deck_thickness + motor_pad_riser
    for sx in (1, -1):
        for sy in (1, -1):
            at = Pos(sx * motor_xy, sy * motor_xy)
            body -= at * extrude(Circle(motor_shaft_relief_dia / 2), pad_top)
            for k in range(3):
                ang = math.radians(90 + k * 120)
                hx = MOTOR_BOLT_CIRCLE_MM / 2 * math.cos(ang)
                hy = MOTOR_BOLT_CIRCLE_MM / 2 * math.sin(ang)
                # thru hole + head pocket from below: 2 mm web, M1.4x4 reaches
                body -= at * Pos(hx, hy) * extrude(
                    Circle(MOTOR_SCREW_HOLE_MM / 2), pad_top
                )
                body -= at * Pos(hx, hy) * extrude(
                    Circle(motor_screw_head_bore / 2), motor_pad_riser
                )
    for sy in (1, -1):  # battery strap slots, outboard of the rails
        body -= Pos(0, sy * strap_slot_y) * extrude(
            SlotOverall(strap_slot_length, strap_slot_width), deck_thickness
        )

    # FC self-tap holes run through post + deck
    for hx in (fc_half, -fc_half):
        for hy in (fc_half, -fc_half):
            body -= Pos(hx, hy) * extrude(
                Circle(FC_SELF_TAP_DIA_MM / 2), deck_thickness + fc_post_height
            )

    # --- phase 3: elephant's-foot chamfer on bed-contact edges
    bottom = body.edges().group_by(Axis.Z)[0]
    body = chamfer(bottom, ELEPHANT_FOOT_CHAMFER_MM)

    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "neo65"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "frame_v1.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "frame_v1.3mf"))
    bb = part.bounding_box()
    print(f"volume {part.volume / 1000:.1f} cm^3, "
          f"mass(ASA) {part.volume / 1000 * 1.07:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
