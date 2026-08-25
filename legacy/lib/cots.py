"""Stand-in solids for BOUGHT parts, for pictures only.

NOTHING HERE IS EVER PRINTED OR EXPORTED. Bearings, servos and fasteners are
COTS items (CLAUDE.md, "Standard components"), so the pipeline deliberately
does not model them as geometry. But leaving them out of a render is its own
kind of lie: a turntable drawn without its bearings looks like a disc
levitating over a 12 mm air gap, and a drum drawn without its servo looks
like an empty can.

These are crude — a bearing is a ring, a servo is a box with tabs — because
their only job is to make an assembly drawing legible. They are never
booleaned against a printed part and never reach exports/ or a build plate.

Dimensions come from lib/bearings.py and lib/servo.py, so a stand-in cannot
drift away from the pockets the real parts have to fit.
"""

from __future__ import annotations

from typing import cast

from build123d import Box, Cylinder, Part, Pos, Rotation

from lib.bearings import B608ZZ, BearingSpec
from lib.servo import ServoSpec

STEEL = "#454b54"      # dark, so steel reads against printed parts
SERVO_BODY = "#23262b"
SERVO_HORN = "#e8e4d9"


def bearing(spec: BearingSpec = B608ZZ) -> Part:
    """Deep-groove bearing as an outer ring, a shield face and an inner ring.
    Built about the origin with its axis along Y — the same convention the
    roller forks use."""
    axis = Rotation(90, 0, 0)
    outer = cast(Part, axis * Cylinder(spec.od / 2, spec.width))
    bore = cast(Part, axis * Cylinder(spec.bore / 2, spec.width + 2))
    body = cast(Part, outer - bore)
    # a shallow step so the shield reads as a separate face
    step = cast(Part, axis * Cylinder(spec.od / 2 - 1.2, spec.width - 1.6))
    ring = cast(Part, body - step + (
        axis * Cylinder(spec.inner_race_od / 2, spec.width) - bore))
    return cast(Part, Part() + ring)


def servo(spec: ServoSpec, horn: bool = True) -> Part:
    """Servo stand-in in lib.servo's own frame: shaft on +Z at the origin,
    flange top face at z = 0, case centred at x = shaft_offset."""
    l, w, h = spec.case
    case = cast(Part, Pos(spec.shaft_offset, 0.0,
                          (spec.case_above_flange - spec.below_flange) / 2)
                * Box(l, w, h))
    tabs = cast(Part, Pos(spec.shaft_offset, 0.0, -spec.tab_thick / 2)
                * Box(spec.tab_span, w, spec.tab_thick))
    boss = cast(Part, Pos(0, 0, spec.horn_seat / 2)
                * Cylinder(spec.shaft_dia * 1.25, spec.horn_seat))
    body = cast(Part, case + tabs + boss)
    if horn:
        arm = cast(Part, Pos(0, 0, spec.horn_seat + spec.horn_thick / 2)
                   * Box(spec.horn_span, spec.horn_arm_w, spec.horn_thick))
        cross = cast(Part, Pos(0, 0, spec.horn_seat + spec.horn_thick / 2)
                     * Box(spec.horn_arm_w, spec.horn_span, spec.horn_thick))
        body = cast(Part, body + arm + cross)
    return cast(Part, Part() + body)


# A 3-core servo lead. Real ones are a flat ribbon; this is the envelope it
# needs, which is what a pocket has to clear.
LEAD_W = 6.0          # across the ribbon
LEAD_T = 2.5          # through it
# Only the stiff bit right at the case: the moulded strain-relief boot and
# the first few mm. Beyond that a real lead bends, so modelling it as a long
# rigid stub would flag clashes that do not exist — what a pocket has to
# provide is room for the wire to LEAVE and TURN, not a straight tunnel.
LEAD_RUN = 10.0


def servo_with_lead(spec: ServoSpec, horn: bool = True,
                    lead_side: float = 1.0) -> Part:
    """The servo AND the lead coming out of the side of its case, near the
    bottom. This is the shape a mounting pocket really has to swallow — a
    pocket cut to the bare case pinches the wire and the servo will not seat.
    """
    body = servo(spec, horn=horn)
    w = spec.case[1]
    z = -spec.below_flange + LEAD_W / 2 + 2.0
    lead = cast(Part, Pos(spec.shaft_offset,
                          lead_side * (w / 2 + LEAD_RUN / 2), z)
                * Box(LEAD_W, LEAD_RUN, LEAD_T))
    return cast(Part, Part() + (body + lead))


def m8_bolt(length: float = 30.0) -> Part:
    """Roller axle stand-in: hex head, plain shank, nyloc nut. Axis along Y."""
    axis = Rotation(90, 0, 0)
    shank = cast(Part, axis * Cylinder(4.0, length))
    head = cast(Part, Pos(0, -length / 2 - 2.65, 0) * axis
                * Cylinder(7.3, 5.3))
    nut = cast(Part, Pos(0, length / 2 - 4.0, 0) * axis * Cylinder(7.3, 8.0))
    return cast(Part, Part() + (shank + head + nut))
