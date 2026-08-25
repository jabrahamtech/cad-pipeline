"""Shared geometry for the two-servo claw.

ONE SERVO PER FINGER. No gears, no rack, no linkage: each finger bolts
straight to its own horn and swings. That is the whole mechanism, and it is
why the hand is two printed designs instead of five.

WHAT IT COSTS, said plainly. The fingers ROTATE, so their faces only meet
flush at one opening and roll off anything wider or narrower. Grip force is
servo torque over finger radius — 0.50 kgf per finger at stall, 0.25 at the
50 % duty limit, against the 0.75 the rack-and-pinion managed at a much
shorter radius. Both are far more than a 32 g payload needs.

FRAME shared by all the hand parts:
    z = 0   the mounting face that bolts to wrist_rotator; the part grows +Z,
            which is FORWARD along the arm.
    x       the fingers close along X toward the centreline x = 0.
    y       the servo shafts run along +Y. Their bodies hang behind the
            uprights at -y and the fingers swing in a plane at +y, which is
            what keeps the hand's centre of mass on the roll axis.
    Each finger pivots about (+/-PIVOT_X, PIVOT_Z) in the XZ plane.

THE TWO FINGERS ARE ONE PRINTED PART. Finger R is finger L turned 180 deg
about the shaft axis — which flips it over, so the horn pocket has to go
CLEAN THROUGH the finger rather than being a blind recess in one face. That
is the only reason the pocket is a through-cut, and it is why the horn's own
screw needs a washer under its head.
"""

from __future__ import annotations

import math

from lib.servo import SG90

# --- the servos and where they pivot
PIVOT_X = 19.0             # each finger's axis, from the centreline
PIVOT_Z = 26.0             # and above the mounting face
# 19, not less: each root has to swallow the SG90's 32 mm cross horn, so it
# is an 18 mm disc, and two of those cannot be closer than 36 mm apart.
ROOT_R = 18.0

# --- the finger
FINGER_T = 4.5             # blade thickness, along Y
FINGER_R = 36.0            # pivot to tip centre
TIP_R = 7.0
SWEEP_DEG = 35.0           # how far the servo actually turns

# DERIVED, not chosen: the angle at which the two tips just touch. It depends
# on the tip radius, so hardcoding it means the fingers silently stop closing
# the moment the blade changes.
CLOSED_DEG = math.degrees(math.acos((PIVOT_X - TIP_R) / FINGER_R))
OPEN_DEG = CLOSED_DEG + SWEEP_DEG

# --- the base
BASE_T = 4.0               # the plate that bolts to wrist_rotator
UPRIGHT_T = 4.0            # each servo's mounting wall
UPRIGHT_HALF_W = 10.0      # either side of its pivot; leaves 3.8 mm
                           # of wall beside the case aperture
UPRIGHT_FACE_Y = 2.0       # +y face of the uprights: the tabs bear here
BASE_HALF_Y = 16.0
GRIP_GROOVE = 1.2


def opening(angle_deg: float) -> float:
    """Gap between the two finger tips at a given finger angle."""
    return 2.0 * ((PIVOT_X - TIP_R)
                  - FINGER_R * math.cos(math.radians(angle_deg)))


def tip_centre(angle_deg: float) -> tuple[float, float]:
    """(x, z) of the LEFT finger's tip centre, in the hand frame."""
    a = math.radians(angle_deg)
    return (-PIVOT_X + FINGER_R * math.cos(a),
            PIVOT_Z + FINGER_R * math.sin(a))


def grip_kgf(radius: float = FINGER_R) -> float:
    """What one finger can push at its tip, at stall."""
    return SG90.stall_kgcm / (radius / 10.0)


# The plane the fingers swing in: just clear of the horns, which stand
# mount_to_horn off the face the tabs bear on. mount_to_horn, NOT horn_seat —
# the tabs sit a tab thickness proud of the upright.
FINGER_PLANE_Y = UPRIGHT_FACE_Y + SG90.mount_to_horn
