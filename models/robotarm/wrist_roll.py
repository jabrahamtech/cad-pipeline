"""robotarm/wrist_roll - Fusion MCP generating script.

Rebuilds `robotarm_wrist_roll` (idempotent). Spec:
specs/robotarm/wrist_roll.md, styled per specs/robotarm/_style.md.

The piece between the two wrist joints. It PITCHES about J4 - a hex socket
in each side face takes a wrist_hub, one driven by the forearm's MG90S -
and it HOUSES the J5 roll SG90, whose shaft points forward along the arm.
The hand bolts to a rotator on that shaft and rolls.

Local frame: origin on the J4 PITCH axis. +X along that axis, +Y forward
toward the hand, +Z up.

WHY THIS PART EXISTS AT ALL. Without it the pitch fork has to straddle the
gripper's 48 mm hand, and every attempt at that came out too wide or too
heavy - 94 mm and 95 g at worst. Straddling this instead, the fork spans
24 mm. The sixth servo deletes more part than it adds.

The roll SG90 lies with its LONG axis across Z, not Y: turned the other way
its 22.6 mm case length would set this housing's width, and the width is
exactly what the fork has to straddle. On its side it sets the height
instead, which is free. The 6.1 mm offset from the shaft to the near end of
the case is why the housing is not symmetric about z = 0.

THE KEEL. Everything this piece sweeps about J4 has to clear the forearm,
and the forearm has only 40 mm to reach the pivot from the elbow. A plain
slab put its bottom-front corner 28.6 mm from the pitch axis, which the
forearm cannot get past. Below the servo pocket the part is therefore not
a slab but a KEEL: a narrow rib that exists only to enclose the lower
mounting tab, bevelled at 45 deg where it meets the back face. That drops
the swept radius to 25.2 mm and takes 5 g of dead plastic out of a part
hanging off a 1.0 kg.cm elbow.

PRINT ORIENTATION: BACK FACE (y = wro_y_back) ON THE BED, BUILT ALONG +Y.
Re-derived 2026-08-31 rather than inherited - the audit is
specs/robotarm/_printability.md. The bed_face_chamfer in phase 4 is cut at
y_back, so the file and this paragraph agree; if one moves, move both.

WHY THIS WAY UP. Every planar face of the slab, of the servo bay, of the tab
slots and of the lead keyway is PARALLEL to +Y, so all of them print at 0
deg from vertical; the rotator bore is a hole straight down the build axis,
so it needs no teardrop; and the keel's back face is the single sloped
surface, cut at exactly 45 deg FOR THIS ORIENTATION. Nothing else comes
close, and each alternative was worked out rather than waved off:

  front face down (-Y)  deletes the bay ceiling outright - but the keel's
                        front face then starts 76.8 mm2 of solid in mid-air
                        8.4 mm up, and it cannot be bevelled back, because
                        the lower tab slot needs full material out to
                        y 8.6 all the way down to z -21.5. That trades a
                        legal bridge for an illegal 90 deg overhang.
  top face down (-Z)    turns the bay FLOOR into a 315 mm2 ceiling and the
                        keel bevel stops doing anything.
  keel down (+Z)        stands a 24 x 31 slab on a 16 x 16 keel and makes
                        the whole slab underside a 90 deg ceiling 4.8 mm up.
  side face down (X)    is the shortest build at 24 mm and makes the hex
                        sockets vertical - but the bay's blind end becomes a
                        582 mm2 ceiling on a 22.9 mm span and the rotator
                        bore becomes a horizontal Oe11 hole wanting a
                        teardrop.

WHAT STILL PRINTS OVER AIR, STATED RATHER THAN CLAIMED AWAY. The old line
here was "No support", and it had never been audited. It cannot be true of
an ENCLOSED BAY: whatever roof the bay has is printed over air. The bay's
blind end used to be a FLAT 12.4 mm ceiling at the far end of a 25.4 mm
hole that opens only at the bed - the one place on this part where a support
tower cannot be reached with any tool. Jonathan, from the bench: "the worst
supports and its just impossible to clean". That end is now a GABLE - two 45
deg flanks and a wro_bay_crown flat - so the free span falls 12.4 -> 7.6 mm
and the sharp internal corner a slicer overhang detector latches onto is
gone. It costs front wall: 5.6 -> wro_front_wall (3.2) over a 7.6 mm band,
which is still 2 x MIN_WALL and is asserted below.

Three things are left, all of them listed with real spans and angles in
specs/robotarm/_printability.md: the 7.6 mm bay crown, two 12.4 mm tab-slot
bridges, and the J4 hex sockets, whose roof facets sit at 60 deg because
that is what a vertex-up hexagon IS - no rotation improves it (a flat-up hex
is 90 deg over the full 16.0 af) and no relief fits, since there is exactly
one wall above the socket apex. Every bridge here is inside MAX_BRIDGE_MM
(40.0) by at least 3x. SLICE THIS PART WITH SUPPORT OFF.

The SHARED wr_* block is defined identically in wrist_hub.py and
wrist_fork.py. SG90 dimensions are DATASHEET (lib/servo.py).
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

from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402 - the J5 gap
from lib.design_rules import MAX_BRIDGE_MM  # noqa: E402 - the bay/tab bridges
from lib.design_rules import MAX_OVERHANG_DEG  # noqa: E402 - keel bevel, gable
from lib.servo import CATALOG  # noqa: E402 - MEASURED lead bundle

COMPONENT = 'robotarm_wrist_roll'
BODY_NAME = 'wrist_roll'
PREFIX = 'wro_'
WRIST = 'wr_'
STYLE = 'sty_'
PH_FORM = 'housing form'
PH_SERVO = 'roll servo bay'
PH_PIVOT = 'pitch sockets'
PH_FINISH = 'finish'
PHASES = [PH_FORM, PH_SERVO, PH_PIVOT, PH_FINISH]
MATERIAL_NAME = 'PET Plastic'
# A count, not a dimension. Hoisted out of hex_socket() because the
# PRINTABILITY block below has to derive the socket's roof angle from the
# same number the socket is drawn from, rather than from a typed 60.
HEX_SIDES = 2 * 3
# _style.md rule 5: two-tone by PART. A wrist is a joint, so it is dark.
# COLOUR LIVES IN lib/palette.py, not here. It used to be typed in this
# file and sixteen others, so a re-theme meant editing seventeen files
# and hoping you found them all.
from lib.palette import hints_for  # noqa: E402
APPEARANCE_HINTS = hints_for('wrist_roll')
_SG90 = CATALOG['SG90']
# SG90 tab underside to case top, DATASHEET via lib/servo.py. Used to
# prove this file's typed case_h / tab_plane still agree with the library.
_SG90_CASE_TOP_MM = _SG90.tab_thk + _SG90.tab_below_top


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

    def style(name, expr, comment='', units='mm'):
        _set(STYLE + name, expr, comment, units)

    def val(name):
        return ups.itemByName(PREFIX + name).value

    def wval(name):
        return ups.itemByName(WRIST + name).value

    # --- SHARED J4 pivot contract -------------------------------------------
    wrist('pivot_af', '16.0 mm',
          'J4 hex socket across flats - SHARED, defined identically in\n'
          '           wrist_hub.py and forearm.py')
    wrist('straddle', '24.0 mm',
          'the width the forearm fork straddles = this housing across the pitch\n'
          '           axis. SHARED - the fork sets its plates off this, so the two\n'
          '           files have to agree or the wrist binds.')
    wrist('sweep_r', '25.4 mm',
          'the radius this housing sweeps about J4. SHARED: no forearm material\n'
          '           inside the straddle may come closer than this to the pitch axis,\n'
          '           or the wrist collides with its own arm at full pitch. Asserted\n'
          '           against every silhouette corner below.')
    style('ef', '0.4 mm', 'elephant-foot chamfer, functional faces - design_rules')

    # --- fits ----------------------------------------------------------------
    param('wall', '1.6 mm', 'minimum wall - design_rules MIN_WALL_MM')
    param('loc', '0.2 mm', 'locational fit - design_rules')
    param('free', '0.4 mm', 'free fit - design_rules')

    # --- SG90, DATASHEET (lib/servo.py) --------------------------------------
    param('case_l', '22.7 mm', 'SG90 case length - lies along Z here. TowerPro B')
    param('case_w', '12.2 mm', 'SG90 case width - lies along X, so it sets the fork\n           span. 12.6 -> 12.2 on TowerPro D, 2026-08-27 flange audit')
    param('case_h', '23.7 mm', 'SG90 case height - lies along Y, the roll axis')
    param('shaft_end', '6.1 mm', 'shaft axis to the NEAR end of the case, along Z')
    param('tab_span', '32.3 mm', 'SG90 tab tip to tab tip, along Z. TowerPro E')
    param('tab_thk', '2.4 mm', 'SG90 tab thickness, along Y')
    param('tab_plane', '17.0 mm', 'case bottom to the tab UNDERSIDE, along Y')
    param('boss_h', '4.2 mm', 'output boss height above the case top')
    param('boss_d', '5.0 mm', 'output boss diameter')

    # --- derived servo placement ---------------------------------------------
    # ---- THE J5 RUNNING GAP, AND WHY THE SERVO SANK 0.40 -------------------
    # wrist_rotator.py no longer bores onto a horn; it bores onto the SG90
    # SPLINE, and lib/servo_hub seats every spline hub ONE RUNNING GAP above
    # the case top. wrt_seat_z moves 6.70 -> 7.10.
    #
    # THE HORN-ERA STACK WAS RUBBING BY CONSTRUCTION. The old relief
    # swallowed boss + hub and sat the rotator's back face FLAT on the SG90
    # case top with zero gap - while that disc ROTATES against the case. It
    # was a brake, not a joint, and it is the same fault the J1 horn had.
    #
    # WHICH PLANE IS HELD, AND WHY IT IS THIS ONE. wro_rot_seat is where
    # wrist_rotator's seating face lands, and the hand hangs off the rotator,
    # so it is the plane the whole effector is positioned by. It does NOT
    # move. The SERVO stands off 0.40 further from it instead - which is what
    # wrist_rotator.py means by "wrist_roll.py has to stand the J5 servo off
    # by 0.40 more than it does today". Holding the servo and letting the
    # rotator walk forward would have been the same 0.40 of clearance and
    # would have moved the gripper, the reach and the J4 sweep with it.
    param('case_gap', '%.4f mm' % _FIT['free'],
          'running gap between the SG90 case top and wrist_rotator\'s seating\n'
          '           face. design_rules JOINT_FIT_MM free - the same number\n'
          '           lib/servo_hub.spline_hub() seats on and wrt_case_gap declares.')
    param('rot_seat', '11.7 mm',
          'where wrist_rotator\'s SEATING FACE sits, and therefore where the\n'
          '           hand hangs from. UNCHANGED by the horn migration, and chosen so\n'
          '           the servo straddles the PITCH axis: its mass then costs J4\n'
          '           almost nothing. This is the datum; the servo is placed off it.')
    param('case_top', PREFIX + 'rot_seat - ' + PREFIX + 'case_gap',
          'derived roll servo case top: one running gap BEHIND the rotator\'s\n'
          '           seating face, where it used to be flat against it. Everything\n'
          '           else about the servo - case_bot, tab_lo, keel_front, lead_y -\n'
          '           is derived from this and follows it back the same 0.40.')
    param('case_bot', PREFIX + 'case_top - ' + PREFIX + 'case_h', 'derived case bottom')
    param('case_z_hi', PREFIX + 'shaft_end', 'derived: case top edge in Z, above the shaft')
    param('case_z_lo', PREFIX + 'case_z_hi - ' + PREFIX + 'case_l', 'derived case bottom edge in Z')
    param('tab_lo', PREFIX + 'case_bot + ' + PREFIX + 'tab_plane', 'derived tab underside')
    param('tab_over', '(' + PREFIX + 'tab_span - ' + PREFIX + 'case_l) / 2',
          'derived tab overhang past the case')
    param('bay_half_x', PREFIX + 'case_w / 2 + ' + PREFIX + 'loc / 2',
          'derived half width of the servo bay, and of the tab slots that run\n'
          '           in the same walls. It was written out longhand in three places;\n'
          '           it is named here because it is also the BRIDGE SPAN every\n'
          '           ceiling in this part is measured against (2 x this = 12.4).')
    param('bay_end', PREFIX + 'case_top + ' + PREFIX + 'loc / 2',
          'derived blind end of the servo bay - half a locational fit past the\n'
          '           case top. It is a CLEARANCE face, not a datum: the servo is\n'
          '           located axially by its tabs in wro_tab_slots, which is why the\n'
          '           gable below is free to open this end up without moving a servo.')

    # --- housing envelope -----------------------------------------------------
    param('half_x', '12.0 mm',
          'half width. Sized by the hex socket: 3.4 mm deep from this face has to '
          'leave a wall beside the servo pocket. THIS is what the fork straddles')
    param('socket_d', '3.4 mm', 'hex socket depth into the side wall')
    param('y_back', '-14.0 mm', 'back face')
    param('y_front', '17.0 mm', 'front face - past the servo boss, carries the rotator bore')
    param('z_top', WRIST + 'pivot_af / cos(30 deg) / 2 + ' + PREFIX + 'wall',
          'derived top face. A guessed 10.0 put the face INSIDE the hex socket\n           circumradius (9.24) - derive it from the socket so it stays right if\n           the pivot size ever moves.')
    param('z_bot',
          PREFIX + 'case_z_lo - ' + PREFIX + 'tab_over - ' + PREFIX + 'loc / 2 - '
          + PREFIX + 'wall',
          'derived keel underside: a wall below the lower tab tip. Derived, not\n'
          '           guessed - a hardcoded -23.0 left only 1.5 mm of floor there.')
    param('body_bot', PREFIX + 'case_z_lo - ' + PREFIX + 'loc / 2 - ' + PREFIX + 'wall',
          'derived: the floor under the servo pocket, and where the slab stops.\n'
          '           Everything below this is keel, not slab.')
    param('keel_half_x', '8.0 mm',
          'keel half width - it only has to enclose the tab, which is as wide as\n'
          '           the case, so it need not run out to the side walls')
    param('keel_front', PREFIX + 'tab_lo + ' + PREFIX + 'tab_thk + ' + PREFIX + 'wall',
          'derived keel front face: a wall past the tab slot')
    param('keel_top', PREFIX + 'case_z_lo',
          'derived: the keel overlaps the slab by wall + loc/2 rather than meeting\n'
          '           it exactly. Two volumes that TOUCH are non-manifold - see PLAYBOOK.')
    param('rot_bore', '11.0 mm', 'clearance bore for the boss and the rotator hub')
    # ---- THE BAY ROOF, AND WHY IT IS A GABLE AND NOT A ROOF ---------------
    # A full 45 deg gable over a 12.4 mm bay needs 6.2 mm of rise, and there
    # are only 5.6 mm between the bay end (11.4) and the front face (17.0) -
    # and the last 3.2 of those are wall. So the gable is TRUNCATED: 45 deg
    # flanks as far as the wall allows, then a flat crown. That is the whole
    # design of it, and both numbers are derived from the wall, not chosen.
    param('front_wall', '2 * ' + PREFIX + 'wall',
          'wall left standing between the bay crown and the front face. TWO\n'
          '           walls, not one: wrist_rotator seats on this face and the whole\n'
          '           hand hangs off it, so the crown is not allowed to thin it to\n'
          '           the MIN_WALL floor. Asserted below.')
    param('bay_roof', PREFIX + 'y_front - ' + PREFIX + 'front_wall - ' + PREFIX + 'bay_end',
          'derived 45 deg rise of the bay gable: every millimetre between the\n'
          '           bay end and the front wall, and no more. At 45 deg the rise IS\n'
          '           the horizontal reach, so this is also how far each flank eats\n'
          '           into the span.')
    param('bay_crown', '2 * (' + PREFIX + 'bay_half_x - ' + PREFIX + 'bay_roof)',
          'derived flat left at the top of the gable - the only part of the bay\n'
          '           roof still at 90 deg, and the number that has to stay under\n'
          '           design_rules MAX_BRIDGE_MM. 12.4 flat became 7.6 flat.')

    # --- lead escape ---------------------------------------------------------
    param('lead_key_d',
          '%.2f mm' % (CATALOG['SG90'].lead_bundle_dia + _FIT['locational']),
          'lead keyway WIDTH across the case width, centred - one full bundle\n'
          '           diameter plus a locational fit. Without it the servo cannot be\n'
          '           inserted at all; see the cut. MEASURED bundle, lib/servo.py.')
    param('lead_d', '3.4 mm',
          'SG90 lead_bundle_dia - lib/servo.py. Typed here like the other\n'
          '           DATASHEET numbers; _check_leads probes with the LIBRARY value,\n'
          '           so if the two drift the gate fails rather than lying.')
    param('lead_y', PREFIX + 'case_bot + ' + PREFIX + 'lead_d',
          'derived: where the lead leaves the case bottom end face - one lead\n'
          '           diameter up from the case bottom, centred across the width.\n'
          '           The same rule _check_leads places its probe by.')
    param('tol', '0.001 mm', 'geometric edge-selection tolerance, not a dimension')

    # ---- idempotent rebuild --------------------------------------------------
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
            # Without this a CUT eats every other component in the document.
            # See fusion/PLAYBOOK.md.
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

    def slab(name, x0, x1, z0, z1, y0_expr, dy_expr, op):
        """Block whose XZ outline is a rectangle, extruded along Y."""
        sk = sketch(comp.xZConstructionPlane, 'sk_' + name)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk, x0, 0, z0), mpt(sk, x1, 0, z1))
        return extrude(profiles(sk, expected=1), op, y0_expr, dy_expr, name)

    def prism_x(name, pts_yz, x0_expr, dx_expr, op):
        """Solid whose YZ silhouette is a polygon, extruded along X."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts_yz)):
            u, w = pts_yz[i], pts_yz[(i + 1) % len(pts_yz)]
            lines.addByTwoPoints(mpt(sk, 0, u[0], u[1]), mpt(sk, 0, w[0], w[1]))
        return extrude(profiles(sk, expected=1), op, x0_expr, dx_expr, name)

    def prism_z(name, pts_xy, z0_expr, dz_expr, op):
        """Solid whose XY silhouette is a polygon, extruded along Z.

        The third of the trio. slab() covers rectangles-along-Y and prism_x()
        covers silhouettes-along-X; the bay gable is the first feature in this
        part that varies in X AND Y at once, which neither of those can draw."""
        sk = sketch(comp.xYConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts_xy)):
            u, w = pts_xy[i], pts_xy[(i + 1) % len(pts_xy)]
            lines.addByTwoPoints(mpt(sk, u[0], u[1], 0), mpt(sk, w[0], w[1], 0))
        return extrude(profiles(sk, expected=1), op, z0_expr, dz_expr, name)

    def hex_socket(name, sign):
        """Hex pocket in one side face, axis along X, centred on the pitch axis."""
        sk = sketch(comp.yZConstructionPlane, 'sk_' + name)
        lines = sk.sketchCurves.sketchLines
        r_c = wval('pivot_af') / 2 / math.cos(math.pi / HEX_SIDES)
        pts = []
        for i in range(HEX_SIDES):
            a = 2 * math.pi * i / HEX_SIDES
            pts.append((r_c * math.cos(a), r_c * math.sin(a)))
        for i in range(len(pts)):
            u, w = pts[i], pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(mpt(sk, 0, u[0], u[1]), mpt(sk, 0, w[0], w[1]))
        if sign > 0:
            return extrude(profiles(sk, expected=1), CUT,
                           PREFIX + 'half_x', '-' + PREFIX + 'socket_d', name)
        return extrude(profiles(sk, expected=1), CUT,
                       '-' + PREFIX + 'half_x', PREFIX + 'socket_d', name)

    # ---- values in cm ---------------------------------------------------------
    half_x = val('half_x')
    loc = val('loc')
    bay_half_x = val('bay_half_x')
    socket_wall = half_x - val('socket_d') - bay_half_x
    assert socket_wall >= val('wall'), (
        'only %.2f mm of wall between the hex socket and the servo pocket' % (socket_wall * 10))
    r_c = wval('pivot_af') / 2 / math.cos(math.pi / HEX_SIDES)
    assert r_c + val('wall') <= val('z_top'), 'the hex socket breaks out of the top face'

    # LEAD KEYWAY sanity, in cm. The keyway is a centred slot in the pocket's
    # +Z END wall - the shaft end, which is where the bundle leaves the case.
    # It replaces a Ø5 channel bored through the pocket floor and keel at the
    # -Z end: that channel was sited from the superseded "leads leave the FAR
    # end" reading and, under the measured datum, drained nothing.
    # bundle + ONE locational fit, the convention every lead keyway in the
    # project uses (forearm, turntable_stator, _gauge_verify). The Ø5 channel
    # this replaces could afford 2 x loc; a 3.6 slot cannot.
    assert val('lead_key_d') >= val('lead_d') + loc, (
        'the lead keyway is tighter than the bundle plus a locational fit')
    assert val('lead_key_d') / 2 + val('wall') <= r_c - val('socket_d'), (
        'the lead keyway comes within a wall of the J4 hex sockets. The two '
        'side-wall keyways it replaces DID cut into them, by 1.2 mm.')
    assert val('lead_y') + val('lead_key_d') / 2 < val('case_top'), (
        'the keyway runs past the case front face and into the rotator bore')

    # The keel's back face is a 45 deg bevel, not a wall: it starts at the bed
    # plane as a knife edge and grows downward one layer per layer, so it needs
    # no support, AND it keeps the bottom-back corner inside the sweep circle.
    keel_drop = val('keel_top') - val('z_bot')
    keel_pts = [(val('y_back') + keel_drop, val('z_bot')),
                (val('keel_front'), val('z_bot')),
                (val('keel_front'), val('keel_top')),
                (val('y_back'), val('keel_top'))]
    body_pts = [(val('y_back'), val('body_bot')), (val('y_front'), val('body_bot')),
                (val('y_front'), val('z_top')), (val('y_back'), val('z_top'))]
    worst = ('', 0.0)
    for label, pts in (('slab', body_pts), ('keel', keel_pts)):
        for y, z in pts:
            r = math.hypot(y, z)
            if r > worst[1]:
                worst = ('%s corner (%.1f, %.1f)' % (label, y * 10, z * 10), r)
    assert worst[1] <= wval('sweep_r'), (
        'the %s sweeps %.1f mm about J4, past the %.1f mm the forearm allows'
        % (worst[0], worst[1] * 10, wval('sweep_r') * 10))

    # ---- PRINTABILITY GATE, back face on the bed, built +Y -------------------
    # Jonathan, from the bench, 2026-08-31: "can you make sure things like the
    # wrist piece are easy to print because that piece came out with the worst
    # supports and its just impossible to clean". He has PRINTED this. That is
    # a measurement and it outranks anything written in this repo, so the
    # angles below are computed from the polygons this script actually draws
    # rather than recited from the docstring. Part-by-part audit and the
    # surfaces that are still not clean: specs/robotarm/_printability.md.
    #
    # THE CONVENTION, once, so the numbers mean something: angle from the
    # BUILD AXIS. A face parallel to +Y is 0 deg, a face square across it is
    # 90, and design_rules.MAX_OVERHANG_DEG (50.0) is the limit. A 90 deg face
    # anchored on BOTH sides is not an overhang at all, it is a BRIDGE, and it
    # answers to MAX_BRIDGE_MM (40.0) instead. Every 90 deg face left in this
    # part is a bridge, and each one is named below.
    gable_pts = [(-bay_half_x, val('bay_end')), (bay_half_x, val('bay_end')),
                 (bay_half_x - val('bay_roof'), val('bay_end') + val('bay_roof')),
                 (-(bay_half_x - val('bay_roof')), val('bay_end') + val('bay_roof'))]
    gable_deg = math.degrees(math.atan2(gable_pts[1][0] - gable_pts[2][0],
                                        gable_pts[2][1] - gable_pts[1][1]))
    assert gable_deg <= MAX_OVERHANG_DEG, (
        'the bay gable flanks are %.1f deg from the build axis and design_rules '
        'allows %.1f - the far end of the bay is the ONE ceiling on this part '
        'that no tool can reach once it is printed'
        % (gable_deg, MAX_OVERHANG_DEG))
    keel_bevel_deg = math.degrees(math.atan2(keel_pts[3][1] - keel_pts[0][1],
                                             keel_pts[0][0] - keel_pts[3][0]))
    assert keel_bevel_deg <= MAX_OVERHANG_DEG, (
        'the keel bevel is %.1f deg from the build axis and design_rules allows '
        '%.1f - it is the only sloped face on the part and the whole reason '
        'this orientation works' % (keel_bevel_deg, MAX_OVERHANG_DEG))
    # THE HEXAGON IS NOT FIXABLE AND IS NOT ASSERTED. A vertex-up hexagon roofs
    # at this angle by definition; rotating it 30 deg gives a FLAT top at 90
    # deg over the full 16.0 af, which is worse, and there is exactly one wall
    # between the socket apex and wro_z_top, so no relief fits above it. It is
    # PRINTED, not gated, and it is written up in _printability.md.
    hex_roof_deg = math.degrees(math.atan2(math.sin(2 * math.pi / HEX_SIDES),
                                           1 - math.cos(2 * math.pi / HEX_SIDES)))
    bridges = [('bay crown', val('bay_crown')),
               ('tab slots', bay_half_x * 2),
               ('lead keyway', val('lead_key_d'))]
    for _label, _span in bridges:
        assert _span * 10 <= MAX_BRIDGE_MM, (
            'the %s bridges %.1f mm and design_rules allows %.1f'
            % (_label, _span * 10, MAX_BRIDGE_MM))
    assert val('bay_crown') > 0, (
        'the bay gable meets itself before it reaches the front wall - '
        'wro_bay_roof %.2f is more than the %.2f half span it has to cover, so '
        'there is no crown left to bridge'
        % (val('bay_roof') * 10, bay_half_x * 10))
    assert val('y_front') - val('bay_end') - val('bay_roof') >= val('wall'), (
        'the bay gable leaves only %.2f mm of front wall and MIN_WALL is %.2f - '
        'wrist_rotator seats on that face and the hand hangs off it'
        % ((val('y_front') - val('bay_end') - val('bay_roof')) * 10,
           val('wall') * 10))
    # THE SG90 OUTPUT BOSS, which nothing in this file used to check against
    # anything. It stands proud of the case top and turns inside the rotator
    # bore, so the bore has to clear it radially AND still be there when the
    # boss tops out. The gable never fouls it: the bore is wider than the boss
    # and concentric with it, so it has already removed everything the crown
    # could have been in the way of.
    assert val('boss_d') + val('free') <= val('rot_bore'), (
        'the Oe%.1f SG90 output boss turns inside the Oe%.1f rotator bore and '
        'wants a free fit - that is %.2f mm short'
        % (val('boss_d') * 10, val('rot_bore') * 10,
           (val('boss_d') + val('free') - val('rot_bore')) * 10))
    assert val('case_top') + val('boss_h') <= val('y_front') + val('wall'), (
        'the boss tops out at y %.2f and the rotator bore only runs to %.2f'
        % ((val('case_top') + val('boss_h')) * 10,
           (val('y_front') + val('wall')) * 10))

    # ---- phase 1: housing form -------------------------------------------------
    t0 = design.timeline.count
    slab('housing', -half_x, half_x, val('body_bot'), val('z_top'),
         PREFIX + 'y_back', PREFIX + 'y_front - ' + PREFIX + 'y_back', NEW)
    prism_x('keel', keel_pts, '-' + PREFIX + 'keel_half_x',
            '2 * ' + PREFIX + 'keel_half_x', JOIN)
    group(t0, PH_FORM)

    # ---- phase 2: roll servo bay ------------------------------------------------
    t1 = design.timeline.count
    slab('servo_case_pocket',
         -bay_half_x, bay_half_x,
         val('case_z_lo') - loc / 2, val('case_z_hi') + loc / 2,
         PREFIX + 'y_back - ' + PREFIX + 'wall',
         PREFIX + 'bay_end - ' + PREFIX + 'y_back + ' + PREFIX + 'wall',
         CUT)
    # THE BAY ROOF. Cut AFTER the bay and over exactly the bay's own Z run, so
    # the two merge into one cavity with a gabled far end instead of a flat
    # one. The trapezoid IS the material being taken out: what is left behind
    # is its upper boundary - two 45 deg flanks and a wro_bay_crown flat.
    #
    # THIS IS THE FIX FOR THE BENCH REPORT. A flat blind end 25.4 mm down a
    # hole that only opens at the bed is the one ceiling on this part that
    # nothing can reach afterwards, so it is the one that must not be left to
    # a slicer's judgement. It is not a full gable: see wro_bay_roof for why
    # 5.6 mm of front wall cannot hold one.
    prism_z('bay_roof_gable', gable_pts,
            PREFIX + 'case_z_lo - ' + PREFIX + 'loc / 2',
            PREFIX + 'case_l + ' + PREFIX + 'loc', CUT)
    # LEAD KEYWAY. The bundle leaves the case's SHORT END FACE at the shaft
    # end - here the +Z end, since the case lies with its long axis across Z
    # - dead centre across the width (lib/servo.py lead datum). The case
    # travels the full pocket depth on the way in, so the cable's exit point
    # sweeps Y from the pocket mouth to its seated position at lead_y: the
    # keyway has to span that whole run or the cable is pinched partway.
    #
    # ONE notch, centred. The two ±X side-wall notches this replaces were
    # sited from a misreading of lead_x, and they cut 1.2 mm into the J4 hex
    # pitch sockets on the way past - a fault nothing caught because the
    # gate that would have (_check_leads) was itself sited from the same
    # misreading. It breaks through the roof rather than leaving a 1.04 mm
    # skin over the slot, which is under wall and would print as two
    # perimeters and a hope.
    slab('lead_key', -val('lead_key_d') / 2, val('lead_key_d') / 2,
         val('case_z_hi') + loc / 2, val('z_top') + loc / 2,
         PREFIX + 'y_back - ' + PREFIX + 'wall',
         PREFIX + 'lead_y + ' + PREFIX + 'lead_key_d / 2 - ' + PREFIX
         + 'y_back + ' + PREFIX + 'wall',
         CUT)
    slab('tab_slots',
         -bay_half_x, bay_half_x,
         val('case_z_lo') - val('tab_over') - loc / 2,
         val('case_z_hi') + val('tab_over') + loc / 2,
         PREFIX + 'tab_lo - ' + PREFIX + 'loc / 2',
         PREFIX + 'tab_thk + ' + PREFIX + 'loc', CUT)
    # (the Ø5 lead_channel that used to be cut here, down through the pocket
    # floor and the keel at the -Z end, is gone. It drained the end the
    # bundle does not leave from.)
    sk_rot = sketch(comp.xZConstructionPlane, 'sk_rotator_bore')
    sk_rot.sketchCurves.sketchCircles.addByCenterRadius(
        mpt(sk_rot, 0, 0, 0), val('rot_bore') / 2)
    extrude(profiles(sk_rot, expected=1), CUT, PREFIX + 'case_top',
            PREFIX + 'y_front - ' + PREFIX + 'case_top + ' + PREFIX + 'wall', 'rotator_bore')
    group(t1, PH_SERVO)

    # ---- phase 3: pitch sockets --------------------------------------------------
    t2 = design.timeline.count
    for sx in (-1, 1):
        hex_socket('pitch_socket_%d' % sx, sx)
    group(t2, PH_PIVOT)

    # ---- phase 4: finish -----------------------------------------------------------
    t3 = design.timeline.count
    for y_pick, nm in ((val('y_back'), 'bed_face_chamfer'), (val('y_front'), 'front_chamfer')):
        col = adsk.core.ObjectCollection.create()
        for e in comp.bRepBodies.item(0).edges:
            eb = e.boundingBox
            if (abs(eb.minPoint.y - y_pick) < val('tol')
                    and abs(eb.maxPoint.y - y_pick) < val('tol')):
                col.add(e)
        c_inp = chf.createInput2()
        c_inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(col, V(STYLE + 'ef'), False)
        chf.add(c_inp).name = nm
    group(t3, PH_FINISH)

    # ---- identity + diagnostics --------------------------------------------------
    assert comp.bRepBodies.count == 1, 'expected 1 body, got ' + str(comp.bRepBodies.count)
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
    print('THE FORK STRADDLES %.1f mm - the whole reason this part exists' % (half_x * 2 * 10))
    # THE TWO NUMBERS THE SPLINE STACK RESTS ON. wro_case_h and wro_tab_plane
    # are typed DATASHEET copies; if either drifts from lib/servo.py the servo
    # is placed from one set of numbers and bored from another.
    _case_top_from_tabs = (val('case_top') - val('tab_lo')) * 10
    assert abs(_case_top_from_tabs - _SG90_CASE_TOP_MM) < val('tol') * 10, (
        'this file places the SG90 case top %.2f above its tab underside and '
        'lib/servo.py says %.2f - wro_case_h or wro_tab_plane has drifted from '
        'the library' % (_case_top_from_tabs, _SG90_CASE_TOP_MM))
    _seat_from_tabs = (val('rot_seat') - val('tab_lo')) * 10
    assert abs(_seat_from_tabs - (_SG90_CASE_TOP_MM + val('case_gap') * 10)) < val('tol') * 10, (
        'wrist_rotator seats %.2f up the SG90 by this part\'s arithmetic and '
        'wrt_seat_z is %.2f - the disc would be bored from one number and '
        'located by another'
        % (_seat_from_tabs, _SG90_CASE_TOP_MM + val('case_gap') * 10))
    print('J5 DRIVE: no horn. wrist_rotator bores onto the SG90 spline and '
          'seats %.2f up it (%.2f off the case top), at y %.2f'
          % (_seat_from_tabs, val('case_gap') * 10, val('rot_seat') * 10))
    print('   so the servo stands off %.2f further than it did: case top y '
          '%.2f, was %.2f. The rotator seat, and the hand on it, did NOT move'
          % (val('case_gap') * 10, val('case_top') * 10, val('rot_seat') * 10))
    print('roll servo: case y %.1f..%.1f, z %.1f..%.1f | tabs y %.1f, z +/-%.1f' % (
        val('case_bot') * 10, val('case_top') * 10,
        val('case_z_lo') * 10, val('case_z_hi') * 10, val('tab_lo') * 10,
        (val('case_z_hi') + val('tab_over')) * 10))
    print('keel: y %.1f..%.1f, z %.1f..%.1f, %.1f wide, back face bevelled %.1f' % (
        val('y_back') * 10, val('keel_front') * 10, val('z_bot') * 10,
        val('keel_top') * 10, val('keel_half_x') * 2 * 10, keel_drop * 10))
    print('lead keyway: %.1f wide, centred, in the +Z END wall at z %.1f, '
          'running y %.1f..%.1f and out through the roof at z %.1f'
          % (val('lead_key_d') * 10, (val('case_z_hi') + loc / 2) * 10,
             (val('y_back') - val('wall')) * 10,
             (val('lead_y') + val('lead_key_d') / 2) * 10, val('z_top') * 10))
    print('PRINTABILITY - BACK FACE ON THE BED (y %.1f), BUILT +Y, SUPPORT OFF.'
          % (val('y_back') * 10))
    print('  every slab, bay, tab-slot and keyway face is parallel to the build')
    print('  axis (0 deg). What is not:')
    print('    keel back bevel   %5.1f deg over %.1f mm   (limit %.1f) OK'
          % (keel_bevel_deg, keel_drop * 10, MAX_OVERHANG_DEG))
    print('    bay gable flanks  %5.1f deg, rising %.1f mm (limit %.1f) OK'
          % (gable_deg, val('bay_roof') * 10, MAX_OVERHANG_DEG))
    print('    J4 hex roofs      %5.1f deg over %.1f mm   (limit %.1f) OVER - '
          'a vertex-up hexagon roofs at this angle by definition; %.2f of wall'
          % (hex_roof_deg, val('socket_d') * 10, MAX_OVERHANG_DEG,
             (val('z_top') - r_c) * 10))
    print('                      above the apex leaves nowhere to put a relief. '
          'DECLARED, see _printability.md.')
    print('  bridges (90 deg but anchored both sides, limit %.1f mm):'
          % MAX_BRIDGE_MM)
    for _label, _span in bridges:
        print('    %-14s %5.1f mm' % (_label, _span * 10))
    print('  the bay crown WAS a flat %.1f mm ceiling %.1f mm down a hole that '
          'opens only at the bed. That is the support Jonathan could not reach.'
          % (bay_half_x * 2 * 10, (val('bay_end') - val('y_back')) * 10))
    print('WORST SWEEP about J4: %s at %.1f mm (forearm allows %.1f)' % (
        worst[0], worst[1] * 10, wval('sweep_r') * 10))
    print('hex socket %.1f af, %.1f deep, leaving %.2f mm of wall beside the servo' % (
        wval('pivot_af') * 10, val('socket_d') * 10, socket_wall * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
        bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
        bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.0f | mass g: %.2f | valid: %s' % (
        body.volume * 1000, body.physicalProperties.mass * 1000, body.isValid))
    print('bodies: %d | sketches: %d | user params: %d' % (
        comp.bRepBodies.count, comp.sketches.count, ups.count))
    print('timeline groups: %r' % (PHASES,))
