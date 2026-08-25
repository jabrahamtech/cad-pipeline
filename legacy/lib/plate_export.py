"""Multi-plate Bambu Studio 3MF project export.

Packs build123d Parts onto named build plates and writes ONE Bambu-flavoured
3MF project file, so a whole project (or a print queue) opens in Bambu Studio
with its plates already populated.

Format notes (reverse-engineered from a Bambu Studio 02.07 save and the
BambuStudio source, src/slic3r/GUI/PartPlate.cpp):
- Each part's mesh lives in ``3D/Objects/object_<k>.model`` (production
  extension); the root ``3D/3dmodel.model`` wraps each in a component object
  and places it with a build item in WORLD coordinates.
- Plates tile world space in a near-square grid: ``cols = compute_colum_count
  (round-up sqrt)``, stride = plate size * (1 + 1/5), rows step toward -Y.
- ``Metadata/model_settings.config`` assigns build items to plates via
  ``<plate>/<model_instance>`` blocks keyed on the wrapper object id.
- Bambu Studio only reads that config from project files it recognises as
  its own, so the root model carries the BambuStudio metadata keys.

Meshes are centred on their bounding-box centre inside the object file and
lifted by the build transform so each part sits ON the plate (bottom at
world z = 0), matching Bambu Studio's own convention.

Slicer settings are NOT invented here: pass ``settings_from=`` a 3MF saved
by Bambu Studio (with the right printer/filament profiles) to carry its
``Metadata/project_settings.config`` through; otherwise Bambu Studio applies
whatever presets are active when the file is opened.
"""

from __future__ import annotations

import math
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Union

from build123d import Part

from lib.design_rules import ENVELOPE_SINGLE

# BambuStudio PartPlate.cpp: LOGICAL_PART_PLATE_GAP = 1/5
PLATE_GAP_FRACTION = 1.0 / 5.0

PROJECT_SETTINGS_ENTRY = "Metadata/project_settings.config"

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
    ' <Default Extension="rels" ContentType='
    '"application/vnd.openxmlformats-package.relationships+xml"/>\n'
    ' <Default Extension="model" ContentType='
    '"application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
    "</Types>\n"
)

_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns='
    '"http://schemas.openxmlformats.org/package/2006/relationships">\n'
    ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type='
    '"http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
    "</Relationships>\n"
)

_MODEL_NS = (
    'unit="millimeter" xml:lang="en-US" '
    'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
    'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
    'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
    'requiredextensions="p"'
)


def plate_origin(index: int, plate_count: int,
                 plate_wd: tuple[float, float]) -> tuple[float, float]:
    """World-space origin (min corner) of plate `index`, 0-based.

    Mirrors PartPlateList::compute_colum_count / compute_origin: plates in
    a near-square grid, columns along +X, rows along -Y, 20 % gap.
    """
    value = math.sqrt(plate_count)
    cols = round(value) + 1 if value > round(value) else round(value)
    cols = max(cols, 1)
    col, row = index % cols, index // cols
    return (col * plate_wd[0] * (1 + PLATE_GAP_FRACTION),
            -row * plate_wd[1] * (1 + PLATE_GAP_FRACTION))


@dataclass
class _Placed:
    name: str
    verts: list          # (x, y, z) centred on bbox centre
    faces: list          # (a, b, c)
    size: tuple[float, float, float]
    plate: int           # 0-based
    extruder: int = 1
    world: tuple[float, float, float] = (0.0, 0.0, 0.0)


def _tessellate_centered(part: Part, tolerance: float):
    verts, faces = part.tessellate(tolerance)
    xs = [v.X for v in verts]
    ys = [v.Y for v in verts]
    zs = [v.Z for v in verts]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    cz = (min(zs) + max(zs)) / 2
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    centred = [(v.X - cx, v.Y - cy, v.Z - cz) for v in verts]
    return centred, faces, size


def _shelf_pack(items: list[_Placed], plate_wd: tuple[float, float],
                spacing: float, plate_no: int) -> list[tuple[float, float]]:
    """Row-based packing; returns per-item (x, y) centre offsets from the
    plate centre. Raises if the plate overflows."""
    w, d = plate_wd
    usable_w, usable_d = w - 2 * spacing, d - 2 * spacing
    rows: list[list[_Placed]] = [[]]
    row_w = 0.0
    for it in items:
        need = it.size[0] + (spacing if rows[-1] else 0)
        if rows[-1] and row_w + need > usable_w:
            rows.append([it])
            row_w = it.size[0]
        else:
            rows[-1].append(it)
            row_w += need
    row_depths = [max(i.size[1] for i in r) for r in rows]
    total_d = sum(row_depths) + spacing * (len(rows) - 1)
    if total_d > usable_d:
        raise ValueError(
            f"plate {plate_no + 1} overflows: parts need "
            f"{total_d:.0f} mm of depth, {usable_d:.0f} mm usable "
            f"(spacing {spacing} mm) — split across more plates"
        )
    offsets = []
    y = total_d / 2  # top edge of the packed block, centred on the plate
    for r, rd in zip(rows, row_depths):
        rw = sum(i.size[0] for i in r) + spacing * (len(r) - 1)
        x = -rw / 2
        for it in r:
            offsets.append((x + it.size[0] / 2, y - rd / 2))
            x += it.size[0] + spacing
        y -= rd + spacing
    return offsets


def _uuid(tag: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"cad-pipeline:{tag}"))


def _matrix12(x: float, y: float, z: float) -> str:
    return f"1 0 0 0 1 0 0 0 1 {x:.6g} {y:.6g} {z:.6g}"


def _object_model_xml(mesh_id: int, placed: _Placed) -> str:
    vs = "\n".join(
        f'     <vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>'
        for x, y, z in placed.verts
    )
    ts = "\n".join(
        f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>'
        for a, b, c in placed.faces
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<model {_MODEL_NS}>\n"
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        " <resources>\n"
        f'  <object id="{mesh_id}" p:UUID="{_uuid(f"mesh-{mesh_id}")}" '
        'type="model">\n   <mesh>\n    <vertices>\n'
        f"{vs}\n    </vertices>\n    <triangles>\n{ts}\n    </triangles>\n"
        "   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n"
    )


PlateEntry = Union[tuple[str, Part], tuple[str, Part, int]]


def export_plates(
    plates: Sequence[Sequence[PlateEntry]],
    out_3mf: str | Path,
    *,
    plate_wd: tuple[float, float] = (ENVELOPE_SINGLE[0], ENVELOPE_SINGLE[1]),
    usable_wd: tuple[float, float] | None = None,
    max_height: float = ENVELOPE_SINGLE[2],
    spacing: float = 10.0,
    tolerance: float = 0.05,
    settings_from: str | Path | None = None,
) -> Path:
    """Write a multi-plate Bambu Studio project 3MF.

    plates: one inner list per build plate, each entry (name, part) or
        (name, part, extruder) — extruder 1 or 2 on a dual-nozzle machine,
        which is how a two-tone body gets printed in one job.
    plate_wd: PHYSICAL bed size — drives the world-space plate grid, so it
        must match the printer profile (256 x 256 on the X2D) or Bambu
        Studio's plates and the parts drift apart.
    usable_wd: printable area parts are packed into, centred on the plate;
        defaults to plate_wd. Pass ENVELOPE_DUAL[:2] for support-nozzle
        prints, where the bed stays 256 wide but only 235.5 is printable.
    spacing: min part-to-part and part-to-edge gap on a plate, mm.
    settings_from: a Bambu-Studio-saved 3MF whose project_settings.config
        (printer/filament/process presets) is copied through verbatim.
    """
    if not plates or any(len(p) == 0 for p in plates):
        raise ValueError("every plate needs at least one (name, part) entry")
    if usable_wd is None:
        usable_wd = plate_wd

    placed: list[_Placed] = []
    for pi, plate in enumerate(plates):
        items = []
        for entry in plate:
            # (name, part) or (name, part, extruder)
            name, part = entry[0], entry[1]
            extruder = entry[2] if len(entry) == 3 else 1  # type: ignore[misc]
            verts, faces, size = _tessellate_centered(part, tolerance)
            for axis, limit in enumerate((*usable_wd, max_height)):
                margin = 2 * spacing if axis < 2 else 0
                if size[axis] + margin > limit:
                    raise ValueError(
                        f"{name}: {size[axis]:.1f} mm on axis "
                        f"{'xyz'[axis]} exceeds the plate limit "
                        f"{limit:.1f} mm (spacing {spacing} mm)"
                    )
            items.append(_Placed(name, verts, faces, size, pi, extruder))
        origin = plate_origin(pi, len(plates), plate_wd)
        centre = (origin[0] + plate_wd[0] / 2, origin[1] + plate_wd[1] / 2)
        for it, (dx, dy) in zip(items, _shelf_pack(items, usable_wd,
                                                   spacing, pi)):
            it.world = (centre[0] + dx, centre[1] + dy, it.size[2] / 2)
        placed.extend(items)

    # ids follow the Bambu convention: object k -> mesh id 2k-1 (inside
    # 3D/Objects/object_k.model), wrapper id 2k (root model + configs)
    out_3mf = Path(out_3mf)
    out_3mf.parent.mkdir(parents=True, exist_ok=True)

    wrappers, obj_rels, build_items, cfg_objects, assemble = [], [], [], [], []
    for k, it in enumerate(placed, start=1):
        mesh_id, wrap_id = 2 * k - 1, 2 * k
        wrappers.append(
            f'  <object id="{wrap_id}" p:UUID="{_uuid(f"wrap-{wrap_id}")}" '
            'type="model">\n   <components>\n'
            f'    <component p:path="/3D/Objects/object_{k}.model" '
            f'objectid="{mesh_id}" p:UUID="{_uuid(f"comp-{wrap_id}")}" '
            'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
            "   </components>\n  </object>"
        )
        obj_rels.append(
            f' <Relationship Target="/3D/Objects/object_{k}.model" '
            f'Id="rel-{k}" Type='
            '"http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        )
        m = _matrix12(*it.world)
        build_items.append(
            f'  <item objectid="{wrap_id}" '
            f'p:UUID="{_uuid(f"item-{wrap_id}")}" transform="{m}" '
            'printable="1"/>'
        )
        cfg_objects.append(
            f'  <object id="{wrap_id}">\n'
            f'    <metadata key="name" value="{it.name}"/>\n'
            f'    <metadata key="extruder" value="{it.extruder}"/>\n'
            f'    <part id="{mesh_id}" subtype="normal_part">\n'
            f'      <metadata key="name" value="{it.name}"/>\n'
            '      <metadata key="matrix" value='
            '"1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
            "    </part>\n  </object>"
        )
        assemble.append(
            f'   <assemble_item object_id="{wrap_id}" instance_id="0" '
            f'transform="{m}" offset="0 0 0" />'
        )

    cfg_plates = []
    for pi in range(len(plates)):
        instances = "\n".join(
            "    <model_instance>\n"
            f'      <metadata key="object_id" value="{2 * (k + 1)}"/>\n'
            '      <metadata key="instance_id" value="0"/>\n'
            f'      <metadata key="identify_id" value="{100 * (k + 1)}"/>\n'
            "    </model_instance>"
            for k, it in enumerate(placed) if it.plate == pi
        )
        cfg_plates.append(
            "  <plate>\n"
            f'    <metadata key="plater_id" value="{pi + 1}"/>\n'
            '    <metadata key="plater_name" value=""/>\n'
            '    <metadata key="locked" value="false"/>\n'
            f"{instances}\n  </plate>"
        )

    root_model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<model {_MODEL_NS}>\n"
        ' <metadata name="Application">BambuStudio-02.07.01.62</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        " <resources>\n" + "\n".join(wrappers) + "\n </resources>\n"
        f' <build p:UUID="{_uuid("build")}">\n'
        + "\n".join(build_items) + "\n </build>\n</model>\n"
    )
    model_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns='
        '"http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "\n".join(obj_rels) + "\n</Relationships>\n"
    )
    model_settings = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
        + "\n".join(cfg_objects) + "\n"
        + "\n".join(cfg_plates) + "\n"
        " <assemble>\n" + "\n".join(assemble) + "\n </assemble>\n</config>\n"
    )

    project_settings = None
    if settings_from is not None:
        with zipfile.ZipFile(settings_from) as zf:
            project_settings = zf.read(PROJECT_SETTINGS_ENTRY)

    with zipfile.ZipFile(out_3mf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _ROOT_RELS)
        zf.writestr("3D/3dmodel.model", root_model)
        zf.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        for k, it in enumerate(placed, start=1):
            zf.writestr(f"3D/Objects/object_{k}.model",
                        _object_model_xml(2 * k - 1, it))
        zf.writestr("Metadata/model_settings.config", model_settings)
        if project_settings is not None:
            zf.writestr(PROJECT_SETTINGS_ENTRY, project_settings)
    return out_3mf
