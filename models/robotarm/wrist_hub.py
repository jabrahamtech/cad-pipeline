"""robotarm/wrist_hub - Fusion MCP generating script.

Rebuilds `robotarm_wrist_hub` (idempotent). Spec:
specs/robotarm/wrist_hub.md, styled per specs/robotarm/_style.md.

Local frame: the J4 axis is +Z. z = 0 is the face that lands on the fork
plate's inner face; the hex boss runs +Z into the effector's socket and the
journal collar runs -Z into the fork plate's bore. The face at
-(wr_journal + wr_flange_t) is the one that looks at the servo.

ONE printed design, TWO copies, and the two do DIFFERENT jobs:

  drive side  - the wrist MG90S's OWN OUTPUT SPLINE drives this hub, so the
                servo turns the hub, the hex turns the effector, and the
                servo's output bearing carries it.
  idler side  - the identical part runs free in the opposite fork plate's
                bore, retained by an M3 screw through the same access bore.
                The spline bore is simply an unused hole.

That is why the effector's socket is a HEX and not a round journal: both
journals live in the FORK, so the socket only has to transmit torque and
index. It can therefore be 3.4 mm deep, which is all the room there is
beside the gripper's servo.

NO HORN. THE HUB BORES ONTO THE SPLINE. Jonathan, 2026-08-31: "we should
not [mount] at the horns but rather add gears that we make". Same migration
j3_pinion.py has already had, for the same three reasons: the horn is
stamped plastic that varies by batch (deshipu's teardown, Roger Cheng's
survey), GATE servo_fit MEASURED it fouling shoulder_bracket by 67.5 mm3,
and the bench reported three times that the horns will not enter anything
cut for them ("the actual horn tips dont fit in anywhere").

AND THE HORN POCKET IN THIS PART WAS WRONG ANYWAY, WHICH NOBODY HAD
NOTICED. wh_horn_arm_slot was extruded from the seating face downward,
0.00..2.10 into the part - but the MG90S's output boss is 6.0 mm tall and
occupies 0.00..6.00 of that same bore. The blade slot was cut 6 mm too
deep, inside solid boss, so the horn arms had nowhere to go and no horn was
ever going to enter this hub. wrist_rotator.py and shoulder_hub.py both got
the same cut right (they start their slot at the boss height); this one did
not, and it survived because nothing static checks a blind pocket against
the servo stack. It is recorded rather than quietly deleted, because the
class of mistake - a z-offset measured from the wrong datum - is the one
this whole migration keeps turning up.

THE SPLINE IS NOT PRINTED, and that is a rule rather than a preference. The
MG90S's spline is 20 teeth on a Oe5.0 circle: 0.79 mm of pitch and roughly
0.24 mm of tooth, against a design_rules.MIN_FEATURE_MM of 0.8 that is
CALIBRATED on this printer. The teeth are a third of the smallest feature
the machine can make, so a "splined" printed bore would come out a slightly
lumpy circle that lies about itself. The bore is therefore ROUND and cut
UNDERSIZE, and the steel spline broaches its own form into the PETG on
first assembly - one diameter to get right instead of twenty teeth.
lib/servo.SPLINE_BROACH_INTERFERENCE_MM is 0.25 and it is ASSUMED: gauge it
before printing a pair.

TWO DIAMETERS, because the spline sits ABOVE the boss. The MG90S presents
6.0 mm of Oe6.0 output collar and only then 4.0 mm of Oe5.0 spline, so the
lower bore CLEARS the collar and only the upper bore grips. That is why a
thin hub cannot drive a servo at all, and it is the arithmetic this part
had to pass:

    seating face   5.90 above the tab datum (case top 5.50 + 0.40 gap)
    boss top      11.50            -> 5.60 of bore is pure clearance
    spline top    15.50            -> 4.00 of bore actually grips
    hub stack     10.80 deep       -> needs 7.60, has 10.80. PASSES.

THE 10.80 IS NOT THE COLLAR, AND THAT IS THE ONLY REASON THIS PART
QUALIFIES. wr_journal + wr_flange_t is 7.00, which is 0.60 SHORT of the
7.60 spline_hub() demands. The bore has to run on THROUGH the hex boss -
7.00 of collar plus wr_reach 3.80 of hex - to reach the spline with 4.00 mm
to spare. The old wh_screw_bore already ran the full 10.80 as screw
access, so this costs no material that was not already gone; but if
wr_reach is ever shortened, check this again before printing. At
wr_reach < 0.60 the hub stops being able to drive a servo.

The hex is left STRONGER, not weaker: it used to carry a Oe5.50 hole over
its whole length and now carries Oe4.75 for the first 2.60 mm and Oe6.75
only over the last 1.20 mm, where the socket is not loaded.

THE HUB NOW RUNS 0.40 OFF THE CASE TOP INSTEAD OF ON IT. The horn-era
relief (wh_horn_hub_depth 9.10 = boss 6.0 + hub 3.1) put this face flat on
the MG90S case top with no gap at all - and this hub ROTATES relative to
that case, so it was rubbing on it by construction. lib/servo_hub's default
0.40 running gap fixes that and costs 0.40 mm of wrist width. forearm.py
has to stand the J4 servo off by 0.40 more than it does today; that is the
one dimension outside this file the migration moves.

THE HUB GOES IN FROM OUTSIDE, so every diameter inboard of the collar has
to pass through the collar's own bore. The hex is 15.80 across flats but
18.24 ACROSS CORNERS, which is why the collar is 20.0 and not the 18.0 it
started at - at 18.0 the corners stood proud of the journal and the part
could not be assembled at all. Any change to wr_pivot_af has to be checked
against that, and the assertion below does it.

A WASHER IS REQUIRED under the servo's retaining screw on the drive side,
and it is not optional. The MG90S's screw is Oe2.5 with a head near Oe5 and
the broach bore is Oe4.75, so the head would land almost entirely over the
hole with nothing to clamp. Without a washer the hub walks up the spline.
wh_access_d is sized so the washer PASSES down to its seat and then bears
on the annulus at the top of the broach bore, 1.20 mm inside the hex nose.
On the idler side the same bore passes the M3 retaining screw, exactly as
the old wh_screw_bore did.

FOUR OF THESE ARE PRINTED, not two: J3 (elbow) uses the identical joint,
so the upper arm straddles the forearm exactly as the forearm straddles
the roll housing. One design, four copies, two joints. Note that only the
two DRIVEN copies see a spline; the other two are plain journals.

PRINT ORIENTATION: THE FLANGE'S OUTBOARD FACE ON THE BED, built +Z. It is
the Oe24.0 face at -(wr_journal + wr_flange_t), the one that looks at the
servo, and the bed_face_chamfer in phase 3 is already cut there - the code
was right and only the word was wrong. It used to say "COLLAR FACE", which
names the Oe20.0 face 2.0 mm further up and is the one face of the three
that is not touching anything. Re-audited 2026-08-31 against
specs/robotarm/_printability.md; the orientation itself is UNCHANGED,
because it is correct.

Every cross-section shrinks going up - Oe24.0 flange, Oe20.0 collar, then
15.80 af hex - so every step is an UP-facing annulus and the outside of this
part has no overhang anywhere. Turned the other way up, on the hex, both of
those steps invert into 90 deg annular ceilings (2.0 mm and 0.88 mm of
reach) and the bed contact drops from 452 mm2 to the hex's 216. The shrink
is now asserted rather than described. The hex flats are also loaded within
layers this way up, which is the direction the wrist's torque runs.

THE BORES, AND THE ONE 90 DEG FACE ON THIS PART. The old line said "the
bores step DOWN in diameter as they go up, so there is no bridged floor",
which has the sign backwards: a bore that NARROWS going up grows material
inward over air, and a bore that WIDENS going up cannot overhang at all.
Read upward from the bed this stack does both - Oe6.40 boss clearance, then
Oe4.75 broach, then Oe6.75 washer access - so the step at the top of the
boss bore is an inward annulus (6.40 - 4.75) / 2 = 0.83 mm wide, and it is
the only face on the part that prints over air. 0.83 mm of unsupported reach
off a fully anchored circular edge needs no support and gets none. The step
above it widens, which is free. No support anywhere on this part.

The SHARED wr_* block is defined identically in wrist_roll.py and
forearm.py; sty_* comes from _style.md. The MG90S stack is DATASHEET
(lib/servo.py) and the broach interference is ASSUMED - gauge before
printing a pair.
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

COMPONENT = 'robotarm_wrist_hub'
BODY_NAME = 'wrist_hub'
PREFIX = 'wh_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'hub form'
PH_SPLINE = 'spline hub'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_SPLINE, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
_MG90S = _SERVOS['MG90S']
# The J4 servo, CONFIRMED against models/robotarm/_check_leads.py MOUNTS
# ('J4 wrist', host forearm, servo MG90S) rather than assumed. The same
# print also serves 'J3 elbow', which is an MG90S too.

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
APPEARANCE_HINTS = hints_for('wrist_hub')


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
          '           stops cannot fight each other.\n'
          '           IT IS ALSO LOAD-BEARING FOR THE SPLINE. The collar alone is 7.00\n'
          '           and the MG90S needs 7.60 to reach its spline, so 0.60 of this\n'
          '           reach is what makes the hub driveable at all. Asserted below.')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- hub ---------------------------------------------------------------
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('hex_af', WRIST + 'pivot_af - ' + PREFIX + 'loc',
          'derived: locational fit inside the effector socket - grow the HOLE, '
          'shrink nothing, so the socket stays nominal and this comes down')
    param('lead_in', '0.6 mm', 'chamfer on the hex nose - joints_tolerances, every mating edge')
    param('stack_h', WRIST + 'journal + ' + WRIST + 'flange_t + ' + WRIST + 'reach',
          'derived: the WHOLE bore-able height, seating face to hex nose. This\n'
          '           is what the spline solve is checked against, NOT the 7.00 of\n'
          '           collar, because the bore runs on through the hex to reach the\n'
          '           spline. 10.80 against a 7.60 minimum.')
    param('free_fit', '%.4f mm' % JOINT_FIT_MM['free'],
          'design_rules JOINT_FIT_MM free - must never bind')
    param('case_gap', '%.4f mm' % JOINT_FIT_MM['free'],
          'running gap between the seating face and the MG90S case top. This\n'
          '           hub ROTATES relative to that case, so the horn-era 0.00 was\n'
          '           rubbing by construction - the relief swallowed boss + hub and\n'
          '           sat the face flat on the case. Costs 0.40 mm of wrist width;\n'
          '           forearm.py has to stand the J4 servo off to match.')

    # --- SPLINE HUB, solved in lib/servo_hub.py. WRITTEN, NOT CHOSEN. ------
    # THE HORN IS GONE, and so is the blade slot that was cut 6 mm inside the
    # output boss and could never have taken a horn. See the docstring.
    H = spline_hub(_MG90S, face=val('stack_h') * 10,
                   case_gap=val('case_gap') * 10, engage_min=ENGAGE_MIN_MM)
    param('seat_z', '%.4f mm' % H.seat_z,
          'servo-z of the SEATING FACE - how far up the MG90S this hub sits,\n'
          '           measured from the underside of its mounting tabs. forearm.py\n'
          '           reads this to place the J4 lobe, and it moves from 5.50 to 5.90\n'
          '           because the hub now runs 0.40 clear of the case instead of on it.')
    param('boss_bore_d', '%.4f mm' % H.boss_clear_d,
          'lower bore - CLEARS the Oe6.0 output collar at a free fit. Nothing\n'
          '           grips the boss; it only has to pass.')
    param('boss_bore_h', '%.4f mm' % H.boss_clear_to,
          'how far up the bore stays wide - to the top of the boss. 5.60 of the\n'
          '           10.80 stack is spent just getting past the MG90S collar, which\n'
          '           is the single reason a 7.00 hub would not have done.')
    param('broach_d', '%.4f mm' % H.broach_d,
          'upper bore - THE STEEL SPLINE CUTS THIS. Deliberately UNDERSIZE by\n'
          '           lib/servo.SPLINE_BROACH_INTERFERENCE_MM. The spline is not\n'
          '           printed: 20 teeth on Oe5.0 is 0.79 mm of pitch and ~0.24 mm of\n'
          '           tooth, against a CALIBRATED MIN_FEATURE_MM of 0.8. The\n'
          '           interference is ASSUMED - gauge it before printing a pair.')
    param('broach_from', '%.4f mm' % H.broach_from, 'derived: the spline starts here')
    param('broach_to', '%.4f mm' % H.broach_to,
          'derived: and ends here, 2.60 mm up inside the hex boss')
    param('engaged', '%.4f mm' % H.engaged,
          'how much spline the bore grips - the FULL 4.0 mm of MG90S spline,\n'
          '           because the stack runs past all of it')
    param('washer_d', '%.4f mm' % H.washer_d,
          'SMALLEST WASHER THAT WORKS, and it is not optional. The retaining\n'
          '           screw is Oe%.1f with a head near Oe5 and the broach bore is\n'
          '           Oe%.2f, so the head would sit over the hole with nothing to\n'
          '           clamp. Without a washer the hub walks up the spline.'
          % (H.screw_d, H.broach_d))
    param('access_d', PREFIX + 'washer_d + ' + PREFIX + 'free_fit',
          'derived: the washer has to PASS down this bore to reach its seat, so\n'
          '           it is the washer plus a free fit. It replaces the old 5.50\n'
          '           wh_screw_bore as the driver access, and on the idler side the\n'
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
    # The face that looks at the servo: the outboard side of the flange.
    SEAT = '-(' + WRIST + 'journal + ' + WRIST + 'flange_t)'

    # ---- phase 1: collar + flange + hex boss --------------------------------
    t0 = design.timeline.count
    disc('journal_collar', wval('hub_d'), '-' + WRIST + 'journal', WRIST + 'journal', NEW)
    # Trapped, not screwed: the flange cannot pass through the plate bore and
    # the effector's socket floor stops it going the other way.
    disc('retaining_flange', wval('flange_d'), SEAT, WRIST + 'flange_t', JOIN)

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
    # THREE BORES, and the order is the MG90S's own stack read upward from the
    # case. It used to be a horn hub relief, a blade slot cut six millimetres
    # inside the output boss, and a separate driver bore that already ran the
    # whole length. Now:
    #   boss_bore    clears the Oe6.0 output collar for 5.60. Pure clearance.
    #   spline_bore  UNDERSIZE. The steel spline broaches this on assembly.
    #   access_bore  passes the washer down to its seat, then the driver, and
    #                on the idler side the M3.
    # TWO DIAMETERS ON THE DRIVEN PART, because the spline sits ABOVE the
    # boss: a hub shorter than boss_bore_h never reaches the spline at all,
    # however good its bore is. That is what spline_hub() refuses on, and the
    # collar ALONE (7.00) does not clear it - see stack_h.
    disc('boss_bore', val('boss_bore_d'), SEAT, PREFIX + 'boss_bore_h', CUT)
    disc('spline_bore', val('broach_d'), SEAT + ' + ' + PREFIX + 'broach_from',
         PREFIX + 'engaged', CUT)
    disc('washer_access_bore', val('access_d'), SEAT + ' + ' + PREFIX + 'broach_to',
         PREFIX + 'stack_h - ' + PREFIX + 'broach_to', CUT)
    group(t1, PH_SPLINE)

    # ---- phase 3: finish ----------------------------------------------------
    t2 = design.timeline.count
    for z_pick, size, nm in ((reach, PREFIX + 'lead_in', 'hex_nose_lead_in'),
                             (-(journal + wval('flange_t')), STYLE + 'ef', 'bed_face_chamfer')):
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

    # THE CHECKS. The old one here was 'the horn relief is narrower than the
    # hex' and nothing else, which is why a blade slot buried inside the
    # output boss survived. What is left to get wrong is the SPLINE STACK, so
    # that is what is checked - against the servo, not against itself.
    boss_wall = (wval('hub_d') - val('boss_bore_d')) / 2
    assert boss_wall * 10 >= MIN_WALL_MM - TOL, (
        'only %.2f mm of collar wall around the Oe%.2f boss bore, and '
        'design_rules wants %.2f'
        % (boss_wall * 10, val('boss_bore_d') * 10, MIN_WALL_MM))
    assert val('broach_to') <= val('stack_h') + TOL, (
        'the spline tops out %.2f into a %.2f stack - the washer would have '
        'no face to bear on' % (val('broach_to') * 10, val('stack_h') * 10))
    assert val('engaged') * 10 >= ENGAGE_MIN_MM - TOL, (
        'only %.2f mm of spline engagement, want %.2f'
        % (val('engaged') * 10, ENGAGE_MIN_MM))
    # THE ONE THAT MATTERS IF wr_reach EVER SHRINKS. The collar alone is 0.60
    # short of the MG90S spline; the hex boss makes up the difference. Say so
    # out loud rather than letting a shortened reach quietly de-drive the arm.
    collar_only = journal + wval('flange_t')
    assert val('stack_h') > collar_only + TOL, (
        'the bore has to run past the collar to reach the spline and stack_h '
        '%.2f is not more than the collar %.2f'
        % (val('stack_h') * 10, collar_only * 10))
    assert val('broach_d') < val('washer_d') < val('access_d'), (
        'the Oe%.2f washer has to be BIGGER than the Oe%.2f broach bore to '
        'have anything to bear on and SMALLER than the Oe%.2f access bore to '
        'reach its seat' % (val('washer_d') * 10, val('broach_d') * 10,
                            val('access_d') * 10))
    hex_wall = (hex_af - val('access_d')) / 2
    assert hex_wall * 10 >= MIN_WALL_MM - TOL, (
        'only %.2f mm between the Oe%.2f access bore and the hex flats'
        % (hex_wall * 10, val('access_d') * 10))
    hex_corners = hex_af / math.cos(math.pi / HEX_SIDES)
    assert hex_corners < wval('hub_d'), (
        'hex is %.2f across corners but the collar is only %.2f - the hub cannot be '
        'threaded through its own bore' % (hex_corners * 10, wval('hub_d') * 10))
    # ---- PRINTABILITY GATE, flange face on the bed, built +Z ---------------
    # The orientation rests on one statement - the stack only ever narrows
    # going up - and until now that statement lived in the docstring, where
    # nothing could check it. Flange >= collar > hex-across-corners, the last
    # of which is already gated above for a different reason.
    assert wval('hub_d') <= wval('flange_d'), (
        'the Oe%.2f collar is wider than the Oe%.2f flange it stands on - '
        'flange-face-down stops being self-supporting'
        % (wval('hub_d') * 10, wval('flange_d') * 10))
    # The one face that prints over air: the inward annulus where the broach
    # bore narrows out of the boss clearance bore. Reported, not gated - it is
    # under a millimetre of reach off an anchored circle.
    bore_ledge = (val('boss_bore_d') - val('broach_d')) / 2
    bb = body.boundingBox
    _case_top = _MG90S.tab_thk + _MG90S.tab_below_top
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('hex %.2f af (socket %.1f - %.1f loc) reaching %.1f mm' % (
        hex_af * 10, wval('pivot_af') * 10, val('loc') * 10, reach * 10))
    print('hex across corners %.2f, threaded through a %.1f collar bore' % (
        hex_corners * 10, wval('hub_d') * 10))
    print('collar OD %.1f x %.1f, retaining flange OD %.1f x %.1f' % (
        wval('hub_d') * 10, journal * 10, wval('flange_d') * 10, wval('flange_t') * 10))
    print('seats %.2f up the MG90S (%.2f clear of its case top) - forearm.py '
          'must stand the J4 servo off to match'
          % (val('seat_z') * 10, val('seat_z') * 10 - _case_top))
    print('spline hub: boss bore Oe%.2f to %.2f, then Oe%.2f BROACHED %.2f..%.2f'
          % (val('boss_bore_d') * 10, val('boss_bore_h') * 10,
             val('broach_d') * 10, val('broach_from') * 10, val('broach_to') * 10))
    print('  %.1f mm of spline engaged | NO HORN | needs a Oe%.1f washer under '
          'the screw, passed down a Oe%.2f access bore'
          % (val('engaged') * 10, val('washer_d') * 10, val('access_d') * 10))
    print('  bore-able stack %.2f (collar %.2f + hex reach %.2f) against a %.2f '
          'minimum - the collar ALONE would not reach the spline'
          % (val('stack_h') * 10, collar_only * 10, reach * 10, H.min_height))
    print('walls: collar/boss bore %.2f | hex flats/access bore %.2f mm'
          % (boss_wall * 10, hex_wall * 10))
    print('PRINTABILITY - FLANGE FACE ON THE BED (z %.2f), BUILT +Z, SUPPORT OFF.'
          % (-(journal + wval('flange_t')) * 10))
    print('  stack narrows all the way up: Oe%.1f flange -> Oe%.1f collar -> '
          '%.2f af hex (%.2f across corners). No outside overhang.'
          % (wval('flange_d') * 10, wval('hub_d') * 10, hex_af * 10,
             hex_corners * 10))
    print('  one 90 deg face: a %.2f mm inward annulus where the Oe%.2f broach '
          'bore steps out of the Oe%.2f boss bore. Anchored all round; printed.'
          % (bore_ledge * 10, val('broach_d') * 10, val('boss_bore_d') * 10))
    print('  bed contact ~%.0f mm2 - hex-down it would be ~%.0f and both '
          'annular steps would invert into ceilings.'
          % (math.pi * (wval('flange_d') / 2 * 10) ** 2,
             HEX_SIDES * (hex_af / 2 * 10) ** 2 * math.tan(math.pi / HEX_SIDES)))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
