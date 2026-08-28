"""robotarm/_check_shoulder - the J2 gate.

Rebuilds the shoulder from its committed scripts, assembles it from FRESH
occurrences through J2's declared travel, and asserts that nothing touches
anything it should not.

Same three failure modes _check_wrist watches for (a part carved to fit its
neighbour, a measurement of nothing, a joint that assembles at zero and jams
at sixty), plus one this joint has and the wrist does not:

4. THE SERVO IS THE BIGGEST THING AT J2 AND IT IS NOT A PRINTED PART. An
   MG995 is 40.9 x 20 x 36.5 with tabs spanning 54.0, and none of it appears in
   any model file - the bracket only cuts a hole where it goes. So this gate
   builds the servo as a scratch envelope (case, tab plate, output boss) and
   sweeps the arm past it. Getting that envelope's ORIGIN wrong is the easy
   mistake, so it is spelled out below rather than left as three numbers.

THE SERVO ENVELOPE, DERIVED NOT ASSUMED. lib/servo.py puts the origin on the
output shaft axis at the TAB PLANE - the underside of the mounting tabs, the
face a bracket clamps - with +Z out of the shaft. tab_below_top is measured to
the TOP of the tabs, so the underside sits tab_below_top + tab_thk = 9.7 mm
from the case top. That sum is exactly sb_lobe_t, which is why the pad is that
thick and not a chosen number: the tabs bear on the pad's OUTER face, the
screws go inboard from there, and the case top lands flush on sb_plate_out.
The case body then runs OUTBOARD from that face, through the pad's window and
out the far side. Model it the other way round and the servo appears to be
buried in the arm.
"""

import importlib.util
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ['wrist_hub', 'shoulder_hub', 'upper_arm', 'shoulder_bracket']
# J2's declared travel. The down end is NOT symmetric and NOT arbitrary: the
# arm reaches the turntable's retainer ring at about -27 deg (shoulder_bracket.py
# scans for it), so -25 is the limit with a margin. It used to be -40, when the
# base was a 40 mm rectangular plate rather than a Ø100 ring.
PITCH_DEG = [-25.0, -10.0, 0.0, 30.0, 60.0, 90.0, 120.0, 160.0]
LEAVE_AT_PITCH = 30.0
# Same spin as the wrist: the hub's hex is drawn with a vertex on its local +X,
# every socket in this arm with a vertex on the assembly's +Y.
HUB_SPIN_DEG = 90.0
# RUN THIS TWICE: REBUILD=True, then REBUILD=False. Four parts plus eight poses
# of interference analysis is over the 60 s MCP call limit in one go, exactly as
# _check_pruner is. The loader sets it - `mod.REBUILD = False` - so the pass that
# does the measuring never touches the geometry it is measuring.
REBUILD = True


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    ups = design.userParameters
    M3 = adsk.core.Matrix3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)

    def gv(name):
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        return p.value

    # ---- rebuild every piece from its committed script ----------------------
    built_volume = {}
    if REBUILD:
        for name in PARTS:
            path = os.path.join(REPO, 'models', 'robotarm', name + '.py')
            assert os.path.exists(path), 'missing ' + path
            spec = importlib.util.spec_from_file_location('gen_' + name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.run(_context)
            for occ in adsk.fusion.Design.cast(
                    app.activeProduct).rootComponent.occurrences:
                if occ.component.name == 'robotarm_' + name:
                    built_volume[name] = occ.component.bRepBodies.item(0).volume
        print('')

    root = design.rootComponent
    keepers = {}
    for occ in list(root.occurrences):
        if occ.component.name in keepers:
            occ.deleteMe()
        else:
            keepers[occ.component.name] = occ
    design.timeline.moveToEnd()

    if REBUILD:
        scars = []
        for name, vol in built_volume.items():
            now = keepers['robotarm_' + name].component.bRepBodies.item(0).volume
            if abs(now - vol) > vol * 1e-6:
                scars.append('%s %.1f -> %.1f mm3' % (name, vol * 1000, now * 1000))
        assert not scars, (
            'a later part script cut into an earlier part: ' + '; '.join(scars) +
            ' - set participantBodies on every non-NewBody feature')
        print('volume unchanged after all parts built: %s' % ', '.join(
            '%s %.0f mm3' % (k, v * 1000) for k, v in sorted(built_volume.items())))
        print('THIS PASS BUILT ONLY. Re-run with REBUILD=False to measure.')
        return
    for name in PARTS:
        assert 'robotarm_' + name in keepers, (
            'robotarm_%s is not in the document - run the REBUILD=True pass first'
            % name)
        print('%s %.0f mm3' % (name, keepers['robotarm_' + name]
                               .component.bRepBodies.item(0).volume * 1000))
    print('')

    C = dict((n, keepers['robotarm_' + n].component) for n in PARTS)

    plate_in = gv('sb_plate_in')
    plate_out = gv('sb_plate_out')
    lobe_t = gv('sb_lobe_t')
    gap = gv('sb_gap')
    rot = gv('sb_rot')
    loc = gv('wh_loc')
    tol = gv('sb_tol')
    l1 = gv('ua_l1')

    # ---- the MG995, as a scratch envelope -----------------------------------
    # Rebuilt every run so it can never drift from the parameters the bracket
    # was cut from. Three boxes on the shaft axis; see the module docstring for
    # why the tab plane and not the case is the datum.
    ENV = 'robotarm_MG995_envelope'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == ENV or c.name.startswith(ENV + ' ('):
            c.name = ENV + '_stale_' + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(ENV + '_stale_'):
            occ.deleteMe()
    env_occ = root.occurrences.addNewComponent(M3())
    env = env_occ.component
    env.name = ENV
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def mm(cm):
        return '%.4f mm' % (cm * 10.0)

    def env_box(name, y0, y1, z0, z1, x0, x1, op):
        sk = env.sketches.add(env.yZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            sk.modelToSketchSpace(P3(0, y0, z0)), sk.modelToSketchSpace(P3(0, y1, z1)))
        assert sk.profiles.count == 1, name
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = env.features.extrudeFeatures.createInput(col, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(x0)))
        inp.setDistanceExtent(False, V(mm(x1 - x0)))
        if op != adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
            inp.participantBodies = [env.bRepBodies.item(i)
                                     for i in range(env.bRepBodies.count)]
        env.features.extrudeFeatures.add(inp).name = name

    def env_cyl(name, y_c, z_c, d, x0, x1, op):
        """ROUND, not a box. Modelling the Oe13 output boss as a 13 x 13 prism
        put its four corners at r 9.19 - a millimetre outside the hub's 16.4
        mouth - and reported 9.7 mm3 of interference at every pose. Constant
        across a sweep is the tell: a real collision moves."""
        sk = env.sketches.add(env.yZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(0, y_c, z_c)), d / 2)
        assert sk.profiles.count == 1, name
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = env.features.extrudeFeatures.createInput(col, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(x0)))
        inp.setDistanceExtent(False, V(mm(x1 - x0)))
        if op != adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
            inp.participantBodies = [env.bRepBodies.item(i)
                                     for i in range(env.bRepBodies.count)]
        env.features.extrudeFeatures.add(inp).name = name

    NEWB = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOINB = adsk.fusion.FeatureOperations.JoinFeatureOperation

    case_w = gv('sb_case_w')
    case_l = gv('sb_case_l')
    case_h = 3.65            # MG995 case_h 36.5 mm, DATASHEET drawing B
    boss_d, boss_h = 1.30, 0.30
    tab_thk = gv('sb_tab_thk')
    tab_span = 5.40          # cm - TowerPro official E 54.0, 2026-08-27 audit
    case_hi = gv('sb_shaft_end')
    case_lo = case_hi - case_l
    tab_plane = plate_out + lobe_t          # the datum. See the docstring.
    p_off = ups.itemByName('sb_horn_standoff')
    standoff = p_off.value if p_off is not None else 0.0
    case_top = plate_out + standoff         # horn audit: stood off, not flush
    assert abs((tab_plane - case_top)
               - (gv('sb_tab_below_top') + gv('sb_tab_thk'))) < 1e-9, (
        'the case top is not tab stack below the tab plane - sb_lobe_t is '
        'not tab_below_top + tab_thk + horn_standoff any more')
    env_box('case', -case_w / 2, case_w / 2, case_lo, case_hi,
            case_top, case_top + case_h, NEWB)
    env_box('tabs', -case_w / 2, case_w / 2,
            (case_hi + case_lo) / 2 - tab_span / 2, (case_hi + case_lo) / 2 + tab_span / 2,
            tab_plane, tab_plane + tab_thk, JOINB)
    assert env.bRepBodies.count == 1, 'servo envelope came out in %d pieces' % (
        env.bRepBodies.count)
    env.bRepBodies.item(0).name = 'MG995_envelope'

    # ---- and the output stack, WHICH TURNS --------------------------------
    # A separate component because it is a separate rigid body: the case is
    # bolted to the bracket and never moves, but the boss, the horn and its
    # cross all turn with the joint. Modelled as one static lump it reported a
    # tidy 49 mm3 of interference at every pitch EXCEPT 0 and 90 - which is the
    # cross's own period, and the giveaway that the fault was the placement.
    OUT = 'robotarm_MG995_output'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == OUT or c.name.startswith(OUT + ' ('):
            c.name = OUT + '_stale_' + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(OUT + '_stale_'):
            occ.deleteMe()
    out_occ = root.occurrences.addNewComponent(M3())
    out = out_occ.component
    out.name = OUT
    env, out = out, env          # env_box/env_cyl close over `env`
    # MEASURED 2026-08-28: hub Ø8.7 (the 13.8 this replaces was a community
    # model 5.1 mm out), blade 2.2 (was 2.5). Hub HEIGHT 3.8 is still model
    # grade - unmeasured, and the only horn number left that is. Arms are
    # modelled AT THE TRIM radius sh_horn_arm_r = 7.6, because the envelope
    # is the TRIMMED horn - an untrimmed tip reads as phantom mm3 in the
    # slot ends, which is exactly what it did at r 8.0.
    horn_hub_d, horn_hub_h = 0.87, 0.38
    blade_thk, arm_r = 0.22, 0.76
    horn_seat = case_top - boss_h                  # the boss top
    env_cyl('output_boss', 0.0, 0.0, boss_d, horn_seat, case_top, NEWB)
    # The horn is fitted BLADE TOWARD THE SERVO, which is the assumption
    # shoulder_hub.py's relief is cut from - so this is the piece of the
    # envelope that actually tests it.
    env_cyl('horn_hub', 0.0, 0.0, horn_hub_d, horn_seat - horn_hub_h, horn_seat, JOINB)
    for k, (dy, dz) in enumerate(((arm_r, blade_thk / 2), (blade_thk / 2, arm_r))):
        env_box('horn_arm_%d' % k, -dy, dy, -dz, dz,
                horn_seat - blade_thk, horn_seat, JOINB)
    env, out = out, env
    assert out.bRepBodies.count == 1, 'output stack came out in %d pieces' % (
        out.bRepBodies.count)
    out.bRepBodies.item(0).name = 'MG995_output'
    for name in (ENV, OUT):
        keepers.pop(name, None)
    print('MG995 envelope: tab plane x %.1f, case top x %.1f, case x %.1f..%.1f, '
          'z %.1f..%.1f' % (tab_plane * 10, case_top * 10, case_top * 10,
                            (case_top + case_h) * 10, case_lo * 10, case_hi * 10))
    print('  output stack inboard of that: boss %.1f x %.1f, horn hub %.1f x %.1f, '
          'blade %.1f thick to r %.1f, reaching x %.1f' % (
              boss_d * 10, boss_h * 10, horn_hub_d * 10, horn_hub_h * 10,
              blade_thk * 10, arm_r * 10, (horn_seat - horn_hub_h) * 10))
    print('')

    def rot_m(angle, axis):
        m = M3()
        m.setToRotation(angle, axis, ORG)
        return m

    def place_hub(sx, pitch):
        """local +Z is the hex and has to point INBOARD; local z = 0 lands on
        the plate's inner face. Both J2 hubs are KEYED INTO the upper arm, so
        both turn with the pitch and run in the bracket's bores - exactly as
        the J4 hubs turn with the roll housing."""
        m = rot_m(math.radians(HUB_SPIN_DEG), VEC(0, 0, 1))
        m.transformBy(rot_m(-sx * math.pi / 2, VEC(0, 1, 0)))
        t = m.translation
        t.x = sx * plate_in
        m.translation = t
        m.transformBy(rot_m(math.radians(pitch), VEC(1, 0, 0)))
        return m

    def place_arm(pitch):
        """upper_arm is drawn with its origin on J3 and J2 at y = -ua_l1, so it
        slides forward by l1 to put J2 on this frame's origin, then pitches
        about it. Positive pitch is UP."""
        m = M3()
        t = m.translation
        t.y = l1
        m.translation = t
        m.transformBy(rot_m(math.radians(pitch), VEC(1, 0, 0)))
        return m

    def pose(pitch):
        add = root.occurrences.addExistingComponent
        return {
            'bracket': add(C['shoulder_bracket'], M3()),
            'servo': add(env, M3()),
            'output': add(out, rot_m(math.radians(pitch), VEC(1, 0, 0))),
            'arm': add(C['upper_arm'], place_arm(pitch)),
            'hub_drive': add(C['shoulder_hub'], place_hub(+1, pitch)),
            'hub_idler': add(C['wrist_hub'], place_hub(-1, pitch)),
        }

    meas = app.measureManager

    def body_of(occ):
        return occ.component.bRepBodies.item(0).createForAssemblyContext(occ)

    def clearance(o1, o2):
        b1, b2 = body_of(o1), body_of(o2)
        for b in (b1, b2):
            bb = b.boundingBox
            assert bb.maxPoint.x - bb.minPoint.x > tol, (
                'degenerate body: the timeline marker is not at the end, or the '
                'occurrence is hidden - measurements here would be fiction')
        return meas.measureMinimumDistance(b1, b2).value * 10

    def label(entity):
        comp = getattr(entity, 'component', None)
        if comp is None:
            comp = getattr(entity, 'parentComponent', None)
        return (comp.name if comp else str(entity.objectType)).replace('robotarm_', '')

    def interference(occs):
        col = adsk.core.ObjectCollection.create()
        for o in occs:
            col.add(o)
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        total, pairs = 0.0, []
        for i in range(res.count):
            r = res.item(i)
            vol = r.interferenceBody.volume * 1000
            total += vol
            pairs.append('%s^%s %.2f mm3' % (label(r.entityOne), label(r.entityTwo), vol))
        return total, pairs

    want_arm_br = gap * 10
    want_hub_br = rot / 2 * 10
    want_hub_arm = loc / 2 * 10

    print('=== J2 shoulder fit check ===')
    print('straddle %.1f | plate inner face |x| %.1f | running gap %.2f each side'
          % (gv('wr_straddle') * 10, plate_in * 10, gap * 10))
    print('')
    print('contracted, per specs/robotarm/_assembly.md:')
    print('  arm^bracket  >= %.3f  free fit, the pitch joint running gap' % want_arm_br)
    print('  hub^bracket  0.000 EXPECTED: the flange bottoms on the counterbore')
    print('  hub^arm      0.000 EXPECTED: the hex bottoms in its socket')
    print('               Those two stops are what trap the hub with no screw. The')
    print('               fit that matters is RADIAL (%.3f / %.3f) and only'
          % (want_hub_br, want_hub_arm))
    print('               interference can see it.')
    print('  servo^arm    > 0     the MG995 is entirely outboard of the straddle,')
    print('               so this should not even be close through the whole sweep.')
    print('')
    print('%8s %12s %12s %12s %12s %10s' % (
        'pitch', 'arm^brkt', 'hub^brkt', 'hub^arm', 'servo^arm', 'interf'))

    worst = 0.0
    fails = []
    for pitch in PITCH_DEG:
        p = pose(pitch)
        total, pairs = interference(list(p.values()))
        worst = max(worst, total)
        d_ab = clearance(p['arm'], p['bracket'])
        d_hb = clearance(p['hub_drive'], p['bracket'])
        d_ha = clearance(p['hub_drive'], p['arm'])
        d_sa = clearance(p['servo'], p['arm'])
        print('%7.0f%s %12.3f %12.3f %12.3f %12.3f %10.2f' % (
            pitch, 'd', d_ab, d_hb, d_ha, d_sa, total))
        if total > 1.0:
            fails.append('pitch %.0f: interference %.2f mm3 (%s)'
                         % (pitch, total, '; '.join(pairs)))
        if d_ab < want_arm_br - tol * 10:
            fails.append('pitch %.0f: arm^bracket %.3f < %.3f' % (pitch, d_ab, want_arm_br))
        if d_sa <= tol * 10:
            fails.append('pitch %.0f: the MG995 envelope is touching the arm' % pitch)
        for o in p.values():
            o.deleteMe()

    final = pose(LEAVE_AT_PITCH)
    printed = sum(body_of(o).physicalProperties.mass
                  for k, o in final.items() if k not in ('servo', 'output'))
    bb = root.boundingBox
    print('')
    print('shoulder bbox at pitch %.0f, mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f' % (
        LEAVE_AT_PITCH, bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('printed mass here, solid PETG %.2f g -> ~%.1f g at 40%% infill + 4 walls'
          % (printed * 1000, printed * 1000 * 0.6))
    print('  (+ 55 g of MG995, which this joint carries but does not lift)')
    print('')
    print('GATE interference : worst %.3f mm3 - %s' % (
        worst, 'PASS' if worst < 1.0 else 'FAIL'))
    print('GATE clearances   : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)

    for occ in keepers.values():
        occ.isLightBulbOn = False
    env_occ.isLightBulbOn = False
    out_occ.isLightBulbOn = False
