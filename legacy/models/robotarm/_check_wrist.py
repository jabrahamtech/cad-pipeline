"""Assembly check for the wrist ROLL joint.

Four things have to be true, and none can be seen by building the parts on
their own:

  1  wrist_mount's saddle actually slips over the forearm's tip and its two
     bolts pass clean through BOTH the saddle walls and both of the link's
     side plates — it fouled the link's plan taper by 425 mm^3 the first
     time, because the saddle was longer than the parallel part of the tip;
  2  the MG90S goes into the bracket nose-first WITH ITS HORN ON — the tabs
     bear on the face's front surface, so the servo sits a tab thickness in
     front of it, not on it;
  3  wrist_rotator seats on that horn and turns a full circle without
     touching the bracket or the link;
  4  the rotator's skirt actually laps the journal boss. Without that lap
     the whole effector hangs off a 4.8 mm servo shaft, which is the failure
     this joint exists to avoid.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/_check_wrist.py
"""

from __future__ import annotations

import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Cylinder, Location, Part, Pos, Rotation  # noqa: E402

from lib.cots import servo  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frame as F  # noqa: E402

TOL = 3.0     # mm^3; the horn stand-in and the screw bore share a surface


def _load(name: str):
    py = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def mount_location() -> Location:
    """The bracket slides straight on: same x-origin at the link's tip, and
    its saddle floor sits one wall thickness below the link's bed face."""
    return cast(Location, Pos(F.FOREARM_LEN, 0.0, -F.WRIST_MOUNT_WALL))


def flange_front() -> float:
    """x of the servo face's FRONT surface, in the link's frame."""
    return F.FOREARM_LEN + F.WRIST_FACE_X + F.WRIST_FLANGE_T


def servo_location(front: float) -> Location:
    """The tabs bear ON the flange's front face, so the servo's own origin
    plane sits a tab thickness in front of it."""
    return cast(Location,
                Pos(front + F.WRIST_SERVO.tab_thick, 0, F.WRIST_ROLL_Z)
                * Rotation(0, 90, 0) * Rotation(0, 0, 180))


def rotator_location(front: float, roll: float = 0.0) -> Location:
    """The rotator seats on the horn's TOP face and its own +Z points back
    down the arm, hence the -90 about Y."""
    return cast(Location,
                Pos(front + F.wrist_horn_face_x() + F.ROTATOR_T, 0,
                    F.WRIST_ROLL_Z)
                * Rotation(0, -90, 0) * Rotation(0, 0, roll))


def main() -> int:
    link = _load("forearm").build()
    mount = cast(Part, mount_location() * _load("wrist_mount").build())
    rot = _load("wrist_rotator").build()
    fails: list[str] = []
    front = flange_front()

    c = link & mount
    v = 0.0 if c is None else c.volume
    print(f"bracket slipped over the tip: {v:.1f} mm^3 of overlap")
    if v > TOL:
        fails.append(f"wrist_mount does not go on: {v:.0f} mm^3 of "
                     f"interference with the forearm")

    # both bolts must pass clean through, AND find material either side
    for dx in F.WRIST_MOUNT_BOLT_DX:
        x = F.FOREARM_LEN + dx
        bolt = cast(Part, Pos(x, 0, F.LINK_AXIS_Z) * Rotation(90, 0, 0)
                    * Cylinder(F.WRIST_MOUNT_BOLT_DIA / 2 - 0.2, 200.0))
        ring = cast(Part, Pos(x, 0, F.LINK_AXIS_Z) * Rotation(90, 0, 0)
                    * (Cylinder(3.6, 200.0) - Cylinder(2.2, 202.0)))
        for name, part in (("forearm", link), ("bracket", mount)):
            blocked = part & bolt
            bv = 0.0 if blocked is None else blocked.volume
            held = part & ring
            hv = 0.0 if held is None else held.volume
            print(f"  bolt at x={x:5.1f}, {name:8s}: {bv:5.1f} mm^3 in the "
                  f"way, {hv:6.1f} mm^3 of material round it")
            if bv > TOL:
                fails.append(f"the bolt at x={x:.0f} is blocked by the "
                             f"{name} ({bv:.0f} mm^3)")
            if hv < 40.0:
                fails.append(f"the bolt at x={x:.0f} has almost nothing to "
                             f"bear on in the {name} ({hv:.0f} mm^3)")

    body = cast(Part, servo_location(front) * servo(F.WRIST_SERVO))
    for name, part in (("forearm", link), ("bracket", mount)):
        c = part & body
        v = 0.0 if c is None else c.volume
        print(f"MG90S nose-first, horn on, vs the {name}: {v:.1f} mm^3")
        if v > TOL:
            fails.append(f"the wrist servo does not go in: {v:.0f} mm^3 "
                         f"against the {name}")

    print(f"\n{'roll':>6} {'vs forearm':>12} {'vs bracket':>12}")
    for deg in range(0, 360, 30):
        placed = cast(Part, rotator_location(front, deg) * rot)
        a = link & placed
        b = mount & placed
        va = 0.0 if a is None else a.volume
        vb = 0.0 if b is None else b.volume
        print(f"{deg:6d} {va:12.2f} {vb:12.2f}")
        if max(va, vb) > TOL:
            fails.append(f"rotator fouls the arm by {max(va, vb):.0f} mm^3 "
                         f"at {deg} deg of roll")

    # the horn must land IN the pocket, not on the rotator's face
    placed = cast(Part, rotator_location(front) * rot)
    c = placed & body
    v = 0.0 if c is None else c.volume
    print(f"\nrotator vs servo+horn: {v:.1f} mm^3 "
          f"(the horn has to sit inside the pocket)")
    if v > TOL:
        fails.append(f"the horn does not seat: {v:.0f} mm^3 of overlap")

    # journal engagement, measured rather than asserted
    boss_end = front + F.WRIST_BOSS_LEN
    skirt_back = front + F.wrist_horn_face_x() - F.ROTATOR_SKIRT_LEN
    lap = boss_end - skirt_back
    print(f"journal: boss reaches x={boss_end:.1f}, skirt starts at "
          f"x={skirt_back:.1f} -> {lap:.1f} mm of engagement")
    if lap < 4.0:
        fails.append(f"the skirt only laps the boss by {lap:.1f} mm — the "
                     f"effector would hang off the servo shaft")

    # and the skirt has to run on the boss, not jam on it
    gap = (F.ROTATOR_R - F.ROTATOR_SKIRT_T) - F.WRIST_BOSS_R
    print(f"running clearance, skirt bore to boss: {gap:.2f} mm")
    if not 0.15 <= gap <= 0.45:
        fails.append(f"skirt-to-boss clearance is {gap:.2f} mm — wanted a "
                     f"sliding fit")

    # and the whole EFFECTOR has to clear the arm through a full roll — the
    # hand is 72 mm across, so its corners sweep a 41 mm circle
    hand = _load("hand_base").build()
    print(f"\n{'roll':>6} {'hand vs forearm':>16} {'hand vs bracket':>16}")
    for deg in range(0, 360, 45):
        placed = cast(Part, rotator_location(front, deg)
                      * Rotation(180, 0, 0) * hand)
        a = link & placed
        b = mount & placed
        va = 0.0 if a is None else a.volume
        vb = 0.0 if b is None else b.volume
        print(f"{deg:6d} {va:16.2f} {vb:16.2f}")
        if max(va, vb) > TOL:
            fails.append(f"the hand fouls the arm by {max(va, vb):.0f} mm^3 "
                         f"at {deg} deg of roll")

    if fails:
        print("\nFAIL")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nOK — the bracket goes on, the servo goes in, the rotator turns "
          "a full circle and the skirt carries the load")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
