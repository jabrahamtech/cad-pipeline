"""robotarm/_check_bits - GATE for duct_grommet in the upper arm.

Driver, not a part. Builds upper_arm and duct_grommet into ONE fresh
document, puts a grommet in each mouth of the cable duct (J3 end and J2
end), adds a dummy of the M3 elbow retention bolt that crosses the duct ON
the J3 axis, and runs Design.analyzeInterference with a POSITIVE CONTROL -
a block buried in the link's rail that MUST be reported.

The ONE designed overlap is the grommet's 0.15 press on the duct walls. It
is computed here from dg_* and must land within PRESS_BAND of the analytic
film - which also proves both grommets are really IN their duct. Anything
else - the bolt, a corner through the drum - fails the gate.

The roller_cap and pcb_keeper are gated in _check_base, where their hosts are.
"""

import io
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ('upper_arm', 'duct_grommet')
DUMMY = 'robotarm_dummy_'
CONTROL = 'dummy_positive_control'
LIMIT_MM3 = 0.001
PRESS_BAND = (0.85, 1.1)           # measured / analytic - the lead-in chamfer eats a little


def _exec(part):
    path = os.path.join(REPO, 'models', 'robotarm', part + '.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    ns = {'__name__': part, '__file__': path}
    exec(compile(io.open(path, encoding='utf-8').read(), path, 'exec'), ns)
    ns['run']('')


def _frame(o, xa, ya, za):
    m = adsk.core.Matrix3D.create()
    V3 = adsk.core.Vector3D.create
    m.setWithCoordinateSystem(adsk.core.Point3D.create(*[c / 10 for c in o]),
                              V3(*[float(c) for c in xa]), V3(*[float(c) for c in ya]),
                              V3(*[float(c) for c in za]))
    return m


def _body(root, name, m, sketch_fn, z0, z1):
    occ = root.occurrences.addNewComponent(m)
    comp = occ.component
    comp.name = DUMMY + name
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = 'sk_' + name
    sketch_fn(sk)
    inp = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByString('%.4f mm' % z0))
    inp.setDistanceExtent(False, adsk.core.ValueInput.createByString('%.4f mm' % (z1 - z0)))
    comp.features.extrudeFeatures.add(inp)
    return occ


def _name(ent):
    if hasattr(ent, 'component'):
        return ent.component.name.replace('robotarm_', '')
    occ = ent.assemblyContext
    return (occ.component.name if occ else ent.parentComponent.name).replace('robotarm_', '')


def run(_context: str):
    app = adsk.core.Application.get()
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'gate_bits'
    for p in PARTS:
        _exec(p)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters

    def v(n):
        return ups.itemByName(n).value * 10
    l1, mouth, half_x = v('ua_l1'), v('dg_mouth'), v('ua_half_x')
    P3 = adsk.core.Point3D.create

    # both mouths: J3 end (y = 0) and J2 end (y = -l1). Local +z INTO the duct.
    frames = [_frame((0, mouth, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0)),
              _frame((0, -l1 - mouth, 0), (-1, 0, 0), (0, 0, 1), (0, 1, 0))]
    g = [o for o in root.occurrences if o.component.name == 'robotarm_duct_grommet'][0]
    occs = [g, root.occurrences.addExistingComponent(g.component, adsk.core.Matrix3D.create())]
    for o, m in zip(occs, frames):
        o.transform2 = m
    # SNAPSHOT AT ONCE: a moved occurrence with no joint reverts on the next
    # compute, and adding the dummies below is one - both grommets came back
    # at the origin, inside each other, on the first run.
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    # the M3 elbow bolt: O3.0 down the J3 axis, the full straddle width
    screw_d = v('ua_bolt_clear') - 0.4       # O3.4 clearance -> O3.0 screw
    _body(root, 'elbow_bolt', _frame((-half_x, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)),
          lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0), screw_d / 20),
          0.0, 2 * half_x)
    # POSITIVE CONTROL - in the top rail, mid-link, above the duct
    zc = v('ua_duct_z') + 0.5
    _body(root, 'positive_control', adsk.core.Matrix3D.create(),
          lambda sk: sk.sketchCurves.sketchLines.addTwoPointRectangle(
              P3(-0.3, -l1 / 20 - 0.25, 0), P3(0.3, -l1 / 20 + 0.25, 0)),
          zc, zc + 1.5)
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    col = adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        col.add(o)
    inp = design.createInterferenceInput(col)
    inp.areCoincidentFacesIncluded = False
    res = design.analyzeInterference(inp)
    hits, control, press = [], 0.0, 0.0
    for i in range(res.count):
        r = res.item(i)
        vol = r.interferenceBody.volume * 1000
        if vol < LIMIT_MM3:
            continue
        pair = sorted((_name(r.entityOne), _name(r.entityTwo)))
        if CONTROL in pair:
            control += vol
        elif pair == ['duct_grommet', 'upper_arm']:
            press += vol
        else:
            hits.append((vol, pair))
    w_o = 2 * v('dg_duct_x') + v('dg_press')
    h_o = 2 * v('dg_duct_z') + v('dg_press')
    analytic = len(occs) * v('dg_press') / 2 * v('dg_depth') * 2 * (w_o + h_o - v('dg_press'))
    ratio = press / analytic
    press_ok = PRESS_BAND[0] <= ratio <= PRESS_BAND[1]
    print('=== GATE bits: %d occurrences ===' % col.count)
    print('positive control: %.2f mm3 found (must be > 0)' % control)
    print('  grommet press film %.2f mm3, analytic %.2f (x%d) ratio %.3f  %s'
          % (press, analytic, len(occs), ratio, 'ok' if press_ok else 'OUT OF BAND'))
    for vol, pair in sorted(hits, reverse=True):
        print('  INTERFERENCE %-26s ^ %-26s %9.3f mm3' % (pair[0], pair[1], vol))
    ok = control > 0 and press_ok and not hits
    print('GATE bits_interference: %s' % ('PASS' if ok else 'FAIL'))
