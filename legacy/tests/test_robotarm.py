"""robotarm project invariants — the cross-part relationships that
tests/test_invariants.py cannot see, because they only exist when parts are
stacked into an assembly.

These are properties that must hold for ANY parameter choice, not golden
values: if someone widens the base or moves the rollers, these still describe
what has to remain true for the thing to bolt together.
"""

import math
import sys
from importlib import util as importlib_util
from pathlib import Path

import pytest

from lib.bearings import B608ZZ

REPO_ROOT = Path(__file__).resolve().parent.parent
ROBOTARM = REPO_ROOT / "models" / "robotarm"
sys.path.insert(0, str(ROBOTARM))


def _load(name: str):
    py = ROBOTARM / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


frame = _load("_frame")


def test_rollers_clear_the_rim():
    """The 608s must sit entirely above the platter rim, or the fork would
    have to reach below the surface the cap bolts down to."""
    assert frame.Z_ROLLER_FLOOR >= frame.Z_RIM, (
        f"roller slot floor {frame.Z_ROLLER_FLOOR} is below the rim "
        f"{frame.Z_RIM} — raise CAP_H"
    )


def test_race_plane_is_the_horn_face():
    """The turntable rides on the rollers AND sits on the base servo's horn;
    those two planes are the same plane or the drive binds."""
    assert frame.Z_RACE == pytest.approx(
        frame.Z_FLANGE + frame.BASE_SERVO.horn_face)
    assert frame.Z_AXLE == pytest.approx(frame.Z_RACE - B608ZZ.radius)


def test_base_servo_case_clears_the_bay_floor():
    case_bottom = frame.Z_FLANGE - frame.BASE_SERVO.below_flange
    assert case_bottom > frame.FLOOR_T, (
        f"base servo case bottom {case_bottom} is inside the "
        f"{frame.FLOOR_T} mm floor"
    )


def test_breadboard_fits_the_bay():
    assert frame.breadboard_corner_r() < frame.INNER_R, (
        "breadboard corners fall outside the bay wall"
    )
    assert frame.BREADBOARD_X0 >= frame.COLUMN_OUTER_X / 2, (
        "breadboard overlaps the servo column"
    )
    assert frame.BAY_H >= frame.BREADBOARD_STACK_H, (
        "bay is shallower than the breadboard + ESP32 stack"
    )


def test_rollers_miss_the_servo_case():
    """Each roller slot must clear the base servo's case footprint. The case
    is offset along Y, so this is not automatic for evenly spaced rollers."""
    half_x = frame.COLUMN_INNER_X / 2
    y_lo = frame.COLUMN_Y - frame.COLUMN_INNER_Y / 2
    y_hi = frame.COLUMN_Y + frame.COLUMN_INNER_Y / 2
    slot_half_w = frame.FORK_GAP / 2 + frame.FORK_WALL_T
    inner_r = frame.ROLLER_PITCH_R - B608ZZ.radius - 3.5
    for az in frame.ROLLER_AZIMUTHS:
        a = math.radians(az)
        radial = (math.cos(a), math.sin(a))
        perp = (-math.sin(a), math.cos(a))
        for side in (-1.0, 1.0):
            x = inner_r * radial[0] + side * slot_half_w * perp[0]
            y = inner_r * radial[1] + side * slot_half_w * perp[1]
            inside = abs(x) < half_x and y_lo < y < y_hi
            assert not inside, (
                f"roller at {az} deg cuts into the base servo pocket at "
                f"({x:.1f}, {y:.1f})"
            )


def test_cap_bolts_miss_the_breadboard_and_the_rollers():
    for az in frame.CAP_BOLT_AZ:
        x = frame.CAP_BOLT_R * math.cos(math.radians(az))
        assert x < frame.BREADBOARD_X0, (
            f"cap bolt at {az} deg lands under the breadboard"
        )
        gap = min(abs((az - r + 180) % 360 - 180)
                  for r in frame.ROLLER_AZIMUTHS)
        assert gap > 20.0, f"cap bolt at {az} deg is under a roller fork"


def test_link_channels_clear_their_servo_stacks():
    """A link straddles the servo driving it: horn seat outboard + case
    inboard + the far wall have to fit inside the channel."""
    for name, servo, width in (
        ("LINK_CHANNEL_W", frame.ELBOW_SERVO, frame.LINK_CHANNEL_W),
        ("SHOULDER_CHANNEL_W", frame.SHOULDER_SERVO,
         frame.SHOULDER_CHANNEL_W),
    ):
        needed = frame.channel_width(servo)
        assert width >= needed, (
            f"{name} {width} < {needed:.1f} needed to straddle "
            f"the {servo.name}"
        )


def test_turntable_has_material_over_the_horn_pocket():
    from lib.design_rules import MIN_WALL_MM
    pocket_depth = frame.BASE_SERVO.horn_thick + 0.2
    remaining = frame.TURNTABLE_T - pocket_depth
    assert remaining >= MIN_WALL_MM, (
        f"only {remaining:.1f} mm of disc above the horn pocket"
    )


def test_servos_fit_with_their_leads_on():
    """A pocket cut to the bare case is useless: the lead leaves the side of
    the case, so the wire gets pinched and the servo will not seat."""
    check = _load("_check_fit")
    assert check.main() == 0, "see the printed failures above"


def test_roller_axles_point_at_the_hub():
    """The disc's surface moves TANGENTIALLY over each roller, so the roller
    axis must be RADIAL for it to roll. Tangential axles look plausible and
    scrub instead — the contact would try to travel radially while the disc
    moves the other way. Probed on the built cap: the fork WALLS must be
    fore-and-aft along the radius, and the slot open tangentially.
    """
    from build123d import Box, Part, Pos, Rotation
    from typing import cast

    cap = _load("turret_cap").build()
    off = frame.FORK_GAP / 2 + frame.FORK_WALL_T / 2      # into a wall
    # just ABOVE the axle bore — probing at the bore's own height only finds
    # the hole, whichever way the fork is turned
    z = frame.Z_AXLE - frame.Z_RIM + frame.AXLE_HOLE_DIA / 2 + 1.5

    def solid_at(dx_radial, dy_tangential):
        probe = cast(Part, Rotation(0, 0, frame.ROLLER_AZIMUTHS[0])
                     * Pos(frame.ROLLER_PITCH_R + dx_radial, dy_tangential, z)
                     * Box(1.2, 1.2, 1.2))
        hit = cast(Part, cap & probe)
        return bool(hit.solids()) and hit.volume > 0.3

    for side in (-1.0, 1.0):
        assert solid_at(side * off, 0.0), (
            "no fork wall fore/aft along the RADIUS — the axle is not radial, "
            "so the rollers would scrub instead of rolling"
        )
        assert not solid_at(0.0, side * off), (
            "fork wall found tangentially — the forks are turned 90 deg"
        )


def test_base_stack_assembles_without_interference():
    """Full geometric check: builds all four base parts and intersects them."""
    check = _load("_check_assembly")
    assert check.main() == 0, "see the printed failures above"


def test_upper_arm_seats_and_swings_on_the_shoulder():
    """Each link is a valid solid on its own; that says nothing about whether
    it goes onto the bracket. This mates them and sweeps the joint."""
    check = _load("_check_arm")
    assert check.main() == 0, "see the printed failures above"


def test_arm_holds_its_own_weight():
    """Servo duty and material stress at every joint, from the parts' REAL
    volumes and centres of mass. Anything that moves mass outboard has to be
    re-checked here — the elbow has set the payload ceiling all along."""
    check = _load("_check_loads")
    assert check.main() == 0, "see the printed failures above"


def test_wrist_rolls_and_carries_its_load():
    """The servo has to go into the forearm's tip nose-first WITH its horn
    on, the rotator has to turn a full circle clear of the link, and its
    skirt has to actually lap the journal boss — without that lap the whole
    effector hangs off a 4.8 mm servo shaft."""
    check = _load("_check_wrist")
    assert check.main() == 0, "see the printed failures above"


def test_hand_racks_mesh_and_stay_symmetric():
    """One pinion, two racks, and they must stay exactly mirrored while
    clearing the base at every opening."""
    check = _load("_check_hand")
    assert check.main() == 0, "see the printed failures above"


def test_finger_roots_cannot_foul_each_other():
    """Each finger's root has to swallow the SG90's 32 mm cross horn, so it
    is an 18 mm disc — and two of those cannot be closer than 36 mm apart.
    That, not styling, is what sets the pivot spacing."""
    hand = _load("_hand")
    assert 2 * hand.PIVOT_X >= 2 * hand.ROOT_R, (
        f"pivots {2 * hand.PIVOT_X} mm apart but the roots are "
        f"{2 * hand.ROOT_R} mm across — they would collide"
    )


def test_finger_horn_pocket_goes_right_through():
    """Finger R is finger L turned over, so a blind pocket would end up on
    the wrong face. Probe the built solid on BOTH faces at the horn."""
    from build123d import Box, Pos

    hand = _load("_hand")
    finger = _load("hand_finger").build()
    for z in (0.2, hand.FINGER_T - 0.2):
        probe = Pos(0, 0, z) * Box(hand.FINGER_R * 0.6, 2.0, 0.2)
        hit = finger & probe
        assert hit is None or hit.volume < 0.01, (
            f"the horn pocket does not break out at z={z} — the flipped "
            f"finger will not sit on its horn"
        )


def test_wrist_bracket_bolts_through_the_link():
    """wrist_mount is only as strong as those two bolts, and they have to
    pass through BOTH its saddle walls and both of the link's side plates.
    The check measures material round each bolt in each part."""
    check = _load("_check_wrist")
    assert check.main() == 0, "see the printed failures above"


def test_both_effectors_share_the_rotator_bolt_circle():
    """hand_base and scissor_cradle must be interchangeable on the wrist.
    They only are if both carry the SAME four clearance holes, so this
    probes the BUILT solids for material-free holes at every bolt position
    rather than trusting two copies of a constant."""
    from build123d import Cylinder, Pos, Rotation

    rotator = _load("wrist_rotator").build()
    for az in frame.EFFECTOR_BOLT_AZ:
        probe = (Rotation(0, 0, az) * Pos(frame.EFFECTOR_BOLT_R, 0, 3.0)
                 * Cylinder(0.6, 4.0))
        hit = rotator & probe
        assert hit is None or hit.volume < 0.01, (
            f"wrist_rotator has no insert hole at {az} deg"
        )
