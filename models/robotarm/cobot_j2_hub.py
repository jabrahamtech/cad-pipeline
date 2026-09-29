"""robotarm/cobot_j2_hub - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j2_hub` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py (the J2 Joint) and lib/servo_hub.py.

THE J2 HUB: the part that makes the joint a turntable (lib/cobot
docstring). One side is BROACHED ONTO THE MG995's SPLINE ON THE BENCH,
pulled down by the servo's own screw (head + washer end up in the recess in
the spigot end). The other side is a FLANGE, bolted to the tower's spigot
with 4 x M3 through clearance holes - the flange is what traps
the upper arm's joint wall, so it is the axial bearing on one side and the
spigot face is the other.

The bolt holes sit where the servo case is not (lib/cobot asserts it with
Joint.driver_clear), so with the servo already on the hub a 2.5 key reaches
every head past the case, straight down the open the upper arm.

Print: SPIGOT FACE DOWN (the flange's flat face on the bed), no support -
the broach bore is then VERTICAL, which is the only way it comes out round
enough to be a fit (servo_hub.py). Print it in the same material as the
spline gauge (README).

Frame: x along the joint axis, 0 on the spigot-side face, +x toward the servo.
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

COMPONENT = 'robotarm_cobot_j2_hub'
BODY_NAME = 'cobot_j2_hub'
PREFIX = 'cj2_'
JOINT = C.J2
HUB = C.HUB2
SERVO = C.MG995
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j2_hub')
PH_BODY = 'flange + body'
PH_BORE = 'broach + bolts'
PHASES = [PH_BODY, PH_BORE]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
TOL = 1e-6                     # cm, edge-selection epsilon - not a dimension


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

    body_d = HUB.boss_clear_d + 2 * C.MIN_WALL
    param('flange_d', '%.4f mm' % JOINT.flange_od, 'lib/cobot - laps the joint wall by the overlap')
    param('flange_t', '%.4f mm' % C.FLANGE_T, 'lib/cobot FLANGE_T')
    param('hub_h', '%.4f mm' % JOINT.hub_h, 'lib/cobot - spigot face to servo-side face')
    param('body_d', '%.4f mm' % body_d, 'boss clearance + MIN_WALL each side')
    param('boss_clear_d', '%.4f mm' % HUB.boss_clear_d, 'servo_hub - the output boss runs in here')
    param('boss_clear_to', '%.4f mm' % HUB.boss_clear_to, 'servo_hub - depth from the servo-side face')
    param('broach_d', '%.4f mm' % HUB.broach_d, 'servo_hub - THE STEEL SPLINE CUTS THIS (gauged)')
    param('broach_to', '%.4f mm' % HUB.broach_to, 'servo_hub - broach depth from the servo-side face')
    param('screw_d', '%.4f mm' % (HUB.screw_d + C.FREE), 'the servo screw, clearance')
    param('bolt_r', '%.4f mm' % JOINT.bolt_r, 'lib/cobot - beside the servo case')
    param('bolt_d', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('ef', '%.4f mm' % C.LOC, 'elephant foot on the bed face')

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------
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
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def disc(name, y, z, d, x0, dx, op):
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(0, y, z)), d / 2)
        inp = ext.createInput(sk.profiles.item(0), op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(x0)))
        inp.setDistanceExtent(False, V(mm(dx)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    h, ft = val('hub_h'), val('flange_t')
    assert val('broach_to') <= h, 'the broach runs out of the hub'
    assert val('body_d') / 2 + C.MIN_WALL / 10 <= val('bolt_r') - val('bolt_d') / 2, 'bolts break into the body'

    t0 = design.timeline.count
    disc('flange', 0.0, 0.0, val('flange_d'), 0.0, ft, NEW)
    if h > ft:
        disc('body', 0.0, 0.0, val('body_d'), ft, h - ft, JOIN)
    group(t0, PH_BODY)

    t1 = design.timeline.count
    disc('boss_clear', 0.0, 0.0, val('boss_clear_d'), h - val('boss_clear_to'), val('boss_clear_to'), CUT)
    disc('broach', 0.0, 0.0, val('broach_d'), h - val('broach_to'), val('broach_to') - val('boss_clear_to'), CUT)
    disc('screw', 0.0, 0.0, val('screw_d'), 0.0, h - val('broach_to'), CUT)
    for k, (bu, bv) in enumerate(JOINT.bolts()):
        disc('bolt_%d' % k, bu / 10, bv / 10, val('bolt_d'), 0.0, ft, CUT)
    group(t1, PH_BORE)

    body = comp.bRepBodies.item(0)
    col = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.x) < TOL and abs(bb.maxPoint.x) < TOL:
            r = math.hypot(bb.maxPoint.y, bb.maxPoint.z)
            if r > val('flange_d') / 2 - val('ef'):
                col.add(e)
    if col.count:
        ci = chf.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(PREFIX + 'ef'), False)
        chf.add(ci).name = 'bed_ef'

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
    print("body: '%s' | appearance: %s | PRINT 1, spigot face down" % (body.name, used))
    print('%s hub for the %s: flange O%.1f x %.1f, body O%.2f to %.2f; broach O%.2f %.2f..%.2f deep, '
          'boss clearance O%.2f x %.2f; %d x M3 at r %.1f az %s'
          % (JOINT.name, SERVO.name, JOINT.flange_od, C.FLANGE_T, val('body_d') * 10, JOINT.hub_h,
             HUB.broach_d, HUB.boss_clear_to, HUB.broach_to, HUB.boss_clear_d, HUB.boss_clear_to,
             len(JOINT.bolt_az), JOINT.bolt_r, list(JOINT.bolt_az)))
    print('driver clearance past the %s case: %.2f mm' % (SERVO.name, JOINT.driver_clear(SERVO, (1.0, 0.0))))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v, v * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
