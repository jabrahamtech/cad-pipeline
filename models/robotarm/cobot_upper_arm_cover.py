"""robotarm/cobot_upper_arm_cover - Fusion MCP generating script.

Rebuilds `robotarm_cobot_upper_arm_cover` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py (the screw pattern is UA_COVER_SCREWS).

THE UPPER ARM'S LID: the capsule outline (a 28, both ends), COVER_T thick,
on the shell's open +x edge.
  * it is the MG995's PULL-OFF STOP: the servo is held by its spline and one
    far tab, and this face sits FREE (0.4) over its case bottom - less than
    the spline's engagement, so the servo cannot walk off its hub
  * a LOCATING LIP runs inside the shell (LOC fit), notched round the six
    cover corbels, so the lid lands square before a screw goes in
  * 6 x M3 x 8 button heads into the upper arm's cover corbels. This is the
    arm's outside face (nothing sweeps over it), so heads may stand proud

Print: OUTER FACE DOWN, lip up, no support.
Frame: arm x; y = u along the link from J2 (0) to J3 (L1); z = v across.
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

COMPONENT = 'robotarm_cobot_upper_arm_cover'
BODY_NAME = 'cobot_upper_arm_cover'
PREFIX = 'cuc_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_upper_arm_cover')
PH_FORM = 'lid + lip'
PH_HOLES = 'screws'
PHASES = [PH_FORM, PH_HOLES]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
LIP_T = 1.2             # CHOSEN - lip wall
LIP_H = 1.5             # CHOSEN - lip depth into the shell
EPS_MM = 1e-6


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

    param('x_out', '%.4f mm' % C.UA_X1, 'lib/cobot UA_X1 - the arm\'s +x face')
    param('t', '%.4f mm' % C.COVER_T, 'lib/cobot COVER_T')
    param('a', '%.4f mm' % C.UA_A, 'lib/cobot UA_A - both ends')
    param('l1', '%.4f mm' % C.L1, 'J2 -> J3')
    param('shell', '%.4f mm' % C.SHELL, 'lib/cobot SHELL')
    param('loc', '%.4f mm' % C.LOC, 'lip to shell, locational')
    param('lip_t', '%.4f mm' % LIP_T, 'lip wall')
    param('lip_h', '%.4f mm' % LIP_H, 'lip depth into the shell')
    param('notch_r', '%.4f mm' % (C.BOSS_R + C.FREE), 'lip notch round a cover corbel')
    param('clear', '%.4f mm' % C.M3['clearance'], 'M3 clearance')

    post = ups.itemByName('cua_post_r')
    if post is not None:
        assert abs(post.value * 10 - C.BOSS_R) < EPS_MM, 'the cover and the upper arm disagree on the corbels'
    # the servos clear the lip's underside
    assert C.UA_J2_CASE_TOP + C.MG995.case_h + C.FREE <= C.UA_X1 - C.COVER_T + EPS_MM
    assert C.UA_J3_CASE_TOP + C.SG90.case_h + C.FREE <= C.UA_X1 - C.COVER_T - LIP_H

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
        inp = ext.createInput(bp, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(x0)))
        inp.setDistanceExtent(False, V(mm(x1 - x0)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    a2 = a3 = val('a') * 10
    L = val('l1') * 10
    xo = val('x_out')
    xi = xo - val('t')
    lip_out = (val('shell') + val('loc')) * 10
    lip_in = lip_out + val('lip_t') * 10
    t0 = design.timeline.count
    along_x('lid', [C.capsule(a2, a3, L)], [], xi, xo, NEW)
    along_x('lip', [C.capsule(a2, a3, L, inset=lip_out), C.capsule(a2, a3, L, inset=lip_in)], [],
            xi - val('lip_h'), xi, JOIN, pick='ring')
    for k, (u, v) in enumerate(C.UA_COVER_SCREWS):
        along_x('lip_notch_%d' % k, [], [(u, v, val('notch_r') * 10 * 2)], xi - val('lip_h'), xi, CUT)
    group(t0, PH_FORM)

    t1 = design.timeline.count
    for k, (u, v) in enumerate(C.UA_COVER_SCREWS):
        along_x('screw_%d' % k, [], [(u, v, val('clear') * 10)], xi, xo, CUT)
    group(t1, PH_HOLES)

    assert comp.bRepBodies.count == 1, 'the lid came out in %d pieces' % comp.bRepBodies.count
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
    print("body: '%s' | appearance: %s | PRINT 1, outer face down" % (body.name, used))
    print('lid x %.2f..%.2f, lip %.1f deep x %.1f wall (LOC to the shell), notched at %d bosses; MG995 base %.2f under'
          % (xi * 10, xo * 10, LIP_H, LIP_T, len(C.UA_COVER_SCREWS),
             xi * 10 - (C.UA_J2_CASE_TOP + C.MG995.case_h)))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
