"""robotarm/_check_base - GATE for the new base and the MG995 J1 stack.

Driver, not a part. Builds, into ONE fresh document, everything that meets
at J1 in the stator frame (z 0 = platter rim top, J1 axis):

    base_platter, base_lid, turntable_stator, turntable_ring   as built
    j1_hub          moved up to its seat: deck_z + seat_z
    shoulder_bracket  moved so its race face lands on tt_race_z
    roller_cap x3   on each 608's stub, over the proud stub end
    pcb_keeper x4   pushed down over each ESP32 corner fence
    DUMMIES (COTS envelopes, not printed): the MG995 case + tabs + boss,
    the ESP32 board and its above/below cable envelopes, the hall sensor,
    the home magnet, the three 608ZZ and the three M3 x 8 cap-screw heads

and runs Design.analyzeInterference over all of it, WITH A POSITIVE
CONTROL - a block buried in the platter floor that MUST be reported. A gate
that has never found anything proves nothing (_HANDOFF.md section 2).

Run FOUR times: STAGE = 1 (fresh document, first three parts), STAGE = 2
(the other three + the dummies), STAGE = 3 (the printed bits + roller
dummies), STAGE = 0 (place + analyse). One call for all of it overran the
60 s MCP limit on 2026-09-27.

Touching faces are not interference (areCoincidentFacesIncluded = False).
The ONE designed overlap is the pcb_keeper: a 0.15 press on its fence and
a 0.2 preload onto the board, plus its tongue sitting inside the board's
above-envelope at each corner. Those three pairs are computed here from the
keeper's own parameters and must land within KEEPER_BAND of the analytic
volume - which also proves every keeper really is ON its fence.
"""

import io
import math
import os
import sys

import adsk.core
import adsk.fusion

STAGE = 1
REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ('base_platter', 'base_lid', 'turntable_stator', 'turntable_ring',
         'j1_hub', 'shoulder_bracket')
DUMMY = 'robotarm_dummy_'
CONTROL = DUMMY + 'positive_control'
LIMIT_MM3 = 0.001                  # a volume below this is a touching face
BITS = ('roller_cap', 'pcb_keeper', 'turret_shroud')
SHROUD_BAND = (0.7, 1.3)          # measured / analytic press film on the posts
KEEPER_BAND = (0.85, 1.15)         # measured / analytic, for the designed overlaps
HEAD = 'dummy_m3_head_'


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


def _cyl(root, name, x, y, d, z0, z1, d_in=0.0, m=None):
    occ = root.occurrences.addNewComponent(m or adsk.core.Matrix3D.create())
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


def _frame(origin_mm, xa, ya, za):
    m = adsk.core.Matrix3D.create()
    V3 = adsk.core.Vector3D.create
    m.setWithCoordinateSystem(
        adsk.core.Point3D.create(*[c / 10 for c in origin_mm]),
        V3(*[float(c) for c in xa]), V3(*[float(c) for c in ya]),
        V3(*[float(c) for c in za]))
    return m


def _radial(az_deg, r_mm, z_mm):
    """Local +z radially OUT at az, local +y up, origin at (r, z)."""
    import math
    a = math.radians(az_deg)
    c, s_ = math.cos(a), math.sin(a)
    return _frame((r_mm * c, r_mm * s_, z_mm), (-s_, c, 0.0), (0.0, 0.0, 1.0), (c, s_, 0.0))


def _local_cyl(root, name, m, d, z0, z1, d_in=0.0):
    """_cyl at the origin of its own frame m."""
    return _cyl(root, name, 0.0, 0.0, d, z0, z1, d_in, m)


def _roll_az():
    import ast
    src = io.open(os.path.join(REPO, 'models', 'robotarm', 'turntable_stator.py'),
                  encoding='utf-8').read()
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'ROLL_AZ':
            return ast.literal_eval(n.value)
    raise AssertionError('turntable_stator has no ROLL_AZ')


def _keeper_frames(ups):
    """(origin, x, y, z) for each board corner, board-top z. The keeper is
    symmetric about its corner diagonal, so a mirror corner is a rotation."""
    def bp(n):
        return ups.itemByName('bp_' + n).value * 10
    zf = -bp('height') + bp('floor_t')
    ztop = zf + bp('esp_below') + bp('pcb_t')
    x0, x1, yh = bp('esp_x0'), bp('esp_x0') + bp('pcb_w'), bp('pcb_l') / 2
    out = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            o = (x0 if sx < 0 else x1, -yh if sy < 0 else yh, ztop)
            if sx * sy > 0:
                out.append(_frame(o, (-sx, 0, 0), (0, -sy, 0), (0, 0, 1)))
            else:
                out.append(_frame(o, (0, -sy, 0), (-sx, 0, 0), (0, 0, 1)))
    return out


def _keeper_expected(ups):
    """Analytic mm3, per keeper, of its three designed overlaps."""
    def pk(n):
        return ups.itemByName('pk_' + n).value * 10
    f_in = -pk('play')
    f_out = f_in - pk('fence_t')
    half = pk('press') / 2
    reach, tongue = pk('reach'), pk('tongue')
    film = (half * pk('grip') * 2 * (reach - f_out)
            + half * (pk('fence_over') + pk('preload')) * 2 * (reach - f_in))
    lap = 2 * tongue * reach - tongue ** 2
    return {'base_platter': film,
            'dummy_esp_pcb': pk('preload') * lap,
            'dummy_esp_above': (pk('fence_over') + pk('plate_t')) * lap}


def _move(root, comp_name, dz_mm):
    for o in root.occurrences:
        if o.component.name == comp_name:
            m = adsk.core.Matrix3D.create()
            m.translation = adsk.core.Vector3D.create(0, 0, dz_mm / 10)
            o.transform2 = m
            return o
    raise AssertionError('no occurrence of %s to move' % comp_name)


def build(app, stage):
    import math
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    if stage == 1:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = 'gate_base'
        for p in PARTS[:3]:
            _exec(p)
        print('stage 1: %s built - now STAGE = 2' % ', '.join(PARTS[:3]))
        return
    doc = app.activeDocument
    assert doc.name.startswith('gate_base'), 'stage %d runs in the gate_base document' % stage
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    if stage == 3:
        for p in BITS:
            _exec(p)
        ups = design.userParameters

        def tt(n):
            return ups.itemByName('tt_' + n).value * 10
        seat = tt('roller_r') - tt('roller_w') / 2        # the race face the cap sits on
        cap_t = ups.itemByName('rc_t').value * 10
        for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
            del sys.modules[m]
        from lib.j1_drive import J1_HUB_HEAD_D_MM, J1_HUB_HEAD_H_MM
        for az in _roll_az():
            _local_cyl(root, '608_%d' % az, _radial(az, seat, tt('axle_z')),
                       tt('roller_od'), 0.0, tt('roller_w'), d_in=tt('axle_d') + 0.1)
            _local_cyl(root, 'm3_head_%d' % az,
                       _radial(az, seat - cap_t - J1_HUB_HEAD_H_MM, tt('axle_z')),
                       J1_HUB_HEAD_D_MM, 0.0, J1_HUB_HEAD_H_MM)
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()
        print('stage 3: %s + 608/head dummies built - now STAGE = 0' % ', '.join(BITS))
        return
    for p in PARTS[3:]:
        _exec(p)
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    from lib.j1_drive import (J1_SERVO, J1_DECK_Z_MM, TT_RACE_Z_MM,
                              HOME_R_MM, HOME_AZ_DEG, MAGNET_D_MM, MAGNET_PROTRUDE_MM,
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
         TT_RACE_Z_MM - MAGNET_PROTRUDE_MM, TT_RACE_Z_MM, d_in=2 * HOME_R_MM - MAGNET_D_MM)
    # POSITIVE CONTROL - buried in the floor under the bay
    _box(root, 'positive_control', x0 + 10, x0 + 20, -5, 5, zf - 1.5, zf + 0.5)
    print('built %d occurrences into %s - now STAGE = 3'
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
    # the printed bits: one occurrence each was built at the origin; put it
    # at its first station and add the rest. Extra copies from an earlier
    # run are removed first, so this is re-runnable.
    ups = design.userParameters
    seat = (ups.itemByName('tt_roller_r').value - ups.itemByName('tt_roller_w').value / 2) * 10
    cap_t = ups.itemByName('rc_t').value * 10
    z_ax = ups.itemByName('tt_axle_z').value * 10
    stations = {'robotarm_roller_cap': [_radial(az, seat - cap_t, z_ax) for az in _roll_az()],
                'robotarm_pcb_keeper': _keeper_frames(ups)}
    for cname, frames in stations.items():
        occs = [o for o in root.occurrences if o.component.name == cname]
        assert occs, 'no %s in the document - run STAGE 3' % cname
        for o in occs[1:]:
            o.deleteMe()
        occs = occs[:1] + [root.occurrences.addExistingComponent(
            occs[0].component, adsk.core.Matrix3D.create()) for _ in frames[1:]]
        # SET EACH ONE AFTER ALL EXIST: addExistingComponent(comp, m) came back
        # with m composed onto the first occurrence's transform (2026-09-27).
        for o, m in zip(occs, frames):
            o.transform2 = m
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
    expect = _keeper_expected(design.userParameters)
    n_keep = sum(1 for o in root.occurrences if o.component.name == 'robotarm_pcb_keeper')
    got = dict((k, 0.0) for k in expect)
    # the shroud's three saddles press 0.15 on the turret posts' outer faces
    def tp(n):
        return design.userParameters.itemByName(n).value * 10
    _post_rr, _post_hr = tp('tt_post_r'), tp('ts_post_d') / 2
    _theta = math.acos(min(1.0, (tp('tsh_saddle_in') - _post_rr) / _post_hr))
    shroud_want = (3 * 2 * _theta * _post_hr * tp('tsh_press') / 2
                   * (tp('tsh_h') - tp('tsh_saddle_z0') - tp('tsh_saddle_gap') - tp('tsh_saddle_chamfer')))
    shroud_got = 0.0
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
        if {n1, n2} == {'turret_shroud', 'turntable_stator'}:
            shroud_got += v
            continue
        if 'pcb_keeper' in (n1, n2):
            other = n2 if n1 == 'pcb_keeper' else n1
            if other in got:
                got[other] += v
                continue
        hits.append((v, n1, n2))
    print('=== GATE base: %d occurrences ===' % col.count)
    print('positive control: %.2f mm3 found (must be > 0)' % control)
    for v, n1, n2 in sorted(hits, reverse=True):
        print('  INTERFERENCE %-26s ^ %-26s %9.3f mm3' % (n1, n2, v))
    keep_ok = True
    for k, per in sorted(expect.items()):
        want = per * n_keep
        ratio = got[k] / want if want else 0.0
        good = KEEPER_BAND[0] <= ratio <= KEEPER_BAND[1]
        keep_ok = keep_ok and good
        print('  keeper ^ %-18s %8.2f mm3, analytic %8.2f (x%d)  %s'
              % (k, got[k], want, n_keep, 'ok' if good else 'OUT OF BAND'))
    s_ratio = shroud_got / shroud_want if shroud_want else 0.0
    shroud_ok = SHROUD_BAND[0] <= s_ratio <= SHROUD_BAND[1]
    print('  shroud ^ turret posts  %8.2f mm3, analytic %8.2f  %s'
          % (shroud_got, shroud_want, 'ok' if shroud_ok else 'OUT OF BAND'))
    ok = control > 0 and not hits and keep_ok and n_keep == 4 and shroud_ok
    print('GATE base_interference: %s' % ('PASS' if ok else 'FAIL'))


def run(_context: str):
    app = adsk.core.Application.get()
    if STAGE:
        build(app, STAGE)
    else:
        analyse(app)
