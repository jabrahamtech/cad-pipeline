"""The cobot arm (2026-09-29) - every number the cobot_* parts share, in ONE place.

Jonathan, 2026-09-29: "no i mean like complete redesign" -> the myCobot 280 /
UFactory Lite 6 layout ("I am liking this more and more"): 12-gon CAPSULE
links lying side by side, servos INSIDE, no forks. Then: "work out how the
parts go together - how the motors are placed with the correct tolerances -
how the cables are managed - minimise the likelihood of reprints ... like
the motor would have to teleport into position". Then: "improve the torque
at different parts using different types of gears" -> "cant you use gears
to just improve the torque rather than changing the motors" -> GEARS + JOINT
ENCODERS (AskUserQuestion, 2026-09-29).

Kept: the printed base_platter + base_lid, the whole J1 turntable, the
motors (J2-J4 now their 360 deg versions - same cases), reach 289.

WHY GEARS NEED ENCODERS HERE
----------------------------
A hobby servo's feedback pot is on ITS output, so a reduction after it
divides the joint's travel by the ratio (2:1 -> 90 deg). So J2-J4 run the
360 deg (continuous) versions of the same servos and the ESP32 closes the
loop on an AS5600 magnetic encoder ON THE JOINT: full range at any ratio.
Research (2026-09-29, specs/robotarm/cobot.md): at 1.5-4:1 inside 45-56 mm
links, SPUR stages are the right gear type - planetary, cycloidal, strain
wave and worm only pay off above ~10:1 with a multi-turn motor.

  J2  MG995 -> 22T/36T m1.25 face 20 (1.64:1). The MG995's stall through a
      printed pinion is what sizes this; 20 mm of face is the least that
      passes lib/gears' Lewis check.
  J3  SG90  -> TWO stages 18/36 + 18/36 m1 (4:1), a compound IDLER on a
      O3 steel pin. One 3:1 stage would need a O56 gear; two fit the link.
  J4  SG90  -> 18T/36T m1 (2:1).
  J5, gripper: position servos, direct, unchanged.

THE JOINT - one pattern at J2, J3, J4
-------------------------------------
Two links: S holds the servo, H is driven.
  * H carries a solid SPIGOT through a BORE in S's 3 mm JOINT WALL.
  * Inside S, the OUTPUT GEAR is bolted to the spigot end (heads sunk in
    its tooth face). Its FLANGE traps S's wall between itself and H's face,
    AX_GAP either side: the joint's axial bearing. The bending load goes into
    those two flat annuli, never into a servo shaft.
  * On the gear's axis a STALK carries the encoder MAGNET up into a hole in
    the SERVO PLATE, where the AS5600 board sits chip-down.
  * The SERVO PLATE is a BENCH UNIT: servo (+ its pinion, broached on and
    screwed) and the AS5600 board are fixed to it on the bench, then the
    whole plate drops into S along -x. The pinion meshes AXIALLY, the stalk
    enters the board's hole, and the plate screws onto posts that stand
    outside every gear sweep (asserted).

WHY NOTHING HAS TO TELEPORT
---------------------------
Every link is a BODY (joint wall + 12-gon shell, open on its +x face) plus
a COVER. Every insertion is along x through that open face, in this order:
spigot through bore -> output gear bolted -> (J3: idler on its pin) ->
servo plate unit -> cover. Every screw is driven along x from the open face.

CABLES
------
Every joint axis carries an encoder, so NO loom goes through a joint. Each
joint is crossed by a short SERVICE LOOP between two grommeted PORTS, one on
each link, close to the axis so the loop length changes least.

Frame: the arm frame at J1 yaw 0. x along the J2/J3/J4 axes, y forward, z up.
The TOOL PLANE is x = 0. In a link: u along it (from its first joint), v across.
"""

import math

from lib.design_rules import FASTENER_MM as _FASTENER
from lib.design_rules import JOINT_FIT_MM as _FIT
from lib.design_rules import MIN_WALL_MM as _MIN_WALL
import lib.gears as _gears  # noqa: F401 - import order: lib.gears before lib.servo_hub
from lib.gears import SpurPair
from lib.joints import JOINT_SERVO
from lib.servo import CATALOG
from lib.servo import MG995_TAB_HOLE_PITCH_Y
from lib.servo_hub import spline_hub
import lib.j1_drive as J1

FREE = _FIT['free']            # 0.40
ROT = _FIT['rotating']         # 0.35 diametral, a running journal
LOC = _FIT['locational']       # 0.20
MIN_WALL = _MIN_WALL           # 1.6
M3 = _FASTENER['M3']
M2 = _FASTENER['M2']
M3_HEAD_D = 5.5      # ISO 4762 M3 cap head - DATASHEET
M3_HEAD_H = 3.0
CBORE_D = M3_HEAD_D + FREE
CBORE_H = M3_HEAD_H + 0.2
EPS = 1e-9

SHELL = 2.0          # CHOSEN - every 12-gon outer wall: 5 perimeters at 0.4
JOINT_WALL = 3.0     # CHOSEN - S's wall in the joint (the bearing annulus)
AX_GAP = 0.25        # CHOSEN - axial running gap each side of that wall
FLANGE_T = 3.0       # CHOSEN - the output gear's flange (the retainer)
COVER_T = 2.0
PLATE_T = 3.0        # CHOSEN - a micro servo plate (M2 pilots)
PLATE2_T = 5.0       # CHOSEN - the MG995 plate (M3 pilots, 4.5 engaged)
PORT_D = 8.0         # CHOSEN - a grommeted cable port
LOOM_D = 6.0         # ASSUMED - 5 servo leads + 3 encoder signals + shared 3V3/GND, bundled
BOSS_R = 3.5         # CHOSEN - an M3 screw boss / post
SIDES = 12

# the 360 deg versions of these (MG995 360 as J1 already uses; SG90 360) -
# same cases, so the catalog dimensions hold. CALIPER each before printing.
MG995 = CATALOG[JOINT_SERVO['J2']]
SG90 = CATALOG[JOINT_SERVO['J4']]
KGCM_NM = 0.0980665

# --- the gear pairs -------------------------------------------------------------
J2_PAIR = SpurPair(name='cobot J2', module=1.25, z_pinion=22, z_gear=36, face=20.0)
J3A_PAIR = SpurPair(name='cobot J3 out', module=1.0, z_pinion=18, z_gear=36, face=12.0)
J3B_PAIR = SpurPair(name='cobot J3 in', module=1.0, z_pinion=18, z_gear=36, face=12.0)
J4_PAIR = SpurPair(name='cobot J4', module=1.0, z_pinion=18, z_gear=36, face=10.0)
MESH_ETA = 0.9       # ASSUMED per mesh, as lib/gears
J2_RATIO = J2_PAIR.ratio
J3_RATIO = J3A_PAIR.ratio * J3B_PAIR.ratio
J4_RATIO = J4_PAIR.ratio
# the stage-A pinion (the idler's 18T) sees the servo's stall x stage B
J3A_INPUT_NM = SG90.stall_kgcm * KGCM_NM * J3B_PAIR.ratio * MESH_ETA

PIN2_HUB = spline_hub(MG995, face=J2_PAIR.face)
PIN3_HUB = spline_hub(SG90, face=J3B_PAIR.face)
PIN4_HUB = spline_hub(SG90, face=J4_PAIR.face)
# the servo screw holds the pinion on the spline from its FRONT face. Each
# pinion is counterbored so a STANDARD screw reaches exactly the spline's
# engagement (SG90: M2.5 x 6; MG995: M3 x 8); on a pinion too short to need it
# the head stands in the flange layer in front of it (asserted)
PIN_SCREW_L = {'SG90': 6.0, 'MG995': 8.0}
PIN_SCREW_STACK = 2.6          # ASSUMED - washer 0.8 + pan head 1.8 (lib/grip)


def pinion_cbore(hub, face):
    """(depth, dia) of the screw counterbore in a pinion's front face; depth 0 = none."""
    floor = face - hub.broach_to
    want = PIN_SCREW_L[hub.servo_name] - hub.engaged
    return (max(floor - want, 0.0), hub.washer_d + FREE)


def pinion_screw_l(hub, face):
    depth, _ = pinion_cbore(hub, face)
    return face - hub.broach_to - depth + hub.engaged

IDLER_PIN_D = 3.0      # ISO 2338 / 8734 dowel O3 x 35 - the J3 idler's axle
IDLER_PIN_L = 35.0

# --- the encoder: AS5600 module + diametric magnet ------------------------------
# the common 23 x 23 AS5600 module (UMLIFE / Tinytronics AS5600MOD listings,
# 2026-09-29). Its hole positions are NOT published, so nothing depends on
# them: the board drops into a LOC pocket on the plate's top face, chip down
# over the stalk hole, and two M2 screws clamp its edges. SOLDER WIRES to its
# pads - no header. CALIPER the board before printing a plate.
BOARD = 23.0
BOARD_POCKET = BOARD + 2 * LOC
BOARD_POCKET_H = 1.0             # the board stands 0.6 proud: the clamp screws bite on it
BOARD_T = 1.6
CHIP_H = 1.5                     # SOIC-8 below the board
AIR_GAP = 1.0                    # magnet face -> chip (AS5600 wants 0.5-3)
MAGNET_D, MAGNET_H = 6.0, 2.5    # the O6 x 2.5 diametric magnet the modules ship with
MAGNET_POCKET = (MAGNET_D + 0.1, MAGNET_H + 0.1)   # glued
STALK_D = 10.0
STALK_HOLE_D = STALK_D + 2 * 1.0

# --- FITS AND TOLERANCES (Jonathan, 2026-09-29: "make sure gears fit correctly in
# housing and instalations and tolerances are taken into account") ----------
# A printed spur mesh has 0.2 of backlash at its centre distance (lib/gears).
# Everything that can move a pinion's axis relative to its gear's eats into
# that, and past it the mesh JAMS. The chain, per source (radial, +-, mm):
POS_TOL = 0.10        # ASSUMED X2D - one printed feature placed relative to another in the same part
REG_PLAY = LOC / 2    # a LOC register (gear on spigot, plate on pin, servo in window)
JOINT_PLAY = ROT / 2  # the spigot running in its bore
PIN_PLAY = ROT / 2    # the idler on its pin
SPLINE_RUNOUT = 0.05  # ASSUMED - the servo output + broached pinion


def rss(*xs):
    return math.sqrt(sum(x * x for x in xs))


# the output gear is CENTRED on its spigot by a register boss (the bolts are
# only clamps - they sit in clearance holes and would let it float 0.2)
REG_D = 12.0          # the boss on the spigot end
REG_H = 1.5
REG_RECESS = (REG_D + LOC, REG_H + FREE)     # in the gear flange's bed face
# J2 and J4: the servo plate's screw holes are SLOTS along the mesh line, so
# the mesh is SET on assembly (0.1 paper between the teeth, push the plate
# into mesh, tighten, pull the paper) - no stack to eat the backlash
PLATE_SLOT = 0.6      # +- along the mesh line
# J3's two meshes are FIXED (the idler pin stands in the upper arm's wall and
# locates the J3 plate), so each gets its tolerance stack added to its centre
# distance - never tighter than the pair's own backlash
J3A_STACK = rss(POS_TOL, JOINT_PLAY, REG_PLAY, PIN_PLAY)          # pin boss <-> J3 bore, all in the upper arm
J3B_STACK = rss(POS_TOL, REG_PLAY, REG_PLAY, PIN_PLAY, SPLINE_RUNOUT)   # plate: pin hole <-> servo window
# every tooth end that SLIDES INTO MESH on assembly gets a 45 deg lead-in
LEAD_IN = 0.5

# --- kinematics, kept ---------------------------------------------------------
ROTOR_DISC_T = 5.0     # turntable_stator tt_disc_t - asserted against the document by cobot_tower
ROTOR_BOSS_H = 4.4     # turntable_stator tt_boss_h
BOSS_TOP = J1.TT_RACE_Z_MM + ROTOR_DISC_T + ROTOR_BOSS_H   # 33.5 above the rim top
J2_STAND = 38.0        # shoulder_bracket sb_stand_h: J2 above the boss top
J2_Z = BOSS_TOP + J2_STAND                                  # 71.5
L1 = 125.0
L2 = 45.0
ROT_SEAT = 15.7        # J4 -> the wrist's front face (wro_y_front)
ROT_FACE = 21.7        # J4 -> the rotator's front face = the gripper mount


def centre_distance(pair):
    return pair.centre_distance


def tip_r(pair, z):
    return pair.r_tip(z)


class GearJoint:
    """A geared cantilever joint, mm. H's face at x_face; S lies on +x.
    The output gear: FLANGE_T flange then `face` of teeth, bolted to the spigot."""

    def __init__(self, name, pair, spigot_od, overlap, bolt_r, bolt_az, x_face, spigot_id=0.0):
        self.name, self.pair = name, pair
        self.spigot_id, self.spigot_od = spigot_id, spigot_od
        self.bore = spigot_od + ROT
        self.flange_od = spigot_od + 2 * overlap
        self.bolt_r, self.bolt_az = bolt_r, bolt_az
        self.x_face = x_face
        self.x_wall0 = x_face + AX_GAP                       # S's joint wall
        self.x_wall1 = self.x_wall0 + JOINT_WALL
        self.x_spigot_end = self.x_wall1 + AX_GAP
        self.x_teeth0 = self.x_spigot_end + FLANGE_T
        self.x_gear_back = self.x_teeth0 + pair.face         # the output gear's back (tooth) face
        self.gear_h = FLANGE_T + pair.face
        self.gear_tip_r = pair.r_tip(pair.z_gear)
        self.gear_root_r = pair.r_root(pair.z_gear)
        self.keep_out_r = self.gear_tip_r + FREE             # nothing of S inside this, gear layers

    def check(self):
        pil = M3['pilot']
        assert self.bolt_r + pil / 2 + MIN_WALL <= self.spigot_od / 2 + EPS, self.name + ' bolts break the spigot'
        assert (self.flange_od - self.bore) / 2 >= 2.0, '%s: the flange barely laps the wall' % self.name
        assert self.flange_od / 2 <= self.gear_tip_r + EPS, self.name + ' flange proud of the teeth'
        # sunk heads: inside the roots, and a web to the stalk
        assert self.bolt_r + CBORE_D / 2 + MIN_WALL <= self.gear_root_r + EPS, self.name + ' head past the roots'
        assert self.bolt_r - CBORE_D / 2 - MIN_WALL >= STALK_D / 2 - EPS, self.name + ' head into the stalk'
        assert self.gear_h - CBORE_H >= 2 * MIN_WALL, self.name + ' too little gear under a head'
        return True

    def bolts(self):
        return [(self.bolt_r * math.cos(math.radians(a)), self.bolt_r * math.sin(math.radians(a)))
                for a in self.bolt_az]

    def bolt_engaged(self, length, h_side_extra):
        """M3 thread left in H past the spigot end: length minus the gear under the head."""
        return length - (self.gear_h - CBORE_H) - (self.x_spigot_end - self.x_face) - h_side_extra


def pinion_seat(joint_x_teeth0, pair):
    """A pinion's teeth span the gear's; the servo case top is FREE behind them."""
    return joint_x_teeth0 + pair.face + FREE


def case_box(servo, shaft_u, shaft_v, along):
    """(u0, u1, v0, v1) of the case, and of case + tabs, for an axis-aligned
    servo whose case runs from its shaft toward `along` (+-u or +-v)."""
    near, far = servo.shaft_from_end, servo.case_l - servo.shaft_from_end
    ext = (servo.tab_span - servo.case_l) / 2
    w = servo.case_w / 2
    du, dv = along
    if du:
        a, b = sorted((shaft_u - du * near, shaft_u + du * far))
        case = (a, b, shaft_v - w, shaft_v + w)
        tabs = (a - ext, b + ext, shaft_v - w, shaft_v + w)
    else:
        a, b = sorted((shaft_v - dv * near, shaft_v + dv * far))
        case = (shaft_u - w, shaft_u + w, a, b)
        tabs = (shaft_u - w, shaft_u + w, a - ext, b + ext)
    return case, tabs


def servo_holes(servo, shaft_u, shaft_v, along):
    """The tab-hole centres of a servo whose shaft is at (shaft_u, shaft_v)
    and whose case runs from the shaft toward `along` (a unit (du, dv)), mm."""
    c = servo.case_l / 2 - servo.shaft_from_end                 # shaft -> case centre
    cu, cv = shaft_u + along[0] * c, shaft_v + along[1] * c
    n = (-along[1], along[0])
    out = []
    for s in (-1, 1):
        for t in ((-1, 1) if servo.name == 'MG995' else (0,)):
            w = MG995_TAB_HOLE_PITCH_Y / 2 * t
            out.append((cu + along[0] * s * servo.tab_hole_pitch / 2 + n[0] * w,
                        cv + along[1] * s * servo.tab_hole_pitch / 2 + n[1] * w))
    return out


def rect_dist(p, box):
    """Distance from a point to an axis-aligned (u0, u1, v0, v1) box (0 inside)."""
    u0, u1, v0, v1 = box
    du = max(u0 - p[0], 0.0, p[0] - u1)
    dv = max(v0 - p[1], 0.0, p[1] - v1)
    return math.hypot(du, dv)


def box_gap(a, b):
    """Gap between two axis-aligned boxes (negative: overlap depth)."""
    du = max(a[0] - b[1], b[0] - a[1])
    dv = max(a[2] - b[3], b[2] - a[3])
    return max(du, dv)


def ring(a, cx=0.0, cy=0.0, az0_deg=180.0 / SIDES):
    """12-gon, apothem a, flats on the axes by default. (u, v) points."""
    r = a / math.cos(math.pi / SIDES)
    return [(cx + r * math.cos(math.radians(az0_deg + 360.0 / SIDES * k)),
             cy + r * math.sin(math.radians(az0_deg + 360.0 / SIDES * k))) for k in range(SIDES)]


def belly_ring(a):
    """ring(a) with the two lower diagonal vertices (225 and 315 deg) dropped:
    the facets either side merge into 45 deg chamfers, so a 12-gon lying on
    its side prints with no overhang shallower than 45 deg. For the tower's
    J2 drum, which prints with its axis horizontal."""
    pts = ring(a)
    drop = {round(math.radians(180.0 / SIDES + 360.0 / SIDES * k), 9) for k in (7, 10)}
    return [p for k, p in enumerate(pts)
            if round(math.radians(180.0 / SIDES + 360.0 / SIDES * k), 9) not in drop]


def hull(pts):
    pts = sorted(set((round(u, 9), round(v, 9)) for u, v in pts))

    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def capsule(a0, a1, length, inset=0.0):
    """A link's side outline: 12-gon ends of apothem a0 at u = 0 and a1 at
    u = length, joined by their hull. inset shrinks it (the inside of the shell)."""
    return hull(ring(a0 - inset) + ring(a1 - inset, cx=length))


def inside_capsule(p, a, length, margin):
    """True if a disc of radius `margin` about p lies inside a capsule(a, a, length):
    the capsule is the hull of two 12-gons, so test against the swept ring."""
    # a point is inside the hull if it is inside one of the end 12-gons or between
    # them with |v| <= a (flats on the axes)
    u, v = p
    if 0.0 <= u <= length:
        return abs(v) + margin <= a + EPS
    c = 0.0 if u < 0 else length
    ang = math.atan2(v, u - c)
    # apothem of a 12-gon along this direction (flats at 0, 30, 60 ... deg)
    k = (ang - math.pi / SIDES) % (2 * math.pi / SIDES) - math.pi / SIDES
    r_edge = a / math.cos(k)
    return math.hypot(u - c, v) + margin <= r_edge + EPS


# --- the 12-gon sizes (apothems) ------------------------------------------------
TW_A = 28.0          # the tower: column about J1, J2 drum about J2
UA_A = 28.0          # upper arm, both ends = the tower: the J2 gear (tip 23.75) + FREE + 1 + SHELL
FA_A = 23.0          # forearm, both ends: the J4 gear (tip 19) + FREE + 1 + SHELL = 22.4
WR_A = 25.0          # wrist drum
HEAD_A = 25.0        # the gripper head, shrunk to the wrist's size
UA_IN = UA_A - SHELL
FA_IN = FA_A - SHELL

# --- the x stack, from the tool plane outward ---------------------------------
WR_HALF = 11.0                          # the wrist clamshell, x -11..+11, split at x = 0
J4 = GearJoint('J4', J4_PAIR, spigot_od=28.0, overlap=2.5, bolt_r=11.0,
               bolt_az=(45.0, 135.0, 225.0, 315.0), x_face=WR_HALF)
J4_BOLT_L = 18.0                        # M3 x 18 - the wrist's J5 bay limits the pilot
FA_X0 = J4.x_wall0
FA_J4_CASE_TOP = pinion_seat(J4.x_teeth0, J4_PAIR)
FA_J4_TAB_TOP = FA_J4_CASE_TOP + SG90.tab_below_top          # the J4 plate's top face
FA_J4_PLATE_X0 = FA_J4_TAB_TOP - PLATE_T
# the forearm's +x plate is STRUCTURAL: it carries the J3 spigot. It is 5
# thick because the links are OFFSET: the upper arm's wall passes AX_GAP over
# this whole face as the elbow folds, so every head in it is counterbored
FA_PLATE_T = 5.0
FA_X1 = FA_J4_CASE_TOP + SG90.case_h + FREE + FA_PLATE_T

J3 = GearJoint('J3', J3A_PAIR, spigot_od=26.0, overlap=3.0, bolt_r=10.0,
               bolt_az=(120.0, 180.0, 240.0), x_face=FA_X1)
J3_BOLT_L = 30.0                        # M3 x 30: gear + spigot + forearm plate + 10 into a forearm boss
FA_J3_PILOT_DEPTH = 12.0
J2 = GearJoint('J2', J2_PAIR, spigot_od=36.0, overlap=3.0, bolt_r=15.0,
               bolt_az=(45.0, 135.0, 225.0, 315.0), x_face=FA_X1)
J2_BOLT_L = 30.0                        # M3 x 30 into the tower drum
TW_J2_PILOT_DEPTH = 10.0
UA_X0 = J2.x_wall0
# J3 stage B layer: behind stage A by FREE
J3B_X0 = J3.x_gear_back + FREE
J3B_X1 = J3B_X0 + J3B_PAIR.face
UA_J3_CASE_TOP = J3B_X1 + FREE
UA_J3_TAB_TOP = UA_J3_CASE_TOP + SG90.tab_below_top          # the J3 plate's top face
UA_J3_PLATE_X0 = UA_J3_TAB_TOP - PLATE_T
UA_J2_CASE_TOP = pinion_seat(J2.x_teeth0, J2_PAIR)
UA_J2_TAB_TOP = UA_J2_CASE_TOP + MG995.tab_below_top         # the J2 plate's top face
UA_J2_PLATE_X0 = UA_J2_TAB_TOP - PLATE2_T
UA_X1 = max(UA_J2_CASE_TOP + MG995.case_h, UA_J3_CASE_TOP + SG90.case_h) + FREE + COVER_T
TOWER_X1 = J2.x_face                    # the tower's +x face, where the J2 spigot stands

# the idler: its 18T in stage A's layer, its 36T in stage B's; a O3 pin from
# a blind hole in a wall boss up through the J3 plate
IDLER_X0 = J3.x_teeth0
IDLER_X1 = J3B_X1
IDLER_BOSS_TOP = IDLER_X0 - FREE
IDLER_PIN_BOTTOM = UA_X0 + MIN_WALL
IDLER_PIN_TOP = IDLER_PIN_BOTTOM + IDLER_PIN_L

# the stalk: magnet face AIR_GAP under the chip, the chip CHIP_H under the board
# that sits in its pocket on the plate's top face


def stalk_top(plate_top):
    """The magnet's face: the board sits BOARD_POCKET_H into the plate's top,
    its chip hangs CHIP_H below it inside the stalk hole, AIR_GAP to the magnet."""
    return plate_top - BOARD_POCKET_H - CHIP_H - AIR_GAP


# --- the layouts, in each S-link's (u, v) ----------------------------------------
# UPPER ARM: J2 at (0, 0), J3 at (L1, 0).
# J2: the MG995 lies along +u, off to -v so the J3 servo passes it at +v.
J2_SERVO_V = -6.5
J2_PIN = (math.sqrt(J2_PAIR.centre_distance ** 2 - J2_SERVO_V ** 2), J2_SERVO_V)
J2_CASE, J2_TABS = case_box(MG995, J2_PIN[0], J2_PIN[1], (1.0, 0.0))
J2_HOLES = servo_holes(MG995, J2_PIN[0], J2_PIN[1], (1.0, 0.0))
# J3: output on J3; the idler on the link line; the servo pinion off to +v,
# its SG90 lying along -u (toward J2) beside the MG995
J3A_CD = J3A_PAIR.centre_distance + J3A_STACK
J3B_CD = J3B_PAIR.centre_distance + J3B_STACK
J3_IDLER = (L1 - J3A_CD, 0.0)
J3_SERVO_V = UA_IN - J3B_PAIR.r_tip(J3B_PAIR.z_pinion) - FREE - 1.0
J3_PIN = (J3_IDLER[0] - math.sqrt(J3B_CD ** 2 - J3_SERVO_V ** 2), J3_SERVO_V)
J3_CASE, J3_TABS = case_box(SG90, J3_PIN[0], J3_PIN[1], (-1.0, 0.0))
J3_HOLES = servo_holes(SG90, J3_PIN[0], J3_PIN[1], (-1.0, 0.0))
# the plates' posts (u, v): outside every gear sweep, servo and each other
J2_POSTS = ((18.0, -24.0), (55.0, -22.0), (78.0, -15.0))
J3_POSTS = ((48.0, 16.0), (L1, 23.5), (L1, -23.5))
# the cover: corbel bosses off the shell, above everything inside
# NOT at the J2 end: the J2 gear (tip 23.75) is lowered in through the whole
# height of the arm there, and a corbel inside that column blocks it
# (_check_cobot_fit found it). The plates are notched round the rest.
UA_COVER_SCREWS = ((37.0, 24.0), (44.0, -24.0), (100.0, 24.0), (100.0, -24.0), (L1 + 17.5, 17.5),
                   (L1 + 17.5, -17.5))
NOTCH = BOSS_R + FREE + 1.0     # a plate's notch round a cover corbel, from its axis
CORBEL_BITE = 0.8     # a corbel boss must overlap its shell by this, or it floats

# the servo plates, as outlines in the link's (u, v). Each lies inside the
# shell (LOC), clear of the other plate, and holds its posts, its servo's
# tabs and its AS5600 board (all asserted). Board clamps: 2 x M2 at the
# pocket's edge, heads biting on the board.
PLATE_EDGE = 2.0
CLAMP_OFF = BOARD_POCKET / 2 + 1.2
_W2 = (J2_CASE[0] - LOC, J2_CASE[1] + LOC, J2_CASE[2] - LOC, J2_CASE[3] + LOC)     # the MG995 window
J2_PLATE = [(-15.5, -15.5), (-15.5, 15.5), (15.5, 15.5), (15.5, 5.5), (_W2[0], 5.5), (_W2[0], _W2[2]),
            (_W2[1], _W2[2]), (_W2[1], 5.5), (76.0, 5.5), (76.0, -9.5), (83.5, -9.5), (83.5, -20.5),
            (60.0, -25.5), (44.0 + NOTCH, -25.5), (44.0 + NOTCH, -24.0 + NOTCH), (44.0 - NOTCH, -24.0 + NOTCH),
            (44.0 - NOTCH, -25.5), (13.0, -25.5)]
J2_CLAMPS = ((0.0, CLAMP_OFF), (0.0, -CLAMP_OFF))
_J3_END = L1 + 13.0
J3_PLATE = [(42.5, 6.5), (86.0, 6.5), (86.0, -25.8), (100.0 - NOTCH, -25.8), (100.0 - NOTCH, -24.0 + NOTCH),
            (100.0 + NOTCH, -24.0 + NOTCH), (100.0 + NOTCH, -25.8), (L1 + 6.9, -25.8), (_J3_END, -14.0),
            (_J3_END, 14.0), (L1 + 6.9, 25.8), (100.0 + NOTCH, 25.8), (100.0 + NOTCH, 24.0 - NOTCH),
            (100.0 - NOTCH, 24.0 - NOTCH), (100.0 - NOTCH, 25.8), (42.5, 25.8)]
J3_CLAMPS = ((L1, CLAMP_OFF), (L1, -CLAMP_OFF))
J4_PLATE = [(0.5, -20.5), (34.0, -20.5), (34.0, -13.8), (46.0, -13.8), (46.0, -18.8), (53.5, -18.8),
            (58.2, -13.8), (58.2, 13.8), (53.5, 18.8), (46.0, 18.8), (46.0, 13.8), (34.0, 13.8),
            (34.0, 20.5), (0.5, 20.5)]
# the forearm plate's J4 end screws into two STANDOFFS printed on the J4
# plate (the J4 gear goes in before the plate, so nothing may stand in its
# column in the body - a corbel there blocked it; _check_cobot_fit)
STANDOFF_R = 3.0
FA_STANDOFFS = ((51.0, 15.2), (51.0, -15.2))
J4_CLAMPS = ((L2, CLAMP_OFF), (L2, -CLAMP_OFF))
# the cover corbels start above both plates' tops (and the boards on them)
UA_COVER_X0 = max(UA_J2_TAB_TOP, UA_J3_TAB_TOP) + BOARD_T + FREE

# CABLE PORTS (grommeted O8) and lanes: every joint is crossed by a service loop
# between a port on each link at the end cap nearest the joint. Inside, the
# loom runs ABOVE the servo plates, in the lane beside the MG995.
# the lane runs in the band between the J3 SG90's bottom and the cover (the
# MG995 fills the arm to the cover); the ports sit in that band
UA_LANE_X0 = UA_J3_CASE_TOP + SG90.case_h + FREE
UA_PORT_X = (UA_LANE_X0 + UA_X1 - COVER_T) / 2
UA_J2_PORT = (-UA_A, 0.0)                              # the J2 end cap, out along -u
UA_J3_PORT = (L1 + UA_A, 0.0)                          # the J3 end cap, out along +u
UA_LANE_V = 12.0                                       # over the J3 SG90, clear of the MG995
FA_PORT_X = FA_J4_TAB_TOP + BOARD_T + (FA_X1 - FA_PLATE_T - FA_J4_TAB_TOP - BOARD_T) / 2
FA_J3_PORT = (-FA_A, 0.0)
FA_J4_PORT = (L2 + FA_A, 0.0)
FA_LANE_V = -17.5

# FOREARM: J3 at (0, 0), J4 at (L2, 0). The J4 SG90 lies ACROSS the link
# (along +v) so its case stays clear of the J4 board on the J4 axis.
J4_SERVO_V = -3.0
J4_PIN = (L2 - math.sqrt(J4_PAIR.centre_distance ** 2 - J4_SERVO_V ** 2), J4_SERVO_V)
J4_CASE, J4_TABS = case_box(SG90, J4_PIN[0], J4_PIN[1], (0.0, 1.0))
J4_HOLES = servo_holes(SG90, J4_PIN[0], J4_PIN[1], (0.0, 1.0))
J4_POSTS = ((4.0, 17.0), (4.0, -17.0), (30.0, 17.5), (30.0, -17.5))
# the forearm plate: J3's 3 through-bolts at the J3 end, 2 standoffs on the J4 plate at the J4 end
FA_PLATE_SCREW_L = 12.0                  # M3 x 12, counterbored

# WRIST - a BODY (x -WR_HALF..WR_SPLIT) holding the whole J5 bay, and a CAP
# (WR_SPLIT..WR_HALF) carrying the J4 spigot. Split at the bay's own wall so
# the body prints outer face down with every pocket open at the top, and the
# cap prints split face down with the spigot on top: no support, no bridge.
HEAD_BACK_MIN_U = FA_A / math.cos(math.pi / SIDES) + FREE    # anything wider than the wrist clears the forearm's J4 end
J5_CASE_TOP = ROT_SEAT - SG90.boss_h - LOC                 # 11.3 in front of J4
J5_TAB_TOP = J5_CASE_TOP - SG90.tab_below_top
J5_TAB_V = SG90.tab_span / 2 + (SG90.case_l / 2 - SG90.shaft_from_end)
WR_SPLIT = SG90.case_w / 2 + LOC / 2                         # the J5 bay's half width
WR_CAP_T = WR_HALF - WR_SPLIT
WRIST_SCREWS = ((-17.5, 9.0), (-18.0, -9.0), (8.0, -17.0))  # M3 x 12 from the cap (counterbored) into the body
WR_PORT = (-WR_A, 0.0)                                       # the back flat, out along -u
WR_PORT_X = -2.5
# the J5 SG90: shaft on the J5 axis (x 0, v 0) pointing +u, case along +v
J5_CASE = (J5_CASE_TOP - SG90.case_h, J5_CASE_TOP, -SG90.shaft_from_end, SG90.case_l - SG90.shaft_from_end)
J5_TAB_EXT = (SG90.tab_span - SG90.case_l) / 2
J5_TABS = (J5_TAB_TOP - SG90.tab_thk, J5_TAB_TOP, J5_CASE[2] - J5_TAB_EXT, J5_CASE[3] + J5_TAB_EXT)
# THE ROTATOR (J5 output): a O21 NECK, not the old O36 disc - the forearm
# (offset, x >= 11.25) passes beside the wrist, and its J4 end reaches r 23.8:
# a disc wider than the wrist would sweep into it. The neck stays inside the
# wrist's own x layer, and the head's face is out at ROT_FACE_C >= r 24.2.
ROT_SEAT_Z = J5_CASE_TOP + FREE          # the neck's back (servo) face
ROT_HUB_D = 10.5                         # runs in the wrist's front bore
ROT_BORE = ROT_HUB_D + ROT
ROT_NECK_D = 21.0
ROT_NECK_X0 = ROT_SEAT + FREE            # the neck starts FREE in front of the wrist's face
ROT_FACE_C = math.ceil(HEAD_BACK_MIN_U * 2) / 2   # 24.5 - the head bolts here (was 21.7)
ROT_HUB = spline_hub(SG90, face=ROT_FACE_C - ROT_SEAT_Z)
ROT_BOLT_R = 7.0
ROT_BOLT_AZ = (45.0, 135.0, 225.0, 315.0)   # M3 self-tap pilots: the head's 4 x M3
# THE HEAD ADAPTER: until the head is shrunk (grip v4), the existing v3
# gripper bolts on UNCHANGED - this disc carries the old rotator's front
# face (O36, 4 x M3 heat-set inserts on +-11 x +-9, lib/grip EFF_BOLT_X/Z)
# and screws to the neck. Its back face is at ROT_FACE_C, so it clears the
# forearm's J4 end like any head (asserted).
ADAPTER_D = 36.0
ADAPTER_T = 6.0
EFF_PATTERN = (11.0, 9.0)
M3_INSERT_DEPTH = 5.5
ADAPTER_SCREW_L = 8.0        # M3 x 8, counterbored, into the neck's 6 mm pilots


def check():
    for j in (J2, J3, J4):
        j.check()
    for p, t in ((J2_PAIR, MG995.stall_kgcm * KGCM_NM), (J3B_PAIR, SG90.stall_kgcm * KGCM_NM),
                 (J3A_PAIR, J3A_INPUT_NM), (J4_PAIR, SG90.stall_kgcm * KGCM_NM)):
        bad = p.validate(t)
        assert not bad, '%s: %s' % (p.name, '; '.join(bad))
    # pinions sit on splines: roots clear the broached hub
    assert J2_PAIR.r_root(J2_PAIR.z_pinion) >= PIN2_HUB.min_gear_root_r
    assert J3B_PAIR.r_root(J3B_PAIR.z_pinion) >= PIN3_HUB.min_gear_root_r
    assert J4_PAIR.r_root(J4_PAIR.z_pinion) >= PIN4_HUB.min_gear_root_r
    # a pinion screw head that is not sunk fits the flange layer in front of its pinion
    for hub, pr in ((PIN2_HUB, J2_PAIR), (PIN3_HUB, J3B_PAIR), (PIN4_HUB, J4_PAIR)):
        d, dia = pinion_cbore(hub, pr.face)
        assert dia / 2 + MIN_WALL <= pr.r_root(pr.z_pinion), '%s: the screw counterbore breaks the roots' % pr.name
        if PIN_SCREW_STACK - d > 0:
            assert PIN_SCREW_STACK - d <= FLANGE_T + AX_GAP - LOC, '%s: the pinion screw head hits the wall' % pr.name
    # every sweep inside its shell, with FREE + 1
    assert J2.gear_tip_r + FREE + 1.0 <= UA_IN + EPS
    assert J3.gear_tip_r + FREE + 1.0 <= UA_IN + EPS
    assert J4.gear_tip_r + FREE + 1.0 <= FA_IN + EPS
    assert J3B_PAIR.r_tip(J3B_PAIR.z_gear) + FREE + 1.0 <= UA_IN + EPS      # the idler's 36T
    # spigots inside their own link's end
    assert J2.spigot_od / 2 + SHELL <= TW_A + EPS
    assert J4.spigot_od / 2 + SHELL <= WR_A + EPS
    # a pinion's tip clears the output gear's flange (the pinion's front face
    # is level with the flange top)
    assert J2_PAIR.centre_distance - J2_PAIR.r_tip(J2_PAIR.z_pinion) >= J2.flange_od / 2 + FREE - EPS
    assert J3A_PAIR.centre_distance - J3A_PAIR.r_tip(J3A_PAIR.z_pinion) >= J3.flange_od / 2 + FREE - EPS
    assert J4_PAIR.centre_distance - J4_PAIR.r_tip(J4_PAIR.z_pinion) >= J4.flange_od / 2 + FREE - EPS
    # the J3 servo pinion (stage B layer) inside the shell
    assert abs(J3_PIN[1]) + J3B_PAIR.r_tip(J3B_PAIR.z_pinion) + FREE <= UA_IN + EPS
    # ---- UPPER ARM ---------------------------------------------------------------
    # the two servos: J3's SG90 (+ tabs) clears the MG995 (+ tabs) and the J2 pinion's layer overlaps
    assert box_gap(J2_TABS, J3_TABS) >= FREE, 'the two upper arm servos meet'
    # the J3 pinion (stage B, x J3B_X0..X1) vs the MG995 case (from UA_J2_CASE_TOP)
    if J3B_X1 > UA_J2_CASE_TOP:
        assert rect_dist(J3_PIN, J2_CASE) >= J3B_PAIR.r_tip(J3B_PAIR.z_pinion) + FREE, 'J3 pinion on the MG995'
    # the J3 idler's 36T (stage B) vs the MG995 case and tabs
    if J3B_X1 > UA_J2_CASE_TOP:
        assert rect_dist(J3_IDLER, J2_TABS) >= J3B_PAIR.r_tip(J3B_PAIR.z_gear) + FREE, 'the idler on the MG995'
    # the J2 board (on the J2 axis, on the J2 plate) clears the MG995 case
    assert box_gap((-BOARD_POCKET / 2, BOARD_POCKET / 2, -BOARD_POCKET / 2, BOARD_POCKET / 2),
                   J2_TABS) >= FREE, 'the J2 board under the MG995'
    # the J3 board on J3 clears the SG90
    assert box_gap((L1 - BOARD_POCKET / 2, L1 + BOARD_POCKET / 2, -BOARD_POCKET / 2, BOARD_POCKET / 2),
                   J3_TABS) >= FREE, 'the J3 board under the SG90'
    # shells: both servos (+ tabs) inside the upper arm
    for box in (J2_TABS, J3_TABS):
        for pu in (box[0], box[1]):
            for pv in (box[2], box[3]):
                assert inside_capsule((pu, pv), UA_IN - LOC, L1, 0.0), 'a servo corner in the shell'
    # the posts
    sweeps2 = [((0.0, 0.0), J2.keep_out_r), (J2_PIN, J2_PAIR.r_tip(J2_PAIR.z_pinion) + FREE),
               ((L1, 0.0), J3.keep_out_r), (J3_IDLER, J3B_PAIR.r_tip(J3B_PAIR.z_gear) + FREE),
               (J3_PIN, J3B_PAIR.r_tip(J3B_PAIR.z_pinion) + FREE)]
    for p in J2_POSTS + J3_POSTS:
        for c, r in sweeps2:
            assert math.hypot(p[0] - c[0], p[1] - c[1]) >= r + BOSS_R - EPS, 'post %r in a sweep at %r' % (p, c)
        for box in (J2_CASE, J3_CASE, J2_TABS, J3_TABS):
            assert rect_dist(p, box) >= BOSS_R + FREE - EPS, 'post %r in a servo' % (p,)
        assert inside_capsule(p, UA_A - 0.5, L1, BOSS_R), 'post %r out of the shell' % (p,)
    # the cover corbels: clear of both servos' footprints (they run the full depth)
    for p in UA_COVER_SCREWS:
        for box in (J2_TABS, J3_TABS):
            assert rect_dist(p, box) >= BOSS_R + FREE - EPS, 'cover boss %r in a servo' % (p,)
        assert inside_capsule(p, UA_A - 0.5, L1, BOSS_R)
    # the idler pin reaches through the J3 plate
    assert IDLER_PIN_TOP >= UA_J3_TAB_TOP + 0.5, 'the idler pin misses the J3 plate'
    assert IDLER_BOSS_TOP - IDLER_PIN_BOTTOM >= 3.0, 'the idler pin is barely held in the wall'
    # the plates clear the gear layers under them
    assert UA_J3_PLATE_X0 >= J3B_X1 + FREE, 'the J3 plate on stage B'
    assert UA_J2_PLATE_X0 >= J2.x_gear_back + FREE, 'the J2 plate on the J2 gear'
    # ---- FOREARM -----------------------------------------------------------------
    assert FA_J4_PLATE_X0 >= J4.x_gear_back + FREE, 'the J4 plate on the J4 gear'
    for pu in (J4_TABS[0], J4_TABS[1]):
        for pv in (J4_TABS[2], J4_TABS[3]):
            assert inside_capsule((pu, pv), FA_IN - LOC, L2, 0.0), 'a J4 servo corner in the shell'
    assert box_gap((L2 - BOARD_POCKET / 2, L2 + BOARD_POCKET / 2, -BOARD_POCKET / 2, BOARD_POCKET / 2),
                   J4_TABS) >= FREE, 'the J4 board under the SG90'
    sweeps4 = [((L2, 0.0), J4.keep_out_r), (J4_PIN, J4_PAIR.r_tip(J4_PAIR.z_pinion) + FREE)]
    for p in J4_POSTS:
        for c, r in sweeps4:
            assert math.hypot(p[0] - c[0], p[1] - c[1]) >= r + BOSS_R - EPS, 'J4 post %r in a sweep' % (p,)
        assert rect_dist(p, J4_TABS) >= BOSS_R + FREE - EPS, 'J4 post %r in the servo' % (p,)
        assert inside_capsule(p, FA_A - 0.5, L2, BOSS_R), 'J4 post %r out of the shell' % (p,)
        for b in J3.bolts():
            assert math.hypot(p[0] - b[0], p[1] - b[1]) >= 2 * BOSS_R + FREE, 'J4 post on a J3 boss'
    for b in J3.bolts():
        assert rect_dist(b, J4_TABS) >= BOSS_R + FREE - EPS, 'a J3 boss in the J4 servo'
    # ---- fits ---------------------------------------------------------------------
    for j in (J2, J3, J4):
        assert REG_D / 2 + MIN_WALL <= j.bolt_r - M3['clearance'] / 2, j.name + ': the register hits the bolts'
        assert REG_RECESS[1] <= FLANGE_T - MIN_WALL + 0.5, j.name + ': the register recess eats the flange'
    # a slotted plate moves its board over the stalk: the stalk hole takes it
    assert (STALK_HOLE_D - STALK_D) / 2 >= PLATE_SLOT + FREE / 2, 'the stalk would rub its hole'
    # the fixed J3 meshes: stack < the extra centre distance given, by construction
    assert abs(math.hypot(J3_PIN[0] - J3_IDLER[0], J3_PIN[1] - J3_IDLER[1]) - J3B_CD) < 1e-6
    # ---- plates -----------------------------------------------------------------
    def poly_in(poly, a, length, inset):
        for p in poly:
            assert inside_capsule(p, a - inset, length, 0.0), 'plate vertex %r out of the shell' % (p,)

    def poly_has(poly, p):
        # ray cast, point strictly inside
        n, c = len(poly), False
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
                c = not c
        return c
    poly_in(J2_PLATE, UA_IN, L1, LOC)
    poly_in(J3_PLATE, UA_IN, L1, LOC)
    poly_in(J4_PLATE, FA_IN, L2, LOC)
    for poly, pts in ((J2_PLATE, J2_POSTS + ((0.0, 0.0),) + tuple(J2_HOLES) + J2_CLAMPS),
                      (J3_PLATE, J3_POSTS + ((L1, 0.0), J3_IDLER) + tuple(J3_HOLES) + J3_CLAMPS),
                      (J4_PLATE, J4_POSTS + ((L2, 0.0),) + tuple(J4_HOLES) + J4_CLAMPS)):
        for p in pts:
            assert poly_has(poly, p), 'plate misses %r' % (p,)
    # the two upper arm plates share an x band: no J3 plate vertex inside the J2 plate and v.v.
    for p in J3_PLATE:
        assert not poly_has(J2_PLATE, p)
    for p in J2_PLATE:
        assert not poly_has(J3_PLATE, p)
    assert min(p[0] for p in J3_PLATE if p[1] < 6.5) - max(p[0] for p in J2_PLATE) >= FREE, 'plates touch'
    # every corbel bites into its shell (else it prints as a separate body)
    for p in UA_COVER_SCREWS:
        assert not inside_capsule(p, UA_IN, L1, BOSS_R - CORBEL_BITE), 'cover corbel %r floats' % (p,)
    # the cover corbels sit clear of the boards and posts in plan, and above the plates in x
    for p in UA_COVER_SCREWS:
        for b_ in ((0.0, 0.0), (L1, 0.0)):
            assert rect_dist(p, (b_[0] - BOARD_POCKET / 2, b_[0] + BOARD_POCKET / 2,
                                 -BOARD_POCKET / 2, BOARD_POCKET / 2)) >= BOSS_R + FREE
    assert FA_PORT_X + PORT_D / 2 <= FA_X1 - FA_PLATE_T and FA_PORT_X - PORT_D / 2 >= FA_J4_TAB_TOP + BOARD_T
    # the loom lanes pass the servos
    assert FA_LANE_V + LOOM_D / 2 <= J4_TABS[2] - FREE and FA_LANE_V - LOOM_D / 2 >= -FA_IN, 'FA lane'
    # ---- INSERTION COLUMNS (what _check_cobot_fit found): a part lowered in
    # along -x sweeps its plan shape through every x above it. So every cover
    # corbel stays out of every plate's plan and every output gear's column,
    # and the forearm's standoffs are on the J4 plate, not in the body
    def seg_dist(p, a, b):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        L2_ = (bx - ax) ** 2 + (by - ay) ** 2
        t = 0.0 if L2_ == 0 else max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L2_))
        return math.hypot(p[0] - (ax + t * (bx - ax)), p[1] - (ay + t * (by - ay)))

    def poly_clear(poly, p, r):
        return (not poly_has(poly, p)) and min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)])
                                               for i in range(len(poly))) >= r
    for p in UA_COVER_SCREWS:
        for poly in (J2_PLATE, J3_PLATE):
            assert poly_clear(poly, p, BOSS_R + FREE), 'cover corbel %r over a plate' % (p,)
        assert math.hypot(p[0], p[1]) >= J2.keep_out_r + BOSS_R, 'cover corbel %r in the J2 gear column' % (p,)
        assert math.hypot(p[0] - L1, p[1]) >= J3.keep_out_r + BOSS_R, 'cover corbel %r in the J3 gear column' % (p,)
        for c, r in ((J2_PIN, J2_PAIR.r_tip(J2_PAIR.z_pinion)), (J3_PIN, J3B_PAIR.r_tip(J3B_PAIR.z_pinion))):
            assert math.hypot(p[0] - c[0], p[1] - c[1]) >= r + FREE + BOSS_R, 'cover corbel %r in a pinion column' % (p,)
        assert math.hypot(p[0] - J3_IDLER[0], p[1] - J3_IDLER[1]) >= \
            J3B_PAIR.r_tip(J3B_PAIR.z_gear) + FREE + BOSS_R, 'cover corbel %r in the idler column' % (p,)
    for p in J2_POSTS + J3_POSTS:
        assert math.hypot(p[0], p[1]) >= J2.keep_out_r + BOSS_R
    for p in FA_STANDOFFS:
        for k in range(16):
            q = (p[0] + STANDOFF_R * math.cos(k * math.pi / 8), p[1] + STANDOFF_R * math.sin(k * math.pi / 8))
            assert poly_has(J4_PLATE, q), 'standoff %r overhangs the J4 plate' % (p,)
        assert rect_dist(p, (L2 - BOARD_POCKET / 2, L2 + BOARD_POCKET / 2, -BOARD_POCKET / 2,
                             BOARD_POCKET / 2)) >= STANDOFF_R + FREE, 'standoff on the J4 board'
        for c in J4_CLAMPS:
            assert math.hypot(p[0] - c[0], p[1] - c[1]) >= STANDOFF_R + 1.9 + FREE, 'standoff on a board clamp'
        assert inside_capsule(p, FA_IN - LOC, L2, STANDOFF_R), 'standoff %r in the shell' % (p,)
        assert STANDOFF_R - M3['pilot'] / 2 >= MIN_WALL - 0.2
    # the UA lane band clears the J3 SG90 below and the cover above
    assert (UA_X1 - COVER_T) - UA_LANE_X0 >= LOOM_D + FREE, 'no room for the loom over the J3 SG90'
    assert UA_LANE_V - LOOM_D / 2 >= J2_TABS[3] + FREE, 'the lane on the MG995'
    assert UA_PORT_X + PORT_D / 2 <= UA_X1 - COVER_T and UA_PORT_X - PORT_D / 2 >= UA_LANE_X0 - PORT_D / 2
    # ---- the bolt stacks ----------------------------------------------------------
    e3 = J3.bolt_engaged(J3_BOLT_L, FA_PLATE_T)
    assert 6.0 <= e3 <= FA_J3_PILOT_DEPTH - 0.5, 'J3 M3 x %.0f: %.1f engaged' % (J3_BOLT_L, e3)
    e2 = J2.bolt_engaged(J2_BOLT_L, 0.0)
    assert 5.0 <= e2 <= TW_J2_PILOT_DEPTH - 0.5, 'J2 M3 x %.0f: %.1f engaged' % (J2_BOLT_L, e2)
    e4 = J4.bolt_engaged(J4_BOLT_L, 0.0)
    assert 4.5 <= e4 and J4.x_spigot_end - (e4 + 0.5) >= J5_BAY_HALF_X + MIN_WALL, 'J4 M3 x %.0f: %.1f' % (
        J4_BOLT_L, e4)
    assert FA_PLATE_T - CBORE_H >= MIN_WALL
    # ---- encoders -----------------------------------------------------------------
    for top, gear_back in ((UA_J2_TAB_TOP, J2.x_gear_back), (UA_J3_TAB_TOP, J3.x_gear_back),
                           (FA_J4_TAB_TOP, J4.x_gear_back)):
        st = stalk_top(top)
        assert st - gear_back >= 0.0, 'the stalk would be negative'
        assert st - MAGNET_POCKET[1] >= gear_back - FLANGE_T, 'the magnet pocket runs out of the gear'
    # ---- wrist -------------------------------------------------------------------
    assert ROT_NECK_D / 2 <= WR_HALF - LOC, 'the rotator neck is wider than the wrist'
    assert ROT_FACE_C >= HEAD_BACK_MIN_U, 'the head would hit the forearm end'
    assert ROT_BOLT_R + M3['pilot'] / 2 + MIN_WALL <= ROT_NECK_D / 2
    assert ROT_BOLT_R - M3['pilot'] / 2 - MIN_WALL >= (ROT_HUB.washer_d + FREE) / 2, 'rotator pilots into the screw access'
    assert ROT_HUB.min_height <= ROT_FACE_C - ROT_SEAT_Z
    for sx in (-1, 1):
        for sz in (-1, 1):
            q = (sx * EFF_PATTERN[0], sz * EFF_PATTERN[1])
            assert math.hypot(*q) + M3['insert'] / 2 + MIN_WALL <= ADAPTER_D / 2
            for az in ROT_BOLT_AZ:
                b_ = (ROT_BOLT_R * math.cos(math.radians(az)), ROT_BOLT_R * math.sin(math.radians(az)))
                assert math.hypot(q[0] - b_[0], q[1] - b_[1]) >= M3['insert'] / 2 + CBORE_D / 2 + 0.8
    assert ADAPTER_T - CBORE_H >= 2 * MIN_WALL - 0.4 - EPS and ADAPTER_T >= M3_INSERT_DEPTH
    assert ADAPTER_SCREW_L - (ADAPTER_T - CBORE_H) <= 6.0 - 0.5, 'the adapter screw bottoms in the neck'
    assert WR_CAP_T - CBORE_H >= MIN_WALL - 0.1, 'no cap under a wrist screw head'
    for p in WRIST_SCREWS:
        assert rect_dist(p, (J5_CASE[0] - LOC, J5_CASE[1], J5_CASE[2] - LOC, J5_CASE[3] + LOC)) >= CBORE_D / 2 + MIN_WALL
        assert rect_dist(p, (J5_TABS[0] - LOC, J5_TABS[1] + LOC, J5_TABS[2] - LOC, J5_TABS[3] + LOC)) >= \
            CBORE_D / 2 + MIN_WALL, 'wrist screw %r in the tab slot' % (p,)
        assert math.hypot(*p) + CBORE_D / 2 + MIN_WALL <= WR_A, 'wrist screw %r out of the drum' % (p,)
        for b_ in J4.bolts():
            assert math.hypot(p[0] - b_[0], p[1] - b_[1]) >= CBORE_D / 2 + M3['pilot'] / 2 + MIN_WALL
        assert abs(p[1] - WR_PORT[1]) >= CBORE_D / 2 + PORT_D / 2 + MIN_WALL - 0.1 or p[0] > -WR_A + 3 * PORT_D, \
            'wrist screw %r in the port' % (p,)
    assert J4.x_spigot_end - (J4.bolt_engaged(J4_BOLT_L, 0.0) + 0.5) >= WR_SPLIT + MIN_WALL, 'J4 pilots into the bay'
    assert math.hypot(J5_TAB_TOP, J5_TAB_V) <= WR_A - SHELL - LOC + EPS
    assert math.hypot(J5_CASE_TOP - SG90.case_h, SG90.case_l - SG90.shaft_from_end) <= WR_A - SHELL - LOC + EPS
    return True


J5_BAY_HALF_X = SG90.case_w / 2 + LOC / 2      # the J5 bay in the wrist, each side of x = 0

check()
