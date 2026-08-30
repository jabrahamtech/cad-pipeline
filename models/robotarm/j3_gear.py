"""robotarm/j3_gear - Fusion MCP generating script.

Rebuilds `robotarm_j3_gear` (idempotent). Spec: lib/gears.py J3_PAIR.

THE 36T OUTPUT HALF OF THE ELBOW REDUCTION. It replaces the drive-side
`wrist_hub` at J3: same wr_ hex into the upper arm's socket, same O20
journal running in the forearm plate's bore, but instead of a 24.0
retaining flange it carries the gear.

WHY THE GEAR IS OUTBOARD OF THE FORK. Inside the straddle the forearm
already subtracts a 13.4 clearance cylinder about J3, and the web that
survives is an hourglass. A 47.5 gear would need that cylinder at 23.75
and there would be no web left. Outboard of the drive plate the -X face is
a clean plane - the only thing that ever stood proud of it was the J3
servo lobe, and the reduction moves that anyway. So the whole train lives
outside the fork and the straddle is untouched.

THE TEETH COME FROM lib/gears.py, NOT FROM THIS FILE. J3_PAIR.tooth_polar
generates the involute from the base circle. j3_pinion.py traces the same
function for its 18 teeth. A tooth form that two parts must share is not
something either part gets to own - that is the mistake this project keeps
making with datums and it is not going to be made with a gear mesh.

RETENTION IS A THROUGH-BOLT, AND THAT IS NOT A PREFERENCE. Every other hub
in the arm is trapped by a flange too big to pass its bore. That works
because the flange sits in a counterbore on the OUTER face, which stops the
hub moving INBOARD - and the socket floor stops the rest. Here both stops
are inboard: the hex bottoms in the socket, and the gear disc lands on the
plate's outer face. Nothing at all stops the gear sliding OUT and pulling
its 3.8 hex clear of a 3.4 socket. So an M3 runs down the elbow axis from
this gear, through the upper arm's duct, into j3_axle on the far side, and
clamps the whole rotating group into one piece. It carries no load - the
hex takes the torque and the journal takes the radial - it only stops the
group walking apart.

Print orientation: GEAR FACE ON THE BED, built -Z, so the teeth print flat
against the glass and every step above them is smaller than the one below.
No overhang anywhere, and the tooth flanks - the only surfaces here that
have to be right - get the best finish the machine has.
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

from lib.gears import J3_PAIR  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_j3_gear'
BODY_NAME = 'j3_gear'
PREFIX = 'jg_'
WRIST = 'wr_'
STYLE = 'sty_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('j3_gear')
PH_TEETH = 'gear teeth'
PH_STEM = 'journal + hex'
PH_FINISH = 'finish'
PHASES = [PH_TEETH, PH_STEM, PH_FINISH]


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

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    # --- shared J4/J3 clevis contract, defined identically elsewhere -------
    wrist('pivot_af', '16.0 mm', 'hex socket across flats - SHARED')
    wrist('hub_d', '20.0 mm', 'journal collar diameter - SHARED')
    wrist('reach', '3.8 mm', 'hex boss length = 0.4 running gap + 3.4 socket - SHARED')
    _set(STYLE + 'ef', '0.4 mm', 'elephant-foot chamfer, functional faces', 'mm')

    # --- the pair, from lib/gears.py. WRITTEN, NOT CHOSEN. -----------------
    P = J3_PAIR
    param('module', '%.4f mm' % P.module, 'lib/gears.py J3_PAIR - do not edit here')
    param('teeth', '%d' % P.z_gear, 'lib/gears.py J3_PAIR', '')
    param('face', '%.4f mm' % P.face, 'lib/gears.py J3_PAIR')
    param('r_tip', '%.5f mm' % P.r_tip(P.z_gear), 'derived in lib/gears.py')
    param('r_root', '%.5f mm' % P.r_root(P.z_gear), 'derived in lib/gears.py')
    param('centre', '%.5f mm' % P.centre_distance,
          'centre distance to the J3 servo shaft - forearm.py reads the SAME\n'
          '           number out of lib/gears.py to place the lobe')

    # --- stem -------------------------------------------------------------
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('hex_af', WRIST + 'pivot_af - ' + PREFIX + 'loc',
          'derived: grow the hole, shrink the hex, socket stays nominal')
    param('free', '0.4 mm', 'free fit - design_rules')
    param('plate_t', '7.5 mm',
          'forearm drive-plate thickness. ASSERTED equal to fa_plate_t when\n'
          '           that parameter exists in the document.')
    param('collar_l', PREFIX + 'plate_t + ' + PREFIX + 'free',
          'derived: the journal spans the plate, plus the running gap that\n'
          '           keeps the gear disc off the plate face')
    param('bolt_clear', '3.4 mm', 'M3 clearance - the retention bolt down the elbow axis')
    param('bolt_head', '6.0 mm', 'M3 socket head - design_rules')
    param('bolt_head_d', '3.2 mm', 'head counterbore depth, head sunk below the tooth face')
    param('lead_in', '0.6 mm', 'chamfer on the hex nose')
    param('tooth_sink', '0.5 mm', 'how far a tooth profile reaches inside the root circle')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE -------------------
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
    assert comp.name == COMPONENT, 'a stale component still holds the name'
    ext = comp.features.extrudeFeatures
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
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm, z_cm=0.0):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def polar(sk, r_cm, ang):
        return mpt(sk, r_cm * math.cos(ang), r_cm * math.sin(ang))

    def disc(name, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    # ---- phase 1: blank + one involute tooth + circular pattern ----------
    t0 = design.timeline.count
    disc('blank', val('r_root') * 2, '0.0 mm', PREFIX + 'face', NEW)

    T = P.tooth_polar(P.z_gear, n=14, sink=val('tooth_sink') * 10)
    sk_t = sketch(comp.xYConstructionPlane, 'sk_tooth_profile')
    lines = sk_t.sketchCurves.sketchLines
    r_sink = T['r_sink'] / 10.0
    for key, sign in (('flank_pos', +1), ('flank_neg', -1)):
        pts = adsk.core.ObjectCollection.create()
        for (r_mm, a) in T[key]:
            pts.add(polar(sk_t, r_mm / 10.0, a))
        sk_t.sketchCurves.sketchFittedSplines.add(pts)
        lines.addByTwoPoints(polar(sk_t, r_sink, sign * T['ang_base']),
                             polar(sk_t, T['r_base'] / 10.0, sign * T['ang_base']))
    lines.addByTwoPoints(polar(sk_t, r_sink, T['ang_base']),
                         polar(sk_t, r_sink, -T['ang_base']))
    sk_t.sketchCurves.sketchArcs.addByCenterStartSweep(
        mpt(sk_t, 0, 0), polar(sk_t, T['r_tip'] / 10.0, T['ang_tip']),
        -2 * T['ang_tip'])
    tooth = extrude(profiles(sk_t, expected=1), JOIN, '0.0 mm', PREFIX + 'face', 'tooth')

    pat_in = adsk.core.ObjectCollection.create()
    pat_in.add(tooth)
    cp = comp.features.circularPatternFeatures.createInput(
        pat_in, comp.zConstructionAxis)
    cp.quantity = adsk.core.ValueInput.createByReal(P.z_gear)
    cp.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    cp.isSymmetric = False
    comp.features.circularPatternFeatures.add(cp).name = 'tooth_ring'
    group(t0, PH_TEETH)

    # ---- phase 2: journal collar, hex, bolt bore -------------------------
    t1 = design.timeline.count
    disc('journal_collar', wval('hub_d'), '-' + PREFIX + 'collar_l',
         PREFIX + 'collar_l', JOIN)

    hex_af = val('hex_af')
    sk_h = sketch(comp.xYConstructionPlane, 'sk_hex_boss')
    r_c = hex_af / 2 / math.cos(math.pi / 6)
    pts = [(r_c * math.cos(2 * math.pi * i / 6), r_c * math.sin(2 * math.pi * i / 6))
           for i in range(6)]
    for i in range(6):
        u, w = pts[i], pts[(i + 1) % 6]
        sk_h.sketchCurves.sketchLines.addByTwoPoints(
            mpt(sk_h, u[0], u[1]), mpt(sk_h, w[0], w[1]))
    extrude(profiles(sk_h, expected=1), JOIN,
            '-(' + PREFIX + 'collar_l + ' + WRIST + 'reach)', WRIST + 'reach',
            'hex_boss')

    disc('bolt_bore', val('bolt_clear'),
         '-(' + PREFIX + 'collar_l + ' + WRIST + 'reach)',
         PREFIX + 'collar_l + ' + WRIST + 'reach + ' + PREFIX + 'face', CUT)
    disc('bolt_head_cbore', val('bolt_head'),
         PREFIX + 'face - ' + PREFIX + 'bolt_head_d', PREFIX + 'bolt_head_d', CUT)
    group(t1, PH_STEM)

    # ---- phase 3: finish --------------------------------------------------
    t2 = design.timeline.count

    def edges_in_plane_z(z_pick):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.z - z_pick) < val('tol')
                    and abs(eb.maxPoint.z - z_pick) < val('tol')):
                col.add(e)
        return col

    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_z(-(val('collar_l') + wval('reach'))),
        V(PREFIX + 'lead_in'), False)
    chf.add(c_inp).name = 'hex_nose_lead_in'
    group(t2, PH_FINISH)

    # ---- identity + diagnostics ------------------------------------------
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
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used = a.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    # ---- the checks -------------------------------------------------------
    bb = body.boundingBox
    r_out = max(abs(bb.minPoint.x), abs(bb.maxPoint.x),
                abs(bb.minPoint.y), abs(bb.maxPoint.y)) * 10
    assert abs(r_out - P.r_tip(P.z_gear)) < 0.05, (
        'the blank came out %.3f across and the tip circle is %.3f - the '
        'tooth pattern did not close' % (r_out * 2, P.r_tip(P.z_gear) * 2))

    # The gear disc IS the flange: it must not pass the plate bore, or the
    # journal is doing nothing and the part would fall through.
    fa_bore = ups.itemByName('fa_bore_d')
    if fa_bore is not None:
        assert P.r_tip(P.z_gear) * 2 > fa_bore.value * 10, (
            'the gear is smaller than the plate bore')
        assert wval('hub_d') * 10 < fa_bore.value * 10, (
            'the journal %.2f does not fit the plate bore %.2f'
            % (wval('hub_d') * 10, fa_bore.value * 10))
    fa_plate = ups.itemByName('fa_plate_t')
    if fa_plate is not None:
        assert abs(fa_plate.value - val('plate_t')) < 1e-9, (
            'jg_plate_t %.2f disagrees with fa_plate_t %.2f - the gear would '
            'either bind on the plate or float' % (val('plate_t') * 10,
                                                   fa_plate.value * 10))

    wall = (wval('hub_d') / 2 - val('bolt_clear') / 2) * 10
    assert wall >= 1.6, 'only %.2f mm of journal wall around the bolt bore' % wall
    root_wall = (P.r_root(P.z_gear) - wval('hub_d') * 10 / 2)
    assert root_wall >= 1.6, (
        'only %.2f mm between the tooth roots and the journal' % root_wall)

    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used))
    print('%dT module %.2f face %.2f - lib/gears.py J3_PAIR, ratio %.4f'
          % (P.z_gear, P.module, P.face, P.ratio))
    print('r base/pitch/tip/root mm: %.3f %.3f %.3f %.3f'
          % (P.r_base(P.z_gear), P.r_pitch(P.z_gear),
             P.r_tip(P.z_gear), P.r_root(P.z_gear)))
    print('tooth thickness at pitch %.3f mm (target %.3f incl. backlash)'
          % (T['thk_pitch'], math.pi * P.module / 2 - P.backlash / 2))
    print('tip land %.3f mm - a pointed tooth would read 0' % (2 * T['ang_tip'] * T['r_tip']))
    print('stem: hex %.2f af reaching %.1f | journal %.1f x %.2f | M3 bore %.1f'
          % (hex_af * 10, wval('reach') * 10, wval('hub_d') * 10,
             val('collar_l') * 10, val('bolt_clear') * 10))
    print('centre distance to the J3 servo shaft %.3f mm' % P.centre_distance)
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s'
          % (body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d'
          % (comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
