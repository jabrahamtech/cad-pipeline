# cobot arm — how it goes together (2026-09-29)

The myCobot 280 / Lite 6-style redesign: 12-gon capsule links side by side, servos inside, offset joints.
Every number lives in `lib/cobot.py`; `check()` asserts every fit on import. The assembly gate is
`models/robotarm/_check_cobot_fit.py`; its last run is `_cobot_fit_gate.log`, and it **PASSES**.

Kept from the old arm: `base_platter`, `base_lid`, the whole J1 turntable, and J1's MG995 360.

---

## 1. Drives: gears + joint encoders

A hobby servo's pot is on its own output, so any gear after it divides the joint's travel.
J2–J4 therefore run the **360° versions of the same servos**, and the ESP32 closes the loop on an
**AS5600 on each joint**.

| Joint | Motor | Gearing | Joint torque at duty (0.5 × stall) | Need @ 50 g, v3 head | Margin |
|---|---|---|---|---|---|
| J2 | MG995 360 | 22T/36T m1.25, face 20 → **1.64:1** | 6.92 kg·cm | 6.23 | **1.11** (1.26 with a 40 g head) |
| J3 | SG90 360 | 18/36 + 18/36 m1 (compound idler) → **4:1** | 2.59 | 1.96 | **1.32** |
| J4 | SG90 360 | 18T/36T m1 → **2:1** | 1.44 | 1.04 | **1.38** |
| J5 | SG90 | direct (position servo) | — | ~0.06 | ample |

- **Masses:** from the Fusion builds (volume × 1.27 × 0.65) plus catalog servo masses. The distances to each joint are ASSUMED, from the lib positions.
- **Mesh efficiency:** 0.9 per mesh, ASSUMED.
- **J2 is the tight one.** The next steps are, in order:
  1. The v4 head at ≤ 40 g.
  2. An extension-spring counterbalance on J2. It needs no redesign, since it anchors at the tower and the upper arm.
- **Why spur gears:** research (2026-09-29) showed planetary, cycloidal, strain-wave and worm drives only pay off above ~10:1 with a multi-turn motor. At 1.5–4:1 inside Ø45–56 links, spur stages are right. Herringbone is out because every pinion meshes by sliding in axially.
- **Tooth strength:** every pair passes `lib/gears` Lewis at the servo's STALL. The J3 stage-A 18T carries 2× the servo torque, so it is face 12.

## 2. The joint pattern (J2, J3, J4)

- **Spigot and gear:** H's solid spigot passes the bore in S's 3 mm joint wall. The OUTPUT GEAR is bolted to the spigot end from inside S (heads sunk), and its flange traps the wall, with AX_GAP 0.25 each side.
- **Encoder:** a stalk on the gear axis carries the Ø6 × 2.5 diametric magnet up into the servo plate's Ø12 hole, 1.0 mm under the AS5600 chip.
- **Servo plate = bench unit:** the servo (with its pinion broached on and screwed) and the AS5600 board are fixed to the plate on the bench. The unit then drops in along −x, and the pinion meshes axially.

## 3. Fits and tolerances

Backlash is 0.2 mm at each centre distance. Everything that moves a pinion relative to its gear is accounted for:

| Source | ± mm (radial) | Where it is handled |
|---|---|---|
| Printed feature-to-feature position (X2D, ASSUMED) | 0.10 | in the J3 stacks |
| Spigot in its bore (ROT 0.35 diametral) | 0.175 | in the J3 stacks |
| Gear on its spigot | 0.10 | **register boss Ø12 × 1.5, LOC recess**; the bolts only clamp |
| Servo in its plate window | 0.10 | LOC window |
| Idler on its Ø3 pin (ROT) | 0.175 | in the J3 stacks |
| Spline + broached pinion runout (ASSUMED) | 0.05 | in J3B |

- **J2 and J4 are SET on assembly.** The plate's post holes are slots ±0.6 along the mesh line: put 0.1 paper between the teeth, push the plate into mesh, tighten, pull the paper.
  - The Ø12 stalk hole leaves the Ø10 stalk room for that travel.
  - The forearm plate's two J4-end screw holes are slotted along the same line, because they go into standoffs on the J4 plate.
- **J3 is fixed by the parts.** The idler pin stands in the upper arm and locates the J3 plate. Each stage's centre distance carries its RSS stack:
  - stage A: +0.29 (27.49);
  - stage B: +0.25 (27.45).
- **Lead-ins (45°, 0.5):** on every tooth end that slides into mesh (pinion fronts, output-gear backs, both idler faces) and on the J3/J4 spigot ends.
- **Pinion screws:** each pinion is counterbored so a standard screw reaches exactly the spline engagement. That is **M2.5 × 6** on the SG90s (the bag screws are the wrong length) and **M3 × 8** on the MG995.
- **Offset links sweep AX_GAP over each other's faces,** so every screw head on those faces is counterbored:
  - the forearm plate is 5 mm (3.2 cbore, 1.8 under);
  - the wrist cap is 4.8.

## 4. Assembly — in this order

Every step inserts along the joint axis (x), or along J5 for the rotator. The gate replays each step backwards 40 mm and checks it against every part already fitted. All 16 steps are clear.

**Bench (do first).**
1. Broach each pinion onto its servo: press, then drive the servo screw. Do the same for the rotator on the J5 SG90.
2. Assemble each servo plate:
   - MG995 → J2 plate: 4 × M3 × 8 through the tabs.
   - SG90 → J3 plate and SG90 → J4 plate: 2 × M2 × 6 each.
3. Glue a magnet into each output gear's stalk.
4. Solder wires to each AS5600 (no header). Drop it into its plate's pocket chip-down and clamp with 2 × M2 × 5 + washers.

**Wrist.**
1. The J5 SG90 goes into the body bay, lead out through the back port.
2. The cap: 3 × M3 × 12.
3. The rotator onto the spline through the front bore: M2.5 × 6 from the front.
4. The head adapter: 4 × M3 × 8, counterbored. Then the v3 head: its own 4 × M3 × 8 into the adapter's inserts.

**Forearm.**
1. The forearm over the wrist's J4 spigot.
2. The J4 gear onto its register: 4 × M3 × 18.
3. The J4 plate unit: mesh set with paper, 4 × M3 × 8.
4. The loom (see §5).
5. The forearm plate: 2 × M3 × 12 into the standoffs.

**Upper arm.**
1. The upper arm over the tower's J2 spigot and the forearm plate's J3 spigot together.
2. The J2 gear: 4 × M3 × 30.
3. The J3 gear: 3 × M3 × 30, through the forearm plate into the forearm's bosses. One clamp stack.
4. Press the Ø3 × 35 dowel into the idler boss. Put the idler on it (run a 3.0 drill through its bore first).
5. The J3 plate unit over the pin: 3 × M3 × 10.
6. The J2 plate unit: mesh set with paper, 3 × M3 × 10.
7. The loom, then the cover: 6 × M3 × 8 button head. The cover is also the MG995's pull-off stop, 0.4 above its base.

**Order matters:** plate units only after their output gears (the plates cover the gear bolts), and the J3 plate only after the idler.

## 5. Cables

No loom passes through a joint, because every joint axis carries a magnet. Each joint is crossed by a **service loop** between two grommeted Ø8 ports, one per link, at the end caps nearest the joint.

| Joint | Port on the moving side | Port on the fixed side | Inside |
|---|---|---|---|
| J1 | — | rotor cable window (unchanged) | down the tower channel |
| J2 | upper arm J2 end cap (x 118.6) | tower back port | over the J2 plate, then the lane over the J3 SG90 (v +12, x 112–125) |
| J3 | forearm J3 end cap (x 42.9) | upper arm J3 end cap | forearm: over the J4 plate at v −17.5, then to v 0 past the J4 board |
| J4 | wrist back port (x −2.5) | forearm J4 end cap | wrist: the bay, out of the back port |
| J5 | head | wrist back port | loop outside; roll range is set by the loop (±90° recommended) |

- **Loom budget:** 5 servo leads plus 3 encoder signals. Run the AS5600s in **analog-out** mode: one signal each to an ESP32 ADC pin, with 3V3 and GND shared (Ø ≈ 6).
- **I2C option:** instead, use a TCA9548A mux in the base, 4 wires per encoder. The AS5600 address is fixed at 0x36.

## 6. Fold limits (gate pose sweep)

- **J3:** ±150° clean (the links are offset).
- **J2:** 0–180° clean.
- **J4:** clean to ±90°. At ±120° the Ø36 head adapter meets the forearm; a head within the wrist's ±11 layer removes that limit.

## 7. Print (X2D, PETG, supports OFF)

`exports/robotarm/cobot/cobot_plate_1.3mf` and `cobot_plate_2.3mf`: 19 parts, about 488 g. Orientations are baked in (`_export_cobot.py`).

- **Plate 1:** tower (race face down), upper arm (joint wall down), upper arm cover.
- **Plate 2:**
  - forearm and its plate;
  - the three servo plates;
  - wrist and cap;
  - three output gears, three pinions and the idler;
  - rotator and head adapter.
- Print the pinions and rotator in the **same filament as the spline gauge**.

## 8. Buy

| Qty | Part |
|---|---|
| 1 | MG995 **360°** (J2); J1 already has one |
| 2 | SG90 **360°** (J3, J4) |
| 3 | AS5600 module, 23 × 23 (magnet included) — CALIPER before printing plates |
| 1 | Ø3 × 35 steel dowel (ISO 2338 / 8734) |
| 7 | M3 × 30 (J2 ×4, J3 ×3) |
| 4 | M3 × 18 (J4 gear) |
| 9 | M3 × 12 (forearm plate ×2, wrist cap ×3, spare 4) |
| 6 | M3 × 10 (J2 + J3 plates) |
| 20 | M3 × 8 (MG995 tabs ×4, J4 plate ×4, cover ×6 button, adapter ×4, MG995 pinion ×1, spare) |
| 4 | M3 heat-set inserts (adapter) |
| 4 | M2 × 6 (SG90 tabs); 6 × M2 × 5 + M2 washers (board clamps) |
| 3 | M2.5 × 6 pan head (J3 pinion, J4 pinion, rotator) |
| 6 | Ø8 rubber grommets (ID ~5) |
| opt | TCA9548A I2C mux, if running the encoders on I2C |

## 9. Open

- **Head v4** (shrink to the wrist; ≤ 40 g): lifts J2 to 1.26 and removes the ±120° J4 limit.
- **J2 counterbalance spring:** recommended regardless.
- **CALIPER** the 360° servos and the AS5600 board against `lib/servo.py` and `BOARD` before printing plates.
- **Firmware:** closed loop per joint on the AS5600, with a deadband about the size of the backlash so it doesn't hunt.
