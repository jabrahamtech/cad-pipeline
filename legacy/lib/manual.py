"""Build-manual pages: a small PDF toolkit for turning parts into documents.

Generic page furniture only — cover, prose, tables, figures, and 3D renders
with leader-line callouts. The project-specific content lives in
models/<project>/manual.py.

Everything is generated from the models themselves, so a manual cannot drift
away from the geometry the way a hand-drawn one does: move a hole in the
model and the callout moves with it.

    from lib.manual import Manual
    with Manual("out.pdf", "Title") as m:
        m.cover(items, subtitle="...", facts=[...])
        m.table("Bill of materials", headers, rows)
        m.steps("Assembly", [(n, title, body, items_or_None), ...])
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
from build123d import Location, Part

INK = "#1c2128"
MUTED = "#5a626e"
RULE = "#c8ccd4"
ACCENT = "#2f6f8f"
PAPER = "#ffffff"
PANEL = "#f2f4f7"

PAGE = (8.27, 11.69)          # A4 portrait, inches
MARGIN = 0.75


def _mesh(part: Part, location: Location | None, tolerance: float):
    shape = part if location is None else location * part
    verts, faces = shape.tessellate(tolerance)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], dtype=float)
    return v, np.array(faces, dtype=int)


class Manual:
    """A multi-page PDF. Use as a context manager."""

    def __init__(self, path: str | Path, title: str, footer: str = ""):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.backends.backend_pdf import PdfPages

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.title = title
        self.footer = footer
        self._pdf = PdfPages(self.path)
        self._page = 0

    def __enter__(self) -> "Manual":
        return self

    def __exit__(self, *exc) -> None:
        self._pdf.close()

    # --- page furniture -------------------------------------------------
    def _new(self, heading: str | None = None, chapter: str = ""):
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D

        fig = plt.figure(figsize=PAGE)
        fig.patch.set_facecolor(PAPER)
        self._page += 1
        if heading:
            fig.text(MARGIN / PAGE[0], 1 - 0.62 / PAGE[1], heading,
                     fontsize=19, color=INK, fontweight="bold", va="top")
            if chapter:
                fig.text(MARGIN / PAGE[0], 1 - 0.42 / PAGE[1], chapter.upper(),
                         fontsize=8.5, color=ACCENT, va="top",
                         fontweight="bold")
            fig.lines.append(Line2D(
                [MARGIN / PAGE[0], 1 - MARGIN / PAGE[0]],
                [1 - 0.95 / PAGE[1]] * 2,
                transform=fig.transFigure, color=RULE, linewidth=0.8))
        return fig

    def _close(self, fig, number: bool = True) -> None:
        import matplotlib.pyplot as plt

        if number:
            fig.text(1 - MARGIN / PAGE[0], 0.42 / PAGE[1], str(self._page),
                     fontsize=8.5, color=MUTED, ha="right")
            if self.footer:
                fig.text(MARGIN / PAGE[0], 0.42 / PAGE[1], self.footer,
                         fontsize=8.5, color=MUTED)
        self._pdf.savefig(fig, facecolor=PAPER)
        plt.close(fig)

    # --- pages ----------------------------------------------------------
    def cover(self, items: Sequence[tuple[Part, Location | None]],
              subtitle: str = "", facts: Sequence[tuple[str, str]] = (),
              colours: Sequence[str] | None = None,
              azimuth: float = 38.0, elevation: float = 12.0) -> None:
        fig = self._new()
        fig.text(0.5, 0.945, self.title, fontsize=31, color=INK,
                 ha="center", fontweight="bold")
        if subtitle:
            fig.text(0.5, 0.912, subtitle, fontsize=12.5, color=MUTED,
                     ha="center")
        from matplotlib.patches import Rectangle
        ax = fig.add_axes((0.02, 0.36, 0.96, 0.53), projection="3d")
        self._draw(ax, items, colours, azimuth, elevation, 0.4, 0.50)
        if facts:
            y = 0.29
            fig.patches.append(Rectangle(
                (0.09, y - 0.015 - 0.028 * len(facts)), 0.82,
                0.028 * len(facts) + 0.03, transform=fig.transFigure,
                facecolor=PANEL, edgecolor="none", zorder=0))
            for label, value in facts:
                fig.text(0.13, y, label, fontsize=10.5, color=MUTED)
                fig.text(0.87, y, value, fontsize=10.5, color=INK,
                         ha="right", fontweight="bold")
                y -= 0.028
        self._close(fig, number=False)

    def prose(self, heading: str, chapter: str,
              blocks: Sequence[tuple[str, str]]) -> None:
        """blocks are (subheading, body). Subheading may be ''."""
        fig = self._new(heading, chapter)
        y = 1 - 1.35 / PAGE[1]
        for sub, body in blocks:
            if sub:
                fig.text(MARGIN / PAGE[0], y, sub, fontsize=12,
                         color=ACCENT, fontweight="bold", va="top")
                y -= 0.026
            for line in body.strip("\n").split("\n"):
                fig.text(MARGIN / PAGE[0], y, line, fontsize=9.8,
                         color=INK, va="top", family="DejaVu Sans")
                y -= 0.0175
            y -= 0.016
        self._close(fig)

    def table(self, heading: str, chapter: str, headers: Sequence[str],
              rows: Sequence[Sequence[str]],
              widths: Sequence[float] | None = None,
              note: str = "") -> None:
        from matplotlib.lines import Line2D
        from matplotlib.patches import Rectangle
        fig = self._new(heading, chapter)
        n = len(headers)
        widths = list(widths or [1.0 / n] * n)
        x0 = MARGIN / PAGE[0]
        span = 1 - 2 * MARGIN / PAGE[0]
        xs = [x0]
        for w in widths[:-1]:
            xs.append(xs[-1] + w * span)
        y = 1 - 1.35 / PAGE[1]
        for x, h in zip(xs, headers):
            fig.text(x, y, h.upper(), fontsize=8.5, color=ACCENT,
                     fontweight="bold", va="top")
        y -= 0.019
        fig.lines.append(Line2D([x0, x0 + span], [y + 0.006] * 2,
                                    transform=fig.transFigure,
                                    color=RULE, linewidth=0.8))
        y -= 0.008
        for r, row in enumerate(rows):
            if r % 2 == 1:
                fig.patches.append(Rectangle(
                    (x0 - 0.008, y - 0.0155), span + 0.016, 0.0205,
                    transform=fig.transFigure, facecolor=PANEL,
                    edgecolor="none", zorder=0))
            for x, cell in zip(xs, row):
                fig.text(x, y, str(cell), fontsize=9.2, color=INK, va="top")
            y -= 0.0205
        if note:
            y -= 0.012
            for line in note.strip("\n").split("\n"):
                fig.text(x0, y, line, fontsize=8.8, color=MUTED, va="top")
                y -= 0.0155
        self._close(fig)

    def figure(self, heading: str, chapter: str,
               items: Sequence[tuple[Part, Location | None]],
               callouts: Sequence[tuple[str, tuple[float, float, float],
                                        tuple[float, float]]] = (),
               body: str = "", colours: Sequence[str] | None = None,
               azimuth: float = 40.0, elevation: float = 20.0,
               tolerance: float = 0.4, zoom: float = 0.40) -> None:
        """One part or sub-assembly with leader-line callouts.

        Each callout is (label, 3D anchor, (dx, dy) label offset in points).
        Anchors are real model coordinates, so they track the geometry.
        """
        fig = self._new(heading, chapter)
        text_h = 0.017 * (len(body.strip().split("\n")) if body else 0)
        ax = fig.add_axes((0.02, 0.09 + text_h, 0.96, 0.79 - text_h),
                          projection="3d")
        self._draw(ax, items, colours, azimuth, elevation, tolerance, zoom)
        self._callouts(ax, callouts)
        if body:
            y = 0.075 + text_h
            for line in body.strip("\n").split("\n"):
                fig.text(MARGIN / PAGE[0], y, line, fontsize=9.5, color=INK,
                         va="top")
                y -= 0.017
        self._close(fig)

    def canvas(self, heading: str, chapter: str, draw, body: str = "",
               aspect: float = 0.66) -> None:
        """A page with a plain 0..1 x 0..1 drawing area. `draw(ax)` is called
        to render a schematic or diagram onto it."""
        fig = self._new(heading, chapter)
        text_h = 0.017 * (len(body.strip().split("\n")) if body else 0)
        ax = fig.add_axes((0.06, 0.10 + text_h, 0.88, 0.76 - text_h))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, aspect)
        ax.set_aspect("equal")
        ax.axis("off")
        draw(ax)
        if body:
            y = 0.075 + text_h
            for line in body.strip("\n").split("\n"):
                fig.text(MARGIN / PAGE[0], y, line, fontsize=9.5, color=INK,
                         va="top")
                y -= 0.017
        self._close(fig)

    def steps(self, heading: str, chapter: str,
              entries: Sequence[tuple[str, str, str]]) -> None:
        """entries are (number, title, body)."""
        from matplotlib.patches import Circle
        fig = self._new(heading, chapter)
        y = 1 - 1.35 / PAGE[1]
        for num, title, body in entries:
            fig.patches.append(Circle(
                (MARGIN / PAGE[0] + 0.014, y - 0.008), 0.0145,
                transform=fig.transFigure, facecolor=ACCENT,
                edgecolor="none"))
            fig.text(MARGIN / PAGE[0] + 0.014, y - 0.008, num, fontsize=9.5,
                     color="white", ha="center", va="center",
                     fontweight="bold")
            fig.text(MARGIN / PAGE[0] + 0.045, y, title, fontsize=11,
                     color=INK, fontweight="bold", va="top")
            y -= 0.024
            for line in body.strip("\n").split("\n"):
                fig.text(MARGIN / PAGE[0] + 0.045, y, line, fontsize=9.5,
                         color=INK, va="top")
                y -= 0.0172
            y -= 0.014
        self._close(fig)

    # --- drawing --------------------------------------------------------
    def _draw(self, ax, items, colours, azimuth, elevation, tolerance,
              zoom: float = 0.56):
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        ax.set_facecolor(PAPER)
        light = np.array([0.45, -0.75, 0.5])
        light = light / np.linalg.norm(light)
        lo = np.array([np.inf] * 3)
        hi = np.array([-np.inf] * 3)
        tris_all, cols_all = [], []
        for i, entry in enumerate(items):
            part, loc = entry if isinstance(entry, tuple) else (entry, None)
            v, f = _mesh(part, loc, tolerance)
            if len(f) == 0:
                continue
            lo = np.minimum(lo, v.min(axis=0))
            hi = np.maximum(hi, v.max(axis=0))
            tris = v[f]
            n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
            mag = np.linalg.norm(n, axis=1)
            mag[mag == 0] = 1.0
            shade = 0.33 + 0.67 * np.clip(np.abs((n / mag[:, None]) @ light),
                                          0, 1)
            base = (colours[i] if colours and i < len(colours) else "#dfe3e8")
            rgb = np.array([int(base[k:k + 2], 16) / 255 for k in (1, 3, 5)])
            tris_all.append(tris)
            cols_all.append(np.clip(shade[:, None] * rgb[None, :], 0, 1))
        if tris_all:
            ax.add_collection3d(Poly3DCollection(
                np.concatenate(tris_all),
                facecolors=np.concatenate(cols_all), linewidths=0))
        span = float((hi - lo).max()) * zoom
        mid = (hi + lo) / 2
        ax.set_xlim(mid[0] - span, mid[0] + span)
        ax.set_ylim(mid[1] - span, mid[1] + span)
        ax.set_zlim(mid[2] - span, mid[2] + span)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=elevation, azim=azimuth)
        ax.set_axis_off()

    def _callouts(self, ax, callouts):
        from mpl_toolkits.mplot3d import proj3d

        for label, (x, y, z), (dx, dy) in callouts:
            sx, sy, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
            ax.annotate(
                label, xy=(sx, sy), xytext=(dx, dy),
                textcoords="offset points", fontsize=8.0, color=INK,
                ha="left" if dx >= 0 else "right",
                va="center",
                bbox=dict(boxstyle="round,pad=0.32", fc="white", ec=RULE,
                          lw=0.7, alpha=0.95),
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.9,
                                shrinkA=0, shrinkB=2),
            )
