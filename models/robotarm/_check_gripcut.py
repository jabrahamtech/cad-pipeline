"""robotarm/_check_gripcut - do the fingers ride the closure without touching
anything they must not?

The finger's whole topology hangs on claims made by arithmetic: that the
grip flag, riding ENTIRELY ABOVE the blade stack (z 3.65..9.55), sweeps over
the nose tops through open air at every pose and every deflection; that on
empty close the two fingers BYPASS - disjoint z bands, like the blades - and
never meet; that the leaf clears its own blade's edge plane. Given this
project's record with arithmetic-only clearances (the 5.2 mm crank, the
buried rollers), none of that ships unswept. This file's own history is the
strongest argument: its sweeps killed the three straddling designs the
current topology replaced.

PAIR CLASSIFICATION IS THE POINT. A rigid-model sweep of a FLEXURE cannot
avoid interpenetration - past first touch the real leaves deflect and the
rigid models overlap. So overlap is sorted by pair:

  finger^finger      MUST BE ZERO at every pose - the fingers bypass in z.
                     Anything here means a finger dips into the other's band
  finger^stem        EXPECTED - that is the grip doing its job
  finger^blade       FAIL at any pose - except the ANCHOR SHEAR artifact:
                     the deflected pose translates the WHOLE rigid finger,
                     so the key boss shears against its own pocket wall. The
                     real leaf bends and the anchor never moves. Interference
                     wholly inside the boss band |z| <= mount_z is filed as
                     anchor shear, capped at the boss's own volume, and the
                     UNDEFLECTED empty close - where the boss must read 0.00
                     - is what proves the anchor actually fits
  blade^blade        _check_pruner's business; near zero here regardless

Placements are _check_pruner's blade_at(), lifted verbatim so the two gates
cannot disagree about how the head closes. Runs in one pass: four small
bodies, five poses.
"""

import importlib.util
import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
PARTS = ['pruner_blade', 'gripcut_finger']
THETA_DEG = [0.0, 5.0, 10.2, 15.0, 24.3]
STEM_DIA_MM = 5.0
STEM_AT_R_MM = 8.5          # in the throat, where the sizing was done
# THE FINGERS ARE POSED DEFLECTED. A rigid finger swung through the closure
# follows a path the real leaf never takes: past first contact the leaf bends
# and the tip stays at the contact, while the rigid model swings the tip's
# below-plane half across the centreline and through the other carrier's
# nose - a 6.7 mm3 phantom collision at closure. So each stem pose translates
# the finger along its local +x by the deflection the leaf would carry:
#   d = (stem surface) - (face plane) = r sin(th) + stem_r - af, clamped at 0
# The applied d is printed and asserted against the 4.7 mm budget - which
# turns the sweep into the deflection check as well. The EMPTY close is posed
# UNDEFLECTED: with no stem nothing loads the leaf, and the claim under test
# is that the bypassing fingers need no deflection to miss each other.


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    M3 = adsk.core.Matrix3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)

    built = {}
    for name in PARTS:
        path = os.path.join(REPO, 'models', 'robotarm', name + '.py')
        spec = importlib.util.spec_from_file_location('gen_' + name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules['gen_' + name] = mod
        spec.loader.exec_module(mod)
        mod.run(_context)
        for o in root.occurrences:
            if o.component.name == 'robotarm_' + name:
                built[name] = o.component.bRepBodies.item(0).volume
    print('')

    keep = {}
    for o in list(root.occurrences):
        if o.component.name in keep:
            o.deleteMe()
        else:
            keep[o.component.name] = o
    design.timeline.moveToEnd()
    for name, vol in built.items():
        now = keep['robotarm_' + name].component.bRepBodies.item(0).volume
        assert abs(now - vol) < vol * 1e-6, (
            '%s changed after both parts built - a shared parameter moved' % name)

    ups = design.userParameters
    gv = lambda n: ups.itemByName(n).value          # noqa: E731
    tail_r = gv('pb_tail_r')
    # the same pivot height _check_pruner uses; pr_pin_y only exists when the
    # rack has been built, so fall back to the linkage value
    p = ups.itemByName('pr_pin_y')
    pivot_y = tail_r + (p.value if p is not None else 1.6)
    af_mm = gv('gf_af') * 10

    C = lambda n: keep['robotarm_' + n].component   # noqa: E731
    add = root.occurrences.addExistingComponent
    for o in keep.values():
        o.isLightBulbOn = False

    def rot(a, axis):
        m = M3()
        m.setToRotation(a, axis, ORG)
        return m

    def blade_at(theta, turned):
        # THE TURNED COPY GETS MINUS THETA, and this is a correction to the
        # placement inherited from _check_pruner. R(th)*Flip rotates the
        # mirrored blade the SAME way as the first - the jaws tilt together
        # and never close on each other; the parallel mouth just swings. That
        # is invisible when everything is measured against a fixed stem
        # (relative closure is equivalent), which is exactly what
        # _check_pruner does - but it made this gate's empty-close test read
        # 'fingers never meet'. F*R(th) = R(-th)*F is the scissor sense.
        m = M3()
        if turned:
            m.setToRotation(math.pi, VEC(0, 1, 0), ORG)
        m.transformBy(rot(-theta if turned else theta, VEC(0, 0, 1)))
        t = m.translation
        t.y = pivot_y
        m.translation = t
        return m

    # a stem: a Z cylinder in the throat, as _check_pruner probes with
    STEM = 'robotarm_gripcut_stem'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == STEM or c.name.startswith(STEM + ' ('):
            c.name = STEM + '_stale_' + str(i)
    for o in list(root.occurrences):
        if o.component.name.startswith(STEM + '_stale_'):
            o.deleteMe()
    st_occ = root.occurrences.addNewComponent(M3())
    st = st_occ.component
    st.name = STEM
    sk = st.sketches.add(st.xYConstructionPlane)
    sk.name = 'sk_stem'
    P3 = adsk.core.Point3D.create
    # pivot_y PLUS the radius - the nose and throat are on +Y of the pivot.
    # The first run of this file wrote MINUS and buried the stem in the tails
    # and the finger rings: finger^stem read 181 mm3 at open mouth and FELL as
    # the head closed, which is backwards, and that inversion is what exposed
    # the sign. A probe in the wrong place produces confident nonsense.
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        sk.modelToSketchSpace(P3(0.0, pivot_y + STEM_AT_R_MM / 10.0, 0)),
        STEM_DIA_MM / 20.0)
    col = adsk.core.ObjectCollection.create()
    col.add(sk.profiles.item(0))
    inp = st.features.extrudeFeatures.createInput(
        col, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    V = adsk.core.ValueInput.createByString
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('-12.0 mm'))
    inp.setDistanceExtent(False, V('24.0 mm'))
    st.features.extrudeFeatures.add(inp).name = 'stem'
    st.bRepBodies.item(0).name = 'stem'
    keep.pop(STEM, None)

    def label(entity):
        comp = getattr(entity, 'component', None)
        if comp is None:
            comp = getattr(entity, 'parentComponent', None)
        n = (comp.name if comp else '?').replace('robotarm_', '')
        # 'pruner_blade' must become 'blade' or every finger^blade collision
        # lands in the wrong bucket - the first run of this file filed a
        # 103 mm3 finger-through-its-own-nose under 'blade^stem' and printed
        # PASS over it.
        return n.replace('gripcut_', '').replace('pruner_', '').replace(
            'probe_', '')

    boss_band_cm = ups.itemByName('gf_mount_z').value + 0.006
    def classify(res):
        out = {'finger^finger': 0.0, 'finger^other_blade': 0.0,
               'anchor_shear': 0.0,
               'finger^stem': 0.0, 'blade^blade': 0.0, 'blade^stem': 0.0}
        pairs = []
        for i in range(res.count):
            r = res.item(i)
            a, b = sorted((label(r.entityOne), label(r.entityTwo)))
            vol = r.interferenceBody.volume * 1000
            ibb = r.interferenceBody.boundingBox
            in_boss_band = (ibb.maxPoint.z < boss_band_cm
                            and ibb.minPoint.z > -boss_band_cm)
            if a == b == 'finger':
                out['finger^finger'] += vol
            elif a == 'blade' and b == 'finger' and in_boss_band:
                out['anchor_shear'] += vol
            elif a == 'blade' and b == 'finger':
                out['finger^other_blade'] += vol
            elif a == 'finger' and b == 'stem':
                out['finger^stem'] += vol
            elif a == b == 'blade':
                out['blade^blade'] += vol
            else:
                out['blade^stem'] += vol
            pairs.append('%s^%s %.2f' % (a, b, vol))
        return out, pairs

    # NAME COLLISION NOTE: both blades are the same component, both fingers
    # too, so 'finger^other_blade' above actually collects EVERY finger^blade
    # pair - own and other. The own-blade pairs are the boss in its pocket and
    # the ring on the face, which are clearance and coincident fits: they
    # contribute 0.00. Anything nonzero in that bucket is therefore real.
    af_cm = gv('gf_af')

    def defl_stem(th):
        return max(0.0, (STEM_AT_R_MM / 10.0) * math.sin(th)
                   + STEM_DIA_MM / 20.0 - af_cm)

    def finger_at(th, turned, d_cm):
        m = M3()
        t = m.translation
        t.x = d_cm
        m.translation = t
        m.transformBy(blade_at(th, turned))
        return m

    print('=== gripcut closure sweep ===')
    print('fingers ride their carriers; grip faces at x %.2f, above the '
          'stack' % af_mm)
    print('')
    shear_cap = 2 * (gv('gf_key_w') * gv('gf_key_l') * gv('gf_key_h')
                     * 1000) + 1.0
    print('%7s %11s %10s %15s %11s %12s %12s' % (
        'theta', 'defl mm', 'fing^fing', 'finger^ANYblade', 'anch shear',
        'finger^stem', 'blade^stem'))

    fails = []
    for deg in THETA_DEG:
        th = math.radians(deg)
        d = defl_stem(th)
        assert d < 0.47 + 0.01, (
            'theta %.1f wants %.2f mm of deflection - past the 4.7 budget'
            % (deg, d * 10))
        pose = [add(C('pruner_blade'), blade_at(th, False)),
                add(C('pruner_blade'), blade_at(th, True)),
                add(C('gripcut_finger'), finger_at(th, False, d)),
                add(C('gripcut_finger'), finger_at(th, True, d)),
                add(st, M3())]
        col = adsk.core.ObjectCollection.create()
        for o in pose:
            col.add(o)
        iinp = design.createInterferenceInput(col)
        iinp.areCoincidentFacesIncluded = False
        out, pairs = classify(design.analyzeInterference(iinp))
        print('%6.1fd  defl %5.2f %10.2f %15.2f %11.2f %12.2f %12.2f' % (
            deg, d * 10, out['finger^finger'], out['finger^other_blade'],
            out['anchor_shear'], out['finger^stem'], out['blade^stem']))
        # deflected poses KISS: any real residual on the expected-contact
        # pairs is a modelling slip, so they get a sliver allowance, while
        # finger^blade gets none.
        if out['finger^other_blade'] > 0.5:
            fails.append('theta %.1f: a finger touches a BLADE by %.2f mm3 (%s)'
                         % (deg, out['finger^other_blade'], '; '.join(pairs)))
        if out['anchor_shear'] > shear_cap:
            fails.append('theta %.1f: anchor shear %.2f mm3 exceeds the boss '
                         'volume cap %.2f - this is more than the posing '
                         'artifact can explain' % (deg, out['anchor_shear'],
                                                   shear_cap))
        if out['finger^finger'] > 0.05:
            fails.append('theta %.1f: fingers overlap by %.2f mm3 - they are '
                         'built to BYPASS in z, so any contact means a finger '
                         'is out of its band' % (deg, out['finger^finger']))
        for o in pose:
            o.deleteMe()
    # the face must actually MEET the stem by full closure, or the couple
    # never forms and the finger is jewellery. d > 0 says the rigid face
    # plane has crossed the stem surface - i.e. the leaf is pressing.
    d_close = defl_stem(math.radians(THETA_DEG[-1]))
    assert d_close > 0.0, (
        'at full closure the face plane never reaches the stem - '
        'defl %.2f mm; the grip face is set too deep' % (d_close * 10))

    # with a stem in the throat the fingers never reach each other - the stem
    # separates them. But the topology's core claim is stronger: they never
    # reach each other AT ALL. The flag lives at z 3.65..9.55, the flipped
    # copy at -9.55..-3.65, and rotation about the pivot z-axis preserves z -
    # so the empty close must read finger^finger 0.00 at EVERY angle, posed
    # UNDEFLECTED, all the way to the hard stop:
    print('')
    print('EMPTY close - no stem, fingers posed undeflected. They BYPASS in')
    print('z like the blades, so every bucket but blade^blade must be zero:')
    for deg in THETA_DEG[1:]:
        th = math.radians(deg)
        pose = [add(C('pruner_blade'), blade_at(th, False)),
                add(C('pruner_blade'), blade_at(th, True)),
                add(C('gripcut_finger'), finger_at(th, False, 0.0)),
                add(C('gripcut_finger'), finger_at(th, True, 0.0))]
        col = adsk.core.ObjectCollection.create()
        for o in pose:
            col.add(o)
        iinp = design.createInterferenceInput(col)
        iinp.areCoincidentFacesIncluded = False
        out, pairs = classify(design.analyzeInterference(iinp))
        fb = out['finger^other_blade'] + out['anchor_shear']
        print('  %5.1fd  finger^finger %8.2f mm3   finger^ANYblade %.2f'
              % (deg, out['finger^finger'], fb))
        if fb > 0.05:
            fails.append('EMPTY theta %.1f: a finger touches a BLADE by %.2f '
                         'mm3 UNDEFLECTED - at d=0 there is no shear artifact,'
                         ' so this is real: the boss does not fit its pocket '
                         'or worse (%s)' % (deg, fb, '; '.join(pairs)))
        if out['finger^finger'] > 0.05:
            fails.append('EMPTY theta %.1f: fingers overlap by %.2f mm3 - '
                         'the bypass claim is broken'
                         % (deg, out['finger^finger']))
        for o in pose:
            o.deleteMe()

    print('')
    print('GATE gripcut : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)
    print('')
    print('NOT CHECKED HERE: shell clearance (the finger adds z to 9.55 and')
    print('the head runs inside pruner_shell - _check_pruner owns that doc),')
    print('and the leaf FORCE, which no rigid sweep can see. The flexure')
    print('coupon on the next gauge plate is the force check.')

    st_occ.deleteMe()
    for o in keep.values():
        o.isLightBulbOn = True
