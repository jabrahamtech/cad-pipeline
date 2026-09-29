"""robotarm/cobot_j3_idler - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j3_idler` (idempotent). Spec: specs/robotarm/cobot.md;
the pairs are lib/cobot J3A_PAIR and J3B_PAIR.

THE J3 COMPOUND IDLER: an 18T (stage A, driving the 36T output gear) and a
36T (stage B, driven by the SG90's 18T) on one hub - 2:1 x 2:1 = 4:1 at J3
inside the upper arm's O52. It turns on a O3 x 35 steel dowel that stands in
a blind hole in a wall boss and is captured at its top by the J3 plate, so
the idler goes on the pin BEFORE the plate unit drops in, and the plate's
pinion meshes it axially.

  * bore O3 + ROT: printed holes come out small - run a 3.0 drill through
    by hand before fitting (a sliding fit on the pin)
  * the stage-A 18T is face 12 because it carries 2x the servo's torque
  * 45 deg LEAD-INS where it slides into mesh: the 18T's wall-side tips
    (into the output gear) and the 36T's plate-side tips (the pinion enters)

Print: THE 36T FACE DOWN, no support; the 18T stands on it.
Frame: z along the pin, 0 on the stage-A (wall-side) face, +z toward the plate.
"""

import os
import sys
import math

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

import lib.cobot as C  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_cobot_j3_idler'
BODY_NAME = 'cobot_j3_idler'
PREFIX = 'cji_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j3_idler')
PH_A = 'stage A 18T'
PH_B = 'stage B 36T'
PH_BORE = 'bore + lead-ins'
PHASES = [PH_A, PH_B, PH_BORE]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
TOOTH_SAMPLES = 14
LEAD_OVER = 0.01          # cm - the lead-in cutter runs this far past the tip
EPS_MM = 1e-6


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()
    A, B = C.J3A_PAIR, C.J3B_PAIR

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

    param('face_a', '%.4f mm' % A.face, 'lib/cobot J3A_PAIR - the 18T')
    param('gap', '%.4f mm' % (C.J3B_X0 - C.J3.x_gear_back), 'stage A -> stage B, FREE')
    param('face_b', '%.4f mm' % B.face, 'lib/cobot J3B_PAIR - the 36T')
    param('bore', '%.4f mm' % (C.IDLER_PIN_D + C.ROT), 'the O3 pin + ROT; drill 3.0 by hand')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')
    assert abs((val('face_a') + val('gap') + val('face_b')) * 10 - (C.IDLER_X1 - C.IDLER_X0)) < EPS_MM

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

    def mpt(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def polar(sk, r, a):
        return mpt(sk, r * math.cos(a), r * math.sin(a))

    def extrude(prof, op, z0, dz, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0)))
        inp.setDistanceExtent(False, V(mm(dz)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def disc(name, d, z0, dz, op):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0), d / 2)
        return extrude(sk.profiles.item(0), op, z0, dz, name)

    def lead_in(name, r_tip, z_face, sense):
        """45 deg lead-in on the tooth tips at z_face; sense -1: teeth below the face, +1: above."""
        sk = comp.sketches.add(comp.xZConstructionPlane)
        sk.name = 'sk_' + name
        L = C.LEAD_IN / 10
        over = LEAD_OVER
        a_ = sk.modelToSketchSpace(P3(r_tip - L, 0, z_face))
        b_ = sk.modelToSketchSpace(P3(r_tip + over, 0, z_face))
        c_ = sk.modelToSketchSpace(P3(r_tip + over, 0, z_face + sense * (L + over)))
        ls = sk.sketchCurves.sketchLines
        l1 = ls.addByTwoPoints(a_, b_)
        l2 = ls.addByTwoPoints(l1.endSketchPoint, c_)
        ls.addByTwoPoints(l2.endSketchPoint, l1.startSketchPoint)
        rv = comp.features.revolveFeatures
        ri = rv.createInput(sk.profiles.item(0), comp.zConstructionAxis, CUT)
        ri.setAngleExtent(False, V('360 deg'))
        ri.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        rv.add(ri).name = name

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    def teeth(pair, z, z0, dz, tag):
        T = pair.tooth_polar(z, n=TOOTH_SAMPLES, sink=val('tooth_sink') * 10)
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_tooth_' + tag
        lines = sk.sketchCurves.sketchLines
        r_sink = T['r_sink'] / 10.0
        for key, sign in (('flank_pos', 1), ('flank_neg', -1)):
            pts = adsk.core.ObjectCollection.create()
            for (r_mm, a) in T[key]:
                pts.add(polar(sk, r_mm / 10.0, a))
            sk.sketchCurves.sketchFittedSplines.add(pts)
            lines.addByTwoPoints(polar(sk, r_sink, sign * T['ang_base']),
                                 polar(sk, T['r_base'] / 10.0, sign * T['ang_base']))
        lines.addByTwoPoints(polar(sk, r_sink, T['ang_base']), polar(sk, r_sink, -T['ang_base']))
        sk.sketchCurves.sketchArcs.addByCenterStartSweep(mpt(sk, 0, 0), polar(sk, T['r_tip'] / 10.0, T['ang_tip']),
                                                         -2 * T['ang_tip'])
        tooth = extrude(sk.profiles.item(0), JOIN, z0, dz, 'tooth_' + tag)
        pat = adsk.core.ObjectCollection.create()
        pat.add(tooth)
        cp = comp.features.circularPatternFeatures.createInput(pat, comp.zConstructionAxis)
        cp.quantity = adsk.core.ValueInput.createByReal(z)
        cp.totalAngle = V('360 deg')
        cp.isSymmetric = False
        comp.features.circularPatternFeatures.add(cp).name = 'ring_' + tag

    fa, gp, fb = val('face_a'), val('gap'), val('face_b')
    t0 = design.timeline.count
    disc('hub_a', A.r_root(A.z_pinion) / 10 * 2, 0.0, fa + gp, NEW)
    teeth(A, A.z_pinion, 0.0, fa, 'a')
    group(t0, PH_A)
    t1 = design.timeline.count
    disc('hub_b', B.r_root(B.z_gear) / 10 * 2, fa + gp, fb, JOIN)
    teeth(B, B.z_gear, fa + gp, fb, 'b')
    group(t1, PH_B)
    t2 = design.timeline.count
    disc('bore', val('bore'), 0.0, fa + gp + fb, CUT)
    lead_in('lead_in_a', A.r_tip(A.z_pinion) / 10, 0.0, +1)
    lead_in('lead_in_b', B.r_tip(B.z_gear) / 10, fa + gp + fb, -1)
    group(t2, PH_BORE)

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
    v = body.volume * 1000
    print("body: '%s' | appearance: %s | PRINT 1, 36T face down" % (body.name, used))
    print('%dT face %.0f + %dT face %.0f, gap %.1f; bore O%.2f on a O%.0f x %.0f pin; ratio %.0f:1 overall'
          % (A.z_pinion, A.face, B.z_gear, B.face, gp * 10, val('bore') * 10, C.IDLER_PIN_D, C.IDLER_PIN_L,
             C.J3_RATIO))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v, v * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
