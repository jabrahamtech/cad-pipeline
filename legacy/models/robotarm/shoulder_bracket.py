"""robotarm shoulder_bracket — the turntable and the shoulder DRUM: a disc
that rides on the three 608ZZ rollers, driven by the base servo's horn,
carrying the MG995 inside a cylindrical housing.

Spec: specs/robotarm/shoulder_bracket.md. Frame: LOCAL — the disc's underside
(the roller race face, global Z_RACE) is z = 0, Z up, the base-yaw axis on +Z.
The shoulder axis is horizontal, along Y, at z = TURNTABLE_T + SHOULDER_RISE.

THE DRUM. This part holds the shoulder servo's CASE, so under the joint
contract in _frame.py it carries the drum: a cylinder concentric with the
shoulder axis, sized to swallow the MG995 — which reaches 32.2 mm from its
own shaft, because the shaft sits well off the case centre. upper_arm then
wraps it with a concentric SKIRT. Both being concentric is the whole trick:
the joint reads closed at every angle and neither part sweeps anything new,
which is exactly what a flat cover can never do.

Drum width is the servo's below-flange depth PLUS BOTH CAPS (32.0 + 2x3.0 =
38.0). Sizing it to the case depth alone is wrong and was the first attempt:
the caps eat the bore, leaving the case 6 mm too deep, with its far end
landing exactly where the idler bore has to go. _check_arm.py caught it.
The horn then seats 19.0 + 6.9 = 25.9 from the drum centre, which is what
sets the arm's channel half-width, so the driven plate lands on the horn.

Load path is unchanged: the disc's flat underside rests on the rollers at
ROLLER_PITCH_R, so weight and overturning moment go into the bearings. The
base servo's horn is captured in a cross pocket, so drive torque is carried
by the horn's arms bearing on pocket walls, not by four M2 screws; its
retaining screw is reached through the Ø6 bore up the middle of the disc.

Print: disc down, drum up. Do NOT print it on its side — the race face must
come off the bed flat. The drum is a horizontal cylinder, so only its bore's
crown droops, over the top millimetre, where nothing bears: the servo is
located by the case aperture and its tab screws, and the idler runs in a
clearance bore.
PETG, 40 % infill, 4 walls.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Box,
    Cylinder,
    GeomType,
    Part,
    Pos,
    Rotation,
    chamfer,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    SLIDING_FIT_CLEARANCE_MM,
)
from lib.servo import horn_pocket

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    BASE_SERVO,
    DRUM_R_SHOULDER,
    BEARING_SEAT_DEPTH,
    BEARING_SEAT_DIA,
    IDLER_BOSS_DIA,
    LEAD_RELIEF_D,
    LEAD_RELIEF_W,
    SHOULDER_AXIS_OFFSET_X,
    SHOULDER_DRUM_WALL,
    SHOULDER_DRUM_Y,
    SHOULDER_RISE,
    SHOULDER_SERVO,
    TURNTABLE_DIA,
    TURNTABLE_T,
    WIRE_BORE_DIA,
)
from _shell import drum  # noqa: E402

PART_METADATA = {"expected_solids": 1}

BOSS_RELIEF_DIA = 9.0       # clears the base servo's output boss above the horn
BOSS_RELIEF_DEPTH = 1.0
PEDESTAL_X = 46.0           # width of the column that lifts the drum


def build(
    disc_dia: float = TURNTABLE_DIA,
    disc_thickness: float = TURNTABLE_T,
    drum_radius: float = DRUM_R_SHOULDER,
    drum_wall_thickness: float = SHOULDER_DRUM_WALL,
    shoulder_rise: float = SHOULDER_RISE,
    idler_dia: float = IDLER_BOSS_DIA,
    pedestal_width: float = PEDESTAL_X,
    boss_relief_dia: float = BOSS_RELIEF_DIA,
    clearance: float = SLIDING_FIT_CLEARANCE_MM,
) -> Part:
    servo = SHOULDER_SERVO
    shaft_z = disc_thickness + shoulder_rise
    shaft_x = SHOULDER_AXIS_OFFSET_X
    y0, y1 = SHOULDER_DRUM_Y
    reach = servo.case[0] / 2 + servo.shaft_offset
    # the CAPS eat into the bore, so the case needs width minus both of them
    bore_len = (y1 - y0) - 2 * drum_wall_thickness
    if bore_len < servo.below_flange:
        raise ValueError(
            f"drum bore is {bore_len} mm deep between its caps but the "
            f"{servo.name} hangs {servo.below_flange} mm below its flange — "
            f"the case would foul the far cap, exactly where its idler bore "
            f"goes; widen the drum to "
            f"{servo.below_flange + 2 * drum_wall_thickness}"
        )
    if drum_radius - drum_wall_thickness < reach:
        raise ValueError(
            f"drum bore r={drum_radius - drum_wall_thickness:.1f} does not "
            f"clear the {servo.name} case reach {reach:.1f}"
        )
    if drum_radius > disc_dia / 2:
        raise ValueError("drum overhangs the turntable disc")

    axis = Pos(shaft_x, 0, shaft_z)
    bore_r = drum_radius - drum_wall_thickness

    # --- phase 1: base shape — race disc, pedestal, drum with end caps
    body = cast(Part, Pos(0, 0, disc_thickness / 2)
                * Cylinder(disc_dia / 2, disc_thickness))
    ped_top = shaft_z - drum_radius * 0.5
    body = cast(Part, body + Pos(shaft_x, (y0 + y1) / 2,
                                 (disc_thickness + ped_top) / 2)
                * Box(pedestal_width, y1 - y0, ped_top - disc_thickness))
    body = cast(Part, body + axis * drum(drum_radius, y0, y1,
                                         drum_wall_thickness))
    body = cast(Part, body + axis * Pos(0, (y0 + y1) / 2, 0)
                * Rotation(90, 0, 0) * Cylinder(drum_radius, y1 - y0))
    # hollow it back out between the caps
    body = cast(Part, body - axis * Pos(0, (y0 + y1) / 2, 0)
                * Rotation(90, 0, 0)
                * Cylinder(bore_r, (y1 - y0) - 2 * drum_wall_thickness))

    # --- phase 2: features — the servo drops in through the near cap
    cuts: list[Part] = [
        # access bore opened out to WIRE_BORE_DIA: it is both the
        # screwdriver access for the horn screw and the wire pass, and it
        # sits ON the axis so base rotation twists the loom rather than
        # dragging it round
        cast(Part, horn_pocket(BASE_SERVO, access_dia=WIRE_BORE_DIA)),
        cast(Part, Pos(0, 0, BOSS_RELIEF_DEPTH / 2)
             * Cylinder(boss_relief_dia / 2, BOSS_RELIEF_DEPTH)),
        # case aperture in the near cap, offset because the shaft is not at
        # the case centre
        cast(Part, axis * Pos(servo.shaft_offset,
                              y0 + drum_wall_thickness / 2, 0)
             * Box(servo.case[0] + clearance, drum_wall_thickness + 2.0,
                   servo.case[1] + clearance)),
        # lead relief: the servo is turned so its case's side faces lie along
        # this part's Z, so the notch goes above and below the aperture
        *[cast(Part, axis * Pos(
            servo.shaft_offset, y0 + drum_wall_thickness / 2,
            side * (servo.case[1] / 2 + LEAD_RELIEF_D / 2))
            * Box(LEAD_RELIEF_W, drum_wall_thickness + 2.0,
                  LEAD_RELIEF_D + 0.02))
          for side in (-1.0, 1.0)],
        # BEARING SEAT in the far cap. upper_arm's stub runs in a 608ZZ
        # rather than in a printed bore — plastic on plastic binds and wears
        # oval. Seated flush with the cap's outer face; it clears the MG995's
        # case by 1.5 mm, which is the tightest thing in this part.
        cast(Part, axis * Pos(0, y1 - BEARING_SEAT_DEPTH / 2, 0)
             * Rotation(90, 0, 0)
             * Cylinder(BEARING_SEAT_DIA / 2, BEARING_SEAT_DEPTH)),
        # and a clearance bore behind it so the stub can pass right through
        cast(Part, axis * Pos(0, y1 - BEARING_SEAT_DEPTH - 2.0, 0)
             * Rotation(90, 0, 0)
             * Cylinder(idler_dia / 2 + 1.0, 6.0)),
    ]
    for sx, sy in servo.tab_holes():
        cuts.append(cast(
            Part,
            axis * Pos(sx, y0 + drum_wall_thickness / 2, sy)
            * Rotation(90, 0, 0)
            * Cylinder(servo.pilot_dia / 2, drum_wall_thickness + 0.5),
        ))
    body = cast(Part, body - cuts)

    # --- phase 3: finish — elephant's foot on the race face
    bed = [
        e for e in body.edges().filter_by(GeomType.CIRCLE)
        if abs(e.center().Z) < 0.01
        and abs(e.radius - disc_dia / 2) < 0.01  # type: ignore[attr-defined]
    ]
    if bed:
        body = cast(Part, chamfer(bed, ELEPHANT_FOOT_CHAMFER_MM))
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"shoulder_bracket: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.0f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
