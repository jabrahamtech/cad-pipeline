"""vergemax clamp_bar — fake desk edge on a Neewer ST-200 light stand so the
amaran Verge Lock Desk Clamp Stand (and the Verge Max on it) mounts to the
stand. The metal amaran clamp keeps carrying the light; this part is a rigid
plate the clamp grips, locked onto the stand's 5/8" stud.

Spec: specs/vergemax/clamp_bar.md. The stand's 5/8" stud (O15.9, 31 mm)
seats in a socket under the plate; its 1/4"-20 threaded tip (5 mm) passes
through a thin web and engages a captive 1/4"-20 hex nut dropped into a
pocket, so the whole bar screws down onto the stud shoulder. An optional M3
heat-set + screw in the boss rear flat locks rotation against the stud.

Frame: Z up as installed, Z=0 at the boss bottom (stand shoulder contact).
+Y is the FRONT edge the clamp slides onto; the boss sits near the rear so
the clamp's lower jaw clears it.

Print: plate top face on the bed (part upside down) — socket, pocket and
access bore all open upward in print, no supports, single nozzle. Bending
at the boss root is ~2 MPa vs PETG's ~30 MPa even across layers, and most
of the moment passes through the steel stud to the shoulder anyway.

Hardware (BOUGHT): 1x 1/4"-20 hex nut (captive, drop-in); optional M3
heat-set insert + M3x8 screw for the rotation lock.
"""

from pathlib import Path
from typing import cast

from build123d import (
    Axis,
    Box,
    Cylinder,
    GeomType,
    Part,
    Pos,
    Rot,
    chamfer,
    fillet,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    M3_INSERT_HOLE_DIA_MM,
    SLIDING_FIT_CLEARANCE_MM,
)
from lib.stand_socket import stud_socket_negative

PART_METADATA = {"expected_solids": 1}

# Interface constants from the spec — not tunables.
STUD_DIA_MM = 15.9        # Neewer ST-200 5/8" stud (MEASURED)
STUD_LEN_MM = 31.0        # 5/8" section, shoulder to shoulder (MEASURED)
TIP_THREAD_LEN_MM = 5.0   # exposed 1/4"-20 tip (MEASURED)
CLAMP_JAW_MIN_MM = 20.0   # amaran clamp desk-thickness range (DATASHEET)
CLAMP_JAW_MAX_MM = 70.0
# 1/4"-20 nut dimensions live in lib/stand_socket.py


def build(
    plate_width: float = 100.0,      # X, along the fake desk edge; covers pads
    plate_depth: float = 100.0,      # Y, clamp slide-in direction
    plate_thickness: float = 30.0,   # mid-range of the 20-70 mm clamp jaw
    plate_corner_radius: float = 8.0,
    boss_dia: float = 32.0,          # socket wall ~7.7 mm each side
    boss_height: float = 20.0,       # socket continues into the plate to 31 mm
    boss_rear_offset: float = 20.0,  # boss centre from rear edge; keeps the
                                     # front 64 mm of underside clear for the jaw
    web_thickness: float = 2.0,      # over the socket; tip protrudes 3 mm
                                     # into the nut for ~2.4 thread engagement
    nut_pocket_fit: float = 0.3,     # extra across flats, drop-in captive
    access_bore_dia: float = 22.0,   # finger room to seat the nut in its pocket
    junction_fillet: float = 3.0,    # boss-to-plate root
    lead_in_chamfer: float = 2.0,    # plate underside perimeter, jaw slide-on
    socket_clearance: float = SLIDING_FIT_CLEARANCE_MM,  # diametral, on stud
    require_jaw_clearance: bool = True,  # gauge stubs opt out of the throat check
) -> Part:
    # The clamp's lower jaw sweeps under the plate from the front; it must
    # reach full pad contact before anything hits the boss.
    front_clear = plate_depth - boss_rear_offset - boss_dia / 2
    if require_jaw_clearance and front_clear < 50.0:
        raise ValueError(
            f"only {front_clear:.0f} mm of clear underside ahead of the boss "
            f"— the clamp jaw will bottom on the boss; deepen the plate or "
            f"push the boss further rearward"
        )
    if not CLAMP_JAW_MIN_MM < plate_thickness < CLAMP_JAW_MAX_MM:
        raise ValueError(
            f"plate_thickness {plate_thickness} outside the clamp's "
            f"{CLAMP_JAW_MIN_MM}-{CLAMP_JAW_MAX_MM} mm jaw range"
        )

    boss_y = -plate_depth / 2 + boss_rear_offset   # front edge is +Y
    total_h = boss_height + plate_thickness

    # --- phase 1: base — plate on boss, rear flat for the M3 rotation-lock
    # insert (cut BEFORE the root fillet so the fillet stays clear of the
    # rear lead-in chamfer), then filleted root
    plate = Pos(0, 0, boss_height + plate_thickness / 2) * Box(
        plate_width, plate_depth, plate_thickness
    )
    plate = fillet(
        plate.edges().filter_by(Axis.Z), plate_corner_radius
    )
    boss = Pos(0, boss_y, boss_height / 2) * Cylinder(boss_dia / 2, boss_height)
    body = cast(Part, plate + boss)
    # flat facet on the boss rear so the heat-set insert seats on a plane
    flat_y = boss_y - (boss_dia / 2 - 2.0)   # 2 mm deep facet
    body -= Pos(0, flat_y - 5, boss_height / 2) * Box(
        boss_dia, 10, boss_height
    )
    root = (
        body.edges()
        .filter_by(GeomType.CIRCLE)
        .filter_by(lambda e: abs(e.center().Z - boss_height) < 0.01)
        .filter_by(lambda e: abs(e.radius - boss_dia / 2) < 0.01)
    )
    body = fillet(root, junction_fillet)

    # --- phase 2: features — stand receiver (socket + tip hole + captive-nut
    # pocket, lib/stand_socket), access bore, M3 rotation-lock hole
    socket_neg, pocket_top = stud_socket_negative(
        stud_dia=STUD_DIA_MM,
        stud_len=STUD_LEN_MM,
        web_thickness=web_thickness,
        nut_pocket_fit=nut_pocket_fit,
        socket_clearance=socket_clearance,
    )
    at_boss = Pos(0, boss_y, 0)
    body -= at_boss * socket_neg
    body -= at_boss * Pos(0, 0, (pocket_top + total_h) / 2) * Cylinder(
        access_bore_dia / 2, total_h - pocket_top  # nut drops in, finger-seatable
    )
    body -= (
        Pos(0, flat_y - 1, 12.0)
        * Rot(90, 0, 0)
        * Cylinder(M3_INSERT_HOLE_DIA_MM / 2, 18)
    )

    # --- phase 3: finish — jaw lead-in on the plate underside perimeter,
    # stud lead-in + rim on the boss bottom, elephant's foot on the bed face
    # (plate top — the part prints upside down)
    def is_perimeter(e) -> bool:
        """Plate-underside outline only — not the root-fillet tangent circle
        or the flat-facet junction line, both of which hug the boss."""
        c = e.center()
        if abs(c.Z - boss_height) > 0.01:
            return False
        boss_dist = ((c.X) ** 2 + (c.Y - boss_y) ** 2) ** 0.5
        return boss_dist > boss_dia / 2 + junction_fillet + 2 or (
            abs(c.Y - plate_depth / 2) < 0.01 or abs(abs(c.Y) - plate_depth / 2) < 0.01
        ) and abs(c.Y - flat_y) > 1.0

    underside = body.edges().filter_by(is_perimeter)
    body = chamfer(underside, lead_in_chamfer)
    body = chamfer(body.edges().group_by(Axis.Z)[0], 0.8)
    body = chamfer(body.edges().group_by(Axis.Z)[-1], ELEPHANT_FOOT_CHAMFER_MM)

    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "vergemax"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "clamp_bar_v3.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "clamp_bar_v3.3mf"))
    bb = part.bounding_box()
    print(
        f"volume {part.volume / 1000:.1f} cm^3, "
        f"mass(PETG solid) {part.volume / 1000 * 1.27:.0f} g, "
        f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
        f"solids {len(part.solids())}, valid {part.is_valid}"
    )
