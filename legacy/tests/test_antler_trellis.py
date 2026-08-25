"""Spec-level checks for the antler trellis (specs/trellis/antler_trellis.md).

Geometry invariants (validity, envelope, export) are covered by
test_invariants.py; these pin the interface numbers and the structural
assumptions the two model files share, without building geometry.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "models" / "trellis"))

import _antler_common as ac
import antler_hub
from lib.design_rules import (
    MIN_WALL_MM,
    PRESS_FIT_CLEARANCE_MM,
    SLIDING_FIT_CLEARANCE_MM,
)
from lib.limb import path_length, tangents, vdot


def test_stem_slides_into_port():
    stem_od = antler_hub.PORT_HOLE_DIA_MM - SLIDING_FIT_CLEARANCE_MM
    assert math.isclose(stem_od, 49.75)


def test_ring_wall_meets_minimum():
    wall = (antler_hub.PORT_HOLE_DIA_MM - SLIDING_FIT_CLEARANCE_MM
            - antler_hub.CUP_BORE_ID_MM) / 2
    assert wall >= MIN_WALL_MM


def test_cup_wedges_in_bore():
    """Flexible Ø50 cup must be squeezed by the bore, not rattle in it."""
    squeeze = 50.0 - antler_hub.CUP_BORE_ID_MM
    assert 2.0 <= squeeze <= 8.0


def test_joint_is_press_fit():
    socket_d = ac.SPIGOT_D + PRESS_FIT_CLEARANCE_MM
    assert math.isclose(socket_d - ac.SPIGOT_D, PRESS_FIT_CLEARANCE_MM)
    assert ac.SOCKET_DEPTH >= ac.SPIGOT_LEN + 1  # spigot bottoms on glue, not air


def test_socket_wall_meets_minimum():
    """Beam wall around the socket at the split (oval minor radius)."""
    pts, radii = ac.sampled_beam(500.0)
    i = ac.split_index(pts)
    wall = radii[i] * ac.FLAT - (ac.SPIGOT_D + PRESS_FIT_CLEARANCE_MM) / 2
    assert wall >= MIN_WALL_MM


def test_beam_path_length_is_spec():
    pts, _ = ac.sampled_beam(500.0)
    assert math.isclose(path_length(pts), 500.0, abs_tol=0.5)


def test_six_tines_split_three_three():
    lower = [t for t in ac.TINES if t[0] < ac.SPLIT_F]
    upper = [t for t in ac.TINES if t[0] > ac.SPLIT_F]
    assert len(lower) == 3 and len(upper) == 3
    # keep the joint region clear of tine roots
    assert all(abs(t[0] - ac.SPLIT_F) > 0.05 for t in ac.TINES)


def test_beam_is_smooth():
    """Anti-faceting regression: the sampled centerline must bend only a few
    degrees per sample, or the antler reads as segmented."""
    pts, _ = ac.sampled_beam(500.0)
    ts = tangents(pts)
    max_kink = max(
        math.degrees(math.acos(max(-1.0, min(1.0, vdot(a, b)))))
        for a, b in zip(ts, ts[1:]))
    assert max_kink < 8.0
    frac = ac.arc_fractions(pts)[ac.split_index(pts)]
    assert 0.42 <= frac <= 0.50  # split stays mid-beam for both envelopes


def test_gyrocup_corridor_clear_at_base():
    """The cup (radius ~25) enters the bore from +Y: the antler base ball
    must stay outside that corridor around the Y axis."""
    pts, radii = ac.sampled_beam(500.0)
    (x, _, z), r = pts[0], radii[0]
    assert math.hypot(x, z) - r >= 50.0 / 2 + 0.5
