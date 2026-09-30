# cobot arm — how it goes together (2026-09-29, rev: J2 spring + grip v4)

The myCobot 280 / Lite 6-style redesign: 12-gon capsule links side by side, servos inside, offset joints.
Every number lives in `lib/cobot.py`; `check()` asserts every fit on import. The assembly gate is
`models/robotarm/_check_cobot_fit.py`; its last run is `_cobot_fit_gate.log`, and it **PASSES**.

Kept from the old arm: `base_platter`, `base_lid`, the whole J1 turntable, and J1's MG995 360.

---

## 1. Drives: gears + joint encoders

A hobby servo's pot is on its own output, so any gear after it divides the joint's travel.
J2–J4 therefore run the **360° versions of the same servos**, and the ESP32 closes the loop on an
**AS5600 on each joint**.

| Joint | Motor | Gearing | Joint torque at duty (0.5 × stall) | Need @ 50 g (70 g head; v4 is 67) | Margin |
|---|---|---|---|---|---|
| J2 | MG995 360 | 22T/36T m1.25, face 20 → **1.64:1** + **torsion spring** (§3) | 6.92 kg·cm | 6.23 → **1.95** with the spring | **1.11 → 3.5** |
| J3 | SG90 360 | 18/36 + 18/36 m1 (compound idler) → **4:1** | 2.59 | 1.96 | **1.32** |
| J4 | SG90 360 | 18T/36T m1 → **2:1** | 1.44 | 1.04 | **1.38** |
| J5 | SG90 | direct (position servo) | — | ~0.06 | ample |

- **Masses:** from the Fusion builds (volume × 1.27 × 0.65) plus catalog servo masses. The distances to each joint are ASSUMED, from the lib positions.
- **Mesh efficiency:** 0.9 per mesh, ASSUMED.
- **J2 was the tight one (1.11).** The spring counterbalance (§3) takes its worst case from 611 to 191 N·mm.
- **Head:** grip v4 is ≈ 67 g built (body 33.2, jaws 2 × 3.2, pinion 2.7, fingers 2 × 2.7, SG90 9, steel rods 10.4). The 40 g target is NOT reachable with this mechanism: the servo and rods alone are 19.4 g. Carbon-fibre Ø3 rods save ≈ 8 g.
- **Why spur gears:** research (2026-09-29) showed planetary, cycloidal, strain-wave and worm drives only pay off above ~10:1 with a multi-turn motor. At 1.5–4:1 inside Ø45–56 links, spur stages are right. Herringbone is out because every pinion meshes by sliding in axially.
- **Tooth strength:** every pair passes `lib/gears` Lewis at the servo's STALL. The J3 stage-A 18T carries 2× the servo torque, so it is face 12.

## 2. The joint pattern (J2, J3, J4)

- **Spigot and gear:** H's solid spigot passes the bore in S's 3 mm joint wall. The OUTPUT GEAR is bolted to the spigot end from inside S (heads sunk), and its flange traps the wall, with AX_GAP 0.25 each side.
- **Encoder (J3, J4):** a stalk on the gear axis carries the Ø6 × 2.5 diametric magnet up into the servo plate's Ø12 hole, 1.0 mm under the AS5600 chip.
- **Encoder (J2):** the J2 gear's stalk is now a Ø10 SHAFT through the plate and the cover into the spring cap (§3). The magnet sits flush in its end; the board is on the cap lid.
- **Servo plate = bench unit:** the servo (with its pinion broached on and screwed) and the AS5600 board are fixed to the plate on the bench. The unit then drops in along −x, and the pinion meshes axially.

## 3. J2 counterbalance: centring torsion spring

**Spring:** Century Spring **TO-5201RCS** (music wire, RH wound, 7 coils, Ø2.16 wire, OD 22.63, body 17.27, legs 63.5 at 180°, **7.34 N·mm/°**, max 205°). Cut both legs to **22 mm** from the tangent point.

- **Neutral = arm vertical.** Gravity on J2 goes as sin θ; the spring as 7.34 · θ. Rate = 0.69 × the gravity peak per radian (`lib/cobot` asserts 0.5–0.9).
- **Result (J2 0–180°, i.e. ±90° from vertical):**

| Case | Gravity peak | Worst residual | J2 margin (679 N·mm available) |
|---|---|---|---|
| 50 g payload | 611 N·mm | +102 at 47° | 6.7 |
| empty | 469 N·mm | −191 at 90° (spring lifts) | **3.5** |

- The residuals assume the catalog rate. ±10 % on the rate (ASSUMED typical) moves the empty case to −258 → margin 2.6. Hysteresis and coil friction are not modelled.

**How it's held (all on the J2 axis, outside the cover, x 126.8 → 159.7):**
- `cobot_j2_cap` — 12-gon cup, UA-fixed: 3 × M3 × 8 through its floor into heat-set inserts in the cover's new bosses. Two **pins** (Ø5 columns, ribbed to the wall) at u ±18.
- `cobot_j2_hub_lo` / `cobot_j2_hub_hi` — discs with a D-bore on the shaft's D-flat (0.1 clear), so they are **tower-fixed**. One Ø5 pin each at u ∓6.
- All four pins sit under the legs' line (v −13.81, tangent to the legs), so each leg is only ever pushed in its winding sense.
- `cobot_j2_cap_lid` — 3 × M3 × 10 into the cap's external lugs (outside the legs' sweep). It traps both hubs axially and carries the J2 AS5600 chip-down over the shaft end.
- **Shaft:** Ø10 PETG with a D-flat from x 132.2 up; torsion at 90° ≈ 4.6 MPa.
- **Encoder wires:** a channel in the cap's outer bump, a groove under the floor, into the arm through the cover.
- **Width:** the arm is now 32.9 mm wider on the J2 side. The cap stack's mass sits on the J2 axis, so it adds no gravity torque at J2.

## 4. Fits and tolerances

**Measured on the built parts** (`_check_cobot_mesh.py`, log `_cobot_mesh_check.log`):

| Pair | Backlash at the pinion pitch circle | Through one full tooth, turned together |
|---|---|---|
| J2 36T / 22T | 0.35 mm | free, flank gap constant 0.16 |
| J3 stage A 36T / 18T idler | 0.58 mm (includes the +0.29 stack) | free, 0.27 |
| J3 stage B 36T idler / 18T | 0.55 mm (includes the +0.25 stack) | free, 0.26 |
| J4 36T / 18T | 0.35 mm | free, 0.16 |

- The constant flank gap through a whole tooth shows the involutes are conjugate: no binding anywhere in the cycle.
- J2 and J4 are set with paper on assembly, so their real backlash is whatever the paper leaves. J3's is nominal: at the tight end of its tolerance stack the extra centre distance is gone and it drops to about 0.35 (2 × 0.29 × tan 20° ≈ 0.21 less).
- Output play from backlash alone, nominal: J2 ≈ 0.9°, J3 ≈ 2.7° (two stages), J4 ≈ 1.1°. Gravity keeps J2 and J3 on one flank most of the time; set the firmware deadband to about this.
- Servos: each sits on its plate's tabs with its pinion seated on the output boss. Nearest other parts: MG995 0.40 to the cover (its pull-off stop), 1.9 to the arm wall; J3 SG90 0.94 to the idler; J4 SG90 0.40 to the forearm plate; J5 SG90 0.10 to the wrist cap (LOC).
- Leads: a 5 mm straight stub out of each servo's lead face clears everything by ≥ 4.5 mm.
- Running gaps between moving parts: gears to the link walls 0.25 (AX_GAP), idler 0.40, hubs 0.40 to the cap and lid, rotator 0.17 radial in the wrist.


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
  - The Ø12 hole leaves the Ø10 J2 shaft room for that travel (and the J4 stalk the same).
  - The forearm plate's two J4-end screw holes are slotted along the same line, because they go into standoffs on the J4 plate.
- **J3 is fixed by the parts.** The idler pin stands in the upper arm and locates the J3 plate. Each stage's centre distance carries its RSS stack:
  - stage A: +0.29 (27.49);
  - stage B: +0.25 (27.45).
- **Lead-ins (45°, 0.5):** on every tooth end that slides into mesh (pinion fronts, output-gear backs, both idler faces) and on the J3/J4 spigot ends.
- **Pinion screws:** each pinion is counterbored so a standard screw reaches exactly the spline engagement. That is **M2.5 × 6** on the SG90s (the bag screws are the wrong length) and **M3 × 8** on the MG995.
- **Offset links sweep AX_GAP over each other's faces,** so every screw head on those faces is counterbored:
  - the forearm plate is 5 mm (3.2 cbore, 1.8 under);
  - the wrist cap is 4.8.

## 5. Assembly — in this order

Every step inserts along the joint axis (x), or along J5 for the rotator and head. The gate replays each step backwards 40 mm (the J2 and J3 gears all the way out of the link: 100 and 72 mm) and checks it against every part already fitted. All 22 steps are clear.

**Bench (do first).**
1. Broach each pinion onto its servo: press, then drive the servo screw. Do the same for the rotator on the J5 SG90.
2. Assemble each servo plate:
   - MG995 → J2 plate: 4 × M3 × 8 through the tabs.
   - SG90 → J3 plate and SG90 → J4 plate: 2 × M2 × 6 each.
3. Glue a magnet into each output gear's stalk (J2: flush in the shaft end).
4. Solder wires to each AS5600 (no header). J3/J4: drop it into its plate's pocket chip-down and clamp with 2 × M2 × 5 + washers. J2: the same, into the cap lid.
5. Press 3 × M3 heat-set inserts into the upper arm cover's cap bosses, from the outer face.

**Wrist.**
1. The J5 SG90 goes into the body bay. Its lead leaves the **shaft-end face near the bottom**: lay it into the keyway in that end wall as the servo goes in, along the channel under the bay floor, and out through the back port.
2. The cap: 3 × M3 × 12.
3. The rotator onto the spline through the front bore: M2.5 × 6 from the front.
4. The grip v4 head, EMPTY, onto the rotator's neck: 4 × M3 × 8 on r 7, driven down the access bores with a long 2.5 key. Then its SG90 (2 × M2 × 8), pinion, jaws, and 4 × Ø3 × 47 rods (`specs/robotarm/grip.md`).

**Forearm.**
1. The forearm over the wrist's J4 spigot.
2. The J4 gear onto its register: 4 × M3 × 18.
3. The J4 plate unit: mesh set with paper, 4 × M3 × 8.
4. The loom (see §5).
5. The forearm plate: 2 × M3 × 12 into the standoffs.

**Upper arm.**
1. The upper arm over the tower's J2 spigot and the forearm plate's J3 spigot together.
2. The J2 gear: 4 × M3 × 30. With the arm vertical, its shaft's D-flat faces FORWARD (tower +y).
3. The J3 gear: 3 × M3 × 30, through the forearm plate into the forearm's bosses. One clamp stack.
4. Press the Ø3 × 35 dowel into the idler boss. Put the idler on it (run a 3.0 drill through its bore first).
5. The J3 plate unit over the pin: 3 × M3 × 10.
6. The J2 plate unit: mesh set with paper, 3 × M3 × 10.
7. The loom, then the cover over the shaft: 6 × M3 × 8 button head. The cover is also the MG995's pull-off stop, 0.4 above its base.

**Spring (arm held vertical throughout).**
1. The cap over the shaft, floor down: 3 × M3 × 8 into the cover's inserts.
2. `hub_lo` onto the D-flat, pin up.
3. The spring over the shaft: the bottom leg across the lower hub pin and the cap pin on the same side, the top leg across the other pair.
4. `hub_hi` onto the D-flat, pin down beside the top leg.
5. The lid (J2 board already clamped in): 3 × M3 × 10 into the lugs, encoder wires down the bump channel.

**Order matters:** plate units only after their output gears (the plates cover the gear bolts); the J3 plate only after the idler; the spring stack only with the arm vertical (neutral), or the legs start preloaded.

## 6. Cables

No loom passes through a joint, because every joint axis carries a magnet. Each joint is crossed by a **service loop** between two grommeted Ø8 ports, one per link, at the end caps nearest the joint.

| Joint | Port on the moving side | Port on the fixed side | Inside |
|---|---|---|---|
| J1 | — | rotor cable window (unchanged) | down the tower channel |
| J2 | upper arm J2 end cap (x 118.6) | tower back port | over the J2 plate, then the lane over the J3 SG90 (v +12, x 112–125); the J2 encoder enters through the cover from the cap |
| J3 | forearm J3 end cap (x 42.9) | upper arm J3 end cap | forearm: over the J4 plate at v −17.5, then to v 0 past the J4 board |
| J4 | wrist back port (x −2.5) | forearm J4 end cap | wrist: the bay, out of the back port |
| J5 | head | wrist back port | loop outside; roll range is set by the loop (±90° recommended) |

- **Loom budget:** 5 servo leads plus 3 encoder signals. Run the AS5600s in **analog-out** mode: one signal each to an ESP32 ADC pin, with 3V3 and GND shared (Ø ≈ 6).
- **I2C option:** instead, use a TCA9548A mux in the base, 4 wires per encoder. The AS5600 address is fixed at 0x36.

## 7. Fold limits (gate pose sweep)

- **J3:** ±150° clean (the links are offset).
- **J2:** 0–180° clean.
- **J4:** clean to ±90°. At ±120° the grip v4 body still meets the forearm (324 mm³), so ±90° stays the J4 limit.

## 8. Print (X2D, supports OFF)

`exports/robotarm/cobot/cobot_plate_{1,2,3}_petg.3mf` and `cobot_plate_4_tpu.3mf`: 28 parts, about 563 g PETG + 4 g TPU. Orientations are baked in (`_export_cobot.py`).

- **Plate 1:** tower, upper arm, spring cap (floor down), cap lid.
- **Plate 2:** cover, grip body, forearm and its plate, the three servo plates, J2 gear (flange down, 96 tall), wrist cap.
- **Plate 3:** wrist, J3/J4 gears, idler, both hubs (disc down), pinions, rotator, jaws, gripper pinion.
- **Plate 4 (TPU 95A):** the two fingers.
- Print the pinions and rotator in the **same filament as the spline gauge**.

## 9. Buy

| Qty | Part |
|---|---|
| 1 | MG995 **360°** (J2); J1 already has one |
| 2 | SG90 **360°** (J3, J4) |
| 3 | AS5600 module, 23 × 23 (magnet included) — CALIPER before printing plates |
| 1 | Ø3 × 35 steel dowel (ISO 2338 / 8734) |
| 7 | M3 × 30 (J2 ×4, J3 ×3) |
| 3 | M3 × 10 (cap lid) |
| 4 | M3 × 18 (J4 gear) |
| 9 | M3 × 12 (forearm plate ×2, wrist cap ×3, spare 4) |
| 6 | M3 × 10 (J2 + J3 plates) |
| 23 | M3 × 8 (MG995 tabs ×4, J4 plate ×4, cover ×6 button, spring cap ×3, head ×4, MG995 pinion ×1, spare) |
| 1 | Century Spring **TO-5201RCS** torsion spring (legs cut to 22 mm) |
| 3 | M3 heat-set inserts (cover → spring cap) |
| 4 | Ø3 × 47 rods: ground steel, or carbon fibre (−8 g) |
| 4 | M2 × 6 (SG90 tabs), 2 × M2 × 8 (head SG90); 6 × M2 × 5 + M2 washers (board clamps) |
| 3 | M2.5 × 6 pan head (J3 pinion, J4 pinion, rotator) |
| 6 | Ø8 rubber grommets (ID ~5) |
| opt | TCA9548A I2C mux, if running the encoders on I2C |

## 10. Open

- **J4 ±120°:** needs a head narrower at its back than the v4 body.
- **Spring rate:** the catalog rate is not measured; hang a known mass on the finished arm and check the residual before tuning firmware gains.
- **CALIPER** the 360° servos and the AS5600 board against `lib/servo.py` and `BOARD` before printing plates.
- **Firmware:** closed loop per joint on the AS5600, with a deadband about the size of the backlash so it doesn't hunt.
