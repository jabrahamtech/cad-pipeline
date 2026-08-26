"""robotarm/servo_adapter - Fusion MCP generating script.

Rebuilds `robotarm_servo_adapter` (idempotent). Puts a SMALL servo into a
mount cut for a BIG one, without touching the mount.

This part exists because of a wrong answer. Asked whether it would be easier
to take a donor arm and change its motor mounts, the answer given was that
re-cutting a pocket means FILLING the old one first, and that filling a
pocket is CAD you would be doing anyway. That is true if you insist on
modifying the donor. You should not. The small servo is smaller in every
plan dimension, so it drops straight into the big one's hole; all that is
actually wrong is the HEIGHT of the output shaft, and a plate fixes that.

  MG90S into an MG995 / MG996R mount: the case is 16.0 x 7.5 mm smaller in
  plan, and the shaft sits 2.6 mm low. The adapter is a 2.6 mm plate.
  SG90 into the same mount: 3.2 mm.

THE ONE DIMENSION THAT MATTERS is `sa_lift`. A donor arm's joint axis is
wherever the big servo's output shaft was. Put the small servo's shaft
anywhere else and every link length downstream is wrong. So the plate is
exactly as thick as the difference between the two servos' shaft heights
ABOVE THEIR OWN TAB PLANE - which is the datum both of them are actually
held by (lib/servo.py: THE DATUM IS THE TAB PLANE, NOT THE CASE).

Local frame: origin ON THE OUTPUT SHAFT AXIS, which is the thing being
preserved. +Z along the shaft, +Y along the case length away from the shaft
end, +X across. Both servos are laid out from this same origin, which is why
their tab patterns come out concentric-ish rather than centred on each other.

Print orientation: PLATE FACE DOWN, built +Z. Bosses are then vertical
prisms and the window a vertical hole. No support.
"""

import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]
from lib.servo import CATALOG  # noqa: E402

DONOR = 'MG995'       # what the mount was cut for
TARGET = 'MG90S'      # what you actually have

COMPONENT = 'robotarm_servo_adapter'
BODY_NAME = 'servo_adapter'
PREFIX = 'sa_'
STYLE = 'sty_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = [('plastic', 'black'), ('paint', 'black'), ('black',), ('plastic',)]
PHASES = ['plate', 'target servo', 'donor interface', 'finish']


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    big, small = CATALOG[DONOR], CATALOG[TARGET]

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')

    lift_mm = ((big.total_h - big.tab_plane_z) - (small.total_h - small.tab_plane_z))
    param('lift', '%.3f mm' % lift_mm,
          'plate thickness = how much LOWER the %s shaft sits than the %s it is\n'
          '           replacing, both measured above their own tab plane. This is the\n'
          '           only dimension that has to be right: it is what keeps the donor\n'
          '           arm\'s joint axis where its link lengths assume it is.'
          % (TARGET, DONOR))
    assert lift_mm > 0, (
        '%s stands TALLER than %s above the tab plane - the small servo would have '
        'to sink into the mount, which a plate cannot do' % (TARGET, DONOR))

    param('donor_pitch', '%.3f mm' % big.tab_hole_pitch,
          '%s mounting hole centres' % DONOR)
    param('donor_shaft_end', '%.3f mm' % big.shaft_from_end,
          '%s shaft to the near end of its case' % DONOR)
    param('donor_case_l', '%.3f mm' % big.case_l, '%s case length' % DONOR)
    param('donor_case_w', '%.3f mm' % big.case_w, '%s case width' % DONOR)
    param('donor_bolt', '3.4 mm', 'M3 clearance for the donor screws - design_rules')

    param('case_l', '%.3f mm' % small.case_l, '%s case length' % TARGET)
    param('case_w', '%.3f mm' % small.case_w, '%s case width' % TARGET)
    param('shaft_end', '%.3f mm' % small.shaft_from_end,
          '%s shaft to the near end of its case' % TARGET)
    param('pitch', '%.3f mm' % small.tab_hole_pitch, '%s mounting hole centres' % TARGET)
    param('pilot', '1.8 mm', 'self-tapping pilot for the %s screws' % TARGET)
    param('boss_d', '5.0 mm', 'boss round each pilot, for thread engagement')
    param('boss_h', '4.0 mm',
          'how far the bosses hang DOWN into the donor cavity. There is room -\n'
          '           the %s hangs %.1f mm below its tab plane and the %s only %.1f -\n'
          '           but the donor may have ribs in there. CHECK IT before printing.'
          % (DONOR, big.tab_plane_z, TARGET, small.tab_plane_z))
    param('margin', '2.5 mm', 'material round the outermost hole')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
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
    assert comp.name == COMPONENT, 'component came back as %r' % comp.name
    ext = comp.features.extrudeFeatures
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                sk.name + ': expected %d, got %d' % (expected, sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, z0, dz, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0))
        inp.setDistanceExtent(False, V(dz))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def mpt(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def rect(name, x0, x1, y0, y1, z0, dz, op):
        sk = sketch('sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0), mpt(sk, x1, y1))
        return extrude(profiles(sk, expected=1), op, z0, dz, name)

    def disc(name, x, y, d, z0, dz, op):
        sk = sketch('sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x, y), d / 2)
        return extrude(profiles(sk, expected=1), op, z0, dz, name)

    # ---- layout, both servos from the SAME shaft-axis origin ----------------
    d_case_y0 = -val('donor_shaft_end')
    d_case_y1 = d_case_y0 + val('donor_case_l')
    d_mid = (d_case_y0 + d_case_y1) / 2
    d_holes = (d_mid - val('donor_pitch') / 2, d_mid + val('donor_pitch') / 2)

    t_case_y0 = -val('shaft_end')
    t_case_y1 = t_case_y0 + val('case_l')
    t_mid = (t_case_y0 + t_case_y1) / 2
    t_holes = (t_mid - val('pitch') / 2, t_mid + val('pitch') / 2)

    assert val('case_l') < val('donor_case_l') and val('case_w') < val('donor_case_w'), (
        'the target servo is not smaller in plan than the donor - it will not drop in')
    for h in t_holes:
        assert not (t_case_y0 - val('tol') < h < t_case_y1 + val('tol')), (
            'a target pilot lands inside its own case window')

    y_lo = min(min(d_holes), min(t_holes)) - val('margin')
    y_hi = max(max(d_holes), max(t_holes)) + val('margin')
    x_half = val('donor_case_w') / 2 + val('margin')

    # ---- phase 1: plate ------------------------------------------------------
    t0 = design.timeline.count
    rect('plate', -x_half, x_half, y_lo, y_hi, '0.0 mm', PREFIX + 'lift', NEW)
    for i, y in enumerate(t_holes):
        disc('boss_%d' % i, 0.0, y, val('boss_d'),
             '-' + PREFIX + 'boss_h', PREFIX + 'boss_h', JOIN)
    if design.timeline.count - t0 > 1:
        design.timeline.timelineGroups.add(t0, design.timeline.count - 1).name = PHASES[0]

    # ---- phase 2: the target servo ------------------------------------------
    t1 = design.timeline.count
    rect('case_window', -(val('case_w') + val('loc')) / 2, (val('case_w') + val('loc')) / 2,
         t_case_y0 - val('loc') / 2, t_case_y1 + val('loc') / 2,
         '-' + PREFIX + 'boss_h', PREFIX + 'boss_h + ' + PREFIX + 'lift', CUT)
    for i, y in enumerate(t_holes):
        disc('pilot_%d' % i, 0.0, y, val('pilot'),
             '-' + PREFIX + 'boss_h', PREFIX + 'boss_h + ' + PREFIX + 'lift', CUT)
    if design.timeline.count - t1 > 1:
        design.timeline.timelineGroups.add(t1, design.timeline.count - 1).name = PHASES[1]

    # ---- phase 3: the donor interface ---------------------------------------
    t2 = design.timeline.count
    for i, y in enumerate(d_holes):
        disc('donor_bolt_%d' % i, 0.0, y, val('donor_bolt'),
             '0.0 mm', PREFIX + 'lift', CUT)
    if design.timeline.count - t2 > 1:
        design.timeline.timelineGroups.add(t2, design.timeline.count - 1).name = PHASES[2]

    # ---- phase 4: finish -----------------------------------------------------
    t3 = design.timeline.count
    col = adsk.core.ObjectCollection.create()
    for e in comp.bRepBodies.item(0).edges:
        bb = e.boundingBox
        if abs(bb.minPoint.z) < val('tol') and abs(bb.maxPoint.z) < val('tol'):
            col.add(e)
    if col.count:
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = 'bed_face_chamfer'
    if design.timeline.count - t3 > 1:
        design.timeline.timelineGroups.add(t3, design.timeline.count - 1).name = PHASES[3]

    # ---- identity + diagnostics ---------------------------------------------
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

    bb = body.boundingBox
    print('body: %r | %s -> %s | appearance: %s' % (body.name, DONOR, TARGET, used))
    print('LIFT %.2f mm - the plate thickness, and the only dimension that has to '
          'be right' % (val('lift') * 10))
    print('donor screws at y %.1f / %.1f (%.1f c-c, %.1f clearance)' % (
        d_holes[0] * 10, d_holes[1] * 10, val('donor_pitch') * 10,
        val('donor_bolt') * 10))
    print('target screws at y %.1f / %.1f (%.1f c-c, %.1f pilot in %.1f of boss)' % (
        t_holes[0] * 10, t_holes[1] * 10, val('pitch') * 10, val('pilot') * 10,
        (val('boss_h') + val('lift')) * 10))
    print('case window %.1f x %.1f | plate %.1f x %.1f x %.2f' % (
        (val('case_w') + val('loc')) * 10, (val('case_l') + val('loc')) * 10,
        x_half * 20, (y_hi - y_lo) * 10, val('lift') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
