# Gears & drives — buy the precision, print the brackets

Read when: motion must be transmitted, reduced, or redirected.
Numbers: `lib/design_rules.py` (GEAR_* constants, all HANDBOOK).

## Buy first — the honest defaults

- Reduction under load → servo with metal gears, or a bought planetary/worm
  gearmotor. A printed gearbox is a project in itself, not a component.
- Motion over distance → **GT2 belt + bought pulleys** (quiet, tolerant of
  center-distance error, no backlash tuning). Prefer belts over printed
  gear trains whenever the layout allows.
- Worm drives, bevel pairs under torque, anything needing hardened faces →
  bought. Printed versions wear in hours.

## When a printed gear is legitimate

Low speed, low torque, intermittent duty: indexing knobs, sensor drives,
toy-grade mechanisms, feed rollers. Then:

- Module ≥ 1.0 absolute floor at 0.4 mm nozzle; **≥ 1.5 for anything
  carrying torque** (teeth are little cantilevers — bigger beats more).
- 20° pressure angle involute; face width ≥ 5 × module.
- **Backlash 0.2 mm added at the centre distance** (not by thinning teeth):
  C = (m·(z1+z2))/2 + 0.2. Make centre distance a user parameter so a
  gauge pair can tune it.
- **Herringbone/double-helical** for smooth mesh + free axial location;
  plain spur when the pair must slide apart for assembly.
- Print gears FLAT (teeth loaded within layers, never across); bore
  vertical; hub with a heat-set grub-screw insert on a D-flat, or a
  printed D-bore (press fit) for light duty.
- ≥ 12 teeth on the pinion (undercut below that at 20° PA).

## Authoring in Fusion

Generate the involute by script (query `apiDocumentation` for sketch
splines / the SpurGear sample add-in's approach) with module, tooth count,
PA, backlash as user parameters. Verify: root/tip diameters printed as
diagnostics, then a **gauge pair** — two small gears on pin axles at the
design centre distance, 20-minute print — before any geared part ships.

## Other drive elements

- Setscrew flats on shafts: cut the flat, insert the grub via heat-set.
- Friction drives (TPU tire on printed hub) beat tiny gear meshes for
  low-precision rotation.
- Ratchets/pawls: pawl flexes within layers (same rule as snaps);
  tooth face angles 45°/90°.
