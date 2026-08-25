"""robotarm plate export — ONE Bambu Studio 3MF per plate, not one project
holding all of them.

Every part is authored in its print orientation, so nothing is rotated here.
Each plate is grouped to be a single kind of job, and each lands in its own
file so you can slice, tune and queue them independently:

  1  base            base_platter, Ø176 — the long print, alone
  2  lid             base_lid, Ø171.8 × 3 — fast, thin, low infill
  3  turret          turret_cap + shoulder_bracket + 3 hold-down clips
  4  links           upper_arm + forearm + the upper arm's gable cover
  5  wrist+hand      wrist_mount + wrist_rotator + the claw: five pieces,
                     three designs, two servos
  6  scissors        scissor_cradle + effector_lever — the ALTERNATIVE
                     effector. INCOMPLETE: it bolts to the rotator on the
                     same four M3 the hand uses, but nothing drives the
                     lever — the effector SG90 lost its mount when the wrist
                     was rebuilt, and re-siting it needs the scissors
                     MEASURED. Print plate 5, not this one, and read
                     specs/robotarm/scissor_cradle.md before you do.

Parts are tagged for a two-tone print: the base and turret go on the dark
nozzle, the arm on the light one, matching the colour blocking of an
industrial arm. Set every entry in EXTRUDER to 1 for a single-colour print.

Individual STEP + 3MF per part are written too, for reuse elsewhere.

No part needs support material, so everything packs into the single-nozzle
envelope. Not a printed part itself (no build()), so invariant tests skip it.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/plates.py
"""

import sys
from importlib import util as importlib_util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Mesher, Part, export_step  # noqa: E402

from lib.design_rules import ENVELOPE_SINGLE  # noqa: E402
from lib.plate_export import export_plates  # noqa: E402

# (plate slug, [part names]) — the slug becomes part of the filename
PLATES: list[tuple[str, list[str]]] = [
    ("base", ["base_platter"]),
    ("lid", ["base_lid"]),
    ("turret", ["turret_cap", "shoulder_bracket",
                "turntable_clip", "turntable_clip", "turntable_clip"]),
    ("links", ["upper_arm", "forearm", "upper_arm_cover"]),
    ("hand", ["wrist_mount", "wrist_rotator", "hand_base",
              "hand_finger", "hand_finger"]),
    ("scissors", ["scissor_cradle", "effector_lever"]),
]

# Two-tone body: dark base, light arm, in the reference's colour blocking.
# The X2D has two nozzles, so this costs one filament change per plate at
# most and nothing at all on plates that are all one colour. Set every part
# to 1 if you are printing in a single colour.
DARK, LIGHT = 2, 1
EXTRUDER = {
    "base_platter": DARK, "base_lid": DARK, "turret_cap": DARK,
    "shoulder_bracket": LIGHT, "upper_arm": LIGHT, "forearm": LIGHT,
    "wrist_mount": LIGHT, "wrist_rotator": LIGHT, "hand_base": LIGHT,
    "turntable_clip": DARK, "hand_finger": DARK,
    "upper_arm_cover": LIGHT,
    "scissor_cradle": LIGHT, "effector_lever": DARK,
}
VERSION = "v1"


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    out_dir = REPO_ROOT / "exports" / "robotarm"
    out_dir.mkdir(parents=True, exist_ok=True)

    # a stale combined file would sit next to the per-plate ones and get
    # printed by mistake
    stale = out_dir / f"robotarm_plates_{VERSION}.3mf"
    if stale.exists():
        stale.unlink()
        print(f"removed the old combined {stale.name}\n")

    total_volume = 0.0
    for index, (slug, names) in enumerate(PLATES, start=1):
        built: list[tuple[str, Part, int]] = []
        plate_volume = 0.0
        seen: dict[str, int] = {}
        for name in names:
            part = _load(name).build()
            seen[name] = seen.get(name, 0) + 1
            label = name if names.count(name) == 1 else f"{name}_{seen[name]}"
            built.append((label, part, EXTRUDER.get(name, LIGHT)))
            bb = part.bounding_box()
            plate_volume += part.volume
            print(f"  {label:22s} {part.volume / 1000:6.1f} cm^3  "
                  f"{bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm")
            export_step(part, str(out_dir / f"{name}_{VERSION}.step"))
            mesher = Mesher()
            mesher.add_shape(part)
            mesher.write(str(out_dir / f"{name}_{VERSION}.3mf"))

        out = out_dir / f"robotarm_p{index}_{slug}_{VERSION}.3mf"
        export_plates(
            [built],
            out,
            plate_wd=(ENVELOPE_SINGLE[0], ENVELOPE_SINGLE[1]),
            max_height=ENVELOPE_SINGLE[2],
        )
        total_volume += plate_volume
        print(f"plate {index} -> {out.name}  "
              f"({plate_volume / 1000:.1f} cm^3, "
              f"{plate_volume / 1000 * 1.27:.0f} g PETG)\n")

    print(f"total {total_volume / 1000:.1f} cm^3 "
          f"({total_volume / 1000 * 1.27:.0f} g in PETG) "
          f"across {len(PLATES)} separate plate files")
