"""robotarm/_preview_arm - pose the WHOLE arm and save viewport images.

A helper, not a part and not a gate. It assembles every component already in
the document into one pose and writes PNGs to docs/robotarm/. Run it after
_check_ledger has built everything, or after any run that leaves all 13 parts
in the document.

It measures nothing and asserts almost nothing. If you want to know whether
the arm FITS, run the gates; a picture will happily show you two solids in the
same place and look fine.

THE FRAME IS THE TURNTABLE'S: origin on the J1 yaw axis at the PRINTED
PLATTER'S RIM TOP (its own z 42.00, measured), +Z up, +Y forward at zero yaw.
Every transform below is expressed as "this part, in its parent's frame",
composed outward, which is the only way this stays readable - the six joints
are six matrices, not one big one.

The platter itself is imported from legacy/exports/robotarm/base_platter_v1.step
and dropped 42 mm so its rim top lands on z = 0. It is the one thing in the
picture that already exists in plastic.

Two placements are taken from other files rather than re-derived, on purpose:
the wrist chain from _check_wrist and the pruner head from _check_pruner. If
they change there they must change here, and the render is where you will see
it first.

The base shell does not exist yet, so the three turntable clips are drawn
where they will sit and everything above them is yawed about J1 as one body.
"""

import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from lib.joints import J5_ROTATOR_ORIGIN_PARTS  # noqa: E402
import lib.grip as G  # noqa: E402

OUT = os.path.join(REPO, 'docs', 'robotarm')
W, H = 1800, 1300

# The pose. Positive pitch is UP: a rotation about +X carries +Y toward +Z.
J1_YAW_DEG = 25.0          # turret, away from the assembly position
J2_PITCH_DEG = 35.0        # shoulder, up and forward
J3_PITCH_DEG = -55.0       # elbow, relative to the upper arm
J4_PITCH_DEG = 15.0        # wrist pitch, relative to the forearm
J5_ROLL_DEG = 0.0
J6_OPEN_MM = 12.0          # grip_jaw travel each side - lib/grip.GR_STROKE is full open

VIEWS = {
    'arm_iso': ((1.0, -1.3, 0.65), (0.0, 0.0, 1.0)),
    'arm_side': ((1.0, -0.001, 0.0), (0.0, 0.0, 1.0)),
    'arm_front': ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    'arm_top': ((0.0, -0.001, 1.0), (0.0, 1.0, 0.0)),
}


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    M3 = adsk.core.Matrix3D.create
    P3 = adsk.core.Point3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)

    def gv(name):
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        return p.value

    # ---- one occurrence per component, everything else cleared -------------
    keep = {}
    for occ in list(root.occurrences):
        n = occ.component.name
        if n in keep:
            occ.deleteMe()
        else:
            keep[n] = occ
    design.timeline.moveToEnd()
    need = ['turntable_stator', 'turntable_ring', 'shoulder_bracket', 'shoulder_hub',
            'wrist_hub', 'upper_arm', 'forearm', 'wrist_roll', 'wrist_rotator',
            'grip_shell', 'grip_jaw', 'grip_finger', 'gripper_pinion',
            'base_platter', 'base_lid', 'j1_hub', 'roller_cap', 'turret_shroud',
            # The geared elbow. Without these J3 renders as a bare pivot and
            # the picture quietly shows an arm that has no elbow drive - the
            # same way it once showed a turret riding on nothing because the
            # three 608ZZ were missing from this file.
            'j3_gear', 'j3_pinion', 'j3_axle', 'j3_servo_cap']
    missing = [n for n in need if 'robotarm_' + n not in keep]
    assert not missing, (
        'not in the document: %r - run _check_ledger BATCH 0,1,2 first' % missing)

    def C(n):
        return keep['robotarm_' + n].component

    def bbox(n):
        return C(n).bRepBodies.item(0).boundingBox

    # ---- matrix plumbing ----------------------------------------------------
    # Fusion's x.transformBy(y) means x := y * x. So mul(a, b) == a * b is
    # "b in a's frame", which is the only composition this file ever does.
    def mul(a, b):
        m = b.copy()
        m.transformBy(a)
        return m

    def rot(angle_rad, axis):
        m = M3()
        m.setToRotation(angle_rad, axis, ORG)
        return m

    def rotx(d):
        return rot(math.radians(d), VEC(1, 0, 0))

    def rotz(d):
        return rot(math.radians(d), VEC(0, 0, 1))

    def trans(x, y, z):
        m = M3()
        t = m.translation
        t.x, t.y, t.z = x, y, z
        m.translation = t
        return m

    # ---- the chain, joint by joint ------------------------------------------
    l1, l2 = gv('ua_l1'), gv('fa_l2')
    yaw = rotz(J1_YAW_DEG)

    # The bracket's race face is its own bbox floor, and it lands on the
    # rollers at tt_race_z. Taken from the body rather than recomputed, so the
    # render cannot disagree with the part about where the arm sits.
    B = mul(yaw, trans(0, 0, gv('tt_race_z') - bbox('shoulder_bracket').minPoint.z))

    # upper_arm is drawn with its origin on J3 and J2 at y = -l1.
    M_ua = mul(B, mul(rotx(J2_PITCH_DEG), trans(0, l1, 0)))
    # forearm is drawn with its origin on J4 and J3 at y = -l2.
    M_fa = mul(M_ua, mul(rotx(J3_PITCH_DEG), trans(0, l2, 0)))
    # wrist_roll shares the forearm's frame exactly - that is what the shared
    # wr_ block buys. At pitch 0 it is the identity.
    M_roll = mul(M_fa, rotx(J4_PITCH_DEG))

    # rotator. The PLANE is lib/joints.J5_ROTATOR_ORIGIN_PARTS - this line
    # read wro_y_front, the housing front face, which is wrt_hub_h above the
    # seat the rotator is located by, so the whole hand hung 1.30 mm proud in
    # every preview render. See lib/joints.py.
    m = rotz(J5_ROLL_DEG)
    m.transformBy(rot(-math.pi / 2, VEC(1, 0, 0)))
    t = m.translation
    t.y = sum(gv(_p) for _p in J5_ROTATOR_ORIGIN_PARTS)
    m.translation = t
    M_rot = mul(M_roll, m)

    # The head bolts to the rotator's front face. Derived from the two bodies
    # rather than typed: the shell's tail face is its bbox floor in Y, the
    # rotator's front face is its bbox ceiling in Z, and R_x(90) takes one
    # normal to the other.
    shell_tail = bbox('grip_shell').minPoint.y
    rot_front = bbox('wrist_rotator').maxPoint.z
    m = rotx(90)
    t = m.translation
    t.z = rot_front - shell_tail
    m.translation = t
    M_shell = mul(M_rot, m)

    # ---- the head, verbatim from _check_grip -------------------------------
    s = J6_OPEN_MM

    def pinion_at(dist):
        mm_ = rot(G.s_to_phase(dist), VEC(0, 0, 1))
        mm_.transformBy(rot(-math.pi / 2, VEC(1, 0, 0)))
        return mul(trans(0, G.PINION_BACK_Y / 10, 0), mm_)

    turned = M3()
    turned.setToRotation(math.pi, VEC(0, 1, 0), ORG)

    # ---- hubs ---------------------------------------------------------------
    # Placed unpitched: at a joint the hex is buried in its socket, so the only
    # thing its spin changes is a picture nobody can see.
    def place_hub(sx, y_p, plate_in):
        mm_ = rotz(90)
        mm_.transformBy(rot(-sx * math.pi / 2, VEC(0, 1, 0)))
        tt = mm_.translation
        tt.x = sx * plate_in
        tt.y = y_p
        mm_.translation = tt
        return mm_

    sb_in, fa_in = gv('sb_plate_in'), gv('fa_plate_in')

    # ---- lay it all out -----------------------------------------------------
    add = root.occurrences.addExistingComponent
    placed = []

    # The turntable's fixed half does NOT yaw - that is the whole point of it.
    placed.append(('turntable_stator', add(C('turntable_stator'), M3())))
    placed.append(('turntable_ring', add(C('turntable_ring'), M3())))

    placed.append(('shoulder_bracket', add(C('shoulder_bracket'), B)))
    placed.append(('shoulder_hub', add(C('shoulder_hub'),
                                       mul(B, place_hub(+1, 0.0, sb_in)))))
    placed.append(('hub_j2m', add(C('wrist_hub'), mul(B, place_hub(-1, 0.0, sb_in)))))

    placed.append(('upper_arm', add(C('upper_arm'), M_ua)))
    placed.append(('forearm', add(C('forearm'), M_fa)))
    for sx, tag in ((+1, 'p'), (-1, 'm')):
        placed.append(('hub_j4' + tag, add(C('wrist_hub'),
                                           mul(M_fa, place_hub(sx, 0.0, fa_in)))))

    # ---- the geared elbow ---------------------------------------------------
    # J3 IS NOT TWO wrist_hubs ANY MORE. The drive side carries j3_gear, the
    # idler side j3_axle running in a 608ZZ, and the servo hangs outboard on
    # j3_servo_cap over a standoff. Each frame is written as the images of the
    # part's own axes in the forearm's, because "rotate it 90 degrees" is how
    # the J2 preview bearings ended up tangential instead of radial.
    po, fr = gv('fa_plate_out'), gv('fa_free')
    so_ = gv('fa_j3_standoff')
    y_pin = -l2 + gv('fa_j3_centre')
    face = gv('jp_face')

    def frame(origin, ax, ay, az):
        m = M3()
        m.setWithCoordinateSystem(P3(*origin), VEC(*ax), VEC(*ay), VEC(*az))
        return m

    # j3_gear: its +Z runs OUTBOARD on -X, and its z 0 is the disc's inner
    # face, standing fa_free off the plate.
    M_gear = frame((-(po + fr), -l2, 0.0), (0, 0, 1), (0, 1, 0), (-1, 0, 0))
    # j3_pinion: coplanar teeth, so its seat face is the gear band's OUTBOARD
    # end and its +Z runs back inboard.
    M_pin = frame((-(po + fr + face), y_pin, 0.0), (0, 0, 1), (0, -1, 0), (1, 0, 0))
    # j3_axle: hex face on the upper arm's socket FLOOR, journal running out.
    M_axle = frame((gv('ua_half_x') - gv('ua_socket_d'), -l2, 0.0),
                   (0, 0, 1), (0, -1, 0), (1, 0, 0))
    # j3_servo_cap: seats on the standoff's end face; its local X runs along
    # the arm and its +Z outboard.
    M_cap = frame((-(po + so_), y_pin, 0.0), (0, 1, 0), (0, 0, -1), (-1, 0, 0))

    for nm, mm_ in (('j3_gear', M_gear), ('j3_pinion', M_pin),
                    ('j3_axle', M_axle), ('j3_servo_cap', M_cap)):
        placed.append((nm, add(C(nm), mul(M_fa, mm_))))

    # THE ASSERT THE BEARING PREVIEW DID NOT HAVE. Both gears must come out
    # with their axes along the forearm's X - that is what a spur pair on
    # parallel shafts means - and the pinion must land one centre distance
    # from the elbow. A frame written with a sign flipped still renders as a
    # confident-looking picture of a gearbox that cannot turn.
    for nm, mm_ in (('j3_gear', M_gear), ('j3_pinion', M_pin)):
        ax = mm_.getAsCoordinateSystem()[3]
        assert abs(abs(ax.x) - 1.0) < 1e-9 and abs(ax.y) < 1e-9 and abs(ax.z) < 1e-9, (
            '%s comes out with its axis at (%.3f, %.3f, %.3f) - a spur pair on '
            'parallel shafts has both axes along X' % (nm, ax.x, ax.y, ax.z))
    _o_g = M_gear.getAsCoordinateSystem()[0]
    _o_p = M_pin.getAsCoordinateSystem()[0]
    _d = math.hypot(_o_g.y - _o_p.y, _o_g.z - _o_p.z)
    assert abs(_d - gv('fa_j3_centre')) < 1e-6, (
        'the gears are %.3f mm apart and the pair is cut for %.3f'
        % (_d * 10, gv('fa_j3_centre') * 10))
    placed.append(('wrist_roll', add(C('wrist_roll'), M_roll)))
    placed.append(('wrist_rotator', add(C('wrist_rotator'), M_rot)))

    placed.append(('grip_shell_a', add(C('grip_shell'), M_shell)))
    placed.append(('grip_shell_b', add(C('grip_shell'), mul(M_shell, turned))))
    placed.append(('gripper_pinion', add(C('gripper_pinion'), mul(M_shell, pinion_at(s)))))
    for sgn, tag in ((1, 'a'), (-1, 'b')):
        base = turned if sgn < 0 else M3()
        placed.append(('grip_jaw_' + tag, add(C('grip_jaw'),
                                              mul(M_shell, mul(trans(sgn * s / 10, 0, 0), base)))))
        placed.append(('grip_finger_' + tag, add(C('grip_finger'), mul(M_shell, mul(
            trans(sgn * (s - G.FINGER_LEAD) / 10, G.FINGER_Y0 / 10, 0), base)))))

    # ---- the base: platter, lid, J1 hub, roller caps - all in the stator frame
    placed.append(('base_platter', add(C('base_platter'), M3())))
    placed.append(('base_lid', add(C('base_lid'), M3())))
    placed.append(('turret_shroud', add(C('turret_shroud'), M3())))
    from lib.j1_drive import J1_DECK_Z_MM, J1_HUB  # noqa: E402
    placed.append(('j1_hub', add(C('j1_hub'), mul(yaw, trans(0, 0, (J1_DECK_Z_MM + J1_HUB.seat_z) / 10)))))
    import ast  # noqa: E402
    _src = open(os.path.join(REPO, 'models', 'robotarm', 'turntable_stator.py')).read()
    ROLL_AZ = [ast.literal_eval(n.value) for n in ast.parse(_src).body
               if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'ROLL_AZ'][0]
    _seat = gv('tt_roller_r') - gv('tt_roller_w') / 2 - gv('rc_t')
    for i, az in enumerate(ROLL_AZ):
        a = math.radians(az)
        c_, s_ = math.cos(a), math.sin(a)
        placed.append(('roller_cap_%d' % i, add(C('roller_cap'), frame(
            (_seat * c_, _seat * s_, gv('tt_axle_z')), (-s_, c_, 0), (0, 0, 1), (c_, s_, 0)))))

    # The unposed originals have to go dark, but ONLY after the posed copies
    # exist and have been switched on explicitly. Hiding an occurrence first
    # and adding from it afterwards hands the new occurrence the same dark
    # state, and the render comes back as an empty grid with a camera fitted
    # to nothing.
    for _, o in placed:
        o.isLightBulbOn = True
    for o in keep.values():
        o.isLightBulbOn = False
    for _, o in placed:
        o.isLightBulbOn = True
    lit = sum(1 for _, o in placed if o.isLightBulbOn)
    assert lit == len(placed), (
        'only %d of %d posed occurrences are visible - the render would be empty'
        % (lit, len(placed)))

    # ---- the three 608ZZ, because without them the rotor floats --------------
    # Jonathan, looking at a render: "I cant see the rotating base touching the
    # base?" He was reading the picture correctly. The rotor does not touch the
    # stator ANYWHERE - it rides on three bearings, and the bearings were not
    # in this file, so the render showed a turret hanging in mid air with
    # nothing under it. The geometry was right and the picture was lying.
    #
    # Built here rather than imported: _check_j1 makes them in its own gate
    # document, which this one is not. Every dimension is READ - the radius,
    # height and azimuths from the stator's own tt_ parameters, the bearing
    # itself from lib/bearings - so this cannot drift from the part it sits in.
    from lib.bearings import CATALOG as BEARINGS          # noqa: E402
    b608 = BEARINGS['608ZZ']
    roller_r, axle_z = gv('tt_roller_r') * 10, gv('tt_axle_z') * 10
    assert abs(b608.od - gv('tt_roller_od') * 10) < 1e-6, (
        'the stator says the roller is Ø%.2f and lib/bearings says Ø%.2f'
        % (gv('tt_roller_od') * 10, b608.od))
    race_z = axle_z + b608.od / 2.0
    # RENAME FIRST, THEN DELETE - the project's idempotent-rebuild pattern.
    # Without it Fusion hands the second run 'preview_608ZZ_rollers (1)' and
    # the stale one stays in the document, hidden. That is not cosmetic: the
    # first check of this very fix measured the STALE rollers and reported the
    # bug as unfixed. A hidden wrong copy is worse than no copy.
    ROLL_ENV = 'preview_608ZZ_rollers'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == ROLL_ENV or c.name.startswith(ROLL_ENV + ' ('):
            c.name = ROLL_ENV + '_stale_' + str(i)
    for o in list(root.occurrences):
        if o.component.name.startswith(ROLL_ENV + '_stale_'):
            o.deleteMe()
    roll_occ = root.occurrences.addNewComponent(M3())
    roll_occ.component.name = ROLL_ENV
    assert roll_occ.component.name == ROLL_ENV, (
        'Fusion handed back %s - a stale roller component reserves the name'
        % roll_occ.component.name)
    rc = roll_occ.component
    for i, az in enumerate(ROLL_AZ):
        a = math.radians(az)
        cx, cy = roller_r * math.cos(a), roller_r * math.sin(a)
        # RADIAL axle. The roller has to ROLL, and the rotor above it moves
        # TANGENTIALLY, so the axis must be perpendicular to that motion and
        # parallel to the contact face - i.e. pointing straight out from the
        # J1 axis, like a trolley wheel. _check_j1 does this by drawing the
        # disc on XY and tipping it 90 deg about Y.
        #
        # So the sketch plane is the vertical one PERPENDICULAR to the radius
        # (it contains the tangent and Z), which is yZ swung to the azimuth -
        # NOT xZ, which contains the radius and puts the axle tangential. The
        # first version of this did exactly that: at az 90 the roller measured
        # 7 along X and 22 along Y, the wrong way round, and it would have
        # scrubbed rather than rolled. Jonathan caught it in the render.
        pl = rc.constructionPlanes.createInput()
        pl.setByAngle(rc.zConstructionAxis, adsk.core.ValueInput.createByReal(a),
                      rc.yZConstructionPlane)
        plane = rc.constructionPlanes.add(pl)
        # THAT PLANE CONTAINS THE J1 AXIS, so a circle drawn on it sits at
        # radius 0 - every roller rendered ON the axis. Offset it out to the
        # roller radius along its own (radial) normal first.
        pl2 = rc.constructionPlanes.createInput()
        pl2.setByOffset(plane, adsk.core.ValueInput.createByReal(roller_r / 10.0))
        plane = rc.constructionPlanes.add(pl2)
        sk = rc.sketches.add(plane)
        sk.isVisible = False
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(cx / 10.0, cy / 10.0, axle_z / 10.0)),
            b608.od / 20.0)
        prof = adsk.core.ObjectCollection.create()
        prof.add(sk.profiles.item(0))
        ei = rc.features.extrudeFeatures.createInput(
            prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setDistanceExtent(True, adsk.core.ValueInput.createByString(
            '%.4f mm' % (b608.width / 2.0)))
        rc.features.extrudeFeatures.add(ei).bodies.item(0).name = '608ZZ_%d' % i

        # PROVE the axle is radial, do not assume it. The disc's flat faces
        # are normal to its axis, so that normal must be the radial unit
        # vector. This is the assert the first version did not have, which is
        # why a roller mounted 90 deg out shipped into a render.
        body = rc.bRepBodies.item(rc.bRepBodies.count - 1)
        flats = []
        for k in range(body.faces.count):
            f = body.faces.item(k)
            if f.geometry.objectType == adsk.core.Plane.classType():
                n = f.geometry.normal
                flats.append((n.x, n.y, n.z))
        assert flats, 'roller %d has no flat face to take an axis from' % i
        _c = body.boundingBox
        _rc = math.hypot((_c.minPoint.x + _c.maxPoint.x) / 2, (_c.minPoint.y + _c.maxPoint.y) / 2) * 10
        assert abs(_rc - roller_r) < 0.5, 'roller %d sits at r %.2f, not %.2f' % (i, _rc, roller_r)
        nx, ny, nz = flats[0]
        dot = abs(nx * math.cos(a) + ny * math.sin(a))
        assert dot > 0.999 and abs(nz) < 0.001, (
            'roller %d at az %.0f has its axle %.1f deg off radial - it would '
            'scrub across the race instead of rolling along it'
            % (i, az, math.degrees(math.acos(min(1.0, dot)))))
    # construction planes render as orange glass in the middle of the turret
    for k in range(rc.constructionPlanes.count):
        rc.constructionPlanes.item(k).isLightBulbOn = False
    placed.append(('608ZZ_rollers', roll_occ))
    roll_occ.isLightBulbOn = True
    print('3 x 608ZZ Ø%.1f x %.1f at r %.1f, axle z %.1f -> race face z %.2f'
          % (b608.od, b608.width, roller_r, axle_z, race_z))
    print('  the rotor rides ON these, not on the stator: race face z %.2f'
          % race_z)

    # ---- the picture ---------------------------------------------------------
    vp = app.activeViewport
    # PET Plastic renders translucent, which turns a 23-piece assembly into
    # wireframe soup. Shaded-with-edges is what makes it readable.
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    # The layout grid sits at z 0 and everything below it - the whole base -
    # renders as if seen through frosted glass. Switch the grid off; it is a
    # UI toggle, not design state, so nothing in the document changes.
    grid = adsk.core.ListControlDefinition.cast(
        app.userInterface.commandDefinitions.itemById('ViewLayoutGridCommand').controlDefinition)
    grid.listItems.item(0).isSelected = False
    adsk.doEvents()
    print('layout grid shown: %s' % grid.listItems.item(0).isSelected)
    # and the ground shadow, which has no ground under it once the grid is
    # gone and reads as a smudge floating beside the arm. Item 1 is 'Off'.
    shadow = adsk.core.ListControlDefinition.cast(
        app.userInterface.commandDefinitions.itemById('ViewGroundShadowCommand').controlDefinition)
    shadow.listItems.item(1).isSelected = True
    adsk.doEvents()
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    # Fit to what is VISIBLE, not to root.boundingBox - that counts hidden
    # bodies too, which is how a camera ends up framing a pile at the origin.
    # Tracked by hand rather than with BoundingBox3D.combine: seeded from an
    # inverted box, combine() keeps the sentinel and reports a 20 000 000 mm
    # assembly with a straight face.
    lo = [1e18, 1e18, 1e18]
    hi = [-1e18, -1e18, -1e18]
    for _, o in placed:
        b = o.component.bRepBodies.item(0).createForAssemblyContext(o).boundingBox
        for i, (p_lo, p_hi) in enumerate(((b.minPoint.x, b.maxPoint.x),
                                          (b.minPoint.y, b.maxPoint.y),
                                          (b.minPoint.z, b.maxPoint.z))):
            lo[i] = min(lo[i], p_lo)
            hi[i] = max(hi[i], p_hi)
    assert max(hi) < 1e6, 'the visible bounding box never got seeded'
    cx, cy, cz = [(lo[i] + hi[i]) / 2 for i in range(3)]
    span = max(hi[i] - lo[i] for i in range(3))
    dist = span * 4

    written = []
    for name, (d, up) in VIEWS.items():
        norm = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        cam = vp.camera
        cam.target = adsk.core.Point3D.create(cx, cy, cz)
        cam.eye = adsk.core.Point3D.create(cx + d[0] / norm * dist,
                                           cy + d[1] / norm * dist,
                                           cz + d[2] / norm * dist)
        cam.upVector = adsk.core.Vector3D.create(up[0], up[1], up[2])
        cam.isFitView = True
        vp.camera = cam
        vp.refresh()
        adsk.doEvents()
        path = os.path.join(OUT, name + '.png')
        if vp.saveAsImageFile(path, W, H):
            written.append(path)

    # CLOSE-UPS of the two things this revision changed most: the head and the
    # base. Framed on the visible bodies of each, like the whole-arm views.
    def frame_on(pred):
        lo_, hi_ = [1e18] * 3, [-1e18] * 3
        for nm_, o in placed:
            if not pred(nm_):
                continue
            b = o.component.bRepBodies.item(0).createForAssemblyContext(o).boundingBox
            for i, (a_, c_) in enumerate(((b.minPoint.x, b.maxPoint.x), (b.minPoint.y, b.maxPoint.y),
                                          (b.minPoint.z, b.maxPoint.z))):
                lo_[i], hi_[i] = min(lo_[i], a_), max(hi_[i], c_)
        return lo_, hi_
    CLOSE = {'head_close': (lambda n: n.startswith('grip') or n == 'wrist_rotator', (1.0, 0.9, 0.7)),
             'base_close': (lambda n: n in ('base_platter', 'base_lid', 'turntable_stator', 'turret_shroud',
                                            'turntable_ring', 'j1_hub', '608ZZ_rollers')
                            or n.startswith('roller_cap'), (1.0, -1.2, 0.8))}
    for name, (pred, d) in CLOSE.items():
        lo_, hi_ = frame_on(pred)
        c = [(lo_[i] + hi_[i]) / 2 for i in range(3)]
        sp = max(hi_[i] - lo_[i] for i in range(3))
        norm = math.sqrt(sum(x * x for x in d))
        cam = vp.camera
        cam.target = adsk.core.Point3D.create(*c)
        cam.eye = adsk.core.Point3D.create(*[c[i] + d[i] / norm * sp * 3 for i in range(3)])
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
        cam.isFitView = False
        vp.camera = cam
        cam = vp.camera
        cam.viewExtents = sp * 1.3
        vp.camera = cam
        vp.refresh()
        adsk.doEvents()
        path = os.path.join(OUT, name + '.png')
        if vp.saveAsImageFile(path, W, H):
            written.append(path)

    print('posed %d occurrences' % len(placed))
    print('J1 %.0f  J2 %.0f  J3 %.0f  J4 %.0f  J5 %.0f  jaws %.0f mm open each' % (
        J1_YAW_DEG, J2_PITCH_DEG, J3_PITCH_DEG, J4_PITCH_DEG,
        J5_ROLL_DEG, J6_OPEN_MM))
    print('head on the rotator: shell tail y %.2f -> rotator front z %.2f, '
          'offset %.2f mm' % (shell_tail * 10, rot_front * 10,
                              (rot_front - shell_tail) * 10))
    print('assembly bbox mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f' % (
        lo[0] * 10, hi[0] * 10, lo[1] * 10, hi[1] * 10, lo[2] * 10, hi[2] * 10))
    print('reach from the yaw axis: %.0f mm; height %.0f mm' % (
        math.hypot(max(abs(lo[0]), abs(hi[0])), max(abs(lo[1]), abs(hi[1]))) * 10,
        (hi[2] - lo[2]) * 10))
    for p in written:
        print('wrote %s' % p)
