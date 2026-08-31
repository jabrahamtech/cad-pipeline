"""robotarm/_gauge_horn - the horn plate: drop YOUR horns into the CAD's holes.

The 2026-08-27 horn audit rewrote every horn number from community-model
sources, and the flange plate that already printed (v1) predates it - its
hub bores bracket the OLD invented guess. This plate is horn-only, and it
does not gauge dimensions one at a time: each station is the ACTUAL horn
interface a part ships, so the test is the assembly, not the number. All
arm slots run open-ended off their pads, so UNTRIMMED horns drop straight
in - engraved ticks mark where the arms get trimmed for the real parts.

STATIONS
--------
  CROSS       the J1 rotor's horn pocket, verbatim from shoulder_bracket:
              cross slots 3.4 wide x 2.4 deep, O13 root relief, O6.0 screw
              bore. Drop the SG90 4-arm horn in BLADE DOWN: it must seat
              with nothing proud of the pad top (0.4 of designed daylight
              over the blade). Ticks at +-16.4: the trim line. If the arms
              wedge in the slots, tt_horn_w is tight; if the root binds,
              the O13 relief is small; proud = pocket too shallow, and the
              rotor would ride the horn instead of the race.
  MG995 STACK the shoulder_hub interface, inverted: hub bore O14.2 x 3.9
              under blade slots 6.65 x 2.6. Drop the MG995 horn in HUB
              DOWN: hub disappears, blade lands in the slots ~0.1 under
              flush. Ticks at +-7.6: the trim line. This is the interface
              the 2.0 J2 standoff was sized around.
  WRIST       the wrist_rotator / gripper_pinion interface: hub pocket
              O8.15 x 3.2 with the 5.65 x 2.1 arm slot across it. Drop a
              micro horn in BLADE DOWN. Ticks at +-6.0.
  HUB u       micro hub bores 7.4 / 7.8 / 8.2 / 8.6 - finer sweep than the
              flange plate's, centred on the audit's O8.0. Smallest bore
              that takes the hub = hub O.
  HUB M       MG995 hub bores 13.2 / 13.8 / 14.4.
  BLADE       comb 1.8 / 2.0 / 2.2 / 2.5 / 2.7 - blade edge-in. Covers the
              micro 2.0 and the MG995 2.5 in one bar.
  PINS        two printed pin pairs: 2.0 c-c O1.2 (micro hole pitch) and
              2.3 c-c O1.3 (MG995). Drop an arm over a pair: both pins in
              both holes = pitch and hole O confirmed together. Pins are
              4 mm and fragile - they are a gauge, not a handle.

Print: PETG, 0.2 layers, 3 walls, SUPPORT OFF, engraved face UP - the
same profile as every gauge. Record in calibration/ dated; promote
lib/servo.py horn values to MEASURED and re-run the gates.
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

from lib.servo import CATALOG  # noqa: E402

COMPONENT = 'robotarm_gauge_horn'
PREFIX = 'gh_'
PH_PLATE = 'plate'
PH_REPLICA = 'interface replicas'
PH_SWEEPS = 'sweeps and pins'
PH_LABELS = 'labels'
PHASES = [PH_PLATE, PH_REPLICA, PH_SWEEPS, PH_LABELS]
MATERIAL_NAME = 'PET Plastic'
PETG_FILAMENT_DENSITY = 1.27
SOLID_FRACTION = 0.65

# ---- the numbers under test - every one traces to a part or lib/servo.py --
# turret cross pocket, tt_ contract (shoulder_bracket / turntable_stator)
CROSS_W_ROOT = 6.04           # tapered now - MEASURED arm + 0.4
CROSS_W_TIP = 4.84
CROSS_R_ROOT = 6.5
CROSS_Z = 2.4
CROSS_RELIEF_D = 13.0
CROSS_SCREW_D = 6.0
CROSS_TRIM_R = 16.4           # tt_horn_span / 2
# shoulder_hub MG995 interface
SH_HUB_BORE = 9.10   # tracks shoulder_hub after the MEASURED 8.7 hub
                     # (was 14.2, for a modelled 13.8 - 5 mm out)
SH_HUB_DEPTH = 3.9            # hub 3.8 + 0.1
SH_ARM_W = 6.65
SH_ARM_DEPTH = 2.30  # MEASURED MG995 blade 2.2 + 0.1 (was 2.5 + 0.1)
SH_TRIM_R = 7.6
# wrist_rotator / gripper_pinion micro interface
WR_HUB_BORE = 6.95   # tracks wrist_rotator/gripper_pinion after
                     # the MEASURED 6.8 hub (was 8.15, for a modelled 8.0)
WR_HUB_DEPTH = 3.2            # hub 3.0 + 0.1 + a hair for the drop test
WR_ARM_W = 5.65
WR_ARM_DEPTH = 2.1
WR_TRIM_R = 6.0
# sweeps
HUB_U = [6.2, 6.6, 7.0, 7.4]      # RE-CENTRED on the MEASURED 6.8. The old
                                  # 7.4-8.6 row overshot every bore - still an
                                  # answer, but a slower one than a bracket.
HUB_M = [8.2, 8.7, 9.2]           # RE-CENTRED on the MEASURED 8.7 (was 13.2-14.4,
                                  # bracketing a hub that does not exist)
BLADE_W = [1.8, 2.0, 2.2, 2.5, 2.7]
PIN_PAIRS = [(2.0, 1.2, 'micro'), (2.3, 1.3, 'mg995')]
PIN_H = 4.0


# A SWEEP THAT DOES NOT BRACKET ITS TARGET IS A WASTED PLATE. Both hub
# rows overshot on 2026-08-28 - every bore took its hub loosely - which
# was still an answer, but a slower one than a bracketing sweep. Assert
# the brackets against the library so a stale sweep cannot be printed.
_MICRO_HUB = CATALOG['SG90'].horn_hub_dia
_M9_HUB = CATALOG['MG995'].horn_hub_dia
_M9_BLADE = CATALOG['MG995'].horn_blade_thk
assert min(HUB_U) <= _MICRO_HUB <= max(HUB_U), (
    'the micro hub sweep %s does not bracket the MEASURED hub %.2f - it '
    'cannot answer anything' % (HUB_U, _MICRO_HUB))
assert min(HUB_M) <= _M9_HUB <= max(HUB_M), (
    'the MG995 hub sweep %s does not bracket the MEASURED hub %.2f'
    % (HUB_M, _M9_HUB))
assert min(BLADE_W) <= _M9_BLADE <= max(BLADE_W), (
    'the blade comb %s does not bracket the MEASURED MG995 blade %.2f'
    % (BLADE_W, _M9_BLADE))


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

    param('base_t', '2.4 mm', 'plate away from the stations')
    param('label_z', '0.6 mm', 'engraving depth - design_rules MIN_EMBOSS_MM')

    # cross-file contract checks, when the parts are in this document
    for full, ours in (('tt_horn_w_root', CROSS_W_ROOT),
                       ('tt_horn_w_tip', CROSS_W_TIP),
                       ('tt_horn_r_root', CROSS_R_ROOT), ('tt_horn_z', CROSS_Z),
                       ('sb_root_relief_d', CROSS_RELIEF_D),
                       ('tt_screw_bore', CROSS_SCREW_D),
                       ('sh_horn_hub_d', SH_HUB_BORE),
                       ('sh_horn_arm_w', SH_ARM_W),
                       ('sh_horn_arm_r', SH_TRIM_R)):
        p = ups.itemByName(full)
        if p is not None:
            assert abs(p.value * 10 - ours) < 1e-6, (
                'gauge %s = %.2f but the live part says %.2f - the gauge '
                'would test an interface that does not ship' % (full, ours, p.value * 10))

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE (PLAYBOOK) -----------
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
    assert comp.name == COMPONENT, 'a stale component still reserves the name'
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

    def extrude_profs(profs, op, z0, dz, name, targets=None):
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
        assert sk.profiles.count == 1, (
            sk.name + ': expected 1 profile, got %d' % sk.profiles.count)
        c = adsk.core.ObjectCollection.create()
        c.add(sk.profiles.item(0))
        return c

    def circle(name, x, y, d, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, x, y), d / 20.0)
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

    # ---- layout, MILLIMETRES, plate centred on origin -----------------------
    BASE_X, BASE_Y = 96.0, 90.0
    base_t = val('base_t')

    CR_X, CR_Y = -24.0, 24.0          # cross replica
    cr_half = 19.0                    # pad 38 x 38
    cr_pad_h = 4.0                    # pocket 2.4 leaves a 1.6 floor above base? no:
                                      # pocket cut into pad top; floor = pad_h - CROSS_Z + base
    ST_X, ST_Y = 30.0, 24.0           # MG995 stack pocket
    st_pad_d = 26.0
    st_pad_h = SH_ARM_DEPTH + SH_HUB_DEPTH + 1.6 - base_t   # floor 1.6 total with base

    WRI_X, WRI_Y = -36.0, -8.0        # wrist replica
    wri_pad_d = 17.0
    wri_pad_h = 4.0

    HU_X, HU_Y = -1.0, -8.0           # micro hub sweep
    hu_pad = (HU_X - 22.0, HU_X + 22.0, HU_Y - 6.5, HU_Y + 6.5)
    HU_DX = [-16.5, -5.5, 5.5, 16.5]
    hu_pad_h = 2.6

    BL_X, BL_Y = 35.5, -8.0           # blade comb
    bl_bar = (BL_X - 11.5, BL_X + 11.5, BL_Y - 5.0, BL_Y + 5.0)
    BL_DX = [-8.8, -4.4, 0.0, 4.4, 8.8]
    bl_h = 8.0
    bl_depth = 6.0

    HM_X, HM_Y = -16.0, -30.0         # MG995 hub sweep
    hm_pad = (HM_X - 28.0, HM_X + 28.0, HM_Y - 8.0, HM_Y + 8.0)
    HM_DX = [-17.0, 0.0, 17.0]
    hm_pad_h = 3.0

    PIN_X, PIN_Y = 30.0, -30.0        # pitch pin pairs
    pin_pad = (PIN_X - 10.0, PIN_X + 10.0, PIN_Y - 8.0, PIN_Y + 8.0)
    pin_pad_h = 1.6

    # ---- sanity -------------------------------------------------------------
    GAP = 2.0
    assert CR_X + cr_half + GAP < ST_X - st_pad_d / 2, 'cross pad touches the stack pad'
    assert CR_Y + cr_half < BASE_Y / 2 - 1.0 and ST_Y + st_pad_d / 2 < BASE_Y / 2 - 1.0, \
        'top row off the plate'
    assert CROSS_RELIEF_D / 2 + 1.6 < cr_half, 'no wall around the cross root relief'
    assert CROSS_TRIM_R < cr_half - 0.8, 'the trim ticks run off the cross pad'
    assert SH_HUB_BORE / 2 + 1.6 < st_pad_d / 2, 'no wall around the MG995 hub bore'
    assert WR_HUB_BORE / 2 + 1.6 < wri_pad_d / 2, 'no wall around the wrist hub bore'
    assert WRI_X + wri_pad_d / 2 + GAP < hu_pad[0], 'wrist pad touches the hub sweep'
    for i in range(len(HU_DX) - 1):
        assert HU_DX[i] + HUB_U[i] / 2 + 1.6 < HU_DX[i + 1] - HUB_U[i + 1] / 2, \
            'micro hub bores %d/%d touch' % (i, i + 1)
    for i in range(len(HM_DX) - 1):
        assert HM_DX[i] + HUB_M[i] / 2 + 1.6 < HM_DX[i + 1] - HUB_M[i + 1] / 2, \
            'MG995 hub bores %d/%d touch' % (i, i + 1)
    for i in range(len(BL_DX) - 1):
        assert BL_DX[i] + BLADE_W[i] / 2 + 1.6 < BL_DX[i + 1] - BLADE_W[i + 1] / 2, \
            'blade comb slots %d/%d touch' % (i, i + 1)
    assert hu_pad[1] + GAP < bl_bar[0], 'hub sweep touches the blade comb'
    assert hm_pad[1] + GAP < pin_pad[0], 'MG995 sweep touches the pin pad'
    assert hm_pad[2] > -BASE_Y / 2 + 5.0, 'bottom row leaves no label band'

    # ---- phase 1: plate -----------------------------------------------------
    t0 = design.timeline.count
    rect('base', -BASE_X / 2, BASE_X / 2, -BASE_Y / 2, BASE_Y / 2, 0.0, base_t, NEW)
    plate = comp.bRepBodies.item(0)
    plate.name = 'gauge_horn_plate'
    group(t0, PH_PLATE)

    # ---- phase 2: the three interface replicas ------------------------------
    t1 = design.timeline.count
    # CROSS - the J1 rotor pocket, inverted (pocket opens UP here)
    rect('cr_pad', CR_X - cr_half, CR_X + cr_half, CR_Y - cr_half, CR_Y + cr_half,
         0.0, base_t + cr_pad_h, JOIN, [plate])
    cr_top = base_t + cr_pad_h
    # TAPERED bowtie slots, matching the rotor pocket exactly (v2: v1 cut
    # these as constant 3.4 rectangles and the horn would not enter at all)
    wr, wt, rr = CROSS_W_ROOT / 2, CROSS_W_TIP / 2, CROSS_R_ROOT
    hs = CROSS_TRIM_R
    for tag, swap in (('a', False), ('b', True)):
        pts = [(-hs, -wt), (-rr, -wr), (rr, -wr), (hs, -wt),
               (hs, wt), (rr, wr), (-rr, wr), (-hs, wt)]
        if swap:
            pts = [(y, x) for (x, y) in pts]
        sk = sketch('cr_slot_' + tag)
        lines = sk.sketchCurves.sketchLines
        for k in range(len(pts)):
            a = pts[k]
            b = pts[(k + 1) % len(pts)]
            lines.addByTwoPoints(pt(sk, CR_X + a[0], CR_Y + a[1]),
                                 pt(sk, CR_X + b[0], CR_Y + b[1]))
        extrude_profs(one(sk), CUT, cr_top, -CROSS_Z, 'cr_slot_' + tag, [plate])
    circle('cr_relief', CR_X, CR_Y, CROSS_RELIEF_D, cr_top, -CROSS_Z, CUT, [plate])
    circle('cr_screw', CR_X, CR_Y, CROSS_SCREW_D, cr_top, -cr_pad_h - base_t - 1.0,
           CUT, [plate])
    for sx in (+1, -1):
        for ax in ('x', 'y'):
            x0 = CR_X + (sx * CROSS_TRIM_R if ax == 'x' else 2.6)
            x1 = CR_X + (sx * CROSS_TRIM_R if ax == 'x' else 4.6)
            y0 = CR_Y + (2.6 if ax == 'x' else sx * CROSS_TRIM_R)
            y1 = CR_Y + (4.6 if ax == 'x' else sx * CROSS_TRIM_R)
            rect('cr_tick_%s%s' % (ax, 'p' if sx > 0 else 'm'),
                 min(x0, x1) - 0.2, max(x0, x1) + 0.2,
                 min(y0, y1) - 0.2, max(y0, y1) + 0.2,
                 cr_top, -val('label_z'), CUT, [plate])

    # MG995 STACK - shoulder_hub interface, hub-first from the top
    circle('st_pad', ST_X, ST_Y, st_pad_d, 0.0, base_t + st_pad_h, JOIN, [plate])
    st_top = base_t + st_pad_h
    rect('st_slot', ST_X - st_pad_d / 2 - 1.0, ST_X + st_pad_d / 2 + 1.0,
         ST_Y - SH_ARM_W / 2, ST_Y + SH_ARM_W / 2, st_top, -SH_ARM_DEPTH, CUT, [plate])
    circle('st_hub', ST_X, ST_Y, SH_HUB_BORE, st_top - SH_ARM_DEPTH,
           -SH_HUB_DEPTH, CUT, [plate])
    circle('st_screw', ST_X, ST_Y, 6.5, st_top, -st_pad_h - base_t - 1.0, CUT, [plate])
    for sx in (+1, -1):
        rect('st_tick_%s' % ('p' if sx > 0 else 'm'),
             ST_X + sx * SH_TRIM_R - 0.2, ST_X + sx * SH_TRIM_R + 0.2,
             ST_Y + SH_ARM_W / 2 + 0.6, ST_Y + SH_ARM_W / 2 + 2.6,
             st_top, -val('label_z'), CUT, [plate])

    # WRIST - micro interface, blade-down
    circle('wri_pad', WRI_X, WRI_Y, wri_pad_d, 0.0, base_t + wri_pad_h, JOIN, [plate])
    wri_top = base_t + wri_pad_h
    rect('wri_slot', WRI_X - wri_pad_d / 2 - 1.0, WRI_X + wri_pad_d / 2 + 1.0,
         WRI_Y - WR_ARM_W / 2, WRI_Y + WR_ARM_W / 2, wri_top, -WR_ARM_DEPTH, CUT, [plate])
    circle('wri_hub', WRI_X, WRI_Y, WR_HUB_BORE, wri_top - WR_ARM_DEPTH,
           -WR_HUB_DEPTH, CUT, [plate])
    group(t1, PH_REPLICA)

    # ---- phase 3: sweeps and pins -------------------------------------------
    t2 = design.timeline.count
    rect('hu_pad', hu_pad[0], hu_pad[1], hu_pad[2], hu_pad[3],
         0.0, base_t + hu_pad_h, JOIN, [plate])
    for i, d in enumerate(HUB_U):
        circle('hu_%d' % i, HU_X + HU_DX[i], HU_Y, d,
               base_t + hu_pad_h, -base_t - hu_pad_h - 1.0, CUT, [plate])
    rect('bl_bar', bl_bar[0], bl_bar[1], bl_bar[2], bl_bar[3],
         0.0, base_t + bl_h, JOIN, [plate])
    for i, w in enumerate(BLADE_W):
        rect('bl_%d' % i, BL_X + BL_DX[i] - w / 2, BL_X + BL_DX[i] + w / 2,
             bl_bar[2] - 1.0, bl_bar[3] + 1.0,
             base_t + bl_h, -bl_depth, CUT, [plate])
    rect('hm_pad', hm_pad[0], hm_pad[1], hm_pad[2], hm_pad[3],
         0.0, base_t + hm_pad_h, JOIN, [plate])
    for i, d in enumerate(HUB_M):
        circle('hm_%d' % i, HM_X + HM_DX[i], HM_Y, d,
               base_t + hm_pad_h, -base_t - hm_pad_h - 1.0, CUT, [plate])
    rect('pin_pad', pin_pad[0], pin_pad[1], pin_pad[2], pin_pad[3],
         0.0, base_t + pin_pad_h, JOIN, [plate])
    for j, (pitch, pd, tag) in enumerate(PIN_PAIRS):
        py = PIN_Y + (4.0 if j == 0 else -4.0)
        for sx in (+1, -1):
            circle('pin_%s_%s' % (tag, 'p' if sx > 0 else 'm'),
                   PIN_X + sx * pitch / 2, py, pd,
                   base_t + pin_pad_h, PIN_H, JOIN, [plate])
    group(t2, PH_SWEEPS)

    # ---- phase 4: labels ----------------------------------------------------
    t3 = design.timeline.count

    def engrave(name, items, z_top):
        for j, (x, y, txt) in enumerate(items):
            sk2 = sketch('%s_%d' % (name, j))
            t_in = sk2.sketchTexts.createInput2(txt, 0.35)
            t_in.setAsMultiLine(
                pt(sk2, x - 24.0, y - 3.0), pt(sk2, x + 24.0, y + 3.0),
                adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            st = sk2.sketchTexts.add(t_in)
            inp = ext.createInput(st, CUT)
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z_top)))
            inp.setDistanceExtent(False, V(mm(-val('label_z'))))
            inp.participantBodies = [plate]
            ext.add(inp).name = '%s_%d' % (name, j)
        return len(items)

    n_lab = engrave('lab', [
        (16.0, 41.5, 'HORN V3'),
        (CR_X, CR_Y - cr_half - 3.5, 'CROSS 34 24'),
        (ST_X, ST_Y - st_pad_d / 2 - 3.5, 'MG995 STACK'),
        (WRI_X, WRI_Y - wri_pad_d / 2 - 3.5, 'WRIST'),
        (HU_X, HU_Y - 10.0, 'HUB 62-74'),
        (33.0, BL_Y - 8.5, 'BL 18-27'),
        (HM_X, HM_Y - 11.5, 'HUB 82-92'),
        (PIN_X, PIN_Y - 11.5, 'PIN 20 23'),
    ], base_t)
    group(t3, PH_LABELS)

    # ---- identity + diagnostics --------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a station is floating' % comp.bRepBodies.count)
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            plate.material = m
            break
    bb = plate.boundingBox
    vol = plate.volume * 1000
    print('component: %r | body: %r' % (comp.name, plate.name))
    print('')
    print('CROSS: TAPERED slots %.2f at r %.1f -> %.2f at the trim line, '
          '%.1f deep, relief O%.1f, screw O%.1f, ticks +-%.1f'
          % (CROSS_W_ROOT, CROSS_R_ROOT, CROSS_W_TIP, CROSS_Z,
             CROSS_RELIEF_D, CROSS_SCREW_D, CROSS_TRIM_R))
    print('MG995 STACK: hub O%.2f x %.1f under slots %.2f x %.1f, trim +-%.1f'
          % (SH_HUB_BORE, SH_HUB_DEPTH, SH_ARM_W, SH_ARM_DEPTH, SH_TRIM_R))
    print('WRIST: hub O%.2f x %.1f under slot %.2f x %.1f'
          % (WR_HUB_BORE, WR_HUB_DEPTH, WR_ARM_W, WR_ARM_DEPTH))
    print('sweeps: micro hub %s | MG995 hub %s | blade %s'
          % (HUB_U, HUB_M, BLADE_W))
    print('pins: %s (h %.1f - a gauge, not a handle)' % (PIN_PAIRS, PIN_H))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume %.0f mm3 | PETG solid %.1f g | at %.0f%% ~%.1f g | labels %d'
          % (vol, vol * PETG_FILAMENT_DENSITY / 1000, SOLID_FRACTION * 100,
             vol * PETG_FILAMENT_DENSITY * SOLID_FRACTION / 1000, n_lab))
    print('valid: %s | sketches: %d' % (plate.isValid, comp.sketches.count))
    print('timeline groups: %r' % (PHASES,))
