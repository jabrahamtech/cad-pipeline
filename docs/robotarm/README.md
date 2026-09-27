# robotarm — what to buy, what to print (current as of 2026-09-27)

J1 = MG995 360° (continuous) · J2 = MG995 · J3–J6 = SG90 · ESP32 on a carrier
PCB in the base. Specs: `specs/robotarm/base_platter.md`, `_harness.md`,
`_build.md` (arm assembly), `_state.md`. The previous version of this file
(the SG90-J1 turret print set) is in git history.

## Print — new or changed on 2026-09-27

| # | file (`exports/robotarm/`) | qty | orientation · notes |
|---|---|---|---|
| 0 | `gauge_broach_v1.3mf` | 1 | FIRST. Its G row (MG995 spline) settles the press-fit j1_hub is cut to |
| 1 | `base_platter_v3.3mf` | 1 | floor down, no support · Ø190 · ~133 g |
| 2 | `base_lid_v8.3mf` | 1 | TOP FACE DOWN (tie bridges grow up), brim · ~63 g |
| 3 | `turntable_stator_v8.3mf` | 1 | base down, supports OFF (stub axles bridge) · ~36 g |
| 4 | `j1_hub_v2.3mf` | 1 | top face down, 5 walls, 40 % infill · cable cup |
| 5 | `shoulder_bracket_v4.3mf` | 1 | −X face down · **or** keep the printed one: drill the centre bore to Ø6.5 and glue the magnet flat |

## Print — unchanged arm parts (skip any already printed)

| part | qty | notes |
|---|---|---|
| turntable_ring | 1 | bore is the J1 journal — do not sand |
| shoulder_hub | 1 | the FLANGELESS one |
| wrist_hub | 3 | J2 idler + J4 both sides |
| upper_arm | 1 | Ø3.4 elbow bolt bore (drill a printed one) |
| forearm | 1 set | printed MG90S forearm + `j4_tab_shim` ×2, or new `forearm_px`, `forearm_nx`, `forearm_rail` ×2 |
| j3_gear, j3_pinion, j3_axle, j3_servo_cap | 1 each | elbow 2:1 |
| wrist_roll | 2 | one design, second MIRRORED |
| wrist_rotator | 1 | front face down; takes 4 heat-set inserts |
| pruner_shell / pruner_blade / pruner_rack | 2 each | |
| gripper_pinion | 1 | |
| gripcut_finger | 2 | TOP FACE DOWN or the flexure fails |

Arm plates: `exports/robotarm/plates/plate_armstack_{green,white}_v8`,
`plate_wrist_green_v8`, `plate_wrist_white_v9`.

## Buy

**Motion + sensing**
- MG995 360° ×1, MG995 ×1, SG90 ×4 (in hand)
- 608ZZ ×4: 3 turntable, 1 elbow (in hand)
- A3144 hall sensor (TO-92) ×1 (pack of 5–10)
- **5 × 2 mm** N52 disc magnets ×1 (pack), not 6 × 2

**Wiring** (`_harness.md`)
- Silicone wire 20 AWG red + black, 2 m each; 22 AWG red + black, 1 m each
- Silicone wire 26 AWG, 5 colours, 2 m each
- Dupont crimp kit (M/F pins, 1–4 pin housings) + crimper; heat-shrink assortment
- Braided PET sleeving 6 mm (1 m) and 3 mm (2 m); 2.5 mm zip ties; 10 × 10 mm stick-on tie mounts (pack)

**Power**
- 5 V 10 A supply with bare leads (through the rim pass-through, zip-tied)
- Toggle switch rated ≥ 10 A DC, 12–13 mm thread, panel ≤ 3 mm
- Electrolytic caps: 1000 µF ≥ 10 V ×1, 100 µF ≥ 10 V ×2

**Fasteners**
- M3 heat-set inserts Ø4.0 hole: 11 (7 base, 4 wrist_rotator) + spares
- M3 socket: ×40 ×4 (3 turret, 1 elbow); ×16 ×2 (j3 cap); ×12 ×3 (roller axles); ×10 ×3 (hub to rotor); ×8 ×8 (4 lid, 4 head to rotator); ×6 ×4 (J1 MG995 tabs)
- M3 × 35 + nyloc ×2 (pruner shells); M3 × 8 ×4 (J2 MG995 tabs)
- M2 × 20 + nut ×3 (wrist_roll clamshell); servo screws as supplied
- Printed roller caps ×3 (Ø11) retain the 608s. They're the `roller_cap` body in `gauge_fits_v4.3mf`; print 3. A standard M3 washer falls through.
