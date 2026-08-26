"""robotarm/_check_wrist - the wrist gate.

Rebuilds the J3/J4/J5 chain from its committed scripts, assembles it from
FRESH occurrences at a series of pitch and roll angles, and asserts that
nothing touches anything it should not through the full sweep.

This is a separate gate from _check_fit (the gripper). Both must pass.

What it is actually looking for, in order of how much each has already cost
this project:

1. A part carved to fit its neighbour. A feature with no participantBodies
   takes part with everything it intersects ACROSS components, so a later
   script's pocket can hollow out an earlier part - silently, isValid still
   True - and the interference check then passes because the two were cut to
   match. Volume is recorded as each part finishes and re-checked at the end.

2. A measurement of nothing. A hidden occurrence reports an EMPTY bounding
   box and a body proxy taken the wrong way collapses to a point, both of
   which measure 0.000 and read as a perfect fit. Every body is checked for a
   real bounding box before it is measured.

3. A joint that assembles at zero and jams at sixty. Pitch is swept, not
   spot-checked at the pose that happens to look right.
"""

import importlib.util
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ['wrist_hub', 'wrist_roll', 'wrist_rotator', 'forearm']
PITCH_DEG = [-90.0, -60.0, -30.0, 0.0, 30.0, 60.0, 90.0]
ROLL_DEG = [-90.0, 0.0, 90.0]
LEAVE_AT_PITCH = -30.0
LEAVE_AT_ROLL = 0.0
# The hub's hex is drawn with a vertex on its local +X; the socket in the roll
# housing is drawn with a vertex on the assembly's +Y. This is the spin that
# takes one to the other. A hex repeats every 60 deg, so only 90 mod 60 = 30
# deg of it matters - but getting it wrong is a jam, not a rattle.
HUB_SPIN_DEG = 90.0


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

    # ---- rebuild every piece from its committed script --------------------
    built_volume = {}
    for name in PARTS:
        path = os.path.join(REPO, 'models', 'robotarm', name + '.py')
        assert os.path.exists(path), 'missing ' + path
        spec = importlib.util.spec_from_file_location('gen_' + name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run(_context)
        for occ in adsk.fusion.Design.cast(app.activeProduct).rootComponent.occurrences:
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
    print('')

    C = dict((n, keepers['robotarm_' + n].component) for n in PARTS)

    plate_in = gv('fa_plate_in')
    l2 = gv('fa_l2')
    gap = gv('fa_gap')
    rot = gv('fa_rot')
    loc = gv('wh_loc')
    tol = gv('fa_tol')
    y_front = gv('wro_y_front')

    def rot_m(angle, axis):
        m = M3()
        m.setToRotation(angle, axis, ORG)
        return m

    def place_hub(sx, y_p, pitch=0.0):
        """local +Z is the hex; it has to point INBOARD, and local z = 0 has to
        land on the plate's inner face.

        A J4 hub is KEYED INTO the roll housing, so it turns with the pitch and
        rotates inside the forearm's bore - not the other way round. Placing it
        unpitched put 81 mm3 of hub inside the housing at every pitch that was
        not a multiple of 60 deg, which is the hex's own period and the giveaway
        that the fault was in the placement, not the part."""
        m = rot_m(math.radians(HUB_SPIN_DEG), VEC(0, 0, 1))
        m.transformBy(rot_m(-sx * math.pi / 2, VEC(0, 1, 0)))
        t = m.translation
        t.x = sx * plate_in
        t.y = y_p
        m.translation = t
        m.transformBy(rot_m(math.radians(pitch), VEC(1, 0, 0)))
        return m

    def place_roll(pitch):
        """wrist_roll is drawn in the SAME frame as the forearm - origin on the
        pitch axis, +X along it - so at pitch 0 it is the identity. That is not
        a coincidence, it is why both files carry the shared wr_ block."""
        return rot_m(math.radians(pitch), VEC(1, 0, 0))

    def place_rotator(pitch, roll):
        m = rot_m(math.radians(roll), VEC(0, 0, 1))
        m.transformBy(rot_m(-math.pi / 2, VEC(1, 0, 0)))
        t = m.translation
        t.y = y_front
        m.translation = t
        m.transformBy(place_roll(pitch))
        return m

    def pose(pitch, roll):
        add = root.occurrences.addExistingComponent
        return {
            'forearm': add(C['forearm'], M3()),
            'hub_j4p': add(C['wrist_hub'], place_hub(+1, 0.0, pitch)),
            'hub_j4m': add(C['wrist_hub'], place_hub(-1, 0.0, pitch)),
            'hub_j3p': add(C['wrist_hub'], place_hub(+1, -l2)),
            'hub_j3m': add(C['wrist_hub'], place_hub(-1, -l2)),
            'roll': add(C['wrist_roll'], place_roll(pitch)),
            'rotator': add(C['wrist_rotator'], place_rotator(pitch, roll)),
        }

    mm = app.measureManager

    def body_of(occ):
        return occ.component.bRepBodies.item(0).createForAssemblyContext(occ)

    def clearance(o1, o2):
        b1, b2 = body_of(o1), body_of(o2)
        for b in (b1, b2):
            bb = b.boundingBox
            assert bb.maxPoint.x - bb.minPoint.x > tol, (
                'degenerate body: the timeline marker is not at the end, or the '
                'occurrence is hidden - measurements here would be fiction')
        return mm.measureMinimumDistance(b1, b2).value * 10

    def label(entity):
        # analyzeInterference hands back Occurrences when each component has one
        # occurrence and BRepBodies when it has several. Both turn up here.
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

    want_roll_fa = gap * 10
    want_hub_fa = rot / 2 * 10
    want_hub_roll = loc / 2 * 10

    print('=== wrist fit check ===')
    print('J4 straddle %.1f | plate inner face |x| %.1f | running gap %.2f each side'
          % (gv('wr_straddle') * 10, plate_in * 10, gap * 10))
    print('')
    print('contracted, per specs/robotarm/_assembly.md:')
    print('  roll^forearm >= %.3f  free fit, the pitch joint running gap' % want_roll_fa)
    print('  hub^forearm  0.000 EXPECTED: the flange bottoms on the counterbore')
    print('  hub^roll     0.000 EXPECTED: the hex bottoms in its socket')
    print('               Those two stops are what trap the hub with no screw, so a')
    print('               distance of zero is the contract being met. The fit that')
    print('               matters there is RADIAL (%.3f / %.3f) and only interference'
          % (want_hub_fa, want_hub_roll))
    print('               can see it - a minimum distance cannot.')
    print('')
    print('%8s %6s %12s %12s %12s %10s' % (
        'pitch', 'roll', 'roll^fa', 'hub^fa', 'hub^roll', 'interf'))

    worst = 0.0
    fails = []
    for pitch in PITCH_DEG:
        for roll in (ROLL_DEG if abs(pitch) < 1e-6 else [0.0]):
            p = pose(pitch, roll)
            moving = [p['forearm'], p['hub_j4p'], p['hub_j4m'], p['roll'], p['rotator']]
            total, pairs = interference(moving)
            worst = max(worst, total)
            d_rf = clearance(p['roll'], p['forearm'])
            d_hf = clearance(p['hub_j4p'], p['forearm'])
            d_hr = clearance(p['hub_j4p'], p['roll'])
            print('%7.0f%s %5.0f%s %12.3f %12.3f %12.3f %10.2f' % (
                pitch, 'd', roll, 'd', d_rf, d_hf, d_hr, total))
            if total > 1.0:
                fails.append('pitch %.0f: interference %.2f mm3 (%s)'
                             % (pitch, total, '; '.join(pairs)))
            if d_rf < want_roll_fa - tol * 10:
                fails.append('pitch %.0f: roll^forearm %.3f < %.3f'
                             % (pitch, d_rf, want_roll_fa))
            for o in p.values():
                o.deleteMe()

    final = pose(LEAVE_AT_PITCH, LEAVE_AT_ROLL)
    solid = sum(body_of(o).physicalProperties.mass for o in final.values())
    bb = root.boundingBox
    print('')
    print('wrist bbox at pitch %.0f, mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f' % (
        LEAVE_AT_PITCH, bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('printed mass, solid PETG %.2f g -> ~%.1f g at 40%% infill + 4 walls'
          % (solid * 1000, solid * 1000 * 0.6))
    print('')
    print('GATE interference : worst %.3f mm3 - %s' % (
        worst, 'PASS' if worst < 1.0 else 'FAIL'))
    print('GATE clearances   : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)

    for occ in keepers.values():
        occ.isLightBulbOn = False
