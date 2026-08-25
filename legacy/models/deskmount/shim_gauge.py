"""deskmount shim_gauge — 4 mm-wide slices of clamp_shim for fit checks.

Spec: specs/deskmount/shim_gauge.md. Geometry is clamp_shim.build() at
reduced width — shared code, so gauges cannot drift from the real part.

v4 is a slot-gap sweep plate (calibration 2026-08-10): three slices with
slot gaps 22.0 / 22.5 / 23.0 mm, each gap debossed on the top face.
Whichever slides onto the desk snugly sets the shim's final slot. Each
slice also re-verifies the 79 mm throat (pad fully on the bottom plate).
"""

from pathlib import Path
from typing import cast

from build123d import Part, Plane, Pos, Rot, Text, extrude

from models.deskmount.clamp_shim import build as shim_build

PART_METADATA = {"expected_solids": 1}

GAP_SWEEP_MM = (22.0, 22.5, 23.0)   # bracket around the ~23 mm desk; v3
                                    # nominal was 23.5 and felt loose to user
LABEL_DEPTH_MM = 0.6
LABEL_FONT_MM = 4.0


def build(width: float = 4.0, slot_gap: float | None = None) -> Part:
    """Full clamp_shim profile at gauge width; all fit dims identical.
    Default slot_gap None = the shim's own slot (desk + sliding clearance).
    """
    return shim_build(width=width, slot_gap=slot_gap)


def labeled_gauge(slot_gap: float, width: float = 4.0) -> Part:
    """Gauge slice with its gap debossed on the +X face (top when printed
    lying flat, bed on the -X face)."""
    part = build(width=width, slot_gap=slot_gap)
    text = (Plane.YZ.offset(width)
            * Pos(45, 3)                     # centred on the bottom plate strip
            * Text(f"{slot_gap:g}", font_size=LABEL_FONT_MM))
    return cast(Part, part - extrude(text, -LABEL_DEPTH_MM))


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "exports" / "deskmount"
    out.mkdir(parents=True, exist_ok=True)
    from build123d import Mesher, export_step

    # lay each slice flat (label face up) and space them along X
    plate: list[Part] = []
    for i, gap in enumerate(GAP_SWEEP_MM):
        g = cast(Part, Rot(0, -90, 0) * labeled_gauge(gap))
        bb = g.bounding_box()
        plate.append(cast(
            Part, Pos(i * 45 - bb.min.X, -bb.min.Y, -bb.min.Z) * g
        ))

    assembly = Part() + plate
    export_step(assembly, str(out / "shim_gauge_v4.step"))
    m = Mesher()
    for g in plate:
        m.add_shape(g)
    m.write(str(out / "shim_gauge_v4.3mf"))
    bb = assembly.bounding_box()
    print(f"gaps {GAP_SWEEP_MM} mm, volume {assembly.volume / 1000:.1f} cm^3, "
          f"mass(PETG) {assembly.volume / 1000 * 1.27:.1f} g, "
          f"plate bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"solids {len(assembly.solids())}, valid {assembly.is_valid}")
