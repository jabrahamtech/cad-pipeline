"""robotarm/j3_axle - Fusion MCP generating script.

Rebuilds `robotarm_j3_axle` (idempotent). Spec: lib/bearings.py B608ZZ.

THE IDLER HALF OF THE GEARED ELBOW. j3_gear drives one side of the upper
arm; this carries the other, and it runs in a 608ZZ instead of rubbing
plastic on plastic in the fork plate like every other hub in this arm.

WHY A BEARING AT ALL, AND WHY THIS ONE. A gear mesh loads the joint axis
RADIALLY - 15.4 N of separating and tangential force at the pitch point,
which the old printed journal would take on a 20.0 bore with 0.175 of slop
in it. Slop at the elbow is backlash at the tooth, and backlash at the tooth
is the one thing a 2:1 reduction cannot fix. So the idler side gets a real
bearing. It is a 608ZZ because that is what Jonathan has - the small sizes
in lib/bearings.py are datasheet nominals nothing has ever printed against,
and a bought part you do not hold is not a part.

WHAT THE 22.0 OUTSIDE COSTS. It is bigger than the 20.35 journal bore it
replaces, so the forearm's idler plate loses its flange counterbore and
gains a 22.0 x 7.0 pocket. The boss is already r 13.775, which leaves 2.775
of wall - over the 1.6 minimum, so the plate does not have to grow. The
11 g of steel sits ON the J3 axis, so it costs the elbow nothing at all and
costs J2 about 140 g.cm at 125 mm of upper arm - under 5 % of a joint
running at 60 %.

THE THRUST FACE IS 0.4 OF COLLAR, AND THAT IS DELIBERATE. The obvious move
is to let the hex's own outer face bear on the bearing - but the hex is
18.24 across corners and a 608's inner race stops at 12.0, so a flat hex
face would land on the OUTER race and lock the joint solid. So the hex
reach is cut to the socket depth alone (3.4) and an 11.0 collar fills the
0.4 running gap, landing inside the inner race with 0.5 of margin. Same
overall stack, one face moved.

RETENTION IS THE SAME M3 THAT RETAINS THE GEAR. It comes down the elbow
axis from j3_gear, through the upper arm's cable duct, and threads into
this part. Nothing else holds the rotating group together - see
j3_gear.py's docstring for why a flange cannot.

Print orientation: HEX FACE ON THE BED, built +Z. Every step is smaller
than the one below it, so there is no overhang anywhere and the 8.0
journal - the only fit that matters - prints as a vertical cylinder.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core
import adsk.fusion

from lib.bearings import B608ZZ  # noqa: E402
from lib.design_rules import FASTENER_MM as _FASTENERS  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_j3_axle'
BODY_NAME = 'j3_axle'
PREFIX = 'ja_'
WRIST = 'wr_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('j3_axle')
PHASES = ['hex + collar', 'journal', 'finish']


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    B = B608ZZ

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    _set(WRIST + 'pivot_af', '16.0 mm', 'hex socket across flats - SHARED', 'mm')
    _set(WRIST + 'reach', '3.8 mm',
         'hex boss length = 0.4 running gap + 3.4 socket - SHARED', 'mm')

    # --- the bearing, from lib/bearings.py. NOT retyped. -------------------
    param('brg_bore', '%.4f mm' % B.bore, 'lib/bearings.py B608ZZ - do not edit here')
    param('brg_od', '%.4f mm' % B.od, 'lib/bearings.py B608ZZ')
    param('brg_w', '%.4f mm' % B.width, 'lib/bearings.py B608ZZ')
    param('brg_race', '%.4f mm' % B.inner_race_od,
          'lib/bearings.py B608ZZ - how far the INNER race reaches. Anything\n'
          '           clamping this bearing must stay inside it or it rubs the\n'
          '           outer race and the joint locks.')

    # --- the axle -----------------------------------------------------------
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('press', '0.02 mm',
          'the journal is a light press in the inner race: 8.0 - 0.02. A\n'
          '           slip fit here is slop, and slop at the elbow is backlash at\n'
          '           the tooth - the one thing the reduction cannot fix.')
    param('hex_af', WRIST + 'pivot_af - ' + PREFIX + 'loc', 'derived')
    param('socket_d', '3.4 mm',
          'upper arm hex socket depth - ua_socket_d. ASSERTED against it below.')
    param('gap', '0.4 mm', 'running gap, plate inner face to the upper arm')
    param('collar_d', '11.0 mm',
          'thrust collar: must land INSIDE the 12.0 inner race and clear the\n'
          '           8.0 bore, so it is 11.0 - 1.5 mm of annular land with 0.5 to\n'
          '           the race edge. The hex cannot do this job: 18.24 across\n'
          '           corners would bear on the OUTER race and lock the joint.')
    param('journal_d', PREFIX + 'brg_bore - ' + PREFIX + 'press',
          'derived: bearing bore less the press')
    param('journal_l', PREFIX + 'brg_w + 0.5 mm',
          'derived: through the bearing and 0.5 proud, so the bearing is seated\n'
          '           on the collar and not on the end of the journal')
    param('tap_d', '%.4f mm' % _FASTENERS['M3']['pilot'],
          'M3 self-tapping pilot - lib/design_rules.py FASTENER_MM. It said\n'
          '           "design_rules" and was 2.5; design_rules says 2.6. Now it reads\n'
          '           the table instead of quoting it from memory.')
    param('tap_l', '9.0 mm', 'thread engagement for the elbow retention M3')
    param('lead_in', '0.5 mm', 'insertion chamfer on the journal nose')
    param('ef', '0.4 mm', 'elephant-foot chamfer, bed face')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
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
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                sk.name + ': expected %d, got %d' % (expected, sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, 0))

    def disc(name, d_cm, z0, dz, op):
        sk = sketch('sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0, dz, name)

    # ---- phase 1: hex + thrust collar --------------------------------------
    t0 = design.timeline.count
    hex_af = val('hex_af')
    sk_h = sketch('sk_hex_boss')
    r_c = hex_af / 2 / math.cos(math.pi / 6)
    pts = [(r_c * math.cos(2 * math.pi * i / 6), r_c * math.sin(2 * math.pi * i / 6))
           for i in range(6)]
    for i in range(6):
        u, w = pts[i], pts[(i + 1) % 6]
        sk_h.sketchCurves.sketchLines.addByTwoPoints(
            mpt(sk_h, u[0], u[1]), mpt(sk_h, w[0], w[1]))
    extrude(profiles(sk_h, expected=1), NEW, '0.0 mm', PREFIX + 'socket_d', 'hex_boss')
    disc('thrust_collar', val('collar_d'), PREFIX + 'socket_d', PREFIX + 'gap', JOIN)
    group(t0, PHASES[0])

    # ---- phase 2: journal + tapping bore -----------------------------------
    t1 = design.timeline.count
    disc('journal', val('journal_d'),
         PREFIX + 'socket_d + ' + PREFIX + 'gap', PREFIX + 'journal_l', JOIN)
    disc('retention_tap', val('tap_d'), '0.0 mm', PREFIX + 'tap_l', CUT)
    group(t1, PHASES[1])

    # ---- phase 3: finish ----------------------------------------------------
    t2 = design.timeline.count

    def edges_in_plane_z(z_pick):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.z - z_pick) < val('tol')
                    and abs(eb.maxPoint.z - z_pick) < val('tol')):
                col.add(e)
        return col

    top = val('socket_d') + val('gap') + val('journal_l')
    for z_pick, size, nm in ((0.0, PREFIX + 'ef', 'bed_face_chamfer'),
                             (top, PREFIX + 'lead_in', 'journal_nose_lead_in')):
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            edges_in_plane_z(z_pick), V(size), False)
        chf.add(c_inp).name = nm
    group(t2, PHASES[2])

    # ---- identity + diagnostics ---------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got %d' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used = a.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    # ---- the checks -----------------------------------------------------------
    # THE ONE THAT MATTERS: the thrust collar has to land on the INNER race.
    assert val('collar_d') * 10 <= B.inner_race_od - 0.5, (
        'the thrust collar is %.2f and the 608ZZ inner race stops at %.2f - it '
        'would bear on the OUTER race and lock the joint'
        % (val('collar_d') * 10, B.inner_race_od))
    assert val('collar_d') * 10 >= B.bore + 2.0, (
        'the thrust collar is %.2f, barely over the %.2f bore - there is no '
        'land to bear on' % (val('collar_d') * 10, B.bore))
    assert val('journal_l') * 10 > B.width, (
        'the journal is %.2f and the bearing is %.2f wide - it does not pass '
        'through' % (val('journal_l') * 10, B.width))
    assert val('tap_l') <= val('socket_d') + val('gap') + val('journal_l') - 0.1, (
        'the retention tap runs out the far end of the axle')
    hex_corners = hex_af / math.cos(math.pi / 6) * 10
    assert hex_corners > B.inner_race_od, (
        'sanity: the hex should be bigger than the race, that is why the '
        'collar exists')
    ua_sock = ups.itemByName('ua_socket_d')
    if ua_sock is not None:
        assert abs(ua_sock.value - val('socket_d')) < 1e-9, (
            'ja_socket_d %.2f disagrees with ua_socket_d %.2f'
            % (val('socket_d') * 10, ua_sock.value * 10))
    tap_wall = (val('collar_d') / 2 - val('tap_d') / 2) * 10
    assert tap_wall >= 1.6, 'only %.2f mm of wall around the retention tap' % tap_wall

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used))
    print('608ZZ: bore %.1f od %.1f width %.1f, inner race reaches %.1f'
          % (B.bore, B.od, B.width, B.inner_race_od))
    print('stack from the socket floor: hex %.2f af x %.1f | collar %.1f x %.1f '
          '| journal %.2f x %.2f'
          % (hex_af * 10, val('socket_d') * 10, val('collar_d') * 10,
             val('gap') * 10, val('journal_d') * 10, val('journal_l') * 10))
    print('journal is a %.2f press in the %.1f race bore' % (val('press') * 10, B.bore))
    print('collar land: r %.2f..%.2f inside a race that ends at r %.2f'
          % (val('journal_d') * 5, val('collar_d') * 5, B.inner_race_od / 2))
    print('M3 retention: %.1f pilot x %.1f deep, from the j3_gear side'
          % (val('tap_d') * 10, val('tap_l') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s'
          % (body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d'
          % (comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
