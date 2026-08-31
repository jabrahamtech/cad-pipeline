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
    param('case_top', '-(' + SHARED + 'face / 2 + ' + PREFIX + 'boss_h)',
          'derived: the pinion back face sits on the horn, the horn on the boss')
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
    param('bolt_y1', '-8.0 mm', 'front clamshell bolt: clear of the channel and the arm')
    param('bolt_y2', '-24.0 mm',
          'rear clamshell bolt - ALSO the wrist interface: the bracket ears clamp '
          'the tail on these two, so an effector swap needs no extra fastener')
    param('pocket_x', '21.0 mm', 'lightening pocket in the rear rail, +/- this')
    param('max_bridge', '40.0 mm', 'longest clean unsupported bridge - design_rules')
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
    pocket_x = val('pocket_x')
    bolt_r = val('bolt_d') / 2
    bolt_x = val('bolt_x')

    assert chan_y < pin_y, 'the pinion recess must be at least as wide as the rack channel'
    assert case_far + tab_over < x_half, 'the servo tabs stick out past the shell'

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
        chan_y, front_y + val('wall'), '0.0 mm', PREFIX + 'chan_z', CUT)
    # The channel runs the FULL width and is open at both ends - the rack is
    # longer than the shell and slides out past it at full open.
    box('rack_channel', -x_half - val('wall'), x_half + val('wall'), -chan_y, chan_y,
        '0.0 mm', PREFIX + 'chan_z', CUT)
    bore('pinion_recess', 0, 0, pin_r, '-' + PREFIX + 'pin_y', PREFIX + 'pin_y * 2', CUT)
    group(t1, PH_MOUTH)

    # ---- phase 3: servo bay -------------------------------------------------
    t2 = design.timeline.count
    # Cut to the SYMMETRIC half-width case_far, not the real case outline, so
    # the servo drops in either way round and one shell serves both halves.
    # The tabs, not the case, are the datum (lib/servo.py).
    box('servo_case_pocket', -(case_far + loc / 2), case_far + loc / 2,
        case_bot, case_top + loc / 2, '0.0 mm',
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
    box('rear_rail_pocket', -pocket_x, pocket_x,
        mid_y + val('wall'), -chan_y - val('wall'),
        '0.0 mm', PREFIX + 'chan_z - ' + PREFIX + 'wall', CUT)
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
    bridges = (('channel floor', chan_y * 2), ('servo bay roof', mid_y - case_bot),
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
