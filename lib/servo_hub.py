"""Bolting a printed gear to a hobby servo — the interface, and what it costs.

WHY THIS FILE EXISTS. lib/gears.py mounts the J3 pinion by PRESSING its bore
onto the horn's hub and KEYING its torque through a cross slot cut to the
horn's arm width. Both of those numbers are the horn's, and the horn is the
one part of this machine nobody can pin down: deshipu's teardown and Roger
Cheng's survey both say micro horn dimensions vary by batch, and Jonathan's
bench has now said three times that the horns do not enter the slots cut for
them ("the actual horn tips dont fit in anywhere", 2026-08-31).

A slot cut to a dimension that varies by batch is not a fit, it is a bet.

WHAT REPLACES IT. Screws through RADIAL SLOTS into the horn's own holes.
  - The horn's HOLES are the one feature on it that is dimensionally
    dependable, because the servo ships the screws that go in them.
  - A RADIAL slot does not care what radius the hole is at. It spans the
    range the hole could be in and catches it wherever it lands. This is the
    same move MG995_TAB_SLOT_X_MM already makes in lib/servo.py for the
    MG995's disputed tab pitch - the precedent is the project's own.
  - Radial is also the load-correct orientation: torque is TANGENTIAL, so it
    bears on the slot's long side wall, not on its ends.
  - Nothing presses on anything. There is no bore on the hub and no slot on
    the arms. The horn's outline stops being a dimension this project holds.

WHY IT MUST BE TWO PIECES, AND THIS IS THE ARITHMETIC THAT DECIDES IT.
A bolt slot needs to reach the horn's innermost hole (r ~6.5 measured) and
needs a wall between it and the tooth roots. That puts the tooth root at
  r_root >= 6.5 + bolt_clearance/2 + MIN_WALL
which for an M2 screw is 6.5 + 1.2 + 1.6 = 9.3 mm. The J3 pinion today is
18T at module 1.00: r_root 8.00. It is 1.3 mm too small to be bolted, and no
amount of care makes a 2.4 mm slot fit in 8.0 mm of radius next to a tooth.

THAT IS THE WHOLE REASON THE GEARS HAVE TO GET BIGGER. Not preference -
the bolt circle sets a floor under the pinion, and the pinion sets the pair.

Jonathan, 2026-08-31, on what else is wrong: "there is so much weight just on
the servos because there is no adaptors". He is right and it is the second
job of this file. A gear pressed on a horn hangs its entire radial load on
the servo's output spline - a 4.9 mm plastic-geared shaft in a 9 g case,
cantilevered. goBILDA sell a machined part (the ServoBlock) whose only
purpose is to take that load off the spline, which tells you the load is
real. `journal_d` below is a printed boss on the adapter's far face that runs
in a bearing carried by the HOST, so the radial component goes into the host
and the spline sees torque alone.

Nothing here touches Fusion.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from lib.design_rules import (
    FASTENER_MM,
    GEAR_MIN_MODULE_MM,
    JOINT_FIT_MM,
    MIN_WALL_MM,
)
from lib.servo import CATALOG, micro_arm_w

# --- what the horn's holes actually are ----------------------------------
# lib/servo.py: horn_hole_dia 1.4 at horn_hole_pitch 2.0, running out each
# arm to horn_arm_len. The INNERMOST hole is not stated anywhere and is the
# number the slot's inner end has to reach, so it is declared here as the
# conservative end of what the bench saw, and the slot spans well past it in
# BOTH directions rather than trusting it.
MICRO_HORN_FIRST_HOLE_R = 6.0    # MEASURED-ish, 2026-08-28 arm comb
MICRO_HORN_LAST_HOLE_R = 17.0    # = horn_arm_len
MG995_HORN_FIRST_HOLE_R = 8.0
MG995_HORN_LAST_HOLE_R = 16.5

# The screw that goes in them is the servo's own bagged self-tapper. It is
# an M2-class thread; the printed part gets a CLEARANCE hole and the horn
# gets the thread, which is what those holes are for.
HORN_SCREW = 'M2'

# How far past the first/last hole the slot runs, so that a horn whose holes
# sit somewhere else still lands one inside the slot. This is the whole
# robustness margin and it is cheap - it costs slot length, nothing else.
SLOT_OVERRUN_MM = 1.5


@dataclass(frozen=True)
class HornBolt:
    """A bolted horn interface, in the SERVO's frame (lib/servo.py)."""

    servo_name: str
    seat_z: float          # servo-z of the adapter's underside
    bore_d: float          # central through bore - clears hub AND screw head
    slot_w: float          # radial slot width
    slot_r_in: float       # slot inner end, radius
    slot_r_out: float      # slot outer end, radius
    slot_count: int
    slot_angles_deg: tuple  # where they are, about the shaft
    min_root_r: float      # the floor this puts under any gear cut into it
    holes_caught: int      # how many horn holes the slot spans, worst case

    @property
    def slot_len(self) -> float:
        return self.slot_r_out - self.slot_r_in


def horn_bolt(servo, screw=HORN_SCREW, overrun=SLOT_OVERRUN_MM,
              slot_angles_deg=(0.0, 180.0), head_clear=2.2):
    """Solve the bolted interface for a servo's stock horn.

    TWO slots by default, on the horn's LONG axis. lib/servo.py records the
    micro cross horn as 34.4 long x 17.0 short - it is NOT a symmetric cross,
    so the two short arms reach only r ~8.5 and cannot carry a useful slot.
    Two screws at opposite radii are a couple; they take torque perfectly
    well. Do not add the short pair without measuring them.

    The seat is the horn's BLADE TOP, because that is the face the adapter
    lands on. The hub stands proud of it by (horn_hub_h - horn_blade_thk)
    and the retaining screw's head proud of that, and the central bore is
    sized to swallow BOTH and stay open - an open bore means a driver still
    reaches the horn's own retaining screw after the adapter is on, which is
    the difference between an assembly and a puzzle.
    """
    micro = servo.name in ('SG90', 'MG90S')
    first_r = MICRO_HORN_FIRST_HOLE_R if micro else MG995_HORN_FIRST_HOLE_R
    last_r = MICRO_HORN_LAST_HOLE_R if micro else MG995_HORN_LAST_HOLE_R

    case_top = servo.tab_below_top + servo.tab_thk
    boss_top = case_top + servo.boss_h
    seat_z = boss_top + servo.horn_blade_thk

    # The bore has to clear the hub (round, and the one horn dimension that
    # is MEASURED rather than modelled) and the retaining screw head.
    hub_clear = servo.horn_hub_dia + JOINT_FIT_MM['free']
    head_clear_d = servo.horn_screw_dia * 2.0 + head_clear
    bore_d = max(hub_clear, head_clear_d)

    slot_w = FASTENER_MM[screw]['clearance']
    slot_r_in = max(first_r - overrun, bore_d / 2.0 + MIN_WALL_MM)
    slot_r_out = last_r + overrun

    min_root_r = slot_r_out + slot_w / 2.0 + MIN_WALL_MM

    # How many of the horn's own holes the slot is guaranteed to span, if the
    # holes sit at first_r + n*pitch. One would do; the count is reported so
    # that a slot which only just catches one is visible rather than implied.
    caught = 0
    r = first_r
    while r <= last_r + 1e-9:
        if slot_r_in <= r <= slot_r_out:
            caught += 1
        r += servo.horn_hole_pitch

    m = HornBolt(
        servo_name=servo.name,
        seat_z=seat_z,
        bore_d=bore_d,
        slot_w=slot_w,
        slot_r_in=slot_r_in,
        slot_r_out=slot_r_out,
        slot_count=len(slot_angles_deg),
        slot_angles_deg=tuple(slot_angles_deg),
        min_root_r=min_root_r,
        holes_caught=caught,
    )

    bad = []
    if m.slot_len < 4.0:
        bad.append('a %.2f mm slot is not a range, it is a hole with '
                   'ambition' % m.slot_len)
    if m.holes_caught < 2:
        bad.append('the slot spans only %d horn hole(s) - the point of a '
                   'radial slot is that it catches the hole wherever the '
                   'batch put it' % m.holes_caught)
    if m.bore_d / 2.0 >= m.slot_r_in:
        bad.append('the bore Oe%.2f eats the slot inner end at r %.2f'
                   % (m.bore_d, m.slot_r_in))
    assert not bad, ('%s bolted horn interface is not buildable: '
                     % servo.name + '; '.join(bad))
    return m


# --- the gear the interface will carry -----------------------------------
# A SEPARATE piece from the adapter, and this is the two-piece decision made
# explicit. The adapter is sized by the HORN (r_out ~18.5). The pinion wants
# to be SMALL, because the pair's centre distance is what has to fit inside
# a link. Making one part do both jobs means the pinion inherits the horn's
# radius, and a 37 mm pinion is not a pinion.
#
# So: the adapter bolts to the horn and presents OUR OWN interface - a boss
# at `hub_d` and three M2 pilots on `hub_bolt_r`, both of them printed, both
# of them dimensions this project controls and can hold. The pinion registers
# on the boss and screws to the pilots. The horn's variation stops at the
# adapter's top face.


@dataclass(frozen=True)
class HubFace:
    """The KNOWN interface the adapter presents. This is the whole payoff."""

    hub_d: float           # register boss OD, printed
    hub_h: float           # how proud it stands
    bolt_r: float          # pilot circle radius
    bolt_count: int
    bolt_pilot_d: float    # self-tap pilot in the adapter
    bolt_clear_d: float    # clearance in whatever bolts to it
    journal_d: float       # boss that runs in the host's bearing
    journal_h: float

    @property
    def min_gear_root_r(self) -> float:
        """Floor under anything bolted to this face."""
        return self.bolt_r + self.bolt_clear_d / 2.0 + MIN_WALL_MM


def hub_face(bearing_bore=None, hub_d=11.0, hub_h=2.0, bolt_r=7.0,
             bolt_count=3, screw='M2'):
    """The adapter's output face.

    bolt_r 7.0 with an M2 clearance puts the floor under a bolted gear at
    7.0 + 1.2 + 1.6 = 9.8 mm of root radius. That is the number that sizes
    every stage below, and it is 1.5 mm smaller than bolting straight to the
    horn - which is exactly what the second piece buys.
    """
    f = FASTENER_MM[screw]
    return HubFace(
        hub_d=hub_d, hub_h=hub_h,
        bolt_r=bolt_r, bolt_count=bolt_count,
        bolt_pilot_d=f['pilot'], bolt_clear_d=f['clearance'],
        journal_d=bearing_bore if bearing_bore else 0.0,
        journal_h=0.0 if not bearing_bore else 3.0,
    )


# --- solving a stage rather than typing one ------------------------------

@dataclass(frozen=True)
class Adapter:
    """The printed disc that bolts to the horn. Full stack, in servo-z."""

    servo_name: str
    seat_z: float          # underside - lands on the horn BLADE top
    thk: float             # disc thickness
    od: float              # disc outer diameter
    pocket_d: float        # underside counterbore, clears the horn hub
    pocket_h: float        # ... and the retaining screw head
    slot_w: float
    slot_r_in: float
    slot_r_out: float
    slot_angles_deg: tuple
    out_bolt_r: float      # pilot circle the gear screws into
    out_bolt_pilot_d: float
    out_bolt_clear_d: float
    out_bolt_count: int
    journal_d: float       # runs in the host's bearing - takes the RADIAL load
    journal_h: float
    out_bolt_angles: tuple  # DERIVED to miss the slots - see adapter()
    slot_cb_d: float       # screw-head counterbore diameter
    slot_cb_h: float       # ... and depth
    out_pilot_h: float     # pilot depth, short of the pocket floor

    @property
    def gear_seat_z(self) -> float:
        """Servo-z of the face the gear sits on."""
        return self.seat_z + self.thk

    @property
    def min_gear_root_r(self) -> float:
        return self.out_bolt_r + self.out_bolt_clear_d / 2.0 + MIN_WALL_MM

    def standoff_vs_pressed(self, pressed_seat_z: float) -> float:
        """WHAT THE TWO-PIECE COSTS, in arm width. Say it, do not hide it."""
        return self.gear_seat_z - pressed_seat_z


def adapter(servo, slot_out_r=11.5, thk=None, out_bolt_r=None, out_bolt_count=3,
            screw=HORN_SCREW, journal_d=0.0, rim=2.5, head_h=2.0,
            head_cb=2.2):
    """Solve the adapter for a servo.

    THE COUNTERBORE IS NOT A THROUGH BORE, and that is the difference between
    a 5 mm disc and a 9 mm one. A through bore would leave no material at the
    centre for the output pilots to thread into, so the pilots would have to
    move out past it and the gear would have to grow to clear THEM. Blind-
    pocketing the horn hub keeps the disc solid from r `pocket_d/2` outward,
    which is where the pilots live.

    The cost of the blind pocket is that the horn's own retaining screw is
    captive once the adapter is on: to get the horn off the spline you take
    the adapter off first. That is one extra step in a teardown, against
    4 mm of arm width in every assembly. Stated so the trade is visible.

    THE SLOT DOES NOT RUN TO THE HORN'S TIP. It runs to `slot_out_r` 11.5,
    which catches the holes at r 6/8/10 - three of them - and keeps the disc
    at Oe28 instead of Oe42. A disc bigger than the pinion it carries cannot
    nest inside anything, and every millimetre of adapter radius past the
    last hole it uses is dead weight hanging off a 9 g servo.
    """
    b = horn_bolt(servo, screw=screw, slot_angles_deg=(0.0, 180.0))
    f = FASTENER_MM[screw]

    pocket_d = servo.horn_hub_dia + JOINT_FIT_MM['free']
    pocket_h = (servo.horn_hub_h - servo.horn_blade_thk) + head_h
    # DERIVED, not defaulted. The MG995's hub is Oe8.7 with a Oe3 retaining
    # screw; typing 5.0/6.0 for every servo put its pilots 0.55 mm from its
    # own horn pocket and left 1.40 mm of floor under it. The asserts caught
    # both, which is the only reason these are derived now.
    if thk is None:
        thk = math.ceil((pocket_h + MIN_WALL_MM) * 2.0) / 2.0
    if out_bolt_r is None:
        out_bolt_r = math.ceil(
            (pocket_d / 2.0 + FASTENER_MM[screw]['pilot'] / 2.0 + 1.2)
            * 2.0) / 2.0
    slot_r_out = min(slot_out_r, b.slot_r_out)
    od = 2.0 * (slot_r_out + f['clearance'] / 2.0 + rim)

    # WHERE THE OUTPUT PILOTS GO. Solved, not typed: three pilots evenly
    # spaced, rotated to the offset that puts them furthest from the horn
    # slots. With slots at 0/180 it lands on 90/210/330. If the slot angles
    # ever change these move with them instead of quietly overlapping - a
    # pilot drilled into a slot is a hole with no thread in it.
    step = 360.0 / out_bolt_count
    best_off, best_gap = 0.0, -1.0
    for i in range(int(step)):
        off = float(i)
        gap = min(abs((off + k * step - sa + 180.0) % 360.0 - 180.0)
                  for k in range(out_bolt_count)
                  for sa in b.slot_angles_deg)
        if gap > best_gap:
            best_off, best_gap = off, gap
    angles = tuple(best_off + k * step for k in range(out_bolt_count))

    a = Adapter(
        servo_name=servo.name,
        seat_z=b.seat_z, thk=thk, od=od,
        out_bolt_angles=angles,
        slot_cb_d=f['clearance'] + head_cb,
        slot_cb_h=head_h - 0.4,
        out_pilot_h=thk - 1.4,
        pocket_d=pocket_d, pocket_h=pocket_h,
        slot_w=b.slot_w, slot_r_in=b.slot_r_in, slot_r_out=slot_r_out,
        slot_angles_deg=b.slot_angles_deg,
        out_bolt_r=out_bolt_r, out_bolt_pilot_d=f['pilot'],
        out_bolt_clear_d=f['clearance'], out_bolt_count=out_bolt_count,
        journal_d=journal_d, journal_h=3.0 if journal_d else 0.0,
    )

    bad = []
    if a.pocket_h > a.thk - 1.6:
        bad.append('a %.2f pocket in a %.2f disc leaves %.2f of floor'
                   % (a.pocket_h, a.thk, a.thk - a.pocket_h))
    lig = a.out_bolt_r - a.out_bolt_pilot_d / 2.0 - a.pocket_d / 2.0
    if lig < 1.0:
        bad.append('only %.2f mm between the horn pocket and the output '
                   'pilots' % lig)
    caught = sum(1 for i in range(12)
                 if a.slot_r_in <= (MICRO_HORN_FIRST_HOLE_R
                                    + i * servo.horn_hole_pitch) <= slot_r_out)
    if caught < 2:
        bad.append('the shortened slot catches only %d horn hole(s)' % caught)
    if a.slot_r_in <= a.pocket_d / 2.0:
        bad.append('the slot starts inside the horn pocket')
    for ang in a.out_bolt_angles:
        for sang in a.slot_angles_deg:
            d = abs((ang - sang + 180.0) % 360.0 - 180.0)
            sep = math.radians(d) * a.out_bolt_r
            need = a.slot_w / 2.0 + a.out_bolt_pilot_d / 2.0 + 1.0
            if sep < need:
                bad.append('output pilot at %.0f deg is only %.2f mm from '
                           'the slot at %.0f deg, needs %.2f'
                           % (ang, sep, sang, need))
    assert not bad, ('%s adapter is not buildable: ' % servo.name
                     + '; '.join(bad))
    return a


@dataclass(frozen=True)
class SplineHub:
    """A printed gear driven straight off the servo spline. No horn.

    Distances in mm, in lib/servo.py's servo frame.
    """

    servo_name: str
    seat_z: float          # servo-z of the hub's underside
    boss_clear_d: float    # lower bore - clears the output collar
    boss_clear_to: float   # ... up to here (the boss top)
    broach_d: float        # upper bore - the spline cuts into this
    broach_from: float     # from the boss top
    broach_to: float       # to the top of the spline
    min_height: float      # least hub height that reaches the spline at all
    engaged: float         # how much spline the bore actually grips
    washer_d: float        # the retaining screw needs one - see below
    screw_d: float

    @property
    def min_gear_root_r(self) -> float:
        """Floor under a gear cut into this hub. Set by the BOSS bore, which
        is the widest thing in the stack - not by a bolt circle, because
        there is no longer a bolt circle."""
        return self.boss_clear_d / 2.0 + MIN_WALL_MM


def spline_hub(servo, face, case_gap=0.4, engage_min=2.0, washer_extra=1.6):
    """Solve a gear-on-spline hub for a servo and a face width.

    SEATED AS LOW AS THE CASE ALLOWS, one running gap above the case top -
    the same rule horn_pinion() used, and for the same reason: seat_z is what
    the host has to stand the servo off by, and every millimetre of it is arm
    width. Deleting the horn is worth a lot here. The bolted-horn adapter put
    the MG90S gear plane at 18.50; this puts it at 5.90, which is exactly
    where the pressed-on-horn pinion already sat. The horn comes out of the
    machine for free.

    THE BORE IS TWO DIAMETERS. The spline sits above the output boss, so the
    lower part of the bore has to CLEAR the boss (Ø6.0 on an MG90S) and only
    the upper part grips the Ø5.0 spline. That is also why a thin gear cannot
    drive a servo directly no matter how good the bore is: it has to be tall
    enough to reach past the boss before it grips anything. min_height is
    that arithmetic, and `face` is checked against it.

    THE RETAINING SCREW NEEDS A WASHER AND THIS IS NOT OPTIONAL. The servo's
    own screw is Ø2.5 (micro) with a head around Ø5.0, and the broach bore is
    Ø4.75. The head would sit almost entirely over the hole with nothing to
    clamp. `washer_d` is the smallest washer that actually lands on the hub's
    top face. Without it the gear is held on by the broach alone and will
    walk up the spline.
    """
    from lib.servo import spline_bore_d, spline_z

    case_top = servo.tab_below_top + servo.tab_thk
    seat_z = case_top + case_gap
    boss_top, spline_top = spline_z(servo)
    boss_clear_d = servo.boss_dia + JOINT_FIT_MM['free']
    broach_d = spline_bore_d(servo)

    top = seat_z + face
    engaged = max(0.0, min(top, spline_top) - boss_top)
    h = SplineHub(
        servo_name=servo.name,
        seat_z=seat_z,
        boss_clear_d=boss_clear_d,
        boss_clear_to=boss_top - seat_z,
        broach_d=broach_d,
        broach_from=boss_top - seat_z,
        broach_to=spline_top - seat_z,
        min_height=(boss_top - seat_z) + engage_min,
        engaged=engaged,
        washer_d=broach_d + washer_extra,
        screw_d=servo.horn_screw_dia,
    )

    bad = []
    if face < h.min_height:
        bad.append('a %.2f face seats at %.2f and never reaches the spline at '
                   '%.2f - it needs at least %.2f'
                   % (face, seat_z, boss_top, h.min_height))
    if h.engaged < engage_min:
        bad.append('only %.2f mm of spline engagement, want %.2f'
                   % (h.engaged, engage_min))
    if h.broach_d >= h.boss_clear_d:
        bad.append('the broach bore Oe%.2f is not smaller than the boss '
                   'clearance Oe%.2f - the boss would not pass'
                   % (h.broach_d, h.boss_clear_d))
    assert not bad, ('%s spline hub is not buildable: ' % servo.name
                     + '; '.join(bad))
    return h


def solve_stage(name, servo, target_ratio, max_centre_mm, torque_nm,
                face=None, min_root_r=None, modules=(1.0, 1.25, 1.5),
                z_max=90):
    """Smallest pair that hits the ratio, clears the bolt circle and holds.

    Returns (SpurPair, notes) or (None, why_not). Nothing is typed: the
    packaging limit and the bolt circle pick the teeth.
    """
    # IMPORTED HERE, NOT AT THE TOP, AND THAT IS LOAD-BEARING. lib/gears.py
    # imports spline_hub() from this module at its foot, so a module-level
    # `from lib.gears import ...` here closes a cycle: `import lib.servo_hub`
    # on its own then raises "cannot import name 'spline_hub' from partially
    # initialized module", and models/robotarm/horn_adapter.py - whose import
    # block reaches servo_hub first - was dead on arrival because of it.
    # Deferring the import to the one function that needs it breaks the cycle
    # without either module having to know about the other's order.
    from lib.gears import LEWIS_Y, SpurPair
    floor = min_root_r if min_root_r is not None else hub_face().min_gear_root_r
    tried, best = [], None
    for module in modules:
        f = face if face is not None else max(3.0 * module, 6.0)
        # smallest pinion whose ROOT clears the bolt circle
        z_min_bolt = math.ceil((floor / module + 1.25) * 2.0)
        z_min_cut = math.ceil(2.0 / math.sin(math.radians(20.0)) ** 2)
        for zp in range(max(z_min_bolt, z_min_cut), 60):
            zg = int(round(zp * target_ratio))
            if zp not in LEWIS_Y or zg not in LEWIS_Y or zg > z_max:
                continue
            pair = SpurPair(name=name, module=module, z_pinion=zp,
                            z_gear=zg, face=f)
            if pair.centre_distance > max_centre_mm:
                tried.append('m%.2f %dT/%dT: centre %.2f over %.2f'
                             % (module, zp, zg, pair.centre_distance,
                                max_centre_mm))
                continue
            bad = pair.validate(torque_nm)
            if bad:
                tried.append('m%.2f %dT/%dT: %s' % (module, zp, zg, bad[0]))
                continue
            if pair.r_root(zp) < floor:
                tried.append('m%.2f %dT/%dT: root r %.2f under the %.2f bolt '
                             'floor' % (module, zp, zg, pair.r_root(zp), floor))
                continue
            if best is None or pair.centre_distance < best.centre_distance:
                best = pair
            break
    if best is None:
        return None, tried
    return best, tried
