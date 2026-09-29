"""robotarm/cobot_j2_gear - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j2_gear` (idempotent). Spec: specs/robotarm/cobot.md;
the pair is lib/cobot J2_PAIR, the joint lib/cobot J2.

THE J2 OUTPUT GEAR (36T m1.25 face 20), which is also the joint's
RETAINER and the carrier of its ENCODER MAGNET:
  * bolted with 4 x M3 x 30 to the end of the tower's solid J2 spigot,
    from inside the upper arm, heads SUNK in counterbores in the tooth face (the servo
    plate passes over this face)
  * its FLANGE traps the upper arm's joint wall: the axial bearing on this side
  * the J2 COUNTERBALANCE SHAFT on its axis (lib/cobot J2 spring): O10 up
    through the J2 plate's hole, the cover and the spring cap's floor, with a
    D-flat from the cap floor up carrying the two hub discs that wind the
    centring spring. The J2 magnet sits flush in the shaft's top end, under
    the AS5600 in the cap's lid. MOUNT THE GEAR WITH THE FLAT FACING FORWARD
    (the tower's +y) WITH THE ARM VERTICAL: that is the spring's neutral
  * CENTRED by a register: a LOC recess in the flange's bed face over the
    O12 boss on the spigot end. The bolts only clamp (clearance holes would
    let it float 0.2 - the mesh's whole backlash)
  * a 45 deg LEAD-IN on its tooth tips at the back face: the pinion enters
    the mesh from that side, axially, with its plate

Print: FLANGE DOWN, no support: the teeth are vertical prisms and the shaft
stands on the tooth face (~95 mm tall - a brim helps).
Frame: z along the joint axis, 0 on the spigot-end face, +z into the upper arm.
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

COMPONENT = 'robotarm_cobot_j2_gear'
BODY_NAME = 'cobot_j2_gear'
PREFIX = 'cg2_'
JOINT = C.J2
PAIR = C.J2_PAIR
PLATE_TOP = C.UA_J2_TAB_TOP
BOLT_L = C.J2_BOLT_L
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j2_gear')
PH_TEETH = 'flange + teeth'
PH_STALK = 'counterbalance shaft'
PH_BOLTS = 'register + lead-in + bolts'
PHASES = [PH_TEETH, PH_STALK, PH_BOLTS]
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

    param('face', '%.4f mm' % PAIR.face, 'lib/cobot ' + PAIR.name)
    param('flange_t', '%.4f mm' % C.FLANGE_T, 'lib/cobot FLANGE_T - the retainer')
    param('flange_d', '%.4f mm' % JOINT.flange_od, 'lib/cobot - laps the joint wall')
    param('bolt_r', '%.4f mm' % JOINT.bolt_r, 'lib/cobot')
    param('bolt_d', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('cbore_d', '%.4f mm' % C.CBORE_D, 'M3 cap head + FREE')
    param('cbore_h', '%.4f mm' % C.CBORE_H, 'the head sunk below the tooth face')
    param('stalk_d', '%.4f mm' % C.STALK_D, 'lib/cobot STALK_D - runs in the plate\'s hole')
    param('shoulder', '%.4f mm' % (C.SHOULDER_X - JOINT.x_spigot_end), 'lib/cobot SHOULDER_X - O10 -> O8 D')
    param('shaft_top', '%.4f mm' % (C.SHAFT_TOP - JOINT.x_spigot_end), 'lib/cobot SHAFT_TOP - under the lid')
    param('shaft_flat', '%.4f mm' % C.SHAFT_FLAT, 'lib/cobot SHAFT_FLAT - the D\'s flat depth')
    param('mag_d', '%.4f mm' % C.MAGNET_POCKET[0], 'the O6 J2 magnet, glued flush in the shaft end')
    param('mag_h', '%.4f mm' % C.MAGNET_POCKET[1], 'its depth')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')
    param('reg_d', '%.4f mm' % C.REG_RECESS[0], 'lib/cobot - LOC over the spigot\'s register boss: CENTRES the gear')
    param('reg_h', '%.4f mm' % C.REG_RECESS[1], 'its depth')

    assert val('flange_d') / 2 <= PAIR.r_tip(PAIR.z_gear) / 10

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

    def disc(name, x, y, d, z0, dz, op):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x, y), d / 2)
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

    ft, fc = val('flange_t'), val('face')
    top = ft + fc
    t0 = design.timeline.count
    disc('flange', 0.0, 0.0, val('flange_d'), 0.0, ft, NEW)
    disc('blank', 0.0, 0.0, PAIR.r_root(PAIR.z_gear) / 10 * 2, ft, fc, JOIN)
    T = PAIR.tooth_polar(PAIR.z_gear, n=TOOTH_SAMPLES, sink=val('tooth_sink') * 10)
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
    tooth = extrude(sk.profiles.item(0), JOIN, ft, fc, 'tooth')
    pat = adsk.core.ObjectCollection.create()
    pat.add(tooth)
    cp = comp.features.circularPatternFeatures.createInput(pat, comp.zConstructionAxis)
    cp.quantity = adsk.core.ValueInput.createByReal(PAIR.z_gear)
    cp.totalAngle = V('360 deg')
    cp.isSymmetric = False
    comp.features.circularPatternFeatures.add(cp).name = 'tooth_ring'
    group(t0, PH_TEETH)

    # J2 ONLY: the stalk is the COUNTERBALANCE SHAFT (lib/cobot J2 spring): O10
    # up through the J2 plate, the cover and the cap floor to the shoulder, then
    # a O8 D-flat that drives both hub discs. The magnet is in the top hub now.
    t1 = design.timeline.count
    st = val('shaft_top')
    disc('shaft', 0.0, 0.0, val('stalk_d'), top, st - top, JOIN)
    # the D: a flat on +x (gear frame) from the shoulder up; mount the gear so it faces FORWARD with the arm vertical
    r2 = val('stalk_d') / 2
    fl = r2 - val('shaft_flat')
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = 'sk_shaft_flat'
    sk.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk, fl, -r2 - val('shaft_flat')), mpt(sk, r2 + val('shaft_flat'),
                                                                                              r2 + val('shaft_flat')))
    extrude(sk.profiles.item(0), CUT, val('shoulder'), st - val('shoulder'), 'shaft_flat')
    disc('magnet', 0.0, 0.0, val('mag_d'), st - val('mag_h'), val('mag_h'), CUT)
    group(t1, PH_STALK)

    t2 = design.timeline.count
    disc('register', 0.0, 0.0, val('reg_d'), 0.0, val('reg_h'), CUT)
    lead_in('lead_in', PAIR.r_tip(PAIR.z_gear) / 10, top, -1)
    for k, az in enumerate(JOINT.bolt_az):
        bx, by = val('bolt_r') * math.cos(math.radians(az)), val('bolt_r') * math.sin(math.radians(az))
        disc('bolt_%d' % k, bx, by, val('bolt_d'), 0.0, top, CUT)
        disc('cbore_%d' % k, bx, by, val('cbore_d'), top - val('cbore_h'), val('cbore_h'), CUT)
    group(t2, PH_BOLTS)

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
    print("body: '%s' | appearance: %s | PRINT 1, flange down" % (body.name, used))
    print('%s: %dT m%.2f face %.0f on a O%.0f x %.0f flange; shaft O%.0f, D-flat from x %.2f, top (magnet) x %.2f; '
          '%d x M3 x %.0f at r %.1f sunk %.1f' % (JOINT.name, PAIR.z_gear, PAIR.module, PAIR.face, JOINT.flange_od,
                                                   C.FLANGE_T, C.STALK_D, C.SHOULDER_X, C.SHAFT_TOP,
                                                   len(JOINT.bolt_az), BOLT_L, JOINT.bolt_r, C.CBORE_H))
    print('tip r %.3f root r %.3f; centre distance %.2f' % (T['r_tip'], PAIR.r_root(PAIR.z_gear), PAIR.centre_distance))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v, v * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
