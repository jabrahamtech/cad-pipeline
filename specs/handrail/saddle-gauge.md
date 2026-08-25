# saddle-gauge — spec

Project: `models/handrail/saddle_gauge.py`
Status: ACCEPTED <!-- v2 printed 2026-08-09, fit confirmed by user;
see calibration/2026-08-09-handrail-saddle-fit.md -->

## Function
15-minute fit prototype for [rail-bracket](rail-bracket.md): a 4 mm slice of
the saddle ring only. Slide onto the rail to verify the bore (16.5 × 30.5,
7.25 mm tip arcs) before committing to the full bracket print.

## Interfaces — the dimensions that matter
All bore dimensions are imported from `rail_bracket.bore_dims()` — this part
cannot drift from the bracket. Reprint after any bore change.

| Interface | Value | Source |
|---|---|---|
| Bore | identical to rail-bracket saddle | CODE (shared function) |

## Loads & environment
None — hand-held fit check only.

## Print plan
PETG (same as bracket, so the fit transfers) · flat on the bed · no supports
· single nozzle · ~10–15 min · 15 % infill, 2 walls.

## Acceptance
- [x] passes over the rail's 7 mm end arcs (v2, 2026-08-09)
- [x] slides along the rail without force, no rattle (v2, 2026-08-09)
- [x] result recorded: calibration/2026-08-09-handrail-saddle-fit.md
