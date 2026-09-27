"""robotarm/grip_finger - Fusion MCP generating script.

Rebuilds `robotarm_grip_finger` (idempotent). PRINT TWO, in TPU 95A. The
second is the same part turned over (rotated 180 deg about Y).

Spec: specs/robotarm/grip.md - all numbers from lib/grip.py.

A FIN RAY FINGER. Two beams - the straight GRIP face and a slanted BACK -
meet at the tip and are tied by cross ribs. Press an object into the grip
face and the ribs shear, and the geometry turns that into the tip curling
TOWARD the object: the finger wraps a stem, a pot rim or a pen instead of
touching it at two points. That is the whole reason a parallel gripper
with one SG90 can hold irregular things without shaped jaws. (Festo's fin
ray effect; the printed-TPU version is the standard hobby form of it.)

It is also the SG90's force limiter. Closed on an object, the finger
deflects; the servo reaches its commanded position instead of stalling
against a rigid jaw and cooking.

WHY TPU AND NOT PETG. A PETG fin ray has to be so thin to bend that its
ribs are under MIN_FEATURE_MM and crack at the rib roots within days. TPU
95A at these sections bends a few millimetres for about a newton.

Grip face: GROOVES across it for bite on a smooth stem. It stands
FINGER_LEAD (1.0) proud of the jaw face, so the fingers touch at s = 1.0
while the jaws are still 2.0 apart - closing to s = 0 squeezes 1 mm each.

Mounting: 2 x M3 x 16 from the back of the jaw arm into two M3 nuts that
press into hex pockets opening into the first cell. Push the nuts in with
the screw before the jaw goes into the shell.

Frame: finger-local. x = 0 on the grip face, +x away from the object;
y = 0 on the base (the jaw arm's front face), +y toward the tip; z centred.

Print orientation: FLAT, z = -FINGER_H/2 on the bed. Every feature is a
prism up z except the two nut pockets and screw holes, which run along y
(small horizontal holes - fine in TPU). 20-25 mm/s, no retraction tricks.
"""

import math
import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

import lib.grip as G  # noqa: E402

MATERIAL_NAME = 'Rubber'          # nearest stock material; mass is computed from TPU
COMPONENT = 'robotarm_grip_finger'
BODY_NAME = 'grip_finger'
PREFIX = 'gf_'
APPEARANCE_HINTS = [('rubber', 'black'), ('plastic', 'black'), ('black',)]
PH_FORM = 'outline'
PH_CELLS = 'fin ray cells'
PH_MOUNT = 'mount'
PH_GRIP = 'grip texture'
PHASES = [PH_FORM, PH_CELLS, PH_MOUNT, PH_GRIP]
HEX_SIDES = 6
QTY = 2


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create
    G.check()

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value

    param('h', '%.4f mm' % G.FINGER_H, 'lib/grip - finger height, centred on z = 0')
    param('l', '%.4f mm' % G.FINGER_L, 'lib/grip - base to tip')
    param('b', '%.4f mm' % G.FINGER_B, 'lib/grip - base width: jaw arm + the lead')
    param('base_d', '%.4f mm' % G.FINGER_BASE_D, 'lib/grip - solid base')
    param('grip_beam', '%.4f mm' % G.GRIP_BEAM, 'lib/grip - the grip face beam')
    param('back_beam', '%.4f mm' % G.BACK_BEAM, 'lib/grip - the slanted back beam')
    param('rib_t', '%.4f mm' % G.RIB_T, 'lib/grip - cross rib')
    param('tip_t', '%.4f mm' % G.TIP_T, 'lib/grip - tip width')
    param('tip_solid', '%.4f mm' % G.TIP_SOLID, 'lib/grip - solid tip length')
    param('groove_w', '%.4f mm' % G.GROOVE_W, 'lib/grip - grip texture')
    param('groove_d', '%.4f mm' % G.GROOVE_D, 'lib/grip - grip texture depth')
    param('groove_p', '%.4f mm' % G.GROOVE_PITCH, 'lib/grip - grip texture pitch')
    param('screw_x', '%.4f mm' % G.FINGER_SCREW_X, 'lib/grip - on the jaw arm centre')
    param('screw_z', '%.4f mm' % G.FINGER_SCREW_Z, 'lib/grip - at z +/- this')
    param('screw_d', '%.4f mm' % G.M3['clearance'], 'M3 clearance')
    param('hex_af', '%.4f mm' % G.HEX_AF, 'M3 nut 5.5 af + 0.2 - a press in TPU')
    param('nut_deep', '%.4f mm' % (G.NUT_T + G.LOC), 'M3 nut 2.4 + locational')

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------
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

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def one(sk):
        assert sk.profiles.count == 1, '%s made %d profiles' % (sk.name, sk.profiles.count)
        return sk.profiles.item(0)

    def extrude(prof, op, start_expr, dist_expr, name):
        inp = ext.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
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

    def poly_z(name, pts, op):
        """Closed XY polygon (cm) through the full finger height."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(P3(a[0], a[1], 0), P3(b[0], b[1], 0))
        return extrude(one(sk), op, '-' + PREFIX + 'h / 2 - 1 mm' if op == CUT
                       else '-' + PREFIX + 'h / 2',
                       PREFIX + 'h + 2 mm' if op == CUT else PREFIX + 'h', name)

    b, l, bd = val('b'), val('l'), val('base_d')
    tip_t = val('tip_t')
    slope = (tip_t - b) / (l - bd)                         # dx/dy of the back line
    back_in = val('back_beam') * math.sqrt(1 + slope ** 2)

    def x_back_in(y):
        return b + slope * (y - bd) - back_in

    # ---- phase 1: outline ----
    t0 = design.timeline.count
    poly_z('outline', [(0, 0), (b, 0), (b, bd), (tip_t, l), (0, l)], NEW)
    group(t0, PH_FORM)

    # ---- phase 2: the cells between the ribs ----
    t1 = design.timeline.count
    y0 = bd
    y1 = l - val('tip_solid')
    n_cells = G.RIBS + 1
    cell_h = ((y1 - y0) - G.RIBS * val('rib_t')) / n_cells
    assert cell_h > val('rib_t') * 2, 'the ribs leave no cells'
    gx = val('grip_beam')
    cells = []
    for k in range(n_cells):
        ya = y0 + k * (cell_h + val('rib_t'))
        yb = ya + cell_h
        assert x_back_in(yb) - gx > val('rib_t'), 'cell %d pinches shut at the tip' % k
        poly_z('cell_%d' % k, [(gx, ya), (x_back_in(ya), ya), (x_back_in(yb), yb), (gx, yb)], CUT)
        cells.append((ya, yb))
    group(t1, PH_CELLS)

    # ---- phase 3: screw holes through the base, nut hexes opening into cell 0 ----
    t2 = design.timeline.count
    r_hex = val('hex_af') / math.sqrt(3)
    for k, sz in enumerate((-1, 1)):
        z = sz * val('screw_z')
        sk = sketch(comp.xZConstructionPlane, 'sk_screw_%d' % k)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(val('screw_x'), 0, z)), val('screw_d') / 2)
        extrude(one(sk), CUT, '-1 mm', PREFIX + 'base_d + 2 mm', 'screw_%d' % k)
        sk = sketch(comp.xZConstructionPlane, 'sk_nut_%d' % k)
        pts = [sk.modelToSketchSpace(P3(val('screw_x') + r_hex * math.cos(math.pi / HEX_SIDES * (2 * i + 1)),
                                        0, z + r_hex * math.sin(math.pi / HEX_SIDES * (2 * i + 1))))
               for i in range(HEX_SIDES)]
        for i in range(HEX_SIDES):
            sk.sketchCurves.sketchLines.addByTwoPoints(pts[i], pts[(i + 1) % HEX_SIDES])
        extrude(one(sk), CUT, PREFIX + 'base_d - ' + PREFIX + 'nut_deep',
                PREFIX + 'nut_deep + 1 mm', 'nut_%d' % k)
    assert val('screw_x') + r_hex < b - G.WALL / 10 / 2, 'the nut breaks the back of the base'
    assert val('screw_x') - r_hex > 0, 'the nut breaks the grip face'
    group(t2, PH_MOUNT)

    # ---- phase 4: grooves across the grip face ----
    t3 = design.timeline.count
    y = bd + val('groove_p')
    n_g = 0
    while y + val('groove_w') < y1:
        poly_z('groove_%d' % n_g, [(-val('groove_d'), y), (val('groove_d'), y),
                                   (val('groove_d'), y + val('groove_w')),
                                   (-val('groove_d'), y + val('groove_w'))], CUT)
        y += val('groove_p')
        n_g += 1
    group(t3, PH_GRIP)

    assert comp.bRepBodies.count == 1, 'the finger came out in %d pieces' % comp.bRepBodies.count
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

    bb = body.boundingBox
    vol = body.physicalProperties.volume * 1000
    print("body: '%s' | appearance: %s | PRINT %d in TPU 95A, flat" % (body.name, used, QTY))
    print('fin ray: %.1f long, base %.1f, tip %.1f, %d ribs x %.1f, cells %.2f tall'
          % (l * 10, b * 10, tip_t * 10, G.RIBS, val('rib_t') * 10, cell_h * 10))
    print('grip face stands %.1f proud of the jaw; %d grooves %.1f x %.1f'
          % (G.FINGER_LEAD, n_g, val('groove_w') * 10, val('groove_d') * 10))
    print('mount: 2 x M3 nut pockets %.1f af x %.1f, opening into cell 0 (y %.1f..%.1f)'
          % (val('hex_af') * 10, val('nut_deep') * 10, cells[0][0] * 10, cells[0][1] * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | TPU ~%.1f g each | valid: %s'
          % (vol, vol * G.TPU_PRINTED_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
