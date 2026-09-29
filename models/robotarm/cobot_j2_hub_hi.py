"""robotarm/cobot_j2_hub_hi - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j2_hub_hi` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py (the J2 spring block).

THE J2 SPRING'S UPPER HUB DISC, on the shaft's D-flat over the coil. Its
one pin (at +u, under the legs' line, hanging down) pushes the spring's UPPER
leg when the arm tips the other way. The lid traps it; the J2 magnet is in the
shaft's end, through its bore.

Print: THE DISC FLAT ON THE BED, pin up, no support.
Frame: the upper arm's at the J2 spring's NEUTRAL (arm vertical); this part
is TOWER-fixed through the shaft's D-flat, which faces -v here.
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

COMPONENT = 'robotarm_cobot_j2_hub_hi'
BODY_NAME = 'cobot_j2_hub_hi'
PREFIX = 'chh_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j2_hub_hi')
PH_0 = 'disc'
PH_1 = 'D-bore + pin'
PHASES = [PH_0, PH_1]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
PLANE_EPS_CM = 1e-6
BORE_SEGS = 40                     # the D-bore's round part as a polygon: sag 0.01 at r 5.1
PRINT_NOTE = 'PRINT 1, disc on the bed'


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


    param('x0', '%.4f mm' % C.HUB_HI[0], 'lib/cobot')
    param('x1', '%.4f mm' % C.HUB_HI[1], 'lib/cobot')
    param('r', '%.4f mm' % C.HUB_R, 'lib/cobot HUB_R')
    param('bore', '%.4f mm' % (C.SHAFT_D2 + C.LOC), 'the D-bore: the shaft + LOC')
    param('flat', '%.4f mm' % (C.SHAFT_D2 / 2 - C.SHAFT_FLAT + C.LOC / 2), 'the D-bore\'s flat, from the axis')
    param('pin_d', '%.4f mm' % C.SPR_PIN_D, 'lib/cobot SPR_PIN_D')
    param('pin_x0', '%.4f mm' % (C.LEG_HI_X - C.SPR_WIRE / 2 - C.SPR_PIN_H), 'the pin reaches past its leg')
    param('pin_x1', '%.4f mm' % C.HUB_HI[0], '')
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
    t0 = design.timeline.count
    along_x('disc', [], [(0.0, 0.0, val('r') * 10 * 2)], x0, x1, NEW)
    group(t0, PH_0)
    t1 = design.timeline.count
    r = val('bore') * 10 / 2
    f = val('flat') * 10
    beta = math.acos(f / r)
    pts = []          # the round part from the flat's one end to the other; the chord (flat) at v = -f
    for k in range(BORE_SEGS):
        phi = -math.pi / 2 + beta + (2 * math.pi - 2 * beta) * k / (BORE_SEGS - 1)
        pts.append((r * math.cos(phi), r * math.sin(phi)))
    assert abs(pts[0][1] + f) < PLANE_EPS_CM * 10 and abs(pts[-1][1] + f) < PLANE_EPS_CM * 10, 'the flat is not on -v'
    along_x('d_bore', [pts], [], x0, x1, CUT)
    along_x('pin', [], [(1 * C.SPR_HUB_S, C.SPR_PIN_V, val('pin_d') * 10)], val('pin_x0'), val('pin_x1'), JOIN)
    group(t1, PH_1)
    print('hub x %.2f..%.2f r %.2f; D-bore O%.2f flat at %.2f (on -v); pin O%.0f at (%+.0f, %.2f) x %.2f..%.2f'
          % (x0 * 10, x1 * 10, C.HUB_R, val('bore') * 10, f, C.SPR_PIN_D, 1 * C.SPR_HUB_S, C.SPR_PIN_V,
             val('pin_x0') * 10, val('pin_x1') * 10))
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
