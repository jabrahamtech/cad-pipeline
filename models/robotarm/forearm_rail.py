"""robotarm/forearm_rail - Fusion MCP generating script.

Rebuilds `robotarm_forearm_rail` (idempotent). Spec: specs/robotarm/forearm.md
for the joint contract and specs/robotarm/_forearm_print.md for the split;
styled per specs/robotarm/_style.md.

THE FOREARM'S BOX-BEAM FLANGE, AND THE THIRD PIECE OF THE SPLIT. Two side
plates and two of these make the forearm. forearm.py still builds the
assembled reference and still declares every fa_* parameter; this file reads
that contract and cuts the piece that crosses the straddle.

PRINTED TWICE, AND THE SECOND COPY IS A ROTATION, NOT A MIRROR. The straddle
is symmetric in Z about the arm's centreline: the link outline is, both sweep
cylinders are centred on z = 0, the elbow relief is, and the duct is. So the
bottom rail is congruent to the top one. And because this piece is also
symmetric in X - it spans the full straddle and every cut in it is a prism
along X - reflecting it in z is the same solid as turning it 180 degrees
about Y. A rotation preserves handedness, so unlike wrist_roll's two halves
there is NO handedness to get wrong and no second part file. The X symmetry
is what makes that true, so it is asserted against the built body below
rather than left as a remark.

WHY IT EXISTS AT ALL - and it is forced, not chosen. Each side plate prints
INNER FACE DOWN, because a side plate is a horizontal slab when it is built
along X and a slab prints perfectly as the FIRST layer and impossibly
otherwise. Nothing that reaches ACROSS the straddle can then belong to
either plate, because "across the straddle" is "below the bed". The rails
are the only thing that does reach across. So they become their own piece.

AND THIS IS THE EASY ONE. Every face of this piece is either parallel to X
or normal to it, and every hole runs down it, so built along X it is a PRISM:
zero overhang, no bridge, nothing over design_rules MAX_OVERHANG_DEG 50.0 in
any layer. It is also the RIGHT orientation structurally - the layers lie
normal to X, so the beam's bending stress, which runs along Y, is in-plane
rather than across layers. The one cost is a 69 mm2 footprint under a
24.8 mm part: print it with a brim, and print both copies together.

WHAT THE SHAPE IS, AND WHY IT IS CUT RATHER THAN DRAWN. The outline is the
link silhouette; then the two clearance cylinders that own the straddle are
subtracted - wr_sweep_r about J4, where the roll housing swings, and
fa_elbow_clear about J3, where the upper arm continues through - and then
everything below fa_duct_z, which is the cable duct. What survives is the
top rail. Drawing that outline by hand would be a guess that goes stale the
moment either neighbour changes size; cutting it cannot.

THE SEAM. Two M3 per end, self-tapping into ONE THROUGH bore each. Blind
pilots drilled from each end would each roof themselves - a small ceiling,
but this piece's whole claim is that it is a prism with nothing over 50
degrees anywhere in it, and a blind hole is the one thing that would spoil
it. A through bore keeps the claim exactly true, and the two screws still
engage fa_seam_engage each with untapped bore left between them. The stations
are solved in forearm.py by lib/forearm_split.Seam - the rail's length at the
screw height comes from those same two sweep circles, and it is what decides
whether two screws fit at all.

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

from lib.forearm_split import Silhouette, Straddle  # noqa: E402
from lib.palette import hints_for  # noqa: E402

COMPONENT = 'robotarm_forearm_rail'
BODY_NAME = 'forearm_rail'
PREFIX = 'fr_'
FOREARM = 'fa_'
WRIST = 'wr_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('forearm')

PH_FORM = 'rail form'
PH_CLEAR = 'joint clearance'
PH_SEAM = 'plate seam'
PHASES = [PH_FORM, PH_CLEAR, PH_SEAM]

EPS = 1e-9
EPS_MM = 1e-6
# How many stations across the rail are checked for a single connected run.
# A COUNT, not a dimension - see lib/forearm_split.PROBE_N, which this
# mirrors for the same reason.
PROBE_N = 100


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
            'fa_%s is not in this document. forearm_rail is one PIECE of a '
            'split part - build forearm.py first, in the same document, so '
            'the interface is read rather than guessed' % name)
        return p.value

    def wr(name):
        p = ups.itemByName(WRIST + name)
        assert p is not None, (
            'wr_%s is not in this document - build forearm.py first' % name)
        return p.value

    L2 = fa('l2')

    param('half_x', FOREARM + 'plate_in',
          'HALF THE RAIL LENGTH, and the mating face at each end. It is\n'
          '           fa_plate_in on both sides because that is where the straddle\n'
          '           starts - the rail runs the full width between the two plates\n'
          '           and lands on the inner face of each.')
    param('floor', FOREARM + 'duct_z',
          'the rail\'s inner face = the cable duct\'s half height. DERIVED in\n'
          '           forearm.py from the seam fastener that has to live above it,\n'
          '           not typed: the pilot needs half a bore and one wall of floor\n'
          '           under it, and what is left below is the duct.')
    param('height', FOREARM + 'waist_z - ' + PREFIX + 'floor',
          'derived rail height at the waist - what is left of the link outline\n'
          '           above the duct. 6.00, against the 3.00 the one-piece part had,\n'
          '           so the beam is stiffer than it was as well as printable.')
    param('pilot_d', FOREARM + 'seam_pilot_d',
          'fa_seam_pilot_d - the M3 self-tapping pilot, bored THROUGH. Two\n'
          '           screws enter from opposite ends and tap their own thread; the\n'
          '           plates carry clearance holes, so tightening pulls the faces\n'
          '           together instead of jacking them apart on a shared thread.')
    param('relief', FOREARM + 'boss_r + ' + FOREARM + 'wall',
          'how far past the outline the clearance cuts reach, so that no cut\n'
          '           face lands exactly ON the outline - two surfaces meeting on a\n'
          '           tangent are the non-manifold edge fa_lobe_over exists to avoid,\n'
          '           one dimension down.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- the shared solves, before any geometry ----------------------------
    SIL = Silhouette(l2=L2 * 10, boss_r=fa('boss_r') * 10,
                     waist_z=fa('waist_z') * 10)
    _bad = SIL.validate()
    assert not _bad, 'the link outline is not buildable: ' + '; '.join(_bad)
    STR = Straddle(l2=L2 * 10, sweep_r=wr('sweep_r') * 10,
                   elbow_clear=fa('elbow_clear') * 10)
    _bad = STR.validate()
    assert not _bad, 'the straddle leaves no web: ' + '; '.join(_bad)

    # THE RAIL HAS TO BE ONE CONNECTED RUN, and it is not obvious that it is:
    # it is what two circles leave behind, and if they ever overlap at the
    # duct floor the rail arrives in two pieces - or none. Checked at the
    # floor, which is the narrowest station, because both circles are widest
    # at low |z|.
    y_lo, y_hi = STR.rail_span(val('floor') * 10)
    assert y_hi > y_lo, (
        'the J4 sweep and the J3 sweep overlap at the duct floor z %.2f - '
        'there is no rail at all. fa_duct_z has to come up, or the sweeps '
        'have to come down' % (val('floor') * 10))
    # And it has to be inside the link OUTLINE for its whole length, or the
    # rail stands proud of the arm's own silhouette.
    for _i in range(PROBE_N + 1):
        _y = y_lo + (y_hi - y_lo) * _i / PROBE_N
        assert SIL.half_z(_y) >= val('floor') * 10 - EPS_MM, (
            'the rail floor is at z %.2f and the link outline is only %.2f '
            'half-tall at y %.2f - the rail would hang below the arm'
            % (val('floor') * 10, SIL.half_z(_y), _y))
    # The seam screws have to be IN the rail, with a wall of floor under them.
    for _ys in (fa('seam_y_a'), fa('seam_y_b')):
        _a, _b = STR.rail_span(fa('seam_z') * 10)
        assert _a + fa('wall') * 10 <= _ys * 10 <= _b - fa('wall') * 10, (
            'the seam pilot at y %.2f is not a wall inside the rail, which '
            'runs y %.2f..%.2f at z %.2f'
            % (_ys * 10, _a, _b, fa('seam_z') * 10))
    assert (fa('seam_z') - val('pilot_d') / 2 - fa('wall')) >= val('floor') - EPS, (
        'a %.2f pilot at z %.2f leaves under a %.2f wall to the duct floor '
        'at %.2f' % (val('pilot_d') * 10, fa('seam_z') * 10,
                     fa('wall') * 10, val('floor') * 10))
    assert fa('seam_engage') * 2 < val('half_x') * 2, (
        'two %.1f deep pilots entering a %.1f rail from each end would meet '
        'in the middle' % (fa('seam_engage') * 10, val('half_x') * 2 * 10))

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
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
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

    # EVERY EXTRUDE IN THIS FILE SPANS THE WHOLE PIECE ALONG X. That is not a
    # coincidence and it is what makes the piece a prism: one start, one
    # distance, used by every feature.
    SPAN0 = '-' + PREFIX + 'half_x'
    SPAND = '2 * ' + PREFIX + 'half_x'

    def yz_circle(name, y_c, z_c, d_cm, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            mpt(sk, 0, y_c, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, SPAN0, SPAND, name)

    def yz_rect(name, y0, y1, z0, z1, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, 0, y0, z0), mpt(sk, 0, y1, z1))
        return extrude(profiles(sk, expected=1), op, SPAN0, SPAND, name)

    def link_profile(name, y_a, y_b, r_end, r_fil, op):
        """The connecting-rod outline. Shape from lib/forearm_split; this is
        the Fusion plumbing that draws it."""
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
        return extrude(profiles(sk, expected=1), op, SPAN0, SPAND, name), waist

    # ---- phase 1: rail form -------------------------------------------------
    t0 = design.timeline.count
    _, waist_z = link_profile('outline', 0.0, -L2, fa('boss_r'),
                              SIL.arc_r / 10, NEW)
    assert abs(waist_z * 10 - SIL.waist_z) < EPS_MM, (
        'link_profile drew a %.4f waist and lib/forearm_split solves %.4f'
        % (waist_z * 10, SIL.waist_z))
    group(t0, PH_FORM)

    # ---- phase 2: joint clearance -------------------------------------------
    t1 = design.timeline.count
    # THE CLEARANCE IS CUT, NOT DRAWN. Two cylinders - wr_sweep_r about J4 and
    # fa_elbow_clear about J3 - plus everything behind the elbow, because the
    # upper arm does not just swing about J3, it CONTINUES through it. Then
    # everything below the duct floor, which leaves the top rail.
    yz_circle('sweep_j4', 0.0, 0.0, 2 * wr('sweep_r'), CUT)
    yz_circle('sweep_j3', -L2, 0.0, 2 * fa('elbow_clear'), CUT)
    yz_rect('behind_j3', -L2 - val('relief'), -L2,
            -val('relief'), val('relief'), CUT)
    # THE DUCT, AND IT IS WHAT MAKES THIS THE TOP RAIL. Cutting everything
    # below fa_duct_z leaves one of the two; the other is this same solid
    # turned 180 degrees about Y, which is why there is no second file.
    yz_rect('below_duct', -L2 - val('relief'), val('relief'),
            -val('relief'), val('floor'), CUT)
    group(t1, PH_CLEAR)

    # ---- phase 3: the plate seam --------------------------------------------
    t2 = design.timeline.count
    # THROUGH bores, not blind pockets - see the docstring. Self-tapped
    # fa_seam_engage deep from each end by the screws that pull the plates on.
    for tag, ys in (('a', fa('seam_y_a')), ('b', fa('seam_y_b'))):
        yz_circle('seam_pilot_' + tag, ys, fa('seam_z'), val('pilot_d'), CUT)
    group(t2, PH_SEAM)

    # ---- identity, the prism rule, diagnostics ------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - the two sweep cuts have broken the rail '
        'into pieces, which means fa_duct_z is below where they cross'
        % comp.bRepBodies.count)
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
    # THE PRISM RULE. The piece must run the FULL straddle and no further -
    # it lands on both plates - and it must be symmetric about x = 0, which
    # is what makes the second copy a rotation rather than a mirror.
    assert abs(bb.minPoint.x + val('half_x')) < val('tol'), (
        'the rail starts at x %.3f and the plate it lands on is at %.3f'
        % (bb.minPoint.x * 10, -val('half_x') * 10))
    assert abs(bb.maxPoint.x - val('half_x')) < val('tol'), (
        'the rail ends at x %.3f and the plate it lands on is at %.3f'
        % (bb.maxPoint.x * 10, val('half_x') * 10))
    assert abs(bb.minPoint.x + bb.maxPoint.x) < val('tol'), (
        'the rail is not symmetric about x = 0, so the bottom copy is a '
        'MIRROR of this one and not a 180 degree turn - it needs its own '
        'part file, and this one is wrong about what it is')
    assert bb.minPoint.z >= val('floor') - val('tol'), (
        'the rail reaches down to z %.3f, below its own duct floor at %.3f'
        % (bb.minPoint.z * 10, val('floor') * 10))

    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used_appearance))
    print('PIECE 3 of 3: the box-beam rail. PRINT TWO - the second copy is '
          'this solid turned 180 deg about Y, NOT a mirror')
    print('print: either end face on the bed, built along X. A PRISM - zero '
          'overhang, no bridge. Small footprint on a %.1f mm part: use a brim'
          % (val('half_x') * 2 * 10))
    print('rail: y %.2f..%.2f at the duct floor z %.2f, %.2f tall to the link '
          'outline, %.2f long between the plates'
          % (y_lo, y_hi, val('floor') * 10, val('height') * 10,
             val('half_x') * 2 * 10))
    print('   cut from the outline by wr_sweep_r %.2f about J4 and '
          'fa_elbow_clear %.2f about J3 - never drawn'
          % (wr('sweep_r') * 10, fa('elbow_clear') * 10))
    print('seam: 2 x %.2f THROUGH pilots at y %.2f / %.2f, z %.2f; %.1f of '
          'self-tap engagement from each end, %.2f of untapped bore between'
          % (val('pilot_d') * 10, fa('seam_y_a') * 10, fa('seam_y_b') * 10,
             fa('seam_z') * 10, fa('seam_engage') * 10,
             (val('half_x') * 2 - fa('seam_engage') * 2) * 10))
    print('duct left for the loom: %.1f wide x %.1f tall between the plates'
          % (val('half_x') * 2 * 10, val('floor') * 2 * 10))
    print('bbox x %.2f..%.2f | y %.2f..%.2f | z %.2f..%.2f | volume %.1f mm3 '
          '| mass %.2f g EACH | valid %s'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10,
             bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10,
             body.physicalProperties.volume * 1000,
             body.physicalProperties.mass * 1000, body.isValid))
