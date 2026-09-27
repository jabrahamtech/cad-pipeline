"""robotarm/grip_shell - Fusion MCP generating script.

Rebuilds `robotarm_grip_shell` (idempotent). PRINT TWO - one design, the
second TURNED OVER (rotated 180 deg about Y). Together they are the hand.

Spec: specs/robotarm/grip.md - all numbers from lib/grip.py.

THE HAND. Half A is z >= 0; the split face z = 0 is the widest line of the
form and both halves bevel away from it (_style.md rule 4), so the pair
reads as one faceted volume with a crisp centre line. In it:

  rack channel   full width, open at BOTH sides: each jaw slides in from its
                 side after the hand is bolted on, and runs out past the
                 shell at full open. Roofed by the 2.4 top plate, walled
                 behind, and - new - LIPPED IN FRONT under the rack teeth.
  front slot     the jaw's tie passes the front wall above that lip, on this
                 half's +x side only (the other jaw's tie is in the other half)
  servo bay      the SG90 lies across the hand, shaft forward. The pocket is
                 symmetric (the case is not: 6.1 / 16.6 about the shaft) so
                 one design serves both halves and the servo goes in either
                 way round. The far tab is trapped in a slot; no servo screws.
  lead notch     at the side, both sides, level with where the lead leaves
                 the case end face (lib/servo lead datum)
  cavity         a closed lightening void over the servo - a 20 mm bridge
  back wall      6.8 thick. TWO of the four rotator M3s pass through it, heads
                 in counterbores, driven with a long 2.5 key down O6.2 access
                 bores from the front - open until the jaws go in. The rotator
                 face then clamps the two halves together at the back.
  clamp bolts    2 x M3 x 30 at the waist. Every bolt hole has the SAME 5.7 af
                 hex pocket in its top face: on one half it holds the head,
                 on the other (turned over) the nut.

Print orientation: SPLIT FACE (z = 0) ON THE BED, built +z. No support: the
channel roof bridges 8.25, the cavity roof ~22.
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
from lib.palette import hints_for  # noqa: E402

MATERIAL_NAME = 'PET Plastic'
COMPONENT = 'robotarm_grip_shell'
BODY_NAME = 'grip_shell'
PREFIX = 'gh_'
STYLE = 'sty_'
APPEARANCE_HINTS = hints_for('grip_shell')
PH_FORM = 'outer form'
PH_MECH = 'channel, lip and slot'
PH_SERVO = 'servo bay'
PH_FIX = 'fixings'
PHASES = [PH_FORM, PH_MECH, PH_SERVO, PH_FIX]
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

    def _set(full, expr, comment):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment=''):
        _set(PREFIX + name, expr, comment)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    # sty_radius is SHARED (_style.md) - define it with the value everyone uses
    _set(STYLE + 'radius', '6.0 mm', 'plan-view corner radius - _style.md rule 2. MUST exceed sty_facet')
    param('x_half', '%.4f mm' % G.X_HALF, 'lib/grip - half width at the hand')
    param('rear_x', '%.4f mm' % G.REAR_X, 'lib/grip - half width at the wrist, rule 3 taper')
    param('taper_y', '%.4f mm' % G.TAPER_Y, 'lib/grip - where the taper starts')
    param('front_y', '%.4f mm' % G.SHELL_FRONT_Y, 'lib/grip - channel + the front lip')
    param('back_y', '%.4f mm' % G.SHELL_BACK_Y, 'lib/grip - the rotator face')
    param('half_z', '%.4f mm' % G.HALF_Z, 'lib/grip - channel roof + 2.4 plate')
    param('facet', '%.4f mm' % G.FACET, 'lib/grip - rule 1, scaled to the 2.4 roof')
    param('chan_y', '%.4f mm' % G.CHAN_Y, 'lib/grip - channel half width, sliding fit')
    param('chan_z', '%.4f mm' % G.CHAN_Z, 'lib/grip - channel roof, sliding fit over the rack back')
    param('slot_z0', '%.4f mm' % G.TIE_SLOT_Z0, 'lib/grip - bottom of the tie slot = top of the lip')
    param('pin_r', '%.4f mm' % (G.R_TIP + G.FREE), 'pinion tip + free: face relief in the lip')
    param('pin_front', '%.4f mm' % (G.GR_FACE / 2 + G.FREE), 'pinion front face + free')
    param('access_r', '%.4f mm' % ((G.HUB.washer_d + 2 * G.FREE) / 2),
          'pinion screw + washer access through the lip')
    param('pocket_x', '%.4f mm' % (G.CASE_FAR + G.LOC / 2), 'symmetric servo pocket half length')
    param('pocket_z', '%.4f mm' % (G.SERVO.case_w / 2 + G.LOC / 2), 'servo pocket half width, in z')
    param('case_bot', '%.4f mm' % (G.CASE_BOT_Y - G.LOC / 2), 'lib/grip - pocket floor')
    param('tab_y0', '%.4f mm' % (G.TAB_Y - G.LOC / 2), 'far tab slot, underside')
    param('tab_y1', '%.4f mm' % (G.TAB_Y + G.SERVO.tab_thk + G.LOC / 2), 'far tab slot, top')
    param('tab_x1', '%.4f mm' % (G.CASE_FAR + G.TAB_OVER + G.LOC / 2), 'far tab slot, outer end')
    param('lead_y', '%.4f mm' % G.LEAD_Y, 'lib/servo lead datum, in the head frame')
    param('lead_r', '%.4f mm' % (G.SERVO.lead_bundle_dia / 2 + G.LOC), 'lead notch half size')
    param('cav_z0', '%.4f mm' % G.CAVITY_Z0, 'lib/grip - one wall over the servo pocket')
    param('wall', '%.4f mm' % G.WALL, 'MIN_WALL')
    param('eff_x', '%.4f mm' % G.EFF_BOLT_X, 'rotator bolt pattern - wro_bolt_x')
    param('eff_z', '%.4f mm' % G.EFF_BOLT_Z, 'rotator bolt pattern - wro_bolt_z')
    param('eff_cbore_d', '%.4f mm' % G.EFF_CBORE_D, 'passes the O5.5 head from the front')
    param('eff_cbore_h', '%.4f mm' % G.EFF_CBORE_H, 'head recess in the back wall')
    param('bolt_d', '%.4f mm' % G.M3['clearance'], 'M3 clearance')
    param('bolt_x', '%.4f mm' % G.BOLT_FRONT_X, 'lib/grip - clamp bolts at x +/- this')
    param('bolt_y', '%.4f mm' % G.BOLT_FRONT_Y, 'lib/grip - clamp bolts at this y')
    param('hex_af', '%.4f mm' % G.HEX_AF, 'M3 nut OR O5.5 head')
    param('hex_deep', '%.4f mm' % G.HEX_DEEP, 'lib/grip - M3 x 30 lands flush')

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
    chf = comp.features.chamferFeatures
    fil = comp.features.filletFeatures
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

    def poly(name, pts, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(P3(a[0], a[1], 0), P3(b[0], b[1], 0))
        return extrude(one(sk), op, z0_expr, dz_expr, name)

    def box(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        return poly(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0_expr, dz_expr, op)

    def circ_y(name, x, z, r, y0_expr, dy_expr):
        """A hole along +y (the XZ sketch normal is +Y in Fusion)."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(x, 0, z)), r)
        return extrude(one(sk), CUT, y0_expr, dy_expr, name)

    def circ_z(name, x, y, r, z0_expr, dz_expr):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(P3(x, y, 0), r)
        return extrude(one(sk), CUT, z0_expr, dz_expr, name)

    def hex_z(name, x, y, z0_expr, dz_expr):
        r = val('hex_af') / math.sqrt(3)
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        pts = [P3(x + r * math.cos(math.pi / HEX_SIDES * (2 * i)),
                  y + r * math.sin(math.pi / HEX_SIDES * (2 * i)), 0) for i in range(HEX_SIDES)]
        for i in range(HEX_SIDES):
            sk.sketchCurves.sketchLines.addByTwoPoints(pts[i], pts[(i + 1) % HEX_SIDES])
        return extrude(one(sk), CUT, z0_expr, dz_expr, name)

    xh, rx = val('x_half'), val('rear_x')
    fy, by, ty = val('front_y'), val('back_y'), val('taper_y')
    hz = val('half_z')
    eps = G.EF / 10

    # ---- phase 1: outer form, BEFORE any cut ----
    t0 = design.timeline.count
    poly('hand', [(-xh, fy), (xh, fy), (xh, ty), (rx, by), (-rx, by), (-xh, ty)],
         '0 mm', PREFIX + 'half_z', NEW)
    body = comp.bRepBodies.item(0)
    vert = adsk.core.ObjectCollection.create()
    for e in body.edges:
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.x - b.x) < eps and abs(a.y - b.y) < eps and abs(a.z - b.z) > eps:
            vert.add(e)
    fi = fil.createInput()
    fi.addConstantRadiusEdgeSet(vert, V(STYLE + 'radius'), True)
    f = fil.add(fi)
    f.name = 'plan_corners'
    top = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.z - hz) < eps and abs(bb.maxPoint.z - hz) < eps:
            top.add(e)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(top, V(PREFIX + 'facet'), False)
    f = chf.add(ci)
    f.name = 'top_facet'
    group(t0, PH_FORM)

    # ---- phase 2: the channel, the lip, the tie slot ----
    t1 = design.timeline.count
    wide = xh + val('wall')
    box('rack_channel', -wide, wide, -val('chan_y'), val('chan_y'), '0 mm', PREFIX + 'chan_z', CUT)
    circ_y('pinion_face_relief', 0, 0, val('pin_r'), PREFIX + 'chan_y - 0.1 mm',
           PREFIX + 'pin_front - ' + PREFIX + 'chan_y + 0.1 mm')
    circ_y('pinion_screw_access', 0, 0, val('access_r'), PREFIX + 'chan_y - 0.1 mm',
           PREFIX + 'front_y - ' + PREFIX + 'chan_y + 1 mm')
    box('tie_slot', -G.FREE / 10, wide, val('chan_y') - eps, fy + val('wall'),
        PREFIX + 'slot_z0', PREFIX + 'chan_z - ' + PREFIX + 'slot_z0', CUT)
    group(t1, PH_MECH)

    # ---- phase 3: servo bay ----
    t2 = design.timeline.count
    px = val('pocket_x')
    box('servo_pocket', -px, px, val('case_bot'), -val('chan_y'), '0 mm', PREFIX + 'pocket_z', CUT)
    for sx in (-1, 1):
        box('tab_slot_%d' % (sx + 1), min(sx * (px - eps), sx * val('tab_x1')),
            max(sx * (px - eps), sx * val('tab_x1')),
            val('tab_y0'), val('tab_y1'), '0 mm', PREFIX + 'pocket_z', CUT)
        box('lead_notch_%d' % (sx + 1), min(sx * (px - eps), sx * wide), max(sx * (px - eps), sx * wide),
            val('lead_y') - val('lead_r'), val('lead_y') + val('lead_r'),
            '0 mm', PREFIX + 'lead_r', CUT)
    box('cavity', -px, px, val('case_bot'), -val('chan_y') - val('wall'),
        PREFIX + 'cav_z0', PREFIX + 'chan_z - ' + PREFIX + 'cav_z0', CUT)
    group(t2, PH_SERVO)

    # ---- phase 4: rotator screws through the back wall, clamp bolts ----
    t3 = design.timeline.count
    for sx in (-1, 1):
        x = sx * val('eff_x')
        circ_y('eff_screw_%d' % (sx + 1), x, val('eff_z'), val('bolt_d') / 2,
               PREFIX + 'back_y - 1 mm', PREFIX + 'case_bot - ' + PREFIX + 'back_y + 1 mm')
        circ_y('eff_access_%d' % (sx + 1), x, val('eff_z'), val('eff_cbore_d') / 2,
               PREFIX + 'case_bot - ' + PREFIX + 'eff_cbore_h',
               PREFIX + 'front_y - ' + PREFIX + 'case_bot + ' + PREFIX + 'eff_cbore_h + 1 mm')
        circ_z('clamp_%d' % (sx + 1), sx * val('bolt_x'), val('bolt_y'), val('bolt_d') / 2,
               '-1 mm', PREFIX + 'half_z + 2 mm')
        hex_z('clamp_hex_%d' % (sx + 1), sx * val('bolt_x'), val('bolt_y'),
              PREFIX + 'half_z - ' + PREFIX + 'hex_deep', PREFIX + 'hex_deep + 1 mm')
    group(t3, PH_FIX)

    assert comp.bRepBodies.count == 1, 'the shell came out in %d pieces' % comp.bRepBodies.count
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
    print("body: '%s' | appearance: %s | PRINT %d, split face down" % (body.name, used, QTY))
    print('hand %.1f wide tapering to %.1f, %.1f long (y %.2f..%.2f), %.1f tall as a pair'
          % (2 * xh * 10, 2 * rx * 10, (fy - by) * 10, by * 10, fy * 10, 2 * hz * 10))
    print('channel y +/-%.3f, roof z %.2f | lip under the teeth z %.2f..%.2f | tie slot z %.3f..%.2f'
          % (G.CHAN_Y, G.CHAN_Z, G.TIP_Z, G.TIE_SLOT_Z0, G.TIE_SLOT_Z0, G.CHAN_Z))
    print('SG90: tab datum y %.2f, case y %.2f..%.2f, symmetric pocket x +/-%.2f, lead notch y %.2f'
          % (G.TAB_Y, G.CASE_BOT_Y, G.CASE_TOP_Y, px * 10, G.LEAD_Y))
    print('rotator: 2 of 4 M3 x %.0f at (+/-%.1f, %.1f) through a %.1f back wall, heads %.1f deep'
          % (G.EFF_SCREW_L, G.EFF_BOLT_X, G.EFF_BOLT_Z, G.BACK_WALL_T, G.EFF_CBORE_H))
    print('clamp: 2 x M3 x %.0f at (+/-%.1f, %.1f), hex %.1f af x %.1f each face'
          % (G.CLAMP_L, G.BOLT_FRONT_X, G.BOLT_FRONT_Y, G.HEX_AF, G.HEX_DEEP))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
             bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | printed ~%.1f g each | valid: %s'
          % (vol, vol * G.PETG_PRINTED_G_PER_MM3, body.isValid))
    print('timeline groups: %r' % (PHASES,))
