"""robotarm/_gauge_verify - ONLY what is untested AND blocks a part.

Jonathan, looking at two full plates: "we didn't use all of these last
time - are we printing everything". He was right. Of the fifteen stations
across gauge_flange and gauge_horn, ten are answered (calipered on the
bench) or gate nothing. Printing them again is filament spent to re-learn
what is already written down.

This plate is the other four. Every one is a FIX THAT HAS NEVER BEEN
PRINTED, or the last number in the project that is still DERIVED:

  MG90S lobe   the forearm's own window, at 1:1 - this pad plus the base
               IS fa_lobe_t. Carries the LEAD KEYWAY (untested) and the
               Ø1.8 pilots at the DERIVED 27.5 pitch (the last derived
               number anywhere in the project). Two answers, one station.
  SG90 seat    the same window wrist_roll / turntable_stator / gripper_shell
               cut, with its keyway. Untested.
  MG995 bed    the corrected 20.4 width - it was cut 20.2 against a
               MEASURED 20.2 case and read line-to-line - plus its keyway
               and the four tab slots.
  FLEX         the gripcut finger's hairpin leaf. Never run, and it is the
               only thing gating the fingers.

THE CROSS STATION IS DELETED, 2026-08-31, AND THIS IS THE ENTRY FOR IT.
It replicated the turret rotor's four-arm horn pocket - tapered slots 6.04 at
r 6.5 down to 4.84 at the trim line, an Ø13 root relief, ticks at +-16.4. J1
does not have that pocket any more. turntable_stator and shoulder_bracket cut
a BOLTED SPLINE HUB now (specs/robotarm/j1_hub.md), and tt_horn_w_root,
tt_horn_w_tip, tt_horn_r_root and tt_horn_z do not exist as parameters. The
cross-check above them was written `if p is not None`, so the day they went it
stopped checking anything and said nothing about it - a station gauging an
interface that does not ship, guarded by a test that cannot fail. That is
worse than a station that is simply wrong, because the wrong one gets caught.

Deleted rather than repaired: there is nothing to repair it INTO. The hub's
interface is a broach bore and a bolt circle, and neither is a drop-in test -
a broach bore is gauged by a bore SWEEP on a stub (the acceptance item that
blocks j1_hub.md), and a bolt circle with 1.00 mm of deliberate radial float
has nothing to fit. The whole horn plate, _gauge_horn.py, went the same way
on the same day and for the same reason.

DELIBERATELY NOT HERE: both hub sweeps (calipered 6.8 and 8.7), the blade
and arm combs (calipered), the pin pairs (nothing structural reads hole
pitch), and the WRIST / MG995 STACK replicas (they derive from measured
values now, so they would confirm arithmetic rather than discover
anything).

Every servo number is READ from lib/servo.py. None is retyped - a gauge
that has drifted from the library certifies the wrong number and you
believe it, which is worse than having no gauge.

Print: PETG, 0.2 layers, 3 walls, SUPPORT OFF, engraved face UP.
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

from lib.servo import CATALOG, MG995_TAB_SLOT_X_MM  # noqa: E402

COMPONENT = 'robotarm_gauge_verify'
PREFIX = 'gv_'
PHASES = ['plate', 'servo windows', 'flexure', 'labels']
MATERIAL_NAME = 'PET Plastic'
PETG = 1.27
SOLID = 0.65

_SG, _MG, _M9 = CATALOG['SG90'], CATALOG['MG90S'], CATALOG['MG995']
LOC = 0.2
KEY_OUT = 2.0          # how far the notch runs PAST the pad edge, to daylight
KEY_D_MICRO = _SG.lead_bundle_dia + LOC
KEY_D_M9 = _M9.lead_bundle_dia + LOC

# THE LEAD LEAVES THE SHORT END FACE, centred (lib/servo.py lead datum).
# v1 of this plate notched the two LONG walls either side of that face, at
# both ends - which is what made every window read as a capital I, and what
# Jonathan caught: "thats not on the right side its on the short side".
# One notch per station now, in the END wall, centred, running out to
# daylight. Insert each servo with its OUTPUT SHAFT toward the notch.

MG90S_LOBE_T = _MG.tab_below_top + _MG.tab_thk      # == fa_lobe_t
MG90S_PITCH_OLD = 29.0
PILOT_D = 1.8
SG90_TAB_THK = _SG.tab_thk

# flexure coupon - gripcut_finger's gf_ params (asserted when present)
FLEX_T, FLEX_W, FLEX_OUT_X = 1.2, 6.0, 4.5
FLEX_FOLD_Y, FLEX_FOLD_IR, FLEX_RET_Y, FLEX_ANCHOR_Y = 18.0, 1.5, 6.3, 3.2
FLEX_MARKS = [2.5, 4.5]


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
        return ups.itemByName(PREFIX + name).value * 10

    param('base_t', '2.4 mm', 'plate away from the stations')
    param('label_z', '0.6 mm', 'engraving depth - design_rules MIN_EMBOSS_MM')

    # THE GAUGE MUST TEST WHAT THE PARTS SHIP, OR IT TESTS NOTHING. This is
    # still opportunistic - a gauge plate is normally built in its own empty
    # document, where none of these parameters exist - but the SKIP IS NO
    # LONGER SILENT. The four tt_horn_* names that used to head this list
    # were deleted along with the J1 horn, and because the guard could not
    # fail, the plate went on certifying a pocket that no part cuts and said
    # nothing. A guarded check that reports 'not checked' is a check; one
    # that reports nothing is decoration. Every name here is a parameter some
    # live part still declares - if one stops being that, delete it and the
    # station it belongs to, do not leave it to skip.
    checked, absent = [], []
    for full, ours in (('gf_t', FLEX_T), ('gf_leaf_w', FLEX_W),
                       ('gf_out_x', FLEX_OUT_X), ('gf_fold_y', FLEX_FOLD_Y)):
        p = ups.itemByName(full)
        if p is None:
            absent.append(full)
            continue
        checked.append(full)
        assert abs(p.value * 10 - ours) < 1e-6, (
            'gauge %s = %.2f but the live part says %.2f - this plate '
            'would certify an interface that does not ship'
            % (full, ours, p.value * 10))

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
    assert comp.name == COMPONENT, 'a stale component reserves the name'
    ext = comp.features.extrudeFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mm(x):
        return '%.4f mm' % x

    def pt(sk, x, y):
        return sk.modelToSketchSpace(P3(x / 10.0, y / 10.0, 0))

    def ex(profs, op, z0, dz, name, targets=None):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0)))
        inp.setDistanceExtent(False, V(mm(dz)))
        if op != NEW:
            inp.participantBodies = targets if targets is not None else [
                comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def one(sk):
        assert sk.profiles.count == 1, sk.name + ': %d profiles' % sk.profiles.count
        c = adsk.core.ObjectCollection.create()
        c.add(sk.profiles.item(0))
        return c

    def rect(name, x0, x1, y0, y1, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(sk, x0, y0), pt(sk, x1, y1))
        return ex(one(sk), op, z0, dz, name, targets)

    def circle(name, x, y, d, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, x, y), d / 20.0)
        return ex(one(sk), op, z0, dz, name, targets)

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(
                start, design.timeline.count - 1).name = name

    # ---- layout, mm --------------------------------------------------------
    BASE_X, BASE_Y = 96.0, 130.0
    base_t = val('base_t')

    M9_Y = 50.0
    m9_wx = (_M9.case_l + LOC) / 2
    m9_wy = (_M9.case_w + LOC) / 2
    m9_stop = _M9.case_l / 2 + LOC / 2
    m9_slot_cx, m9_slot_cy = _M9.tab_hole_pitch / 2, 10.2 / 2

    SG_Y = 22.0
    sg_wx = (_SG.case_l + LOC) / 2
    sg_wy = (_SG.case_w + LOC) / 2
    sg_rx = (_SG.tab_span + LOC) / 2
    sg_seat_h = SG90_TAB_THK + LOC
    sg_pad = (-sg_rx - 4.0, sg_rx + 4.0, SG_Y - 9.0, SG_Y + 9.0)

    MG_X, MG_Y = -30.0, -10.0
    mg_wx = (_MG.case_w + LOC) / 2
    mg_wy = (_MG.case_l + LOC) / 2
    mg_pad = (MG_X - 11.0, MG_X + 11.0, MG_Y - 18.0, MG_Y + 18.0)
    mg_pad_h = MG90S_LOBE_T - base_t

    # THE PLATE OUTLINE IS UNCHANGED with the cross station gone, and that is
    # deliberate. Every layout assert below is proved against these
    # coordinates; re-laying four stations out on a smaller plate is a change
    # that can only be checked by printing it, and this plate exists to
    # answer four questions, not to be the tidiest possible rectangle. The
    # right-hand band from y -31 to +7 is now free for whoever needs a
    # station next - it held the cross pad.
    FX0, FY0 = -14.0, -56.0

    # Where each end-wall notch STOPS: past the raised pad (or past the MG995
    # rails, which is the only raised thing that station has) by KEY_OUT, so
    # the cable always reaches daylight. A notch that ends inside the pad is a
    # blind pocket and traps the cable exactly as a solid wall would.
    m9_key_out = -26.0 - KEY_OUT
    sg_key_out = sg_pad[0] - KEY_OUT
    mg_key_out = mg_pad[2] - KEY_OUT

    # ---- sanity ------------------------------------------------------------
    GAP = 2.0
    # The cable leaves the END face, so it costs LENGTH, not width. The v1
    # asserts charged it against case_w and passed while the notches were on
    # the wrong walls entirely - an assert on the wrong axis is worse than no
    # assert, because it reads like proof.
    for tag, win_len, notch_len, spec in (
            ('MG995', 2 * m9_wx, -m9_wx - m9_key_out, _M9),
            ('SG90', 2 * sg_wx, -sg_wx - sg_key_out, _SG),
            ('MG90S', 2 * mg_wy, (MG_Y - mg_wy) - mg_key_out, _MG)):
        assert win_len + notch_len >= spec.case_l + spec.lead_bundle_dia, (
            'the %s station passes %.1f along the case and the servo with its '
            'cable is %.1f long - it cannot be threaded in'
            % (tag, win_len + notch_len, spec.case_l + spec.lead_bundle_dia))
        assert notch_len >= KEY_OUT, '%s notch does not clear its pad' % tag
    assert 2 * m9_wx >= _M9.case_l + LOC - 1e-9, 'MG995 window shorter than the case'
    assert 2 * m9_wy >= _M9.case_w + LOC - 1e-9, 'MG995 window narrower than the case'
    assert 2 * sg_wy >= _SG.case_w + LOC - 1e-9, 'SG90 window narrower than the case'
    assert 2 * mg_wx >= _MG.case_w + LOC - 1e-9, 'MG90S window narrower than the case'
    assert abs(mg_pad_h + base_t - MG90S_LOBE_T) < 1e-9, 'the MG90S pad is not fa_lobe_t'
    assert _MG.tab_hole_pitch / 2 > mg_wy + PILOT_D / 2 + 0.4, 'pilots break into the window'
    assert M9_Y + m9_wy + 3.0 < BASE_Y / 2 - 1.0, 'MG995 bed off the top'
    assert sg_pad[3] + GAP < M9_Y - m9_wy - 3.0, 'SG90 pad touches the MG995 bed'
    assert mg_pad[3] + GAP < sg_pad[2], 'MG90S pad touches the SG90 pad'

    # ---- phase 1: plate ----------------------------------------------------
    t0 = design.timeline.count
    rect('base', -BASE_X / 2, BASE_X / 2, -BASE_Y / 2, BASE_Y / 2, 0.0, base_t, NEW)
    plate = comp.bRepBodies.item(0)
    plate.name = 'gauge_verify_plate'
    group(t0, PHASES[0])

    # ---- phase 2: the three servo windows, each with its keyway ------------
    t1 = design.timeline.count
    # MG995 bed
    rect('m9_window', -m9_wx, m9_wx, M9_Y - m9_wy, M9_Y + m9_wy,
         -1.0, base_t + 2.0, CUT, [plate])
    for sy in (+1, -1):
        rect('m9_rail_%s' % ('p' if sy > 0 else 'm'), -26.0, 26.0,
             M9_Y + sy * m9_wy, M9_Y + sy * (m9_wy + 3.0), base_t, 3.0, JOIN, [plate])
    rect('m9_stop', m9_stop, m9_stop + 3.0, M9_Y - 2.5, M9_Y + 2.5,
         base_t, 3.0, JOIN, [plate])
    for sx in (+1, -1):
        for sy in (+1, -1):
            rect('m9_slot_%s%s' % ('p' if sx > 0 else 'm', 'p' if sy > 0 else 'm'),
                 sx * m9_slot_cx - MG995_TAB_SLOT_X_MM / 2,
                 sx * m9_slot_cx + MG995_TAB_SLOT_X_MM / 2,
                 M9_Y + sy * m9_slot_cy - _M9.tab_thk / 2,
                 M9_Y + sy * m9_slot_cy + _M9.tab_thk / 2,
                 -1.0, base_t + 2.0, CUT, [plate])
    rect('m9_key', m9_key_out, -m9_wx,
         M9_Y - KEY_D_M9 / 2, M9_Y + KEY_D_M9 / 2,
         -1.0, base_t + 2.0, CUT, [plate])

    # SG90 seat
    rect('sg_pad', sg_pad[0], sg_pad[1], sg_pad[2], sg_pad[3],
         0.0, base_t + sg_seat_h, JOIN, [plate])
    rect('sg_recess', -sg_rx, sg_rx, SG_Y - sg_wy, SG_Y + sg_wy,
         base_t + sg_seat_h, -sg_seat_h, CUT, [plate])
    rect('sg_window', -sg_wx, sg_wx, SG_Y - sg_wy, SG_Y + sg_wy,
         base_t, -base_t - 1.0, CUT, [plate])
    rect('sg_key', sg_key_out, -sg_wx,
         SG_Y - KEY_D_MICRO / 2, SG_Y + KEY_D_MICRO / 2,
         base_t + sg_seat_h + 1.0, -base_t - sg_seat_h - 2.0, CUT, [plate])
    for sx in (+1, -1):
        rect('sg_sight_%s' % ('p' if sx > 0 else 'm'),
             sx * _SG.tab_hole_pitch / 2 - 0.2, sx * _SG.tab_hole_pitch / 2 + 0.2,
             SG_Y - sg_wy, SG_Y + sg_wy, base_t, -val('label_z'), CUT, [plate])

    # MG90S lobe - 1:1 with the forearm
    rect('mg_pad', mg_pad[0], mg_pad[1], mg_pad[2], mg_pad[3],
         0.0, base_t + mg_pad_h, JOIN, [plate])
    mg_top = base_t + mg_pad_h
    rect('mg_window', MG_X - mg_wx, MG_X + mg_wx, MG_Y - mg_wy, MG_Y + mg_wy,
         mg_top, -mg_top - 1.0, CUT, [plate])
    rect('mg_key', MG_X - KEY_D_MICRO / 2, MG_X + KEY_D_MICRO / 2,
         mg_key_out, MG_Y - mg_wy,
         mg_top + 1.0, -mg_top - 2.0, CUT, [plate])
    for sy in (+1, -1):
        circle('mg_pilot_%s' % ('p' if sy > 0 else 'm'),
               MG_X, MG_Y + sy * _MG.tab_hole_pitch / 2, PILOT_D,
               mg_top, -mg_top - 1.0, CUT, [plate])
        for tag, pitch in (('275', _MG.tab_hole_pitch), ('29', MG90S_PITCH_OLD)):
            for sx in (+1, -1):
                rect('mg_sight%s_%s%s' % (tag, 'p' if sy > 0 else 'm',
                                          'p' if sx > 0 else 'm'),
                     MG_X + sx * (_MG.case_w / 2 + 0.5),
                     MG_X + sx * (_MG.case_w / 2 + 3.5),
                     MG_Y + sy * pitch / 2 - 0.2, MG_Y + sy * pitch / 2 + 0.2,
                     mg_top, -val('label_z'), CUT, [plate])
    group(t1, PHASES[1])

    # ---- phase 3: the flexure coupon ---------------------------------------
    t2 = design.timeline.count
    ox0 = FY0 + FLEX_OUT_X
    ox1 = ox0 + FLEX_T
    fc = ox1 + FLEX_FOLD_IR
    rx0 = fc + FLEX_FOLD_IR
    rx1 = rx0 + FLEX_T
    anchor = (FX0 - 8.0, FX0 + FLEX_ANCHOR_Y, FY0 + 1.5, FY0 + 11.0)
    ax1 = FX0 + FLEX_ANCHOR_Y
    fx_fold = FX0 + FLEX_FOLD_Y
    ret_end = FX0 + FLEX_RET_Y
    tip_x0 = ret_end
    assert rx1 < anchor[3], 'the leaf runs outside its anchor face'
    assert fx_fold + FLEX_FOLD_IR + FLEX_T + 1.0 < BASE_X / 2, 'the fold runs off the plate'
    assert anchor[2] > -BASE_Y / 2 + 1.0, 'the anchor runs off the bottom'

    rect('flex_anchor', anchor[0], anchor[1], anchor[2], anchor[3],
         base_t, FLEX_W, JOIN, [plate])
    sk = sketch('flex_leaf')
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    lines.addByTwoPoints(pt(sk, ax1, ox0), pt(sk, fx_fold, ox0))
    arcs.addByThreePoints(pt(sk, fx_fold, ox0),
                          pt(sk, fx_fold + FLEX_FOLD_IR + FLEX_T, fc),
                          pt(sk, fx_fold, rx1))
    lines.addByTwoPoints(pt(sk, fx_fold, rx1), pt(sk, ret_end, rx1))
    lines.addByTwoPoints(pt(sk, ret_end, rx1), pt(sk, ret_end, rx0))
    lines.addByTwoPoints(pt(sk, ret_end, rx0), pt(sk, fx_fold, rx0))
    arcs.addByThreePoints(pt(sk, fx_fold, rx0), pt(sk, fx_fold + FLEX_FOLD_IR, fc),
                          pt(sk, fx_fold, ox1))
    lines.addByTwoPoints(pt(sk, fx_fold, ox1), pt(sk, ax1, ox1))
    lines.addByTwoPoints(pt(sk, ax1, ox1), pt(sk, ax1, ox0))
    ex(one(sk), JOIN, base_t, FLEX_W, 'flex_leaf', [plate])
    rect('flex_tip', tip_x0 - 2.0, tip_x0 + 2.5, rx0, rx1 + 2.0,
         base_t, FLEX_W, JOIN, [plate])
    tick_x0 = tip_x0 + 3.5
    rest_y = rx1 + 2.0
    for d in [0.0] + FLEX_MARKS:
        rect('flex_tick_%02d' % int(d * 10), tick_x0, tick_x0 + 4.0,
             rest_y + d - 0.2, rest_y + d + 0.2, base_t, -val('label_z'), CUT, [plate])
    group(t2, PHASES[2])

    # ---- phase 4: labels ---------------------------------------------------
    t3 = design.timeline.count

    def engrave(items, z_top):
        for j, (x, y, txt) in enumerate(items):
            sk2 = sketch('lab_%d' % j)
            t_in = sk2.sketchTexts.createInput2(txt, 0.35)
            t_in.setAsMultiLine(
                pt(sk2, x - 26.0, y - 3.0), pt(sk2, x + 26.0, y + 3.0),
                adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            st = sk2.sketchTexts.add(t_in)
            inp = ext.createInput(st, CUT)
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z_top)))
            inp.setDistanceExtent(False, V(mm(-val('label_z'))))
            inp.participantBodies = [plate]
            ext.add(inp).name = 'lab_%d' % j
        return len(items)

    # every label sits on the BASE plate, never on a raised pad - a 0.6 deep
    # cut inside a pad footprint would gouge a slot through its middle. The
    # three servo stations label to the LEFT because the plate has no vertical
    # room below them: the first draft ran MG90S off the edge and drove
    # VERIFY V1 straight through the MG995 rails.
    LABELS = [
        (-38.0, M9_Y - 7.0, 'MG995'),
        (-36.0, SG_Y, 'SG90'),
        (MG_X + 16.0, mg_pad[2] - 3.5, 'MG90S 27.5'),
        (FX0 + 12.0, FY0 - 5.0, 'FLEX 0 25 45'),
        # V3, NOT V3-shaped-like-V2. The plate has physically changed - the
        # CROSS station is gone - and two different plates engraved with the
        # same name is exactly how a superseded gauge gets picked up off the
        # bench and believed. Bump this whenever a station is added or removed.
        (30.0, -50.0, 'VERIFY V3'),
    ]
    _PADS = [('MG995 rails', -26.0, 26.0, M9_Y - m9_wy - 3.0, M9_Y + m9_wy + 3.0),
             ('SG90 pad', sg_pad[0], sg_pad[1], sg_pad[2], sg_pad[3]),
             ('MG90S pad', mg_pad[0], mg_pad[1], mg_pad[2], mg_pad[3])]
    _PADS += [('MG995 keyway', m9_key_out, -m9_wx,
               M9_Y - KEY_D_M9 / 2, M9_Y + KEY_D_M9 / 2),
              ('SG90 keyway', sg_key_out, -sg_wx,
               SG_Y - KEY_D_MICRO / 2, SG_Y + KEY_D_MICRO / 2),
              ('MG90S keyway', MG_X - KEY_D_MICRO / 2, MG_X + KEY_D_MICRO / 2,
               mg_key_out, MG_Y - mg_wy)]
    for lx, ly, txt in LABELS:
        half_w = 1.35 * len(txt)      # measured from the v1 render, per char
        assert abs(lx) + half_w < BASE_X / 2 - 1.0, txt + ' runs off the plate'
        assert abs(ly) + 2.0 < BASE_Y / 2 - 1.0, txt + ' runs off the plate'
        for pn, px0, px1, py0, py1 in _PADS:
            clear = (lx + half_w < px0 or lx - half_w > px1
                     or ly + 2.0 < py0 or ly - 2.0 > py1)
            assert clear, '%r would engrave into the %s' % (txt, pn)
    n_lab = engrave(LABELS, base_t)
    group(t3, PHASES[3])

    # ---- identity ----------------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a station is floating' % comp.bRepBodies.count)
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            plate.material = m
            break
    bb = plate.boundingBox
    vol = plate.volume * 1000
    print('component: %r | FOUR stations, every one untested AND blocking'
          % comp.name)
    print('  cross-checked against live parameters: %s'
          % (', '.join(checked) if checked else 'NONE'))
    print('  NOT cross-checked, not in this document: %s'
          % (', '.join(absent) if absent else 'none'))
    print('  MG995 KEY  window %.1f x %.1f (case %.1f x %.1f MEASURED), END notch '
          '%.1f wide x %.1f long'
          % (2 * m9_wx, 2 * m9_wy, _M9.case_l, _M9.case_w, KEY_D_M9,
             -m9_wx - m9_key_out))
    print('  SG90 KEY   window %.1f x %.1f, END notch %.1f x %.1f, tab recess %.1f deep'
          % (2 * sg_wx, 2 * sg_wy, KEY_D_MICRO, -sg_wx - sg_key_out, sg_seat_h))
    print('  MG90S KEY  window %.1f x %.1f through %.2f (= fa_lobe_t), END notch '
          '%.1f x %.1f, pilots %.1f at the DERIVED %.1f'
          % (2 * mg_wx, 2 * mg_wy, MG90S_LOBE_T, KEY_D_MICRO,
             (MG_Y - mg_wy) - mg_key_out, PILOT_D, _MG.tab_hole_pitch))
    print('  FLEX       t %.1f x w %.1f hairpin, marks at %s (0.67-0.99 N = 68-101 g)'
          % (FLEX_T, FLEX_W, FLEX_MARKS))
    print('NOT HERE, and deliberately: both hub sweeps, blade and arm combs, pin')
    print('  pairs, WRIST and MG995 STACK replicas - all calipered or gating nothing.')
    print('GONE 2026-08-31: the CROSS station. J1 has no horn pocket - it has a')
    print('  bolted spline hub (specs/robotarm/j1_hub.md), and the tt_horn_*')
    print('  parameters it cross-read no longer exist. Nothing on this plate')
    print('  gauges a servo horn any more, and neither does the project.')
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume %.0f mm3 | PETG solid %.1f g | at %.0f%% ~%.1f g | labels %d'
          % (vol, vol * PETG / 1000, SOLID * 100, vol * PETG * SOLID / 1000, n_lab))
    print('valid: %s | sketches: %d' % (plate.isValid, comp.sketches.count))
