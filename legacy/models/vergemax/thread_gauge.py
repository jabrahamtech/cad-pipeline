"""vergemax thread_gauge — fit-identification rings for the pole thread.

Round 1 (pitch sweep at bore O27.9) all jammed. Photo pixel analysis then
pinned the pitch: crest spacing 45.6 px at 44.4 px/mm (scale from the
known O27.5 silhouette) = 1.02 +/- 0.04 -> 1.0 mm, single start (crests
run square, no helix slant). Diagnosis: the O27.5 caliper reading on fine
crests reads low — the thread is almost certainly nominal M28x1.0, so the
27.9 bores were undersized; round 1 rings also lacked an entry chamfer
(first-layer squish pinched the mouth).

Round 2: pitch fixed at 1.0, bore major swept 28.3 / 28.7 / 29.1
(engraved on top), entry chamfers both ends. The smoothest-running ring
sets pole_adapter's thread size.

Print: PLA, engraved face up, 0.1 mm layers (fine-pitch teeth).
"""

from pathlib import Path
from typing import cast

from bd_warehouse.thread import IsoThread
from build123d import (
    Align,
    Axis,
    Cylinder,
    FontStyle,
    Part,
    Plane,
    Pos,
    Text,
    chamfer,
    extrude,
)

PART_METADATA = {"expected_solids": 1}

POLE_PITCH_MM = 1.0        # photo pixel analysis, single start
MAJOR_CANDIDATES = [28.3, 28.7, 29.1]   # bore majors around nominal M28


def build(
    thread_major: float = 28.7,
    pitch: float = POLE_PITCH_MM,
    ring_od: float = 38.0,
    ring_h: float = 8.0,
    label_depth: float = 0.5,
    entry_chamfer: float = 0.8,      # both bore mouths — beats first-layer squish
) -> Part:
    ring = cast(
        Part,
        Pos(0, 0, ring_h / 2) * Cylinder(ring_od / 2, ring_h)
        - Pos(0, 0, ring_h / 2) * Cylinder(thread_major / 2, ring_h),
    )
    bore_rims = ring.edges().filter_by(
        lambda e: e.geom_type.name == "CIRCLE"
        and abs(e.radius - thread_major / 2) < 0.01
    )
    ring = chamfer(bore_rims, entry_chamfer)
    # thread stays clear of both chamfer cones
    ring += Pos(0, 0, entry_chamfer) * IsoThread(
        major_diameter=thread_major,
        pitch=pitch,
        length=ring_h - 2 * entry_chamfer,
        external=False,
        end_finishes=("fade", "fade"),
    )
    label = cast(
        Part,
        extrude(
            Plane.XY.offset(ring_h)
            * Pos(0, (ring_od / 2 + thread_major / 2) / 2 - 1)
            * Text(
                f"{thread_major:g}",
                font_size=3.4,
                font_style=FontStyle.BOLD,
                align=(Align.CENTER, Align.CENTER),
            ),
            -label_depth,
        ),
    )
    ring -= label
    rims = (
        ring.edges()
        .group_by(Axis.Z)[0]
        .filter_by(lambda e: e.geom_type.name == "CIRCLE"
                   and e.radius > ring_od / 2 - 0.01)
    )
    return cast(Part, chamfer(rims, 0.4))


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "exports" / "vergemax"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    for maj in MAJOR_CANDIDATES:
        part = build(thread_major=maj)
        tag = f"thread_gauge_d{str(maj).replace('.', '_')}_v2"
        export_step(part, str(out / f"{tag}.step"))
        m = Mesher()
        m.add_shape(part)
        m.write(str(out / f"{tag}.3mf"))
        print(
            f"major {maj}: volume {part.volume / 1000:.1f} cm^3, "
            f"solids {len(part.solids())}, valid {part.is_valid}"
        )
