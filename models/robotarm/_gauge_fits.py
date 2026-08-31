"""robotarm/_gauge_fits - SUPERSEDED by _gauge_slim.py. Kept as a fallback.

    DO NOT PRINT THIS unless _gauge_slim has a problem on the bed. It is
    117,941 mm3 / 3h10m against the slim plate's 77,184 / ~2h, and it answers
    the same questions - it just prints eight three-way sweeps that
    lib/gauge_reduce.py now derives from a wider truth row instead. Its hex
    sockets are also 4.0 deep where the arm ships 3.4, so it measures a
    stiffer joint than the one being built.

    Original header follows.

    ---

robotarm/_gauge_fits - the fit-identification gauge.

Rebuilds `robotarm_gauge_fits` (idempotent). Three bodies, one bed:

  gauge_plate   every FEMALE feature, swept, with the value engraved beside it
  gauge_lever   ONE hex boss at the nominal 15.80, on a 60 mm arm
  gauge_plug    ONE journal collar at a true Ø20.00

THE SWEEP IS ON THE FEMALE SIDE ONLY, and that is the whole design. One
lever tests four hex clearances; one plug tests three journal clearances.
Sweeping both sides would need twelve probes and would confound which half
moved. Clearance is symmetric, so sweeping the hole answers the same
question - and calipering the printed boss against the printed hole is what
tells us which way THIS machine biases.

WHAT IT ANSWERS, in the order the audit ranked them:

  hex        4 sockets, clearance 0.10 / 0.20 / 0.30 / 0.40 against the lever,
             so the sockets measure 15.90 / 16.00 / 16.10 / 16.20 across flats.
             The 0.20 station IS the arm as it ships - same 15.80 boss, same
             16.00 socket - so it doubles as the control.
             0.20 is what the arm ships today and it buys 1.28 deg of play at
             every pitch joint - the largest single term in a 22 mm tip error.
  journal    3 bores, clearance 0.25 / 0.35 / 0.45 on a Ø20 collar. 0.35 is
             today's, and at +-0.15 per printed dimension it is predicted to
             land anywhere between binding and 0.65 of slop.
  608 pocket 3 pockets, 0.00 / 0.05 / 0.10. Not used in the arm yet - it is
             the prerequisite for putting real bearings in the pitch joints.
  pilots     M3 self-tap 2.4/2.5/2.6, M2 servo screw 1.6/1.7/1.8.
  horn       SG90 hub bore 7.05 / 7.15 / 7.25 - the press that currently
             holds a servo horn into a hub.
  MACHINE    a true Ø20.00 boss, a true Ø20.00 bore, and a 20 x 10 x 5 block.
  TRUTH      Caliper these three and you have this printer's real bias in X,
             Y and Z and for inside vs outside features. EVERY other number
             on this plate is read through them.

PLATE B carries the four things plate A does not reach, each tied to a named
audit item:

  MG995 horn 12.05 / 12.15 / 12.25. Plate A tests the SG90 horn; the press
             that holds the WHOLE ARM up at J2 is the MG995 one (J6).
  sliding    slots 10.15 / 10.25 / 10.35 on the lever's own 10.00 arm - the
             `sliding` fit, which nothing on plate A exercises.
  stub axle  Ø7.80 / 7.90 / 8.00 into a real 608 bore, VERTICAL - plus one
             more at 7.90 lying HORIZONTAL, because that is the orientation
             turntable_stator actually prints its axles in, and a round hole
             is not the same size in the two directions.
  M3 insert  3.9 / 4.0 / 4.1 for heat-set bosses, which tier 2 and 3 of the
             fix ladder both want and no part uses yet.

Print A alone if you only want the answer to the 22 mm. Print both to close
every fit in lib/design_rules.

The machine-truth row is the one people skip and it is the one that matters
most: a fit is a difference between two printed features, so without knowing
the bias you cannot tell a bad CLEARANCE from a bad PRINTER.

The 608 pockets sit directly over the journal bores at the same three
stations - Ø22 pocket down from the top, Ø20 bore below it, a Ø10 push-out
through the floor so the bearing comes back out with a rod. Two fits per
station, half the plate area.

Print: PETG, plate flat, engraved face UP, no support, 0.2 mm layers, 20 %
infill, 3 walls. Print it with the SAME profile the real parts will use -
a gauge printed at a different layer height is measuring a different machine.

Record results in calibration/ as a dated note, then change lib/design_rules
only if the gauge indicates it.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_gauge_fits'
PREFIX = 'gg_'
STYLE = 'sty_'
PH_PLATE = 'plate'
PH_STATIONS = 'stations'
PH_LABELS = 'labels'
PH_PROBES = 'probes'
PH_B = 'plate B'
PHASES = [PH_PLATE, PH_STATIONS, PH_LABELS, PH_PROBES, PH_B]
MATERIAL_NAME = 'PET Plastic'

# ---- the sweeps. Every number here is a CLEARANCE unless it says otherwise.
HEX_SOCKET_AF = 16.0          # the wr_ contract socket
HEX_LEVER_AF = 15.80          # the wr_ contract hub - the one probe
HEX_CLEAR = [0.10, 0.20, 0.30, 0.40]        # 0.20 is today's

JOURNAL_PLUG_D = 20.00        # the wr_ hub collar - the one probe
JOURNAL_CLEAR = [0.25, 0.35, 0.45]          # 0.35 is today's

BEARING_OD = 22.0             # 608ZZ
BEARING_CLEAR = [0.00, 0.05, 0.10]          # 0.05 is the handbook value

M3_PILOT = [2.4, 2.5, 2.6]    # 2.5 is what the turntable uses, 2.6 is the rule
M2_PILOT = [1.6, 1.7, 1.8]    # 1.8 is SERVO_SCREW_PILOT_MM
HORN_BORE = [7.05, 7.15, 7.25]              # 7.15 is today's SG90 hub press

# ---- PLATE B: the four fits plate A does not reach ------------------------
MG995_HORN = [12.05, 12.15, 12.25]   # 12.15 is today's - THE press that holds
                                     # the whole arm up at J2 (audit item J6)
SLIDE_W = [10.15, 10.25, 10.35]      # `sliding` 0.25 - the rack in its channel.
                                     # The lever's 10.00 arm is the probe.
STUB_D = [7.80, 7.90, 8.00]          # printed axle INTO a 608 bore, vertical
STUB_H_D = 7.90                      # the same axle HORIZONTAL - which is how
                                     # turntable_stator actually prints it
M3_INSERT = [3.9, 4.0, 4.1]          # M3_INSERT_HOLE_DIA_MM is 4.0 CALIBRATED
COLLAR_D = [10.0, 11.0, 12.0]        # THE BEARING SEAT. The only surface it may
                                     # touch is the inner race FACE - an annulus
                                     # from the 8.0 bore to the 12.0 race OD.
                                     # Wider than 12.0 and it reaches over the
                                     # gap toward the ZZ shield, which is fixed
                                     # to the OUTER race. turntable_stator had
                                     # 12.5, which overhung. This row settles it
                                     # by experiment instead of by argument.
COLLAR_STUB_D = 7.90                 # all three on the same nominal axle
BEARING_W = 7.0                      # 608ZZ width
BEARING_BORE = 8.0
RACE_OD = 12.0                       # 608ZZ inner race OD - lib/bearings.py

# ---- roller_cap: the retainer, printed --------------------------------------
# A standard M3 washer is Ø7 and falls THROUGH the 608's Ø8 bore. Every bought
# alternative needs an order; this needs 0.4 g. The spigot centres it in the
# bore so it cannot sit skew and rub the shield.
CAP_FLANGE_D = 11.0
CAP_FLANGE_T = 1.6
CAP_SPIGOT_D = 7.60
CAP_SPIGOT_H = 1.2
CAP_BORE = 3.4
LEVER_ARM_W = 10.0                   # must match the lever built below


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value

    param('base_t', '3.0 mm', 'plate thickness away from the stations')
    param('hex_depth', '4.0 mm', 'socket depth - the arm uses 3.4, this is deeper')
    param('journal_depth', '5.0 mm', 'the arm journal is wr_journal = 5.0')
    param('pocket_depth', '3.5 mm', 'half a 608 - enough to judge, easy to push out')
    param('floor_t', '1.5 mm', 'between the 608 pocket and the journal bore')
    param('label_z', '0.6 mm', 'engraving depth - design_rules MIN_EMBOSS_MM')
    param('tol', '0.001 mm', 'edge-selection tolerance, not a dimension')

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

    def sketch(name):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        return sk

    def mm(x):
        return '%.4f mm' % x

    def pt(sk, x, y):
        return sk.modelToSketchSpace(P3(x / 10.0, y / 10.0, 0))

    def extrude_profs(profs, op, z0, dz, name, targets=None):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z0)))
        inp.setDistanceExtent(False, V(mm(dz)))
        if op != NEW:
            bodies = targets if targets is not None else [
                comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
            # Without this a CUT eats every other component. See PLAYBOOK.md.
            inp.participantBodies = bodies
        f = ext.add(inp)
        f.name = name
        return f

    def one(sk):
        assert sk.profiles.count == 1, (
            sk.name + ': expected 1 profile, got %d' % sk.profiles.count)
        c = adsk.core.ObjectCollection.create()
        c.add(sk.profiles.item(0))
        return c

    def circle(name, x, y, d, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(sk, x, y), d / 20.0)
        return extrude_profs(one(sk), op, z0, dz, name, targets)

    def rect(name, x0, x1, y0, y1, z0, dz, op, targets=None):
        sk = sketch(name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(sk, x0, y0), pt(sk, x1, y1))
        return extrude_profs(one(sk), op, z0, dz, name, targets)

    def hexagon(name, x, y, af, z0, dz, op, targets=None):
        sk = sketch(name)
        r_c = (af / 20.0) / math.cos(math.pi / 6)
        pts = [(r_c * math.cos(2 * math.pi * i / 6 + math.pi / 6),
                r_c * math.sin(2 * math.pi * i / 6 + math.pi / 6)) for i in range(6)]
        lines = sk.sketchCurves.sketchLines
        for i in range(6):
            a, b = pts[i], pts[(i + 1) % 6]
            lines.addByTwoPoints(
                sk.modelToSketchSpace(P3(x / 10.0 + a[0], y / 10.0 + a[1], 0)),
                sk.modelToSketchSpace(P3(x / 10.0 + b[0], y / 10.0 + b[1], 0)))
        return extrude_profs(one(sk), op, z0, dz, name, targets)

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    # ---- layout, all in MILLIMETRES in the plate's own frame -----------------
    BASE_X, BASE_Y = 96.0, 124.0
    base_t = val('base_t') * 10
    ROW_TRUTH, ROW_STA, ROW_HEX, ROW_SMALL = 46.0, 8.0, -26.0, -52.0
    # label bands: clear strips of BASE between the rows. Engraving happens on
    # the base's top face, so a label under a raised pad would be buried.
    LAB_TRUTH, LAB_STA, LAB_HEX = 28.0, -9.0, -41.0
    STA_X = [-30.0, 0.0, 30.0]
    HEX_X = [-36.0, -12.0, 12.0, 36.0]
    HEX_PAD = 23.0
    SMALL_PAD_H = 5.0

    pocket_d = val('pocket_depth') * 10
    journal_d = val('journal_depth') * 10
    floor_t = val('floor_t') * 10
    sta_pad_h = pocket_d + journal_d + floor_t          # 10.0
    hex_d = val('hex_depth') * 10
    hex_pad_h = hex_d + 1.5

    # ---- sanity, before any geometry ----------------------------------------
    assert min(HEX_CLEAR) > 0, 'a zero-clearance hex will not assemble to be measured'
    assert HEX_LEVER_AF < HEX_SOCKET_AF, 'the lever must be under the nominal socket'
    hex_pitch = HEX_X[1] - HEX_X[0]
    hex_across_corners = (HEX_LEVER_AF + max(HEX_CLEAR)) / math.cos(math.pi / 6)
    assert hex_pitch > hex_across_corners + 3.0, (
        'hex sockets at %.1f pitch overlap - they are %.2f across corners'
        % (hex_pitch, hex_across_corners))
    assert HEX_PAD - hex_across_corners >= 2 * 1.6 - 1e-9, (
        'a %.1f hex pad leaves %.2f of wall round a %.2f socket'
        % (HEX_PAD, (HEX_PAD - hex_across_corners) / 2, hex_across_corners))
    assert abs((HEX_LEVER_AF + HEX_CLEAR[1]) - HEX_SOCKET_AF) < 1e-9, (
        'the middle hex station is meant to BE the arm as it ships - lever %.2f + '
        '%.2f should equal the wr_ socket %.2f'
        % (HEX_LEVER_AF, HEX_CLEAR[1], HEX_SOCKET_AF))
    sta_pad_d = BEARING_OD + max(BEARING_CLEAR) + 2 * 2.0
    assert (STA_X[1] - STA_X[0]) > sta_pad_d + 2.0, 'the station pads overlap'
    assert sta_pad_d / 2 + abs(STA_X[-1]) < BASE_X / 2, 'a station pad hangs off the plate'
    assert floor_t >= 1.2, 'less than a wall between the 608 pocket and the journal bore'

    # ---- phase 1: the plate --------------------------------------------------
    t0 = design.timeline.count
    sk = sketch('base')
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        pt(sk, -BASE_X / 2, -BASE_Y / 2), pt(sk, BASE_X / 2, BASE_Y / 2))
    extrude_profs(one(sk), NEW, 0.0, base_t, 'base')
    plate = comp.bRepBodies.item(0)
    plate.name = 'gauge_plate'
    # No lightening windows: the strips between the rows are where the labels
    # get engraved, and a label cut over a hole loses half its glyphs.
    group(t0, PH_PLATE)

    # ---- phase 2: the stations -----------------------------------------------
    t1 = design.timeline.count
    # MACHINE TRUTH - the three references everything else is read through
    circle('truth_boss', -32.0, ROW_TRUTH, 20.00, 0.0, base_t + 6.0, JOIN, [plate])
    circle('truth_bore_pad', -2.0, ROW_TRUTH, 28.0, 0.0, base_t + 6.0, JOIN, [plate])
    circle('truth_bore', -2.0, ROW_TRUTH, 20.00, base_t + 6.0, -6.0, CUT, [plate])
    rect('truth_block', 18.0, 38.0, ROW_TRUTH - 5.0, ROW_TRUTH + 5.0,
         base_t, 5.0, JOIN, [plate])

    # JOURNAL + 608, stacked at one station
    for i, x in enumerate(STA_X):
        circle('sta_pad_%d' % i, x, ROW_STA, sta_pad_d, 0.0, base_t + sta_pad_h,
               JOIN, [plate])
    for i, x in enumerate(STA_X):
        top = base_t + sta_pad_h
        circle('pocket_%d' % i, x, ROW_STA, BEARING_OD + BEARING_CLEAR[i],
               top, -pocket_d, CUT, [plate])
        circle('journal_%d' % i, x, ROW_STA, JOURNAL_PLUG_D + JOURNAL_CLEAR[i],
               top - pocket_d - floor_t, -journal_d, CUT, [plate])
        circle('pushout_%d' % i, x, ROW_STA, 10.0, -1.0, base_t + sta_pad_h + 2.0,
               CUT, [plate])

    # HEX - four sockets, one lever
    for i, x in enumerate(HEX_X):
        rect('hex_pad_%d' % i, x - HEX_PAD / 2, x + HEX_PAD / 2,
             ROW_HEX - HEX_PAD / 2, ROW_HEX + HEX_PAD / 2,
             0.0, base_t + hex_pad_h, JOIN, [plate])
    for i, x in enumerate(HEX_X):
        # Sized off the LEVER, not off the nominal socket. Sizing it off the
        # socket gave 0.30..0.60 of clearance while the engraving said 0.10..0.40.
        hexagon('hex_socket_%d' % i, x, ROW_HEX, HEX_LEVER_AF + HEX_CLEAR[i],
                base_t + hex_pad_h, -hex_d, CUT, [plate])

    # SMALL FEATURES - pilots and the horn press
    rect('small_pad', -44.0, 44.0, ROW_SMALL - 8.0, ROW_SMALL + 8.0,
         0.0, base_t + SMALL_PAD_H, JOIN, [plate])
    small_top = base_t + SMALL_PAD_H
    for i, d in enumerate(M3_PILOT):
        circle('m3_%d' % i, -38.0 + i * 9.0, ROW_SMALL, d, small_top, -6.0, CUT, [plate])
    for i, d in enumerate(M2_PILOT):
        circle('m2_%d' % i, -8.0 + i * 7.0, ROW_SMALL, d, small_top, -5.0, CUT, [plate])
    for i, d in enumerate(HORN_BORE):
        circle('horn_%d' % i, 16.0 + i * 11.0, ROW_SMALL, d, small_top, -4.0, CUT, [plate])
    group(t1, PH_STATIONS)

    # ---- phase 3: labels ------------------------------------------------------
    # ENGRAVE THE SKETCHTEXT, NOT ITS PROFILES. A SketchText does not populate
    # sketch.profiles on this Fusion build - the first version collected zero
    # and cut nothing, silently, leaving an unlabelled gauge that is worse than
    # no gauge because you cannot tell the stations apart. ExtrudeFeatures
    # accepts the SketchText object itself.
    t2 = design.timeline.count

    def engrave(name, items, z_top):
        """items: (x, y, text). One sketch per z level; one extrude per text."""
        cut = 0
        for j, (x, y, txt) in enumerate(items):
            sk = sketch('%s_%d' % (name, j))
            t_in = sk.sketchTexts.createInput2(txt, 0.35)
            t_in.setAsMultiLine(
                pt(sk, x - 14.0, y - 3.0), pt(sk, x + 14.0, y + 3.0),
                adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            st = sk.sketchTexts.add(t_in)
            inp = ext.createInput(st, CUT)
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z_top)))
            inp.setDistanceExtent(False, V(mm(-val('label_z') * 10)))
            inp.participantBodies = [plate]
            f = ext.add(inp)
            f.name = '%s_%d' % (name, j)
            cut += 1
        return cut

    base_labels = [(-32.0, LAB_TRUTH, 'D20'), (-2.0, LAB_TRUTH, 'B20'),
                   (28.0, LAB_TRUTH, 'BLOCK')]
    for i, x in enumerate(STA_X):
        base_labels.append((x, LAB_STA, '%02d/%02d' % (
            int(round(BEARING_CLEAR[i] * 100)), int(round(JOURNAL_CLEAR[i] * 100)))))
    for i, x in enumerate(HEX_X):
        base_labels.append((x, LAB_HEX, '%02d' % int(round(HEX_CLEAR[i] * 100))))
    n_base = engrave('lab_base', base_labels, base_t)

    # the small-feature strip labels go on the PAD's own top face - there is no
    # clear band of base left below it
    pad_labels = [(-29.0, ROW_SMALL + 5.5, 'M3'), (-2.0, ROW_SMALL + 5.5, 'M2'),
                  (27.0, ROW_SMALL + 5.5, 'SG90')]
    n_pad = engrave('lab_pad', pad_labels, base_t + SMALL_PAD_H)
    n_lab = n_base + n_pad
    group(t2, PH_LABELS)

    # ---- phase 4: the two probes ----------------------------------------------
    t3 = design.timeline.count
    LEVER_X, LEVER_Y = BASE_X / 2 + 22.0, -26.0
    LEVER_ARM = 60.0
    HUB_D, ARM_T = 24.0, 4.0
    # THE HEX MUST STAND PROUD OF THE HUB. First version put both from z 0 to 4
    # and the Ø24 hub simply swallowed an 18.2-across-corners hex - a disc with
    # nothing to insert. Hex on the bottom, everything else stacked above it.
    hexagon('lever_hex', LEVER_X, LEVER_Y, HEX_LEVER_AF, 0.0, hex_d, NEW)
    lever = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    lever.name = 'gauge_lever'
    circle('lever_hub', LEVER_X, LEVER_Y, HUB_D, hex_d, ARM_T, JOIN, [lever])
    rect('lever_arm', LEVER_X - 5.0, LEVER_X + 5.0, LEVER_Y, LEVER_Y + LEVER_ARM,
         hex_d, ARM_T, JOIN, [lever])
    rect('lever_tip', LEVER_X - 12.0, LEVER_X + 12.0,
         LEVER_Y + LEVER_ARM, LEVER_Y + LEVER_ARM + 6.0, hex_d, ARM_T, JOIN, [lever])

    # the plug: a true Ø20.00 collar on a disc you can grip. Parked well clear
    # of the lever's swing - the two overlapped in the first layout.
    PLUG_X, PLUG_Y = LEVER_X + 37.0, 0.0
    PLUG_GRIP_D = 32.0
    circle('plug_collar', PLUG_X, PLUG_Y, JOURNAL_PLUG_D, 0.0, journal_d, NEW)
    plug = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    plug.name = 'gauge_plug'
    circle('plug_grip', PLUG_X, PLUG_Y, PLUG_GRIP_D, journal_d, 4.0, JOIN, [plug])
    group(t3, PH_PROBES)

    # nothing may interpenetrate - these are three separate printed pieces
    lever_reach = LEVER_X + 12.0
    assert PLUG_X - PLUG_GRIP_D / 2 > lever_reach + 2.0, (
        'the plug at r %.1f overlaps the lever tip reaching x %.1f'
        % (PLUG_X - PLUG_GRIP_D / 2, lever_reach))
    assert LEVER_X - HUB_D / 2 > BASE_X / 2 + 2.0, 'the lever hub overlaps the plate'
    assert HUB_D / 2 > (HEX_LEVER_AF / 2) / math.cos(math.pi / 6), (
        'the hub is smaller than the hex it is supposed to sit on')

    # ---- phase 5: PLATE B ------------------------------------------------------
    t4 = design.timeline.count
    # Parked BELOW plate A, not beside it. Beside, the four pieces spanned
    # 274 mm of X against a 256 mm bed - the envelope assertion at the end of
    # this phase is there because I got that wrong first.
    PB_X, PB_Y = 0.0, -126.0
    PB_W, PB_H = 96.0, 104.0
    PB_ROW = {'horn': PB_Y + 34.0, 'slide': PB_Y + 4.0,
              'stub': PB_Y - 22.0, 'wall': PB_Y - 38.0, 'seat': PB_Y - 42.0}

    def cyl_y(name, x, z, d, y0, dy, op, targets=None):
        """A cylinder on a HORIZONTAL axis along Y. The stator's stub axles are
        built exactly like this, and a hole printed sideways is not the same
        size as the same hole printed up the Z axis - which is the entire
        reason this feature is on the plate."""
        sk = comp.sketches.add(comp.xZConstructionPlane)
        sk.name = 'sk_' + name
        c = sk.modelToSketchSpace(P3(x / 10.0, 0.0, z / 10.0))
        sk.sketchCurves.sketchCircles.addByCenterRadius(c, d / 20.0)
        return extrude_profs(one(sk), op, y0, dy, name, targets)

    rect('pb_base', PB_X - PB_W / 2, PB_X + PB_W / 2,
         PB_Y - PB_H / 2, PB_Y + PB_H / 2, 0.0, base_t, NEW)
    plate_b = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    plate_b.name = 'gauge_plate_b'

    # MG995 horn press - the one holding the arm up at J2
    horn_pad_h = base_t + 7.0
    for i2, d in enumerate(MG995_HORN):
        x = PB_X - 30.0 + i2 * 30.0
        circle('pb_horn_pad_%d' % i2, x, PB_ROW['horn'], d + 6.0, 0.0, horn_pad_h,
               JOIN, [plate_b])
    for i2, d in enumerate(MG995_HORN):
        x = PB_X - 30.0 + i2 * 30.0
        circle('pb_horn_%d' % i2, x, PB_ROW['horn'], d, horn_pad_h, -6.0,
               CUT, [plate_b])

    # sliding fit - the lever's own arm is the probe
    slide_pad_h = base_t + 6.0
    for i2, w in enumerate(SLIDE_W):
        x = PB_X - 30.0 + i2 * 30.0
        rect('pb_slide_pad_%d' % i2, x - 12.0, x + 12.0,
             PB_ROW['slide'] - 10.0, PB_ROW['slide'] + 10.0, 0.0, slide_pad_h,
             JOIN, [plate_b])
    for i2, w in enumerate(SLIDE_W):
        x = PB_X - 30.0 + i2 * 30.0
        rect('pb_slide_%d' % i2, x - w / 2, x + w / 2,
             PB_ROW['slide'] - 11.0, PB_ROW['slide'] + 11.0, slide_pad_h, -5.0,
             CUT, [plate_b])

    # printed axle into a real 608 bore - three vertical
    for i2, d in enumerate(STUB_D):
        x = PB_X - 30.0 + i2 * 16.0
        circle('pb_stub_%d' % i2, x, PB_ROW['stub'], d, base_t, 9.0, JOIN, [plate_b])
    # THE SPIN TEST. Same Ø7.90 axle, three seat diameters. Put a real 608 on
    # each and turn it: the one that spins freely is the seat, and the ones that
    # drag are landing on the shield. The plain stubs above answer whether the
    # BORE fits; only these answer whether it ROLLS.
    for i2, cd in enumerate(COLLAR_D):
        x = PB_X + 4.0 + i2 * 16.0
        circle('pb_seat_%d' % i2, x, PB_ROW['seat'], cd, base_t, 0.5, JOIN, [plate_b])
        circle('pb_seatstub_%d' % i2, x, PB_ROW['seat'], COLLAR_STUB_D,
               base_t + 0.5, BEARING_W + 2.0, JOIN, [plate_b])

    # M3 heat-set insert holes
    ins_pad_h = base_t + 7.0
    rect('pb_ins_pad', PB_X + 14.0, PB_X + 44.0, PB_ROW['stub'] - 8.0,
         PB_ROW['stub'] + 8.0, 0.0, ins_pad_h, JOIN, [plate_b])
    for i2, d in enumerate(M3_INSERT):
        circle('pb_ins_%d' % i2, PB_X + 20.0 + i2 * 9.0, PB_ROW['stub'], d,
               ins_pad_h, -6.0, CUT, [plate_b])

    # the SAME axle, lying down - TWICE. One bare, to caliper the bore in the
    # orientation turntable_stator actually prints its axles; one with the
    # 11.0 seat, because a spin test done standing up does not prove a bearing
    # spins on an axle that was printed lying down.
    # the wall to grow them off, then Y-axis cylinders
    # running AWAY from it in -Y, so both the wall and the full length of the
    # stub stay on the plate - the first version hung them off the bottom edge
    # and engraved the label into thin air.
    WALL_X0, WALL_X1 = PB_X - 47.0, PB_X - 21.0
    WALL_Y = PB_ROW['wall']
    STUB_H_LEN = 9.0
    H_STUB_X = [PB_X - 40.0, PB_X - 27.0]
    rect('pb_wall', WALL_X0, WALL_X1, WALL_Y, WALL_Y + 3.0, 0.0, base_t + 16.0,
         JOIN, [plate_b])
    cyl_y('pb_stub_h', H_STUB_X[0], base_t + 10.0, STUB_H_D,
          WALL_Y, -STUB_H_LEN, JOIN, [plate_b])
    # the same axle, lying down, WITH a seat - the representative spin test
    cyl_y('pb_seat_h', H_STUB_X[1], base_t + 10.0, COLLAR_D[1],
          WALL_Y, -0.5, JOIN, [plate_b])
    cyl_y('pb_seatstub_h', H_STUB_X[1], base_t + 10.0, STUB_H_D,
          WALL_Y - 0.5, -STUB_H_LEN, JOIN, [plate_b])
    assert H_STUB_X[1] - H_STUB_X[0] > COLLAR_D[1] / 2 + STUB_H_D / 2 + 2.0, (
        'the two lying-down stubs foul each other')
    assert max(COLLAR_D) < 12.0 + 1e-9, (
        'a seat wider than the 12.0 inner race lands on the ZZ shield')
    assert PB_X + 4.0 + (len(COLLAR_D) - 1) * 16.0 + max(COLLAR_D) / 2 \
        < PB_X + PB_W / 2 - 2.0, 'the spin-test stubs run off plate B'
    assert PB_ROW['seat'] - max(COLLAR_D) / 2 > PB_Y - PB_H / 2 + 2.0, (
        'the spin-test row hangs off the bottom of plate B')
    assert WALL_Y - STUB_H_LEN > PB_Y - PB_H / 2 + 2.0, (
        'the horizontal stub reaches y %.1f and plate B ends at %.1f'
        % (WALL_Y - STUB_H_LEN, PB_Y - PB_H / 2))
    group(t4, PH_B)

    # plate B labels
    pb_base_labels = []
    for i2, d in enumerate(MG995_HORN):
        pb_base_labels.append((PB_X - 30.0 + i2 * 30.0, PB_ROW['horn'] - 14.0,
                               '%.2f' % d))
    for i2, w in enumerate(SLIDE_W):
        pb_base_labels.append((PB_X - 30.0 + i2 * 30.0, PB_ROW['slide'] - 15.0,
                               '%.2f' % w))
    for i2, d in enumerate(STUB_D):
        pb_base_labels.append((PB_X - 30.0 + i2 * 16.0, PB_ROW['stub'] - 9.0,
                               '%.2f' % d))
    pb_base_labels.append((PB_X + 29.0, PB_ROW['stub'] - 11.0, 'INSERT'))
    # beside the horizontal stub, not under it - the stub occupies the space
    # below the wall and a label there would be cut into the stub's shadow
    pb_base_labels.append((WALL_X1 + 15.0, WALL_Y - 4.0, 'FLAT'))
    pb_base_labels.append((WALL_X1 + 15.0, WALL_Y - 11.0, 'S11 FLAT'))
    for i2, cd in enumerate(COLLAR_D):
        pb_base_labels.append((PB_X + 4.0 + i2 * 16.0, PB_ROW['seat'] - 8.5,
                               'S%.0f' % cd))

    def engrave_b(items, z_top):
        for j, (x, y, txt) in enumerate(items):
            sk = sketch('pb_lab_%d' % j)
            t_in = sk.sketchTexts.createInput2(txt, 0.35)
            t_in.setAsMultiLine(
                pt(sk, x - 14.0, y - 3.0), pt(sk, x + 14.0, y + 3.0),
                adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            st = sk.sketchTexts.add(t_in)
            inp = ext.createInput(st, CUT)
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z_top)))
            inp.setDistanceExtent(False, V(mm(-val('label_z') * 10)))
            inp.participantBodies = [plate_b]
            ext.add(inp).name = 'pb_lab_%d' % j
        return len(items)

    n_lab_b = engrave_b(pb_base_labels, base_t)

    assert abs(LEVER_ARM_W - 10.0) < 1e-9, (
        'the sliding slots are sized on a 10.00 lever arm')
    assert min(SLIDE_W) > LEVER_ARM_W, 'the tightest slide slot will not admit the arm'
    assert PB_Y + PB_H / 2 + 6.0 < -BASE_Y / 2 - 4.0, (
        'plate B reaches y %.1f and plate A starts at %.1f'
        % (PB_Y + PB_H / 2 + 6.0, -BASE_Y / 2))

    # IT HAS TO FIT ON THE BED. design_rules.ENVELOPE_SINGLE is 256 x 256.
    lo = [1e9, 1e9]
    hi = [-1e9, -1e9]
    for bi in range(comp.bRepBodies.count):
        bbx = comp.bRepBodies.item(bi).boundingBox
        lo[0] = min(lo[0], bbx.minPoint.x * 10)
        hi[0] = max(hi[0], bbx.maxPoint.x * 10)
        lo[1] = min(lo[1], bbx.minPoint.y * 10)
        hi[1] = max(hi[1], bbx.maxPoint.y * 10)
    bed = (hi[0] - lo[0], hi[1] - lo[1])
    assert bed[0] <= 256.0 and bed[1] <= 256.0, (
        'the four pieces need a %.0f x %.0f bed; the X2D single-nozzle envelope '
        'is 256 x 256' % bed)

    # ---- roller_cap: the retainer that replaces a washer we do not have ------
    CAP_X, CAP_Y = PLUG_X, -40.0
    circle('cap_flange', CAP_X, CAP_Y, CAP_FLANGE_D, 0.0, CAP_FLANGE_T, NEW)
    cap = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    cap.name = 'roller_cap'
    circle('cap_spigot', CAP_X, CAP_Y, CAP_SPIGOT_D, CAP_FLANGE_T, CAP_SPIGOT_H,
           JOIN, [cap])
    circle('cap_bore', CAP_X, CAP_Y, CAP_BORE, -1.0,
           CAP_FLANGE_T + CAP_SPIGOT_H + 2.0, CUT, [cap])
    assert CAP_SPIGOT_D < BEARING_BORE - 0.2, (
        'the cap spigot will not enter the 608 bore')
    assert BEARING_BORE < CAP_FLANGE_D <= RACE_OD, (
        'the cap flange must span the inner race face (%.1f..%.1f); %.1f does not'
        % (BEARING_BORE, RACE_OD, CAP_FLANGE_D))
    assert CAP_Y - CAP_FLANGE_D / 2 > -62.0 or CAP_X - CAP_FLANGE_D / 2 > 48.0, (
        'the cap overlaps plate A')

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 5, (
        'expected 5 bodies (plate A, lever, plug, plate B, roller_cap), got %d'
        % comp.bRepBodies.count)
    for b in comp.bRepBodies:
        for i in range(app.materialLibraries.count):
            m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
            if m:
                b.material = m
                break

    total = sum(b.volume for b in comp.bRepBodies) * 1000
    bb = plate.boundingBox
    print('component: %r | bodies: %s' % (
        comp.name, [comp.bRepBodies.item(i).name for i in range(comp.bRepBodies.count)]))
    print('')
    print('SWEEPS (the value engraved beside each station):')
    print('  hex socket   %s af  -> clearance %s against a %.2f lever'
          % ([round(HEX_LEVER_AF + c, 2) for c in HEX_CLEAR], HEX_CLEAR, HEX_LEVER_AF))
    print('  journal bore %s      -> clearance %s on a %.2f plug'
          % ([round(JOURNAL_PLUG_D + c, 2) for c in JOURNAL_CLEAR],
             JOURNAL_CLEAR, JOURNAL_PLUG_D))
    print('  608 pocket   %s      -> clearance %s on a %.1f race'
          % ([round(BEARING_OD + c, 2) for c in BEARING_CLEAR],
             BEARING_CLEAR, BEARING_OD))
    print('  M3 pilot %s | M2 pilot %s | SG90 horn bore %s'
          % (M3_PILOT, M2_PILOT, HORN_BORE))
    print('  MACHINE TRUTH: boss D20.00, bore B20.00, block 20.00 x 10.00 x 5.00')
    print('  PLATE B: MG995 horn %s | slide %s | stub %s + one FLAT at %.2f | insert %s'
          % (MG995_HORN, SLIDE_W, STUB_D, STUB_H_D, M3_INSERT))
    print('           SPIN TEST: %.2f axles with %s seats - which lets a 608 turn?'
          % (COLLAR_STUB_D, COLLAR_D))
    print('           plus the same test LYING DOWN at %.1f, the orientation the'
          % COLLAR_D[1])
    print('           stator actually prints its axles in')
    print('  roller_cap: %.1f flange x %.1f on a %.1f spigot - the retainer, PRINTED,'
          % (CAP_FLANGE_D, CAP_FLANGE_T, CAP_SPIGOT_D))
    print('              because an M3 washer is 7.0 and the 608 bore is 8.0')
    print('           engraved %d labels' % n_lab_b)
    print('  BED: all four pieces occupy %.0f x %.0f mm (envelope 256 x 256)' % bed)
    print('')
    print('stations: %d hex, %d journal+608, %d pilots, 3 references'
          % (len(HEX_CLEAR), len(STA_X), len(M3_PILOT) + len(M2_PILOT) + len(HORN_BORE)))
    tip_r = LEVER_ARM + 3.0
    print('lever: %.2f af hex standing %.1f proud of a %.1f hub; arm to r %.0f, so '
          '%.2f deg of play reads as %.2f mm of tip travel'
          % (HEX_LEVER_AF, hex_d, HUB_D, tip_r, 1.28, math.radians(1.28) * tip_r))
    print('engraved %d labels (%d on the base, %d on the small pad), %.1f deep'
          % (n_lab, n_base, n_pad, val('label_z') * 10))
    print('  small-feature values run SMALL to LARGE left to right under each cluster')
    print('plate bbox mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    for i in range(comp.bRepBodies.count):
        b = comp.bRepBodies.item(i)
        print('  %-14s %8.0f mm3  %6.1f g solid' % (
            b.name, b.volume * 1000, b.physicalProperties.mass * 1000))
    print('TOTAL %.0f mm3 | %.1f g solid | ~%.0f g at 20%% infill'
          % (total, total * 0.00154, total * 0.00154 * 0.45))
    print('sketches: %d | valid: %s' % (
        comp.sketches.count, all(comp.bRepBodies.item(i).isValid for i in range(comp.bRepBodies.count))))
    print('timeline groups: %r' % (PHASES,))
