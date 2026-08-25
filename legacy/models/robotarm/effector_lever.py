"""robotarm effector_lever — the light arm on the effector SG90's horn that
pushes the free scissor handle closed.

Spec: covered by specs/robotarm/scissor_cradle.md (the lever is called out
there as the pushing element). ALL scissor-facing dimensions are ASSUMED
(generic 170 mm office scissors) and are build() parameters:
    handle_thickness = 6.0   free handle bar thickness, captured by the fork
    lever_length     = 25.0  servo axis -> pad centre

FRAME: LOCAL, the driven frame of lib.servo.horn_pocket — the effector horn's
TOP face is z = 0, the servo shaft axis is Z through the origin, the part
grows into +Z, and the arm reaches out along +X. Mounted on wrist_bracket the
servo axis lies along the bracket's Y, so the lever swings in the scissors'
own plane.

FORK, NOT A NUB: the pad is a Ø9 post that drops BACK toward the servo
(-Z local, i.e. down past the arm) with a lip at its far end. The free handle
therefore sits in a slot bounded by the arm underside above and the lip
below, so it cannot walk off the pad along the shaft axis — which is the only
direction it can escape. Contact is a cylinder on a bar: it rolls, it does
not dig in.

PRINT: horn-pocket face UP — the part lies on its outer (z = +body_thickness)
face and the pad post plus lip build upward. No support: the lip is a 2 mm
radial overhang and the horn pocket is an open-topped recess. PETG, 40 %
infill; it is at the far end of the arm, so keep it light.

HONESTY: an SG90 stalls at 1.8 kg·cm, so at lever_length = 25 mm it can push
about 0.7 kg. Nothing here is sized for more; if the scissors need a firmer
squeeze, shorten lever_length (more force, less travel) rather than expecting
more from the servo.
"""

import sys
from pathlib import Path
from typing import cast

from build123d import Axis, Box, Cylinder, Part, Pos, chamfer, fillet

from lib.design_rules import MIN_WALL_MM
from lib.servo import horn_pocket

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import EFFECTOR_SERVO  # noqa: E402

PART_METADATA = {"expected_solids": 1}

HORN_POCKET_CLEARANCE = 0.4   # lib.servo.horn_pocket default


def push_force_kg(lever_length: float = 25.0) -> float:
    """What the effector servo can actually deliver at the pad."""
    return EFFECTOR_SERVO.stall_kgcm / (lever_length / 10.0)


def build(
    lever_length: float = 25.0,      # servo axis -> pad centre
    body_thickness: float = 5.0,     # hub and arm, one slab
    hub_wall: float = 2.0,           # material around the horn pocket
    arm_width: float = 8.0,
    pad_dia: float = 9.0,
    pad_drop: float = 9.0,           # pad reaches this far back toward the servo
    handle_thickness: float = 6.0,   # ASSUMED free scissor handle bar
    lip_thickness: float = 2.0,      # retaining lip at the far end of the pad
    lip_proud: float = 2.0,          # how far the lip stands out radially
    horn_arms: int = 1,              # single-arm horn keeps the hub small
    arm_fillet: float = 3.0,
) -> Part:
    hub_len = EFFECTOR_SERVO.horn_span + HORN_POCKET_CLEARANCE + 2 * hub_wall
    hub_wid = EFFECTOR_SERVO.horn_arm_w + HORN_POCKET_CLEARANCE + 2 * hub_wall
    pocket_depth = EFFECTOR_SERVO.horn_thick + 0.2
    fork_gap = pad_drop - lip_thickness   # slot the handle rides in

    # --- interface checks
    if hub_wall < MIN_WALL_MM:
        raise ValueError(f"hub_wall {hub_wall} below {MIN_WALL_MM} mm")
    if body_thickness - pocket_depth < MIN_WALL_MM:
        raise ValueError(
            f"body_thickness {body_thickness} leaves < {MIN_WALL_MM} mm over "
            f"the horn pocket"
        )
    if fork_gap < handle_thickness + 0.5:
        raise ValueError(
            f"fork slot is {fork_gap:.1f} mm but the handle is "
            f"{handle_thickness} mm — increase pad_drop"
        )
    if lever_length - pad_dia / 2 - lip_proud < hub_len / 2:
        raise ValueError("pad overlaps the hub — lengthen the lever")

    # --- phase 1: base shape — hub bar + arm out to the pad, one slab
    prims: list[Part] = [
        cast(Part, Pos(0, 0, body_thickness / 2)
             * Box(hub_len, hub_wid, body_thickness)),
        cast(Part, Pos(lever_length / 2, 0, body_thickness / 2)
             * Box(lever_length, arm_width, body_thickness)),
    ]
    body = cast(Part, Part() + prims)

    # --- phase 2: features — soften the arm/hub junction before the pad is
    # added (fillets here are the load path from pad to horn)
    try:
        waist = [
            e for e in body.edges().filter_by(Axis.Z)
            if e.center().X > hub_len / 2 - 0.01 and abs(e.center().Y) > 0.01
        ]
        if waist:
            body = cast(Part, fillet(waist, arm_fillet))
    except Exception:  # OCC declines — cosmetic only
        pass

    # pad post + retaining lip, both reaching back toward the servo
    pad_h = pad_drop + body_thickness
    body = cast(Part, body + [
        cast(Part, Pos(lever_length, 0, body_thickness - pad_h / 2)
             * Cylinder(pad_dia / 2, pad_h)),
        cast(Part, Pos(lever_length, 0, -pad_drop + lip_thickness / 2)
             * Cylinder(pad_dia / 2 + lip_proud, lip_thickness)),
    ])

    # --- phase 3: finish — horn pocket, then break the pad's far edge so the
    # handle can be flicked back into the fork
    body = cast(Part, body - horn_pocket(EFFECTOR_SERVO, arms=horn_arms))
    try:
        far = [
            e for e in body.edges().group_by(Axis.Z)[0]
            if abs(e.center().X - lever_length) < 0.01
        ]
        if far:
            body = cast(Part, chamfer(far, lip_thickness / 2))
    except Exception:
        pass
    return cast(Part, Part() + body)


if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()
    print(f"effector_lever: volume {part.volume / 1000:.2f} cm^3, "
          f"mass(PETG) {part.volume / 1000 * 1.27:.1f} g, "
          f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(part.solids())}, valid {part.is_valid}")
    print(f"  {EFFECTOR_SERVO.name} at 25 mm lever pushes "
          f"~{push_force_kg():.2f} kg — design to that, not more")
