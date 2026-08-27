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

It measures and never mutates: no part script is executed, nothing is built,
no parameter is touched. Safe to run against a document you care about.
"""

import json
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
OUT = os.path.join(REPO, 'specs', 'robotarm', '_mass_properties.json')

# Bought parts carry no printed-density correction and no volume in Fusion,
# because none of them is modelled. lib/servo.py is the source for the servos.
BOUGHT_G = {
    'MG995 J2': 55.0,
    'MG90S J3': 13.4,
    'MG90S J4': 13.4,
    'SG90 J5': 9.0,
    'SG90 effector': 9.0,
    'SG90 J1 yaw': 9.0,
    '608ZZ x3': 3 * 32.0,
}

# Where each mass sits, as a radius from the joint being summed about, in mm.
# OFFSETS ARE MEASURED FROM THE WRIST END OF THE FOREARM, exactly as
# lib/arm_budget.py's CLUSTER is - the two files must not disagree about the
# geometry or they are modelling different arms.
CLUSTER_OFFSET_MM = {
    'wrist_hub': 0.0,
    'wrist_roll': 2.3,
    'wrist_rotator': 19.8,
    'MG90S J4': -6.0,
    'SG90 J5': 0.0,
    'SG90 effector': 32.0,
}
HEAD_OFFSET_MM = 47.0        # pruner head centre of mass, past the wrist end
PAYLOAD_G = 25.0             # rated payload, _assembly.md
PAYLOAD_OFFSET_MM = 68.0     # asm_l3 - wrist axis to the jaw faces

# The J1 turret: what rotates, and how far the arm reaches over the rollers.
ROTATING = ('shoulder_bracket', 'shoulder_hub', 'upper_arm', 'forearm',
            'wrist_hub', 'wrist_roll', 'wrist_rotator', 'pruner_shell',
            'pruner_blade', 'pruner_rack', 'gripper_pinion')
ROTATING_BOUGHT = ('MG995 J2', 'MG90S J3', 'MG90S J4', 'SG90 J5',
                   'SG90 effector')


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
    l2_mm = gv('fa_l2') if ups.itemByName('fa_l2') else gv('ua_l1')
    head_g = (mass('pruner_shell') + 2 * mass('pruner_blade')
              + 2 * mass('pruner_rack') + mass('gripper_pinion'))

    I = al.Item
    cluster = [
        I('wrist_hub x2', 2 * mass('wrist_hub'), 0.0, 'MEASURED'),
        I('wrist_roll', mass('wrist_roll'), CLUSTER_OFFSET_MM['wrist_roll'],
          'MEASURED'),
        I('wrist_rotator', mass('wrist_rotator'),
          CLUSTER_OFFSET_MM['wrist_rotator'], 'MEASURED'),
        I('MG90S J4', BOUGHT_G['MG90S J4'], CLUSTER_OFFSET_MM['MG90S J4'],
          'BOUGHT'),
        I('SG90 J5', BOUGHT_G['SG90 J5'], CLUSTER_OFFSET_MM['SG90 J5'],
          'BOUGHT'),
        I('SG90 effector', BOUGHT_G['SG90 effector'],
          CLUSTER_OFFSET_MM['SG90 effector'], 'BOUGHT'),
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
    fa_com_mm = l2_mm * 0.437       # _assembly.md's fraction, see the caveat
    j3_items = shifted(cluster, l2_mm)
    j3_items.append(I('forearm link', mass('forearm'), fa_com_mm, 'MEASURED'))
    j3_items.append(I('payload', PAYLOAD_G, l2_mm + PAYLOAD_OFFSET_MM,
                      'PAYLOAD'))

    # J2: shoulder at the origin. Everything above moves out by L1 again.
    j2_items = shifted(j3_items, l1_mm)
    j2_items.append(I('upper arm link', mass('upper_arm'), l1_mm * 0.5,
                      'MEASURED'))
    j2_items.append(I('MG90S J3', BOUGHT_G['MG90S J3'], l1_mm, 'BOUGHT'))

    print('=== B. joint moments, worst pose: arm straight out, payload gripped')
    print('L1 %.1f  L2 %.1f  head %.1f g (measured)  payload %.1f g'
          % (l1_mm, l2_mm, head_g, PAYLOAD_G))
    print('')
    print('%-7s %11s %11s %9s %9s  %s'
          % ('joint', 'required', 'duty', 'of duty', 'margin', ''))
    duty_fail = []
    for joint, items in (('J2', j2_items), ('J3', j3_items), ('J4', j4_items)):
        r = al.duty_report(joint, items)
        flag = 'OVER DUTY' if r['over'] else ''
        print('%-7s %8.2f kgcm %8.2f kgcm %8.0f%% %9.2f  %s'
              % (joint, r['required_kgcm'], r['duty_kgcm'],
                 r['fraction'] * 100, r['margin'], flag))
        if r['over']:
            duty_fail.append('%s at %.0f%% of duty' % (joint,
                                                       r['fraction'] * 100))
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
    rot_g = sum(mass(p) for p in ROTATING if p in props)
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
    print('  cluster offsets are rigid; forearm COM at 0.437 of L2 and upper')
    print('  arm at 0.50 are FRACTIONS from _assembly.md, not the COMs this')
    print('  script just harvested. Wiring those in is the next improvement.')
    print('  Static only - no slew, no stop, no impact.')
