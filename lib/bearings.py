"""Deep-groove ball bearings (COTS — never modelled as a printed part).

Only the mounting-relevant dimensions live here: a bearing is a bought part,
so parts in models/ cut pockets and axles from these numbers.
knowledge/bearings_rotation.md holds selection and pocket-design guidance.

inner_race_od: how far the inner race extends — a clamping pad must stay
inside this or it rubs the outer race. 608ZZ's value is from the datasheet
and confirmed in use (robotarm); the others are DATASHEET nominals — verify
against the purchased bearing before clamping against the race.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BearingSpec:
    name: str
    bore: float
    od: float
    width: float
    inner_race_od: float

    @property
    def radius(self) -> float:
        return self.od / 2


# The common skate bearing. Runs on an M8 bolt as its axle. IN USE (robotarm).
B608ZZ = BearingSpec(
    name="608ZZ", bore=8.0, od=22.0, width=7.0, inner_race_od=12.0
)

# Small hobby sizes — DATASHEET nominals, not yet used in a printed part.
B623ZZ = BearingSpec(name="623ZZ", bore=3.0, od=10.0, width=4.0, inner_race_od=4.8)
B625ZZ = BearingSpec(name="625ZZ", bore=5.0, od=16.0, width=5.0, inner_race_od=7.6)
B688ZZ = BearingSpec(name="688ZZ", bore=8.0, od=16.0, width=5.0, inner_race_od=10.4)
B6000ZZ = BearingSpec(name="6000ZZ", bore=10.0, od=26.0, width=8.0, inner_race_od=14.8)
B6001ZZ = BearingSpec(name="6001ZZ", bore=12.0, od=28.0, width=8.0, inner_race_od=17.2)

CATALOG = {b.name: b for b in (B608ZZ, B623ZZ, B625ZZ, B688ZZ, B6000ZZ, B6001ZZ)}

# M8 hardware for the 608 axle (DATASHEET, DIN 934 / DIN 985)
M8_NUT_AF = 13.0
M8_NUT_THICK = 6.5
M8_NYLOC_THICK = 8.0
M8_WASHER_OD = 16.0
M8_WASHER_THICK = 1.6
