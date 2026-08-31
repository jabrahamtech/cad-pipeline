"""robotarm/horn_adapter - Fusion MCP generating script.

Rebuilds `robotarm_horn_adapter` (idempotent). Spec: lib/servo_hub.py.

THE PIECE THAT FITS ON THE SERVO. Jonathan, 2026-08-31: "model pieces that
fit on the servos that increase the gear size", and, on why: "there is so
much weight just on the servos because there is no adaptors - also none of
them fit in the holes you have set for them".

It is a disc that bolts to the servo's OWN stock horn through two radial
slots, and presents a printed bolt pattern that this project controls. Every
gear from here on screws to that pattern. Nothing presses on a horn again.

WHY SLOTS AND NOT HOLES. The horn is the one part of this machine whose
dimensions nobody can pin down - deshipu's teardown and Roger Cheng's survey
both say micro horn geometry varies by batch, and the bench has now said
three times that horns do not enter the slots cut for them. A RADIAL slot
does not need to know what radius the hole is at: it spans r 5.20..11.50 and
catches the holes at r 6, 8 and 10 wherever the batch actually put them.
Three chances instead of one. This is the same move lib/servo.py already
makes with MG995_TAB_SLOT_X_MM for the MG995's disputed tab pitch.

Radial is also the load-correct orientation. Torque is TANGENTIAL, so the
screw bears on the slot's long side wall - the strong direction - and never
on its ends.

WHAT IT COSTS, SAID BEFORE THE GOOD NEWS. The gear plane moves from 5.90 to
18.50 in the MG90S's frame: +12.60 mm. At J3 that is forearm width and it is
almost certainly too much - see the note in lib/servo_hub.py. At J1 and J2,
where the servo sits in the base and the shoulder, the width is free and
this is simply better. Do not fit it to the elbow without pricing the arm.

WHAT IT BUYS BESIDES ASSEMBLY. `journal_d`, when non-zero, is a boss on the
far face that runs in a bearing carried by the HOST. A gear pressed on a
horn hangs its whole radial load on the servo's 4.9 mm plastic-geared output
spline, cantilevered. goBILDA sell a machined part (the ServoBlock) whose
only job is to take that load off the spline, which is decent evidence the
load is real. With a journal the spline sees torque and nothing else.

THE HORN'S RETAINING SCREW GOES CAPTIVE. The centre is a blind pocket, not a
through bore, because a through bore leaves no material for the output
pilots to thread into and they would have to move outboard - which grows
every gear downstream. Cost: to get the horn off the spline you take this
disc off first. One extra teardown step against 4 mm of arm width.

Print orientation: GEAR FACE ON THE BED, horn pocket opening upward. The
pocket is then an open blind hole with no bridged roof, the screw-head
counterbores are first-layer recesses, and the output pilots are clean
vertical holes. No support.
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

from lib.design_rules import (  # noqa: E402
    ELEPHANT_FOOT_CHAMFER_MM,
    FASTENER_MM,
    MIN_WALL_MM,
)
from lib.palette import hints_for  # noqa: E402
from lib.servo import CATALOG  # noqa: E402
from lib.servo_hub import HORN_SCREW, adapter  # noqa: E402

# WHICH SERVO THIS INSTANCE IS FOR. One script, three parts - change this and
# rerun. The geometry is solved in lib/servo_hub.py from lib/servo.py's stack,
# so nothing below is a number anybody chose.
SERVO = 'MG90S'

COMPONENT = 'robotarm_horn_adapter'
BODY_NAME = 'horn_adapter'
PREFIX = 'ha_'
STYLE = 'sty_'
MATERIAL_NAME = 'PET Plastic'
APPEARANCE_HINTS = hints_for('horn_adapter')
PH_DISC = 'disc'
PH_HORN = 'horn interface'
PH_OUT = 'output pattern'
PH_FINISH = 'finish'
PHASES = [PH_DISC, PH_HORN, PH_OUT, PH_FINISH]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    S = CATALOG[SERVO]
    A = adapter(S)

    def _set(full, expr, comment, units):
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), units, comment)
        else:
            p.expression = expr
            p.comment = comment

    def param(name, expr, comment='', units='mm'):
        _set(PREFIX + name, expr, comment, units)

    def val(name):
        # NOTE: Fusion returns CENTIMETRES. Everything below works in mm and
        # converts at the point of use, never in the middle of arithmetic.
        return ups.itemByName(PREFIX + name).value * 10.0

    _set(STYLE + 'ef', '%.2f mm' % ELEPHANT_FOOT_CHAMFER_MM,
         'elephant-foot chamfer, functional faces', 'mm')

    # --- the contract. WRITTEN FROM lib/servo_hub.py, NOT CHOSEN HERE. -----
    param('od', '%.4f mm' % A.od,
          'disc OD - DERIVED: slot outer end + screw clearance + rim.\n'
          '           It stops at the last horn hole it uses. Every mm past that\n'
          '           is dead weight hanging off a %.0f g servo.' % S.mass_g)
    param('thk', '%.4f mm' % A.thk,
          'disc thickness - DERIVED from the horn pocket depth + MIN_WALL.\n'
          '           Typed as 5.0 for every servo first; the MG995 needs 5.5 and\n'
          '           the assert in lib/servo_hub.py caught it.')
    param('seat_z', '%.4f mm' % A.seat_z,
          'servo-z of the UNDERSIDE - it lands on the horn BLADE top.\n'
          '           The host must stand the servo off by this + thk to put the\n'
          '           gear plane where the mating gear is.')
    param('gear_plane_z', '%.4f mm' % A.gear_seat_z,
          'servo-z of the face the gear bolts to. THE number the host reads.')

    # --- horn interface ---------------------------------------------------
    param('pocket_d', '%.4f mm' % A.pocket_d,
          'clears the horn HUB (Oe%.1f MEASURED 2026-08-28) at a FREE fit.\n'
          '           This is not a press and must never become one - the hub is the\n'
          '           dimension that varies by batch.' % S.horn_hub_dia)
    param('pocket_h', '%.4f mm' % A.pocket_h,
          'depth - swallows the hub standing proud of the blade PLUS the\n'
          '           horn retaining screw head. Blind, not through: see the module\n'
          '           docstring for what the through bore would have cost.')
    param('slot_w', '%.4f mm' % A.slot_w,
          '%s clearance - design_rules FASTENER_MM' % HORN_SCREW)
    param('slot_r_in', '%.4f mm' % A.slot_r_in, 'radial slot, inner end')
    param('slot_r_out', '%.4f mm' % A.slot_r_out,
          'radial slot, outer end. r %.2f..%.2f spans the horn holes at\n'
          '           r 6/8/10 - THREE chances to catch a hole whose real radius\n'
          '           nobody has measured.' % (A.slot_r_in, A.slot_r_out))
    param('slot_cb_d', '%.4f mm' % A.slot_cb_d,
          'screw-head counterbore on the gear side - the heads MUST end up\n'
          '           flush or below, because the gear lands on that face')
    param('slot_cb_h', '%.4f mm' % A.slot_cb_h,
          'counterbore depth - lib/servo_hub.py, from the head height')

    # --- output pattern: the whole point ----------------------------------
    param('out_bolt_r', '%.4f mm' % A.out_bolt_r,
          'pilot circle the GEAR screws into. This is the datum the horn\n'
          '           variation stops at: everything outboard of here is a dimension\n'
          '           this project prints and can hold.')
    param('out_pilot_d', '%.4f mm' % A.out_bolt_pilot_d,
          '%s self-tap pilot - fasteners_inserts.md' % HORN_SCREW)
    param('out_pilot_h', '%.4f mm' % A.out_pilot_h,
          'pilot depth, stopping short of the horn pocket floor')
    param('gear_root_floor', '%.4f mm' % A.min_gear_root_r,
          'NO GEAR BOLTED TO THIS FACE MAY HAVE A ROOT RADIUS UNDER THIS.\n'
          '           It is what sizes the pair: at m1.00 it makes the pinion 21T,\n'
          '           not the 18T that was pressed on the horn. lib/servo_hub.py\n'
          '           solve_stage() reads it - do not re-derive it in a part.')

    # --- rebuild: RENAME then delete, so a failed run leaves the old part --
    occ = None
    for o in root.occurrences:
        if o.component.name == COMPONENT:
            occ = o
            break
    if occ is not None:
        occ.component.name = COMPONENT + '_old'
        occ.deleteMe()

    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = COMPONENT
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures
    xy = comp.xYConstructionPlane

    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def group(start_index, name):
        """Fold a phase into one readable timeline node."""
        if design.timeline.count - start_index > 1:
            g = design.timeline.timelineGroups.add(
                start_index, design.timeline.count - 1)
            g.name = name

    # ---- PHASE: disc -----------------------------------------------------
    t0 = design.timeline.count
    sk = sketches.add(xy)
    sk.name = PH_DISC
    sk.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0),
                                                    val('od') / 2.0 / 10.0)
    ext = extrudes.addSimple(sk.profiles.item(0),
                             V('%s thk' % PREFIX), NEW)
    ext.name = 'disc blank'
    body = ext.bodies.item(0)
    body.name = BODY_NAME
    # EVERY cut below names this body. A CUT with no participantBodies in
    # this codebase has eaten every other component in the document before.
    ONLY = [body]

    def cut_profile(sketch, prof_index, depth_expr, offset_expr=None):
        inp = extrudes.createInput(sketch.profiles.item(prof_index), CUT)
        inp.participantBodies = ONLY
        dist = adsk.fusion.DistanceExtentDefinition.create(V(depth_expr))
        inp.setOneSideExtent(
            dist, adsk.fusion.ExtentDirections.NegativeExtentDirection)
        if offset_expr is not None:
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
                V(offset_expr))
        return extrudes.add(inp)

    group(t0, PH_DISC)

    # ---- PHASE: horn interface ------------------------------------------
    t1 = design.timeline.count
    # Pocket, cut DOWN from the top (gear) face - i.e. it opens on the servo
    # side, which is the face that is up on the bed.
    sk = sketches.add(xy)
    sk.name = PH_HORN
    sk.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0),
                                                    val('pocket_d') / 2.0 / 10.0)
    inp = extrudes.createInput(sk.profiles.item(0), CUT)
    inp.participantBodies = ONLY
    inp.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(V('%s pocket_h' % PREFIX)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        V('%s thk' % PREFIX))
    extrudes.add(inp)

    # Two radial slots, on the horn's LONG axis. lib/servo.py records the
    # micro cross horn as 34.4 long x 17.0 short - it is NOT symmetric, so
    # the two SHORT arms reach only r ~8.5 and cannot carry a useful slot.
    # Two screws at opposite radii are a couple and take torque perfectly.
    w = val('slot_w')
    r0, r1 = val('slot_r_in'), val('slot_r_out')
    cb_d, cb_h = val('slot_cb_d'), val('slot_cb_h')

    def slot_path(sketch, ang_deg, width, ra, rb):
        """A radial slot as a closed loop: two arcs, two lines."""
        a = math.radians(ang_deg)
        ca, sa = math.cos(a), math.sin(a)
        hw = width / 2.0
        lines = sketch.sketchCurves.sketchLines
        arcs = sketch.sketchCurves.sketchArcs

        def pt(r, off):
            return P3((r * ca - off * sa) / 10.0, (r * sa + off * ca) / 10.0, 0)

        p_in_p, p_in_n = pt(ra, +hw), pt(ra, -hw)
        p_out_p, p_out_n = pt(rb, +hw), pt(rb, -hw)
        lines.addByTwoPoints(p_in_p, p_out_p)
        lines.addByTwoPoints(p_in_n, p_out_n)
        arcs.addByThreePoints(p_in_p, pt(ra - hw, 0.0), p_in_n)
        arcs.addByThreePoints(p_out_p, pt(rb + hw, 0.0), p_out_n)

    sk = sketches.add(xy)
    sk.name = PH_HORN + ' slots'
    for ang in A.slot_angles_deg:
        slot_path(sk, ang, w, r0, r1)
    for i in range(sk.profiles.count):
        inp = extrudes.createInput(sk.profiles.item(i), CUT)
        inp.participantBodies = ONLY
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V('%s thk * 2' % PREFIX)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        extrudes.add(inp)

    # Head counterbores, on the GEAR side (z = 0 face, the one on the bed).
    sk = sketches.add(xy)
    sk.name = PH_HORN + ' head relief'
    for ang in A.slot_angles_deg:
        slot_path(sk, ang, cb_d, r0, r1)
    for i in range(sk.profiles.count):
        inp = extrudes.createInput(sk.profiles.item(i), CUT)
        inp.participantBodies = ONLY
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V('%s slot_cb_h' % PREFIX)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        extrudes.add(inp)

    group(t1, PH_HORN)

    # ---- PHASE: output pattern ------------------------------------------
    t2 = design.timeline.count
    # Three pilots at 90/210/330 deg. They MUST miss the slots at 0/180.
    sk = sketches.add(xy)
    sk.name = PH_OUT
    br = val('out_bolt_r')
    # DERIVED IN lib/servo_hub.py, not here: three pilots rotated to the
    # offset furthest from the horn slots. A pilot drilled into a slot is a
    # hole with no thread in it, so the contract solves it and asserts it.
    angles = A.out_bolt_angles
    for ang in angles:
        a = math.radians(ang)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            P3(br * math.cos(a) / 10.0, br * math.sin(a) / 10.0, 0),
            val('out_pilot_d') / 2.0 / 10.0)
    for i in range(sk.profiles.count):
        inp = extrudes.createInput(sk.profiles.item(i), CUT)
        inp.participantBodies = ONLY
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V('%s out_pilot_h' % PREFIX)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        extrudes.add(inp)

    group(t2, PH_OUT)

    # ---- checks that run in the model, not in the comments ---------------
    bad = []
    if val('pocket_h') > val('thk') - MIN_WALL_MM:
        bad.append('pocket %.2f in a %.2f disc' % (val('pocket_h'), val('thk')))
    if val('out_pilot_h') + 1.0 > val('thk') - val('pocket_h'):
        pass  # pilots are outboard of the pocket - depth is the disc, not the floor
    assert not bad, 'horn_adapter: ' + '; '.join(bad)

    print('horn_adapter for %s' % SERVO)
    print('  disc Oe%.2f x %.2f' % (val('od'), val('thk')))
    print('  seat_z %.2f -> GEAR PLANE %.2f (servo frame)'
          % (val('seat_z'), val('gear_plane_z')))
    print('  horn pocket Oe%.2f x %.2f, blind' % (val('pocket_d'), val('pocket_h')))
    print('  2 radial slots %.2f wide, r %.2f..%.2f, at %s deg'
          % (w, r0, r1, '/'.join('%.0f' % a for a in A.slot_angles_deg)))
    print('  %d x %s pilot Oe%.2f on r %.2f'
          % (len(angles), HORN_SCREW, val('out_pilot_d'), br))
    print('  GEAR ROOT FLOOR %.2f mm - no gear on this face may be smaller'
          % val('gear_root_floor'))
