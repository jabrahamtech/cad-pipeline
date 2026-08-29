"""robotarm/gripcut_finger - Fusion MCP generating script.

Rebuilds `robotarm_gripcut_finger` (idempotent). Spec:
specs/robotarm/gripcut_finger.md; sizing authority lib/gripcut_finger.py;
packaging analysis specs/robotarm/gripcut.md.

ONE design, TWO copies, the second FLIPPED - the same trick as the blade
carriers, and the reason this is a separate part at all: an integrated finger
lands on opposite sides of the cutting plane on the two carriers, and a
severed piece touched by one finger pressing against nothing falls.

Local frame: THE BLADE CARRIER'S, mounted, undeflected. Origin on the pivot,
+Y toward the nose, +X into the body away from the edge, carrier z 0.05..3.55.
The finger rests on the carrier's OUTER face (z 3.55), stacks on the existing
pivot M3, and keys against rotation with one boss into a pocket cut in the
carrier - the 'one extra feature per carrier' the gripcut spec budgeted.

THE GRIP IS A COUPLE ON ONE CARRIER, AND THE FACE SITS ENTIRELY ABOVE THE
BLADE STACK (z 3.65..9.55). Three designs died before this one, each killed
by its gate:

  1. A straddling face (z +-3) - the only band the turn-over maps to itself -
     collides with the OTHER carrier's Ø12 hub disc, and its below-plane half
     fights the blade bodies, which sweep the +-3.55 band during closure.
     Nothing can grip there; the space is spoken for.
  2. Fixing the hub clip left the deflection fault: the stem pushes the
     finger back toward its OWN blade, and the tip had 0.1 mm of room against
     4.5 mm of travel. A below-plane tip cannot back away from its own nose.
  3. So the face lives above the stack, where deflection sweeps over the
     nose tops through open air.

WHAT HOLDS THE CUTTING, THEN: the finger presses the piece sideways from
above the stack, and the piece's lower end leans against the carrier's own
NOSE EDGE FACE below - two opposed contacts, offset in z, both riding the
same blade. A one-sided hold-down against the blade's own flat is exactly
how real cut-and-hold secateurs work. The flipped copy grips the stump side
the same way, harmlessly; opening the head releases both.

On empty close the two fingers BYPASS - no z overlap, like the blades. Only
a stem loads the leaf.

Print orientation: TOP FACE DOWN (z +9.55 on the bed). Ring, leaf, face
column and bridge all start at the bed - no cantilever, no support. Layers
then lie ALONG the leaf, so bending stress is in-plane - the flexure's one
hard rule (knowledge/materials.md; a cross-layer flexure is a fatigue crack
waiting).
"""

import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]
from lib.pruner_linkage import CHOSEN  # noqa: E402

COMPONENT = 'robotarm_gripcut_finger'
BODY_NAME = 'gripcut_finger'
PREFIX = 'gf_'
PH_ANCHOR = 'ring and key'
PH_LEAF = 'leaf'
PH_TIP = 'tip'
PHASES = [PH_ANCHOR, PH_LEAF, PH_TIP]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: a moving part in the head - dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('gripcut_finger')


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

    # ---- the numbers, every one from the solver or a design rule ------------
    param('lead', '2.0 mm', 'how far the finger leads the blade - lib/gripcut_finger CHOSEN')
    param('af', '%.3f mm' % (CHOSEN.edge_offset - 2.0),
          'derived: edge_offset - lead. The grip face lies on the plane x = af,\n'
          '           the blade equation with a smaller number - gripcut.md')
    param('t', '1.2 mm',
          'leaf thickness. BELOW MIN_WALL 1.6 DELIBERATELY - that rule is\n'
          '           structure, this is a flexure; three full extrusions at 0.4.\n'
          '           Recorded as a departure in gripcut.md.')
    param('leaf_w', '6.0 mm', 'leaf width = grip band height - the solver\'s w')
    param('mount_z', '3.55 mm', 'the carrier\'s outer face - pb thk 3.5 + gap 0.05')

    param('bore_d', '3.2 mm', 'M3 clearance - rides the existing pivot screw')
    param('ring_od', '12.0 mm', 'anchor ring - matches the carrier hub Ø12')
    param('key_w', '4.0 mm', 'anti-rotation boss, tangential')
    param('key_l', '3.0 mm', 'boss, radial')
    param('key_h', '1.4 mm', 'boss depth into the carrier pocket - leaves 2.1 of\n'
                             '           carrier under a 3.5 wall')
    param('key_y', '-7.9 mm', 'boss centre, on the tail where the carrier is solid')
    param('out_x', '4.5 mm', 'leaf out-run inner face - 1.0 clear of the edge plane\n'
                             '           at 3.5, and the leaf bows AWAY from it under load')
    param('fold_y', '18.0 mm', 'fold centre - reach 20.7 stays inside the 22 nose')
    param('fold_ir', '1.5 mm', 'fold inner radius')
    param('tip_y0', '6.3 mm',
          'grip face span, near end - also where the leaf return run lands.\n'
          '           The value predates the above-stack move: in the dead designs it\n'
          '           cleared the other carrier hub (5.5 put the corner at r 5.70,\n'
          '           inside Ø12 - _check_gripcut found it). No hub shares z now,\n'
          '           but 6.3 keeps the flag off the ring and it stays.')
    param('tab_top', '-5.5 mm',
          'key tab upper end - reaches the ring and STOPS. The first build ran\n'
          '           it to +3.0, roofing the pivot bore shut at leaf height: the M3\n'
          '           could never have passed. _check would not see that; reading the\n'
          '           sketch did.')
    param('tip_y1', '8.2 mm',
          'grip face span, far end. sqrt(af^2 + tip_y1^2) = 8.34 must stay\n'
          '           INSIDE the throat crossing radius 8.5 - asserted')
    param('bridge_z', '3.65 mm', 'bridge underside - 0.1 air over the carrier top')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('margin', '0.1 mm', 'assertion margin')
    param('edge_clear', '1.0 mm', 'leaf out-run clearance off the edge plane')
    param('nose_over', '2.0 mm', 'the carrier nose runs this far past tip_r -\n'
          '           pb_nose_len does the same; the fold may use it minus margin')
    param('tol', '0.001 mm', 'edge-selection tolerance, not a dimension')

    # ---- sanity, in MILLIMETRES, before any geometry ------------------------
    af_mm = val('af') * 10
    tip_r_mm = math.hypot(af_mm, val('tip_y1') * 10)
    assert tip_r_mm < CHOSEN.throat_r - val('margin') * 10, (
        'the grip face corner reaches r %.2f, outside the throat crossing '
        'radius %.2f - the couple only works over the throat, where the '
        'carrier\'s own nose edge below can take the counter-contact'
        % (tip_r_mm, CHOSEN.throat_r))
    pb_edge = ups.itemByName('pb_edge_off')
    if pb_edge is not None:
        assert abs((pb_edge.value * 10 - val('lead') * 10) - af_mm) < val('tol') * 10, (
            'gf_af %.3f is not pb_edge_off - gf_lead: the finger no longer '
            'leads the blade it rides' % af_mm)
    assert val('out_x') * 10 >= CHOSEN.edge_offset + val('edge_clear') * 10 - val('margin') * 10, (
        'the leaf out-run at x %.1f is within a wall of the edge plane %.1f'
        % (val('out_x') * 10, CHOSEN.edge_offset))
    fold_reach_mm = val('fold_y') * 10 + (val('fold_ir') + val('t')) * 10
    assert fold_reach_mm < CHOSEN.tip_r + val('nose_over') * 10 - val('margin') * 10, (
        'the fold reaches y %.1f, past the blade nose' % fold_reach_mm)
    # NOTHING BELOW THE BRIDGE PLANE. The tip's whole structure sits above
    # z = bridge_z, over the blade stack, so deflection sweeps through open
    # air. This assert is the law that killed designs 1 and 2.
    assert val('bridge_z') * 10 > val('mount_z') * 10 + val('tol') * 10, (
        'the tip dips to z %.2f, into the blade band - the deflection has '
        'nowhere to go there' % (val('bridge_z') * 10))

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

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mm(cm):
        return '%.4f mm' % (cm * 10.0)

    def pt(sk, x_cm, y_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, 0))

    def one(sk):
        assert sk.profiles.count == 1, (
            sk.name + ': %d profiles' % sk.profiles.count)
        col = adsk.core.ObjectCollection.create()
        col.add(sk.profiles.item(0))
        return col

    def extrude(profs, op, z0_cm, dz_cm, name):
        inp = comp.features.extrudeFeatures.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0_cm)))
        inp.setDistanceExtent(False, V(mm(dz_cm)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = comp.features.extrudeFeatures.add(inp)
        f.name = name
        return f

    mount = val('mount_z')
    top = mount + val('leaf_w')

    # ---- phase 1: ring, key tab, key boss -----------------------------------
    t0 = design.timeline.count
    sk = sketch('ring')
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, 0, 0), val('ring_od') / 2)
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, 0, 0), val('bore_d') / 2)
    assert sk.profiles.count == 2, 'ring: expected annulus + core'
    want = math.pi * ((val('ring_od') / 2) ** 2 - (val('bore_d') / 2) ** 2)
    col = adsk.core.ObjectCollection.create()
    for i in range(2):
        p = sk.profiles.item(i)
        if abs(p.areaProperties().area - want) < want / 1000:
            col.add(p)
    assert col.count == 1, 'ring: no profile matched the annulus'
    extrude(col, NEW, mount, val('leaf_w'), 'ring')
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME

    ky = val('key_y')
    sk = sketch('key_tab')
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        pt(sk, -val('key_w') / 2, ky - val('key_l') / 2),
        pt(sk, val('key_w') / 2, val('tab_top')))
    extrude(one(sk), JOIN, mount, val('leaf_w'), 'key_tab')
    sk = sketch('key_boss')
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        pt(sk, -val('key_w') / 2, ky - val('key_l') / 2),
        pt(sk, val('key_w') / 2, ky + val('key_l') / 2))
    extrude(one(sk), JOIN, mount - val('key_h'), val('key_h'), 'key_boss')
    design.timeline.timelineGroups.add(t0, design.timeline.count - 1).name = PH_ANCHOR

    # ---- phase 2: the leaf, one hairpin profile -----------------------------
    t1 = design.timeline.count
    ox0, t_l = val('out_x'), val('t')
    ox1 = ox0 + t_l
    fy, fir = val('fold_y'), val('fold_ir')
    fc_x = ox1 + fir                    # fold centre x
    rx0, rx1 = fc_x + fir, fc_x + fir + t_l
    ret_y = val('tip_y0')               # return run ends at the riser
    anchor_y = val('bore_d')            # buried in the ring by construction
    sk = sketch('leaf')
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    lines.addByTwoPoints(pt(sk, ox0, anchor_y), pt(sk, ox0, fy))
    arcs.addByThreePoints(pt(sk, ox0, fy), pt(sk, fc_x, fy + fir + t_l),
                          pt(sk, rx1, fy))
    lines.addByTwoPoints(pt(sk, rx1, fy), pt(sk, rx1, ret_y))
    lines.addByTwoPoints(pt(sk, rx1, ret_y), pt(sk, rx0, ret_y))
    lines.addByTwoPoints(pt(sk, rx0, ret_y), pt(sk, rx0, fy))
    arcs.addByThreePoints(pt(sk, rx0, fy), pt(sk, fc_x, fy + fir), pt(sk, ox1, fy))
    lines.addByTwoPoints(pt(sk, ox1, fy), pt(sk, ox1, anchor_y))
    lines.addByTwoPoints(pt(sk, ox1, anchor_y), pt(sk, ox0, anchor_y))
    extrude(one(sk), JOIN, mount, val('leaf_w'), 'leaf')
    design.timeline.timelineGroups.add(t1, design.timeline.count - 1).name = PH_LEAF

    # ---- phase 3: the grip flag -------------------------------------------
    # One block from the leaf's return run forward to the face plane, all of
    # it above the blade stack with 0.1 of air, so the sweep gate sees any
    # contact with a nose top and the deflection path is open sky.
    t2 = design.timeline.count
    y0, y1 = val('tip_y0'), val('tip_y1')
    sk = sketch('grip_flag')
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        pt(sk, val('af'), y0), pt(sk, rx1, y1))
    extrude(one(sk), JOIN, val('bridge_z'), top - val('bridge_z'), 'grip_flag')
    design.timeline.timelineGroups.add(t2, design.timeline.count - 1).name = PH_TIP

    # ---- material, diagnostics ---------------------------------------------
    lib_mat = None
    for li in range(app.materialLibraries.count):
        mats = app.materialLibraries.item(li).materials
        m = mats.itemByName(MATERIAL_NAME)
        if m is not None:
            lib_mat = m
    if lib_mat is not None:
        body.material = lib_mat
    for hints in APPEARANCE_HINTS:
        done = False
        for li in range(app.materialLibraries.count):
            aps = app.materialLibraries.item(li).appearances
            for ai in range(aps.count):
                ap = aps.item(ai)
                nm = ap.name.lower()
                if all(h in nm for h in hints):
                    body.appearance = ap
                    done = True
                    break
            if done:
                break
        if done:
            break

    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a feature is not touching the rest'
        % comp.bRepBodies.count)
    assert body.isValid, 'body invalid'
    bb = body.boundingBox
    vol = body.volume * 1000
    leaf_len_mm = ((fy - anchor_y) + (fy - ret_y)) * 10 + math.pi * (fc_x * 0) \
        + math.pi * (fir + t_l / 2) * 10
    print('body: %r | material: %s' % (BODY_NAME, MATERIAL_NAME))
    print('ONE design, TWO copies, the second FLIPPED - like the carriers.')
    print('grip face: plane x %.2f (edge_off - lead %.1f), y %.1f..%.1f, '
          'z %.2f..%.2f - ABOVE the blade stack'
          % (af_mm, val('lead') * 10, y0 * 10, y1 * 10,
             val('bridge_z') * 10, top * 10))
    print('  the grip is a COUPLE: finger presses from above, the piece leans')
    print('  on the carrier\'s own nose edge below. Empty close: fingers')
    print('  BYPASS, no z overlap - only a stem loads the leaf.')
    print('leaf: t %.1f x w %.1f, hairpin out to y %.1f and back - effective '
          'length ~%.0f mm (solver sized 29.1 straight; coupon calibrates)'
          % (val('t') * 10, val('leaf_w') * 10, fold_reach_mm, leaf_len_mm))
    print('anchor: ring Ø%.1f on the pivot M3, key boss %.1f x %.1f x %.1f at '
          'y %.1f into the carrier pocket'
          % (val('ring_od') * 10, val('key_w') * 10, val('key_l') * 10,
             val('key_h') * 10, ky * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f (pair %.2f) | valid: %s' % (
        vol, body.physicalProperties.mass * 1000,
        2 * body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %s' % ([g.name for g in design.timeline.timelineGroups],))
