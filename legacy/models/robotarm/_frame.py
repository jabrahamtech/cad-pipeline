"""Shared frame for the robotarm project — the numbers more than one part
must agree on. Spec: specs/robotarm/_project.md.

GLOBAL FRAME: origin at the centre of the base's bottom face, Z up, the
base-yaw (MG995) shaft on the Z axis. Every height below is z in that frame.

VERTICAL STACK
    0.0            bed / bottom of the platter floor
    FLOOR_T        bay floor -> electronics bay
    Z_LID          lid shelf; base_lid closes the bay flush with the rim
    Z_RIM          top of the rounded rim; turret_cap lands here
    Z_FLANGE       cap top face: the MG995 flange bolts down onto it
    Z_RACE         underside of the shoulder turntable = top of the rollers
                   = MG995 horn top face

WHY THE TURRET IS A SEPARATE PART: the MG995 column has to stay narrow
(27 mm across) where it passes through the bay, or the 85.5 x 55.5 breadboard
cannot clear it inside any sane base diameter. The roller race has to be
Ø104. Flaring one into the other inside a single part means a >50 deg
overhang; as two parts, both print flat with no support at all.

TURNTABLE BEARINGS: three 608ZZ roll on their outer races against the flat
underside of the turntable, on a ROLLER_PITCH_R circle, axles horizontal
(tangential). They carry the arm's weight and overturning moment, so the
MG995 horn only transmits torque — a bare MG995 output shaft is the usual
slop/failure point on an arm this size.

The MG995 case lies along Y and the rollers sit at 0/120/240 deg, so no
roller pocket cuts into the case pocket.
"""

from __future__ import annotations

import math

from lib.bearings import B608ZZ
from lib.design_rules import (
    M3_INSERT_BOSS_WALL_MM,
    M3_INSERT_HOLE_DIA_MM,
    PRESS_FIT_CLEARANCE_MM,
    SLIDING_FIT_CLEARANCE_MM,
)
from lib.servo import MG90S, MG995, SG90

# --- servo allocation (decided 2026-08-22 from a static torque check)
# The MG995 goes to the SHOULDER, not the base. The shoulder is the only
# joint where gravity acts on the whole arm at the longest moment arm: with
# a 50 g payload at 150 mm reach it needs 2.31 kg.cm, and an MG90S stalls at
# 2.2. The base turns about a vertical axis, so gravity does no work there —
# and the 608ZZ rollers take the overturning moment off the shaft entirely —
# so the base only has to overcome inertia and friction, which an MG90S does
# at a few percent of stall.
# Base takes the SG90 and the wrist takes the MG90S, not the other way round.
# The two are dimensionally IDENTICAL (see lib/servo.py), so this costs no
# geometry at all — it is purely which servo goes in which hole. The base
# fights inertia only; the wrist holds the whole end effector out at ~55 mm
# (0.78 kg.cm) continuously, which is 43 % of an SG90 but 35 % of an MG90S,
# and the MG90S's metal gears do not creep under a sustained static load.
BASE_SERVO = SG90
SHOULDER_SERVO = MG995
ELBOW_SERVO = MG90S
WRIST_SERVO = MG90S
EFFECTOR_SERVO = SG90
# TWO of them: the parallel-jaw hand drives one four-bar per side, which
# removes the meshing gears entirely and lets each jaw be driven on its own.
EFFECTOR_SERVO_COUNT = 2

# --- base platter
OUTER_DIA = 176.0
WALL = 4.0
INNER_R = OUTER_DIA / 2 - WALL          # 84.0 (breadboard corners land at 82.0)
FLOOR_T = 3.0
LID_T = 3.0
LID_WALL = 2.0                          # rim wall thinned over the lid recess
Z_RIM = 42.0
Z_LID = Z_RIM - LID_T                   # 39.0 — lid underside sits here
BAY_H = Z_LID - FLOOR_T                 # 36.0 (stack is 16.1; the rest is
                                        # wiring room AND the height the base
                                        # needs to not look like a saucer)

# --- base-servo column through the bay (case long axis along Y)
COLUMN_INNER_X = BASE_SERVO.case[1] + SLIDING_FIT_CLEARANCE_MM   # 12.45
COLUMN_INNER_Y = BASE_SERVO.case[0] + SLIDING_FIT_CLEARANCE_MM   # 23.05
COLUMN_OUTER_X = COLUMN_INNER_X + 2 * WALL                       # 20.45
COLUMN_OUTER_Y = COLUMN_INNER_Y + 2 * WALL                       # 31.05
COLUMN_Y = -BASE_SERVO.shaft_offset     # case centre, so the shaft is at y=0
# A servo's lead leaves the SIDE of its case, so an opening cut to the case
# plus a sliding fit pinches the wire and the servo will not push home. Every
# case opening gets a full-depth relief on both side faces — both, so the
# servo can go in either way round. Measured against lib.cots.servo_with_lead.
LEAD_RELIEF_W = 9.0                     # along the case
LEAD_RELIEF_D = 4.0                     # out past the case face

# --- turret cap (separate part, bolts onto the rim/column at Z_RIM)
CAP_DIA = 104.0
# Cap height is driven by the rollers, not the servo: the 22 mm bearing has to
# sit entirely above the rim, so Z_RACE - B608ZZ.od >= Z_RIM.
CAP_H = 12.0
Z_FLANGE = Z_RIM + CAP_H                # 54.0
CAP_BOLT_R = 45.0
# x < BREADBOARD_X0 keeps every boss clear of the breadboard, and
# 120/180/240 sits 30 deg off every roller azimuth.
CAP_BOLT_AZ = [120.0, 180.0, 240.0]

# HOLD-DOWN CLIPS. The rollers only push UP. With the arm extended the
# combined centre of mass leaves the roller circle (45.7 mm out against a
# 36 mm circle, 60.4 mm with a payload), so the turntable tips onto two
# rollers and lifts off the third — and the only thing resisting that would
# be the base servo's horn screw, i.e. the very shaft the bearings exist to
# unload. Three clips bolt to the cap AFTER the disc is on and overlap its
# rim, so it still turns freely but cannot lift. Fitted afterwards rather
# than moulded in, because fixed hooks would need a bayonet slot and that
# would cap base rotation at about +/-50 deg.
# The clips bolt RADIALLY into the cap's outer face, not down into its top.
# There is only a 4 mm annulus between the Ø96 disc and the Ø104 cap edge —
# nowhere near enough for an M3 boss — but the cap plate is 12 mm of solid
# material when you come at it from the side. It also means anyone who has
# already printed a cap can retrofit the clips by drilling three holes.
CLIP_R = CAP_DIA / 2                 # the cap's outer face: where they land
CLIP_SCREW_Z = -6.0                  # below the cap's TOP face, mid-plate
CLIP_AZ = [30.0, 150.0, 270.0]       # between the rollers and the cap bolts
CLIP_OVERLAP_R = 44.0                # tongue reaches this far in over the rim
CLIP_LIFT_GAP = 0.4                  # running clearance above the disc

# WIRE ROUTE. Four servo leads (shoulder, elbow, wrist, effector) have to get
# from the ESP32 in the bay, through a joint that ROTATES, and up the arm.
# They go up beside the base servo, through the cap at WIRE_PASS_R, then
# inward and up through the turntable's centre bore — which is ON the axis of
# rotation, so turning the base twists the bundle instead of dragging it.
# That is why the disc's horn-screw access bore is opened out to
# WIRE_BORE_DIA: it is the screwdriver access AND the wire pass.
# Twist, not travel, is what limits base rotation: keep it to +/-90 deg and
# leave a slack loop in the 12 mm gap under the disc.
WIRE_PASS_R = 24.0
WIRE_PASS_AZ = 0.0                   # clear of forks, cap bolts and clips
WIRE_PASS_DIA = 14.0
WIRE_BORE_DIA = 14.0                 # through the turntable, on the axis

# --- lid
LID_DIA = OUTER_DIA - 2 * LID_WALL - SLIDING_FIT_CLEARANCE_MM   # 171.75
LID_SCREW_R = 78.0
LID_SCREW_AZ = [45.0, 135.0, 225.0, 315.0]

# --- turntable rollers (3 x 608ZZ on M8 axles)
ROLLER_COUNT = 3
ROLLER_PITCH_R = 36.0
Z_RACE = Z_FLANGE + BASE_SERVO.horn_face     # 54.2
Z_AXLE = Z_RACE - B608ZZ.radius              # 43.2
Z_ROLLER_FLOOR = Z_RACE - B608ZZ.od          # 32.2 — bottom of the roller slot
# 90/210/330, not 0/120/240: the base servo's case is off-centre along Y (its
# shaft sits shaft_offset off the case centre), so a roller at 240 deg would
# cut into the case pocket. tests/test_robotarm.py checks this.
ROLLER_AZIMUTHS = [90.0, 210.0, 330.0]
FORK_WALL_T = 4.0
FORK_GAP = B608ZZ.width + 0.9                # 7.9: 0.4 pads per side + slack
FORK_PAD_DIA = B608ZZ.inner_race_od - 0.6    # clamp the inner race only
FORK_PAD_PROUD = 0.4
AXLE_HOLE_DIA = B608ZZ.bore + 0.4            # M8 bolt runs free in the fork

# --- turntable (shoulder_bracket's disc)
TURNTABLE_DIA = 96.0
# 6 mm: thick enough for the base servo's horn pocket plus a boss relief and
# still leave more than MIN_WALL_MM, and stiff enough not to dish between the
# three rollers.
TURNTABLE_T = 6.0
Z_TURNTABLE_TOP = Z_RACE + TURNTABLE_T       # 60.2
# The rollers contact the disc along a line at ROLLER_PITCH_R, not over the
# whole bearing OD, so only this narrow annulus has to stay flat. The band is
# widened by +/-3 mm for the shaft-offset tolerance on the MG995.
RACE_CONTACT_BAND = (ROLLER_PITCH_R - 3.0, ROLLER_PITCH_R + 3.0)

# --- arm chain
UPPER_ARM_LEN = 80.0                         # shoulder -> elbow axis
FOREARM_LEN = 70.0                           # elbow -> wrist axis
def channel_width(servo) -> float:
    """Inner width a link needs to straddle `servo`: the horn seat stands
    proud of the flange on one side, the case hangs below it on the other,
    and the far bracket wall and clearances sit beyond that."""
    return servo.horn_seat + servo.below_flange + 4.0 + 2.6


# --- JOINT ENCLOSURE: the drum-and-skirt contract
#
# Every joint is built the same way, which is what gives the arm a closed
# silhouette instead of a visible mechanism:
#
#   the member holding the servo CASE carries a DRUM — a cylinder concentric
#   with the joint axis, sized to swallow the case;
#   the member driven by the HORN carries a SKIRT — an annular wall that laps
#   over the drum with a running clearance.
#
# Both are concentric with the axis, so the joint reads closed at EVERY angle
# and nothing new is swept: a disc turning about its own centre cannot foul.
# That is the whole reason this works where a flat cover does not — see the
# sweep rule in models/robotarm/_shell.py.
#
# Drum radii come from the servo envelope measured off the joint axis (the
# case is NOT centred on its shaft), plus a 3 mm wall.
# 38.5, not 35.5: at 35.5 the bore left 0.3 mm around the MG995's case
# corners. That is unbuildable in a printed part, and it leaves the servo's
# own lead nowhere to go — the wire has to reach 34.9 mm from the axis to
# escape. 38.5 gives 3.3 mm around the case and swallows the lead.
DRUM_R_SHOULDER = 38.5      # MG995 case encloses at r=32.2
DRUM_R_ELBOW = 21.0         # MG90S case encloses at r=18.0
SKIRT_CLEARANCE = 1.0       # radial running gap, drum OD to skirt ID
SKIRT_T = 2.5
SKIRT_LAP = 6.0             # axial overlap, so no gap shows at any angle


# Drum width = the servo's below-flange depth PLUS BOTH CAPS. The caps eat
# into the bore, so sizing the drum to the case depth alone leaves the case
# 2*wall too deep — it would foul the far cap, and its end lands exactly
# where that cap's idler bore has to go. (Got this wrong first time round;
# the assembly check caught it.)
#   MG995: 32.0 below flange + 2 x 3.0 wall = 38.0
# The horn then seats 19.0 + 6.9 = 25.9 from the drum centre, which sets the
# arm's channel half-width, so its driven plate lands exactly on the horn.
SHOULDER_DRUM_Y = (-19.0, 19.0)     # joint frame: channel centred on 0
# Elbow and wrist drums are sized to their link's channel rather than to the
# micro servo, which is much smaller — the drum is a housing, not a shrink
# wrap. Widths chosen so the mating link's channel closes on the numbers:
#   elbow: horn seats at 17.5 + 10.6 = 28.1 from centre, drum far end at
#          17.5, so the forearm needs 28.1 + 17.5 + 1 = 46.6 -> 47.
# +/-12, not +/-17.5: an MG90S needs only below_flange + two caps = 21.9 mm
# of drum, and every extra millimetre of drum width costs TWO millimetres of
# channel in the link that straddles it.
ELBOW_DRUM_Y = (-12.0, 12.0)
DRUM_WALL = 3.0
SHOULDER_DRUM_WALL = 3.0
# Raised from 30: the arm's near end now carries a skirt out at r=39, and the
# tail has to clear the turntable when the arm lifts (see SHOULDER_TAIL_R).
SHOULDER_RISE = 46.0        # follows the bigger drum + skirt


def skirt_inner_r(drum_r: float) -> float:
    return drum_r + SKIRT_CLEARANCE


def skirt_outer_r(drum_r: float) -> float:
    return drum_r + SKIRT_CLEARANCE + SKIRT_T


# Elbow and wrist joints (both micro servos) share one channel width; the
# shoulder is an MG995, so upper_arm's near end has to be wider than its
# far end. The elbow channel now has to straddle upper_arm's far DRUM, not
# just its plates, which is also what finally puts the elbow in double shear.
LINK_AXIS_Z = 14.0          # every link's joint axes, above its own bed face
LINK_CHANNEL_W = 35.0                        # wrist end of the forearm
# Derived the same way the shoulder is, and for the same reason: the driven
# member seats on the HORN, which is mount_to_horn beyond the drum's cap —
# tab thickness included. Hardcoding these left the elbow's driven plate
# 7.1 mm short of its horn, the identical fault the shoulder had.
ELBOW_CHANNEL_W = 2 * (ELBOW_DRUM_Y[1] + ELBOW_SERVO.mount_to_horn)   # 50.2
# = 2 * (drum half + mount_to_horn). mount_to_horn, NOT horn_seat: the tabs
# bear on the cap's OUTER face, so they sit a tab thickness outboard of it,
# and the horn is that much further out again. Measuring from horn_seat put
# the servo's tabs inside the cap wall — the fit check caught it.
SHOULDER_CHANNEL_W = 2 * (SHOULDER_DRUM_Y[1] + MG995.mount_to_horn)   # 57.8
# Back to zero: with a drum housing the case is enclosed by a Ø71 cylinder
# that fits the Ø96 disc easily, so there is no longer any reason to shift
# the shoulder axis off the yaw axis.
SHOULDER_AXIS_OFFSET_X = 0.0
# Radius of shoulder_bracket's material about the shoulder axis. upper_arm
# straddles the bracket and rotates about that axis, so its two side plates
# may come as close as they like, but NOTHING may bridge between them inside
# this radius — a web there jams against the bracket at every angle.
SHOULDER_SWEEP_R = 42.0
LINK_WEB_CLEAR_R = SHOULDER_SWEEP_R + 1.5
# The link's tail — the plate material BEHIND the shoulder axis that contains
# the MG995 horn — swings down toward the turntable as the arm lifts. It has
# to stay inside the axis height above the disc, or the arm cannot raise past
# about 40 deg. Big enough to still hold the horn (span/2 = 27).
SHOULDER_TAIL_R = SHOULDER_RISE - 2.0
LINK_PLATE_T = 4.0
# IDLER SIDE RUNS ON A BEARING. The horn side is carried by the servo's own
# output bearing; the far side used to be a printed stub in a printed bore —
# plastic on plastic, which binds and wears oval. A 608ZZ in the far cap
# turns that into a real journal. It is nearly free structurally because the
# bearing sits ON the joint axis, so it adds mass but almost no moment: the
# elbow's bearing contributes nothing to the elbow at all.
# Uses two of the three 608ZZ left over from the turntable.
ARM_BEARING = B608ZZ
# Outer race presses into the housing, inner race presses onto the stub.
BEARING_SEAT_DIA = B608ZZ.od - PRESS_FIT_CLEARANCE_MM
BEARING_SEAT_DEPTH = B608ZZ.width + 0.5      # seated flush with the cap face
IDLER_BOSS_DIA = B608ZZ.bore - PRESS_FIT_CLEARANCE_MM    # the stub, 7.85


def stub_length(channel_w: float, drum_half: float) -> float:
    """How far the idler stub must reach to pass right through its bearing:
    from the link's plate face to the far side of the race."""
    return channel_w / 2 - (drum_half - ARM_BEARING.width)
# ---------------------------------------------------------------------------
# WRIST: a ROLL joint on a BOLT-ON BRACKET.
#
# The wrist servo does not live inside the forearm any more. wrist_mount is a
# saddle that slips over the forearm's tip from outside, takes two M3 straight
# through it, and presents a slotted face the servo's flange bolts to with its
# shaft pointing forward down the arm. wrist_rotator turns on that shaft and
# the effector bolts to it.
#
# WHY BOLT-ON RATHER THAN BUILT-IN: the wrist is the part of this machine most
# likely to change, and a bracket can be re-cut on its own without touching a
# 28 cm^3 link. It also makes the forearm's tip a plain rectangular channel —
# no flange, no drum, no servo pocket — which is far easier to print well.
#
# The joint still ROLLS. Gravity does almost no work about a roll axis, so the
# wrist servo runs at a few percent of stall.
WRIST_ROLL_Z = LINK_AXIS_Z                   # roll axis, on the link centreline
FOREARM_TIP_CHANNEL_W = 16.0                 # plain channel at the far end
FOREARM_TIP_PLATE_T = 3.0
FOREARM_TIP_W = FOREARM_TIP_CHANNEL_W + 2 * FOREARM_TIP_PLATE_T      # 22
FOREARM_TIP_OVERRUN = 2.0                    # plates run this far past
                                             # FOREARM_LEN; the plan's far
                                             # corner cannot be filleted at
                                             # exactly zero
WRIST_FACE_X = FOREARM_TIP_OVERRUN + 0.5     # servo face, from FOREARM_LEN
# Two M3 straight through the saddle AND both of the forearm's side plates,
# nutted on the far side. Measured back from FOREARM_LEN.
WRIST_MOUNT_BOLT_DX = (-9.0, -24.0)
WRIST_MOUNT_BOLT_DIA = 3.4
# The saddle may only grip the PARALLEL part of the tip. The forearm's plan
# tapers from the elbow channel down to FOREARM_TIP_CHANNEL_W and does not
# finish until FOREARM_TAPER_END, so a longer saddle simply will not go on —
# it fouled the taper by 425 mm^3 the first time.
FOREARM_TAPER_END = 40.0
WRIST_MOUNT_SADDLE_LEN = 27.0
WRIST_MOUNT_WALL = 3.2

WRIST_FLANGE_T = 5.0                         # servo face; also the pilot depth
# The face has to reach the servo's OUTER tab hole with a full pilot boss
# round it. That hole is 19.4 from the shaft — the case is not centred on it —
# so 19.4 + pilot/2 + MIN_WALL sets the radius, not taste.
WRIST_FLANGE_R = 22.5
# Journal: an annular boss on the face that the rotator's skirt runs on, so
# the effector's weight goes into a Ø39 plain bearing instead of into the
# servo's 4.8 mm output shaft.
WRIST_BOSS_BORE_R = 17.0                     # clears the horn (r 16.2)
WRIST_BOSS_R = 19.5                          # journal surface
WRIST_BOSS_LEN = 12.0
# Cut flat above 45 deg from the axis so every surface on it prints inside
# 45 deg of vertical. What is left is a V-journal open top and bottom, which
# still constrains the rotator both ways — and it is what keeps the servo's
# own mounting tabs clear of the boss wall (they reach r = 21.75 at the top).
WRIST_BOSS_CUT_Z = WRIST_ROLL_Z + WRIST_BOSS_R * 0.707
ROTATOR_SKIRT_T = 2.5
ROTATOR_SKIRT_LEN = 10.0
ROTATOR_R = WRIST_BOSS_R + SLIDING_FIT_CLEARANCE_MM + ROTATOR_SKIRT_T   # 22.25
ROTATOR_T = 4.0                              # the disc itself


def wrist_horn_face_x() -> float:
    """Distance from the servo face's FRONT surface to the horn's TOP face —
    the plane the rotator seats on. mount_to_horn, not horn_seat: the tabs
    bear ON that surface, so everything is measured from there."""
    return WRIST_SERVO.mount_to_horn + WRIST_SERVO.horn_thick   # 14.7


# EFFECTOR INTERFACE: a flat bolt circle on the rotator's face. Both end
# effectors carry the same four clearance holes, so they swap by undoing four
# screws with the arm untouched.
#
# r = 11, not more: the inserts sit in bosses on the rotator's BACK face,
# which have to live inside the journal boss's bore (r 17) and miss the horn's
# four arms. At r 11 a Ø8.8 boss spans r 6.6..15.4 and az +/-24 deg about its
# own centre, so bosses at 45/135/225/315 clear arms at 0/90/180/270
# (half-width 16.5 deg at that radius) with 5 deg to spare.
EFFECTOR_BOLT_R = 11.0
EFFECTOR_BOLT_AZ = (45.0, 135.0, 225.0, 315.0)
EFFECTOR_BOLT_CLEAR_DIA = 3.4
EFFECTOR_BOSS_DIA = M3_INSERT_HOLE_DIA_MM + 2 * M3_INSERT_BOSS_WALL_MM   # 8.8
EFFECTOR_BOSS_LEN = 5.0


# --- electronics bay contents (MEASURED 2026-08-22)
BREADBOARD = (55.5, 85.5, 9.3)   # (x, y) with the long axis tangential
BREADBOARD_STACK_H = 16.1        # with the ESP32 seated on it
BREADBOARD_X0 = 11.5             # near edge, 1.3 mm clear of the column
SWITCH_HOLE_DIA = 13.1 + SLIDING_FIT_CLEARANCE_MM
DC_CABLE_DIA = 9.7 + SLIDING_FIT_CLEARANCE_MM
LED_HOLE_DIA = 5.0 - 0.15        # press fit, 5 mm LED


def roller_positions() -> list[tuple[float, float, float]]:
    """(x, y, azimuth_deg) of each roller axle centre, at Z_AXLE."""
    return [
        (ROLLER_PITCH_R * math.cos(math.radians(a)),
         ROLLER_PITCH_R * math.sin(math.radians(a)), a)
        for a in ROLLER_AZIMUTHS
    ]


def race_band() -> tuple[float, float]:
    """Inner/outer radius the turntable's flat underside must cover."""
    return (ROLLER_PITCH_R - B608ZZ.radius, ROLLER_PITCH_R + B608ZZ.radius)


def breadboard_corner_r() -> float:
    """Radius of the breadboard's far corners — must stay inside INNER_R."""
    return math.hypot(BREADBOARD_X0 + BREADBOARD[0], BREADBOARD[1] / 2)
