# deskmount

Adapter parts for mounting a monitor arm to a thin (~22 mm) desk.

## Printed parts
| Part | Current version | Material | Orientation | Infill |
|---|---|---|---|---|
| clamp_shim | **v4** (`exports/deskmount/clamp_shim_v4.*`) | PETG | standing on an X end face — C-profile flat on the bed, 100 mm tall, no supports | 40 % gyroid, 4 perimeters, 5 top/bottom |
| shim_gauge | **v4** (`exports/deskmount/shim_gauge_v4.*`) — sweep plate, gaps 22/22.5/23 mm labeled; print FIRST, note which gap fits snug | any (PLA fine) | plate imports lying flat, labels up | 10 %, 2 perimeters |

v1 (symmetric 6/6 mm plates, 108.8 cm³) superseded by v2 (4 mm top / 6 mm
bottom plate, depth 68 mm, 85.6 cm³, ~21 % less material/time) before any
print. v2 superseded by v3 after the gauge print found desk = 23 mm (not 20) and throat = 79 mm (not 40) — see calibration/2026-08-10-deskmount-gauge-fit.md. Do not print v1 or v2. v3 superseded by v4: gauge sweep fixed the slot at 22.5 mm (snug) and the bottom plate doubled to 12 mm — print only v4.

## Bought parts
- Monitor arm with C-clamp (user's existing arm; jaw range 10–80 mm,
  foot 60 × 60 mm, pad Ø10, throat 79 mm gauge-observed)
- Monitor: LG 34WN80C-B class 34" ultrawide, 6.3 kg

## Assembly
Slide the shim onto the desk edge (light sliding fit), clamp the arm over
it: foot on the top plate, screw pad centered on the bottom plate,
clamp front against the shim web. Retighten after 24 h — PETG creeps
slightly under sustained clamp load.
