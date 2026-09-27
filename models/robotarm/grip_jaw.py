"""robotarm/grip_jaw - Fusion MCP generating script.

Rebuilds `robotarm_grip_jaw` (idempotent). PRINT TWO - the second is the
same part turned over (rotated 180 deg about Y).

Spec: specs/robotarm/grip.md - all numbers from lib/grip.py.

ONE JAW = RACK + TIE + ARM. The rack is gripper_rack_jaw's, tooth for
tooth (same gr_ contract, same 8 teeth, same run), so gripper_pinion drives
it unchanged. What is new is everything in front of the rack:

  * the TIE leaves the rack at its back, above the tooth roots, and passes
    FORWARD through a slot in the shell's front wall. The wall keeps a lip
    under the teeth over the whole channel, so a pull on the finger cannot
    walk the rack forward off the pinion - the old open mouth could.
  * the ARM stands wholly IN FRONT of the shell, so it never sweeps through
    either shell half; it hangs from the tie down across the split plane to
    carry the finger centred on it.
  * the FINGER bolts to the arm's front face with 2 x M3 x 16 from the
    arm's back, heads in counterbores, into nuts trapped in the TPU finger.
    Fit the finger BEFORE the jaw slides into the shell.

Frame: the head frame (lib/grip.py) with the jaw CLOSED at s = 0: jaw face
on x = 0, rack pitch line at z = +OFFSET, teeth toward -z.

Print orientation: RACK BACK DOWN (z = BACK_Z on the bed), built -z. The
rack back, tie top and arm top are one plane; teeth, tie and arm then grow
down as prisms. No support.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

import lib.grip as G  # noqa: E402
from lib.palette import hints_for  # noqa: E402

MATERIAL_NAME = 'PET Plastic'
COMPONENT = 'robotarm_grip_jaw'
BODY_NAME = 'grip_jaw'
PREFIX = 'gj_'
APPEARANCE_HINTS = hints_for('grip_jaw')
PH_RACK = 'rack bar'
PH_ARM = 'tie and arm'
PH_FINISH = 'finish'
PHASES = [PH_RACK, PH_ARM, PH_FINISH]
QTY = 2


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    G.check()

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value

    param('face', '%.4f mm' % G.GR_FACE, 'lib/grip GR_FACE - rack face width, = pinion face')
    param('tip_z', '%.4f mm' % G.TIP_Z, 'lib/grip - tooth tips, OFFSET - addendum')
    param('root_z', '%.4f mm' % G.ROOT_Z, 'lib/grip - tooth roots, OFFSET + dedendum')
    param('back_z', '%.4f mm' % G.BACK_Z, 'lib/grip - rack back, the print bed')
    param('x_lo', '%.4f mm' % G.X_LO, 'lib/grip - inner end of the rack bar')
    param('arm_y0', '%.4f mm' % G.ARM_Y0, 'lib/grip - arm back face, clear of the pinion screw')
    param('arm_d', '%.4f mm' % G.ARM_D, 'lib/grip - arm depth in y')
    param('arm_thk', '%.4f mm' % G.ARM_THK, 'lib/grip - arm thickness in x')
    param('tie_thk', '%.4f mm' % G.TIE_THK, 'lib/grip - the tie through the front-wall slot')
    param('finger_h', '%.4f mm' % G.FINGER_H, 'lib/grip - finger height, centred on z = 0')
    param('screw_d', '%.4f mm' % G.M3['clearance'], 'M3 clearance - design_rules')
    param('cbore_d', '%.4f mm' % (G.EFF_CBORE_D), 'O5.5 head + clearance')
    param('cbore_h', '%.4f mm' % G.FINGER_CBORE_H, 'lib/grip - head recess in the arm back')
    param('screw_z', '%.4f mm' % G.FINGER_SCREW_Z, 'lib/grip - finger screws at z +/- this')
    param('facet', PREFIX + 'arm_thk / 3', '_style.md rule 1, scaled to the 9 mm arm')
    param('ef', '%.4f mm' % G.EF, 'elephant foot - design_rules')

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
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def one(sk):
        assert sk.profiles.count == 1, '%s made %d profiles' % (sk.name, sk.profiles.count)
        return sk.profiles.item(0)

    def extrude(prof, op, start_expr, dist_expr, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x, y, z):
        return sk.modelToSketchSpace(P3(x, y, z))

    def box(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk, x0, y0, 0), mpt(sk, x1, y1, 0))
        return extrude(one(sk), op, z0_expr, dz_expr, name)

    def hole_y(name, x, z, d, y0_expr, dy_expr):
        """XZ sketch: its normal is +Y in Fusion, so the extent runs +y."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x, 0, z), d / 2)
        return extrude(one(sk), CUT, y0_expr, dy_expr, name)

    # ---- values, cm ----
    pitch = G.PITCH / 10
    add_h = G.ADD / 10
    ded_h = G.DED / 10
    off = G.OFFSET / 10
    tan_pa = math.tan(math.radians(G.GR_PA_DEG))
    tip_half = pitch / 2 / 2 - add_h * tan_pa
    root_half = pitch / 2 / 2 + ded_h * tan_pa
    x_a, x_b = G.X_A / 10, G.X_B / 10
    x_lo = val('x_lo')
    x_hi = val('arm_thk')                  # the bar runs out to the arm's outer face
    assert tip_half > 0, 'the tooth comes to a point'

    # ---- phase 1: the rack bar (gripper_rack_jaw's teeth, lifted by OFFSET) ----
    t0 = design.timeline.count
    sk = sketch(comp.xZConstructionPlane, 'sk_rack_profile')
    pts = [(x_lo, val('back_z')), (x_hi, val('back_z')), (x_hi, off + ded_h), (x_b, off + ded_h)]
    for i in range(G.RACK_TEETH - 1, -1, -1):
        xc = x_a + (2 * i + 1) * pitch / 2
        pts.append((xc + root_half, off + ded_h))
        pts.append((xc + tip_half, val('tip_z')))
        pts.append((xc - tip_half, val('tip_z')))
        pts.append((xc - root_half, off + ded_h))
    pts.append((x_a, off + ded_h))
    pts.append((x_lo, off + ded_h))
    lines = sk.sketchCurves.sketchLines
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        lines.addByTwoPoints(mpt(sk, a[0], 0, a[1]), mpt(sk, b[0], 0, b[1]))
    extrude(one(sk), NEW, '-' + PREFIX + 'face / 2', PREFIX + 'face', 'rack_bar')
    group(t0, PH_RACK)

    # ---- phase 2: tie forward through the wall slot, arm in front ----
    t1 = design.timeline.count
    box('tie', 0.0, val('tie_thk'), -val('face') / 2, val('arm_y0') + val('arm_d') / 2,
        PREFIX + 'root_z', PREFIX + 'back_z - ' + PREFIX + 'root_z', JOIN)
    box('arm', 0.0, val('arm_thk'), val('arm_y0'), val('arm_y0') + val('arm_d'),
        '-' + PREFIX + 'finger_h / 2', PREFIX + 'back_z + ' + PREFIX + 'finger_h / 2', JOIN)
    for k, sz in enumerate((-1, 1)):
        z = sz * val('screw_z')
        hole_y('finger_screw_%d' % k, val('arm_thk') / 2, z, val('screw_d'),
               PREFIX + 'arm_y0 - 1 mm', PREFIX + 'arm_d + 2 mm')
        hole_y('finger_cbore_%d' % k, val('arm_thk') / 2, z, val('cbore_d'),
               PREFIX + 'arm_y0 - 1 mm', PREFIX + 'cbore_h + 1 mm')
    group(t1, PH_ARM)

    # ---- phase 3: the facet on the arm's outer face, elephant foot on the bed ----
    t2 = design.timeline.count
    body = comp.bRepBodies.item(0)
    eps = val('ef') / 10
    outer = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.x - val('arm_thk')) < eps and abs(bb.maxPoint.x - val('arm_thk')) < eps \
                and bb.minPoint.y > val('arm_y0') - eps:
            outer.add(e)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(outer, V(PREFIX + 'facet'), False)
    f = chf.add(ci)
    f.name = 'arm_outer_facet'
    group(t2, PH_FINISH)

    assert comp.bRepBodies.count == 1, 'the jaw came out in %d pieces' % comp.bRepBodies.count
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
    vol = body.physicalProperties.volume * 1000
    print("body: '%s' | appearance: %s | PRINT %d, rack back down" % (body.name, used, QTY))
    print('rack %d teeth, run x %.2f..%.2f, bar %.2f..%.2f, pitch line z %.2f'
          % (G.RACK_TEETH, G.X_A, G.X_B, x_lo * 10, x_hi * 10, G.OFFSET))
    print('tie z %.3f..%.3f through the front-wall slot | arm y %.2f..%.2f, z %.2f..%.3f'
          % (G.ROOT_Z, G.BACK_Z, G.ARM_Y0, G.ARM_Y0 + G.ARM_D, -G.FINGER_H / 2, G.BACK_Z))
    print('finger: 2 x M3 x %.0f at z +/-%.1f, heads %.1f deep in the arm back'
          % (G.FINGER_SCREW_L, G.FINGER_SCREW_Z, G.FINGER_CBORE_H))
    print('facet %.1f on %d outer-face edges' % (val('facet') * 10, outer.count))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g each | valid: %s'
          % (vol, vol * G.PETG_PRINTED_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
