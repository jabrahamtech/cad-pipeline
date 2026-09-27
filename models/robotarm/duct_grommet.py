"""robotarm/duct_grommet - Fusion MCP generating script.

Rebuilds `robotarm_duct_grommet` (idempotent). PRINT TWO - one in each end of
the upper arm's cable duct.

Spec: specs/robotarm/duct_grommet.md

THE UPPER ARM'S DUCT IS THE LOOM'S ROUTE PAST J2 AND J3, AND ITS MOUTHS
ARE SHARP. The duct is a 14 x 19 rectangular tunnel cut the full length of
the link; it breaks out through the curved drum at each joint, which leaves
a square-edged mouth right where the J2 and J3 service loops flex. A loom
that bends over a printed edge a few thousand times saws through its own
sleeving (specs/robotarm/_harness.md: bend radius >= 10 x OD, and the
bending must happen in the loop, not at the exit).

THREE JOBS:
  1. a rounded LIP - a 1.0 chamfer round the inside of the mouth, so the
     loom leaves over a radius and not an arris
  2. a TIE BAR across the mouth, 3.0 off one wall. A zip tie threads
     through that gap, round the bar and the loom: the anchor at the
     duct end of each service loop ("tie at both ends of each loop")
  3. it PRESSES in (0.15 total, design_rules JOINT_FIT_MM['press']) - no
     glue, no screw, nothing in the link has to change

WHY ITS OUTER END STOPS 8.8 FROM THE JOINT AXIS. The duct breaks out of a
r 13.0 drum, so its corner edges end at y = sqrt(13.0^2 - 9.5^2) = 8.87 and
the middle of the mouth at 13.0. The forearm (at J3) and the shoulder
bracket (at J2) are cut to clear r 13.4 about the axis, so nothing may
stand proud of the drum: the grommet's outer end sits where its own
corners meet the drum circle. It is 6.0 deep, which ends it 2.8 from the
axis - clear of the M3 elbow retention bolt that crosses the duct ON the J3
axis (O3.0 in a O3.4 bore; see upper_arm.py). Asserted.

The duct numbers are upper_arm's (ua_duct_x, ua_duct_z, ua_drum_r,
ua_bolt_clear). They are declared here with the same values and ASSERTED
equal whenever upper_arm is in the same document - which it is in the
gate, _check_bits.

Print orientation: outer end DOWN - the tie bar is then a bar on the bed
and the lip chamfer faces down, both printable without support.

Frame: z 0 the outer (mouth) end, +z INTO the duct. x across the duct's
14 width (upper_arm X), y across its 19 height (upper_arm Z).
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402
from lib.design_rules import MIN_WALL_MM, ELEPHANT_FOOT_CHAMFER_MM  # noqa: E402
from lib.palette import hints_for  # noqa: E402

MATERIAL_NAME = 'PET Plastic'
COMPONENT = 'robotarm_duct_grommet'
BODY_NAME = 'duct_grommet'
PREFIX = 'dg_'
APPEARANCE_HINTS = hints_for('upper_arm')

PH_TUBE = 'tube'
PH_LIP = 'lip'
PH_BAR = 'tie bar'
PHASES = [PH_TUBE, PH_LIP, PH_BAR]
TOL = 1e-9                     # comparison epsilon, not a dimension
RECT_EDGES = 4                 # a rectangle's edge loop - a count, not a dimension

# upper_arm's own values - asserted against ua_* when both are in one document
UA_DUCT_X_MM = 7.0
UA_DUCT_Z_MM = 9.5
UA_DRUM_R_MM = 13.0
TIE_W_MM = 2.5                 # DATASHEET - a 2.5 mm zip tie, the small standard
LOOM_OD_MM = 6.0               # specs/robotarm/_harness.md - the 6 mm PET sleeving


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

    param('duct_x', '%.2f mm' % UA_DUCT_X_MM, 'upper_arm ua_duct_x - half width (asserted)')
    param('duct_z', '%.2f mm' % UA_DUCT_Z_MM, 'upper_arm ua_duct_z - half height (asserted)')
    param('drum_r', '%.2f mm' % UA_DRUM_R_MM, 'upper_arm ua_drum_r (asserted)')
    param('bolt_clear', '%.2f mm' % _FASTENER['M3']['clearance'],
          'upper_arm ua_bolt_clear - the elbow bolt on the J3 axis (asserted)')
    param('press', '%.2f mm' % _FIT['press'], 'design_rules JOINT_FIT_MM press, total')
    param('free', '%.2f mm' % _FIT['free'], 'design_rules JOINT_FIT_MM free')
    param('wall', '%.2f mm' % MIN_WALL_MM, 'MIN_WALL')
    param('depth', '6.0 mm', 'how far it goes in - asserted clear of the elbow bolt')
    param('lip', '1.0 mm', 'chamfer round the inside of the mouth - the loom leaves over it')
    param('lead', '%.2f mm' % ELEPHANT_FOOT_CHAMFER_MM,
          'lead-in chamfer round the inner end - it goes in first')
    param('tie_gap', '%.2f mm' % (TIE_W_MM + _FIT['locational'] * 2 + _FIT['free']),
          'zip tie 2.5 + play - between the bar and the -y wall')
    param('bar_t', '%.2f mm' % MIN_WALL_MM, 'tie bar section across the gap - MIN_WALL')
    param('bar_d', '2.4 mm', 'tie bar depth along the duct')

    # the same document may hold upper_arm - then its numbers win or we stop
    for mine, theirs in (('duct_x', 'ua_duct_x'), ('duct_z', 'ua_duct_z'),
                         ('drum_r', 'ua_drum_r'), ('bolt_clear', 'ua_bolt_clear')):
        p = ups.itemByName(theirs)
        if p is not None:
            assert abs(p.value - val(mine)) < TOL * 10, (
                '%s is %.2f in upper_arm and %.2f here - the grommet is cut to the wrong duct'
                % (theirs, p.value * 10, val(mine) * 10))

    w_o = 2 * val('duct_x') + val('press')          # outer, across x
    h_o = 2 * val('duct_z') + val('press')          # outer, across y
    w_i = w_o - 2 * val('wall')
    h_i = h_o - 2 * val('wall')
    # the mouth: where the grommet's own corners meet the drum circle
    y_mouth = math.sqrt(val('drum_r') ** 2 - (h_o / 2) ** 2)
    y_inner = y_mouth - val('depth')
    bar_y0 = -h_i / 2 + val('tie_gap')
    above_bar = h_i / 2 - (bar_y0 + val('bar_t'))

    assert y_inner >= val('bolt_clear') / 2 + val('free') - TOL, (
        'the grommet ends %.2f from the J3 axis and the elbow bolt bore is r %.2f '
        '- it would sit on the bolt' % (y_inner * 10, val('bolt_clear') / 2 * 10))
    assert above_bar * 10 >= LOOM_OD_MM + 2 * val('free') * 10 - TOL, (
        'only %.2f above the tie bar for a %.1f loom' % (above_bar * 10, LOOM_OD_MM))
    assert val('lip') < val('wall') - TOL, 'the lip chamfer eats the whole wall'
    assert math.hypot(y_mouth, h_o / 2) <= val('drum_r') + TOL, (
        'the grommet corner stands proud of the drum - the next link is cut to r 13.4')

    param('mouth', '%.4f mm' % (y_mouth * 10),
          'DERIVED: outer end, from the joint axis - sqrt(drum_r^2 - (h_o/2)^2)')

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
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation

    def rect(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchLines.addTwoPointRectangle(P3(x0, y0, 0.0), P3(x1, y1, 0.0))
        assert sk.profiles.count == 1, sk.name
        inp = ext.createInput(sk.profiles.item(0), op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0_expr))
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V(dz_expr)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(0)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    def chamfer(name, pick, dist_expr):
        body = comp.bRepBodies.item(0)
        col = adsk.core.ObjectCollection.create()
        for e in body.edges:
            if pick(e):
                col.add(e)
        assert col.count == RECT_EDGES, '%s: expected 4 edges, found %d' % (name, col.count)
        ci = comp.features.chamferFeatures.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(dist_expr), False)
        f = comp.features.chamferFeatures.add(ci)
        f.name = name

    eps = val('lead') / 10

    def at_z(e, z):
        a, b = e.startVertex.geometry, e.endVertex.geometry
        return abs(a.z - z) < eps and abs(b.z - z) < eps

    def mid(e):
        a, b = e.startVertex.geometry, e.endVertex.geometry
        return (a.x + b.x) / 2, (a.y + b.y) / 2

    def inner(e):
        mx, my = mid(e)
        return abs(mx) < w_o / 2 - eps and abs(my) < h_o / 2 - eps

    t0 = design.timeline.count
    rect('tube', -w_o / 2, w_o / 2, -h_o / 2, h_o / 2, '0 mm', PREFIX + 'depth', NEW)
    rect('bore', -w_i / 2, w_i / 2, -h_i / 2, h_i / 2, '-1 mm', PREFIX + 'depth + 2 mm', CUT)
    group(t0, PH_TUBE)

    t1 = design.timeline.count
    chamfer('mouth_lip', lambda e: at_z(e, 0.0) and inner(e), PREFIX + 'lip')
    chamfer('lead_in', lambda e: at_z(e, val('depth')) and not inner(e), PREFIX + 'lead')
    group(t1, PH_LIP)

    # the bar spans the OUTER width so it still meets the walls where the lip
    # chamfer has cut them back at the bed
    t2 = design.timeline.count
    rect('tie_bar', -w_o / 2, w_o / 2, bar_y0, bar_y0 + val('bar_t'), '0 mm',
         PREFIX + 'bar_d', JOIN)
    group(t2, PH_BAR)

    assert comp.bRepBodies.count == 1, 'the grommet came out in %d pieces' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
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
    print("body: '%s' | appearance: %s | PRINT TWO, mouth end down"
          % (body.name, used_appearance))
    print('outer %.2f x %.2f (duct %.1f x %.1f + %.2f press), wall %.1f, %.1f deep'
          % (w_o * 10, h_o * 10, val('duct_x') * 2 * 10, val('duct_z') * 2 * 10,
             val('press') * 10, val('wall') * 10, val('depth') * 10))
    print('seats %.2f .. %.2f from the joint axis; elbow bolt bore r %.2f'
          % (y_mouth * 10, y_inner * 10, val('bolt_clear') / 2 * 10))
    print('tie gap %.2f, bar %.1f x %.1f; %.2f of opening above the bar for the loom'
          % (val('tie_gap') * 10, val('bar_t') * 10, val('bar_d') * 10, above_bar * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10,
             bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | mass g: %.2f (x2 = %.2f) | valid: %s'
          % (props.volume * 1000, props.mass * 1000, 2 * props.mass * 1000, body.isValid))
    print('timeline groups: %r' % (PHASES,))
