"""robotarm/cobot_forearm - Fusion MCP generating script.

Rebuilds `robotarm_cobot_forearm` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py. Its +x plate, which carries the J3 spigot,
is cobot_forearm_plate.

THE FOREARM BODY: a 12-gon capsule (a 22 at both ends, J3 -> J4 45), open
on its +x face.
  * the -x face is the J4 JOINT WALL: the wrist's spigot passes through its
    bore and the J4 hub, bolted to that spigot from in here, traps it
  * the J4 SG90 lies along the link, shaft on J4, spline toward -x into its
    broached hub. Its FAR tab screws to a post (M2); the near tab sits over
    the hub flange. A rib on the +x plate stops the case tilting
  * the loom: in from J3 through the plate's hollow spigot, along the top
    of the shell, out of the J4 port at the front to the wrist

ASSEMBLY:
  1. over the wrist's J4 spigot, plate off
  2. the J4 SG90 with its hub already broached on: in along -x, hub onto
     the spigot, 4 x M3 x 12 past the case; far tab: M2 x 8
  3. the loom, then the +x plate: 4 x M3 x 12, heads counterbored (the
     upper arm's wall sweeps AX_GAP over that face). Two bosses stand on the
     floor; the two at the J4 end are CORBELS off the shell, above the J4
     flange sweep, on 45 deg cones (lib/cobot FA_CORBEL_*)
  4. (with the upper arm) the J3 gear's 3 x M3 x 30 run through gear, spigot
     and plate into the three J3 BOSSES here - the plate's J3 end has no
     screws of its own

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
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_cobot_forearm'
BODY_NAME = 'cobot_forearm'
PREFIX = 'cfa_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_forearm')
PH_FORM = 'wall + shell'
PH_JOINT = 'J4 bore'
PH_SERVO = 'servo post'
PH_BOSS = 'plate bosses'
PH_LOOM = 'loom'
PH_KEEP = 'keep-out'
PHASES = [PH_FORM, PH_JOINT, PH_SERVO, PH_BOSS, PH_LOOM, PH_KEEP]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
EPS_CM = 1e-9
POST_PAD = 3.0


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()
    SG = C.SG90
    M2 = _FASTENER['M2']

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

    far = SG.case_l - SG.shaft_from_end
    param('x0', '%.4f mm' % C.FA_X0, 'lib/cobot FA_X0 - the joint wall\'s -x face')
    param('wall_t', '%.4f mm' % C.JOINT_WALL, 'lib/cobot JOINT_WALL')
    param('x_top', '%.4f mm' % (C.FA_X1 - C.FA_PLATE_T), 'the shell\'s open edge = the plate seat')
    param('shell', '%.4f mm' % C.SHELL, 'lib/cobot SHELL')
    param('a', '%.4f mm' % C.FA_A, 'apothem, both ends')
    param('l2', '%.4f mm' % C.L2, 'J3 -> J4')
    param('bore4', '%.4f mm' % C.J4.bore, 'lib/cobot J4 - the wrist spigot runs in it')
    param('keep4', '%.4f mm' % C.J4.keep_out_r, 'the J4 hub flange sweep + FREE')
    param('keep4_top', '%.4f mm' % (C.J4.x_spigot_end + C.FLANGE_T + C.FREE), 'to the flange top + FREE')
    param('tab_top', '%.4f mm' % C.FA_J4_TAB_TOP, 'the SG90 tab face toward -x')
    param('case_end', '%.4f mm' % (far + C.LOC), 'the case\'s far end + LOC, back from J4')
    param('hole', '%.4f mm' % (far + (SG.tab_hole_pitch - SG.case_l) / 2), 'far tab hole, back from J4')
    param('tab_w', '%.4f mm' % (SG.case_w / 2), 'the tab is as wide as the case')
    param('m2_pilot', '%.4f mm' % M2['pilot'], 'SG90 bag screw')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('m_deep', '8.0 mm', 'pilot depth')
    param('j3_deep', '%.4f mm' % C.FA_J3_PILOT_DEPTH, 'lib/cobot - the J3 through-bolts (M3 x 30)')
    param('post_pad', '%.4f mm' % POST_PAD, 'material round a pilot')
    param('boss_r', '%.4f mm' % C.FA_BOSS_R, 'lib/cobot FA_BOSS_R - a plate-screw boss')
    param('corbel_x0', '%.4f mm' % C.FA_CORBEL_X0, 'lib/cobot - a corbel cone\'s apex, above the J4 flange')
    param('port_d', '%.4f mm' % C.PORT_D, 'the J4 loom port, grommeted')
    param('port_x', '%.4f mm' % (C.FA_X1 - C.FA_PLATE_T - C.PORT_D), 'port height, up by the plate')

    assert val('corbel_x0') >= val('keep4_top') - EPS_CM and val('corbel_x0') + val('boss_r') < val('x_top')

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
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def extrude(prof, op, start_cm, dist_cm, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(start_cm)))
        inp.setDistanceExtent(False, V(mm(dist_cm)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    def along_x(name, loops_mm, circles_mm, x0, x1, op, pick='largest'):
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        for pts in loops_mm:
            sp = [sk.modelToSketchSpace(P3(0, u / 10, v / 10)) for u, v in pts]
            for k in range(len(sp)):
                sk.sketchCurves.sketchLines.addByTwoPoints(sp[k], sp[(k + 1) % len(sp)])
        for u, v, d in circles_mm:
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(0, u / 10, v / 10)), d / 2 / 10)
        best, bp = -1, None
        for i in range(sk.profiles.count):
            pr = sk.profiles.item(i)
            a_ = pr.areaProperties().area
            if (pick == 'largest' and a_ > best) or (pick == 'ring' and pr.profileLoops.count == 2 and a_ > best):
                best, bp = a_, pr
        return extrude(bp, op, x0, x1 - x0, name)

    def rect(u0, u1, v0, v1):
        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

    x0, wt, xt = val('x0'), val('wall_t'), val('x_top')
    xw = x0 + wt
    L = val('l2') * 10
    outer = C.capsule(val('a') * 10, val('a') * 10, L)
    inner = C.capsule(val('a') * 10, val('a') * 10, L, inset=val('shell') * 10)

    t0 = design.timeline.count
    along_x('joint_wall', [outer], [], x0, xw, NEW)
    along_x('shell', [outer, inner], [], xw, xt, JOIN, pick='ring')
    group(t0, PH_FORM)

    t1 = design.timeline.count
    along_x('bore_j4', [], [(L, 0.0, val('bore4') * 10)], x0, xw, CUT)
    group(t1, PH_JOINT)

    t2 = design.timeline.count
    pad, hole, ce, tw = val('post_pad') * 10, val('hole') * 10, val('case_end') * 10, val('tab_w') * 10
    along_x('j4_post', [rect(L - hole - pad, L - ce, -tw, tw)], [], xw, val('tab_top'), JOIN)
    along_x('j4_pilot', [], [(L - hole, 0.0, val('m2_pilot') * 10)], val('tab_top') - val('m_deep'),
            val('tab_top'), CUT)
    group(t2, PH_SERVO)

    def corbel_cone(name, u, v, r_cm, x_apex):
        # a 45 deg cone, apex down, under a corbel boss: revolved about the boss axis
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.xYConstructionPlane, V(mm(v / 10)))
        pl = comp.constructionPlanes.add(pi)
        pl.name = 'pl_' + name
        sk = comp.sketches.add(pl)
        sk.name = 'sk_' + name
        ls = sk.sketchCurves.sketchLines
        a_ = sk.modelToSketchSpace(P3(x_apex, u / 10, v / 10))
        b_ = sk.modelToSketchSpace(P3(x_apex + r_cm, u / 10, v / 10))
        c_ = sk.modelToSketchSpace(P3(x_apex + r_cm, u / 10 + r_cm, v / 10))
        axis = ls.addByTwoPoints(a_, b_)
        side = ls.addByTwoPoints(axis.endSketchPoint, c_)
        ls.addByTwoPoints(side.endSketchPoint, axis.startSketchPoint)
        rv = comp.features.revolveFeatures
        ri = rv.createInput(sk.profiles.item(0), axis, JOIN)
        ri.setAngleExtent(False, V('360 deg'))
        ri.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        rv.add(ri).name = name

    t3 = design.timeline.count
    br = val('boss_r')
    for k, (u, v) in enumerate(C.FA_PLATE_SCREWS):
        base = xw
        if (u, v) in C.FA_CORBEL_SCREWS:
            corbel_cone('corbel_cone_%d' % k, u, v, br, val('corbel_x0'))
            base = val('corbel_x0') + br
        along_x('plate_boss_%d' % k, [], [(u, v, br * 10 * 2)], base, xt, JOIN)
        along_x('plate_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], xt - val('m_deep'), xt, CUT)
    for k, (u, v) in enumerate(C.J3.bolts()):
        along_x('j3_boss_%d' % k, [], [(u, v, br * 10 * 2)], xw, xt, JOIN)
        along_x('j3_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], xt - val('j3_deep'), xt, CUT)
    group(t3, PH_BOSS)

    # the J4 loom port: out of the front of the J4 end, along +u
    t4 = design.timeline.count
    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = 'sk_j4_port'
    sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(val('port_x'), 0, 0)),
                                                    val('port_d') / 2)
    extrude(sk.profiles.item(0), CUT, (L + C.FA_A - 2 * C.SHELL) / 10, 3 * C.SHELL / 10, 'j4_port')
    group(t4, PH_LOOM)

    t5 = design.timeline.count
    along_x('keep_j4_flange', [], [(L, 0.0, val('keep4') * 10 * 2)], xw, val('keep4_top'), CUT)
    group(t5, PH_KEEP)

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
    print('capsule a %.0f over %.0f; wall x %.2f..%.2f, shell to x %.2f (plate to %.2f)'
          % (C.FA_A, C.L2, x0 * 10, xw * 10, xt * 10, C.FA_X1))
    print('J4 bore O%.2f; SG90 far post u %.2f..%.2f to x %.2f, M2 pilot at u %.2f; keep-out r %.2f to x %.2f'
          % (C.J4.bore, L - hole - pad, L - ce, val('tab_top') * 10, L - hole, val('keep4') * 10,
             val('keep4_top') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
