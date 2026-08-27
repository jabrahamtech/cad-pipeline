"""robotarm/_gauge_flange - do TowerPro's numbers fit JONATHAN'S servos?

The 2026-08-27 flange audit moved every servo's case and tab dimensions to
TowerPro's own config tables (lib/servo.py has the trail). Those are the
manufacturer's numbers for genuine servos; the bench servos are unbranded
clones, and clone flanges are exactly where clones cheap out. Two numbers
on the audit are not even TowerPro's: the MG90S hole pitch 27.5 is DERIVED
(holes centred in the tab overhang) and its tab 2.5 is ASSUMED. This plate
settles all of it by drop test, which outresolves the 0.1 mm caliper.

STATIONS - every one is a question with a servo for an answer
-------------------------------------------------------------
  MG995 bed    a through window the case sits into, an end stop at the
               case's far end, and the shoulder bracket's OWN slot pattern
               (5.6 x 2.5 at 47.8 x 10.2) cut THROUGH the plate. Set the
               servo in, look through the tab holes: daylight in every
               slot = the bracket will bolt up. The slots already cover
               pitch 47.5..49.5 by design - what this tests is the whole
               pattern at once, which four caliper readings cannot.
  SG90 seat    the case window (22.9 x 12.4) through the plate with the
               tab recess (32.5 x 12.4 x 2.6) around it - the wrist_roll
               tab slot, flat. The servo should sit FLUSH: proud tabs mean
               tab_thk 2.4 is low, a case that will not enter means the
               12.2 width is optimistic, tabs that will not drop in mean
               span 32.3 is tight. Sight lines at +-13.9 under the tab
               holes read the 27.8 pitch.
  MG90S lobe   the forearm lobe, played by the plate itself: the stack
               under the tabs is EXACTLY fa_lobe_t (window through pad +
               base = 5.5), window 12.6 x 23.0, pilot holes 1.8 at the
               DERIVED 27.5. If the tab holes land over the pilots, the
               derivation holds and the forearm can print. Sight lines at
               +-14.5 mark the OLD 29.0 so a miss reads as a direction,
               not a shrug.
  tab comb     slots 2.4 / 2.5 / 2.6 / 2.8 - slide a micro tab in
               edgewise; tightest slot that accepts it IS the tab
               thickness. Serves SG90 (2.4 on file) and MG90S (2.5
               ASSUMED) both.
  horn hub     bores 7.2 / 8.0 / 8.8, bracketing the horn audit's Ø8.0
               (community-model grade; batches vary). The J1 gate is
               BLOCKED on this number, and every wrist part press-fits a
               pocket on it. Push the horn in hub-first: the smallest
               bore that takes it is the answer.
  arm comb     slots 4.5 / 5.0 / 5.5 / 6.0 - slide a horn ARM in edgewise
               near its root. The arm tapers ~5.5 -> 3, five parts cut
               slots at its width AT THE TRIM RADIUS (5.5 at r 6), and
               the old CAD had the blade thickness there instead. The
               tightest slot that takes the arm at ~6 mm from the hub is
               the number the wrist parts live on.
  (the tab comb's 2.0 slot doubles as the BLADE thickness check - the
   horn audit says 2.0 where the old CAD said 1.5)
  flexure      the gripcut finger's hairpin leaf - SAME t 1.2, w 6.0,
               out-run, fold and return as gripcut_finger.py, asserted
               against the live gf_ parameters when they are in the
               document. Push the tip to the engraved 2.5 and 4.5 marks:
               the solver says the grip runs 0.67..0.99 N (68..101 g on a
               kitchen scale) across that range. This is the force check
               no sweep can do - the leaf's ~33 mm folded path was sized
               as a 29.1 straight beam, and this coupon is the correction
               factor.

Print: PETG, same profile as every gauge (a gauge in another material
measures a different machine), flat, engraved face UP, 0.2 layers, 3
walls, SUPPORT OFF. The MG90S/SG90 windows print as through holes; the
flexure leaf is 1.2 wide and needs a clean first layer.

Record results in calibration/ dated, then move lib/servo.py values from
DERIVED/ASSUMED to MEASURED and re-run the gates.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_gauge_flange'
PREFIX = 'gfl_'
PH_PLATE = 'plate'
PH_MG995 = 'mg995 bed'
PH_MICRO = 'micro stations'
PH_FLEX = 'flexure coupon'
PH_LABELS = 'labels'
PHASES = [PH_PLATE, PH_MG995, PH_MICRO, PH_FLEX, PH_LABELS]
MATERIAL_NAME = 'PET Plastic'
PETG_FILAMENT_DENSITY = 1.27
SOLID_FRACTION = 0.65

# ---- the numbers under test, lib/servo.py after the flange audit ----------
LOC = 0.2                     # locational fit - design_rules
# MG995 (shoulder_bracket's slot pattern, verbatim)
MG995_CASE_W = 20.0
MG995_CASE_L = 40.9
MG995_SLOT_L = 5.6            # MG995_TAB_SLOT_X_MM
MG995_SLOT_W = 2.5
MG995_PITCH_X = 47.8          # drawing B - the slots absorb 47.5..49.5
MG995_PITCH_Y = 10.2
# SG90
SG90_CASE_W = 12.2
SG90_CASE_L = 22.7
SG90_SPAN = 32.3
SG90_TAB_THK = 2.4
SG90_PITCH = 27.8
# MG90S
MG90S_CASE_W = 12.4
MG90S_CASE_L = 22.8
MG90S_PITCH = 27.5            # DERIVED - the bet this plate settles
MG90S_PITCH_OLD = 29.0        # the drawing TowerPro's table contradicts
MG90S_LOBE_T = 5.5            # fa_lobe_t = tab_below_top 3.0 + tab_thk 2.5
PILOT_D = 1.8                 # fa_pilot_d
TAB_HOLE_D = 2.1
# combs and horn
COMB_W = [2.0, 2.4, 2.5, 2.6, 2.8]   # 2.0 doubles as the horn BLADE check
HORN_HUB_D = [7.2, 8.0, 8.8]  # brackets the horn audit's hub Ø8.0
ARM_COMB_W = [4.5, 5.0, 5.5, 6.0]  # horn arm width at the r 6 trim
# flexure - MUST MATCH gripcut_finger.py's gf_ params (asserted below)
FLEX_T = 1.2
FLEX_W = 6.0
FLEX_OUT_X = 4.5
FLEX_FOLD_Y = 18.0
FLEX_FOLD_IR = 1.5
FLEX_RET_Y = 6.3              # gf_tip_y0 - the return run ends here
FLEX_ANCHOR_Y = 3.2           # gf_bore_d - where the finger's ring holds it
FLEX_MARKS = [2.5, 4.5]       # grip engagement, full-closure budget


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

    # the flexure numbers are gripcut_finger's - if that part is in this
    # document, disagreeing silently would make the coupon calibrate a leaf
    # that does not exist. (Checked against gf_ params, in mm.)
    for gf_name, ours in (('gf_t', FLEX_T), ('gf_leaf_w', FLEX_W),
                          ('gf_out_x', FLEX_OUT_X), ('gf_fold_y', FLEX_FOLD_Y),
                          ('gf_fold_ir', FLEX_FOLD_IR), ('gf_tip_y0', FLEX_RET_Y),
                          ('gf_bore_d', FLEX_ANCHOR_Y)):
        p = ups.itemByName(gf_name)
        if p is not None:
            assert abs(p.value * 10 - ours) < 1e-6, (
                'coupon %s = %.2f but the live finger says %.2f - the coupon '
                'would calibrate a leaf that does not exist'
                % (gf_name, ours, p.value * 10))

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE (PLAYBOOK) -----------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
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

    # ---- layout, MILLIMETRES, plate centred on the origin -------------------
    BASE_X, BASE_Y = 96.0, 140.0
    base_t = val('base_t')

    # MG995 bed, top row
    M9_Y = 44.0
    m9_win_x = 15.0                        # half-length of the body window
    m9_win_y = (MG995_CASE_W + LOC) / 2    # 10.1 - THE width test
    m9_stop_x0 = MG995_CASE_L / 2 + LOC / 2   # 20.55 - the end stop face
    m9_rail_h = 3.0
    m9_slot_cx = MG995_PITCH_X / 2         # 23.9
    m9_slot_cy = MG995_PITCH_Y / 2         # 5.1

    # SG90 seat + horn sweep, second row
    SG_Y = 12.0
    SG_X = -20.0
    sg_recess_x = (SG90_SPAN + LOC) / 2    # 16.25
    sg_recess_y = (SG90_CASE_W + LOC) / 2  # 6.2
    sg_win_x = (SG90_CASE_L + LOC) / 2     # 11.45
    sg_pad = (SG_X - 21.0, SG_X + 21.0, SG_Y - 9.0, SG_Y + 9.0)
    sg_seat_h = SG90_TAB_THK + LOC         # 2.6 - the wrist_roll slot, flat
    HORN_X, HORN_Y = 30.0, 12.0
    horn_pad = (HORN_X - 17.5, HORN_X + 17.5, HORN_Y - 6.0, HORN_Y + 6.0)
    horn_pad_h = 2.0
    HORN_DX = [-11.0, 0.0, 11.0]

    # MG90S lobe + comb, third row
    MG_Y = -20.0
    MG_X = -24.0
    mg_win_x = (MG90S_CASE_W + LOC) / 2    # 6.3
    mg_win_y = (MG90S_CASE_L + LOC) / 2    # 11.5
    mg_pad = (MG_X - 11.0, MG_X + 11.0, MG_Y - 18.0, MG_Y + 18.0)
    mg_pad_h = MG90S_LOBE_T - base_t       # 3.1: pad + base = the lobe
    COMB_X, COMB_Y = 22.0, -20.0
    comb_bar = (COMB_X - 13.0, COMB_X + 13.0, COMB_Y - 5.0, COMB_Y + 5.0)
    comb_h = 8.0
    comb_slot_depth = 6.0
    COMB_DX = [-10.0, -5.0, 0.0, 5.0, 10.0]
    ARM_X, ARM_Y = -30.0, -50.0
    arm_bar = (ARM_X - 16.5, ARM_X + 16.5, ARM_Y - 5.0, ARM_Y + 5.0)
    ARM_DX = [-12.0, -4.0, 4.0, 12.0]

    # flexure coupon, bottom RIGHT - finger local (x,y) -> gauge
    # (fx0 + y, fy0 + x). Bottom LEFT put the MG90S label on top of the leaf.
    FX0, FY0 = -2.0, -56.0
    flex_ox0 = FY0 + FLEX_OUT_X                       # out-run inner face (gauge y)
    flex_ox1 = flex_ox0 + FLEX_T
    flex_fc = flex_ox1 + FLEX_FOLD_IR                 # fold centre (gauge y)
    flex_rx0 = flex_fc + FLEX_FOLD_IR
    flex_rx1 = flex_rx0 + FLEX_T                      # 8.4 above FY0
    anchor = (FX0 - 8.0, FX0 + FLEX_ANCHOR_Y, FY0 + 1.5, FY0 + 11.0)
    tip_x0 = FX0 + FLEX_RET_Y                          # tip block, on the return run
    flex_h = FLEX_W

    # ---- sanity, all in mm --------------------------------------------------
    GAP = 2.0
    assert m9_slot_cx - MG995_SLOT_L / 2 > m9_stop_x0 + 0.4, (
        'the MG995 end stop face at %.2f runs into the slot starting %.2f'
        % (m9_stop_x0, m9_slot_cx - MG995_SLOT_L / 2))
    assert m9_slot_cy - MG995_SLOT_W / 2 > 2.5 + 1.0, (
        'the end stop (y +-2.5) reaches the slots')
    assert m9_slot_cx + MG995_SLOT_L / 2 + 3.0 < BASE_X / 2, (
        'MG995 slots run off the plate')
    assert M9_Y + m9_win_y + m9_rail_h + 2.0 < BASE_Y / 2, 'MG995 bed off the top'
    assert sg_recess_x > sg_win_x + 1.5, (
        'no visible tab seat between the SG90 window and the recess ends')
    assert SG90_PITCH / 2 > sg_win_x + 0.6, (
        'the SG90 sight lines at %.2f fall inside the window %.2f'
        % (SG90_PITCH / 2, sg_win_x))
    assert SG90_PITCH / 2 < sg_recess_x - 0.6, (
        'the SG90 sight lines fall outside the tab recess - the tab holes '
        'could never show them')
    assert sg_pad[1] + GAP < horn_pad[0], 'SG90 pad touches the horn pad'
    assert MG90S_PITCH / 2 > mg_win_y + PILOT_D / 2 + 0.4, (
        'MG90S pilots break into the window')
    assert MG90S_PITCH_OLD / 2 < (mg_pad[3] - MG_Y) - 0.8, (
        'the 29.0 sight lines run off the MG90S pad')
    # 27.5 vs 29.0 is only 0.75 a side - a 1.8 pilot at 13.75 swallows a line
    # at 14.5, so the sight lines cannot share the centreline with the
    # pilots. They live BESIDE the tab instead (the tab is only as wide as
    # the case), where both pitches can be marked and read against the tab
    # hole's edge with the servo seated.
    sight_x0 = MG90S_CASE_W / 2 + 0.5
    sight_x1 = sight_x0 + 3.0
    assert sight_x1 < (mg_pad[1] - MG_X) - 0.8, (
        'the MG90S sight lines run off the pad side')
    assert mg_pad[1] + GAP < comb_bar[0], 'MG90S pad touches the comb'
    for i in range(len(COMB_DX) - 1):
        assert COMB_DX[i] + COMB_W[i] / 2 + 1.6 < COMB_DX[i + 1] - COMB_W[i + 1] / 2, (
            'less than a wall between comb slots %d and %d' % (i, i + 1))
    assert comb_h - comb_slot_depth >= 1.6, 'the comb floor is under a wall'
    for i in range(len(ARM_DX) - 1):
        assert ARM_DX[i] + ARM_COMB_W[i] / 2 + 1.6 < ARM_DX[i + 1] - ARM_COMB_W[i + 1] / 2, (
            'less than a wall between arm-comb slots %d and %d' % (i, i + 1))
    assert arm_bar[1] < FX0 - 8.0 - GAP, 'the arm comb touches the flex anchor'
    for i in range(len(HORN_DX) - 1):
        assert HORN_DX[i] + HORN_HUB_D[i] / 2 + 1.6 < HORN_DX[i + 1] - HORN_HUB_D[i + 1] / 2, (
            'less than a wall between hub bores %d and %d' % (i, i + 1))
    assert flex_rx1 < anchor[3], 'the leaf runs outside its anchor face'
    assert FX0 + FLEX_FOLD_Y + FLEX_FOLD_IR + FLEX_T + 1.0 < BASE_X / 2, (
        'the flexure fold runs off the plate')
    assert anchor[2] > -BASE_Y / 2 + 1.0, 'the anchor runs off the bottom'
    tip_clear = FY0 + 10.4 + FLEX_MARKS[-1] + 1.0     # rest face + travel
    assert tip_clear < comb_bar[2] - GAP, (
        'the deflection travel reaches the comb row above')
    assert anchor[0] > mg_pad[1] - 40.0 or anchor[0] > -12.0, (
        'the coupon anchor drifted back under the MG90S station')

    # ---- phase 1: plate -----------------------------------------------------
    t0 = design.timeline.count
    rect('base', -BASE_X / 2, BASE_X / 2, -BASE_Y / 2, BASE_Y / 2, 0.0, base_t, NEW)
    plate = comp.bRepBodies.item(0)
    plate.name = 'gauge_flange_plate'
    group(t0, PH_PLATE)

    # ---- phase 2: MG995 bed -------------------------------------------------
    t1 = design.timeline.count
    rect('m9_window', -m9_win_x, m9_win_x, M9_Y - m9_win_y, M9_Y + m9_win_y,
         -1.0, base_t + 2.0, CUT, [plate])
    for sy in (+1, -1):
        rect('m9_rail_%s' % ('p' if sy > 0 else 'm'),
             -26.0, 26.0, M9_Y + sy * m9_win_y, M9_Y + sy * (m9_win_y + 3.0),
             base_t, m9_rail_h, JOIN, [plate])
    rect('m9_stop', m9_stop_x0, m9_stop_x0 + 3.0, M9_Y - 2.5, M9_Y + 2.5,
         base_t, m9_rail_h, JOIN, [plate])
    for sx in (+1, -1):
        for sy in (+1, -1):
            rect('m9_slot_%s%s' % ('p' if sx > 0 else 'm', 'p' if sy > 0 else 'm'),
                 sx * m9_slot_cx - MG995_SLOT_L / 2, sx * m9_slot_cx + MG995_SLOT_L / 2,
                 M9_Y + sy * m9_slot_cy - MG995_SLOT_W / 2,
                 M9_Y + sy * m9_slot_cy + MG995_SLOT_W / 2,
                 -1.0, base_t + 2.0, CUT, [plate])
    group(t1, PH_MG995)

    # ---- phase 3: SG90 seat, horn sweep, MG90S lobe, comb -------------------
    t2 = design.timeline.count
    rect('sg_pad', sg_pad[0], sg_pad[1], sg_pad[2], sg_pad[3],
         0.0, base_t + sg_seat_h, JOIN, [plate])
    rect('sg_recess', SG_X - sg_recess_x, SG_X + sg_recess_x,
         SG_Y - sg_recess_y, SG_Y + sg_recess_y,
         base_t + sg_seat_h, -sg_seat_h, CUT, [plate])
    rect('sg_window', SG_X - sg_win_x, SG_X + sg_win_x,
         SG_Y - sg_recess_y, SG_Y + sg_recess_y,
         base_t, -base_t - 1.0, CUT, [plate])
    for sx in (+1, -1):
        rect('sg_sight_%s' % ('p' if sx > 0 else 'm'),
             SG_X + sx * SG90_PITCH / 2 - 0.2, SG_X + sx * SG90_PITCH / 2 + 0.2,
             SG_Y - sg_recess_y, SG_Y + sg_recess_y,
             base_t, -val('label_z'), CUT, [plate])

    rect('horn_pad', horn_pad[0], horn_pad[1], horn_pad[2], horn_pad[3],
         0.0, base_t + horn_pad_h, JOIN, [plate])
    for i, d in enumerate(HORN_HUB_D):
        circle('horn_%d' % i, HORN_X + HORN_DX[i], HORN_Y, d,
               base_t + horn_pad_h, -base_t - horn_pad_h - 1.0, CUT, [plate])

    rect('mg_pad', mg_pad[0], mg_pad[1], mg_pad[2], mg_pad[3],
         0.0, base_t + mg_pad_h, JOIN, [plate])
    mg_top = base_t + mg_pad_h
    assert abs(mg_top - MG90S_LOBE_T) < 1e-9, (
        'pad %.2f + base %.2f is not the %.2f lobe the forearm ships'
        % (mg_pad_h, base_t, MG90S_LOBE_T))
    rect('mg_window', MG_X - mg_win_x, MG_X + mg_win_x,
         MG_Y - mg_win_y, MG_Y + mg_win_y, mg_top, -mg_top - 1.0, CUT, [plate])
    for sy in (+1, -1):
        circle('mg_pilot_%s' % ('p' if sy > 0 else 'm'),
               MG_X, MG_Y + sy * MG90S_PITCH / 2, PILOT_D,
               mg_top, -mg_top - 1.0, CUT, [plate])
        for tag, pitch in (('275', MG90S_PITCH), ('29', MG90S_PITCH_OLD)):
            for sx in (+1, -1):
                rect('mg_sight%s_%s%s' % (tag, 'p' if sy > 0 else 'm',
                                          'p' if sx > 0 else 'm'),
                     MG_X + sx * sight_x0, MG_X + sx * sight_x1,
                     MG_Y + sy * pitch / 2 - 0.2,
                     MG_Y + sy * pitch / 2 + 0.2,
                     mg_top, -val('label_z'), CUT, [plate])

    rect('comb_bar', comb_bar[0], comb_bar[1], comb_bar[2], comb_bar[3],
         0.0, base_t + comb_h, JOIN, [plate])
    for i, w in enumerate(COMB_W):
        rect('comb_%d' % i, COMB_X + COMB_DX[i] - w / 2, COMB_X + COMB_DX[i] + w / 2,
             comb_bar[2] - 1.0, comb_bar[3] + 1.0,
             base_t + comb_h, -comb_slot_depth, CUT, [plate])
    rect('arm_bar', arm_bar[0], arm_bar[1], arm_bar[2], arm_bar[3],
         0.0, base_t + comb_h, JOIN, [plate])
    for i, w in enumerate(ARM_COMB_W):
        rect('arm_comb_%d' % i, ARM_X + ARM_DX[i] - w / 2, ARM_X + ARM_DX[i] + w / 2,
             arm_bar[2] - 1.0, arm_bar[3] + 1.0,
             base_t + comb_h, -comb_slot_depth, CUT, [plate])
    group(t2, PH_MICRO)

    # ---- phase 4: the flexure coupon ---------------------------------------
    # The finger's hairpin, transplanted: finger local +y runs along gauge +x
    # from FX0, finger local +x (the DEFLECTION direction) along gauge +y
    # from FY0. Printed flat, so the layers lie along the leaf - the same
    # in-plane bending the finger prints with.
    t3 = design.timeline.count
    rect('flex_anchor', anchor[0], anchor[1], anchor[2], anchor[3],
         base_t, flex_h, JOIN, [plate])
    sk = sketch('flex_leaf')
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    ax1 = FX0 + FLEX_ANCHOR_Y            # leaf springs from the anchor face
    fx_fold = FX0 + FLEX_FOLD_Y
    ret_end = FX0 + FLEX_RET_Y
    lines.addByTwoPoints(pt(sk, ax1, flex_ox0), pt(sk, fx_fold, flex_ox0))
    arcs.addByThreePoints(pt(sk, fx_fold, flex_ox0),
                          pt(sk, fx_fold + FLEX_FOLD_IR + FLEX_T, flex_fc),
                          pt(sk, fx_fold, flex_rx1))
    lines.addByTwoPoints(pt(sk, fx_fold, flex_rx1), pt(sk, ret_end, flex_rx1))
    lines.addByTwoPoints(pt(sk, ret_end, flex_rx1), pt(sk, ret_end, flex_rx0))
    lines.addByTwoPoints(pt(sk, ret_end, flex_rx0), pt(sk, fx_fold, flex_rx0))
    arcs.addByThreePoints(pt(sk, fx_fold, flex_rx0),
                          pt(sk, fx_fold + FLEX_FOLD_IR, flex_fc),
                          pt(sk, fx_fold, flex_ox1))
    lines.addByTwoPoints(pt(sk, fx_fold, flex_ox1), pt(sk, ax1, flex_ox1))
    lines.addByTwoPoints(pt(sk, ax1, flex_ox1), pt(sk, ax1, flex_ox0))
    extrude_profs(one(sk), JOIN, base_t, flex_h, 'flex_leaf', [plate])
    # tip block on the return run's end - the thing to push on
    rect('flex_tip', tip_x0 - 2.0, tip_x0 + 2.5, flex_rx0, flex_rx1 + 2.0,
         base_t, flex_h, JOIN, [plate])
    # deflection scale: rest face is the tip block's outer edge; ticks at the
    # grip engagement and the full-closure budget, in the +y direction the
    # stem would push
    tick_x0 = tip_x0 + 3.5
    rest_y = flex_rx1 + 2.0
    for d in [0.0] + FLEX_MARKS:
        rect('flex_tick_%02d' % int(d * 10),
             tick_x0, tick_x0 + 4.0, rest_y + d - 0.2, rest_y + d + 0.2,
             base_t, -val('label_z'), CUT, [plate])
    group(t3, PH_FLEX)

    # ---- phase 5: labels ----------------------------------------------------
    t4 = design.timeline.count

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
        (0.0, 64.0, 'FLANGE V2'),
        (0.0, 28.0, 'MG995 P47.8'),
        (SG_X, SG_Y - 13.0, 'SG90 P27.8'),
        (HORN_X, HORN_Y - 10.5, 'HUB 72 80 88'),
        (MG_X, MG_Y - 20.8, 'MG90S P27.5'),
        (COMB_X, COMB_Y - 9.5, 'TAB 20 24 25 26 28'),
        (FX0 + 10.0, FY0 - 8.5, 'FLEX 0 25 45'),
        (ARM_X + 5.0, ARM_Y - 9.0, 'ARM 45 50 55 60'),
    ], base_t)
    group(t4, PH_LABELS)

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
    print('MG995 bed: window %.1f wide, end stop at %.2f, slots %.1f x %.1f at '
          '+-%.2f / +-%.2f THROUGH the plate - daylight in all four = bolts up'
          % (2 * m9_win_y, m9_stop_x0, MG995_SLOT_L, MG995_SLOT_W,
             m9_slot_cx, m9_slot_cy))
    print('SG90 seat: window %.1f x %.1f, tab recess %.1f x %.1f x %.1f deep - '
          'the servo should sit FLUSH; sight lines at +-%.2f'
          % (2 * sg_win_x, 2 * sg_recess_y, 2 * sg_recess_x, 2 * sg_recess_y,
             sg_seat_h, SG90_PITCH / 2))
    print('MG90S lobe: window %.1f x %.1f through %.1f (pad %.1f + base %.1f '
          '= fa_lobe_t), pilots %.1f at the DERIVED %.1f, sight lines at the '
          'old %.1f' % (2 * mg_win_x, 2 * mg_win_y, mg_top, mg_pad_h, base_t,
                        PILOT_D, MG90S_PITCH, MG90S_PITCH_OLD))
    print('tab comb: %s (2.0 = horn blade) | arm comb: %s | hub bores: %s'
          % (COMB_W, ARM_COMB_W, HORN_HUB_D))
    print('flexure: t %.1f x w %.1f hairpin, fold at %.1f, marks at rest %s mm'
          % (FLEX_T, FLEX_W, FLEX_FOLD_Y, FLEX_MARKS))
    print('  solver says 0.67..0.99 N across the marks = 68..101 g on a scale')
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume %.0f mm3 | PETG solid %.1f g | at %.0f%% ~%.1f g | labels %d'
          % (vol, vol * PETG_FILAMENT_DENSITY / 1000, SOLID_FRACTION * 100,
             vol * PETG_FILAMENT_DENSITY * SOLID_FRACTION / 1000, n_lab))
    print('valid: %s | sketches: %d' % (plate.isValid, comp.sketches.count))
    print('timeline groups: %r' % (PHASES,))
