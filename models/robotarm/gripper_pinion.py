"""robotarm/gripper_pinion - Fusion MCP generating script.

Rebuilds `robotarm_gripper_pinion` (idempotent). Local frame: pinion axis
is +Z, BACK face (the servo side) on z=0, teeth centred on the origin.
Spec: specs/robotarm/gripper_pinion.md.

12T module-1.5 involute pinion that drives both gripper racks, bored
straight onto the gripper SG90's own output spline.

12 TEETH IS LEGAL HERE AND WOULD NOT BE ON A GEAR PAIR. z_min at 20 deg
pressure angle is 2/sin^2(20) = 17.1, so 12 undercuts against another
involute - but a RACK has no tip circle to interfere with, so there is
nothing for the undercut flank to foul. j3_pinion cannot take the same
licence and roots at 18T for exactly that reason.

NO HORN. THE PINION BORES ONTO THE SPLINE. Jonathan, 2026-08-31: "we should
not [mount] at the horns but rather add gears that we make". Same migration
j3_pinion.py has already had, for the same three reasons: the horn is
stamped plastic that varies by batch (deshipu's teardown, Roger Cheng's
survey), GATE servo_fit MEASURED it fouling shoulder_bracket by 67.5 mm3,
and the bench reported three times that the horns will not enter anything
cut for them - "the actual horn tips dont fit in anywhere".

WHAT CAME OUT, AND HOW HARD IT HAD ALREADY BEEN FOUGHT. gp_hub_d was
re-measured twice (modelled 8.0, bench 6.8). gp_arm_w was typed as the
blade THICKNESS by mistake, corrected to the arm width at the r 6 trim,
then corrected AGAIN from a 0.15 press to a sliding clearance because a
printed slot comes out undersize and the press was an interference. gp_arm_r
required 11.20 mm to be cut off each horn arm BEFORE anything went together.
Four revisions across three files, all of them chasing a stamped part. The
whole interface is gone and not one of those numbers survives.

THE SPLINE IS NOT PRINTED, and that is a rule rather than a preference. The
SG90's spline is 20 teeth on a Oe4.9 circle: 0.77 mm of pitch and roughly
0.24 mm of tooth, against a design_rules.MIN_FEATURE_MM of 0.8 that is
CALIBRATED on this printer. The teeth are a third of the smallest feature
the machine can make, so a "splined" printed bore would come out a slightly
lumpy circle that lies about itself. The bore is therefore ROUND and cut
UNDERSIZE, and the steel spline broaches its own form into the PETG on
first assembly - one diameter to get right instead of twenty teeth.
lib/servo.SPLINE_BROACH_INTERFERENCE_MM is 0.25 and it is ASSUMED: gauge it
before a shell pair prints.

TWO DIAMETERS, because the spline sits ABOVE the boss. The SG90 presents
4.2 mm of Oe5.0 output collar and only then 2.5 mm of Oe4.9 spline, so the
lower bore CLEARS the collar and only the upper bore grips. That is why a
thin pinion cannot drive a servo at all, and it is the arithmetic this part
had to pass:

    seating face   7.10 above the tab datum (case top 6.70 + 0.40 gap)
    boss top      10.90            -> 3.80 of bore is pure clearance
    spline top    13.40            -> 2.50 of bore actually grips
    face width     8.00            -> needs 5.80, has 8.00. PASSES.

The face width does NOT change. gr_face 8.00 is the shared rack contract
and it already clears the 5.80 minimum by 2.20, so gripper_rack_jaw.py is
untouched by this. The bore runs through to the top face at gp_broach_d,
which is 1.70 mm of plain clearance above where the spline ends - that is
the screw shank's run, not wasted material.

THE PINION DROPS 3.80 mm TOWARD THE SERVO, AND THAT IS THE ONE COST. It
used to sit on the horn blade at the OUTPUT BOSS TOP, servo-z 10.90. It now
sits 0.40 off the case top, servo-z 7.10, because the bore swallows the boss
instead of perching on it. gripper_shell.py has to move the pinion plane -
and with it both rack channels, which mesh on that plane - 3.80 mm toward
the case. Nothing else in the gear contract moves: module, teeth, face,
centre distance and backlash are all as they were.

A WASHER IS REQUIRED under the servo's retaining screw, and it is not
optional. The SG90's screw is Oe2.5 with a head near Oe5 and the broach bore
is Oe4.65, so the head would land almost entirely over the hole with nothing
to clamp. gp_washer_d is the smallest washer that actually bears on the
pinion's top face, and it is asserted to land inside the root circle.

THAT IS A CHANGE TO HOW THIS PART IS RETAINED, and it needs saying. The
docstring used to read "the pinion is not clamped by the horn screw; the two
gripper shells trap it axially". It is now clamped, by the servo's own screw
and this washer, because a broached bore that is only pressed on will walk
up the spline under a gripping load. The shells still locate it radially,
but they must leave the screw head and the Oe6.25 washer clear above the top
face and leave a path to fit them - a shell that closes over the screw makes
this an assembly nobody can do twice. gripper_shell.py is not this file's to
edit; the requirement is recorded here.

Print orientation: TOOTH FACE ON THE BED, bore vertical. Same as
j3_pinion, and the bore is now through, so it prints as a clean vertical
hole stepping down in diameter with no bridged floor.
"""

import math

import adsk.core
import adsk.fusion

from lib.design_rules import JOINT_FIT_MM, MIN_WALL_MM  # noqa: E402
from lib.servo import CATALOG as _SERVOS  # noqa: E402
# IMPORT ORDER IS LOAD-BEARING AND THAT IS A LIBRARY BUG, NOT A STYLE.
# lib/servo_hub.py imports lib/gears.py at its head and lib/gears.py imports
# lib/servo_hub.py back at its foot, so whichever of the pair is reached
# FIRST decides whether the cycle resolves. Reaching for servo_hub first
# raises "ImportError: cannot import name 'spline_hub' from partially
# initialized module lib.servo_hub" and the script never runs at all.
# Touching lib.gears first breaks the tie. models/robotarm/horn_adapter.py
# has the imports in the other order and is dead on arrival because of it -
# reported, not fixed here, because lib/ is not this file's to edit.
import lib.gears  # noqa: E402,F401  - MUST precede lib.servo_hub, see above
from lib.servo_hub import spline_hub  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_gripper_pinion'
BODY_NAME = 'gripper_pinion'
PREFIX = 'gp_'
SHARED = 'gr_'      # gear contract shared with gripper_rack_jaw.py
MATERIAL_NAME = 'PET Plastic'
_SG90 = _SERVOS['SG90']
# The gripper servo, CONFIRMED against models/robotarm/_check_leads.py
# MOUNTS ('gripper', host gripper_shell, servo SG90) rather than assumed.

# Counts and epsilons, not dimensions.
TOOTH_SAMPLES = 10      # involute points per flank
TOL = 1e-9
# Least spline engagement this pinion will accept, in mm. Passed INTO
# spline_hub so the library's own refusal and the assertion below are
# arguing from the same number instead of two copies of it.
ENGAGE_MIN_MM = 2.0
# _style.md rule 5: two-tone by PART. The pinion is a joint, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
APPEARANCE_HINTS = hints_for('gripper_pinion')
PH_TEETH = 'gear teeth'
PH_SPLINE = 'spline hub'
PH_FINISH = 'finish'
PHASES = [PH_TEETH, PH_SPLINE, PH_FINISH]


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
    # NOTHING IN THIS BLOCK MOVED WHEN THE HORN CAME OUT - the spline sits on
    # the same axis the horn did, so the mesh is untouched. Only the pinion's
    # z along that axis changed, and that is gripper_shell's problem.
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
    # gr_face IS ALSO THE HUB HEIGHT the spline solve is checked against: the
    # SG90 needs 5.80 mm to reach past its output boss and this is 8.00, so
    # the shared contract did not have to move at all. Do NOT thin it below
    # 5.80 or the pinion stops being able to drive a servo - spline_hub()
    # will refuse it, which is the point of asking the library rather than
    # typing a bore. The comment string is left EXACTLY as gripper_rack_jaw.py
    # writes it, because the two scripts overwrite each other's parameter
    # comments and the contract says identical or neither.
    shared('face', '8.0 mm', 'face width, >= 5 x module - design_rules')
    shared('backlash', '0.2 mm', 'backlash added at the centre distance - design_rules GEAR_BACKLASH_MM')
    shared('r_pitch', SHARED + 'module * ' + SHARED + 'teeth / 2', 'derived pitch radius')
    shared('r_tip', SHARED + 'r_pitch + ' + SHARED + 'module', 'derived tip radius')
    shared('r_root', SHARED + 'r_pitch - ' + SHARED + 'module * ' + SHARED + 'ded_f', 'derived root radius')
    shared('r_base', SHARED + 'r_pitch * cos(' + SHARED + 'pa)', 'derived base radius')
    shared('offset', SHARED + 'r_pitch + ' + SHARED + 'backlash', 'pinion axis to rack PITCH LINE - the centre distance')
    shared('stroke', '20.0 mm', 'travel of ONE rack; jaw opening is twice this')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')
    param('case_gap', '%.4f mm' % JOINT_FIT_MM['free'],
          'running gap between the back face and the SG90 case top. The pinion\n'
          '           ROTATES relative to that case, so it cannot sit on it; this is\n'
          '           design_rules JOINT_FIT_MM free, which is what lib/servo_hub\n'
          '           seats every spline hub at.')

    # --- SPLINE HUB, solved in lib/servo_hub.py. WRITTEN, NOT CHOSEN. ------
    # THE HORN IS GONE. Every gp_hub_*/gp_arm_*/gp_screw_d parameter went
    # with it - see the docstring for what each of them cost to get wrong.
    H = spline_hub(_SG90, face=sval('face') * 10,
                   case_gap=val('case_gap') * 10, engage_min=ENGAGE_MIN_MM)
    param('seat_z', '%.4f mm' % H.seat_z,
          'servo-z of the BACK FACE - how far up the SG90 this pinion sits,\n'
          '           measured from the underside of its mounting tabs. It was 10.90\n'
          '           (perched on the output boss, on the horn blade) and is now 7.10\n'
          '           (swallowing the boss), so gripper_shell.py must bring the pinion\n'
          '           plane and BOTH rack channels 3.80 mm toward the case.')
    param('boss_bore_d', '%.4f mm' % H.boss_clear_d,
          'lower bore - CLEARS the Oe5.0 output collar at a free fit. Nothing\n'
          '           grips the boss; it only has to pass. It is the widest hole in\n'
          '           the part and it is what sets the wall to the tooth roots.')
    param('boss_bore_h', '%.4f mm' % H.boss_clear_to,
          'how far up the bore stays wide - to the top of the boss')
    param('broach_d', '%.4f mm' % H.broach_d,
          'upper bore - THE STEEL SPLINE CUTS THIS. Deliberately UNDERSIZE by\n'
          '           lib/servo.SPLINE_BROACH_INTERFERENCE_MM. The spline is not\n'
          '           printed: 20 teeth on Oe4.9 is 0.77 mm of pitch and ~0.24 mm of\n'
          '           tooth, against a CALIBRATED MIN_FEATURE_MM of 0.8. The\n'
          '           interference is ASSUMED - gauge it before a shell pair prints.')
    param('broach_from', '%.4f mm' % H.broach_from, 'derived: the spline starts here')
    param('broach_to', '%.4f mm' % H.broach_to,
          'derived: and ends here, 1.70 below the top face - the rest of the\n'
          '           bore is the retaining screw\'s shank run, not waste')
    param('engaged', '%.4f mm' % H.engaged,
          'how much spline the bore grips - the FULL 2.5 mm of SG90 spline')
    param('washer_d', '%.4f mm' % H.washer_d,
          'SMALLEST WASHER THAT WORKS, and it is not optional. The retaining\n'
          '           screw is Oe%.1f with a head near Oe5 and the broach bore is\n'
          '           Oe%.2f, so the head would sit over the hole with nothing to\n'
          '           clamp. Without a washer the pinion walks up the spline under a\n'
          '           gripping load. It lands on the TOP FACE - asserted below - so\n'
          '           gripper_shell must leave it and the screw head clear.'
          % (H.screw_d, H.broach_d))
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

    def disc(name, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

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
    r_sink = r_root - val('tooth_sink')
    ang_base = flank_ang(r_base)
    ang_tip = flank_ang(r_tip)
    for sign in (1, -1):
        flank = adsk.core.ObjectCollection.create()
        for i in range(TOOTH_SAMPLES):
            r = r_base + (r_tip - r_base) * i / (TOOTH_SAMPLES - 1)
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
    group(t0, PH_TEETH)

    # ---- phase 2: spline hub --------------------------------------------
    t1 = design.timeline.count
    # ONE through bore in TWO diameters. It was three cuts - a blind horn hub
    # relief, a blind arm slot and a separate screw bore that already went
    # all the way through - so the blind pockets were never doing anything
    # the through bore would not, once the horn stopped being in the way.
    # The step is at the OUTPUT BOSS TOP, because the spline sits above the
    # boss: the lower part of the bore lets the Oe5.0 collar through and only
    # the upper part meets the Oe4.9 spline. That is also why a thin pinion
    # cannot drive a servo directly however good the bore is - it has to
    # reach past the boss before it grips anything, which is what
    # spline_hub() refuses on.
    disc('boss_bore', val('boss_bore_d'), '0.0 mm', PREFIX + 'boss_bore_h', CUT)
    disc('spline_bore', val('broach_d'), PREFIX + 'boss_bore_h',
         SHARED + 'face - ' + PREFIX + 'boss_bore_h', CUT)
    group(t1, PH_SPLINE)

    # ---- phase 3: finish -------------------------------------------------
    t2 = design.timeline.count
    n_bed = chamfer(comp.bRepBodies.item(0), 0, 'ef', 'bed_face_chamfer')
    n_top = chamfer(comp.bRepBodies.item(0), sval('face'), 'lead_in', 'spline_lead_in')
    group(t2, PH_FINISH)

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

    # ---- the checks -------------------------------------------------------
    # The old ones here were all about the mesh, and they stay. What is added
    # is the SPLINE STACK, because that is what is new and what can be got
    # wrong by thinning a face width in the shared block.
    hub_wall = r_root * 10 - val('boss_bore_d') * 10 / 2
    assert hub_wall >= MIN_WALL_MM - TOL, (
        'only %.2f mm between the Oe%.2f boss bore and the %.2f root circle, '
        'and design_rules wants %.2f - the teeth would break into the bore'
        % (hub_wall, val('boss_bore_d') * 10, r_root * 10, MIN_WALL_MM))
    assert val('broach_to') <= sval('face') + TOL, (
        'the spline tops out %.2f into a %.2f face'
        % (val('broach_to') * 10, sval('face') * 10))
    assert val('engaged') * 10 >= ENGAGE_MIN_MM - TOL, (
        'only %.2f mm of spline engagement, want %.2f'
        % (val('engaged') * 10, ENGAGE_MIN_MM))
    assert val('broach_d') < val('washer_d') < r_root * 2, (
        'the Oe%.2f washer has to be BIGGER than the Oe%.2f broach bore to '
        'have anything to bear on and SMALLER than the %.2f root circle to '
        'land on the top face at all'
        % (val('washer_d') * 10, val('broach_d') * 10, r_root * 2 * 10))

    bb = body.boundingBox
    _case_top = _SG90.tab_thk + _SG90.tab_below_top
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
    print('seats %.2f up the SG90 (%.2f clear of its case top) - it sat at '
          '10.90 on the horn, so gripper_shell must bring the pinion plane '
          'and BOTH rack channels down to match'
          % (val('seat_z') * 10, val('seat_z') * 10 - _case_top))
    print('spline hub: boss bore Oe%.2f to %.2f, then Oe%.2f BROACHED %.2f..%.2f'
          % (val('boss_bore_d') * 10, val('boss_bore_h') * 10,
             val('broach_d') * 10, val('broach_from') * 10, val('broach_to') * 10))
    print('  %.1f mm of spline engaged | NO HORN | needs a Oe%.1f washer on the '
          'top face under the screw - the shells must leave it clear'
          % (val('engaged') * 10, val('washer_d') * 10))
    print('  face %.2f against a %.2f minimum to reach the spline at all'
          % (sval('face') * 10, H.min_height))
    print('wall between the boss bore and the tooth roots: %.2f mm' % hub_wall)
    print('chamfered edges: bed %d, top %d' % (n_bed, n_top))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
