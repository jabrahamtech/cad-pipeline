"""robotarm/_mesh_as5600_4hole_clamp - MESH generator (trimesh + manifold3d).

STOPGAP: Fusion MCP is down (2026-10-14), so this part is built as a mesh, like
_mesh_j4_pinion_v5. A Fusion script (models/robotarm/as5600_4hole_clamp.py) is
owed before this is treated as source of truth. Spec: specs/robotarm/as5600_4hole_clamp.md

WHAT IT IS: converts the existing AS5600 mounts (J3 plate, J4 plate, J2 cap lid -
all the same 23.4 pocket x 1.0 deep with 2 x M2 pilots at +-CLAMP_OFF) to hold the
new 23 x 23 board BY ITS 4 HOLES, with no drilling and no reprint of the mount.
The board still drops into the pocket chip-down, so the magnet gap is unchanged.
Each mount takes TWO halves. A half = a bar across two of the board's holes (pegs
locate it, Ø4 rings press the copper round each hole) + a web out to a foot that
sits on the plate and takes the EXISTING M2 x 5 + washer in the existing pilot.
The foot stands PRELOAD lower than the board top so tightening clamps the board.

Frame: u along the bar, v from the board centre toward the clamp screw, z = 0 on
the board's top face, +z up (away from the board). Printed flipped: top face on
the bed, pegs and foot pointing up - no supports.
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402

# --- the board (Jonathan, 2026-10-14) -----------------------------------------
BOARD = 23.0                 # MEASURED 23 x 23 (same as lib/cobot BOARD)
HOLE_PITCH = 15.5            # MEASURED, centre to centre, both ways; chip in the middle
BOARD_T = C.BOARD_T          # ASSUMED 1.6 - not measured; see spec
HOLE_D_MIN = 2.0             # ASSUMED - the board's holes are at least this (M2 boards are 2.2-2.5)

# --- this part -------------------------------------------------------------------
PEG_D = HOLE_D_MIN - C.LOC                    # locational in the board's hole
PEG_L = BOARD_T - 0.3                         # stops short of the pocket floor
RING_D = 3.0                                  # the only faces that touch the board (the hole's copper ring)
RELIEF = 0.5                                  # elsewhere the bar clears top-side parts by this
BAR_T = 2.0                                   # top of the bar / web / lug, above the board top
BAR_W = 4.0
BAR_HALF_U = HOLE_PITCH / 2 + RING_D / 2 - 0.25   # 9.0: stops short of a pad row on the u edges
WEB_W = 5.0
LUG_R = 2.5                                   # an M2 washer (OD 5)
SCREW_D = C.M2['clearance']                   # the existing M2 x 5 passes through
PRELOAD = 0.15                                # foot stands this lower than plate-top + board proud
PROUD = BOARD_T - C.BOARD_POCKET_H            # 0.6: the board's top above the plate top
FOOT_V0 = C.BOARD_POCKET / 2 + 0.1            # 11.8: the foot lands on the plate, past the pocket edge
FOOT_Z0 = -PROUD + PRELOAD                    # -0.45
EF = 0.3                                      # first-layer chamfer on the screw hole (bed side)
EPS = 0.01


def slab(u0, u1, v0, v1, z0, z1):
    b = box(extents=[u1 - u0, v1 - v0, z1 - z0])
    b.apply_translation([(u0 + u1) / 2, (v0 + v1) / 2, (z0 + z1) / 2])
    return b


def cyl(u, v, r, z0, z1, n=64):
    c = cylinder(radius=r, height=z1 - z0, sections=n)
    c.apply_translation([u, v, (z0 + z1) / 2])
    return c


def frustum(u, v, r0, r1, z0, z1, n=64):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    p = np.vstack([np.c_[u + r0 * np.cos(a), v + r0 * np.sin(a), np.full(n, z0)],
                   np.c_[u + r1 * np.cos(a), v + r1 * np.sin(a), np.full(n, z1)]])
    return trimesh.convex.convex_hull(p)


def half():
    hp = HOLE_PITCH / 2
    cv = C.CLAMP_OFF
    parts = [
        slab(-BAR_HALF_U, BAR_HALF_U, hp - BAR_W / 2, hp + BAR_W / 2, RELIEF, BAR_T),       # the bar
        slab(-WEB_W / 2, WEB_W / 2, hp, FOOT_V0, RELIEF, BAR_T),                             # web over the board
        slab(-WEB_W / 2, WEB_W / 2, FOOT_V0, cv, FOOT_Z0, BAR_T),                            # web on the plate
        cyl(0.0, cv, LUG_R, FOOT_Z0, BAR_T),                                                 # the lug / foot
    ]
    for su in (-1, 1):
        parts.append(cyl(su * hp, hp, RING_D / 2, 0.0, RELIEF + EPS))                        # contact ring
        parts.append(cyl(su * hp, hp, PEG_D / 2, -PEG_L, EPS))                               # peg
    m = parts[0]
    for p in parts[1:]:
        m = m.union(p, engine='manifold')
    m = m.difference(cyl(0.0, cv, SCREW_D / 2, FOOT_Z0 - 1, BAR_T + 1), engine='manifold')
    # 45 deg cone that crosses the bore wall at BAR_T - EF (starts inside the hole: no coincident rings)
    m = m.difference(frustum(0.0, cv, SCREW_D / 2 - 0.3, SCREW_D / 2 + EF + 0.05, BAR_T - EF - 0.3, BAR_T + 0.05, n=90),
                     engine='manifold')
    return m


def checks(m):
    assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    hp = HOLE_PITCH / 2
    assert hp + RING_D / 2 <= BOARD / 2 - 0.5, 'contact ring off the board edge'
    assert FOOT_V0 - LUG_R < C.CLAMP_OFF, 'the foot must reach under the screw'
    assert max(BAR_HALF_U, hp + RING_D / 2) <= BOARD / 2 - 2.2, 'the bar/ring reaches a pad row on the u edges'
    assert PEG_L < BOARD_T, 'the peg would bottom on the pocket floor'
    # J4: the lug clears the forearm plate's standoffs (the tightest neighbour)
    for s in C.FA_STANDOFFS:
        for c in C.J4_CLAMPS:
            assert np.hypot(s[0] - c[0], s[1] - c[1]) - LUG_R - C.STANDOFF_R >= C.FREE, 'lug on a J4 standoff'
    # the half stays inside the forearm shell (the smallest link) about the board axis
    r_far = max(np.hypot(BAR_HALF_U, hp + BAR_W / 2), C.CLAMP_OFF + LUG_R)
    assert r_far <= C.FA_IN - C.LOC, 'outside the forearm shell'
    return r_far


def main(out_dir):
    m = half()
    r_far = checks(m)
    flip = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    m.apply_transform(flip)
    m.apply_translation([0, 0, -m.bounds[0, 2]])
    stl = os.path.join(out_dir, 'as5600_4hole_clamp_v1.stl')
    m.export(stl)
    assert trimesh.load(stl).is_watertight, 'STL round-trip'
    sc = trimesh.Scene()
    # 3 mounts x 2 halves, 3 columns x 2 rows round the bed centre (X2D 256 x 256)
    w, h = m.extents[0], m.extents[1]
    k = 0
    for i in range(3):
        for j in range(2):
            g = m.copy()
            g.apply_translation([128 + (i - 1) * (w + 6) - m.centroid[0], 128 + (j - 0.5) * (h + 6) - m.centroid[1], 0])
            sc.add_geometry(g, geom_name='as5600_4hole_clamp_%d' % k, node_name='as5600_4hole_clamp_%d' % k)
            k += 1
    plate = os.path.join(out_dir, 'cobot_plate_as5600_clamps_petg.3mf')
    sc.export(plate)
    print('half: %.2f x %.2f x %.2f mm, %.2f cm3 (%.2f g PETG solid), reach r %.2f from the board axis'
          % (*m.extents, m.volume / 1000, m.volume * 1.27 / 1000, r_far))
    print('board-contact rings at +-%.2f, pegs O%.2f x %.2f, foot preload %.2f, screw hole O%.2f at v %.2f'
          % (HOLE_PITCH / 2, PEG_D, PEG_L, PRELOAD, SCREW_D, C.CLAMP_OFF))
    print('wrote', stl, plate)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
