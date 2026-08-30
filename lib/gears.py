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

WHY MODULE 1.25 AND NOT THE HANDBOOK'S 1.5. design_rules.py prefers 1.5 for
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
LEWIS_Y = {12: 0.245, 14: 0.261, 16: 0.277, 17: 0.303, 18: 0.309,
           20: 0.322, 24: 0.337, 32: 0.364, 34: 0.371, 36: 0.377}


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
J3_PAIR = SpurPair(name='J3', module=1.25, z_pinion=18, z_gear=36, face=8.0)

# MG90S stall, lib/servo.py, in N.m: 2.0 kg.cm x 9.80665 / 100.
J3_INPUT_STALL_NM = 2.0 * 9.80665 / 100.0

# What the reduction does to the joint, for anything that reports it.
J3_SERVO_TRAVEL_DEG = 180.0
J3_JOINT_TRAVEL_DEG = J3_SERVO_TRAVEL_DEG / J3_PAIR.ratio

_bad = J3_PAIR.validate(J3_INPUT_STALL_NM)
assert not _bad, 'J3_PAIR is not buildable: ' + '; '.join(_bad)
