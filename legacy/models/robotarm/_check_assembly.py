"""robotarm base-stack assembly check — numeric, no rendering.

Stacks base_platter + base_lid + turret_cap + shoulder_bracket at their global
Z from _frame.py and asserts the things a picture would not tell you reliably:

  1. no two parts share volume (interference)
  2. the base servo case passes through the cap opening and down the column, and
     its bottom clears the bay floor
  3. the breadboard's footprint fits the bay and clears the servo column
  4. the roller contact circle lands on flat, uncut turntable underside
  5. every part is inside the printer envelope

Underscore-prefixed, so the invariant tests skip it.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/_check_assembly.py
"""

import math
import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Box, Part, Pos  # noqa: E402

from lib.bearings import B608ZZ  # noqa: E402
from lib.design_rules import ENVELOPE_SINGLE  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    BASE_SERVO,
    BREADBOARD,
    BREADBOARD_X0,
    COLUMN_OUTER_X,
    FLOOR_T,
    INNER_R,
    RACE_CONTACT_BAND,
    ROLLER_PITCH_R,
    Z_FLANGE,
    Z_LID,
    Z_RACE,
    Z_RIM,
    breadboard_corner_r,
)

TOL = 1.0  # mm^3 — OCC leaves slivers on coincident faces


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    errors: list[str] = []
    stack = {
        "base_platter": (_load("base_platter").build(), 0.0),
        "base_lid": (_load("base_lid").build(), Z_LID),
        "turret_cap": (_load("turret_cap").build(), Z_RIM),
        "shoulder_bracket": (_load("shoulder_bracket").build(), Z_RACE),
    }
    placed = {n: cast(Part, Pos(0, 0, z) * p) for n, (p, z) in stack.items()}

    # 1. interference
    names = list(placed)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = cast(Part, placed[a] & placed[b])
            vol = shared.volume if shared.solids() else 0.0
            if vol > TOL:
                errors.append(f"{a} ∩ {b}: {vol:.1f} mm^3 of interference")

    # 2. MG995 fits: case hangs from the flange plane down into the column
    case_bottom = Z_FLANGE - BASE_SERVO.below_flange
    if case_bottom < FLOOR_T + 2.0:
        errors.append(
            f"base servo case bottom at z={case_bottom:.1f} fouls the "
            f"{FLOOR_T} mm bay floor"
        )
    case = cast(Part, Pos(0, -BASE_SERVO.shaft_offset,
                          (case_bottom + Z_FLANGE) / 2)
                * Box(BASE_SERVO.case[1], BASE_SERVO.case[0],
                      BASE_SERVO.below_flange))
    for n in ("base_platter", "turret_cap", "base_lid"):
        shared = cast(Part, case & placed[n])
        vol = shared.volume if shared.solids() else 0.0
        if vol > TOL:
            errors.append(f"base servo case ∩ {n}: {vol:.1f} mm^3 — it will not "
                          f"drop in")

    # 3. breadboard
    corner_r = breadboard_corner_r()
    if corner_r > INNER_R:
        errors.append(f"breadboard corners at r={corner_r:.1f} exceed the "
                      f"bay wall at r={INNER_R:.1f}")
    if BREADBOARD_X0 < COLUMN_OUTER_X / 2:
        errors.append(f"breadboard starts at x={BREADBOARD_X0} but the "
                      f"column reaches x={COLUMN_OUTER_X / 2:.1f}")
    board = cast(Part, Pos(BREADBOARD_X0 + BREADBOARD[0] / 2, 0.0,
                           FLOOR_T + BREADBOARD[2] / 2)
                 * Box(BREADBOARD[0], BREADBOARD[1], BREADBOARD[2]))
    shared = cast(Part, board & placed["base_platter"])
    vol = shared.volume if shared.solids() else 0.0
    if vol > TOL:
        errors.append(f"breadboard ∩ base_platter: {vol:.1f} mm^3")

    # 4. roller contact ring must meet flat, uncut turntable underside:
    # probe a 1 mm cube just above the race plane all the way round
    probe_size = 0.6
    for r in (RACE_CONTACT_BAND[0], ROLLER_PITCH_R, RACE_CONTACT_BAND[1]):
        for k in range(24):
            theta = k * math.pi / 12
            probe = cast(Part, Pos(r * math.cos(theta), r * math.sin(theta),
                                   Z_RACE + 0.5)
                         * Box(probe_size, probe_size, 1.0))
            shared = cast(Part, probe & placed["shoulder_bracket"])
            solid_frac = (shared.volume / probe_size ** 2
                          if shared.solids() else 0.0)
            if solid_frac < 0.9:
                errors.append(
                    f"turntable underside is not solid at r={r:.1f}, "
                    f"{k * 15} deg — the roller would drop into a pocket"
                )
                break

    # 5. envelope
    for n, p in placed.items():
        bb = p.bounding_box()
        dims = sorted([bb.size.X, bb.size.Y, bb.size.Z])
        if any(d > e for d, e in zip(dims, sorted(ENVELOPE_SINGLE))):
            errors.append(f"{n} exceeds the print envelope")

    print(f"roller race: contact ring r={ROLLER_PITCH_R:.1f} "
          f"(band {RACE_CONTACT_BAND[0]:.0f}–{RACE_CONTACT_BAND[1]:.0f}), "
          f"bearing Ø{B608ZZ.od:.0f}, race plane z={Z_RACE:.1f}")
    print(f"base servo case: z {case_bottom:.1f} → {Z_FLANGE:.1f}, "
          f"floor at {FLOOR_T:.1f}")
    print(f"breadboard corners r={corner_r:.1f} vs bay wall r={INNER_R:.1f}")
    if errors:
        print("\nFAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nOK — no interference, everything clears")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
