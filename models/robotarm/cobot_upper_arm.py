"""robotarm/cobot_upper_arm - Fusion MCP generating script.

Rebuilds `robotarm_cobot_upper_arm` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py. Its lid is cobot_upper_arm_cover.

THE UPPER ARM BODY: a straight 12-gon capsule (a 28 both ends = the tower),
the servo link (S) at BOTH of its joints, open on its +x face.
  * the -x face is ONE 3 mm JOINT WALL. The tower's J2 spigot and the
    forearm plate's J3 spigot pass through its two bores; the J2 and J3
    OUTPUT GEARS, bolted to those spigots from in here, trap it
  * J2: the MG995 360 on the J2 PLATE (a bench unit - lib/cobot), its 22T
    pinion in mesh with the 36T J2 gear, 1.64:1. The plate's 3 posts stand
    here; its holes are slotted along the mesh line so the mesh is SET
  * J3: 4:1 in two stages. The COMPOUND IDLER turns on a O3 x 35 dowel
    pressed into the blind hole in the IDLER BOSS on the wall; the J3 PLATE
    (SG90 360 + its 18T pinion + the J3 encoder) drops over the pin, which
    locates it. Its 3 posts stand here
  * six COVER CORBELS off the shell, above both plates, on 45 deg cones
  * every gear sweep and servo case is CUT at the end: no feature here can
    ever sit in one (lib/cobot asserts it; the cut makes it structural)
  * the loom: in at the J2 end cap port, over the J2 plate, down the lane
    beside the MG995 (v -21), over the J3 plate, out of the J3 end cap port

ASSEMBLY (specs/robotarm/cobot.md has the whole sequence):
  1. over the tower's J2 spigot and the forearm's J3 spigot, cover off
  2. the J2 gear onto its register: 4 x M3 x 30; the J3 gear: 3 x M3 x 30
     (through the forearm plate into the forearm's bosses)
  3. the dowel into the idler boss, the idler onto it
  4. the J3 plate unit over the pin, pinion into mesh: 3 x M3 x 10
  5. the J2 plate unit, pinion into mesh, set with 0.1 paper: 3 x M3 x 10
  6. the loom through the ports and down the lane, then the cover: 6 x M3 x 8

Print: JOINT WALL DOWN (the -x face on the bed), no support. The bores are
vertical; posts and bosses rise straight; the corbels stand on 45 deg cones;
the two O8 ports are horizontal holes through a vertical wall.
Frame: arm x (the joint axes), y = u along the link from J2 (0) to J3 (L1),
z = v across it, at zero pitch. J2 on the origin.
"""

import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

import lib.cobot as C  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_cobot_upper_arm'
BODY_NAME = 'cobot_upper_arm'
PREFIX = 'cua_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_upper_arm')
PH_FORM = 'wall + shell'
PH_JOINTS = 'joint bores'
PH_POSTS = 'plate posts + idler boss'
PH_COVER = 'cover corbels'
PH_LOOM = 'ports'
PH_KEEP = 'keep-outs'
PHASES = [PH_FORM, PH_JOINTS, PH_POSTS, PH_COVER, PH_LOOM, PH_KEEP]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value      # cm

    def mm(v_cm):
        return '%.5f mm' % (v_cm * 10)

    param('x0', '%.4f mm' % C.UA_X0, 'lib/cobot UA_X0 - the joint wall\'s -x face')
    param('wall_t', '%.4f mm' % C.JOINT_WALL, 'lib/cobot JOINT_WALL')
    param('x_top', '%.4f mm' % (C.UA_X1 - C.COVER_T), 'the shell\'s open edge = the cover seat')
    param('shell', '%.4f mm' % C.SHELL, 'lib/cobot SHELL')
    param('a', '%.4f mm' % C.UA_A, 'lib/cobot UA_A - both ends')
    param('l1', '%.4f mm' % C.L1, 'J2 -> J3')
    param('bore2', '%.4f mm' % C.J2.bore, 'lib/cobot J2 - the tower spigot runs in it')
    param('bore3', '%.4f mm' % C.J3.bore, 'lib/cobot J3 - the forearm plate\'s spigot runs in it')
    param('post_r', '%.4f mm' % C.BOSS_R, 'lib/cobot BOSS_R - a post / boss')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('m3_deep', '8.0 mm', 'pilot depth: M3 x 10 through a plate, M3 x 8 through the cover')
    param('j2_post_top', '%.4f mm' % C.UA_J2_PLATE_X0, 'lib/cobot - the J2 plate sits on these')
    param('j3_post_top', '%.4f mm' % C.UA_J3_PLATE_X0, 'lib/cobot - the J3 plate sits on these')
    param('idler_boss_top', '%.4f mm' % C.IDLER_BOSS_TOP, 'lib/cobot - FREE under the idler')
    param('pin_hole', '%.4f mm' % C.IDLER_PIN_D, 'the O3 dowel, PRESSED (a printed O3 comes out ~2.9)')
    param('pin_bottom', '%.4f mm' % C.IDLER_PIN_BOTTOM, 'lib/cobot - a MIN_WALL floor under the pin')
    param('corbel_x0', '%.4f mm' % C.UA_COVER_X0, 'lib/cobot - a corbel cone\'s apex, above both plates')
    param('port_d', '%.4f mm' % C.PORT_D, 'a grommeted cable port')
    param('port_x', '%.4f mm' % C.UA_PORT_X, 'lib/cobot - above the plates, under the cover')

    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c == design.rootComponent:
            continue
        if c.name == COMPONENT or c.name.startswith(COMPONENT + ' ('):
            c.name = STALE + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(STALE):
            occ.deleteMe()
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = COMPONENT
    assert comp.name == COMPONENT, 'a stale component still holds the name'
    ext = comp.features.extrudeFeatures
    rev = comp.features.revolveFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def bodies():
        return [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]

    def extrude(profs, op, start_cm, dist_cm, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(start_cm)))
        inp.setDistanceExtent(False, V(mm(dist_cm)))
        if op != NEW:
            inp.participantBodies = bodies()
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    def along_x(name, loops_mm, circles_mm, x0, x1, op, pick='largest'):
        """YZ sketch (u = y, v = z), extruded along +x from x0 to x1 (cm)."""
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        for pts in loops_mm:
            sp = [sk.modelToSketchSpace(P3(0, u / 10, v / 10)) for u, v in pts]
            for k in range(len(sp)):
                sk.sketchCurves.sketchLines.addByTwoPoints(sp[k], sp[(k + 1) % len(sp)])
        for u, v, d in circles_mm:
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(0, u / 10, v / 10)), d / 2 / 10)
        profs = adsk.core.ObjectCollection.create()
        if pick == 'all':
            for i in range(sk.profiles.count):
                profs.add(sk.profiles.item(i))
        else:
            best, bp = -1, None
            for i in range(sk.profiles.count):
                pr = sk.profiles.item(i)
                a_ = pr.areaProperties().area
                if (pick == 'largest' and a_ > best) or (pick == 'ring' and pr.profileLoops.count == 2 and a_ > best):
                    best, bp = a_, pr
            profs.add(bp)
        return extrude(profs, op, x0, x1 - x0, name)

    def revolve_xu(name, v_cm, pts_xu, axis_xu, op):
        """Revolve a closed polyline of (x, u) cm points, on the plane v = v_cm, about the line axis_xu."""
        if abs(v_cm) > 0:
            pi = comp.constructionPlanes.createInput()
            pi.setByOffset(comp.xYConstructionPlane, V(mm(v_cm)))
            plane = comp.constructionPlanes.add(pi)
            plane.name = 'pl_' + name
        else:
            plane = comp.xYConstructionPlane
        sk = comp.sketches.add(plane)
        sk.name = 'sk_' + name
        ls = sk.sketchCurves.sketchLines
        sp = [sk.modelToSketchSpace(P3(xx, uu, v_cm)) for xx, uu in pts_xu]
        first = ls.addByTwoPoints(sp[0], sp[1])
        prev = first
        for q in sp[2:]:
            prev = ls.addByTwoPoints(prev.endSketchPoint, q)
        ls.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        axis = ls.addByTwoPoints(sk.modelToSketchSpace(P3(axis_xu[0][0], axis_xu[0][1], v_cm)),
                                 sk.modelToSketchSpace(P3(axis_xu[1][0], axis_xu[1][1], v_cm)))
        axis.isConstruction = True
        best, bp = -1, None
        for i in range(sk.profiles.count):
            a_ = sk.profiles.item(i).areaProperties().area
            if a_ > best:
                best, bp = a_, sk.profiles.item(i)
        ri = rev.createInput(bp, axis, op)
        ri.setAngleExtent(False, V('360 deg'))
        ri.participantBodies = bodies()
        rev.add(ri).name = name

    x0, wt, xt = val('x0'), val('wall_t'), val('x_top')
    xw = x0 + wt
    A, L = val('a') * 10, val('l1') * 10
    outer = C.capsule(A, A, L)
    inner = C.capsule(A, A, L, inset=val('shell') * 10)
    pr = val('post_r') * 10

    # ---- phase 1: the joint wall and the 12-gon shell --------------------------------
    t0 = design.timeline.count
    along_x('joint_wall', [outer], [], x0, xw, NEW)
    along_x('shell', [outer, inner], [], xw, xt, JOIN, pick='ring')
    group(t0, PH_FORM)

    # ---- phase 2: the two joint bores ------------------------------------------------
    t1 = design.timeline.count
    along_x('bore_j2', [], [(0.0, 0.0, val('bore2') * 10)], x0, xw, CUT)
    along_x('bore_j3', [], [(L, 0.0, val('bore3') * 10)], x0, xw, CUT)
    group(t1, PH_JOINTS)

    # ---- phase 3: plate posts, the idler boss and its pin hole -------------------------
    t2 = design.timeline.count
    for k, (u, v) in enumerate(C.J2_POSTS):
        along_x('j2_post_%d' % k, [], [(u, v, 2 * pr)], xw, val('j2_post_top'), JOIN)
        along_x('j2_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], val('j2_post_top') - val('m3_deep'),
                val('j2_post_top'), CUT)
    for k, (u, v) in enumerate(C.J3_POSTS):
        along_x('j3_post_%d' % k, [], [(u, v, 2 * pr)], xw, val('j3_post_top'), JOIN)
        along_x('j3_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], val('j3_post_top') - val('m3_deep'),
                val('j3_post_top'), CUT)
    iu, iv = C.J3_IDLER
    along_x('idler_boss', [], [(iu, iv, 2 * pr)], xw, val('idler_boss_top'), JOIN)
    along_x('idler_pin_hole', [], [(iu, iv, val('pin_hole') * 10)], val('pin_bottom'), val('idler_boss_top'), CUT)
    group(t2, PH_POSTS)

    # ---- phase 4: cover corbels: a 45 deg cone under each boss, off the shell ----------
    t3 = design.timeline.count
    cx0 = val('corbel_x0')
    for k, (u, v) in enumerate(C.UA_COVER_SCREWS):
        uc, vc = u / 10, v / 10
        revolve_xu('corbel_cone_%d' % k, vc, [(cx0, uc), (cx0 + pr / 10, uc), (cx0 + pr / 10, uc + pr / 10)],
                   [(cx0, uc), (cx0 + pr / 10, uc)], JOIN)
        along_x('corbel_%d' % k, [], [(u, v, 2 * pr)], cx0 + pr / 10, xt, JOIN)
        along_x('corbel_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], xt - val('m3_deep'), xt, CUT)
    group(t3, PH_COVER)

    # ---- phase 5: the two cable ports, through the end caps along u -------------------
    t4 = design.timeline.count
    px, pr_ = val('port_x'), val('port_d') / 2
    for name, (u, v), sense in (('j2_port', C.UA_J2_PORT, -1), ('j3_port', C.UA_J3_PORT, +1)):
        uc = u / 10
        u_in = uc - sense * 3 * val('shell')
        u_out = uc + sense * val('shell')
        revolve_xu(name, v / 10, [(px, u_in), (px + pr_, u_in), (px + pr_, u_out), (px, u_out)],
                   [(px, u_in), (px, u_out)], CUT)
    group(t4, PH_LOOM)

    # ---- phase 6: keep-outs - every gear sweep and servo case, cut -------------------
    t5 = design.timeline.count
    j2, j3 = C.J2, C.J3
    tip = C.J2_PAIR.r_tip(C.J2_PAIR.z_pinion) + C.FREE
    along_x('keep_j2_gear', [], [(0.0, 0.0, 2 * j2.keep_out_r)], j2.x_spigot_end / 10, (j2.x_gear_back + C.FREE) / 10, CUT)
    along_x('keep_j2_pinion', [], [(C.J2_PIN[0], C.J2_PIN[1], 2 * tip)], j2.x_teeth0 / 10 - C.FREE / 10,
            (j2.x_gear_back + C.FREE) / 10, CUT)
    along_x('keep_j3_gear', [], [(L, 0.0, 2 * j3.keep_out_r)], j3.x_spigot_end / 10, (j3.x_gear_back + C.FREE) / 10, CUT)
    ra = C.J3A_PAIR.r_tip(C.J3A_PAIR.z_pinion) + C.FREE
    rb = C.J3B_PAIR.r_tip(C.J3B_PAIR.z_gear) + C.FREE
    rp = C.J3B_PAIR.r_tip(C.J3B_PAIR.z_pinion) + C.FREE
    along_x('keep_idler_a', [], [(iu, iv, 2 * ra)], val('idler_boss_top'), C.J3B_X0 / 10, CUT)
    along_x('keep_idler_b', [], [(iu, iv, 2 * rb)], j3.x_gear_back / 10, (C.J3B_X1 + C.FREE) / 10, CUT)
    along_x('keep_j3_pinion', [], [(C.J3_PIN[0], C.J3_PIN[1], 2 * rp)], j3.x_gear_back / 10,
            (C.J3B_X1 + C.FREE) / 10, CUT)
    lc = C.LOC

    def box(b):
        return [(b[0] - lc, b[2] - lc), (b[1] + lc, b[2] - lc), (b[1] + lc, b[3] + lc), (b[0] - lc, b[3] + lc)]
    along_x('keep_mg995', [box(C.J2_CASE)], [], C.UA_J2_CASE_TOP / 10, xt, CUT)
    along_x('keep_mg995_tabs', [box(C.J2_TABS)], [], C.UA_J2_TAB_TOP / 10,
            (C.UA_J2_TAB_TOP + C.MG995.tab_thk + C.FREE) / 10, CUT)
    along_x('keep_sg90', [box(C.J3_CASE)], [], C.UA_J3_CASE_TOP / 10, xt, CUT)
    along_x('keep_sg90_tabs', [box(C.J3_TABS)], [], C.UA_J3_TAB_TOP / 10,
            (C.UA_J3_TAB_TOP + C.SG90.tab_thk + C.FREE) / 10, CUT)
    group(t5, PH_KEEP)

    assert comp.bRepBodies.count == 1, 'the upper arm came out in %d pieces' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a_ = apps.item(j)
                if all(w.lower() in a_.name.lower() for w in want):
                    body.appearance = a_
                    used = a_.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break
    bb = body.boundingBox
    v_ = body.volume * 1000
    print("body: '%s' | appearance: %s | PRINT 1, joint wall down" % (body.name, used))
    print('capsule a %.0f over %.0f; wall x %.2f..%.2f, shell to x %.2f (cover to %.2f); bores O%.2f / O%.2f'
          % (C.UA_A, C.L1, x0 * 10, xw * 10, xt * 10, C.UA_X1, C.J2.bore, C.J3.bore))
    print('J2 posts %s to x %.2f; J3 posts %s to x %.2f; idler boss at %s to x %.2f, pin hole O%.1f from x %.2f'
          % (list(C.J2_POSTS), C.UA_J2_PLATE_X0, list(C.J3_POSTS), C.UA_J3_PLATE_X0,
             tuple(round(q, 2) for q in C.J3_IDLER), C.IDLER_BOSS_TOP, C.IDLER_PIN_D, C.IDLER_PIN_BOTTOM))
    print('%d cover corbels from x %.2f; ports O%.0f at x %.2f in both end caps'
          % (len(C.UA_COVER_SCREWS), C.UA_COVER_X0, C.PORT_D, C.UA_PORT_X))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
