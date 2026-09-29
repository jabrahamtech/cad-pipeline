"""robotarm/cobot_j3_plate - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j3_plate` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py.

THE J3 SERVO PLATE. The J3 SG90's near tab hole is 8.65 from its shaft -
inside the 18T pinion's r 10.4 sweep - so no post from the upper arm's wall
can reach it. Instead the SG90 is screwed to this plate ON THE BENCH
(2 x M2 x 6 through both tabs - NOT the ~8 mm bag screws: their tips would
reach the pinion, lib/cobot J3_TAB_SCREW_MAX), and the plate, riding above the
pinion, screws down onto two posts that stand outside both gear sweeps
(2 x M3 x 8). The plate therefore sets the gear centre distance: its window
is a locational fit on the case and its posts are pilot holes in the body.

Insert path: servo + pinion + plate go into the open upper arm along -x as
one piece; the pinion slides into mesh axially. Nothing has to move sideways.

Print: FLAT, no support.
Frame: the upper arm's (arm x; y = u along the link; z = v across).
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

COMPONENT = 'robotarm_cobot_j3_plate'
BODY_NAME = 'cobot_j3_plate'
PREFIX = 'cjp_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j3_plate')
PHASES = ['plate']
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
J3_POST_U = 14.0        # = cobot_upper_arm J3_POST_U - asserted against its parameter when present
J3_POST_V = 15.0
EDGE = 2.5              # CHOSEN - plate beyond a hole centre
EPS_MM = 1e-6


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()
    SG = C.SG90

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def mm(v_cm):
        return '%.5f mm' % (v_cm * 10)

    pin_u = C.L1 - C.J3_CENTRE
    near = SG.shaft_from_end + (SG.tab_hole_pitch - SG.case_l) / 2       # 8.65
    far = SG.case_l - SG.shaft_from_end + (SG.tab_hole_pitch - SG.case_l) / 2
    param('x0', '%.4f mm' % (C.UA_J3_TAB_TOP - C.PLATE_T), 'lib/cobot - on the upper arm posts')
    param('t', '%.4f mm' % C.PLATE_T, 'lib/cobot PLATE_T')
    param('u0', '%.4f mm' % (pin_u - J3_POST_U - EDGE - C.M3['clearance'] / 2), 'plate end toward J2')
    param('u1', '%.4f mm' % (pin_u + SG.case_w / 2 + EDGE), 'plate end toward J3')
    param('v0', '%.4f mm' % (-far - EDGE), 'plate edge, far tab side')
    param('v1', '%.4f mm' % (J3_POST_V + EDGE + C.M3['clearance'] / 2), 'plate edge, post side')
    param('win_u', '%.4f mm' % (SG.case_w / 2 + C.LOC), 'the case window, half across u - locational')
    param('win_v0', '%.4f mm' % (-(SG.case_l - SG.shaft_from_end) - C.LOC), 'window, far end')
    param('win_v1', '%.4f mm' % (SG.shaft_from_end + C.LOC), 'window, near end')
    param('pilot', '%.4f mm' % _FASTENER['M2']['pilot'], 'SG90 bag screw pilot')
    param('clear', '%.4f mm' % C.M3['clearance'], 'M3 clearance to the posts')

    ups_post = ups.itemByName('cua_j3_post_u')
    if ups_post is not None:
        assert abs(ups_post.value * 10 - (pin_u - J3_POST_U)) < EPS_MM, 'the plate and the upper arm disagree on the posts'
    assert val('v0') * 10 >= -(C.UA_A3 - C.SHELL - C.LOC), 'the plate hits the shell'
    assert val('v1') * 10 <= C.UA_A3 - C.SHELL - C.LOC, 'the plate hits the shell'

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
    ext = comp.features.extrudeFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sk_uv(name):
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def pt(sk, u, v):
        return sk.modelToSketchSpace(P3(0, u, v))

    def extrude(prof, op, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(val('x0'))))
        inp.setDistanceExtent(False, V(mm(val('t'))))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(0)]
        ext.add(inp).name = name

    t0 = design.timeline.count
    sk = sk_uv('plate')
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(sk, val('u0'), val('v0')), pt(sk, val('u1'), val('v1')))
    extrude(sk.profiles.item(0), NEW, 'plate')
    sk = sk_uv('case_window')
    pu = pin_u / 10
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(sk, pu - val('win_u'), val('win_v0')),
                                                     pt(sk, pu + val('win_u'), val('win_v1')))
    extrude(sk.profiles.item(0), CUT, 'case_window')
    for k, (u, v, d) in enumerate(((pin_u, near, val('pilot')), (pin_u, -far, val('pilot')),
                                   (pin_u - J3_POST_U, J3_POST_V, val('clear')),
                                   (pin_u - J3_POST_U, -J3_POST_V, val('clear')))):
        sk = sk_uv('hole_%d' % k)
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, u / 10, v / 10), d / 2)
        extrude(sk.profiles.item(0), CUT, 'hole_%d' % k)
    if design.timeline.count - t0 > 1:
        design.timeline.timelineGroups.add(t0, design.timeline.count - 1).name = PHASES[0]

    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    for want in APPEARANCE_HINTS:
        hit = None
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                if all(w.lower() in apps.item(j).name.lower() for w in want):
                    hit = apps.item(j)
                    break
            if hit:
                break
        if hit:
            body.appearance = hit
            break
    bb = body.boundingBox
    v = body.volume * 1000
    print("body: '%s' | PRINT 1, flat" % body.name)
    print('plate x %.2f..%.2f, u %.2f..%.2f, v %.2f..%.2f; window %.1f x %.1f; M2 pilots at v %.2f / %.2f; '
          'M3 clearance at u %.1f v +-%.1f' % (val('x0') * 10, (val('x0') + val('t')) * 10, val('u0') * 10,
                                              val('u1') * 10, val('v0') * 10, val('v1') * 10,
                                              val('win_u') * 10 * 2, (val('win_v1') - val('win_v0')) * 10, near, -far,
                                              pin_u - J3_POST_U, J3_POST_V))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v, v * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
