"""robotarm/cobot_j2_cap - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j2_cap` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py (the J2 spring block).

THE J2 COUNTERBALANCE CAP: a 12-gon cup (apothem 27.5 - the arm's own
section) standing on the upper arm's cover over J2, holding the centring
torsion spring (Century Spring TO-5201RCS). It is UPPER-ARM-fixed; the J2
gear's shaft (tower-fixed) comes up through its floor and carries the two
hub discs.
  * its two PINS (columns tied to the wall by ribs) hold whichever leg the
    hub is not pushing - both sit under the legs' line, on the far sides
  * 3 x M3 x 8 through the floor (counterbored) into heat-set inserts in the
    cover; three LUGS outside the wall take the lid's 3 x M3 x 10
  * the J2 encoder's wires: down a channel in the BUMP outside the wall, a
    groove under the floor, into the arm through the cover

Print: FLOOR DOWN, no support.
Frame: the upper arm's (arm x; y = u; z = v).
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

COMPONENT = 'robotarm_cobot_j2_cap'
BODY_NAME = 'cobot_j2_cap'
PREFIX = 'cjc_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j2_cap')
PH_0 = 'floor + wall + lugs'
PH_1 = 'pins'
PH_2 = 'holes + wire path'
PHASES = [PH_0, PH_1, PH_2]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
RIB_W_FRAC = 0.8                   # a pin's rib is 0.8 of the pin's width
PLANE_EPS_CM = 1e-6
PRINT_NOTE = 'PRINT 1, floor down'


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


    param('x0', '%.4f mm' % C.CAP_X0, 'lib/cobot CAP_X0 - on the cover\'s outer face')
    param('floor_t', '%.4f mm' % C.CAP_FLOOR_T, 'lib/cobot CAP_FLOOR_T')
    param('x_top', '%.4f mm' % C.LID[0], 'lib/cobot - the lid sits here')
    param('a', '%.4f mm' % C.CAP_A, 'lib/cobot CAP_A')
    param('wall', '%.4f mm' % C.CAP_WALL, 'lib/cobot CAP_WALL')
    param('pin_d', '%.4f mm' % C.SPR_PIN_D, 'lib/cobot SPR_PIN_D')
    param('lug_r', '%.4f mm' % C.LID_LUG_R, 'lib/cobot LID_LUG_R')
    param('bump_d', '%.4f mm' % C.CAP_BUMP_D, 'lib/cobot CAP_BUMP_D')
    param('wire_d', '%.4f mm' % C.CAP_WIRE_D, 'lib/cobot CAP_WIRE_D')
    param('groove_h', '2.0 mm', 'the wire groove under the floor')
    param('shaft_bore', '%.4f mm' % C.SHAFT_BORE, 'lib/cobot - the J2 shaft turns here')
    param('clear', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('cbore_d', '%.4f mm' % C.CBORE_D, 'lib/cobot CBORE_D')
    param('cbore_h', '%.4f mm' % C.CBORE_H, 'lib/cobot CBORE_H')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('m3_deep', '8.0 mm', 'M3 x 10 through the 3 mm lid')
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

    def radial_rib(name, p, r_out, w, x0, x1):
        """A rib of width w from point p out along its own radius to r_out (mm), extruded x0..x1 (cm)."""
        a_ = math.atan2(p[1], p[0])
        cu, su = math.cos(a_), math.sin(a_)
        r0 = math.hypot(*p)
        n = (-su * w / 2, cu * w / 2)
        q0, q1 = (r0 * cu, r0 * su), (r_out * cu, r_out * su)
        along_x(name, [[(q0[0] + n[0], q0[1] + n[1]), (q1[0] + n[0], q1[1] + n[1]), (q1[0] - n[0], q1[1] - n[1]),
                        (q0[0] - n[0], q0[1] - n[1])]], [], x0, x1, JOIN)

    x0, ft, xt = val('x0'), val('floor_t'), val('x_top')
    xf = x0 + ft
    A = val('a') * 10
    outer, inner = C.ring(A), C.ring(A - val('wall') * 10)
    lugs = [(C.LID_SCREWS_R * math.cos(math.radians(az)), C.LID_SCREWS_R * math.sin(math.radians(az)))
            for az in C.LID_SCREWS_AZ]
    t0 = design.timeline.count
    along_x('floor', [outer], [], x0, xf, NEW)
    along_x('wall', [outer], [], xf, xt, JOIN)
    along_x('wall_bore', [inner], [], xf, xt, CUT)
    for k, (u, v) in enumerate(lugs):
        along_x('lug_%d' % k, [], [(u, v, val('lug_r') * 10 * 2)], x0, xt, JOIN)
    along_x('bump', [], [(C.CAP_WIRE[0], C.CAP_WIRE[1], val('bump_d') * 10)], x0, xt, JOIN)
    group(t0, PH_0)

    t1 = design.timeline.count
    pd = val('pin_d') * 10
    for k, su in enumerate((-1, 1)):
        p = (su * C.SPR_CUP_S, C.SPR_PIN_V)
        along_x('pin_%d' % k, [], [(p[0], p[1], pd)], xf, xt - C.FREE / 10, JOIN)
        radial_rib('pin_rib_%d' % k, p, A - val('wall') * 10 / 2, pd * RIB_W_FRAC, xf, xt - C.FREE / 10)
    group(t1, PH_1)

    t2 = design.timeline.count
    along_x('shaft_hole', [], [(0.0, 0.0, val('shaft_bore') * 10)], x0, xf, CUT)
    for k, (u, v) in enumerate(C.CAP_SCREWS):
        along_x('screw_%d' % k, [], [(u, v, val('clear') * 10)], x0, xf, CUT)
        along_x('cbore_%d' % k, [], [(u, v, val('cbore_d') * 10)], xf - val('cbore_h'), xf, CUT)
    for k, (u, v) in enumerate(lugs):
        along_x('lug_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], xt - val('m3_deep'), xt, CUT)
    wd = val('wire_d') * 10
    along_x('wire_channel', [], [(C.CAP_WIRE[0], C.CAP_WIRE[1], wd)], x0, xt, CUT)
    a_ = math.radians(C.CAP_WIRE_AZ)
    cu, su = math.cos(a_), math.sin(a_)
    n = (-su * wd / 2, cu * wd / 2)
    r0, r1 = C.CAP_WIRE_IN_R, C.CAP_BUMP_R
    along_x('wire_groove', [[(r0 * cu + n[0], r0 * su + n[1]), (r1 * cu + n[0], r1 * su + n[1]),
                             (r1 * cu - n[0], r1 * su - n[1]), (r0 * cu - n[0], r0 * su - n[1])]],
            [(r0 * cu, r0 * su, wd)], x0, x0 + val('groove_h'), CUT, pick='all')
    group(t2, PH_2)
    print('cap a %.1f, x %.2f..%.2f (floor %.0f); pins O%.0f at u +-%.0f v %.2f; lugs r %.2f; shaft bore O%.2f; '
          '%d cover screws' % (C.CAP_A, x0 * 10, xt * 10, C.CAP_FLOOR_T, C.SPR_PIN_D, C.SPR_CUP_S, C.SPR_PIN_V,
                               C.LID_SCREWS_R, C.SHAFT_BORE, len(C.CAP_SCREWS)))
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
