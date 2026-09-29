"""robotarm/_export_cobot - the cobot arm's printed parts, oriented and packed onto X2D plates.

Run AFTER every cobot_* part script has built into the active document.

ONE 3MF PER PLATE (Fusion writes single-plate 3MFs). Every part is turned to
the PRINT ORIENTATION its own docstring states (the table below quotes each),
shelf-packed onto the Bambu X2D's dual-nozzle area (235.5 x 256, _export_plates
BED_X/BED_Y), and then CHECKED: every placed body is re-measured in Fusion for
lying inside the plate and sitting on z = 0, and every footprint against every
other for overlap. Nothing here is trusted because it looks right.

Out: exports/robotarm/cobot/cobot_plate_<n>.3mf and a manifest printed at the end.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

OUT_DIR = os.path.join(REPO, 'exports', 'robotarm', 'cobot')
BED_X, BED_Y, BED_H = 235.5, 256.0, 260.0
MARGIN, GAP = 6.0, 5.0
EPS_MM = 0.01
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0

# component, qty, rotation (axis, deg) putting the print face DOWN, the part's own words
ORIENT = [
    ('robotarm_cobot_tower', 1, None, 'race face down, no support'),
    ('robotarm_cobot_upper_arm', 1, ('y', -90), 'joint wall down'),
    ('robotarm_cobot_upper_arm_cover', 1, ('y', 90), 'outer face down, lip up'),
    ('robotarm_cobot_forearm', 1, ('y', -90), 'joint wall down'),
    ('robotarm_cobot_forearm_plate', 1, ('y', -90), 'inner face down, spigot up'),
    ('robotarm_cobot_j2_plate', 1, ('y', -90), 'flat, board pocket up'),
    ('robotarm_cobot_j3_plate', 1, ('y', -90), 'flat, board pocket up'),
    ('robotarm_cobot_j4_plate', 1, ('y', -90), 'flat, standoffs up'),
    ('robotarm_cobot_wrist', 1, ('y', -90), 'outer face down, pockets up'),
    ('robotarm_cobot_wrist_cap', 1, ('y', -90), 'split face down, spigot up'),
    ('robotarm_cobot_j2_gear', 1, None, 'flange down'),
    ('robotarm_cobot_j3_gear', 1, None, 'flange down'),
    ('robotarm_cobot_j4_gear', 1, None, 'flange down'),
    ('robotarm_cobot_j2_pinion', 1, None, 'front face down, broach up'),
    ('robotarm_cobot_j3_pinion', 1, None, 'front face down, broach up'),
    ('robotarm_cobot_j4_pinion', 1, None, 'front face down, broach up'),
    ('robotarm_cobot_j3_idler', 1, ('x', 180), '36T face down'),
    ('robotarm_cobot_rotator', 1, ('x', 180), 'front face down, broach up'),
    ('robotarm_grip_body', 1, ('x', 90), 'back face down, cup up (grip v4)'),
    ('robotarm_grip_jaw', 2, ('x', 180), 'bar top down (grip v4)'),
    ('robotarm_gripper_pinion', 1, None, 'flat (grip v4)'),
    ('robotarm_grip_finger', 2, None, 'TPU 95A, flat, 20-25 mm/s'),
]
TPU = {'robotarm_grip_finger'}     # its own plate: another material


def rot3(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    if axis == 'x':
        return [[1, 0, 0], [0, c, -s], [0, s, c]]
    if axis == 'y':
        return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def apply3(m, v):
    return [sum(m[r][k] * v[k] for k in range(3)) for r in range(3)]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    V3 = adsk.core.Vector3D.create

    comps = {o.component.name: o.component for o in root.occurrences}
    items = []
    for name, qty, rot, why in ORIENT:
        assert name in comps, 'build %s first' % name
        comp = comps[name]
        assert comp.bRepBodies.count == 1, name
        lin = rot3(*rot) if rot else [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        bb = comp.bRepBodies.item(0).boundingBox
        pts = [apply3(lin, [x * 10, y * 10, z * 10]) for x in (bb.minPoint.x, bb.maxPoint.x)
               for y in (bb.minPoint.y, bb.maxPoint.y) for z in (bb.minPoint.z, bb.maxPoint.z)]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        w, d, h = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
        if w < d and d <= BED_X - 2 * MARGIN:           # lie the long side along x where it fits
            rz = rot3('z', 90)
            lin = [[sum(rz[r][k] * lin[k][c] for k in range(3)) for c in range(3)] for r in range(3)]
            pts = [apply3(lin, [x * 10, y * 10, z * 10]) for x in (bb.minPoint.x, bb.maxPoint.x)
                   for y in (bb.minPoint.y, bb.maxPoint.y) for z in (bb.minPoint.z, bb.maxPoint.z)]
            lo = [min(p[i] for p in pts) for i in range(3)]
            hi = [max(p[i] for p in pts) for i in range(3)]
            w, d, h = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
        assert h <= BED_H and w <= BED_X - 2 * MARGIN and d <= BED_Y - 2 * MARGIN, '%s does not fit the X2D' % name
        for _ in range(qty):
            items.append({'name': name, 'comp': comp, 'lin': lin, 'lo': lo, 'w': w, 'd': d, 'h': h, 'why': why,
                          'vol': comp.bRepBodies.item(0).volume * 1000})

    # ---- shelf packing, largest first, one material per plate ------------------------
    plates = []
    for group in ([it for it in items if it['name'] not in TPU], [it for it in items if it['name'] in TPU]):
        if not group:
            continue
        group.sort(key=lambda it: (-it['d'], -it['w']))
        plates.append([])
        x = y = MARGIN
        shelf = 0.0
        for it in group:
            if x + it['w'] > BED_X - MARGIN:
                x, y, shelf = MARGIN, y + shelf + GAP, 0.0
            if y + it['d'] > BED_Y - MARGIN:
                plates.append([])
                x = y = MARGIN
                shelf = 0.0
            it['at'] = (x, y)
            plates[-1].append(it)
            x += it['w'] + GAP
            shelf = max(shelf, it['d'])

    # ---- check the packing -----------------------------------------------------------
    for pl in plates:
        for i, a in enumerate(pl):
            ax, ay = a['at']
            assert ax >= MARGIN - EPS_MM and ay >= MARGIN - EPS_MM
            assert ax + a['w'] <= BED_X - MARGIN + EPS_MM and ay + a['d'] <= BED_Y - MARGIN + EPS_MM, a['name']
            for b in pl[i + 1:]:
                bx, by = b['at']
                sep = (ax + a['w'] + GAP - EPS_MM <= bx or bx + b['w'] + GAP - EPS_MM <= ax or
                       ay + a['d'] + GAP - EPS_MM <= by or by + b['d'] + GAP - EPS_MM <= ay)
                assert sep, '%s overlaps %s' % (a['name'], b['name'])

    # ---- place, re-measure, export ----------------------------------------------------
    os.makedirs(OUT_DIR, exist_ok=True)
    for k, pl in enumerate(plates):
        for o in list(root.occurrences):
            if o.component.name == 'cobot_plate_%d' % k:
                o.deleteMe()
        po = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        pc = po.component
        pc.name = 'cobot_plate_%d' % k
        grams = 0.0
        for it in pl:
            m = adsk.core.Matrix3D.create()
            for r in range(3):
                for c in range(3):
                    m.setCell(r, c, it['lin'][r][c])
            m.translation = V3((it['at'][0] - it['lo'][0]) / 10, (it['at'][1] - it['lo'][1]) / 10, -it['lo'][2] / 10)
            occ = pc.occurrences.addExistingComponent(it['comp'], m)
            bb = occ.bRepBodies.item(0).boundingBox
            assert abs(bb.minPoint.z * 10) < EPS_MM * 10, '%s is not on the bed (z %.3f)' % (it['name'], bb.minPoint.z * 10)
            assert bb.minPoint.x * 10 >= MARGIN - EPS_MM * 10 and bb.maxPoint.x * 10 <= BED_X - MARGIN + EPS_MM * 10
            assert bb.minPoint.y * 10 >= MARGIN - EPS_MM * 10 and bb.maxPoint.y * 10 <= BED_Y - MARGIN + EPS_MM * 10
            grams += it['vol'] * PETG_G_PER_MM3
        mat = 'tpu' if pl[0]['name'] in TPU else 'petg'
        path = os.path.join(OUT_DIR, 'cobot_plate_%d_%s.3mf' % (k + 1, mat))
        em = design.exportManager
        em.execute(em.createC3MFExportOptions(pc, path))
        print('PLATE %d  ~%.0f g  %s' % (k + 1, grams, path))
        for it in pl:
            print('   %-32s %6.1f x %6.1f x %5.1f  %s' % (it['name'].replace('robotarm_', ''), it['w'], it['d'], it['h'],
                                                        it['why']))
        po.isLightBulbOn = False
    print('%d parts on %d plates; ~%.0f g PETG in all' % (len(items), len(plates),
                                                          sum(it['vol'] for it in items) * PETG_G_PER_MM3))
