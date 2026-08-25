"""trellis antler-hub — ring + mounting plate + both lower antler halves.

Spec: specs/trellis/antler_trellis.md. The stem tube slots into the tower's
Ø50 port (sliding fit); the flexible gyrocup then pushes into the ring bore
and wedges the trellis in place. A stadium plate spans the two antler bases
so the ring sits between the antlers; the plate seats flat on the tower wall.

Frame: see models/trellis/_antler_common.py (wall = XZ plane, port axis -Y).
"""

import sys
from pathlib import Path
from typing import cast

from build123d import Align, Box, Cone, Cylinder, Part, Plane

from lib.design_rules import SLIDING_FIT_CLEARANCE_MM

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _antler_common import lower_antler  # noqa: E402

PART_METADATA = {"expected_solids": 1, "needs_support_material": True}

_ALIGN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# Interface constants from the spec — not tunables.
PORT_HOLE_DIA_MM = 50.0   # tower port (ASSUMED nominal)
CUP_BORE_ID_MM = 45.5     # flexible Ø50 gyrocup wedges into this (ASSUMED)
STEM_DEPTH_MM = 45.0      # insertion depth into the port (ASSUMED)


def build(
    antler_length: float = 500.0,
    plate_span: float = 88.0,        # stadium plate overall width, ±X
    plate_height: float = 58.0,      # stadium plate height (= end cap dia)
    plate_thickness: float = 4.0,
    bore_lead_chamfer: float = 1.5,  # cup lead-in at the bore mouth
) -> Part:
    stem_od = PORT_HOLE_DIA_MM - SLIDING_FIT_CLEARANCE_MM
    cap_r = plate_height / 2
    cap_x = plate_span / 2 - cap_r

    # --- phase 1: base — stadium plate (y 0..t) + stem tube (y -depth..0)
    plate = cast(Part, Box(2 * cap_x, plate_thickness, plate_height,
                           align=(Align.CENTER, Align.MIN, Align.CENTER)))
    for sx in (-1, 1):
        plate += Plane(
            origin=(sx * cap_x, 0, 0), z_dir=(0, 1, 0)
        ) * Cylinder(cap_r, plate_thickness, align=_ALIGN_MIN)
    tube = Plane(origin=(0, 0, 0), z_dir=(0, -1, 0)) * Cylinder(
        stem_od / 2, STEM_DEPTH_MM, align=_ALIGN_MIN)
    body = plate + tube

    # --- phase 2: features — both lower antler halves (sockets pre-cut),
    # then the through bore + cup lead-in chamfer cut LAST so nothing
    # re-enters the cup path
    body += [lower_antler(antler_length, mirror=m) for m in (False, True)]
    body -= Plane(
        origin=(0, -STEM_DEPTH_MM - 1, 0), z_dir=(0, 1, 0)
    ) * Cylinder(CUP_BORE_ID_MM / 2, STEM_DEPTH_MM + plate_thickness + 2,
                 align=_ALIGN_MIN)
    body -= Plane(
        origin=(0, plate_thickness, 0), z_dir=(0, -1, 0)
    ) * Cone(CUP_BORE_ID_MM / 2 + bore_lead_chamfer, CUP_BORE_ID_MM / 2,
             bore_lead_chamfer, align=_ALIGN_MIN)

    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "trellis"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "antler_hub_v3.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "antler_hub_v3.3mf"))
    bb = part.bounding_box()
    print(f"volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PLA) {part.volume / 1000 * 1.24:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
