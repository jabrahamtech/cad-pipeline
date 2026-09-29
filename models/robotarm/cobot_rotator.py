"""robotarm/cobot_rotator - Fusion MCP generating script.

Rebuilds `robotarm_cobot_rotator` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py. REPLACES wrist_rotator in the cobot arm.

J5's OUTPUT: a O21 NECK on the roll SG90's own spline, carrying the head.
Why a neck and not the old O36 disc: the forearm is OFFSET beside the wrist
(x >= 11.25) and its J4 end reaches r 23.8 about J4, so anything wider than
the wrist's +-11 that sits nearer J4 than that sweeps into the forearm as the
wrist pitches. The neck stays inside the wrist's own layer and puts the
head's face out at u 24.5 (lib/cobot ROT_FACE_C, asserted >= r 24.2).
  * the HUB (O10.5) runs in the wrist's front bore; its back face seats FREE
    above the SG90's case top; the spline broaches the round bore (servo_hub)
  * the servo's screw goes in from the FRONT through a counterbore that
    leaves just the standard screw's reach (M2.5 x 6)
  * 4 x M3 self-tap pilots on r 7 take the head

Print: FRONT FACE DOWN, no support: the broach opens at the top of the build.
Frame: z along J5, 0 on the seat (servo-side) face, +z forward.
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

COMPONENT = 'robotarm_cobot_rotator'
BODY_NAME = 'cobot_rotator'
PREFIX = 'crt_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_rotator')
PH_FORM = 'hub + neck'
PH_BORE = 'broach + screw + head pilots'
PHASES = [PH_FORM, PH_BORE]
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

    H = C.ROT_HUB
    stack = C.ROT_FACE_C - C.ROT_SEAT_Z
    cb_h, cb_d = C.pinion_cbore(H, stack)
    param('hub_d', '%.4f mm' % C.ROT_HUB_D, 'lib/cobot ROT_HUB_D - runs in the wrist\'s front bore')
    param('hub_h', '%.4f mm' % (C.ROT_NECK_X0 - C.ROT_SEAT_Z), 'seat -> the neck, FREE past the wrist face')
    param('neck_d', '%.4f mm' % C.ROT_NECK_D, 'lib/cobot ROT_NECK_D - inside the wrist\'s x layer')
    param('stack', '%.4f mm' % stack, 'seat -> head face')
    param('boss_clear_d', '%.4f mm' % H.boss_clear_d, 'servo_hub')
    param('boss_clear_to', '%.4f mm' % H.boss_clear_to, 'servo_hub')
    param('broach_d', '%.4f mm' % H.broach_d, 'servo_hub - THE STEEL SPLINE CUTS THIS (gauged)')
    param('broach_to', '%.4f mm' % H.broach_to, 'servo_hub')
    param('screw_d', '%.4f mm' % (H.screw_d + C.FREE), 'the servo screw, clearance')
    param('cbore_d', '%.4f mm' % cb_d, 'the screw head + washer')
    param('cbore_h', '%.4f mm' % cb_h, 'lib/cobot pinion_cbore - a standard screw reaches')
    param('bolt_r', '%.4f mm' % C.ROT_BOLT_R, 'lib/cobot ROT_BOLT_R - the head\'s 4 x M3')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('m3_deep', '%.4f mm' % C.ROT_PILOT_DEEP, 'lib/cobot ROT_PILOT_DEEP - the head\'s M3 x 8')

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

    hh, st = val('hub_h'), val('stack')
    t0 = design.timeline.count
    disc('hub', 0.0, 0.0, val('hub_d'), 0.0, hh, NEW)
    disc('neck', 0.0, 0.0, val('neck_d'), hh, st - hh, JOIN)
    group(t0, PH_FORM)
    t1 = design.timeline.count
    disc('boss_clear', 0.0, 0.0, val('boss_clear_d'), 0.0, val('boss_clear_to'), CUT)
    disc('broach', 0.0, 0.0, val('broach_d'), val('boss_clear_to'), val('broach_to') - val('boss_clear_to'), CUT)
    disc('screw', 0.0, 0.0, val('screw_d'), val('broach_to'), st - val('broach_to'), CUT)
    if val('cbore_h') > 0:
        disc('screw_cbore', 0.0, 0.0, val('cbore_d'), st - val('cbore_h'), val('cbore_h'), CUT)
    for k, az in enumerate(C.ROT_BOLT_AZ):
        bx, by = val('bolt_r') * math.cos(math.radians(az)), val('bolt_r') * math.sin(math.radians(az))
        disc('head_pilot_%d' % k, bx, by, val('m3_pilot'), st - val('m3_deep'), val('m3_deep'), CUT)
    group(t1, PH_BORE)
    print('hub O%.1f x %.1f, neck O%.0f to %.1f (u %.2f..%.2f); broach O%.2f %.1f..%.1f; screw cbore O%.2f x %.1f; '
          '%d x M3 pilots at r %.0f' % (C.ROT_HUB_D, hh * 10, C.ROT_NECK_D, st * 10, C.ROT_SEAT_Z, C.ROT_FACE_C,
                                        H.broach_d, H.boss_clear_to, H.broach_to, cb_d, cb_h, len(C.ROT_BOLT_AZ),
                                        C.ROT_BOLT_R))

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
