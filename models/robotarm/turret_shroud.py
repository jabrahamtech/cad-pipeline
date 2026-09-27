"""robotarm/turret_shroud - Fusion MCP generating script.

Rebuilds `robotarm_turret_shroud` (idempotent). PRINT ONE, dark.

Spec: specs/robotarm/turret_shroud.md

THE TURRET HAD ITS WORKINGS ON SHOW. Between the base lid and the lobed
ring every render showed three bare posts, three 608s, the MG995, the hall
post and the loom - the J1 stage looked unfinished next to a styled arm.
This is a fixed 12-sided skirt from the lid up to the ring's top face: the
turret reads as one drum, the same dodecagon as the base below it, with the
ring and the rotating shoulder set into its top.

FIXED, NOT ROTATING. It belongs to the stator side: it stands on the lid and
grips the three turret posts with saddles - a 0.15 press (design_rules
JOINT_FIT_MM['press']) on each post's outer face. It slides down over the
posts BEFORE the ring goes on, and lifts off the same way once the ring is
removed. Nothing is screwed to it and nothing inside has to change.

Every radius and height is READ from the tt_/ts_ parameters turntable_stator
writes, and asserted present - it cannot be built into a document without the
stator, and it cannot drift from the posts and ring it has to clear.

WHAT IT COSTS: J2's down-pitch. The arm pitching down used to reach the ring
(r 50); now it reaches the shroud's corners. The new limit is scanned the way
shoulder_bracket.py scans it and printed below when sb_* is in the document.

Print orientation: LID END DOWN, as it stands. The saddles start 6 mm up;
their underside is chamfered 45 deg into the wall, so they grow out of it
without support. Brim not needed.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402
from lib.design_rules import MIN_WALL_MM as _MIN_WALL  # noqa: E402
from lib.palette import hints_for  # noqa: E402

MATERIAL_NAME = 'PET Plastic'
COMPONENT = 'robotarm_turret_shroud'
BODY_NAME = 'turret_shroud'
PREFIX = 'tsh_'
APPEARANCE_HINTS = hints_for('turret_shroud')
SIDES = 12
VERTEX_AZ0 = 30.0          # same as base_platter: the two dodecagons line up
POST_AZ = (120.0, 180.0, 240.0)
PH_FORM = 'drum'
PH_SADDLES = 'saddles'
PHASES = [PH_FORM, PH_SADDLES]
TOL = 1e-9
SCAN_STEP = 0.05           # cm, the down-pitch scan (as shoulder_bracket)
DEG_STEP = 0.5
MIN_DOWN_DEG = 20.0
FULL_DOWN_DEG = 90.0
SADDLE_BITE_MM = 3.5       # how far the saddle wraps onto the post's outer face
CLEAR_EXTRA_MM = 0.1
AREA_REL_TOL = 1e-6
EDGE_TOL_CM = 1e-6
PRINTED_G_PER_MM3 = 1.27 * 0.65 / 1000.0   # lib/arm_loads SOLID_TO_PRINTED


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def need(n):
        p = ups.itemByName(n)
        assert p is not None, ('%s is not in this document - build turntable_stator first; '
                               'the shroud reads the turret from it' % n)
        return p.value

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value

    post_r, post_d = need('tt_post_r'), need('ts_post_d')
    ring_top = need('tt_race_z') + need('tt_disc_t') + need('tt_ring_lift') + need('tt_ring_t')
    ring_or, plate_or = need('tt_ring_or'), need('ts_plate_or')

    param('free', '%.2f mm' % _FIT['free'], 'free fit - design_rules')
    param('press', '%.2f mm' % _FIT['press'], 'press fit on the posts - design_rules')
    param('wall', '2.0 mm', 'skirt wall at the flats - MIN_WALL + margin, it is all you see')
    param('ri', '%.4f mm' % ((max(post_r + post_d / 2, ring_or, plate_or)) * 10 + _FIT['free'] * 2
                            + CLEAR_EXTRA_MM),
          'DERIVED: clears the posts, the ring and the stator plate by 2 x free')
    param('ro', PREFIX + 'ri + ' + PREFIX + 'wall', 'apothem - across flats / 2')
    param('h', '%.4f mm' % (ring_top * 10), 'DERIVED: lid top (z 0) to the ring\'s top face')
    param('top_facet', '1.2 mm', 'top outer edge - _style.md rule 1 scaled to the 2.0 wall')
    param('saddle_z0', '6.0 mm', 'saddles start above the stator base plate (z 0..4)')
    param('saddle_gap', '%.4f mm' % (need('tt_ring_t') * 10 + _FIT['free']),
          'DERIVED: saddles stop a free fit under the ring, which fills the top ring_t')
    param('saddle_in', '%.4f mm' % ((post_r + post_d / 2) * 10 - SADDLE_BITE_MM),
          'saddles reach in to here - 3.5 into the post\'s outer face')
    param('saddle_chamfer', '%.4f mm' % (SADDLE_BITE_MM - _MIN_WALL / 2),
          '45 deg under each saddle, leaving a small land - printed upright')
    param('saddle_w', '%.4f mm' % (post_d * 10 + 2 * _MIN_WALL), 'tangential width')

    ri, ro, h = val('ri'), val('ro'), val('h')
    assert ro - ri >= _MIN_WALL / 10 - TOL
    assert (ro - ri) - val('top_facet') >= _MIN_WALL / 10 / 2 - TOL, 'the top facet eats the wall'
    assert val('saddle_z0') > need('ts_plate_t') + val('free'), 'the saddles hit the stator plate'

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c == design.rootComponent:
            continue
        if c.name == COMPONENT or c.name.startswith(COMPONENT + ' ('):
            c.name = STALE + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(STALE):
            occ.deleteMe()
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = COMPONENT
    assert comp.name == COMPONENT, 'a stale component still holds the name'
    ext = comp.features.extrudeFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def extrude(prof, op, z0_expr, dz_expr, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0_expr))
        inp.setDistanceExtent(False, V(dz_expr))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    # ---- phase 1: the drum - a dodecagon with a round bore ----
    t0 = design.timeline.count
    r_v = ro / math.cos(math.pi / SIDES)
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = 'sk_drum'
    pts = [P3(r_v * math.cos(math.radians(VERTEX_AZ0) + 2 * math.pi * k / SIDES),
              r_v * math.sin(math.radians(VERTEX_AZ0) + 2 * math.pi * k / SIDES), 0)
           for k in range(SIDES)]
    for k in range(SIDES):
        sk.sketchCurves.sketchLines.addByTwoPoints(pts[k], pts[(k + 1) % SIDES])
    sk.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0), ri)
    want = SIDES * ro ** 2 * math.tan(math.pi / SIDES) - math.pi * ri ** 2
    prof = [sk.profiles.item(i) for i in range(sk.profiles.count)
            if abs(sk.profiles.item(i).areaProperties().area - want) < want * AREA_REL_TOL]
    assert len(prof) == 1, 'the drum profile was not found'
    extrude(prof[0], NEW, '0 mm', PREFIX + 'h', 'drum')
    body = comp.bRepBodies.item(0)
    top = adsk.core.ObjectCollection.create()
    for e in body.edges:
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.z - h) < EDGE_TOL_CM and abs(b.z - h) < EDGE_TOL_CM and \
                math.hypot((a.x + b.x) / 2, (a.y + b.y) / 2) > ri + TOL:
            top.add(e)
    assert top.count == SIDES, 'expected %d top outer edges, found %d' % (SIDES, top.count)
    ci = comp.features.chamferFeatures.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(top, V(PREFIX + 'top_facet'), False)
    f = comp.features.chamferFeatures.add(ci)
    f.name = 'top_facet'
    group(t0, PH_FORM)

    # ---- phase 2: three saddles pressing on the posts ----
    t1 = design.timeline.count
    r_cut = post_d / 2 - val('press') / 2
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        c, s = math.cos(a), math.sin(a)
        hw = val('saddle_w') / 2
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_saddle_%d' % i
        corners = [(val('saddle_in'), -hw), (ri + val('wall') / 2, -hw),
                   (ri + val('wall') / 2, hw), (val('saddle_in'), hw)]
        q = [P3(rr * c - tt * s, rr * s + tt * c, 0) for rr, tt in corners]
        for k in range(len(q)):
            sk.sketchCurves.sketchLines.addByTwoPoints(q[k], q[(k + 1) % len(q)])
        assert sk.profiles.count == 1
        extrude(sk.profiles.item(0), JOIN, PREFIX + 'saddle_z0',
                PREFIX + 'h - ' + PREFIX + 'saddle_z0 - ' + PREFIX + 'saddle_gap', 'saddle_%d' % i)
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_post_%d' % i
        sk.sketchCurves.sketchCircles.addByCenterRadius(P3(post_r * c, post_r * s, 0), r_cut)
        extrude(sk.profiles.item(0), CUT, '-1 mm', PREFIX + 'h + 2 mm', 'post_seat_%d' % i)
    # 45 deg under each saddle, so it grows out of the wall when printed upright
    body = comp.bRepBodies.item(0)
    under = adsk.core.ObjectCollection.create()
    z0 = val('saddle_z0')
    for e in body.edges:
        a_, b_ = e.startVertex.geometry, e.endVertex.geometry
        if abs(a_.z - z0) < EDGE_TOL_CM and abs(b_.z - z0) < EDGE_TOL_CM and \
                isinstance(e.geometry, adsk.core.Arc3D) and abs(e.geometry.radius - r_cut) < EDGE_TOL_CM:
            under.add(e)
    assert under.count == len(POST_AZ), 'expected %d saddle seat arcs, found %d' % (len(POST_AZ), under.count)
    ci = comp.features.chamferFeatures.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(under, V(PREFIX + 'saddle_chamfer'), False)
    f = comp.features.chamferFeatures.add(ci)
    f.name = 'saddle_underside'
    group(t1, PH_SADDLES)

    assert comp.bRepBodies.count == 1, 'the shroud came out in %d pieces' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used = 'none'
    for want_ in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a_ = apps.item(j)
                if all(w.lower() in a_.name.lower() for w in want_):
                    body.appearance = a_
                    used = a_.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    # ---- what it costs J2: shoulder_bracket.py's own scan, with the ring's
    # r swapped for the shroud's CORNER radius (worst azimuth). The shroud's
    # top is flush with the ring's, which is the plane the bracket stands on,
    # sb_stand_h below the J2 axis.
    down = None
    if ups.itemByName('sb_arm_l1') is not None:
        l1, half = need('sb_arm_l1'), need('sb_arm_half')
        drop = need('sb_stand_h')

        def hits(theta):
            sn, cs = math.sin(theta), math.cos(theta)
            d = 0.0
            while d <= l1 + TOL:
                for t in (-half, 0.0, half):
                    if abs(d * cs + t * sn) <= r_v and -d * sn + t * cs <= -drop:
                        return True
                d += SCAN_STEP
            return False
        down = 0.0
        while down < FULL_DOWN_DEG and not hits(math.radians(down + DEG_STEP)):
            down += DEG_STEP
        assert down >= MIN_DOWN_DEG, 'the shroud leaves J2 only %.1f deg of down-pitch' % down

    bb = body.boundingBox
    vol = body.physicalProperties.volume * 1000
    print("body: '%s' | appearance: %s | PRINT 1, upright" % (body.name, used))
    print('dodecagon %.1f across flats (%.1f across corners), bore O%.1f, %.1f tall: lid top to ring top'
          % (2 * ro * 10, 2 * r_v * 10, 2 * ri * 10, h * 10))
    print('clears posts (r %.1f), ring (r %.1f), stator plate (r %.1f); saddles press %.2f on 3 posts'
          % ((post_r + post_d / 2) * 10, ring_or * 10, plate_or * 10, val('press') * 10))
    if down is not None:
        print('J2 down-pitch with the shroud: %.1f deg' % down)
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (vol, vol * PRINTED_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
