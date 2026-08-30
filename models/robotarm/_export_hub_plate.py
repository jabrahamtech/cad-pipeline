"""robotarm/_export_hub_plate - the six hubs, each marked with its joint.

WHAT THE SIX ARE. _preview_arm places them, so this is not a guess:

    J2  +X   shoulder_hub    the driven side - it carries the MG995 disc horn
    J2  -X   wrist_hub
    J3  +X   wrist_hub        elbow, both sides
    J3  -X   wrist_hub
    J4  +X   wrist_hub        wrist pitch, both sides
    J4  -X   wrist_hub

FIVE OF THE SIX ARE THE SAME PART. Only shoulder_hub differs, and it differs
visibly - it has the horn relief and blade slot cut into it. So the marks are
a convenience for sorting a pile on the bench, not a correctness measure: a
J3 hub and a J4 hub are interchangeable and nothing goes wrong if you swap
them. Said plainly here because a stamped part implies a distinction, and
implying one that does not exist is its own kind of error.

WHERE THE MARK GOES, and why there is only one candidate. The hub is a
retaining flange (OD 24 x 2.0), a collar (OD 20 x 5.0) and a hex (15.8 af x
3.8). Working through the surfaces:

  hex flats        the DRIVE surface. Cutting into it removes material from
                   the load path and changes the fit. No.
  collar OD        a journal, it runs inside a bore. No.
  hex top face     an annulus 1-2.5 mm wide - the centre is open bore. No
                   room, and it was the obvious first choice.
  flange underside the seating face, and it is on the bed. No.
  flange top ring  r 10.0..12.0, 2.0 mm wide, faces UP when the part is
                   printed collar-down, and carries no load. This one.

So the text is 1.6 mm on a 2.0 mm ring, engraved 0.4 deep. That is small.
It is legible, and it is the only place on this part that is both free and
prints cleanly.

The source components are NOT modified - the bodies are copied into a base
feature and the text is cut into the copies. Cutting the real parts would
put them out of step with the ledger.
"""

import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
OUT_DIR = os.path.join(REPO, 'exports', 'robotarm', 'plates')
VERSION = 5
COMP = 'robotarm_hub_plate'

FLANGE_TOP_MM = 2.0        # flange 2.0 thick, printed collar-face-down
MARK_R_MM = 11.0           # centre of the r 10..12 ring
MARK_H_MM = 1.6
MARK_DEPTH_MM = 0.4
PITCH_MM = 30.0            # hub OD is 24
PETG, SOLID = 1.27, 0.65

# source part, label, what it is
# LABELS AVOID ENCLOSED COUNTERS. Every profile the explode produces gets
# cut, inner ones included, so a letter with a hole in it (D, 8, a closed 4)
# comes out as a filled silhouette. 2, 3, 4 and H are safe. '2H' is the
# horn-driven hub; the rest are plain.
HUBS = [
    ('shoulder_hub', '2H', 'J2 DRIVEN (+X) - takes the MG995 disc horn'),
    ('wrist_hub', '2', 'J2 idle (-X)'),
    ('wrist_hub', '3', 'J3 elbow (+X)'),
    ('wrist_hub', '3', 'J3 elbow (-X)'),
    ('wrist_hub', '4', 'J4 wrist pitch (+X)'),
    ('wrist_hub', '4', 'J4 wrist pitch (-X)'),
]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    M3 = adsk.core.Matrix3D.create
    P3 = adsk.core.Point3D.create
    V = adsk.core.ValueInput.createByString

    src = {}
    for occ in root.occurrences:
        n = occ.component.name.replace('robotarm_', '')
        if n in ('wrist_hub', 'shoulder_hub') and n not in src:
            src[n] = occ.component.bRepBodies.item(0)
    for want in ('wrist_hub', 'shoulder_hub'):
        assert want in src, '%s is not in this document - build it first' % want

    lo_z = min(src[k].boundingBox.minPoint.z for k in src)
    assert abs(lo_z * 10 + 7.0) < 0.01, (
        'a hub starts at z %.2f, not -7.00 - the flange thickness this file '
        'engraves on is no longer where it thinks' % (lo_z * 10))

    # idempotent
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == COMP or c.name.startswith(COMP + ' ('):
            c.name = COMP + '_stale_' + str(i)
    for o in list(root.occurrences):
        if o.component.name.startswith(COMP + '_stale_'):
            o.deleteMe()
    occ = root.occurrences.addNewComponent(M3())
    occ.component.name = COMP
    comp = occ.component
    assert comp.name == COMP, 'a stale component reserves the name'

    # PARAMETRIC COPIES, not a base feature. The first version built the six
    # hubs as bodies inside a BaseFeature, and every subsequent cut feature
    # ran without removing a thing: features will not modify base-feature
    # bodies this way. Three rounds of chasing the wrong cause - extrude
    # direction, then a stale body handle, then the text profiles - before
    # measuring the geometry proved the placement had been right the whole
    # time and the bodies were the problem.
    #
    # copyPasteBodies gives ordinary parametric bodies, which cut fine.
    placed = []
    for i, (part, label, note) in enumerate(HUBS):
        cx = (i % 3) * PITCH_MM
        cy = (i // 3) * PITCH_MM
        col = adsk.core.ObjectCollection.create()
        col.add(src[part])
        cpb = comp.features.copyPasteBodies.add(col)
        nb = cpb.bodies.item(0)
        nb.name = '%s_%s' % (part, label)
        mv = adsk.core.ObjectCollection.create()
        mv.add(nb)
        m = M3()
        t = m.translation
        t.x, t.y, t.z = cx / 10.0, cy / 10.0, 0.7      # +7 mm: collar face down
        m.translation = t
        mi = comp.features.moveFeatures.createInput2(mv)
        mi.defineAsFreeMove(m)
        comp.features.moveFeatures.add(mi).name = 'place_' + nb.name
        placed.append((nb, cx, cy, part, label, note))

    marked = []
    for nb, cx, cy, part, label, note in placed:
        bb = nb.boundingBox
        assert abs(bb.minPoint.z) < 1e-6, (
            '%s does not sit on the bed (z %.3f)' % (nb.name, bb.minPoint.z * 10))
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'mark_' + nb.name
        ti = sk.sketchTexts.createInput2(label, MARK_H_MM / 10.0)
        ti.setAsMultiLine(
            sk.modelToSketchSpace(P3((cx - 6.0) / 10.0,
                                     (cy + MARK_R_MM - 2.0) / 10.0, 0)),
            sk.modelToSketchSpace(P3((cx + 6.0) / 10.0,
                                     (cy + MARK_R_MM + 2.0) / 10.0, 0)),
            adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
            adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
        st = sk.sketchTexts.add(ti)
        # EXPLODE THE TEXT. A SketchText carries no profiles - the earlier
        # diagnostic said 'profiles 0' on all six sketches - so handing it
        # straight to an extrude produces a feature that runs and cuts
        # nothing. explode() turns it into real curves, which close into
        # profiles the extrude can use.
        st.explode()
        assert sk.profiles.count > 0, (
            'text %r exploded into %d profiles' % (label, sk.profiles.count))
        prof = adsk.core.ObjectCollection.create()
        for k in range(sk.profiles.count):
            prof.add(sk.profiles.item(k))
        ei = comp.features.extrudeFeatures.createInput(
            prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        # START LOW AND CUT UP. The first version started at the flange top
        # and gave setDistanceExtent a NEGATIVE distance, which Fusion took
        # as 0.4 mm UPWARD into thin air: six cut features, six sketches, and
        # not one cubic millimetre removed. The volume came back as exactly
        # the sum of six unmarked hubs, which is the only reason it was
        # caught - so that check is now an assert rather than a coincidence.
        def _total():
            return sum(comp.bRepBodies.item(k).volume
                       for k in range(comp.bRepBodies.count))
        before = _total()
        ei.startExtent = adsk.fusion.OffsetStartDefinition.create(
            V('%.4f mm' % (FLANGE_TOP_MM - MARK_DEPTH_MM)))
        ei.setDistanceExtent(False, V('%.4f mm' % MARK_DEPTH_MM))
        ei.participantBodies = [nb]
        comp.features.extrudeFeatures.add(ei).name = 'mark_' + nb.name
        # measure the COMPONENT, not the body handle: an extrude cut can
        # consume and rebuild the body, leaving the local reference stale and
        # reporting an unchanged volume for a cut that worked.
        dropped = (before - _total()) * 1000
        assert dropped > 0.05, (
            'engraving %r on %s removed %.4f mm3 - the mark is not there. A '
            'cut feature that runs without cutting looks identical to one '
            'that worked.' % (label, nb.name, dropped))
        marked.append((nb.name, label, dropped))

    assert comp.bRepBodies.count == len(HUBS), (
        'expected %d hubs, got %d' % (len(HUBS), comp.bRepBodies.count))
    vol = sum(comp.bRepBodies.item(i).volume * 1000
              for i in range(comp.bRepBodies.count))

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, 'hub_plate_v%d.3mf' % VERSION)
    assert not os.path.exists(path), '%s exists - bump VERSION' % path
    occ.isLightBulbOn = True
    em = design.exportManager
    em.execute(em.createC3MFExportOptions(comp, path))
    size = os.path.getsize(path)
    assert size > 20000, 'exported %d bytes' % size

    print('=== hub plate v%d ===' % VERSION)
    print('%s  (%d bytes)' % (os.path.basename(path), size))
    print('')
    for nb, cx, cy, part, label, note in placed:
        print('  %-2s  %-14s at (%3.0f, %3.0f)   %s' % (label, part, cx, cy, note))
    print('')
    print('%d hubs, %.0f mm3 = %.1f g PETG'
          % (len(placed), vol, vol * PETG * SOLID / 1000.0))
    print('mark: %.1f mm text, %.1f deep, on the flange top ring at r %.1f'
          % (MARK_H_MM, MARK_DEPTH_MM, MARK_R_MM))
    for nm, label, dropped in marked:
        print('   %-2s cut %.3f mm3' % (label, dropped))
    print('PRINT: collar face DOWN (as arranged), no support.')
    print('')
    print('FIVE OF THE SIX ARE THE SAME PART - only 2H differs. A 3 and a 4')
    print('are interchangeable; the marks sort the pile, they do not gate')
    print('anything.')
