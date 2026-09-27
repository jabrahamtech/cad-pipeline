"""robotarm/turntable_stator - Fusion MCP generating script.

2026-09-27 - J1 IS AN MG995 360 deg NOW, NOT AN SG90. Wherever the prose
below says SG90, read "the J1 servo": the numbers come from lib/j1_drive.py
and lib/servo.MG995. What changed in THIS part: the rollers moved to az
30/150/270 so the 40.9 mm case passes between them; the pad is 24 x 55 and
carries all FOUR tab screws (the one-screw problem below is gone); the lead
groove is not needed; the loom window moved to az 210 and is plug-sized.
The platter is no longer the printed legacy one - specs/robotarm/base_platter.md.

Rebuilds `robotarm_turntable_stator` (idempotent). Spec:
specs/robotarm/base_platter_measured.md.

J1's FIXED half. Bolts to the printed platter, holds the yaw servo, and
carries the three 608ZZ rollers the shoulder disc rides on.

Local frame: origin ON THE J1 YAW AXIS at the PLATTER'S RIM TOP - platter
z 42.00, measured, not assumed. +Z up. Everything in this part and in
turntable_ring is in this frame; the shoulder bracket's rotor meets it at
tt_race_z.

WHAT THIS REPLACES. The legacy turret was a 12 mm solid Ø104 plate, three M8
axle bolts with nylocs, three separate hold-down clips and three more heat-set
inserts in the cap's rim - eleven fasteners and four printed parts to carry a
300 g arm. This does the same three jobs with three screws:

  weight down   3 x 608ZZ on RADIAL axles, rolling, as before
  radial        the rotor's Ø68 boss turns inside the ring's bore - one
                big-diameter plain journal instead of nothing at all
  uplift        the ring hooks over the rotor's rim

and ONE M3 per post runs the whole stack - through the ring, down the post,
into the platter's insert. Take those three out and the turret lifts off.
Nothing caps rotation, so J1 gets the servo's full 180 deg.

NO HORN. THE SG90 DRIVES A BOLTED HUB. Until 2026-08-31 this part stood the
servo off so a stamped four-arm horn reached up into a cross pocket in the
rotor. The bench reported that twice and both readings were right: "the
actual horn tips dont fit in anywhere" (the pocket was cut to a modelled arm
width that no real arm has) and "if we put the horn on the base gear the
turret plate does not touch the bearings" (the horn held the rotor off its
own rollers). The second is the interesting one, because it was ARITHMETIC
rather than tolerance - tt_horn_z cancelled out of the deck derivation, so
the seating gap was 0.00 for every value of it, and the 0.40 mm ts_horn_seat
added in August was the entire clearance against a ring that gives 0.40 mm
of float. See the deck derivation below, which now has no such term because
NOTHING ON THE SERVO REACHES THE ROTOR AT ALL.

What drives J1 now is a separate printed hub, broached onto the SG90's own
spline and bolted to the rotor with three M3 on an r 8.00 circle. This file
does not build it - specs/robotarm/j1_hub.md does - and this file's only
share of it is WHERE THE SERVO SITS, which is one subtraction from the race
face. The reasoning for a bolted hub rather than j3_pinion's direct broach
is at the top of the code, with the torque arithmetic.

THE AXLES ARE RADIAL, and that is not a detail. The rotor's underside moves
TANGENTIALLY over each roller, so the roller's axis has to be perpendicular to
that - radial - or the bearing scrubs sideways instead of rolling and wears a
flat on its outer race. The legacy design got this right and said so; it is
repeated here because it is the one thing about a roller turntable that looks
equally plausible either way.

THE RACE COLLAR IS THE OTHER ONE. Each stub axle stands 0.5 mm proud where the
bearing seats, so the M3 and washer clamp the INNER race only. Without it the
outer race touches the cheek and the roller stops rolling and starts rubbing.

Print orientation: FLAT, base down, cheeks and posts up. The stub axles then
grow sideways off the cheeks as horizontal cylinders - the one real overhang
in the part, and short enough (Ø7.9 over 8.5 mm) to bridge. Print it axles-up
instead and the bearing seat gets a seam down its side.
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


COMPONENT = 'robotarm_turntable_stator'
BODY_NAME = 'turntable_stator'
PREFIX = 'ts_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_FORM = 'stator form'
PH_ROLLERS = 'rollers'
PH_SERVO = 'yaw servo'
PH_FIX = 'platter interface'
PH_HOME = 'home sensor'
PHASES = [PH_FORM, PH_ROLLERS, PH_SERVO, PH_FIX, PH_HOME]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. The base is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
from lib.servo import SERVO_CASE_CLEARANCE_MM  # noqa: E402

# THE J1 DRIVE CONTRACT LIVES IN lib/j1_drive.py since 2026-09-27 (J1 -> MG995).
# It was typed verbatim here, in shoulder_bracket.py and in j1_hub.py; a
# servo swap is the change that finds every copy, so there is one now.
from lib.j1_drive import (  # noqa: E402
    J1_SERVO,
    J1_HUB_OVERSHOOT_MM,
    J1_HUB_ENGAGE_MIN_MM,
    J1_HUB_BOLT_R_MM,
    J1_HUB_FLOAT_MM,
    J1_HUB_HOLE_D_MM,
    J1_HUB_CBORE_D_MM,
    J1_HUB_CBORE_H_MM,
    J1_HUB_OD_MM,
    J1_HUB_SCREW_BORE_MM,
    J1_HUB_FACE_MM,
    J1_HUB,
    J1_BOSS_TOP_MM,
    J1_SPLINE_TOP_MM,
)
_J1S = J1_SERVO
from lib.servo import MG995_TAB_HOLE_PITCH_Y as _MG995_PY  # noqa: E402
from lib.j1_drive import (  # noqa: E402
    TT_AXLE_Z_MM, TT_ROLLER_OD_MM, J1_DECK_Z_MM,
    HOME_R_MM, HOME_AZ_DEG, MAGNET_D_MM, MAGNET_H_MM, HALL_GAP_MM,
    MAGNET_PROTRUDE_MM, LOOM_AZ_DEG, LOOM_IR_MM, LOOM_OR_MM, LOOM_DEG,
    HALL_BODY_W_MM, HALL_BODY_H_MM, HALL_BODY_T_MM, HALL_LEAD_PITCH_MM,
    HALL_LEAD_N, HALL_SLOT_MM,
)
from lib.servo import SERVO_SCREW_PILOT_MM as _MICRO_PILOT  # noqa: E402
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
_TAB_PITCH_Y = _MG995_PY if _J1S.name == 'MG995' else 0.0
_TAB_PILOT_MM = (_FASTENER['M3']['pilot']
                 if _J1S.tab_hole_dia >= _FASTENER['M3']['clearance']
                 else _MICRO_PILOT)

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
SAMPLE_ALONG = 9               # clearance sampling density - counts, not dimensions
SAMPLE_AROUND = 24
# AZIMUTHS, degrees. Module-level so they are one edit point and not literals
# in run(). POSTS are fixed by turntable_ring's holes. ROLLERS moved 2026-09-27
# from 90/210/330 so the MG995 case (along +Y, az 90) passes between them -
# see run(). The lightening windows are GONE: az 210 is the loom window, az
# 330 carries the J1 HOME SENSOR post (lib/j1_drive.HOME_*), and az 90 is
# the servo. Nothing is left that carries nothing.
ROLL_AZ = (30.0, 150.0, 270.0)
POST_AZ = (120.0, 180.0, 240.0)
APPEARANCE_HINTS = hints_for('turntable_stator')


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

    # ---- the SHARED turntable contract --------------------------------------
    # Defined identically here, in turntable_ring.py and shoulder_bracket.py.
    # The first two entries are MEASURED off the printed platter and are the
    # only things in this whole assembly that are not ours to choose.
    turret('post_r', '45.0 mm',
           'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
           '           top face at its rim, az 120/180/240. The ONLY fixing there is.')
    turret('bolt_d', '3.4 mm',
           'M3 clearance. One screw per post runs the whole stack - through the\n'
           '           ring, down the post, into the platter insert. About 40 long.')
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - DRAWING-CONFIRMED')
    turret('roller_w', '7.0 mm', '608ZZ width. The axle is RADIAL, so this lies radially.')
    turret('roller_r', '27.0 mm',
           'roller pitch radius. Boxed in: the servo hub reaches r 21 inside it and\n'
           '           the mounting posts sit at r 45 outside, and the cheeks have to\n'
           '           fit between the two.')
    turret('axle_z', '13.1 mm',
           'roller axle height. = ts_relief_floor + ts_relief_clear + roller_od/2,\n'
           '           so a 608 sitting on its axle clears a MIN_WALL floor of base\n'
           '           plate with ts_relief_clear of daylight. WAS 12.0, set to clear\n'
           '           the PLATTER top at z 0 - which ignored this part\'s OWN 4.0 mm\n'
           '           base plate sitting on it. The bearing bottomed at z 1.00 inside\n'
           '           a plate spanning z 0..4 and could not be fitted at all.\n'
           '           _check_j1 found it 2026-08-26; asserted below now.')
    turret('race_z', TURRET + 'axle_z + ' + TURRET + 'roller_od / 2',
           'derived: where the rotor\'s underside sits. NEVER type this.')
    turret('disc_d', '76.0 mm',
           'rotor diameter. Not free: the MG995 pad on the shoulder bracket reaches\n'
           '           r 32.1, and the ring has to hook over the rim outside that.')
    turret('disc_t', '5.0 mm', 'rotor rim thickness, where the ring hooks over it')
    turret('boss_d', '68.0 mm',
           'the rotor\'s raised centre. This is the JOURNAL - it turns inside the\n'
           '           ring\'s bore, and it is what locates the arm radially. A big\n'
           '           diameter running slowly is the one plain bearing that is\n'
           '           genuinely better than a rolling one here.')
    turret('boss_h', '4.4 mm',
           'how far that boss stands above the rim. = ring_lift + ring_t, so the\n'
           '           ring finishes FLUSH with the boss top and the plane the fork\n'
           '           stands on is one continuous face. WAS 4.0 HERE and 4.4 in\n'
           '           shoulder_bracket.py - one shared parameter with two values,\n'
           '           which only ever worked because the bracket happens to build\n'
           '           last. Found by _check_j1 2026-08-26.')
    turret('ring_t', '4.0 mm',
           'retainer thickness. NOT 3.0: an M3 head counterbore is 2.4 and design\n'
           '           _rules wants a wall under it, so 4.0 is the floor if the screws\n'
           '           are to finish flush.')
    turret('ring_or', '50.0 mm', 'ring outer radius - has to cover the posts at r 45')
    turret('ring_lift', '0.40 mm', 'gap between the ring and the rotor rim it holds down')
    turret('collar_h', '0.5 mm',
           'how far the bearing seat stands proud of its cheek. Small, but it is the\n'
           '           only thing keeping the OUTER race off the cheek - without it\n'
           '           the roller does not roll, it rubs.')
    turret('axle_d', '7.9 mm', '608 bore 8.0 - 0.1, a press')
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
    style('radius', '6.0 mm', 'silhouette corner radius - SHARED, do not retune it here')

    # ---- THE J1 SERVO, from lib/servo.py via lib/joints.JOINT_SERVO -----------
    # 2026-09-27: an MG995 360 deg (continuous) - Jonathan: "same as the other
    # big motor", so every number is lib/servo.MG995's. These are NOT typed:
    # the SG90 block that stood here was a hand copy the loop further down
    # had to police. Written from the library, the loop still runs and now
    # guards against someone typing over them.
    param('case_l', '%.2f mm' % _J1S.case_l, '%s case length - lies along Y here' % _J1S.name)
    param('case_w', '%.2f mm' % _J1S.case_w, '%s case width - lies along X' % _J1S.name)
    param('case_h', '%.2f mm' % _J1S.case_h, '%s case height' % _J1S.name)
    param('tab_thk', '%.2f mm' % _J1S.tab_thk, '%s tab thickness' % _J1S.name)
    param('tab_below_top', '%.2f mm' % _J1S.tab_below_top, 'case top to the TOP of the tabs')
    param('tab_pitch', '%.2f mm' % _J1S.tab_hole_pitch,
          '%s tab hole pitch ALONG the case. MG995 vendor drawings disagree\n'
          '           (47.5 / 47.8 / 49.5); the O4.8 tab hole takes an M3 with 0.9 of\n'
          '           radial slack either way, which covers all three.' % _J1S.name)
    param('tab_pitch_y', '%.2f mm' % _TAB_PITCH_Y,
          'hole pitch ACROSS the case - an MG995 tab carries TWO holes\n'
          '           (lib/servo.MG995_TAB_HOLE_PITCH_Y); 0 for a one-hole micro tab.')
    # THE OUTPUT SHAFT IS NOT IN THE MIDDLE OF THE CASE, and this part used to
    # assume it was. lib/servo.py has carried shaft_from_end = 6.1 since the
    # library was written and, until 2026-08-26, servo_adapter.py was the ONLY
    # file that read it. Centring the CASE on J1 puts the SHAFT 5.2 mm off the
    # axis - the drive would then turn shoulder_bracket about a point 5.2 mm
    # off its own journal, which orbits and binds instead of turning. That was
    # true of the horn and it is just as true of the spline hub: the hub is
    # centred by the SPLINE, so an off-axis spline is an off-axis hub bolted
    # to an on-axis rotor, and the bolt float would spend itself taking it up.
    # shoulder_bracket got this right for the MG995 (case z -30..10, shaft at
    # 0) and forearm got it right for both MG90S. This part did not.
    param('shaft_from_end', '%.2f mm' % _J1S.shaft_from_end,
          '%s shaft axis to the NEAR end of the case - lib/servo.py' % _J1S.name)
    param('shaft_off', PREFIX + 'case_l / 2 - ' + PREFIX + 'shaft_from_end',
          'derived: how far the CASE CENTRE must sit from the J1 axis so the\n'
          '           SHAFT lands on it. Everything servo-related below is offset\n'
          '           by this in +Y, which also moves the case away from the cable\n'
          '           window at az 270 rather than into it.')
    param('tab_span', '%.2f mm' % _J1S.tab_span, '%s tab tip to tip' % _J1S.name)
    param('boss_h', '%.2f mm' % _J1S.boss_h, '%s output collar above the case top' % _J1S.name)
    param('pilot_d', '%.2f mm' % _TAB_PILOT_MM,
          'tab screw pilot, self-tapping into PETG. A micro servo\'s O2.1 tab\n'
          '           hole takes its own 2 mm screw (SERVO_SCREW_PILOT_MM 1.8); the\n'
          '           MG995\'s O4.8 hole takes an M3 (FASTENER_MM pilot).')
    param('pilot_depth', '4.0 mm', 'into the servo pad')

    # ---- fits and local geometry --------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('srv_clear', '%.2f mm' % SERVO_CASE_CLEARANCE_MM,
          'SERVO CASE WINDOW CLEARANCE - lib/servo.py, NOT `loc`.\n'
          '           The window was cut at loc 0.2 TOTAL (0.10 per side) around a\n'
          '           DATASHEET case dimension. GATE servo_fit measured the servo\n'
          '           solid against this host and found real interference; the fix\n'
          '           costs nothing because the TABS locate the servo, not the case.')
    param('free', '0.4 mm', 'free fit - design_rules')
    param('plate_t', '4.0 mm', 'base plate thickness')
    param('lead_key_d', '%.2f mm' % (_J1S.lead_bundle_dia + 0.2),
          'lead keyway WIDTH across the case width, centred on the bundle.\n'
          '           The servo cannot be INSERTED without it: the cable crosses the\n'
          '           whole aperture on the way down.')
    param('lead_groove_w', '5.0 mm',
          'lead groove width in the plate underside - same Ø-5 convention as\n'
          '           every other lead escape in the project')
    param('lead_groove_d', '1.2 mm',
          'lead groove depth up into the plate underside. The bundle leaves at\n'
          '           z -1.0 with its top edge at +0.7, and the plate is 0..4.0, so on\n'
          '           its way out it grazes 0.7 into the plate. _check_leads measured\n'
          '           exactly that - 2.20 mm3, 3 %% of the escape - after the keyway\n'
          '           was moved to the -Y end. This is the same groove that used to\n'
          '           relieve the +Y end, re-sited to the end the lead actually uses.')
    param('lead_escape', '8.0 mm',
          'how far the lead must run clear before bending - MUST MATCH\n'
          '           _check_leads.ESCAPE_MM. The lead_groove_* pair that used to sit\n'
          '           here went with the datum correction of 2026-08-28: the groove\n'
          '           relieved the case\'s FAR (+Y) end, and the bundle leaves the -Y\n'
          '           end, where at z -1.0 it is already clear under the plate.')
    param('plate_ir', '10.0 mm', 'base plate inner radius - the servo comes through here')
    param('plate_or', '50.0 mm', 'base plate outer radius - out to the ring')
    # THE LOOM HAD NO WAY THROUGH THIS PART. The servo well is 12.40 x 22.90
    # against an SG90 case of 12.20 x 22.70 - one tenth of a millimetre each
    # side, which is a clearance fit for the servo and nothing at all for
    # fifteen wires. Five servos live above J1 (J2 MG995, J3 and J4 MG90S,
    # J5 SG90, effector SG90) and every one of their leads has to cross here.
    # shoulder_bracket already cuts a matching window in the rotor at
    # sb_cable_ir 18.0, 50 deg, astern at az 270; this is the fixed half of
    # that route and base_lid carries the same slot underneath.
    # 2026-09-27: MOVED FROM az 270 TO az 210. The MG995's near tab and its
    # pad now cover az 270 out to r 21, and the rollers moved to 30/150/270
    # to let the 40.9 mm case through (see ROLL_AZ). az 210 is the one sector
    # with no roller, no post and no servo - the old lightening window's
    # place - and it is BIG: a servo plug (8.7 x 4.5) now passes through it,
    # which the 7 mm slot at r 13.7-20 never allowed.
    # REVISION 2026-09-27: 210 -> 330 (lib/j1_drive.LOOM_AZ_DEG). az 330 is
    # the same kind of sector - no roller, post or servo - but it sits right
    # over the ESP32 bay in base_platter, so the loom drops onto the board
    # instead of crossing under the MG995. The home post took az 210.
    param('cable_az', '%.2f deg' % LOOM_AZ_DEG, 'lib/j1_drive.LOOM_AZ_DEG - over the ESP32\n'
                                   '           bay, between the az-270 and az-30 rollers', 'deg')
    param('cable_ir', '%.2f mm' % LOOM_IR_MM,
          'inner radius - outside the servo pad\'s near corner (r 21.0 at az\n'
          '           234) by a wall. Asserted by sampling, not by a radius.')
    param('cable_or', '%.2f mm' % LOOM_OR_MM,
          'outer radius. NOT out to the posts: the home magnet sweeps r 31.5..37.5\n'
          '           under the rotor, and a loom bundled wider than this would be\n'
          '           brushed by it every revolution. Still 145 mm2, plug-sized.')
    param('cable_deg', '%.2f deg' % LOOM_DEG, 'arc swept, 190..230. Clears the roller reliefs\n'
                                   '           (to 176 and from 244) and the pad corner.\n'
                                   '           Chord at r 26 is 17.8 - an 8.7 plug passes flat', 'deg')
    param('post_d', '11.0 mm', 'mounting post diameter - 3.8 of wall round an M3 clearance')
    param('relief_floor', '1.6 mm',
          'what is LEFT of the base plate under each roller - design_rules\n'
          '           MIN_WALL_MM exactly, and it is the floor that sets tt_axle_z.')
    param('relief_clear', '0.5 mm',
          'daylight between the bearing and that floor. Not a fit - nothing\n'
          '           bears here; it is there so a stringy first layer cannot touch\n'
          '           the roller and add drag to a joint with no torque to spare.')
    param('relief_margin', '1.0 mm',
          'how far the relief overruns the bearing footprint, radially and\n'
          '           tangentially. The relief stops AT cheek_ir, so the cheeks keep\n'
          '           their full footing and only the plate between them is cut.')
    param('cheek_t', '4.0 mm', 'roller cheek thickness, radially')
    param('cheek_w', '18.0 mm', 'roller cheek width, tangentially')
    param('cheek_over', '6.0 mm', 'material above the axle centre')
    param('race_od', '12.0 mm', '608ZZ INNER race outer diameter - lib/bearings.py')
    param('collar_d', '11.0 mm',
          'the bearing seat. The ONLY surface it may touch is the inner race\n'
          '           FACE - an annulus from the 8.0 bore to the 12.0 race OD. Wider\n'
          '           than 12.0 and it reaches over the gap toward the ZZ shield,\n'
          '           which is fixed to the OUTER race; touch that and the roller\n'
          '           drags instead of rolling. 11.0 leaves 1.5 mm of contact and\n'
          '           1.0 mm of margin. It was 12.5, which overhung the race.')
    param('washer_od', '11.0 mm',
          'the retainer, and it is a PRINTED part - see roller_cap on the gauge.\n'
          '           A standard M3 washer is Ø7 and falls straight THROUGH the\n'
          '           608\'s Ø8 bore, clamping nothing. The alternatives are all\n'
          '           bought (M3 penny, M4 flat); printing it costs 0.4 g, needs no\n'
          '           order, and obeys the same Ø8..Ø12 rule as the seat.')
    param('axle_len', '8.0 mm',
          'stub length past the collar. Bearing is 7.0, so 1.0 stands proud for the\n'
          '           washer - which must land on the race, never on the axle end.')
    param('axle_pilot', '2.5 mm', 'M3 self-tapper up the middle of the stub')
    param('axle_screw_z', '7.0 mm', 'how deep that pilot goes')
    param('hub_x', PREFIX + 'case_w / 2 + ' + PREFIX + 'srv_clear / 2 + ' + PREFIX + 'wall',
          'servo pad half width - the case window plus ONE wall. For the MG995\n'
          '           that is 12.2, and it is what keeps the az-30/150 roller reliefs\n'
          '           off the pad (their corners reach x 12.45).')
    param('hub_y', PREFIX + 'tab_span / 2 + 0.5 mm',
          'servo pad half length, centred on the CASE (shaft_off): the tabs plus\n'
          '           0.5. SQUARE ends now - the SG90 pad was rounded because its far\n'
          '           corner sat under the az-90 roller, and there is no roller there.')
    # DEFINED HERE, not with the other lead params: it reads hub_y, and
    # Fusion rejects an expression naming a parameter that does not exist
    # yet. Order is part of the contract.
    param('lead_key_l', PREFIX + 'hub_y - (' + PREFIX + 'case_l + ' + PREFIX
          + 'loc) / 2 + 1.0 mm',
          'keyway length OUT from the shaft-end face. DERIVED to clear the\n'
          '           servo pad plus 1.0 of overshoot - a keyway that stops inside the\n'
          '           pad is a blind pocket and traps the cable. Never hardcode it.')
    # ---- J1 HOME SENSOR POST - lib/j1_drive.HOME_*, 2026-09-27 ----------------
    # An A3144 hall sensor lies FLAT in a pocket on top of a post, branded
    # (sensing) face UP, and a 5x2 magnet in a pocket under the rotor at the same
    # radius passes over it once a revolution. The leads bend down a slot
    # through the post and the plate into the base - the sensor's cable route.
    param('home_r', '%.2f mm' % HOME_R_MM, 'lib/j1_drive.HOME_R_MM - CHOSEN')
    param('home_az', '%.2f deg' % HOME_AZ_DEG, 'lib/j1_drive.HOME_AZ_DEG - CHOSEN', 'deg')
    param('magnet_d', '%.2f mm' % MAGNET_D_MM, '5 x 2 N52 disc, in shoulder_bracket\'s pocket')
    param('magnet_h', '%.2f mm' % MAGNET_H_MM, 'its thickness')
    param('magnet_protrude', '%.2f mm' % MAGNET_PROTRUDE_MM,
          'how far it hangs below the race face: thickness minus the locating\n'
          '           pocket shoulder_bracket cuts for it (lib/j1_drive)')
    param('hall_gap', '%.2f mm' % HALL_GAP_MM, 'magnet face to sensor face - ASSUMED, lib/j1_drive')
    param('hall_w', '%.2f mm' % HALL_BODY_W_MM, 'A3144 TO-92UA body width - DATASHEET')
    param('hall_h', '%.2f mm' % HALL_BODY_H_MM, 'body height, leads out of this edge - DATASHEET')
    param('hall_t', '%.2f mm' % HALL_BODY_T_MM, 'body thickness = pocket depth, face flush - DATASHEET')
    param('hall_lead_w', '%.2f mm' % ((HALL_LEAD_N - 1) * HALL_LEAD_PITCH_MM + 1.0),
          'lead fan width - 3 leads on 1.27 plus a wire each side')
    param('hall_slot', '%.2f mm' % HALL_SLOT_MM, 'lead slot depth, the way the leads fold down - lib, ASSUMED')
    param('hall_post_d', '12.0 mm',
          'post diameter: the pocket and the lead slot plus MIN_WALL round both')
    param('hall_top', TURRET + 'race_z - ' + PREFIX + 'magnet_protrude - ' + PREFIX + 'hall_gap',
          'post top = sensor face. DERIVED from the race face, so the gap holds\n'
          '           if the rollers ever move. NEVER type it.')
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

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = 'sk_' + name
        return sk

    def one(sk, expected=1):
        assert sk.profiles.count == expected, (
            sk.name + ': expected %d, got %d' % (expected, sk.profiles.count))
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

    def mm(cm):
        """cm -> a millimetre EXPRESSION. createByString reads a bare number as
        millimetres; val() hands out centimetres. See fusion/PLAYBOOK.md."""
        return '%.4f mm' % (cm * 10.0)

    def mxy(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def xy_circle(name, x, y, d, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, x, y), d / 2)
        return extrude(one(sk), op, z0, dz, name)

    def xy_rect(name, x0, x1, y0, y1, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(mxy(sk, x0, y0), mxy(sk, x1, y1))
        return extrude(one(sk), op, z0, dz, name)

    def xy_ring(name, r_out, r_in, z0, dz, op):
        """Two concentric circles give TWO profiles - the inner disc and the
        annulus. Picking by index is a coin toss, so pick by area."""
        sk = sketch(comp.xYConstructionPlane, name)
        for r in (r_out, r_in):
            sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, 0, 0), r)
        assert sk.profiles.count == 2, sk.name + ': got %d profiles' % sk.profiles.count
        want = math.pi * (r_out ** 2 - r_in ** 2)
        c = adsk.core.ObjectCollection.create()
        for i in range(2):
            p = sk.profiles.item(i)
            if abs(p.areaProperties().area - want) < want * 1e-6:
                c.add(p)
        assert c.count == 1, sk.name + ': no profile matched the annulus'
        return extrude(c, op, z0, dz, name)

    def xy_arc(name, r_in, r_out, mid, half, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        arcs, lines = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines
        a0, a1 = mid - half, mid + half

        def p(r, a):
            return mxy(sk, r * math.cos(a), r * math.sin(a))

        arcs.addByThreePoints(p(r_out, a0), p(r_out, mid), p(r_out, a1))
        arcs.addByThreePoints(p(r_in, a0), p(r_in, mid), p(r_in, a1))
        lines.addByTwoPoints(p(r_in, a0), p(r_out, a0))
        lines.addByTwoPoints(p(r_in, a1), p(r_out, a1))
        return extrude(one(sk), op, z0, dz, name)

    def radial_cyl(name, az, r_a, r_b, d, op):
        """A cylinder on a RADIAL horizontal axis at azimuth `az`, running from
        radius r_a to r_b at height tt_axle_z.

        The plane is the YZ plane (normal +X) turned about Z by az, so its
        normal IS the outward radial direction - which makes the extrude
        distance a signed radial length and nothing else. r_b < r_a therefore
        just means 'inward', with no rotation matrix to get backwards.
        """
        pl_in = comp.constructionPlanes.createInput()
        pl_in.setByAngle(comp.zConstructionAxis,
                         adsk.core.ValueInput.createByReal(az),
                         comp.yZConstructionPlane)
        pl = comp.constructionPlanes.add(pl_in)
        pl.name = 'pl_' + name
        sk = comp.sketches.add(pl)
        sk.name = 'sk_' + name
        # (0, 0, axle_z) lies ON that plane whatever az is, so this cannot pick
        # up an out-of-plane component that the sketch would silently drop.
        c = sk.modelToSketchSpace(P3(0.0, 0.0, tval('axle_z')))
        sk.sketchCurves.sketchCircles.addByCenterRadius(c, d / 2)
        return extrude(one(sk), op, mm(r_a), mm(r_b - r_a), name)

    # ---- values in cm --------------------------------------------------------
    plate_t = val('plate_t')
    race_z = tval('race_z')
    roll_r = tval('roller_r')
    seat_r = roll_r + tval('roller_w') / 2            # collar face
    cheek_ir = seat_r + tval('collar_h')              # cheek inner face
    cheek_or = cheek_ir + val('cheek_t')
    stub_ir = cheek_ir - tval('collar_h') - val('axle_len')
    ring_under = race_z + tval('disc_t') + tval('ring_lift')
    post_top = ring_under
    # ---- WHERE THE SERVO SITS, NOW THAT NOTHING REACHES THE ROTOR ------
    # THE OLD STACK, AND WHY IT COULD NOT WORK AT ANY VALUE. The servo used
    # to be placed so a horn fitted to its spline reached UP into a cross
    # pocket in the rotor's underside:
    #     deck_z   = race_z + horn_z - horn_seat - K
    #     horn_top = deck_z + K = race_z + horn_z
    # and race_z + horn_z IS the pocket ceiling, so horn_z cancelled and the
    # seating gap was EXACTLY ZERO for every value of it. Raising the pocket
    # 1.8 -> 2.4 in August therefore changed nothing but the servo's height.
    # ts_horn_seat 0.4, added 2026-08-30 to break the cancellation, bought
    # 0.40 mm of seating - on a rotor whose retainer ring already gives away
    # 0.40 mm of float. That is "the turret plate does not touch the
    # bearings", and it was arithmetic rather than tolerance.
    #
    # THE NEW STACK HAS NO SUCH TERM, because the servo no longer touches
    # the rotor anywhere. The J1 hub bolts FLAT to the rotor's underside and
    # hangs BELOW it; the spline slides up into the hub's broach bore and
    # stops J1_HUB_OVERSHOOT_MM short of the rotor face. The rotor's height
    # is set by three 608ZZ and by nothing else, which is what a turntable
    # is for. Read downward from the race face:
    #     race face      tt_race_z            the ROLLERS set it
    #     hub top        = race face          bolted, face to face
    #     hub underside  - tt_hub_h
    #     SG90 case top  - tt_hub_seat_z      a running gap over the boss
    # One subtraction, and there is nothing in it that can cancel with
    # anything else. If this ever needs a seating gap again, something has
    # gone back to touching the rotor and that is the bug, not the gap.
    deck_z = race_z - tval('hub_h') - tval('hub_seat_z')
    spline_top_z = deck_z + J1_SPLINE_TOP_MM / 10
    boss_top_z = deck_z + J1_BOSS_TOP_MM / 10
    hub_bottom_z = race_z - tval('hub_h')

    # THE LEAD GROOVE TRACKS THE DECK, because the deck keeps moving and the
    # groove was a typed 1.2. Derived here, where deck_z is finally known,
    # from the same bundle top edge the assert further down tests - so the
    # number and its check cannot drift apart. It has earned its keep
    # twice: deepening the old horn pocket raised this servo 1.0 and the
    # seating gap lowered it 0.4, and dropping the horn altogether has now
    # lowered it 3.0 more. A typed 1.2 would have been wrong every time.
    _sg0 = _J1S
    _cb0 = (deck_z * 10) - (_sg0.case_h - _sg0.tab_below_top - _sg0.tab_thk)
    _need_groove = _cb0 + _sg0.lead_bundle_dia * 1.5
    param('lead_groove_d', '%.4f mm' % max(1.2, _need_groove + 0.2),
          'DERIVED from the deck, not typed: deep enough for the bundle\'s TOP\n'
          '           EDGE where the servo actually sits, plus 0.2. Was 1.2, which was\n'
          '           right for a deck that has since moved twice.')
    case_bottom = deck_z - (val('case_h') - val('tab_below_top') - val('tab_thk'))
    cheek_top = tval('axle_z') + val('cheek_over')
    # the relief footprint: the bearing's own shadow plus relief_margin, and
    # never past cheek_ir, which is where the cheeks stand.
    relief_ir = roll_r - tval('roller_w') / 2 - val('relief_margin')
    relief_half = math.asin(
        (tval('roller_od') / 2 + val('relief_margin')) / roll_r)
    # THE PAD IS NOT CENTRED, so its reach is not hypot(half_x, half_y). That
    # is what this was, and it reported r 21.02 for a pad that reached 25.82.
    # With the end rounded to hub_x the furthest point is on the axis, so the
    # reach is simply the far edge - but the assertion below is written against
    # the CORNER too, because a future un-rounding must not pass silently.
    # 2026-09-27, J1 -> MG995. ROLLERS 90/210/330 -> 30/150/270. The MG995
    # case runs 30.9 mm out along +Y (az 90) and its tab to 37.45, straight
    # through the old az-90 roller. Rotating the servo instead would have
    # meant rotated rectangles in every servo feature below; rotating three
    # rollers is one tuple. The POSTS DO NOT MOVE - turntable_ring's screw
    # holes stay where they are - and every clearance this creates or
    # destroys is sampled, not argued, in _clear() below.
    case_top = deck_z + val('tab_thk') + val('tab_below_top')

    # ---- sampled clearance, in cm -------------------------------------------
    # The SG90 pad was small enough that "the pad reaches r X, the stub starts
    # at r Y" was an honest check. A 55 x 24 pad next to three rollers is not
    # a radius, so these sample the real solids against the real boxes.
    def _box_d(px, py, pz, box):
        (x0, x1), (y0, y1), (z0, z1) = box
        dx = max(x0 - px, 0.0, px - x1)
        dy = max(y0 - py, 0.0, py - y1)
        dz = max(z0 - pz, 0.0, pz - z1)
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    _soff0 = val('shaft_off')
    PAD_BOX = ((-val('hub_x'), val('hub_x')),
               (_soff0 - val('hub_y'), _soff0 + val('hub_y')),
               (plate_t, deck_z))
    CASE_BOX = ((-val('case_w') / 2, val('case_w') / 2),
                (_soff0 - val('case_l') / 2, _soff0 + val('case_l') / 2),
                (deck_z - (val('case_h') - val('tab_below_top') - val('tab_thk')),
                 case_top))
    TAB_BOX = ((-val('case_w') / 2, val('case_w') / 2),
               (_soff0 - val('tab_span') / 2, _soff0 + val('tab_span') / 2),
               (deck_z, deck_z + val('tab_thk')))
    SERVO_BOXES = (('pad', PAD_BOX), ('case', CASE_BOX), ('tabs', TAB_BOX))

    def _roller_points(az_deg):
        """Surface samples of one roller station: the 608 and its stub."""
        a = math.radians(az_deg)
        c, s_ = math.cos(a), math.sin(a)
        pts = []
        spans = ((roll_r - tval('roller_w') / 2, roll_r + tval('roller_w') / 2,
                  tval('roller_od') / 2),
                 (stub_ir, cheek_ir, val('collar_d') / 2))
        for r0, r1, rad in spans:
            for k in range(SAMPLE_ALONG):
                rr = r0 + (r1 - r0) * k / (SAMPLE_ALONG - 1)
                for m in range(SAMPLE_AROUND):
                    th = 2 * math.pi * m / SAMPLE_AROUND
                    t, dz = rad * math.cos(th), rad * math.sin(th)
                    pts.append((rr * c - t * s_, rr * s_ + t * c,
                                tval('axle_z') + dz))
        return pts

    def _arc_points(r_in, r_out, mid, half):
        """XY boundary samples of an annular sector (angles in radians)."""
        pts = []
        for k in range(SAMPLE_AROUND + 1):
            a = mid - half + 2 * half * k / SAMPLE_AROUND
            for rr in (r_in, r_out):
                pts.append((rr * math.cos(a), rr * math.sin(a)))
        for k in range(SAMPLE_ALONG):
            rr = r_in + (r_out - r_in) * k / (SAMPLE_ALONG - 1)
            for a in (mid - half, mid + half):
                pts.append((rr * math.cos(a), rr * math.sin(a)))
        return pts

    def _xy_gap(pts, box):
        return min(_box_d(x, y, box[2][0], (box[0], box[1], box[2]))
                   for x, y in pts)

    # ---- sanity, before any geometry ----------------------------------------
    # lib/j1_drive carries these two for base_platter, which is not built in
    # this document. Two copies of one number are only safe when checked.
    assert abs(tval('axle_z') * 10 - TT_AXLE_Z_MM) < TOL * 10 + 1e-6, (
        'tt_axle_z %.2f disagrees with lib/j1_drive.TT_AXLE_Z_MM %.2f'
        % (tval('axle_z') * 10, TT_AXLE_Z_MM))
    assert abs(tval('roller_od') * 10 - TT_ROLLER_OD_MM) < TOL * 10 + 1e-6, (
        'tt_roller_od disagrees with lib/j1_drive.TT_ROLLER_OD_MM')
    assert abs(race_z - (tval('axle_z') + tval('roller_od') / 2)) < 1e-9, (
        'tt_race_z is meant to be derived from the axle height and the 608 OD')
    # THE BEARING RUNS OVER THIS PART'S OWN BASE PLATE, not over the platter.
    # This compared the roller against z 0 and called it "the lid", and so never
    # saw the 4.0 mm plate in between. Three 608 were 3.00 mm inside it.
    _roll_bottom = tval('axle_z') - tval('roller_od') / 2
    assert _roll_bottom >= val('relief_floor') + val('relief_clear') - 1e-9, (
        'the rollers reach z %.2f and the relieved plate floor is z %.2f with '
        '%.2f of daylight wanted - raise tt_axle_z to at least %.2f'
        % (_roll_bottom * 10, val('relief_floor') * 10, val('relief_clear') * 10,
           (val('relief_floor') + val('relief_clear')
            + tval('roller_od') / 2) * 10))
    assert val('relief_floor') >= val('wall') - 1e-9, (
        'the relief leaves %.2f of plate under each roller against a %.2f '
        'minimum wall' % (val('relief_floor') * 10, val('wall') * 10))
    assert cheek_top < race_z - val('free') - 1e-9, (
        'the roller cheeks reach z %.2f and the rotor rides at %.2f - only the '
        'BEARING may touch it' % (cheek_top * 10, race_z * 10))
    for _az in ROLL_AZ:
        _pts = _roller_points(_az)
        for _nm, _bx in SERVO_BOXES:
            _g = min(_box_d(x, y, z, _bx) for x, y, z in _pts)
            assert _g >= val('free') - TOL, (
                'the az-%.0f roller station comes within %.2f mm of the servo %s '
                '(free fit %.2f wanted)' % (_az, _g * 10, _nm, val('free') * 10))
    assert cheek_or < tval('post_r') - val('post_d') / 2 - val('wall'), (
        'the roller cheeks reach r %.2f and the posts start at r %.2f'
        % (cheek_or * 10, (tval('post_r') - val('post_d') / 2) * 10))
    assert cheek_or < tval('disc_d') / 2, (
        'the cheeks are outboard of the rotor they carry')
    assert tval('post_r') - val('post_d') / 2 > tval('disc_d') / 2 + val('free'), (
        'the mounting posts at r %.2f foul the rotor at r %.2f' % (
            (tval('post_r') - val('post_d') / 2) * 10, tval('disc_d') / 2 * 10))
    assert val('collar_d') < val('race_od') - 1e-9, (
        'the %.1f collar is wider than the %.1f inner race, so it lands on the ZZ '
        'shield and the bearing drags instead of rolling'
        % (val('collar_d') * 10, val('race_od') * 10))
    assert val('collar_d') > tval('axle_d') + 2 * 0.1, (
        'the collar barely clears the axle - there is nothing for the race to sit on')
    assert tval('axle_d') < val('washer_od') < val('race_od') - 1e-9, (
        'the retaining washer must be wider than the %.1f bore and narrower than '
        'the %.1f inner race; %.1f is not'
        % (tval('axle_d') * 10, val('race_od') * 10, val('washer_od') * 10))
    # THIS FILE RETYPES THE SG90 AND THE HUB STACK WAS SOLVED FROM THE
    # LIBRARY. Two copies of one servo is how the deck ends up derived from
    # numbers no other part agrees with, so they are checked rather than
    # trusted. ts_tab_span had no reader at all before this - a parameter
    # nothing reads is an edit point that does nothing.
    for _name, _lib_mm in (('case_l', _J1S.case_l), ('case_w', _J1S.case_w),
                           ('case_h', _J1S.case_h), ('tab_thk', _J1S.tab_thk),
                           ('tab_below_top', _J1S.tab_below_top),
                           ('tab_pitch', _J1S.tab_hole_pitch),
                           ('tab_span', _J1S.tab_span),
                           ('boss_h', _J1S.boss_h),
                           ('shaft_from_end', _J1S.shaft_from_end)):
        assert abs(val(_name) * 10 - _lib_mm) < val('tol') * 10, (
            'ts_%s says %.2f and lib/servo.py SG90 says %.2f - this file '
            'retypes the servo, and the hub stack that positions it was '
            'solved from the library copy'
            % (_name, val(_name) * 10, _lib_mm))

    assert abs(deck_z * 10 - J1_DECK_Z_MM) < 1e-6, (
        'the stator puts the J1 tab underside at z %.3f and lib/j1_drive says '
        '%.3f - base_platter keeps out of the lib number' % (deck_z * 10, J1_DECK_Z_MM))
    # NOTHING ON THE SERVO MAY TOUCH THE ROTOR, and this is the assertion
    # the horn stack never had. The old one compared the horn top against
    # the POCKET CEILING, which moved with it, so it could only ever be
    # satisfied by construction. This compares the spline top against the
    # RACE FACE, which the rollers set and which the servo cannot move.
    assert race_z - spline_top_z >= J1_HUB_OVERSHOOT_MM / 10 - TOL, (
        'the SG90 spline tops out at z %.2f and the rotor race face is at '
        '%.2f - %.2f mm apart, and %.2f is wanted. The servo would carry the '
        'arm instead of the rollers, which is exactly what the horn did'
        % (spline_top_z * 10, race_z * 10, (race_z - spline_top_z) * 10,
           J1_HUB_OVERSHOOT_MM))
    # AND THE BORE MUST STILL GRIP THE SPLINE WITH THE RING FULLY LIFTED.
    # tt_ring_lift is 0.40 mm of deliberate axial float in the retainer. The
    # rotor may sit that high; the hub bolted to it rises with it, sliding UP
    # the spline and losing that much engagement off the BOTTOM. An SG90 has
    # 2.50 mm of spline in total - the MG90S that J3 drives has 4.00 - so the
    # float comes off a number with nothing spare, and it is checked here
    # rather than in lib, which does not know about the ring.
    _engaged_lifted = tval('hub_engaged') * 10 - tval('ring_lift') * 10
    assert _engaged_lifted >= J1_HUB_ENGAGE_MIN_MM - TOL, (
        'the hub grips %.2f mm of spline and tt_ring_lift lets the rotor rise '
        '%.2f, leaving %.2f against a %.2f minimum. Deepen nothing - either '
        'take float out of the ring or accept that an SG90 has 2.50 mm of '
        'spline and no more' % (tval('hub_engaged') * 10, tval('ring_lift') * 10,
                                _engaged_lifted, J1_HUB_ENGAGE_MIN_MM))
    # THE HUB HANGS IN THE GAP BETWEEN THIS PART AND THE ROTOR. It is not
    # built here and it is not built by shoulder_bracket either, so the one
    # thing this file can prove about it is that there is room.
    assert hub_bottom_z >= deck_z + val('free') - TOL, (
        'the J1 hub\'s underside sits at z %.2f and this part\'s servo pad '
        'tops out at %.2f - the hub would run on the pad'
        % (hub_bottom_z * 10, deck_z * 10))
    assert boss_top_z > deck_z + TOL, (
        'the SG90 output collar tops out at z %.2f, at or below its own '
        'mounting deck at %.2f' % (boss_top_z * 10, deck_z * 10))
    assert val('axle_len') > tval('roller_w'), (
        'the stub is shorter than the bearing - the washer would clamp the axle end')
    assert deck_z > plate_t + 1e-9, (
        'the servo deck at z %.2f is inside the base plate' % (deck_z * 10))
    _relief_ir0 = roll_r - tval('roller_w') / 2 - val('relief_margin')
    _relief_half0 = math.asin((tval('roller_od') / 2 + val('relief_margin')) / roll_r)
    for _nm, _az, _half, _ir, _or in (
            [('loom window', val('cable_az') * 180 / math.pi, val('cable_deg') / 2,
              val('cable_ir'), val('cable_or'))]):
        _pts = _arc_points(_ir, _or, math.radians(_az), _half)
        _g = _xy_gap(_pts, PAD_BOX)
        assert _g >= val('wall') - TOL, (
            'the %s at az %.0f comes within %.2f mm of the servo pad'
            % (_nm, _az, _g * 10))
        for _raz in ROLL_AZ:
            _d = abs((math.radians(_az) - math.radians(_raz) + math.pi)
                     % (2 * math.pi) - math.pi)
            _sep = (_d - _half - _relief_half0) * _relief_ir0
            assert _sep >= val('wall') - TOL, (
                'the %s at az %.0f leaves %.2f mm to the az-%.0f roller relief'
                % (_nm, _az, _sep * 10, _raz))
        assert _or < tval('post_r') - val('post_d') / 2 - val('wall'), (
            'the %s runs into the mounting posts' % _nm)
    # THE HOME MAGNET SWEEPS A FULL CIRCLE under the rotor, so everything
    # it passes is checked against the annulus, not against one azimuth.
    _m_in = val('home_r') - val('magnet_d') / 2
    _m_out = val('home_r') + val('magnet_d') / 2
    assert _m_in >= roll_r + tval('roller_w') / 2 + val('free') - TOL, (
        'the home magnet sweeps in to r %.2f over 608s reaching r %.2f'
        % (_m_in * 10, (roll_r + tval('roller_w') / 2) * 10))
    assert _m_out <= tval('disc_d') / 2 - TOL, (
        'the home magnet overhangs the rotor rim (r %.2f > %.2f)'
        % (_m_out * 10, tval('disc_d') / 2 * 10))
    assert _m_in >= val('cable_or') + val('wall') - TOL, (
        'the loom window reaches r %.2f and the magnet sweeps from r %.2f - it '
        'would brush the loom every revolution' % (val('cable_or') * 10, _m_in * 10))
    assert val('hall_gap') >= val('free') - TOL, 'the magnet would strike the sensor'
    # A BRACKET PRINTED BEFORE THE POCKET EXISTED takes the magnet glued
    # FLAT, so it hangs the full thickness. The gap must survive that too.
    _flat_gap = val('hall_gap') - (val('magnet_h') - val('magnet_protrude'))
    assert _flat_gap >= val('free') - TOL, (
        'glued flat on an un-pocketed rotor the magnet clears the sensor by '
        'only %.2f' % (_flat_gap * 10))
    _post_half = math.asin(val('hall_post_d') / 2 / val('home_r'))
    for _raz in ROLL_AZ:
        _d = abs((val('home_az') - math.radians(_raz) + math.pi) % (2 * math.pi) - math.pi)
        _cheek_half = math.atan(val('cheek_w') / 2 / cheek_ir)
        _sep = (_d - _post_half - _cheek_half) * cheek_ir
        assert _sep >= val('wall') - TOL, (
            'the home post at az %.0f leaves %.2f mm to the az-%.0f cheek'
            % (math.degrees(val('home_az')), _sep * 10, _raz))
    for _paz in POST_AZ:
        _px = tval('post_r') * math.cos(math.radians(_paz))
        _py2 = tval('post_r') * math.sin(math.radians(_paz))
        _hx = val('home_r') * math.cos(val('home_az'))
        _hy = val('home_r') * math.sin(val('home_az'))
        assert math.hypot(_px - _hx, _py2 - _hy) >= (
            (val('post_d') + val('hall_post_d')) / 2 + val('wall') - TOL), (
            'the home post runs into the az-%.0f mounting post' % _paz)
    _pts = _arc_points(val('home_r') - val('hall_post_d') / 2,
                       val('home_r') + val('hall_post_d') / 2, val('home_az'), _post_half)
    assert _xy_gap(_pts, PAD_BOX) >= val('wall') - TOL, 'the home post hits the servo pad'
    # THE RELIEFS MAY NOT BITE THE PAD. They cut z relief_floor..plate_t+1,
    # which overlaps the pad's foot, so they must miss it in XY outright.
    for _raz in ROLL_AZ:
        _pts = _arc_points(_relief_ir0, cheek_ir, math.radians(_raz), _relief_half0)
        _g = _xy_gap(_pts, PAD_BOX)
        assert _g > TOL, ('the az-%.0f roller relief cuts into the servo pad'
                          % _raz)

    # ---- phase 1: stator form -------------------------------------------------
    t0 = design.timeline.count
    xy_ring('base_plate', val('plate_or'), val('plate_ir'), '0.0 mm',
            PREFIX + 'plate_t', NEW)
    # The servo pad: a raised slab the tabs bear on, standing on the plate.
    # Its OUTBOARD end is a semicircle of radius hub_x, not a square corner.
    # With the +5.20 shaft offset a square corner reaches r 25.82, inside the
    # roller band at r 23.50, and the relief cut below would undercut the very
    # pad it stands on. Rounded, the furthest point is on the axis at r 21.60.
    _soff = val('shaft_off')
    xy_rect('servo_pad', -val('hub_x'), val('hub_x'),
            _soff - val('hub_y'), _soff + val('hub_y'),
            mm(plate_t - 0.1), mm(deck_z - plate_t + 0.1), JOIN)
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        xy_circle('post_%d' % i, tval('post_r') * math.cos(a),
                  tval('post_r') * math.sin(a), val('post_d'),
                  '0.0 mm', mm(post_top), JOIN)
    for i, az in enumerate(ROLL_AZ):
        a = math.radians(az)
        # the cheek: a tangential slab standing outboard of its roller
        sk = sketch(comp.xYConstructionPlane, 'cheek_%d' % i)
        pts = []
        for rr, tt in ((cheek_ir, -val('cheek_w') / 2), (cheek_or, -val('cheek_w') / 2),
                       (cheek_or, val('cheek_w') / 2), (cheek_ir, val('cheek_w') / 2)):
            pts.append((rr * math.cos(a) - tt * math.sin(a),
                        rr * math.sin(a) + tt * math.cos(a)))
        lines = sk.sketchCurves.sketchLines
        for k in range(4):
            lines.addByTwoPoints(mxy(sk, pts[k][0], pts[k][1]),
                                 mxy(sk, pts[(k + 1) % 4][0], pts[(k + 1) % 4][1]))
        extrude(one(sk), JOIN, '0.0 mm', mm(cheek_top), 'cheek_%d' % i)
    group(t0, PH_FORM)

    # ---- phase 2: rollers ------------------------------------------------------
    t1 = design.timeline.count
    for i, az in enumerate(ROLL_AZ):
        a = math.radians(az)
        # stub axle, pointing INWARD from the cheek; then the collar step on it
        radial_cyl('stub_%d' % i, a, cheek_or, stub_ir, tval('axle_d'), JOIN)
        radial_cyl('collar_%d' % i, a, cheek_ir, seat_r, val('collar_d'), JOIN)
        radial_cyl('axle_pilot_%d' % i, a, stub_ir,
                   stub_ir + val('axle_screw_z'), val('axle_pilot'), CUT)
    # THE RELIEF. Each 608 hangs into the base plate; this floors the plate to
    # MIN_WALL under it and no further. It stops AT cheek_ir, so the cheeks
    # keep their whole footing and only the span between them is thinned.
    _vol_before = comp.bRepBodies.item(0).volume
    for i, az in enumerate(ROLL_AZ):
        xy_arc('roller_relief_%d' % i, relief_ir, cheek_ir, math.radians(az),
               relief_half, mm(val('relief_floor')),
               mm(plate_t - val('relief_floor') + 1.0), CUT)
    # PLAYBOOK: when a CUT changes nothing, the cut is in the wrong place.
    _vol_after = comp.bRepBodies.item(0).volume
    assert _vol_before - _vol_after > 1e-4, (
        'the three roller reliefs removed %.3f mm3 - the cut is in the wrong '
        'place or at the wrong scale' % ((_vol_before - _vol_after) * 1000))
    group(t1, PH_ROLLERS)

    # ---- phase 3: yaw servo -----------------------------------------------------
    t2 = design.timeline.count
    _soff = val('shaft_off')
    xy_rect('case_aperture',
            -(val('case_w') + val('srv_clear')) / 2,
            (val('case_w') + val('srv_clear')) / 2,
            _soff - (val('case_l') + val('srv_clear')) / 2,
            _soff + (val('case_l') + val('srv_clear')) / 2,
            mm(-1.0), mm(deck_z + 1.0), CUT)
    # LEAD KEYWAY: ONE notch, centred, in the aperture's shaft-end END wall,
    # running OUT through the servo pad to daylight. The bundle leaves the
    # case's SHORT END FACE at the shaft end, dead centre across the width
    # (lib/servo.py lead datum), and the whole case travels this aperture on
    # the way down - so the cable's exit point sweeps the full aperture
    # height and the notch is cut through it, z -1.0 to deck_z.
    #
    # The two ±X side-wall notches this replaces were sited from a misreading
    # of lead_x. They also cut past the pad's own half-width (hub_x 9.0 <
    # 9.8), severing it across its full width over 6 mm of its length.
    #
    # COST, and it is a real one: this notch destroys servo_pilot_0, the NEAR
    # tab's screw pilot. The pilot is at (x 0, y _soff - tab_pitch/2), dead on
    # the notch's centreline, and lead_y = 0 means the notch cannot be moved
    # off it. The servo keeps ONE tab screw.
    #
    # THE 2026-08-28 JUSTIFICATION FOR THAT IS NOW GONE, TWICE OVER, AND IT
    # IS LEFT STANDING HERE BECAUSE SOMEONE HAS TO FIX IT. It read: "the
    # aperture is cut to case + loc so it carries the sideways load, and the
    # horn is bolted to the platter above, so the near end cannot lift far on
    # one screw." Both halves have since stopped being true.
    #   - the aperture is no longer cut to loc. lib/servo.py named THIS LINE
    #     as the one part deliberately gripping a servo case against its own
    #     tab datum, and it is cut at ts_srv_clear 1.0 now - 0.5 a side. A
    #     pocket that loose carries no sideways load at all.
    #   - the horn was never bolted to the platter; it drove the rotor. And
    #     there is no horn.
    # So the SG90 is held by ONE tab screw and a loose pocket, and its
    # reaction torque - 156.9 N.mm at stall - is taken by that one screw and
    # by whatever the pocket walls catch after 0.5 mm of lost motion, which
    # at the 11.35 mm case half-length is about 2.5 deg of yaw backlash.
    # THE FIX IS THE BRIDGE CAP that note already contemplated: a small
    # printed strap over the near tab, screwed to the pad either side of the
    # keyway, carrying the second pilot across the cable. It is a NEW part,
    # so it is not made here, and it does not change this part's geometry -
    # only two more pilots in the pad, which the bridge's own spec should
    # call for. Reported rather than quietly left as a solved problem.
    _shaft_y = _soff - val('case_l') / 2          # the near/shaft end face
    xy_rect('lead_key',
            -val('lead_key_d') / 2, val('lead_key_d') / 2,
            _shaft_y - val('lead_key_l'), _shaft_y + val('loc') / 2,
            mm(-1.0), mm(deck_z + 1.0), CUT)
    # the lead groove: from just before the case's far end face out past the
    # escape run, cut up into the plate underside so the bundle's top edge
    # keeps daylight. Volume-drop asserted below.
    # LEAD GROOVE, re-sited with the keyway. "At z -1.0 the bundle is already
    # below the plate" was true of its CENTRE and wrong about the bundle: its
    # top edge is at -1.0 + 3.4/2 = +0.7, and the plate starts at 0. So it
    # grazes 0.7 into the plate over the run between the pad and the cable
    # window - which is what the +Y groove was for, at the wrong end.
    # From the CASE END FACE, not from the end of the keyway: the plate's
    # inner rim starts at r plate_ir, which is inboard of where the keyway
    # ends, so a groove that began at the keyway left 2.15 mm of unrelieved
    # plate over the bundle. The gate read it as 0.98 mm3 still solid.
    # THE LEAD GROOVE IS CONDITIONAL NOW. The SG90 hung its case bottom 1 mm
    # below this plate, so its lead left at z -1.0 and its top edge grazed
    # the plate underside - hence a groove. The MG995 hangs ~21 mm below the
    # plate; its lead leaves far under it and has no plate to graze. Cutting
    # the groove anyway would trip the "removed nothing" guard for a cut with
    # no job. It is kept, gated on the same bundle-top arithmetic, so a
    # future short servo gets it back automatically.
    _sg = _J1S
    _case_bot_z = (deck_z * 10) - (_sg.case_h - _sg.tab_below_top - _sg.tab_thk)
    _lead_top = _case_bot_z + _sg.lead_bundle_dia + _sg.lead_bundle_dia / 2
    _need_lead_groove = _lead_top > 0.0
    if _need_lead_groove:
        _v_groove = comp.bRepBodies.item(0).volume
        _g_a = _shaft_y + 0.1
        _g_b = _g_a - val('lead_key_l') - val('lead_escape')
        xy_rect('lead_groove',
                -val('lead_groove_w') / 2, val('lead_groove_w') / 2,
                min(_g_a, _g_b) - 0.1, max(_g_a, _g_b) + 0.1,
                mm(-0.1), PREFIX + 'lead_groove_d + 1.0 mm', CUT)
        _g_drop = (_v_groove - comp.bRepBodies.item(0).volume) * 1000
        _g_full = (val('lead_groove_w') * 10) * (val('lead_groove_d') * 10) \
            * ((val('lead_key_l') + val('lead_escape') + 0.2) * 10)
        assert 1.0 < _g_drop < _g_full, (
            'the lead groove removed %.1f mm3 against a %.1f ceiling - it is not '
            'cutting where the plate is' % (_g_drop, _g_full))
        assert val('plate_t') - val('lead_groove_d') >= val('wall'), (
            'the lead groove leaves less than a wall of plate above it')
        assert val('lead_groove_d') * 10 >= _lead_top, (
            'the bundle\'s top edge reaches z %+.2f and the groove is only %.2f '
            'deep - the lead is pinched against the plate on its way out'
            % (_lead_top, val('lead_groove_d') * 10))
    #
    # ALL TAB SCREWS ARE BACK. The SG90 lost its near screw because its one
    # tab hole sat dead on the lead keyway's centreline. An MG995 tab carries
    # TWO holes, tab_pitch_y apart ACROSS the case, so both near holes land
    # either side of the keyway - asserted, not assumed. That also retires
    # the "bridge cap" the old note asked for: four screws take the 9.4
    # kg.cm reaction, not one screw and a loose pocket.
    _py = [0.0] if val('tab_pitch_y') < TOL else [-val('tab_pitch_y') / 2,
                                                    val('tab_pitch_y') / 2]
    _n_pilot = 0
    for _end, _sy in (('far', 1.0), ('near', -1.0)):
        for _k, _px in enumerate(_py):
            _y = _soff + _sy * val('tab_pitch') / 2
            if _end == 'near':
                _gap = abs(_px) - val('pilot_d') / 2 - val('lead_key_d') / 2
                if _gap < val('wall') - TOL:
                    continue            # a one-hole micro tab: keyway wins
            xy_circle('servo_pilot_%s_%d' % (_end, _k), _px, _y, val('pilot_d'),
                      mm(deck_z - val('pilot_depth')), PREFIX + 'pilot_depth', CUT)
            _n_pilot += 1
            # a pilot must stand on pad, beyond the case window, inside the pad
            assert abs(_y - _soff) - val('pilot_d') / 2 >= (
                (val('case_l') + val('srv_clear')) / 2 + val('wall') - TOL), (
                'tab pilot at y %.2f breaks into the case window' % (_y * 10))
            assert abs(_px) + val('pilot_d') / 2 <= val('hub_x') - val('wall') + TOL, (
                'tab pilot at x %.2f falls off the pad' % (_px * 10))
    assert _n_pilot == 2 * len(_py) or len(_py) == 1, (
        'only %d of %d tab screws were placed' % (_n_pilot, 2 * len(_py)))
    # THE WHOLE POINT: the shaft has to be ON the axis.
    _shaft_y_mm = (_soff - val('case_l') / 2 + val('shaft_from_end')) * 10
    assert abs(_shaft_y_mm) < 1e-6, (
        'the J1 output shaft lands at y %.3f mm and J1 turns about y = 0 - '
        'the J1 hub is centred by this spline, so an off-axis spline drives '
        'the rotor as a crank' % _shaft_y_mm)
    assert val('hub_y') * 10 >= val('tab_pitch') / 2 * 10 + 1.6, (
        'the servo pad is %.1f mm long each way and the pilots are at +-%.1f - '
        'a pilot falls off the pad'
        % (val('hub_y') * 10, val('tab_pitch') / 2 * 10))
    group(t2, PH_SERVO)

    # ---- phase 4: platter interface ----------------------------------------------
    t3 = design.timeline.count
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        xy_circle('bolt_%d' % i, tval('post_r') * math.cos(a),
                  tval('post_r') * math.sin(a), tval('bolt_d'),
                  mm(-1.0), mm(post_top + 2.0), CUT)
    # the loom window - cut LAST so it reads as a hole in a finished plate.
    # NOTE val() on an ANGLE parameter returns RADIANS, not degrees. xy_arc
    # wants radians, so they go straight in; only the printout converts.
    # vs the servo pad, the roller reliefs and the posts: sampled up in the
    # sanity block, before any geometry.
    xy_arc('cable_window', val('cable_ir'), val('cable_or'),
           val('cable_az'), val('cable_deg') / 2.0,
           '-1.0 mm', PREFIX + 'plate_t + 2.0 mm', CUT)
    group(t3, PH_FIX)

    # ---- phase 5: J1 home sensor post ---------------------------------------------
    t4 = design.timeline.count
    _hx = val('home_r') * math.cos(val('home_az'))
    _hy = val('home_r') * math.sin(val('home_az'))
    hall_top = val('hall_top')
    xy_circle('home_post', _hx, _hy, val('hall_post_d'),
              mm(plate_t - val('tol')), mm(hall_top - plate_t + val('tol')), JOIN)
    # the sensor lies FLAT, branded face up, flush with the post top
    _pw = val('hall_w') / 2 + val('loc') / 2
    _ph = val('hall_h') / 2 + val('loc') / 2
    xy_rect('hall_pocket', _hx - _pw, _hx + _pw, _hy - _ph, _hy + _ph,
            mm(hall_top - val('hall_t')), PREFIX + 'hall_t + 1.0 mm', CUT)
    # the leads leave the body's -Y edge and fold straight down this slot,
    # through the post AND the base plate, into the base below - the
    # sensor's whole cable route is this one cut.
    xy_rect('hall_lead_slot', _hx - val('hall_lead_w') / 2, _hx + val('hall_lead_w') / 2,
            _hy - _ph - val('hall_slot'), _hy - _ph + val('tol'),
            mm(-1.0), mm(hall_top + 2.0), CUT)
    group(t4, PH_HOME)

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a cheek, post or the servo pad is not touching '
        'the base plate' % comp.bRepBodies.count)
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
                a_ = apps.item(j)
                if all(w.lower() in a_.name.lower() for w in want):
                    body.appearance = a_
                    used = a_.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (body.name, body.material.name, used))
    print('DATUM: z 0 is the printed platter rim top (its z 42.00, MEASURED)')
    print('base plate r %.1f..%.1f x %.1f, 3 posts r %.1f dia %.1f to z %.2f' % (
        val('plate_ir') * 10, val('plate_or') * 10, plate_t * 10,
        tval('post_r') * 10, val('post_d') * 10, post_top * 10))
    print('rollers: 3 x 608ZZ at r %.1f, az %s, axles RADIAL at z %.2f' % (
        roll_r * 10, ROLL_AZ, tval('axle_z') * 10))
    print('  stub %.2f dia from r %.2f to %.2f past a %.1f collar %.2f proud' % (
        tval('axle_d') * 10, cheek_or * 10, stub_ir * 10,
        val('collar_d') * 10, tval('collar_h') * 10))
    print('  cheeks r %.2f..%.2f, top z %.2f (rotor rides at %.2f)' % (
        cheek_ir * 10, cheek_or * 10, cheek_top * 10, race_z * 10))
    print('RACE FACE z %.2f = axle %.2f + 608 OD/2. Rotor rim top %.2f, ring under '
          '%.2f.' % (race_z * 10, tval('axle_z') * 10,
                     (race_z + tval('disc_t')) * 10, ring_under * 10))
    print('J1 SPLINE DRIVE - NO HORN. deck %.2f, case top %.2f, boss top '
          '%.2f, spline top %.2f' % (deck_z * 10, (deck_z + (val('tab_below_top')
                                                            + val('tab_thk'))) * 10,
                                     boss_top_z * 10, spline_top_z * 10))
    print('  the rotor race face is at %.2f, so the spline stops %.2f SHORT '
          'of it - nothing on the servo touches the rotor and the rollers '
          'carry the arm' % (race_z * 10, (race_z - spline_top_z) * 10))
    print('  hub: O%.2f broach over %.2f of spline, %.2f left with the ring '
          'fully lifted (min %.2f). Bolted to the rotor, 3 x M3 on r %.2f.'
          % (tval('hub_broach_d') * 10, tval('hub_engaged') * 10,
             _engaged_lifted, J1_HUB_ENGAGE_MIN_MM, tval('hub_bolt_r') * 10))
    print('  hub body z %.2f..%.2f - built by NEITHER of J1\'s two host '
          'parts. specs/robotarm/j1_hub.md.'
          % (hub_bottom_z * 10, race_z * 10))
    print('J1 SERVO %s (360 deg continuous): tabs bear at z %.2f, case top %.2f, '
          'case bottom z %.2f - below the platter datum, so base_platter carries it'
          % (_J1S.name, deck_z * 10, case_top * 10, case_bottom * 10))
    print('  bearing seat: %.1f collar on a %.1f inner race, retained by a %.1f '
          'washer (NOT a standard M3 Ø7 - it falls through the Ø8 bore)'
          % (val('collar_d') * 10, val('race_od') * 10, val('washer_od') * 10))
    print('  SHAFT ON AXIS: case centre offset %+.2f in Y (shaft %.1f from the near '
          'end of a %.1f case)' % (val('shaft_off') * 10, val('shaft_from_end') * 10,
                                   val('case_l') * 10))
    print('  %d tab pilots O%.2f x %.1f deep, at y %+.2f / %+.2f, x +-%.2f'
          % (_n_pilot, val('pilot_d') * 10, val('pilot_depth') * 10,
             (_soff - val('tab_pitch') / 2) * 10, (_soff + val('tab_pitch') / 2) * 10,
             val('tab_pitch_y') * 5))
    print('  lead groove: %s (bundle top edge at z %+.2f)'
          % ('cut' if _need_lead_groove else 'not needed', _lead_top))
    print('  rollers at az %s clear the servo pad/case/tabs by >= %.2f (sampled)'
          % (ROLL_AZ, val('free') * 10))
    print('  LEAD KEYWAY %.1f wide, centred, END wall at y %+.1f, out to y %+.1f'
          % (val('lead_key_d') * 10,
             (val('shaft_off') - val('case_l') / 2) * 10,
             (val('shaft_off') - val('case_l') / 2 - val('lead_key_l')) * 10))
    print('  pad %.0f x %.0f centred y %+.2f'
          % (val('hub_x') * 20, val('hub_y') * 20, val('shaft_off') * 10))
    print('CABLE WINDOW: r %.1f..%.1f, %.0f deg at az %.0f - the fixed half of the'
          % (val('cable_ir') * 10, val('cable_or') * 10,
             val('cable_deg') * 180 / math.pi, val('cable_az') * 180 / math.pi))
    print('  plug-sized (8.7 x 4.5 passes); base_lid/base_platter take the loom on '
          'down; shoulder_bracket\'s window is the moving half.')
    print('ONE M3 per post: ring -> post -> platter insert. 3 screws hold the turret.')
    print('HOME SENSOR: A3144 flat in a %.2f x %.2f pocket on a O%.1f post at r %.1f az '
          '%.0f, face at z %.2f; a O%.0f x %.0f magnet in the rotor\'s pocket at r %.1f '
          'hangs to z %.2f - gap %.2f (%.2f if glued flat to an un-pocketed rotor). '
          'Leads down a %.2f x %.2f slot into the base.'
          % (val('hall_w') * 10 + val('loc') * 10, val('hall_h') * 10 + val('loc') * 10,
             val('hall_post_d') * 10, val('home_r') * 10, math.degrees(val('home_az')),
             hall_top * 10, val('magnet_d') * 10, val('magnet_h') * 10,
             val('home_r') * 10, (race_z - val('magnet_protrude')) * 10,
             (race_z - val('magnet_protrude') - hall_top) * 10,
             (race_z - val('magnet_h') - hall_top) * 10,
             val('hall_lead_w') * 10, val('hall_slot') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 1000 * 0.6, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
