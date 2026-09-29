"""robotarm/cobot_j3_pinion - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j3_pinion` (idempotent). Spec: specs/robotarm/cobot.md;
the pair is lib/cobot J3B_PAIR, the spline bore lib/cobot PIN3_HUB (lib/servo_hub).

THE J3 SERVO PINION (18T m1 face 12) on the SG90 360.
BROACHED ONTO THE SPLINE ON THE BENCH: pressed on, pulled home by the
servo's own screw from the FRONT face (M2.5 x 6). A long pinion is
counterbored so only PIN_FLOOR of it lies over the spline; on a short one
the head stands in the output gear's flange layer, which has room for it
(lib/cobot check). The pinion goes in with its servo plate as one unit and
meshes AXIALLY - nothing slides sideways - led in by a 45 deg chamfer on its
front tooth tips.

Print: FRONT FACE DOWN, no support: the broach opens at the top of the
build, clear of the elephant foot, and is vertical - the only way it comes
out round enough to broach (servo_hub.py). Same material as the spline gauge.
Frame: z along the servo shaft, 0 on the front face, +z toward the servo.
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

COMPONENT = 'robotarm_cobot_j3_pinion'
BODY_NAME = 'cobot_j3_pinion'
PREFIX = 'cp3_'
PAIR = C.J3B_PAIR
HUB = C.PIN3_HUB
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j3_pinion')
PH_TEETH = 'teeth'
PH_BORE = 'broach + screw + lead-in'
PHASES = [PH_TEETH, PH_BORE]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
TOOTH_SAMPLES = 14
LEAD_OVER = 0.01          # cm - the lead-in cutter runs this far past the tip


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

    cb_h, cb_d = C.pinion_cbore(HUB, PAIR.face)
    param('face', '%.4f mm' % PAIR.face, 'lib/cobot ' + PAIR.name)
    param('boss_clear_d', '%.4f mm' % HUB.boss_clear_d, 'servo_hub - the output boss runs in here')
    param('boss_clear_to', '%.4f mm' % HUB.boss_clear_to, 'servo_hub - from the servo-side face')
    param('broach_d', '%.4f mm' % HUB.broach_d, 'servo_hub - THE STEEL SPLINE CUTS THIS (gauged)')
    param('broach_to', '%.4f mm' % HUB.broach_to, 'servo_hub - from the servo-side face')
    param('screw_d', '%.4f mm' % (HUB.screw_d + C.FREE), 'the servo screw, clearance')
    param('cbore_d', '%.4f mm' % cb_d, 'the screw head + washer')
    param('cbore_h', '%.4f mm' % max(cb_h, 0.0), 'lib/cobot pinion_cbore - leaves PIN_FLOOR over the spline')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')

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

    fc = val('face')
    t0 = design.timeline.count
    disc('blank', PAIR.r_root(PAIR.z_pinion) / 10 * 2, 0.0, fc, NEW)
    T = PAIR.tooth_polar(PAIR.z_pinion, n=TOOTH_SAMPLES, sink=val('tooth_sink') * 10)
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = 'sk_tooth_profile'
    lines = sk.sketchCurves.sketchLines
    r_sink = T['r_sink'] / 10.0
    for key, sign in (('flank_pos', 1), ('flank_neg', -1)):
        pts = adsk.core.ObjectCollection.create()
        for (r_mm, a) in T[key]:
            pts.add(polar(sk, r_mm / 10.0, a))
        sk.sketchCurves.sketchFittedSplines.add(pts)
        lines.addByTwoPoints(polar(sk, r_sink, sign * T['ang_base']), polar(sk, T['r_base'] / 10.0, sign * T['ang_base']))
    lines.addByTwoPoints(polar(sk, r_sink, T['ang_base']), polar(sk, r_sink, -T['ang_base']))
    sk.sketchCurves.sketchArcs.addByCenterStartSweep(mpt(sk, 0, 0), polar(sk, T['r_tip'] / 10.0, T['ang_tip']),
                                                     -2 * T['ang_tip'])
    tooth = extrude(sk.profiles.item(0), JOIN, 0.0, fc, 'tooth')
    pat = adsk.core.ObjectCollection.create()
    pat.add(tooth)
    cp = comp.features.circularPatternFeatures.createInput(pat, comp.zConstructionAxis)
    cp.quantity = adsk.core.ValueInput.createByReal(PAIR.z_pinion)
    cp.totalAngle = V('360 deg')
    cp.isSymmetric = False
    comp.features.circularPatternFeatures.add(cp).name = 'tooth_ring'
    group(t0, PH_TEETH)

    t1 = design.timeline.count
    disc('boss_clear', val('boss_clear_d'), fc - val('boss_clear_to'), val('boss_clear_to'), CUT)
    disc('broach', val('broach_d'), fc - val('broach_to'), val('broach_to') - val('boss_clear_to'), CUT)
    disc('screw', val('screw_d'), 0.0, fc - val('broach_to'), CUT)
    if val('cbore_h') > 0:
        disc('screw_cbore', val('cbore_d'), 0.0, val('cbore_h'), CUT)
    lead_in('lead_in', PAIR.r_tip(PAIR.z_pinion) / 10, 0.0, +1)
    group(t1, PH_BORE)

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
    print("body: '%s' | appearance: %s | PRINT 1, front face down" % (body.name, used))
    print('%dT m%.2f face %.0f; broach O%.2f %.1f..%.1f from the servo face; counterbore O%.2f x %.1f; '
          'screw %s x %.1f min' % (PAIR.z_pinion, PAIR.module, PAIR.face, HUB.broach_d, HUB.boss_clear_to,
                                   HUB.broach_to, cb_d, cb_h, 'M%.1f' % HUB.screw_d,
                                   C.pinion_screw_l(HUB, PAIR.face)))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v, v * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
