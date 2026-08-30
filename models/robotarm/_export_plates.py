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
VERSION = 6
BED_X, BED_Y = 256.0, 256.0
MARGIN, GAP = 6.0, 4.0
# A BRIM IS FOOTPRINT. base_lid is 171.75 across, 3 thick, and warps without
# one - so it needs a brim, and a brim is 5-8 mm of extra plastic all round
# that the packer has to know about or the neighbours land on top of it. The
# part is placed CENTRED in its padded slot, so the pad is real space.
BRIM_PAD = {'base_lid': 5.0}

# SETTINGS THAT CANNOT SHARE A PLATE. forearm is the only part that wants
# supports; turntable_stator is a part they would RUIN - its stub axle bridge
# is load-bearing and support scars the underside. Putting them together
# means one per-object override stands between you and a wrecked axle, so
# they go on different plates and the packer enforces it rather than a note
# in a document hoping to be read.
NEVER_TOGETHER = [('forearm', 'turntable_stator')]

# PLATES ARE ASSIGNED, NOT PACKED INTO. Letting a bin-packer choose was the
# wrong objective and it showed: sorting for density put forearm (supports)
# beside turntable_stator (supports would ruin it), and sorting for height
# put the 76 mm shoulder_bracket in the middle of twelve small parts, where
# if it lets go it ploughs through all of them.
#
# So the grouping is a decision, and the packer only arranges within it:
#
#   1  THE J1 ANSWER, and everything that needs no supports and no brim.
#      Print this one first: "does the turret turn" is the riskiest open
#      claim in the project and this plate settles it. Uniform settings -
#      supports OFF, no brim - so there is no per-object override to forget.
#   2  The long parts and the big thin one. base_lid wants a brim, forearm
#      wants supports, and neither can hurt the other. Nothing on this plate
#      is short enough to be shadowed by upper_arm's 151 mm of travel.
PLATE_OF = {
    'turntable_stator': 1, 'turntable_ring': 1, 'shoulder_bracket': 1,
    'shoulder_hub': 1, 'wrist_hub': 1, 'wrist_roll': 1, 'wrist_rotator': 1,
    'pruner_shell': 1, 'gripper_pinion': 1, 'gripcut_finger': 1,
    # the flat ones ride in the 58 mm strip beside base_lid, which is
    # otherwise dead space - plate 1 has no room for them and this costs
    # nothing
    'pruner_blade': 2, 'pruner_rack': 2,
    'base_lid': 2, 'upper_arm': 2, 'forearm': 2,
}
# A SUBSET, when some of it is already on the bench. Empty means everything.
# Parts not named in PLATE_OF land in a bucket that opens new plates as it
# fills, instead of asserting - the deliberate grouping is for the full build
# and does not apply to whatever happens to be left.
ONLY = []
AUTO_SPLIT = False

PLATE_NOTE = {
    1: 'THE J1 ANSWER + the head. Supports OFF, no brim - uniform settings.',
    2: 'The long parts. base_lid BRIM, forearm SUPPORTS, nothing else.',
}

# Parts whose height makes them the thing that gets knocked off. A tall part
# is placed at the BACK, so the toolhead crosses it less on its way to
# everything else, and a detached part does not then plough through the rest.
TALL_MM = 40.0
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
        if ONLY and name not in ONLY:
            continue
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
                               pad=pad, raw=(w, d), yaw=False,
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
    # ---- arrange WITHIN each assigned plate --------------------------------
    # Tallest first, so the tall parts take the first shelf, which the mirror
    # at the end lifts to the BACK of the bed - less toolhead travel across
    # them, and a part that lets go does not sweep the others on its way.
    groups = {}
    for pc in pieces:
        if AUTO_SPLIT:
            groups.setdefault(99, []).append(pc)
            continue
        assert pc['name'] in PLATE_OF, '%s has no plate assigned' % pc['name']
        groups.setdefault(PLATE_OF[pc['name']], []).append(pc)

    plates = []
    for key in sorted(groups):
        # DEEPEST first, tallest as the tie-break. Sorting by height first
        # read better but packed badly: turntable_ring is 100 x 100 and only
        # 4 mm tall, so it sorted to the end and missed the shelf its
        # identically-sized twin turntable_stator had already opened. Shelf
        # packing wants like depths adjacent; height only decides ties.
        items = sorted(groups[key], key=lambda p: (-p['d'], -p['h'], -p['w']))
        shelves, items_done = [], []
        for pc in items:
            assert (pc['w'] <= BED_X - 2 * MARGIN
                    and pc['d'] <= BED_Y - 2 * MARGIN), (
                '%s is %.1f x %.1f and does not fit a %.0f x %.0f bed'
                % (pc['name'], pc['w'], pc['d'], BED_X, BED_Y))
            # YAW IS FREE. Turning a part 90 deg about Z does not change
            # which face is on the bed, so it costs nothing in print quality
            # and it is the difference between this fitting and not. Try both
            # ways round on every shelf before opening a new one.
            done = False
            for sh in shelves:
                for yaw in (False, True):
                    w, d = (pc['d'], pc['w']) if yaw else (pc['w'], pc['d'])
                    if (d <= sh['d'] + 1e-9
                            and sh['x'] + w <= BED_X - MARGIN + 1e-9):
                        pc['yaw'] = yaw
                        pc['w'], pc['d'] = w, d
                        pc['x'], pc['y'] = sh['x'], sh['y']
                        sh['x'] += w + GAP
                        done = True
                        break
                if done:
                    break
            if done:
                # BOOK IT ONTO THE PLATE. Missing this line placed the part
                # correctly and then dropped it from the plate's own list:
                # the run reported '12 pieces' and exported five, because
                # everything that shared an existing shelf was positioned and
                # then forgotten.
                items_done.append(pc)
                continue
            top = MARGIN
            for sh in shelves:
                top = max(top, sh['y'] + sh['d'] + GAP)
            # opening a shelf: take whichever way round is SHALLOWER, since
            # shelf depth is what runs the plate out of room
            if pc['d'] > pc['w'] and top + pc['w'] <= BED_Y - MARGIN + 1e-9:
                pc['yaw'] = True
                pc['w'], pc['d'] = pc['d'], pc['w']
            if top + pc['d'] > BED_Y - MARGIN + 1e-9:
                if AUTO_SPLIT:
                    plates.append(items_done)
                    items_done, shelves = [], []
                    top = MARGIN
                else:
                    raise AssertionError(
                        'plate %d is full: %s (%.1f x %.1f) will not fit. Move '
                        'something to the other plate in PLATE_OF rather than '
                        'letting a packer decide - the grouping is deliberate.'
                        % (key, pc['name'], pc['w'], pc['d']))
            sh = dict(y=top, d=pc['d'], x=MARGIN)
            pc['x'], pc['y'] = sh['x'], sh['y']
            sh['x'] += pc['w'] + GAP
            shelves.append(sh)
            items_done.append(pc)
        plates.append(items_done)

    # the conflict rule is now structural, but assert it anyway - a future
    # edit to PLATE_OF is exactly the kind of thing that quietly breaks it
    for i, plate in enumerate(plates):
        here = set(p['name'] for p in plate)
        for a, b in NEVER_TOGETHER:
            assert not (a in here and b in here), (
                'plate %d has both %s and %s, whose settings are '
                'incompatible' % (i + 1, a, b))

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
            if p['yaw']:
                import math
                yz = M3()
                yz.setToRotation(math.radians(90), AXIS['z'], ORG)
                yz.transformBy(m)
                m = yz
                # re-measure the corner after the yaw, or the part lands in
                # the wrong place by its own width
                bb0 = p['comp'].bRepBodies.item(0).boundingBox
                xs2, ys2, zs2 = [], [], []
                for cx in (bb0.minPoint.x, bb0.maxPoint.x):
                    for cy in (bb0.minPoint.y, bb0.maxPoint.y):
                        for cz in (bb0.minPoint.z, bb0.maxPoint.z):
                            q = adsk.core.Point3D.create(cx, cy, cz)
                            q.transformBy(m)
                            xs2.append(q.x * 10)
                            ys2.append(q.y * 10)
                            zs2.append(q.z * 10)
                p['lo'] = (min(xs2), min(ys2), min(zs2))
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
        # A HIDDEN OCCURRENCE EXPORTS AS AN EMPTY FILE. Lighting the plate
        # itself is not enough - each child occurrence inside it carries its
        # own state, and it inherits whatever the source occurrence had when
        # it was added. Any earlier script that toggled bulbs for a render
        # leaves them off, and the export comes back as a 1.7 KB header.
        pocc.isLightBulbOn = True
        for k in range(pc.occurrences.count):
            pc.occurrences.item(k).isLightBulbOn = True
        lit = sum(1 for k in range(pc.occurrences.count)
                  if pc.occurrences.item(k).isLightBulbOn)
        assert lit == pc.occurrences.count, (
            'plate %d: only %d of %d parts are visible - the export would be '
            'short' % (i + 1, lit, pc.occurrences.count))
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
        needs = sorted(set(p['name'] for p in plate if p['name'] == 'forearm'))
        brims = sorted(set(p['name'] for p in plate if p['pad']))
        print('PLATE %d - %d pieces, %.0f g, tallest %.1f mm, %.0f%% of the bed'
              % (n, len(plate), g, tall,
                 100.0 * used / (BED_X * BED_Y)))
        # PLATE_NOTE describes the FULL build's grouping. On a subset the
        # plates are whatever is left, so the note would be describing a plate
        # that does not exist - it once read 'forearm SUPPORTS' on a plate
        # with no forearm on it.
        if not ONLY:
            print('  %s' % PLATE_NOTE.get(n, ''))
        print('  supports: %s | brim: %s'
              % (', '.join(needs) if needs else 'NONE - leave them off',
                 ', '.join(brims) if brims else 'none'))
        for p in plate:
            if p['h'] >= TALL_MM:
                mid = p['y'] + p['d'] / 2.0
                where = ('back' if mid > 2 * BED_Y / 3 else
                         'front' if mid < BED_Y / 3 else 'middle')
                print('  TALL: %s, %.0f mm, sitting %s (y centre %.0f). It is '
                      'the knock-off risk on this plate.'
                      % (p['name'], p['h'], where, mid))
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
    _sup = sorted(set(p['name'] for pl in plates for p in pl
                      if p['name'] == 'forearm'))
    print('SUPPORTS: %s. OFF everywhere else - on turntable_stator that is'
          % (', '.join(_sup) if _sup else 'NONE on these plates'))
    print('  not a preference, the axle bridge is load-bearing.')
    print('BRIM: base_lid. Budget 5-8 mm of extra footprint for it.')
    print('Orientations are BAKED IN. If you auto-arrange in the slicer, keep')
    print('  rotation locked or gripcut_finger and pruner_rack will flip.')
