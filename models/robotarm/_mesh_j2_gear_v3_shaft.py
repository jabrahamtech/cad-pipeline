"""robotarm/_mesh_j2_gear_v3_shaft - MESH generator (trimesh + manifold3d).

STOPGAP: Fusion MCP is down (2026-10-14). Owed: cobot_j2_gear.py + a cobot_j2_shaft.py Fusion script.

WHY: the printed O10 counterbalance shaft broke AT THE GEAR FACE, and the hub discs slipped
on its 1.0 D-flat (Jonathan, 2026-10-14). The shaft was printed upright with the gear, so its
layers stacked across it - the weak axis for both the spring's torsion and any bending.
He chose a SEPARATE PRINTED HEX SHAFT (over a bought steel D-shaft):
  * gear v3 = gear v2 with the shaft cut off at its tooth face (z 23) and a HEX SOCKET
    (AF HEX_AF + LOC) sunk 15 into it, one flat facing +x = the old D-flat's direction,
    so the spring's neutral (flat forward with the arm vertical) is unchanged
  * shaft v1 = a HEX (AF 8.5) bar, printed LYING ON A FLAT so its layers run along it,
    seated on the socket floor; its top end carries the O6 J2 magnet as before and ends
    AX_GAP under the lid, which also stops it lifting out. Corners broken CORNER for
    the socket's printed corners. A groove marks the +x flat at the top end: the hubs'
    hex bores go on with their mark on that flat (6 positions; the wrong one = 60 deg off)
  * the hubs get matching hex bores (and are thickened for the new spring) separately
Frame (both parts, as installed): z along J2, 0 on the gear's spigot-end face (gear v2 frame).
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402

GEAR_TOP = C.J2.gear_h                       # 23.0: the tooth face
SHAFT_TOP = C.SHAFT_TOP - C.J2.x_spigot_end  # 95.67 in this frame (AX_GAP under the lid)
HEX_AF = 8.5                                 # across flats
CORNER = 0.3                                 # corners broken by this (radially)
SOCKET_AF = HEX_AF + C.LOC
SOCKET_Z0 = 8.0                              # 15 deep; the register recess stops at 1.9
LEAD = 0.5                                   # 45 deg chamfer at the socket mouth and on the shaft's bottom end
MAG_D, MAG_H = C.MAGNET_POCKET
MARK_W, MARK_D, MARK_L = 1.2, 0.5, 6.0
EPS = 0.01


def prism(af, z0, z1, corner=0.0):
    """Hex prism, flats normal to 0/60/120.. deg (one flat facing +x), corners cut by `corner`."""
    h = cylinder(radius=af / np.sqrt(3), height=z1 - z0, sections=6)
    h.apply_transform(trimesh.transformations.rotation_matrix(np.radians(30), [0, 0, 1]))
    h.apply_translation([0, 0, (z0 + z1) / 2])
    if corner > 0:
        r = af / np.sqrt(3) - corner
        h = h.intersection(cylinder(radius=r, height=z1 - z0 + 1, sections=180).apply_translation([0, 0, (z0 + z1) / 2]),
                           engine='manifold')
    return h


def frustum(r0, r1, z0, z1, n=180, rot=0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.radians(rot)
    return trimesh.convex.convex_hull(np.vstack([np.c_[r0 * np.cos(a), r0 * np.sin(a), np.full(n, z0)],
                                                 np.c_[r1 * np.cos(a), r1 * np.sin(a), np.full(n, z1)]]))


def gear_v3(v2):
    keep = box(extents=[80, 80, GEAR_TOP]); keep.apply_translation([0, 0, GEAR_TOP / 2])
    g = v2.intersection(keep, engine='manifold')
    g = g.difference(prism(SOCKET_AF, SOCKET_Z0, GEAR_TOP + 1), engine='manifold')
    # hex 45 deg chamfer (a hex frustum: no near-coincident facets against the socket walls)
    ac = SOCKET_AF / np.sqrt(3)
    g = g.difference(frustum(ac - 0.3, ac + LEAD + 0.05, GEAR_TOP - LEAD - 0.3, GEAR_TOP + 0.05, n=6, rot=30), engine='manifold')
    return g


def shaft_v1():
    z0 = SOCKET_Z0
    s = prism(HEX_AF, z0, SHAFT_TOP, CORNER)
    r = HEX_AF / np.sqrt(3)
    # bottom-end lead-in: everything outside a 45 deg cone from (r - LEAD) at z0
    s = s.intersection(frustum(r - LEAD - CORNER, r - LEAD - CORNER + 40, z0, z0 + 40).union(
        cylinder(radius=20, height=SHAFT_TOP - z0 - 30).apply_translation([0, 0, (SHAFT_TOP + z0 + 30) / 2]),
        engine='manifold'), engine='manifold')
    s = s.difference(cylinder(radius=MAG_D / 2, height=MAG_H + 1, sections=96)
                     .apply_translation([0, 0, SHAFT_TOP - MAG_H + (MAG_H + 1) / 2]), engine='manifold')
    mark = box(extents=[MARK_D * 2, MARK_W, MARK_L + 1])
    mark.apply_translation([HEX_AF / 2, 0, SHAFT_TOP - MARK_L + (MARK_L + 1) / 2])
    s = s.difference(mark, engine='manifold')
    return s


def clean(m):
    """Round-trip through manifold3d in float32 (what the STL holds): it drops the zero-area slivers the
    booleans leave on the socket walls, which otherwise open edges once the STL is re-read."""
    import manifold3d as mf
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                             tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    assert mm.status() == mf.Error.NoError
    out = mm.to_mesh()
    return trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts))


def section_af(m, z):
    """Across-flats of the section at z, measured along x (the marked flat) - for the checks."""
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    v = s.vertices
    return v[:, 0].max() - v[:, 0].min(), np.hypot(v[:, 0], v[:, 1]).max()


def checks(g, s, v2):
    for m in (g, s):
        assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    assert abs(g.bounds[1, 2] - GEAR_TOP) < 1e-6
    # gear teeth and bolt pattern untouched: same section as v2 at mid-face
    for z in (5.0, 15.0, 21.0):
        a2 = v2.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0].area
        a3 = g.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_2D()[0].area
        hole = 0.0 if z < SOCKET_Z0 else 3 * np.sqrt(3) / 2 * (SOCKET_AF / np.sqrt(3)) ** 2
        assert abs(a2 - a3 - hole) < 0.5, 'gear section at z %.1f changed by more than the socket' % z
    # the socket's wall to the bolt holes (r 15, O3.4)
    wall = 15.0 - 3.4 / 2 - SOCKET_AF / np.sqrt(3)
    assert wall >= 2 * C.MIN_WALL, 'socket to bolt hole %.2f' % wall
    assert SOCKET_Z0 - C.REG_RECESS[1] >= 3.0, 'thin floor over the register recess'
    # shaft passes every bore it runs in (round bores: SHAFT_BORE; the J2 plate's O12 hole with its slot travel)
    ac = HEX_AF / np.sqrt(3) - CORNER
    assert 2 * ac + C.FREE <= C.SHAFT_BORE + 1e-6, 'shaft corners in the O%.1f bores' % C.SHAFT_BORE
    assert (C.STALK_HOLE_D - 2 * ac) / 2 >= C.PLATE_SLOT + C.FREE / 2, 'shaft in the J2 plate hole + slot travel'
    assert (HEX_AF - MAG_D) / 2 >= 0.8, 'magnet pocket wall'
    af, _ = section_af(s, 50.0)
    assert abs(af - HEX_AF) < 0.05, af
    return wall, ac


def main(v2_path, out_dir):
    v2 = trimesh.load(v2_path)
    g = clean(gear_v3(v2))
    s = clean(shaft_v1())
    wall, ac = checks(g, s, v2)
    gp = os.path.join(out_dir, 'cobot_j2_gear_v3.stl'); g.export(gp)
    sp = os.path.join(out_dir, 'cobot_j2_shaft_v1.stl')
    sl = s.copy()
    # print lying on the flat opposite the mark: rotate z -> x, then put the -x... flat (now down) on the bed
    sl.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))   # shaft axis along x
    sl.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))       # mark flat (+x before) up
    # after the y-rotation the marked flat faces -z; the x-rotation turns it to +z
    sl.apply_translation(-sl.bounds[0])
    sl = clean(sl)
    sl.export(sp)
    for p in (gp, sp):
        assert trimesh.load(p).is_watertight, p
    torque = C.spr_torque_nmm(C.SPR_MAX_DEG / 2 + 90.0)
    tau = torque / (0.188 * HEX_AF ** 3)
    print('gear v3: %.1f x %.1f x %.1f, socket AF %.2f z %.1f..%.1f, wall to bolt holes %.2f'
          % (*g.extents, SOCKET_AF, SOCKET_Z0, GEAR_TOP, wall))
    print('shaft v1: AF %.2f (corners r %.2f), z %.2f..%.2f (%.2f long), magnet O%.1f x %.1f; lying %.1f x %.1f x %.1f'
          % (HEX_AF, ac, SOCKET_Z0, SHAFT_TOP, SHAFT_TOP - SOCKET_Z0, MAG_D, MAG_H, *sl.extents))
    print('shaft torsion at full wind (%.0f N.mm): %.1f MPa' % (torque, tau))
    print('wrote', gp, sp)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '.')
