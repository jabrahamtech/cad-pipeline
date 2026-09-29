"""robotarm/wrist_rotator - Fusion MCP generating script.

Rebuilds `robotarm_wrist_rotator` (idempotent). Spec:
specs/robotarm/wrist_rotator.md, styled per specs/robotarm/_style.md.

J5. A disc on the roll SG90's OWN OUTPUT SPLINE, carrying the four M3
inserts every effector bolts to. It is the swap point of the whole arm:
pull four screws and the hand comes off.

Local frame: the roll axis is +Z. z = 0 is the BACK face of the disc; the
back hub runs -Z toward the servo and the effector bolts to the front. The
face at -wrt_hub_h is the one that looks at the servo.

The bolt pattern is small (+/-11, +/-9) on purpose. This disc SPINS, so
every millimetre of pattern is two millimetres of swept diameter, and the
load on it is trivial: the hand's weight at its centre of mass works out at
about 1 N per bolt. Spreading the pattern would buy strength nothing needs
and cost sweep everything notices.

NO HORN. THE DISC BORES ONTO THE SPLINE. Jonathan, 2026-08-31: "we should
not [mount] at the horns but rather add gears that we make". Same migration
j3_pinion.py has already had, for the same three reasons: the horn is
stamped plastic that varies by batch (deshipu's teardown, Roger Cheng's
survey), GATE servo_fit MEASURED it fouling shoulder_bracket by 67.5 mm3,
and the bench reported three times that the horns will not enter anything
cut for them ("the actual horn tips dont fit in anywhere"). The whole horn
interface - the Oe6.95 hub pocket, the r 6.0 arm slot, the 2.1 blade depth,
and the 2026-08-28 bench numbers behind all three - is gone. Not one of
those was a dimension this project could hold.

THE SPLINE IS NOT PRINTED, and that is a rule rather than a preference. The
SG90's spline is 20 teeth on a Oe4.9 circle: 0.77 mm of pitch and roughly
0.24 mm of tooth, against a design_rules.MIN_FEATURE_MM of 0.8 that is
CALIBRATED on this printer. The teeth are a third of the smallest feature
the machine can make, so a "splined" printed bore would come out a slightly
lumpy circle that lies about itself. The bore is therefore ROUND and cut
UNDERSIZE, and the steel spline broaches its own form into the PETG on
first assembly - one diameter to get right instead of twenty teeth.
lib/servo.SPLINE_BROACH_INTERFERENCE_MM is 0.25 and it is ASSUMED: gauge it
before an effector hangs off it.

TWO DIAMETERS, because the spline sits ABOVE the boss. The SG90 presents
4.2 mm of Oe5.0 output collar and only then 2.5 mm of Oe4.9 spline, so the
lower bore CLEARS the collar and only the upper bore grips. That is why a
thin disc cannot drive a servo at all, and it is the arithmetic this part
had to pass:

    seating face   7.10 above the tab datum (case top 6.70 + 0.40 gap)
    boss top      10.90            -> 3.80 of bore is pure clearance
    spline top    13.40            -> 2.50 of bore actually grips
    stack        10.00 deep        -> needs 5.80, has 10.00. PASSES.

THE BACK HUB IS WHAT MAKES THIS PART DRIVEABLE, and it was put there for an
entirely different reason. wrt_hub_h 4.00 exists so the disc does not have
to be 10 mm of solid PETG everywhere just to swallow a horn; it happens to
be exactly what lifts the bore-able stack from the disc's 6.00 to 10.00.
Run the numbers on the DISC ALONE and it is uncomfortably close: 6.00 of
face seats at 7.10, reaches the boss top at 10.90, and grips only
6.00 - 3.80 = 2.20 mm of spline - 0.20 over the 2.00 minimum, and with none
of the 2.5 mm spline to spare. With the hub it takes the whole spline.
Anyone tempted to delete the hub as "just a boss" is deleting the drive.

THE DISC NOW RUNS 0.40 OFF THE CASE TOP INSTEAD OF ON IT. The horn-era
relief (wrt_relief_d = boss_h + 3.1) put the hub's back face flat on the
SG90 case top with no gap at all - and this disc ROTATES relative to that
case, so it was rubbing by construction. lib/servo_hub's default 0.40
running gap fixes that and costs 0.40 mm of roll-joint length. wrist_roll.py
has to stand the J5 servo off by 0.40 more than it does today; that is the
one dimension outside this file the migration moves.

A WASHER IS REQUIRED under the servo's retaining screw, and it is not
optional. The SG90's screw is Oe2.5 with a head near Oe5 and the broach bore
is Oe4.65, so the head would land almost entirely over the hole with nothing
to clamp. Without a washer the disc walks up the spline and the hand droops.
wrt_access_d is sized so the washer PASSES down to its seat and then bears
on the annulus at the top of the broach bore, 3.70 mm below the front face -
so the screw goes in BEFORE the effector does, which is the same assembly
order the old horn screw needed.

PRINT ORIENTATION: FRONT FACE ON THE BED (z = wrt_disc_t), BUILT -Z. THIS
IS A CHANGE, 2026-08-31, and it is the largest single support saving in the
wrist. Audit: specs/robotarm/_printability.md.

WHAT WAS THERE BEFORE, AND WHY IT WAS NOT "no support". The old line said
BACK FACE ON THE BED, built +Z, "no bridged floor anywhere. No support."
Read the two solids it draws. The back hub is Oe10.5 and it runs z -4.0..0.
The disc is Oe36.0 and it starts at z = 0. So hub-down, the ENTIRE disc
underside - pi/4 x (36.0^2 - 10.5^2), about 931 mm2 before the scallops take
their bite - is a flat 90 deg ceiling hanging 4.0 mm above the bed on a
Oe10.5 post, and the bed contact holding all of it is the hub's own end
face, an annulus of about 64 mm2. That is not a bridge; nothing anchors it
at the far side. It is a mushroom, it gets a full support raft under the
whole disc, and the raft comes off against the face the effector bolts to.
Jonathan, from the bench: "the worst supports and its just impossible to
clean". Nothing in this file ever checked it, because the docstring asserted
the conclusion instead of the geometry.

TURNED OVER, THE SAME TWO SOLIDS ARE SELF-SUPPORTING BY CONSTRUCTION. Front
face down, the Oe36 disc IS the first layer - about 950 mm2 of bed contact
instead of 64 - and the Oe10.5 hub sits on top of it. The cross-section only
ever SHRINKS going up, which is the whole test, and it is asserted below
rather than asserted in prose. The scallops are cut through the full stack,
so they stay vertical walls either way up.

WHAT THE FLIP COSTS, because it is not free. The four M3 insert holes are
cut from the front face, so they now open AT THE BED and are blind at the
top: each is a Oe4.0 circular roof with wrt_disc_t - wrt_insert_depth = 0.50
mm of disc skin over it. That skin used to print as a floor and now prints
as a short bridge - 4.0 mm across, two layers thick. Four small bridges a
slicer will not even flag, in exchange for 931 mm2 of raft. The inserts
themselves are unaffected: they still go in down a vertical hole, which is
the orientation heat-set inserts want, and the bed-face chamfer now doubles
as their lead-in.

The bores, read from the bed upward, are access -> broach -> boss clearance,
so they WIDEN going up after one small inward step at the top of the broach
bore. That step is an annulus (wrt_access_d - wrt_broach_d) / 2 wide - 1.00
mm - and it is printed, not supported. It is the only 90 deg face left.
"""

import math

import adsk.core
import adsk.fusion

from lib.design_rules import JOINT_FIT_MM, MIN_WALL_MM  # noqa: E402
from lib.joints import J5_ROTATOR_HUB_H_MM  # noqa: E402
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

COMPONENT = 'robotarm_wrist_rotator'
BODY_NAME = 'wrist_rotator'
PREFIX = 'wrt_'
STYLE = 'sty_'
PH_FORM = 'disc'
PH_SCALLOP = 'scallops'
PH_SPLINE = 'spline hub'
PH_MOUNT = 'effector inserts'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_SCALLOP, PH_SPLINE, PH_MOUNT, PH_FINISH]

# _style.md rule 4b: lobed flanges, not plain discs. This part was a plain
# Ø36 circle until 2026-08-27 - the second most flange-shaped object in the
# arm, fully exposed at the effector end, and the ONLY part other than
# turntable_ring that the rule obviously applies to.
#
# FOUR, AND 4b's OWN REQUIREMENT CANNOT BE MET LITERALLY HERE. The rule says
# the lobe count must divide into the fixing pattern so every fixing lands on
# a lobe. On the ring that works: three posts at az 120/180/240, spacing
# divides 60. Here the four inserts sit on a RECTANGLE - ±11.0 by ±9.0, so
# az 39.29 / 140.71 / 219.29 / 320.71 - and the gaps alternate 101.42 and
# 78.58 deg. No uniform lobe count lands on all four; the pattern has 2-fold
# symmetry, not 4-fold.
#
# So the notches go in the GAPS instead, at 0/90/180/270, which puts every
# insert on a lobe by construction rather than by divisibility. EIGHT WAS
# TRIED AND FAILS: a notch at az 45 sits 5.71 deg from the insert at 39.29
# and breaks into its boss. The assertion below is what caught that, and it
# is kept so the next person raising the count gets the same answer.
SCALLOP_N = 4
SCALLOP_AZ0 = 0.0
MATERIAL_NAME = 'PET Plastic'
_SG90 = _SERVOS['SG90']
# The J5 servo, CONFIRMED against models/robotarm/_check_leads.py MOUNTS
# ('J5 roll', host wrist_roll, servo SG90) rather than assumed.

# Angles, counts and epsilons, not dimensions.
FULL_TURN_DEG = 360.0
TOL = 1e-9
# Least the scallops may bite out of the rim before they read as a defect
# rather than a lobe, in mm. A styling floor, not a fit.
SCALLOP_MIN_BITE_MM = 1.0
# Least spline engagement this disc will accept, in mm. Passed INTO
# spline_hub so the library's own refusal and the assertion below are
# arguing from the same number instead of two copies of it.
ENGAGE_MIN_MM = 2.0
# _style.md rule 5: two-tone by PART. A rotator is a joint, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
import lib.facets as F  # noqa: E402 - _style.md rule 6
APPEARANCE_HINTS = hints_for('wrist_rotator')


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
          'central hub on the BACK face, carrying the deep end of the spline\n'
          '           bore. A disc thick enough to swallow the boss everywhere would\n'
          '           be 10 mm of solid PETG; this puts the depth only where it is\n'
          '           needed. Sized to run inside the roll housing\'s rotator bore,\n'
          '           and wide enough to keep design_rules MIN_WALL around the Oe5.40\n'
          '           boss bore - asserted below.')
    param('hub_h', '%.4f mm' % J5_ROTATOR_HUB_H_MM,
          'hub height behind the disc. IT IS ALSO THE DRIVE. The disc alone is\n'
          '           6.00 and grips only 2.20 mm of spline; with the hub the stack is\n'
          '           10.00 and grips the whole 2.50. Do not delete this as "just a\n'
          '           boss" - see the docstring arithmetic. lib/joints owns the\n'
          '           number, because wrist_roll derives its FRONT FACE from it.')
    param('stack_h', PREFIX + 'hub_h + ' + PREFIX + 'disc_t',
          'derived: the WHOLE bore-able height, seating face to front face.\n'
          '           This is what the spline solve is checked against, not disc_t.')
    param('free_fit', '%.4f mm' % JOINT_FIT_MM['free'],
          'design_rules JOINT_FIT_MM free - must never bind')
    param('case_gap', '%.4f mm' % JOINT_FIT_MM['free'],
          'running gap between the seating face and the SG90 case top. This\n'
          '           disc ROTATES relative to that case, so the horn-era 0.00 was\n'
          '           rubbing by construction - the relief swallowed boss + hub and\n'
          '           sat the face flat on the case. Costs 0.40 mm of roll length;\n'
          '           wrist_roll.py has to stand the J5 servo off to match.')

    # --- SPLINE HUB, solved in lib/servo_hub.py. WRITTEN, NOT CHOSEN. ------
    H = spline_hub(_SG90, face=val('stack_h') * 10,
                   case_gap=val('case_gap') * 10, engage_min=ENGAGE_MIN_MM)
    param('seat_z', '%.4f mm' % H.seat_z,
          'servo-z of the SEATING FACE - how far up the SG90 this disc sits,\n'
          '           measured from the underside of its mounting tabs. wrist_roll.py\n'
          '           reads this to place the J5 servo, and it moves from 6.70 to 7.10\n'
          '           because the disc now runs clear of the case instead of on it.')
    param('boss_bore_d', '%.4f mm' % H.boss_clear_d,
          'lower bore - CLEARS the Oe5.0 output collar at a free fit. Nothing\n'
          '           grips the boss; it only has to pass.')
    param('boss_bore_h', '%.4f mm' % H.boss_clear_to,
          'how far up the bore stays wide - to the top of the boss. 3.80 of the\n'
          '           10.00 stack is spent just getting past the SG90 collar, which is\n'
          '           most of the back hub.')
    param('broach_d', '%.4f mm' % H.broach_d,
          'upper bore - THE STEEL SPLINE CUTS THIS. Deliberately UNDERSIZE by\n'
          '           lib/servo.SPLINE_BROACH_INTERFERENCE_MM. The spline is not\n'
          '           printed: 20 teeth on Oe4.9 is 0.77 mm of pitch and ~0.24 mm of\n'
          '           tooth, against a CALIBRATED MIN_FEATURE_MM of 0.8. The\n'
          '           interference is ASSUMED - gauge it before an effector hangs\n'
          '           off it.')
    param('broach_from', '%.4f mm' % H.broach_from, 'derived: the spline starts here')
    param('broach_to', '%.4f mm' % H.broach_to,
          'derived: and ends here, 2.30 mm up inside the disc')
    param('engaged', '%.4f mm' % H.engaged,
          'how much spline the bore grips - the FULL 2.5 mm of SG90 spline,\n'
          '           because hub + disc runs past all of it')
    param('washer_d', '%.4f mm' % H.washer_d,
          'SMALLEST WASHER THAT WORKS, and it is not optional. The retaining\n'
          '           screw is Oe%.1f with a head near Oe5 and the broach bore is\n'
          '           Oe%.2f, so the head would sit over the hole with nothing to\n'
          '           clamp. Without a washer the disc walks up the spline.'
          % (H.screw_d, H.broach_d))
    param('access_d', PREFIX + 'washer_d + ' + PREFIX + 'free_fit',
          'derived: the washer has to PASS down this bore to reach its seat, so\n'
          '           it is the washer plus a free fit. It replaces the old 5.50\n'
          '           wrt_screw_bore as the tool access, and it must still clear the\n'
          '           insert bosses radially - asserted below.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')
    param('scallop_r', '4.0 mm', 'radius of each notch cut into the rim - _style.md 4b')
    param('scallop_cr', '20.0 mm',
          'centre radius of the notch circles. At 20.0 with r 4.0 the cut\n'
          '           reaches in to r 16.0, biting 2.0 mm out of an 18.0 rim - enough\n'
          '           to read as a cog without touching an insert boss.')

    # ---- idempotent rebuild ---------------------------------------------------
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

    def disc(name, x_cm, y_cm, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_cm, y_cm, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def polydisc(name, d_cm, z0_expr, dz_expr, op):
        """The rotator disc as a 12-gon (_style.md rule 6), FLATS on the d_cm
        circle so every wall this file measures to the rim holds, and a flat
        centred on each scallop azimuth (0/90/180/270) so the notches land
        mid-flat. The hub stays round: it turns in wrist_roll's bore."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        ring = F.polygon(0.0, 0.0, d_cm / 2, az0_deg=F.FLAT_ON_AXIS_DEG, outside=True)
        for k in range(len(ring)):
            u, w = ring[k], ring[(k + 1) % len(ring)]
            sk.sketchCurves.sketchLines.addByTwoPoints(mpt(sk, u[0], u[1], 0), mpt(sk, w[0], w[1], 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    # ---- values in cm -----------------------------------------------------------
    corner = math.hypot(val('bolt_x'), val('bolt_z'))
    s_cr = val('scallop_cr')
    s_r = val('scallop_r')
    SEAT = '-' + PREFIX + 'hub_h'          # the face that looks at the servo
    assert corner + val('boss_od') / 2 <= val('disc_d') / 2, (
        'the bolt bosses reach %.2f mm, past the %.2f mm disc radius'
        % ((corner + val('boss_od') / 2) * 10, val('disc_d') / 2 * 10))
    # THE SPLINE STACK AND THE INSERTS ARE RADIALLY SEPARATE, not stacked -
    # the checks are that the bore has somewhere to end and that the two do
    # not overlap in RADIUS. The old version of this checked a horn relief
    # against disc_t + hub_h; the bore it now checks is the same length but
    # it means something, because spline_hub() has already refused anything
    # that could not reach the spline.
    assert val('broach_to') <= val('stack_h') + TOL, (
        'the spline tops out %.2f into a %.2f stack - the washer would have '
        'no face to bear on' % (val('broach_to') * 10, val('stack_h') * 10))
    assert val('engaged') * 10 >= ENGAGE_MIN_MM - TOL, (
        'only %.2f mm of spline engagement, want %.2f'
        % (val('engaged') * 10, ENGAGE_MIN_MM))
    assert val('broach_d') < val('washer_d') < val('access_d'), (
        'the Oe%.2f washer has to be BIGGER than the Oe%.2f broach bore to '
        'have anything to bear on and SMALLER than the Oe%.2f access bore to '
        'reach its seat' % (val('washer_d') * 10, val('broach_d') * 10,
                            val('access_d') * 10))
    hub_wall = (val('hub_d') - val('boss_bore_d')) / 2
    assert hub_wall * 10 >= MIN_WALL_MM - TOL, (
        'only %.2f mm of back-hub wall around the Oe%.2f boss bore, and '
        'design_rules wants %.2f'
        % (hub_wall * 10, val('boss_bore_d') * 10, MIN_WALL_MM))
    assert val('insert_depth') <= val('disc_t'), 'the inserts run out of the disc'
    assert corner - val('boss_od') / 2 > val('hub_d') / 2, (
        'the insert bosses overlap the central hub')
    # The access bore is the widest hole that reaches into the DISC, which is
    # where the insert bosses live. hub_d is wider, but it stops at z = 0.
    assert corner - val('boss_od') / 2 > val('access_d') / 2, (
        'the Oe%.2f access bore reaches r %.2f and the insert bosses start at '
        'r %.2f' % (val('access_d') * 10, val('access_d') / 2 * 10,
                    (corner - val('boss_od') / 2) * 10))
    # ---- PRINTABILITY GATE, front face on the bed, built -Z ----------------
    # THE ONE TEST THIS ORIENTATION RESTS ON: turned front-face-down, the
    # cross-section has to SHRINK going up, and here that is exactly the
    # statement that the back hub is no wider than the disc it stands on. The
    # old docstring claimed self-support and checked nothing, which is how a
    # 931 mm2 raft under the effector face survived to the bench. Say it in
    # code so the next person who widens the hub is stopped here and not by a
    # print. specs/robotarm/_printability.md carries the full audit.
    assert val('hub_d') <= val('disc_d'), (
        'the Oe%.2f back hub is wider than the Oe%.2f disc it stands on - '
        'front-face-down stops being self-supporting and this part goes back '
        'to needing a raft under the whole disc'
        % (val('hub_d') * 10, val('disc_d') * 10))
    # The four insert holes now open at the bed and are roofed by whatever
    # disc is left above them. It is thin - thinner than MIN_WALL - so it is
    # NOT asserted, it is DECLARED: a Oe4.0 bridge two layers thick. Anything
    # that shortens the disc or deepens the inserts makes it thinner.
    insert_roof = val('disc_t') - val('insert_depth')
    # The bores widen going up apart from one inward step where the washer
    # access bore meets the broach bore. That annulus is the only 90 deg face
    # on the part; it prints unsupported because it is 1.00 mm of reach.
    bore_ledge = (val('access_d') - val('broach_d')) / 2

    # ---- phase 1: the disc --------------------------------------------------------
    t0 = design.timeline.count
    polydisc('rotator_disc', val('disc_d'), '0.0 mm', PREFIX + 'disc_t', NEW)
    disc('spline_boss', 0, 0, val('hub_d'), SEAT, PREFIX + 'hub_h', JOIN)
    group(t0, PH_FORM)

    # ---- phase 1b: scallops, _style.md rule 4b -------------------------------
    # Cut BEFORE the inserts so the assertion below is the only thing standing
    # between a notch and an insert boss - if it ever stops being true the
    # build fails here rather than quietly eating a boss wall later.
    ts = design.timeline.count
    s_cr_mm = val('scallop_cr') * 10
    s_r_mm = val('scallop_r') * 10
    disc_r_mm = val('disc_d') / 2 * 10
    boss_r_mm = val('boss_od') / 2 * 10
    corner_mm = corner * 10
    reach_in_mm = s_cr_mm - s_r_mm
    assert reach_in_mm < disc_r_mm - TOL, (
        'the scallops reach r %.2f and the disc is r %.2f - they would not cut '
        'the rim at all' % (reach_in_mm, disc_r_mm))
    assert disc_r_mm - reach_in_mm >= SCALLOP_MIN_BITE_MM, (
        'the scallops bite only %.2f mm out of the rim - under a millimetre '
        'reads as a defect, not a lobe' % (disc_r_mm - reach_in_mm))
    insert_az = [math.degrees(math.atan2(sz * val('bolt_z'), sx * val('bolt_x')))
                 for sx in (-1, 1) for sz in (-1, 1)]
    for i in range(SCALLOP_N):
        az = SCALLOP_AZ0 + i * FULL_TURN_DEG / SCALLOP_N
        a = math.radians(az)
        # NO NOTCH MAY BREAK INTO AN INSERT BOSS. This is the achievable half
        # of 4b, and it is what turntable_ring actually asserts too.
        for iaz in insert_az:
            d_mm = math.sqrt(s_cr_mm ** 2 + corner_mm ** 2
                             - 2 * s_cr_mm * corner_mm
                             * math.cos(math.radians(az - iaz)))
            assert d_mm > s_r_mm + boss_r_mm + MIN_WALL_MM, (
                'scallop at az %.0f is %.2f mm from the insert boss at az %.2f '
                '- it needs %.2f. Lower SCALLOP_N or move scallop_cr out.'
                % (az, d_mm, iaz, s_r_mm + boss_r_mm + MIN_WALL_MM))
        disc('scallop_%d' % i, s_cr * math.cos(a), s_cr * math.sin(a),
             val('scallop_r') * 2, SEAT, PREFIX + 'stack_h', CUT)
    group(ts, PH_SCALLOP)

    # ---- phase 2: spline hub ----------------------------------------------------
    t1 = design.timeline.count
    # THREE BORES, and the order is the SG90's own stack read upward from the
    # case. It used to be a horn hub relief, an arm slot at the boss height
    # and a separate 5.50 screw bore. Now:
    #   boss_bore    clears the Oe5.0 output collar for 3.80. Pure clearance.
    #   spline_bore  UNDERSIZE. The steel spline broaches this on assembly.
    #   access_bore  passes the washer down to its seat, then the tool.
    # TWO DIAMETERS ON THE DRIVEN PART, because the spline sits ABOVE the
    # boss: a disc shorter than boss_bore_h never reaches the spline at all,
    # however good its bore is. That is what spline_hub() refuses on, and it
    # is why hub_h is load-bearing rather than decorative.
    disc('boss_bore', 0, 0, val('boss_bore_d'), SEAT, PREFIX + 'boss_bore_h', CUT)
    disc('spline_bore', 0, 0, val('broach_d'), SEAT + ' + ' + PREFIX + 'broach_from',
         PREFIX + 'engaged', CUT)
    disc('washer_access_bore', 0, 0, val('access_d'), SEAT + ' + ' + PREFIX + 'broach_to',
         PREFIX + 'stack_h - ' + PREFIX + 'broach_to', CUT)
    group(t1, PH_SPLINE)

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
    # THE ELEPHANT-FOOT CHAMFER FOLLOWS THE BED, and the bed moved. Both faces
    # were already being chamfered at sty_ef, so turning the part over costs
    # nothing here but the two names - which have to be right, because the
    # bed-face chamfer is the one that answers to design_rules
    # ELEPHANT_FOOT_CHAMFER_MM and it is now also the inserts' lead-in.
    for z_pick, nm in ((val('disc_t'), 'bed_face_chamfer'), (-val('hub_h'), 'hub_back_chamfer')):
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
    _case_top = _SG90.tab_thk + _SG90.tab_below_top
    _disc_only = val('disc_t') * 10 - val('boss_bore_h') * 10
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('SCALLOPS: %d lobes at az %s - _style.md 4b. The inserts sit on the'
          % (SCALLOP_N, [round(SCALLOP_AZ0 + FULL_TURN_DEG / 2 / SCALLOP_N
                               + i * FULL_TURN_DEG / SCALLOP_N) for i in range(SCALLOP_N)]))
    print('  lobes because the notches are in the GAPS: a rectangular bolt')
    print('  pattern has no lobe count that lands on all four.')
    print('  notch r %.1f at r %.1f, biting %.1f mm out of an %.1f rim'
          % (val('scallop_r') * 10, val('scallop_cr') * 10,
             val('disc_d') / 2 * 10 - (val('scallop_cr') - val('scallop_r')) * 10,
             val('disc_d') / 2 * 10))
    print('disc OD %.1f x %.1f | effector pattern 4 x M3 at +/-%.1f, +/-%.1f (corner %.2f)' % (
        val('disc_d') * 10, val('disc_t') * 10, val('bolt_x') * 10, val('bolt_z') * 10,
        corner * 10))
    print('seats %.2f up the SG90 (%.2f clear of its case top) - wrist_roll.py '
          'must stand the J5 servo off to match'
          % (val('seat_z') * 10, val('seat_z') * 10 - _case_top))
    print('spline hub: boss bore Oe%.2f to %.2f, then Oe%.2f BROACHED %.2f..%.2f'
          % (val('boss_bore_d') * 10, val('boss_bore_h') * 10,
             val('broach_d') * 10, val('broach_from') * 10, val('broach_to') * 10))
    print('  %.1f mm of spline engaged | NO HORN | needs a Oe%.1f washer under '
          'the screw, passed down a Oe%.2f access bore'
          % (val('engaged') * 10, val('washer_d') * 10, val('access_d') * 10))
    print('  bore-able stack %.2f (back hub %.2f + disc %.2f) against a %.2f '
          'minimum - the DISC ALONE would grip only %.2f mm'
          % (val('stack_h') * 10, val('hub_h') * 10, val('disc_t') * 10,
             H.min_height, _disc_only))
    print('back-hub wall around the boss bore: %.2f mm' % (hub_wall * 10))
    hub_r_mm = val('hub_d') / 2 * 10
    shadow_mm2 = math.pi * (disc_r_mm ** 2 - hub_r_mm ** 2)
    print('PRINTABILITY - FRONT FACE ON THE BED (z %.1f), BUILT -Z, SUPPORT OFF.'
          % (val('disc_t') * 10))
    print('  cross-section shrinks all the way up: Oe%.1f disc -> Oe%.1f hub, so'
          % (val('disc_d') * 10, val('hub_d') * 10))
    print('  every outer face is vertical or up-facing. Bed contact ~%.0f mm2.'
          % (math.pi * disc_r_mm ** 2))
    print('  HUB-DOWN, WHICH IS WHAT THIS FILE USED TO SAY, the disc underside')
    print('  is %.0f mm2 of flat 90 deg ceiling on a Oe%.1f post with %.0f mm2 of'
          % (shadow_mm2, val('hub_d') * 10,
             math.pi * (hub_r_mm ** 2 - (val('boss_bore_d') / 2 * 10) ** 2)))
    print('  bed contact - a full raft against the effector face. That is the')
    print('  support Jonathan could not clean. Do not turn this part back over.')
    print('  left over air, declared not gated: 4 x Oe%.1f insert roofs under '
          '%.2f mm of disc, and a %.2f mm bore ledge at the broach bore top.'
          % (val('insert_d') * 10, insert_roof * 10, bore_ledge * 10))
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
