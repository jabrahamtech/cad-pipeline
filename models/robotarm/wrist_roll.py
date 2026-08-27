"""robotarm/wrist_roll - Fusion MCP generating script.

Rebuilds `robotarm_wrist_roll` (idempotent). Spec:
specs/robotarm/wrist_roll.md, styled per specs/robotarm/_style.md.

The piece between the two wrist joints. It PITCHES about J4 - a hex socket
in each side face takes a wrist_hub, one driven by the forearm's MG90S -
and it HOUSES the J5 roll SG90, whose shaft points forward along the arm.
The hand bolts to a rotator on that shaft and rolls.

Local frame: origin on the J4 PITCH axis. +X along that axis, +Y forward
toward the hand, +Z up.

WHY THIS PART EXISTS AT ALL. Without it the pitch fork has to straddle the
gripper's 48 mm hand, and every attempt at that came out too wide or too
heavy - 94 mm and 95 g at worst. Straddling this instead, the fork spans
24 mm. The sixth servo deletes more part than it adds.

The roll SG90 lies with its LONG axis across Z, not Y: turned the other way
its 22.6 mm case length would set this housing's width, and the width is
exactly what the fork has to straddle. On its side it sets the height
instead, which is free. The 6.1 mm offset from the shaft to the near end of
the case is why the housing is not symmetric about z = 0.

THE KEEL. Everything this piece sweeps about J4 has to clear the forearm,
and the forearm has only 40 mm to reach the pivot from the elbow. A plain
slab put its bottom-front corner 28.6 mm from the pitch axis, which the
forearm cannot get past. Below the servo pocket the part is therefore not
a slab but a KEEL: a narrow rib that exists only to enclose the lower
mounting tab, bevelled at 45 deg where it meets the back face. That drops
the swept radius to 25.2 mm and takes 5 g of dead plastic out of a part
hanging off a 1.0 kg.cm elbow.

Print orientation: BACK FACE (y = -y_back) ON THE BED, built along +Y. The
servo pocket is then a prism opening at the bed, the hex sockets are
horizontal, and the front bore is a vertical hole. No support.

The SHARED wr_* block is defined identically in wrist_hub.py and
wrist_fork.py. SG90 dimensions are DATASHEET (lib/servo.py).
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_wrist_roll'
BODY_NAME = 'wrist_roll'
PREFIX = 'wro_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'housing form'
PH_SERVO = 'roll servo bay'
PH_PIVOT = 'pitch sockets'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_SERVO, PH_PIVOT, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A wrist is a joint, so it is dark.
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

    # --- SHARED J4 pivot contract -------------------------------------------
    wrist('pivot_af', '16.0 mm',
          'J4 hex socket across flats - SHARED, defined identically in\n'
          '           wrist_hub.py and forearm.py')
    wrist('straddle', '24.0 mm',
          'the width the forearm fork straddles = this housing across the pitch\n'
          '           axis. SHARED - the fork sets its plates off this, so the two\n'
          '           files have to agree or the wrist binds.')
    wrist('sweep_r', '25.4 mm',
          'the radius this housing sweeps about J4. SHARED: no forearm material\n'
          '           inside the straddle may come closer than this to the pitch axis,\n'
          '           or the wrist collides with its own arm at full pitch. Asserted\n'
          '           against every silhouette corner below.')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- fits ----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('free', '0.4 mm', 'free fit - design_rules')

    # --- SG90, DATASHEET (lib/servo.py) --------------------------------------
    param('case_l', '22.6 mm', 'SG90 case length - lies along Z here')
    param('case_w', '12.6 mm', 'SG90 case width - lies along X, so it sets the fork span')
    param('case_h', '23.7 mm', 'SG90 case height - lies along Y, the roll axis')
    param('shaft_end', '6.1 mm', 'shaft axis to the NEAR end of the case, along Z')
    param('tab_span', '32.4 mm', 'SG90 tab tip to tab tip, along Z')
    param('tab_thk', '2.4 mm', 'SG90 tab thickness, along Y')
    param('tab_plane', '17.0 mm', 'case bottom to the tab UNDERSIDE, along Y')
    param('boss_h', '4.2 mm', 'output boss height above the case top')
    param('boss_d', '5.0 mm', 'output boss diameter')

    # --- derived servo placement ---------------------------------------------
    param('case_top', '11.7 mm',
          'roll servo case top. Set so the servo straddles the PITCH axis: its '
          'mass then costs J4 almost nothing')
    param('case_bot', PREFIX + 'case_top - ' + PREFIX + 'case_h', 'derived case bottom')
    param('case_z_hi', PREFIX + 'shaft_end', 'derived: case top edge in Z, above the shaft')
    param('case_z_lo', PREFIX + 'case_z_hi - ' + PREFIX + 'case_l', 'derived case bottom edge in Z')
    param('tab_lo', PREFIX + 'case_bot + ' + PREFIX + 'tab_plane', 'derived tab underside')
    param('tab_over', '(' + PREFIX + 'tab_span - ' + PREFIX + 'case_l) / 2',
          'derived tab overhang past the case')

    # --- housing envelope -----------------------------------------------------
    param('half_x', '12.0 mm',
          'half width. Sized by the hex socket: 3.4 mm deep from this face has to '
          'leave a wall beside the servo pocket. THIS is what the fork straddles')
    param('socket_d', '3.4 mm', 'hex socket depth into the side wall')
    param('y_back', '-14.0 mm', 'back face')
    param('y_front', '17.0 mm', 'front face - past the servo boss, carries the rotator bore')
    param('z_top', WRIST + 'pivot_af / cos(30 deg) / 2 + ' + PREFIX + 'wall',
          'derived top face. A guessed 10.0 put the face INSIDE the hex socket\n           circumradius (9.24) - derive it from the socket so it stays right if\n           the pivot size ever moves.')
    param('z_bot',
          PREFIX + 'case_z_lo - ' + PREFIX + 'tab_over - ' + PREFIX + 'loc / 2 - '
          + PREFIX + 'wall',
          'derived keel underside: a wall below the lower tab tip. Derived, not\n'
          '           guessed - a hardcoded -23.0 left only 1.5 mm of floor there.')
    param('body_bot', PREFIX + 'case_z_lo - ' + PREFIX + 'loc / 2 - ' + PREFIX + 'wall',
          'derived: the floor under the servo pocket, and where the slab stops.\n'
          '           Everything below this is keel, not slab.')
    param('keel_half_x', '8.0 mm',
          'keel half width - it only has to enclose the tab, which is as wide as\n'
          '           the case, so it need not run out to the side walls')
    param('keel_front', PREFIX + 'tab_lo + ' + PREFIX + 'tab_thk + ' + PREFIX + 'wall',
          'derived keel front face: a wall past the tab slot')
    param('keel_top', PREFIX + 'case_z_lo',
          'derived: the keel overlaps the slab by wall + loc/2 rather than meeting\n'
          '           it exactly. Two volumes that TOUCH are non-manifold - see PLAYBOOK.')
    param('rot_bore', '11.0 mm', 'clearance bore for the boss and the rotator hub')

    # --- lead escape ---------------------------------------------------------
    param('lead_d', '3.4 mm',
          'SG90 lead_bundle_dia - lib/servo.py. Typed here like the other\n'
          '           DATASHEET numbers; _check_leads probes with the LIBRARY value,\n'
          '           so if the two drift the gate fails rather than lying.')
    param('lead_y', PREFIX + 'case_bot + ' + PREFIX + 'lead_d',
          'derived: where the lead leaves the case bottom end face - one lead\n'
          '           diameter up from the case bottom, centred across the width.\n'
          '           The same rule _check_leads places its probe by.')
    param('lead_ch_d', '5.0 mm',
          'lead channel bore through the pocket floor and keel - same Ø as\n'
          '           pruner_shell\'s lead_notch for the same servo. Without it the\n'
          '           lead was 81 % TRAPPED: below the case bottom end face is floor,\n'
          '           then keel, solid to z_bot.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
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

    def slab(name, x0, x1, z0, z1, y0_expr, dy_expr, op):
        """Block whose XZ outline is a rectangle, extruded along Y."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, 0, z0), mpt(sk, x1, 0, z1))
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    def prism_x(name, pts_yz, x0_expr, dx_expr, op):
        """Solid whose YZ silhouette is a polygon, extruded along X."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts_yz)):
            u, w = pts_yz[i], pts_yz[(i + 1) % len(pts_yz)]
            lines.addByTwoPoints(mpt(sk, 0, u[0], u[1]), mpt(sk, 0, w[0], w[1]))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def hex_socket(name, sign):
        """Hex pocket in one side face, axis along X, centred on the pitch axis."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        n_side = 2 * 3
        r_c = wval('pivot_af') / 2 / math.cos(math.pi / n_side)
        pts = []
        for i in range(n_side):
            a = 2 * math.pi * i / n_side
            pts.append((r_c * math.cos(a), r_c * math.sin(a)))
        for i in range(len(pts)):
            u, w = pts[i], pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(mpt(sk, 0, u[0], u[1]), mpt(sk, 0, w[0], w[1]))
        if sign > 0:
            return extrude(profiles(sk, expected=1), CUT,
                           PREFIX + 'half_x', '-' + PREFIX + 'socket_d', name)
        return extrude(profiles(sk, expected=1), CUT,
                       '-' + PREFIX + 'half_x', PREFIX + 'socket_d', name)

    # ---- values in cm ---------------------------------------------------------
    half_x = val('half_x')
    loc = val('loc')
    socket_wall = half_x - val('socket_d') - (val('case_w') / 2 + loc / 2)
    assert socket_wall >= val('wall'), (
        'only %.2f mm of wall between the hex socket and the servo pocket' % (socket_wall * 10))
    r_c = wval('pivot_af') / 2 / math.cos(math.pi / (2 * 3))
    assert r_c + val('wall') <= val('z_top'), 'the hex socket breaks out of the top face'

    # lead channel sanity, in cm. The channel may break out of the keel's 45
    # deg back bevel partway down - that is a feature, the lead leaves through
    # the bevel face - but it must never reach the tab slot, which is what the
    # keel is FOR, and it must pass the bundle.
    assert val('lead_ch_d') >= val('lead_d') + 2 * loc, (
        'the lead channel is tighter than the bundle plus a locational fit')
    assert val('lead_y') + val('lead_ch_d') / 2 + val('wall') <= \
        val('tab_lo') - loc / 2, (
        'the lead channel comes within a wall of the lower tab slot')
    assert val('lead_ch_d') / 2 + val('wall') <= val('keel_half_x'), (
        'the lead channel leaves less than a wall of keel beside it')

    # The keel's back face is a 45 deg bevel, not a wall: it starts at the bed
    # plane as a knife edge and grows downward one layer per layer, so it needs
    # no support, AND it keeps the bottom-back corner inside the sweep circle.
    keel_drop = val('keel_top') - val('z_bot')
    keel_pts = [(val('y_back') + keel_drop, val('z_bot')),
                (val('keel_front'), val('z_bot')),
                (val('keel_front'), val('keel_top')),
                (val('y_back'), val('keel_top'))]
    body_pts = [(val('y_back'), val('body_bot')), (val('y_front'), val('body_bot')),
                (val('y_front'), val('z_top')), (val('y_back'), val('z_top'))]
    worst = ('', 0.0)
    for label, pts in (('slab', body_pts), ('keel', keel_pts)):
        for y, z in pts:
            r = math.hypot(y, z)
            if r > worst[1]:
                worst = ('%s corner (%.1f, %.1f)' % (label, y * 10, z * 10), r)
    assert worst[1] <= wval('sweep_r'), (
        'the %s sweeps %.1f mm about J4, past the %.1f mm the forearm allows'
        % (worst[0], worst[1] * 10, wval('sweep_r') * 10))

    # ---- phase 1: housing form -------------------------------------------------
    t0 = design.timeline.count
    slab('housing', -half_x, half_x, val('body_bot'), val('z_top'),
         PREFIX + 'y_back', PREFIX + 'y_front - ' + PREFIX + 'y_back', NEW)
    prism_x('keel', keel_pts, '-' + PREFIX + 'keel_half_x',
            '2 * ' + PREFIX + 'keel_half_x', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: roll servo bay ------------------------------------------------
    t1 = design.timeline.count
    slab('servo_case_pocket',
         -(val('case_w') / 2 + loc / 2), val('case_w') / 2 + loc / 2,
         val('case_z_lo') - loc / 2, val('case_z_hi') + loc / 2,
         PREFIX + 'y_back - ' + PREFIX + 'wall',
         PREFIX + 'case_top + ' + PREFIX + 'loc / 2 - ' + PREFIX + 'y_back + ' + PREFIX + 'wall',
         CUT)
    slab('tab_slots',
         -(val('case_w') / 2 + loc / 2), val('case_w') / 2 + loc / 2,
         val('case_z_lo') - val('tab_over') - loc / 2,
         val('case_z_hi') + val('tab_over') + loc / 2,
         PREFIX + 'tab_lo - ' + PREFIX + 'loc / 2',
         PREFIX + 'tab_thk + ' + PREFIX + 'loc', CUT)
    v_before = comp.bRepBodies.item(0).volume
    sk_lead = sketch(comp.xYConstructionPlane, 'sk_lead_channel')
    sk_lead.sketchCurves.sketchCircles.addByCenterRadius(
        mpt(sk_lead, 0, val('lead_y'), 0), val('lead_ch_d') / 2)
    extrude(profiles(sk_lead, expected=1), CUT,
            PREFIX + 'z_bot - ' + PREFIX + 'wall',
            PREFIX + 'case_z_lo - ' + PREFIX + 'z_bot + ' + PREFIX + 'wall',
            'lead_channel')
    drop = (v_before - comp.bRepBodies.item(0).volume) * 1000
    # bounds from the geometry itself: a full cylinder through the keel span
    # is the ceiling; the 45 deg back bevel eats some of it, but never half.
    ch_full = math.pi * (val('lead_ch_d') / 2) ** 2 \
        * (val('case_z_lo') - val('z_bot')) * 1000
    assert ch_full / 2 < drop < ch_full, (
        'the lead channel removed %.1f mm3 against a %.1f full-cylinder '
        'ceiling - it is not cutting where the trap was' % (drop, ch_full))
    sk_rot = sketch(comp.xZConstructionPlane, 'sk_rotator_bore')
    sk_rot.sketchCurves.sketchCircles.addByCenterRadius(
        mpt(sk_rot, 0, 0, 0), val('rot_bore') / 2)
    extrude(profiles(sk_rot, expected=1), CUT, PREFIX + 'case_top',
            PREFIX + 'y_front - ' + PREFIX + 'case_top + ' + PREFIX + 'wall', 'rotator_bore')
    group(t1, PH_SERVO)

    # ---- phase 3: pitch sockets --------------------------------------------------
    t2 = design.timeline.count
    for sx in (-1, 1):
        hex_socket('pitch_socket_%d' % sx, sx)
    group(t2, PH_PIVOT)

    # ---- phase 4: finish -----------------------------------------------------------
    t3 = design.timeline.count
    for y_pick, nm in ((val('y_back'), 'bed_face_chamfer'), (val('y_front'), 'front_chamfer')):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.y - y_pick) < val('tol')
                    and abs(eb.maxPoint.y - y_pick) < val('tol')):
                col.add(e)
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = nm
    group(t3, PH_FINISH)

    # ---- identity + diagnostics --------------------------------------------------
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

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('THE FORK STRADDLES %.1f mm - the whole reason this part exists' % (half_x * 2 * 10))
    print('roll servo: case y %.1f..%.1f, z %.1f..%.1f | tabs y %.1f, z +/-%.1f' % (
        val('case_bot') * 10, val('case_top') * 10,
        val('case_z_lo') * 10, val('case_z_hi') * 10, val('tab_lo') * 10,
        (val('case_z_hi') + val('tab_over')) * 10))
    print('keel: y %.1f..%.1f, z %.1f..%.1f, %.1f wide, back face bevelled %.1f' % (
        val('y_back') * 10, val('keel_front') * 10, val('z_bot') * 10,
        val('keel_top') * 10, val('keel_half_x') * 20, keel_drop * 10))
    print('lead channel: Ø%.1f at (x 0, y %.1f), z %.1f down through the keel '
          '- the SG90 lead escapes the bay it was 81 %% trapped in'
          % (val('lead_ch_d') * 10, val('lead_y') * 10,
             val('case_z_lo') * 10))
    print('WORST SWEEP about J4: %s at %.1f mm (forearm allows %.1f)' % (
        worst[0], worst[1] * 10, wval('sweep_r') * 10))
    print('hex socket %.1f af, %.1f deep, leaving %.2f mm of wall beside the servo' % (
        wval('pivot_af') * 10, val('socket_d') * 10, socket_wall * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
