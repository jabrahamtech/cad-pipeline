# Verge Max pole adapter — spec

Project: `models/vergemax/pole_adapter.py`
Status: MODELED (thread confirmed by gauge: pitch 1.0, bore major 28.7)

## Function
O40 x 54.5 mm puck that screws the amaran Verge desk-clamp POLE (with its
Verge Lock head) directly onto a Neewer ST-200 light stand, replacing the
desk-clamp base. Supersedes the clamp_bar fake-desk-edge design — same
stand receiver (lib/stand_socket), no plate, no desk clamp in the stack.

## Interfaces — the dimensions that matter

| Interface | Value | Source |
|---|---|---|
| Neewer stud diameter (5/8") | Ø15.9 mm | MEASURED |
| Neewer 5/8" stud length (incl. base collar) | 31 mm | MEASURED |
| Stud base collar | Ø21 × 4 mm — counterbore Ø21.25 × 4.3, step seats on collar shoulder | MEASURED |
| 1/4"-20 tip: thread length | 5 mm | MEASURED |
| 1/4"-20 hex nut (captive) AF 11.11 × 5.6 | COTS | DATASHEET |
| Pole male thread crest | Ø27.5 mm | MEASURED |
| Pole thread pitch | 1.0 mm, single start (photo pixel analysis: 45.6 px crest spacing / 44.4 px/mm; ring pitch-sweep eliminated multi-start) | MEASURED (photo) |
| Pole thread bore major | 28.7 (ring sweep winner; see calibration/2026-08-14-verge-pole-thread-fit.md) | GAUGE-FIT |
| Pole thread length | 12 mm | MEASURED |
| Pole shoulder (seats on top face) | Ø30 mm | MEASURED |
| Stud-to-socket fit | sliding, 0.25 mm diametral | design rule |
| Printed female thread allowance | +0.4 mm diametral | ASSUMED |

## Loads & environment
Static indoor. ~3.6 kg light on the pole; tipping moment ~9 N·m passes
through the printed thread joint (~2 MPa at the body section) into the
steel stud. Fine-pitch teeth (~0.7 mm) are below the 0.8 mm feature rule —
print at 0.1 mm layers; gauge rings verify the thread prints and fits.

## Print plan
PETG · upright, bottom on bed (thread axis vertical, all steps widen
upward; single 16 mm bridge over the socket) · single nozzle · 40 %
infill, 5 walls, 0.1 mm layers.

## Gauges
1. `thread_gauge` rings (PLA, pitch 1.0 / 1.111 / 1.25, labelled): the one
   that spins the full 12 mm smoothly sets `pole_pitch`.
2. `clamp_bar_gauge` hub: same stand receiver — verifies stud socket fit
   and captive-nut engagement.

## Acceptance
- [ ] invariant tests pass
- [ ] gauge rings identify pitch; adapter threads onto pole smoothly
- [ ] fits stand stud (sliding) and bottoms on shoulder without wobble
- [ ] printed and verified — date, measured result, deviations

On ACCEPTED: record measured fit deviations in `calibration/`.
