"""robotarm/forearm_nx - Fusion MCP generating script.

Rebuilds `robotarm_forearm_nx` (idempotent). Spec: specs/robotarm/forearm.md
for the joint contract and specs/robotarm/_forearm_print.md for the split;
styled per specs/robotarm/_style.md.

THE -X SIDE PLATE OF THE FOREARM. One of the three pieces the forearm now
prints as - forearm_px, this, and two copies of forearm_rail. forearm.py
still builds the assembled reference and still declares every fa_*
parameter; this file reads that contract and cuts the other plate from it.

THE TWO PLATES ARE NOT MIRROR IMAGES, which is why this is a second file and
not a second copy of the first. wrist_roll got away with one design printed
twice because its halves really are reflections; these are not. This side
carries the J3 DRIVE bore and the J3 servo STANDOFF; the other carries the
608ZZ idler pocket and the J4 servo lobe. Only the outline, the waist, the
J4 journal and the seam are common - and those live in lib/forearm_split.py
so that the two files cannot drift apart on them.

WHAT IS ON THIS SIDE.

  - the J4 pitch journal and its flange counterbore, the same pair the other
    plate carries, because the wrist hub is journalled in BOTH;
  - the J3 DRIVE bore, and it has NO flange counterbore. j3_gear's O20
    journal runs in it but that part has no flange - its gear disc stands
    proud of the face - so the counterbore that retains every other hub in
    this arm is deliberately absent. Leaving it would cut the journal's
    bearing length from the full fa_plate_t to fa_journal, against a hub
    built for the whole plate, and j3_gear.py asserts fa_plate_t is that
    whole thickness;
  - the J3 servo STANDOFF web, with the gear and pinion clearance cylinders
    cut through it and the two fa_cap_* pilots j3_servo_cap bolts into. The
    PAD is not here and must not come back - see _HANDOFF section 10;
  - the servo seat, and the seam.

PRINT ORIENTATION: INNER FACE DOWN - the split plane, x = -fa_plate_in, on
the bed, built along -X. Same reasoning as the other plate: a side plate is
a horizontal slab when it is built along X, and a slab prints perfectly as
the FIRST layer and impossibly otherwise. Here that face is 1084 mm2 of
first layer.

AND IT IS WHY THIS PIECE PRINTS AT ALL. In the one-piece part this plate was
the WORST of the two: the J3 boss disc floated 10.80 mm up on nothing,
because everything under it is the 36T gear's swept volume, and the whole
part balanced on the carved standoff web - 330 mm2 of bed under a 56.50 mm
tower. Turned over, the standoff is at the TOP of the build and lands on the
plate, the gear and pinion cuts remove material as the build rises rather
than adding it, the flange counterbore opens to the sky, and the cap pilots
open at the very top.

NOTHING MAY LIE OUTBOARD OF THE BED FACE in +X. Asserted against the built
body's bounding box at the end of this file, not trusted - it is the rule
that keeps the rails off this piece.

WHAT STILL NEEDS SUPPORT, HONESTLY. 370 mm2, in two places, neither of them
structural and neither inside the straddle:

  317 mm2  the J4 flange counterbore, roofed by the standoff block that
           passes over it. A BRIDGE, not a ledge - it spans 24.35 mm against
           design_rules MAX_BRIDGE_MM 40.0, and fa_cbore_extra leaves 0.50 mm
           of designed clearance under it, so sag there touches nothing. It
           cannot be relieved: the block has to cross y = 0 because
           fa_cap_screw_y puts the cap screws at 4.90, well inside the
           counterbore's own radius.
   52 mm2  the ledge where the standoff block oversails the seat by one
           fa_wall - 1.60 mm wide, one nozzle line.

The SHARED derivations come from lib/forearm_split.py, the same objects
forearm.py and forearm_px.py use.

A NOTE ON ONE WORD. Like forearm.py, this docstring avoids the word
tests/test_fusion_scripts.py scans for - the one naming a script that places
an imported mesh or a measured transform. Carrying it SKIPS the magic-number
and entity-naming lints for the whole file, silently and with a green run to
show for it.
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

from lib.forearm_split import ServoBlock, Silhouette  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_forearm_nx'
BODY_NAME = 'forearm_nx'
PREFIX = 'fn_'
FOREARM = 'fa_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('forearm')

PH_FORM = 'plate form'
PH_PIVOT = 'pivot journals'
PH_ELBOW = 'elbow drive clearance'
PH_SEAM = 'rail seam'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_PIVOT, PH_ELBOW, PH_SEAM, PH_FINISH]

EPS = 1e-9
EPS_MM = 1e-6
FACET = True
LOBE_FILLET = True


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def _set(full, expr, comment, units='mm'):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment=''):
        _set(PREFIX + name, expr, comment)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def fa(name):
        p = ups.itemByName(FOREARM + name)
        assert p is not None, (
            'fa_%s is not in this document. forearm_nx is one PIECE of a '
            'split part - build forearm.py first, in the same document, so '
            'the interface is read rather than guessed' % name)
        return p.value

    L2 = fa('l2')
    Y_PIN = -L2 + fa('j3_centre')

    param('split', FOREARM + 'plate_in',
          'THE SPLIT PLANE, AND THE BED FACE, at x = MINUS this. The plate is\n'
          '           cut off the arm here and printed with that face down, so this\n'
          '           one number is both the joint and the print orientation. Held\n'
          '           positive and negated at every use, so it reads as the same\n'
          '           fa_plate_in the other plate splits on rather than as its own\n'
          '           number that happens to match.')
    param('reach', FOREARM + 'plate_out + ' + FOREARM + 'j3_standoff - '
          + PREFIX + 'split',
          'derived build height: bed face to the J3 standoff\'s outer face,\n'
          '           which is the outermost thing on this piece and the face\n'
          '           j3_servo_cap bolts to. 18.20 mm, against 56.50 for the\n'
          '           one-piece part.')
    param('facet', FOREARM + 'facet', 'fa_facet - the plate outline chamfer')
    param('lobe_radius', FOREARM + 'lobe_radius_j3',
          'fa_lobe_radius_j3 - a PROBED ceiling, not a preference. The J3\n'
          '           corner edge runs from inside the plate, through the gear\n'
          '           clearance cut, to the standoff face, and the faces either side\n'
          '           of it change along the way; 6.0 and 5.5 and 5.0 all fail.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    SIL = Silhouette(l2=L2 * 10, boss_r=fa('boss_r') * 10,
                     waist_z=fa('waist_z') * 10)
    _bad = SIL.validate()
    assert not _bad, 'the link outline is not buildable: ' + '; '.join(_bad)
    BLK = ServoBlock(y_pivot=Y_PIN * 10, run=+1, shaft_end=fa('shaft_end') * 10,
                     case_l=fa('case_l') * 10, tab_pitch=fa('tab_pitch') * 10,
                     lobe_pad=fa('lobe_pad') * 10)
    _bad = BLK.validate()
    assert not _bad, 'the J3 servo block does not place: ' + '; '.join(_bad)

    # THE BLOCK REACHES TO fa_cap_reach, NOT TO ITS OWN PAD. J4's block stops
    # one fa_lobe_pad past its outer screw; J3's has to carry the cap's two
    # M3 as well, and the web left by the pinion cut has nowhere else to put
    # them. fa_cap_reach is that station, solved in forearm.py against the
    # servo window, the block edge and the servo's own outer tab pilot.
    block_lo = BLK.span[0] / 10
    block_hi = fa('cap_reach')
    seat_hi = min(block_hi, fa('seat_y_max'))
    assert seat_hi > block_lo, (
        'fa_seat_y_max %.2f has cut the seat away entirely against a block '
        'starting at %.2f' % (fa('seat_y_max') * 10, block_lo * 10))
    assert SIL.contains_band(block_lo * 10, seat_hi * 10, fa('seat_z') * 10), (
        'the seat is %.2f half-tall over y %.2f..%.2f and the link outline '
        'is thinner than that somewhere in that span'
        % (fa('seat_z') * 10, block_lo * 10, seat_hi * 10))
    for _ys in (fa('seam_y_a'), fa('seam_y_b')):
        _half = SIL.half_z(_ys * 10)
        assert _half >= (fa('seam_z') + fa('seam_clear_d') / 2) * 10, (
            'the seam hole at y %.2f needs %.2f of outline and there is %.2f'
            % (_ys * 10, (fa('seam_z') + fa('seam_clear_d') / 2) * 10, _half))
    # THE WHOLE REASON THE STANDOFF IS A WEB AND NOT A BLOCK, restated here so
    # the geometry below cannot quietly stop being true: the pinion clearance
    # circle is TALLER than the block, so it cuts the standoff clean through
    # top to bottom and what is left joining the block to the plate is a web
    # at the WRIST end. Priced in _HANDOFF section 9 - 71x on interlayer
    # shear - and that pricing is untouched by the split, because this piece
    # still builds along X and the web is still whole and still integral.
    assert fa('j3_pin_clear') > fa('lobe_z'), (
        'the pinion clears at r %.2f and the block is %.2f tall, so the '
        'pinion circle does NOT cut the standoff through - the web analysis '
        'in _HANDOFF section 9 no longer describes this part'
        % (fa('j3_pin_clear') * 10, fa('lobe_z') * 10))

    # ---- idempotent rebuild -------------------------------------------------
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
    assert comp.name == COMPONENT, (
        'component came back as %r - a stale component still holds the name'
        % comp.name)
    ext = comp.features.extrudeFeatures
    fil = comp.features.filletFeatures
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
                sk.name + ': expected ' + str(expected)
                + ', got ' + str(sk.profiles.count))
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
            g = design.timeline.timelineGroups.add(
                start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm, z_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def yz_circle(name, y_c, z_c, d_cm, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            mpt(sk, 0, y_c, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def yz_rect(name, y0, y1, z0, z1, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, 0, y0, z0), mpt(sk, 0, y1, z1))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def link_profile(name, y_a, y_b, r_end, r_fil, x0_expr, dx_expr, op):
        """The connecting-rod outline. Shape from lib/forearm_split; this is
        the Fusion plumbing that draws it, and it is the only part of the
        outline repeated between the two plate scripts - a sketch cannot live
        in a module that does not import Fusion."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        arcs = sk.sketchCurves.sketchArcs
        half = abs(y_b - y_a) / 2.0
        mid_y = (y_a + y_b) / 2.0
        h = math.sqrt((r_fil + r_end) ** 2 - half ** 2)
        waist = h - r_fil
        assert waist > 0, 'fillet radius %.1f pinches the link shut' % (r_fil * 10)

        def tangent(cy, fz):
            dy, dz = mid_y - cy, fz
            n = math.hypot(dy, dz)
            return (cy + r_end * dy / n, r_end * dz / n)

        for sz in (+1, -1):
            fz = sz * h
            ta, tb = tangent(y_a, fz), tangent(y_b, fz)
            arcs.addByThreePoints(mpt(sk, 0, ta[0], ta[1]),
                                  mpt(sk, 0, mid_y, sz * waist),
                                  mpt(sk, 0, tb[0], tb[1]))
        for cy, out in ((y_a, y_a + r_end if y_a > y_b else y_a - r_end),
                        (y_b, y_b + r_end if y_b > y_a else y_b - r_end)):
            up, dn = tangent(cy, h), tangent(cy, -h)
            arcs.addByThreePoints(mpt(sk, 0, up[0], up[1]),
                                  mpt(sk, 0, out, 0.0),
                                  mpt(sk, 0, dn[0], dn[1]))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name), waist

    def edge_along_x_at(y_c, z_c, min_len=0.0):
        """Edges running along X at one (y, z) corner, at least min_len long.

        The length filter is not tidiness: the standoff's INBOARD corner is
        split by the gear clearance cut into a short stub inside the plate
        and a longer one on the block, and asking a 4.5 fillet to run along
        the stub is an ASM_INCONS_FACE.
        """
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            b = e.boundingBox
            if (abs(b.minPoint.y - b.maxPoint.y) < val('tol')
                    and abs(b.minPoint.z - b.maxPoint.z) < val('tol')
                    and abs(b.minPoint.y - y_c) < val('tol')
                    and abs(b.minPoint.z - z_c) < val('tol')
                    and e.length >= min_len - EPS):
                col.add(e)
        return col

    OUT = '-' + FOREARM + 'plate_out'
    IN_D = FOREARM + 'plate_out - ' + PREFIX + 'split'
    BAND = '-(' + FOREARM + 'plate_out + ' + FOREARM + 'j3_standoff)'

    # ---- phase 1: plate form ------------------------------------------------
    t0 = design.timeline.count
    _, waist_z = link_profile(
        'waist', 0.0, -L2, fa('boss_r'), SIL.arc_r / 10,
        '-(' + PREFIX + 'split + ' + FOREARM + 'waist_t)',
        FOREARM + 'waist_t', NEW)
    assert abs(waist_z * 10 - SIL.waist_z) < EPS_MM, (
        'link_profile drew a %.4f waist and lib/forearm_split solves %.4f'
        % (waist_z * 10, SIL.waist_z))
    for y_p, jnt in ((0.0, 'j4'), (-L2, 'j3')):
        yz_circle('boss_' + jnt, y_p, 0.0, 2 * fa('boss_r'), OUT, IN_D, JOIN)
    yz_rect('seat_j3', block_lo, seat_hi, -fa('seat_z'), fa('seat_z'),
            OUT, FOREARM + 'lobe_seat', JOIN)
    # THE STANDOFF, AS ONE BLOCK from inside the plate out to the pad face.
    # Phase 3 then carves the gear and the pinion out of it, which is what
    # makes the standoff a WEB rather than something drawn by hand and gone
    # stale the next time either gear changes size.
    yz_rect('standoff_j3', block_lo, block_hi, -fa('lobe_z'), fa('lobe_z'),
            BAND, FOREARM + 'j3_standoff + ' + FOREARM + 'lobe_over', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: pivot journals --------------------------------------------
    t1 = design.timeline.count
    yz_circle('bore_j4', 0.0, 0.0, fa('bore_d'), OUT, IN_D, CUT)
    # Cut from the OUTER face, so in this orientation it opens at the TOP of
    # the build - and the standoff block above it roofs the part of it the
    # block crosses. That bridge is this piece's largest remaining ceiling
    # and it is a bridge, not a ledge: 24.35 mm against MAX_BRIDGE_MM 40.0,
    # with fa_cbore_extra 0.50 of clearance under it so sag touches nothing.
    yz_circle('cbore_j4', 0.0, 0.0, fa('cbore_d'), OUT,
              FOREARM + 'cbore_depth', CUT)
    # J3 DRIVE SIDE, AND NO COUNTERBORE - see the docstring. j3_gear has no
    # flange, and j3_gear.py asserts this journal is the full fa_plate_t.
    yz_circle('bore_j3', -L2, 0.0, fa('bore_d'), OUT, IN_D, CUT)
    group(t1, PH_PIVOT)

    # ---- phase 3: elbow drive clearance -------------------------------------
    t2 = design.timeline.count
    # Both gears turn in the band between the plate outer face and the servo
    # pad, and BOTH are cut out of the block above rather than drawn around.
    # Building along -X these cuts REMOVE material as the build rises, so
    # they cost nothing in support - in the one-piece part, built the other
    # way, this same pair was 317 mm2 of re-solidifying ceiling.
    yz_circle('gear_sweep_j3', -L2, 0.0, 2 * fa('j3_gear_clear'),
              BAND, FOREARM + 'j3_standoff', CUT)
    yz_circle('pinion_sweep_j3', Y_PIN, 0.0, 2 * fa('j3_pin_clear'),
              BAND, FOREARM + 'j3_standoff', CUT)
    # THE CAP'S TWO M3, into the end face of what is left. The station was
    # solved in forearm.py against the servo window, the block edge and the
    # servo's own outer tab pilot - which is the one that is easy to miss,
    # because it is blind in the same face the cap sinks its counterbore
    # into, so the two collide underground while looking 2.4 mm apart.
    for sz in (+1, -1):
        yz_circle('cap_pilot_%s' % ('p' if sz > 0 else 'm'),
                  fa('cap_screw_y'), sz * fa('cap_screw_z'),
                  fa('cap_pilot_d'), BAND, FOREARM + 'cap_pilot_depth', CUT)
    group(t2, PH_ELBOW)

    # ---- phase 4: the rail seam ---------------------------------------------
    t3 = design.timeline.count
    for tag, ys in (('a', fa('seam_y_a')), ('b', fa('seam_y_b'))):
        for sz, zt in ((+1, 'p'), (-1, 'm')):
            yz_circle('seam_clear_%s%s' % (tag, zt), ys, sz * fa('seam_z'),
                      fa('seam_clear_d'),
                      '-(' + PREFIX + 'split + ' + FOREARM + 'waist_t)',
                      FOREARM + 'waist_t', CUT)
    group(t3, PH_SEAM)

    # ---- phase 5: finish ----------------------------------------------------
    t4 = design.timeline.count
    n_fillet, skipped, buried = 0, 0, 0
    col = adsk.core.ObjectCollection.create()
    for y_c in (block_lo, block_hi):
        for z_c in (-fa('lobe_z'), fa('lobe_z')):
            in_boss = False
            for y_b in (0.0, -L2):
                if math.hypot(y_c - y_b, z_c) < fa('boss_r'):
                    in_boss = True
            if in_boss:
                buried += edge_along_x_at(y_c, z_c).count
                continue
            rad = val('lobe_radius')
            skipped += (edge_along_x_at(y_c, z_c).count
                        - edge_along_x_at(y_c, z_c, rad).count)
            for e in edge_along_x_at(y_c, z_c, rad):
                col.add(e)
    if col.count and LOBE_FILLET:
        f_inp = fil.createInput()
        f_inp.addConstantRadiusEdgeSet(col, V(PREFIX + 'lobe_radius'), True)
        fil.add(f_inp).name = 'standoff_corners_j3'
        n_fillet = col.count
    n_face = 0
    if FACET:
        fcol = adsk.core.ObjectCollection.create()
        x_pick = -fa('plate_out')
        for e in comp.bRepBodies.item(0).edges:
            bb = e.boundingBox
            if abs(bb.minPoint.x - x_pick) > val('tol'):
                continue
            if abs(bb.maxPoint.x - x_pick) > val('tol'):
                continue
            t = e.geometry.objectType
            if not (t.endswith('Arc3D') or t.endswith('Circle3D')):
                continue
            reach = max(abs(bb.minPoint.z), abs(bb.maxPoint.z))
            if abs(reach - fa('boss_r')) < val('tol'):
                fcol.add(e)
        n_circ = sum(1 for e in fcol
                     if e.geometry.objectType.endswith('Circle3D'))
        # The honest assert is about what the edges ARE, not how many. On
        # this face the standoff block runs past where the silhouette arc
        # ends and blends into it, SPLITTING the arc into two segments, so a
        # bare count of 2 was right only while the outline came in one piece.
        assert n_circ == 1, (
            'expected exactly one closed boss circle on the plate outer '
            'face, found %d - the selection is picking up a bore' % n_circ)
        assert fcol.count - n_circ >= 1, 'no silhouette arc on the outer face'
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            fcol, V(PREFIX + 'facet'), False)
        chf.add(c_inp).name = 'plate_facet'
        n_face = fcol.count
    group(t4, PH_FINISH)

    # ---- identity, the bed-face rule, diagnostics ---------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - the pinion cut has severed the standoff '
        'from the plate' % comp.bRepBodies.count)
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
    assert bb.maxPoint.x <= -val('split') + val('tol'), (
        'the piece reaches x %.3f, outboard of its own bed face at %.3f - '
        'anything past the bed cannot print, and the rails are a separate '
        'piece for exactly this reason'
        % (bb.maxPoint.x * 10, -val('split') * 10))
    assert bb.minPoint.x >= -(fa('plate_out') + fa('j3_standoff')) - val('tol'), (
        'the piece reaches x %.3f, past the J3 pad face at %.3f - that face '
        'is j3_servo_cap\'s seating plane'
        % (bb.minPoint.x * 10, -(fa('plate_out') + fa('j3_standoff')) * 10))

    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used_appearance))
    print('PIECE 2 of 3: the -X side plate. forearm_px and 2 x forearm_rail '
          'complete the forearm; forearm.py is the assembled reference')
    print('print: INNER FACE DOWN, x %.2f on the bed, built along -X - %.2f mm '
          'tall, all bores VERTICAL'
          % (-val('split') * 10, val('reach') * 10))
    print('J4: bore %.2f, flange counterbore %.2f x %.1f deep (opens UP, and '
          'the standoff bridges %.2f of it)'
          % (fa('bore_d') * 10, fa('cbore_d') * 10, fa('cbore_depth') * 10,
             fa('cbore_d') * 10))
    print('J3 drive: bore %.2f through the full %.1f plate, NO flange '
          'counterbore - j3_gear has no flange'
          % (fa('bore_d') * 10, fa('plate_t') * 10))
    print('J3 standoff: y %.2f..%.2f, seat to y %.2f, %.2f deep; gear clears '
          'at r %.2f and the pinion at r %.2f, both cut through it'
          % (block_lo * 10, block_hi * 10, seat_hi * 10,
             fa('j3_standoff') * 10, fa('j3_gear_clear') * 10,
             fa('j3_pin_clear') * 10))
    print('   the servo PAD is NOT here - it is j3_servo_cap, bolted to this '
          'web by 2 x M3 at y %.2f, z +/-%.2f, %.2f pilot x %.1f deep'
          % (fa('cap_screw_y') * 10, fa('cap_screw_z') * 10,
             fa('cap_pilot_d') * 10, fa('cap_pilot_depth') * 10))
    print('seam: 4 x %.2f clearance at y %.2f / %.2f, z +/-%.2f'
          % (fa('seam_clear_d') * 10, fa('seam_y_a') * 10,
             fa('seam_y_b') * 10, fa('seam_z') * 10))
    print('finish: %d standoff corner edges at r %.2f (%d too short, %d '
          'inside a boss), %d outline edges faceted at %.2f'
          % (n_fillet, val('lobe_radius') * 10, skipped, buried, n_face,
             val('facet') * 10))
    print('bbox x %.2f..%.2f | y %.2f..%.2f | z %.2f..%.2f | volume %.1f mm3 '
          '| mass %.2f g | valid %s'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10,
             bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10,
             body.physicalProperties.volume * 1000,
             body.physicalProperties.mass * 1000, body.isValid))
