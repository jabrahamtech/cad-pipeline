"""robotarm turret_cap — the drum that bolts on top of base_platter: carries
the MG995 base-yaw servo and the three 608ZZ turntable rollers.

Spec: specs/robotarm/turret_cap.md. Frame: LOCAL — the part's bottom face
(which lands on the platter rim at global Z_RIM) is z = 0, Z up, the MG995
shaft on +Z. Add Z_RIM to get global heights.

Why the rollers: three 608ZZ run on horizontal axles at ROLLER_PITCH_R and
bear on the flat underside of the shoulder turntable. They take the arm's
weight and its overturning moment, so the base servo's output shaft is left
transmitting torque only. That is what lets a micro servo drive the base at
all — without the rollers the whole arm's tipping moment would land on its
gear train. The bearings are bought parts (608ZZ skate bearings on M8 bolts);
nothing here models a bearing.

Print: flat on the bottom face, forks up. No support — the fork slots are
open-ended vertical channels and the Ø8.4 axle holes are short bridged holes.
PETG, 25 % infill, 4 walls.
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
)

from lib.bearings import B608ZZ
from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    M3_INSERT_HOLE_DIA_MM,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    AXLE_HOLE_DIA,
    BASE_SERVO,
    CLIP_AZ,
    CLIP_SCREW_Z,
    WIRE_PASS_AZ,
    WIRE_PASS_DIA,
    WIRE_PASS_R,
    CAP_BOLT_AZ,
    CAP_BOLT_R,
    CAP_DIA,
    CAP_H,
    COLUMN_INNER_X,
    COLUMN_INNER_Y,
    COLUMN_Y,
    LEAD_RELIEF_D,
    LEAD_RELIEF_W,
    FORK_GAP,
    FORK_PAD_DIA,
    FORK_PAD_PROUD,
    FORK_WALL_T,
    ROLLER_AZIMUTHS,
    ROLLER_PITCH_R,
    Z_AXLE,
    Z_RIM,
    Z_ROLLER_FLOOR,
)

PART_METADATA = {"expected_solids": 1}

# local heights
FORK_FLOOR = Z_ROLLER_FLOOR - Z_RIM      # 1.4
AXLE_Z = Z_AXLE - Z_RIM                  # 12.4
FORK_TOP = AXLE_Z + 6.0                  # 18.4 — enough meat over the axle

M3_CLEAR_DIA = 3.4
M3_HEAD_DIA = 6.5
PILOT_DEPTH = 12.0


def servo_to_local(sx: float, sy: float) -> tuple[float, float]:
    """lib.servo's frame (case long axis along +X) -> this part's frame,
    where the case lies along Y with its centre at COLUMN_Y."""
    return (sy, -sx)


def build(
    cap_dia: float = CAP_DIA,
    cap_thickness: float = CAP_H,
    roller_pitch_r: float = ROLLER_PITCH_R,
    fork_wall_thickness: float = FORK_WALL_T,
    fork_gap: float = FORK_GAP,
    axle_hole_dia: float = AXLE_HOLE_DIA,
    pad_dia: float = FORK_PAD_DIA,
    pad_proud: float = FORK_PAD_PROUD,
    bolt_clear_dia: float = M3_CLEAR_DIA,
    bolt_head_dia: float = M3_HEAD_DIA,
    edge_chamfer: float = 1.0,
    skirt_flare: float = 8.0,            # extra radius at the cap's foot
    clip_insert_dia: float = M3_INSERT_HOLE_DIA_MM,
    clip_insert_depth: float = 8.0,
) -> Part:
    # --- phase 1: base shape — the cap plate, on a tapered skirt. The skirt
    # narrows going up so it prints without support, and it steps the base
    # up to the shoulder instead of leaving a disc balanced on a drum.
    body = cast(Part, Pos(0, 0, cap_thickness / 2)
                * Cylinder(cap_dia / 2, cap_thickness))
    if skirt_flare > 0:
        body = cast(Part, body + Cone(
            cap_dia / 2 + skirt_flare, cap_dia / 2, cap_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN)))

    # --- phase 2: roller forks — boss first, then the slot that splits it.
    #
    # THE AXLE POINTS AT THE HUB. The disc's surface moves TANGENTIALLY over
    # each roller, so for the roller to actually roll its axis must be
    # perpendicular to that — i.e. RADIAL, like the rollers in a thrust
    # bearing or the wheels of a car going round a roundabout. An axle laid
    # tangentially looks plausible and is completely wrong: the contact then
    # tries to travel radially while the disc moves tangentially, so the
    # bearing scrubs instead of rolling and wears a flat on its outer race.
    #
    # So the fork's GAP is measured radially (the walls stand fore and aft of
    # the bearing along the radius) and the bearing's diameter lies
    # tangentially.
    slot_span = B608ZZ.od + 7.0          # tangential: clears the Ø22 bearing
    boss_span = B608ZZ.od + 4.0
    boss_w = fork_gap + 2 * fork_wall_thickness      # radial: gap + 2 walls
    for az in ROLLER_AZIMUTHS:
        body = cast(Part, body + Rotation(0, 0, az)
                    * Pos(roller_pitch_r, 0, FORK_TOP / 2)
                    * Box(boss_w, boss_span, FORK_TOP))
    for az in ROLLER_AZIMUTHS:
        slot_h = FORK_TOP - FORK_FLOOR + 10.0
        body = cast(Part, body - Rotation(0, 0, az)
                    * Pos(roller_pitch_r, 0, FORK_FLOOR + slot_h / 2)
                    * Box(fork_gap, slot_span, slot_h))

    # --- phase 3: features — clamp pads (inner race only, so the outer race
    # never touches the fork), then the axle bore through everything
    pads: list[Part] = []
    axles: list[Part] = []
    for az in ROLLER_AZIMUTHS:
        for side in (-1.0, 1.0):
            pads.append(cast(
                Part,
                Rotation(0, 0, az)
                * Pos(roller_pitch_r + side * (fork_gap - pad_proud) / 2,
                      0, AXLE_Z)
                * Rotation(0, 90, 0) * Cylinder(pad_dia / 2, pad_proud),
            ))
        axles.append(cast(
            Part,
            Rotation(0, 0, az) * Pos(roller_pitch_r, 0, AXLE_Z)
            * Rotation(0, 90, 0)
            * Cylinder(axle_hole_dia / 2, boss_w + 20.0),
        ))
    body = cast(Part, body + pads)
    body = cast(Part, body - axles)

    # --- phase 4: servo — case passes through, flange lands on the top face
    cuts: list[Part] = [
        cast(Part, Pos(0, COLUMN_Y, cap_thickness / 2)
             * Box(COLUMN_INNER_X, COLUMN_INNER_Y, cap_thickness + 2.0))
    ]
    # lead relief, full depth, on both side faces of the aperture
    for side in (-1.0, 1.0):
        cuts.append(cast(
            Part,
            Pos(side * (COLUMN_INNER_X / 2 + LEAD_RELIEF_D / 2), COLUMN_Y,
                cap_thickness / 2)
            * Box(LEAD_RELIEF_D + 0.02, LEAD_RELIEF_W, cap_thickness + 2.0)))
    for sx, sy in BASE_SERVO.tab_holes():
        x, y = servo_to_local(sx, sy)
        cuts.append(cast(Part, Pos(x, y, cap_thickness - PILOT_DEPTH / 2)
                         * Cylinder(BASE_SERVO.pilot_dia / 2, PILOT_DEPTH)))

    # --- phase 4a: the wire pass, and a pair of zip-tie slots beside it so
    # the loom is anchored to the cap and its slack loop stays under the disc
    wp = Rotation(0, 0, WIRE_PASS_AZ) * Pos(WIRE_PASS_R, 0, 0)
    cuts.append(cast(Part, Pos(wp.position.X, wp.position.Y,
                               cap_thickness / 2)
                     * Cylinder(WIRE_PASS_DIA / 2, cap_thickness + 2.0)))
    for side in (-1.0, 1.0):
        tie = (Rotation(0, 0, WIRE_PASS_AZ)
               * Pos(WIRE_PASS_R + side * (WIRE_PASS_DIA / 2 + 3.5), 0, 0))
        cuts.append(cast(Part, Pos(tie.position.X, tie.position.Y,
                                   cap_thickness / 2)
                         * Box(3.4, 2.0, cap_thickness + 2.0)))

    # --- phase 4b: RADIAL heat-set inserts for the three hold-down clips.
    # Radial, because the annulus between the Ø96 disc and this Ø104 cap is
    # only 4 mm wide — no room for a boss on the top face — while the plate
    # is 12 mm of solid material edge-on.
    for az in CLIP_AZ:
        cuts.append(cast(
            Part,
            Rotation(0, 0, az)
            * Pos(cap_dia / 2 - clip_insert_depth / 2 + 1.0, 0,
                  cap_thickness + CLIP_SCREW_Z)
            * Rotation(0, 90, 0)
            * Cylinder(clip_insert_dia / 2, clip_insert_depth + 2.0),
        ))

    # --- phase 5: bolts down into the platter's column bosses
    for az in CAP_BOLT_AZ:
        p = Rotation(0, 0, az) * Pos(CAP_BOLT_R, 0, 0)
        x, y = p.position.X, p.position.Y
        cuts.append(cast(Part, Pos(x, y, cap_thickness / 2)
                         * Cylinder(bolt_clear_dia / 2, cap_thickness + 2.0)))
        cuts.append(cast(Part, Pos(x, y, cap_thickness - 2.0)
                         * Cylinder(bolt_head_dia / 2, 4.0 + 2.0)))
    body = cast(Part, body - cuts)

    # --- phase 6: finish — break the crown edge, elephant's foot on the bed
    crown = [
        e for e in body.edges().filter_by(GeomType.CIRCLE)
        if abs(e.center().Z - cap_thickness) < 0.01
        and abs(e.radius - cap_dia / 2) < 0.01  # type: ignore[attr-defined]
    ]
    if crown:
        body = cast(Part, chamfer(crown, edge_chamfer))
    bed = [
        e for e in body.edges().filter_by(GeomType.CIRCLE)
        if abs(e.center().Z) < 0.01
        and e.radius > cap_dia / 2 - 0.5  # type: ignore[attr-defined]
    ]
    if bed:
        body = cast(Part, chamfer(bed, ELEPHANT_FOOT_CHAMFER_MM))
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"turret_cap: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.0f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
    print(f"  flange plane (global z) {Z_RIM + CAP_H:.1f}, "
          f"roller axle {Z_AXLE:.1f}, race {Z_ROLLER_FLOOR + B608ZZ.od:.1f}")
