"""deskmount clamp_shim — C-channel shim so a monitor-arm clamp grips a
thin (~22 mm) desk.

Spec: specs/deskmount/clamp_shim.md. Wraps the desk edge: web at the edge
face, top plate under the clamp foot, bottom plate over the screw pad.
Raises the clamped stack to desk + 2 plates (38 mm) and spreads the
60 x 60 foot / O10 screw pad over the full plate area.

Frame: X along the desk edge (part width), Y into the desk from the edge
(web at Y=0), Z vertical (slot bottom face at Z=plate_thickness).

Print: standing on an X end face (profile on the bed, extrude axis
vertical) — no supports, and plate bending under clamp load stays within
layers.
"""

from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Part,
    Plane,
    Pos,
    Rectangle,
    Sketch,
    chamfer,
    extrude,
    fillet,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    SLIDING_FIT_CLEARANCE_MM,
)

PART_METADATA = {"expected_solids": 1}

# Interface constants from the spec — not tunables.
DESK_THICKNESS_MM = 22.0     # GAUGE-FIT: sweep showed 22.5 mm gap snug =
                             # 22.0 + 2x sliding clearance (was 23 estimate)
CLAMP_FOOT_MM = 60.0         # top jaw contact, 60 x 60 (MEASURED)
SCREW_PAD_DIA_MM = 10.0      # bottom screw pad (MEASURED)
THROAT_DEPTH_MM = 79.0       # desk edge -> screw center; gauge v2: pad fell
                             # ~10 mm past the 74 mm tip (was 40, crude)


def clamped_stack_mm(
    top_plate_thickness: float = 4.0, bottom_plate_thickness: float = 12.0
) -> float:
    """Total thickness the clamp jaw must span once the shim is fitted."""
    return DESK_THICKNESS_MM + top_plate_thickness + bottom_plate_thickness


def build(
    width: float = 100.0,                 # along the desk edge; spreads the load
    top_plate_thickness: float = 4.0,     # under the 60x60 foot (pre-spread load)
    bottom_plate_thickness: float = 12.0,  # over the O10 pad — does the spreading;
                                           # doubled at user request (safety)
    web_thickness: float = 6.0,           # edge face joining the plates
    plate_depth: float = 82.0,            # plate reach past the web, into the desk
    lead_in_chamfer: float = 1.5,         # slot mouth, to slide onto the desk
    corner_fillet: float = 3.0,           # outer web corners, comfort/cosmetic
    edge_chamfer: float = 1.0,            # remaining outer profile corners
    slot_gap: float | None = None,        # calibration override; None = desk
                                          # thickness + sliding clearance
) -> Part:
    # The clamp sits against the shim's web; plates must fully cover the
    # screw pad. (Gauge v2 showed the foot is NOT centred on the screw — it
    # sits toward the clamp front, so pad coverage is the binding reach.)
    reach_needed = THROAT_DEPTH_MM - web_thickness + SCREW_PAD_DIA_MM / 2
    if plate_depth < reach_needed:
        raise ValueError(
            f"plate_depth {plate_depth} leaves the clamp unsupported — "
            f"needs >= {reach_needed:.1f} mm"
        )

    slot_h = (slot_gap if slot_gap is not None
              else DESK_THICKNESS_MM + 2 * SLIDING_FIT_CLEARANCE_MM)
    total_y = web_thickness + plate_depth
    total_z = top_plate_thickness + bottom_plate_thickness + slot_h

    # --- phase 1: base — C profile in YZ (sketch x -> Y, y -> Z), extruded
    # along X; bottom plate at Z=0, top plate above the slot. Slot cut runs
    # past the plate tips so the mouth is open.
    slot_z = bottom_plate_thickness + slot_h / 2
    outer = cast(
        Sketch,
        Pos(total_y / 2, total_z / 2) * Rectangle(total_y, total_z),
    )
    web_corners = outer.vertices().filter_by(lambda v: v.X < 0.01)
    outer = cast(Sketch, fillet(web_corners, corner_fillet))
    slot = Pos(web_thickness + plate_depth / 2 + 1, slot_z) * Rectangle(
        plate_depth + 2, slot_h
    )
    body = extrude(Plane.YZ * cast(Sketch, outer - slot), width)

    # --- phase 2: features — lead-in chamfer on the two slot-mouth edges
    mouth = [
        e for e in body.edges().filter_by(Axis.X)
        if abs(e.center().Y - total_y) < 0.01
        and bottom_plate_thickness - 0.01
        < e.center().Z
        < bottom_plate_thickness + slot_h + 0.01
    ]
    body = chamfer(mouth, lead_in_chamfer)

    # --- phase 3: finish — soften remaining outer profile corners (plate
    # tip outer edges), then elephant's foot on the bed face (x = 0 end)
    tips = [
        e for e in body.edges().filter_by(Axis.X)
        if abs(e.center().Y - total_y) < 0.01
        and (e.center().Z < 0.01 or e.center().Z > total_z - 0.01)
    ]
    body = chamfer(tips, edge_chamfer)

    bed_edges = body.edges().group_by(Axis.X)[0]
    body = chamfer(bed_edges, ELEPHANT_FOOT_CHAMFER_MM)

    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "deskmount"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "clamp_shim_v4.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "clamp_shim_v4.3mf"))
    bb = part.bounding_box()
    print(f"clamped stack {clamped_stack_mm():.1f} mm, "
          f"volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
