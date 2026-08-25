"""robotarm turntable_clip — hold-down that stops the turntable lifting off
its rollers. PRINT THREE.

Spec: specs/robotarm/turntable_clip.md. Frame: LOCAL — the origin is where
the clip's screw enters turret_cap's OUTER FACE, at radius CLIP_R and global
height Z_FLANGE. +X points radially OUTWARD, +Z up, so z = 0 is the cap's top
face and the disc sits above it.

WHY THIS EXISTS. The three 608ZZ rollers only push UP. With the arm extended
the combined centre of mass of bracket + servo + arm leaves the roller circle
— 45.7 mm out against a 36 mm circle, 60.4 mm with a payload — so the disc
tips onto two rollers and lifts off the third. Without a hold-down the only
thing resisting that is the base servo's horn screw, which puts roughly 2.2 N
of axial pull straight into the output shaft the rollers were fitted to
unload; and any lift shows up as rock, magnified about four times by the time
it reaches the gripper.

WHY IT BOLTS RADIALLY. The gap between the Ø96 disc and the Ø104 cap is a
4 mm annulus — nowhere near enough for an M3 boss on the cap's top face. Come
at the cap from the side and there are 12 mm of solid plate. It also means a
cap that has already been printed can take these by drilling three holes,
with no reprint.

Fitted after the disc is on, not moulded into the cap: fixed hooks would need
a bayonet slot in the rim, and that would cap base rotation at about ±50°.

Print: on its side, the profile flat on the bed, so the tongue is not an
overhang. PETG, 40 % infill, 3 walls.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Cylinder,
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    CLIP_LIFT_GAP,
    CLIP_OVERLAP_R,
    CLIP_R,
    CLIP_SCREW_Z,
    TURNTABLE_DIA,
    TURNTABLE_T,
    Z_FLANGE,
    Z_RACE,
)

PART_METADATA = {"expected_solids": 1}

M3_CLEAR_DIA = 3.4


def build(
    width: float = 15.0,             # across the clip, tangential
    pad_thickness: float = 6.5,      # sits against the cap's outer face
    tongue_thickness: float = 4.0,   # the bit that overhangs the disc
    pad_below: float = 11.0,         # pad reach below the cap's top face
    pad_above: float = 2.5,
    bolt_clear_dia: float = M3_CLEAR_DIA,
    disc_dia: float = TURNTABLE_DIA,
    disc_thickness: float = TURNTABLE_T,
    lift_gap: float = CLIP_LIFT_GAP,
    overlap_r: float = CLIP_OVERLAP_R,
    edge_chamfer: float = 0.8,
) -> Part:
    disc_top = (Z_RACE + disc_thickness) - Z_FLANGE     # 18.2 above cap top
    tongue_z = disc_top + lift_gap
    top = tongue_z + tongue_thickness

    x_in = -(CLIP_R - overlap_r)          # tongue's inner tip, going inward
    x_rim = -(CLIP_R - disc_dia / 2)      # where the disc's rim sits
    if x_in >= x_rim:
        raise ValueError(
            f"tongue reaches r={overlap_r} but the disc rim is at "
            f"r={disc_dia / 2} — it would not overlap"
        )

    # --- phase 1: base shape — pad and post outboard, tongue reaching in
    profile = cast(Sketch, make_face(Polyline(
        (0.0, -pad_below),
        (pad_thickness, -pad_below),
        (pad_thickness, top),
        (x_in, top),
        (x_in, tongue_z),
        (0.0, tongue_z),
        (0.0, pad_above),
        (0.0, -pad_below),
        close=True,
    )))
    body = cast(Part, extrude(Plane.XZ.offset(-width / 2) * profile, width))

    # --- phase 2: the radial screw, clearance only — the insert is in the cap
    body = cast(Part, body - (
        Pos(-2.0, 0, CLIP_SCREW_Z) * Rotation(0, 90, 0)
        * Cylinder(bolt_clear_dia / 2, pad_thickness + 8.0)))

    # --- phase 3: finish — break the lip that passes over the turning disc
    lip = [e for e in body.edges().filter_by(Axis.Y)
           if abs(e.center().X - x_in) < 0.01
           and abs(e.center().Z - tongue_z) < 0.01]
    if lip:
        try:
            body = cast(Part, chamfer(lip, edge_chamfer))
        except Exception:
            pass
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"turntable_clip (PRINT 3): volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
    print(f"  screw enters the cap {abs(CLIP_SCREW_Z):.0f} mm below its top "
          f"face, at r={CLIP_R:.0f}")
    print(f"  tongue sits {CLIP_LIFT_GAP} mm over the disc, overlapping its "
          f"rim by {TURNTABLE_DIA / 2 - CLIP_OVERLAP_R:.1f} mm")
