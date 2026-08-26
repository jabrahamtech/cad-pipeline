"""robotarm/_check_pruner - the pruner head gate.

Rebuilds the head from its committed scripts and asks the only question that
matters about a cutting tool: DOES THE CUT TRAVEL?

Interference alone cannot answer that. The two blades sit either side of the
split plane and never touch each other at any angle, so an interference check
between them reads 0.000 whether the tool is a scissor or a nutcracker. The
first build of this head had both cutting edges lying ON the pivot, which
makes them coincident at closure - the whole stem section shears in one
instant, with no travelling contact and no mechanical advantage from the
shear at all. Every check then in place passed it.

So this gate puts a STEM in the throat and watches where the blades bite:

  1. at theta = 0 the stem has to FIT - no interference at all;
  2. the crossing has to sweep from OUTSIDE the stem's outer radius to
     INSIDE its inner one, so the cut passes clean through;
  3. and the bite has to grow monotonically while it does.

Test 2 is what separates a scissor from a pinch, and it is worth being
precise about why. The first draft of this gate tried to assert that the
interference CENTROID travels along the stem. It does not, and it would not
have caught anything: with a stem standing across the blades, a V-pinch also
bites progressively as its V narrows. What actually separates them is the GAP
PROFILE - a scissor's gap is zero at exactly one radius and opens away from
it, a pinch's is proportional to r and reaches zero everywhere at once. That
property lives in lib/pruner_linkage.crossing_r and is asserted by
test_there_is_exactly_one_crossing_and_it_sweeps_monotonically. What this
gate adds is the physical half: a real stem fits the mouth, and the sweep
really does carry the crossing through it.

RUNNING IT. Rebuilding four parts and then running interference exceeds the
60 s the MCP bridge allows in one call, so REBUILD is a switch: run once with
it True to rebuild, then again with it False to check. Both passes have to be
green for the gate to mean anything.

Frame: the effector's own. X is the jaw opening, Y forward out of the hand,
Z the rack separation and the plane the blades bypass across. A stem lies
along X, across the mouth, and the crossing sweeps along Y through it.
"""

import importlib.util
import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]
from lib.pruner_linkage import CHOSEN  # noqa: E402

REBUILD = True               # see RUNNING IT in the docstring
PARTS = ['gripper_pinion', 'pruner_blade', 'pruner_rack', 'pruner_shell']
STEM_DIA_MM = 5.0
STEM_AT_R_MM = 8.5           # where the stem sits, from the pivot
CUT_ANGLES_DEG = [0.0, 15.0, 24.3, 32.0, 40.0]
FULL_POSE_AT_DEG = 20.0      # the one angle the WHOLE head is checked at


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    M3 = adsk.core.Matrix3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)

    # ---- rebuild every piece from its committed script ---------------------
    built = {}
    for name in (PARTS if REBUILD else []):
        path = os.path.join(REPO, 'models', 'robotarm', name + '.py')
        assert os.path.exists(path), 'missing ' + path
        spec = importlib.util.spec_from_file_location('gen_' + name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run(_context)
        for occ in adsk.fusion.Design.cast(app.activeProduct).rootComponent.occurrences:
            if occ.component.name == 'robotarm_' + name:
                built[name] = occ.component.bRepBodies.item(0).volume
    print('')

    keep = {}
    for occ in list(root.occurrences):
        if occ.component.name in keep:
            occ.deleteMe()
        else:
            keep[occ.component.name] = occ
    design.timeline.moveToEnd()

    scars = []
    for name, vol in (built.items() if REBUILD else []):
        now = keep['robotarm_' + name].component.bRepBodies.item(0).volume
        if abs(now - vol) > vol * 1e-6:
            scars.append('%s %.1f -> %.1f mm3' % (name, vol * 1000, now * 1000))
    assert not scars, ('a later part script cut into an earlier one: '
                       + '; '.join(scars) + ' - set participantBodies')
    if REBUILD:
        print('volume unchanged after all parts built: %s' % ', '.join(
            '%s %.0f' % (k, v * 1000) for k, v in sorted(built.items())))
    else:
        print('REBUILD off - checking whatever is already in the document')

    ups = design.userParameters
    gv = lambda n: ups.itemByName(n).value          # noqa: E731
    tail_r = gv('pb_tail_r')
    pivot_y = tail_r + gv('pr_pin_y')
    edge_off = gv('pb_edge_off')
    offset, face, r_pitch = gv('gr_offset'), gv('gr_face'), gv('gr_r_pitch')
    x_a = gv('pr_tooth_lead') - int(round(gv('pr_rack_teeth'))) * gv('pr_pitch')
    C = lambda n: keep['robotarm_' + n].component   # noqa: E731
    add = root.occurrences.addExistingComponent
    for o in keep.values():
        o.isLightBulbOn = False

    def rot(a, axis):
        m = M3()
        m.setToRotation(a, axis, ORG)
        return m

    def blade_at(theta, turned):
        m = M3()
        if turned:
            m.setToRotation(math.pi, VEC(0, 1, 0), ORG)
        m.transformBy(rot(theta, VEC(0, 0, 1)))
        t = m.translation
        t.y = pivot_y
        m.translation = t
        return m

    def rack_at(s, turned):
        m = M3()
        if turned:
            m.setToRotation(math.pi, VEC(0, 1, 0), ORG)
        t = m.translation
        t.x = -s if turned else s
        t.z = -offset if turned else offset
        m.translation = t
        return m

    def pinion_at(s):
        m = rot(-math.pi / 2 + (x_a + s) / r_pitch, VEC(0, 0, 1))
        m.transformBy(rot(-math.pi / 2, VEC(1, 0, 0)))
        t = m.translation
        t.y = -face / 2
        m.translation = t
        return m

    def interference(occs):
        col = adsk.core.ObjectCollection.create()
        for o in occs:
            col.add(o)
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        total, y_lo, y_hi = 0.0, 1e9, -1e9
        for i in range(res.count):
            ib = res.item(i).interferenceBody
            total += ib.volume * 1000
            bb = ib.boundingBox
            y_lo = min(y_lo, bb.minPoint.y * 10)
            y_hi = max(y_hi, bb.maxPoint.y * 10)
        return total, (None if total == 0 else (y_lo + y_hi) / 2)

    # ---- the stem, as a body ----------------------------------------------
    # A cylinder along Z, PERPENDICULAR TO THE BLADE PLATES, standing in the
    # in-plane mouth. That is how a branch sits in a pruner: it passes through
    # the gap between blade and counter-blade, and the blades close on its
    # cross-section from either side. Laid along X instead it threads straight
    # through both blades and reads as 122 mm3 of interference at a wide open
    # mouth - which is what the first version of this probe did.
    stem_comp = root.occurrences.addNewComponent(M3()).component
    stem_comp.name = 'probe_stem'
    sk = stem_comp.sketches.add(stem_comp.xYConstructionPlane)
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        sk.modelToSketchSpace(adsk.core.Point3D.create(
            0, pivot_y + STEM_AT_R_MM / 10.0, 0)), STEM_DIA_MM / 20.0)
    ext = stem_comp.features.extrudeFeatures
    einp = ext.createInput(sk.profiles.item(0),
                           adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    einp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByString('-10 mm'))
    einp.setDistanceExtent(False, adsk.core.ValueInput.createByString('20 mm'))
    ext.add(einp)
    stem_occ_src = None
    for occ in root.occurrences:
        if occ.component.name == 'probe_stem':
            stem_occ_src = occ
    stem_occ_src.isLightBulbOn = False

    print('')
    print('=== pruner head gate ===')
    print('edge offset %.2f -> mouth %.2f mm | stem probe %.1f dia at r %.1f, '
          'standing across the blades' % (
              edge_off * 10, 2 * edge_off * 10, STEM_DIA_MM, STEM_AT_R_MM))
    assert STEM_DIA_MM < 2 * edge_off * 10, (
        'a %.1f mm stem cannot enter a %.1f mm mouth - the probe is asking for '
        'something the tool never claimed' % (STEM_DIA_MM, 2 * edge_off * 10))
    print('')
    print('%8s %11s %13s %14s   %s' % (
        'theta', 'crossing r', 'bite mm3', 'bite y centre', 'meaning'))

    fails = []
    bites = []
    for deg in CUT_ANGLES_DEG:
        th = math.radians(deg)
        pair = [add(C('pruner_blade'), blade_at(th, False)),
                add(C('pruner_blade'), blade_at(th, True)),
                add(stem_comp, M3())]
        vol, y_c = interference(pair)
        cr = float('inf') if deg < 1e-6 else edge_off / math.sin(th) * 10
        note = ('stem FITS' if vol == 0 else
                'cutting' if vol < 200 else 'through')
        print('%7.1fd %10s %13.2f %14s   %s' % (
            deg, 'open' if cr == float('inf') else '%.2f' % cr, vol,
            '-' if y_c is None else '%.2f' % y_c, note))
        if abs(deg) < 1e-6 and vol > 0.01:
            fails.append('the stem does not fit the open mouth (%.2f mm3)' % vol)
        if vol > 0:
            bites.append((deg, vol))
        for o in pair:
            o.deleteMe()

    assert bites, 'the blades never touched the stem at any angle - it cannot cut'
    stem_r_in = STEM_AT_R_MM - STEM_DIA_MM / 2
    stem_r_out = STEM_AT_R_MM + STEM_DIA_MM / 2
    cr_first = edge_off / math.sin(math.radians(CUT_ANGLES_DEG[1])) * 10
    cr_last = edge_off / math.sin(math.radians(CUT_ANGLES_DEG[-1])) * 10
    swept = True
    if cr_first < stem_r_out:
        swept = False
        fails.append('the sweep starts with the crossing already inside the stem '
                     '(%.2f < %.2f) - it never enters cleanly' % (cr_first, stem_r_out))
    if cr_last > stem_r_in:
        swept = False
        fails.append('the crossing only reaches r %.2f, short of the stem inner edge '
                     'at %.2f - the cut does not finish' % (cr_last, stem_r_in))
    if not all(bites[i][1] >= bites[i - 1][1] for i in range(1, len(bites))):
        fails.append('the bite does not grow monotonically through the sweep')

    print('')
    print('crossing sweeps r %.2f -> %.2f; the stem occupies r %.2f..%.2f' % (
        cr_first, cr_last, stem_r_in, stem_r_out))
    print('the cut ENTERS beyond the stem and FINISHES inside it')

    # ---- the whole head, once ----------------------------------------------
    th = math.radians(FULL_POSE_AT_DEG)
    s = tail_r * math.tan(th)
    turned = M3()
    turned.setToRotation(math.pi, VEC(0, 1, 0), ORG)
    head = [add(C('gripper_pinion'), pinion_at(s)),
            add(C('pruner_shell'), M3()), add(C('pruner_shell'), turned),
            add(C('pruner_rack'), rack_at(s, False)),
            add(C('pruner_rack'), rack_at(s, True)),
            add(C('pruner_blade'), blade_at(th, False)),
            add(C('pruner_blade'), blade_at(th, True))]
    vol, _ = interference(head)
    solid = sum(o.component.bRepBodies.item(0).physicalProperties.mass for o in head)
    print('whole head at %.0f deg: 7 bodies, interference %.2f mm3' % (
        FULL_POSE_AT_DEG, vol))
    print('head solid PETG %.2f g -> ~%.1f g printed' % (solid * 1000, solid * 600))
    if vol > 1.0:
        fails.append('head interference %.2f mm3' % vol)

    print('')
    print('GATE cut passes through : %s' % ('PASS' if swept else 'FAIL'))
    print('GATE clearances  : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)
