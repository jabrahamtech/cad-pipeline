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
# and a neodymium disc GLUED into a pocket under the ROTOR (shoulder_bracket) - no
# contact, no adjustment, nothing for the loom to snag. Frames: stator
# frame (z 0 = platter rim top, J1 axis, az from +X).
HOME_R_MM = 33.7          # CHOSEN - the rotor underside is flat and free
                          # between the roller track (to r 31.0) and the rim
                          # edge (r 38). A O5.2 pocket centred here leaves
                          # 0.1 to the track and MIN_WALL + 0.1 to the edge.
                          # Revision 2026-09-27: 34.5 -> 33.7 with the magnet
                          # O6 -> O5, because a O6.2 pocket cannot keep a
                          # MIN_WALL to the rim anywhere in that band.
HOME_AZ_DEG = 210.0       # CHOSEN - between the az-150 and az-270 roller
                          # cheeks, clear of the posts. 330 -> 210 in the
                          # 2026-09-27 revision: az 330 went to the LOOM,
                          # which is right over the ESP32 bay.
MAGNET_D_MM = 5.0         # DATASHEET-class - 5 x 2 N52 disc, bought
                          # (was 6 x 2; see HOME_R_MM)
MAGNET_H_MM = 2.0
MAGNET_POCKET_MM = 1.0    # CHOSEN - locating pocket in the rotor underside
                          # (shoulder_bracket). Half the magnet sits in it.
MAGNET_PROTRUDE_MM = MAGNET_H_MM - MAGNET_POCKET_MM
HALL_GAP_MM = 2.5         # ASSUMED - magnet face to sensor face. An A3144
                          # operates at ~9-17 mT; a 5x2 N52 gives that well
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


# --- WHERE THE LOOM CROSSES J1, AND WHAT "HOME" MEANS ------------------------
# Stator frame. The loom leaves the rotating half through shoulder_bracket's
# connector gate (rotor frame az 270) and enters the fixed half through the
# stator's loom window. 2026-09-27 revision: the window moved 210 -> 330 so
# it sits DIRECTLY OVER the ESP32 bay - the loom and the board's top-face
# cables drop straight onto the board instead of crossing under the MG995.
LOOM_AZ_DEG = 330.0
LOOM_IR_MM = 22.0             # outside the servo pad corner by a wall
LOOM_OR_MM = 29.5             # inside the home magnet's sweep (r 31.5) by a wall
LOOM_DEG = 40.0               # arc; chord at the mean radius passes an 8.7 plug
ROTOR_GATE_AZ_DEG = 270.0     # shoulder_bracket's connector gate - it asserts this
# HOME IS WHERE THE LOOM IS UNTWISTED. J1 is continuous and firmware limits
# it to +-180 deg from home, so home should be the angle at which the gate is
# right over the window - then the twist is symmetric. At that angle the
# rotor has turned (LOOM - GATE); the magnet must then sit over the sensor,
# so in the ROTOR's own frame it goes at HOME - (LOOM - GATE).
MAGNET_ROTOR_AZ_DEG = (HOME_AZ_DEG - (LOOM_AZ_DEG - ROTOR_GATE_AZ_DEG)) % 360.0

# The platter's three turret posts. Revision 2026-09-27: O8.8 -> O12.0. They
# are 40 mm free-standing columns carrying the whole arm's tipping moment into
# three M3; stiffness goes as d^4, so this is ~3.5x. base_lid's holes follow.
TT_POST_D_MM = 12.0
TT_POST_LID_CLEAR_MM = 0.7    # legacy MEASURED fit: O9.5 over O8.8


# --- THE J1 CABLE CUP ----------------------------------------------------------
# Revision 2026-09-27, after cable-routing research (igus / LAPP torsion
# limits): a +-180 deg loom cannot twist straight down a ~20 mm axis, so it
# WRAPS round the J1 hub in the chamber between the MG995's case top and the
# rotor. Unguarded, that loose loop can drift outward into the 608s - whose
# tops ride in contact with the rotor race face, a nip that would crush it.
# j1_hub therefore grows a CUP: a flat ring flush with its bolted top face
# out to a skirt that hangs down to just above the servo. It rotates with the
# rotor, so the loop lives inside it, and the fixed end of the loom leaves
# under the skirt's lower edge toward the stator's loom window.
J1_CUP_R_IN_MM = 20.0         # skirt inner radius - the loop's outer wall
J1_CUP_WALL_MM = 1.6          # skirt wall and top ring thickness - MIN_WALL
J1_CUP_R_OUT_MM = J1_CUP_R_IN_MM + J1_CUP_WALL_MM   # 21.6, vs roller stubs at r 22.5
# THE SKIRT STOPS ABOVE THE ROLLER CAPS. Each 608 is held on its stub by a
# printed cap and an M3 screw at the stub's INNER end (r 23.5 -> 21.1), and a
# O11 cap reaches z 18.6. A skirt down to the servo would have run through all
# three. So the skirt guards z 19.0 up - which is where the danger is: the
# nip is where each 608's TOP meets the rotor, at z 24.1.
ROLLER_CAP_D_MM = 11.0        # spans the 608 inner race face (O8..O12)
ROLLER_CAP_T_MM = 3.0        # 1.7 floor over the recess - MIN_WALL + 0.1
ROLLER_CAP_RECESS_D_MM = 8.3  # clears the O7.9 stub, which stands 1.0 proud
ROLLER_CAP_RECESS_H_MM = 1.3  # of the bearing face (+0.3)
ROLLER_SCREW_L_MM = 8.0       # M3 x 8 socket cap, cap -> stub pilot. The stator
                              # asserts it bites >= 2 d and stops short of the pilot.
ROLLER_CAP_TOP_Z_MM = TT_AXLE_Z_MM + ROLLER_CAP_D_MM / 2.0       # stator frame, 18.6
J1_CUP_SKIRT_Z_MM = (ROLLER_CAP_TOP_Z_MM + 0.4                  # free fit
                     - (J1_DECK_Z_MM + J1_HUB.seat_z))          # hub-frame: 2.8
J1_CUP_GATE_HALF_DEG = 25.0   # cutout under the rotor's connector gate + window,
                              # +-25 deg about ROTOR_GATE_AZ_DEG (rotor frame)
J1_CUP_LOOP_MM = 110.0        # free loom length to leave coiled in the cup:
                              # +-180 deg x r_mean ~15.5 = 97, + margin (DERIVED)


# --- the rotor's connector gate, as shoulder_bracket cuts it (it asserts) ----
ROTOR_GATE_W_MM = 9.8
ROTOR_GATE_IR_MM = 12.2
ROTOR_GATE_OR_MM = 18.0
