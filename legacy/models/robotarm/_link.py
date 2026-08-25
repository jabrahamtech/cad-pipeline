"""Shared C-channel link generator for the robotarm's arm links.

upper_arm and forearm are the same object with different lengths, servos and
channel widths, so the geometry lives here once. The leading underscore keeps
tests/test_invariants.py from treating it as a part.

LINK FRAME (which is also the print frame)
    X   long axis. x = 0 is the DRIVEN joint axis (this link is turned by
        that servo's horn); x = length is the DRIVING joint axis (this link
        carries the next servo's case).
    Y   both joint axes. The channel is symmetric about y = 0: void
        |y| <= channel_w/2, side plates out to |y| = channel_w/2 + plate_t.
        Near and far channel widths may differ — the link then tapers in
        plan between taper_x0 and taper_x1.
    Z   up. The part sits on the bed at z = 0 and the channel opens toward
        +Z; the web is the bottom flange of the C.

WHY THIS ORIENTATION: every plate is a vertical wall and the web is the
first layer, so nothing overhangs — no support anywhere, on either nozzle.
Bending runs along X inside the plates, i.e. within layers, off the weak Z
axis.

THE WEB IS NOT FULL LENGTH, and that is a hard requirement rather than a
saving: see the joint-sweep rule in channel_link(). The driven end is an
open fork of two parallel plates, and the web only starts outside the
mating part's sweep radius. It is a mid-span spine, not a flange.

JOINT ENCLOSURE — the drum-and-skirt contract (models/robotarm/_frame.py).
A link is DRIVEN at its near end and DRIVES at its far end, so it carries
one of each:
    near end   SKIRTS. Two annular walls, concentric with the near joint
               axis, lapping over the mating member's drum with a running
               clearance so no gap shows at any angle. Both grow inward
               from the side plates' inner faces.
    far end    a DRUM, unless far_case_features is False. This link holds
               the next servo's CASE, so the far
               end is not an open fork at all: it is a closed cylinder
               concentric with the far joint axis, capped at both ends,
               with the servo's case aperture and tab pilots in the cap on
               the horn side and the next link's idler bore in the other.
               That bore is what puts the far joint in double shear.

WHY THE SKIRTS ARE CLIPPED TO THE LINK'S OWN SILHOUETTE, FORWARD OF THE
AXIS. A full annulus is rotation-invariant and would be ideal, but it would
reach far above the plate and far below the bed, and it cannot be printed
free-standing. What is left has to obey the sweep rule: a PARTIAL ring
sweeps everything its arc passes through. Behind the axis the mating member
lives (its own body at the elbow, its pedestal once the arm lifts at the
shoulder), so a skirt arc there jams inside the working range. The arc is
therefore taken as skirt ∩ link silhouette ∩ {x >= 0}: supported everywhere
along its length, flush with the link's profile, and clear of the mating
member throughout the swing.

HORIZONTAL BORES AND THEIR CROWNS. The far drum, its bore and the idler
stub are all horizontal cylinders, which is the one thing this orientation
cannot make self-supporting. Each is handled without support material:
    - the drum is TRUNCATED at the bed, so it lands on a flat face instead
      of a tangent line and its flanks never exceed 45 deg from vertical
      (the chord at z = 0 is wide because axis_z is well under the drum
      radius);
    - the drum's interior gets a flat floor web_t thick, continuous with
      the link's own web, so nothing has to bridge the bottom of the bore;
    - the bore's crown is the top of a horizontal hole: its last ~1 mm
      droops. Nothing bears there — the servo is located by the case
      aperture and its tab screws, and the idler runs in a clearance bore —
      so the droop is cosmetic and no support nozzle is earned;
    - the idler stub is a Ø IDLER_BOSS_DIA cylinder; at that size its crown
      droops a couple of tenths, which a clearance bore tolerates.

SERVO PLACEMENT (see lib/servo.py for the servo frame)
    driven end   the horn seat lands on the INNER face of the horn-side
                 plate, so the link straddles the servo that drives it; the
                 horn recesses into the plate and the screwdriver bore
                 breaks out of the outer face. The opposite plate carries
                 the idler stub, so the joint is in double shear instead of
                 hanging off the servo's output shaft.
    driving end  the next servo's flange tabs land on the OUTER face of the
                 far drum's near cap, its case reaches inward into the drum,
                 and its shaft and horn stand off outboard. The outer tab
                 hole sits close to the cap's rim, so each hole gets a local
                 pad MIN_WALL thick around it rather than a thinned rim.
"""

from __future__ import annotations

import math
from typing import cast

from build123d import (
    Box,
    Cylinder,
    Part,
    Plane,
    Polyline,
    Pos,
    Circle,
    Rectangle,
    Rotation,
    Sketch,
    chamfer,
    extrude,
    fillet,
    make_face,
)

from lib.design_rules import (
    ELEPHANT_FOOT_CHAMFER_MM,
    MIN_WALL_MM,
    SLIDING_FIT_CLEARANCE_MM,
)
from lib.servo import (
    ServoSpec,
    case_pocket,
    horn_pocket,
    idler_boss,
    tab_pilots,
)

from _shell import drum, drum_cap, skirt  # noqa: E402


def _side_outline(x_min: float, x_max: float, plate_h: float,
                  corner_fillet: float, waist_depth: float = 0.0,
                  waist_x: float | None = None,
                  waist_r: float = 90.0) -> Sketch:
    """Side elevation in XZ: flat on the bed, rounded along the top, and
    optionally scalloped down to a waist in the middle.

    The waist is a single large circle subtracted from the top edge rather
    than a filleted polyline: one boolean, no blend that OCC can decline, and
    the result is a true circular arc. It is also what turns a flat slab into
    something that reads as a machined link — and it removes more mass than
    punched windows do, without leaving holes for swarf to sit in.

    Bottom stays flat: it is the bed face and the web lives there.
    """
    prof = cast(
        Sketch,
        Pos((x_min + x_max) / 2, plate_h / 2)
        * Rectangle(x_max - x_min, plate_h),
    )
    if waist_depth > 0.0:
        wx = (x_min + x_max) / 2 if waist_x is None else waist_x
        if waist_r <= waist_depth:
            raise ValueError("waist_r must exceed waist_depth")
        prof = cast(Sketch, prof - Pos(wx, plate_h - waist_depth + waist_r)
                    * Circle(waist_r))
    top = prof.vertices().filter_by(lambda v: v.Y > plate_h - 0.01)
    if top:
        prof = cast(Sketch, fillet(top, corner_fillet))
    return prof


def _plan(x_min: float, x_max: float, hw_near: float, hw_far: float,
          taper_x0: float, taper_x1: float, corner_r: float) -> Sketch:
    """Plan outline in XY at half-width `hw_near` / `hw_far`, tapered
    between taper_x0 and taper_x1 (a plain rectangle when they match)."""
    if abs(hw_near - hw_far) < 1e-6:
        pts = [(x_min, hw_near), (x_max, hw_near),
               (x_max, -hw_near), (x_min, -hw_near), (x_min, hw_near)]
    else:
        pts = [(x_min, hw_near), (taper_x0, hw_near), (taper_x1, hw_far),
               (x_max, hw_far), (x_max, -hw_far), (taper_x1, -hw_far),
               (taper_x0, -hw_near), (x_min, -hw_near), (x_min, hw_near)]
    face = cast(Sketch, make_face(Polyline(*pts)))
    if corner_r > 0:
        face = cast(Sketch, fillet(face.vertices(), corner_r))
    return face


def _box(x0: float, x1: float, y0: float, y1: float,
         z0: float, z1: float) -> Part:
    """Axis-aligned box from two opposite corners."""
    return cast(
        Part,
        Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        * Box(x1 - x0, y1 - y0, z1 - z0),
    )


def _window(x_c: float, half_len: float, z_c: float, half_h: float,
            half_width: float) -> Part:
    """Self-supporting lightening window: a rhombus (roof at 45 deg or
    shallower, so it bridges nothing) swept through both side plates."""
    pts = [
        (x_c - half_len, z_c),
        (x_c, z_c + half_h),
        (x_c + half_len, z_c),
        (x_c, z_c - half_h),
        (x_c - half_len, z_c),
    ]
    face = cast(Sketch, make_face(Polyline(*pts)))
    face = cast(Sketch, fillet(face.vertices(),
                               min(1.5, 0.3 * min(half_len, half_h))))
    plane = Plane(origin=(0, half_width, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return cast(Part, extrude(plane * face, 2 * half_width))


def channel_link(
    length: float,
    horn_servo: ServoSpec,
    case_servo: ServoSpec,
    near_channel_w: float,
    far_channel_w: float,
    near_plate_t: float,
    far_plate_t: float,
    taper_x0: float,
    taper_x1: float,
    plate_h: float,
    axis_z: float,
    web_t: float,
    web_near_inset: float,
    web_far_inset: float,
    web_near_clear_r: float,
    web_far_clear_r: float,
    near_ext: float,
    far_ext: float,
    horn_side: float,
    idler_dia: float,
    idler_len: float,
    idler_base_fillet: float,
    corner_fillet: float,
    plan_fillet: float,
    web_fillet: float,
    window_count: int,
    window_gap: float,
    window_half_height: float,
    window_clear: float,
    near_cap_r: float = 0.0,
    waist_depth: float = 0.0,
    waist_x: float | None = None,
    waist_r: float = 90.0,
    near_skirt_drum_r: float = 0.0,
    near_skirt_drum_half_y: float = 0.0,
    near_skirt_clearance: float = 0.0,
    near_skirt_t: float = 0.0,
    near_skirt_lap: float = 0.0,
    far_drum_r: float = 0.0,
    far_drum_half_y: float = 0.0,
    far_drum_wall: float = 0.0,
    far_idler_dia: float = 0.0,
    far_bearing_seat_dia: float = 0.0,
    far_bearing_seat_depth: float = 0.0,
    far_case_features: bool = True,
) -> Part:
    """One U-channel arm link. See the module docstring for the frame.

    far_case_features=False leaves the far end a bare fork with no servo
    pocket, tab pilots or pads in it. The forearm uses that: its wrist is a
    ROLL joint, so the servo goes in nose-first along X behind an end
    flange, which is nothing like the across-the-channel mounting every
    other joint here uses. That flange is built in forearm.py rather than
    generalised into this function — it is one link's tip, not a pattern.
    """
    hs = 1.0 if horn_side >= 0 else -1.0
    y_in_n, y_in_f = near_channel_w / 2, far_channel_w / 2
    y_out_n, y_out_f = y_in_n + near_plate_t, y_in_f + far_plate_t
    x_min, x_max = -near_ext, length + far_ext
    web_x0, web_x1 = web_near_inset, length - web_far_inset

    # the driven plate has to contain the whole horn pocket, and the driving
    # servo's outermost tab hole has to land in plate material
    if near_ext < horn_servo.horn_span / 2 + near_plate_t / 2:
        raise ValueError(
            f"near_ext {near_ext} does not enclose the {horn_servo.name} "
            f"horn (span {horn_servo.horn_span})"
        )
    tab_over = (case_servo.hole_pitch_l / 2 - case_servo.shaft_offset
                + case_servo.pilot_dia)
    if far_case_features and far_drum_r <= 0.0 and far_ext < tab_over:
        raise ValueError(
            f"far_ext {far_ext} clips the {case_servo.name} tab holes — "
            f"needs >= {tab_over:.1f} mm"
        )
    if far_drum_r > 0.0:
        # the tab holes land in the drum's near cap instead of a plate, so
        # the cap has to be big enough to hold the outermost one plus its pad
        tab_reach = max(abs(sx) for sx, _ in case_servo.tab_holes())
        pad_r = case_servo.pilot_dia / 2 + MIN_WALL_MM
        if tab_reach - pad_r >= far_drum_r:
            raise ValueError(
                f"far drum r={far_drum_r} cannot hold the {case_servo.name} "
                f"tab hole at r={tab_reach:.1f} even with a pad"
            )
        if far_drum_wall < MIN_WALL_MM:
            raise ValueError(f"far_drum_wall {far_drum_wall} below MIN_WALL")
        if far_drum_r - far_drum_wall < case_servo.case[1] / 2:
            raise ValueError(
                f"far drum bore r={far_drum_r - far_drum_wall:.1f} does not "
                f"clear the {case_servo.name} case"
            )
        if far_drum_half_y * 2 < case_servo.below_flange + far_drum_wall:
            raise ValueError(
                f"far drum is {2 * far_drum_half_y} mm wide but the "
                f"{case_servo.name} hangs {case_servo.below_flange} below "
                f"its flange"
            )
        if abs(far_drum_half_y - (far_channel_w / 2 + far_plate_t)) > 1e-6:
            raise ValueError(
                "the far plates must land exactly on the drum's caps: "
                f"far_channel_w/2 + far_plate_t = "
                f"{far_channel_w / 2 + far_plate_t} != {far_drum_half_y}"
            )
    if near_skirt_drum_r > 0.0:
        if near_skirt_lap >= near_skirt_drum_half_y:
            raise ValueError(
                f"skirt lap {near_skirt_lap} swallows the whole drum half "
                f"width {near_skirt_drum_half_y}"
            )
        if near_skirt_drum_r + near_skirt_clearance + near_skirt_t > (
                near_cap_r if near_cap_r > 0.0 else float("inf")):
            raise ValueError(
                f"near_cap_r {near_cap_r} cuts inside the skirt's outer "
                f"radius {near_skirt_drum_r + near_skirt_clearance + near_skirt_t}"
            )
        if near_skirt_t < MIN_WALL_MM:
            raise ValueError(f"skirt wall {near_skirt_t} below MIN_WALL")
    if near_plate_t < horn_servo.horn_thick + 0.2 + 1.6:
        raise ValueError(
            f"near_plate_t {near_plate_t} leaves under 1.6 mm behind the "
            f"{horn_servo.name} horn pocket"
        )
    if web_x1 - web_x0 < web_t:
        raise ValueError(
            f"web insets {web_near_inset}/{web_far_inset} leave no web on a "
            f"{length} mm link"
        )
    # THE JOINT-SWEEP RULE. The side plates may come as close to a joint axis
    # as they like — they pass OUTSIDE the mating bracket in Y. Anything that
    # BRIDGES the channel cannot: the bracket, its saddle and the servo case
    # fill a region around the axis, so bridging material inside that radius
    # jams the joint at every angle instead of just at the extremes. The web
    # and its junction fillet are the only bridging features here, so both
    # ends of the web have to start outside the mating part's sweep radius.
    # models/robotarm/_check_arm.py is the assembly-level version of this.
    if taper_x0 < web_near_clear_r and near_channel_w > far_channel_w:
        raise ValueError(
            f"the taper narrows the channel {taper_x0} mm from the near "
            f"axis, inside the {web_near_clear_r} mm sweep — the plates "
            f"would close on the bracket's far wall"
        )
    bridge_z = abs(axis_z - (web_t + web_fillet))
    for tag, inset, need in (("near", web_near_inset, web_near_clear_r),
                             ("far", web_far_inset, web_far_clear_r)):
        got = math.hypot(inset, bridge_z)
        if got < need:
            raise ValueError(
                f"the web bridges the channel {got:.1f} mm from the {tag} "
                f"joint axis but must clear {need:.1f} mm — the joint would "
                f"foul its bracket at every angle; raise web_{tag}_inset to "
                f">= {math.sqrt(max(need ** 2 - bridge_z ** 2, 0.0)):.1f}"
            )
    # the driving servo's case aperture has to sit clear of the web fillet
    # and leave a rib above it
    ap_half = (case_servo.case[1] + SLIDING_FIT_CLEARANCE_MM) / 2
    if axis_z - ap_half < web_t + web_fillet:
        raise ValueError(
            f"axis_z {axis_z} puts the {case_servo.name} case aperture into "
            f"the web — raise it to >= {web_t + web_fillet + ap_half:.1f}"
        )
    if plate_h - (axis_z + ap_half) < MIN_WALL_MM:
        raise ValueError(
            f"plate_h {plate_h} leaves no rib above the case aperture"
        )

    # --- phase 1: base — plan footprint capped by the side elevation, then
    # the channel carved out of it. The void runs the whole length above the
    # web and full height beyond the web's ends, which leaves exactly two
    # side plates joined by a mid-span web.
    top = plate_h + 1.0
    body = extrude(
        Plane.XY * _plan(x_min, x_max, y_out_n, y_out_f,
                         taper_x0, taper_x1, plan_fillet),
        plate_h,
    )
    wide_y = max(y_out_n, y_out_f) + 1
    elevation = cast(Part, extrude(
        Plane(origin=(0, wide_y, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        * _side_outline(x_min - 1, x_max + 1, plate_h, corner_fillet,
                        waist_depth, waist_x, waist_r),
        2 * wide_y,
    ))
    body &= elevation
    void = _plan(x_min - 1, x_max + 1, y_in_n, y_in_f, taper_x0, taper_x1, 0.0)
    body -= Pos(0, 0, web_t) * extrude(Plane.XY * void, top - web_t)
    # ...and the channel runs to full depth outside the web, following the
    # taper rather than a box, so a web that starts mid-taper still cuts to
    # the right width
    floor = Pos(0, 0, -1.0) * extrude(Plane.XY * void, web_t + 1.0)
    wide = y_out_n + 1
    body -= floor & _box(x_min - 1, web_x0, -wide, wide, -2.0, web_t)
    body -= floor & _box(web_x1, x_max + 1, -wide, wide, -2.0, web_t)

    # The tail behind the joint axis sweeps DOWN as the link lifts, toward
    # whatever the mating bracket is standing on. Cap it to a circle about
    # the axis so the swing is limited by the bracket, not by the tail.
    if near_cap_r > 0.0:
        if near_cap_r < horn_servo.horn_span / 2 + 1.0:
            raise ValueError(
                f"near_cap_r {near_cap_r} would clip the "
                f"{horn_servo.name} horn (span {horn_servo.horn_span})"
            )
        y_lim2 = max(y_out_n, y_out_f) + 2.0
        tail = _box(x_min - 2, 0.0, -y_lim2, y_lim2, -2.0, plate_h + 2.0)
        keep = cast(Part, Pos(0, 0, axis_z) * Rotation(90, 0, 0)
                    * Cylinder(near_cap_r, 2 * y_lim2))
        body -= cast(Part, tail - keep)

    # concave web-to-plate junction only: the web's own end edges are convex,
    # and OCC will not blend a loop that mixes the two
    if web_fillet > 0:
        junction = [e for e in body.edges()
                    if abs(e.center().Z - web_t) < 0.01
                    and abs(e.center().Y) > min(y_in_n, y_in_f) / 2]
        if junction:
            body = fillet(junction, web_fillet)

    # --- phase 2: the FAR DRUM. This link holds the next servo's case, so
    # under the joint contract the far end is a closed cylinder concentric
    # with the far joint axis, not an open fork. It replaces the far channel
    # entirely: the plan's far plates land exactly on its two caps.
    if far_drum_r > 0.0:
        dh = far_drum_half_y
        at = Pos(length, 0.0, axis_z)
        housing = cast(Part, drum(far_drum_r, -dh, dh, far_drum_wall)
                       + drum_cap(far_drum_r, far_drum_wall,
                                  -dh + far_drum_wall / 2)
                       + drum_cap(far_drum_r, far_drum_wall,
                                  dh - far_drum_wall / 2))
        # flat interior floor, continuous with the link's own web, so the
        # bottom of the bore never has to bridge
        housing = cast(Part, housing + (
            drum_cap(far_drum_r, 2 * dh, 0.0)
            & _box(-far_drum_r - 1, far_drum_r + 1, -dh - 1, dh + 1,
                   -axis_z, -axis_z + web_t)))
        # truncate at the bed: a cylinder tangent to the plate would leave a
        # >50 deg flank, a chord axis_z below the centre leaves under 45 deg
        housing = cast(Part, at * housing)
        housing &= _box(length - far_drum_r - 1, length + far_drum_r + 1,
                        -dh - 1, dh + 1, 0.0, axis_z + far_drum_r + 1)
        body += housing

    # --- phase 3: features — driven end (horn pocket + opposed idler stub)
    driven = Plane(origin=(0.0, hs * y_in_n, axis_z),
                   x_dir=(1, 0, 0), z_dir=(0.0, hs, 0.0))
    body -= driven * horn_pocket(horn_servo, arms=2)

    idler = Plane(origin=(0.0, -hs * y_in_n, axis_z),
                  x_dir=(1, 0, 0), z_dir=(0.0, hs, 0.0))
    body += idler * idler_boss(idler_dia, idler_len,
                               base_fillet=idler_base_fillet)

    # driving end: the servo is turned 180 deg about its shaft so its case
    # reaches back along the link instead of hanging off the tip
    cap_t = far_drum_wall if far_drum_r > 0.0 else far_plate_t
    driving = Plane(origin=(length, hs * (far_drum_half_y if far_drum_r > 0.0
                                          else y_out_f), axis_z),
                    x_dir=(-1, 0, 0), z_dir=(0.0, hs, 0.0))
    if far_drum_r > 0.0 and far_case_features:
        # local pads so the outermost tab hole keeps MIN_WALL of material all
        # round instead of a knife rim where it runs off the cap
        pad_r = case_servo.pilot_dia / 2 + MIN_WALL_MM
        for sx, sy in case_servo.tab_holes():
            body += driving * Pos(sx, sy, -cap_t / 2) * Cylinder(pad_r, cap_t)
    if far_case_features:
        body -= driving * case_pocket(case_servo)
        body -= driving * tab_pilots(case_servo, depth=cap_t)
    if far_drum_r > 0.0:
        # BEARING SEAT in the far cap — this is what puts the far joint in
        # double shear instead of hanging off the servo's output shaft, and
        # on a real journal rather than printed-on-printed, which binds and
        # wears the bore oval.
        if far_bearing_seat_dia > 0.0:
            side = -hs * far_drum_half_y
            body -= cast(Part, Pos(
                length, side + hs * far_bearing_seat_depth / 2, axis_z)
                * Rotation(90, 0, 0)
                * Cylinder(far_bearing_seat_dia / 2, far_bearing_seat_depth))
            # clearance behind it so the stub passes right through the race
            body -= cast(Part, Pos(
                length, side + hs * (far_bearing_seat_depth + 3.0), axis_z)
                * Rotation(90, 0, 0)
                * Cylinder(far_idler_dia / 2 + 1.0, 6.0))
        else:
            body -= cast(Part, Pos(length,
                                   -hs * (far_drum_half_y - cap_t / 2),
                                   axis_z) * Rotation(90, 0, 0)
                         * Cylinder(
                             (far_idler_dia + SLIDING_FIT_CLEARANCE_MM) / 2,
                             cap_t + 2.0))

    # --- phase 4: the NEAR SKIRTS. Concentric annuli lapping over the mating
    # member's drum, clipped to the link's own silhouette forward of the
    # joint axis — see the module docstring for why that clip is a
    # requirement and not a saving.
    if near_skirt_drum_r > 0.0:
        lap_y = near_skirt_drum_half_y - near_skirt_lap
        clip = cast(Part, elevation & _box(0.0, x_max + 1, -wide_y, wide_y,
                                           0.0, plate_h))
        for sgn in (-1.0, 1.0):
            y0, y1 = sorted((sgn * lap_y, sgn * y_in_n))
            ring = cast(Part, Pos(0, 0, axis_z) * skirt(
                near_skirt_drum_r, near_skirt_clearance, near_skirt_t,
                y0, y1))
            body += cast(Part, ring & clip)

    # --- phase 5: lightening windows in the clear mid-span. They sit
    # between the web fillet and the plate's top edge, and each is at most
    # as long as it is tall so its roof never exceeds 45 deg.
    win_x0 = horn_servo.horn_span / 2 + window_clear
    win_x1 = length - tab_over - window_clear
    z_c = (web_t + web_fillet + plate_h) / 2
    half_h = min(window_half_height,
                 (plate_h - web_t - web_fillet) / 2 - window_clear)
    span = win_x1 - win_x0 - window_gap * max(window_count - 1, 0)
    each = span / window_count if window_count > 0 else 0.0
    if window_count > 0 and half_h >= 4.0 and each >= 8.0:
        half_len = min(each / 2, half_h)
        pitch = 2 * half_len + window_gap
        x_first = (win_x0 + win_x1) / 2 - pitch * (window_count - 1) / 2
        for i in range(window_count):
            body -= _window(x_first + i * pitch, half_len, z_c,
                            half_h, y_out_n + 1)

    # --- phase 6: finish — elephant's foot all round the bed face. Selected
    # by predicate, not group_by(Axis.Z)[0]: the outer and inner bottom
    # edges land in different groups on a signed-zero tolerance, which
    # silently chamfers only half of them.
    bed = [e for e in body.edges() if abs(e.center().Z) < 0.01]
    body = chamfer(bed, ELEPHANT_FOOT_CHAMFER_MM)
    return cast(Part, Part() + body)


def report(name: str, part: Part) -> str:
    """One-line diagnostics for both links' __main__ blocks."""
    bb = part.bounding_box()
    return (
        f"{name}: volume {part.volume / 1000:.1f} cm^3, "
        f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
        f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
        f"solids {len(part.solids())}, valid {part.is_valid}"
    )
