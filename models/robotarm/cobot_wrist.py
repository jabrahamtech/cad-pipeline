"""robotarm/cobot_wrist - Fusion MCP generating script.

Rebuilds `robotarm_cobot_wrist` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py. Its +x cap, which carries the J4 spigot, is
cobot_wrist_cap.

THE WRIST BODY: the 12-gon drum (a 25 about J4) from the tool plane side
(x -11) to the J5 bay's wall (x +6.2), cut flat at the front (u 15.7) where
the rotator's neck stands. It HOUSES the J5 roll SG90 (position servo,
direct): shaft forward on the J5 axis, case lying along +v.
  * the BAY and the TAB SLOT are pockets open at the split face: the servo
    is LAID IN along -x, its tabs drop into the slot (LOC in u) - the slot
    holds it, no tab screws. The case top bears on the front wall
  * the FRONT BORE (O10.85) takes the rotator's hub; it is a teardrop that
    opens into the split face, so it prints without a roof
  * the BACK PORT (O8, grommeted) takes the J5 lead and the gripper's lead
    out to the J4 service loop
  * 3 x M3 pilots for the cap's screws

ASSEMBLY: the J5 SG90 into the bay (lead out through the port) -> the cap
over it (3 x M3 x 12) -> the wrist's J4 spigot into the forearm's bore ->
the rotator onto the spline through the front bore (M2.5 x 6 from the
front) -> the head (4 x M3 into the rotator).

Print: OUTER FACE (x -11) DOWN, no support: every pocket opens at the top.
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

COMPONENT = 'robotarm_cobot_wrist'
BODY_NAME = 'cobot_wrist'
PREFIX = 'cwr_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_wrist')
PH_FORM = 'drum'
PH_BAY = 'J5 bay + tab slot + front bore'
PH_MISC = 'port + screws'
PHASES = [PH_FORM, PH_BAY, PH_MISC]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
PLANE_EPS_CM = 1e-6
PRINT_NOTE = 'PRINT 1, outer face down'


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

    param('x0', '%.4f mm' % -C.WR_HALF, 'lib/cobot - the tool-plane side face')
    param('x1', '%.4f mm' % C.WR_SPLIT, 'lib/cobot WR_SPLIT - the J5 bay\'s wall')
    param('a', '%.4f mm' % C.WR_A, 'lib/cobot WR_A')
    param('front', '%.4f mm' % C.ROT_SEAT, 'lib/cobot ROT_SEAT - the front face')
    param('loc', '%.4f mm' % C.LOC, 'bay + slot, locational')
    param('bore', '%.4f mm' % C.ROT_BORE, 'lib/cobot ROT_BORE - the rotator hub + ROT')
    param('port_d', '%.4f mm' % C.PORT_D, 'a grommeted cable port')
    param('port_x', '%.4f mm' % C.WR_PORT_X, 'lib/cobot WR_PORT_X')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('m3_deep', '10.0 mm', 'M3 x 12 through the cap')

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

    x0, x1 = val('x0'), val('x1')
    lc = val('loc') * 10
    drum = clip_front(C.ring(val('a') * 10), val('front') * 10)
    t0 = design.timeline.count
    along_x('drum', [drum], [], x0, x1, NEW)
    group(t0, PH_FORM)

    t1 = design.timeline.count
    ca, ta = C.J5_CASE, C.J5_TABS
    along_x('bay', [[(ca[0] - lc, ca[2] - lc), (ca[1], ca[2] - lc), (ca[1], ca[3] + lc), (ca[0] - lc, ca[3] + lc)]],
            [], -x1, x1, CUT)
    along_x('tab_slot', [[(ta[0] - lc / 2, ta[2] - lc), (ta[1] + lc / 2, ta[2] - lc), (ta[1] + lc / 2, ta[3] + lc),
                          (ta[0] - lc / 2, ta[3] + lc)]], [], -x1, x1, CUT)
    r = val('bore') * 10 / 2
    tear = [(r / math.sqrt(2), -r / math.sqrt(2)), (r * math.sqrt(2), 0.0), (r / math.sqrt(2), r / math.sqrt(2))]
    fu, bu = val('front'), C.J5_CASE_TOP / 10
    along_u('front_bore', (fu + bu) / 2, (fu - bu) / 2 + val('loc'), [tear], [(0.0, 0.0, 2 * r)], CUT)
    group(t1, PH_BAY)

    t2 = design.timeline.count
    back = C.WR_PORT[0] / 10
    along_u('back_port', (back + ca[0] / 10) / 2, (ca[0] / 10 - back) / 2 + val('loc'), [],
            [(val('port_x') * 10, C.WR_PORT[1], val('port_d') * 10)], CUT)
    for k, (u, v) in enumerate(C.WRIST_SCREWS):
        along_x('screw_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], x1 - val('m3_deep'), x1, CUT)
    group(t2, PH_MISC)
    print('drum a %.0f, x %.2f..%.2f, front u %.2f; bay u %.2f..%.2f v %.2f..%.2f; tab slot u %.2f..%.2f; '
          'front bore O%.2f; port O%.0f; %d cap screws'
          % (C.WR_A, x0 * 10, x1 * 10, C.ROT_SEAT, ca[0], ca[1], ca[2], ca[3], ta[0], ta[1], C.ROT_BORE, C.PORT_D,
             len(C.WRIST_SCREWS)))

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
