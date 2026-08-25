"""Organic limb generators for smooth tapered branch-like solids.

Two levels of fidelity, both defined by waypoints + per-waypoint radii:

- `limb()` — chain of frustums with sphere-blended joints. Cheap and robust;
  visibly faceted at sparse waypoints, so use it for quick jigs only.
- `loft_limb()` — smooth organic solid: the control polyline is interpolated
  with a Catmull-Rom spline, cross-sections (circles or ellipses) are placed
  on parallel-transported frames along the curve, and the sections are
  lofted into one solid. This is the one to use for finished parts.

`catmull_rom()` / `catmull_rom_scalars()` are exposed so callers can sample
the same centerline the loft uses (e.g. to split a limb into printable
segments at an exact sample, keeping the mating faces identical).

All primitives per limb are fused in a single boolean.
"""

import math
from typing import cast

from build123d import (
    Align,
    Cone,
    Cylinder,
    Ellipse,
    Part,
    Plane,
    Polyline,
    Pos,
    Sphere,
    loft,
    make_face,
)

Vec3 = tuple[float, float, float]

_ALIGN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(v: Vec3, s: float) -> Vec3:
    return (v[0] * s, v[1] * s, v[2] * s)


def vdot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vlen(v: Vec3) -> float:
    return math.sqrt(vdot(v, v))


def vunit(v: Vec3) -> Vec3:
    return vscale(v, 1.0 / vlen(v))


def path_length(points: list[Vec3]) -> float:
    return sum(vlen(vsub(b, a)) for a, b in zip(points, points[1:]))


def catmull_rom(ctrl: list[Vec3], samples_per_span: int = 4) -> list[Vec3]:
    """Uniform Catmull-Rom interpolation through every control point
    (phantom endpoints by duplication). Returns the sampled polyline
    including both ends."""
    if len(ctrl) < 2:
        raise ValueError("need at least 2 control points")
    ext = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out: list[Vec3] = []
    for i in range(len(ctrl) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for k in range(samples_per_span):
            t = k / samples_per_span
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t
                       + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                for j in range(3)))  # type: ignore[arg-type]
    out.append(ctrl[-1])
    return out


def catmull_rom_scalars(vals: list[float],
                        samples_per_span: int = 4) -> list[float]:
    return [p[0] for p in catmull_rom([(v, 0.0, 0.0) for v in vals],
                                      samples_per_span)]


def tangents(pts: list[Vec3]) -> list[Vec3]:
    """Central-difference unit tangents (one-sided at the ends)."""
    out = [vunit(vsub(pts[1], pts[0]))]
    for i in range(1, len(pts) - 1):
        out.append(vunit(vsub(pts[i + 1], pts[i - 1])))
    out.append(vunit(vsub(pts[-1], pts[-2])))
    return out


def transport_frames(pts: list[Vec3],
                     n0_hint: Vec3 = (0.0, 1.0, 0.0)) -> list[tuple[Vec3, Vec3]]:
    """(tangent, normal) per sample; the normal is parallel-transported so
    consecutive section frames never flip or twist."""
    ts = tangents(pts)
    n = vsub(n0_hint, vscale(ts[0], vdot(n0_hint, ts[0])))
    if vlen(n) < 1e-9:
        n = vsub((1.0, 0.0, 0.0), vscale(ts[0], ts[0][0]))
    n = vunit(n)
    frames = [(ts[0], n)]
    for t in ts[1:]:
        n = vsub(n, vscale(t, vdot(n, t)))
        n = vunit(n)
        frames.append((t, n))
    return frames


# dome cap profile: (advance, radius) factors ~ (sin, cos) of the quarter arc
_DOME_STEPS = [(0.42, 0.91), (0.77, 0.64), (0.94, 0.34), (0.99, 0.14)]

# Grooves: (angle rad, relative depth) — longitudinal flutes like the
# vascular gutters on real antler. Depths fade out below this radius so
# thin tips stay smooth and polished.
Groove = tuple[float, float]
_GROOVE_HALF_WIDTH = 0.55       # rad
_GROOVE_SMOOTH_ABOVE_R = 3.0    # mm — no grooves below this radius
_GROOVE_FULL_ABOVE_R = 7.0      # mm — full depth above this radius


def _section_outline(r: float, flat: float, grooves: list[Groove] | None,
                     groove_depth: float, phase: float,
                     n_side: int) -> list[tuple[float, float]]:
    """Closed 2D outline: ellipse (major r along +x) with radial groove
    notches carved at `grooves` angles (rotated by `phase`)."""
    fade = max(0.0, min(1.0, (r - _GROOVE_SMOOTH_ABOVE_R)
                        / (_GROOVE_FULL_ABOVE_R - _GROOVE_SMOOTH_ABOVE_R)))
    out = []
    for k in range(n_side):
        th = 2 * math.pi * k / n_side
        m = 1.0
        if grooves and fade > 0:
            for ga, gd in grooves:
                d = (th - ga - phase + math.pi) % (2 * math.pi) - math.pi
                if abs(d) < _GROOVE_HALF_WIDTH:
                    m -= (groove_depth * gd * fade
                          * math.cos(d / _GROOVE_HALF_WIDTH
                                     * math.pi / 2) ** 2)
        out.append((r * m * math.cos(th), r * flat * m * math.sin(th)))
    return out


def loft_limb(
    pts: list[Vec3],
    radii: list[float],
    flat: float | list[float] = 1.0,
    start: str = "dome",
    end: str = "dome",
    frames: list[tuple[Vec3, Vec3]] | None = None,
    grooves: list[Groove] | None = None,
    groove_depth: float = 0.08,
    twist: float = 0.0,
    arc_offset: float = 0.0,
    n_side: int = 32,
) -> Part:
    """Organic lofted limb through pre-sampled `pts` (e.g. from catmull_rom).

    `flat` < 1 gives oval sections: major radius r along the transported
    normal, minor radius r*flat across it (a list gives per-sample ovality).
    `grooves` carves longitudinal flutes into every section (depth as a
    fraction of local radius, spiraling at `twist` rad/mm of arc length,
    fading out at thin tips). Ends (`start`/`end`):
    - "dome"  — rounded tip, built as extra shrinking loft sections along
      the tangent (no sphere boolean, so nothing tangent-fuses);
    - "ball"  — protruding sphere of the FULL major radius: a swollen
      knuckle that also guarantees a deep (non-tangent) overlap with a
      parent body the limb springs from;
    - "flat"  — planar face perpendicular to the local tangent. To split a
      limb into segments with flush mating faces, compute
      `transport_frames` over the FULL sample list once, pass matching
      slices here, and give the later segment `arc_offset` = arc length up
      to the cut so the groove spiral phase matches — both segments then
      share the exact outline at the cut.
    """
    if len(pts) != len(radii) or len(pts) < 2:
        raise ValueError("need equal-length pts/radii lists, >= 2 entries")
    for name in (start, end):
        if name not in ("dome", "ball", "flat"):
            raise ValueError(f"unknown end style {name!r}")
    if frames is None:
        frames = transport_frames(pts)
    elif len(frames) != len(pts):
        raise ValueError("frames must match pts length")
    flats = list(flat) if isinstance(flat, (list, tuple)) else [flat] * len(pts)
    if len(flats) != len(pts):
        raise ValueError("flat list must match pts length")

    arcs, cum = [arc_offset], arc_offset
    for a, b in zip(pts, pts[1:]):
        cum += vlen(vsub(b, a))
        arcs.append(cum)

    sec = list(zip(pts, radii, frames, flats, arcs))
    if start == "dome":
        t, n = frames[0]
        depth = radii[0] * flats[0]
        sec = [(vadd(pts[0], vscale(t, -adv * depth)), radii[0] * rf,
                (t, n), flats[0], arcs[0]) for adv, rf in
               reversed(_DOME_STEPS)] + sec
    if end == "dome":
        t, n = frames[-1]
        depth = radii[-1] * flats[-1]
        sec = sec + [(vadd(pts[-1], vscale(t, adv * depth)), radii[-1] * rf,
                      (t, n), flats[-1], arcs[-1]) for adv, rf in _DOME_STEPS]
    sections = []
    for p, r, (t, n), fl, s in sec:
        plane = Plane(origin=p, x_dir=n, z_dir=t)
        if grooves:
            outline = _section_outline(r, fl, grooves, groove_depth,
                                       twist * s, n_side)
            sections.append(plane * make_face(Polyline(*outline, close=True)))
        else:
            sections.append(plane * Ellipse(r, r * fl))
    # ruled: straight skin between sections. At this sampling density the
    # chord sag is < 0.4 mm (below print resolution) and OCC's smooth
    # skinning (ruled=False) oscillates badly through dense curved sections.
    prims: list[Part] = [cast(Part, loft(sections, ruled=True))]
    if start == "ball":
        prims.append(cast(Part, Pos(*pts[0]) * Sphere(radii[0])))
    if end == "ball":
        prims.append(cast(Part, Pos(*pts[-1]) * Sphere(radii[-1])))
    return cast(Part, Part() + prims)


def frustum(a: Vec3, b: Vec3, ra: float, rb: float) -> Part:
    """Frustum from point a (radius ra) to point b (radius rb)."""
    length = vlen(vsub(b, a))
    plane = Plane(origin=a, z_dir=vsub(b, a))
    if abs(ra - rb) < 1e-6:
        prim = Cylinder(ra, length, align=_ALIGN_MIN)
    else:
        prim = Cone(ra, rb, length, align=_ALIGN_MIN)
    return cast(Part, plane * prim)


def limb(
    points: list[Vec3],
    radii: list[float],
    ball_start: bool = True,
    ball_end: bool = True,
) -> Part:
    """Faceted frustum-chain limb (quick-jig fidelity — see module docs)."""
    if len(points) != len(radii) or len(points) < 2:
        raise ValueError("need equal-length points/radii lists, >= 2 entries")
    prims: list[Part] = [
        frustum(a, b, ra, rb)
        for a, b, ra, rb in zip(points, points[1:], radii, radii[1:])
    ]
    caps = list(points[1:-1])
    cap_radii = list(radii[1:-1])
    if ball_start:
        caps.append(points[0])
        cap_radii.append(radii[0])
    if ball_end:
        caps.append(points[-1])
        cap_radii.append(radii[-1])
    prims += [cast(Part, Pos(*p) * Sphere(r)) for p, r in zip(caps, cap_radii)]
    return cast(Part, Part() + prims)
