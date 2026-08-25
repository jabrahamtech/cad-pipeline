"""robotarm wrist_rotator — the wrist ROLL disc. The whole moving half of
the wrist joint, in one part.

Spec: specs/robotarm/wrist_rotator.md.

It replaces a yoke that straddled a drum, an idler stub, a 608ZZ and a
twin-lug clevis. The wrist servo now sits nose-first in the forearm's tip
with its shaft pointing forward down the arm (see models/robotarm/forearm.py),
and this disc is simply what that shaft turns. Two printed parts, no
hardware in the joint at all.

FRAME: LOCAL, and it is the PRINT frame. z = 0 is the FRONT face — the flat
face the effector bolts to — and the part grows +Z toward the arm. The roll
axis is Z through the origin. Assembled, this +Z points back along the
forearm's -X.

WHAT CARRIES THE LOAD. Not the servo shaft. The SKIRT — an annular wall on
the back face at _frame.ROTATOR_R inward — runs on the journal boss on the
forearm's flange, so the effector's weight goes into a Ø39 plain bearing and
the MG90S's 4.8 mm output shaft only ever sees torque. The boss is cut flat
above 45 deg for printability, which leaves it a V-journal open top and
bottom; the skirt is a FULL ring, so the pair still constrains the disc in
every direction.

THE EFFECTOR INTERFACE is four M3 on a Ø22 circle. The inserts go in from
the FRONT and bottom out in bosses on the BACK face, which is the only place
there is room for them: they have to sit inside the journal boss's bore
(r 17) and miss the horn's four arms. See EFFECTOR_BOLT_R in _frame.

Print: front face DOWN on the bed exactly as modelled. Skirt, bosses and
horn pocket all open upward, so there is no support anywhere and the one
face that has to be flat — the effector mounting face — is the bed face.
PETG, 40 % infill, 3 walls.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Cylinder,
    Part,
    Plane,
    Pos,
    Rotation,
    chamfer,
)

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM, M3_INSERT_HOLE_DIA_MM
from lib.servo import horn_pocket

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    EFFECTOR_BOLT_AZ,
    EFFECTOR_BOLT_R,
    EFFECTOR_BOSS_DIA,
    EFFECTOR_BOSS_LEN,
    ROTATOR_R,
    ROTATOR_SKIRT_LEN,
    ROTATOR_SKIRT_T,
    ROTATOR_T,
    WRIST_SERVO,
)

PART_METADATA = {"expected_solids": 1}

HORN_SCREW_BORE = 6.0      # access for the horn's own retaining screw


def build(
    disc_radius: float = ROTATOR_R,
    disc_thickness: float = ROTATOR_T,
    skirt_thickness: float = ROTATOR_SKIRT_T,
    skirt_length: float = ROTATOR_SKIRT_LEN,
    bolt_radius: float = EFFECTOR_BOLT_R,
    bolt_azimuths: tuple[float, ...] = EFFECTOR_BOLT_AZ,
    boss_dia: float = EFFECTOR_BOSS_DIA,
    boss_length: float = EFFECTOR_BOSS_LEN,
    insert_dia: float = M3_INSERT_HOLE_DIA_MM,
    horn_bore_dia: float = HORN_SCREW_BORE,
    rim_chamfer: float = 0.8,
) -> Part:
    # --- phase 1: the disc, then the skirt and the insert bosses, all of
    # which grow +Z off the back face so the bed face stays flat
    body = cast(Part, Pos(0, 0, disc_thickness / 2)
                * Cylinder(disc_radius, disc_thickness))
    skirt = cast(Part, Pos(0, 0, disc_thickness + skirt_length / 2)
                 * (Cylinder(disc_radius, skirt_length)
                    - Cylinder(disc_radius - skirt_thickness,
                               skirt_length + 2)))
    body = cast(Part, body + skirt)
    for az in bolt_azimuths:
        body = cast(Part, body + Rotation(0, 0, az) * Pos(
            bolt_radius, 0, disc_thickness + boss_length / 2)
            * Cylinder(boss_dia / 2, boss_length))

    # --- phase 2: the horn pocket, cut DOWN into the back face. Torque goes
    # through the horn's arms bearing on the pocket walls, not through the
    # M2 horn screws.
    back = Plane(origin=(0, 0, disc_thickness), x_dir=(1, 0, 0),
                 z_dir=(0, 0, -1))
    body = cast(Part, body - back * horn_pocket(
        WRIST_SERVO, arms=4, access_dia=horn_bore_dia,
        access_depth=disc_thickness + 2.0))

    # --- phase 3: the insert holes, drilled from the FRONT so the heat-set
    # tool reaches them, bottoming out inside the bosses
    cuts: list[Part] = []
    for az in bolt_azimuths:
        depth = disc_thickness + boss_length - 1.2
        cuts.append(cast(Part, Rotation(0, 0, az) * Pos(
            bolt_radius, 0, depth / 2) * Cylinder(insert_dia / 2, depth)))
    body = cast(Part, body - cuts)

    # --- phase 4: finish
    try:
        bed = [e for e in body.edges().group_by(Axis.Z)[0]]
        body = cast(Part, chamfer(bed, ELEPHANT_FOOT_CHAMFER_MM))
    except Exception:
        pass
    try:
        rim = [e for e in body.edges().filter_by(Axis.Z, reverse=True)
               if abs(e.center().Z - (disc_thickness + skirt_length)) < 0.01]
        if rim:
            body = cast(Part, chamfer(rim, rim_chamfer))
    except Exception:   # cosmetic only
        pass
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"wrist_rotator: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
