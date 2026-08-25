"""trellis antler-upper — upper antler segment (prints twice, mirrored).

Spec: specs/trellis/antler_trellis.md. Beam from the mid-antler split to the
tip with three tines, press-fit spigot (+ CA glue) into the hub's socket.
`build(mirror=True)` is the left antler; geometry is in assembly position,
the slicer lays it flat.

Frame: see models/trellis/_antler_common.py.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import Part

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _antler_common import upper_antler  # noqa: E402

PART_METADATA = {"expected_solids": 1, "needs_support_material": True}


def build(antler_length: float = 500.0, mirror: bool = False) -> Part:
    return cast(Part, upper_antler(antler_length, mirror))


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "exports" / "trellis"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    for mirror, side in ((False, "right"), (True, "left")):
        part = build(mirror=mirror)
        export_step(part, str(out / f"antler_upper_{side}_v3.step"))
        m = Mesher()
        m.add_shape(part)
        m.write(str(out / f"antler_upper_{side}_v3.3mf"))
        bb = part.bounding_box()
        print(f"{side}: volume {part.volume / 1000:.1f} cm^3, "
              f"mass(PLA) {part.volume / 1000 * 1.24:.1f} g, "
              f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
              f"solids {len(part.solids())}, valid {part.is_valid}")
