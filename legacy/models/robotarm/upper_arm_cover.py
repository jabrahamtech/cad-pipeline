"""robotarm upper_arm_cover — the gable shell that closes the upper arm's
channel and hides its wiring.

Spec: specs/robotarm/upper_arm_cover.md. Frame: identical to upper_arm's, so
it drops straight on with no transform (X = long axis, 0 = shoulder axis,
Y = joint axes, Z up).

It starts where the link's web starts, for the same reason the web does:
inside _frame.LINK_WEB_CLEAR_R the cover would bridge the channel and jam
against the shoulder bracket at every angle. The joint itself is closed by a
concentric drum instead.

Fixing: two M3 screws through the link's -Y side plate into bosses inside the
cover. Visible fasteners on the flank are what the reference does too.

Print: gable UP, open side down on the bed. No support — both flanks are at
45 deg and the crown is narrow. PETG, 3 walls, 12 % infill; this part carries
nothing.
"""

import math
import sys
from pathlib import Path
from typing import cast

from build123d import Part

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frame  # noqa: E402
from _shell import channel_cover  # noqa: E402

PART_METADATA = {"expected_solids": 1}

COVER_SKIN = 2.0
COVER_RISE = 18.0
CROWN_MIN = 5.0
SCREW_PILOT = 2.5           # M3 self-tapper into PETG
BOSS = 8.0


def build(
    x0: float = 43.0,                    # sweep rule: >= LINK_WEB_CLEAR_R
    x_step: float = 52.0,                # where the link's plan steps in
    x1: float = 63.0,                    # stops where the elbow drum's
                                         # surface crosses base_z (63.5)
    near_half_width: float = _frame.SHOULDER_CHANNEL_W / 2 + 6.0,
    far_half_width: float = _frame.LINK_CHANNEL_W / 2 + _frame.LINK_PLATE_T,
    base_z: float = 27.0,                # the link's plate height
    rise: float = COVER_RISE,
    skin_thickness: float = COVER_SKIN,
    crown_min: float = CROWN_MIN,
    screw_pilot: float = SCREW_PILOT,
    boss_dia: float = BOSS,
) -> Part:
    lo = math.hypot(x0, base_z - 14.05)
    if lo < _frame.LINK_WEB_CLEAR_R:
        raise ValueError(
            f"cover starts {lo:.1f} mm from the shoulder axis but must clear "
            f"{_frame.LINK_WEB_CLEAR_R} — it would jam the joint"
        )
    return cast(Part, channel_cover(
        segments=[(x0, x_step, near_half_width),
                  (x_step, x1, far_half_width)],
        base_z=base_z,
        rise=rise,
        skin=skin_thickness,
        crown_min=crown_min,
        screw_x=(x0 + 7.0, x1 - 7.0),
        screw_z=base_z + 5.0,
        screw_pilot=screw_pilot,
        boss=boss_dia,
        boss_side=-1.0,
    ))


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"upper_arm_cover: volume {part.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
