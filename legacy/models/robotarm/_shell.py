"""Cosmetic covers that close the arm's open channels — the "shell" half of
the drum-and-shell look, and the thing that hides the servo wiring.

WHY COVERS RATHER THAN A CLOSED LINK: each link has to straddle the servo
that drives it (that is what puts the joints in double shear), so its channel
must stay open to get the servo in and the wiring routed. Building the roof
into the link would close a tube you then could not assemble. A separate
cover that screws on afterwards keeps assembly easy and hides everything.

WHY A GABLE AND NOT A FLAT LID: a flat lid over a 35-46 mm channel is a
35-46 mm bridge. Two 45 deg slopes meeting at a narrow crown are
self-supporting, so a cover prints gable-up with no support at all — and a
faceted shell is the reference's surface language anyway.

THE SWEEP RULE, which decides where a cover may go: at a joint, only a
CONCENTRIC cover is safe, because a disc turning about its own axis sweeps
nothing new. Anywhere else a cover bridges the channel, so it must clear the
mating bracket's sweep radius exactly as the link's web does
(_frame.LINK_WEB_CLEAR_R). That is why a gable starts out at that radius and
the joints themselves need concentric drums instead.

CONSTRUCTION: the gable is a 2D trapezoid extruded along the link. Not a
loft and not a chamfer — OCC declines both on these tapered outlines — just
an extruded profile and booleans, which cannot fail. Stepping the section
rather than tapering it is also closer to the reference, which is visibly
stepped.

Frame: identical to the link's (models/robotarm/_link.py), so a cover drops
straight onto its link with no transform.
"""

from __future__ import annotations

from typing import cast

from build123d import (
    Box,
    Cylinder,
    Part,
    Plane,
    Polyline,
    Pos,
    Rotation,
    Sketch,
    extrude,
    make_face,
)

Segment = tuple[float, float, float]   # (x_start, x_end, outer half width)


def _trapezoid(half_width: float, base_z: float, rise: float,
               crown_min: float) -> Sketch:
    """Gable cross-section in the YZ plane: flat base, 45 deg flanks, flat
    crown. 45 deg is the steepest fully self-supporting slope."""
    h = min(rise, max(half_width - crown_min, 0.1))
    top = half_width - h
    return cast(Sketch, make_face(Polyline(
        (-half_width, base_z), (half_width, base_z),
        (top, base_z + h), (-top, base_z + h), close=True,
    )))


def _gable(x0: float, x1: float, half_width: float, base_z: float,
           rise: float, crown_min: float) -> Part:
    return cast(Part, Pos(x0, 0, 0) * extrude(
        Plane.YZ * _trapezoid(half_width, base_z, rise, crown_min), x1 - x0))


def channel_cover(
    segments: list[Segment],
    base_z: float,
    rise: float,
    skin: float,
    crown_min: float = 5.0,
    screw_x: tuple[float, ...] = (),
    screw_z: float = 0.0,
    screw_pilot: float = 2.5,
    boss: float = 9.0,
    boss_side: float = -1.0,
) -> Part:
    """A stepped gable cover, hollow and open downward.

    `segments` are (x_start, x_end, outer_half_width) runs — one per step of
    the link's plan. Widths should match the link's outer faces so the cover's
    flanks sit flush with them.

    `screw_x` are stations where a screw passes horizontally through the
    link's side plate into a boss inside the cover. Visible fixings on the
    flank are what the reference does too.
    """
    if not segments:
        raise ValueError("a cover needs at least one segment")
    if skin <= 0:
        raise ValueError("skin must be positive")

    body: Part | None = None
    for x0, x1, hw in segments:
        outer = _gable(x0, x1, hw, base_z, rise, crown_min)
        # inner trapezoid: a true perpendicular inset of a 45 deg flank moves
        # it sqrt(2)*skin horizontally; the base drops below base_z so the
        # shell is open downward and needs no support
        inner = _gable(x0 - 0.5, x1 + 0.5, hw - skin * 1.4142,
                       base_z - 2.0, rise - skin + 2.0, max(crown_min - 1.0, 0.5))
        seg = cast(Part, outer - inner)
        body = seg if body is None else cast(Part, body + seg)
    assert body is not None

    for sx in screw_x:
        hw = next((w for a, b, w in segments if a <= sx <= b), segments[0][2])
        y_face = boss_side * (hw - skin)
        body = cast(Part, body + Pos(sx, y_face - boss_side * boss / 2, screw_z)
                    * Box(boss, boss, boss))
        body = cast(Part, body - (
            Pos(sx, y_face, screw_z) * Rotation(90, 0, 0)
            * Cylinder(screw_pilot / 2, boss * 3)))
    return cast(Part, Part() + body)


def _tube(inner_r: float, outer_r: float, y0: float, y1: float) -> Part:
    """Annular wall about the Y axis, spanning y0..y1."""
    length = y1 - y0
    mid = (y0 + y1) / 2
    outer = cast(Part, Pos(0, mid, 0) * Rotation(90, 0, 0)
                 * Cylinder(outer_r, length))
    if inner_r <= 0:
        return outer
    bore = cast(Part, Pos(0, mid, 0) * Rotation(90, 0, 0)
                * Cylinder(inner_r, length + 2.0))
    return cast(Part, outer - bore)


def drum(radius: float, y0: float, y1: float, wall: float) -> Part:
    """The joint housing carried by the member that holds the servo CASE:
    a cylinder concentric with the joint axis, hollow, spanning y0..y1.

    Built about the origin with the joint axis along Y, so a caller positions
    it by translating to its own joint axis. Both end faces are left open —
    the caller cuts the case aperture in one and the idler bore in the other,
    which is also how the joint ends up in double shear.
    """
    if wall <= 0 or wall >= radius:
        raise ValueError("wall must be positive and smaller than radius")
    return _tube(radius - wall, radius, y0, y1)


def skirt(drum_radius: float, clearance: float, thickness: float,
          y0: float, y1: float) -> Part:
    """The annular wall carried by the member driven by the HORN, lapping
    over `drum` with a running clearance so the joint shows no gap at any
    angle. Concentric, so it sweeps nothing new."""
    inner = drum_radius + clearance
    return _tube(inner, inner + thickness, y0, y1)


def drum_cap(radius: float, thickness: float, y: float,
             bore: float = 0.0) -> Part:
    """A concentric disc closing one end of a joint. Axis along Y."""
    disc = cast(Part, Pos(0, y, 0) * Rotation(90, 0, 0)
                * Cylinder(radius, thickness))
    if bore > 0:
        disc = cast(Part, disc - Pos(0, y, 0) * Rotation(90, 0, 0)
                    * Cylinder(bore / 2, thickness * 3))
    return disc
