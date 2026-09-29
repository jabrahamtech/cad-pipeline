"""robotarm/_check_cobot_mesh - GEARS AND SERVOS, MEASURED on the built parts (not a part).

Jonathan, 2026-09-29: "could you first confirm all the gears and servos etc
fit correctly".

Run with every cobot part built in the active document (after _check_cobot_fit,
which adds the fit_ envelopes). It poses the arm at home with the gate's own
placer. Nothing here is read from lib/cobot's intent; it is measured on the
Fusion bodies:

  1. MESH - for each gear pair, hold the gear and turn the pinion through one
     tooth pitch to find the window where the teeth do not touch. The window's
     width x the pinion's pitch radius is the BACKLASH of the teeth as built.
     Then turn the pair TOGETHER, coupled by the tooth ratio, through one full
     gear tooth from the window's centre: every step must be free (no binding
     anywhere in the mesh cycle) and the flank gap is reported.
  2. SERVOS - each servo envelope (case, tabs, output boss) and a LEAD STUB
     (the bundle leaving its end face, lib/servo lead_x/y/z, LEAD_STUB_MM long):
     the nearest parts and the gap to each.
  3. GEARS IN THEIR HOUSINGS - each gear, pinion, idler and spring hub: the
     nearest part that is NOT its mate, and the gap.
Prints a verdict per check and PASS / FAIL.
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

_GATE = os.path.join(REPO, 'models', 'robotarm', '_check_cobot_fit.py')

VOL_TOL_MM3 = 0.001        # any overlap above this is a hit (tessellation noise is far below)
SCAN_STEP_DEG = 0.5        # the phase scan; every window here is > 0.8 deg wide
BISECT_DEG = 0.01          # the window edges to this
SWEEP_STEPS = 12           # coupled steps through one gear tooth
LEAD_STUB_MM = 5.0         # ASSUMED - the straight run of a lead before it can bend
TOUCH_MM = 0.005           # a gap under this is contact

# (label, member A, teeth A, member B, teeth B, B's pitch radius mm)
PAIRS = [
    ('J2   36T gear / 22T MG995 pinion', 'robotarm_cobot_j2_gear', C.J2_PAIR.z_gear,
     'robotarm_cobot_j2_pinion', C.J2_PAIR.z_pinion, C.J2_PAIR.r_pitch(C.J2_PAIR.z_pinion)),
    ('J3a  36T gear / 18T idler', 'robotarm_cobot_j3_gear', C.J3A_PAIR.z_gear,
     'robotarm_cobot_j3_idler', C.J3A_PAIR.z_pinion, C.J3A_PAIR.r_pitch(C.J3A_PAIR.z_pinion)),
    ('J3b  36T idler / 18T SG90 pinion', 'robotarm_cobot_j3_idler', C.J3B_PAIR.z_gear,
     'robotarm_cobot_j3_pinion', C.J3B_PAIR.z_pinion, C.J3B_PAIR.r_pitch(C.J3B_PAIR.z_pinion)),
    ('J4   36T gear / 18T SG90 pinion', 'robotarm_cobot_j4_gear', C.J4_PAIR.z_gear,
     'robotarm_cobot_j4_pinion', C.J4_PAIR.z_pinion, C.J4_PAIR.r_pitch(C.J4_PAIR.z_pinion)),
]
MATES = {frozenset((a, b)) for _, a, _, b, _, _ in PAIRS}
MATES |= {frozenset(p) for p in (
    ('fit_sg90_j5', 'robotarm_cobot_rotator'), ('fit_dowel', 'robotarm_cobot_upper_arm'),
    ('fit_dowel', 'robotarm_cobot_j3_idler'))}

# servo envelopes and where each lead leaves: (envelope, servo, end-face axis, face, direction, centre (u|v, x))
SERVOS = [
    ('fit_mg995', C.MG995, 'u', C.J2_CASE[0], -1, C.J2_PIN[1],
     C.UA_J2_CASE_TOP + C.MG995.tab_below_top - C.MG995.lead_z),
    ('fit_sg90_j3', C.SG90, 'u', C.J3_CASE[1], +1, C.J3_PIN[1],
     C.UA_J3_CASE_TOP + C.SG90.tab_below_top - C.SG90.lead_z),
    ('fit_sg90_j4', C.SG90, 'v', C.J4_CASE[2], -1, C.J4_PIN[0],
     C.FA_J4_CASE_TOP + C.SG90.tab_below_top - C.SG90.lead_z),
]
MOVING = ['robotarm_cobot_j2_gear', 'robotarm_cobot_j2_pinion', 'robotarm_cobot_j3_gear', 'robotarm_cobot_j3_idler',
          'robotarm_cobot_j3_pinion', 'robotarm_cobot_j4_gear', 'robotarm_cobot_j4_pinion',
          'robotarm_cobot_j2_hub_lo', 'robotarm_cobot_j2_hub_hi', 'robotarm_cobot_rotator']


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    P3 = adsk.core.Point3D.create
    V3 = adsk.core.Vector3D.create
    V = adsk.core.ValueInput.createByString
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    mm = app.measureManager
    C.check()
    import importlib.util
    spec = importlib.util.spec_from_file_location('cobot_fit_gate', _GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    def occ_named(name):
        for o in root.occurrences:
            if o.component.name == name:
                return o
        raise AssertionError('missing part (run _check_cobot_fit first): ' + name)

    def overlap(oa, ob):
        col = adsk.core.ObjectCollection.create()
        for o in (oa, ob):
            for i in range(o.bRepBodies.count):
                col.add(o.bRepBodies.item(i))
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        return sum(res.item(i).interferenceBody.volume * 1000 for i in range(res.count)
                   if res.item(i).interferenceBody)

    def gap(oa, ob):
        best = None
        for i in range(oa.bRepBodies.count):
            for j in range(ob.bRepBodies.count):
                d = mm.measureMinimumDistance(oa.bRepBodies.item(i), ob.bRepBodies.item(j)).value * 10
                best = d if best is None else min(best, d)
        return best

    def axis_of(o):
        """The member's own axis: local z through its origin (every gear script builds about it)."""
        bb = o.component.bRepBodies.item(0).boundingBox
        off = math.hypot(bb.minPoint.x + bb.maxPoint.x, bb.minPoint.y + bb.maxPoint.y) / 2 * 10
        assert off < 0.05, '%s is not built about its origin (%.2f mm off)' % (o.component.name, off)
        return P3(0, 0, 0)

    def turned(o, placed, deg):
        r = adsk.core.Matrix3D.create()
        r.setToRotation(math.radians(deg), V3(0, 0, 1), axis_of(o))
        r.transformBy(placed)
        return r

    def stub(env, servo, axis, face, sense, centre, x_mid):
        name = env.replace('fit_', 'fit_lead_')
        for o in root.occurrences:
            if o.component.name == name:
                o.deleteMe()
        o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        o.component.name = name
        comp = o.component
        h = servo.lead_bundle_dia / 2
        a0, a1 = sorted((face, face + sense * LEAD_STUB_MM))
        if axis == 'u':
            u0, u1, v0, v1 = a0, a1, centre - h, centre + h
        else:
            u0, u1, v0, v1 = centre - h, centre + h, a0, a1
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(sk.modelToSketchSpace(P3(0, u0 / 10, v0 / 10)),
                                                         sk.modelToSketchSpace(P3(0, u1 / 10, v1 / 10)))
        inp = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), NEW)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('%.5f mm' % (x_mid - h)))
        inp.setDistanceExtent(False, V('%.5f mm' % (2 * h)))
        comp.features.extrudeFeatures.add(inp).name = 'lead_stub'
        return o

    ok = True
    stubs = {env: stub(env, servo, axis, face, sense, centre, x_mid)
             for env, servo, axis, face, sense, centre, x_mid in SERVOS}
    gate.placer(root)(gate.HOME_Q2, gate.HOME_Q3)
    for env, so in stubs.items():
        so.transform2 = occ_named(env).transform2.copy()

    # ---- 1. mesh ---------------------------------------------------------------------
    print('MESH (measured on the built teeth)')
    for label, na, za, nb, zb, rb in PAIRS:
        oa, ob = occ_named(na), occ_named(nb)
        pa, pb = oa.transform2.copy(), ob.transform2.copy()
        za_w, zb_w = pa.getAsCoordinateSystem()[3], pb.getAsCoordinateSystem()[3]
        sign = -1.0 if za_w.dotProduct(zb_w) > 0 else 1.0      # external mesh: opposite senses

        def pose(alpha, phi):
            oa.transform2 = turned(oa, pa, alpha)
            ob.transform2 = turned(ob, pb, phi + sign * alpha * za / zb)

        def free(phi):
            pose(0.0, phi)
            return overlap(oa, ob) <= VOL_TOL_MM3

        pitch = 360.0 / zb
        n = int(round(pitch / SCAN_STEP_DEG))
        states = [free(k * pitch / n) for k in range(n)]
        if all(states) or not any(states):
            print('  %s: %s' % (label, 'NEVER TOUCHES (no mesh)' if all(states) else 'ALWAYS HITS (binds)'))
            ok = False
            oa.transform2, ob.transform2 = pa, pb
            continue
        k0 = next(k for k in range(n) if states[k] and not states[k - 1])     # first free after a hit
        k1 = k0
        while states[(k1 + 1) % n]:
            k1 += 1

        def edge(lo_hit, hi_free):
            while abs(hi_free - lo_hit) > BISECT_DEG:
                mid = (lo_hit + hi_free) / 2
                if free(mid):
                    hi_free = mid
                else:
                    lo_hit = mid
            return hi_free
        step = pitch / n
        w0 = edge((k0 - 1) * step, k0 * step)
        w1 = edge((k1 + 1) * step, k1 * step)
        width = w1 - w0
        backlash = math.radians(width) * rb
        centre = (w0 + w1) / 2
        gaps, hits = [], 0
        for k in range(SWEEP_STEPS + 1):
            alpha = (360.0 / za) * k / SWEEP_STEPS
            pose(alpha, centre)
            if overlap(oa, ob) > VOL_TOL_MM3:
                hits += 1
            gaps.append(gap(oa, ob))
        good = hits == 0 and 0.05 <= backlash <= 0.8
        ok = ok and good
        print('  %s: backlash %.2f mm at the pinion pitch circle (window %.2f deg); '
              'through one full tooth, coupled %d:%d: %s, flank gap %.2f..%.2f mm  %s'
              % (label, backlash, width, za, zb, 'FREE' if not hits else '%d BINDS' % hits,
                 min(gaps), max(gaps), 'ok' if good else 'CHECK'))
        oa.transform2, ob.transform2 = pa, pb

    # ---- 2. servos + lead stubs ---------------------------------------------------------
    everything = [o for o in root.occurrences if o.isLightBulbOn and o.bRepBodies.count
                  and not o.component.name.startswith('cobot_plate_')]

    def nearest(o, skip=(), k=4):
        out = []
        for p in everything:
            if p.component.name == o.component.name or p.component.name in skip:
                continue
            d = gap(o, p)
            out.append((d, p.component.name))
        out.sort()
        return out[:k]

    def report(o, label, skip=()):
        global_ok = True
        near = nearest(o, skip)
        parts = []
        for d, n in near:
            tag = ''
            if d < TOUCH_MM:
                v = overlap(o, occ_named(n))
                tag = ' OVERLAP %.2f mm3' % v if v > VOL_TOL_MM3 else ' (touching)'
                global_ok = global_ok and v <= VOL_TOL_MM3
            parts.append('%s %.2f%s' % (n.replace('robotarm_', '').replace('cobot_', ''), d, tag))
        print('  %-26s %s' % (label, ' | '.join(parts)))
        return global_ok

    print('SERVOS (envelope = case + tabs + output boss; gaps in mm to the nearest parts)')
    for env, servo, axis, face, sense, centre, x_mid in SERVOS:
        so = stubs[env]
        ok = report(occ_named(env), env, (so.component.name,)) and ok
        ok = report(so, '  its lead stub (%.0f mm)' % LEAD_STUB_MM, (env,)) and ok

    ok = report(occ_named('fit_sg90_j5'), 'fit_sg90_j5 (lead: back port)', ('robotarm_cobot_rotator',)) and ok

    print('GEARS IN THEIR HOUSINGS (nearest part that is not the mate)')
    for n in MOVING:
        o = occ_named(n)
        mates = {m for pr in MATES if n in pr for m in pr if m != n}
        ok = report(o, n.replace('robotarm_cobot_', ''), mates) and ok

    print('VERDICT: %s' % ('PASS' if ok else 'FAIL'))
