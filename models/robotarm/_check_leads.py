"""robotarm/_check_leads - can each servo be INSTALLED, and can its lead get out?

REPAIRED 2026-08-28, after the file spent a day marked INVALID.

TWO QUESTIONS, and the file used to ask only the second one:

  INSERTION  the case is walked along its fitting path with the lead bundle
             attached, and at every step the pair is checked against the host.
             A pocket cut to case + loc passes an escape check and still
             cannot be assembled, because the cable crosses the mounting
             window on the way in and is pinched when the case seats. That is
             what stopped all three servos on the bench.
  ESCAPE     the bundle, seated, is pushed ESCAPE_MM outward. If it hits the
             host, the lead is trapped and the servo cannot be wired in place.
             Modelled square, side = bundle diameter: three wires side by
             side are a rectangle, not a circle.

WHERE THE LEAD LEAVES THE CASE. Not typed here. Read from lib/servo.py:
lead_x (the SHORT END FACE at the shaft end, = -shaft_from_end), lead_y
(0.0, centred) and lead_z. Each row below gives only a FRAME - where the
servo's shaft sits in the host, and which host axis each servo axis maps to -
and the probe position is computed from that frame and the library.

That is the whole repair. The old rows carried hand-typed lead_at / across
coordinates, and every one of them was written from a sentence in the
library's comment rather than its numbers. The sentence said the leads left
the FAR end face; the numbers said -shaft_from_end, which is the NEAR one.
Six rows, six wrong probes, one 6/6 CLEAR that meant nothing - and then five
parts notched on the strength of it. A datum that each consumer re-types in
its own coordinates is not a contract, it is six copies of a rumour.

If a row is wrong now, it is wrong in its FRAME - a rotation or an origin -
which is a claim about how the servo sits in the part, visible in a
screenshot. It can no longer be wrong about where a cable leaves a servo.

THE CONTROL. gripper_shell and pruner_shell are clamshells: the servo is
laid in and the halves close, so they have NO insertion path and only the
escape question applies. Their rows are marked clamshell=True and are the
control for the escape half - both cut a deliberate outboard lead notch, so
both must read CLEAR. If they do not, the method is wrong and no other row
means anything.

WHAT IT STILL DOES NOT CHECK. Whether an escaped lead can then REACH the
cable duct. That needs the loom modelled, and nothing models it.

Run after _check_ledger, in the same document. It builds scratch probe
bodies and deletes them; occurrence count and timeline length come back
unchanged.
"""


import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules)
               if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core
import adsk.fusion

# THE TABLE BELOW IS DERIVED NOW, NOT TYPED, AND THAT IS THE REPAIR THIS
# FILE'S OWN COMMENT ASKED FOR. See the MOUNTS header.
from lib.joints import HEX_PIVOT as _PIVOT  # noqa: E402
from lib.joints import servo_for as _servo_for  # noqa: E402
from lib.joints import servo_name_for as _servo_name_for  # noqa: E402
from lib.servo_hub import spline_hub as _spline_hub  # noqa: E402

ESCAPE_MM = 8.0     # how far a lead must run clear before it can be bent away
STEPS = 12          # insertion-path samples, seated last
JAM_MM3 = 0.5       # interference below this is meshing noise, not a jam

# One entry per servo in the arm. Each row is a FRAME, not a coordinate:
#
#   shaft    where the servo's output shaft axis meets its TAB PLANE, in host
#            mm. This is the origin of lib/servo.py's servo frame.
#   xa       which host axis (and sign) the servo's +x maps to, as
#            ('x'|'y'|'z', +1|-1). Servo +x runs along the case length AWAY
#            from the shaft end.
#   za       likewise for servo +z, which points up out of the tab plane
#            toward the horn. The third axis is COMPUTED as za x xa, so a row
#            cannot accidentally describe a left-handed servo.
#   insert   host-frame unit vector the servo TRAVELS along as it is fitted,
#            or None for a clamshell that has no insertion path.
#   travel   how far back along -insert the case starts, mm.
#
# Everything else - the lead position, the case envelope, the escape
# direction - is computed from these and lib/servo.py.
# THREE OF THESE SEVEN ROWS WERE STALE ON 2026-09-03 - J1 by 2.40, J4 by
# 0.40, J5 by 0.40 - each of them a number a part had since re-derived. This
# table is typed and the parts are computed, which is the failure CLAUDE.md
# names: a datum only one file reads is a decoration, not a contract. Every
# gate that reads MOUNTS was placing servos where they are not, and GATE
# servo_fit's 7/7 CLEAR was measured against those wrong places.
# _check_motor_clearance.py now carries a placement audit that compares each
# row against the host's own parameters. The real fix is for these to be
# DERIVED, not audited - see specs/robotarm/_decouple.md.
#
# THE SERVO COLUMN IS NOW DERIVED, AND THAT WAS THE WORST COPY OF THE THREE.
# Each row used to name its motor - `servo='MG90S'` - which is the same fact
# lib/joints.JOINT_SERVO holds and lib/gears.py, lib/arm_loads.py and six
# part scripts each held their own version of. On 2026-09-03 J3 and J4 went
# MG90S -> SG90, and a typed column here would have gone on driving a solid
# MG90S case through an SG90 pocket in every probe this file builds - and
# reported CLEAR, because an MG90S case is BIGGER in every dimension that
# matters. A stale row that errs toward "clear" is worse than one that errs
# toward "jam": it is the shape of failure that survives a gate.
#
# TWO STATIONS ARE NOW DERIVED TOO - J3's and J4's, the two the swap moves.
# They are exactly the sums the hosts build them from:
#   J4  the tab plane is the forearm's plate outer face plus fa_j4_lobe_t,
#       and fa_j4_lobe_t IS wrist_hub's spline seat height, because that is
#       what the lobe was thickened to deliver (forearm.py's j4_standoff
#       block). 25.80 -> 27.00 on the SG90, and the 25.80 itself was a
#       2026-09-03 correction of a 25.40 that was stale by 0.40.
#   J3  the cap's tab plane is its own outer face, sc_t = fa_cap_t =
#       fa_lobe_t = the servo's case-top height above its tab underside.
#       5.50 -> 6.70.
# The other five stations stay typed: they belong to hosts this pass does not
# touch, and inventing a derivation for a frame nobody has re-checked would
# be worse than leaving a number a person can compare against a screenshot.
_J4_SEAT_Z = _spline_hub(
    _servo_for('J4'),
    face=_PIVOT.journal + _PIVOT.flange_t + _PIVOT.reach).seat_z
_J4_TAB_X = _PIVOT.plate_out + _J4_SEAT_Z
_J3_SERVO = _servo_for('J3')
_J3_CAP_T = _J3_SERVO.tab_below_top + _J3_SERVO.tab_thk

MOUNTS = [
    # 12.60 -> 10.20, CORRECTED 2026-09-03. turntable_stator builds its deck
    # as `race_z - tt_hub_h - tt_hub_seat_z` = 10.20 since the J1 horn came
    # out and the bolted j1_hub went in. This row still carried the horn-era
    # 12.60, so every gate reading it has been placing the yaw servo 2.40 mm
    # too high - including GATE servo_fit, which reported J1 clear.
    dict(tag='J1 yaw', host='turntable_stator', servo=_servo_name_for('J1'),
         shaft=(0.0, 0.0, 10.20),
         xa=('y', +1), za=('z', +1),
         insert=(0.0, 0.0, -1.0), travel=30.0),
    dict(tag='J2 shoulder', host='shoulder_bracket',
         servo=_servo_name_for('J2'),
         shaft=(29.6, 0.0, 0.0),
         xa=('z', -1), za=('x', -1),
         insert=(-1.0, 0.0, 0.0), travel=45.0),
    # J3 DOES NOT MOUNT IN THE FOREARM ANY MORE, and this row went on saying
    # it did for four commits after the 2:1 landed. It read
    # shaft=(-25.4, -45.0, 0.0): the OLD tab plane, on the OLD elbow axis,
    # in a host that no longer carries the servo. The reduction moved it one
    # centre distance toward the wrist and 9.60 mm further out, onto
    # j3_servo_cap - so "leads 6/6 CLEAR" was checking thin air for this one,
    # which is the exact failure this file was rewritten to stop making.
    #
    # The frame is the CAP's: origin on the pinion axis at its INNER face,
    # +X along the arm toward the wrist, +Z out of the seating face toward
    # the servo. The tab plane is the cap's outer face, so the shaft origin
    # sits at z = sc_t. Insertion is into the cap OFF THE ARM, which is the
    # whole point of the cap existing - see _HANDOFF.md section 10.
    # sc_t is fa_cap_t is fa_lobe_t is the servo's own case-top height, so it
    # is derived from the servo rather than typed: 5.50 on the MG90S, 6.70 on
    # the SG90 that replaced it.
    #
    # za +1 -> -1, CORRECTED 2026-09-03, AND THE COMMENT ABOVE IS WHAT
    # CONVICTED IT. It says "+Z out of the seating face TOWARD THE SERVO",
    # and lib/servo.py's frame puts the servo's BODY at its own -z with the
    # boss and spline at +z. Toward the servo body is therefore the servo's
    # -z, so servo +z maps to cap -z and this column is -1. It was +1, which
    # modelled the J3 motor INSIDE OUT: case and lead pointing inboard into
    # the 10.80 standoff band where the gear and pinion run, spline pointing
    # outboard into open air. Every consumer of this row inherited it -
    # servo_fit measured the case against the cap with the case on the wrong
    # side and read 0.0, GATE leads sited the escape corridor on the wrong
    # side, and GATE motor_clearance reported the 36T gear STRIKING the lead
    # for 23.0 mm3, which is the gear passing through a cable that is not
    # there. The parts themselves were never wrong: GATE j3_mesh places the
    # pinion from the PART's own jp_seat_z and reads 0 of 420 flank points
    # buried, so the pinion is in the gear's plane and the servo that drives
    # it can only be the way round that puts it there.
    dict(tag='J3 elbow', host='j3_servo_cap', servo=_servo_name_for('J3'),
         shaft=(0.0, 0.0, _J3_CAP_T),
         xa=('x', +1), za=('z', -1),
         insert=(0.0, 0.0, -1.0), travel=30.0),
    # 25.40 -> 25.80 (CORRECTED 2026-09-03), then DERIVED and 27.00 with the
    # SG90. forearm.py's tab plane is `fa_plate_out + fa_j4_lobe_t` = 19.90 +
    # 7.10; the running gap inside that 7.10 is fa_j4_standoff, added when
    # wrist_hub moved onto the spline and stopped rubbing the servo case. A
    # 0.40 sliver falls between GATE servo_fit's 1.50 mm samples, which is why
    # the stale row read CLEAR - the 1.20 the servo swap adds would not have,
    # but nothing should be relying on an error being big enough to see.
    dict(tag='J4 wrist', host='forearm', servo=_servo_name_for('J4'),
         shaft=(_J4_TAB_X, 0.0, 0.0),
         xa=('y', -1), za=('x', -1),
         insert=(-1.0, 0.0, 0.0), travel=30.0),
    # 5.00 -> 4.60, CORRECTED 2026-09-03. wrist_roll builds wro_tab_lo at
    # 4.60; the 0.40 is wro_case_gap, added when wrist_rotator moved onto the
    # spline. Found by the agent that split this part, which was told to
    # report a stale row rather than edit a file it did not own.
    dict(tag='J5 roll', host='wrist_roll', servo=_servo_name_for('J5'),
         shaft=(0.0, 4.60, 0.0),
         xa=('z', -1), za=('y', +1),
         insert=(0.0, 1.0, 0.0), travel=30.0),
    dict(tag='gripper', host='gripper_shell', servo=_servo_name_for('J6'),
         shaft=(0.0, -14.90, 0.0),
         xa=('x', +1), za=('y', +1),
         insert=None, travel=0.0, clamshell=True),
    dict(tag='effector', host='pruner_shell', servo=_servo_name_for('J6'),
         shaft=(0.0, -14.90, 0.0),
         xa=('x', +1), za=('y', +1),
         insert=None, travel=0.0, clamshell=True),
]

ENV = 'robotarm_lead_probe'

AXES = {'x': 0, 'y': 1, 'z': 2}


def _unit(spec):
    v = [0.0, 0.0, 0.0]
    v[AXES[spec[0]]] = float(spec[1])
    return v


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _frame(m):
    """Servo axes as host unit vectors. +y is COMPUTED (za x xa), so a row
    cannot describe a left-handed servo however it is typed."""
    ex = _unit(m['xa'])
    ez = _unit(m['za'])
    ey = _cross(ez, ex)
    assert abs(sum(a * b for a, b in zip(ex, ez))) < 1e-9, (
        '%s: xa and za are the same host axis' % m['tag'])
    return ex, ey, ez


def _to_host(m, p):
    ex, ey, ez = _frame(m)
    s = m['shaft']
    return [s[i] + p[0] * ex[i] + p[1] * ey[i] + p[2] * ez[i] for i in range(3)]


def _aabb(m, lo, hi):
    """Host-frame AABB of a servo-frame box. The frame is a signed
    permutation, so the mapped box is still axis-aligned - no hull needed."""
    pts = []
    for cx in (lo[0], hi[0]):
        for cy in (lo[1], hi[1]):
            for cz in (lo[2], hi[2]):
                pts.append(_to_host(m, (cx, cy, cz)))
    return ([min(p[i] for p in pts) for i in range(3)],
            [max(p[i] for p in pts) for i in range(3)])


def _sweep(box, insert, travel):
    """Extend an AABB backwards along the insertion path. Every insert vector
    in MOUNTS is axis-aligned, so the swept volume of the box IS a box - the
    check is exact, not sampled."""
    lo, hi = [list(b) for b in box]
    if insert is None or travel <= 0:
        return lo, hi
    for i in range(3):
        d = -insert[i] * travel
        if d < 0:
            lo[i] += d
        else:
            hi[i] += d
    return lo, hi


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

    comps, host_occ = {}, {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in comps:
            comps[n] = occ.component
            host_occ[n] = occ

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

    probe_occ = fresh(ENV)
    probe = probe_occ.component
    ext = probe.features.extrudeFeatures

    def mmv(x):
        return V('%.5f mm' % x)

    def box(name, lo, hi):
        sk = probe.sketches.add(probe.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            sk.modelToSketchSpace(P3(lo[0] / 10.0, lo[1] / 10.0, 0)),
            sk.modelToSketchSpace(P3(hi[0] / 10.0, hi[1] / 10.0, 0)))
        assert sk.profiles.count == 1, name
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = ext.createInput(col, NEWB)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(mmv(lo[2]))
        inp.setDistanceExtent(False, mmv(hi[2] - lo[2]))
        b = ext.add(inp).bodies.item(0)
        b.name = name
        return b

    found = []

    def hits(body, host_name, label=''):
        occ = host_occ[host_name]
        col = adsk.core.ObjectCollection.create()
        col.add(body)
        for i in range(occ.component.bRepBodies.count):
            col.add(occ.component.bRepBodies.item(i).createForAssemblyContext(occ))
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        vol, blobs = 0.0, []
        for i in range(res.count):
            b = res.item(i).interferenceBody
            bb = b.boundingBox
            vol += b.volume * 1000
            blobs.append('%.2f mm3 at X %.2f..%.2f Y %.2f..%.2f Z %.2f..%.2f'
                         % (b.volume * 1000,
                            bb.minPoint.x * 10, bb.maxPoint.x * 10,
                            bb.minPoint.y * 10, bb.maxPoint.y * 10,
                            bb.minPoint.z * 10, bb.maxPoint.z * 10))
        found.extend('    %s: %s' % (label, t) for t in blobs)
        return vol

    print('=== servo INSERTION + lead ESCAPE ===')
    print('probe positions are computed from lib/servo.py lead_x/lead_y/lead_z')
    print('and each row\'s frame. Nothing about the lead is typed in this file.')
    print('WHICH servo each row drives is lib/joints.JOINT_SERVO, not this '
          'table: %s' % ', '.join('%s %s' % (m['tag'], m['servo'])
                                  for m in MOUNTS))
    print('')
    print('%-12s %-19s %-6s %9s %9s %9s  %s'
          % ('mount', 'host', 'servo', 'seated', 'insert', 'escape', 'verdict'))

    fails, skipped, rows = [], [], []
    for m in MOUNTS:
        host = 'robotarm_' + m['host']
        if host not in comps:
            skipped.append('%s (%s not in document)' % (m['tag'], m['host']))
            continue
        sp = CATALOG[m['servo']]
        d = sp.lead_bundle_dia
        tab_top = sp.tab_thk + sp.tab_below_top

        case = _aabb(m,
                     (-sp.shaft_from_end, -sp.case_w / 2, tab_top - sp.case_h),
                     (sp.case_l - sp.shaft_from_end, sp.case_w / 2, tab_top))
        # the bundle, as a square stub running OUTWARD from the end face
        lead = _aabb(m,
                     (sp.lead_x - d, sp.lead_y - d / 2, sp.lead_z - d / 2),
                     (sp.lead_x, sp.lead_y + d / 2, sp.lead_z + d / 2))

        b_seat = box('seat_' + m['tag'].replace(' ', '_'), case[0], case[1])
        seated = hits(b_seat, host, m['tag'] + ' seated case')

        ins = None
        if m['insert'] is not None:
            c_lo, c_hi = _sweep(case, m['insert'], m['travel'])
            l_lo, l_hi = _sweep(lead, m['insert'], m['travel'])
            tag = m['tag'].replace(' ', '_')
            ins = (hits(box('swc_' + tag, c_lo, c_hi), host,
                        m['tag'] + ' swept case')
                   + hits(box('swl_' + tag, l_lo, l_hi), host,
                          m['tag'] + ' swept lead'))

        # the escape run: the same stub, extended ESCAPE_MM outward. SQUARE
        # section, side = bundle diameter. Three wires lying side by side are
        # closer to a rectangle than to a circle, so this is honest rather
        # than merely conservative - and it reuses box(), the primitive every
        # seated check proves at 0.00. The cylinder that used to be here
        # stacked its start offset onto its sketch plane and sited every
        # probe lead_x too far out; it called two correct parts TIGHT.
        esc_box = _aabb(m,
                        (sp.lead_x - ESCAPE_MM, sp.lead_y - d / 2, sp.lead_z - d / 2),
                        (sp.lead_x, sp.lead_y + d / 2, sp.lead_z + d / 2))
        p0 = _to_host(m, (sp.lead_x, sp.lead_y, sp.lead_z))
        esc = hits(box('esc_' + m['tag'].replace(' ', '_'),
                       esc_box[0], esc_box[1]), host, m['tag'] + ' escape')
        print('  lead point (%.2f, %.2f, %.2f), escape run X %.2f..%.2f '
              'Y %.2f..%.2f Z %.2f..%.2f'
              % tuple(list(p0) + [esc_box[0][0], esc_box[1][0],
                                  esc_box[0][1], esc_box[1][1],
                                  esc_box[0][2], esc_box[1][2]]))
        free = d * d * ESCAPE_MM

        if seated > 1.0:
            verdict = 'FRAME WRONG - the case alone overlaps %.1f mm3' % seated
            fails.append('%s: %s' % (m['tag'], verdict))
        elif ins is not None and ins > JAM_MM3:
            verdict = 'JAMS ON INSERTION - %.1f mm3 in the path' % ins
            fails.append('%s: %s' % (m['tag'], verdict))
        elif esc > 0.05:
            pct = 100.0 * esc / free
            verdict = ('TRAPPED - %.0f%% solid' % pct if pct >= 25
                       else 'TIGHT - %.0f%% of the escape is solid' % pct)
            fails.append('%s: %s' % (m['tag'], verdict))
        else:
            verdict = 'CLEAR'
        rows.append((m, verdict))
        print('%-12s %-19s %-6s %9.2f %9s %9.2f  %s'
              % (m['tag'], m['host'], sp.name, seated,
                 'clamshell' if ins is None else '%.2f' % ins, esc, verdict))

    for occ in list(root.occurrences):
        if occ.component.name == ENV:
            occ.deleteMe()

    print('')
    if found:
        print('WHERE, for every overlap found - a gate that only reports a')
        print('volume sends you hunting through the part for it:')
        for line in found:
            print(line)
        print('')
    if skipped:
        print('NOT CHECKED - host not in this document:')
        for s2 in skipped:
            print('  %s' % s2)
        print('')
    ctl = [(m, v) for m, v in rows if m.get('clamshell')]
    if ctl:
        bad = [m['tag'] for m, v in ctl if v != 'CLEAR']
        print('CONTROL: the two clamshells cut a deliberate outboard lead')
        print('  notch and have no insertion path, so both must read CLEAR.')
        print('  %s' % ('they do, so the escape method works' if not bad
                        else 'FAIL (%s) - THIS FILE IS WRONG, ignore every row'
                             % ', '.join(bad)))
        print('')
    print('SEATED is the frame self-check: every pocket is cut to case + loc,')
    print('so the case alone must overlap ~0. A large number means the ROW is')
    print('wrong - a rotation or an origin - not that the part is.')
    print('')
    # A GATE THAT CHECKED NOTHING IS NOT A PASS. Run into an empty document
    # this file skips all seven rows, prints them under "NOT CHECKED", and
    # then printed "GATE leads : PASS" underneath - which is the one output a
    # gate must never produce. It happened on 2026-09-03, in a run that was
    # meant to confirm the SG90 swap, and the log read green. Every row
    # skipped is a question that was not asked, so it fails here.
    assert rows, (
        'GATE leads CHECKED NOTHING - all %d hosts are absent from this '
        'document. Build the hosts first (see _check_servo_fit, which builds '
        'its own); a run with no rows is not a pass.' % len(skipped))
    if skipped:
        fails.append('%d of %d rows NOT CHECKED - their hosts are not in this '
                     'document, so this run says nothing about them'
                     % (len(skipped), len(skipped) + len(rows)))
    print('GATE leads : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)
    print('')
    print('NOT CHECKED: whether an escaped lead can then REACH the duct. That')
    print('needs the loom modelled, and nothing models it.')
