# robotarm — what to print, what to buy (current as of 2026-09-28, restyle)

J1 = MG995 360° · J2 = MG995 (sized from the drawing in `calibration/2026-09-28-mg995-drawing.png`: 40.5 tall to the top of the lip, 49 mm hole pitch, 55 mm tab span) · J3–J6 = SG90 · ESP32 carrier PCB in the base ·
**new gripper head** (fin ray fingers, no cutter). Colours: **black** base + turret,
**green** links + hand, **white** joints, **black TPU** fingers. Specs: `specs/robotarm/grip.md`,
`base_platter.md`, `turret_shroud.md`, `_harness.md`, `_build.md`. Renders: `docs/robotarm/arm_*.png`,
`head_close.png`, `base_close.png`.

## Print — in this order

Everything PETG, 0.2 layers, 3 walls, 15–20 % infill, **supports off**, unless noted.

**Spline bores are gauged (2026-09-28, gauge_broach_v2 in PLA): SG90 drawn −0.05, MG995 drawn −0.25.** Print the hubs (J1 hub, shoulder hub, J3 pinion, wrist hubs, rotator, gripper pinion) in the same material as the gauge, or re-check one gauge station in PETG first.
Files are in `exports/robotarm/`.

**1. Gauge — DONE 2026-09-28** (`gauge_broach_v2.3mf`: S-5 and G-25 pressed on tight). Reprint it only if you change filament.

**2. Base + turret (black PETG, ~290 g)**
- `base_platter_v6.3mf` ×1 — 12-sided, **LED eyes in the front**, floor down, no brim needed (3 mm foot facet) · ~154 g
- `base_lid_v10.3mf` ×1 — top face down, brim · ~64 g (vents removed: every hole now passes a post, the servo or cables)
- `turntable_stator_v10.3mf` ×1 — base down, supports OFF · ~31 g
- `turret_shroud_v1.3mf` ×1 — **new**: upright, lid end down, no support · ~26 g
- `turntable_ring_v6.3mf` ×1 — don't sand the bore · ~13 g
- `j1_hub_v5.3mf` ×1 — top face down, 5 walls, 40 % infill
- `plates/plate_bits_white_v1.3mf` — 3 roller caps + 4 PCB keepers, **print in black** (filename predates the colour split; tiny: slow first layer)

**3. Shoulder (white)**
- `shoulder_bracket_v5.3mf` ×1 — −X face down · ~53 g

**4. Arm**
- `plates/plate_armstack_green_v12.3mf` — upper arm (open duct, recessed side panels), forearm halves, 2 rails (brim), J3 servo cap, 2 duct grommets
- `plates/plate_armstack_white_v12.3mf` — J3 gear, J3 pinion, J3 axle, shoulder hub
- `plates/plate_wrist_white_v10.3mf` — wrist roll pair (mirrored), rotator, 2 hubs — all on one plate now, no shims

**5. Gripper head (new)**
- `plates/plate_grip_green_v2.3mf` — 2 shell halves
- `plates/plate_grip_white_v2.3mf` — 2 jaws + pinion
- `grip_finger_v1.3mf` ×2 — **TPU 95A**, flat, 20–25 mm/s

Superseded — don't print: `base_platter_v4` (fluted round), `base_platter_v5` (no eyes), and everything cut for the old flat-topped MG995: `shoulder_bracket_v4`, `turntable_stator_v9`, `base_lid_v8`/`_v9`, `j1_hub_v3`/`_v4`, `plate_armstack_*_v9`–`_v11`, `plate_wrist_*_v8`/`_v9`, `plate_grip_*_v1` (hub bores cut before the gauge). Retired: the pruner (`pruner_*`, `gripcut_finger`) and the old `gripper_shell` / `gripper_rack_jaw`.

**Assembly note:** the shroud goes on after the rotor and BEFORE the ring — slide it down over the three turret posts. With it fitted, J2 can pitch down to **23°** below horizontal (was 25°).

## Buy

**Motion + sensing**
- MG995 360° ×1, MG995 ×1, SG90 ×4 (in hand)
- 608ZZ ×4 — 3 turntable, 1 elbow
- A3144 hall sensor ×1 (pack), 5 × 2 mm N52 disc magnets (pack)
- **5 mm LEDs ×2 for the eyes** — any 5 mm LED fits; addressable RGB (WS2812D-F5 / PL9823-F5) runs both off one ESP32 pin. Push in from inside until the flange seats; a dab of hot glue holds them

**Filament**
- PETG **black** (~290 g: base, lid, stator, ring, shroud, J1 hub, bits), PETG white, PETG green
- **TPU 95A, black** — ~10 g for the two fingers (skip if you have it)

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
