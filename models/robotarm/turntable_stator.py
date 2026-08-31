"""robotarm/turntable_stator - Fusion MCP generating script.

Rebuilds `robotarm_turntable_stator` (idempotent). Spec:
specs/robotarm/base_platter_measured.md.

J1's FIXED half. Bolts to the printed platter, holds the yaw servo, and
carries the three 608ZZ rollers the shoulder disc rides on.

Local frame: origin ON THE J1 YAW AXIS at the PLATTER'S RIM TOP - platter
z 42.00, measured, not assumed. +Z up. Everything in this part and in
turntable_ring is in this frame; the shoulder bracket's rotor meets it at
tt_race_z.

WHAT THIS REPLACES. The legacy turret was a 12 mm solid Ø104 plate, three M8
axle bolts with nylocs, three separate hold-down clips and three more heat-set
inserts in the cap's rim - eleven fasteners and four printed parts to carry a
300 g arm. This does the same three jobs with three screws:

  weight down   3 x 608ZZ on RADIAL axles, rolling, as before
  radial        the rotor's Ø68 boss turns inside the ring's bore - one
                big-diameter plain journal instead of nothing at all
  uplift        the ring hooks over the rotor's rim

and ONE M3 per post runs the whole stack - through the ring, down the post,
into the platter's insert. Take those three out and the turret lifts off.
Nothing caps rotation, so J1 gets the servo's full 180 deg.

THE AXLES ARE RADIAL, and that is not a detail. The rotor's underside moves
TANGENTIALLY over each roller, so the roller's axis has to be perpendicular to
that - radial - or the bearing scrubs sideways instead of rolling and wears a
flat on its outer race. The legacy design got this right and said so; it is
repeated here because it is the one thing about a roller turntable that looks
equally plausible either way.

THE RACE COLLAR IS THE OTHER ONE. Each stub axle stands 0.5 mm proud where the
bearing seats, so the M3 and washer clamp the INNER race only. Without it the
outer race touches the cheek and the roller stops rolling and starts rubbing.

Print orientation: FLAT, base down, cheeks and posts up. The stub axles then
grow sideways off the cheeks as horizontal cylinders - the one real overhang
in the part, and short enough (Ø7.9 over 8.5 mm) to bridge. Print it axles-up
instead and the bearing seat gets a seam down its side.
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

COMPONENT = 'robotarm_turntable_stator'
BODY_NAME = 'turntable_stator'
PREFIX = 'ts_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_FORM = 'stator form'
PH_ROLLERS = 'rollers'
PH_SERVO = 'yaw servo'
PH_FIX = 'platter interface'
PHASES = [PH_FORM, PH_ROLLERS, PH_SERVO, PH_FIX]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. The base is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
from lib.servo import CATALOG as _SERVOS  # noqa: E402

_SG_HORN = _SERVOS['SG90']
APPEARANCE_HINTS = hints_for('turntable_stator')


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

    def turret(name, expr, comment='', units='mm'):
        _set(TURRET + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    # ---- the SHARED turntable contract --------------------------------------
    # Defined identically here, in turntable_ring.py and shoulder_bracket.py.
    # The first two entries are MEASURED off the printed platter and are the
    # only things in this whole assembly that are not ours to choose.
    turret('post_r', '45.0 mm',
           'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
           '           top face at its rim, az 120/180/240. The ONLY fixing there is.')
    turret('bolt_d', '3.4 mm',
           'M3 clearance. One screw per post runs the whole stack - through the\n'
           '           ring, down the post, into the platter insert. About 40 long.')
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - DRAWING-CONFIRMED')
    turret('roller_w', '7.0 mm', '608ZZ width. The axle is RADIAL, so this lies radially.')
    turret('roller_r', '27.0 mm',
           'roller pitch radius. Boxed in: the servo hub reaches r 21 inside it and\n'
           '           the mounting posts sit at r 45 outside, and the cheeks have to\n'
           '           fit between the two.')
    turret('axle_z', '13.1 mm',
           'roller axle height. = ts_relief_floor + ts_relief_clear + roller_od/2,\n'
           '           so a 608 sitting on its axle clears a MIN_WALL floor of base\n'
           '           plate with ts_relief_clear of daylight. WAS 12.0, set to clear\n'
           '           the PLATTER top at z 0 - which ignored this part\'s OWN 4.0 mm\n'
           '           base plate sitting on it. The bearing bottomed at z 1.00 inside\n'
           '           a plate spanning z 0..4 and could not be fitted at all.\n'
           '           _check_j1 found it 2026-08-26; asserted below now.')
    turret('race_z', TURRET + 'axle_z + ' + TURRET + 'roller_od / 2',
           'derived: where the rotor\'s underside sits. NEVER type this.')
    turret('disc_d', '76.0 mm',
           'rotor diameter. Not free: the MG995 pad on the shoulder bracket reaches\n'
           '           r 32.1, and the ring has to hook over the rim outside that.')
    turret('disc_t', '5.0 mm', 'rotor rim thickness, where the ring hooks over it')
    turret('boss_d', '68.0 mm',
           'the rotor\'s raised centre. This is the JOURNAL - it turns inside the\n'
           '           ring\'s bore, and it is what locates the arm radially. A big\n'
           '           diameter running slowly is the one plain bearing that is\n'
           '           genuinely better than a rolling one here.')
    turret('boss_h', '4.4 mm',
           'how far that boss stands above the rim. = ring_lift + ring_t, so the\n'
           '           ring finishes FLUSH with the boss top and the plane the fork\n'
           '           stands on is one continuous face. WAS 4.0 HERE and 4.4 in\n'
           '           shoulder_bracket.py - one shared parameter with two values,\n'
           '           which only ever worked because the bracket happens to build\n'
           '           last. Found by _check_j1 2026-08-26.')
    turret('ring_t', '4.0 mm',
           'retainer thickness. NOT 3.0: an M3 head counterbore is 2.4 and design\n'
           '           _rules wants a wall under it, so 4.0 is the floor if the screws\n'
           '           are to finish flush.')
    turret('ring_or', '50.0 mm', 'ring outer radius - has to cover the posts at r 45')
    turret('ring_lift', '0.40 mm', 'gap between the ring and the rotor rim it holds down')
    turret('collar_h', '0.5 mm',
           'how far the bearing seat stands proud of its cheek. Small, but it is the\n'
           '           only thing keeping the OUTER race off the cheek - without it\n'
           '           the roller does not roll, it rubs.')
    turret('axle_d', '7.9 mm', '608 bore 8.0 - 0.1, a press')
    turret('horn_span', '32.8 mm', 'yaw horn LONG-arm pocket span. The real 4-arm\n           horn runs ~33.5 tip to tip (ASYMMETRIC - short axis ~16; slots run\n           full span both ways, a slot longer than its arm is air), and the\n           arms were ALWAYS trimmed at assembly. 32.8 is the ceiling the\n           cable window allows (2 x (cable_ir - wall)) - trim to fit it.\n           2026-08-27 horn audit')
    turret('horn_w_root', '6.04 mm',
           'SHARED tt_ contract - shoulder_bracket cuts the pocket and DERIVES\n           this from lib.servo.micro_arm_w(6.5) + 0.4. Declared here so the\n           two files fail loudly if they ever disagree; the rotor is the\n           authority. 2026-08-28 measured taper.')
    turret('horn_w_tip', '4.84 mm',
           'SHARED - micro_arm_w(16.4) + 0.4. THE SLOTS ARE TAPERED.')
    turret('horn_r_root', '6.5 mm', 'SHARED - where the tapered slots start')
    turret('horn_z', '%.4f mm' % (_SG_HORN.horn_hub_h + 0.4),
           'derived: the horn\'s FULL protrusion above the output collar,\n'
           '           plus a 0.4 seating gap. NOT "blade thickness 2.0 + 0.4" -\n'
           '           what goes into this pocket is the whole horn and the splined\n'
           '           HUB stands proud of the blade. Pocket depth into the rotor underside.\n'
           '           2026-08-30, from the bench: the rotor would not sit down on\n'
           '           its races. See ts_horn_seat - raising this number alone had\n'
           '           never once changed the clearance.')
    turret('screw_bore', '6.0 mm', 'driver access to the horn screw, up the rotor centre')

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'silhouette corner radius - SHARED, do not retune it here')

    # ---- SG90, DATASHEET (lib/servo.py) -------------------------------------
    # J1 is an SG90 because both MG90S are spoken for at J3 and J4.
    param('case_l', '22.7 mm', 'SG90 case length - lies along Y here. TowerPro B')
    param('case_w', '12.2 mm', 'SG90 case width - lies along X. TowerPro D; was 12.6')
    param('case_h', '23.7 mm', 'SG90 case height')
    param('tab_thk', '2.4 mm', 'SG90 tab thickness')
    param('tab_below_top', '4.3 mm', 'case top to the TOP of the tabs')
    param('tab_pitch', '27.8 mm', 'SG90 tab hole pitch - drawing SG90_Model_A;\n           the MG90S is the same footprint (27.5 derived), 2026-08-27 audit')
    # THE OUTPUT SHAFT IS NOT IN THE MIDDLE OF THE CASE, and this part used to
    # assume it was. lib/servo.py has carried shaft_from_end = 6.1 since the
    # library was written and, until 2026-08-26, servo_adapter.py was the ONLY
    # file that read it. Centring the CASE on J1 puts the SHAFT 5.2 mm off the
    # axis - the horn would have driven shoulder_bracket's cross pocket as a
    # 5.2 mm crank, which orbits and binds instead of turning.
    # shoulder_bracket got this right for the MG995 (case z -30..10, shaft at
    # 0) and forearm got it right for both MG90S. This part did not.
    param('shaft_from_end', '6.1 mm',
          'SG90 shaft axis to the NEAR end of the case - lib/servo.py')
    param('shaft_off', PREFIX + 'case_l / 2 - ' + PREFIX + 'shaft_from_end',
          'derived: how far the CASE CENTRE must sit from the J1 axis so the\n'
          '           SHAFT lands on it. Everything servo-related below is offset\n'
          '           by this in +Y, which also moves the case away from the cable\n'
          '           window at az 270 rather than into it.')
    param('tab_span', '32.3 mm', 'SG90 tab tip to tip. TowerPro E')
    param('boss_h', '4.2 mm', 'SG90 output collar above the case top')
    param('horn_hub_h', '3.0 mm', 'SG90 horn hub height, seated on that collar -\n           2026-08-27 horn audit (was 3.8)')
    param('horn_blade_t', '2.0 mm', 'SG90 horn blade thickness - horn audit (was 1.5)')
    param('pilot_d', '1.8 mm', 'SERVO_SCREW_PILOT_MM - self-tapping into PETG')
    param('pilot_depth', '4.0 mm', 'into the servo pad')

    # ---- fits and local geometry --------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('free', '0.4 mm', 'free fit - design_rules')
    param('plate_t', '4.0 mm', 'base plate thickness')
    param('lead_key_d', '%.2f mm' % (CATALOG['SG90'].lead_bundle_dia + 0.2),
          'lead keyway WIDTH across the case width, centred on the bundle.\n'
          '           The servo cannot be INSERTED without it: the cable crosses the\n'
          '           whole aperture on the way down.')
    param('lead_groove_w', '5.0 mm',
          'lead groove width in the plate underside - same Ø-5 convention as\n'
          '           every other lead escape in the project')
    param('lead_groove_d', '1.2 mm',
          'lead groove depth up into the plate underside. The bundle leaves at\n'
          '           z -1.0 with its top edge at +0.7, and the plate is 0..4.0, so on\n'
          '           its way out it grazes 0.7 into the plate. _check_leads measured\n'
          '           exactly that - 2.20 mm3, 3 %% of the escape - after the keyway\n'
          '           was moved to the -Y end. This is the same groove that used to\n'
          '           relieve the +Y end, re-sited to the end the lead actually uses.')
    param('lead_escape', '8.0 mm',
          'how far the lead must run clear before bending - MUST MATCH\n'
          '           _check_leads.ESCAPE_MM. The lead_groove_* pair that used to sit\n'
          '           here went with the datum correction of 2026-08-28: the groove\n'
          '           relieved the case\'s FAR (+Y) end, and the bundle leaves the -Y\n'
          '           end, where at z -1.0 it is already clear under the plate.')
    param('plate_ir', '10.0 mm', 'base plate inner radius - the servo comes through here')
    param('plate_or', '50.0 mm', 'base plate outer radius - out to the ring')
    # THE LOOM HAD NO WAY THROUGH THIS PART. The servo well is 12.40 x 22.90
    # against an SG90 case of 12.20 x 22.70 - one tenth of a millimetre each
    # side, which is a clearance fit for the servo and nothing at all for
    # fifteen wires. Five servos live above J1 (J2 MG995, J3 and J4 MG90S,
    # J5 SG90, effector SG90) and every one of their leads has to cross here.
    # shoulder_bracket already cuts a matching window in the rotor at
    # sb_cable_ir 18.0, 50 deg, astern at az 270; this is the fixed half of
    # that route and base_lid carries the same slot underneath.
    param('cable_az', '270.0 deg', 'astern of the arm, matching sb_cable_deg\'s\n'
                                   '           centre - the loom is never under the reach', 'deg')
    param('cable_ir', '13.7 mm',
          'inner radius. 13.0 -> 13.7 on 2026-08-28: the servo well no longer\n'
          '           ends at the aperture, it ends at the LEAD KEYWAY, which runs\n'
          '           5.95 further out to y -12.05. At 13.0 that left 0.95 of plate\n'
          '           between two through-slots. Costs 0.7 mm of window width; the\n'
          '           loom needs 45 mm2 and this still gives 126.')
    param('cable_or', '20.0 mm', 'outer radius. The race band starts at r 23.0')
    param('cable_deg', '70.0 deg', 'arc swept. At a 16.5 mean radius that is 20 mm\n'
                                   '           of slot, 7 mm wide - 140 mm2 for a loom that needs 45', 'deg')
    param('post_d', '11.0 mm', 'mounting post diameter - 3.8 of wall round an M3 clearance')
    param('relief_floor', '1.6 mm',
          'what is LEFT of the base plate under each roller - design_rules\n'
          '           MIN_WALL_MM exactly, and it is the floor that sets tt_axle_z.')
    param('relief_clear', '0.5 mm',
          'daylight between the bearing and that floor. Not a fit - nothing\n'
          '           bears here; it is there so a stringy first layer cannot touch\n'
          '           the roller and add drag to a joint with no torque to spare.')
    param('relief_margin', '1.0 mm',
          'how far the relief overruns the bearing footprint, radially and\n'
          '           tangentially. The relief stops AT cheek_ir, so the cheeks keep\n'
          '           their full footing and only the plate between them is cut.')
    param('cheek_t', '4.0 mm', 'roller cheek thickness, radially')
    param('cheek_w', '18.0 mm', 'roller cheek width, tangentially')
    param('cheek_over', '6.0 mm', 'material above the axle centre')
    param('race_od', '12.0 mm', '608ZZ INNER race outer diameter - lib/bearings.py')
    param('collar_d', '11.0 mm',
          'the bearing seat. The ONLY surface it may touch is the inner race\n'
          '           FACE - an annulus from the 8.0 bore to the 12.0 race OD. Wider\n'
          '           than 12.0 and it reaches over the gap toward the ZZ shield,\n'
          '           which is fixed to the OUTER race; touch that and the roller\n'
          '           drags instead of rolling. 11.0 leaves 1.5 mm of contact and\n'
          '           1.0 mm of margin. It was 12.5, which overhung the race.')
    param('washer_od', '11.0 mm',
          'the retainer, and it is a PRINTED part - see roller_cap on the gauge.\n'
          '           A standard M3 washer is Ø7 and falls straight THROUGH the\n'
          '           608\'s Ø8 bore, clamping nothing. The alternatives are all\n'
          '           bought (M3 penny, M4 flat); printing it costs 0.4 g, needs no\n'
          '           order, and obeys the same Ø8..Ø12 rule as the seat.')
    param('axle_len', '8.0 mm',
          'stub length past the collar. Bearing is 7.0, so 1.0 stands proud for the\n'
          '           washer - which must land on the race, never on the axle end.')
    param('axle_pilot', '2.5 mm', 'M3 self-tapper up the middle of the stub')
    param('axle_screw_z', '7.0 mm', 'how deep that pilot goes')
    param('hub_x', '9.0 mm', 'servo pad half width, and the radius its outboard\n'
                             '           end is rounded to')
    param('hub_y', '16.4 mm',
          'servo pad half length. WAS 19.0, which with the +5.20 shaft offset\n'
          '           put the pad\'s far CORNER at r 25.82 - inside the roller band,\n'
          '           which starts at r 23.50. The relief under the az-90 roller\n'
          '           would have undercut the pad it stands on. 16.4 still clears\n'
          '           both pilots by 2.5, and the outboard end is ROUNDED to hub_x so\n'
          '           the pad\'s furthest reach is on the axis at r 21.60, not at a\n'
          '           corner. _check_j1 found the corner 2026-08-26.')
    # DEFINED HERE, not with the other lead params: it reads hub_y, and
    # Fusion rejects an expression naming a parameter that does not exist
    # yet. Order is part of the contract.
    param('lead_key_l', PREFIX + 'hub_y - (' + PREFIX + 'case_l + ' + PREFIX
          + 'loc) / 2 + 1.0 mm',
          'keyway length OUT from the shaft-end face. DERIVED to clear the\n'
          '           servo pad plus 1.0 of overshoot - a keyway that stops inside the\n'
          '           pad is a blind pocket and traps the cable. Never hardcode it.')
    param('window_ir', '22.0 mm', 'lightening windows, inner radius')
    param('window_or', '37.0 mm',
          'lightening windows, outer radius. Bounded by the posts: at 40 the\n'
          '           window ate into the wall around a mounting bolt.')
    param('window_deg', '50.0 deg',
          'arc each window sweeps. Placed at 30/150/270 - between the rollers at\n'
          '           90/210/330 and the posts at 120/180/240, the only azimuths that\n'
          '           carry nothing.', 'deg')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
    # RENAME FIRST, THEN DELETE. See fusion/PLAYBOOK.md.
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        # SKIP THE ROOT. Once this part lives in its own saved file the root
        # component carries the DOCUMENT's name, which is COMPONENT - and a
        # root component cannot be renamed, so the rename below raised
        # "3 : root component name cannot be changed" and no part rebuilt.
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
        'component came back as %r - a stale component still holds the name' % comp.name)
    ext = comp.features.extrudeFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = 'sk_' + name
        return sk

    def one(sk, expected=1):
        assert sk.profiles.count == expected, (
            sk.name + ': expected %d, got %d' % (expected, sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        if op != NEW:
            # Without this a CUT eats every other component. See PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mm(cm):
        """cm -> a millimetre EXPRESSION. createByString reads a bare number as
        millimetres; val() hands out centimetres. See fusion/PLAYBOOK.md."""
        return '%.4f mm' % (cm * 10.0)

    def mxy(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def xy_circle(name, x, y, d, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, x, y), d / 2)
        return extrude(one(sk), op, z0, dz, name)

    def xy_rect(name, x0, x1, y0, y1, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(mxy(sk, x0, y0), mxy(sk, x1, y1))
        return extrude(one(sk), op, z0, dz, name)

    def xy_ring(name, r_out, r_in, z0, dz, op):
        """Two concentric circles give TWO profiles - the inner disc and the
        annulus. Picking by index is a coin toss, so pick by area."""
        sk = sketch(comp.xYConstructionPlane, name)
        for r in (r_out, r_in):
            sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, 0, 0), r)
        assert sk.profiles.count == 2, sk.name + ': got %d profiles' % sk.profiles.count
        want = math.pi * (r_out ** 2 - r_in ** 2)
        c = adsk.core.ObjectCollection.create()
        for i in range(2):
            p = sk.profiles.item(i)
            if abs(p.areaProperties().area - want) < want * 1e-6:
                c.add(p)
        assert c.count == 1, sk.name + ': no profile matched the annulus'
        return extrude(c, op, z0, dz, name)

    def xy_arc(name, r_in, r_out, mid, half, z0, dz, op):
        sk = sketch(comp.xYConstructionPlane, name)
        arcs, lines = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines
        a0, a1 = mid - half, mid + half

        def p(r, a):
            return mxy(sk, r * math.cos(a), r * math.sin(a))

        arcs.addByThreePoints(p(r_out, a0), p(r_out, mid), p(r_out, a1))
        arcs.addByThreePoints(p(r_in, a0), p(r_in, mid), p(r_in, a1))
        lines.addByTwoPoints(p(r_in, a0), p(r_out, a0))
        lines.addByTwoPoints(p(r_in, a1), p(r_out, a1))
        return extrude(one(sk), op, z0, dz, name)

    def radial_cyl(name, az, r_a, r_b, d, op):
        """A cylinder on a RADIAL horizontal axis at azimuth `az`, running from
        radius r_a to r_b at height tt_axle_z.

        The plane is the YZ plane (normal +X) turned about Z by az, so its
        normal IS the outward radial direction - which makes the extrude
        distance a signed radial length and nothing else. r_b < r_a therefore
        just means 'inward', with no rotation matrix to get backwards.
        """
        pl_in = comp.constructionPlanes.createInput()
        pl_in.setByAngle(comp.zConstructionAxis,
                         adsk.core.ValueInput.createByReal(az),
                         comp.yZConstructionPlane)
        pl = comp.constructionPlanes.add(pl_in)
        pl.name = 'pl_' + name
        sk = comp.sketches.add(pl)
        sk.name = 'sk_' + name
        # (0, 0, axle_z) lies ON that plane whatever az is, so this cannot pick
        # up an out-of-plane component that the sketch would silently drop.
        c = sk.modelToSketchSpace(P3(0.0, 0.0, tval('axle_z')))
        sk.sketchCurves.sketchCircles.addByCenterRadius(c, d / 2)
        return extrude(one(sk), op, mm(r_a), mm(r_b - r_a), name)

    # ---- values in cm --------------------------------------------------------
    plate_t = val('plate_t')
    race_z = tval('race_z')
    roll_r = tval('roller_r')
    seat_r = roll_r + tval('roller_w') / 2            # collar face
    cheek_ir = seat_r + tval('collar_h')              # cheek inner face
    cheek_or = cheek_ir + val('cheek_t')
    stub_ir = cheek_ir - tval('collar_h') - val('axle_len')
    ring_under = race_z + tval('disc_t') + tval('ring_lift')
    post_top = ring_under
    # THE HORN HAS TO REACH INTO THE ROTOR, NOT STOP AT IT. The rotor's cross
    # pocket is cut tt_horn_z UP from its race face, so the servo sits that much
    # higher than "horn top flush with the race face" - which is what this was,
    # and it left the blade sitting 1.8 mm short of the slot it is meant to
    # drive. J1 would not have turned at all.
    # THE SEATING GAP, AND IT WAS NEVER IN THE STACK. tt_horn_z used to
    # cancel out of this derivation entirely: deck_z = race_z + horn_z - K
    # gives horn_top = deck_z + K = race_z + horn_z, which IS the pocket
    # ceiling. Exactly zero clearance, for any value of horn_z. That is why
    # raising it 1.8 -> 2.4 in August changed nothing except lowering the
    # servo 0.6 - the horn went on touching the ceiling and the rotor went on
    # riding the horn instead of its races. Jonathan, at the bench, 2026-08-30:
    # "if we put the horn on the base gear the turret plate does not touch
    # the bearings."
    #
    # The gap is subtracted HERE, where the servo is positioned, because the
    # pocket depth appears on both sides of that equation and anything folded
    # into it alone does nothing at all.
    param('horn_seat', '0.4 mm',
          'clearance between the top of the FITTED horn and the ceiling of the\n'
          '           rotor pocket. Subtracted from the deck so it cannot cancel.')
    deck_z = race_z + tval('horn_z') - val('horn_seat') - (
        val('tab_below_top') + val('tab_thk')
        + val('boss_h') + val('horn_hub_h'))
    horn_top = deck_z + (val('tab_below_top') + val('tab_thk')
                         + val('boss_h') + val('horn_hub_h'))

    # THE LEAD GROOVE TRACKS THE DECK, because the deck keeps moving and the
    # groove was a typed 1.2. Derived here, where deck_z is finally known,
    # from the same bundle top edge the assert further down tests - so the
    # number and its check cannot drift apart. Deepening the horn pocket
    # raised this servo 1.0 and the seating gap lowered it 0.4; net +0.6 put
    # the bundle straight into the plate, and the assert caught it.
    _sg0 = CATALOG['SG90']
    _cb0 = (deck_z * 10) - (_sg0.case_h - _sg0.tab_below_top - _sg0.tab_thk)
    _need_groove = _cb0 + _sg0.lead_bundle_dia * 1.5
    param('lead_groove_d', '%.4f mm' % max(1.2, _need_groove + 0.2),
          'DERIVED from the deck, not typed: deep enough for the bundle\'s TOP\n'
          '           EDGE where the servo actually sits, plus 0.2. Was 1.2, which was\n'
          '           right for a deck that has since moved twice.')
    blade_bottom = horn_top - val('horn_blade_t')
    case_bottom = deck_z - (val('case_h') - val('tab_below_top') - val('tab_thk'))
    cheek_top = tval('axle_z') + val('cheek_over')
    # the relief footprint: the bearing's own shadow plus relief_margin, and
    # never past cheek_ir, which is where the cheeks stand.
    relief_ir = roll_r - tval('roller_w') / 2 - val('relief_margin')
    relief_half = math.asin(
        (tval('roller_od') / 2 + val('relief_margin')) / roll_r)
    # THE PAD IS NOT CENTRED, so its reach is not hypot(half_x, half_y). That
    # is what this was, and it reported r 21.02 for a pad that reached 25.82.
    # With the end rounded to hub_x the furthest point is on the axis, so the
    # reach is simply the far edge - but the assertion below is written against
    # the CORNER too, because a future un-rounding must not pass silently.
    pad_far = val('shaft_off') + val('hub_y')
    hub_r = pad_far
    hub_r_square = math.hypot(val('hub_x'), pad_far)
    ROLL_AZ = (90.0, 210.0, 330.0)
    POST_AZ = (120.0, 180.0, 240.0)
    WIN_AZ = (30.0, 150.0, 270.0)

    # ---- sanity, before any geometry ----------------------------------------
    assert abs(race_z - (tval('axle_z') + tval('roller_od') / 2)) < 1e-9, (
        'tt_race_z is meant to be derived from the axle height and the 608 OD')
    # THE BEARING RUNS OVER THIS PART'S OWN BASE PLATE, not over the platter.
    # This compared the roller against z 0 and called it "the lid", and so never
    # saw the 4.0 mm plate in between. Three 608 were 3.00 mm inside it.
    _roll_bottom = tval('axle_z') - tval('roller_od') / 2
    assert _roll_bottom >= val('relief_floor') + val('relief_clear') - 1e-9, (
        'the rollers reach z %.2f and the relieved plate floor is z %.2f with '
        '%.2f of daylight wanted - raise tt_axle_z to at least %.2f'
        % (_roll_bottom * 10, val('relief_floor') * 10, val('relief_clear') * 10,
           (val('relief_floor') + val('relief_clear')
            + tval('roller_od') / 2) * 10))
    assert val('relief_floor') >= val('wall') - 1e-9, (
        'the relief leaves %.2f of plate under each roller against a %.2f '
        'minimum wall' % (val('relief_floor') * 10, val('wall') * 10))
    assert cheek_top < race_z - val('free') - 1e-9, (
        'the roller cheeks reach z %.2f and the rotor rides at %.2f - only the '
        'BEARING may touch it' % (cheek_top * 10, race_z * 10))
    assert stub_ir > hub_r + val('free'), (
        'the stub axles reach in to r %.2f and the servo pad corner is at r %.2f'
        % (stub_ir * 10, hub_r * 10))
    assert cheek_or < tval('post_r') - val('post_d') / 2 - val('wall'), (
        'the roller cheeks reach r %.2f and the posts start at r %.2f'
        % (cheek_or * 10, (tval('post_r') - val('post_d') / 2) * 10))
    assert cheek_or < tval('disc_d') / 2, (
        'the cheeks are outboard of the rotor they carry')
    assert tval('post_r') - val('post_d') / 2 > tval('disc_d') / 2 + val('free'), (
        'the mounting posts at r %.2f foul the rotor at r %.2f' % (
            (tval('post_r') - val('post_d') / 2) * 10, tval('disc_d') / 2 * 10))
    assert val('collar_d') < val('race_od') - 1e-9, (
        'the %.1f collar is wider than the %.1f inner race, so it lands on the ZZ '
        'shield and the bearing drags instead of rolling'
        % (val('collar_d') * 10, val('race_od') * 10))
    assert val('collar_d') > tval('axle_d') + 2 * 0.1, (
        'the collar barely clears the axle - there is nothing for the race to sit on')
    assert tval('axle_d') < val('washer_od') < val('race_od') - 1e-9, (
        'the retaining washer must be wider than the %.1f bore and narrower than '
        'the %.1f inner race; %.1f is not'
        % (tval('axle_d') * 10, val('race_od') * 10, val('washer_od') * 10))
    assert blade_bottom >= race_z - 1e-9, (
        'the horn blade bottoms at z %.2f and the rotor face is at %.2f - the blade '
        'never enters the cross pocket and the yaw servo drives nothing'
        % (blade_bottom * 10, race_z * 10))
    # STRICTLY LESS, BY THE SEATING GAP. The old form was <= and passed at
    # exact equality - which is precisely the state that got printed: horn top
    # flush with the pocket ceiling, nothing left for a horn 0.1 thicker than
    # its datasheet or a pocket 0.1 shallow off the printer.
    _gap = (race_z + tval('horn_z')) - horn_top
    assert _gap >= val('horn_seat') - 1e-9, (
        'only %.2f mm between the horn top and the rotor pocket ceiling, and '
        '%.2f is wanted - the rotor rests on the horn, not on its rollers'
        % (_gap * 10, val('horn_seat') * 10))

    # AND THE BLADE MUST REACH INTO THE SLOT FAR ENOUGH TO DRIVE IT. Read
    # conservatively: blade sitting ON the collar with the hub proud above it,
    # which is lib/gears.py's reading of the same horn. If the other reading
    # is right there is MORE engagement than this asserts, never less.
    _blade_lo = horn_top - val('horn_hub_h')
    _blade_hi = _blade_lo + val('horn_blade_t')
    _engage = min(_blade_hi, race_z + tval('horn_z')) - max(_blade_lo, race_z)
    assert _engage >= val('horn_blade_t') - 1e-9, (
        'only %.2f mm of the %.2f blade is inside the rotor cross pocket - '
        'that is all there is to turn the whole arm with'
        % (_engage * 10, val('horn_blade_t') * 10))
    assert val('axle_len') > tval('roller_w'), (
        'the stub is shorter than the bearing - the washer would clamp the axle end')
    assert deck_z > plate_t + 1e-9, (
        'the servo deck at z %.2f is inside the base plate' % (deck_z * 10))
    assert case_bottom > -15.9 + 1e-9, (
        'the SG90 case bottom reaches z %.2f below the platter rim; the legacy '
        'column bottoms out around -15.9' % (case_bottom * 10))
    assert val('window_or') < tval('post_r') - val('post_d') / 2 - val('wall'), (
        'the lightening windows run into the mounting posts')
    assert val('window_ir') > hub_r, 'the lightening windows undercut the servo pad'

    # ---- phase 1: stator form -------------------------------------------------
    t0 = design.timeline.count
    xy_ring('base_plate', val('plate_or'), val('plate_ir'), '0.0 mm',
            PREFIX + 'plate_t', NEW)
    # The servo pad: a raised slab the tabs bear on, standing on the plate.
    # Its OUTBOARD end is a semicircle of radius hub_x, not a square corner.
    # With the +5.20 shaft offset a square corner reaches r 25.82, inside the
    # roller band at r 23.50, and the relief cut below would undercut the very
    # pad it stands on. Rounded, the furthest point is on the axis at r 21.60.
    _soff = val('shaft_off')
    _pad_flat = _soff + val('hub_y') - val('hub_x')
    xy_rect('servo_pad', -val('hub_x'), val('hub_x'),
            _soff - val('hub_y'), _pad_flat,
            mm(plate_t - 0.1), mm(deck_z - plate_t + 0.1), JOIN)
    xy_circle('servo_pad_end', 0.0, _pad_flat, val('hub_x') * 2,
              mm(plate_t - 0.1), mm(deck_z - plate_t + 0.1), JOIN)
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        xy_circle('post_%d' % i, tval('post_r') * math.cos(a),
                  tval('post_r') * math.sin(a), val('post_d'),
                  '0.0 mm', mm(post_top), JOIN)
    for i, az in enumerate(ROLL_AZ):
        a = math.radians(az)
        # the cheek: a tangential slab standing outboard of its roller
        sk = sketch(comp.xYConstructionPlane, 'cheek_%d' % i)
        pts = []
        for rr, tt in ((cheek_ir, -val('cheek_w') / 2), (cheek_or, -val('cheek_w') / 2),
                       (cheek_or, val('cheek_w') / 2), (cheek_ir, val('cheek_w') / 2)):
            pts.append((rr * math.cos(a) - tt * math.sin(a),
                        rr * math.sin(a) + tt * math.cos(a)))
        lines = sk.sketchCurves.sketchLines
        for k in range(4):
            lines.addByTwoPoints(mxy(sk, pts[k][0], pts[k][1]),
                                 mxy(sk, pts[(k + 1) % 4][0], pts[(k + 1) % 4][1]))
        extrude(one(sk), JOIN, '0.0 mm', mm(cheek_top), 'cheek_%d' % i)
    group(t0, PH_FORM)

    # ---- phase 2: rollers ------------------------------------------------------
    t1 = design.timeline.count
    for i, az in enumerate(ROLL_AZ):
        a = math.radians(az)
        # stub axle, pointing INWARD from the cheek; then the collar step on it
        radial_cyl('stub_%d' % i, a, cheek_or, stub_ir, tval('axle_d'), JOIN)
        radial_cyl('collar_%d' % i, a, cheek_ir, seat_r, val('collar_d'), JOIN)
        radial_cyl('axle_pilot_%d' % i, a, stub_ir,
                   stub_ir + val('axle_screw_z'), val('axle_pilot'), CUT)
    # THE RELIEF. Each 608 hangs into the base plate; this floors the plate to
    # MIN_WALL under it and no further. It stops AT cheek_ir, so the cheeks
    # keep their whole footing and only the span between them is thinned.
    _vol_before = comp.bRepBodies.item(0).volume
    for i, az in enumerate(ROLL_AZ):
        xy_arc('roller_relief_%d' % i, relief_ir, cheek_ir, math.radians(az),
               relief_half, mm(val('relief_floor')),
               mm(plate_t - val('relief_floor') + 1.0), CUT)
    # PLAYBOOK: when a CUT changes nothing, the cut is in the wrong place.
    _vol_after = comp.bRepBodies.item(0).volume
    assert _vol_before - _vol_after > 1e-4, (
        'the three roller reliefs removed %.3f mm3 - the cut is in the wrong '
        'place or at the wrong scale' % ((_vol_before - _vol_after) * 1000))
    group(t1, PH_ROLLERS)

    # ---- phase 3: yaw servo -----------------------------------------------------
    t2 = design.timeline.count
    _soff = val('shaft_off')
    xy_rect('case_aperture',
            -(val('case_w') + val('loc')) / 2, (val('case_w') + val('loc')) / 2,
            _soff - (val('case_l') + val('loc')) / 2,
            _soff + (val('case_l') + val('loc')) / 2,
            mm(-1.0), mm(deck_z + 1.0), CUT)
    # LEAD KEYWAY: ONE notch, centred, in the aperture's shaft-end END wall,
    # running OUT through the servo pad to daylight. The bundle leaves the
    # case's SHORT END FACE at the shaft end, dead centre across the width
    # (lib/servo.py lead datum), and the whole case travels this aperture on
    # the way down - so the cable's exit point sweeps the full aperture
    # height and the notch is cut through it, z -1.0 to deck_z.
    #
    # The two ±X side-wall notches this replaces were sited from a misreading
    # of lead_x. They also cut past the pad's own half-width (hub_x 9.0 <
    # 9.8), severing it across its full width over 6 mm of its length.
    #
    # COST, and it is a real one: this notch destroys servo_pilot_0, the NEAR
    # tab's screw pilot. The pilot is at (x 0, y _soff - tab_pitch/2), dead on
    # the notch's centreline, and lead_y = 0 means the notch cannot be moved
    # off it. The servo keeps ONE tab screw. Decided with Jonathan 2026-08-28:
    # the aperture is cut to case + loc so it carries the sideways load, and
    # the horn is bolted to the platter above, so the near end cannot lift far
    # on one screw. A separate bridge cap carrying the second screw remains
    # possible later without changing this part.
    _shaft_y = _soff - val('case_l') / 2          # the near/shaft end face
    xy_rect('lead_key',
            -val('lead_key_d') / 2, val('lead_key_d') / 2,
            _shaft_y - val('lead_key_l'), _shaft_y + val('loc') / 2,
            mm(-1.0), mm(deck_z + 1.0), CUT)
    # the lead groove: from just before the case's far end face out past the
    # escape run, cut up into the plate underside so the bundle's top edge
    # keeps daylight. Volume-drop asserted below.
    # LEAD GROOVE, re-sited with the keyway. "At z -1.0 the bundle is already
    # below the plate" was true of its CENTRE and wrong about the bundle: its
    # top edge is at -1.0 + 3.4/2 = +0.7, and the plate starts at 0. So it
    # grazes 0.7 into the plate over the run between the pad and the cable
    # window - which is what the +Y groove was for, at the wrong end.
    # From the CASE END FACE, not from the end of the keyway: the plate's
    # inner rim starts at r plate_ir, which is inboard of where the keyway
    # ends, so a groove that began at the keyway left 2.15 mm of unrelieved
    # plate over the bundle. The gate read it as 0.98 mm3 still solid.
    _v_groove = comp.bRepBodies.item(0).volume
    _g_a = _shaft_y + 0.1
    _g_b = _g_a - val('lead_key_l') - val('lead_escape')
    xy_rect('lead_groove',
            -val('lead_groove_w') / 2, val('lead_groove_w') / 2,
            min(_g_a, _g_b) - 0.1, max(_g_a, _g_b) + 0.1,
            # mm() takes CENTIMETRES, so mm(-0.1) is -1.0 mm and the distance
            # has to carry that back: groove_d + 1.0 lands the roof at
            # +groove_d. Written as groove_d + 0.1 it stopped at z +0.3 and
            # left the bundle's top 0.4 mm still buried in the plate.
            mm(-0.1), PREFIX + 'lead_groove_d + 1.0 mm', CUT)
    _g_drop = (_v_groove - comp.bRepBodies.item(0).volume) * 1000
    # ceiling over the cut's FULL span; the plate's inner rim and the cable
    # window are both void along part of it, so the real drop is well under.
    _g_full = (val('lead_groove_w') * 10) * (val('lead_groove_d') * 10) \
        * ((val('lead_key_l') + val('lead_escape') + 0.2) * 10)
    assert 1.0 < _g_drop < _g_full, (
        'the lead groove removed %.1f mm3 against a %.1f ceiling - it is not '
        'cutting where the plate is' % (_g_drop, _g_full))
    assert val('plate_t') - val('lead_groove_d') >= val('wall'), (
        'the lead groove leaves less than a wall of plate above it')
    # deep enough for the bundle's TOP EDGE, not its centre - the distinction
    # that made this groove necessary in the first place.
    _sg = CATALOG['SG90']
    _case_bot_z = (deck_z * 10) - (_sg.case_h - _sg.tab_below_top - _sg.tab_thk)
    _lead_top = _case_bot_z + _sg.lead_bundle_dia + _sg.lead_bundle_dia / 2
    assert val('lead_groove_d') * 10 >= _lead_top, (
        'the bundle\'s top edge reaches z %+.2f and the groove is only %.2f '
        'deep - the lead is pinched against the plate on its way out'
        % (_lead_top, val('lead_groove_d') * 10))
    #
    # ONE pilot, not two - the near one stood where the cable has to travel.
    # See the keyway note above for why that is unavoidable and what it costs.
    xy_circle('servo_pilot_far', 0.0, _soff + val('tab_pitch') / 2,
              val('pilot_d'),
              mm(deck_z - val('pilot_depth')), PREFIX + 'pilot_depth', CUT)
    _near_pilot_y = (_soff - val('tab_pitch') / 2) * 10
    _key_y0 = (_shaft_y - val('lead_key_l')) * 10
    assert _key_y0 <= _near_pilot_y <= (_shaft_y + val('loc') / 2) * 10, (
        'the near pilot at y %.2f is NOT inside the keyway span %.2f..%.2f - '
        'if it has moved clear, restore it rather than leaving the servo on '
        'one screw' % (_near_pilot_y, _key_y0, (_shaft_y + val('loc') / 2) * 10))
    # THE WHOLE POINT: the shaft has to be ON the axis.
    _shaft_y_mm = (_soff - val('case_l') / 2 + val('shaft_from_end')) * 10
    assert abs(_shaft_y_mm) < 1e-6, (
        'the SG90 output shaft lands at y %.3f mm and J1 turns about y = 0 - '
        'the horn would drive the rotor as a crank' % _shaft_y_mm)
    assert val('hub_y') * 10 >= val('tab_pitch') / 2 * 10 + 1.6, (
        'the servo pad is %.1f mm long each way and the pilots are at +-%.1f - '
        'a pilot falls off the pad'
        % (val('hub_y') * 10, val('tab_pitch') / 2 * 10))
    group(t2, PH_SERVO)

    # ---- phase 4: platter interface ----------------------------------------------
    t3 = design.timeline.count
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        xy_circle('bolt_%d' % i, tval('post_r') * math.cos(a),
                  tval('post_r') * math.sin(a), tval('bolt_d'),
                  mm(-1.0), mm(post_top + 2.0), CUT)
    for i, az in enumerate(WIN_AZ):
        xy_arc('window_%d' % i, val('window_ir'), val('window_or'),
               math.radians(az), val('window_deg') / 2, mm(-1.0),
               mm(plate_t + 2.0), CUT)
    # the loom window - cut LAST so it reads as a hole in a finished plate.
    # NOTE val() on an ANGLE parameter returns RADIANS, not degrees. xy_arc
    # wants radians, so they go straight in; only the printout converts.
    _c_ir = val('cable_ir') * 10
    _c_or = val('cable_or') * 10
    # the well now reaches as far as the KEYWAY, not the aperture - deriving
    # this from the aperture again would leave the guard checking the wrong
    # number by the length of the keyway.
    _well_half_y = abs(val('shaft_off') - val('case_l') / 2
                       - val('lead_key_l')) * 10
    assert _c_ir >= _well_half_y + 1.6, (
        'the cable window starts at r %.1f mm and the servo well, keyway '
        'included, reaches %.1f mm - less than a wall between them'
        % (_c_ir, _well_half_y))
    _race_ir_mm = tval('race_ir') * 10 if ups.itemByName(TURRET + 'race_ir') else 23.0
    assert _c_or + 1.6 <= _race_ir_mm, (
        'the cable window reaches r %.1f mm and the race band starts at %.1f mm'
        % (_c_or, _race_ir_mm))
    xy_arc('cable_window', val('cable_ir'), val('cable_or'),
           val('cable_az'), val('cable_deg') / 2.0,
           '-1.0 mm', PREFIX + 'plate_t + 2.0 mm', CUT)
    group(t3, PH_FIX)

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a cheek, post or the servo pad is not touching '
        'the base plate' % comp.bRepBodies.count)
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
    print('body: %r | material: %s | appearance: %s' % (body.name, body.material.name, used))
    print('DATUM: z 0 is the printed platter rim top (its z 42.00, MEASURED)')
    print('base plate r %.1f..%.1f x %.1f, 3 posts r %.1f dia %.1f to z %.2f' % (
        val('plate_ir') * 10, val('plate_or') * 10, plate_t * 10,
        tval('post_r') * 10, val('post_d') * 10, post_top * 10))
    print('rollers: 3 x 608ZZ at r %.1f, az %s, axles RADIAL at z %.2f' % (
        roll_r * 10, ROLL_AZ, tval('axle_z') * 10))
    print('  stub %.2f dia from r %.2f to %.2f past a %.1f collar %.2f proud' % (
        tval('axle_d') * 10, cheek_or * 10, stub_ir * 10,
        val('collar_d') * 10, tval('collar_h') * 10))
    print('  cheeks r %.2f..%.2f, top z %.2f (rotor rides at %.2f)' % (
        cheek_ir * 10, cheek_or * 10, cheek_top * 10, race_z * 10))
    print('RACE FACE z %.2f = axle %.2f + 608 OD/2. Rotor rim top %.2f, ring under '
          '%.2f.' % (race_z * 10, tval('axle_z') * 10,
                     (race_z + tval('disc_t')) * 10, ring_under * 10))
    print('J1 HORN STACK: deck %.2f, horn top %.2f, pocket ceiling %.2f -> '
          '%.2f of seating' % (deck_z * 10, horn_top * 10,
                               (race_z + tval('horn_z')) * 10, _gap * 10))
    print('  blade %.2f..%.2f against a rotor face at %.2f: %.2f mm of it is in '
          'the slot' % (_blade_lo * 10, _blade_hi * 10, race_z * 10, _engage * 10))
    print('SG90: tabs bear at z %.2f, case bottom z %.2f (into the platter column)'
          % (deck_z * 10, case_bottom * 10))
    print('  horn blade z %.2f..%.2f sits IN the rotor cross pocket z %.2f..%.2f'
          % (blade_bottom * 10, horn_top * 10, race_z * 10,
             (race_z + tval('horn_z')) * 10))
    print('  bearing seat: %.1f collar on a %.1f inner race, retained by a %.1f '
          'washer (NOT a standard M3 Ø7 - it falls through the Ø8 bore)'
          % (val('collar_d') * 10, val('race_od') * 10, val('washer_od') * 10))
    print('  SHAFT ON AXIS: case centre offset %+.2f in Y so the output shaft'
          % (val('shaft_off') * 10))
    print('    lands at y 0. The SG90 shaft is %.1f from the near end of a %.1f'
          % (val('shaft_from_end') * 10, val('case_l') * 10))
    print('    case, so centring the CASE would put it %.1f mm off the J1 axis.'
          % (val('shaft_off') * 10))
    print('  ONE pilot %.1f at y %+.1f (FAR tab). The near tab at y %+.1f has '
          'no screw:' % (val('pilot_d') * 10,
                         (val('shaft_off') + val('tab_pitch') / 2) * 10,
                         (val('shaft_off') - val('tab_pitch') / 2) * 10))
    print('    the lead keyway runs straight through it and lead_y = 0 means '
          'it cannot')
    print('    be moved aside. Pocket carries the load, horn holds the near '
          'end down.')
    print('  LEAD KEYWAY %.1f wide, centred, END wall at y %+.1f, out to y %+.1f'
          % (val('lead_key_d') * 10,
             (val('shaft_off') - val('case_l') / 2) * 10,
             (val('shaft_off') - val('case_l') / 2 - val('lead_key_l')) * 10))
    print('  pad %.0f x %.0f centred y %+.2f'
          % (val('hub_x') * 20, val('hub_y') * 20, val('shaft_off') * 10))
    print('CABLE WINDOW: r %.1f..%.1f, %.0f deg at az %.0f - the fixed half of the'
          % (val('cable_ir') * 10, val('cable_or') * 10,
             val('cable_deg') * 180 / math.pi, val('cable_az') * 180 / math.pi))
    print('  loom route. The servo well is %.2f x %.2f on a %.2f x %.2f case,'
          % (val('case_w') * 10 + val('loc') * 10, val('case_l') * 10 + val('loc') * 10,
             val('case_w') * 10, val('case_l') * 10))
    print('  so NOTHING could pass beside the servo - 15 leads cross J1 here.')
    print('  base_lid repeats it below; shoulder_bracket\'s window is the moving half.')
    print('ONE M3 per post: ring -> post -> platter insert. 3 screws hold the turret.')
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 1000 * 0.6, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
