"""robotarm/shoulder_bracket - Fusion MCP generating script.

Rebuilds `robotarm_shoulder_bracket` (idempotent). Spec: specs/robotarm/_state.md.

J1's rotating half AND J2's fork, in one part. Its underside is the Ø96
turntable disc that rides the three 608ZZ rollers in the ALREADY PRINTED
legacy base; standing on that disc is the fork that straddles the upper arm
and carries the MG995.

Local frame: origin ON THE J2 PITCH AXIS. +X along that axis (drive side),
+Y forward along the arm's reach at zero pitch, +Z up. The disc's top face is
at z = -sb_stand_h and its underside - the race face - at one disc thickness
below that.

THIS PART IS ALSO J1'S ROTOR. Jonathan has printed the legacy base PLATTER -
the control unit, with the electronics bay and the yaw servo column - and that
is kept. The legacy turret that sat on it is not: a 12 mm solid Ø104 plate,
three M8 axle bolts, three separate hold-down clips and three more heat-set
inserts. turntable_stator.py and turntable_ring.py replace it.

So the underside of this part is the turntable disc:

  race face flat, r 23.0..31.0   where the three 608ZZ touch - keep it FLAT
  Ø68 boss, tt_boss_h proud      THE JOURNAL. It turns inside the ring's bore
                                 and it is what locates the arm radially.
  Ø76 rim below that             the ring hooks over it with 0.40 of daylight
  cross pocket + Ø6 bore         the yaw servo's horn drives this disc

The ring finishes flush with the boss top, so the plane the fork stands on IS
the boss top and nothing of the arm ever reaches past r 34.

Nothing caps rotation, so J1 gets the servo's full 180 deg.

THE SERVO POINTS DOWN, AND THAT IS THE WHOLE ARRANGEMENT. An MG995 is 40 mm
along its own long axis with the shaft 10 mm from one end, so 30 mm of case
has to go somewhere. Pointing it UP leaves the outer tab 33.9 mm above the
pitch axis, which is 20 mm past the top of the pivot boss: the mounting pad
becomes a free-standing ear, needs support material to print, and cantilevers
55 g of servo off nothing. Pointing it DOWN lands that same tab 1.6 mm inside
the disc. The pad then runs boss-to-disc as one unbroken web, prints with no
support in the +X build direction, and puts the heaviest single component at
the bottom of the arm where J1 pays least for it.

sb_stand_h IS BOXED IN, and that is why it is 38 and not a round number.
Above 39.6 the servo pad stops reaching the disc and becomes a cantilever
again; below about 30.4 the MG995's case fouls the retainer ring as the turret
turns past it. Both are asserted. Within that window, higher is better - every
millimetre buys a little more down-pitch before the arm reaches its own base.

THE LEGS ARE SOLID, ON PURPOSE. Every other link in this arm is hollowed to
the wall because its mass sits outboard of a joint that has to hold it up.
This part sits BELOW J2, so its mass loads no pitch joint at all - only J1,
whose axis is vertical, so gravity does not see it. What it does carry is the
entire arm's bending moment through two 7.5 mm plates. The disc is lightened
where that is provably free and nowhere else: the race band and the load path
under the legs stay full thickness.

THE TAB SLOTS ARE SLOTS BECAUSE THE DATASHEET IS NOT TRUSTWORTHY. The two
MG995 drawings Jonathan supplied disagree by 1.2 mm on tab span and 1.7 mm on
hole pitch (see lib/servo.py). A 5.6 mm slot along the case's long axis covers
both patterns. A self-tapper in a slot grips two flanks instead of a full
circle - call it half the pull-out of a round pilot, which against 9.4 kg cm
of stall through four screws is still not close.

Print orientation: -X face down, built along +X. Both journal bores come out
vertical and round; they are the only precision fits in the FORK. The disc
then stands on edge, which is wrong for a race face and for the Ø68 journal -
both want to come off the bed flat. If either proves out of round, split this
part on the boss top plane: the disc prints flat, the fork prints on its side,
and they bolt together on the same plane the ring already defines.

The shared wr_* block is defined identically in wrist_hub.py, wrist_roll.py,
forearm.py and upper_arm.py. MG995 dimensions are DATASHEET, not measured.
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

from lib.servo import micro_arm_w  # noqa: E402 - MEASURED horn taper

COMPONENT = 'robotarm_shoulder_bracket'
BODY_NAME = 'shoulder_bracket'
PREFIX = 'sb_'
WRIST = 'wr_'
TURRET = 'tt_'
STYLE = 'sty_'
PH_FORM = 'bracket form'
PH_PIVOT = 'pivot journals'
PH_DRIVE = 'servo mount'
PH_BASE = 'turntable interface'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_PIVOT, PH_DRIVE, PH_BASE, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# _style.md rule 5: two-tone by PART. A bracket is structure, so it is dark.
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

    def wrist(name, expr, comment='', units='mm'):
        _set(WRIST + name, expr, comment, units)

    def turret(name, expr, comment='', units='mm'):
        _set(TURRET + name, expr, comment, units)

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    def tval(name):
        return ups.itemByName(TURRET + name).value

    # ---- the SHARED joint contract ------------------------------------------
    # Identical in wrist_hub.py, wrist_roll.py, forearm.py and upper_arm.py.
    wrist('pivot_af', '16.0 mm',
          'hex across flats - the drive between a hub and the block it turns')
    wrist('straddle', '24.0 mm',
          'width a fork straddles - the upper arm is exactly this across')
    wrist('hub_d', '20.0 mm', 'hub journal collar diameter - SHARED, see wrist_hub.py')
    wrist('journal', '5.0 mm', 'collar length = the bore depth it runs in')
    wrist('flange_d', '24.0 mm', 'hub retaining flange diameter')
    wrist('flange_t', '2.0 mm', 'hub retaining flange thickness')
    wrist('reach', '3.8 mm', 'hex boss length past this plate - SHARED, see wrist_hub.py')

    # ---- the SHARED turntable contract --------------------------------------
    # Defined identically here, in turntable_stator.py and turntable_ring.py.
    # Only post_r is MEASURED (off the printed platter); the rest is ours.
    turret('post_r', '45.0 mm',
           'MEASURED: the platter carries 3 M3 heat-set inserts on this circle,\n'
           '           top face at its rim, az 120/180/240. The ONLY fixing there is.')
    turret('roller_od', '22.0 mm', '608ZZ outer diameter - DRAWING-CONFIRMED')
    turret('roller_w', '7.0 mm', '608ZZ width. The axle is RADIAL, so this lies radially.')
    turret('roller_r', '27.0 mm', 'roller pitch radius - SHARED, see turntable_stator.py')
    turret('race_margin', '0.5 mm', 'overrun each side of the rollers on the race band')
    turret('axle_z', '13.1 mm',
           'roller axle height. Set so the bearing clears the platter top by 1.0.')
    turret('race_z', TURRET + 'axle_z + ' + TURRET + 'roller_od / 2',
           'derived: where this part\'s underside sits. NEVER type this.')
    turret('disc_d', '76.0 mm',
           'rotor diameter. Not free: the MG995 pad below reaches r 32.1 and the\n'
           '           ring has to hook over the rim outside that.')
    turret('disc_t', '5.0 mm', 'rotor rim thickness, where the ring hooks over it')
    turret('boss_d', '68.0 mm',
           'the raised centre of this disc. This is the JOURNAL - it turns inside\n'
           '           the ring\'s bore, and it is what locates the arm radially.')
    turret('boss_h', '4.4 mm',
           'how far that boss stands above the rim. = ring_lift + ring_t, so the\n'
           '           ring finishes FLUSH with the boss top and the plane the fork\n'
           '           stands on is one continuous face.')
    turret('ring_t', '4.0 mm', 'retainer thickness - SHARED, see turntable_ring.py')
    turret('ring_or', '50.0 mm', 'ring outer radius - it is what the arm pitches down onto')
    turret('ring_lift', '0.40 mm', 'gap between the ring and the rim it holds down')
    turret('horn_span', '32.8 mm', 'yaw horn LONG-arm pocket span. The real 4-arm\n           horn runs ~33.5 tip to tip (ASYMMETRIC - short axis ~16; slots run\n           full span both ways, a slot longer than its arm is air), and the\n           arms were ALWAYS trimmed at assembly. 32.8 is the ceiling the\n           cable window allows (2 x (cable_ir - wall)) - trim to fit it.\n           2026-08-27 horn audit')
    # THE SLOTS ARE TAPERED, because the arm is. Widths come from
    # lib.servo.micro_arm_w() - the MEASURED taper, not a retyped constant,
    # so a re-measured horn moves this pocket on the next rebuild.
    _HORN_R_ROOT = 6.5
    _HORN_R_TIP = 16.4                       # = horn_span / 2, asserted below
    _HORN_CLEAR = 0.4
    turret('horn_r_root', '%.2f mm' % _HORN_R_ROOT,
           'where the tapered arm slots START - just outside the root relief.\n'
           '           Inboard of this the O13 relief swallows the arm roots whole.')
    turret('horn_w_root', '%.2f mm' % (micro_arm_w(_HORN_R_ROOT) + _HORN_CLEAR),
           'slot width at horn_r_root: MEASURED arm %.2f + %.1f clearance -\n'
           '           lib.servo.micro_arm_w(%.1f), 2026-08-28 bench.'
           % (micro_arm_w(_HORN_R_ROOT), _HORN_CLEAR, _HORN_R_ROOT))
    turret('horn_w_tip', '%.2f mm' % (micro_arm_w(_HORN_R_TIP) + _HORN_CLEAR),
           'slot width at the trim line: MEASURED arm %.2f + %.1f. The old\n'
           '           CONSTANT 3.4 (modelled 3.0 + 0.4) fit NOWHERE - the real arm\n'
           '           is 4.0 at its narrowest - and even a constant 4.4 would only\n'
           '           have taken it outboard of r 13.5. gauge_horn v1 CROSS, first\n'
           '           drop, 2026-08-28.' % (micro_arm_w(_HORN_R_TIP), _HORN_CLEAR))
    turret('horn_z', '2.4 mm', 'blade thickness 2.0 + 0.4 seating. At the old 1.8 a\n           real 2.0 blade stood proud and the rotor rode the horn, not the race\n           - horn audit. Pocket depth into this underside')
    turret('screw_bore', '6.0 mm', 'driver access to the horn screw, up the centre')

    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')
    style('radius', '6.0 mm', 'silhouette corner radius - _style.md rule 2')

    # ---- fits ---------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('rot', '0.35 mm', 'rotating fit - design_rules, both journals here')
    param('free', '0.4 mm', 'free fit - design_rules')

    # ---- the fork, derived exactly as forearm.py derives its own ------------
    param('gap', PREFIX + 'free', 'running gap, plate inner face to the straddled part')
    param('plate_in', WRIST + 'straddle / 2 + ' + PREFIX + 'gap', 'derived plate inner face')
    param('cbore_extra', '0.5 mm',
          'slack behind the hub flange so the hex bottoms in its socket and the\n'
          '           flange never becomes the stop')
    param('cbore_depth', WRIST + 'flange_t + ' + PREFIX + 'cbore_extra', 'derived')
    param('plate_t', WRIST + 'journal + ' + PREFIX + 'cbore_depth', 'derived plate thickness')
    param('plate_out', PREFIX + 'plate_in + ' + PREFIX + 'plate_t', 'derived plate outer face')
    param('bore_d', WRIST + 'hub_d + ' + PREFIX + 'rot', 'derived journal bore')
    param('cbore_d', WRIST + 'flange_d + ' + PREFIX + 'rot', 'derived flange counterbore')
    param('boss_r', PREFIX + 'cbore_d / 2 + ' + PREFIX + 'wall', 'derived pivot boss radius')

    # ---- the column ---------------------------------------------------------
    param('col_y', PREFIX + 'boss_r',
          'derived: the leg is exactly as wide as its own pivot boss, so the two\n'
          '           sides run in tangent to the boss circle and the silhouette is\n'
          '           one round-topped column with no corner to fillet')
    param('stand_h', '38.0 mm',
          'J2 axis above the BOSS TOP - which is the plane the retainer ring is\n'
          '           flush with, so it is also the top of the whole turntable. Boxed\n'
          '           in and asserted both ways: above ~39.6 the servo pad stops\n'
          '           reaching the disc, below ~30.4 the MG995 case fouls the ring.\n'
          '           It also sets the down-pitch limit - see the scan below.')

    # NOT LIGHTENED. The obvious pockets are all in the wrong place: inside the
    # race band is where the fork's load reaches the rollers, outside it is the
    # 4 mm rim the ring hooks over, and the middle is the journal. Spoking the
    # disc is possible and would save maybe 10 g of FILAMENT - it saves no
    # payload at all, because J1's axis is vertical.
    param('cable_ir', '18.0 mm', 'the loom passes through the disc, astern of the arm')
    # THE CONNECTOR GATE. The cable window is 3.4 mm wide radially (18.0 to
    # race_in - wall) and a standard servo plug is ~8.7 x 4.5 in cross-section:
    # the WIRES pass, the PLUGS on their ends do not. Found 2026-08-27. Without
    # this, every lead from a servo mounted after turret assembly (J3, J4, J5,
    # effector) cannot be threaded down to the bay - the arm has to come off
    # its rollers to feed wires. One keyhole at the window's centre azimuth
    # fixes it: plugs pass one at a time, ribbons then lie in the arc.
    #
    # THE GATE DELIBERATELY ENTERS THE HORN-ARM CORRIDOR. The astern arm of
    # the horn cross loses its side walls from gate_ir out to horn_span/2 -
    # about 3.8 mm of ONE of four arms, each bearing over its full 16 mm. At
    # 0.8 kg.cm of duty the lost area is nothing. The cable_ir assertion
    # protects the WINDOW from the horn; the gate floors at the screw bore.
    param('gate_w', '9.8 mm',
          'connector gate width, tangentially. A servo plug is ~8.7 wide;\n'
          '           +1.1 so it never needs forcing. Stays inboard of the fork'
          ' plates - asserted.')
    param('gate_ir', '12.2 mm',
          'how far in the gate bites. Floor: screw_bore/2 + wall. A plug is\n'
          '           4.5 thick and the gate spans from here to cable_ir - asserted.')
    param('cable_deg', '50.0 deg',
          'arc the cable window sweeps, centred astern at 270 - one of the two\n'
          '           azimuths a fork leg does not occupy (a leg spans -48..+48 about\n'
          '           its own side).', 'deg')

    # ---- MG995, DATASHEET (lib/servo.py) ------------------------------------
    param('case_l', '40.9 mm', 'MG995 case length - runs DOWN along Z, see the\n           docstring. 40.0 -> 40.9 on TowerPro B, 2026-08-27 flange audit')
    param('case_w', '20.0 mm', 'MG995 case width - lies along Y')
    param('shaft_end', '10.0 mm', 'shaft axis to the near end of the case, along Z')
    param('tab_thk', '2.5 mm', 'MG995 tab thickness - the pad is this proud, it is the datum')
    param('tab_below_top', '7.2 mm', 'case top to the tab TOP, along X - DERIVED from\n           TowerPro F 26.8: case_h - F - tab_thk. Was 7.5')
    param('tab_pitch', '47.8 mm',
          'tab hole pitch along the case, drawing B. Drawing A implies 49.5 - hence\n'
          '           slots, see MG995_TAB_SLOT_X_MM in lib/servo.py')
    param('tab_pitch_y', '10.2 mm', 'tab hole pitch across the case - MG995_TAB_HOLE_PITCH_Y')
    param('root_relief_d', '13.0 mm',
          'round relief at the yaw horn cross centre. The arms taper 5.5 -> 3\n           and are wider than the 3.4 slots everywhere inboard of r ~6.5, so\n           Ø13 clears that whole root zone; beyond it the slots take over.\n           2026-08-27 horn audit')
    param('slot_len', '5.6 mm', 'MG995_TAB_SLOT_X_MM - covers every candidate pitch\n           (derived 47.5, drawing B 47.8, clones 49.5)')
    param('slot_w', '2.5 mm', 'M3 self-tapper into PETG')
    param('slot_depth', '5.0 mm',
          'blind. Must stay inside the pad or the screws break through into the\n'
          '           straddle - asserted below.')
    param('horn_standoff', '2.0 mm',
          'the MG995 case stands this far off plate_out (it used to land flush).\n'
          '           2026-08-27 horn audit: the real horn hub is \u00d813.8 x 3.8, and\n'
          '           swallowing it at the old depth tunnelled a 0.8 mm tube through\n'
          '           the shoulder_hub hex root. Standing the servo off 2.0 pulls the\n'
          '           whole horn stack outboard so the hub bore stops at the hub\n'
          '           part\'s body and never enters the hex. shoulder_hub derives its\n'
          '           interface depths from the same 2.0 - the two files must agree.')
    param('lobe_t', PREFIX + 'tab_below_top + ' + PREFIX + 'tab_thk + '
          + PREFIX + 'horn_standoff',
          'derived: tab stack + horn_standoff, so the case top stands exactly\n'
          '           horn_standoff off plate_out and the tabs bear on the pad face')
    param('lobe_over', '1.0 mm', 'how far the pad sinks into the leg so the two merge')
    param('lobe_y', PREFIX + 'case_w / 2 + ' + PREFIX + 'wall', 'derived pad half width')
    param('lobe_pad', '3.0 mm', 'material past the end of the outermost tab slot')

    # ---- the upper arm, for the down-pitch scan ONLY -------------------------
    param('arm_l1', '65.0 mm',
          'upper arm length - MUST TRACK ua_l1 in upper_arm.py. Was 85.0 and did\n'
          '           NOT track it when ua_l1 moved to 65 on 2026-08-26, because a\n'
          '           comment is not a mechanism. The assertion below is.')
    param('arm_half', '13.0 mm',
          'upper arm half height at its widest (the drum) - MUST TRACK ua_drum_r.\n'
          '           Conservative: the waist is only 12.0.')

    # A COMMENT SAYING "MUST TRACK" IS NOT A MECHANISM. This part carries its
    # own copy of the upper arm's length so the down-pitch scan can run without
    # upper_arm in the document - and the copy silently went stale. The volume
    # ledger cannot catch it either, because the number is a DIAGNOSTIC and
    # moves no geometry. So: when upper_arm IS in the document, check.
    for _shared, _mine in (('ua_l1', 'arm_l1'), ('ua_drum_r', 'arm_half')):
        _p = ups.itemByName(_shared)
        if _p is not None:
            assert abs(_p.value - val(_mine)) < 1e-9, (
                '%s is %.2f mm and this part\'s %s says %.2f - the down-pitch '
                'limit below would be computed for an arm that does not exist'
                % (_shared, _p.value * 10, PREFIX + _mine, val(_mine) * 10))
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

    def mpt(sk, x_cm, y_cm, z_cm):
        return sk.modelToSketchSpace(P3(x_cm, y_cm, z_cm))

    def mm(cm):
        """cm -> a millimetre EXPRESSION. createByString reads a bare number as
        millimetres; val() hands out centimetres. See fusion/PLAYBOOK.md."""
        return '%.4f mm' % (cm * 10.0)

    def yz_circle(name, y_c, z_c, d_cm, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, 0, y_c, z_c), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def yz_rect(name, y0, y1, z0, z1, x0_expr, dx_expr, op):
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, 0, y0, z0), mpt(sk, 0, y1, z1))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def xy_circle(name, x_c, y_c, d_cm, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk, x_c, y_c, 0), d_cm / 2)
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def xy_rect(name, x0, x1, y0, y1, z0_expr, dz_expr, op):
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, y0, 0), mpt(sk, x1, y1, 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def xy_arc(name, r_in, r_out, mid_ang, half_ang, z0_expr, dz_expr, op):
        """An annular sector with square ends. Four curves closed by hand -
        Fusion will not infer a sector from two full circles."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        arcs = sk.sketchCurves.sketchArcs
        lines = sk.sketchCurves.sketchLines
        a0, a1 = mid_ang - half_ang, mid_ang + half_ang

        def p(r, a):
            return mpt(sk, r * math.cos(a), r * math.sin(a), 0)

        arcs.addByThreePoints(p(r_out, a0), p(r_out, mid_ang), p(r_out, a1))
        arcs.addByThreePoints(p(r_in, a0), p(r_in, mid_ang), p(r_in, a1))
        lines.addByTwoPoints(p(r_in, a0), p(r_out, a0))
        lines.addByTwoPoints(p(r_in, a1), p(r_out, a1))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def edge_along_x_at(y_c, z_c):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            b = e.boundingBox
            if (abs(b.minPoint.y - b.maxPoint.y) < val('tol')
                    and abs(b.minPoint.z - b.maxPoint.z) < val('tol')
                    and abs(b.minPoint.y - y_c) < val('tol')
                    and abs(b.minPoint.z - z_c) < val('tol')):
                col.add(e)
        return col

    # ---- values in cm --------------------------------------------------------
    stand = val('stand_h')
    disc_t = tval('disc_t')
    disc_r = tval('disc_d') / 2
    journal_r = tval('boss_d') / 2              # the TURNTABLE boss, not the pivot one
    boss_top = -stand                           # the plane the fork stands on
    rim_top = boss_top - tval('boss_h')
    race_z = rim_top - disc_t                   # the race face, and this part's floor
    race_in = tval('roller_r') - tval('roller_w') / 2 - tval('race_margin')
    race_out = tval('roller_r') + tval('roller_w') / 2 + tval('race_margin')
    ring_top = rim_top + tval('ring_lift') + tval('ring_t')
    boss_r = val('boss_r')                      # the PIVOT boss - a different thing
    col_y = val('col_y')
    lobe_t = val('lobe_t')

    # The servo runs DOWN: near end +shaft_end, far end 40 below that.
    case_hi = val('shaft_end')
    case_lo = case_hi - val('case_l')
    case_mid = (case_hi + case_lo) / 2.0
    screw_z = (case_mid - val('tab_pitch') / 2.0, case_mid + val('tab_pitch') / 2.0)
    lobe_lo = min(screw_z) - val('slot_len') / 2.0 - val('lobe_pad')
    lobe_hi = max(screw_z) + val('slot_len') / 2.0 + val('lobe_pad')

    # every corner of the fork and the pad, as a radius from the yaw axis
    leg_r = math.hypot(val('plate_out'), col_y)
    pad_r = math.hypot(val('plate_out') + lobe_t, val('lobe_y'))

    # ---- sanity, before any geometry ----------------------------------------
    assert wval('reach') > val('gap'), 'the hub hex does not reach across the running gap'
    assert val('slot_depth') <= lobe_t + 1e-9, (
        'the %.1f mm tab pilots break through a %.1f mm pad into the straddle'
        % (val('slot_depth') * 10, lobe_t * 10))
    assert val('lobe_y') <= col_y + 1e-9, (
        'the servo pad (%.1f half) is wider than the leg it hangs on (%.1f half)'
        % (val('lobe_y') * 10, col_y * 10))
    # --- the two that box stand_h in ---
    assert lobe_lo < boss_top - 1e-9, (
        'the servo pad stops %.2f below the axis and the boss top is %.2f - the pad '
        'does not reach the disc and is a cantilever again. sb_stand_h must be under '
        '%.2f.' % (-lobe_lo * 10, -boss_top * 10, -lobe_lo * 10))
    assert case_lo >= ring_top + val('free') - 1e-9, (
        'the MG995 case bottom sits at %.2f and the retainer ring reaches %.2f - the '
        'servo would strike the ring as the turret turns under it. sb_stand_h must '
        'be over %.2f.' % (case_lo * 10, ring_top * 10,
                           (tval('boss_h') - tval('ring_lift') - tval('ring_t')
                            + val('free') - case_lo) * 10))
    assert lobe_lo > race_z + 1e-9, 'the servo pad pokes through the race face'
    # --- the ring is flush with the boss top, so the fork must stay inside it ---
    assert abs(ring_top - boss_top) < 1e-9, (
        'tt_boss_h must equal ring_lift + ring_t so the ring finishes flush; the '
        'boss top is %.2f and the ring reaches %.2f'
        % (boss_top * 10, ring_top * 10))
    assert pad_r < journal_r - 1e-9, (
        'the servo pad reaches r %.1f and the journal boss it stands on is only r %.1f'
        % (pad_r * 10, journal_r * 10))
    assert leg_r < journal_r - 1e-9, (
        'a fork leg reaches r %.1f, past the journal boss at r %.1f' % (
            leg_r * 10, journal_r * 10))
    # --- the race band is sacred, and the rim has to be there to be held ---
    assert race_out < journal_r - 1e-9, (
        'the rollers run out to r %.1f, past the journal boss at r %.1f - the race '
        'band would be on the rim, not the boss' % (race_out * 10, journal_r * 10))
    # MILLIMETRES. val()/tval() are CENTIMETRES, so the bare literal goes on the
    # *10 form - written the other way round this fired on a good 4 mm rim.
    rim_mm = (disc_r - journal_r) * 10
    assert rim_mm >= 1.5, (
        'only %.2f mm of rim outside the journal for the ring to hook over' % rim_mm)
    assert val('cable_ir') + val('wall') < race_in, (
        'the cable window runs into the race band')
    assert val('cable_ir') >= tval('horn_span') / 2 + val('wall'), (
        'the cable window runs into the base servo horn')
    # --- the connector gate's own contracts, in MILLIMETRES ---
    _gate_w_mm = val('gate_w') * 10
    _gate_ir_mm = val('gate_ir') * 10
    _gate_span_mm = val('cable_ir') * 10 - _gate_ir_mm
    PLUG_W_MM, PLUG_T_MM = 8.7, 4.5     # standard JR/Futaba servo plug
    assert _gate_w_mm >= PLUG_W_MM + 1.0, (
        'the gate is %.1f wide and a servo plug is %.1f - it would need '
        'forcing' % (_gate_w_mm, PLUG_W_MM))
    assert _gate_span_mm >= PLUG_T_MM + 1.0, (
        'the gate spans %.1f radially and a plug is %.1f thick'
        % (_gate_span_mm, PLUG_T_MM))
    assert _gate_ir_mm >= (tval('screw_bore') / 2 + val('wall')) * 10, (
        'the gate reaches r %.1f, into the horn screw bore wall' % _gate_ir_mm)
    assert _gate_w_mm / 2 + val('wall') * 10 <= val('plate_in') * 10, (
        'the gate is %.1f wide and the fork plates start at |x| %.1f - it '
        'undercuts a leg' % (_gate_w_mm, val('plate_in') * 10))

    # How far the arm can pitch DOWN before it reaches the base it stands on.
    # Scanned, not solved. TWO obstacles now, not one: the disc out to r 48, and
    # the three clips standing clip_top proud of it beyond r 44. The disc is a
    # full circle, so unlike the old rectangular base plate there is no azimuth
    # that buys travel - this is the price of using the printed base.
    def hits_base(theta):
        s, c = math.sin(theta), math.cos(theta)
        d = 0.0
        while d <= val('arm_l1') + 1e-9:
            for t in (-val('arm_half'), 0.0, val('arm_half')):
                y = d * c + t * s
                z = -d * s + t * c
                if abs(y) <= tval('ring_or') and z <= boss_top:
                    return True
            d += 0.05
        return False

    down_deg = 0.0
    while down_deg < 90.0 and not hits_base(math.radians(down_deg + 0.5)):
        down_deg += 0.5
    assert down_deg >= 20.0, (
        'J2 can only pitch %.1f deg below horizontal before the arm reaches the '
        'turntable - raise sb_stand_h' % down_deg)

    def plate(sx):
        if sx > 0:
            return PREFIX + 'plate_in', PREFIX + 'plate_t'
        return '-' + PREFIX + 'plate_out', PREFIX + 'plate_t'

    # ---- phase 1: bracket form ------------------------------------------------
    t0 = design.timeline.count
    # The disc first, so both legs and the pad have something to merge into.
    # Rim then boss, in that order, so the step between them is unambiguous.
    xy_circle('turntable_rim', 0, 0, tval('disc_d'), mm(race_z), TURRET + 'disc_t', NEW)
    xy_circle('journal_boss', 0, 0, tval('boss_d'), mm(race_z),
              mm(disc_t + tval('boss_h')), JOIN)
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        # Column from the race face to the axis, then the boss on top of it.
        # col_y == boss_r, so the sides run in tangent and there is no corner.
        yz_rect('col_' + tag, -col_y, col_y, race_z, 0.0, x0, dx, JOIN)
        yz_circle('boss_' + tag, 0.0, 0.0, 2 * boss_r, x0, dx, JOIN)
    yz_rect('servo_pad', -val('lobe_y'), val('lobe_y'), lobe_lo, lobe_hi,
            PREFIX + 'plate_out - ' + PREFIX + 'lobe_over',
            PREFIX + 'lobe_t + ' + PREFIX + 'lobe_over', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: pivot journals ----------------------------------------------
    t1 = design.timeline.count
    for sx in (+1, -1):
        x0, dx = plate(sx)
        tag = 'p' if sx > 0 else 'm'
        if sx > 0:
            cb0 = PREFIX + 'plate_out - ' + PREFIX + 'cbore_depth'
        else:
            cb0 = '-' + PREFIX + 'plate_out'
        yz_circle('bore_' + tag, 0.0, 0.0, val('bore_d'), x0, dx, CUT)
        yz_circle('cbore_' + tag, 0.0, 0.0, val('cbore_d'), cb0,
                  PREFIX + 'cbore_depth', CUT)
    group(t1, PH_PIVOT)

    # ---- phase 3: servo mount ---------------------------------------------------
    t2 = design.timeline.count
    yz_rect('case_window',
            -(val('case_w') + val('loc')) / 2, (val('case_w') + val('loc')) / 2,
            case_lo - val('loc') / 2, case_hi + val('loc') / 2,
            PREFIX + 'plate_out', PREFIX + 'lobe_t', CUT)
    for i, z_s in enumerate(screw_z):
        for j, y_s in enumerate((-val('tab_pitch_y') / 2, val('tab_pitch_y') / 2)):
            xy = sketch(comp.yZConstructionPlane, 'sk_tab_slot_%d%d' % (i, j))
            r_s = val('slot_w') / 2
            hi_z, lo_z = z_s + val('slot_len') / 2 - r_s, z_s - val('slot_len') / 2 + r_s
            arcs, lines = xy.sketchCurves.sketchArcs, xy.sketchCurves.sketchLines
            arcs.addByThreePoints(mpt(xy, 0, y_s - r_s, hi_z), mpt(xy, 0, y_s, hi_z + r_s),
                                  mpt(xy, 0, y_s + r_s, hi_z))
            arcs.addByThreePoints(mpt(xy, 0, y_s + r_s, lo_z), mpt(xy, 0, y_s, lo_z - r_s),
                                  mpt(xy, 0, y_s - r_s, lo_z))
            lines.addByTwoPoints(mpt(xy, 0, y_s + r_s, hi_z), mpt(xy, 0, y_s + r_s, lo_z))
            lines.addByTwoPoints(mpt(xy, 0, y_s - r_s, hi_z), mpt(xy, 0, y_s - r_s, lo_z))
            extrude(profiles(xy, expected=1), CUT,
                    PREFIX + 'plate_out + ' + PREFIX + 'lobe_t - ' + PREFIX + 'slot_depth',
                    PREFIX + 'slot_depth', 'tab_slot_%d%d' % (i, j))
    group(t2, PH_DRIVE)

    # ---- phase 4: turntable interface ---------------------------------------------
    # Everything here is cut from the RACE FACE upward, because that face is the
    # datum the printed base sets and the only one worth measuring from.
    t3 = design.timeline.count
    # The base servo's horn, driving this disc: a cross, so it takes the four-arm
    # horn at 90 deg increments instead of relying on a press fit.
    half_span = tval('horn_span') / 2
    r_root = tval('horn_r_root')
    w_root = tval('horn_w_root') / 2
    w_tip = tval('horn_w_tip') / 2
    assert abs(half_span * 10 - _HORN_R_TIP) < 1e-6, (
        'horn_span/2 is %.2f but the tip width was cut for r %.2f - the taper '
        'is being evaluated at the wrong radius'
        % (half_span * 10, _HORN_R_TIP))
    assert w_root > w_tip, 'the arm tapers OUTWARD in this build - check micro_arm_w'
    assert 2 * w_root * 10 < val('root_relief_d') * 10, (
        'the slot is wider at its root (%.2f) than the O%.2f relief that is '
        'supposed to swallow the arm roots'
        % (2 * w_root * 10, val('root_relief_d') * 10))
    for ang, tag in ((0, 'a'), (1, 'b')):
        # one bowtie per axis: wide at the roots, narrowing to each trim line
        pts = [(-half_span, -w_tip), (-r_root, -w_root), (r_root, -w_root),
               (half_span, -w_tip), (half_span, w_tip), (r_root, w_root),
               (-r_root, w_root), (-half_span, w_tip)]
        if ang:
            pts = [(y, x) for (x, y) in pts]
        sk = sketch(comp.xYConstructionPlane, 'sk_horn_arm_' + tag)
        lines = sk.sketchCurves.sketchLines
        for k in range(len(pts)):
            a = pts[k]
            b = pts[(k + 1) % len(pts)]
            lines.addByTwoPoints(mpt(sk, a[0], a[1], 0), mpt(sk, b[0], b[1], 0))
        extrude(profiles(sk, expected=1), CUT, mm(race_z),
                TURRET + 'horn_z', 'horn_arm_' + tag)
    # The arm ROOTS, inboard of horn_r_root: the arm is at its widest there
    # and the tapered slots stop short of it. One round relief swallows every
    # root and the screw boss with it.
    xy_circle('horn_root_relief', 0, 0, val('root_relief_d'), mm(race_z),
              TURRET + 'horn_z', CUT)
    xy_circle('horn_screw_bore', 0, 0, tval('screw_bore'), mm(race_z),
              mm(disc_t + tval('boss_h')), CUT)
    # The loom, astern of the arm at 270 deg - one of the two azimuths a leg
    # does not occupy.
    xy_arc('cable_window', val('cable_ir'), race_in - val('wall'),
           -math.pi / 2, val('cable_deg') / 2, mm(race_z),
           mm(disc_t + tval('boss_h')), CUT)
    # The connector gate: a keyhole merging with the window's inner edge at
    # its centre azimuth. See the gate_w/gate_ir comments for why it exists
    # and why entering the horn-arm corridor is deliberate.
    _vol_before_gate = comp.bRepBodies.item(0).volume
    xy_rect('connector_gate', -val('gate_w') / 2, val('gate_w') / 2,
            -val('cable_ir'), -val('gate_ir'), mm(race_z),
            mm(disc_t + tval('boss_h')), CUT)
    _gate_drop = (_vol_before_gate - comp.bRepBodies.item(0).volume) * 1000
    # PLAYBOOK: when a CUT changes nothing, the cut is in the wrong place.
    assert _gate_drop > 100.0, (
        'the connector gate removed %.1f mm3 - a 9.8 x 5.8 through-cut '
        'should take ~500; wrong place or wrong scale' % _gate_drop)
    group(t3, PH_BASE)

    # ---- phase 5: finish -------------------------------------------------------------
    t4 = design.timeline.count
    col = adsk.core.ObjectCollection.create()
    for y_c in (-val('lobe_y'), val('lobe_y')):
        for e in edge_along_x_at(y_c, lobe_hi):
            col.add(e)
    n_filleted = col.count
    if col.count:
        f_inp = fil.createInput()
        f_inp.addConstantRadiusEdgeSet(col, V(STYLE + 'radius'), True)
        fil.add(f_inp).name = 'pad_corners'
    group(t4, PH_FINISH)

    # ---- identity + diagnostics ---------------------------------------------------
    assert comp.bRepBodies.count == 1, (
        'expected 1 body, got %d - a leg or the pad is not reaching the disc'
        % comp.bRepBodies.count)
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used_appearance = 'none'
    for want_a in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want_a):
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
    print('fork: plates |x| %.1f..%.1f (%.1f thick), bore %.2f, cbore %.2f x %.1f, '
          'boss r %.2f' % (val('plate_in') * 10, val('plate_out') * 10,
                           val('plate_t') * 10, val('bore_d') * 10,
                           val('cbore_d') * 10, val('cbore_depth') * 10, boss_r * 10))
    print('column: %.1f wide x %.1f tall from the boss top to the axis' % (
        col_y * 20, stand * 10))
    print('TURNTABLE ROTOR (this part IS J1\'s rotating half):')
    print('  race face z %.2f | rim %.1f dia x %.2f to z %.2f | journal boss %.1f '
          'dia, %.2f proud, top z %.2f' % (
              race_z * 10, tval('disc_d') * 10, disc_t * 10, rim_top * 10,
              tval('boss_d') * 10, tval('boss_h') * 10, boss_top * 10))
    print('  race band r %.1f..%.1f, rollers at r %.1f - LEFT FLAT, never pocketed' % (
        race_in * 10, race_out * 10, tval('roller_r') * 10))
    print('  ring laps the rim from r %.1f and finishes FLUSH with the boss top' % (
        (tval('boss_d') / 2 + 0.0175) * 10))
    print('  horn cross %.1f span, TAPERED %.2f wide at r %.1f -> %.2f at the '
          'trim line, %.2f deep, screw bore %.1f (MEASURED taper 2026-08-28)' % (
              tval('horn_span') * 10, tval('horn_w_root') * 10,
              tval('horn_r_root') * 10, tval('horn_w_tip') * 10,
              tval('horn_z') * 10, tval('screw_bore') * 10))
    print('CLEARANCES:')
    print('  servo pad reaches r %.1f, fork legs r %.1f, journal boss is r %.1f' % (
        pad_r * 10, leg_r * 10, journal_r * 10))
    print('  MG995 case bottom z %.2f vs ring top z %.2f -> %.2f mm of daylight' % (
        case_lo * 10, ring_top * 10, (case_lo - ring_top) * 10))
    print('  servo pad ends z %.2f, %.2f mm inside the boss top' % (
        lobe_lo * 10, (boss_top - lobe_lo) * 10))
    print('MG995 runs DOWN: case z %.1f..%.1f, tab slots z %.1f / %.1f (%.1f long x '
          '%.1f), pad z %.1f..%.1f x %.1f thick' % (
              case_lo * 10, case_hi * 10, screw_z[0] * 10, screw_z[1] * 10,
              val('slot_len') * 10, val('slot_w') * 10,
              lobe_lo * 10, lobe_hi * 10, lobe_t * 10))
    print('J2 DOWN-PITCH LIMIT: %.1f deg before the arm reaches the turntable '
          '(arm %.0f long, %.1f half height, ring r %.1f)' % (
              down_deg, val('arm_l1') * 10, val('arm_half') * 10,
              tval('ring_or') * 10))
    print('CONNECTOR GATE: %.1f x %.1f keyhole at az 270, r %.1f..%.1f - servo'
          % (val('gate_w') * 10, val('cable_ir') * 10 - val('gate_ir') * 10,
             val('gate_ir') * 10, val('cable_ir') * 10))
    print('  plugs (~8.7 x 4.5) pass here; the 3.4 window takes only wires.')
    print('J1 TRAVEL: the full servo 180 deg - the ring hooks over the rim, so '
          'nothing caps rotation')
    print('filleted %d pad corners at r %.1f' % (
        n_filleted, ups.itemByName(STYLE + 'radius').value * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | printed ~%.1f g | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000,
        body.physicalProperties.mass * 1000 * 0.6, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
