"""robotarm/gripper_shell - Fusion MCP generating script.

Rebuilds `robotarm_gripper_shell` (idempotent). Specs:
specs/robotarm/gripper_shell.md, styled per specs/robotarm/_style.md.

Local frame IS the gripper assembly frame, with this half occupying z >= 0:
  x  jaw opening direction, 0 on the centre plane
  y  forward along the arm; the pinion axis and the SG90 shaft lie on it
  z  the clamshell split axis; z = 0 is the split face

ONE printed design, TWO copies, the second TURNED OVER - rotated 180 deg
about Y, (x, y, z) -> (-x, y, -z). Everything is therefore symmetric in x,
INCLUDING the servo mount, which the SG90 itself is not: its shaft sits
6.1 mm from one end of a 22.6 mm case, so about the shaft its tabs land at
-11.0..-6.1 and +16.5..+21.4. The case pocket is cut to the SYMMETRIC
half-width 16.5 mm - the union of that layout and its mirror - and only the
far tab is slotted, on both sides. The servo goes in either way round, the
near tab lands in open pocket, and one design serves both halves.

The servo takes NO screws: its far tab is trapped in x and y by the slot and
in z by the two halves closing.

FORM (specs/robotarm/_style.md). The outer shape is built FIRST, as one
shaped solid - plan polygon, R4 on every vertical corner, a 4 mm 45 deg
facet round the top - and the mechanism is cut into it afterwards. Doing it
the other way round chamfers every pocket edge and yields a slab with round
holes. The split face is the widest line of the form and both halves bevel
away from it, so the assembled hand reads as one faceted volume with a crisp
centre line. The tall front block steps down to a narrower, shorter tail
that tapers into the wrist.

THE FRONT IS AN OPEN MOUTH, and that is forced, not chosen. A front wall
over the rack channel would have to live between y = 4.125 and 4.4 - 0.275
mm - because the jaw arm sweeps everything forward of the channel across the
shell's whole height. The rack is held down by the top plate, back by the
channel's rear wall, and in mesh by the pinion; nothing pushes it forward
but its own weight. The reference image's hand is an open mouth too.

Print orientation: SPLIT FACE (z = 0) ON THE BED, built in +z. No support.

The SHARED gr_* block is defined identically in gripper_pinion.py and
gripper_rack_jaw.py; sty_* comes from _style.md. Servo dimensions are
DATASHEET (lib/servo.py) - gauge the tab plate before printing this.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_gripper_shell'
BODY_NAME = 'gripper_shell'
PREFIX = 'gs_'
SHARED = 'gr_'
WRIST = 'wr_'       # J4 clevis contract - shared with wrist_hub / wrist_fork
STYLE = 'sty_'
PH_FORM = 'outer form'
PH_MOUTH = 'mouth, rack channel and pinion'
PH_SERVO = 'servo bay'
PH_FASTEN = 'fasteners'
PH_FINISH = 'finish'
PH_EFFECTOR = 'effector bolts'
PHASES = [PH_FORM, PH_MOUTH, PH_SERVO, PH_FASTEN, PH_FINISH, PH_EFFECTOR]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. The shell is a body, so it is light.
# Matched as sets of substrings, best first, against every appearance in
# every loaded library.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('gripper_shell')


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

    def shared(name, expr, comment='', units='mm'):
        _set(SHARED + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def wrist(name, expr, comment='', units='mm'):
        _set(WRIST + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def sval(name):
        return ups.itemByName(SHARED + name).value

    def tval(name):
        return ups.itemByName(STYLE + name).value

    # --- SHARED gear contract: identical to the other two gripper scripts --
    shared('module', '1.5 mm', 'gear module - design_rules GEAR_PREFERRED_MODULE_MM')
    shared('teeth', '12', 'pinion tooth count - gears_drives.md floor at 20 deg PA', '')
    shared('ded_f', '1.25', 'dedendum factor, standard full-depth tooth', '')
    shared('face', '8.0 mm', 'face width, >= 5 x module - design_rules')
    shared('backlash', '0.2 mm', 'backlash added at the centre distance - design_rules')
    shared('r_pitch', SHARED + 'module * ' + SHARED + 'teeth / 2', 'derived pitch radius')
    shared('r_tip', SHARED + 'r_pitch + ' + SHARED + 'module', 'derived pinion tip radius')
    shared('offset', SHARED + 'r_pitch + ' + SHARED + 'backlash', 'pinion axis to rack PITCH LINE')
    shared('stroke', '20.0 mm', 'travel of ONE rack; jaw opening is twice this')
    shared('rack_web', '3.5 mm', 'rack back thickness above the tooth root')
    shared('rack_back', SHARED + 'module * ' + SHARED + 'ded_f + ' + SHARED + 'rack_web',
           'derived rack back, above the pitch line - the channel floor rides on this')
    shared('blade_half', '8.0 mm', 'how far a blade reaches PAST the gripper centre plane')

    # --- STYLE: specs/robotarm/_style.md, shared by every part -------------
    style('facet', '4.0 mm', '45 deg chamfer on outer edges - _style.md rule 1')
    style('radius', '6.0 mm',
          'plan-view corner radius - _style.md rule 2. MUST exceed sty_facet: a\n           chamfer equal to the radius it runs into fails outright')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- fits ---------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('slide', '0.25 mm', 'sliding fit, rack in channel - design_rules CALIBRATED')
    param('free', '0.4 mm', 'free fit, must never bind - design_rules')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('case_gap', PREFIX + 'free',
          'running gap between the pinion BACK FACE and the SG90 case top.\n'
          '           The pinion ROTATES relative to that case, so it cannot sit on\n'
          '           it; this is design_rules JOINT_FIT_MM free, which is what\n'
          '           lib/servo_hub seats every spline hub at and what\n'
          '           gripper_pinion.py declares as gp_case_gap. Edit neither here.')

    # --- outer form ---------------------------------------------------------
    param('x', '24.0 mm', 'half width at the hand; also half the channel guide length')
    param('rear_x', '20.0 mm', 'half width where the tail meets the wrist - _style.md rule 3')
    param('front_y', '8.0 mm', 'front face: a brow over the jaws')
    param('mid_y', '-12.0 mm', 'where the hand steps down to the tail')
    param('back_y', '-34.5 mm', 'back face, 2.6 mm behind the servo')
    param('chan_z', SHARED + 'offset + ' + SHARED + 'rack_back + ' + PREFIX + 'slide / 2',
          'derived channel floor: where the rack back rides')
    param('half_z', PREFIX + 'chan_z + ' + PREFIX + 'wall', 'derived shell half height')
    param('chan_y', SHARED + 'face / 2 + ' + PREFIX + 'slide / 2', 'derived channel half width')
    param('pin_r', SHARED + 'r_tip + ' + PREFIX + 'free', 'derived pinion recess radius')
    param('pin_y', SHARED + 'face / 2 + ' + PREFIX + 'free', 'derived pinion recess half width')

    # --- SG90, DATASHEET (lib/servo.py) --------------------------------------
    param('case_l', '22.7 mm', 'SG90 case length - DATASHEET (TowerPro B)')
    param('case_w', '12.2 mm', 'SG90 case width - DATASHEET (TowerPro D; was 12.6)')
    param('case_h', '23.7 mm', 'SG90 case height - DATASHEET')
    param('shaft_end', '6.1 mm', 'shaft axis to the NEAR end of the case - DATASHEET')
    param('tab_span', '32.3 mm', 'SG90 tab tip to tab tip - DATASHEET (TowerPro E)')
    param('tab_thk', '2.4 mm', 'SG90 mounting tab thickness - DATASHEET')
    param('tab_plane', '17.0 mm', 'case bottom to the tab UNDERSIDE - DATASHEET')
    param('boss_h', '4.2 mm', 'output boss height above the case top - DATASHEET')
    # THE PINION PLANE IS NO LONGER y = 0, AND THIS IS THE WHOLE OF THE
    # HORN MIGRATION AS IT LANDS ON THIS PART. gripper_pinion.py used to
    # perch its back face on the horn blade at the OUTPUT BOSS TOP, servo-z
    # 10.90. It now bores THROUGH the boss and seats one running gap off the
    # case top, servo-z 7.10 - so the pinion, and both rack channels that
    # mesh on its plane, come 3.80 mm TOWARD THE CASE. The 3.80 is not typed:
    # it is boss_h 4.20 minus the case_gap 0.40 that replaces it, so if
    # either moves this follows.
    #
    # THE SERVO BAY DOES NOT MOVE. gs_case_top comes out at -8.20 exactly as
    # before, because it is now derived BACK from the gear plane instead of
    # the gear plane being pinned to y = 0. That is deliberate: back_y, the
    # tail cavity, both lead notches and the tab slots are all sited off the
    # case, and the alternative - holding the pinion at y = 0 and walking the
    # servo forward - would have moved every one of them and shortened the
    # shell by 3.80 for no reason anyone asked for.
    param('gear_y', '-(' + PREFIX + 'boss_h - ' + PREFIX + 'case_gap)',
          'derived: the pinion MID plane, and with it both rack channels. It is\n'
          '           -3.80 - how far the pinion dropped toward the servo when its bore\n'
          '           started swallowing the Oe5.0 output boss instead of perching on\n'
          '           it. gripper_pinion.py gp_seat_z 10.90 -> 7.10 is the same move,\n'
          '           measured up the servo instead of along the arm.')
    param('case_top', PREFIX + 'gear_y - ' + SHARED + 'face / 2 - ' + PREFIX + 'case_gap',
          'derived: the pinion back face sits one running gap off the case top,\n'
          '           and the case top is that much further back again. NOT the horn\n'
          '           stack it replaces - there is no horn and no blade in this\n'
          '           machine any more. Comes out at the SAME -8.20 it always was.')
    param('case_bot', PREFIX + 'case_top - ' + PREFIX + 'case_h', 'derived case bottom')
    param('case_far', PREFIX + 'case_l - ' + PREFIX + 'shaft_end', 'derived shaft to the FAR case end')
    param('tab_over', '(' + PREFIX + 'tab_span - ' + PREFIX + 'case_l) / 2',
          'derived: how far one tab stands out past the case')
    param('tab_lo', PREFIX + 'case_bot + ' + PREFIX + 'tab_plane', 'derived tab underside')
    param('lead_slot', '5.0 mm',
          'back-wall notch for the servo lead. Sited OUTBOARD of the case\n'
          '           end, not on the shaft axis and not straddling the end face -\n'
          '           see the lead datum in lib/servo.py')
    param('lead_notch_x', PREFIX + 'shaft_end + ' + PREFIX + 'lead_slot / 2 + '
          + PREFIX + 'loc / 2',
          'derived: notch centre. Half a locational fit past the case end\n'
          '           face, so the slot\'s inner edge lands on it and the whole slot\n'
          '           is clear of the case body.')
    param('srv_roof', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2 + ' + PREFIX + 'wall',
          'derived: floor of the tail cavity, one wall above the servo')
    param('pocket_inset', '2.5 mm',
          'wall left around the tail cavity - _style.md: the styling may not cost\n           payload, so the facets and the thicker jaws are paid for here')

    # --- J5 wrist ROLL: the gripper bolts FLAT to the rotator ---------------
    # Four attempts at this interface, and 6 DOF is what settles it. With a
    # ROLL joint between the pitch fork and the hand, the fork straddles a
    # narrow roll housing instead of this 48 mm hand - so the gripper needs no
    # ears, no trunnions and no barrel. It bolts to the rotator's face and
    # turns with it.
    #
    # Each shell carries TWO of the four bolts, at +z; turned over it supplies
    # the other two at -z.
    param('eff_bolt_x', '11.0 mm',
          'effector bolt pattern - asm_eff_bolt_x. Small, because the pattern\n           has to fit a rotator that SPINS: every mm of pattern is 2 mm of\n           swept diameter. The load is trivial - 1 N per bolt.')
    param('eff_bolt_z', '9.0 mm', 'effector bolt pattern - asm_eff_bolt_z')
    param('back_wall', '2.6 mm', 'back wall the effector bolts pass through')

    # --- fasteners -----------------------------------------------------------
    param('bolt_d', '3.4 mm', 'M3 clearance - design_rules FASTENER_MM')
    param('bolt_x', '19.0 mm', 'clamshell bolts, +/- this in x')
    # DERIVED NOW, AND IT HAD TO BE. It was a typed -8.00, which sat 3.88 mm
    # behind a channel whose rear wall was at -4.125. With the channel 3.80
    # further back its rear wall is at -7.925 and a Oe3.4 hole centred on
    # -8.00 breaks INTO the channel over 1.63 mm - the rack would run past an
    # open bolt hole. So the bolt is now placed off the channel it has to
    # clear rather than typed beside where the channel used to be.
    param('bolt_y1',
          PREFIX + 'gear_y - ' + PREFIX + 'chan_y - ' + PREFIX + 'wall - '
          + PREFIX + 'bolt_d / 2',
          'front clamshell bolt: one wall behind the rack channel\'s rear face.\n'
          '           It moves with gs_gear_y - see the note there. It crosses gs_mid_y\n'
          '           into the taper, which is fine (the tail is one joined solid and\n'
          '           still 23.8 wide there) and is checked below.')
    param('bolt_y2', '-24.0 mm',
          'rear clamshell bolt - ALSO the wrist interface: the bracket ears clamp '
          'the tail on these two, so an effector swap needs no extra fastener')
    # gs_pocket_x IS GONE, WITH THE POCKET IT SIZED. rear_rail_pocket
    # lightened the RAIL - the band of solid material between the rack
    # channel's rear wall and the servo bay behind it, most of it the servo
    # bay's roof. It was 4.68 mm deep in y and took ~1.3 cm3 out of a part
    # that carries almost nothing there.
    #
    # THE 3.80 DROP TOOK THE RAIL, NOT JUST THE POCKET. The channel's rear
    # wall moved from y -4.125 to -7.925 and the SG90 case top is at -8.20,
    # so what is left between them is 0.275 mm - 0.175 after the pocket's
    # locational fit. There is no rail any more, and a pocket inset one wall
    # into each side of it came out 0.88 mm wide: under MIN_FEATURE_MM 0.8's
    # useful range, and at the split face a 0.88 mm LAND between two cuts
    # that each want a 0.4 chamfer. That is what failed the build -
    # ASM_BL_UNFIN_SHEET on split_face_chamfer - and shrinking the chamfer to
    # fit a sliver would have been dressing a vestige rather than removing
    # it. So the pocket is deleted. The 0.6 g it used to save is real and
    # this costs it; the alternative is an unprintable feature.
    param('max_bridge', '40.0 mm', 'longest clean unsupported bridge - design_rules')
    param('min_feature', '0.8 mm',
          'smallest positive feature this printer makes - design_rules\n'
          '           MIN_FEATURE_MM, CALIBRATED. Used to prove no LAND at the\n'
          '           split face is too thin to carry its sty_ef chamfer.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild ------------------------------------------------
    # RENAME FIRST, THEN DELETE. Deleting a component's LAST occurrence orphans
    # the component: it drops straight out of allComponents while still holding
    # its name, so a rename afterwards cannot reach it and the rebuild is handed
    # 'robotarm_x (1)'. Every lookup by name then misses. See fusion/PLAYBOOK.md.
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
    chf = comp.features.chamferFeatures
    fil = comp.features.filletFeatures

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
            # Without this a CUT eats every other component in the document -
            # feature operations take part with everything they intersect,
            # across component boundaries. See fusion/PLAYBOOK.md.
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

    def polygon(name, pts, z0_expr, dz_expr, op):
        """Closed plan polygon in the XY plane, extruded along Z."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(mpt(sk, a[0], a[1], 0), mpt(sk, b[0], b[1], 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def box(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        return polygon(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0_expr, dz_expr, op)

    def bore(name, x_cm, y_cm, r_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_cm, y_cm, 0), r_cm)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def bore_y(name, x_cm, z_cm, r_cm, y0_expr, dy_expr, op):
        """A hole along Y - the effector bolts pull along the arm's axis."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_cm, 0, z_cm), r_cm)
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    def edges_in_plane_z(z_pick):
        tol = val('tol')
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if abs(eb.minPoint.z - z_pick) < tol and abs(eb.maxPoint.z - z_pick) < tol:
                col.add(e)
        return col

    def vertical_edges():
        """Every straight edge running along Z - on a plain prism these are
        exactly the plan-view corners. Geometric selection, so it survives a
        parameter change reordering the B-rep."""
        tol = val('tol')
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            p1 = e.startVertex.geometry
            p2 = e.endVertex.geometry
            if (abs(p1.x - p2.x) < tol and abs(p1.y - p2.y) < tol
                    and abs(p1.z - p2.z) > tol):
                col.add(e)
        return col

    # ---- values in cm -------------------------------------------------------
    x_half = val('x')
    rear_x = val('rear_x')
    front_y = val('front_y')
    mid_y = val('mid_y')
    back_y = val('back_y')
    gear_y = val('gear_y')
    chan_y = val('chan_y')
    pin_r = val('pin_r')
    pin_y = val('pin_y')
    case_top = val('case_top')
    case_bot = val('case_bot')
    case_far = val('case_far')
    tab_over = val('tab_over')
    tab_lo = val('tab_lo')
    loc = val('loc')
    facet = tval('facet')
    # The servo pocket's CEILING, taken flush to the rack channel's rear
    # wall rather than one locational fit over the case top - see the cut.
    srv_front = gear_y - chan_y
    bolt_r = val('bolt_d') / 2
    bolt_x = val('bolt_x')

    assert chan_y < pin_y, 'the pinion recess must be at least as wide as the rack channel'
    assert case_far + tab_over < x_half, 'the servo tabs stick out past the shell'

    # ---- WHAT THE 3.80 DROP HAD TO BE CHECKED AGAINST ----------------------
    # Everything that keys off the pinion plane, asserted rather than hoped
    # for. The drop is small and it is entirely toward the servo, so it is
    # the REAR of the mechanism that runs out of room, never the front.
    chan_rear = gear_y - chan_y

    # ---- SPLIT-FACE LANDS: ZERO, OR THICK ENOUGH TO CHAMFER ---------------
    # THIS IS THE CHECK THAT WAS MISSING, AND IT COST A BUILD. Phase 5
    # chamfers EVERY edge in the plane z = 0 at sty_ef 0.4. Two cuts that
    # both open on the split face and stop a hair apart leave a LAND that has
    # to carry two of those chamfers, and Fusion fails the WHOLE feature -
    # "3 : Chamfer2 / Compute Failed // ASM_BL_UNFIN_SHEET" on
    # split_face_chamfer - rather than the one edge that cannot take it. The
    # -3.80 gear-plane drop left two such lands (0.175 mm between the rack
    # channel and the servo pocket, 0.88 mm across rear_rail_pocket) and the
    # build died 130 lines below here with nothing pointing back at gs_gear_y.
    #
    # These are the Y lands, because gs_gear_y is what moves things in Y.
    # A land may be NEGATIVE (the two cuts overlap and merge, no edge) or
    # ZERO (they meet flush, one edge) or at least MIN_FEATURE_MM. It may not
    # be a sliver in between.
    for _nm, _gap in (
            ('servo pocket ceiling to rack channel rear',
             chan_rear - srv_front),
            ('rack channel rear to the front clamp bolt',
             chan_rear - (val('bolt_y1') + bolt_r)),
            ('rack channel front to the mouth', 0.0),
            ('front clamp bolt to rear clamp bolt',
             (val('bolt_y1') - bolt_r) - (val('bolt_y2') + bolt_r))):
        assert _gap < val('tol') or _gap >= val('min_feature'), (
            'the split face leaves a %.3f mm land, %s. sty_ef is %.2f, so two '
            'chamfers want %.2f of it and split_face_chamfer will fail whole. '
            'Make it flush or make it at least %.2f - gs_gear_y is what moves '
            'these' % (_gap * 10, _nm, tval('ef') * 10, tval('ef') * 2 * 10,
                       val('min_feature') * 10))

    # AND THE OTHER HALF OF THAT RULE. The pocket ceiling is taken flush
    # BECAUSE the natural land is unprintable. If gs_gear_y ever moves
    # forward far enough to put a real wall back between the rack channel and
    # the SG90 case top, taking the ceiling flush is throwing that wall away
    # and this says so rather than quietly costing the part its rib.
    _natural = chan_rear - (case_top + val('loc') / 2)
    assert _natural < val('min_feature'), (
        'there is %.2f mm between the rack channel and the SG90 case top now '
        '- a printable wall - and this file still takes the servo pocket '
        'ceiling flush to the channel and throws it away. Put the ceiling '
        'back on gs_case_top + gs_loc / 2' % (_natural * 10))
    assert val('bolt_y1') + bolt_r <= chan_rear - val('wall') + val('tol'), (
        'the front clamshell bolt reaches y %.2f and the rack channel backs '
        'onto %.2f - the bolt hole opens into the channel the rack slides in'
        % ((val('bolt_y1') + bolt_r) * 10, chan_rear * 10))
    # The bolt has crossed mid_y into the tapered tail, so the outline is no
    # longer x_half where it sits. Measure the taper at the bolt's far edge.
    _by = val('bolt_y1') - bolt_r
    _half_at_bolt = (x_half if _by >= mid_y else
                     x_half + (rear_x - x_half) * (mid_y - _by) / (mid_y - back_y))
    assert bolt_x + bolt_r + val('wall') <= _half_at_bolt + val('tol'), (
        'the front clamshell bolt reaches x %.2f at y %.2f where the shell is '
        'only %.2f half wide' % ((bolt_x + bolt_r) * 10, _by * 10,
                                 _half_at_bolt * 10))
    assert case_top < chan_rear, (
        'the SG90 case top at y %.2f is not behind the rack channel at %.2f - '
        'the servo would stand in the rack\'s way'
        % (case_top * 10, chan_rear * 10))

    # ---- phase 1: outer form (BEFORE any internal cut) ----------------------
    t0 = design.timeline.count
    polygon('hand_block',
            [(x_half, front_y), (x_half, mid_y), (-x_half, mid_y), (-x_half, front_y)],
            '0.0 mm', PREFIX + 'half_z', NEW)
    # Full height, not a stepped-down block. A short tail beside a tall hand
    # leaves the tail's top edge running into the hand's side wall, and a
    # chamfer there will not compute - ASM_BL_UNFIN_SHEET, every size. One
    # continuous volume tapering in PLAN only takes a single clean facet, is
    # closer to the reference arm's wrist, and comes out lighter once the
    # cavity over the servo is cut (phase 3).
    polygon('wrist_tail',
            [(x_half, mid_y), (rear_x, back_y), (-rear_x, back_y), (-x_half, mid_y)],
            '0.0 mm', PREFIX + 'half_z', JOIN)

    f_inp = fil.createInput()
    f_inp.addConstantRadiusEdgeSet(vertical_edges(), V(STYLE + 'radius'), True)
    fil.add(f_inp).name = 'corner_radii'

    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_z(val('half_z')), V(STYLE + 'facet'), False)
    chf.add(c_inp).name = 'top_facet'
    group(t0, PH_FORM)

    # ---- phase 2: the mouth, the rack channel and the pinion ----------------
    t1 = design.timeline.count
    # Everything forward of the channel comes out below the top plate: that is
    # the mouth the jaws reach through, and the reason there is no front wall.
    box('mouth', -x_half - val('wall'), x_half + val('wall'),
        gear_y + chan_y, front_y + val('wall'), '0.0 mm', PREFIX + 'chan_z', CUT)
    # The channel runs the FULL width and is open at both ends - the rack is
    # longer than the shell and slides out past it at full open.
    box('rack_channel', -x_half - val('wall'), x_half + val('wall'),
        gear_y - chan_y, gear_y + chan_y,
        '0.0 mm', PREFIX + 'chan_z', CUT)
    # THE RECESS MOVES WITH THE PLANE, AND ITS AXIS IS A QUESTION THIS EDIT
    # DID NOT ANSWER. As written the recess is a cut about Z - bore() sketches
    # on XY and extrudes along Z - while the pinion's axis is Y: gr_offset is
    # measured in Z from the axis to the rack pitch line, and the rack travels
    # in X, so the axis can only be Y. The `assert chan_y < pin_y` below reads
    # gs_pin_y as a HALF WIDTH IN Y, which the extrusion then uses as a Z
    # range. The two readings cannot both be right and this file has a bore_y()
    # that would build the other one. That is a PRE-EXISTING disagreement, not
    # something the horn migration introduced, and correcting it is a geometry
    # change nobody has been able to rebuild and look at - so it is recorded
    # here rather than guessed at. The shift below tracks the plane under the
    # code AS WRITTEN (the circle centre is the y position of a Z-axis cut);
    # if the recess is ever corrected to bore_y, gs_gear_y moves to the
    # EXTRUSION START instead, '-gs_pin_y' -> 'gs_gear_y - gs_pin_y'.
    bore('pinion_recess', 0, gear_y, pin_r, '-' + PREFIX + 'pin_y',
         PREFIX + 'pin_y * 2', CUT)
    group(t1, PH_MOUTH)

    # ---- phase 3: servo bay -------------------------------------------------
    t2 = design.timeline.count
    # Cut to the SYMMETRIC half-width case_far, not the real case outline, so
    # the servo drops in either way round and one shell serves both halves.
    # The tabs, not the case, are the datum (lib/servo.py).
    # THE POCKET CEILING IS THE RACK CHANNEL'S REAR WALL, NOT case_top +
    # loc/2, AND THE 3.80 DROP IS WHY. The channel now backs onto y -7.925
    # and the case top is at -8.20: 0.275 mm apart, 0.175 after the
    # locational fit. That is a curtain thinner than the nozzle between two
    # voids - it cannot print, and at the split face it is a land two 0.4
    # chamfers have to share, which is the ASM_BL_UNFIN_SHEET that stopped
    # the build. There is no wall to be had here, because the pinion now
    # seats 0.40 off the case top and the rack is coplanar with it, so the
    # two cuts are made FLUSH instead. Nothing is lost: the servo is located
    # in y by its TAB SLOTS, this face was only clearance over the case top,
    # and the rack rides at z 7.7..14.6 while this pocket stops at 6.2 - so
    # the channel keeps its rear wall over the whole height the rack uses.
    box('servo_case_pocket', -(case_far + loc / 2), case_far + loc / 2,
        case_bot, srv_front, '0.0 mm',
        PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2', CUT)
    # Only the OUTER tab pair needs slotting: a symmetric pocket of half-width
    # case_far already swallows whichever tab lands on the near side.
    for lo, hi in ((case_far, case_far + tab_over), (-(case_far + tab_over), -case_far)):
        box('tab_slot_%d' % int(round(lo * 100)), lo - loc / 2, hi + loc / 2,
            tab_lo - loc / 2, tab_lo + val('tab_thk') + loc / 2,
            '0.0 mm', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2', CUT)
    # Hollow the tail above the servo: this is what pays for the full-height
    # form, and it is a 1.6 mm capped cavity rather than an open one so the
    # outer surface stays unbroken.
    box('tail_cavity', -(rear_x - val('pocket_inset')), rear_x - val('pocket_inset'),
        back_y + val('pocket_inset'), mid_y - val('wall'),
        PREFIX + 'srv_roof', PREFIX + 'half_z - ' + PREFIX + 'srv_roof - ' + PREFIX + 'wall', CUT)
    # LEAD NOTCH. The bundle leaves the case's SHORT END FACE at the shaft end
    # (lib/servo.py lead datum), so it emerges OUTBOARD of the case end, in
    # the empty 10.6 mm of pocket beyond it. The notch therefore belongs at
    # x = lead_notch_x - its inner edge on the case end face,
    # the whole slot clear of the case body - not at x 0 (the
    # shaft AXIS, where it sat until 2026-08-28) and not straddling the case
    # end at x = shaft_end, where half the slot is roofed by the case and the
    # 3.4 bundle is pinched into 2.5 mm of clear channel. Half-working is
    # worse than not working: it reads CLEAR to a probe and jams on the bench.
    #
    # Two notches, one per end, because the pocket is deliberately symmetric
    # so the servo drops in either way round. That is NOT the two-side-walls
    # anti-pattern lib/servo.py warns about - these are the two pocket END
    # walls, and exactly one of them is in use at a time.
    #
    # This shell is a CLAMSHELL: the servo drops in along z and the cable is
    # laid in by hand before the halves close. There is no insertion jam here
    # and the notch is purely an exit, which is why it can sit clear of the
    # case rather than on the cable's insertion path.
    for _sx in (+1, -1):
        _cx = _sx * val('lead_notch_x')
        box('lead_notch_%s' % ('p' if _sx > 0 else 'm'),
            min(_cx - val('lead_slot') / 2, _cx + val('lead_slot') / 2),
            max(_cx - val('lead_slot') / 2, _cx + val('lead_slot') / 2),
            back_y - val('wall'), case_bot + val('wall'),
            '0.0 mm', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2', CUT)
    group(t2, PH_SERVO)

    # ---- phase 4: fasteners + lightening ------------------------------------
    t3 = design.timeline.count
    for sx in (-1, 1):
        bore('clamp_bolt_front_%d' % sx, sx * bolt_x, val('bolt_y1'), bolt_r,
             '0.0 mm', PREFIX + 'half_z', CUT)
        bore('clamp_bolt_rear_%d' % sx, sx * bolt_x, val('bolt_y2'), bolt_r,
             '0.0 mm', PREFIX + 'half_z', CUT)
    # (rear_rail_pocket was cut here. It is gone - see the note where
    # gs_pocket_x used to be declared. The rail it lightened does not exist
    # any more.)
    group(t3, PH_FASTEN)

    # ---- phase 5: finish -----------------------------------------------------
    t4 = design.timeline.count
    c_inp = chf.createInput2()
    c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges_in_plane_z(0), V(STYLE + 'ef'), False)
    chf.add(c_inp).name = 'split_face_chamfer'
    group(t4, PH_FINISH)


    # ---- phase 6: effector bolts --------------------------------------------
    t5 = design.timeline.count
    for sx in (-1, 1):
        bore_y('eff_bolt_%d' % sx, sx * val('eff_bolt_x'), val('eff_bolt_z'),
               val('bolt_d') / 2, PREFIX + 'back_y',
               PREFIX + 'back_wall + ' + PREFIX + 'wall', CUT)
    group(t5, PH_EFFECTOR)

    # ---- identity + diagnostics ---------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got ' + str(comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    # Appearances.itemByName RAISES on a miss instead of returning null, unlike
    # Materials.itemByName - so scan the libraries rather than probing names.
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

    tail_wall = (rear_x + (x_half - rear_x) * (case_bot - back_y) / (mid_y - back_y)
                 - (case_far + loc / 2))
    # The roof spans from the case bottom to the pocket CEILING, which is now
    # the channel's rear wall rather than gs_mid_y - 4.08 mm more than the
    # figure this line used to quote.
    bridges = (('channel floor', chan_y * 2), ('servo bay roof', srv_front - case_bot),
               ('tail cavity cap', (rear_x - val('pocket_inset')) * 2))
    for nm, span in bridges:
        assert span <= val('max_bridge'), (
            '%s bridges %.1f mm, over MAX_BRIDGE_MM %.1f' % (nm, span * 10, val('max_bridge') * 10))

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('form: %.0f long x %.1f tall, %.0f wide at the hand tapering to %.0f at the wrist' % (
        (front_y - back_y) * 10, val('half_z') * 10, x_half * 2 * 10, rear_x * 2 * 10))
    print('style: %.1f mm facet, R%.1f corners, %.1f mm elephant foot' % (
        facet * 10, tval('radius') * 10, tval('ef') * 10))
    print('channel floor %.2f mm | half width %.3f mm | pinion recess r %.2f mm' % (
        val('chan_z') * 10, chan_y * 10, pin_r * 10))
    print('pinion/rack plane y %.2f (was 0.00 on the horn) | channel y %.2f..%.2f '
          '| mouth opens at %.2f' % (
              gear_y * 10, (gear_y - chan_y) * 10, (gear_y + chan_y) * 10,
              (gear_y + chan_y) * 10))
    print('  NO HORN: the pinion bores THROUGH the Oe%.1f boss and seats %.2f '
          'off the case top, so it and both rack channels came %.2f toward the '
          'servo. gs_case_top is unmoved at %.2f' % (
              val('boss_h') * 10, val('case_gap') * 10,
              (val('boss_h') - val('case_gap')) * 10, case_top * 10))
    print('  front clamshell bolt y %.2f, DERIVED one wall behind the channel '
          '(it was a typed -8.00, which the moved channel now runs through)'
          % (val('bolt_y1') * 10))
    print('  rear_rail_pocket DELETED: the rail it lightened is gone. The '
          'channel backs onto %.2f and the case top is at %.2f, %.3f apart, '
          'so the servo pocket ceiling is taken FLUSH to the channel instead '
          'of leaving an unprintable curtain'
          % (chan_rear * 10, case_top * 10, _natural * 10))
    print('  PRE-EXISTING and NOT moved by gs_gear_y (it is an X land, not a '
          'Y one): the front bolt passes %.2f mm outboard of the servo pocket '
          'wall. It built at HEAD at this width, so it is reported here and '
          'not asserted' % ((bolt_x - bolt_r - (case_far + loc / 2)) * 10))
    print('servo bay y %.2f..%.2f | tabs at y %.2f | far-tab slot x %.1f..%.1f' % (
        case_bot * 10, case_top * 10, tab_lo * 10, case_far * 10, (case_far + tab_over) * 10))
    print('J5 roll interface: 4 x M3 at x +/-%.1f, z +/-%.1f through a %.1f mm wall' % (
        val('eff_bolt_x') * 10, val('eff_bolt_z') * 10, val('back_wall') * 10))
    print('tail wall beside the servo pocket: %.2f mm' % (tail_wall * 10))
    print('bridges (all under %.0f mm, no support): %s' % (
        val('max_bridge') * 10,
        ', '.join('%s %.2f mm' % (nm, span * 10) for nm, span in bridges)))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
