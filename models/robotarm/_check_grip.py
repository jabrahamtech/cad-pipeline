"""robotarm/_check_grip - GATE for the new gripper head (grip_*).

Driver, not a part. Builds grip_shell, grip_jaw, grip_finger and the
UNCHANGED gripper_pinion into one fresh document, then poses the whole
head at three strokes - s = S_TOUCH (fingers just touching), 10, 20 (full
open) - and runs Design.analyzeInterference at each, with:

  * DUMMIES for what is bought: the SG90 case, tabs and output boss placed
    from lib/grip's stack (its spline is left out - it BROACHES the pinion
    bore by design), the servo lead leaving the case end face at the
    lib/servo datum, and the rotator disc behind the back wall.
  * a POSITIVE CONTROL buried in the shell's solid, which MUST be reported.

Poses follow _check_fit's two hard rules: every pose occurrence gets its
transform AT CREATION (addExistingComponent), never by setting transform2
afterwards, and the occurrence each part script leaves is hidden, never
deleted.

Pinion phase is lib/grip.s_to_phase - the derivation from _check_fit.

Run STAGE = 1 (fresh document, build), then STAGE = 0 (pose + analyse).
"""

import io
import math
import os
import sys

import adsk.core
import adsk.fusion

STAGE = 1
REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ('grip_shell', 'grip_jaw', 'grip_finger', 'gripper_pinion')
DUMMY = 'robotarm_dummy_'
POSE = 'pose_'
LIMIT_MM3 = 0.001


def _exec(part):
    path = os.path.join(REPO, 'models', 'robotarm', part + '.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    ns = {'__name__': part, '__file__': path}
    exec(compile(io.open(path, encoding='utf-8').read(), path, 'exec'), ns)
    ns['run']('')


def _lib():
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    import lib.grip as G
    return G


def _dummy(root, name, sketch_fn, plane, z0, z1):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = DUMMY + name
    sk = comp.sketches.add(getattr(comp, plane))
    sk.name = 'sk_' + name
    sketch_fn(sk)
    inp = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByString('%.4f mm' % z0))
    inp.setDistanceExtent(False, adsk.core.ValueInput.createByString('%.4f mm' % (z1 - z0)))
    comp.features.extrudeFeatures.add(inp)
    return occ


def build(app, G):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'gate_grip'
    for p in PARTS:
        _exec(p)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    P3 = adsk.core.Point3D.create
    S = G.SERVO

    def rect_xy(x0, x1, y0, y1):
        return lambda sk: sk.sketchCurves.sketchLines.addTwoPointRectangle(
            P3(x0 / 10, y0 / 10, 0), P3(x1 / 10, y1 / 10, 0))

    def circ_xz(x, z, d):
        return lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(x / 10, 0, z / 10)), d / 20)

    def circ_yz(y, z, d):
        return lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(0, y / 10, z / 10)), d / 20)

    near, far = -S.shaft_from_end, S.case_l - S.shaft_from_end
    hw = S.case_w / 2
    _dummy(root, 'sg90_case', rect_xy(near, far, G.CASE_BOT_Y, G.CASE_TOP_Y),
           'xYConstructionPlane', -hw, hw)
    _dummy(root, 'sg90_tabs', rect_xy(near - G.TAB_OVER, far + G.TAB_OVER,
                                      G.TAB_Y, G.TAB_Y + S.tab_thk),
           'xYConstructionPlane', -hw, hw)
    _dummy(root, 'sg90_boss', circ_xz(0, 0, S.boss_dia), 'xZConstructionPlane',
           G.CASE_TOP_Y, G.CASE_TOP_Y + S.boss_h)
    # the lead, out of the near end face and away to the side (YZ normal is +X)
    _dummy(root, 'sg90_lead', circ_yz(G.LEAD_Y, 0, S.lead_bundle_dia), 'yZConstructionPlane',
           -G.X_HALF - 5, near)
    _dummy(root, 'rotator_disc', circ_xz(0, 0, 36.0), 'xZConstructionPlane',
           G.SHELL_BACK_Y - 6.0, G.SHELL_BACK_Y)
    _dummy(root, 'positive_control', rect_xy(-23.0, -21.0, -15.0, -13.0),
           'xYConstructionPlane', 2.0, 4.0)
    print('built %d occurrences into %s - now STAGE = 0'
          % (root.occurrences.count, doc.name))


def _name(ent):
    if hasattr(ent, 'component'):
        return ent.component.name.replace('robotarm_', '')
    occ = ent.assemblyContext
    return (occ.component.name if occ else ent.parentComponent.name).replace('robotarm_', '')


def analyse(app, G):
    design = adsk.fusion.Design.cast(app.activeProduct)
    assert app.activeDocument.name.startswith('gate_grip'), 'STAGE 0 runs in gate_grip'
    root = design.rootComponent
    ups = design.userParameters
    M3 = adsk.core.Matrix3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)

    # the pinion's gr_ block must be lib/grip's
    for nm, want in (('gr_offset', G.OFFSET), ('gr_face', G.GR_FACE), ('gr_r_pitch', G.R_PITCH),
                     ('gp_seat_z', G.HUB.seat_z)):
        p = ups.itemByName(nm)
        assert p is not None and abs(p.value * 10 - want) < 1e-6, (
            '%s is %s in the document and %.3f in lib/grip' % (nm, p and p.value * 10, want))

    for o in list(root.occurrences):
        if o.name.startswith(POSE) or o.component.name.startswith(POSE):
            o.deleteMe()
    comps = {}
    for o in root.occurrences:
        n = o.component.name
        if n.startswith('robotarm_grip_') or n == 'robotarm_gripper_pinion':
            comps[n.replace('robotarm_', '')] = o.component
            o.isLightBulbOn = False
    statics = [o for o in root.occurrences if o.component.name.startswith(DUMMY)]

    turned = M3()
    turned.setToRotation(math.pi, VEC(0, 1, 0), ORG)

    def moved(m, dx=0.0, dy=0.0):
        t = m.translation
        t.x, t.y = t.x + dx / 10, t.y + dy / 10
        m.translation = t
        return m

    def pinion_at(s):
        m = M3()
        m.setToRotation(G.s_to_phase(s), VEC(0, 0, 1), ORG)
        flip = M3()
        flip.setToRotation(-math.pi / 2, VEC(1, 0, 0), ORG)
        m.transformBy(flip)
        return moved(m, dy=G.PINION_BACK_Y)

    def rot():
        r = M3()
        r.setToRotation(math.pi, VEC(0, 1, 0), ORG)
        return r

    ok_all, report = True, []
    for s in (G.S_TOUCH, 10.0, G.GR_STROKE):
        add = root.occurrences.addExistingComponent
        pose = [add(comps['grip_shell'], M3()), add(comps['grip_shell'], turned),
                add(comps['gripper_pinion'], pinion_at(s)),
                add(comps['grip_jaw'], moved(M3(), dx=s)),
                add(comps['grip_jaw'], moved(rot(), dx=-s)),
                add(comps['grip_finger'], moved(M3(), dx=s - G.FINGER_LEAD, dy=G.FINGER_Y0)),
                add(comps['grip_finger'], moved(rot(), dx=-(s - G.FINGER_LEAD), dy=G.FINGER_Y0))]
        for o in pose:
            o.isLightBulbOn = True
        col = adsk.core.ObjectCollection.create()
        for o in pose + statics:
            col.add(o)
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        hits, control = [], 0.0
        for i in range(res.count):
            r = res.item(i)
            v = r.interferenceBody.volume * 1000
            if v < LIMIT_MM3:
                continue
            n1, n2 = _name(r.entityOne), _name(r.entityTwo)
            if 'dummy_positive_control' in (n1, n2):
                control += v
                continue
            if n1.startswith('dummy_') and n2.startswith('dummy_'):
                continue
            hits.append((v, n1, n2))
        good = control > 0 and not hits
        ok_all = ok_all and good
        report.append('s %5.1f mm (jaw gap %4.1f, finger gap %4.1f): control %.1f mm3, %d hit(s) %s'
                      % (s, 2 * s, 2 * (s - G.FINGER_LEAD), control, len(hits),
                         'ok' if good else 'FAIL'))
        for v, n1, n2 in sorted(hits, reverse=True):
            report.append('    INTERFERENCE %-22s ^ %-22s %9.3f mm3' % (n1, n2, v))
        if s < G.GR_STROKE:
            for o in pose:
                o.deleteMe()
    vols = dict((k, c.bRepBodies.item(0).volume * 1000) for k, c in comps.items())
    g = (2 * vols['grip_shell'] + 2 * vols['grip_jaw'] + vols['gripper_pinion']) \
        * G.PETG_PRINTED_G_PER_MM3 + 2 * vols['grip_finger'] * G.TPU_PRINTED_G_PER_MM3
    print('=== GATE grip: %d poses ===' % 3)
    for line in report:
        print(line)
    print('printed head: %.1f g (2 shells, 2 jaws, pinion PETG; 2 fingers TPU) + SG90 9 g + screws'
          % g)
    print('GATE grip_interference: %s' % ('PASS' if ok_all else 'FAIL'))


def run(_context: str):
    app = adsk.core.Application.get()
    G = _lib()
    if STAGE:
        build(app, G)
    else:
        analyse(app, G)
