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
    # WHERE THE LEADS LEAVE THE CASE - MEASURED 2026-08-28, and the previous
    # written assumption was wrong at BOTH ends of its own description.
    # It said "the FAR END FACE, centred across the case width and one lead
    # diameter up from the case bottom". Jonathan's bench, all three servos:
    # the bundle leaves at the SHAFT END, up at TAB HEIGHT. Wrong end, wrong
    # height. It is the difference between a lead that dangles in free air
    # and one that sits exactly in the band a mounting window grips - which
    # is why not one of the three can be pushed into its own pocket.
    #
    # WHICH FACE. This is the part every consumer got wrong, so it is stated
    # first and in one sentence: the bundle leaves the SHORT END FACE - the
    # case's case_w x case_h end, the one the output shaft is nearest - dead
    # CENTRE across the width, near the bottom.
    #
    # It does NOT leave a long side wall. lead_x below equals -shaft_from_end,
    # which IS that end face (the shaft sits shaft_from_end in from it), but
    # five parts read it as a point ON a long wall and notched the two walls
    # either side of the face instead of the face itself. Jonathan, at the
    # bench, 2026-08-28: "thats not on the right side its on the short side
    # specifically the side where the motor is closer to that short side",
    # and then, asked whether it was centred across that face: "centre".
    #
    # A keyway cut from this datum is therefore ONE notch, centred, in the
    # END wall of the pocket, running outward until it breaks daylight. Not
    # two notches in the side walls. If you are writing `for sz in (+1, -1)`
    # around a lead keyway, you have misread this block.
    #
    # Expressed in this frame (origin at the shaft axis on the tab plane):
    #   lead_x  the END FACE the bundle leaves, = -shaft_from_end, NEGATIVE
    #   lead_y  across the width. MEASURED 0.0 - centred, all three servos
    #   lead_z  relative to the tab plane. The case BOTTOM sits at
    #           tab_thk + tab_below_top - case_h, and the bundle leaves one
    #           bundle-diameter up from it, so lead_z is strongly NEGATIVE.
    # Corrected within the session: first read as tab height, then Jonathan
    # sketched it and confirmed BOTTOM. Shaft END was right, height was not,
    # and the FACE was not either.
    lead_x: float
    lead_y: float
    lead_z: float
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
    lead_x=-6.1, lead_y=0.0, lead_z=-13.6,  # shaft END FACE (= -shaft_from_end),
                            # centred, one bundle up from the case bottom:
                            # 2.4 + 4.3 - 23.7 = -17.0, +3.4
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
    lead_x=-6.0, lead_y=0.0, lead_z=-15.1,  # 2.5 + 3.0 - 24.0 = -18.5, +3.4
    mass_g=13.4,
    stall_kgcm=2.0,
)

# --- MG995: 55 g standard metal-gear. JONATHAN'S DRAWING, 2026-09-28 --------
# calibration/2026-09-28-mg995-drawing.png - the drawing for the servos he
# actually has. Jonathan: "this is more correct than what you had before".
# It REPLACES the TowerPro-table numbers this block carried since 2026-08-27
# (case 40.9 x 20.2 x 36.5, tab_below_top 7.2, pitch 47.8, span 54): those
# described a different case, 4 mm shorter, with a flat top.
#
# DIMENSIONED on the drawing: case 40.00 x 20.00, 40.50 bottom to the top of
# the LIP, tab span 55.00, hole pitch 49.00, hole O4.50, shaft 14.50 from the
# near holes (-> shaft_from_end = 49/2 - 14.5 = 10.0), U-slots open out to
# 15.50 from the shaft (pitch 51.0), tab underside -> lip top 12.95, tab
# underside -> collar top 14.45.
# SCALED off the same drawing (its dimension lines check to 4.02 px/mm, the
# 12.95 and 14.45 both reproduce to 0.05): lip 2.2 tall, collar O12.5,
# spline 3.9, tab plate 3.1, rib 2.0 wide reaching 6.7 above the tab
# underside at the case wall, lead stub centred 9.8 up from the case bottom
# on the shaft-end face.
#
# THE LIP. Jonathan, 2026-09-28: "the top of the motor has a lip so the top
# is not flush". The top is a D-shaped plate 2.2 proud of the case top -
# 3.2 in from the far end, ~0.7 in at the shaft end (R ~9.5 about the
# shaft), ~18 wide. case_h is taken to the TOP OF THE LIP, over the whole
# case footprint: every consumer that clears or bears on "the case top"
# then clears or bears on the lip, which is the face that actually touches.
# The 2.2 mm step round the lip is left out on purpose - nothing reaches
# into it.
#
# case_w stays 20.2: MEASURED on the bench 2026-08-28, the drawing says 20.0.
# boss_dia stays 13.0 against the drawing's scaled 12.5 - it only ever sizes
# CLEARANCE bores, and the larger number is the safe one.
MG995 = ServoSpec(
    name="MG995",
    case_l=40.0, case_w=20.2, case_h=40.5,   # l, h DRAWING (h to the lip top);
                                            # w MEASURED 2026-08-28
    tab_span=55.0, tab_thk=3.1, tab_hole_dia=4.5, tab_hole_pitch=49.0,
    tab_below_top=9.85, shaft_from_end=10.0,  # 12.95 - tab_thk
    boss_dia=13.0, boss_h=1.5, spline_dia=5.9, spline_h=3.9,
    horn_hub_dia=8.7, horn_hub_h=3.8, horn_blade_thk=2.2,
    horn_arm_len=16.5, horn_hole_dia=1.5, horn_hole_pitch=2.3,
    horn_screw_dia=3.0,
    lead_bundle_dia=4.2,
    lead_x=-10.0, lead_y=0.0, lead_z=-17.75,  # bottom -27.55, stub centre +9.8
    mass_g=55.0,
    stall_kgcm=9.4,
)
# the drawing's two dimension chains, asserted so an edit above cannot
# silently leave one of them behind
assert abs(MG995.tab_below_top + MG995.tab_thk - 12.95) < 1e-9
assert abs(MG995.tab_below_top + MG995.tab_thk + MG995.boss_h - 14.45) < 1e-9
assert abs(MG995.tab_hole_pitch / 2 - MG995.shaft_from_end - 14.5) < 1e-9
# THE LIP, as a footprint, in the servo frame (+X away from the shaft).
# case_h runs to its top (see above); a mount that wants the CASE top flush
# on a face pockets this instead. Scaled off the drawing's top view:
#   height above the case top                 2.2
#   width across Y (case 20.0 on the drawing) 17.8
#   shaft-end edge: a D, R 9.75 about the shaft (case end is at 10.0)
#   far-end edge: 3.2 in from the far end of the case
# Modelled as the RECTANGLE x -R .. case_l - shaft_from_end - inset: the D's
# corners are left in, which makes a pocket cut from it slightly generous.
MG995_LIP_H_MM = 2.2
MG995_LIP_W_MM = 17.8
MG995_LIP_R_MM = 9.75
MG995_LIP_FAR_INSET_MM = 3.2
# The stiffening RIB on each tab: a web down the tab's centreline (between
# the two holes) that rises from the tab top toward the case top. It is what
# a pad clamping the tab TOP runs into. Width, and its top above the TAB
# UNDERSIDE where it meets the case wall (it slopes down toward the tip).
MG995_TAB_RIB_W_MM = 2.0
MG995_TAB_RIB_TOP_MM = 6.7
# MG995 mounts on FOUR holes: 49.0 apart along X, this far apart across Y
# (not dimensioned; scales 10.1 - 10.2 kept, the difference is inside M3
# clearance).
MG995_TAB_HOLE_PITCH_Y = 10.2
# Slot length along X in a mount, centred on the 49.0 pitch: an M3 clearance
# hole plus +-1.1 of travel for print and pitch error: 3.4 + 2.2 = 5.6. (The
# servo's own U-slots run outward to pitch 51.0, so travel OUTWARD is free on
# the servo side too.)
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
# DERIVED from the two measured ends, not typed. It was 0.121, which does not
# pass through its own data: 5.7 - 0.121 x 11 = 4.37, and the measured outer
# width is 4.0. Every slot cut from it ran up to 0.37 mm WIDE at the tip - a
# sloppy slot rather than a tight one, so it was not what stopped the horns
# going in, but a fitted line that misses its own endpoints is not a fit.
MICRO_HORN_TAPER_PER_MM = ((MICRO_HORN_ARM_W_AT_6 - MICRO_HORN_ARM_W_OUTER)
                           / (17.0 - 6.0))
assert abs((MICRO_HORN_ARM_W_AT_6 - MICRO_HORN_TAPER_PER_MM * 11.0)
           - MICRO_HORN_ARM_W_OUTER) < 1e-9, (
    'the taper must land on the measured outer width at r 17')


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
INVENTORY = {"MG995": 2, "MG90S": 2, "SG90": 3}  # MG995: 1 standard (J2)
#   + 1 x 360 deg continuous (J1), Jonathan 2026-09-27. SG90 count is stale:
#   lib/joints.py records he has the five the arm uses.

# Servo-kit self-tapping screw: pilot per knowledge/fasteners_inserts.md.
SERVO_SCREW_PILOT_MM = 1.8


# --- THE CASE POCKET CLEARANCE. ROOT CAUSE, FOUND 2026-08-31 -------------
# Jonathan, three times now, most recently today: "none of them fit in the
# holes you have set for them". This is why, and it is one number.
#
# Every servo pocket in models/ is cut at `loc` = 0.2 mm TOTAL diametral
# clearance - 0.10 mm PER SIDE - around case_l/case_w. Those case dimensions
# are DATASHEET grade for cheap servos, and the docstring at the top of this
# file already says datasheet body dimensions of cheap servos are weak. It
# then claims "a case 0.4 mm fatter than the drawing costs nothing". At 0.10
# per side a case 0.4 fatter is a 0.30 INTERFERENCE. The prose and the number
# have contradicted each other since the file was written, and the number is
# what got cut.
#
# Three errors stack in the same direction, all of them making the hole
# smaller than the servo:
#   1. datasheet case dimension, unmeasured, plausibly 0.3-0.5 under
#   2. printed pockets come out UNDERSIZE - the same effect design_rules
#      records as HOLE_DIA_COMP_MM for round holes, uncompensated here
#   3. elephant's foot on the first layers of the pocket walls
# 0.10 per side absorbs none of them.
#
# WHAT IT COSTS TO FIX: nothing. Re-read the datum block at the top of this
# file - the servo is located by its TAB HOLES and clamped on its TAB FACES.
# The case pocket exists so the body clears, and for no other reason. A
# pocket 0.5 mm per side loose positions the servo exactly as well as one
# 0.1 mm loose, because neither of them is what positions it.
#
# THE ONE PART THAT DISAGREED has to change with this: turntable_stator.py
# line ~675 says "the aperture is cut to case + loc so it carries the
# sideways load". That part is deliberately gripping the case, against the
# datum this file declares. It is also the J1 servo Jonathan cannot seat.
# Loading a servo's plastic case sideways is not a thing to do on purpose;
# the load path is the tabs.
SERVO_CASE_CLEARANCE_MM = 1.0    # total, diametral - 0.5 mm per side


def case_pocket(spec: ServoSpec, clearance: float = None) -> tuple:
    """(length, width) of the pocket a case DROPS INTO, mm.

    Not a fit. The tabs locate the servo; this hole only has to let the body
    through, so it is sized for the WORST case the datasheet could be hiding
    plus what the printer takes off a pocket wall.
    """
    c = SERVO_CASE_CLEARANCE_MM if clearance is None else clearance
    return (spec.case_l + c, spec.case_w + c)


def case_pocket_h(spec: ServoSpec, clearance: float = None) -> float:
    """Depth a pocket needs to swallow the case below the tab plane."""
    c = SERVO_CASE_CLEARANCE_MM if clearance is None else clearance
    return spec.case_h - spec.tab_below_top - spec.tab_thk + c / 2.0


# The lead datum, guarded. lead_x is the SHORT END FACE at the shaft end,
# which is exactly -shaft_from_end; lead_y is centred on that face. Five
# parts once read lead_x as a point on a long side wall and notched the
# wrong wall, so the relationship is asserted rather than described.
for _s in CATALOG.values():
    assert abs(_s.lead_x + _s.shaft_from_end) < 1e-9, (
        '%s: lead_x %.2f is not the shaft-end face (-shaft_from_end %.2f). '
        'The bundle leaves that FACE - if this is being changed, the five '
        'pocket keyways that derive from it have to move with it.'
        % (_s.name, _s.lead_x, -_s.shaft_from_end))
    assert _s.lead_y == 0.0, '%s: the bundle is centred on the end face' % _s.name
    assert _s.lead_z < 0.0, '%s: the bundle leaves below the tab plane' % _s.name
del _s


# --- DRIVING THE SPLINE DIRECTLY, AND WHY THE TEETH ARE NOT PRINTED -----
# Jonathan, 2026-08-31: "we should not [mount] at the horns but rather add
# gears that we make". Right, and it removes the worst part in the machine
# from the load path: the horn is stamped plastic, varies by batch (deshipu,
# Roger Cheng), and GATE servo_fit has now MEASURED it fouling the shoulder
# bracket by 67.5 mm3. Nothing downstream should depend on its outline.
#
# THE SPLINE CANNOT BE PRINTED, and that is a rule, not an opinion. A micro
# spline is 20 teeth on a 4.9 mm circle: 0.77 mm of pitch and roughly 0.24 mm
# of tooth. design_rules.MIN_FEATURE_MM is 0.8, CALIBRATED on this printer.
# The teeth are a third of the smallest feature the machine can make. A
# "splined" printed bore would come out as a slightly lumpy circle, which is
# a round bore that lies about itself.
#
# SO IT IS A ROUND BORE, CUT UNDERSIZE, AND THE STEEL SPLINE BROACHES IT.
# The servo's own output shaft cuts its form into the plastic on first
# assembly. One diameter has to be right instead of twenty teeth, and the
# one diameter is exactly the kind of thing gauge_fits already calibrates.
# The servo's own retaining screw then clamps the hub down axially, which is
# what that screw is for.
#
# THE INTERFERENCE IS A GUESS UNTIL A GAUGE SETTLES IT. design_rules calls
# 0.15 diametral a PRESS on a plain bore; broaching needs the bore SMALLER
# than the shaft, not larger, and how much smaller depends on how much PETG
# will displace before it splits a thin hub. 0.25 is the starting figure and
# it is ASSUMED - print the sweep before committing a gear to it.
SPLINE_BROACH_INTERFERENCE_MM = 0.25   # ASSUMED - bore = spline_dia - this
#
# MEASURED 2026-09-28, gauge_broach_v2. v1 (0.10..0.40) fitted NOTHING on
# Jonathan's printer. v2 swept -0.45..+0.25; his reading: "S-5 and G-25 fit
# super tight" - i.e. those are the stations that press on, and are tight.
# So the DRAWN interference that gives a tight press on this printer is:
#   SG90   -0.05  (bore drawn 4.95 on a 4.90 spline)
#   MG995  -0.25  (bore drawn 6.15 on a 5.90 spline)
# NEGATIVE: the bore is drawn LARGER than the spline and the printer's hole
# shrink makes it the press. The two differ by 0.20 - either the MG995's
# spline is bigger than the 5.9 assumed, or its 25 teeth bite differently;
# either way each servo is read off its own row, not off the other.
# CAVEAT, stated by Jonathan: the coupon was printed in PLA at 90 % infill.
# Infill does not form a bore (the perimeters do); the material can move
# it by a few hundredths. Print the hubs in the same material, or re-check
# one station in PETG before a PETG hub.
SPLINE_BROACH_INTERFERENCE_BY_SERVO = {"SG90": -0.05, "MG995": -0.25}
SPLINE_TEETH = {"SG90": 20, "MG90S": 20, "MG995": 25}


def spline_bore_d(spec: ServoSpec, interference: float = None) -> float:
    """Bore diameter for a printed hub the servo spline broaches into.

    Per servo from SPLINE_BROACH_INTERFERENCE_BY_SERVO (gauged); a servo
    with no gauge reading falls back to the old assumed constant."""
    if interference is None:
        interference = SPLINE_BROACH_INTERFERENCE_BY_SERVO.get(
            spec.name, SPLINE_BROACH_INTERFERENCE_MM)
    i = interference
    return spec.spline_dia - i


def spline_z(spec: ServoSpec) -> tuple:
    """(bottom, top) of the spline in the servo frame - what the bore grips.

    The spline sits ABOVE the output boss, so a hub seated near the case has
    to clear the boss first and only meets the spline higher up. That is what
    sets the minimum hub height, and it is why a thin gear cannot drive a
    servo directly however good the bore is.
    """
    boss_top = spec.tab_below_top + spec.tab_thk + spec.boss_h
    return (boss_top, boss_top + spec.spline_h)


def horn_arms(spec: ServoSpec):
    """[(angle_deg, reach_mm), ...] for the horn that ships with this servo.

    THE MICRO CROSS IS NOT SYMMETRIC and that is the whole reason this is a
    function rather than four equal arms. MEASURED 2026-08-28: 34.4 tip to
    tip the long way, 17.0 the short way - so the long arms reach r 17.2 and
    the short ones only r 8.5. A part that assumes four r-17 arms will cut
    two slots that nothing ever enters, and a part that assumes four r-8.5
    arms will be struck by the long pair.

    The MG995 takes Futaba-compatible horns, which ARE symmetric.
    """
    if spec.name in ('SG90', 'MG90S'):
        return [(0.0, MICRO_HORN_CROSS_LONG / 2.0),
                (180.0, MICRO_HORN_CROSS_LONG / 2.0),
                (90.0, MICRO_HORN_CROSS_SHORT / 2.0),
                (270.0, MICRO_HORN_CROSS_SHORT / 2.0)]
    return [(a, spec.horn_arm_len) for a in (0.0, 90.0, 180.0, 270.0)]


def horn_arm_w(spec: ServoSpec, r_mm: float) -> float:
    """Arm width at radius r, for whichever horn family this servo takes."""
    if spec.name in ('SG90', 'MG90S'):
        return micro_arm_w(r_mm)
    return MG995_HORN_ARM_W_AT_8


def lead_keyway_w(spec: ServoSpec, clearance: float = 0.2) -> float:
    """Width of the END-WALL keyway, across the case width, centred on
    lead_y. ONE notch - see the lead datum block above."""
    return spec.lead_bundle_dia + clearance
