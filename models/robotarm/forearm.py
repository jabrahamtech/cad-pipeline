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

J3's SERVO PAD IS NOT PART OF THIS FILE ANY MORE. It is `j3_servo_cap`,
bolted to the end of the standoff web with two M3. That is not tidiness: with
the pad integral the elbow could not be assembled at all - GATE j3_installs
found the 36T gear 1.25 mm too big to pass its own insertion path, the pinion
short of its run-up onto the horn by 6.8 mm, and the retention M3 with 1.20 mm
of driver clearance where a bit needs 25. All three were the pad being in the
way, and all three go when it lifts off. See _HANDOFF.md section 10.

What stays here is the standoff WEB, so section 9's load path is unchanged.

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

from lib.bearings import B608ZZ  # noqa: E402 - the idler runs in one
from lib.design_rules import FASTENER_MM as _FASTENERS  # noqa: E402
from lib.gears import J3_MOUNT, J3_PAIR  # noqa: E402 - the elbow reduction
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
PH_ELBOW = 'elbow drive clearance'
PH_CABLE = 'cable route'
PH_FINISH = 'finish'

# Probe hook: _probe_forearm_facet.py sets this False to build the plain body
# and then try chamfer sizes against it. Nothing else touches it.
FACET = True
# Same hook for the lobe-corner fillet. The J3 lobe's INBOARD corners are cut
# away by the gear and pinion clearance cylinders now, so which corners still
# exist is a question to probe, not to assume.
LOBE_FILLET = True
PHASES = [PH_FORM, PH_CLEAR, PH_PIVOT, PH_ELBOW, PH_DRIVE, PH_CABLE, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A link is light; the joints are dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('forearm')


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

    def sval(name):
        return ups.itemByName(STYLE + name).value

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
    param('facet', '1.0 mm',
          'LOCAL, not sty_facet - _style.md rule 1 says the facet scales with\n'
          '           the volume it bevels, and these are 7.5 mm fork plates, not the\n'
          '           upper arm\'s 24 mm slab. A 4.0 shared facet on a 7.5 plate is not\n'
          '           a facet, it is most of the plate. And redefining sty_facet to\n'
          '           suit this part would silently re-cut every other part in the\n'
          '           document - that is the exact bug _check_ledger.py exists for.\n'
          '           A PROBED CEILING, not a preference, and the ceiling MOVED when\n'
          '           the J3 reduction landed. It was plate_t/5 = 1.50: measured\n'
          '           against the built body, 2.50 and 2.00 failed ASM_BL_UNFIN_SHEET\n'
          '           because the silhouette arc runs tangentially into the boss\n'
          '           circles and has nowhere to run out, and 1.50 was the largest\n'
          '           that computed. The J3 servo standoff now blends into the -X\n'
          '           plate face as well, and on THAT face 1.50 and 1.25 both fail\n'
          '           ASM_INCONS_FACE; 1.00 computes on both. Held as ONE number\n'
          '           rather than one per face: the two faces bevel the same plate,\n'
          '           and a part chamfered 1.50 on one side and 1.00 on the other\n'
          '           reads as a bug. Do not raise it without re-probing BOTH faces.')
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
    param('lobe_radius_j3', '4.5 mm',
          'LOCAL, not sty_radius - and for the same reason fa_facet is local.\n'
          '           The J3 lobe stopped being a pad on the plate when the reduction\n'
          '           pushed it out on a standoff: its corner edge now runs 16.10 mm\n'
          '           from inside the plate, through the gear clearance cut, to the\n'
          '           servo face, and the faces either side of it change along the way.\n'
          '           J4\'s 6.0 will not compute on it. PROBED against the built body:\n'
          '           6.0 fails ASM_INCONS_FACE, 5.5 and 5.0 fail ASM_BL_CAP_COMPLEX,\n'
          '           4.5 computes. A CEILING, not a preference. Do not raise it\n'
          '           without re-probing.')
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
    # --- THE GEARED ELBOW ---------------------------------------------------
    # Every number here is READ, not chosen. The handoff priced this drive at
    # "~7 mm of forearm width" and it was never a free parameter - see
    # lib/gears.py J3_MOUNT, which solves it from the MG90S stack and the
    # pair's face width, and specs/robotarm/_HANDOFF.md section 9.
    _P, _M, _B = J3_PAIR, J3_MOUNT, B608ZZ
    param('j3_centre', '%.5f mm' % _P.centre_distance,
          'lib/gears.py J3_PAIR - do not edit here. The J3 servo shaft sits\n'
          '           this far from the elbow, TOWARD THE WRIST, and j3_gear and\n'
          '           j3_pinion cut their teeth from the same object.')
    param('j3_band', PREFIX + 'free + %.5f mm + ' % _P.face + PREFIX + 'free',
          'derived: the axial band the 36T gear turns in, out from the plate\n'
          '           outer face - a running gap, the face width, another gap')
    param('j3_gear_clear', '%.5f mm + ' % _P.r_tip(_P.z_gear) + PREFIX + 'free',
          'derived: the radius the 36T sweeps about J3, plus clearance.\n'
          '           NOTHING may stand inside this between the plate outer face and\n'
          '           the servo lobe.')
    param('j3_pin_clear', '%.5f mm + ' % _P.r_tip(_P.z_pinion) + PREFIX + 'free',
          'derived: the same for the 18T about the SERVO axis. This one is the\n'
          '           surprise - it is r %.2f and the lobe is only %.2f tall, so it\n'
          '           cuts the standoff clean through and the lobe hangs off the J4\n'
          '           end on a web. Priced in _HANDOFF.md section 9: 71x on\n'
          '           interlayer shear, 1.6 %%%% of backlash in lost motion.'
          % (_P.r_tip(_P.z_pinion) + 0.4, CATALOG['MG90S'].case_w / 2 + 1.6 + 1.0))
    param('j3_standoff',
          PREFIX + 'free + %.5f mm + %.5f mm - ' % (_P.face, _M.seat_z) + PREFIX + 'lobe_t',
          'derived, and the whole cost of this drive: how far the J3 servo pad\n'
          '           stands off the plate so the pinion lands coplanar with the gear.\n'
          '           free + face + J3_MOUNT.seat_z - lobe_t. Boring the pinion\n'
          '           through instead of blind-pocketing it is what makes seat_z 6.70\n'
          '           rather than 11.50, and that is 4.8 mm of arm width.')

    # --- 608ZZ at the idler side, in place of a flange counterbore ----------
    # A gear mesh loads this axis RADIALLY and slop at the elbow is backlash
    # at the tooth, which is the one thing a 2:1 cannot fix. j3_axle.py has
    # the argument. Its inner race is the datum read from BOTH ends:
    # j3_axle's collar must land INSIDE it, this shoulder OUTSIDE it, and
    # _check_elbow.py asserts both.
    param('brg_od', '%.4f mm' % _B.od, 'lib/bearings.py B608ZZ - do not edit here')
    param('brg_w', '%.4f mm' % _B.width, 'lib/bearings.py B608ZZ')
    param('brg_press', '0.02 mm',
          'interference on the OUTER race. ASSUMED - it is j3_axle\'s number for\n'
          '           the inner race applied to the other one, and a housing fit is not\n'
          '           a shaft fit. GAUGE IT before printing a second one.')
    param('brg_pocket_d', PREFIX + 'brg_od - ' + PREFIX + 'brg_press', 'derived')
    param('brg_bore', '%.4f mm' % (_B.inner_race_od + 1.0),
          'the retaining shoulder\'s bore. DERIVED from B608ZZ.inner_race_od,\n'
          '           not typed: this plate does not turn, so its shoulder must bear\n'
          '           OUTSIDE the inner race or it rubs it and locks the joint.')
    param('brg_shoulder', PREFIX + 'plate_t - ' + PREFIX + 'brg_w',
          'derived: what is left of the plate outboard of the pocket')

    # --- the bolt-on servo cap ---------------------------------------------
    param('cap_t', PREFIX + 'lobe_t',
          'the cap IS the servo pad, so it is exactly the pad thickness this\n'
          '           file used to carry. j3_servo_cap.py asserts it matches.')
    param('cap_pilot_d', '%.4f mm' % _FASTENERS['M3']['pilot'],
          'M3 self-tapping pilot - lib/design_rules.py FASTENER_MM, the same\n'
          '           table the elbow retention bolt reads.')
    param('cap_head_d', '6.0 mm',
          'M3 socket head. The cap counterbores its screws FLUSH to this and\n'
          '           it has no choice: the servo\'s tab plate lands on that face and\n'
          '           spans them. So the head, not the shank, is what sets how far\n'
          '           this standoff has to reach - sized on the shank first and the\n'
          '           counterbore came out 0.72 mm from the edge.')
    param('bolt_clear_r', '%.4f mm' % (_FASTENERS['M3']['clearance'] / 2.0),
          'half the M3 clearance the CAP is bored to. This file needs it to\n'
          '           place the pilots so the cap\'s own holes clear the window.')
    param('cap_pilot_depth', '8.0 mm',
          'engagement into the standoff web, which is %.2f deep. Leaves 1.6.'
          % 9.6)
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

    def edge_along_x_at(y_c, z_c, min_len=0.0):
        """Edges running along X at one (y, z) corner, at least min_len long.

        The length filter is not tidiness. The J3 lobe's INBOARD corner is now
        SPLIT by the gear clearance cut into a 1.00 stub inside the plate and a
        5.50 stub on the lobe; asking a 4.5 fillet to run along a 1.00 edge is
        the ASM_INCONS_FACE this used to die on.
        """
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            b = e.boundingBox
            if (abs(b.minPoint.y - b.maxPoint.y) < val('tol')
                    and abs(b.minPoint.z - b.maxPoint.z) < val('tol')
                    and abs(b.minPoint.y - y_c) < val('tol')
                    and abs(b.minPoint.z - z_c) < val('tol')
                    and e.length >= min_len - 1e-9):
                col.add(e)
        return col

    # ---- the two servo lobes, as data ---------------------------------------
    # (sign of X, pivot y, sign of the case's run along Y). Both cases point
    # INBOARD along the arm so their mass sits between the joints, not past
    # them: J4's runs back from the wrist, J3's runs forward from the elbow.
    L2 = val('l2')
    # J3's servo NO LONGER SITS ON THE ELBOW. It drives a 2:1 spur pair, so
    # it sits one centre distance toward the WRIST and one standoff further
    # outboard, with the gear train filling the space between. Both numbers
    # are read from lib/gears.py, not chosen here.
    Y_PIN = -L2 + val('j3_centre')
    LOBES = [(+1, 0.0, -1, 'j4'), (-1, Y_PIN, +1, 'j3')]

    def SO(jnt):
        """The standoff expression for one lobe. J4 sits on its plate."""
        return (' + ' + PREFIX + 'j3_standoff') if jnt == 'j3' else ''

    def so_val(jnt):
        return val('j3_standoff') if jnt == 'j3' else 0.0

    def block_hi(jnt, hi):
        """How far along +Y the servo block reaches.

        J4 stops at lobe_pad past its outer screw, as it always did. J3
        REACHES TO THE BOSS RADIUS, and that is not styling: the web which
        survives the pinion cut is 9.75 mm of Y, the servo window eats 4.0 of
        it, and a M3 through-hole with two minimum walls wants 6.6 - so there
        is nowhere to put the cap screws otherwise. boss_r is as far as it can
        go without standing proud of the part's own silhouette, which stops
        there anyway.
        """
        return val('cap_reach') if jnt == 'j3' else hi

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

    # ---- where the cap bolts on, SOLVED before anything is cut --------------
    # The band for the cap screws is pinned on both sides: the servo window
    # inboard, the block edge outboard, a minimum wall and a HEAD RADIUS from
    # each. So the reach is not a styling choice - it is the smallest block
    # that can carry the screw, and it comes out past the silhouette. That is
    # the honest cost of bolting through the same face the servo clamps.
    _Y_PIN = -val('l2') + val('j3_centre')
    _c0, _c1, _scr, _, _ = lobe_geometry(_Y_PIN, +1)
    _win_y1 = _c1 + val('loc') / 2
    _head_r = val('cap_head_d') / 2

    # Z first - it does not depend on anything else. As far apart as the edge
    # and a FLUSH head allow, because the pair splits the servo's reaction
    # couple and wants the longest lever it can get.
    param('cap_screw_z', '%.5f mm' % ((val('lobe_z') - val('wall') - _head_r) * 10),
          'derived: as far apart as the cap edge and a flush HEAD allow. The\n'
          '           pair is stacked in Z on purpose - the servo reacts its stall\n'
          '           torque about X as a couple in Z and two screws split it; side\n'
          '           by side in Y they would not. What binds this is the counterbore,\n'
          '           not the hole: 5.0 looked fine on the shank and put the head\n'
          '           0.80 from the edge.')

    # Y is pinned by THREE things, and it took all three to find out. The
    # servo window inboard; the servo's own outer tab pilot, which is blind in
    # the same face this counterbore sinks into; and the block edge outboard.
    _y_win = _win_y1 + val('wall') + _head_r
    _sep = _head_r + val('pilot_d') / 2 + val('wall')
    _dz = val('cap_screw_z')
    _y_pilot = (max(_scr) + math.sqrt(max(_sep ** 2 - _dz ** 2, 0.0))
                if _sep > _dz else max(_scr))
    param('cap_screw_y', '%.5f mm' % (max(_y_win, _y_pilot) * 10),
          'derived: the first station clear of BOTH the servo window and the\n'
          '           servo\'s own outer tab pilot. The pilot is the binding one and it\n'
          '           is easy to miss - it is blind in the same face the cap sinks its\n'
          '           counterbore into, so the two collide underground while looking\n'
          '           2.4 mm apart on the face.')
    param('cap_margin', '0.1 mm',
          'slack on the derived reach. Without it the block edge lands EXACTLY\n'
          '           on the minimum wall and every assert downstream sits on a float\n'
          '           comparison it can fail either side of. 0.1 costs nothing and\n'
          '           means the checks are measuring the design, not the arithmetic.')
    param('cap_reach', '%.5f mm'
          % ((max(_y_win, _y_pilot) + _head_r + val('wall') + val('cap_margin')) * 10),
          'derived: one head, one wall and a hair past the screw. The SMALLEST\n'
          '           block that can carry the fixing, and it finishes past fa_boss_r -\n'
          '           so the standoff stands proud of the link silhouette at the wrist\n'
          '           end, in free air outboard of the plate where nothing sweeps.\n'
          '           That is the honest cost of bolting through the same face the\n'
          '           servo clamps.')
    assert val('cap_screw_y') + _head_r + val('wall') <= val('cap_reach') + 1e-9, (
        'the cap screw head at y %.2f reaches past the block edge at %.2f'
        % (val('cap_screw_y') * 10, val('cap_reach') * 10))
    assert val('cap_screw_y') - _head_r - val('wall') >= _win_y1 - 1e-9, (
        'the cap screw head at y %.2f breaks into the servo window ending at '
        'y %.2f' % (val('cap_screw_y') * 10, _win_y1 * 10))
    assert val('cap_screw_z') + _head_r + val('wall') <= val('lobe_z') + 1e-9, (
        'the cap screw HEAD at z %.2f leaves under a wall to the edge at %.2f - '
        'the counterbore is what binds here, not the hole'
        % (val('cap_screw_z') * 10, val('lobe_z') * 10))
    for _ys in _scr:
        _d = math.hypot(val('cap_screw_y') - _ys, val('cap_screw_z'))
        assert _d >= _sep - 1e-9, (
            'the cap screw and the servo tab pilot at y %.2f are %.2f apart '
            'and a flush head plus a wall needs %.2f'
            % (_ys * 10, _d * 10, _sep * 10))
    assert val('cap_pilot_depth') + val('wall') <= val('j3_standoff'), (
        'a %.1f deep pilot in a %.2f standoff leaves under %.1f of floor'
        % (val('cap_pilot_depth') * 10, val('j3_standoff') * 10,
           val('wall') * 10))

    # ---- the geared elbow, checked before any of it is cut ------------------
    assert val('j3_standoff') >= val('j3_band') - 1e-9, (
        'the J3 lobe stands off %.2f but the gear turns through %.2f of that '
        'band - the servo pad would sit in the gear'
        % (val('j3_standoff') * 10, val('j3_band') * 10))
    _pocket_wall = (val('boss_r') - val('brg_pocket_d') / 2) * 10
    assert _pocket_wall >= val('wall') * 10 - 1e-6, (
        'only %.2f mm of boss wall around the %.2f 608ZZ pocket - the boss has '
        'to grow' % (_pocket_wall, val('brg_pocket_d') * 10))
    assert val('brg_shoulder') * 10 >= 0.4 - 1e-6, (
        'the 608ZZ pocket leaves only %.2f mm of retaining shoulder'
        % (val('brg_shoulder') * 10))
    assert val('brg_bore') * 10 > B608ZZ.inner_race_od, (
        'the retaining shoulder bores %.2f and the 608 inner race reaches '
        '%.2f - this plate does not turn, so it would rub the INNER race and '
        'lock the joint' % (val('brg_bore') * 10, B608ZZ.inner_race_od))
    assert val('brg_bore') * 10 < B608ZZ.od, (
        'the retaining shoulder bores %.2f against a %.2f bearing OD - it '
        'retains nothing' % (val('brg_bore') * 10, B608ZZ.od))
    # The whole reason the standoff is a web and not a block. Stated here so
    # the geometry below cannot quietly stop being true.
    assert val('j3_pin_clear') > val('lobe_z'), (
        'the pinion clears at r %.2f and the lobe is %.2f tall, so the pinion '
        'circle does NOT cut the standoff through - the web analysis in '
        '_HANDOFF.md section 9 no longer describes this part'
        % (val('j3_pin_clear') * 10, val('lobe_z') * 10))

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
        hi = block_hi(jnt, hi)
        # ONE block from inside the plate out to the tab plane. For J3 that
        # is standoff + lobe; the clearance phase then carves the gear and
        # the pinion out of it, which is what makes the standoff a web rather
        # than something drawn by hand and gone stale.
        # J4 is a pad on its plate, as it always was. J3 is now only the
        # STANDOFF - its pad lifts off as j3_servo_cap, because with the pad
        # here nothing could be assembled past it.
        if sx > 0:
            x0 = PREFIX + 'plate_out - ' + PREFIX + 'lobe_over'
            dx = PREFIX + 'lobe_t + ' + PREFIX + 'lobe_over'
        else:
            x0 = '-(' + PREFIX + 'plate_out + ' + PREFIX + 'j3_standoff)'
            dx = PREFIX + 'j3_standoff + ' + PREFIX + 'lobe_over'
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
        # J4 is untouched by the reduction: a journal bore and a flange
        # counterbore in each plate, same as every other joint in the arm.
        yz_circle('bore_j4_%s' % tag, 0.0, 0.0, val('bore_d'), x0, dx, CUT)
        yz_circle('cbore_j4_%s' % tag, 0.0, 0.0, val('cbore_d'),
                  cb0, PREFIX + 'cbore_depth', CUT)
        if sx < 0:
            # J3 DRIVE SIDE. j3_gear's O20 journal runs in this bore - but
            # that part has NO FLANGE (its gear disc is 47.5 and sits proud
            # of the face), so the counterbore that retains every other hub
            # in this arm is DELETED here. Leaving it would cut the journal's
            # bearing length from 7.5 to 5.0 against a hub whose collar is
            # built for the whole plate - and j3_gear.py asserts fa_plate_t
            # is that whole 7.5, so the two would silently disagree.
            yz_circle('bore_j3_%s' % tag, -L2, 0.0, val('bore_d'), x0, dx, CUT)
        else:
            # J3 IDLER SIDE. A 608ZZ, not a printed journal: the mesh loads
            # this axis radially and slop here is backlash at the tooth,
            # which is the one thing a 2:1 cannot fix. Pocketed from the
            # INNER face and retained by what is left of the plate outboard
            # of it - a shoulder whose bore must clear the INNER race, or
            # this stationary plate rubs it and locks the joint.
            yz_circle('brg_bore_j3_%s' % tag, -L2, 0.0, val('brg_bore'), x0, dx, CUT)
            yz_circle('brg_pocket_j3_%s' % tag, -L2, 0.0, val('brg_pocket_d'),
                      PREFIX + 'plate_in', PREFIX + 'brg_w', CUT)
    group(t2, PH_PIVOT)

    # ---- phase 3b: elbow drive clearance ---------------------------------------
    # The gear and the pinion both turn in the band between the plate outer
    # face and the servo lobe, and BOTH are cut out of the block above rather
    # than drawn around. The pinion's is the one that surprises: r 12.90
    # against a lobe only 8.80 tall, so it cuts the standoff through top to
    # bottom and what is left joining the lobe to the plate is a web at the
    # WRIST end. That is priced in _HANDOFF.md section 9 and it passes.
    t2b = design.timeline.count
    band0 = '-(' + PREFIX + 'plate_out + ' + PREFIX + 'j3_standoff)'
    bandd = PREFIX + 'j3_standoff'
    yz_circle('gear_sweep_j3', -L2, 0.0, 2 * val('j3_gear_clear'), band0, bandd, CUT)
    yz_circle('pinion_sweep_j3', Y_PIN, 0.0, 2 * val('j3_pin_clear'),
              band0, bandd, CUT)

    # THE CAP'S TWO M3, into the end face of what is left. The station was
    # solved in the sanity block above, against the window and the block edge.
    for sz in (+1, -1):
        yz_circle('cap_pilot_%s' % ('p' if sz > 0 else 'm'),
                  val('cap_screw_y'), sz * val('cap_screw_z'),
                  val('cap_pilot_d'), band0, PREFIX + 'cap_pilot_depth', CUT)
    group(t2b, PH_ELBOW)

    # ---- phase 4: servo lobes ----------------------------------------------------
    t3 = design.timeline.count
    for sx, y_p, run, jnt in LOBES:
        if jnt == 'j3':
            continue          # the window, keyway and pilots are on the cap
        c0, c1, screws, _, _ = lobe_geometry(y_p, run)
        if sx > 0:
            win0 = PREFIX + 'plate_out' + SO(jnt)
            wind = PREFIX + 'lobe_t'
            pil0 = (PREFIX + 'plate_out' + SO(jnt) + ' + ' + PREFIX + 'lobe_t - '
                    + PREFIX + 'pilot_depth')
        else:
            win0 = '-(' + PREFIX + 'plate_out' + SO(jnt) + ' + ' + PREFIX + 'lobe_t)'
            wind = PREFIX + 'lobe_t'
            pil0 = '-(' + PREFIX + 'plate_out' + SO(jnt) + ' + ' + PREFIX + 'lobe_t)'
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
    # ONE FILLET PER LOBE, NOT ONE FOR BOTH. They no longer take the same
    # radius - see fa_lobe_radius_j3 - and a single edge set would fail whole
    # rather than fail the corner that actually cannot carry it.
    n_fillet, fillet_note = 0, []
    for sx, y_p, run, jnt in LOBES:
        _, _, _, lo, hi = lobe_geometry(y_p, run)
        hi = block_hi(jnt, hi)
        if jnt == 'j3':
            rad_expr, rad = PREFIX + 'lobe_radius_j3', val('lobe_radius_j3')
        else:
            rad_expr, rad = STYLE + 'radius', sval('radius')
        col = adsk.core.ObjectCollection.create()
        skipped = 0
        for y_c in (lo, hi):
            for z_c in (-val('lobe_z'), val('lobe_z')):
                skipped += (edge_along_x_at(y_c, z_c).count
                            - edge_along_x_at(y_c, z_c, rad).count)
                for e in edge_along_x_at(y_c, z_c, rad):
                    col.add(e)
        fillet_note.append('%s r%.1f on %d edges (%d too short)'
                           % (jnt, rad * 10, col.count, skipped))
        if col.count and LOBE_FILLET:
            f_inp = fil.createInput()
            f_inp.addConstantRadiusEdgeSet(col, V(rad_expr), True)
            fil.add(f_inp).name = 'lobe_corners_' + jnt
            n_fillet += col.count
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
        # WHAT THIS HAS TO BE, and it is no longer "two edges". The rule
        # selects everything on this face reaching the body's z extreme,
        # which is exactly the outline: one CLOSED boss circle plus the
        # silhouette. On +X the silhouette is a single arc. On -X the J3
        # standoff block now runs past where that arc ends and blends into
        # the face, SPLITTING it into two segments - so the honest assert is
        # about what the edges ARE, not how many. A bare count of 2 was right
        # only while the outline happened to come in one piece, and it failed
        # the moment the block grew; a count of 3 would be just as brittle.
        n_circ = sum(1 for e in col if e.geometry.objectType.endswith('Circle3D'))
        n_arc = col.count - n_circ
        assert n_circ == 1, (
            'expected exactly one closed boss circle on the x %+.1f plate '
            'face, found %d - the selection is picking up a counterbore'
            % (x_pick * 10, n_circ))
        assert n_arc >= 1, (
            'no silhouette arc found on the x %+.1f plate face' % (x_pick * 10))
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
    print('POLYGONAL: %.2f mm facet (LOCAL, probed ceiling on BOTH faces) on %d '
          'plate-outline edges (1 boss circle + silhouette, split on -X by the '
          'J3 standoff)' % (val('facet') * 10, n_face))
    print('lobe corners: %s' % ' | '.join(fillet_note))
    _y0 = Y_PIN + val('j3_pin_clear')
    _hi = max(lobe_geometry(Y_PIN, +1)[4], lobe_geometry(Y_PIN, +1)[3])
    print('')
    print('GEARED ELBOW: J3 servo moved %.2f mm toward the wrist (y %.2f) and '
          '%.2f mm out' % (val('j3_centre') * 10, Y_PIN * 10,
                           val('j3_standoff') * 10))
    print('   gear turns at r %.2f, pinion at r %.2f, both in the %.2f band off '
          'the plate face' % (val('j3_gear_clear') * 10,
                              val('j3_pin_clear') * 10, val('j3_band') * 10))
    print('   the pinion circle (r %.2f) is taller than the lobe (%.2f), so the '
          'standoff' % (val('j3_pin_clear') * 10, val('lobe_z') * 10))
    print('   survives only as a web at the WRIST end, y %.2f .. %.2f - '
          '%.2f mm of it' % (_y0 * 10, _hi * 10, (_hi - _y0) * 10))
    print('   608ZZ: %.2f pocket x %.1f deep from the plate INNER face, %.2f '
          'shoulder' % (val('brg_pocket_d') * 10, val('brg_w') * 10,
                        val('brg_shoulder') * 10))
    print('   shoulder bores %.1f - OUTSIDE the %.1f inner race, so the '
          'stationary plate bears on the OUTER one'
          % (val('brg_bore') * 10, B608ZZ.inner_race_od))
    print('   J3 drive-side flange counterbore DELETED - j3_gear has no flange '
          'and its journal is built for the full %.1f plate' % (val('plate_t') * 10))
    print('   the servo PAD is not here - it is j3_servo_cap, %.1f thick, bolted '
          'to this web' % (val('cap_t') * 10))
    print('   by 2 x M3 at y %.2f, z +/-%.2f, %.1f pilot x %.1f deep. Without '
          'that split' % (val('cap_screw_y') * 10, val('cap_screw_z') * 10,
                          val('cap_pilot_d') * 10, val('cap_pilot_depth') * 10))
    print('   the gear, the pinion and the retention M3 could none of them be '
          'fitted - GATE j3_installs.')
    print('')
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
