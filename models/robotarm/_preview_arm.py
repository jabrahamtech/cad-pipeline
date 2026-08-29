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

import importlib.util
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
OUT = os.path.join(REPO, 'docs', 'robotarm')
W, H = 1800, 1300

# The pose. Positive pitch is UP: a rotation about +X carries +Y toward +Z.
J1_YAW_DEG = 25.0          # turret, away from the assembly position
J2_PITCH_DEG = 35.0        # shoulder, up and forward
J3_PITCH_DEG = -55.0       # elbow, relative to the upper arm
J4_PITCH_DEG = 15.0        # wrist pitch, relative to the forearm
J5_ROLL_DEG = 0.0
J6_BLADE_DEG = 12.0        # part closed, so the mouth reads as a mouth

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
            'pruner_shell', 'pruner_rack', 'pruner_blade', 'gripper_pinion']
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

    # rotator, verbatim from _check_wrist.place_rotator
    m = rotz(J5_ROLL_DEG)
    m.transformBy(rot(-math.pi / 2, VEC(1, 0, 0)))
    t = m.translation
    t.y = gv('wro_y_front')
    m.translation = t
    M_rot = mul(M_roll, m)

    # The head bolts to the rotator's front face. Derived from the two bodies
    # rather than typed: the shell's tail face is its bbox floor in Y, the
    # rotator's front face is its bbox ceiling in Z, and R_x(90) takes one
    # normal to the other.
    shell_tail = bbox('pruner_shell').minPoint.y
    rot_front = bbox('wrist_rotator').maxPoint.z
    m = rotx(90)
    t = m.translation
    t.z = rot_front - shell_tail
    m.translation = t
    M_shell = mul(M_rot, m)

    # ---- the head, verbatim from _check_pruner ------------------------------
    tail_r = gv('pb_tail_r')
    pivot_y = tail_r + gv('pr_pin_y')
    offset, face, r_pitch = gv('gr_offset'), gv('gr_face'), gv('gr_r_pitch')
    x_a = gv('pr_tooth_lead') - int(round(gv('pr_rack_teeth'))) * gv('pr_pitch')
    th = math.radians(J6_BLADE_DEG)
    s = tail_r * math.tan(th)

    def blade_at(theta, turned):
        mm_ = M3()
        if turned:
            mm_.setToRotation(math.pi, VEC(0, 1, 0), ORG)
        mm_.transformBy(rot(theta, VEC(0, 0, 1)))
        tt = mm_.translation
        tt.y = pivot_y
        mm_.translation = tt
        return mm_

    def rack_at(dist, turned):
        mm_ = M3()
        if turned:
            mm_.setToRotation(math.pi, VEC(0, 1, 0), ORG)
        tt = mm_.translation
        tt.x = -dist if turned else dist
        tt.z = -offset if turned else offset
        mm_.translation = tt
        return mm_

    def pinion_at(dist):
        mm_ = rot(-math.pi / 2 + (x_a + dist) / r_pitch, VEC(0, 0, 1))
        mm_.transformBy(rot(-math.pi / 2, VEC(1, 0, 0)))
        tt = mm_.translation
        tt.y = -face / 2
        mm_.translation = tt
        return mm_

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
        placed.append(('hub_j3' + tag, add(C('wrist_hub'),
                                           mul(M_fa, place_hub(sx, -l2, fa_in)))))
        placed.append(('hub_j4' + tag, add(C('wrist_hub'),
                                           mul(M_fa, place_hub(sx, 0.0, fa_in)))))
    placed.append(('wrist_roll', add(C('wrist_roll'), M_roll)))
    placed.append(('wrist_rotator', add(C('wrist_rotator'), M_rot)))

    placed.append(('pruner_shell_a', add(C('pruner_shell'), M_shell)))
    placed.append(('pruner_shell_b', add(C('pruner_shell'), mul(M_shell, turned))))
    placed.append(('gripper_pinion', add(C('gripper_pinion'),
                                         mul(M_shell, pinion_at(s)))))
    for flip, tag in ((False, 'a'), (True, 'b')):
        placed.append(('pruner_rack_' + tag, add(C('pruner_rack'),
                                                 mul(M_shell, rack_at(s, flip)))))
        placed.append(('pruner_blade_' + tag, add(C('pruner_blade'),
                                                  mul(M_shell, blade_at(th, flip)))))

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
    roll_occ = root.occurrences.addNewComponent(M3())
    roll_occ.component.name = 'preview_608ZZ_rollers'
    rc = roll_occ.component
    for i, az in enumerate((90.0, 210.0, 330.0)):
        a = math.radians(az)
        cx, cy = roller_r * math.cos(a), roller_r * math.sin(a)
        # RADIAL axle: the disc's own axis is horizontal, pointing outward,
        # so the sketch plane is the vertical one containing that radius.
        pl = rc.constructionPlanes.createInput()
        pl.setByAngle(rc.zConstructionAxis, adsk.core.ValueInput.createByReal(a),
                      rc.xZConstructionPlane)
        plane = rc.constructionPlanes.add(pl)
        sk = rc.sketches.add(plane)
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
    placed.append(('608ZZ_rollers', roll_occ))
    roll_occ.isLightBulbOn = True
    print('3 x 608ZZ Ø%.1f x %.1f at r %.1f, axle z %.1f -> race face z %.2f'
          % (b608.od, b608.width, roller_r, axle_z, race_z))
    _rotor_z = C('shoulder_bracket').bRepBodies.item(0).boundingBox.maxPoint.z * 10
    print('  the rotor rides ON these, not on the stator: race face z %.2f'
          % race_z)

    # ---- the printed platter, for scale --------------------------------------
    # Imported, not modelled. If the STEP is missing the render still works and
    # just looks like the arm is floating, which is what it did before.
    step = os.path.join(REPO, 'legacy', 'exports', 'robotarm', 'base_platter_v1.step')
    PLATTER = 'legacy_base_platter'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name.startswith(PLATTER):
            c.name = PLATTER + '_stale_' + str(i)
    for o in list(root.occurrences):
        if o.component.name.startswith(PLATTER + '_stale_'):
            o.deleteMe()
    if os.path.exists(step):
        imp = app.importManager
        before = set(o.component.name for o in root.occurrences)
        imp.importToTarget(imp.createSTEPImportOptions(step), root)
        for o in list(root.occurrences):
            if o.component.name not in before and o.component.bRepBodies.count:
                o.component.name = PLATTER
                o.transform = trans(0, 0, -4.2)   # its rim top -> z 0
                placed.append((PLATTER, o))
                break

    # ---- the picture ---------------------------------------------------------
    vp = app.activeViewport
    # PET Plastic renders translucent, which turns a 23-piece assembly into
    # wireframe soup. Shaded-with-edges is what makes it readable.
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
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

    print('posed %d occurrences' % len(placed))
    print('J1 %.0f  J2 %.0f  J3 %.0f  J4 %.0f  J5 %.0f  blades %.0f deg' % (
        J1_YAW_DEG, J2_PITCH_DEG, J3_PITCH_DEG, J4_PITCH_DEG,
        J5_ROLL_DEG, J6_BLADE_DEG))
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
