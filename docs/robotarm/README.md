# robotarm — what to print, what to buy (current as of 2026-09-29, gripper v3)

J1 = MG995 360° · J2 = MG995 (sized from the drawing in `calibration/2026-09-28-mg995-drawing.png`: 40.5 tall to the top of the lip, 49 mm hole pitch, 55 mm tab span) · J3–J6 = SG90 · ESP32 carrier PCB in the base ·
**gripper head v3** (rod-guided rack & pinion, one-piece 12-gon body, fin ray fingers). Colours: **black** base + turret,
**green** links + hand, **white** joints, **black TPU** fingers. Specs: `specs/robotarm/grip.md`,
`base_platter.md`, `turret_shroud.md`, `_harness.md`, `_build.md`. Renders: `docs/robotarm/arm_*.png`,
`head_close.png`, `base_close.png`.

## Print — in this order

Everything PETG, 0.2 layers, 3 walls, 15–20 % infill, **supports off**, unless noted.

**Printer: Bambu Lab X2D.** Every plate is packed to the X2D's **dual-nozzle** area (235.5 × 256, 260 tall), so any plate can print with one nozzle or both without re-arranging. In Bambu Studio: pick the X2D + 0.4 nozzle, Generic/Bambu PETG HF, textured PEI plate. Chamber heating **off** for PETG. Keep **auto-arrange rotation locked** — the orientations are baked in.
- **One colour per plate** (files are split `_green` / `_white`). With the X2D you can also load green on one nozzle and white on the other and print a green and a white plate together with no purge tower waste — but never let the slicer re-orient anything.
- **TPU fingers:** print from the external spool on the main (direct-drive) nozzle, not through the AMS; 20–25 mm/s, no retraction tuning needed beyond the Bambu TPU 95A profile.
- **Small holes print under** on this machine (gauge_broach_v2): the gripper's Ø3.5 rod bores in the jaws should slide on a Ø3 rod; if one drags, run a 3.5 mm drill through by hand.

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
- `shoulder_bracket_v6.3mf` ×1 — −X face down, 12-gon pivot bosses · ~47 g (76 mm tall — add a brim if it wobbles)

**4. Arm**
- `plates/plate_armstack_green_v13.3mf` — upper arm and forearm halves with **12-gon faceted drums and bosses** (2026-09-29), 2 rails (brim), J3 servo cap, 2 duct grommets
- `plates/plate_armstack_white_v13.3mf` — J3 gear, J3 pinion, J3 axle, shoulder hub (unchanged parts, re-packed for the X2D)
- `plates/plate_wrist_white_v11.3mf` — wrist roll pair (mirrored), 12-gon rotator, 2 hubs — all on one plate, no shims

**5. Gripper head (v3 — rod-guided, one-piece 12-gon body)**
- `plates/plate_grip_green_v3.3mf` — the body (back face down, 47 mm tall)
- `plates/plate_grip_white_v3.3mf` — 2 jaws + pinion
- `grip_finger_v1.3mf` ×2 — **TPU 95A**, flat, 20–25 mm/s

Superseded — don't print: `base_platter_v4` (fluted round), `base_platter_v5` (no eyes), and everything cut for the old flat-topped MG995: `shoulder_bracket_v4`/`_v5`, `turntable_stator_v9`, `base_lid_v8`/`_v9`, `j1_hub_v3`/`_v4`, `plate_armstack_*_v9`–`_v12`, `plate_wrist_*_v8`–`_v10`, `plate_grip_*_v1` (hub bores cut before the gauge), `plate_grip_*_v2` (clamshell head, replaced by v3). Retired: the pruner (`pruner_*`, `gripcut_finger`) and the old `gripper_shell` / `gripper_rack_jaw`.

**Assembly note:** the shroud goes on after the rotor and BEFORE the ring — slide it down over the three turret posts. With it fitted, J2 can pitch down to **23°** below horizontal (was 25°).

## Buy

**Motion + sensing**
- MG995 360° ×1, MG995 ×1, SG90 ×4 (in hand)
- 608ZZ ×4 — 3 turntable, 1 elbow
- A3144 hall sensor ×1 (pack), 5 × 2 mm N52 disc magnets (pack)
- **Ø3 mm ground steel rod, 4 × 59 mm** — the gripper's jaw guides (cut from a Ø3 × 250+ silver-steel / linear-shaft rod; deburr the ends)
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
- M3 × 16 ×6 — 2 J3 cap, 4 fingers
- M3 × 10 ×3 — J1 hub to rotor
- M3 × 8 ×15 — 3 roller caps, 4 lid, 4 head to rotator, 4 J2 MG995 tabs
- M3 × 6 ×4 — J1 MG995 tabs
- M3 nuts ×4 — fingers
- M2 × 8 self-tapper ×2 — SG90 tabs into the head (the SG90's own bag screws)
- M2 × 20 + nut ×3 — wrist roll clamshell
- Long 2.5 mm hex key (≥ 60 mm reach) — the head's rotator screws go in through the front
