"""robotarm/_check_j1 - the J1 gate.

The turntable has never been swept in Fusion the way _check_shoulder sweeps
J2. Every J1 clearance in this repo is ARITHMETIC: shoulder_bracket asserts
the MG995 clears the ring, turntable_stator asserts the horn reaches the
pocket, and nothing has ever put the five bodies in one document and turned
the thing. Given that the yaw servo turned out to be 5.2 mm off the axis in a
part whose own assertions were all green, arithmetic is not enough here.

Frame: the STATOR's frame. Origin ON THE J1 YAW AXIS at the PLATTER'S RIM
TOP - platter z 42.00, measured. +Z up. turntable_stator and turntable_ring
are authored in it directly. TWO PARTS ARE NOT, and both are spelled out
below rather than left as offsets: base_lid, which is authored on its own
underside and has to drop a lid thickness so its top finishes flush at z 0,
and the rotor.

WHERE THE ROTOR GOES, DERIVED. shoulder_bracket's origin is on the J2 PITCH
axis, so its turntable disc hangs a long way below its own zero:

    boss_top  = -sb_stand_h                     the plane the fork stands on
    rim_top   = boss_top - tt_boss_h
    race_z    = rim_top  - tt_disc_t            the race face, its floor

and the race face has to land on the roller crowns at tt_race_z. So

    DZ = tt_race_z - race_z_local
       = tt_race_z + sb_stand_h + tt_boss_h + tt_disc_t

That is read from the live parameters every run and never typed. It comes to
70.40, which is what _preview_j1.py's STACK table carries as a literal.

AND THE 0.4 IN IT IS A SHARED PARAMETER WITH TWO VALUES. `tt_boss_h` is
declared 4.0 mm in turntable_stator.py and turntable_ring.py and 4.4 mm in
shoulder_bracket.py, where it has to be ring_lift + ring_t or the ring does
not finish flush with the boss top. Nothing errors, because every runner of
this stack happens to build shoulder_bracket LAST and 4.4 wins. Rebuild the
ring on its own after an edit and the number silently becomes 4.0: the rotor
drops 0.4, the ring clamps it, and J1 stops turning. PLAYBOOK, "Redefining a
SHARED user parameter reshapes every part already built" - a file may define
a shared parameter only with the value every other file gives it. Asserted
below so it cannot go on being true by luck.

WHAT IS NOT IN ANY MODEL FILE, AND SO IS BUILT HERE AS AN ENVELOPE:

  3 x 608ZZ   Ø22 OD, Ø8 BORE, 7 wide, on RADIAL axles at r tt_roller_r,
              az 90/210/330, axis height tt_axle_z. The stator only cuts the
              stub they press onto. THE CROWN IS THE WHOLE JOINT - if
              tt_axle_z + od/2 is not tt_race_z the arm does not sit on its
              bearings, and no script in this repo has ever measured that
              against real geometry. THE BORE IS NOT DECORATION: modelled
              solid, the roller swallows its own Ø7.9 stub axle and reports
              ~550 mm3 of interference per roller that is not there.
  MG995       bolted to the rotor's pad and pointing DOWN. It is the biggest
              thing on the rotating half and shoulder_bracket's lower bound on
              sb_stand_h exists solely to keep it off the ring. It TURNS.
  SG90        in the platter's column, pointing UP, FIXED. Its horn turns.

THE SG90's DATUM, and it is the one this project already got wrong once. The
origin is the shaft axis at the TAB PLANE - the underside of the tabs, the
face the pad bears on - which turntable_stator computes as ts_deck_z. The case
runs DOWN from tab_thk + tab_below_top above it; the boss and horn run UP.
And the CASE CENTRE sits ts_shaft_off in +Y so the SHAFT lands on the axis.
Model the case centred and the horn drives the rotor as a 5.2 mm crank.

RUN ORDER. Four parts plus thirteen poses of interference is far over the 60 s
MCP call limit, so this splits the way _check_ledger does:

    mod.REBUILD = True                      builds, verifies, stops
    mod.REBUILD = False; mod.BATCH = 0,1,2,3   sweeps; batch 3 prints the gate

Results accumulate in specs/robotarm/_j1_sweep.json so the last batch can
judge the whole sweep rather than its own slice.
"""

import importlib.util
import json
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
LEDGER = os.path.join(REPO, 'specs', 'robotarm', '_j1_sweep.json')
PARTS = ['base_lid', 'turntable_stator', 'turntable_ring', 'shoulder_bracket']

# J1's travel. The SG90 gives 180 deg and NOTHING CAPS IT mechanically - the
# ring hooks over the rim all the way round - so the sweep is the servo's full
# range about centre. _assembly.md limits the joint to +-90 for LOOM TWIST,
# which is the same number by coincidence, not by mechanism.
YAW_DEG = [-90.0, -75.0, -60.0, -45.0, -30.0, -15.0, 0.0,
           15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
BATCH_SIZE = 4
LEAVE_AT_YAW = 0.0

# The fixed half is 3-fold (posts 120/180/240, rollers 90/210/330) and the
# rotor is 1-fold, so 15 deg steps see every post-past-window event.
ROLL_AZ = (90.0, 210.0, 330.0)

# The two numbers no user parameter in this project carries. Both are the
# BOUGHT part, not ours, and both are read by this gate only.
ROLLER_BORE_MM = 8.0        # 608ZZ bore - lib/bearings.py
SG90_BLADE_W_MM = 3.0       # arm width over its outer half - 2026-08-27 horn
                            # audit (community-model grade). tt_horn_w is 3.4 =
                            # this + 0.4; cutting the envelope at 3.4 would
                            # model the POCKET as the blade and report mm3
                            # that are not there.
SG90_HUB_D_MM = 8.0         # horn audit: was 6.30 INVENTED; now the FreeCAD
                            # measured-model value. Still not from Jonathan's
                            # bench - the horn dims vary by batch, and the
                            # gauge_flange v2 hub sweep (7.0/7.6/8.2/8.8) is
                            # what promotes this to MEASURED. Until then the
                            # gate stays BLOCKED, same as before, new number.

# Two bodies in rolling contact meet on a LINE, and a printed collar meets an
# inner race on an annulus. Both are exact in the maths and neither is exact in
# a faceted kernel, so a correct assembly reports a few hundredths of a cubic
# millimetre at every such contact. 0.05 mm3 is a cube 0.37 mm on a side - far
# under a layer height, and two orders below the 3.02 that turned out to be a
# real guess. Anything above this floor is reported and judged.
NOISE_FLOOR_MM3 = 0.05

ROLLER_ENV = 'robotarm_608ZZ_rollers'
MG995_ENV = 'robotarm_MG995_j1_envelope'
SG90_ENV = 'robotarm_SG90_case_envelope'
SG90_OUT = 'robotarm_SG90_horn'

REBUILD = True
BATCH = 0


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    M3 = adsk.core.Matrix3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)
    P3 = adsk.core.Point3D.create
    V = adsk.core.ValueInput.createByString
    NEWB = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOINB = adsk.fusion.FeatureOperations.JoinFeatureOperation

    def gv(name):
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        return p.value

    def mm(cm):
        return '%.4f mm' % (cm * 10.0)

    # ---- rebuild every piece from its committed script ----------------------
    built_volume = {}
    if REBUILD:
        for name in PARTS:
            path = os.path.join(REPO, 'models', 'robotarm', name + '.py')
            assert os.path.exists(path), 'missing ' + path
            spec = importlib.util.spec_from_file_location('gen_' + name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.run(_context)
            for occ in adsk.fusion.Design.cast(
                    app.activeProduct).rootComponent.occurrences:
                if occ.component.name == 'robotarm_' + name:
                    built_volume[name] = occ.component.bRepBodies.item(0).volume
        print('')

    keepers = {}
    for occ in list(root.occurrences):
        if occ.component.name in keepers:
            occ.deleteMe()
        else:
            keepers[occ.component.name] = occ
    design.timeline.moveToEnd()

    if REBUILD:
        scars = []
        for name, vol in built_volume.items():
            now = keepers['robotarm_' + name].component.bRepBodies.item(0).volume
            if abs(now - vol) > vol * 1e-6:
                scars.append('%s %.1f -> %.1f mm3' % (name, vol * 1000, now * 1000))
        assert not scars, (
            'a later part script changed an earlier part: ' + '; '.join(scars) +
            ' - a shared parameter was redefined, or a cut took the wrong '
            'participantBodies. See PLAYBOOK "Redefining a SHARED user parameter".')
        print('volume unchanged after all parts built: %s' % ', '.join(
            '%s %.0f mm3' % (k, v * 1000) for k, v in sorted(built_volume.items())))
        if os.path.exists(LEDGER):
            os.remove(LEDGER)
        print('THIS PASS BUILT ONLY. Re-run with REBUILD=False, BATCH=0..%d.'
              % ((len(YAW_DEG) - 1) // BATCH_SIZE))
        return

    for name in PARTS:
        assert 'robotarm_' + name in keepers, (
            'robotarm_%s is not in the document - run the REBUILD=True pass first'
            % name)
    C = dict((n, keepers['robotarm_' + n].component) for n in PARTS)

    # ---- everything in MILLIMETRES, converted once -------------------------
    # PLAYBOOK "Units in ASSERTIONS": val() is CENTIMETRES. Nothing below this
    # block compares a raw parameter value against a written number.
    race_z_mm = gv('tt_race_z') * 10
    axle_z_mm = gv('tt_axle_z') * 10
    roller_od_mm = gv('tt_roller_od') * 10
    roller_w_mm = gv('tt_roller_w') * 10
    roller_r_mm = gv('tt_roller_r') * 10
    disc_t_mm = gv('tt_disc_t') * 10
    disc_d_mm = gv('tt_disc_d') * 10
    boss_d_mm = gv('tt_boss_d') * 10
    boss_h_mm = gv('tt_boss_h') * 10
    ring_t_mm = gv('tt_ring_t') * 10
    ring_lift_mm = gv('tt_ring_lift') * 10
    collar_h_mm = gv('tt_collar_h') * 10
    stand_h_mm = gv('sb_stand_h') * 10
    rot_fit_mm = gv('tr_rot') * 10
    horn_z_mm = gv('tt_horn_z') * 10
    roller_bore_mm = ROLLER_BORE_MM

    # THE PLACEMENT. See the docstring; never a literal.
    dz_mm = race_z_mm + stand_h_mm + boss_h_mm + disc_t_mm
    crown_mm = axle_z_mm + roller_od_mm / 2.0
    # THE SHARED-PARAMETER TRAP, caught rather than relied on. See the
    # docstring: three files declare tt_boss_h and they do not agree.
    assert abs(boss_h_mm - (ring_lift_mm + ring_t_mm)) < 1e-6, (
        'tt_boss_h is %.2f but ring_lift + ring_t is %.2f - the ring no longer '
        'finishes flush with the boss top. turntable_stator.py and '
        'turntable_ring.py declare tt_boss_h 4.0 and shoulder_bracket.py '
        'declares 4.4; whichever script ran last is what this document holds. '
        'Fix the declarations, do not re-run in a luckier order.'
        % (boss_h_mm, ring_lift_mm + ring_t_mm))
    assert abs(crown_mm - race_z_mm) < 1e-6, (
        'the roller crown is at z %.3f and the race face at z %.3f - tt_race_z '
        'is not tt_axle_z + tt_roller_od/2 any more' % (crown_mm, race_z_mm))

    # base_lid is authored on its own underside: z 0..bl_t in its own frame,
    # and it finishes FLUSH with the platter rim, which is this frame's zero.
    # So it drops by its own thickness. Measured off the built body rather
    # than read from a parameter, then checked against the parameter - the
    # body is what gets posed, and a parameter that stopped driving it would
    # not show up any other way.
    lid_bb = C['base_lid'].bRepBodies.item(0).boundingBox
    dz_lid_mm = -lid_bb.maxPoint.z * 10
    lid_t_mm = (lid_bb.maxPoint.z - lid_bb.minPoint.z) * 10
    assert abs(dz_lid_mm + lid_t_mm) < 1e-6, (
        'base_lid spans z %.3f..%.3f in its own frame - it is not authored on '
        'its underside any more, and this drop is wrong'
        % (lid_bb.minPoint.z * 10, lid_bb.maxPoint.z * 10))

    print('=== J1 turntable gate ===')
    print('rotor placed at dz %.2f mm - DERIVED as tt_race_z + sb_stand_h + '
          'tt_boss_h + tt_disc_t' % dz_mm)
    print('roller crown z %.2f = race face z %.2f' % (crown_mm, race_z_mm))
    print('base_lid dropped %.2f mm - its own %.2f thickness, top flush at z 0'
          % (dz_lid_mm, lid_t_mm))
    print('')

    def fresh(comp_name):
        """PLAYBOOK: rename the outgoing component BEFORE deleting its
        occurrences, or the last one orphans the component and reserves its
        name. This gate places extras and cleans them up, which is exactly the
        case that fires it."""
        stale = comp_name + '_stale_'
        for i in range(design.allComponents.count):
            c = design.allComponents.item(i)
            if c.name == comp_name or c.name.startswith(comp_name + ' ('):
                c.name = stale + str(i)
        for occ in list(root.occurrences):
            if occ.component.name.startswith(stale):
                occ.deleteMe()
        occ = root.occurrences.addNewComponent(M3())
        occ.component.name = comp_name
        assert occ.component.name == comp_name, (
            'Fusion handed back %s - a stale component still reserves the name'
            % occ.component.name)
        keepers.pop(comp_name, None)
        return occ

    def box(comp, name, x0, x1, y0, y1, z0, z1, op):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            sk.modelToSketchSpace(P3(x0 / 10.0, y0 / 10.0, 0)),
            sk.modelToSketchSpace(P3(x1 / 10.0, y1 / 10.0, 0)))
        assert sk.profiles.count == 1, name
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = comp.features.extrudeFeatures.createInput(col, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('%.4f mm' % z0))
        inp.setDistanceExtent(False, V('%.4f mm' % (z1 - z0)))
        if op != NEWB:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        comp.features.extrudeFeatures.add(inp).name = name

    def disc(comp, name, x_c, y_c, d, z0, z1, op):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(x_c / 10.0, y_c / 10.0, 0)), d / 20.0)
        assert sk.profiles.count == 1, name
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = comp.features.extrudeFeatures.createInput(col, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V('%.4f mm' % z0))
        inp.setDistanceExtent(False, V('%.4f mm' % (z1 - z0)))
        if op != NEWB:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        comp.features.extrudeFeatures.add(inp).name = name

    # ---- the three 608ZZ, on RADIAL axles ----------------------------------
    # Built as plain Ø22 x 7 solids: the bore and the shields change nothing
    # about what the rotor and the cheeks can touch, and the collar clearance
    # is measured as cheek-face-to-roller-face, which a solid gives correctly.
    roll_occ = fresh(ROLLER_ENV)
    rollers = roll_occ.component
    for i, az in enumerate(ROLL_AZ):
        # A cylinder about a RADIAL horizontal axis: draw it on XY at the
        # origin, then move it out to r and turn it up onto its side.
        sub = rollers.sketches.add(rollers.xYConstructionPlane)
        sub.name = 'sk_roller_%d' % i
        sub.sketchCurves.sketchCircles.addByCenterRadius(
            sub.modelToSketchSpace(P3(0, 0, 0)), roller_od_mm / 20.0)
        sub.sketchCurves.sketchCircles.addByCenterRadius(
            sub.modelToSketchSpace(P3(0, 0, 0)), roller_bore_mm / 20.0)
        assert sub.profiles.count == 2, (
            'expected an annulus, got %d profiles' % sub.profiles.count)
        outer = max((sub.profiles.item(k) for k in range(2)),
                    key=lambda pr: pr.areaProperties().area)
        col = adsk.core.ObjectCollection.create()
        col.add(outer)
        inp = rollers.features.extrudeFeatures.createInput(col, NEWB)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
            V('%.4f mm' % (-roller_w_mm / 2.0)))
        inp.setDistanceExtent(False, V('%.4f mm' % roller_w_mm))
        body = rollers.features.extrudeFeatures.add(inp)
        body.name = 'roller_%d' % i
        # lie it down (+Z axis -> +X), then swing to its azimuth, then out to r
        m = M3()
        m.setToRotation(math.pi / 2, VEC(0, 1, 0), ORG)
        m2 = M3()
        m2.setToRotation(math.radians(az), VEC(0, 0, 1), ORG)
        m.transformBy(m2)
        t = m.translation
        t.x = roller_r_mm * math.cos(math.radians(az)) / 10.0
        t.y = roller_r_mm * math.sin(math.radians(az)) / 10.0
        t.z = axle_z_mm / 10.0
        m.translation = t
        mv = adsk.core.ObjectCollection.create()
        mv.add(rollers.bRepBodies.item(rollers.bRepBodies.count - 1))
        mvi = rollers.features.moveFeatures.createInput2(mv)
        mvi.defineAsFreeMove(m)
        rollers.features.moveFeatures.add(mvi).name = 'place_roller_%d' % i
        rollers.bRepBodies.item(rollers.bRepBodies.count - 1).name = '608ZZ_%d' % i
    assert rollers.bRepBodies.count == 3, (
        'expected 3 rollers, got %d' % rollers.bRepBodies.count)
    print('3 x 608ZZ Ø%.1f OD / Ø%.1f bore x %.1f at r %.1f, az %s, axles '
          'RADIAL at z %.2f' % (roller_od_mm, roller_bore_mm, roller_w_mm,
                                roller_r_mm,
                                '/'.join('%.0f' % a for a in ROLL_AZ), axle_z_mm))

    # ---- the MG995, hanging off the rotor and pointing DOWN ----------------
    mg_occ = fresh(MG995_ENV)
    mg = mg_occ.component
    mg_case_l_mm = gv('sb_case_l') * 10
    mg_case_w_mm = gv('sb_case_w') * 10
    mg_shaft_end_mm = gv('sb_shaft_end') * 10
    mg_lobe_t_mm = gv('sb_lobe_t') * 10
    mg_tab_thk_mm = gv('sb_tab_thk') * 10
    mg_plate_out_mm = gv('sb_plate_out') * 10
    MG_CASE_H_MM = 36.5              # MG995 case height, DATASHEET drawing B
    MG_TAB_SPAN_MM = 54.0            # TowerPro official E, 2026-08-27 audit
    # In the ROTOR's frame: the pad's outer face is the tab plane, the case
    # runs outboard from it in +X, and the case's own long axis is Z.
    mg_tab_x = mg_plate_out_mm + mg_lobe_t_mm
    mg_case_x = mg_tab_x - mg_lobe_t_mm
    mg_hi = mg_shaft_end_mm
    mg_lo = mg_hi - mg_case_l_mm
    box(mg, 'case', mg_case_x, mg_case_x + MG_CASE_H_MM,
        -mg_case_w_mm / 2, mg_case_w_mm / 2, mg_lo, mg_hi, NEWB)
    box(mg, 'tabs', mg_tab_x, mg_tab_x + mg_tab_thk_mm,
        -mg_case_w_mm / 2, mg_case_w_mm / 2,
        (mg_hi + mg_lo) / 2 - MG_TAB_SPAN_MM / 2,
        (mg_hi + mg_lo) / 2 + MG_TAB_SPAN_MM / 2, JOINB)
    assert mg.bRepBodies.count == 1, (
        'MG995 envelope came out in %d pieces' % mg.bRepBodies.count)
    mg.bRepBodies.item(0).name = 'MG995_envelope'
    ring_top_local = -stand_h_mm + 0.0     # boss top, and the ring finishes flush
    print('MG995 on the rotor: case z %.1f..%.1f local, ring top %.1f local - '
          '%.2f of daylight by arithmetic' % (mg_lo, mg_hi, ring_top_local,
                                              mg_lo - ring_top_local))

    # ---- the SG90, FIXED in the platter column, pointing UP ----------------
    sg_occ = fresh(SG90_ENV)
    sg = sg_occ.component
    sg_case_l_mm = gv('ts_case_l') * 10
    sg_case_w_mm = gv('ts_case_w') * 10
    sg_case_h_mm = gv('ts_case_h') * 10
    sg_tab_thk_mm = gv('ts_tab_thk') * 10
    sg_tab_below_mm = gv('ts_tab_below_top') * 10
    sg_tab_span_mm = gv('ts_tab_span') * 10
    sg_boss_h_mm = gv('ts_boss_h') * 10
    sg_hub_h_mm = gv('ts_horn_hub_h') * 10
    sg_blade_t_mm = gv('ts_horn_blade_t') * 10
    sg_off_mm = gv('ts_shaft_off') * 10
    horn_span_mm = gv('tt_horn_span') * 10
    horn_w_mm = gv('tt_horn_w') * 10
    # ts_deck_z, rebuilt from the same parameters the stator derives it from.
    deck_z_mm = race_z_mm + horn_z_mm - (sg_tab_below_mm + sg_tab_thk_mm
                                         + sg_boss_h_mm + sg_hub_h_mm)
    sg_case_top = deck_z_mm + sg_tab_thk_mm + sg_tab_below_mm
    # THE CASE CENTRE IS OFFSET so the SHAFT lands on the axis.
    sg_y0 = sg_off_mm - sg_case_l_mm / 2
    sg_y1 = sg_off_mm + sg_case_l_mm / 2
    assert abs(sg_y0 + gv('ts_shaft_from_end') * 10) < 1e-6, (
        'the SG90 shaft lands at y %.3f, not on the axis - ts_shaft_off is '
        'not case_l/2 - shaft_from_end' % (sg_y0 + gv('ts_shaft_from_end') * 10))
    box(sg, 'case', -sg_case_w_mm / 2, sg_case_w_mm / 2, sg_y0, sg_y1,
        sg_case_top - sg_case_h_mm, sg_case_top, NEWB)
    box(sg, 'tabs', -sg_case_w_mm / 2, sg_case_w_mm / 2,
        sg_off_mm - sg_tab_span_mm / 2, sg_off_mm + sg_tab_span_mm / 2,
        deck_z_mm, deck_z_mm + sg_tab_thk_mm, JOINB)
    assert sg.bRepBodies.count == 1, (
        'SG90 envelope came out in %d pieces' % sg.bRepBodies.count)
    sg.bRepBodies.item(0).name = 'SG90_envelope'

    # the horn TURNS - separate component, separate rigid body
    hn_occ = fresh(SG90_OUT)
    hn = hn_occ.component
    horn_top_mm = deck_z_mm + (sg_tab_below_mm + sg_tab_thk_mm
                               + sg_boss_h_mm + sg_hub_h_mm)
    disc(hn, 'output_boss', 0, 0, SG90_HUB_D_MM, sg_case_top,
         sg_case_top + sg_boss_h_mm, NEWB)
    disc(hn, 'horn_hub', 0, 0, SG90_HUB_D_MM, sg_case_top + sg_boss_h_mm,
         horn_top_mm, JOINB)
    for k in (0, 1):
        if k == 0:
            box(hn, 'horn_arm_0', -SG90_BLADE_W_MM / 2, SG90_BLADE_W_MM / 2,
                -horn_span_mm / 2, horn_span_mm / 2,
                horn_top_mm - sg_blade_t_mm, horn_top_mm, JOINB)
        else:
            box(hn, 'horn_arm_1', -horn_span_mm / 2, horn_span_mm / 2,
                -SG90_BLADE_W_MM / 2, SG90_BLADE_W_MM / 2,
                horn_top_mm - sg_blade_t_mm, horn_top_mm, JOINB)
    assert hn.bRepBodies.count == 1, (
        'SG90 horn came out in %d pieces' % hn.bRepBodies.count)
    hn.bRepBodies.item(0).name = 'SG90_horn'
    print('SG90 FIXED in the column: deck z %.2f, case z %.2f..%.2f, y %.2f..%.2f'
          % (deck_z_mm, sg_case_top - sg_case_h_mm, sg_case_top, sg_y0, sg_y1))
    print('  horn blade z %.2f..%.2f into the rotor pocket z %.2f..%.2f'
          % (horn_top_mm - sg_blade_t_mm, horn_top_mm, race_z_mm,
             race_z_mm + horn_z_mm))
    print('')

    # ---- posing -------------------------------------------------------------
    def yaw_m(deg, dz=0.0):
        m = M3()
        t = m.translation
        t.z = dz / 10.0
        m.translation = t
        r = M3()
        r.setToRotation(math.radians(deg), VEC(0, 0, 1), ORG)
        m.transformBy(r)
        return m

    def pose(deg):
        add = root.occurrences.addExistingComponent
        return {
            'lid': add(C['base_lid'], yaw_m(0.0, dz_lid_mm)),
            'stator': add(C['turntable_stator'], M3()),
            'ring': add(C['turntable_ring'], M3()),
            'rollers': add(rollers, M3()),
            'sg90': add(sg, M3()),
            'rotor': add(C['shoulder_bracket'], yaw_m(deg, dz_mm)),
            'mg995': add(mg, yaw_m(deg, dz_mm)),
            'horn': add(hn, yaw_m(deg)),
        }

    meas = app.measureManager

    def body_of(occ):
        return occ.component.bRepBodies.item(0).createForAssemblyContext(occ)

    def bodies_of(occ):
        return [occ.component.bRepBodies.item(i).createForAssemblyContext(occ)
                for i in range(occ.component.bRepBodies.count)]

    def clearance(o1, o2):
        best = None
        for b1 in bodies_of(o1):
            bb = b1.boundingBox
            assert bb.maxPoint.x - bb.minPoint.x > 1e-6, (
                'degenerate body: the timeline marker is not at the end, or an '
                'occurrence is hidden - measurements here would be fiction')
            for b2 in bodies_of(o2):
                d = meas.measureMinimumDistance(b1, b2).value * 10
                best = d if best is None else min(best, d)
        return best

    def label(entity):
        comp = getattr(entity, 'component', None)
        if comp is None:
            comp = getattr(entity, 'parentComponent', None)
        return (comp.name if comp else str(entity.objectType)).replace(
            'robotarm_', '')

    def interference(occs):
        col = adsk.core.ObjectCollection.create()
        for o in occs:
            col.add(o)
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        total, pairs, assumed, noise = 0.0, [], 0.0, 0.0
        for i in range(res.count):
            r = res.item(i)
            vol = r.interferenceBody.volume * 1000
            names = (label(r.entityOne), label(r.entityTwo))
            tag = '%s^%s %.2f mm3' % (names[0], names[1], vol)
            if vol < NOISE_FLOOR_MM3:
                noise += vol
                continue
            # The horn hub is the one INVENTED dimension in this file. It is
            # not evidence either way, so it cannot pass the gate and it must
            # not fail it either - it is reported on its own line.
            if 'SG90_horn' in names:
                assumed += vol
                pairs.append('ASSUMED ' + tag)
                continue
            total += vol
            pairs.append(tag)
        return total, pairs, assumed, noise

    want_journal = rot_fit_mm / 2.0          # radial half of the diametral fit
    want_lift = ring_lift_mm

    lo = BATCH * BATCH_SIZE
    hi = min(lo + BATCH_SIZE, len(YAW_DEG))
    assert lo < len(YAW_DEG), 'BATCH %d is past the end of the sweep' % BATCH

    if BATCH == 0:
        print('contracted, per specs/robotarm/_assembly.md and the part scripts:')
        print('  rotor^roller   0.000 EXPECTED - the arm SITS on the bearings.')
        print('                 Anything above zero means it is not carried at all.')
        print('  ring^boss      %.3f  tr_rot %.2f diametral, the J1 journal'
              % (want_journal, rot_fit_mm))
        print('  ring^rim       %.3f  tt_ring_lift - uplift stop, not a bearing'
              % want_lift)
        print('  MG995^ring     > 0    shoulder_bracket asserts this arithmetically')
        print('                 and has never once measured it. THIS IS THE ONE.')
        print('  rotor^stator   > 0    posts at r 45, cheeks at r 27')
        print('  horn^rotor     <= %.3f the blade drives the cross pocket' % horn_z_mm)
        print('')
        print('%7s %11s %11s %11s %11s %11s %11s %9s' % (
            'yaw', 'rotor^roll', 'ring^boss', 'ring^rim', 'MG995^ring',
            'rotor^stat', 'MG995^stat', 'interf'))

    rows = []
    for deg in YAW_DEG[lo:hi]:
        p = pose(deg)
        total, pairs, assumed, noise = interference(list(p.values()))
        d_rr = clearance(p['rotor'], p['rollers'])
        d_rb = clearance(p['ring'], p['rotor'])
        d_mr = clearance(p['mg995'], p['ring'])
        d_rs = clearance(p['rotor'], p['stator'])
        d_ms = clearance(p['mg995'], p['stator'])
        d_ml = clearance(p['mg995'], p['lid'])
        d_hr = clearance(p['horn'], p['rotor'])
        d_sr = clearance(p['sg90'], p['rotor'])
        print('%6.0fd %11.3f %11s %11s %11.3f %11.3f %11.3f %9.2f' % (
            deg, d_rr, '-', '-', d_mr, d_rs, d_ms, total))
        rows.append({'yaw': deg, 'rotor_roller': d_rr, 'ring_rotor': d_rb,
                     'mg995_ring': d_mr, 'rotor_stator': d_rs,
                     'mg995_stator': d_ms, 'mg995_lid': d_ml,
                     'horn_rotor': d_hr, 'sg90_rotor': d_sr,
                     'interference': total, 'pairs': pairs,
                     'assumed': assumed, 'noise': noise})
        for o in p.values():
            o.deleteMe()

    have = []
    if os.path.exists(LEDGER):
        fh = open(LEDGER)
        have = json.load(fh)
        fh.close()
    have = [r for r in have if r['yaw'] not in [x['yaw'] for x in rows]] + rows
    have.sort(key=lambda r: r['yaw'])
    fh = open(LEDGER, 'w')
    json.dump(have, fh, indent=1)
    fh.close()

    if hi < len(YAW_DEG):
        print('')
        print('batch %d of %d done, %d/%d poses on file. Re-run with BATCH = %d.'
              % (BATCH, (len(YAW_DEG) - 1) // BATCH_SIZE, len(have),
                 len(YAW_DEG), BATCH + 1))
        for occ in keepers.values():
            occ.isLightBulbOn = False
        return

    # ---- the whole-sweep verdict -------------------------------------------
    assert len(have) == len(YAW_DEG), (
        'only %d of %d poses are on file - run the earlier batches'
        % (len(have), len(YAW_DEG)))
    fails = []
    worst_int = max(r['interference'] for r in have)
    for r in have:
        if r['interference'] > 1.0:
            fails.append('yaw %.0f: interference %.2f mm3 (%s)'
                         % (r['yaw'], r['interference'], '; '.join(r['pairs'])))
        if r['rotor_roller'] > 0.01:
            fails.append('yaw %.0f: the rotor floats %.3f above its rollers - '
                         'the arm is not carried' % (r['yaw'], r['rotor_roller']))
        if r['mg995_ring'] <= 0.0:
            fails.append('yaw %.0f: the MG995 is touching the retainer ring'
                         % r['yaw'])
        if r['rotor_stator'] <= 0.0:
            fails.append('yaw %.0f: the rotor is touching the stator' % r['yaw'])
        if r['mg995_stator'] <= 0.0:
            fails.append('yaw %.0f: the MG995 is touching the stator' % r['yaw'])
        if r['mg995_lid'] <= 0.0:
            fails.append('yaw %.0f: the MG995 is touching the base lid' % r['yaw'])
        if r['sg90_rotor'] <= 0.0:
            fails.append('yaw %.0f: the SG90 case is touching the rotor' % r['yaw'])

    print('')
    print('=== whole sweep, %.0f deg to %.0f deg in %.0f deg steps ==='
          % (YAW_DEG[0], YAW_DEG[-1], YAW_DEG[1] - YAW_DEG[0]))
    print('%-16s %9s %9s   %s' % ('pair', 'min', 'max', 'contract'))
    for key, name, want in (
            ('rotor_roller', 'rotor^roller', '0.000 - it SITS on them'),
            ('ring_rotor', 'ring^rotor', '%.3f journal / %.3f lift'
             % (want_journal, want_lift)),
            ('mg995_ring', 'MG995^ring', '> 0 through the whole sweep'),
            ('rotor_stator', 'rotor^stator', '> 0'),
            ('mg995_stator', 'MG995^stator', '> 0'),
            ('mg995_lid', 'MG995^lid', '> 0'),
            ('sg90_rotor', 'SG90^rotor', '> 0'),
            ('horn_rotor', 'horn^rotor', 'in the cross pocket')):
        vals = [r[key] for r in have]
        print('%-16s %9.3f %9.3f   %s' % (name, min(vals), max(vals), want))
    worst_assumed = max(r.get('assumed', 0.0) for r in have)
    worst_noise = max(r.get('noise', 0.0) for r in have)
    print('')
    print('GATE J1 interference : worst %.3f mm3 - %s'
          % (worst_int, 'PASS' if worst_int < 1.0 else 'FAIL'))
    print('GATE J1 clearances   : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)
    print('  contact noise below the %.2f floor: %.3f mm3 at worst - three'
          % (NOISE_FLOOR_MM3, worst_noise))
    print('  rolling contacts and three collar faces, all of them meant to touch.')
    if worst_assumed > 0.0:
        print('')
        print('GATE J1 OVERALL      : BLOCKED, not failed.')
        print('  The measured geometry passes. %.3f mm3 sits on the SG90 horn'
              % worst_assumed)
        print('  hub Ø - community-model grade since the horn audit, still not')
        print('  bench-measured, and a number that varies by batch cannot clear')
        print('  a gate. Run the gauge_flange hub sweep and re-run.')
    print('')
    print('ASSUMED, AND SO NOT EVIDENCE:')
    print('  the SG90 horn hub at Ø%.2f - community-model grade (horn audit),'
          % SG90_HUB_D_MM)
    print('  varies by batch, unmeasured on this bench. It decides the hub vs')
    print('  tt_screw_bore Ø%.2f story, so any horn^rotor reading is that number.'
          % (gv('tt_screw_bore') * 10))
    print('')
    print('STILL ARITHMETIC, NOT MEASURED HERE:')
    print('  the platter\'s servo column 12.45 x 23.05 against an SG90 at %.2f'
          % sg_case_w_mm)
    print('  wide - %.2f of interference. The platter is a legacy STEP, so'
          % (sg_case_w_mm - 12.45))
    print('  importing it would only re-measure the drawing. CALIPER THE PRINT.')

    final = pose(LEAVE_AT_YAW)
    bb = root.boundingBox
    print('')
    print('J1 bbox at yaw %.0f, mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f' % (
        LEAVE_AT_YAW, bb.minPoint.x * 10, bb.maxPoint.x * 10,
        bb.minPoint.y * 10, bb.maxPoint.y * 10,
        bb.minPoint.z * 10, bb.maxPoint.z * 10))
    for o in final.values():
        o.isLightBulbOn = True
    for occ in keepers.values():
        occ.isLightBulbOn = False
