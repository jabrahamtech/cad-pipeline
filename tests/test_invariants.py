"""Invariant checks for every part in models/.

Every models/<project>/<part>.py must expose `build(**params) -> Part`
with sane defaults. Optional module-level PART_METADATA dict:
    expected_solids: int        (default 1)
    needs_support_material: bool  (default False → single-nozzle envelope)

No golden files. These assert properties that must hold for ANY output
of the pipeline, regardless of design intent.

Run:  .venv/bin/pytest tests/ -v
"""

import inspect
import math
import sys
from importlib import util as importlib_util
from pathlib import Path

import pytest
from build123d import export_step, export_stl

from lib.design_rules import (
    ENVELOPE_DUAL,
    ENVELOPE_SINGLE,
    MIN_WALL_MM,
)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def discover_parts():
    for py in sorted(MODELS_DIR.rglob("*.py")):
        if py.name.startswith("_"):
            continue
        spec = importlib_util.spec_from_file_location(py.stem, py)
        assert spec and spec.loader
        mod = importlib_util.module_from_spec(spec)
        sys.modules[py.stem] = mod
        spec.loader.exec_module(mod)
        build = getattr(mod, "build", None)
        if build is None:
            continue
        meta = getattr(mod, "PART_METADATA", {})
        yield pytest.param((build, meta), id=str(py.relative_to(MODELS_DIR)))


PARTS = list(discover_parts())
if not PARTS:
    pytest.skip("no part scripts found under models/", allow_module_level=True)


@pytest.fixture(params=PARTS, scope="module")
def built(request):
    """Build each part once for the whole module, not once per test."""
    build, meta = request.param
    return build, build(), meta


def test_geometry_is_valid(built):
    _, part, _ = built
    # build123d >= 0.11: is_valid is a property, not a method
    assert part.is_valid, "OCC reports invalid geometry"


def test_is_watertight_solid(built):
    _, part, meta = built
    solids = part.solids()
    expected = meta.get("expected_solids", 1)
    assert len(solids) == expected, (
        f"expected {expected} solid(s), got {len(solids)} — stray body, "
        f"failed boolean, or open shell?"
    )
    assert part.volume > 0 and math.isfinite(part.volume)


def test_fits_print_envelope(built):
    """Bounding box fits the envelope for the part's declared print mode.

    Orientation-agnostic: passes if ANY axis permutation of the bbox fits.
    """
    _, part, meta = built
    env = ENVELOPE_DUAL if meta.get("needs_support_material") else ENVELOPE_SINGLE
    bb = part.bounding_box()
    dims = sorted([bb.size.X, bb.size.Y, bb.size.Z])
    assert all(d <= e for d, e in zip(dims, sorted(env))), (
        f"bbox {[round(d, 1) for d in dims]} mm exceeds envelope {env} — "
        f"split the part or flag it"
    )


def test_default_wall_params_meet_minimum(built):
    """Wall/thickness parameter DEFAULTS in build()'s signature must respect
    the minimum wall. Catches a parametric default drifting too thin; full
    geometric thin-wall analysis is deliberately out of scope here.
    """
    build, _, _ = built
    for name, p in inspect.signature(build).parameters.items():
        if not isinstance(p.default, (int, float)):
            continue
        if any(k in name.lower() for k in ("wall", "thickness", "web")):
            assert p.default >= MIN_WALL_MM, (
                f"default {name}={p.default} below minimum wall {MIN_WALL_MM} mm"
            )


def test_exports_cleanly(built, tmp_path):
    """STL and STEP export must succeed — catches degenerate geometry that
    validates but won't mesh."""
    _, part, _ = built
    stl = tmp_path / "part.stl"
    step = tmp_path / "part.step"
    export_stl(part, str(stl))
    export_step(part, str(step))
    assert stl.stat().st_size > 100, "STL export empty/degenerate"
    assert step.stat().st_size > 100, "STEP export empty/degenerate"
