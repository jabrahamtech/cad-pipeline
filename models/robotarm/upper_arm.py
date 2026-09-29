"""robotarm/upper_arm - Fusion MCP generating script.

Rebuilds `robotarm_upper_arm` (idempotent). Spec: specs/robotarm/upper_arm.md,
styled per specs/robotarm/_style.md.

Local frame: origin on the J3 ELBOW axis. +X along it, +Y forward toward the
wrist, +Z up. The J2 shoulder axis is at y = -ua_l1.

ONE HOLE IN IT IS NOT DECORATION. A Ø3.4 bore runs down the ELBOW AXIS,
through the cable duct, from the j3_gear side to j3_axle on the other. It is
the only thing holding the geared elbow together. Every other hub in this arm
is trapped by a flange too big to pass its bore, seating in a counterbore on
the OUTER face; at J3 both stops are inboard - j3_gear's hex bottoms in this
part's socket and its disc lands on the forearm plate's outer face - so
nothing at all stops the group sliding apart and pulling a 3.8 hex clear of a
3.4 socket. An M3 down the axis is what stops it. It carries no load: the hex
takes the torque and the journal takes the radial. See j3_gear.py's docstring.

THE SIMPLEST PART IN THE ARM, and that is a consequence of a decision made
three parts ago rather than luck. The forearm forks at both ends because it
had to; the shoulder bracket forks for the same reason. So this link is
STRADDLED at both ends, and a straddled end is just a block with a hex socket
in each face. No prongs, no journals, no counterbores, no servo lobes. Four
wrist_hubs do all the work, and they are the same four-off part already
printed for J3 and J4.

The drum radius is the one number that is not free. The forearm's clearance
cut assumes nothing of this part comes closer than fa_elbow_clear (13.4) to
the J3 axis, so the drums are 11.0 and the running gap is 0.4. Grow them and
the forearm has to be rebuilt; the assertion below says so.

Print orientation: FLAT, split plane down, built along +Z... it does not have
one. The hex sockets face along X, so they want to be vertical, which means
building along X with the whole 85 mm length lying across the bed. The waist
is then a vertical prism and the sockets are vertical pockets. No support.

The SHARED wr_* block is defined identically in wrist_hub.py, wrist_roll.py
and forearm.py.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_upper_arm'
BODY_NAME = 'upper_arm'
PREFIX = 'ua_'
WRIST = 'wr_'
STYLE = 'sty_'
PHASES = ['link form', 'elbow sockets + bolt', 'shoulder sockets',
          'cable route', 'finish', 'side panels']
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A link is light.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.design_rules import FASTENER_MM as _FASTENERS  # noqa: E402
from lib.palette import hints_for  # noqa: E402
import lib.facets as F  # noqa: E402

_M3 = _FASTENERS['M3']
APPEARANCE_HINTS = hints_for('upper_arm')


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def wrist(name, expr, comment='', units='mm'):
        _set(WRIST + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    def sval(name):
        return ups.itemByName(STYLE + name).value

    # --- SHARED joint contract ----------------------------------------------
    wrist('pivot_af', '16.0 mm', 'hex socket across flats - SHARED')
    wrist('straddle', '24.0 mm', 'the width a fork straddles - SHARED')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('facet', '4.0 mm', '45 deg chamfer on outer edges - _style.md rule 1')

    # --- fits ----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')

    # --- link -----------------------------------------------------------------
    param('l1', '125.0 mm',
          'J2 to J3. Was 85. Shortened 2026-08-26 to match the reference arm\'s\n'
          '           proportions - see specs/robotarm/_assembly.md "SUPERSEDED".\n'
          '           Everything outboard of the elbow translates 1:1 with fa_l2, so\n'
          '           the pair 65/45 takes J3 from 80 % of duty to 61 % and BUYS the\n'
          '           section growth below rather than costing anything.')
    param('half_x', WRIST + 'straddle / 2', 'derived: what the forks straddle')
    param('socket_d', '3.4 mm', 'hex socket depth into each end face')
    # CAP ON waist_z: the link is two drums joined by a CONCAVE arc, so the
    # waist must stay under drum_r or the blend inverts and the build asserts
    # ('no concave arc joins drums of r 11.0 ... at a 14.0 waist'). Making the
    # link visually chunkier past 20 mm therefore means growing the DRUMS, and
    # ua_drum_r is locked to fa_elbow_clear - see the comment below.
    param('drum_r', '13.0 mm',
          'radius of the drum at each joint. NOT FREE: the forearm cuts its own\n'
          '           clearance at fa_elbow_clear = 13.4 about J3, so this plus the 0.4\n'
          '           running gap is exactly that. Grow it and the forearm is wrong.')
    param('waist_z', '12.0 mm',
          'half height of the link between the drums. Was 9.0 (an 18 mm link);\n'
          '           24 mm, against the r 13.0 drums that now allow it. Grown WITH the duct\n'
          '           below, not instead of it - a taller box beam is bulkier to look at,\n'
          '           stiffer, and costs almost no mass. Filling it solid would cost\n'
          '           mass for nothing, since the plastic is nowhere near a stress limit.')
    param('duct_z', '9.5 mm',
          'half height of the cable duct. Sized to LIGHTEN, not just to pass a\n'
          '           loom: at 5.0 this link came out 31 g printed, heavier than the\n'
          '           forearm that carries a whole wrist. The duct runs the full length\n'
          '           and hollows the drums on its way through, so it is the only\n'
          '           lightening feature the part needs. 2 mm of rail top and bottom.')
    param('duct_x', '7.0 mm', 'half width of the cable duct')
    # THE RETENTION BOLT. Read from design_rules, not typed: j3_gear cuts the
    # matching clearance and j3_axle taps for the same screw, so this is a
    # three-file number and the one thing this project reliably gets wrong is
    # a datum only one file reads. The assert at the bottom checks j3_gear
    # agrees whenever it is in the same document.
    param('bolt_clear', '%.4f mm' % _M3['clearance'],
          'M3 clearance - lib/design_rules.py FASTENER_MM. The elbow retention\n'
          '           bolt runs the full width down the J3 axis, through the duct,\n'
          '           from j3_gear into j3_axle.')
    # SIDE PANELS, 2026-09-28. The flanks were two 125 mm blank walls - the
    # largest plain faces on the arm. A shallow stadium pocket with a crisp
    # rim reads as machined, takes a little mass out, and prints fine: on the
    # bed face it is a 11 mm bridge, on the top face a plain pocket.
    param('panel_d', '1.2 mm', 'side panel depth - the 5.0 side wall keeps 3.8')
    param('panel_end', '4.0 mm', 'panel ends this far clear of each drum')
    param('panel_border', '2.5 mm', 'land between the panel and the silhouette facet')
    param('panel_rim', '0.6 mm', 'chamfer on the panel rim')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild ---------------------------------------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        # SKIP THE ROOT. Once this part lives in its own saved file the root
        # component carries the DOCUMENT's name, which is COMPONENT - and a
        # root component cannot be renamed, so the rename below raised
        # "3 : root component name cannot be changed" and no part rebuilt.
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
    assert comp.name == COMPONENT, 'component came back as %r' % comp.name
    ext = comp.features.extrudeFeatures
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
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

    def extrude(profs, op, z0, dz, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0))
        inp.setDistanceExtent(False, V(dz))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    def mpt(sk, x, y, z):
        return sk.modelToSketchSpace(P3(x, y, z))

    def arc_radius(l, r_end, waist):
        """Concave arc tangent to both drums leaving `waist` at the middle."""
        return (r_end ** 2 - (l / 2.0) ** 2 - waist ** 2) / (2.0 * (waist - r_end))

    def link_profile(name, y_a, y_b, r_end, r_fil, x0, dx, op):
        """Two drums joined by tangent concave arcs - the same silhouette as the
        forearm, so the two links read as one family."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        arcs = sk.sketchCurves.sketchArcs
        half = abs(y_b - y_a) / 2.0
        mid_y = (y_a + y_b) / 2.0
        h = math.sqrt((r_fil + r_end) ** 2 - half ** 2)
        waist = h - r_fil
        assert waist > 0, 'the fillet radius pinches the link shut'

        def tangent(cy, fz):
            dy, dz = mid_y - cy, fz
            n = math.hypot(dy, dz)
            return (cy + r_end * dy / n, r_end * dz / n)

        for sz in (+1, -1):
            fz = sz * h
            ta, tb = tangent(y_a, fz), tangent(y_b, fz)
            arcs.addByThreePoints(mpt(sk, 0, ta[0], ta[1]),
                                  mpt(sk, 0, mid_y, sz * waist),
                                  mpt(sk, 0, tb[0], tb[1]))
        # THE DRUMS ARE 12-GON ARCS (_style.md rule 6, lib/facets): vertices on
        # the drum circle, so nothing grows past drum_r and the forearm's
        # clearance cut still holds; one on the link axis, so they line up
        # with the hex sockets' corners.
        n_facets = 0
        for cy, other in ((y_a, y_b), (y_b, y_a)):
            up, dn = tangent(cy, h), tangent(cy, -h)
            via = 0.0 if cy > other else math.pi
            pts = F.arc_polyline(cy, 0.0, r_end, math.atan2(up[1], up[0] - cy),
                                 math.atan2(dn[1], dn[0] - cy), via)
            for u, w in zip(pts, pts[1:]):
                sk.sketchCurves.sketchLines.addByTwoPoints(mpt(sk, 0, u[0], u[1]),
                                                           mpt(sk, 0, w[0], w[1]))
            n_facets += len(pts) - 1
        return extrude(profiles(sk, expected=1), op, x0, dx, name), waist, n_facets

    def hex_socket(name, y_c, sign):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        r_c = wval('pivot_af') / 2 / math.cos(math.pi / 6)
        pts = [(r_c * math.cos(2 * math.pi * i / 6), r_c * math.sin(2 * math.pi * i / 6))
               for i in range(6)]
        for i in range(6):
            u, w = pts[i], pts[(i + 1) % 6]
            lines.addByTwoPoints(mpt(sk, 0, y_c + u[0], u[1]),
                                 mpt(sk, 0, y_c + w[0], w[1]))
        if sign > 0:
            return extrude(profiles(sk, expected=1), CUT,
                           PREFIX + 'half_x', '-' + PREFIX + 'socket_d', name)
        return extrude(profiles(sk, expected=1), CUT,
                       '-' + PREFIX + 'half_x', PREFIX + 'socket_d', name)

    def yz_circle(name, y_c, z_c, d, x0, dx, op):
        """A cylinder on an axis parallel to X. The bolt bore is the only one."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, y_c, z_c), d / 2)
        return extrude(profiles(sk, expected=1), op, x0, dx, name)

    def xz_rect(name, x0, x1, z0, z1, y0, dy, op):
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, 0, z0), mpt(sk, x1, 0, z1))
        return extrude(profiles(sk, expected=1), op, y0, dy, name)

    # ---- sanity, before any geometry -----------------------------------------
    L1 = val('l1')
    r_c = wval('pivot_af') / 2 / math.cos(math.pi / 6)
    assert val('drum_r') >= r_c + val('wall'), (
        'the drum is %.2f but a %.1f af socket needs %.2f of circumradius plus a '
        'wall' % (val('drum_r') * 10, wval('pivot_af') * 10, r_c * 10))
    socket_wall = val('half_x') - val('socket_d') - val('duct_x')
    assert socket_wall >= val('wall') - 1e-9, (
        'only %.2f mm of wall between the cable duct and the hex sockets'
        % (socket_wall * 10))
    rail = val('waist_z') - val('duct_z')
    assert rail >= val('wall') - 1e-9, (
        'the duct leaves only %.2f mm of rail at the waist' % (rail * 10))
    # The bolt bore must land INSIDE the duct's cross-section. If it did not,
    # it would drill two blind pockets into solid instead of one through hole,
    # and the screw would have nowhere to go.
    assert val('bolt_clear') / 2 < min(val('duct_x'), val('duct_z')), (
        'the %.2f bolt bore is wider than the %.1f x %.1f duct it has to pass '
        'through' % (val('bolt_clear') * 10, val('duct_x') * 20, val('duct_z') * 20))
    socket_floor_wall = (r_c - val('bolt_clear') / 2)
    assert socket_floor_wall >= val('wall') - 1e-9, (
        'the bolt bore leaves only %.2f mm of hex socket floor'
        % (socket_floor_wall * 10))

    # ---- phase 1: link form ----------------------------------------------------
    t0 = design.timeline.count
    r_fil = arc_radius(L1, val('drum_r'), val('waist_z'))
    assert r_fil > 0, 'no concave arc joins drums of r %.1f over %.1f at a %.1f waist' % (
        val('drum_r') * 10, L1 * 10, val('waist_z') * 10)
    _, waist, n_drum_facets = link_profile('link', 0.0, -L1, val('drum_r'), r_fil,
                            '-' + PREFIX + 'half_x', '2 * ' + PREFIX + 'half_x', NEW)
    group(t0, PHASES[0])

    # ---- phases 2 and 3: the two joints ------------------------------------------
    for phase, y_c, tag in ((1, 0.0, 'j3'), (2, -L1, 'j2')):
        t = design.timeline.count
        for sx in (-1, 1):
            hex_socket('socket_%s_%d' % (tag, sx), y_c, sx)
        if tag == 'j3':
            # ONE cut, right across. The duct is already open in the middle,
            # so this only has to make it through the two socket floors - but
            # cutting it as a single full-width cylinder is what keeps it on
            # the axis by construction rather than by two numbers agreeing.
            yz_circle('elbow_bolt_bore', y_c, 0.0, val('bolt_clear'),
                      '-' + PREFIX + 'half_x', '2 * ' + PREFIX + 'half_x', CUT)
        group(t, PHASES[phase])

    # ---- phase 4: cable route ------------------------------------------------------
    t3 = design.timeline.count
    # OUT THROUGH BOTH DRUMS. Until 2026-09-27 this ran axis to axis, y -l1..0,
    # and both drums were SOLID past their axes: a closed tunnel with no way
    # in or out, while specs/robotarm/_harness.md routed the loom through it
    # and tied off at its "mouths". _check_bits found it - duct_grommet sat in
    # solid. Now it breaks out of each drum's end, so the J2 and J3 service
    # loops leave the link along its own axis. The side walls beside it are
    # unchanged (the socket_wall assert above), and at J3 the elbow bolt
    # still crosses it on the axis.
    xz_rect('duct', -val('duct_x'), val('duct_x'), -val('duct_z'), val('duct_z'),
            '-' + PREFIX + 'l1 - ' + PREFIX + 'drum_r - 1 mm',
            PREFIX + 'l1 + 2 * ' + PREFIX + 'drum_r + 2 mm', CUT)
    group(t3, PHASES[3])

    # ---- phase 5: finish -------------------------------------------------------------
    t4 = design.timeline.count

    # THE SIDE FACES CARRY TWO DIFFERENT KINDS OF EDGE and they want two
    # different chamfers. Probed on the built body, each face has exactly:
    #   4 x Arc3D   the silhouette outline (63.5 and 41.1 mm) - _style.md rule 1
    #               says these get the 4 mm FACET, and they never had it: this
    #               part had only the 0.4 elephant foot, so the biggest yellow
    #               volume in the arm was the one unfaceted piece in it.
    #   12 x Line3D the two hex sockets' flats, 9.7 mm each. A 4 mm chamfer on
    #               a 9.7 mm socket flat destroys the socket. These keep 0.4.
    # Select by CURVE TYPE, not by length: an arc is what a silhouette is and a
    # flat is what a socket is, and that stays true if the numbers move.
    facet_mm = sval('facet') * 10
    duct_wall_mm = (val('half_x') * 10 + val('drum_r') * 10 - facet_mm
                    - val('duct_x') * 10 - val('duct_z') * 10) / math.sqrt(2.0)
    assert duct_wall_mm >= 1.6, (
        'a %.1f mm facet leaves %.2f mm between the chamfer and the duct corner '
        '- design_rules MIN_WALL_MM is 1.6' % (facet_mm, duct_wall_mm))

    # 2026-09-29: the drums are 12-gon arcs now, so the silhouette is LINES as
    # well as arcs. Socket flats and drum facets are both lines round the same
    # two centres; they are told apart by DISTANCE from the joint axis - a
    # socket flat's midpoint sits inside the hex circumradius, a drum facet's
    # at the drum's apothem.
    split_r = (r_c + val('drum_r') * math.cos(math.pi / F.SIDES)) / 2

    def side_edges(kind):
        """Edges on either side face: 'silhouette' or 'socket'. RE-QUERIED EVERY
        TIME: a chamfer rebuilds the B-rep, so references collected before one
        are dead after it - which is what 'InternalValidationError :
        isSucceeded' means when a second chamfer is added from a stale
        collection."""
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            bb = e.boundingBox
            if abs(abs(bb.minPoint.x) - val('half_x')) > val('tol'):
                continue
            if abs(bb.maxPoint.x - bb.minPoint.x) > val('tol'):
                continue
            if e.geometry.objectType.endswith('Arc3D'):
                silhouette = True
            else:
                my = (bb.minPoint.y + bb.maxPoint.y) / 2
                mz = (bb.minPoint.z + bb.maxPoint.z) / 2
                silhouette = min(math.hypot(my, mz), math.hypot(my + L1, mz)) > split_r
            if silhouette == (kind == 'silhouette'):
                col.add(e)
        return col

    # SOCKETS FIRST, at the small chamfer. They sit in the middle of the face
    # and do not touch the silhouette, so doing them first leaves the arcs
    # untouched - and doing them SECOND does not work at all, because the
    # facet has rebuilt the body by then.
    lines = side_edges('socket')
    n_line = lines.count
    if n_line:
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            lines, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = 'socket_ef'

    arcs = side_edges('silhouette')
    n_arc = arcs.count
    assert n_arc == 2 * (2 + n_drum_facets), (
        'expected %d silhouette edges (2 waist arcs + %d drum facets, both side '
        'faces), found %d - the outline changed and the facet would land '
        'somewhere else' % (2 * (2 + n_drum_facets), n_drum_facets, n_arc))
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        arcs, V(STYLE + 'facet'), False)
    chf.add(c_inp).name = 'silhouette_facet'
    group(t4, PHASES[4])

    # ---- phase 6: side panels ---------------------------------------------------------
    t5 = design.timeline.count
    p_r = val('waist_z') - sval('facet') - val('panel_border')      # stadium half height
    p_y0 = -L1 + val('drum_r') + val('panel_end') + p_r
    p_y1 = -val('drum_r') - val('panel_end') - p_r
    assert p_y1 > p_y0, 'no room for a side panel between the drums'
    tol = val('tol')
    assert val('half_x') - val('duct_x') - val('panel_d') >= val('wall') - tol, (
        'the side panel thins the duct wall under MIN_WALL')
    for sign in (1, -1):
        # a stadium with 12-gon ends (_style.md rule 6), one closed polyline
        sk = sketch(comp.yZConstructionPlane, 'sk_side_panel_%d' % (sign + 1))
        ring = (F.arc_polyline(p_y1, 0.0, p_r, math.pi / 2, -math.pi / 2, 0.0)
                + F.arc_polyline(p_y0, 0.0, p_r, -math.pi / 2, math.pi / 2, math.pi))
        for k in range(len(ring)):
            u, w = ring[k], ring[(k + 1) % len(ring)]
            sk.sketchCurves.sketchLines.addByTwoPoints(mpt(sk, 0, u[0], u[1]),
                                                       mpt(sk, 0, w[0], w[1]))
        if sign > 0:
            extrude(profiles(sk), CUT, PREFIX + 'half_x', '-' + PREFIX + 'panel_d',
                    'side_panel_%d' % (sign + 1))
        else:
            extrude(profiles(sk), CUT, '-' + PREFIX + 'half_x', PREFIX + 'panel_d',
                    'side_panel_%d' % (sign + 1))
    rim = adsk.core.ObjectCollection.create()
    for e in comp.bRepBodies.item(0).edges:
        eb = e.boundingBox
        if abs(abs(eb.minPoint.x) - val('half_x')) < tol and abs(abs(eb.maxPoint.x) - val('half_x')) < tol \
                and eb.minPoint.y > p_y0 - p_r - tol and eb.maxPoint.y < p_y1 + p_r + tol \
                and eb.minPoint.z > -p_r - tol and eb.maxPoint.z < p_r + tol:
            rim.add(e)
    assert rim.count > 0, 'no side panel rim edges found'
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(rim, V(PREFIX + 'panel_rim'), False)
    chf.add(c_inp).name = 'side_panel_rim'
    group(t5, PHASES[PHASES.index('side panels')])

    # ---- identity + diagnostics --------------------------------------------------------
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

    bb = body.boundingBox
    print('body: %r | appearance: %s' % (body.name, used))
    print('L1 %.1f | straddled BOTH ends at |x| %.1f - no prongs, no journals' % (
        L1 * 10, val('half_x') * 10))
    # THE FOREARM'S ALLOWANCE IS NOT A CONSTANT. It was printed here as a
    # hardcoded 11.4 and went stale the moment ua_drum_r moved to 13.0 - the
    # geometry was right and the message said the joint interfered by 1.6 mm.
    # Read it when the forearm is in the document, and check it.
    _fa = ups.itemByName('fa_elbow_clear')
    _allow = _fa.value * 10 if _fa is not None else val('drum_r') * 10 + 0.4
    assert _allow >= val('drum_r') * 10 + 0.4 - 1e-9, (
        'fa_elbow_clear is %.2f and this drum is r %.2f - the forearm cuts less '
        'clearance than the upper arm needs and they will foul at J3'
        % (_allow, val('drum_r') * 10))
    print('drums r %.1f (forearm allows %.1f about J3, so %.1f of running gap)%s' % (
        val('drum_r') * 10, _allow, _allow - val('drum_r') * 10,
        '' if _fa is not None else '  [fa not in doc - allowance ASSUMED]'))
    print('silhouette: r %.1f drums joined by r %.1f arcs, waist half %.2f' % (
        val('drum_r') * 10, r_fil * 10, waist * 10))
    print('4 hex sockets %.1f af x %.1f deep, %.2f of wall beside the duct' % (
        wval('pivot_af') * 10, val('socket_d') * 10, socket_wall * 10))

    # ---- the elbow retention bolt, checked against the parts it joins -------
    # Same pattern as fa_elbow_clear above: read the OTHER file's parameter
    # when it is in the document rather than restating its number here. A
    # bolt whose three holes are three independently typed 3.4s is exactly
    # the failure this project keeps paying for.
    _jg = ups.itemByName('jg_bolt_clear')
    if _jg is not None:
        assert abs(_jg.value - val('bolt_clear')) < 1e-9, (
            'jg_bolt_clear is %.2f and ua_bolt_clear is %.2f - the retention '
            'bolt does not have one diameter'
            % (_jg.value * 10, val('bolt_clear') * 10))
    _ja_sock = ups.itemByName('ja_socket_d')
    if _ja_sock is not None:
        assert abs(_ja_sock.value - val('socket_d')) < 1e-9, (
            'ja_socket_d is %.2f and ua_socket_d is %.2f - j3_axle\'s hex does '
            'not match the socket it bottoms in'
            % (_ja_sock.value * 10, val('socket_d') * 10))

    # WHAT LENGTH SCREW TO BUY. Stated, because nothing else in the repo says
    # it and a bolt that is 5 mm short is a joint that comes apart on the
    # bench with every gate passing.
    _need = [n for n in ('jg_face', 'jg_bolt_head_d', 'jg_collar_l',
                         'wr_reach', 'ja_tap_l') if ups.itemByName(n) is None]
    if not _need:
        def _g(n):
            return ups.itemByName(n).value * 10
        head_to_hex = _g('jg_face') - _g('jg_bolt_head_d') + _g('jg_collar_l') + _g('wr_reach')
        across = 2 * (val('half_x') - val('socket_d')) * 10
        to_tap = head_to_hex + across
        full = to_tap + _g('ja_tap_l')
        min_eng = to_tap + 1.5 * val('bolt_clear') * 10
        print('elbow bolt: %.1f clear on the J3 axis, through the duct. From the '
              'head underside:' % (val('bolt_clear') * 10))
        print('   %.1f through j3_gear + %.1f across this part = %.1f to the '
              'j3_axle tap' % (head_to_hex, across, to_tap))
        print('   M3 x %.0f gives 1.5d of engagement, M3 x %.0f bottoms the '
              '%.1f tap - BUY M3 x %.0f'
              % (5 * round(min_eng / 5.0 + 0.499), 5 * round(full / 5.0 + 0.499),
                 _g('ja_tap_l'), 5 * round(min_eng / 5.0 + 0.499)))
    else:
        print('elbow bolt: %.1f clear on the J3 axis, through the duct. Screw '
              'length not stated - %s not in this document'
              % (val('bolt_clear') * 10, ', '.join(_need)))
    print('POLYGONAL: 12-gon drums (%d facets); %.1f mm facet on %d silhouette edges, %.1f on %d socket flats;'
          ' %.2f mm of wall left at the duct corner'
          % (n_drum_facets, sval('facet') * 10, n_arc, sval('ef') * 10, n_line, duct_wall_mm))
    print('duct %.1f x %.1f runs the full length and OUT through both drum ends, %.1f rails' % (
        val('duct_x') * 20, val('duct_z') * 20, rail * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 600, body.isValid))
