"""robotarm/cobot_forearm - Fusion MCP generating script.

Rebuilds `robotarm_cobot_forearm` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py. Its +x plate, which carries the J3 spigot,
is cobot_forearm_plate.

THE FOREARM BODY: a 12-gon capsule (a 23 both ends, J3 -> J4 45), open on
its +x face; the servo link (S) at J4.
  * the -x face is the J4 JOINT WALL: the wrist's spigot passes through its
    bore and the J4 OUTPUT GEAR (36T, 2:1), bolted to that spigot from in
    here, traps it
  * the J4 SG90 360 on the J4 PLATE (a bench unit: servo + 18T pinion +
    the J4 encoder, lib/cobot) lying ACROSS the link, its pinion in mesh.
    The plate's 4 posts stand here; its holes are slotted along the mesh
    line so the mesh is SET on assembly
  * three J3 BOSSES under the J3 axis: the J3 gear's 3 x M3 x 30 run through
    gear, spigot and the forearm plate into them - one clamp stack
  * two CORBELS at the J4 end, above the J4 gear on 45 deg cones, take the
    forearm plate's other two screws
  * every gear sweep and the servo case are CUT at the end
  * the loom: in at the J3 end cap port, over the J4 plate in the lane at
    v -17.5, across to v 0 before the corbels, out of the J4 end cap port

ASSEMBLY:
  1. over the wrist's J4 spigot, plate off
  2. the J4 gear onto its register: 4 x M3 x 18
  3. the J4 plate unit, pinion into mesh, set with 0.1 paper: 4 x M3 x 8
  4. the loom, then the forearm plate: 2 x M3 x 12 (counterbored) into
     the corbels; its J3 end is clamped later by the J3 gear's bolts

Print: JOINT WALL DOWN, no support.
Frame: arm x; y = u along the link from J3 (0) to J4 (L2); z = v across.
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

COMPONENT = 'robotarm_cobot_forearm'
BODY_NAME = 'cobot_forearm'
PREFIX = 'cfa_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_forearm')
PH_FORM = 'wall + shell'
PH_JOINT = 'J4 bore'
PH_POSTS = 'plate posts + J3 bosses + corbels'
PH_LOOM = 'ports'
PH_KEEP = 'keep-outs'
PHASES = [PH_FORM, PH_JOINT, PH_POSTS, PH_LOOM, PH_KEEP]
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

    param('x0', '%.4f mm' % C.FA_X0, 'lib/cobot FA_X0 - the joint wall\'s -x face')
    param('wall_t', '%.4f mm' % C.JOINT_WALL, 'lib/cobot JOINT_WALL')
    param('x_top', '%.4f mm' % (C.FA_X1 - C.FA_PLATE_T), 'the shell\'s open edge = the plate seat')
    param('shell', '%.4f mm' % C.SHELL, 'lib/cobot SHELL')
    param('a', '%.4f mm' % C.FA_A, 'lib/cobot FA_A - both ends')
    param('l2', '%.4f mm' % C.L2, 'J3 -> J4')
    param('bore4', '%.4f mm' % C.J4.bore, 'lib/cobot J4 - the wrist spigot runs in it')
    param('post_r', '%.4f mm' % C.BOSS_R, 'lib/cobot BOSS_R')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('m3_deep', '8.0 mm', 'pilot depth')
    param('j3_deep', '%.4f mm' % C.FA_J3_PILOT_DEPTH, 'lib/cobot - the J3 gear\'s M3 x 30')
    param('j4_post_top', '%.4f mm' % C.FA_J4_PLATE_X0, 'lib/cobot - the J4 plate sits on these')
    param('corbel_x0', '%.4f mm' % C.FA_CORBEL_X0, 'lib/cobot - a corbel cone\'s apex, above the J4 gear')
    param('port_d', '%.4f mm' % C.PORT_D, 'a grommeted cable port')
    param('port_x', '%.4f mm' % C.FA_PORT_X, 'lib/cobot - over the J4 plate, under the forearm plate')

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
    A, L = val('a') * 10, val('l2') * 10
    outer = C.capsule(A, A, L)
    inner = C.capsule(A, A, L, inset=val('shell') * 10)
    pr = val('post_r') * 10

    t0 = design.timeline.count
    along_x('joint_wall', [outer], [], x0, xw, NEW)
    along_x('shell', [outer, inner], [], xw, xt, JOIN, pick='ring')
    group(t0, PH_FORM)

    t1 = design.timeline.count
    along_x('bore_j4', [], [(L, 0.0, val('bore4') * 10)], x0, xw, CUT)
    group(t1, PH_JOINT)

    t2 = design.timeline.count
    for k, (u, v) in enumerate(C.J4_POSTS):
        along_x('j4_post_%d' % k, [], [(u, v, 2 * pr)], xw, val('j4_post_top'), JOIN)
        along_x('j4_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], val('j4_post_top') - val('m3_deep'),
                val('j4_post_top'), CUT)
    for k, (u, v) in enumerate(C.J3.bolts()):
        along_x('j3_boss_%d' % k, [], [(u, v, 2 * pr)], xw, xt, JOIN)
        along_x('j3_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], xt - val('j3_deep'), xt, CUT)
    cx0 = val('corbel_x0')
    for k, (u, v) in enumerate(C.FA_CORBEL_SCREWS):
        uc, vc = u / 10, v / 10
        revolve_xu('corbel_cone_%d' % k, vc, [(cx0, uc), (cx0 + pr / 10, uc), (cx0 + pr / 10, uc + pr / 10)],
                   [(cx0, uc), (cx0 + pr / 10, uc)], JOIN)
        along_x('corbel_%d' % k, [], [(u, v, 2 * pr)], cx0 + pr / 10, xt, JOIN)
        along_x('corbel_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], xt - val('m3_deep'), xt, CUT)
    group(t2, PH_POSTS)

    t3 = design.timeline.count
    px, pr_ = val('port_x'), val('port_d') / 2
    for name, (u, v), sense in (('j3_port', C.FA_J3_PORT, -1), ('j4_port', C.FA_J4_PORT, +1)):
        uc = u / 10
        u_in = uc - sense * 3 * val('shell')
        u_out = uc + sense * val('shell')
        revolve_xu(name, v / 10, [(px, u_in), (px + pr_, u_in), (px + pr_, u_out), (px, u_out)],
                   [(px, u_in), (px, u_out)], CUT)
    group(t3, PH_LOOM)

    t4 = design.timeline.count
    j4 = C.J4
    tip = C.J4_PAIR.r_tip(C.J4_PAIR.z_pinion) + C.FREE
    along_x('keep_j4_gear', [], [(L, 0.0, 2 * j4.keep_out_r)], j4.x_spigot_end / 10, (j4.x_gear_back + C.FREE) / 10, CUT)
    along_x('keep_j4_pinion', [], [(C.J4_PIN[0], C.J4_PIN[1], 2 * tip)], (j4.x_teeth0 - C.FREE) / 10,
            (j4.x_gear_back + C.FREE) / 10, CUT)
    lc = C.LOC

    def box(b):
        return [(b[0] - lc, b[2] - lc), (b[1] + lc, b[2] - lc), (b[1] + lc, b[3] + lc), (b[0] - lc, b[3] + lc)]
    along_x('keep_sg90', [box(C.J4_CASE)], [], C.FA_J4_CASE_TOP / 10, xt, CUT)
    along_x('keep_sg90_tabs', [box(C.J4_TABS)], [], C.FA_J4_TAB_TOP / 10,
            (C.FA_J4_TAB_TOP + C.SG90.tab_thk + C.FREE) / 10, CUT)
    group(t4, PH_KEEP)

    assert comp.bRepBodies.count == 1, 'the forearm came out in %d pieces' % comp.bRepBodies.count
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
    print('capsule a %.0f over %.0f; wall x %.2f..%.2f, shell to x %.2f (plate to %.2f); J4 bore O%.2f'
          % (C.FA_A, C.L2, x0 * 10, xw * 10, xt * 10, C.FA_X1, C.J4.bore))
    print('J4 posts %s to x %.2f; J3 bosses at r %.1f pilots %.0f deep; corbels %s from x %.2f; ports at x %.2f'
          % (list(C.J4_POSTS), C.FA_J4_PLATE_X0, C.J3.bolt_r, C.FA_J3_PILOT_DEPTH,
             [tuple(round(q, 2) for q in c) for c in C.FA_CORBEL_SCREWS], C.FA_CORBEL_X0, C.FA_PORT_X))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
