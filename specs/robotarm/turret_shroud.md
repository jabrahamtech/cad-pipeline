# turret_shroud — the J1 drum (print 1, dark)

Script: `models/robotarm/turret_shroud.py` · gate: `_check_base.py` (stage 3)

## Why
Between the lid and the ring every render showed bare posts, the 608s, the
MG995, the hall post and the loom. The shroud is a fixed 12-sided skirt from
the lid top to the ring's top face. The turret reads as one drum, the same
dodecagon as the base, with the ring and the rotating shoulder set into it.

## Interface — all READ from the stator's tt_/ts_ parameters
| to | contract |
|---|---|
| turret posts (r 45, Ø11) | 3 saddles, 0.15 press on each post's outer face, z 6 → 25.1 |
| ring (r 50, z 29.5–33.5) | bore Ø102.8 clears it; top flush with the ring top |
| stator plate (r 50, z 0–4) | saddles start at z 6 |
| lid | stands on its top face; nothing else holds it down |

## Cost
J2 down-pitch **25.0° → 23.0°**: the arm now meets the shroud's corners
(r 55.3) instead of the ring (r 50). Asserted ≥ 20°.

## Assembly
After the rotor, BEFORE the ring: slide it down over the three posts.

## Gate
`_check_base`: shroud-on-post press film 60.1 mm³ vs analytic 60.5, no other
contact, PASS.

## Print
Upright, lid end down. The saddle undersides are 45° chamfers. ~26 g.
