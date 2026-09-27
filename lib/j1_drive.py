"""The J1 drive contract - ONE copy, read by every file that touches it.

Until 2026-09-27 this block was typed three times, verbatim, into
turntable_stator.py, shoulder_bracket.py and j1_hub.py, each copy saying "if
these three ever disagree the hub is BORED from one set of numbers and
LOCATED by another". A servo swap is exactly the change that finds every
copy, so it moved here when J1 went from an SG90 to an MG995 360 deg
(Jonathan, 2026-09-27). The reasoning that used to live beside each copy is
in turntable_stator.py's header and specs/robotarm/j1_hub.md; this file
keeps the numbers and the two rules that derive them.

Everything is in MILLIMETRES. Nothing here is a Fusion parameter; the
scripts mirror these as tt_* user parameters.
"""

from lib.design_rules import FASTENER_MM as _FASTENER
from lib.design_rules import JOINT_FIT_MM as _FIT
from lib.design_rules import MIN_WALL_MM as _MIN_WALL
from lib.joints import servo_for
from lib.servo import spline_z as _spline_z
# IMPORT ORDER IS LOAD-BEARING: lib.gears <-> lib.servo_hub is a cycle that
# only resolves when lib.gears is imported first. Same note as the scripts.
import lib.gears  # noqa: F401,E402
from lib.servo_hub import spline_hub  # noqa: E402

J1_SERVO = servo_for('J1')

J1_HUB_OVERSHOOT_MM = 0.5      # ASSUMED - minimum run of hub bore past the
                               # spline top, so the spline stops SHORT of the
                               # rotor face instead of jacking it off its rollers.
J1_HUB_PROBE_FACE_MM = 12.0    # NOT A DIMENSION - a face past min_height so
                               # spline_hub() will solve; only broach_to is read.
J1_HUB_ENGAGE_MIN_MM = 2.0     # spline_hub()'s own engagement floor
J1_HUB_SCREW = 'M3'
J1_HUB_SCREW_D_MM = 3.0        # DATASHEET - M3 nominal, the bearing width
J1_HUB_BOLT_R_MM = 8.0         # boxed in: rotor cbore must clear the rotor
                               # screw bore + wall, hub OD must stay inside
                               # shoulder_bracket's connector gate (r 12.2).
J1_HUB_BOLT_AZ_DEG = (90.0, 210.0, 330.0)   # miss the rotor gate at az 270
J1_HUB_FLOAT_MM = 1.0          # deliberate radial float in the ROTOR hole
J1_HUB_HOLE_D_MM = _FASTENER[J1_HUB_SCREW]['clearance'] + J1_HUB_FLOAT_MM
J1_HUB_HEAD_D_MM = 5.5         # DATASHEET - ISO 4762 M3 cap head
J1_HUB_HEAD_H_MM = 3.0         # DATASHEET
J1_HUB_CBORE_D_MM = J1_HUB_HEAD_D_MM + _FIT['free']
J1_HUB_CBORE_H_MM = J1_HUB_HEAD_H_MM
J1_HUB_PILOT_D_MM = _FASTENER[J1_HUB_SCREW]['pilot']
J1_HUB_PILOT_H_MM = 3.7        # CHOSEN - the thread engagement the bearing
                               # tables in j1_hub.md are computed at
J1_HUB_OD_MM = 2.0 * (J1_HUB_BOLT_R_MM + J1_HUB_PILOT_D_MM / 2.0 + _MIN_WALL)
J1_HUB_SCREW_BORE_MM = J1_SERVO.horn_screw_dia * 2.0 + _FIT['free']

_J1_PROBE = spline_hub(J1_SERVO, face=J1_HUB_PROBE_FACE_MM)

# THE FACE, AND THE ONE RULE THAT CHANGED WITH THE MG995. The hub used to be
# exactly tall enough to swallow the spline plus overshoot (SG90: 6.80). An
# SG90's output boss is O5.0, so the hub's boss clearance (O5.4) sat far
# inside the r 8.00 bolt circle and the pilots could run down beside it.
# An MG995's boss is O13.0 -> clearance O13.4, r 6.70 - and a O2.60 pilot on
# r 8.00 starts at r 6.70. Same radius. So when the pilots stand over the
# boss clearance, the hub grows until they sit ON TOP of it with a wall
# between: clearance depth + MIN_WALL + pilot depth. That keeps the bolt
# circle - and so the rotor's holes - where they were, which is the cheaper
# of the two fixes (the other was r 9.60 and a new gate in the rotor).
_PILOT_OVER_BOSS = (J1_HUB_BOLT_R_MM - J1_HUB_PILOT_D_MM / 2.0
                    < _J1_PROBE.boss_clear_d / 2.0 + _MIN_WALL)
J1_HUB_FACE_MM = max(
    _J1_PROBE.broach_to + J1_HUB_OVERSHOOT_MM,
    (_J1_PROBE.boss_clear_to + _MIN_WALL + J1_HUB_PILOT_H_MM)
    if _PILOT_OVER_BOSS else 0.0)
J1_HUB = spline_hub(J1_SERVO, face=J1_HUB_FACE_MM)
J1_BOSS_TOP_MM, J1_SPLINE_TOP_MM = _spline_z(J1_SERVO)

assert J1_HUB.engaged >= J1_HUB_ENGAGE_MIN_MM, (
    'J1 %s: the hub grips %.2f of spline against a %.2f floor'
    % (J1_SERVO.name, J1_HUB.engaged, J1_HUB_ENGAGE_MIN_MM))


# --- J1 HOME SENSOR --------------------------------------------------------
# Jonathan, 2026-09-27: J1 is a CONTINUOUS MG995, so it has no position
# feedback and must be homed. A roller microswitch was considered and
# dropped the same day: a KW12-3 needs ~24 mm of height under whatever
# presses it and the rotor is 24.1 above the stator plate, so the switch
# would have had to be sunk through two parts and hand-adjusted. Chosen
# instead: an A3144 unipolar hall sensor standing on a post on the STATOR,
# and a neodymium disc GLUED under the ROTOR (shoulder_bracket) - no
# contact, no adjustment, nothing for the loom to snag. Frames: stator
# frame (z 0 = platter rim top, J1 axis, az from +X).
HOME_R_MM = 34.5          # CHOSEN - the rotor underside is flat and free
                          # between the race band (r 23..31) and the rim
                          # edge (r 38); r 34.5 centres a O6 magnet in it.
HOME_AZ_DEG = 330.0       # CHOSEN - between the az-270 and az-30 roller
                          # cheeks, clear of the posts and the loom window.
MAGNET_D_MM = 6.0         # DATASHEET-class - 6 x 2 N52 disc, bought
MAGNET_H_MM = 2.0
HALL_GAP_MM = 2.5         # ASSUMED - magnet face to sensor face. An A3144
                          # operates at ~9-17 mT; a 6x2 N52 gives that well
                          # past 3 mm. Gauge on the bench if it misses.
# A3144 in TO-92UA (Allegro 'UA' package) - DATASHEET
HALL_BODY_W_MM = 4.06     # across the leads' plane
HALL_BODY_H_MM = 3.00     # body height, leads out of the bottom edge
HALL_BODY_T_MM = 1.52     # thickness; the BRANDED face is the sensing face
HALL_LEAD_PITCH_MM = 1.27
HALL_LEAD_N = 3
HALL_SLOT_MM = 2.4        # ASSUMED - lead slot depth beside the pocket, the way
                          # the leads fold down (stator cuts it, lid holes under it)


# --- WHERE THE ROTOR RIDES, for parts that are not the stator --------------
# turntable_stator.py declares these as tt_axle_z / tt_roller_od and ASSERTS
# its values against these two, so base_platter.py can place the J1 servo
# envelope without being built into the stator's document.
TT_AXLE_Z_MM = 13.1
TT_ROLLER_OD_MM = 22.0
TT_RACE_Z_MM = TT_AXLE_Z_MM + TT_ROLLER_OD_MM / 2.0
J1_DECK_Z_MM = TT_RACE_Z_MM - J1_HUB_FACE_MM - J1_HUB.seat_z   # tab underside
