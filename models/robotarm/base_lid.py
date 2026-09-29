"""robotarm/base_lid - closes base_platter's bay; the turntable stands on it.

Rebuilds `robotarm_base_lid` (idempotent). Spec: specs/robotarm/base_platter.md.

REWRITTEN 2026-09-27 for the NEW base_platter (O190, J1 = MG995 360 deg).
The previous file fitted the printed legacy platter (O171.75 lid, SG90 well,
loom slot at az 270) and is in git history; none of its openings line up
with the new stator, so it was replaced rather than patched.

Frame: the SAME as turntable_stator and base_platter - origin on the J1
axis at the platter RIM TOP, so this lid is z -3.00..0.00 and its top face
is the plane the stator's base plate lands on. Everything the lid has to
pass is read from lib/j1_drive and lib/servo, not re-measured:

  disc          O(recess - loc), sits on the platter's shelf, flush at z 0
  3 x O9.50     turret posts (O8.8) pass through to the stator - tt_post_r
  4 x M3        at r 88 into the platter's lid columns, heads counterbored
  servo opening the MG995 case + window clearance + the stator's lead
                keyway, so the case drops straight through from the stator
                above and its lead follows it down. Insertion play on top.
  loom window   under the stator's az-210 window, one margin bigger, with
                two zip-tie bridges on the UNDERSIDE either side of it so the
                loom is tied to the base where it enters, not to the stator.
  hall lead     a hole under the stator's home-post lead slot (az 330).
  (no vents)    REMOVED 2026-09-28. Jonathan: the lid's openings are "just
                for all the servos coming out the top". Twelve O4 holes in a
                ring outside the shroud were the only VISIBLE openings with no
                cable through them; the servo opening and loom window already
                connect the bay to the shroud's interior.

Print: PETG, TOP FACE DOWN, so the two tie bridges grow up off the bed and
bridge 7 mm - no support.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core
import adsk.fusion

from lib.palette import hints_for  # noqa: E402
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402
from lib.design_rules import MIN_WALL_MM as _MIN_WALL  # noqa: E402
from lib.servo import SERVO_CASE_CLEARANCE_MM  # noqa: E402
from lib.j1_drive import (  # noqa: E402
    J1_SERVO, HOME_R_MM, HOME_AZ_DEG, HALL_BODY_H_MM, HALL_SLOT_MM,
    LOOM_AZ_DEG, LOOM_IR_MM, LOOM_OR_MM, LOOM_DEG, TT_POST_D_MM, TT_POST_LID_CLEAR_MM,
)

COMPONENT = 'robotarm_base_lid'
BODY_NAME = 'base_lid'
PREFIX = 'bl_'
TURRET = 'tt_'
PH_DISC = 'disc'
PH_OPEN = 'openings'
PH_FIX = 'fixings'
PH_TIES = 'loom ties'
PH_FINISH = 'finish'
PHASES = [PH_DISC, PH_OPEN, PH_FIX, PH_TIES, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('base_lid')

POST_AZ = (120.0, 180.0, 240.0)
SCREW_AZ = (45.0, 135.0, 225.0, 315.0)
TIE_SIDES = (-1, 1)
TOL = 1e-9
REL_TOL = 1e-6
PETG_G_CM3 = 1.27
PRINT_FILL = 0.65
HALL_OFF_MM = HALL_BODY_H_MM / 2 + _FIT['locational'] / 2 + HALL_SLOT_MM / 2

# THE STATOR'S OPENINGS, from the same library numbers the stator cuts them
# with. The lid's job is to contain each of these with a margin.
_S = J1_SERVO
SERVO_HALF_W_MM = _S.case_w / 2 + SERVO_CASE_CLEARANCE_MM / 2
SERVO_Y_OFF_MM = _S.case_l / 2 - _S.shaft_from_end
SERVO_Y0_MM = SERVO_Y_OFF_MM - _S.case_l / 2 - SERVO_CASE_CLEARANCE_MM / 2
SERVO_Y1_MM = SERVO_Y_OFF_MM + _S.case_l / 2 + SERVO_CASE_CLEARANCE_MM / 2


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    _set(TURRET + 'post_r', '45.0 mm',
         'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
         '           top face at its rim, az 120/180/240. The ONLY fixing there is.', 'mm')

    # --- the platter this lid closes - base_platter.py -----------------------
    param('recess_d', '186.8 mm', 'base_platter lid recess: od 190 - 2 x rim_t 1.6')
    param('loc', '%.2f mm' % _FIT['locational'], 'locational fit - design_rules')
    param('free', '%.2f mm' % _FIT['free'], 'free fit - design_rules')
    param('min_wall', '%.2f mm' % _MIN_WALL, 'MIN_WALL_MM - design_rules')
    param('dia', PREFIX + 'recess_d - ' + PREFIX + 'loc', 'lid disc - locational in the recess')
    param('t', '3.0 mm', 'thickness - base_platter lid_t, shelf to flush')
    param('post_clear_d', '%.2f mm' % (TT_POST_D_MM + TT_POST_LID_CLEAR_MM),
          'over the O%.1f turret posts - lib/j1_drive, legacy MEASURED 0.7 fit' % TT_POST_D_MM)
    param('screw_r', '88.0 mm', 'base_platter lid_r')
    param('screw_d', '%.2f mm' % _FASTENER['M3']['clearance'], 'M3 clearance - FASTENER_MM')
    param('head_d', '6.5 mm', 'M3 cap head 5.5 + clearance')
    param('head_z', '1.2 mm', 'head counterbore depth, leaving 1.8 of lid under it')
    # --- openings -----------------------------------------------------------------
    param('play', '1.0 mm',
          'INSERTION PLAY round every opening, total. Jonathan: "leave tolerance\n'
          '           to put it in" - the case, its lead and the loom plugs all go\n'
          '           through by hand, at an angle, with the stator in the way.')
    param('srv_half_w', '%.3f mm' % SERVO_HALF_W_MM, 'stator case window half width - lib')
    param('srv_y0', '%.3f mm' % SERVO_Y0_MM, 'stator case window, shaft end - lib')
    param('srv_y1', '%.3f mm' % SERVO_Y1_MM, 'stator case window, far end - lib')
    param('key_y0', '-18.05 mm',
          'the stator lead keyway runs out to here (ts_lead_key_l). The J1 lead\n'
          '           follows the case down through it, so the lid passes it too.')
    param('loom_ir', '%.2f mm' % LOOM_IR_MM, 'lib/j1_drive = ts_cable_ir')
    param('loom_or', '%.2f mm' % LOOM_OR_MM, 'lib/j1_drive = ts_cable_or')
    param('loom_az', '%.2f deg' % LOOM_AZ_DEG, 'lib/j1_drive.LOOM_AZ_DEG = ts_cable_az - over the bay', 'deg')
    param('loom_deg', '%.2f deg' % LOOM_DEG, 'lib/j1_drive = ts_cable_deg', 'deg')
    param('home_r', '%.2f mm' % HOME_R_MM, 'lib/j1_drive.HOME_R_MM')
    param('home_az', '%.2f deg' % HOME_AZ_DEG, 'lib/j1_drive.HOME_AZ_DEG', 'deg')
    param('hall_off', '%.3f mm' % HALL_OFF_MM,
          'stator lead slot centre, -Y of the post centre (pocket half + half the 2.4 slot)')
    param('hall_d', '7.0 mm', 'hole for the hall leads - 3 wires and their heat-shrink')
    # --- loom tie bridges, on the underside ------------------------------------------
    param('tie_w', '4.0 mm', 'zip-tie slot width')
    param('tie_h', '3.0 mm', 'tunnel height under the bar')
    param('tie_bar', '1.6 mm', 'bar thickness - MIN_WALL. The bridges hang over the ESP32\n'
          '           bay now; at 2.0 they reached into its 1.5 keep-out')
    param('tie_leg', '3.0 mm', 'each leg')
    param('tie_gap', '7.0 mm', 'tunnel length between the legs')
    param('tie_r', '(' + PREFIX + 'loom_ir + ' + PREFIX + 'loom_or) / 2', 'on the window\'s mean radius')
    param('tie_off', '8.0 deg', 'how far past each end of the window the bridges stand', 'deg')
    param('ef', '0.4 mm', 'elephant-foot chamfer - design_rules')

    # ---- idempotent rebuild ------------------------------------------------------
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
    assert comp.name == COMPONENT, 'component came back as %r' % comp.name
    ext = comp.features.extrudeFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def mm(cm):
        return '%.4f mm' % (cm * 10.0)

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mxy(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def extrude(sk, op, z0, dz, name, pick=None):
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            p = sk.profiles.item(i)
            if pick is None or pick(p):
                c.add(p)
        assert c.count == 1, '%s: %d profiles' % (sk.name, c.count)
        inp = ext.createInput(c, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0)))
        inp.setDistanceExtent(False, V(mm(dz)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def circle(name, x, y, d, z0, dz, op):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, x, y), d / 2)
        return extrude(sk, op, z0, dz, name)

    def poly(name, pts, z0, dz, op):
        sk = sketch(name)
        q = [mxy(sk, x, y) for x, y in pts]
        for k in range(len(q)):
            sk.sketchCurves.sketchLines.addByTwoPoints(q[k], q[(k + 1) % len(q)])
        return extrude(sk, op, z0, dz, name)

    def arc(name, r_in, r_out, mid, half, z0, dz, op):
        sk = sketch(name)
        A, L = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines

        def p(r, a):
            return mxy(sk, r * math.cos(a), r * math.sin(a))
        A.addByThreePoints(p(r_out, mid - half), p(r_out, mid), p(r_out, mid + half))
        A.addByThreePoints(p(r_in, mid - half), p(r_in, mid), p(r_in, mid + half))
        L.addByTwoPoints(p(r_in, mid - half), p(r_out, mid - half))
        L.addByTwoPoints(p(r_in, mid + half), p(r_out, mid + half))
        return extrude(sk, op, z0, dz, name)

    def tangential_box(name, r0, r1, az, t0, t1, z0, dz, op):
        c, s = math.cos(az), math.sin(az)
        pts = [(rr * c - tt * s, rr * s + tt * c)
               for rr, tt in ((r0, t0), (r1, t0), (r1, t1), (r0, t1))]
        return poly(name, pts, z0, dz, op)

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    t = val('t')
    z0 = -t
    play = val('play') / 2

    # ---- sanity -----------------------------------------------------------------------
    for az in POST_AZ + SCREW_AZ:
        rr = tval('post_r') if az in POST_AZ else val('screw_r')
        px, py = rr * math.cos(math.radians(az)), rr * math.sin(math.radians(az))
        dx = max(-val('srv_half_w') - play - px, 0.0, px - val('srv_half_w') - play)
        dy = max(val('key_y0') - play - py, 0.0, py - val('srv_y1') - play)
        assert math.hypot(dx, dy) > val('post_clear_d') / 2 + val('min_wall') - TOL, (
            'the az-%.0f hole runs into the servo opening' % az)
    assert val('key_y0') < val('srv_y0') - TOL, (
        'the lead keyway is meant to run PAST the case window\'s shaft end')
    assert val('dia') / 2 - val('screw_r') >= val('head_d') / 2 + val('min_wall') - TOL, (
        'the M3 heads at r %.1f overhang the lid edge' % (val('screw_r') * 10))

    # ---- phase 1: disc -------------------------------------------------------------------
    t0_ = design.timeline.count
    circle('disc', 0.0, 0.0, val('dia'), z0, t, NEW)
    group(t0_, PH_DISC)

    # ---- phase 2: openings ------------------------------------------------------------------
    t1 = design.timeline.count
    hw = val('srv_half_w') + play
    poly('servo_opening', [(-hw, val('key_y0') - play), (hw, val('key_y0') - play),
                           (hw, val('srv_y1') + play), (-hw, val('srv_y1') + play)],
         z0 - t, t * 3, CUT)
    _grow = play / val('loom_ir')
    arc('loom_window', val('loom_ir') - play, val('loom_or') + play, val('loom_az'),
        val('loom_deg') / 2 + _grow, z0 - t, t * 3, CUT)
    _hx = val('home_r') * math.cos(val('home_az'))
    _hy = val('home_r') * math.sin(val('home_az')) - val('hall_off')
    circle('hall_lead_hole', _hx, _hy, val('hall_d'), z0 - t, t * 3, CUT)
    group(t1, PH_OPEN)

    # ---- phase 3: fixings ---------------------------------------------------------------------
    t2 = design.timeline.count
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        circle('post_hole_%d' % i, tval('post_r') * math.cos(a), tval('post_r') * math.sin(a),
               val('post_clear_d'), z0 - t, t * 3, CUT)
    for i, az in enumerate(SCREW_AZ):
        a = math.radians(az)
        x, y = val('screw_r') * math.cos(a), val('screw_r') * math.sin(a)
        circle('screw_%d' % i, x, y, val('screw_d'), z0 - t, t * 3, CUT)
        circle('screw_head_%d' % i, x, y, val('head_d'), -val('head_z'), t, CUT)
    group(t2, PH_FIX)

    # ---- phase 4: loom tie bridges on the underside ----------------------------------------------
    # Each bridge: two legs and a bar, a tie-sized tunnel between, standing
    # DOWN from the lid underside just past each end of the loom window. A
    # zip tie round the loom and through one bridge holds it where it enters.
    t3 = design.timeline.count
    tr = val('tie_r')
    half_len = val('tie_gap') / 2 + val('tie_leg')
    for k, sgn in enumerate(TIE_SIDES):
        az = val('loom_az') + sgn * (val('loom_deg') / 2 + val('tie_off'))
        tangential_box('tie_bridge_%d' % k, tr - half_len, tr + half_len, az,
                       -val('tie_w') / 2, val('tie_w') / 2,
                       z0 - val('tie_h') - val('tie_bar'), val('tie_h') + val('tie_bar'), JOIN)
        tangential_box('tie_tunnel_%d' % k, tr - val('tie_gap') / 2, tr + val('tie_gap') / 2, az,
                       -val('tie_w'), val('tie_w'), z0 - val('tie_h'), val('tie_h'), CUT)
    group(t3, PH_TIES)

    # ---- finish: elephant-foot chamfer on the TOP rim - it prints face down ----
    t4 = design.timeline.count
    body = comp.bRepBodies.item(0)
    edges = adsk.core.ObjectCollection.create()
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Circle3D) and abs(g.center.z) < REL_TOL \
                and abs(g.radius - val('dia') / 2) < REL_TOL * 10:
            edges.add(e)
    assert edges.count == 1, 'expected the one top rim edge, found %d' % edges.count
    ch_in = comp.features.chamferFeatures.createInput2()
    ch_in.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(PREFIX + 'ef'), False)
    comp.features.chamferFeatures.add(ch_in).name = 'elephant_foot'
    group(t4, PH_FINISH)

    # ---- identity + diagnostics ----------------------------------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got %d' % comp.bRepBodies.count
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
    print('body: %r | material: %s | appearance: %s' % (body.name, body.material.name, used))
    print('FRAME: z 0 = platter rim top = stator datum; lid z %.2f..0' % (z0 * 10))
    print('disc O%.2f x %.2f in the O%.2f recess' % (val('dia') * 10, t * 10,
                                                      val('recess_d') * 10))
    print('SERVO OPENING x +-%.2f, y %.2f..%.2f - case window + lead keyway + %.1f play'
          % (hw * 10, (val('key_y0') - play) * 10, (val('srv_y1') + play) * 10,
             val('play') * 10))
    print('LOOM WINDOW r %.2f..%.2f at az %.0f, %.0f deg - under ts_cable_*; '
          '2 tie bridges on the underside at +-%.0f deg past its ends'
          % ((val('loom_ir') - play) * 10, (val('loom_or') + play) * 10,
             math.degrees(val('loom_az')), math.degrees(val('loom_deg')) + math.degrees(2 * _grow),
             math.degrees(val('tie_off'))))
    print('hall lead hole O%.1f at (%.2f, %.2f) - under the stator home-post slot'
          % (val('hall_d') * 10, _hx * 10, _hy * 10))
    print('fixings: 3 x O%.1f posts at r %.1f | 4 x M3 at r %.1f, heads O%.1f x %.1f'
          % (val('post_clear_d') * 10, tval('post_r') * 10, val('screw_r') * 10,
             val('head_d') * 10, val('head_z') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | printed ~%.0f g PETG | valid: %s' % (
        body.volume * 1000, body.volume * PETG_G_CM3 * PRINT_FILL, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
