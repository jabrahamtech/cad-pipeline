"""robotarm/wrist_rotator - Fusion MCP generating script.

Rebuilds `robotarm_wrist_rotator` (idempotent). Spec:
specs/robotarm/wrist_rotator.md, styled per specs/robotarm/_style.md.

J5. A disc on the roll SG90's horn, carrying the four M3 inserts every
effector bolts to. It is the swap point of the whole arm: pull four screws
and the hand comes off.

Local frame: the roll axis is +Z. z = 0 is the BACK face, the one that
faces the servo; the effector bolts to the front.

The bolt pattern is small (+/-11, +/-9) on purpose. This disc SPINS, so
every millimetre of pattern is two millimetres of swept diameter, and the
load on it is trivial: the hand's weight at its centre of mass works out at
about 1 N per bolt. Spreading the pattern would buy strength nothing needs
and cost sweep everything notices.

Print orientation: BACK FACE ON THE BED, built +Z. The insert bosses are
then vertical holes, which is the orientation heat-set inserts want, and
the horn pocket is a prism opening at the bed. No support.

SG90 horn dimensions are DATASHEET (lib/servo.py). The relief swallows the
output boss as well as the horn, so this disc sits on the servo's case top
rather than 4.2 mm above it - the roll joint is that much shorter for it.
"""

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_wrist_rotator'
BODY_NAME = 'wrist_rotator'
PREFIX = 'wrt_'
STYLE = 'sty_'
PH_FORM = 'disc'
PH_HORN = 'horn interface'
PH_MOUNT = 'effector inserts'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_HORN, PH_MOUNT, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A rotator is a joint, so it is dark.
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

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    param('bolt_x', '11.0 mm', 'effector bolt pattern - matches gs_eff_bolt_x')
    param('bolt_z', '9.0 mm', 'effector bolt pattern - matches gs_eff_bolt_z')
    param('insert_d', '4.0 mm', 'M3 heat-set insert hole - design_rules FASTENER_MM CALIBRATED')
    param('insert_depth', '5.5 mm', 'insert length + 1 - fasteners_inserts.md')
    param('boss_od', '6.4 mm', 'insert boss OD - wall >= 2.4 around the hole')
    param('disc_d', '36.0 mm',
          'derived by hand from the bolt pattern: corner radius 14.2 plus a boss '
          'wall. Any bigger and the swept circle starts to matter')
    param('disc_t', '6.0 mm', 'thick enough to sink an M3 insert from the front')
    param('hub_d', '10.5 mm',
          'central hub on the BACK face, carrying the rest of the horn relief.\n           A disc thick enough to swallow boss + horn everywhere would be 10 mm\n           of solid PETG; this puts the depth only where it is needed. Sized to\n           run inside the roll housing\'s rotator bore.')
    param('hub_h', '4.0 mm', 'hub height behind the disc')

    # --- SG90 horn + boss, DATASHEET (lib/servo.py) ---------------------------
    param('boss_h', '4.2 mm', 'SG90 output boss height above the case top')
    param('horn_hub_d', '7.15 mm', 'SG90 horn hub 7.0 DATASHEET + press 0.15')
    param('horn_arm_w', '3.95 mm', 'SG90 horn arm 3.8 DATASHEET + press 0.15')
    param('horn_arm_r', '6.0 mm', 'horn arm TRIMMED to this radius at assembly')
    param('relief_d', PREFIX + 'boss_h + '
          '3.9 mm', 'derived: horn hub 3.8 + 0.1 PLUS the boss, so the disc sits on the case top')
    param('horn_arm_depth', '1.6 mm', 'horn blade 1.5 DATASHEET + 0.1')
    param('screw_d', '5.5 mm', 'driver access to the horn retaining screw')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild ---------------------------------------------------
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

    def disc(name, x_cm, y_cm, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_cm, y_cm, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    # ---- values in cm -----------------------------------------------------------
    corner = (val('bolt_x') ** 2 + val('bolt_z') ** 2) ** 0.5
    assert corner + val('boss_od') / 2 <= val('disc_d') / 2, (
        'the bolt bosses reach %.2f mm, past the %.2f mm disc radius'
        % ((corner + val('boss_od') / 2) * 10, val('disc_d') / 2 * 10))
    # The relief and the inserts are radially separate, not stacked - the check
    # is that each has depth, and that they do not overlap in RADIUS.
    assert val('relief_d') <= val('disc_t') + val('hub_h') - val('tol'), (
        'the horn relief (%.2f) runs out of the back of the disc + hub (%.2f)'
        % (val('relief_d') * 10, (val('disc_t') + val('hub_h')) * 10))
    assert val('insert_depth') <= val('disc_t'), 'the inserts run out of the disc'
    assert corner - val('boss_od') / 2 > val('hub_d') / 2, (
        'the insert bosses overlap the central hub')

    # ---- phase 1: the disc --------------------------------------------------------
    t0 = design.timeline.count
    disc('rotator_disc', 0, 0, val('disc_d'), '0.0 mm', PREFIX + 'disc_t', NEW)
    disc('horn_hub', 0, 0, val('hub_d'), '-' + PREFIX + 'hub_h', PREFIX + 'hub_h',
         adsk.fusion.FeatureOperations.JoinFeatureOperation)
    group(t0, PH_FORM)

    # ---- phase 2: horn interface ----------------------------------------------------
    t1 = design.timeline.count
    disc('horn_relief', 0, 0, val('horn_hub_d'), '-' + PREFIX + 'hub_h',
         PREFIX + 'relief_d', CUT)
    sk_arm = sketch(comp.xYConstructionPlane, 'sk_horn_arm_slot')
    sk_arm.sketchCurves.sketchLines.addTwoPointRectangle(
        mpt(sk_arm, -val('horn_arm_r'), -val('horn_arm_w') / 2, 0),
        mpt(sk_arm, val('horn_arm_r'), val('horn_arm_w') / 2, 0))
    extrude(profiles(sk_arm, expected=1), CUT,
            PREFIX + 'boss_h - ' + PREFIX + 'hub_h',
            PREFIX + 'horn_arm_depth', 'horn_arm_slot')
    disc('horn_screw_bore', 0, 0, val('screw_d'), '-' + PREFIX + 'hub_h',
         PREFIX + 'hub_h + ' + PREFIX + 'disc_t', CUT)
    group(t1, PH_HORN)

    # ---- phase 3: effector inserts ----------------------------------------------------
    t2 = design.timeline.count
    for sx in (-1, 1):
        for sz in (-1, 1):
            disc('insert_%d_%d' % (sx, sz), sx * val('bolt_x'), sz * val('bolt_z'),
                 val('insert_d'),
                 PREFIX + 'disc_t - ' + PREFIX + 'insert_depth',
                 PREFIX + 'insert_depth', CUT)
    group(t2, PH_MOUNT)

    # ---- phase 4: finish ------------------------------------------------------------
    t3 = design.timeline.count
    for z_pick, nm in ((-val('hub_h'), 'bed_face_chamfer'), (val('disc_t'), 'front_face_chamfer')):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.z - z_pick) < val('tol')
                    and abs(eb.maxPoint.z - z_pick) < val('tol')):
                col.add(e)
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = nm
    group(t3, PH_FINISH)

    # ---- identity + diagnostics --------------------------------------------------------
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
    print('disc OD %.1f x %.1f | effector pattern 4 x M3 at +/-%.1f, +/-%.1f (corner %.2f)' % (
        val('disc_d') * 10, val('disc_t') * 10, val('bolt_x') * 10, val('bolt_z') * 10,
        corner * 10))
    print('horn relief %.2f deep (swallows the %.1f mm boss) through a %.1f mm back hub' % (
        val('relief_d') * 10, val('boss_h') * 10, val('hub_h') * 10))
    print('inserts %.1f deep from the front, %.2f mm clear of the hub radially' % (
        val('insert_depth') * 10, (corner - val('boss_od') / 2 - val('hub_d') / 2) * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
