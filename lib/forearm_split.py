"""Forearm split — the one derivation the three printed pieces share.

THE FOREARM IS NO LONGER ONE PRINTED PART. It is a +X side plate, a -X side
plate and two copies of one box-beam rail, and the reason is measured, not
stylistic: as a single body it wants 2391 mm2 of support and 918 mm2 of that
is one face — the +X plate's inner face, floating 43 mm up over the straddle
on nothing but the rails. Support goes into that straddle and comes back out
through a 24.8 mm slot 43 mm deep, and the face it scars on the way is
fa_plate_in, which IS the J4 running gap. specs/robotarm/_forearm_print.md
carries the numbers and the six-orientation sweep behind that sentence.

WHY THE SPLIT IS AT THE PLATE INNER FACES AND NOT AT x = 0. The obvious
plane is the middle, the way wrist_roll was split. It was measured and it
does not work: with the seam at x = 0 each half still contains half the
straddle, so each half still floats its own plate — 1194 mm2 for the +X half
at best, 1083 mm2 for the -X half. Splitting in the middle halves the DROP
and changes nothing else.

What actually fixes it is the observation that a side plate is a horizontal
slab when it is built along X, and a slab prints perfectly if it is the FIRST
LAYER and impossibly if it is not. So each plate is split off at its own
inner face and printed INNER FACE DOWN, where the plate itself is the bed:
1030 and 1084 mm2 of first layer. Everything outboard of it - boss, servo
seat, servo lobe, standoff - is narrower than the plate and lands on it, and
every pocket that used to be a roof now opens at the top of the build.

THE PRICE OF THAT IS THE THIRD PIECE, and it is forced rather than chosen.
Nothing that reaches across the straddle can belong to a plate that prints
inner-face-down, because "across the straddle" means "below the bed". So the
box-beam rails become their own printed piece. They are a PRISM along X -
every face parallel to the build axis, every hole down it - so they print
with zero overhang in that orientation, which is the one thing in this whole
part that is easy.

The two rails are the same solid. The straddle is symmetric in Z about the
arm's centreline and so are both sweep cylinders, so the bottom rail is the
top rail turned 180 degrees about Y. That is a ROTATION, not a reflection, so
there is no handedness to get wrong and no second part file - unlike
wrist_roll, whose two halves are mirror images.

WHAT THIS MODULE IS. Arithmetic and the checks the arithmetic has to
survive, and nothing else - it does not import Fusion and can be argued with
from a terminal. It holds the derivations that MORE THAN ONE of the four
scripts needs, so that the silhouette the plates are cut from, the seat the
servo blocks stand on and the seam they all bolt through exist once. The
project's recurring failure is a datum only one file reads; this is the
answer to that for the forearm, the way lib/gears.py is for the elbow.

IT DOES NOT OWN THE NUMBERS, ONLY THE SOLVE. forearm.py still declares every
fa_* user parameter, because wrist_hub.py, j3_servo_cap.py, _check_leads.py
and _check_servo_fit.py all read them out of the document by name. Each
script passes what it read into these solvers rather than re-deriving it, so
there is one arithmetic and several readers instead of four copies drifting.

Provenance: every value here is DERIVED from its arguments. The arguments
themselves are graded where they are declared, in forearm.py.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from lib.design_rules import MIN_WALL_MM

# Sampling density for the "is this inside the outline" probes below. A
# COUNT, not a dimension: the concave waist arc is thinnest in the MIDDLE of
# a span, so checking a span's two ends can pass a feature that breaks out
# between them, and nothing in a CAD UI should be able to make that check
# coarser.
PROBE_N = 100

# Names and print orientation of the three printed pieces, so that the spec,
# the exporter and the scripts cannot disagree about what exists.
PIECES = {
    'forearm_px': 'inner face (x = +fa_plate_in) on the bed, built along +X',
    'forearm_nx': 'inner face (x = -fa_plate_in) on the bed, built along -X',
    'forearm_rail': 'either end face on the bed, built along X - a prism; '
                    'printed TWICE, the second copy turned 180 deg about Y',
}


@dataclass(frozen=True)
class Silhouette:
    """The connecting-rod outline both plates are cut from.

    A circle of `boss_r` at each pivot, joined by two concave arcs tangent to
    both, sized so the outline is exactly `waist_z` half-tall in the middle.
    The pivots are at y = 0 (J4) and y = -l2 (J3).

    This is the shape forearm.py's link_profile() draws. It lives here as
    well because BOTH plates are cut from it and every feature either plate
    puts near the edge - the servo seats, the seam screw heads - has to be
    checked against it. A second hand-rolled copy of this arc is exactly the
    drift this module exists to stop.
    """

    l2: float
    boss_r: float
    waist_z: float

    @property
    def mid_y(self) -> float:
        return -self.l2 / 2.0

    @property
    def arc_r(self) -> float:
        """Radius of the concave arc tangent to both bosses.

        From h = arc_r + waist_z and h^2 = (arc_r + boss_r)^2 - (l2/2)^2.
        """
        num = self.boss_r ** 2 - (self.l2 / 2.0) ** 2 - self.waist_z ** 2
        den = 2.0 * (self.waist_z - self.boss_r)
        return num / den

    @property
    def arc_h(self) -> float:
        """Height of the concave arc's centre above the centreline."""
        return math.sqrt((self.arc_r + self.boss_r) ** 2 - (self.l2 / 2.0) ** 2)

    def half_z(self, y: float) -> float:
        """Half-height of the outline at y. Zero outside it."""
        best = 0.0
        for cy in (0.0, -self.l2):
            d = abs(y - cy)
            if d < self.boss_r:
                best = max(best, math.sqrt(self.boss_r ** 2 - d ** 2))
        if -self.l2 <= y <= 0.0:
            best = max(best,
                       self.arc_h
                       - math.sqrt(self.arc_r ** 2 - (y - self.mid_y) ** 2))
        return best

    def contains_band(self, y_lo: float, y_hi: float, half: float) -> bool:
        """Is a rectangle y_lo..y_hi by +/- half inside the outline?

        Probed across the whole span, not at its ends - see PROBE_N.
        """
        for i in range(PROBE_N + 1):
            y = y_lo + (y_hi - y_lo) * i / PROBE_N
            if self.half_z(y) < half:
                return False
        return True

    def validate(self) -> list[str]:
        bad = []
        if self.waist_z >= self.boss_r:
            bad.append('waist_z %.2f is not under boss_r %.2f - the outline '
                       'would have to bulge, not pinch'
                       % (self.waist_z, self.boss_r))
        if self.arc_r <= 0.0:
            bad.append('no concave arc joins these bosses: arc_r %.2f'
                       % self.arc_r)
        if abs((self.arc_h - self.arc_r) - self.waist_z) > 1e-9:
            bad.append('the arc delivers a %.4f waist, not %.4f'
                       % (self.arc_h - self.arc_r, self.waist_z))
        if 2.0 * self.boss_r >= self.l2:
            bad.append('the two pivot bosses overlap at l2 %.2f' % self.l2)
        return bad


@dataclass(frozen=True)
class Seat:
    """The plate, at full thickness, under a servo block.

    Both servo blocks are drawn to land on a `plate_t` plate and sink
    `lobe_over` into it, but the plate is only `plate_t` inside the boss
    circles - everywhere else it is `waist_t`. The gap between those two
    faces is the air each block was bridging. See forearm.py's fa_lobe_seat.
    """

    plate_t: float
    waist_t: float
    lobe_over: float
    lobe_z: float
    wall: float
    boss_r: float

    @property
    def depth(self) -> float:
        """Seat depth, measured IN from the plate outer face.

        The full plate, less the waist already there, plus one `lobe_over` so
        the seat OVERLAPS the web at one end and the block at the other
        instead of meeting either on a bare plane - which is non-manifold and
        fails the fillet later.
        """
        return self.plate_t - self.waist_t + self.lobe_over

    @property
    def air(self) -> float:
        """What was actually under the block before the seat existed.

        The block starts one `lobe_over` inside the plate outer face and the
        waist ends `waist_t` outside the plate inner face; the gap between
        those two is what it was bridging. NOT `depth - lobe_over`: the seat
        spends a `lobe_over` at EACH end, one overlapping the web and one
        overlapping the block, and only the middle of it was ever air.
        """
        return self.plate_t - self.waist_t - self.lobe_over

    @property
    def half_z(self) -> float:
        """One wall inside the block, so the seat shares no edge with it.

        At the block's full half-height the seat would be coplanar with the
        block's top and bottom faces and would EXTEND the corner edges the
        finish phase fillets, off the block and out onto the web's curved
        silhouette face, where a round-over has nowhere to run out.
        """
        return self.lobe_z - self.wall

    @property
    def y_max(self) -> float:
        """+Y limit: where the boss circle falls to the BLOCK's half-height.

        Derived from `lobe_z` and not from `half_z`, and that is not an
        oversight. The y at which the circle falls to `half_z` is a tangency
        with zero margin, and a user parameter written to five decimals
        rounds - it rounded UP by 4.5e-6 mm, which puts the seat's own corner
        outside the circle it came from and fails the outline probe. Stopping
        where the boss can still carry a FULL block height leaves exactly one
        `wall` of margin, by construction, at every y the seat reaches.
        """
        return math.sqrt(self.boss_r ** 2 - self.lobe_z ** 2)

    def validate(self) -> list[str]:
        bad = []
        if self.depth <= self.lobe_over:
            bad.append('the seat is %.2f deep against a %.2f overlap - the '
                       'waist already reaches the block'
                       % (self.depth, self.lobe_over))
        if self.half_z < MIN_WALL_MM:
            bad.append('seat half-height %.2f is under one wall'
                       % self.half_z)
        if self.boss_r <= self.lobe_z:
            bad.append('boss_r %.2f does not exceed lobe_z %.2f - no y_max '
                       'exists' % (self.boss_r, self.lobe_z))
        elif self.boss_r ** 2 - self.lobe_z ** 2 <= 0.0:
            bad.append('y_max is not real')
        return bad


@dataclass(frozen=True)
class Straddle:
    """The gap between the plates, and what is allowed to live in it.

    Two cylinders are subtracted from everything inside: `sweep_r` about J4
    (the roll housing swings there) and `elbow_clear` about J3 (the upper arm
    does). What survives is the only material that may cross from one plate
    to the other, and it is what the rails are cut from.
    """

    l2: float
    sweep_r: float
    elbow_clear: float

    @property
    def on_axis(self) -> float:
        """Web left on the arm's centreline where the two swings nearly
        meet. forearm.py asserts this against one wall."""
        return self.l2 - self.sweep_r - self.elbow_clear

    def rail_span(self, z: float) -> tuple[float, float]:
        """(y_lo, y_hi) of the material that survives both sweeps at height z.

        The J4 sweep bounds it from the wrist end and the J3 sweep from the
        elbow end. Both circles narrow with |z|, so the span WIDENS as the
        rail gets taller - which is why the seam screws go as high as their
        heads allow rather than on the centreline.
        """
        y_hi = -math.sqrt(max(self.sweep_r ** 2 - z ** 2, 0.0))
        y_lo = -self.l2 + math.sqrt(max(self.elbow_clear ** 2 - z ** 2, 0.0))
        return y_lo, y_hi

    def validate(self) -> list[str]:
        if self.on_axis < MIN_WALL_MM:
            return ['the two sweeps leave %.2f mm on the centreline at '
                    'l2 %.2f - under one wall' % (self.on_axis, self.l2)]
        return []


@dataclass(frozen=True)
class Seam:
    """Where a side plate bolts to a rail — solved, not chosen.

    THE SEAM IS THE ONE THING THE SPLIT ADDS, so nothing about it is a
    preference. Four numbers pin it and each of them binds:

      - the screw head has to stay inside the link OUTLINE, because at the
        rail's y station the plate is only the waist and the head lands on
        its outer face, in free air where nothing sweeps. That caps the
        screw height at waist_z - head_r - margin.
      - the pilot has to stay inside the RAIL, one wall from the duct below
        it. That sets how deep the duct may be, which is the same thing as
        how tall the rail is.
      - the rail's LENGTH at the screw height comes from the two sweeps, and
        it is what decides whether two screws fit at all.
      - and the walls between and either side of those two screws have to be
        a wall each, which is the check that closes the loop.

    So the duct stops being a styling number and becomes what is left of the
    link once the seam fastener has taken its room: `duct_z` below is
    DERIVED, where forearm.py used to type 9.0.
    """

    silhouette: Silhouette
    straddle: Straddle
    waist_z: float
    wall: float
    head_d: float
    pilot_d: float
    margin: float

    @property
    def z(self) -> float:
        """Screw axis height. As high as a head inside the outline allows,
        because the pair carries the plate-to-rail couple and wants the
        longest lever it can get. Measured against `waist_z`, the outline's
        MINIMUM half-height, so it is safe at every y."""
        return self.waist_z - self.head_d / 2.0 - self.margin

    @property
    def duct_z(self) -> float:
        """Half-height of the cable duct = the rail's inner face.

        DERIVED from the fastener that has to live in the rail above it: the
        screw axis, less half a pilot, less one wall of floor.
        """
        return self.z - self.pilot_d / 2.0 - self.wall

    @property
    def rail_z(self) -> float:
        """Rail height. What is left of the link outline above the duct."""
        return self.waist_z - self.duct_z

    @property
    def span(self) -> tuple[float, float]:
        """The rail's y extent at the screw height."""
        return self.straddle.rail_span(self.z)

    @property
    def wall_between(self) -> float:
        """Equal walls: two pilots share the span with three walls."""
        y_lo, y_hi = self.span
        return ((y_hi - y_lo) - 2.0 * self.pilot_d) / 3.0

    @property
    def pilots(self) -> tuple[float, float]:
        """The two screw stations in y, walls equalised across the span."""
        y_lo, y_hi = self.span
        w = self.wall_between
        return (y_lo + w + self.pilot_d / 2.0,
                y_hi - w - self.pilot_d / 2.0)

    def head_clearance(self) -> float:
        """Smallest gap between a screw head and the link outline, over the
        two stations. Positive means both heads are inside the part."""
        return min(self.silhouette.half_z(y) - self.z - self.head_d / 2.0
                   for y in self.pilots)

    def validate(self) -> list[str]:
        bad = []
        if self.duct_z <= 0.0:
            bad.append('the seam fastener has eaten the whole duct: '
                       'duct_z %.2f' % self.duct_z)
        if self.rail_z < self.pilot_d + 2.0 * self.wall:
            bad.append('rail %.2f tall cannot hold a %.2f pilot with a wall '
                       'each side' % (self.rail_z, self.pilot_d))
        if self.wall_between < self.wall:
            y_lo, y_hi = self.span
            bad.append('the rail is %.2f long at z %.2f and two %.2f pilots '
                       'leave %.2f of wall against a %.2f minimum - the seam '
                       'does not fit two screws'
                       % (y_hi - y_lo, self.z, self.pilot_d,
                          self.wall_between, self.wall))
        if self.head_clearance() < 0.0:
            bad.append('a seam screw head stands %.3f mm proud of the link '
                       'outline' % -self.head_clearance())
        return bad


@dataclass(frozen=True)
class ServoBlock:
    """Where one servo's case, tab screws and mounting block sit along Y.

    THIS IS THE THIRD COPY OF THIS ARITHMETIC AND IT IS MEANT TO BE THE LAST.
    forearm.py worked it out for both lobes, j3_servo_cap.py worked it out
    again for the cap, and forearm_px.py would have been a fourth - which is
    how the project lost `shaft_from_end` and the lead datum. The shaft sits
    `shaft_end` in from the NEAR end of the case, so the near end is upstream
    of the pivot and the case runs away from it; `run` is +1 or -1 and says
    which way along Y that is.

    `lobe_pad` is the material left past the OUTERMOST tab screw, and it is
    not a round number - it is derived in forearm.py from the flange recess,
    which reaches further along Y than the tab screws do.
    """

    y_pivot: float
    run: float
    shaft_end: float
    case_l: float
    tab_pitch: float
    lobe_pad: float

    @property
    def case(self) -> tuple[float, float]:
        """(lo, hi) of the servo case along Y, ordered."""
        near = self.y_pivot - self.run * self.shaft_end
        far = near + self.run * self.case_l
        return min(near, far), max(near, far)

    @property
    def near_face(self) -> float:
        """The case's SHORT END FACE at the shaft end — the face the lead
        bundle leaves from, and so where the keyway has to start."""
        return self.y_pivot - self.run * self.shaft_end

    @property
    def screws(self) -> tuple[float, float]:
        y0, y1 = self.case
        mid = (y0 + y1) / 2.0
        return mid - self.tab_pitch / 2.0, mid + self.tab_pitch / 2.0

    @property
    def span(self) -> tuple[float, float]:
        """(lo, hi) of the mounting block: one pad past each tab screw."""
        a, b = self.screws
        return min(a, b) - self.lobe_pad, max(a, b) + self.lobe_pad

    def validate(self) -> list[str]:
        bad = []
        if self.run not in (1.0, -1.0, 1, -1):
            bad.append('run is %r, not +1 or -1' % (self.run,))
        if self.tab_pitch <= self.case_l:
            bad.append('tab_pitch %.2f is inside the case %.2f - the screws '
                       'would land on the case, not past it'
                       % (self.tab_pitch, self.case_l))
        if self.lobe_pad <= 0.0:
            bad.append('lobe_pad %.2f leaves nothing past the outer screw'
                       % self.lobe_pad)
        return bad
