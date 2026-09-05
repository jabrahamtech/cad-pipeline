"""robotarm/j4_tab_shim - Fusion MCP generating script.

Rebuilds `robotarm_j4_tab_shim` (idempotent). PRINT TWO.

Spec: specs/robotarm/j4_tab_shim.md

THE PART THAT LETS AN SG90 SIT ON A FOREARM CUT FOR AN MG90S.

Jonathan, 2026-09-05: "we have already printed the forarm so I am not keen on
reprinting it - so design around that". The forearm on his bench predates the
J3/J4 servo swap. Its J4 lobe gives 5.90 mm from the plate outer face to the
tab plane, which is exactly what an MG90S wants; an SG90 is 6.70 mm to the
same plane. The case bottoms out 0.80 mm early, on about 37 mm2 of ledge at
the two ends of the J4 journal bore where the Oe20.35 bore stops and the
22.70 case does not, and holds the tab plate 0.80 proud of its own pad. The
two tab screws then have nothing to pull down onto.

THE 0.80 IS MEASURED, NOT DERIVED. The f0509b4 forearm was rebuilt from its
own snapshot, an SG90 solid dropped into its J4 station, and the servo swept
outboard in 0.40 steps against a pointContainment sampler:

    shim 0.00  ->  45.8 mm3 of servo inside the lobe
    shim 0.40  ->  22.9 mm3
    shim 0.80  ->   0.0 mm3      <- the first offset that clears

and 0.80 is not merely the first that works, it is the largest worth having:
every further 0.40 costs 0.40 of spline engagement, measured on the same
model. lib/joints.J4_PRINTED_FOREARM_SHIM_MM carries the number and the
sweep; wrist_hub takes the 0.20 of engagement it still costs back out of its
own bore.

WHY TWO PADS AND NOT ONE FRAME. The SG90's tab plate is 32.30 x 12.20 and its
case is 22.70 x 12.20 - the case is exactly as wide as the flange. There is
no material along the long sides to join the two ears with, so a one-piece
shim would have to be wider than the flange and the lobe recess is not. Two
pads, one under each ear.

THE SLOT IS OPEN, and that is the difference between a shim you can fit and
one you cannot. A closed hole means threading a 0.80 mm pad down a pocket and
holding it on the screw while the servo goes in. Open to the outer edge, each
pad slides in under its ear after the servo is resting in the window. It is
what a shim is normally shaped like and for the same reason.

NOT A STRUCTURAL PART. It is in pure compression between the tab plate and
the pad, and the tab screw passes through the slot without touching it. That
is why the 1.35 mm of material beside the slot is reported rather than
asserted against MIN_WALL: a wall that carries nothing is a printability
question, and at 0.80 tall it prints as three perimeters.

BUY LONGER SCREWS. The servo's own M2 tab screws now have 0.80 mm more stack
to cross before they reach the forearm's pilots, so they engage 0.80 less.
"""

import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

from lib.design_rules import MIN_WALL_MM  # noqa: E402
from lib.joints import J4_PRINTED_FOREARM_SHIM_MM  # noqa: E402
from lib.joints import servo_for as _servo_for  # noqa: E402
from lib.palette import hints_for  # noqa: E402

MATERIAL_NAME = 'PET Plastic'

COMPONENT = 'robotarm_j4_tab_shim'
BODY_NAME = 'j4_tab_shim'
PREFIX = 'ts_'
# The shim prints with the wrist, so it takes the wrist's filament.
APPEARANCE_HINTS = hints_for('wrist_hub')

PH_PAD = 'pad'
PH_SLOT = 'screw slot'
PHASES = [PH_PAD, PH_SLOT]

# Clearance around the M2 tab screw in the open slot. It is a slot, not a
# hole - the screw must never touch it, or the shim starts locating the servo
# and the tabs stop.
SLOT_CLEARANCE_MM = 0.6


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    S = _servo_for('J4')

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

    # ---- the pad, in the servo's own frame --------------------------------
    # x runs along the case, from the case END outward to the flange tip.
    ear = (S.tab_span - S.case_l) / 2.0
    hole_from_case_end = S.tab_hole_pitch / 2.0 - S.case_l / 2.0

    param('t', '%.4f mm' % J4_PRINTED_FOREARM_SHIM_MM,
          'lib/joints.J4_PRINTED_FOREARM_SHIM_MM. MEASURED as the first servo\n'
          '           offset that clears the printed J4 lobe - see the docstring sweep.')
    param('len', '%.4f mm' % ear,
          'derived: (tab_span - case_l) / 2, the ear that overhangs the case')
    param('wid', '%.4f mm' % S.case_w,
          'derived: the flange is exactly as wide as the case on an SG90')
    param('slot_w', '%.4f mm' % (S.tab_hole_dia + SLOT_CLEARANCE_MM),
          'derived: the tab hole plus clearance. The screw passes through\n'
          '           without touching - the TABS locate the servo, never this.')
    param('slot_x', '%.4f mm' % hole_from_case_end,
          'derived: tab_hole_pitch / 2 - case_l / 2, the screw measured from\n'
          '           the case end - the edge this pad is registered against')

    inner_wall = val('slot_x') * 10 - val('slot_w') * 10 / 2.0
    side_wall = (val('wid') * 10 - val('slot_w') * 10) / 2.0
    assert inner_wall > 0.0, (
        'the slot at x %.2f is wider than its own offset from the case edge'
        % (val('slot_x') * 10))
    assert val('len') * 10 > val('slot_x') * 10, (
        'the screw at x %.2f is past the end of a %.2f pad'
        % (val('slot_x') * 10, val('len') * 10))

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
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
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected):
        assert sk.profiles.count == expected, (
            '%s made %d profiles, wanted %d' % (sk.name, sk.profiles.count, expected))
        col = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            col.add(sk.profiles.item(i))
        return col

    def extrude(prof, op, z0_expr, dz_expr, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0_expr))
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V(dz_expr)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        if op == CUT:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, 0.0))

    def rect(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0), mpt(sk, x1, y1))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    # ---- phase 1: the pad --------------------------------------------------
    t0 = design.timeline.count
    rect('pad', 0.0, val('len'), -val('wid') / 2, val('wid') / 2,
         '0 mm', PREFIX + 't', NEW)
    group(t0, PH_PAD)

    # ---- phase 2: the slot, OPEN at the outer edge -------------------------
    # It runs from the screw centre OUT past the end of the pad, so the shim
    # slides in sideways under an ear that is already in its recess.
    t1 = design.timeline.count
    rect('slot', val('slot_x'), val('len') + val('t'),
         -val('slot_w') / 2, val('slot_w') / 2,
         '0 mm', PREFIX + 't', CUT)
    group(t1, PH_SLOT)

    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used_appearance = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used_appearance = a.name
                    break
            if used_appearance != 'none':
                break
        if used_appearance != 'none':
            break

    props = body.physicalProperties
    vol = props.volume * 1000.0
    mass = props.mass * 1000.0
    bb = body.boundingBox
    print("body: '%s' | appearance: %s | PRINT TWO - one under each tab ear"
          % (body.name, used_appearance))
    print('THE SG90 DOES NOT FIT THE PRINTED J4 LOBE WITHOUT THIS.')
    print('   that lobe gives 5.90 from the plate face to the tab plane and an')
    print('   SG90 wants 6.70. MEASURED: 45.8 mm3 of servo inside the part at')
    print('   shim 0.00, 22.9 at 0.40, and 0.0 at %.2f.' % (val('t') * 10))
    print('pad %.2f x %.2f x %.2f, slot %.2f wide OPEN at the outer end'
          % (val('len') * 10, val('wid') * 10, val('t') * 10, val('slot_w') * 10))
    print('   screw at x %.2f from the case edge - the pad registers on that edge'
          % (val('slot_x') * 10))
    print('   material beside the slot: %.2f inner, %.2f each side (MIN_WALL %.2f,'
          % (inner_wall, side_wall, MIN_WALL_MM))
    print('   reported not asserted - this pad is in pure compression and carries')
    print('   nothing, so its walls are a printability question, not a load one)')
    print('COSTS 0.80 OF TAB SCREW ENGAGEMENT. The servo\'s own M2s cross 0.80 mm')
    print('   more stack before they reach the forearm pilots. Buy them 1 mm longer.')
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10,
             bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f (x2 = %.2f) | valid: %s'
          % (vol, mass, 2 * mass, body.isValid))
    print('timeline groups: %r' % (PHASES,))
