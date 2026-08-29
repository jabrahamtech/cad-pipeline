"""robotarm/_export_arm - export every printable part, with a print plan.

WHAT THIS IS. _export_turret does the three J1 parts. This does all fifteen,
with the COUNT of each, because five of them are not one-offs and a plan that
says "pruner_shell" when it means "two of them" gets you halfway through an
assembly before you find out.

IT REFUSES TO EXPORT ANYTHING THE LEDGER HAS NOT SEEN. Every part's volume is
checked against specs/robotarm/_volumes.json before it is written. That file
is what _check_ledger gates on, so a match means this export is the geometry
the gates passed - not something rebuilt from edited source since. Without it
the export is just whatever happens to be in the document, which on this
project has more than once been a stale rebuild.

Never overwrite a version that may have been printed; bump VERSION instead.

v1: 2026-08-29. First whole-arm export. Carries L1 125 (the 65 -> 125 length
change), the lead keyways on their corrected walls in all five pocket parts,
the stator's single tab pilot and re-sited lead groove, cable_ir 13.7 with
base_lid following it, and pruner_shell's 2.5 mm cheek trim.

PRINT THE GAUGE FIRST. exports/robotarm/gauge_verify_v2.3mf settles five
numbers that these parts are cut to, and four of them have never been near a
servo: the MG90S tab pitch is DERIVED, the MG995 bed was corrected on paper,
the turret's cross pocket was re-cut to a measured taper nobody has test
fitted, and the flexure leaf has never been sprung. If one of those is wrong,
the parts it gates get reprinted - forearm, shoulder_bracket, wrist_roll,
turntable_stator, gripcut_finger. That is most of the arm, against about an
hour and 29 g for the plate.
"""

import json
import os
import shutil

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
EXPORT_DIR = os.path.join(REPO, 'exports', 'robotarm', 'print')
# The flat, numbered, un-versioned copy you actually feed the slicer. The
# versioned files above are the ARCHIVE and are never overwritten; this
# folder is the CURRENT queue and is rewritten every export. Two different
# jobs, so two different rules - a folder that is both is neither.
QUEUE_DIR = os.path.join(REPO, 'exports', 'robotarm', 'print_queue')
LEDGER = os.path.join(REPO, 'specs', 'robotarm', '_volumes.json')
VERSION = 2
TOL_MM3 = 1.0
PETG, SOLID = 1.27, 0.65

# Queue order. 01 is the gauge, which is not a part and so is not in PARTS -
# it is copied in separately. The rest are printed in this order for a reason:
# the turret first because "does J1 turn" is the riskiest open claim in the
# project, then the arm, then the head, then the lid last because you can
# print it while assembling everything else.
QUEUE = ['turntable_stator', 'turntable_ring', 'shoulder_bracket', 'upper_arm',
         'forearm', 'wrist_roll', 'wrist_rotator', 'wrist_hub', 'shoulder_hub',
         'pruner_shell', 'pruner_blade', 'pruner_rack', 'gripper_pinion',
         'gripcut_finger', 'base_lid']
# suffixes that put the instruction in the FILENAME, where it cannot be
# missed, rather than in a document nobody has open at the printer
SUFFIX = {'forearm': '_SUPPORTS', 'base_lid': '_BRIM'}
GAUGE = os.path.join(REPO, 'exports', 'robotarm', 'gauge_verify_v2.3mf')

# name, how many, print orientation, note
PARTS = [
    ('turntable_stator', 1, 'FLAT, base down, cheeks and posts UP',
     'the stub axles grow sideways off the cheeks as horizontal cylinders - '
     'the one real overhang, short enough to bridge. SUPPORTS OFF: that '
     'bridge is load-bearing and support scars it.'),
    ('turntable_ring', 1, 'FLAT - it is an annulus, there is no second option',
     'no support. The bore is the J1 journal: do not sand it.'),
    ('base_lid', 1, 'FLAT, 3 mm plate',
     'BRIM ON - 171.75 across and 3 thick, it will warp without one.'),
    ('shoulder_bracket', 1, '-X FACE DOWN, built along +X',
     'both journal bores come out vertical and round. The disc stands on '
     'edge, which is wrong for the race face and the O68 journal - if either '
     'proves out of round, split the part on the boss top plane.'),
    ('shoulder_hub', 1, 'COLLAR FACE ON THE BED, built +Z', 'no support.'),
    ('upper_arm', 1, 'FLAT, built along X, the 125 mm length across the bed',
     'the hex sockets face along X and want to be vertical. NOW 125 mm long '
     '- check it fits the bed diagonally before slicing.'),
    ('forearm', 1, '-X FACE DOWN, built along +X',
     'all four journal bores vertical and round. This one DOES need support '
     'under the +X wall and the two lobes.'),
    ('wrist_hub', 2, 'COLLAR FACE ON THE BED, built +Z',
     'every cross-section shrinks going up, so no support. TWO OF THESE.'),
    ('wrist_roll', 1, 'BACK FACE ON THE BED, built along +Y',
     'the servo pocket is then a prism opening at the bed and the lead '
     'keyway vents through the roof. No support.'),
    ('wrist_rotator', 1, 'BACK FACE ON THE BED, built +Z',
     'insert bosses vertical, which is what heat-set inserts want. No support.'),
    ('pruner_shell', 2, 'SPLIT FACE (z = 0) ON THE BED, built +Z',
     'TWO OF THESE - it is a clamshell, one design used twice, the second '
     'turned over. This is the part the load gate counted once.'),
    ('pruner_blade', 2, 'INNER FACE ON THE BED, built +Z',
     'flat plate, pivot bore and drive slot vertical. No support. TWO.'),
    ('pruner_rack', 2, 'BACK FACE ON THE BED, built along -Z',
     'teeth down would need support for the pin. TWO.'),
    ('gripper_pinion', 1, 'FLAT, z = 0 on the bed', 'no support.'),
    ('gripcut_finger', 2, 'TOP FACE DOWN (z +9.55 on the bed)',
     'layers then lie ALONG the leaf, so bending stress is in-plane - the '
     'flexure only works printed this way. TWO.'),
]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    comps, occs = {}, {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in comps:
            comps[n] = occ.component
            occs[n] = occ

    with open(LEDGER) as fh:
        ledger = json.load(fh)

    os.makedirs(EXPORT_DIR, exist_ok=True)
    em = design.exportManager
    written, total_mm3, drift = [], 0.0, []

    for name, count, orientation, note in PARTS:
        full = 'robotarm_' + name
        assert full in comps, (
            '%s is not in this document - run _check_ledger BATCH 0..3' % full)
        comp = comps[full]
        assert comp.bRepBodies.count == 1, (
            '%s has %d bodies; an export must be one solid'
            % (name, comp.bRepBodies.count))
        body = comp.bRepBodies.item(0)
        assert body.isValid, '%s is not a valid body' % name

        # THE GATED GEOMETRY, or nothing. A volume that does not match the
        # ledger means this document has been rebuilt from source the gates
        # have not seen since.
        vol = body.volume * 1000.0
        want = ledger.get(name)
        assert want is not None, '%s is not in the ledger at all' % name
        if abs(vol - want) > TOL_MM3:
            drift.append('%s: ledger %.3f, document %.3f' % (name, want, vol))
            continue

        # A HIDDEN OCCURRENCE EXPORTS AS AN EMPTY FILE - Fusion silently skips
        # it, and the gates toggle bulbs while posing.
        occs[full].isLightBulbOn = True
        assert occs[full].isLightBulbOn, '%s stays hidden' % name

        base = os.path.join(EXPORT_DIR, '%s_v%d' % (name, VERSION))
        assert not os.path.exists(base + '.3mf'), (
            '%s.3mf exists - bump VERSION rather than overwrite a part that '
            'may already be on a bed' % base)
        em.execute(em.createC3MFExportOptions(comp, base + '.3mf'))
        mf_b = os.path.getsize(base + '.3mf')
        assert mf_b > 20000, (
            '%s exported %d bytes - that is an empty file, not a part'
            % (name, mf_b))
        total_mm3 += vol * count
        written.append((name, count, vol, mf_b, orientation, note))

    assert not drift, (
        'these parts do not match the ledger, so they are NOT what the gates '
        'passed - re-run _check_ledger and re-baseline deliberately, or '
        'rebuild from source:\n  ' + '\n  '.join(drift))

    print('=== robotarm, every printable part, v%d ===' % VERSION)
    print('written to exports/robotarm/print/')
    print('')
    print('%-20s %3s %9s %9s  %s'
          % ('part', 'qty', 'mm3 ea', 'g total', 'orientation'))
    for name, count, vol, mf_b, orientation, note in written:
        print('%-20s %3d %9.0f %9.1f  %s'
              % (name, count, vol, vol * count * PETG * SOLID / 1000.0,
                 orientation))
    print('')
    for name, count, vol, mf_b, orientation, note in written:
        print('%s_v%d  x%d' % (name, VERSION, count))
        print('  %s' % note)
    print('')
    n_pieces = sum(c for _, c, _, _, _, _ in written)
    print('%d part types, %d pieces, %.0f mm3 = %.0f g of PETG'
          % (len(written), n_pieces, total_mm3,
             total_mm3 * PETG * SOLID / 1000.0))
    print('')
    print('PRINT SETTINGS - the SAME profile the gauge plate was printed on,')
    print('  or the fits stop meaning anything: PETG, 0.2 layers, 3 walls,')
    print('  15-20 % infill. Supports only where a part says so above.')
    print('')
    print('PRINT THE GAUGE FIRST. gauge_verify_v2.3mf settles five numbers')
    print('  these parts are cut to. If one is wrong, the reprint is forearm,')
    print('  shoulder_bracket, wrist_roll, turntable_stator and')
    print('  gripcut_finger - most of the arm, against an hour for the plate.')
    print('')
    print('BOUGHT PARTS: 1 x MG995, 2 x MG90S, 3 x SG90, 3 x 608ZZ,')
    print('  M3 hardware, and heat-set inserts for wrist_rotator.')

    # ---- the numbered queue -------------------------------------------------
    by_name = {n: (c, o, t) for n, c, _, m, o, t in
               [(w[0], w[1], w[2], w[3], w[4], w[5]) for w in written]}
    assert set(QUEUE) == set(by_name), (
        'QUEUE and PARTS disagree: %r' % (set(QUEUE) ^ set(by_name)))
    os.makedirs(QUEUE_DIR, exist_ok=True)
    made = []
    if os.path.exists(GAUGE):
        dst = os.path.join(QUEUE_DIR, '01_gauge_FIRST.3mf')
        shutil.copyfile(GAUGE, dst)
        made.append(os.path.basename(dst))
    else:
        print('')
        print('NOTE: %s is missing, so the queue has no 01. Print the gauge '
              'before any of this.' % os.path.basename(GAUGE))
    for i, name in enumerate(QUEUE, start=2):
        count = by_name[name][0]
        tag = '%s%s%s' % (name, '_x%d' % count if count > 1 else '',
                          SUFFIX.get(name, ''))
        src = os.path.join(EXPORT_DIR, '%s_v%d.3mf' % (name, VERSION))
        dst = os.path.join(QUEUE_DIR, '%02d_%s.3mf' % (i, tag))
        shutil.copyfile(src, dst)
        made.append(os.path.basename(dst))
    print('')
    print('QUEUE - exports/robotarm/print_queue/, print in number order:')
    for f in made:
        print('  %s' % f)
    print('')
    print('The queue is REWRITTEN every export and carries no version in the')
    print('names. The versioned files in print/ are the archive and are never')
    print('overwritten - if you need to know what you actually printed, that')
    print('is where it lives.')
