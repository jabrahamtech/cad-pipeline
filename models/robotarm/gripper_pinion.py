"""robotarm/gripper_pinion - Fusion MCP generating script.

Rebuilds `robotarm_gripper_pinion` (idempotent). Local frame: pinion axis
is +Z, BACK face (the horn side) on z=0, teeth centred on the origin.
Spec: specs/robotarm/gripper_pinion.md.

12T module-1.5 involute pinion that drives both gripper racks. It is
pressed onto the SG90's own single-arm horn, which must be TRIMMED to
gp_arm_r before assembly - the horn is 15.95 mm long and the pinion's root
circle is only 7.125 mm, so an untrimmed arm would break out through the
teeth. The pinion is not clamped by the horn screw; the two gripper shells
trap it axially (see specs/robotarm/_assembly.md, gripper split contract).

Every horn dimension here is DATASHEET (lib/servo.py, vendor drawing
SG90_Arm_Original) and is the first suspect if the pinion will not press
on. Gauge before printing a shell pair.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_gripper_pinion'
BODY_NAME = 'gripper_pinion'
PREFIX = 'gp_'
SHARED = 'gr_'      # gear contract shared with gripper_rack_jaw.py
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. The pinion is a joint, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('gripper_pinion')
PHASES = ['gear teeth', 'horn interface', 'finish']


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def param(name, expr, comment='', units='mm'):
        p = ups.itemByName(PREFIX + name)
        if p is None:
            ups.add(PREFIX + name, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value

    # --- SHARED gear contract: defined IDENTICALLY in gripper_rack_jaw.py.
    # specs/robotarm/_assembly.md "pinion mesh" row. Edit both or neither.
    def shared(name, expr, comment='', units='mm'):
        p = ups.itemByName(SHARED + name)
        if p is None:
            ups.add(SHARED + name, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def sval(name):
        return ups.itemByName(SHARED + name).value

    shared('module', '1.5 mm', 'gear module - design_rules GEAR_PREFERRED_MODULE_MM')
    shared('teeth', '12', 'pinion tooth count - gears_drives.md floor at 20 deg PA', '')
    shared('pa', '20 deg', 'pressure angle - gears_drives.md', 'deg')
    shared('ded_f', '1.25', 'dedendum factor, standard full-depth tooth', '')
    shared('face', '8.0 mm', 'face width, >= 5 x module - design_rules')
    shared('backlash', '0.2 mm', 'backlash added at the centre distance - design_rules GEAR_BACKLASH_MM')
    shared('r_pitch', SHARED + 'module * ' + SHARED + 'teeth / 2', 'derived pitch radius')
    shared('r_tip', SHARED + 'r_pitch + ' + SHARED + 'module', 'derived tip radius')
    shared('r_root', SHARED + 'r_pitch - ' + SHARED + 'module * ' + SHARED + 'ded_f', 'derived root radius')
    shared('r_base', SHARED + 'r_pitch * cos(' + SHARED + 'pa)', 'derived base radius')
    shared('offset', SHARED + 'r_pitch + ' + SHARED + 'backlash', 'pinion axis to rack PITCH LINE - the centre distance')
    shared('stroke', '20.0 mm', 'travel of ONE rack; jaw opening is twice this')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')
    param('hub_d', '6.95 mm', 'SG90 horn hub 8.0 + press 0.15 - 2026-08-27 horn audit\n           MEASURED 2026-08-28: hub is 6.8, not the modelled 8.0 - at 8.15 this pocket was 1.35 loose and no press at all.')
    param('hub_depth', '3.1 mm', 'horn hub 3.0 + 0.1 so the shells set the axial gap - horn audit')
    param('arm_w', '5.85 mm', 'horn arm width AT the r 6 trim: 5.5 + press 0.15.\n           The arm tapers 5.5 -> 3; 3.95 was thickness-as-width - horn audit\n           MEASURED 2026-08-28: the arm is 5.7 at the r 6 trim, so 5.65 was 0.05 UNDER it - an interference, not a press fit.')
    param('arm_r', '6.0 mm', 'horn arm TRIMMED to this radius at assembly - see spec')
    param('arm_depth', '2.1 mm', 'horn blade 2.0 + 0.1 seating - horn audit')
    param('screw_d', '5.5 mm', 'driver access to the horn retaining screw - fasteners_inserts')
    param('ef', '0.4 mm', 'elephant-foot chamfer - design_rules')
    param('lead_in', '0.5 mm', 'insertion lead-in chamfer - joints_tolerances')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

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

    def mpt(sk, x_cm, y_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, 0))

    def polar(sk, r_cm, ang):
        return mpt(sk, r_cm * math.cos(ang), r_cm * math.sin(ang))

    def chamfer(body, z_pick, dist_param, name):
        """Chamfer every edge lying flat in the plane z = z_pick (cm).
        Geometric selection - survives a parameter change reordering the B-rep."""
        tol = val('tol')
        edges = adsk.core.ObjectCollection.create()
        for e in body.edges:
            eb = e.boundingBox
            if abs(eb.minPoint.z - z_pick) < tol and abs(eb.maxPoint.z - z_pick) < tol:
                edges.add(e)
        inp = chf.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(PREFIX + dist_param), False)
        chf.add(inp).name = name
        return edges.count

    r_pitch, r_tip, r_root, r_base = sval('r_pitch'), sval('r_tip'), sval('r_root'), sval('r_base')
    teeth = int(round(sval('teeth')))
    pa = sval('pa')
    assert r_root < r_base < r_tip, 'radial flank assumption broken: ' + str((r_root, r_base, r_tip))

    def inv(a):
        return math.tan(a) - a

    psi_base_half = math.pi / (2 * teeth) + inv(pa)

    def flank_ang(r):
        return psi_base_half - inv(math.acos(r_base / r))

    # ---- phase 1: blank + involute tooth + ring -------------------------
    t0 = design.timeline.count
    sk_blank = sketch(comp.xYConstructionPlane, 'sk_root_circle')
    sk_blank.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk_blank, 0, 0), r_root)
    extrude(profiles(sk_blank, expected=1), NEW, '0.0 mm', SHARED + 'face', 'blank')

    sk_tooth = sketch(comp.xYConstructionPlane, 'sk_tooth_profile')
    lines = sk_tooth.sketchCurves.sketchLines
    n_pts = 10
    r_sink = r_root - val('tooth_sink')
    ang_base = flank_ang(r_base)
    ang_tip = flank_ang(r_tip)
    for sign in (1, -1):
        flank = adsk.core.ObjectCollection.create()
        for i in range(n_pts):
            r = r_base + (r_tip - r_base) * i / (n_pts - 1)
            flank.add(polar(sk_tooth, r, sign * flank_ang(r)))
        sk_tooth.sketchCurves.sketchFittedSplines.add(flank)
        lines.addByTwoPoints(polar(sk_tooth, r_sink, sign * ang_base),
                             polar(sk_tooth, r_base, sign * ang_base))
    lines.addByTwoPoints(polar(sk_tooth, r_sink, ang_base), polar(sk_tooth, r_sink, -ang_base))
    sk_tooth.sketchCurves.sketchArcs.addByCenterStartSweep(
        mpt(sk_tooth, 0, 0), polar(sk_tooth, r_tip, ang_tip), -2 * ang_tip)
    tooth = extrude(profiles(sk_tooth, expected=1), JOIN, '0.0 mm', SHARED + 'face', 'tooth')

    pat_in = adsk.core.ObjectCollection.create()
    pat_in.add(tooth)
    cp_inp = comp.features.circularPatternFeatures.createInput(pat_in, comp.zConstructionAxis)
    cp_inp.quantity = adsk.core.ValueInput.createByReal(teeth)
    cp_inp.totalAngle = V('360 deg')
    cp_inp.isSymmetric = False
    comp.features.circularPatternFeatures.add(cp_inp).name = 'tooth_ring'
    group(t0, 'gear teeth')

    # ---- phase 2: horn interface ----------------------------------------
    t1 = design.timeline.count
    sk_hub = sketch(comp.xYConstructionPlane, 'sk_horn_hub')
    sk_hub.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk_hub, 0, 0), val('hub_d') / 2)
    extrude(profiles(sk_hub, expected=1), CUT, '0.0 mm', PREFIX + 'hub_depth', 'horn_hub_relief')

    sk_arm = sketch(comp.xYConstructionPlane, 'sk_horn_arm_slot')
    sk_arm.sketchCurves.sketchLines.addTwoPointRectangle(
        mpt(sk_arm, -val('arm_r'), -val('arm_w') / 2),
        mpt(sk_arm, val('arm_r'), val('arm_w') / 2))
    extrude(profiles(sk_arm, expected=1), CUT, '0.0 mm', PREFIX + 'arm_depth', 'horn_arm_slot')

    sk_scr = sketch(comp.xYConstructionPlane, 'sk_horn_screw_bore')
    sk_scr.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk_scr, 0, 0), val('screw_d') / 2)
    extrude(profiles(sk_scr, expected=1), CUT, '0.0 mm', SHARED + 'face', 'horn_screw_bore')
    group(t1, 'horn interface')

    # ---- phase 3: finish -------------------------------------------------
    t2 = design.timeline.count
    n_bed = chamfer(comp.bRepBodies.item(0), 0, 'ef', 'bed_face_chamfer')
    n_top = chamfer(comp.bRepBodies.item(0), sval('face'), 'lead_in', 'driver_lead_in')
    group(t2, 'finish')

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
    print('teeth %d  module %.2f mm  face %.2f mm' % (teeth, sval('module') * 10, sval('face') * 10))
    print('r base/pitch/tip/root mm: %.3f %.3f %.3f %.3f' % (
        r_base * 10, r_pitch * 10, r_tip * 10, r_root * 10))
    print('tooth thickness at pitch mm: %.3f (target pi*m/2 = %.3f)' % (
        2 * flank_ang(r_pitch) * r_pitch * 10, math.pi * sval('module') * 10 / 2))
    print('tip thickness mm: %.3f | rack travel per radian mm: %.2f' % (
        2 * ang_tip * r_tip * 10, r_pitch * 10))
    print('centre distance (axis to rack pitch line) mm: %.2f | backlash %.2f' % (
        sval('offset') * 10, sval('backlash') * 10))
    print('pinion sweep for full stroke: %.1f deg' % (
        math.degrees(sval('stroke') / r_pitch)))
    print('radial clearance to rack root mm: %.3f' % (
        (sval('offset') + sval('module') * sval('ded_f') - r_tip) * 10))
    print('chamfered edges: bed %d, top %d' % (n_bed, n_top))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
