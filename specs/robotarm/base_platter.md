# base_platter — spec (Fusion rebuild, replaces the printed legacy platter)

Project: `models/robotarm/base_platter.py`
Status: MODELED — 2026-09-27, restyled 2026-09-28 (12-sided pedestal, black) · gate `_check_base.py` PASS · current exports `base_platter_v6` (eyes), `base_lid_v10`, `turntable_stator_v10`, `turret_shroud_v1`, `shoulder_bracket_v5`, `j1_hub_v5`

## Why this exists
Jonathan, 2026-09-27: J1 base yaw becomes an **MG995 360° (continuous)**; J2
shoulder stays the standard MG995; the electronics are now an **ESP32 on a
small carrier PCB with cables off BOTH faces**; the breadboard is dropped;
toggle switch and DC jack stay in the rim; all other cables leave the base
through the TOP only.

The printed legacy platter (`base_platter_measured.md`) cannot take any of
this: its yaw column is 12.45 × 23.05 (SG90) against an MG995 case of
40.9 × 20.2. That file stays as the record of the old part; this one
supersedes it for design.

## Function
Holds the J1 servo on the yaw axis, the ESP32 carrier, the home switch, the
toggle switch and DC jack; carries the turntable on the SAME `tt_*` contract
the stator already uses, so `turntable_stator`, `turntable_ring` and the
rotor keep their fixing pattern.

## Interfaces — the dimensions that matter

| Interface | Value | Source | Joint / fit |
|---|---|---|---|
| Turret mount | 3 × **Ø12** posts (was Ø8.8), 2.0 root fillet, M3 insert Ø4.0 × 8, r 45.0, az 120/180/240 | `tt_post_r` contract; Ø from `lib/j1_drive.TT_POST_D_MM` | insert, design_rules |
| Shell | **12-sided**, 190 across flats (196.7 across corners) × 42, vertices at 30° + k·30°, wall 3.0, floor 2.4, 3.0 foot facet; lid recess Ø186.8 × 3.0 (round, inside the flats) | CHOSEN — bay + finger gaps beside a 40.9 servo need r ~90; dodecagon matches the ring's 12 lobes and `turret_shroud` (2026-09-28 restyle, flutes dropped) | — |
| Eyes | 2 × 5 mm LED on the two front flats at az ±15° (either side of the +X corner), z −15, 49 mm apart; Ø5.3 bore, Ø6.3 × 1.2 flange seat from inside a 4 mm teardrop boss, Ø8 × 0.8 socket outside — the dome shows ~2.8 mm | Jonathan 2026-09-28: "led holes on the base platter like eyes" | push fit |
| Lid columns | 4 × Ø8.8 at r 88, az 45/135/225/315, M3 insert Ø4.0 × 6 — merge into the wall | CHOSEN | insert |
| J1 servo | MG995 360° — case 40.9 × 20.2 × 36.5, tab pitch 47.8 × 10.2, tab below top 7.2 | **Jonathan 2026-09-27: "same as the other big motor"** → `lib/servo.py` MG995 (l CONFIRMED, w MEASURED, rest DATASHEET) | locational (0.20) on case, slots per `MG995_TAB_SLOT_X_MM` |
| J1 servo insertion | drops in from ABOVE: case through the stator window (case + 1.0) and the lid opening (+1.0 more); tabs land on the stator pad; lead follows down the stator keyway and the lid opening | Jonathan: "keep room for the cables and clearance to insert it" | SERVO_CASE_CLEARANCE 1.0 + play 1.0 |
| J1 servo below tab underside | 26.8 | DERIVED 36.5 − 7.2 − 2.5 | floor clearance ≥ 1.0 |
| J1 servo orientation | case along +Y, shaft on axis, lead exit toward −Y | stator frame (`turntable_stator.py`) | — |
| ESP32 carrier PCB | **70 × 50 × 1.3** board | MEASURED (Jonathan 2026-09-27; 1.3 "probably") | corner ledges + L fences |
| PCB mounting holes | **unknown** | — | none used: corner ledges + L fences hold it |
| PCB + ESP32 + cables, both faces | **70 × 50 × 30 envelope, total** (both faces confirmed) | Jonathan 2026-09-27 | keep-out box + 1.5 all round |
| PCB insertion | lowered in from above, lid off, onto 4 corner ledges inside 4 L fences; **1.0 play total**; 12 mm finger gap past each short end; sides open for cables | Jonathan: "leave tolerance to put it in" | 0.5 a side, by hand |
| Cable bundle to the top exit | wire count unknown — sized for 30 × dupont Ø1.4 → bundle ≈ Ø9 → channel ≥ Ø13.5 | ASSUMED; `CABLE_CHANNEL_FACTOR` 1.5 | free |
| Toggle switch | thread Ø13.1 → Ø13.35 hole, panel ≤ 3.0 | MEASURED (legacy spec) | clearance |
| DC cable | Ø9.7 → Ø9.95 pass-through + zip-tie block | MEASURED (legacy spec) | clearance + strain relief |
| Home sensor | **A3144 hall (TO-92UA)** flat on a Ø12 stator post at **r 33.7, az 210**, face z 20.6; **5 × 2 mm N52 magnet** in a Ø5.2 × 1.0 pocket under the rotor (shoulder_bracket, rotor az 150) → 2.5 gap; 1.5 if glued flat to an un-pocketed rotor | DATASHEET; gap ASSUMED — bench-check | locational pocket + glue |
| Lid | Ø186.6 × 3 in the Ø186.8 recess; 4 × M3 at r 88; turret posts through Ø12.7 | `base_lid.py` | locational (0.20) |

## Layout (as built, stator frame: z 0 = rim top, J1 axis, az from +X)
- **J1 MG995** lies along +Y under the stator, case x ±10.1, y −10..30.9, bottom z −20.7 — 18.9 above the floor. Nothing in the base enters it; it drops in from above through the stator and lid.
- **Stator** (revised): rollers moved to az **30/150/270** so the case passes between them; posts unchanged at 120/180/240. Loom window at **az 330, r 22–29.5** — directly over the ESP32 bay (plug-sized). Home-sensor post at az 210.
- **ESP32 bay**: board 50 (x) × 70 (y) at **x 16–66, y ±35**, underside z −25.25 (mid-height, ASSUMED). Four corner **ledges** (2.5 in) inside four **L fences** (3.0), **1.0 insertion play** total. Sides open between corners so bottom-face cables come out and up. 12 mm finger gap past each short end.
- **Rim**: toggle Ø13.35 at az 165, DC Ø9.95 at az 195, both z −21; zip-tie bridge inside the DC entry.
- **Lid** (`base_lid.py`, rewritten): servo opening (case window + lead keyway + 1.0 play), loom window under the stator's, two zip-tie bridges on the underside either side of it, Ø7 hall-lead hole, 12 vents at r 62.

## Cable routes
| Cable | Route |
|---|---|
| Arm loom (J2–J6) | rotor gate → **coiled 110 mm in the j1_hub cable cup** → under the cup's lip at az 330 → stator window → lid window → tied at the lid's underside bridges → **straight down onto the bay**. Harness: `_harness.md` |
| J1 MG995 lead | case −Y end → stator keyway → lid servo opening → floor → bay |
| Hall sensor | pocket → post slot → stator plate → lid Ø7 hole at az 210 → along the floor round the servo's −Y end → bay |
| ESP32 top-face cables | straight up through the lid's loom window, beside the loom |
| DC in | rim az 195 → zip-tie bridge → bay |
| Toggle | rim az 165 |

## Loads & environment
Static indoor. Carries the whole arm's overturning moment through the
3 posts; J1 reaction torque (MG995 9.4 kg·cm stall) through the servo tabs.
Mass stays low — this is the tipping ballast.

## Cables & service
Board removable without desoldering: slide out of the rails upward once the
lid is off. Strain relief: zip-tie block at the DC entry and at the top exit.
Continuous J1 + fixed cabling = **software rotation limit ±180° from home**
(no slip ring). **Service access to the ESP32 means lifting the turret (3 × M3) and then the lid** — see open items. USB on the ESP32 must stay reachable with the lid off.

## Print plan
PETG · flat, open side up · no support expected · 4 walls at the servo
pocket and posts · 20 % infill.

## Revision 2026-09-27 (same day) — what changed and why
| # | Change | Why | Volume Δ |
|---|---|---|---|
| 1 | Loom window 210 → **330**, home post 330 → **210** | the loom now drops onto the board instead of crossing under the MG995; ESP32 top cables exit straight up | stator +105 (post 1.0 taller) |
| 2 | Magnet **pocket** in the rotor at rotor-az 150; magnet Ø6 → **Ø5** | home = gate over window = loom untwisted, so ±180° is symmetric; a Ø6.2 pocket could not keep MIN_WALL to the rim | bracket −21 |
| 3 | Turret posts Ø8.8 → **Ø12** + 2.0 root fillets; lid holes Ø9.5 → Ø12.7 | 40 mm columns carry the arm's tipping moment; ~3.5× stiffer | platter +6315, lid −502 |
| 4 | Lid tie-bridge bar 2.0 → 1.6 | they hang over the bay now; keeps them out of its 1.5 keep-out | lid −42 |
| — | j1_hub, turntable_ring | unchanged | 0 |

Not changed: **ESP32 hold-down** (gravity + fences) — a zip tie cannot wrap a board corner without spanning the whole board; waiting on PCB hole positions to add screw bosses.

## Open
1. PCB mounting holes (if any), which edges the cables leave from, and how much of the 30 is under the board (`bp_esp_below`, one parameter).
2. **ESP32 USB access** with the lid on: none yet. Options: a rim slot at the bay, or leave a USB cable plugged and routed out with the loom.
3. Bench-check the hall gap (2.5) with the real sensor + a **5 × 2** magnet before gluing.
5. Board hold-down — needs the PCB's hole positions (or a 3 mm component-free edge band).
4. `j1_hub` broach carries **16 MPa at MG995 stall** — gauge the broach first (`_gauge_broach.py`).

## Acceptance
- [ ] lint passes; design review run
- [ ] J1 gate: servo, stator, rotor and home cam assembled, interference 0
- [ ] PCB slides in, both cable zones clear, lid closes
- [ ] printed and verified
