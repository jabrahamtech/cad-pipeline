"""Shared antler geometry for the trellis (spec: specs/trellis/antler_trellis.md).

Frame: tower wall is the XZ plane at y=0; the port axis is -Y (stem tube goes
into the port), so +Y is "away from the tower". The ring sits at the origin
between the two antler bases; antlers rise in +Z.

Organic character (all deterministic, no RNG):
- the beam centerline is a Catmull-Rom spline PLUS a low-frequency wander in
  the transported normal/binormal, so it waves like grown bone instead of
  following one clean curve;
- radii undulate a few percent along the arc and swell into knuckles where
  tines emerge;
- cross-sections are ovals whose flatness varies along the beam, carved with
  longitudinal grooves (the vascular fluting on real antler) that spiral
  slowly and fade out at the polished tips;
- tines are spaced and sized unevenly, brow/bez point forward (+Y, where the
  vines are), brow and crown tips fork.

The beam is sampled once; the hub piece owns samples up to SPLIT_F of the
arc length and the upper segment owns the rest. Both slice the SAME samples
with the SAME frames, flats and groove phases (via arc_offset), so the two
flat joint faces are identical and mate flush. Joint axis = beam tangent at
the split sample.

Gyrocup insertion corridor: the flexible cup (OD ~= port dia) is pushed into
the ring bore from +Y, so nothing may intrude into the cylinder of radius
~port_dia/2 + 0.5 mm around the Y axis for y > 0. Wander and radius
undulation both ramp in from zero at the base, so the base ball stays at
x=36 with radius 9.5 -> closest approach 26.5 mm. Widen the base X if the
port diameter grows.
"""

import math
from typing import cast

from build123d import Align, Cone, Cylinder, Part, Plane

from lib.design_rules import PRESS_FIT_CLEARANCE_MM
from lib.limb import (
    Vec3,
    catmull_rom,
    catmull_rom_scalars,
    loft_limb,
    path_length,
    transport_frames,
    vadd,
    vcross,
    vscale,
    vsub,
    vunit,
)

_ALIGN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# Right-antler beam control points (x, y, z) and radii, before length
# scaling. Big C-sweep: out and up, crest at ~z 320, tip curling back inward
# and forward like the reference photo.
CTRL: list[Vec3] = [
    (36, 10, 0),
    (50, 16, 38),
    (64, 22, 76),
    (78, 28, 114),
    (90, 34, 152),
    (100, 40, 190),
    (112, 46, 230),
    (124, 52, 270),
    (132, 56, 310),
    (132, 56, 348),
    (122, 52, 380),
    (104, 46, 400),
    (84, 40, 414),
    (62, 32, 420),
]
# radii at the split region (idx 5-6) carry margin for the socket wall under
# the groove + undulation worst case — see test_socket_wall_meets_minimum
CTRL_RADII = [9.5, 9.0, 8.7, 8.3, 8.0, 7.9, 7.6, 6.9, 6.5, 6.0,
              5.4, 4.8, 4.1, 3.4]
SAMPLES_PER_SPAN = 6
SPLIT_F = 0.46         # arc-length fraction where the hub piece ends

FLAT = 0.85            # mean ovality: minor radius = FLAT * major
FLAT_SWING = 0.05      # ovality varies along the arc by this much

# centerline wander (mm) and radius undulation, both ramped in from the base
WANDER_N = 3.0
WANDER_B = 2.4
UNDULATE = (0.055, 0.04)
KNUCKLE = 0.10         # radius swell where a tine emerges

# longitudinal grooves: (angle rad, relative depth), unevenly placed
GROOVES = [(0.35, 1.0), (1.55, 0.65), (2.70, 0.9), (3.95, 0.55), (5.15, 0.8)]
GROOVE_DEPTH = 0.08    # fraction of local radius
TWIST = 0.0018         # groove spiral, rad per mm of arc

# Tines: (arc fraction, launch direction, length mm, forked tip).
# Deliberately uneven spacing/lengths — evenly spaced identical tines are
# what makes a model read as artificial. Directions keep y >= 0 (nothing
# reaches back past the tower wall) and all climb, so vines wind up them.
# Fractions < SPLIT_F belong to the hub piece, > SPLIT_F to the upper
# segment: 3 + 3 = 6 per antler.
TINES: list[tuple[float, Vec3, float, bool]] = [
    (0.08, (0.12, 0.82, 0.42), 100, True),   # brow — forward, forked
    (0.19, (-0.06, 0.74, 0.50), 78, False),  # bez — forward
    (0.33, (0.42, 0.48, 0.46), 58, False),
    (0.56, (0.58, 0.42, 0.55), 88, False),
    (0.71, (-0.33, 0.48, 0.66), 64, False),
    # crown — near-horizontal forward curl (photo-style), which also keeps
    # its tip below the beam tip so the upper piece stays in the envelope
    (0.88, (-0.10, 0.92, 0.14), 58, True),
]
TINE_CURVE_UP = 0.5    # added to direction z past the elbow — tines rise
TINE_FLAT = 0.92       # tines are rounder than the beam
TINE_TIP_R = 3.0       # rounded ball tip — vine- and finger-safe
FORK_F = 0.65          # fork leaves the tine at this fraction of its length
FORK_LEN_F = 0.34      # each fork point's length, as a fraction of the tine

# Segment joint (press fit + CA glue)
SPIGOT_D = 8.0
SPIGOT_LEN = 20.0
SOCKET_DEPTH = 22.0


def arc_fractions(pts: list[Vec3]) -> list[float]:
    total = path_length(pts)
    out, cum = [0.0], 0.0
    for a, b in zip(pts, pts[1:]):
        cum += path_length([a, b])
        out.append(cum / total)
    return out


def flat_at(t: float) -> float:
    return FLAT + FLAT_SWING * math.sin(2 * math.pi * 1.7 * t + 0.8)


def sampled_beam(length: float = 500.0,
                 mirror: bool = False) -> tuple[list[Vec3], list[float]]:
    """Spline-sampled beam with wander + radius undulation, scaled about the
    base so arc length == `length`. `mirror` gives the left antler (x
    negated; its radius undulation is phase-shifted so the pair is not a
    perfect mirror clone)."""
    pts = catmull_rom(CTRL, SAMPLES_PER_SPAN)
    radii = catmull_rom_scalars(CTRL_RADII, SAMPLES_PER_SPAN)
    fr = arc_fractions(pts)
    frames = transport_frames(pts)
    wandered = []
    for p, (tg, n), t in zip(pts, frames, fr):
        b = vcross(tg, n)
        ramp = min(1.0, t / 0.2)
        dn = WANDER_N * ramp * math.sin(2 * math.pi * 2.2 * t + 1.3)
        db = WANDER_B * ramp * math.sin(2 * math.pi * 3.1 * t + 4.0)
        wandered.append(vadd(p, vadd(vscale(n, dn), vscale(b, db))))
    pts = wandered
    s = length / path_length(pts)
    base = pts[0]
    pts = [vadd(base, vscale(vsub(p, base), s)) for p in pts]
    phase = 0.9 if mirror else 0.0
    a1, a2 = UNDULATE
    out_r = []
    for r, t in zip(radii, fr):
        ramp = min(1.0, t / 0.15)
        m = 1.0 + ramp * (a1 * math.sin(2 * math.pi * 2.6 * t + 2.0 + phase)
                          + a2 * math.sin(2 * math.pi * 6.3 * t + 0.7 + phase))
        m += sum(KNUCKLE * math.exp(-(((t - tf) / 0.025) ** 2))
                 for tf, _, _, _ in TINES)
        out_r.append(r * m)
    if mirror:
        pts = [(-x, y, z) for x, y, z in pts]
    return pts, out_r


def split_index(pts: list[Vec3]) -> int:
    fr = arc_fractions(pts)
    return min(range(len(fr)), key=lambda i: abs(fr[i] - SPLIT_F))


def station_index(pts: list[Vec3], frac: float) -> int:
    fr = arc_fractions(pts)
    return min(range(len(fr)), key=lambda i: abs(fr[i] - frac))


def tine_limb(pts: list[Vec3], radii: list[float],
              spec: tuple[float, Vec3, float, bool], mirror: bool) -> Part:
    """One tine: spline-lofted from its beam station, bending upward past the
    elbow; forked tips get two short diverging points."""
    frac, direction, length, fork = spec
    if mirror:
        direction = (-direction[0], direction[1], direction[2])
    i = station_index(pts, frac)
    u1 = vunit(direction)
    u2 = vunit(vadd(u1, (0, 0, TINE_CURVE_UP)))
    p0 = pts[i]
    ctrl = [p0,
            vadd(p0, vscale(u1, 0.5 * length)),
            vadd(p0, vadd(vscale(u1, 0.5 * length), vscale(u2, 0.5 * length)))]
    base_r = max(0.72 * radii[i], TINE_TIP_R + 0.8)   # swollen root knuckle
    r_ctrl = [base_r, max(0.62 * base_r, TINE_TIP_R + 0.3), TINE_TIP_R]
    tpts = catmull_rom(ctrl, 5)
    tradii = catmull_rom_scalars(r_ctrl, 5)
    # flat start: the base section sits on the beam centerline, buried
    # inside the (thicker) beam — a deep overlap, no tangent surfaces
    body = loft_limb(tpts, tradii, flat=TINE_FLAT, start="flat", end="dome",
                     grooves=GROOVES, groove_depth=0.05, n_side=24)
    if fork:
        j = int(FORK_F * (len(tpts) - 1))
        ps = tpts[j]
        ut = vunit(vsub(tpts[j + 1], tpts[j - 1]))
        w = vunit(vcross(ut, (0.0, 0.0, 1.0)))
        for sgn in (1.0, -1.0):
            uf = vunit(vadd(vscale(ut, 0.75), vscale(w, 0.55 * sgn)))
            uf2 = vunit(vadd(uf, (0, 0, 0.4)))
            fl = FORK_LEN_F * length
            fctrl = [ps,
                     vadd(ps, vscale(uf, 0.55 * fl)),
                     vadd(ps, vadd(vscale(uf, 0.55 * fl),
                                   vscale(uf2, 0.45 * fl)))]
            fr = max(0.80 * tradii[j], 2.6)
            body += loft_limb(catmull_rom(fctrl, 4),
                              catmull_rom_scalars([fr, 0.8 * fr, 2.4], 4),
                              flat=TINE_FLAT, start="flat", end="dome")
    return cast(Part, body)


def lower_antler(length: float, mirror: bool) -> Part:
    """Hub-owned lower beam (flat top face at the split) + its tines, with
    the joint socket already cut."""
    pts, radii = sampled_beam(length, mirror)
    i = split_index(pts)
    frames = transport_frames(pts)
    flats = [flat_at(t) for t in arc_fractions(pts)]
    u = frames[i][0]
    # "ball" start: swollen base knuckle that overlaps the hub plate deeply
    body = loft_limb(pts[: i + 1], radii[: i + 1], flat=flats[: i + 1],
                     start="ball", end="flat", frames=frames[: i + 1],
                     grooves=GROOVES, groove_depth=GROOVE_DEPTH, twist=TWIST)
    body += [tine_limb(pts, radii, spec, mirror)
             for spec in TINES if spec[0] < SPLIT_F]
    socket = Plane(
        origin=vadd(pts[i], vscale(u, 0.5)), z_dir=vscale(u, -1.0)
    ) * Cylinder((SPIGOT_D + PRESS_FIT_CLEARANCE_MM) / 2,
                 SOCKET_DEPTH + 0.5, align=_ALIGN_MIN)
    return cast(Part, body - socket)


def upper_antler(length: float, mirror: bool) -> Part:
    """Upper beam from the split to the tip + its tines, with the press-fit
    spigot (chamfered lead) on the flat base face."""
    pts, radii = sampled_beam(length, mirror)
    i = split_index(pts)
    frames = transport_frames(pts)
    flats = [flat_at(t) for t in arc_fractions(pts)]
    u = frames[i][0]
    body = loft_limb(pts[i:], radii[i:], flat=flats[i:],
                     start="flat", end="dome", frames=frames[i:],
                     grooves=GROOVES, groove_depth=GROOVE_DEPTH, twist=TWIST,
                     arc_offset=path_length(pts[: i + 1]))
    body += [tine_limb(pts, radii, spec, mirror)
             for spec in TINES if spec[0] > SPLIT_F]
    down = Plane(origin=pts[i], z_dir=vscale(u, -1.0))
    lead = 2.0
    body += down * Cylinder(SPIGOT_D / 2, SPIGOT_LEN - lead, align=_ALIGN_MIN)
    body += Plane(
        origin=vadd(pts[i], vscale(u, -(SPIGOT_LEN - lead))),
        z_dir=vscale(u, -1.0),
    ) * Cone(SPIGOT_D / 2, SPIGOT_D / 2 - 0.8, lead, align=_ALIGN_MIN)
    return cast(Part, body)
