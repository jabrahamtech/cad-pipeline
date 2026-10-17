"""robotarm/_mesh_as5600_glue_pins - MESH generator (trimesh + manifold3d).

STOPGAP: Fusion MCP is down. Owed: a Fusion script once it is back. Spec: specs/robotarm/as5600_4hole_clamp.md

WHY (Jonathan, 2026-10-17): the 4-hole clamp halves (_mesh_as5600_4hole_clamp) "get in the way of some of
the ports" - each half's web crosses the middle of a board edge. REPLACED by 4 GLUE PINS per board, one in
each of its 4 holes: a shaft through the hole, a small head on the board's top face. Nothing reaches a board
edge (the head stops 2.25 short of it, the clamp's own pad-row rule), and the M2 clamp screws are not used.
The board still drops into the existing 23.4 pocket chip-down (that locates it; the magnet gap is unchanged).
Fit: a drop of CA on the shaft tip, push it through the hole onto the pocket floor; the head holds the board.
The shaft stops GLUE short of the floor on a 1.6 board, so a thinner board still seats the head.
Print: head down, shaft up, no support.
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402

BOARD = 23.0                     # MEASURED 2026-10-14
HOLE_PITCH = 15.5                # MEASURED, centre to centre, both ways
BOARD_T = C.BOARD_T              # ASSUMED 1.6 (not calipered)
HOLE_D_MIN = 2.0                 # ASSUMED - the board's holes are at least this
SHAFT_D = HOLE_D_MIN - C.LOC     # 1.8
GLUE = 0.1                       # shaft tip short of the pocket floor (glue film)
SHAFT_L = BOARD_T - GLUE         # 1.5
HEAD_D = 3.0                     # the clamp's contact ring: stays off the pad rows
HEAD_H = 0.8
EF = 0.2                         # first-layer chamfer, head's bed edge
TIP = 0.2                        # lead-in on the shaft tip
PER_BOARD, BOARDS, SPARES = 4, 3, 4


def frustum(r0, r1, z0, z1, n=64):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return trimesh.convex.convex_hull(np.vstack([np.c_[r0 * np.cos(a), r0 * np.sin(a), np.full(n, z0)],
                                                 np.c_[r1 * np.cos(a), r1 * np.sin(a), np.full(n, z1)]]))


def cyl(r, z0, z1, n=64):
    c = cylinder(radius=r, height=z1 - z0, sections=n)
    c.apply_translation([0, 0, (z0 + z1) / 2])
    return c


def clean(m):
    import manifold3d as mf
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                             tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    assert mm.status() == mf.Error.NoError
    o = mm.to_mesh()
    return trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts))


def pin():
    """Print frame: head on the bed (z 0), shaft up."""
    rh, rs = HEAD_D / 2, SHAFT_D / 2
    head = frustum(rh - EF, rh, 0.0, EF).union(cyl(rh, EF - 0.01, HEAD_H), engine='manifold')
    shaft = cyl(rs, HEAD_H - 0.01, HEAD_H + SHAFT_L - TIP).union(
        frustum(rs, rs - TIP, HEAD_H + SHAFT_L - TIP - 0.001, HEAD_H + SHAFT_L), engine='manifold')
    return head.union(shaft, engine='manifold')


def main(out_dir):
    m = clean(pin())
    assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    reach = HOLE_PITCH / 2 + HEAD_D / 2
    assert reach <= BOARD / 2 - 2.2, 'head on a pad row'
    assert SHAFT_L < BOARD_T and SHAFT_D < HOLE_D_MIN
    # the head stays inside the old clamp's height above the board (BAR_T 2.0): nothing new above the board
    assert HEAD_H <= 2.0
    p = os.path.join(out_dir, 'as5600_glue_pin_v1.stl'); m.export(p)
    assert trimesh.load(p).is_watertight
    n = PER_BOARD * BOARDS + SPARES
    print('pin: head O%.1f x %.1f, shaft O%.1f x %.1f (board %.1f ASSUMED, hole >= O%.1f ASSUMED); head reaches %.2f '
          'of the board\'s %.1f half-width; %d to print (%d boards x %d + %d spares), %.1f mm3 each'
          % (HEAD_D, HEAD_H, SHAFT_D, SHAFT_L, BOARD_T, HOLE_D_MIN, reach, BOARD / 2, n, BOARDS, PER_BOARD, SPARES,
             m.volume))
    print('wrote', p)
    return m, n


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
