"""robotarm/wrist_hub - Fusion MCP generating script.

Rebuilds `robotarm_wrist_hub` (idempotent). Spec:
specs/robotarm/wrist_hub.md, styled per specs/robotarm/_style.md.

Local frame: the J4 axis is +Z. z = 0 is the face that lands on the fork
plate's inner face; the hex boss runs +Z into the effector's socket and the
journal collar runs -Z into the fork plate's bore.

ONE printed design, TWO copies, and the two do DIFFERENT jobs:

  drive side  - the wrist MG90S's trimmed horn keys into the pocket in its
                back face, so the servo turns this hub, the hex turns the
                effector, and the servo's own output bearing carries it.
  idler side  - the identical part runs free in the opposite fork plate's
                bore, retained by an M3 screw through the same pocket. The
                horn slot is simply an unused void.

That is why the effector's socket is a HEX and not a round journal: both
journals live in the FORK, so the socket only has to transmit torque and
index. It can therefore be 3.4 mm deep, which is all the room there is
beside the gripper's servo.

Print orientation: COLLAR FACE ON THE BED, built +Z. Every cross-section
shrinks going up (collar -> hex), so no support. The hex flats are then
loaded within layers, which is the direction the wrist's torque runs.

THE HUB GOES IN FROM OUTSIDE, so every diameter inboard of the collar has
to pass through the collar's own bore. The hex is 15.80 across flats but
18.24 ACROSS CORNERS, which is why the collar is 20.0 and not the 18.0 it
started at - at 18.0 the corners stood proud of the journal and the part
could not be assembled at all. Any change to wr_pivot_af has to be checked
against that, and the assertion below does it.

FOUR OF THESE ARE PRINTED, not two: J3 (elbow) uses the identical joint,
so the upper arm straddles the forearm exactly as the forearm straddles
the roll housing. One design, four copies, two joints.

The SHARED wr_* block is defined identically in wrist_roll.py and
forearm.py; sty_* comes from _style.md. MG90S horn dimensions are
DATASHEET (lib/servo.py) and are the first suspects if the horn will not
press in - gauge before printing a pair.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_wrist_hub'
BODY_NAME = 'wrist_hub'
PREFIX = 'wh_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'hub form'
PH_HORN = 'horn interface'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_HORN, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A hub is a joint, so it is dark.
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

    def wrist(name, expr, comment='', units='mm'):
        _set(WRIST + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    # --- SHARED J4 clevis contract -----------------------------------------
    wrist('pivot_af', '16.0 mm',
          'J4 hex socket across flats - SHARED, defined identically in\n'
          '           wrist_roll.py and forearm.py')
    wrist('straddle', '24.0 mm',
          'the width the forearm fork straddles = the roll housing across the\n'
          '           pitch axis. SHARED - see wrist_roll.py.')
    wrist('sweep_r', '25.4 mm',
          'the radius the roll housing sweeps about J4. SHARED - see wrist_roll.py.')
    wrist('hub_d', '20.0 mm',
          'journal collar diameter - runs in the fork plate bore. MUST exceed the\n'
          '           hex ACROSS CORNERS (18.24), because the hex is threaded through\n'
          '           this bore at assembly. Asserted below.')
    wrist('journal', '5.0 mm', 'collar length, i.e. the fork plate thickness it runs in')
    wrist('flange_d', '24.0 mm',
          'retaining flange: too big to pass through the fork plate bore, so the\n'
          '           hub cannot walk out and needs no screw. It sits in a counterbore\n'
          '           in the plate face.')
    wrist('flange_t', '2.0 mm', 'flange thickness = the plate counterbore depth')
    wrist('reach', '3.8 mm',
          'hex boss length = the running gap between the fork plate and the roll\n'
          '           housing (0.4, free fit) PLUS the socket depth (3.4), so the hex\n'
          '           bottoms in the socket. That bottoming is what locates the housing\n'
          '           axially; the flange sits 0.5 loose in its counterbore so the two\n'
          '           stops cannot fight each other.')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- hub ---------------------------------------------------------------
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('hex_af', WRIST + 'pivot_af - ' + PREFIX + 'loc',
          'derived: locational fit inside the effector socket - grow the HOLE, '
          'shrink nothing, so the socket stays nominal and this comes down')
    param('lead_in', '0.6 mm', 'chamfer on the hex nose - joints_tolerances, every mating edge')

    # --- MG90S horn, DATASHEET (lib/servo.py) -------------------------------
    param('horn_hub_d', '8.15 mm', 'MG90S horn hub 8.0 + press 0.15 - 2026-08-27 horn audit, lib/servo.py')
    param('horn_hub_depth', '9.1 mm',
          'horn hub 3.0 + 0.1 (2026-08-27 horn audit), PLUS the MG90S output boss (6.0) which this relief\n           swallows. Sitting the hub ON the case top instead of on top of the boss\n           takes 6 mm out of the wrist width, which is the whole ballgame here:\n           the yoke has to fit between two ears 38.8 mm apart.')
    param('horn_arm_w', '5.85 mm', 'horn arm width AT THE r 6 trim: 5.5 + press\n           0.15. The arm tapers 5.5 -> 3; 3.95 was the blade thickness\n           misread as width - 2026-08-27 horn audit, lib/servo.py\n           MEASURED 2026-08-28: the arm is 5.7 at the r 6 trim, so 5.65 was 0.05 UNDER it - an interference, not a press fit.')
    param('horn_arm_r', '6.0 mm', 'horn arm TRIMMED to this radius at assembly - see spec')
    param('horn_arm_depth', '2.1 mm', 'horn blade 2.0 + 0.1 seating - 2026-08-27 horn audit, lib/servo.py')
    param('screw_d', '5.5 mm',
          'driver access to the horn screw on the drive side; on the idler side '
          'the M3 retaining screw passes through the same bore')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild -------------------------------------------------
    # RENAME FIRST, THEN DELETE. Deleting a component's LAST occurrence orphans
    # the component: it drops straight out of allComponents while still holding
    # its name, so a rename afterwards cannot reach it and the rebuild is handed
    # 'robotarm_x (1)'. Every lookup by name then misses. See fusion/PLAYBOOK.md.
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
    chf = comp.features.chamferFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                sk.name + ': expected ' + str(expected) + ', got ' + str(sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            # Without this a CUT eats every other component in the document.
            # See fusion/PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm, z_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def disc(name, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def edges_in_plane_z(z_pick):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.z - z_pick) < val('tol')
                    and abs(eb.maxPoint.z - z_pick) < val('tol')):
                col.add(e)
        return col

    # ---- values in cm -------------------------------------------------------
    hex_af = val('hex_af')
    journal = wval('journal')
    reach = wval('reach')

    # ---- phase 1: collar + hex boss ----------------------------------------
    t0 = design.timeline.count
    disc('journal_collar', wval('hub_d'), '-' + WRIST + 'journal', WRIST + 'journal', NEW)
    # Trapped, not screwed: the flange cannot pass through the plate bore and
    # the effector's socket floor stops it going the other way.
    disc('retaining_flange', wval('flange_d'),
         '-(' + WRIST + 'journal + ' + WRIST + 'flange_t)', WRIST + 'flange_t', JOIN)

    sk_hex = sketch(comp.xYConstructionPlane, 'sk_hex_boss')
    lines = sk_hex.sketchCurves.sketchLines
    n_side = 2 * 3
    r_c = hex_af / 2 / math.cos(math.pi / n_side)
    pts = []
    for i in range(n_side):
        a = 2 * math.pi * i / n_side
        pts.append((r_c * math.cos(a), r_c * math.sin(a)))
    for i in range(len(pts)):
        u, w = pts[i], pts[(i + 1) % len(pts)]
        lines.addByTwoPoints(mpt(sk_hex, u[0], u[1], 0), mpt(sk_hex, w[0], w[1], 0))
    extrude(profiles(sk_hex, expected=1), JOIN, '0.0 mm', WRIST + 'reach', 'hex_boss')
    group(t0, PH_FORM)

    # ---- phase 2: horn interface -------------------------------------------
    t1 = design.timeline.count
    disc('horn_hub_relief', val('horn_hub_d'), '-(' + WRIST + 'journal + ' + WRIST + 'flange_t)',
         PREFIX + 'horn_hub_depth', CUT)

    sk_arm = sketch(comp.xYConstructionPlane, 'sk_horn_arm_slot')
    sk_arm.sketchCurves.sketchLines.addTwoPointRectangle(
        mpt(sk_arm, -val('horn_arm_r'), -val('horn_arm_w') / 2, 0),
        mpt(sk_arm, val('horn_arm_r'), val('horn_arm_w') / 2, 0))
    extrude(profiles(sk_arm, expected=1), CUT,
            '-(' + WRIST + 'journal + ' + WRIST + 'flange_t)',
            PREFIX + 'horn_arm_depth', 'horn_arm_slot')

    disc('screw_bore', val('screw_d'), '-(' + WRIST + 'journal + ' + WRIST + 'flange_t)',
         WRIST + 'journal + ' + WRIST + 'flange_t + ' + WRIST + 'reach', CUT)
    group(t1, PH_HORN)

    # ---- phase 3: finish ----------------------------------------------------
    t2 = design.timeline.count
    for z_pick, size, nm in ((reach, PREFIX + 'lead_in', 'hex_nose_lead_in'),
                             (-(journal + wval('flange_t')), STYLE + 'ef', 'bed_face_chamfer')):
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            edges_in_plane_z(z_pick), V(size), False)
        chf.add(c_inp).name = nm
    group(t2, PH_FINISH)

    # ---- identity + diagnostics ---------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got ' + str(comp.bRepBodies.count)
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

    wall = (hex_af / 2 - val('horn_hub_d') / 2)
    assert wall > 0, 'the horn relief is wider than the hex boss'
    hex_corners = hex_af / math.cos(math.pi / 6)
    assert hex_corners < wval('hub_d'), (
        'hex is %.2f across corners but the collar is only %.2f - the hub cannot be '
        'threaded through its own bore' % (hex_corners * 10, wval('hub_d') * 10))
    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('hex %.2f af (socket %.1f - %.1f loc) reaching %.1f mm' % (
        hex_af * 10, wval('pivot_af') * 10, val('loc') * 10, reach * 10))
    print('hex across corners %.2f, threaded through a %.1f collar bore' % (
        hex_corners * 10, wval('hub_d') * 10))
    print('collar OD %.1f x %.1f, retaining flange OD %.1f x %.1f' % (
        wval('hub_d') * 10, journal * 10, wval('flange_d') * 10, wval('flange_t') * 10))
    print('wall between the horn relief and the hex flats: %.2f mm' % (wall * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
