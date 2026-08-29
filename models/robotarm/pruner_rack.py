"""robotarm/pruner_rack - Fusion MCP generating script.

Rebuilds `robotarm_pruner_rack` (idempotent). Spec: specs/robotarm/pruner.md.
Linkage from lib/pruner_linkage.py.

The gripper's rack with the JAW REPLACED BY A PIN. Everything from the pitch
line down - teeth, module, pressure angle, face width - is the gr_ contract
shared with gripper_pinion.py, lifted verbatim so the two cannot drift. The
pinion is reused UNCHANGED; only what happens forward of it differs.

ONE design, TWO copies, the second TURNED OVER (180 deg about Y).

Local frame, as the gripper's: +X the travel direction, +Y forward out of the
hand and along the pinion axis, +Z radially away from the pinion, pitch line
at z = 0.

WHY THE PIN SITS WHERE IT DOES. The pinion's face and the rack's are the same
8 mm and coincident, so the disc runs to y = +4. The pin is a cylinder, not a
point, so its BACK EDGE is what has to clear that - at y = 6.0 with a 3.0
diameter the back edge lands at 4.5, clearing by the same 0.4 the gripper's
own jaw arm uses. Three earlier layouts fouled the disc, twice because the
pin was treated as a point.

The pin reaches DOWN past the pinion's tip circle to the blade plane, where
it runs in the blade's radial slot. It is the only thing this part does.

Print orientation: TEETH DOWN is wrong - the pin would need support. BACK FACE
(z = gr_rack_back) ON THE BED, built along -Z: the teeth are then a vertical
prism, the bracket a vertical prism, and the pin the last thing printed,
standing on the bracket. No support.
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
from lib.pruner_linkage import ARM_CLEAR_MM, CHOSEN, FACE_MM, PIN_DIA_MM  # noqa: E402

COMPONENT = 'robotarm_pruner_rack'
BODY_NAME = 'pruner_rack'
PREFIX = 'pr_'
SHARED = 'gr_'      # gear contract shared with gripper_pinion.py
STYLE = 'sty_'
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A rack is a moving part, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('pruner_rack')
PHASES = ['rack bar', 'drive bracket', 'finish']


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

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def sval(name):
        return ups.itemByName(SHARED + name).value

    # --- SHARED gear contract: identical to gripper_pinion.py -------------
    shared('module', '1.5 mm', 'gear module - design_rules GEAR_PREFERRED_MODULE_MM')
    shared('teeth', '12', 'pinion tooth count - gears_drives.md floor at 20 deg PA', '')
    shared('pa', '20 deg', 'pressure angle - gears_drives.md', 'deg')
    shared('ded_f', '1.25', 'dedendum factor, standard full-depth tooth', '')
    shared('face', '8.0 mm', 'face width, >= 5 x module - design_rules')
    shared('backlash', '0.2 mm', 'backlash added at the centre distance - design_rules GEAR_BACKLASH_MM')
    shared('r_pitch', SHARED + 'module * ' + SHARED + 'teeth / 2', 'derived pitch radius')
    shared('offset', SHARED + 'r_pitch + ' + SHARED + 'backlash', 'pinion axis to rack PITCH LINE - the centre distance')
    shared('stroke', '20.0 mm', 'travel of ONE rack; jaw opening is twice this')
    shared('r_tip', SHARED + 'r_pitch + ' + SHARED + 'module', 'derived pinion tip radius')
    shared('rack_web', '3.5 mm', 'rack back thickness above the tooth root')
    shared('rack_back', SHARED + 'module * ' + SHARED + 'ded_f + ' + SHARED + 'rack_web',
           'derived rack back, above the pitch line - the shell channel floor rides on this')
    shared('arm_thk', '9.0 mm',
           'jaw arm and blade thickness in x - thick enough to carry a facet\n            that reads, with the mass taken back out as a recessed panel')
    shared('blade_half', '8.0 mm',
           'how far a blade reaches PAST the gripper centre plane - so it also says\n            how far each arm intrudes into the OTHER shell half')

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'plan-view corner radius - _style.md rule 2')

    # --- rack -----------------------------------------------------------------
    param('pitch', SHARED + 'module * PI', 'derived circular pitch of the rack')
    param('rack_teeth', '8',
          'rack tooth count. The same 8 as the gripper: 8 teeth already reach\n'
          '           29.7 mm back, which covers the 24.8 mm this needs. The pruner uses\n'
          '           more TRAVEL than the gripper (24.8 against 20.0) because advantage\n'
          '           is travel over throat opening and travel is the only free variable\n'
          '           left - but that comes out of the servo sweep, not out of more\n'
          '           teeth. 10 gave a 39 mm toothed run for no reason. Asserted below.', '')
    param('tooth_lead', '8.0 mm', 'toothed run reaches this far outboard of the pin')
    param('end_lead', '3.0 mm', 'plain rack beyond the last tooth at each end')
    param('stroke', '%.3f mm' % CHOSEN.rack_travel_mm,
          'travel of ONE rack. FROM lib/pruner_linkage.CHOSEN. Note this is NOT\n'
          '           gr_stroke: the gripper contract stays at 20.0 so the gripper keeps\n'
          '           working, and the pruner buys its force with the servo sweep the\n'
          '           gripper leaves on the table.')

    # --- drive bracket and pin --------------------------------------------------
    param('pin_d', '%.2f mm' % PIN_DIA_MM, 'drive pin - FROM lib/pruner_linkage')
    param('pin_y', '%.3f mm' % (CHOSEN.pivot_y - CHOSEN.tail_r),
          'pin axis, forward of the pinion. FROM lib/pruner_linkage.CHOSEN')
    param('arm_clear', '%.2f mm' % ARM_CLEAR_MM,
          'what the pin BACK EDGE clears the pinion disc by - the same figure the\n'
          '           gripper jaw arm uses')
    param('blade_z', '%.3f mm' % (0.05 + 3.5),
          'outer face of the blade carrier, in the effector frame. The pin has to\n'
          '           reach past this to fill the blade slot. Mirrors pb_gap + pb_thk.')
    param('blade_gap', '0.05 mm', 'half the bypass gap - mirrors pb_gap')
    param('brk_w', '11.0 mm', 'bracket width, about the pin')
    param('brk_t', '3.5 mm', 'bracket thickness, radially')
    param('pin_extra', '0.0 mm',
          'how far the pin may stand proud of the blade it drives. ZERO, and that\n'
          '           is not laziness: the OTHER rack is the mirror of this one, so its pin\n'
          '           is coaxial and comes the other way. 0.4 of proud made the two pins\n'
          '           overlap across the centreline by 4.95 mm3. The pin ends flush with\n'
          '           the blade inner face and the two tips face each other across the\n'
          '           same 2 x pb_gap the blades themselves bypass on.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild -----------------------------------------------------
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

    def mm(cm):
        """A length computed in Python, as an expression Fusion reads correctly.

        val() hands back Fusion's INTERNAL unit, centimetres. ValueInput's
        createByString reads a BARE NUMBER in the DOCUMENT's unit, millimetres.
        Formatting a cm value into a bare string therefore builds the feature
        ten times too small, in the wrong place, with no error at all: the
        drive tie came out 0.35 mm thick sitting exactly on the pitch line,
        where it chewed 8.6 mm3 out of the pinion. Never emit a bare number -
        always this, or a parameter expression.
        """
        return '%.4f mm' % (cm * 10.0)

    def box(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0, 0), mpt(sk, x1, y1, 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def post(name, x, y, d, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x, y, 0), d / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    # ---- geometry in cm ----------------------------------------------------------
    pitch = val('pitch')
    n_teeth = int(round(val('rack_teeth')))
    add_h = sval('module')
    ded_h = sval('module') * sval('ded_f')
    tan_pa = math.tan(sval('pa'))
    tip_half = pitch / 2 / 2 - add_h * tan_pa
    root_half = pitch / 2 / 2 + ded_h * tan_pa
    x_b = val('tooth_lead')
    x_a = x_b - n_teeth * pitch
    x_lo = x_a - val('end_lead')
    x_hi = x_b + val('end_lead')
    z_back = sval('rack_back')
    half_face = sval('face') / 2
    stroke = val('stroke')

    assert tip_half > 0, 'tooth would come to a point: module or pressure angle wrong'
    assert x_a <= -stroke, (
        'rack runs off the pinion at full open: toothed run starts at %.2f mm but '
        'must reach %.2f mm - add teeth' % (x_a * 10, -stroke * 10))
    assert x_b >= 0, 'rack runs off the pinion at full close'
    back_edge = val('pin_y') - val('pin_d') / 2
    assert back_edge >= half_face + val('arm_clear'), (
        'the drive pin back edge is at y = %.2f, inside the pinion disc which ends '
        'at %.2f' % (back_edge * 10, half_face * 10))

    # The pin has to span the blade carrier, which sits BELOW the pitch line by
    # the centre distance. Everything here is in the rack's own frame, so the
    # blade's effector-frame z has to come back through gr_offset.
    pin_top = -(sval('offset') - val('blade_z'))
    pin_bot = -(sval('offset') - val('blade_gap')) - val('pin_extra')
    # The mirrored rack's pin is coaxial with this one and arrives from the far
    # side. Whatever this pin does past the centreline, that one does too.
    pin_tip_z = sval('offset') + pin_bot        # effector-frame z of the pin tip
    assert pin_tip_z >= val('blade_gap') - 1e-9, (
        'the drive pin reaches to z = %.3f, past the blade inner face at %.3f - it '
        'will hit the other rack\'s pin' % (pin_tip_z * 10, val('blade_gap') * 10))
    brk_top = pin_top + val('brk_t')
    assert brk_top < z_back, 'the drive bracket stands proud of the rack back'

    # ---- phase 1: rack bar ---------------------------------------------------------
    t0 = design.timeline.count
    sk_rack = sketch(comp.xZConstructionPlane, 'sk_rack_profile')
    pts = [(x_lo, z_back), (x_hi, z_back), (x_hi, ded_h), (x_b, ded_h)]
    for i in range(n_teeth - 1, -1, -1):
        xc = x_a + (2 * i + 1) * pitch / 2
        pts.append((xc + root_half, ded_h))
        pts.append((xc + tip_half, -add_h))
        pts.append((xc - tip_half, -add_h))
        pts.append((xc - root_half, ded_h))
    pts.append((x_a, ded_h))
    pts.append((x_lo, ded_h))
    lines = sk_rack.sketchCurves.sketchLines
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        lines.addByTwoPoints(mpt(sk_rack, a[0], 0, a[1]), mpt(sk_rack, b[0], 0, b[1]))
    extrude(profiles(sk_rack, expected=1), NEW,
            '-' + SHARED + 'face / 2', SHARED + 'face', 'rack_bar')
    group(t0, PHASES[0])

    # ---- phase 2: drive bracket ------------------------------------------------------
    t1 = design.timeline.count
    # Spans from the rack's front face forward past the pin, and from the blade
    # plane up into the rack's own back, so the load path is short.
    # The tie crosses the rack's own depth, but ONLY above the pinion's tip
    # circle - which in this frame reaches z = -gr_offset + gr_r_tip. Below
    # that line nothing may cross y in [-4, +4]. The gripper's arm_tie starts
    # at the tooth root for exactly this reason; so does this.
    tip_line = -sval('offset') + sval('r_tip')
    assert ded_h > tip_line, 'the tie would cross the pinion tip circle'
    box('tie', -val('brk_w') / 2, val('brk_w') / 2,
        -half_face, half_face + val('arm_clear'),
        mm(ded_h), mm(z_back - ded_h), JOIN)
    # The bracket drops to the blade plane, so it may only exist FORWARD of the
    # disc. Starting it at half_face - brk_t put 14.5 mm3 of it inside the
    # pinion; the assertion below is what that cost.
    assert half_face + val('arm_clear') > half_face, 'bracket starts inside the disc'
    box('bracket', -val('brk_w') / 2, val('brk_w') / 2,
        half_face + val('arm_clear'), val('pin_y') + val('pin_d'),
        mm(pin_top), mm(z_back - pin_top), JOIN)
    post('drive_pin', 0.0, val('pin_y'), val('pin_d'),
         mm(pin_bot), mm(pin_top - pin_bot), JOIN)
    group(t1, PHASES[1])

    # ---- phase 3: finish ---------------------------------------------------------------
    t2 = design.timeline.count
    col = adsk.core.ObjectCollection.create()
    for e in comp.bRepBodies.item(0).edges:
        bb = e.boundingBox
        if (abs(bb.minPoint.z - z_back) < val('tol')
                and abs(bb.maxPoint.z - z_back) < val('tol')):
            col.add(e)
    if col.count:
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = 'bed_face_chamfer'
    group(t2, PHASES[2])

    # ---- identity + diagnostics ----------------------------------------------------------
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
    print('%d teeth, toothed run x %.2f..%.2f, covers a %.2f mm stroke (needs %.2f)' % (
        n_teeth, x_a * 10, x_b * 10, -x_a * 10, stroke * 10))
    print('drive pin %.1f dia at y %.1f | BACK EDGE %.2f, pinion disc ends %.2f' % (
        val('pin_d') * 10, val('pin_y') * 10, back_edge * 10, half_face * 10))
    print('pin spans z %.2f..%.2f in the rack frame; tip lands at effector z %.2f, '
          'facing the other pin across %.2f' % (
              pin_bot * 10, pin_top * 10, pin_tip_z * 10, 2 * val('blade_gap') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f (x2 = %.2f) | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 2000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
