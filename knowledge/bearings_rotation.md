# Bearings & rotation — anything that spins rides on steel

Read when: a joint rotates in service, oscillates under load, or a printed
pivot is wearing. Catalog: `lib/bearings.py` (608ZZ proven in use;
others DATASHEET — verify before clamping against a race).

## Selection

1. **Default: 608ZZ** (8×22×7, ~$1) on an M8 bolt axle — the proven repo
   pattern (robotarm wrist). Nyloc + washers; bolt inserted last from
   outside so the assembly drops together.
2. Space-constrained: 625ZZ (5×16×5, M5 axle) or 623ZZ (3×10×4, M3 axle).
   Same-bore slim: 688ZZ (8×16×5) where the 608's OD doesn't fit.
3. Printed-on-printed rotation (`rotating` fit, 0.35 mm) ONLY for slow,
   light, occasional motion — a knob, a latch. Continuous or loaded
   rotation on plastic = wear + slop; say so and spec a bearing.
4. Axial (thrust) load: deep-groove handles light thrust only. Real thrust
   or big moment on one bearing → TWO bearings spaced ≥ 1 shaft Ø apart
   (moment pair), or a roller ring (see robotarm turntable in docs/).

## Pocket design (bearing in printed part)

- Pocket Ø = OD + `JOINT_FIT_MM["bearing_pocket"]` (0.05 HANDBOOK — gauge
  it per material before a big part; too tight distorts the race and the
  bearing grinds, too loose spins the race and wears the pocket).
- Seat depth = bearing width + 0.2; retain with a lip (Ø = OD − 2 mm) on
  the blind side; open side: printed cap, circlip groove, or bolt washer.
- **Clamp ONLY the inner race** on the rotating side: shoulders and spacers
  stay inside `inner_race_od`, or the pad rubs the outer race and brakes
  the bearing. Washer stacks set the clamp path: head → washer → inner
  race → spacer → inner race → washer → nyloc.
- Pocket axis vertical when printing if possible (round hole); an XY-axis
  pocket needs teardrop relief or post-sizing with a reamer/drill.

## Verification before export

- Print the pocket check: bore Ø at three angles (script measure), lip Ø,
  seat depth. Interference-check the spacer stack against the outer race
  diameter. Gauge-print the pocket ring alone (10 min) when the
  bearing_pocket clearance hasn't been calibrated in this material.
