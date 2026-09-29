"""robotarm/cobot_upper_arm - Fusion MCP generating script.

Rebuilds `robotarm_cobot_upper_arm` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py. Its lid is cobot_upper_arm_cover.

THE UPPER ARM BODY: a 12-gon capsule (a 26 at J2, a 24 at J3), the servo
link at BOTH of its joints, open on its +x face.
  * the -x face is ONE 3 mm JOINT WALL. The tower's J2 spigot and the
    forearm's J3 spigot pass through its two bores; the J2 hub and the J3
    gear, bolted to those spigots from in here, trap it (lib/cobot Joint)
  * the MG995 (J2) lies along the link, shaft on J2, spline toward -x into
    its broached hub. Its FAR tab screws to a post block with a relief slot
    for the tab rib; the near tab sits over the hub flange and is not used
  * the J3 SG90 lies ACROSS the link, 27.2 from J3, its 18T pinion in mesh
    with the 36T gear. Its near tab hole is inside the pinion's sweep, so it
    is screwed to a separate SERVO PLATE (cobot_j3_plate) on the bench, and
    the plate screws down onto two posts outside both gear sweeps
  * every keep-out is CUT at the end, so no feature can ever sit in the J2
    flange's or the J3 gear's sweep
  * the loom: in through the J2 port at the back of the J2 end, along the
    bottom of the shell, and out through the J3 gear's bore to the forearm

ASSEMBLY (specs/robotarm/cobot.md has the whole sequence):
  1. over the tower's J2 spigot and the forearm's J3 spigot, cover off
  2. the J3 gear onto the forearm spigot: 3 x M3 x 16
  3. the MG995 with its hub already broached on: in along -x, hub onto the
     tower spigot, 4 x M3 x 12 past the case; far tab: 2 x M3 x 10
  4. the J3 SG90 on its plate, pinion first, in along -x into mesh; plate
     to the posts: 2 x M3 x 8
  5. the loom, then the cover: 6 x M3 x 8

Print: JOINT WALL DOWN (the -x face on the bed), no support. The bores are
vertical and round; the shell and every post rise straight up.

Frame: arm x (the joint axes), y = u along the link from J2 (0) to J3 (L1),
z = v across it, at zero pitch. J2 on the origin.
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
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.servo import MG995_TAB_HOLE_PITCH_Y, MG995_TAB_RIB_W_MM, MG995_TAB_RIB_TOP_MM  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_cobot_upper_arm'
BODY_NAME = 'cobot_upper_arm'
PREFIX = 'cua_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_upper_arm')
PH_FORM = 'wall + shell'
PH_JOINTS = 'joint bores'
PH_SERVOS = 'servo posts'
PH_COVER = 'cover bosses'
PH_LOOM = 'loom'
PH_KEEP = 'keep-outs'
PHASES = [PH_FORM, PH_JOINTS, PH_SERVOS, PH_COVER, PH_LOOM, PH_KEEP]
M2 = _FASTENER['M2']
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
POST_PAD = 3.0          # CHOSEN - post material round a pilot
J3_POST_U = 14.0        # CHOSEN - the J3 plate posts, this far back from the pinion axis
J3_POST_V = 15.0        # CHOSEN - and this far either side
BOSS_R = 3.5            # CHOSEN - a cover-screw boss, merged into the shell
COVER_SCREWS = ((45.0, 20.0), (45.0, -20.0), (75.0, 20.0), (75.0, -20.0), (110.0, 19.0), (110.0, -19.0))


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

    MG, SG = C.MG995, C.SG90
    param('x0', '%.4f mm' % C.UA_X0, 'lib/cobot UA_X0 - the joint wall\'s outer (-x) face')
    param('wall_t', '%.4f mm' % C.JOINT_WALL, 'lib/cobot JOINT_WALL')
    param('x_top', '%.4f mm' % (C.UA_X1 - C.COVER_T), 'the shell\'s open edge = the cover seat')
    param('shell', '%.4f mm' % C.SHELL, 'lib/cobot SHELL')
    param('a2', '%.4f mm' % C.UA_A2, 'apothem at J2')
    param('a3', '%.4f mm' % C.UA_A3, 'apothem at J3')
    param('l1', '%.4f mm' % C.L1, 'J2 -> J3')
    param('bore2', '%.4f mm' % C.J2.bore, 'lib/cobot J2 - the tower spigot runs in it')
    param('bore3', '%.4f mm' % C.J3.bore, 'lib/cobot J3 - the forearm spigot runs in it')
    param('keep2', '%.4f mm' % C.J2.keep_out_r, 'the J2 hub flange sweep + FREE')
    param('keep2_top', '%.4f mm' % (C.J2.x_spigot_end + C.FLANGE_T + C.FREE), 'to the flange top + FREE')
    param('keep3', '%.4f mm' % (C.GEAR_TIP_R + C.FREE), 'the J3 gear sweep + FREE')
    param('keep3_top', '%.4f mm' % (C.J3.x_hub_back + C.FREE), 'to the gear top + FREE')
    param('keep_pin', '%.4f mm' % (C.PIN_TIP_R + C.FREE), 'the pinion sweep + FREE')
    param('mg_tab_top', '%.4f mm' % C.UA_J2_TAB_TOP, 'the MG995 tab face toward -x, where it lands')
    param('mg_case_end', '%.4f mm' % (MG.case_l - MG.shaft_from_end + C.LOC), 'the case\'s far end + LOC, along u')
    param('mg_hole_u', '%.4f mm' % (MG.case_l - MG.shaft_from_end + (MG.tab_hole_pitch - MG.case_l) / 2),
          'far tab holes, along u')
    param('mg_hole_v', '%.4f mm' % (MG995_TAB_HOLE_PITCH_Y / 2), 'and across')
    param('m3_pilot', '%.4f mm' % C.M3['pilot'], 'design_rules')
    param('m3_deep', '8.0 mm', 'pilot depth')
    param('post_pad', '%.4f mm' % POST_PAD, 'material round a pilot')
    param('rib_w', '%.4f mm' % (MG995_TAB_RIB_W_MM + C.FREE), 'the MG995 tab rib + FREE')
    param('rib_d', '%.4f mm' % (MG995_TAB_RIB_TOP_MM - MG.tab_thk + C.FREE), 'how far it stands off the tab')
    param('pin_u', '%.4f mm' % (C.L1 - C.J3_CENTRE), 'the pinion axis, along u')
    param('j3_post_u', '%.4f mm' % (C.L1 - C.J3_CENTRE - J3_POST_U), 'the J3 plate posts')
    param('j3_post_v', '%.4f mm' % J3_POST_V, 'and across')
    param('j3_plate_under', '%.4f mm' % (C.UA_J3_TAB_TOP - C.PLATE_T), 'the plate\'s underside')
    param('boss_r', '%.4f mm' % BOSS_R, 'a cover-screw boss')
    param('port_d', '%.4f mm' % C.PORT_D, 'the J2 loom port, grommeted')
    param('port_x', '%.4f mm' % (C.UA_X0 + C.JOINT_WALL + C.FLANGE_T + C.PORT_D), 'port height off the wall')

    # ---- sanity, mm, before any geometry ------------------------------------------
    for u, v in ((val('j3_post_u') * 10, val('j3_post_v') * 10),):
        r_pin = math.hypot(val('pin_u') * 10 - u, v)
        assert r_pin - POST_PAD >= val('keep_pin') * 10, 'a J3 plate post is in the pinion sweep'
        assert math.hypot(C.L1 - u, v) - POST_PAD >= val('keep3') * 10, 'a J3 plate post is in the gear sweep'
        assert v + POST_PAD <= C.UA_A3 - C.SHELL + 1.0
    assert val('mg_hole_u') * 10 - MG.tab_hole_dia / 2 >= val('keep2') * 10, 'the MG995 far post is in the J2 sweep'
    mg_tip = MG.case_l - MG.shaft_from_end + (MG.tab_span - MG.case_l) / 2
    for u, v in COVER_SCREWS:
        assert math.hypot(u, v) - BOSS_R >= C.J2.keep_out_r
        assert math.hypot(C.L1 - u, v) - BOSS_R >= C.GEAR_TIP_R + C.FREE
        assert abs(v) - BOSS_R >= MG.case_w / 2 + C.FREE or u - BOSS_R >= mg_tip + C.FREE, 'a cover boss in the MG995'
    assert val('j3_plate_under') >= val('keep3_top') - C.FREE / 10, 'the J3 plate would sit on the pinion'

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------------
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

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def extrude(prof, op, start_cm, dist_cm, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(start_cm)))
        inp.setDistanceExtent(False, V(mm(dist_cm)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    def uv_poly(sk, pts_mm):
        sp = [sk.modelToSketchSpace(P3(0, u / 10, v / 10)) for u, v in pts_mm]
        for k in range(len(sp)):
            sk.sketchCurves.sketchLines.addByTwoPoints(sp[k], sp[(k + 1) % len(sp)])

    def along_x(name, loops_mm, circles_mm, x0, x1, op, pick='largest'):
        """YZ sketch (u = y, v = z), extruded along +x from x0 to x1 (cm)."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        for pts in loops_mm:
            uv_poly(sk, pts)
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
                if (pick == 'largest' and a_ > best) or (pick == 'ring' and pr.profileLoops.count == 2 and a_ > best):
                    best, bp = a_, pr
            profs.add(bp)
        return extrude(profs, op, x0, x1 - x0, name)

    def rect(u0, u1, v0, v1):
        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

    x0, wt, xt = val('x0'), val('wall_t'), val('x_top')
    xw = x0 + wt                                  # the wall's inner face
    outer = C.capsule(val('a2') * 10, val('a3') * 10, val('l1') * 10)
    inner = C.capsule(val('a2') * 10, val('a3') * 10, val('l1') * 10, inset=val('shell') * 10)

    # ---- phase 1: the joint wall and the 12-gon shell ---------------------------------
    t0 = design.timeline.count
    along_x('joint_wall', [outer], [], x0, xw, NEW)
    along_x('shell', [outer, inner], [], xw, xt, JOIN, pick='ring')
    group(t0, PH_FORM)

    # ---- phase 2: the two joint bores --------------------------------------------------
    t1 = design.timeline.count
    along_x('bore_j2', [], [(0.0, 0.0, val('bore2') * 10)], x0, xw, CUT)
    along_x('bore_j3', [], [(C.L1, 0.0, val('bore3') * 10)], x0, xw, CUT)
    group(t1, PH_JOINTS)

    # ---- phase 3: servo posts ------------------------------------------------------------
    t2 = design.timeline.count
    hu, hv, pad = val('mg_hole_u') * 10, val('mg_hole_v') * 10, val('post_pad') * 10
    u_lo = val('mg_case_end') * 10
    along_x('mg995_post', [rect(u_lo, hu + pad, -hv - pad, hv + pad)], [], xw, val('mg_tab_top'), JOIN)
    for k, sv in enumerate((1, -1)):
        along_x('mg995_pilot_%d' % k, [], [(hu, sv * hv, val('m3_pilot') * 10)],
                val('mg_tab_top') - val('m3_deep'), val('mg_tab_top'), CUT)
    rw = val('rib_w') * 10
    along_x('mg995_rib_slot', [rect(u_lo - 1.0, hu + pad + 1.0, -rw / 2, rw / 2)], [],
            val('mg_tab_top') - val('rib_d'), val('mg_tab_top'), CUT)
    pu, pv = val('j3_post_u') * 10, val('j3_post_v') * 10
    for k, sv in enumerate((1, -1)):
        along_x('j3_post_%d' % k, [], [(pu, sv * pv, 2 * pad)], xw, val('j3_plate_under'), JOIN)
        along_x('j3_pilot_%d' % k, [], [(pu, sv * pv, val('m3_pilot') * 10)],
                val('j3_plate_under') - val('m3_deep'), val('j3_plate_under'), CUT)
    group(t2, PH_SERVOS)

    # ---- phase 4: cover-screw bosses, merged into the shell --------------------------------
    t3 = design.timeline.count
    for k, (u, v) in enumerate(COVER_SCREWS):
        along_x('cover_boss_%d' % k, [], [(u, v, val('boss_r') * 10 * 2)], xw, xt, JOIN)
        along_x('cover_pilot_%d' % k, [], [(u, v, val('m3_pilot') * 10)], xt - val('m3_deep'), xt, CUT)
    group(t3, PH_COVER)

    # ---- phase 5: the J2 loom port, out of the back of the J2 end --------------------------
    t4 = design.timeline.count
    sk = sketch(comp.xZConstructionPlane, 'sk_j2_port')
    sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(val('port_x'), 0, 0)),
                                                    val('port_d') / 2)
    extrude(sk.profiles.item(0), CUT, -(C.UA_A2 + C.SHELL) / 10, (C.UA_A2 + C.SHELL) / 10 - (C.UA_A2 - 2 * C.SHELL) / 10,
            'j2_port')
    group(t4, PH_LOOM)

    # ---- phase 6: keep-outs - whatever was built, nothing stays in a sweep -------------------
    t5 = design.timeline.count
    along_x('keep_j2_flange', [], [(0.0, 0.0, val('keep2') * 10 * 2)], xw, val('keep2_top'), CUT)
    along_x('keep_j3_gear', [], [(C.L1, 0.0, val('keep3') * 10 * 2)], xw, val('keep3_top'), CUT)
    along_x('keep_pinion', [], [(val('pin_u') * 10, 0.0, val('keep_pin') * 10 * 2)], xw, val('keep3_top'), CUT)
    group(t5, PH_KEEP)

    assert comp.bRepBodies.count == 1, 'the upper arm came out in %d pieces' % comp.bRepBodies.count
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
    print("body: '%s' | appearance: %s | PRINT 1, joint wall down" % (body.name, used))
    print('capsule a %.0f -> %.0f over %.0f; wall x %.2f..%.2f, shell to x %.2f (cover to %.2f)'
          % (C.UA_A2, C.UA_A3, C.L1, x0 * 10, xw * 10, xt * 10, C.UA_X1))
    print('bores: J2 O%.2f (tower spigot O%.0f), J3 O%.2f (forearm spigot O%.0f)'
          % (C.J2.bore, C.J2.spigot_od, C.J3.bore, C.J3.spigot_od))
    print('MG995 far post u %.2f..%.2f v +-%.2f to x %.2f, pilots O%.1f at u %.1f v +-%.1f, rib slot %.1f x %.1f'
          % (u_lo, hu + pad, hv + pad, val('mg_tab_top') * 10, val('m3_pilot') * 10, hu, hv, rw,
             val('rib_d') * 10))
    print('J3 plate posts at u %.1f v +-%.1f to x %.2f; pinion axis u %.1f'
          % (pu, pv, val('j3_plate_under') * 10, val('pin_u') * 10))
    print('keep-outs: J2 r %.2f to x %.2f, gear r %.2f and pinion r %.2f to x %.2f'
          % (val('keep2') * 10, val('keep2_top') * 10, val('keep3') * 10, val('keep_pin') * 10,
             val('keep3_top') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
