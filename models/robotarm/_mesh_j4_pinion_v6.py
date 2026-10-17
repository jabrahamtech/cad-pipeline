"""robotarm/_mesh_j4_pinion_v6 - MESH generator (trimesh + manifold3d).

STOPGAP: Fusion MCP is down. Owed: cobot_j4_pinion.py with a profile shift (lib/gears SpurPair has none).

WHY (Jonathan, 2026-10-17): the J4 pinion "is not always catching on the gear" - make it slightly bigger.
Bigger the right way = a POSITIVE PROFILE SHIFT on the pinion (x * m), not a scale (a scaled gear has the
wrong pitch and will not mesh at all). The pair (lib/cobot J4_PAIR: m 1, 18T : 36T) runs at the standard
27.0 + GEAR_BACKLASH 0.2 = 27.2 centre distance, so the teeth only engage 1.8 deep (of 2.0). x = +0.2 (spends the 0.2: depth 2.0) printed as
"too small" (Jonathan); he chose the MOST this pair takes, x = +0.35: tip r 10.35, root r 8.10, depth 2.15,
0.10 tip/root clearance both ways (the limit: more and the tips bottom in the mate's roots), backlash ~0.09,
0.35 to the J4 gear's flange (lib wants FREE 0.4 - accepted). Teeth thicker by 2 x m tan20 at the pitch
circle. The pair's backlash/2 tooth thinning is kept.
v6 = v5 (the 4.8 tall trimmed pinion, its spline bore, boss clearance and chamfers untouched) UNION the
shifted tooth ring (a superset of the old teeth at every radius), with v5's 45 deg front lead-in re-made
on the new tip. The tooth phase is taken from v5's own teeth.
Frame: as v5 - z 0 on the front face (on the bed), +z toward the servo.
"""
import math
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Polygon

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402

P = C.J4_PAIR
Z = P.z_pinion                                # 18
M = P.module                                  # 1.0
ALPHA = math.radians(20.0)
X = 0.35                                      # profile shift: the most this pair takes (Jonathan: 0.20 'too small')
V5 = 'exports/robotarm/cobot/parts/cobot_j4_pinion_v5.stl'
LEAD = 0.5                                    # v5's 45 deg front lead-in on the tips
RING_IN = 3.5                                 # the new tooth ring's inner radius (inside the old root, outside the bore)
FLANGE_R = C.J4.flange_od / 2                 # the J4 gear's flange: lib/cobot wants FREE 0.4 to the pinion tip
MIN_GAP = 0.3                                 # x 0.35 leaves 0.35 (accepted 2026-10-17, below lib's FREE)
TIP_MIN = 0.1                                 # tip -> the mate's root, both ways


def inv(a):
    return math.tan(a) - a


def tooth_outline(x, phase, n_flank=24, n_arc=8):
    """The pinion's outline (shapely Polygon) with profile shift x, teeth centred at phase + k*2pi/Z."""
    r_p = M * Z / 2
    r_b = r_p * math.cos(ALPHA)
    r_t = r_p + M * (1.0 + x)                # addendum 1.0 m (SpurPair.r_tip)
    r_r = r_p - M * (P.ded_f - x)
    bl_ang = (P.backlash / 2.0) / r_p
    psi = math.pi / (2 * Z) + 2 * x * math.tan(ALPHA) / Z + inv(ALPHA) - bl_ang / 2.0

    def half(r):
        return psi if r <= r_b else psi - inv(math.acos(r_b / r))

    pts = []
    pitch = 2 * math.pi / Z
    for k in range(Z):
        c = phase + k * pitch
        rs = np.linspace(max(r_r, r_b) if r_b > r_r else r_r, r_t, n_flank)
        if r_b > r_r:
            rs = np.concatenate([[r_r], rs])
        right = [(r, c - half(r)) for r in rs]                  # rising flank
        left = [(r, c + half(r)) for r in rs[::-1]]             # falling flank
        tip = [(r_t, a) for a in np.linspace(c - half(r_t), c + half(r_t), n_arc)[1:-1]]
        a_next = c + pitch - half(r_r)
        root = [(r_r, a) for a in np.linspace(c + half(r_r), a_next, n_arc)[1:-1]]
        for r, a in right + tip + left + root:
            pts.append((r * math.cos(a), r * math.sin(a)))
    return Polygon(pts).buffer(0), r_t, r_r


def frustum(r0, r1, z0, z1, n=256):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return trimesh.convex.convex_hull(np.vstack([np.c_[r0 * np.cos(a), r0 * np.sin(a), np.full(n, z0)],
                                                 np.c_[r1 * np.cos(a), r1 * np.sin(a), np.full(n, z1)]]))


def clean(m):
    import manifold3d as mf
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                             tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    assert mm.status() == mf.Error.NoError
    o = mm.to_mesh()
    return trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts))


def section(m, z):
    return m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0].polygons_full[0]


def v5_phase(v5, z=2.0):
    """Angle of a tooth centreline in v5: the mean angle of the tip-arc vertices of one tooth."""
    s = v5.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    v = s.vertices[:, :2]
    r = np.hypot(*v.T)
    a = np.arctan2(v[:, 1], v[:, 0])[r > r.max() - 0.05]
    pitch = 2 * math.pi / Z
    # fold every tip vertex into one pitch, circular-mean it
    f = np.mod(a, pitch) / pitch * 2 * math.pi
    return math.atan2(np.sin(f).mean(), np.cos(f).mean()) / (2 * math.pi) * pitch


def pinion_v6(v5, phase):
    h = v5.bounds[1, 2]
    out, r_t, r_r = tooth_outline(X, phase)
    ring = trimesh.creation.extrude_polygon(out.difference(Polygon(
        [(RING_IN * math.cos(a), RING_IN * math.sin(a)) for a in np.linspace(0, 2 * np.pi, 96, endpoint=False)])), h)
    env = frustum(r_t - LEAD, r_t + 0.6, 0.0 - 0.001, LEAD + 0.6 - 0.001).union(
        trimesh.creation.cylinder(radius=r_t + 2, height=h).apply_translation([0, 0, h / 2 + LEAD]), engine='manifold')
    ring = ring.intersection(env, engine='manifold')
    return v5.union(ring, engine='manifold'), r_t, r_r


def main(out_dir):
    v5 = trimesh.load(os.path.join(REPO, V5))
    assert v5.is_watertight and abs(v5.bounds[1, 2] - 4.8) < 0.01
    phase = v5_phase(v5)
    # the outline code, unshifted, reproduces v5's teeth (validates the involute and the phase)
    old, r_t0, _ = tooth_outline(0.0, phase)
    s5 = section(v5, 2.0)
    s5_out = Polygon(s5.exterior)
    mismatch = s5_out.symmetric_difference(old).area
    assert mismatch < 0.6, 'x=0 outline does not reproduce v5 (%.3f mm2 off)' % mismatch
    m, r_t, r_r = pinion_v6(v5, phase)
    m = clean(m)
    assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    # untouched inside the old root (the bore, the boss clearance, the chamfers)
    for z in (0.1, 1.0, 2.5, 4.0, 4.7):
        a5 = section(v5, z).interiors
        a6 = section(m, z).interiors
        d5 = sorted(round(Polygon(i).area, 2) for i in a5)
        d6 = sorted(round(Polygon(i).area, 2) for i in a6)
        assert d5 == d6, 'bore changed at z %.1f: %s vs %s' % (z, d5, d6)
    new_out = Polygon(section(m, 2.0).exterior)
    assert new_out.contains(s5_out.buffer(-0.01)), 'v6 is not a superset of v5 at z 2'
    r6 = np.hypot(*m.vertices[:, :2].T).max()
    assert abs(r6 - r_t) < 0.02
    # the mesh, at the pair's centre distance
    cd = P.centre_distance
    depth = r_t + P.r_tip(P.z_gear) - cd
    tip_clear = cd - r_t - P.r_root(P.z_gear)
    root_clear = cd - P.r_tip(P.z_gear) - r_r
    flange = cd - r_t - FLANGE_R
    assert min(tip_clear, root_clear) >= TIP_MIN - 1e-9 and flange >= MIN_GAP, (tip_clear, root_clear, flange)
    # zero-backlash centre distance of the shifted pair with standard-thickness teeth -> radial play left
    aw = cd
    inv_aw = 2 * math.tan(ALPHA) * X / (Z + P.z_gear) + inv(ALPHA)
    lo, hi = 0.0, 0.7
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if inv(mid) < inv_aw else (lo, mid)
    a0 = M * (Z + P.z_gear) / 2 * math.cos(ALPHA) / math.cos(lo)
    bl = 2 * (aw - a0) * math.tan(lo) + P.backlash         # circular, at the pitch circle (approx.)
    bl_v5 = 2 * (aw - M * (Z + P.z_gear) / 2) * math.tan(ALPHA) + P.backlash
    p = os.path.join(out_dir, 'cobot_j4_pinion_v6.stl'); m.export(p)
    assert trimesh.load(p).is_watertight
    print('x %+.2f: tip O%.2f (v5 O%.2f), root O%.2f (v5 O%.2f); x=0 outline vs v5: %.3f mm2 off'
          % (X, 2 * r_t, 2 * r_t0, 2 * r_r, 2 * P.r_root(Z), mismatch))
    print('at CD %.2f: working depth %.2f (v5 %.2f); tip->gear root %.2f; gear tip->root %.2f; gap to the gear flange %.2f'
          % (cd, depth, P.r_tip(Z) + P.r_tip(P.z_gear) - cd, tip_clear, root_clear, flange))
    print('backlash ~%.2f (v5 ~%.2f) at the pitch circle; volume %.1f (v5 %.1f) mm3'
          % (bl, bl_v5, m.volume, v5.volume))
    # plate 8 (with the J5 rotator v5 and the AS5600 glue pins): models/robotarm/_mesh_plate_8.py
    print('wrote', p)
    return m


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
