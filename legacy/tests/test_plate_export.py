"""Unit tests for lib/plate_export.py — multi-plate Bambu 3MF structure."""

import xml.etree.ElementTree as ET
import zipfile

import pytest
from build123d import Box

from lib import plate_export as pe

CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"


def _export(tmp_path, plates, **kw):
    return pe.export_plates(plates, tmp_path / "out.3mf", **kw)


def _build_items(path):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("3D/3dmodel.model"))
    return root.findall(f"{CORE}build/{CORE}item")


def _plate_blocks(path):
    with zipfile.ZipFile(path) as zf:
        cfg = ET.fromstring(zf.read("Metadata/model_settings.config"))
    return cfg.findall("plate")


def _attr(elem, name):
    value = elem.get(name)
    assert value is not None
    return value


def _translation(item):
    return [float(v) for v in _attr(item, "transform").split()[9:]]


def test_package_structure(tmp_path):
    out = _export(tmp_path, [[("a", Box(10, 10, 10))],
                             [("b", Box(20, 10, 5))]])
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert {"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model",
            "3D/_rels/3dmodel.model.rels", "3D/Objects/object_1.model",
            "3D/Objects/object_2.model",
            "Metadata/model_settings.config"} <= names
    # no settings template given -> no project_settings.config
    assert pe.PROJECT_SETTINGS_ENTRY not in names


def test_meshes_are_centred_and_lifted_to_plate(tmp_path):
    out = _export(tmp_path, [[("a", Box(10, 20, 30))]])
    with zipfile.ZipFile(out) as zf:
        obj = ET.fromstring(zf.read("3D/Objects/object_1.model"))
    verts = obj.findall(f".//{CORE}vertex")
    zs = [float(_attr(v, "z")) for v in verts]
    assert min(zs) == pytest.approx(-15) and max(zs) == pytest.approx(15)
    (item,) = _build_items(out)
    # single plate: centred on the 256 bed, bottom on the plate
    assert _translation(item) == pytest.approx([128, 128, 15])


def test_two_plates_use_bambu_grid_stride(tmp_path):
    out = _export(tmp_path, [[("a", Box(10, 10, 10))],
                             [("b", Box(10, 10, 10))]])
    items = _build_items(out)
    xs = sorted(_translation(i)[0] for i in items)
    # plate 2 sits one stride (256 * 1.2) right of plate 1
    assert xs[1] - xs[0] == pytest.approx(256 * 1.2)

    plates = _plate_blocks(out)
    assert len(plates) == 2
    ids = []
    for p in plates:
        inst = p.find("model_instance/metadata[@key='object_id']")
        assert inst is not None
        ids.append(_attr(inst, "value"))
    assert ids == ["2", "4"]  # wrapper ids 2k


def test_parts_on_one_plate_do_not_overlap(tmp_path):
    out = _export(tmp_path, [[("a", Box(60, 40, 10)),
                              ("b", Box(60, 40, 10)),
                              ("c", Box(60, 40, 10))]], spacing=10)
    items = _build_items(out)
    boxes = []
    for it, size in zip(items, [(60, 40), (60, 40), (60, 40)]):
        tx, ty, _ = _translation(it)
        boxes.append((tx - size[0] / 2, tx + size[0] / 2,
                      ty - size[1] / 2, ty + size[1] / 2))
        # inside the plate with the edge margin respected
        assert boxes[-1][0] >= 10 - 1e-6 and boxes[-1][1] <= 246 + 1e-6
        assert boxes[-1][2] >= 10 - 1e-6 and boxes[-1][3] <= 246 + 1e-6
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            assert (a[1] <= b[0] or b[1] <= a[0]
                    or a[3] <= b[2] or b[3] <= a[2])


def test_oversize_part_rejected(tmp_path):
    with pytest.raises(ValueError, match="exceeds the plate limit"):
        _export(tmp_path, [[("big", Box(250, 50, 10))]])  # 250+2*10 > 256


def test_plate_overflow_rejected(tmp_path):
    plate = [(f"p{i}", Box(110, 110, 5)) for i in range(6)]
    with pytest.raises(ValueError, match="overflows"):
        _export(tmp_path, [plate])


def test_settings_template_copied_through(tmp_path):
    template = tmp_path / "template.3mf"
    with zipfile.ZipFile(template, "w") as zf:
        zf.writestr(pe.PROJECT_SETTINGS_ENTRY, '{"printer_model": "X2D"}')
    out = _export(tmp_path, [[("a", Box(5, 5, 5))]], settings_from=template)
    with zipfile.ZipFile(out) as zf:
        assert b"X2D" in zf.read(pe.PROJECT_SETTINGS_ENTRY)


def test_empty_plate_rejected(tmp_path):
    with pytest.raises(ValueError, match="at least one"):
        _export(tmp_path, [[("a", Box(5, 5, 5))], []])
