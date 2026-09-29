"""robotarm/cobot_wrist_cap - Fusion MCP generating script.

Rebuilds `robotarm_cobot_wrist_cap` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py.

THE WRIST CAP: the drum from the J5 bay's wall (x +6.2) to the wrist's +x
face (x +11), closing the bay, and carrying the J4 SPIGOT - the wrist is H
at J4. The spigot (O28) runs in the forearm's J4 wall bore; the J4 gear
CENTRES on the O12 register boss on its end and bolts to it with
4 x M3 x 18 into the pilots here, from inside the forearm.
  * 3 x M3 x 12 into the body; heads COUNTERBORED - the forearm's J4 wall
    sweeps AX_GAP over this face as the wrist pitches
  * a 0.5 lead-in on the spigot's end: it enters the forearm bore easily

Print: SPLIT FACE (x +6.2) DOWN, spigot up, no support.
Frame: arm x; y = u forward along J5 from J4; z = v.
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

import lib.cobot as C  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_cobot_wrist_cap'
BODY_NAME = 'cobot_wrist_cap'
PREFIX = 'cwc_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_wrist_cap')
PH_FORM = 'cap + spigot'
PH_HOLES = 'pilots + screws'
PHASES = [PH_FORM, PH_HOLES]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
PLANE_EPS_CM = 1e-6
PRINT_NOTE = 'PRINT 1, split face down, spigot up'
EPS_CM = 1e-5
PILOT_RUNOUT = 0.5        # mm - a pilot runs this far past the screw's tip


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()

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

    j4 = C.J4
    param('x0', '%.4f mm' % C.WR_SPLIT, 'lib/cobot WR_SPLIT')
    param('x1', '%.4f mm' % C.WR_HALF, 'lib/cobot WR_HALF - the J4 face')
    param('a', '%.4f mm' % C.WR_A, 'lib/cobot WR_A')
    param('front', '%.4f mm' % C.ROT_SEAT, 'lib/cobot ROT_SEAT')
    param('spigot_od', '%.4f mm' % j4.spigot_od, 'lib/cobot J4 - runs in the forearm bore')
    param('spigot_end', '%.4f mm' % j4.x_spigot_end, 'lib/cobot J4')
    param('reg_d', '%.4f mm' % C.REG_D, 'lib/cobot REG_D - the J4 gear centres on this')
    param('reg_h', '%.4f mm' % C.REG_H, 'lib/cobot REG_H')
    param('bolt_r', '%.4f mm' % j4.bolt_r, 'lib/cobot J4')
    param('pilot_deep', '%.4f mm' % (j4.bolt_engaged(C.J4_BOLT_L, 0.0) + PILOT_RUNOUT), 'M3 x 18 through the gear')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('clear', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('cbore_d', '%.4f mm' % C.CBORE_D, 'lib/cobot CBORE_D')
    param('cbore_h', '%.4f mm' % C.CBORE_H, 'lib/cobot CBORE_H')
    param('lead_in', '0.5 mm', 'spigot end chamfer')

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
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def bodies():
        return [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]

    def extrude(profs, op, start_cm, dist_cm, name, symmetric=False):
        inp = ext.createInput(profs, op)
        if symmetric:
            inp.setSymmetricExtent(V(mm(dist_cm)), False)   # dist_cm EACH side
        else:
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(start_cm)))
            inp.setDistanceExtent(False, V(mm(dist_cm)))
        if op != NEW:
            inp.participantBodies = bodies()
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    def along_x(name, loops_mm, circles_mm, x0, x1, op, pick='largest'):
        """YZ sketch (u = y, v = z), extruded along +x from x0 to x1 (cm)."""
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        for pts in loops_mm:
            sp = [sk.modelToSketchSpace(P3(0, u / 10, v / 10)) for u, v in pts]
            for k in range(len(sp)):
                sk.sketchCurves.sketchLines.addByTwoPoints(sp[k], sp[(k + 1) % len(sp)])
        for u, v, d in circles_mm:
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(0, u / 10, v / 10)), d / 2 / 10)
        profs = adsk.core.ObjectCollection.create()
        if pick == 'all':
            for i in range(sk.profiles.count):
                profs.add(sk.profiles.item(i))
        else:
            best, bp = -1, None
            for i in range(sk.profiles.count):
                pr = sk.profiles.item(i)
                a_ = pr.areaProperties().area
                if a_ > best:
                    best, bp = a_, pr
            profs.add(bp)
        return extrude(profs, op, x0, x1 - x0, name)

    def along_u(name, u_mid_cm, half_cm, loops_xv, circles_xv, op):
        """A sketch on the plane u = u_mid (x, v in mm), cut/extruded +-half along u."""
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.xZConstructionPlane, V(mm(u_mid_cm)))
        pl = comp.constructionPlanes.add(pi)
        if abs(pl.geometry.origin.y - u_mid_cm) > PLANE_EPS_CM:        # the XZ normal may be -y
            pl.deleteMe()
            pi = comp.constructionPlanes.createInput()
            pi.setByOffset(comp.xZConstructionPlane, V(mm(-u_mid_cm)))
            pl = comp.constructionPlanes.add(pi)
        assert abs(pl.geometry.origin.y - u_mid_cm) <= PLANE_EPS_CM, 'plane at the wrong u'
        pl.name = 'pl_' + name
        sk = comp.sketches.add(pl)
        sk.name = 'sk_' + name
        for pts in loops_xv:
            sp = [sk.modelToSketchSpace(P3(x / 10, u_mid_cm, v / 10)) for x, v in pts]
            for k in range(len(sp)):
                sk.sketchCurves.sketchLines.addByTwoPoints(sp[k], sp[(k + 1) % len(sp)])
        for x, v, d in circles_xv:
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(x / 10, u_mid_cm, v / 10)),
                                                            d / 2 / 10)
        profs = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            profs.add(sk.profiles.item(i))
        return extrude(profs, op, 0.0, half_cm, name, symmetric=True)

    def clip_front(poly, u_max):
        """Clip a (u, v) polygon to u <= u_max."""
        out = []
        n = len(poly)
        for i in range(n):
            a_, b_ = poly[i], poly[(i + 1) % n]
            ina, inb = a_[0] <= u_max, b_[0] <= u_max
            if ina:
                out.append(a_)
            if ina != inb:
                t = (u_max - a_[0]) / (b_[0] - a_[0])
                out.append((u_max, a_[1] + t * (b_[1] - a_[1])))
        return out

    x0, x1, xe = val('x0'), val('x1'), val('spigot_end')
    drum = clip_front(C.ring(val('a') * 10), val('front') * 10)
    t0 = design.timeline.count
    along_x('cap', [drum], [], x0, x1, NEW)
    along_x('spigot', [], [(0.0, 0.0, val('spigot_od') * 10)], x1, xe, JOIN)
    along_x('register', [], [(0.0, 0.0, val('reg_d') * 10)], xe, xe + val('reg_h'), JOIN)
    group(t0, PH_FORM)

    t1 = design.timeline.count
    for k, az in enumerate(j4.bolt_az):
        bu, bv = val('bolt_r') * 10 * math.cos(math.radians(az)), val('bolt_r') * 10 * math.sin(math.radians(az))
        along_x('j4_pilot_%d' % k, [], [(bu, bv, val('m3_pilot') * 10)], xe - val('pilot_deep'), xe, CUT)
    for k, (u, v) in enumerate(C.WRIST_SCREWS):
        along_x('screw_%d' % k, [], [(u, v, val('clear') * 10)], x0, x1, CUT)
        along_x('cbore_%d' % k, [], [(u, v, val('cbore_d') * 10)], x1 - val('cbore_h'), x1, CUT)
    body0 = comp.bRepBodies.item(0)
    col = adsk.core.ObjectCollection.create()
    for e in body0.edges:
        eb = e.boundingBox
        if abs(eb.minPoint.x - xe) < EPS_CM and abs(eb.maxPoint.x - xe) < EPS_CM:
            if math.hypot(eb.maxPoint.y, eb.maxPoint.z) > val('spigot_od') / 2 - EPS_CM:
                col.add(e)
    if col.count:
        ci = comp.features.chamferFeatures.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(PREFIX + 'lead_in'), False)
        comp.features.chamferFeatures.add(ci).name = 'spigot_lead_in'
    group(t1, PH_HOLES)
    print('cap x %.2f..%.2f; J4 spigot O%.0f to x %.2f, register O%.0f x %.1f; %d x M3 pilots %.1f deep at r %.0f; '
          '%d counterbored screws; lead-in edges %d'
          % (x0 * 10, x1 * 10, j4.spigot_od, xe * 10, C.REG_D, C.REG_H, len(j4.bolt_az), val('pilot_deep') * 10,
             j4.bolt_r, len(C.WRIST_SCREWS), col.count))

    assert comp.bRepBodies.count == 1, '%s came out in %d pieces' % (COMPONENT, comp.bRepBodies.count)
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
    v_ = body.volume * 1000
    print("body: '%s' | appearance: %s | %s" % (body.name, used, PRINT_NOTE))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
