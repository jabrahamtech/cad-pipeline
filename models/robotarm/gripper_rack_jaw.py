"""robotarm/gripper_rack_jaw - Fusion MCP generating script.

Rebuilds `robotarm_gripper_rack_jaw` (idempotent). Spec:
specs/robotarm/gripper_rack_jaw.md.

Local frame:
  x = 0 at the JAW GRIPPING FACE, +x outboard; the rack runs out to -x
  y = 0 at the rack's face-width centre, +y forward (the approach direction)
  z = 0 on the rack's PITCH LINE, teeth toward -z, rack back toward +z

ONE printed design, TWO copies. The second goes on TURNED OVER - rotated
180 deg about the Y axis, which maps (x, y, z) -> (-x, y, -z) and lands it
exactly on the opposite rack channel with its teeth facing the pinion and
its jaw face pointing back at the first. That symmetry is the whole reason
the pinion axis runs along the arm instead of across it.

Print orientation: RACK BACK FACE (z = +z_back) ON THE BED, part built in
-z. Every cross-section then shrinks or holds going up, so the part needs
no support anywhere: the teeth are flanked at the pressure angle (20 deg
off the build direction), the arm is a subset of the rack's footprint, and
the blade is on the bed from the first layer. Tooth loads run along x,
which is in-layer in that orientation (gears_drives.md).

The SHARED gear block (gr_*) is defined identically in gripper_pinion.py.
Editing it in one place only is a bug: see the "pinion mesh" row of
specs/robotarm/_assembly.md.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_gripper_rack_jaw'
BODY_NAME = 'gripper_rack_jaw'
PREFIX = 'rj_'
SHARED = 'gr_'      # gear contract shared with gripper_pinion.py
STYLE = 'sty_'      # design language - specs/robotarm/_style.md
# _style.md rule 5: two-tone by PART. The jaws are body, so they are light.
APPEARANCE_HINTS = [('plastic', 'yellow'), ('paint', 'yellow'), ('yellow',),
                    ('plastic',)]
MATERIAL_NAME = 'PET Plastic'
PHASES = ['rack bar', 'jaw arm and blade', 'finish']


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

    def shared(name, expr, comment='', units='mm'):
        _set(SHARED + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def sval(name):
        return ups.itemByName(SHARED + name).value

    def tval(name):
        return ups.itemByName(STYLE + name).value

    # --- SHARED gear contract: identical to gripper_pinion.py -------------
    shared('module', '1.5 mm', 'gear module - design_rules GEAR_PREFERRED_MODULE_MM')
    shared('teeth', '12', 'pinion tooth count - gears_drives.md floor at 20 deg PA', '')
    shared('pa', '20 deg', 'pressure angle - gears_drives.md', 'deg')
    shared('ded_f', '1.25', 'dedendum factor, standard full-depth tooth', '')
    shared('face', '8.0 mm', 'face width, >= 5 x module - design_rules')
    shared('backlash', '0.2 mm', 'backlash added at the centre distance - design_rules GEAR_BACKLASH_MM')
    shared('r_pitch', SHARED + 'module * ' + SHARED + 'teeth / 2', 'derived pitch radius')
    shared('offset', SHARED + 'r_pitch + ' + SHARED + 'backlash', 'pinion axis to rack PITCH LINE - the centre distance')
    shared('stroke', '20.0 mm', 'travel of ONE rack; jaw opening is twice this')
    shared('r_tip', SHARED + 'r_pitch + ' + SHARED + 'module', 'derived pinion tip radius')
    shared('rack_web', '3.5 mm', 'rack back thickness above the tooth root')
    shared('rack_back', SHARED + 'module * ' + SHARED + 'ded_f + ' + SHARED + 'rack_web',
           'derived rack back, above the pitch line - the shell channel floor rides on this')
    shared('arm_thk', '9.0 mm',
           'jaw arm and blade thickness in x - thick enough to carry a facet\n            that reads, with the mass taken back out as a recessed panel')
    shared('blade_half', '8.0 mm',
           'how far a blade reaches PAST the gripper centre plane - so it also says\n            how far each arm intrudes into the OTHER shell half')

    # --- STYLE: specs/robotarm/_style.md, shared by every part -------------
    style('facet', '4.0 mm', '45 deg chamfer on outer edges - _style.md rule 1')
    style('radius', '6.0 mm',
          'plan-view corner radius - _style.md rule 2. MUST exceed sty_facet')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- rack ------------------------------------------------------------
    param('pitch', SHARED + 'module * PI', 'derived circular pitch of the rack')
    param('rack_teeth', '8', 'rack tooth count - sized in code to keep mesh over the whole stroke', '')
    param('tooth_lead', '8.0 mm', 'toothed run reaches this far OUTBOARD of the jaw face')
    param('end_lead', '3.0 mm', 'plain rack beyond the last tooth at each end')

    # --- jaw --------------------------------------------------------------
    param('reach', SHARED + 'offset + ' + SHARED + 'blade_half', 'derived: pitch line down to the blade tip')
    param('arm_y', '16.0 mm', 'arm front face; the blade starts here')
    param('blade_len', '24.0 mm', 'blade length forward of the arm')
    param('arm_clear', '0.4 mm', 'free fit off the OTHER rack front face - design_rules')
    param('tie_thk', '6.0 mm',
          'the tie into the rack is THINNER than the jaw. Keeping it flush at 9 mm\n           put a 0.4 mm notch in the jaw outer face where the rack ends, and a\n           chamfer will not run through that - it fails ASM_BL_END_TOO_CMPLX.\n           Recessing it leaves the visible face one clean rectangle.')
    param('jaw_facet', SHARED + 'arm_thk / 3',
          'derived: the facet scales with the thickness it cuts into - _style.md rule 1')
    param('panel_depth', '5.0 mm',
          'recessed panel in the blade outer face - floors 1 mm clear of the\n           V-groove apex, which is the deepest it can go')
    param('panel_inset', '3.0 mm', 'frame left around the recessed panel')
    param('v_depth', '3.0 mm', 'V-groove depth so round stock self-centres')
    param('v_half', '3.0 mm', 'V-groove half-opening on the jaw face')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild ----------------------------------------------
    # Idempotent rebuild. Deleting an occurrence does NOT release its
    # component's name straight away, so a plain delete-then-create makes
    # Fusion silently hand the new component "<name> (1)" - and every later
    # lookup by name misses it. Rename the outgoing component out of the way
    # first, then assert the new one actually got the name it asked for.
    # RENAME FIRST, THEN DELETE. Deleting a component's LAST occurrence orphans
    # it: it drops straight out of allComponents while still holding its name,
    # so a rename afterwards cannot reach it. Components also outlive their last
    # occurrence until the document is saved, so clear the name across the WHOLE
    # design, not just what is placed.
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
            # WITHOUT THIS, A CUT EATS EVERY OTHER COMPONENT IN THE DOCUMENT.
            # An extrude with no participantBodies takes part with everything
            # it intersects, across component boundaries, and reports nothing.
            # In a shared assembly document that means one part's pocket
            # quietly hollows out its neighbours - measured here as a pinion
            # losing 95 % of its volume and a rack going to zero while
            # isValid stayed True. Scope every non-NEW operation to this
            # component's own bodies.
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

    def box(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        """Axis-aligned block: XY rectangle in cm, Z from parameter expressions."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0, 0), mpt(sk, x1, y1, 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def chamfer_at_z(z_pick, name):
        tol = val('tol')
        edges = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if abs(eb.minPoint.z - z_pick) < tol and abs(eb.maxPoint.z - z_pick) < tol:
                edges.add(e)
        inp = chf.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(STYLE + 'ef'), False)
        chf.add(inp).name = name
        return edges.count

    def style_the_jaw():
        """_style.md on the two surfaces anyone actually sees.

        The rack bar is buried in the shell, so it is left alone. The arm and
        blade get R6 on their silhouette - the edges that run along x, which
        on this part ARE the outline corners - and a facet on the outer face
        sized to the 9 mm thickness it cuts into, not to the 4 mm the primary
        volumes use. The GRIPPING face (x = 0) is left dead flat: it is a
        functional surface and _style.md rule 1 exempts those.

        The jaws are 9 mm, not 6. A 6 mm blade cannot carry a facet that
        reads - the chamfer would be two thirds of its thickness, and Fusion
        refuses it outright - and it looks like sheet stock. The mass that
        buys goes straight back out as the recessed panel cut below.
        """
        tol = val('tol')
        seen = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            p1, p2 = e.startVertex.geometry, e.endVertex.geometry
            along_x = (abs(p1.y - p2.y) < tol and abs(p1.z - p2.z) < tol
                       and abs(p1.x - p2.x) > tol)
            on_jaw = abs(max(p1.x, p2.x) - sval('arm_thk')) < tol
            if along_x and on_jaw and min(p1.y, p2.y) > half_face:
                seen.add(e)
        f_inp = comp.features.filletFeatures.createInput()
        f_inp.addConstantRadiusEdgeSet(seen, V(STYLE + 'radius'), True)
        comp.features.filletFeatures.add(f_inp).name = 'jaw_silhouette_radii'

        outer = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.x - sval('arm_thk')) < tol
                    and abs(eb.maxPoint.x - sval('arm_thk')) < tol
                    and eb.minPoint.y > half_face):
                outer.add(e)
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            outer, V(PREFIX + 'jaw_facet'), False)
        chf.add(c_inp).name = 'jaw_outer_facet'
        return seen.count, outer.count

    # ---- geometry in cm (the API's internal unit) ------------------------
    pitch = val('pitch')
    n_teeth = int(round(val('rack_teeth')))
    add_h = sval('module')                      # addendum: tips below the pitch line
    ded_h = sval('module') * sval('ded_f')       # dedendum: root above the pitch line
    tan_pa = math.tan(sval('pa'))
    tip_half = pitch / 2 / 2 - add_h * tan_pa
    root_half = pitch / 2 / 2 + ded_h * tan_pa
    x_b = val('tooth_lead')
    x_a = x_b - n_teeth * pitch
    x_lo = x_a - val('end_lead')
    x_hi = x_b + val('end_lead')
    z_back = sval('rack_back')
    half_face = sval('face') / 2
    stroke = sval('stroke')

    assert tip_half > 0, 'tooth would come to a point: module or pressure angle wrong'
    assert x_a <= -stroke, (
        'rack runs off the pinion at full open: toothed run starts at %.2f mm '
        'but must reach %.2f mm' % (x_a * 10, -stroke * 10))
    assert x_b >= 0, 'rack runs off the pinion at full close'

    # ---- phase 1: rack bar ----------------------------------------------
    t0 = design.timeline.count
    sk_rack = sketch(comp.xZConstructionPlane, 'sk_rack_profile')
    pts = [(x_lo, z_back), (x_hi, z_back), (x_hi, ded_h), (x_b, ded_h)]
    for i in range(n_teeth - 1, -1, -1):
        xc = x_a + (2 * i + 1) * pitch / 2
        pts.append((xc + root_half, ded_h))
        pts.append((xc + tip_half, -add_h))
        pts.append((xc - tip_half, -add_h))
        pts.append((xc - root_half, ded_h))
    pts.append((x_a, ded_h))
    pts.append((x_lo, ded_h))
    lines = sk_rack.sketchCurves.sketchLines
    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]
        lines.addByTwoPoints(mpt(sk_rack, a[0], 0, a[1]), mpt(sk_rack, b[0], 0, b[1]))
    extrude(profiles(sk_rack, expected=1), NEW,
            '-' + SHARED + 'face / 2', SHARED + 'face', 'rack_bar')
    group(t0, 'rack bar')

    # ---- phase 2: jaw arm and blade --------------------------------------
    t1 = design.timeline.count
    # Upper tie: spans the rack's full depth, but stays ABOVE the tooth roots
    # so it can never fill a tooth space, and above the pinion's tip circle.
    box('arm_tie', 0, val('tie_thk'), -half_face, val('arm_y'),
        SHARED + 'module * ' + SHARED + 'ded_f',
        SHARED + 'rack_web', JOIN)
    # Arm + blade: forward of the rack's face width, so it clears the pinion
    # disc entirely at every opening.
    box('arm_blade', 0, sval('arm_thk'), half_face + val('arm_clear'),
        val('arm_y') + val('blade_len'),
        '-' + PREFIX + 'reach',
        PREFIX + 'reach + ' + SHARED + 'rack_back', JOIN)
    group(t1, 'jaw arm and blade')

    # ---- phase 3: finish --------------------------------------------------
    t2 = design.timeline.count
    n_rad, n_facet = style_the_jaw()
    # AFTER the facet, never before: the panel's rim lands on the very face
    # being chamfered, and a 3 mm chamfer round a 4 mm deep pocket rim fails.
    box('blade_panel',
        sval('arm_thk') - val('panel_depth'), sval('arm_thk'),
        val('arm_y') + val('panel_inset'),
        val('arm_y') + val('blade_len') - val('panel_inset'),
        '-' + PREFIX + 'reach + ' + PREFIX + 'panel_inset',
        PREFIX + 'reach + ' + SHARED + 'rack_back - ' + PREFIX + 'panel_inset * 2', CUT)
    sk_v = sketch(comp.xZConstructionPlane, 'sk_grip_vee')
    z_mid = -sval('offset')
    vl = sk_v.sketchCurves.sketchLines
    v_pts = [(0, z_mid - val('v_half')), (val('v_depth'), z_mid), (0, z_mid + val('v_half'))]
    for i in range(len(v_pts)):
        a = v_pts[i]
        b = v_pts[(i + 1) % len(v_pts)]
        vl.addByTwoPoints(mpt(sk_v, a[0], 0, a[1]), mpt(sk_v, b[0], 0, b[1]))
    extrude(profiles(sk_v, expected=1), CUT, PREFIX + 'arm_y', PREFIX + 'blade_len', 'grip_vee')
    n_bed = chamfer_at_z(z_back, 'bed_face_chamfer')
    group(t2, 'finish')

    # ---- identity + diagnostics ------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got ' + str(comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    # Appearances.itemByName RAISES on a miss, unlike Materials - so scan.
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
    print('rack: %d teeth at %.3f mm pitch, toothed run x %.2f..%.2f mm' % (
        n_teeth, pitch * 10, x_a * 10, x_b * 10))
    print('mesh window: needs x_a <= %.1f and x_b >= 0 over a %.1f mm stroke - OK' % (
        -stroke * 10, stroke * 10))
    print('tooth half-thickness mm: tip %.3f root %.3f | root space %.3f' % (
        tip_half * 10, root_half * 10, (pitch - 2 * root_half) * 10))
    print('jaw opening: 0.0 .. %.1f mm | blade tip at z %.2f mm' % (
        2 * stroke * 10, -val('reach') * 10))
    print('style: %.1f mm jaws, R%.1f on %d silhouette edges, %.1f mm facet on %d outer' % (
        sval('arm_thk') * 10, tval('radius') * 10, n_rad, val('jaw_facet') * 10, n_facet))
    print('chamfered bed edges: %d' % n_bed)
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
