"""robotarm/turntable_clip - Fusion MCP generating script.

Rebuilds `robotarm_turntable_clip` (idempotent). Spec: specs/robotarm/_state.md.

One of three. Each holds a 608ZZ on a horizontal radial stub axle so its outer
race rolls under the turret cap's track. Three of these carry the whole arm.

Local frame: origin AT THE AXLE CENTRE. +X radially OUTWARD, toward the base
wall; +Z up; +Y tangential. base_shell places three of these at 120 deg on
tt_roller_r, at tt_axle_z. Nothing in this file knows the yaw axis exists,
which is the point: the clip is the same part at every station.

THE AXLE IS SINGLE-SIDED, AND THAT IS FORCED. A yoke straddling the bearing
would have to spread 3 mm per cheek to let a 608 in - not something a 4 mm
PETG cheek does without cracking. So one cheek, one stub, and an M3 with a
washer clamping the INNER race against a raised collar. The collar is the
whole trick: without it the outer race rubs the cheek and the roller stops
rolling.

Loads are not the problem here. Worst case is roughly 5 N on one roller, on a
Oe7.9 stub cantilevered 8 mm - under a megapascal of bending. What this part
actually has to get right is the two clearances: the outer race must not touch
the cheek, and the top of the clip must stay clear of the cap above it.

Print orientation: BACK FACE ON THE BED, built +X, so the stub axle grows
straight up out of the plate as a solid round column with no support and no
seam across the bearing seat. The bolt holes come out horizontal, which is
fine - they are clearance, not a fit.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_turntable_clip'
BODY_NAME = 'turntable_clip'
PREFIX = 'tk_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_FORM = 'clip form'
PH_AXLE = 'axle'
PH_BOLTS = 'base interface'
PHASES = [PH_FORM, PH_AXLE, PH_BOLTS]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A clip is structure, so it is dark.
APPEARANCE_HINTS = [('plastic', 'black'), ('paint', 'black'), ('black',), ('plastic',)]


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

    def turret(name, expr, comment='', units='mm'):
        _set(TURRET + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    # ---- the SHARED turret contract, the members this part consumes ---------
    # Every member is defined identically wherever it appears. turret_cap.py
    # carries the full block; this file carries the roller and clip half of it.
    turret('roller_r', '30.0 mm', 'yaw axis to the MID-PLANE of each 608ZZ')
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - the rolling surface')
    turret('roller_w', '7.0 mm', '608ZZ width - lies RADIALLY, the axle is radial')
    turret('cap_t', '7.0 mm', 'turret cap thickness - SHARED, see turret_cap.py')
    turret('axle_z', '-(' + TURRET + 'cap_t + ' + TURRET + 'roller_od / 2)',
           'derived: roller axle height in the CAP\'s frame. Never typed.')
    turret('pad_r', '38.0 mm',
           'yaw axis to the FLAT pad on the inside of the base wall that this clip\n'
           '           bolts to. Flat, not cylindrical: base_shell puts three inward\n'
           '           bosses there, and a flat pad is the only back face a printed\n'
           '           plate can actually sit on.')
    turret('clip_pitch', '14.0 mm',
           'the two clip bolts, vertical, straddling the axle. NOT bigger: at 16 the\n'
           '           top of the clip reaches z -6.5 and the cap above it starts at\n'
           '           -7.0. Asserted below.')
    turret('clip_clear', '3.4 mm', 'M3 clearance, in THIS part')
    turret('clip_pilot', '2.5 mm', 'M3 self-tapper into the base wall boss')
    turret('collar_h', '0.5 mm',
           'how far the bearing seat stands proud of the cheek. Small, but it is the\n'
           '           only thing keeping the OUTER race off the cheek - without it\n'
           '           the roller does not roll, it rubs.')
    turret('axle_d', '7.9 mm',
           '608 bore 8.0 - 0.1. A press, because a roller axle that turns in its own\n'
           '           clip wears the print, not the bearing.')

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm',
          'silhouette corner radius - SHARED. This file wants 3.0 and MUST NOT get\n'
          '           it by writing 3.0 here: a fillet stores a live reference to the\n'
          '           parameter, so redefining it re-cut every corner in every part\n'
          '           already in the document. It cost pruner_shell 1352 mm3, the\n'
          '           forearm 209 and the shoulder bracket 220, silently, with every\n'
          '           part still reporting isValid True. See fusion/PLAYBOOK.md.')

    # ---- fits and local geometry --------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('free', '0.4 mm', 'free fit - design_rules')
    param('plate_t', '4.0 mm',
          'back plate thickness. Set by the M3 clearance holes through it and by\n'
          '           the stub axle root, not by strength.')
    param('collar_d', '12.5 mm',
          '608ZZ inner race OD 12.0 + 0.5. The seat touches ONLY the inner race.')
    param('axle_len', '8.0 mm',
          'stub length past the collar face. Bearing is 7.0, so 1.0 stands proud\n'
          '           for the washer to clamp against - the washer must land on the\n'
          '           race, never on the axle end.')
    param('screw_pilot', '2.5 mm', 'M3 self-tapper up the middle of the stub')
    param('screw_depth', '7.0 mm', 'into an axle that is 8.0 long plus the collar')
    param('half_w', '9.0 mm', 'back plate half width, tangential')
    param('radius', '3.0 mm',
          'THIS part\'s corner radius, deliberately local. A 20 mm plate cannot take\n'
          '           the arm\'s 6.0 without eating its own bolt pads.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # derived, in the local frame where +X is outward from the yaw axis
    param('seat_x', TURRET + 'roller_w / 2',
          'derived: the collar face, where the bearing\'s inner race seats')
    param('cheek_x', PREFIX + 'seat_x + ' + TURRET + 'collar_h', 'derived: the cheek face')
    param('back_x', TURRET + 'pad_r - ' + TURRET + 'roller_r',
          'derived: the base wall pad, in this frame')
    param('half_h', TURRET + 'clip_pitch / 2 + 3.0 mm',
          'derived: back plate half height - the bolts plus a pad past them')

    # ---- idempotent rebuild --------------------------------------------------
    # RENAME FIRST, THEN DELETE. See fusion/PLAYBOOK.md.
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
    assert comp.name == COMPONENT, (
        'component came back as %r - a stale component still holds the name' % comp.name)
    ext = comp.features.extrudeFeatures
    fil = comp.features.filletFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mpt(sk, y, z):
        return sk.modelToSketchSpace(P3(0, y, z))

    def mm(cm):
        """cm -> a millimetre EXPRESSION. createByString reads a bare number as
        millimetres; val() hands out centimetres. See fusion/PLAYBOOK.md."""
        return '%.4f mm' % (cm * 10.0)

    def one(sk):
        assert sk.profiles.count == 1, (
            sk.name + ': expected 1 profile, got ' + str(sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        c.add(sk.profiles.item(0))
        return c

    def extrude(profs, op, x0_expr, dx_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(x0_expr))
        inp.setDistanceExtent(False, V(dx_expr))
        if op != NEW:
            # Without this a CUT eats every other component. See PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def circle(name, y, z, d, x0_expr, dx_expr, op):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, y, z), d / 2)
        return extrude(one(sk), op, x0_expr, dx_expr, name)

    def rect(name, y0, y1, z0, z1, x0_expr, dx_expr, op):
        sk = sketch(name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk, y0, z0), mpt(sk, y1, z1))
        return extrude(one(sk), op, x0_expr, dx_expr, name)

    # ---- values in cm --------------------------------------------------------
    cheek_x = val('cheek_x')
    back_x = val('back_x')
    half_h = val('half_h')
    half_w = val('half_w')
    plate_t = val('plate_t')
    bolt_z = tval('clip_pitch') / 2

    # The clip's top, in the CAP's frame: the axle sits at tt_axle_z and the
    # plate reaches half_h above it.
    clip_top_z = tval('axle_z') + half_h
    cap_under_z = -tval('cap_t')
    roller_top_z = tval('axle_z') + tval('roller_od') / 2

    # ---- sanity, before any geometry ----------------------------------------
    assert abs(roller_top_z - cap_under_z) < 1e-9, (
        'the roller crowns at z %.2f but the cap underside is at %.2f - they are '
        'meant to touch, that is the whole joint' % (
            roller_top_z * 10, cap_under_z * 10))
    assert clip_top_z <= cap_under_z - val('free') + 1e-9, (
        'the clip reaches z %.2f and the cap starts at %.2f - only the BEARING may '
        'touch the cap. Shrink tt_clip_pitch.' % (clip_top_z * 10, cap_under_z * 10))
    assert back_x - cheek_x >= plate_t - 1e-9, (
        'the base pad is at x %.2f and the cheek face at %.2f, which is less than a '
        '%.1f plate - tt_pad_r is too small' % (
            back_x * 10, cheek_x * 10, plate_t * 10))
    assert val('collar_d') < tval('roller_od') - 2 * val('wall'), (
        'the %.1f collar is nearly as big as the %.1f outer race - it would foul it'
        % (val('collar_d') * 10, tval('roller_od') * 10))
    assert val('axle_len') > tval('roller_w'), (
        'the stub is %.1f and the bearing %.1f - the washer would clamp the axle end '
        'instead of the inner race' % (val('axle_len') * 10, tval('roller_w') * 10))
    assert val('screw_depth') < val('axle_len') + tval('collar_h') + plate_t, (
        'the retaining screw pilot runs out through the back of the clip')
    assert half_w >= val('collar_d') / 2 + val('wall'), (
        'the back plate is narrower than the collar it carries')

    # ---- phase 1: clip form ---------------------------------------------------
    t0 = design.timeline.count
    rect('back_plate', -half_w, half_w, -half_h, half_h,
         mm(back_x - plate_t), PREFIX + 'plate_t', NEW)
    group(t0, PH_FORM)

    # ---- phase 2: the axle -----------------------------------------------------
    # Stub first, collar second, so the collar is unambiguously a step ON the
    # stub rather than two cylinders that happen to meet.
    t1 = design.timeline.count
    circle('stub_axle', 0, 0, tval('axle_d'),
           mm(cheek_x - val('axle_len') - tval('collar_h')),
           mm(val('axle_len') + tval('collar_h') + (back_x - cheek_x)), JOIN)
    circle('race_collar', 0, 0, val('collar_d'), mm(val('seat_x')), TURRET + 'collar_h', JOIN)
    circle('axle_pilot', 0, 0, val('screw_pilot'),
           mm(cheek_x - val('axle_len') - tval('collar_h')), PREFIX + 'screw_depth', CUT)
    group(t1, PH_AXLE)

    # ---- phase 3: base interface ------------------------------------------------
    t2 = design.timeline.count
    for i, sz in enumerate((-1, +1)):
        circle('clip_bolt_%d' % i, 0, sz * bolt_z, tval('clip_clear'),
               mm(back_x - plate_t), PREFIX + 'plate_t', CUT)
    col = adsk.core.ObjectCollection.create()
    for e in comp.bRepBodies.item(0).edges:
        b = e.boundingBox
        if (abs(b.minPoint.y - b.maxPoint.y) < val('tol')
                and abs(b.minPoint.z - b.maxPoint.z) < val('tol')
                and abs(abs(b.minPoint.y) - half_w) < val('tol')
                and abs(abs(b.minPoint.z) - half_h) < val('tol')):
            col.add(e)
    n_filleted = col.count
    if col.count:
        f_inp = fil.createInput()
        f_inp.addConstantRadiusEdgeSet(col, V(PREFIX + 'radius'), True)
        fil.add(f_inp).name = 'plate_corners'
    group(t2, PH_BOLTS)

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - the stub is not reaching the back plate'
        % comp.bRepBodies.count)
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

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('back plate %.1f x %.1f x %.1f, bolted at z +-%.1f (%.1f clearance), '
          'back face at x %.1f' % (
              half_w * 20, half_h * 20, plate_t * 10, bolt_z * 10,
              tval('clip_clear') * 10, back_x * 10))
    print('stub axle %.2f x %.1f past a %.1f collar %.1f proud; bearing seats x '
          '%.1f..%.1f, %.1f of stub left for the washer' % (
              tval('axle_d') * 10, val('axle_len') * 10, val('collar_d') * 10,
              tval('collar_h') * 10, (val('seat_x') - tval('roller_w')) * 10,
              val('seat_x') * 10, (val('axle_len') - tval('roller_w')) * 10))
    print('IN THE CAP FRAME: axle z %.1f, roller crown z %.1f = cap underside %.1f, '
          'clip top z %.1f (%.1f of daylight)' % (
              tval('axle_z') * 10, roller_top_z * 10, cap_under_z * 10,
              clip_top_z * 10, (cap_under_z - clip_top_z) * 10))
    print('filleted %d plate corners at r %.1f (tc/local, NOT the shared %.1f)' % (
        n_filleted, val('radius') * 10, ups.itemByName(STYLE + 'radius').value * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | x3 printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 1000 * 0.6 * 3, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
