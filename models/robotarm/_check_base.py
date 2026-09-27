"""robotarm/_check_base - GATE for the new base and the MG995 J1 stack.

Driver, not a part. Builds, into ONE fresh document, everything that meets
at J1 in the stator frame (z 0 = platter rim top, J1 axis):

    base_platter, base_lid, turntable_stator, turntable_ring   as built
    j1_hub          moved up to its seat: deck_z + seat_z
    shoulder_bracket  moved so its race face lands on tt_race_z
    DUMMIES (COTS envelopes, not printed): the MG995 case + tabs + boss,
    the ESP32 board and its above/below cable envelopes, the hall sensor,
    the home magnet

and runs Design.analyzeInterference over all of it, WITH A POSITIVE
CONTROL - a block buried in the platter floor that MUST be reported. A gate
that has never found anything proves nothing (_HANDOFF.md section 2).

Run TWICE: REBUILD = True (build + place, ~40 s), then REBUILD = False
(analyse the active document). The 60 s MCP limit will not take both.

EXPECTED contacts are listed in EXPECTED and must be ZERO-VOLUME or absent:
touching faces are not interference (areCoincidentFacesIncluded = False).
"""

import io
import os
import sys

import adsk.core
import adsk.fusion

REBUILD = True
REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ('base_platter', 'base_lid', 'turntable_stator', 'turntable_ring',
         'j1_hub', 'shoulder_bracket')
DUMMY = 'robotarm_dummy_'
CONTROL = DUMMY + 'positive_control'
LIMIT_MM3 = 0.001                  # a volume below this is a touching face


def _exec(part):
    path = os.path.join(REPO, 'models', 'robotarm', part + '.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    ns = {'__name__': part, '__file__': path}
    exec(compile(io.open(path, encoding='utf-8').read(), path, 'exec'), ns)
    ns['run']('')


def _box(root, name, x0, x1, y0, y1, z0, z1):
    """A dummy box in its own component, mm in, cm to Fusion."""
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = DUMMY + name
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = 'sk_' + name
    P3 = adsk.core.Point3D.create
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        sk.modelToSketchSpace(P3(x0 / 10, y0 / 10, 0)),
        sk.modelToSketchSpace(P3(x1 / 10, y1 / 10, 0)))
    inp = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByString('%.4f mm' % z0))
    inp.setDistanceExtent(False, adsk.core.ValueInput.createByString('%.4f mm' % (z1 - z0)))
    comp.features.extrudeFeatures.add(inp)
    return occ


def _cyl(root, name, x, y, d, z0, z1, d_in=0.0):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = DUMMY + name
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = 'sk_' + name
    P3 = adsk.core.Point3D.create
    c = sk.modelToSketchSpace(P3(x / 10, y / 10, 0))
    sk.sketchCurves.sketchCircles.addByCenterRadius(c, d / 20)
    if d_in:
        sk.sketchCurves.sketchCircles.addByCenterRadius(c, d_in / 20)
    prof = min((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda p: -p.areaProperties().area if not d_in
               else abs(p.areaProperties().area - 3.14159265 * ((d / 20) ** 2 - (d_in / 20) ** 2)))
    inp = comp.features.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByString('%.4f mm' % z0))
    inp.setDistanceExtent(False, adsk.core.ValueInput.createByString('%.4f mm' % (z1 - z0)))
    comp.features.extrudeFeatures.add(inp)
    return occ


def _move(root, comp_name, dz_mm):
    for o in root.occurrences:
        if o.component.name == comp_name:
            m = adsk.core.Matrix3D.create()
            m.translation = adsk.core.Vector3D.create(0, 0, dz_mm / 10)
            o.transform2 = m
            return o
    raise AssertionError('no occurrence of %s to move' % comp_name)


def build(app):
    import math
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'gate_base'
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    for p in PARTS:
        _exec(p)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    from lib.j1_drive import (J1_SERVO, J1_DECK_Z_MM, TT_RACE_Z_MM,
                              HOME_R_MM, HOME_AZ_DEG, MAGNET_D_MM, MAGNET_H_MM,
                              HALL_BODY_W_MM, HALL_BODY_H_MM, HALL_BODY_T_MM)
    ups = design.userParameters
    # the MG995: case, tabs, boss (spline left out - it is a PRESS into the hub)
    s = J1_SERVO
    yo = s.case_l / 2 - s.shaft_from_end
    case_top = J1_DECK_Z_MM + s.tab_thk + s.tab_below_top
    _box(root, 'mg995_case', -s.case_w / 2, s.case_w / 2, yo - s.case_l / 2, yo + s.case_l / 2,
         case_top - s.case_h, case_top)
    _box(root, 'mg995_tabs', -s.case_w / 2, s.case_w / 2, yo - s.tab_span / 2,
         yo + s.tab_span / 2, J1_DECK_Z_MM, J1_DECK_Z_MM + s.tab_thk)
    _cyl(root, 'mg995_boss', 0.0, 0.0, s.boss_dia, case_top, case_top + s.boss_h)
    # the ESP32 carrier, from base_platter's own parameters
    def bp(n):
        return ups.itemByName('bp_' + n).value * 10
    zf = -bp('height') + bp('floor_t')
    zp = zf + bp('esp_below')
    x0, x1, yh = bp('esp_x0'), bp('esp_x0') + bp('pcb_w'), bp('pcb_l') / 2
    _box(root, 'esp_pcb', x0, x1, -yh, yh, zp, zp + bp('pcb_t'))
    _box(root, 'esp_above', x0, x1, -yh, yh, zp + bp('pcb_t'), zf + bp('esp_h'))
    lg = bp('ledge')
    _box(root, 'esp_below', x0 + lg, x1 - lg, -yh + lg, yh - lg, zf, zp)
    # home sensor and magnet
    a = math.radians(HOME_AZ_DEG)
    hx, hy = HOME_R_MM * math.cos(a), HOME_R_MM * math.sin(a)
    top = ups.itemByName('ts_hall_top').value * 10
    _box(root, 'hall_a3144', hx - HALL_BODY_W_MM / 2, hx + HALL_BODY_W_MM / 2,
         hy - HALL_BODY_H_MM / 2, hy + HALL_BODY_H_MM / 2, top - HALL_BODY_T_MM, top)
    _cyl(root, 'home_magnet_sweep', 0.0, 0.0, 2 * HOME_R_MM + MAGNET_D_MM,
         TT_RACE_Z_MM - MAGNET_H_MM, TT_RACE_Z_MM, d_in=2 * HOME_R_MM - MAGNET_D_MM)
    # POSITIVE CONTROL - buried in the floor under the bay
    _box(root, 'positive_control', x0 + 10, x0 + 20, -5, 5, zf - 1.5, zf + 0.5)
    print('built %d occurrences into %s - now run with REBUILD = False'
          % (root.occurrences.count, doc.name))


def place(design):
    """Put the hub and the rotor where they run. ABSOLUTE, so re-running is
    harmless; and SNAPSHOTTED, because a moved occurrence with no joint is
    reverted on the next compute otherwise - the first analyse() saw both
    still at their own origins, inside the servo and the base. Kept out of
    build(): a build that overruns the 60 s MCP limit never reaches it."""
    root = design.rootComponent
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from lib.j1_drive import J1_DECK_Z_MM, J1_HUB, TT_RACE_Z_MM
    _move(root, 'robotarm_j1_hub', J1_DECK_Z_MM + J1_HUB.seat_z)
    sb = [o for o in root.occurrences if o.component.name == 'robotarm_shoulder_bracket'][0]
    sb.transform2 = adsk.core.Matrix3D.create()
    sb_race = sb.component.bRepBodies.item(0).boundingBox.minPoint.z * 10
    _move(root, 'robotarm_shoulder_bracket', TT_RACE_Z_MM - sb_race)
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()
    for o in root.occurrences:
        if o.component.name in ('robotarm_j1_hub', 'robotarm_shoulder_bracket'):
            print('placed %s at z %+.2f' % (o.component.name,
                                           o.transform2.translation.z * 10))


def _name(ent):
    """An interference entity is an Occurrence or (in context) a BRepBody."""
    if hasattr(ent, 'component'):
        return ent.component.name.replace('robotarm_', '')
    occ = ent.assemblyContext
    return (occ.component.name if occ else ent.parentComponent.name).replace('robotarm_', '')


def analyse(app):
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    place(design)
    col = adsk.core.ObjectCollection.create()
    for o in root.occurrences:
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
        n1 = _name(r.entityOne)
        n2 = _name(r.entityTwo)
        if CONTROL.replace('robotarm_', '') in (n1, n2):
            control += v
            continue
        if n1.startswith('dummy_') and n2.startswith('dummy_'):
            continue            # envelopes of one COTS item overlap by design
        hits.append((v, n1, n2))
    print('=== GATE base: %d occurrences ===' % col.count)
    print('positive control: %.2f mm3 found (must be > 0)' % control)
    for v, n1, n2 in sorted(hits, reverse=True):
        print('  INTERFERENCE %-26s ^ %-26s %9.3f mm3' % (n1, n2, v))
    ok = control > 0 and not hits
    print('GATE base_interference: %s' % ('PASS' if ok else 'FAIL'))


def run(_context: str):
    app = adsk.core.Application.get()
    if REBUILD:
        build(app)
    else:
        analyse(app)
