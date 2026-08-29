"""Kinematics of the pruner's blade linkage.

THE PINION IS CENTRED ON y = 0, NOT BEHIND IT. Its face and the rack's are
the same 8 mm and coincident, so the disc occupies y in [-4, +4] - not
[-8, 0], which is what this file assumed at first and which put the drive
pin 2 mm INSIDE the disc at mid-sweep. The gripper's own jaw arm already
recorded the right answer: it starts at half_face + arm_clear = 4.4 mm.

Plain Python, no Fusion. `models/robotarm/pruner_*.py` imports this so the
CAD and the numbers below cannot drift apart, and `tests/` exercises it.

Frame (the effector's own, shared with the gripper):
    X  jaw opening, the direction the racks travel
    Y  forward, out of the hand
    Z  rack separation; the pinion axis is +Y

One blade per rack. The blade pivots on a post fixed to the SHELL at
(-pivot_x, pivot_y) for the -X blade, mirrored for the other. Its nose
carries the cutting edge and reaches in toward the centreline; its tail runs
back to a pin carried by the rack, which drives it through a short slot.

THE PIVOT CANNOT SIT NEAR THE CENTRELINE. The pinion is a disc of tip radius
gr_r_tip in the XZ plane spanning y in [-gr_face, 0], and the blades have to
shear at z ~ 0, right through it. So the tail has to run OUTBOARD of the
pinion for that whole band of y. `clears_pinion` is that check, and it is
what sets pivot_x - not styling, not packaging.

Mechanical advantage is R/r: the perpendicular distance from the pivot to
the drive force, over the distance from the pivot to where the stem sits.
It is therefore not one number. A stem pushed deep into the throat cuts at
small r and high advantage; the same stem at the blade tip cuts at large r
and may not cut at all. That is true of every bypass pruner ever made and
it is a technique instruction, not a defect - but it does mean the quoted
figure has to say WHERE.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# From the gripper, unchanged - see models/robotarm/gripper_pinion.py
R_TIP_MM = 10.5
FACE_MM = 8.0
RACK_OFFSET_MM = 9.2
SERVO_STALL_KGCM = 1.6
CUT_DERATE = 0.7          # a cut is a brief event, not a static hold
DRIVE_EFF = 0.7           # horn + mesh + channel friction
R_PITCH_MM = 9.0
PIN_DIA_MM = 3.0          # drive pin, same nominal as the pivot screw
ARM_CLEAR_MM = 0.4        # what the gripper's own jaw arm clears the disc by
SLIDE_MM = 0.25           # sliding fit, design_rules CALIBRATED
WALL_MM = 1.6             # design_rules MIN_WALL_MM
KGF_N = 9.807


@dataclass(frozen=True)
class Layout:
    pivot_x: float        # blade pivot, distance from the centreline
    pivot_y: float        # blade pivot, forward of the pinion axis
    tail_r: float         # pivot to the drive pin
    knee_x: float         # dog-leg knee, distance from the centreline
    knee_y: float         # dog-leg knee, forward of the pinion axis
    edge_offset: float    # perpendicular distance from the PIVOT to the edge
    throat_r: float       # pivot to where the stem sits, at the THROAT ROOT
    tip_r: float          # pivot to the far end of the usable edge
    half_sweep_deg: float # blade rotation each way from centre

    @property
    def rack_travel_mm(self) -> float:  # noqa: D401
        """Rack travel needed for the full sweep.

        THE SLOT IS RADIAL, so the pin lies on the line through the pivot at
        the blade's own angle, and s = tail_r * TAN(theta) - not sin, and not
        the arc length. Two earlier versions used each of those. `sin` is the
        one that hurt: it looks right, it is only 4 % off in travel, and it
        puts the pin on a path that wanders 1.5 mm sideways in the blade's
        frame - straight out through the wall of its own slot. It cost
        10.65 mm3 of rack buried in blade before anything caught it.
        """
        # The sweep runs from 0 (mouth fully open, edges parallel) to
        # half_sweep_deg (crossed in to crossing_r), one-sided - not +/-.
        return self.tail_r * math.tan(math.radians(self.half_sweep_deg))

    def theta_for_travel(self, s_mm: float) -> float:
        """Blade angle, radians, at rack travel s from mid-stroke."""
        return math.atan(s_mm / self.tail_r)

    @property
    def tail_past_pin_mm(self) -> float:
        """How far the tail runs BEYOND its drive pin, to close the slot.

        Not a constant. It is the slot's own length past the pin - which grows
        with the sweep, because the pin's distance from the pivot is
        tail_r / cos(theta) - plus half the slot width, the fit, and a wall.
        Hard-coding it at 6.3 was fine at a 27 deg sweep and 4.9 mm short at
        45 deg, which put the tail end back inside the pinion. THIS is the end
        that has to clear, not the pin.
        """
        return ((self.pin_r_far_mm - self.tail_r)
                + PIN_DIA_MM / 2 + SLIDE_MM / 2 + WALL_MM)

    @property
    def pin_r_far_mm(self) -> float:
        """Pin distance from the pivot at full sweep - how far the slot runs.
        Radial slot, so it is tail_r / cos(theta)."""
        return self.tail_r / math.cos(math.radians(self.half_sweep_deg))

    @property
    def throat_open_mm(self) -> float:
        """Widest the jaws open, at theta = 0.

        With the edges offset, the two of them are PARALLEL at theta = 0 and
        exactly 2 * edge_offset apart along their whole length. That is the
        mouth: it does not taper, and it is what bounds the stem this tool
        can admit at all.
        """
        return 2 * self.edge_offset

    def gap_at(self, r: float, theta_rad: float) -> float:
        """In-plane gap between the two edges at radius r. Negative = crossed."""
        return 2 * (self.edge_offset - r * math.sin(theta_rad)) / math.cos(theta_rad)

    def crossing_r(self, theta_rad: float) -> float:
        """Radius of the single point where the two edges cross.

        THIS IS THE WHOLE MECHANISM, and the first build did not have it. With
        both edges lying ON the pivot the two straight lines meet at the pivot
        and nowhere else, and at theta = 0 they go coincident along their whole
        length at once: the entire stem section shears in one instant, with no
        travelling contact and therefore no scissor advantage whatsoever. It is
        a V-pinch with a nice pivot. Offsetting each edge by `edge_offset` gives
        exactly one crossing, at a / sin(theta), which sweeps in from the tip as
        the blades close - which is what a pair of scissors is.
        """
        st = math.sin(theta_rad)
        return float('inf') if st <= 1e-12 else self.edge_offset / st

    def theta_for_crossing(self, r: float) -> float:
        """Blade angle at which the cut reaches radius r."""
        return math.asin(min(1.0, self.edge_offset / r))

    def ma_at_cut(self, r: float) -> float:
        """Advantage at the instant the crossing passes radius r.

        At that instant gap = 0, so a = r sin(theta) and the awkward term in
        d(gap)/dtheta vanishes, leaving -2r. With s = tail_r tan(theta) and
        BOTH racks pushing, MA = tail_r / (r cos^2 theta).
        """
        th = self.theta_for_crossing(r)
        return self.tail_r / (r * math.cos(th) ** 2)

    def ma_numeric(self, theta_rad: float = 0.0, h: float = 1e-6) -> float:
        """Mechanical advantage by differentiating the actual kinematics.

        Both racks push, so the work in is 2 F ds; the output closes the
        throat by d(gap). MA = 2 (ds/dtheta) / (dgap/dtheta).

        This exists to cross-check `ma()`, which is the closed form. An
        earlier version of this file asserted instead that MA equals rack
        travel over throat opening - which is the AVERAGE over the whole
        stroke, most of which is spent closing empty air. The instantaneous
        figure at the cut is the one the force claim rests on, and it is
        roughly half the average. Both are real; only one is the answer.
        """
        def s_of(t):
            return self.tail_r * math.tan(t)

        def gap_of(t):
            return 2 * self.throat_r * math.sin(t)

        ds = (s_of(theta_rad + h) - s_of(theta_rad - h)) / (2 * h)
        dg = (gap_of(theta_rad + h) - gap_of(theta_rad - h)) / (2 * h)
        return 2 * ds / dg

    def ma(self, r: float) -> float:
        """Kept for the tip/root falloff comparison. `ma_at_cut` is the one
        the force claim uses - it accounts for the sec^2 term."""
        return self.tail_r / r

    def slot_travel_mm(self) -> float:
        """Radial movement the drive slot has to absorb over the sweep."""
        return self.tail_r * (1 - math.cos(math.radians(self.half_sweep_deg)))

    def tail_path(self, theta_deg: float):
        """Pivot -> knee -> pin, in the blade's own plane, at this rotation.

        A STRAIGHT tail cannot be used. It would have to cross the pinion, and
        pushing the pivot outboard far enough to miss it drops the mechanical
        advantage to 2.7 - the difference between cutting a 4 mm stem and a
        7 mm one. The tail is therefore a dog-leg: out to a knee that clears
        the pinion, then back in to the pin. Both segments rotate rigidly with
        the blade, so this is one printed arm, not a linkage.
        """
        th = math.radians(theta_deg)
        c, s_ = math.cos(th), math.sin(th)

        def rot(x, y):
            dx, dy = x + self.pivot_x, y - self.pivot_y
            return (-self.pivot_x + dx * c - dy * s_,
                    self.pivot_y + dx * s_ + dy * c)

        pivot = (-self.pivot_x, self.pivot_y)
        knee = rot(-self.knee_x, self.knee_y)
        pin = rot(-self.pivot_x, self.pivot_y - self.tail_r)
        return [pivot, knee, pin]

    def clears_pinion(self, z_blade: float = 0.0) -> tuple[bool, float]:
        """Does the tail stay outboard of the pinion through the whole sweep?

        The pinion's half width at the blade's own height z is
        sqrt(r_tip^2 - z^2), over y in [-face, 0]. Returns (ok, worst mm).
        """
        if abs(z_blade) >= R_TIP_MM:
            return True, float('inf')
        half = math.sqrt(R_TIP_MM ** 2 - z_blade ** 2)
        worst = float('inf')
        for i in range(-20, 21):
            pts = self.tail_path(self.half_sweep_deg * i / 20.0)
            for a, b in zip(pts, pts[1:]):
                for j in range(41):
                    t = j / 40.0
                    x = a[0] + t * (b[0] - a[0])
                    y = a[1] + t * (b[1] - a[1])
                    if -FACE_MM / 2 <= y <= FACE_MM / 2:
                        worst = min(worst, abs(x) - half)
        return worst > 0, worst

    def within_shell(self, half_x: float, back_y: float) -> tuple[bool, float]:
        """The swinging tail has to stay inside the clamshell."""
        worst = float('inf')
        for i in range(-20, 21):
            for x, y in self.tail_path(self.half_sweep_deg * i / 20.0):
                worst = min(worst, half_x - abs(x), y - back_y)
        return worst > 0, worst


def rack_force_N() -> float:
    torque = SERVO_STALL_KGCM * CUT_DERATE
    return torque / (R_PITCH_MM / 10.0) * DRIVE_EFF * KGF_N


def cut_force_N(lay: Layout, r: float) -> float:
    return rack_force_N() * lay.ma(r)


def stem_mm(force_N: float, progression: float, n_per_mm: float = 10.0) -> float:
    """Stem a given blade force will sever. `progression` is the credit taken
    for an angled edge cutting a slice at a time instead of the whole chord -
    ASSUMED, and the softest number in the whole design."""
    return force_N * progression / n_per_mm


# --- the chosen layout ---------------------------------------------------
#
# Searched over pivot position, tail length and sweep, subject to: the tail
# clears the pinion by >= 1.0 mm through the whole sweep, the tail stays
# inside the clamshell, the throat opens >= 10 mm, and rack travel fits the
# 20.0 mm the gripper already uses. 61 layouts survived; this is the one with
# the most advantage at the throat root.
#
# THE TAIL RUNS FORWARD OF THE PINION, NOT AROUND IT. Every attempt to route
# it back past the pinion failed: a straight tail has to cross the disc, and
# a dog-legged one swings its own knee back into it - the knee sits at radius
# from the pivot, so it sweeps too. Pushing the pivot outboard far enough to
# miss the disc drops the advantage to 2.7. Putting the whole tail forward of
# y = 0, where there is no pinion at all, costs nothing and needs no dodge.
# THE ADVANTAGE IS BOUGHT WITH SERVO SWEEP, NOT WITH GEOMETRY. Because
# MA = rack travel / throat opening, and the throat has to open far enough to
# get a stem into it, the only free variable left is how far the rack travels
# - and that is r_pitch x servo sweep. The gripper uses 127 deg of the SG90's
# 180. The pruner uses all of it: 28.3 mm of rack travel instead of 20.0.
# That single change is worth 40 % more cutting force and costs nothing but
# firmware.
# The pivot sits far enough FORWARD that the drive pin, 26 mm back down the
# tail, lands at y = +11, and the tail's own far END - 6.3 mm further back
# again - lands at 4.7, clear of the disc's y = +4 by the 0.4 the gripper's jaw
# arm uses. Earlier versions put the pivot at 24, 28, 31 and 32 and fouled the
# disc every time: by assuming the disc sat behind y = 0, then by treating the
# pin as a point rather than a cylinder, then by forgetting the tail runs past
# the pin at all. Each is now an assertion, because each looked fine.
# SHORTENED, THEN REVERTED, 2026-08-29. Recorded because the reasoning is
# the useful part and someone will propose it again.
#
# tail_r 26 -> 21 was tried to buy elbow margin. tail_r IS the mechanical
# advantage one for one, so it cost 19 % of cutting force: 31.5 -> 25.4 N at
# the throat, and the claimed stem on the pessimistic progression fell from
# 6.3 to 5.06 mm against a committed 5.0 floor.
#
# It bought THREE POINTS of J3 duty, 88 % -> 85 %, not the ten that were
# projected. The projection assumed a 9 mm shorter head moves 9 mm inboard.
# It does not: the SG90 bay in the tail is half the head's mass and does not
# move at all, so mass-weighted the head COM moved 1.46 mm. Only the payload
# really moved, 6.5 mm, riding on pivot_y.
#
# A fifth of the cutting force for three points of a STATIC margin is a bad
# trade, so this is back where it was. If the elbow needs margin, it is
# cheaper to find it anywhere other than tail_r.
#
# What was KEPT: ps_cheek_front's pad, 6.0 -> 3.5 mm past the pivot. That is
# pure padding - 3.2 mm is needed for the bore and its wall - so it is 2.5 mm
# of head length for no mechanical cost at all.
CHOSEN = Layout(
    pivot_x=0.0,        # common pivot, true scissors: the two blades share a
    pivot_y=42.0,       # post, which is what keeps the crossing angle shallow
    tail_r=26.0,
    knee_x=0.0,
    knee_y=29.0,
    edge_offset=3.5,    # THE cut-or-crush parameter. See crossing_r().
    throat_r=8.5,       # nominal stem position, measured from the pivot
    tip_r=20.0,         # far end of the usable edge
    half_sweep_deg=40.0,
)


def report(min_r: float = 6.5) -> str:
    lay = CHOSEN
    lines = [
        'rack force        %.1f N  (SG90 at %.2f x stall, eff %.2f, r %.1f)'
        % (rack_force_N(), CUT_DERATE, DRIVE_EFF, R_PITCH_MM),
        'mouth opens       %.1f mm  (2 x edge offset; the edges are PARALLEL at'
        ' theta 0)' % lay.throat_open_mm,
        'rack travel       %.1f mm, one-sided, theta 0 -> %.0f deg'
        % (lay.rack_travel_mm, lay.half_sweep_deg),
        'crossing sweeps   r %.1f -> %.1f mm as it closes'
        % (lay.crossing_r(lay.theta_for_crossing(lay.tip_r)),
           lay.crossing_r(math.radians(lay.half_sweep_deg))),
        '',
        '%8s %8s %8s %8s   %s' % ('cut at r', 'theta', 'MA', 'force N', 'stem x2/x3'),
    ]
    for r in (16.0, 12.0, lay.throat_r, 7.5, min_r):
        ma = lay.ma_at_cut(r)
        f = rack_force_N() * ma
        lines.append('%8.1f %7.1fd %8.2f %8.1f   %.1f / %.1f mm'
                     % (r, math.degrees(lay.theta_for_crossing(r)), ma, f,
                        stem_mm(f, 2), stem_mm(f, 3)))
    return '\n'.join(lines)
