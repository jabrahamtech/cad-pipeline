"""robotarm/cobot_j2_cap_lid - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j2_cap_lid` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py (the J2 spring block).

THE J2 CAP'S LID, and the J2 ENCODER's new home. It closes the spring cap
(3 x M3 x 10 into the cap's lugs) and traps both hub discs axially - nothing
else holds them. The AS5600 board drops into the pocket on its top face,
CHIP DOWN over the O12 hole, clamped by 2 x M2 x 5 + washers, over the magnet
in the J2 shaft's end; its wires run along the groove to the channel down the
cap's bump. CALIPER the board first (23 x 23 assumed).

Print: FLAT, bottom face down, no support.
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

COMPONENT = 'robotarm_cobot_j2_cap_lid'
BODY_NAME = 'cobot_j2_cap_lid'
PREFIX = 'cjl_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j2_cap_lid')
PH_0 = 'lid'
PH_1 = 'board + holes'
PHASES = [PH_0, PH_1]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
PLANE_EPS_CM = 1e-6
PRINT_NOTE = 'PRINT 1, flat'


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


    param('x0', '%.4f mm' % C.LID[0], 'lib/cobot LID')
    param('t', '%.4f mm' % C.CAP_LID_T, 'lib/cobot CAP_LID_T')
    param('a', '%.4f mm' % C.CAP_A, 'lib/cobot CAP_A')
    param('lug_r', '%.4f mm' % C.LID_LUG_R, 'lib/cobot LID_LUG_R')
    param('bump_d', '%.4f mm' % C.CAP_BUMP_D, 'lib/cobot CAP_BUMP_D')
    param('wire_d', '%.4f mm' % C.CAP_WIRE_D, 'lib/cobot CAP_WIRE_D')
    param('clear', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('pocket', '%.4f mm' % C.BOARD_POCKET, 'lib/cobot BOARD_POCKET')
    param('pocket_h', '%.4f mm' % C.BOARD_POCKET_H, 'lib/cobot BOARD_POCKET_H')
    param('stalk_hole', '%.4f mm' % C.STALK_HOLE_D, 'the chip hangs in here, over the magnet')
    param('clamp_pilot', '%.4f mm' % C.M2['pilot'], 'M2 x 5 + washer clamps the board edge')
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

    x0, t = val('x0'), val('t')
    A = val('a') * 10
    lugs = [(C.LID_SCREWS_R * math.cos(math.radians(az)), C.LID_SCREWS_R * math.sin(math.radians(az)))
            for az in C.LID_SCREWS_AZ]
    t0 = design.timeline.count
    along_x('lid', [C.ring(A)], [], x0, x0 + t, NEW)
    for k, (u, v) in enumerate(lugs):
        along_x('lug_%d' % k, [], [(u, v, val('lug_r') * 10 * 2)], x0, x0 + t, JOIN)
    along_x('bump', [], [(C.CAP_WIRE[0], C.CAP_WIRE[1], val('bump_d') * 10)], x0, x0 + t, JOIN)
    group(t0, PH_0)

    t1 = design.timeline.count
    for k, (u, v) in enumerate(lugs):
        along_x('lug_hole_%d' % k, [], [(u, v, val('clear') * 10)], x0, x0 + t, CUT)
    hp = val('pocket') * 10 / 2
    ph = val('pocket_h')
    along_x('board_pocket', [[(-hp, -hp), (hp, -hp), (hp, hp), (-hp, hp)]], [], x0 + t - ph, x0 + t, CUT)
    along_x('stalk_hole', [], [(0.0, 0.0, val('stalk_hole') * 10)], x0, x0 + t, CUT)
    for k, (u, v) in enumerate(((0.0, C.CLAMP_OFF), (0.0, -C.CLAMP_OFF))):
        along_x('clamp_%d' % k, [], [(u, v, val('clamp_pilot') * 10)], x0, x0 + t, CUT)
    wd = val('wire_d') * 10
    along_x('wire_hole', [], [(C.CAP_WIRE[0], C.CAP_WIRE[1], wd)], x0, x0 + t, CUT)
    a_ = math.radians(C.CAP_WIRE_AZ)
    cu, su = math.cos(a_), math.sin(a_)
    n = (-su * wd / 2, cu * wd / 2)
    r0, r1 = hp, C.CAP_BUMP_R
    along_x('wire_groove', [[(r0 * cu + n[0], r0 * su + n[1]), (r1 * cu + n[0], r1 * su + n[1]),
                             (r1 * cu - n[0], r1 * su - n[1]), (r0 * cu - n[0], r0 * su - n[1])]],
            [], x0 + t - ph, x0 + t, CUT)
    group(t1, PH_1)
    print('lid x %.2f..%.2f; board pocket %.1f sq over O%.0f; 3 lug holes; wire groove to r %.1f'
          % (x0 * 10, (x0 + t) * 10, C.BOARD_POCKET, C.STALK_HOLE_D, C.CAP_BUMP_R))
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
