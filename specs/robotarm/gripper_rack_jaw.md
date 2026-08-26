# gripper_rack_jaw — spec

Project: `models/robotarm/gripper_rack_jaw.py`
Status: MODELED <!-- DRAFT → MODELED → PRINTED → ACCEPTED -->

## Function
One printed design that is both gear racks and both gripping jaws. A
toothed bar runs in a channel in one `gripper_shell` half; an arm reaches
forward past the pinion and down across the gripper's centre plane to a
blade whose face is normal to the opening direction. Fulfils the "rack in
channel" and "pinion mesh" rows of `specs/robotarm/_assembly.md`.

**Print two, fit the second TURNED OVER** — rotated 180° about the Y axis,
which maps (x, y, z) → (−x, y, −z). That lands it on the opposite rack
channel with its teeth facing the pinion and its blade facing back at the
first. Choosing a pinion axis that runs *along* the arm instead of across it
is what buys this symmetry, and with it half the part count.

## Interfaces — the dimensions that matter

| Interface | Value | Source | Joint / fit |
|---|---|---|---|
| rack module / PA | 1.5 mm / 20° | shared `gr_` block — see gripper_pinion.md | — |
| circular pitch | 4.712 mm | derived (π·m) | — |
| rack teeth | 8 | sized so the mesh survives the whole stroke | — |
| toothed run | x −29.70 … +8.00 mm | derived, asserted in the script | — |
| addendum / dedendum | 1.5 / 1.875 mm | standard full-depth | — |
| tooth half-thickness, tip / root | 0.632 / 1.861 mm | derived | root space 0.991 mm |
| face width | 8.0 mm | shared `gr_face` | — |
| rack back above the root | 3.5 mm | design decision | — |
| pitch line to blade tip | 17.20 mm | derived: `gr_offset` + 8.0 | — |
| rack in shell channel | — | design_rules | **sliding (0.25)** |
| clearance off the OTHER rack's front face | 0.40 mm | design_rules | **free (0.40)** |
| arm / blade thickness | 6.0 mm | sized by bending, below | — |
| V-groove | 3.0 deep × ±3.0, 90° | design decision | round stock self-centres |

Jaw opening **0 – 40 mm**, from 20 mm of travel per rack, which is 127.3° at
the pinion — comfortably inside an SG90's sweep, leaving room for end stops.

**The mesh window is asserted, not assumed.** The script fails the build if
the toothed run does not still cover the pinion at both ends of the stroke:
it must start at or before −20 mm and reach at least 0.

## Loads & environment
Static and intermittent, indoor. Grip force **8.7 N** per jaw at the SG90's
duty limit. Worst load path is the blade as a cantilever off the rack:
40 mm arm, resisted by the arm's 6 mm × 14 mm section about Z,
I = 252 mm⁴, c = 3 mm → σ = **4.1 MPa** against ~35 MPa in-plane PETG, an
**8.5× margin**. Thickness in X is the term that matters (it cubes), and it
is free here because each jaw's material lives entirely on its own side of
its gripping face — the two jaws can never meet anywhere but at those faces.

Printed-on-printed sliding in the channel: `sliding` 0.25 is CALIBRATED, and
gripper duty is low-cycle, which is what makes plastic-on-plastic acceptable
here (motion_mechanisms.md, friction & wear).

## Cables & service
n/a — unpowered. Lifts straight out once the shells are apart.

## Print plan
PETG · **rack BACK face on the bed, part built in −z** · single nozzle ·
40 % infill, 4 walls · **no support anywhere**.

That orientation is chosen, not incidental: every cross-section shrinks or
holds going up, so nothing overhangs. The tooth flanks sit 20° off the build
direction, the arm's footprint is a subset of the rack's, and the blade is
on the bed from the first layer. It also puts the tooth load and the blade's
bending stress in-layer. Any other orientation leaves the rack or the blade
starting in mid-air.

## Acceptance
- [x] built and verified numerically; mesh window asserted in the script
- [x] `_check_fit.py`: jaws meet at exactly 0.000 mm at full close, hold
      0.400 mm off the other rack elsewhere, zero interference at 0/20/40 mm
- [ ] **gauge print first** — rack/pinion mesh gauge (`_assembly.md`)
- [ ] channel fit proven against a real `gripper_shell`
- [ ] printed and verified — date, measured result, deviations

## ASSUMED / unverified
- backlash 0.20 mm at the centre distance is HANDBOOK, never gauged in PETG
  on this printer — the gauge print settles it
- the `sliding` 0.25 channel fit is CALIBRATED but was proven in XY, and this
  channel is a Z-axis feature on the shell (joints_tolerances.md: a fit
  calibrated in XY is not calibrated in Z)
