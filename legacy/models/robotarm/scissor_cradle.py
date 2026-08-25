"""robotarm scissor_cradle — holds a pair of scissors in the wrist clevis:
a zip-tied trough for the fixed handle loop and a V-notch post under the
pivot boss, leaving the free handle clear to swing.

Spec: specs/robotarm/scissor_cradle.md.

ALL SCISSOR DIMENSIONS ARE ASSUMED (generic 170 mm office scissors, no
calipers on the real pair yet). Every scissor-facing dimension is a build()
parameter carrying the assumed default:
    handle_loop_length    45.0   fixed handle loop, along the trough
    handle_loop_width     30.0   across the trough
    handle_loop_thickness  6.0   loop material thickness = trough wall height
    pivot_boss_dia        12.0   the rivet boss the V-notch grips
    pivot_offset          55.0   loop centre -> pivot, along the trough
    free_handle_travel    30.0   how far the free handle sweeps, closed->open
Re-measure these before printing v2.

FRAME: LOCAL. The bed face is z = 0 and the part grows +Z; +X runs along the
scissors toward the pivot and the blades (so -X is proximal, toward the
wrist), and +Y is the side the FREE handle swings on.

HOW IT HOLDS
  - Trough: floor at base_thickness, two walls exactly handle_loop_thickness
    tall. The fixed loop drops in flat. The walls are deliberately no taller
    than the loop, because real scissors' handles sit in two parallel planes
    (offset by the blade stack) — the free handle rides OVER these walls as
    it sweeps, so nothing may stand above the trough floor + loop thickness
    anywhere on the +Y side.
  - Zip ties: two transverse channels, ziptie_slot_l x ziptie_slot_d, run
    right through the base plate under both walls and open into the trough
    floor as grooves. A tie lies in the groove, comes up the outside of both
    walls and over the loop. Nothing is glued; the scissors lift straight out
    when the ties are cut.
  - V-notch post: a 90 deg vee cut into a post at pivot_offset, opening back
    toward the handles. The pivot boss wedges into it, which is what stops
    the scissors rotating in the trough while the lever pushes.
  - A MOUNTING FLANGE on the proximal (-X) end: a disc normal to X with the
    same four M3 on a Ø22 circle the hand uses, so the two effectors swap on
    wrist_rotator by construction rather than by agreement. The wrist is a
    ROLL joint now, so the scissors turn about their own long axis rather
    than pitching.

PRINT: flat on the bed face (z = 0), trough up, no support. The only bridges
are the two wall sections over the zip-tie channels (ziptie_slot_l wide) and
the two Ø3.4 pin holes. PETG, 30 % infill.

HONESTY: the SG90 effector gives ~0.7 kg at a 25 mm lever. This part holds
the scissors; it cannot make them lighter to squeeze. If the blades do not
close, that is the servo, not the cradle.
"""

import math
import sys
from pathlib import Path
from typing import cast

from build123d import Axis, Box, Cylinder, Part, Pos, Rotation, chamfer

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM, MIN_WALL_MM

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    EFFECTOR_BOLT_AZ,
    EFFECTOR_BOLT_CLEAR_DIA,
    EFFECTOR_BOLT_R,
)

PART_METADATA = {"expected_solids": 1}

# The trough's own length fixes where the flange sits, and _assembly and
# tests/test_robotarm.py both place the cradle off FLANGE_X — so the part
# and everything that positions it cannot disagree.
HANDLE_LOOP_LENGTH = 45.0        # ASSUMED, see the docstring
TROUGH_OVERHANG = 10.0
FLANGE_X = -(HANDLE_LOOP_LENGTH + TROUGH_OVERHANG) / 2
FLANGE_R = 16.0
FLANGE_T = 4.0
# The roll axis has to run through the flange's centre AND sit high enough
# that the lowest bolt hole does not break out of the bed face.
ROLL_AXIS_Z = 11.0


def build(
    # --- scissors (ALL ASSUMED — see module docstring)
    handle_loop_length: float = HANDLE_LOOP_LENGTH,
    handle_loop_width: float = 30.0,
    handle_loop_thickness: float = 6.0,
    pivot_boss_dia: float = 12.0,
    pivot_offset: float = 55.0,
    free_handle_travel: float = 30.0,
    # --- cradle
    trough_width: float = 32.0,        # loop 30 + 2 slack
    trough_wall: float = 3.0,
    trough_wall_height: float = 6.0,   # must not exceed the loop thickness
    trough_overhang: float = TROUGH_OVERHANG,   # trough longer than the loop
    base_thickness: float = 6.0,
    # --- wrist_rotator interface (shared with hand_base, via _frame)
    flange_radius: float = FLANGE_R,
    flange_thickness: float = FLANGE_T,
    axis_z: float = ROLL_AXIS_Z,
    bolt_r: float = EFFECTOR_BOLT_R,
    bolt_az: tuple[float, ...] = EFFECTOR_BOLT_AZ,
    bolt_clear_dia: float = EFFECTOR_BOLT_CLEAR_DIA,
    # --- zip ties
    ziptie_slot_l: float = 5.0,
    ziptie_slot_d: float = 2.5,
    ziptie_offset_x: float = 17.0,
    # --- pivot post
    post_half_width: float = 16.0,
    post_back_wall: float = 5.0,
    notch_half_width: float = 12.0,
    edge_chamfer: float = 1.0,
) -> Part:
    half_w = trough_width / 2 + trough_wall
    trough_len = handle_loop_length + trough_overhang
    trough_x = trough_len / 2
    flange_x = -trough_x
    wall_h = trough_wall_height             # see docstring: free-handle sweep
    top_z = base_thickness + wall_h
    # 90 deg vee: a circle of radius r touching both faces sits sqrt(2)*r
    # back from the apex, so put the apex here and the boss lands on pivot.
    apex_x = pivot_offset + pivot_boss_dia / 2 * math.sqrt(2.0)
    post_x0 = pivot_offset - pivot_boss_dia / 2 - 2.0
    post_x1 = apex_x + post_back_wall

    # --- interface checks
    if trough_width < handle_loop_width + 1.0:
        raise ValueError(
            f"trough_width {trough_width} will not take a "
            f"{handle_loop_width} mm loop"
        )
    if base_thickness - ziptie_slot_d < MIN_WALL_MM:
        raise ValueError("zip-tie channel leaves too little floor below it")
    if wall_h > handle_loop_thickness:
        raise ValueError(
            f"trough walls stand {wall_h} mm proud but the free handle sweeps "
            f"{free_handle_travel} mm across the +Y side at "
            f"{handle_loop_thickness} mm above the floor — it would foul"
        )
    if post_x0 < trough_x + MIN_WALL_MM:
        raise ValueError("pivot post collides with the trough")
    if apex_x - 2 * notch_half_width > post_x0:
        raise ValueError(
            "vee notch does not reach the front of the post — the boss "
            "cannot enter; raise notch_half_width"
        )
    if notch_half_width > post_half_width - MIN_WALL_MM:
        raise ValueError("vee notch breaks out of the sides of the post")
    if axis_z - bolt_r * 0.708 - bolt_clear_dia / 2 < 0.8:
        raise ValueError(
            "the lowest flange bolt breaks out of the bed face — raise axis_z"
        )

    # --- phase 1: base shape — trough base + walls, spine, pivot post
    prims: list[Part] = [
        cast(Part, Pos(0, 0, base_thickness / 2)
             * Box(trough_len, 2 * half_w, base_thickness)),
        cast(Part, Pos((trough_x + post_x0) / 2, 0, base_thickness / 2)
             * Box(post_x0 - trough_x, 2 * post_half_width, base_thickness)),
        cast(Part, Pos((post_x0 + post_x1) / 2, 0, top_z / 2)
             * Box(post_x1 - post_x0, 2 * post_half_width, top_z)),
    ]
    for sy in (-1.0, 1.0):
        prims.append(cast(
            Part,
            Pos(0, sy * (half_w - trough_wall / 2), base_thickness + wall_h / 2)
            * Box(trough_len, trough_wall, wall_h),
        ))
    body = cast(Part, Part() + prims)

    # --- phase 2: features — vee notch, bolts, zip-tie channels
    notch_box = notch_half_width * math.sqrt(2.0)
    cuts: list[Part] = [
        cast(Part, Pos(apex_x - notch_half_width, 0, top_z - wall_h / 2 + 0.5)
             * Rotation(0, 0, 45)
             * Box(notch_box, notch_box, wall_h + 1.0)),
    ]
    for sx in (-1.0, 1.0):
        cuts.append(cast(
            Part,
            Pos(sx * ziptie_offset_x, 0,
                base_thickness - ziptie_slot_d / 2 + 0.5)
            * Box(ziptie_slot_l, 2 * half_w + 2.0, ziptie_slot_d + 1.0),
        ))
    body = cast(Part, body - cuts)

    # --- phase 3: finish — break the trough mouth, elephant's foot on the bed
    try:
        mouth = [
            e for e in body.edges().filter_by(Axis.X)
            if abs(e.center().Z - top_z) < 0.01
            and abs(abs(e.center().Y) - half_w) < 0.01
        ]
        if mouth:
            body = cast(Part, chamfer(mouth, edge_chamfer))
    except Exception:  # OCC declines — cosmetic only
        pass
    try:
        body = cast(Part, chamfer(body.edges().group_by(Axis.Z)[0],
                                  ELEPHANT_FOOT_CHAMFER_MM))
    except Exception:
        pass
    # --- mounting flange: a disc normal to X on the proximal end, with the
    # same four M3 the hand uses. Truncated at the bed like every other
    # vertical disc on this machine.
    body = cast(Part, body + Pos(flange_x - flange_thickness / 2, 0, axis_z)
                * Rotation(0, 90, 0)
                * Cylinder(flange_radius, flange_thickness))
    for az in bolt_az:
        p = Rotation(0, 0, az) * Pos(bolt_r, 0, 0)
        body = cast(Part, body - Pos(
            flange_x - flange_thickness / 2, p.position.X,
            axis_z + p.position.Y)
            * Rotation(0, 90, 0)
            * Cylinder(bolt_clear_dia / 2, flange_thickness + 2.0))
    body = cast(Part, body - Pos(0, 0, -200) * Box(600, 600, 400))
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"scissor_cradle: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.0f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
    print("  every scissor dimension above is ASSUMED — measure before v2")
