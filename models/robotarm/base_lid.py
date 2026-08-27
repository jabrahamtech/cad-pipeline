"""robotarm/base_lid - closes the printed platter's electronics bay.

REPLACES the printed `legacy/exports/robotarm/base_lid_v1.step`, which cannot
be used: **it has no central opening.** Its own spec claims a Ø60 hole for the
yaw servo; the STEP was measured face-by-face on 2026-08-26 and there is
nothing in the middle at all. The SG90 has to reach z -6.90 into the platter's
column and the old lid is solid across that whole area.

Everything this part must obey comes from two MEASURED sources, not from any
spec: `specs/robotarm/base_platter_measured.md` (the platter, printed and in
hand) and a face analysis of the old lid STEP for the fixings it already
proved fit.

  disc          Ø171.75 x 3.00, sits on the platter's shelf at z 39.00 and
                finishes flush with the rim at 42.00. Kept at the OLD lid's
                measured diameter, not the Ø172.0 the recess nominally is:
                that lid was printed and fits, and 0.125 of radial clearance
                is not a number to re-derive from a drawing.
  3 x Ø9.50     at r 45.0, az 120/180/240 - the platter's Ø8.8 turret posts
                pass through on their way to the stator and the ring.
  4 x M3        at r 78.0, az 45/135/225/315, counterbored from the top so the
                heads finish under the rim.
  servo well    NEW. The stator's own central void is a Ø20 circle unioned
                with a 12.40 x 22.90 rectangle - tracked off the stator's
                case + loc cut (flange audit 2026-08-27) -
                and the SG90 case (12.20 x 22.70) drops through it. This lid
                has to clear ALL of that, not just the servo.
  cable route   NEW, and it is the same opening. The loom crosses from the
                rotating half to the fixed half at the CENTRE, where the twist
                per degree of J1 is smallest. Two zip-tie anchors beside it.
  vents         12 x Ø4 at r 62 - kept from the old lid, and they have to stay
                outside r 50 because the stator's base plate lands flat on the
                lid from r 10 to r 50 and would seal anything inside that.

Print: PETG, flat, no support. It is a 3 mm plate; the only thing to get right
is that it does not warp, so a brim.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_base_lid'
BODY_NAME = 'base_lid'
PREFIX = 'bl_'
STYLE = 'sty_'
PH_DISC = 'disc'
PH_OPEN = 'servo + cable opening'
PH_FIX = 'fixings'
PH_VENT = 'vents'
PHASES = [PH_DISC, PH_OPEN, PH_FIX, PH_VENT]
MATERIAL_NAME = 'PET Plastic'

POST_AZ = (120.0, 180.0, 240.0)
SCREW_AZ = (45.0, 135.0, 225.0, 315.0)
VENT_N = 12

# MEASURED off the built turntable_stator, 2026-08-26. The lid's opening must
# contain all of this or the two parts fight over the same servo.
#
# AND CONTAIN IS AN INTERVAL, NOT A LENGTH. These were measured as sizes and
# checked as sizes - open_y 26.0 >= well_y 22.8 + 1.0, comfortably true - while
# the opening was cut about the origin and the well sits at y +5.20, because
# ts_shaft_off moved it there on 2026-08-26 and this file was never told. The
# lid masked 3.60 of the well and the SG90 case fouled the lid by 3.50.
# _check_j1 found it. Every comparison below is now lo/hi, not length.
STATOR_VOID_R = 10.00        # the circular part
STATOR_WELL_X = 12.40        # the rectangular part (case 12.2 + loc)
STATOR_WELL_Y = 22.90        # case 22.7 + loc - 2026-08-27 flange audit
STATOR_WELL_OFF_Y = 5.25     # ts_shaft_off - the well's centre, off the axis
STATOR_PLATE_IR = 10.00      # stator base plate lands on the lid from here...
STATOR_PLATE_OR = 50.00      # ...to here. Nothing may vent under it.
SG90_CASE_W = 12.20          # TowerPro D - 2026-08-27 flange audit
SG90_CASE_L = 22.70          # TowerPro B


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

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    # --- MEASURED interface. Not ours to choose. -----------------------------
    param('dia', '171.75 mm',
          'MEASURED off the printed lid STEP. The recess wall is nominally\n'
          '           172.0, so this is 0.125 of radial clearance - tight, and proven\n'
          '           by the fact that the old lid was printed and fits.')
    param('t', '3.00 mm', 'MEASURED. Shelf z 39.00 + 3.00 finishes flush at the 42.00 rim')
    param('post_r', '45.00 mm', 'MEASURED. The platter\'s 3 turret posts')
    param('post_clear_d', '9.50 mm', 'MEASURED. Clearance over the platter\'s 8.8 posts')
    param('screw_r', '78.00 mm', 'MEASURED. 4 x M3 into the platter\'s lid inserts')
    param('screw_d', '3.40 mm', 'M3 clearance')
    param('head_d', '6.50 mm', 'M3 socket head + clearance')
    param('head_z', '1.20 mm', 'head recess, leaving 1.80 of lid under it')

    # --- NEW ------------------------------------------------------------------
    param('open_x', '22.00 mm',
          'servo + cable opening, across the flats of the SG90. Must contain\n'
          '           the STATOR\'S void (a 20.0 circle unioned with a 12.40 x 22.90\n'
          '           rectangle), not merely the servo - the two parts share this hole.')
    param('open_y', '31.00 mm',
          'the long way. WAS 26.00 and centred, which masked the servo well.\n'
          '           Three things set it now: the stator\'s Ø20 void ON the axis,\n'
          '           its 12.40 x 22.90 well at y +5.25, and the loom slot\'s inner\n'
          '           radius at 13.0, which this opening has to reach PAST rather\n'
          '           than stop short of - see the merge note below.')
    param('open_off_y', '2.00 mm',
          'the opening\'s centre, off the J1 axis. NOT a style choice and NOT\n'
          '           ts_shaft_off either. The void union runs y -10.00..+16.60 and\n'
          '           the loom slot wants the astern edge at or past -13.00, so the\n'
          '           opening runs -13.50..+17.50. All three asserted below.')
    param('open_r', '3.00 mm', 'corner radius on the opening')
    param('vent_r', '62.00 mm', 'MEASURED off the old lid - and it has to stay\n'
                                '           outside the stator\'s 50.0 footprint anyway')
    param('vent_d', '4.00 mm', 'MEASURED off the old lid')
    param('band_i', '54.00 mm', 'recessed band, inner - styling, and it puts a\n'
                                '           shadow line between the turntable and the vents')
    param('band_o', '70.00 mm', 'recessed band, outer')
    param('band_z', '0.80 mm', 'band depth. Cosmetic only; leaves 2.20 of lid')
    param('tie_w', '2.00 mm', 'zip-tie slot width - _assembly.md wants an anchor\n'
                              '           at every loom entry')
    param('tie_l', '4.00 mm', 'zip-tie slot length')
    param('tie_r', '20.00 mm', 'zip-tie slots this far out, either side of the opening')
    # THE LOOM. Five servos live above J1 - J2 MG995, J3/J4 MG90S, J5 SG90 and
    # the effector SG90 - so fifteen leads cross here. They cannot pass beside
    # the yaw servo: turntable_stator's well is 12.40 x 22.90 on a 12.20 x
    # 22.70 case, a tenth of a millimetre each side. This slot is the bottom of
    # a three-part route: base_lid -> turntable_stator (same slot) -> the space
    # under the rotor -> shoulder_bracket's own window, which turns with J1.
    param('cable_ir', '13.00 mm', 'MUST MATCH ts_cable_ir - asserted below')
    param('cable_or', '20.00 mm', 'MUST MATCH ts_cable_or - asserted below')
    param('cable_az', '270.00 deg', 'astern of the arm', 'deg')
    param('cable_deg', '70.00 deg', 'MUST MATCH ts_cable_deg', 'deg')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')
    style('ef', '0.4 mm', 'elephant-foot chamfer - design_rules')

    # ---- idempotent rebuild. RENAME FIRST, THEN DELETE. ---------------------
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
    ext = comp.features.extrudeFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mm(x):
        return '%.4f mm' % x

    def pt(sk, x, y):
        return sk.modelToSketchSpace(P3(x / 10.0, y / 10.0, 0))

    def one(sk):
        assert sk.profiles.count == 1, (
            sk.name + ': expected 1 profile, got %d' % sk.profiles.count)
        c = adsk.core.ObjectCollection.create()
        c.add(sk.profiles.item(0))
        return c

    def extrude(profs, op, z0, dz, name, targets=None):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0)))
        inp.setDistanceExtent(False, V(mm(dz)))
        if op != NEW:
            inp.participantBodies = targets if targets is not None else [
                comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def circle(name, x, y, d, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, x, y), d / 20.0)
        return extrude(one(sk), op, z0, dz, name, targets)

    def rounded_rect(name, hx, hy, r, z0, dz, op, targets=None, off_y=0.0):
        """Rounded rectangle from 4 arcs and 4 lines, centred on (0, off_y).
        addTwoPointRectangle plus a fillet would need edge picks on a sketch
        that has not been extruded yet.

        off_y is not decoration. The servo opening this cuts is shared with
        turntable_stator's well, which sits ts_shaft_off off the axis so the
        SG90's SHAFT lands on it. Centred on the origin, this hole masked the
        far end of that well - see the header."""
        sk = sketch(name)
        lines = sk.sketchCurves.sketchLines
        arcs = sk.sketchCurves.sketchArcs
        cy_hi, cy_lo = off_y + hy - r, off_y - (hy - r)
        corners = [(hx - r, cy_hi, 0.0), (-(hx - r), cy_hi, 90.0),
                   (-(hx - r), cy_lo, 180.0), (hx - r, cy_lo, 270.0)]
        pts = []
        for cx, cy, a0 in corners:
            for a in (a0, a0 + 90.0):
                pts.append((cx + r * math.cos(math.radians(a)),
                            cy + r * math.sin(math.radians(a))))
        for i in range(4):
            s = pts[i * 2 + 1]
            e = pts[(i * 2 + 2) % 8]
            lines.addByTwoPoints(pt(sk, s[0], s[1]), pt(sk, e[0], e[1]))
        for i, (cx, cy, a0) in enumerate(corners):
            arcs.addByCenterStartSweep(pt(sk, cx, cy),
                                       pt(sk, pts[i * 2][0], pts[i * 2][1]),
                                       math.radians(90.0))
        return extrude(one(sk), op, z0, dz, name, targets)

    def xy_arc(name, r_in, r_out, mid, half, z0, dz, op, targets=None):
        """Annular sector with square ends. Four curves closed by hand - Fusion
        will not infer a sector from two full circles."""
        sk = sketch(name)
        arcs = sk.sketchCurves.sketchArcs
        lines = sk.sketchCurves.sketchLines
        a0, a1 = mid - half, mid + half

        def p(r, a):
            return pt(sk, r * math.cos(a), r * math.sin(a))

        arcs.addByThreePoints(p(r_out, a0), p(r_out, mid), p(r_out, a1))
        arcs.addByThreePoints(p(r_in, a0), p(r_in, mid), p(r_in, a1))
        lines.addByTwoPoints(p(r_in, a0), p(r_out, a0))
        lines.addByTwoPoints(p(r_in, a1), p(r_out, a1))
        return extrude(one(sk), op, z0, dz, name, targets)

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    # ---- sanity, in MILLIMETRES, before any geometry ------------------------
    # fusion/PLAYBOOK.md: convert once into _mm names. val() is centimetres and
    # comparing one against a bare 1.6 has now cost this project four bugs.
    t_mm = val('t') * 10
    dia_mm = val('dia') * 10
    ox_mm, oy_mm = val('open_x') * 10, val('open_y') * 10
    post_r_mm, post_d_mm = val('post_r') * 10, val('post_clear_d') * 10
    screw_r_mm = val('screw_r') * 10
    vent_r_mm, vent_d_mm = val('vent_r') * 10, val('vent_d') * 10
    band_i_mm, band_o_mm = val('band_i') * 10, val('band_o') * 10
    WALL_MM = 1.6

    # INTERVALS, both sides, every time. A length comparison cannot see an
    # offset, and offsets are exactly what gets added late.
    off_mm = val('open_off_y') * 10
    op_lo, op_hi = off_mm - oy_mm / 2, off_mm + oy_mm / 2
    # what the opening has to contain, as ONE interval: the circular void sits
    # on the axis, the well sits at STATOR_WELL_OFF_Y, and neither one's centre
    # is the answer.
    need_lo = min(-STATOR_VOID_R, STATOR_WELL_OFF_Y - STATOR_WELL_Y / 2) - 0.5
    need_hi = max(STATOR_VOID_R, STATOR_WELL_OFF_Y + STATOR_WELL_Y / 2) + 0.5
    assert op_lo <= need_lo and op_hi >= need_hi, (
        'the opening runs y %.2f..%.2f and the stator\'s void runs %.2f..%.2f '
        '- it wants open_y %.2f centred at %.2f'
        % (op_lo, op_hi, need_lo, need_hi, need_hi - need_lo,
           (need_hi + need_lo) / 2))
    well_lo = STATOR_WELL_OFF_Y - STATOR_WELL_Y / 2
    well_hi = STATOR_WELL_OFF_Y + STATOR_WELL_Y / 2
    assert ox_mm / 2 >= STATOR_VOID_R + 0.5, (
        'the opening is %.1f across and the stator\'s circular void alone is '
        'Ø%.1f - the lid would mask it' % (ox_mm, STATOR_VOID_R * 2))
    assert ox_mm >= STATOR_WELL_X + 1.0, (
        'the opening is %.1f across against the stator\'s %.1f well - the lid '
        'pinches the servo pocket' % (ox_mm, STATOR_WELL_X))
    cable_gap = (ox_mm - SG90_CASE_W) / 2
    assert cable_gap >= 3.0, (
        'only %.1f mm each side of the SG90 case for the loom - it crosses J1 '
        'here and nowhere else' % cable_gap)
    assert vent_r_mm - vent_d_mm / 2 > STATOR_PLATE_OR + WALL_MM, (
        'vents at r %.1f are under the stator base plate, which lands flat on '
        'this lid out to r %.1f and would seal them' % (vent_r_mm, STATOR_PLATE_OR))
    assert vent_r_mm + vent_d_mm / 2 + WALL_MM < screw_r_mm - val('head_d') / 2 * 10, \
        'the vent ring runs into the M3 head recesses'
    assert band_i_mm < vent_r_mm - vent_d_mm / 2 and band_o_mm > vent_r_mm + vent_d_mm / 2, \
        'the recessed band does not contain the vent ring'
    assert t_mm - val('band_z') * 10 >= 2.0, 'the cosmetic band leaves under 2 mm of lid'
    assert t_mm - val('head_z') * 10 >= 1.6, 'the head recess leaves under a wall'
    assert post_r_mm + post_d_mm / 2 < dia_mm / 2, 'the post holes run off the lid'
    assert screw_r_mm + val('head_d') / 2 * 10 < dia_mm / 2 - 1.0, \
        'the M3 heads run off the edge'

    # ---- phase 1: the disc ---------------------------------------------------
    t0 = design.timeline.count
    circle('disc', 0, 0, dia_mm, 0.0, t_mm, NEW)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    group(t0, PH_DISC)

    # ---- phase 2: the servo + cable opening ---------------------------------
    # ONE opening does both jobs. The loom crosses from the rotating half to
    # the fixed half here because this is the axis of rotation - the twist per
    # degree of J1 is smallest at r = 0, which is why _assembly.md can cap J1
    # at +-90 on loom twist rather than on anything mechanical.
    t1 = design.timeline.count
    rounded_rect('servo_open', ox_mm / 2, oy_mm / 2, val('open_r') * 10,
                 -1.0, t_mm + 2.0, CUT, [body], off_y=off_mm)
    for sx in (-1, 1):
        sk = sketch('tie_%d' % (sx > 0))
        x = sx * val('tie_r') * 10
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(sk, x - val('tie_w') * 5, -val('tie_l') * 5),
            pt(sk, x + val('tie_w') * 5, val('tie_l') * 5))
        extrude(one(sk), CUT, -1.0, t_mm + 2.0, 'tie_%d' % (sx > 0), [body])
    # the loom slot, and it has to line up with the stator's. A comment saying
    # MUST MATCH is not a mechanism - when the stator is in the document, check.
    c_ir_mm, c_or_mm = val('cable_ir') * 10, val('cable_or') * 10
    for _theirs, _mine in (('ts_cable_ir', 'cable_ir'), ('ts_cable_or', 'cable_or'),
                           ('ts_cable_az', 'cable_az'), ('ts_cable_deg', 'cable_deg')):
        _p = ups.itemByName(_theirs)
        if _p is not None:
            assert abs(_p.value - val(_mine)) < 1e-9, (
                '%s is %.3f and this lid says %.3f - the two halves of the loom '
                'route would not line up' % (_theirs, _p.value, val(_mine)))
    assert c_or_mm < STATOR_PLATE_OR, (
        'the cable slot reaches r %.1f, past the stator plate at r %.1f'
        % (c_or_mm, STATOR_PLATE_OR))
    # THESE TWO OPENINGS MUST MERGE, AND "OR LEAVE A FULL WALL" IS NOT THE
    # ALTERNATIVE IT LOOKS LIKE. The loom slot is an ARC: its inner edge is at
    # r 13.0 on the centreline but only y -10.65 at its angular ends, so a
    # straight opening edge anywhere between those two values cuts the strip
    # BETWEEN them free at the ends while leaving it standing in the middle.
    # Offsetting the opening to +3.30 did exactly that and dropped a 48 mm3
    # sliver, 1.8 mm wide, out of the lid - and a 1.8 mm rib would have passed
    # a MIN_WALL check, because the rib was never the problem. It was attached
    # to nothing.
    #
    # So the rule is a real overlap, not a wall: the opening reaches at least
    # 0.5 past r 13.0 and the two become one D-shaped hole, which is what this
    # part always intended. The STATOR still separates servo from loom: its
    # well reaches 11.40, it is 4 mm thick, and it keeps a real 1.6 mm wall.
    #
    # A body count is what caught this, not a dimension. Keep asserting it.
    merge = -op_lo - c_ir_mm
    assert merge >= 0.5, (
        'the servo opening ends at y %.2f and the loom slot starts at r %.2f, '
        'so they overlap by %.2f - the opening must reach at least 0.5 PAST the '
        'slot\'s inner radius' % (op_lo, c_ir_mm, merge))
    # MILLIMETRES. xy_arc feeds pt(), and pt() is the one that divides by ten.
    # Handing it centimetres built the slot at r 1.3 and it cut nothing at all -
    # the tell was the volume coming back byte-identical. fusion/PLAYBOOK.md.
    _before = body.volume * 1000
    xy_arc('cable_window', c_ir_mm, c_or_mm,
           val('cable_az'), val('cable_deg') / 2.0,
           -1.0, t_mm + 2.0, CUT, [body])
    assert body.volume * 1000 < _before - 100.0, (
        'the loom slot removed only %.1f mm3 - it is not where it is meant to be'
        % (_before - body.volume * 1000))
    group(t1, PH_OPEN)

    # ---- phase 3: fixings ----------------------------------------------------
    t2 = design.timeline.count
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        circle('post_%d' % i, post_r_mm * math.cos(a), post_r_mm * math.sin(a),
               post_d_mm, -1.0, t_mm + 2.0, CUT, [body])
    for i, az in enumerate(SCREW_AZ):
        a = math.radians(az)
        x, y = screw_r_mm * math.cos(a), screw_r_mm * math.sin(a)
        circle('screw_%d' % i, x, y, val('screw_d') * 10, -1.0, t_mm + 2.0, CUT, [body])
        circle('head_%d' % i, x, y, val('head_d') * 10,
               t_mm, -val('head_z') * 10, CUT, [body])
    group(t2, PH_FIX)

    # ---- phase 4: vents + the cosmetic band ---------------------------------
    t3 = design.timeline.count
    sk = sketch('band')
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, 0, 0), band_o_mm / 10.0)
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, 0, 0), band_i_mm / 10.0)
    # TWO concentric circles give TWO profiles - the inner disc AND the
    # annulus between them. "smaller than the outer disc" selects both, which
    # recesses the whole middle of the lid instead of a band. Match the
    # annulus area itself.
    want = math.pi * (band_o_mm ** 2 - band_i_mm ** 2)
    col = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        pr = sk.profiles.item(i)
        if abs(pr.areaProperties().area * 100 - want) < want * 0.02:
            col.add(pr)
    assert col.count == 1, (
        'expected 1 annular profile of ~%.0f mm2, got %d of %d'
        % (want, col.count, sk.profiles.count))
    extrude(col, CUT, t_mm, -val('band_z') * 10, 'band', [body])
    for i in range(VENT_N):
        a = math.radians(360.0 * i / VENT_N + 15.0)
        circle('vent_%d' % i, vent_r_mm * math.cos(a), vent_r_mm * math.sin(a),
               vent_d_mm, -1.0, t_mm + 2.0, CUT, [body])
    group(t3, PH_VENT)

    # ---- identity + diagnostics ---------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got %d' % comp.bRepBodies.count
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    bb = body.boundingBox
    print('body: %r | material: %s' % (body.name, body.material.name))
    print('REPLACES the printed base_lid_v1, which has NO central opening -')
    print('  measured, not assumed: its own spec claims a 60.0 servo hole and the')
    print('  STEP has nothing in the middle. The SG90 could never have gone in.')
    print('disc %.2f x %.2f, on the platter shelf z 39.00, flush at 42.00'
          % (dia_mm, t_mm))
    print('OPENING %.1f x %.1f (r %.1f corners) - clears the stator\'s own void'
          % (ox_mm, oy_mm, val('open_r') * 10))
    print('  stator void: %.1f circle + %.1f x %.1f well | SG90 case %.1f x %.1f'
          % (STATOR_VOID_R * 2, STATOR_WELL_X, STATOR_WELL_Y, SG90_CASE_W, SG90_CASE_L))
    print('LOOM SLOT: r %.1f..%.1f, %.0f deg at az %.0f - matches ts_cable_*'
          % (c_ir_mm, c_or_mm, val('cable_deg') * 180 / math.pi,
             val('cable_az') * 180 / math.pi))
    print('  15 leads cross J1 (5 servos above it). They CANNOT go beside the')
    print('  yaw servo: the stator\'s well is %.2f x %.2f on a %.2f case.'
          % (STATOR_WELL_X, STATOR_WELL_Y, SG90_CASE_W))
    print('fixings: 3 x %.2f at r %.1f az %s | 4 x M3 at r %.1f az %s, heads %.1f x %.1f'
          % (post_d_mm, post_r_mm, POST_AZ, screw_r_mm, SCREW_AZ,
             val('head_d') * 10, val('head_z') * 10))
    print('vents: %d x %.1f at r %.1f - OUTSIDE the stator\'s %.1f footprint'
          % (VENT_N, vent_d_mm, vent_r_mm, STATOR_PLATE_OR))
    print('band: r %.1f..%.1f recessed %.1f, leaving %.1f of lid'
          % (band_i_mm, band_o_mm, val('band_z') * 10, t_mm - val('band_z') * 10))
    print('zip-tie anchors: 2 x %.1f x %.1f at x +-%.1f'
          % (val('tie_w') * 10, val('tie_l') * 10, val('tie_r') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | printed ~%.1f g PETG | valid: %s'
          % (body.volume * 1000, body.volume * 1000 * 0.00127 * 0.65, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d'
          % (comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
