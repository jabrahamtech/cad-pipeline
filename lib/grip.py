"""The gripper head (J6) - every number the grip_* parts share, in ONE place.

v4, 2026-09-29 (the cobot arm): the v3 mechanism, SHRUNK to the wrist -
stroke 20 -> 12.5 per jaw (25 at the jaw faces), 6 -> 5 rack teeth, and
the back bolts straight to the cobot rotator's O21 neck (lib/cobot ROT_*)
instead of the old O36 disc. Jonathan chose "Shrink head to match"; the
load table (specs/robotarm/cobot.md) wants it <= 40 g for J2's margin.

v3, 2026-09-29. Jonathan: "the gripper mechanism just seems so poorly
designed - could you go out and research what the best designs are", then
"I like arms that are more circular with polygonal lines for texture", and
chose ROD-GUIDED RACK AND PINION, 20 mm stroke per jaw kept (38 at the fingers).

WHAT THE RESEARCH SAID (specs/robotarm/grip.md has the sources)
----------------------------------------------------------------
* The good open parallel grippers (Source Robotics SSG-48, Techniccontroller's
  SG90 gripper) are rack and pinion: one pinion, two racks, jaws centred and
  parallel, linear stroke per degree. Linkages were rejected by both for
  non-linear, arcing jaw paths.
* What separates the good ones is GUIDANCE. SSG-48 runs its jaws on proper
  linear guides; the cheap ones slide a printed rack in a printed channel,
  which binds, wears and lets the rack lift off the pinion under load.
* Fin Ray TPU fingers (SO-101's compliant option, XLeRobot) are the proven
  way to grip odd shapes with a weak servo. Kept.

WHAT v3 CHANGES FROM v2 (grip_shell x2 + grip_jaw)
---------------------------------------------------
* EACH RACK RIDES ON TWO O3 STEEL RODS running through its own full length,
  one in front of the pinion and one behind it. Two rods, not one: a bar on
  a single rod is free to ROLL about it, and the gear's separating force
  and any load on the finger both try to roll it - into the pinion or out
  of mesh. Two rods fix the rack's centre distance exactly and nothing
  slides plastic-on-plastic. The rods sit BESIDE the pinion (in y), not
  above the teeth, which is what keeps the head 64 wide and not 70.
* ONE-PIECE BODY (grip_body), a 12-sided prism round the roll axis - the
  base's dodecagon, again. Open front cup: servo, pinion, jaws and rods all
  go in from the front, in that order, and the rods push in through the side
  walls. No clamshell, no clamp bolts.
* The jaw is one part, printed twice; the second turned over (180 deg about
  y). 6 teeth instead of 8 - exactly the stroke plus one pitch of mesh at
  each end, because every millimetre of rack is a millimetre of head width.

Frame, the head's own (unchanged): origin on the pinion axis in its MID plane.
  x  jaw opening direction, 0 on the centre plane
  y  forward, along the arm - the pinion and servo shaft lie on it
  z  up; jaw A's rack is above the pinion (z > 0), jaw B's below

Provenance: SG90 numbers are lib/servo; the gear block is gripper_pinion's
gr_* contract; fits are design_rules. ASSUMED values are tagged.
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
import lib.cobot as _C  # noqa: E402

SERVO = servo_for('J6')                  # SG90

# --- the gear contract: IDENTICAL to the gr_* block in gripper_pinion.py ---
GR_MODULE = 1.5
GR_TEETH = 12
GR_PA_DEG = 20.0
GR_DED_F = 1.25
GR_FACE = 8.0
GR_BACKLASH = 0.2
GR_STROKE = 12.5                         # per rack: opening 0..25 at the jaw faces (v4; v3 was 20)
GR_RACK_WEB = 3.5
R_PITCH = GR_MODULE * GR_TEETH / 2.0     # 9.0
OFFSET = R_PITCH + GR_BACKLASH           # 9.2 - pinion axis to rack pitch line
R_TIP = R_PITCH + GR_MODULE              # 10.5
ADD = GR_MODULE
DED = GR_MODULE * GR_DED_F
PITCH = GR_MODULE * math.pi
TIP_Z = OFFSET - ADD                     # 7.70  rack tooth tips (jaw A)
ROOT_Z = OFFSET + DED                    # 11.075

HUB = spline_hub(SERVO, face=GR_FACE)

# --- fits (design_rules) ---
EF = _EF
FREE = _FIT['free']
LOC = _FIT['locational']
SLIDE = _FIT['sliding']
WALL = _MIN_WALL
M2 = _FASTENER['M2']
M3 = _FASTENER['M3']

# --- the rack: only as long as the stroke needs ---
# Mesh margin: one pitch of teeth beyond the contact point at BOTH ends of
# travel. Closed (s = 0) the contact is at rack x = 0, open (s = 20) at -20.
RACK_TEETH = 5
X_A = -(GR_STROKE + PITCH)               # -24.71  toothed run starts
X_B = X_A + RACK_TEETH * PITCH           # +3.56   toothed run ends
END_LEAD = 0.5
X_LO = X_A - END_LEAD                    # -25.21  bar end
TIE_THK = 6.0                            # CHOSEN - the tie to the arm, in x; also the bar's +x end

# --- the guide rods: two O3 steel rods per rack, either side of the pinion ---
ROD_D = 3.0                              # BOUGHT - O3 ground / silver steel rod
ROD_BORE = 3.5   # ASSUMED - drawn; this printer's small holes print 0.1-0.3
                 # under (gauge_broach_v2), so ~3.3 printed: a free slide
ROD_PRESS = 3.0  # ASSUMED - drawn line-to-line; prints under = a press fit.
                 # Each rod passes through BOTH side walls: a slip hole in
                 # one, this press hole in the other, pressed flush.
BAR_GAP = 0.5    # CHOSEN - the rod blocks' inner faces stand this far off the pinion faces
ROD_Y = GR_FACE / 2.0 + BAR_GAP + WALL + ROD_BORE / 2.0   # 7.85  rods at y = +-this
BAR_Y = ROD_Y + ROD_BORE / 2.0 + WALL                 # 11.2  bar half depth in y

# --- along y: the stack from the pinion back to the servo ---
PINION_BACK_Y = -GR_FACE / 2.0                       # -4.0
TAB_Y = PINION_BACK_Y - HUB.seat_z                   # -11.1  servo datum
CASE_TOP_Y = TAB_Y + SERVO.tab_thk + SERVO.tab_below_top   # -4.4
CASE_BOT_Y = CASE_TOP_Y - SERVO.case_h               # -28.1
CASE_NEAR = -SERVO.shaft_from_end                    # -6.1  shaft end (lead end)
CASE_FAR = SERVO.case_l - SERVO.shaft_from_end       # 16.6
TAB_OVER = (SERVO.tab_span - SERVO.case_l) / 2.0     # 4.8
TAB_HOLE_X = ((CASE_NEAR + CASE_FAR) / 2.0 - SERVO.tab_hole_pitch / 2.0,
              (CASE_NEAR + CASE_FAR) / 2.0 + SERVO.tab_hole_pitch / 2.0)
TAB_SCREW_L = 8.0    # M2 x 8 self-tapper, the SG90's own bag screw
LEAD_Y = TAB_Y + SERVO.lead_z                        # where the bundle leaves
LEAD_R = SERVO.lead_bundle_dia / 2.0 + LOC
# the bar's rod blocks run beside the pinion and over the servo case, so
# their underside clears the case (and its pocket) by a free fit
EXT_Z0 = SERVO.case_w / 2.0 + LOC / 2.0 + FREE       # 6.7
ROD_Z = EXT_Z0 + WALL + ROD_BORE / 2.0               # 10.05 rod centre height
BAR_TOP = max(ROOT_Z + GR_RACK_WEB / 2.0, ROD_Z + ROD_BORE / 2.0 + WALL)  # 13.4

# --- the body: an open-fronted 12-sided cup round the roll axis ---
SERVO_SLOT_X1 = CASE_FAR + TAB_OVER + LOC / 2.0          # 21.5 - the servo's way in, v4
CORE_Y0 = PINION_BACK_Y - FREE                       # -4.4  full-width cavity floor
CAV_Y0 = -BAR_Y - FREE                               # -11.6 floor of the two SLABS the
                                                     #       bars' rear rod blocks run in
                                                     #       (|z| >= EXT_Z0 - FREE only, so the
                                                     #       servo's tab ledge survives between)
RIM_Y = BAR_Y + FREE                                 # 11.6  the cup's front rim
W_IN = max(TIE_THK + GR_STROKE, -X_LO) + FREE        # 26.4  cavity half width in x
Z_IN = BAR_TOP + FREE                                # 13.7  cavity half height
BODY_WALL = 2.4      # CHOSEN - at the cavity corners, the thinnest place
SIDES = 12
VERTEX_AZ0 = 0.0     # a VERTEX on the x axis: the widest point is where the
                     # racks run, and the flats meet the cavity corners
_normals = [math.radians(VERTEX_AZ0 + 180.0 / SIDES + 360.0 / SIDES * k) for k in range(SIDES)]
A_OUT = math.ceil(2 * (max(W_IN * abs(math.cos(a)) + Z_IN * abs(math.sin(a)) for a in _normals)
                       + BODY_WALL)) / 2.0       # outer apothem, rounded up to 0.5
R_OUT = A_OUT / math.cos(math.pi / SIDES)            # outer vertex radius
BACK_CHAMFER = 13.0  # CHOSEN - the back tapers down to a O25 face on the O21 neck
FRONT_FACET = 1.5    # CHOSEN - the rim's outer edge
# the back bolts to the cobot rotator's NECK: 4 x M3 self-tap pilots on r 7
EFF_BOLT_R = _C.ROT_BOLT_R
EFF_BOLT_AZ = _C.ROT_BOLT_AZ
EFF_SCREW_L = 8.0    # M3 x 8 into the neck's pilots
EFF_CBORE_D = 6.2    # passes the O5.5 head the whole way from the front
EFF_CBORE_H = 3.2
BACK_WALL_T = EFF_CBORE_H + 3.6                      # 6.8
ROTATOR_INSERT_DEEP = _C.ROT_PILOT_DEEP
SHELL_BACK_Y = CASE_BOT_Y - LOC / 2.0 - BACK_WALL_T  # -35.0 = the rotator face
ROTATOR_D = _C.ROT_NECK_D


def x_outer(z):
    """The body's outer x at height z (0 <= z <= the first vertex above the x axis)."""
    v1z = R_OUT * math.sin(math.radians(VERTEX_AZ0 + 360.0 / SIDES))
    v1x = R_OUT * math.cos(math.radians(VERTEX_AZ0 + 360.0 / SIDES))
    return R_OUT + (v1x - R_OUT) * z / v1z


# --- lightening: the 12-gon round a 53 x 27 cup is mostly solid, ~100 cm3 ---
# Three hollows, all printable back face down with no support:
#  * two LUNES above and below the cup, inside the 12-gon inset BODY_WALL,
#    from behind the back taper to a BODY_WALL skin under the rim - the roof
#    is a ~13 mm bridge across z
#  * the SLABS deepened back to the same floor, keeping BODY_WALL round the
#    servo pocket - they open into the cup
#  * a SIDE POCKET at -x beyond the tab ledge, also open into the cup
LIGHT_Y0 = SHELL_BACK_Y + BACK_CHAMFER + BODY_WALL   # -24.6 hollow floor
LIGHT_Y1 = RIM_Y - BODY_WALL                         # 9.2   the lunes' front skin
LUNE_Z0 = Z_IN + BODY_WALL                           # 16.1  lune floor, over the cup roof
A_LUNE = A_OUT - BODY_WALL                           # 29.1  lune outer apothem
SLAB_DEEP_Z0 = SERVO.case_w / 2.0 + LOC / 2.0 + BODY_WALL   # 8.6
SIDE_X1 = CASE_NEAR - TAB_OVER - LOC / 2.0 - BODY_WALL      # -13.4


def dodecagon(r):
    """The body's outline on XZ, mm: SIDES vertices at radius r, one on +x."""
    return [(r * math.cos(math.radians(VERTEX_AZ0 + 360.0 / SIDES * k)),
             r * math.sin(math.radians(VERTEX_AZ0 + 360.0 / SIDES * k))) for k in range(SIDES)]


def lune_outline():
    """The upper lune on XZ, mm: the 12-gon inset to A_LUNE, clipped at
    z >= LUNE_Z0. Mirror z for the lower one."""
    ring = dodecagon(A_LUNE / math.cos(math.pi / SIDES))
    out = []
    for k in range(SIDES):
        (x0, z0), (x1, z1) = ring[k], ring[(k + 1) % SIDES]
        if z0 >= LUNE_Z0:
            out.append((x0, z0))
        if (z0 - LUNE_Z0) * (z1 - LUNE_Z0) < 0:
            t = (LUNE_Z0 - z0) / (z1 - z0)
            out.append((x0 + t * (x1 - x0), LUNE_Z0))
    return out


# the rod: through both side walls, a hair short of both outer faces
ROD_RECESS = 0.2
ROD_L = math.floor(2 * (2 * x_outer(ROD_Z) - 2 * ROD_RECESS)) / 2.0
ROD_X0 = -ROD_L / 2.0

# --- the jaw ---
PIN_SCREW_STACK = 2.6    # ASSUMED - SG90 horn screw washer 0.8 + pan head 1.8
ARM_Y0 = RIM_Y + FREE                                # 10.4  the arm stands in front of the rim
ARM_THK = 9.0            # jaw arm, in x
ARM_D = 10.0             # jaw arm, in y - carries the finger
FINGER_Y0 = ARM_Y0 + ARM_D                           # 20.4 finger base

# --- the finger (TPU 95A) - grip_finger, unchanged ---
FINGER_H = 16.0          # in z, centred on z = 0
FINGER_LEAD = 1.0        # grip face stands this proud of the jaw face
S_TOUCH = FINGER_LEAD    # stroke at which the fingers first touch
FINGER_L = 40.0          # base to tip
FINGER_BASE_D = 5.0
FINGER_B = ARM_THK + FINGER_LEAD                     # base width in x, 10.0
GRIP_BEAM = 1.6
BACK_BEAM = 1.2
RIB_T = 1.0
RIBS = 4
TIP_T = 4.0
TIP_SOLID = 4.0
GROOVE_W = 0.8
GROOVE_D = 0.5
GROOVE_PITCH = 2.4
FINGER_SCREW_Z = 4.0
FINGER_SCREW_X = FINGER_LEAD + ARM_THK / 2.0         # finger-local
FINGER_SCREW_L = 16.0    # M3 x 16 from the jaw's back, into a nut in the finger
NUT_T = 2.4
FINGER_CBORE_H = 3.2
HEX_AF = M3['nut_af'] + 0.2                          # the finger's nut pocket
TPU_DENSITY = 1.21
PETG_PRINTED_G_PER_MM3 = 1.27 * 0.65 / 1000.0
TPU_PRINTED_G_PER_MM3 = TPU_DENSITY * 0.9 / 1000.0


def s_to_phase(s_mm):
    """Pinion rotation (rad, about its own +Z) that meshes BOTH racks at rack
    travel s. The pinion tooth meets the upper rack at x = r (psi + pi/2), and
    the rack's space centres sit at X_A + s (mod p). Even tooth count, so one
    angle serves the lower rack too."""
    assert GR_TEETH % 2 == 0, 'pinion tooth count must be even'
    return -math.pi / 2.0 + (X_A + s_mm) / R_PITCH


def check():
    """The contracts, in millimetres. Every grip_* script calls this."""
    # mesh: one pitch of teeth past the contact at both ends of travel
    assert X_A <= -GR_STROKE - PITCH + 1e-9, 'the rack runs off the pinion at full open'
    assert X_B >= PITCH / 2.0, 'the rack runs off the pinion at closed'
    assert TIP_Z - (R_PITCH - DED) >= 0.25 * GR_MODULE - 1e-9
    # the rod blocks stand clear of the pinion faces, with a wall inside the bore
    assert ROD_Y - ROD_BORE / 2.0 - WALL >= GR_FACE / 2.0 + BAR_GAP - 1e-9
    assert ROOT_Z >= R_TIP + FREE - 1e-9, 'the web over the pinion would touch its tips'
    assert ROD_BORE > ROD_D and ROD_PRESS <= ROD_D
    # ... and ride over the servo case, which runs under them
    assert EXT_Z0 >= SERVO.case_w / 2.0 + LOC / 2.0 + FREE - 1e-9
    assert EXT_Z0 < TIP_Z, 'the rod blocks would hang below the tooth tips'
    # the racks stay inside the cavity over the whole stroke, both ends
    assert TIE_THK + GR_STROKE <= W_IN - FREE + 1e-9
    assert -X_LO <= W_IN - FREE + 1e-9
    # every cavity corner keeps BODY_WALL to the outer 12-gon
    for a in _normals:
        assert A_OUT - (W_IN * abs(math.cos(a)) + Z_IN * abs(math.sin(a))) >= BODY_WALL - 1e-9
    # the rod stays inside both outer faces and fills both walls
    assert ROD_L / 2.0 <= x_outer(ROD_Z) - ROD_RECESS + 1e-9
    assert ROD_L / 2.0 >= x_outer(ROD_Z) - 1.0, 'the rod stops well short of a wall face'
    assert x_outer(ROD_Z) - W_IN >= 2 * WALL, 'the side wall is too thin to hold a rod'
    # the servo case reaches up into the cavity, under the bars' rod blocks
    assert SERVO.case_w / 2.0 + LOC / 2.0 <= EXT_Z0 - FREE + 1e-9
    # v4: the cup is sized by the racks, not the servo. The SG90 (tabs to
    # x 21.4) goes in through a SERVO SLOT in the cup at |z| <= its half
    # height, out past W_IN - the racks run above and below that band
    assert SERVO_SLOT_X1 + BODY_WALL <= x_outer(SERVO.case_w / 2.0 + LOC / 2.0), 'the servo slot breaks the wall'
    assert SERVO.case_w / 2.0 + LOC / 2.0 <= TIP_Z - FREE, 'the servo slot reaches the racks'
    assert ROD_Z - ROD_BORE / 2.0 - WALL >= SERVO.case_w / 2.0 + LOC / 2.0, 'the slot cuts a rod hole'
    # the rotator screws: counterbores inside the back face after the chamfer,
    # clear of the pinion, and they bite without bottoming
    assert EFF_BOLT_R + EFF_CBORE_D / 2 + WALL <= A_OUT - BACK_CHAMFER
    # the neck screws lie UNDER the servo: they are driven through the EMPTY
    # pocket, before the servo goes in (their access bores run up beside it,
    # through the pocket walls into the slabs)
    for az in EFF_BOLT_AZ:
        bx, bz = EFF_BOLT_R * math.cos(math.radians(az)), EFF_BOLT_R * math.sin(math.radians(az))
        for hx in TAB_HOLE_X:
            assert math.hypot(bx - hx, bz) >= EFF_CBORE_D / 2 + M2['pilot'] / 2 + WALL, 'neck screw on a tab pilot'
        # the rods are held only in the side walls (|x| > W_IN); inside, they run in the slab void
        assert abs(bx) + EFF_CBORE_D / 2 + WALL <= W_IN, 'a neck screw bore reaches a side wall'
    # the head clears the forearm's J4 end: nothing wider than the wrist nearer J4 than r 24.2
    assert A_OUT - BACK_CHAMFER <= _C.ROT_NECK_D / 2 + 2.0, 'the back face is much wider than the neck'
    bite = EFF_SCREW_L - (BACK_WALL_T - EFF_CBORE_H)
    assert 3.0 <= bite <= ROTATOR_INSERT_DEEP - FREE, bite
    # the hollows keep their walls: to the back taper, the rim facet, the cup
    # roof, the servo pocket and the tab ledge
    assert ((A_OUT - BACK_CHAMFER) + (LIGHT_Y0 - SHELL_BACK_Y) - A_LUNE) / math.sqrt(2) >= BODY_WALL - 1e-9
    assert (A_OUT + RIM_Y - FRONT_FACET - A_LUNE - LIGHT_Y1) / math.sqrt(2) >= WALL - 1e-9
    assert LUNE_Z0 - Z_IN >= BODY_WALL - 1e-9 and LIGHT_Y1 > LIGHT_Y0
    assert LIGHT_Y0 > CASE_BOT_Y - LOC / 2.0 - EFF_CBORE_H, 'the floor would cut the screw-head seats'
    assert len(lune_outline()) >= 3
    assert SIDE_X1 > -W_IN + BODY_WALL
    # the arm clears the pinion screw stack, and the bars clear its washer
    assert ARM_Y0 >= PINION_BACK_Y + GR_FACE + PIN_SCREW_STACK
    assert EXT_Z0 >= HUB.washer_d / 2.0 + FREE
    # the servo tabs sit in the central band, under the slabs, on a ledge
    assert SERVO.case_w / 2.0 + LOC / 2.0 <= EXT_Z0 - FREE + 1e-9
    # the finger screw passes its nut
    through = FINGER_SCREW_L - (ARM_D - FINGER_CBORE_H)
    assert through >= FINGER_BASE_D + 0.5, 'the finger screw stops short of the nut'
    assert RIB_T >= 0.8 and GRIP_BEAM >= 1.2
    return True


check()
