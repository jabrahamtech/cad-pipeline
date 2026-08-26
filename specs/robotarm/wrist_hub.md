# wrist_hub — spec

Project: `models/robotarm/wrist_hub.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
The J4 pivot. One printed design, two copies, doing two different jobs:

- **drive side** — the wrist MG90S's trimmed horn keys into the pocket in
  its back face. The servo turns the hub, the hex turns the effector, and
  the servo's own output bearing carries it.
- **idler side** — the identical part runs free in the opposite fork plate's
  bore, retained by an M3 screw through the same pocket. Its horn slot is an
  unused void.

Fulfils the "J4 pivot" and "effector mount" rows of
`specs/robotarm/_assembly.md`.

**Why the effector's socket is a hex and not a round journal.** Both
journals live in the *fork*, so this socket only has to transmit torque and
index — which is what lets it be **3.4 mm deep**, all the room there is
beside the gripper's own servo. A round journal would have had to carry the
load as well, and 3.4 mm is nowhere near enough bearing length for that.
Six flats also index an effector every 60° when setting the wrist range.

## Interfaces — the dimensions that matter

| Interface | Value | Source | Joint / fit |
|---|---|---|---|
| hex across flats | 15.80 mm | derived `wr_pivot_af − loc` | **locational (0.20)** |
| hex reach | 6.20 mm | derived: 2.71 gap + 3.49 socket | — |
| journal collar | Ø18.0 × 5.0 | `wr_hub_d`, `wr_journal` | **rotating (0.35)** in the fork bore |
| MG90S horn hub | Ø7.0 | DATASHEET | press (0.15) → Ø7.15 |
| MG90S horn blade | 1.5 mm | DATASHEET | 1.6 mm slot |
| horn arm TRIMMED to | 6.0 mm radius | design decision | leaves 4.33 mm wall to the hex flats |
| screw bore | Ø5.5 through | — | horn screw / M3 retainer |

The clearance goes on the HEX, not the socket: grow the hole, shrink
nothing (joints_tolerances.md). The gripper's socket stays nominal at 16.0
and this part comes down to 15.8.

## Loads & environment
Static, indoor, low duty. Worst case is the wrist holding the whole gripper
plus payload: **0.42 kg·cm**, shared by two hubs, so ~2.1 N·cm each through
a 15.8 mm hex — negligible for PETG. The hub is sized by the horn it has to
swallow, not by load.

## Cables & service
n/a — unpowered. Serviceable: pull the M3 on the idler side and the horn
screw on the drive side, and the effector drops out of the fork. That IS the
effector swap — no bolt circle, no four screws.

## Print plan
PETG · **collar face on the bed, built +z** · single nozzle · 40 % infill,
4 walls · no support. Every cross-section shrinks going up (collar → hex),
and the hex flats end up loaded within layers, which is the direction the
wrist's torque runs.

Dark filament — `_style.md` rule 5, a hub reads as a joint.

## Acceptance
- [x] built and verified numerically; wall to the horn relief 4.33 mm
- [ ] `_check_fit.py` — needs `wrist_fork` before the pair can be placed
- [ ] **gauge the hex fit** — `locational` 0.20 into a 3.4 mm deep socket has
      never been gauged in PETG on this printer, and a hex is less forgiving
      than a round bore
- [ ] printed and verified — date, measured result, deviations

## ASSUMED / unverified
Every MG90S horn dimension is DATASHEET, carried over from the SG90 drawing
(lib/servo.py records them as the same). If the horn will not press in,
`wh_horn_hub_d`, `wh_horn_arm_w` and `wh_horn_arm_depth` are the suspects.
