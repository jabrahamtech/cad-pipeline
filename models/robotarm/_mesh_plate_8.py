"""robotarm/_mesh_plate_8 - the 2026-10-17 reprint plate (PETG): J5 rotator v5, J4 pinion v6, AS5600 glue pins,
J1 hub v7 (Jonathan: "add them all to one plate"; plate 9 folded in).

Lays out the parts the three generators wrote (run them first, into exports/robotarm/cobot/parts):
  _mesh_cobot_rotator_v5.py, _mesh_j4_pinion_v6.py, _mesh_as5600_glue_pins.py, _mesh_j1_hub_v7.py
Usage: python3 models/robotarm/_mesh_plate_8.py <parts_dir> <out_dir>
"""
import os
import sys

import trimesh

PLATE = 'cobot_plate_8_all_petg.3mf'
BED_C = 128.0
PIN_PITCH = 6.0
PINS = 16


def place(sc, name, m, x, y):
    g = m.copy(); c = g.bounds.mean(0)
    g.apply_translation([x - c[0], y - c[1], -g.bounds[0, 2]])
    sc.add_geometry(g, geom_name=name, node_name=name)
    return g


def main(parts, out_dir):
    load = lambda n: trimesh.load(os.path.join(parts, n))
    sc = trimesh.Scene()
    placed = [place(sc, 'cobot_rotator_v5', load('cobot_rotator_v5.stl'), BED_C - 13.0, BED_C + 6.0),
              place(sc, 'cobot_j4_pinion_v6', load('cobot_j4_pinion_v6.stl'), BED_C + 13.0, BED_C + 6.0)]
    placed.append(place(sc, 'cobot_j1_hub_v7', load('cobot_j1_hub_v7.stl'), BED_C, BED_C + 6.0 + 10.5 + 4.0 + 21.6))
    pin = load('as5600_glue_pin_v1.stl')
    for k in range(PINS):
        i, j = k % 8, k // 8
        placed.append(place(sc, 'as5600_glue_pin_%d' % k, pin,
                            BED_C + (i - 3.5) * PIN_PITCH, BED_C - 13.0 - j * PIN_PITCH))
    for a in range(len(placed)):
        for b in range(a + 1, len(placed)):
            lo = [max(placed[a].bounds[0, i], placed[b].bounds[0, i]) for i in (0, 1)]
            hi = [min(placed[a].bounds[1, i], placed[b].bounds[1, i]) for i in (0, 1)]
            assert lo[0] >= hi[0] or lo[1] >= hi[1], 'parts %d and %d overlap on the plate' % (a, b)
    p = os.path.join(out_dir, PLATE); sc.export(p)
    print('plate 8: rotator v5, J4 pinion v6, J1 hub v7, %d AS5600 glue pins -> %s' % (PINS, p))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
