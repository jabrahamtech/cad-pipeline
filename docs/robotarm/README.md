# robotarm — what to print, what to buy (current as of 2026-09-28)

J1 = MG995 360° · J2 = MG995 · J3–J6 = SG90 · ESP32 carrier PCB in the base ·
**new gripper head** (fin ray fingers, no cutter). Specs: `specs/robotarm/grip.md`,
`base_platter.md`, `_harness.md`, `_build.md`. Renders: `docs/robotarm/arm_*.png`,
`head_close.png`, `base_close.png`.

## Print — in this order

Everything PETG, 0.2 layers, 3 walls, 15–20 % infill, **supports off**, unless noted.
Files are in `exports/robotarm/`.

**1. Gauge first**
- `gauge_broach_v1.3mf` — its G row settles the MG995 spline press the J1 hub is cut to.

**2. Base + turret (white)**
- `base_platter_v4.3mf` ×1 — floor down, no brim needed (3 mm foot facet) · ~130 g
- `base_lid_v8.3mf` ×1 — top face down, brim
- `turntable_stator_v9.3mf` ×1 — base down, supports OFF
- `turntable_ring_v6.3mf` ×1 — don't sand the bore
- `j1_hub_v3.3mf` ×1 — top face down, 5 walls, 40 % infill

**3. Shoulder + small base bits (white)**
- `shoulder_bracket_v4.3mf` ×1 — −X face down
- `plates/plate_bits_white_v1.3mf` — 3 roller caps + 4 PCB keepers (tiny: slow first layer)

**4. Arm**
- `plates/plate_armstack_green_v9.3mf` — upper arm (open duct), forearm halves, 2 rails (brim), J3 servo cap, 2 duct grommets
- `plates/plate_armstack_white_v9.3mf` — J3 gear, J3 pinion, J3 axle, shoulder hub
- `plates/plate_wrist_green_v8.3mf` + `plates/plate_wrist_white_v9.3mf` — wrist roll pair (mirrored), rotator, hubs

**5. Gripper head (new)**
- `plates/plate_grip_green_v1.3mf` — 2 shell halves
- `plates/plate_grip_white_v1.3mf` — 2 jaws + pinion
- `grip_finger_v1.3mf` ×2 — **TPU 95A**, flat, 20–25 mm/s

Retired — don't print: the pruner (`pruner_*`, `gripcut_finger`), the old `gripper_*` shells/jaws, `j4_tab_shim` (only for a pre-SG90 printed forearm).

## Buy

**Motion + sensing**
- MG995 360° ×1, MG995 ×1, SG90 ×4 (in hand)
- 608ZZ ×4 — 3 turntable, 1 elbow
- A3144 hall sensor ×1 (pack), 5 × 2 mm N52 disc magnets (pack)

**Filament**
- PETG white, PETG green
- **TPU 95A** — ~10 g for the two fingers (skip if you have it)

**Wiring** (`_harness.md`)
- Silicone wire: 20 AWG red/black 2 m each; 22 AWG red/black 1 m each; 26 AWG 5 colours 2 m each
- Dupont crimp kit + crimper; heat-shrink assortment
- Braided PET sleeving 6 mm (1 m) + 3 mm (2 m); 2.5 mm zip ties; 10 × 10 mm stick-on tie mounts

**Power**
- 5 V 10 A supply, bare leads
- Toggle switch ≥ 10 A DC, 12–13 mm thread, panel ≤ 3 mm
- Caps: 1000 µF ≥ 10 V ×1, 100 µF ≥ 10 V ×2

**Fasteners** (all socket cap unless noted)
- M3 heat-set inserts, Ø4.0 hole: 11 (7 base, 4 rotator) + spares
- M3 × 40 ×4 — 3 turret, 1 elbow
- M3 × 30 ×2 — gripper clamshell
- M3 × 16 ×6 — 2 J3 cap, 4 fingers
- M3 × 10 ×3 — J1 hub to rotor
- M3 × 8 ×15 — 3 roller caps, 4 lid, 4 head to rotator, 4 J2 MG995 tabs
- M3 × 6 ×4 — J1 MG995 tabs
- M3 nuts ×6 — 4 fingers, 2 clamshell
- M2 × 20 + nut ×3 — wrist roll clamshell
- Long 2.5 mm hex key (≥ 60 mm reach) — the head's rotator screws go in through the front
