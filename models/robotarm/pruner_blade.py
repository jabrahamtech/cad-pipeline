"""robotarm/pruner_blade - Fusion MCP generating script.

Rebuilds `robotarm_pruner_blade` (idempotent). Spec: specs/robotarm/pruner.md,
styled per specs/robotarm/_style.md. Linkage from lib/pruner_linkage.py.

ONE design, TWO copies, the second TURNED OVER (180 deg about Y, so
(x, y, z) -> (-x, y, -z)). The two share one pivot post: true scissors.

Local frame: origin ON THE PIVOT. +Y toward the nose, +X into the body and
away from the cutting edge, +Z the thickness. THE CUTTING EDGE LIES ON THE
PLANE x = pb_edge_off, OFFSET FROM THE PIVOT, AND THAT IS THE WHOLE
MECHANISM. The first build laid both edges ON the pivot. Two straight lines
through one point meet at that point and nowhere else, and at closure they go
coincident along their entire length in one instant: the whole stem section
shears at once, there is no travelling contact, and the scissor advantage is
exactly 1. It is a V-pinch with a nice pivot, and it would have crushed stems
rather than cut them.

Offset each edge by a and the two cross at exactly ONE point, at
r = a / sin(theta), sweeping IN from the tip as the blades close. At theta = 0
the edges are parallel and 2a apart - that is the mouth, and it does not
taper. Advantage climbs as the crossing sweeps in, which is why every pruner
carries the same instruction: put the stem deep in the throat.

THE STEEL IS NOT PRINTED. A PETG edge crushes plant tissue instead of
severing it and is blunt after a handful of cuts. The nose carries a 9 mm
snap-off cutter segment in a pocket in its INNER face, so the steel's own
face is flush with the carrier's and the two blades' edges pass with
`pb_gap` between them. Blades are consumables; the pocket is a slide-in fit
with one clamp screw, not a glue joint.

Cut at the THROAT, not the tip. Advantage is 3.25 at the throat root and
1.30 at the tip - the same 2.5x falloff every bypass pruner has. A stem cut
at the tip gets 11 N and is crushed.

Print orientation: INNER FACE (z = pb_gap) ON THE BED, built along +Z. The
blade pocket then opens upward, the pivot bore and the drive slot are
vertical, and the part is a flat plate. No support.
"""

import math
import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)
# FUSION KEEPS ONE PYTHON SESSION ALIVE ACROSS EVERY SCRIPT RUN, so `lib` stays
# in sys.modules from the last run and an edited solver is NOT picked up. Today
# that raised ImportError because a constant was new; the normal case is worse -
# the CAD quietly rebuilds against yesterday's numbers and every diagnostic
# looks right. Purge it, every time, before importing.
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]
from lib.pruner_linkage import CHOSEN, PIN_DIA_MM  # noqa: E402

COMPONENT = 'robotarm_pruner_blade'
BODY_NAME = 'pruner_blade'
PREFIX = 'pb_'
STYLE = 'sty_'
PH_FORM = 'carrier form'
PH_PIVOT = 'pivot'
PH_STEEL = 'blade pocket'
PH_DRIVE = 'drive slot'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_PIVOT, PH_STEEL, PH_DRIVE, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A blade carrier is a moving part: dark.
APPEARANCE_HINTS = [('plastic', 'black'), ('paint', 'black'), ('black',), ('plastic',)]


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

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- fits -----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('slide', '0.25 mm', 'sliding fit - design_rules CALIBRATED')
    param('rot', '0.35 mm', 'rotating fit - design_rules')

    # --- linkage, from lib/pruner_linkage.CHOSEN ------------------------------
    param('tail_r', '%.3f mm' % CHOSEN.tail_r,
          'pivot to the drive pin. FROM lib/pruner_linkage.CHOSEN - change it\n'
          '           there, not here, or the solver and the CAD drift apart.')
    param('throat_r', '%.3f mm' % CHOSEN.throat_r, 'pivot to where the stem sits')
    param('tip_r', '%.3f mm' % CHOSEN.tip_r, 'pivot to the far end of the usable edge')
    param('sweep', '%.3f deg' % CHOSEN.half_sweep_deg, 'blade rotation each way',
          'deg')

    # --- carrier --------------------------------------------------------------
    param('thk', '3.5 mm', 'carrier thickness')
    param('gap', '0.05 mm',
          'half the bypass gap. The two carriers face each other across 2x this,\n'
          '           and the steel edges with them. A scissor wants its edges in light\n'
          '           rubbing contact; this leaves 0.10 and the pivot screw takes it up.')
    param('edge_off', '%.3f mm' % CHOSEN.edge_offset,
          'perpendicular distance from the PIVOT to the cutting edge. FROM\n'
          '           lib/pruner_linkage.CHOSEN. Zero here means the tool crushes\n'
          '           instead of cutting - see the docstring.')
    param('hub_r', '6.0 mm',
          'boss round the pivot. It also sets how DEEP a stem can go: the hub\n'
          '           fills the throat inside this radius, and advantage climbs the\n'
          '           deeper the cut is, so every millimetre here is force given up.')
    param('pivot_d', '3.2 mm', 'M3 clearance - design_rules FASTENER_MM')
    param('pin_d', '%.2f mm' % PIN_DIA_MM,
          'the rack\'s drive pin - FROM lib/pruner_linkage. The slot is sized off\n'
          '           THIS, not off the pivot: they are the same nominal today and a\n'
          '           change to either would silently mis-size the slot otherwise.')
    param('nose_root_w', '10.0 mm', 'nose width at the hub, measured off the edge')
    param('nose_tip_w', '5.0 mm', 'nose width at the tip')
    param('nose_len', PREFIX + 'tip_r + 2.0 mm', 'derived: usable edge plus a nose')
    param('tail_w', '8.0 mm', 'tail width')
    param('slot_w', PREFIX + 'pin_d + ' + PREFIX + 'slide',
          'derived drive slot width: the pin is the same 3.0 nominal as the pivot,\n'
          '           on a sliding fit')
    param('tail_len', '0 mm', 'DERIVED IN SCRIPT from the slot - set below')

    # --- steel, 9 mm snap-off segment. NOMINAL, not measured -------------------
    param('steel_t', '0.55 mm', 'segment 0.5 DATASHEET-nominal + 0.05 - GAUGE THIS')
    param('steel_w', '9.2 mm', 'segment 9.0 wide + slide')
    param('steel_len', '11.5 mm', 'one segment between score lines, plus slide')
    param('steel_proud', '1.5 mm',
          'how far the ground edge stands past the carrier. Enough to cut, little\n'
          '           enough that the carrier takes the side load, not the steel.')
    param('clamp_d', '1.8 mm', 'M2 pilot for the segment clamp')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild ---------------------------------------------------
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
    assert comp.name == COMPONENT, (
        'component came back as %r - a stale component still holds the name' % comp.name)
    ext = comp.features.extrudeFeatures
    chf = comp.features.chamferFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
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

    def extrude(profs, op, z0_expr, dz_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0_expr))
        inp.setDistanceExtent(False, V(dz_expr))
        if op != NEW:
            # Without this a CUT eats every other component. See PLAYBOOK.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def poly(name, pts, z0, dz, op):
        sk = sketch('sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(mpt(sk, a[0], a[1]), mpt(sk, b[0], b[1]))
        return extrude(profiles(sk, expected=1), op, z0, dz, name)

    def disc(name, x, y, d, z0, dz, op):
        sk = sketch('sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x, y), d / 2)
        return extrude(profiles(sk, expected=1), op, z0, dz, name)

    def slot(name, y0, y1, w, z0, dz, op):
        """Obround along Y - the drive slot, and nothing else here."""
        sk = sketch('sk_' + name)
        r = w / 2
        lines = sk.sketchCurves.sketchLines
        arcs = sk.sketchCurves.sketchArcs
        lines.addByTwoPoints(mpt(sk, -r, y0), mpt(sk, -r, y1))
        lines.addByTwoPoints(mpt(sk, r, y0), mpt(sk, r, y1))
        arcs.addByThreePoints(mpt(sk, -r, y1), mpt(sk, 0, y1 + r), mpt(sk, r, y1))
        arcs.addByThreePoints(mpt(sk, r, y0), mpt(sk, 0, y0 - r), mpt(sk, -r, y0))
        return extrude(profiles(sk, expected=1), op, z0, dz, name)

    Z0 = PREFIX + 'gap'
    DZ = PREFIX + 'thk'

    # ---- the drive slot has to absorb the arc/line mismatch -------------------
    # The blade's tail point runs on an ARC; the pin that drives it is carried
    # by a rack running in a STRAIGHT channel. The slot is the difference, and
    # it is radial: the pin's distance from the pivot grows as the blade turns.
    # val() hands back Fusion's INTERNAL units - centimetres for length and
    # RADIANS for angle. Wrapping math.radians() round an angle parameter made
    # the sweep 0.5 deg and collapsed this slot to nothing, silently.
    #
    # THE SLOT IS RADIAL, so the pin sits on the line through the pivot at the
    # blade's angle and its distance from the pivot is tail_r / cos(theta).
    # An earlier version used tail_r * sqrt(1 + sin^2) - the locus you get if
    # the blade angle were asin(s / tail_r) instead of atan. Same number to
    # within 1 %, and completely the wrong curve: it puts the pin 1.5 mm
    # sideways of this slot at full sweep, which is straight through its wall.
    th = val('sweep')
    r_far = val('tail_r') / math.cos(th)
    slot_travel = r_far - val('tail_r')
    # Lower bound catches the radians/degrees mix-up that once collapsed this
    # slot to nothing; upper bound catches a sweep that has run away. The slot
    # grows fast with sweep - tail_r/cos(theta) - so 40 deg costs 7.9 mm of it.
    assert 0.1 < slot_travel < 1.5, (
        'drive slot absorbs %.2f mm, which is outside anything sane - check the '
        'units on pb_sweep' % (slot_travel * 10))
    # The tail has to be long enough to CLOSE round the slot. Left to a guessed
    # +4 mm the slot's far arc ran 0.65 mm past the end of the tail and opened
    # it into a fork - which assembles more easily and lets the blade walk off
    # the pin under any load that is not purely tangential. Derive it.
    slot_far = r_far + val('slide') / 2 + val('slot_w') / 2
    param('tail_len', '%.3f mm' % ((slot_far + val('wall')) * 10),
          'derived: far end of the drive slot plus a wall, so the slot is CLOSED')
    assert val('tail_len') > slot_far, 'the drive slot breaks out of the tail'

    # ---- phase 1: carrier form ------------------------------------------------
    t0 = design.timeline.count
    edge_x = val('edge_off')
    nose = [(edge_x, -0.2), (edge_x, val('nose_len')),
            (edge_x + val('nose_tip_w'), val('nose_len')),
            (edge_x + val('nose_root_w'), 0.5), (edge_x + val('nose_root_w'), -0.2)]
    poly('nose', nose, Z0, DZ, NEW)
    disc('hub', 0.0, 0.0, 2 * val('hub_r'), Z0, DZ, JOIN)
    poly('tail', [(-val('tail_w') / 2, -val('tail_len')),
                  (val('tail_w') / 2, -val('tail_len')),
                  (val('tail_w') / 2, 0.2), (-val('tail_w') / 2, 0.2)],
         Z0, DZ, JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: pivot --------------------------------------------------------
    t1 = design.timeline.count
    disc('pivot_bore', 0.0, 0.0, val('pivot_d'), Z0, DZ, CUT)
    group(t1, PH_PIVOT)

    # ---- phase 3: blade pocket --------------------------------------------------
    # In the INNER face, so the steel's own face is flush with the carrier's and
    # the two edges pass on the bypass gap alone.
    t2 = design.timeline.count
    # The edge runs along x = edge_off, so a cut at RADIUS r happens at height
    # y = sqrt(r^2 - edge_off^2). The steel has to cover the radii the crossing
    # actually sweeps, not a range measured straight off the pivot.
    r_in = val('hub_r') + 0.05
    y0 = math.sqrt(max(r_in ** 2 - edge_x ** 2, 0.0))
    r_out = math.hypot(edge_x, y0 + val('steel_len'))
    assert r_out >= val('throat_r'), (
        'the steel only reaches r %.1f, short of the %.1f nominal stem radius'
        % (r_out * 10, val('throat_r') * 10))
    poly('steel_pocket',
         [(edge_x - 0.001, y0), (edge_x - 0.001, y0 + val('steel_len')),
          (edge_x + val('steel_w'), y0 + val('steel_len')), (edge_x + val('steel_w'), y0)],
         Z0, PREFIX + 'steel_t', CUT)
    disc('clamp_pilot', edge_x + val('steel_w') / 2, y0 + val('steel_len') / 2,
         val('clamp_d'), PREFIX + 'gap + ' + PREFIX + 'steel_t',
         PREFIX + 'thk - ' + PREFIX + 'steel_t', CUT)
    group(t2, PH_STEEL)

    # ---- phase 4: drive slot -----------------------------------------------------
    t3 = design.timeline.count
    slot('drive_slot', -(r_far + val('slide') / 2), -(val('tail_r') - val('slide') / 2),
         val('pin_d') + val('slide'), Z0, DZ, CUT)
    group(t3, PH_DRIVE)

    # ---- phase 5: finish -----------------------------------------------------------
    t4 = design.timeline.count
    col = adsk.core.ObjectCollection.create()
    for e in comp.bRepBodies.item(0).edges:
        bb = e.boundingBox
        if (abs(bb.minPoint.z - val('gap')) < val('tol')
                and abs(bb.maxPoint.z - val('gap')) < val('tol')):
            col.add(e)
    if col.count:
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = 'bed_face_chamfer'
    group(t4, PH_FINISH)

    # ---- identity + diagnostics ------------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got %d' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used_appearance = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used_appearance = a.name
                    break
            if used_appearance != 'none':
                break
        if used_appearance != 'none':
            break

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('EDGE OFFSET FROM THE PIVOT - one crossing point, and it travels')
    print('linkage from lib/pruner_linkage.CHOSEN: tail %.1f, throat %.1f, tip %.1f, '
          '+/-%.1f deg' % (val('tail_r') * 10, val('throat_r') * 10,
                           val('tip_r') * 10, math.degrees(val('sweep'))))
    print('MA %.2f at the throat root, %.2f at the tip' % (
        val('tail_r') / val('throat_r'), val('tail_r') / val('tip_r')))
    print('drive slot RADIAL, r %.2f..%.2f, absorbing %.2f mm as the blade turns' % (
        val('tail_r') * 10, r_far * 10, slot_travel * 10))
    print('edge offset %.2f -> mouth %.2f, ONE crossing at r = %.2f / sin(theta)'
          % (edge_x * 10, 2 * edge_x * 10, edge_x * 10))
    print('steel pocket %.1f x %.1f x %.2f in the INNER face, covering r %.1f..%.1f'
          % (val('steel_w') * 10, val('steel_len') * 10, val('steel_t') * 10,
             r_in * 10, r_out * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f (x2 = %.2f) | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 2000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
