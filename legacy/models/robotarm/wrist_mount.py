"""robotarm wrist_mount — the bracket that carries the wrist servo.

Spec: specs/robotarm/wrist_mount.md.

It is a SADDLE with a face on the front. The saddle slips over the forearm's
tip from outside and takes two M3 straight through it and both of the link's
side plates; the face is a plate square across the arm with a slot for the
servo's body, so the flange bolts to it and the shaft points forward down the
arm. wrist_rotator turns on that shaft.

WHY IT IS A SEPARATE PART. The wrist is the piece of this machine most likely
to change, and a bracket can be re-cut on its own without reprinting a 20 cm^3
link. It also leaves the forearm's tip as the easiest shape in the project to
print: two vertical walls and a floor, no drum, no flange, no servo pocket.

FRAME: LOCAL, and also the print frame. x = 0 is the FOREARM'S TIP — i.e.
x = FOREARM_LEN in the link's own frame — and the saddle runs back along -X
from there, so the two mate with a pure translation of (FOREARM_LEN, 0,
-floor). z = 0 is the saddle's outside floor, which sits floor below the
link's own bed face, so the roll axis lands at floor + LINK_AXIS_Z.

WHAT CARRIES THE LOAD. Not the servo shaft. The annular JOURNAL BOSS on the
front of the face is what wrist_rotator's skirt runs on, so the effector's
weight goes into a Ø39 plain bearing and the MG90S only ever sees torque.
The boss is cut flat above 45 deg from the axis so it prints without support,
which leaves it a V-journal open top and bottom; the skirt is a full ring, so
the pair still constrains the disc in every direction. That cut is also what
keeps the servo's own mounting tabs clear of the boss wall — they reach
r 21.75 at the top of their span, well outside the bore.

Print: flat on the bed as modelled, saddle opening up. Every wall is
vertical, the face is a vertical disc truncated at the bed, and the boss is
cut at 45 deg — no support anywhere. PETG, 40 % infill, 4 walls.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Box,
    Cylinder,
    Part,
    Pos,
    Rotation,
    chamfer,
)

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM, SLIDING_FIT_CLEARANCE_MM
from lib.servo import case_pocket, tab_pilots

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    FOREARM_TIP_W,
    LINK_AXIS_Z,
    WRIST_BOSS_BORE_R,
    WRIST_BOSS_CUT_Z,
    WRIST_BOSS_LEN,
    WRIST_BOSS_R,
    WRIST_FACE_X,
    WRIST_FLANGE_R,
    WRIST_FLANGE_T,
    WRIST_MOUNT_BOLT_DIA,
    WRIST_MOUNT_BOLT_DX,
    WRIST_MOUNT_SADDLE_LEN,
    WRIST_MOUNT_WALL,
    WRIST_SERVO,
)

PART_METADATA = {"expected_solids": 1}

SADDLE_H = 24.0      # how far up the link's side plates the saddle grips


def build(
    tip_width: float = FOREARM_TIP_W,
    wall: float = WRIST_MOUNT_WALL,
    floor: float = WRIST_MOUNT_WALL,
    saddle_length: float = WRIST_MOUNT_SADDLE_LEN,
    saddle_height: float = SADDLE_H,
    face_x: float = WRIST_FACE_X,
    face_thickness: float = WRIST_FLANGE_T,
    face_radius: float = WRIST_FLANGE_R,
    boss_bore_r: float = WRIST_BOSS_BORE_R,
    boss_r: float = WRIST_BOSS_R,
    boss_len: float = WRIST_BOSS_LEN,
    boss_cut_z: float = WRIST_BOSS_CUT_Z,
    bolt_dx: tuple[float, ...] = WRIST_MOUNT_BOLT_DX,
    bolt_dia: float = WRIST_MOUNT_BOLT_DIA,
    axis_z: float = 0.0,          # 0 = derive from floor + LINK_AXIS_Z
    clearance: float = SLIDING_FIT_CLEARANCE_MM,
) -> Part:
    z_axis = axis_z or (floor + LINK_AXIS_Z)
    inner_w = tip_width + clearance
    outer_w = inner_w + 2 * wall
    x0 = -saddle_length
    x1 = face_x
    front = face_x + face_thickness
    big = 400.0

    # --- phase 1: the saddle — a U the link's tip slides into
    body = cast(Part, Pos((x0 + x1) / 2, 0, (floor + saddle_height) / 2)
                * Box(x1 - x0, outer_w, floor + saddle_height))
    body = cast(Part, body - Pos((x0 + x1) / 2 - 0.5, 0,
                                 floor + saddle_height / 2 + 0.5)
                * Box(x1 - x0 + 1.0, inner_w, saddle_height + 1.0))

    # --- phase 2: the face, and the journal boss on the front of it
    disc = cast(Part, Pos(face_x + face_thickness / 2, 0, z_axis)
                * Rotation(0, 90, 0) * Cylinder(face_radius, face_thickness))
    boss = cast(Part, Pos(front + boss_len / 2, 0, z_axis) * Rotation(0, 90, 0)
                * (Cylinder(boss_r, boss_len) - Cylinder(boss_bore_r,
                                                         boss_len + 2)))
    boss = cast(Part, boss - Pos(front + boss_len / 2, 0, boss_cut_z + big / 2)
                * Box(big, big, big))
    body = cast(Part, body + disc + boss)

    # --- phase 3: the servo, nose-first. Its own X (the tab / 22.8 mm axis)
    # goes UP and its Z (the shaft) goes forward, so the case stands upright
    # behind the face and the tabs land top and bottom of it.
    # Rz(180) first, not Rz(90): X->Z with Y fixed is a reflection, and the
    # servo would come out mirrored.
    at = Pos(front, 0, z_axis) * Rotation(0, 90, 0) * Rotation(0, 0, 180)
    body = cast(Part, body - at * case_pocket(
        WRIST_SERVO, below=WRIST_SERVO.below_flange,
        above=face_thickness + 1.0, lead_notch=False))
    body = cast(Part, body - at * tab_pilots(WRIST_SERVO,
                                             depth=face_thickness))

    # --- phase 4: the two through-bolts, and trim everything below the bed
    for dx in bolt_dx:
        body = cast(Part, body - Pos(dx, 0, z_axis) * Rotation(90, 0, 0)
                    * Cylinder(bolt_dia / 2, big))
    body = cast(Part, body - Pos(0, 0, -big / 2) * Box(big, big, big))

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
    print(f"wrist_mount: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
