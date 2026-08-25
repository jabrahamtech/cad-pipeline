"""robotarm fit check — can each servo actually go in WITH ITS LEAD ON?

A pocket cut to the bare servo case plus a sliding fit looks right in CAD and
is useless on the bench: the lead leaves the side of the case, so the wire
gets pinched and the servo will not push home.

Two things are checked, and deliberately NOT a third. The servo must fit
SEATED with its lead attached, and the relief must be big enough to pass the
lead's cross-section. What is NOT checked is sweeping a rigid lead down the
insertion path: a real lead bends the moment it leaves its boot, so a rigid
stub reports clashes that do not exist. What a pocket has to provide is room
for the wire to LEAVE and TURN, not a straight tunnel.

Underscore-prefixed, so the invariant tests skip it.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/_check_fit.py
"""

import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Location, Part, Pos, Rotation  # noqa: E402

from lib.cots import servo_with_lead  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    BASE_SERVO,
    CAP_H,
    COLUMN_Y,
    SHOULDER_DRUM_Y,
    SHOULDER_RISE,
    SHOULDER_SERVO,
    TURNTABLE_T,
    Z_FLANGE,
    Z_RIM,
)

TOL = 1.0          # mm^3 — OCC slivers on coincident faces
STEPS = 7


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _clash(a: Part, b: Part) -> float:
    hit = cast(Part, a & b)
    return hit.volume if hit.solids() else 0.0


def main() -> int:
    errors: list[str] = []
    cap = _load("turret_cap").build()
    platter = _load("base_platter").build()
    bracket = _load("shoulder_bracket").build()

    # --- base servo: drops vertically through the cap into the column.
    # Try BOTH lead orientations: the notch is on both faces so either works.
    for side in (-1.0, 1.0):
        srv = servo_with_lead(BASE_SERVO, lead_side=side)
        at = cast(Location, Pos(0, 0, Z_FLANGE) * Rotation(0, 0, -90))
        here = cast(Part, at * srv)
        worst = max(_clash(here, cap), _clash(here, platter))
        tag = "+Y" if side > 0 else "-Y"
        print(f"base {BASE_SERVO.name} seated, lead {tag}: "
              f"{worst:7.1f} mm^3")
        if worst > TOL:
            errors.append(
                f"base servo with its lead on the {tag} side fouls by "
                f"{worst:.0f} mm^3 — the lead relief is too small"
            )

    # --- shoulder MG995: slides along +Y into the drum through the near cap
    shaft_z = TURNTABLE_T + SHOULDER_RISE
    for side in (-1.0, 1.0):
        srv = servo_with_lead(SHOULDER_SERVO, lead_side=side)
        at = cast(Location,
                  Pos(0, SHOULDER_DRUM_Y[0] - SHOULDER_SERVO.tab_thick,
                      shaft_z) * Rotation(90, 0, 0))
        worst = _clash(cast(Part, at * srv), bracket)
        tag = "+Y" if side > 0 else "-Y"
        print(f"shoulder {SHOULDER_SERVO.name} seated, lead {tag}: "
              f"{worst:7.1f} mm^3")
        if worst > TOL:
            errors.append(
                f"shoulder servo with its lead on the {tag} side fouls by "
                f"{worst:.0f} mm^3"
            )

    # --- is the relief actually big enough for the wire to get out?
    from lib.cots import LEAD_T, LEAD_W
    from _frame import LEAD_RELIEF_D, LEAD_RELIEF_W
    print(f"\nlead section {LEAD_W:.1f} x {LEAD_T:.1f} mm; "
          f"relief {LEAD_RELIEF_W:.1f} x {LEAD_RELIEF_D:.1f} mm")
    if LEAD_RELIEF_W < LEAD_W + 1.0 or LEAD_RELIEF_D < LEAD_T + 1.0:
        errors.append(
            f"lead relief {LEAD_RELIEF_W} x {LEAD_RELIEF_D} is too small for "
            f"a {LEAD_W} x {LEAD_T} lead with room to turn"
        )

    if errors:
        print("\nFAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nOK — every servo goes in with its lead attached, all the way")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
