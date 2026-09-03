"""robotarm/forearm_px - Fusion MCP generating script.

Rebuilds `robotarm_forearm_px` (idempotent). Spec: specs/robotarm/forearm.md
for the joint contract and specs/robotarm/_forearm_print.md for the split;
styled per specs/robotarm/_style.md.

THE +X SIDE PLATE OF THE FOREARM. One of the three pieces the forearm now
prints as - this, forearm_nx, and two copies of forearm_rail. forearm.py
still builds the assembled reference and still declares every fa_*
parameter; this file reads that contract and cuts one plate from it.

WHAT IS ON THIS SIDE. The J4 pitch journal and its flange counterbore; the
608ZZ pocket that carries the elbow IDLER side; the servo seat; and the J4
servo lobe with its two-step case window, flange recess, lead keyway and tab
pilots. The J3 drive bore and the J3 standoff are on the other plate.

PRINT ORIENTATION: INNER FACE DOWN - the split plane, x = fa_plate_in, on the
bed, built along +X. That is the whole reason the part was split, so it is
worth stating why rather than asserting it.

A side plate is a horizontal SLAB when it is built along X. A slab prints
perfectly when it is the FIRST LAYER and impossibly when it is not, and in
the one-piece forearm it was not: its inner face floated 43 mm up over the
straddle on nothing but the rails, 918 mm2 of it, in a volume that has to
stay empty because the roll housing swings through it. Split the plate off at
its own inner face and that same face becomes 1030 mm2 of first layer.

EVERYTHING ELSE THEN FALLS THE RIGHT WAY UP, which is the part that is easy
to miss. Outboard of the plate, every feature is NARROWER than the plate and
lands on it: boss, seat, lobe. Every pocket that was a roof now opens at the
top of the build - the flange counterbore, the case window, the flange
recess, the tab pilots, the lead keyway. All four journal bores stay VERTICAL
and round, which was the reason the one-piece part was built along X in the
first place and is the one thing the split must not give up.

NOTHING MAY LIE INBOARD OF THE BED FACE. That is the single rule this piece
has to obey and it is asserted against the built body's bounding box at the
end of this file, not trusted. It is also why the rails are not here: they
cross the straddle, and "across the straddle" is "below the bed".

WHAT STILL NEEDS SUPPORT, HONESTLY. 390 mm2, in three places, none of it
structural and none of it inside the straddle:

  231 mm2  the 608ZZ pocket roof - a 4.49 mm annular LEDGE under a 0.50 mm
           shoulder. This is the one item that neither the split nor any
           orientation fixes. It would go if the pocket were cut from the
           OUTER face instead, and that flips which side of the inner race
           the shoulder bears on - a contract j3_axle.py and _check_elbow.py
           own, not this file.
  121 mm2  the J4 flange counterbore, roofed by the lobe above it. A BRIDGE,
           not a ledge: it spans 24.35 mm against design_rules
           MAX_BRIDGE_MM 40.0, and fa_cbore_extra leaves 0.50 mm of designed
           clearance under it, so sag there touches nothing.
   38 mm2  the ledge where the lobe oversails the seat by one fa_wall. 1.60
           mm wide, one nozzle line; it is the price of keeping the seat
           clear of the corner edges the fillet has to run along.

THE INTERFACE IS THE FOREARM'S AND IT IS REQUIRED, NOT DEFAULTED. Every fa_*
this file reads is asserted present. A plate that quietly built itself to its
own idea of the interface would fit nothing and print beautifully doing it -
which is the failure mode this project has already had on shaft_from_end, on
the lead datum and on sb_arm_l1.

The SHARED derivations - the link outline, the servo block placement - come
from lib/forearm_split.py, the same objects forearm.py and forearm_nx.py
use. A silhouette that three files each solve for themselves is the
datum-only-one-file-reads failure with the serial numbers filed off.

A NOTE ON ONE WORD. Like forearm.py, this docstring avoids the word
tests/test_fusion_scripts.py scans for - the one naming a script that places
an imported mesh or a measured transform. Carrying it SKIPS the magic-number
and entity-naming lints for the whole file, silently and with a green run to
show for it. j3_servo_cap.py carries it by accident today, in a sentence
about hex-key clearance, and has been unlinted ever since.
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

COMPONENT = 'robotarm_forearm_px'
BODY_NAME = 'forearm_px'
PREFIX = 'fp_'
FOREARM = 'fa_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('forearm')

PH_FORM = 'plate form'
PH_PIVOT = 'pivot journals'
PH_DRIVE = 'J4 servo lobe'
PH_SEAM = 'rail seam'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_PIVOT, PH_DRIVE, PH_SEAM, PH_FINISH]

# Float slack, and neither is a dimension: these are tolerances on a float
# COMPARISON, not on the part, so they live up here where they read as what
# they are. EPS is against internal (cm) values, EPS_MM against values
# already scaled to mm for a message.
EPS = 1e-9
EPS_MM = 1e-6
# Probe hooks, matching forearm.py's: a bench script sets these False to
# build the plain body and try radii against it.
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

    # ---- THE FOREARM'S CONTRACT, READ AND REQUIRED -------------------------
    # Returned in cm, which is Fusion's internal unit and what every sketch
    # coordinate below is in. Messages scale by 10 to talk in mm.
    def fa(name):
        p = ups.itemByName(FOREARM + name)
        assert p is not None, (
            'fa_%s is not in this document. forearm_px is one PIECE of a '
            'split part - build forearm.py first, in the same document, so '
            'the interface is read rather than guessed' % name)
        return p.value

    L2 = fa('l2')

    # ---- this piece's own datums -------------------------------------------
    param('split', FOREARM + 'plate_in',
          'THE SPLIT PLANE, AND THE BED FACE. The plate is cut off the arm\n'
          '           here and printed with this face down, so this one number is\n'
          '           both the joint and the print orientation. It is fa_plate_in\n'
          '           because that is where the straddle starts: everything inboard\n'
          '           of it is running clearance for the roll housing and belongs to\n'
          '           no piece at all.')
    param('reach', FOREARM + 'plate_out + ' + FOREARM + 'j4_lobe_t - '
          + PREFIX + 'split',
          'derived build height: bed face to the J4 TAB PLANE, which is the\n'
          '           outermost thing on this piece. 13.50 mm, against 56.50 for the\n'
          '           one-piece part - and short parts do not need a brim.')
    param('facet', FOREARM + 'facet',
          'fa_facet - the plate outline chamfer, a PROBED ceiling on the\n'
          '           one-piece part and unchanged here because it bevels the same\n'
          '           7.50 plate against the same boss circles.')
    param('lobe_radius', FOREARM + 'lobe_radius_j4',
          'fa_lobe_radius_j4 - a CEILING, not a preference: the flange recess\n'
          '           set it, and the corner it rounds is unchanged by the split.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- the shared solves, before any geometry ----------------------------
    SIL = Silhouette(l2=L2 * 10, boss_r=fa('boss_r') * 10,
                     waist_z=fa('waist_z') * 10)
    _bad = SIL.validate()
    assert not _bad, 'the link outline is not buildable: ' + '; '.join(_bad)
    BLK = ServoBlock(y_pivot=0.0, run=-1, shaft_end=fa('shaft_end') * 10,
                     case_l=fa('case_l') * 10, tab_pitch=fa('tab_pitch') * 10,
                     lobe_pad=fa('lobe_pad') * 10)
    _bad = BLK.validate()
    assert not _bad, 'the J4 servo block does not place: ' + '; '.join(_bad)

    case_lo, case_hi = (v / 10 for v in BLK.case)
    case_mid = (case_lo + case_hi) / 2
    lobe_lo, lobe_hi = (v / 10 for v in BLK.span)
    seat_hi = min(lobe_hi, fa('seat_y_max'))
    assert seat_hi > lobe_lo, (
        'fa_seat_y_max %.2f has cut the seat away entirely against a block '
        'starting at %.2f' % (fa('seat_y_max') * 10, lobe_lo * 10))
    # The seat has to stay inside the link outline or it stands proud of the
    # part and the finish phase has two outlines to chase. Probed across the
    # WHOLE span, not at its ends: the concave waist arc is thinnest in the
    # middle, so two end checks would pass a seat that breaks out between
    # them. lib/forearm_split owns the probe as well as the outline.
    assert SIL.contains_band(lobe_lo * 10, seat_hi * 10, fa('seat_z') * 10), (
        'the seat is %.2f half-tall over y %.2f..%.2f and the link outline '
        'is thinner than that somewhere in that span'
        % (fa('seat_z') * 10, lobe_lo * 10, seat_hi * 10))
    # The seam screws land on the WAIST's outer face, and this piece is the
    # half that has to have a waist there at all.
    for _ys in (fa('seam_y_a'), fa('seam_y_b')):
        _half = SIL.half_z(_ys * 10)
        assert _half >= (fa('seam_z') + fa('seam_clear_d') / 2) * 10, (
            'the seam hole at y %.2f needs %.2f of outline and there is %.2f'
            % (_ys * 10, (fa('seam_z') + fa('seam_clear_d') / 2) * 10, _half))

    # ---- idempotent rebuild -------------------------------------------------
    # RENAME FIRST, THEN DELETE - deleting a component's last occurrence
    # orphans the component, which then still holds its name and cannot be
    # renamed. See fusion/PLAYBOOK.md.
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
            # Without this a CUT eats every other component in the document.
            # See fusion/PLAYBOOK.md.
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
        """Cylinder on an axis parallel to X - every pivot here is one, and
        in this orientation every one of them is VERTICAL."""
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
        """The connecting-rod outline: a circle at each pivot joined by two
        concave arcs tangent to both.

        The SHAPE is solved in lib/forearm_split.Silhouette; this is the
        Fusion plumbing that draws it, and it is the only part of the
        outline that is repeated between the two plate scripts - because a
        sketch cannot live in a module that does not import Fusion.
        """
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
        """Edges running along X at one (y, z) corner, at least min_len long."""
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

    # ---- phase 1: plate form ------------------------------------------------
    t0 = design.timeline.count
    # THE WAIST WALL FIRST, and it is the FULL outline. Between the bosses the
    # plate is only fa_waist_t thick - that is the single biggest lever on the
    # mass of the link and it is not going up - so the outline is extruded
    # thin here and the bosses stand proud of it below.
    _, waist_z = link_profile('waist', 0.0, -L2, fa('boss_r'), SIL.arc_r / 10,
                              PREFIX + 'split', FOREARM + 'waist_t', NEW)
    assert abs(waist_z * 10 - SIL.waist_z) < EPS_MM, (
        'link_profile drew a %.4f waist and lib/forearm_split solves %.4f'
        % (waist_z * 10, SIL.waist_z))
    for y_p, jnt in ((0.0, 'j4'), (-L2, 'j3')):
        yz_circle('boss_' + jnt, y_p, 0.0, 2 * fa('boss_r'),
                  PREFIX + 'split',
                  FOREARM + 'plate_out - ' + PREFIX + 'split', JOIN)
    # THE SERVO SEAT: the plate at FULL thickness under the servo block. In
    # the one-piece part this filled 3.00 mm of air the lobe was bridging;
    # here it does that AND carries the lobe down onto the first layer.
    yz_rect('seat_j4', lobe_lo, seat_hi, -fa('seat_z'), fa('seat_z'),
            FOREARM + 'plate_out - ' + FOREARM + 'lobe_seat',
            FOREARM + 'lobe_seat', JOIN)
    # ONE BLOCK from inside the plate out to the tab plane. Phase 3 opens it
    # in two steps; it is cut in one piece because a lobe drawn in two pieces
    # is a lobe with a seam in it where the fillet has to run.
    yz_rect('lobe_j4', lobe_lo, lobe_hi, -fa('lobe_z'), fa('lobe_z'),
            FOREARM + 'plate_out - ' + FOREARM + 'lobe_over',
            FOREARM + 'j4_lobe_t + ' + FOREARM + 'lobe_over', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: pivot journals --------------------------------------------
    t1 = design.timeline.count
    # ALL FOUR OF THESE ARE VERTICAL IN THIS ORIENTATION and that is the
    # constraint the whole split had to protect. They are the only precision
    # fits in the piece.
    yz_circle('bore_j4', 0.0, 0.0, fa('bore_d'), PREFIX + 'split',
              FOREARM + 'plate_out - ' + PREFIX + 'split', CUT)
    # The flange counterbore is deeper than the flange so the flange NEVER
    # seats - the hex bottoming in its socket locates the joint axially, and
    # two hard stops on one axis fight each other. Cut from the OUTER face,
    # so in this orientation it opens at the TOP of the build.
    yz_circle('cbore_j4', 0.0, 0.0, fa('cbore_d'),
              FOREARM + 'plate_out - ' + FOREARM + 'cbore_depth',
              FOREARM + 'cbore_depth', CUT)
    # J3 IDLER SIDE: a 608ZZ, not a printed journal. The mesh loads this axis
    # radially and slop here is backlash at the tooth, which is the one thing
    # a 2:1 cannot fix. Pocketed from the INNER face and retained by what is
    # left of the plate outboard of it - a shoulder whose bore must clear the
    # INNER race or this stationary plate rubs it and locks the joint.
    #
    # AND IT IS THIS PIECE'S ONE REMAINING SUPPORT PROBLEM. The inner face is
    # the bed, so the pocket opens onto the bed and its 0.50 mm shoulder
    # roofs it: a 4.49 mm annular LEDGE, 231 mm2, which no orientation of
    # this piece fixes. Cutting it from the outer face instead would open it
    # to the sky - and would move the shoulder to the other side of the inner
    # race, which is j3_axle.py's and _check_elbow.py's contract, not this
    # file's. See specs/robotarm/_forearm_print.md.
    yz_circle('brg_bore_j3', -L2, 0.0, fa('brg_bore'), PREFIX + 'split',
              FOREARM + 'plate_out - ' + PREFIX + 'split', CUT)
    yz_circle('brg_pocket_j3', -L2, 0.0, fa('brg_pocket_d'),
              PREFIX + 'split', FOREARM + 'brg_w', CUT)
    group(t1, PH_PIVOT)

    # ---- phase 3: the J4 servo lobe -----------------------------------------
    t2 = design.timeline.count
    # TWO CUTS, NOT ONE, AND AN MG90S IS WHY. Reading up from its case top
    # there are fa_tab_below_top of bare case and then fa_tab_thk of mounting
    # FLANGE, and that flange is fa_tab_span long against a much shorter
    # case. A single window sized for the case lands the flange on solid
    # lobe. GATE servo_fit MEASURED that collision - 195.75 mm3 of MG90S
    # inside the host, in the flange band and nowhere else. So the case
    # window is cut for the case alone and a FLANGE RECESS takes the last
    # fa_tab_thk out to the tab plane. specs/robotarm/_flange.md.
    #
    # AND IN THIS ORIENTATION THE STEP IS NOT A ROOF. Built along +X both
    # bands open UPWARD and the recess is the WIDER of the two, so the step
    # between them is the upward-facing ledge the tabs bed on. Measured
    # ceiling at the recess floor and at the pilot tops: 0.00 mm2.
    win0 = FOREARM + 'plate_out'
    wind = FOREARM + 'j4_lobe_t - ' + FOREARM + 'tab_thk'
    rec0 = (FOREARM + 'plate_out + ' + FOREARM + 'j4_lobe_t - '
            + FOREARM + 'tab_thk')
    pil0 = rec0 + ' - ' + FOREARM + 'pilot_depth'
    yz_rect('window_j4',
            case_lo - fa('srv_clear') / 2, case_hi + fa('srv_clear') / 2,
            -fa('win_z') / 2, fa('win_z') / 2, win0, wind, CUT)
    yz_rect('flange_recess_j4',
            case_mid - fa('recess_l') / 2, case_mid + fa('recess_l') / 2,
            -fa('win_z') / 2, fa('win_z') / 2,
            rec0, FOREARM + 'tab_thk', CUT)
    # LEAD KEYWAY: ONE notch, centred across the width, cut into the END wall
    # at the shaft end and running OUTWARD to daylight. The bundle leaves the
    # case's short END face - lib/servo.py's lead datum - and the whole case
    # travels this window during assembly, so the cable has to traverse it
    # too. Cut through BOTH bands: a keyway stopping at the recess floor
    # would walk the cable into the recess end wall instead of the window's.
    near_y = BLK.near_face / 10
    k_a, k_b = sorted((near_y, near_y + fa('lead_key_l')))
    yz_rect('lead_key_j4', k_a, k_b,
            -fa('lead_key_d') / 2, fa('lead_key_d') / 2,
            FOREARM + 'plate_out', FOREARM + 'j4_lobe_t', CUT)
    # THE PILOTS START AT THE RECESS FLOOR, not at the outer face: that is
    # where the screw finds material, and drilling from the old station would
    # put the hole fa_tab_thk deeper into the part.
    for i, ys in enumerate(v / 10 for v in BLK.screws):
        yz_circle('pilot_j4_%d' % i, ys, 0.0, fa('pilot_d'),
                  pil0, FOREARM + 'pilot_depth', CUT)
    group(t2, PH_DRIVE)

    # ---- phase 4: the rail seam ---------------------------------------------
    t3 = design.timeline.count
    # FOUR CLEARANCE HOLES THROUGH THE WAIST, one per rail end. The screw is
    # a CLEARANCE fit here and self-taps in the rail, so tightening pulls the
    # two faces together instead of jacking them apart on a shared thread.
    # The head lands on the waist's outer face and stands in the empty band
    # out to fa_plate_out, where the lobe does not reach at this height and
    # nothing sweeps - fa_seam_z is derived to keep it inside the outline.
    for tag, ys in (('a', fa('seam_y_a')), ('b', fa('seam_y_b'))):
        for sz, zt in ((+1, 'p'), (-1, 'm')):
            yz_circle('seam_clear_%s%s' % (tag, zt), ys, sz * fa('seam_z'),
                      fa('seam_clear_d'), PREFIX + 'split',
                      FOREARM + 'waist_t', CUT)
    group(t3, PH_SEAM)

    # ---- phase 5: finish ----------------------------------------------------
    t4 = design.timeline.count
    n_fillet, skipped, buried = 0, 0, 0
    col = adsk.core.ObjectCollection.create()
    for y_c in (lobe_lo, lobe_hi):
        for z_c in (-fa('lobe_z'), fa('lobe_z')):
            # A CORNER INSIDE A PIVOT BOSS IS NOT A CORNER. Where the block
            # runs into the boss the two merge and there is nothing coherent
            # to blend - Fusion says ASM_INCONS_FACE at every radius.
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
        fil.add(f_inp).name = 'lobe_corners_j4'
        n_fillet = col.count
    # POLYGONAL: facet the OUTLINE of the plate's outer face. The face carries
    # several closed curves - the boss circle, the journal counterbore, the
    # lobe blends - and only the outline reaches the body's z extreme at
    # +/- fa_boss_r. Select on that and the counterbore is never touched.
    n_face = 0
    if FACET:
        fcol = adsk.core.ObjectCollection.create()
        x_pick = fa('plate_out')
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
        assert n_circ == 1, (
            'expected exactly one closed boss circle on the plate outer face, '
            'found %d - the selection is picking up a counterbore' % n_circ)
        assert fcol.count - n_circ >= 1, 'no silhouette arc on the outer face'
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            fcol, V(PREFIX + 'facet'), False)
        chf.add(c_inp).name = 'plate_facet'
        n_face = fcol.count
    group(t4, PH_FINISH)

    # ---- identity, the bed-face rule, diagnostics ---------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - the seat or the lobe is not reaching the '
        'plate' % comp.bRepBodies.count)
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

    # THE ONE RULE THIS PIECE HAS TO OBEY, ASSERTED AND NOT TRUSTED. It
    # prints inner-face-down; anything inboard of that face is below the bed
    # and cannot print at all. This is the check that would have caught the
    # rails being left on the plate.
    bb = body.boundingBox
    assert bb.minPoint.x >= val('split') - val('tol'), (
        'the piece reaches x %.3f, inboard of its own bed face at %.3f - '
        'anything below the bed cannot print, and the rails are a separate '
        'piece for exactly this reason'
        % (bb.minPoint.x * 10, val('split') * 10))
    assert bb.maxPoint.x <= (fa('plate_out') + fa('j4_lobe_t')) * (1 + EPS) \
        + val('tol'), (
        'the piece reaches x %.3f, outboard of the J4 tab plane at %.3f - '
        'that plane is _check_leads MOUNTS\' shaft station and nothing may '
        'stand past it'
        % (bb.maxPoint.x * 10, (fa('plate_out') + fa('j4_lobe_t')) * 10))

    print('body: %r | material: %s | appearance: %s'
          % (body.name, body.material.name, used_appearance))
    print('PIECE 1 of 3: the +X side plate. forearm_nx and 2 x forearm_rail '
          'complete the forearm; forearm.py is the assembled reference')
    print('print: INNER FACE DOWN, x %.2f on the bed, built along +X - %.2f mm '
          'tall, all four bores VERTICAL'
          % (val('split') * 10, val('reach') * 10))
    print('plate: waist %.1f thick over the link outline, bosses r %.2f to '
          'x %.2f' % (fa('waist_t') * 10, fa('boss_r') * 10,
                      fa('plate_out') * 10))
    print('J4: bore %.2f, flange counterbore %.2f x %.1f deep (opens UP)'
          % (fa('bore_d') * 10, fa('cbore_d') * 10, fa('cbore_depth') * 10))
    print('J3 idler: 608ZZ pocket %.2f x %.1f deep from the bed face, %.2f '
          'shoulder - the one LEDGE left on this piece, 4.49 mm wide'
          % (fa('brg_pocket_d') * 10, fa('brg_w') * 10,
             fa('brg_shoulder') * 10))
    print('J4 lobe: y %.2f..%.2f, seat to y %.2f, window then flange recess, '
          '%d tab pilots' % (lobe_lo * 10, lobe_hi * 10, seat_hi * 10,
                             len(BLK.screws)))
    print('seam: 4 x %.2f clearance at y %.2f / %.2f, z +/-%.2f'
          % (fa('seam_clear_d') * 10, fa('seam_y_a') * 10,
             fa('seam_y_b') * 10, fa('seam_z') * 10))
    print('finish: %d lobe corner edges at r %.2f (%d too short, %d inside a '
          'boss), %d outline edges faceted at %.2f'
          % (n_fillet, val('lobe_radius') * 10, skipped, buried, n_face,
             val('facet') * 10))
    print('bbox x %.2f..%.2f | y %.2f..%.2f | z %.2f..%.2f | volume %.1f mm3 '
          '| mass %.2f g | valid %s'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10,
             bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10,
             body.physicalProperties.volume * 1000,
             body.physicalProperties.mass * 1000, body.isValid))
