"""robotarm/_check_elbow - the J3 gate.

WHY THIS FILE EXISTS AT ALL. lib/gears.py's own docstring has named
`_check_elbow.py` as a consumer of J3_PAIR since the reduction was written,
and until now there was no such file. The 2026-08-30 handoff recorded
`GATE j3_mesh: PASS - 0 of 420 flank points buried, control buries 102`.
That result was produced by a script that was never committed, so it could
not be re-run, and an ungated number in this project is a decoration. This
file makes the claim reproducible or it makes it fail.

It is the project's own recurring failure in its purest form: a datum in a
shared library which only one file reads is not a contract. J3_PAIR was read
by j3_gear.py and j3_pinion.py - the two parts CUT FROM it, which proves
nothing about whether they fit each other - and by nobody who measures the
result. B608ZZ.inner_race_od was read by j3_axle.py alone. Both are checked
here against the OTHER side of their interface.

WHAT IS MEASURED, AND HOW.

1. GATE j3_mesh. The two BUILT bodies, not the arithmetic - lib/gears.py
   already asserts its own maths at import and that is a different claim.
   The gear sits at the origin; the pinion sits at J3_PAIR.centre_distance
   along +X, spun half a tooth pitch so a SPACE faces the line of centres
   (the gear has a TOOTH there - tooth_polar draws tooth 1 on local +X and
   the circular pattern keeps it there). The pair is then rolled through one
   full gear tooth pitch. At each step every flank point of the three teeth
   in the mesh zone is mapped into the pinion's own frame and handed to
   pointContainment. INSIDE is interference. ON_ENTITY is contact and is
   what a working mesh is made of.

   NOT TemporaryBRepManager.booleanOperation. It returns an empty body here
   and reports success, so a zero volume reads as "no interference" and
   proves nothing. Two real bugs in this project hid behind exactly that.
   See fusion/PLAYBOOK.md.

2. THE POSITIVE CONTROL IS NOT OPTIONAL. The same sweep runs again with the
   pinion's half-pitch offset removed, so tooth meets tooth. That MUST bury
   a large number of points. If it buries none, the sampling is measuring
   nothing and the clean pass above is worthless - so the control failing
   fails the gate, exactly as a real interference would.

3. GATE j3_installs. CAN THE THING BE PUT TOGETHER. This is a different
   question from every other gate here and it is the one that has already
   cost this project a printed part: `shoulder_hub` as first printed passed
   every pose check and could not be installed at all, because the checks
   measured where things END UP and not the journey they take to get there.
   The wr_ contract retained it, the poses cleared, and a O24 flange could
   not physically reach its own seat.

   So this measures the JOURNEY. j3_gear seats by sliding along the elbow
   axis from outboard, so the gate walks the whole insertion path and, at
   each station, bisects for the largest radius about that axis which is
   clear of forearm material - the same method _check_shoulder uses for the
   drive hub. If the tightest aperture on the path is smaller than the gear,
   the gear does not go in, whatever the seated clearances say.

   The pinion's journey is arithmetic, not geometry, so it is checked as
   arithmetic: it threads onto the horn from outboard, which needs its own
   face width of run-up between the seat and the servo lobe.

4. GATE j3_contract. The numbers the elbow shares across files, each checked
   from the side that did NOT define it:
     - forearm's J3 centre distance == J3_PAIR.centre_distance
     - forearm's gear clearance clears r_tip of the 36T
     - fa_plate_t == jg_plate_t (the gear spans the plate it is journalled in)
     - the 608ZZ pocket in the forearm == B608ZZ od/width
     - the forearm's retaining shoulder bore is LARGER than the inner race,
       so the stationary side bears on the OUTER race
     - j3_axle's collar is SMALLER than the inner race, so the rotating side
       bears on the INNER race
   The last two are the same datum read from opposite ends. Get either
   backwards and the joint locks solid; j3_axle.py's docstring explains why,
   and nothing until now checked that the forearm agreed.

AN ABSENT PARAMETER IS A FAILURE, NOT A PASS. If robotarm_forearm is in the
document but its J3 parameters are not, that is the rework not having landed
and the gate says so. A check that silently does not run is the thing this
project keeps being bitten by.

RUN IT TWICE: REBUILD=True, then REBUILD=False. Three parts plus two sweeps
of containment is over the 60 s MCP call limit in one go, the same way
_check_shoulder and _check_pruner are. The loader sets it - `mod.REBUILD =
False` - so the pass that measures never touches the geometry it measures.
"""

import importlib.util
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ['forearm', 'j3_servo_cap', 'j3_gear', 'j3_pinion', 'j3_axle']

# One full gear tooth pitch, in steps. 5 steps x 3 teeth x 28 flank points
# = 420 samples, which is the population the handoff's claim was made over.
ROLL_STEPS = 5
MESH_TEETH = (-1, 0, 1)
FLANK_N = 14

# How much straight-line room a driver needs beyond a fastener head to turn
# it. ASSUMED: a 25 mm 1/4in bit with nothing behind it. A ball-end hex key
# wants more, a stubby bit slightly less. It is here as a named number rather
# than a shrug because "can this screw be turned" is a real constraint and
# nothing else in this project states it.
DRIVER_REACH_MM = 25.0
# ... and how fat it is. A 1/4in bit holder is 6.35 across; a bare hex key is
# 2.5. ASSUMED at the bit-holder end, because that is what most people reach
# for and it is the case that fails.
DRIVER_BIT_R_MM = 6.35 / 2.0

REBUILD = True


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters

    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    for _stale in [m for m in list(sys.modules)
                   if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[_stale]
    from lib.bearings import B608ZZ
    from lib.gears import J3_PAIR

    P = J3_PAIR
    B = B608ZZ

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
    gear = keepers['robotarm_j3_gear'].component.bRepBodies.item(0)
    pinion = keepers['robotarm_j3_pinion'].component.bRepBodies.item(0)

    # ---- both gears must be prisms over the SAME face, or the sample plane
    # ---- below is measuring one gear against thin air.
    # BOTH SETS OF TEETH ARE THE PRISM z 0 .. face, and only that. The gear
    # also carries a journal and a hex BELOW z 0 and the pinion a horn pocket
    # inside its own face, so the bodies' bounding boxes are NOT the tooth
    # band - checking the whole bbox would fail a perfectly good gear. What
    # has to be true is that the two tooth bands are coplanar and the same
    # depth, because the sample plane below sits at face/2 and would
    # otherwise be measuring one gear against thin air.
    fails = []
    for nm, bd in (('j3_gear', gear), ('j3_pinion', pinion)):
        bb = bd.boundingBox
        z0, z1 = bb.minPoint.z * 10, bb.maxPoint.z * 10
        if abs(z1 - P.face) > 0.05:
            fails.append('%s tops out at z %.3f, not the %.3f face width - the '
                         'two tooth bands are not coplanar and the sample '
                         'plane at z %.3f is not in both' % (nm, z1, P.face,
                                                             P.face / 2.0))
        if z0 > 0.05:
            fails.append('%s starts at z %.3f, above the tooth band base'
                         % (nm, z0))
        print('%-10s tooth band z 0.000 .. %.3f (body z %.3f .. %.3f)'
              % (nm, P.face, z0, z1))

    # ---- GATE j3_mesh -------------------------------------------------------
    P3 = adsk.core.Point3D.create
    INSIDE = adsk.fusion.PointContainment.PointInsidePointContainment
    ON = adsk.fusion.PointContainment.PointOnPointContainment

    C = P.centre_distance
    ratio = P.ratio
    phase0 = math.pi / P.z_pinion          # half a pinion tooth pitch
    z_mid = P.face / 2.0

    T = P.tooth_polar(P.z_gear, n=FLANK_N)
    flank = [(r, +a) for (r, a) in T['flank_pos']] + \
            [(r, -a) for (r, a) in T['flank_neg']]

    def sample(mis_phase):
        """Return (buried, total, worst_depth_mm) over one gear tooth pitch."""
        phase = 0.0 if mis_phase else phase0
        buried, total, worst = 0, 0, 0.0
        pitch = 2 * math.pi / P.z_gear
        for s in range(ROLL_STEPS):
            th = pitch * s / float(ROLL_STEPS)
            th_p = -th * ratio + phase
            ct, st = math.cos(th_p), math.sin(th_p)
            for k in MESH_TEETH:
                base = 2 * math.pi * k / P.z_gear
                for (r_mm, a) in flank:
                    ang = a + base + th
                    x = r_mm * math.cos(ang) - C
                    y = r_mm * math.sin(ang)
                    u = x * ct + y * st
                    v = -x * st + y * ct
                    total += 1
                    pc = pinion.pointContainment(P3(u / 10.0, v / 10.0,
                                                    z_mid / 10.0))
                    if pc == INSIDE:
                        buried += 1
                        d = P.r_root(P.z_pinion) - math.hypot(u, v)
                        if d > worst:
                            worst = d
        return buried, total, worst

    mesh_buried, mesh_total, mesh_worst = sample(False)
    ctl_buried, ctl_total, _ = sample(True)

    mesh_ok = (mesh_buried == 0)
    ctl_ok = (ctl_buried > 0)

    print('J3 pair: %dT/%dT module %.2f face %.2f, ratio %.4f, centre %.3f mm'
          % (P.z_pinion, P.z_gear, P.module, P.face, ratio, C))
    print('phasing: the gear carries a TOOTH on the line of centres, so the '
          'pinion is spun %.3f deg to face it with a SPACE'
          % math.degrees(phase0))
    print('rolled through one gear tooth pitch (%.3f deg) in %d steps, '
          'sampling %d flank points of %d teeth per step'
          % (360.0 / P.z_gear, ROLL_STEPS, len(flank), len(MESH_TEETH)))
    print('')
    print('GATE j3_mesh      : %d of %d flank points buried in the pinion - %s'
          % (mesh_buried, mesh_total, 'PASS' if mesh_ok else 'FAIL'))
    if mesh_buried:
        print('   worst penetration %.3f mm past the pinion root circle' % mesh_worst)
    print('   CONTROL (half-pitch mis-phase, tooth onto tooth): %d of %d '
          'buried - %s' % (ctl_buried, ctl_total,
                           'the test can see' if ctl_ok else
                           'THE TEST SEES NOTHING, the pass above is worthless'))
    if not ctl_ok:
        fails.append('the positive control buried 0 points - pointContainment '
                     'is not registering interference, so GATE j3_mesh proves '
                     'nothing whether it passes or not')

    def gv(name):
        p = ups.itemByName(name)
        return None if p is None else p.value * 10.0   # val() is CENTIMETRES

    def gv_mm(name):
        v = gv(name)
        assert v is not None, 'missing user parameter ' + name
        return v

    # ---- GATE j3_installs ---------------------------------------------------
    # THE PROCEDURE THIS MEASURES, in order, with the cap OFF:
    #   1. j3_gear slides in along the elbow axis, through the plate bore
    #   2. the M3 goes down that axis and is TIGHTENED - a driver has to fit
    #   3. servo + pinion + j3_servo_cap arrive as one unit along the PINION
    #      axis, phased into mesh
    # Each step is an aperture measured on the real forearm body, and each has
    # a control that must find material. All three failed before the pad was
    # split off; see _HANDOFF.md section 10.
    fa = keepers.get('robotarm_forearm')
    install_fails = []
    if fa is None:
        install_fails.append('robotarm_forearm is not in the document, so no '
                             'insertion path could be walked at all')
    else:
        fa_body = fa.component.bRepBodies.item(0)
        OUTSIDE = adsk.fusion.PointContainment.PointOutsidePointContainment
        L2 = gv_mm('fa_l2')
        plate_in, plate_out = gv_mm('fa_plate_in'), gv_mm('fa_plate_out')
        standoff = gv_mm('fa_j3_standoff')
        free = gv_mm('fa_free')
        y_pin = -L2 + gv_mm('fa_j3_centre')

        def first_material_r(x_mm, axis_y, cap=40.0, step=0.25):
            """Radius of the FIRST forearm material going out from an axis.

            NOT A BISECTION, and the first version of this was one - it read
            r 31.22 of free space in the middle of a solid fork plate and the
            control caught it. Bisection needs "clear at R implies clear at
            every smaller R", and about these axes the forearm is an ANNULUS:
            open bore inside, plate material, free air outside the silhouette.
            A disc of radius R passes only if EVERY radius under R is clear,
            so this scans outward and stops at the first hit.
            """
            r = 0.0
            while r <= cap:
                for k in range(48):
                    a = 2 * math.pi * k / 48
                    pt = P3(x_mm / 10.0,
                            (axis_y + r * math.cos(a)) / 10.0,
                            (r * math.sin(a)) / 10.0)
                    if fa_body.pointContainment(pt) != OUTSIDE:
                        return r
                r += step
            return cap

        def walk(x_from, x_to, axis_y, step=0.75):
            worst, at, x = 99.0, None, x_from
            while x <= x_to + 1e-9:
                r = first_material_r(x, axis_y)
                if r < worst:
                    worst, at = r, x
                x += step
            return worst, at

        # -- 1. the gear, along the elbow axis --------------------------------
        r_gear = P.r_tip(P.z_gear)
        g_from, g_to = -(plate_out + standoff) - 6.0, -plate_out - 0.25
        ap_g, at_g = walk(g_from, g_to, -L2)
        print('')
        print('1. j3_gear along the elbow axis, x %.2f -> %.2f (cap off):'
              % (g_from, g_to))
        print('   tightest aperture r %.2f at x %.2f; the 36T is r %.2f'
              % (ap_g, at_g, r_gear))
        if ap_g < r_gear - 1e-6:
            install_fails.append(
                'the 36T gear is r %.2f and the tightest aperture on its path '
                'is r %.2f at x %.2f - %.2f mm too big to reach its seat'
                % (r_gear, ap_g, at_g, r_gear - ap_g))

        # -- 2. a driver on the M3, along the same axis -----------------------
        mouth = -(plate_out + free + P.face)
        d_from, d_to = mouth - DRIVER_REACH_MM, mouth - 0.25
        ap_d, at_d = walk(d_from, d_to, -L2)
        print('2. an M3 driver on the same axis, from the counterbore mouth at '
              'x %.2f out %.1f:' % (mouth, DRIVER_REACH_MM))
        print('   tightest aperture r %.2f at x %.2f; a bit needs about r %.1f'
              % (ap_d, at_d, DRIVER_BIT_R_MM))
        if ap_d < DRIVER_BIT_R_MM - 1e-6:
            install_fails.append(
                'an M3 driver needs r %.1f for %.1f mm out of the counterbore '
                'and the forearm closes to r %.2f at x %.2f - the retention '
                'bolt cannot be turned'
                % (DRIVER_BIT_R_MM, DRIVER_REACH_MM, ap_d, at_d))

        # -- 3. servo + pinion + cap, along the PINION axis -------------------
        r_pin = P.r_tip(P.z_pinion)
        p_from, p_to = -(plate_out + standoff) - 6.0, -(plate_out + free) - 0.25
        ap_p, at_p = walk(p_from, p_to, y_pin)
        print('3. servo + pinion + cap along the pinion axis (y %.2f), '
              'x %.2f -> %.2f:' % (y_pin, p_from, p_to))
        print('   tightest aperture r %.2f at x %.2f; the 18T is r %.2f'
              % (ap_p, at_p, r_pin))
        if ap_p < r_pin - 1e-6:
            install_fails.append(
                'the 18T pinion is r %.2f and the tightest aperture on its '
                'path is r %.2f at x %.2f' % (r_pin, ap_p, at_p))

        # -- THE CONTROL. Every aperture above is a "nothing found" reading,
        # and a probe that can never find anything would report exactly the
        # same. Push it into the fork plate, which is solid.
        ctl_x = -(plate_in + plate_out) / 2.0
        ctl = first_material_r(ctl_x, -L2)
        print('   CONTROL, the same probe inside the fork plate at x %.2f: '
              'first material at r %.2f - %s'
              % (ctl_x, ctl, 'the probe can see' if ctl < r_gear else
                 'THE PROBE SEES NOTHING, every reading above is worthless'))
        if ctl >= r_gear:
            install_fails.append(
                'the aperture probe found r %.2f of free space inside the fork '
                'plate, which is solid - it is measuring nothing' % ctl)

        # -- and the cap must actually BE a separate part, or none of the
        # above describes the arm that gets built.
        if 'robotarm_j3_servo_cap' not in keepers:
            install_fails.append(
                'robotarm_j3_servo_cap is not in this document. Every clearance '
                'above exists BECAUSE the servo pad lifts off; measured with a '
                'pad in place all three of these failed')

    print('')
    print('GATE j3_installs   : %s' % ('PASS' if not install_fails else 'FAIL'))
    for f in install_fails:
        print('   %s' % f)
    fails.extend(install_fails)

    # ---- GATE j3_contract ---------------------------------------------------
    checked, absent, contract_fails = [], [], []

    def agree(name, want, why, tol=1e-6):
        got = gv(name)
        if got is None:
            absent.append(name)
            return
        checked.append(name)
        if abs(got - want) > tol:
            contract_fails.append('%s is %.4f and %s wants %.4f - %s'
                         % (name, got, why, want, why))

    def at_least(name, floor, why):
        got = gv(name)
        if got is None:
            absent.append(name)
            return
        checked.append(name)
        if got < floor - 1e-6:
            contract_fails.append('%s is %.4f, under the %.4f it needs - %s'
                         % (name, got, floor, why))

    forearm_here = 'robotarm_forearm' in keepers

    agree('fa_j3_centre', C, 'lib/gears.py J3_PAIR.centre_distance')
    at_least('fa_j3_gear_clear', P.r_tip(P.z_gear),
             'the 36T tip circle has to turn inside it')
    agree('fa_brg_od', B.od, 'lib/bearings.py B608ZZ.od')
    agree('fa_brg_w', B.width, 'lib/bearings.py B608ZZ.width')

    jg_plate = gv('jg_plate_t')
    fa_plate = gv('fa_plate_t')
    if jg_plate is not None and fa_plate is not None:
        checked.append('fa_plate_t == jg_plate_t')
        if abs(jg_plate - fa_plate) > 1e-6:
            contract_fails.append('jg_plate_t %.3f disagrees with fa_plate_t %.3f - the '
                         'gear would either bind on the plate or float'
                         % (jg_plate, fa_plate))
    elif fa_plate is None:
        absent.append('fa_plate_t')

    # THE RACE DATUM, READ FROM BOTH ENDS. Same number, opposite senses.
    shoulder = gv('fa_brg_bore')
    if shoulder is None:
        absent.append('fa_brg_bore')
    else:
        checked.append('fa_brg_bore')
        if shoulder <= B.inner_race_od:
            contract_fails.append('the forearm retaining shoulder bore is %.2f and the '
                         '608 inner race reaches %.2f - the STATIONARY plate '
                         'would bear on the INNER race and lock the joint'
                         % (shoulder, B.inner_race_od))
        if shoulder >= B.od:
            contract_fails.append('the forearm retaining shoulder bore is %.2f, at or '
                         'over the %.2f bearing OD - it retains nothing'
                         % (shoulder, B.od))
    collar = gv('ja_collar_d')
    if collar is None:
        absent.append('ja_collar_d')
    else:
        checked.append('ja_collar_d')
        if collar >= B.inner_race_od:
            contract_fails.append('j3_axle\'s thrust collar is %.2f and the 608 inner '
                         'race ends at %.2f - the ROTATING axle would bear on '
                         'the OUTER race and lock the joint'
                         % (collar, B.inner_race_od))

    # The gear disc is the flange: it must not pass the bore it journals in.
    bore = gv('fa_bore_d')
    if bore is None:
        absent.append('fa_bore_d')
    else:
        checked.append('fa_bore_d')
        if P.r_tip(P.z_gear) * 2 <= bore:
            contract_fails.append('the 36T gear is %.2f across and the plate bore is '
                         '%.2f - it would fall through'
                         % (P.r_tip(P.z_gear) * 2, bore))

    contract_ok = not absent and not contract_fails
    print('')
    print('GATE j3_contract  : %d terms checked, %d absent, %d disagree - %s'
          % (len(checked), len(absent), len(contract_fails),
             'PASS' if contract_ok else 'FAIL'))
    if checked:
        print('   checked: %s' % ', '.join(sorted(checked)))
    if absent:
        print('   ABSENT (not a pass - the check did not run): %s'
              % ', '.join(sorted(absent)))
        if forearm_here:
            contract_fails.append('robotarm_forearm is in the document but %d of the J3 '
                         'contract parameters do not exist - the forearm rework '
                         'has not landed and these terms are unchecked'
                         % len(absent))
        else:
            print('   robotarm_forearm is not in this document, so the fa_* '
                  'terms could not be read. Build it and re-run.')

    print('')
    print('608ZZ: bore %.1f od %.1f width %.1f, inner race reaches %.1f'
          % (B.bore, B.od, B.width, B.inner_race_od))
    print('       stationary side (forearm shoulder) must bear OUTSIDE %.1f'
          % B.inner_race_od)
    print('       rotating side  (j3_axle collar)   must bear INSIDE  %.1f'
          % B.inner_race_od)
    fails.extend(contract_fails)
    print('')
    print('ELBOW: j3_mesh %s, j3_contract %s'
          % ('PASS' if mesh_ok and ctl_ok else 'FAIL',
             'PASS' if contract_ok else 'FAIL'))
    for f in fails:
        print('   FAIL %s' % f)
    assert not fails, 'the elbow gate failed - see above'
