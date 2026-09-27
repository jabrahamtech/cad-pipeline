"""robotarm/j1_hub - Fusion MCP generating script.

2026-09-27 - J1 IS AN MG995 360 deg NOW. Prose below that says SG90 means
"the J1 servo"; every number comes from lib/j1_drive.py. The MG995's O13.0
boss put the boss bore right under the pilot circle, so the hub grew to 7.90
(pilots stand on a MIN_WALL floor over the boss bore) rather than moving the
bolt circle - the rotor's holes did not move.

Rebuilds `robotarm_j1_hub` (idempotent). Spec: specs/robotarm/j1_hub.md.

THE ONE PIECE BETWEEN THE J1 SG90 AND THE ARM. It is broached onto the
servo's own output spline and bolted flat to the underside of
shoulder_bracket's turntable disc - the rotor - with three M3. It replaces
the stamped four-arm horn, which is out of this machine entirely.

Frame: lib/servo.py's SERVO FRAME. Origin on the SG90 output axis at the
TAB plane, +Z up out of the shaft. That is the frame spline_hub() solves in,
so nothing here needs converting. The BODY is built with its underside on
z = 0 for a clean bed face; jh_seat_z records where that face lands on the
servo, and turntable_stator.py places the SG90 from the same number.

WHY THIS PART EXISTS RATHER THAN A BORE IN THE ROTOR. j3_pinion went
straight onto the MG90S spline four commits earlier and the obvious move was
to do the same to shoulder_bracket. It was priced and rejected, and the
pricing is in specs/robotarm/j1_hub.md. Shortest first:

  1. PRINT ORIENTATION, and this one is disqualifying. shoulder_bracket
     prints -X face down; its own docstring says the disc therefore "stands
     on edge". A broach bore cut into that disc is an XY-FACING hole, and
     lib/design_rules says in as many words that XY-facing holes come out
     undersize and out of round and want a teardrop. A broach bore has to be
     ROUND to a fraction of the 0.25 mm interference or it is not a fit, it
     is a lottery. j3_pinion could go direct BECAUSE its bore prints
     vertical, and it says so in its own print-orientation note. This hub
     prints the same way and inherits the same argument.
  2. THERE IS NO ASSEMBLY ORDER FOR A DIRECT BROACH. Broaching is a PRESS
     stroke of 0.25 mm diametral interference cutting twenty teeth into
     PETG. The rotor's height is set by three 608ZZ at r 27 and a ring
     hooked over its rim: once it is on the turntable there is no press
     stroke left, and pressing it on first makes the Oe68 journal impossible
     to enter afterwards.
  3. ITERATION COST. lib/servo.SPLINE_BROACH_INTERFERENCE_MM is graded
     ASSUMED and lib/servo.py says outright to print the sweep before
     committing a gear to it. Committing an ungauged press fit to the arm's
     largest structural part costs a whole shoulder-bracket print per try.
     This costs minutes, and it is the piece that SHOULD wear out.

WHAT THE BOLT CIRCLE IS WORTH, AND THE HONEST HALF OF IT. SG90 stall is
1.6 kg.cm = 156.9 N.mm (lib/arm_loads.STALL_KGCM['J1']). Stall, not duty,
is the right figure for an INTERFACE: a servo driven into a stop delivers
it.

    at the broach bore  r 2.33  F 67.5 N  over 4.65 x 2.50 = 11.6 mm2   5.81 MPa
    at 3 x M3 on r 8.00 F  6.5 N each     over 3.0 x 3.7  = 11.1 mm2    0.59 MPa

A factor of ten, bought with radius. AND THE HONEST HALF: THE BOLT CIRCLE
DOES NOT REDUCE THE LOAD ON THE SPLINE. The broach still carries all
156.9 N.mm at 5.81 MPa, because the servo has exactly one output and
everything leaves through it. What the bolt circle buys is WHERE that
5.81 MPa lives - in a 3 g consumable instead of in the arm's 85 g bracket -
and that the rotor keeps a FLAT interface with no fit on it at all. Anyone
reading the 10x as a strength win has read the wrong column.

5.81 MPa is not even the reason. PETG is 35 MPa in plane, x0.5 across
layers, /4 cyclic = 4.4 MPa allowable, so a direct broach is MARGINAL on
stress - interesting, and not decisive. Reasons 1-3 above decided it.

THE RETAINING SCREW IS NOT USED IN SERVICE, and this is the one place J1
deliberately differs from j3_pinion rather than copying it. j3_pinion needs
that screw and its washer because nothing else holds the pinion down on the
spline. This hub is bolted to a rotor that turntable_ring already captures
axially, so running the screw as well would be a SECOND AXIAL DATUM FIGHTING
THE FIRST - precisely the over-constraint that had the horn holding the
turret off its own bearings ("if we put the horn on the base gear the turret
plate does not touch the bearings"). Use the screw and its Oe6.25 washer to
pull the hub down WHILE THE SPLINE BROACHES IT, then take both out before
the hub is bolted up. There is deliberately NO washer recess in the top
face: that face is the bolted joint, and a washer sunk into it is a 1 mm
shim the rotor would ride on - the horn failure reinvented in a new hat.

THERE IS NO REGISTER BETWEEN HUB AND ROTOR, AND THAT IS DELIBERATE. The
rotor's three holes are Oe4.40 - M3 clearance 3.40 plus 1.00 mm of
INTENTIONAL radial float. The hub is centred by the SPLINE; the rotor is
centred by its Oe68 journal in the ring, itself a rotating fit with 0.35 mm
of play; the joint takes up whatever is left between the two axes when it is
tightened. Same move as lib/servo_hub.py's radial slots and
lib/servo.MG995_TAB_SLOT_X_MM. A tight register would have to be a round
bore in a disc that prints on edge - objection 1 all over again. The joint
carries torque by FRICTION FIRST: three M3 at r 8.00 hand-tight (~200 N
each, mu ~ 0.3 PETG on PETG) is ~1260 N.mm against 156.9 required, and if it
ever slips the screws come into bearing at 0.59 MPa as the backstop. (The
spec quotes ~1260 N.mm for that friction; 3 x 200 x 0.3 x 8.00 is 1440 and
this file prints what it computes rather than the round number. Either way
it is an order of magnitude over what the servo can deliver, so nothing
turns on which is right - but they should not silently disagree.)

2.50 mm OF SPLINE IS ALL AN SG90 HAS. The MG90S that J3 drives has 4.00.
spline_hub()'s engage_min is 2.00, and tt_ring_lift lets the rotor - and the
hub bolted to it - float up 0.40, leaving 2.10. There is no margin to spend:
do not add axial clearance anywhere in this stack. turntable_stator.py
asserts it and so does this file when tt_ring_lift is in the document.

Print plan: PETG, FLAT, BORE VERTICAL, TOP FACE ON THE BED. 40 % infill,
5 walls - the broach has to displace plastic without splitting the hub and
walls are what resist that. No support. sty_ef on the bed face, jh_lead_in
on the broach bore's lower mouth, which is where the spline enters. Same
orientation and the same argument as gripper_pinion and j3_pinion.

GAUGE THE BROACH INTERFERENCE BEFORE PRINTING THIS PART.
SPLINE_BROACH_INTERFERENCE_MM 0.25 is ASSUMED and has never been cut in PETG
on this printer. Sweep 0.15 / 0.20 / 0.25 / 0.30 on a stub first. This
blocks J1.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core
import adsk.fusion

from lib.arm_loads import STALL_KGCM as _STALL  # noqa: E402
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.design_rules import MIN_WALL_MM as _MIN_WALL  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_j1_hub'
BODY_NAME = 'j1_hub'
PREFIX = 'jh_'
TURRET = 'tt_'      # the J1 drive contract - SHARED with turntable_stator.py
STYLE = 'sty_'      # and shoulder_bracket.py; every value DERIVED below
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('j1_hub')
PH_BODY = 'hub body'
PH_SPLINE = 'spline bore'
PH_BOLTS = 'bolt circle'
PH_CUP = 'cable cup'
PH_FINISH = 'finish'
PHASES = [PH_BODY, PH_SPLINE, PH_BOLTS, PH_CUP, PH_FINISH]

# THE J1 DRIVE CONTRACT LIVES IN lib/j1_drive.py since 2026-09-27 (J1 -> MG995).
# It was typed verbatim here, in shoulder_bracket.py and in j1_hub.py; a
# servo swap is the change that finds every copy, so there is one now.
from lib.j1_drive import (  # noqa: E402
    J1_SERVO,
    J1_HUB_OVERSHOOT_MM,
    J1_HUB_ENGAGE_MIN_MM,
    J1_HUB_SCREW,
    J1_HUB_SCREW_D_MM,
    J1_HUB_BOLT_R_MM,
    J1_HUB_BOLT_AZ_DEG,
    J1_HUB_FLOAT_MM,
    J1_HUB_HOLE_D_MM,
    J1_HUB_HEAD_H_MM,
    J1_HUB_CBORE_D_MM,
    J1_HUB_PILOT_H_MM,
    J1_HUB_OD_MM,
    J1_HUB_SCREW_BORE_MM,
    J1_HUB_FACE_MM,
    J1_HUB,
    J1_BOSS_TOP_MM,
    J1_SPLINE_TOP_MM,
    J1_CUP_R_IN_MM,
    J1_CUP_WALL_MM,
    J1_CUP_SKIRT_Z_MM,
    J1_CUP_GATE_HALF_DEG,
    ROTOR_GATE_AZ_DEG,
)
_J1S = J1_SERVO

# --- THE J1 DRIVE CONTRACT ------------------------------------------------
# EVERY NUMBER IN THIS BLOCK IS COPIED VERBATIM FROM shoulder_bracket.py AND
# turntable_stator.py, WHICH DERIVE THEM THE SAME WAY. It is deliberately a
# copy and not an import: models/ scripts do not import each other, and the
# single source of truth is one layer down in lib/servo_hub.spline_hub() and
# lib/design_rules. If those three ever disagree the hub is BORED from one
# set of numbers and LOCATED by another, so run() asserts this file's values
# against the tt_* user parameters whenever a host has already declared them
# in the same document.
                               # spline top, so the spline stops SHORT of the
                               # rotor face instead of jacking it off its
                               # rollers.
                               # to solve and the face is what we are solving
                               # FOR; this probe is any value past min_height,
                               # used only to read broach_to back out.
                               # ring-lift check has something to measure to.
                               # would not survive being taken apart twice.
                               # counterbore in the ROTOR must clear the
                               # rotor's Oe5.40 screw bore (r 2.70 + wall 1.60
                               # + cbore 2.95 = 7.25) and this hub's OD must
                               # stay inside the connector gate at r 12.20.
                               # gate at az 270. Read from the spec, NOT
                               # re-derived here - shoulder_bracket.py cut the
                               # mating holes to these three angles and the
                               # only thing this file may do is agree.
                               # and not in this part. See the docstring.
                               # pilot, is the width the screw bears on once
                               # it has formed its own thread, and it is what
                               # both the spec's and shoulder_bracket.py's
                               # bearing tables are computed at (3.0 x 3.7).
# PILOT DEPTH, AND A DISCREPANCY IN THE SPEC WORTH RECORDING. 3.70 is the
# thread engagement BOTH bearing-pressure tables are computed at - the spec's
# "3 x (Oe3.0 x 3.7) = 33.3 mm2" and shoulder_bracket.py's "3.0 x 3.7 = 11.1
# mm2" - so it is the number to keep. The spec derives it as "body 5.30 -
# MIN_WALL 1.60", and that arithmetic DOES NOT CLOSE AXIALLY: this hub is
# 6.80 tall, not 5.30. 5.30 is the RADIAL ligament between the Oe5.40 boss
# bore and the r 8.00 bolt circle (8.00 - 2.70), which is a width, not a
# depth. Kept at 3.70 as an explicit choice rather than a derivation that
# does not hold: it is what the load numbers assume, and it leaves 3.10 mm of
# floor over the seat face against a 1.60 MIN_WALL. Asserted below.
# INSERTION LEAD-IN ON THE BROACH MOUTH, CAPPED BY THE STEP IT SITS ON.
# Typed as a flat 0.5 first and Fusion refused it outright:
#   "3 : Chamfer1 / Compute Failed ... could not be created at the requested
#   size". The mouth is the step between the Oe5.40 boss bore and the Oe4.65
# broach, which is (5.40 - 4.65) / 2 = 0.375 mm of RADIUS. A 0.5 chamfer has
# nowhere to go. It is derived from the step now, so it cannot outgrow it
# again when the broach interference is corrected after a gauge print - and
# SPLINE_BROACH_INTERFERENCE_MM is ASSUMED, so that WILL move.
J1_HUB_LEAD_IN_NOMINAL_MM = 0.5
J1_HUB_LEAD_IN_MARGIN_MM = 0.1   # leave the step some square shoulder
# 1 kg.cm = 1 kg x 9.80665 m/s2 x 0.01 m = 0.0980665 N.m = 98.0665 N.mm.
KGCM_TO_NMM = 98.0665
# Comparison epsilon and a friction estimate. NOT dimensions.
TOL = 1e-9
REL_TOL = 1e-6
BOLT_PRELOAD_N = 200.0         # ASSUMED - M3 hand-tight in PETG
PETG_ON_PETG_MU = 0.3          # HANDBOOK


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

    def turret(name, expr, comment='', units='mm'):
        _set(TURRET + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    def host(name):
        """A tt_* value a HOST part already wrote, or None.

        turntable_stator.py and shoulder_bracket.py declare this same block.
        When one of them has run into this document first, its values are
        what the servo is placed by and the rotor is cut to, so this part
        must agree with them rather than quietly overwrite them with its
        own arithmetic. itemByName returns None on a miss - no exception, so
        no try/except.
        """
        p = ups.itemByName(TURRET + name)
        return None if p is None else p.value * 10

    # ---- the SHARED J1 drive contract, declared identically in
    # ---- turntable_stator.py and shoulder_bracket.py -----------------------
    # Read BEFORE they are overwritten, so a disagreement is caught rather
    # than papered over by this file writing last.
    _was = dict((n, host(n)) for n in
                ('hub_seat_z', 'hub_h', 'hub_broach_d', 'hub_od',
                 'hub_bolt_r', 'hub_engaged'))

    turret('hub_seat_z', '%.4f mm' % J1_HUB.seat_z,
           'servo-z of the hub UNDERSIDE - one running gap above the SG90 case\n'
           '           top. lib/servo_hub.spline_hub(). NEVER type this.')
    turret('hub_h', '%.4f mm' % J1_HUB_FACE_MM,
           'hub total height, underside to top face. DERIVED: enough to swallow\n'
           '           the whole %.2f of spline reach plus %.2f of overshoot, so the\n'
           '           spline stops SHORT of the rotor instead of lifting it off its\n'
           '           rollers.' % (J1_HUB.broach_to, J1_HUB_OVERSHOOT_MM))
    turret('hub_broach_d', '%.4f mm' % J1_HUB.broach_d,
           'the hub\'s bore - THE STEEL SPLINE CUTS THIS, it is not printed.\n'
           '           20 teeth on Oe4.9 is 0.77 of pitch and ~0.24 of tooth against a\n'
           '           CALIBRATED MIN_FEATURE_MM of 0.8. Undersize by lib/servo.\n'
           '           SPLINE_BROACH_INTERFERENCE_MM, which is ASSUMED - gauge it.')
    turret('hub_engaged', '%.4f mm' % J1_HUB.engaged,
           'how much spline the bore grips. 2.50 is ALL an SG90 has (the MG90S\n'
           '           has 4.00) and tt_ring_lift takes 0.40 of it when the rotor\n'
           '           floats up.')
    turret('hub_od', '%.4f mm' % J1_HUB_OD_MM,
           'hub outer diameter. DERIVED from the bolt circle plus a self-tap\n'
           '           boss and MIN_WALL, and it is what keeps this part inside the\n'
           '           connector gate at r 12.20.')
    turret('hub_bolt_r', '%.4f mm' % J1_HUB_BOLT_R_MM,
           'bolt circle radius. THE WHOLE POINT OF THE SEPARATE HUB: it moves\n'
           '           the drive from r 2.33 at the broach bore to r 8.00. It does NOT\n'
           '           unload the spline - see this file\'s docstring.')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # ---- what only this part cuts -----------------------------------------
    param('seat_z', TURRET + 'hub_seat_z',
          'this body is BUILT from z = 0 at its underside; this is the servo-z\n'
          '           that face lands on. turntable_stator.py places the SG90 from the\n'
          '           same number, so the two must not drift.')
    param('face', TURRET + 'hub_h', 'hub height - the SHARED tt_hub_h')
    param('od', TURRET + 'hub_od', 'hub outer diameter - the SHARED tt_hub_od')
    # ---- the CABLE CUP - lib/j1_drive, revision 2026-09-27 -----------------
    param('cup_r_in', '%.2f mm' % J1_CUP_R_IN_MM, 'skirt inner radius - the loom loop\'s outer wall')
    param('cup_wall', '%.2f mm' % J1_CUP_WALL_MM, 'skirt wall and top ring - MIN_WALL')
    param('cup_skirt_z', '%.2f mm' % J1_CUP_SKIRT_Z_MM,
          'skirt lower edge above this part\'s underside: 0.8 over the MG995 case top')
    param('cup_gate_az', '%.2f deg' % ROTOR_GATE_AZ_DEG,
          'the rotor\'s connector gate, SAME frame - the bolt pattern keys it', 'deg')
    param('cup_gate_half', '%.2f deg' % J1_CUP_GATE_HALF_DEG,
          'half-width of the cutout under the rotor gate + cable window', 'deg')
    param('cup_gate_clear', '0.5 mm', 'how far the cutout stands off the hub body')
    param('cup_lip', '0.8 mm',
          'chamfer on the skirt\'s inner lower edge - the loom slides under it')
    param('boss_bore_d', '%.4f mm' % J1_HUB.boss_clear_d,
          'lower bore - CLEARS the Oe5.0 output collar at a free fit. Nothing\n'
          '           grips the boss; it only has to pass. It is also the hole the\n'
          '           SG90 retaining screw\'s head goes down during the broach step,\n'
          '           and it is wider than the rotor\'s Oe%.2f screw bore.'
          % J1_HUB_SCREW_BORE_MM)
    param('boss_bore_h', '%.4f mm' % J1_HUB.boss_clear_to,
          'how far up the bore stays wide - to the top of the boss. %.2f of the\n'
          '           %.2f hub is spent just getting past the SG90 collar, which is\n'
          '           why a thin hub cannot drive a servo however good its bore is.'
          % (J1_HUB.boss_clear_to, J1_HUB_FACE_MM))
    param('broach_d', TURRET + 'hub_broach_d',
          'upper bore - the SHARED tt_hub_broach_d. THE STEEL SPLINE CUTS IT.')
    param('broach_to', '%.4f mm' % J1_HUB.broach_to,
          'derived: where the spline ends inside the hub. jh_face stands\n'
          '           %.2f past it so the spline cannot reach the rotor face.'
          % J1_HUB_OVERSHOOT_MM)
    param('engaged', TURRET + 'hub_engaged', 'how much spline the bore grips')
    param('washer_d', '%.4f mm' % J1_HUB.washer_d,
          'SMALLEST washer that lands on the bore mouth. ASSEMBLY AID ONLY:\n'
          '           it and the retaining screw pull the hub down WHILE the spline\n'
          '           broaches it and then BOTH COME OUT. There is deliberately no\n'
          '           recess for it - the top face is the bolted joint and a washer\n'
          '           sunk into it is a shim the rotor would ride on.')
    param('bolt_r', TURRET + 'hub_bolt_r', 'pilot circle - the SHARED tt_hub_bolt_r')
    param('pilot_d', '%.4f mm' % _FASTENER[J1_HUB_SCREW]['pilot'],
          'M3 self-tapping pilot - lib/design_rules FASTENER_MM. HANDBOOK.\n'
          '           The rotor carries the Oe%.2f clearance holes and the Oe%.2f head\n'
          '           counterbores; the thread is in THIS part.'
          % (J1_HUB_HOLE_D_MM, J1_HUB_CBORE_D_MM))
    param('pilot_h', '%.4f mm' % J1_HUB_PILOT_H_MM,
          'thread engagement, blind FROM THE TOP FACE. 3.70 is what both\n'
          '           bearing-pressure tables are computed at (3.0 x 3.7 = 11.1 mm2 a\n'
          '           bolt). It leaves %.2f of floor over the seat face against a\n'
          '           %.2f MIN_WALL - see the module note on the spec\'s "body 5.30".'
          % (J1_HUB_FACE_MM - J1_HUB_PILOT_H_MM, _MIN_WALL))
    # val() answers in CENTIMETRES in this file - the x10 is not decoration.
    # Without it the step read 0.037 and the assert below fired on geometry
    # that was perfectly fine.
    _step_r = (val('boss_bore_d') - val('broach_d')) * 10.0 / 2.0
    _lead_in = min(J1_HUB_LEAD_IN_NOMINAL_MM,
                   _step_r - J1_HUB_LEAD_IN_MARGIN_MM)
    assert _lead_in > 0.0, (
        'the boss bore Oe%.2f and the broach Oe%.2f leave a %.3f mm step - '
        'there is no room for a lead-in at all'
        % (val('boss_bore_d'), val('broach_d'), _step_r))
    param('lead_in', '%.4f mm' % _lead_in,
          'lead-in chamfer on the broach bore\'s LOWER mouth - the step at\n'
          '           jh_boss_bore_h, which is exactly where the spline enters. A\n'
          '           square mouth shaves the spline instead of being cut by it.\n'
          '           DERIVED from the %.3f mm radial step, not typed: a flat 0.5 was\n'
          '           and Fusion refused to build it.' % _step_r)
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE ---------------------
    # Deleting a component's LAST occurrence orphans the component: it drops
    # out of allComponents while still holding its name, so a rename
    # afterwards cannot reach it and the rebuild is handed 'robotarm_x (1)'.
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        # SKIP THE ROOT. Once this part lives in its own saved file the root
        # component carries the DOCUMENT's name, which is COMPONENT - and a
        # root component cannot be renamed, so the rename below raised
        # "3 : root component name cannot be changed" and nothing rebuilt.
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
        'component came back as %r - a stale component still holds the name'
        % comp.name)
    ext = comp.features.extrudeFeatures
    chf = comp.features.chamferFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                sk.name + ': expected ' + str(expected) + ', got '
                + str(sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            # Without this a CUT eats every other component in the document -
            # feature operations take part with everything they intersect,
            # across component boundaries. See fusion/PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(
                start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, 0.0))

    def disc(name, x_cm, y_cm, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            mpt(sk, x_cm, y_cm), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def edges_in_plane_z(z_pick, radius_pick=None):
        """Edges lying flat in a z plane, optionally only those of one radius.

        THE RADIUS FILTER IS NOT OPTIONAL FOR THE BROACH MOUTH, and leaving it
        out is why this part would not build. The mouth is an ANNULAR step, so
        the plane at jh_boss_bore_h holds TWO circles - the Oe5.40 boss bore
        and the Oe4.65 broach. Selecting the plane selected both, and Fusion
        was asked to fit two 0.275 chamfers into 0.375 mm of annulus:
          "3 : Chamfer1 / Compute Failed ... could not be created at the
          requested size"
        Only the inner circle is the mouth the spline enters; chamfering the
        outer one would just thin the step for nothing.
        """
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if not (abs(eb.minPoint.z - z_pick) < val('tol')
                    and abs(eb.maxPoint.z - z_pick) < val('tol')):
                continue
            if radius_pick is not None:
                r = (eb.maxPoint.x - eb.minPoint.x) / 2.0
                if abs(r - radius_pick) > val('tol') * 10:
                    continue
            col.add(e)
        return col

    # ---- phase 1: the body ------------------------------------------------
    # A plain disc, and it is deliberately plain. Every feature this part
    # could grow - a register spigot, a washer recess, a lightening pocket -
    # is either an over-constraint (see the docstring) or material taken out
    # of the one part in the stack that has to survive a press fit.
    t0 = design.timeline.count
    disc('hub_blank', 0, 0, val('od'), '0.0 mm', PREFIX + 'face', NEW)
    group(t0, PH_BODY)

    # ---- phase 2: the spline bore -----------------------------------------
    # TWO DIAMETERS, because the spline sits ABOVE the boss: the lower bore
    # CLEARS the Oe5.0 output collar and only the upper bore grips the Oe4.9
    # spline. That is why a hub thinner than jh_boss_bore_h cannot drive a
    # servo at all, which is what spline_hub() refuses on.
    # ONE THROUGH BORE, not a blind pocket. The bore has to pass the SG90's
    # retaining screw and its washer during the broach step and let a driver
    # back onto them afterwards; a blind bore makes that a puzzle instead of
    # an assembly, and it would print a bridged floor over the spline.
    t1 = design.timeline.count
    disc('boss_bore', 0, 0, val('boss_bore_d'), '0.0 mm',
         PREFIX + 'boss_bore_h', CUT)
    disc('spline_bore', 0, 0, val('broach_d'), PREFIX + 'boss_bore_h',
         PREFIX + 'face - ' + PREFIX + 'boss_bore_h', CUT)
    group(t1, PH_SPLINE)

    # ---- phase 3: the bolt circle -----------------------------------------
    # THREE BLIND PILOTS FROM THE TOP FACE. Blind, because the top face is
    # the bolted joint and the underside runs 0.40 off a servo case - a
    # through pilot would open into that gap and the screw tips would stand
    # in it. The angles are READ FROM specs/robotarm/j1_hub.md and cut to
    # match shoulder_bracket.py's clearance holes; they are not re-derived
    # here, because two parts deriving the same pattern independently is how
    # a pattern goes out of agreement.
    t2 = design.timeline.count
    for _i, _az in enumerate(J1_HUB_BOLT_AZ_DEG):
        _a = math.radians(_az)
        disc('bolt_pilot_%d' % _i, val('bolt_r') * math.cos(_a),
             val('bolt_r') * math.sin(_a), val('pilot_d'),
             PREFIX + 'face - ' + PREFIX + 'pilot_h', PREFIX + 'pilot_h', CUT)
    group(t2, PH_BOLTS)

    # ---- phase 4: the cable cup ---------------------------------------------
    # A flat ring flush with the bolted top face, out to a skirt that hangs
    # to just above the servo. The J1 loom loop lives INSIDE it, wrapping the
    # hub as J1 turns +-180 deg, and cannot drift out into the 608/rotor nip.
    # The cutout under the rotor's gate lets plugs drop straight into it.
    t_cup = design.timeline.count
    r_out = val('cup_r_in') + val('cup_wall')

    def annulus(name, r_o, r_i, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        for r in (r_o, r_i):
            sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0), r)
        want = math.pi * (r_o ** 2 - r_i ** 2)
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            p = sk.profiles.item(i)
            if abs(p.areaProperties().area - want) < want * REL_TOL:
                c.add(p)
        assert c.count == 1, sk.name + ': annulus profile not found'
        return extrude(c, op, z0_expr, dz_expr, name)

    annulus('cup_top', r_out, val('od') / 2 - val('tol'),
            PREFIX + 'face - ' + PREFIX + 'cup_wall', PREFIX + 'cup_wall', JOIN)
    annulus('cup_skirt', r_out, val('cup_r_in'), PREFIX + 'cup_skirt_z',
            PREFIX + 'face - ' + PREFIX + 'cup_skirt_z', JOIN)
    # the gate cutout: an annular sector in the top ring only
    sk = sketch(comp.xYConstructionPlane, 'sk_cup_gate')
    arcs, lines = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines
    _mid, _half = val('cup_gate_az'), val('cup_gate_half')
    _ri = val('od') / 2 + val('cup_gate_clear')
    _ro = val('cup_r_in')

    def _p(r, a):
        return mpt(sk, r * math.cos(a), r * math.sin(a))
    arcs.addByThreePoints(_p(_ro, _mid - _half), _p(_ro, _mid), _p(_ro, _mid + _half))
    arcs.addByThreePoints(_p(_ri, _mid - _half), _p(_ri, _mid), _p(_ri, _mid + _half))
    lines.addByTwoPoints(_p(_ri, _mid - _half), _p(_ro, _mid - _half))
    lines.addByTwoPoints(_p(_ri, _mid + _half), _p(_ro, _mid + _half))
    _v = comp.bRepBodies.item(0).volume
    extrude(profiles(sk, expected=1), CUT,
            PREFIX + 'face - ' + PREFIX + 'cup_wall - 1.0 mm', PREFIX + 'cup_wall + 2.0 mm',
            'cup_gate_cutout')
    assert _v - comp.bRepBodies.item(0).volume > TOL, 'the cup gate cutout cut nothing'
    group(t_cup, PH_CUP)

    # ---- phase 4: finish ---------------------------------------------------
    # The bed face is the TOP face - this prints top down, bore vertical, so
    # the broach bore comes out as a clean vertical hole and the bolt circle
    # threads into solid material rather than into a bridged ceiling.
    t3 = design.timeline.count
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_z(val('boss_bore_h'), val('broach_d') / 2.0),
        V(PREFIX + 'lead_in'), False)
    chf.add(c_inp).name = 'broach_lead_in'
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_z(val('face')), V(STYLE + 'ef'), False)
    chf.add(c_inp).name = 'bed_face_chamfer'
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_z(val('cup_skirt_z'), val('cup_r_in')), V(PREFIX + 'cup_lip'), False)
    chf.add(c_inp).name = 'cup_lip'
    group(t3, PH_FINISH)

    # ---- identity ----------------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d' % comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used = a.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    # ---- the checks --------------------------------------------------------
    # THE HOSTS ARE THE AUTHORITY. If turntable_stator.py or
    # shoulder_bracket.py has already written this document, the servo is
    # placed and the rotor is cut to THEIR numbers. Any drift here means the
    # hub is bored from one set and located by another.
    for _n, _prev in _was.items():
        if _prev is None:
            continue
        assert abs(_prev - tval(_n) * 10) < TOL, (
            'tt_%s was %.4f when a host part wrote it and this file derives '
            '%.4f - the hub would be bored from one set of numbers and '
            'located by another. Fix lib/, not one of the three copies'
            % (_n, _prev, tval(_n) * 10))

    _lift = ups.itemByName(TURRET + 'ring_lift')
    if _lift is not None:
        _engaged_lifted = tval('hub_engaged') * 10 - _lift.value * 10
        assert _engaged_lifted >= J1_HUB_ENGAGE_MIN_MM - TOL, (
            'the hub grips %.2f mm of spline and tt_ring_lift lets the rotor '
            'rise %.2f, leaving %.2f against a %.2f minimum. Deepen nothing - '
            'either take float out of the ring or accept that an SG90 has '
            '2.50 mm of spline and no more'
            % (tval('hub_engaged') * 10, _lift.value * 10, _engaged_lifted,
               J1_HUB_ENGAGE_MIN_MM))

    # The spline must stop SHORT of the top face. If it ever reaches it, the
    # servo shaft bears on the rotor and carries the arm - which is the
    # failure this whole migration exists to fix.
    assert val('face') * 10 - val('broach_to') * 10 >= J1_HUB_OVERSHOOT_MM - TOL, (
        'the spline tops out %.2f into a %.2f hub, leaving %.2f of overshoot '
        'against %.2f wanted - the shaft would push on the rotor'
        % (val('broach_to') * 10, val('face') * 10,
           (val('face') - val('broach_to')) * 10, J1_HUB_OVERSHOOT_MM))
    assert val('engaged') * 10 >= J1_HUB_ENGAGE_MIN_MM - TOL, (
        'only %.2f mm of spline engagement against a %.2f minimum'
        % (val('engaged') * 10, J1_HUB_ENGAGE_MIN_MM))
    assert val('broach_d') < val('boss_bore_d'), (
        'the broach bore Oe%.2f is not smaller than the boss clearance '
        'Oe%.2f - the output collar would not pass'
        % (val('broach_d') * 10, val('boss_bore_d') * 10))

    # THE BORE'S TWO STEPS MUST LAND ON THE SERVO'S OWN FEATURES. This body
    # is built from z = 0 at its underside; lib/servo.spline_z() says where
    # the boss and the spline actually are in the SERVO frame. If seat_z and
    # the bore steps ever stop adding up to those, the hub is a nicely
    # dimensioned part that grips nothing.
    assert abs((val('seat_z') + val('boss_bore_h')) * 10 - J1_BOSS_TOP_MM) < TOL, (
        'the bore steps from Oe%.2f to Oe%.2f at servo-z %.2f and the SG90 '
        'output collar tops out at %.2f - the wide bore stops short of the '
        'boss or runs past it'
        % (val('boss_bore_d') * 10, val('broach_d') * 10,
           (val('seat_z') + val('boss_bore_h')) * 10, J1_BOSS_TOP_MM))
    assert abs((val('seat_z') + val('broach_to')) * 10 - J1_SPLINE_TOP_MM) < TOL, (
        'the broach bore is drawn to servo-z %.2f and the SG90 spline tops '
        'out at %.2f'
        % ((val('seat_z') + val('broach_to')) * 10, J1_SPLINE_TOP_MM))

    # PILOT FLOOR. Blind from the top, so what is left underneath is what
    # stops the screw tip standing in the running gap over the servo case.
    _floor = (val('face') - val('pilot_h')) * 10
    assert _floor >= _MIN_WALL - TOL, (
        'a %.2f pilot in a %.2f hub leaves %.2f of floor over the seat face, '
        'under a %.2f MIN_WALL'
        % (val('pilot_h') * 10, val('face') * 10, _floor, _MIN_WALL))

    # THE TWO WALLS THAT SIZE THE DISC. Inboard: pilot to boss bore.
    # Outboard: pilot to the rim, which is what tt_hub_od was derived from,
    # so this one should land EXACTLY on MIN_WALL.
    # 2026-09-27, MG995: the O13.40 boss bore reaches r 6.70, exactly where a
    # O2.60 pilot on r 8.00 starts, so there is NO radial wall. lib/j1_drive
    # grows the hub instead so the pilots stand ON TOP of the boss bore with
    # a MIN_WALL floor between them. Either ligament is a wall; one must be.
    _in_wall = (val('bolt_r') - val('pilot_d') / 2 - val('boss_bore_d') / 2) * 10
    _over_wall = (val('face') - val('pilot_h') - val('boss_bore_h')) * 10
    assert max(_in_wall, _over_wall) >= _MIN_WALL - TOL, (
        'only %.2f mm radially and %.2f mm axially between the Oe%.2f boss '
        'bore and the pilots, against a %.2f MIN_WALL'
        % (_in_wall, _over_wall, val('boss_bore_d') * 10, _MIN_WALL))
    _out_wall = (val('od') / 2 - val('bolt_r') - val('pilot_d') / 2) * 10
    assert _out_wall >= _MIN_WALL - TOL, (
        'only %.2f mm of rim outside the pilot circle - tt_hub_od %.2f no '
        'longer follows from tt_hub_bolt_r %.2f'
        % (_out_wall, val('od') * 10, val('bolt_r') * 10))

    # THE WASHER IS AN ASSEMBLY AID AND MUST NOT BECOME A JOINT. It has to
    # land on the bore mouth and stay well clear of the pilots, because
    # anything it touches during the broach step becomes a second axial datum.
    assert val('washer_d') * 10 > val('broach_d') * 10, (
        'the Oe%.2f washer does not overhang the Oe%.2f bore it is meant to '
        'bear beside' % (val('washer_d') * 10, val('broach_d') * 10))
    assert val('washer_d') / 2 < val('bolt_r') - val('pilot_d') / 2, (
        'the Oe%.2f washer reaches the pilot circle at r %.2f - it would '
        'bear on the bolted joint instead of beside the bore'
        % (val('washer_d') * 10, val('bolt_r') * 10))

    # THE FLOAT IS IN THE ROTOR, NOT HERE. Nothing in this file cuts it, so
    # the check is on the arithmetic the two parts share.
    assert (J1_HUB_HOLE_D_MM - _FASTENER[J1_HUB_SCREW]['clearance']
            - J1_HUB_FLOAT_MM) < TOL, (
        'the rotor hole Oe%.2f is not M3 clearance plus the %.2f of radial '
        'float this joint is centred by'
        % (J1_HUB_HOLE_D_MM, J1_HUB_FLOAT_MM))

    # ---- diagnostics -------------------------------------------------------
    _stall_nmm = _STALL['J1'] * KGCM_TO_NMM
    _bore_r = val('broach_d') * 10 / 2
    _bore_area = val('broach_d') * 10 * val('engaged') * 10
    _bore_mpa = (_stall_nmm / _bore_r) / _bore_area
    _bolt_f = _stall_nmm / (len(J1_HUB_BOLT_AZ_DEG) * val('bolt_r') * 10)
    _bolt_area = J1_HUB_SCREW_D_MM * val('pilot_h') * 10
    _bolt_mpa = _bolt_f / _bolt_area
    _friction_nmm = (len(J1_HUB_BOLT_AZ_DEG) * BOLT_PRELOAD_N
                     * PETG_ON_PETG_MU * val('bolt_r') * 10)
    _case_top = _J1S.tab_thk + _J1S.tab_below_top

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used))
    print('seats %.2f up the %s (%.2f clear of its case top) - '
          'turntable_stator.py places the servo from the SAME number'
          % (val('seat_z') * 10, _J1S.name, val('seat_z') * 10 - _case_top))
    print('spline hub: boss bore Oe%.2f to %.2f, then Oe%.2f BROACHED %.2f..%.2f'
          % (val('boss_bore_d') * 10, val('boss_bore_h') * 10,
             val('broach_d') * 10, val('boss_bore_h') * 10,
             val('broach_to') * 10))
    print('  %.2f mm of spline engaged (an %s has %.2f in total) | '
          '%.2f of overshoot above it | NO HORN'
          % (val('engaged') * 10, _J1S.name, _J1S.spline_h,
             (val('face') - val('broach_to')) * 10))
    print('  the Oe%.2f washer and the servo screw are an ASSEMBLY AID ONLY - '
          'both come OUT before the rotor goes on' % (val('washer_d') * 10))
    print('bolt circle: %d x %s pilot Oe%.2f x %.2f deep at r %.2f, az %s'
          % (len(J1_HUB_BOLT_AZ_DEG), J1_HUB_SCREW, val('pilot_d') * 10,
             val('pilot_h') * 10, val('bolt_r') * 10, J1_HUB_BOLT_AZ_DEG))
    print('  the ROTOR carries Oe%.2f clearance (M3 + %.2f of DELIBERATE '
          'radial float) and Oe%.2f x %.2f head counterbores - '
          'shoulder_bracket.py cuts them, this file only agrees with them'
          % (J1_HUB_HOLE_D_MM, J1_HUB_FLOAT_MM, J1_HUB_CBORE_D_MM,
             J1_HUB_HEAD_H_MM))
    print('walls: %.2f inboard (radial) / %.2f over the boss bore (axial) to the '
          'pilots, %.2f outboard to the rim | pilot floor %.2f'
          % (_in_wall, _over_wall, _out_wall, _floor))
    print('LOAD, at %s STALL %.1f N.mm (lib/arm_loads.STALL_KGCM):'
          % (_J1S.name, _stall_nmm))
    print('  broach bore  r %.2f  %.2f MPa  <- THE SPLINE STILL CARRIES ALL '
          'OF IT' % (_bore_r, _bore_mpa))
    print('  bolt circle  r %.2f  %.2f MPa per bolt, and this is where it '
          'LIVES, not less load' % (val('bolt_r') * 10, _bolt_mpa))
    print('  friction at %.0f N a bolt, mu %.2f: %.0f N.mm against %.1f '
          'required - the screws are the backstop, not the drive'
          % (BOLT_PRELOAD_N, PETG_ON_PETG_MU, _friction_nmm, _stall_nmm))
    print('  the %.2f MPa lives in a %.1f g consumable instead of the '
          'bracket. GAUGE THE BROACH BEFORE PRINTING - the %.2f mm '
          'interference is ASSUMED'
          % (_bore_mpa, body.physicalProperties.mass * 1000,
             _J1S.spline_dia - val('broach_d') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s'
          % (body.volume * 1000, body.physicalProperties.mass * 1000,
             body.isValid))
    print('bodies: %d | sketches: %d | user params: %d'
          % (comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
