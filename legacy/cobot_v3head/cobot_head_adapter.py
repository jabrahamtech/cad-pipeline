"""robotarm/cobot_head_adapter - Fusion MCP generating script.

Rebuilds `robotarm_cobot_head_adapter` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py (the pattern from lib/grip).

THE HEAD ADAPTER: the existing v3 gripper bolts to the cobot arm UNCHANGED.
The cobot's J5 output is a O21 neck (lib/cobot - the forearm passes beside
the wrist, so nothing wider may sit nearer J4 than r 24.2); this disc bolts
to the neck's face (4 x M3 x 8, heads counterbored under the head) and
carries the old rotator's front face: O36, 4 x M3 heat-set inserts on
+-11 x +-9, which the v3 head's own M3 x 8 go into. Retired when the head is
shrunk to the wrist (grip v4).

Print: FRONT FACE DOWN, no support; press the inserts from the front after.
Frame: z along J5, 0 on its back face (= the neck's face, u 24.5), +z forward.
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

COMPONENT = 'robotarm_cobot_head_adapter'
BODY_NAME = 'cobot_head_adapter'
PREFIX = 'cha_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_head_adapter')
PH_FORM = 'disc'
PH_HOLES = 'inserts + screws'
PHASES = [PH_FORM, PH_HOLES]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
PLANE_EPS_CM = 1e-6
PRINT_NOTE = 'PRINT 1, front face down'


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


    param('d', '%.4f mm' % C.ADAPTER_D, 'lib/cobot ADAPTER_D - the old rotator face')
    param('t', '%.4f mm' % C.ADAPTER_T, 'lib/cobot ADAPTER_T')
    param('eff_x', '%.4f mm' % C.EFF_PATTERN[0], 'lib/grip EFF_BOLT_X - the v3 head')
    param('eff_z', '%.4f mm' % C.EFF_PATTERN[1], 'lib/grip EFF_BOLT_Z')
    param('insert_d', '%.4f mm' % C.M3['insert'], 'design_rules - M3 heat-set')
    param('insert_h', '%.4f mm' % C.M3_INSERT_DEPTH, 'insert length + 1')
    param('bolt_r', '%.4f mm' % C.ROT_BOLT_R, 'lib/cobot ROT_BOLT_R - into the neck')
    param('clear', '%.4f mm' % C.M3['clearance'], 'M3 clearance')
    param('cbore_d', '%.4f mm' % C.CBORE_D, 'lib/cobot CBORE_D')
    param('cbore_h', '%.4f mm' % C.CBORE_H, 'lib/cobot CBORE_H')
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

    def disc(name, x, y, d, z0, dz, op):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(x, y, 0)), d / 2)
        return extrude(sk.profiles.item(0), op, z0, dz, name)

    t = val('t')
    t0 = design.timeline.count
    disc('disc', 0.0, 0.0, val('d'), 0.0, t, NEW)
    group(t0, PH_FORM)
    t1 = design.timeline.count
    k = 0
    for sx in (-1, 1):
        for sz in (-1, 1):
            disc('insert_%d' % k, sx * val('eff_x'), sz * val('eff_z'), val('insert_d'), t - val('insert_h'),
                 val('insert_h'), CUT)
            k += 1
    for k, az in enumerate(C.ROT_BOLT_AZ):
        bx, by = val('bolt_r') * math.cos(math.radians(az)), val('bolt_r') * math.sin(math.radians(az))
        disc('screw_%d' % k, bx, by, val('clear'), 0.0, t, CUT)
        disc('cbore_%d' % k, bx, by, val('cbore_d'), t - val('cbore_h'), val('cbore_h'), CUT)
    group(t1, PH_HOLES)
    print('O%.0f x %.0f at u %.1f..%.1f; 4 x M3 inserts on +-%.0f x +-%.0f; 4 x M3 x %.0f counterbored at r %.0f'
          % (C.ADAPTER_D, C.ADAPTER_T, C.ROT_FACE_C, C.ROT_FACE_C + C.ADAPTER_T, C.EFF_PATTERN[0],
             C.EFF_PATTERN[1], C.ADAPTER_SCREW_L, C.ROT_BOLT_R))
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
