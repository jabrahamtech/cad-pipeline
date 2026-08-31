"""robotarm/shoulder_hub - Fusion MCP generating script.

Rebuilds `robotarm_shoulder_hub` (idempotent). Spec: specs/robotarm/_state.md.

`wrist_hub` with an MG995 horn in it instead of an MG90S one. The hex and
the journal collar are the shared wr_ contract, unchanged, so the shoulder
fork is the same fork the forearm already is and the idler side takes an
ordinary wrist_hub off the same print. The RETENTION is not shared - see
the next paragraph.

ONE of these is printed. The J2 idler is a plain wrist_hub.

THIS HUB HAS NO RETAINING FLANGE, AND THAT IS THE WHOLE POINT OF THE
PART. Every other hub in the arm is trapped by a 24.0 flange too big to
pass its own 20.35 journal bore. On the J2 DRIVE side that flange makes
the hub impossible to install, and the first one printed had to be
scrapped:

  from inside   the flange must pass the fork's 20.35 journal bore.  24.0.
  from outside  the flange must pass the servo pad's case window, which
                is 20.4 wide in Y (sb_case_w + sb_loc) and only 12.2 mm
                of depth from the counterbore floor to the pad's outer
                face. Tilting a 24.0 disc far enough to clear 20.4 costs
                at least 21.8 mm of that depth. There is no path.

So the counterbore on the drive plate is unreachable and is left empty,
and the collar simply runs the full plate thickness instead - the horn
face lands in exactly the same place it did, sh_collar_l = wr_journal +
wr_flange_t. Retention is by the two stops that were always there and
are 3.4 mm apart:

  inboard   the hex bottoms in the upper arm's socket (wr_reach 3.8 =
            0.4 running gap + 3.4 socket depth)
  outboard  the MG995's own case top, 0.5 mm off this face

The idler side is unaffected: it takes an ordinary flanged wrist_hub off
the same print, because nothing is bolted over its counterbore.

NOTHING ON THIS PART MAY EXCEED wr_hub_d. That is asserted on the built
body, not on the parameters, because it is the assembly that is at stake
and a flange is exactly the kind of feature that gets added back.

THE RELIEF IS A THREE-STEP POCKET, AND THAT IS NOT DECORATION. An MG995
does not present a bare spline: it presents 3.0 mm of 13.0 output boss
and then the horn hub sitting on it, 6.8 mm of stack above the case top
going into a hub 7.0 mm deep before its hex starts. Depths below are from
this face, which stands 0.5 off the case top:

  0.0 - 2.5 mm   15.60 mouth   swallows the boss AND passes the horn arms
  2.5 - 4.8 mm   cross slot    the blade, keyed at 90 deg increments
  0.0 - 6.4 mm   9.10 bore     the horn hub (MEASURED 8.7) + 0.4 free

The mouth is 15.60 because of the ARMS, not the 13.0 boss: the arms are
TRIMMED to r 7.6 at assembly and have to travel down this hole to reach
their slot. On the boss alone it would be 13.4 and the servo could never
be fitted. An untrimmed MG995 cross is 33.5 tip to tip and the round horn
is 22.0 - neither goes in as it comes out of the bag.

The horn goes in BLADE TOWARD THE SERVO. Flipped the other way its blade
would sit 5 mm deeper, which is inside the hex, and the arm tips would
break out through the flats.

THE HORN IS SCREWED TO THE SERVO FIRST. Once the hub is on the horn its
retaining screw is behind the hex, and once the upper arm is on the hex
there is no access at all. The 6.50 screw bore on this side is driver
access for that first step and nothing else; on the idler side the same
bore passes the M3.

The horn slot is a CROSS, not a bar. An MG995 ships with a four-arm horn
and a round one; the cross takes either at 90 deg increments, and a
shoulder that carries the entire arm wants positive keying rather than a
press fit doing the work.

Print orientation: COLLAR FACE ON THE BED, built +Z. As wrist_hub.
"""


import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_shoulder_hub'
BODY_NAME = 'shoulder_hub'
PREFIX = 'sh_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'hub form'
PH_HORN = 'horn interface'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_HORN, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A hub is a joint, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('shoulder_hub')


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
    param('collar_l', WRIST + 'journal + ' + WRIST + 'flange_t',
          'derived: the drive hub is FLANGELESS, so its collar runs the whole\n'
          '           plate thickness - the journal bore plus the counterbore the\n'
          '           flange can never reach. Same overall length as the idler\n'
          '           hub, so the horn face lands on the same datum. 2026-08-30.')

    # --- MG90S horn, DATASHEET (lib/servo.py) -------------------------------
    param('horn_hub_d', '9.10 mm',
          'MG995 horn hub MEASURED 8.7 (2026-08-28 bench) + 0.4 free. The\n           model said 13.8 and it was 5.1 mm out - the whole reason the J2\n           standoff was invented was to keep a 13.95 relief out of the hex\n           root, and at 9.10 there is 3.35 mm of wall to the hex flats. The\n           standoff is therefore GONE (sb_horn_standoff 0.0).')
    param('horn_hub_depth', '6.40 mm',
          'boss 3.0 + MEASURED hub 3.8 = 6.8 of stack above the case top,\n           less the 0.5 this face stands off that top, + 0.1 seating.\n           Hub HEIGHT 3.8 is the last horn number still model-grade.')
    param('boss_d', '15.6 mm',
          'the mouth. Sized by the horn ARMS, not the 13.0 output boss it also\n           clears: the arms are trimmed to r 7.6 (horn audit) and have to pass\n           down this hole to reach their slot, so it is 2 x horn_arm_r + 0.4\n           free. On the 13.0 boss alone it would be 13.4 and the servo\n           could never be fitted.')
    param('boss_depth', '2.50 mm',
          'the MG995 output boss stands 3.0 proud of the case top and this\n           face sits 0.5 outboard of it, so 2.5 of boss lands inside the hub.\n           Was 0.5 while sb_horn_standoff held the case 2.0 further out;\n           retiring the standoff (the O13.8 hub it dodged does not exist)\n           put the boss back 2.0 deeper - _check_shoulder caught it as\n           75.59 mm3 of MG995_output^shoulder_hub. 2026-08-28.')
    param('arm_start', PREFIX + 'boss_depth',
          'derived: the blade plane is one boss height down from this face,\n'
          '           because the horn is fitted BLADE TOWARD THE SERVO')
    param('horn_arm_w', '6.65 mm',
          'horn arm width AT the r 7.6 trim: ~6.5 + press 0.15. The old 2.65\n           was the blade THICKNESS misread as width - no MG995 horn arm\n           would have entered - 2026-08-27 horn audit')
    param('horn_arm_r', '7.6 mm',
          'horn arms TRIMMED to this radius at assembly. Was 8.0; the audited\n           6.65 slot corner at hypot(8, 3.3) = 8.66 left 1.34 of collar wall,\n           7.6 restores 1.7. Still past the wrist hub 6.0 - this joint\n           carries the whole arm.')
    param('horn_arm_depth', '2.30 mm',
          'MG995 blade MEASURED 2.2 (BL comb, middle slot) + 0.1 seating.\n           The model said 2.5. 2026-08-28 bench.')
    param('screw_d', '6.5 mm',
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
    # ONE collar, full plate thickness. No flange - see the docstring. The
    # length is still written as journal + flange_t so the horn face stays
    # on the plate's outer datum if either of those ever moves.
    disc('journal_collar', wval('hub_d'), '-' + PREFIX + 'collar_l',
         PREFIX + 'collar_l', NEW)

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
    disc('horn_hub_relief', val('horn_hub_d'), '-' + PREFIX + 'collar_l',
         PREFIX + 'horn_hub_depth', CUT)
    # The mouth. Cut second so the step is unambiguous: everything above
    # boss_depth opens out to clear the output boss and let the arms through.
    disc('horn_mouth', val('boss_d'), '-' + PREFIX + 'collar_l',
         PREFIX + 'boss_depth', CUT)

    for ang, tag in ((0, 'a'), (1, 'b')):
        sk_arm = sketch(comp.xYConstructionPlane, 'sk_horn_arm_slot_' + tag)
        if ang == 0:
            p0 = mpt(sk_arm, -val('horn_arm_r'), -val('horn_arm_w') / 2, 0)
            p1 = mpt(sk_arm, val('horn_arm_r'), val('horn_arm_w') / 2, 0)
        else:
            p0 = mpt(sk_arm, -val('horn_arm_w') / 2, -val('horn_arm_r'), 0)
            p1 = mpt(sk_arm, val('horn_arm_w') / 2, val('horn_arm_r'), 0)
        sk_arm.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
        extrude(profiles(sk_arm, expected=1), CUT,
                '-' + PREFIX + 'collar_l' + ' + ' + PREFIX + 'arm_start',
                PREFIX + 'horn_arm_depth', 'horn_arm_slot_' + tag)

    disc('screw_bore', val('screw_d'), '-' + PREFIX + 'collar_l',
         PREFIX + 'collar_l + ' + WRIST + 'reach', CUT)
    group(t1, PH_HORN)

    # ---- phase 3: finish ----------------------------------------------------
    t2 = design.timeline.count
    for z_pick, size, nm in ((reach, PREFIX + 'lead_in', 'hex_nose_lead_in'),
                             (-val('collar_l'), STYLE + 'ef', 'bed_face_chamfer')):
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

    # THE OLD CHECK HERE WAS RADIAL-ONLY (hex flats vs relief radius) and
    # depth-blind. What actually matters, horn audit 2026-08-27: (1) the hub
    # bore must STOP inside the body - if it tunnels past journal + flange it
    # cores the hex boss root, which carries all of J2; (2) the collar wall
    # around the bore takes the torque across the bore band.
    body_deep = val('collar_l')
    assert val('horn_hub_depth') <= body_deep + 1e-9, (
        'the horn hub bore runs %.2f deep and the body is only %.2f - it '
        'tunnels into the hex boss root. Lengthen the collar, do not '
        'thin the hex.' % (val('horn_hub_depth') * 10, body_deep * 10))
    wall = (wval('hub_d') / 2 - val('horn_hub_d') / 2)
    assert wall >= 0.16 - 1e-9, (
        'only %.2f mm of collar wall around the horn hub bore' % (wall * 10))
    assert val('boss_d') >= 2 * val('horn_arm_r') + 0.04 - 1e-9, (
        'the mouth is %.2f but the trimmed horn arms sweep %.2f - they cannot '
        'travel down to their slot and the servo cannot be fitted'
        % (val('boss_d') * 10, val('horn_arm_r') * 20))
    mouth_wall = (wval('hub_d') - val('boss_d')) / 2
    assert mouth_wall >= 0.16 - 1e-9, (
        'only %.2f mm of collar wall around the %.2f mouth' % (
            mouth_wall * 10, val('boss_d') * 10))
    arm_wall = wval('hub_d') / 2 - val('horn_arm_r')
    assert arm_wall >= 0.16 - 1e-9, (
        'only %.2f mm of collar wall at the horn arm tips' % (arm_wall * 10))
    blade_end = val('arm_start') + val('horn_arm_depth')
    assert blade_end <= val('collar_l') + 1e-9, (
        'the blade slot ends %.2f mm below this face, past the %.2f mm of collar '
        '- the arm tips would break out through the hex flats'
        % (blade_end * 10, val('collar_l') * 10))
    # THE ASSEMBLY ASSERT. This hub is installed through a servo pad that is
    # already bolted over its counterbore: nothing on it may exceed the journal
    # collar, or it cannot be fitted at all. Measured on the BODY, because a
    # flange is exactly the feature that gets added back by someone reading
    # wrist_hub.py. See the docstring.
    _bb = body.boundingBox
    max_r = max(abs(_bb.minPoint.x), abs(_bb.maxPoint.x),
                abs(_bb.minPoint.y), abs(_bb.maxPoint.y))
    assert max_r <= wval('hub_d') / 2 + 1e-6, (
        'this hub is %.2f across at its widest and the drive plate journal bore '
        'is %.2f - it cannot be installed from either side. The drive hub is '
        'FLANGELESS; retention is the arm socket inboard and the MG995 case '
        'outboard.' % (max_r * 20, wval('hub_d') * 10))

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
    print('collar OD %.1f x %.1f (FLANGELESS - widest point %.2f), journal band %.1f' % (
        wval('hub_d') * 10, val('collar_l') * 10, max_r * 20, journal * 10))
    print('relief: mouth %.2f x %.2f | blade slot %.2f..%.2f r %.2f | bore %.2f x %.2f'
          % (val('boss_d') * 10, val('boss_depth') * 10, val('arm_start') * 10,
             blade_end * 10, val('horn_arm_r') * 10,
             val('horn_hub_d') * 10, val('horn_hub_depth') * 10))
    print('walls: hex/bore %.2f | collar/mouth %.2f | collar/arm tips %.2f mm'
          % (wall * 10, mouth_wall * 10, arm_wall * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
