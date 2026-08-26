"""robotarm/_check_fit - assembly fit check (helper, not a part script).

Rebuilds every gripper piece from its own generating script, places them at
their real assembly transforms, and sweeps the jaw open. Prints, per pose:
interference across every mating pair, and each clearance the
specs/robotarm/_assembly.md joint table contracts.

Gate (workflow 02 step 8): zero UNEXPECTED interference and zero missing
clearance, at the motion extremes, BEFORE any piece exports.

Assembly frame (the gripper's own):
  x  jaw opening direction, 0 on the centre plane
  y  forward, along the arm; the pinion axis and the servo shaft lie on it
  z  the clamshell split axis; the two rack pitch lines sit at +/- gr_offset

Two hard-won rules are baked into how this file places things:

1. NEVER set `occurrence.transform2` more than once in a parametric design.
   Each assignment adds a Move feature, and a stack of them corrupts the
   assembly-context body proxies - silently. The symptom is a body whose
   boundingBox collapses to a single point and whose measured distance to
   everything is 0.000, which reads as "the parts touch" rather than as the
   bug it is. Poses are therefore built by handing the transform to
   `addExistingComponent` and throwing the occurrence away afterwards.

2. Never delete the LAST occurrence of a component. An orphaned component
   still reserves its name while dropping out of allComponents, so the next
   rebuild gets handed "<name> (1)" and every lookup by name misses it. The
   occurrence each part script leaves behind is what keeps its component
   alive; this file hides those and never touches them.

Gear phasing is derived, not eyeballed - see phase_angle() below.
"""

import importlib.util
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ['gripper_pinion', 'gripper_rack_jaw', 'gripper_shell']
OPENINGS_MM = [0.0, 10.0, 20.0, 30.0, 40.0]
LEAVE_AT_MM = 20.0


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

    # ---- rebuild every piece from its committed script -------------------
    # Volume is recorded the moment each part finishes and re-checked after
    # the last one. A feature operation with no participantBodies takes part
    # with everything it intersects ACROSS components, so a later part's
    # pocket can hollow out an earlier one - silently, with isValid still
    # True, and the interference check then passes because the parts were
    # carved to fit each other. This is the guard for that.
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
            occ.deleteMe()          # a pose occurrence left over from last run
        else:
            keepers[occ.component.name] = occ
    # Deleting timeline-bearing objects can leave the marker part-way down the
    # history. Bodies then measure as they were AT THE MARKER - the pinion came
    # back half-cut and the rack collapsed to a point at (5, 5, 5) - with no
    # error anywhere. Drive the marker to the end before measuring anything.
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

    comp_pin = keepers['robotarm_gripper_pinion'].component
    comp_rack = keepers['robotarm_gripper_rack_jaw'].component
    comp_shell = keepers['robotarm_gripper_shell'].component

    # ---- the numbers the placement is built from -------------------------
    r_pitch = gv('gr_r_pitch')
    offset = gv('gr_offset')
    face = gv('gr_face')
    stroke = gv('gr_stroke')
    pitch = gv('rj_pitch')
    n_teeth = int(round(gv('rj_rack_teeth')))
    x_a = gv('rj_tooth_lead') - n_teeth * pitch
    arm_clear = gv('rj_arm_clear')
    slide = gv('gs_slide')

    def phase_angle(s):
        """Pinion rotation that meshes BOTH racks at rack travel s (cm).

        A pinion tooth at local angle psi + k*2pi/z contacts the upper rack at
        x = a + k*p, where a = r_pitch*(psi + pi/2). Meshing needs a tooth in
        the upper rack's space centres, x = x_a + s (mod p), so a = x_a + s.
        The lower rack is the SAME part turned over, so its space centres sit
        at -(x_a + s) (mod p); the pinion tooth half a turn away contacts it
        at -(a + (j - z/2)*p), which is congruent to -a. With z EVEN, j - z/2
        is an integer and the two conditions collapse to one. An odd tooth
        count would need two different angles and could not mesh both racks.
        """
        assert int(round(gv('gr_teeth'))) % 2 == 0, 'pinion tooth count must be even'
        return -math.pi / 2 + (x_a + s) / r_pitch

    def place_pinion(s):
        m = M3()
        m.setToRotation(phase_angle(s), VEC(0, 0, 1), ORG)
        flip = M3()
        flip.setToRotation(-math.pi / 2, VEC(1, 0, 0), ORG)
        m.transformBy(flip)
        t = m.translation
        t.y = -face / 2
        m.translation = t
        return m

    def place_rack(s, turned_over):
        m = M3()
        if turned_over:
            m.setToRotation(math.pi, VEC(0, 1, 0), ORG)
        t = m.translation
        t.x = -s if turned_over else s
        t.z = -offset if turned_over else offset
        m.translation = t
        return m

    turned = M3()
    turned.setToRotation(math.pi, VEC(0, 1, 0), ORG)

    def pose(s):
        """Fresh occurrences at this jaw position - each gets its transform at
        creation, so no Move feature is ever added. Returns a dict."""
        return {
            'pinion': root.occurrences.addExistingComponent(comp_pin, place_pinion(s)),
            'rackA': root.occurrences.addExistingComponent(comp_rack, place_rack(s, False)),
            'rackB': root.occurrences.addExistingComponent(comp_rack, place_rack(s, True)),
            'shellA': root.occurrences.addExistingComponent(comp_shell, M3()),
            'shellB': root.occurrences.addExistingComponent(comp_shell, turned),
        }

    mm = app.measureManager

    def body_of(occ):
        """The occurrence's body IN ASSEMBLY CONTEXT.

        `occurrence.bRepBodies.item(0)` looks like it gives this and does not
        when a component has several occurrences - it hands back something
        whose boundingBox collapses to a point, so every measured distance
        comes out 0.000. createForAssemblyContext is the documented way and
        the only one that survives multiple occurrences.
        """
        return occ.component.bRepBodies.item(0).createForAssemblyContext(occ)

    def gap(o1, o2):
        b1, b2 = body_of(o1), body_of(o2)
        for b in (b1, b2):
            bb = b.boundingBox
            assert bb.maxPoint.x - bb.minPoint.x > gv('gs_tol'), (
                'degenerate body: the timeline marker is not at the end, or the '
                'occurrence is hidden - measurements here would be fiction')
        return mm.measureMinimumDistance(b1, b2).value * 10

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
            pairs.append('%s^%s %.1f mm3' % (
                r.entityOne.component.name.replace('robotarm_gripper_', ''),
                r.entityTwo.component.name.replace('robotarm_gripper_', ''), vol))
        return total, pairs

    print('=== gripper fit check ===')
    print('centre distance %.2f mm | backlash %.2f mm | stroke %.1f mm/rack'
          % (offset * 10, gv('gr_backlash') * 10, stroke * 10))
    print('')
    print('contracted, per specs/robotarm/_assembly.md:')
    print('  jaw^jaw    0.000 at 0 mm opening (the faces MEET), then >= %.3f'
          % (arm_clear * 10))
    print('             - a jaw arm passes the OTHER rack on a free fit')
    print('  rack^shell >= %.3f - half the sliding fit, each side of the channel'
          % (slide / 2 * 10))
    print('  mesh       ~0 at every opening: a gear pair touches on one flank.')
    print('             Backlash shows as zero INTERFERENCE, not as a gap,')
    print('             which is why interference is the actual gate.')
    print('')
    header = ('%-9s %-8s %-10s %-10s %-10s %-11s %-11s %-9s'
              % ('opening', 'pinion', 'jaw^jaw', 'meshA', 'meshB',
                 'rackA^shlA', 'rackA^shlB', 'interf'))
    print(header)
    print('-' * len(header))

    worst, fails = 0.0, []
    for opening in OPENINGS_MM:
        s = opening / 2 / 10                     # cm of travel per rack
        p = pose(s)
        total, pairs = interference(list(p.values()))
        worst = max(worst, total)
        jj = gap(p['rackA'], p['rackB'])
        ra_sa = gap(p['rackA'], p['shellA'])
        ra_sb = gap(p['rackA'], p['shellB'])
        print('%-9.1f %-8.1f %-10.3f %-10.3f %-10.3f %-11.3f %-11.3f %-9.2f' % (
            opening, math.degrees(phase_angle(s)), jj,
            gap(p['rackA'], p['pinion']), gap(p['rackB'], p['pinion']),
            ra_sa, ra_sb, total))
        for line in pairs:
            print('      interference: ' + line)

        want_touch = opening < gv('gs_tol') * 10
        if want_touch:
            if jj > gv('gs_tol') * 10:
                fails.append('%.0f mm: jaws do not meet (%.3f)' % (opening, jj))
        elif jj < arm_clear * 10 - gv('gs_tol') * 10:
            fails.append('%.0f mm: jaw^jaw %.3f < %.3f' % (opening, jj, arm_clear * 10))
        if ra_sa < slide / 2 * 10 - gv('gs_tol') * 10:
            fails.append('%.0f mm: rack^shell %.3f < %.3f' % (opening, ra_sa, slide / 2 * 10))
        for o in p.values():
            o.deleteMe()

    # ---- leave the model in a readable pose ------------------------------
    final = pose(LEAVE_AT_MM / 2 / 10)
    solid = sum(body_of(o).physicalProperties.mass for o in final.values())
    bb = root.boundingBox
    print('')
    print('assembly bbox at %.0f mm open, mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f' % (
        LEAVE_AT_MM, bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('printed mass, solid PETG %.2f g -> ~%.1f g at 40%% infill + 4 walls'
          % (solid * 1000, solid * 1000 * 0.6))
    print('')
    print('GATE interference : worst %.3f mm3 - %s' % (
        worst, 'PASS' if worst < 1.0 else 'FAIL'))
    print('GATE clearances   : %s' % ('PASS' if not fails else 'FAIL - ' + '; '.join(fails)))

    # Hide the parked occurrences the part scripts left at the origin, so the
    # viewport shows only the assembled pose. Do this LAST: an invisible body
    # reports an EMPTY bounding box, and every measurement above depends on
    # the box being real.
    for occ in keepers.values():
        occ.isLightBulbOn = False
