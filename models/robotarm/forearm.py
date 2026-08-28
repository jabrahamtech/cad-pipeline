"""robotarm/forearm - Fusion MCP generating script.

Rebuilds `robotarm_forearm` (idempotent). Spec: specs/robotarm/forearm.md,
styled per specs/robotarm/_style.md.

L2 = 40 mm of link carrying BOTH wrist servos and forking at BOTH ends.

Local frame: origin on the J4 PITCH axis. +X along that axis, +Y forward
toward the hand, +Z up. The J3 elbow axis is at y = -fa_l2.

WHY IT FORKS AT BOTH ENDS. The first layout had the forearm straddled at
the elbow and forking at the wrist. It cannot be built. Material inside the
straddle has to clear the roll housing's 26 mm sweep about J4, so it can
only live at y < -26; material outboard has to clear the upper arm's own
prongs, so it can only live at y > -25.8. The two regions do not touch, and
nothing at 12.0 < |x| < 12.4 can bridge them without eating the running
clearance. Fork at both ends and the side walls run unbroken from pivot to
pivot, which is what this part is: two walls and a web.

THE CLEARANCE IS CUT, NOT DRAWN. Two cylinders - wr_sweep_r about J4 and
fa_elbow_clear about J3 - are subtracted from everything inside the
straddle. The web that survives is an hourglass, narrow on the arm's
centreline where the two swings nearly meet and wide above and below where
they do not. Drawing that outline by hand would be a guess that goes stale
the moment either neighbour changes size; cutting it cannot.

BOTH wrist servos hang off this part, staggered: J4's on +X, J3's on -X.
That is forced, not chosen. An MG90S is 24.0 mm along its own shaft axis,
so a servo driving a joint whose axis is X occupies 24 mm of X. Inboard is
the straddle and it is spoken for, so the servo goes outboard. Hiding it in
the link behind a 1:1 gear pair was priced and rejected: the case would
have had to start 28.6 mm behind the pitch axis and end 12.6 mm PAST the
elbow.

Print orientation: -X face down, built along +X, so all four journal bores
are vertical and round - they are the only precision fits in the part. This
does need support under the +X wall and the two lobes; nothing about a
fork of two servo mounts is support-free in any orientation, and a sagging
20 mm journal is the worse trade. Split the part on the XZ plane if the
scarring matters.

The SHARED wr_* block is defined identically in wrist_hub.py and
wrist_roll.py. MG90S dimensions are DATASHEET (lib/servo.py) - the tab
plane is the datum, the case pocket is only clearance.
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

from lib.servo import CATALOG  # noqa: E402 - MEASURED lead bundle

COMPONENT = 'robotarm_forearm'
BODY_NAME = 'forearm'
PREFIX = 'fa_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'link form'
PH_CLEAR = 'joint clearance'
PH_PIVOT = 'pivot journals'
PH_DRIVE = 'servo lobes'
PH_CABLE = 'cable route'
PH_FINISH = 'finish'

# Probe hook: _probe_forearm_facet.py sets this False to build the plain body
# and then try chamfer sizes against it. Nothing else touches it.
FACET = True
PHASES = [PH_FORM, PH_CLEAR, PH_PIVOT, PH_DRIVE, PH_CABLE, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A link is light; the joints are dark.
APPEARANCE_HINTS = [('plastic', 'yellow'), ('paint', 'yellow'), ('yellow',), ('plastic',)]


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

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    # --- SHARED joint contract ----------------------------------------------
    wrist('pivot_af', '16.0 mm',
          'J4 hex socket across flats - SHARED, defined identically in\n'
          '           wrist_roll.py and wrist_hub.py')
    wrist('straddle', '24.0 mm',
          'the width this fork straddles - SHARED, see wrist_roll.py')
    wrist('sweep_r', '25.4 mm',
          'the radius the roll housing sweeps about J4 - SHARED, see wrist_roll.py')
    wrist('hub_d', '20.0 mm', 'hub journal collar diameter - SHARED, see wrist_hub.py')
    wrist('journal', '5.0 mm', 'collar length = the bore depth it runs in')
    wrist('flange_d', '24.0 mm', 'hub retaining flange diameter')
    wrist('flange_t', '2.0 mm', 'hub retaining flange thickness')
    wrist('reach', '3.8 mm', 'hex boss length past this plate - SHARED, see wrist_hub.py')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'silhouette corner radius - _style.md rule 2')

    # --- fits ----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('rot', '0.35 mm', 'rotating fit - design_rules, every journal here')
    param('free', '0.4 mm', 'free fit - design_rules')

    # --- link ----------------------------------------------------------------
    param('l2', '45.0 mm',
          'J3 to J4. Was 65. Shortened 2026-08-26 to the reference arm\'s\n'
          '           proportions. This is the single highest-leverage number in the\n'
          '           arm: the whole outboard cluster - wrist, both wrist servos, the\n'
          '           effector servo and the head - sits at FIXED offsets from the\n'
          '           wrist end, so shortening L2 translates all of it inboard 1:1.\n'
          '           The head alone is 49 % of the elbow moment. 65 -> 45 takes J3\n'
          '           from 80 % to 61 % of duty. lib/arm_budget.py is the authority.\n'
          '           Cost: working reach 300 -> 260 mm at the jaw faces.')
    param('gap', PREFIX + 'free', 'running gap, plate inner face to the straddled part')
    param('plate_in', WRIST + 'straddle / 2 + ' + PREFIX + 'gap', 'derived plate inner face')
    param('cbore_extra', '0.5 mm',
          'the counterbore is deeper than the flange so the flange NEVER seats: the\n'
          '           hex bottoming in its socket is what locates the joint axially, and\n'
          '           two hard stops on one axis fight each other')
    param('cbore_depth', WRIST + 'flange_t + ' + PREFIX + 'cbore_extra', 'derived')
    param('plate_t', WRIST + 'journal + ' + PREFIX + 'cbore_depth', 'derived plate thickness')
    param('plate_out', PREFIX + 'plate_in + ' + PREFIX + 'plate_t', 'derived plate outer face')
    param('bore_d', WRIST + 'hub_d + ' + PREFIX + 'rot', 'derived journal bore')
    param('cbore_d', WRIST + 'flange_d + ' + PREFIX + 'rot', 'derived flange counterbore')
    param('boss_r', PREFIX + 'cbore_d / 2 + ' + PREFIX + 'wall', 'derived pivot boss radius')
    param('facet', PREFIX + 'plate_t / 5',
          'LOCAL, not sty_facet - _style.md rule 1 says the facet scales with\n'
          '           the volume it bevels, and these are 7.5 mm fork plates, not the\n'
          '           upper arm\'s 24 mm slab. A 4.0 shared facet on a 7.5 plate is not\n'
          '           a facet, it is most of the plate. And redefining sty_facet to\n'
          '           suit this part would silently re-cut every other part in the\n'
          '           document - that is the exact bug _check_ledger.py exists for.\n'
          '           plate_t/5 = 1.50, and 1.50 is a CEILING, not a preference. The\n'
          '           silhouette arc runs tangentially into the boss circles at both\n'
          '           ends and has nowhere to run out; measured by probing the built\n'
          '           body, 2.50 and 2.00 both fail ASM_BL_UNFIN_SHEET and 1.50 is the\n'
          '           largest that computes. Do not raise it without re-probing.')
    param('waist_t', '3.5 mm',
          'wall thickness between the two pivot bosses. The bosses need 7.5 for the\n'
          '           journal + counterbore; the span between them does not, and this is\n'
          '           the single biggest lever on the mass of the part.')
    param('waist_z', '12.0 mm',
          'half height of the link at its narrowest. THIS is the input; the arc\n'
          '           radius that delivers it is derived from it and from fa_l2. Setting\n'
          '           the radius directly worked at L2 = 40 and pinched the link shut at\n'
          '           L2 = 65 - the shape has to follow the length, not fight it.\n'
          '           Was 9.0. Grown to 12.0 with fa_rail_z held, so the duct grows too:\n'
          '           a 28 mm box beam, not a 28 mm slab. arm_budget says up to 4x the\n'
          '           link mass is affordable at L2 = 45; this spends far less than that.')
    param('elbow_clear', '13.4 mm',
          'the radius the UPPER ARM sweeps about J3, plus clearance. Its elbow block\n'
          '           has to hold a 16.0 af hex socket, so 9.24 circumradius + 1.6 wall\n'
          '           + 0.4 = 11.4, but ua_drum_r drives it and that is now 13.0,\n'
          '           so 13.4. The centreline web pays for it: 45 - 25.4 - 13.4 = 6.2. If that block grows, this grows, and the web between\n'
          '           the two joints is what gets eaten.')
    param('rail_z', '3.0 mm',
          'top and bottom rail left when the duct is cut out of the web. The two\n'
          '           side walls plus these two rails make the link a box beam; the slab\n'
          '           that was there instead was 13 g of nothing.')
    param('duct_z', PREFIX + 'waist_z - ' + PREFIX + 'rail_z', 'derived duct half height')

    # --- MG90S, DATASHEET (lib/servo.py) -------------------------------------
    param('case_l', '22.8 mm', 'MG90S case length - lies along Y. 24.0 -> 22.8 on\n           TowerPro B, 2026-08-27 flange audit (lib/servo.py)')
    param('case_w', '12.4 mm', 'MG90S case width - lies along Z. TowerPro D')
    param('shaft_end', '6.0 mm', 'shaft axis to the near end of the case, along Y')
    param('tab_thk', '2.5 mm', 'MG90S tab thickness - ASSUMED micro-family value, the\n           TowerPro table does not give it. Part of the lobe_t datum stack')
    param('tab_below_top', '3.0 mm', 'case top to the tab TOP, along X - DERIVED from\n           TowerPro F 18.5: case_h - F - tab_thk. Was 1.0, which floated the\n           tabs 2.0 too high and sank the case 1.5 too shallow')
    param('tab_pitch', '27.5 mm', 'MG90S tab hole pitch - DERIVED, holes centred in the\n           tab overhang of TowerPro B/E ((22.8+32.1)/2). The 29.0 it replaces\n           came from a drawing TowerPro\'s own table contradicts. CALIPER\n           before printing anything that screws to these tabs')
    param('lobe_t', PREFIX + 'tab_below_top + ' + PREFIX + 'tab_thk',
          'derived lobe thickness: the tabs bear on its outer face and the case top\n'
          '           sits flush with the plate outer face')
    param('lobe_over', '1.0 mm',
          'the lobe starts INSIDE the plate. Two volumes that meet exactly on a plane\n'
          '           are non-manifold and the fillet fails later - see PLAYBOOK.')
    param('lobe_z', PREFIX + 'case_w / 2 + ' + PREFIX + 'wall + 1.0 mm', 'derived lobe half height')
    param('lobe_pad', '3.5 mm', 'material past the outermost tab screw')
    # ---- LEAD KEYWAY -------------------------------------------------------
    # The servo cannot be installed without this. The whole case travels
    # through this window during assembly (the tabs land on the FAR face), so
    # the cable has to traverse it too - and the bundle leaves the SHORT END
    # FACE at the shaft end, dead centre across the width (lib/servo.py lead
    # datum, MEASURED 2026-08-28). Along the length the servo-plus-cable is
    # case_l + bundle = 26.2 against a 23.0 window: it does not go.
    #
    # The first repair notched the two LONG walls either side of that face -
    # right station, wrong walls, and it would have printed. Jonathan, at the
    # bench: "thats not on the right side its on the short side". ONE notch,
    # centred, in the END wall.
    _LEAD = CATALOG['MG90S'].lead_bundle_dia
    param('lead_key_d', '%.2f mm' % (_LEAD + 0.2),
          'keyway WIDTH across the case width, centred on the bundle - one\n'
          '           bundle diameter plus a locational fit')
    param('lead_key_l', '%slobe_pad + (%stab_pitch - %scase_l) / 2 + 1.0 mm'
          % (PREFIX, PREFIX, PREFIX),
          'keyway length OUT from the shaft-end face. DERIVED to reach the\n'
          '           lobe edge plus 1.0 of overshoot: a keyway that stops inside the\n'
          '           lobe is a blind pocket and traps the cable exactly as the solid\n'
          '           wall did. Never hardcode this - it moves with lobe_pad.')
    param('pilot_d', '1.8 mm', 'servo screw pilot - design_rules, self-tapping into PETG')
    param('pilot_depth', '3.5 mm',
          'engagement. Must not break into the flange counterbore behind it - asserted.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
    # RENAME FIRST, THEN DELETE. Deleting a component's LAST occurrence orphans
    # the component: it drops straight out of allComponents while still holding
    # its name, so a rename afterwards cannot reach it and the rebuild is handed
    # 'robotarm_x (1)'. Every lookup by name then misses. See fusion/PLAYBOOK.md.
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
            # Without this a CUT eats every other component in the document.
            # See fusion/PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm, z_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def yz_circle(name, y_c, z_c, d_cm, x0_expr, dx_expr, op):
        """Cylinder on an axis parallel to X. Every pivot in this part is one."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, y_c, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def yz_rect(name, y0, y1, z0, z1, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, 0, y0, z0), mpt(sk, 0, y1, z1))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def arc_radius(l, r_end, waist):
        """Radius of the concave arc tangent to both bosses that leaves exactly
        `waist` of half-height at the middle. From h = r_fil + waist and
        h^2 = (r_fil + r_end)^2 - (l/2)^2."""
        num = r_end ** 2 - (l / 2.0) ** 2 - waist ** 2
        den = 2.0 * (waist - r_end)
        assert abs(den) > 1e-9, 'waist equals the boss radius; the link has no waist'
        return num / den

    def link_profile(name, y_a, y_b, r_end, r_fil, x0_expr, dx_expr, op):
        """The classic connecting-rod outline: a circle at each pivot joined by
        two concave arcs tangent to both. Tangency is what makes it read as one
        shape rather than a strap bolted between two rings, and it is computed,
        not eyeballed - there is no straight edge to get subtly wrong."""
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

    def xz_rect(name, x0, x1, z0, z1, y0_expr, dy_expr, op):
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, 0, z0), mpt(sk, x1, 0, z1))
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    def edge_along_x_at(y_c, z_c):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            b = e.boundingBox
            if (abs(b.minPoint.y - b.maxPoint.y) < val('tol')
                    and abs(b.minPoint.z - b.maxPoint.z) < val('tol')
                    and abs(b.minPoint.y - y_c) < val('tol')
                    and abs(b.minPoint.z - z_c) < val('tol')):
                col.add(e)
        return col

    # ---- the two servo lobes, as data ---------------------------------------
    # (sign of X, pivot y, sign of the case's run along Y). Both cases point
    # INBOARD along the arm so their mass sits between the joints, not past
    # them: J4's runs back from the wrist, J3's runs forward from the elbow.
    L2 = val('l2')
    LOBES = [(+1, 0.0, -1, 'j4'), (-1, -L2, +1, 'j3')]

    def lobe_geometry(y_p, run):
        """Case span, screw positions and lobe outline for one servo, in cm."""
        # The shaft sits shaft_end in from the NEAR end, so the near end is
        # upstream of the pivot and the case runs away from it.
        near = y_p - run * val('shaft_end')
        far = near + run * val('case_l')
        case_y0, case_y1 = min(near, far), max(near, far)
        mid = (case_y0 + case_y1) / 2
        screws = (mid - val('tab_pitch') / 2, mid + val('tab_pitch') / 2)
        pad = val('lobe_pad')
        return (case_y0, case_y1, screws,
                min(screws) - pad, max(screws) + pad)

    # ---- sanity, before any geometry ----------------------------------------
    assert val('boss_r') * 2 < L2, 'the two pivot bosses overlap - L2 is too short'
    web_axis = L2 - wval('sweep_r') - val('elbow_clear')
    assert web_axis >= val('wall'), (
        'the J4 sweep (%.1f) and the J3 sweep (%.1f) leave only %.1f mm of web on the '
        'centreline at L2 = %.1f' % (wval('sweep_r') * 10, val('elbow_clear') * 10,
                                     web_axis * 10, L2 * 10))
    assert val('pilot_depth') <= val('lobe_t') + val('lobe_over'), (
        'the servo pilot holes break through the lobe into the flange counterbore')
    assert wval('reach') > val('gap'), 'the hub hex does not reach across the running gap'
    # The cable leaves the END face, so it steals LENGTH, not width. The
    # superseded form of this assert charged it against case_w and passed
    # happily while the keyway was on the wrong wall entirely.
    _need = CATALOG['MG90S'].case_l + CATALOG['MG90S'].lead_bundle_dia
    _have = val('case_l') * 10 + val('loc') * 10 + val('lead_key_l') * 10
    assert _have >= _need, (
        'the window plus its end keyway passes %.1f mm along the case and the '
        'MG90S with its cable is %.1f mm long at the lead - it cannot be '
        'threaded through' % (_have, _need))
    _to_edge = (val('tab_pitch') - val('case_l')) / 2 + val('lobe_pad')
    assert val('lead_key_l') >= _to_edge, (
        'the keyway runs %.2f mm from the case face but the lobe edge is '
        '%.2f mm away - it would end blind inside the lobe and trap the cable'
        % (val('lead_key_l') * 10, _to_edge * 10))

    def plate(sx):
        """(start expression, distance expression) for one side wall."""
        if sx > 0:
            return PREFIX + 'plate_in', PREFIX + 'plate_t'
        return '-' + PREFIX + 'plate_out', PREFIX + 'plate_t'

    # ---- phase 1: link form ---------------------------------------------------
    t0 = design.timeline.count
    # One profile spans the full straddle AND both waists - the outboard part of
    # it IS the waist. Splitting them would only invite the two to disagree.
    r_fil = arc_radius(L2, val('boss_r'), val('waist_z'))
    assert r_fil > 0, (
        'no concave arc can join bosses of r %.1f over %.1f mm at a %.1f waist - '
        'the link would have to bulge, not pinch'
        % (val('boss_r') * 10, L2 * 10, val('waist_z') * 10))
    _, waist_z = link_profile('web', 0.0, -L2, val('boss_r'), r_fil,
                              '-(' + PREFIX + 'plate_in + ' + PREFIX + 'waist_t)',
                              '2 * (' + PREFIX + 'plate_in + ' + PREFIX + 'waist_t)', NEW)
    # The bosses stand proud of that waist by plate_t - waist_t on each face.
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        for y_p, jnt in ((0.0, 'j4'), (-L2, 'j3')):
            yz_circle('boss_%s_%s' % (jnt, tag), y_p, 0.0,
                      2 * val('boss_r'), x0, dx, JOIN)
    for sx, y_p, run, jnt in LOBES:
        _, _, _, lo, hi = lobe_geometry(y_p, run)
        if sx > 0:
            x0 = PREFIX + 'plate_out - ' + PREFIX + 'lobe_over'
            dx = PREFIX + 'lobe_t + ' + PREFIX + 'lobe_over'
        else:
            x0 = '-(' + PREFIX + 'plate_out + ' + PREFIX + 'lobe_t)'
            dx = PREFIX + 'lobe_t + ' + PREFIX + 'lobe_over'
        yz_rect('lobe_' + jnt, lo, hi, -val('lobe_z'), val('lobe_z'), x0, dx, JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: joint clearance ---------------------------------------------
    # Everything inside the straddle that either neighbour would sweep through.
    # Cut to |x| < plate_in, not straddle/2, or the running gap gets skinned over.
    t1 = design.timeline.count
    inner0 = '-' + PREFIX + 'plate_in'
    inner_d = '2 * ' + PREFIX + 'plate_in'
    for y_p, d, nm in ((0.0, 2 * wval('sweep_r'), 'sweep_j4'),
                       (-L2, 2 * val('elbow_clear'), 'sweep_j3')):
        yz_circle(nm, y_p, 0.0, d, inner0, inner_d, CUT)
    # J4's clearance is a disc because the roll housing only swings; J3's is a
    # disc AND everything behind it, because the upper arm does not just swing
    # about the elbow, it CONTINUES through it. Cutting only the disc left the
    # elbow end webbed across and the fork shut.
    reach_back = val('boss_r') + val('wall')
    yz_rect('behind_j3', -L2 - reach_back, -L2, -reach_back, reach_back,
            inner0, inner_d, CUT)
    group(t1, PH_CLEAR)

    # ---- phase 3: pivot journals ------------------------------------------------
    t2 = design.timeline.count
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        if sx > 0:
            cb0 = PREFIX + 'plate_out - ' + PREFIX + 'cbore_depth'
        else:
            cb0 = '-' + PREFIX + 'plate_out'
        for y_p, jnt in ((0.0, 'j4'), (-L2, 'j3')):
            yz_circle('bore_%s_%s' % (jnt, tag), y_p, 0.0, val('bore_d'), x0, dx, CUT)
            yz_circle('cbore_%s_%s' % (jnt, tag), y_p, 0.0, val('cbore_d'),
                      cb0, PREFIX + 'cbore_depth', CUT)
    group(t2, PH_PIVOT)

    # ---- phase 4: servo lobes ----------------------------------------------------
    t3 = design.timeline.count
    for sx, y_p, run, jnt in LOBES:
        c0, c1, screws, _, _ = lobe_geometry(y_p, run)
        if sx > 0:
            win0, wind = PREFIX + 'plate_out', PREFIX + 'lobe_t'
            pil0 = PREFIX + 'plate_out + ' + PREFIX + 'lobe_t - ' + PREFIX + 'pilot_depth'
        else:
            win0 = '-(' + PREFIX + 'plate_out + ' + PREFIX + 'lobe_t)'
            wind = PREFIX + 'lobe_t'
            pil0 = '-(' + PREFIX + 'plate_out + ' + PREFIX + 'lobe_t)'
        yz_rect('window_' + jnt,
                c0 - val('loc') / 2, c1 + val('loc') / 2,
                -(val('case_w') + val('loc')) / 2, (val('case_w') + val('loc')) / 2,
                win0, wind, CUT)
        # LEAD KEYWAY: ONE notch, centred across the width, cut into the END
        # wall at the shaft end and running OUTWARD to daylight. Being centred
        # it is symmetric under the J3/J4 mirror, so one notch serves both
        # lobes and the servo may arrive either way up - which is what the
        # two-wall version was reaching for and got wrong.
        near_y = y_p - run * val('shaft_end')
        k_d, k_l = val('lead_key_d'), val('lead_key_l')
        ka, kb = sorted((near_y, near_y - run * k_l))
        yz_rect('lead_key_' + jnt, ka, kb, -k_d / 2, k_d / 2, win0, wind, CUT)
        for i, ys in enumerate(screws):
            yz_circle('pilot_%s_%d' % (jnt, i), ys, 0.0, val('pilot_d'),
                      pil0, PREFIX + 'pilot_depth', CUT)
    group(t3, PH_DRIVE)

    # ---- phase 5: cable route -----------------------------------------------------
    t4 = design.timeline.count
    # The duct and the lightening are the same cut. Everything between the two
    # walls, minus a rail top and bottom, is web that carries nothing - and the
    # loom has to get from the elbow to the wrist somehow regardless.
    xz_rect('duct', -val('plate_in'), val('plate_in'), -val('duct_z'), val('duct_z'),
            '-' + PREFIX + 'l2', PREFIX + 'l2', CUT)
    group(t4, PH_CABLE)

    # ---- phase 6: finish ------------------------------------------------------------
    t5 = design.timeline.count
    col = adsk.core.ObjectCollection.create()
    for sx, y_p, run, jnt in LOBES:
        _, _, _, lo, hi = lobe_geometry(y_p, run)
        for y_c in (lo, hi):
            for z_c in (-val('lobe_z'), val('lobe_z')):
                for e in edge_along_x_at(y_c, z_c):
                    col.add(e)
    if col.count:
        f_inp = fil.createInput()
        f_inp.addConstantRadiusEdgeSet(col, V(STYLE + 'radius'), True)
        fil.add(f_inp).name = 'lobe_corners'
    # POLYGONAL: facet the OUTLINE of each fork plate. The plate's outer face
    # carries several closed curves - the boss circle, the journal counterbore,
    # the lobe blends - and only the outline reaches the body's z extreme at
    # +/- boss_r. Select on that and the counterbore is never touched, which a
    # length filter would not guarantee (the counterbore circle is 76.5 mm and
    # the outline arc is 67.3, so longer-is-outer is simply false here).
    # The plate outline is a boss CIRCLE plus a silhouette ARC, and both get the
    # facet - but only at 1.50. Probed against the built body: 2.50 and 2.00
    # fail ASM_BL_UNFIN_SHEET whether the circle is included or not, because the
    # arc runs tangentially into the circles and has nowhere to run out. 1.50
    # computes, and with the circle in it removes 331 mm3 against 143 without,
    # so the fuller outline is worth having.
    # Also note: match the SIGNED x. Comparing abs() to abs() picks up both
    # faces on the first pass and then re-uses dead references on the second.
    n_face = 0
    for x_pick in ((val('plate_out'), -val('plate_out')) if FACET else ()):
        col = adsk.core.ObjectCollection.create()
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
            if abs(reach - val('boss_r')) < val('tol'):
                col.add(e)
        assert col.count == 2, (
            'expected the boss circle and the silhouette arc on the x %+.1f '
            'plate face, found %d edges' % (x_pick * 10, col.count))
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            col, V(PREFIX + 'facet'), False)
        chf.add(c_inp).name = 'plate_facet_%s' % ('p' if x_pick > 0 else 'm')
        n_face += col.count
    group(t5, PH_FINISH)

    # ---- identity + diagnostics --------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - the web is not reaching both walls'
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

    web_at_axis = web_axis
    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('L2 %.1f | plates |x| %.1f..%.1f (%.1f thick) | waist %.1f flush inside' % (
        L2 * 10, val('plate_in') * 10, val('plate_out') * 10,
        val('plate_t') * 10, val('waist_t') * 10))
    print('silhouette: r %.2f bosses joined by r %.1f concave arcs (DERIVED from the '
          '%.1f waist), waist half %.2f' % (
              val('boss_r') * 10, r_fil * 10, val('waist_z') * 10, waist_z * 10))
    print('journal bore %.2f / flange counterbore %.2f x %.1f deep, boss r %.2f' % (
        val('bore_d') * 10, val('cbore_d') * 10,
        val('cbore_depth') * 10, val('boss_r') * 10))
    for sx, y_p, run, jnt in LOBES:
        c0, c1, screws, lo, hi = lobe_geometry(y_p, run)
        print('%s lobe on %sX: case y %.1f..%.1f, screws y %.1f / %.1f, '
              'lobe y %.1f..%.1f' % (
                  jnt, '+' if sx > 0 else '-', c0 * 10, c1 * 10,
                  screws[0] * 10, screws[1] * 10, lo * 10, hi * 10))
    print('box beam: 2 walls %.1f thick + rails %.1f top and bottom, duct %.1f x %.1f'
          % (val('waist_t') * 10, val('rail_z') * 10,
             val('plate_in') * 20, val('duct_z') * 20))
    print('POLYGONAL: %.2f mm facet (plate_t/5, LOCAL, probed ceiling) on %d plate-outline edges'
          % (val('facet') * 10, n_face))
    print('WEB ON THE CENTRELINE: %.1f mm between the two swings '
          '(J4 takes %.1f, J3 takes %.1f)' % (
              web_at_axis * 10, wval('sweep_r') * 10, val('elbow_clear') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
