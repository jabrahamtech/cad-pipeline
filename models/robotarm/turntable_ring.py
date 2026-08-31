"""robotarm/turntable_ring - Fusion MCP generating script.

Rebuilds `robotarm_turntable_ring` (idempotent). Spec:
specs/robotarm/base_platter_measured.md.

The retainer. One flat annulus that does the two jobs the legacy base needed
three separate clips and three extra heat-set inserts for:

  UPLIFT    its underside hooks over the rotor's rim with tt_ring_lift of
            daylight, so the arm cannot tip the turntable off its rollers
  RADIAL    its BORE is a journal on the rotor's Ø68 raised boss - that is
            what locates the arm on the yaw axis, and without it three
            radial-axled rollers locate nothing at all sideways

Local frame: origin ON THE J1 YAW AXIS at the PLATTER'S RIM TOP, the same
frame turntable_stator uses. This part sits at z = tt_race_z + tt_disc_t +
tt_ring_lift and is fixed by the same three M3 that hold the stator down -
one screw per post, through this ring, down the post, into the platter.

WHY A RING AND NOT CLIPS. Three clips have to be bolted on AFTER the rotor is
in, each into its own insert, each set by hand to the same 0.4 mm gap. A ring
lands on three posts that were printed to height, so the gap is a printed
dimension rather than an assembly skill, and there is one part instead of
three. It also closes the joint visually at every angle, which three clips
never do.

THE BORE IS A RUNNING FIT, NOT A CLEARANCE HOLE. Ø68 turning in Ø68.35 is
0.35 of diametral slop - design_rules `rotating` - which at r 34 is under
0.01 deg of play at the shoulder. Open it up "to be safe" and the arm gets a
wobble that multiplies by five before it reaches the blades.

Print orientation: FLAT. It is an annulus; there is no second option and no
support anywhere.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_turntable_ring'
BODY_NAME = 'turntable_ring'
PREFIX = 'tr_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_FORM = 'ring form'
PH_SCALLOP = 'scallops'
PH_FIX = 'fixings'
PHASES = [PH_FORM, PH_SCALLOP, PH_FIX]

# The reference arm's base flange is a lobed cog, not a plain disc, and it is
# the single most recognisable thing in the photo. Twelve lobes because the
# spacing MUST divide 60 deg - the three M3 posts sit at az 120/180/240 and
# every one of them has to land on a lobe, not in a notch. 6 works too and
# reads too coarse; 9 does not contain 180.
SCALLOP_N = 12
SCALLOP_AZ0 = 15.0        # halfway between lobes, so lobes land on 0/30/60...
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. The base is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('turntable_ring')


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

    # ---- the SHARED turntable contract, the members this part consumes ------
    # Every member is defined identically wherever it appears. turntable_stator
    # carries the full block.
    turret('post_r', '45.0 mm',
           'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
           '           top face at its rim, az 120/180/240. The ONLY fixing there is.')
    turret('bolt_d', '3.4 mm',
           'M3 clearance. One screw per post runs the whole stack - through the\n'
           '           ring, down the post, into the platter insert. About 40 long.')
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - DRAWING-CONFIRMED')
    turret('axle_z', '13.1 mm',
           'roller axle height. Set so the bearing clears the platter top by 1.0 -\n'
           '           any lower and a 608 fouls the lid.')
    turret('race_z', TURRET + 'axle_z + ' + TURRET + 'roller_od / 2',
           'derived: where the rotor\'s underside sits. NEVER type this.')
    turret('disc_d', '76.0 mm',
           'rotor diameter. Not free: the MG995 pad on the shoulder bracket reaches\n'
           '           r 32.1, and the ring has to hook over the rim outside that.')
    turret('disc_t', '5.0 mm', 'rotor rim thickness, where the ring hooks over it')
    turret('boss_d', '68.0 mm',
           'the rotor\'s raised centre. This is the JOURNAL - it turns inside this\n'
           '           ring\'s bore, and it is what locates the arm radially.')
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

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'silhouette corner radius - SHARED, do not retune it here')

    # ---- fits ---------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('rot', '0.35 mm', 'rotating fit - design_rules. THE fit in this part.')
    param('head_d', '6.5 mm', 'M3 socket head 5.5 + clearance')
    param('head_z', '2.4 mm', 'M3 socket head 3.0 recessed until 1.6 of ring is left')
    param('bore_d', TURRET + 'boss_d + ' + PREFIX + 'rot',
          'derived: the journal. Ø68 turning in Ø68.35.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')
    param('scallop_r', '6.0 mm', 'radius of each notch cut into the rim')
    param('scallop_cr', '53.0 mm',
          'centre radius of the notch circles. At 53.0 with r 6.0 the cut\n'
          '           reaches in to r 47.0, leaving 12.8 mm of web over the 34.2 bore\n'
          '           and clearing the M3 heads by a wide margin - see the assertion.')

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
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mxy(sk, x, y):
        return sk.modelToSketchSpace(P3(x, y, 0))

    def mm(cm):
        """cm -> a millimetre EXPRESSION. createByString reads a bare number as
        millimetres; val() hands out centimetres. See fusion/PLAYBOOK.md."""
        return '%.4f mm' % (cm * 10.0)

    def extrude(profs, op, z0, dz, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0))
        inp.setDistanceExtent(False, V(dz))
        if op != NEW:
            # Without this a CUT eats every other component. See PLAYBOOK.md.
            inp.participantBodies = [comp.bRepBodies.item(i)
                                     for i in range(comp.bRepBodies.count)]
        f = ext.add(inp)
        f.name = name
        return f

    def one(sk):
        assert sk.profiles.count == 1, (
            sk.name + ': expected 1 profile, got %d' % sk.profiles.count)
        c = adsk.core.ObjectCollection.create()
        c.add(sk.profiles.item(0))
        return c

    def xy_circle(name, x, y, d, z0, dz, op):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, x, y), d / 2)
        return extrude(one(sk), op, z0, dz, name)

    def group(start_index, name):
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    # ---- values in cm --------------------------------------------------------
    ring_z = tval('race_z') + tval('disc_t') + tval('ring_lift')
    boss_top = tval('race_z') + tval('disc_t') + tval('boss_h')
    engage = boss_top - ring_z
    POST_AZ = (120.0, 180.0, 240.0)

    # ---- sanity, before any geometry ----------------------------------------
    assert val('bore_d') < tval('disc_d'), (
        'the bore is wider than the rotor - there would be nothing to hook over')
    # THESE ARE IN MILLIMETRES. val()/tval() hand out CENTIMETRES, so the
    # comparison is done on the *10 form and not on the raw value - written the
    # other way round this assertion fired on a perfectly good 3.8 mm lap.
    # See fusion/PLAYBOOK.md.
    overlap_mm = (tval('disc_d') - val('bore_d')) / 2 * 10
    engage_mm = engage * 10
    assert overlap_mm >= 1.5, (
        'the ring only laps the rotor rim by %.2f mm - not enough to hold it down'
        % overlap_mm)
    assert engage_mm >= 2.5, (
        'the journal only engages %.2f mm of the rotor boss; it needs enough depth '
        'to resist tilt, not just to touch' % engage_mm)
    assert tval('ring_or') > tval('post_r') + val('head_d') / 2 + val('wall'), (
        'the ring reaches r %.1f but a bolt head at r %.1f needs %.1f more'
        % (tval('ring_or') * 10, tval('post_r') * 10,
           (val('head_d') / 2 + val('wall')) * 10))
    assert val('head_z') + val('wall') <= tval('ring_t') + 1e-9, (
        'a %.1f head counterbore leaves under a wall in a %.1f ring'
        % (val('head_z') * 10, tval('ring_t') * 10))
    # The shoulder bracket's MG995 pad reaches r 32.1 and stands ON the boss.
    PAD_R_MM = 32.1
    assert tval('boss_d') * 10 / 2 > PAD_R_MM, (
        'the rotor boss is r %.1f but the MG995 pad that stands on it reaches r %.1f'
        % (tval('boss_d') * 10 / 2, PAD_R_MM))

    # ---- phase 1: ring form ---------------------------------------------------
    t0 = design.timeline.count
    sk = sketch('ring')
    for r in (tval('ring_or'), val('bore_d') / 2):
        sk.sketchCurves.sketchCircles.addByCenterRadius(mxy(sk, 0, 0), r)
    assert sk.profiles.count == 2, 'sk_ring: got %d profiles' % sk.profiles.count
    want = math.pi * (tval('ring_or') ** 2 - (val('bore_d') / 2) ** 2)
    col = adsk.core.ObjectCollection.create()
    for i in range(2):
        p = sk.profiles.item(i)
        if abs(p.areaProperties().area - want) < want * 1e-6:
            col.add(p)
    assert col.count == 1, 'no profile matched the ring annulus'
    extrude(col, NEW, mm(ring_z), TURRET + 'ring_t', 'ring')
    group(t0, PH_FORM)

    # ---- phase 2: scallops -----------------------------------------------------
    # Cut the notches BEFORE the bolt holes: the assertion below is what proves
    # a notch never eats a fixing, and it wants both sets of numbers, not a
    # visual check after the fact.
    ts = design.timeline.count
    s_r = val('scallop_r')
    s_cr = val('scallop_cr')
    # EVERY COMPARISON BELOW IS IN MILLIMETRES. val()/tval() return Fusion's
    # internal CENTIMETRES, and comparing one of those against a bare 1.6 makes
    # the wall ten times too thick - which is exactly how the first version of
    # this assertion failed on geometry that was fine. Convert once, compare
    # never in mixed units. fusion/PLAYBOOK.md has the running tally.
    s_r_mm = s_r * 10
    s_cr_mm = s_cr * 10
    post_r_mm = tval('post_r') * 10
    bore_r_mm = tval('boss_d') / 2 * 10
    head_r_mm = val('head_d') / 2 * 10
    WALL_MM = 1.6
    reach_in_mm = s_cr_mm - s_r_mm
    assert reach_in_mm > bore_r_mm + WALL_MM, (
        'the scallops reach r %.1f mm and the bore is r %.1f mm - less than a '
        'wall left' % (reach_in_mm, bore_r_mm))
    for i in range(SCALLOP_N):
        az = SCALLOP_AZ0 + i * 360.0 / SCALLOP_N
        a = math.radians(az)
        # no notch may come near a fixing head
        for paz in POST_AZ:
            d_mm = math.sqrt(s_cr_mm ** 2 + post_r_mm ** 2
                             - 2 * s_cr_mm * post_r_mm
                             * math.cos(math.radians(az - paz)))
            assert d_mm > s_r_mm + head_r_mm + WALL_MM, (
                'scallop at az %.0f is %.1f mm from the M3 head at az %.0f - it '
                'would break into the counterbore' % (az, d_mm, paz))
        xy_circle('scallop_%d' % i, s_cr * math.cos(a), s_cr * math.sin(a),
                  s_r * 2, mm(ring_z), TURRET + 'ring_t', CUT)
    group(ts, PH_SCALLOP)

    # ---- phase 3: fixings ------------------------------------------------------
    t1 = design.timeline.count
    for i, az in enumerate(POST_AZ):
        a = math.radians(az)
        x, y = tval('post_r') * math.cos(a), tval('post_r') * math.sin(a)
        xy_circle('bolt_%d' % i, x, y, tval('bolt_d'), mm(ring_z), TURRET + 'ring_t', CUT)
        xy_circle('head_%d' % i, x, y, val('head_d'),
                  mm(ring_z + tval('ring_t') - val('head_z')), PREFIX + 'head_z', CUT)
    group(t1, PH_FIX)

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d' % comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used = 'none'
    for want_a in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a_ = apps.item(j)
                if all(w.lower() in a_.name.lower() for w in want_a):
                    body.appearance = a_
                    used = a_.name
                    break
            if used != 'none':
                break
        if used != 'none':
            break

    bb = body.boundingBox
    print('body: %r | material: %s | appearance: %s' % (body.name, body.material.name, used))
    print('ring: bore %.2f x OD %.1f x %.1f thick, underside z %.2f, top z %.2f' % (
        val('bore_d') * 10, tval('ring_or') * 20, tval('ring_t') * 10,
        ring_z * 10, (ring_z + tval('ring_t')) * 10))
    print('UPLIFT: laps the %.1f rotor rim by %.2f mm, with %.2f of daylight under it' % (
        tval('disc_d') * 10, overlap_mm, tval('ring_lift') * 10))
    print('RADIAL: journal on the rotor\'s %.1f boss, %.2f of clearance, %.2f engaged' % (
        tval('boss_d') * 10, val('rot') * 10, engage_mm))
    print('SCALLOPS: %d lobes, notch r %.1f centred at r %.1f, reaching in to r %.1f'
          % (SCALLOP_N, val('scallop_r') * 10, val('scallop_cr') * 10,
             (val('scallop_cr') - val('scallop_r')) * 10))
    print('  lobes at az %s - every M3 post lands on a lobe'
          % ([round(SCALLOP_AZ0 + 180.0 / SCALLOP_N + i * 360.0 / SCALLOP_N)
              for i in range(SCALLOP_N)]))
    print('fixings: 3 x %.1f clearance at r %.1f az %s, heads %.1f x %.1f recessed' % (
        tval('bolt_d') * 10, tval('post_r') * 10, POST_AZ,
        val('head_d') * 10, val('head_z') * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 1000 * 0.6, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
