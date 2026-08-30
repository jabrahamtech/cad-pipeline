"""robotarm/j3_servo_cap - Fusion MCP generating script.

Rebuilds `robotarm_j3_servo_cap` (idempotent).

THE J3 SERVO PAD, LIFTED OFF THE FOREARM. It is the outer 5.50 mm that
forearm.py used to carry integrally, and it is a separate part for exactly
one reason: with it integral the geared elbow COULD NOT BE ASSEMBLED. All
three of GATE j3_installs' failures were this pad being in the way -

  - the 36T gear was 1.25 mm too big to pass its own insertion path,
  - the pinion was 6.80 mm short of the run-up it needs to thread onto the
    horn, and could not go in on the servo either (r 12.50 against a 12.40
    window),
  - the retention M3 had 1.20 mm of driver clearance where a bit wants 25.

Lift the pad off and all three go. See specs/robotarm/_HANDOFF.md section 10.

WHAT STAYS ON THE FOREARM IS THE STANDOFF WEB, so the load path priced in
section 9 - 71x on interlayer shear, 1.6 % of backlash in lost motion - is
unchanged. This part only carries the servo's own reaction into that web.

THE ORDER THIS BUYS:
  1. j3_gear in through the plate bore - nothing outboard of the standoff,
  2. M3 down the elbow axis and TIGHTENED - open access,
  3. j3_pinion pressed onto the horn with the servo in your hand, off the arm,
  4. servo + pinion + this cap bolted on as one unit, phased into mesh.

EVERY MATING NUMBER IS READ FROM THE FOREARM, NOT RE-DERIVED. fa_cap_t,
fa_cap_reach, fa_cap_screw_y/z, fa_lobe_z and the servo window stations all
come out of the document, and the build ASSERTS they are there rather than
falling back on a default. A cap that quietly built itself to its own idea of
the interface would fit nothing, and this project has been bitten by exactly
that class of drift on shaft_from_end, the lead datum and sb_arm_l1.

THE SCREW HEADS ARE COUNTERBORED FLUSH AND THEY HAVE TO BE. The servo's tab
plate lands ON this face and spans y -21.70..10.40 by z +/-6.20 - the cap
screws sit under it. Flush heads leave 2.30 mm of cap below the counterbore:
bearing area 19.2 mm2 under the head, and ~43 mm2 of shear-out around it at
the interlayer allowable, against about 7 N per screw. Not generous-looking,
not close either.

Local frame: origin on the J3 SERVO SHAFT axis (which is the pinion axis, one
centre distance from the elbow). +X runs along the arm toward the wrist - the
forearm's +Y - and +Z out of the seating face toward the servo, so z 0 is the
face that lands on the web and z = fa_cap_t is the tab plane.

Print orientation: FLAT, seating face on the bed. Every hole is vertical, the
window is a through slot, and the only overhangs are the counterbore roofs,
which are 3.4 -> 6.0 and bridge fine.
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

from lib.design_rules import FASTENER_MM as _FASTENERS  # noqa: E402
from lib.gears import J3_PAIR  # noqa: E402
from lib.palette import hints_for  # noqa: E402
from lib.servo import CATALOG  # noqa: E402

COMPONENT = 'robotarm_j3_servo_cap'
BODY_NAME = 'j3_servo_cap'
PREFIX = 'sc_'
STYLE = 'sty_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('forearm')
PH_PLATE = 'cap plate'
PH_SERVO = 'servo window'
PH_FIX = 'fixing'
PH_FINISH = 'finish'
PHASES = [PH_PLATE, PH_SERVO, PH_FIX, PH_FINISH]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    S = CATALOG['MG90S']
    M3 = _FASTENERS['M3']

    def _set(full, expr, comment, units='mm'):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment=''):
        _set(PREFIX + name, expr, comment)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    # ---- THE INTERFACE IS THE FOREARM'S, AND IT IS REQUIRED ----------------
    # Not defaulted. A cap that built itself to its own idea of the interface
    # would fit nothing, and would print clean while doing it.
    def fa(name):
        p = ups.itemByName('fa_' + name)
        assert p is not None, (
            'fa_%s is not in this document. j3_servo_cap is a MATING part - '
            'build forearm.py first, in the same document, so the interface '
            'is read rather than guessed' % name)
        return p.value * 10.0

    t = fa('cap_t')
    reach = fa('cap_reach')
    screw_y = fa('cap_screw_y')
    screw_z = fa('cap_screw_z')
    lobe_z = fa('lobe_z')
    lobe_pad = fa('lobe_pad')
    loc = fa('loc')
    wall = fa('wall')
    centre = fa('j3_centre')
    l2 = fa('l2')
    y_pin = -l2 + centre

    # ---- the servo, in this part's own frame ------------------------------
    # Same construction forearm.py uses, so the window lands where the servo
    # actually is: the shaft sits shaft_from_end in from the NEAR end and the
    # case runs on toward the wrist.
    near = -S.shaft_from_end
    far = near + S.case_l
    mid = (near + far) / 2.0
    sc_lo, sc_hi = mid - S.tab_hole_pitch / 2.0, mid + S.tab_hole_pitch / 2.0
    x_lo = sc_lo - lobe_pad
    x_hi = reach - y_pin

    param('t', '%.4f mm' % t, 'fa_cap_t - the pad thickness the forearm gave up')
    param('x_lo', '%.4f mm' % x_lo, 'derived: lobe_pad past the inboard tab screw')
    param('x_hi', '%.4f mm' % x_hi, 'derived: fa_cap_reach, in this frame')
    param('half_z', '%.4f mm' % lobe_z, 'fa_lobe_z')
    param('case_x0', '%.4f mm' % (near - loc / 2), 'servo window, near end')
    param('case_x1', '%.4f mm' % (far + loc / 2), 'servo window, far end')
    param('case_z', '%.4f mm' % (S.case_w + loc), 'servo window across the width')
    param('screw_a', '%.4f mm' % sc_lo, 'inboard servo tab screw')
    param('screw_b', '%.4f mm' % sc_hi, 'outboard servo tab screw')
    param('pilot_d', '1.8 mm', 'servo screw pilot - design_rules, self-tapping')
    param('pilot_depth', '3.5 mm', 'engagement from the tab plane')
    param('lead_key_d', '%.4f mm' % (S.lead_bundle_dia + 0.2),
          'keyway width, one bundle diameter plus a locational fit. The bundle\n'
          '           leaves the SHORT END FACE - lib/servo.py names the face in its\n'
          '           first sentence, and five parts had this on the wrong wall.')
    param('lead_key_l', '%.4f mm' % (lobe_pad + (S.tab_hole_pitch - S.case_l) / 2 + 1.0),
          'out from the shaft-end face to the cap edge plus 1.0 of overshoot -\n'
          '           a keyway that stops inside the plate is a blind pocket and traps\n'
          '           the cable exactly as a solid wall would')
    param('fix_x', '%.4f mm' % (screw_y - y_pin), 'fa_cap_screw_y, in this frame')
    param('fix_z', '%.4f mm' % screw_z, 'fa_cap_screw_z')
    param('fix_d', '%.4f mm' % M3['clearance'], 'M3 clearance - design_rules')
    param('fix_head_d', '6.0 mm', 'M3 socket head, the same pair j3_gear uses')
    param('fix_head_z', '3.2 mm',
          'counterbore depth. The heads MUST finish flush: the servo tab plate\n'
          '           lands on this face and spans the screws. Leaves t - this = the\n'
          '           material under the head.')
    param('corner_r', '%.4f mm' % (ups.itemByName('fa_lobe_radius_j3').value * 10
                                   if ups.itemByName('fa_lobe_radius_j3') else 4.5),
          'fa_lobe_radius_j3 - the same corner the standoff behind it carries')
    param('ef', '0.4 mm', 'elephant-foot chamfer, bed face')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- checks, before any geometry --------------------------------------
    assert val('fix_head_z') < val('t'), (
        'the %.1f counterbore goes straight through a %.1f cap'
        % (val('fix_head_z') * 10, val('t') * 10))
    under = (val('t') - val('fix_head_z')) * 10
    assert under >= 2.0, (
        'only %.2f mm of cap under the screw head' % under)
    assert (val('fix_x') + val('fix_head_d') / 2) * 10 <= x_hi - wall + 1e-6, (
        'the counterbore at x %.2f reaches past the cap edge at %.2f'
        % (val('fix_x') * 10, x_hi))
    assert (val('fix_x') - val('fix_head_d') / 2) * 10 >= val('case_x1') * 10 + wall - 1e-6, (
        'the counterbore at x %.2f breaks into the servo window ending at %.2f'
        % (val('fix_x') * 10, val('case_x1') * 10))
    assert (val('fix_z') + val('fix_head_d') / 2) * 10 <= lobe_z - wall + 1e-6, (
        'the counterbore at z %.2f reaches past the cap edge at %.2f'
        % (val('fix_z') * 10, lobe_z))
    # The cap screws and the servo's own tab screws must not foul each other.
    for sx_name in ('screw_a', 'screw_b'):
        d = math.hypot((val(sx_name) - val('fix_x')) * 10, val('fix_z') * 10)
        need = (val('fix_head_d') / 2 + val('pilot_d') / 2) * 10 + wall
        assert d >= need, (
            'the cap screw and the servo pilot at x %.2f are %.2f apart and '
            'need %.2f' % (val(sx_name) * 10, d, need))

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------
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
    fil = comp.features.filletFeatures
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                sk.name + ': expected ' + str(expected) + ', got '
                + str(sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            # Without this a CUT eats every other component in the document.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm, z_cm=0.0):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def rect(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0), mpt(sk, x1, y1))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def hole(name, x_c, y_c, d, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_c, y_c), d / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    # ---- phase 1: the plate ------------------------------------------------
    t0 = design.timeline.count
    rect('plate', val('x_lo'), val('x_hi'), -val('half_z'), val('half_z'),
         '0 mm', PREFIX + 't', NEW)
    col = adsk.core.ObjectCollection.create()
    for e in comp.bRepBodies.item(0).edges:
        b = e.boundingBox
        if (abs(b.minPoint.x - b.maxPoint.x) < val('tol')
                and abs(b.minPoint.y - b.maxPoint.y) < val('tol')):
            col.add(e)
    assert col.count == 4, 'expected 4 vertical corners, found %d' % col.count
    f_inp = fil.createInput()
    f_inp.addConstantRadiusEdgeSet(col, V(PREFIX + 'corner_r'), True)
    fil.add(f_inp).name = 'corners'
    group(t0, PH_PLATE)

    # ---- phase 2: the servo goes through it --------------------------------
    t1 = design.timeline.count
    rect('window', val('case_x0'), val('case_x1'),
         -val('case_z') / 2, val('case_z') / 2, '0 mm', PREFIX + 't', CUT)
    # ONE keyway, centred across the width, in the END wall at the shaft end,
    # running OUT to daylight. Centred it is symmetric under a flip, so the
    # servo may arrive either way up.
    rect('lead_key', val('case_x0') - val('lead_key_l'), val('case_x0'),
         -val('lead_key_d') / 2, val('lead_key_d') / 2,
         '0 mm', PREFIX + 't', CUT)
    for nm, xs in (('a', val('screw_a')), ('b', val('screw_b'))):
        hole('pilot_' + nm, xs, 0.0, val('pilot_d'),
             PREFIX + 't - ' + PREFIX + 'pilot_depth', PREFIX + 'pilot_depth', CUT)
    group(t1, PH_SERVO)

    # ---- phase 3: the two M3 into the standoff web -------------------------
    t2 = design.timeline.count
    for sz, nm in ((+1, 'p'), (-1, 'm')):
        hole('fix_' + nm, val('fix_x'), sz * val('fix_z'), val('fix_d'),
             '0 mm', PREFIX + 't', CUT)
        hole('fix_cbore_' + nm, val('fix_x'), sz * val('fix_z'),
             val('fix_head_d'), PREFIX + 't - ' + PREFIX + 'fix_head_z',
             PREFIX + 'fix_head_z', CUT)
    group(t2, PH_FIX)

    # ---- phase 4: finish ---------------------------------------------------
    t3 = design.timeline.count
    col = adsk.core.ObjectCollection.create()
    for e in comp.bRepBodies.item(0).edges:
        bb = e.boundingBox
        if abs(bb.minPoint.z) < val('tol') and abs(bb.maxPoint.z) < val('tol'):
            col.add(e)
    if col.count:
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            col, V(PREFIX + 'ef'), False)
        chf.add(c_inp).name = 'bed_face_ef'
    group(t3, PH_FINISH)

    # ---- identity + diagnostics -------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d' % comp.bRepBodies.count)
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

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used))
    print('the J3 servo pad, lifted off the forearm so the elbow can be built')
    print('plate %.2f x %.2f x %.2f, corners r %.2f'
          % (val('x_hi') * 10 - val('x_lo') * 10, val('half_z') * 20,
             val('t') * 10, val('corner_r') * 10))
    print('servo window %.2f x %.2f, keyway %.2f wide x %.2f out of the end face'
          % (val('case_x1') * 10 - val('case_x0') * 10, val('case_z') * 10,
             val('lead_key_d') * 10, val('lead_key_l') * 10))
    print('servo pilots %.1f x %.1f deep at x %.2f / %.2f'
          % (val('pilot_d') * 10, val('pilot_depth') * 10,
             val('screw_a') * 10, val('screw_b') * 10))
    print('fixing: 2 x M3 at x %.2f, z +/-%.2f - %.1f clear, %.1f cbore x %.1f '
          'deep, %.2f of cap under the head'
          % (val('fix_x') * 10, val('fix_z') * 10, val('fix_d') * 10,
             val('fix_head_d') * 10, val('fix_head_z') * 10, under))
    print('   heads MUST be flush: the servo tab plate lands on this face')
    _need = val('t') * 10 + fa('cap_pilot_depth')
    _stock = [8, 10, 12, 16, 20, 25]
    _buy = next((n for n in _stock if n >= _need), _stock[-1])
    print('   screws go %.1f into the standoff web, so %.1f of screw is wanted '
          '- BUY M3 x %d' % (fa('cap_pilot_depth'), _need, _buy))
    assert _buy <= _need + 4.0, (
        'the nearest stock M3 is %d for a %.1f stack - it would bottom in the '
        'web' % (_buy, _need))
    print('interface READ from the forearm: cap_t %.2f, cap_reach %.2f, '
          'screw y %.2f z %.2f' % (t, reach, screw_y, screw_z))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s'
          % (body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('timeline groups: %r' % (PHASES,))
