"""robotarm/grip_jaw - Fusion MCP generating script.

Rebuilds `robotarm_grip_jaw` (idempotent). PRINT TWO - the second is the
same part turned over (rotated 180 deg about Y).

Spec: specs/robotarm/grip.md - all numbers from lib/grip.py.

GRIP v3 (2026-09-29): ONE JAW = ROD-GUIDED RACK BAR + TIE + ARM.

  * the RACK is gripper_pinion's gr_ contract, 6 teeth - the stroke plus
    one pitch of mesh at each end - on the underside of a WEB
  * the web carries two ROD BLOCKS, one each side of the pinion (y), each
    bored O3.5 along x for a O3 steel rod. Two rods, not one: they fix the
    rack's centre distance to the pinion and it cannot roll into or out of
    mesh. Nothing slides plastic-on-plastic.
  * the TIE runs forward out of the body's open front to the ARM, which
    stands wholly in front of the rim and carries the TPU finger
    (2 x M3 x 16 from the arm's back, heads in counterbores, into nuts in
    the finger). Fit the finger BEFORE the jaw goes into the body.

Frame: the head frame (lib/grip.py), jaw A CLOSED at s = 0: jaw face on
x = 0, rack above the pinion with its pitch line at z = +OFFSET, teeth
toward -z. Jaw A opens toward +x.

Print: the BAR_TOP face down (z = BAR_TOP on the bed) - web, rod blocks, tie
and arm tops are one plane; teeth, rod blocks and arm grow from it as
prisms. The rod bores are small horizontals. No support.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

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
PH_RODS = 'rod blocks'
PH_ARM = 'tie and arm'
PH_FINISH = 'finish'
PHASES = [PH_RACK, PH_RODS, PH_ARM, PH_FINISH]
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
        return ups.itemByName(PREFIX + name).value      # cm

    def mm(v_cm):
        return '%.5f mm' % (v_cm * 10)

    param('face', '%.4f mm' % G.GR_FACE, 'lib/grip GR_FACE - rack face width, = pinion face')
    param('tip_z', '%.4f mm' % G.TIP_Z, 'lib/grip - tooth tips, OFFSET - addendum')
    param('root_z', '%.4f mm' % G.ROOT_Z, 'lib/grip - tooth roots, OFFSET + dedendum')
    param('bar_top', '%.4f mm' % G.BAR_TOP, 'lib/grip - the bar back, the print bed')
    param('bar_y', '%.4f mm' % G.BAR_Y, 'lib/grip - bar half depth in y')
    param('block_y0', '%.4f mm' % (G.GR_FACE / 2 + G.BAR_GAP), 'lib/grip - rod blocks stand off the pinion faces')
    param('ext_z0', '%.4f mm' % G.EXT_Z0, 'lib/grip - rod block underside, clear of the servo case')
    param('rod_y', '%.4f mm' % G.ROD_Y, 'lib/grip - rods at y +-this')
    param('rod_z', '%.4f mm' % G.ROD_Z, 'lib/grip - rod centre height')
    param('rod_bore', '%.4f mm' % G.ROD_BORE, 'lib/grip - slip bore, drawn (ASSUMED)')
    param('x_lo', '%.4f mm' % G.X_LO, 'lib/grip - inner end of the rack bar')
    param('tie_thk', '%.4f mm' % G.TIE_THK, 'lib/grip - the tie, and the bar\'s +x end')
    param('wall', '%.4f mm' % G.WALL, 'MIN_WALL')
    param('arm_y0', '%.4f mm' % G.ARM_Y0, 'lib/grip - arm back face, in front of the rim')
    param('arm_d', '%.4f mm' % G.ARM_D, 'lib/grip - arm depth in y')
    param('arm_thk', '%.4f mm' % G.ARM_THK, 'lib/grip - arm thickness in x')
    param('finger_h', '%.4f mm' % G.FINGER_H, 'lib/grip - finger height, centred on z = 0')
    param('screw_d', '%.4f mm' % G.M3['clearance'], 'M3 clearance - design_rules')
    param('cbore_d', '%.4f mm' % G.EFF_CBORE_D, 'O5.5 head + clearance')
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

    def extrude(prof, op, start_cm, dist_cm, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(start_cm)))
        inp.setDistanceExtent(False, V(mm(dist_cm)))
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

    def box(name, x0, x1, y0, y1, z0, z1, op=JOIN):
        """Drawn on XY, extruded along +z from z0 to z1."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            sk.modelToSketchSpace(P3(x0, y0, 0)), sk.modelToSketchSpace(P3(x1, y1, 0)))
        return extrude(one(sk), op, z0, z1 - z0, name)

    def hole_y(name, x, z, d, y0, y1):
        """XZ sketch: its normal is +Y, so the extent runs +y."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(x, 0, z)), d / 2)
        return extrude(one(sk), CUT, y0, y1 - y0, name)

    def hole_x(name, y, z, d, x0, x1):
        """YZ sketch: its normal is +X, so the extent runs +x."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(0, y, z)), d / 2)
        return extrude(one(sk), CUT, x0, x1 - x0, name)

    # ---- values, cm ----
    pitch = G.PITCH / 10
    add_h = G.ADD / 10
    ded_h = G.DED / 10
    off = G.OFFSET / 10
    tan_pa = math.tan(math.radians(G.GR_PA_DEG))
    tip_half = pitch / 2 / 2 - add_h * tan_pa
    root_half = pitch / 2 / 2 + ded_h * tan_pa
    x_a, x_b = G.X_A / 10, G.X_B / 10
    x_lo, x_hi = val('x_lo'), val('tie_thk')
    top, root_z, by = val('bar_top'), val('root_z'), val('bar_y')
    assert tip_half > 0, 'the tooth comes to a point'

    # ---- phase 1: the rack teeth under a full-depth web ------------------------
    t0 = design.timeline.count
    sk = sketch(comp.xZConstructionPlane, 'sk_rack_profile')
    pts = [(x_lo, top), (x_hi, top), (x_hi, off + ded_h), (x_b, off + ded_h)]
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
        lines.addByTwoPoints(sk.modelToSketchSpace(P3(a[0], 0, a[1])),
                             sk.modelToSketchSpace(P3(b[0], 0, b[1])))
    extrude(one(sk), NEW, -val('face') / 2, val('face'), 'rack_teeth')
    box('web', x_lo, x_hi, -by, by, root_z, top)
    group(t0, PH_RACK)

    # ---- phase 2: the rod blocks beside the pinion, bored for the rods ---------
    t1 = design.timeline.count
    for sy in (1, -1):
        tag = 'f' if sy > 0 else 'r'
        y0, y1 = sorted((sy * val('block_y0'), sy * by))
        box('rod_block_' + tag, x_lo, x_hi, y0, y1, val('ext_z0'), top)
        hole_x('rod_bore_' + tag, sy * val('rod_y'), val('rod_z'), val('rod_bore'),
               x_lo - val('wall'), x_hi + val('wall'))
    group(t1, PH_RODS)

    # ---- phase 3: the tie out of the cup, the arm in front of the rim ----------
    t2 = design.timeline.count
    a0, ad = val('arm_y0'), val('arm_d')
    box('tie', 0.0, x_hi, by - val('wall'), a0 + ad / 2, val('ext_z0'), top)
    box('arm', 0.0, val('arm_thk'), a0, a0 + ad, -val('finger_h') / 2, top)
    for k, sz in enumerate((-1, 1)):
        z = sz * val('screw_z')
        hole_y('finger_screw_%d' % k, val('arm_thk') / 2, z, val('screw_d'), a0 - val('wall'),
               a0 + ad + val('wall'))
        hole_y('finger_cbore_%d' % k, val('arm_thk') / 2, z, val('cbore_d'), a0 - val('wall'),
               a0 + val('cbore_h'))
    group(t2, PH_ARM)

    # ---- phase 4: the facet on the arm's outer face ----------------------------
    t3 = design.timeline.count
    body = comp.bRepBodies.item(0)
    eps = val('ef') / 10
    outer = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.x - val('arm_thk')) < eps and abs(bb.maxPoint.x - val('arm_thk')) < eps \
                and bb.minPoint.y > a0 - eps:
            outer.add(e)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(outer, V(PREFIX + 'facet'), False)
    chf.add(ci).name = 'arm_outer_facet'
    group(t3, PH_FINISH)

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
                a_ = apps.item(j)
                if all(w.lower() in a_.name.lower() for w in want):
                    body.appearance = a_
                    used = a_.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    bb = body.boundingBox
    vol = body.physicalProperties.volume * 1000
    print("body: '%s' | appearance: %s | PRINT %d, bar top down" % (body.name, used, QTY))
    print('rack %d teeth, run x %.2f..%.2f, bar %.2f..%.2f, pitch line z %.2f, web z %.3f..%.2f y +-%.2f'
          % (G.RACK_TEETH, G.X_A, G.X_B, G.X_LO, G.TIE_THK, G.OFFSET, G.ROOT_Z, G.BAR_TOP, G.BAR_Y))
    print('rod blocks |y| %.2f..%.2f z %.2f..; bores O%.1f at y +-%.2f z %.2f'
          % (G.GR_FACE / 2 + G.BAR_GAP, G.BAR_Y, G.EXT_Z0, G.ROD_BORE, G.ROD_Y, G.ROD_Z))
    print('arm y %.2f..%.2f, z %.2f..%.2f | finger: 2 x M3 x %.0f at z +/-%.1f, heads %.1f deep'
          % (G.ARM_Y0, G.FINGER_Y0, -G.FINGER_H / 2, G.BAR_TOP, G.FINGER_SCREW_L,
             G.FINGER_SCREW_Z, G.FINGER_CBORE_H))
    print('facet %.1f on %d outer-face edges' % (val('facet') * 10, outer.count))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g each | valid: %s'
          % (vol, vol * G.PETG_PRINTED_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
