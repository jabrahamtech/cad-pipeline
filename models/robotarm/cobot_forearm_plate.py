"""robotarm/cobot_forearm_plate - Fusion MCP generating script.

Rebuilds `robotarm_cobot_forearm_plate` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py.

THE FOREARM'S +x PLATE - structural, not a cover: it carries the SOLID J3
SPIGOT (the forearm is H at J3). The spigot passes the upper arm's J3 wall
bore; the J3 gear CENTRES on the O12 register boss on its end (LOC) and
bolts to it from inside the upper arm, and those same 3 x M3 x 30 run on
through the spigot and this plate into the J3 bosses in the forearm body -
gear, spigot, plate and body clamped in one stack.
  * the spigot's shoulder (this plate's outer face) and the gear's flange
    trap the upper arm's wall, AX_GAP each side
  * the J3 axis carries the J3 encoder's magnet (on the gear's stalk), so
    the loom crosses J3 in a service loop between the two end-cap ports
  * the other 2 screws (M3 x 12, into the J4-end corbels) sit in
    COUNTERBORES: the links are offset, so the upper arm's wall sweeps
    AX_GAP over this whole face as the elbow folds
  * the inner face is FREE over the J4 SG90's case bottom: the servo's
    back-stop

Print: INNER FACE DOWN, spigot up, no support. The spigot OD is the fit and
it is at the top, away from the elephant foot.
Frame: arm x; y = u along the link from J3 (0) to J4 (L2); z = v across.
"""

import math
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

COMPONENT = 'robotarm_cobot_forearm_plate'
BODY_NAME = 'cobot_forearm_plate'
PREFIX = 'cfp_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_forearm_plate')
PH_FORM = 'plate + spigot'
PH_HOLES = 'bore + bolts'
PHASES = [PH_FORM, PH_HOLES]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
LEAD_IN = 0.5           # CHOSEN - chamfer on the spigot's end, into the upper arm bore
EPS_CM = 1e-5


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

    param('x_out', '%.4f mm' % C.FA_X1, 'lib/cobot FA_X1 - the outer face, AX_GAP under the upper arm')
    param('t', '%.4f mm' % C.FA_PLATE_T, 'lib/cobot FA_PLATE_T')
    param('a', '%.4f mm' % C.FA_A, 'apothem, both ends')
    param('l2', '%.4f mm' % C.L2, 'J3 -> J4')
    param('spigot_od', '%.4f mm' % C.J3.spigot_od, 'lib/cobot J3 - runs in the upper arm bore')
    param('spigot_end', '%.4f mm' % C.J3.x_spigot_end, 'lib/cobot J3 - the gear bolts on here')
    param('reg_d', '%.4f mm' % C.REG_D, 'lib/cobot REG_D - the J3 gear centres on this boss')
    param('reg_h', '%.4f mm' % C.REG_H, 'lib/cobot REG_H')
    param('clear', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('cbore_d', '%.4f mm' % C.CBORE_D, 'lib/cobot CBORE_D - M3 cap head + FREE')
    param('cbore_h', '%.4f mm' % C.CBORE_H, 'lib/cobot CBORE_H - head below the face')
    param('lead_in', '%.4f mm' % LEAD_IN, 'spigot end chamfer')

    x_in = val('x_out') - val('t')
    assert val('cbore_d') / 2 <= C.BOSS_R / 10, 'a counterbore wider than its boss'

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

    def along_x(name, loops_mm, circles_mm, x0, x1, op):
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
            if a_ > best:
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

    L = val('l2') * 10
    xo, xe = val('x_out'), val('spigot_end')
    t0 = design.timeline.count
    along_x('plate', [C.capsule(val('a') * 10, val('a') * 10, L)], [], x_in, xo, NEW)
    along_x('spigot', [], [(0.0, 0.0, val('spigot_od') * 10)], xo, xe, JOIN)
    along_x('register', [], [(0.0, 0.0, val('reg_d') * 10)], xe, xe + val('reg_h'), JOIN)
    group(t0, PH_FORM)

    t1 = design.timeline.count
    for k, (u, v) in enumerate(C.J3.bolts()):
        along_x('j3_bolt_%d' % k, [], [(u, v, val('clear') * 10)], x_in, xe, CUT)
    for k, (u, v) in enumerate(C.FA_CORBEL_SCREWS):
        along_x('screw_%d' % k, [], [(u, v, val('clear') * 10)], x_in, xo, CUT)
        along_x('cbore_%d' % k, [], [(u, v, val('cbore_d') * 10)], xo - val('cbore_h'), xo, CUT)
    group(t1, PH_HOLES)

    body = comp.bRepBodies.item(0)
    col = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.x - xe) < EPS_CM and abs(bb.maxPoint.x - xe) < EPS_CM:
            if math.hypot(bb.maxPoint.y, bb.maxPoint.z) > val('spigot_od') / 2 - EPS_CM:
                col.add(e)
    if col.count:
        ci = comp.features.chamferFeatures.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(PREFIX + 'lead_in'), False)
        comp.features.chamferFeatures.add(ci).name = 'spigot_lead_in'

    assert comp.bRepBodies.count == 1
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
    print("body: '%s' | appearance: %s | PRINT 1, inner face down, spigot up" % (body.name, used))
    print('plate x %.2f..%.2f; J3 spigot O%.1f to x %.2f (lead-in %.1f), register O%.0f x %.1f; %d J3 through-holes; '
          '%d counterbored M3 (cbore O%.1f x %.1f); chamfer edges %d'
          % (x_in * 10, xo * 10, C.J3.spigot_od, xe * 10, LEAD_IN, C.REG_D, C.REG_H, len(C.J3.bolt_az),
             len(C.FA_CORBEL_SCREWS), val('cbore_d') * 10, val('cbore_h') * 10, col.count))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
