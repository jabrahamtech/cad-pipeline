"""Joint interfaces — the datums that cross a PART BOUNDARY.

THE PROJECT'S NAMED FAILURE IS A DATUM ONLY ONE FILE READS. lib/gears.py
owns the J3 involute because two printed parts have to cut the same tooth;
lib/servo.py owns the servo envelopes because six parts cut the same pocket.
This file owns the third class and the one that has actually broken the
build: the numbers that describe a JOINT — the place where two printed parts
touch — which until now lived in whichever part script happened to be
written first and were read back out of a SHARED FUSION DOCUMENT by the
other side.

WHY A FUSION USER PARAMETER CANNOT BE THAT HOME. A user parameter is
DOCUMENT-scoped. It exists only while both parts sit in the same document,
it is invisible across an external reference, and when it is absent the
consumer's `ups.itemByName('fa_...')` returns None. Four of the five
consumers then fall back to a hardcoded literal and print nothing — the
part builds, the gate passes, and the joint is wrong. That is not a
tolerance problem, it is a part built against a datum that was not there.

The five reads, and what each turns out to be (the audit is in
specs/robotarm/_decouple.md, the workaround is _build_parts.DEPS):

    gripcut_finger -> pb_edge_off      ALREADY DERIVABLE - lib/pruner_linkage
    j3_gear        -> fa_bore_d        DERIVABLE - HEX_PIVOT below
                   -> fa_plate_t       DERIVABLE - FORK_PLATE below
    j3_servo_cap   -> fa_cap_*, fa_lobe_*, fa_j3_centre, fa_l2, fa_wall
                                        GENUINE, and SOLVED here as J3_PAD
    j3_axle        -> ua_socket_d      GENUINE - HEX_PIVOT.socket_d
    upper_arm      -> fa_elbow_clear   GENUINE - ELBOW below (the cycle)
                   -> jg_bolt_clear    ALREADY DERIVABLE - design_rules M3
                   -> ja_socket_d      GENUINE - HEX_PIVOT.socket_d
                   -> jg_/ja_ x5       DERIVABLE - ELBOW_BOLT below

Nothing here touches Fusion. It is arithmetic plus the checks the arithmetic
has to survive, so it runs and can be argued with outside the CAD — the same
contract lib/gears.py keeps.

PROVENANCE GRADES, one per number, no exceptions:
    MEASURED   caliper or probe against the real object / the built body
    DATASHEET  vendor drawing or table for a BOUGHT part
    DERIVED    arithmetic on other graded numbers in this repo
    ASSUMED    chosen, defensible, and NOT yet checked against anything

EXTRACTION NOTE. Every MEASURED/ASSUMED constant below currently also
exists as a literal inside a part script. This file is written to be the
home; it does not by itself remove the copy. specs/robotarm/_decouple.md
names the line to delete in each consumer, and until that edit lands the
two copies agree only by inspection. Where a number could not be traced to
a lib module or a stated derivation it is marked EXTRACTED-FROM with the
script it was lifted from, because inventing a dimension is the one thing
this repo forbids outright.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from lib.bearings import B608ZZ
from lib.design_rules import (
    FASTENER_MM,
    JOINT_FIT_MM,
    MIN_WALL_MM,
)
from lib.gears import J3_MOUNT, J3_PAIR
from lib.servo import (
    CATALOG as SERVOS,
    SERVO_CASE_CLEARANCE_MM,
    SERVO_SCREW_PILOT_MM,
)

# --- the fits, named once so no part re-types the table ------------------
# These are the design_rules JOINT_FIT_MM rows this project's joints use.
# They are aliased rather than copied: a part that says `loc` means THIS.
LOC = JOINT_FIT_MM['locational']     # 0.20  HANDBOOK
ROT = JOINT_FIT_MM['rotating']       # 0.35  HANDBOOK
FREE = JOINT_FIT_MM['free']          # 0.40  HANDBOOK

M3 = FASTENER_MM['M3']

# M3 socket cap head, ISO 4762. DATASHEET. design_rules' FASTENER_MM has no
# head column, which is why five scripts each typed 6.0 by hand; it lives
# here until that table grows one.
M3_SOCKET_HEAD_DIA_MM = 6.0          # DATASHEET
M3_SOCKET_HEAD_CBORE_MM = 3.2        # DERIVED: 3.0 nominal head + 0.2 so it
                                     # finishes BELOW the face, not level


# =========================================================================
#  1. THE HEX PIVOT — J3 and J4 are the SAME joint, four printed copies
# =========================================================================
# This is the `wr_*` block, and it is currently typed out in FIVE part
# scripts (wrist_hub, wrist_roll, forearm, upper_arm, j3_gear, j3_pinion,
# j3_axle — six, counting the two that carry only half of it) each of them
# ending its comment with "SHARED, defined identically in ...". A datum that
# is defined identically in six files is defined nowhere.
#
# THE JOINT: a hub with a round journal collar runs in a bore through a fork
# plate. Outboard of the plate a flange sits loose in a counterbore and
# stops the hub walking out. Inboard, a HEX boss reaches across the running
# gap and bottoms in a hex socket in the straddled part, and that bottoming
# — not the flange — is what locates the joint axially. Two hard stops on
# one axis would fight, so the counterbore is deliberately deeper than the
# flange (`cbore_extra`).
#
# WHY THE SOCKET IS A HEX AND NOT A SECOND JOURNAL: both journals live in
# the FORK, so the socket only has to transmit torque and index. It can
# therefore be 3.4 deep, which is all the room there is beside the gripper
# servo (wrist_hub.py's docstring makes the argument).


@dataclass(frozen=True)
class HexPivot:
    """One straddled hex pivot, and the fork plate that carries it.

    All lengths mm. The frame is the hub's: +Z out along the pivot axis,
    z = 0 on the face that lands on the fork plate's INNER face.
    """

    name: str
    pivot_af: float        # hex SOCKET across flats (the hole is nominal)
    straddle: float        # width the fork straddles
    sweep_r: float         # radius the straddled part sweeps about the axis
    hub_d: float           # journal collar diameter
    journal: float         # collar length = the plate thickness it runs in
    flange_d: float        # retaining flange diameter
    flange_t: float        # flange thickness
    socket_d: float        # hex socket DEPTH into the straddled part
    gap: float = FREE      # running gap, plate inner face to that part
    cbore_extra: float = 0.5
    wall: float = MIN_WALL_MM

    # ---- the hub side ---------------------------------------------------
    @property
    def hex_af(self) -> float:
        """Hub hex across flats. GROW THE HOLE, SHRINK THE HEX — the socket
        stays nominal so the straddled part's tooling never moves."""
        return self.pivot_af - LOC

    @property
    def hex_across_corners(self) -> float:
        """The number that sized hub_d. The hub is threaded through its own
        journal bore at assembly, so the collar has to be bigger than this
        or the part cannot be assembled at all — it was 18.0 once and the
        corners stood proud."""
        return self.hex_af / math.cos(math.pi / 6.0)

    @property
    def reach(self) -> float:
        """Hex boss length = running gap + socket depth, so it BOTTOMS.

        This is the derivation the repo has been carrying as the literal
        3.8 in six scripts. `socket_d` and `gap` are the primitives; reach
        is arithmetic on them and must never be typed again.
        """
        return self.gap + self.socket_d

    # ---- the fork plate side --------------------------------------------
    @property
    def cbore_depth(self) -> float:
        return self.flange_t + self.cbore_extra

    @property
    def plate_t(self) -> float:
        """Fork plate thickness — journal length plus the counterbore.

        j3_gear.py carries this as `jg_plate_t = 7.5 mm` and then asserts it
        equals `fa_plate_t` IF the forearm happens to be in the document.
        It is not an independent number in either file: it is this sum.
        """
        return self.journal + self.cbore_depth

    @property
    def plate_in(self) -> float:
        """Plate inner face, from the straddle centreline."""
        return self.straddle / 2.0 + self.gap

    @property
    def plate_out(self) -> float:
        return self.plate_in + self.plate_t

    @property
    def bore_d(self) -> float:
        """Journal bore in the plate — this is `fa_bore_d`, which j3_gear
        reads out of the document to check its own journal passes."""
        return self.hub_d + ROT

    @property
    def cbore_d(self) -> float:
        return self.flange_d + ROT

    @property
    def boss_r(self) -> float:
        """Pivot boss radius on the fork plate: counterbore plus a wall."""
        return self.cbore_d / 2.0 + self.wall

    def validate(self) -> list:
        """Complaints. Empty means the joint is assemblable and printable."""
        bad = []
        if self.hub_d <= self.hex_across_corners:
            bad.append('the collar is %.2f and the hex is %.2f across corners '
                       '- the hub cannot be threaded through its own bore'
                       % (self.hub_d, self.hex_across_corners))
        if self.flange_d <= self.bore_d:
            bad.append('the %.2f flange passes the %.2f bore and retains '
                       'nothing' % (self.flange_d, self.bore_d))
        if self.reach <= self.gap:
            bad.append('the hex does not reach across the running gap')
        if self.cbore_extra <= 0.0:
            bad.append('the flange would seat in its counterbore and fight '
                       'the hex bottoming in its socket - two hard stops on '
                       'one axis')
        if self.boss_r * 2.0 <= self.flange_d:
            bad.append('the pivot boss is inside its own counterbore')
        return bad


# THE ONE JOINT, USED TWICE. J3 (elbow) and J4 (wrist pitch) are the same
# design: the upper arm straddles the forearm exactly as the forearm
# straddles the roll housing. One design, four printed copies, two joints —
# so there is one object here, not two.
#
# pivot_af 16.0     ASSUMED   EXTRACTED-FROM wrist_hub.py wr_pivot_af. The
#                             biggest hex that fits beside the gripper servo;
#                             nothing has measured it because nothing needs
#                             to - it mates only with printed parts.
# straddle 24.0     ASSUMED   EXTRACTED-FROM wrist_roll.py - "this housing
#                             across the pitch axis". It is the roll
#                             housing's own width and wrist_roll is the
#                             authority; see the extraction note in
#                             _decouple.md, it should become a derived
#                             property of that part's envelope.
# sweep_r 25.4      ASSUMED   EXTRACTED-FROM wrist_roll.py. No forearm
#                             material inside the straddle may come closer
#                             than this to the pitch axis.
# hub_d 20.0        DERIVED   from hex_across_corners 18.24 + clearance to
#                             pass. Was 18.0 and would not assemble.
# journal 5.0       ASSUMED   EXTRACTED-FROM wrist_hub.py
# flange_d 24.0     ASSUMED   EXTRACTED-FROM wrist_hub.py
# flange_t 2.0      ASSUMED   EXTRACTED-FROM wrist_hub.py
# socket_d 3.4      ASSUMED   EXTRACTED-FROM upper_arm.py ua_socket_d. THE
#                             PRIMITIVE behind wr_reach, and the number
#                             j3_axle reads across the document today.
HEX_PIVOT = HexPivot(
    name='J3/J4 straddled hex pivot',
    pivot_af=16.0, straddle=24.0, sweep_r=25.4,
    hub_d=20.0, journal=5.0, flange_d=24.0, flange_t=2.0,
    socket_d=3.4,
)

# Aliases, so a consumer says which joint it means and gets the same object.
J4_PIVOT = HEX_PIVOT
J3_PIVOT = HEX_PIVOT

_bad = HEX_PIVOT.validate()
assert not _bad, 'HEX_PIVOT is not assemblable: ' + '; '.join(_bad)

# The literals this replaces, asserted against their derivations so that
# moving a primitive cannot silently change a part that still carries the
# old copy. If one of these fires, a consumer in models/ is now wrong.
assert abs(HEX_PIVOT.reach - 3.8) < 1e-9, (
    'wr_reach is 3.8 in six scripts and this now derives %.3f'
    % HEX_PIVOT.reach)
assert abs(HEX_PIVOT.plate_t - 7.5) < 1e-9, (
    'jg_plate_t is 7.5 and this now derives %.3f' % HEX_PIVOT.plate_t)
assert abs(HEX_PIVOT.bore_d - 20.35) < 1e-9, (
    'fa_bore_d builds out at 20.35 and this now derives %.3f'
    % HEX_PIVOT.bore_d)
assert abs(HEX_PIVOT.boss_r - 13.775) < 1e-9, (
    'j3_axle.py reasons about a r 13.775 boss and this derives %.3f'
    % HEX_PIVOT.boss_r)


# =========================================================================
#  2. THE ELBOW — and the circular dependency it caused
# =========================================================================
# THE CYCLE, PLAINLY. upper_arm.py sets `ua_drum_r = 13.0` and comments
# "NOT FREE: the forearm cuts its own clearance at fa_elbow_clear = 13.4".
# forearm.py sets `fa_elbow_clear = 13.4` and comments "ua_drum_r drives it
# and that is now 13.0". Each file names the other as the authority, and
# then upper_arm READS fa_elbow_clear out of the document to assert on it —
# falling back, when the forearm is absent, to `drum_r + 0.4`, which is the
# very number it was trying to check. The assert cannot fail on its own
# fallback. That is the cycle _build_parts.DEPS runs upper_arm TWICE for.
#
# IT IS NOT A CYCLE. It is one number with two names. The upper arm's drum
# radius is the primitive — it is set by what the elbow block has to hold,
# which is a 16.0 af hex socket: circumradius 9.24, plus a 1.6 wall, plus
# 0.4 gives 11.24, and 13.0 is above that floor for section rather than for
# fit. The forearm's allowance is that radius plus a running gap, and
# NOTHING ELSE. So the primitive lives here and both sides derive.


@dataclass(frozen=True)
class ElbowSweep:
    """What the upper arm sweeps about J3, and what the forearm must give it.

    drum_r 13.0   ASSUMED   EXTRACTED-FROM upper_arm.py ua_drum_r. Above the
                            derived floor (see `floor_r`) for section, not
                            for fit: the link is two drums joined by a
                            CONCAVE arc, so the waist must stay under the
                            drum radius or the blend inverts, and at
                            waist_z 12.0 the drums have to be at least 12.
    """

    drum_r: float
    gap: float = FREE

    @property
    def clearance_r(self) -> float:
        """`fa_elbow_clear`. The radius the forearm must keep empty about
        J3 — derived, never typed."""
        return self.drum_r + self.gap

    def floor_r(self, pivot: HexPivot, wall: float = MIN_WALL_MM) -> float:
        """The smallest drum that can hold the hex socket at all.

        Circumradius of the SOCKET (nominal af, not the hub's shrunk hex —
        the socket is the hole in this part), plus a wall, plus the gap.
        """
        return (pivot.pivot_af / 2.0 / math.cos(math.pi / 6.0)
                + wall + self.gap)


ELBOW = ElbowSweep(drum_r=13.0)

assert abs(ELBOW.clearance_r - 13.4) < 1e-9, (
    'fa_elbow_clear is 13.4 in forearm.py and this derives %.3f'
    % ELBOW.clearance_r)
assert ELBOW.drum_r >= ELBOW.floor_r(HEX_PIVOT), (
    'a r %.2f drum cannot hold a %.1f af hex socket with a wall round it - '
    'the floor is %.2f' % (ELBOW.drum_r, HEX_PIVOT.pivot_af,
                           ELBOW.floor_r(HEX_PIVOT)))


# --- the elbow retention bolt --------------------------------------------
# WHY THERE IS ONE. Every other hub in the arm is trapped by a flange too
# big to pass its bore. At the geared elbow both stops are INBOARD - the hex
# bottoms in the socket and the gear disc lands on the plate's outer face -
# so nothing at all stops the group sliding out and pulling a 3.8 hex clear
# of a 3.4 socket. An M3 runs the full width down the J3 axis, from j3_gear
# through the upper arm's cable duct, into j3_axle's tap.
#
# IT IS A THREE-FILE NUMBER, which is exactly the shape of bug this repo
# keeps paying for. j3_gear cuts the clearance, upper_arm bores the duct,
# j3_axle taps. All three already read FASTENER_MM['M3'] — the cross-
# document assert between jg_bolt_clear and ua_bolt_clear is therefore
# checking design_rules against itself and can simply go.
#
# WHAT IS NOT DERIVABLE without a cross-read today is the SCREW LENGTH,
# which upper_arm.py prints by reading five sibling parameters (jg_face,
# jg_bolt_head_d, jg_collar_l, wr_reach, ja_tap_l) and silently stops
# printing when they are absent. Every one of those five is arithmetic on
# things this file and lib/gears.py already own, so `elbow_bolt()` below
# computes it with no document at all.


@dataclass(frozen=True)
class ElbowBolt:
    """The M3 that clamps the rotating elbow group into one piece.

    tap_l 9.0   ASSUMED   EXTRACTED-FROM j3_axle.py ja_tap_l - thread
                          engagement into printed PETG. 9.0 is 3x diameter,
                          comfortably over the 1.5d a self-tapping M3 needs,
                          and it is bounded by the axle's own length.
    """

    clearance: float = M3['clearance']       # DERIVED - design_rules
    pilot: float = M3['pilot']               # DERIVED - design_rules
    head_d: float = M3_SOCKET_HEAD_DIA_MM    # DATASHEET
    cbore_depth: float = M3_SOCKET_HEAD_CBORE_MM
    tap_l: float = 9.0

    def gear_collar_l(self, pivot: HexPivot) -> float:
        """`jg_collar_l` — the gear's journal spans the plate plus the gap
        that keeps its disc off the plate face."""
        return pivot.plate_t + pivot.gap

    def head_to_hex(self, pivot: HexPivot, pair=J3_PAIR) -> float:
        """From the head UNDERSIDE to the far face of the gear's hex."""
        return (pair.face - self.cbore_depth
                + self.gear_collar_l(pivot) + pivot.reach)

    def across(self, pivot: HexPivot) -> float:
        """Through the upper arm: socket floor to socket floor."""
        return 2.0 * (pivot.straddle / 2.0 - pivot.socket_d)

    def to_tap(self, pivot: HexPivot, pair=J3_PAIR) -> float:
        return self.head_to_hex(pivot, pair) + self.across(pivot)

    def buy_mm(self, pivot: HexPivot, pair=J3_PAIR) -> float:
        """WHAT LENGTH SCREW TO BUY, rounded up to the next 5 mm.

        Sized for 1.5 diameters of engagement, not for bottoming: a screw
        that bottoms in a printed tap splits the boss, and one 5 mm short is
        a joint that comes apart on the bench with every gate passing.
        """
        min_eng = self.to_tap(pivot, pair) + 1.5 * self.clearance
        return 5.0 * math.ceil(min_eng / 5.0)

    def bottoms_mm(self, pivot: HexPivot, pair=J3_PAIR) -> float:
        """The longest screw that still fits — full tap, no protrusion."""
        return self.to_tap(pivot, pair) + self.tap_l


ELBOW_BOLT = ElbowBolt()

assert ELBOW_BOLT.tap_l <= (HEX_PIVOT.socket_d + HEX_PIVOT.gap
                            + B608ZZ.width + 0.5 - 0.1), (
    'the %.1f retention tap runs out the far end of the axle' % ELBOW_BOLT.tap_l)
assert abs(ELBOW_BOLT.gear_collar_l(HEX_PIVOT) - 7.9) < 1e-9, (
    'jg_collar_l builds out at 7.9 and this derives %.3f'
    % ELBOW_BOLT.gear_collar_l(HEX_PIVOT))


# --- the idler side: a 608ZZ instead of plastic on plastic ---------------
# WHY. A gear mesh loads the J3 axis RADIALLY, and slop at the elbow is
# backlash at the tooth — the one thing a 2:1 reduction cannot fix. The
# printed journal it replaces ran a 20.0 collar in a 20.35 bore, 0.175 of
# slop per side. j3_axle.py carries the full argument.
#
# THIS IS ALREADY CLEAN — both sides read lib/bearings.B608ZZ. It is
# restated here only because the two sides have to agree about WHICH RACE
# each one touches, and that agreement is the joint, not the bearing:
# j3_axle's thrust collar must land INSIDE the inner race, the forearm's
# retaining shoulder must bear OUTSIDE it, and a part that gets this
# backwards rubs the outer race and locks the joint solid.


@dataclass(frozen=True)
class BearingSeat:
    """Who touches which race, at the J3 idler.

    collar_d 11.0  DERIVED  inside inner_race_od 12.0 with 0.5 of margin,
                            outside bore 8.0 with 1.5 of land.
    press 0.02     ASSUMED  EXTRACTED-FROM j3_axle.py. A light press on the
                            INNER race. forearm.py applies the same 0.02 to
                            the OUTER race and says so in its own comment -
                            a housing fit is not a shaft fit and neither has
                            been gauged. design_rules has a HANDBOOK
                            `bearing_pocket` 0.05 for the housing side; the
                            two disagree and only a gauge print settles it.
    """

    brg = B608ZZ
    collar_d: float = 11.0
    shaft_press: float = 0.02
    housing_press: float = 0.02
    proud: float = 0.5

    @property
    def journal_d(self) -> float:
        return self.brg.bore - self.shaft_press

    @property
    def journal_l(self) -> float:
        """Through the bearing and proud, so the bearing seats on the
        COLLAR and not on the end of the journal."""
        return self.brg.width + self.proud

    @property
    def pocket_d(self) -> float:
        """The forearm's pocket, on the outer race."""
        return self.brg.od - self.housing_press

    @property
    def shoulder_bore_d(self) -> float:
        """The forearm's retaining shoulder. The plate does not turn, so
        its shoulder must bear OUTSIDE the inner race."""
        return self.brg.inner_race_od + 1.0

    @property
    def shoulder_t(self) -> float:
        return HEX_PIVOT.plate_t - self.brg.width


J3_BEARING = BearingSeat()

assert J3_BEARING.collar_d <= B608ZZ.inner_race_od - 0.5, (
    'the thrust collar is %.2f and the inner race stops at %.2f - it would '
    'bear on the OUTER race and lock the joint'
    % (J3_BEARING.collar_d, B608ZZ.inner_race_od))
assert J3_BEARING.collar_d >= B608ZZ.bore + 2.0, (
    'the thrust collar is %.2f, barely over the %.2f bore - no land to bear '
    'on' % (J3_BEARING.collar_d, B608ZZ.bore))
assert J3_BEARING.shoulder_bore_d > B608ZZ.inner_race_od, (
    'the plate shoulder would rub the inner race')
assert HEX_PIVOT.hex_across_corners > B608ZZ.inner_race_od, (
    'sanity: the hex is meant to be bigger than the race - that is the whole '
    'reason the thrust collar exists')
# THE RETAINING SHOULDER IS 0.50 MM AND THAT IS NOT A WALL. plate_t 7.5
# less the 608's 7.0 width leaves half a millimetre of plate outboard of the
# pocket. forearm.py floors it at 0.40 rather than at MIN_WALL_MM, and it is
# right to: this is an annular LIP that stops the outer race walking out, in
# pure compression, backed by the whole boss - not a wall spanning anything.
# It is still one extrusion pair thick, it is the thinnest feature in the
# elbow, and it is the reason `journal_l` runs the bearing PROUD so the
# clamp lands on the collar. If plate_t ever comes down, this goes first.
_SHOULDER_FLOOR_MM = 0.4        # ASSUMED - EXTRACTED-FROM forearm.py
assert J3_BEARING.shoulder_t >= _SHOULDER_FLOOR_MM, (
    'only %.2f mm of plate outboard of the bearing pocket - the outer race '
    'has nothing to bear against' % J3_BEARING.shoulder_t)


# =========================================================================
#  3. THE J3 SERVO PAD — the interface j3_servo_cap cannot guess
# =========================================================================
# THIS IS THE ONE GENUINELY HARD CASE, and it is the only consumer that
# ASSERTS rather than falling back. j3_servo_cap.py is right to: a cap that
# built itself to its own idea of the interface would fit nothing and would
# print clean while doing it. But the interface it demands is not a set of
# free choices the forearm made — it is a SOLVED result, and forearm.py
# solves it in twenty lines of `run()` before it cuts anything.
#
# WHAT IS BEING SOLVED. The J3 servo bolts to a pad that the forearm's
# standoff carries. The cap is that pad, made removable, so the servo can be
# fitted after the gears are meshed. Two M3s hold the cap on. Where they go
# is pinned on all four sides:
#     inboard   the servo case window, which the cap must not break into
#     outboard  the block edge, one head radius and one wall short of it
#     across    the servo's OWN outer tab pilot, which is BLIND in the same
#               face the cap sinks its counterbore into - so the two collide
#               underground while looking 2.4 mm apart on the face. That is
#               the binding constraint and it is the easy one to miss.
#     in Z      as far apart as the edge and a FLUSH head allow, because the
#               servo reacts its stall torque about X as a couple in Z and
#               two screws split it; side by side in Y they would not.
# Nothing in that list is a preference. Given the MG90S envelope, the wall
# and the head, there is exactly one answer, and both parts can compute it.
#
# THE FRAME IS THE SERVO'S, NOT THE FOREARM'S, and that is what breaks the
# dependency. Today j3_servo_cap reads `fa_l2` and `fa_j3_centre` purely to
# subtract `y_pin = -l2 + centre` and get back into the servo's own frame -
# it converts the forearm's numbers into servo-local and then uses only
# those. Express the contract in servo-local to begin with and BOTH datums
# drop out of the cap entirely. The cap does not care where the elbow is.
#
#   +X  along the case, away from the shaft, from the shaft-end face
#       toward the far end. The case spans -shaft_from_end .. +case_l-that.
#   +Z  across the case width, 0 on the servo's centre plane.
#   The pad plane is the servo's own tab plane (lib/servo.py's datum).
#
# NOTE ON lib/servo.py's frame docstring: it says "+X runs along the case
# length away from the shaft, toward the lead end", but the corrected lead
# datum in the same file puts lead_x at -shaft_from_end, i.e. NEGATIVE. The
# lead end is -X. The prose is stale; the numbers are right and this file
# follows the numbers. Flagged in _decouple.md.


@dataclass(frozen=True)
class ServoPad:
    """Where a servo bolts to a pad, and where the pad bolts to its host.

    Every length mm, in the SERVO's frame (see the block above). This is
    the whole of the `fa_cap_*` / `fa_lobe_*` interface, solved.
    """

    servo_name: str
    pad_t: float           # pad thickness - the tabs bear on its outer face
    half_z: float          # pad half height across the case width
    x_lo: float            # pad edge, inboard (past the near tab screw)
    x_hi: float            # pad edge, outboard - this is `fa_cap_reach`
    case_x0: float         # servo window, near end
    case_x1: float         # servo window, far end
    case_z: float          # servo window across the width, full
    tab_x_lo: float        # the servo's own inboard tab screw
    tab_x_hi: float        # ... and the outboard one
    pilot_d: float         # tab screw pilot
    fix_x: float           # cap screw station along X - `fa_cap_screw_y`
    fix_z: float           # cap screw offset in Z, +/- - `fa_cap_screw_z`
    fix_d: float           # cap screw clearance
    fix_head_d: float      # cap screw head
    fix_head_z: float      # counterbore depth, head FLUSH
    corner_r: float        # pad corner radius
    lead_key_d: float      # lead keyway width, END wall, ONE notch
    lead_key_l: float      # keyway length out from the shaft-end face

    @property
    def under_head(self) -> float:
        return self.pad_t - self.fix_head_z


def servo_pad(servo, standoff_pad_over=1.0, pad_pad=3.5, corner_r=4.5,
              head_d=M3_SOCKET_HEAD_DIA_MM,
              head_cbore=M3_SOCKET_HEAD_CBORE_MM,
              wall=MIN_WALL_MM, margin=0.1):
    """Solve the J3 servo pad for a servo. Pure arithmetic, no document.

    This reproduces forearm.py's in-`run()` solve EXACTLY - the assertions
    at the bottom of this file pin it to the numbers that part builds today
    - so adopting it is a refactor, not a redesign.

    pad_pad 3.5     ASSUMED   EXTRACTED-FROM forearm.py fa_lobe_pad -
                              material past the outermost tab screw.
    corner_r 4.5    MEASURED  (probed against the built body, 2026-08-31)
                              EXTRACTED-FROM forearm.py fa_lobe_radius_j3.
                              A CEILING, not a preference: 6.0 fails
                              ASM_INCONS_FACE, 5.5 and 5.0 fail
                              ASM_BL_CAP_COMPLEX, 4.5 computes. Do not raise
                              it without re-probing the built body.
    over 1.0        ASSUMED   EXTRACTED-FROM forearm.py fa_lobe_over - the
                              lobe starts INSIDE the plate, because two
                              volumes meeting exactly on a plane are
                              non-manifold and the fillet fails later.
    margin 0.1      ASSUMED   EXTRACTED-FROM forearm.py fa_cap_margin -
                              slack so the downstream asserts measure the
                              design and not a float comparison.

    THE WINDOW CLEARANCE IS lib/servo.py's, NOT `loc`. forearm.py CUTS its
    window at SERVO_CASE_CLEARANCE_MM (1.0) but SOLVES the screw station
    against a window edge computed with `fa_loc` (0.2) - so its own assert
    is checking against an edge 0.4 mm inboard of the one it cut. It does
    not bind today (the tab pilot governs, by 0.80 mm), but it is a latent
    contradiction and this function uses the clearance that is actually cut.
    """
    c = SERVO_CASE_CLEARANCE_MM

    # The case, in the servo's own frame. The shaft sits shaft_from_end in
    # from the NEAR end and the case runs on away from it.
    near = -servo.shaft_from_end
    far = near + servo.case_l
    mid = (near + far) / 2.0
    tab_lo = mid - servo.tab_hole_pitch / 2.0
    tab_hi = mid + servo.tab_hole_pitch / 2.0

    pad_t = servo.tab_below_top + servo.tab_thk
    half_z = servo.case_w / 2.0 + wall + 1.0
    win_x0, win_x1 = near - c / 2.0, far + c / 2.0

    head_r = head_d / 2.0

    # Z FIRST - it depends on nothing else. What binds is the COUNTERBORE,
    # not the hole: sized on the shank, 5.0 looked fine and put the head
    # 0.80 from the edge.
    fix_z = half_z - wall - head_r

    # X is pinned by three things and it took all three to find out.
    x_win = win_x1 + wall + head_r
    sep = head_r + SERVO_SCREW_PILOT_MM / 2.0 + wall
    x_pilot = (tab_hi + math.sqrt(max(sep ** 2 - fix_z ** 2, 0.0))
               if sep > fix_z else tab_hi)
    fix_x = max(x_win, x_pilot)
    x_hi = fix_x + head_r + wall + margin

    m = ServoPad(
        servo_name=servo.name,
        pad_t=pad_t,
        half_z=half_z,
        x_lo=tab_lo - pad_pad,
        x_hi=x_hi,
        case_x0=win_x0, case_x1=win_x1, case_z=servo.case_w + c,
        tab_x_lo=tab_lo, tab_x_hi=tab_hi,
        pilot_d=SERVO_SCREW_PILOT_MM,
        fix_x=fix_x, fix_z=fix_z,
        fix_d=M3['clearance'], fix_head_d=head_d, fix_head_z=head_cbore,
        corner_r=corner_r,
        # ONE notch, centred, in the END wall - lib/servo.py's lead datum
        # names the face in its first sentence and five parts had it on the
        # wrong wall. If you are writing `for sz in (+1, -1)` here, stop.
        lead_key_d=servo.lead_bundle_dia + LOC,
        lead_key_l=pad_pad + (servo.tab_hole_pitch - servo.case_l) / 2.0 + 1.0,
    )

    bad = []
    if m.fix_head_z >= m.pad_t:
        bad.append('a %.2f counterbore goes straight through a %.2f pad'
                   % (m.fix_head_z, m.pad_t))
    if m.under_head < 2.0:
        bad.append('only %.2f mm of pad under the screw head' % m.under_head)
    if m.fix_x + head_r + wall > m.x_hi + 1e-9:
        bad.append('the screw head at x %.2f reaches past the pad edge at '
                   '%.2f' % (m.fix_x, m.x_hi))
    if m.fix_x - head_r - wall < m.case_x1 - 1e-9:
        bad.append('the screw head at x %.2f breaks into the servo window '
                   'ending at %.2f' % (m.fix_x, m.case_x1))
    if m.fix_z + head_r + wall > m.half_z + 1e-9:
        bad.append('the screw HEAD at z %.2f leaves under a wall to the edge '
                   'at %.2f' % (m.fix_z, m.half_z))
    for tx in (m.tab_x_lo, m.tab_x_hi):
        d = math.hypot(m.fix_x - tx, m.fix_z)
        if d < sep - 1e-9:
            bad.append('the cap screw and the tab pilot at x %.2f are %.2f '
                       'apart and a flush head plus a wall needs %.2f'
                       % (tx, d, sep))
    # The whole case travels through this window during assembly, cable and
    # all, so the window plus its END keyway has to pass case_l + bundle.
    if (servo.case_l + c + m.lead_key_l) < (servo.case_l
                                            + servo.lead_bundle_dia):
        bad.append('the window plus its end keyway will not pass the cable')
    if m.lead_key_l < (servo.tab_hole_pitch - servo.case_l) / 2.0 + pad_pad:
        bad.append('the keyway ends blind inside the pad and traps the cable')
    assert not bad, ('%s servo pad is not buildable: ' % servo.name
                     + '; '.join(bad))
    return m


J3_PAD = servo_pad(SERVOS['MG90S'])

# HOW FAR THE PAD STANDS OFF THE PLATE. This is `fa_j3_standoff`, and it is
# the whole cost of the reduction: the pinion has to land coplanar with the
# gear, so the servo must sit out by a running gap, the gear's face width,
# and the pinion's seat height on the servo, less the pad's own thickness.
# Boring the pinion THROUGH rather than blind-pocketing it is what makes
# seat_z 5.90 instead of 11.50 - see lib/gears.py.
J3_STANDOFF = FREE + J3_PAIR.face + J3_MOUNT.seat_z - J3_PAD.pad_t

# The forearm's own solve, reproduced. These are the numbers models/ builds
# today - if one of these fires, this function and the part have parted
# company and the CAP WILL NOT FIT THE PAD.
assert abs(J3_PAD.pad_t - 5.5) < 1e-9, 'fa_cap_t/fa_lobe_t is 5.5, got %.4f' % J3_PAD.pad_t
assert abs(J3_PAD.half_z - 8.8) < 1e-9, 'fa_lobe_z is 8.8, got %.4f' % J3_PAD.half_z
assert abs(J3_PAD.fix_z - 4.2) < 1e-9, 'fa_cap_screw_z is 4.2, got %.4f' % J3_PAD.fix_z
assert abs(J3_PAD.fix_x - 22.70106) < 1e-4, (
    'fa_cap_screw_y builds out at 4.90106 in the forearm frame, i.e. '
    '22.70106 in the servo frame; got %.5f' % J3_PAD.fix_x)
assert abs(J3_PAD.x_hi - 27.40106) < 1e-4, (
    'fa_cap_reach builds out at 9.60106 in the forearm frame, i.e. '
    '27.40106 in the servo frame; got %.5f' % J3_PAD.x_hi)
assert abs(J3_STANDOFF - 10.8) < 1e-9, (
    'fa_j3_standoff derives 10.8 today, got %.4f' % J3_STANDOFF)
assert J3_STANDOFF >= FREE + J3_PAIR.face - 1e-9, (
    'the pad would sit inside the band the 36T turns in')


def pad_x_to_link_y(x_mm, l2_mm, centre=None):
    """Convert a servo-frame X on the J3 pad to the FOREARM's link frame.

    The cap never needs this - it works entirely in the servo frame, which
    is the point. The FOREARM does, because it has to place the pad relative
    to its own two pivots, and it is the only part that knows L2.

    l2 stays in forearm.py deliberately: it is that link's length, read by
    nobody else's geometry, and it is not a joint interface.
    """
    c = J3_PAIR.centre_distance if centre is None else centre
    return x_mm + (-l2_mm + c)


# =========================================================================
#  4. THE GRIPCUT FINGER KEY — pruner_blade <-> gripcut_finger
# =========================================================================
# THE ONE CROSS-READ THAT WAS NEVER NEEDED. gripcut_finger.py reads
# `pb_edge_off` out of the document and asserts `pb_edge_off - gf_lead ==
# gf_af`. But three lines earlier the same file computes gf_af as
# `CHOSEN.edge_offset - 2.0` from lib/pruner_linkage, which is the identical
# object pruner_blade.py builds pb_edge_off from. The assert compares a
# number to itself by a longer route, and when the blade is absent it is
# skipped silently. Delete the read; import the module.
#
# WHAT IS GENUINELY SHARED is everything else the two parts agree about and
# NEITHER file owns: the finger rests on the carrier's outer face, its ring
# matches the carrier hub, and its anti-rotation boss enters a pocket the
# carrier cuts. Six numbers, currently typed twice - once in each script,
# with the second copy's comment naming the first ("pocket, tangential -
# gf_key_w 4.0 + loc 0.2"). A comment is not a contract.


@dataclass(frozen=True)
class FingerKey:
    """The gripcut finger's seat on a pruner blade carrier.

    Frame: the carrier's, mounted and undeflected. Origin on the pivot,
    +Y toward the nose, +X into the body away from the edge.

    carrier_thk 3.5   ASSUMED  EXTRACTED-FROM pruner_blade.py pb_thk
    half_gap 0.05     ASSUMED  EXTRACTED-FROM pruner_blade.py pb_gap - half
                               the bypass gap. The two carriers face each
                               other across 2x this and the pivot screw
                               takes it up; a scissor wants light rubbing
                               contact.
    hub_r 6.0         ASSUMED  EXTRACTED-FROM pruner_blade.py pb_hub_r. It
                               also sets how deep a stem can go, so every
                               millimetre of it is cutting force given up.
    boss_w/l/h        ASSUMED  EXTRACTED-FROM gripcut_finger.py gf_key_*
    boss_y -7.9       ASSUMED  EXTRACTED-FROM gripcut_finger.py gf_key_y -
                               on the tail, where the carrier is solid.
    lead 2.0          ASSUMED  EXTRACTED-FROM gripcut_finger.py gf_lead -
                               how far the finger leads the blade it rides.
    """

    carrier_thk: float = 3.5
    half_gap: float = 0.05
    hub_r: float = 6.0
    boss_w: float = 4.0
    boss_l: float = 3.0
    boss_h: float = 1.4
    boss_y: float = -7.9
    lead: float = 2.0
    # THE PIVOT SCREW BORE, AND IT IS WRONG IN BOTH FILES. pruner_blade
    # calls 3.2 "M3 clearance - design_rules FASTENER_MM" and
    # gripcut_finger calls the same 3.2 "M3 clearance". design_rules says
    # M3 clearance is 3.4. 3.2 is what is BUILT, so it is what is recorded
    # here rather than silently corrected - changing a pivot bore is a
    # design decision with a fit behind it, not a typo fix. Reported in
    # specs/robotarm/_decouple.md; it needs Jonathan's call.
    pivot_bore_d: float = 3.2

    @property
    def mount_z(self) -> float:
        """The face the finger rests on: the carrier's OUTER face."""
        return self.carrier_thk + self.half_gap

    @property
    def ring_od(self) -> float:
        """The finger's anchor ring matches the carrier hub."""
        return 2.0 * self.hub_r

    # The pocket is the boss plus a locational fit, on both plan dimensions.
    @property
    def pocket_w(self) -> float:
        return self.boss_w + LOC

    @property
    def pocket_l(self) -> float:
        return self.boss_l + LOC

    @property
    def pocket_d(self) -> float:
        """Pocket depth = boss height. NOT boss + fit: the boss must not
        bottom, the finger's ring face has to land on the carrier."""
        return self.boss_h

    @property
    def carrier_under_pocket(self) -> float:
        return self.carrier_thk - self.pocket_d

    def face_offset(self, edge_offset: float) -> float:
        """`gf_af` - the plane the grip face lies on. The blade's own edge
        equation with a smaller number, so the finger leads the blade."""
        return edge_offset - self.lead


GRIPCUT_KEY = FingerKey()

assert GRIPCUT_KEY.carrier_under_pocket >= MIN_WALL_MM, (
    'the key pocket leaves %.2f of carrier under it - below the %.2f wall'
    % (GRIPCUT_KEY.carrier_under_pocket, MIN_WALL_MM))
assert abs(GRIPCUT_KEY.mount_z - 3.55) < 1e-9, (
    'gf_mount_z is 3.55 and this derives %.3f' % GRIPCUT_KEY.mount_z)
assert abs(GRIPCUT_KEY.ring_od - 12.0) < 1e-9, (
    'gf_ring_od is 12.0 and this derives %.3f' % GRIPCUT_KEY.ring_od)
assert abs(GRIPCUT_KEY.pocket_w - 4.2) < 1e-9 and \
       abs(GRIPCUT_KEY.pocket_l - 3.2) < 1e-9, (
    'pb_key_w/pb_key_l are 4.2/3.2 and this derives %.3f/%.3f'
    % (GRIPCUT_KEY.pocket_w, GRIPCUT_KEY.pocket_l))
assert GRIPCUT_KEY.pivot_bore_d < GRIPCUT_KEY.ring_od - 2 * MIN_WALL_MM, (
    'the anchor ring has under a wall around the pivot bore')

# THE ONE CROSS-READ THAT SIMPLY DISSOLVES. gripcut_finger.py computes its
# grip-face plane as `CHOSEN.edge_offset - 2.0` and then reads `pb_edge_off`
# out of the document to assert the two agree - but pruner_blade builds
# pb_edge_off from the SAME CHOSEN. It is one import, stated once, here.
from lib.pruner_linkage import CHOSEN as _LINK  # noqa: E402

GRIPCUT_FACE_OFFSET = GRIPCUT_KEY.face_offset(_LINK.edge_offset)
assert abs(GRIPCUT_FACE_OFFSET - 1.5) < 1e-9, (
    'gf_af builds out at 1.5 and this derives %.3f' % GRIPCUT_FACE_OFFSET)


# =========================================================================
#  WHAT THIS FILE DOES NOT OWN, STATED SO NOBODY GOES LOOKING
# =========================================================================
# fa_l2, ua_l1        LINK LENGTHS, not joint interfaces. They belong to
#                     their own parts; lib/arm_budget.py is the authority on
#                     what they cost. `pad_x_to_link_y` above is the only
#                     bridge either of them needs.
# ua_drum_r's waist,  the upper arm's SECTION. Nothing else touches it.
# fa_waist_t/_z
# the tooth pair      lib/gears.py J3_PAIR, and the pinion's seat on the
#                     servo, lib/gears.py J3_HUB / J3_MOUNT.
# the servo envelope  lib/servo.py. This file consumes it; it never restates
#                     a case dimension.
# the bearing         lib/bearings.py B608ZZ. BearingSeat above says who
#                     touches which RACE, which is the joint, not the part.
# sty_*               specs/robotarm/_style.md, via lib/palette.py.
#
# STILL OUTSTANDING, and NOT fixed by this file: _preview_arm.py poses the
# arm from 19 document user parameters, which is why _build_assembly.py
# cannot build a REFERENCED assembly. Four of those 19 are now derivable
# from here (fa_plate_in, fa_plate_out, fa_j3_standoff, fa_j3_centre) and
# ua_half_x / ua_socket_d make six. The remaining thirteen are turntable,
# shoulder and pruner datums that want the same treatment in a second pass.
