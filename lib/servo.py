"""Hobby servo envelopes (COTS — never modelled as a printed part).

Only the mounting-relevant dimensions live here: parts in models/ cut
pockets, tab pilots and horn recesses from these numbers.

Provenance: SG90 and MG90S values are DATASHEET, read off the vendor
drawings Jonathan supplied 2026-08-25 (SG90_Model_A / SG90_Arm_Original,
TowerPro MG90S). MG995 is DATASHEET nominal, NOT yet confirmed against the
servo in hand. knowledge/dimensioning.md rates datasheet body dimensions
of cheap servos as weak — so:

  THE DATUM IS THE TAB PLANE, NOT THE CASE.

Every mount locates a servo by its two (or four) tab holes and clamps on
the tab faces; the case pocket is cut at a `locational` fit around
`case_l/case_w` purely so the body clears. A case 0.4 mm fatter than the
drawing then costs nothing. Anything that would be ruined by a wrong case
dimension is a design error, not a tolerance problem.

The 608ZZ drawing Jonathan supplied confirms lib/bearings.py exactly
(OD 22.0, bore 8.0, width 7.0, inner race OD 12.0) -- that entry is
promoted from DATASHEET-nominal to DRAWING-CONFIRMED.

Stall torques are the CONSERVATIVE end of the published range (hobby
ratings are optimistic). knowledge/motion_mechanisms.md derates by a
further x0.5 for anything held statically — use `duty_limit_kgcm`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServoSpec:
    """A servo, in its own frame.

    Frame: origin at the OUTPUT SHAFT AXIS on the TAB PLANE (the underside
    of the mounting tabs — the face a bracket clamps).
    +X runs along the case length away from the shaft, toward the lead end.
    +Z runs up out of the shaft, the direction the horn faces.

    That origin is chosen because it is the only one a printed mount can
    actually hold to: the tab holes set X/Y, the tab face sets Z.
    """

    name: str
    # case envelope
    case_l: float           # along X (long axis)
    case_w: float           # across Y
    case_h: float           # bottom of case to top of case
    # mounting tabs
    tab_span: float         # tip to tip, along X
    tab_thk: float          # tab thickness
    tab_hole_dia: float     # through-hole in the tab
    tab_hole_pitch: float   # hole centre to hole centre, along X
    tab_below_top: float    # top of case down to the TOP of the tabs
    shaft_from_end: float   # shaft axis to the NEAR end of the case, along X
    # output
    boss_dia: float         # round collar the horn hub sits on
    boss_h: float           # collar height above the top of the case
    spline_dia: float       # output spline OD
    spline_h: float         # spline height above the collar
    # horn (the single-arm "original" horn, mounted on the spline)
    horn_hub_dia: float
    horn_hub_h: float
    horn_blade_thk: float
    horn_arm_len: float     # shaft centre to the OUTERMOST hole centre
    horn_hole_dia: float
    horn_hole_pitch: float
    horn_screw_dia: float   # the retaining screw through the hub
    # electrical / mechanical
    lead_bundle_dia: float
    mass_g: float
    stall_kgcm: float       # conservative end of the published range

    @property
    def duty_limit_kgcm(self) -> float:
        """What it may HOLD continuously — stall x 0.5.

        knowledge/motion_mechanisms.md: stall is a peak rating, not a duty
        rating. Above this they run hot, buzz, and strip their gears.
        """
        return self.stall_kgcm * 0.5

    @property
    def tab_overhang(self) -> float:
        """How far one tab sticks out past the end of the case."""
        return (self.tab_span - self.case_l) / 2

    @property
    def total_h(self) -> float:
        """Case bottom to the top of the spline."""
        return self.case_h + self.boss_h + self.spline_h

    @property
    def tab_plane_z(self) -> float:
        """Height of the tab UNDERSIDE above the case bottom.

        This is the datum offset: a mount whose clamping face sits at this
        height holds the servo with `case_h - that` sticking out above.
        """
        return self.case_h - self.tab_below_top - self.tab_thk


# --- SG90: 9 g plastic-gear micro. DATASHEET, drawing "SG90_Model_A" -----
# Read off the drawing: 32.4 tab span with the holes 2.3 in from each tip
# gives 27.8 c-c, which agrees with the widely published SG90 value.
SG90 = ServoSpec(
    name="SG90",
    case_l=22.6, case_w=12.6, case_h=23.7,
    tab_span=32.4, tab_thk=2.4, tab_hole_dia=2.1, tab_hole_pitch=27.8,
    tab_below_top=4.3, shaft_from_end=6.1,
    boss_dia=5.0, boss_h=4.2, spline_dia=4.9, spline_h=2.5,
    horn_hub_dia=7.0, horn_hub_h=3.8, horn_blade_thk=1.5,
    horn_arm_len=15.95, horn_hole_dia=0.9, horn_hole_pitch=2.1,
    horn_screw_dia=2.5,
    lead_bundle_dia=3.4,
    mass_g=9.0,
    stall_kgcm=1.6,
)

# --- MG90S: 13.4 g metal-gear micro. DATASHEET, TowerPro drawing --------
# NOT dimensionally identical to the SG90 on this drawing: 34.0 span and
# 29.0 c-c against the SG90's 32.4 / 27.8. They are NOT interchangeable in
# a shared tab pattern — do not design one pocket for both.
MG90S = ServoSpec(
    name="MG90S",
    case_l=24.0, case_w=12.5, case_h=24.0,
    tab_span=34.0, tab_thk=3.0, tab_hole_dia=2.1, tab_hole_pitch=29.0,
    tab_below_top=1.0, shaft_from_end=6.0,
    boss_dia=6.0, boss_h=6.0, spline_dia=5.0, spline_h=4.0,
    horn_hub_dia=7.0, horn_hub_h=3.8, horn_blade_thk=1.5,
    horn_arm_len=15.95, horn_hole_dia=0.9, horn_hole_pitch=2.1,
    horn_screw_dia=2.5,
    lead_bundle_dia=3.4,
    mass_g=13.4,
    stall_kgcm=2.0,
)

# --- MG995: 55 g standard metal-gear. DATASHEET, two vendor drawings ----
# THE TWO DRAWINGS JONATHAN SUPPLIED DISAGREE ON THE MOUNTING PATTERN:
#   drawing A (grey):  tab span 54.0, case 40 x 20 x 38,  total 47.2
#   drawing B (black): tab span 52.8, case 40 x 20 x 36.5, c-c 47.8 x 10.2
# 1.2 mm of span and 1.7 mm of hole pitch is more than any clearance hole
# absorbs. The values below are drawing B (the one that dimensions the hole
# pitch at all); the shoulder bracket therefore mounts this servo on SLOTS
# elongated along X, not on holes -- see MG995_TAB_SLOT_X_MM. Replace both
# with MEASURED values before the bracket prints at full size.
MG995 = ServoSpec(
    name="MG995",
    case_l=40.0, case_w=20.0, case_h=36.5,
    tab_span=52.8, tab_thk=2.5, tab_hole_dia=4.8, tab_hole_pitch=47.8,
    tab_below_top=7.5, shaft_from_end=10.0,
    boss_dia=13.0, boss_h=3.0, spline_dia=5.9, spline_h=3.6,
    horn_hub_dia=12.0, horn_hub_h=5.0, horn_blade_thk=2.5,
    horn_arm_len=19.5, horn_hole_dia=1.6, horn_hole_pitch=3.0,
    horn_screw_dia=3.0,
    lead_bundle_dia=4.2,
    mass_g=55.0,
    stall_kgcm=9.4,
)
# MG995 mounts on FOUR holes: 47.8 apart along X, this far apart across Y.
MG995_TAB_HOLE_PITCH_Y = 10.2
# Slot length along X that covers BOTH published patterns (47.8 and 49.5)
# plus an M3 clearance hole: 3.4 + (49.5 - 47.8) = 5.1, rounded up.
MG995_TAB_SLOT_X_MM = 5.4

# --- MG995 round horn (the Oe22 aluminium disc), DATASHEET -------------
# Supplied drawing: Oe22 disc, 4 holes on a Oe16 bolt circle (2 tapped M4,
# 2 clearance Oe4), Oe3 central retaining screw, 8 mm overall hub height,
# ~3 mm disc thickness. This is what drives the shoulder link.
MG995_DISC_HORN = {
    "disc_dia": 22.0,
    "disc_thk": 3.0,
    "hub_h": 8.0,              # total height incl. the splined hub
    "bolt_circle_dia": 16.0,
    "bolt_count": 4,
    "bolt_dia": 4.0,           # 2 are tapped M4, 2 are clearance
    "screw_dia": 3.0,          # central retaining screw
}

CATALOG = {s.name: s for s in (SG90, MG90S, MG995)}

# Jonathan's inventory, 2026-08-25.
INVENTORY = {"MG995": 1, "MG90S": 2, "SG90": 3}

# Servo-kit self-tapping screw: pilot per knowledge/fasteners_inserts.md.
SERVO_SCREW_PILOT_MM = 1.8
