"""robotarm/gripper_shell - Fusion MCP generating script.

Rebuilds `robotarm_gripper_shell` (idempotent). Spec:
specs/robotarm/gripper_shell.md.

Local frame IS the gripper assembly frame, with this half occupying z >= 0:
  x  jaw opening direction, 0 on the centre plane
  y  forward along the arm; the pinion axis and the SG90 shaft lie on it
  z  the clamshell split axis; z = 0 is the split face

ONE printed design, TWO copies. The second goes on TURNED OVER - rotated
180 deg about Y, (x, y, z) -> (-x, y, -z). Everything here is therefore
symmetric in x, INCLUDING the servo mount, which the SG90 itself is not:
its shaft sits 6.1 mm from one end of a 22.6 mm case, so its tabs land at
-11.0..-6.1 and +16.5..+21.4 about the shaft. The pocket is cut to the
UNION of that layout and its mirror - four tab slots, of which the fitted
servo uses two. The two spare slots are empty voids and cost nothing; two
mirror-image shell designs would have cost a whole second part.

The servo takes NO screws. Its tabs are trapped in x and y by their slots
and in z by the two halves closing, which is stiffer than two self-tappers
into printed bosses and removes a fastener from the build.

Print orientation: SPLIT FACE (z = 0) ON THE BED, built in +z. The rack
channel's floor bridges 8.25 mm, the pinion recess is a self-supporting
arch narrowing as it rises, and the servo cavity's roof bridges 19.9 mm -
all inside MAX_BRIDGE_MM. No support.

The SHARED gr_* block is defined identically in gripper_pinion.py and
gripper_rack_jaw.py. Servo dimensions are DATASHEET (lib/servo.py) and are
the first suspects if the SG90 will not seat: gauge the tab plate first.
"""

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_gripper_shell'
BODY_NAME = 'gripper_shell'
PREFIX = 'gs_'
SHARED = 'gr_'
PH_BLOCK = 'shell block'
PH_CHANNEL = 'rack channel and pinion'
PH_SERVO = 'servo bay'
PH_FASTEN = 'fasteners'
PH_FINISH = 'finish'
PHASES = [PH_BLOCK, PH_CHANNEL, PH_SERVO, PH_FASTEN, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'


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

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def sval(name):
        return ups.itemByName(SHARED + name).value

    # --- SHARED contract: identical to gripper_pinion / gripper_rack_jaw ---
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
    shared('arm_thk', '6.0 mm', 'jaw arm and blade thickness in x - this shell slots for it')
    shared('blade_half', '8.0 mm',
           'how far a blade reaches PAST the gripper centre plane - so it also says\n            how far the OTHER half\'s arm intrudes into this one')

    # --- fits ---------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('slide', '0.25 mm', 'sliding fit, rack in channel - design_rules CALIBRATED')
    param('free', '0.4 mm', 'free fit, must never bind - design_rules')
    param('loc', '0.2 mm', 'locational fit - design_rules')

    # --- shell envelope ------------------------------------------------------
    param('x', '24.0 mm', 'half width; also the rack channel guide length / 2')
    param('front_y', '6.0 mm', 'front face, forward of the rack channel')
    param('mid_y', '-12.0 mm', 'boundary between the channel block and the servo bay')
    param('chan_z', SHARED + 'offset + ' + SHARED + 'rack_back + ' + PREFIX + 'slide / 2',
          'derived channel floor: where the rack back rides')
    param('half_z', PREFIX + 'chan_z + ' + PREFIX + 'wall', 'derived shell half height')
    param('chan_y', SHARED + 'face / 2 + ' + PREFIX + 'slide / 2', 'derived channel half width')
    param('pin_r', SHARED + 'r_tip + ' + PREFIX + 'free', 'derived pinion recess radius')
    param('pin_y', SHARED + 'face / 2 + ' + PREFIX + 'free', 'derived pinion recess half width')

    # --- the slot the jaw arm sweeps through --------------------------------
    param('arm_lo', '-1.0 mm', 'arm slot starts just inboard of the closed jaw')
    param('arm_hi', SHARED + 'stroke + ' + SHARED + 'arm_thk + ' + PREFIX + 'free',
          'derived: the arm at FULL OPEN, plus a free fit')
    param('other_arm_z', SHARED + 'blade_half + ' + PREFIX + 'free',
          'derived: how far the OTHER half\'s arm reaches into this one')

    # --- SG90, DATASHEET (lib/servo.py) --------------------------------------
    param('case_l', '22.6 mm', 'SG90 case length - DATASHEET')
    param('case_w', '12.6 mm', 'SG90 case width - DATASHEET')
    param('case_h', '23.7 mm', 'SG90 case height - DATASHEET')
    param('shaft_end', '6.1 mm', 'shaft axis to the NEAR end of the case - DATASHEET')
    param('tab_span', '32.4 mm', 'SG90 tab tip to tab tip - DATASHEET')
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
    param('lead_slot', '5.0 mm', 'notch in the back wall for the servo lead - cable_management')

    # --- fasteners -----------------------------------------------------------
    param('bolt_d', '3.4 mm', 'M3 clearance - design_rules FASTENER_MM')
    param('bolt_x', '19.0 mm', 'clamshell bolts, +/- this in x')
    param('bolt_y1', '-8.0 mm', 'front clamshell bolt: clear of the channel, clear of the arm')
    param('bolt_y2', '-24.0 mm', 'rear clamshell bolt, through the servo bay walls')
    param('flange_t', '2.6 mm', 'wrist mounting flange thickness')
    param('flange_bolt_x', '16.0 mm', 'effector bolt pattern - asm_eff_bolt_x')
    param('flange_bolt_z', '12.0 mm', 'effector bolt pattern - asm_eff_bolt_z')

    # --- lightening ----------------------------------------------------------
    param('pocket_x', '20.0 mm', 'lightening pocket in the rear rail, +/- this')
    param('max_bridge', '40.0 mm', 'longest clean unsupported bridge - design_rules MAX_BRIDGE_MM')
    param('ef', '0.4 mm', 'elephant-foot chamfer - design_rules')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild ------------------------------------------------
    for occ in list(root.occurrences):
        if occ.component.name == COMPONENT or occ.component.name.startswith(COMPONENT + ' ('):
            occ.deleteMe()
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name == COMPONENT or c.name.startswith(COMPONENT + ' ('):
            c.name = COMPONENT + '_stale_' + str(i)
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
            # WITHOUT THIS, A CUT EATS EVERY OTHER COMPONENT IN THE DOCUMENT.
            # An extrude with no participantBodies takes part with everything
            # it intersects, across component boundaries, and reports nothing.
            # In a shared assembly document that means one part's pocket
            # quietly hollows out its neighbours - measured here as a pinion
            # losing 95 % of its volume and a rack going to zero while
            # isValid stayed True. Scope every non-NEW operation to this
            # component's own bodies.
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

    def box(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        """Axis-aligned block: XY rectangle in cm, Z from parameter expressions."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0, 0), mpt(sk, x1, y1, 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def bore(name, x_cm, y_cm, r_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_cm, y_cm, 0), r_cm)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def bore_y(name, x_cm, z_cm, r_cm, y0_expr, dy_expr, op):
        """A hole along Y - the wrist flange bolts pull along the arm's axis,
        not across the clamshell split."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_cm, 0, z_cm), r_cm)
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    # ---- values in cm -------------------------------------------------------
    x_half = val('x')
    front_y = val('front_y')
    mid_y = val('mid_y')
    chan_y = val('chan_y')
    pin_r = val('pin_r')
    pin_y = val('pin_y')
    case_top = val('case_top')
    case_bot = val('case_bot')
    case_far = val('case_far')
    tab_over = val('tab_over')
    tab_lo = val('tab_lo')
    loc = val('loc')
    srv_z = val('case_w') / 2 + loc / 2
    pocket_x = val('pocket_x')
    bolt_r = val('bolt_d') / 2
    bolt_x = val('bolt_x')

    assert chan_y < pin_y, 'the pinion recess must be at least as wide as the rack channel'
    assert case_far + tab_over < x_half, 'the servo tabs stick out past the shell'

    # ---- phase 1: shell block ----------------------------------------------
    t0 = design.timeline.count
    box('channel_block', -x_half, x_half, mid_y, front_y, '0.0 mm', PREFIX + 'half_z', NEW)
    box('servo_block', -x_half, x_half, case_bot, mid_y,
        '0.0 mm', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2 + ' + PREFIX + 'wall', JOIN)
    box('wrist_flange', -x_half, x_half, case_bot - val('flange_t'), case_bot,
        '0.0 mm', PREFIX + 'half_z', JOIN)
    group(t0, PH_BLOCK)

    # ---- phase 2: rack channel and pinion recess ---------------------------
    # The channel runs the full width and is OPEN at both ends: the rack is
    # longer than the shell and has to slide out past it at full open.
    t1 = design.timeline.count
    box('rack_channel', -x_half, x_half, -chan_y, chan_y, '0.0 mm', PREFIX + 'chan_z', CUT)
    bore('pinion_recess', 0, 0, pin_r, '-' + PREFIX + 'pin_y',
         PREFIX + 'pin_y * 2', CUT)
    # The jaw arm sweeps through the front rail. Cutting only this half's
    # sweep is what keeps the front rail intact over the other half's range
    # once the pair is turned over and closed.
    box('arm_sweep_slot', val('arm_lo'), val('arm_hi'), chan_y, front_y,
        '0.0 mm', PREFIX + 'chan_z', CUT)
    # ... and the OTHER half's arm crosses the split plane into this one. Its
    # blade reaches gr_blade_half past centre, so it intrudes exactly that far
    # and sweeps the mirrored x range. Missing this is a collision the fit
    # check finds only once both shells are placed.
    box('other_arm_slot', -val('arm_hi'), -val('arm_lo'), chan_y, front_y,
        '0.0 mm', PREFIX + 'other_arm_z', CUT)
    group(t1, PH_CHANNEL)

    # ---- phase 3: servo bay -------------------------------------------------
    t2 = design.timeline.count
    # The case pocket is cut to the SYMMETRIC half-width case_far, not to the
    # real case outline, so the servo drops in either way round and one shell
    # design serves both halves. It leaves the case 10.4 mm of slack in x -
    # the tabs, not the case, are the datum (lib/servo.py).
    box('servo_case_pocket', -(case_far + loc / 2), case_far + loc / 2,
        case_bot, case_top + loc / 2, '0.0 mm',
        PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2', CUT)
    # Only the OUTER tab pair needs slotting. A symmetric pocket of half-width
    # case_far already swallows whichever tab ends up on the near side (it
    # reaches only shaft_end + tab_over = 11.0 mm), so cutting there would find
    # no material at all. The far tab is what locates the servo in x and y;
    # both halves closing locate it in z, and it takes no screws.
    for lo, hi in ((case_far, case_far + tab_over),
                   (-(case_far + tab_over), -case_far)):
        box('tab_slot_%d' % int(round(lo * 100)), lo - loc / 2, hi + loc / 2,
            tab_lo - loc / 2, tab_lo + val('tab_thk') + loc / 2,
            '0.0 mm', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2', CUT)
    box('lead_notch', -val('lead_slot') / 2, val('lead_slot') / 2,
        case_bot - val('flange_t'), case_bot + val('wall'),
        '0.0 mm', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2', CUT)
    group(t2, PH_SERVO)

    # ---- phase 4: fasteners + lightening ------------------------------------
    t3 = design.timeline.count
    for sx in (-1, 1):
        bore('clamp_bolt_front_%d' % sx, sx * bolt_x, val('bolt_y1'), bolt_r,
             '0.0 mm', PREFIX + 'half_z', CUT)
        bore('clamp_bolt_rear_%d' % sx, sx * bolt_x, val('bolt_y2'), bolt_r,
             '0.0 mm', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2 + ' + PREFIX + 'wall', CUT)
        bore_y('wrist_bolt_%d' % sx, sx * val('flange_bolt_x'), val('flange_bolt_z'),
               bolt_r, PREFIX + 'case_bot - ' + PREFIX + 'flange_t',
               PREFIX + 'flange_t', CUT)
    box('rear_rail_pocket', -pocket_x, pocket_x,
        mid_y + val('wall'), -chan_y - val('wall'),
        '0.0 mm', PREFIX + 'chan_z - ' + PREFIX + 'wall', CUT)
    group(t3, PH_FASTEN)

    # ---- phase 5: finish -----------------------------------------------------
    t4 = design.timeline.count
    tol = val('tol')
    for z_pick, dist, nm in ((0, 'ef', 'split_face_chamfer'),
                             (val('half_z'), 'ef', 'top_face_chamfer')):
        edges = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if abs(eb.minPoint.z - z_pick) < tol and abs(eb.maxPoint.z - z_pick) < tol:
                edges.add(e)
        inp = chf.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(PREFIX + dist), False)
        chf.add(inp).name = nm
    group(t4, PH_FINISH)

    # ---- identity + diagnostics ---------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got ' + str(comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break

    bb = body.boundingBox
    print('body: %r | material: %s' % (body.name, body.material.name))
    print('half height %.2f mm | channel floor %.2f mm | channel half width %.3f mm' % (
        val('half_z') * 10, val('chan_z') * 10, chan_y * 10))
    print('pinion recess r %.2f mm (tip %.2f + free %.2f)' % (
        pin_r * 10, sval('r_tip') * 10, val('free') * 10))
    print('arm slots: own x %.1f..%.1f full height; other x %.1f..%.1f to z %.1f mm' % (
        val('arm_lo') * 10, val('arm_hi') * 10,
        -val('arm_hi') * 10, -val('arm_lo') * 10, val('other_arm_z') * 10))
    print('servo bay y %.2f..%.2f mm | tabs at y %.2f mm | far-tab slot x %.1f..%.1f' % (
        case_bot * 10, case_top * 10, tab_lo * 10, case_far * 10,
        (case_far + tab_over) * 10))
    bridges = (('channel floor', chan_y * 2), ('servo bay roof', mid_y - case_bot))
    for nm, span in bridges:
        assert span <= val('max_bridge'), (
            '%s bridges %.1f mm, over MAX_BRIDGE_MM %.1f - it would need support'
            % (nm, span * 10, val('max_bridge') * 10))
    print('bridges (all under %.0f mm, so no support): %s' % (
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
