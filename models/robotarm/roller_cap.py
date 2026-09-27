"""robotarm/roller_cap - Fusion MCP generating script.

Rebuilds `robotarm_roller_cap` (idempotent). PRINT THREE.

Spec: specs/robotarm/roller_cap.md

THE RETAINER ON EACH 608 ROLLER. The turntable stator carries three 608ZZ
on radial stub axles that point INWARD from their cheeks. Nothing holds a
bearing on its stub except this cap and an M3 x 8 up the stub's pilot.

A STANDARD M3 WASHER IS O7 AND THE 608 BORE IS O8 - it falls straight
through and clamps nothing. The cap is O11: over the 8.0 bore, inside the
12.0 inner-race OD, so it presses the INNER race only. Past 12.0 it would
reach the ZZ shield, which rides with the OUTER race, and the roller would
drag instead of roll. lib/j1_drive.ROLLER_CAP_D_MM; the stator asserts it.

THE RECESS IS THE POINT OF THE PART. The stub is 8.0 long and the bearing
7.0, so the stub stands 1.0 proud of the race face. A flat cap would land
on the stub end and clamp nothing; the old gauge cap had a spigot INTO the
bore, which the stub already fills. This cap has a O8.3 x 1.3 pocket on its
bearing face that swallows the proud stub with 0.3 to spare, so the only
thing it can bear on is the race. The stator asserts both numbers against
its own stub, and that an M3 x 8 bites 2 d into the stub and stops short
of the 7.0 pilot.

AND IT DECIDES THE HUB. With a cap and a screw head at each stub's inner
end, a O11 disc reaches z 18.6 in the stator frame. The j1_hub cable cup's
skirt used to come down to 16.6 and would have run through all three;
lib/j1_drive derives the skirt height from ROLLER_CAP_TOP_Z_MM now.

Print orientation: FLAT, head face on the bed, pocket up. No support. The
pocket is a blind O8.3 hole open to the top - nothing bridges.

Frame: z 0 = the screw-head face, z = cap_t the bearing face. On the stator
the local +z points radially OUTWARD, the head face at r 20.5.
"""

import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

from lib.bearings import B608ZZ  # noqa: E402
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.design_rules import MIN_WALL_MM, ELEPHANT_FOOT_CHAMFER_MM  # noqa: E402
from lib.j1_drive import (  # noqa: E402
    ROLLER_CAP_D_MM, ROLLER_CAP_T_MM, ROLLER_CAP_RECESS_D_MM,
    ROLLER_CAP_RECESS_H_MM, ROLLER_SCREW_L_MM, J1_HUB_SCREW,
)
from lib.palette import hints_for  # noqa: E402

MATERIAL_NAME = 'PET Plastic'
COMPONENT = 'robotarm_roller_cap'
BODY_NAME = 'roller_cap'
PREFIX = 'rc_'
APPEARANCE_HINTS = hints_for('turntable_stator')

PH_DISC = 'disc'
PH_HOLES = 'bore and recess'
PH_FINISH = 'finish'
PHASES = [PH_DISC, PH_HOLES, PH_FINISH]
TOL = 1e-9                     # comparison epsilon, not a dimension


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

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

    param('d', '%.2f mm' % ROLLER_CAP_D_MM,
          'lib/j1_drive.ROLLER_CAP_D_MM - over the 8.0 bore, inside the 12.0 inner race')
    param('t', '%.2f mm' % ROLLER_CAP_T_MM, 'lib/j1_drive.ROLLER_CAP_T_MM')
    param('recess_d', '%.2f mm' % ROLLER_CAP_RECESS_D_MM,
          'swallows the O7.9 stub end - lib, asserted by the stator')
    param('recess_h', '%.2f mm' % ROLLER_CAP_RECESS_H_MM,
          'the stub stands 1.0 proud of the race; 0.3 more - lib, asserted by the stator')
    param('bore', '%.2f mm' % _FASTENER[J1_HUB_SCREW]['clearance'],
          'M3 clearance - design_rules FASTENER_MM')
    param('ef', '%.2f mm' % ELEPHANT_FOOT_CHAMFER_MM, 'elephant-foot chamfer - design_rules')

    floor = val('t') - val('recess_h')
    assert floor * 10 >= MIN_WALL_MM - TOL, (
        'the cap floor under the screw head is %.2f - MIN_WALL %.2f'
        % (floor * 10, MIN_WALL_MM))
    assert B608ZZ.bore < val('d') * 10 < B608ZZ.inner_race_od - TOL, (
        'the cap must land on the inner race annulus %.1f..%.1f; %.2f does not'
        % (B608ZZ.bore, B608ZZ.inner_race_od, val('d') * 10))
    assert val('recess_d') * 10 < B608ZZ.bore + (B608ZZ.inner_race_od - B608ZZ.bore) / 2, (
        'the recess eats the inner-race contact annulus - the cap bears on '
        'nothing but its rim')
    assert val('bore') < val('recess_d') - TOL, 'the screw bore is wider than the recess'

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
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def circle(name, d, z0_expr, dz_expr, op):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(P3(0.0, 0.0, 0.0), d / 2)
        assert sk.profiles.count == 1, sk.name
        inp = ext.createInput(sk.profiles.item(0), op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0_expr))
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V(dz_expr)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        if op == CUT:
            inp.participantBodies = [comp.bRepBodies.item(0)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    t0 = design.timeline.count
    circle('disc', val('d'), '0 mm', PREFIX + 't', NEW)
    group(t0, PH_DISC)

    t1 = design.timeline.count
    circle('screw_bore', val('bore'), '-1 mm', PREFIX + 't + 2 mm', CUT)
    circle('stub_recess', val('recess_d'), PREFIX + 't - ' + PREFIX + 'recess_h',
           PREFIX + 'recess_h + 1 mm', CUT)
    group(t1, PH_HOLES)

    # the bed edge: the outer circle at z 0
    t2 = design.timeline.count
    body = comp.bRepBodies.item(0)
    edges = adsk.core.ObjectCollection.create()
    r_out = val('d') / 2
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Circle3D) and abs(g.center.z) < val('ef') / 10 \
                and abs(g.radius - r_out) < val('ef') / 10:
            edges.add(e)
    assert edges.count == 1, 'expected the one outer bed edge, found %d' % edges.count
    ch = comp.features.chamferFeatures
    cin = ch.createInput2()
    cin.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(PREFIX + 'ef'), False)
    f = ch.add(cin)
    f.name = 'elephant_foot'
    group(t2, PH_FINISH)

    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used_appearance = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used_appearance = a.name
                    break
            if used_appearance != 'none':
                break
        if used_appearance != 'none':
            break

    props = body.physicalProperties
    bb = body.boundingBox
    print("body: '%s' | appearance: %s | PRINT THREE, head face down"
          % (body.name, used_appearance))
    print('O%.1f x %.1f, O%.1f x %.1f pocket over the proud stub, O%.1f bore, floor %.2f'
          % (val('d') * 10, val('t') * 10, val('recess_d') * 10, val('recess_h') * 10,
             val('bore') * 10, floor * 10))
    print('screw: %s x %.0f socket cap into the stub pilot - the stator asserts the bite'
          % (J1_HUB_SCREW, ROLLER_SCREW_L_MM))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10,
             bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | mass g: %.2f (x3 = %.2f) | valid: %s'
          % (props.volume * 1000, props.mass * 1000, 3 * props.mass * 1000, body.isValid))
    print('timeline groups: %r' % (PHASES,))
