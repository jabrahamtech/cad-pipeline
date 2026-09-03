"""Spur gear pairs — the shared contract, not a drawing.

THE PROJECT'S RECURRING FAILURE IS A DATUM ONLY ONE FILE READS. So the J3
reduction lives here and NOWHERE else: j3_gear.py, j3_pinion.py, forearm.py
and _check_elbow.py all import J3_PAIR, and the centre distance that places
the servo is the same object the tooth profiles are cut from. If you change
the module, every consumer moves with it or its own assert fails.

Nothing here touches Fusion. It is arithmetic plus the checks that arithmetic
has to survive, so it can be run and argued with outside the CAD.

WHY 2:1 AT ALL. Measured 2026-08-30, arm straight out with 25 g gripped:
J2 60 % of duty, J3 87 %, J4 36 %. The elbow is the whole bottleneck and has
been since the forearm went to 65 mm. Doubling it costs half the elbow's
travel (a 180 deg servo through 2:1 gives 90 deg at the joint) and buys the
rated payload back: 25 g -> roughly 60 g.

WHICH SERVO DRIVES J3 IS NOT DECIDED HERE. It is `lib/joints.JOINT_SERVO`,
and this file reads it - see J3_SERVO below. That dict is the arm's single
statement of which motor is on which joint, and it exists because the answer
used to be typed into eleven files at once. As of 2026-09-03 J3 is an SG90.

MODULE 1.00, FACE 10.0 - AND THE FACE IS WHAT PAYS FOR THE MODULE.
2026-08-31: Jonathan asked whether the train could sit less proud of the arm.
The WIDTH cannot move - the 10.80 mm standoff is the servo's own stack plus
the gear band, and J3_MOUNT already has it at its floor. The RADIUS is the
module, and it can: m 1.25 -> 1.00 takes the 36T from r_tip 23.75 to 19.00
and the centre distance from 33.95 to 27.20.

Root stress goes the other way, as 1/(face x module): at m 1.00 on the old
8.0 face it is 8.82 MPa against an 8.75 allowable, which FAILS - validate()
said so rather than letting it through. Face 8.0 -> 10.0 buys it back to
7.05 on the MG90S, and 5.64 now that J3 is an SG90 - a 20 % smaller stall
torque goes straight into the root. That costs 2.0 mm of standoff, so the
part is 4.75 mm less proud radially and 2.0 mm wider axially.

What is not a cost: both clearance cylinders in the forearm shrink with the
gears, so the standoff web GROWS. The pinion circle now cuts the 8.80-tall
servo lobe over +/-5.54 mm of Y instead of +/-9.43 - considerably more web
left than the version priced at 71x in _HANDOFF.md section 9.

THE SUPERSEDED ARGUMENT FOR 1.25, kept because it is still the reason 1.5 is
not here: WHY MODULE 1.25 AND NOT THE HANDBOOK'S 1.5. design_rules.py prefers 1.5 for
anything carrying torque and floors at 1.0. 1.5 was priced first and the
package is what rejected it: 18T/36T at m 1.5 is a 40.5 mm centre distance,
and with L2 = 45 that puts the J3 servo shaft 4.5 mm from the WRIST axis,
with its case straddling J4's. At m 1.25 the same tooth counts give 33.75 and
the servo lands mid-forearm. The strength this costs is affordable and is
stated rather than assumed - see lewis_stress() and the assert at the bottom:
5.6 MPa against the 8.75 MPa CYCLIC allowable, which already carries
design_rules' safety factor of 4.0. 64 %.

WHY 18 TEETH. z_min = 2 / sin^2(pa) = 17.1 at 20 deg, so 18 is the smallest
standard full-depth pinion that does not undercut. 17 is under it and 12 -
which gripper_pinion uses - only survives because a rack has no tip to
interfere with. This pair has two involutes and no such licence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from lib.design_rules import (
    GEAR_BACKLASH_MM,
    GEAR_MIN_FACE_WIDTH_FACTOR,
    GEAR_MIN_MODULE_MM,
    SAFETY_FACTOR,
)

# PETG in-plane tensile, the same number loads_strength.md uses elsewhere.
PETG_TENSILE_MPA = 35.0

# Lewis form factor, 20 deg full-depth, HANDBOOK table. Only the counts this
# project actually uses are listed - an unknown count raises rather than
# interpolating silently.
# EXTENDED AND PARTLY CORRECTED 2026-08-31. Two entries were shifted one row
# off the standard 20 deg full-depth table: 14 carried 0.261 (which is z=13's
# value) and 16 carried 0.277 (z=14's). Both errors were CONSERVATIVE - a low
# Y reads as high root stress - and a grep says no part in this project has
# ever built a 14T or 16T pair, so nothing that passed a gate passed it on
# these. They are corrected rather than left, because a table that is wrong
# where you have not looked is a trap for whoever looks next.
# 32 and 36 are interpolations between standard rows and check out (30/34 ->
# 0.365 vs the 0.364 on file; 34/38 -> 0.377 exactly). Kept.
LEWIS_Y = {12: 0.245, 13: 0.261, 14: 0.277, 15: 0.290, 16: 0.296,
           17: 0.303, 18: 0.309, 19: 0.314, 20: 0.322, 21: 0.328,
           22: 0.331, 24: 0.337, 25: 0.341, 26: 0.346, 27: 0.350,
           28: 0.353, 30: 0.359, 32: 0.364, 34: 0.371, 36: 0.377,
           38: 0.384, 40: 0.389, 42: 0.394, 43: 0.397, 44: 0.399,
           45: 0.400, 48: 0.405, 50: 0.409, 54: 0.414, 56: 0.417,
           60: 0.422, 64: 0.426, 66: 0.428, 70: 0.432, 72: 0.433,
           75: 0.435, 80: 0.438, 90: 0.443, 100: 0.447}


@dataclass(frozen=True)
class SpurPair:
    """An external involute pair. All lengths mm, angles degrees."""

    name: str
    module: float
    z_pinion: int
    z_gear: int
    face: float
    pressure_angle: float = 20.0
    ded_f: float = 1.25          # dedendum factor, standard full depth
    backlash: float = GEAR_BACKLASH_MM

    # ---- ratio ----------------------------------------------------------
    @property
    def ratio(self) -> float:
        return self.z_gear / self.z_pinion

    # ---- radii ----------------------------------------------------------
    def r_pitch(self, z: int) -> float:
        return self.module * z / 2.0

    def r_tip(self, z: int) -> float:
        return self.r_pitch(z) + self.module

    def r_root(self, z: int) -> float:
        return self.r_pitch(z) - self.module * self.ded_f

    def r_base(self, z: int) -> float:
        return self.r_pitch(z) * math.cos(math.radians(self.pressure_angle))

    @property
    def centre_distance(self) -> float:
        """Backlash is taken at the centre distance, per design_rules."""
        return (self.r_pitch(self.z_pinion) + self.r_pitch(self.z_gear)
                + self.backlash)

    # ---- strength -------------------------------------------------------
    def lewis_stress_mpa(self, torque_nm: float) -> float:
        """Root bending stress in the PINION at a given input torque.

        The pinion is the weaker member: same tangential force, fewer teeth,
        smaller form factor. Sized on the servo's STALL torque, because that
        is what the servo can actually deliver into a jam - not the duty
        limit, which is only what it may HOLD.
        """
        ft = torque_nm / (self.r_pitch(self.z_pinion) / 1000.0)   # N
        y = LEWIS_Y[self.z_pinion]
        return ft / (self.face * self.module * y)

    @property
    def allowable_mpa(self) -> float:
        return PETG_TENSILE_MPA / SAFETY_FACTOR['cyclic']

    @property
    def undercut_floor(self) -> float:
        a = math.radians(self.pressure_angle)
        return 2.0 / (math.sin(a) ** 2)

    @property
    def contact_ratio(self) -> float:
        a = math.radians(self.pressure_angle)
        c = self.centre_distance

        def arm(z):
            return math.sqrt(max(self.r_tip(z) ** 2 - self.r_base(z) ** 2, 0.0))

        return ((arm(self.z_pinion) + arm(self.z_gear) - c * math.sin(a))
                / (math.pi * self.module * math.cos(a)))

    def validate(self, torque_nm: float) -> list:
        """Return a list of complaints. Empty means the pair is buildable."""
        bad = []
        if self.module < GEAR_MIN_MODULE_MM:
            bad.append('module %.2f is under the %.2f floor for a 0.4 nozzle'
                       % (self.module, GEAR_MIN_MODULE_MM))
        if self.face < GEAR_MIN_FACE_WIDTH_FACTOR * self.module:
            bad.append('face %.2f is under %.1f x module'
                       % (self.face, GEAR_MIN_FACE_WIDTH_FACTOR))
        if self.z_pinion < self.undercut_floor:
            bad.append('%dT undercuts at %.0f deg - the floor is %.1f'
                       % (self.z_pinion, self.pressure_angle,
                          self.undercut_floor))
        if self.z_pinion not in LEWIS_Y or self.z_gear not in LEWIS_Y:
            bad.append('no Lewis factor on file for %dT/%dT'
                       % (self.z_pinion, self.z_gear))
        if self.contact_ratio < 1.2:
            bad.append('contact ratio %.2f - under 1.2 the mesh is not '
                       'continuous' % self.contact_ratio)
        s = self.lewis_stress_mpa(torque_nm)
        if s > self.allowable_mpa:
            bad.append('root stress %.2f MPa over the %.2f MPa cyclic '
                       'allowable' % (s, self.allowable_mpa))
        return bad


    # ---- profile -------------------------------------------------------
    def tooth_polar(self, z: int, n: int = 12, sink: float = 0.5):
        """One tooth as polar points, for a CAD sketch to trace.

        Returns (flank_pos, flank_neg, ang_base, ang_tip, r_sink) with every
        radius in mm and every angle in radians about the tooth's centreline.
        The involute is generated from the base circle - it is not an arc
        approximation - so the pressure angle at the pitch circle comes out
        of the maths rather than being drawn in.

        Both printed gears in this project trace THIS function. That is the
        point of it being here: a tooth form that two parts have to share is
        not something either part gets to own.
        """
        r_b = self.r_base(z)
        r_p = self.r_pitch(z)
        r_t = self.r_tip(z)
        r_r = self.r_root(z)

        def inv(a):
            return math.tan(a) - a

        # half the tooth's angular thickness at the base circle, less the
        # backlash this member carries (half the pair's, taken on the tooth)
        bl_ang = (self.backlash / 2.0) / r_p
        psi_half = math.pi / (2 * z) + inv(math.acos(r_b / r_p)) - bl_ang / 2.0

        def flank_ang(r):
            if r <= r_b:
                return psi_half
            return psi_half - inv(math.acos(r_b / r))

        lo = max(r_b, r_r)
        pos, neg = [], []
        for i in range(n):
            r = lo + (r_t - lo) * i / (n - 1.0)
            pos.append((r, +flank_ang(r)))
            neg.append((r, -flank_ang(r)))
        return {
            'flank_pos': pos, 'flank_neg': neg,
            'ang_base': psi_half, 'ang_tip': flank_ang(r_t),
            'r_sink': r_r - sink, 'r_base': r_b, 'r_tip': r_t, 'r_root': r_r,
            'thk_pitch': 2 * flank_ang(r_p) * r_p,
        }


# --- J3, the elbow. The only geared joint in this arm. --------------------
# Face 8.0 matches gripper_pinion's, so both printed gears in this project
# are the same thickness and one test print settles both.
J3_PAIR = SpurPair(name='J3', module=1.00, z_pinion=18, z_gear=36, face=10.0)

# WHAT THE PINION IS VALIDATED AGAINST: the stall torque of whatever servo
# JOINT_SERVO says drives J3, in N.m.
#
# IT USED TO BE `2.0 * 9.80665 / 100.0` WITH A COMMENT SAYING "MG90S stall,
# lib/servo.py". That is a copy of a number lib/servo.py already holds, with
# a comment naming the file it was copied from - which is the shape this
# project's failures take, not a citation. Put an SG90 on J3 and the 2.0
# stays 2.0, the Lewis check passes against a torque the servo cannot
# produce, and nothing anywhere says so.
#
# IMPORTED HERE, AT MODULE LEVEL, AND lib/joints.py DEFERS ITS SIDE OF THE
# PAIR SO THAT THIS CAN. See the `_j3_pair()` note in that file: gears needs
# one small dict from joints while it is still defining J3_MOUNT, and joints
# needs a tooth count only inside three functions. The cheap direction is
# the one taken.
from lib.joints import servo_for as _servo_for  # noqa: E402
from lib.joints import stall_nm as _stall_nm  # noqa: E402

J3_SERVO = _servo_for('J3')
J3_INPUT_STALL_NM = _stall_nm('J3')

# What the reduction does to the joint, for anything that reports it.
J3_SERVO_TRAVEL_DEG = 180.0
J3_JOINT_TRAVEL_DEG = J3_SERVO_TRAVEL_DEG / J3_PAIR.ratio

_bad = J3_PAIR.validate(J3_INPUT_STALL_NM)
assert not _bad, 'J3_PAIR is not buildable: ' + '; '.join(_bad)


# --- Mounting a printed pinion on a hobby servo horn ----------------------
# THIS IS THE NUMBER THE ELBOW WAS COSTED WRONG ON. The 2026-08-30 handoff
# priced the offset spur pair at "~7 mm of forearm width". It is not a free
# parameter: a servo's horn seat is a fixed height above the tab plane its
# mount clamps, the pinion's tooth band has to coincide with the gear's, and
# the gear's band is fixed by the fork plate it journals in. Those three
# facts SOLVE for how far the servo mount must stand off the plate. Nobody
# gets to choose it, and the first version of this reduction was drawn as
# though somebody had.
#
# THE STACK, from the tab plane, +Z out of the shaft (lib/servo.py's frame):
#     case top   = tab_below_top + tab_thk
#     boss top   = case top + boss_h          <- the horn blade sits here
#     blade top  = boss top + horn_blade_thk
#     hub top    = boss top + horn_hub_h
#
# WHY THE BORE GOES STRAIGHT THROUGH. Blind-pocketing the horn puts the
# pinion's seat face on the BOSS TOP - 11.5 mm up an MG90S, 10.9 up an SG90 -
# and every one of those millimetres is standoff the forearm has to grow.
# Boring straight through at the hub press diameter lets the servo's own
# output boss pass freely and drops the seat face to just clear the case top,
# which is 4.8 mm of arm width on the MG90S and 3.8 on the SG90 (its boss is
# shorter, so it had less to give). Thickening the pinion to swallow the boss in a
# blind pocket does NOT work: the swallowed depth comes out of the pinion's
# own thickness, the pinion is bounded inboard by the fork plate, and it ends
# up 2.7 mm inside it needing a relief that breaks into the J4 counterbore.
#
# THE PRESS IS UNCHANGED - the hub still presses over its full horn_hub_h,
# just partway along a through bore instead of at the bottom of a blind one.


@dataclass(frozen=True)
class HornPinion:
    """Where a printed pinion sits on a servo horn, and what it costs.

    All distances in mm. `seat_z` is in the SERVO's frame (lib/servo.py);
    every other depth is measured from the pinion's own seat face, which is
    the face that looks at the servo.
    """

    servo_name: str
    seat_z: float          # servo-z of the pinion's seat (servo-side) face
    face: float            # pinion blank thickness = the pair's face width
    bore_d: float          # the single through bore
    press_from: float      # depth where the horn hub press begins
    press_to: float        # ... and ends
    slot_r: float          # horn arms trimmed to this radius
    slot_w: float          # horn arm width at that radius, plus press
    slot_depth: float      # cross slot depth from the seat face
    case_gap: float        # seat face to the servo case top

    @property
    def press_len(self) -> float:
        return self.press_to - self.press_from


def horn_pinion(servo, pair, arm_r=6.0, arm_w=None, press=0.15,
                slot_clear=None, case_gap=0.4, hub_margin=0.5, slot_extra=0.1):
    """Solve the pinion's seat face for a servo and a gear pair.

    arm_w defaults to lib/servo.py's MEASURED micro arm width at `arm_r`, so
    it is not a second copy of that number.

    THE BORE IS A PRESS; THE SLOT IS NOT. `press` sizes the round bore on the
    horn hub - that is what retains the pinion, along with the horn's own
    screw. `slot_clear` sizes the CROSS SLOT, whose job is to key torque, not
    to grip. The slot used to take `press` too, i.e. it was cut 0.15 OVER a
    measured 5.7 arm and called a press fit; a printed slot comes out
    undersize, so the real thing was an interference and the arm would not
    enter. It takes design_rules' CALIBRATED sliding clearance now.

    Jonathan, at the bench 2026-08-31: "the actual horn tips dont fit in
    anywhere".

    arm_r / arm_w are MEASURED, not datasheet - specs/robotarm/_horn_numbers.md
    (caliper 2026-08-28: the model said the micro hub was 8.0 and it is 6.8,
    which had made every press pocket in this project 1.35 loose).

    The seat face is placed as LOW on the servo as the CASE allows - one
    running gap above the case top - because seat_z is what the host has to
    stand the servo off by, and every millimetre of it is arm width. The face
    then has to be thick enough to swallow the horn hub with `hub_margin`
    behind it, since the pinion's far face looks at the fork plate across a
    running gap and a proud hub would rub it.
    """
    from lib.design_rules import SLIDING_FIT_CLEARANCE_MM as _SLIDE
    from lib.servo import micro_arm_w as _arm_w
    if arm_w is None:
        arm_w = _arm_w(arm_r)
    if slot_clear is None:
        slot_clear = _SLIDE

    case_top = servo.tab_below_top + servo.tab_thk
    boss_top = case_top + servo.boss_h
    blade_top = boss_top + servo.horn_blade_thk
    hub_top = boss_top + servo.horn_hub_h

    # SEAT AS LOW ON THE SERVO AS THE CASE ALLOWS. This used to be
    # hub_top - face + recess, which pinned the pinion's FAR face a fixed
    # hair above the horn hub - an arbitrary constraint that made seat_z grow
    # with the face width. At face 10.0 it put the seat face 0.80 mm INSIDE
    # the case and the case_gap check below caught it.
    #
    # The real constraints are: clear the case top by a running gap, and be
    # thick enough to swallow the hub. Seating on the first of those makes
    # seat_z - and so the whole standoff the host has to grow - as small as
    # it can be, which is the point of the through bore in the first place.
    seat_z = case_top + case_gap
    m = HornPinion(
        servo_name=servo.name,
        seat_z=seat_z,
        face=pair.face,
        bore_d=servo.horn_hub_dia + press,
        press_from=boss_top - seat_z,
        press_to=hub_top - seat_z,
        slot_r=arm_r,
        slot_w=arm_w + slot_clear,
        slot_depth=(blade_top - seat_z) + slot_extra,
        case_gap=seat_z - case_top,
    )

    bad = []
    if m.case_gap < 0.4:
        bad.append('the pinion seat face would sit %.2f mm off the %s case '
                   'top - it needs a running gap, not a rub'
                   % (m.case_gap, servo.name))
    if m.press_to > pair.face - hub_margin:
        bad.append('the horn hub tops out %.2f mm into a %.2f face and wants '
                   '%.2f of margin behind it - it would stand proud of the '
                   'pinion and foul the plate'
                   % (m.press_to, pair.face, hub_margin))
    if m.slot_depth > pair.face:
        bad.append('the horn arm slot is %.2f deep in a %.2f face'
                   % (m.slot_depth, pair.face))
    if m.bore_d / 2 < servo.boss_dia / 2:
        bad.append('the %.2f bore will not pass the %.2f output boss'
                   % (m.bore_d, servo.boss_dia))
    wall = pair.r_root(pair.z_pinion) - m.bore_d / 2
    if wall < 1.6:
        bad.append('only %.2f mm between the bore and the tooth roots' % wall)
    if pair.r_root(pair.z_pinion) - arm_r < 1.6:
        bad.append('only %.2f mm between the horn arm slot and the tooth roots'
                   % (pair.r_root(pair.z_pinion) - arm_r))
    assert not bad, ('%s pinion mount is not buildable: ' % servo.name
                     + '; '.join(bad))
    return m


from lib.servo_hub import spline_hub  # noqa: E402

J3_MOUNT = horn_pinion(J3_SERVO, J3_PAIR)

# HOW MUCH SPLINE THE PINION HAS TO GRIP, PRICED RATHER THAN DEFAULTED
# -------------------------------------------------------------------------
# lib/servo_hub.spline_hub() takes `engage_min` and defaults it to 2.00 mm.
# That default is fine on a joint nobody has thought about; J3 is not one.
# The J3 pinion drives the ENTIRE forearm, wrist, head and payload through a
# 2:1, and on an SG90 it does it through 2.50 mm of broached PETG - all the
# spline an SG90 has, against the MG90S's 4.00. Letting a library default
# decide whether that is enough is exactly the "decoration, not a contract"
# failure, so the floor is DERIVED here and passed IN.
#
# THE SHEAR ARITHMETIC. The broach is a round hole the steel spline cuts its
# own form into, so what carries the torque is the cylindrical surface at the
# bore. Torque T (N.mm) on a bore of diameter d over an engaged length L:
#
#     tangential force   F   = T / (d/2)          = 2T/d
#     sheared area       A   = pi * d * L
#     shear stress       tau = F/A = 2T / (pi d^2 L)
#     so                 L  >= 2T / (pi d^2 tau_allow)
#
# THE ALLOWABLE. PETG_TENSILE_MPA 35.0 in plane, x PETG_SHEAR_FACTOR, over
# design_rules SAFETY_FACTOR['cyclic'] 4.0 - the same allowable the tooth
# roots are checked against, because it is the same material loaded the same
# number of times. IN PLANE is right here and it is worth saying why: the
# pinion prints tooth-face-on-the-bed with the bore vertical, so this shear
# runs WITHIN each layer, not across the layer boundaries. Print it on its
# side and Z_TENSILE_FACTOR would halve everything below.
#
# WHAT IT COMES OUT AT, and this is the honest answer rather than the
# comfortable one:
#
#     SG90   T 156.91 N.mm, d 4.65 -> tau 1.85 MPa at L 2.50, floor L 0.88
#     MG90S  T 196.13 N.mm, d 4.75 -> tau 1.38 MPa at L 4.00, floor L 1.05
#
# SO SHEAR IS NOT WHAT BINDS, and the SG90 is not close to it - 2.50 mm is
# 2.8x the length the torque needs. The swap raises the stress in this joint
# by 34 % (1.38 -> 1.85 MPa) and it is still at 35 % of an allowable that
# already carries a safety factor of 4. The 20 % LOWER stall torque is doing
# real work here: the spline sees the SERVO's torque, not the joint's, so
# the 2:1 that multiplies the elbow's output is entirely downstream of it.
#
# WHAT DOES BIND IS THE FLOOR BELOW, AND IT IS NOT A STRESS AT ALL. 2.00 mm
# is a MANUFACTURING floor: it is how much broached bore is needed for the
# steel to form a usable tooth trace in PETG rather than skive a short lip,
# and it is ASSUMED - specs/robotarm/_gauge_broach_sheet.md is the print that
# settles it and it has not been run. 2.50 clears it by 0.50 mm, 25 %.
#
# AND THE MARGIN CANNOT BE BOUGHT. `engaged` is min(hub top, spline top) less
# the boss top, and with a 10.00 face the hub top is far above the spline, so
# engaged IS spline_h - the whole spline and not a millimetre more. A thicker
# gear buys nothing. That is the real exposure and it is stated rather than
# hidden: spline_h 2.50 is DATASHEET for a cheap servo, and lib/servo.py's
# own docstring rates that grade weak. A spline 0.5 shorter than the drawing
# puts this joint ON the floor. CALIPER IT before the pinion prints.
PETG_SHEAR_FACTOR = 0.6            # HANDBOOK - ductile polymer, shear/tensile

# ASSUMED. The least broached length that forms a tooth trace rather than a
# lip. specs/robotarm/_gauge_broach_sheet.md is the print that promotes it.
SPLINE_BROACH_MIN_FORM_MM = 2.0


def broach_shear_floor_mm(servo, torque_nm, bore_d=None,
                          shear_factor=PETG_SHEAR_FACTOR):
    """Least engaged spline length that carries `torque_nm` in shear, mm.

    See the block above for the derivation. `bore_d` defaults to the broach
    bore lib/servo.py sizes for this servo, so the two cannot disagree.
    """
    from lib.servo import spline_bore_d
    d = spline_bore_d(servo) if bore_d is None else bore_d
    tau = PETG_TENSILE_MPA * shear_factor / SAFETY_FACTOR['cyclic']
    return 2.0 * (torque_nm * 1000.0) / (math.pi * d * d * tau)


J3_BROACH_SHEAR_FLOOR_MM = broach_shear_floor_mm(J3_SERVO, J3_INPUT_STALL_NM)
# THE LARGER OF THE TWO FLOORS, and it is written as a max so that whichever
# one binds is visible in the diagnostics rather than assumed. Today the
# forming floor binds on both servos, which is the useful thing to know.
J3_ENGAGE_FLOOR_MM = max(J3_BROACH_SHEAR_FLOOR_MM, SPLINE_BROACH_MIN_FORM_MM)


# --- THE HORN IS OUT OF THE LOAD PATH. -----------------------------------
# Jonathan, 2026-08-31: "we should not [mount] at the horns but rather add
# gears that we make". The pinion now bores onto the servo's own SPLINE and
# the horn is not used at all - see lib/servo_hub.spline_hub() for why the
# spline teeth are not printed (they are a third of MIN_FEATURE_MM) and why a
# broached round bore is what replaces them.
#
# IT COSTS NOTHING AND IT WAS THE CHEAPEST OF THE THREE OPTIONS PRICED
# (gear plane in the SERVO's frame, MG90S first, SG90 as built today):
#   pressed on the horn   gear plane  5.90 / 7.10  varies by batch, no fit
#   bolted horn adapter   gear plane 18.50 / 17.10 +12.60 mm of forearm width
#   ON THE SPLINE         gear plane  5.90 / 7.10  +0.00, and no horn at all
#
# J3_PAIR IS UNCHANGED BY THE SERVO SWAP TOO, and that is the thing worth
# checking rather than assuming - m1.00 18T/36T, centre 27.20, gear Oe38.0
# survives because the pinion's root radius has to clear the BOSS BORE, and
# the SG90's boss is SMALLER than the MG90S's:
#   MG90S  boss Oe6.0 -> bore Oe6.40 -> root floor 4.80
#   SG90   boss Oe5.0 -> bore Oe5.40 -> root floor 4.30
# An 18T pinion at m1.00 roots at 7.75, which was clear by 2.95 and is now
# clear by 3.45. The swap makes the compact gears MORE comfortable, not less.
# The assert below is what actually says so.
#
# J3_MOUNT is kept above ONLY because forearm.py still reads its seat_z, and
# the two agree to the millimetre (both 7.10 on the SG90, both 5.90 on the
# MG90S) - which is why the forearm's standoff arithmetic needs no rework.
# It should be deleted once j3_pinion and _check_elbow read J3_HUB directly.
J3_HUB = spline_hub(J3_SERVO, J3_PAIR.face,
                    engage_min=J3_ENGAGE_FLOOR_MM)
assert abs(J3_HUB.seat_z - J3_MOUNT.seat_z) < 1e-9, (
    'the spline hub seats at %.2f and the horn press at %.2f - forearm.py '
    'stands the servo off by one of them and would now be wrong'
    % (J3_HUB.seat_z, J3_MOUNT.seat_z))
assert J3_PAIR.r_root(J3_PAIR.z_pinion) >= J3_HUB.min_gear_root_r, (
    'an %dT pinion roots at %.2f, inside the %.2f floor the boss bore sets'
    % (J3_PAIR.z_pinion, J3_PAIR.r_root(J3_PAIR.z_pinion),
       J3_HUB.min_gear_root_r))

# What the drive costs the part that carries the servo. forearm.py adds its
# own plate chain to this; _check_elbow.py asserts the two agree.
#
#   standoff = (gear band outboard face) - seat_z - (lobe outer face today)
#
# which is 10.80 mm of extra forearm width, NOT the 7 the handoff claimed and
# not the 14.40 a blind-pocketed pinion would have cost. It is the SAME 10.80
# on an SG90 as on an MG90S, and that is arithmetic rather than luck:
# seat_z is the case top plus one running gap, the lobe IS the case top, and
# the two cancel. lib/joints.j3_standoff() states the cancellation and
# forearm.py asserts its own expression against it.
J3_MOUNT_SEAT_Z = J3_MOUNT.seat_z
