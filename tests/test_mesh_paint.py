"""Unit tests for lib/mesh_paint.py on tiny synthetic 3MF files."""

import zipfile

import numpy as np
import pytest

from lib import mesh_paint as mp

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="model" '
    'ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)


def make_3mf(path, vertices, triangles, filament_colours=None):
    """Write a minimal Bambu-style 3MF: triangles = (v1, v2, v3, state)."""
    vs = "\n".join(
        f'<vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in vertices
    )
    ts = []
    for v1, v2, v3, state in triangles:
        attr = mp.encode_paint(state)
        paint = "" if attr is None else f' paint_color="{attr}"'
        ts.append(f'<triangle v1="{v1}" v2="{v2}" v3="{v3}"{paint}/>')
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter">'
        f"<resources><object id=\"1\" type=\"model\"><mesh>"
        f"<vertices>{vs}</vertices><triangles>{''.join(ts)}</triangles>"
        "</mesh></object></resources>"
        '<build><item objectid="1"/></build></model>'
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("3D/3dmodel.model", model)
        if filament_colours:
            cfg = ('{"filament_colour": ['
                   + ", ".join(f'"{c}"' for c in filament_colours) + "]}")
            zf.writestr("Metadata/project_settings.config", cfg)
    return path


# regular tetrahedron: every face borders the other three
TETRA_VERTS = [(0, 0, 0), (10, 0, 0), (5, 8.66, 0), (5, 2.89, 8.16)]
TETRA_FACES = [(0, 1, 2), (0, 1, 3), (1, 2, 3), (0, 2, 3)]


def tetra_3mf(tmp_path, states, colours=None):
    tris = [(*f, s) for f, s in zip(TETRA_FACES, states)]
    return make_3mf(tmp_path / "t.3mf", TETRA_VERTS, tris, colours)


def test_paint_encoding_roundtrip():
    for state in range(19):
        assert mp.decode_paint(mp.encode_paint(state)) == state
    assert mp.decode_paint(None) == 0
    assert mp.decode_paint("") == 0
    with pytest.raises(ValueError):
        mp.decode_paint("104C")  # sub-triangle stroke
    with pytest.raises(ValueError):
        mp.encode_paint(19)


def test_load_mesh_and_states(tmp_path):
    m = mp.load_paint_mesh(tetra_3mf(tmp_path, [0, 1, 2, 5]))
    assert m.face_count == 4
    assert len(m.vertices) == 4
    assert m.states.tolist() == [0, 1, 2, 5]


def test_face_adjacency_tetrahedron(tmp_path):
    m = mp.load_paint_mesh(tetra_3mf(tmp_path, [0, 0, 0, 0]))
    adj = m.face_adjacency()
    assert len(adj) == 6  # tetrahedron has 6 edges, each shared by 2 faces
    pairs = {frozenset(p) for p in adj.tolist()}
    assert pairs == {frozenset(c) for c in
                     [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]}


def test_majority_smooth_flips_odd_face(tmp_path):
    m = mp.load_paint_mesh(tetra_3mf(tmp_path, [1, 2, 2, 2]))
    flips = mp.majority_smooth(m)
    assert flips == 1
    assert m.states.tolist() == [2, 2, 2, 2]


def test_majority_smooth_keeps_balanced_split(tmp_path):
    # 2 vs 2: neither face has >= 2 neighbours of the other colour... on a
    # tetrahedron each face touches both other-colour faces, so states where
    # no strict majority exists must survive
    m = mp.load_paint_mesh(tetra_3mf(tmp_path, [1, 1, 2, 2]))
    mp.majority_smooth(m, iterations=1)
    assert sorted(m.states.tolist()) == [1, 1, 2, 2]


def test_absorb_small_island(tmp_path):
    m = mp.load_paint_mesh(tetra_3mf(tmp_path, [3, 2, 2, 2]))
    # face areas are ~43 mm² here, so threshold above that absorbs face 0
    absorbed = mp.absorb_small_islands(m, min_area_mm2=50.0)
    assert absorbed == 1
    assert m.states.tolist() == [2, 2, 2, 2]


def test_paint_islands_counts(tmp_path):
    m = mp.load_paint_mesh(tetra_3mf(tmp_path, [1, 1, 2, 2]))
    labels, sizes = mp.paint_islands(m)
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]
    assert sorted(sizes[np.unique(labels)].tolist()) == [2, 2]


def test_save_roundtrip_with_palette(tmp_path):
    src = tetra_3mf(tmp_path, [0, 1, 2, 3], ["#111111", "#222222"])
    m = mp.load_paint_mesh(src)
    m.states = np.array([4, 4, 0, 1], dtype=np.int16)
    out = mp.save_paint_3mf(m, tmp_path / "out.3mf",
                            filament_colors=["#ABCDEF", "#123456"])
    m2 = mp.load_paint_mesh(out)
    assert m2.states.tolist() == [4, 4, 0, 1]
    assert np.allclose(m2.vertices, m.vertices)
    with zipfile.ZipFile(out) as zf:
        cfg = zf.read("Metadata/project_settings.config").decode()
    assert '"#ABCDEF", "#123456"' in cfg
