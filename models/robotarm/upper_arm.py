"""robotarm/upper_arm - Fusion MCP generating script.

Rebuilds `robotarm_upper_arm` (idempotent). Spec: specs/robotarm/upper_arm.md,
styled per specs/robotarm/_style.md.

Local frame: origin on the J3 ELBOW axis. +X along it, +Y forward toward the
wrist, +Z up. The J2 shoulder axis is at y = -ua_l1.

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
PHASES = ['link form', 'elbow sockets', 'shoulder sockets', 'cable route', 'finish']
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A link is light.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
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
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild ---------------------------------------------------
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
        for cy, out in ((y_a, y_a + r_end if y_a > y_b else y_a - r_end),
                        (y_b, y_b + r_end if y_b > y_a else y_b - r_end)):
            up, dn = tangent(cy, h), tangent(cy, -h)
            arcs.addByThreePoints(mpt(sk, 0, up[0], up[1]),
                                  mpt(sk, 0, out, 0.0),
                                  mpt(sk, 0, dn[0], dn[1]))
        return extrude(profiles(sk, expected=1), op, x0, dx, name), waist

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

    # ---- phase 1: link form ----------------------------------------------------
    t0 = design.timeline.count
    r_fil = arc_radius(L1, val('drum_r'), val('waist_z'))
    assert r_fil > 0, 'no concave arc joins drums of r %.1f over %.1f at a %.1f waist' % (
        val('drum_r') * 10, L1 * 10, val('waist_z') * 10)
    _, waist = link_profile('link', 0.0, -L1, val('drum_r'), r_fil,
                            '-' + PREFIX + 'half_x', '2 * ' + PREFIX + 'half_x', NEW)
    group(t0, PHASES[0])

    # ---- phases 2 and 3: the two joints ------------------------------------------
    for phase, y_c, tag in ((1, 0.0, 'j3'), (2, -L1, 'j2')):
        t = design.timeline.count
        for sx in (-1, 1):
            hex_socket('socket_%s_%d' % (tag, sx), y_c, sx)
        group(t, PHASES[phase])

    # ---- phase 4: cable route ------------------------------------------------------
    t3 = design.timeline.count
    xz_rect('duct', -val('duct_x'), val('duct_x'), -val('duct_z'), val('duct_z'),
            '-' + PREFIX + 'l1', PREFIX + 'l1', CUT)
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

    def side_edges(kind):
        """Edges on either side face, of one curve type. RE-QUERIED EVERY TIME:
        a chamfer rebuilds the B-rep, so references collected before one are
        dead after it - which is what 'InternalValidationError : isSucceeded'
        means when a second chamfer is added from a stale collection."""
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            bb = e.boundingBox
            if abs(abs(bb.minPoint.x) - val('half_x')) > val('tol'):
                continue
            if abs(bb.maxPoint.x - bb.minPoint.x) > val('tol'):
                continue
            if e.geometry.objectType.endswith('Arc3D') == (kind == 'arc'):
                col.add(e)
        return col

    # SOCKETS FIRST, at the small chamfer. They sit in the middle of the face
    # and do not touch the silhouette, so doing them first leaves the arcs
    # untouched - and doing them SECOND does not work at all, because the
    # facet has rebuilt the body by then.
    lines = side_edges('line')
    n_line = lines.count
    if n_line:
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            lines, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = 'socket_ef'

    arcs = side_edges('arc')
    n_arc = arcs.count
    assert n_arc == 8, (
        'expected 8 silhouette arcs across the two side faces, found %d - the '
        'outline changed and the facet would land somewhere else' % n_arc)
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        arcs, V(STYLE + 'facet'), False)
    chf.add(c_inp).name = 'silhouette_facet'
    group(t4, PHASES[4])

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
    print('POLYGONAL: %.1f mm facet on %d silhouette arcs, %.1f on %d socket flats;'
          ' %.2f mm of wall left at the duct corner'
          % (sval('facet') * 10, n_arc, sval('ef') * 10, n_line, duct_wall_mm))
    print('duct %.1f x %.1f runs the full length, hollowing both drums, %.1f rails' % (
        val('duct_x') * 20, val('duct_z') * 20, rail * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 600, body.isValid))
