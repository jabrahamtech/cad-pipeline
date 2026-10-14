"""J4 pinion v5 = v4 with 5.2 mm removed from the FRONT face (Jonathan 2026-10-14).
v3 is the watertight base; v4 = v3 with the broach bore 0.10 smaller (O4.85 -> O4.75, z 3.7..9.4),
so the ring that makes that change is re-added here. Frame: z 0 = old front face, +z toward the servo."""
import sys, numpy as np, trimesh
from trimesh.creation import cylinder, annulus
src_v3, src_v4, out = sys.argv[1:4]
TRIM = 5.2
LEAD = 0.5          # 45 deg lead-in on the new front tooth tips (lib/cobot LEAD_IN)
EF = 0.4            # first-layer chamfer on the bore's bottom edge (design rules)
v3 = trimesh.load(src_v3); v4 = trimesh.load(src_v4)
z1 = v3.bounds[1, 2]
r_tip = 10.0
keep = trimesh.creation.box(extents=[40, 40, z1 - TRIM]); keep.apply_translation([0, 0, (z1 + TRIM) / 2])
m = v3.intersection(keep, engine='manifold')
# re-make the bore from solid: fill it, then cut O4.75 (no coincident shells)
fill = cylinder(radius=3.0, height=9.4 - TRIM, sections=96); fill.apply_translation([0, 0, (9.4 + TRIM) / 2])
m = m.union(fill, engine='manifold')
bore = cylinder(radius=4.75 / 2, height=9.7 - TRIM + 1.0, sections=200); bore.apply_translation([0, 0, (9.7 + TRIM - 1.0) / 2])
m = m.difference(bore, engine='manifold')
# lead-in: remove everything outside a 45 deg cone that is r_tip-LEAD at the new face
z0 = TRIM
cone_h = 4.0
outer = cylinder(radius=r_tip + 2, height=LEAD + 0.02, sections=256); outer.apply_translation([0, 0, z0 + (LEAD - 0.02) / 2])
keepcone = trimesh.creation.cone(radius=r_tip - LEAD + cone_h, height=cone_h, sections=256)
# cone apex up by default: flip so it widens with +z
keepcone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
keepcone.apply_translation([0, 0, z0 + cone_h])        # base radius r_tip-LEAD+cone_h at z0+cone_h? fix below
# build the frustum directly instead: r(z) = r_tip - LEAD + (z - z0)
def frustum(r0, r1, za, zb, n=256):
    a = np.linspace(0, 2*np.pi, n, endpoint=False)
    bot = np.c_[r0*np.cos(a), r0*np.sin(a), np.full(n, za)]
    top = np.c_[r1*np.cos(a), r1*np.sin(a), np.full(n, zb)]
    return trimesh.convex.convex_hull(np.vstack([bot, top]))
cut = outer.difference(frustum(r_tip - LEAD - 0.02, r_tip - LEAD - 0.02 + LEAD + 0.6, z0 - 0.02, z0 + LEAD + 0.58), engine='manifold')
m = m.difference(cut, engine='manifold')
# bore bottom chamfer (elephant foot): 45 deg, EF
m = m.difference(frustum(4.75/2 + EF + 0.02, 4.75/2 - 0.3, z0 - 0.02, z0 + EF + 0.32), engine='manifold')
m.apply_translation([0, 0, -TRIM])
m.export(out)
r = trimesh.load(out); assert r.is_watertight, 'STL round-trip not watertight'
print('bounds', m.bounds.round(3).tolist(), 'watertight', m.is_watertight, 'bodies', len(m.split(only_watertight=False)), 'vol', round(m.volume, 1))
# compare with v4 above the cut
for z in [0.1, 0.3, 0.6, 1.0, 2.0, 3.0, 4.0, 4.15, 4.25, 4.5, 4.75]:
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]); p, _ = s.to_2D()
    s4 = v4.section(plane_origin=[0, 0, z + TRIM], plane_normal=[0, 0, 1]); p4, _ = s4.to_2D()
    def d(p):
        pg = p.polygons_full[0]; e = np.array(pg.exterior.coords)
        h = [2*np.hypot(*(np.array(i.coords) - np.array(i.coords).mean(0)).T).mean() for i in pg.interiors]
        return '%.2f tipR %.2f bore %s area %.2f' % (z, np.hypot(*e.T).max(), ['%.2f' % x for x in h], pg.area)
    print('v5', d(p), '| v4', d(p4).split(' ', 1)[1])
