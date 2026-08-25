"""AABB layout helpers for COTS internals reference assemblies.

Used by models/<project>/_internals.py scripts (op1field, tp7): every bought
part is modeled as an axis-aligned datasheet-sized box inside the enclosure
cavity, so containment and collision checks are exact interval math — no
boolean operations needed. Geometry is built only for STEP/3MF export.

Conventions: cavity coordinates have their origin at the front-left-floor
corner; component entries are (name, size (w, d, h), min-corner pos).
"""

from typing import cast

from build123d import Box, Part, Pos

Vec3 = tuple[float, float, float]
Component = tuple[str, Vec3, Vec3]


def overlap_1d(a0: float, a1: float, b0: float, b1: float) -> float:
    return min(a1, b1) - max(a0, b0)


def check_aabb_layout(parts: list[Component], cavity: Vec3) -> list[str]:
    """Exact containment + pairwise collision check. Returns error strings."""
    errors = []
    for name, size, pos in parts:
        for axis in range(3):
            if pos[axis] < -1e-9 or pos[axis] + size[axis] > cavity[axis] + 1e-9:
                errors.append(f"{name} outside cavity on axis {'xyz'[axis]}")
    for i, (na, sa, pa) in enumerate(parts):
        for nb, sb, pb in parts[i + 1:]:
            pen = [overlap_1d(pa[k], pa[k] + sa[k], pb[k], pb[k] + sb[k])
                   for k in range(3)]
            if all(p > 1e-9 for p in pen):
                errors.append(f"{na} ∩ {nb}: {[round(p, 2) for p in pen]} mm")
    return errors


def hung(size: Vec3, cx: float, cy: float, cavity_h: float) -> Vec3:
    """Min corner for a body centered at (cx, cy) hanging from the cavity top."""
    w, d, h = size
    return (cx - w / 2, cy - d / 2, cavity_h - h)


def labeled_box(name: str, size: Vec3, pos: Vec3) -> Part:
    w, d, h = size
    x, y, z = pos
    b = cast(Part, Part() + Pos(x + w / 2, y + d / 2, z + h / 2) * Box(w, d, h))
    b.label = name
    return b


def envelope_shell(outer: Vec3, wall: float) -> Part:
    """Open-top tray dummy (floor + walls, no lid) positioned so the cavity
    min corner is at origin. Open so the layout stays visible in opaque
    viewers like Bambu Studio — the real enclosure lid is its own part."""
    cavity = (outer[0] - 2 * wall, outer[1] - 2 * wall, outer[2] - 2 * wall)
    cutter = Pos(cavity[0] / 2, cavity[1] / 2, outer[2] / 2) * Box(
        cavity[0], cavity[1], outer[2]
    )
    shell = cast(Part, Part() + (
        Pos(cavity[0] / 2, cavity[1] / 2, cavity[2] / 2)
        * Box(outer[0], outer[1], outer[2])
        - cutter
    ))
    shell.label = "envelope_shell"
    return shell
