"""vergemax clamp_bar_gauge — minimal fit-check hub for clamp_bar.

Same generator cut down to the attachment hub only: the boss with its stud
socket (O16.15 x 31), the 1/4"-20 captive-nut pocket, 2 mm web, M3 lock
hole, and a 45 mm square cap at the full 30 mm plate thickness. Boss is
centred, throat-clearance guard waived — the clamp throat/pad coverage is
NOT tested by this gauge (accepted risk; datasheet says the jaw takes
20-70 mm, so thickness itself is safe).

Checks, in order: nut drops down the O22 access bore and finger-seats in
the hex pocket; gauge spins onto the stand's 1/4"-20 tip and bottoms on
the stud shoulder; socket wobble (loose / sliding / tight).

Print: PLA is fine for a fit gauge; note PETG usually prints a touch
tighter, so a snug PLA socket may need +0.1 mm clearance for the PETG run.
"""

from build123d import Part

from models.vergemax.clamp_bar import build as clamp_bar_build

PART_METADATA = {"expected_solids": 1}


def build(cap_size: float = 45.0, **kwargs) -> Part:
    return clamp_bar_build(
        plate_width=cap_size,
        plate_depth=cap_size,
        boss_rear_offset=cap_size / 2,
        require_jaw_clearance=False,
        **kwargs,
    )


if __name__ == "__main__":
    from pathlib import Path

    from build123d import Mesher, export_step

    part = build()
    out = Path(__file__).resolve().parents[2] / "exports" / "vergemax"
    out.mkdir(parents=True, exist_ok=True)
    export_step(part, str(out / "clamp_bar_gauge_v3.step"))
    m = Mesher()
    m.add_shape(part)
    m.write(str(out / "clamp_bar_gauge_v3.3mf"))
    bb = part.bounding_box()
    print(
        f"volume {part.volume / 1000:.1f} cm^3, "
        f"mass(PLA solid) {part.volume / 1000 * 1.24:.0f} g, "
        f"bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
        f"solids {len(part.solids())}, valid {part.is_valid}"
    )
