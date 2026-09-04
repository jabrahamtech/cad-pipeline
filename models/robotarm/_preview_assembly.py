"""robotarm/_preview_assembly - render the arm going together, one step at a time.

Spec: specs/robotarm/_assembly.md. Driver, not a part.

Jonathan, 2026-09-04: "can you generate a set of photos putting it together".
There are no photos - nothing is built yet - so this renders the NEXT BEST
THING: the real geometry, from the real posed assembly, revealed one build
step at a time.

HOW IT IS POSED, AND WHY IT IS NOT POSED HERE. _preview_arm.py owns every
joint transform in this project and this file does not add a second opinion
about any of them. It runs _preview_arm with VIEWS emptied - which poses the
whole arm and renders nothing - and then works entirely by TOGGLING
VISIBILITY on the occurrences that run left behind. A step is therefore a
subset of one assembly, not a re-derivation of it, and no picture here can
show a joint in a place the assembly render would not.

THE FIRST SEVENTEEN OCCURRENCES ARE NOT THE ARM. _preview_arm keeps one
source occurrence per component at the origin and then ADDS the posed ones
from those components. Rendering without hiding the source pile frames a heap
at the origin with the arm as a speck beside it - which is exactly the failure
_preview_arm's own camera comment warns about, arrived at from the other end.

EACH STEP IS FRAMED ON WHAT IT ADDS, not on what is lit. The first version
fitted the camera to every visible body, and because step 1 lights a 186 mm
turntable, the elbow drive in step 6 came out as a 20 mm speck at the top of
the frame - a picture of the whole arm with the subject too small to read.
The subject of a step is the part that went on in it, so that is what the
camera targets; the rest of the assembly stays in shot as context at
CONTEXT_SPANS times the subject's own size.
"""

import io
import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
OUT = os.path.join(REPO, 'docs', 'robotarm', 'assembly')
W, H = 1500, 1100

# Iso and up, the same pair _preview_arm's arm_iso uses - a step that framed
# itself differently from the assembly render would be a second convention.
ISO = ((1.0, -1.3, 0.65), (0.0, 0.0, 1.0))

# How much of the arm to keep around the subject, in multiples of the
# subject's own longest dimension. 1.0 would crop to the part itself and lose
# what it bolts to, which is the one thing a build step has to show.
CONTEXT_SPANS = 2.4
MIN_EXTENTS_CM = 4.0   # a 20 mm hub alone would otherwise fill the frame

# The posed occurrences, in the order _preview_arm.placed appends them. Held
# as INDICES because three of them are the same component - wrist_hub serves
# J2's idler and both J4 trunnions - and a name lookup cannot tell them apart.
POSED_FIRST = 17

P = {
    'stator': 17, 'ring': 18, 'bracket': 19,
    'j2_hub': 20, 'j2_idler': 21,
    'upper_arm': 22, 'forearm': 23,
    'j4_hub_p': 24, 'j4_hub_m': 25,
    'j3_gear': 26, 'j3_pinion': 27, 'j3_axle': 28, 'j3_cap': 29,
    'wrist_roll': 30, 'rotator': 31,
    'shell_a': 32, 'shell_b': 33, 'pinion': 34,
    'rack_a': 35, 'blade_a': 36, 'rack_b': 37, 'blade_b': 38,
    'rollers': 39, 'platter': 40,
}

# CUMULATIVE. Each step adds to the one before it, because that is what
# building is - nothing here ever comes back off.
STEPS = [
    ('01_turret', ['platter', 'stator', 'rollers', 'ring'],
     'the turntable you already have - stator, 3 x 608ZZ, ring'),
    ('02_shoulder_bracket', ['bracket'],
     'shoulder_bracket bolts to the ring, 3 x M3 through the posts'),
    ('03_j2_hubs', ['j2_hub', 'j2_idler'],
     'shoulder_hub onto the MG995 spline; a wrist_hub as the idler trunnion'),
    ('04_upper_arm', ['upper_arm'],
     'upper_arm drops onto both hex hubs - L1 125 mm'),
    ('05_elbow_servo', ['j3_cap', 'j3_pinion'],
     'SG90 into j3_servo_cap, j3_pinion onto its spline. 2 x M3 x 16 BUTTON HEAD'),
    ('06_elbow_gear', ['j3_gear', 'j3_axle'],
     'j3_gear meshes the pinion at 27.20 centre, 2:1; j3_axle runs in the 608ZZ'),
    ('07_forearm', ['forearm'],
     'the forearm closes over the elbow - nx + px + 2 rails, 8 x M3 seam'),
    ('08_j4_hubs', ['j4_hub_p', 'j4_hub_m'],
     'two wrist_hub on the J4 SG90 spline and its idler side'),
    ('09_wrist_roll', ['wrist_roll'],
     'wrist_roll clamshell keys onto both hexes, 3 x M2 through-bolt'),
    ('10_rotator', ['rotator'],
     'wrist_rotator onto the J5 spline, seating face at wro_rot_seat 11.70'),
    ('11_effector', ['shell_a', 'shell_b', 'pinion',
                     'rack_a', 'rack_b', 'blade_a', 'blade_b'],
     'the pruner head, 4 x M3 to the rotator'),
    # Adds nothing. It exists so the set ends on the whole arm rather than on
    # a close-up of the last thing fitted.
    ('12_complete', [], 'the arm, posed at J1 25 / J2 35 / J3 -55 / J4 15'),
]


def run(_context: str):
    app = adsk.core.Application.get()
    if REPO not in sys.path:
        sys.path.insert(0, REPO)

    # ---- pose the arm, render nothing --------------------------------------
    name = '_preview_arm'
    path = os.path.join(REPO, 'models', 'robotarm', name + '.py')
    for m in [m for m in list(sys.modules) if m.split('.')[0] in ('lib', 'models')]:
        del sys.modules[m]
    ns = {'__name__': name, '__file__': path}
    exec(compile(io.open(path, encoding='utf-8').read(), path, 'exec'), ns)
    ns['VIEWS'] = {}
    ns['run']('')

    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    occs = [root.occurrences.item(i) for i in range(root.occurrences.count)]
    assert len(occs) > max(P.values()), (
        'only %d occurrences - _preview_arm did not pose the arm' % len(occs))

    # THE SOURCE PILE GOES DARK FIRST. Indices below POSED_FIRST are the
    # unposed components sitting on top of each other at the origin.
    for i, o in enumerate(occs):
        o.isLightBulbOn = False
    for i in range(POSED_FIRST):
        assert not occs[i].isLightBulbOn, 'source occurrence %d still lit' % i

    vp = app.activeViewport
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    shown = []
    written = []
    def box(idx):
        """Bounding box of a set of occurrence indices, as (centre, span) in cm.

        Tracked by hand rather than with BoundingBox3D.combine: seeded from an
        inverted box, combine() keeps the sentinel and reports a 20 000 000 mm
        assembly with a straight face. _preview_arm learned that first.
        """
        lo = [1e18, 1e18, 1e18]
        hi = [-1e18, -1e18, -1e18]
        for i in idx:
            o = occs[i]
            for j in range(o.component.bRepBodies.count):
                b = o.component.bRepBodies.item(j).createForAssemblyContext(o).boundingBox
                for a, (p_lo, p_hi) in enumerate(
                        ((b.minPoint.x, b.maxPoint.x),
                         (b.minPoint.y, b.maxPoint.y),
                         (b.minPoint.z, b.maxPoint.z))):
                    lo[a] = min(lo[a], p_lo)
                    hi[a] = max(hi[a], p_hi)
        assert max(hi) < 1e6, 'the bounding box never got seeded'
        return ([(lo[a] + hi[a]) / 2 for a in range(3)],
                max(hi[a] - lo[a] for a in range(3)))

    for label, adds, note in STEPS:
        new_idx = []
        for k in adds:
            assert k in P, 'step %s names %r, which is not in P' % (label, k)
            occs[P[k]].isLightBulbOn = True
            shown.append(P[k])
            new_idx.append(P[k])

        # THE SUBJECT IS WHAT WENT ON, and the frame is sized from it. A step
        # that adds nothing (the closing wide shot) falls back to everything
        # lit, which is the only time fitting the whole arm is the point.
        wide = not new_idx
        c, subject = box(shown if wide else new_idx)
        _, lit = box(shown)
        extents = max(subject * CONTEXT_SPANS, MIN_EXTENTS_CM)
        d, up = ISO
        norm = math.sqrt(sum(v * v for v in d))
        dist = lit * 6
        cam = vp.camera
        cam.target = adsk.core.Point3D.create(c[0], c[1], c[2])
        cam.eye = adsk.core.Point3D.create(*[c[a] + d[a] / norm * dist for a in range(3)])
        cam.upVector = adsk.core.Vector3D.create(up[0], up[1], up[2])
        # THE WIDE SHOT FITS, THE STEPS DO NOT. viewExtents is the smaller of
        # the view's two dimensions, so sizing the last frame from a 338 mm
        # diagonal cropped the turret off the bottom of a 1500 x 1100 image.
        # A step that adds nothing wants everything in frame and Fusion's own
        # fit is the thing that guarantees it; a step with a subject wants a
        # fixed frame around that subject, which fit cannot express.
        cam.isFitView = wide
        if not wide:
            cam.viewExtents = extents
        vp.camera = cam
        vp.refresh()
        adsk.doEvents()

        out = os.path.join(OUT, label + '.png')
        ok = vp.saveAsImageFile(out, W, H)
        assert ok, 'step %s: the viewport refused to save %s' % (label, out)
        written.append(out)
        print('%-20s %2d lit  subject %6.1f mm  frame %s  %s'
              % (label, len(shown), subject * 10,
                 'FIT   ' if wide else '%6.1f' % (extents * 10), note))

    print('')
    print('wrote %d images to %s' % (len(written), OUT))
