"""robotarm/_j1_roller_options - pricing the three ways past the J1 roller fault.

_check_j1 found that the three 608ZZ foul turntable_stator's own base plate by
218 mm3 each and cannot be fitted: tt_axle_z 12.0 with a 22.0 OD puts the
roller's lowest point at z 1.00, and the plate is solid from z 0 to
ts_plate_t 4.00 at the roller azimuths. This does not fix it. It builds each
candidate, measures it, and prints what each one actually costs, so the choice
is made on numbers rather than on which one sounds cheapest.

  A  POCKET      floor the plate under each roller, keep tt_race_z
     (and note gdeg() below: writing this file turned up a sixth instance
      of the units bug, in a flavour the PLAYBOOK does not yet name.)
  B  RAISE       lift tt_axle_z until the bearing clears a full 4.0 plate
  C  WINDOW      cut the roller through the plate at its own azimuth

A and C are built. B is arithmetic on purpose - it re-datums the rotor, the
ring and sb_stand_h, so building it means rebuilding the joint, and the number
that decides whether it is worth doing is available without any of that.

THE FOOTPRINT, and it is the same for A and C. The roller spans
tt_roller_r +- tt_roller_w/2 radially and +- tt_roller_od/2 tangentially, so
at r 27 it subtends asin(11/27) = 24.0 deg. The relief has to contain that and
stop short of the cheek footing at cheek_ir, or the cheeks stand on air.

Read-only with respect to the repo: this builds turntable_stator from its
committed script and cuts SCRATCH bodies on copies. It never edits the part.
"""

import importlib.util
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
ROLL_AZ = (90.0, 210.0, 330.0)
WIN_AZ = (30.0, 150.0, 270.0)
RELIEF_CLEAR_MM = 0.5     # daylight under the bearing, not a fit
ROLLER_BORE_MM = 8.0      # 608ZZ bore - lib/bearings.py


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters

    path = os.path.join(REPO, 'models', 'robotarm', 'turntable_stator.py')
    spec = importlib.util.spec_from_file_location('gen_stator', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run(_context)
    print('')

    def gv(name):
        """MILLIMETRES, converted once. LENGTH parameters only."""
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        assert p.unit not in ('deg', 'rad'), (
            '%s is an angle - use gdeg(), not gv()' % name)
        return p.value * 10.0

    def gdeg(name):
        """DEGREES. A sixth flavour of the units bug, found writing this file:
        val() returns Fusion's internal unit, and for an ANGLE that is RADIANS,
        not centimetres. ts_window_deg came back as 0.87, the x10 made it 8.7,
        and the half-angle printed as 0.4 deg instead of 25.0 - which reported
        the ligament between the windows as 14.6 mm when it is 4.5. It threw
        no error and the number looked plausible. PLAYBOOK, 'Units in
        ASSERTIONS'."""
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        assert p.unit in ('deg', 'rad'), '%s is not an angle' % name
        return math.degrees(p.value)

    plate_t = gv('ts_plate_t')
    plate_ir = gv('ts_plate_ir')
    plate_or = gv('ts_plate_or')
    axle_z = gv('tt_axle_z')
    od = gv('tt_roller_od')
    rw = gv('tt_roller_w')
    rr = gv('tt_roller_r')
    collar_h = gv('tt_collar_h')
    cheek_ir = rr + rw / 2 + collar_h
    win_ir = gv('ts_window_ir')
    win_or = gv('ts_window_or')
    win_half = gdeg('ts_window_deg') / 2.0
    hub_x = gv('ts_hub_x')
    hub_y = gv('ts_hub_y')
    soff = gv('ts_shaft_off')
    min_wall = 1.6                             # design_rules MIN_WALL_MM

    roll_bottom = axle_z - od / 2
    bite = plate_t - roll_bottom
    foot_ir = rr - rw / 2
    foot_or = cheek_ir
    foot_half = math.degrees(math.asin((od / 2) / rr))

    print('=== the fault, in numbers ===')
    print('roller bottom z %.2f (tt_axle_z %.2f - OD/2 %.2f)'
          % (roll_bottom, axle_z, od / 2))
    print('plate         z 0.00 .. %.2f, solid r %.1f .. %.1f'
          % (plate_t, plate_ir, plate_or))
    print('THE BITE: %.2f mm of plate stands in the bearing.' % bite)
    print('footprint to clear: r %.2f..%.2f, +-%.1f deg at each of az %s'
          % (foot_ir, foot_or, foot_half,
             '/'.join('%.0f' % a for a in ROLL_AZ)))
    print('')

    # ---- A: POCKET ---------------------------------------------------------
    floor = roll_bottom - RELIEF_CLEAR_MM
    print('=== A  POCKET - floor the plate under each roller ===')
    print('the pocket floor has to sit %.2f under the bearing, at z %.2f,'
          % (RELIEF_CLEAR_MM, floor))
    print('which leaves %.2f mm of plate.' % floor)
    if floor < min_wall:
        print('THAT IS UNDER MIN_WALL %.2f. A is NOT VIABLE at tt_axle_z %.2f:'
              % (min_wall, axle_z))
        print('  a 4.00 plate cannot be relieved %.2f and still be a wall.'
              % (bite + RELIEF_CLEAR_MM))
        print('  It becomes viable only above tt_axle_z %.2f, which is B.'
              % (od / 2 + RELIEF_CLEAR_MM + min_wall))
    else:
        print('clears MIN_WALL %.2f with %.2f to spare.' % (min_wall, floor - min_wall))
    print('')

    # ---- B: RAISE ----------------------------------------------------------
    axle_b = plate_t + RELIEF_CLEAR_MM + od / 2
    print('=== B  RAISE tt_axle_z until a full plate clears ===')
    print('tt_axle_z %.2f -> %.2f  (plate %.2f + %.2f daylight + OD/2 %.2f)'
          % (axle_z, axle_b, plate_t, RELIEF_CLEAR_MM, od / 2))
    print('tt_race_z %.2f -> %.2f, so the WHOLE ROTOR rises %.2f mm.'
          % (axle_z + od / 2, axle_b + od / 2, axle_b - axle_z))
    print('re-datums: tt_race_z, the ring z, sb_stand_h\'s two bounds, the')
    print('  cheek and post heights, and J2\'s down-pitch limit. Plate untouched.')
    print('')

    # ---- C: WINDOW ---------------------------------------------------------
    print('=== C  WINDOW - cut the roller through the plate ===')
    gap_deg = min(abs(((r - w + 180) % 360) - 180) for r in ROLL_AZ for w in WIN_AZ)
    lig_in = math.radians(gap_deg - foot_half - win_half) * foot_ir
    lig_out = math.radians(gap_deg - foot_half - win_half) * min(foot_or, win_or)
    print('roller windows at az %s, +-%.1f deg, r %.2f..%.2f'
          % ('/'.join('%.0f' % a for a in ROLL_AZ), foot_half, foot_ir, foot_or))
    print('existing lightening windows at az %s, +-%.1f deg, r %.2f..%.2f'
          % ('/'.join('%.0f' % a for a in WIN_AZ), win_half, win_ir, win_or))
    print('centres are %.0f deg apart; edge to edge that is %.1f deg'
          % (gap_deg, gap_deg - foot_half - win_half))
    print('LIGAMENT between them: %.2f mm at r %.1f, %.2f mm at r %.1f'
          % (lig_in, foot_ir, lig_out, min(foot_or, win_or)))
    if min(lig_in, lig_out) < min_wall:
        print('  UNDER MIN_WALL %.2f - the spokes are too thin.' % min_wall)
    else:
        print('  clears MIN_WALL %.2f.' % min_wall)
    pad_r = math.hypot(hub_x, hub_y + soff)
    print('servo pad corner reaches r %.2f; the roller window starts at r %.2f'
          % (pad_r, foot_ir))
    if pad_r > foot_ir:
        print('  THE PAD OVERLAPS THE WINDOW by %.2f mm of radius - the az-90'
              % (pad_r - foot_ir))
        print('  window would undercut the servo pad, which is the SECOND fault')
        print('  _check_j1 found. C has to solve both or neither.')
    print('')

    # cut it and weigh it
    comp = None
    for occ in root.occurrences:
        if occ.component.name == 'robotarm_turntable_stator':
            comp = occ.component
    assert comp is not None, 'turntable_stator did not build'
    body = comp.bRepBodies.item(0)
    before = body.volume * 1000
    P3 = adsk.core.Point3D.create
    V = adsk.core.ValueInput.createByString
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
    for i, az in enumerate(ROLL_AZ):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_optC_window_%d' % i
        a = math.radians(az)
        h = math.radians(foot_half)
        arcs, lines = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines

        def p(r, ang):
            return sk.modelToSketchSpace(
                P3(r * math.cos(ang) / 10.0, r * math.sin(ang) / 10.0, 0))

        arcs.addByThreePoints(p(foot_or, a - h), p(foot_or, a), p(foot_or, a + h))
        arcs.addByThreePoints(p(foot_ir, a - h), p(foot_ir, a), p(foot_ir, a + h))
        lines.addByTwoPoints(p(foot_ir, a - h), p(foot_or, a - h))
        lines.addByTwoPoints(p(foot_ir, a + h), p(foot_or, a + h))
        assert sk.profiles.count == 1, 'optC window %d: %d profiles' % (
            i, sk.profiles.count)
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = comp.features.extrudeFeatures.createInput(col, CUT)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('-1.0 mm'))
        inp.setDistanceExtent(False, V('%.4f mm' % (plate_t + 2.0)))
        inp.participantBodies = [body]
        comp.features.extrudeFeatures.add(inp).name = 'optC_window_%d' % i
    after = body.volume * 1000
    # PLAYBOOK: when a CUT changes nothing, the cut is in the wrong place.
    assert before - after > 1.0, (
        'the three roller windows removed %.3f mm3 - the cut is in the wrong '
        'place or at the wrong scale' % (before - after))
    print('C built: stator %.0f -> %.0f mm3, %.0f mm3 removed, %.1f g lighter '
          'in PETG' % (before, after, before - after,
                       (before - after) * 1.27 * 0.65 / 1000))
    print('bodies %d | valid %s' % (comp.bRepBodies.count, body.isValid))
    print('')
    print('VERDICT: A is arithmetically dead at the current tt_axle_z. The real')
    print('choice is B (move the datum, keep the plate) against C (keep the')
    print('datum, spoke the plate) - and C still owes an answer on the servo pad.')
