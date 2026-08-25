"""Hobby-servo dimensions and mounting negatives (SG90 / MG90S / MG995).

Every robotarm part that carries a servo cuts its pockets from here, so a
corrected dimension propagates to all of them.

FRAME CONVENTION (used by every function in this module)
    - output shaft on the +Z axis, shaft axis through the origin;
    - mounting-flange TOP face at z = 0 (the face a bracket bolts against),
      so the case hangs to z = -below_flange and rises to
      z = +case_above_flange, with the horn seating at z = horn_seat;
    - the case is longest along X. The shaft is NOT at the case centre:
      the case centre sits at x = +shaft_offset.

Dimensions are DATASHEET/common-catalogue values, not measured — the tolerant
features (oversize body pockets, a form-fitting horn pocket rather than
matched screw holes) are deliberate so a few tenths of error don't bite.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import cast

from build123d import Box, Cylinder, Part, Pos

from lib.design_rules import SLIDING_FIT_CLEARANCE_MM


@dataclass(frozen=True)
class ServoSpec:
    """One servo family. Lengths in mm."""

    name: str
    case: tuple[float, float, float]  # L x W x H of the plastic case
    below_flange: float               # case height below the mounting tabs
    tab_span: float                   # overall across both mounting tabs
    tab_thick: float
    tab_hole_dia: float               # the servo's own tab hole
    pilot_dia: float                  # printed pilot for the supplied screw
    hole_pitch_l: float               # tab hole spacing along X
    hole_pitch_w: float               # along Y (0.0 = single row of two)
    shaft_offset: float               # case centre - shaft, along +X
    shaft_dia: float
    horn_seat: float                  # z of the horn's underside
    horn_thick: float
    horn_span: float                  # tip-to-tip of the supplied cross horn
    horn_arm_w: float                 # widest arm width
    stall_kgcm: float

    @property
    def case_above_flange(self) -> float:
        return self.case[2] - self.below_flange

    @property
    def mount_to_horn(self) -> float:
        """From the face the tabs BEAR ON to the horn's underside.

        This — not horn_seat — is what a mounting stack has to add up, and
        getting it wrong by tab_thick puts the servo's tabs inside the
        bracket wall. horn_seat is measured from the flange's TOP face, but
        when a servo is dropped in from outside, the face that lands on the
        bracket is the flange's far side, one tab thickness further out.
        """
        return self.tab_thick + self.horn_seat

    @property
    def horn_face(self) -> float:
        """z of the horn's TOP face — where a driven link seats."""
        return self.horn_seat + self.horn_thick

    def tab_holes(self) -> list[tuple[float, float]]:
        """Tab-hole centres (x, y) in the servo frame.

        NOT symmetric about the shaft: the holes straddle the CASE centre,
        which sits shaft_offset away from the shaft. For an SG90 that gives
        -8.4 and +19.4, not +/-13.9. Position brackets off these values
        rather than assuming symmetry.
        """
        ys = [0.0] if self.hole_pitch_w == 0.0 else [
            -self.hole_pitch_w / 2, self.hole_pitch_w / 2
        ]
        return [
            (self.shaft_offset + sx * self.hole_pitch_l / 2, y)
            for sx in (-1.0, 1.0)
            for y in ys
        ]


# SG90 and MG90S share an outline; MG90S is metal-geared and stronger.
SG90 = ServoSpec(
    name="SG90",
    case=(22.8, 12.2, 22.5),
    below_flange=15.9,
    tab_span=32.5,
    tab_thick=2.5,
    tab_hole_dia=2.2,
    pilot_dia=1.8,
    hole_pitch_l=27.8,
    hole_pitch_w=0.0,
    shaft_offset=5.5,      # 22.8/2 - 5.9 (shaft 5.9 from the short end)
    shaft_dia=4.8,
    horn_seat=10.6,        # 6.6 case above the flange + 4.0 boss
    horn_thick=1.6,
    horn_span=32.0,
    horn_arm_w=7.0,
    stall_kgcm=1.8,
)

MG90S = replace(SG90, name="MG90S", stall_kgcm=2.2)

MG995 = ServoSpec(
    name="MG995",
    case=(40.7, 19.7, 42.9),
    below_flange=32.0,
    tab_span=54.5,
    tab_thick=3.0,
    tab_hole_dia=4.5,
    pilot_dia=3.2,
    hole_pitch_l=49.5,
    hole_pitch_w=10.0,
    shaft_offset=10.35,    # 40.7/2 - 10.0 (shaft 10.0 from the short end)
    shaft_dia=5.9,
    horn_seat=6.9,         # case above the flange, before the boss
    horn_thick=2.5,
    horn_span=54.0,
    horn_arm_w=9.0,
    stall_kgcm=11.0,
)

SERVOS = {s.name: s for s in (SG90, MG90S, MG995)}


# A servo's lead leaves the side of its case, so a pocket cut to the case
# alone pinches the wire and the servo will not seat. Every pocket gets a
# notch on BOTH side faces — both, so the servo can go in either way round.
LEAD_NOTCH_W = 7.0        # along the case
LEAD_NOTCH_D = 3.5        # out past the case face
LEAD_NOTCH_H = 7.0        # up from the bottom of the pocket


def case_pocket(
    spec: ServoSpec,
    clearance: float = SLIDING_FIT_CLEARANCE_MM,
    below: float | None = None,
    above: float = 0.0,
    lead_notch: bool = True,
) -> Part:
    """Drop-in pocket for the servo case, in the servo frame.

    `below` defaults to the full below-flange depth; pass more for a
    through-cut. `above` extends the pocket over the flange plane (use it
    when the case must also pass through the mounting plate).

    `lead_notch` adds a relief on each side face for the servo's own lead.
    Without it the pocket is cut to the case plus a sliding fit, and the
    wire has nowhere to go — the servo simply will not push home.
    """
    depth_below = spec.below_flange if below is None else below
    height = depth_below + above
    body = cast(
        Part,
        Pos(spec.shaft_offset, 0.0, above - height / 2)
        * Box(spec.case[0] + clearance, spec.case[1] + clearance, height),
    )
    if lead_notch:
        w = spec.case[1] + clearance
        notches = [
            Pos(spec.shaft_offset,
                side * (w / 2 + LEAD_NOTCH_D / 2),
                above - height + LEAD_NOTCH_H / 2)
            * Box(LEAD_NOTCH_W, LEAD_NOTCH_D + 0.02, LEAD_NOTCH_H)
            for side in (-1.0, 1.0)
        ]
        body = cast(Part, body + notches)
    return body


def tab_relief(
    spec: ServoSpec,
    clearance: float = SLIDING_FIT_CLEARANCE_MM,
    depth: float | None = None,
) -> Part:
    """Recess that sinks the mounting tabs flush into the mounting face
    (top of the recess at z = 0, i.e. the tabs end up below the face)."""
    d = spec.tab_thick + clearance if depth is None else depth
    return cast(
        Part,
        Pos(spec.shaft_offset, 0.0, -d / 2)
        * Box(spec.tab_span + clearance, spec.case[1] + clearance, d),
    )


def tab_pilots(spec: ServoSpec, depth: float,
               dia: float | None = None) -> Part:
    """Pilot holes for the supplied self-tapping screws, drilled DOWN from
    the flange plane (z = 0) by `depth`."""
    d = spec.pilot_dia if dia is None else dia
    holes = [
        Pos(x, y, -depth / 2) * Cylinder(d / 2, depth)
        for x, y in spec.tab_holes()
    ]
    return cast(Part, Part() + holes)


def horn_pocket(
    spec: ServoSpec,
    depth: float | None = None,
    clearance: float = 0.4,
    arms: int = 4,
    access_dia: float = 6.0,
    access_depth: float = 60.0,
) -> Part:
    """Form-fitting pocket for the supplied cross horn, for the DRIVEN part.

    Torque goes through the horn's arms bearing on pocket walls, not through
    the tiny horn screws — so it tolerates a horn that isn't quite the
    catalogue size, and it survives loads that would strip M2 screws.

    Built in the driven part's frame: the pocket mouth (the face that lands
    on the horn's top surface) is at z = 0 and the pocket goes UP into the
    part, with a screwdriver access bore continuing above it. Rotation axis
    is Z through the origin.

    `access_depth` defaults to 60 mm, which is deliberately longer than any
    part here is thick, so the bore always breaks through to the outside.
    On a TALL part it will keep going and tunnel through whatever sits above
    the pocket — pass an explicit depth there.
    """
    d = spec.horn_thick + 0.2 if depth is None else depth
    span = spec.horn_span + clearance
    width = spec.horn_arm_w + clearance
    slot_x = Pos(0, 0, d / 2) * Box(span, width, d)
    prims: list[Part] = [cast(Part, slot_x)]
    if arms >= 4:
        prims.append(cast(Part, Pos(0, 0, d / 2) * Box(width, span, d)))
    prims.append(
        cast(Part, Pos(0, 0, d + access_depth / 2)
             * Cylinder(access_dia / 2, access_depth))
    )
    return cast(Part, Part() + prims)


def idler_boss(dia: float, height: float, base_fillet: float = 0.0) -> Part:
    """Stub axle for the far side of a servo joint (the side opposite the
    horn), so the joint is supported in double shear instead of hanging off
    the servo's output shaft. Grows in +Z from z = 0."""
    boss = cast(Part, Pos(0, 0, height / 2) * Cylinder(dia / 2, height))
    if base_fillet > 0:
        boss = cast(Part, boss + Pos(0, 0, base_fillet / 2) * Cylinder(
            dia / 2 + base_fillet, base_fillet))
    return boss
