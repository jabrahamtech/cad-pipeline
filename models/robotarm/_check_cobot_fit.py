"""robotarm/_check_cobot_fit - the cobot ASSEMBLY GATE (not a part).

Jonathan, 2026-09-29: "work out how the parts go together - how the motors
are placed with the correct tolerances ... minimise the likelihood of
reprints and issues fitting parts into other like no place to put the motor
in (like the motor would have to teleport into position)" and "make sure
gears fit correctly in housing and instalations and tolerances are taken
into account".

Run AFTER every cobot_* part script has built into the active document. It:
  1. adds ENVELOPE bodies for what is bought: MG995 / SG90 cases, tabs and
     output bosses, the AS5600 boards and their chips, the idler's dowel,
     the J2 counterbalance spring (coil tube + legs, at neutral)
  2. places every occurrence in the arm frame at a pose (lib/cobot numbers)
  3. STATIC: Fusion interference over everything; the only pairs allowed to
     touch are the designed ones (each gear with its pinion, the dowel in
     its press hole)
  4. INSERTION: replays the build (specs/robotarm/cobot.md) backwards - each
     step's parts are moved out along +x in 4 mm steps to 40 mm and checked
     against every part fitted BEFORE that step. A step that collides
     anywhere on that path cannot be assembled: it would have to teleport
  5. POSES: sweeps J3, J4 and J2 and checks the links, plates and gears of one
     link against the other's - the fold limits of the offset joints

Prints a verdict per check and PASS / FAIL. Tolerance: overlap volume
> 0.05 mm3 counts (coincident faces are excluded by the Fusion option).
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
import lib.grip as G  # noqa: E402

VOL_TOL_MM3 = 0.05
STEP_MM = 4.0
OUT_MM = 40.0
# steps whose parts sit deeper than OUT_MM below the open face: replayed until they are clear of the link
# (the J2 gear's spring shaft reaches x 156; its back is at 60.5 and the upper arm's open face at 126.8)
OUT_FULL = {'J2 gear onto its register': 100.0, 'J3 gear onto its register': 72.0}
HOME_Q2 = 90.0           # the upper arm straight up
HOME_Q3 = 0.0            # the forearm straight on
Q3_SWEEP = (-150.0, -120.0, -90.0, -60.0, -30.0, 30.0, 60.0, 90.0, 120.0, 150.0)
Q2_SWEEP = (0.0, 30.0, 150.0, 180.0)
Q4_SWEEP = (-150.0, -120.0, -90.0, -60.0, -30.0, 30.0, 60.0, 90.0, 120.0, 150.0)
HOME_Q4 = 0.0

# what moves with what: link groups
TOWER = ['robotarm_cobot_tower', 'robotarm_cobot_j2_gear', 'robotarm_cobot_j2_hub_lo', 'robotarm_cobot_j2_hub_hi']
HUBS = ('robotarm_cobot_j2_hub_lo', 'robotarm_cobot_j2_hub_hi')   # keyed on the J2 gear's shaft: tower-fixed,
#                                                                    built in the UA frame at HOME_Q2 (neutral)
SPRING = ['fit_spring']       # the counterbalance at neutral: in the static and insertion checks, NOT the J2 sweep
#                               (its legs are carried round by the pins - lib/cobot asserts their sweep)
UA = ['robotarm_cobot_upper_arm', 'robotarm_cobot_upper_arm_cover', 'robotarm_cobot_j2_cap',
      'robotarm_cobot_j2_cap_lid', 'robotarm_cobot_j2_plate',
      'robotarm_cobot_j3_plate', 'robotarm_cobot_j2_pinion', 'robotarm_cobot_j3_pinion', 'robotarm_cobot_j3_idler',
      'fit_mg995', 'fit_sg90_j3', 'fit_board_j2', 'fit_board_j3', 'fit_dowel']
FA = ['robotarm_cobot_forearm', 'robotarm_cobot_forearm_plate', 'robotarm_cobot_j3_gear', 'robotarm_cobot_j4_plate',
      'robotarm_cobot_j4_pinion', 'fit_sg90_j4', 'fit_board_j4']
WR = ['robotarm_cobot_wrist', 'robotarm_cobot_wrist_cap', 'robotarm_cobot_rotator', 'robotarm_grip_body',
      'robotarm_cobot_j4_gear', 'fit_sg90_j5']
# designed contacts
ALLOWED = {frozenset(p) for p in (
    ('fit_sg90_j5', 'robotarm_cobot_rotator'),          # the output boss runs inside the rotator's bore
    ('robotarm_cobot_j2_gear', 'robotarm_cobot_j2_pinion'),
    ('robotarm_cobot_j3_gear', 'robotarm_cobot_j3_idler'),
    ('robotarm_cobot_j3_idler', 'robotarm_cobot_j3_pinion'),
    ('robotarm_cobot_j4_gear', 'robotarm_cobot_j4_pinion'),
    ('fit_dowel', 'robotarm_cobot_upper_arm'),          # pressed
)}
# the build, in order: (step, parts moved in along -x)
BUILD = [
    ('upper arm over both spigots', ['robotarm_cobot_upper_arm']),
    ('J2 gear onto its register', ['robotarm_cobot_j2_gear']),
    ('J3 gear onto its register', ['robotarm_cobot_j3_gear']),
    ('dowel into the idler boss', ['fit_dowel']),
    ('idler onto the dowel', ['robotarm_cobot_j3_idler']),
    ('J3 plate unit (SG90 + pinion + board)', ['robotarm_cobot_j3_plate', 'fit_sg90_j3', 'robotarm_cobot_j3_pinion',
                                               'fit_board_j3']),
    ('J2 plate unit (MG995 + pinion)', ['robotarm_cobot_j2_plate', 'fit_mg995', 'robotarm_cobot_j2_pinion']),
    ('upper arm cover', ['robotarm_cobot_upper_arm_cover']),
    ('J2 spring cap over the shaft', ['robotarm_cobot_j2_cap']),
    ('lower hub onto the D-flat', ['robotarm_cobot_j2_hub_lo']),
    ('spring over the shaft, legs over the pins', ['fit_spring']),
    ('upper hub onto the D-flat', ['robotarm_cobot_j2_hub_hi']),
    ('cap lid + J2 AS5600 board', ['robotarm_cobot_j2_cap_lid', 'fit_board_j2']),
]
WR_BUILD = [
    ('J5 SG90 laid into the wrist body', ['fit_sg90_j5']),
    ('wrist cap', ['robotarm_cobot_wrist_cap']),
    ('rotator onto the J5 spline (along -u)', ['robotarm_cobot_rotator']),
    ('grip v4 head onto the neck (along -u)', ['robotarm_grip_body']),
]
FA_BUILD = [
    ('forearm over the wrist spigot', ['robotarm_cobot_forearm']),
    ('J4 gear onto the wrist spigot', ['robotarm_cobot_j4_gear']),
    ('J4 plate unit (SG90 + pinion + board)', ['robotarm_cobot_j4_plate', 'fit_sg90_j4', 'robotarm_cobot_j4_pinion',
                                               'fit_board_j4']),
    ('forearm plate', ['robotarm_cobot_forearm_plate']),
]
FA_BASE = ['robotarm_cobot_wrist', 'robotarm_cobot_wrist_cap', 'robotarm_cobot_rotator', 'fit_sg90_j5']
WR_BASE = ['robotarm_cobot_wrist']
ALONG_U = {'robotarm_cobot_rotator', 'robotarm_grip_body'}      # these go in along -u of their link, not -x


def placer(root):
    """place(q2, q3, lift=None, q4=HOME_Q4): every part (and fit_ envelope) to a pose, in the arm frame.

    Module level so _check_cobot_mesh can pose the same arm: occurrence moves are not captured in the
    timeline, so any later recompute (the exporter adding its plates) puts every part back at its origin.
    """
    P3 = adsk.core.Point3D.create
    V3 = adsk.core.Vector3D.create

    def occ_named(name):
        for o in root.occurrences:
            if o.component.name == name:
                return o
        return None

    def link_matrix(q_deg, origin_yz):
        """Link frame (x, u, v) -> arm frame: u at angle q in the arm's y-z plane."""
        q = math.radians(q_deg)
        m = adsk.core.Matrix3D.create()
        m.setWithCoordinateSystem(P3(0, origin_yz[0] / 10, origin_yz[1] / 10), V3(1, 0, 0),
                                  V3(0, math.cos(q), math.sin(q)), V3(0, -math.sin(q), math.cos(q)))
        return m

    def axial_matrix(link_m, u, v, x0):
        """A gear/pinion frame (z along the joint axis, 0 at x0) at (u, v) of a link."""
        m = adsk.core.Matrix3D.create()
        m.setWithCoordinateSystem(P3(x0 / 10, u / 10, v / 10), V3(0, 1, 0), V3(0, 0, 1), V3(1, 0, 0))
        m.transformBy(link_m)
        return m

    def rot_matrix(link_m, u0=C.ROT_SEAT_Z):
        """A J5 part: its z along J5 (the wrist's u), 0 at u0."""
        m = adsk.core.Matrix3D.create()
        m.setWithCoordinateSystem(P3(0, u0 / 10, 0), V3(0, 0, 1), V3(1, 0, 0), V3(0, 1, 0))
        m.transformBy(link_m)
        return m

    def place(q2, q3, lift=None, q4=HOME_Q4):
        lift = lift or {}
        ident = adsk.core.Matrix3D.create()
        mu = link_matrix(q2, (0.0, 0.0))
        j3 = (C.L1 * math.cos(math.radians(q2)), C.L1 * math.sin(math.radians(q2)))
        mf = link_matrix(q2 + q3, j3)
        j4 = (j3[0] + C.L2 * math.cos(math.radians(q2 + q3)), j3[1] + C.L2 * math.sin(math.radians(q2 + q3)))
        mw = link_matrix(q2 + q3 + q4, j4)
        uw = (0.0, math.cos(math.radians(q2 + q3 + q4)), math.sin(math.radians(q2 + q3 + q4)))
        where = {
            'robotarm_cobot_tower': ident,
            'robotarm_cobot_j2_gear': axial_matrix(ident, 0.0, 0.0, C.J2.x_spigot_end),
        }
        for n in UA:
            where[n] = mu
        m_neutral = link_matrix(HOME_Q2, (0.0, 0.0))
        for n in HUBS + tuple(SPRING):
            where[n] = m_neutral
        where['robotarm_cobot_j2_pinion'] = axial_matrix(mu, C.J2_PIN[0], C.J2_PIN[1], C.J2.x_teeth0)
        where['robotarm_cobot_j3_pinion'] = axial_matrix(mu, C.J3_PIN[0], C.J3_PIN[1], C.J3B_X0)
        where['robotarm_cobot_j3_idler'] = axial_matrix(mu, C.J3_IDLER[0], C.J3_IDLER[1], C.IDLER_X0)
        for n in FA:
            where[n] = mf
        where['robotarm_cobot_j3_gear'] = axial_matrix(mf, 0.0, 0.0, C.J3.x_spigot_end)
        for n in WR:
            where[n] = mw
        where['robotarm_cobot_j4_gear'] = axial_matrix(mw, 0.0, 0.0, C.J4.x_spigot_end)
        where['robotarm_cobot_rotator'] = rot_matrix(mw)
        hm = adsk.core.Matrix3D.create()          # the head frame: x, y along J5, z = v; back face on the neck
        hm.translation = V3(0, (C.ROT_FACE_C - G.SHELL_BACK_Y) / 10, 0)
        hm.transformBy(mw)
        where['robotarm_grip_body'] = hm
        where['robotarm_cobot_j4_pinion'] = axial_matrix(mf, C.J4_PIN[0], C.J4_PIN[1], C.J4.x_teeth0)
        for n, m in where.items():
            o = occ_named(n)
            assert o is not None, 'missing part: ' + n
            mm_ = m.copy()
            if n in lift:
                t = adsk.core.Matrix3D.create()
                d = lift[n] / 10
                t.translation = V3(0, uw[1] * d, uw[2] * d) if n in ALONG_U else V3(d, 0, 0)
                mm_.transformBy(t)
            o.transform2 = mm_

    return place


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    P3 = adsk.core.Point3D.create
    V = adsk.core.ValueInput.createByString
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
    C.check()

    def occ_named(name):
        for o in root.occurrences:
            if o.component.name == name:
                return o
        return None

    def fresh_comp(name):
        o = occ_named(name)
        if o is not None:
            o.deleteMe()
        o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        o.component.name = name
        return o

    def box_x(comp, name, u0, u1, v0, v1, x0, x1, op):
        """A box in a link frame: y = u, z = v, x along the joints (mm)."""
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchLines.addTwoPointRectangle(sk.modelToSketchSpace(P3(0, u0 / 10, v0 / 10)),
                                                         sk.modelToSketchSpace(P3(0, u1 / 10, v1 / 10)))
        inp = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('%.5f mm' % x0))
        inp.setDistanceExtent(False, V('%.5f mm' % (x1 - x0)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(0)]
        comp.features.extrudeFeatures.add(inp).name = name

    def cyl_x(comp, name, u, v, d, x0, x1, op):
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(0, u / 10, v / 10)), d / 20)
        inp = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('%.5f mm' % x0))
        inp.setDistanceExtent(False, V('%.5f mm' % (x1 - x0)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(0)]
        comp.features.extrudeFeatures.add(inp).name = name

    # ---- 1. envelopes ------------------------------------------------------------
    def servo_env(name, servo, case, tabs, case_top, pin):
        comp = fresh_comp(name).component
        box_x(comp, 'case', case[0], case[1], case[2], case[3], case_top, case_top + servo.case_h, NEW)
        box_x(comp, 'tabs', tabs[0], tabs[1], tabs[2], tabs[3], case_top + servo.tab_below_top,
              case_top + servo.tab_below_top + servo.tab_thk, JOIN)
        cyl_x(comp, 'boss', pin[0], pin[1], servo.boss_dia, case_top - servo.boss_h, case_top, JOIN)
    servo_env('fit_mg995', C.MG995, C.J2_CASE, C.J2_TABS, C.UA_J2_CASE_TOP, C.J2_PIN)
    servo_env('fit_sg90_j3', C.SG90, C.J3_CASE, C.J3_TABS, C.UA_J3_CASE_TOP, C.J3_PIN)
    servo_env('fit_sg90_j4', C.SG90, C.J4_CASE, C.J4_TABS, C.FA_J4_CASE_TOP, C.J4_PIN)

    def board_env(name, cu, top):
        comp = fresh_comp(name).component
        b = C.BOARD / 2
        x_bot = top - C.BOARD_POCKET_H
        box_x(comp, 'board', cu - b, cu + b, -b, b, x_bot, x_bot + C.BOARD_T, NEW)
        box_x(comp, 'chip', cu - 2.5, cu + 2.5, -3.0, 3.0, x_bot - C.CHIP_H, x_bot, JOIN)
    board_env('fit_board_j2', 0.0, C.J2_BOARD_TOP)      # on the spring cap's lid, over the shaft-end magnet
    board_env('fit_board_j3', C.L1, C.UA_J3_TAB_TOP)
    board_env('fit_board_j4', C.L2, C.FA_J4_TAB_TOP)
    j5 = fresh_comp('fit_sg90_j5').component
    w5 = C.SG90.case_w / 2
    box_x(j5, 'case', C.J5_CASE[0], C.J5_CASE[1], C.J5_CASE[2], C.J5_CASE[3], -w5, w5, NEW)
    box_x(j5, 'tabs', C.J5_TABS[0], C.J5_TABS[1], C.J5_TABS[2], C.J5_TABS[3], -w5, w5, JOIN)
    # the spring at neutral: the coil as a tube, each leg a wire-square bar tangent-off at v = -RC to its cut length
    comp = fresh_comp('fit_spring').component
    cyl_x(comp, 'coil', 0.0, 0.0, C.SPR_OD, C.COIL[0], C.COIL[1], NEW)
    cyl_x(comp, 'bore', 0.0, 0.0, C.SPR_OD - 2 * C.SPR_WIRE, C.COIL[0], C.COIL[1], CUT)
    w2 = C.SPR_WIRE / 2
    box_x(comp, 'leg_lo', -C.SPR_LEG_CUT, 0.0, -C.SPR_RC - w2, -C.SPR_RC + w2, C.COIL[0], C.COIL[0] + C.SPR_WIRE, JOIN)
    box_x(comp, 'leg_hi', 0.0, C.SPR_LEG_CUT, -C.SPR_RC - w2, -C.SPR_RC + w2, C.COIL[1] - C.SPR_WIRE, C.COIL[1], JOIN)
    comp = fresh_comp('fit_dowel').component
    cyl_x(comp, 'dowel', C.J3_IDLER[0], C.J3_IDLER[1], C.IDLER_PIN_D, C.IDLER_PIN_BOTTOM, C.IDLER_PIN_TOP, NEW)

    # ---- 2. placement --------------------------------------------------------------
    place = placer(root)

    def owner(ent):
        if ent.assemblyContext is not None:
            return ent.assemblyContext.component.name
        body = adsk.fusion.BRepBody.cast(ent)
        if body is not None:
            return body.parentComponent.name
        return '?'

    def clashes(names_a, names_b=None):
        """Overlaps > VOL_TOL between parts of A (and B if given: only A x B pairs)."""
        col = adsk.core.ObjectCollection.create()
        pool = list(names_a) + (list(names_b) if names_b else [])
        for n in pool:
            o = occ_named(n)
            for i in range(o.bRepBodies.count):
                col.add(o.bRepBodies.item(i))
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        out = []
        for i in range(res.count):
            r = res.item(i)
            a, b = owner(r.entityOne), owner(r.entityTwo)
            if frozenset((a, b)) in ALLOWED:
                continue
            if names_b and not ((a in names_a and b in names_b) or (b in names_a and a in names_b)):
                continue
            vol = r.interferenceBody.volume * 1000 if r.interferenceBody else 0.0
            if vol > VOL_TOL_MM3:
                out.append((a, b, vol))
        return out

    everything = TOWER + SPRING + UA + FA + WR
    ok = True

    # ---- 3. static ----------------------------------------------------------------
    place(HOME_Q2, HOME_Q3)
    st = clashes(everything)
    print('STATIC (home pose): %s' % ('clean' if not st else 'CLASH'))
    for a, b, vol in st:
        print('   %s x %s: %.2f mm3' % (a, b, vol))
    ok = ok and not st

    # ---- 4. insertion paths ---------------------------------------------------------
    def replay(build, base):
        good = True
        fitted = list(base)
        for step, parts in build:
            worst = None
            d = 0.0
            out = OUT_FULL.get(step, OUT_MM)
            while d <= out + 1e-9:
                place(HOME_Q2, HOME_Q3, {n: d for n in parts})
                c = clashes(parts, fitted)
                if c:
                    worst = (d, c)
                    break
                d += STEP_MM
            if worst:
                print('INSERT %-44s BLOCKED at %.0f mm out: %s' % (
                    step, worst[0], '; '.join('%s x %s %.1f mm3' % x for x in worst[1][:3])))
                good = False
            else:
                print('INSERT %-44s clear along -%s (%d mm)' % (step, 'u' if set(parts) & ALONG_U else 'x', out))
            fitted += parts
        return good
    ok = replay(BUILD, ['robotarm_cobot_tower', 'robotarm_cobot_forearm', 'robotarm_cobot_forearm_plate']) and ok
    ok = replay(WR_BUILD, WR_BASE) and ok
    ok = replay(FA_BUILD, FA_BASE) and ok
    place(HOME_Q2, HOME_Q3)

    # ---- 5. poses -------------------------------------------------------------------
    fold = []
    for q3 in Q3_SWEEP:
        place(HOME_Q2, q3)
        c = clashes(UA, FA)
        fold.append((q3, c))
        print('POSE J3 %+5.0f: %s' % (q3, 'clean' if not c else 'CLASH ' + '; '.join(
            '%s x %s %.0f mm3' % x for x in c[:3])))
    for q4 in Q4_SWEEP:
        place(HOME_Q2, HOME_Q3, None, q4)
        c = clashes(WR, FA)
        print('POSE J4 %+5.0f: %s' % (q4, 'clean' if not c else 'CLASH ' + '; '.join(
            '%s x %s %.0f mm3' % x for x in c[:3])))
    for q2 in Q2_SWEEP:
        place(q2, HOME_Q3)
        c = clashes(TOWER, UA + FA)
        print('POSE J2 %+5.0f: %s' % (q2, 'clean' if not c else 'CLASH ' + '; '.join(
            '%s x %s %.0f mm3' % x for x in c[:3])))
    place(HOME_Q2, HOME_Q3)
    print('VERDICT: %s (static + insertion; pose clashes are fold LIMITS, reported not failed)'
          % ('PASS' if ok else 'FAIL'))
