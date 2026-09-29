"""robotarm/_check_head_sweep - GATE: does the grip head clear the forearm?

Driver, not a part. The head (grip v3) is a 65 mm 12-gon, and it hangs off the
J5 rotator in front of the J4 wrist pitch. _check_wrist sweeps the wrist
housing and never had a head in it; _check_grip poses the head on its own.
Nothing had asked whether the head, pitching about J4, runs into the
forearm, its J4 hubs or the geared elbow behind them. This does.

Runs in a document that already holds every part (_check_ledger batches +
the grip_* parts, i.e. the document _preview_arm renders from). Everything
is placed in the FOREARM's frame - origin on J4 - using _preview_arm's own
chain, then J4 is swept over J4_SWEEP_DEG and J5 over J5_SWEEP_DEG, and
Design.analyzeInterference runs between the moving side (wrist_roll,
rotator, the head) and the fixed side (forearm, its hubs, the J3 drive).

Positive control: the head's back face is also placed 3 mm INTO the rotator
in one extra pose, which must be reported.
"""

import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
J4_SWEEP_DEG = (-90.0, -60.0, -30.0, 0.0, 30.0, 60.0, 90.0)
J5_SWEEP_DEG = (0.0, 90.0)
OPEN_MM = 20.0
POSE_TAG = 'hs_'
LIMIT_MM3 = 0.001
CONTROL_SINK_MM = 3.0


def run(_context: str):
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    import lib.grip as G
    from lib.joints import J5_ROTATOR_ORIGIN_PARTS
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    M3 = adsk.core.Matrix3D.create
    P3 = adsk.core.Point3D.create
    VEC = adsk.core.Vector3D.create
    ORG = P3(0, 0, 0)

    def gv(n):
        p = ups.itemByName(n)
        assert p is not None, 'missing ' + n
        return p.value

    comps = {}
    for o in root.occurrences:
        comps.setdefault(o.component.name.replace('robotarm_', ''), o.component)
    need = ('forearm', 'wrist_hub', 'wrist_roll', 'wrist_rotator', 'j3_gear', 'j3_pinion',
            'j3_axle', 'j3_servo_cap', 'grip_body', 'grip_jaw', 'grip_finger', 'gripper_pinion')
    missing = [n for n in need if n not in comps]
    assert not missing, 'not in this document: %r' % missing

    def mul(a, b):
        m = b.copy()
        m.transformBy(a)
        return m

    def rot(a, axis):
        m = M3()
        m.setToRotation(a, axis, ORG)
        return m

    def rotx(d):
        return rot(math.radians(d), VEC(1, 0, 0))

    def trans(x, y, z):
        m = M3()
        t = m.translation
        t.x, t.y, t.z = x, y, z
        m.translation = t
        return m

    def frame(o, ax, ay, az):
        m = M3()
        m.setWithCoordinateSystem(P3(*o), VEC(*ax), VEC(*ay), VEC(*az))
        return m

    def bbox(n):
        return comps[n].bRepBodies.item(0).boundingBox

    # ---- the fixed side, in the forearm frame (as _preview_arm) ----
    l2 = gv('fa_l2')
    fa_in = gv('fa_plate_in')

    def place_hub(sx, y_p, plate_in):
        mm_ = rot(math.pi / 2, VEC(0, 0, 1))
        mm_.transformBy(rot(-sx * math.pi / 2, VEC(0, 1, 0)))
        t = mm_.translation
        t.x, t.y = sx * plate_in, y_p
        mm_.translation = t
        return mm_

    po, fr, so_ = gv('fa_plate_out'), gv('fa_free'), gv('fa_j3_standoff')
    y_pin = -l2 + gv('fa_j3_centre')
    face = gv('jp_face')
    # The J4 wrist_hubs are NOT fixed: their hex is keyed into wrist_roll's
    # socket and they turn WITH it (the J4 servo drives through them). The
    # first run held them still and reported the hex against the turned
    # socket - 40.6 mm3 at every J4 that is not a multiple of 60 deg.
    hubs = [place_hub(+1, 0.0, fa_in), place_hub(-1, 0.0, fa_in)]
    fixed = [('forearm', M3()),
             ('j3_gear', frame((-(po + fr), -l2, 0.0), (0, 0, 1), (0, 1, 0), (-1, 0, 0))),
             ('j3_pinion', frame((-(po + fr + face), y_pin, 0.0), (0, 0, 1), (0, -1, 0), (1, 0, 0))),
             ('j3_axle', frame((gv('ua_half_x') - gv('ua_socket_d'), -l2, 0.0),
                               (0, 0, 1), (0, -1, 0), (1, 0, 0))),
             ('j3_servo_cap', frame((-(po + so_), y_pin, 0.0), (0, 1, 0), (0, 0, -1), (-1, 0, 0)))]

    shell_tail = bbox('grip_body').minPoint.y
    rot_front = bbox('wrist_rotator').maxPoint.z
    turned = rot(math.pi, VEC(0, 1, 0))

    def moving(j4, j5, sink=0.0):
        M_roll = rotx(j4)
        m = rot(math.radians(j5), VEC(0, 0, 1))
        m.transformBy(rot(-math.pi / 2, VEC(1, 0, 0)))
        t = m.translation
        t.y = sum(gv(p) for p in J5_ROTATOR_ORIGIN_PARTS)
        m.translation = t
        M_rot = mul(M_roll, m)
        mh = rotx(90)
        t = mh.translation
        t.z = rot_front - shell_tail - sink / 10
        mh.translation = t
        M_sh = mul(M_rot, mh)
        s = OPEN_MM
        pin = rot(G.s_to_phase(s), VEC(0, 0, 1))
        pin.transformBy(rot(-math.pi / 2, VEC(1, 0, 0)))
        out = [('wrist_roll', M_roll), ('wrist_rotator', M_rot),
               ('wrist_hub', mul(M_roll, hubs[0])), ('wrist_hub', mul(M_roll, hubs[1])),
               ('grip_body', M_sh),
               ('gripper_pinion', mul(M_sh, mul(trans(0, G.PINION_BACK_Y / 10, 0), pin)))]
        for sgn in (1, -1):
            base = turned if sgn < 0 else M3()
            out.append(('grip_jaw', mul(M_sh, mul(trans(sgn * s / 10, 0, 0), base))))
            out.append(('grip_finger', mul(M_sh, mul(
                trans(sgn * (s - G.FINGER_LEAD) / 10, G.FINGER_Y0 / 10, 0), base))))
        return out

    def interfere(pairs_fixed, pairs_moving):
        add = root.occurrences.addExistingComponent
        occs_f = [add(comps[n], m) for n, m in pairs_fixed]
        occs_m = [add(comps[n], m) for n, m in pairs_moving]
        for o in occs_f + occs_m:
            o.isLightBulbOn = True
        col = adsk.core.ObjectCollection.create()
        for o in occs_f + occs_m:
            col.add(o)
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        MOVING = ('wrist_roll', 'wrist_rotator', 'wrist_hub', 'grip_body', 'grip_jaw', 'grip_finger',
                  'gripper_pinion')

        def nm(e):
            if hasattr(e, 'component'):
                return e.component.name.replace('robotarm_', '')
            o = e.assemblyContext
            return (o.component.name if o else e.parentComponent.name).replace('robotarm_', '')
        hits = []
        for i in range(res.count):
            r = res.item(i)
            v = r.interferenceBody.volume * 1000
            if v < LIMIT_MM3:
                continue
            a, b = nm(r.entityOne), nm(r.entityTwo)
            if (a in MOVING) != (b in MOVING) or \
                    ({a, b} & {'wrist_rotator'} and (a.startswith('grip_') or b.startswith('grip_'))):
                hits.append((v, a, b))
        for o in occs_f + occs_m:
            o.deleteMe()
        return hits

    for o in root.occurrences:
        o.isLightBulbOn = False
    ctrl = interfere([], moving(0.0, 0.0, sink=CONTROL_SINK_MM))
    ctrl_v = sum(v for v, a, b in ctrl if 'rotator' in a or 'rotator' in b)
    print('=== GATE head sweep: J4 %s x J5 %s, jaws %.0f open ===' % (
        list(J4_SWEEP_DEG), list(J5_SWEEP_DEG), 2 * OPEN_MM))
    print('positive control (head %.0f mm into the rotator): %.1f mm3 (must be > 0)'
          % (CONTROL_SINK_MM, ctrl_v))
    worst, bad = [], 0
    for j5 in J5_SWEEP_DEG:
        for j4 in J4_SWEEP_DEG:
            hits = interfere(fixed, moving(j4, j5))
            hits = [h for h in hits if not ('rotator' in h[1] or 'rotator' in h[2])
                    or 'grip_' not in h[1] + h[2]]
            if hits:
                bad += 1
                worst.append((j4, j5, sum(v for v, a, b in hits),
                              sorted(set('%s^%s' % (a, b) for v, a, b in hits))))
    for j4, j5, v, names in worst:
        print('  J4 %+4.0f J5 %3.0f: %8.1f mm3  %s' % (j4, j5, v, ', '.join(names)))
    clear = [(j4, j5) for j5 in J5_SWEEP_DEG for j4 in J4_SWEEP_DEG
             if not any(w[0] == j4 and w[1] == j5 for w in worst)]
    print('clear poses: %d of %d' % (len(clear), len(J4_SWEEP_DEG) * len(J5_SWEEP_DEG)))
    print('GATE head_sweep: %s' % ('PASS' if ctrl_v > 0 and not bad else 'FAIL'))
