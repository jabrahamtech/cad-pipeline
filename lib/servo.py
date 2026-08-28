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


# --- SG90: 9 g plastic-gear micro. DATASHEET, drawing "SG90_Model_A",
# reconciled 2026-08-27 against TowerPro's own config table
# (towerpro.com.tw/product/sg90-analog: B 22.7, D 12.2, E 32.3, F 17,
# A 30.3 - A confirms case_h + boss_h + spline_h exactly). Deltas applied:
# case_l 22.6 -> 22.7, case_w 12.6 -> 12.2, tab_span 32.4 -> 32.3. Hole
# pitch stays 27.8 (drawing-stated; holes 2.3 in from each tip of a 32.3
# span gives 27.7, agreement to 0.1). tab_plane 17.0 = TowerPro F, exact.
SG90 = ServoSpec(
    name="SG90",
    case_l=22.7, case_w=12.2, case_h=23.7,
    tab_span=32.3, tab_thk=2.4, tab_hole_dia=2.1, tab_hole_pitch=27.8,
    tab_below_top=4.3, shaft_from_end=6.1,
    boss_dia=5.0, boss_h=4.2, spline_dia=4.9, spline_h=2.5,
    horn_hub_dia=6.8, horn_hub_h=3.0, horn_blade_thk=2.0,
    horn_arm_len=17.0, horn_hole_dia=1.4, horn_hole_pitch=2.0,
    horn_screw_dia=2.5,
    lead_bundle_dia=3.4,
    mass_g=9.0,
    stall_kgcm=1.6,
)

# --- MG90S: 13.4 g metal-gear micro. DATASHEET — CORRECTED 2026-08-27.
# The drawing this block was first typed from said 34.0 span / 29.0 c-c and
# "not interchangeable with the SG90". TowerPro's own config table
# (towerpro.com.tw/product/mg90s-3: A 32.5, B 22.8, C 28.4, D 12.4,
# E 32.1, F 18.5) contradicts it: the flange is the SG90's footprint to
# within 0.2. Third-party drawings (components101, electronicoscaldas)
# agree on ~22.5-22.8 case / 32.5 span and never showed 34/29. Adopted:
# case_l 22.8, case_w 12.4, tab_span 32.1; tab_thk 2.5 ASSUMED (micro
# family, table does not give it); tab_below_top 3.0 DERIVED from F:
# case_h - F - tab_thk = 24.0 - 18.5 - 2.5. Hole pitch 27.5 DERIVED
# (holes centred in the tab overhang, (B+E)/2), no drawing states it —
# CALIPER before anything prints against these holes. Note official
# A 32.5 reads 1.5 SHORTER than case_h+boss+spline below — the envelope
# kept here is the conservative one.
MG90S = ServoSpec(
    name="MG90S",
    case_l=22.8, case_w=12.4, case_h=24.0,
    tab_span=32.1, tab_thk=2.5, tab_hole_dia=2.1, tab_hole_pitch=27.5,
    tab_below_top=3.0, shaft_from_end=6.0,
    boss_dia=6.0, boss_h=6.0, spline_dia=5.0, spline_h=4.0,
    horn_hub_dia=6.8, horn_hub_h=3.0, horn_blade_thk=2.0,
    horn_arm_len=17.0, horn_hole_dia=1.4, horn_hole_pitch=2.0,
    horn_screw_dia=2.5,
    lead_bundle_dia=3.4,
    mass_g=13.4,
    stall_kgcm=2.0,
)

# --- MG995: 55 g standard metal-gear. DATASHEET, two vendor drawings ----
# THE TWO DRAWINGS JONATHAN SUPPLIED DISAGREE ON THE MOUNTING PATTERN:
#   drawing A (grey):  tab span 54.0, case 40 x 20 x 38,  total 47.2
#   drawing B (black): tab span 52.8, case 40 x 20 x 36.5, c-c 47.8 x 10.2
# TIE PARTLY BROKEN 2026-08-27 by TowerPro's own config table
# (towerpro.com.tw/product/mg995: A 42.7, B 40.9, C 37, D 20, E 54,
# F 26.8 - the MG995 and MG996R pages carry the same case table): the
# manufacturer sides with drawing A on the span (54, not 52.8) and reads
# the case a shade longer (40.9). Adopted: tab_span 54.0, case_l 40.9,
# tab_below_top 7.2 (DERIVED from official F: case_h - F - tab_thk =
# 36.5 - 26.8 - 2.5). The hole pitch is still ONLY drawing B's 47.8 -
# tab-centred derivation off the official numbers gives (B+E)/2 = 47.5,
# published clones say 49.5 - so the bracket keeps mounting this servo on
# SLOTS elongated along X (MG995_TAB_SLOT_X_MM, widened to cover
# 47.5..49.5). Replace with MEASURED values before the bracket prints at
# full size — this is the standing bench item that blocks the shoulder.
MG995 = ServoSpec(
    name="MG995",
    case_l=40.9, case_w=20.0, case_h=36.5,
    tab_span=54.0, tab_thk=2.5, tab_hole_dia=4.8, tab_hole_pitch=47.8,
    tab_below_top=7.2, shaft_from_end=10.0,
    boss_dia=13.0, boss_h=3.0, spline_dia=5.9, spline_h=3.6,
    horn_hub_dia=8.7, horn_hub_h=3.8, horn_blade_thk=2.2,
    horn_arm_len=16.5, horn_hole_dia=1.5, horn_hole_pitch=2.3,
    horn_screw_dia=3.0,
    lead_bundle_dia=4.2,
    mass_g=55.0,
    stall_kgcm=9.4,
)
# MG995 mounts on FOUR holes: 47.8 apart along X, this far apart across Y.
MG995_TAB_HOLE_PITCH_Y = 10.2
# Slot length along X that covers EVERY candidate pattern (derived 47.5,
# drawing B's 47.8, published clones' 49.5) plus an M3 clearance hole:
# 3.4 + (49.5 - 47.5) = 5.4, rounded up.
MG995_TAB_SLOT_X_MM = 5.6

# --- HORN GEOMETRY, CORRECTED 2026-08-27 ("the servo arms seem really
# wrong" - Jonathan, and he was right) -----------------------------------
# The horn values above were re-derived from the FreeCAD parts library's
# measured SG90 horn set (STEP/STL, read numerically: hub Ø8.0 x 3.0,
# blade 2.0 thick, total 5.0, holes Ø1.4 at 2.0 pitch, single arm
# outermost hole r 17) cross-checked against deshipu's SG-90 teardown
# (holes 2 mm apart) and an independent spec (arm ~20 long x 5 wide x
# 2 THICK). The old 1.5 blade / Ø7.0 hub / 0.9 holes matched nothing.
# MG995 horn values follow the Futaba 25T-spline family model (hub
# Ø13.5-14, total 6.3, symmetric cross reach ~19.5, outermost hole
# ~16.5) - MG995 clones take Futaba-compatible horns.
#
# THE MISTAKE THE OLD NUMBERS CAUSED IN PARTS: a horn ARM is not a
# constant-width blade. It tapers from ~5.5-6 wide near the hub to ~3 at
# the tip (micro; the MG995's runs ~6.5 down to ~4.5). Five parts cut
# arm SLOTS at "blade 2.5/3.8 wide" - the blade THICKNESS misread as its
# width - and no real horn would have entered any of them. Slot widths
# now come from the width AT THE TRIM RADIUS below.
#
# HUB DIAMETERS, MEASURED 2026-08-28, and this is the correction that
# matters most: the FreeCAD community model over-stated BOTH hubs badly.
#   micro  model 8.0  -> MEASURED 6.8   (and the PRE-AUDIT value was 7.0,
#                                        so the "correction" made it worse)
#   MG995  model 13.8 -> MEASURED 8.7   (5.1 mm out; the 2.0 J2 standoff
#                                        was invented to dodge a hub that
#                                        does not exist at that size)
# Both were caught by the gauge's hub sweeps overshooting on the FIRST drop:
# every bore accepted every hub loosely. A sweep that is entirely too big
# is still an answer, and a faster one than a caliper.
#
# deshipu's warning stands: horn dimensions VARY BY BATCH. Everything in
# this block is COMMUNITY-MODEL grade, one step above the old numbers
# and one below the bench. gauge_flange v2 carries the arm comb and hub
# sweep that promote these to MEASURED.
# MEASURED 2026-08-28 on Jonathan's bench horns (calibration/2026-08-28-*).
# The community model was right about the shape and wrong about the WIDTH,
# and the width is what every slot in this project is cut from.
MICRO_HORN_ARM_W_AT_6 = 5.7    # MEASURED at the first hole (~r 6), was 5.5
MICRO_HORN_CROSS_LONG = 34.4   # MEASURED, was 33.5. Long axis tip to tip
MICRO_HORN_CROSS_SHORT = 17.0  # MEASURED 16-18, was 16.0 - NOT a sym cross
MICRO_HORN_ARM_W_OUTER = 4.0   # MEASURED at the last hole (~r 17), was 3.0.
                               # THE ONE THAT BIT: tt_horn_w was 3.0 + 0.4
                               # clearance = 3.4, and a 4.0 arm cannot enter
                               # a 3.4 slot anywhere. The turret cross pocket
                               # never accepted the horn - gauge_horn v1
                               # CROSS station, first drop.
MG995_HORN_ARM_W_AT_8 = 6.5    # MEASURED 2026-08-28 (6-7 at r 8) - the one
                               # model number the bench CONFIRMED

# The micro arm TAPERS, and the taper is now measured at both ends:
#   w(r) ~= 5.7 - 0.121 * (r - 6)   for r 6 .. 17
# A CONSTANT-WIDTH slot therefore cannot fit a trimmed arm over any long
# span: at the turret's r 6.5..16.4 engagement the arm runs 5.3 down to 4.1.
# Slots must be cut to the width AT THEIR OWN ENGAGEMENT RADIUS, or tapered.
MICRO_HORN_TAPER_PER_MM = 0.121


def micro_arm_w(r_mm: float) -> float:
    """MEASURED micro horn arm width at radius r, mm. Clamped to the
    measured span - do not extrapolate a linear fit past its data."""
    r = max(6.0, min(17.0, r_mm))
    return MICRO_HORN_ARM_W_AT_6 - MICRO_HORN_TAPER_PER_MM * (r - 6.0)

# --- MG995 round horn (the Oe22 aluminium disc), DATASHEET -------------
# Supplied drawing: Oe22 disc, 4 holes on a Oe16 bolt circle (2 tapped M4,
# 2 clearance Oe4), Oe3 central retaining screw, 8 mm overall hub height,
# ~3 mm disc thickness. This is what drives the shoulder link.
MG995_DISC_HORN = {
    "disc_dia": 20.6,   # MEASURED 2026-08-28 (the drawing said 22.0 -
                         # this is the black plastic clone disc, not alu)
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
