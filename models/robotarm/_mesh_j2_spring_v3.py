"""robotarm/_mesh_j2_spring_v3 - MESH generator (trimesh + manifold3d): J2 cap v3, hub_lo v3, hub_hi v3.

v3 (Jonathan, 2026-10-16): the spring is 14 long over both legs, not 12 - the hubs get thinner and every
pin band moves to the real legs. The cap's pin brackets ('ridges') are made stronger: rib 3 -> 5 wide, the pins
reach 4.5 past each leg (was 3.5), and each bracket now stands SOLID on the floor wherever nothing sweeps
under it (it used to hang off the wall on a 45 deg gusset only).

v2 notes follow.

STOPGAP: Fusion MCP is down (2026-10-14). Owed: cobot_j2_cap.py / cobot_j2_hub_lo.py / cobot_j2_hub_hi.py
+ the lib/cobot J2 spring block, rewritten for the spring below.

WHY (Jonathan, 2026-10-14): the AliExpress spring went in instead of the TO-5201RCS. Calipered:
coil body 12, OD 20, wire 2, legs 15.5 (from the coil). The old cap pins (u +-18) sit beyond the
leg ends, and the hub discs slipped on the D. He chose: REPRINT THE CAP with the pins moved in.
  * hubs: HEX bores (AF 8.5 shaft + LOC) on the new hex shaft (_mesh_j2_gear_v3_shaft), a notch
    marking the flat that faces -v at neutral (= the shaft's grooved flat). Thickened to fill the
    shorter coil's room: the stack between the cap floor and the lid is unchanged.
  * every pin still sits just under the legs' line (in-line 180 deg legs): hub pins at u -+HUB_PIN_U,
    cap pins at u -+CAP_PIN_U, the cap pins as BRACKETS off the wall, each only in its own leg's band
    (a full-height column there would cut through the hub discs' sweep). Undersides 45 deg to the wall.
  * the hub_lo now slides on the hex, so the cap floor gets a O15 x FREE RING round the shaft bore for
    hub_lo to run on (sets the old shoulder's gap, small friction radius).
  * the cap v2 = cap v1 (plate 1 mesh) with everything inside the wall above the floor removed (the old
    pins + ribs), plus the ring and the two new brackets. Wall, lugs, bump, wire channel, screws untouched.
Frame: the upper arm's x (J2 axis) and (u, v) of lib/cobot's J2 spring block, at neutral.
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO)
import lib.cobot as C  # noqa: E402

FREE, LOC = C.FREE, C.LOC
# --- the spring (MEASURED 2026-10-14) ---------------------------------------------------
WIRE, OD, BODY, LEG = 2.0, 20.0, 14.0, 15.5   # BODY MEASURED 2026-10-16: 14 over both legs (was 12)
RC = (OD - WIRE) / 2                      # 9.0: the legs run tangent at v = -RC
RATE_EST = 207000 * WIRE ** 4 / (64 * RC * 2 * 6) * np.pi / 180   # N.mm/deg, 6 coils - ESTIMATE, not measured
# --- the fixed stack (unchanged parts) -------------------------------------------------------
FLOOR_TOP = C.CAP_FLOOR_TOP               # 131.8
LID_X0 = C.LID[0]                         # 156.67
SHAFT_AF = 8.5                            # _mesh_j2_gear_v3_shaft HEX_AF
SHAFT_CORNER_R = SHAFT_AF / np.sqrt(3) - 0.3
BORE_AF = SHAFT_AF + LOC
# --- new stack ----------------------------------------------------------------------------
RING = (5.6 + 0.4, 7.5, FREE)             # (r_in, r_out, h) on the cap floor round the O10.6 shaft bore
HUB_LO_X0 = FLOOR_TOP + RING[2]           # 132.2 = the old SHOULDER_X
HUB_T = (LID_X0 - FREE - HUB_LO_X0 - BODY - 2 * FREE) / 2
HUB_LO = (HUB_LO_X0, HUB_LO_X0 + HUB_T)
COIL = (HUB_LO[1] + FREE, HUB_LO[1] + FREE + BODY)
LEG_LO = (COIL[0], COIL[0] + WIRE)
LEG_HI = (COIL[1] - WIRE, COIL[1])
HUB_HI = (COIL[1] + FREE, COIL[1] + FREE + HUB_T)
PIN_D = C.SPR_PIN_D                       # 5
PIN_V = -(RC + WIRE / 2 + PIN_D / 2)      # -12.5: every pin's top touches the legs' underside
PIN_H = 4.5                               # past the leg (v2: 3.5); <= (BODY - 2*WIRE - FREE)/2
HUB_PIN_U = 3.5
R_HUB_PIN = np.hypot(HUB_PIN_U, PIN_V)
HUB_R = R_HUB_PIN + PIN_D / 2 + 1.2
CAP_PIN_U = 13.5
R_CAP_PIN = np.hypot(CAP_PIN_U, PIN_V)
RIB_W = 5.0                               # v2: 3.0
# v3 COLLAR (Jonathan, 2026-10-16: 'make that ridge all the way around'): a solid ring all round the inside of
# the cup, from the floor up to the top of the upper pin, starting just outside the swinging legs' reach.
# The two pins stand out of it as short stubs. (A ring at the pins' own radius would block the legs.)
R_COLLAR = np.hypot(LEG, RC) + WIRE / 2 + FREE          # 19.32
SCREW_ACCESS_D = C.CBORE_D + 1.1                        # 7.0: a hex key and the screw head pass the collar
WALL_IN = C.CAP_A - C.CAP_WALL            # 25.5 apothem
# cap v1 mesh <-> arm frame: mesh = (CX - u, CY - v, x - CAP_X0) (measured off the floor holes)
CX, CY, CAP_X0 = 142.27, 33.5, C.CAP_X0
MARK_W, MARK_D, MARK_L = 1.2, 0.6, 3.0
EF = 0.3


def cyl(u, v, r, x0, x1, n=96):
    return cylinder(radius=r, height=x1 - x0, sections=n).apply_translation([u, v, (x0 + x1) / 2])


def hex_prism(af, x0, x1, flat_dir_deg):
    """Hex prism along x, one flat's outward normal at flat_dir_deg in (u, v)."""
    h = cylinder(radius=af / np.sqrt(3), height=x1 - x0, sections=6)
    h.apply_transform(trimesh.transformations.rotation_matrix(np.radians(30 + flat_dir_deg), [0, 0, 1]))
    return h.apply_translation([0, 0, (x0 + x1) / 2])


def cone_hull(r0, z0, r1, z1, n=180):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = [np.c_[r * np.cos(a), r * np.sin(a), np.full(n, z)] if r > 0 else np.array([[0, 0, z]])
           for r, z in ((r0, z0), (r1, z1))]
    return trimesh.convex.convex_hull(np.vstack(pts))


def clean(m):
    import manifold3d as mf
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                             tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    assert mm.status() == mf.Error.NoError
    o = mm.to_mesh()
    return trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts))


def U(a, b):
    return a.union(b, engine='manifold')


def D(a, b):
    return a.difference(b, engine='manifold')


def I(a, b):
    return a.intersection(b, engine='manifold')


def hub(x0, x1, pin_u, pin_x0, pin_x1, mark_at_x):
    m = cyl(0, 0, HUB_R, x0, x1, n=180)
    m = U(m, cyl(pin_u, PIN_V, PIN_D / 2, pin_x0, pin_x1))
    m = D(m, hex_prism(BORE_AF, x0 - 1, x1 + 1, -90))           # a flat facing -v
    mark = box(extents=[MARK_W, MARK_L + 0.5, 2 * MARK_D])
    mark.apply_translation([0, -(BORE_AF / 2 + MARK_L / 2 - 0.25), mark_at_x])
    m = D(m, mark)
    return m


def bracket(su, x0, x1):
    """A cap pin at (su*CAP_PIN_U, PIN_V), x0..x1, tied to the wall by a radial rib; flat underside
    inside HUB_R + FREE, then 45 deg down and out to the wall/floor."""
    p = np.array([su * CAP_PIN_U, PIN_V])
    d = p / np.linalg.norm(p)
    L = WALL_IN + 0.8 - R_CAP_PIN
    rib = box(extents=[L, RIB_W, x1 - (FLOOR_TOP - 1)])
    rib.apply_translation([R_CAP_PIN + L / 2, 0, (x1 + FLOOR_TOP - 1) / 2])
    rib.apply_transform(trimesh.transformations.rotation_matrix(np.arctan2(d[1], d[0]), [0, 0, 1]))
    col = cyl(p[0], p[1], PIN_D / 2, FLOOR_TOP - 1, x1)
    solid = U(col, rib)
    r_flat = HUB_R + FREE
    big = cyl(0, 0, 40, FLOOR_TOP - 2, x1 + 1, n=180)
    below = I(box(extents=[100, 100, 100]).apply_translation([0, 0, x0 - 50]),
              cone_hull(0.0, x0 + r_flat, 60.0, x0 + r_flat - 60.0))
    hung = I(solid, D(big, below))
    # SOLID TO THE FLOOR wherever nothing sweeps under the bracket: past the hub discs (lower bracket) or
    # past the lower leg's swing (upper bracket, which sits above that leg's band)
    r_support = HUB_R + FREE if su < 0 else np.hypot(LEG, RC) + WIRE / 2 + FREE
    ring = D(cyl(0, 0, 40, FLOOR_TOP - 1, x1, n=180), cyl(0, 0, r_support, FLOOR_TOP - 2, x1 + 1, n=180))
    return U(hung, I(solid, ring))


def cap_v2(cap1):
    to_arm = np.diag([-1.0, -1.0, 1.0, 1.0]); to_arm[:3, 3] = [CX, CY, -CAP_X0]   # arm -> mesh
    m = cap1.copy(); m.apply_transform(np.linalg.inv(to_arm))                        # now in arm (u, v, x)
    # the inside of the wall above the floor: the wall's inner 12-gon, taken where the old pins stop
    top = m.bounds[1, 2]
    sec = m.section(plane_origin=[0, 0, top - 0.2], plane_normal=[0, 0, 1])
    p2, T = sec.to_2D()
    inner = [trimesh.path.polygons.Polygon(h) for pg in p2.polygons_full for h in pg.interiors]
    inner = max(inner, key=lambda q: q.area).buffer(-0.01)
    cut = trimesh.creation.extrude_polygon(inner, height=top - FLOOR_TOP + 1)
    cut.apply_transform(T)
    if cut.bounds[1, 2] - (top - 0.2) < 0.5:          # extruded downward: flip it up
        cut.apply_translation([0, 0, (top - 0.2) - cut.bounds[0, 2]])
    cut.apply_translation([0, 0, FLOOR_TOP - cut.bounds[0, 2]])
    assert cut.bounds[0, 2] == FLOOR_TOP and cut.bounds[1, 2] > top
    m = D(m, cut)
    m = U(m, D(cyl(0, 0, RING[1], FLOOR_TOP - 0.5, FLOOR_TOP + RING[2], n=180),
               cyl(0, 0, RING[0], FLOOR_TOP - 1, FLOOR_TOP + 1, n=180)))
    m = U(m, bracket(-1, LEG_LO[0], LEG_LO[1] + PIN_H))      # holds the LOWER leg (along -u)
    m = U(m, bracket(+1, LEG_HI[0] - PIN_H, LEG_HI[1]))      # holds the UPPER leg (along +u)
    collar_top = LEG_HI[1]
    # a disc that reaches 1 into the 12-gon wall everywhere (inner corners r 26.4, outer apothem 27.5)
    collar = cyl(0, 0, WALL_IN / np.cos(np.pi / 12) + 0.1, FLOOR_TOP - 0.5, collar_top, n=240)
    assert WALL_IN / np.cos(np.pi / 12) + 0.1 < C.CAP_A, 'collar would poke through the wall'
    collar = D(collar, cyl(0, 0, R_COLLAR, FLOOR_TOP - 2, collar_top + 2, n=240))
    for (u, v) in C.CAP_SCREWS:
        collar = D(collar, cyl(u, v, SCREW_ACCESS_D / 2, FLOOR_TOP - 1, collar_top + 1))
    m = U(m, collar)
    return m, inner, top


def checks(cap, inner, hub_lo, hub_hi):
    for m in (cap, hub_lo, hub_hi):
        assert m.is_watertight and len(m.split(only_watertight=False)) == 1
    assert HUB_T >= 3.0, HUB_T
    assert BODY - 2 * WIRE - 2 * PIN_H >= FREE, 'the two pin bands overlap'
    assert abs(HUB_HI[1] + FREE - LID_X0) < 1e-6
    assert C.SHAFT_TOP <= HUB_HI[1], 'the shaft end above the top hub'
    assert (OD - 2 * WIRE) / 2 - SHAFT_CORNER_R >= FREE, 'coil on the shaft'
    assert R_HUB_PIN - PIN_D / 2 - OD / 2 >= 0.3, 'hub pin on the coil OD (winding only shrinks it)'
    assert R_CAP_PIN - PIN_D / 2 >= R_HUB_PIN + PIN_D / 2 + FREE, 'cap pin in a hub pin sweep'
    assert LEG - CAP_PIN_U >= 1.8, 'the leg passes the cap pin centre by %.2f' % (LEG - CAP_PIN_U)
    assert LEG_LO[1] + PIN_H + FREE <= LEG_HI[0] - PIN_H, 'hub_lo pin band into hub_hi pin band'
    r_leg_end = np.hypot(LEG, RC) + WIRE / 2
    assert r_leg_end + FREE <= WALL_IN, 'leg ends on the wall'
    # the other band's bracket stays out of a swinging leg's band within its sweep radius:
    # +u bracket underside (45 deg from HUB_R+FREE at LEG_HI[0]-PIN_H) at r_leg_end is above LEG_LO[1]
    assert (LEG_HI[0] - PIN_H) - (r_leg_end - (HUB_R + FREE)) >= LEG_LO[1] + FREE, 'upper bracket on the lower leg'
    # nothing of the cap inside the hub discs' sweep, in the hub bands
    for x0, x1 in (HUB_LO, HUB_HI):
        for x in np.linspace(x0 + 0.05, x1 - 0.05, 6):
            s = cap.section(plane_origin=[0, 0, x], plane_normal=[0, 0, 1])
            if s is None:
                continue
            r = np.hypot(s.vertices[:, 0], s.vertices[:, 1])
            near = r[r < HUB_R + FREE - 0.02]
            assert near.size == 0, 'cap inside a hub disc sweep at x %.2f r %.2f' % (x, near.min())
    # pins fully cover their leg's band
    return r_leg_end


def to_print_cap(m):
    t = np.diag([-1.0, -1.0, 1.0, 1.0]); t[:3, 3] = [CX, CY, -CAP_X0]
    m = m.copy(); m.apply_transform(t); return m


def main(plate1, out_dir):
    s = trimesh.load(plate1, force='scene')
    cap1 = s.geometry['cobot_j2_cap']
    cap, inner, top = cap_v2(cap1)
    hub_lo = hub(HUB_LO[0], HUB_LO[1], -HUB_PIN_U, HUB_LO[1] - 0.01, LEG_LO[1] + PIN_H, HUB_LO[1])
    hub_hi = hub(HUB_HI[0], HUB_HI[1], +HUB_PIN_U, LEG_HI[0] - PIN_H, HUB_HI[0] + 0.01, HUB_HI[1])
    cap, hub_lo, hub_hi = clean(cap), clean(hub_lo), clean(hub_hi)
    r_leg_end = checks(cap, inner, hub_lo, hub_hi)
    # print orientations: cap floor down (as plate 1); hub_lo disc down pin up; hub_hi flipped, pin up
    capp = clean(to_print_cap(cap))
    lo = hub_lo.copy(); lo.apply_translation(-lo.bounds[0])
    hi = hub_hi.copy(); hi.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    hi.apply_translation(-hi.bounds[0])
    lo, hi = clean(lo), clean(hi)
    paths = {}
    for name, m in (('cobot_j2_cap_v3', capp), ('cobot_j2_hub_lo_v3', lo), ('cobot_j2_hub_hi_v3', hi)):
        p = os.path.join(out_dir, name + '.stl'); m.export(p)
        assert trimesh.load(p).is_watertight, p
        paths[name] = p
    print('stack x: ring %.2f..%.2f | hub_lo %.2f..%.2f (T %.2f) | coil %.2f..%.2f | hub_hi %.2f..%.2f | lid %.2f'
          % (FLOOR_TOP, HUB_LO_X0, *HUB_LO, HUB_T, *COIL, *HUB_HI, LID_X0))
    print('pins O%.0f at v %.2f: hub u -+%.1f (r %.2f, sweep %.2f), cap u -+%.1f (r %.2f); hub disc r %.2f'
          % (PIN_D, PIN_V, HUB_PIN_U, R_HUB_PIN, R_HUB_PIN + PIN_D / 2, CAP_PIN_U, R_CAP_PIN, HUB_R))
    print('leg passes the cap pin centre by %.2f; leg-end sweep r %.2f (wall %.1f)' % (LEG - CAP_PIN_U, r_leg_end, WALL_IN))
    print('spring rate ESTIMATE %.2f N.mm/deg (designed 7.34); at 90 deg %.0f N.mm vs gravity peak %.0f'
          % (RATE_EST, RATE_EST * 90, C.SPR_GRAVITY_PEAK_NMM))
    for n, m in (('cap', capp), ('hub_lo', lo), ('hub_hi', hi)):
        print('%-7s %.1f x %.1f x %.1f  %.1f g solid PETG' % (n, *m.extents, m.volume * 1.27 / 1000))
    print('cap v1 -> v2 volume %.1f -> %.1f cm3' % (cap1.volume / 1000, capp.volume / 1000))
    return paths


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '.')
