"""Whole-arm assembly: every part placed at its real mating position.

The transforms are DERIVED from the joint contract in _frame.py, not dialled
in by eye — each one is the same arithmetic the parts were built from, so if
a constant moves, the assembly follows.

Used by the preview renders, and available for whole-arm interference work.
Underscore-prefixed, so the invariant tests skip it.

Chain, each stage in the previous stage's frame:

    base_platter        world origin
    base_lid            +Z_LID
    turret_cap          +Z_RIM
    shoulder_bracket    +Z_RACE                    (rides the rollers)
    upper_arm           shoulder axis, rotated by the shoulder angle
    forearm             elbow axis, rotated by the elbow angle
    wrist_mount         saddle over the forearm's tip, two M3 through it
    wrist servo         in that bracket, shaft forward along the arm
    wrist_rotator       on that shaft, turned by the roll angle
    hand_base           bolted flat to the rotator's face

MATING OFFSETS, all derived:
  * upper_arm sits with NO y offset: the shoulder drum's cap plus the
    MG995's mount_to_horn IS the arm's channel half width, by construction.
    mount_to_horn, not horn_seat — the servo's tabs bear on the cap's OUTER
    face, one tab thickness further out than the flange plane.
  * forearm sits at dy = -(ELBOW_DRUM_Y[1] + horn_seat) + ELBOW_CHANNEL_W/2,
    i.e. its driven plate lands on the elbow horn.
  * the WRIST ROLLS, on a BOLT-ON bracket. wrist_mount slides straight onto
    the link's tip — same x-origin, one wall thickness below its bed face —
    and everything downstream is measured from the servo face's FRONT
    surface: the tabs bear on it, the horn's top face is wrist_horn_face_x()
    beyond it, and the rotator seats there. mount_to_horn, not horn_seat.
  * wrist_rotator's frame has its FRONT (effector) face at z = 0 growing +Z
    toward the arm, so it is turned -90 about Y to put that +Z along the
    forearm's -X. The hand is the same frame flipped, because its +Z points
    the other way — out along the arm.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/_assembly.py
"""

from __future__ import annotations

import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Location, Part, Pos, Rotation  # noqa: E402

from lib.cots import STEEL, SERVO_BODY, bearing, m8_bolt, servo  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    BASE_SERVO,
    CLIP_AZ,
    CLIP_R,
    EFFECTOR_SERVO,
    ELBOW_CHANNEL_W,
    ELBOW_DRUM_Y,
    ELBOW_SERVO,
    FOREARM_LEN,
    LINK_AXIS_Z,
    SHOULDER_CHANNEL_W,
    SHOULDER_DRUM_Y,
    SHOULDER_RISE,
    SHOULDER_SERVO,
    TURNTABLE_T,
    UPPER_ARM_LEN,
    ROTATOR_T,
    WRIST_FACE_X,
    WRIST_FLANGE_T,
    WRIST_MOUNT_WALL,
    WRIST_ROLL_Z,
    WRIST_SERVO,
    wrist_horn_face_x,
    Z_AXLE,
    Z_FLANGE,
    Z_LID,
    Z_RACE,
    Z_RIM,
    roller_positions,
)

ROLLER_R_FOR_COTS = 36.0    # = _frame.ROLLER_PITCH_R, where the bearings sit
DARK = "#3f454e"
MID = "#7b828c"
LIGHT = "#eef0f3"
ACCENT = "#c9ced6"


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _joint(base: Location, x: float, y: float, angle: float) -> Location:
    """Move to a joint at (x, y) in the current link's frame, turn about it,
    and hand back a frame whose origin is the next link's bed origin."""
    return cast(Location, base * Pos(x, y, LINK_AXIS_Z)
                * Rotation(0, angle, 0) * Pos(0, 0, -LINK_AXIS_Z))


def place_all(shoulder: float = -62.0, elbow: float = 58.0,
              wrist: float = 0.0, open_frac: float = 0.55,
              bought: bool = True) -> list[tuple[str, Part, Location, str]]:
    """(name, part, location, colour) for the whole arm at the given joint
    angles in degrees. Shoulder: negative lifts. Elbow: positive folds up.
    `wrist` is now a ROLL angle about the arm's own axis, and `open_frac` is
    how far open the jaws are, 0 (closed) to 1.

    `bought` adds stand-ins for the COTS parts — the three 608ZZ bearings and
    the five servos. They are never printed or exported, but leaving them out
    makes the drawing unreadable: the turntable looks like a disc levitating
    over a 12 mm air gap, because that gap IS the bearings.
    """
    out: list[tuple[str, Part, Location, str]] = []

    def add(name: str, loc: Location, colour: str) -> None:
        py = Path(__file__).parent / f"{name}.py"
        if py.exists():
            out.append((name, _load(name).build(), loc, colour))

    add("base_platter", Location(), DARK)
    add("base_lid", cast(Location, Pos(0, 0, Z_LID)), DARK)
    add("turret_cap", cast(Location, Pos(0, 0, Z_RIM)), MID)

    if bought:
        # the three rollers, and the M8 axles they run on
        for x, y, az in roller_positions():
            # +90 about Z puts the stand-in's own Y axis (its bore) along
            # the RADIUS — the axle points at the hub, or it scrubs
            at = cast(Location, Rotation(0, 0, az)
                      * Pos(ROLLER_R_FOR_COTS, 0, Z_AXLE)
                      * Rotation(0, 0, 90))
            out.append(("608ZZ", bearing(), at, STEEL))
            out.append(("M8 axle", m8_bolt(), at, STEEL))
        # base servo, hanging under the turret cap's top face
        out.append(("base servo", servo(BASE_SERVO),
                    cast(Location, Pos(0, 0, Z_FLANGE) * Rotation(0, 0, -90)),
                    SERVO_BODY))

    turntable = cast(Location, Pos(0, 0, Z_RACE))
    add("shoulder_bracket", turntable, LIGHT)
    # three hold-down clips: the rollers only push up, so without these the
    # disc tips off one roller whenever the arm reaches out
    clip_py = Path(__file__).parent / "turntable_clip.py"
    if clip_py.exists():
        clip = _load("turntable_clip").build()
        for az in CLIP_AZ:
            out.append(("turntable_clip", clip,
                        cast(Location, Rotation(0, 0, az)
                             * Pos(CLIP_R, 0, Z_FLANGE)), MID))

    # shoulder: the drum cap + mount_to_horn equal the arm's channel half
    # width, so there is no y offset at all. mount_to_horn, NOT horn_seat —
    # the tabs bear on the cap's outer face, a tab thickness further out.
    assert abs((SHOULDER_DRUM_Y[1] + SHOULDER_SERVO.mount_to_horn)
               - SHOULDER_CHANNEL_W / 2) < 0.2
    shoulder_axis_z = TURNTABLE_T + SHOULDER_RISE
    if bought:
        # MG995 inside the shoulder drum, shaft out through the near cap
        out.append(("shoulder servo", servo(SHOULDER_SERVO),
                    cast(Location, turntable
                         * Pos(0, SHOULDER_DRUM_Y[0], shoulder_axis_z)
                         * Rotation(90, 0, 0)), SERVO_BODY))
    upper = _joint(cast(Location, turntable
                        * Pos(0, 0, shoulder_axis_z - LINK_AXIS_Z)),
                   0.0, 0.0, shoulder)
    add("upper_arm", upper, LIGHT)
    add("upper_arm_cover", upper, ACCENT)

    # elbow: the forearm's driven plate lands on the elbow horn
    dy_elbow = -(ELBOW_DRUM_Y[1] + ELBOW_SERVO.horn_seat) + ELBOW_CHANNEL_W / 2
    if bought:
        out.append(("elbow servo", servo(ELBOW_SERVO),
                    cast(Location, upper
                         * Pos(UPPER_ARM_LEN, ELBOW_DRUM_Y[0], LINK_AXIS_Z)
                         * Rotation(90, 0, 0)), SERVO_BODY))
    fore = _joint(upper, UPPER_ARM_LEN, dy_elbow, elbow)
    add("forearm", fore, LIGHT)
    # wrist: a bolt-on bracket over the link's tip, then the servo in it
    # nose-first. Its tabs bear on the face's FRONT surface, so it sits a
    # tab thickness in front of that — the same mount_to_horn arithmetic as
    # every other joint here, turned through 90 degrees.
    add("wrist_mount", cast(Location, fore
                            * Pos(FOREARM_LEN, 0.0, -WRIST_MOUNT_WALL)), MID)
    face_front = FOREARM_LEN + WRIST_FACE_X + WRIST_FLANGE_T
    if bought:
        out.append(("wrist servo", servo(WRIST_SERVO),
                    cast(Location, fore
                         * Pos(face_front + WRIST_SERVO.tab_thick, 0.0,
                               WRIST_ROLL_Z)
                         * Rotation(0, 90, 0) * Rotation(0, 0, 180)),
                    SERVO_BODY))

    # the rotator seats on the horn's top face and turns about X
    rot = cast(Location, fore
               * Pos(face_front + wrist_horn_face_x() + ROTATOR_T, 0.0,
                     WRIST_ROLL_Z)
               * Rotation(0, -90, 0) * Rotation(0, 0, wrist))
    add("wrist_rotator", rot, MID)

    # the hand bolts to the rotator's front face. Its +Z points OUT along
    # the arm while the rotator's points back in, so it is the same frame
    # turned 180 about X.
    grip = cast(Location, rot * Rotation(180, 0, 0))
    add("hand_base", grip, LIGHT)
    check = _load("_check_hand")
    hand = _load("_hand")
    angle = hand.CLOSED_DEG + (hand.OPEN_DEG - hand.CLOSED_DEG) * open_frac
    finger = _load("hand_finger").build()
    for side in (-1.0, 1.0):
        out.append(("hand finger", finger,
                    cast(Location, grip * check.finger_location(side, angle)),
                    ACCENT))
        if bought:
            out.append(("effector servo", servo(EFFECTOR_SERVO),
                        cast(Location, grip * check.servo_location(side)),
                        SERVO_BODY))
    return out


if __name__ == "__main__":
    parts = place_all()
    print(f"{len(parts)} parts placed")
    for name, part, loc, _ in parts:
        p = cast(Part, loc * part)
        bb = p.bounding_box()
        print(f"  {name:24s} z {bb.min.Z:7.1f} .. {bb.max.Z:7.1f}")
    total = sum(cast(Part, p).volume for _, p, _, _ in parts) / 1000
    print(f"total printed volume {total:.1f} cm^3")
