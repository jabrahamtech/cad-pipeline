"""Receiver for a Neewer-style light-stand top: 5/8" stud with a 1/4"-20
threaded tip, retained by a captive 1/4"-20 hex nut.

Used by models/vergemax/{clamp_bar,pole_adapter}. The part screws down
onto the stud tip (nut captive in a hex pocket) until it bottoms on the
stud shoulder; the steel stud carries the bending moment.

`stud_socket_negative()` returns the cutter compound, built at the origin
with the socket mouth at Z=0 opening downward-in-use, plus the Z of the
pocket top so callers can stack their own access geometry above it.
"""

from typing import cast

from build123d import Cylinder, Part, Pos, RegularPolygon, Sketch, extrude

from lib.design_rules import SLIDING_FIT_CLEARANCE_MM

# 1/4"-20 hex nut, DATASHEET
NUT_AF_MM = 11.11     # across flats (7/16")
NUT_THICK_MM = 5.6
NUT_AC_MM = 12.83     # across corners
TIP_HOLE_DIA_MM = 7.0  # clearance for the 1/4" threaded tip


def stud_socket_negative(
    stud_dia: float = 15.9,        # Neewer ST-200, MEASURED
    stud_len: float = 31.0,        # MEASURED — total incl. base collar
    collar_dia: float = 21.0,      # MEASURED — bottom 4 mm of the stud is wider
    collar_len: float = 4.0,
    seat_slack: float = 0.3,       # counterbore step seats on the collar
                                   # shoulder; bottom face hovers this much
    web_thickness: float = 2.0,    # nut bears on this, backed by the steel stud
    nut_pocket_fit: float = 0.3,   # extra across flats, drop-in captive
    socket_clearance: float = SLIDING_FIT_CLEARANCE_MM,  # diametral
) -> tuple[Part, float]:
    """Cutter for counterbore + socket + tip hole + captive-nut pocket;
    also returns the pocket-top Z (stack access bores from there).

    Seating plane is the counterbore step on the collar's top shoulder, so
    the stud tip lands at stud_len + seat_slack regardless of collar fit.
    """
    socket_depth = stud_len + seat_slack
    web_top = socket_depth + web_thickness
    pocket_top = web_top + NUT_THICK_MM + 0.6
    socket = Pos(0, 0, socket_depth / 2) * Cylinder(
        (stud_dia + socket_clearance) / 2, socket_depth
    )
    counterbore = Pos(0, 0, (collar_len + seat_slack) / 2) * Cylinder(
        (collar_dia + socket_clearance) / 2, collar_len + seat_slack
    )
    tip_hole = Pos(0, 0, (socket_depth + web_top) / 2) * Cylinder(
        TIP_HOLE_DIA_MM / 2, web_thickness
    )
    hex_sk = cast(
        Sketch,
        Pos(0, 0, web_top)
        * RegularPolygon((NUT_AF_MM + nut_pocket_fit) / 2, 6, major_radius=False),
    )
    pocket = extrude(hex_sk, pocket_top - web_top)
    return cast(Part, socket + counterbore + tip_hole + pocket), pocket_top
