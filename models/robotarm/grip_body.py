"""robotarm/grip_body - Fusion MCP generating script.

Rebuilds `robotarm_grip_body` (idempotent). PRINT ONE. Spec:
specs/robotarm/grip.md - all numbers from lib/grip.py.

THE HEAD, IN ONE PIECE (grip v4, 2026-09-29: v3 shrunk to the cobot wrist -
lib/grip docstring). Replaces the two grip_shell
halves. A 12-sided prism round the J5 roll axis - the base's dodecagon
again (Jonathan: "more circular with polygonal lines for texture") - with
an OPEN FRONT CUP. Everything goes in from the front, in this order:

  1. bolt the EMPTY body to the rotator's neck: 4 x M3 x 8 on r 7, heads
     down the four access bores (inside the servo pocket) with a long 2.5 key
  2. SG90 down its pocket - through the SERVO SLOT, the cup is narrower
     than the servo in v4 - plug first out through the side slot; the lead
     lies in the groove in the pocket's end wall; 2 x M2 x 8 through the tabs
     into the ledge
  3. gripper_pinion onto the spline (servo centred), screw + washer
  4. the two jaws (fingers already on), both at the same opening
  5. four O3 x 47 steel rods (lib/grip ROD_L) through the side walls and the jaws: slip hole
     on one side, press hole on the other, pressed flush

Print: BACK FACE DOWN, no support. The cup, the servo pocket and the access
bores all open upward; the rod holes are small horizontals; the back taper
is a 45 deg chamfer; the lead slot's roof is an 8 mm bridge; the two
lightening lunes are closed under the rim by a ~14 mm bridge across z.

Frame: the head frame (lib/grip.py).
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
COMPONENT = 'robotarm_grip_body'
BODY_NAME = 'grip_body'
PREFIX = 'gb3_'
APPEARANCE_HINTS = hints_for('grip_body')
PH_FORM = 'dodecagon'
PH_CUP = 'cup + servo bay'
PH_FIX = 'rotator + rods'
PH_LIGHT = 'lighten'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_CUP, PH_FIX, PH_LIGHT, PH_FINISH]
PLUG_W = 8.0         # ASSUMED - an SG90's 3-pin plug passes an 8 x 8 slot
PILOT_DEEP = 6.0     # M2 x 8 through a 2.4 tab: 5.6 of bite + a hair


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

    param('r_out', '%.4f mm' % G.R_OUT, 'lib/grip - outer vertex radius of the 12-gon')
    param('back_y', '%.4f mm' % G.SHELL_BACK_Y, 'lib/grip - the rotator face')
    param('rim_y', '%.4f mm' % G.RIM_Y, 'lib/grip - the cup rim, in front of the jaws\' rod blocks')
    param('back_chamfer', '%.4f mm' % G.BACK_CHAMFER, 'lib/grip - taper down to the O21 neck')
    param('front_facet', '%.4f mm' % G.FRONT_FACET, 'lib/grip - the rim\'s outer edge')
    param('w_in', '%.4f mm' % G.W_IN, 'lib/grip - cavity half width: the racks\' full travel + free')
    param('z_in', '%.4f mm' % G.Z_IN, 'lib/grip - cavity half height: rack back + free')
    param('core_y0', '%.4f mm' % G.CORE_Y0, 'lib/grip - full cavity floor, just behind the pinion')
    param('cav_y0', '%.4f mm' % G.CAV_Y0, 'lib/grip - slab floor for the rear rod blocks')
    param('slab_z0', '%.4f mm' % (G.EXT_Z0 - G.FREE), 'lib/grip - the slabs start above the servo')
    param('pocket_x0', '%.4f mm' % (G.CASE_NEAR - G.LOC / 2), 'SG90 pocket, shaft (lead) end')
    param('pocket_x1', '%.4f mm' % (G.CASE_FAR + G.LOC / 2), 'SG90 pocket, far end')
    param('pocket_z', '%.4f mm' % (G.SERVO.case_w / 2 + G.LOC / 2), 'SG90 pocket half height')
    param('case_bot', '%.4f mm' % (G.CASE_BOT_Y - G.LOC / 2), 'SG90 pocket floor')
    param('tab_y', '%.4f mm' % G.TAB_Y, 'the tab ledge = the SG90 datum')
    param('tab_x0', '%.4f mm' % (G.CASE_NEAR - G.TAB_OVER - G.LOC / 2), 'tab relief, near end')
    param('tab_x1', '%.4f mm' % (G.CASE_FAR + G.TAB_OVER + G.LOC / 2), 'tab relief, far end')
    param('pilot_d', '%.4f mm' % G.M2['pilot'], 'M2 self-tapper pilot - design_rules')
    param('pilot_deep', '%.4f mm' % PILOT_DEEP, 'into the ledge behind each tab')
    param('lead_y', '%.4f mm' % G.LEAD_Y, 'lib/servo lead datum, head frame')
    param('lead_r', '%.4f mm' % G.LEAD_R, 'lead groove / bundle + loc')
    param('plug_w', '%.4f mm' % PLUG_W, 'side slot for the plug, square')
    param('wall', '%.4f mm' % G.WALL, 'MIN_WALL')
    param('eff_r', '%.4f mm' % G.EFF_BOLT_R, 'lib/cobot ROT_BOLT_R - the neck\'s 4 x M3')
    param('eff_cbore_d', '%.4f mm' % G.EFF_CBORE_D, 'passes the O5.5 head from the front')
    param('eff_cbore_h', '%.4f mm' % G.EFF_CBORE_H, 'head recess in the back wall')
    param('bolt_d', '%.4f mm' % G.M3['clearance'], 'M3 clearance')
    param('rod_y', '%.4f mm' % G.ROD_Y, 'lib/grip - rods at y +-this')
    param('rod_z', '%.4f mm' % G.ROD_Z, 'lib/grip - rods at z +-this')
    param('rod_bore', '%.4f mm' % G.ROD_BORE, 'slip hole, drawn - lib/grip ASSUMED')
    param('rod_press', '%.4f mm' % G.ROD_PRESS, 'press hole, drawn - lib/grip ASSUMED')
    param('light_y0', '%.4f mm' % G.LIGHT_Y0, 'lib/grip - hollow floor, in front of the back taper')
    param('light_y1', '%.4f mm' % G.LIGHT_Y1, 'lib/grip - the lunes stop a skin short of the rim')
    param('slab_deep_z0', '%.4f mm' % G.SLAB_DEEP_Z0, 'lib/grip - deep slabs keep a wall round the servo')
    param('side_x1', '%.4f mm' % G.SIDE_X1, 'lib/grip - side pocket stops a wall short of the tab ledge')

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

    def box_y(name, x0, x1, z0, z1, y0, y1, op=CUT):
        """A box drawn on XZ (normal +Y) and extruded along +y from y0 to y1."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            sk.modelToSketchSpace(P3(x0, 0, z0)), sk.modelToSketchSpace(P3(x1, 0, z1)))
        return extrude(one(sk), op, y0, y1 - y0, name)

    def hole_y(name, x, z, d, y0, y1):
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(x, 0, z)), d / 2)
        return extrude(one(sk), CUT, y0, y1 - y0, name)

    def hole_x(name, y, z, d, x0, x1):
        """YZ sketch: its normal is +X, so the extent runs +x."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(0, y, z)), d / 2)
        return extrude(one(sk), CUT, x0, x1 - x0, name)

    ro, by, ry = val('r_out'), val('back_y'), val('rim_y')
    wi, zi = val('w_in'), val('z_in')
    tol = G.EF / 100

    # ---- phase 1: the dodecagon prism ----------------------------------------
    t0 = design.timeline.count
    sk = sketch(comp.xZConstructionPlane, 'sk_dodecagon')
    pts = [sk.modelToSketchSpace(P3(x / 10, 0, z / 10)) for x, z in G.dodecagon(ro * 10)]
    for k in range(G.SIDES):
        sk.sketchCurves.sketchLines.addByTwoPoints(pts[k], pts[(k + 1) % G.SIDES])
    extrude(one(sk), NEW, by, ry - by, 'dodecagon')
    body = comp.bRepBodies.item(0)
    back = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.y - by) < tol and abs(bb.maxPoint.y - by) < tol:
            back.add(e)
    assert back.count == G.SIDES, 'found %d back edges' % back.count
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(back, V(PREFIX + 'back_chamfer'), False)
    chf.add(ci).name = 'back_taper'
    group(t0, PH_FORM)

    # ---- phase 2: the cup, the slabs, the servo bay -----------------------------
    t1 = design.timeline.count
    box_y('cup', -wi, wi, -zi, zi, val('core_y0'), ry + val('wall'))
    for sz in (1, -1):
        z0, z1 = sorted((sz * val('slab_z0'), sz * zi))
        box_y('slab_%s' % ('a' if sz > 0 else 'b'), -wi, wi, z0, z1, val('cav_y0'),
              val('core_y0') + tol)
    pz = val('pocket_z')
    box_y('servo_pocket', val('pocket_x0'), val('pocket_x1'), -pz, pz, val('case_bot'),
          val('core_y0') + tol)
    box_y('tab_relief', val('tab_x0'), val('tab_x1'), -pz, pz, val('tab_y'), val('core_y0') + tol)
    # v4: the cup is narrower than the servo - its way in is a slot at the
    # servo's own height, clear of both racks (lib/grip SERVO_SLOT_X1)
    box_y('servo_slot', -wi, val('tab_x1'), -pz, pz, val('core_y0'), ry + val('wall'))
    for k, hx in enumerate(G.TAB_HOLE_X):
        hole_y('tab_pilot_%d' % k, hx / 10, 0.0, val('pilot_d'), val('tab_y') - val('pilot_deep'),
               val('tab_y') + tol)
    # the lead: a groove down the pocket's end wall, BELOW the tab pilot, and a
    # plug-sized slot out through the -x side at the lead's own height
    lr, pw = val('lead_r'), val('plug_w')
    x_end = val('pocket_x0')
    box_y('lead_groove', x_end - 2 * lr, x_end + tol, -pz, -pz + 2 * lr,
          val('lead_y') - lr, val('core_y0') + tol)
    box_y('plug_slot', -ro - val('wall'), x_end + tol, -pz, -pz + pw,
          val('lead_y') - pw / 2, val('lead_y') + pw / 2)
    group(t1, PH_CUP)

    # ---- phase 3: rotator screws, and the four rods ------------------------------
    t2 = design.timeline.count
    for k, az in enumerate(G.EFF_BOLT_AZ):
        x, z = val('eff_r') * math.cos(math.radians(az)), val('eff_r') * math.sin(math.radians(az))
        tag = '%d' % k
        hole_y('eff_screw_' + tag, x, z, val('bolt_d'), by - val('wall'), val('case_bot'))
        hole_y('eff_access_' + tag, x, z, val('eff_cbore_d'),
               val('case_bot') - val('eff_cbore_h'), val('core_y0') + tol)
    # rod A (upper, z > 0) slips in from +x and presses at -x; rod B mirrored
    far = ro + val('wall')
    for sz in (1, -1):
        for sy in (1, -1):
            y, z = sy * val('rod_y'), sz * val('rod_z')
            tag = '%s%s' % ('a' if sz > 0 else 'b', 'f' if sy > 0 else 'r')
            hole_x('rod_slip_' + tag, y, z, val('rod_bore'),
                   0.0 if sz > 0 else -far, far if sz > 0 else 0.0)
            hole_x('rod_press_' + tag, y, z, val('rod_press'),
                   -far if sz > 0 else 0.0, 0.0 if sz > 0 else far)
    group(t2, PH_FIX)

    # ---- phase 3b: lightening - two lunes, deep slabs, a side pocket ------------
    t25 = design.timeline.count
    ly0, ly1 = val('light_y0'), val('light_y1')
    for sz in (1, -1):
        sk = sketch(comp.xZConstructionPlane, 'sk_lune_%s' % ('a' if sz > 0 else 'b'))
        pts = [sk.modelToSketchSpace(P3(x / 10, 0, sz * z / 10)) for x, z in G.lune_outline()]
        for k in range(len(pts)):
            sk.sketchCurves.sketchLines.addByTwoPoints(pts[k], pts[(k + 1) % len(pts)])
        extrude(one(sk), CUT, ly0, ly1 - ly0, 'lune_%s' % ('a' if sz > 0 else 'b'))
        z0, z1 = sorted((sz * val('slab_deep_z0'), sz * zi))
        box_y('slab_deep_%s' % ('a' if sz > 0 else 'b'), -wi, wi, z0, z1, ly0, val('cav_y0') + tol)
    box_y('side_pocket', -wi, val('side_x1'), -zi, zi, ly0, val('core_y0') + tol)
    group(t25, PH_LIGHT)

    # ---- phase 4: the rim's outer facet -------------------------------------------
    t3 = design.timeline.count
    body = comp.bRepBodies.item(0)
    rim = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.y - ry) < tol and abs(bb.maxPoint.y - ry) < tol:
            mid_r = math.hypot((bb.minPoint.x + bb.maxPoint.x) / 2, (bb.minPoint.z + bb.maxPoint.z) / 2)
            if mid_r > (G.A_OUT - G.BODY_WALL / 2) / 10:   # outer flats only, not the cup mouth or servo slot
                rim.add(e)
    assert rim.count == G.SIDES, 'found %d rim edges' % rim.count
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(rim, V(PREFIX + 'front_facet'), False)
    chf.add(ci).name = 'rim_facet'
    group(t3, PH_FINISH)

    assert comp.bRepBodies.count == 1, 'the body came out in %d pieces' % comp.bRepBodies.count
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
    print("body: '%s' | appearance: %s | PRINT 1, back face down" % (body.name, used))
    print('12-gon, %.1f across vertices (on x and z), %.1f across flats, y %.1f..%.1f; back taper %.1f, rim facet %.1f on %d edges'
          % (2 * G.R_OUT, 2 * G.A_OUT, G.SHELL_BACK_Y, G.RIM_Y, G.BACK_CHAMFER, G.FRONT_FACET, rim.count))
    print('cup x +-%.1f z +-%.2f from y %.1f; slabs |z| >= %.2f back to y %.1f'
          % (G.W_IN, G.Z_IN, G.CORE_Y0, G.EXT_Z0 - G.FREE, G.CAV_Y0))
    print('SG90: tab ledge y %.2f, pilots O%.1f at x %s, lead groove + %.0f mm plug slot at y %.1f'
          % (G.TAB_Y, G.M2['pilot'], ['%.2f' % v for v in G.TAB_HOLE_X], PLUG_W, G.LEAD_Y))
    print('neck: %d x M3 x %.0f on r %.0f, heads %.1f deep, access O%.1f down the empty servo pocket'
          % (len(G.EFF_BOLT_AZ), G.EFF_SCREW_L, G.EFF_BOLT_R, G.EFF_CBORE_H, G.EFF_CBORE_D))
    print('rods: 4 x O%.0f x %.1f at y +-%.2f z +-%.2f - slip O%.1f one side, press O%.1f the other'
          % (G.ROD_D, G.ROD_L, G.ROD_Y, G.ROD_Z, G.ROD_BORE, G.ROD_PRESS))
    print('lightening: lunes |z| >= %.1f inside apothem %.1f, y %.1f..%.1f; slabs deepened |z| >= %.1f; side pocket x <= %.1f'
          % (G.LUNE_Z0, G.A_LUNE, G.LIGHT_Y0, G.LIGHT_Y1, G.SLAB_DEEP_Z0, G.SIDE_X1))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s'
          % (vol, vol * G.PETG_PRINTED_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
