"""robotarm/shoulder_hub - Fusion MCP generating script.

Rebuilds `robotarm_shoulder_hub` (idempotent). Spec: specs/robotarm/_state.md.

`wrist_hub` with an MG995 under it instead of an MG90S. The hex and the
journal collar are the shared wr_ contract, unchanged, so the shoulder fork
is the same fork the forearm already is and the idler side takes an ordinary
wrist_hub off the same print. The RETENTION is not shared - see below.

ONE of these is printed. The J2 idler is a plain wrist_hub.

NO HORN. THE HUB BORES ONTO THE SPLINE. Jonathan, 2026-08-31: "we should
not [mount] at the horns but rather add gears that we make". Same migration
j3_pinion.py has already had, for the same three reasons: the horn is
stamped plastic that varies by batch (deshipu's teardown, Roger Cheng's
survey), GATE servo_fit MEASURED it fouling shoulder_bracket by 67.5 mm3,
and the bench reported three times that the horns will not enter anything
cut for them. On J2 that mattered more than anywhere else, because this is
the joint that carries the entire arm.

WHAT CAME OUT. The whole three-step horn pocket is gone: the 15.60 mouth
sized by the TRIMMED arm sweep, the 90-degree cross slot, the 9.10 hub
bore, and the audit history behind all three (2026-08-27 horn audit,
2026-08-28 bench measurement of hub 8.7 / blade 2.2, the sb_horn_standoff
that was invented to dodge a 13.8 hub that turned out not to exist, and the
75.59 mm3 of MG995_output^shoulder_hub that _check_shoulder caught when the
standoff retired). None of it is load path any more. Every one of those
numbers was a horn number, and not one of them was ours to hold.

THE SPLINE IS NOT PRINTED, and that is a rule rather than a preference. The
MG995's spline is 25 teeth on a Oe5.9 circle: 0.74 mm of pitch and roughly
0.22 mm of tooth, against a design_rules.MIN_FEATURE_MM of 0.8 that is
CALIBRATED on this printer. A "splined" printed bore would come out a
slightly lumpy circle that lies about itself. So the bore is ROUND and cut
UNDERSIZE, and the steel spline broaches its own form into the PETG on
first assembly - one diameter to get right instead of twenty-five teeth.
lib/servo.SPLINE_BROACH_INTERFERENCE_MM is 0.25 and it is ASSUMED: gauge it
before this joint carries the arm.

TWO DIAMETERS, because the spline sits ABOVE the boss. The MG995 presents
3.0 mm of Oe13.0 output collar and only then 3.6 mm of Oe5.9 spline, so the
lower bore CLEARS the collar and only the upper bore grips. That is why a
thin hub cannot drive a servo at all, and it is the arithmetic this part
had to pass:

    seating face  10.20 above the case bottom datum (case top + 0.50)
    boss top      12.70            -> 2.50 of bore is pure clearance
    spline top    16.30            -> 3.60 of bore actually grips
    collar        7.00 deep        -> needs 4.50, has 7.00. PASSES.

The collar is 7.00 because it was already journal + flange_t; nothing had
to grow. The spline tops out 6.10 into it, 0.90 clear of the fork plate
datum, so the washer face stays inside the collar.

THE 0.50 CASE GAP IS KEPT, NOT RE-DERIVED. lib/servo_hub.spline_hub seats a
hub 0.40 off the case top by default. This part already sat at 0.50 and
shoulder_bracket's servo pad is built to that datum, so 0.50 is passed in
explicitly and the seating face does not move by a tenth. Note the check it
falls out of: boss_top - seat_z = 12.70 - 10.20 = 2.50, which is exactly the
sh_boss_depth this file has been carrying since 2026-08-28. The old pocket
and the new bore agree about where the boss top is, which is the one number
the horn version had right.

A WASHER IS REQUIRED under the servo's retaining screw, and it is not
optional. The MG995's screw is Oe3.0 with a head near Oe6 and the broach
bore is Oe5.65, so the head would land almost entirely over the hole with
nothing to clamp. Without a washer the hub walks up the spline and J2 loses
its index. sh_access_d is sized so the washer PASSES down to its seat and
then bears on the annulus at the top of the broach bore; the same bore is
the tool access the 6.50 screw bore used to be.

WHAT IT COSTS: nothing in arm width. The seating face has not moved, the
collar has not grown, and the fork is untouched. What it costs is that
_check_shoulder.py still builds an MG995 horn envelope and _gauge_horn.py
still cross-checks sh_horn_* parameters that no longer exist - both will
need rework, and neither is this file's to edit.

THIS HUB HAS NO RETAINING FLANGE, AND THAT IS STILL THE POINT OF THE PART.
Every other hub in the arm is trapped by a 24.0 flange too big to pass its
own 20.35 journal bore. On the J2 DRIVE side that flange makes the hub
impossible to install, and the first one printed had to be scrapped:

  from inside   the flange must pass the fork's 20.35 journal bore.  24.0.
  from outside  the flange must pass the servo pad's case window, which
                is 20.4 wide in Y (sb_case_w + sb_loc) and only 12.2 mm
                of depth from the counterbore floor to the pad's outer
                face. Tilting a 24.0 disc far enough to clear 20.4 costs
                at least 21.8 mm of that depth. There is no path.

So the counterbore on the drive plate is unreachable and is left empty, and
the collar simply runs the full plate thickness instead, sh_collar_l =
wr_journal + wr_flange_t. Retention is by the two stops that were always
there and are 3.4 mm apart:

  inboard   the hex bottoms in the upper arm's socket (wr_reach 3.8 =
            0.4 running gap + 3.4 socket depth)
  outboard  the MG995's own case top, 0.5 mm off this face

and now, axially on the shaft, by the retaining screw and its washer.

NOTHING ON THIS PART MAY EXCEED wr_hub_d. That is asserted on the built
body, not on the parameters, because it is the assembly that is at stake
and a flange is exactly the kind of feature that gets added back.

Print orientation: COLLAR FACE ON THE BED, built +Z. As wrist_hub. The
bores are now plain vertical holes stepping DOWN in diameter as they go up,
so there is no bridged floor anywhere and no support.
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

COMPONENT = 'robotarm_shoulder_hub'
BODY_NAME = 'shoulder_hub'
PREFIX = 'sh_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'hub form'
PH_SPLINE = 'spline hub'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_SPLINE, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
_MG995 = _SERVOS['MG995']
# The J2 servo, CONFIRMED against models/robotarm/_check_leads.py MOUNTS
# ('J2 shoulder', host shoulder_bracket, servo MG995) rather than assumed.

# Counts and epsilons, not dimensions.
HEX_SIDES = 2 * 3
TOL = 1e-9
# Least spline engagement this hub will accept, in mm. Passed INTO
# spline_hub so the library's own refusal and the assertion below are
# arguing from the same number instead of two copies of it.
ENGAGE_MIN_MM = 2.0
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
          '           in the plate face. THIS HUB HAS NONE - see the docstring.')
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
          '           hub, so the seating face lands on the same datum. 2026-08-30.\n'
          '           It is ALSO the hub height the spline solve is checked against,\n'
          '           and at 7.00 against a 4.50 minimum it passes with room.')
    param('free_fit', '%.4f mm' % JOINT_FIT_MM['free'],
          'design_rules JOINT_FIT_MM free - must never bind')
    param('case_gap', '0.5 mm',
          'running gap between this face and the MG995 case top. lib/servo_hub\n'
          '           defaults to 0.40; this part has sat at 0.50 since the standoff\n'
          '           retired and shoulder_bracket\'s servo pad is built to it, so the\n'
          '           existing datum is passed IN rather than re-derived. Dropping to\n'
          '           0.40 would move the whole J2 stack by a tenth for nothing.')

    # --- SPLINE HUB, solved in lib/servo_hub.py. WRITTEN, NOT CHOSEN. ------
    # THE HORN IS GONE. This hub bores straight onto the MG995's own output
    # spline; every sh_horn_* and sh_boss_* parameter this file used to
    # declare went with it. See the docstring for what they were and why not
    # one of them was ours to hold.
    H = spline_hub(_MG995, face=val('collar_l') * 10,
                   case_gap=val('case_gap') * 10, engage_min=ENGAGE_MIN_MM)
    param('seat_z', '%.4f mm' % H.seat_z,
          'servo-z of the SEATING FACE - how far up the MG995 this hub sits,\n'
          '           measured from the underside of its mounting tabs. This is the\n'
          '           number shoulder_bracket has to stand the servo off by, and the\n'
          '           horn migration leaves it UNCHANGED at 10.20 - which is the whole\n'
          '           reason the bracket needs no rework.')
    param('boss_bore_d', '%.4f mm' % H.boss_clear_d,
          'lower bore - CLEARS the Oe13.0 output collar at a free fit. Nothing\n'
          '           grips the boss; it only has to pass. This is the widest hole in\n'
          '           the part and it is what sets the collar wall.')
    param('boss_bore_h', '%.4f mm' % H.boss_clear_to,
          'how far up the bore stays wide - to the top of the boss. 2.50, and\n'
          '           the horn-era sh_boss_depth was 2.50 as well: the pocket and the\n'
          '           bore agree about where the MG995 boss top is.')
    param('broach_d', '%.4f mm' % H.broach_d,
          'upper bore - THE STEEL SPLINE CUTS THIS. Deliberately UNDERSIZE by\n'
          '           lib/servo.SPLINE_BROACH_INTERFERENCE_MM. The spline is not\n'
          '           printed: 25 teeth on Oe5.9 is 0.74 mm of pitch and ~0.22 mm of\n'
          '           tooth, against a CALIBRATED MIN_FEATURE_MM of 0.8. The\n'
          '           interference is ASSUMED - gauge it before J2 carries the arm.')
    param('broach_from', '%.4f mm' % H.broach_from, 'derived: the spline starts here')
    param('broach_to', '%.4f mm' % H.broach_to,
          'derived: and ends here, 6.10 into a 7.00 collar - so the washer face\n'
          '           sits 0.90 inside the fork plate datum rather than on it')
    param('engaged', '%.4f mm' % H.engaged,
          'how much spline the bore grips - the FULL 3.6 mm of MG995 spline,\n'
          '           because the collar is long enough to run past all of it')
    param('washer_d', '%.4f mm' % H.washer_d,
          'SMALLEST WASHER THAT WORKS, and it is not optional. The retaining\n'
          '           screw is Oe%.1f with a head near Oe6 and the broach bore is\n'
          '           Oe%.2f, so the head would sit over the hole with nothing to\n'
          '           clamp. Without a washer the hub walks up the spline and J2\n'
          '           loses its index.' % (H.screw_d, H.broach_d))
    param('access_d', PREFIX + 'washer_d + ' + PREFIX + 'free_fit',
          'derived: the washer has to PASS down this bore to reach its seat, so\n'
          '           it is the washer plus a free fit. It doubles as the driver\n'
          '           access the old 6.50 screw bore was, and on the idler side the\n'
          '           M3 retaining screw still passes through it.')
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
    SEAT = '-' + PREFIX + 'collar_l'      # the face that looks at the servo

    # ---- phase 1: collar + hex boss ----------------------------------------
    t0 = design.timeline.count
    # ONE collar, full plate thickness. No flange - see the docstring. The
    # length is still written as journal + flange_t so the seating face stays
    # on the plate's outer datum if either of those ever moves.
    disc('journal_collar', wval('hub_d'), SEAT, PREFIX + 'collar_l', NEW)

    sk_hex = sketch(comp.xYConstructionPlane, 'sk_hex_boss')
    lines = sk_hex.sketchCurves.sketchLines
    r_c = hex_af / 2 / math.cos(math.pi / HEX_SIDES)
    pts = []
    for i in range(HEX_SIDES):
        a = 2 * math.pi * i / HEX_SIDES
        pts.append((r_c * math.cos(a), r_c * math.sin(a)))
    for i in range(len(pts)):
        u, w = pts[i], pts[(i + 1) % len(pts)]
        lines.addByTwoPoints(mpt(sk_hex, u[0], u[1], 0), mpt(sk_hex, w[0], w[1], 0))
    extrude(profiles(sk_hex, expected=1), JOIN, '0.0 mm', WRIST + 'reach', 'hex_boss')
    group(t0, PH_FORM)

    # ---- phase 2: spline hub ------------------------------------------------
    t1 = design.timeline.count
    # THREE BORES, STEPPING DOWN THEN UP, and the order is the servo's own
    # stack read from the case upward. It used to be a three-step HORN pocket
    # - a 15.60 mouth sized by the trimmed arm sweep, a cross slot for the
    # blade, and a 9.10 hub bore - and every one of those numbers belonged to
    # a stamped part that varies by batch. Now:
    #   boss_bore    clears the Oe13.0 output collar. Pure clearance.
    #   spline_bore  UNDERSIZE. The steel spline broaches this on assembly.
    #   access_bore  passes the washer down to its seat, then the driver.
    # TWO DIAMETERS ON THE DRIVING PART, because the spline sits ABOVE the
    # boss: a hub shorter than boss_bore_h never reaches the spline at all,
    # however good its bore is. That is what spline_hub() refuses on, and it
    # is why this part had to be checked rather than assumed.
    disc('boss_bore', val('boss_bore_d'), SEAT, PREFIX + 'boss_bore_h', CUT)
    disc('spline_bore', val('broach_d'), SEAT + ' + ' + PREFIX + 'broach_from',
         PREFIX + 'engaged', CUT)
    disc('washer_access_bore', val('access_d'), SEAT + ' + ' + PREFIX + 'broach_to',
         PREFIX + 'collar_l - ' + PREFIX + 'broach_to + ' + WRIST + 'reach', CUT)
    group(t1, PH_SPLINE)

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

    # THE CHECKS. The old set here was about a horn: hub bore depth against
    # the collar, collar wall against a 15.60 mouth, blade slot against the
    # hex flats. Every one of them tested a stamped part's outline. What is
    # left to get wrong is the SPLINE STACK, so that is what is checked.
    boss_wall = (wval('hub_d') - val('boss_bore_d')) / 2
    assert boss_wall * 10 >= MIN_WALL_MM - TOL, (
        'only %.2f mm of collar wall around the Oe%.2f boss bore, and '
        'design_rules wants %.2f - this is the widest hole in the part and '
        'the one the J2 torque runs around'
        % (boss_wall * 10, val('boss_bore_d') * 10, MIN_WALL_MM))
    assert val('broach_to') <= val('collar_l') + TOL, (
        'the spline tops out %.2f into a %.2f collar - the washer would have '
        'no face to bear on inside the hub'
        % (val('broach_to') * 10, val('collar_l') * 10))
    assert val('engaged') * 10 >= ENGAGE_MIN_MM - TOL, (
        'only %.2f mm of spline engagement and this joint carries the whole '
        'arm - it needs at least %.2f'
        % (val('engaged') * 10, ENGAGE_MIN_MM))
    assert val('broach_d') < val('washer_d') < val('access_d'), (
        'the Oe%.2f washer has to be BIGGER than the Oe%.2f broach bore to '
        'have anything to bear on and SMALLER than the Oe%.2f access bore to '
        'reach its seat' % (val('washer_d') * 10, val('broach_d') * 10,
                            val('access_d') * 10))
    hex_wall = (hex_af - val('access_d')) / 2
    assert hex_wall * 10 >= MIN_WALL_MM - TOL, (
        'only %.2f mm between the Oe%.2f access bore and the hex flats'
        % (hex_wall * 10, val('access_d') * 10))
    # THE ASSEMBLY ASSERT. This hub is installed through a servo pad that is
    # already bolted over its counterbore: nothing on it may exceed the journal
    # collar, or it cannot be fitted at all. Measured on the BODY, because a
    # flange is exactly the feature that gets added back by someone reading
    # wrist_hub.py. See the docstring.
    _bb = body.boundingBox
    max_r = max(abs(_bb.minPoint.x), abs(_bb.maxPoint.x),
                abs(_bb.minPoint.y), abs(_bb.maxPoint.y))
    assert max_r <= wval('hub_d') / 2 + val('tol'), (
        'this hub is %.2f across at its widest and the drive plate journal bore '
        'is %.2f - it cannot be installed from either side. The drive hub is '
        'FLANGELESS; retention is the arm socket inboard and the MG995 case '
        'outboard.' % (max_r * 2 * 10, wval('hub_d') * 10))

    hex_corners = hex_af / math.cos(math.pi / HEX_SIDES)
    assert hex_corners < wval('hub_d'), (
        'hex is %.2f across corners but the collar is only %.2f - the hub cannot be '
        'threaded through its own bore' % (hex_corners * 10, wval('hub_d') * 10))
    bb = body.boundingBox
    _case_top = _MG995.tab_thk + _MG995.tab_below_top
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('hex %.2f af (socket %.1f - %.1f loc) reaching %.1f mm' % (
        hex_af * 10, wval('pivot_af') * 10, val('loc') * 10, reach * 10))
    print('hex across corners %.2f, threaded through a %.1f collar bore' % (
        hex_corners * 10, wval('hub_d') * 10))
    print('collar OD %.1f x %.1f (FLANGELESS - widest point %.2f), journal band %.1f' % (
        wval('hub_d') * 10, val('collar_l') * 10, max_r * 2 * 10, journal * 10))
    print('seats %.2f up the MG995 (%.2f clear of its case top) - shoulder_bracket '
          'must stand the servo off to match'
          % (val('seat_z') * 10, val('seat_z') * 10 - _case_top))
    print('spline hub: boss bore Oe%.2f to %.2f, then Oe%.2f BROACHED %.2f..%.2f'
          % (val('boss_bore_d') * 10, val('boss_bore_h') * 10,
             val('broach_d') * 10, val('broach_from') * 10, val('broach_to') * 10))
    print('  %.1f mm of spline engaged | NO HORN | needs a Oe%.1f washer under '
          'the screw, passed down a Oe%.2f access bore'
          % (val('engaged') * 10, val('washer_d') * 10, val('access_d') * 10))
    print('walls: collar/boss bore %.2f | hex flats/access bore %.2f mm'
          % (boss_wall * 10, hex_wall * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
