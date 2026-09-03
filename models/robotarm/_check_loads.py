"""robotarm/_check_loads - the load gate _assembly.md has promised since it was
written.

Reads every part's REAL volume and centre of mass out of Fusion, turns them
into joint moments and section stresses through `lib/arm_loads.py`, and says
whether anything is over its limit.

WHY IT FINALLY EXISTS. Two reasons, and the second one is a debt this session
created rather than inherited:

1. `_assembly.md`'s load table is ESTIMATED masses, and its own text says so:
   "models/robotarm/_check_loads.py replaces them with real Fusion volumes and
   centres of mass before any piece exports". It has said that since the spec
   was written. `lib/arm_budget.py` stood in, honestly, but its cluster masses
   are that same estimated table and its link masses are back-calculated from
   two volumes.
2. On 2026-08-26 the base plate was relieved to MIN_WALL under each roller to
   let the 608s fit at all. The judgement at the time was "1.6 clears a
   wall-thickness rule" - which is a manufacturing rule, not a strength one.
   Nothing checked what that band actually carries. Section D does.

WHAT IT DOES NOT DO, said plainly so nobody trusts it further than it goes:

- **No FEA.** knowledge/loads_strength.md's method: worst-case moment, real
  section read off the model, sigma = M.c/I against 35 MPa in-plane, halved
  across layers, divided by a safety factor. Beam arithmetic on a part that is
  not a beam is approximate, and where it comes out marginal the answer is a
  physical test, not a finer model.
- **No dynamics.** Every number here is a static hold in the worst pose. A
  servo slewing the arm and stopping it sees more than this.
- **The cluster offsets are still assumed rigid.** Masses are now measured;
  where each mass SITS is still the geometric model arm_budget uses. Change
  the head and these offsets move and nothing here notices.

RUN ORDER. Needs every part in the document, so it runs after _check_ledger:

    mod.BATCH = 0,1,2,3   on _check_ledger, THEN
    _check_loads.run()    in the same document

It runs no part script, builds no geometry and touches no parameter. It does
place three occurrences to compose the wrist chain (section B0) and deletes
them again, which is the only mark it makes on the timeline.
"""

import json
import math
import os
import sys

import adsk.core
import adsk.fusion

REPO_FOR_IMPORT = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO_FOR_IMPORT not in sys.path:
    sys.path.insert(0, REPO_FOR_IMPORT)

from lib.joints import servo_name_for  # noqa: E402
from lib.servo import CATALOG  # noqa: E402

# Set inside run() from lib.gears.J3_PAIR, once lib is importable.
J3_OFFSET_MM = None

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
OUT = os.path.join(REPO, 'specs', 'robotarm', '_mass_properties.json')

# Bought parts carry no printed-density correction and no volume in Fusion,
# because none of them is modelled. lib/servo.py is the source for the servos.
#
# THE SERVO ROWS ARE DERIVED, NAME AND MASS BOTH. They were typed - 'MG90S
# J3': 13.4 and 'MG90S J4': 13.4 - and stayed typed through the 2026-09-03
# swap to SG90s, which is 9.0 g. This model was carrying 4.4 g of servo that
# is not on the arm at each of J3 and J4, 8.8 g in total, and every duty
# percentage downstream of it was quietly generous. That is the failure
# CLAUDE.md names: a servo mapping copied out of lib/joints instead of read
# from it. J3's copy is worse than J4's, because it hangs on the far end of
# a 125 mm upper arm.
def _srv(joint, where):
    """('<SERVO> <where>', mass_g) for the servo lib/joints gives that joint."""
    name = servo_name_for(joint)
    return '%s %s' % (name, where), CATALOG[name].mass_g


J3_SERVO, _J3_SERVO_G = _srv('J3', 'J3')
J4_SERVO, _J4_SERVO_G = _srv('J4', 'J4')
J5_SERVO, _J5_SERVO_G = _srv('J5', 'J5')
J6_SERVO, _J6_SERVO_G = _srv('J6', 'effector')
J1_SERVO, _J1_SERVO_G = _srv('J1', 'J1 yaw')
J2_SERVO, _J2_SERVO_G = _srv('J2', 'J2')

BOUGHT_G = {
    J2_SERVO: _J2_SERVO_G,
    J3_SERVO: _J3_SERVO_G,
    J4_SERVO: _J4_SERVO_G,
    J5_SERVO: _J5_SERVO_G,
    J6_SERVO: _J6_SERVO_G,
    J1_SERVO: _J1_SERVO_G,
    '608ZZ x3': 3 * 32.0,
}

# Where each mass sits, as a radius from the joint being summed about, in mm.
#
# THE PRINTED PARTS ARE NO LONGER IN THIS TABLE. Their offsets are COMPOSED -
# the wrist chain is assembled at the worst pose and each part's COM is read
# in the ASSEMBLY's frame, so the number is the real distance from J4 and not
# a figure anyone typed. lib/arm_budget.py still carries them as constants;
# section B prints both and says when they drift.
#
# What is left here is the BOUGHT parts, which appear in no model file and so
# have no COM to read. These stay declared, and stay flagged BOUGHT.
BOUGHT_OFFSET_MM = {
    J4_SERVO: -6.0,
    J5_SERVO: 0.0,
    J6_SERVO: 32.0,
}
HUB_SPIN_DEG = 90.0          # matches _check_wrist - every socket in this arm
                             # has a hex vertex on the assembly's +Y
# BOTH OF THESE ARE TYPED, and this file's own closing note says nothing
# here notices when the head changes. It did not: the 2026-08-29 head diet
# shortened the shell 9.0 mm and these two constants held the old head in
# place, hiding most of the benefit for one whole gate run.
#
# What actually moved, and by how much - the head is NOT rigid-shifted by
# the 9.0 mm, because its tail (the SG90 bay, half its mass) did not move:
#
#   HEAD_OFFSET   mass-weighted from the rebuilt COMs. With tail_r reverted
#                 the only surviving change is ps_cheek_front's pad, 6.0 ->
#                 3.5: that removes 2 x 0.26 g of cheek nose about 3 mm
#                 ahead of the head COM, which moves it under 0.1 mm - below
#                 what a typed constant resolves. So 47.0 stands, and it
#                 stands because it was CHECKED, not because nobody looked.
#   PAYLOAD       the stem sits in the jaw, and the jaw is the crossing
#                 point, which rides on CHOSEN.pivot_y. pivot_y is back at
#                 42.0, so this is back at 68.0.
#
# The shortening that made this note necessary is documented in
# lib/pruner_linkage.py, along with why it was reverted.
HEAD_OFFSET_MM = 47.0        # pruner head centre of mass, past the wrist end
PAYLOAD_G = 25.0             # rated payload, _assembly.md
PAYLOAD_OFFSET_MM = 68.0     # asm_l3 - wrist axis to the jaw faces

# HOW MANY OF EACH. The head is a CLAMSHELL: _check_pruner places
# pruner_shell twice (M3() and `turned`) and so does _preview_arm. This file
# counted it ONCE, in two places, and nothing asserted the two views agreed.
# 11.44 g - a third of the head - sat at 9.2 cm from the elbow and was simply
# absent from the budget, which is about ten points of J3 duty. Found
# 2026-08-28 while pricing a longer arm; it made the arm look affordable.
#
# Counts live here, once, and both the head and the turret read them.
COUNT = {'pruner_shell': 2, 'pruner_blade': 2, 'pruner_rack': 2,
         'gripper_pinion': 1, 'wrist_hub': 2}

# The J1 turret: what rotates, and how far the arm reaches over the rollers.
ROTATING = ('shoulder_bracket', 'shoulder_hub', 'upper_arm', 'forearm',
            'wrist_hub', 'wrist_roll', 'wrist_rotator', 'pruner_shell',
            'pruner_blade', 'pruner_rack', 'gripper_pinion',
            'j3_gear', 'j3_pinion', 'j3_axle', 'j3_servo_cap')
ROTATING_BOUGHT = (J2_SERVO, J3_SERVO, J4_SERVO, J5_SERVO, J6_SERVO)


def compose_wrist(design, root, gv):
    """Assemble the wrist chain at pitch 0 / roll 0 and return each printed
    part's COM as a distance from J4, in mm.

    Placements are lifted from _check_wrist so the two files cannot disagree
    about how this arm goes together. It PLACES OCCURRENCES AND DELETES THEM -
    the only mutation this gate makes, and the timeline is left as it was
    found.
    """
    M3 = adsk.core.Matrix3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)
    plate_in = gv('fa_plate_in') / 10.0        # placements work in Fusion cm
    y_front = gv('wro_y_front') / 10.0

    def rot_m(angle, axis):
        m = M3()
        m.setToRotation(angle, axis, ORG)
        return m

    def place_hub(sx):
        m = rot_m(math.radians(HUB_SPIN_DEG), VEC(0, 0, 1))
        m.transformBy(rot_m(-sx * math.pi / 2, VEC(0, 1, 0)))
        t = m.translation
        t.x = sx * plate_in
        m.translation = t
        return m

    def place_rotator():
        m = rot_m(-math.pi / 2, VEC(1, 0, 0))
        t = m.translation
        t.y = y_front
        m.translation = t
        return m

    comps = {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in comps:
            comps[n] = occ.component
    want = ('wrist_hub', 'wrist_roll', 'wrist_rotator')
    for w in want:
        assert 'robotarm_' + w in comps, (
            '%s is not in this document - run _check_ledger first' % w)

    add = root.occurrences.addExistingComponent
    placed = {
        'wrist_hub': add(comps['robotarm_wrist_hub'], place_hub(+1)),
        'wrist_roll': add(comps['robotarm_wrist_roll'], M3()),
        'wrist_rotator': add(comps['robotarm_wrist_rotator'], place_rotator()),
    }
    out = {}
    for tag, occ in placed.items():
        body = occ.component.bRepBodies.item(0).createForAssemblyContext(occ)
        bb = body.boundingBox
        assert bb.maxPoint.x - bb.minPoint.x > 1e-6, (
            'degenerate body composing %s - the timeline marker is not at the '
            'end, or the occurrence is hidden' % tag)
        out[tag] = body.physicalProperties.centerOfMass.y * 10.0
    for occ in placed.values():
        occ.deleteMe()
    return out


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters

    for _stale in [m for m in list(sys.modules)
                   if m == 'lib' or m.startswith('lib.') or m == 'arm_loads']:
        del sys.modules[_stale]
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from lib import arm_loads as al
    from lib.gears import J3_PAIR
    # The J3 servo's offset from the elbow IS the pair's centre distance -
    # imported, not typed, so it cannot drift from the teeth it is cut with.
    global J3_OFFSET_MM
    J3_OFFSET_MM = J3_PAIR.centre_distance
    from lib import arm_budget as ab
    ab_fa_frac = ab.FOREARM_COM_FRAC
    ab_ua_frac = ab.UPPERARM_COM_FRAC

    def gv(name):
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        return p.value * 10.0                      # MILLIMETRES, converted once

    # ---- A: harvest what is actually on disk --------------------------------
    props = {}
    for occ in root.occurrences:
        name = occ.component.name
        if not name.startswith('robotarm_'):
            continue
        short = name[len('robotarm_'):]
        if short in props or occ.component.bRepBodies.count == 0:
            continue
        body = occ.component.bRepBodies.item(0)
        pp = body.physicalProperties
        com = pp.centerOfMass
        bb = body.boundingBox
        props[short] = {
            'volume_mm3': body.volume * 1000.0,
            'printed_g': al.printed_g(body.volume * 1000.0),
            'com_mm': [com.x * 10.0, com.y * 10.0, com.z * 10.0],
            'bbox_mm': [bb.minPoint.x * 10.0, bb.maxPoint.x * 10.0,
                        bb.minPoint.y * 10.0, bb.maxPoint.y * 10.0,
                        bb.minPoint.z * 10.0, bb.maxPoint.z * 10.0],
        }
    assert props, 'no robotarm_ parts in this document - run _check_ledger first'

    print('=== A. mass properties, measured off the built bodies ===')
    print('%-20s %10s %9s   %s' % ('part', 'mm3', 'printed g', 'COM x,y,z mm'))
    total_printed = 0.0
    for k in sorted(props):
        v = props[k]
        total_printed += v['printed_g']
        print('%-20s %10.0f %9.2f   %7.1f %7.1f %7.1f'
              % (k, v['volume_mm3'], v['printed_g'],
                 v['com_mm'][0], v['com_mm'][1], v['com_mm'][2]))
    print('%-20s %10s %9.2f   (%d parts)' % ('TOTAL PRINTED', '', total_printed,
                                             len(props)))
    print('  at PETG %.2f g/cm3 x %.2f infill. _assembly.md\'s table used'
          % (al.PETG_FILAMENT_DENSITY, al.REAL_INFILL))
    print('  Fusion PET %.3f x %.2f and is 12%% HIGH on every printed part.'
          % (al.FUSION_PET_DENSITY, 0.60))
    print('')

    fh = open(OUT, 'w')
    json.dump({k: props[k] for k in sorted(props)}, fh, indent=1, sort_keys=True)
    fh.close()
    print('wrote %s' % OUT)
    print('')

    def mass(part):
        assert part in props, (
            '%s is not in this document - the load table would silently omit '
            'it. Run _check_ledger BATCH 0..3 first.' % part)
        return props[part]['printed_g']

    # ---- B: the joint moment budget -----------------------------------------
    l1_mm = gv('ua_l1')
    l2_mm = gv('fa_l2')
    head_g = sum(COUNT.get(p, 1) * mass(p) for p in
                 ('pruner_shell', 'pruner_blade', 'pruner_rack',
                  'gripper_pinion'))

    # ---- the link centres of mass, DERIVED from what was just harvested ----
    # Both links are authored with one joint on the origin and the other at
    # -length in Y, so the COM Fusion reports converts straight into a
    # fraction with no pose composition and nothing to get backwards:
    #   forearm   origin on J4, J3 at y = -fa_l2
    #   upper_arm origin on J3, J2 at y = -ua_l1
    # arm_budget carries these as constants - 0.437 from _assembly.md's table
    # and 0.50 marked ESTIMATE. They are measured now, and the two are
    # cross-checked below rather than left to drift apart silently.
    fa_com_y = props['forearm']['com_mm'][1]
    ua_com_y = props['upper_arm']['com_mm'][1]
    fa_frac = (fa_com_y + l2_mm) / l2_mm
    ua_frac = (ua_com_y + l1_mm) / l1_mm
    assert 0.0 < fa_frac < 1.0, (
        'the forearm COM at y %.2f is outside its own length - the frame '
        'assumption above is wrong' % fa_com_y)
    assert 0.0 < ua_frac < 1.0, (
        'the upper arm COM at y %.2f is outside its own length' % ua_com_y)
    fa_com_mm = fa_frac * l2_mm
    ua_com_mm = ua_frac * l1_mm

    # ---- compose the wrist chain and read the COMs where they really sit ---
    # Placements are _check_wrist's, at the worst pose (pitch 0, roll 0): the
    # arm straight out. Reading createForAssemblyContext gives the COM in the
    # ROOT frame, so the radius from J4 is just its Y - no hand-derived
    # rotation to get backwards, which is how the hub placement went wrong in
    # _check_wrist and cost 81 mm3 at every pitch.
    composed = compose_wrist(design, root, gv)
    print('=== B0. wrist cluster offsets, COMPOSED not declared ===')
    print('%-16s %10s %10s   %s' % ('part', 'composed', 'arm_budget', ''))
    ab_cluster = dict((n.split(' ')[0], off) for n, _m, off, _b in ab.CLUSTER)
    for tag in sorted(composed):
        was = ab_cluster.get(tag)
        note = ''
        if was is not None:
            note = ('agrees' if abs(composed[tag] - was) < 0.05
                    else 'DRIFT %+.2f mm' % (composed[tag] - was))
        print('%-16s %10.2f %10s   %s'
              % (tag, composed[tag],
                 '%.2f' % was if was is not None else '-', note))
    print('')

    I = al.Item
    cluster = [
        I('wrist_hub x2', 2 * mass('wrist_hub'), composed['wrist_hub'],
          'MEASURED'),
        I('wrist_roll', mass('wrist_roll'), composed['wrist_roll'],
          'MEASURED'),
        I('wrist_rotator', mass('wrist_rotator'), composed['wrist_rotator'],
          'MEASURED'),
        I(J4_SERVO, BOUGHT_G[J4_SERVO], BOUGHT_OFFSET_MM[J4_SERVO],
          'BOUGHT'),
        I(J5_SERVO, BOUGHT_G[J5_SERVO], BOUGHT_OFFSET_MM[J5_SERVO],
          'BOUGHT'),
        I(J6_SERVO, BOUGHT_G[J6_SERVO],
          BOUGHT_OFFSET_MM['SG90 effector'], 'BOUGHT'),
        I('pruner head', head_g, HEAD_OFFSET_MM, 'MEASURED'),
    ]

    def shifted(items, extra_mm):
        return [I(i.name, i.mass_g, i.radius_mm + extra_mm, i.source)
                for i in items]

    # J4: wrist axis at the origin. Only what hangs past the wrist.
    j4_items = [i for i in cluster if i.radius_mm >= 0.0]
    j4_items = [I(i.name, i.mass_g, i.radius_mm, i.source) for i in j4_items]
    j4_items.append(I('payload', PAYLOAD_G, PAYLOAD_OFFSET_MM, 'PAYLOAD'))

    # J3: elbow at the origin. The whole cluster moves out by L2, plus the
    # forearm's own mass at its measured centre of mass along the link.
    j3_items = shifted(cluster, l2_mm)
    j3_items.append(I('forearm link', mass('forearm'), fa_com_mm, 'MEASURED'))

    # THE ELBOW DRIVE ITSELF, AND IT WAS NOT HERE. The 2:1 moved the J3 servo
    # one centre distance TOWARD THE WRIST, so it now loads the joint it
    # drives - and this file still listed it only against J2, sitting on the
    # elbow axis, contributing nothing to J3 at all. Same for the three new
    # printed parts: the gear and the axle sit ON the axis and cost J3
    # nothing, but they are 13.75 g that J2 carries at the full L1 and
    # nothing was counting them either.
    #
    # The offset is imported, not typed. It is the same centre distance the
    # teeth are cut from.
    j3_items.append(I(J3_SERVO, BOUGHT_G[J3_SERVO], J3_OFFSET_MM, 'BOUGHT'))
    j3_items.append(I('j3_servo_cap', mass('j3_servo_cap'), J3_OFFSET_MM,
                      'MEASURED'))
    j3_items.append(I('j3_pinion', mass('j3_pinion'), J3_OFFSET_MM, 'MEASURED'))
    j3_items.append(I('j3_gear', mass('j3_gear'), 0.0, 'MEASURED'))
    j3_items.append(I('j3_axle', mass('j3_axle'), 0.0, 'MEASURED'))
    j3_items.append(I('payload', PAYLOAD_G, l2_mm + PAYLOAD_OFFSET_MM,
                      'PAYLOAD'))

    # J2: shoulder at the origin. Everything above moves out by L1 again -
    # INCLUDING the J3 servo now, which is why it is no longer added here.
    j2_items = shifted(j3_items, l1_mm)
    j2_items.append(I('upper arm link', mass('upper_arm'), ua_com_mm,
                      'MEASURED'))

    print('=== B. joint moments, worst pose: arm straight out, payload gripped')
    print('L1 %.1f  L2 %.1f  head %.1f g (measured)  payload %.1f g'
          % (l1_mm, l2_mm, head_g, PAYLOAD_G))
    print('link centres of mass, DERIVED from the harvested COM:')
    for tag, frac, assumed, com_mm in (
            ('forearm', fa_frac, ab_fa_frac, fa_com_mm),
            ('upper_arm', ua_frac, ab_ua_frac, ua_com_mm)):
        drift = frac - assumed
        note = 'agrees' if abs(drift) < 0.005 else 'DRIFT %+.3f' % drift
        print('  %-10s %.4f of its length (%.2f mm)  arm_budget says %.3f - %s'
              % (tag, frac, com_mm, assumed, note))
    print('')
    print('%-7s %11s %11s %9s %9s  %-28s %s'
          % ('joint', 'required', 'duty', 'of duty', 'margin', 'drive', ''))
    duty_fail = []
    geared = []
    for joint, items in (('J2', j2_items), ('J3', j3_items), ('J4', j4_items)):
        r = al.duty_report(joint, items)
        flag = 'OVER DUTY' if r['over'] else ''
        if r['ratio'] == 1.0:
            drive = 'direct'
        else:
            drive = ('%.1f:1 x %.0f%% eff, %.0f deg travel'
                     % (r['ratio'], r['efficiency'] * 100, r['travel_deg']))
            geared.append((joint, r))
        # DUTY IS NOW THE DUTY AT THE JOINT, not at the servo. Those differ
        # by the reduction, and reporting the servo's figure against a joint
        # moment is how this model would have kept calling the elbow 87 %.
        print('%-7s %8.2f kgcm %8.2f kgcm %8.0f%% %9.2f  %-28s %s'
              % (joint, r['required_kgcm'], r['duty_kgcm'],
                 r['fraction'] * 100, r['margin'], drive, flag))
    for joint, r in geared:
        print('   %s runs through a %s.' % (joint, r['reduction']))
        print('   servo holds %.2f kg.cm; at the joint that is %.2f kg.cm, '
              'and the joint swings %.0f deg not 180.'
              % (r['servo_duty_kgcm'], r['duty_kgcm'], r['travel_deg']))
        print('   mesh efficiency %.0f%% is ASSUMED (lib/arm_loads.py '
              'MESH_EFFICIENCY) - not measured on the bench.'
              % (r['efficiency'] * 100))
        if r['over']:
            duty_fail.append('%s at %.0f%% of duty' % (joint,
                                                       r['fraction'] * 100))
    # ---- what payload the arm would actually carry -------------------------
    # The rated payload was a NUMBER IN _assembly.md and nothing computed it.
    # It is not free either: it is whatever the first joint to reach its duty
    # limit allows, and which joint that is moves when a reduction lands. The
    # handoff estimated "25 g -> roughly 60 g" for the geared elbow; estimates
    # are what this file exists to replace.
    ceiling = []
    for joint, items in (('J2', j2_items), ('J3', j3_items), ('J4', j4_items)):
        r = al.duty_report(joint, items)
        pay = [i for i in items if i.source == 'PAYLOAD']
        if not pay:
            continue
        radius_cm = pay[0].radius_mm / 10.0
        headroom_gcm = r['duty_kgcm'] * 1000.0 - r['required_gcm']
        ceiling.append((joint, PAYLOAD_G + headroom_gcm / radius_cm))
    if ceiling:
        binder, cap = min(ceiling, key=lambda t: t[1])
        print('')
        print('RATED PAYLOAD: %.0f g at the jaws, and %s is what binds it.'
              % (cap, binder))
        print('   per joint: %s'
              % ',  '.join('%s %.0f g' % c for c in sorted(ceiling)))
        print('   PAYLOAD_G is currently %.0f g. The figure above is the ceiling'
              % PAYLOAD_G)
        print('   the geometry allows, not a recommendation - it is static, and')
        print('   it spends the binding joint to 100% of its duty limit.')

    # ---- J1 yaw: the assertion nobody had computed --------------------------
    # _assembly.md has rated J1 "inertia + friction only" since it was
    # written. True - gravity makes no moment about a vertical axis - but it
    # is not a number, and "should J1 be geared?" cannot be answered without
    # one, because a reduction there costs yaw travel 1:1.
    print('')
    print('=== B2. J1 yaw, arm straight out (the worst pose for inertia) ===')
    for sweep, secs in ((90.0, 1.0), (90.0, 0.5), (180.0, 1.0)):
        y = al.yaw_slew_report(j2_items, sweep_deg=sweep, seconds=secs)
        print('  %5.0f deg in %.1f s: alpha %6.2f rad/s2 -> inertia %.3f + '
              'friction %.3f = %.3f kg.cm, %3.0f%% of the %.2f duty'
              % (sweep, secs, y['alpha_rad_s2'], y['inertia_kgcm'],
                 y['friction_kgcm'], y['total_kgcm'], y['fraction'] * 100,
                 y['duty_kgcm']))
    _y = al.yaw_slew_report(j2_items)
    print('  rotating I = %.0f g.mm2 about the yaw axis, %.1f g of it'
          % (_y['inertia_gmm2'], _y['mass_g']))
    print('  friction is %.1f%% of the total - the rollers are not the problem'
          % (100.0 * _y['friction_kgcm'] / _y['total_kgcm']))
    print('  ASSUMED: triangular slew, bearing mu %.4f, %.2f N.mm of shield drag'
          % (al.BEARING_ROLLING_MU, al.SHIELD_DRAG_NMM_EACH))
    print('  NOT modelled: cutting reaction at the jaws, or any side load.')

    print('')
    print('J3 detail - the elbow sets the payload, so show its work:')
    for i in sorted(j3_items, key=lambda x: -x.moment_gcm):
        print('  %-18s %7.2f g x %6.2f cm = %8.1f g.cm   %s'
              % (i.name, i.mass_g, i.radius_mm / 10.0, i.moment_gcm, i.source))
    print('')

    # ---- C: the sections that carry it --------------------------------------
    print('=== C. section stress at the loaded roots ===')
    print('sigma = M.c/I against %.0f MPa in-plane, x%.1f across layers, '
          'safety %.1f' % (al.PETG_SIGMA_MPA, al.Z_TENSILE_FACTOR,
                           al.SAFETY_STATIC))
    j2_nmm = al.to_newtons(al.joint_moment(j2_items) * 10.0 / 1.0) / 1.0
    # moment in g.cm -> g.mm -> N.mm
    j2_moment_nmm = al.to_newtons(al.joint_moment(j2_items) * 10.0)
    j3_moment_nmm = al.to_newtons(al.joint_moment(j3_items) * 10.0)

    plate_t = gv('sb_plate_t') if ups.itemByName('sb_plate_t') else 7.5
    col_y = gv('sb_col_y') if ups.itemByName('sb_col_y') else 13.8
    stress = []
    stress.append(al.stress_check(
        'shoulder_bracket legs (2 plates)', j2_moment_nmm,
        2 * al.rect_section_modulus_mm3(plate_t, 2 * col_y),
        across_layers=False))
    stress.append(al.stress_check(
        'forearm box beam at J3', j3_moment_nmm,
        al.rect_section_modulus_mm3(2 * 3.5, 26.0), across_layers=False))
    for s in stress:
        print('  %-34s %6.2f MPa / %5.2f allow = %4.0f%%  %s'
              % (s['name'], s['sigma_mpa'], s['allowable_with_safety_mpa'],
                 s['utilisation'] * 100, 'OVER' if s['over'] else ''))
    print('')

    # ---- D: J1, and the relief this session cut -----------------------------
    print('=== D. J1 turret - the roller path, and the 2026-08-26 relief ===')
    rot_g = sum(COUNT.get(p, 1) * mass(p) for p in ROTATING if p in props)
    rot_g += sum(BOUGHT_G[b] for b in ROTATING_BOUGHT)
    reach_mm = l1_mm + l2_mm + PAYLOAD_OFFSET_MM
    roller_r_mm = gv('tt_roller_r')
    even_g = al.roller_share(rot_g)
    # THE OVERTURNING MOMENT, not mass x reach. J2's budget is already sum(m.r)
    # about the shoulder axis, and the fork stands on the yaw axis, so that sum
    # IS what tries to tip the turret. Handing this mass x full-reach put the
    # 47 g bracket - which sits at r 0 - out at 178 mm and reported one roller
    # carrying 4.7x the whole arm.
    overturning_gmm = al.joint_moment(j2_items) * 10.0
    worst_g = al.worst_roller_g(rot_g, overturning_gmm, roller_r_mm)
    print('rotating mass %.1f g (printed + 5 servos), reach %.0f mm'
          % (rot_g, reach_mm))
    print('overturning moment about J1: %.0f g.mm (= J2\'s own budget)'
          % overturning_gmm)
    print('per roller, evenly shared      %6.1f g  = %5.2f N' % (
        even_g, al.to_newtons(even_g)))
    print('WORST roller, arm over it      %6.1f g  = %5.2f N' % (
        worst_g, al.to_newtons(worst_g)))
    print('  three points on a circle do NOT share evenly when the arm reaches')
    print('  to one side. The worst figure is what to design to.')
    print('')
    axle_d = gv('tt_axle_d')
    axle_len = gv('ts_axle_len') if ups.itemByName('ts_axle_len') else 8.5
    stub_moment_nmm = al.to_newtons(worst_g) * (axle_len / 2.0)
    s_axle = al.stress_check(
        'roller stub axle root, %.1f dia' % axle_d, stub_moment_nmm,
        al.annulus_section_modulus_mm3(axle_d, 0.0), across_layers=True)
    print('  stub axle: %.2f N at %.1f mm = %.1f N.mm'
          % (al.to_newtons(worst_g), axle_len / 2.0, stub_moment_nmm))
    print('  %-34s %6.2f MPa / %5.2f allow = %4.0f%%  %s'
          % (s_axle['name'], s_axle['sigma_mpa'],
             s_axle['allowable_with_safety_mpa'],
             s_axle['utilisation'] * 100, 'OVER' if s_axle['over'] else ''))
    print('  ACROSS LAYERS: the stub prints as a horizontal cylinder bridging')
    print('  off its cheek, so its root is a layer boundary. That halves the')
    print('  allowable and it is the reason this check exists.')
    stress.append(s_axle)
    print('')
    floor = gv('ts_relief_floor')
    relief_ir = roller_r_mm - gv('tt_roller_w') / 2.0 - gv('ts_relief_margin')
    band_mm = gv('ts_cheek_ir') if ups.itemByName('ts_cheek_ir') else 31.0
    print('  relieved band: plate floored to %.2f from r %.1f to r %.1f'
          % (floor, relief_ir, band_mm))
    print('  It does NOT sit under the axle. The cheeks stand at r %.1f..%.1f'
          % (band_mm, band_mm + gv('ts_cheek_t')))
    print('  on FULL %.1f mm plate - the relief stops at cheek_ir, asserted in'
          % gv('ts_plate_t'))
    print('  turntable_stator. So the band is a WEB between the servo pad and')
    print('  the cheeks, loaded in shear and bending, not a bearing pad.')
    print('  Earlier framing of this as "a cantilevered axle on 1.6 mm" was')
    print('  wrong and is corrected here.')
    print('')

    fails = duty_fail + ['%s at %.0f%%' % (s['name'], s['utilisation'] * 100)
                         for s in stress if s['over']]
    print('GATE loads duty      : %s' % ('PASS' if not duty_fail else 'FAIL'))
    print('GATE loads sections  : %s'
          % ('PASS' if not [s for s in stress if s['over']] else 'FAIL'))
    for f in fails:
        print('   %s' % f)
    print('')
    print('STILL ASSUMED, not measured here:')
    print('  The BOUGHT parts. Three servos sit at declared offsets because')
    print('  no model file contains them - there is no COM to read. They are')
    print('  %.1f g of the %.1f g cluster.'
          % (sum(BOUGHT_G[k] for k in BOUGHT_OFFSET_MM), rot_g))
    print('  The pruner head is one lump at HEAD_OFFSET_MM %.1f mm; its own'
          % HEAD_OFFSET_MM)
    print('  five pieces are measured but not composed.')
    print('  Static only - no slew, no stop, no impact. No FEA.')
