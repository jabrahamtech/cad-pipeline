"""robotarm/_export_plates - every piece, oriented and packed onto plates.

ONE 3MF PER PLATE. Fusion writes a single-plate 3MF; multi-plate project
files are a slicer format, not something Fusion exports. So "one file" means
one per plate, with the parts already turned the right way up and arranged.

WHAT THIS DOES THAT DRAGGING FILES INTO A SLICER DOES NOT: it applies each
part's PRINT ORIENTATION from its own docstring, which for three of them is
not a preference:

  gripcut_finger  TOP FACE DOWN. Layers must lie ALONG the leaf or the
                  flexure is a fatigue crack waiting. Printed flat the wrong
                  way it looks identical and breaks.
  pruner_rack     BACK FACE DOWN, not teeth down - teeth down needs support
                  under the drive pin.
  turntable_stator  base down, and SUPPORTS OFF: the stub axle bridge is
                  load-bearing and support scars it.

THE PACKING IS CHECKED, NOT EYEBALLED. Every placed rectangle is asserted
inside the plate and against every other rectangle for overlap, and every
placed body is re-measured in Fusion afterwards for bounds and for sitting
on z = 0. Two orientation bugs have already shipped on this project in one
day - both mine, both caught by Jonathan looking at a picture - so nothing
here is trusted because it looks right.

BED: Bambu Lab X2D, 256 x 256. MARGIN keeps parts off the edge; GAP is the
space between them. Neither is a slicer setting - re-check brims yourself,
base_lid wants one and a brim is 5-8 mm of extra footprint.
"""

import json
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
SRC_DIR = os.path.join(REPO, 'exports', 'robotarm', 'print')
OUT_DIR = os.path.join(REPO, 'exports', 'robotarm', 'plates')
LEDGER = os.path.join(REPO, 'specs', 'robotarm', '_volumes.json')
VERSION = 3
BED_X, BED_Y = 256.0, 256.0
MARGIN, GAP = 6.0, 4.0
# A BRIM IS FOOTPRINT. base_lid is 171.75 across, 3 thick, and warps without
# one - so it needs a brim, and a brim is 5-8 mm of extra plastic all round
# that the packer has to know about or the neighbours land on top of it. The
# part is placed CENTRED in its padded slot, so the pad is real space.
BRIM_PAD = {'base_lid': 8.0}
PETG, SOLID = 1.27, 0.65

# name, qty, (rotation axis, degrees) to put the print face DOWN, why
ORIENT = [
    ('base_lid',         1, None,        'flat 3 mm plate, BRIM'),
    ('upper_arm',        1, ('y', -90),  'built along X, 125 mm across the bed'),
    ('forearm',          1, ('y', -90),  '-X face down. SUPPORTS under +X wall and lobes'),
    ('wrist_roll',       1, ('x', 90),   'back face down, built +Y'),
    ('turntable_stator', 1, None,        'base down, cheeks up. SUPPORTS OFF'),
    ('turntable_ring',   1, None,        'annulus. Do not sand the bore'),
    ('shoulder_bracket', 1, ('y', -90),  '-X face down, journal bores vertical'),
    ('pruner_shell',     2, None,        'split face down. TWO'),
    ('pruner_rack',      2, ('x', 180),  'BACK face down - teeth down needs support'),
    ('pruner_blade',     2, None,        'inner face down. TWO'),
    ('wrist_rotator',    1, None,        'back face down, insert bosses vertical'),
    ('wrist_hub',        2, None,        'collar face down. TWO'),
    ('shoulder_hub',     1, None,        'collar face down'),
    ('gripper_pinion',   1, None,        'flat'),
    ('gripcut_finger',   2, ('x', 180),  'TOP FACE DOWN - the flexure rule. TWO'),
]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    M3 = adsk.core.Matrix3D.create
    V3 = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)
    AXIS = {'x': V3(1, 0, 0), 'y': V3(0, 1, 0), 'z': V3(0, 0, 1)}

    comps = {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in comps:
            comps[n] = occ.component
    with open(LEDGER) as fh:
        ledger = json.load(fh)

    def rot_of(spec):
        m = M3()
        if spec is not None:
            import math
            m.setToRotation(math.radians(spec[1]), AXIS[spec[0]], ORG)
        return m

    # ---- measure every piece in its PRINT orientation ----------------------
    pieces = []
    for name, qty, spec, note in ORIENT:
        full = 'robotarm_' + name
        assert full in comps, '%s not in this document' % full
        comp = comps[full]
        assert comp.bRepBodies.count == 1, '%s is not one body' % name
        body = comp.bRepBodies.item(0)
        vol = body.volume * 1000.0
        assert abs(vol - ledger[name]) <= 1.0, (
            '%s is %.3f but the ledger says %.3f - this is not the geometry '
            'the gates passed' % (name, vol, ledger[name]))
        m = rot_of(spec)
        # rotate the 8 bbox corners to get the footprint after orientation
        bb = body.boundingBox
        xs, ys, zs = [], [], []
        for cx in (bb.minPoint.x, bb.maxPoint.x):
            for cy in (bb.minPoint.y, bb.maxPoint.y):
                for cz in (bb.minPoint.z, bb.maxPoint.z):
                    p = adsk.core.Point3D.create(cx, cy, cz)
                    p.transformBy(m)
                    xs.append(p.x * 10)
                    ys.append(p.y * 10)
                    zs.append(p.z * 10)
        w, d, h = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
        pad = BRIM_PAD.get(name, 0.0)
        for k in range(qty):
            pieces.append(dict(name=name, comp=comp, rot=m, note=note,
                               w=w + 2 * pad, d=d + 2 * pad, h=h, vol=vol,
                               pad=pad, raw=(w, d),
                               lo=(min(xs), min(ys), min(zs)), idx=k))

    # ---- pack: first fit into ANY open shelf, on ANY plate ----------------
    # The first version was a single forward shelf pass and it cost a whole
    # plate: base_lid is 171.8 deep, so its row owned the bed, and the 256 x
    # 68 strip left underneath was never revisited - eleven small parts went
    # to a third plate that was 13 % full.
    #
    # This keeps every shelf open on every plate and tries them all before
    # opening anything new. Still simple enough to read, which matters more
    # than optimal: a packer nobody can check is a packer nobody should trust.
    pieces.sort(key=lambda p: (-p['d'], -p['w']))
    plates = []          # each: dict(shelves=[dict(y, d, x)], items=[])

    def fits_shelf(sh, pc, plate):
        if pc['d'] > sh['d'] + 1e-9:
            return False
        return sh['x'] + pc['w'] <= BED_X - MARGIN + 1e-9

    for pc in pieces:
        assert pc['w'] <= BED_X - 2 * MARGIN and pc['d'] <= BED_Y - 2 * MARGIN, (
            '%s is %.1f x %.1f and does not fit a %.0f x %.0f bed at all'
            % (pc['name'], pc['w'], pc['d'], BED_X, BED_Y))
        done = False
        # 1. an existing shelf with room
        for plate in plates:
            for sh in plate['shelves']:
                if fits_shelf(sh, pc, plate):
                    pc['x'], pc['y'] = sh['x'], sh['y']
                    sh['x'] += pc['w'] + GAP
                    plate['items'].append(pc)
                    done = True
                    break
            if done:
                break
        if done:
            continue
        # 2. a new shelf on an existing plate
        for plate in plates:
            top = MARGIN
            for sh in plate['shelves']:
                top = max(top, sh['y'] + sh['d'] + GAP)
            if top + pc['d'] <= BED_Y - MARGIN + 1e-9:
                sh = dict(y=top, d=pc['d'], x=MARGIN)
                pc['x'], pc['y'] = sh['x'], sh['y']
                sh['x'] += pc['w'] + GAP
                plate['shelves'].append(sh)
                plate['items'].append(pc)
                done = True
                break
        if done:
            continue
        # 3. a new plate
        sh = dict(y=MARGIN, d=pc['d'], x=MARGIN)
        pc['x'], pc['y'] = sh['x'], sh['y']
        sh['x'] += pc['w'] + GAP
        plates.append(dict(shelves=[sh], items=[pc]))
    plates = [pl['items'] for pl in plates]

    # ---- prove the packing before building anything ------------------------
    for i, plate in enumerate(plates):
        for a in range(len(plate)):
            pa = plate[a]
            assert pa['x'] >= MARGIN - 1e-6 and pa['y'] >= MARGIN - 1e-6, (
                'plate %d: %s starts off the bed' % (i + 1, pa['name']))
            assert pa['x'] + pa['w'] <= BED_X - MARGIN + 1e-6, (
                'plate %d: %s runs off in X' % (i + 1, pa['name']))
            assert pa['y'] + pa['d'] <= BED_Y - MARGIN + 1e-6, (
                'plate %d: %s runs off in Y' % (i + 1, pa['name']))
            for b in range(a + 1, len(plate)):
                pb = plate[b]
                gap_x = (pa['x'] + pa['w'] <= pb['x'] + 1e-6
                         or pb['x'] + pb['w'] <= pa['x'] + 1e-6)
                gap_y = (pa['y'] + pa['d'] <= pb['y'] + 1e-6
                         or pb['y'] + pb['d'] <= pa['y'] + 1e-6)
                assert gap_x or gap_y, (
                    'plate %d: %s and %s overlap'
                    % (i + 1, pa['name'], pb['name']))

    # ---- build and export --------------------------------------------------
    os.makedirs(OUT_DIR, exist_ok=True)
    STALE = 'robotarm_plate'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name.startswith(STALE):
            c.name = STALE + '_stale_' + str(i)
    for o in list(root.occurrences):
        if o.component.name.startswith(STALE + '_stale_'):
            o.deleteMe()

    made = []
    for i, plate in enumerate(plates):
        pocc = root.occurrences.addNewComponent(M3())
        pocc.component.name = '%s_%d' % (STALE, i + 1)
        pc = pocc.component
        for p in plate:
            m = p['rot'].copy()
            t = m.translation
            t.x = (p['x'] + p['pad'] - p['lo'][0]) / 10.0
            t.y = (p['y'] + p['pad'] - p['lo'][1]) / 10.0
            t.z = (0.0 - p['lo'][2]) / 10.0
            m.translation = t
            pc.occurrences.addExistingComponent(p['comp'], m)
        # RE-MEASURE what was actually built, do not trust the arithmetic
        for k in range(pc.occurrences.count):
            o = pc.occurrences.item(k)
            for j in range(o.bRepBodies.count):
                bb = o.bRepBodies.item(j).boundingBox
                assert bb.minPoint.z * 10 > -0.01, (
                    'plate %d: %s sits below the bed at z %.3f'
                    % (i + 1, o.component.name, bb.minPoint.z * 10))
                assert bb.minPoint.z * 10 < 0.01, (
                    'plate %d: %s floats %.3f above the bed'
                    % (i + 1, o.component.name, bb.minPoint.z * 10))
                assert (bb.minPoint.x * 10 > -0.01
                        and bb.maxPoint.x * 10 < BED_X + 0.01
                        and bb.minPoint.y * 10 > -0.01
                        and bb.maxPoint.y * 10 < BED_Y + 0.01), (
                    'plate %d: %s lands outside the bed' % (i + 1, o.component.name))
        pocc.isLightBulbOn = True
        path = os.path.join(OUT_DIR, 'plate_%d_v%d.3mf' % (i + 1, VERSION))
        assert not os.path.exists(path), '%s exists - bump VERSION' % path
        em = design.exportManager
        em.execute(em.createC3MFExportOptions(pc, path))
        size = os.path.getsize(path)
        assert size > 50000, 'plate %d exported %d bytes' % (i + 1, size)
        made.append((i + 1, plate, path, size))

    print('=== %d plate(s), %.0f x %.0f bed, %.0f margin / %.0f gap ==='
          % (len(plates), BED_X, BED_Y, MARGIN, GAP))
    print('')
    total_g = 0.0
    for n, plate, path, size in made:
        g = sum(p['vol'] for p in plate) * PETG * SOLID / 1000.0
        total_g += g
        tall = max(p['h'] for p in plate)
        used = sum(p['w'] * p['d'] for p in plate)
        print('PLATE %d - %d pieces, %.0f g, tallest %.1f mm, %.0f%% of the bed'
              % (n, len(plate), g, tall,
                 100.0 * used / (BED_X * BED_Y)))
        print('  %s  (%d bytes)' % (os.path.basename(path), size))
        for p in sorted(plate, key=lambda q: (q['x'], q['y'])):
            extra = ' (+%.0f brim)' % p['pad'] if p['pad'] else ''
            print('    %-18s %6.1f x %-6.1f h %-5.1f at (%5.1f, %5.1f)%s  %s'
                  % (p['name'], p['raw'][0], p['raw'][1], p['h'],
                     p['x'] + p['pad'], p['y'] + p['pad'], extra,
                     p['note'] if p['idx'] == 0 else ''))
        print('')
    print('%d pieces, %.0f g of PETG total' % (len(pieces), total_g))
    print('')
    print('SUPPORTS: forearm only. OFF everywhere else - on turntable_stator')
    print('  that is not a preference, the axle bridge is load-bearing.')
    print('BRIM: base_lid. Budget 5-8 mm of extra footprint for it.')
    print('Orientations are BAKED IN. If you auto-arrange in the slicer, keep')
    print('  rotation locked or gripcut_finger and pruner_rack will flip.')
