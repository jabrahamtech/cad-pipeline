"""robotarm/_mesh_j1_hub_v7 - MESH generator (trimesh + manifold3d).

STOPGAP: Fusion MCP is down. Owed: j1_hub.py updated to match (a lip over the broach, an M3 hole).

WHY (Jonathan, 2026-10-17): the J1 hub (v6, plate 5) went onto the new MG995 and "started to slip";
he asked for "a little lip so that we can screw in a screw". v6 has nothing a screw can bear on: its
O6.05 broach runs straight out of the top face, and that face is the bolted joint to the tower's disc,
so a washer on it is the 'shim that lifts the tower off its rollers' j1_hub.py warns about.
v7 = v6 with the top of the bore closed by a LIP (z LIP_Z0 .. the face) and an M3 clearance hole through
it. A plain M3 head bears on the lip and stands up INTO the tower disc's blind O6.3 x ~9 centre pocket
(measured off cobot_tower in plate 1), so nothing sits between the hub face and the disc.
The lip's underside stays LIP_GAP above the drawn spline top (j1_drive J1_HUB.broach_to), so a shaft a
little longer than drawn still lets the hub seat. The screw is a keeper: snug it, don't crank it.
Untouched: the cup, the 3 x M3 pilots, the boss clearance, the broach bore (a fresh one cuts onto the
new motor's spline - re-using a bore cut by the old motor is what slips).
Frames: HUB frame z 0 on the servo-side face, + toward the tower (j1_hub.py); printed TOP FACE ON THE BED.
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402
import lib.j1_drive as J  # noqa: E402

V6_PLATE = 'exports/robotarm/cobot/cobot_plate_5_base_petg_v2.3mf'
V6_NAME = '9'                                  # the J1 hub v6 on plate 5 v2 (43.2 x 43.2 x 6.4)
TOWER_PLATE = 'exports/robotarm/cobot/cobot_plate_1_petg.3mf'
FACE = J.J1_HUB_FACE_MM                        # 6.4
SPLINE_TOP = J.J1_HUB.broach_to                # 5.0 (drawn)
LIP_GAP = 0.2                                  # lip underside above the drawn shaft end
LIP_Z0 = SPLINE_TOP + LIP_GAP                  # 5.2 -> lip 1.2 thick
HOLE_D = C.M3['clearance'] if hasattr(C, 'M3') and 'clearance' in C.M3 else 3.4
HEAD_D, HEAD_H = J.J1_HUB_HEAD_D_MM, J.J1_HUB_HEAD_H_MM      # ISO 4762 M3 cap: 5.5 x 3.0
EF = 0.3                                       # first-layer chamfer on the hole (top face is the bed)
FILL_R = 3.6                                   # covers the O6.05 bore and v6's 45 deg mouth chamfer (r 3.42)


def cyl(r, z0, z1, n=96):
    c = cylinder(radius=r, height=z1 - z0, sections=n)
    c.apply_translation([0, 0, (z0 + z1) / 2])
    return c


def frustum(r0, r1, z0, z1, n=96):
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


def rmin(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    return np.hypot(*s.vertices[:, :2].T).min()


def load_v6():
    g = trimesh.load(os.path.join(REPO, V6_PLATE)).geometry[V6_NAME].copy()
    c = g.bounds.mean(0)
    g.apply_translation([-c[0], -c[1], -g.bounds[0, 2]])
    assert abs(g.extents[2] - FACE) < 0.01 and abs(g.extents[0] - 43.2) < 0.1, g.extents
    # servo side at z 0: the O13.4 boss clearance is there, the broach above it
    assert abs(2 * rmin(g, 0.5) - J.J1_HUB.boss_clear_d) < 0.1 and abs(2 * rmin(g, 3.0) - 6.05) < 0.08
    return g


def tower_pocket():
    """(diameter, depth) of the blind pocket in the tower disc's underside on the J1 axis."""
    t = trimesh.load(os.path.join(REPO, TOWER_PLATE)).geometry['cobot_tower']
    s = t.section(plane_origin=[0, 0, 2.0], plane_normal=[0, 0, 1])
    p, T = s.to_2D()
    best = None
    for poly in p.polygons_full:
        for i in poly.interiors:
            h = np.array(i.coords); c = h.mean(0); d = 2 * np.hypot(*(h - c).T).mean()
            if 6.0 < d < 6.8 and (best is None or abs(d - 6.4) < abs(best[1] - 6.4)):
                best = (c, d)
    axis = (T @ np.r_[best[0], 0, 1])[:2]
    depth = 0.0
    for z in np.arange(0.25, 30, 0.25):
        if t.contains([[axis[0], axis[1], z]])[0]:
            break
        depth = z
    return best[1], depth


def hub_v7(v6):
    m = v6.union(cyl(FILL_R, LIP_Z0, FACE), engine='manifold')
    cut = cyl(HOLE_D / 2, LIP_Z0 - 1.0, FACE + 1.0)
    cut = cut.union(frustum(HOLE_D / 2 - 0.3, HOLE_D / 2 + EF + 0.05, FACE - EF - 0.3, FACE + 0.05), engine='manifold')
    return m.difference(cut, engine='manifold')


def main(out_dir):
    v6 = load_v6()
    m = clean(hub_v7(v6))
    assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    # unchanged below the lip, and everywhere outside FILL_R
    for z in (0.5, 2.0, 4.0, 5.0):
        assert abs(rmin(m, z) - rmin(v6, z)) < 0.01, 'bore changed at z %.1f' % z
        a6 = v6.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0].area
        a7 = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0].area
        assert abs(a6 - a7) < 0.05, z
    for z in (LIP_Z0 + 0.2, FACE - 0.6):
        assert abs(2 * rmin(m, z) - HOLE_D) < 0.08, (z, 2 * rmin(m, z))
    lip = FACE - LIP_Z0
    seat = (HEAD_D - HOLE_D) / 2
    assert lip >= C.MIN_WALL * 0.75 and seat >= 0.8
    pd, pdepth = tower_pocket()
    assert HEAD_D + C.FREE <= pd and HEAD_H + 1.0 <= pdepth, (pd, pdepth)
    out = m.copy()                                   # print: top face on the bed
    out.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    out.apply_translation(-out.bounds[0])
    out = clean(out)
    p = os.path.join(out_dir, 'cobot_j1_hub_v7.stl'); out.export(p)
    assert trimesh.load(p).is_watertight
    sc = trimesh.Scene(); g = out.copy(); g.apply_translation([128 - g.centroid[0], 128 - g.centroid[1], 0])
    sc.add_geometry(g, geom_name='cobot_j1_hub_v7', node_name='cobot_j1_hub_v7')
    plate = os.path.join(out_dir, 'cobot_plate_9_j1_hub_petg.3mf'); sc.export(plate)
    print('lip z %.2f..%.2f (%.2f thick, %.2f over the drawn shaft end), M3 hole O%.2f: cap head O%.1f seats %.2f/side'
          % (LIP_Z0, FACE, lip, LIP_GAP, HOLE_D, HEAD_D, seat))
    print('tower centre pocket O%.2f x %.2f deep: the O%.1f x %.1f head clears it by %.2f/side, %.1f above'
          % (pd, pdepth, HEAD_D, HEAD_H, (pd - HEAD_D) / 2, pdepth - HEAD_H))
    print('hub %.1f x %.1f x %.1f, %.2f cm3 (v6 %.2f); wrote %s %s' % (*out.extents, m.volume / 1000, v6.volume / 1000, p, plate))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
