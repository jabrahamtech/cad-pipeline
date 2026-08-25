# handrail — replacement wardrobe-rail bracket

## Printed parts
| Part | Material | Orientation | Infill |
|---|---|---|---|
| rail_bracket_v6 (current) | PETG | flat on its flush side face (plate + stem + saddle all touch the bed), no supports | 40 %, 4+ perimeters |

Fit prototype saddle_gauge_v2 printed 2026-08-09 and confirmed well fitted;
its exports were cleaned up (regenerate any time with
`PYTHONPATH=. .venv/bin/python models/handrail/saddle_gauge.py`).

History: v1 saddle vertical → v2 rotated horizontal → v3 stem centred +
7 mm neck arc → v4 bore tip arcs 7.25 mm → v5 stem flush (prints flat,
no support) → v6 rail length corrected 35 → 30 mm, bore confirmed by
gauge. Superseded exports deleted; git history has the code for each.

Layers must run along the stem (the flat-side orientation gives this) —
printing it plate-down puts the load across layers and it will snap.

## Bought parts
| Item | Qty per bracket | Note |
|---|---|---|
| 4 × 40 mm countersunk wood screws | 2 | any hardware store |
| Wall plugs to suit wall type | 2 | e.g. 6 mm nylon plugs in plaster/masonry |

## Assembly
1. Slide the saddle loop onto the rail from the end (closed loop).
2. Screw plate to wall, countersinks facing out.

Rail corner radius was ASSUMED at 4 mm — if the printed saddle binds on the
rail corners, measure the actual corner radius and revise.
