# Enclosures & electronics housings — the most common job, done right

Read when: a PCB, module, display, battery, or wiring lives inside the
part. Companions: cable_management.md (wires), fasteners_inserts.md
(closures), materials.md (thermals).

## Board mounting

- Bosses + M2/M3 into heat-set inserts (repeat service) or self-tap pilots
  (assemble-once). Boss height ≥ 3 mm standoff so through-hole solder
  joints and bottom components clear — MEASURE the tallest bottom-side
  component, don't assume flat.
- Support the board at its holes, not its edges; a board pinched at the
  rim rattles and flexes. No mounting holes on the board? Edge rails +
  one snap finger over a component-free zone, or corner posts with a
  clamping lid rib landing on the board EDGE only.
- Keep-outs: 1.5 mm clearance over every component top; 3 mm around
  antennas AND no metal/inserts in front of them; connectors get pockets
  per cable_management.md; SD/USB slots need finger or cable room, not
  just hole alignment.
- Locate the board with two diagonal bosses as pins (locational fit),
  other holes at clearance — the pin+slot rule (joints_tolerances.md).

## Openings — every port is an interface row

Each cutout gets a spec-table row: connector body size (MEASURED), plug
OVERMOLD size (the rubber boot is wider than the port!), and insertion
depth. Cutout = body + locational clearance; face thickness at the port
≤ the connector's reach (a USB-C plug engages ~6.5 mm — a 4 mm wall plus
recess can defeat it). Recessed ports get a finger/plug cone, not a
straight well.

## Ventilation & thermals

- Passive convection needs a PATH: low inlets + high outlets on opposite
  sides, ≥ 30% more outlet area than inlet. Slots beat holes (print
  self-supporting when vertical, strain less).
- Rough budget: electronics dissipating ~1 W in a sealed 1 L box rises
  ~10–15 °C over ambient — sealed + PLA + warm room is how enclosures
  sag. > 2–3 W: vents or a fan pocket (measure the fan: 30/40 mm + its
  screw pattern), and the enclosure goes PETG+.
- Hot chips near walls: 5 mm air gap minimum; never park a battery
  against the hot zone; batteries also get their own bay with restraint
  (foam rib or strap) and a fail path that isn't "into the electronics".

## Closure & sealing

- Lid classes: screwed (inserts, ≥ 4 for a seal, ≤ 100 mm screw spacing);
  snap (service ≤ weekly, arms per joints_tolerances.md); sliding rail
  (no vertical space); hinged (printed pin hinge only for light lids —
  steel pin for daily use).
- Registration lip on every lid: 1.5–2 mm tongue at locational fit — it
  aligns, stiffens, keeps dust, and hides layer seams.
- Real sealing (splash/IP-ish): tongue + groove with a TPU gasket printed
  as its own part (groove = gasket + 0 clearance wide, 80% deep for 20%
  crush); screws every ≤ 60 mm. Honest limit: hobby FDM does splash-proof
  well, submersion badly — say so.
- ESD/creepage sanity: mains voltage does NOT go in a printed enclosure
  without Jonathan explicitly owning the isolation design — flag it,
  suggest a certified enclosure for the mains side.

## Interface details worth stealing

- Buttons: printed plunger over a tact switch — plunger sliding fit,
  travel = switch travel + 0.5, keep-in flange, spring = the switch
  itself (no printed springs).
- Light pipes: 3 mm clear filament rod or bought pipe in a press-fit
  bore over the LED; or a 1 mm wall "window" printed in natural filament.
- Labels: emboss ≥ MIN_EMBOSS_MM, top-surface engrave prints cleanest;
  put orientation-critical text where it reads in the assembled pose.
- Wall thickness default 2.0–2.4 (2 = MIN_WALL + stiffness margin); add
  internal ribs rather than thicker walls for drum-resonant flat panels.

## Enclosure checklist add-ons (beyond design_review.md)

- [ ] tallest-component measurement in spec (top AND bottom side)
- [ ] every port row has plug-overmold width and engagement depth
- [ ] thermal path stated (sealed OK / vented / fan) with the wattage
- [ ] battery restrained, away from heat, with cable strain relief
- [ ] board removable without desoldering (cable_management.md)
- [ ] antenna keep-out honored (no inserts/bosses in front)
