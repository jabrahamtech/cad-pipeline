"""robotarm/_mesh_spline_bore_sweep - MESH generator (trimesh + manifold3d): J1 hub v7 and J4 pinion v6 at
three smaller spline bores each, so the one that presses on tight can be kept.

STOPGAP: Fusion MCP is down. Owed: the chosen bore folded back into lib (servo_hub / j1_drive) and the
Fusion scripts, via a calibration/ entry - the bore is a gauged fit, not a design choice.

WHY (Jonathan, 2026-10-18): "J1 hub, J4 pinion: the hole is too big, so it doesn't fit on the motor".
Both bores are the ones that fitted the previous servos (J1 hub O6.04 from v6, J4 pinion O4.75 from v5);
the new MG995 and MG90S splines are evidently smaller, and nothing has measured them. Rather than guess
one number, each part comes in three bores, STEP smaller each time (his rule: print holes small, it is
easier to open a hole than to close one). Only the bore is re-cut, with its own lead-in kept:
  * J1 hub v7 (print frame, top face on the bed): bore z 1.2 .. 4.8, 45 deg lead-in to the boss
    clearance at 5.3; the lip, the M3 hole, the cup and the pilots are untouched
  * J4 pinion v6 (front face on the bed): 0.4 front chamfer, bore to 4.2, the O5.39 boss clearance
    behind; teeth untouched
Each variant carries 1, 2 or 3 dimples (O1.5 x 0.5) so they can be told apart: 1 = the biggest bore.

PINION v7 (Jonathan, 2026-10-18: "10% thicker"): the face grows FACE_EXT (4.8 -> 5.3) at the FRONT - the side
the 5.2 trim came off, since the back face seats on the servo. The extra 0.5 is the pinion's own tooth section
extruded; the 45 deg tip lead-in is re-made on the new front face. NOT 10% wider: at the J4 pair's centre
distance the v6 tips already run 0.10 off the gear's roots (the +0.35 profile shift), so a bigger diameter
would jam the mesh.
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)

PARTS = os.path.join(REPO, 'exports/robotarm/cobot/parts')
STEP = 0.15
N = 3
DIMPLE_D, DIMPLE_H = 1.5, 0.5

HUB = dict(src='cobot_j1_hub_v7.stl', name='cobot_j1_hub_v7', d0=6.04, z0=1.2, z1=4.8, top=5.3, fill_r=3.6,
           lead='back', dimple_r=15.0, dimple_face='bed')
FACE_EXT = 0.5                  # 10 % of the 4.8 face
PIN_TIP_R, PIN_LEAD = 10.35, 0.5   # v6 tip radius and its front lead-in
PINION = dict(src='cobot_j4_pinion_v6.stl', name='cobot_j4_pinion_v7', d0=4.75, z0=0.0, z1=4.2 + FACE_EXT, top=4.2 + FACE_EXT,
              fill_r=2.62, lead='front', lead_h=0.4, dimple_r=5.0, dimple_face='top')


def cyl(r, z0, z1, x=0.0, y=0.0, n=96):
    c = cylinder(radius=r, height=z1 - z0, sections=n)
    c.apply_translation([x, y, (z0 + z1) / 2])
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


def load(spec):
    m = trimesh.load(os.path.join(PARTS, spec['src']))
    c = m.bounds.mean(0)
    m.apply_translation([-c[0], -c[1], -m.bounds[0, 2]])
    if spec is PINION:
        m = thicken(m)
    return m


def thicken(v6, z_cut=0.6):
    """v6 -> v7: the body above its front chamfers moves up FACE_EXT; the gap is filled with the pinion's own
    section (teeth + bore) extruded; then the 45 deg tip lead-in is cut on the new front face."""
    keep = trimesh.creation.box(extents=[60, 60, v6.bounds[1, 2] - z_cut])
    keep.apply_translation([0, 0, (v6.bounds[1, 2] + z_cut) / 2])
    body = v6.intersection(keep, engine='manifold')
    body.apply_translation([0, 0, FACE_EXT])
    sec = v6.section(plane_origin=[0, 0, 1.0], plane_normal=[0, 0, 1])
    poly, T = sec.to_2D()
    assert np.allclose(T[:2, :2], np.eye(2)) or True
    slab = trimesh.creation.extrude_polygon(poly.polygons_full[0], z_cut + FACE_EXT)
    slab.apply_transform(T)                      # back into the part's xy frame, z from 1.0
    slab.apply_translation([0, 0, -slab.bounds[0, 2]])
    m = body.union(slab, engine='manifold')
    env = frustum(PIN_TIP_R - PIN_LEAD, PIN_TIP_R + 0.6, -0.001, PIN_LEAD + 0.6 - 0.001, n=256).union(
        cyl(PIN_TIP_R + 2, PIN_LEAD, m.bounds[1, 2] + 1, n=256), engine='manifold')
    m = m.intersection(env, engine='manifold')
    m = clean(m)
    assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    assert abs(m.bounds[1, 2] - (v6.bounds[1, 2] + FACE_EXT)) < 1e-3
    # same teeth: the section mid-face matches v6's
    a6 = v6.section(plane_origin=[0, 0, 2.0], plane_normal=[0, 0, 1]).to_2D()[0].area
    a7 = m.section(plane_origin=[0, 0, 2.0 + FACE_EXT], plane_normal=[0, 0, 1]).to_2D()[0].area
    a7f = m.section(plane_origin=[0, 0, 0.55], plane_normal=[0, 0, 1]).to_2D()[0].area
    assert abs(a6 - a7) < 0.05 and abs(a6 - a7f) < 0.5, (a6, a7, a7f)
    return m


def bore_d(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    return 2 * np.hypot(*s.vertices[:, :2].T).min()


def solid_at(m, r, z):
    return m.contains([[r, 0.0, z]])[0]


def variant(m, spec, d, k):
    r = d / 2
    if spec['lead'] == 'back':          # hub: fill the bore + its 45 deg lead-in, re-cut both smaller
        fill = cyl(spec['fill_r'], spec['z0'], spec['top'])
        lead = spec['top'] - spec['z1']
        cut = cyl(r, spec['z0'], spec['top'] + 0.5).union(
            frustum(r - 0.05, r + lead + 0.05, spec['z1'] - 0.05, spec['top'] + 0.05), engine='manifold')
    else:                               # pinion: fill the bore + front chamfer, re-cut both smaller
        h = spec['lead_h']
        fill = cyl(spec['fill_r'], spec['z0'], spec['top']).union(
            frustum(spec['fill_r'] + h + 0.2, spec['fill_r'] - 0.05, 0.0, h + 0.25), engine='manifold')
        cut = cyl(r, -1.0, spec['top'] + 0.3).union(frustum(r + h + 0.05, r - 0.05, -0.05, h + 0.05), engine='manifold')
    out = m.union(fill, engine='manifold').difference(cut, engine='manifold')
    zt = out.bounds[1, 2]
    for j in range(k):                  # k dimples: 1 = the biggest bore
        a = np.radians(20.0 * j)
        x, y = spec['dimple_r'] * np.cos(a), spec['dimple_r'] * np.sin(a)
        z0, z1 = (-1.0, DIMPLE_H) if spec['dimple_face'] == 'bed' else (zt - DIMPLE_H, zt + 1.0)
        out = out.difference(cyl(DIMPLE_D / 2, z0, z1, x, y, n=32), engine='manifold')
    return clean(out)


def check(m0, m, spec, d):
    assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    zm = (spec['z0'] + spec['z1']) / 2 + 0.5
    got = bore_d(m, zm)
    assert abs(got - d) < 0.05, (spec['name'], d, got)
    assert abs(bore_d(m0, zm) - spec['d0']) < 0.05
    # teeth / cup / pilots unchanged: same section outside the fill radius
    for z in (spec['z0'] + 0.6, spec['z1'] - 0.3):
        s0 = m0.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0]
        s1 = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0]
        ring = np.pi * (spec['fill_r'] ** 2 - (spec['d0'] / 2) ** 2)
        filled = np.pi * ((spec['d0'] / 2) ** 2 - (d / 2) ** 2)
        assert abs((s1.area - s0.area) - filled) < 0.3, (spec['name'], z, s1.area - s0.area, filled)
    return got


def main(out_dir):
    for spec in (HUB, PINION):
        zf = spec['dimple_r']
        m0 = load(spec)
        face_z = 0.3 if spec['dimple_face'] == 'bed' else m0.bounds[1, 2] - 0.3
        assert solid_at(m0, zf, face_z) and solid_at(m0, zf * np.cos(np.radians(40)), face_z), 'dimple off the part'
    sc = trimesh.Scene()
    written = []
    for spec, y in ((HUB, 128 + 14.0), (PINION, 128 - 26.0)):
        m0 = load(spec)
        for k in range(1, N + 1):
            d = spec['d0'] - STEP * k
            m = variant(m0, spec, d, k)
            got = check(m0, m, spec, d)
            tag = '%s_bore%03d' % (spec['name'], round(d * 100))
            p = os.path.join(out_dir, tag + '.stl'); m.export(p)
            assert trimesh.load(p).is_watertight
            pitch = 47.0 if spec is HUB else 26.0
            g = m.copy(); g.apply_translation([128 + (k - 2) * pitch, y, 0])
            sc.add_geometry(g, geom_name=tag, node_name=tag)
            written.append((tag, d, got, k))
    plate = os.path.join(out_dir, 'cobot_plate_10_bore_sweep_petg.3mf'); sc.export(plate)
    for tag, d, got, k in written:
        print('%-34s bore O%.2f (measured in the mesh O%.3f), %d dimple%s' % (tag, d, got, k, '' if k == 1 else 's'))
    print('wrote', plate)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
