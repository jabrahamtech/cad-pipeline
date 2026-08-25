"""robotarm hand_finger — one claw finger, straight onto a servo horn.

Spec: specs/robotarm/hand_finger.md. **Print two identical copies.**

Frame: LOCAL, and also the print frame. The pivot is the origin, the blade
runs along +X, and the thickness is Z so the part lies flat on the bed. In
the hand its local X becomes the swing direction and its local Z becomes the
servo's shaft axis.

THE HORN POCKET GOES CLEAN THROUGH, and that is the whole reason the two
fingers are one part. Finger R is finger L turned 180 deg about the shaft
axis, which FLIPS IT OVER — so a blind pocket in one face would end up on the
wrong side. Cut through and either face can meet the horn. The cost is that
the horn's own retaining screw needs a WASHER under its head; there is no
material left above it to bear on.

Torque runs horn arms -> pocket walls -> blade, never through the little M2
horn screws.

The gripping edge is the -Y side, because that is the side the tip moves
toward as the finger closes. Three grooves are cut into it near the tip.

Print: flat on the bed exactly as modelled. It is a plate with a slot in it —
no overhangs anywhere, no support. PETG, 40 % infill, 4 walls; orient it so
the blade's length runs along the bed's X for the best layer direction,
because it is loaded in bending about Z.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Box,
    Circle,
    Part,
    Plane,
    Polyline,
    Pos,
    Rotation,
    Sketch,
    chamfer,
    extrude,
    make_face,
)

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM
from lib.servo import horn_pocket

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import EFFECTOR_SERVO  # noqa: E402
from _hand import (  # noqa: E402
    FINGER_R,
    FINGER_T,
    GRIP_GROOVE,
    ROOT_R,
    TIP_R,
)

PART_METADATA = {"expected_solids": 1}


def _outline(root_r: float, tip_r: float, reach: float) -> Sketch:
    """Root disc, tapered arm, rounded tip — the classic claw paddle."""
    arm = cast(Sketch, make_face(Polyline(
        (0.0, -root_r * 0.72), (reach, -tip_r), (reach, tip_r),
        (0.0, root_r * 0.72), close=True)))
    return cast(Sketch, Circle(root_r) + arm + Pos(reach, 0) * Circle(tip_r))


def build(
    root_radius: float = ROOT_R,
    tip_radius: float = TIP_R,
    reach: float = FINGER_R,
    thickness: float = FINGER_T,
    groove_depth: float = GRIP_GROOVE,
    groove_count: int = 3,
    groove_first: float = 0.52,     # fraction of reach
    groove_step: float = 0.16,
    edge_chamfer: float = 0.8,
) -> Part:
    # --- phase 1: the blade
    body = cast(Part, extrude(Plane.XY * _outline(root_radius, tip_radius,
                                                  reach), thickness))

    # --- phase 2: the horn pocket, cut RIGHT THROUGH (see the docstring)
    body = cast(Part, body - Pos(0, 0, -1.0) * horn_pocket(
        EFFECTOR_SERVO, depth=thickness + 2.0, arms=4,
        access_dia=EFFECTOR_SERVO.horn_arm_w,
        access_depth=0.01))

    # --- phase 3: grip grooves in the -Y edge, the side the tip moves
    # toward as the finger closes
    cuts: list[Part] = []
    for i in range(groove_count):
        x = reach * (groove_first + groove_step * i)
        cuts.append(cast(Part, Pos(x, -tip_radius, thickness / 2)
                         * Rotation(0, 0, 45)
                         * Box(groove_depth * 1.414, groove_depth * 1.414,
                               thickness + 2.0)))
    body = cast(Part, body - cuts)

    # --- phase 4: finish. Break both faces, not just the bed one: this part
    # gets printed twice and one of them is fitted upside down.
    for grp in (0, -1):
        try:
            edges = [e for e in body.edges().group_by(Axis.Z)[grp]
                     if e.length > 2.0]
            body = cast(Part, chamfer(edges, ELEPHANT_FOOT_CHAMFER_MM
                                      if grp == 0 else edge_chamfer))
        except Exception:   # cosmetic only
            pass
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"hand_finger: volume {part.volume / 1000:.2f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
