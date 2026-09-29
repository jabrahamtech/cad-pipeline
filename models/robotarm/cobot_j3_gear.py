"""robotarm/cobot_j3_gear - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j3_gear` (idempotent). Spec: specs/robotarm/cobot.md;
the pair is lib/gears.py J3_PAIR, the joint is lib/cobot.py J3.

THE J3 GEAR, AND THE J3 RETAINER, IN ONE PART. 36T module 1 face 10 - the
same gear j3_gear cut, teeth from lib/gears, 2:1 against the 18T j3_pinion
on the J3 SG90. What is new is how it is held:
  * bolted with 3 x M3 x 18 to the END of the forearm's hollow J3 spigot,
    from inside the upper arm; the heads sit ON the tooth face (a counterbore
    would leave 0.55 mm to the loom bore) - nothing turns within r 12.5 there
  * its O32 FLANGE traps the upper arm's joint wall against the forearm -
    the axial bearing on this side of J3
  * the flange also stands the teeth off the wall by FLANGE_T: the pinion's
    retaining screw and washer sit on the pinion's far face, and they need
    that room
  * the O12 BORE is the loom's way across J3 - the only joint the loom
    crosses inside the arm, because it is the only one whose axis is free

Print: FLANGE DOWN, no support - the teeth are then vertical prisms, which is
how every gear in this project prints.

Frame: z along the J3 axis, 0 on the spigot-end face, +z into the upper arm.
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
from lib.gears import J3_PAIR  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_cobot_j3_gear'
BODY_NAME = 'cobot_j3_gear'
PREFIX = 'cjg_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j3_gear')
PH_TEETH = 'flange + teeth'
PH_BORE = 'bore + bolts'
PHASES = [PH_TEETH, PH_BORE]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
TOOTH_SAMPLES = 14


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()
    P = J3_PAIR

    def param(name, expr, comment='', units='mm'):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value      # cm

    def mm(v_cm):
        return '%.5f mm' % (v_cm * 10)

    param('face', '%.4f mm' % P.face, 'lib/gears J3_PAIR')
    param('r_tip', '%.5f mm' % P.r_tip(P.z_gear), 'lib/gears')
    param('r_root', '%.5f mm' % P.r_root(P.z_gear), 'lib/gears')
    param('flange_t', '%.4f mm' % C.FLANGE_T, 'lib/cobot FLANGE_T - the retainer, and the pinion screw\'s room')
    param('flange_d', '%.4f mm' % C.J3.flange_od, 'lib/cobot J3 - laps the upper arm wall')
    param('bore', '%.4f mm' % C.J3.spigot_id, 'lib/cobot J3 - the loom\'s way across')
    param('bolt_r', '%.4f mm' % C.J3.bolt_r, 'lib/cobot J3')
    param('bolt_d', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')

    assert val('flange_d') / 2 < val('r_root'), 'the flange would stand proud of the tooth roots'
    assert val('bolt_r') + val('bolt_d') / 2 + C.MIN_WALL / 10 <= val('r_root')
    assert val('bolt_r') - val('bolt_d') / 2 >= val('bore') / 2 + C.MIN_WALL / 10, 'bolt hole breaks into the loom bore'
    assert (C.J3.bolt_r + C.M3_HEAD_D / 2 + C.FREE) / 10 < val('r_root'), 'a head overhangs the teeth'

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

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    ft, fc = val('flange_t'), val('face')
    t0 = design.timeline.count
    disc('flange', 0.0, 0.0, val('flange_d'), 0.0, ft, NEW)
    disc('blank', 0.0, 0.0, val('r_root') * 2, ft, fc, JOIN)
    T = P.tooth_polar(P.z_gear, n=TOOTH_SAMPLES, sink=val('tooth_sink') * 10)
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
    cp.quantity = adsk.core.ValueInput.createByReal(P.z_gear)
    cp.totalAngle = V('360 deg')
    cp.isSymmetric = False
    comp.features.circularPatternFeatures.add(cp).name = 'tooth_ring'
    group(t0, PH_TEETH)

    t1 = design.timeline.count
    top = ft + fc
    disc('loom_bore', 0.0, 0.0, val('bore'), 0.0, top, CUT)
    for k, (bx, by) in enumerate(C.J3.bolts()):
        disc('bolt_%d' % k, bx / 10, by / 10, val('bolt_d'), 0.0, top, CUT)
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
    print("body: '%s' | appearance: %s | PRINT 1, flange down" % (body.name, used))
    print('%dT m %.1f face %.1f on a O%.0f x %.1f flange; O%.0f loom bore; %d x M3 x 18 at r %.1f, heads on the face'
          % (P.z_gear, P.module, P.face, C.J3.flange_od, C.FLANGE_T, C.J3.spigot_id, len(C.J3.bolt_az), C.J3.bolt_r))
    print('tip r %.3f root r %.3f; centre distance to the pinion %.2f' % (T['r_tip'], P.r_root(P.z_gear),
                                                                       P.centre_distance))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v, v * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
