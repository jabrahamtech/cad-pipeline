"""robotarm/cobot_tower - Fusion MCP generating script.

Rebuilds `robotarm_cobot_tower` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py and lib/j1_drive.py. REPLACES shoulder_bracket.

THE COBOT ARM'S SHOULDER. J1's rotating half, the column, and J2's drum, in
one part. It holds NO servo: the J2 MG995 lives in the upper arm (lib/cobot
docstring - the servo drops in along its own shaft there). What this part
carries at J2 is the SPIGOT the upper arm turns on, and the four pilots the
MG995's broached hub bolts into.

  * the rotor: the O76 turntable disc on the three 608ZZ, the O68 journal
    boss the ring laps, the J1 hub bolt circle, the loom window and the
    connector gate, the home magnet pocket - all as shoulder_bracket cut
    them, and this file defines the SAME tt_ contract turntable_stator,
    turntable_ring and j1_hub read
  * the column: a 12-gon about J1 that stays inside the boss (r 29 < 34),
    so the ring still goes on over the rotor from above
  * the J2 drum: a 12-gon about J2 from x -28 out to the +x face at x 47.5,
    where the solid J2 spigot stands. It lies on its side in the print, so
    its two lower diagonal facets are merged into 45 deg chamfers
    (lib/cobot.belly_ring), and a keel under its belly carries the overhang
    past the column, cut back by a 45 deg cone so it never touches the
    stationary ring
  * SOLID, not shelled: a hollow tower has a 56 x 75 ceiling nothing can
    print. J1 is vertical, so its mass costs no payload
  * three O7 ACCESS HOLES from the top down to the J1 hub bolt heads, and a
    loom channel from the J2 port down to the rotor's cable window

Print: RACE FACE DOWN (z = race_z on the bed), no support. Everything rises
from the disc; the drum's overhang is carried by the stadium column; the
cone under it is 45 deg; the spigot's pilots and the port are horizontal
holes of O2.5 and O8.

Frame: origin ON THE J2 AXIS above the J1 axis. +X along J2 (toward the
arm), +Y forward, +Z up - shoulder_bracket's frame, so the tt_ contract and
every downstream placement are unchanged.
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
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.design_rules import JOINT_FIT_MM as _FIT_J  # noqa: E402
from lib.j1_drive import (  # noqa: E402
    J1_HUB_BOLT_R_MM,
    J1_HUB_BOLT_AZ_DEG,
    J1_HUB_HOLE_D_MM,
    J1_HUB_CBORE_D_MM,
    J1_HUB_CBORE_H_MM,
    J1_HUB_OD_MM,
    J1_HUB_SCREW_BORE_MM,
    J1_HUB_FACE_MM,
    J1_HUB,
    HOME_R_MM,
    MAGNET_D_MM,
    MAGNET_POCKET_MM,
    MAGNET_ROTOR_AZ_DEG,
    ROTOR_GATE_AZ_DEG,
    ROTOR_GATE_W_MM,
    ROTOR_GATE_IR_MM,
    ROTOR_GATE_OR_MM,
)

COMPONENT = 'robotarm_cobot_tower'
BODY_NAME = 'cobot_tower'
PREFIX = 'ct_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_ROTOR = 'rotor'
PH_TOWER = 'column + J2 drum'
PH_J2 = 'J2 spigot'
PH_BASE = 'turntable interface'
PH_ROUTE = 'access + loom'
PHASES = [PH_ROTOR, PH_TOWER, PH_J2, PH_BASE, PH_ROUTE]
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_tower')
FULL_TURN_DEG = 360.0
GATE_AZ_CUT_DEG = 270.0        # the connector gate is cut at -pi/2 below
TOL = 1e-9                     # comparison epsilon, not a dimension
HUB_BOLT_MIN_DROP_MM3 = 300.0  # PLAYBOOK "the cut did nothing" tripwire
PLUG_W_MM, PLUG_T_MM = 8.7, 4.5     # standard JR/Futaba servo plug
RIM_MIN_MM = 1.5               # least rim outside the journal for the ring to hook
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0   # solid x the usual walls-and-infill factor


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def turret(name, expr, comment='', units='mm'):
        _set(TURRET + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    # ---- the SHARED turntable contract (as shoulder_bracket defined it) -------
    turret('post_r', '45.0 mm',
           'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
           '           top face at its rim, az 120/180/240. The ONLY fixing there is.')
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - DRAWING-CONFIRMED')
    turret('roller_w', '7.0 mm', '608ZZ width. The axle is RADIAL, so this lies radially.')
    turret('roller_r', '27.0 mm', 'roller pitch radius - SHARED, see turntable_stator.py')
    turret('race_margin', '0.5 mm', 'overrun each side of the rollers on the race band')
    turret('axle_z', '13.1 mm', 'roller axle height. Set so the bearing clears the platter top by 1.0.')
    turret('race_z', TURRET + 'axle_z + ' + TURRET + 'roller_od / 2',
           'derived: where the rotor\'s underside sits. NEVER type this.')
    turret('disc_d', '76.0 mm', 'rotor diameter - the ring hooks over the rim outside the boss')
    turret('disc_t', '%.2f mm' % C.ROTOR_DISC_T, 'rotor rim thickness, where the ring hooks over it - lib/cobot')
    turret('boss_d', '68.0 mm', 'the JOURNAL: turns inside the ring\'s bore and locates the arm radially')
    turret('boss_h', '%.2f mm' % C.ROTOR_BOSS_H, '= ring_lift + ring_t: the ring finishes FLUSH with the boss top')
    turret('ring_t', '4.0 mm', 'retainer thickness - SHARED, see turntable_ring.py')
    turret('ring_or', '50.0 mm', 'ring outer radius')
    turret('ring_lift', '0.40 mm', 'gap between the ring and the rim it holds down')
    turret('hub_seat_z', '%.4f mm' % J1_HUB.seat_z, 'lib/servo_hub.spline_hub() - NEVER type this')
    turret('hub_h', '%.4f mm' % J1_HUB_FACE_MM, 'J1 hub total height - lib/j1_drive')
    turret('hub_broach_d', '%.4f mm' % J1_HUB.broach_d, 'J1 hub bore - the steel spline cuts it')
    turret('hub_engaged', '%.4f mm' % J1_HUB.engaged, 'spline the J1 hub grips')
    turret('hub_od', '%.4f mm' % J1_HUB_OD_MM, 'J1 hub outer diameter')
    turret('hub_bolt_r', '%.4f mm' % J1_HUB_BOLT_R_MM, 'J1 hub bolt circle radius')
    turret('hub_bolt_d', '%.4f mm' % J1_HUB_HOLE_D_MM, 'clearance + deliberate float - no register')
    turret('hub_cbore_d', '%.4f mm' % J1_HUB_CBORE_D_MM, 'head counterbore in the boss top')
    turret('hub_cbore_h', '%.4f mm' % J1_HUB_CBORE_H_MM, 'and how deep - an ISO 4762 M3 cap head')
    turret('screw_bore', '%.4f mm' % J1_HUB_SCREW_BORE_MM, 'passes the servo screw head while the hub broaches')
    turret('hub_washer_d', '%.4f mm' % J1_HUB.washer_d, 'smallest washer that lands on the hub bore mouth')
    _set(STYLE + 'ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules', 'mm')

    # ---- fits + the rotor's own features ----------------------------------------
    param('wall', '%.2f mm' % C.MIN_WALL, 'minimum wall - design_rules MIN_WALL_MM')
    param('free', '%.2f mm' % C.FREE, 'free fit - design_rules')
    param('stand_h', '%.4f mm' % C.J2_STAND, 'J2 axis above the boss top - lib/cobot J2_STAND')
    param('cable_ir', '%.2f mm' % ROTOR_GATE_OR_MM, 'the loom passes through the disc, astern')
    param('gate_w', '%.2f mm' % ROTOR_GATE_W_MM, 'connector gate width - a servo plug is ~8.7')
    param('gate_ir', '%.2f mm' % ROTOR_GATE_IR_MM, 'how far in the gate bites')
    param('cable_deg', '50.0 deg', 'arc the cable window sweeps, centred astern at 270', 'deg')
    param('magnet_r', '%.2f mm' % HOME_R_MM, 'lib/j1_drive.HOME_R_MM - over the stator hall post')
    param('magnet_az', '%.2f deg' % MAGNET_ROTOR_AZ_DEG, 'lib/j1_drive - home = loom untwisted', 'deg')
    param('magnet_pocket_d', '%.2f mm' % (MAGNET_D_MM + _FIT_J['locational']), 'magnet + locational - glued')
    param('magnet_pocket_h', '%.2f mm' % MAGNET_POCKET_MM, 'half the magnet - lib/j1_drive')

    # ---- the tower ----------------------------------------------------------------
    param('tw_a', '%.4f mm' % C.TW_A, 'lib/cobot TW_A - column and drum apothem')
    param('x_face', '%.4f mm' % C.TOWER_X1, 'lib/cobot - the +x face the upper arm runs on')
    param('keel_w', '%.4f mm' % (C.TW_A * math.tan(math.pi / C.SIDES)), 'the drum\'s bottom flat half-width - the keel under it')
    param('relief', '%.4f mm' % C.FREE, 'the column clears the stationary ring by this')
    param('spigot_od', '%.4f mm' % C.J2.spigot_od, 'lib/cobot J2 - the upper arm turns on it')
    param('spigot_l', '%.4f mm' % (C.J2.x_spigot_end - C.J2.x_face), 'through the upper arm wall + 2 gaps')
    param('bolt_r', '%.4f mm' % C.J2.bolt_r, 'J2 hub bolt circle - placed beside the MG995 case')
    param('pilot_d', '%.4f mm' % C.M3['pilot'], 'M3 self-tap pilot - design_rules')
    param('pilot_deep', '10.0 mm', 'M3 x 12 through the 3 mm hub flange')
    param('screw_recess_d', '%.4f mm' % C.SCREW_HEAD_RECESS[0], 'the MG995 screw + washer, broached hub')
    param('screw_recess_h', '%.4f mm' % C.SCREW_HEAD_RECESS[1], 'its depth')
    param('access_d', '7.0 mm', 'O7 from the top to each J1 hub bolt head - a 2.5 key and its handle')
    param('port_d', '%.4f mm' % C.PORT_D, 'the J2 loom port, grommeted')
    param('loom_d', '8.0 mm', 'the channel from the port down to the rotor window')
    param('port_x', '6.0 mm', 'the port over the window arc (az 270 +- 25)')
    param('port_z', '-6.0 mm', 'the port just below the J2 axis')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

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
    rev = comp.features.revolveFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, '%s: expected %d, got %d' % (
                sk.name, expected, sk.profiles.count)
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            design.timeline.timelineGroups.add(start_index, design.timeline.count - 1).name = name

    def mpt(sk, x, y, z):
        return sk.modelToSketchSpace(P3(x, y, z))

    def mm(cm):
        return '%.4f mm' % (cm * 10.0)

    def poly(sk, pts3):
        for k in range(len(pts3)):
            sk.sketchCurves.sketchLines.addByTwoPoints(mpt(sk, *pts3[k]), mpt(sk, *pts3[(k + 1) % len(pts3)]))

    def xy_circle(name, x_c, y_c, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_c, y_c, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def xy_rect(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk, x0, y0, 0), mpt(sk, x1, y1, 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def xy_poly(name, pts_xy, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        poly(sk, [(x, y, 0) for x, y in pts_xy])
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def yz_poly(name, pts_yz, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        poly(sk, [(0, y, z) for y, z in pts_yz])
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def yz_circle(name, y_c, z_c, d_cm, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, y_c, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def xz_circle(name, x_c, z_c, d_cm, y0_expr, dy_expr, op):
        """XZ sketch: its normal is +Y, so the extent runs +y."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_c, 0, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    def xy_arc(name, r_in, r_out, mid_ang, half_ang, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        arcs = sk.sketchCurves.sketchArcs
        lines = sk.sketchCurves.sketchLines
        a0, a1 = mid_ang - half_ang, mid_ang + half_ang

        def p(r, a):
            return mpt(sk, r * math.cos(a), r * math.sin(a), 0)
        arcs.addByThreePoints(p(r_out, a0), p(r_out, mid_ang), p(r_out, a1))
        arcs.addByThreePoints(p(r_in, a0), p(r_in, mid_ang), p(r_in, a1))
        lines.addByTwoPoints(p(r_in, a0), p(r_out, a0))
        lines.addByTwoPoints(p(r_in, a1), p(r_out, a1))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def vol():
        return comp.bRepBodies.item(0).volume * 1000

    # ---- values in cm ---------------------------------------------------------------
    stand = val('stand_h')
    disc_t = tval('disc_t')
    disc_r = tval('disc_d') / 2
    journal_r = tval('boss_d') / 2
    boss_top = -stand
    rim_top = boss_top - tval('boss_h')
    race_z = rim_top - disc_t
    race_in = tval('roller_r') - tval('roller_w') / 2 - tval('race_margin')
    race_out = tval('roller_r') + tval('roller_w') / 2 + tval('race_margin')
    ring_top = rim_top + tval('ring_lift') + tval('ring_t')
    a = val('tw_a')
    xf = val('x_face')
    vtx = a / math.cos(math.pi / C.SIDES)

    # ---- sanity, before any geometry ---------------------------------------------------
    assert abs((boss_top - race_z) * 10 - (C.ROTOR_DISC_T + C.ROTOR_BOSS_H)) < TOL * 10
    assert abs(ring_top - boss_top) < TOL, 'the ring no longer finishes flush with the boss top'
    assert vtx < journal_r - val('relief'), (
        'the column (vertex r %.2f) reaches past the journal boss (r %.2f) - the ring '
        'could not go on over the rotor' % (vtx * 10, journal_r * 10))
    assert race_out < journal_r - TOL, 'the race band would be on the rim, not the boss'
    assert (disc_r - journal_r) * 10 >= RIM_MIN_MM, 'no rim outside the journal for the ring to hook'
    assert val('cable_ir') + val('wall') < race_in, 'the cable window runs into the race band'
    assert tval('hub_od') / 2 < val('gate_ir') - TOL, 'a servo plug down the gate lands on the J1 hub'
    assert (tval('hub_bolt_r') - tval('hub_cbore_d') / 2 >= tval('screw_bore') / 2 + val('wall') - TOL)
    assert tval('hub_cbore_h') <= disc_t + tval('boss_h') - val('wall') - TOL
    for _i, _az in enumerate(J1_HUB_BOLT_AZ_DEG):
        _a = math.radians(_az)
        _bx = tval('hub_bolt_r') * math.cos(_a) * 10
        _by = tval('hub_bolt_r') * math.sin(_a) * 10
        _dx = max(abs(_bx) - val('gate_w') * 10 / 2, 0.0)
        _dy = max(max(-val('cable_ir') * 10 - _by, _by + val('gate_ir') * 10), 0.0)
        assert math.hypot(_dx, _dy) - tval('hub_cbore_d') * 10 / 2 >= val('wall') * 10 - TOL, (
            'hub bolt %d is too near the connector gate' % _i)
        # the access hole over it misses the loom channel
        _lx, _ly = val('port_x') * 10, -(val('cable_ir') + race_in - val('wall')) / 2 * 10
        assert math.hypot(_bx - _lx, _by - _ly) >= (val('access_d') + val('loom_d')) * 10 / 2 + val('wall') * 10
    assert val('gate_w') * 10 >= PLUG_W_MM + 1.0 and (val('cable_ir') - val('gate_ir')) * 10 >= PLUG_T_MM + 1.0
    assert val('spigot_od') / 2 <= a - val('wall'), 'the J2 spigot overhangs the drum face'
    # the J2 hub bolt pilots land in the spigot, a wall from its edge
    assert val('bolt_r') + val('pilot_d') / 2 + val('wall') <= val('spigot_od') / 2 + TOL
    assert val('screw_recess_d') / 2 + val('wall') <= val('bolt_r') - val('pilot_d') / 2 + TOL

    # ---- phase 1: the rotor -------------------------------------------------------------
    t0 = design.timeline.count
    xy_circle('turntable_rim', 0, 0, tval('disc_d'), mm(race_z), TURRET + 'disc_t', NEW)
    xy_circle('journal_boss', 0, 0, tval('boss_d'), mm(rim_top), TURRET + 'boss_h', JOIN)
    group(t0, PH_ROTOR)

    # ---- phase 2: the column and the J2 drum ---------------------------------------------
    t1 = design.timeline.count
    # the column: a 12-gon about J1, inside the journal
    xy_poly('column', [(x / 10, y / 10) for x, y in C.ring(a * 10)], mm(boss_top), mm(stand), JOIN)
    # the J2 drum: a 12-gon about the x axis with a 45 deg belly, from -a out to the +x face
    yz_poly('j2_drum', [(y / 10, z / 10) for y, z in C.belly_ring(a * 10)], mm(-a), mm(xf + a), JOIN)
    # the keel: under the drum's bottom flat, from the column out to the face
    xy_rect('keel', 0.0, xf, -val('keel_w'), val('keel_w'), mm(boss_top), mm(stand - a), JOIN)
    # the cone relief: nothing of the column below 45 deg outside the journal,
    # so it never touches the stationary ring (flush with the boss top)
    sk = sketch(comp.xZConstructionPlane, 'sk_ring_relief')
    r0 = journal_r - val('relief')
    far = xf + a * 2
    poly(sk, [(r0, 0, boss_top), (far, 0, boss_top), (far, 0, boss_top + far - r0)])
    axis = sk.sketchCurves.sketchLines.addByTwoPoints(mpt(sk, 0, 0, boss_top), mpt(sk, 0, 0, 0))
    axis.isConstruction = True
    rinp = rev.createInput(sk.profiles.item(0), axis, CUT)
    rinp.setAngleExtent(False, V('360 deg'))
    rinp.participantBodies = [comp.bRepBodies.item(0)]
    rev.add(rinp).name = 'ring_relief'
    group(t1, PH_TOWER)

    # ---- phase 3: the J2 spigot and its hub pilots -------------------------------------------
    t2 = design.timeline.count
    yz_circle('j2_spigot', 0, 0, val('spigot_od'), mm(xf), PREFIX + 'spigot_l', JOIN)
    x_end = xf + val('spigot_l')
    yz_circle('servo_screw_recess', 0, 0, val('screw_recess_d'), mm(x_end - val('screw_recess_h')),
              PREFIX + 'screw_recess_h', CUT)
    for k, (bu, bv) in enumerate(C.J2.bolts()):
        # the MG995 case runs along +y (the upper arm's +u) at zero pitch
        yz_circle('hub_pilot_%d' % k, bu / 10, bv / 10, val('pilot_d'), mm(x_end - val('pilot_deep')),
                  PREFIX + 'pilot_deep', CUT)
    group(t2, PH_J2)

    # ---- phase 4: turntable interface (shoulder_bracket's, unchanged) --------------------------
    t3 = design.timeline.count
    xy_circle('hub_screw_bore', 0, 0, tval('screw_bore'), mm(race_z), mm(disc_t + tval('boss_h')), CUT)
    v_before = vol()
    for _i, _az in enumerate(J1_HUB_BOLT_AZ_DEG):
        _a = math.radians(_az)
        _bx = tval('hub_bolt_r') * math.cos(_a)
        _by = tval('hub_bolt_r') * math.sin(_a)
        xy_circle('hub_bolt_%d' % _i, _bx, _by, tval('hub_bolt_d'), mm(race_z), mm(disc_t + tval('boss_h')), CUT)
        xy_circle('hub_cbore_%d' % _i, _bx, _by, tval('hub_cbore_d'), mm(boss_top - tval('hub_cbore_h')),
                  TURRET + 'hub_cbore_h', CUT)
    assert v_before - vol() > HUB_BOLT_MIN_DROP_MM3, 'the J1 hub bolts cut next to nothing'
    xy_arc('cable_window', val('cable_ir'), race_in - val('wall'), -math.pi / 2, val('cable_deg') / 2,
           mm(race_z), mm(disc_t + tval('boss_h')), CUT)
    v_before = vol()
    xy_rect('connector_gate', -val('gate_w') / 2, val('gate_w') / 2, -val('cable_ir'), -val('gate_ir'),
            mm(race_z), mm(disc_t + tval('boss_h')), CUT)
    assert v_before - vol() > 100.0, 'the connector gate cut next to nothing'
    assert abs((ROTOR_GATE_AZ_DEG % FULL_TURN_DEG) - GATE_AZ_CUT_DEG) < TOL
    _m_in = val('magnet_r') - val('magnet_pocket_d') / 2
    _m_out = val('magnet_r') + val('magnet_pocket_d') / 2
    assert _m_in >= race_out - TOL and _m_out <= disc_r - val('wall') + TOL
    v_before = vol()
    xy_circle('home_magnet_pocket', val('magnet_r') * math.cos(val('magnet_az')),
              val('magnet_r') * math.sin(val('magnet_az')), val('magnet_pocket_d'),
              mm(race_z), PREFIX + 'magnet_pocket_h', CUT)
    assert v_before - vol() > TOL, 'the magnet pocket cut nothing'
    group(t3, PH_BASE)

    # ---- phase 5: access to the J1 hub bolts, and the J2 loom ---------------------------------
    t4 = design.timeline.count
    top = vtx                                  # above the drum's top vertex
    for _i, _az in enumerate(J1_HUB_BOLT_AZ_DEG):
        _a = math.radians(_az)
        xy_circle('access_%d' % _i, tval('hub_bolt_r') * math.cos(_a), tval('hub_bolt_r') * math.sin(_a),
                  val('access_d'), mm(boss_top), mm(top - boss_top), CUT)
    # the loom: a vertical channel down to the window arc, and a port out the
    # back (-y) face, just below J2
    ly = -(val('cable_ir') + race_in - val('wall')) / 2      # over the middle of the window arc
    assert -ly + val('loom_d') / 2 + val('wall') <= a + TOL, 'the loom channel breaks out of the column'
    xy_circle('loom_channel', val('port_x'), ly, val('loom_d'), mm(boss_top), mm(val('port_z') - boss_top), CUT)
    xz_circle('loom_port', val('port_x'), val('port_z'), val('port_d'), mm(-a * 2), mm(a * 2 + ly), CUT)
    group(t4, PH_ROUTE)

    # ---- identity + diagnostics ----------------------------------------------------------------
    assert comp.bRepBodies.count == 1, 'the tower came out in %d pieces' % comp.bRepBodies.count
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
    v = vol()
    print("body: '%s' | appearance: %s | PRINT 1, race face down, no support" % (body.name, used))
    print('rotor: O%.0f x %.1f disc, O%.0f journal to the boss top z %.2f (J2 %.1f above it)'
          % (tval('disc_d') * 10, disc_t * 10, tval('boss_d') * 10, boss_top * 10, stand * 10))
    print('tower: 12-gon a %.1f (vertex r %.2f inside the r %.1f journal); J2 drum x %.1f..%.1f; '
          'keel to x %.1f under it, cone relief from r %.2f'
          % (a * 10, vtx * 10, journal_r * 10, -a * 10, xf * 10, xf * 10, r0 * 10))
    print('J2 spigot O%.1f x %.2f at x %.2f..%.2f; 4 x M3 pilots O%.1f x %.0f at r %.1f az %s; '
          'screw recess O%.0f x %.0f' % (val('spigot_od') * 10, val('spigot_l') * 10, xf * 10, x_end * 10,
                                          val('pilot_d') * 10, val('pilot_deep') * 10, val('bolt_r') * 10,
                                          list(C.J2.bolt_az), val('screw_recess_d') * 10,
                                          val('screw_recess_h') * 10))
    print('J1 hub bolts: 3 x O%.0f access holes from the top; loom: O%.0f channel at (%.1f, %.1f) and '
          'a O%.0f port out the back at z %.1f'
          % (val('access_d') * 10, val('loom_d') * 10, val('port_x') * 10, ly * 10, val('port_d') * 10,
             val('port_z') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g (solid x 0.65) | valid: %s'
          % (v, v * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
