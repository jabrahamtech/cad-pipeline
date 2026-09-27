"""robotarm/base_platter - Fusion MCP generating script.

Rebuilds `robotarm_base_platter` (idempotent). Spec:
specs/robotarm/base_platter.md - ASSUMED there: where the ESP32 carrier
sits inside its 30 mm envelope (mid-height), and the insertion clearance.

THE BASE, REBUILT. Jonathan, 2026-09-27: J1 is an MG995 360 deg, the
electronics are an ESP32 on a 70 x 50 carrier PCB with cables off BOTH
faces (70 x 50 x 30 all-in), the breadboard is gone, the toggle switch and
DC jack stay in the rim, and every other cable leaves through the TOP. The
printed legacy platter (specs/robotarm/base_platter_measured.md) had an
SG90-sized column and cannot take any of that.

Frame: the SAME as turntable_stator - origin on the J1 yaw axis at the RIM
TOP, +Z up, az from +X. So this part lives at z < 0. The MG995 case lies
along +Y and hangs to z -20.70 (turntable_stator prints it); nothing in this
part is allowed inside that envelope or its insertion path.

  shell        O190 x 42, wall 3.0, floor 2.4. Bigger than the old O176:
               the ESP32 bay plus a finger gap at each end has to fit beside
               a 40.9 mm servo, and the old diameter left no room for both.
  lid recess   O186.8 x 3.0 from the top, so base_lid finishes flush.
  turret posts 3 x O8.8 at r 45, az 120/180/240, M3 insert O4.0 at the top -
               the tt_post_r contract, so turntable_stator and turntable_ring
               bolt on unchanged. Stator -> lid -> post, one M3 each.
  lid columns  4 x O8.8 at r 88, az 45/135/225/315, M3 insert O4.0, top
               under the lid. At r 88 they merge into the wall - no slot.
  ESP32 bay    +X sector, 50 (x) x 70 (y) board, 30 tall envelope. The
               board drops in from above onto four corner LEDGES inside four
               L-shaped corner FENCES, with esp_clear of insertion play. The
               sides between the corners are open, so the bottom-face cables
               have a way out and up. Finger gaps at both short ends.
  rim          toggle switch hole and DC-cable pass-through at the REAR
               (az 165 / 195), with a zip-tie bridge inside the DC entry.

Cables: the loom from the arm comes DOWN through the stator's az-210
window and the lid's matching window, and runs under the servo to the bay
(18.9 mm of clearance under the MG995 case). The J1 servo lead leaves the
case's -Y end. The hall sensor's leads drop through the lid right over the
bay. Nothing else leaves the base but power.

Print: PETG, FLAT on its floor, open side up, no support. The two rim holes
are horizontal; the toggle hole droops ~0.3 at its crown, which the switch's
own nut covers.
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

from lib.palette import hints_for  # noqa: E402
from lib.design_rules import FASTENER_MM as _FASTENER  # noqa: E402
from lib.design_rules import MIN_WALL_MM as _MIN_WALL  # noqa: E402
from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402
from lib.servo import SERVO_CASE_CLEARANCE_MM  # noqa: E402
from lib.j1_drive import (  # noqa: E402
    J1_SERVO, J1_DECK_Z_MM, LOOM_AZ_DEG, LOOM_IR_MM, LOOM_OR_MM, LOOM_DEG, TT_POST_D_MM,
)
from lib.design_rules import MIN_FILLET_LOADED_MM  # noqa: E402
from lib.esp_bay import (  # noqa: E402
    PCB_W_MM, PCB_L_MM, PCB_T_MM, ESP_H_MM, ESP_CLEAR_MM,
    FENCE_T_MM, FENCE_LEG_MM, LEDGE_MM, FENCE_OVER_MM,
)

COMPONENT = 'robotarm_base_platter'
BODY_NAME = 'base_platter'
PREFIX = 'bp_'
TURRET = 'tt_'
PH_SHELL = 'shell'
PH_POSTS = 'posts + columns'
PH_BAY = 'esp32 bay'
PH_RIM = 'rim + strain relief'
PH_FINISH = 'finish'
PHASES = [PH_SHELL, PH_POSTS, PH_BAY, PH_RIM, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('base_platter')

POST_AZ = (120.0, 180.0, 240.0)          # tt_ contract - the ring's holes
LID_AZ = (45.0, 135.0, 225.0, 315.0)
CORNERS = ((-1, -1), (1, -1), (1, 1), (-1, 1))
TOL = 1e-9
REL_TOL = 1e-6                # profile-area match, relative
PETG_G_CM3 = 1.27             # printed-mass convention, _HANDOFF.md
PRINT_FILL = 0.65

# THE J1 SERVO ENVELOPE, in this frame, from lib/j1_drive - the same numbers
# turntable_stator places the servo from (it asserts its tt_ params against
# them). Nothing in this part may enter it: it is the case, its window
# clearance, and the insertion path straight down from the stator.
def _servo_box_mm():
    """(x0, x1, y0, y1, z0, z1) of the J1 case + its window clearance."""
    s = J1_SERVO
    half_w = s.case_w / 2 + SERVO_CASE_CLEARANCE_MM / 2
    y_off = s.case_l / 2 - s.shaft_from_end
    bottom = J1_DECK_Z_MM - (s.case_h - s.tab_below_top - s.tab_thk)
    return (-half_w, half_w,
            y_off - s.case_l / 2 - SERVO_CASE_CLEARANCE_MM / 2,
            y_off + s.case_l / 2 + SERVO_CASE_CLEARANCE_MM / 2,
            bottom, 0.0)


SERVO_BOX_MM = _servo_box_mm()


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

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    # ---- the SHARED turntable contract (identical in turntable_stator.py) ----
    _set(TURRET + 'post_r', '45.0 mm',
         'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
         '           top face at its rim, az 120/180/240. The ONLY fixing there is.', 'mm')

    # ---- shell -----------------------------------------------------------------
    param('od', '190.0 mm',
          'outer diameter. CHOSEN: the ESP32 bay (x 13..69) plus its finger gaps\n'
          '           (y +-47) beside a 40.9 mm MG995 need r ~90 inside the wall.')
    param('height', '42.0 mm',
          'rim height, floor underside to rim top. Kept at the legacy 42: the bay\n'
          '           needs floor + 30 + 1.5 keep-out under a 3 mm lid, = 36.9.')
    param('wall', '3.0 mm',
          'side wall. 3.0 is also the toggle switch\'s panel limit (MEASURED\n'
          '           thread reach, legacy spec) - thicker and its nut will not start.')
    param('floor_t', '2.4 mm', 'floor - 1.5 x MIN_WALL, it is the base\'s one big flat')
    param('lid_t', '3.0 mm', 'lid thickness - base_lid.py, finishes flush at z 0')
    param('rim_t', '%.2f mm' % _MIN_WALL,
          'what is left of the wall beside the lid recess - MIN_WALL')
    param('loc', '%.2f mm' % _FIT['locational'], 'locational fit - design_rules')
    param('free', '%.2f mm' % _FIT['free'], 'free fit - design_rules')
    param('min_wall', '%.2f mm' % _MIN_WALL, 'MIN_WALL_MM - design_rules')
    # ---- posts and columns -------------------------------------------------------
    param('boss_d', '%.2f mm' % _FASTENER['M3']['boss_od'],
          'M3 insert boss - FASTENER_MM (O4.0 insert + 2.4 wall)')
    param('post_d', '%.2f mm' % TT_POST_D_MM,
          'TURRET post diameter - lib/j1_drive.TT_POST_D_MM. O8.8 -> O12.0 in the\n'
          '           2026-09-27 revision: 40 mm columns carrying the arm\'s tipping\n'
          '           moment; stiffness ~ d^4, so ~3.5x for 3.2 mm of diameter.')
    param('post_fillet', '%.2f mm' % MIN_FILLET_LOADED_MM,
          'root fillet where each turret post meets the floor - MIN_FILLET_LOADED')
    param('insert_d', '%.2f mm' % _FASTENER['M3']['insert'],
          'M3 heat-set insert bore - CALIBRATED')
    param('insert_h', '8.0 mm', 'turret post insert depth - legacy MEASURED')
    param('lid_insert_h', '6.0 mm', 'lid column insert depth - one insert length')
    param('screw_clear_d', '%.2f mm' % _FASTENER['M3']['clearance'], 'M3 clearance - FASTENER_MM')
    param('runout', '4.0 mm',
          'screw RUN-OUT below each insert. The turret screw is an M3 x 40 from\n'
          '           the ring\'s head recess (z 31.1): it ends at z -8.9, and the insert\n'
          '           bore stops at -8.0 - it would bottom and never clamp. Same for an\n'
          '           M3 x 8 through the lid into a 6.0 column insert. 4.0 covers both.')
    param('lid_r', '88.0 mm',
          'lid screw circle. At r 88 a O8.8 column reaches r 92.4 against the\n'
          '           inner wall at r 92.0 - it MERGES into the wall, no sliver.')
    # ---- ESP32 bay - MEASURED by Jonathan 2026-09-27 ---------------------------
    param('pcb_w', '%.2f mm' % PCB_W_MM, 'carrier PCB, along X - MEASURED')
    param('pcb_l', '%.2f mm' % PCB_L_MM, 'carrier PCB, along Y - MEASURED')
    param('pcb_t', '%.2f mm' % PCB_T_MM, 'carrier PCB thickness - MEASURED ("probably")')
    param('esp_h', '%.2f mm' % ESP_H_MM,
          'PCB + ESP32 + cables, BOTH faces, all-in height - MEASURED ("about")')
    param('esp_below', PREFIX + 'esp_h / 2 - ' + PREFIX + 'pcb_t / 2',
          'how much of the 30 hangs UNDER the board. ASSUMED mid-height -\n'
          '           Jonathan has not given the split. Edit this one number.')
    param('esp_keep', '1.5 mm', 'keep-out round the envelope - enclosures_electronics.md')
    param('esp_clear', '%.2f mm' % ESP_CLEAR_MM,
          'INSERTION PLAY, total, board to fences. Jonathan: "leave tolerance to\n'
          '           put it in". 0.5 a side - a PCB with cables hanging off both\n'
          '           faces goes in by hand, not by a locational fit.')
    param('esp_x0', '16.0 mm',
          'inner (servo-side) edge of the board. The MG995 window reaches x 10.60;\n'
          '           a 3.0 fence plus 2.4 of air puts the board here. Asserted.')
    param('fence_t', '%.2f mm' % FENCE_T_MM, 'corner fence wall, both legs of the L')
    param('fence_leg', '%.2f mm' % FENCE_LEG_MM, 'how far each leg of the L runs along the board edge')
    param('ledge', '%.2f mm' % LEDGE_MM, 'how far the ledge runs in under the board corner')
    param('fence_over', '%.2f mm' % FENCE_OVER_MM, 'fence height above the board top face')
    param('finger', '12.0 mm', 'finger gap past each short end of the board')
    # ---- rim -----------------------------------------------------------------------
    param('toggle_d', '13.35 mm', 'toggle switch thread O13.1 + clearance - MEASURED (legacy)')
    param('toggle_az', '165.0 deg', 'rear, away from the bay and the servo', 'deg')
    param('dc_d', '9.95 mm', 'DC cable O9.7 + clearance - MEASURED (legacy)')
    param('dc_az', '195.0 deg', 'rear, beside the toggle', 'deg')
    param('rim_z', '-21.0 mm', 'height of both rim holes - mid-wall')
    param('tie_w', '4.0 mm', 'zip-tie slot width - 2.5 tie + clearance')
    param('tie_h', '3.0 mm', 'zip-tie slot height under the bridge')
    param('tie_bridge', '3.0 mm', 'bridge bar thickness over the tie')
    param('tie_leg', '5.0 mm', 'bridge leg footprint, each side')
    param('tie_r', '76.0 mm', 'where the bridge stands - inside the DC entry')
    # ---- finish ----------------------------------------------------------------------
    param('ef', '0.4 mm', 'elephant-foot chamfer on the floor edge - design_rules')
    param('tol', '0.01 mm', 'overlap so joined solids share volume - not a dimension')

    # ---- idempotent rebuild ------------------------------------------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
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
    assert comp.name == COMPONENT, 'component came back as %r' % comp.name
    ext = comp.features.extrudeFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = 'sk_' + name
        return sk

    def profs(sk, pick=None):
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            p = sk.profiles.item(i)
            if pick is None or pick(p):
                c.add(p)
        assert c.count >= 1, sk.name + ': no profile'
        return c

    def extrude(pr, op, z0_cm, dz_cm, name):
        inp = ext.createInput(pr, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0_cm)))
        inp.setDistanceExtent(False, V(mm(dz_cm)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    def mm(cm):
        return '%.4f mm' % (cm * 10.0)

    def mxy(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def circle(name, x, y, d, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, x, y), d / 2)
        assert sk.profiles.count == 1, sk.name
        return extrude(profs(sk), op, z0, dz, name)

    def rect(name, x0, x1, y0, y1, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(mxy(sk, x0, y0), mxy(sk, x1, y1))
        assert sk.profiles.count == 1, sk.name
        return extrude(profs(sk), op, z0, dz, name)

    def ring(name, r_out, r_in, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        for r in (r_out, r_in):
            sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, 0, 0), r)
        want = math.pi * (r_out ** 2 - r_in ** 2)
        return extrude(profs(sk, lambda p: abs(p.areaProperties().area - want) < want * REL_TOL),
                       op, z0, dz, name)

    def radial_hole(name, az, d, z, r_a, r_b):
        """A horizontal hole on a RADIAL axis at azimuth az (radians), from
        radius r_a outward to r_b, centred at height z. Sketch on the plane
        through the Z axis turned to az; extrude along its normal."""
        pl_in = comp.constructionPlanes.createInput()
        pl_in.setByAngle(comp.zConstructionAxis, adsk.core.ValueInput.createByReal(az),
                         comp.yZConstructionPlane)
        pl = comp.constructionPlanes.add(pl_in)
        pl.name = 'pl_' + name
        sk = comp.sketches.add(pl)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(0.0, 0.0, z)), d / 2)
        assert sk.profiles.count == 1, sk.name
        return extrude(profs(sk), CUT, r_a, r_b - r_a, name)

    # ---- values, cm ----------------------------------------------------------------
    H = val('height')
    ro = val('od') / 2
    ri = ro - val('wall')
    r_recess = ro - val('rim_t')
    z_floor = -H + val('floor_t')           # floor top face
    z_lid = -val('lid_t')                    # lid underside = shelf
    x0 = val('esp_x0')
    x1 = x0 + val('pcb_w')
    yh = val('pcb_l') / 2
    z_pcb = z_floor + val('esp_below')       # board underside
    z_top = z_floor + val('esp_h')           # envelope top
    fence_top = z_pcb + val('pcb_t') + val('fence_over')
    c_half = val('esp_clear') / 2
    sx0, sx1, sy0, sy1, sz0, sz1 = [v / 10.0 for v in SERVO_BOX_MM]

    # ---- sanity, before any geometry --------------------------------------------------
    assert z_top + val('esp_keep') <= z_lid - TOL, (
        'the ESP32 envelope tops out at z %.2f + %.2f keep-out and the lid is at '
        '%.2f' % (z_top * 10, val('esp_keep') * 10, z_lid * 10))
    assert fence_top <= z_lid - TOL, 'the corner fences reach the lid'
    assert x0 - c_half - val('fence_t') >= sx1 + val('min_wall') - TOL, (
        'the bay\'s inner fences at x %.2f crowd the MG995 window at x %.2f'
        % ((x0 - c_half - val('fence_t')) * 10, sx1 * 10))
    _far = math.hypot(x1 + c_half + val('fence_t'), yh + val('finger'))
    assert _far <= ri - TOL, (
        'the bay + finger gap reaches r %.2f and the wall starts at r %.2f'
        % (_far * 10, ri * 10))
    assert sz0 >= z_floor + val('min_wall') - TOL, (
        'the MG995 case bottom z %.2f is too close to the floor at %.2f'
        % (sz0 * 10, z_floor * 10))
    for az in POST_AZ + LID_AZ:
        rr = tval('post_r') if az in POST_AZ else val('lid_r')
        pd = val('post_d') if az in POST_AZ else val('boss_d')
        px, py = rr * math.cos(math.radians(az)), rr * math.sin(math.radians(az))
        dx = max(x0 - c_half - val('fence_t') - px, 0.0, px - (x1 + c_half + val('fence_t')))
        dy = max(-yh - val('finger') - py, 0.0, py - (yh + val('finger')))
        assert math.hypot(dx, dy) >= pd / 2 + val('free') - TOL, (
            'the post/column at az %.0f r %.1f lands in the ESP32 bay' % (az, rr * 10))
        dx = max(sx0 - px, 0.0, px - sx1)
        dy = max(sy0 - py, 0.0, py - sy1)
        assert math.hypot(dx, dy) >= pd / 2 + val('free') - TOL, (
            'the post/column at az %.0f is in the MG995\'s way' % az)
    # THE LOOM DROPS ONTO THE BOARD. lib/j1_drive.LOOM_AZ_DEG put the stator's
    # loom window over this bay; if either moves, this says so.
    for _r in (LOOM_IR_MM / 10, LOOM_OR_MM / 10):
        for _a in (LOOM_AZ_DEG - LOOM_DEG / 2, LOOM_AZ_DEG + LOOM_DEG / 2):
            _lx = _r * math.cos(math.radians(_a))
            _ly = _r * math.sin(math.radians(_a))
            assert x0 - val('fence_t') - TOL < _lx < x1 + TOL and abs(_ly) < yh + val('finger'), (
                'the loom window (az %.0f) no longer lands over the ESP32 bay - corner '
                '(%.1f, %.1f)' % (LOOM_AZ_DEG, _lx * 10, _ly * 10))

    # ---- phase 1: shell --------------------------------------------------------------
    t0 = design.timeline.count
    circle('floor', 0.0, 0.0, ro * 2, -H, val('floor_t'), NEW)
    ring('wall', ro, ri, z_floor - val('tol'), H - val('floor_t') + val('tol'), JOIN)
    ring('lid_recess', r_recess, ri - val('tol'), z_lid, val('lid_t') + val('tol'), CUT)
    group(t0, PH_SHELL)

    # ---- phase 2: turret posts + lid columns -----------------------------------------
    t1 = design.timeline.count
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        px, py = tval('post_r') * math.cos(a), tval('post_r') * math.sin(a)
        circle('turret_post_%d' % i, px, py, val('post_d'), z_floor - val('tol'),
               -z_floor + val('tol'), JOIN)
        circle('turret_insert_%d' % i, px, py, val('insert_d'), -val('insert_h'),
               val('insert_h') + val('tol'), CUT)
        circle('turret_runout_%d' % i, px, py, val('screw_clear_d'),
               -val('insert_h') - val('runout'), val('runout') + val('tol'), CUT)
    for i, az in enumerate(LID_AZ):
        a = math.radians(az)
        px, py = val('lid_r') * math.cos(a), val('lid_r') * math.sin(a)
        circle('lid_column_%d' % i, px, py, val('boss_d'), z_floor - val('tol'),
               z_lid - z_floor + val('tol'), JOIN)
        circle('lid_insert_%d' % i, px, py, val('insert_d'), z_lid - val('lid_insert_h'),
               val('lid_insert_h') + val('tol'), CUT)
        circle('lid_runout_%d' % i, px, py, val('screw_clear_d'),
               z_lid - val('lid_insert_h') - val('runout'), val('runout') + val('tol'), CUT)
    group(t1, PH_POSTS)

    # ---- phase 3: ESP32 bay - four corner ledges inside four L fences ------------------
    # Each corner is a solid block from the floor to fence_top; then the
    # board's own outline PLUS esp_clear is cut from the board underside up,
    # which leaves a LEDGE (the part of the block under the board) and an L
    # FENCE (the part outside it). One cut makes all four.
    t2 = design.timeline.count
    for i, (sx, sy) in enumerate(CORNERS):
        cx = x0 if sx < 0 else x1
        cy = -yh if sy < 0 else yh
        # block: from ledge-inside the corner out to fence_t past the clearance
        bx = sorted([cx - sx * val('ledge'), cx + sx * (c_half + val('fence_t'))])
        by = sorted([cy - sy * val('fence_leg'), cy + sy * (c_half + val('fence_t'))])
        rect('corner_%d' % i, bx[0], bx[1], by[0], by[1], z_floor - val('tol'),
             fence_top - z_floor + val('tol'), JOIN)
    _v = comp.bRepBodies.item(0).volume
    rect('board_pocket', x0 - c_half, x1 + c_half, -yh - c_half, yh + c_half,
         z_pcb, fence_top - z_pcb + val('tol'), CUT)
    assert _v - comp.bRepBodies.item(0).volume > TOL, 'the board pocket cut nothing'
    group(t2, PH_BAY)

    # ---- phase 4: rim holes + DC strain relief ---------------------------------------------
    t3 = design.timeline.count
    radial_hole('toggle_hole', val('toggle_az'), val('toggle_d'), val('rim_z'),
                ri - val('tol') * 100, ro + val('tol') * 100)
    radial_hole('dc_hole', val('dc_az'), val('dc_d'), val('rim_z'),
                ri - val('tol') * 100, ro + val('tol') * 100)
    # zip-tie bridge: two legs either side of the cable path and a bar over a
    # tie-sized tunnel, standing on the floor just inside the DC entry.
    a = val('dc_az')
    ux, uy = math.cos(a), math.sin(a)          # radial
    vx, vy = -uy, ux                           # tangential
    tr = val('tie_r')
    half_span = val('dc_d') / 2 + val('tie_leg')
    sk = sketch(comp.xYConstructionPlane, 'tie_bridge')
    pts = []
    for (rr, tt) in ((tr - val('tie_w') / 2, -half_span), (tr + val('tie_w') / 2, -half_span),
                     (tr + val('tie_w') / 2, half_span), (tr - val('tie_w') / 2, half_span)):
        pts.append(mxy(sk, rr * ux + tt * vx, rr * uy + tt * vy))
    for k in range(len(pts)):
        sk.sketchCurves.sketchLines.addByTwoPoints(pts[k], pts[(k + 1) % len(pts)])
    assert sk.profiles.count == 1, sk.name
    extrude(profs(sk), JOIN, z_floor - val('tol'),
            val('tie_h') + val('tie_bridge') + val('tol'), 'tie_bridge')
    sk = sketch(comp.xYConstructionPlane, 'tie_tunnel')
    pts = []
    hw = val('dc_d') / 2
    for (rr, tt) in ((tr - val('tie_w'), -hw), (tr + val('tie_w'), -hw),
                     (tr + val('tie_w'), hw), (tr - val('tie_w'), hw)):
        pts.append(mxy(sk, rr * ux + tt * vx, rr * uy + tt * vy))
    for k in range(len(pts)):
        sk.sketchCurves.sketchLines.addByTwoPoints(pts[k], pts[(k + 1) % len(pts)])
    assert sk.profiles.count == 1, sk.name
    extrude(profs(sk), CUT, z_floor, val('tie_h'), 'tie_tunnel')
    group(t3, PH_RIM)

    # ---- phase 5: finish - elephant-foot chamfer on the floor's outer edge -------------------
    t4 = design.timeline.count
    body = comp.bRepBodies.item(0)
    edges = adsk.core.ObjectCollection.create()
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Circle3D) and abs(g.center.z + H) < val('tol') \
                and abs(g.radius - ro) < val('tol'):
            edges.add(e)
    assert edges.count == 1, 'expected the one floor rim edge, found %d' % edges.count
    ch_in = comp.features.chamferFeatures.createInput2()
    ch_in.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(PREFIX + 'ef'), False)
    comp.features.chamferFeatures.add(ch_in).name = 'elephant_foot'
    # root fillets on the three turret posts: the circle where each meets the
    # floor top, found by centre and radius, never by index.
    body = comp.bRepBodies.item(0)
    roots = adsk.core.ObjectCollection.create()
    for e in body.edges:
        g = e.geometry
        if not isinstance(g, adsk.core.Circle3D):
            continue
        if abs(g.center.z - z_floor) > val('tol') or abs(g.radius - val('post_d') / 2) > val('tol'):
            continue
        if abs(math.hypot(g.center.x, g.center.y) - tval('post_r')) < val('tol'):
            roots.add(e)
    assert roots.count == len(POST_AZ), (
        'expected %d post root edges, found %d' % (len(POST_AZ), roots.count))
    f_in = comp.features.filletFeatures.createInput()
    f_in.addConstantRadiusEdgeSet(roots, V(PREFIX + 'post_fillet'), False)
    comp.features.filletFeatures.add(f_in).name = 'post_root_fillets'
    group(t4, PH_FINISH)

    # ---- identity + diagnostics ---------------------------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got %d' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a_ = apps.item(j)
                if all(w.lower() in a_.name.lower() for w in want):
                    body.appearance = a_
                    used = a_.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break
    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (body.name, body.material.name, used))
    print('FRAME: z 0 = rim top = turntable_stator datum; J1 axis; az from +X')
    print('shell O%.1f x %.1f, wall %.1f, floor %.1f; lid recess O%.2f x %.1f (shelf z %.2f)'
          % (ro * 2 * 10, H * 10, val('wall') * 10, val('floor_t') * 10, r_recess * 2 * 10,
             val('lid_t') * 10, z_lid * 10))
    print('turret posts O%.1f at r %.1f az %s, insert O%.1f x %.1f, root fillet %.1f - '
          'tt_post_r contract' % (val('post_d') * 10, tval('post_r') * 10, POST_AZ,
                                  val('insert_d') * 10, val('insert_h') * 10,
                                  val('post_fillet') * 10))
    print('screw run-out: O%.1f x %.1f below every insert - M3 x 40 turret, M3 x 8 lid'
          % (val('screw_clear_d') * 10, val('runout') * 10))
    print('lid columns O%.1f at r %.1f az %s, insert O%.1f x %.1f, top z %.2f'
          % (val('boss_d') * 10, val('lid_r') * 10, LID_AZ, val('insert_d') * 10,
             val('lid_insert_h') * 10, z_lid * 10))
    print('MG995 (J1) keep-out: x %.2f..%.2f y %.2f..%.2f z %.2f..0 - %.2f above the floor'
          % (sx0 * 10, sx1 * 10, sy0 * 10, sy1 * 10, sz0 * 10, (sz0 - z_floor) * 10))
    print('ESP32 BAY: board %.0f x %.0f x %.1f at x %.1f..%.1f y +-%.1f, underside z %.2f '
          '(%.1f under it, ASSUMED mid)' % (val('pcb_w') * 10, val('pcb_l') * 10,
                                           val('pcb_t') * 10, x0 * 10, x1 * 10, yh * 10,
                                           z_pcb * 10, val('esp_below') * 10))
    print('  envelope z %.2f..%.2f (+%.1f keep-out) under the lid at %.2f; insertion play '
          '%.1f total; 4 corner ledges %.1f in, L fences %.1f thick to z %.2f'
          % (z_floor * 10, z_top * 10, val('esp_keep') * 10, z_lid * 10,
             val('esp_clear') * 10, val('ledge') * 10, val('fence_t') * 10, fence_top * 10))
    print('  sides OPEN between the corners - the bottom-face cables come out and up; '
          'finger gaps %.0f past each short end reach r %.1f of %.1f'
          % (val('finger') * 10, _far * 10, ri * 10))
    print('RIM: toggle O%.2f at az %.0f, DC pass-through O%.2f at az %.0f, both z %.1f; '
          'zip-tie bridge at r %.0f' % (val('toggle_d') * 10, math.degrees(val('toggle_az')),
                                          val('dc_d') * 10, math.degrees(val('dc_az')),
                                          val('rim_z') * 10, val('tie_r') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.1f | printed ~%.0f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.volume * PETG_G_CM3 * PRINT_FILL, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
