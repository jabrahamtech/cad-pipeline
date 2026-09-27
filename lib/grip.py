"""The gripper head (J6) - every number the grip_* parts share, in ONE place.

Jonathan, 2026-09-27: "finish the gripper as well - I think it needs a pretty
huge redesign", then "doesn't need to have cutter" and "keep the SG90". So
this is a GRIPPER, not the pruner, driven by the SG90 already on J6.

WHAT CHANGED FROM gripper_shell / gripper_rack_jaw, AND WHY
-----------------------------------------------------------
Kept, because it is the one mechanism in the head that was gated: an SG90
turns ONE 12T pinion bored onto its spline (gripper_pinion, reused
unchanged), which drives TWO racks in opposite directions. One printed
jaw design, the second turned over.

Replaced:
  * RIGID V-BLADE JAWS -> TPU FIN RAY FINGERS (grip_finger). A fin ray
    finger wraps an object it is pressed on - the tip curls toward the load
    - so one parallel stroke holds a stem, a pot rim or a pen without a
    shaped jaw for each. It is also the force limiter an SG90 needs: the
    finger deflects instead of the servo stalling.
  * THE RACK COULD WALK OUT OF MESH. The old channel had no front wall,
    because the jaw arm swept everything forward of it; nothing stopped a
    pull on the jaw sliding the rack forward off the pinion. Here the jaw
    arm stands IN FRONT of the shell and reaches in through a slot, so the
    channel keeps a front lip under the rack's teeth over its whole length.
  * THE HEAD COULD NOT BE BOLTED ON. The rotator takes M3 screws from the
    head side, and inside a closed clamshell there is no way to reach them.
    grip_mount is a plate that bolts to the rotator ON ITS OWN, and the two
    shell halves then clamp around it on the same three clamshell bolts.
  * ONE HEX POCKET SERVES HEAD OR NUT, the wrist_roll trick: the two halves
    are one design turned over, so every bolt hole needs a head recess on
    one half and a nut trap on the other at the SAME spot. A 5.7 af hex
    takes both an M3 nut and a O5.5 socket head.

Frame, the head's own: origin on the pinion axis in its MID plane.
  x  jaw opening direction, 0 on the centre plane
  y  forward, along the arm - the pinion and servo shaft lie on it
  z  the clamshell split; shell half A is z >= 0, B is A turned over

Provenance: SG90 numbers are lib/servo DATASHEET (gauge the tab plate);
the gear block is gripper_pinion's gr_* contract; fits are design_rules.
Anything else is tagged.
"""

import math

from lib.design_rules import FASTENER_MM as _FASTENER
from lib.design_rules import JOINT_FIT_MM as _FIT
from lib.design_rules import MIN_WALL_MM as _MIN_WALL
from lib.design_rules import ELEPHANT_FOOT_CHAMFER_MM as _EF
from lib.joints import servo_for
# IMPORT ORDER IS LOAD-BEARING: lib.gears <-> lib.servo_hub cycle.
import lib.gears  # noqa: F401,E402
from lib.servo_hub import spline_hub  # noqa: E402

SERVO = servo_for('J6')                  # SG90

# --- the gear contract: IDENTICAL to the gr_* block in gripper_pinion.py ---
# A shared Fusion parameter given a different value in one file reshapes
# every part already built (fusion/PLAYBOOK.md trap 7). The grip_* scripts
# write these into gr_* and assert against whatever is already there.
GR_MODULE = 1.5
GR_TEETH = 12
GR_PA_DEG = 20.0
GR_DED_F = 1.25
GR_FACE = 8.0
GR_BACKLASH = 0.2
GR_STROKE = 20.0                         # per rack: opening 0..40 at the jaws
GR_RACK_WEB = 3.5
R_PITCH = GR_MODULE * GR_TEETH / 2.0     # 9.0
OFFSET = R_PITCH + GR_BACKLASH           # 9.2 - pinion axis to rack pitch line
R_TIP = R_PITCH + GR_MODULE              # 10.5
ADD = GR_MODULE
DED = GR_MODULE * GR_DED_F
RACK_BACK = DED + GR_RACK_WEB            # 5.375 above the pitch line
PITCH = GR_MODULE * math.pi
RACK_TEETH = 8
TOOTH_LEAD = 8.0                         # toothed run reaches this far past the jaw face
END_LEAD = 3.0
X_B = TOOTH_LEAD
X_A = X_B - RACK_TEETH * PITCH           # -29.70: must be <= -stroke
X_LO = X_A - END_LEAD                    # -32.70
TIP_Z = OFFSET - ADD                     # 7.70  rack tooth tips (jaw A)
ROOT_Z = OFFSET + DED                    # 11.075
BACK_Z = OFFSET + RACK_BACK              # 14.575

HUB = spline_hub(SERVO, face=GR_FACE)

# --- fits (design_rules) ---
EF = _EF
FREE = _FIT['free']
LOC = _FIT['locational']
SLIDE = _FIT['sliding']
WALL = _MIN_WALL
M3 = _FASTENER['M3']

# --- along y: the stack from the pinion back to the servo ---
PINION_BACK_Y = -GR_FACE / 2.0                       # -4.0
TAB_Y = PINION_BACK_Y - HUB.seat_z                   # -11.1  servo datum
CASE_TOP_Y = TAB_Y + SERVO.tab_thk + SERVO.tab_below_top   # -4.4
CASE_BOT_Y = CASE_TOP_Y - SERVO.case_h               # -28.1
CASE_FAR = SERVO.case_l - SERVO.shaft_from_end       # 16.6
TAB_OVER = (SERVO.tab_span - SERVO.case_l) / 2.0     # 4.8
LEAD_Y = TAB_Y + SERVO.lead_z                        # where the bundle leaves

# --- the shell ---
CHAN_Y = GR_FACE / 2.0 + SLIDE / 2.0                 # 4.125 channel half width
CHAN_Z = BACK_Z + SLIDE / 2.0                        # 14.7  channel roof
TOP_T = 2.4          # CHOSEN - the roof over the channel; carries the facet
HALF_Z = CHAN_Z + TOP_T                              # 17.1
FRONT_T = WALL                                       # front lip under the teeth
SHELL_FRONT_Y = CHAN_Y + FRONT_T                     # 5.725
FACET = TOP_T + 0.6  # 3.0 - _style.md rule 1, scaled to the 2.4 roof it cuts
                     # (a 4.0 facet on a 2.4 roof over the open channel
                     # leaves a knife edge; 3.0 bevels it cleanly)
X_HALF = 26.5        # CHOSEN - see the clamshell bolts, below
REAR_X = 22.0        # _style.md rule 3: tapers into the wrist
TAPER_Y = -22.0      # where the taper starts
HEX_AF = M3['nut_af'] + 0.2                          # 5.7: an M3 nut OR a O5.5 head
HEX_DEEP = 4.0       # CHOSEN - nut at the floor, M3 x 30 lands flush (asserted)
CLAMP_L = 30.0       # M3 x 30 socket cap, two of them
BOLT_FRONT_X = 20.2  # clear of the servo pocket by a wall, of the facet by the hex
BOLT_FRONT_Y = -18.5
CAVITY_Z0 = SERVO.case_w / 2.0 + LOC / 2.0 + WALL    # lightening over the servo
TIE_SLOT_Z0 = ROOT_Z - FREE                          # the tie passes the front lip here

# --- the rotator interface: wrist_rotator.py wro_bolt_x / wro_bolt_z ---
# NO ADAPTER PLATE. Each half's BACK WALL carries two of the four M3s, head
# in a counterbore, driven with a long 2.5 hex key down an access bore from
# the front - which is open until the jaws slide in from the sides. The
# rotator then also clamps the two halves together at the rear.
EFF_BOLT_X = 11.0
EFF_BOLT_Z = 9.0
EFF_SCREW_L = 8.0    # M3 x 8 into the rotator's 5.5 deep insert holes
EFF_CBORE_D = 6.2    # passes the O5.5 head the whole way from the front
EFF_CBORE_H = 3.2
BACK_WALL_T = EFF_CBORE_H + 3.6                      # 6.8
ROTATOR_INSERT_DEEP = 5.5
SHELL_BACK_Y = CASE_BOT_Y - LOC / 2.0 - BACK_WALL_T  # -35.0 = the rotator face

# --- the jaw ---
PIN_SCREW_STACK = 2.6    # ASSUMED - SG90 horn screw washer 0.8 + pan head 1.8
ARM_Y0 = PINION_BACK_Y + GR_FACE + PIN_SCREW_STACK + FREE   # 7.0
ARM_THK = 9.0            # jaw arm, in x
ARM_D = 10.0             # jaw arm, in y - carries the finger
TIE_THK = 6.0            # the tie from rack to arm, in x
FINGER_Y0 = ARM_Y0 + ARM_D                           # 17.0 finger base

# --- the finger (TPU 95A) ---
FINGER_H = 16.0          # in z, centred on the split plane
FINGER_LEAD = 1.0        # grip face stands this proud of the jaw face
S_TOUCH = FINGER_LEAD    # stroke at which the fingers first touch
FINGER_L = 40.0          # base to tip
FINGER_BASE_D = 5.0
FINGER_B = ARM_THK + FINGER_LEAD                     # base width in x, 10.0
GRIP_BEAM = 1.6          # HANDBOOK fin ray: grip face beam in TPU 95A
BACK_BEAM = 1.2
RIB_T = 1.0
RIBS = 4
TIP_T = 4.0              # tip width, where the two beams meet
TIP_SOLID = 4.0
GROOVE_W = 0.8           # grip texture across z
GROOVE_D = 0.5
GROOVE_PITCH = 2.4
FINGER_SCREW_Z = 4.0
FINGER_SCREW_X = FINGER_LEAD + ARM_THK / 2.0         # finger-local
FINGER_SCREW_L = 16.0    # M3 x 16 from the jaw's back, into a nut in the finger
NUT_T = 2.4              # M3 nut, DIN 934
FINGER_CBORE_H = 3.2
TPU_DENSITY = 1.21       # g/cm3 - TPU 95A, DATASHEET typical
PETG_PRINTED_G_PER_MM3 = 1.27 * 0.65 / 1000.0   # lib/arm_loads SOLID_TO_PRINTED
TPU_PRINTED_G_PER_MM3 = TPU_DENSITY * 0.9 / 1000.0   # ASSUMED: thin walls print ~solid


def s_to_phase(s_mm):
    """Pinion rotation (rad, about its own +Z) that meshes BOTH racks at rack
    travel s. Verbatim the derivation in _check_fit.phase_angle: a pinion
    tooth meets the upper rack at x = r (psi + pi/2), and the rack's space
    centres sit at X_A + s (mod p). Even tooth count, so one angle serves
    the lower rack too."""
    assert GR_TEETH % 2 == 0, 'pinion tooth count must be even'
    return -math.pi / 2.0 + (X_A + s_mm) / R_PITCH


def check():
    """The contracts, in millimetres. Every grip_* script calls this."""
    assert X_A <= -GR_STROKE, 'the rack runs off the pinion at full open'
    assert X_B >= S_TOUCH, 'the rack runs off the pinion at closed'
    # the rack tip clears the pinion root and the tie clears the pinion tip
    assert TIP_Z - (R_PITCH - DED) >= 0.25 * GR_MODULE - 1e-9
    assert ROOT_Z - R_TIP >= 0.25 * GR_MODULE - 1e-9, (
        'the tie runs at z %.2f and the pinion tips reach %.2f' % (ROOT_Z, R_TIP))
    assert TIE_SLOT_Z0 - TIP_Z >= WALL - 1e-9, (
        'the front lip under the teeth is only %.2f tall' % (TIE_SLOT_Z0 - TIP_Z))
    # the servo sits behind the channel and inside the shell
    assert CASE_TOP_Y < -CHAN_Y, 'the SG90 case top stands in the rack channel'
    assert CASE_FAR + TAB_OVER + LOC / 2 + WALL <= X_HALF, 'the tabs leave the shell'
    # the front clamshell bolt: a wall from the servo pocket, and its hex
    # clear of the top facet
    assert BOLT_FRONT_X - M3['clearance'] / 2 - (CASE_FAR + LOC / 2) >= WALL - 1e-9
    assert BOLT_FRONT_X + HEX_AF / math.sqrt(3) <= X_HALF - FACET + 1e-9, (
        'the front bolt hex breaks into the top facet')
    assert BOLT_FRONT_Y + M3['clearance'] / 2 <= TAB_Y - LOC / 2 - WALL, (
        'the front bolt runs into the far tab slot')
    lead_top = LEAD_Y + SERVO.lead_bundle_dia / 2 + LOC
    assert BOLT_FRONT_Y - M3['clearance'] / 2 - lead_top >= WALL - 1e-9, (
        'the clamp bolt runs into the lead notch')
    # the rotator screw counterbores stay inside the shell and clear the pinion
    assert EFF_BOLT_Z + EFF_CBORE_D / 2 + WALL <= HALF_Z
    assert math.hypot(EFF_BOLT_X, EFF_BOLT_Z) - EFF_CBORE_D / 2 >= R_TIP + FREE
    assert EFF_BOLT_X + EFF_CBORE_D / 2 + WALL <= REAR_X
    # every clamshell bolt reaches through its nut and not past the face
    grip = 2 * HALF_Z - 2 * HEX_DEEP
    assert grip + NUT_T <= CLAMP_L <= 2 * HALF_Z - HEX_DEEP + 1e-9, (
        'an M3 x %.0f through %.1f of shell: it must pass the nut and stay '
        'below the far face' % (CLAMP_L, 2 * HALF_Z))
    # the rotator screws bite and do not bottom
    bite = EFF_SCREW_L - (BACK_WALL_T - EFF_CBORE_H)
    assert 3.0 <= bite <= ROTATOR_INSERT_DEEP - FREE, bite
    # the jaw arm clears the pinion screw and the shell front
    assert ARM_Y0 >= SHELL_FRONT_Y + FREE - 1e-9
    # the finger screw passes its nut
    through = FINGER_SCREW_L - (ARM_D - FINGER_CBORE_H)
    assert through >= FINGER_BASE_D + 0.5, 'the finger screw stops short of the nut'
    # fins: the first cell holds the nut; a rib is a printable wall
    assert RIB_T >= 0.8 and GRIP_BEAM >= 1.2
    return True


check()
