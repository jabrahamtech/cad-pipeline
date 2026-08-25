"""robotarm hand_base — the claw body: bolts to wrist_rotator and carries
both finger servos.

Spec: specs/robotarm/hand_base.md. Frame: models/robotarm/_hand.py — z = 0 is
the face that bolts to the rotator and the part grows +Z, forward along the
arm. The fingers close along X.

SHAPE: a plate and two uprights, and nothing else. Each upright is one
servo's mounting wall: the case drops through its aperture from the front,
the tabs land on its +Y face, and the horn stands proud on that same side
with the finger straight on it. No standoff box, no deck, no linkage.

WHY THE UPRIGHTS ARE 38 mm APART. Not styling — each finger's root has to
swallow the SG90's 32 mm cross horn, which makes it an 18 mm disc, and two
of those cannot be closer than 36 mm without fouling each other.

WHY THE SERVOS FACE THE SAME WAY. Both shafts run +Y, so both bodies hang
behind the uprights and both fingers swing in one plane in front of them.
That also balances the hand about the roll axis: ~18 g of servo at y = -10
against ~11 g of finger at y = +17 puts the centre of mass within a
millimetre of the axis, which is what keeps the wrist servo idle.

The four flange screws go in from ABOVE, clear of both uprights — but they
still have to be fitted before the servos, because a driver cannot reach past
a fitted case.

Print: flat on the bed face as modelled. Uprights and gussets are vertical
walls, the gussets' hypotenuses are 45 deg, and the case apertures are
through-slots — no support anywhere. PETG, 35 % infill, 4 walls.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Box,
    Cylinder,
    Part,
    Plane,
    Polyline,
    Pos,
    Rotation,
    chamfer,
    extrude,
    make_face,
)

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM
from lib.servo import case_pocket, tab_pilots

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    EFFECTOR_BOLT_AZ,
    EFFECTOR_BOLT_CLEAR_DIA,
    EFFECTOR_BOLT_R,
    EFFECTOR_SERVO,
)
from _hand import (  # noqa: E402
    BASE_HALF_Y,
    BASE_T,
    PIVOT_X,
    PIVOT_Z,
    UPRIGHT_FACE_Y,
    UPRIGHT_HALF_W,
    UPRIGHT_T,
)

PART_METADATA = {"expected_solids": 1}

ARM_HALF_Y = 9.0          # the base's arms out to the uprights
PAD_HALF_X = 16.0         # the central pad that carries the bolt circle


def build(
    base_thickness: float = BASE_T,
    pad_half_x: float = PAD_HALF_X,
    pad_half_y: float = BASE_HALF_Y,
    arm_half_y: float = ARM_HALF_Y,
    pivot_x: float = PIVOT_X,
    pivot_z: float = PIVOT_Z,
    upright_t: float = UPRIGHT_T,
    upright_half_w: float = UPRIGHT_HALF_W,
    face_y: float = UPRIGHT_FACE_Y,
    gusset_t: float = 3.0,
    gusset_size: float = 15.0,
    bolt_r: float = EFFECTOR_BOLT_R,
    bolt_az: tuple[float, ...] = EFFECTOR_BOLT_AZ,
    bolt_clear_dia: float = EFFECTOR_BOLT_CLEAR_DIA,
    clearance: float = 0.25,
) -> Part:
    servo = EFFECTOR_SERVO
    x_out = pivot_x + upright_half_w
    # tall enough to carry the OUTER tab hole with a full pad round it; the
    # case is not centred on its shaft, so that hole is 19.4 above the pivot
    top_z = pivot_z + servo.shaft_offset + servo.hole_pitch_l / 2 + 4.0

    # --- phase 1: the base — a central pad for the bolt circle, two arms
    body = cast(Part, Pos(0, 0, base_thickness / 2)
                * Box(2 * pad_half_x, 2 * pad_half_y, base_thickness))
    for sx in (-1.0, 1.0):
        body = cast(Part, body + Pos(
            sx * (pad_half_x + x_out) / 2, 0, base_thickness / 2)
            * Box(x_out - pad_half_x, 2 * arm_half_y, base_thickness))

    # --- phase 2: the two uprights, plus a gusset on each outer edge
    for sx in (-1.0, 1.0):
        body = cast(Part, body + Pos(
            sx * pivot_x, face_y - upright_t / 2, top_z / 2)
            * Box(2 * upright_half_w, upright_t, top_z))
        gus = cast(Part, extrude(Plane.YZ * make_face(Polyline(
            (face_y - upright_t, base_thickness),
            (face_y - upright_t - gusset_size, base_thickness),
            (face_y - upright_t, base_thickness + gusset_size),
            close=True)), gusset_t))
        bb = gus.bounding_box()
        body = cast(Part, body + Pos(
            sx * x_out - bb.min.X - (gusset_t if sx > 0 else 0.0), 0, 0)
            * gus)

    # --- phase 3: the servos. Shaft +Y, case dropping back through the
    # upright, tabs bearing on its +Y face.
    cuts: list[Part] = []
    for sx in (-1.0, 1.0):
        at = (Pos(sx * pivot_x, face_y, pivot_z)
              * Rotation(-90, 0, 0) * Rotation(0, 0, 90))
        cuts.append(cast(Part, at * case_pocket(
            servo, clearance=clearance,
            below=servo.below_flange, above=upright_t + 1.0)))
        cuts.append(cast(Part, at * tab_pilots(servo, depth=upright_t)))

    # --- phase 4: the four flange bolts, clear of both uprights
    for az in bolt_az:
        cuts.append(cast(Part, Rotation(0, 0, az) * Pos(
            bolt_r, 0, base_thickness / 2)
            * Cylinder(bolt_clear_dia / 2, base_thickness + 2.0)))
    body = cast(Part, body - cuts)

    # --- phase 5: finish
    try:
        bed = [e for e in body.edges().group_by(Axis.Z)[0] if e.length > 2.0]
        body = cast(Part, chamfer(bed, ELEPHANT_FOOT_CHAMFER_MM))
    except Exception:
        pass
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"hand_base: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
