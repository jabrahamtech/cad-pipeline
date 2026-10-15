"""robotarm/_mesh_as5600_magnet_sleeve - MESH generator (trimesh + manifold3d).

STOPGAP: Fusion MCP is down. Owed: a Fusion script once it is back.

WHY (Jonathan, 2026-10-15): the AS5600 magnets that arrived are O4 x 1.4 (MEASURED), not the
O6 x 2.5 every magnet pocket was drawn for (lib/cobot MAGNET_POCKET = O6.1 x 2.6: the J2 hex shaft's
top end, the J3 and J4 gear stalks). A SLEEVE adapts them without reprinting those parts:
  * outside: O(6.1 - SLEEVE_CLEAR) x SLEEVE_H, glued into the existing pocket, bottomed out
  * inside: a O(4 + LOC/2... see MAG_BORE) pocket, MAG_DEPTH deep, the magnet glued in it
  * the magnet's face lands where the old magnet's face was (0.1 under the pocket's rim), so the
    1.0 air gap to the chip is unchanged; the sleeve is concentric, so the magnet stays on the axis
Print: pocket UP, flat on the bed, no support; tiny, so a brim.
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402

POCKET_D, POCKET_H = C.MAGNET_POCKET          # 6.1 x 2.6 (as drawn in every part)
OLD_MAG_H = C.MAGNET_H                        # 2.5: the old magnet sat 0.1 under the rim
MAG_D, MAG_H = 4.0, 1.4                       # MEASURED 2026-10-15
GLUE = 0.05                                   # ASSUMED glue film under the magnet
SLEEVE_CLEAR = 0.15                           # diametral, glued (same 0.1-ish rule as the old magnet)
SLEEVE_D = POCKET_D - SLEEVE_CLEAR            # 5.95
SLEEVE_H = OLD_MAG_H                          # top face where the old magnet's face was
MAG_BORE = MAG_D + 0.1                        # glued, the old pocket's +0.1 rule
MAG_DEPTH = MAG_H + GLUE                      # magnet face flush with the sleeve top
EF = 0.3                                      # first-layer chamfer, outer bottom edge
COUNT = 6                                     # 3 joints (J2, J3, J4) + 3 spares


def frustum(r0, r1, z0, z1, n=96):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return trimesh.convex.convex_hull(np.vstack([np.c_[r0 * np.cos(a), r0 * np.sin(a), np.full(n, z0)],
                                                 np.c_[r1 * np.cos(a), r1 * np.sin(a), np.full(n, z1)]]))


def sleeve():
    r = SLEEVE_D / 2
    body = frustum(r - EF, r, 0.0, EF).union(cylinder(radius=r, height=SLEEVE_H - EF + 0.01, sections=96)
                                             .apply_translation([0, 0, EF + (SLEEVE_H - EF) / 2 - 0.005]),
                                             engine='manifold')
    bore = cylinder(radius=MAG_BORE / 2, height=MAG_DEPTH + 1, sections=96)
    bore.apply_translation([0, 0, SLEEVE_H - MAG_DEPTH + (MAG_DEPTH + 1) / 2])
    return body.difference(bore, engine='manifold')


def clean(m):
    import manifold3d as mf
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                             tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    assert mm.status() == mf.Error.NoError
    o = mm.to_mesh()
    return trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts))


def main(out_dir):
    s = clean(sleeve())
    wall = (SLEEVE_D - MAG_BORE) / 2
    floor = SLEEVE_H - MAG_DEPTH
    assert s.is_watertight and len(s.split(only_watertight=False)) == 1
    assert SLEEVE_H <= POCKET_H and wall >= 0.8 and floor >= 0.8, (wall, floor)
    face_drop = (POCKET_H - SLEEVE_H) + (MAG_DEPTH - GLUE - MAG_H)   # magnet face under the pocket rim
    old_drop = POCKET_H - OLD_MAG_H
    assert abs(face_drop - old_drop) < 1e-6, 'air gap changed'
    p = os.path.join(out_dir, 'as5600_magnet_sleeve_v1.stl'); s.export(p)
    assert trimesh.load(p).is_watertight
    sc = trimesh.Scene()
    for k in range(COUNT):
        g = s.copy(); g.apply_translation([128 + (k % 3 - 1) * 14, 128 + (k // 3 - 0.5) * 14, 0])
        sc.add_geometry(g, geom_name='as5600_magnet_sleeve_%d' % k, node_name='as5600_magnet_sleeve_%d' % k)
    plate = os.path.join(out_dir, 'cobot_plate_magnet_sleeves_petg.3mf'); sc.export(plate)
    print('sleeve O%.2f x %.2f (pocket O%.2f x %.2f); magnet bore O%.2f x %.2f; wall %.2f, floor %.2f'
          % (SLEEVE_D, SLEEVE_H, POCKET_D, POCKET_H, MAG_BORE, MAG_DEPTH, wall, floor))
    print('magnet face %.2f under the pocket rim (old %.2f): air gap unchanged; %d on the plate'
          % (face_drop, old_drop, COUNT))
    print('wrote', p, plate)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
