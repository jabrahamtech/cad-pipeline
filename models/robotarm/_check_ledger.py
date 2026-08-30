"""robotarm/_check_ledger - the whole-project gate.

Rebuilds EVERY part from its committed script into ONE FRESH DOCUMENT and
compares all the volumes at the END. Nothing else in this project can see the
failure it exists for.

WHY IT EXISTS. `turntable_clip.py` set the shared `sty_radius` to 3.0 because
3.0 suits a small part. A fillet stores a live REFERENCE to a parameter, so
that one line re-cut every corner in every part already in the document:
pruner_shell +1352 mm3, forearm +209, shoulder_bracket +220. No exception, no
invalid body, and every part's own script still printed its own correct volume
- because each prints immediately after building, before the next script moves
the parameter. The damage only shows if you re-read an earlier part after a
later one has run.

So this gate reads LAST, and reads EVERYTHING. It is the only check that can
catch a part being changed by a file that never mentions it.

The other three gates answer a different question and none of them replaces
this one:
  _check_fit      does the gripper assemble
  _check_wrist    does J4/J5 sweep without touching
  _check_shoulder does J2 sweep without touching
Each rebuilds only the parts IT needs, so each is blind to everything else.

RUN IT IN BATCHES: `mod.BATCH = 0`, then 1, 2, 3, 4. Eighteen parts is over
the 60 s MCP call limit in one go. Batch 0 opens the fresh document; the LAST
batch does the comparison. Running them out of order is caught, not guessed at.

The ledger itself is specs/robotarm/_volumes.json. If it is missing, batch 2
WRITES it and says so rather than passing vacuously - but a ledger written
from a run you have not read is not a gate, it is a photograph. Read the
numbers before you trust the next run.
"""

import json
import importlib.util
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
LEDGER = os.path.join(REPO, 'specs', 'robotarm', '_volumes.json')

# Order matters: it is the order the arm is built in, and a shared-parameter
# fault only shows downstream of the file that causes it.
BATCHES = [
    ['gripper_pinion', 'pruner_blade', 'gripcut_finger', 'pruner_rack',
     'pruner_shell'],
    ['wrist_hub', 'wrist_rotator', 'wrist_roll', 'forearm'],
    ['upper_arm', 'shoulder_hub', 'shoulder_bracket'],
    ['turntable_stator', 'turntable_ring', 'base_lid'],
    # The J3 reduction. LAST because j3_gear asserts against fa_plate_t and
    # fa_bore_d, which do not exist until forearm has built in batch 1 - a
    # gear that silently skips its own fit check is worse than no check.
    ['j3_pinion', 'j3_gear', 'j3_axle'],
]
# The superseded gripper head still builds but is not in the arm, so it is not
# in the ledger. Add gripper_shell and gripper_rack_jaw here if it comes back.
# turret_cap and turntable_clip are gone entirely - the printed platter kept
# its control unit and the turntable was redesigned around it. They live in
# legacy/models/robotarm/superseded/.
#
# shoulder_bracket is built BEFORE the turntable pair on purpose: it IS J1's
# rotor, so it defines half the tt_ block the other two consume, and building
# it last would hide a contract that had drifted.

# Volumes are in mm3. A shared-parameter fault moves them by hundreds; 1.0 mm3
# is far tighter than that and still well clear of float noise on a 25000 mm3
# body.
TOL_MM3 = 1.0

BATCH = 0


def run(_context: str):
    app = adsk.core.Application.get()

    if BATCH == 0:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        print('opened a FRESH document - nothing here is inherited')
    else:
        design = adsk.fusion.Design.cast(app.activeProduct)

    assert 0 <= BATCH < len(BATCHES), 'BATCH must be 0..%d' % (len(BATCHES) - 1)
    root = design.rootComponent

    have = set()
    for occ in root.occurrences:
        have.add(occ.component.name.replace('robotarm_', ''))
    expected_before = [n for b in BATCHES[:BATCH] for n in b]
    missing = [n for n in expected_before if n not in have]
    assert not missing, (
        'batch %d expects %d parts already built and %r are missing - the batches '
        'were run out of order, or batch 0 opened a document this one is not in'
        % (BATCH, len(expected_before), missing))

    for name in BATCHES[BATCH]:
        path = os.path.join(REPO, 'models', 'robotarm', name + '.py')
        assert os.path.exists(path), 'missing ' + path
        spec = importlib.util.spec_from_file_location('gen_' + name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run(_context)

    design.timeline.moveToEnd()

    if BATCH < len(BATCHES) - 1:
        print('')
        print('batch %d built: %s' % (BATCH, ', '.join(BATCHES[BATCH])))
        print('now run BATCH = %d' % (BATCH + 1))
        return

    # ---- the comparison ------------------------------------------------------
    now = {}
    multi = []
    for occ in root.occurrences:
        c = occ.component
        n = c.name.replace('robotarm_', '')
        if c.bRepBodies.count != 1:
            multi.append('%s has %d bodies' % (n, c.bRepBodies.count))
            continue
        now[n] = round(c.bRepBodies.item(0).volume * 1000, 3)
    assert not multi, 'not one body per part: ' + '; '.join(multi)

    want_all = [n for b in BATCHES for n in b]
    absent = [n for n in want_all if n not in now]
    assert not absent, 'built but not found in the document: %r' % absent

    if not os.path.exists(LEDGER):
        with open(LEDGER, 'w') as fh:
            json.dump({k: now[k] for k in want_all}, fh, indent=2, sort_keys=True)
            fh.write('\n')
        print('')
        print('NO LEDGER EXISTED. Wrote %s from this run.' % LEDGER)
        print('That is not a pass - it is a photograph. Read these numbers, satisfy')
        print('yourself they are right, and commit the file. The NEXT run is a gate.')
        for k in want_all:
            print('  %-22s %10.3f mm3' % (k, now[k]))
        return

    with open(LEDGER) as fh:
        want = json.load(fh)

    print('')
    print('=== volume ledger ===')
    print('%-22s %12s %12s %10s' % ('part', 'ledger', 'built', 'delta'))
    drift, new, gone = [], [], []
    for k in want_all:
        w = want.get(k)
        b = now[k]
        if w is None:
            new.append(k)
            print('%-22s %12s %12.3f %10s' % (k, '-', b, 'NEW'))
            continue
        d = b - w
        flag = '' if abs(d) <= TOL_MM3 else '  <<< DRIFT'
        print('%-22s %12.3f %12.3f %10.3f%s' % (k, w, b, d, flag))
        if abs(d) > TOL_MM3:
            drift.append('%s %+.1f mm3' % (k, d))
    for k in want:
        if k not in now:
            gone.append(k)

    print('')
    if new:
        print('IN THE BUILD BUT NOT THE LEDGER: %r' % new)
        print('  A new part is not a failure. OVERWRITE %s and re-run - note'
              % os.path.basename(LEDGER))
        print('  overwrite, not delete: device_bash cannot delete files on the Mac.')
    if gone:
        print('IN THE LEDGER BUT NOT BUILT: %r' % gone)
    print('components %d | timeline %d | params %d' % (
        design.allComponents.count, design.timeline.count,
        design.userParameters.count))
    print('GATE ledger : %s' % ('PASS - every part matches, so no file is reaching '
                                'into another' if not drift
                                else 'FAIL - ' + '; '.join(drift)))
    if drift:
        print('  Volumes UP means a shared parameter moved - look for a style(),')
        print('  wrist() or turret() call giving a shared name a different value.')
        print('  Volumes DOWN means an unscoped CUT - look for a non-NewBody')
        print('  feature with no participantBodies. See fusion/PLAYBOOK.md.')
