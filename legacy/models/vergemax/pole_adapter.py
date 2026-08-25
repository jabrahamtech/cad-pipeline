"""vergemax pole_adapter — screws the amaran Verge desk-clamp POLE straight
onto a Neewer ST-200 light stand, replacing the clamp base (and the whole
clamp_bar fake-desk-edge design).

The desk clamp is two parts: the pole (with the Verge Lock head) screws
into the clamp base via a proprietary fine thread. This puck replicates
the base's female thread on top of the proven stand receiver: 5/8" stud
socket + captive 1/4"-20 nut below (lib/stand_socket), threaded socket for
the pole above. Pole shoulder (O30, MEASURED) seats on the top face.

Pole thread: pitch 1.0 single start (photo pixel analysis, thread_gauge
docstring has the math); likely nominal M28x1.0 — the O27.5 caliper crest
reading runs low on fine threads. Bore major comes from the thread_gauge
v2 diameter sweep (28.3/28.7/29.1): set `thread_clearance` so
POLE_THREAD_CREST_MM + thread_clearance equals the winning ring's major.

Frame: Z up as installed, Z=0 at the bottom (stand shoulder contact).
Print: upright, bottom face on bed — both bores' steps widen upward
(self-supporting), the only bridge is the 16 mm web over the socket, and
the load-bearing thread prints cleanly with its axis vertical. 0.1 mm
layers recommended for the fine pitch.

Load path: light's moment enters through the printed thread (~2 MPa at
the body section vs ~30 MPa PETG) into the steel stud. Fine-pitch teeth
are ~0.7 mm — below the 0.8 mm feature rule, hence the gauge-ring check.

Hardware (BOUGHT): 1x 1/4"-20 hex nut; optional M3 heat-set + M3x8 screw
rotation lock.
"""

from pathlib import Path
from typing import cast

from bd_warehouse.thread import IsoThread
from build123d import Axis, Box, Cylinder, GeomType, Part, Pos, Rot, chamfer

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    M3_INSERT_HOLE_DIA_MM,
)
from lib.stand_socket import NUT_AC_MM, stud_socket_negative

PART_METADATA = {"expected_solids": 1}

# Interface constants from the spec — not tunables.
POLE_THREAD_CREST_MM = 27.5   # male thread on the pole (MEASURED)
POLE_THREAD_LEN_MM = 12.0     # MEASURED
POLE_SHOULDER_DIA_MM = 30.0   # seats on the adapter top face (MEASURED)


def build(
    pole_pitch: float = 1.0,        # photo-confirmed, single start
    body_dia: float = 40.0,         # > shoulder O30; thread wall ~6 mm
    thread_clearance: float = 1.2,  # diametral vs measured crest; CONFIRM
                                    # with thread_gauge v2 ring sweep
    thread_socket_depth: float = 13.0,   # pole thread 12 + bottom clearance
    passage_dia: float = 20.0,      # nut drop-through / finger reach to pocket
    passage_len: float = 2.3,       # pocket top -> thread socket floor
    include_m3_lock: bool = False,  # optional rear-flat rotation lock
    flat_depth: float = 2.0,        # rear facet for the M3 lock insert
    m3_lock_z: float = 12.0,        # lock screw height on the socket
) -> Part:
    socket_neg, pocket_top = stud_socket_negative()
    thread_major = POLE_THREAD_CREST_MM + thread_clearance
    thread_floor = pocket_top + passage_len
    total_h = thread_floor + thread_socket_depth
    if body_dia < POLE_SHOULDER_DIA_MM + 2:
        raise ValueError(
            f"body_dia {body_dia} leaves no seat for the O"
            f"{POLE_SHOULDER_DIA_MM} pole shoulder"
        )

    # --- phase 1: base — plain puck (rear flat only if the M3 lock is wanted)
    body = cast(Part, Pos(0, 0, total_h / 2) * Cylinder(body_dia / 2, total_h))
    flat_y = -(body_dia / 2 - flat_depth)
    if include_m3_lock:
        body -= Pos(0, flat_y - 5, 10) * Box(body_dia, 10, 20)

    # --- phase 2: features — stand receiver below, nut passage, threaded
    # pole socket above, M3 lock hole through the flat
    body -= socket_neg
    body -= Pos(0, 0, (pocket_top + thread_floor) / 2) * Cylinder(
        passage_dia / 2, passage_len
    )
    body -= Pos(0, 0, (thread_floor + total_h) / 2) * Cylinder(
        thread_major / 2, thread_socket_depth
    )
    thread = IsoThread(
        major_diameter=thread_major,
        pitch=pole_pitch,
        length=thread_socket_depth,
        external=False,
        end_finishes=("fade", "fade"),
    )
    body += Pos(0, 0, thread_floor) * thread
    if include_m3_lock:
        body -= (
            Pos(0, flat_y - 1, m3_lock_z)
            * Rot(90, 0, 0)
            * Cylinder(M3_INSERT_HOLE_DIA_MM / 2, 18)
        )

    # --- phase 3: finish — stud lead-in at the socket mouth, elephant's
    # foot on the remaining bed edges, top rim chamfer
    circles_at = lambda z: (
        body.edges()
        .filter_by(GeomType.CIRCLE)
        .filter_by(lambda e: abs(e.center().Z - z) < 0.01)
    )
    body = chamfer(
        circles_at(0.0).filter_by(lambda e: e.radius < body_dia / 2 - 4), 1.0
    )
    bed_rim = (
        body.edges()
        .group_by(Axis.Z)[0]
        .filter_by(lambda e: e.geom_type is not GeomType.CIRCLE
                   or e.radius > body_dia / 2 - 3)
    )
    body = chamfer(bed_rim, ELEPHANT_FOOT_CHAMFER_MM)
    body = chamfer(
        circles_at(total_h).filter_by(
            lambda e: abs(e.radius - body_dia / 2) < 0.01
        ),
        1.0,
    )

    assert passage_dia > NUT_AC_MM + 0.8, "nut cannot drop through the passage"
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "vergemax"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    export_step(part, str(out / "pole_adapter_v4.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "pole_adapter_v4.3mf"))
    bb = part.bounding_box()
    print(
        f"volume {part.volume / 1000:.1f} cm^3, "
        f"mass(PETG solid) {part.volume / 1000 * 1.27:.0f} g, "
        f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
        f"solids {len(part.solids())}, valid {part.is_valid}"
    )
