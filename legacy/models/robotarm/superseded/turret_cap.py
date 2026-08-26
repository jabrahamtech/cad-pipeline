"""robotarm/turret_cap - Fusion MCP generating script.

Rebuilds `robotarm_turret_cap` (idempotent). Spec: specs/robotarm/_state.md.

J1, the rotating half. The shoulder bracket bolts to its top face; three
608ZZ on horizontal radial axles roll under its track; an SG90 in the base
drives it through a horn recessed into its centre; and two bayonet lugs on
its rim hold it DOWN.

Local frame: origin ON THE J1 YAW AXIS at the cap's TOP face - which is the
same plane as the shoulder bracket's mounting face, so the two parts share a
z = 0. +Z up. Everything in this part is at z <= 0.

THE BAYONET IS NOT A FLOURISH, THE ARM TIPS WITHOUT IT. Three rollers on a
30 mm circle carry weight downward and nothing upward. Fully extended, this
arm puts roughly 187 g of moving mass about 130 mm forward of the yaw axis
against roughly 101 g of turret, bracket and MG995 sitting on it - a
resultant 84 mm out, nearly three times the roller radius. The rear of the
turret lifts. Either the roller circle grows past 84 mm (a 190 mm base) or
the turret is held down; the lugs are the cheap answer and they cost one
printed feature on each half.

TWO LUGS, ON +-X, AND THAT SETS THE TRAVEL. A bayonet with N lugs locks for
360/N minus the lug's own arc. Three lugs would give 95 deg; two give
180 - 28 = 152. J1 is therefore 15..165 deg with neutral at 90, and 0 deg -
lugs aligned with the base's gaps - is the ASSEMBLY position, not a working
one. Drawing them on +-X is also why they are plain rectangles: axis-aligned
tabs need no rotated sketch geometry to go wrong.

THE HORN GOES IN BLADE TOWARD THE SERVO, same convention as shoulder_hub, and
for the same reason: flipped, the blade sits a horn-hub deeper and the arm
tips break out of the pocket. The SG90 sits low enough that its output boss
never enters this part at all - only the horn does - so the mouth is sized by
the trimmed arms, not the boss.

Print orientation: TOP FACE ON THE BED, built -Z... no. Built +Z with the top
face DOWN, so the track annulus and the lug undersides - the two surfaces that
have to be flat and true - are the top of the print, and the pockets are
overhangs no deeper than tc_pocket_z. The horn recess then prints as a stack
of three counterbores, which is the one thing in it that wants to be round.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_turret_cap'
BODY_NAME = 'turret_cap'
PREFIX = 'tc_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_FORM = 'cap form'
PH_TRACK = 'track and lightening'
PH_HORN = 'horn interface'
PH_BOLTS = 'bracket interface'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_TRACK, PH_HORN, PH_BOLTS, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. The turret is structure, so it is dark.
APPEARANCE_HINTS = [('plastic', 'black'), ('paint', 'black'), ('black',), ('plastic',)]


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

    # ---- the SHARED turret contract -----------------------------------------
    # Defined identically here, in shoulder_bracket.py, base_shell.py and
    # turntable_clip.py. Change it in one place only by changing it in all.
    turret('bolt_pitch', '30.0 mm',
           'square 4-bolt pattern joining the shoulder bracket to this cap.\n'
           '           30.0 puts every bolt directly under a bracket leg.')
    turret('bolt_pilot', '2.5 mm',
           'M3 self-tapper into PETG, in the BRACKET. NOT the 1.8 servo pilot.')
    turret('bolt_depth', '3.0 mm', 'how far that pilot goes into the bracket')
    turret('bolt_clear', '3.4 mm', 'M3 clearance, in THIS part - the screws come up')
    turret('head_d', '6.0 mm', 'M3 socket head 5.5 + 0.5, counterbored from below')
    turret('head_h', '3.2 mm', 'M3 socket head height + 0.2')
    turret('roller_r', '30.0 mm',
           'yaw axis to the MID-PLANE of each 608ZZ. Not free in two directions:\n'
           '           it has to clear the bolt heads at r 21.2 on the inside, and\n'
           '           every mm of it is a mm of overturning resistance.')
    turret('cap_r', '38.0 mm', 'cap outer radius, full thickness. The lugs go beyond it.')
    turret('cap_t', '7.0 mm',
           'cap thickness. NOT a round number picked for looks: the horn recess is\n'
           '           mouth 1.2 + bore 3.8 = 5.0 deep and needs a wall of roof over\n'
           '           it, so 6.6 is the floor. The M3 head counterbore (3.2) is the\n'
           '           looser of the two constraints, not the binding one.')
    turret('lug_or', '44.0 mm', 'bayonet lug outer radius')
    turret('lug_w', '20.0 mm', 'lug width, tangential. Sets the travel - see the docstring.')
    turret('lug_t', '3.0 mm', 'lug thickness, hanging from the cap underside')
    turret('run_gap', '0.4 mm', 'free fit between this cap and the base around it')
    turret('lip_ir', TURRET + 'cap_r + ' + TURRET + 'run_gap',
           'derived: inner radius of the base\'s bayonet lip. It overhangs the lugs\n'
           '           and clears this cap\'s rim.')
    # 608ZZ, DRAWING-CONFIRMED (lib/bearings.py). These live in the SHARED block
    # because base_shell and turntable_clip build from them too, and because
    # axle_z has to be DERIVED from cap_t - it was hand-set at -17.0, cap_t then
    # moved 6.0 -> 7.0 for the horn recess, and the assertion below caught it.
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - the rolling surface')
    turret('roller_w', '7.0 mm', '608ZZ width - lies RADIALLY, the axle is radial')
    turret('axle_z', '-(' + TURRET + 'cap_t + ' + TURRET + 'roller_od / 2)',
           'derived: roller axle height in this frame. The bearing touches the cap\n'
           '           underside, so this follows cap_t and must never be typed.')

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'silhouette corner radius - _style.md rule 2')

    # ---- fits ----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('free', '0.4 mm', 'free fit - design_rules')

    # ---- the track and the lightening ---------------------------------------
    param('track_in', TURRET + 'roller_r - ' + TURRET + 'roller_w / 2 - 0.5 mm',
          'derived: the flat band the rollers run on, with 0.5 of overrun inboard')
    param('track_out', TURRET + 'roller_r + ' + TURRET + 'roller_w / 2 + 0.5 mm',
          'derived, 0.5 of overrun outboard')
    param('pocket_z', '3.0 mm',
          'depth of the underside pockets either side of the track. Half the plate,\n'
          '           which is as far as it can go and still leave 1.6 over the bolt\n'
          '           head counterbores.')
    param('boss_d', '11.0 mm', 'the pad left standing round each bolt inside the pocket')
    param('hub_r', '9.0 mm', 'inner edge of the underside pocket - the horn hub stays solid')

    # ---- SG90 horn, DATASHEET (lib/servo.py) --------------------------------
    param('hub_bore', '7.15 mm', 'SG90 horn hub 7.0 DATASHEET + press 0.15')
    param('arm_r', '6.0 mm', 'horn arms TRIMMED to this radius at assembly, as wrist_hub')
    param('arm_w', '1.65 mm', 'SG90 horn blade 1.5 DATASHEET + press 0.15')
    param('mouth_d', '2 * ' + PREFIX + 'arm_r + ' + PREFIX + 'free',
          'derived: the mouth is sized by the ARMS travelling down to their slot.\n'
          '           The SG90 sits low enough that its 5.0 output boss never enters\n'
          '           this part, so the boss does not size anything here.')
    param('mouth_z', '1.2 mm',
          'how far the mouth reaches before the blade slot starts. Set by where the\n'
          '           servo sits: boss top is 1.2 above this cap\'s underside.')
    param('blade_z', PREFIX + 'arm_w', 'derived: the slot is as deep as the blade is thick')
    param('bore_z', '3.8 mm', 'SG90 horn hub height - the bore is exactly that')
    param('roof', TURRET + 'cap_t - ' + PREFIX + 'mouth_z - ' + PREFIX + 'bore_z',
          'derived: what is left over the horn recess. Asserted against the wall.')

    # ---- the loom ------------------------------------------------------------
    param('cable_ir', '11.0 mm', 'inner radius of the arc the whole loom passes through')
    param('cable_or', '17.5 mm',
          'outer radius. Bounded: the bolt clearance holes sit at r 21.2 and want a\n'
          '           wall beside them.')
    param('cable_deg', '120.0 deg',
          'arc swept by the cable window. The loom twists through J1\'s 150 deg of\n'
          '           travel, so it needs room to move, not just room to sit.', 'deg')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
    # RENAME FIRST, THEN DELETE. See fusion/PLAYBOOK.md.
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

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mpt(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def mm(cm):
        """cm -> a millimetre EXPRESSION. createByString reads a bare number as
        millimetres; val() hands out centimetres. See fusion/PLAYBOOK.md."""
        return '%.4f mm' % (cm * 10.0)

    def extrude(profs, op, z0_expr, dz_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0_expr))
        inp.setDistanceExtent(False, V(dz_expr))
        if op != NEW:
            # Without this a CUT eats every other component. See PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def one(sk, expected=1):
        assert sk.profiles.count == expected, (
            sk.name + ': expected ' + str(expected) + ', got ' + str(sk.profiles.count))
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def circle(name, x, y, d, z0_expr, dz_expr, op):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x, y), d / 2)
        return extrude(one(sk), op, z0_expr, dz_expr, name)

    def ring(name, r_out, r_in, z0_expr, dz_expr, op):
        """Two concentric circles give TWO profiles - the inner disc and the
        annulus. Picking by index is a coin toss, so pick by area."""
        sk = sketch(name)
        for r in (r_out, r_in):
            sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, 0), r)
        assert sk.profiles.count == 2, sk.name + ': got %d profiles' % sk.profiles.count
        want = math.pi * (r_out ** 2 - r_in ** 2)
        c = adsk.core.ObjectCollection.create()
        for i in range(2):
            p = sk.profiles.item(i)
            if abs(p.areaProperties().area - want) < want * 1e-6:
                c.add(p)
        assert c.count == 1, sk.name + ': no profile matched the annulus area'
        return extrude(c, op, z0_expr, dz_expr, name)

    def rect(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk, x0, y0), mpt(sk, x1, y1))
        return extrude(one(sk), op, z0_expr, dz_expr, name)

    def arc_slot(name, r_in, r_out, half_ang, mid_ang, z0_expr, dz_expr, op):
        """An annular sector with square ends. Four curves, closed by hand -
        Fusion will not infer the sector from two full circles."""
        sk = sketch(name)
        arcs = sk.sketchCurves.sketchArcs
        lines = sk.sketchCurves.sketchLines
        a0, a1 = mid_ang - half_ang, mid_ang + half_ang
        am = mid_ang

        def p(r, a):
            return mpt(sk, r * math.cos(a), r * math.sin(a))

        arcs.addByThreePoints(p(r_out, a0), p(r_out, am), p(r_out, a1))
        arcs.addByThreePoints(p(r_in, a0), p(r_in, am), p(r_in, a1))
        lines.addByTwoPoints(p(r_in, a0), p(r_out, a0))
        lines.addByTwoPoints(p(r_in, a1), p(r_out, a1))
        return extrude(one(sk), op, z0_expr, dz_expr, name)

    # ---- values in cm --------------------------------------------------------
    cap_t = tval('cap_t')
    cap_r = tval('cap_r')
    under = -cap_t                       # the cap's underside plane
    half = tval('bolt_pitch') / 2
    bolt_r = half * math.sqrt(2.0)
    lug_hw = tval('lug_w') / 2
    lug_arc = 2 * math.degrees(math.atan2(lug_hw, tval('lug_or')))
    travel = 180.0 - lug_arc

    # ---- sanity, before any geometry ----------------------------------------
    assert abs(tval('axle_z') + (cap_t + tval('roller_od') / 2)) < 1e-9, (
        'tt_axle_z is %.2f but the rollers touch this cap at z %.2f and are %.1f '
        'across, so it must be %.2f - it is meant to be derived, not typed' % (
            tval('axle_z') * 10, under * 10, tval('roller_od') * 10,
            -(cap_t + tval('roller_od') / 2) * 10))
    assert val('track_out') < cap_r - val('wall'), (
        'the roller track reaches r %.1f on a cap only %.1f in radius'
        % (val('track_out') * 10, cap_r * 10))
    assert bolt_r + tval('head_d') / 2 + val('wall') < val('track_in'), (
        'the bolt head counterbores reach r %.1f and the track starts at r %.1f - '
        'the rollers would run over them' % (
            (bolt_r + tval('head_d') / 2) * 10, val('track_in') * 10))
    assert val('cable_or') + val('wall') < bolt_r - tval('bolt_clear') / 2, (
        'the cable window reaches r %.1f and the bolt holes start at r %.1f'
        % (val('cable_or') * 10, (bolt_r - tval('bolt_clear') / 2) * 10))
    assert val('roof') >= val('wall') - 1e-9, (
        'only %.2f mm of roof over the horn recess - the pocket breaks through the '
        'mounting face' % (val('roof') * 10))
    # The pocket and the head counterbore do NOT stack: each bolt stands on a
    # boss that fills the pocket back flush, so the counterbore is cut from a
    # full-thickness plate. Check each against what it actually sits in.
    assert tval('head_h') + val('wall') <= cap_t + 1e-9, (
        'a %.1f head counterbore leaves under a wall in a %.1f plate'
        % (tval('head_h') * 10, cap_t * 10))
    assert val('boss_d') >= tval('head_d') + 2 * val('wall') - 1e-9, (
        'the %.1f bolt boss does not leave a wall around a %.1f head counterbore'
        % (val('boss_d') * 10, tval('head_d') * 10))
    assert val('mouth_d') > val('hub_bore'), 'the mouth is narrower than the bore below it'
    assert travel > 120.0, (
        'a %.1f deg lug leaves only %.1f deg of locked travel' % (lug_arc, travel))

    # ---- phase 1: cap form ----------------------------------------------------
    t0 = design.timeline.count
    circle('disc', 0, 0, 2 * cap_r, mm(under), TURRET + 'cap_t', NEW)
    # Two lugs, on +-X, so they are axis-aligned rectangles. They hang from the
    # underside; the base's lip closes over them.
    for i, sx in enumerate((+1, -1)):
        x0 = sx * (cap_r - val('wall'))          # overlap the rim, never touch it
        x1 = sx * tval('lug_or')
        rect('lug_%d' % i, min(x0, x1), max(x0, x1), -lug_hw, lug_hw,
             mm(under), TURRET + 'lug_t', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: track and lightening ----------------------------------------
    # The track is not added, it is what is LEFT: two underside pockets, one
    # either side of the band the rollers run on. Cutting it this way means the
    # track can never be a different height from the rim it is measured against.
    t1 = design.timeline.count
    ring('pocket_inner', val('track_in'), val('hub_r'), mm(under), PREFIX + 'pocket_z', CUT)
    ring('pocket_outer', cap_r - val('wall'), val('track_out'),
         mm(under), PREFIX + 'pocket_z', CUT)
    for i, sx in enumerate((-1, +1)):
        for j, sy in enumerate((-1, +1)):
            circle('bolt_boss_%d%d' % (i, j), sx * half, sy * half, val('boss_d'),
                   mm(under), PREFIX + 'pocket_z', JOIN)
    group(t1, PH_TRACK)

    # ---- phase 3: horn interface ----------------------------------------------
    # Three steps, same shape as shoulder_hub's and for the same reason: the
    # arms have to travel down a mouth wide enough to pass them before they can
    # turn into their slot.
    t2 = design.timeline.count
    circle('horn_mouth', 0, 0, val('mouth_d'), mm(under), PREFIX + 'mouth_z', CUT)
    circle('horn_bore', 0, 0, val('hub_bore'), mm(under + val('mouth_z')),
           PREFIX + 'bore_z', CUT)
    for ang, tag in ((0, 'a'), (1, 'b')):
        if ang == 0:
            rect('horn_arm_' + tag, -val('arm_r'), val('arm_r'),
                 -val('arm_w') / 2, val('arm_w') / 2,
                 mm(under + val('mouth_z')), PREFIX + 'blade_z', CUT)
        else:
            rect('horn_arm_' + tag, -val('arm_w') / 2, val('arm_w') / 2,
                 -val('arm_r'), val('arm_r'),
                 mm(under + val('mouth_z')), PREFIX + 'blade_z', CUT)
    group(t2, PH_HORN)

    # ---- phase 4: bracket interface --------------------------------------------
    t3 = design.timeline.count
    for i, sx in enumerate((-1, +1)):
        for j, sy in enumerate((-1, +1)):
            circle('bolt_%d%d' % (i, j), sx * half, sy * half, tval('bolt_clear'),
                   mm(under), TURRET + 'cap_t', CUT)
            circle('head_%d%d' % (i, j), sx * half, sy * half, tval('head_d'),
                   mm(under), TURRET + 'head_h', CUT)
    # The loom, behind the arm. Neutral is J1 = 90, so -Y is astern.
    arc_slot('cable_window', val('cable_ir'), val('cable_or'),
             val('cable_deg') / 2, -math.pi / 2, mm(under), TURRET + 'cap_t', CUT)
    group(t3, PH_BOLTS)

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a lug or a bolt boss is not touching the disc'
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
    print('body: %r | material: %s | appearance: %s' % (
        body.name, body.material.name, used_appearance))
    print('cap: r %.1f x %.1f thick, top face z 0 = the bracket mounting plane' % (
        cap_r * 10, cap_t * 10))
    print('track: flat band r %.1f..%.1f on the underside, 3 x 608ZZ (%.1f od x %.1f) '
          'at r %.1f, axles at z %.1f' % (
              val('track_in') * 10, val('track_out') * 10, tval('roller_od') * 10,
              tval('roller_w') * 10, tval('roller_r') * 10, tval('axle_z') * 10))
    print('bayonet: 2 lugs %.1f wide to r %.1f, %.1f thick -> lug arc %.1f deg, '
          'LOCKED TRAVEL %.1f deg (J1 = 15..165, assembly at 0)' % (
              tval('lug_w') * 10, tval('lug_or') * 10, tval('lug_t') * 10,
              lug_arc, travel))
    print('bracket: 4 x %.1f clearance on a %.1f square (r %.2f), heads %.1f x %.1f '
          'counterbored from below' % (
              tval('bolt_clear') * 10, tval('bolt_pitch') * 10, bolt_r * 10,
              tval('head_d') * 10, tval('head_h') * 10))
    print('horn: mouth %.2f x %.2f, blade slot r %.1f x %.2f, bore %.2f x %.1f, '
          'roof %.2f' % (
              val('mouth_d') * 10, val('mouth_z') * 10, val('arm_r') * 10,
              val('arm_w') * 10, val('hub_bore') * 10, val('bore_z') * 10,
              val('roof') * 10))
    print('lightening: underside pockets %.1f deep, r %.1f..%.1f and r %.1f..%.1f; '
          'cable arc r %.1f..%.1f over %.0f deg' % (
              val('pocket_z') * 10, val('hub_r') * 10, val('track_in') * 10,
              val('track_out') * 10, (cap_r - val('wall')) * 10,
              val('cable_ir') * 10, val('cable_or') * 10,
              math.degrees(val('cable_deg'))))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 1000 * 0.6, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
