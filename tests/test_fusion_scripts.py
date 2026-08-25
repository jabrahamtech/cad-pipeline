"""Static lint for the scripts in models/.

The system recognises three kinds of script, each with its own contract.

1. FUSION PART SCRIPT (the default). Runs inside Fusion via the MCP, so
   adsk is only importable there and it can't be executed headlessly —
   the contract from fusion/PLAYBOOK.md is enforced by AST inspection:
   - module docstring (frame, spec, ASSUMED values)
   - `def run(_context)` entry point with exactly one argument
   - imports adsk.core / adsk.fusion
   - prints diagnostics (body count / bbox / volume / isValid)
   - references a component name prefixed with its project folder
     (`<project>_...`) — the idempotent delete-and-rebuild target

2. MESH DRIVER (imports lib.mesh_paint). CLAUDE.md's imported-mesh
   exception: runs headlessly with .venv/bin/python to process a Meshy /
   scan 3MF, so it has a CLI entry, not run(_context). Contract: module
   docstring, a `__main__` guard or main(), and printed diagnostics.

3. HELPER (filename starts with `_`): check/assembly scripts, safety
   subset only.

All three share the safety rules: NO try/except (the traceback is the
debugging signal — Fusion scripts only) and no build123d / bd_warehouse /
legacy imports, public or private (Fusion-only system; the frozen
build123d pipelines live in legacy/ and private/legacy/).

Run:  .venv/bin/pytest tests/ -q
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIRS = [REPO_ROOT / "models", REPO_ROOT / "private" / "models"]

FORBIDDEN_IMPORTS = ("build123d", "bd_warehouse", "legacy", "lib.cots")


def discover_scripts():
    for models_dir in MODELS_DIRS:
        if not models_dir.is_dir():
            continue
        for py in sorted(models_dir.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            yield pytest.param(py, id=str(py.relative_to(models_dir)))


SCRIPTS = list(discover_scripts())
if not SCRIPTS:
    pytest.skip("no fusion scripts under models/", allow_module_level=True)


@pytest.fixture(params=SCRIPTS, scope="module")
def script(request):
    path = request.param
    source = path.read_text()
    return path, source, ast.parse(source, filename=str(path))


def _imported_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _is_mesh_driver(tree):
    """CLAUDE.md imported-mesh exception: a headless driver that processes
    an external mesh with lib/mesh_paint.py, not a Fusion part script."""
    return any(
        n == "mesh_paint" or n.endswith(".mesh_paint") or n == "lib"
        for n in _imported_names(tree)
    ) and any(
        isinstance(n, ast.Name) and n.id == "mesh_paint"
        or isinstance(n, ast.alias) and n.asname == "mp"
        for n in ast.walk(tree)
    )


def _prints(tree):
    return [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == "print"
    ]


def test_no_try_except(script):
    path, _, tree = script
    if _is_mesh_driver(tree):
        pytest.skip("mesh driver — runs headlessly, may handle CLI errors")
    offenders = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Try)]
    assert not offenders, (
        f"{path.name}: try/except at line(s) {offenders} — never catch in "
        f"Fusion scripts, the traceback is the debugging signal"
    )


def test_no_forbidden_imports(script):
    path, _, tree = script
    bad = {
        n for n in _imported_names(tree)
        if any(n == f or n.startswith(f + ".") for f in FORBIDDEN_IMPORTS)
    }
    assert not bad, f"{path.name}: forbidden import(s) {sorted(bad)} — Fusion-only system"


def test_mesh_driver_contract(script):
    """Mesh drivers (CLAUDE.md imported-mesh exception) run headlessly:
    docstring, a CLI entry, and printed diagnostics. Geometry is never
    hand-edited — the driver only processes an external source mesh."""
    path, source, tree = script
    if not _is_mesh_driver(tree):
        pytest.skip("not a mesh driver")

    assert ast.get_docstring(tree), f"{path.name}: missing module docstring"
    has_main = any(
        isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body
    ) or "__main__" in source
    assert has_main, (
        f"{path.name}: mesh driver needs a CLI entry (main() or a "
        f"`if __name__ == \"__main__\"` guard) — it runs with "
        f".venv/bin/python, not inside Fusion"
    )
    assert _prints(tree), f"{path.name}: must print() what it did (paint stats, export path)"


def test_part_script_contract(script):
    path, source, tree = script
    if path.name.startswith("_"):
        pytest.skip("helper script — safety checks only")
    if _is_mesh_driver(tree):
        pytest.skip("mesh driver — see test_mesh_driver_contract")

    assert ast.get_docstring(tree), f"{path.name}: missing module docstring"

    runs = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "run"
    ]
    assert len(runs) == 1, f"{path.name}: must define exactly one run()"
    args = runs[0].args
    n_args = len(args.args) + len(args.posonlyargs)
    assert n_args == 1 and not args.vararg and not args.kwonlyargs, (
        f"{path.name}: run() must take exactly one argument (def run(_context))"
    )

    imported = _imported_names(tree)
    assert "adsk.core" in imported and "adsk.fusion" in imported, (
        f"{path.name}: must import adsk.core and adsk.fusion"
    )

    assert _prints(tree), f"{path.name}: must print() diagnostics (bbox/volume/isValid)"

    project = path.parent.name
    strings = {
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }
    assert any(s.startswith(f"{project}_") for s in strings), (
        f"{path.name}: no '{project}_<part>' component name found — scripts "
        f"must target a named component for idempotent rebuild"
    )


def test_docstring_names_spec_or_driver(script):
    """A part script's docstring must reference its spec (spec-first
    workflow) or declare itself a driver script (imported meshes etc.)."""
    path, _, tree = script
    if path.name.startswith("_"):
        pytest.skip("helper script")
    doc = (ast.get_docstring(tree) or "").lower()
    assert "spec" in doc or "driver" in doc, (
        f"{path.name}: docstring must reference 'Spec: specs/...' or "
        f"declare itself a driver script"
    )


def test_multi_part_projects_have_assembly_spec():
    """A project with 2+ Fusion part scripts is an assembly: it needs
    specs/<project>/_assembly.md (or the older _project.md) with the piece
    tree, joint contracts, and assembly order BEFORE pieces multiply.
    Helpers and mesh drivers don't count as pieces.
    See knowledge/assembly_decomposition.md."""
    for models_dir in MODELS_DIRS:
        if not models_dir.is_dir():
            continue
        for proj in sorted(p for p in models_dir.iterdir() if p.is_dir()):
            if proj.name in ("scratch", "__pycache__"):
                continue
            parts = [
                p for p in proj.glob("*.py")
                if not p.name.startswith("_")
                and not _is_mesh_driver(ast.parse(p.read_text()))
            ]
            if len(parts) < 2:
                continue
            specs_dir = REPO_ROOT / "specs" / proj.name
            if models_dir.parts[-2:] == ("private", "models"):
                specs_dir = REPO_ROOT / "private" / "specs" / proj.name
            assert (specs_dir / "_assembly.md").exists() or (
                specs_dir / "_project.md"
            ).exists(), (
                f"{proj.name}: {len(parts)} part scripts but no "
                f"specs/{proj.name}/_assembly.md — decompose-first rule "
                f"(knowledge/assembly_decomposition.md)"
            )
