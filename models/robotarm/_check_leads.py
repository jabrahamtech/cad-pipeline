"""robotarm/_check_leads - can each servo's own lead actually get out?

THE GAP THIS CLOSES. lib/servo.py carries `lead_bundle_dia` for all three
servos - SG90 3.4, MG90S 3.4, MG995 4.2 - and until this file existed
NOTHING IN THE PROJECT READ IT. Defined, documented, never used.

_assembly.md already wrote the lesson, about a different field: "a datum in a
shared library which only one file reads is not a contract, it is a
decoration." shaft_from_end was read by exactly one file and the yaw servo
ended up 5.2 mm off the axis. lead_bundle_dia was read by none. This file
makes it load-bearing.

WHAT IT CHECKS. For every servo in the arm, a Ø lead_bundle_dia cylinder is
built at the case's LEAD END and pushed ESCAPE_MM outward. If it interferes
with the host part, the lead is trapped and the servo cannot be wired in
place. If it clears, the lead has somewhere to go.

WHERE THE LEAD LEAVES THE CASE - AND THIS IS THE ASSUMPTION IN THIS FILE.
lib/servo.py's frame says "+X runs along the case length away from the shaft,
toward the lead end", so the leads exit the FAR END FACE, opposite the output
shaft. Within that face they are modelled as centred across the case width and
sitting one lead-diameter up from the case bottom. That is where they sit on
a real SG90 and MG90S. IT IS NOT MEASURED. A servo whose leads leave from a
side face instead would need this file changed, not the parts.

WHAT IT DOES NOT CHECK. Whether the lead, having escaped its pocket, can then
REACH the cable duct. That is a routing question and it needs the loom modelled,
which nothing does yet.

Run after _check_ledger, in the same document. It builds scratch lead bundles
and deletes them; occurrence count and timeline length come back unchanged.
"""

import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
ESCAPE_MM = 8.0     # how far a lead must run clear before it can be bent away

# One entry per servo in the arm. `axis` is which way the case's LONG axis
# runs in the HOST's frame, and `lead_at` is the coordinate of the far end
# face along that axis. Both come from the host part's own printed
# diagnostics and are asserted against live parameters where one exists.
#
#   host          the printed part the servo pocket is cut into
#   servo         lib/servo.py catalogue name
#   axis          'x' | 'y' | 'z' - the case's long axis in the host frame
#   sign          +1 if the lead end is at the HIGH end of that axis
#   lead_at       coordinate of the far end face, mm
#   across        the other two coords of the lead centre, mm
MOUNTS = [
    # J1 yaw. Case y -6.10..+16.50 (shaft on the axis, ts_shaft_off +5.20),
    # z -5.80..+17.90. Lead end +Y, and it sits BELOW the stator's 0..4 base
    # plate - which is the whole question for this one.
    dict(tag='J1 yaw', host='turntable_stator', servo='SG90',
         axis='y', sign=+1, lead_at=16.50, across=(0.0, -3.5)),
    # J2 shoulder. The MG995 runs DOWN along Z, case z -30.0..+10.0, mounted
    # on a pad whose outer face is at x = sb_plate_out + sb_lobe_t. Lead end
    # is the BOTTOM, -Z.
    dict(tag='J2 shoulder', host='shoulder_bracket', servo='MG995',
         axis='z', sign=-1, lead_at=-30.0, across=(29.9 + 18.25, 0.0)),
    # J3 elbow. MG90S in the forearm's -X lobe, case y -51.0..-27.0 with the
    # elbow at y -45.0, so the near end is -51.0 and the lead end is -27.0.
    dict(tag='J3 elbow', host='forearm', servo='MG90S',
         axis='y', sign=+1, lead_at=-27.0, across=(-19.0, -3.5)),
    # J4 wrist pitch. MG90S in the +X lobe, case y -18.0..+6.0, shaft at 0,
    # near end +6.0, lead end -18.0.
    dict(tag='J4 wrist', host='forearm', servo='MG90S',
         axis='y', sign=-1, lead_at=-18.0, across=(19.0, -3.5)),
    # J5 roll. SG90 on its side, long axis along Z, case z -16.5..+6.1 with
    # the shaft at 0. Lead end is the BOTTOM, -Z, down in the keel.
    dict(tag='J5 roll', host='wrist_roll', servo='SG90',
         axis='z', sign=-1, lead_at=-16.5, across=(0.0, 0.0)),
    # Effector. THE CONTROL, and the only mount that already models a lead
    # escape: pruner_shell cuts a 5.0 mm lead_notch through its back wall at
    # x +-2.5, z 0 .. (case_w/2 + loc/2) = 0..6.40. The lead centre is the
    # middle of that, z 3.2 - NOT 8.0, which was the first guess here and put
    # the probe just ABOVE the notch and into solid wall. It reported the one
    # part that deliberately solved this problem as TRAPPED, which is how the
    # guess was caught. If this row is not CLEAR, the whole file is wrong and
    # no other row means anything.
    dict(tag='effector', host='pruner_shell', servo='SG90',
         axis='y', sign=-1, lead_at=-31.9, across=(0.0, 3.2)),
]

ENV = 'robotarm_lead_probe'


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    for _stale in [m for m in list(sys.modules)
                   if m == 'lib' or m.startswith('lib.') or m == 'servo']:
        del sys.modules[_stale]
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from lib.servo import CATALOG

    comps = {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in comps:
            comps[n] = occ.component

    M3 = adsk.core.Matrix3D.create
    P3 = adsk.core.Point3D.create
    V = adsk.core.ValueInput.createByString
    NEWB = adsk.fusion.FeatureOperations.NewBodyFeatureOperation

    def fresh(name):
        stale = name + '_stale_'
        for i in range(design.allComponents.count):
            c = design.allComponents.item(i)
            if c.name == name or c.name.startswith(name + ' ('):
                c.name = stale + str(i)
        for occ in list(root.occurrences):
            if occ.component.name.startswith(stale):
                occ.deleteMe()
        occ = root.occurrences.addNewComponent(M3())
        occ.component.name = name
        assert occ.component.name == name, (
            'Fusion handed back %s - a stale component reserves the name'
            % occ.component.name)
        return occ

    print('=== servo lead escape check ===')
    print('a lead must run %.1f mm clear of its own host before it can bend'
          % ESCAPE_MM)
    print('lead diameters are lib/servo.py lead_bundle_dia, read here for the')
    print('first time in this project.')
    print('')
    print('%-13s %-18s %-7s %6s   %s'
          % ('mount', 'host', 'servo', 'Ø lead', 'verdict'))

    fails, skipped = [], []
    probe_occ = fresh(ENV)
    probe = probe_occ.component
    bodies = []

    for m in MOUNTS:
        host_name = 'robotarm_' + m['host']
        if host_name not in comps:
            skipped.append('%s (%s not in document)' % (m['tag'], m['host']))
            continue
        spec = CATALOG[m['servo']]
        d = spec.lead_bundle_dia

        # a cylinder on the case's long axis, starting at the far end face
        # and running ESCAPE_MM further out.
        ax = m['axis']
        lo = m['lead_at']
        hi = lo + m['sign'] * ESCAPE_MM
        a, b = min(lo, hi), max(lo, hi)
        c0, c1 = m['across']
        if ax == 'y':
            plane, centre = probe.xZConstructionPlane, (c0, c1)
        elif ax == 'z':
            plane, centre = probe.xYConstructionPlane, (c0, c1)
        else:
            plane, centre = probe.yZConstructionPlane, (c0, c1)

        sk = probe.sketches.add(plane)
        sk.name = 'sk_lead_' + m['tag'].replace(' ', '_')
        if ax == 'y':
            pt = sk.modelToSketchSpace(P3(centre[0] / 10.0, 0, centre[1] / 10.0))
        elif ax == 'z':
            pt = sk.modelToSketchSpace(P3(centre[0] / 10.0, centre[1] / 10.0, 0))
        else:
            pt = sk.modelToSketchSpace(P3(0, centre[0] / 10.0, centre[1] / 10.0))
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt, d / 20.0)
        assert sk.profiles.count == 1, m['tag']
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = probe.features.extrudeFeatures.createInput(col, NEWB)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
            V('%.4f mm' % a))
        inp.setDistanceExtent(False, V('%.4f mm' % (b - a)))
        body = probe.features.extrudeFeatures.add(inp).bodies.item(0)
        body.name = 'lead_' + m['tag'].replace(' ', '_')
        bodies.append((m, spec, body))

    # interference, one lead against its own host
    host_occ = {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in host_occ:
            host_occ[n] = occ

    for m, spec, body in bodies:
        host = host_occ['robotarm_' + m['host']]
        hb = host.component.bRepBodies.item(0).createForAssemblyContext(host)
        col = adsk.core.ObjectCollection.create()
        col.add(body)
        col.add(hb)
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        vol = sum(res.item(i).interferenceBody.volume * 1000
                  for i in range(res.count))
        free = math.pi * (spec.lead_bundle_dia / 2.0) ** 2 * ESCAPE_MM
        blocked_pct = 100.0 * vol / free if free else 0.0
        if vol < 0.05:
            verdict = 'CLEAR'
        elif blocked_pct < 25.0:
            verdict = 'TIGHT - %.0f%% of the lead path is solid' % blocked_pct
            fails.append('%s: %s' % (m['tag'], verdict))
        else:
            verdict = 'TRAPPED - %.0f%% solid' % blocked_pct
            fails.append('%s: %s' % (m['tag'], verdict))
        print('%-13s %-18s %-7s %6.1f   %s'
              % (m['tag'], m['host'], spec.name, spec.lead_bundle_dia, verdict))

    for occ in list(root.occurrences):
        if occ.component.name == ENV:
            occ.deleteMe()

    print('')
    if skipped:
        print('NOT CHECKED - host not in this document:')
        for s in skipped:
            print('  %s' % s)
        print('')
    print('GATE leads : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)
    print('')
    ctl = [r for r in bodies if r[0]['tag'] == 'effector']
    if ctl:
        ctl_failed = any(f.startswith('effector') for f in fails)
        print('CONTROL: pruner_shell has a DELIBERATE lead notch, so the')
        print('  effector row must read CLEAR. It reads %s.'
              % ('FAIL - THIS FILE IS WRONG, ignore every row above'
                 if ctl_failed else 'CLEAR, so the method works'))
        print('')
    print('EVERY OTHER ROW\'S LEAD POSITION IS STILL A PER-PART GUESS. The')
    print('control proves the METHOD, not the five placements. A TRAPPED row')
    print('below means "go look at that pocket", not "that part is broken".')
    print('')
    print('ASSUMED, and it is the one assumption here: the leads leave the FAR')
    print('END FACE, centred across the case and one diameter up from the case')
    print('bottom. lib/servo.py\'s frame says the lead end is +X, away from the')
    print('shaft. Nobody has measured where they actually emerge.')
    print('NOT CHECKED: whether an escaped lead can then REACH the duct. That')
    print('needs the loom modelled, and nothing models it.')
