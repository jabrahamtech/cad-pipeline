"""robotarm/forearm - Fusion MCP generating script.

Rebuilds `robotarm_forearm` (idempotent). Spec: specs/robotarm/forearm.md,
styled per specs/robotarm/_style.md.

L2 = 40 mm of link carrying BOTH wrist servos and forking at BOTH ends.

Local frame: origin on the J4 PITCH axis. +X along that axis, +Y forward
toward the hand, +Z up. The J3 elbow axis is at y = -fa_l2.

WHY IT FORKS AT BOTH ENDS. The first layout had the forearm straddled at
the elbow and forking at the wrist. It cannot be built. Material inside the
straddle has to clear the roll housing's 26 mm sweep about J4, so it can
only live at y < -26; material outboard has to clear the upper arm's own
prongs, so it can only live at y > -25.8. The two regions do not touch, and
nothing at 12.0 < |x| < 12.4 can bridge them without eating the running
clearance. Fork at both ends and the side walls run unbroken from pivot to
pivot, which is what this part is: two walls and a web.

THE CLEARANCE IS CUT, NOT DRAWN. Two cylinders - wr_sweep_r about J4 and
fa_elbow_clear about J3 - are subtracted from everything inside the
straddle. The web that survives is an hourglass, narrow on the arm's
centreline where the two swings nearly meet and wide above and below where
they do not. Drawing that outline by hand would be a guess that goes stale
the moment either neighbour changes size; cutting it cannot.

J3's SERVO PAD IS NOT PART OF THIS FILE ANY MORE. It is `j3_servo_cap`,
bolted to the end of the standoff web with two M3. That is not tidiness: with
the pad integral the elbow could not be assembled at all - GATE j3_installs
found the 36T gear 1.25 mm too big to pass its own insertion path, the pinion
short of its run-up onto the horn by 6.8 mm, and the retention M3 with 1.20 mm
of hex-key clearance where a bit needs 25. All three were the pad being in the
way, and all three go when it lifts off. See _HANDOFF.md section 10.

What stays here is the standoff WEB, so section 9's load path is unchanged.

BOTH wrist servos hang off this part, staggered: J4's on +X, J3's on -X.
That is forced, not chosen. A micro servo is ~24 mm along its own shaft
axis, so a servo driving a joint whose axis is X occupies 24 mm of X.
WHICH micro servo is lib/joints.JOINT_SERVO's answer, not this file's - both
were MG90S until 2026-09-03 and both are SG90 now, and every case, tab and
lobe number below is read from that mapping rather than typed. Inboard is
the straddle and it is spoken for, so the servo goes outboard. Hiding it in
the link behind a 1:1 gear pair was priced and rejected: the case would
have had to start 28.6 mm behind the pitch axis and end 12.6 mm PAST the
elbow.

THIS FILE IS THE ASSEMBLED REFERENCE AND IS NOT THE PRINTED PART ANY MORE.
The forearm prints as THREE pieces - forearm_px, forearm_nx and two copies of
forearm_rail - and lib/forearm_split.py is the contract all four scripts
share. This body is still built, and has to be: every fa_* parameter is
declared here, and wrist_hub.py, j3_servo_cap.py, _check_leads.py and
_check_servo_fit.py all read them out of the document BY NAME, with GATE
servo_fit measuring a solid servo (lib/joints.JOINT_SERVO says which)
against this solid. Build it; do not print
it. _export_plates.py still carries a row for `forearm` and knows nothing
about the three pieces - that row has to be replaced, and this file cannot
do it.

WHY IT IS SPLIT. In one piece, built along +X, it wants 2391 mm2 of support -
and 918 mm2 of that is a SINGLE FACE: the +X plate's inner face at
fa_plate_in, a 72 x 28 slab floating 43 mm up over the straddle on nothing
but the two rails. Nothing inside this file can reach it. The volume beneath
it is the wr_sweep_r 25.4 disc about J4 and the fa_elbow_clear 13.4 disc
about J3; that is running clearance and it has to stay empty. So support goes
in there, and it comes back out through a 24.8 mm slot 43 mm deep, and the
face it scars on the way is fa_plate_in - which IS fa_gap, 0.40, the J4
running gap.

AND NOT ON x = 0, WHICH IS THE OBVIOUS PLANE AND THE WRONG ONE. Splitting
down the middle, the way wrist_roll was split, leaves half the straddle in
each half - so each half still floats its own plate. Measured: 1194 mm2 for
the +X half at its best orientation, 1083 for the -X half. It halves the DROP
and fixes nothing.

What works instead comes out of one observation: a side plate is a horizontal
SLAB when it is built along X, and a slab prints perfectly if it is the FIRST
LAYER and impossibly if it is not. So each plate is split off at its OWN
INNER FACE and printed inner-face-down - 1030 and 1084 mm2 of first layer -
and everything outboard of it, boss and seat and servo block, is narrower
than the plate and lands on it. Every pocket that used to be a roof now opens
at the top of the build.

THE THIRD PIECE IS FORCED BY THAT, not chosen: nothing that reaches ACROSS
the straddle can belong to a plate that begins at its own inner face, because
"across the straddle" means "below the bed". So the box-beam rails become
their own piece - a prism along X, which is the one thing in this part that
prints with nothing over 50 deg in any orientation. Both rails are the same
solid: the straddle and both sweep cylinders are symmetric in Z, so the
bottom rail is the top one turned 180 deg about Y. A rotation, not a
reflection, so there is no handedness to get wrong.

WHAT THE SPLIT COSTS AND BUYS. It costs one seam, 8 x M3 x 12, and +1.07 g of
rail. It takes the support from 2391 mm2 to 760 - and, which matters more,
NONE of what is left is inside the straddle and none of it touches a running
face. specs/robotarm/_forearm_print.md carries the per-piece tables, the seam
arithmetic and the three roofs that still bridge.

THE TWO-STEP J4 POCKET IS NOT THE PROBLEM AND NEVER WAS - recorded here so it
is not "simplified" back by someone who reads "stepped blind sideways pocket"
and assumes the worst. Built along +X the case window and the flange recess
both open UPWARD, and the recess is the WIDER of the two, so the step between
them is an upward-facing tab bed rather than a roof. Measured ceiling at the
recess floor and at the pilot tops: 0.00 mm2 each. The flange recess that
fixed GATE servo_fit costs this part nothing to print.

THE J4 LOBE IS 0.40 THICKER THAN IT WAS, AND THAT IS THE HORN MIGRATION
LANDING HERE. wrist_hub.py now bores onto the servo's SPLINE instead of a
horn, and lib/servo_hub seats every spline hub ONE RUNNING GAP off the case
top - wh_seat_z 5.50 -> 5.90 on the MG90S, and 7.10 on the SG90 that
replaced it, because that servo carries 1.20 mm more case above its tabs. The horn-era stack sat that hub's face FLAT
on the case top with zero gap while it rotated against it, which is a brake
rather than a joint. So the J4 tab PLANE stands 0.40 further out
(fa_j4_lobe_t) and the case top lands 0.40 outboard of fa_plate_out, which
puts the hub's seating face back exactly on fa_plate_out where every
downstream wrist dimension already expects it. Cost: 0.40 mm of arm width,
once. J3 is deliberately untouched - see the note at fa_j4_standoff.

THE J4 LOBE IS CUT IN TWO STEPS, NOT ONE, AND THE FLANGE IS WHY. A micro
servo is not a box. Reading up from its case top there is tab_below_top of
bare case and then tab_thk of mounting FLANGE, and that flange is tab_span
long against a much shorter case - 4.65 wider at each end on the MG90S,
4.80 on the SG90 that replaced it. A single window sized for the case lands
the flange on solid lobe. That is measured, not argued: GATE servo_fit
builds the servo solid from servo_body.py and found 195.75 mm3 of MG90S
inside this part, in the band x 23.40..24.90 and nowhere else, which is the
flange band exactly. THAT MEASUREMENT IS NOW AGAINST THE OLD SERVO and the
band has moved outboard with fa_j4_lobe_t - re-run the gate. So the case window is cut for the case
alone and a FLANGE RECESS takes the last tab_thk out to the tab plane.
specs/robotarm/_flange.md has the derivation, the two rejected
alternatives and every cost.

BOTH SERVO BLOCKS WERE STANDING ON 3.00 mm OF AIR, AND fa_lobe_seat IS THAT
FIXED. Each block is sized to land on a fa_plate_t plate and fa_lobe_over
sinks it 1.00 mm into one - but the plate is only fa_plate_t INSIDE the two
boss circles. Everywhere else it is fa_waist_t, which stops at
fa_plate_in + fa_waist_t = 15.90, and the blocks start at 18.90. So for the
whole of each block that overhangs its boss there was a 3.00 mm gap, and the
block bridged it in mid-air. Measured on the +X side: the J4 lobe hangs
9.53 mm past its boss circle at the elbow end and 184.5 mm2 of its underside
had nothing at all beneath it - directly under the servo the bench complaint
names. The J3 standoff block hangs the same 3.00 mm clear of the web.

fa_lobe_seat fills exactly that gap and nothing else: the plate at FULL
thickness under each servo block, from the outer face inward, overlapping
both the web and the block so no two volumes meet on a bare plane. It is cut
back to fa_seat_z = fa_lobe_z - fa_wall in Z and to fa_seat_y_max in +Y, and
that inset is not styling - it keeps the seat strictly inside both the lobe
silhouette and the link outline, so it cannot touch a lobe corner edge the
phase-6 fillet has to run along, and cannot stand proud of the part. Cost
1197 mm3, 1.5 g. Measured return: the J4 lobe underside 188.9 -> 38.0 mm2
and the waist ceiling 526.2 -> 266.7, total support 2802 -> 2391 mm2.

It is a stiffness fix as much as a print fix. The J4 servo reacts its stall
torque as a couple into this lobe, and until now that couple was carried by
a 1.00 mm lip of fa_lobe_over into a plate that was not there.

The SHARED wr_* block is defined identically in wrist_hub.py and
wrist_roll.py. Servo dimensions are DATASHEET (lib/servo.py) and WHICH servo
is lib/joints.JOINT_SERVO - the tab plane is the datum, the case pocket is
only clearance.

A NOTE ON ONE WORD, so that it is not innocently put back. This docstring
avoids the word tests/test_fusion_scripts.py scans docstrings for - the
one naming a script that places an imported mesh or a measured transform.
That word is a SELF-DECLARATION: a file carrying it is read as holding
measured data, and the magic-number and entity-naming lints are then
SKIPPED for the whole file, silently and with a green run to show for it.
This is an ordinary part script and wants both lints. It carried the word
once, describing tool clearance for a screw, and went unlinted for months.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core
import adsk.fusion

from lib.bearings import B608ZZ  # noqa: E402 - the idler runs in one
from lib.design_rules import FASTENER_MM as _FASTENERS  # noqa: E402
from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402 - the J4 running gap
from lib.forearm_split import Seam, Seat, ServoBlock  # noqa: E402
import lib.facets as F  # noqa: E402 - _style.md rule 6, 12-gon round forms
from lib.forearm_split import Silhouette, Straddle  # noqa: E402
from lib.gears import J3_MOUNT, J3_PAIR  # noqa: E402 - the elbow reduction
from lib.joints import j3_standoff as _j3_standoff  # noqa: E402
from lib.joints import servo_for as _servo_for  # noqa: E402
from lib.joints import servo_name_for as _servo_name_for  # noqa: E402

COMPONENT = 'robotarm_forearm'
BODY_NAME = 'forearm'
PREFIX = 'fa_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'link form'
PH_CLEAR = 'joint clearance'
PH_PIVOT = 'pivot journals'
PH_DRIVE = 'servo lobes'
PH_ELBOW = 'elbow drive clearance'
PH_CABLE = 'cable route'
PH_SEAM = 'plate/rail seam'
PH_FINISH = 'finish'

# Probe hook: _probe_forearm_facet.py sets this False to build the plain body
# and then try chamfer sizes against it. Nothing else touches it.
FACET = True
# Same hook for the lobe-corner fillet. The J3 lobe's INBOARD corners are cut
# away by the gear and pinion clearance cylinders now, so which corners still
# exist is a question to probe, not to assume.
LOBE_FILLET = True
PHASES = [PH_FORM, PH_CLEAR, PH_PIVOT, PH_ELBOW, PH_DRIVE, PH_CABLE,
          PH_SEAM, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# FLOAT SLACK, AND IT IS NOT A DIMENSION. Every number inside run() is a
# dimension and belongs in a user parameter where the Fusion UI can reach
# it; these two are the tolerance on a float COMPARISON, not on the part,
# so they live up here where they read as what they are.
EPS = 1e-9                 # against internal (cm) values
EPS_MM = 1e-6              # against values already scaled to mm for a message
# THE PRECISION A DERIVED STATION IS WRITTEN TO, in mm. Not a dimension and
# not a tolerance on the part: it is one unit in the last place of the
# '%.5f mm' every solved station in this file is written with.
#
# WHY IT HAS TO EXIST. Several stations here are solved to land EXACTLY on a
# limit - fa_cap_screw_y is placed at precisely `_sep` from the servo's own
# tab pilot, because the smallest block that can carry the screw is the one
# that wants no more than that. Writing it to five decimals then rounds it,
# and rounding is signed: it can land a few 1e-7 mm the WRONG side of the
# limit it was solved to sit on. Checking that against EPS (1e-8 mm) is not
# checking the design, it is checking the printf.
#
# IT IS NOT A FUDGE AND THE DIFFERENCE MATTERS. Anything that fails by more
# than this is a real interference; anything that fails by less is the
# parameter table's own write precision. The MG90S rounded UP on this station
# and passed; the SG90 rounds DOWN by 4.1e-7 mm and did not - the design is
# identical either way, and a check that a servo swap can flip by changing
# the fifth decimal place is measuring nothing. fa_cap_margin exists for the
# same reason and says so in its own comment; this is that argument applied
# to a station that has no margin to spend.
PARAM_ROUND_MM = 1e-5
# The floor on what is left of the fork plate outboard of the 608ZZ pocket.
# ASSUMED, and it is BELOW design_rules MIN_FEATURE_MM 0.8 - it is one
# nozzle width, and it is what a 7.50 plate can spare against a 7.00 mm
# bearing. It is deliberately not a user parameter: it drives no geometry,
# it only tells the assert below what "too thin" means.
MIN_SHOULDER_MM = 0.4
# How many stations along a servo seat are checked against the link
# silhouette. A COUNT, not a dimension - it belongs up here with EPS rather
# than in a user parameter, because nothing in the Fusion UI should be able
# to make the check coarser. The seat's -Y end runs along the concave waist
# arc, whose half height is smallest in the MIDDLE of the span, so checking
# only the two ends would pass a seat that breaks out between them.
SEAT_PROBE_N = 100
# _style.md rule 5: two-tone by PART. A link is light; the joints are dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
from lib.servo import SERVO_CASE_CLEARANCE_MM  # noqa: E402
APPEARANCE_HINTS = hints_for('forearm')


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def wrist(name, expr, comment='', units='mm'):
        _set(WRIST + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    def sval(name):
        return ups.itemByName(STYLE + name).value

    # --- SHARED joint contract ----------------------------------------------
    wrist('pivot_af', '16.0 mm',
          'J4 hex socket across flats - SHARED, defined identically in\n'
          '           wrist_roll.py and wrist_hub.py')
    wrist('straddle', '24.0 mm',
          'the width this fork straddles - SHARED, see wrist_roll.py')
    wrist('sweep_r', '25.4 mm',
          'the radius the roll housing sweeps about J4 - SHARED, see wrist_roll.py')
    wrist('hub_d', '20.0 mm', 'hub journal collar diameter - SHARED, see wrist_hub.py')
    wrist('journal', '5.0 mm', 'collar length = the bore depth it runs in')
    wrist('flange_d', '24.0 mm', 'hub retaining flange diameter')
    wrist('flange_t', '2.0 mm', 'hub retaining flange thickness')
    wrist('reach', '3.8 mm', 'hex boss length past this plate - SHARED, see wrist_hub.py')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'silhouette corner radius - _style.md rule 2')

    # --- fits ----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('srv_clear', '%.2f mm' % SERVO_CASE_CLEARANCE_MM,
          'SERVO CASE WINDOW CLEARANCE - lib/servo.py, NOT `loc`.\n'
          '           The window was cut at loc 0.2 TOTAL (0.10 per side) around a\n'
          '           DATASHEET case dimension. GATE servo_fit measured the servo\n'
          '           solid against this host and found real interference; the fix\n'
          '           costs nothing because the TABS locate the servo, not the case.')
    param('rot', '0.35 mm', 'rotating fit - design_rules, every journal here')
    param('free', '0.4 mm', 'free fit - design_rules')

    # --- link ----------------------------------------------------------------
    param('l2', '45.0 mm',
          'J3 to J4. Was 65. Shortened 2026-08-26 to the reference arm\'s\n'
          '           proportions. This is the single highest-leverage number in the\n'
          '           arm: the whole outboard cluster - wrist, both wrist servos, the\n'
          '           effector servo and the head - sits at FIXED offsets from the\n'
          '           wrist end, so shortening L2 translates all of it inboard 1:1.\n'
          '           The head alone is 49 % of the elbow moment. 65 -> 45 takes J3\n'
          '           from 80 % to 61 % of duty. lib/arm_budget.py is the authority.\n'
          '           Cost: working reach 300 -> 260 mm at the jaw faces.')
    param('gap', PREFIX + 'free', 'running gap, plate inner face to the straddled part')
    param('plate_in', WRIST + 'straddle / 2 + ' + PREFIX + 'gap', 'derived plate inner face')
    param('cbore_extra', '0.5 mm',
          'the counterbore is deeper than the flange so the flange NEVER seats: the\n'
          '           hex bottoming in its socket is what locates the joint axially, and\n'
          '           two hard stops on one axis fight each other')
    param('cbore_depth', WRIST + 'flange_t + ' + PREFIX + 'cbore_extra', 'derived')
    param('plate_t', WRIST + 'journal + ' + PREFIX + 'cbore_depth', 'derived plate thickness')
    param('plate_out', PREFIX + 'plate_in + ' + PREFIX + 'plate_t', 'derived plate outer face')
    param('bore_d', WRIST + 'hub_d + ' + PREFIX + 'rot', 'derived journal bore')
    param('cbore_d', WRIST + 'flange_d + ' + PREFIX + 'rot', 'derived flange counterbore')
    param('boss_r', PREFIX + 'cbore_d / 2 + ' + PREFIX + 'wall', 'derived pivot boss radius')
    param('facet', '1.0 mm',
          'LOCAL, not sty_facet - _style.md rule 1 says the facet scales with\n'
          '           the volume it bevels, and these are 7.5 mm fork plates, not the\n'
          '           upper arm\'s 24 mm slab. A 4.0 shared facet on a 7.5 plate is not\n'
          '           a facet, it is most of the plate. And redefining sty_facet to\n'
          '           suit this part would silently re-cut every other part in the\n'
          '           document - that is the exact bug _check_ledger.py exists for.\n'
          '           A PROBED CEILING, not a preference, and the ceiling MOVED when\n'
          '           the J3 reduction landed. It was plate_t/5 = 1.50: measured\n'
          '           against the built body, 2.50 and 2.00 failed ASM_BL_UNFIN_SHEET\n'
          '           because the silhouette arc runs tangentially into the boss\n'
          '           circles and has nowhere to run out, and 1.50 was the largest\n'
          '           that computed. The J3 servo standoff now blends into the -X\n'
          '           plate face as well, and on THAT face 1.50 and 1.25 both fail\n'
          '           ASM_INCONS_FACE; 1.00 computes on both. Held as ONE number\n'
          '           rather than one per face: the two faces bevel the same plate,\n'
          '           and a part chamfered 1.50 on one side and 1.00 on the other\n'
          '           reads as a bug. Do not raise it without re-probing BOTH faces.')
    param('waist_t', '3.5 mm',
          'wall thickness between the two pivot bosses. The bosses need 7.5 for the\n'
          '           journal + counterbore; the span between them does not, and this is\n'
          '           the single biggest lever on the mass of the part.')
    param('waist_z', '12.0 mm',
          'half height of the link at its narrowest. THIS is the input; the arc\n'
          '           radius that delivers it is derived from it and from fa_l2. Setting\n'
          '           the radius directly worked at L2 = 40 and pinched the link shut at\n'
          '           L2 = 65 - the shape has to follow the length, not fight it.\n'
          '           Was 9.0. Grown to 12.0 with fa_rail_z held, so the duct grows too:\n'
          '           a 28 mm box beam, not a 28 mm slab. arm_budget says up to 4x the\n'
          '           link mass is affordable at L2 = 45; this spends far less than that.')
    param('elbow_clear', '13.4 mm',
          'the radius the UPPER ARM sweeps about J3, plus clearance. Its elbow block\n'
          '           has to hold a 16.0 af hex socket, so 9.24 circumradius + 1.6 wall\n'
          '           + 0.4 = 11.4, but ua_drum_r drives it and that is now 13.0,\n'
          '           so 13.4. The centreline web pays for it: 45 - 25.4 - 13.4 = 6.2. If that block grows, this grows, and the web between\n'
          '           the two joints is what gets eaten.')
    # fa_rail_z AND fa_duct_z ARE NO LONGER TYPED HERE. They stopped being
    # free the moment the rails became a separate printed piece bolted to
    # both plates: the rail now has to be tall enough to hold the seam
    # fastener, and the duct is whatever is left of the link once that
    # fastener has taken its room. Both are solved in the SEAM block below,
    # after the fixing sizes they depend on exist. lib/forearm_split.Seam.

    # --- THE WRIST SERVO, DERIVED. lib/joints.JOINT_SERVO -> lib/servo.py ---
    # SIX OF THESE SEVEN WERE TYPED LITERALS AND ALL SIX WERE WRONG THE MOMENT
    # THE SERVO CHANGED. `param('case_l', '22.8 mm', 'MG90S case length ...')`
    # is a copy of a number lib/servo.py already holds, with a comment naming
    # the file it was copied from - and on 2026-09-03 J3 and J4 went MG90S ->
    # SG90 (Jonathan: "both the motors will be sg90"). Every one of these
    # moves, and every one of them feeds a cut: the case window, the flange
    # recess, the tab pilots, the lobe height and fa_lobe_t itself.
    #
    # ONE SET OF PARAMETERS FOR BOTH LOBES, and that is only legitimate
    # because J3 and J4 are the SAME servo. lib/joints asserts that where it
    # is decided; this file asserts it again where it is USED, because the day
    # they diverge this block silently cuts the J4 envelope for the J3 lobe.
    _J34 = _servo_for('J4')
    assert _servo_name_for('J3') == _servo_name_for('J4'), (
        'this file declares ONE case/tab block and cuts BOTH lobes from it, '
        'but J3 is a %s and J4 is a %s - the J3 lobe would be cut to the J4 '
        'servo. Split fa_case_* per lobe before splitting the servos.'
        % (_servo_name_for('J3'), _servo_name_for('J4')))
    param('case_l', '%.4f mm' % _J34.case_l,
          'servo case length - lies along Y. lib/servo.py, for whatever\n'
          '           lib/joints.JOINT_SERVO puts on J3 and J4 (SG90 today, %.2f;\n'
          '           MG90S until 2026-09-03, 22.80 - itself a 24.0 -> 22.8\n'
          '           correction on TowerPro B in the 2026-08-27 flange audit)'
          % _J34.case_l)
    param('case_w', '%.4f mm' % _J34.case_w,
          'servo case width - lies along Z. lib/servo.py. SG90 %.2f against\n'
          '           the MG90S 12.40 it replaces, so fa_lobe_z comes down 0.10 and\n'
          '           every Z-derived wall on the lobe moves with it.' % _J34.case_w)
    param('shaft_end', '%.4f mm' % _J34.shaft_from_end,
          'shaft axis to the NEAR end of the case, along Y - lib/servo.py\n'
          '           shaft_from_end. It is also where the lead bundle leaves, so the\n'
          '           keyway station is this and not the far end. SG90 %.2f, MG90S\n'
          '           6.00.' % _J34.shaft_from_end)
    param('tab_thk', '%.4f mm' % _J34.tab_thk,
          'servo tab thickness - lib/servo.py. It is the depth of the FLANGE\n'
          '           RECESS and part of the fa_lobe_t datum stack. Both micro values\n'
          '           are weak: the MG90S 2.50 is ASSUMED (the TowerPro table does not\n'
          '           give it) and the SG90 %.2f is drawing-stated. CALIPER.'
          % _J34.tab_thk)
    param('tab_below_top', '%.4f mm' % _J34.tab_below_top,
          'case top to the tab TOP, along X - lib/servo.py. THE NUMBER THE\n'
          '           SERVO SWAP MOVES MOST: MG90S 3.00 (DERIVED from TowerPro F 18.5)\n'
          '           against SG90 %.2f (= TowerPro F 17.0, exact). +1.30 straight\n'
          '           into fa_lobe_t, so the J4 lobe and the J3 cap both get thicker\n'
          '           by it - and fa_j3_standoff does NOT, because the pinion seat\n'
          '           rises by the same amount. See fa_j3_standoff.' % _J34.tab_below_top)
    param('tab_pitch', '%.4f mm' % _J34.tab_hole_pitch,
          'servo tab hole pitch - lib/servo.py. SG90 %.2f is DRAWING-STATED\n'
          '           (SG90_Model_A, and holes 2.3 in from each tip of a 32.3 span\n'
          '           gives 27.7 - agreement to 0.1). The MG90S 27.50 it replaces was\n'
          '           DERIVED and no drawing stated it, so the swap actually IMPROVES\n'
          '           the provenance of the two pilots this lobe drills. CALIPER\n'
          '           anyway before printing anything that screws to these tabs.'
          % _J34.tab_hole_pitch)
    param('tab_span', '%.4f mm' % _J34.tab_span,
          'servo mounting FLANGE, tip to tip - lib/servo.py, DATASHEET. It is\n'
          '           the dimension this lobe was blind to: %.2f of flange against a\n'
          '           %.2f case, so %.2f of tab hangs past the case at EACH end and\n'
          '           more than that past the case window. A recess cut to it is\n'
          '           charged mm for mm to fa_lobe_pad, so lib/servo.py\'s standing\n'
          '           CALIPER warning on the micro tables bites hardest here.'
          % (_J34.tab_span, _J34.case_l,
             (_J34.tab_span - _J34.case_l) / 2))
    param('lobe_t', PREFIX + 'tab_below_top + ' + PREFIX + 'tab_thk',
          'derived SERVO STACK, TAB PLANE to case top - and read the next\n'
          '           four lines before using it as a bearing face, because it is not\n'
          '           one. It is TWO different things: fa_tab_below_top of bare case,\n'
          '           then fa_tab_thk of FLANGE that runs past the case at EACH end.\n'
          '           6.70 on the SG90 (4.30 + 2.40), 5.50 on the MG90S it replaced\n'
          '           (3.00 + 2.50) - so the J4 lobe and the J3 cap are both 1.20\n'
          '           thicker than they were. NOTHING BEARS ON THE LOBE\'S OUTER\n'
          '           FACE: at that plane the tab UNDERSIDE is level with the face and\n'
          '           the tab BODY is already 2.50 inside it, in what used to be solid\n'
          '           lobe. GATE servo_fit MEASURED that collision - 195.75 mm3 of\n'
          '           MG90S inside this part at x 23.40..24.90, the flange band and\n'
          '           nothing else. The fix is the flange recess cut in phase 4: the\n'
          '           tab TOP beds on its floor and the screw heads land on the\n'
          '           underside, flush with the outer face. specs/robotarm/_flange.md.\n'
          '           Otherwise a servo dimension and nothing else: the J3 cap is\n'
          '           exactly this thick (fa_cap_t) and fa_j3_standoff subtracts it.\n'
          '           The J4 LOBE is fa_j4_lobe_t, this plus a running gap - see there.')
    # ---- THE J4 RUNNING GAP, AND WHY THE LOBE GOT 0.40 THICKER -------------
    # wrist_hub.py no longer bores onto a horn; it bores onto the servo's
    # spline, and lib/servo_hub seats every spline hub ONE RUNNING GAP above
    # the case top. wh_seat_z therefore moves 5.50 -> 5.90 on the MG90S, and
    # to 7.10 on the SG90 that replaced it (fa_lobe_t 6.70 + this gap).
    #
    # THE HORN-ERA STACK WAS RUBBING BY CONSTRUCTION. lobe_t 5.50 put the
    # case top EXACTLY on this plate's outer face, and the hub's seating
    # face flat on the case top with ZERO gap - while the hub ROTATES
    # against that case. Nothing was clearance; the joint was a brake.
    #
    # WHAT MOVES, AND WHAT DELIBERATELY DOES NOT. The tab PLANE goes
    # 0.40 further OUT, so the case top lands 0.40 outboard of fa_plate_out
    # and the hub's seating face lands back ON fa_plate_out where it has
    # always been. That is the point of standing the servo off rather than
    # letting the hub move: the pivot journal, wr_reach, the hex socket and
    # the whole roll housing downstream of it do not move at all. The cost
    # is 0.40 mm of arm width, once, on the +X side.
    #
    # J3 IS UNTOUCHED BY THIS, and that is why it is a separate parameter
    # instead of 0.40 added to lobe_t. fa_cap_t is lobe_t and fa_j3_standoff
    # subtracts lobe_t, so widening lobe_t would have thickened
    # j3_servo_cap's pad and shortened this part's standoff web to
    # compensate - a change to another part's contract, to buy a gap J3
    # already has (J3_HUB.seat_z carries its own case_gap).
    param('j4_standoff', '%.4f mm' % _FIT['free'],
          'running gap between the servo case top and wrist_hub\'s seating\n'
          '           face. design_rules JOINT_FIT_MM free - the same number\n'
          '           lib/servo_hub.spline_hub() seats on and wh_case_gap declares.\n'
          '           The hub ROTATES against that case, so the horn-era 0.00 was\n'
          '           rubbing by construction.')
    param('j4_lobe_t', PREFIX + 'lobe_t + ' + PREFIX + 'j4_standoff',
          'derived J4 lobe thickness, plate outer face to the TAB PLANE -\n'
          '           the servo datum, not a bearing face; what bears is the flange\n'
          '           recess floor fa_tab_thk inside it. = wh_seat_z 5.90. The servo\n'
          '           case travels the whole of it\n'
          '           during assembly, so the two cuts of phase 4 - case window\n'
          '           then flange recess - span all of it between them and not just\n'
          '           the lobe_t part: a 0.40 skin over the case top would make the\n'
          '           servo uninstallable and the shaft unreachable.')
    param('lobe_over', '1.0 mm',
          'the lobe starts INSIDE the plate. Two volumes that meet exactly on a plane\n'
          '           are non-manifold and the fillet fails later - see PLAYBOOK.')
    param('lobe_z', PREFIX + 'case_w / 2 + ' + PREFIX + 'wall + 1.0 mm', 'derived lobe half height')
    # ---- THE SEAT UNDER EACH SERVO BLOCK ---------------------------------
    # THE PLATE IS ONLY fa_plate_t WHERE THE BOSSES ARE. Everywhere else it
    # is fa_waist_t, and fa_waist_t is the single biggest lever on the mass
    # of this part, so it is not going up. But both servo blocks are drawn to
    # land on a full-thickness plate: they start one fa_lobe_over inside
    # fa_plate_out, and the waist stops at fa_plate_in + fa_waist_t. Between
    # those two faces there is 3.00 mm of nothing, and every part of a block
    # that reaches past its own boss circle was bridging it in mid air - on
    # +X, 184.5 mm2 of the J4 lobe's underside, 49.6 mm up the print, under
    # the servo the bench complaint names.
    #
    # DERIVED, NOT TYPED, and that is the point: 3.00 is the gap between the
    # two faces that make it, so writing it as those faces means it tracks
    # fa_plate_t and fa_waist_t instead of going stale the next time either
    # moves. The extra fa_lobe_over is the same trick the blocks already use.
    param('lobe_seat', PREFIX + 'plate_t - ' + PREFIX + 'waist_t + '
          + PREFIX + 'lobe_over',
          'derived seat depth, measured IN from the plate outer face: the\n'
          '           full plate, less the waist that is already there, plus one\n'
          '           fa_lobe_over so the seat OVERLAPS the web at one end and the\n'
          '           servo block at the other rather than meeting either on a bare\n'
          '           plane - which is non-manifold and fails the fillet later, the\n'
          '           reason fa_lobe_over exists at all. 5.00, of which 3.00 is the\n'
          '           air the blocks were standing on.')
    param('seat_z', PREFIX + 'lobe_z - ' + PREFIX + 'wall',
          'derived seat half height, one fa_wall inside fa_lobe_z, and the\n'
          '           inset is not styling. At fa_lobe_z the seat would be coplanar\n'
          '           with the lobe\'s own top and bottom faces, which would EXTEND\n'
          '           the four corner edges phase 6 fillets - off the lobe, down the\n'
          '           seat, and out onto the web\'s CURVED silhouette face, where a\n'
          '           round-over has nowhere to run out. That is the exact failure\n'
          '           fa_facet was cut to 1.00 for and fa_lobe_radius_j3 to 4.5. One\n'
          '           wall in, the seat touches no edge the fillet needs and every\n'
          '           probed radius above stays valid. The ledge it leaves is fa_wall\n'
          '           wide, which bridges without support.')
    # THE SEAT IS SOLVED IN lib/forearm_split, NOT HERE. Both printed side
    # plates carry one and both have to arrive at the same answer; the two
    # expressions above are the Fusion-facing form of that solve, and the
    # asserts below are what stops the two forms drifting apart. It is the
    # same discipline lib/gears.py imposes on the elbow.
    _SEAT = Seat(plate_t=val('plate_t') * 10, waist_t=val('waist_t') * 10,
                 lobe_over=val('lobe_over') * 10, lobe_z=val('lobe_z') * 10,
                 wall=val('wall') * 10, boss_r=val('boss_r') * 10)
    _bad = _SEAT.validate()
    assert not _bad, 'the servo seat does not fit: ' + '; '.join(_bad)
    assert abs(val('lobe_seat') * 10 - _SEAT.depth) < EPS_MM, (
        'fa_lobe_seat is %.4f and lib/forearm_split solves %.4f'
        % (val('lobe_seat') * 10, _SEAT.depth))
    assert abs(val('seat_z') * 10 - _SEAT.half_z) < EPS_MM, (
        'fa_seat_z is %.4f and lib/forearm_split solves %.4f'
        % (val('seat_z') * 10, _SEAT.half_z))
    # AND IT IS DERIVED FROM fa_lobe_z, NOT fa_seat_z, WHICH IS NOT AN
    # OVERSIGHT. The y where the boss circle falls to fa_seat_z is the LAST
    # y the seat fits at - a tangency with zero margin - and this parameter
    # is written to 5 decimal places, so it rounds. It rounded UP, by
    # 4.5e-6 mm, which puts the seat's own corner 7.4e-6 mm OUTSIDE the
    # circle it came from and fails the silhouette probe against an EPS of
    # 1e-8 mm. Stopping where the boss can still carry a FULL lobe height
    # leaves exactly fa_wall of margin, by construction, at every y the seat
    # reaches, and no rounding of any precision can eat it. Cost: 1.15 mm of
    # seat at the wrist end of J4, which is its small end.
    param('seat_y_max', '%.5f mm' % _SEAT.y_max,
          'derived +Y limit for a seat: the y at which the boss circle falls\n'
          '           to fa_lobe_z. Past it the plate outline drops below the block,\n'
          '           and a seat drawn to the block\'s full length would stand proud\n'
          '           of the part\'s own silhouette at the wrist end - giving the\n'
          '           phase-6 facet a second outline to chase. It leaves fa_wall of\n'
          '           silhouette above fa_seat_z wherever the seat reaches, which is\n'
          '           the margin that makes the probe in phase 1 robust to rounding.\n'
          '           Binds on J4 (block reaches 12.50, seat stops at 10.60); slack\n'
          '           on J3 (block 9.60, so the block\'s own end governs).')
    param('win_z', PREFIX + 'case_w + ' + PREFIX + 'srv_clear',
          'derived height of BOTH the case window and the flange recess, and\n'
          '           they are ONE number on purpose. The case passes through both\n'
          '           bands on its way in, so the recess cannot be the tighter of the\n'
          '           two without becoming the fit the window was widened to stop\n'
          '           being - and two rectangles 0.25 apart in Z would leave a ledge\n'
          '           overhanging the pocket for no gain.')
    param('recess_l', PREFIX + 'tab_span + ' + PREFIX + 'srv_clear / 2',
          'derived FLANGE RECESS length. HALF the case window clearance, and\n'
          '           the asymmetry is the point. The window is cut at fa_srv_clear\n'
          '           because the case is the untrusted dimension and a fat case costs\n'
          '           nothing there. Along Y it is not free: every 0.1 here comes\n'
          '           straight out of the recess END WALL, which fa_wall then charges\n'
          '           back to fa_lobe_pad and so to the length of the arm. 0.25 a side\n'
          '           clears a flange that is flat, stamped and located by its own two\n'
          '           screws in any case.')
    param('lobe_pad', PREFIX + 'recess_l / 2 - ' + PREFIX + 'tab_pitch / 2 + '
          + PREFIX + 'wall',
          'material past the outermost tab screw. NO LONGER THE ROUND 3.50 it\n'
          '           was: the flange recess reaches fa_recess_l/2 = 16.30 from the\n'
          '           case mid and the outer screw sits at fa_tab_pitch/2 = 13.75, so\n'
          '           a 3.50 pad left 0.95 of end wall and the recess BROKE OUT of\n'
          '           both ends of the lobe. This is that floor written down: half the\n'
          '           recess, back to the screw, plus one fa_wall. 4.15, DERIVED, and\n'
          '           it costs 0.65 mm of lobe at each end in Y. J3 reads it too\n'
          '           (j3_servo_cap sizes its pad from fa_lobe_pad), which is right -\n'
          '           the cap carries the same flange and needs the same room.')
    param('lobe_radius_j3', '4.5 mm',
          'LOCAL, not sty_radius - and for the same reason fa_facet is local.\n'
          '           The J3 lobe stopped being a pad on the plate when the reduction\n'
          '           pushed it out on a standoff: its corner edge now runs 16.10 mm\n'
          '           from inside the plate, through the gear clearance cut, to the\n'
          '           servo face, and the faces either side of it change along the way.\n'
          '           J4\'s 6.0 will not compute on it. PROBED against the built body:\n'
          '           6.0 fails ASM_INCONS_FACE, 5.5 and 5.0 fail ASM_BL_CAP_COMPLEX,\n'
          '           4.5 computes. A CEILING, not a preference. Do not raise it\n'
          '           without re-probing.')
    param('lobe_radius_j4', '%.5f mm'
          % (min(sval('radius'), val('lobe_z') - val('win_z') / 2) * 10),
          'LOCAL, not sty_radius - and like fa_lobe_radius_j3 it is a CEILING,\n'
          '           not a preference. The flange recess set it. A corner fillet\n'
          '           reaches its own radius in from BOTH faces of the corner it\n'
          '           rounds, and the recess corner sits only fa_wall inside the end\n'
          '           face and fa_lobe_z - fa_win_z/2 inside the top: at sty_radius\n'
          '           6.0 the rounded face passed 0.28 mm from the pocket, which is\n'
          '           not a wall, it is a slot the slicer would drop. The largest\n'
          '           radius that leaves the corner as thick as the flat end wall is\n'
          '           exactly fa_lobe_z - fa_win_z/2, so that is what this is, capped\n'
          '           at sty_radius for the day the recess shrinks. Asserted below.\n'
          '           A SMALLER radius also means the length filter in phase 6 now\n'
          '           accepts the two ELBOW-end corners it used to reject as too\n'
          '           short - J4 fillets 4 edges now, not 2.')
    # ---- LEAD KEYWAY -------------------------------------------------------
    # The servo cannot be installed without this. The whole case travels
    # through this window during assembly (the tabs land on the FAR face), so
    # the cable has to traverse it too - and the bundle leaves the SHORT END
    # FACE at the shaft end, dead centre across the width (lib/servo.py lead
    # datum, MEASURED 2026-08-28). Along the length the servo-plus-cable is
    # case_l + bundle = 26.2 against a 23.0 window: it does not go.
    #
    # The first repair notched the two LONG walls either side of that face -
    # right station, wrong walls, and it would have printed. Jonathan, at the
    # bench: "thats not on the right side its on the short side". ONE notch,
    # centred, in the END wall.
    _LEAD = _J34.lead_bundle_dia
    param('lead_key_d', '%.2f mm' % (_LEAD + val('loc') * 10),
          'keyway WIDTH across the case width, centred on the bundle - one\n'
          '           bundle diameter plus a locational fit')
    param('lead_key_l', '%slobe_pad + (%stab_pitch - %scase_l) / 2 + 1.0 mm'
          % (PREFIX, PREFIX, PREFIX),
          'keyway length OUT from the shaft-end face. DERIVED to reach the\n'
          '           lobe edge plus 1.0 of overshoot: a keyway that stops inside the\n'
          '           lobe is a blind pocket and traps the cable exactly as the solid\n'
          '           wall did. Never hardcode this - it moves with lobe_pad.')
    param('pilot_d', '1.8 mm', 'servo screw pilot - design_rules, self-tapping into PETG')
    param('pilot_depth', '3.0 mm',
          'engagement, and 3.50 is no longer available. The pilots are drilled\n'
          '           from the FLANGE RECESS FLOOR now, not from the lobe\'s outer\n'
          '           face, so what they have to work in is fa_j4_lobe_t - fa_tab_thk\n'
          '           = 3.40 of lobe before fa_plate_out and the J4 flange counterbore\n'
          '           behind it - and the outer pilot sits 8.35 from the J4 axis,\n'
          '           well inside that counterbore\'s r 12.175. 3.00 leaves 0.40 of\n'
          '           floor. Cost: 0.50 mm of self-tap engagement on a screw that has\n'
          '           3.00. Asserted below, against the number that actually binds.')
    # --- THE GEARED ELBOW ---------------------------------------------------
    # Every number here is READ, not chosen. The handoff priced this drive at
    # "~7 mm of forearm width" and it was never a free parameter - see
    # lib/gears.py J3_MOUNT, which solves it from the servo stack (whichever
    # servo lib/joints.JOINT_SERVO puts on J3) and the pair's face width, and
    # specs/robotarm/_HANDOFF.md section 9.
    _P, _M, _B = J3_PAIR, J3_MOUNT, B608ZZ
    param('j3_centre', '%.5f mm' % _P.centre_distance,
          'lib/gears.py J3_PAIR - do not edit here. The J3 servo shaft sits\n'
          '           this far from the elbow, TOWARD THE WRIST, and j3_gear and\n'
          '           j3_pinion cut their teeth from the same object.')
    param('j3_band', PREFIX + 'free + %.5f mm + ' % _P.face + PREFIX + 'free',
          'derived: the axial band the 36T gear turns in, out from the plate\n'
          '           outer face - a running gap, the face width, another gap')
    param('j3_gear_clear', '%.5f mm + ' % _P.r_tip(_P.z_gear) + PREFIX + 'free',
          'derived: the radius the 36T sweeps about J3, plus clearance.\n'
          '           NOTHING may stand inside this between the plate outer face and\n'
          '           the servo lobe.')
    param('j3_pin_clear', '%.5f mm + ' % _P.r_tip(_P.z_pinion) + PREFIX + 'free',
          'derived: the same for the 18T about the SERVO axis. This one is the\n'
          '           surprise - it is r %.2f and the lobe is only %.2f tall, so it\n'
          '           cuts the standoff clean through and the lobe hangs off the J4\n'
          '           end on a web. Priced in _HANDOFF.md section 9: 71x on\n'
          '           interlayer shear, 1.6 %%%% of backlash in lost motion.'
          % (_P.r_tip(_P.z_pinion) + val('free') * 10, val('lobe_z') * 10))
    param('j3_standoff',
          PREFIX + 'free + %.5f mm + %.5f mm - ' % (_P.face, _M.seat_z) + PREFIX + 'lobe_t',
          'derived, and the whole cost of this drive: how far the J3 servo pad\n'
          '           stands off the plate so the pinion lands coplanar with the gear.\n'
          '           free + face + J3_MOUNT.seat_z - lobe_t. Boring the pinion\n'
          '           through instead of blind-pocketing it is what makes seat_z %.2f\n'
          '           rather than the %.2f a blind pocket would need (the seat would\n'
          '           land on the output BOSS top), and that is %.2f mm of arm width.\n'
          '           THE SERVO SWAP DOES NOT MOVE THIS PARAMETER. seat_z is the case\n'
          '           top plus a running gap and fa_lobe_t IS the case top, so the two\n'
          '           cancel and this is free + face + case_gap for any micro servo in\n'
          '           the catalogue: 10.80 on the MG90S, 10.80 on the SG90. The\n'
          '           standoff web, fa_cap_pilot_depth and fa_j3_band are all\n'
          '           untouched by the change. Asserted against lib/joints below.'
          % (_M.seat_z, val('lobe_t') * 10 + _J34.boss_h, _J34.boss_h))

    # --- 608ZZ at the idler side, in place of a flange counterbore ----------
    # A gear mesh loads this axis RADIALLY and slop at the elbow is backlash
    # at the tooth, which is the one thing a 2:1 cannot fix. j3_axle.py has
    # the argument. Its inner race is the datum read from BOTH ends:
    # j3_axle's collar must land INSIDE it, this shoulder OUTSIDE it, and
    # _check_elbow.py asserts both.
    param('brg_od', '%.4f mm' % _B.od, 'lib/bearings.py B608ZZ - do not edit here')
    param('brg_w', '%.4f mm' % _B.width, 'lib/bearings.py B608ZZ')
    param('brg_press', '0.02 mm',
          'interference on the OUTER race. ASSUMED - it is j3_axle\'s number for\n'
          '           the inner race applied to the other one, and a housing fit is not\n'
          '           a shaft fit. GAUGE IT before printing a second one.')
    param('brg_pocket_d', PREFIX + 'brg_od - ' + PREFIX + 'brg_press', 'derived')
    param('brg_bore', '%.4f mm' % (_B.inner_race_od + 1.0),
          'the retaining shoulder\'s bore. DERIVED from B608ZZ.inner_race_od,\n'
          '           not typed: this plate does not turn, so its shoulder must bear\n'
          '           OUTSIDE the inner race or it rubs it and locks the joint.')
    param('brg_shoulder', PREFIX + 'plate_t - ' + PREFIX + 'brg_w',
          'derived: what is left of the plate outboard of the pocket')

    # --- the bolt-on servo cap ---------------------------------------------
    param('cap_t', PREFIX + 'lobe_t',
          'the cap IS the servo pad, so it is exactly the pad thickness this\n'
          '           file used to carry. j3_servo_cap.py asserts it matches.')
    param('cap_pilot_d', '%.4f mm' % _FASTENERS['M3']['pilot'],
          'M3 self-tapping pilot - lib/design_rules.py FASTENER_MM, the same\n'
          '           table the elbow retention bolt reads.')
    param('cap_head_d', '6.0 mm',
          'M3 socket head. The cap counterbores its screws FLUSH to this and\n'
          '           it has no choice: the servo\'s tab plate lands on that face and\n'
          '           spans them. So the head, not the shank, is what sets how far\n'
          '           this standoff has to reach - sized on the shank first and the\n'
          '           counterbore came out 0.72 mm from the edge.')
    param('cap_margin', '0.1 mm',
          'slack on a derived reach, and it is declared HERE rather than down\n'
          '           beside fa_cap_reach where it used to live, because the SEAM\n'
          '           block below reads it and that block runs first. On a rebuild the\n'
          '           parameter already existed from the previous run and the late\n'
          '           declaration worked; on a FIRST build in a clean document it did\n'
          '           not exist yet. That is the whole class of bug an idempotent\n'
          '           script hides from itself.\n'
          '           What it buys: without it a derived edge lands EXACTLY on the\n'
          '           minimum wall and every assert downstream sits on a float\n'
          '           comparison it can fail either side of. 0.1 costs nothing and\n'
          '           means the checks are measuring the design, not the arithmetic.\n'
          '           fa_cap_reach spends it on the block edge; fa_seam_z spends it\n'
          '           keeping the screw head inside the link outline.')
    param('cap_pilot_depth', '8.0 mm',
          'engagement into the standoff web, which is fa_j3_standoff - %.2f\n'
          '           deep today. What the pilot leaves of that floor is asserted\n'
          '           against fa_wall below, so it cannot go stale unnoticed: this\n'
          '           comment read "9.6 deep" long after the web stopped being 9.6.'
          % (val('j3_standoff') * 10))
    # ---- THE SEAM: WHERE THE PLATES BOLT TO THE RAILS ----------------------
    # This part is printed as three pieces now - forearm_px, forearm_nx and
    # two copies of forearm_rail - and this block is the joint between them.
    # specs/robotarm/_forearm_print.md carries the measurement that forced
    # it; the short version is that a side plate is a horizontal slab when it
    # is built along X, a slab prints perfectly as the FIRST layer and
    # impossibly otherwise, and nothing that reaches across the straddle can
    # belong to a plate that starts at its own inner face.
    #
    # NOTHING HERE IS CHOSEN. lib/forearm_split.Seam solves the whole joint
    # from four things that each bind: the screw HEAD has to stay inside the
    # link outline (it lands on the waist's outer face, in free air where
    # nothing sweeps); the PILOT has to stay inside the rail with a wall of
    # floor under it; the rail's LENGTH at that height comes from the two
    # sweep circles; and the walls between and either side of the two screws
    # have to be one fa_wall each. Solve those and fa_duct_z falls out - it
    # is no longer the 9.0 that used to be typed above.
    _SEAM = Seam(silhouette=Silhouette(l2=val('l2') * 10,
                                       boss_r=val('boss_r') * 10,
                                       waist_z=val('waist_z') * 10),
                 straddle=Straddle(l2=val('l2') * 10,
                                   sweep_r=wval('sweep_r') * 10,
                                   elbow_clear=val('elbow_clear') * 10),
                 waist_z=val('waist_z') * 10, wall=val('wall') * 10,
                 head_d=val('cap_head_d') * 10,
                 pilot_d=val('cap_pilot_d') * 10,
                 margin=val('cap_margin') * 10)
    _bad = _SEAM.validate()
    assert not _bad, 'the plate/rail seam does not fit: ' + '; '.join(_bad)
    param('seam_z', '%.5f mm' % _SEAM.z,
          'derived seam screw height. As high as a fa_cap_head_d head inside\n'
          '           the link OUTLINE allows, because the pair carries the couple\n'
          '           between plate and rail and wants the longest lever it can get.\n'
          '           Measured against fa_waist_z, which is the outline\'s MINIMUM\n'
          '           half height, so the head is inside at every y and not only at\n'
          '           the two stations - asserted below at both anyway.')
    param('duct_z', '%.5f mm' % _SEAM.duct_z,
          'derived cable duct half height, and it is DERIVED now: the seam\n'
          '           screw axis, less half a pilot, less one fa_wall of rail floor.\n'
          '           6.00 against the 9.00 that used to be typed - the duct gives up\n'
          '           3.00 mm of half height so the rail can hold the fastener that\n'
          '           makes the split possible. What is left is a 24.8 x 12.0 channel,\n'
          '           still several times CABLE_CHANNEL_FACTOR on the fattest bundle\n'
          '           in the arm.')
    param('rail_z', PREFIX + 'waist_z - ' + PREFIX + 'duct_z',
          'derived rail height - what is left of the link above the duct. The\n'
          '           two side walls plus these two rails still make the link a box\n'
          '           beam; the rails are simply their own printed piece now, and at\n'
          '           6.00 rather than 3.00 the beam is stiffer than it was.')
    param('seam_pilot_d', PREFIX + 'cap_pilot_d',
          'the SAME M3 self-tapping pilot j3_servo_cap screws into, read from\n'
          '           the one place design_rules FASTENER_MM reaches this file. A seam\n'
          '           with its own idea of an M3 is the drift lib/forearm_split exists\n'
          '           to stop.')
    param('seam_clear_d', '%.4f mm' % _FASTENERS['M3']['clearance'],
          'M3 free through-hole in the plate - design_rules FASTENER_MM. The\n'
          '           screw is a clearance fit in the PLATE and self-taps in the RAIL,\n'
          '           so the joint pulls the two faces together instead of jacking\n'
          '           them apart on a thread it shares.')
    param('seam_engage', PREFIX + 'cap_pilot_depth',
          'self-tap engagement into the rail end face, the same 8.0 the cap\n'
          '           takes into the standoff web. The rail is fa_plate_in * 2 long, so\n'
          '           two screws entering from opposite ends engage 8.00 each and still\n'
          '           leave 8.80 of untapped bore between them.')
    param('seam_y_a', '%.5f mm' % _SEAM.pilots[0],
          'derived inboard seam screw station. The rail is only as long as the\n'
          '           two sweep circles leave it at fa_seam_z - %.2f mm - and the two\n'
          '           pilots share that with three equal walls of %.2f.'
          % (_SEAM.span[1] - _SEAM.span[0], _SEAM.wall_between))
    param('seam_y_b', '%.5f mm' % _SEAM.pilots[1],
          'derived outboard seam screw station - see fa_seam_y_a.')
    assert _SEAM.head_clearance() >= 0.0, (
        'a seam screw head stands %.3f mm proud of the link outline'
        % -_SEAM.head_clearance())
    assert val('seam_engage') + val('wall') <= val('plate_in'), (
        'a %.1f deep seam pilot entering a rail %.1f long from each end would '
        'meet in the middle' % (val('seam_engage') * 10, val('plate_in') * 2 * 10))
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
    # RENAME FIRST, THEN DELETE. Deleting a component's LAST occurrence orphans
    # the component: it drops straight out of allComponents while still holding
    # its name, so a rename afterwards cannot reach it and the rebuild is handed
    # 'robotarm_x (1)'. Every lookup by name then misses. See fusion/PLAYBOOK.md.
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        # SKIP THE ROOT. Once this part lives in its own saved file the root
        # component carries the DOCUMENT's name, which is COMPONENT - and a
        # root component cannot be renamed, so the rename below raised
        # "3 : root component name cannot be changed" and no part rebuilt.
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
        'component came back as %r - a stale component still holds the name' % comp.name)
    ext = comp.features.extrudeFeatures
    fil = comp.features.filletFeatures
    chf = comp.features.chamferFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                sk.name + ': expected ' + str(expected) + ', got ' + str(sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            # Without this a CUT eats every other component in the document.
            # See fusion/PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm, z_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def yz_circle(name, y_c, z_c, d_cm, x0_expr, dx_expr, op):
        """Cylinder on an axis parallel to X. Every pivot in this part is one."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, y_c, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def yz_polygon(name, y_c, z_c, d_cm, x0_expr, dx_expr, op):
        """A 12-gon boss on an axis parallel to X, its FLATS on the d_cm circle
        (_style.md rule 6) - so a wall measured to that circle still holds."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        ring = F.polygon(y_c, z_c, d_cm / 2, outside=True)
        for k in range(len(ring)):
            u, w = ring[k], ring[(k + 1) % len(ring)]
            sk.sketchCurves.sketchLines.addByTwoPoints(mpt(sk, 0, u[0], u[1]),
                                                       mpt(sk, 0, w[0], w[1]))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def yz_rect(name, y0, y1, z0, z1, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, 0, y0, z0), mpt(sk, 0, y1, z1))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def arc_radius(l, r_end, waist):
        """Radius of the concave arc tangent to both bosses, in cm.

        DELEGATED to lib/forearm_split.Silhouette, and the delegation is the
        point. THREE scripts are now cut from this outline - this assembled
        reference and both printed side plates - and a silhouette that three
        files each solve for themselves is the datum-only-one-file-reads
        failure with the serial numbers filed off. The arithmetic lives in
        one module that can be run from a terminal; this is the cm/mm shim.
        """
        sil = Silhouette(l2=l * 10, boss_r=r_end * 10, waist_z=waist * 10)
        bad = sil.validate()
        assert not bad, 'the link outline is not buildable: ' + '; '.join(bad)
        return sil.arc_r / 10

    def link_profile(name, y_a, y_b, r_end, r_fil, x0_expr, dx_expr, op):
        """The classic connecting-rod outline: a circle at each pivot joined by
        two concave arcs tangent to both. Tangency is what makes it read as one
        shape rather than a strap bolted between two rings, and it is computed,
        not eyeballed - there is no straight edge to get subtly wrong."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        arcs = sk.sketchCurves.sketchArcs
        half = abs(y_b - y_a) / 2.0
        mid_y = (y_a + y_b) / 2.0
        h = math.sqrt((r_fil + r_end) ** 2 - half ** 2)
        waist = h - r_fil
        assert waist > 0, 'fillet radius %.1f pinches the link shut' % (r_fil * 10)

        def tangent(cy, fz):
            dy, dz = mid_y - cy, fz
            n = math.hypot(dy, dz)
            return (cy + r_end * dy / n, r_end * dz / n)

        for sz in (+1, -1):
            fz = sz * h
            ta, tb = tangent(y_a, fz), tangent(y_b, fz)
            arcs.addByThreePoints(mpt(sk, 0, ta[0], ta[1]),
                                  mpt(sk, 0, mid_y, sz * waist),
                                  mpt(sk, 0, tb[0], tb[1]))
        # THE DRUMS ARE 12-GON ARCS (_style.md rule 6, lib/facets), drawn with
        # their FLATS on the boss circle (outside=True): every wall this file
        # measures to fa_boss_r - the counterbore, the 608 pocket - keeps its
        # thickness, and the vertices stand 3.5 % proud of it.
        for cy, other in ((y_a, y_b), (y_b, y_a)):
            up, dn = tangent(cy, h), tangent(cy, -h)
            pts = F.arc_polyline(cy, 0.0, r_end, math.atan2(up[1], up[0] - cy),
                                 math.atan2(dn[1], dn[0] - cy),
                                 0.0 if cy > other else math.pi, outside=True)
            for u, w in zip(pts, pts[1:]):
                sk.sketchCurves.sketchLines.addByTwoPoints(mpt(sk, 0, u[0], u[1]),
                                                           mpt(sk, 0, w[0], w[1]))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name), waist

    def xz_rect(name, x0, x1, z0, z1, y0_expr, dy_expr, op):
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, 0, z0), mpt(sk, x1, 0, z1))
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    def edge_along_x_at(y_c, z_c, min_len=0.0):
        """Edges running along X at one (y, z) corner, at least min_len long.

        The length filter is not tidiness. The J3 lobe's INBOARD corner is now
        SPLIT by the gear clearance cut into a 1.00 stub inside the plate and a
        5.50 stub on the lobe; asking a 4.5 fillet to run along a 1.00 edge is
        the ASM_INCONS_FACE this used to die on.
        """
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            b = e.boundingBox
            if (abs(b.minPoint.y - b.maxPoint.y) < val('tol')
                    and abs(b.minPoint.z - b.maxPoint.z) < val('tol')
                    and abs(b.minPoint.y - y_c) < val('tol')
                    and abs(b.minPoint.z - z_c) < val('tol')
                    and e.length >= min_len - EPS):
                col.add(e)
        return col

    # ---- the two servo lobes, as data ---------------------------------------
    # (sign of X, pivot y, sign of the case's run along Y). Both cases point
    # INBOARD along the arm so their mass sits between the joints, not past
    # them: J4's runs back from the wrist, J3's runs forward from the elbow.
    L2 = val('l2')
    # J3's servo NO LONGER SITS ON THE ELBOW. It drives a 2:1 spur pair, so
    # it sits one centre distance toward the WRIST and one standoff further
    # outboard, with the gear train filling the space between. Both numbers
    # are read from lib/gears.py, not chosen here.
    Y_PIN = -L2 + val('j3_centre')
    LOBES = [(+1, 0.0, -1, 'j4'), (-1, Y_PIN, +1, 'j3')]

    # SO()/so_val() USED TO LIVE HERE and are gone with the cuts that read
    # them: they offset a station by fa_j3_standoff for the J3 lobe, and the
    # only phase that ever asked was the servo window, which left this file
    # with J3's pad. J4 sits on its own plate and needs no offset.

    def block_hi(jnt, hi):
        """How far along +Y the servo block reaches.

        J4 stops at lobe_pad past its outer screw, as it always did. J3
        REACHES TO THE BOSS RADIUS, and that is not styling: the web which
        survives the pinion cut is 9.75 mm of Y, the servo window eats 4.0 of
        it, and a M3 through-hole with two minimum walls wants 6.6 - so there
        is nowhere to put the cap screws otherwise. boss_r is as far as it can
        go without standing proud of the part's own silhouette, which stops
        there anyway.
        """
        return val('cap_reach') if jnt == 'j3' else hi

    def servo_block(y_p, run):
        """lib/forearm_split.ServoBlock for one servo, in mm.

        DELEGATED, and this was the third copy of the arithmetic: here for
        both lobes, again in j3_servo_cap.py for the cap, and forearm_px.py
        would have been a fourth. That is exactly how this project lost
        shaft_from_end and the lead datum - see _HANDOFF section 3.
        """
        blk = ServoBlock(y_pivot=y_p * 10, run=run,
                         shaft_end=val('shaft_end') * 10,
                         case_l=val('case_l') * 10,
                         tab_pitch=val('tab_pitch') * 10,
                         lobe_pad=val('lobe_pad') * 10)
        bad = blk.validate()
        assert not bad, 'the servo block does not place: ' + '; '.join(bad)
        return blk

    def lobe_geometry(y_p, run):
        """Case span, screw positions and lobe outline for one servo, in cm."""
        blk = servo_block(y_p, run)
        c0, c1 = blk.case
        lo, hi = blk.span
        return (c0 / 10, c1 / 10,
                tuple(v / 10 for v in blk.screws), lo / 10, hi / 10)

    # ---- sanity, before any geometry ----------------------------------------
    assert val('boss_r') * 2 < L2, 'the two pivot bosses overlap - L2 is too short'
    web_axis = L2 - wval('sweep_r') - val('elbow_clear')
    assert web_axis >= val('wall'), (
        'the J4 sweep (%.1f) and the J3 sweep (%.1f) leave only %.1f mm of web on the '
        'centreline at L2 = %.1f' % (wval('sweep_r') * 10, val('elbow_clear') * 10,
                                     web_axis * 10, L2 * 10))
    # THE PILOTS, AGAINST THE DEPTH THEY ACTUALLY HAVE. This used to read
    # `pilot_depth <= j4_lobe_t + lobe_over` - 3.50 against 6.90 - which is
    # the whole lobe INCLUDING the 1.00 it spends buried inside the plate,
    # so it could never fire for any pilot that would fit in the part at
    # all. What binds is the material between the recess floor and
    # fa_plate_out, and behind fa_plate_out is the J4 flange counterbore.
    _pilot_have = (val('j4_lobe_t') - val('tab_thk')) * 10
    assert val('pilot_depth') * 10 <= _pilot_have + EPS_MM, (
        'the servo pilots start at the flange recess floor and have %.2f mm '
        'of lobe before fa_plate_out, but fa_pilot_depth is %.2f - they break '
        'through into the J4 flange counterbore (r %.2f, and the outer pilot '
        'is well inside it)'
        % (_pilot_have, val('pilot_depth') * 10, val('cbore_d') * 10 / 2))

    # THE FLANGE RECESS, CHECKED BEFORE IT IS CUT. Three walls, and the
    # third one is the one that is easy to miss: the lobe's own corner
    # fillet reaches in from both faces at once, so the diagonal is thinner
    # than either flat. fa_lobe_radius_j4 is derived to make it exactly
    # fa_wall; this is that derivation stated from the other end, so the
    # two cannot quietly disagree.
    _end_wall = (val('lobe_pad') + val('tab_pitch') / 2 - val('recess_l') / 2) * 10
    assert _end_wall >= val('wall') * 10 - EPS_MM, (
        'the flange recess reaches %.2f from the case mid and the lobe ends '
        'at %.2f - %.2f mm of end wall against a %.2f minimum. It breaks out '
        'of both ends of the lobe: grow fa_lobe_pad, it is derived from '
        'exactly this'
        % (val('recess_l') * 10 / 2,
           (val('lobe_pad') + val('tab_pitch') / 2) * 10,
           _end_wall, val('wall') * 10))
    _side_wall = (val('lobe_z') - val('win_z') / 2) * 10
    assert _side_wall >= val('wall') * 10 - EPS_MM, (
        'the case window and flange recess are %.2f tall in a lobe %.2f tall '
        '- %.2f mm of side wall against a %.2f minimum'
        % (val('win_z') * 10, val('lobe_z') * 2 * 10, _side_wall, val('wall') * 10))
    _rad = val('lobe_radius_j4')
    _corner = (_rad - math.hypot(
        max(val('recess_l') / 2 - (val('lobe_pad') + val('tab_pitch') / 2 - _rad), 0.0),
        max(val('win_z') / 2 - (val('lobe_z') - _rad), 0.0))) * 10
    assert _corner >= val('wall') * 10 - EPS_MM, (
        'the r %.2f corner fillet on the J4 lobe passes %.2f mm from the '
        'flange recess against a %.2f minimum - the two flats are fine and '
        'the DIAGONAL is not, which is what fa_lobe_radius_j4 exists to stop'
        % (_rad * 10, _corner, val('wall') * 10))
    assert wval('reach') > val('gap'), 'the hub hex does not reach across the running gap'
    # The cable leaves the END face, so it steals LENGTH, not width. The
    # superseded form of this assert charged it against case_w and passed
    # happily while the keyway was on the wrong wall entirely.
    _need = _J34.case_l + _J34.lead_bundle_dia
    _have = val('case_l') * 10 + val('loc') * 10 + val('lead_key_l') * 10
    assert _have >= _need, (
        'the window plus its end keyway passes %.1f mm along the case and the '
        '%s with its cable is %.1f mm long at the lead - it cannot be '
        'threaded through' % (_have, _J34.name, _need))
    _to_edge = (val('tab_pitch') - val('case_l')) / 2 + val('lobe_pad')
    assert val('lead_key_l') >= _to_edge, (
        'the keyway runs %.2f mm from the case face but the lobe edge is '
        '%.2f mm away - it would end blind inside the lobe and trap the cable'
        % (val('lead_key_l') * 10, _to_edge * 10))

    # ---- where the cap bolts on, SOLVED before anything is cut --------------
    # The band for the cap screws is pinned on both sides: the servo window
    # inboard, the block edge outboard, a minimum wall and a HEAD RADIUS from
    # each. So the reach is not a styling choice - it is the smallest block
    # that can carry the screw, and it comes out past the silhouette. That is
    # the honest cost of bolting through the same face the servo clamps.
    _Y_PIN = -val('l2') + val('j3_centre')
    _c0, _c1, _scr, _, _ = lobe_geometry(_Y_PIN, +1)
    _win_y1 = _c1 + val('loc') / 2
    _head_r = val('cap_head_d') / 2

    # Z first - it does not depend on anything else. As far apart as the edge
    # and a FLUSH head allow, because the pair splits the servo's reaction
    # couple and wants the longest lever it can get.
    param('cap_screw_z', '%.5f mm' % ((val('lobe_z') - val('wall') - _head_r) * 10),
          'derived: as far apart as the cap edge and a flush HEAD allow. The\n'
          '           pair is stacked in Z on purpose - the servo reacts its stall\n'
          '           torque about X as a couple in Z and two screws split it; side\n'
          '           by side in Y they would not. What binds this is the counterbore,\n'
          '           not the hole: 5.0 looked fine on the shank and put the head\n'
          '           0.80 from the edge.')

    # Y is pinned by THREE things, and it took all three to find out. The
    # servo window inboard; the servo's own outer tab pilot, which is blind in
    # the same face this counterbore sinks into; and the block edge outboard.
    _y_win = _win_y1 + val('wall') + _head_r
    _sep = _head_r + val('pilot_d') / 2 + val('wall')
    _dz = val('cap_screw_z')
    _y_pilot = (max(_scr) + math.sqrt(max(_sep ** 2 - _dz ** 2, 0.0))
                if _sep > _dz else max(_scr))
    param('cap_screw_y', '%.5f mm' % (max(_y_win, _y_pilot) * 10),
          'derived: the first station clear of BOTH the servo window and the\n'
          '           servo\'s own outer tab pilot. The pilot is the binding one and it\n'
          '           is easy to miss - it is blind in the same face the cap sinks its\n'
          '           counterbore into, so the two collide underground while looking\n'
          '           2.4 mm apart on the face.')
    param('cap_reach', '%.5f mm'
          % ((max(_y_win, _y_pilot) + _head_r + val('wall') + val('cap_margin')) * 10),
          'derived: one head, one wall and a hair past the screw. The SMALLEST\n'
          '           block that can carry the fixing, and it finishes past fa_boss_r -\n'
          '           so the standoff stands proud of the link silhouette at the wrist\n'
          '           end, in free air outboard of the plate where nothing sweeps.\n'
          '           That is the honest cost of bolting through the same face the\n'
          '           servo clamps.')
    assert val('cap_screw_y') + _head_r + val('wall') <= val('cap_reach') + EPS, (
        'the cap screw head at y %.2f reaches past the block edge at %.2f'
        % (val('cap_screw_y') * 10, val('cap_reach') * 10))
    assert val('cap_screw_y') - _head_r - val('wall') >= _win_y1 - EPS, (
        'the cap screw head at y %.2f breaks into the servo window ending at '
        'y %.2f' % (val('cap_screw_y') * 10, _win_y1 * 10))
    assert val('cap_screw_z') + _head_r + val('wall') <= val('lobe_z') + EPS, (
        'the cap screw HEAD at z %.2f leaves under a wall to the edge at %.2f - '
        'the counterbore is what binds here, not the hole'
        % (val('cap_screw_z') * 10, val('lobe_z') * 10))
    # AGAINST THE WRITE PRECISION, NOT AGAINST EPS - see PARAM_ROUND_MM.
    # fa_cap_screw_y is SOLVED to sit exactly _sep from this pilot, so the
    # only thing between it and the limit is how the station rounds.
    for _ys in _scr:
        _d = math.hypot(val('cap_screw_y') - _ys, val('cap_screw_z'))
        assert _d * 10 >= _sep * 10 - PARAM_ROUND_MM, (
            'the cap screw and the servo tab pilot at y %.2f are %.4f apart '
            'and a flush head plus a wall needs %.4f - short by %.6f mm, '
            'which is more than the %.0e mm the station is written to'
            % (_ys * 10, _d * 10, _sep * 10, (_sep - _d) * 10,
               PARAM_ROUND_MM))
    assert val('cap_pilot_depth') + val('wall') <= val('j3_standoff'), (
        'a %.1f deep pilot in a %.2f standoff leaves under %.1f of floor'
        % (val('cap_pilot_depth') * 10, val('j3_standoff') * 10,
           val('wall') * 10))

    # ---- the geared elbow, checked before any of it is cut ------------------
    # THE STANDOFF, AGAINST THE LIBRARY THAT ALSO SOLVES IT. j3_servo_cap.py
    # is built to lib/joints.J3_PAD and this part is built to the expression
    # above; the two are the same arithmetic in two languages, and the servo
    # swap is exactly the change that would make one of them stale. Cheap to
    # check, and it is the check that would have caught a J3 lobe still cut
    # for an MG90S while lib/ had already moved.
    assert abs(val('j3_standoff') * 10 - _j3_standoff()) < EPS_MM, (
        'fa_j3_standoff is %.4f and lib/joints.j3_standoff() derives %.4f - '
        'this part and j3_servo_cap.py are being built to different servos'
        % (val('j3_standoff') * 10, _j3_standoff()))
    assert val('j3_standoff') >= val('j3_band') - EPS, (
        'the J3 lobe stands off %.2f but the gear turns through %.2f of that '
        'band - the servo pad would sit in the gear'
        % (val('j3_standoff') * 10, val('j3_band') * 10))
    _pocket_wall = (val('boss_r') - val('brg_pocket_d') / 2) * 10
    assert _pocket_wall >= val('wall') * 10 - EPS_MM, (
        'only %.2f mm of boss wall around the %.2f 608ZZ pocket - the boss has '
        'to grow' % (_pocket_wall, val('brg_pocket_d') * 10))
    assert val('brg_shoulder') * 10 >= MIN_SHOULDER_MM - EPS_MM, (
        'the 608ZZ pocket leaves only %.2f mm of retaining shoulder against a '
        '%.2f floor' % (val('brg_shoulder') * 10, MIN_SHOULDER_MM))
    assert val('brg_bore') * 10 > B608ZZ.inner_race_od, (
        'the retaining shoulder bores %.2f and the 608 inner race reaches '
        '%.2f - this plate does not turn, so it would rub the INNER race and '
        'lock the joint' % (val('brg_bore') * 10, B608ZZ.inner_race_od))
    assert val('brg_bore') * 10 < B608ZZ.od, (
        'the retaining shoulder bores %.2f against a %.2f bearing OD - it '
        'retains nothing' % (val('brg_bore') * 10, B608ZZ.od))
    # The whole reason the standoff is a web and not a block. Stated here so
    # the geometry below cannot quietly stop being true.
    assert val('j3_pin_clear') > val('lobe_z'), (
        'the pinion clears at r %.2f and the lobe is %.2f tall, so the pinion '
        'circle does NOT cut the standoff through - the web analysis in '
        '_HANDOFF.md section 9 no longer describes this part'
        % (val('j3_pin_clear') * 10, val('lobe_z') * 10))

    def plate(sx):
        """(start expression, distance expression) for one side wall."""
        if sx > 0:
            return PREFIX + 'plate_in', PREFIX + 'plate_t'
        return '-' + PREFIX + 'plate_out', PREFIX + 'plate_t'

    # ---- phase 1: link form ---------------------------------------------------
    t0 = design.timeline.count
    # One profile spans the full straddle AND both waists - the outboard part of
    # it IS the waist. Splitting them would only invite the two to disagree.
    r_fil = arc_radius(L2, val('boss_r'), val('waist_z'))
    assert r_fil > 0, (
        'no concave arc can join bosses of r %.1f over %.1f mm at a %.1f waist - '
        'the link would have to bulge, not pinch'
        % (val('boss_r') * 10, L2 * 10, val('waist_z') * 10))
    _, waist_z = link_profile('web', 0.0, -L2, val('boss_r'), r_fil,
                              '-(' + PREFIX + 'plate_in + ' + PREFIX + 'waist_t)',
                              '2 * (' + PREFIX + 'plate_in + ' + PREFIX + 'waist_t)', NEW)
    # The bosses stand proud of that waist by plate_t - waist_t on each face.
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        for y_p, jnt in ((0.0, 'j4'), (-L2, 'j3')):
            yz_polygon('boss_%s_%s' % (jnt, tag), y_p, 0.0,
                      2 * val('boss_r'), x0, dx, JOIN)
    for sx, y_p, run, jnt in LOBES:
        _, _, _, lo, hi = lobe_geometry(y_p, run)
        hi = block_hi(jnt, hi)
        # ONE block from inside the plate out to the tab plane. For J3 that
        # is standoff + lobe; the clearance phase then carves the gear and
        # the pinion out of it, which is what makes the standoff a web rather
        # than something drawn by hand and gone stale.
        # J4 is a pad on its plate, as it always was. J3 is now only the
        # STANDOFF - its pad lifts off as j3_servo_cap, because with the pad
        # here nothing could be assembled past it.
        if sx > 0:
            x0 = PREFIX + 'plate_out - ' + PREFIX + 'lobe_over'
            # fa_j4_lobe_t, not fa_lobe_t: the block has to reach the tab
            # PLANE, which the running gap moved 0.40 further out. Phase 4
            # then takes the outer fa_tab_thk of it back out again as the
            # flange recess - the block is cut in one piece and opened in
            # two, because a lobe drawn in two pieces is a lobe with a seam
            # in it where the fillet has to run.
            dx = PREFIX + 'j4_lobe_t + ' + PREFIX + 'lobe_over'
        else:
            x0 = '-(' + PREFIX + 'plate_out + ' + PREFIX + 'j3_standoff)'
            dx = PREFIX + 'j3_standoff + ' + PREFIX + 'lobe_over'
        yz_rect('lobe_' + jnt, lo, hi, -val('lobe_z'), val('lobe_z'), x0, dx, JOIN)
    # ---- the seat under each servo block ------------------------------------
    # THE 3.00 mm OF AIR, FILLED. It belongs in the FORM phase and not in a
    # phase of its own: this is the plate, at full thickness, under the thing
    # bolted to it - not a clearance and not a finish.
    #
    # It is CHECKED against the silhouette, not trusted to be inside it.
    # fa_seat_y_max pins the +Y end on the boss circle, but the -Y end runs
    # out along the concave waist arc, and that arc's half height is smallest
    # in the MIDDLE of the span - so the whole span is probed. Checking the
    # two ends only would pass a seat that breaks out between them.
    SIL = Silhouette(l2=L2 * 10, boss_r=val('boss_r') * 10,
                     waist_z=val('waist_z') * 10)
    assert abs(SIL.waist_z - waist_z * 10) < EPS_MM, (
        'lib/forearm_split says the outline is %.4f half-tall at the waist and '
        'link_profile drew %.4f - the two are reading different arcs'
        % (SIL.waist_z, waist_z * 10))

    def profile_half_z(y_c):
        """Half height of the link silhouette at y, in cm.

        DELEGATED, like arc_radius above: this is the same object both
        printed plates probe their own edge features against, so a feature
        that clears the outline here clears it there.
        """
        return SIL.half_z(y_c * 10) / 10

    for sx, y_p, run, jnt in LOBES:
        _, _, _, s_lo, s_hi = lobe_geometry(y_p, run)
        s_hi = min(block_hi(jnt, s_hi), val('seat_y_max'))
        assert s_hi > s_lo, (
            'the %s seat spans y %.2f .. %.2f - fa_seat_y_max has cut it away '
            'entirely' % (jnt, s_lo * 10, s_hi * 10))
        for _i in range(SEAT_PROBE_N + 1):
            _y = s_lo + (s_hi - s_lo) * _i / SEAT_PROBE_N
            assert profile_half_z(_y) >= val('seat_z') - EPS, (
                'the %s seat is %.2f half-tall but the link silhouette is only '
                '%.2f at y %.2f - the seat breaks out of the part outline'
                % (jnt, val('seat_z') * 10, profile_half_z(_y) * 10, _y * 10))
        # IN from the plate OUTER face, which is the one face both neighbours
        # are referenced to: the block starts one fa_lobe_over inside it and
        # the web ends fa_lobe_seat - fa_lobe_over inside it, so one extrude
        # overlaps both. Same shape as plate(), one face further out.
        s_x0 = (PREFIX + 'plate_out - ' + PREFIX + 'lobe_seat' if sx > 0
                else '-' + PREFIX + 'plate_out')
        yz_rect('seat_' + jnt, s_lo, s_hi, -val('seat_z'), val('seat_z'),
                s_x0, PREFIX + 'lobe_seat', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: joint clearance ---------------------------------------------
    # Everything inside the straddle that either neighbour would sweep through.
    # Cut to |x| < plate_in, not straddle/2, or the running gap gets skinned over.
    t1 = design.timeline.count
    inner0 = '-' + PREFIX + 'plate_in'
    inner_d = '2 * ' + PREFIX + 'plate_in'
    for y_p, d, nm in ((0.0, 2 * wval('sweep_r'), 'sweep_j4'),
                       (-L2, 2 * val('elbow_clear'), 'sweep_j3')):
        yz_circle(nm, y_p, 0.0, d, inner0, inner_d, CUT)
    # J4's clearance is a disc because the roll housing only swings; J3's is a
    # disc AND everything behind it, because the upper arm does not just swing
    # about the elbow, it CONTINUES through it. Cutting only the disc left the
    # elbow end webbed across and the fork shut.
    reach_back = val('boss_r') + val('wall')
    yz_rect('behind_j3', -L2 - reach_back, -L2, -reach_back, reach_back,
            inner0, inner_d, CUT)
    group(t1, PH_CLEAR)

    # ---- phase 3: pivot journals ------------------------------------------------
    t2 = design.timeline.count
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        if sx > 0:
            cb0 = PREFIX + 'plate_out - ' + PREFIX + 'cbore_depth'
        else:
            cb0 = '-' + PREFIX + 'plate_out'
        # J4 is untouched by the reduction: a journal bore and a flange
        # counterbore in each plate, same as every other joint in the arm.
        yz_circle('bore_j4_%s' % tag, 0.0, 0.0, val('bore_d'), x0, dx, CUT)
        yz_circle('cbore_j4_%s' % tag, 0.0, 0.0, val('cbore_d'),
                  cb0, PREFIX + 'cbore_depth', CUT)
        if sx < 0:
            # J3 DRIVE SIDE. j3_gear's O20 journal runs in this bore - but
            # that part has NO FLANGE (its gear disc is 47.5 and sits proud
            # of the face), so the counterbore that retains every other hub
            # in this arm is DELETED here. Leaving it would cut the journal's
            # bearing length from 7.5 to 5.0 against a hub whose collar is
            # built for the whole plate - and j3_gear.py asserts fa_plate_t
            # is that whole 7.5, so the two would silently disagree.
            yz_circle('bore_j3_%s' % tag, -L2, 0.0, val('bore_d'), x0, dx, CUT)
        else:
            # J3 IDLER SIDE. A 608ZZ, not a printed journal: the mesh loads
            # this axis radially and slop here is backlash at the tooth,
            # which is the one thing a 2:1 cannot fix. Pocketed from the
            # INNER face and retained by what is left of the plate outboard
            # of it - a shoulder whose bore must clear the INNER race, or
            # this stationary plate rubs it and locks the joint.
            yz_circle('brg_bore_j3_%s' % tag, -L2, 0.0, val('brg_bore'), x0, dx, CUT)
            yz_circle('brg_pocket_j3_%s' % tag, -L2, 0.0, val('brg_pocket_d'),
                      PREFIX + 'plate_in', PREFIX + 'brg_w', CUT)
    group(t2, PH_PIVOT)

    # ---- phase 3b: elbow drive clearance ---------------------------------------
    # The gear and the pinion both turn in the band between the plate outer
    # face and the servo lobe, and BOTH are cut out of the block above rather
    # than drawn around. The pinion's is the one that surprises: r 12.90
    # against a lobe only 8.80 tall, so it cuts the standoff through top to
    # bottom and what is left joining the lobe to the plate is a web at the
    # WRIST end. That is priced in _HANDOFF.md section 9 and it passes.
    t2b = design.timeline.count
    band0 = '-(' + PREFIX + 'plate_out + ' + PREFIX + 'j3_standoff)'
    bandd = PREFIX + 'j3_standoff'
    yz_circle('gear_sweep_j3', -L2, 0.0, 2 * val('j3_gear_clear'), band0, bandd, CUT)
    yz_circle('pinion_sweep_j3', Y_PIN, 0.0, 2 * val('j3_pin_clear'),
              band0, bandd, CUT)

    # THE CAP'S TWO M3, into the end face of what is left. The station was
    # solved in the sanity block above, against the window and the block edge.
    for sz in (+1, -1):
        yz_circle('cap_pilot_%s' % ('p' if sz > 0 else 'm'),
                  val('cap_screw_y'), sz * val('cap_screw_z'),
                  val('cap_pilot_d'), band0, PREFIX + 'cap_pilot_depth', CUT)
    group(t2b, PH_ELBOW)

    # ---- phase 4: servo lobes ----------------------------------------------------
    t3 = design.timeline.count
    # J4 ONLY. J3's window, keyway and pilots left this file with its pad
    # and live on j3_servo_cap now; what is left of J3 here is the standoff
    # web, which phase 3b already carved. The loop still runs over LOBES so
    # that the stations keep coming from the one data table above rather
    # than from a second copy of the same arithmetic.
    for sx, y_p, run, jnt in LOBES:
        if jnt == 'j3':
            continue          # the window, keyway and pilots are on the cap
        assert sx > 0, 'the only lobe this phase still cuts is J4, on +X'
        c0, c1, screws, _, _ = lobe_geometry(y_p, run)
        # TWO CUTS, NOT ONE, AND THE SERVO'S FLANGE IS WHY.
        #
        # A micro servo is not a box. fa_tab_below_top down from its case top
        # the case grows a fa_tab_thk FLANGE, fa_tab_span long - several mm
        # past the case WINDOW at each end. Cut one window
        # sized for the case and that flange lands on solid lobe, which is
        # the last fa_tab_thk of the travel it has to pass through and the
        # only material the tab screws have. GATE servo_fit MEASURED
        # it: 195.75 mm3 of MG90S inside this part, in the band
        # x 23.40..24.90, which was the flange band and nothing else. That
        # measurement predates the SG90 and its band has moved outboard with
        # fa_j4_lobe_t; the two-cut FIX is unchanged, the number is stale
        # until the gate is re-run. The two
        # rejected alternatives - standing the whole lobe off outboard of the
        # tab plane (+5.50 mm of arm width at the wrist), and simply widening
        # the one window to the flange (nothing left for the tabs to bear on
        # and no material for the pilots) - are priced in
        # specs/robotarm/_flange.md.
        #
        # THE WINDOW STILL STARTS AT THE PLATE FACE, for the reason it always
        # did: the servo travels the whole depth on the way in, so the
        # fa_j4_standoff running gap cannot be left as a skin over the case
        # top. It just stops fa_tab_thk short of the outer face now, and the
        # recess takes it from there.
        #
        # WHAT BEARS ON WHAT, AFTERWARDS. The tab TOP beds on the recess
        # floor; the screw heads land on the tab underside, flush with the
        # lobe's outer face. The tab PLANE does not move - it is still
        # fa_plate_out + fa_j4_lobe_t, and it is still the servo's datum and
        # _check_leads MOUNTS' shaft station. What changed is that it was
        # never a bearing face and no longer pretends to be one.
        win0 = PREFIX + 'plate_out'
        wind = PREFIX + 'j4_lobe_t - ' + PREFIX + 'tab_thk'
        rec0 = (PREFIX + 'plate_out + ' + PREFIX + 'j4_lobe_t - '
                + PREFIX + 'tab_thk')
        # AND THE PILOTS START AT THE RECESS FLOOR, not at the outer face:
        # that is where the screw now finds material, and drilling from the
        # old station would put the hole fa_tab_thk deeper into the part.
        pil0 = rec0 + ' - ' + PREFIX + 'pilot_depth'
        yz_rect('window_' + jnt,
                c0 - val('srv_clear') / 2, c1 + val('srv_clear') / 2,
                -val('win_z') / 2, val('win_z') / 2,
                win0, wind, CUT)
        yz_rect('flange_recess_' + jnt,
                (c0 + c1) / 2 - val('recess_l') / 2,
                (c0 + c1) / 2 + val('recess_l') / 2,
                -val('win_z') / 2, val('win_z') / 2,
                rec0, PREFIX + 'tab_thk', CUT)
        # LEAD KEYWAY: ONE notch, centred across the width, cut into the END
        # wall at the shaft end and running OUTWARD to daylight. Being centred
        # it is symmetric under the J3/J4 mirror, so one notch serves both
        # lobes and the servo may arrive either way up - which is what the
        # two-wall version was reaching for and got wrong.
        #
        # IT IS CUT THROUGH THE WHOLE LOBE, both bands. The bundle leaves the
        # case's short END face and the case fills the recess band as well as
        # the window band, so a keyway that stopped at the recess floor would
        # walk the cable straight into 1.60 mm of recess end wall - the blind
        # pocket this notch exists to prevent, one station further out.
        near_y = y_p - run * val('shaft_end')
        k_d, k_l = val('lead_key_d'), val('lead_key_l')
        ka, kb = sorted((near_y, near_y - run * k_l))
        yz_rect('lead_key_' + jnt, ka, kb, -k_d / 2, k_d / 2,
                PREFIX + 'plate_out', PREFIX + 'j4_lobe_t', CUT)
        for i, ys in enumerate(screws):
            yz_circle('pilot_%s_%d' % (jnt, i), ys, 0.0, val('pilot_d'),
                      pil0, PREFIX + 'pilot_depth', CUT)
    group(t3, PH_DRIVE)

    # ---- phase 5: cable route -----------------------------------------------------
    t4 = design.timeline.count
    # The duct and the lightening are the same cut. Everything between the two
    # walls, minus a rail top and bottom, is web that carries nothing - and the
    # loom has to get from the elbow to the wrist somehow regardless.
    xz_rect('duct', -val('plate_in'), val('plate_in'), -val('duct_z'), val('duct_z'),
            '-' + PREFIX + 'l2', PREFIX + 'l2', CUT)
    group(t4, PH_CABLE)

    # ---- phase 5b: the plate/rail seam -------------------------------------
    t4b = design.timeline.count
    # THIS BODY IS THE ASSEMBLED REFERENCE, so the seam appears here as the
    # holes it drills rather than as a joint. In the printed pieces the same
    # four stations are: a clearance hole through each plate's waist, and one
    # through-pilot down the whole length of each rail, self-tapped 8.00 from
    # EACH end by the two screws that pull the two plates onto it.
    #
    # THE PILOT RUNS RIGHT THROUGH THE RAIL AND THAT IS DELIBERATE. Blind
    # pilots drilled from each end would each roof themselves - a small
    # ceiling, but the rail's whole claim is that it is a prism along X with
    # nothing over 50 deg anywhere in it, and a blind hole is the one thing
    # that would spoil that claim. A through bore keeps it exactly true.
    #
    # WHY THE HEADS LAND ON THE WAIST AND NOT ON THE BOSS. At fa_seam_y_a/b
    # there is no boss - the plate is its fa_waist_t wall and nothing else -
    # so the head bears on that wall's OUTER face at
    # fa_plate_in + fa_waist_t and stands in the empty band out to
    # fa_plate_out, where neither servo block reaches at this height and
    # nothing sweeps. fa_seam_z is derived to keep it inside the outline.
    for tag, ys in (('a', val('seam_y_a')), ('b', val('seam_y_b'))):
        for sz, zt in ((+1, 'p'), (-1, 'm')):
            z_c = sz * val('seam_z')
            yz_circle('seam_pilot_%s%s' % (tag, zt), ys, z_c,
                      val('seam_pilot_d'), '-' + PREFIX + 'plate_in',
                      '2 * ' + PREFIX + 'plate_in', CUT)
            yz_circle('seam_clear_%s%s_p' % (tag, zt), ys, z_c,
                      val('seam_clear_d'), PREFIX + 'plate_in',
                      PREFIX + 'waist_t', CUT)
            yz_circle('seam_clear_%s%s_m' % (tag, zt), ys, z_c,
                      val('seam_clear_d'),
                      '-(' + PREFIX + 'plate_in + ' + PREFIX + 'waist_t)',
                      PREFIX + 'waist_t', CUT)
    group(t4b, PH_SEAM)

    # ---- phase 6: finish ------------------------------------------------------------
    t5 = design.timeline.count
    # ONE FILLET PER LOBE, NOT ONE FOR BOTH. They no longer take the same
    # radius - see fa_lobe_radius_j3 - and a single edge set would fail whole
    # rather than fail the corner that actually cannot carry it.
    n_fillet, fillet_note = 0, []
    for sx, y_p, run, jnt in LOBES:
        _, _, _, lo, hi = lobe_geometry(y_p, run)
        hi = block_hi(jnt, hi)
        if jnt == 'j3':
            rad_expr, rad = PREFIX + 'lobe_radius_j3', val('lobe_radius_j3')
        else:
            # J4 IS NOT sty_radius EITHER ANY MORE, AND THE FLANGE RECESS
            # TOOK IT. A 6.0 round-over reaches 6.0 in from both faces of the
            # corner it rounds, and the recess corner sits one fa_wall inside
            # the end face and 2.10 inside the top: 6.0 passed 0.28 mm from
            # the pocket. fa_lobe_radius_j4 is the largest radius that leaves
            # that diagonal as thick as the flat end wall, and the sanity
            # block asserts it.
            rad_expr, rad = PREFIX + 'lobe_radius_j4', val('lobe_radius_j4')
        col = adsk.core.ObjectCollection.create()
        skipped, buried = 0, 0
        for y_c in (lo, hi):
            for z_c in (-val('lobe_z'), val('lobe_z')):
                # A CORNER INSIDE A PIVOT BOSS IS NOT A CORNER. Where the
                # block runs into the boss the two merge and there is nothing
                # coherent to blend - Fusion says ASM_INCONS_FACE at EVERY
                # radius, which is the tell that this is not a ceiling to
                # probe for. It bit when the J3 pair shrank to module 1.00:
                # the smaller centre distance pulled the servo 6.75 mm
                # toward the elbow, cap_reach came back with it, and the +Y
                # corner landed 13.02 from the J4 axis against a 13.78 boss.
                _in_boss = False
                for _yb in (0.0, -L2):
                    # INSIDE the boss, not merely near it. The first version
                    # of this test used boss_r + rad and took J4 from four
                    # filleted corners to two - it had rounded all four for
                    # months.
                    if math.hypot(y_c - _yb, z_c) < val('boss_r'):
                        _in_boss = True
                if _in_boss:
                    buried += edge_along_x_at(y_c, z_c).count
                    continue
                skipped += (edge_along_x_at(y_c, z_c).count
                            - edge_along_x_at(y_c, z_c, rad).count)
                for e in edge_along_x_at(y_c, z_c, rad):
                    col.add(e)
        fillet_note.append('%s r%.1f on %d edges (%d too short, %d inside a boss)'
                           % (jnt, rad * 10, col.count, skipped, buried))
        if col.count and LOBE_FILLET:
            f_inp = fil.createInput()
            f_inp.addConstantRadiusEdgeSet(col, V(rad_expr), True)
            fil.add(f_inp).name = 'lobe_corners_' + jnt
            n_fillet += col.count
    # POLYGONAL: facet the OUTLINE of each fork plate. The plate's outer face
    # carries several closed curves - the boss circle, the journal counterbore,
    # the lobe blends - and only the outline reaches the body's z extreme at
    # +/- boss_r. Select on that and the counterbore is never touched, which a
    # length filter would not guarantee (the counterbore circle is 76.5 mm and
    # the outline arc is 67.3, so longer-is-outer is simply false here).
    # The plate outline is a boss CIRCLE plus a silhouette ARC, and both get the
    # facet - but only at 1.50. Probed against the built body: 2.50 and 2.00
    # fail ASM_BL_UNFIN_SHEET whether the circle is included or not, because the
    # arc runs tangentially into the circles and has nowhere to run out. 1.50
    # computes, and with the circle in it removes 331 mm3 against 143 without,
    # so the fuller outline is worth having.
    # Also note: match the SIGNED x. Comparing abs() to abs() picks up both
    # faces on the first pass and then re-uses dead references on the second.
    # THE OUTLINE IS 12-GON FLATS NOW (rule 6), so select it by GEOMETRY, not
    # by curve type: a line whose two ends both lie between the boss circle
    # and the polygon's vertex radius about ONE joint axis. The counterbore
    # and pocket circles are circles, and nothing else on the face has both
    # ends out there.
    def on_outline(e):
        if not e.geometry.objectType.endswith('Line3D'):
            return False
        r_lo = val('boss_r') - val('tol')
        r_hi = val('boss_r') / math.cos(math.pi / F.SIDES) + val('tol')
        for y_j in (0.0, -L2):
            if all(r_lo <= math.hypot(v.geometry.y - y_j, v.geometry.z) <= r_hi
                   for v in (e.startVertex, e.endVertex)):
                return True
        return False

    n_face = 0
    for x_pick in ((val('plate_out'), -val('plate_out')) if FACET else ()):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            bb = e.boundingBox
            if abs(bb.minPoint.x - x_pick) > val('tol'):
                continue
            if abs(bb.maxPoint.x - x_pick) > val('tol'):
                continue
            if on_outline(e):
                col.add(e)
        # WHAT THIS HAS TO BE, and it is no longer "two edges". The rule
        # selects everything on this face reaching the body's z extreme,
        # which is exactly the outline: one CLOSED boss circle plus the
        # silhouette. On +X the silhouette is a single arc. On -X the J3
        # standoff block now runs past where that arc ends and blends into
        # the face, SPLITTING it into two segments - so the honest assert is
        # about what the edges ARE, not how many. A bare count of 2 was right
        # only while the outline happened to come in one piece, and it failed
        # the moment the block grew; a count of 3 would be just as brittle.
        assert col.count >= F.SIDES, (
            'only %d outline facets found on the plate face - the 12-gon '
            'selection missed the outline' % col.count)
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            col, V(PREFIX + 'facet'), False)
        chf.add(c_inp).name = 'plate_facet_%s' % ('p' if x_pick > 0 else 'm')
        n_face += col.count
    group(t5, PH_FINISH)

    # ---- identity + diagnostics --------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - the web is not reaching both walls'
        % comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used_appearance = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used_appearance = a.name
                    break
            if used_appearance != 'none':
                break
        if used_appearance != 'none':
            break

    web_at_axis = web_axis
    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('SERVOS: J3 %s, J4 %s - lib/joints.JOINT_SERVO, not typed here. '
          'case %.2f x %.2f, tabs %.2f thick at %.2f pitch, flange %.2f span'
          % (_servo_name_for('J3'), _servo_name_for('J4'),
             val('case_l') * 10, val('case_w') * 10, val('tab_thk') * 10,
             val('tab_pitch') * 10, val('tab_span') * 10))
    print('L2 %.1f | plates |x| %.1f..%.1f (%.1f thick) | waist %.1f flush inside' % (
        L2 * 10, val('plate_in') * 10, val('plate_out') * 10,
        val('plate_t') * 10, val('waist_t') * 10))
    print('silhouette: r %.2f bosses joined by r %.1f concave arcs (DERIVED from the '
          '%.1f waist), waist half %.2f' % (
              val('boss_r') * 10, r_fil * 10, val('waist_z') * 10, waist_z * 10))
    print('journal bore %.2f / flange counterbore %.2f x %.1f deep, boss r %.2f' % (
        val('bore_d') * 10, val('cbore_d') * 10,
        val('cbore_depth') * 10, val('boss_r') * 10))
    for sx, y_p, run, jnt in LOBES:
        c0, c1, screws, lo, hi = lobe_geometry(y_p, run)
        print('%s lobe on %sX: case y %.1f..%.1f, screws y %.1f / %.1f, '
              'lobe y %.1f..%.1f' % (
                  jnt, '+' if sx > 0 else '-', c0 * 10, c1 * 10,
                  screws[0] * 10, screws[1] * 10, lo * 10, hi * 10))
    print('box beam: 2 walls %.1f thick + rails %.1f top and bottom, duct %.1f x %.1f'
          % (val('waist_t') * 10, val('rail_z') * 10,
             val('plate_in') * 2 * 10, val('duct_z') * 2 * 10))
    print('SPLIT: this body is the ASSEMBLED REFERENCE and is NOT the printed '
          'part - see forearm_px / forearm_nx / forearm_rail x2')
    print('   seam: 8 x M3 at y %.2f / %.2f, z +/-%.2f - %.2f clearance through '
          'each %.2f waist, %.2f pilot through the rail, %.1f engagement each end'
          % (val('seam_y_a') * 10, val('seam_y_b') * 10, val('seam_z') * 10,
             val('seam_clear_d') * 10, val('waist_t') * 10,
             val('seam_pilot_d') * 10, val('seam_engage') * 10))
    print('servo seats: fa_lobe_seat %.2f in from each plate outer face, '
          'z +/-%.2f, +Y capped at %.2f - filling the %.2f mm of air each '
          'servo block bridged outside its boss circle'
          % (val('lobe_seat') * 10, val('seat_z') * 10,
             val('seat_y_max') * 10,
             (val('plate_t') - val('waist_t') - val('lobe_over')) * 10))
    print('POLYGONAL: %.2f mm facet (LOCAL, probed ceiling on BOTH faces) on %d '
          'plate-outline edges (1 boss circle + silhouette, split on -X by the '
          'J3 standoff)' % (val('facet') * 10, n_face))
    print('lobe corners: %s' % ' | '.join(fillet_note))
    _y0 = Y_PIN + val('j3_pin_clear')
    _, _, _, _lo_j3, _hi_j3 = lobe_geometry(Y_PIN, +1)
    _hi = max(_hi_j3, _lo_j3)
    print('')
    print('GEARED ELBOW: J3 servo moved %.2f mm toward the wrist (y %.2f) and '
          '%.2f mm out' % (val('j3_centre') * 10, Y_PIN * 10,
                           val('j3_standoff') * 10))
    print('   gear turns at r %.2f, pinion at r %.2f, both in the %.2f band off '
          'the plate face' % (val('j3_gear_clear') * 10,
                              val('j3_pin_clear') * 10, val('j3_band') * 10))
    print('   the pinion circle (r %.2f) is taller than the lobe (%.2f), so the '
          'standoff' % (val('j3_pin_clear') * 10, val('lobe_z') * 10))
    print('   survives only as a web at the WRIST end, y %.2f .. %.2f - '
          '%.2f mm of it' % (_y0 * 10, _hi * 10, (_hi - _y0) * 10))
    print('   608ZZ: %.2f pocket x %.1f deep from the plate INNER face, %.2f '
          'shoulder' % (val('brg_pocket_d') * 10, val('brg_w') * 10,
                        val('brg_shoulder') * 10))
    print('   shoulder bores %.1f - OUTSIDE the %.1f inner race, so the '
          'stationary plate bears on the OUTER one'
          % (val('brg_bore') * 10, B608ZZ.inner_race_od))
    print('   J3 drive-side flange counterbore DELETED - j3_gear has no flange '
          'and its journal is built for the full %.1f plate' % (val('plate_t') * 10))
    print('   the servo PAD is not here - it is j3_servo_cap, %.1f thick, bolted '
          'to this web' % (val('cap_t') * 10))
    print('   by 2 x M3 at y %.2f, z +/-%.2f, %.1f pilot x %.1f deep. Without '
          'that split' % (val('cap_screw_y') * 10, val('cap_screw_z') * 10,
                          val('cap_pilot_d') * 10, val('cap_pilot_depth') * 10))
    print('   the gear, the pinion and the retention M3 could none of them be '
          'fitted - GATE j3_installs.')
    print('')
    print('J4 DRIVE: no horn. wrist_hub bores onto the %s spline and seats '
          '%.2f off the case top,' % (_J34.name, val('j4_standoff') * 10))
    print('   so the lobe is %.2f thick (servo stack %.2f + running gap %.2f) '
          'against %.2f before. The case top now sits %.2f OUTBOARD of the '
          'plate outer face and the hub seats ON it - the wrist does not move, '
          'the arm is %.2f wider'
          % (val('j4_lobe_t') * 10, val('lobe_t') * 10,
             val('j4_standoff') * 10, val('lobe_t') * 10,
             val('j4_standoff') * 10, val('j4_standoff') * 10))
    print('   THE FLANGE NEVER FITTED THE ONE-STEP WINDOW: tab plate %.2f '
          'long against a %.2f window, overhanging %.2f at EACH end onto solid '
          'lobe - GATE servo_fit MEASURED 195.75 mm3 of MG90S in that band. '
          'Re-run 2026-09-03 against the SG90 that replaced it, this lobe '
          'reads 0.0 - the double cut below is what fixed it, and it fixed '
          'it for the smaller case too'
          % (val('tab_span') * 10, (val('case_l') + val('srv_clear')) * 10,
             (val('tab_span') - val('case_l') - val('srv_clear')) * 10 / 2))
    print('   SO THE LOBE IS CUT TWICE: case window %.2f x %.2f deep %.2f, '
          'then a flange recess %.2f x %.2f deep %.2f to the tab plane at %.2f'
          % ((val('case_l') + val('srv_clear')) * 10, val('win_z') * 10,
             (val('j4_lobe_t') - val('tab_thk')) * 10, val('recess_l') * 10,
             val('win_z') * 10, val('tab_thk') * 10,
             (val('plate_out') + val('j4_lobe_t')) * 10))
    print('   walls left: end %.2f, side %.2f, fillet corner %.2f, all against '
          'MIN_WALL %.2f - fa_lobe_pad %.2f and fa_lobe_radius_j4 %.2f are '
          'DERIVED from those three floors, not chosen'
          % (_end_wall, _side_wall, _corner, val('wall') * 10,
             val('lobe_pad') * 10, val('lobe_radius_j4') * 10))
    print('   pilots %.1f x %.2f deep FROM THE RECESS FLOOR, leaving %.2f to '
          'fa_plate_out and the J4 flange counterbore behind it'
          % (val('pilot_d') * 10, val('pilot_depth') * 10,
             _pilot_have - val('pilot_depth') * 10))
    print('   J3 STACK UNCHANGED: fa_cap_t %.2f and fa_j3_standoff %.2f both '
          'still read fa_lobe_t, so the cap thickness and the pinion plane did '
          'not move' % (val('cap_t') * 10, val('j3_standoff') * 10))
    print('   BUT J3 IS NOT DONE. No recess is cut in the J3 lobe here and '
          'none is wanted: that lobe carries no servo any more, only the '
          'standoff web. The J3 SERVO sits on j3_servo_cap, which cuts its '
          'window through the full fa_cap_t at a tighter clearance still, so '
          'it has this same flange landing on solid pad - and it is not this '
          'file. What it gets from here is the pad: it reads fa_lobe_pad, now '
          '%.2f, which is exactly the room a %.2f recess needs.'
          % (val('lobe_pad') * 10, val('recess_l') * 10))
    print('')
    print('WEB ON THE CENTRELINE: %.1f mm between the two swings '
          '(J4 takes %.1f, J3 takes %.1f)' % (
              web_at_axis * 10, wval('sweep_r') * 10, val('elbow_clear') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
