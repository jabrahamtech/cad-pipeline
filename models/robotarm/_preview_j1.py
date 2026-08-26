"""robotarm/_preview_j1 - what J1 actually is, exploded and assembled.

"How does the bottom even rotate" is a fair question: in the whole-arm render
the turntable is a black disc under a black bracket and nothing about it reads.
This builds the five-part stack and lays it out so the mechanism is visible.

THE STACK, bottom to top. z = 0 is the printed platter's rim top.

  base_platter   PRINTED, IN HAND. A shallow enclosure, rim top z 42.00 in its
                 own frame. Carries the electronics, a rectangular column at
                 the centre for the yaw servo, and 3 M3 heat-set inserts on
                 Ø8.8 posts at r 45.0, az 120/180/240. That is the ONLY fixing.
  base_lid       PRINTED, IN HAND. Ø171.75 x 3.0, sits on the shelf at z 39.00
                 and finishes flush at 42.00. MEASURED here, not taken from its
                 spec: 3 x Ø9.5 clearance at r 45 for the posts, 12 x Ø4 vents
                 at r 62, 4 x M3 counterbored at r 78. And NO central opening.
  turntable_stator   the fixed half. Base plate r 10..50, three posts rising to
                 z 28.40, and three 608ZZ on RADIAL stub axles at r 27, axle
                 z 12.00. The bearings' tops therefore sit at z 23.00.
  shoulder_bracket   the rotating half. Its underside is a flat annulus from
                 r 23 to r 31 - the RACE FACE - and it simply rests on the
                 three bearings at z 23.00. Nothing else carries the arm.
  turntable_ring     the retainer. Bore 68.35 journals on the rotor's Ø68 boss
                 (0.35 rotating fit) and its underside laps the rotor's Ø76 rim
                 by 3.82 mm with 0.40 of daylight. Three M3 pass through it,
                 through the stator posts, into the platter inserts.

SO THE ROTATION IS: three ball bearings take the weight, one printed journal
takes the side load, and the ring stops it lifting. Three screws hold all of
it down, and the rotor is not screwed to anything - it is trapped.

The SG90 sits in the platter's own column, pointing UP, and its horn blade
lands in a cross pocket in the rotor's underside at z 23.30..24.80. Turning
the horn turns the rotor. Travel is the servo's full 180 deg: the ring hooks
over the rim all the way round, so nothing caps it.
"""

import os
import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
LEGACY = os.path.join(REPO, 'legacy', 'exports', 'robotarm')

# name, z offset to bring it into the stator's frame, explode rank
STACK = [
    ('base_platter', -42.0, 0),
    ('base_lid', -3.0, 1),  # ours, built above
    ('turntable_stator', 0.0, 2),
    ('shoulder_bracket', 70.4, 3),
    ('turntable_ring', 0.0, 4),
]
EXPLODE_MM = 38.0

# Everything in this stack is black in the real arm, and a front-orthographic
# render of five black parts is five black blobs. These appearances exist ONLY
# for the explanatory render - nothing else reads them.
TINT = {
    'base_platter': 'Plastic - Glossy (Gray)',
    'base_lid': 'Plastic - Glossy (White)',
    'turntable_stator': 'Plastic - Glossy (Blue)',
    'shoulder_bracket': 'Plastic - Glossy (Yellow)',
    'turntable_ring': 'Plastic - Glossy (Red)',
}


def _load(name):
    import importlib.util
    import sys
    p = os.path.join(REPO, 'models', 'robotarm', name + '.py')
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def run(_context: str):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    for name in ('shoulder_hub', 'wrist_hub', 'shoulder_bracket',
                 'turntable_stator', 'turntable_ring', 'base_lid'):
        _load(name).run(_context)

    imp = app.importManager
    # base_lid is OURS now - the printed one has no central opening and the
    # SG90 cannot pass it. Only the platter still comes in as a legacy STEP.
    for step in ('base_platter_v1.step',):
        path = os.path.join(LEGACY, step)
        assert os.path.exists(path), 'missing %s' % path
        occ = imp.importToTarget2(imp.createSTEPImportOptions(path), root)
        occ.item(0).component.name = 'legacy_' + step.split('_v1')[0]

    def find(name):
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            if o.component.name in ('robotarm_' + name, 'legacy_' + name):
                return o
        return None

    # tint for legibility
    libs = app.materialLibraries
    for name, want in TINT.items():
        occ = None
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            if o.component.name in ('robotarm_' + name, 'legacy_' + name):
                occ = o
        if occ is None:
            continue
        for li in range(libs.count):
            # itemByName THROWS on a name that is not there, it does not return
            # None. Every appearance name in this table is a guess at Fusion's
            # library, so ask forgiveness.
            try:
                ap = libs.item(li).appearances.itemByName(want)
            except Exception:
                ap = None
            if ap is None:
                continue
            print('  tint %-18s -> %s' % (name, want))
            for bi in range(occ.component.bRepBodies.count):
                occ.component.bRepBodies.item(bi).appearance = ap
            break

    for exploded in (False, True):
        for name, dz, rank in STACK:
            occ = find(name)
            if occ is None:
                print('  MISSING %s' % name)
                continue
            m = adsk.core.Matrix3D.create()
            lift = dz + (rank * EXPLODE_MM if exploded else 0.0)
            m.translation = adsk.core.Vector3D.create(0, 0, lift / 10.0)
            occ.transform2 = m
        des.snapshots.add() if des.snapshots.hasPendingSnapshot else None

        vp = app.activeViewport
        cam = vp.camera
        cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
        cam.isFitView = True
        vp.camera = cam
        vp.refresh()
        adsk.doEvents()
        out = os.path.join(REPO, 'docs', 'robotarm',
                           'j1_%s.png' % ('exploded' if exploded else 'assembled'))
        vp.saveAsImageFile(out, 1800, 1400)
        print('wrote %s' % out)

    print('')
    print('J1 STACK, z = platter rim top:')
    for name, dz, rank in STACK:
        occ = find(name)
        if occ is None or not occ.component.bRepBodies.count:
            continue
        bb = occ.component.bRepBodies.item(0).boundingBox
        print('  %-20s z %7.2f .. %7.2f' % (name, bb.minPoint.z * 10 + dz,
                                            bb.maxPoint.z * 10 + dz))
