# Design review — the gate before any export

Run this checklist before exporting ANY part, and state the result in the
delivery summary (pass / fail / n-a per line, one compact block). For
assemblies, run it per piece plus the assembly items. It exists so the
"CAD god" questions get asked every time, not just on good days.

## Spec integrity
- [ ] Interface table complete; every row tagged MEASURED/DATASHEET/STEP/ASSUMED
- [ ] Every ASSUMED value listed in the summary (and gauged if fit-critical)
- [ ] Every interface names a joint type; clearance traces to JOINT_FIT_MM
- [ ] Units all mm; conversions stated and confirmed

## Structure & printing
- [ ] Fits the envelope for its declared print mode (single vs dual nozzle)
- [ ] Orientation stated; primary loads run WITHIN layers, not across
- [ ] Walls ≥ 1.6; features ≥ 0.8; pins ≥ 3.0 or replaced with steel
- [ ] Overhangs ≤ 50° or support declared ("requires support material");
      support can physically be removed (no trapped cavities)
- [ ] Bridges ≤ 40 mm; elephant-foot chamfer 0.4 on bottom edges
- [ ] Material matches duty (PLA static / PETG functional / ASA-PA loaded);
      chamber/plate requirements stated for ABS/ASA/PA

## Mechanisms (n/a when static)
- [ ] Rotation rides on a bearing (or justified `rotating` fit); only the
      inner race is clamped; pocket clearance gauged in this material
- [ ] Gears: bought where precision/torque demands; printed ones meet
      module/backlash/face-width rules and print flat
- [ ] Moving joints checked at motion EXTREMES, not just neutral pose

## Fasteners
- [ ] Every screw has: correct hole size for its role (clearance/pilot/
      insert), boss wall ≥ 2.4, and a clear driver path in assembled state
- [ ] No screw loaded in pull-out across layers; trapped nuts can't spin
- [ ] No printed thread below M8

## Cables & service (n/a when unpowered)
- [ ] Entry/exit/route defined; channels ≥ 1.5× bundle; bends ≥ 4× Ø
- [ ] Strain relief at every entry; connectors reachable when assembled
- [ ] Service loop ≥ 10 mm at each board; boards removable without desolder

## Assembly (n/a for single pieces)
- [ ] _assembly.md exists: piece tree, joint contracts, numbered order
- [ ] Assembly order walked — every piece's insertion path and every
      fastener reachable at its step
- [ ] `_check_fit.py` run: zero unexpected interference; every contracted
      clearance measured present
- [ ] Shared dimensions are shared user parameters, not copied numbers

## Close-out
- [ ] Diagnostics printed (bbox/volume/bodies/isValid) and sane vs spec
- [ ] `pytest tests/ -q` passes; script committed with the spec
- [ ] Export versioned `_v{n}`; never overwrites a printed version
- [ ] Gauge offered/printed for any uncalibrated critical fit
- [ ] Summary states: orientation, material, infill, support yes/no,
      ASSUMED list, and any rule this part stress-tested
