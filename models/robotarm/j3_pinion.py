"""robotarm/j3_pinion - Fusion MCP generating script.

Rebuilds `robotarm_j3_pinion` (idempotent). Spec: lib/gears.py J3_PAIR.

THE 18T INPUT HALF OF THE ELBOW REDUCTION, bored straight onto the J3
servo's own spline. j3_gear.py is the other half and both trace the SAME
involute out of lib/gears.py - see that file's tooth_polar().

WHICH SERVO IS NOT THIS FILE'S TO SAY. lib/joints.JOINT_SERVO holds it for
the whole arm; J3 is an SG90 as of 2026-09-03 and was an MG90S before.

18 TEETH IS THE FLOOR, NOT A ROUND NUMBER. z_min = 2/sin^2(20 deg) = 17.1,
so 17 undercuts and 18 does not. gripper_pinion gets away with 12 because a
rack has no tip circle to interfere with; this pair has two involutes and no
such licence. lib/gears.py asserts it rather than trusting this comment.

NO HORN. THE PINION BORES ONTO THE SPLINE. Jonathan, 2026-08-31: "we should
not [mount] at the horns but rather add gears that we make". The horn was
stamped plastic that varies by batch (deshipu, Roger Cheng), that GATE
servo_fit measured fouling shoulder_bracket by 67.5 mm3, and that the bench
reported three times would not enter anything cut for it. It is now out of
the load path entirely.

THE SPLINE IS NOT PRINTED, and that is a rule rather than a preference. 20
teeth on a Oe5.0 circle is 0.79 mm of pitch and roughly 0.24 mm of tooth;
design_rules.MIN_FEATURE_MM is 0.8, CALIBRATED on this printer. A "splined"
printed bore would come out a slightly lumpy circle. So the bore is ROUND and
cut UNDERSIZE, and the steel spline broaches its own form into the PETG on
first assembly - one diameter to get right instead of twenty teeth. The
interference is ASSUMED until a gauge settles it.

TWO DIAMETERS, because the spline sits ABOVE the boss: the lower bore clears
the output collar, the upper bore grips the spline. A gear thinner than the
boss height cannot drive a servo directly at all.

THE ENGAGEMENT HALVED WITH THE SERVO AND IT IS THE ONE NUMBER TO ARGUE
ABOUT. MG90S: Oe6.0 collar, then 4.00 mm of Oe5.0 spline. SG90: Oe5.0
collar, then 2.50 mm of Oe4.9 - and 2.50 is ALL an SG90 has, so the bore
grips the whole of it and a thicker pinion cannot buy more.

Priced, because this pinion drives the entire arm outboard of the elbow
through a 2:1: the spline sees the SERVO's torque, not the joint's, and the
SG90 stalls 20 % LOWER. Shear on the broached cylinder goes 1.38 -> 1.85 MPa
against a 5.25 MPa allowable that already carries a safety factor of 4 -
35 % utilised, and the length the torque actually needs is 0.88 mm. What
binds is the 2.00 mm FORMING floor, which 2.50 clears by 25 %. The exposure
is not stress, it is that spline_h 2.50 is DATASHEET for a cheap servo and
lib/servo.py rates that grade weak: caliper it before printing.
lib/gears.py J3_ENGAGE_FLOOR_MM carries the arithmetic.

WHAT IT COSTS: nothing. The three interfaces priced -
    pressed on the horn   gear plane  5.90   varies by batch, does not fit
    bolted horn adapter   gear plane 18.50   +12.60 mm of forearm width
    ON THE SPLINE         gear plane  5.90   +0.00, and no horn at all
J3_PAIR is unchanged by BOTH migrations - m1.00 18T/36T, centre 27.20, gear
Oe38.0. The horn going was free because the Oe6.40 boss bore set the root
floor at 4.80 against a 7.75 root. The SG90 is freer still: its smaller boss
gives a Oe5.40 bore and a 4.30 floor, so the pinion clears by 3.45 instead of
2.95. And forearm.py needs no rework either time - the seat rises 5.90 ->
7.10 but fa_lobe_t rises by the same 1.20, so fa_j3_standoff stays 10.80.

A WASHER IS REQUIRED under the servo's retaining screw. The screw head is
near Oe5 and the broach bore is Oe4.75, so the head lands almost entirely
over the hole. Without a washer the pinion walks up the spline.

Print orientation: TOOTH FACE ON THE BED, bore vertical. Same as
gripper_pinion, same face width, so one test print settles both. The bore is
now through, so it prints as a clean vertical hole with no bridged floor.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core
import adsk.fusion

from lib.design_rules import MIN_WALL_MM  # noqa: E402
from lib.gears import J3_ENGAGE_FLOOR_MM, J3_HUB, J3_PAIR  # noqa: E402
from lib.joints import servo_for as _servo_for  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_j3_pinion'
BODY_NAME = 'j3_pinion'
PREFIX = 'jp_'
WRIST = 'wr_'
STYLE = 'sty_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('j3_pinion')
PH_TEETH = 'gear teeth'
PH_STEM = 'spline hub'
# THE J3 SERVO, from the arm's one mapping. `_SERVOS['MG90S']` used to be
# typed here; it is lib/joints.JOINT_SERVO's answer now, which is an SG90
# since 2026-09-03 and was an MG90S before it.
_SERVO = _servo_for('J3')
# Geometric comparison epsilons and sample counts, not dimensions.
TOL = 1e-6
TOOTH_SAMPLES = 14      # involute points per flank
TIP_TOL = 0.05         # mm the traced tip may miss the computed tip circle
PH_FINISH = 'finish'
PHASES = [PH_TEETH, PH_STEM, PH_FINISH]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def wrist(name, expr, comment='', units='mm'):
        _set(WRIST + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    # --- shared J4/J3 clevis contract, defined identically elsewhere -------
    wrist('pivot_af', '16.0 mm', 'hex socket across flats - SHARED')
    wrist('hub_d', '20.0 mm', 'journal collar diameter - SHARED')
    wrist('reach', '3.8 mm', 'hex boss length = 0.4 running gap + 3.4 socket - SHARED')
    _set(STYLE + 'ef', '0.4 mm', 'elephant-foot chamfer, functional faces', 'mm')

    # --- the pair, from lib/gears.py. WRITTEN, NOT CHOSEN. -----------------
    P = J3_PAIR
    param('module', '%.4f mm' % P.module, 'lib/gears.py J3_PAIR - do not edit here')
    param('teeth', '%d' % P.z_pinion, 'lib/gears.py J3_PAIR', '')
    param('face', '%.4f mm' % P.face, 'lib/gears.py J3_PAIR')
    param('r_tip', '%.5f mm' % P.r_tip(P.z_pinion), 'derived in lib/gears.py')
    param('r_root', '%.5f mm' % P.r_root(P.z_pinion), 'derived in lib/gears.py')
    param('centre', '%.5f mm' % P.centre_distance,
          'centre distance to the J3 servo shaft - forearm.py reads the SAME\n'
          '           number out of lib/gears.py to place the lobe')

    # --- SPLINE HUB, from lib/gears.py J3_HUB. WRITTEN, NOT CHOSEN. ------
    # THE HORN IS GONE. This pinion bores straight onto the MG90S's own
    # output spline. The horn was stamped plastic that varies by batch, that
    # GATE servo_fit measured fouling the shoulder bracket by 67.5 mm3, and
    # that Jonathan reported three times would not enter anything cut for it.
    # Nothing in this part refers to it any more.
    H = J3_HUB
    param('seat_z', '%.4f mm' % H.seat_z,
          'servo-z of THIS face - how far up the MG90S the pinion sits.\n'
          '           lib/gears.py J3_HUB. forearm.py reads the SAME number to place\n'
          '           the servo lobe, and dropping the horn leaves it UNCHANGED at\n'
          '           5.90 - which is why the forearm needs no rework at all.')
    param('boss_bore_d', '%.4f mm' % H.boss_clear_d,
          'lower bore - CLEARS the Oe6.0 output collar at a free fit. Nothing\n'
          '           grips the boss; it only has to pass.')
    param('boss_bore_h', '%.4f mm' % H.boss_clear_to,
          'how far up the bore stays wide - to the top of the boss')
    param('broach_d', '%.4f mm' % H.broach_d,
          'upper bore - THE STEEL SPLINE CUTS THIS. Deliberately UNDERSIZE by\n'
          '           lib/servo.SPLINE_BROACH_INTERFERENCE_MM. The spline is not\n'
          '           printed: 20 teeth on Oe5.0 is 0.79 mm of pitch and ~0.24 mm of\n'
          '           tooth, against a CALIBRATED MIN_FEATURE_MM of 0.8. The\n'
          '           interference is ASSUMED - gauge it before trusting a gear to it.')
    param('boss_bore_from', '%.4f mm' % H.broach_from, 'derived: the spline starts here')
    param('broach_to', '%.4f mm' % H.broach_to, 'derived: and ends here')
    param('engaged', '%.4f mm' % H.engaged, 'how much spline the bore grips')
    param('washer_d', '%.4f mm' % H.washer_d,
          'SMALLEST WASHER THAT WORKS, and it is not optional. The retaining\n'
          '           screw is Oe%.1f with a head near Oe5 and the broach bore is Oe%.2f,\n'
          '           so the head would sit over the hole with nothing to clamp.\n'
          '           Without a washer the pinion walks up the spline.'
          % (H.screw_d, H.broach_d))

    param('lead_in', '0.5 mm', 'insertion lead-in chamfer')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE -------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        # SKIP THE ROOT. Once this part lives in its own saved file the root
        # component carries the DOCUMENT's name, which is COMPONENT - and a
        # root component cannot be renamed, so the rename below raised
        # "3 : root component name cannot be changed" and no part rebuilt.
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
    assert comp.name == COMPONENT, 'a stale component still holds the name'
    ext = comp.features.extrudeFeatures
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                sk.name + ': expected ' + str(expected) + ', got ' + str(sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm, z_cm=0.0):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def polar(sk, r_cm, ang):
        return mpt(sk, r_cm * math.cos(ang), r_cm * math.sin(ang))

    def disc(name, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    # ---- phase 1: blank + one involute tooth + circular pattern ----------
    t0 = design.timeline.count
    disc('blank', val('r_root') * 2, '0.0 mm', PREFIX + 'face', NEW)

    T = P.tooth_polar(P.z_pinion, n=TOOTH_SAMPLES, sink=val('tooth_sink') * 10)
    sk_t = sketch(comp.xYConstructionPlane, 'sk_tooth_profile')
    lines = sk_t.sketchCurves.sketchLines
    r_sink = T['r_sink'] / 10.0
    for key, sign in (('flank_pos', +1), ('flank_neg', -1)):
        pts = adsk.core.ObjectCollection.create()
        for (r_mm, a) in T[key]:
            pts.add(polar(sk_t, r_mm / 10.0, a))
        sk_t.sketchCurves.sketchFittedSplines.add(pts)
        lines.addByTwoPoints(polar(sk_t, r_sink, sign * T['ang_base']),
                             polar(sk_t, T['r_base'] / 10.0, sign * T['ang_base']))
    lines.addByTwoPoints(polar(sk_t, r_sink, T['ang_base']),
                         polar(sk_t, r_sink, -T['ang_base']))
    sk_t.sketchCurves.sketchArcs.addByCenterStartSweep(
        mpt(sk_t, 0, 0), polar(sk_t, T['r_tip'] / 10.0, T['ang_tip']),
        -2 * T['ang_tip'])
    tooth = extrude(profiles(sk_t, expected=1), JOIN, '0.0 mm', PREFIX + 'face', 'tooth')

    pat_in = adsk.core.ObjectCollection.create()
    pat_in.add(tooth)
    cp = comp.features.circularPatternFeatures.createInput(
        pat_in, comp.zConstructionAxis)
    cp.quantity = adsk.core.ValueInput.createByReal(P.z_pinion)
    cp.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    cp.isSymmetric = False
    comp.features.circularPatternFeatures.add(cp).name = 'tooth_ring'
    group(t0, PH_TEETH)

    # ---- phase 2: horn interface ------------------------------------------
    t1 = design.timeline.count
    # ONE through bore. It was three cuts - a blind hub relief, a blind arm
    # slot and a separate driver access bore - and the driver bore already
    # went all the way through, so the blind hub pocket was never doing
    # anything a through bore would not.
    # TWO DIAMETERS, because the spline sits ABOVE the boss. The lower part
    # of the bore lets the Oe6.0 collar through; only the upper part meets
    # the Oe5.0 spline. That is also why a thin gear cannot drive a servo
    # directly however good the bore is - it has to reach past the boss
    # before it grips anything.
    disc('boss_bore', val('boss_bore_d'), '0.0 mm', PREFIX + 'boss_bore_h', CUT)
    disc('spline_bore', val('broach_d'), PREFIX + 'boss_bore_h',
         PREFIX + 'face - ' + PREFIX + 'boss_bore_h', CUT)
    group(t1, PH_STEM)

    # ---- phase 3: finish --------------------------------------------------
    t2 = design.timeline.count

    def edges_in_plane_z(z_pick):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.z - z_pick) < val('tol')
                    and abs(eb.maxPoint.z - z_pick) < val('tol')):
                col.add(e)
        return col

    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_z(val('face')), V(PREFIX + 'lead_in'), False)
    chf.add(c_inp).name = 'driver_lead_in'
    group(t2, PH_FINISH)

    # ---- identity + diagnostics ------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got %d' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used = a.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    # ---- the checks -------------------------------------------------------
    bb = body.boundingBox
    r_out = max(abs(bb.minPoint.x), abs(bb.maxPoint.x),
                abs(bb.minPoint.y), abs(bb.maxPoint.y)) * 10
    assert abs(r_out - P.r_tip(P.z_pinion)) < TIP_TOL, (
        'the blank came out %.3f across and the tip circle is %.3f - the '
        'tooth pattern did not close' % (r_out * 2, P.r_tip(P.z_pinion) * 2))

    # The horn arm slot must not reach the tooth roots, or the arms break out.
    hub_wall = P.r_root(P.z_pinion) - val('boss_bore_d') * 10 / 2
    assert hub_wall >= MIN_WALL_MM, (
        'only %.2f mm between the Oe%.2f boss bore and the %.2f root circle'
        % (hub_wall, val('boss_bore_d') * 10, P.r_root(P.z_pinion)))
    assert val('broach_to') * 10 <= val('face') * 10 + TOL, (
        'the spline tops out %.2f into a %.2f face'
        % (val('broach_to') * 10, val('face') * 10))
    # AGAINST THE DERIVED FLOOR, NOT AGAINST ITSELF. This read
    # `>= J3_HUB.engaged`, which is the value being checked - an assert that
    # cannot fail. lib/gears.J3_ENGAGE_FLOOR_MM is the larger of the shear
    # floor the servo's own stall torque needs (0.88 mm on the SG90) and the
    # forming floor a broach needs to cut a usable tooth trace in PETG
    # (2.00 mm, ASSUMED). The forming floor binds; see lib/gears.py.
    assert val('engaged') * 10 >= J3_ENGAGE_FLOOR_MM - TOL, (
        'only %.2f mm of spline engagement on the %s against a %.2f floor'
        % (val('engaged') * 10, _SERVO.name, J3_ENGAGE_FLOOR_MM))
    assert val('washer_d') * 10 < P.r_root(P.z_pinion) * 2, (
        'the Oe%.2f washer does not land on the top face' % (val('washer_d') * 10))
    assert abs(val('module') * 10 - P.module) < TOL, (
        'the module parameter %.4f does not match J3_PAIR %.4f'
        % (val('module') * 10, P.module))
    _case_top = _SERVO.tab_thk + _SERVO.tab_below_top
    print('seats %.2f up the %s (%.2f clear of its case top) - forearm.py '
          'must stand the J3 lobe off to match'
          % (val('seat_z') * 10, _SERVO.name, val('seat_z') * 10 - _case_top))
    print('spline hub: boss bore Oe%.2f to %.2f, then Oe%.2f BROACHED %.2f..%.2f'
          % (val('boss_bore_d') * 10, val('boss_bore_h') * 10,
             val('broach_d') * 10, val('boss_bore_from') * 10,
             val('broach_to') * 10))
    print('  %.2f mm of spline engaged against a %.2f floor (%.0f%% margin) - '
          'NO HORN | needs a Oe%.1f washer under the screw'
          % (val('engaged') * 10, J3_ENGAGE_FLOOR_MM,
             100.0 * (val('engaged') * 10 / J3_ENGAGE_FLOOR_MM - 1),
             val('washer_d') * 10))
    print('  THAT IS THE WHOLE SPLINE. engaged = min(hub top, spline top) less '
          'the boss top, and this face is far above the spline, so it equals '
          'spline_h exactly - %.2f on the %s. A thicker gear buys no more of '
          'it; only a different servo would.'
          % (_SERVO.spline_h, _SERVO.name))
    print('wall between the boss bore and the tooth roots: %.2f mm' % hub_wall)
    print('centre distance to the J3 servo shaft %.3f mm' % P.centre_distance)
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s'
          % (body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d'
          % (comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
