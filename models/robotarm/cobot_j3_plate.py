"""robotarm/cobot_j3_plate - Fusion MCP generating script.

Rebuilds `robotarm_cobot_j3_plate` (idempotent). Spec: specs/robotarm/cobot.md;
every number from lib/cobot.py.

THE J3 SERVO PLATE - a BENCH UNIT. On the bench:
  1. the SG90 360 with its pinion already broached on and screwed, down
     through the plate's case window (a LOC fit - it locates the servo)
  2. its tabs screwed to the plate: 2 x M2 x 6 (not the ~8 mm bag screws)
  3. the AS5600 board into the pocket on the top face, CHIP DOWN over the
     stalk hole, wires soldered to its pads; 2 x M2 x 5 with washers clamp
     its edges (the pocket is 23.4 - CALIPER the board first)
Then the whole unit drops into the upper arm along -x: the pinion meshes AXIALLY
(lead-ins on both gears), the output gear's stalk enters the O12 hole
and puts its magnet under the chip. The idler pin, already standing in the upper arm with the idler on it, passes through the plate's LOC hole and LOCATES it, so both J3 meshes are set by the parts (their tolerance stacks are built into their centre distances - lib/cobot FITS); 3 x M3 x 10 to the posts through round clearance holes.

Print: FLAT, bottom face down, no support; the board pocket opens upward.
Frame: arm x; y = u along the upper arm; z = v across it.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

import lib.cobot as C  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_cobot_j3_plate'
BODY_NAME = 'cobot_j3_plate'
PREFIX = 'cp3p_'
OUTLINE = C.J3_PLATE
CASE = C.J3_CASE
TAB_HOLES = C.J3_HOLES
TAB_PILOT = C.M2['pilot']
POSTS = C.J3_POSTS
BOARD_AT = (C.L1, 0.0)
CLAMPS = C.J3_CLAMPS
PIN_AT = C.J3_IDLER                    # the idler pin's hole, or None
SLOT_DIR = None                # unit (du, dv) along the mesh line, or None: the posts' slots run along it
PLATE_TOP = C.UA_J3_TAB_TOP
PLATE_T = C.PLATE_T
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('cobot_j3_plate')
PH_PLATE = 'plate + window'
PH_HOLES = 'servo + posts'
PH_BOARD = 'encoder'
PHASES = [PH_PLATE, PH_HOLES, PH_BOARD]
PETG_G_PER_MM3 = 1.27 * 0.65 / 1000.0
EPS_MM = 1e-6


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    C.check()

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value      # cm

    def mm(v_cm):
        return '%.5f mm' % (v_cm * 10)

    param('x0', '%.4f mm' % (PLATE_TOP - PLATE_T), 'lib/cobot - the plate\'s bottom face')
    param('t', '%.4f mm' % PLATE_T, 'lib/cobot')
    param('loc', '%.4f mm' % C.LOC, 'the case window, locational')
    param('tab_pilot', '%.4f mm' % TAB_PILOT, 'the servo\'s tab screws')
    param('post_clear', '%.4f mm' % C.M3['clearance'], 'M3 x 10 to the posts')
    param('slot', '%.4f mm' % (C.PLATE_SLOT if SLOT_DIR else 0.0), 'lib/cobot PLATE_SLOT - the mesh is SET on assembly')
    param('pin_hole', '%.4f mm' % (C.IDLER_PIN_D + C.LOC), 'the idler pin, locational - it LOCATES this plate')
    param('pocket', '%.4f mm' % C.BOARD_POCKET, 'lib/cobot BOARD_POCKET - the 23 x 23 AS5600 + LOC')
    param('pocket_h', '%.4f mm' % C.BOARD_POCKET_H, 'the board stands proud of it for the clamps')
    param('stalk_hole', '%.4f mm' % C.STALK_HOLE_D, 'the stalk + slot travel + FREE')
    param('clamp_pilot', '%.4f mm' % C.M2['pilot'], 'M2 x 5 + washer clamps the board edge')

    assert abs(val('x0') * 10 + PLATE_T - PLATE_TOP) < EPS_MM

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
    assert comp.name == COMPONENT, 'a stale component still holds the name'
    ext = comp.features.extrudeFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.yZConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def pt(sk, u, v):
        return sk.modelToSketchSpace(P3(0, u / 10, v / 10))

    def extrude_all(sk, op, x0, dx, name):
        col = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            col.add(sk.profiles.item(i))
        inp = ext.createInput(col, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(x0)))
        inp.setDistanceExtent(False, V(mm(dx)))
        if op != NEW:
            inp.participantBodies = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
        ext.add(inp).name = name

    def poly(name, pts, op, x0, dx):
        sk = sketch(name)
        sp = [pt(sk, u, v) for u, v in pts]
        for k in range(len(sp)):
            sk.sketchCurves.sketchLines.addByTwoPoints(sp[k], sp[(k + 1) % len(sp)])
        extrude_all(sk, op, x0, dx, name)

    def hole(name, u, v, d_cm, x0, dx, slot_cm=0.0, along=None):
        sk = sketch(name)
        c = pt(sk, u, v)
        if slot_cm and along:
            n = math.hypot(along[0], along[1])
            du, dv = along[0] / n * slot_cm * 10, along[1] / n * slot_cm * 10
            a_, b_ = pt(sk, u - du, v - dv), pt(sk, u + du, v + dv)
            sk.sketchCurves.sketchCircles.addByCenterRadius(a_, d_cm / 2)
            sk.sketchCurves.sketchCircles.addByCenterRadius(b_, d_cm / 2)
            w = d_cm / 2 * 10
            nu, nv = -dv / (slot_cm * 10) * w, du / (slot_cm * 10) * w
            q = [pt(sk, u - du + nu, v - dv + nv), pt(sk, u + du + nu, v + dv + nv),
                 pt(sk, u + du - nu, v + dv - nv), pt(sk, u - du - nu, v - dv - nv)]
            for k in range(len(q)):
                sk.sketchCurves.sketchLines.addByTwoPoints(q[k], q[(k + 1) % len(q)])
        else:
            sk.sketchCurves.sketchCircles.addByCenterRadius(c, d_cm / 2)
        extrude_all(sk, CUT, x0, dx, name)

    def group(start, name):
        if design.timeline.count - start > 1:
            design.timeline.timelineGroups.add(start, design.timeline.count - 1).name = name

    x0, t = val('x0'), val('t')
    lc = val('loc') * 10
    t0 = design.timeline.count
    poly('plate', OUTLINE, NEW, x0, t)
    poly('case_window', [(CASE[0] - lc, CASE[2] - lc), (CASE[1] + lc, CASE[2] - lc),
                         (CASE[1] + lc, CASE[3] + lc), (CASE[0] - lc, CASE[3] + lc)], CUT, x0, t)
    group(t0, PH_PLATE)

    t1 = design.timeline.count
    for k, (u, v) in enumerate(TAB_HOLES):
        hole('tab_pilot_%d' % k, u, v, val('tab_pilot'), x0, t)
    # the mesh line: slots run along the line from the output gear's axis to the pinion
    for k, (u, v) in enumerate(POSTS):
        hole('post_%d' % k, u, v, val('post_clear'), x0, t, val('slot'), SLOT_DIR)
    if PIN_AT is not None:
        hole('idler_pin', PIN_AT[0], PIN_AT[1], val('pin_hole'), x0, t)
    group(t1, PH_HOLES)

    t2 = design.timeline.count
    bu, bv = BOARD_AT
    hp = val('pocket') * 10 / 2
    poly('board_pocket', [(bu - hp, bv - hp), (bu + hp, bv - hp), (bu + hp, bv + hp), (bu - hp, bv + hp)], CUT,
         x0 + t - val('pocket_h'), val('pocket_h'))
    hole('stalk_hole', bu, bv, val('stalk_hole'), x0, t)
    for k, (u, v) in enumerate(CLAMPS):
        hole('clamp_%d' % k, u, v, val('clamp_pilot'), x0, t)
    group(t2, PH_BOARD)

    assert comp.bRepBodies.count == 1, 'the plate came out in %d pieces' % comp.bRepBodies.count
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
    v_ = body.volume * 1000
    print("body: '%s' | appearance: %s | PRINT 1, flat" % (body.name, used))
    print('plate x %.2f..%.2f; window %.1f x %.1f (LOC); %d tab pilots O%.1f; %d posts %s; board pocket %.1f sq at %r%s'
          % (x0 * 10, (x0 + t) * 10, CASE[1] - CASE[0] + 2 * lc, CASE[3] - CASE[2] + 2 * lc, len(TAB_HOLES),
             TAB_PILOT, len(POSTS), 'slotted +-%.1f along the mesh' % (val('slot') * 10) if SLOT_DIR else 'round',
             val('pocket') * 10, BOARD_AT, '; idler pin hole O%.1f' % (val('pin_hole') * 10) if PIN_AT else ''))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g | valid: %s' % (v_, v_ * PETG_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
