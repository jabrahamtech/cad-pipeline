# robotarm — build notes

## Print set 1: the J1 turret — READY, exported 2026-08-27

Three parts, **92.2 g of PETG**, roughly 2–3 h. This is the first real print of
the project and it is deliberately the base, not the arm: it settles whether J1
turns, on a platter that is already printed and in hand.

| Part | File | Solid | Printed | Orientation |
|---|---|---|---|---|
| `turntable_stator` | `turntable_stator_v1.3mf` / `.step` | 35,297 mm³ | 29.1 g | FLAT, base down, cheeks and posts **up** |
| `turntable_ring` | `turntable_ring_v1.3mf` / `.step` | 15,438 mm³ | 12.7 g | FLAT — it is an annulus |
| `base_lid` | `base_lid_v1.3mf` / `.step` | 60,901 mm³ | 50.3 g | FLAT, brim **on** |

**Material: PETG, and it must be the same spool the gauge plate was printed
on** — a different spool makes every fit an unmeasured assumption again.

**Settings:** 0.2 mm layers, 3 walls, 15–20 % infill, **supports OFF on all
three.** Not "auto". OFF. The stator's stub axles are horizontal Ø7.9 cylinders
bridging off their cheeks, and that bridge carries the bearing load — support
material scars the surface the 608 sits on. `base_lid` needs a brim: it is
171.75 across and 3 mm thick and it will warp without one.

### Bought parts

| | | |
|---|---|---|
| 3 × 608ZZ | have 6 | |
| 1 × SG90 | have 3 | J1 yaw |
| 3 × M3 × 40 socket head | **check stock** | ring → post → platter insert. Longer than a typical assortment holds. |
| 3 × M3 × 12 | | roller axle screws |
| 3 × printed washer | `roller_cap`, on the gauge plate | a standard M3 washer is Ø7 and falls **through** a 608's Ø8 bore |

### What this print is buying an answer to

Named up front so a failure reads as a result rather than a surprise.

1. **The ring's 0.40 mm daylight over the rotor rim.** Two printed Z surfaces at
   `DIM_TOL_Z` 0.25 each. Stack them the wrong way and the ring clamps the rotor
   and J1 will not turn. **Most likely single failure.** Mitigation is designed
   in: sand or shim at the three posts.
2. **Whether a 608 sits on the stub at all.** The gauge plate says the printed
   Ø7.9 runs loose in an Ø8.0 bore. Not fatal — the axle locates and the M3 plus
   `roller_cap` clamps — but it is the first thing to feel for.
3. **Whether the SG90 horn hub clears `tt_screw_bore` Ø6.00.** That hub diameter
   is the one invented number in the J1 gate, which is why the gate reports
   BLOCKED rather than PASS.
4. **The platter's servo column**, 12.45 × 23.05 UNVERIFIED, against a 12.60 mm
   SG90 case — 0.15 of interference nobody has confirmed. **Caliper it before
   pressing the servo in.**

### Gates behind this export

All five green against the exact geometry that was exported:

| Gate | Result |
|---|---|
| `_check_ledger` | PASS — 14 parts, 0.000 drift |
| `_check_j1` | interference 0.000 across −90…+90; **OVERALL BLOCKED** on the SG90 horn hub only |
| `_check_loads` | duty PASS (J2 35 %, J3 77 %, J4 31 %), sections PASS (roller stub 4 %) |
| `_check_fit` | PASS — required by CLAUDE.md before any export |
| `_check_wrist`, `_check_shoulder` | PASS |

## NOT ready to print

- **`shoulder_bracket`** — it is J1's rotor *and* J2's fork, and it is cut from
  MG995 dimensions that are DATASHEET only. The two vendor drawings disagree on
  tab pitch and horn hub, and either would force a rebuild. **Measure the MG995
  in hand first.**
- **The head has no fingers.** `lib/gripcut_finger.py` solves the mechanism and
  `specs/robotarm/gripcut.md` writes it up; the CAD was never started.
- **`forearm_cover`, `upper_arm_cover`** — in the part table since it was
  written, never built.
- **Every fit is HANDBOOK grade.** The gauge plate is printed but was not
  measurable: a 0.1 mm caliper cannot resolve fits that differ by 0.10.
  **A 0.01 mm caliper is the gating purchase for the whole project.**
