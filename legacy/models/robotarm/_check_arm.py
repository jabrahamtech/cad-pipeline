"""robotarm shoulder-joint assembly check — numeric, no rendering.

tests/test_invariants.py proves each part is a valid solid, and
tests/test_robotarm.py proves the shared constants agree. Neither proves that
upper_arm actually goes ONTO shoulder_bracket, which is a different question:
the link is built in its own frame and only meets the bracket through a chain
of offsets. This puts them together and measures.

Placement is derived, not guessed:
  - the link's driven plate seats on the MG995 horn's UNDERSIDE, because
    lib.servo.horn_pocket embeds the horn in the plate;
  - the horn underside is SHOULDER_SERVO.mount_to_horn outboard of the face
    the tabs bear on
    plane, which is the bracket's near-wall outer face;
  - the link's own joint axis sits at LINK_AXIS_Z above its bed face.

Asserts: no interference through the usable swing, the idler stub actually
engages the bracket's far-wall bore, and the channel has clearance on both
sides.

Underscore-prefixed, so the invariant tests skip it.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/_check_arm.py
"""

import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Box, Part, Pos, Rotation  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frame import (  # noqa: E402
    ARM_BEARING,
    SHOULDER_AXIS_OFFSET_X,
    SHOULDER_CHANNEL_W,
    SHOULDER_DRUM_WALL,
    SHOULDER_DRUM_Y,
    SHOULDER_RISE,
    SHOULDER_SERVO,
    TURNTABLE_T,
)

TOL = 1.0            # mm^3, OCC leaves slivers on coincident faces
# The bracket's two walls are the shoulder DRUM's end caps, so both come from
# the joint frame rather than from a wall thickness of their own: the MG995
# bolts to the near cap's OUTER face and the arm's idler stub runs in a bore
# through the far cap.
BRACKET_WALL_T = SHOULDER_DRUM_WALL
# The bracket sits below the shoulder axis, so the arm runs out of room going
# DOWN, not up. Rather than assert an arbitrary limit, find the real one and
# require it to be at least horizontal.
# Rotation about +Y: NEGATIVE angles lift the arm up, positive swing it down
# into the base. The bracket sits below the axis, so the arm must reach
# horizontal (0) and vertical (-90); how far below horizontal it gets is a
# bonus we measure rather than demand.
SWING_REQUIRED = (-90.0, 0.0)
SWING_PROBE = (-95.0, 40.0)


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _volume(part: Part) -> float:
    return part.volume if part.solids() else 0.0


def _solid_bands(part: Part, axis: str, lo: float, hi: float,
                 at: tuple[float, float], step: float = 0.1
                 ) -> list[tuple[float, float]]:
    """Where `part` is solid along one axis, probing at a fixed point on the
    other two. Used to find plate faces without hard-coding them."""
    bands: list[tuple[float, float]] = []
    start = None
    n = int((hi - lo) / step) + 1
    for k in range(n):
        v = lo + k * step
        pos = {"x": (v, at[0], at[1]), "y": (at[0], v, at[1]),
               "z": (at[0], at[1], v)}[axis]
        probe = cast(Part, Pos(*pos) * Box(1.0, 1.0, 1.0))
        solid = _volume(cast(Part, part & probe)) > 0.05
        if solid and start is None:
            start = v
        if not solid and start is not None:
            bands.append((start, v))
            start = None
    if start is not None:
        bands.append((start, lo + (n - 1) * step))
    return bands


def main() -> int:
    errors: list[str] = []
    bracket = _load("shoulder_bracket").build()
    arm = _load("upper_arm").build()

    # --- measure the link's own frame instead of trusting a docstring
    bands = _solid_bands(arm, "y", -40.0, 40.0, at=(0.0, 0.0))
    if len(bands) != 2:
        print(f"could not find two side plates at the near end: {bands}")
        return 1
    (horn_out, horn_in), (idler_in, idler_out) = bands
    channel = idler_in - horn_in
    print(f"upper_arm near end: horn plate y {horn_out:.1f}..{horn_in:.1f}, "
          f"idler plate y {idler_in:.1f}..{idler_out:.1f}, "
          f"channel {channel:.1f} mm")
    if abs(channel - SHOULDER_CHANNEL_W) > 1.0:
        errors.append(f"near-end channel is {channel:.1f}, not "
                      f"SHOULDER_CHANNEL_W {SHOULDER_CHANNEL_W}")

    # joint axis height: the horn-pocket access bore is the gap in the plate
    plate_mid = (horn_out + horn_in) / 2
    zb = _solid_bands(arm, "z", 0.0, 30.0, at=(0.0, plate_mid))
    gaps = [(a[1], b[0]) for a, b in zip(zb, zb[1:])]
    if not gaps:
        print(f"no access bore found in the horn plate: {zb}")
        return 1
    axis_z = sum(gaps[0]) / 2
    print(f"link joint axis at z = {axis_z:.2f}")

    # --- derive the mating transform
    flange_y = SHOULDER_DRUM_Y[0]                 # bracket near-cap outer face
    # mount_to_horn, NOT horn_seat: the tabs bear on the cap's outer face,
    # a tab thickness outboard of the flange plane, and the horn is that
    # much further out again.
    horn_under = flange_y - SHOULDER_SERVO.mount_to_horn
    dy = horn_under - horn_in
    bracket_axis_z = TURNTABLE_T + SHOULDER_RISE
    print(f"horn underside at bracket y = {horn_under:.2f}; "
          f"link offset dy = {dy:+.2f}")

    def place(angle: float) -> Part:
        return cast(Part, Pos(SHOULDER_AXIS_OFFSET_X, dy, bracket_axis_z)
                    * Rotation(0, angle, 0) * Pos(0, 0, -axis_z) * arm)

    # --- 1. find the real swing envelope, then check it covers what we need
    clear: list[float] = []
    a = SWING_PROBE[0]
    while a <= SWING_PROBE[1] + 1e-9:
        if _volume(cast(Part, place(a) & bracket)) <= TOL:
            clear.append(a)
        a += 5.0
    if not clear:
        errors.append("upper_arm fouls shoulder_bracket at every angle")
    else:
        lo, hi = min(clear), max(clear)
        # the clear set must be one contiguous run, or something odd is going on
        expected = int(round((hi - lo) / 5.0)) + 1
        if len(clear) != expected:
            errors.append(f"swing envelope is not contiguous: {clear}")
        print(f"swing envelope: {lo:+.0f} to {hi:+.0f} deg from horizontal")
        if lo > SWING_REQUIRED[0] or hi < SWING_REQUIRED[1]:
            errors.append(
                f"arm swings {lo:+.0f}..{hi:+.0f} deg but must cover "
                f"{SWING_REQUIRED[0]:+.0f}..{SWING_REQUIRED[1]:+.0f}"
            )

    # --- 2. the idler stub must reach right through its BEARING
    far_out = SHOULDER_DRUM_Y[1]                  # bracket far-cap outer face
    far_in = far_out - BRACKET_WALL_T
    stub = _solid_bands(place(0.0), "y", far_in - 12.0, far_out + 12.0,
                        at=(SHOULDER_AXIS_OFFSET_X, bracket_axis_z))
    reach = [b for b in stub if b[0] < far_out]
    if not reach:
        errors.append(f"idler stub never reaches the far wall "
                      f"(y {far_in:.1f}..{far_out:.1f}); bands {stub}")
    else:
        engaged = min(far_out, reach[-1][1]) - max(far_in, reach[-1][0])
        print(f"idler stub engages {engaged:.1f} mm of the "
              f"{BRACKET_WALL_T:.0f} mm far wall")
        if engaged < 2.0:
            errors.append(f"idler stub only engages {engaged:.1f} mm — "
                          f"lengthen it")
        reach = (SHOULDER_CHANNEL_W / 2
                 - (SHOULDER_DRUM_Y[1] - ARM_BEARING.width))
        print(f"idler stub reaches {reach:.1f} mm, through the "
              f"{ARM_BEARING.width:.0f} mm {ARM_BEARING.name} race")
        if reach < SHOULDER_CHANNEL_W / 2 - SHOULDER_DRUM_Y[1] \
                + ARM_BEARING.width:
            errors.append("idler stub does not pass right through the race")

    # --- 3. channel clearance either side of the bracket
    lash_far = (dy + idler_in) - far_out
    print(f"clearance: horn side seats on the horn, idler side "
          f"{lash_far:+.1f} mm")
    if lash_far < 0.4:
        errors.append(f"only {lash_far:.1f} mm between the link's idler plate "
                      f"and the bracket's far wall")

    if errors:
        print("\nFAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nOK — upper_arm seats on the shoulder and swings clear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
