"""robotarm/_gauge_slim - the fit gauge, reduced to what a caliper cannot answer.

Supersedes _gauge_fits.py. Same job, one plate instead of two, ~40% less
plastic. Read this header before changing a station: the REASON a station
is swept is the only thing that justifies its cost.

WHY THIS EXISTS
---------------
_gauge_fits swept eight fits three ways each. Jonathan's objection was
correct: most of those sweeps are re-measuring one thing. A printed fit is
the difference between two printed features, and this machine applies
roughly ONE bias to outside features and ONE to inside features. Measure
that bias once and every collapsed station below can be computed instead of
printed - which is what lib/gauge_reduce.py now does.

So the plate splits into three kinds of station:

  SWEPT      the answer is not a dimension, so no amount of calipering the
             single feature gets you there.
  COLLAPSED  one feature at today's value. Caliper it, feed it to
             gauge_reduce, and the other values fall out of the bias.
  TRUTH      the bias itself. Everything above is read through it, so it is
             now the single point of failure for this plate and it is
             DELIBERATELY WIDER than _gauge_fits had it.

SWEPT - kept, and why a caliper will not do
-------------------------------------------
  hex x4     0.10 / 0.20 / 0.30 / 0.40 against one 15.80 lever.
             Backlash is an ANGLE (1-3 deg). You read it as tip travel over
             a 63 mm lever, where 1.28 deg is 1.4 mm of movement. Calipering
             the socket to 0.01 mm does not tell you how far the joint rocks
             under a hand, because that also depends on the flats being flat.
             The 0.20 station IS the arm as it ships - same 15.80 boss, same
             16.00 socket - so it doubles as the control.
             Socket depth is 3.4, which is what the arm actually uses.
             _gauge_fits used 4.0 "to be safe" and so measured a deeper,
             stiffer joint than the one being shipped.
  seats x3   10.0 / 11.0 / 12.0 under a real 608. The question is "does it
             SPIN", which is a hand test against a real bearing. A seat
             wider than the 12.0 inner race reaches over the gap toward the
             ZZ shield and drags. turntable_stator shipped 12.5 until this
             was caught by arithmetic; this row settles it by experiment.
  flats x2   the same 7.90 axle lying DOWN, once bare and once with the 11.0
             seat. Their undersides bridge off a wall with nothing beneath
             and they WILL droop - and the droop is the measurement. This is
             exactly how turntable_stator prints its roller axles. Supports
             OFF or this station tells you nothing.
  pilots x6  M3 2.4/2.5/2.6 and M2 1.6/1.7/1.8. The question is "does the
             screw cut its own thread without splitting the boss", which is
             destructive - the hole is consumed by the test - and is a feel,
             not a number. Six holes in a pad that already exists: near-free.

COLLAPSED - one feature, at today's value, derived from there
------------------------------------------------------------
  journal    one bore at 0.35 clearance on the :20.00 plug
  608 pocket one at 0.05, stacked over the journal on the same pad
  MG995 horn one at 12.15 - the press holding the whole arm up at J2
  SG90 horn  one at 7.15
  slide      one slot at 10.25 on the lever's own 10.00 arm
  stub axle  one at 7.90, vertical, into a real 608 bore
  M3 insert  one at 4.0 for heat-set bosses

TRUTH - widened, because everything now leans on it
---------------------------------------------------
  _gauge_fits took the bias from ONE pair (:20 boss, :20 bore) and one
  block. That was enough when every fit had its own sweep to fall back on.
  It is NOT enough now: the collapsed stations run from :4 to :22, and a
  small hole does not carry the same bias as a large one - the perimeter
  pulls inward and short arcs get approximated, so :4 typically prints
  further under nominal than :20 does. Three bores and two bosses give a
  bias-versus-diameter CURVE rather than a point, and gauge_reduce
  interpolates the collapsed stations along it.

    D20 boss :20.00   B20 bore :20.00
    D8  boss : 8.00   B8  bore : 8.00   B4 bore : 4.00
    BLOCK 20.00 x 10.00 x 5.00 - X, Y and Z bias on flat faces

  If D8 and D20 disagree, the collapsed stations are NOT safe to derive and
  gauge_reduce says so instead of quietly interpolating. That check is the
  price of dropping the sweeps and it is the reason this plate is honest.

DROPPED outright
----------------
  Nothing. Every station in _gauge_fits is either still swept, collapsed to
  one feature, or - in the case of the bare vertical stub row - reduced from
  three to one because the flats row is the harder case and it survived.

Print: PETG (or whatever the ARM will be printed in - a gauge in a different
material is measuring a different machine), plate flat, engraved face UP,
0.2 mm layers, 3 walls, 15-20% infill, SUPPORT OFF. Not "auto". OFF.

Record results in calibration/ as a dated note, then change lib/design_rules
only if the gauge indicates it.
"""

import math

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_gauge_slim'
PREFIX = 'gs_'
PH_PLATE = 'plate'
PH_TRUTH = 'truth'
PH_STATIONS = 'stations'
PH_STUBS = 'stubs'
PH_LABELS = 'labels'
PH_PROBES = 'probes'
PHASES = [PH_PLATE, PH_TRUTH, PH_STATIONS, PH_STUBS, PH_LABELS, PH_PROBES]
MATERIAL_NAME = 'PET Plastic'

# Fusion's 'PET Plastic' is 1.541 g/cm3. PETG FILAMENT is ~1.27. Every mass
# this project has quoted off Fusion is therefore ~21% high. Reported both
# ways at the bottom so the error cannot hide again.
FUSION_PET_DENSITY = 1.541
PETG_FILAMENT_DENSITY = 1.27
SOLID_FRACTION = 0.65        # MEASURED off the v4 slice, not assumed:
                             # 96.7 g / (117941 mm3 * 1.27) = 0.646

# ---- SWEPT ----------------------------------------------------------------
HEX_SOCKET_AF = 16.0          # the wr_ contract socket
HEX_LEVER_AF = 15.80          # the wr_ contract hub - the one probe
HEX_CLEAR = [0.10, 0.20, 0.30, 0.40]        # 0.20 is today's
COLLAR_D = [10.0, 11.0, 12.0]               # bearing seats, spin test
# Four values, and the extra one is on the LARGE side deliberately. Every
# published figure for FDM says a small hole prints UNDER nominal - Bambu PETG
# reports and the PLA curve in knowledge/materials.md both - so drawn 1.6 may
# arrive as 1.3 and split the boss. A sweep of 1.6/1.7/1.8 could plausibly
# come back "all three too tight", which costs a reprint and answers nothing.
M3_PILOT = [2.4, 2.5, 2.6, 2.8]
M2_PILOT = [1.6, 1.7, 1.8, 2.0]

# ---- COLLAPSED (today's value only; gauge_reduce derives the rest) --------
JOURNAL_PLUG_D = 20.00
JOURNAL_CLEAR = 0.35
BEARING_OD = 22.0
BEARING_CLEAR = 0.05
MG995_HORN = 12.15
HORN_BORE = 7.15              # SG90
SLIDE_W = 10.25
STUB_D = 7.90
M3_INSERT = 4.0

# ---- TRUTH ----------------------------------------------------------------
TRUTH_BOSS = [20.00, 8.00]
TRUTH_BORE = [20.00, 8.00, 4.00]
BLOCK_XYZ = (20.00, 10.00, 5.00)

# ---- fixed hardware -------------------------------------------------------
BEARING_W = 7.0
BEARING_BORE = 8.0
RACE_OD = 12.0                # 608ZZ inner race OD - lib/bearings.py
CAP_FLANGE_D = 11.0
CAP_FLANGE_T = 1.6
CAP_SPIGOT_D = 7.60
CAP_SPIGOT_H = 1.2
CAP_BORE = 3.4
LEVER_ARM_W = 10.0            # must match the lever built below


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
        return ups.itemByName(PREFIX + name).value * 10      # -> MILLIMETRES

    param('base_t', '2.4 mm', 'plate thickness away from the stations')
    param('hex_depth', '3.4 mm', 'THE ARM VALUE. _gauge_fits used 4.0 and so '
                                 'measured a deeper joint than it shipped')
    param('journal_depth', '5.0 mm', 'the arm journal is wr_journal = 5.0')
    param('pocket_depth', '3.5 mm', 'half a 608 - enough to judge, easy to push out')
    param('floor_t', '1.5 mm', 'between the 608 pocket and the journal bore')
    param('label_z', '0.6 mm', 'engraving depth - design_rules MIN_EMBOSS_MM')

    # ---- idempotent rebuild. RENAME FIRST, THEN DELETE. fusion/PLAYBOOK.md ---
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
        'component came back as %r - a stale component still holds the name'
        % comp.name)
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
            # Without participantBodies a CUT eats every other body. PLAYBOOK.md.
            inp.participantBodies = targets if targets is not None else [
                comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
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
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(sk, x0, y0), pt(sk, x1, y1))
        return extrude_profs(one(sk), op, z0, dz, name, targets)

    def hexagon(name, x, y, af, z0, dz, op, targets=None):
        sk = sketch(name)
        r_c = (af / 20.0) / math.cos(math.pi / 6)
        pts = [(r_c * math.cos(2 * math.pi * i / 6 + math.pi / 6),
                r_c * math.sin(2 * math.pi * i / 6 + math.pi / 6))
               for i in range(6)]
        lines = sk.sketchCurves.sketchLines
        for i in range(6):
            a, b = pts[i], pts[(i + 1) % 6]
            lines.addByTwoPoints(
                sk.modelToSketchSpace(P3(x / 10.0 + a[0], y / 10.0 + a[1], 0)),
                sk.modelToSketchSpace(P3(x / 10.0 + b[0], y / 10.0 + b[1], 0)))
        return extrude_profs(one(sk), op, z0, dz, name, targets)

    def cyl_y(name, x, z, d, y0, dy, op, targets=None):
        """Cylinder on a HORIZONTAL axis along Y. The stator's roller axles are
        built exactly like this, and a sideways cylinder is not the same size
        as the same cylinder printed up Z - which is the whole point."""
        sk = comp.sketches.add(comp.xZConstructionPlane)
        sk.name = 'sk_' + name
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(P3(x / 10.0, 0.0, z / 10.0)), d / 20.0)
        return extrude_profs(one(sk), op, y0, dy, name, targets)

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    # ---- layout, ALL IN MILLIMETRES, plate centred on the origin ------------
    # EXACTLY 96.000 x 150.000, and nothing on the plate reaches outside it.
    # That makes the plate's own outline a free pair of LONG outside
    # references. It matters because the published outside error is
    # shrinkage-dominated and therefore PROPORTIONAL to length (20 mm -> 0.1,
    # 100 mm -> 0.4), while the truth-row bosses only span 8..20 mm and cannot
    # tell a constant offset from a scale error. Calipering these two edges
    # extends the range to 19x for free. See specs/robotarm/_gauge_sheet.md.
    BASE_X, BASE_Y = 96.0, 150.0
    base_t = val('base_t')
    hex_d = val('hex_depth')
    journal_d = val('journal_depth')
    pocket_d = val('pocket_depth')
    floor_t = val('floor_t')

    ROW_TRUTH = 60.0
    LAB_TRUTH = 44.0
    ROW_STA = 28.0
    LAB_STA = 11.0
    ROW_HEX = -3.0
    LAB_HEX = -19.0
    ROW_SMALL = -36.0
    LAB_SMALL = -29.5
    ROW_STUB = -56.0
    LAB_STUB_A = -66.0      # the stub row needs TWO label bands: at 3.5 mm
    LAB_STUB_B = -72.0      # text 'S11FLAT' is 23 mm wide and ran into 'FLAT'

    HEX_X = [-36.0, -12.0, 12.0, 36.0]
    HEX_BAR_H = 22.0                     # one BAR, not four pads: same plastic,
    HEX_BAR_X = 47.0                     # far stiffer under a lever being pried
    hex_pad_h = hex_d + 1.5

    TR_BOSS_X = [-34.0, 14.0]            # D20 on the base, D8 on the small pad
    TR_BORE_X = [-8.0, 27.0, 38.0]       # B20 on its own pad, B8+B4 on the pad
    TR_PAD = (8.0, 44.0, 50.0, 70.0)     # x0, x1, y0, y1
    TR_SMALL_Y = 62.0
    TR_BORE_PAD_D = 26.0
    TR_RISE = 6.0

    STA_X = -33.0
    sta_pad_h = pocket_d + floor_t + journal_d
    sta_pad_d = BEARING_OD + BEARING_CLEAR + 2 * 2.0
    HORN_X = -5.0
    horn_pad_d = MG995_HORN + 12.0
    horn_pad_h = 7.0
    SLIDE_PAD = (13.0, 41.0, 16.0, 40.0)
    SLIDE_X = 27.0
    slide_pad_h = 6.0

    SMALL_PAD = (-46.0, 32.0, -44.0, -26.0)
    small_pad_h = 4.5
    M3_X = [-42.0, -35.0, -28.0, -21.0]
    M2_X = [-13.0, -7.0, -1.0, 5.0]
    SG90_X = 13.0
    INSERT_X = 25.0
    BLOCK_X0, BLOCK_X1 = 34.0, 44.0      # 10 wide x 20 tall - long axis in Y so
    BLOCK_Y0, BLOCK_Y1 = -45.0, -25.0    # it fits beside the small pad

    VSTUB_X = -40.0
    WALL_X0, WALL_X1 = -32.0, -6.0
    WALL_Y0, WALL_Y1 = -52.0, -49.0
    WALL_H = 16.0
    HSTUB_X = [-26.0, -13.0]             # bare, then seated
    HSTUB_Z = 10.0
    HSTUB_LEN = 9.0
    SEAT_X = [8.0, 24.0, 40.0]
    SEAT_T = 0.5
    SEAT_STUB_H = 9.0

    # ---- geometry sanity, BEFORE anything is built --------------------------
    # Units: every literal below is MILLIMETRES and every variable it is
    # compared against has already been scaled to mm by val(). Two assertions
    # in _gauge_fits compared centimetres against mm literals and fired on
    # perfectly good geometry - hence this note.
    GAP = 2.0
    hex_ac = (HEX_LEVER_AF + max(HEX_CLEAR)) / math.cos(math.pi / 6)
    assert min(HEX_CLEAR) > 0, 'a zero-clearance hex cannot be assembled to be measured'
    assert HEX_LEVER_AF < HEX_SOCKET_AF, 'the lever must sit under the nominal socket'
    assert abs((HEX_LEVER_AF + HEX_CLEAR[1]) - HEX_SOCKET_AF) < 1e-9, (
        'the middle hex station must BE the arm as it ships: lever %.2f + %.2f '
        'should equal the wr_ socket %.2f'
        % (HEX_LEVER_AF, HEX_CLEAR[1], HEX_SOCKET_AF))
    assert (HEX_X[1] - HEX_X[0]) > hex_ac + 3.0, (
        'hex sockets at %.1f pitch overlap - they are %.2f across corners'
        % (HEX_X[1] - HEX_X[0], hex_ac))
    assert HEX_BAR_H - hex_ac >= 2 * 1.6, (
        'a %.1f bar leaves %.2f of wall round a %.2f socket'
        % (HEX_BAR_H, (HEX_BAR_H - hex_ac) / 2, hex_ac))
    assert hex_pad_h - hex_d >= 1.2, 'less than a wall under the hex sockets'
    assert abs(hex_d - 3.4) < 1e-9, (
        'hex depth %.2f is not the 3.4 the arm ships - this station is meant to '
        'measure the joint that exists, not a deeper one' % hex_d)
    assert floor_t >= 1.2, 'less than a wall between the 608 pocket and the journal'
    assert max(COLLAR_D) <= RACE_OD, (
        'a seat wider than the %.1f inner race lands on the ZZ shield' % RACE_OD)
    assert SLIDE_W > LEVER_ARM_W, (
        'the slide slot %.2f will not admit the %.2f lever arm' % (SLIDE_W, LEVER_ARM_W))
    assert TRUTH_BOSS[0] == JOURNAL_PLUG_D, (
        'the D20 boss and the journal plug should be the same nominal so one '
        'bias reading serves both')
    assert min(TRUTH_BORE) <= min([M3_INSERT, HORN_BORE, STUB_D, MG995_HORN]), (
        'the truth bores must BRACKET the collapsed stations - the smallest '
        'collapsed feature is %.2f and the smallest truth bore is %.2f'
        % (min([M3_INSERT, HORN_BORE, STUB_D, MG995_HORN]), min(TRUTH_BORE)))
    assert max(TRUTH_BORE) >= BEARING_OD - 2.0, (
        'the truth bores do not reach the large end of the collapsed range')

    # row-by-row adjacency, top of the plate downwards
    lab_h = 3.5                                   # engraved text height
    truth_bot = min(ROW_TRUTH - TR_BORE_PAD_D / 2, TR_PAD[2])
    assert ROW_TRUTH + TR_BORE_PAD_D / 2 < BASE_Y / 2 - 1.0, 'the B20 pad runs off the top'
    assert truth_bot - (LAB_TRUTH + lab_h / 2) >= 1.0, (
        'the truth labels at y %.1f touch the truth row at y %.1f'
        % (LAB_TRUTH + lab_h / 2, truth_bot))
    sta_top = max(ROW_STA + sta_pad_d / 2, ROW_STA + horn_pad_d / 2, SLIDE_PAD[3])
    assert (LAB_TRUTH - lab_h / 2) - sta_top >= 1.0, (
        'the truth labels sit on the station row (%.2f vs %.2f)'
        % (LAB_TRUTH - lab_h / 2, sta_top))
    sta_bot = min(ROW_STA - sta_pad_d / 2, ROW_STA - horn_pad_d / 2, SLIDE_PAD[2])
    assert sta_bot - (LAB_STA + lab_h / 2) >= 1.0, 'the station labels touch the station row'
    assert (LAB_STA - lab_h / 2) - (ROW_HEX + HEX_BAR_H / 2) >= 1.0, (
        'the station labels sit on the hex bar')
    assert (ROW_HEX - HEX_BAR_H / 2) - (LAB_HEX + lab_h / 2) >= 1.0, 'hex labels touch the bar'
    assert (LAB_HEX - lab_h / 2) - max(SMALL_PAD[3], BLOCK_Y1) >= 1.0, (
        'the hex labels sit on the small pad or the block')
    assert min(SMALL_PAD[2], BLOCK_Y0) - (ROW_STUB + max(COLLAR_D) / 2) >= 1.0, (
        'the small row overlaps the seat row')
    assert (ROW_STUB - max(COLLAR_D) / 2) - (LAB_STUB_A + lab_h / 2) >= 1.0, (
        'the stub labels sit under the seats')
    assert (WALL_Y0 - HSTUB_LEN - 0.5) - (LAB_STUB_A + lab_h / 2) >= 1.0, (
        'the lying-down stubs reach y %.1f and their labels start at %.1f'
        % (WALL_Y0 - HSTUB_LEN - 0.5, LAB_STUB_A + lab_h / 2))
    assert LAB_STUB_A - lab_h / 2 > LAB_STUB_B + lab_h / 2, 'the two stub bands overlap'
    assert LAB_STUB_B - lab_h / 2 > -BASE_Y / 2 + 1.0, 'the stub labels run off the bottom'

    # in-row X adjacency
    assert STA_X + sta_pad_d / 2 + GAP < HORN_X - horn_pad_d / 2, 'station and horn pads touch'
    assert HORN_X + horn_pad_d / 2 + GAP < SLIDE_PAD[0], 'horn and slide pads touch'
    assert SLIDE_PAD[1] < BASE_X / 2 - 1.0, 'the slide pad runs off the plate'
    assert STA_X - sta_pad_d / 2 > -BASE_X / 2 + 1.0, 'the station pad runs off the plate'
    assert TR_BOSS_X[0] + TRUTH_BOSS[0] / 2 + GAP < TR_BORE_X[0] - TR_BORE_PAD_D / 2, \
        'the D20 boss and B20 pad touch'
    assert TR_BORE_X[0] + TR_BORE_PAD_D / 2 + GAP < TR_PAD[0], 'the B20 pad and truth pad touch'
    assert TR_PAD[1] < BASE_X / 2 - 1.0, 'the truth pad runs off the plate'
    assert len(M3_X) == len(M3_PILOT) and len(M2_X) == len(M2_PILOT), \
        'a pilot value has no x position'
    for _xs, _ds, _tag in ((M3_X, M3_PILOT, 'M3'), (M2_X, M2_PILOT, 'M2')):
        for _i in range(len(_xs) - 1):
            assert _xs[_i] + _ds[_i] / 2 + 1.6 < _xs[_i + 1] - _ds[_i + 1] / 2, \
                'less than a wall between %s pilots %d and %d' % (_tag, _i, _i + 1)
        assert _xs[0] - _ds[0] / 2 > SMALL_PAD[0] + 1.6, '%s row runs off the pad' % _tag
        assert _xs[-1] + _ds[-1] / 2 < SMALL_PAD[1] - 1.6, '%s row runs off the pad' % _tag
    assert M3_X[-1] + M3_PILOT[-1] / 2 + GAP < M2_X[0] - M2_PILOT[0] / 2, \
        'the M3 and M2 rows touch'
    assert M2_X[-1] + M2_PILOT[-1] / 2 + GAP < SG90_X - HORN_BORE / 2, \
        'the M2 row touches the SG90 bore'
    assert SG90_X + HORN_BORE / 2 + GAP < INSERT_X - M3_INSERT / 2, \
        'the SG90 bore touches the insert hole'
    assert INSERT_X + M3_INSERT / 2 < SMALL_PAD[1] - 1.6, 'the insert runs off the pad'
    assert SMALL_PAD[1] + GAP <= BLOCK_X0, 'the small pad and the block touch'
    assert BLOCK_X1 < BASE_X / 2 - 1.0, 'the block runs off the plate'
    assert VSTUB_X + STUB_D / 2 + GAP < WALL_X0, 'the vertical stub touches the wall'
    assert WALL_X1 + GAP < SEAT_X[0] - COLLAR_D[0] / 2, 'the wall touches the seat row'
    for i in range(len(SEAT_X) - 1):
        assert SEAT_X[i] + COLLAR_D[i] / 2 + GAP < SEAT_X[i + 1] - COLLAR_D[i + 1] / 2, \
            'seats %d and %d touch' % (i, i + 1)
    assert SEAT_X[-1] + COLLAR_D[-1] / 2 < BASE_X / 2 - 1.0, 'the last seat runs off the plate'
    assert HSTUB_X[1] - HSTUB_X[0] > COLLAR_D[1] / 2 + STUB_D / 2 + GAP, \
        'the two lying-down stubs foul each other'
    assert WALL_X0 < min(HSTUB_X) - STUB_D / 2 and max(HSTUB_X) + COLLAR_D[1] / 2 < WALL_X1, \
        'a lying-down stub grows off the end of its wall'

    # ---- phase 1: the plate --------------------------------------------------
    t0 = design.timeline.count
    rect('base', -BASE_X / 2, BASE_X / 2, -BASE_Y / 2, BASE_Y / 2, 0.0, base_t, NEW)
    plate = comp.bRepBodies.item(0)
    plate.name = 'gauge_slim_plate'
    group(t0, PH_PLATE)

    # ---- phase 2: machine truth ----------------------------------------------
    # The single point of failure for this plate. Two bosses and three bores
    # spanning :4 to :20 so gauge_reduce gets a bias CURVE, not a point.
    t1 = design.timeline.count
    circle('truth_boss_20', TR_BOSS_X[0], ROW_TRUTH, TRUTH_BOSS[0],
           0.0, base_t + TR_RISE, JOIN, [plate])
    circle('truth_bore_20_pad', TR_BORE_X[0], ROW_TRUTH, TR_BORE_PAD_D,
           0.0, base_t + TR_RISE, JOIN, [plate])
    circle('truth_bore_20', TR_BORE_X[0], ROW_TRUTH, TRUTH_BORE[0],
           base_t + TR_RISE, -TR_RISE, CUT, [plate])
    rect('truth_pad', TR_PAD[0], TR_PAD[1], TR_PAD[2], TR_PAD[3],
         0.0, base_t + TR_RISE, JOIN, [plate])
    tr_top = base_t + TR_RISE
    circle('truth_boss_8', TR_BOSS_X[1], TR_SMALL_Y, TRUTH_BOSS[1],
           tr_top, TR_RISE, JOIN, [plate])
    circle('truth_bore_8', TR_BORE_X[1], TR_SMALL_Y, TRUTH_BORE[1],
           tr_top, -TR_RISE, CUT, [plate])
    circle('truth_bore_4', TR_BORE_X[2], TR_SMALL_Y, TRUTH_BORE[2],
           tr_top, -TR_RISE, CUT, [plate])
    rect('truth_block', BLOCK_X0, BLOCK_X1, BLOCK_Y0, BLOCK_Y1,
         base_t, BLOCK_XYZ[2], JOIN, [plate])
    assert abs((BLOCK_X1 - BLOCK_X0) - BLOCK_XYZ[1]) < 1e-9, (
        'the block is %.2f wide in X and BLOCK_XYZ says %.2f'
        % (BLOCK_X1 - BLOCK_X0, BLOCK_XYZ[1]))
    assert abs((BLOCK_Y1 - BLOCK_Y0) - BLOCK_XYZ[0]) < 1e-9, (
        'the block is %.2f long in Y and BLOCK_XYZ says %.2f'
        % (BLOCK_Y1 - BLOCK_Y0, BLOCK_XYZ[0]))
    group(t1, PH_TRUTH)

    # ---- phase 3: the stations -----------------------------------------------
    t2 = design.timeline.count
    # journal + 608, stacked on one pad: :22.05 pocket down from the top, the
    # :20.35 journal bore below it, a :10 push-out through the floor so the
    # bearing comes back out with a rod.
    circle('sta_pad', STA_X, ROW_STA, sta_pad_d, 0.0, base_t + sta_pad_h, JOIN, [plate])
    sta_top = base_t + sta_pad_h
    circle('sta_pocket', STA_X, ROW_STA, BEARING_OD + BEARING_CLEAR,
           sta_top, -pocket_d, CUT, [plate])
    circle('sta_journal', STA_X, ROW_STA, JOURNAL_PLUG_D + JOURNAL_CLEAR,
           sta_top - pocket_d - floor_t, -journal_d, CUT, [plate])
    circle('sta_pushout', STA_X, ROW_STA, 10.0, -1.0, base_t + sta_pad_h + 2.0,
           CUT, [plate])

    # MG995 horn press - the one holding the whole arm up at J2
    circle('horn_pad', HORN_X, ROW_STA, horn_pad_d, 0.0, base_t + horn_pad_h,
           JOIN, [plate])
    circle('horn_bore', HORN_X, ROW_STA, MG995_HORN,
           base_t + horn_pad_h, -horn_pad_h + 1.0, CUT, [plate])

    # sliding fit - the lever's own 10.00 arm is the probe
    rect('slide_pad', SLIDE_PAD[0], SLIDE_PAD[1], SLIDE_PAD[2], SLIDE_PAD[3],
         0.0, base_t + slide_pad_h, JOIN, [plate])
    rect('slide_slot', SLIDE_X - SLIDE_W / 2, SLIDE_X + SLIDE_W / 2,
         SLIDE_PAD[2] - 2.0, SLIDE_PAD[3] + 2.0,
         base_t + slide_pad_h, -slide_pad_h + 1.0, CUT, [plate])

    # HEX - one bar, four sockets, one lever. Sized off the LEVER, not off the
    # nominal socket: sizing it off the socket gave 0.30..0.60 of real
    # clearance while the engraving still said 0.10..0.40.
    rect('hex_bar', -HEX_BAR_X, HEX_BAR_X, ROW_HEX - HEX_BAR_H / 2,
         ROW_HEX + HEX_BAR_H / 2, 0.0, base_t + hex_pad_h, JOIN, [plate])
    for i, x in enumerate(HEX_X):
        hexagon('hex_socket_%d' % i, x, ROW_HEX, HEX_LEVER_AF + HEX_CLEAR[i],
                base_t + hex_pad_h, -hex_d, CUT, [plate])

    # SMALL FEATURES - the two pilot sweeps, plus three collapsed bores
    rect('small_pad', SMALL_PAD[0], SMALL_PAD[1], SMALL_PAD[2], SMALL_PAD[3],
         0.0, base_t + small_pad_h, JOIN, [plate])
    small_top = base_t + small_pad_h
    for i, d in enumerate(M3_PILOT):
        circle('m3_%d' % i, M3_X[i], ROW_SMALL, d, small_top, -small_top - 1.0,
               CUT, [plate])
    for i, d in enumerate(M2_PILOT):
        circle('m2_%d' % i, M2_X[i], ROW_SMALL, d, small_top, -small_top - 1.0,
               CUT, [plate])
    circle('sg90_horn', SG90_X, ROW_SMALL, HORN_BORE, small_top, -4.0, CUT, [plate])
    circle('m3_insert', INSERT_X, ROW_SMALL, M3_INSERT, small_top, -6.0, CUT, [plate])
    group(t2, PH_STATIONS)

    # ---- phase 4: stubs, seats and the two lying-down axles ------------------
    t3 = design.timeline.count
    # one vertical stub at today's 7.90, into a real 608 bore
    circle('vstub', VSTUB_X, ROW_STUB, STUB_D, base_t, SEAT_STUB_H, JOIN, [plate])

    # THE SPIN TEST. One 7.90 axle, three seat diameters. Put a real 608 on each
    # and turn it: the one that spins is the seat, the ones that drag are landing
    # on the shield. Nothing but a real bearing answers this.
    for i, cd in enumerate(COLLAR_D):
        circle('seat_%d' % i, SEAT_X[i], ROW_STUB, cd, base_t, SEAT_T, JOIN, [plate])
        circle('seatstub_%d' % i, SEAT_X[i], ROW_STUB, STUB_D,
               base_t + SEAT_T, SEAT_STUB_H, JOIN, [plate])
        assert SEAT_STUB_H > BEARING_W + 1.0, (
            'a %.1f stub will not stand a %.1f bearing proud enough to spin'
            % (SEAT_STUB_H, BEARING_W))

    # the same axle LYING DOWN, twice. One bare, to caliper the droop in the
    # orientation turntable_stator actually prints its axles; one with the 11.0
    # seat, because a spin test done standing up does not prove a bearing spins
    # on an axle that was printed sideways.
    rect('wall', WALL_X0, WALL_X1, WALL_Y0, WALL_Y1, 0.0, base_t + WALL_H, JOIN, [plate])
    cyl_y('hstub_bare', HSTUB_X[0], base_t + HSTUB_Z, STUB_D,
          WALL_Y0, -HSTUB_LEN, JOIN, [plate])
    cyl_y('hseat', HSTUB_X[1], base_t + HSTUB_Z, COLLAR_D[1],
          WALL_Y0, -SEAT_T, JOIN, [plate])
    cyl_y('hseatstub', HSTUB_X[1], base_t + HSTUB_Z, STUB_D,
          WALL_Y0 - SEAT_T, -HSTUB_LEN, JOIN, [plate])
    assert base_t + HSTUB_Z - COLLAR_D[1] / 2 > 1.0, (
        'the lying-down seat at z %.1f cuts into the plate' % (base_t + HSTUB_Z))
    assert WALL_H + base_t > HSTUB_Z + COLLAR_D[1] / 2, (
        'the wall is %.1f tall and the seated stub reaches z %.1f - the stub '
        'grows off the top of its own wall'
        % (WALL_H + base_t, base_t + HSTUB_Z + COLLAR_D[1] / 2))
    group(t3, PH_STUBS)

    # ---- phase 5: labels ------------------------------------------------------
    # ENGRAVE THE SKETCHTEXT, NOT ITS PROFILES. A SketchText does not populate
    # sketch.profiles on this Fusion build - the first version of _gauge_fits
    # collected zero and cut nothing, silently, leaving an unlabelled gauge,
    # which is worse than no gauge because you cannot tell the stations apart.
    t4 = design.timeline.count

    CHAR_W = 0.95 * lab_h          # measured off the v1 render, rounded up

    def check_labels(items):
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                xa, ya, ta = items[a]
                xb, yb, tb = items[b]
                if abs(ya - yb) >= lab_h:
                    continue
                wa = len(ta) * CHAR_W / 2.0
                wb = len(tb) * CHAR_W / 2.0
                assert xa + wa + 0.5 < xb - wb or xb + wb + 0.5 < xa - wa, (
                    'labels %r at x %.1f and %r at x %.1f collide - %.1f mm '
                    'apart and they need %.1f'
                    % (ta, xa, tb, xb, abs(xa - xb), wa + wb + 0.5))
        return items

    def engrave(name, items, z_top):
        check_labels(items)
        for j, (x, y, txt) in enumerate(items):
            sk = sketch('%s_%d' % (name, j))
            t_in = sk.sketchTexts.createInput2(txt, 0.35)
            t_in.setAsMultiLine(
                pt(sk, x - 15.0, y - 3.0), pt(sk, x + 15.0, y + 3.0),
                adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            st = sk.sketchTexts.add(t_in)
            inp = ext.createInput(st, CUT)
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(mm(z_top)))
            inp.setDistanceExtent(False, V(mm(-val('label_z'))))
            inp.participantBodies = [plate]
            ext.add(inp).name = '%s_%d' % (name, j)
        return len(items)

    base_labels = [
        (TR_BOSS_X[0], LAB_TRUTH, 'D20'),
        (TR_BORE_X[0], LAB_TRUTH, 'B20'),
        (STA_X, LAB_STA, 'J35 P05'),
        (HORN_X, LAB_STA, 'MG12.15'),
        (SLIDE_X, LAB_STA, 'SL10.25'),
        (VSTUB_X, LAB_STUB_A, 'STUB'),
        (HSTUB_X[1], LAB_STUB_A, 'S11FLAT'),
        (HSTUB_X[0], LAB_STUB_B, 'FLAT'),
        (BLOCK_X0 + 5.0, (BLOCK_Y0 + ROW_STUB + max(COLLAR_D) / 2) / 2, 'BLOCK'),
    ]
    for i, cd in enumerate(COLLAR_D):
        # alternate bands so a 3-character label never has to squeeze
        base_labels.append((SEAT_X[i], LAB_STUB_A if i % 2 else LAB_STUB_B,
                            'S%.0f' % cd))
    for i, c in enumerate(HEX_CLEAR):
        base_labels.append((HEX_X[i], LAB_HEX, '%02d' % int(round(c * 100))))
    n_base = engrave('lab_base', base_labels, base_t)

    truth_pad_labels = [(TR_BOSS_X[1], 53.5, 'D8'),
                        (TR_BORE_X[1], 53.5, 'B8'),
                        (TR_BORE_X[2], 53.5, 'B4')]
    n_tr = engrave('lab_truth', truth_pad_labels, base_t + TR_RISE)

    small_labels = [(-31.5, LAB_SMALL, 'M3'), (-4.0, LAB_SMALL, 'M2'),
                    (12.0, LAB_SMALL, 'SG90'), (INSERT_X, LAB_SMALL, 'INS')]
    n_sm = engrave('lab_small', small_labels, base_t + small_pad_h)
    n_lab = n_base + n_tr + n_sm
    group(t4, PH_LABELS)

    # ---- phase 6: the probes --------------------------------------------------
    t5 = design.timeline.count
    LEVER_X, LEVER_Y = BASE_X / 2 + 22.0, -26.0
    LEVER_ARM = 60.0
    HUB_D, ARM_T = 24.0, 4.0
    LEVER_TIP_W = 24.0
    # THE HEX MUST STAND PROUD OF THE HUB. Put both from z 0 to hex_d and the
    # :24 hub simply swallows an 18.2-across-corners hex, leaving a disc with
    # nothing to insert. Hex on the bottom, everything else stacked above it.
    hexagon('lever_hex', LEVER_X, LEVER_Y, HEX_LEVER_AF, 0.0, hex_d, NEW)
    lever = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    lever.name = 'gauge_slim_lever'
    circle('lever_hub', LEVER_X, LEVER_Y, HUB_D, hex_d, ARM_T, JOIN, [lever])
    rect('lever_arm', LEVER_X - LEVER_ARM_W / 2, LEVER_X + LEVER_ARM_W / 2,
         LEVER_Y, LEVER_Y + LEVER_ARM, hex_d, ARM_T, JOIN, [lever])
    rect('lever_tip', LEVER_X - LEVER_TIP_W / 2, LEVER_X + LEVER_TIP_W / 2,
         LEVER_Y + LEVER_ARM, LEVER_Y + LEVER_ARM + 6.0, hex_d, ARM_T, JOIN, [lever])

    PLUG_X, PLUG_Y = LEVER_X + 37.0, 0.0
    PLUG_GRIP_D = 32.0
    circle('plug_collar', PLUG_X, PLUG_Y, JOURNAL_PLUG_D, 0.0, journal_d, NEW)
    plug = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    plug.name = 'gauge_slim_plug'
    circle('plug_grip', PLUG_X, PLUG_Y, PLUG_GRIP_D, journal_d, 4.0, JOIN, [plug])

    # roller_cap: an M3 washer is :7.0 and the 608 bore is :8.0, so a washer
    # falls straight through. This is the retainer, printed, at 0.4 g.
    CAP_X, CAP_Y = PLUG_X, -40.0
    circle('cap_flange', CAP_X, CAP_Y, CAP_FLANGE_D, 0.0, CAP_FLANGE_T, NEW)
    cap = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    cap.name = 'roller_cap'
    circle('cap_spigot', CAP_X, CAP_Y, CAP_SPIGOT_D, CAP_FLANGE_T, CAP_SPIGOT_H,
           JOIN, [cap])
    circle('cap_bore', CAP_X, CAP_Y, CAP_BORE, -1.0,
           CAP_FLANGE_T + CAP_SPIGOT_H + 2.0, CUT, [cap])
    group(t5, PH_PROBES)

    # nothing may interpenetrate - these are four separate printed pieces
    lever_reach = LEVER_X + LEVER_TIP_W / 2
    assert LEVER_X - HUB_D / 2 > BASE_X / 2 + GAP, 'the lever hub overlaps the plate'
    assert HUB_D / 2 > (HEX_LEVER_AF / 2) / math.cos(math.pi / 6), (
        'the hub is smaller than the hex it is supposed to sit on')
    assert PLUG_X - PLUG_GRIP_D / 2 > lever_reach + GAP, (
        'the plug at x %.1f overlaps the lever tip reaching x %.1f'
        % (PLUG_X - PLUG_GRIP_D / 2, lever_reach))
    assert CAP_Y + CAP_FLANGE_D / 2 + GAP < PLUG_Y - PLUG_GRIP_D / 2, (
        'the cap overlaps the plug grip')
    assert CAP_X - CAP_FLANGE_D / 2 > BASE_X / 2 + GAP, 'the cap overlaps the plate'
    assert CAP_SPIGOT_D < BEARING_BORE - 0.2, 'the cap spigot will not enter the 608 bore'
    assert BEARING_BORE < CAP_FLANGE_D <= RACE_OD, (
        'the cap flange must span the inner race face (%.1f..%.1f); %.1f does not'
        % (BEARING_BORE, RACE_OD, CAP_FLANGE_D))
    lever_tip_r = LEVER_ARM + 6.0 - 3.0
    assert abs(lever_tip_r - 63.0) < 1e-9, (
        'lib/gauge_reduce.LEVER_TIP_R is 63.0 and this lever reads at %.1f - the '
        'reducer would convert every tip travel to the wrong angle' % lever_tip_r)

    # ---- identity + diagnostics ----------------------------------------------
    assert comp.bRepBodies.count == 4, (
        'expected 4 bodies (plate, lever, plug, roller_cap), got %d'
        % comp.bRepBodies.count)
    for b in comp.bRepBodies:
        for i in range(app.materialLibraries.count):
            m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
            if m:
                b.material = m
                break

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
        'the four pieces need a %.0f x %.0f bed; ENVELOPE_SINGLE is 256 x 256' % bed)

    total = sum(b.volume for b in comp.bRepBodies) * 1000
    print('component: %r | bodies: %s' % (
        comp.name,
        [comp.bRepBodies.item(i).name for i in range(comp.bRepBodies.count)]))
    print('')
    print('SWEPT - a caliper cannot answer these')
    print('  hex      %s af  -> clearance %s on a %.2f lever, %.1f deep (the ARM value)'
          % ([round(HEX_LEVER_AF + c, 2) for c in HEX_CLEAR], HEX_CLEAR,
             HEX_LEVER_AF, hex_d))
    print('  seats    %s under a real 608 on a %.2f axle - which one SPINS?'
          % (COLLAR_D, STUB_D))
    print('  flats    %.2f axle lying down, bare and with the %.1f seat - the '
          'DROOP is the measurement' % (STUB_D, COLLAR_D[1]))
    print('  pilots   M3 %s | M2 %s - self-tap is destructive and is a feel'
          % (M3_PILOT, M2_PILOT))
    print('')
    print('COLLAPSED - one feature; gauge_reduce derives the rest from the bias')
    print('  journal %.2f | 608 pocket %.2f | MG995 horn %.2f | SG90 horn %.2f'
          % (JOURNAL_CLEAR, BEARING_CLEAR, MG995_HORN, HORN_BORE))
    print('  slide %.2f | vertical stub %.2f | M3 insert %.2f'
          % (SLIDE_W, STUB_D, M3_INSERT))
    print('')
    print('TRUTH - the bias CURVE everything above is read through')
    print('  bosses %s | bores %s | block %.2f x %.2f x %.2f'
          % (TRUTH_BOSS, TRUTH_BORE, BLOCK_XYZ[0], BLOCK_XYZ[1], BLOCK_XYZ[2]))
    print('  bores span %.1f..%.1f and the collapsed stations span %.1f..%.1f - '
          'BRACKETED' % (min(TRUTH_BORE), max(TRUTH_BORE),
                         min([M3_INSERT, HORN_BORE, STUB_D, MG995_HORN]),
                         BEARING_OD + BEARING_CLEAR))
    print('')
    print('lever: %.2f af hex standing %.1f proud of a %.1f hub; tip at r %.0f, '
          'so %.2f deg reads as %.2f mm of travel'
          % (HEX_LEVER_AF, hex_d, HUB_D, lever_tip_r, 1.28,
             math.radians(1.28) * lever_tip_r))
    print('engraved %d labels (%d base, %d truth pad, %d small pad), %.1f deep'
          % (n_lab, n_base, n_tr, n_sm, val('label_z')))
    print('BED: %.0f x %.0f mm (envelope 256 x 256)' % bed)
    print('')
    for i in range(comp.bRepBodies.count):
        b = comp.bRepBodies.item(i)
        print('  %-20s %8.0f mm3' % (b.name, b.volume * 1000))
    print('TOTAL %.0f mm3' % total)
    print('')
    print('MASS - both ways, because the project has been quoting the wrong one.')
    print('  Fusion %r density %.3f g/cm3  -> %.1f g solid  <- OVERSTATED'
          % (MATERIAL_NAME, FUSION_PET_DENSITY, total * FUSION_PET_DENSITY / 1000))
    print('  PETG filament        %.3f g/cm3  -> %.1f g solid  <- the real one'
          % (PETG_FILAMENT_DENSITY, total * PETG_FILAMENT_DENSITY / 1000))
    print('  at %.0f%% solid (measured off the v4 slice, not assumed) -> %.1f g'
          % (SOLID_FRACTION * 100,
             total * PETG_FILAMENT_DENSITY * SOLID_FRACTION / 1000))
    print('  _gauge_fits was 117941 mm3 / 96.7 g / 3h10m sliced.')
    print('  this is %.0f%% of that: %.1f g, so roughly %.0f min on the same profile'
          % (100.0 * total / 117941.0,
             total * PETG_FILAMENT_DENSITY * SOLID_FRACTION / 1000,
             190.0 * total / 117941.0))
    print('sketches: %d | valid: %s' % (
        comp.sketches.count,
        all(comp.bRepBodies.item(i).isValid for i in range(comp.bRepBodies.count))))
    print('timeline groups: %r' % (PHASES,))
