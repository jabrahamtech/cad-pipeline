"""robotarm/servo_body - Fusion MCP generating script.

Rebuilds `robotarm_servo_<SERVO>` (idempotent). Spec: lib/servo.py.

THE SERVO AS A SOLID. Not a printed part - a COTS envelope, so that the
pockets cut for it can be tested against geometry instead of against
arithmetic.

WHY IT DID NOT EXIST AND SHOULD HAVE. Every servo pocket in this project was
cut from numbers in lib/servo.py and checked against those same numbers. That
is not a check, it is a restatement: if case_w is wrong, the pocket is wrong
and the assert that compares them agrees. Jonathan has now reported three
times that the servos do not go in. The bench is the only thing that has ever
disagreed with this project about a servo, and it should not have to be.

With a solid, _check_servo_fit.py can drop this body into the host that
carries it and ask pointContainment whether they overlap - the same method
GATE j3_installs uses. A pocket that grips reads as interference; a pocket
that is merely tight reads as clearance and can be measured.

WHAT IS AND IS NOT TRUSTWORTHY HERE. Everything below is DATASHEET grade
except where lib/servo.py says otherwise, and lib/servo.py's own docstring
rates datasheet body dimensions of cheap servos as weak. So:

  THIS BODY IS AS WRONG AS lib/servo.py IS.

It cannot discover that an MG90S case is really 12.9 wide. What it CAN do is
find every place the project's own numbers already fail to fit each other -
a pocket cut at a 0.10 mm per side clearance, a horn slot narrower than the
horn, a lead that leaves through a wall. Those are the errors that have
actually been blocking assembly, and they are all visible without a caliper.
When the caliper does arrive, correcting lib/servo.py corrects this body and
every gate that uses it, in one edit.

THE FRAME IS lib/servo.py's, EXACTLY: origin on the OUTPUT SHAFT AXIS at the
TAB PLANE (the underside of the mounting tabs - the face a bracket clamps).
+X along the case length AWAY from the shaft end. +Z out of the shaft.
Nothing here re-derives that; it is the datum every mount already holds to.

TWO BODIES, ON PURPOSE:
  servo_<name>  case + flange + boss + spline + lead stub
  horn_<name>   the horn alone, so a gate can ask about the horn separately
The horn is the part that varies by batch (lib/servo.py, deshipu, Roger
Cheng) and the part Jonathan says will not enter anything, so it is testable
on its own rather than welded to the case.

Not printed. Not exported. Never on a plate.
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

from lib.palette import hints_for  # noqa: E402
from lib.servo import (  # noqa: E402
    CATALOG,
    MG995_TAB_HOLE_PITCH_Y,
    horn_arm_w,
    horn_arms,
)

# WHICH SERVO. One script, three bodies - change and rerun.
SERVO = 'MG90S'

COMPONENT = 'robotarm_servo_' + SERVO
BODY_NAME = 'servo_' + SERVO
HORN_NAME = 'horn_' + SERVO
PREFIX = 'sv_'
STYLE = 'sty_'
MATERIAL_NAME = 'ABS Plastic'
APPEARANCE_HINTS = hints_for('servo_body')
PH_CASE = 'case'
PH_FLANGE = 'flange'
PH_OUTPUT = 'output'
PH_HORN = 'horn'
PH_LEAD = 'lead'
PHASES = [PH_CASE, PH_FLANGE, PH_OUTPUT, PH_HORN, PH_LEAD]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    S = CATALOG[SERVO]
    micro = SERVO in ('SG90', 'MG90S')

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def val(name):
        # Fusion answers in CENTIMETRES.
        return ups.itemByName(PREFIX + name).value * 10.0

    # --- the envelope, WRITTEN FROM lib/servo.py, NOT CHOSEN HERE ---------
    param('case_l', '%.4f mm' % S.case_l, '%s case length, along X' % SERVO)
    param('case_w', '%.4f mm' % S.case_w, '%s case width, across Y' % SERVO)
    param('case_h', '%.4f mm' % S.case_h, '%s case height' % SERVO)
    param('shaft_from_end', '%.4f mm' % S.shaft_from_end,
          'shaft axis to the NEAR end of the case. The frame origin is ON\n'
          '           the shaft, so the case runs -shaft_from_end .. case_l - this.')
    param('tab_span', '%.4f mm' % S.tab_span, 'flange tip to tip, along X')
    param('tab_thk', '%.4f mm' % S.tab_thk, 'flange thickness')
    param('tab_hole_dia', '%.4f mm' % S.tab_hole_dia, 'through-hole in the tab')
    param('tab_hole_pitch', '%.4f mm' % S.tab_hole_pitch,
          'hole centres along X. DERIVED in lib/servo.py for the MG90S and\n'
          '           NOT stated by any drawing - caliper before trusting a pocket cut\n'
          '           against it.')
    param('tab_below_top', '%.4f mm' % S.tab_below_top,
          'case top down to the TOP of the tabs')
    param('case_top', '%stab_thk + %stab_below_top' % (PREFIX, PREFIX),
          'DERIVED: the tab plane is z 0, the tabs are tab_thk thick')
    param('case_bot', '%scase_top - %scase_h' % (PREFIX, PREFIX), 'derived')
    param('boss_dia', '%.4f mm' % S.boss_dia, 'output collar the horn sits on')
    param('boss_h', '%.4f mm' % S.boss_h, 'collar height above the case top')
    param('spline_dia', '%.4f mm' % S.spline_dia, 'output spline OD')
    param('spline_h', '%.4f mm' % S.spline_h, 'spline height above the collar')
    param('boss_top', '%scase_top + %sboss_h' % (PREFIX, PREFIX), 'derived')
    param('horn_hub_dia', '%.4f mm' % S.horn_hub_dia,
          'MEASURED 2026-08-28 - the community model said 8.0 for the micro\n'
          '           and it is 6.8, which had made every press pocket 1.35 loose')
    param('horn_hub_h', '%.4f mm' % S.horn_hub_h, 'hub height above the blade seat')
    param('horn_blade_thk', '%.4f mm' % S.horn_blade_thk, 'blade thickness')
    param('horn_arm_len', '%.4f mm' % S.horn_arm_len,
          'shaft centre to the OUTERMOST hole centre')
    param('lead_bundle_dia', '%.4f mm' % S.lead_bundle_dia, 'the three-wire bundle')
    param('lead_x', '%.4f mm' % S.lead_x,
          'the END FACE the bundle leaves = -shaft_from_end. It is the SHORT\n'
          '           end face at the shaft end, NOT a long side wall - five parts once\n'
          '           notched the wrong wall from this datum.')
    param('lead_z', '%.4f mm' % S.lead_z,
          'one bundle diameter up from the case BOTTOM, so strongly negative')
    _set(STYLE + 'ef', '0.4 mm', 'elephant-foot chamfer, functional faces', 'mm')

    # --- rebuild: RENAME then delete ---------------------------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        # Skip the root: in a saved part file it carries the document's name.
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

    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures
    xy = comp.xYConstructionPlane
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    def rect(sk, x0, x1, y0, y1):
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            P3(x0 / 10.0, y0 / 10.0, 0), P3(x1 / 10.0, y1 / 10.0, 0))

    def solid(sk, z0_mm, dz_mm, op, target=None):
        inp = extrudes.createInput(sk.profiles.item(0), op)
        if op != NEW and target is not None:
            inp.participantBodies = [target]
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V('%.5f mm' % abs(dz_mm))),
            (adsk.fusion.ExtentDirections.PositiveExtentDirection if dz_mm >= 0
             else adsk.fusion.ExtentDirections.NegativeExtentDirection))
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
            V('%.5f mm' % z0_mm))
        return extrudes.add(inp)

    x_near = -val('shaft_from_end')
    x_far = x_near + val('case_l')
    hw = val('case_w') / 2.0

    # ---- PHASE: case -----------------------------------------------------
    t0 = design.timeline.count
    sk = sketches.add(xy)
    sk.name = 'sk_case'
    rect(sk, x_near, x_far, -hw, hw)
    ext = solid(sk, val('case_bot'), val('case_h'), NEW)
    ext.name = 'case'
    body = ext.bodies.item(0)
    body.name = BODY_NAME
    group(t0, PH_CASE)

    # ---- PHASE: flange ---------------------------------------------------
    # ONE plate across the full span. The tabs are the DATUM - lib/servo.py:
    # "THE DATUM IS THE TAB PLANE, NOT THE CASE" - so this is the face every
    # mount clamps and the holes are what locate the servo.
    t1 = design.timeline.count
    span = val('tab_span')
    x_mid = (x_near + x_far) / 2.0
    sk = sketches.add(xy)
    sk.name = 'sk_flange'
    rect(sk, x_mid - span / 2.0, x_mid + span / 2.0, -hw, hw)
    ext = solid(sk, 0.0, val('tab_thk'), JOIN, body)
    ext.name = 'flange'

    sk = sketches.add(xy)
    sk.name = 'sk_tab_holes'
    pitch = val('tab_hole_pitch')
    ys = [0.0] if micro else [-MG995_TAB_HOLE_PITCH_Y / 2.0,
                              MG995_TAB_HOLE_PITCH_Y / 2.0]
    for sx in (-1, 1):
        for y in ys:
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                P3((x_mid + sx * pitch / 2.0) / 10.0, y / 10.0, 0),
                val('tab_hole_dia') / 2.0 / 10.0)
    for i in range(sk.profiles.count):
        inp = extrudes.createInput(sk.profiles.item(i), CUT)
        inp.participantBodies = [body]
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V('%stab_thk * 2' % PREFIX)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('0 mm'))
        extrudes.add(inp)
    group(t1, PH_FLANGE)

    # ---- PHASE: output ---------------------------------------------------
    t2 = design.timeline.count
    sk = sketches.add(xy)
    sk.name = 'sk_boss'
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        P3(0, 0, 0), val('boss_dia') / 2.0 / 10.0)
    ext = solid(sk, val('case_top'), val('boss_h'), JOIN, body)
    ext.name = 'output boss'

    sk = sketches.add(xy)
    sk.name = 'sk_spline'
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        P3(0, 0, 0), val('spline_dia') / 2.0 / 10.0)
    ext = solid(sk, val('boss_top'), val('spline_h'), JOIN, body)
    ext.name = 'spline'
    group(t2, PH_OUTPUT)

    # ---- PHASE: horn -----------------------------------------------------
    # A SEPARATE BODY. It is the piece that varies by batch and the piece
    # Jonathan says enters nothing, so a gate must be able to ask about it
    # without the case in the way.
    #
    # THE ARM TAPERS AND THE TAPER IS MEASURED. lib/servo.py: 5.7 wide at
    # r 6 down to 4.0 at r 17. A constant-width arm would be a lie in the
    # direction that makes every slot look fine.
    t3 = design.timeline.count
    sk = sketches.add(xy)
    sk.name = 'sk_horn_arms'
    # WHERE THE ARMS ARE - lib/servo.py horn_arms(). The micro cross is
    # NOT symmetric (34.4 long, 17.0 short, MEASURED) so this is four
    # different reaches, not four equal ones.
    reaches = horn_arms(S)
    lines = sk.sketchCurves.sketchLines
    for ang, reach in reaches:
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        r0 = val('horn_hub_dia') / 2.0

        def pt(r, off):
            return P3((r * ca - off * sa) / 10.0, (r * sa + off * ca) / 10.0, 0)

        w0 = horn_arm_w(S, r0) / 2.0
        w1 = horn_arm_w(S, reach) / 2.0
        p = [pt(r0, w0), pt(reach, w1), pt(reach, -w1), pt(r0, -w0)]
        for k in range(len(p)):
            lines.addByTwoPoints(p[k], p[(k + 1) % len(p)])
    for i in range(sk.profiles.count):
        inp = extrudes.createInput(sk.profiles.item(i), NEW if i == 0 else JOIN)
        if i:
            inp.participantBodies = [comp.bRepBodies.itemByName(HORN_NAME)]
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V('%shorn_blade_thk' % PREFIX)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
            V('%sboss_top' % PREFIX))
        e = extrudes.add(inp)
        if i == 0:
            e.bodies.item(0).name = HORN_NAME

    horn = comp.bRepBodies.itemByName(HORN_NAME)
    sk = sketches.add(xy)
    sk.name = 'sk_horn_hub'
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        P3(0, 0, 0), val('horn_hub_dia') / 2.0 / 10.0)
    ext = solid(sk, val('boss_top'), val('horn_hub_h'), JOIN, horn)
    ext.name = 'horn hub'
    group(t3, PH_HORN)

    # ---- PHASE: lead -----------------------------------------------------
    # ONE stub, out of the SHORT END FACE at the shaft end, centred across
    # the width. lead_y is 0 in lib/servo.py and asserted there.
    t4 = design.timeline.count
    yz = comp.yZConstructionPlane
    sk = sketches.add(yz)
    sk.name = 'sk_lead'
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        sk.modelToSketchSpace(P3(val('lead_x') / 10.0, 0.0, val('lead_z') / 10.0)),
        val('lead_bundle_dia') / 2.0 / 10.0)
    inp = extrudes.createInput(sk.profiles.item(0), JOIN)
    inp.participantBodies = [body]
    inp.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(V('%slead_bundle_dia * 2' % PREFIX)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        V('%.5f mm' % val('lead_x')))
    e = extrudes.add(inp)
    e.name = 'lead stub'
    group(t4, PH_LEAD)

    for b in (body, horn):
        b.material = design.materials.itemByName(MATERIAL_NAME) or b.material

    bb = body.boundingBox
    hb = horn.boundingBox
    print('%s envelope, frame = shaft axis on the TAB PLANE' % SERVO)
    print('  case   x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f'
          % (x_near, x_far, -hw, hw, val('case_bot'), val('case_top')))
    print('  flange span %.2f x %.2f x %.2f, %d hole(s) Oe%.2f at pitch %.2f'
          % (span, val('case_w'), val('tab_thk'), 2 * len(ys),
             val('tab_hole_dia'), pitch))
    assert abs(max(r for _, r in reaches) - val('horn_arm_len')) < val('horn_arm_len'), (
        'horn_arms() reaches %.2f against a stated arm length of %.2f'
        % (max(r for _, r in reaches), val('horn_arm_len')))
    print('  boss Oe%.2f to z %.2f | spline Oe%.2f to z %.2f'
          % (val('boss_dia'), val('boss_top'), val('spline_dia'),
             val('boss_top') + val('spline_h')))
    print('  horn hub Oe%.2f x %.2f | arms reach %.2f, %.2f wide at the hub -> %.2f at the tip'
          % (val('horn_hub_dia'), val('horn_hub_h'),
             max(r for _, r in reaches),
             horn_arm_w(S, val('horn_hub_dia') / 2.0),
             horn_arm_w(S, max(r for _, r in reaches))))
    print('  lead Oe%.2f leaving the SHORT END FACE at x %.2f, z %.2f'
          % (val('lead_bundle_dia'), val('lead_x'), val('lead_z')))
    print('  body bbox mm  X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('  horn bbox mm  X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (hb.minPoint.x * 10, hb.maxPoint.x * 10, hb.minPoint.y * 10,
             hb.maxPoint.y * 10, hb.minPoint.z * 10, hb.maxPoint.z * 10))
    print('  NOT PRINTED - COTS envelope, never goes on a plate')
