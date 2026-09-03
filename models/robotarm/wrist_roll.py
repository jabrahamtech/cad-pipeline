"""robotarm/wrist_roll - Fusion MCP generating script.

Rebuilds `robotarm_wrist_roll` (idempotent). Spec:
specs/robotarm/wrist_roll.md, styled per specs/robotarm/_style.md.
Printability audit and the AFTER overhang table: specs/robotarm/_printability.md.

The piece between the two wrist joints. It PITCHES about J4 - a hex socket
in each side face takes a wrist_hub, one driven by the forearm's MG90S -
and it HOUSES the J5 roll SG90, whose shaft points forward along the arm.
The hand bolts to a rotator on that shaft and rolls.

THIS SCRIPT NOW BUILDS ONE HALF OF A CLAMSHELL. Read the next section
before changing anything: the part number, the print, the assembly order
and the fastener list all changed with it.

Local frame: origin on the J4 PITCH axis. +X along that axis, +Y forward
toward the hand, +Z up. THIS HALF OCCUPIES x >= 0.

===========================================================================
WHY IT IS A CLAMSHELL NOW: THE BENCH REJECTED THE MONOLITH TWICE
===========================================================================
Jonathan, holding the printed part, 2026-08-31:

    "that piece came out with the worst supports and its just impossible
     to clean"

and again after the in-place fix that followed:

    "the wrist piece is impossible to print"

TWO REPORTS, ONE PART, BOTH FROM A REAL PRINT. That outranks every rule in
this repo and it outranks the previous pass's written conclusion, which was
"Should wrist_roll be split? No." It was wrong, and it is worth naming why
it was wrong rather than just deleting it: it priced a FRONT CAP - a split
on an XZ plane at the front face - found nowhere to put fasteners in the
5.6 mm of front wall, and stopped. It never priced the split this project
already uses everywhere else.

gripper_shell.py and pruner_shell.py are BOTH clamshells carrying an SG90:
split face at z = 0, `split_face_chamfer` at sty_ef, clamshell bolts
through the split face, one design and two copies. wrist_roll was the only
servo-carrying shell in the arm that was not one, and it is the only one
that will not print. That is not a coincidence, it is the answer.

The in-place fix (a 45 deg gable on the bay's blind end) is REVERSED here.
It bought 189 -> 98 mm2 of 90 deg ceiling at the cost of thinning the front
wall 5.6 -> 3.2 over a 7.6 mm band, and it left untouched the three things
that actually made the print unclean: two 12.4 mm tab-slot bridges and a
7.6 mm bay crown at the far end of a 25.4 mm hole that opens only at the
bed - the one ceiling on the part no tool can reach - and four J4 hex
socket roof facets at 60 deg that the spec itself called unfixable and told
the user to "slice with support off and hope". Splitting deletes all of
them. The gable is gone and the front wall is 5.6 mm again.

===========================================================================
THE SPLIT PLANE: x = 0, AND IT IS CHOSEN BY THE CAVITIES, NOT BY TASTE
===========================================================================
Every internal cavity in this part is centred on, or symmetric about, the
YZ plane through the pitch axis. Splitting there turns each one into an
open pocket on both halves:

  servo bay        x +/-6.20  -> open pocket in each half, floor at 6.20
  both tab slots   x +/-6.20  -> open pockets, servo is LAID IN not threaded
  lead keyway      x +/-1.80  -> open channel, cable is laid in
  rotator bore     Oe11 on X=0 -> a half bore each, widening upward
  J4 hex sockets   x 8.60..12 -> WHOLLY inside one half. Untouched by the
                                 seam, which is the point: a pitch socket
                                 split down the middle would index on a
                                 seam and the joint would rock.

The alternatives were worked, not waved off. A split at x = +6.20 (the
bay's own wall) leaves the CENTRED features - keyway and rotator bore -
roofed, because they straddle x = 0 and nothing else does. A split on an XZ
plane (the front cap the last pass costed) puts the whole hand's moment
through the joint and still leaves the bay enclosed from the back. A split
on an XY plane cuts both hex sockets in half. x = 0 is the only plane that
opens everything and cuts no joint.

ONE DESIGN, TWO COPIES, THE SECOND MIRRORED IN X. Mirroring x -> -x leaves
the YZ silhouette unchanged and maps bay->bay and socket->socket, so the
same body is both halves. It is NOT a turn-over like gripper_shell's (the
silhouette has a keel at the bottom and a crest at the top, so it is
chiral) - the slicer mirrors it, which is exact. That is why there is no
wrist_roll_cap.py: a second script would have to re-declare this file's
whole 30-parameter servo block, and "a datum defined identically in two
files is defined nowhere" is this repo's named failure mode (lib/joints.py
exists because of it).

The price of one-design-mirrored is that EVERY feature on the seam has to
be its own complement. That rules out tongues, grooves and dowel bosses -
mirroring would put a tongue on both halves - and it is why the fastener
recess is the shape it is. See below.

PRINT ORIENTATION: OUTER SIDE FACE (x = wro_half_x) ON THE BED, BUILT ALONG
-X TOWARD THE SPLIT FACE. Build height 12.0 mm - the shortest in the wrist.

WHY THIS WAY UP, AND NOT SPLIT-FACE-DOWN LIKE gripper_shell. Both were
worked. Split face down puts every pocket at the BOTTOM of the build and
roofs each one: the bay becomes a 618 mm2 ceiling on a 22.9 mm bridge, the
tab slots and the keyway get roofs of their own, and the rotator half bore
becomes an arch that exceeds 50 deg over its top 1.29 mm. Outer face down
inverts all of it: every cavity opens at the TOP face, the half bore only
ever WIDENS going up so it needs no teardrop, and the entire outer form is
a prism along the build axis, so no outer face is an overhang at all. What
it costs is one bridge - the J4 socket's floor, 3.4 mm above the bed - and
that is the whole of what is left. gripper_shell prints split-face-down
because ITS cavities are cut up from z = 0; the rule the two parts share is
"pockets open at the top of the build", not "split face on the bed".

WHAT IS LEFT OVER AIR, STATED RATHER THAN CLAIMED AWAY:

  J4 hex socket floor   90 deg, an 18.48 mm bridge (across corners) over a
                        3.4 mm deep pocket that opens AT THE BED, anchored
                        on all six walls. 46 % of MAX_BRIDGE_MM. It is a
                        clearance-and-datum face; see the note at the
                        socket for what a sagging bridge costs there.
  nut recess shoulders  90 deg, a 4.85 mm annular bridge, x3, 2.4 mm above
                        the bed.

That is the list. No 60 deg hex roofs, no unreachable bay crown, no
tab-slot bridges, nothing over MAX_OVERHANG_DEG. SLICE WITH SUPPORT OFF.

===========================================================================
THE FASTENERS, WHICH THE LAST PASS SAID COULD NOT EXIST
===========================================================================
They exist, they are M2, and they are placed by the arithmetic below rather
than eyeballed. The last pass was right that nothing fits in the 4.64 mm
above the bay or the 5.6 mm in front of it; it was looking in the two
places that ARE full. The two that are not are the KEEL and a new CREST,
and both are on the seam where the clamping is wanted.

WHY M2 AND NOT THE ARM'S M3, WHICH IS THE ONE REAL COST OF THIS PASS. The
one-design-mirrored trick needs a single recess that takes EITHER a bolt
head or a nut, because a mirrored half does not know which it will be.
M2: head Oe3.80 fits inside a nut pocket 4.20 across flats. It works.
M3: head Oe6.00 (lib/joints M3_SOCKET_HEAD_DIA_MM) does NOT fit inside
    5.70 across flats, so M3 needs two different recesses, which means two
    mirror-image scripts and the duplicated datum block above.
M3 also does not fit the keel: its Oe3.40 hole wants 6.60 of depth between
the bay floor and the keel underside and there are 6.40, and buying the
0.20 by dropping wro_z_bot puts the keel corner past wr_sweep_r. So the
wrist clamshell is on M2 while the gripper and pruner clamshells are on M3.
That is a second hex key in the kit and it is a real wart. It is declared
here rather than hidden, and the cheap way to close it is to drop those two
to M2 as well - their seam load is no larger than this one's.

THE PATTERN, three bolts, all of them derived:
  clamp_keel_aft    one wall off the keel's 45 deg bevel, measured to the
                    nut pocket's lowest rear corner
  clamp_keel_fwd    one wall behind the lower tab slot
  clamp_crest       one wall in front of the upper tab slot, in the crest
Two at the bottom and one at the top front is not laziness, it is what the
J4 hex socket leaves: the socket is a 9.24 mm circumradius void through the
outer 3.4 mm of every bolt's path, and it eats the whole middle of the
section. Every hole and every nut pocket is checked against its true
hexagonal boundary below, not against a bounding circle.

WHAT THE SEAM CARRIES, WITH NUMBERS, BECAUSE THE LAST PASS RAISED IT.
x = 0 is a mirror plane of the structure AND of the load, so the J4 pitch
moment - 0.32 kg.cm, _assembly.md - crosses it as ZERO net force: each half
takes half the moment out through its OWN hex socket, in plane. What does
cross the seam is the J5 SG90's stall reaction, 1.8 kg.cm about Y reacted
as a couple on the bay side walls over the case length, about 7.8 N trying
to splay the halves. Three M2 bolts at ~500 N preload each put ~5.7 MPa of
contact pressure on a ~260 mm2 seam; the couple's separating stress is
about 0.09 MPa. The seam cannot open, by ~60x. Layer adhesion
(Z_TENSILE_FACTOR 0.5) is not in the load path either: layers stack along
X here, and the only sustained X-direction stresses are the hex boss
bottoming (compression) and bolt preload (compression). The pitch moment
lands as sigma_yy / sigma_zz, IN PLANE. The old +Y build had that same
moment pulling ACROSS layers - this orientation improves the weak axis
rather than compromising it.

===========================================================================
INTERFACES: NOTHING MOVED
===========================================================================
wr_pivot_af / wr_straddle / wr_sweep_r are unchanged, and wro_half_x is now
DERIVED from wr_straddle / 2 rather than typed beside it, so the two halves
provably still add up to the 24.0 the forearm fork straddles. wro_rot_seat,
the bay, both tab slots, the keyway and the Oe11 rotator bore are all at
the same coordinates they were. The worst sweep corner is still the
front-bottom one at 24.98 mm against 25.4 - neither the crest nor the
deeper keel becomes the governing corner.

Two clearances the split had to be checked against and passes:
  - the SG90's retaining screw and Oe6.3 washer are reached down
    wrt_access_d from the ROTATOR'S FRONT FACE, forward of y_front. This
    part is entirely behind that path and the crest stops at wro_crest_y1,
    well behind it, so the wrist is still serviceable after assembly.
  - the crest is inside the straddle (|x| <= half_x) and at r 18.8 max
    about J4, so wr_sweep_r keeps the forearm off it by construction.

THE KEEL. Everything this piece sweeps about J4 has to clear the forearm,
and the forearm has only 40 mm to reach the pivot from the elbow. Below the
servo pocket the part is therefore not a slab but a KEEL, bevelled at 45
deg where it meets the back face. The bevel's 45 deg is now a SWEEP number,
not a print number - it prints at 0 deg in this orientation like every
other silhouette face - and it still drops the swept radius to 24.74 mm.
The keel now runs the full half width instead of stopping at 8.0: at 8.0 it
put an 88.8 mm2 face square across the build axis with nothing under it,
which is the one overhang this orientation would otherwise have had, and
the full width is also the only material under the bay a clamp bolt can
live in. It costs about 0.7 g printed and it buys both.

The SHARED wr_* block is defined identically in wrist_hub.py and
forearm.py; lib/joints.HEX_PIVOT is the home it is being moved to.
SG90 dimensions are DATASHEET (lib/servo.py); fastener sizes are
design_rules FASTENER_MM.
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

from lib.design_rules import FASTENER_MM  # noqa: E402 - clamshell bolt sizes
from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402 - the J5 gap
from lib.design_rules import MAX_BRIDGE_MM  # noqa: E402 - socket floor, recesses
from lib.design_rules import MAX_OVERHANG_DEG  # noqa: E402 - the keel bevel
from lib.design_rules import MIN_FEATURE_MM  # noqa: E402 - split-face lands
from lib.design_rules import NUT_POCKET_AF_CLEARANCE_MM  # noqa: E402
from lib.joints import J5_ROTATOR_HUB_H_MM  # noqa: E402 - the front face
from lib.servo import CATALOG  # noqa: E402 - MEASURED lead bundle

COMPONENT = 'robotarm_wrist_roll'
BODY_NAME = 'wrist_roll'
PREFIX = 'wro_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'housing form'
PH_SERVO = 'roll servo bay'
PH_PIVOT = 'pitch socket'
PH_CLAMP = 'clamshell'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_SERVO, PH_PIVOT, PH_CLAMP, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# A count, not a dimension. Hoisted out of hexagon() because the
# PRINTABILITY block below has to derive the socket's bridge span from the
# same number the socket is drawn from, rather than from a typed 18.48.
HEX_SIDES = 2 * 3
# _style.md rule 5: two-tone by PART. A wrist is a joint, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('wrist_roll')
_SG90 = CATALOG['SG90']
# SG90 tab underside to case top, DATASHEET via lib/servo.py. Used to
# prove this file's typed case_h / tab_plane still agree with the library.
_SG90_CASE_TOP_MM = _SG90.tab_thk + _SG90.tab_below_top

# ---- THE CLAMSHELL FASTENER, SIZED AT MODULE LEVEL --------------------
# Everything here is arithmetic on design_rules and on two ISO tables, so
# it belongs outside run() where it can be read without a Fusion session.
_M2 = FASTENER_MM['M2']
# DATASHEET, ISO 4762 socket head cap screw M2. lib/joints.py carries the
# M3 head as a named constant for the same reason and this is its sibling;
# design_rules' FASTENER_MM still has no head column.
M2_SOCKET_HEAD_DIA_MM = 3.8
M2_SOCKET_HEAD_H_MM = 2.0
# DATASHEET, ISO 4032 hex nut M2.
M2_NUT_THK_MM = 1.6
# knowledge/fasteners_inserts.md boss recipe: a seat is the part's height
# plus this, so the head or the nut finishes BELOW the face rather than
# level with it. The fork plate runs 0.40 off this face - HEX_PIVOT.gap -
# so anything standing proud here fouls the wrist at full pitch.
SEAT_CLEARANCE_MM = 0.4
# ONE recess takes either end of the bolt, which is what lets one printed
# design be both halves. Deep enough for the taller of the two.
RECESS_DEPTH_MM = max(M2_SOCKET_HEAD_H_MM, M2_NUT_THK_MM) + SEAT_CLEARANCE_MM
NUT_POCKET_AF_MM = _M2['nut_af'] + NUT_POCKET_AF_CLEARANCE_MM
# What models/robotarm/_check_leads.py MOUNTS says the J5 roll shaft plane
# is, in this part's frame. It is here as a CONSTANT so the agreement with
# wro_tab_lo is ARITHMETIC rather than a remark, and so nothing in run()
# types it. It read 5.00 - the pre-spline tab plane - while this file built
# 4.60, and the disagreement was printed on every build for several commits
# and fixed by none of them. It is now 4.60 on both sides and the check
# below ASSERTS instead of printing, because a printed disagreement is a
# thing you can keep not reading. EXTRACTED-FROM _check_leads.py MOUNTS.
CHECK_LEADS_J5_SHAFT_Y_MM = 4.6
# The two are typed to two decimals on either side of the boundary, so
# they are compared at the precision they are WRITTEN at, not at eps.
PARAM_ROUND_MM = 1e-5


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

    # --- SHARED J4 pivot contract -------------------------------------------
    wrist('pivot_af', '16.0 mm',
          'J4 hex socket across flats - SHARED, defined identically in\n'
          '           wrist_hub.py and forearm.py')
    wrist('straddle', '24.0 mm',
          'the width the forearm fork straddles = this housing across the pitch\n'
          '           axis. SHARED - the fork sets its plates off this, so the two\n'
          '           files have to agree or the wrist binds. It is now the SUM OF\n'
          '           TWO PRINTED HALVES and wro_half_x derives from it, so the\n'
          '           clamshell cannot silently change what the fork straddles.')
    wrist('sweep_r', '25.4 mm',
          'the radius this housing sweeps about J4. SHARED: no forearm material\n'
          '           inside the straddle may come closer than this to the pitch axis,\n'
          '           or the wrist collides with its own arm at full pitch. Asserted\n'
          '           against every silhouette corner below, crest and keel included.')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- fits ----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('free', '0.4 mm', 'free fit - design_rules')
    param('min_feature', '%.2f mm' % MIN_FEATURE_MM,
          'smallest positive feature this printer makes - design_rules\n'
          '           MIN_FEATURE_MM, CALIBRATED. Used to prove no LAND at the split\n'
          '           face is too thin to carry its sty_ef chamfer - the failure that\n'
          '           cost gripper_shell a build (ASM_BL_UNFIN_SHEET).')

    # --- SG90, DATASHEET (lib/servo.py) --------------------------------------
    param('case_l', '22.7 mm', 'SG90 case length - lies along Z here. TowerPro B')
    param('case_w', '12.2 mm', 'SG90 case width - lies along X, so it sets the fork\n           span. 12.6 -> 12.2 on TowerPro D, 2026-08-27 flange audit')
    param('case_h', '23.7 mm', 'SG90 case height - lies along Y, the roll axis')
    param('shaft_end', '6.1 mm', 'shaft axis to the NEAR end of the case, along Z')
    param('tab_span', '32.3 mm', 'SG90 tab tip to tab tip, along Z. TowerPro E')
    param('tab_thk', '2.4 mm', 'SG90 tab thickness, along Y')
    param('tab_plane', '17.0 mm', 'case bottom to the tab UNDERSIDE, along Y')
    param('boss_h', '4.2 mm', 'output boss height above the case top')
    param('boss_d', '5.0 mm', 'output boss diameter')

    # --- derived servo placement ---------------------------------------------
    # ---- THE J5 RUNNING GAP, AND WHY THE SERVO SANK 0.40 -------------------
    # wrist_rotator.py no longer bores onto a horn; it bores onto the SG90
    # SPLINE, and lib/servo_hub seats every spline hub ONE RUNNING GAP above
    # the case top. wrt_seat_z moves 6.70 -> 7.10.
    #
    # WHICH PLANE IS HELD, AND WHY IT IS THIS ONE. wro_rot_seat is where
    # wrist_rotator's seating face lands, and the hand hangs off the rotator,
    # so it is the plane the whole effector is positioned by. It does NOT
    # move - not for the spline migration and not for this split. The SERVO
    # stands off 0.40 further from it instead.
    #
    # THE TAB PLANE MOVED WITH IT, 5.00 -> 4.60, AND _check_leads WAS TOLD.
    # That row was stale by exactly this file's wro_case_gap - the same 0.40
    # class of staleness found on the J4 row - and was corrected on
    # 2026-09-03. The agreement is now an assert in run(), not a printed
    # remark, and GATE motor_clearance audits it from the other side
    # (audit=(1, ('wro_tab_lo',))).
    param('case_gap', '%.4f mm' % _FIT['free'],
          'running gap between the SG90 case top and wrist_rotator\'s seating\n'
          '           face. design_rules JOINT_FIT_MM free - the same number\n'
          '           lib/servo_hub.spline_hub() seats on and wrt_case_gap declares.')
    param('rot_seat', '11.7 mm',
          'where wrist_rotator\'s SEATING FACE sits, and therefore where the\n'
          '           hand hangs from. UNCHANGED by the horn migration and UNCHANGED\n'
          '           by the clamshell split, and chosen so the servo straddles the\n'
          '           PITCH axis: its mass then costs J4 almost nothing. This is the\n'
          '           datum; the servo is placed off it.')
    param('case_top', PREFIX + 'rot_seat - ' + PREFIX + 'case_gap',
          'derived roll servo case top: one running gap BEHIND the rotator\'s\n'
          '           seating face. Everything else about the servo - case_bot,\n'
          '           tab_lo, keel_front, lead_y - is derived from this.')
    param('case_bot', PREFIX + 'case_top - ' + PREFIX + 'case_h', 'derived case bottom')
    param('case_z_hi', PREFIX + 'shaft_end', 'derived: case top edge in Z, above the shaft')
    param('case_z_lo', PREFIX + 'case_z_hi - ' + PREFIX + 'case_l', 'derived case bottom edge in Z')
    param('tab_lo', PREFIX + 'case_bot + ' + PREFIX + 'tab_plane',
          'derived tab underside, and the plane _check_leads MOUNTS reads for\n'
          '           J5 roll. Both are 4.60, and run() asserts it.')
    param('tab_over', '(' + PREFIX + 'tab_span - ' + PREFIX + 'case_l) / 2',
          'derived tab overhang past the case')
    param('bay_half_x', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2',
          'derived half width of the servo bay, and of the tab slots that run\n'
          '           in the same walls. IT IS ALSO THE DEPTH OF THE OPEN POCKET IN\n'
          '           THIS HALF: the bay used to be a 12.4 wide blind hole 25.4 deep\n'
          '           and it is now a 6.2 deep tray that opens at the top face.')
    param('bay_end', PREFIX + 'case_top + ' + PREFIX + 'loc / 2',
          'derived blind end of the servo bay - half a locational fit past the\n'
          '           case top. It is a CLEARANCE face, not a datum: the servo is\n'
          '           located axially by its tabs in wro_tab_slots. It prints as a\n'
          '           WALL PARALLEL TO THE BUILD AXIS now, which is why the 45 deg\n'
          '           gable that used to be cut into it has been deleted.')

    # --- housing envelope -----------------------------------------------------
    param('half_x', WRIST + 'straddle / 2',
          'half width, and THE WHOLE OF THIS PRINTED PIECE IN X. Derived from\n'
          '           the shared straddle rather than typed beside it: two of these\n'
          '           bolted back to back are what the fork straddles, and deriving\n'
          '           it is how the split cannot silently change that number.')
    param('socket_d', '3.4 mm',
          'hex socket depth into the side wall - lib/joints HEX_PIVOT.socket_d.\n'
          '           The hub\'s hex boss BOTTOMS on this floor and that bottoming,\n'
          '           not the flange, locates J4 axially. It is a datum, so it is not\n'
          '           allowed to move for a print.')
    param('y_back', '-14.0 mm', 'back face')
    param('y_front', PREFIX + 'rot_seat + %.4f mm' % J5_ROTATOR_HUB_H_MM,
          'front face - past the servo boss, carries the rotator bore, and it\n'
          '           is the plane wrist_rotator\'s DISC lands on. DERIVED, and it\n'
          '           used to be a typed 17.0 - 1.30 mm forward of rot_seat plus\n'
          '           the rotator\'s 4.00 back hub, so the disc buried 239 mm3 of\n'
          '           itself in this face. GATE motor_clearance found it as a FRAME\n'
          '           WRONG the moment its own pose stopped making the same error -\n'
          '           see lib/joints.J5_ROTATOR_HUB_H_MM.')
    param('z_top', WRIST + 'pivot_af / cos(30 deg) / 2 + ' + PREFIX + 'wall',
          'derived top face. A guessed 10.0 put the face INSIDE the hex socket\n           circumradius (9.24) - derive it from the socket so it stays right if\n           the pivot size ever moves.')
    param('body_bot', PREFIX + 'case_z_lo - ' + PREFIX + 'loc / 2 - ' + PREFIX + 'wall',
          'derived: the floor under the servo pocket, and where the slab stops.\n'
          '           Everything below this is keel, not slab.')
    param('keel_front', PREFIX + 'tab_lo + ' + PREFIX + 'tab_thk + ' + PREFIX + 'wall',
          'derived keel front face: a wall past the tab slot')
    param('keel_top', PREFIX + 'case_z_lo',
          'derived: where the keel\'s 45 deg bevel meets the BACK FACE. The keel\n'
          '           and the slab are now drawn as ONE silhouette polygon rather than\n'
          '           two solids that overlap, so this is a construction datum for the\n'
          '           bevel line and no longer a non-manifold dodge.')
    param('rot_bore', '11.0 mm',
          'clearance bore for the boss and the rotator hub. It sits ON the split\n'
          '           plane, so each half carries a half bore; the seam runs down a\n'
          '           FREE-fit clearance bore, not a bearing, and the sty_ef relief at\n'
          '           the split face leaves a 0.4 groove there that nothing rides on.')

    # --- lead escape ---------------------------------------------------------
    param('lead_key_d',
          '%.2f mm' % (CATALOG['SG90'].lead_bundle_dia + _FIT['locational']),
          'lead keyway WIDTH across the case width, centred - one full bundle\n'
          '           diameter plus a locational fit. MEASURED bundle, lib/servo.py.\n'
          '           It is centred on the SPLIT PLANE, so it is now an open channel\n'
          '           in each half and the cable is LAID IN, not threaded - the same\n'
          '           thing gripper_shell says about its own lead notch.')
    param('lead_d', '3.4 mm',
          'SG90 lead_bundle_dia - lib/servo.py. Typed here like the other\n'
          '           DATASHEET numbers; _check_leads probes with the LIBRARY value,\n'
          '           so if the two drift the gate fails rather than lying.')
    param('lead_y', PREFIX + 'case_bot + ' + PREFIX + 'lead_d',
          'derived: where the lead leaves the case bottom end face - one lead\n'
          '           diameter up from the case bottom, centred across the width.\n'
          '           The same rule _check_leads places its probe by.')

    # --- clamshell fasteners --------------------------------------------------
    # THE ONE RECESS THAT TAKES EITHER END OF THE BOLT. This is what makes
    # one printed design serve both halves: a mirrored copy does not know
    # whether it is the head side or the nut side, so the seat has to be
    # both. A hexagon 4.20 across flats traps an M2 nut (4.00 af, so it
    # cannot spin - decision tree 3 in knowledge/fasteners_inserts.md) AND
    # swallows an M2 socket head (Oe3.80). Asserted below, because the whole
    # scheme collapses if that inequality ever stops holding.
    param('bolt_d', '%.2f mm' % _M2['clearance'],
          'M2 clearance - design_rules FASTENER_MM. THROUGH both halves: the\n'
          '           tension is carried by the steel and the plastic only ever sees\n'
          '           compression under the head and the nut. That is the one way\n'
          '           knowledge/fasteners_inserts.md allows a fastener to be loaded\n'
          '           ALONG the layer direction, and layers stack along X here.')
    param('head_d', '%.2f mm' % M2_SOCKET_HEAD_DIA_MM,
          'M2 socket cap head - DATASHEET ISO 4762. Declared so the assertion\n'
          '           that it fits inside the nut pocket is arithmetic and not a\n'
          '           remark. It is the number that chose M2 over the arm\'s M3.')
    param('nut_af', '%.2f mm' % NUT_POCKET_AF_MM,
          'nut POCKET across flats: M2 nut 4.00 af plus design_rules\n'
          '           NUT_POCKET_AF_CLEARANCE_MM. It also sets how much Z the pocket\n'
          '           needs, which is what wro_z_bot and wro_crest_top are derived\n'
          '           from - the two places on this part a nut actually fits.')
    param('nut_ac', PREFIX + 'nut_af / cos(30 deg)',
          'derived nut pocket across corners - the pocket\'s reach in Y, and\n'
          '           the span its shoulder bridges when it prints.')
    param('recess_d', '%.2f mm' % RECESS_DEPTH_MM,
          'seat depth, cut from the BED face. The taller of head and nut plus\n'
          '           a seat clearance, so whichever one lands here finishes BELOW\n'
          '           the face - the fork plate runs 0.40 off it (HEX_PIVOT.gap) and\n'
          '           anything proud of it fouls the wrist at full pitch.')
    param('clamp_z_lo', PREFIX + 'case_z_lo - ' + PREFIX + 'loc / 2 - '
          + PREFIX + 'wall - ' + PREFIX + 'bolt_d / 2',
          'derived: the keel bolts sit as high under the bay floor as MIN_WALL\n'
          '           allows. As high as possible, because every millimetre lower is a\n'
          '           millimetre of keel that has to grow to hold the nut, and the\n'
          '           keel corner is the second worst sweep corner on the part.')
    param('clamp_z_hi', PREFIX + 'case_z_hi + ' + PREFIX + 'loc / 2 + '
          + PREFIX + 'wall + ' + PREFIX + 'bolt_d / 2',
          'derived: the crest bolt sits as low over the bay roof as MIN_WALL\n'
          '           allows, for the mirror-image reason - every millimetre higher is\n'
          '           a millimetre of crest, and the crest is mass on a part hanging\n'
          '           off a 1.0 kg.cm elbow.')
    param('z_bot', PREFIX + 'clamp_z_lo - ' + PREFIX + 'nut_af / 2 - ' + PREFIX + 'wall',
          'derived keel underside - and it is now the CLAMP NUT that sets it,\n'
          '           not the servo tab. It used to be case_z_lo - tab_over - loc/2 -\n'
          '           wall = -23.10; the nut pocket wants -23.20, so the keel grows\n'
          '           0.10 mm. Both floors are asserted below: the nut has to fit AND\n'
          '           the lower tab still has to have its wall.')
    param('crest_top', PREFIX + 'clamp_z_hi + ' + PREFIX + 'nut_af / 2 + ' + PREFIX + 'wall',
          'derived crest top. THE ONE PLACE THE ENVELOPE GREW: 1.86 mm of new\n'
          '           material above wro_z_top, over the 8.05 mm of Y that the crest\n'
          '           bolt\'s nut pocket needs and no more. There is nowhere else on\n'
          '           this part an upper clamp fits - the roof block over the bay is\n'
          '           4.64 mm and an M2 hole with its two walls wants 5.60.')
    param('clamp_y_crest',
          PREFIX + 'tab_lo + ' + PREFIX + 'tab_thk + ' + PREFIX + 'loc / 2 + '
          + PREFIX + 'wall + ' + PREFIX + 'bolt_d / 2',
          'derived: one wall in front of the upper tab slot. Forward of this the\n'
          '           rotator bore starts and behind it the tab slot runs, so this is\n'
          '           the only Y the crest bolt can take.')
    param('clamp_y_fwd', PREFIX + 'tab_lo - ' + PREFIX + 'loc / 2 - '
          + PREFIX + 'wall - ' + PREFIX + 'bolt_d / 2',
          'derived: one wall BEHIND the lower tab slot - the mirror of\n'
          '           wro_clamp_y_crest about the same slot. The two forward bolts\n'
          '           straddle the tab that carries the hand\'s weight.')
    param('clamp_y_aft',
          PREFIX + 'y_back + ' + PREFIX + 'keel_top - ' + PREFIX + 'clamp_z_lo + '
          + PREFIX + 'nut_ac / 4 + ' + PREFIX + 'nut_af / 2 + '
          + PREFIX + 'wall * sqrt(2)',
          'derived: the aft keel bolt sits exactly one wall off the keel\'s 45\n'
          '           deg bevel, measured to the NUT POCKET\'S lowest rear corner -\n'
          '           which is at (y - nut_ac/4, z - nut_af/2) on a hexagon drawn\n'
          '           vertex-out. The sqrt(2) is the perpendicular from a 45 deg face.')
    param('crest_y0', PREFIX + 'clamp_y_crest - ' + PREFIX + 'nut_ac / 2 - ' + PREFIX + 'wall',
          'derived crest back face: the crest is exactly as long as the nut\n'
          '           pocket plus its two walls. It is a pad, not a rail.')
    param('crest_y1', PREFIX + 'clamp_y_crest + ' + PREFIX + 'nut_ac / 2 + ' + PREFIX + 'wall',
          'derived crest front face. It stops well behind wrist_rotator\'s Oe36\n'
          '           disc, and behind the wrt_access_d path the SG90\'s retaining\n'
          '           screw and Oe6.3 washer are driven down, so the crest costs no\n'
          '           serviceability. Asserted against y_front below.')
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
    chf = comp.features.chamferFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
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

    def slab(name, x0, x1, z0, z1, y0_expr, dy_expr, op):
        """Block whose XZ outline is a rectangle, extruded along Y.

        Every CUT drawn with this now starts at x = -wro_wall, OUTSIDE the
        half, so the pocket provably breaks through the split face instead
        of leaving a curtain a hair thick on it."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, 0, z0), mpt(sk, x1, 0, z1))
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    def prism_x(name, pts_yz, x0_expr, dx_expr, op):
        """Solid whose YZ silhouette is a polygon, extruded along X.

        THE WHOLE OUTER FORM IS NOW ONE OF THESE, and that is the printability
        argument in a sentence: X is the build axis, so every face this makes
        except the two ends is PARALLEL to it - 0 deg - and no outer surface
        of the part can be an overhang by construction. The old script built
        the slab and the keel as two solids of different width, which put an
        88.8 mm2 face square across the build axis with nothing under it."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts_yz)):
            u, w = pts_yz[i], pts_yz[(i + 1) % len(pts_yz)]
            lines.addByTwoPoints(mpt(sk, 0, u[0], u[1]), mpt(sk, 0, w[0], w[1]))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def bore_x(name, y_cm, z_cm, r_cm, x0_expr, dx_expr, op):
        """A hole along X - the clamshell bolts pull across the split face."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, y_cm, z_cm), r_cm)
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def hex_pts(y_cm, z_cm, r_c_cm):
        """Regular hexagon centred on (y, z), vertices ON the Y axis and
        flats square across Z. ONE construction for the J4 pitch socket and
        for the three nut pockets, because they are the same shape at two
        sizes and drawing them twice is how two hexagons drift apart."""
        pts = []
        for i in range(HEX_SIDES):
            a = 2 * math.pi * i / HEX_SIDES
            pts.append((y_cm + r_c_cm * math.cos(a), z_cm + r_c_cm * math.sin(a)))
        return pts

    def hexagon(name, y_cm, z_cm, r_c_cm, x0_expr, dx_expr, op):
        """Hexagonal pocket, axis along X."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        pts = hex_pts(y_cm, z_cm, r_c_cm)
        for i in range(len(pts)):
            u, w = pts[i], pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(mpt(sk, 0, u[0], u[1]), mpt(sk, 0, w[0], w[1]))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def edges_in_plane_x(x_pick):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.x - x_pick) < val('tol')
                    and abs(eb.maxPoint.x - x_pick) < val('tol')):
                col.add(e)
        return col

    # ---- values in cm ---------------------------------------------------------
    half_x = val('half_x')
    loc = val('loc')
    wall = val('wall')
    bay_half_x = val('bay_half_x')
    bolt_r = val('bolt_d') / 2
    nut_r = val('nut_ac') / 2
    socket_wall = half_x - val('socket_d') - bay_half_x
    assert socket_wall >= wall, (
        'only %.2f mm of wall between the hex socket and the servo pocket' % (socket_wall * 10))
    assert abs(half_x * 2 - wval('straddle')) < val('tol'), (
        'two halves of %.2f make %.2f and the fork straddles %.2f - the split '
        'has changed the shared J4 contract'
        % (half_x * 10, half_x * 2 * 10, wval('straddle') * 10))
    r_c = wval('pivot_af') / 2 / math.cos(math.pi / HEX_SIDES)
    assert r_c + wall <= val('z_top'), 'the hex socket breaks out of the top face'

    # ---- THE HEX SOCKET IS AN OBSTRUCTION, NOT JUST A JOINT ----------------
    # It is a 9.24 mm circumradius void through the OUTER 3.4 mm of the half,
    # centred on the pitch axis - which is to say it sits in the middle of
    # every clamshell bolt's path and of every nut pocket. The previous pass
    # said there was nowhere to put fasteners; this is the real reason the
    # answer is three and not six. Every hole and every pocket is checked
    # against the socket's TRUE hexagonal boundary rather than its bounding
    # circle, because the circle is 1.24 mm pessimistic exactly where the
    # crest bolt has to go and it would have cost a millimetre of crest.
    socket_ap = r_c * math.cos(math.pi / HEX_SIDES)

    def socket_gap(y_cm, z_cm):
        """Distance from a point to the J4 socket hexagon. Positive outside.

        max over the six supporting half planes: exact when the nearest
        feature is an edge and an UNDER-estimate when it is a vertex, so it
        errs toward demanding more wall, never less."""
        best = None
        for k in range(HEX_SIDES):
            n = math.pi / HEX_SIDES + 2 * math.pi * k / HEX_SIDES
            s = y_cm * math.cos(n) + z_cm * math.sin(n) - socket_ap
            if best is None or s > best:
                best = s
        return best

    # LEAD KEYWAY sanity, in cm. The keyway is a centred slot in the pocket's
    # +Z END wall - the shaft end, which is where the bundle leaves the case.
    assert val('lead_key_d') >= val('lead_d') + loc, (
        'the lead keyway is tighter than the bundle plus a locational fit')
    assert val('lead_key_d') / 2 + wall <= r_c - val('socket_d'), (
        'the lead keyway comes within a wall of the J4 hex sockets')
    assert val('lead_y') + val('lead_key_d') / 2 < val('case_top'), (
        'the keyway runs past the case front face and into the rotator bore')

    # ---- THE OUTER FORM, AS ONE SILHOUETTE --------------------------------
    # Slab, keel and crest in a single closed polygon, walked from the back
    # bottom clockwise. The keel is no longer a narrower second solid: it is
    # the bottom of this outline, so it runs the full half width, so there is
    # no step across the build axis and there IS material under the bay for a
    # clamp bolt. Both of those are the same edit.
    keel_drop = val('keel_top') - val('z_bot')
    assert val('keel_top') > val('body_bot'), (
        'the keel bevel starts below the slab, so the silhouette folds on '
        'itself - wro_keel_top %.2f is under wro_body_bot %.2f'
        % (val('keel_top') * 10, val('body_bot') * 10))
    form_pts = [
        (val('y_back'), val('body_bot')),
        (val('y_back') + val('keel_top') - val('body_bot'), val('body_bot')),
        (val('y_back') + keel_drop, val('z_bot')),
        (val('keel_front'), val('z_bot')),
        (val('keel_front'), val('body_bot')),
        (val('y_front'), val('body_bot')),
        (val('y_front'), val('z_top')),
        (val('crest_y1'), val('z_top')),
        (val('crest_y1'), val('crest_top')),
        (val('crest_y0'), val('crest_top')),
        (val('crest_y0'), val('z_top')),
        (val('y_back'), val('z_top')),
    ]
    worst = ('', 0.0)
    for y, z in form_pts:
        r = math.hypot(y, z)
        if r > worst[1]:
            worst = ('corner (%.1f, %.1f)' % (y * 10, z * 10), r)
    assert worst[1] <= wval('sweep_r'), (
        'the %s sweeps %.1f mm about J4, past the %.1f mm the forearm allows'
        % (worst[0], worst[1] * 10, wval('sweep_r') * 10))
    assert val('crest_y1') + wall <= val('y_front'), (
        'the crest reaches y %.2f and the front face is at %.2f - it would '
        'stand in front of the rotator seat'
        % (val('crest_y1') * 10, val('y_front') * 10))

    # ---- PRINTABILITY GATE, OUTER FACE ON THE BED, BUILT -X ----------------
    # Jonathan has now printed this part TWICE and called it impossible both
    # times. The angles below are computed from the polygons this script
    # actually draws, in the orientation it is actually sliced in, rather
    # than recited from a docstring - which is what let "No support." stand
    # in this file for months over an enclosed bay.
    #
    # THE CONVENTION, once: angle from the BUILD AXIS, which is X. A face
    # parallel to X is 0 deg, a face square across it is 90, and
    # MAX_OVERHANG_DEG (50.0) is the limit. A 90 deg face anchored on ALL
    # sides is not an overhang, it is a BRIDGE, and answers to MAX_BRIDGE_MM.
    #
    # There are exactly two 90 deg faces left on this part and both are
    # bridges. Everything else is either parallel to X (the whole outer form
    # and every cavity wall) or an UP-FACING FLOOR, which is free.
    hex_ac = wval('pivot_af') / math.cos(math.pi / HEX_SIDES)
    bridges = [('J4 socket floor', hex_ac),
               ('nut recess shoulder', val('nut_ac'))]
    for _label, _span in bridges:
        assert _span * 10 <= MAX_BRIDGE_MM, (
            'the %s bridges %.1f mm and design_rules allows %.1f'
            % (_label, _span * 10, MAX_BRIDGE_MM))
    # The keel bevel is a SWEEP feature now, not a print feature - it prints
    # at 0 deg like every other silhouette face. The check stays because the
    # bevel is still the only sloped line on the part, and if anyone ever
    # stands this back on its back face it is the thing that makes that
    # survivable. Honest about which orientation it is talking about.
    keel_bevel_deg = math.degrees(math.atan2(
        form_pts[2][0] - form_pts[1][0], form_pts[1][1] - form_pts[2][1]))
    assert keel_bevel_deg <= MAX_OVERHANG_DEG, (
        'the keel bevel is %.1f deg and design_rules allows %.1f'
        % (keel_bevel_deg, MAX_OVERHANG_DEG))

    # ---- SPLIT-FACE LANDS: ZERO, OR THICK ENOUGH TO CHAMFER ---------------
    # THIS CHECK COST gripper_shell A BUILD. The finish phase chamfers EVERY
    # edge in the plane x = 0 at sty_ef. Two cuts that both open on the split
    # face and stop a hair apart leave a LAND that has to carry two of those
    # chamfers, and Fusion fails the WHOLE feature - ASM_BL_UNFIN_SHEET - not
    # the one edge that cannot take it. A land may be NEGATIVE (the cuts
    # merge), ZERO (flush, one edge) or at least MIN_FEATURE_MM. Not between.
    lands = [
        ('bay roof to lead keyway floor',
         (val('case_z_hi') + loc / 2) - (val('case_z_hi') + loc / 2)),
        ('lead keyway roof to the top face',
         val('z_top') - (val('z_top') + loc / 2)),
        ('bay front wall to the rotator bore',
         val('case_top') - val('bay_end')),
        ('tab slot roof to the crest top',
         val('crest_top') - (val('case_z_hi') + val('tab_over') + loc / 2)),
        ('tab slot floor to the keel underside',
         (val('case_z_lo') - val('tab_over') - loc / 2) - val('z_bot')),
        ('keel clamp bolts to the bay floor',
         (val('case_z_lo') - loc / 2) - (val('clamp_z_lo') + bolt_r)),
        ('keel clamp bolts to the keel underside',
         (val('clamp_z_lo') - bolt_r) - val('z_bot')),
        ('crest clamp bolt to the bay roof',
         (val('clamp_z_hi') - bolt_r) - (val('case_z_hi') + loc / 2)),
        ('crest clamp bolt to the crest top',
         val('crest_top') - (val('clamp_z_hi') + bolt_r)),
        ('forward keel bolt to the lower tab slot',
         (val('tab_lo') - loc / 2) - (val('clamp_y_fwd') + bolt_r)),
        ('crest bolt to the upper tab slot',
         (val('clamp_y_crest') - bolt_r)
         - (val('tab_lo') + val('tab_thk') + loc / 2)),
    ]
    for _nm, _gap in lands:
        assert _gap < val('tol') or _gap >= val('min_feature'), (
            'the split face leaves a %.3f mm land, %s. Two sty_ef chamfers have '
            'to share it and split_face_chamfer will fail WHOLE, not just on '
            'that edge. Make it flush or make it at least %.2f mm'
            % (_gap * 10, _nm, val('min_feature') * 10))

    # ---- THE FASTENERS EXIST, AND HERE IS THE ARITHMETIC ------------------
    # The previous pass's objection was "there is nowhere to put them". Each
    # clamp below is proved against every surface it could break into, and
    # the two envelope changes it forced - a 0.10 mm deeper keel and a
    # 1.86 mm crest - are derived from the nut pocket rather than chosen.
    assert val('head_d') <= val('nut_af'), (
        'an M2 socket head is %.2f across and the nut pocket is %.2f across '
        'flats - ONE recess can no longer take either end of the bolt, so one '
        'printed design can no longer be both halves. This inequality is what '
        'put the wrist clamshell on M2 instead of the arm\'s M3 (head 6.00 '
        'against a 5.70 pocket)' % (val('head_d') * 10, val('nut_af') * 10))
    assert val('recess_d') + wall <= half_x - val('socket_d'), (
        'the %.2f deep fastener seat and the %.2f deep hex socket meet inside '
        'a %.2f half' % (val('recess_d') * 10, val('socket_d') * 10, half_x * 10))
    # The keel floor is set by the clamp nut now. It still has to be at least
    # as deep as the servo tab wanted, or the split has quietly taken the
    # wall out from under the lower tab.
    _tab_floor = val('case_z_lo') - val('tab_over') - loc / 2 - wall
    assert val('z_bot') <= _tab_floor, (
        'the keel floor is %.2f and the lower servo tab needs %.2f - the clamp '
        'nut pocket has pulled the keel up above the tab\'s wall'
        % (val('z_bot') * 10, _tab_floor * 10))
    clamps = [
        ('clamp_keel_aft', val('clamp_y_aft'), val('clamp_z_lo')),
        ('clamp_keel_fwd', val('clamp_y_fwd'), val('clamp_z_lo')),
        ('clamp_crest', val('clamp_y_crest'), val('clamp_z_hi')),
    ]
    bevel_sum = val('y_back') + val('keel_top')
    for _nm, _y, _z in clamps:
        assert socket_gap(_y, _z) - bolt_r >= wall, (
            '%s passes %.2f mm from the J4 hex socket and MIN_WALL is %.2f - '
            'the bolt would break into the pitch joint'
            % (_nm, (socket_gap(_y, _z) - bolt_r) * 10, wall * 10))
        for _vy, _vz in hex_pts(_y, _z, nut_r):
            assert socket_gap(_vy, _vz) >= wall, (
                '%s\'s nut pocket comes %.2f mm from the J4 hex socket and '
                'MIN_WALL is %.2f' % (_nm, socket_gap(_vy, _vz) * 10, wall * 10))
            # and inside the outline: the keel's 45 deg bevel is the only
            # boundary a pocket can cross without crossing a flat face first.
            if _vz < val('body_bot'):
                _d = (_vy + _vz - bevel_sum) / math.sqrt(2)
                assert _d >= wall - val('tol'), (
                    '%s\'s nut pocket reaches %.2f mm from the keel bevel and '
                    'MIN_WALL is %.2f' % (_nm, _d * 10, wall * 10))
        assert _y - nut_r - wall >= val('y_back') and _y + nut_r + wall <= val('y_front'), (
            '%s\'s nut pocket runs out of the part in Y' % _nm)
    # The crest bolt is the one that passes the rotator bore. It clears in Z,
    # not in Y - the hole ends 0.08 short of the bore's start plane and only
    # the 3.5 mm of Z between them keeps it out of the bore, which is why
    # this is measured as a distance and not as a Y land.
    _bore_gap = math.hypot(
        max(val('case_top') - val('clamp_y_crest'), 0.0),
        max(val('clamp_z_hi') - val('rot_bore') / 2, 0.0)) - bolt_r
    assert _bore_gap >= wall, (
        'the crest clamp bolt passes %.2f mm from the Oe%.1f rotator bore and '
        'MIN_WALL is %.2f' % (_bore_gap * 10, val('rot_bore') * 10, wall * 10))

    # THE SG90 OUTPUT BOSS, which nothing in this file used to check against
    # anything. It stands proud of the case top and turns inside the rotator
    # bore, so the bore has to clear it radially AND still be there when the
    # boss tops out.
    assert val('boss_d') + val('free') <= val('rot_bore'), (
        'the Oe%.1f SG90 output boss turns inside the Oe%.1f rotator bore and '
        'wants a free fit - that is %.2f mm short'
        % (val('boss_d') * 10, val('rot_bore') * 10,
           (val('boss_d') + val('free') - val('rot_bore')) * 10))
    assert val('case_top') + val('boss_h') <= val('y_front') + wall, (
        'the boss tops out at y %.2f and the rotator bore only runs to %.2f'
        % ((val('case_top') + val('boss_h')) * 10,
           (val('y_front') + wall) * 10))

    # ---- phase 1: housing form -------------------------------------------------
    t0 = design.timeline.count
    prism_x('housing_form', form_pts, '0.0 mm', PREFIX + 'half_x', NEW)
    # THE BED FACE, CHAMFERED BEFORE ANY CAVITY IS CUT. Elephant foot on the
    # outer silhouette only: doing it here rather than in the finish phase
    # deliberately leaves the J4 socket mouth and the three fastener seats
    # SHARP, because the socket mouth is a joint surface and 0.4 off it is
    # 0.4 of hex indexing this part is not allowed to give away.
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_x(half_x), V(STYLE + 'ef'), False)
    chf.add(c_inp).name = 'bed_face_chamfer'
    group(t0, PH_FORM)

    # ---- phase 2: roll servo bay ------------------------------------------------
    # EVERY CUT IN THIS PHASE STARTS AT x = -wro_wall, outside the half, so
    # each one opens fully on the split face. That is the whole fix: the bay,
    # both tab slots and the keyway stop being enclosed volumes with roofs
    # printed over air and become trays that open at the top of the build.
    # (The bay_roof_gable that used to be cut here is GONE. It was the last
    # pass's answer to the same bench report and it did not survive contact
    # with the printer - see the docstring.)
    t1 = design.timeline.count
    slab('servo_case_pocket',
         -wall, bay_half_x,
         val('case_z_lo') - loc / 2, val('case_z_hi') + loc / 2,
         PREFIX + 'y_back - ' + PREFIX + 'wall',
         PREFIX + 'bay_end - ' + PREFIX + 'y_back + ' + PREFIX + 'wall',
         CUT)
    # LEAD KEYWAY. The bundle leaves the case's SHORT END FACE at the shaft
    # end - here the +Z end - dead centre across the width, which puts it ON
    # the split plane. It breaks out through the top face at z_top; the crest
    # starts forward of wro_crest_y0 and never roofs it, which is checked by
    # the aft-keel-bolt land above being measured from the same edge.
    slab('lead_key', -wall, val('lead_key_d') / 2,
         val('case_z_hi') + loc / 2, val('z_top') + loc / 2,
         PREFIX + 'y_back - ' + PREFIX + 'wall',
         PREFIX + 'lead_y + ' + PREFIX + 'lead_key_d / 2 - ' + PREFIX
         + 'y_back + ' + PREFIX + 'wall',
         CUT)
    slab('tab_slots',
         -wall, bay_half_x,
         val('case_z_lo') - val('tab_over') - loc / 2,
         val('case_z_hi') + val('tab_over') + loc / 2,
         PREFIX + 'tab_lo - ' + PREFIX + 'loc / 2',
         PREFIX + 'tab_thk + ' + PREFIX + 'loc', CUT)
    # THE ROTATOR BORE IS SKETCHED WHOLE AND CUT HALF. Its axis lies IN the
    # split plane, so the circle drawn here reaches x = -5.5 into nothing and
    # what is left in this half is the upper half of a horizontal hole - which
    # in this orientation only ever WIDENS toward the top of the build, so it
    # needs no teardrop. Turned the other way up it would be an arch over 50
    # deg for its top 1.29 mm. That is the single clearest reason this part is
    # sliced outer-face-down and not split-face-down.
    sk_rot = sketch(comp.xZConstructionPlane, 'sk_rotator_bore')
    sk_rot.sketchCurves.sketchCircles.addByCenterRadius(
        mpt(sk_rot, 0, 0, 0), val('rot_bore') / 2)
    extrude(profiles(sk_rot, expected=1), CUT, PREFIX + 'case_top',
            PREFIX + 'y_front - ' + PREFIX + 'case_top + ' + PREFIX + 'wall', 'rotator_bore')
    group(t1, PH_SERVO)

    # ---- phase 3: pitch socket --------------------------------------------------
    # ONE socket now, not two: the other one belongs to the mirrored half.
    # It is cut from the BED face and its floor is the last 90 deg surface on
    # the part - an 18.48 mm bridge over a 3.4 mm pocket, anchored on all six
    # walls, three layers up. The floor is also the axial DATUM the hub's hex
    # boss bottoms on (lib/joints: "that bottoming, not the flange, is what
    # locates the joint"), so bridge sag matters here and is bounded: a 0.2 mm
    # droop shortens the socket by 0.2, the hub sits 0.2 further out, and
    # HEX_PIVOT.cbore_extra is 0.5 of slack put there for exactly that.
    t2 = design.timeline.count
    hexagon('pitch_socket', 0, 0, r_c, PREFIX + 'half_x',
            '-' + PREFIX + 'socket_d', CUT)
    group(t2, PH_PIVOT)

    # ---- phase 4: clamshell ------------------------------------------------------
    # Three M2 through-bolts on the seam. Each is a clearance hole the whole
    # width of the half plus a hexagonal seat at the BED face that takes the
    # head on one copy and traps the nut on the mirrored one.
    t3 = design.timeline.count
    for _nm, _y, _z in clamps:
        bore_x(_nm, _y, _z, bolt_r, '-' + PREFIX + 'wall',
               PREFIX + 'half_x + ' + PREFIX + 'wall', CUT)
        hexagon(_nm + '_seat', _y, _z, nut_r, PREFIX + 'half_x',
                '-' + PREFIX + 'recess_d', CUT)
    group(t3, PH_CLAMP)

    # ---- phase 5: finish -----------------------------------------------------------
    # THE SPLIT FACE, RELIEVED AT sty_ef - the same feature name, the same
    # value and the same reason as gripper_shell.py and pruner_shell.py: a
    # burr or an elephant foot on the mating plane holds the two halves apart
    # and the seam shows. The lands that feed this chamfer are asserted above.
    t4 = design.timeline.count
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_x(0), V(STYLE + 'ef'), False)
    chf.add(c_inp).name = 'split_face_chamfer'
    group(t4, PH_FINISH)

    # ---- identity + diagnostics --------------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got ' + str(comp.bRepBodies.count)
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

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('CLAMSHELL HALF. ONE DESIGN, TWO COPIES, THE SECOND MIRRORED IN X.')
    print('  split face x 0.0, this half x 0.0..%.1f; the pair still straddle %.1f'
          % (half_x * 10, wval('straddle') * 10))
    print('  the bench rejected the monolith TWICE - "worst supports, impossible '
          'to clean", then "impossible to print" after the gable. The gable is '
          'reverted; the front wall is %.2f again.'
          % ((val('y_front') - val('bay_end')) * 10))
    # THE TWO NUMBERS THE SPLINE STACK RESTS ON. wro_case_h and wro_tab_plane
    # are typed DATASHEET copies; if either drifts from lib/servo.py the servo
    # is placed from one set of numbers and bored from another.
    _case_top_from_tabs = (val('case_top') - val('tab_lo')) * 10
    assert abs(_case_top_from_tabs - _SG90_CASE_TOP_MM) < val('tol') * 10, (
        'this file places the SG90 case top %.2f above its tab underside and '
        'lib/servo.py says %.2f - wro_case_h or wro_tab_plane has drifted from '
        'the library' % (_case_top_from_tabs, _SG90_CASE_TOP_MM))
    _seat_from_tabs = (val('rot_seat') - val('tab_lo')) * 10
    assert abs(_seat_from_tabs - (_SG90_CASE_TOP_MM + val('case_gap') * 10)) < val('tol') * 10, (
        'wrist_rotator seats %.2f up the SG90 by this part\'s arithmetic and '
        'wrt_seat_z is %.2f' % (_seat_from_tabs, _SG90_CASE_TOP_MM + val('case_gap') * 10))
    print('roll servo: case y %.1f..%.1f, z %.1f..%.1f | tabs y %.1f, z +/-%.1f' % (
        val('case_bot') * 10, val('case_top') * 10,
        val('case_z_lo') * 10, val('case_z_hi') * 10, val('tab_lo') * 10,
        (val('case_z_hi') + val('tab_over')) * 10))
    _tab_lo_mm = val('tab_lo') * 10
    assert abs(CHECK_LEADS_J5_SHAFT_Y_MM - _tab_lo_mm) < PARAM_ROUND_MM, (
        '_check_leads MOUNTS puts J5 roll\'s shaft at y %.2f and this part '
        'builds its tab plane at y %.2f - off by %.2f. Every lead and motor '
        'clearance measured at J5 is sited from that row.'
        % (CHECK_LEADS_J5_SHAFT_Y_MM, _tab_lo_mm,
           CHECK_LEADS_J5_SHAFT_Y_MM - _tab_lo_mm))
    print('J5 SEATING: tab plane y %.2f, agreed with _check_leads MOUNTS. The '
          'rotator seats on wro_rot_seat %.2f, NOT on wro_y_front %.2f - '
          'lib/joints.J5_ROTATOR_ORIGIN_PARTS. _check_wrist, _preview_arm and '
          '_check_motor_clearance all posed it off the front face until '
          '2026-09-03, 1.30 mm out, which stopped the retaining washer '
          'reaching the spline step.'
          % (_tab_lo_mm, val('rot_seat') * 10, val('y_front') * 10))
    print('keel: full half width now (was 8.0), y %.1f..%.1f, z %.1f..%.1f, '
          'bevel %.1f mm at %.1f deg' % (
              (val('y_back') + keel_drop) * 10, val('keel_front') * 10,
              val('z_bot') * 10, val('keel_top') * 10, keel_drop * 10,
              keel_bevel_deg))
    print('crest: y %.2f..%.2f, top %.2f (z_top %.2f) - THE ONLY ENVELOPE '
          'GROWTH, %.2f mm in +Z over %.2f mm of Y, to seat one nut'
          % (val('crest_y0') * 10, val('crest_y1') * 10, val('crest_top') * 10,
             val('z_top') * 10, (val('crest_top') - val('z_top')) * 10,
             (val('crest_y1') - val('crest_y0')) * 10))
    print('clamshell: 3 x M2 through-bolt, Oe%.2f clearance, seat %.2f af x '
          '%.2f deep at the bed face (head Oe%.2f OR nut, same recess)'
          % (val('bolt_d') * 10, val('nut_af') * 10, val('recess_d') * 10,
             val('head_d') * 10))
    for _nm, _y, _z in clamps:
        print('    %-16s y %7.2f  z %7.2f   J4 socket clearance %.2f mm'
              % (_nm, _y * 10, _z * 10, (socket_gap(_y, _z) - bolt_r) * 10))
    print('    the arm\'s other two clamshells are on M3. This one cannot be: '
          'an M3 head is 6.00 across and an M3 nut pocket 5.70, so one recess '
          'cannot take both ends and the one-design-mirrored trick fails.')
    print('PRINTABILITY - OUTER FACE ON THE BED (x %.1f), BUILT -X, SUPPORT OFF.'
          % (half_x * 10))
    print('  the entire outer form is ONE prism along the build axis, so no '
          'outer face is an overhang. Every cavity opens at the top face.')
    print('  faces over %.1f deg: NONE.' % MAX_OVERHANG_DEG)
    print('  bridges (90 deg, anchored all round, limit %.1f mm):' % MAX_BRIDGE_MM)
    for _label, _span in bridges:
        print('    %-22s %5.2f mm' % (_label, _span * 10))
    print('  GONE with the split: a 7.6 mm bay crown %.1f mm down a hole that '
          'opened only at the bed, two %.1f mm tab-slot bridges, a %.1f mm '
          'keyway bridge, and four J4 socket roof facets at 60 deg.'
          % ((val('bay_end') - val('y_back')) * 10, bay_half_x * 2 * 10,
             val('lead_key_d') * 10))
    print('WORST SWEEP about J4: %s at %.2f mm (forearm allows %.1f)' % (
        worst[0], worst[1] * 10, wval('sweep_r') * 10))
    print('hex socket %.1f af, %.1f deep, leaving %.2f mm of wall beside the servo' % (
        wval('pivot_af') * 10, val('socket_d') * 10, socket_wall * 10))
    print('SERVICE: the SG90 retaining screw and Oe6.3 washer are driven down '
          'wrt_access_d from the ROTATOR front face, forward of y %.1f. This '
          'half is entirely behind it and the crest stops at y %.2f, so the '
          'wrist is still serviceable assembled.'
          % (val('y_front') * 10, val('crest_y1') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s   (ONE HALF - double it '
          'for the assembly)' % (
              body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
