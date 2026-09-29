"""Polygonal round forms - specs/robotarm/_style.md rule 6.

Jonathan, 2026-09-29: "I like arms that are more circular with poliagonal
lines for texture". The base platter, the turret and the grip head are
already 12-gons; this is the same move for every other round form - the
DRUMS at each end of a link are drawn as 12-gon arcs, not true arcs.

Two rules keep this safe to apply to an existing part:
  * every vertex lies ON the circle it replaces, so the polygon is INSIDE
    it - a running clearance cut round the circle is never violated
  * a vertex sits on the local +axis (AZ0 = 0) and every 30 deg from it, so
    it lines up with a hex socket's corners (every 60 deg) - the flats never
    come closer to a hex corner than the true circle did
"""

import math

SIDES = 12
AZ0_DEG = 0.0
# the other alignment: a FLAT centred on the local +axis (and on +90, 180,
# 270), for a boss whose sides run tangent into straight columns
FLAT_ON_AXIS_DEG = 180.0 / SIDES
# a vertex closer than this fraction of a facet to an arc's end is dropped:
# a sliver facet is a sliver chamfer, and Fusion refuses those
MIN_FACET_FRAC = 0.25


def arc_polyline(cy, cz, r, a0, a1, via, sides=SIDES, az0_deg=AZ0_DEG, outside=False):
    """Points (u, v) of a polygonal arc on the circle centre (cy, cz), radius r,
    from angle a0 to a1 (radians, measured from +u toward +v), going the way
    round that passes angle `via`. The two ends are exact; between them the
    vertices sit at az0 + k * 360/sides.

    outside=False: vertices ON the circle - the polygon is inside it (a
    running clearance round the circle still holds).
    outside=True: the polygon's FLATS touch the circle - it is outside it
    (a wall measured to the circle still holds). The ends stay on the circle,
    so the two end segments are part-flats."""
    two = 2.0 * math.pi
    step = two / sides
    base = math.radians(az0_deg)
    ccw_span = (a1 - a0) % two
    ccw = (via - a0) % two < ccw_span
    span = ccw_span if ccw else two - ccw_span
    sgn = 1.0 if ccw else -1.0
    rv = r / math.cos(math.pi / sides) if outside else r
    pts = [(cy + r * math.cos(a0), cz + r * math.sin(a0))]
    # the first grid angle strictly past a0 in the direction of travel
    k0 = math.floor((a0 - base) / step) + (1 if ccw else 0)
    for i in range(sides + 1):
        a = base + (k0 + sgn * i) * step
        t = (a - a0) * sgn
        if t <= MIN_FACET_FRAC * step:
            continue
        if t >= span - MIN_FACET_FRAC * step:
            break
        pts.append((cy + rv * math.cos(a), cz + rv * math.sin(a)))
    pts.append((cy + r * math.cos(a1), cz + r * math.sin(a1)))
    return pts


def polygon(cy, cz, r, sides=SIDES, az0_deg=AZ0_DEG, outside=False):
    """A closed polygon for the circle centre (cy, cz), radius r: vertices on
    it (outside=False) or flats touching it (outside=True)."""
    rv = r / math.cos(math.pi / sides) if outside else r
    return [(cy + rv * math.cos(math.radians(az0_deg) + 2 * math.pi * k / sides),
             cz + rv * math.sin(math.radians(az0_deg) + 2 * math.pi * k / sides))
            for k in range(sides)]


def check():
    # a half circle from +90 to -90 through 0: vertices at 60, 30, 0, -30, -60
    p = arc_polyline(0.0, 0.0, 1.0, math.pi / 2, -math.pi / 2, 0.0)
    assert len(p) == 7, p
    assert all(abs(math.hypot(u, v) - 1.0) < 1e-12 for u, v in p)
    assert abs(p[3][0] - 1.0) < 1e-12 and abs(p[3][1]) < 1e-12
    # the other way round, through pi
    q = arc_polyline(0.0, 0.0, 1.0, math.pi / 2, -math.pi / 2, math.pi)
    assert len(q) == 7 and abs(q[3][0] + 1.0) < 1e-12
    # outside: the ends stay on the circle, the vertices move out, the flats touch it
    o = arc_polyline(0.0, 0.0, 1.0, math.pi / 2, -math.pi / 2, 0.0, outside=True)
    assert abs(math.hypot(*o[0]) - 1.0) < 1e-12 and math.hypot(*o[3]) > 1.0
    g = polygon(0.0, 0.0, 1.0, outside=True)
    mid = ((g[0][0] + g[1][0]) / 2, (g[0][1] + g[1][1]) / 2)
    assert abs(math.hypot(*mid) - 1.0) < 1e-12
    return True


check()
