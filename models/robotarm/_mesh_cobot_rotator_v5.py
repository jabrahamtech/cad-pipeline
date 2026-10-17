"""robotarm/_mesh_cobot_rotator_v5 - MESH generator (trimesh + manifold3d).

STOPGAP: Fusion MCP is down. Owed: cobot_rotator.py updated to match (screw hole, head pocket, cone).

WHY (Jonathan, 2026-10-17): the J5 rotator's servo screw "is not attaching to the motor properly and
also not being held on correctly". v4 was drawn for an assumed M2.5 x 6 screw + washer (lib/servo_hub:
screw O2.5, head ~O5). The screw he actually has (MEASURED 2026-10-17): thread O2.1, total 6.3,
head O3.3 x 1.0 -> shank 5.3. Against the printed v4 (sectioned from cobot_rotator_v4 below):
  * counterbore O6.95 x 3.0 from the front face, then a O2.9 hole 3.5 long down to the spline:
    head on the floor -> the tip only 5.3 - 3.5 = 1.8 into the servo shaft    -> "not attaching"
  * the O3.3 head on a O2.9 hole = 0.2 per side of ledge                        -> "not held on"
v5 = v4 with the screw path re-cut from the front face down to the spline (the broach, the hub, the neck
and the 4 head pilots are untouched):
  * O6.95 driver access 0 .. CONE_D0, a 45 deg cone in to the head pocket (self-supporting face-down)
  * O3.7 head pocket (head + FREE: centres the screw on the axis), floor WEB above the spline top
  * O2.4 (design_rules M2 clearance) hole through the web: 0.45 per side of head seat
  -> thread in the servo shaft = SHANK - WEB = 3.3 (was 1.8)
Frame: as printed - z 0 on the FRONT face (on the bed), +z toward the servo.
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402

# --- the screw (MEASURED, Jonathan 2026-10-17) ------------------------------------
SCREW_D, SCREW_L, HEAD_D, HEAD_H = 2.1, 6.3, 3.3, 1.0
SHANK = SCREW_L - HEAD_H                      # 5.3
# --- the printed v4 (sectioned from its mesh, print frame) -------------------------
V4_PLATE = 'exports/robotarm/cobot/cobot_plate_3s_sg90_gears_petg_v2.3mf'
V4_NAME = 'cobot_rotator_v4'
V4_H = 12.8
V4_CBORE = (6.95, 3.0)                        # driver access (d, depth)
V4_HOLE_D = 2.9
BROACH_TOP = 6.5                              # depth of the spline's end (= the servo shaft's top face)
BROACH_D = 4.75
# --- v5 ---------------------------------------------------------------------------
HOLE_D = C.M2['clearance']                    # 2.4
HEAD_POCKET_D = HEAD_D + C.FREE               # 3.7
WEB = 2.0                                     # under the head, over the spline (>= MIN_WALL 1.6)
FLOOR = BROACH_TOP - WEB                      # 4.5: the head seats here
HEAD_POCKET_H = HEAD_H + 0.3                  # 1.3
POCKET_TOP = FLOOR - HEAD_POCKET_H            # 3.2
DRIVER_D = V4_CBORE[0]
CONE_D0 = POCKET_TOP - (DRIVER_D - HEAD_POCKET_D) / 2   # 1.575: 45 deg
FILL_D = DRIVER_D + 0.6
EPS = 0.01


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


def load_v4():
    g = trimesh.load(os.path.join(REPO, V4_PLATE)).geometry[V4_NAME].copy()
    c = g.bounds.mean(0)
    g.apply_translation([-c[0], -c[1], -g.bounds[0, 2]])
    assert abs(g.extents[2] - V4_H) < 0.01
    return g


def min_d(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    return 2 * np.hypot(*s.vertices[:, :2].T).min()


def rotator_v5(v4):
    m = v4.union(cyl(FILL_D / 2, 0.0, BROACH_TOP), engine='manifold')        # the old screw path, filled
    cut = cyl(HOLE_D / 2, -1.0, BROACH_TOP + 1.0)                            # into the broach
    cut = cut.union(cyl(HEAD_POCKET_D / 2, CONE_D0 + 0.5, FLOOR), engine='manifold')
    r_cone0 = DRIVER_D / 2 + 0.05
    cut = cut.union(frustum(r_cone0, HEAD_POCKET_D / 2 - 0.05, CONE_D0 - 0.05, POCKET_TOP + 0.05), engine='manifold')
    cut = cut.union(cyl(DRIVER_D / 2, -1.0, CONE_D0 + EPS), engine='manifold')
    return m.difference(cut, engine='manifold')


def checks(v4, m):
    assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    assert abs(m.volume - v4.volume) < 60, (m.volume, v4.volume)
    # the old path, as sectioned
    assert abs(min_d(v4, 1.0) - V4_CBORE[0]) < 0.15 and abs(min_d(v4, 5.0) - V4_HOLE_D) < 0.05
    assert abs(min_d(v4, BROACH_TOP + 0.1) - BROACH_D) < 0.05
    # v5 path
    for z, want in ((0.5, DRIVER_D), (FLOOR - 0.5, HEAD_POCKET_D), (FLOOR + 0.5, HOLE_D),
                    (BROACH_TOP - 0.1, HOLE_D), (BROACH_TOP + 0.1, BROACH_D)):
        got = min_d(m, z)
        assert abs(got - want) < 0.08, 'at z %.2f: O%.3f, want O%.2f' % (z, got, want)
    # untouched below the spline top and outside the fill
    for z in (7.0, 9.0, 11.0, 12.6):
        a4 = v4.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0].area
        a5 = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0].area
        assert abs(a4 - a5) < 0.05, 'v4 changed below the spline at z %.1f' % z
    assert WEB >= C.MIN_WALL
    assert HEAD_D > HOLE_D + 0.8, 'head seat < 0.4 per side'
    thread = SHANK - WEB
    assert thread >= 3.0, thread
    return thread


def main(out_dir):
    v4 = load_v4()
    m = clean(rotator_v5(v4))
    thread = checks(v4, m)
    p = os.path.join(out_dir, 'cobot_rotator_v5.stl'); m.export(p)
    assert trimesh.load(p).is_watertight
    sc = trimesh.Scene()
    g = m.copy(); g.apply_translation([128, 128, 0])
    sc.add_geometry(g, geom_name='cobot_rotator_v5', node_name='cobot_rotator_v5')
    plate = os.path.join(out_dir, 'cobot_plate_8_rotator_v5_petg.3mf'); sc.export(plate)
    v4_thread = SHANK - (BROACH_TOP - V4_CBORE[1])
    print('screw path from the front face: O%.2f to %.2f, 45 deg cone to %.2f, head pocket O%.2f to %.2f, '
          'hole O%.2f to the spline at %.2f' % (DRIVER_D, CONE_D0, POCKET_TOP, HEAD_POCKET_D, FLOOR, HOLE_D, BROACH_TOP))
    print('screw O%.1f x %.1f, head O%.1f x %.1f: head seat %.2f/side (v4 %.2f); thread in the servo %.2f (v4 %.2f)'
          % (SCREW_D, SCREW_L, HEAD_D, HEAD_H, (HEAD_D - HOLE_D) / 2, (HEAD_D - V4_HOLE_D) / 2, thread, v4_thread))
    print('rotator %.2f x %.2f x %.2f, %.2f cm3 (v4 %.2f); head top %.2f under the face'
          % (*m.extents, m.volume / 1000, v4.volume / 1000, FLOOR - HEAD_H))
    print('wrote', p, plate)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
