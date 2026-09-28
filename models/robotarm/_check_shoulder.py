"""robotarm/_check_shoulder - the J2 gate.

Rebuilds the shoulder from its committed scripts, assembles it from FRESH
occurrences through J2's declared travel, and asserts that nothing touches
anything it should not.

Same three failure modes _check_wrist watches for (a part carved to fit its
neighbour, a measurement of nothing, a joint that assembles at zero and jams
at sixty), plus one this joint has and the wrist does not:

4. THE SERVO IS THE BIGGEST THING AT J2 AND IT IS NOT A PRINTED PART. An
   MG995 is 40.9 x 20 x 36.5 with tabs spanning 54.0, and none of it appears in
   any model file - the bracket only cuts a hole where it goes. So this gate
   builds the servo as a scratch envelope (case, tab plate, output boss,
   spline) and sweeps the arm past it. Getting that envelope's ORIGIN wrong is
   the easy mistake, so it is spelled out below rather than left as three
   numbers.

THERE IS NO HORN HERE ANY MORE, AND THAT IS THE 2026-08-31 REPAIR. Until that
date this file built a stamped MG995 horn - hub, two blades, trimmed to
r 7.6 - and interfered it against shoulder_hub. shoulder_hub does not have a
horn pocket now: it BORES STRAIGHT ONTO THE SPLINE (lib/servo_hub.spline_hub,
the same migration j3_pinion.py had). So the horn envelope sat inside the
hub's solid collar and reported roughly 250 mm3 at every pitch - a FALSE
collision, in a gate whose whole job is to be believed. Every sh_horn_*
parameter it cross-read is gone as well. What turns at J2 is the output boss
and the spline, so that is what turns here.

THE SPLINE IS MODELLED AT THE BROACHED DIAMETER, NOT THE FREE ONE, and the
reason is the same argument the output boss already carries below. Ø5.9 of
steel spline in a Ø5.65 printed bore is a 0.25 mm DESIGNED interference - it
is how the joint is meant to be assembled - and modelling it free would post
8.2 mm3 of "interference" at every pose. Constant across a sweep is the tell:
a real collision moves. The press fit is still checked, as arithmetic, against
lib/servo.SPLINE_BROACH_INTERFERENCE_MM and shoulder_hub's own sh_broach_d -
the gate that can measure it is a printed gauge, not this one.

EVERY SERVO NUMBER IS READ FROM lib/servo.py. They used to be typed here -
case_h 3.65, tab_span 5.40, boss 1.30 x 0.30 - four copies of a datum that
lives in the library, in a file whose docstring is about the cost of getting
the envelope wrong. Two of them are on the sweep's critical dimension.

THE POSITIVE CONTROL. The last thing this gate does is drive the output stack
CONTROL_SHIFT_MM further up the hub's bore and require that the interference
analysis registers it. A sweep that reports 0.00 mm3 because it is looking at
nothing reads exactly like a sweep that reports 0.00 mm3 because the joint is
clean, and the two are not the same result. If the control does not fire,
nothing above it means anything and the run fails.

THE SERVO ENVELOPE, DERIVED NOT ASSUMED. lib/servo.py puts the origin on the
output shaft axis at the TAB PLANE - the underside of the mounting tabs, the
face a bracket clamps - with +Z out of the shaft. tab_below_top is measured to
the TOP of the tabs, so the underside sits tab_below_top + tab_thk = 9.7 mm
from the case top. That sum is exactly sb_lobe_t, which is why the pad is that
thick and not a chosen number: the tabs bear on the pad's OUTER face, the
screws go inboard from there, and the case top lands flush on sb_plate_out.
The case body then runs OUTBOARD from that face, through the pad's window and
out the far side. Model it the other way round and the servo appears to be
buried in the arm.
"""

import importlib.util
import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
# PURGED FIRST. The part scripts this gate execs delete lib.* out of
# sys.modules themselves, so a stale copy imported by an earlier run of a
# different gate is exactly the kind of thing that makes two files disagree
# about a servo. Bind the objects once, here, from a fresh import.
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

from lib.servo import CATALOG, spline_bore_d  # noqa: E402
from lib.servo import MG995_TAB_RIB_TOP_MM, MG995_TAB_RIB_W_MM  # noqa: E402
from lib.servo import (MG995_LIP_H_MM, MG995_LIP_W_MM, MG995_LIP_R_MM,  # noqa: E402
                       MG995_LIP_FAR_INSET_MM)

MG995 = CATALOG['MG995']
PARTS = ['wrist_hub', 'shoulder_hub', 'upper_arm', 'shoulder_bracket']
# J2's declared travel. The down end is NOT symmetric and NOT arbitrary: the
# arm reaches the turntable's retainer ring at about -27 deg (shoulder_bracket.py
# scans for it), so -25 is the limit with a margin. It used to be -40, when the
# base was a 40 mm rectangular plate rather than a Ø100 ring.
PITCH_DEG = [-25.0, -10.0, 0.0, 30.0, 60.0, 90.0, 120.0, 160.0]
LEAVE_AT_PITCH = 30.0
# Same spin as the wrist: the hub's hex is drawn with a vertex on its local +X,
# every socket in this arm with a vertex on the assembly's +Y.
HUB_SPIN_DEG = 90.0
# RUN THIS TWICE: REBUILD=True, then REBUILD=False. Four parts plus eight poses
# of interference analysis is over the 60 s MCP call limit in one go, exactly as
# _check_pruner is. The loader sets it - `mod.REBUILD = False` - so the pass that
# does the measuring never touches the geometry it is measuring.
REBUILD = True
# How far the positive control drives the output stack up the hub's bore. It
# has to be bigger than any fit in the stack and smaller than the collar, so
# that a hit is unambiguous and is still INSIDE the part rather than out the
# far side of it: sh_collar_l is 7.00 and the boss bore is 2.50 deep, so 4.0
# lands the Ø13 boss squarely in the Ø5.65 broach bore. Same number, and the
# same reasoning, as _check_servo_fit.CONTROL_SHIFT_MM.
CONTROL_SHIFT_MM = 4.0
# Below this an interference is kernel facet noise on a face two bodies are
# meant to share, not a collision. _check_j1 carries the same floor and the
# same argument.
CONTROL_FLOOR_MM3 = 0.05
# HOW CLOSE TWO NUMBERS HAVE TO BE TO COUNT AS THE SAME NUMBER, in mm, and it
# is not an arbitrary epsilon. Every sh_ parameter this gate cross-reads is
# written by shoulder_hub.py as '%.4f mm', so a value can come back up to half
# a ten-thousandth off what the library solved. A tolerance tighter than the
# precision the number was STORED at fails on rounding and reads as a real
# disagreement, which is the most expensive kind of false alarm a gate has.
PARAM_ROUNDING_MM = 1e-4


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    ups = design.userParameters
    M3 = adsk.core.Matrix3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)

    def gv(name):
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        return p.value

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

    root = design.rootComponent
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
            'a later part script cut into an earlier part: ' + '; '.join(scars) +
            ' - set participantBodies on every non-NewBody feature')
        print('volume unchanged after all parts built: %s' % ', '.join(
            '%s %.0f mm3' % (k, v * 1000) for k, v in sorted(built_volume.items())))
        print('THIS PASS BUILT ONLY. Re-run with REBUILD=False to measure.')
        return
    for name in PARTS:
        assert 'robotarm_' + name in keepers, (
            'robotarm_%s is not in the document - run the REBUILD=True pass first'
            % name)
        print('%s %.0f mm3' % (name, keepers['robotarm_' + name]
                               .component.bRepBodies.item(0).volume * 1000))
    print('')

    C = dict((n, keepers['robotarm_' + n].component) for n in PARTS)

    plate_in = gv('sb_plate_in')
    plate_out = gv('sb_plate_out')
    lobe_t = gv('sb_lobe_t')
    gap = gv('sb_gap')
    rot = gv('sb_rot')
    loc = gv('wh_loc')
    tol = gv('sb_tol')
    l1 = gv('ua_l1')

    # ---- the MG995, as a scratch envelope -----------------------------------
    # Rebuilt every run so it can never drift from the parameters the bracket
    # was cut from. Three boxes on the shaft axis; see the module docstring for
    # why the tab plane and not the case is the datum.
    ENV = 'robotarm_MG995_envelope'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == ENV or c.name.startswith(ENV + ' ('):
            c.name = ENV + '_stale_' + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(ENV + '_stale_'):
            occ.deleteMe()
    env_occ = root.occurrences.addNewComponent(M3())
    env = env_occ.component
    env.name = ENV
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def mm(cm):
        return '%.4f mm' % (cm * 10.0)

    def env_box(name, y0, y1, z0, z1, x0, x1, op):
        sk = env.sketches.add(env.yZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            sk.modelToSketchSpace(P3(0, y0, z0)), sk.modelToSketchSpace(P3(0, y1, z1)))
        assert sk.profiles.count == 1, name
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = env.features.extrudeFeatures.createInput(col, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(x0)))
        inp.setDistanceExtent(False, V(mm(x1 - x0)))
        if op != adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
            inp.participantBodies = [env.bRepBodies.item(i)
                                     for i in range(env.bRepBodies.count)]
        env.features.extrudeFeatures.add(inp).name = name

    def env_cyl(name, y_c, z_c, d, x0, x1, op):
        """ROUND, not a box. Modelling the Oe13 output boss as a 13 x 13 prism
        put its four corners at r 9.19 - a millimetre outside the hub's 16.4
        mouth - and reported 9.7 mm3 of interference at every pose. Constant
        across a sweep is the tell: a real collision moves."""
        sk = env.sketches.add(env.yZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(0, y_c, z_c)), d / 2)
        assert sk.profiles.count == 1, name
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        inp = env.features.extrudeFeatures.createInput(col, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(x0)))
        inp.setDistanceExtent(False, V(mm(x1 - x0)))
        if op != adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
            inp.participantBodies = [env.bRepBodies.item(i)
                                     for i in range(env.bRepBodies.count)]
        env.features.extrudeFeatures.add(inp).name = name

    NEWB = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOINB = adsk.fusion.FeatureOperations.JoinFeatureOperation

    # EVERYTHING IN CENTIMETRES, because that is what Fusion answers in and
    # what env_box/env_cyl are given. lib/servo.py is in millimetres, so every
    # library read is divided once, here, and never again.
    case_w = gv('sb_case_w')
    case_l = gv('sb_case_l')
    case_h = MG995.case_h / 10.0        # lib/servo.py - to the LIP top, drawing 2026-09-28
    boss_d = MG995.boss_dia / 10.0      # the Ø13.0 output collar
    boss_h = MG995.boss_h / 10.0
    spline_d = MG995.spline_dia / 10.0  # Ø5.9 of 25-tooth spline above it
    spline_h = MG995.spline_h / 10.0
    broach_d = spline_bore_d(MG995) / 10.0     # per-servo, gauged 2026-09-28
    tab_thk = gv('sb_tab_thk')
    tab_span = MG995.tab_span / 10.0    # TowerPro official E 54.0
    case_hi = gv('sb_shaft_end')
    case_lo = case_hi - case_l
    tab_plane = plate_out + lobe_t          # the datum. See the docstring.
    # sb_horn_standoff is RETIRED and shoulder_bracket keeps it as a named
    # zero so the history stays legible. It is read with gv(), not with a
    # guarded itemByName: if it is ever actually deleted this gate must stop,
    # because sb_lobe_t is derived from it and the servo would silently move.
    standoff = gv('sb_horn_standoff')
    case_top = plate_out + standoff         # 0.0 since the standoff retired
    # THE LIP (drawing 2026-09-28). lib's case_h and tab_below_top both run
    # to the LIP top, and it is the lip that lands on plate_out; the case
    # proper starts lip_h outboard of it. So `case_top` here IS the lip top.
    lip_h = MG995_LIP_H_MM / 10.0
    lip_top = case_top
    assert abs((tab_plane - case_top)
               - (gv('sb_tab_below_top') + gv('sb_tab_thk'))) < 1e-9, (
        'the case top is not tab stack below the tab plane - sb_lobe_t is '
        'not tab_below_top + tab_thk + horn_standoff any more')
    # THE BRACKET'S COPIES, AGAINST THE LIBRARY. shoulder_bracket declares the
    # MG995's case and tab dimensions as its own sb_ parameters; lib/servo.py
    # is where they come from. Nothing in this project checks that the two
    # still agree, and a bracket cut from a stale case width is precisely the
    # failure this gate exists to catch and cannot see - a pocket and an
    # envelope built from the same wrong number agree perfectly.
    for pname, lib_mm in (('sb_case_w', MG995.case_w),
                          ('sb_case_l', MG995.case_l),
                          ('sb_tab_thk', MG995.tab_thk),
                          ('sb_tab_below_top', MG995.tab_below_top),
                          ('sb_shaft_end', MG995.shaft_from_end)):
        assert abs(gv(pname) * 10 - lib_mm) < 1e-6, (
            '%s is %.3f but lib/servo.py says %.3f - shoulder_bracket and the '
            'library disagree about the MG995, so this envelope is testing a '
            'servo that neither of them describes' % (pname, gv(pname) * 10, lib_mm))
    env_box('case', -case_w / 2, case_w / 2, case_lo, case_hi,
            case_top + lip_h, case_top + case_h, NEWB)
    env_box('lip', -MG995_LIP_W_MM / 20.0, MG995_LIP_W_MM / 20.0,
            case_lo + MG995_LIP_FAR_INSET_MM / 10.0, MG995_LIP_R_MM / 10.0,
            lip_top, lip_top + lip_h, JOINB)
    # THE TAB BODY RUNS INBOARD OF THE TAB PLANE - from the tab underside
    # (the plane) toward the case top. This box sat on the OUTBOARD side,
    # tab_plane .. + tab_thk, from before the flange recess existed, and so
    # could never see the recess or anything standing on the tab top.
    # Corrected 2026-09-28 with the MG995 redrawn from Jonathan's drawing.
    tab_mid = (case_hi + case_lo) / 2
    env_box('tabs', -case_w / 2, case_w / 2,
            tab_mid - tab_span / 2, tab_mid + tab_span / 2,
            tab_plane - tab_thk, tab_plane, JOINB)
    # and the rib on each tab, square to its full height (lib/servo.py)
    rib_hw = MG995_TAB_RIB_W_MM / 20.0
    rib_top = MG995_TAB_RIB_TOP_MM / 10.0
    for z0, z1 in ((tab_mid - tab_span / 2, case_lo), (case_hi, tab_mid + tab_span / 2)):
        env_box('tab_rib', -rib_hw, rib_hw, z0, z1, tab_plane - rib_top, tab_plane, JOINB)
    assert env.bRepBodies.count == 1, 'servo envelope came out in %d pieces' % (
        env.bRepBodies.count)
    env.bRepBodies.item(0).name = 'MG995_envelope'

    # ---- and the output stack, WHICH TURNS --------------------------------
    # A separate component because it is a separate rigid body: the case is
    # bolted to the bracket and never moves, but the boss and the spline turn
    # with the joint. Modelled as one static lump the old horn version of this
    # reported a tidy 49 mm3 at every pitch EXCEPT 0 and 90 - which was the
    # cross's own period, and the giveaway that the fault was the placement.
    OUT = 'robotarm_MG995_output'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == OUT or c.name.startswith(OUT + ' ('):
            c.name = OUT + '_stale_' + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(OUT + '_stale_'):
            occ.deleteMe()
    out_occ = root.occurrences.addNewComponent(M3())
    out = out_occ.component
    out.name = OUT
    env, out = out, env          # env_box/env_cyl close over `env`
    # THE INTERFACE THAT ACTUALLY SHIPS: Ø13.0 x 3.0 of output collar, then
    # Ø5.9 x 3.6 of spline above it. Both DATASHEET, both read from
    # lib/servo.py. This stack runs INBOARD from the case top - the servo's
    # +Z is this frame's -X, see the docstring - so each piece starts where
    # the one below it ended and the arithmetic never has to be done twice.
    boss_top = lip_top - boss_h                    # top of the collar, off the LIP
    spline_top = boss_top - spline_h               # top of the spline
    env_cyl('output_boss', 0.0, 0.0, boss_d, boss_top, lip_top, NEWB)
    # AT THE BROACHED DIAMETER, NOT THE FREE ONE - docstring, and the same
    # argument env_cyl itself carries about the boss. The 0.25 mm of designed
    # interference is checked as arithmetic below, where it can be read.
    env_cyl('output_spline', 0.0, 0.0, broach_d, spline_top, boss_top, JOINB)
    env, out = out, env
    assert out.bRepBodies.count == 1, 'output stack came out in %d pieces' % (
        out.bRepBodies.count)
    out.bRepBodies.item(0).name = 'MG995_output'

    # ---- THE HUB'S BORE, AGAINST THE SHAFT IT IS BORED FOR ------------------
    # Interference can see a bore that is too SMALL. It cannot see a bore that
    # is bored from the wrong servo, because a hole and a shaft cut from the
    # same wrong number pass each other perfectly. These four are the whole
    # spline contract and they are checked unguarded: shoulder_hub is in PARTS,
    # so if one of them is missing this gate is not looking at the shoulder.
    hub_seat = tab_plane - gv('sh_seat_z')         # X of the hub's underside
    hub_top = hub_seat - gv('sh_collar_l')         # ... and of its top face
    tol_cm = PARAM_ROUNDING_MM / 10.0
    assert abs(gv('sh_boss_bore_d') - (boss_d + gv('sh_free_fit'))) < tol_cm, (
        'sh_boss_bore_d is %.3f but the MG995 collar is %.3f and sh_free_fit '
        'is %.3f - the lower bore no longer clears the boss it is for'
        % (gv('sh_boss_bore_d') * 10, boss_d * 10, gv('sh_free_fit') * 10))
    assert abs(gv('sh_broach_d') - broach_d) < tol_cm, (
        'sh_broach_d is %.3f but the spline is %.3f less the %.3f of designed '
        'broach interference = %.3f - the press fit this joint is assembled by '
        'is not the one shoulder_hub is cut for'
        % (gv('sh_broach_d') * 10, spline_d * 10,
           spline_d * 10 - broach_d * 10, broach_d * 10))
    # and the geometric half of the same question: does the spline REACH?
    engaged = min(boss_top, hub_seat) - max(spline_top, hub_top)
    assert abs(engaged - gv('sh_engaged')) < tol_cm, (
        'the spline and the hub overlap over %.3f mm in this assembly but '
        'sh_engaged says %.3f - the hub is seated somewhere other than where '
        'lib/servo_hub solved it' % (engaged * 10, gv('sh_engaged') * 10))
    print('MG995 output: boss Ø%.2f x %.2f then spline Ø%.2f x %.2f, modelled '
          'at the broached Ø%.2f' % (boss_d * 10, boss_h * 10, spline_d * 10,
                                     spline_h * 10, broach_d * 10))
    print('  shoulder_hub seats at X %.2f, tops out at X %.2f, and grips %.2f '
          'mm of spline - NO HORN in the path' % (hub_seat * 10, hub_top * 10,
                                                  engaged * 10))
    for name in (ENV, OUT):
        keepers.pop(name, None)
    print('MG995 envelope: tab plane x %.1f, case top x %.1f, case x %.1f..%.1f, '
          'z %.1f..%.1f' % (tab_plane * 10, case_top * 10, case_top * 10,
                            (case_top + case_h) * 10, case_lo * 10, case_hi * 10))
    print('  output stack inboard of that: boss Ø%.1f x %.1f then spline '
          'Ø%.1f x %.1f, reaching x %.1f' % (
              boss_d * 10, boss_h * 10, broach_d * 10, spline_h * 10,
              spline_top * 10))
    print('')

    def rot_m(angle, axis):
        m = M3()
        m.setToRotation(angle, axis, ORG)
        return m

    def place_hub(sx, pitch):
        """local +Z is the hex and has to point INBOARD; local z = 0 lands on
        the plate's inner face. Both J2 hubs are KEYED INTO the upper arm, so
        both turn with the pitch and run in the bracket's bores - exactly as
        the J4 hubs turn with the roll housing."""
        m = rot_m(math.radians(HUB_SPIN_DEG), VEC(0, 0, 1))
        m.transformBy(rot_m(-sx * math.pi / 2, VEC(0, 1, 0)))
        t = m.translation
        t.x = sx * plate_in
        m.translation = t
        m.transformBy(rot_m(math.radians(pitch), VEC(1, 0, 0)))
        return m

    def place_arm(pitch):
        """upper_arm is drawn with its origin on J3 and J2 at y = -ua_l1, so it
        slides forward by l1 to put J2 on this frame's origin, then pitches
        about it. Positive pitch is UP."""
        m = M3()
        t = m.translation
        t.y = l1
        m.translation = t
        m.transformBy(rot_m(math.radians(pitch), VEC(1, 0, 0)))
        return m

    def pose(pitch):
        add = root.occurrences.addExistingComponent
        return {
            'bracket': add(C['shoulder_bracket'], M3()),
            'servo': add(env, M3()),
            'output': add(out, rot_m(math.radians(pitch), VEC(1, 0, 0))),
            'arm': add(C['upper_arm'], place_arm(pitch)),
            'hub_drive': add(C['shoulder_hub'], place_hub(+1, pitch)),
            'hub_idler': add(C['wrist_hub'], place_hub(-1, pitch)),
        }

    meas = app.measureManager

    def body_of(occ):
        return occ.component.bRepBodies.item(0).createForAssemblyContext(occ)

    def clearance(o1, o2):
        b1, b2 = body_of(o1), body_of(o2)
        for b in (b1, b2):
            bb = b.boundingBox
            assert bb.maxPoint.x - bb.minPoint.x > tol, (
                'degenerate body: the timeline marker is not at the end, or the '
                'occurrence is hidden - measurements here would be fiction')
        return meas.measureMinimumDistance(b1, b2).value * 10

    def label(entity):
        comp = getattr(entity, 'component', None)
        if comp is None:
            comp = getattr(entity, 'parentComponent', None)
        return (comp.name if comp else str(entity.objectType)).replace('robotarm_', '')

    def interference(occs):
        col = adsk.core.ObjectCollection.create()
        for o in occs:
            col.add(o)
        inp = design.createInterferenceInput(col)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        total, pairs = 0.0, []
        for i in range(res.count):
            r = res.item(i)
            vol = r.interferenceBody.volume * 1000
            total += vol
            pairs.append('%s^%s %.2f mm3' % (label(r.entityOne), label(r.entityTwo), vol))
        return total, pairs

    want_arm_br = gap * 10
    want_hub_br = rot / 2 * 10
    want_hub_arm = loc / 2 * 10

    print('=== J2 shoulder fit check ===')
    print('straddle %.1f | plate inner face |x| %.1f | running gap %.2f each side'
          % (gv('wr_straddle') * 10, plate_in * 10, gap * 10))
    print('')
    print('contracted, per specs/robotarm/_assembly.md:')
    print('  arm^bracket  >= %.3f  free fit, the pitch joint running gap' % want_arm_br)
    print('  hub^bracket  0.000 EXPECTED: the drive hub is flangeless (2026-08-30)')
    print('  hub^arm      0.000 EXPECTED: the hex bottoms in its socket')
    print('               Those two stops are what trap the hub with no screw. The')
    print('               fit that matters is RADIAL (%.3f / %.3f) and only'
          % (want_hub_br, want_hub_arm))
    print('               interference can see it.')
    print('  servo^arm    > 0     the MG995 is entirely outboard of the straddle,')
    print('               so this should not even be close through the whole sweep.')
    print('')
    print('%8s %12s %12s %12s %12s %10s' % (
        'pitch', 'arm^brkt', 'hub^brkt', 'hub^arm', 'servo^arm', 'interf'))

    worst = 0.0
    fails = []
    for pitch in PITCH_DEG:
        p = pose(pitch)
        total, pairs = interference(list(p.values()))
        worst = max(worst, total)
        d_ab = clearance(p['arm'], p['bracket'])
        d_hb = clearance(p['hub_drive'], p['bracket'])
        d_ha = clearance(p['hub_drive'], p['arm'])
        d_sa = clearance(p['servo'], p['arm'])
        print('%7.0f%s %12.3f %12.3f %12.3f %12.3f %10.2f' % (
            pitch, 'd', d_ab, d_hb, d_ha, d_sa, total))
        if total > 1.0:
            fails.append('pitch %.0f: interference %.2f mm3 (%s)'
                         % (pitch, total, '; '.join(pairs)))
        if d_ab < want_arm_br - tol * 10:
            fails.append('pitch %.0f: arm^bracket %.3f < %.3f' % (pitch, d_ab, want_arm_br))
        if d_sa <= tol * 10:
            fails.append('pitch %.0f: the MG995 envelope is touching the arm' % pitch)
        for o in p.values():
            o.deleteMe()

    final = pose(LEAVE_AT_PITCH)
    printed = sum(body_of(o).physicalProperties.mass
                  for k, o in final.items() if k not in ('servo', 'output'))
    bb = root.boundingBox
    print('')
    print('shoulder bbox at pitch %.0f, mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f' % (
        LEAVE_AT_PITCH, bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('printed mass here, solid PETG %.2f g -> ~%.1f g at 40%% infill + 4 walls'
          % (printed * 1000, printed * 1000 * 0.6))
    print('  (+ 55 g of MG995, which this joint carries but does not lift)')
    print('')

    # ---- POSITIVE CONTROL: can this gate see a hit at all? -------------------
    # Every number above is a distance or a volume that came back small, and a
    # small number is what you get from a clean joint AND from an analysis that
    # is looking at nothing - a hidden occurrence, a timeline marker parked in
    # the middle of the history, a body that came back degenerate. The
    # clearance() helper guards its own inputs; the interference() helper has
    # never had a way to prove it can register anything.
    #
    # So: put the output stack CONTROL_SHIFT_MM further up the hub's bore,
    # where the Ø13 boss has to land in the Ø5.65 broach bore, and require the
    # analysis to say so. The shift is along the pitch axis itself, so it
    # commutes with the pose rotation and the control is the SAME assembly with
    # one part deliberately driven in - not a second, differently-built one.
    #
    # This runs BEFORE the gate verdicts print, and stops the run if it fails,
    # for the reason _check_servo_fit gives in the same situation: a clear
    # result from a blind check is worse than no result, because it is
    # indistinguishable from a real pass and it is believed.
    ctrl_m = rot_m(math.radians(LEAVE_AT_PITCH), VEC(1, 0, 0))
    ctrl_t = ctrl_m.translation
    ctrl_t.x = -CONTROL_SHIFT_MM / 10.0
    ctrl_m.translation = ctrl_t
    ctrl_occ = root.occurrences.addExistingComponent(out, ctrl_m)
    ctrl_vol, ctrl_pairs = interference([ctrl_occ, final['hub_drive']])
    ctrl_occ.deleteMe()
    print('positive control: output stack driven %.1f mm further up the bore '
          '-> %.2f mm3 (%s)' % (CONTROL_SHIFT_MM, ctrl_vol,
                                '; '.join(ctrl_pairs) if ctrl_pairs else 'nothing'))
    assert ctrl_vol > CONTROL_FLOOR_MM3, (
        'THE CHECK IS BLIND. The MG995 output stack was driven %.1f mm into '
        'shoulder_hub and the interference analysis registered %.3f mm3. '
        'Every clear result above is meaningless until this is fixed - it is '
        'not evidence that J2 assembles, it is evidence that nothing was '
        'measured.' % (CONTROL_SHIFT_MM, ctrl_vol))
    print('')
    # ---- GATE: can the drive hub actually be FITTED? ------------------------
    # Found 2026-08-30, on Jonathan trying to assemble J2 with the first hub
    # printed. It does not go in. The wr_ contract retains every hub with a
    # 24.0 flange too big to pass its own 20.35 journal bore - which is the
    # point of it - but on the DRIVE side the servo pad is bolted over the
    # counterbore, so the flange has to pass the pad's case window as well.
    # It is 20.4 wide in Y, and there is no path. Interference at a pose
    # cannot see this: every pose is fine, it is the JOURNEY that is blocked.
    #
    # The aperture is measured on the bracket, not assumed, because it is a
    # contract between two parts and a number only one file reads is a
    # decoration.
    ins_fails = []
    brk_body = C['shoulder_bracket'].bRepBodies.item(0)
    hub_body = C['shoulder_hub'].bRepBodies.item(0)
    OUTSIDE = adsk.fusion.PointContainment.PointOutsidePointContainment
    P3c = adsk.core.Point3D.create

    def clear_r_at(x_mm, lo=0.0, hi=16.0):
        # largest radius about the J2 axis that is free of bracket at this X
        for _ in range(14):
            mid = (lo + hi) / 2.0
            free = True
            for k in range(24):
                a = 2 * math.pi * k / 24
                if brk_body.pointContainment(P3c(
                        x_mm / 10.0, mid * math.cos(a) / 10.0,
                        mid * math.sin(a) / 10.0)) != OUTSIDE:
                    free = False
                    break
            if free:
                lo = mid
            else:
                hi = mid
        return lo

    up = design.userParameters
    x_in = up.itemByName('sb_plate_in').value * 10
    x_out = (up.itemByName('sb_plate_out').value
             + up.itemByName('sb_lobe_t').value) * 10
    aperture, at_x = 99.0, None
    x = x_in + 0.25
    while x <= x_out - 0.25:
        r = clear_r_at(x)
        if r < aperture:
            aperture, at_x = r, x
        x += 0.75

    hb = hub_body.boundingBox
    hub_r = max(abs(hb.minPoint.x), abs(hb.maxPoint.x),
                abs(hb.minPoint.y), abs(hb.maxPoint.y)) * 10
    print('')
    print('drive-side aperture: the bracket is clear to r %.2f mm all the way '
          'from the plate inner face (X %.1f) to the pad outer face (X %.1f);'
          % (aperture, x_in, x_out))
    print('   tightest at X %.2f. The hub is %.2f across at its widest.'
          % (at_x, hub_r * 2))
    if hub_r > aperture + 1e-6:
        ins_fails.append(
            'the drive hub is %.2f across and the tightest aperture on its '
            'insertion path is %.2f (at X %.2f) - it cannot be fitted from '
            'either side' % (hub_r * 2, aperture * 2, at_x))
    print('GATE hub_installs : %s' % ('PASS' if not ins_fails else 'FAIL'))
    for f in ins_fails:
        print('   %s' % f)

    print('GATE interference : worst %.3f mm3 - %s' % (
        worst, 'PASS' if worst < 1.0 else 'FAIL'))
    print('GATE clearances   : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)

    for occ in keepers.values():
        occ.isLightBulbOn = False
    env_occ.isLightBulbOn = False
    out_occ.isLightBulbOn = False
