"""robotarm forearm — elbow-to-wrist link, enclosed at both joints.

Spec: specs/robotarm/forearm.md. Same object as upper_arm, one joint down the
chain: DRIVEN at the near end by the elbow MG90S's horn, holding the wrist
MG90S's CASE at the far end. So under the drum-and-skirt contract in
models/robotarm/_frame.py it carries skirts at the elbow and a drum at the
wrist, exactly as upper_arm does at the shoulder and the elbow.

    NEAR (elbow)  SKIRTS at _frame.skirt_inner_r(DRUM_R_ELBOW) ..
        skirt_outer_r (22.0 to 24.5), lapping upper_arm's elbow drum by
        _frame.SKIRT_LAP with 1 mm of running clearance. Its channel is
        _frame.ELBOW_CHANNEL_W, so the skirts run y ±11.5 to ±23.5. The
        idler stub reaches the elbow drum's far CAP, which is what puts the
        elbow in double shear.

    FAR (wrist)  NOTHING. It is a plain rectangular channel that stops
        square, with two cross-drilled M3 holes through both side plates.
        models/robotarm/wrist_mount.py is a saddle that slips over it from
        outside, bolts through those two holes and carries the wrist servo.

        That is deliberate. The wrist is the part of this machine most
        likely to change, and a bolt-on bracket can be re-cut on its own
        without reprinting a 28 cm^3 link. It also leaves the tip as the
        easiest shape in the whole project to print: two vertical walls and
        a floor, no drum, no flange, no servo pocket.

MATING NOTE, not something built into this part: the forearm's frame ends up
about 4.6 mm off upper_arm's in y. Its driven plate seats on the elbow horn,
which sits 17.5 + 10.6 = 28.1 from the elbow drum's centre, while this link's
own channel half width is 23.5. That difference is a fact of the assembly;
the forearm itself is built symmetric about its own y = 0.

The horn side is mirrored relative to upper_arm (+Y instead of -Y): the elbow
servo's horn faces -Y out of upper_arm, so the forearm meets it from the
other side and the chain assembles without flipping a printed part.

Both joints still leave an open fork between the plates — nothing bridges the
channel near either axis (see the joint-sweep rule in
models/robotarm/_link.py), and the skirts are clipped forward of the elbow
axis so their arc never sweeps back into upper_arm's far end as the elbow
folds.

Frame: see models/robotarm/_link.py. X = long axis (0 = elbow axis,
FOREARM_LEN = wrist axis), Y = both joint axes, Z up.

Print: flat on the bed exactly as modelled — channel opening up, both side
plates vertical, NO support material anywhere. The two cross-holes are short
horizontal bores whose crowns droop over the top millimetre; an M3 clearance
hole tolerates that. PETG, 4 walls, 25 % infill, bed face is the web.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import Cylinder, Part, Pos, Rotation

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frame  # noqa: E402
from _link import channel_link, report  # noqa: E402

PART_METADATA = {"expected_solids": 1}

# SAME hand as upper_arm, not mirrored. The elbow servo's case sits in
# upper_arm's far drum with its shaft pointing -Y, so the forearm's driven
# plate has to face that way too. Mirroring it (+1) would only assemble by
# flipping the forearm over, which puts its channel upside down.
HORN_SIDE = -1.0


def build(
    length: float = _frame.FOREARM_LEN,            # elbow -> wrist axis
    # straddles upper_arm's elbow DRUM now, not just its plates
    near_channel_width: float = _frame.ELBOW_CHANNEL_W,
    far_channel_width: float = _frame.FOREARM_TIP_CHANNEL_W,
    near_plate_thickness: float = _frame.LINK_PLATE_T,
    far_plate_thickness: float = _frame.FOREARM_TIP_PLATE_T,
    plate_height: float = 27.0,
    axis_height: float = _frame.LINK_AXIS_Z,
    web_thickness: float = _frame.LINK_PLATE_T,
    web_near_inset: float = 30.0,
    # nothing sweeps at the wrist end any more — the rotator turns about X,
    # entirely forward of the flange — so the web runs right up to it
    web_far_inset: float = 4.0,
    web_near_clear_r: float = 30.0,      # clears upper_arm's whole far end,
                                         # drum and body behind it
    web_far_clear_r: float = 0.0,
    taper_start: float = 30.0,           # outside the elbow sweep; see _link
    taper_end: float = _frame.FOREARM_TAPER_END,
    near_extension: float = 20.0,        # plate past the elbow axis
    # the tail cap may not cut inside the skirt it carries
    near_cap_radius: float = _frame.skirt_outer_r(_frame.DRUM_R_ELBOW) + 1.5,
    # 2, not 0: at exactly 0 the plan's far corner lands on the plate's own
    # top-corner fillet and OCC cannot fillet the degenerate vertex. The
    # 2 mm of plate that results is buried inside the flange anyway.
    far_extension: float = 2.0,
    idler_dia: float = _frame.IDLER_BOSS_DIA,
    # reaches the elbow drum's far CAP, not just the line of the channel
    idler_length: float = (_frame.ELBOW_CHANNEL_W / 2
                           - (_frame.ELBOW_DRUM_Y[1] - _frame.DRUM_WALL)),
    idler_base_fillet: float = 1.0,
    corner_fillet: float = 6.0,          # top corners, side elevation
    plan_fillet: float = 5.0,            # plan corners
    web_fillet: float = 3.0,             # web-to-plate junction
    waist_depth: float = 11.0,           # scallop in the top edge
    waist_r: float = 42.0,
    window_count: int = 0,               # the waist is the lightening now
    window_gap: float = 5.0,
    window_half_height: float = 7.0,
    window_clear: float = 3.0,
    # --- elbow skirts (this link is driven, so it laps upper_arm's drum)
    skirt_drum_radius: float = _frame.DRUM_R_ELBOW,
    skirt_drum_half_width: float = _frame.ELBOW_DRUM_Y[1],
    skirt_clearance: float = _frame.SKIRT_CLEARANCE,
    skirt_thickness: float = _frame.SKIRT_T,
    skirt_lap: float = _frame.SKIRT_LAP,
    # --- wrist_mount interface: two M3 straight through both side plates
    mount_bolt_dx: tuple[float, ...] = _frame.WRIST_MOUNT_BOLT_DX,
    mount_bolt_dia: float = _frame.WRIST_MOUNT_BOLT_DIA,
) -> Part:
    body = channel_link(
        length=length,
        horn_servo=_frame.ELBOW_SERVO,
        case_servo=_frame.WRIST_SERVO,
        near_channel_w=near_channel_width,
        far_channel_w=far_channel_width,
        near_plate_t=near_plate_thickness,
        far_plate_t=far_plate_thickness,
        taper_x0=taper_start,
        taper_x1=taper_end,
        plate_h=plate_height,
        axis_z=axis_height,
        web_t=web_thickness,
        web_near_inset=web_near_inset,
        web_far_inset=web_far_inset,
        web_near_clear_r=web_near_clear_r,
        web_far_clear_r=web_far_clear_r,
        near_ext=near_extension,
        near_cap_r=near_cap_radius,
        far_ext=far_extension,
        horn_side=HORN_SIDE,
        idler_dia=idler_dia,
        idler_len=idler_length,
        idler_base_fillet=idler_base_fillet,
        corner_fillet=corner_fillet,
        plan_fillet=plan_fillet,
        web_fillet=web_fillet,
        window_count=window_count,
        window_gap=window_gap,
        window_half_height=window_half_height,
        window_clear=window_clear,
        waist_depth=waist_depth,
        waist_x=length / 2,
        waist_r=waist_r,
        near_skirt_drum_r=skirt_drum_radius,
        near_skirt_drum_half_y=skirt_drum_half_width,
        near_skirt_clearance=skirt_clearance,
        near_skirt_t=skirt_thickness,
        near_skirt_lap=skirt_lap,
        far_case_features=False,
    )
    # two cross-drilled M3 for wrist_mount, right through both plates
    for dx in mount_bolt_dx:
        body = cast(Part, body - Pos(length + dx, 0, axis_height)
                    * Rotation(90, 0, 0)
                    * Cylinder(mount_bolt_dia / 2, 200.0))
    return cast(Part, Part() + body)


if __name__ == "__main__":
    print(report("forearm", build()))
