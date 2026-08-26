# gripper_pinion — spec

Project: `models/robotarm/gripper_pinion.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
The 12-tooth module-1.5 involute pinion that drives both gripper racks. It
presses onto the gripper SG90's own single-arm horn and turns between the
two rack channels; one turn of the servo opens or closes both jaws by equal
amounts. Fulfils the "pinion mesh" and "pinion on horn" rows of
`specs/robotarm/_assembly.md`.

It is **not** clamped by the horn screw — the two `gripper_shell` halves
trap it axially with a running gap. That is deliberate: the SG90's horn
screw is too short to reach through 3.9 mm of extra pinion.

## Interfaces — the dimensions that matter

| Interface | Value | Source | Joint / fit |
|---|---|---|---|
| module | 1.5 mm | design_rules `GEAR_PREFERRED_MODULE_MM` | — |
| tooth count | 12 | gears_drives.md floor at 20° PA | — |
| pressure angle | 20° | gears_drives.md | — |
| face width | 8.0 mm | ≥ 5 × module — design_rules | — |
| pitch / tip / root Ø | 18.00 / 21.00 / 14.25 | derived | — |
| centre distance to rack pitch line | 9.20 mm | 9.00 + `GEAR_BACKLASH_MM` 0.20 | — |
| SG90 horn hub Ø | 7.0 mm | DATASHEET (lib/servo.py) | press (0.15) → Ø7.15 pocket |
| SG90 horn blade thickness | 1.5 mm | DATASHEET | 1.6 mm slot depth |
| SG90 horn arm width | 3.8 mm | DATASHEET | press (0.15) → 3.95 slot |
| horn arm TRIMMED radius | 6.0 mm | design decision | blind slot, 1.125 mm to the root circle |
| horn retaining screw | Ø2.5 shank | DATASHEET | Ø5.5 driver bore through |

**The horn must be cut down.** The stock SG90 arm reaches 15.95 mm from the
spline; the pinion's root circle is at 7.125 mm. An untrimmed arm breaks out
through the teeth. Snip it to 6 mm with side cutters before assembly — 10
seconds, and the pocket is a diametral slot so it can go in either way up
and a double-arm horn fits too.

## Loads & environment
Static and intermittent, indoor. Peak tangential tooth load at the SG90's
duty limit (0.80 kg·cm at 9.0 mm pitch radius) is **8.7 N**. Tooth bending
at the root, σ = 6·F·h / (b·t²) with h = 3.375, b = 8.0, t = 3.72:
**1.6 MPa** against ~35 MPa for PETG in-plane — a **22×** margin, and still
7× if a sharp root corner concentrates stress 3×.

**No root fillets, deliberately.** The margin above is the reason; the rack
teeth are the same. Revisit only if a gauge print shows root cracking.

Torque transfer through the horn arm: 0.157 N·m at a ~4.5 mm mean radius is
35 N bearing on a 1.5 × 2.5 mm slot face = 9.3 MPa, ~5× margin in
compression.

## Cables & service
n/a — unpowered. Serviceable: the pinion lifts off the horn once the shells
are apart, and it is the wear item, so it reprints in ~6 minutes on its own.

## Print plan
PETG · **flat, bore vertical, back (horn) face on the bed** · single nozzle ·
40 % infill, 4 walls. Teeth are loaded within layers in that orientation
(gears_drives.md). No support. 0.4 mm elephant-foot chamfer on the bed face,
which doubles as the horn's lead-in; 0.5 mm lead-in on the driver bore.

## Acceptance
- [x] script lint conventions followed; built and verified numerically
- [x] tooth thickness at the pitch circle measures 2.356 mm = π·m/2 exactly
- [x] `_check_fit.py`: zero interference with both racks at 0/20/40 mm opening
- [ ] **gauge print first** — the rack/pinion mesh gauge in `_assembly.md`.
      Backlash 0.20 is HANDBOOK and has never been gauged in PETG here.
- [ ] fits the real trimmed horn (press fit)
- [ ] printed and verified — date, measured result, deviations

## ASSUMED / unverified
Every SG90 horn dimension is DATASHEET, read off the vendor drawing rather
than the horn in hand. If the pinion will not press on, the horn pocket is
the first suspect — `gp_hub_d`, `gp_arm_w`, `gp_arm_depth`.
