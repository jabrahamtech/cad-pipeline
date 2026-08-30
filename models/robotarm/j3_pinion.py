"""robotarm/j3_pinion - Fusion MCP generating script.

Rebuilds `robotarm_j3_pinion` (idempotent). Spec: lib/gears.py J3_PAIR.

THE 18T INPUT HALF OF THE ELBOW REDUCTION, pressed onto the J3 MG90S's own
horn. j3_gear.py is the other half and both trace the SAME involute out of
lib/gears.py - see that file's tooth_polar().

18 TEETH IS THE FLOOR, NOT A ROUND NUMBER. z_min = 2/sin^2(20 deg) = 17.1,
so 17 undercuts and 18 does not. gripper_pinion gets away with 12 because a
rack has no tip circle to interfere with; this pair has two involutes and no
such licence. lib/gears.py asserts it rather than trusting this comment.

THE HORN NUMBERS ARE MEASURED AND THEY ARE NOT THE DATASHEET'S. The model
said the micro hub was 8.0; the caliper said 6.8 on 2026-08-28, which had
made every press pocket in this project 1.35 loose. The same three numbers
that gripper_pinion now uses are used here, because it is the same accessory
family (lib/servo.py: SG90 and MG90S carry identical horn dimensions). If
the MG90S horn in your bag differs, this pocket is the first suspect and
specs/robotarm/_horn_numbers.md is where the correction goes.

TRIM THE HORN TO gp-style arm_r BEFORE ASSEMBLY. The horn arm is 17.0 long
and this pinion's root circle is 9.69 - an untrimmed arm breaks straight out
through the teeth. The slot is a CROSS so either the single-arm or the
four-arm horn keys at 90 deg increments; a joint that carries the whole
forearm wants positive keying, not a press fit doing the work.

Print orientation: TOOTH FACE ON THE BED, horn pocket up. Same as
gripper_pinion, same face width, so one test print settles both.
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

from lib.gears import J3_PAIR  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_j3_pinion'
BODY_NAME = 'j3_pinion'
PREFIX = 'jp_'
WRIST = 'wr_'
STYLE = 'sty_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('j3_pinion')
PH_TEETH = 'gear teeth'
PH_STEM = 'horn interface'
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

    # --- horn interface. MEASURED 2026-08-28, see the docstring. ----------
    param('hub_d', '6.95 mm',
          'MG90S horn hub MEASURED 6.8 + press 0.15. The model said 8.0 and\n'
          '           every press pocket in this project was 1.35 loose on it.')
    param('hub_depth', '3.1 mm', 'horn hub 3.0 + 0.1 so the shaft sets the axial gap')
    param('arm_w', '5.85 mm',
          'horn arm width AT the r 6 trim: MEASURED 5.7 + press 0.15')
    param('arm_r', '6.0 mm', 'horn arms TRIMMED to this radius at assembly')
    param('arm_depth', '2.1 mm', 'horn blade 2.0 + 0.1 seating')
    param('screw_d', '5.5 mm', 'driver access to the horn retaining screw')
    param('lead_in', '0.5 mm', 'insertion lead-in chamfer')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE -------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
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

    T = P.tooth_polar(P.z_pinion, n=14, sink=val('tooth_sink') * 10)
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
    disc('horn_hub_relief', val('hub_d'), '0.0 mm', PREFIX + 'hub_depth', CUT)
    for ang, tag in ((0, 'a'), (1, 'b')):
        sk_a = sketch(comp.xYConstructionPlane, 'sk_horn_arm_slot_' + tag)
        if ang == 0:
            p0 = mpt(sk_a, -val('arm_r'), -val('arm_w') / 2)
            p1 = mpt(sk_a, val('arm_r'), val('arm_w') / 2)
        else:
            p0 = mpt(sk_a, -val('arm_w') / 2, -val('arm_r'))
            p1 = mpt(sk_a, val('arm_w') / 2, val('arm_r'))
        sk_a.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
        extrude(profiles(sk_a, expected=1), CUT, '0.0 mm', PREFIX + 'arm_depth',
                'horn_arm_slot_' + tag)
    disc('horn_screw_bore', val('screw_d'), '0.0 mm', PREFIX + 'face', CUT)
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
    assert abs(r_out - P.r_tip(P.z_pinion)) < 0.05, (
        'the blank came out %.3f across and the tip circle is %.3f - the '
        'tooth pattern did not close' % (r_out * 2, P.r_tip(P.z_pinion) * 2))

    # The horn arm slot must not reach the tooth roots, or the arms break out.
    arm_wall = P.r_root(P.z_pinion) - val('arm_r') * 10
    assert arm_wall >= 1.6, (
        'only %.2f mm between the horn arm tips (r %.2f) and the tooth roots '
        '(r %.2f) - trim the horn shorter or the pinion loses teeth'
        % (arm_wall, val('arm_r') * 10, P.r_root(P.z_pinion)))
    hub_wall = P.r_root(P.z_pinion) - val('hub_d') * 10 / 2
    assert hub_wall >= 1.6, (
        'only %.2f mm between the horn hub pocket and the tooth roots' % hub_wall)
    assert val('hub_depth') + 1e-9 >= val('arm_depth'), (
        'the hub pocket is shallower than the arm slot - the horn cannot seat')
    assert val('face') > val('hub_depth'), 'the hub pocket goes straight through'

    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used))
    print('%dT module %.2f face %.2f - lib/gears.py J3_PAIR, ratio %.4f'
          % (P.z_pinion, P.module, P.face, P.ratio))
    print('r base/pitch/tip/root mm: %.3f %.3f %.3f %.3f'
          % (P.r_base(P.z_pinion), P.r_pitch(P.z_pinion),
             P.r_tip(P.z_pinion), P.r_root(P.z_pinion)))
    print('tooth thickness at pitch %.3f mm (target %.3f incl. backlash)'
          % (T['thk_pitch'], math.pi * P.module / 2 - P.backlash / 2))
    print('tip land %.3f mm - a pointed tooth would read 0' % (2 * T['ang_tip'] * T['r_tip']))
    print('horn: hub %.2f x %.2f | cross slot r %.1f x %.2f wide x %.2f deep '
          '| driver bore %.1f'
          % (val('hub_d') * 10, val('hub_depth') * 10, val('arm_r') * 10,
             val('arm_w') * 10, val('arm_depth') * 10, val('screw_d') * 10))
    print('walls: arm tips/roots %.2f | hub/roots %.2f mm' % (arm_wall, hub_wall))
    print('centre distance to the J3 servo shaft %.3f mm' % P.centre_distance)
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s'
          % (body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d'
          % (comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
