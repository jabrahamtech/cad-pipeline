"""robotarm/_check_motor_clearance - GATE motor_clearance.

Does the MOVING half of each joint clear the MOTOR HARDWARE, all the way
through that joint's travel?

Spec: specs/robotarm/_motor_clearance.md. Driver, not a part.

THE COMPLAINT THIS FILE EXISTS FOR. Jonathan, with the printed parts in his
hands, 2026-09-02: "the joints dont have clearance where the motor bits are".
GATE servo_fit reads 7/7 clear on the same design. Both can be true at once,
because servo_fit asks a strictly smaller question than the bench does: it
drops the servo solid into the host that CARRIES it, AT REST, and measures
overlap. Four things are outside that question and every one of them is a
"motor bit":

  1 THE OTHER HALF OF THE JOINT. The servo sits in the fixed half. The thing
    that strikes it is the half that SWINGS PAST. servo_fit never builds that
    part at all, so no amount of clearance in the servo's own pocket says
    anything about it. That gap is the whole reason for this file, and it is
    the reading of the complaint that fits the words: a joint can only fail
    to have clearance WHERE IT MOVES.
  2 THE LEAD BUNDLE, against that moving half. _check_leads does test the
    bundle, but only against the HOST - seated, and along the insertion path.
    A cable that leaves its own pocket cleanly and is then guillotined by the
    link swinging past reads CLEAR in both existing gates.
  3 THE TAB SCREW HEADS. servo_body.py CUTS the two tab holes and models no
    screw in them. Every mount in this arm clamps the tab TOP in a recess cut
    exactly tab_thk deep (shoulder_bracket: "the pad clamps the tab TOP on
    that floor"), so the tab finishes FLUSH with the pad face and the SCREW
    HEAD becomes the highest thing on the servo - a hard steel dome standing
    proud of the pad, sitting in the plane the moving half sweeps through.
    Nothing in this project has ever modelled it.
  4 THE RETAINING SCREW AND ITS WASHER. Since the horn came out, every driven
    part in this arm bores onto the spline and is held down by the servo's own
    screw through a washer - lib/servo_hub.spline_hub(), whose docstring says
    in as many words that the washer "is not optional". Six parts each check
    that THEY clear it. Not one thing checks what SWEEPS PAST it, and it is
    the tallest object on the whole motor stack.

METHOD, and its limits stated before its results:

- The host, the moving part and the servo solid are built into ONE document
  and placed from _check_leads.MOUNTS. THE PLACEMENT IS IMPORTED, NEVER
  RE-TYPED. That table already owns where every servo sits and is already
  maintained; a second copy here would be this project's own named failure -
  a datum only one file reads. The frame MATH is imported from the same file
  for the same reason, underscore names and all: _check_leads owns the
  convention that servo +y is COMPUTED as za x xa, and a second hand-rolled
  copy of it here could go left-handed on its own.
- The moving part is stepped through its travel in SWEEP_STEPS positions.
  At each step: sampled interference (mm3) and the true minimum gap (mm).
- INTERFERENCE IS pointContainment, ONLY. TemporaryBRepManager.booleanOperation
  returns empty in this codebase and reads as "no interference", which is the
  worst failure a gate can have. Sampling resolves nothing finer than STEP, so
  a 0.00 mm3 row is NOT a pass on its own - read the gap column with it.
- CLEARANCE IS measureManager.measureMinimumDistance, which is exact and does
  see what the sampler misses. That pairing is the point: the sampler says how
  BADLY two things overlap, the measurement says how NEARLY they do.
- ONLY THE INTERSECTION OF THE TWO BOUNDING BOXES IS SAMPLED. _check_servo_fit
  learned this the hard way - walking a whole bounding box tests tens of
  thousands of points nowhere near the other body and never finishes. An
  interference can only be where both boxes are, so that is the only place
  worth asking about.

THE POSITIVE CONTROL, AND WHY IT CANNOT BE BACKWARDS. _check_servo_fit's first
control drove the servo along -insert, which WITHDREW it from the host, and
four of seven stations quietly read 0.00 mm3. The lesson is not "pick the
other sign", it is "never let a sign be picked at all". So this control does
not choose a direction: it MEASURES one. measureMinimumDistance returns the
two WITNESS POINTS of the closest approach - one on the moving body, one on
the motor hardware - and the control translates the moving part along the
vector FROM its own witness point TO the servo's, by that same gap plus
CONTROL_OVERDRIVE_MM. Landing the moving body's nearest point CONTROL_OVERDRIVE
past the other body's nearest point is contact by construction, not by hope,
and the direction is derived from the pair in that order, so there is no sign
left to get wrong. It is then checked three ways and any one of them failing
fails the gate:
    a the control vector must point at the motor hardware
      (dot(unit, servo_centre - moving_centre) > 0) - things move TOGETHER;
    b the re-measured gap after the shift must be ~0 - they are touching;
    c the sampled control volume must exceed JAM_MM3 - the sampler can see it.

THE SECOND CONTROL, on the placement table itself. Each station re-derives the
servo's tab plane from the HOST's own user parameters and compares it with the
shaft coordinate MOUNTS carries. shoulder_bracket.py states in its docstring
that its row is right and is not to be touched, so J2's delta MUST come back
0.00: if it does not, this audit is wrong and every other delta it prints is
noise. That is what makes a non-zero delta somewhere else worth acting on.

WHAT THIS STILL DOES NOT CHECK, named rather than left to be discovered:

  ONE MOVER PER JOINT. Each station sweeps the ONE part that most obviously
  passes the servo. At J3 that is the 36T gear, and the UPPER ARM swings about
  the same axis and is not built here - its fork straddles the forearm on the
  far side of the standoff and its pose needs the J2 chain, which this
  document does not carry. J3 is therefore the least complete row in the file
  and the one to extend first.
  THE LOOM. Whether an escaped lead can then REACH the duct. Nothing models it.
  DEFLECTION. Every part here is rigid. A 125 mm upper arm on a 2:1 elbow is
  not, and the gaps this reports are the no-load ones.
  ASSEMBLY ORDER. This asks whether the assembled joint can MOVE, not whether
  it could be built in the first place - that is GATE leads' question.
  THE SOLID ITSELF, which is only as right as lib/servo.py, whose own
  docstring rates cheap-servo datasheet dimensions as weak.

Run in its own gate document. It clears root occurrences per station, so do
not run it into a document you wanted to keep.
"""

import io
import json
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

from lib.gears import J3_JOINT_TRAVEL_DEG  # noqa: E402
from lib.servo import CATALOG, MG995_TAB_HOLE_PITCH_Y, spline_z  # noqa: E402
from lib.servo_hub import spline_hub  # noqa: E402

# --- how hard we look ------------------------------------------------------
# STEP 1.0 rather than servo_fit's 1.5. This gate is hunting a SLIVER - a
# screw head grazing a swinging link - not a servo buried in a wall, and a
# 1.5 mm lattice steps straight over a 1.0 mm graze. The cost is 3.4x the
# points, paid only inside the bounding-box intersection, which for these
# pairs is a slab a few mm thick.
STEP = 1.0                  # sample pitch, mm
JAM_MM3 = 0.5               # below this is sampling noise, not a strike
SWEEP_STEPS = 9             # positions per joint, both limits included
CONTROL_OVERDRIVE_MM = 0.50  # how far PAST contact the control is driven
# A gap under this is reported TIGHT rather than clear. It is design_rules'
# `free` fit, 0.40: two printed parts nominally that far apart are touching
# once the printer has had its say, and a joint that scrubs is a joint that
# buzzes and browns out. Not a hard failure - a flag.
TIGHT_MM = 0.40

# --- the hardware servo_body.py does not model -----------------------------
# WHY THESE ARE RATIOS AND NOT A TABLE OF PART NUMBERS. Nobody has calipered
# the screws. What the project DOES already have is a house rule for the same
# quantity: lib/servo_hub.horn_bolt() sizes its head clearance as
# `horn_screw_dia * 2.0 + head_clear`, i.e. it takes a pan head to be twice
# the screw diameter, and lib/servo_hub.spline_hub()'s docstring says of the
# micro servos' Oe2.5 screw that its head is "around Oe5.0" - the same 2.0.
# Adopting that ratio here makes these numbers DERIVED from a datum the
# project already relies on rather than invented at this file's convenience.
# Grade them ASSUMED all the same and caliper before a part is cut to them;
# they are the least certain thing in this gate and they are load-bearing.
TAB_HEAD_D_FACTOR = 2.0     # ASSUMED - pan head diameter / screw diameter
TAB_HEAD_H_FACTOR = 0.70    # ASSUMED - pan head height / screw diameter
RETAIN_HEAD_D_FACTOR = 2.0  # ASSUMED - same rule, retaining screw
RETAIN_HEAD_H_FACTOR = 0.70  # ASSUMED - same rule, retaining screw
# ASSUMED. A DIN 125 washer in these sizes is 0.5 thick, but the washer that
# actually turns up in a servo bag is a thicker stamped one, and this number
# only ever pushes the retaining stack FURTHER into the swept volume - so the
# conservative value is the larger one and 0.8 is it.
WASHER_T_MM = 0.80

# The tab screw passes THROUGH the servo's own tab hole, so its nominal
# diameter is the largest metric size that will go through it. That makes the
# screw a consequence of lib/servo.py's tab_hole_dia rather than a choice made
# here: Oe2.1 -> M2 on both micros, Oe4.8 -> M4 on the MG995.
TAB_SCREW_NOMINAL_MM = (2.0, 2.5, 3.0, 4.0, 5.0)

# Full servo sweep. Every joint in this arm is driven by an unmodified hobby
# servo, and none of them has an electrical travel limit set - so 180 deg at
# the OUTPUT SHAFT is what the joint gets unless a reduction divides it
# (J3) or a mechanical stop caps it. Capping is not modelled here: sweeping
# the full 180 can only find MORE interference than the arm can reach, never
# less, and a clash just outside the stop is one bad calibration away.
SERVO_TRAVEL_DEG = 180.0

# Hosts that must be built before the one under test, from _build_parts.DEPS.
# These are interfaces that belong in lib/ - the list shrinking to empty is
# the goal, and this copy exists only because that move has not happened yet.
DEPS = {
    'j3_servo_cap': ['forearm'],
    'j3_gear': ['forearm'],
    'j3_pinion': ['forearm'],
    'upper_arm': ['forearm'],
    'j3_axle': ['forearm', 'upper_arm'],
    'gripcut_finger': ['pruner_blade'],
}

# One row per joint, keyed by the tag _check_leads.MOUNTS uses. The row says
# WHAT MOVES and HOW FAR; it does not say where the servo is - that is
# MOUNTS' job and it is imported.
#
#   moving      the part script for the half that swings past the servo
#   what        plain words, for the report
#   travel      total joint travel in degrees (or mm, for a prismatic row)
#   driven      the part bored onto the spline. Built for its PARAMETERS
#               ONLY and then deleted, exactly as _build_parts.py does with
#               its DEPS - a gate document holds the pair under test and not
#               a heap. Its seat and face are what put the retaining screw
#               and washer at the right height.
#   seat_p      document parameter holding that hub's seat above the tab plane
#   face_p      parameters that SUM to the hub's height above its own seat
#   access_p    the hub's washer ACCESS BORE, if it cuts one. This is the
#               difference between a retaining stack that is a hazard and one
#               that is not, and it is READ from the part rather than judged
#               here: a hub with an access bore takes the washer DOWN inside
#               itself onto the step at the top of the broach ("wh_access_d is
#               sized so the washer PASSES down to its seat") - the spline top
#               - so the screw finishes flush or below. A hub without one has
#               the washer bearing on its TOP FACE, standing the full washer
#               plus head PROUD of the driven part, in the open, exactly where
#               the other half of the joint goes past. j1_hub says so in as
#               many words: "There is deliberately NO washer recess in the top
#               face". Absent from the document = proud.
#   washer      whether the washer is still in the machine when it RUNS. The
#               one judgement in this table, and it is sourced rather than
#               made: at J1 both parts say the washer comes OUT. j1_hub.py
#               calls it an "ASSEMBLY AID ONLY: it and the retaining screw
#               pull the hub down WHILE the spline broaches", and
#               shoulder_bracket.py explains why - "the hub's top face IS the
#               face bolted to the rotor, so a washer there" cannot stay - and
#               then bores tt_screw_bore, Oe5.40, which passes the Oe5.00 screw
#               HEAD and will not pass a Oe6.25 washer. Modelling a washer
#               there would be a gate inventing a strike the machine does not
#               have, which is worse than missing one: it teaches you to
#               ignore the gate. Everywhere else the washer is load-bearing
#               and lib/servo_hub.py says it is not optional.
#   audit       (index, tokens that SUM to where the host actually BUILDS the
#               servo's tab plane, on that axis). A token starting with '-'
#               subtracts. The second control - see the docstring. Only the
#               four joints whose host states the stack-up in its own
#               parameters carry one; a row with audit=None is not a pass,
#               it is a question this gate cannot ask.
STATIONS = [
    dict(tag='J1 yaw', moving='shoulder_bracket',
         what='the whole turret, yawing on the printed hub',
         kind='revolute', travel=SERVO_TRAVEL_DEG,
         driven='j1_hub', seat_p='jh_seat_z', face_p=('jh_face',),
         access_p=None, washer=False,
         # turntable_stator.py builds the yaw deck by ONE subtraction it
         # spells out in a comment: race face, less the hub, less the hub's
         # seat. The tabs bear on that deck (its screw pilots start there),
         # so the deck IS the tab plane and the row's z should equal it.
         audit=(2, ('tt_race_z', '-tt_hub_h', '-tt_hub_seat_z'))),
    dict(tag='J2 shoulder', moving='upper_arm',
         what='the upper arm, pitching about J2',
         kind='revolute', travel=SERVO_TRAVEL_DEG,
         driven='shoulder_hub', seat_p='sh_seat_z', face_p=('sh_collar_l',), washer=True,
         access_p='sh_access_d',
         audit=(0, ('sb_plate_out', 'sb_lobe_t'))),
    dict(tag='J3 elbow', moving='j3_gear',
         what='the 36T output gear, turning about the elbow',
         # HALF the servo's, and it is imported rather than halved here.
         # lib/gears.py owns the reduction "and NOWHERE else"; a 2 typed
         # into this file is a second copy of the ratio waiting to go stale
         # the way the J3 MOUNTS row did for four commits.
         kind='revolute', travel=J3_JOINT_TRAVEL_DEG,
         driven='j3_pinion', seat_p='jp_seat_z', face_p=('jp_face',), washer=True,
         access_p=None,
         audit=(2, ('sc_t',))),
    dict(tag='J4 wrist', moving='wrist_roll',
         what='the roll housing, pitching about J4',
         kind='revolute', travel=SERVO_TRAVEL_DEG,
         driven='wrist_hub', seat_p='wh_seat_z', face_p=('wh_stack_h',), washer=True,
         access_p='wh_access_d',
         audit=(0, ('fa_plate_out', 'fa_j4_lobe_t'))),
    dict(tag='J5 roll', moving='wrist_rotator',
         what='the effector disc, rolling about J5',
         kind='revolute', travel=SERVO_TRAVEL_DEG,
         driven='wrist_rotator', seat_p='wrt_seat_z',
         face_p=('wrt_disc_t', 'wrt_hub_h'), access_p='wrt_access_d',
         washer=True,
         audit=None),
    dict(tag='gripper', moving='gripper_rack_jaw',
         what='the rack jaw, sliding across the pinion',
         kind='prismatic', travel=None,
         driven='gripper_pinion', seat_p='gp_seat_z', face_p=('gr_face',), washer=True,
         access_p=None,
         audit=None),
    dict(tag='effector', moving='pruner_rack',
         what='the pruner rack, sliding across the pinion',
         kind='prismatic', travel=None,
         driven='gripper_pinion', seat_p='gp_seat_z', face_p=('gr_face',), washer=True,
         access_p=None,
         audit=None),
]

ENV = 'robotarm_motor_furniture'
OUT_JSON = os.path.join(REPO, 'specs', 'robotarm', '_motor_clearance.json')


def _tab_screw_d(spec):
    """The screw through the tab, from the hole it passes through."""
    fits = [d for d in TAB_SCREW_NOMINAL_MM if d <= spec.tab_hole_dia]
    assert fits, (
        '%s: no metric screw passes a Oe%.2f tab hole - lib/servo.py'
        % (spec.name, spec.tab_hole_dia))
    return max(fits)


def _exec(name, repo):
    """Run a script into the active document.

    Nothing is caught. tests/test_fusion_scripts.py bans try/except in Fusion
    scripts - the traceback is the debugging signal - and a gate is the last
    place to bend it.
    """
    path = os.path.join(repo, 'models', 'robotarm', name + '.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    ns = {'__name__': name, '__file__': path}
    # ENCODING IS EXPLICIT AND THAT IS NOT PEDANTRY. Fusion's embedded Python
    # resolves open() to the ASCII codec and dies on the first Oe in a
    # docstring: "UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3".
    # 23 files in this repo carry Oe, em dashes or +/- signs, so this fails on
    # whichever file it reaches first and looks like a fault in that file
    # rather than in the reader.
    _src = io.open(path, encoding='utf-8').read()
    exec(compile(_src, path, 'exec'), ns)
    ns['run']('')


def _exec_servo(servo, repo):
    """Build the servo solid for a named servo.

    servo_body.py carries its subject as a module constant, so the SOURCE is
    substituted rather than the module poked: the names it derives at import
    time (COMPONENT, BODY_NAME) have to move with it.
    """
    path = os.path.join(repo, 'models', 'robotarm', 'servo_body.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    src = io.open(path, encoding='utf-8').read().replace(
        "SERVO = 'MG90S'", "SERVO = '%s'" % servo)
    ns = {'__name__': 'servo_body', '__file__': path}
    exec(compile(src, path, 'exec'), ns)
    ns['run']('')


def _furniture(comp, spec, hub_top_mm, washer):
    """Add the motor hardware servo_body.py does not model.

    BUILT INSIDE THE SERVO'S OWN COMPONENT, in the servo's own frame, so it
    inherits the servo occurrence's transform and cannot drift from the case
    by a single placement mistake. Everything here is coaxial with servo +Z
    or sits on the tab plane, so it is all axis-aligned in that frame and a
    circle on the component's XY plane is the whole of the geometry.

    Two bodies, named, so a report can say WHICH bit of hardware was struck:

      tab_screws_<servo>   the heads on the mounting tabs, standing proud of
                           the tab TOP. Not the tab underside: every mount in
                           this arm recesses the flange tab_thk deep so the
                           tab finishes flush with the pad, which leaves the
                           head as the highest thing on the flange.
      retain_<servo>       the retaining screw head and its washer, on top of
                           whatever the spline drives. Modelled as one
                           cylinder at the larger of the two diameters
                           because that is the silhouette a swinging part
                           meets; separating them would buy nothing a sweep
                           can see.

    The LEAD BUNDLE is deliberately NOT built here - servo_body.py's PHASE
    lead already joins it into the case body, so it arrives as part of
    servo_<name> and is swept with it. The caller asserts that.
    """
    P3 = adsk.core.Point3D.create
    V = adsk.core.ValueInput.createByString
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures
    xy = comp.xYConstructionPlane
    t0 = comp.parentDesign.timeline.count

    def column(sk_name, centres, dia, z0, dz, body_name):
        sk = sketches.add(xy)
        sk.name = sk_name
        for cx, cy in centres:
            sk.sketchCurves.sketchCircles.addByCenterRadius(
                P3(cx / 10.0, cy / 10.0, 0), dia / 2.0 / 10.0)
        assert sk.profiles.count == len(centres), (
            '%s: %d profiles for %d circles - two heads overlap, which means '
            'the pitch or the head diameter is wrong'
            % (sk_name, sk.profiles.count, len(centres)))
        made = None
        for i in range(sk.profiles.count):
            inp = extrudes.createInput(sk.profiles.item(i), NEW if i == 0 else JOIN)
            if i:
                inp.participantBodies = [made]
            inp.setOneSideExtent(
                adsk.fusion.DistanceExtentDefinition.create(V('%.5f mm' % dz)),
                adsk.fusion.ExtentDirections.PositiveExtentDirection)
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
                V('%.5f mm' % z0))
            e = extrudes.add(inp)
            e.name = body_name + '_%d' % i
            if i == 0:
                made = e.bodies.item(0)
                made.name = body_name
        return made

    # ---- the tab screw heads ---------------------------------------------
    screw_d = _tab_screw_d(spec)
    head_d = screw_d * TAB_HEAD_D_FACTOR
    head_h = screw_d * TAB_HEAD_H_FACTOR
    near = -spec.shaft_from_end
    x_mid = near + spec.case_l / 2.0
    # The MG995 has FOUR tab holes on two rows; the micros have two, on the
    # centreline. lib/servo.py owns that split (MG995_TAB_HOLE_PITCH_Y) and
    # servo_body.py already reads it the same way, so the two agree by
    # construction rather than by both being typed the same.
    micro = spec.name in ('SG90', 'MG90S')
    ys = [0.0] if micro else [-MG995_TAB_HOLE_PITCH_Y / 2.0,
                              MG995_TAB_HOLE_PITCH_Y / 2.0]
    centres = [(x_mid + sx * spec.tab_hole_pitch / 2.0, y)
               for sx in (-1, 1) for y in ys]
    heads = column('sk_tab_heads', centres, head_d,
                   spec.tab_thk, head_h, 'tab_screws_' + spec.name)

    # ---- the retaining screw and its washer -------------------------------
    hub = _hub_of(spec)
    r_head_d = spec.horn_screw_dia * RETAIN_HEAD_D_FACTOR
    r_head_h = spec.horn_screw_dia * RETAIN_HEAD_H_FACTOR
    # A washer that is removed before the machine runs is not an obstacle,
    # and modelling it as one would invent a strike. See the `washer` key.
    stack_d = max(hub.washer_d, r_head_d) if washer else r_head_d
    stack_h = (WASHER_T_MM + r_head_h) if washer else r_head_h
    retain = column('sk_retain', [(0.0, 0.0)], stack_d,
                    hub_top_mm, stack_h, 'retain_' + spec.name)

    if comp.parentDesign.timeline.count - t0 > 1:
        g = comp.parentDesign.timeline.timelineGroups.add(
            t0, comp.parentDesign.timeline.count - 1)
        g.name = 'motor furniture'
    return heads, retain, dict(
        tab_screw='M%g' % screw_d, tab_head_d=head_d, tab_head_h=head_h,
        washer_d=hub.washer_d, retain_head_d=r_head_d,
        washer_fitted=washer, retain_stack_d=stack_d, hub_top=hub_top_mm,
        retain_top=hub_top_mm + stack_h)


def _hub_of(spec):
    """The spline hub solved for this servo, for its WASHER DIAMETER.

    washer_d is broach_d + a fixed extra in lib/servo_hub.spline_hub(), so it
    does not depend on the hub's face at all - but spline_hub() still asserts
    that the face it is handed reaches the spline, and it is right to. So the
    face passed here is the one face every servo is guaranteed to admit: case
    top to spline top, the full height the output actually offers. Deriving
    the face from a hub_top read out of the document instead would let a
    missing parameter turn a clearance question into an assertion failure
    three functions away from the thing that was actually wrong.
    """
    return spline_hub(spec, face=spline_z(spec)[1] - spec.tab_below_top
                      - spec.tab_thk)


def _overlap_mm3(probe, others):
    """Sampled volume the probe shares with any of `others`, in mm3.

    ONLY THE OVERLAP REGION IS SAMPLED, and that is not an optimisation, it
    is the difference between a gate that finishes and one that does not.
    _check_servo_fit's first version walked the probe's whole bounding box,
    testing tens of thousands of points nowhere near the other body, and
    never returned. An interference can only exist where both bounding boxes
    are, so that intersection is the only place worth asking about.

    pointContainment ONLY. TemporaryBRepManager.booleanOperation returns
    empty in this codebase and reads as "no interference".
    """
    INSIDE = adsk.fusion.PointContainment.PointInsidePointContainment
    P3 = adsk.core.Point3D.create
    pb = probe.boundingBox
    step = STEP / 10.0
    hits, where = 0, []
    for h in others:
        hb = h.boundingBox
        lo = [max(pb.minPoint.x, hb.minPoint.x),
              max(pb.minPoint.y, hb.minPoint.y),
              max(pb.minPoint.z, hb.minPoint.z)]
        hi = [min(pb.maxPoint.x, hb.maxPoint.x),
              min(pb.maxPoint.y, hb.maxPoint.y),
              min(pb.maxPoint.z, hb.maxPoint.z)]
        if any(lo[i] > hi[i] for i in range(3)):
            continue            # the boxes miss - nothing to test
        x = lo[0]
        while x <= hi[0]:
            y = lo[1]
            while y <= hi[1]:
                z = lo[2]
                while z <= hi[2]:
                    p = P3(x, y, z)
                    if (h.pointContainment(p) == INSIDE
                            and probe.pointContainment(p) == INSIDE):
                        hits += 1
                        where.append((x * 10.0, y * 10.0, z * 10.0))
                    z += step
                y += step
            x += step
    return hits * (STEP ** 3), where


def _span(pts):
    """Bounding box of the interfering points, in HOST mm - WHICH FEATURE.

    A volume tells you a joint does not turn. It does not tell you what it
    hit, and "does not turn" is not actionable. This is.
    """
    if not pts:
        return None
    return [round(min(p[i] for p in pts), 2) for i in range(3)] + \
           [round(max(p[i] for p in pts), 2) for i in range(3)]


def _dump(rows, meta):
    """Persist what has been measured SO FAR, after every joint.

    Not at the end. The MCP call that runs a gate dies at 60 s, and
    _check_servo_fit lost a complete seven-station run to exactly that even
    though it had finished the work. A result you cannot read is not a result.
    """
    payload = dict(meta)
    payload['stations'] = rows
    with io.open(OUT_JSON, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(payload, indent=2, sort_keys=True))


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    mm = app.measureManager
    M3 = adsk.core.Matrix3D.create
    P3 = adsk.core.Point3D.create
    VEC = adsk.core.Vector3D.create
    ORG = adsk.core.Point3D.create(0, 0, 0)
    repo = REPO

    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    from models.robotarm import _check_leads  # noqa
    mounts = {m['tag']: m for m in _check_leads.MOUNTS}

    # THE FRAME MATH IS _check_leads', NOT A SECOND COPY. That file owns the
    # convention - servo +y is COMPUTED as za x xa, so a row cannot describe a
    # left-handed servo - and a hand-rolled copy here could quietly disagree
    # with it. Underscore names crossing a module boundary is the smaller sin.
    _unit = _check_leads._unit
    _frame = _check_leads._frame

    def gv(name):
        """A document user parameter, in MM. Fusion answers in centimetres and
        every dimension in this file is millimetres, so the conversion happens
        once, here, rather than at forty call sites."""
        p = ups.itemByName(name)
        assert p is not None, 'missing user parameter ' + name
        return p.value * 10.0

    def has(name):
        return ups.itemByName(name) is not None

    def mul(a, b):
        """a * b, i.e. "b expressed in a's frame". Fusion's
        x.transformBy(y) means x := y * x, which is the opposite of how it
        reads; this wrapper is the only composition this file does."""
        m = b.copy()
        m.transformBy(a)
        return m

    def rot(deg, axis, origin=ORG):
        m = M3()
        m.setToRotation(math.radians(deg), axis, origin)
        return m

    def trans(x, y, z):
        m = M3()
        t = m.translation
        t.x, t.y, t.z = x / 10.0, y / 10.0, z / 10.0
        m.translation = t
        return m

    def frame(origin, ax, ay, az):
        m = M3()
        m.setWithCoordinateSystem(P3(origin[0] / 10.0, origin[1] / 10.0,
                                     origin[2] / 10.0),
                                  VEC(*ax), VEC(*ay), VEC(*az))
        return m

    # ---- where the moving half sits at travel zero, and what it turns about -
    # Every pose below is VERBATIM from _preview_arm.py, which owns every joint
    # transform in this project, re-expressed in the HOST's frame instead of
    # the world's. Nothing is re-derived: a joint transform invented here would
    # be a second opinion about the arm's kinematics, and this project has
    # already been bitten once by a J3 row that described a mount that had
    # moved. Each returns (home matrix, axis point mm, axis direction).
    def pose_j1():
        # _preview_arm: B = yaw * trans(0, 0, tt_race_z - bracket bbox floor).
        # The bracket's race face is its own bbox floor and it lands on the
        # rollers at tt_race_z - taken from the BODY rather than recomputed, so
        # this cannot disagree with the part about where the arm sits.
        b = _body_of_part('shoulder_bracket').boundingBox
        return (trans(0.0, 0.0, gv('tt_race_z') - b.minPoint.z * 10.0),
                (0.0, 0.0, 0.0), VEC(0, 0, 1))

    def pose_j2():
        # upper_arm is drawn with its origin on J3 and J2 at y = -ua_l1, so in
        # the bracket's frame it hangs one link length out along +Y and pitches
        # about the bracket's X.
        return trans(0.0, gv('ua_l1'), 0.0), (0.0, 0.0, 0.0), VEC(1, 0, 0)

    def pose_j3():
        # The only offset drive in the arm: the servo is on the PINION axis and
        # the joint is one centre distance away on the GEAR axis. Both frames
        # are built in the FOREARM's coordinates exactly as _preview_arm does,
        # then the cap's is inverted to land in the host's.
        po, fr, so_ = gv('fa_plate_out'), gv('fa_free'), gv('fa_j3_standoff')
        l2, centre = gv('fa_l2'), gv('fa_j3_centre')
        y_pin = -l2 + centre
        m_gear = frame((-(po + fr), -l2, 0.0), (0, 0, 1), (0, 1, 0), (-1, 0, 0))
        m_cap = frame((-(po + so_), y_pin, 0.0), (0, 1, 0), (0, 0, -1), (-1, 0, 0))
        inv = m_cap.copy()
        assert inv.invert(), 'the J3 cap frame is singular - a row is malformed'
        home = mul(inv, m_gear)
        cs = home.getAsCoordinateSystem()
        # The gear's own +Z IS the elbow axis - that is what a spur pair on
        # parallel shafts means - so the axis comes out of the pose rather
        # than being typed beside it and able to disagree with it.
        return home, (cs[0].x * 10.0, cs[0].y * 10.0, cs[0].z * 10.0), cs[3]

    def pose_j4():
        # wrist_roll shares the forearm's frame exactly - that is what the
        # shared wr_ block buys - so at pitch 0 it is the identity.
        return M3(), (0.0, 0.0, 0.0), VEC(1, 0, 0)

    def pose_j5():
        # Verbatim from _check_wrist.place_rotator, which _preview_arm also
        # copies: R_x(-90) takes the disc's +Z onto the roll housing's +Y, and
        # the disc sits at the housing's front face.
        home = mul(rot(-90.0, VEC(1, 0, 0)), M3())
        t = home.translation
        t.y = gv('wro_y_front') / 10.0
        home.translation = t
        return home, (0.0, 0.0, 0.0), VEC(0, 1, 0)

    def pose_rack():
        # Verbatim from _check_pruner.rack_at(s, turned=False): the rack sits
        # gr_offset off the centre plane and slides along the shell's X. Both
        # hands share the gr_ block, which is why one pose serves both rows.
        return trans(0.0, 0.0, gv('gr_offset')), (0.0, 0.0, 0.0), VEC(1, 0, 0)

    POSE = {'J1 yaw': pose_j1, 'J2 shoulder': pose_j2, 'J3 elbow': pose_j3,
            'J4 wrist': pose_j4, 'J5 roll': pose_j5,
            'gripper': pose_rack, 'effector': pose_rack}

    def _body_of_part(part):
        for occ in root.occurrences:
            if occ.component.name == 'robotarm_' + part:
                return occ.component.bRepBodies.item(0)
        assert False, 'robotarm_%s is not in the document' % part

    def _place_servo(occ, mount):
        """Put the servo occurrence into the host frame, from MOUNTS."""
        xa, ya, za = _frame(mount)
        sx, sy, sz = mount['shaft']
        m = M3()
        m.setWithArray([xa[0], ya[0], za[0], sx / 10.0,
                        xa[1], ya[1], za[1], sy / 10.0,
                        xa[2], ya[2], za[2], sz / 10.0,
                        0.0, 0.0, 0.0, 1.0])
        occ.transform2 = m
        return m

    def bodies(occ):
        return [occ.bRepBodies.item(i) for i in range(occ.bRepBodies.count)]

    def gap_mm(a, b):
        """Exact minimum distance and the two witness points, in mm.

        This is what the sampler cannot do. A 0.30 mm graze is invisible at a
        1.00 mm lattice and is the whole complaint.
        """
        r = mm.measureMinimumDistance(a, b)
        return r.value * 10.0, r.positionOne, r.positionTwo

    def centre_of(bs):
        lo = [1e18, 1e18, 1e18]
        hi = [-1e18, -1e18, -1e18]
        for b in bs:
            bb = b.boundingBox
            for i, (p_lo, p_hi) in enumerate(
                    ((bb.minPoint.x, bb.maxPoint.x), (bb.minPoint.y, bb.maxPoint.y),
                     (bb.minPoint.z, bb.maxPoint.z))):
                lo[i] = min(lo[i], p_lo)
                hi[i] = max(hi[i], p_hi)
        return [(lo[i] + hi[i]) / 2.0 for i in range(3)]

    print('GATE motor_clearance - the moving half of each joint against the')
    print('MOTOR HARDWARE, swept through travel. Placement imported from')
    print('_check_leads.MOUNTS; joint transforms from _preview_arm.py.')
    print('sample %.2f mm | strike floor %.2f mm3 | tight under %.2f mm | %d '
          'positions per joint' % (STEP, JAM_MM3, TIGHT_MM, SWEEP_STEPS))
    print('')

    meta = dict(step_mm=STEP, jam_floor_mm3=JAM_MM3, tight_mm=TIGHT_MM,
                sweep_steps=SWEEP_STEPS,
                control_overdrive_mm=CONTROL_OVERDRIVE_MM,
                tab_head_d_factor=TAB_HEAD_D_FACTOR,
                tab_head_h_factor=TAB_HEAD_H_FACTOR,
                retain_head_d_factor=RETAIN_HEAD_D_FACTOR,
                washer_t_mm=WASHER_T_MM,
                j3_joint_travel_deg=J3_JOINT_TRAVEL_DEG,
                grade='tab and retaining screw heads are ASSUMED - caliper '
                      'before cutting a part to them')
    rows, fails, blind, notes = [], [], [], []

    for st in STATIONS:
        tag = st['tag']
        mount = mounts[tag]
        host, servo_name = mount['host'], mount['servo']
        spec = CATALOG[servo_name]

        for occ in list(root.occurrences):
            occ.deleteMe()
        built = []
        for part in (DEPS.get(host, []) + [host]
                     + DEPS.get(st['moving'], []) + [st['moving']]
                     + DEPS.get(st['driven'], []) + [st['driven']]):
            if part not in built:
                _exec(part, repo)
                built.append(part)
        _exec_servo(servo_name, repo)

        # THE DRIVEN HUB WAS BUILT FOR ITS PARAMETERS AND ITS BODIES GO. It
        # rides on the spline, so relative to the moving half it is part of
        # the motor - but at J3 it is the PINION, and pinion-against-gear is
        # the tooth mesh, which would read as a strike at every step. What is
        # wanted from it is only where its top face is, and user parameters
        # survive the deletion. _build_parts.py deletes its DEPS' bodies for
        # the same reason: a document holds the thing under test, not a heap.
        if st['driven'] != st['moving'] and st['driven'] != host:
            for occ in list(root.occurrences):
                if occ.component.name == 'robotarm_' + st['driven']:
                    occ.deleteMe()

        host_occ = moving_occ = servo_occ = None
        for occ in root.occurrences:
            n = occ.component.name
            if n == 'robotarm_' + host:
                host_occ = occ
            elif n == 'robotarm_' + st['moving']:
                moving_occ = occ
            elif n == 'robotarm_servo_' + servo_name:
                servo_occ = occ
        assert host_occ is not None, 'no host occurrence for ' + host
        assert moving_occ is not None, 'no moving occurrence for ' + st['moving']
        assert servo_occ is not None, 'no servo occurrence for ' + servo_name

        # ---- where the retaining stack sits ------------------------------
        # From the DRIVEN PART'S OWN parameters where it declares them, so the
        # washer lands on the face it actually bears on. The fallback is the
        # spline top, and the row says which was used - a retaining stack put
        # LOW is not conservative (a moving part that clears it low can still
        # strike it high), so a fallback row is a weaker result, not a safe
        # one, and it is labelled as such rather than averaged in silently.
        recessed = st['access_p'] is not None and has(st['access_p'])
        if recessed:
            # The washer goes DOWN the access bore and bears on the step at
            # the top of the broach, which is the SPLINE TOP - the one datum
            # lib/servo.py owns for every servo. The stack finishes inside
            # the hub and the swept volume never sees it.
            hub_top = spline_z(spec)[1]
            hub_basis = 'recessed in %s (%s)' % (st['driven'], st['access_p'])
        elif has(st['seat_p']) and all(has(p) for p in st['face_p']):
            # No access bore, so the washer bears on the hub's TOP FACE and
            # the whole stack stands proud of the driven part, in the open.
            hub_top = gv(st['seat_p']) + sum(gv(p) for p in st['face_p'])
            hub_basis = 'PROUD of %s top face' % st['driven']
        else:
            # Neither could be established. A retaining stack placed LOW is
            # not conservative - a moving part that clears it low can still
            # strike it high - so this row is a WEAKER result, not a safe
            # one, and it is named rather than averaged in silently.
            hub_top = spline_z(spec)[1]
            hub_basis = 'spline top (FALLBACK - %s declares neither %s nor %s)' % (
                st['driven'], st['access_p'] or 'an access bore',
                '/'.join((st['seat_p'],) + st['face_p']))
            notes.append('%s: retaining stack placed on the %s' % (tag, hub_basis))

        heads, retain, furn = _furniture(servo_occ.component, spec, hub_top,
                                        st['washer'])
        _place_servo(servo_occ, mount)

        # THE LEAD IS ALREADY IN THE CASE BODY - servo_body.py's PHASE lead
        # joins it - and this asserts that rather than trusting it, because a
        # lead silently missing from the probe is a lead this gate says is fine.
        case = servo_occ.component.bRepBodies.itemByName('servo_' + servo_name)
        assert case is not None, 'servo_body.py built no servo_%s' % servo_name
        cb = case.boundingBox
        reach = max(abs(cb.minPoint.x), abs(cb.maxPoint.x),
                    abs(cb.minPoint.y), abs(cb.maxPoint.y),
                    abs(cb.minPoint.z), abs(cb.maxPoint.z)) * 10.0
        need = abs(spec.lead_x) + spec.lead_bundle_dia
        assert reach >= need - STEP, (
            '%s: the case body reaches only %.2f mm from the shaft but the '
            'lead bundle leaves at %.2f and runs on - servo_body.py\'s lead '
            'phase did not land, and this gate would sweep a servo with no '
            'cable on it' % (tag, reach, need))

        # The motor side: the case (with its lead), the tab screw heads and
        # the retaining stack. Everything that is NOT printed and NOT moving.
        motor = [b for b in bodies(servo_occ)
                 if b.name.startswith(('servo_', 'tab_screws_', 'retain_'))]
        assert len(motor) == 3, (
            '%s: %d motor bodies, wanted case + tab screws + retaining stack'
            % (tag, len(motor)))

        home, axis_pt, axis_dir = POSE[tag]()
        axis_org = P3(axis_pt[0] / 10.0, axis_pt[1] / 10.0, axis_pt[2] / 10.0)

        def at(u):
            """The moving part at travel u - degrees for a revolute joint,
            millimetres for a prismatic one."""
            if st['kind'] == 'revolute':
                return mul(rot(u, axis_dir, axis_org), home)
            return mul(trans(axis_dir.x * u, axis_dir.y * u, axis_dir.z * u),
                       home)

        # ---- travel ------------------------------------------------------
        if st['kind'] == 'revolute':
            lo, hi = -st['travel'] / 2.0, st['travel'] / 2.0
            unit = 'deg'
        else:
            lo, hi = 0.0, gv('gr_stroke')
            unit = 'mm'

        # ---- the FRAME self-check, before any result is believed ----------
        # At travel zero the two halves are mating parts on running fits, so
        # the moving half must not be INSIDE the host. A large number here
        # means this station's POSE is wrong - a rotation or an origin - not
        # that the part is, and every clearance below it would be measured
        # from the wrong place. The same self-check _check_leads calls SEATED.
        moving_occ.transform2 = at(0.0)
        host_b = bodies(host_occ)
        seat_v = 0.0
        for b in bodies(moving_occ):
            v, _w = _overlap_mm3(b, host_b)
            seat_v += v
        framed = seat_v <= JAM_MM3

        # ---- the sweep ----------------------------------------------------
        worst_gap, worst_at, worst_what = 1e18, None, ''
        total_hit, hit_at, hit_span = 0.0, None, None
        samples = []
        for i in range(SWEEP_STEPS):
            u = lo + (hi - lo) * i / (SWEEP_STEPS - 1.0)
            moving_occ.transform2 = at(u)
            mv = bodies(moving_occ)
            step_v, step_where, step_gap, step_what = 0.0, [], 1e18, ''
            for a in mv:
                for b in motor:
                    v, w = _overlap_mm3(a, b)
                    step_v += v
                    step_where.extend(w)
                    g, _p1, _p2 = gap_mm(a, b)
                    if g < step_gap:
                        step_gap, step_what = g, b.name
            samples.append(dict(at=round(u, 2), unit=unit,
                                hit_mm3=round(step_v, 2),
                                gap_mm=round(step_gap, 3), nearest=step_what))
            if step_gap < worst_gap:
                worst_gap, worst_at, worst_what = step_gap, u, step_what
            if step_v > total_hit:
                total_hit, hit_at, hit_span = step_v, u, _span(step_where)

        # ---- THE POSITIVE CONTROL ------------------------------------------
        # No direction is chosen here; one is MEASURED. See the module
        # docstring - this is the half of the file that decides whether any
        # number above means anything.
        moving_occ.transform2 = at(worst_at)
        mv = bodies(moving_occ)
        best = None
        for a in mv:
            for b in motor:
                g, p1, p2 = gap_mm(a, b)
                if best is None or g < best[0]:
                    best = (g, p1, p2, a, b)
        g0, p1, p2, ca, cb2 = best
        d = [(p2.x - p1.x) * 10.0, (p2.y - p1.y) * 10.0, (p2.z - p1.z) * 10.0]
        norm = math.sqrt(sum(c * c for c in d))
        if norm < 1e-9:
            # Already touching at the worst step. Any push at all deepens it,
            # so close on the motor's centre - still a measured direction.
            mc, ac = centre_of(motor), centre_of(mv)
            d = [(mc[i] - ac[i]) * 10.0 for i in range(3)]
            norm = math.sqrt(sum(c * c for c in d))
        assert norm > 1e-9, (
            '%s: the moving part and the motor share a centre - no closing '
            'direction exists and the control cannot be aimed' % tag)
        u_hat = [c / norm for c in d]
        shift = g0 + CONTROL_OVERDRIVE_MM

        # (a) THINGS MOVE TOGETHER. The one check _check_servo_fit's first
        # control did not have: the closing vector must actually point at the
        # motor. A backwards control fails HERE, before it can report a
        # comfortable zero.
        mc, ac = centre_of(motor), centre_of(mv)
        toward = sum(u_hat[i] * (mc[i] - ac[i]) for i in range(3))
        assert toward > 0.0, (
            '%s: THE CONTROL IS BACKWARDS - it would move the part AWAY from '
            'the motor (%.4f). Every clear result at this station is '
            'meaningless.' % (tag, toward))

        moving_occ.transform2 = mul(
            trans(u_hat[0] * shift, u_hat[1] * shift, u_hat[2] * shift),
            at(worst_at))
        mv = bodies(moving_occ)
        ctrl_v = 0.0
        for a in mv:
            for b in motor:
                v, _w = _overlap_mm3(a, b)
                ctrl_v += v
        # (b) they are TOUCHING after the shift, by measurement not by faith
        ctrl_gap = min(gap_mm(a, b)[0] for a in mv for b in motor)
        moving_occ.transform2 = at(0.0)

        if ctrl_v <= JAM_MM3 or ctrl_gap > CONTROL_OVERDRIVE_MM:
            blind.append('%s (%.2f mm3, gap %.3f after a %.2f mm close)'
                         % (tag, ctrl_v, ctrl_gap, shift))

        # ---- the placement audit, the SECOND control ----------------------
        audit = None
        if st['audit'] is not None:
            idx, parts = st['audit']
            names = [p.lstrip('-') for p in parts]
            if all(has(n) for n in names):
                want = sum((-1.0 if p.startswith('-') else 1.0) * gv(p.lstrip('-'))
                           for p in parts)
                audit = dict(axis='xyz'[idx], table=mount['shaft'][idx],
                             part=round(want, 3),
                             delta=round(mount['shaft'][idx] - want, 3),
                             parts='+'.join(parts))
            else:
                notes.append('%s: placement audit skipped, %s not in this '
                             'document' % (tag, '/'.join(names)))

        row = dict(tag=tag, host=host, servo=servo_name, moving=st['moving'],
                   what=st['what'], kind=st['kind'],
                   travel=[round(lo, 2), round(hi, 2)], travel_unit=unit,
                   frame_seated_mm3=round(seat_v, 2), frame_ok=framed,
                   min_gap_mm=round(worst_gap, 3),
                   min_gap_at=round(worst_at, 2), min_gap_against=worst_what,
                   worst_hit_mm3=round(total_hit, 2),
                   worst_hit_at=(round(hit_at, 2) if hit_at is not None else None),
                   worst_hit_span=hit_span,
                   control_mm3=round(ctrl_v, 2), control_shift_mm=round(shift, 3),
                   control_gap_mm=round(ctrl_gap, 3),
                   retain_basis=hub_basis, furniture=furn,
                   audit=audit, samples=samples)
        rows.append(row)

        if not framed:
            fails.append('%s: FRAME WRONG - the moving half overlaps the HOST '
                         'by %.1f mm3 at travel zero. This station measured '
                         'nothing.' % (tag, seat_v))
        elif total_hit > JAM_MM3:
            fails.append('%s: STRIKES the %s - %.1f mm3 at %.1f %s'
                         % (tag, worst_what, total_hit, hit_at, unit))
        elif worst_gap < TIGHT_MM:
            fails.append('%s: TIGHT - %.2f mm to the %s at %.1f %s (free fit '
                         'is %.2f)' % (tag, worst_gap, worst_what, worst_at,
                                       unit, TIGHT_MM))

        print('%-12s %-16s vs %-18s %6.2f %-3s..%6.2f  gap %6.2f mm to %-22s '
              'hit %8.1f mm3  control %8.1f mm3'
              % (tag, host, st['moving'], lo, unit, hi, worst_gap, worst_what,
                 total_hit, ctrl_v))
        _dump(rows, meta)

    # ---- what the run is worth, before what it found ----------------------
    print('')
    assert not blind, (
        'THE CHECK IS BLIND at %s - the moving part was closed onto the motor '
        'past contact and registered nothing. Every clear result above is '
        'meaningless until this is fixed.' % ', '.join(blind))
    print('positive control fired at all %d stations: each moving part was '
          'driven along its own MEASURED closing vector, past contact, and '
          'the sampler saw it. The check can see.' % len(rows))

    j2 = [r for r in rows if r['tag'] == 'J2 shoulder' and r['audit']]
    if j2:
        d = j2[0]['audit']['delta']
        print('')
        print('PLACEMENT AUDIT CONTROL: shoulder_bracket.py states in its own')
        print('  docstring that its MOUNTS row is right and is not to be')
        print('  touched, so J2 must read 0.00. It reads %.2f - %s' % (
            d, 'the audit is sound' if abs(d) < 1e-6
            else 'THE AUDIT IS WRONG, ignore every delta it prints'))
    audits = [r for r in rows if r['audit'] and abs(r['audit']['delta']) > 1e-6]
    if audits:
        print('')
        print('THE PLACEMENT TABLE DISAGREES WITH THE PARTS:')
        for r in audits:
            a = r['audit']
            print('  %-12s MOUNTS shaft.%s = %.2f, but %s builds %s = %.2f '
                  '- %+.2f mm' % (r['tag'], a['axis'], a['table'], r['host'],
                                  a['parts'], a['part'], a['delta']))
        print('  Every gate that imports MOUNTS - leads, servo_fit and this')
        print('  one - places that servo by the wrong number, and a sliver')
        print('  thinner than a sample pitch is exactly what a sampled gate')
        print('  reports as 0.00 mm3.')

    print('')
    if notes:
        print('WEAKER THAN THE REST, and named rather than averaged in:')
        for n in notes:
            print('  %s' % n)
        print('')
    print('GATE motor_clearance : %s' % ('PASS' if not fails else 'FAIL'))
    for f in fails:
        print('   %s' % f)
    print('')
    print('wrote %s' % OUT_JSON)
    print('READ THIS BEFORE BELIEVING A CLEAR RESULT. The tab and retaining')
    print('screw heads are ASSUMED, at twice the screw diameter - the ratio')
    print('lib/servo_hub.py already uses, not a caliper. The servo solid is')
    print('only as right as lib/servo.py, whose own docstring rates cheap-')
    print('servo datasheet dimensions as weak. A clear result means the')
    print('project no longer disagrees with ITSELF about its own motors.')
    print('It is not the bench, and the bench is what raised this.')
