"""Shaded PNG previews of build123d parts.

The pipeline's rule is to check work numerically and render only when a
question cannot be answered with numbers (CLAUDE.md). Appearance is exactly
that kind of question, so this exists to answer it cheaply: tessellate, shade
by face normal, write a PNG.

It is a VERIFICATION tool, not a source of truth — nothing here feeds back
into geometry.

    from lib.preview import render
    render([(part, Location())], "out.png", azimuth=35, elevation=20)
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from build123d import Location, Part

# a light, neutral studio palette so shape reads clearly
BACKGROUND = "#f4f4f6"
DEFAULT_COLOUR = "#d8dade"
EDGE_COLOUR = "#5a5f66"
LIGHT_DIR = np.array([0.45, -0.75, 0.5])


def _mesh(part: Part, location: Location | None, tolerance: float):
    shape = part if location is None else location * part
    verts, faces = shape.tessellate(tolerance)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], dtype=float)
    f = np.array(faces, dtype=int)
    return v, f


def render(
    items: Sequence[tuple[Part, Location | None]] | Iterable[Part],
    out_png: str | Path,
    *,
    colours: Sequence[str] | None = None,
    azimuth: float = 35.0,
    elevation: float = 22.0,
    tolerance: float = 0.35,
    size: tuple[int, int] = (1400, 1000),
    dpi: int = 100,
    title: str | None = None,
    show_edges: bool = False,
) -> Path:
    """Render parts to a shaded PNG. `items` may be bare Parts or
    (part, location) pairs."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    pairs: list[tuple[Part, Location | None]] = []
    for it in items:
        if isinstance(it, tuple):
            pairs.append(it)
        else:
            pairs.append((it, None))

    fig = plt.figure(figsize=(size[0] / dpi, size[1] / dpi), dpi=dpi)
    fig.patch.set_facecolor(BACKGROUND)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(BACKGROUND)

    light = LIGHT_DIR / np.linalg.norm(LIGHT_DIR)
    lo = np.array([np.inf] * 3)
    hi = np.array([-np.inf] * 3)

    # ONE collection for everything: matplotlib depth-sorts within a
    # collection but not between them, so separate collections make near
    # parts disappear behind far ones.
    all_tris: list[np.ndarray] = []
    all_cols: list[np.ndarray] = []
    for index, (part, loc) in enumerate(pairs):
        v, f = _mesh(part, loc, tolerance)
        if len(f) == 0:
            continue
        lo = np.minimum(lo, v.min(axis=0))
        hi = np.maximum(hi, v.max(axis=0))
        tris = v[f]
        n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        norm = np.linalg.norm(n, axis=1)
        norm[norm == 0] = 1.0
        n = n / norm[:, None]
        shade = 0.30 + 0.70 * np.clip(np.abs(n @ light), 0.0, 1.0)
        base = colours[index] if colours and index < len(colours) else (
            DEFAULT_COLOUR)
        rgb = np.array([int(base[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        all_tris.append(tris)
        all_cols.append(np.clip(shade[:, None] * rgb[None, :], 0, 1))

    if all_tris:
        coll = Poly3DCollection(
            np.concatenate(all_tris),
            facecolors=np.concatenate(all_cols),
            linewidths=0.15 if show_edges else 0,
            edgecolors=EDGE_COLOUR if show_edges else "none",
        )
        coll.set_sort_zpos(None)
        ax.add_collection3d(coll)

    span = float((hi - lo).max()) * 0.55
    mid = (hi + lo) / 2
    ax.set_xlim(mid[0] - span, mid[0] + span)
    ax.set_ylim(mid[1] - span, mid[1] + span)
    ax.set_zlim(mid[2] - span, mid[2] + span)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_axis_off()
    if title:
        ax.set_title(title, color="#33383f", fontsize=13, pad=2)

    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, facecolor=BACKGROUND, bbox_inches="tight",
                pad_inches=0.05)
    plt.close(fig)
    return out_png
