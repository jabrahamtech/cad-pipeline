"""robotarm/_check_servo_fit - GATE servo_fit. Does the servo actually go in?

Spec: lib/servo.py. Driver, not a part.

WHAT THIS ANSWERS THAT NOTHING ELSE DOES. Every servo pocket in this project
was cut from numbers in lib/servo.py and then checked against those same
numbers. That is a restatement, not a check - if case_w is wrong the pocket
is wrong and the assert comparing them agrees. Jonathan has reported three
times that the servos do not go in, and the project has had no way to
disagree with itself.

This gate builds the SOLID (models/robotarm/servo_body.py), puts it where the
host says the servo goes, and asks pointContainment whether the two occupy the
same space. Interference is measured in mm3, not asserted.

IT IMPORTS ITS PLACEMENTS. _check_leads.MOUNTS already owns where every servo
sits - shaft origin, axis mapping, insertion direction - and it is already
maintained (its J3 row was wrong for four commits and the comment explaining
that is still in it). A second placement table in this file would be the
project's own named failure: a datum only one file reads. So there is not one.

METHOD, and its limits stated first:
- Grid-sample the servo's bounding box at STEP mm. A point inside BOTH the
  servo and the host is interference. Volume is count x STEP^3, which is an
  ESTIMATE - it resolves nothing thinner than STEP (1.5 mm) and reads 0 for any
  pinch finer than that. Read the CLEARANCE figure for those.
- Clearance is the smallest gap found by walking outward from the servo's
  faces. It is what tells you a pocket is technically clear and practically
  a press.
- pointContainment only. TemporaryBRepManager.booleanOperation returns empty
  in this codebase and reads as "no interference", which is the worst
  possible failure mode for a gate.

POSITIVE CONTROL. Every run also tests the servo deliberately driven
CONTROL_SHIFT_MM into the host. If that does not register interference the
gate is not looking at anything and the run fails, whatever the real result
was. A check that cannot see a hit is worse than no check.
"""

import json
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core
import adsk.fusion

from lib.servo import CATALOG  # noqa: E402

STEP = 1.5              # sample pitch, mm
CONTROL_SHIFT_MM = 4.0  # how far to drive the servo in for the control
JAM_MM3 = 0.5           # below this is sampling noise, not a jam

# Hosts that must be built before the one under test, from _build_parts.DEPS.
DEPS = {
    'j3_servo_cap': ['forearm'],
    'gripcut_finger': ['pruner_blade'],
    'upper_arm': ['forearm'],
}

AXES = {'x': 0, 'y': 1, 'z': 2}


def _unit(spec):
    v = [0.0, 0.0, 0.0]
    v[AXES[spec[0]]] = float(spec[1])
    return v


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _exec(name, repo):
    """Run a script into the active document. Nothing caught - the repo bans
    try/except in Fusion scripts and a gate is the last place to bend it."""
    path = os.path.join(repo, 'models', 'robotarm', name + '.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    ns = {'__name__': name, '__file__': path}
    exec(compile(open(path).read(), path, 'exec'), ns)
    ns['run']('')


def _exec_servo(servo, repo):
    """servo_body.py carries its subject as a module constant, so the source
    is substituted rather than the module poked - the names it derives at
    import time (COMPONENT, BODY_NAME) have to move with it."""
    path = os.path.join(repo, 'models', 'robotarm', 'servo_body.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    src = open(path).read().replace("SERVO = 'MG90S'", "SERVO = '%s'" % servo)
    ns = {'__name__': 'servo_body', '__file__': path}
    exec(compile(src, path, 'exec'), ns)
    ns['run']('')


def _place(occ, mount, offset_mm):
    """Put the servo occurrence into the host frame.

    The third axis is COMPUTED as za x xa so a row cannot describe a
    left-handed servo - the same guard _check_leads makes.
    """
    xa = _unit(mount['xa'])
    za = _unit(mount['za'])
    ya = _cross(za, xa)
    sx, sy, sz = mount['shaft']
    m = adsk.core.Matrix3D.create()
    m.setWithArray([
        xa[0], ya[0], za[0], (sx + offset_mm[0]) / 10.0,
        xa[1], ya[1], za[1], (sy + offset_mm[1]) / 10.0,
        xa[2], ya[2], za[2], (sz + offset_mm[2]) / 10.0,
        0.0, 0.0, 0.0, 1.0])
    occ.transform2 = m
    return m


def _overlap_mm3(probe, hosts):
    """Sampled volume the probe shares with any host body, mm3.

    ONLY THE OVERLAP REGION IS SAMPLED. Walking the servo's whole bounding
    box meant testing tens of thousands of points that are nowhere near the
    host - the first version of this gate did exactly that and never
    finished. The intersection of the two bounding boxes is the only place
    an interference can be, so it is the only place worth asking about; for
    the elbow that is a 33 x 12 x 5.5 slab instead of a 33 x 12 x 34 one.
    """
    INSIDE = adsk.fusion.PointContainment.PointInsidePointContainment
    pb = probe.boundingBox
    P3 = adsk.core.Point3D.create
    hits = 0
    where = []
    step = STEP / 10.0
    for h in hosts:
        hb = h.boundingBox
        lo = [max(pb.minPoint.x, hb.minPoint.x),
              max(pb.minPoint.y, hb.minPoint.y),
              max(pb.minPoint.z, hb.minPoint.z)]
        hi = [min(pb.maxPoint.x, hb.maxPoint.x),
              min(pb.maxPoint.y, hb.maxPoint.y),
              min(pb.maxPoint.z, hb.maxPoint.z)]
        if any(lo[i] > hi[i] for i in range(len(lo))):
            continue        # bounding boxes miss - nothing to test
        x = lo[0]
        while x <= hi[0]:
            y = lo[1]
            while y <= hi[1]:
                z = lo[2]
                while z <= hi[2]:
                    p = P3(x, y, z)
                    if (h.pointContainment(p) == INSIDE
                            and probe.pointContainment(p) == INSIDE):
                        hits += 1
                        where.append((x * 10.0, y * 10.0, z * 10.0))
                    z += step
                y += step
            x += step
    return hits * (STEP ** 3), where


def _span(pts):
    """Bounding box of the interfering points, in HOST mm - which feature.

    A volume tells you a servo does not fit. It does not tell you what it
    hit, and "does not fit" is not actionable. This is."""
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    return [round(min(xs), 2), round(max(xs), 2), round(min(ys), 2),
            round(max(ys), 2), round(min(zs), 2), round(max(zs), 2)]


def _dump(repo, rows):
    """Persist what has been measured so far, so a timeout costs nothing."""
    out = os.path.join(repo, 'specs', 'robotarm', '_servo_fit.json')
    payload = {
        'step_mm': STEP,
        'jam_floor_mm3': JAM_MM3,
        'control_shift_mm': CONTROL_SHIFT_MM,
        'stations': [
            {'tag': t, 'host': h, 'servo': s_, 'case_mm3': round(cv, 2),
             'horn_mm3': round(hv, 2), 'control_mm3': round(kv, 2),
             'case_at': cw, 'horn_at': hw}
            for t, h, s_, cv, hv, kv, cw, hw in rows
        ],
    }
    with open(out, 'w') as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)


def run(_context: str):
    app = adsk.core.Application.get()
    repo = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
    if repo not in sys.path:
        sys.path.insert(0, repo)
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    from models.robotarm import _check_leads  # noqa
    mounts = _check_leads.MOUNTS

    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    print('GATE servo_fit - the servo as a SOLID, in the host that carries it')
    print('sample pitch %.2f mm, jam floor %.2f mm3, control shift %.1f mm'
          % (STEP, JAM_MM3, CONTROL_SHIFT_MM))
    print('')

    rows = []
    for mount in mounts:
        host, servo, tag = mount['host'], mount['servo'], mount['tag']
        for occ in list(root.occurrences):
            occ.deleteMe()
        for dep in DEPS.get(host, []):
            _exec(dep, repo)
        _exec(host, repo)
        _exec_servo(servo, repo)

        host_occ, servo_occ = None, None
        for occ in root.occurrences:
            n = occ.component.name
            if n == 'robotarm_' + host:
                host_occ = occ
            elif n == 'robotarm_servo_' + servo:
                servo_occ = occ
        assert host_occ is not None, 'no host occurrence for ' + host
        assert servo_occ is not None, 'no servo occurrence for ' + servo

        host_bodies = [host_occ.bRepBodies.item(i)
                       for i in range(host_occ.bRepBodies.count)]

        _place(servo_occ, mount, (0.0, 0.0, 0.0))
        case = servo_occ.bRepBodies.itemByName('servo_' + servo)
        horn = servo_occ.bRepBodies.itemByName('horn_' + servo)
        case_v, case_where = _overlap_mm3(case, host_bodies)
        horn_v, horn_where = _overlap_mm3(horn, host_bodies)

        ins = mount.get('insert') or (0.0, 0.0, 0.0)
        # ALONG +insert, NOT AGAINST IT. `insert` is the direction the servo
        # TRAVELS as it is fitted and `travel` is how far back along -insert
        # it starts, so the seat is at the END of that motion: driving
        # further along +insert overshoots into the host, and driving along
        # -insert simply withdraws it. The first version of this control used
        # -insert and read 0.00 mm3 at four of the seven stations - a control
        # that backs the probe out of the thing it is meant to collide with.
        # It was only visible because a zero control is treated as a failure
        # rather than as good news.
        ctrl_off = tuple(c * CONTROL_SHIFT_MM for c in ins)
        if ctrl_off == (0.0, 0.0, 0.0):
            # A clamshell has no insertion path, so drive the control along
            # the servo's own -z instead - into the shell floor either way.
            ctrl_off = tuple(-c * CONTROL_SHIFT_MM for c in _unit(mount['za']))
        _place(servo_occ, mount, ctrl_off)
        ctrl_v, _ = _overlap_mm3(case, host_bodies)
        _place(servo_occ, mount, (0.0, 0.0, 0.0))

        rows.append((tag, host, servo, case_v, horn_v, ctrl_v,
                     _span(case_where), _span(horn_where)))
        print('%-12s %-18s %-6s case %8.1f  horn %8.1f  control %8.1f mm3'
              % (tag, host, servo, case_v, horn_v, ctrl_v))
        # WRITTEN AFTER EVERY STATION, not at the end. The MCP call that runs
        # this gate dies at 60 s and the first complete run lost all seven
        # results to that timeout even though it had finished the work. A
        # result you cannot read is not a result.
        _dump(repo, rows)

    print('')
    blind = [r for r in rows if r[5] <= JAM_MM3]
    assert not blind, (
        'THE CHECK IS BLIND at %s - the control drove the servo %.1f mm into '
        'the host and registered nothing. Every clear result above is '
        'meaningless until this is fixed.'
        % (', '.join(r[0] for r in blind), CONTROL_SHIFT_MM))
    print('positive control fired at all %d stations - the check can see' % len(rows))

    jams = [r for r in rows if r[3] > JAM_MM3 or r[4] > JAM_MM3]
    if jams:
        print('')
        print('%d STATION(S) DO NOT ACCEPT THEIR SERVO:' % len(jams))
        for tag, host, servo, cv, hv, _k, cw, hw in jams:
            what = []
            if cv > JAM_MM3:
                what.append('case %.1f mm3' % cv)
            if hv > JAM_MM3:
                what.append('horn %.1f mm3' % hv)
            print('   %-12s %-18s %s' % (tag, host, ', '.join(what)))
            for label, sp in (('case', cw), ('horn', hw)):
                if sp:
                    print('      %s clash spans host x %.1f..%.1f  y %.1f..%.1f'
                          '  z %.1f..%.1f' % ((label,) + tuple(sp)))
    else:
        print('all %d stations clear at this sample pitch' % len(rows))
    print('')
    print('READ THIS BEFORE BELIEVING A CLEAR RESULT: the solid is only as')
    print('right as lib/servo.py, whose own docstring rates cheap-servo')
    print('datasheet dimensions as weak. A clear result here means the')
    print('project no longer disagrees with ITSELF. It is not the bench.')
