"""robotarm mass and static-torque budget — does the arm still hold itself up
after the enclosure rebuild?

The drums, skirts and covers all added material, and some of it sits a long
way from the shoulder. This rebuilds every part, takes its REAL volume and
centre of mass, lays the arm out in its worst pose (straight out, horizontal,
where gravity has the longest lever on every joint) and works out the static
torque each servo has to hold. It then compares that to the servo's stall.

Two mass models are reported, because the honest answer sits between them:
  SOLID   volume x 1.27 g/cm^3 — what the part would weigh at 100 % infill.
          Nothing prints like this; it is the pessimistic bound.
  PRINTED the same scaled by FILL_FACTOR, a rule-of-thumb for these wall
          counts and infills. This is the number to plan around.
If a joint passes at SOLID it is safe with no argument at all.

Rule of thumb used for the verdict: a hobby servo should hold a static load
at or under ~50 % of its stall torque. Above that they run hot, buzz, and
strip their gears over time — stall is a peak rating, not a duty rating.

Underscore-prefixed, so the invariant tests skip it.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/_check_loads.py
"""

import sys
from importlib import util as importlib_util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import CenterOf  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hand as HAND  # noqa: E402
from _frame import (  # noqa: E402
    ELBOW_SERVO,
    FOREARM_LEN,
    ROTATOR_T,
    SHOULDER_SERVO,
    UPPER_ARM_LEN,
    WRIST_FACE_X,
    WRIST_FLANGE_T,
    WRIST_SERVO,
    wrist_horn_face_x,
)

PETG_DENSITY = 1.27          # g/cm^3
FILL_FACTOR = 0.55           # printed mass / solid mass, walls + infill
DUTY_LIMIT = 0.50            # of stall, for a load held statically
PAYLOAD_G = 28.0             # rated payload in the gripper jaws; the check
                             # below derives where this ceiling comes from.
                             # The elbow MG90S sets it and always has.
                             # The roll wrist took 40 g off the outboard
                             # end, which is why this is 28 g and not the
                             # 20 g the yoke-and-clevis version managed.
                             # Swap the elbow for an MG995 and it roughly
                             # quadruples again.
SERVO_MASS = {"SG90": 9.0, "MG90S": 13.4, "MG995": 55.0}
# Conservative allowable for PETG loaded ACROSS the printed layers, which is
# how every one of these sections is stressed. Datasheet tensile is ~45 MPa;
# interlayer is roughly half that, and this halves it again for safety.
PETG_INTERLAYER_MPA = 12.0

# Where each printed part's own origin sits along the arm, measured from
# the SHOULDER axis with the arm straight out, and WHICH of the part's own
# axes runs along the arm. The links are modelled along their local X; every
# part outboard of the wrist roll joint is modelled along its local Z, and
# the rotator's Z points BACK down the arm, so its sign is negative.
WRIST_TIP = UPPER_ARM_LEN + FOREARM_LEN
FACE_FRONT = WRIST_TIP + WRIST_FACE_X + WRIST_FLANGE_T
ROTATOR_FACE = FACE_FRONT + wrist_horn_face_x() + ROTATOR_T

CHAIN = [
    ("upper_arm", 0.0, "X", 1.0),
    ("forearm", UPPER_ARM_LEN, "X", 1.0),
    ("wrist_mount", WRIST_TIP, "X", 1.0),
    ("wrist_rotator", ROTATOR_FACE, "Z", -1.0),
    ("hand_base", ROTATOR_FACE, "Z", 1.0),
]
COVERS = ["upper_arm_cover"]

# The fingers do not lie along any one of their own axes once they are
# swung, so they go in as point masses at a measured distance instead: the
# blade's centre of mass is about 0.4 of its reach out, and near the middle
# of the sweep that is almost entirely along the arm.
FINGERS = [("hand_finger", ROTATOR_FACE + HAND.PIVOT_Z + HAND.FINGER_R * 0.4)
           for _ in range(2)]

# Servos carried by the arm, and where they sit along it. TWO effector
# servos: one per finger.
SERVOS_ON_ARM = [
    (ELBOW_SERVO.name, UPPER_ARM_LEN),
    (WRIST_SERVO.name, WRIST_TIP + 8.0),
    ("SG90", ROTATOR_FACE + HAND.PIVOT_Z - 8.0),
    ("SG90", ROTATOR_FACE + HAND.PIVOT_Z - 8.0),
]

# 608ZZ journals on the idler side of the shoulder and elbow. They sit ON
# their own joint axis, so each contributes NOTHING to the joint it serves —
# the elbow's bearing adds zero elbow torque. Only the shoulder feels the
# elbow's bearing, at the elbow's own radius. The wrist no longer has one:
# a roll joint is journalled by the rotator's own skirt on a printed boss.
BEARINGS_ON_ARM = [
    ("608ZZ shoulder", 0.0),
    ("608ZZ elbow", UPPER_ARM_LEN),
]
BEARING_G = 12.0

# Where the payload actually hangs: between the finger tips, not at the
# mounting flange.
PAYLOAD_S = ROTATOR_FACE + HAND.PIVOT_Z + HAND.FINGER_R * 0.9

# Only the two PITCH joints are loaded by gravity through a moment arm.
JOINTS = [
    ("shoulder", 0.0, SHOULDER_SERVO),
    ("elbow", UPPER_ARM_LEN, ELBOW_SERVO),
]

# The wrist is a ROLL joint, so it is not in that table: gravity does almost
# no work about it, exactly as at the base. What it DOES have to hold is
# whatever sits off the roll axis — and since the hand is built symmetric
# about that axis, that is the payload gripped off-centre. Worst case taken
# as the payload at the outer edge of the jaws' common face.
ROLL_OFFSET_MM = 20.0


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    masses: list[tuple[str, float, float, float]] = []  # name, solid, printed, s
    print(f"{'part':24s} {'cm^3':>7s} {'solid g':>8s} {'print g':>8s} "
          f"{'arm mm':>7s}")
    for name, base_s, ax, sign in (
            CHAIN + [(c, 0.0, "X", 1.0) for c in COVERS]
            + [(n, s_, "-", 0.0) for n, s_ in FINGERS]):
        py = Path(__file__).parent / f"{name}.py"
        if not py.exists():
            continue
        part = _load(name).build()
        vol_cm3 = part.volume / 1000.0
        solid = vol_cm3 * PETG_DENSITY
        if ax == "-":
            s = base_s                      # placed explicitly, see FINGERS
        else:
            com = part.center(CenterOf.MASS)
            s = base_s + sign * (com.X if ax == "X" else com.Z)
        masses.append((name, solid, solid * FILL_FACTOR, s))
        print(f"{name:24s} {vol_cm3:7.1f} {solid:8.1f} "
              f"{solid * FILL_FACTOR:8.1f} {s:7.1f}")

    for sname, s in SERVOS_ON_ARM:
        m = SERVO_MASS[sname]
        masses.append((f"servo {sname}", m, m, s))
        print(f"{'servo ' + sname:24s} {'':7s} {m:8.1f} {m:8.1f} {s:7.1f}")
    for bname, s_ in BEARINGS_ON_ARM:
        masses.append((bname, BEARING_G, BEARING_G, s_))
        print(f"{bname:24s} {'':7s} {BEARING_G:8.1f} {BEARING_G:8.1f} "
              f"{s_:7.1f}")
    masses.append(("payload", PAYLOAD_G, PAYLOAD_G, PAYLOAD_S))
    print(f"{'payload':24s} {'':7s} {PAYLOAD_G:8.1f} {PAYLOAD_G:8.1f} "
          f"{PAYLOAD_S:7.1f}")

    arm_solid = sum(m[1] for m in masses if m[0] != "payload")
    arm_print = sum(m[2] for m in masses if m[0] != "payload")
    print(f"\narm mass beyond the shoulder: {arm_print:.0f} g printed "
          f"({arm_solid:.0f} g if solid), plus {PAYLOAD_G:.0f} g payload")

    errors: list[str] = []
    print(f"\n{'joint':10s} {'servo':7s} {'stall':>7s} {'printed':>9s} "
          f"{'solid':>9s}  verdict")
    for jname, js, servo in JOINTS:
        # only what hangs OUTBOARD of this joint loads it; g.mm -> kg.cm
        outboard = [m for m in masses if m[3] > js]
        t_print = sum(m[2] * (m[3] - js) for m in outboard) / 10.0 / 1000.0
        t_solid = sum(m[1] * (m[3] - js) for m in outboard) / 10.0 / 1000.0
        frac = t_print / servo.stall_kgcm
        verdict = "OK" if frac <= DUTY_LIMIT else (
            "TIGHT" if frac <= 1.0 else "OVER STALL")
        print(f"{jname:10s} {servo.name:7s} {servo.stall_kgcm:6.1f}  "
              f"{t_print:8.2f}  {t_solid:8.2f}  {verdict} "
              f"({frac * 100:.0f} % of stall)")
        if frac > DUTY_LIMIT:
            errors.append(
                f"{jname}: {t_print:.2f} kg.cm is {frac * 100:.0f} % of the "
                f"{servo.name}'s stall — over the {DUTY_LIMIT * 100:.0f} % "
                f"duty limit for a statically held load"
            )

    roll_kgcm = PAYLOAD_G * ROLL_OFFSET_MM / 10.0 / 1000.0
    roll_frac = roll_kgcm / WRIST_SERVO.stall_kgcm
    print(f"{'wrist roll':10s} {WRIST_SERVO.name:7s} "
          f"{WRIST_SERVO.stall_kgcm:6.1f}  {roll_kgcm:8.2f}  {'':8s}  "
          f"OK ({roll_frac * 100:.0f} % of stall) — gravity does almost no "
          f"work about a roll axis")
    if roll_frac > DUTY_LIMIT:
        errors.append(
            f"wrist roll: {roll_kgcm:.2f} kg.cm is {roll_frac * 100:.0f} % "
            f"of the {WRIST_SERVO.name}'s stall with the payload "
            f"{ROLL_OFFSET_MM:.0f} mm off the roll axis"
        )

    # --- structural check: is the PLASTIC strong enough, as opposed to the
    # servos? Printed PETG fails first across layers, so use a conservative
    # interlayer allowable rather than the datasheet tensile figure.
    print(f"\n{'section':28s} {'M N.mm':>8s} {'sigma MPa':>10s} {'margin':>8s}")
    shoulder_moment = max(
        sum(m[2] * (m[3] - 0.0) for m in masses if m[3] > 0.0) / 1000.0, 0.0
    ) * 9.81                      # g.mm -> N.mm
    elbow_moment = max(
        sum(m[2] * (m[3] - UPPER_ARM_LEN)
            for m in masses if m[3] > UPPER_ARM_LEN) / 1000.0, 0.0
    ) * 9.81
    for label, moment, second_moment, c in (
        # pedestal root: solid rectangle, bending across the printed layers
        ("shoulder pedestal root", shoulder_moment, 32.0 * 46.0 ** 3 / 12, 23.0),
        # drums: thin-wall tubes, I ~ pi r^3 t
        ("shoulder drum wall", shoulder_moment, 3.14159 * 35.5 ** 3 * 3.0, 35.5),
        ("elbow drum wall", elbow_moment, 3.14159 * 21.0 ** 3 * 3.0, 21.0),
    ):
        sigma = moment * c / second_moment
        margin = PETG_INTERLAYER_MPA / sigma if sigma > 0 else float("inf")
        print(f"{label:28s} {moment:8.1f} {sigma:10.3f} {margin:7.0f}x")
        if margin < 3.0:
            errors.append(f"{label}: only {margin:.1f}x margin on "
                          f"{PETG_INTERLAYER_MPA} MPa interlayer strength")

    # --- what payload does each joint actually allow at the duty limit?
    print()
    payload_s = UPPER_ARM_LEN + FOREARM_LEN + 60.0
    limits = []
    for jname, js, servo in JOINTS:
        if payload_s <= js:
            continue
        bare = sum(m[2] * (m[3] - js)
                   for m in masses if m[3] > js and m[0] != "payload")
        budget = servo.stall_kgcm * DUTY_LIMIT * 1000.0 * 10.0   # -> g.mm
        allowed = (budget - bare) / (payload_s - js)
        limits.append((jname, allowed))
        print(f"payload allowed by the {jname:8s} at "
              f"{DUTY_LIMIT * 100:.0f} % duty: {allowed:5.1f} g")
    if limits:
        worst, cap = min(limits, key=lambda t: t[1])
        print(f"-> rated payload is {cap:.0f} g, set by the {worst}")

    if errors:
        print("\nFAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nOK — every joint holds its worst-case static load inside duty, "
          "and the plastic is nowhere near its limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
