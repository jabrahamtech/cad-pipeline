"""Multi-colour paint utilities for Bambu Studio 3MF mesh projects.

Meshy / Bambu Studio store per-triangle filament assignments as a
``paint_color`` attribute on each ``<triangle>`` (MMU segmentation encoding).
This module loads that data as numpy arrays, cleans it up (speckle islands,
ragged boundaries), and writes it back into a copy of the source 3MF so the
project slices unchanged apart from the paint.

Scope: whole-triangle paint states only. Sub-triangle paint strings (longer
encodings from manual brush strokes) are rejected on load rather than
silently mangled.

State convention: 0 = unpainted (object's default filament), N >= 1 = 3MF
filament slot N (1-based, matching Bambu Studio's filament list order).
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

_VERTEX_RE = re.compile(
    rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"'
)
_TRIANGLE_RE = re.compile(
    rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"(?: paint_color="([0-9A-Fa-f]*)")?'
)


# --- paint_color attribute encoding (whole-triangle states) ----------------

def decode_paint(attr: str | None) -> int:
    """paint_color attribute -> filament state (0 = default filament)."""
    if not attr:
        return 0
    if attr == "4":
        return 1
    if attr == "8":
        return 2
    if len(attr) == 2 and attr[1] in "Cc":
        return int(attr[0], 16) + 3
    raise ValueError(
        f"paint_color={attr!r} is a sub-triangle paint stroke; "
        "this module only handles whole-triangle paint"
    )


def encode_paint(state: int) -> str | None:
    """Filament state -> paint_color attribute (None = drop the attribute)."""
    if state == 0:
        return None
    if state == 1:
        return "4"
    if state == 2:
        return "8"
    if 3 <= state <= 18:
        return f"{state - 3:X}C"
    raise ValueError(f"filament state {state} out of range 0..18")


@dataclass
class PaintMesh:
    """Triangle mesh with per-face filament states, tied to a source 3MF."""

    vertices: np.ndarray          # (V, 3) float64, mm
    faces: np.ndarray             # (F, 3) int32 vertex indices
    states: np.ndarray            # (F,) int16 filament state per face
    source_3mf: Path              # zip the mesh came from
    object_entry: str             # path of the object .model inside the zip
    _adjacency: np.ndarray | None = field(default=None, repr=False)

    @property
    def face_count(self) -> int:
        return len(self.faces)

    def face_areas(self) -> np.ndarray:
        v = self.vertices
        a, b, c = (v[self.faces[:, i]] for i in range(3))
        return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)

    def face_centroids(self) -> np.ndarray:
        return self.vertices[self.faces].mean(axis=1)

    def face_adjacency(self) -> np.ndarray:
        """(E, 2) pairs of face indices sharing an edge (cached)."""
        if self._adjacency is None:
            edges = self.faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
            edges.sort(axis=1)
            order = np.lexsort((edges[:, 1], edges[:, 0]))
            se = edges[order]
            same = np.all(se[:-1] == se[1:], axis=1)
            i = np.flatnonzero(same)
            # a face index is edge_row // 3; non-manifold extras pair up too
            self._adjacency = np.stack(
                [order[i] // 3, order[i + 1] // 3], axis=1
            ).astype(np.int32)
        return self._adjacency


def load_paint_mesh(path_3mf: str | Path, object_entry: str | None = None) -> PaintMesh:
    """Load the (single) mesh object and its paint states from a Bambu 3MF."""
    path_3mf = Path(path_3mf)
    with zipfile.ZipFile(path_3mf) as zf:
        if object_entry is None:
            candidates = [
                n for n in zf.namelist()
                if n.startswith("3D/Objects/") and n.endswith(".model")
            ]
            if not candidates:
                # plain 3MF: mesh lives directly in 3D/3dmodel.model
                candidates = ["3D/3dmodel.model"]
            if len(candidates) > 1:
                raise ValueError(
                    f"{path_3mf.name} has {len(candidates)} mesh objects; "
                    f"pass object_entry explicitly: {candidates}"
                )
            object_entry = candidates[0]
        xml = zf.read(object_entry)

    verts = np.array(_VERTEX_RE.findall(xml), dtype=np.float64)
    tris = _TRIANGLE_RE.findall(xml)
    if len(verts) == 0 or len(tris) == 0:
        raise ValueError(f"no mesh found in {path_3mf.name}:{object_entry}")

    faces = np.array([t[:3] for t in tris], dtype=np.int32)
    states = np.array(
        [decode_paint(t[3].decode()) for t in tris], dtype=np.int16
    )
    return PaintMesh(verts, faces, states, path_3mf, object_entry)


# --- diagnostics -----------------------------------------------------------

def paint_islands(mesh: PaintMesh) -> tuple[np.ndarray, np.ndarray]:
    """Connected components of same-state faces.

    Returns (labels (F,), sizes (n_components,)).
    """
    adj = mesh.face_adjacency()
    same = mesh.states[adj[:, 0]] == mesh.states[adj[:, 1]]
    e = adj[same]
    n = mesh.face_count
    g = coo_matrix(
        (np.ones(len(e), dtype=np.int8), (e[:, 0], e[:, 1])), shape=(n, n)
    )
    n_comp, labels = connected_components(g, directed=False)
    sizes = np.bincount(labels, minlength=n_comp)
    return labels, sizes


def paint_stats(mesh: PaintMesh, filament_names: dict[int, str] | None = None) -> str:
    """Human-readable paint report: per-state faces, area, island counts."""
    labels, sizes = paint_islands(mesh)
    areas = mesh.face_areas()
    lines = []
    for s in np.unique(mesh.states):
        sel = mesh.states == s
        comp_ids = np.unique(labels[sel])
        comp_sizes = sizes[comp_ids]
        name = (filament_names or {}).get(int(s), f"state {s}")
        lines.append(
            f"{name}: {sel.sum():>8} faces  {areas[sel].sum():>9.1f} mm²  "
            f"{len(comp_ids):>5} islands  "
            f"(largest {comp_sizes.max()}, "
            f"<10-face islands: {(comp_sizes < 10).sum()})"
        )
    return "\n".join(lines)


# --- cleanup ---------------------------------------------------------------

def majority_smooth(mesh: PaintMesh, iterations: int = 10) -> int:
    """Flip each face to the state >= 2 of its 3 edge-neighbours agree on.

    Removes single-face speckle and staircase boundary noise while leaving
    any feature more than ~2 faces wide alone. Returns total flips.
    """
    adj = mesh.face_adjacency()
    n = mesh.face_count
    # neighbour table (F, 3), -1 padded, built without a Python loop
    src = np.concatenate([adj[:, 0], adj[:, 1]])
    dst = np.concatenate([adj[:, 1], adj[:, 0]])
    order = np.argsort(src, kind="stable")
    src_s, dst_s = src[order], dst[order]
    first = np.searchsorted(src_s, np.arange(n))
    pos = np.arange(len(src_s)) - first[src_s]
    ok = pos < 3  # non-manifold faces keep their first three neighbours
    nbr = np.full((n, 3), -1, dtype=np.int32)
    nbr[src_s[ok], pos[ok]] = dst_s[ok]
    total = 0
    states = mesh.states
    pad = np.concatenate([states, [np.int16(-1)]])  # -1 slot for missing nbr
    for _ in range(iterations):
        s = pad[nbr]  # (F, 3) neighbour states, -1 where no neighbour
        cur = states
        # mode of 3 values exists iff at least two agree
        cand = np.where(s[:, 0] == s[:, 1], s[:, 0],
                        np.where(s[:, 0] == s[:, 2], s[:, 0],
                                 np.where(s[:, 1] == s[:, 2], s[:, 1], -1)))
        flip = (cand >= 0) & (cand != cur)
        if not flip.any():
            break
        states[flip] = cand[flip]
        pad[:-1] = states
        total += int(flip.sum())
    mesh.states = states
    return total


def absorb_small_islands(mesh: PaintMesh, min_area_mm2: float = 1.0) -> int:
    """Reassign same-colour islands below min_area_mm2 to their dominant
    neighbouring colour (weighted by shared boundary edge count).

    An island smaller than ~1 mm² is a filament-change speckle the printer
    can't render cleanly anyway. Returns number of faces reassigned.
    """
    labels, sizes = paint_islands(mesh)
    areas = mesh.face_areas()
    comp_area = np.zeros(len(sizes))
    np.add.at(comp_area, labels, areas)
    small = np.flatnonzero(comp_area < min_area_mm2)
    if len(small) == 0:
        return 0
    small_set = np.zeros(len(sizes), dtype=bool)
    small_set[small] = True

    adj = mesh.face_adjacency()
    la, lb = labels[adj[:, 0]], labels[adj[:, 1]]
    boundary = la != lb
    reassigned = 0
    # vote per small component: most frequent neighbouring state across its
    # boundary edges, preferring large (non-small) neighbours
    votes: dict[int, dict[int, int]] = {}
    for a, b in ((adj[boundary, 0], adj[boundary, 1]),
                 (adj[boundary, 1], adj[boundary, 0])):
        for f, g in zip(a, b):
            lf = labels[f]
            if small_set[lf] and not small_set[labels[g]]:
                votes.setdefault(int(lf), {})
                st = int(mesh.states[g])
                votes[int(lf)][st] = votes[int(lf)].get(st, 0) + 1
    for comp, v in votes.items():
        new_state = max(v.items(), key=lambda kv: kv[1])[0]
        sel = labels == comp
        mesh.states[sel] = new_state
        reassigned += int(sel.sum())
    return reassigned


def clean_paint(mesh: PaintMesh, min_area_mm2: float = 1.0,
                smooth_iterations: int = 10) -> dict[str, int]:
    """Standard cleanup pass: majority smoothing, island absorption, one more
    smoothing to tidy the new boundaries, and a final absorption so the
    result never ends on smoothing-created micro-specks."""
    flips = majority_smooth(mesh, iterations=smooth_iterations)
    absorbed = absorb_small_islands(mesh, min_area_mm2=min_area_mm2)
    flips += majority_smooth(mesh, iterations=smooth_iterations)
    absorbed += absorb_small_islands(mesh, min_area_mm2=min_area_mm2)
    return {"flipped": flips, "absorbed": absorbed}


# --- preview render --------------------------------------------------------

def render_preview(mesh: PaintMesh, state_colors: dict[int, str],
                   out_png: str | Path, yaw_deg: float = 0.0,
                   pitch_deg: float = 15.0, size: int = 900) -> Path:
    """Orthographic z-buffer splat of face centroids, coloured by state.

    Diagnostic-quality render (no lighting) — enough to judge colour regions
    without a slicer round-trip.
    """
    from PIL import Image

    c = mesh.face_centroids()
    yaw, pitch = np.radians(yaw_deg), np.radians(pitch_deg)
    rz = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                   [np.sin(yaw), np.cos(yaw), 0],
                   [0, 0, 1]])  # model is z-up: yaw spins about z
    rx = np.array([[1, 0, 0],
                   [0, np.cos(pitch), -np.sin(pitch)],
                   [0, np.sin(pitch), np.cos(pitch)]])
    # model z-up -> screen: x right, z up, y toward viewer
    p = (c - c.mean(axis=0)) @ rz.T @ rx.T
    x, depth, y = p[:, 0], p[:, 1], p[:, 2]
    span = max(float(np.ptp(x)), float(np.ptp(y))) * 1.08
    px = ((x - x.min() + (span - np.ptp(x)) / 2) / span * (size - 1)).astype(np.int32)
    py = (size - 1 - (y - y.min() + (span - np.ptp(y)) / 2) / span * (size - 1)).astype(np.int32)

    rgb = np.zeros((max(state_colors) + 1, 3), dtype=np.uint8)
    for s, hexcol in state_colors.items():
        h = hexcol.lstrip("#")
        rgb[s] = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    col = rgb[np.clip(mesh.states, 0, len(rgb) - 1)]

    img = np.full((size, size, 3), 30, dtype=np.uint8)
    # viewer sits at -y looking along +y: small depth is near, written last
    order = np.argsort(-depth)
    for dx in (0, 1):
        for dy in (0, 1):
            qx = np.clip(px[order] + dx, 0, size - 1)
            qy = np.clip(py[order] + dy, 0, size - 1)
            flat = qy.astype(np.int64) * size + qx
            img.reshape(-1, 3)[flat] = col[order]
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(out_png)
    return out_png


# --- save ------------------------------------------------------------------

def save_paint_3mf(mesh: PaintMesh, out_3mf: str | Path,
                   filament_colors: list[str] | None = None) -> Path:
    """Write a copy of the source 3MF with this mesh's paint states.

    Geometry and every other project file are copied through untouched;
    only paint_color attributes (and optionally the filament colour list in
    Metadata/project_settings.config) are rewritten.
    """
    out_3mf = Path(out_3mf)
    out_3mf.parent.mkdir(parents=True, exist_ok=True)

    counter = {"i": 0}
    states = mesh.states

    def _sub(m: re.Match) -> bytes:
        i = counter["i"]
        counter["i"] = i + 1
        attr = encode_paint(int(states[i]))
        core = b'<triangle v1="%s" v2="%s" v3="%s"' % (
            m.group(1), m.group(2), m.group(3))
        return core if attr is None else core + b' paint_color="' + attr.encode() + b'"'

    with zipfile.ZipFile(mesh.source_3mf) as src, \
            zipfile.ZipFile(out_3mf, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == mesh.object_entry:
                data = _TRIANGLE_RE.sub(_sub, data)
                if counter["i"] != len(states):
                    raise RuntimeError(
                        f"triangle count mismatch: rewrote {counter['i']}, "
                        f"expected {len(states)}"
                    )
            elif (filament_colors
                  and item.filename == "Metadata/project_settings.config"):
                data = _replace_filament_colours(data, filament_colors)
            dst.writestr(item, data)
    return out_3mf


def _replace_filament_colours(data: bytes, colors: list[str]) -> bytes:
    new = ('"filament_colour": ['
           + ", ".join(f'"{c}"' for c in colors) + "]").encode()
    return re.sub(rb'"filament_colour":\s*\[[^\]]*\]', new, data)
