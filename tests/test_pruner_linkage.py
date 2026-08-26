"""The pruner linkage has to keep its promises or the head cannot cut."""

import math

from lib.pruner_linkage import CHOSEN, cut_force_N, rack_force_N, stem_mm  # noqa: F401


def test_tail_clears_the_pinion_through_the_whole_sweep():
    ok, clear = CHOSEN.clears_pinion(0.0)
    assert ok, 'the tail fouls the pinion'
    assert clear >= 1.0, 'only %.2f mm of clearance' % clear


def test_tail_stays_inside_the_clamshell():
    ok, clear = CHOSEN.within_shell(22.0, -32.0)
    assert ok and clear >= 1.0, 'tail leaves the shell (%.2f mm)' % clear


def test_rack_travel_fits_what_the_servo_can_sweep():
    """The gripper uses 127 deg of the SG90's 180. The pruner buys its
    advantage by using the rest - but it cannot use more than all of it."""
    from lib.pruner_linkage import R_PITCH_MM
    deg = math.degrees(CHOSEN.rack_travel_mm / R_PITCH_MM)
    assert deg <= 175.0, 'needs %.0f deg of servo sweep' % deg


def test_closed_form_advantage_matches_the_differentiated_kinematics():
    """`ma()` is a closed form; `ma_numeric()` differentiates the real slot
    kinematics. If they disagree, one of them has the wrong relation between
    rack travel and blade angle - which has happened twice."""
    assert abs(CHOSEN.ma(CHOSEN.throat_r) - CHOSEN.ma_numeric(0.0)) < 1e-4


def test_the_pin_stays_inside_a_RADIAL_slot():
    """A radial slot means the pin sits on the line through the pivot at the
    blade's angle, so s = tail_r tan(theta). Using sin instead puts the pin
    1.5 mm sideways of the slot centreline at full sweep - through the wall.
    """
    import math as _m
    worst = 0.0
    for i in range(-40, 41):
        s = CHOSEN.rack_travel_mm / 2 * i / 40.0
        th = CHOSEN.theta_for_travel(s)
        # pin in blade-local coords: rotate (s, -tail_r) by -theta
        c, sn = _m.cos(-th), _m.sin(-th)
        x_l = s * c - (-CHOSEN.tail_r) * sn
        worst = max(worst, abs(x_l))
    assert worst < 1e-9, 'pin wanders %.3f mm off the slot centreline' % worst


def test_throat_opens_far_enough_for_a_house_plant_stem():
    assert CHOSEN.throat_open_mm >= 7.0


def test_the_edges_do_NOT_pass_through_the_pivot():
    """Two straight edges through one pivot cross at the pivot and nowhere
    else, and at closure they go coincident along their whole length at once.
    That is a V-pinch: the entire stem section shears in one instant, with no
    travelling contact and no scissor advantage at all. The first build of
    this head had exactly that. An offset edge is not a refinement."""
    assert CHOSEN.edge_offset > 0.0


def test_there_is_exactly_one_crossing_and_it_sweeps_monotonically():
    import math as _m
    last = None
    for deg in range(3, int(CHOSEN.half_sweep_deg) + 1):
        r = CHOSEN.crossing_r(_m.radians(deg))
        assert r > 0 and r != float('inf')
        if last is not None:
            assert r < last, 'crossing did not move inward at %d deg' % deg
        last = r


def test_the_mouth_admits_a_house_plant_stem():
    assert CHOSEN.throat_open_mm >= 6.0, (
        'mouth opens only %.1f mm' % CHOSEN.throat_open_mm)


def test_the_cut_reaches_deep_enough_to_be_worth_it():
    """Advantage climbs as the crossing sweeps in, so what matters is how deep
    it can get before the sweep runs out."""
    import math as _m
    deepest = CHOSEN.crossing_r(_m.radians(CHOSEN.half_sweep_deg))
    assert deepest <= 5.5, 'crossing only reaches r = %.1f' % deepest


def test_force_deep_in_the_throat_clears_a_soft_stem():
    from lib.pruner_linkage import rack_force_N
    f = rack_force_N() * CHOSEN.ma_at_cut(7.5)
    assert stem_mm(f, 2.0) >= 6.0, 'only %.1f mm at x2 progression' % stem_mm(f, 2.0)


def test_advantage_falls_off_toward_the_tip():
    """Real pruners are strong at the throat and weak at the tip. If this ever
    inverts, the pivot and the throat have swapped and the geometry is wrong."""
    assert CHOSEN.ma(CHOSEN.throat_r) > CHOSEN.ma(CHOSEN.tip_r) * 2


def test_cuts_a_soft_stem_on_the_pessimistic_progression():
    f = rack_force_N() * CHOSEN.ma_at_cut(CHOSEN.throat_r)
    assert stem_mm(f, 2.0) >= 5.0, 'only %.1f mm at x2 progression' % stem_mm(f, 2.0)


def test_rack_force_is_what_the_spec_claims():
    assert abs(rack_force_N() - 8.5) < 0.2


def test_drive_pin_is_clear_of_the_pinion_disc():
    """The pinion is centred on y = 0 with an 8 mm face, so its disc ends at
    y = +4. The gripper's jaw arm clears it by 0.4; so must this pin."""
    from lib.pruner_linkage import ARM_CLEAR_MM, FACE_MM, PIN_DIA_MM
    back_edge = CHOSEN.pivot_y - CHOSEN.tail_r - PIN_DIA_MM / 2
    assert back_edge >= FACE_MM / 2 + ARM_CLEAR_MM, (
        'drive pin back edge at y = %.1f, inside the pinion disc' % back_edge)


def test_the_tail_END_is_clear_of_the_pinion_disc():
    """Not the pin - the tail runs past it to close the slot, and that end is
    6.3 mm further back."""
    from lib.pruner_linkage import ARM_CLEAR_MM, FACE_MM
    tail_end = CHOSEN.pivot_y - CHOSEN.tail_r - CHOSEN.tail_past_pin_mm
    assert tail_end >= FACE_MM / 2 + ARM_CLEAR_MM, (
        'blade tail ends at y = %.1f, inside the pinion disc' % tail_end)
