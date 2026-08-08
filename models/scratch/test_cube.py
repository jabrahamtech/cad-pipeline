"""20 mm test cube — pipeline smoke part, proves discovery → build →
invariants → export end to end. Not a real project part."""

from build123d import Box, Part

PART_METADATA = {"expected_solids": 1}


def build(size: float = 20.0) -> Part:
    return Part() + Box(size, size, size)
