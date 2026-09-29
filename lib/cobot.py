"""The cobot arm (2026-09-29) - every number the cobot_* parts share, in ONE place.

Jonathan, 2026-09-29: "no i mean like complete redesign" -> the myCobot 280 /
UFactory Lite 6 layout ("I am liking this more and more"): 12-gon CAPSULE
links lying side by side, servos INSIDE, no forks. Then: "work out how the
parts go together - how the motors are placed with the correct tolerances -
how the cables are managed - minimise the likelihood of reprints ... like
the motor would have to teleport into position".

Kept: the printed base_platter + base_lid, the whole J1 turntable (stator,
608 rollers, ring, j1_hub, shroud), every servo, every link length (reach 289).

THE JOINT - one pattern, used at J2, J3 and J4
-----------------------------------------------
Two links: S holds the servo, H is driven.
  * H carries a SPIGOT that passes through a BORE in S's JOINT WALL.
  * Inside S, a printed HUB (at J3: the 36T gear) is bolted to the spigot's
    end. Its FLANGE traps S's wall between itself and H's face, with an
    AX_GAP running clearance either side.
  * S's servo drives the hub: on its spline (J2, J4) or through the 18T
    pinion (J3). A direct-drive hub is BROACHED ONTO ITS SERVO ON THE BENCH
    (servo screw + washer, head in a recess in the spigot end), and the
    hub bolts sit where the servo case is not, so a driver reaches them
    past the case from the open side (asserted).
The bending load goes into two flat annuli (H's face and the flange) - a
couple of ~10 N at these radii - and never into a servo shaft. The radial
load goes into the spigot in the bore (a rotating fit).

WHY NOTHING HAS TO TELEPORT
---------------------------
Every link is a BODY (joint walls + 12-gon shell, open on one face) plus a
flat COVER, and the servo is always inserted along its own shaft axis
through that open face:
  1. H's spigot goes through S's bore (S's cover off).
  2. Geared joint (J3): the gear is bolted to the spigot end, then the
     servo + pinion slides in along x and the pinion meshes axially.
     Direct joints (J2, J4): servo + broached hub go in as one, along x,
     onto the spigot end, and the hub bolts are driven past the case.
  3. The servo's FAR tab screws to a post that stands outside the flange's
     sweep (asserted); the near tab sits over the flange and is not needed:
     the spline locates the shaft end, the far screw takes the torque
     reaction, and a pad on the cover stops the case tilting.
  4. The cover closes.
The wrist's servo shaft is not along x, so the wrist is a clamshell split
through its servo (as wrist_roll was). The tower holds no servo: it is the
rotor, a column and the J2 spigot, and its J1 hub bolts are reached through
three access holes from the top.

CABLES (see specs/robotarm/cobot.md for the run list)
------------------------------------------------------
J3 is geared, so its axis is FREE: the loom passes through the hollow J3
spigot and the gear's bore, fully inside. At J2 and J4 the servo sits on the
axis, so the loom crosses in a short service loop between two GROMMET PORTS,
one on each link, close to the joint axis so the loop length changes least. Inside every link it runs in a channel clear of the servo's insertion
path. J1 is unchanged: down the tower, through the rotor's cable window.

Frame: the arm frame at J1 yaw 0. x along the J2/J3/J4 axes, y forward, z up.
The TOOL PLANE is x = 0: the wrist is centred on it, so the J5 axis and the
gripper stay on the J1 plane and the planar IK is unchanged.
"""

import math

from lib.design_rules import FASTENER_MM as _FASTENER
from lib.design_rules import JOINT_FIT_MM as _FIT
from lib.design_rules import MIN_WALL_MM as _MIN_WALL
import lib.gears as _gears  # noqa: F401 - import order: lib.gears before lib.servo_hub
from lib.gears import J3_PAIR
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
M3_HEAD_D = 5.5      # ISO 4762 M3 cap head - DATASHEET

SHELL = 2.0          # CHOSEN - every 12-gon outer wall: 5 perimeters at 0.4
JOINT_WALL = 3.0     # CHOSEN - S's wall in the joint (the bearing annulus)
AX_GAP = 0.25        # CHOSEN - axial running gap each side of that wall
FLANGE_T = 3.0       # CHOSEN - the hub flange
COVER_T = 2.0
PLATE_T = 3.0        # CHOSEN - the servo plate the tabs screw to
PORT_D = 8.0         # CHOSEN - a grommeted cable port; the J2 loom is ~O5
SIDES = 12

MG995 = CATALOG[JOINT_SERVO['J2']]
SG90 = CATALOG[JOINT_SERVO['J4']]
HUB2_H = 6.0         # the J2 hub: flange + a body toward the servo (broach 1.1..5.0)
HUB4_H = 6.5         # the J4 hub (the SG90 broach runs 3.8..6.3)
HUB2 = spline_hub(MG995, face=HUB2_H)
HUB4 = spline_hub(SG90, face=HUB4_H)

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


class Joint:
    """A cantilever joint, mm. H's face at x_face; S lies on the `sign` side."""

    def __init__(self, name, spigot_id, spigot_od, overlap, bolt_r, bolt_az, hub_h, x_face, sign):
        self.name, self.sign = name, sign
        self.bolt_az = bolt_az
        self.spigot_id, self.spigot_od = spigot_id, spigot_od
        self.bore = spigot_od + ROT
        self.flange_od = spigot_od + 2 * overlap
        self.bolt_r, self.hub_h = bolt_r, hub_h
        self.x_face = x_face
        self.x_wall0 = x_face + sign * AX_GAP                  # S's joint wall
        self.x_wall1 = self.x_wall0 + sign * JOINT_WALL
        self.x_spigot_end = self.x_wall1 + sign * AX_GAP
        self.x_hub_back = self.x_spigot_end + sign * hub_h     # the hub's servo-side face
        self.keep_out_r = self.flange_od / 2 + FREE            # nothing of S inside this, near the flange

    def check(self):
        pil = M3['pilot']
        if self.spigot_id:
            assert self.spigot_id / 2 + MIN_WALL + pil / 2 <= self.bolt_r + 1e-9, self.name
        assert self.bolt_r + pil / 2 + MIN_WALL <= self.spigot_od / 2 + 1e-9, self.name
        assert (self.flange_od - self.bore) / 2 >= 2.0, '%s: the flange barely laps the wall' % self.name
        return True

    def bolts(self):
        return [(self.bolt_r * math.cos(math.radians(a)), self.bolt_r * math.sin(math.radians(a)))
                for a in self.bolt_az]

    def driver_clear(self, servo, along):
        """Least distance, mm, from any bolt head to the servo case + tabs seen
        along x (the case runs from the shaft toward `along`). > 0: a driver
        reaches every bolt past the case."""
        head = M3_HEAD_D / 2
        near = servo.shaft_from_end + (servo.tab_span - servo.case_l) / 2
        far = servo.case_l - servo.shaft_from_end + (servo.tab_span - servo.case_l) / 2
        best = 1e9
        for bu, bv in self.bolts():
            a = bu * along[0] + bv * along[1]            # along the case
            c = -bu * along[1] + bv * along[0]           # across it
            if -near <= a <= far:
                best = min(best, abs(c) - servo.case_w / 2 - head)
        return best


# --- the x stack, from the tool plane outward ---------------------------------
WR_HALF = 11.0                          # the wrist clamshell, x -11..+11, split at x = 0
J4 = Joint('J4', spigot_id=0.0, spigot_od=28.0, overlap=3.0, bolt_r=11.0,
           bolt_az=(70.0, 110.0, 250.0, 290.0), hub_h=HUB4_H, x_face=WR_HALF, sign=+1)
FA_X0 = J4.x_wall0
FA_J4_CASE_TOP = J4.x_hub_back + FREE                                  # hub -> case top (seat_z's 0.4)
FA_J4_TAB_TOP = FA_J4_CASE_TOP + SG90.tab_below_top                     # the tab face toward the hub
# the forearm's +x plate is STRUCTURAL: it carries the J3 spigot (the forearm
# is H at J3). It is 5 thick, not a joint wall's 3, because the links are
# OFFSET: the upper arm's wall passes AX_GAP over this whole face as the elbow
# folds, so every screw head in it must sit in a counterbore (M3 head 3.0 in a
# 3.2 bore, 1.8 left under it)
FA_PLATE_T = 5.0
FA_CBORE_H = 3.2
FA_X1 = FA_J4_CASE_TOP + SG90.case_h + FREE + FA_PLATE_T
# J3 and J2 both have the upper arm as S: ONE joint wall, the upper arm's -x face
# THE J3 GEAR: a FLANGE_T flange (the retainer, O32) then the tooth band. The
# flange also stands the teeth off the upper arm's wall by FLANGE_T, which is
# exactly the room the 18T pinion's retaining screw + washer need on ITS far
# face (grip PIN_SCREW_STACK 2.6 + a gap): without it that head would run on
# the wall.
PIN_SCREW_STACK = 2.6      # ASSUMED - SG90 horn screw washer 0.8 + pan head 1.8 (lib/grip)
J3 = Joint('J3', spigot_id=12.0, spigot_od=26.0, overlap=3.0, bolt_r=9.5,
           bolt_az=(90.0, 210.0, 330.0), hub_h=FLANGE_T + J3_PAIR.face, x_face=FA_X1, sign=+1)
J2 = Joint('J2', spigot_id=0.0, spigot_od=40.0, overlap=3.0, bolt_r=17.0,
           bolt_az=(60.0, 120.0, 240.0, 300.0), hub_h=HUB2_H, x_face=FA_X1, sign=+1)
UA_X0 = J3.x_wall0
UA_J3_CASE_TOP = J3.x_hub_back + FREE                                  # the pinion is as wide as the gear
UA_J3_TAB_TOP = UA_J3_CASE_TOP + SG90.tab_below_top
# the J3 SG90's tab screws go through the tab and the J3 plate and come out
# over the pinion: longest that stays out of its face (+ FREE). The SG90 bag
# screws are ~8 mm - too long; the BOM calls for M2 x 6
J3_TAB_SCREW_MAX = UA_J3_TAB_TOP + SG90.tab_thk - (J3.x_hub_back + FREE)
UA_J2_CASE_TOP = J2.x_hub_back + FREE
UA_J2_TAB_TOP = UA_J2_CASE_TOP + MG995.tab_below_top
UA_X1 = max(UA_J2_CASE_TOP + MG995.case_h, UA_J3_CASE_TOP + SG90.case_h) + FREE + COVER_T
TOWER_X1 = J2.x_face                    # the tower's +x face, where the J2 spigot stands
SCREW_HEAD_RECESS = (8.0, 3.0)          # the servo screw + washer head, recessed in a direct spigot end

# --- the J3 gear pair -------------------------------------------------------------
GEAR_TIP_R = J3_PAIR.module * (J3_PAIR.z_gear + 2) / 2.0              # 19.0
PIN_TIP_R = J3_PAIR.module * (J3_PAIR.z_pinion + 2) / 2.0             # 10.0
J3_CENTRE = J3_PAIR.module * (J3_PAIR.z_gear + J3_PAIR.z_pinion) / 2.0 + J3_PAIR.backlash

# --- the 12-gon sizes (apothems) ------------------------------------------------
TW_A = 28.0          # the tower: column about J1, J2 drum about J2, one apothem
UA_A2 = 26.0         # upper arm at J2: the J2 flange keep-out r 23.4 + SHELL
UA_A3 = 24.0         # upper arm at J3: the J3 SG90 lies ACROSS it, tabs to v -21.4
FA_A = 22.0          # forearm, both ends
WR_A = 25.0          # wrist drum: the J5 SG90's tabs reach r 22.5 about J4
HEAD_A = 25.0        # the gripper head, shrunk to the wrist's size

# J5 SG90 in the wrist, shaft forward on the J5 axis (x = 0, v = 0); its boss
# runs up inside the front wall, exactly as in wrist_roll
J5_CASE_TOP = ROT_SEAT - SG90.boss_h - LOC                 # 11.3 in front of J4
J5_TAB_TOP = J5_CASE_TOP - SG90.tab_below_top
J5_TAB_V = SG90.tab_span / 2 + (SG90.case_l / 2 - SG90.shaft_from_end)

# the forearm's +x plate screws (u from J3, v). FLOOR bosses stand on the J4
# joint wall. At the J4 end the flange sweep (r 17.4) leaves 2.6 mm to the
# shell, so the two there are CORBELS: they hang off the shell, start above
# the flange (J4 x_spigot_end + FLANGE_T + FREE) on a 45 deg cone - no support
FA_BOSS_R = 3.5
FA_FLOOR_SCREWS = ((30.0, 15.0), (30.0, -15.0))
# at J3 the plate needs no screws of its own: the gear's 3 bolts run through
# gear, spigot and plate into bosses in the forearm body - one stack, one clamp
FA_J3_PILOT_DEPTH = 10.0
J3_BOLT_L = 30.0                          # M3 x 30
FA_CORBEL_R = 18.5                       # from J4
FA_CORBEL_AZ = (50.0, -50.0)             # from +u
FA_CORBEL_SCREWS = tuple((L2 + FA_CORBEL_R * math.cos(math.radians(a)), FA_CORBEL_R * math.sin(math.radians(a)))
                         for a in FA_CORBEL_AZ)
FA_PLATE_SCREWS = FA_FLOOR_SCREWS + FA_CORBEL_SCREWS
FA_CORBEL_X0 = J4.x_spigot_end + FLANGE_T + FREE       # the cone's apex: just above the flange


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


def servo_holes(servo, shaft_u, shaft_v, along):
    """The four tab-hole centres of a servo whose shaft is at (shaft_u, shaft_v)
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


def check():
    for j in (J2, J3, J4):
        j.check()
    # the J3 axis is free for the loom: the gear bore is the spigot bore
    assert J3.spigot_id >= 2 * 5.0, 'the J3 loom (~O5) does not pass the spigot'
    # every hub/gear sweep is inside the link shell it turns in
    assert J2.keep_out_r <= UA_A2 - SHELL + 1e-9
    assert J4.keep_out_r <= FA_A - SHELL + 1e-9
    assert GEAR_TIP_R + FREE + 1.0 <= UA_A3 - SHELL + 1e-9
    # the spigots fit inside their own link's end
    assert J2.spigot_od / 2 + SHELL <= TW_A + 1e-9
    assert J4.spigot_od / 2 + SHELL <= WR_A + 1e-9
    # the pinion clears the gear's flange, and its screw head clears the wall
    assert J3_CENTRE - PIN_TIP_R >= J3.flange_od / 2 + FREE
    assert FLANGE_T >= PIN_SCREW_STACK + AX_GAP, 'the pinion screw head would run on the upper arm wall'
    # the J3 SG90 lies ACROSS the upper arm (case along v) so no tab hole
    # falls in the gear's sweep, and all four sit inside the shell
    for u, v in servo_holes(SG90, L1 - J3_CENTRE, 0.0, (0.0, -1.0)):
        assert math.hypot(u - L1, v) >= GEAR_TIP_R + FREE + M3['pilot'], 'J3 tab post in the gear sweep'
    tab_v = SG90.tab_span / 2 + (SG90.case_l / 2 - SG90.shaft_from_end)
    assert tab_v + LOC <= UA_A3 - SHELL, 'the J3 SG90 tab end hits the upper arm shell'
    # direct joints: every hub bolt is reachable past the case, from the open side
    assert J2.driver_clear(MG995, (1.0, 0.0)) >= FREE, 'a J2 hub bolt is hidden under the MG995'
    assert J4.driver_clear(SG90, (-1.0, 0.0)) >= FREE, 'a J4 hub bolt is hidden under the SG90'
    # the far-tab posts stand outside the flange keep-out (+ a pilot's wall)
    mg_far = MG995.case_l - MG995.shaft_from_end + (MG995.tab_hole_pitch - MG995.case_l) / 2
    assert mg_far - MIN_WALL - M3['pilot'] / 2 >= J2.keep_out_r, 'the MG995 far post is in the J2 flange sweep'
    sg_far = SG90.case_l - SG90.shaft_from_end + (SG90.tab_hole_pitch - SG90.case_l) / 2
    assert sg_far >= J4.keep_out_r + FREE, 'the J4 far tab hole is in the flange sweep'
    # the two upper-arm servos do not meet: MG995 along +u from J2, J3 SG90 across at L1 - 27.2
    mg_tip = MG995.case_l - MG995.shaft_from_end + (MG995.tab_span - MG995.case_l) / 2
    assert (L1 - J3_CENTRE - SG90.case_w / 2) - mg_tip >= 10.0
    # the J2 flange and the MG995 case clear the upper arm shell at J2
    assert math.hypot(MG995.shaft_from_end + (MG995.tab_span - MG995.case_l) / 2,
                      MG995.case_w / 2) <= UA_A2 - SHELL - LOC
    # the J5 SG90 in the wrist drum: the far tab corner and the case bottom corner
    assert math.hypot(J5_TAB_TOP, J5_TAB_V) <= WR_A - SHELL - LOC + 1e-9
    assert math.hypot(J5_CASE_TOP - SG90.case_h, SG90.case_l - SG90.shaft_from_end) <= WR_A - SHELL - LOC + 1e-9
    # the forearm plate screws: floor bosses outside the J4 flange sweep, corbels
    # leave the hub bolts' driver path clear; none in the SG90's slot
    for u, v in FA_FLOOR_SCREWS:
        assert math.hypot(u - L2, v) - FA_BOSS_R >= J4.keep_out_r, 'a floor boss in the J4 flange sweep'
    for u, v in FA_CORBEL_SCREWS:
        assert FA_CORBEL_R - FA_BOSS_R >= J4.bolt_r + M3_HEAD_D / 2 + FREE, 'a corbel over a J4 hub bolt'
        assert FA_CORBEL_R + M3['pilot'] / 2 <= FA_A - SHELL, 'a corbel pilot breaks the shell'
    for u, v in FA_PLATE_SCREWS:
        assert abs(v) - FA_BOSS_R >= SG90.case_w / 2 + FREE, 'a plate boss in the J4 SG90 slot'
    assert J3_TAB_SCREW_MAX >= 6.0, 'an M2 x 6 on the J3 plate would reach the pinion'
    # the J3 through-bolt: engages the forearm boss, does not bottom out
    grip = J3.hub_h + (J3.x_spigot_end - FA_X1) + FA_PLATE_T
    assert 6.0 <= J3_BOLT_L - grip <= FA_J3_PILOT_DEPTH - 0.5, 'M3 x %.0f in the J3 stack: %.1f engaged' % (
        J3_BOLT_L, J3_BOLT_L - grip)
    assert FA_PLATE_T - FA_CBORE_H >= MIN_WALL, 'no plate left under a counterbored head'
    for u, v in J3.bolts():
        assert math.hypot(u, v) - FA_BOSS_R >= J3.spigot_id / 2 - 1e-9, 'a J3 boss in the loom bore'
    return True


check()
