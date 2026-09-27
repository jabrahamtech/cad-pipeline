# robotarm — wiring harness and cable management

Status: SPEC — 2026-09-27. Research-backed (sources at the end); the J1
cable cup is modelled and gated, everything above J1 is specified here and
not yet modelled.

## Topology — a bus, not six home-runs
Stock leads home-run to the base would put **5 flat servo leads (15 wires,
~7 mm bundle)** through J1's cable cup, whose chamber is 5.9 mm tall. So:

| run | conductors | notes |
|---|---|---|
| base → shoulder (through J1) | **2 × 20 AWG silicone** (V+, GND) + **5 × 26 AWG silicone** (S2–S6) | 7 wires, bundle ≈ Ø5 |
| shoulder → elbow (upper arm duct) | 2 × 22 AWG + 4 × 26 AWG (S3–S6) | J2 MG995 taps off at the shoulder |
| elbow → wrist (forearm) | 2 × 22 AWG + 2 × 26 AWG (S5, S6) | J3 + J4 SG90 tap off in the forearm |
| wrist → head (through J5 roll) | the J6 SG90's own 3 wires | only one lead crosses J5 |
| J1 MG995 | its stock lead, straight to the carrier | never crosses a moving joint |

- **Why 20 AWG through J1:** J2 MG995 + 4 × SG90 at stall ≈ 3.8 A (5+ A if the
  MG995 draws like an MG996R). 20 AWG is 33 mΩ/m: ~0.1 V over the ~0.8 m
  round trip. 26 AWG signals carry nothing.
- **Silicone, not PVC,** anywhere that flexes: PVC is rated for fixed or
  occasional flexing only (LAPP).
- **Taps:** V+/GND spliced (solder + heat-shrink) inside the link body at each
  junction; each servo's stock plug mates a 3-pin Dupont/JR male on the harness.
  **Every disconnect sits inside a link, never in a flexing loop** (igus).

## Service loops — r × θ + 20 mm
The loom crosses each pitch joint at its drum end, ≈ r 13 from the axis.

| joint | travel | loop to leave | where it is fixed |
|---|---|---|---|
| J1 yaw | ±180° | **110 mm coiled in the j1_hub cable cup** (±180° × r̄ 15.5 = 97 + margin) | lid tie bridges (az 330 ± 28°) below; rotor gate above |
| J2 shoulder | −25…+160° (185°) | **62 mm** (13 × 3.23 + 20) | tie at the bracket column; tie at the upper-arm duct mouth |
| J3 elbow | 90° | **40 mm** | upper-arm duct mouth; forearm inner wall |
| J4 wrist pitch | ±90° | **60 mm** | forearm; wrist_roll lead channel |
| J5 roll | ±90° | **40 mm**, one loose partial wrap round the rotator hub | wrist_roll; pruner_shell notch |

- **Centre each loop at mid-travel** (J2 at about +67°) so it flexes both ways.
- **Bend radius:** ≥ 10 × OD. That is 14 mm for 1.4 mm silicone wire (LAPP, rule of thumb).
- **Tie at both ends of every loop, and nowhere in it.** Over-binding makes the
  cable corkscrew and fail (igus).
- **Anchors:** the upper-arm duct mouths have a printed `duct_grommet` each
  (rounded lip + tie bar) — tie the loom to the bar. Stick-on 10 × 10 mm
  zip-tie mounts only where no printed anchor exists: the rotor boss beside
  the connector gate, and the bracket column. Clean the PETG with IPA first.
- **The upper arm's duct is open at both drum ends since v3.** Older prints
  are a sealed tunnel with no exit (see `duct_grommet.md`).

## J1 — why a cup (modelled, `j1_hub_v2`)
Industrial torsion-rated cable allows only ±180–360° per metre (LAPP, igus).
J1's ±180° over ~20 mm of axis is ~10× that. So the loom **wraps** round the
hub instead of twisting. Unguarded, that loop could drift into the 608s,
whose tops are in contact with the rotor: a nip. The hub's cup (skirt at
r 20–21.6, bottom edge z 19.0 — 0.4 above the printed roller caps, which is
what sets it) keeps the loop in; the nip it guards is at z 24.1. The fixed end leaves under
the skirt's chamfered lip at az 330, straight down the stator and lid loom
windows onto the ESP32 bay. **No slip ring:** ±180° doesn't need one, and a
capsule ring would have to sit on the axis the MG995 shaft occupies.

## Protection
- Base→shoulder bundle: **6 mm braided PET sleeving** (Techflex Flexo 1/4");
  3 mm on the arm runs. Hot-knife the ends.
- **No heat-shrink over a flexing loop.** It stiffens the cable.
- Strain-relieve 10–20 mm from every servo exit and at the carrier PCB, so
  bending happens in the loop and not at the grommet.

## Electrical
- **Supply:** 5 V, **10 A** (6 A minimum). Worst-case stall is 2 × 1.2 + 4 × 0.65 ≈ 5 A
  (~7.6 A with MG996R-like MG995s); moving load is ~2 A. Never power servos
  from the ESP32's pins.
- **Toggle switch and DC cable** carry that current. Rate the switch ≥ 10 A DC.
- **Capacitors:** 1000 µF (≥ 10 V) across the servo rail at the carrier;
  100 µF at the elbow tap (optional; Adafruit rule is 100 µF per servo).
- **Common ground** between the ESP32 and the servo supply is mandatory.
  Intermittent ground is the usual cause of jitter.
- **Signal:** 40–50 cm of 50 Hz PWM at 3.3 V is fine. If a servo jitters, add a
  74AHCT125 buffer at the carrier.
- **Hall sensor (A3144):** 5 V supply, open-collector output to a GPIO with
  INPUT_PULLUP. The unipolar part needs the magnet's SOUTH face toward it.
  Test the magnet's polarity before gluing.

## Sources
igus unharnessed robot cable spec; igus "Less is More" robotic cable management;
igus ±360°/m torsion bus cable press release; LAPP flex-life basics;
US20130270399 (clock-spring cable); Adafruit slip rings 775/1195/1196, silicone
wire 1970, 16-ch servo driver hookup (100 µF/servo); ProtoSupplies SG90;
components101 MG995; Handsontec MG996R datasheet; JST XH; PAR6 cable build
guide; Techflex Flexo PET; DroneBot servo guide.
