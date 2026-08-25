"""handrail saddle gauge — 15-minute fit prototype for rail_bracket.

A thin slice of the bracket's saddle ring, nothing else. Slide it onto the
rail: it must pass over the rail's 7 mm end arcs and slide without rattle.
Bore geometry comes from rail_bracket.bore_dims(), so this gauge always
matches the current bracket — reprint it after any bore change.

Prints flat on the bed, no supports, single nozzle, ~10-15 min in PETG
(same material as the bracket, so the fit transfers).
"""

from pathlib import Path
from typing import cast

from build123d import Axis, Part, RectangleRounded, Sketch, chamfer, extrude

from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM
from models.handrail.rail_bracket import bore_dims

PART_METADATA = {"expected_solids": 1}


def build(
    depth: float = 4.0,          # along the rail — enough to feel the fit
    ring_wall: float = 4.0,      # same as the bracket default
    rail_long_axis: str = "horizontal",
) -> Part:
    bore_y, bore_z, bore_r = bore_dims(rail_long_axis)
    ring = cast(
        Sketch,
        RectangleRounded(bore_y + 2 * ring_wall, bore_z + 2 * ring_wall,
                         bore_r + ring_wall)
        - RectangleRounded(bore_y, bore_z, bore_r),
    )
    body = extrude(ring, depth)
    body = chamfer(body.edges().group_by(Axis.Z)[0], ELEPHANT_FOOT_CHAMFER_MM)
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "handrail"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "saddle_gauge_v2.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "saddle_gauge_v2.3mf"))
    bb = part.bounding_box()
    print(f"volume {part.volume / 1000:.2f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
