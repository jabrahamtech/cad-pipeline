"""robotarm/_gauge_broach - the coupon that settles the broach interference.

Rebuilds `robotarm_gauge_broach` (idempotent). Companion sheet:
specs/robotarm/_gauge_broach_sheet.md. Nothing here is a part of the arm.

WHY THIS EXISTS, AND WHY IT IS THE MOST OVERDUE PRINT IN THE PROJECT
--------------------------------------------------------------------
On 2026-08-31 the servo horn came out of the whole machine. Jonathan: "we
should not [mount] at the horns but rather add gears that we make". Every
driven part now carries a ROUND bore cut UNDERSIZE, and the servo's own
STEEL SPLINE broaches its form into the PETG on first assembly. The teeth
are not printed and cannot be: 20 teeth on a Oe4.9 circle is 0.245 mm of
module and roughly a quarter-millimetre of tooth, against a MIN_FEATURE_MM
of 0.80 that is CALIBRATED on this machine. A "splined" printed bore would
come out a slightly lumpy circle that lies about itself.

So twenty teeth were traded for ONE DIAMETER, and that diameter is:

    bore = spline_dia - SPLINE_BROACH_INTERFERENCE_MM        (lib/servo.py)
    SPLINE_BROACH_INTERFERENCE_MM = 0.25   # ASSUMED

ASSUMED. Not handbook, not calibrated, not measured - a starting figure
typed in the same session that made six parts depend on it: j1_hub,
gripper_pinion, wrist_rotator, wrist_hub, j3_pinion and shoulder_hub, plus
turntable_stator and shoulder_bracket which mirror j1_hub's bore. Every one
of those files carries the same sentence - "gauge it before trusting a gear
to it" - and no gauge existed. This is it.

WHAT GOES WRONG AT EACH END, WHICH IS WHY IT MUST BE SWEPT
----------------------------------------------------------
TOO LITTLE and the steel skims the plastic instead of cutting it: the gear
turns on the shaft under load and the joint has no index at all. The failure
is silent - it assembles perfectly and then slips.
TOO MUCH and either the hub splits as the spline is driven in (hoop tension
across printed layers), or it cannot be pressed in at all and the servo's
own Oe2.5 retaining screw strips trying to draw it down.
Neither end is a dimension a caliper can find. The bore can be measured to
0.01 mm and still tell you nothing about whether 0.25 mm of interference
DISPLACES PETG or SPLITS it - that depends on the plastic, the layer
adhesion, the wall around the bore and the shape of the spline teeth. It is
a destructive, feel-and-listen test, which is exactly the class of station
_gauge_slim.py keeps SWEPT rather than collapsing to a caliper reading.

WHAT IS ON THE COUPON
---------------------
21 stations: three servo splines x seven interferences.

    S10 S15 S20 S25 S30 S35 S40    SG90   spline Oe4.9, 20T
    M10 M15 M20 M25 M30 M35 M40    MG90S  spline Oe5.0, 20T
    G10 G15 G20 G25 G30 G35 G40    MG995  spline Oe5.9, 25T

The label is the interference in HUNDREDTHS OF A MILLIMETRE, raised beside
its own bore, so a station that has been snapped off, pressed, twisted and
split still says what it was. The letter is the servo, because after the
test the bores are no longer round and no longer measurable.

SG90 AND MG90S ARE NOT THE SAME SPLINE and that is why both are swept.
lib/servo.py records Oe4.9 and Oe5.0 - a tenth of a millimetre apart, which
is 40 % of the smallest interference on this coupon. Three joints run on
SG90s (J1, J5 roll, J6 pruner) and two on MG90S (J3 elbow, J4 wrist), so if
the two splines want different numbers the arm needs a per-servo table and
not a constant. This coupon can say so; a single micro row could not.

X25 IS THE CONTROL. The middle-of-sweep station is exactly what the arm
ships today, on every one of the three servos - asserted below against
lib/servo.SPLINE_BROACH_INTERFERENCE_MM rather than trusted to a comment.

HOW MUCH TOOTH EACH STATION ACTUALLY BITES. The interference is DIAMETRAL,
so the radial bite is half of it, and it has to be read against the height
of a spline tooth. Taking the tooth addendum as one module (m = spline_dia
/ teeth, ESTIMATED - no drawing of these splines exists), the sweep runs
from about a fifth of a tooth at 0.10 to about four fifths at 0.40. That is
the real span of the question: below it the spline planes the bore smooth,
above it the bore has to swallow nearly a whole tooth per side.

EVERY STATION IS SEPARATELY BREAKABLE, AND THAT IS THE POINT
------------------------------------------------------------
Each bore sits in its own round boss on its own lever, hanging off a comb
spine by a 1.6 mm neck. Snap one off, test it to destruction, and the other
twenty are untouched - a split boss cannot propagate into its neighbours
because there is 3 mm of air between them. The neck is deliberately the
weakest section on the coupon (1.6 x 2.0 mm, against a 4.55 mm hoop) so it
gives before anything being measured does.

THE WALL AROUND EACH BORE IS THE ARM'S OWN WALL, NOT A ROUND NUMBER
-------------------------------------------------------------------
A coupon with a fat wall tests a hub the arm does not have: hoop stiffness
is what resists splitting, so a generous wall would report an interference
that then splits a real part. `gb_wall` is DERIVED from the reference
implementation - j3_pinion.py prints it as "wall between the boss bore and
the tooth roots" and it is J3_PAIR.r_root(18) - J3_HUB.boss_clear_d / 2 =
7.75 - 3.20 = 4.55 mm. Nothing is typed; if lib/gears.py moves, so does the
coupon.

4.55 is also the CONSERVATIVE choice across the fleet, which is checked
below rather than asserted by prose. The thinnest wall any real part
presents AT THE BROACH SECTION is gripper_pinion's: a m1.5 12T pinion roots
at r 7.125 around a Oe4.65 bore, so 4.80 mm. j3_pinion's own broach section
is 5.375, wrist_hub and shoulder_hub sit inside a Oe20 collar and j1_hub
inside a Oe21.8 disc. 4.55 is under all of them, so the coupon splits
before the arm does - which is the direction an error is allowed to run in.

TORQUE IS TESTED, NOT JUST INSERTION
-------------------------------------
"Does it go on" is the easy half. The question that decides the arm is
"does it SLIP", and that needs a moment applied to a bore that is now full
of steel. Every station therefore carries an integral lever, and the lever
length is SOLVED, not styled: it is the servo's own conservative stall
torque divided by a 10 N tip force - a kilogram, which a kitchen scale
reads and a thumb can produce - capped at 30 mm so the coupon stays a
coupon. The MG995 hits that cap, so its lever needs about 31 N instead;
the script prints the number each station wants and the sheet turns it into
grams on a scale.

The lever is sized against bending too, so it does not become the thing
that fails: width from sqrt(6 M / (t sigma)) with sigma = PETG_SIGMA_MPA /
SAFETY_FACTOR['static'] and M taken as the FULL stall torque (conservative
- the real root moment is smaller by the boss radius). It is then floored
at whatever the raised label needs, because a lever too narrow to carry its
own legend is a station you cannot identify afterwards.

PRINT ORIENTATION IS PART OF THE TEST, NOT A SLICER PREFERENCE
---------------------------------------------------------------
COUPON FLAT ON THE BED, LABELS UP, EVERY BORE VERTICAL. This is not
convenience - a broach into an XY-facing hole is a different experiment:

  1. A hole printed on its side comes out out-of-round and undersize
     (design_rules.HOLE_DIA_COMP_MM, and the reason this project's own
     parts reach for teardrops in XY). The interference under test would
     not be the interference designed, and it would not even be one number
     - it would differ across the hole.
  2. Broaching loads the bore in HOOP TENSION. In a vertical bore that
     hoop runs within a layer, in the strong direction. In a sideways bore
     it runs across layers, at design_rules.Z_TENSILE_FACTOR = 0.5 of the
     strength, so the hub splits at roughly half the interference.
  3. It is what the arm does. Every broached hub in this project prints
     bore-vertical, and j1_hub / shoulder_bracket both record REFUSING to
     put a broach bore in a part that stands on edge, for exactly (1) and
     (2). A gauge printed in the other orientation would answer a question
     nobody is asking.

Print PETG - the same spool the arm will use - 0.2 mm layers, 3 walls,
SUPPORT OFF. Not "auto". OFF. A gauge printed on a different profile is
measuring a different machine, and a gauge printed in PLA is measuring a
different material: calibration/2026-08-14-verge-pole-thread-fit.md already
records PETG running tighter than PLA on this printer.

THE BOTTOM OF EACH BORE IS RELIEVED, AND IT MATTERS MORE HERE THAN ANYWHERE
---------------------------------------------------------------------------
The first few layers of a printed bore are squeezed inward by elephant's
foot. On a normal fit that is a nuisance; on a 0.10 mm interference it is
most of the measurement. So each bore opens out by ELEPHANT_FOOT_CHAMFER_MM
per side over the first `gb_relief_h`, and the station is made that much
TALLER, so the length that actually grips is the full spline height and the
squashed layers grip nothing. It doubles as the lead-in the spline needs to
start - the real parts cut a 0.5 chamfer there for the same reason.

Engagement is therefore the whole spline, which is what every real hub in
the arm gets: SG90 2.50, MG90S 4.00, MG995 3.60 mm.

WHY EVERY FEATURE OVERLAPS THE ONE BEFORE IT BY gb_weld
--------------------------------------------------------
THE FIRST BUILD CAME BACK WITH 122 BODIES instead of one, and the count is
worth writing down because it is exactly diagnostic:

     3   the three spine bars and the rail
    21   station bosses
    21   station levers
    14   station necks - the 7 in the first column welded, the other 14 did not
    63   label glyphs, three per label, none of them touching anything
   ---
   122

Two causes, and they are the same mistake in different clothes.

FIRST, participantBodies. Every JOIN was handed `[coupon]` - the ONE body
captured right after the first spine bar. A Fusion JOIN merges the new lump
only with the bodies it is GIVEN, and only where it actually intersects one
of them; anything else quietly becomes a new body. But this coupon is a
CHAIN - spine, neck, lever, boss - so a boss built first touched nothing
that existed yet, and a neck in the third column touched spine_2, which was
never a participant. _gauge_slim.py gets away with `[plate]` everywhere
because every one of its stations grows straight off the plate. This one
does not, and copying that pattern without copying its topology is the whole
bug. Every JOIN now takes ALL current bodies, and every station is built in
CONTACT ORDER - neck onto the spine, lever onto the neck, boss onto the
lever - so nothing is ever created in mid-air hoping a later feature reaches
back for it. The cuts moved to the end for the same reason: a bore cut
against a body that does not yet own that material removes nothing.

SECOND, A SHARED FACE IS NOT AN INTERSECTION. The neck ended exactly at the
spine's edge, and the raised text started exactly on the lever's top face.
Both are zero-volume contact, and a boolean given zero volume to work with
leaves two bodies. It is worse than cosmetic for the labels: text that only
touches the face it sits on is text a slicer can lay down as 21 floating
islands, so the emboss would not have printed either. Every joined feature
is now driven gb_weld INTO whatever it joins. Nothing visible changes - the
neck's free span is still gb_neck_l, because the weld is buried inside the
spine and the lever, and the label still stands exactly MIN_EMBOSS_MM proud
because it now STARTS below the face instead of on it.

The body count is checked at EVERY phase boundary now rather than once at
the end, and a failure reports the orphan count and where the first of them
are. A bare count says something did not join; it does not say what, or when.

Record the result in calibration/ as a dated note, then change ONE line -
lib/servo.py SPLINE_BROACH_INTERFERENCE_MM - and every broached hub in the
arm moves with it. The sheet says exactly which line and what it reaches.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
# PURGED FIRST, the same way every gate in this folder does it: a stale
# lib.* left in sys.modules by an earlier run is how two scripts end up
# disagreeing about a servo.
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

from lib.arm_loads import PETG_SIGMA_MPA  # noqa: E402
from lib.design_rules import (  # noqa: E402
    ELEPHANT_FOOT_CHAMFER_MM,
    ENVELOPE_SINGLE,
    MIN_EMBOSS_MM,
    MIN_FEATURE_MM,
    MIN_WALL_MM,
    SAFETY_FACTOR,
    Z_TENSILE_FACTOR,
)
from lib.gears import J3_HUB, J3_PAIR  # noqa: E402
from lib.servo import (  # noqa: E402
    CATALOG,
    SPLINE_BROACH_INTERFERENCE_MM,
    SPLINE_TEETH,
    spline_bore_d,
)

COMPONENT = 'robotarm_gauge_broach'
PREFIX = 'gb_'
PH_SPINE = 'spine'
PH_STATIONS = 'stations'
PH_LABELS = 'labels'
PH_BORES = 'bores'
PHASES = [PH_SPINE, PH_STATIONS, PH_LABELS, PH_BORES]
MATERIAL_NAME = 'PET Plastic'

# Fusion's 'PET Plastic' is 1.541 g/cm3 and PETG FILAMENT is ~1.27, so every
# mass Fusion reports is ~21 % high. SOLID_FRACTION 0.65 is MEASURED off the
# gauge_fits v4 slice (96.7 g / (117941 mm3 x 1.27) = 0.646), not assumed.
# Both figures are carried here for the same reason _gauge_slim carries them:
# the project quoted the wrong one for weeks.
PETG_FILAMENT_DENSITY = 1.27
SOLID_FRACTION = 0.65
KGCM_TO_NMM = 98.0665           # 1 kgf.cm = 0.0980665 N.m

# ---- THE SWEEP ------------------------------------------------------------
# 0.10 to 0.40 in 0.05. The bottom is where the spline stops cutting and
# starts polishing (a fifth of a tooth of radial bite); the top is where a
# 4.55 mm PETG hoop is being asked to swallow most of a tooth per side. The
# step is 0.05 because that is about the resolution a printed bore can
# actually hold - design_rules.DIM_TOL_MM is 0.15 per printed dimension in
# plane, so a finer step would be sweeping inside its own noise.
BROACH_LO = 0.10
BROACH_HI = 0.40
BROACH_STEP = 0.05
INTERFERENCE = [
    round(BROACH_LO + k * BROACH_STEP, 4)
    for k in range(int(round((BROACH_HI - BROACH_LO) / BROACH_STEP)) + 1)
]

# ---- the servos, in the order they go on the bed, left to right -----------
# One letter each, because the label has to fit on a 7.5 mm lever and still
# be legible after the boss it is attached to has been twisted apart.
ROW_TAGS = [('S', 'SG90'), ('M', 'MG90S'), ('G', 'MG995')]

# ---- the wall. DERIVED from the reference implementation. -----------------
# j3_pinion.py computes and prints exactly this as `hub_wall`. Mirroring the
# arithmetic rather than the number means a change to J3_PAIR or to the
# MG90S's boss diameter moves the coupon with the part.
HUB_WALL_MM = J3_PAIR.r_root(J3_PAIR.z_pinion) - J3_HUB.boss_clear_d / 2.0

# The thinnest wall any real part presents AT ITS BROACH SECTION, used only
# to prove the coupon is the conservative one. MIRRORED from
# models/robotarm/gripper_pinion.py's shared gear contract (gr_module 1.5,
# gr_teeth 12, gr_ded_f 1.25) - those live as Fusion user parameters in that
# script, not in lib/, so they cannot be imported. If that pinion is
# re-toothed this check has to be re-read.
GRIPPER_MODULE_MM = 1.5
GRIPPER_TEETH = 12
GRIPPER_DEDENDUM_F = 1.25
GRIPPER_ROOT_R_MM = (GRIPPER_MODULE_MM * GRIPPER_TEETH / 2.0
                     - GRIPPER_MODULE_MM * GRIPPER_DEDENDUM_F)

# lib/servo_hub.spline_hub()'s own engage_min default, restated so the
# assertion below reads as a comparison against the library's floor rather
# than against a number invented here.
ENGAGE_MIN_MM = 2.0

# ---- the lever ------------------------------------------------------------
# 10 N is a kilogram on a kitchen scale: producible with a thumb, readable
# to a few grams, and nowhere near what would break a wrist if the station
# lets go suddenly. 30 mm caps the coupon's size; the MG995 hits the cap and
# the script prints what it costs.
TIP_FORCE_TARGET_N = 10.0
LEVER_R_MAX_MM = 30.0
# Glyph advance as a fraction of cap height, for the label's footprint.
# _gauge_slim uses 0.95 as a deliberately generous COLLISION bound; 0.80 is
# the advance itself, and it is used here to size a pocket the text must fit
# inside, with the fit asserted rather than eyeballed.
TEXT_ADVANCE = 0.80
LABEL_CHARS = 3


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value * 10      # -> MILLIMETRES

    # ---- parameters. Every one of these drives geometry below. ------------
    param('wall', '%.4f mm' % HUB_WALL_MM,
          'hoop of PETG around every bore. DERIVED, never typed: it is\n'
          '           j3_pinion.py\'s own reported hub_wall, J3_PAIR.r_root(18) minus\n'
          '           half J3_HUB.boss_clear_d. A fatter coupon would report an\n'
          '           interference that then splits a real hub.')
    param('relief_h', '0.6 mm',
          'the bottom of every bore opens out for this depth, so the layers\n'
          '           elephant\'s foot has squeezed inward grip nothing. Three 0.2 mm\n'
          '           layers. It is also the lead-in the spline needs to start, and\n'
          '           the station is made this much TALLER so the gripping length is\n'
          '           still the full spline height.')
    param('relief_r', '%.4f mm' % ELEPHANT_FOOT_CHAMFER_MM,
          'how far the relief opens out PER SIDE - design_rules\n'
          '           ELEPHANT_FOOT_CHAMFER_MM, which is CALIBRATED on this printer\n'
          '           as the amount a first layer spreads.')
    param('emboss_h', '%.4f mm' % MIN_EMBOSS_MM,
          'label relief height - design_rules MIN_EMBOSS_MM. RAISED, not\n'
          '           engraved as the plate gauges are: a 0.6 groove in a 3.1 mm lever\n'
          '           is a fifth of its section, and this lever is deliberately loaded\n'
          '           to the servo\'s stall torque.')
    param('text_h', '5.0 mm',
          'cap height. Bigger than the 3.5 the plate gauges engrave, because\n'
          '           raised text needs a stroke at least MIN_EMBOSS_MM wide and a\n'
          '           stroke is roughly an eighth of cap height. Asserted below.')
    param('pad', '1.25 mm', 'margin between a label and the edge of its lever')
    param('neck_w', '%.4f mm' % MIN_WALL_MM,
          'breakaway neck width. THE WEAKEST SECTION ON THE COUPON ON PURPOSE:\n'
          '           MIN_WALL_MM against a %.2f mm hoop, so it lets go long before\n'
          '           anything being measured does.' % HUB_WALL_MM)
    param('neck_l', '2.5 mm', 'air between a lever tip and the spine - room for cutters')
    param('spine_w', '4.0 mm', 'the comb backbone, across')
    param('spine_t', '2.0 mm',
          'and how thick. Thinner than every station so the spine cannot\n'
          '           stiffen a station that is being twisted, and so a snapped neck\n'
          '           leaves nothing proud.')
    param('sta_gap', '3.0 mm',
          'air between neighbouring bosses. A split boss must not be able to\n'
          '           reach its neighbour - that is what makes the stations\n'
          '           independent rather than merely adjacent.')
    param('col_gap', '4.0 mm', 'air between one servo\'s column and the next')
    param('over', '1.0 mm', 'cut overrun, so a through bore is unambiguously through')
    param('weld', '0.8 mm',
          'HOW FAR EVERY JOINED FEATURE IS DRIVEN INTO THE ONE IT JOINS TO.\n'
          '           A shared face is not an intersection: the first build butted the\n'
          '           necks against the spine edge and started the raised text exactly\n'
          '           on the lever face, and Fusion returned 122 separate bodies. It is\n'
          '           buried material, so it changes no visible dimension - the neck\n'
          '           free span is still gb_neck_l and the label still stands\n'
          '           MIN_EMBOSS_MM proud, because it starts BELOW the face.')

    wall = val('wall')
    relief_h = val('relief_h')
    relief_r = val('relief_r')
    emboss_h = val('emboss_h')
    text_h = val('text_h')
    pad = val('pad')
    neck_w = val('neck_w')
    neck_l = val('neck_l')
    spine_w = val('spine_w')
    spine_t = val('spine_t')
    sta_gap = val('sta_gap')
    col_gap = val('col_gap')
    over = val('over')
    weld = val('weld')

    # ---- solve the columns. NOTHING below is typed. -----------------------
    label_len = LABEL_CHARS * TEXT_ADVANCE * text_h
    sigma_allow = PETG_SIGMA_MPA / SAFETY_FACTOR['static']
    cols = []
    for tag, name in ROW_TAGS:
        s = CATALOG[name]
        bores = [spline_bore_d(s, i) for i in INTERFERENCE]
        bosses = [b + 2.0 * wall for b in bores]
        max_boss = max(bosses)
        sta_h = s.spline_h + relief_h
        stall_nmm = s.stall_kgcm * KGCM_TO_NMM
        # WHERE THE LEVER LENGTH COMES FROM. Torque sets it; the label sets a
        # floor under it; the coupon's size caps it.
        by_torque = stall_nmm / TIP_FORCE_TARGET_N
        by_label = max_boss / 2.0 + label_len + 2.0 * pad
        lever_r = math.ceil(
            max(min(by_torque, LEVER_R_MAX_MM), by_label) * 2.0) / 2.0
        # ... and the width from bending, at the FULL stall torque. The real
        # root moment is smaller by the boss radius; using the whole thing
        # keeps the lever out of the answer.
        w_bend = math.sqrt(6.0 * stall_nmm / (sta_h * sigma_allow))
        lever_w = math.ceil(max(w_bend, text_h + 2.0 * pad) * 2.0) / 2.0
        module_spline = s.spline_dia / SPLINE_TEETH[name]
        cols.append({
            'tag': tag, 'name': name, 'servo': s,
            'bores': bores, 'bosses': bosses, 'max_boss': max_boss,
            'sta_h': sta_h, 'engage': s.spline_h,
            'lever_r': lever_r, 'lever_w': lever_w,
            'stall_nmm': stall_nmm, 'tip_n': stall_nmm / lever_r,
            'w_bend': w_bend, 'module': module_spline,
        })

    pitch = max(c['max_boss'] for c in cols) + sta_gap
    n_sta = len(INTERFERENCE)
    row_y = [-k * pitch for k in range(n_sta)]
    y_top = max(c['max_boss'] for c in cols) / 2.0
    y_bot = row_y[-1] - y_top
    rail_y1 = y_bot - sta_gap
    rail_y0 = rail_y1 - spine_w

    x = 0.0
    for c in cols:
        c['x0'] = x
        c['cx'] = x + c['max_boss'] / 2.0
        c['tip_x'] = c['cx'] + c['lever_r']
        c['spine_x0'] = c['tip_x'] + neck_l
        c['spine_x1'] = c['spine_x0'] + spine_w
        x = c['spine_x1'] + col_gap

    # ---- everything that has to be true BEFORE any geometry ---------------
    # Units: every literal here is MILLIMETRES and every variable it meets
    # has already been scaled by val(). _gauge_fits once compared centimetres
    # against millimetre literals and fired on perfectly good geometry.
    assert abs(INTERFERENCE[0] - BROACH_LO) < 1e-9, 'the sweep lost its low end'
    assert abs(INTERFERENCE[-1] - BROACH_HI) < 1e-9, 'the sweep lost its high end'
    assert any(abs(i - SPLINE_BROACH_INTERFERENCE_MM) < 1e-9 for i in INTERFERENCE), (
        'lib/servo.SPLINE_BROACH_INTERFERENCE_MM is %.3f and the sweep is %s - '
        'the value the arm SHIPS has to be one of the stations, or the coupon '
        'has no control to read the others against'
        % (SPLINE_BROACH_INTERFERENCE_MM, INTERFERENCE))
    assert wall >= MIN_WALL_MM, (
        'a %.2f mm hoop is under MIN_WALL_MM %.2f - the coupon would fail as a '
        'print, not as a fit' % (wall, MIN_WALL_MM))
    gp_wall = GRIPPER_ROOT_R_MM - spline_bore_d(CATALOG['SG90']) / 2.0
    assert wall <= gp_wall + 1e-9, (
        'the coupon wall %.2f is FATTER than gripper_pinion\'s %.2f at its own '
        'broach section - the coupon would survive an interference that splits '
        'a real part, which is the one direction this must not be wrong in'
        % (wall, gp_wall))
    assert abs(wall - (J3_PAIR.r_root(J3_PAIR.z_pinion)
                       - J3_HUB.boss_clear_d / 2.0)) < 1e-9, (
        'gb_wall no longer equals j3_pinion\'s reported hub_wall')
    assert CATALOG['SG90'].spline_dia != CATALOG['MG90S'].spline_dia, (
        'lib/servo.py now gives the SG90 and MG90S the same spline - if that is '
        'right, this coupon is sweeping the same bore twice and one row should '
        'come off it')
    assert text_h * 0.125 >= MIN_EMBOSS_MM - 1e-9, (
        'a %.1f mm cap height gives roughly a %.2f mm stroke, under '
        'MIN_EMBOSS_MM %.2f - raised text that thin does not print'
        % (text_h, text_h * 0.125, MIN_EMBOSS_MM))
    assert neck_w >= MIN_FEATURE_MM, (
        'a %.2f mm neck is under MIN_FEATURE_MM %.2f' % (neck_w, MIN_FEATURE_MM))
    assert neck_w < wall, (
        'the %.2f neck is not weaker than the %.2f hoop - snapping a station '
        'off would crack the thing being measured' % (neck_w, wall))
    assert relief_h > 0.0 and relief_r > 0.0, 'the bore relief has no size'
    assert weld > 0.0, (
        'a zero weld is what produced 122 bodies - a boolean needs volume to '
        'work with, not a shared face')
    assert weld < neck_l, (
        'a %.2f weld eats the whole %.2f neck - there would be no free span '
        'left to snap' % (weld, neck_l))
    assert weld < spine_w, 'the weld drives the neck clean through the spine'

    for c in cols:
        s = c['servo']
        assert c['engage'] >= ENGAGE_MIN_MM, (
            '%s engages only %.2f mm of spline against spline_hub()\'s %.2f floor'
            % (c['name'], c['engage'], ENGAGE_MIN_MM))
        assert abs(c['sta_h'] - (c['engage'] + relief_h)) < 1e-9, (
            '%s station height and its gripping length disagree' % c['name'])
        for i, b in zip(INTERFERENCE, c['bores']):
            assert abs((s.spline_dia - i) - b) < 1e-9, (
                '%s at %.2f: the bore %.3f is not spline_dia %.2f less the '
                'interference - a number got typed somewhere'
                % (c['name'], i, b, s.spline_dia))
            assert b > 0.0, '%s at %.2f has no bore left' % (c['name'], i)
            # THE STATION HAS TO LAND ON THE OUTPUT BOSS. The bore only meets
            # the spline; the underside seats on the collar below it. A bore
            # as wide as that collar would swallow it and the coupon would
            # slide straight past the spline, testing nothing.
            assert b < s.boss_dia, (
                '%s at %.2f: the Oe%.3f bore is not smaller than the Oe%.2f '
                'output collar - the station would drop over the boss instead '
                'of seating on it' % (c['name'], i, b, s.boss_dia))
        assert c['lever_w'] >= text_h + 2.0 * pad - 1e-9, (
            '%s lever %.2f wide cannot carry a %.1f label' % (c['name'], c['lever_w'], text_h))
        assert c['lever_r'] - c['max_boss'] / 2.0 >= label_len + 2.0 * pad - 1e-9, (
            '%s lever is %.2f long past the boss and the label needs %.2f'
            % (c['name'], c['lever_r'] - c['max_boss'] / 2.0, label_len + 2.0 * pad))
        assert c['lever_w'] >= c['w_bend'], (
            '%s lever is %.2f wide and bending wants %.2f - the lever would '
            'fail before the bore did' % (c['name'], c['lever_w'], c['w_bend']))
    assert pitch > max(c['max_boss'] for c in cols), 'the bosses overlap in a column'
    for a in range(len(cols) - 1):
        assert cols[a]['spine_x1'] + col_gap <= cols[a + 1]['x0'] + 1e-9, (
            'columns %d and %d touch' % (a, a + 1))
    assert rail_y1 < y_bot, 'the rail sits inside the bottom row'

    # ---- idempotent rebuild. RENAME FIRST, THEN DELETE. fusion/PLAYBOOK.md -
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        # SKIP THE ROOT. Once this lives in its own saved file the root
        # component carries the DOCUMENT's name, which is COMPONENT, and a
        # root component cannot be renamed - the rename raises "3 : root
        # component name cannot be changed" and nothing rebuilds.
        if c == design.rootComponent:
            continue
        if c.name == COMPONENT or c.name.startswith(COMPONENT + ' ('):
            c.name = STALE + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(STALE):
            occ.deleteMe()
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = COMPONENT
    assert comp.name == COMPONENT, (
        'component came back as %r - a stale component still holds the name'
        % comp.name)
    ext = comp.features.extrudeFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mm(v):
        return '%.4f mm' % v

    def pt(sk, px, py):
        return sk.modelToSketchSpace(P3(px / 10.0, py / 10.0, 0))

    def one(sk):
        assert sk.profiles.count == 1, (
            sk.name + ': expected 1 profile, got %d' % sk.profiles.count)
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        return col

    def extrude_profs(profs, op, z0, dz, name, targets=None):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0)))
        inp.setDistanceExtent(False, V(mm(dz)))
        if op != NEW:
            # Without participantBodies a CUT eats every other body. PLAYBOOK.md.
            inp.participantBodies = targets if targets is not None else [
                comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def circle(name, cx, cy, d, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, cx, cy), d / 20.0)
        return extrude_profs(one(sk), op, z0, dz, name, targets)

    def rect(name, x0, x1, y0, y1, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(sk, x0, y0), pt(sk, x1, y1))
        return extrude_profs(one(sk), op, z0, dz, name, targets)

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    def one_body(where):
        """The coupon is ONE piece, checked at every phase boundary.

        THE FIRST BUILD RETURNED 122 BODIES and a single check at the end
        could only say that something had not joined - not what, and not
        when. Called after each phase, this names the phase; and when it
        does fire it reports the orphan COUNT and where the first few of
        them sit, because an orphan's bounding box says immediately whether
        it is a boss, a lever or a label glyph.
        """
        n = comp.bRepBodies.count
        det = []
        for bi in range(min(n, 6)):
            b = comp.bRepBodies.item(bi)
            bx = b.boundingBox
            det.append('%s %.1f mm3 X %.1f..%.1f Y %.1f..%.1f Z %.1f..%.1f'
                       % (b.name, b.volume * 1000,
                          bx.minPoint.x * 10, bx.maxPoint.x * 10,
                          bx.minPoint.y * 10, bx.maxPoint.y * 10,
                          bx.minPoint.z * 10, bx.maxPoint.z * 10))
        assert n == 1, (
            'after %s: expected 1 body, got %d - %d orphan(s) that did not '
            'touch what they were meant to touch. First %d: %s'
            % (where, n, n - 1, len(det), ' | '.join(det)))

    # ---- phase 1: the comb -------------------------------------------------
    # One spine per servo column, joined at the foot by a rail, so the whole
    # coupon comes off the bed as ONE piece and no station can be mislaid
    # before it has been read.
    t0 = design.timeline.count
    # NO participantBodies ANYWHERE FROM HERE ON. extrude_profs() falls back
    # to every body in the component, which is what a JOIN on a chained shape
    # has to see: the three spine bars do not touch each other, and it is the
    # RAIL that unites them. Naming a single body as the participant is what
    # left spine_1 and spine_2 orphaned in the first build.
    rect('spine_0', cols[0]['spine_x0'], cols[0]['spine_x1'], rail_y0, y_top,
         0.0, spine_t, NEW)
    for ci in range(1, len(cols)):
        rect('spine_%d' % ci, cols[ci]['spine_x0'], cols[ci]['spine_x1'],
             rail_y0, y_top, 0.0, spine_t, JOIN)
    # the rail overlaps all three bars over rail_y0..rail_y1 - a real volume,
    # not a shared edge - so this is the feature that makes the comb one piece
    rect('rail', cols[0]['spine_x0'], cols[-1]['spine_x1'], rail_y0, rail_y1,
         0.0, spine_t, JOIN)
    group(t0, PH_SPINE)
    one_body('phase 1, the comb')

    # ---- phase 2: the stations ---------------------------------------------
    t1 = design.timeline.count
    for c in cols:
        h = c['sta_h']
        for k, i in enumerate(INTERFERENCE):
            nm = '%s%02d' % (c['tag'], int(round(i * 100)))
            y = row_y[k]
            bd = c['bosses'][k]
            # BUILT IN CONTACT ORDER: neck onto the spine, lever onto the
            # neck, boss onto the lever. The first version built the boss
            # first, in mid-air, and Fusion had nothing to join it to.
            #
            # the breakaway neck, thin in Z as well as narrow in plan. It
            # runs a weld PAST the spine edge at one end and a weld INTO the
            # lever's footprint at the other, so both booleans get volume.
            rect('neck_' + nm, c['tip_x'] - weld, c['spine_x0'] + weld,
                 y - neck_w / 2.0, y + neck_w / 2.0, 0.0, spine_t, JOIN)
            # the lever: torque handle, label carrier and the thing the user
            # actually holds. It reaches back to the bore AXIS, so the boss
            # is welded into it over a full radius rather than tangent to it.
            rect('lever_' + nm, c['cx'], c['tip_x'],
                 y - c['lever_w'] / 2.0, y + c['lever_w'] / 2.0, 0.0, h, JOIN)
            # the hoop under test
            circle('boss_' + nm, c['cx'], y, bd, 0.0, h, JOIN)
        one_body('phase 2, column %s' % c['tag'])
    group(t1, PH_STATIONS)

    # ---- phase 3: the labels -----------------------------------------------
    # RAISED, and extruded from the SketchText OBJECT rather than from
    # sk.profiles - a SketchText does not populate profiles on this Fusion
    # build, and the first version of _gauge_fits silently collected zero and
    # cut nothing, leaving an unlabelled gauge. An unlabelled gauge is worse
    # than no gauge: you cannot tell the stations apart afterwards, and after
    # this test the bores are no longer round enough to caliper.
    t2 = design.timeline.count
    n_lab = 0
    for c in cols:
        h = c['sta_h']
        lab_cx = (c['cx'] + c['max_boss'] / 2.0 + pad + c['tip_x'] - pad) / 2.0
        half_w = label_len / 2.0 + pad
        half_h = text_h / 2.0 + pad
        assert lab_cx - half_w >= c['cx'] + c['max_boss'] / 2.0 - 1e-9, (
            '%s label starts inside the boss' % c['name'])
        assert lab_cx + half_w <= c['tip_x'] + 1e-9, (
            '%s label runs off the lever tip' % c['name'])
        assert half_h <= c['lever_w'] / 2.0 + 1e-9, (
            '%s label is taller than its lever is wide' % c['name'])
        for k, i in enumerate(INTERFERENCE):
            nm = '%s%02d' % (c['tag'], int(round(i * 100)))
            y = row_y[k]
            sk = sketch('lab_' + nm)
            t_in = sk.sketchTexts.createInput2(nm, text_h / 10.0)
            t_in.setAsMultiLine(
                pt(sk, lab_cx - half_w, y - half_h),
                pt(sk, lab_cx + half_w, y + half_h),
                adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            st = sk.sketchTexts.add(t_in)
            inp = ext.createInput(st, JOIN)
            # STARTS BELOW THE FACE, NOT ON IT. Text extruded from z = h
            # upward only touches the lever - three glyphs, three shared
            # faces, three new bodies each, and a slicer would have printed
            # them as floating islands. Starting a weld down means the
            # boolean has volume; the relief above the face is still exactly
            # emboss_h, which is MIN_EMBOSS_MM.
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
                V(mm(h - weld)))
            inp.setDistanceExtent(False, V(mm(emboss_h + weld)))
            inp.participantBodies = [
                comp.bRepBodies.item(bi) for bi in range(comp.bRepBodies.count)]
            ext.add(inp).name = 'lab_' + nm
            n_lab += 1
        one_body('phase 3, labels for column %s' % c['tag'])
    group(t2, PH_LABELS)

    # ---- phase 4: the bores -------------------------------------------------
    # CUT LAST, and that is not tidiness. A cut is applied to the bodies it is
    # given, where they have material; running the bores while the boss was
    # still an orphan meant they removed nothing at all from the body that was
    # named. By here the coupon is one solid and every bore lands in it.
    t3 = design.timeline.count
    for c in cols:
        h = c['sta_h']
        for k, i in enumerate(INTERFERENCE):
            nm = '%s%02d' % (c['tag'], int(round(i * 100)))
            y = row_y[k]
            bore = c['bores'][k]
            # THE BORE. Through, vertical, and the only dimension on this
            # coupon that is being asked a question.
            circle('bore_' + nm, c['cx'], y, bore, -over, h + 2.0 * over, CUT)
            # ... and the elephant's-foot relief at its mouth, which is also
            # the lead-in the spline enters on.
            circle('relief_' + nm, c['cx'], y, bore + 2.0 * relief_r,
                   -over, relief_h + over, CUT)
    group(t3, PH_BORES)
    one_body('phase 4, the bores')

    # ---- identity ----------------------------------------------------------
    # ONE body. THIS ASSERT IS THE ONE THAT CAUGHT THE 122-BODY BUILD, so it
    # stays exactly where it is; one_body() only makes it say more, and the
    # per-phase calls above make it say it sooner.
    one_body('the whole build - the comb, its stations, labels and bores')
    body = comp.bRepBodies.item(0)
    body.name = 'gauge_broach_coupon'
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break

    bb = body.boundingBox
    bed = ((bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10)
    assert bed[0] <= ENVELOPE_SINGLE[0] and bed[1] <= ENVELOPE_SINGLE[1], (
        'the coupon needs a %.0f x %.0f bed; ENVELOPE_SINGLE is %.0f x %.0f'
        % (bed[0], bed[1], ENVELOPE_SINGLE[0], ENVELOPE_SINGLE[1]))
    assert n_lab == len(cols) * n_sta, (
        'engraved %d labels for %d stations' % (n_lab, len(cols) * n_sta))

    # ---- diagnostics --------------------------------------------------------
    vol = body.volume * 1000
    print('component: %r | body: %r' % (comp.name, body.name))
    print('')
    print('THE ONE NUMBER: lib/servo.SPLINE_BROACH_INTERFERENCE_MM = %.2f, ASSUMED.'
          % SPLINE_BROACH_INTERFERENCE_MM)
    print('  swept %.2f .. %.2f in %.2f -> %s'
          % (BROACH_LO, BROACH_HI, BROACH_STEP, INTERFERENCE))
    print('  the shipping value sits at station index %d, which is the control.'
          % INTERFERENCE.index(SPLINE_BROACH_INTERFERENCE_MM))
    print('')
    print('WALL: %.2f mm of PETG around every bore. DERIVED = j3_pinion hub_wall'
          % wall)
    print('  J3_PAIR.r_root(%d) %.2f - J3_HUB.boss_clear_d/2 %.2f = %.2f'
          % (J3_PAIR.z_pinion, J3_PAIR.r_root(J3_PAIR.z_pinion),
             J3_HUB.boss_clear_d / 2.0, wall))
    print('  thinnest real broach-section wall in the arm is gripper_pinion\'s '
          '%.2f, so this coupon splits FIRST. Correct direction.' % gp_wall)
    print('')
    print('STATIONS - 3 splines x %d interferences = %d, each on its own boss'
          % (n_sta, len(cols) * n_sta))
    print('  %-4s %-6s %6s %6s %6s %6s %6s %7s'
          % ('lab', 'servo', 'intf', 'bore', 'bossOD', 'grip', 'bite%', 'tipN'))
    for c in cols:
        for i, b, bd in zip(INTERFERENCE, c['bores'], c['bosses']):
            print('  %-4s %-6s %6.2f %6.3f %6.2f %6.2f %6.0f %7.1f'
                  % ('%s%02d' % (c['tag'], int(round(i * 100))), c['name'],
                     i, b, bd, c['engage'], 100.0 * (i / 2.0) / c['module'],
                     c['tip_n']))
    print('')
    print('BITE is the RADIAL interference as a fraction of one spline module')
    print('  (addendum taken as 1 x m, ESTIMATED - no drawing of these splines')
    print('  exists). Below ~25 %% the steel planes the bore; above ~75 %% the')
    print('  hoop has to swallow most of a tooth per side.')
    for c in cols:
        print('  %-6s Oe%.2f / %dT -> m %.3f mm, tooth ~%.2f mm'
              % (c['name'], c['servo'].spline_dia, SPLINE_TEETH[c['name']],
                 c['module'], c['module']))
    print('')
    print('LEVERS - solved from each servo\'s own conservative stall torque')
    for c in cols:
        print('  %-6s stall %.1f kg.cm = %.0f N.mm | arm %.1f mm | tip %.1f N '
              '(%.0f g on a scale) | %.1f x %.1f section'
              % (c['name'], c['servo'].stall_kgcm, c['stall_nmm'], c['lever_r'],
                 c['tip_n'], c['tip_n'] * 1000.0 / 9.80665, c['lever_w'], c['sta_h']))
    print('  target tip force was %.1f N, capped at a %.1f mm arm - the MG995 '
          'is the one that hits the cap.' % (TIP_FORCE_TARGET_N, LEVER_R_MAX_MM))
    print('  lever allowable %.1f MPa = PETG_SIGMA_MPA %.0f / static SF %.1f, '
          'in-plane (bending about Z, NOT across layers at %.2f)'
          % (sigma_allow, PETG_SIGMA_MPA, SAFETY_FACTOR['static'], Z_TENSILE_FACTOR))
    print('')
    print('ORIENTATION: FLAT ON THE BED, LABELS UP, EVERY BORE VERTICAL.')
    print('  Same as every broached hub in the arm. A sideways bore prints')
    print('  out-of-round and undersize, and puts the broaching hoop stress')
    print('  ACROSS layers at Z_TENSILE_FACTOR %.2f - it would split at about'
          % Z_TENSILE_FACTOR)
    print('  half the interference and answer a question nobody asked.')
    print('  Supports OFF. Nothing here overhangs; "auto" would only add')
    print('  material inside the bores, which are the measurement.')
    print('')
    print('breakaway: %.2f x %.2f mm neck per station over a %.2f mm free '
          'span, %.2f mm of air between bosses'
          % (neck_w, spine_t, neck_l, sta_gap))
    print('  every joint welded %.2f mm INTO what it joins - a shared face is '
          'not an intersection, and the first build proved it at 122 bodies'
          % weld)
    print('labels: %d raised %.1f mm text, %.2f proud (MIN_EMBOSS_MM %.2f)'
          % (n_lab, text_h, emboss_h, MIN_EMBOSS_MM))
    print('bbox mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('BED: %.0f x %.0f mm (envelope %.0f x %.0f)'
          % (bed[0], bed[1], ENVELOPE_SINGLE[0], ENVELOPE_SINGLE[1]))
    print('volume %.0f mm3 | PETG %.3f g/cm3 x %.0f%% solid -> %.1f g PRINTED'
          % (vol, PETG_FILAMENT_DENSITY, SOLID_FRACTION * 100,
             vol * PETG_FILAMENT_DENSITY * SOLID_FRACTION / 1000.0))
    print('  (%.1f g solid, and %.1f g if you believe Fusion\'s PET density - '
          'the project has quoted that wrong one before)'
          % (vol * PETG_FILAMENT_DENSITY / 1000.0,
             body.physicalProperties.mass * 1000))
    print('bodies: %d | sketches: %d | user params: %d | valid: %s'
          % (comp.bRepBodies.count, comp.sketches.count, ups.count, body.isValid))
    print('timeline groups: %r' % (PHASES,))
