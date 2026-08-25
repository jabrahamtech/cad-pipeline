"""Assembly check for the two-servo claw.

Each part is a valid solid on its own; that says nothing about whether the
hand works. This places both real servos, both real fingers and the real
base, sweeps the fingers from closed to open, and checks:

  1  each SG90 goes into its upright WITH ITS HORN ON, clear of the base;
  2  neither finger fouls the base at any angle;
  3  the two fingers never foul each other, and their tips meet at the
     closed end;
  4  finger R really is finger L turned 180 deg about the shaft axis — the
     same printed part, which is only true because the horn pocket goes
     clean through.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/_check_hand.py
"""

from __future__ import annotations

import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Location, Part, Pos, Rotation  # noqa: E402

from lib.cots import servo  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hand as H  # noqa: E402
from _frame import EFFECTOR_SERVO  # noqa: E402

TOL = 1.0


def _load(name: str):
    py = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def servo_location(side: float) -> Location:
    """Shaft along +Y, tabs bearing on the upright's +Y face — so the servo's
    own origin plane sits a tab thickness proud of it."""
    return cast(Location,
                Pos(side * H.PIVOT_X,
                    H.UPRIGHT_FACE_Y + EFFECTOR_SERVO.tab_thick, H.PIVOT_Z)
                * Rotation(-90, 0, 0) * Rotation(0, 0, 90))


def finger_location(side: float, angle_deg: float) -> Location:
    """Finger R is finger L TURNED OVER — 180 deg about its own blade axis.

    Not simply rotated about the shaft: a plain rotation would leave its
    gripping edge facing away from the other finger. Turning it over swaps
    which edge grips, and that is exactly why the horn pocket has to be a
    through-cut — the flipped copy meets the horn on its other face.
    """
    a = angle_deg if side < 0 else 180.0 - angle_deg
    flip = Rotation(180, 0, 0) if side > 0 else Rotation(0, 0, 0)
    y0 = H.FINGER_PLANE_Y + (0.0 if side > 0 else H.FINGER_T)
    return cast(Location,
                Pos(side * H.PIVOT_X, y0, H.PIVOT_Z)
                * Rotation(90, 0, 0) * Rotation(0, 0, a) * flip)


def main() -> int:
    base = _load("hand_base").build()
    finger = _load("hand_finger").build()
    fails: list[str] = []

    print(f"  pivots at x = +/-{H.PIVOT_X}, z = {H.PIVOT_Z}; finger reach "
          f"{H.FINGER_R}, sweep {H.SWEEP_DEG:.0f} deg")

    for side, label in ((-1.0, "left"), (1.0, "right")):
        body = cast(Part, servo_location(side) * servo(EFFECTOR_SERVO))
        c = base & body
        v = 0.0 if c is None else c.volume
        print(f"  {label} SG90 + horn into its upright: {v:.1f} mm^3")
        if v > TOL:
            fails.append(f"the {label} servo does not go in: {v:.0f} mm^3")

    print(f"\n{'angle':>7} {'opening':>9} {'vs base':>9} {'L vs R':>9} "
          f"{'tip err':>9}")
    steps = 8
    for i in range(steps):
        a = H.CLOSED_DEG + (H.OPEN_DEG - H.CLOSED_DEG) * i / (steps - 1)
        fl = cast(Part, finger_location(-1.0, a) * finger)
        fr = cast(Part, finger_location(1.0, a) * finger)

        vs_base = 0.0
        for f in (fl, fr):
            c = base & f
            vs_base = max(vs_base, 0.0 if c is None else c.volume)
        c = fl & fr
        lr = 0.0 if c is None else c.volume

        # the placement has to agree with _hand's own kinematics: transform
        # the finger's OWN tip point and compare, rather than guessing at a
        # bounding box (the root disc is what a bbox actually finds)
        want_x, want_z = H.tip_centre(a)
        tip = cast(Location, finger_location(-1.0, a)
                   * Pos(H.FINGER_R, 0.0, H.FINGER_T / 2)).position
        err = max(abs(tip.X - want_x), abs(tip.Z - want_z))

        print(f"{a:7.1f} {H.opening(a):9.2f} {vs_base:9.2f} {lr:9.2f} "
              f"{err:9.2f}")
        if vs_base > TOL:
            fails.append(f"a finger fouls the base by {vs_base:.0f} mm^3 at "
                         f"{a:.0f} deg")
        if lr > TOL:
            fails.append(f"the two fingers foul each other by {lr:.0f} mm^3 "
                         f"at {a:.0f} deg")
        if err > 0.5:
            fails.append(f"finger placement disagrees with _hand.tip_centre "
                         f"by {err:.1f} mm at {a:.0f} deg")

    # tips must actually meet
    fl = cast(Part, finger_location(-1.0, H.CLOSED_DEG) * finger)
    fr = cast(Part, finger_location(1.0, H.CLOSED_DEG) * finger)
    gap = fr.bounding_box().min.X - fl.bounding_box().max.X
    print(f"\nclosed gap between the fingers: {gap:.2f} mm")
    if gap > 0.5:
        fails.append(f"the fingers do not close: {gap:.2f} mm left")

    # both fingers must sit in the SAME plane, or they grip past each other
    dy = abs(fl.bounding_box().min.Y - fr.bounding_box().min.Y)
    print(f"the two fingers are {dy:.2f} mm out of plane")
    if dy > 0.05:
        fails.append(f"the fingers are {dy:.1f} mm out of plane — they would "
                     f"pass each other instead of gripping")

    print(f"\nopening 0.0 -> {H.opening(H.OPEN_DEG):.1f} mm over "
          f"{H.SWEEP_DEG:.0f} deg of servo travel")
    print(f"grip force {H.grip_kgf():.2f} kgf per finger at stall, "
          f"{H.grip_kgf() / 2:.2f} at the 50 % duty limit")

    if fails:
        print("\nFAIL")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nOK — both servos fit, both fingers sweep clear and meet on the "
          "centreline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
