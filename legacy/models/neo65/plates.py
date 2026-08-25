"""neo65 multi-plate project export — frame (plate 1) + canopy (plate 2).

Both parts print in their as-built orientation (frame flat on the rib-feet
plane, canopy legs-down), so no pre-rotation is needed. One 3MF opens in
Bambu Studio with both plates populated; both parts need support material
(dual-nozzle mode).

Not a printed part itself (no build()), so invariant tests skip this file.
"""

from pathlib import Path
from importlib import util as importlib_util
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from lib.design_rules import ENVELOPE_DUAL  # noqa: E402
from lib.plate_export import export_plates  # noqa: E402


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    frame = _load("frame").build()
    canopy = _load("canopy").build()
    out = REPO_ROOT / "exports" / "neo65" / "neo65_plates_v1.3mf"
    export_plates(
        [
            [("frame", frame)],
            [("canopy", canopy)],
        ],
        out,
        # both parts need support material -> pack into the dual-nozzle
        # printable area (bed geometry stays the physical 256 x 256)
        usable_wd=(ENVELOPE_DUAL[0], ENVELOPE_DUAL[1]),
        max_height=ENVELOPE_DUAL[2],
    )
    print(f"wrote {out.relative_to(REPO_ROOT)}")
