"""robotarm upper_arm — shoulder-to-elbow link, enclosed at both joints.

Spec: specs/robotarm/upper_arm.md. Driven at the near end by the shoulder
MG995's horn and supported opposite it by an idler stub, so the shoulder is
in double shear rather than cantilevered off the servo shaft. The far end
holds the elbow MG90S's case.

BOTH JOINTS ARE ENCLOSED, by the drum-and-skirt contract in
models/robotarm/_frame.py:

    NEAR (shoulder)  this link is DRIVEN, so it carries SKIRTS. Two annular
        walls at _frame.skirt_inner_r(DRUM_R_SHOULDER)..skirt_outer_r,
        lapping shoulder_bracket's drum by _frame.SKIRT_LAP with a running
        clearance. The channel is derived, not chosen: the drum's cap plus
        the MG995's mount_to_horn IS the channel half width, so the arm's
        channel centre and the shoulder joint frame share y = 0 with no
        offset at all. mount_to_horn, not horn_seat — the tabs bear on the
        cap's outer face, a tab thickness further out than the flange plane.
        The idler stub reaches INTO the drum's far cap, not merely up to its
        inner face, so the shoulder really is in double shear.

    FAR (elbow)  this link holds the elbow servo's CASE, so it carries the
        DRUM: _frame.DRUM_R_ELBOW over _frame.ELBOW_DRUM_Y, capped both ends,
        replacing what used to be an open fork. The MG90S's case aperture and
        tab pilots are in the near cap and the forearm's idler bore is in the
        far cap — which is what finally puts the ELBOW in double shear; it
        was single-shear, hanging off the MG90S output shaft, before.

THE SHOULDER END IS STILL AN OPEN FORK between the plates. Nothing may
bridge the channel within _frame.LINK_WEB_CLEAR_R of the shoulder axis — the
bracket, its pedestal and the MG995 fill that region — which is why the web
starts that far out and the taper starts no sooner. The skirts are the one
exception the contract allows, and only because they are concentric; they
are still clipped forward of the axis so their arc never sweeps into the
bracket's pedestal as the arm lifts (see models/robotarm/_link.py). The tail
behind the axis is capped to _frame.SHOULDER_TAIL_R, which is >= the skirt's
outer radius and still clears the turntable at full lift.
models/robotarm/_check_arm.py is the assembly-level proof of all of it.

Frame: see models/robotarm/_link.py. X = long axis (0 = shoulder axis,
UPPER_ARM_LEN = elbow axis), Y = both joint axes, Z up.

Print: flat on the bed exactly as modelled — channel opening up, both side
plates vertical, NO support material. The elbow drum is a horizontal
cylinder, so it is truncated at the bed (its flanks never exceed 45 deg from
vertical) and floored web_thickness thick inside; only its bore's crown
droops, over the top millimetre, where nothing bears. PETG, 4 walls, 30 %
infill, bed face is the web.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import Part

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frame  # noqa: E402
from _link import channel_link, report  # noqa: E402

PART_METADATA = {"expected_solids": 1}

# Which side the driving horns live on. The shoulder horn and the elbow
# servo's shaft both face -Y, so both features sit on the -Y plate; the
# forearm mirrors this (+1) so the chain assembles without flipping a part.
HORN_SIDE = -1.0


def build(
    length: float = _frame.UPPER_ARM_LEN,          # shoulder -> elbow axis
    near_channel_width: float = _frame.SHOULDER_CHANNEL_W,   # straddles MG995
    # the far plates ARE the elbow drum's caps, so they have to land on it
    far_channel_width: float = 2 * (_frame.ELBOW_DRUM_Y[1] - _frame.DRUM_WALL),
    near_plate_thickness: float = 6.0,   # >= MG995 horn pocket + MIN_WALL
    far_plate_thickness: float = _frame.DRUM_WALL,
    plate_height: float = 27.0,          # clears the elbow case aperture
    axis_height: float = 14.0,           # both joint axes above the bed
    web_thickness: float = _frame.LINK_PLATE_T,
    web_near_inset: float = _frame.LINK_WEB_CLEAR_R,
    web_far_inset: float = _frame.DRUM_R_ELBOW,   # web stops at the drum
    web_near_clear_r: float = _frame.LINK_WEB_CLEAR_R,
    web_far_clear_r: float = 20.0,
    taper_start: float = _frame.LINK_WEB_CLEAR_R,   # outside the
    taper_end: float = 54.0,             # shoulder sweep; see _link.
                                         # It must also FINISH before the
                                         # forearm's tail reaches back over
                                         # it: the forearm straddles the
                                         # elbow drum at |y| 23.5 in its own
                                         # frame, which is only 18.9 on this
                                         # side of the 4.6 mm frame offset,
                                         # so anything wider than the drum
                                         # inside the forearm's tail radius
                                         # collides as the elbow folds.
    near_extension: float = 31.0,        # plate past the shoulder axis
    near_cap_radius: float = _frame.SHOULDER_TAIL_R,   # the tail
                                         # sweeps down onto the
                                         # turntable disc
    far_extension: float = 12.0,         # the drum is the far end now; the
                                         # plan runs on a little only so its
                                         # top edge is long enough to fillet,
                                         # and every bit of it is buried
                                         # inside the drum
    idler_dia: float = _frame.IDLER_BOSS_DIA,
    # reaches right THROUGH the 608ZZ in the shoulder drum's far cap, so the
    # stub is journalled by the race rather than resting on printed plastic
    idler_length: float = _frame.stub_length(
        _frame.SHOULDER_CHANNEL_W, _frame.SHOULDER_DRUM_Y[1]),
    idler_base_fillet: float = 1.0,
    corner_fillet: float = 6.0,          # top corners, side elevation
    plan_fillet: float = 5.0,            # plan corners incl. the taper
    web_fillet: float = 3.0,             # web-to-plate junction
    waist_depth: float = 13.0,           # scallop in the top edge
    waist_r: float = 52.0,
    window_count: int = 0,               # the waist is the lightening now
    window_gap: float = 5.0,
    window_half_height: float = 7.0,
    window_clear: float = 3.0,
    # --- shoulder skirts (this link is driven, so it laps the bracket's drum)
    skirt_drum_radius: float = _frame.DRUM_R_SHOULDER,
    skirt_drum_half_width: float = _frame.SHOULDER_DRUM_Y[1],
    skirt_clearance: float = _frame.SKIRT_CLEARANCE,
    skirt_thickness: float = _frame.SKIRT_T,
    skirt_lap: float = _frame.SKIRT_LAP,
    # --- elbow drum (this link holds the elbow servo's case)
    drum_radius: float = _frame.DRUM_R_ELBOW,
    drum_half_width: float = _frame.ELBOW_DRUM_Y[1],
    drum_wall_thickness: float = _frame.DRUM_WALL,
    drum_idler_dia: float = _frame.IDLER_BOSS_DIA,
) -> Part:
    body = channel_link(
        length=length,
        horn_servo=_frame.SHOULDER_SERVO,
        case_servo=_frame.ELBOW_SERVO,
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
        far_drum_r=drum_radius,
        far_drum_half_y=drum_half_width,
        far_drum_wall=drum_wall_thickness,
        far_idler_dia=drum_idler_dia,
        far_bearing_seat_dia=_frame.BEARING_SEAT_DIA,
        far_bearing_seat_depth=_frame.BEARING_SEAT_DEPTH,
    )
    return cast(Part, Part() + body)


if __name__ == "__main__":
    print(report("upper_arm", build()))
