"""robotarm/shoulder_bracket - Fusion MCP generating script.

2026-09-27 - J1 (the rotor this part carries) is driven by an MG995 360 deg
now. The J1 drive contract is lib/j1_drive.py; the only change it makes here
is the rotor's centre screw bore, O5.40 -> O6.40, for the MG995's M3 horn
screw. A bracket already printed can be DRILLED to 6.5 instead of reprinted.

Rebuilds `robotarm_shoulder_bracket` (idempotent). Spec: specs/robotarm/_state.md.

J1's rotating half AND J2's fork, in one part. Its underside is the Ø96
turntable disc that rides the three 608ZZ rollers in the ALREADY PRINTED
legacy base; standing on that disc is the fork that straddles the upper arm
and carries the MG995.

Local frame: origin ON THE J2 PITCH AXIS. +X along that axis (drive side),
+Y forward along the arm's reach at zero pitch, +Z up. The disc's top face is
at z = -sb_stand_h and its underside - the race face - at one disc thickness
below that.

THIS PART IS ALSO J1'S ROTOR. Jonathan has printed the legacy base PLATTER -
the control unit, with the electronics bay and the yaw servo column - and that
is kept. The legacy turret that sat on it is not: a 12 mm solid Ø104 plate,
three M8 axle bolts, three separate hold-down clips and three more heat-set
inserts. turntable_stator.py and turntable_ring.py replace it.

So the underside of this part is the turntable disc:

  race face flat, r 23.0..31.0   where the three 608ZZ touch - keep it FLAT
  Ø68 boss, tt_boss_h proud      THE JOURNAL. It turns inside the ring's bore
                                 and it is what locates the arm radially.
  Ø76 rim below that             the ring hooks over it with 0.40 of daylight
  flat face + 3 x M3 on r 8.0    the J1 hub bolts here and drives the disc

The ring finishes flush with the boss top, so the plane the fork stands on IS
the boss top and nothing of the arm ever reaches past r 34.

Nothing caps rotation, so J1 gets the servo's full 180 deg.

NO HORN, AND NO CROSS POCKET. Until 2026-08-31 the yaw servo's stamped
four-arm horn drove this disc through a tapered cross pocket in its
underside. The bench reported both halves of that failing: the arms did not
enter the slots ("the actual horn tips dont fit in anywhere"), and with a
horn fitted the disc sat ON THE HORN rather than on its rollers ("the turret
plate does not touch the bearings"). Neither was a tolerance problem - the
pocket was cut to a modelled arm width no real arm has, and the seating gap
cancelled out of its own derivation, so it was 0.00 by construction.

What replaces it is FLAT. A separately printed hub is broached onto the
SG90's spline and bolted up against this underside with three M3 on an
r 8.00 circle, heads counterbored flush into the boss top. This disc keeps
no fit of any kind at the drive: a flat face, three deliberately oversize
clearance holes, and a screw bore that only has to stay clear of things.
The hub is a NEW part that neither this file nor turntable_stator builds -
spec: specs/robotarm/j1_hub.md - and the reasoning for a bolted hub rather
than boring this disc straight onto the spline the way j3_pinion does is at
the top of the code, with the torque arithmetic. The short version is that
this part prints ON EDGE, so a broach bore in it would be an XY-facing hole
in a part that needs it round to a fraction of 0.25 mm.

THE HOLES ARE OVERSIZE ON PURPOSE. There is no register between hub and
rotor. The hub is centred by the spline, this disc is centred by its O68
journal in the ring, and the M3 clearance holes carry 1.0 mm of deliberate
float so the joint takes up whatever is left between the two axes when it is
tightened. That is lib/servo_hub.py's radial-slot argument and
MG995_TAB_SLOT_X_MM's, applied to a bolt circle.

THE SERVO POINTS DOWN, AND THAT IS THE WHOLE ARRANGEMENT. An MG995 is 40 mm
along its own long axis with the shaft 10 mm from one end, so 30 mm of case
has to go somewhere. Pointing it UP leaves the outer tab 33.9 mm above the
pitch axis, which is 20 mm past the top of the pivot boss: the mounting pad
becomes a free-standing ear, needs support material to print, and cantilevers
55 g of servo off nothing. Pointing it DOWN lands that same tab 1.6 mm inside
the disc. The pad then runs boss-to-disc as one unbroken web, prints with no
support in the +X build direction, and puts the heaviest single component at
the bottom of the arm where J1 pays least for it.

sb_stand_h IS BOXED IN, and that is why it is 38 and not a round number.
Above 39.6 the servo pad stops reaching the disc and becomes a cantilever
again; below about 30.4 the MG995's case fouls the retainer ring as the turret
turns past it. Both are asserted. Within that window, higher is better - every
millimetre buys a little more down-pitch before the arm reaches its own base.

THE LEGS ARE SOLID, ON PURPOSE. Every other link in this arm is hollowed to
the wall because its mass sits outboard of a joint that has to hold it up.
This part sits BELOW J2, so its mass loads no pitch joint at all - only J1,
whose axis is vertical, so gravity does not see it. What it does carry is the
entire arm's bending moment through two 7.5 mm plates. The disc is lightened
where that is provably free and nowhere else: the race band and the load path
under the legs stay full thickness.

THE TAB SLOTS ARE SLOTS BECAUSE THE DATASHEET IS NOT TRUSTWORTHY. The two
MG995 drawings Jonathan supplied disagree by 1.2 mm on tab span and 1.7 mm on
hole pitch (see lib/servo.py). A 5.6 mm slot along the case's long axis covers
both patterns. A self-tapper in a slot grips two flanks instead of a full
circle - call it half the pull-out of a round pilot, which against 9.4 kg cm
of stall through four screws is still not close.

THE FLANGE GETS ITS OWN RECESS, AND THAT IS THE 2026-08-31 REPAIR. GATE
servo_fit - models/robotarm/_check_servo_fit.py, results in
specs/robotarm/_servo_fit.json - builds the MG995 SOLID from lib/servo.py,
puts it where _check_leads.MOUNTS says it goes and asks pointContainment.
That is the one check in this project that is not a restatement: every assert
in this file compares the pocket with the table the pocket was cut from, so
none of them could ever have found this. It MEASURED 243.0 mm3 of servo inside
this bracket, at host x 28.30, y -8.60..9.40, z -35.95..15.05. Nobody guessed
it and nobody could have argued it away.

WHAT IT IS. The MG995's mounting FLANGE is tab_span 54.0 long against a
case_l 40.9 case - 6.55 mm of tab plate overhanging the case at EACH end -
and it is exactly case_w wide, so the overhang is along the case only. This
pad cut ONE window, sized for the CASE. Read the stack outward: the pad spans
plate_out 19.90 (the case top) to the tab plane at 29.60, and lobe_t is
tab_below_top + tab_thk, so the last tab_thk of it - host x 27.10..29.60 - is
precisely where the flange has to be. The measured band is one sample plane
inside it, the measured y span is case_w and the measured z span is tab_span.
The signature is the flange and nothing else.

SO THE PAD IS CUT IN TWO STEPS. A case window, case_l x case_w, through the
whole pad; then a flange recess, only tab_thk deep from the pad's outer face,
tab_span x case_w. specs/robotarm/_flange.md worked the identical fault out
at J4 first and priced both fixes - this is its Fix A, at J2.

AND THE DATUM INVERTS, WHICH IS THE HONEST COST. lib/servo.py says "THE DATUM
IS THE TAB PLANE, NOT THE CASE - the underside of the tabs, the face a bracket
clamps." This bracket cannot clamp that face and never could: the tab
underside is the face at host x 29.60 and the tab BODY runs INBOARD from it,
into the pad. What the pad clamps now is the tab TOP, on the recess floor at
x 27.10, with the screw head landing on the tab underside flush with the pad's
outer face. The tab is squeezed between head and floor, which is a sound
joint - but it is the other face, and lib/servo.py's sentence needs a second
case. That file is not edited from here.

_check_leads.MOUNTS IS RIGHT AND IS NOT TOUCHED. shaft=(29.6, 0, 0) with
za=('x', -1) is what puts the tab plane on this pad's outer face, and it
agrees with plate_out + lobe_t to the last decimal. The servo does not move;
only the material in front of its flange does.

Print orientation: -X face down, built along +X. Both journal bores come out
vertical and round; they are the only precision fits in the FORK. The disc
then stands on edge, which is wrong for a race face and for the Ø68 journal -
both want to come off the bed flat. If either proves out of round, split this
part on the boss top plane: the disc prints flat, the fork prints on its side,
and they bolt together on the same plane the ring already defines.

The shared wr_* block is defined identically in wrist_hub.py, wrist_roll.py,
forearm.py and upper_arm.py. MG995 dimensions are DATASHEET, not measured.
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

COMPONENT = 'robotarm_shoulder_bracket'
BODY_NAME = 'shoulder_bracket'
PREFIX = 'sb_'
WRIST = 'wr_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_FORM = 'bracket form'
PH_PIVOT = 'pivot journals'
PH_DRIVE = 'servo mount'
PH_BASE = 'turntable interface'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_PIVOT, PH_DRIVE, PH_BASE, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A bracket is structure, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
from lib.servo import SERVO_CASE_CLEARANCE_MM  # noqa: E402
from lib.servo import CATALOG as _SERVOS  # noqa: E402
from lib.servo import MG995_TAB_HOLE_PITCH_Y as _MG995_PITCH_Y  # noqa: E402
from lib.servo import MG995_TAB_SLOT_X_MM as _MG995_SLOT_X  # noqa: E402
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402

# THE J1 DRIVE CONTRACT LIVES IN lib/j1_drive.py since 2026-09-27 (J1 -> MG995).
# It was typed verbatim here, in shoulder_bracket.py and in j1_hub.py; a
# servo swap is the change that finds every copy, so there is one now.
from lib.j1_drive import (  # noqa: E402
    J1_SERVO,
    J1_HUB_OVERSHOOT_MM,
    J1_HUB_SCREW,
    J1_HUB_BOLT_R_MM,
    J1_HUB_BOLT_AZ_DEG,
    J1_HUB_FLOAT_MM,
    J1_HUB_HOLE_D_MM,
    J1_HUB_CBORE_D_MM,
    J1_HUB_CBORE_H_MM,
    J1_HUB_OD_MM,
    J1_HUB_SCREW_BORE_MM,
    J1_HUB_FACE_MM,
    J1_HUB,
)
_J1S = J1_SERVO
_MG995 = _SERVOS['MG995']

# --- THE J1 DRIVE CONTRACT: THE HORN IS OUT OF THE LOAD PATH --------------
# Jonathan, 2026-08-31: "we should not [mount] at the horns but rather add
# gears that we make". J3 went first - commit 0a422e2, models/robotarm/
# j3_pinion.py - and this is J1 following it. J1 had TWO bench failures to
# answer rather than one, and they are the same root cause seen twice:
#   "the actual horn tips dont fit in anywhere"          - the CROSS POCKET
#   "if we put the horn on the base gear the turret       - the SEATING
#    plate does not touch the bearings"                     STACK
# The horn's OUTLINE and the horn's HEIGHT were both load-bearing dimensions
# of a stamped plastic part that varies by batch (deshipu, Roger Cheng).
# Neither is a dimension this project holds any more.
#
# WHY J1 DOES NOT COPY j3_pinion EXACTLY, AND THIS IS THE DECISION.
# j3_pinion bores its gear STRAIGHT onto the spline. J1 does not, and the
# full pricing is in specs/robotarm/j1_hub.md. The three reasons, shortest
# first:
#   1. PRINT ORIENTATION. shoulder_bracket prints -X face down, so its disc
#      stands ON EDGE - its own docstring says so. A broach bore cut into it
#      is an XY-FACING hole, and design_rules is explicit that XY-facing
#      holes come out non-round and want a teardrop. A broach bore has to be
#      ROUND to a fraction of the 0.25 mm interference or it is not a fit at
#      all. j3_pinion could go direct precisely BECAUSE its bore prints
#      vertical, and it says so in its own print-orientation note.
#   2. ASSEMBLY. Broaching is a PRESS stroke. The rotor's height is set by
#      three 608ZZ at r 27 and a ring hooked over its rim; once it is on the
#      turntable there is no press stroke left, and pressing it on first
#      makes the O68 journal impossible to enter afterwards. There is no
#      order in which a direct broach into the rotor can be assembled.
#   3. ITERATION COST. SPLINE_BROACH_INTERFERENCE_MM is ASSUMED, and
#      lib/servo.py says in as many words to print the sweep before
#      committing a gear to it. Committing an ungauged press fit to the
#      largest structural part in the arm costs a whole shoulder-bracket
#      print per iteration. A 3 g hub costs minutes, and it is the piece
#      that should wear out and be replaced anyway.
# So J1 gets a SEPARATE printed hub, broached onto the spline and bolted to
# the rotor with three M3 on a bolt circle. It is a NEW part and NEITHER of
# these two files builds it - see specs/robotarm/j1_hub.md.
#
# WHAT THE BOLT CIRCLE IS WORTH, IN NUMBERS. SG90 stall is 1.6 kg.cm =
# 156.9 N.mm (lib/arm_loads.STALL_KGCM['J1']). Stall, not duty, is the right
# figure for an INTERFACE: a servo driven into a stop delivers it.
#   at the broach bore   r 2.33   F 67.5 N over 4.65 x 2.50 = 11.6 mm2   5.81 MPa
#   at 3 x M3 on r 8.00  F  6.5 N each over 3.0 x 3.7 = 11.1 mm2         0.59 MPa
# A factor of ten, bought with radius. AND THE HONEST HALF OF THAT: it does
# NOT reduce the load on the spline. The broach still carries all 156.9 N.mm
# because the servo has exactly one output. What the bolt circle buys is
# that the 5.81 MPa lives in a 3 g consumable instead of in the arm's
# largest structural part, and that the rotor keeps a FLAT interface with no
# fit on it at all.
#
# 2.50 mm OF SPLINE IS ALL AN SG90 HAS. The MG90S that J3 drives has 4.00.
# spline_hub()'s engage_min is 2.00, so J1 has 0.50 mm of margin and the
# ring's 0.40 mm of axial float eats most of it - asserted, not assumed,
# where the servo is placed.
                               # spline top, so the spline stops short of the
                               # rotor face instead of jacking it off its
                               # rollers. This is the number ts_horn_seat was
                               # trying to be, in a stack where it cannot
                               # cancel out.
                               # to solve, and the face is what we are
                               # solving FOR; this probe is any value past
                               # min_height, used only to read broach_to back
                               # out. Nothing is cut to it.
                               # the ring-lift check below has something to
                               # measure against.
                               # would not survive being taken apart twice.
                               # counterbore must clear the screw bore
                               # (r 3.33 + wall 1.6 + cbore 2.95 = 7.88) and
                               # the hub's own OD must stay inside the
                               # connector gate at r 12.2. 8.0 is the only
                               # half-millimetre that does both.
                               # gate at az 270 - at r 8.0 a head counterbore
                               # reaches r 10.95 and the gate starts at 12.2,
                               # which is 1.25 mm and not a wall. Asserted.
                               # clearance, and it is the whole concentricity
                               # strategy. There is NO register between hub
                               # and rotor: the hub is centred by the SPLINE,
                               # the rotor by its O68 journal in the ring, and
                               # the joint takes up whatever is left between
                               # them when it is tightened. Same move as
                               # lib/servo_hub.py's radial slots and
                               # MG995_TAB_SLOT_X_MM - a slot does not care
                               # exactly where the other part's feature is.
                               # A tight register would have to be a round
                               # bore in a disc that prints on edge, which is
                               # objection 1 above all over again.
# THE ROTOR'S SCREW BORE IS NOT ON THE CRITICAL PATH, and the first pass at
# it was wrong in a way worth recording. It was sized to swallow the SG90's
# retaining WASHER (O6.25) so the washer could clamp the hub's top face -
# but the hub's top face IS the face bolted to the rotor, so a washer there
# is a 1 mm shim between them that the rotor then rides on. The horn failure
# in a different hat, reinvented from scratch in one afternoon.
#
# SO J1 DOES NOT USE THE RETAINING SCREW IN SERVICE, and that is the one
# place J1 deliberately differs from j3_pinion instead of copying it.
# j3_pinion needs that screw and its washer because NOTHING ELSE holds the
# pinion down on the spline; its own docstring says so twice. J1's hub is
# bolted to a rotor that the retainer ring already captures axially, so the
# screw would be a SECOND axial datum fighting the first - which is exactly
# the over-constraint that made the horn hold the turret off its bearings.
# The screw stays an ASSEMBLY AID: run it in with its washer to pull the hub
# down while the broach cuts, then take it out before the hub is bolted up.
# This bore therefore only has to pass that screw's head on the way in and
# stay clear of everything afterwards. Sized by lib/servo_hub.horn_bolt()'s
# own head convention - twice the screw diameter - plus a free fit.
TOL = 1e-9                     # comparison epsilon, not a dimension
# Volume floor for the hub bolt cut, mm3. Three O4.40 through the 9.40 boss
# is 429 and the three head counterbores add ~109, so ~538 is expected. This
# is a PLAYBOOK "the cut did nothing" tripwire, not a dimension.
HUB_BOLT_MIN_DROP_MM3 = 300.0
APPEARANCE_HINTS = hints_for('shoulder_bracket')


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

    def turret(name, expr, comment='', units='mm'):
        _set(TURRET + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    # ---- the SHARED joint contract ------------------------------------------
    # Identical in wrist_hub.py, wrist_roll.py, forearm.py and upper_arm.py.
    wrist('pivot_af', '16.0 mm',
          'hex across flats - the drive between a hub and the block it turns')
    wrist('straddle', '24.0 mm',
          'width a fork straddles - the upper arm is exactly this across')
    wrist('hub_d', '20.0 mm', 'hub journal collar diameter - SHARED, see wrist_hub.py')
    wrist('journal', '5.0 mm', 'collar length = the bore depth it runs in')
    wrist('flange_d', '24.0 mm', 'hub retaining flange diameter')
    wrist('flange_t', '2.0 mm', 'hub retaining flange thickness')
    wrist('reach', '3.8 mm', 'hex boss length past this plate - SHARED, see wrist_hub.py')

    # ---- the SHARED turntable contract --------------------------------------
    # Defined identically here, in turntable_stator.py and turntable_ring.py.
    # Only post_r is MEASURED (off the printed platter); the rest is ours.
    turret('post_r', '45.0 mm',
           'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
           '           top face at its rim, az 120/180/240. The ONLY fixing there is.')
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - DRAWING-CONFIRMED')
    turret('roller_w', '7.0 mm', '608ZZ width. The axle is RADIAL, so this lies radially.')
    turret('roller_r', '27.0 mm', 'roller pitch radius - SHARED, see turntable_stator.py')
    turret('race_margin', '0.5 mm', 'overrun each side of the rollers on the race band')
    turret('axle_z', '13.1 mm',
           'roller axle height. Set so the bearing clears the platter top by 1.0.')
    turret('race_z', TURRET + 'axle_z + ' + TURRET + 'roller_od / 2',
           'derived: where this part\'s underside sits. NEVER type this.')
    turret('disc_d', '76.0 mm',
           'rotor diameter. Not free: the MG995 pad below reaches r 32.1 and the\n'
           '           ring has to hook over the rim outside that.')
    turret('disc_t', '5.0 mm', 'rotor rim thickness, where the ring hooks over it')
    turret('boss_d', '68.0 mm',
           'the raised centre of this disc. This is the JOURNAL - it turns inside\n'
           '           the ring\'s bore, and it is what locates the arm radially.')
    turret('boss_h', '4.4 mm',
           'how far that boss stands above the rim. = ring_lift + ring_t, so the\n'
           '           ring finishes FLUSH with the boss top and the plane the fork\n'
           '           stands on is one continuous face.')
    turret('ring_t', '4.0 mm', 'retainer thickness - SHARED, see turntable_ring.py')
    turret('ring_or', '50.0 mm', 'ring outer radius - it is what the arm pitches down onto')
    turret('ring_lift', '0.40 mm', 'gap between the ring and the rim it holds down')
    # ---- the J1 HUB CONTRACT. THREE files read it, so it lives in tt_. ---
    # turntable_stator places the SG90 from hub_seat_z + hub_h;
    # shoulder_bracket cuts the bolt circle, the counterbores and the screw
    # bore; and robotarm_j1_hub - specs/robotarm/j1_hub.md, not yet built -
    # is the part itself. Every number is DERIVED at the top of this file
    # from lib/servo_hub.spline_hub(SG90) and lib/design_rules, so a change
    # to SPLINE_BROACH_INTERFERENCE_MM moves all three at once. NOTHING here
    # is typed, and nothing here is a horn dimension.
    turret('hub_seat_z', '%.4f mm' % J1_HUB.seat_z,
           'servo-z of the hub UNDERSIDE - one running gap above the SG90 case\n'
           '           top. lib/servo_hub.spline_hub(). NEVER type this.')
    turret('hub_h', '%.4f mm' % J1_HUB_FACE_MM,
           'hub total height, underside to top face. DERIVED: enough to swallow\n'
           '           the whole %.2f of spline reach plus %.2f of overshoot, so the\n'
           '           spline stops SHORT of the rotor instead of lifting it off its\n'
           '           rollers. That lift is what the bench called "the turret plate\n'
           '           does not touch the bearings".'
           % (J1_HUB.broach_to, J1_HUB_OVERSHOOT_MM))
    turret('hub_broach_d', '%.4f mm' % J1_HUB.broach_d,
           'the hub\'s bore - THE STEEL SPLINE CUTS THIS, it is not printed.\n'
           '           20 teeth on O4.9 is 0.77 of pitch and ~0.24 of tooth against a\n'
           '           CALIBRATED MIN_FEATURE_MM of 0.8. Undersize by lib/servo.\n'
           '           SPLINE_BROACH_INTERFERENCE_MM, which is ASSUMED - gauge it.')
    turret('hub_engaged', '%.4f mm' % J1_HUB.engaged,
           'how much spline the bore grips. 2.50 is ALL an SG90 has (the MG90S\n'
           '           has 4.00) and tt_ring_lift takes 0.40 of it when the rotor\n'
           '           floats up. Asserted in turntable_stator.py.')
    turret('hub_od', '%.4f mm' % J1_HUB_OD_MM,
           'hub outer diameter. DERIVED from the bolt circle plus a self-tap\n'
           '           boss and MIN_WALL. Declared HERE and not only in the hub file\n'
           '           because shoulder_bracket has to prove a servo plug coming down\n'
           '           the connector gate does not land on it.')
    turret('hub_bolt_r', '%.4f mm' % J1_HUB_BOLT_R_MM,
           'bolt circle radius. THE WHOLE POINT OF THE SEPARATE HUB: it moves\n'
           '           the drive from r 2.33 at the broach bore to r 8.00, which with\n'
           '           three screws is a tenth of the bearing pressure.')
    turret('hub_bolt_d', '%.4f mm' % J1_HUB_HOLE_D_MM,
           'clearance hole in the ROTOR - M3 clearance plus %.1f of DELIBERATE\n'
           '           radial float. There is no register: the hub is centred by the\n'
           '           spline and the rotor by its journal, and this hole is where the\n'
           '           difference between the two goes.' % J1_HUB_FLOAT_MM)
    turret('hub_cbore_d', '%.4f mm' % J1_HUB_CBORE_D_MM,
           'head counterbore in the BOSS TOP, so the screws finish flush with\n'
           '           the plane the fork stands on and the ring is level with.')
    turret('hub_cbore_h', '%.4f mm' % J1_HUB_CBORE_H_MM,
           'and how deep - an ISO 4762 M3 cap head. DATASHEET.')
    turret('screw_bore', '%.4f mm' % J1_HUB_SCREW_BORE_MM,
           'clearance up the rotor centre, DERIVED now rather than the typed\n'
           '           6.0 it was. It passes the SG90\'s retaining screw head during\n'
           '           the broach step and then has nothing to do: J1 does NOT run\n'
           '           that screw in service - the ring captures the rotor axially\n'
           '           and a second axial datum is what the horn was. It is not a\n'
           '           fit, it carries no torque, and nothing registers in it.')
    turret('hub_washer_d', '%.4f mm' % J1_HUB.washer_d,
           'SMALLEST washer that lands on the hub\'s bore mouth - the retaining\n'
           '           screw is O%.1f with a head near O5 against a O%.2f bore, so\n'
           '           without one the head sits over the hole with nothing to bear\n'
           '           on. Needed only to PULL THE HUB DOWN while the spline broaches\n'
           '           it; both come off before the hub is bolted to this rotor.'
           % (J1_HUB.screw_d, J1_HUB.broach_d))

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'silhouette corner radius - _style.md rule 2')

    # ---- fits ---------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('srv_clear', '%.2f mm' % SERVO_CASE_CLEARANCE_MM,
          'SERVO CASE WINDOW CLEARANCE - lib/servo.py, NOT `loc`.\n'
          '           The window was cut at loc 0.2 TOTAL (0.10 per side) around a\n'
          '           DATASHEET case dimension. GATE servo_fit measured the servo\n'
          '           solid against this host and found real interference; the fix\n'
          '           costs nothing because the TABS locate the servo, not the case.')
    param('rot', '0.35 mm', 'rotating fit - design_rules, both journals here')
    param('free', '0.4 mm', 'free fit - design_rules')

    # ---- the fork, derived exactly as forearm.py derives its own ------------
    param('gap', PREFIX + 'free', 'running gap, plate inner face to the straddled part')
    param('plate_in', WRIST + 'straddle / 2 + ' + PREFIX + 'gap', 'derived plate inner face')
    param('cbore_extra', '0.5 mm',
          'slack behind the hub flange so the hex bottoms in its socket and the\n'
          '           flange never becomes the stop')
    param('cbore_depth', WRIST + 'flange_t + ' + PREFIX + 'cbore_extra', 'derived')
    param('plate_t', WRIST + 'journal + ' + PREFIX + 'cbore_depth', 'derived plate thickness')
    param('plate_out', PREFIX + 'plate_in + ' + PREFIX + 'plate_t', 'derived plate outer face')
    param('bore_d', WRIST + 'hub_d + ' + PREFIX + 'rot', 'derived journal bore')
    param('cbore_d', WRIST + 'flange_d + ' + PREFIX + 'rot', 'derived flange counterbore')
    param('boss_r', PREFIX + 'cbore_d / 2 + ' + PREFIX + 'wall', 'derived pivot boss radius')

    # ---- the column ---------------------------------------------------------
    param('col_y', PREFIX + 'boss_r',
          'derived: the leg is exactly as wide as its own pivot boss, so the two\n'
          '           sides run in tangent to the boss circle and the silhouette is\n'
          '           one round-topped column with no corner to fillet')
    param('stand_h', '38.0 mm',
          'J2 axis above the BOSS TOP - which is the plane the retainer ring is\n'
          '           flush with, so it is also the top of the whole turntable. Boxed\n'
          '           in and asserted both ways: above ~39.6 the servo pad stops\n'
          '           reaching the disc, below ~30.4 the MG995 case fouls the ring.\n'
          '           It also sets the down-pitch limit - see the scan below.')

    # NOT LIGHTENED. The obvious pockets are all in the wrong place: inside the
    # race band is where the fork's load reaches the rollers, outside it is the
    # 4 mm rim the ring hooks over, and the middle is the journal. Spoking the
    # disc is possible and would save maybe 10 g of FILAMENT - it saves no
    # payload at all, because J1's axis is vertical.
    param('cable_ir', '18.0 mm', 'the loom passes through the disc, astern of the arm')
    # THE CONNECTOR GATE. The cable window is 3.4 mm wide radially (18.0 to
    # race_in - wall) and a standard servo plug is ~8.7 x 4.5 in cross-section:
    # the WIRES pass, the PLUGS on their ends do not. Found 2026-08-27. Without
    # this, every lead from a servo mounted after turret assembly (J3, J4, J5,
    # effector) cannot be threaded down to the bay - the arm has to come off
    # its rollers to feed wires. One keyhole at the window's centre azimuth
    # fixes it: plugs pass one at a time, ribbons then lie in the arc.
    #
    # THE GATE USED TO EAT INTO THE HORN-ARM CORRIDOR, and that trade is
    # gone with the horn: the drive now stops at r tt_hub_od/2 and the gate
    # starts well outside it. What the gate still has to miss is the HUB and its
    # bolt heads, and it misses them by AZIMUTH as much as by radius - the
    # head counterbores reach r 10.95 against a gate at 12.2, which is not a
    # wall, so the bolt azimuths are chosen away from 270 and asserted below.
    # The gate still floors at the screw bore.
    param('gate_w', '9.8 mm',
          'connector gate width, tangentially. A servo plug is ~8.7 wide;\n'
          '           +1.1 so it never needs forcing. Stays inboard of the fork'
          ' plates - asserted.')
    param('gate_ir', '12.2 mm',
          'how far in the gate bites. Floor: screw_bore/2 + wall. A plug is\n'
          '           4.5 thick and the gate spans from here to cable_ir - asserted.')
    param('cable_deg', '50.0 deg',
          'arc the cable window sweeps, centred astern at 270 - one of the two\n'
          '           azimuths a fork leg does not occupy (a leg spans -48..+48 about\n'
          '           its own side).', 'deg')

    # ---- MG995, DATASHEET (lib/servo.py) ------------------------------------
    param('case_l', '40.9 mm', 'MG995 case length - runs DOWN along Z, see the\n           docstring. 40.0 -> 40.9 on TowerPro B, 2026-08-27 flange audit')
    param('case_w', '20.2 mm', 'MG995 case width - lies along Y. MEASURED\n           2026-08-28 (was the datasheet 20.0). The gauge bed cut at\n           20.0 + 0.2 loc was line-to-line on the real case - not a fit.')
    param('shaft_end', '10.0 mm', 'shaft axis to the near end of the case, along Z')
    param('tab_thk', '2.5 mm',
          'MG995 tab thickness, and now also the FLANGE RECESS DEPTH. This read\n'
          '           "the pad is this proud, it is the datum" until 2026-08-31, and\n'
          '           that sentence WAS the fault GATE servo_fit measured: the tab\n'
          '           plane is the face at plate_out + lobe_t and the tab BODY runs\n'
          '           inboard of it, so this much material has to be taken AWAY from\n'
          '           the pad face, not left standing proud of it.')
    param('tab_span', '%.2f mm' % _MG995.tab_span,
          'MG995 flange tip to tip, running DOWN along Z with the case. DATASHEET,\n'
          '           read out of lib/servo.py rather than typed here - it is what the\n'
          '           flange recess is cut from. It is tab_span - case_l = 13.1 mm\n'
          '           longer than the case, and every one of those 13.1 mm was landing\n'
          '           on solid pad until the recess below existed.')
    param('tab_below_top', '7.2 mm', 'case top to the tab TOP, along X - DERIVED from\n           TowerPro F 26.8: case_h - F - tab_thk. Was 7.5')
    param('tab_pitch', '47.8 mm',
          'tab hole pitch along the case, drawing B. Drawing A implies 49.5 - hence\n'
          '           slots, see MG995_TAB_SLOT_X_MM in lib/servo.py')
    param('tab_pitch_y', '10.2 mm', 'tab hole pitch across the case - MG995_TAB_HOLE_PITCH_Y')
    param('slot_len', '5.6 mm', 'MG995_TAB_SLOT_X_MM - covers every candidate pitch\n           (derived 47.5, drawing B 47.8, clones 49.5)')
    param('slot_w', '2.5 mm', 'M3 self-tapper into PETG')
    param('slot_depth', '5.0 mm',
          'blind, and MEASURED FROM THE RECESS FLOOR since 2026-08-31, not from\n'
          '           the pad face - the tabs now sit tab_thk down in the recess, so a\n'
          '           pilot started at the face would be a stepped hole with a roof on\n'
          '           it. The self-tap engagement is unchanged at the full 5.0 and so\n'
          '           is the screw length (tab_thk through the tab + this), because the\n'
          '           pilot moved inboard by exactly as much as the bearing face did.\n'
          '           What it must not do is break out of the pad floor into the fork\n'
          '           plate and the straddle: the material under the flange IS\n'
          '           tab_below_top, so the ceiling is tab_below_top - wall = 5.60.\n'
          '           Asserted below, against the floor and not against lobe_t.')
    param('horn_standoff', '0.0 mm',
          'RETIRED 2026-08-28, kept as a named zero so the history is legible.\n           It was 2.0 to stand the MG995 case off plate_out, because a horn\n           hub modelled at O13.8 could not pass behind the 16.0 af hex. The\n           bench says the hub is O8.7 - the obstruction never existed, and\n           the shoulder gets its 2 mm of width back. If a future horn really\n           is fat, raise this rather than thinning the hex.')
    param('lobe_t', PREFIX + 'tab_below_top + ' + PREFIX + 'tab_thk + '
          + PREFIX + 'horn_standoff',
          'derived: tab stack + horn_standoff, so the case top stands exactly\n'
          '           horn_standoff off plate_out and the pad ends ON the tab plane.\n'
          '           It used to finish "and the tabs bear on the pad face". They do\n'
          '           not and they cannot: the tab plane is this face, and the tab\n'
          '           BODY runs tab_thk INBOARD of it, through pad material. That is\n'
          '           the 243.0 mm3 GATE servo_fit measured. The last tab_thk of\n'
          '           lobe_t is now taken back out as sb_flange_l x sb_flange_w, and\n'
          '           what bears on the recess floor is the tab TOP.')
    param('lobe_over', '1.0 mm', 'how far the pad sinks into the leg so the two merge')
    param('flange_l', PREFIX + 'tab_span + ' + PREFIX + 'srv_clear',
          'derived flange recess length along Z: the tab plate plus the same\n'
          '           window clearance the case gets. NOT A FIT and not a locator -\n'
          '           the tab SLOTS locate this servo (lib/servo.py: the datum is the\n'
          '           tab plane, and the holes in it), so this pocket only has to let\n'
          '           the flange down onto its floor.')
    param('flange_w', PREFIX + 'case_w + ' + PREFIX + 'srv_clear',
          'derived flange recess width across Y. The MG995 flange is exactly\n'
          '           case_w wide - it overhangs the case along the case only - so\n'
          '           this comes out equal to the case window width by the SHAPE OF\n'
          '           THIS SERVO, not by construction. A servo whose flange were\n'
          '           wider than its case would move this and not the window, which\n'
          '           is why it is its own parameter and not a reuse.')
    param('lobe_y', PREFIX + 'flange_w / 2 + ' + PREFIX + 'wall',
          'derived pad half width. Was case_w / 2 + wall, which left 1.10 mm of\n'
          '           flank beside a window cut at case_w + srv_clear - under MIN_WALL\n'
          '           1.60, and under it since before srv_clear went from the 0.20\n'
          '           locational fit to lib/servo.py\'s 1.00. Derived from the WINDOW\n'
          '           now, so the flank is MIN_WALL by construction whatever the\n'
          '           clearance does next. Costs 0.50 mm per side; the pad still\n'
          '           reaches only r 32.02 against the r 34.0 journal boss it stands\n'
          '           on - asserted, as it already was.')
    param('lobe_pad', '4.0 mm',
          'material past the end of the outermost tab slot. Was 3.0, and its\n'
          '           FLOOR IS DERIVED rather than chosen: the flange recess ends\n'
          '           flange_l / 2 = 27.50 from the case mid, and sty_radius rounds\n'
          '           the pad\'s top corner away, so the wall left at the RECESS\n'
          '           CORNER is what that fillet leaves and not lobe_hi - recess_hi.\n'
          '           2.72 is where the recess stops breaking daylight through the\n'
          '           fillet; 3.34 keeps sty_ef of skin on it. 4.0 is the round number\n'
          '           above that, and the margin is deliberate because tab_pitch is\n'
          '           DISPUTED (47.5 / 47.8 / 49.5) and lobe_hi is measured off it -\n'
          '           the corner stays clear across the whole disputed range. Both the\n'
          '           end walls and the corner skin are asserted below.')

    # ---- the upper arm, for the down-pitch scan ONLY -------------------------
    param('arm_l1', '125.0 mm',
          'upper arm length - MUST TRACK ua_l1 in upper_arm.py. Was 85.0 and did\n'
          '           NOT track it when ua_l1 moved to 65 on 2026-08-26, because a\n'
          '           comment is not a mechanism. The assertion below is - and it\n'
          '           earned its keep again on 2026-08-29, catching this at 65.0\n'
          '           when ua_l1 had gone to 125. The ledger had reported PASS in\n'
          '           between, because the only run since the change was BATCH 3\n'
          '           and this part sat in the document STALE, matching its own\n'
          '           old volume. A gate that never rebuilt a part is not a gate\n'
          '           that checked it.')
    param('arm_half', '13.0 mm',
          'upper arm half height at its widest (the drum) - MUST TRACK ua_drum_r.\n'
          '           Conservative: the waist is only 12.0.')

    # A COMMENT SAYING "MUST TRACK" IS NOT A MECHANISM. This part carries its
    # own copy of the upper arm's length so the down-pitch scan can run without
    # upper_arm in the document - and the copy silently went stale. The volume
    # ledger cannot catch it either, because the number is a DIAGNOSTIC and
    # moves no geometry. So: when upper_arm IS in the document, check.
    for _shared, _mine in (('ua_l1', 'arm_l1'), ('ua_drum_r', 'arm_half')):
        _p = ups.itemByName(_shared)
        if _p is not None:
            assert abs(_p.value - val(_mine)) < 1e-9, (
                '%s is %.2f mm and this part\'s %s says %.2f - the down-pitch '
                'limit below would be computed for an arm that does not exist'
                % (_shared, _p.value * 10, PREFIX + _mine, val(_mine) * 10))
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
    # RENAME FIRST, THEN DELETE. See fusion/PLAYBOOK.md.
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
    fil = comp.features.filletFeatures

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
            # Without this a CUT eats every other component. See PLAYBOOK.md.
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

    def mm(cm):
        """cm -> a millimetre EXPRESSION. createByString reads a bare number as
        millimetres; val() hands out centimetres. See fusion/PLAYBOOK.md."""
        return '%.4f mm' % (cm * 10.0)

    def yz_circle(name, y_c, z_c, d_cm, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, y_c, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def yz_rect(name, y0, y1, z0, z1, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, 0, y0, z0), mpt(sk, 0, y1, z1))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def xy_circle(name, x_c, y_c, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_c, y_c, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def xy_rect(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0, 0), mpt(sk, x1, y1, 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def xy_arc(name, r_in, r_out, mid_ang, half_ang, z0_expr, dz_expr, op):
        """An annular sector with square ends. Four curves closed by hand -
        Fusion will not infer a sector from two full circles."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        arcs = sk.sketchCurves.sketchArcs
        lines = sk.sketchCurves.sketchLines
        a0, a1 = mid_ang - half_ang, mid_ang + half_ang

        def p(r, a):
            return mpt(sk, r * math.cos(a), r * math.sin(a), 0)

        arcs.addByThreePoints(p(r_out, a0), p(r_out, mid_ang), p(r_out, a1))
        arcs.addByThreePoints(p(r_in, a0), p(r_in, mid_ang), p(r_in, a1))
        lines.addByTwoPoints(p(r_in, a0), p(r_out, a0))
        lines.addByTwoPoints(p(r_in, a1), p(r_out, a1))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def edge_along_x_at(y_c, z_c):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            b = e.boundingBox
            if (abs(b.minPoint.y - b.maxPoint.y) < val('tol')
                    and abs(b.minPoint.z - b.maxPoint.z) < val('tol')
                    and abs(b.minPoint.y - y_c) < val('tol')
                    and abs(b.minPoint.z - z_c) < val('tol')):
                col.add(e)
        return col

    # ---- values in cm --------------------------------------------------------
    stand = val('stand_h')
    disc_t = tval('disc_t')
    disc_r = tval('disc_d') / 2
    journal_r = tval('boss_d') / 2              # the TURNTABLE boss, not the pivot one
    boss_top = -stand                           # the plane the fork stands on
    rim_top = boss_top - tval('boss_h')
    race_z = rim_top - disc_t                   # the race face, and this part's floor
    race_in = tval('roller_r') - tval('roller_w') / 2 - tval('race_margin')
    race_out = tval('roller_r') + tval('roller_w') / 2 + tval('race_margin')
    ring_top = rim_top + tval('ring_lift') + tval('ring_t')
    boss_r = val('boss_r')                      # the PIVOT boss - a different thing
    col_y = val('col_y')
    lobe_t = val('lobe_t')

    # The servo runs DOWN: near end +shaft_end, far end 40 below that.
    case_hi = val('shaft_end')
    case_lo = case_hi - val('case_l')
    case_mid = (case_hi + case_lo) / 2.0
    screw_z = (case_mid - val('tab_pitch') / 2.0, case_mid + val('tab_pitch') / 2.0)
    lobe_lo = min(screw_z) - val('slot_len') / 2.0 - val('lobe_pad')
    lobe_hi = max(screw_z) + val('slot_len') / 2.0 + val('lobe_pad')

    # every corner of the fork and the pad, as a radius from the yaw axis
    leg_r = math.hypot(val('plate_out'), col_y)
    pad_r = math.hypot(val('plate_out') + lobe_t, val('lobe_y'))

    # THE FLANGE RECESS, in the same frame as everything else. The tab plate is
    # centred on the case (tab_overhang is equal at both ends), so the recess is
    # centred on case_mid exactly as the window is - it is only LONGER, and only
    # tab_thk deep instead of the whole lobe_t.
    recess_lo = case_mid - val('flange_l') / 2.0
    recess_hi = case_mid + val('flange_l') / 2.0
    recess_x0 = val('plate_out') + lobe_t - val('tab_thk')   # the recess FLOOR
    pilot_floor = recess_x0 - val('slot_depth')              # deepest the pilots go
    slot_lo = min(screw_z) - val('slot_len') / 2.0
    slot_hi = max(screw_z) + val('slot_len') / 2.0
    slot_y = val('tab_pitch_y') / 2.0 + val('slot_w') / 2.0
    # THE END WALL AT THE RECESS CORNER IS NOT lobe_hi - recess_hi. sty_radius
    # rounds the pad's top corner off along X, so near |y| = flange_w / 2 the
    # material above the recess is whatever the fillet leaves. Measured as the
    # skin between the recess's own corner and that fillet cylinder, whose axis
    # runs along X at (lobe_y - r, lobe_hi - r). The low end has no fillet.
    fil_r = ups.itemByName(STYLE + 'radius').value
    corner_skin = fil_r - math.hypot(val('flange_w') / 2 - (val('lobe_y') - fil_r),
                                     recess_hi - (lobe_hi - fil_r))

    # ---- sanity, before any geometry ----------------------------------------
    # THE MG995 TABLE IS TYPED HERE AND OWNED IN lib/servo.py, and this file
    # already knows what that costs - see the ua_l1 block above, "a comment
    # saying MUST TRACK is not a mechanism". GATE servo_fit found 243 mm3 of
    # flange in this pad because a servo dimension the pad needed (tab_span)
    # was not in this table at all; the least this file can do is prove the
    # ones that ARE in it still say what lib/servo.py says.
    for _pn, _lib_mm in (('case_l', _MG995.case_l), ('case_w', _MG995.case_w),
                         ('shaft_end', _MG995.shaft_from_end),
                         ('tab_thk', _MG995.tab_thk),
                         ('tab_below_top', _MG995.tab_below_top),
                         ('tab_span', _MG995.tab_span),
                         ('tab_pitch', _MG995.tab_hole_pitch),
                         ('tab_pitch_y', _MG995_PITCH_Y),
                         ('slot_len', _MG995_SLOT_X)):
        assert abs(val(_pn) * 10 - _lib_mm) < TOL, (
            'sb_%s is %.3f mm and lib/servo.py MG995 says %.3f - this pad is '
            'cut from a servo that is not in the catalogue any more'
            % (_pn, val(_pn) * 10, _lib_mm))
    assert wval('reach') > val('gap'), 'the hub hex does not reach across the running gap'
    # THE TAB PILOTS START AT THE RECESS FLOOR, so what they must not break
    # through is the material UNDER the flange - which is tab_below_top, and
    # that is not a coincidence: tab_below_top is by definition the case top to
    # the tab top, and the recess floor IS the tab top. The old form of this
    # assert measured against lobe_t, which included the tab_thk the recess has
    # since taken away, so it would have passed a pilot 2.50 mm too deep.
    assert pilot_floor >= val('plate_out') + val('wall') - TOL, (
        'the %.1f mm tab pilots start at the recess floor x %.2f and bottom at '
        '%.2f, leaving %.2f mm of pad floor above plate_out %.2f against a '
        '%.2f wall - they break through into the fork plate and the straddle. '
        'sb_slot_depth must be under %.2f (= tab_below_top - wall).'
        % (val('slot_depth') * 10, recess_x0 * 10, pilot_floor * 10,
           (pilot_floor - val('plate_out')) * 10, val('plate_out') * 10,
           val('wall') * 10, (val('tab_below_top') - val('wall')) * 10))
    # --- the recess must not open the pad's ends, at either end or the corner ---
    assert recess_lo - lobe_lo >= val('wall') - TOL, (
        'the flange recess ends z %.2f and the pad ends z %.2f - %.2f mm of end '
        'wall against MIN_WALL %.2f. Raise sb_lobe_pad.'
        % (recess_lo * 10, lobe_lo * 10, (recess_lo - lobe_lo) * 10, val('wall') * 10))
    assert lobe_hi - recess_hi >= val('wall') - TOL, (
        'the flange recess ends z %.2f and the pad ends z %.2f - %.2f mm of end '
        'wall against MIN_WALL %.2f. Raise sb_lobe_pad.'
        % (recess_hi * 10, lobe_hi * 10, (lobe_hi - recess_hi) * 10, val('wall') * 10))
    assert corner_skin >= ups.itemByName(STYLE + 'ef').value - TOL, (
        'the r %.1f pad fillet leaves only %.2f mm of skin over the flange '
        'recess corner - the recess breaks daylight through the rounded corner '
        'even though the flat end wall reads %.2f. Raise sb_lobe_pad.'
        % (fil_r * 10, corner_skin * 10, (lobe_hi - recess_hi) * 10))
    # --- and it must not invalidate the SLOTS, which exist because the pitch
    # --- is disputed. Every candidate pitch (47.5 derived, 47.8 drawing B,
    # --- 49.5 clones) puts its screw inside a slot cut at sb_tab_pitch, and
    # --- every one of those slots has to open ENTIRELY onto the recess floor.
    # --- A slot mouth half on the floor and half on the pad face is a buried
    # --- void with a tab_thk roof, which is worse than the clash it replaced.
    assert slot_lo >= recess_lo + TOL and slot_hi <= recess_hi - TOL, (
        'the tab slots span z %.2f..%.2f and the flange recess only %.2f..%.2f '
        '- a slot mouth would start partly on the pad face and partly on the '
        'recess floor. sb_tab_pitch has moved without sb_tab_span moving with '
        'it.' % (slot_lo * 10, slot_hi * 10, recess_lo * 10, recess_hi * 10))
    assert slot_y <= val('flange_w') / 2 - TOL, (
        'the tab slots reach |y| %.2f and the flange recess is only %.2f half '
        'wide' % (slot_y * 10, val('flange_w') / 2 * 10))
    # --- the flank beside the window and the recess, which is the same flank ---
    assert val('lobe_y') - val('flange_w') / 2 >= val('wall') - TOL, (
        'only %.2f mm of pad flank beside a %.2f wide window against MIN_WALL '
        '%.2f' % ((val('lobe_y') - val('flange_w') / 2) * 10,
                  val('flange_w') * 10, val('wall') * 10))
    assert val('lobe_y') <= col_y + 1e-9, (
        'the servo pad (%.1f half) is wider than the leg it hangs on (%.1f half)'
        % (val('lobe_y') * 10, col_y * 10))
    # --- the two that box stand_h in ---
    assert lobe_lo < boss_top - 1e-9, (
        'the servo pad stops %.2f below the axis and the boss top is %.2f - the pad '
        'does not reach the disc and is a cantilever again. sb_stand_h must be under '
        '%.2f.' % (-lobe_lo * 10, -boss_top * 10, -lobe_lo * 10))
    assert case_lo >= ring_top + val('free') - 1e-9, (
        'the MG995 case bottom sits at %.2f and the retainer ring reaches %.2f - the '
        'servo would strike the ring as the turret turns under it. sb_stand_h must '
        'be over %.2f.' % (case_lo * 10, ring_top * 10,
                           (tval('boss_h') - tval('ring_lift') - tval('ring_t')
                            + val('free') - case_lo) * 10))
    assert lobe_lo > race_z + 1e-9, 'the servo pad pokes through the race face'
    # --- the ring is flush with the boss top, so the fork must stay inside it ---
    assert abs(ring_top - boss_top) < 1e-9, (
        'tt_boss_h must equal ring_lift + ring_t so the ring finishes flush; the '
        'boss top is %.2f and the ring reaches %.2f'
        % (boss_top * 10, ring_top * 10))
    assert pad_r < journal_r - 1e-9, (
        'the servo pad reaches r %.1f and the journal boss it stands on is only r %.1f'
        % (pad_r * 10, journal_r * 10))
    assert leg_r < journal_r - 1e-9, (
        'a fork leg reaches r %.1f, past the journal boss at r %.1f' % (
            leg_r * 10, journal_r * 10))
    # --- the race band is sacred, and the rim has to be there to be held ---
    assert race_out < journal_r - 1e-9, (
        'the rollers run out to r %.1f, past the journal boss at r %.1f - the race '
        'band would be on the rim, not the boss' % (race_out * 10, journal_r * 10))
    # MILLIMETRES. val()/tval() are CENTIMETRES, so the bare literal goes on the
    # *10 form - written the other way round this fired on a good 4 mm rim.
    rim_mm = (disc_r - journal_r) * 10
    assert rim_mm >= 1.5, (
        'only %.2f mm of rim outside the journal for the ring to hook over' % rim_mm)
    assert val('cable_ir') + val('wall') < race_in, (
        'the cable window runs into the race band')
    # --- the J1 hub, and the three things it has to miss ---
    # It is not built here, so what this part can prove about it is that
    # there is room for it, that its bolt heads land on solid boss top, and
    # that a servo plug coming down the connector gate does not hit it.
    assert tval('hub_od') / 2 < val('gate_ir') - TOL, (
        'the J1 hub is O%.2f, reaching r %.2f, and the connector gate starts '
        'at r %.2f - a servo plug coming down the gate lands on the hub'
        % (tval('hub_od') * 10, tval('hub_od') / 2 * 10, val('gate_ir') * 10))
    assert (tval('hub_bolt_r') - tval('hub_cbore_d') / 2
            >= tval('screw_bore') / 2 + val('wall') - TOL), (
        'only %.2f mm between the O%.2f screw bore and the head counterbores '
        'on r %.2f - MIN_WALL is %.2f'
        % ((tval('hub_bolt_r') - tval('hub_cbore_d') / 2
            - tval('screw_bore') / 2) * 10, tval('screw_bore') * 10,
           tval('hub_bolt_r') * 10, val('wall') * 10))
    assert (tval('hub_bolt_r') + tval('hub_cbore_d') / 2
            < val('plate_in') - TOL), (
        'a head counterbore reaches r %.2f and the fork plates start at |x| '
        '%.2f - a driver could not reach the screw'
        % ((tval('hub_bolt_r') + tval('hub_cbore_d') / 2) * 10,
           val('plate_in') * 10))
    assert tval('hub_cbore_h') <= disc_t + tval('boss_h') - val('wall') - TOL, (
        'a %.2f counterbore in a %.2f boss leaves %.2f of floor for the M3 to '
        'bear on' % (tval('hub_cbore_h') * 10,
                     (disc_t + tval('boss_h')) * 10,
                     (disc_t + tval('boss_h') - tval('hub_cbore_h')) * 10))
    # THE BOLT CIRCLE MISSES THE CONNECTOR GATE BY AZIMUTH, NOT BY RADIUS,
    # and that is exactly the kind of thing this project has got wrong before
    # by looking at a radius and calling it clear. Distance from each head
    # counterbore to the gate RECTANGLE, in millimetres.
    for _i, _az in enumerate(J1_HUB_BOLT_AZ_DEG):
        _a = math.radians(_az)
        _bx = tval('hub_bolt_r') * math.cos(_a) * 10
        _by = tval('hub_bolt_r') * math.sin(_a) * 10
        _dx = max(abs(_bx) - val('gate_w') * 10 / 2, 0.0)
        _dy = max(max(-val('cable_ir') * 10 - _by,
                      _by + val('gate_ir') * 10), 0.0)
        _d = math.hypot(_dx, _dy) - tval('hub_cbore_d') * 10 / 2
        assert _d >= val('wall') * 10 - TOL, (
            'hub bolt %d at az %.0f leaves %.2f mm between its head '
            'counterbore and the connector gate, against a %.2f wall - move '
            'the azimuths, not the radius'
            % (_i, _az, _d, val('wall') * 10))
    # --- the connector gate's own contracts, in MILLIMETRES ---
    _gate_w_mm = val('gate_w') * 10
    _gate_ir_mm = val('gate_ir') * 10
    _gate_span_mm = val('cable_ir') * 10 - _gate_ir_mm
    PLUG_W_MM, PLUG_T_MM = 8.7, 4.5     # standard JR/Futaba servo plug
    assert _gate_w_mm >= PLUG_W_MM + 1.0, (
        'the gate is %.1f wide and a servo plug is %.1f - it would need '
        'forcing' % (_gate_w_mm, PLUG_W_MM))
    assert _gate_span_mm >= PLUG_T_MM + 1.0, (
        'the gate spans %.1f radially and a plug is %.1f thick'
        % (_gate_span_mm, PLUG_T_MM))
    assert _gate_ir_mm >= (tval('screw_bore') / 2 + val('wall')) * 10, (
        'the gate reaches r %.1f, into the hub screw bore wall' % _gate_ir_mm)
    assert _gate_w_mm / 2 + val('wall') * 10 <= val('plate_in') * 10, (
        'the gate is %.1f wide and the fork plates start at |x| %.1f - it '
        'undercuts a leg' % (_gate_w_mm, val('plate_in') * 10))

    # How far the arm can pitch DOWN before it reaches the base it stands on.
    # Scanned, not solved. TWO obstacles now, not one: the disc out to r 48, and
    # the three clips standing clip_top proud of it beyond r 44. The disc is a
    # full circle, so unlike the old rectangular base plate there is no azimuth
    # that buys travel - this is the price of using the printed base.
    def hits_base(theta):
        s, c = math.sin(theta), math.cos(theta)
        d = 0.0
        while d <= val('arm_l1') + 1e-9:
            for t in (-val('arm_half'), 0.0, val('arm_half')):
                y = d * c + t * s
                z = -d * s + t * c
                if abs(y) <= tval('ring_or') and z <= boss_top:
                    return True
            d += 0.05
        return False

    down_deg = 0.0
    while down_deg < 90.0 and not hits_base(math.radians(down_deg + 0.5)):
        down_deg += 0.5
    assert down_deg >= 20.0, (
        'J2 can only pitch %.1f deg below horizontal before the arm reaches the '
        'turntable - raise sb_stand_h' % down_deg)

    def plate(sx):
        if sx > 0:
            return PREFIX + 'plate_in', PREFIX + 'plate_t'
        return '-' + PREFIX + 'plate_out', PREFIX + 'plate_t'

    # ---- phase 1: bracket form ------------------------------------------------
    t0 = design.timeline.count
    # The disc first, so both legs and the pad have something to merge into.
    # Rim then boss, in that order, so the step between them is unambiguous.
    xy_circle('turntable_rim', 0, 0, tval('disc_d'), mm(race_z), TURRET + 'disc_t', NEW)
    xy_circle('journal_boss', 0, 0, tval('boss_d'), mm(race_z),
              mm(disc_t + tval('boss_h')), JOIN)
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        # Column from the race face to the axis, then the boss on top of it.
        # col_y == boss_r, so the sides run in tangent and there is no corner.
        yz_rect('col_' + tag, -col_y, col_y, race_z, 0.0, x0, dx, JOIN)
        yz_circle('boss_' + tag, 0.0, 0.0, 2 * boss_r, x0, dx, JOIN)
    yz_rect('servo_pad', -val('lobe_y'), val('lobe_y'), lobe_lo, lobe_hi,
            PREFIX + 'plate_out - ' + PREFIX + 'lobe_over',
            PREFIX + 'lobe_t + ' + PREFIX + 'lobe_over', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: pivot journals ----------------------------------------------
    t1 = design.timeline.count
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        if sx > 0:
            cb0 = PREFIX + 'plate_out - ' + PREFIX + 'cbore_depth'
        else:
            cb0 = '-' + PREFIX + 'plate_out'
        yz_circle('bore_' + tag, 0.0, 0.0, val('bore_d'), x0, dx, CUT)
        yz_circle('cbore_' + tag, 0.0, 0.0, val('cbore_d'), cb0,
                  PREFIX + 'cbore_depth', CUT)
    group(t1, PH_PIVOT)

    # ---- phase 3: servo mount ---------------------------------------------------
    t2 = design.timeline.count
    yz_rect('case_window',
            -(val('case_w') + val('srv_clear')) / 2,
            (val('case_w') + val('srv_clear')) / 2,
            case_lo - val('srv_clear') / 2, case_hi + val('srv_clear') / 2,
            PREFIX + 'plate_out', PREFIX + 'lobe_t', CUT)
    # THE FLANGE RECESS. The window above is sized for the CASE and goes
    # through the whole pad; this one is sized for the FLANGE and is only
    # tab_thk deep, cut back from the tab plane. Between them they are
    # the two halves of lobe_t: tab_below_top of case, then tab_thk of tab
    # plate that is 13.1 mm longer than the case and was landing on solid pad.
    # GATE servo_fit MEASURED that - 243.0 mm3 at x 28.30, inside the flange
    # band 27.10..29.60, y matching case_w and z matching tab_span. It is not
    # an inference from this file's own numbers; nothing built from those could
    # have found it, which is the entire argument for that gate existing.
    _vol_before_flange = comp.bRepBodies.item(0).volume
    yz_rect('flange_recess',
            -val('flange_w') / 2, val('flange_w') / 2,
            recess_lo, recess_hi,
            PREFIX + 'plate_out + ' + PREFIX + 'lobe_t - ' + PREFIX + 'tab_thk',
            PREFIX + 'tab_thk', CUT)
    # PLAYBOOK: when a CUT changes nothing, the cut is in the wrong place. The
    # window has already taken the middle of this footprint through the whole
    # pad, so what is left to remove is the two ears - (flange_l - case_l -
    # srv_clear) x flange_w x tab_thk, about 694 mm3. Half of that is the
    # tripwire; it is a scale check, not a dimension.
    _flange_drop = (_vol_before_flange - comp.bRepBodies.item(0).volume) * 1000
    _flange_floor = ((val('flange_l') - val('case_l') - val('srv_clear'))
                     * val('flange_w') * val('tab_thk')) * 1000 / 2
    assert _flange_drop > _flange_floor, (
        'the flange recess removed %.1f mm3 against a %.1f floor - wrong place '
        'or wrong scale. It should be taking the two %.2f mm ears the tab plate '
        'overhangs the case window by.'
        % (_flange_drop, _flange_floor,
           (val('flange_l') - val('case_l') - val('srv_clear')) / 2 * 10))
    for i, z_s in enumerate(screw_z):
        for j, y_s in enumerate((-val('tab_pitch_y') / 2, val('tab_pitch_y') / 2)):
            xy = sketch(comp.yZConstructionPlane, 'sk_tab_slot_%d%d' % (i, j))
            r_s = val('slot_w') / 2
            hi_z, lo_z = z_s + val('slot_len') / 2 - r_s, z_s - val('slot_len') / 2 + r_s
            arcs, lines = xy.sketchCurves.sketchArcs, xy.sketchCurves.sketchLines
            arcs.addByThreePoints(mpt(xy, 0, y_s - r_s, hi_z), mpt(xy, 0, y_s, hi_z + r_s),
                                  mpt(xy, 0, y_s + r_s, hi_z))
            arcs.addByThreePoints(mpt(xy, 0, y_s + r_s, lo_z), mpt(xy, 0, y_s, lo_z - r_s),
                                  mpt(xy, 0, y_s - r_s, lo_z))
            lines.addByTwoPoints(mpt(xy, 0, y_s + r_s, hi_z), mpt(xy, 0, y_s + r_s, lo_z))
            lines.addByTwoPoints(mpt(xy, 0, y_s - r_s, hi_z), mpt(xy, 0, y_s - r_s, lo_z))
            # FROM THE RECESS FLOOR, not from the pad face. The tab sits
            # tab_thk down in the recess now, so a pilot started at the face
            # would be a stepped hole with a roof over its bottom half.
            extrude(profiles(xy, expected=1), CUT,
                    PREFIX + 'plate_out + ' + PREFIX + 'lobe_t - '
                    + PREFIX + 'tab_thk - ' + PREFIX + 'slot_depth',
                    PREFIX + 'slot_depth', 'tab_slot_%d%d' % (i, j))
    group(t2, PH_DRIVE)

    # ---- phase 4: turntable interface ---------------------------------------------
    # Everything here is cut from the RACE FACE upward, because that face is the
    # datum the printed base sets and the only one worth measuring from.
    t3 = design.timeline.count
    # THE J1 DRIVE. A flat face, a screw bore and three bolts - and the
    # whole of it is CLEARANCE. Nothing on this disc is cut to a fit any
    # more, which is the point: the horn cross pocket was two measured widths
    # and a depth, all of them the stamped horn's, and all three were wrong
    # on the bench. What is left here is a hole pattern.
    #
    # THE SCREW BORE IS NOT A DRIVE FEATURE AND NOT A FIT. It passes the
    # SG90's retaining screw head while the hub is being broached onto the
    # spline, and after that it does nothing: J1 does NOT run that screw in
    # service - tt_ring_lift's retainer already captures this rotor axially,
    # and a second axial datum is precisely what the horn was. It carries no
    # torque and nothing registers in it. It was tt_screw_bore O6.00 for the
    # horn's hub; it is derived now, and smaller.
    xy_circle('hub_screw_bore', 0, 0, tval('screw_bore'), mm(race_z),
              mm(disc_t + tval('boss_h')), CUT)
    # THE BOLTS RUN DOWNWARD, and that is deliberate. Clearance in this disc,
    # thread in the hub, heads counterbored flush into the BOSS TOP - the
    # plane the fork stands on and the retainer ring finishes level with, at
    # |x| well inside the fork plates, so a driver reaches all three from
    # straight above with the turret fully assembled. Run the other way the
    # screws would only be reachable from under the base plate, which means
    # taking the turret off to touch the drive.
    _vol_before_bolts = comp.bRepBodies.item(0).volume
    for _i, _az in enumerate(J1_HUB_BOLT_AZ_DEG):
        _a = math.radians(_az)
        _bx = tval('hub_bolt_r') * math.cos(_a)
        _by = tval('hub_bolt_r') * math.sin(_a)
        xy_circle('hub_bolt_%d' % _i, _bx, _by, tval('hub_bolt_d'),
                  mm(race_z), mm(disc_t + tval('boss_h')), CUT)
        xy_circle('hub_cbore_%d' % _i, _bx, _by, tval('hub_cbore_d'),
                  mm(boss_top - tval('hub_cbore_h')), TURRET + 'hub_cbore_h',
                  CUT)
    # PLAYBOOK: when a CUT changes nothing, the cut is in the wrong place.
    _bolt_drop = (_vol_before_bolts - comp.bRepBodies.item(0).volume) * 1000
    assert _bolt_drop > HUB_BOLT_MIN_DROP_MM3, (
        'the three hub bolts and their counterbores removed %.1f mm3 against '
        'a %.1f floor - wrong place or wrong scale'
        % (_bolt_drop, HUB_BOLT_MIN_DROP_MM3))
    # The loom, astern of the arm at 270 deg - one of the two azimuths a leg
    # does not occupy.
    xy_arc('cable_window', val('cable_ir'), race_in - val('wall'),
           -math.pi / 2, val('cable_deg') / 2, mm(race_z),
           mm(disc_t + tval('boss_h')), CUT)
    # The connector gate: a keyhole merging with the window's inner edge at
    # its centre azimuth. See the gate_w/gate_ir comments for why it exists
    # and what it now has to miss, which is the hub and its bolt heads.
    _vol_before_gate = comp.bRepBodies.item(0).volume
    xy_rect('connector_gate', -val('gate_w') / 2, val('gate_w') / 2,
            -val('cable_ir'), -val('gate_ir'), mm(race_z),
            mm(disc_t + tval('boss_h')), CUT)
    _gate_drop = (_vol_before_gate - comp.bRepBodies.item(0).volume) * 1000
    # PLAYBOOK: when a CUT changes nothing, the cut is in the wrong place.
    assert _gate_drop > 100.0, (
        'the connector gate removed %.1f mm3 - a 9.8 x 5.8 through-cut '
        'should take ~500; wrong place or wrong scale' % _gate_drop)
    group(t3, PH_BASE)

    # ---- phase 5: finish -------------------------------------------------------------
    t4 = design.timeline.count
    col = adsk.core.ObjectCollection.create()
    for y_c in (-val('lobe_y'), val('lobe_y')):
        for e in edge_along_x_at(y_c, lobe_hi):
            col.add(e)
    n_filleted = col.count
    if col.count:
        f_inp = fil.createInput()
        f_inp.addConstantRadiusEdgeSet(col, V(STYLE + 'radius'), True)
        fil.add(f_inp).name = 'pad_corners'
    group(t4, PH_FINISH)

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a leg or the pad is not reaching the disc'
        % comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used_appearance = 'none'
    for want_a in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want_a):
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
    print('fork: plates |x| %.1f..%.1f (%.1f thick), bore %.2f, cbore %.2f x %.1f, '
          'boss r %.2f' % (val('plate_in') * 10, val('plate_out') * 10,
                           val('plate_t') * 10, val('bore_d') * 10,
                           val('cbore_d') * 10, val('cbore_depth') * 10, boss_r * 10))
    print('column: %.1f wide x %.1f tall from the boss top to the axis' % (
        col_y * 20, stand * 10))
    print('TURNTABLE ROTOR (this part IS J1\'s rotating half):')
    print('  race face z %.2f | rim %.1f dia x %.2f to z %.2f | journal boss %.1f '
          'dia, %.2f proud, top z %.2f' % (
              race_z * 10, tval('disc_d') * 10, disc_t * 10, rim_top * 10,
              tval('boss_d') * 10, tval('boss_h') * 10, boss_top * 10))
    print('  race band r %.1f..%.1f, rollers at r %.1f - LEFT FLAT, never pocketed' % (
        race_in * 10, race_out * 10, tval('roller_r') * 10))
    print('  ring laps the rim from r %.1f and finishes FLUSH with the boss top' % (
        (tval('boss_d') / 2 + 0.0175) * 10))
    print('  J1 DRIVE, NO HORN: flat face + %d x M3 clearance O%.2f on r %.2f '
          'at az %s' % (len(J1_HUB_BOLT_AZ_DEG), tval('hub_bolt_d') * 10,
                        tval('hub_bolt_r') * 10, J1_HUB_BOLT_AZ_DEG))
    print('    heads O%.2f x %.2f counterbored FLUSH into the boss top; screw '
          'bore O%.2f is clearance only, no torque'
          % (tval('hub_cbore_d') * 10, tval('hub_cbore_h') * 10,
             tval('screw_bore') * 10))
    print('    the hub itself (O%.2f, broach O%.2f over %.2f of spline) is a '
          'SEPARATE part - specs/robotarm/j1_hub.md, built by neither host'
          % (tval('hub_od') * 10, tval('hub_broach_d') * 10,
             tval('hub_engaged') * 10))
    print('    holes are M3 clearance + %.2f of DELIBERATE float: no register, '
          'the spline centres the hub and this joint takes up the difference'
          % (tval('hub_bolt_d') * 10 - _FASTENER[J1_HUB_SCREW]['clearance']))
    print('CLEARANCES:')
    print('  servo pad reaches r %.1f, fork legs r %.1f, journal boss is r %.1f' % (
        pad_r * 10, leg_r * 10, journal_r * 10))
    print('  MG995 case bottom z %.2f vs ring top z %.2f -> %.2f mm of daylight' % (
        case_lo * 10, ring_top * 10, (case_lo - ring_top) * 10))
    print('  servo pad ends z %.2f, %.2f mm inside the boss top' % (
        lobe_lo * 10, (boss_top - lobe_lo) * 10))
    print('MG995 runs DOWN: case z %.1f..%.1f, tab slots z %.1f / %.1f (%.1f long x '
          '%.1f), pad z %.1f..%.1f x %.1f thick' % (
              case_lo * 10, case_hi * 10, screw_z[0] * 10, screw_z[1] * 10,
              val('slot_len') * 10, val('slot_w') * 10,
              lobe_lo * 10, lobe_hi * 10, lobe_t * 10))
    print('  FLANGE RECESS %.1f x %.1f x %.2f deep from the pad face (z %.2f..%.2f, '
          'x %.2f..%.2f): the tab plate is %.1f mm longer than the case and all of '
          'it used to land on solid pad - GATE servo_fit MEASURED 243.0 mm3 there'
          % (val('flange_l') * 10, val('flange_w') * 10, val('tab_thk') * 10,
             recess_lo * 10, recess_hi * 10, recess_x0 * 10,
             (val('plate_out') + lobe_t) * 10,
             (val('tab_span') - val('case_l')) * 10))
    print('    end walls %.2f / %.2f, skin over the corner under the r%.1f pad '
          'fillet %.2f, flank beside the window %.2f (MIN_WALL %.2f)'
          % ((recess_lo - lobe_lo) * 10, (lobe_hi - recess_hi) * 10,
             fil_r * 10, corner_skin * 10,
             (val('lobe_y') - val('flange_w') / 2) * 10, val('wall') * 10))
    print('    tab pilots start at the RECESS FLOOR x %.2f, bottom at %.2f, %.2f '
          'above plate_out - engagement is still the full %.1f and the screw is '
          'still %.1f long' % (recess_x0 * 10, pilot_floor * 10,
                               (pilot_floor - val('plate_out')) * 10,
                               val('slot_depth') * 10,
                               (val('tab_thk') + val('slot_depth')) * 10))
    print('    slots z %.2f..%.2f sit %.2f / %.2f inside the recess ends, so every '
          'disputed pitch (47.5 / 47.8 / 49.5) lands on its floor'
          % (slot_lo * 10, slot_hi * 10, (slot_lo - recess_lo) * 10,
             (recess_hi - slot_hi) * 10))
    print('    the pad clamps the tab TOP on that floor, not the tab underside - '
          'see the docstring, lib/servo.py\'s datum sentence needs a second case')
    print('J2 DOWN-PITCH LIMIT: %.1f deg before the arm reaches the turntable '
          '(arm %.0f long, %.1f half height, ring r %.1f)' % (
              down_deg, val('arm_l1') * 10, val('arm_half') * 10,
              tval('ring_or') * 10))
    print('CONNECTOR GATE: %.1f x %.1f keyhole at az 270, r %.1f..%.1f - servo'
          % (val('gate_w') * 10, val('cable_ir') * 10 - val('gate_ir') * 10,
             val('gate_ir') * 10, val('cable_ir') * 10))
    print('  plugs (~8.7 x 4.5) pass here; the 3.4 window takes only wires.')
    print('J1 TRAVEL: nothing here caps rotation (the ring hooks over the rim). '
          'J1 is an MG995 360 deg since 2026-09-27 - the LOOM caps it: +-180 deg '
          'from the hall home sensor, in firmware (specs/robotarm/base_platter.md)')
    print('filleted %d pad corners at r %.1f' % (
        n_filleted, ups.itemByName(STYLE + 'radius').value * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 1000 * 0.6, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
