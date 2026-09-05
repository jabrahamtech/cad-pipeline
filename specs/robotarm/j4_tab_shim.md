# j4_tab_shim — the 0.80 that lets an SG90 sit on an MG90S lobe

**PRINT TWO.** One under each tab ear of the J4 servo.

## Why it exists

Jonathan printed the forearm before J3 and J4 became SG90s, and is not
reprinting it. That forearm's J4 lobe gives **5.90 mm** from the plate outer
face to the tab plane, which is what an MG90S wants. An SG90 is **6.70 mm** to
the same plane.

The case bottoms 0.80 mm early — on roughly 37 mm² of ledge at the two ends of
the J4 journal bore, where the Ø20.35 bore stops and the 22.70 mm case does
not — and holds the tab plate proud of its own pad. The two tab screws then
have nothing to pull down onto and the flange clamps air.

## The 0.80 is measured

The f0509b4 forearm was rebuilt from its own git snapshot, an SG90 solid
dropped into its J4 station, and the servo swept outboard against a
pointContainment sampler:

| shim | servo inside the forearm | spline in the hub bore |
|---|---|---|
| 0.00 | 45.8 mm³ | — |
| 0.40 | 22.9 mm³ | — |
| **0.80** | **0.0 mm³** | **2.30 mm** |
| 1.20 | 0.0 mm³ | 1.90 mm |
| 1.60 | 0.0 mm³ | 1.50 mm |

0.80 is both the first offset that clears and the largest worth having: every
further 0.40 costs 0.40 of spline engagement, one for one.

## What it costs, and who pays it

- **0.20 mm of spline engagement.** `wrist_hub` takes it back by moving its
  bore stations outboard — `lib/joints.J4_HUB_BORE_SHIFT_MM`. That makes a hub
  built this way **specific to the printed forearm**.
- **0.80 mm of tab screw engagement.** The servo's own M2s cross more stack
  before they reach the forearm's pilots. Buy them 1 mm longer.

## Shape

Two pads rather than one frame, because an SG90's flange is exactly as wide as
its case — 12.20 both — so there is no material along the long sides to join
the ears with, and a one-piece shim would have to be wider than the lobe
recess.

The screw slot is **open at the outer edge**. A closed hole means threading a
0.80 mm pad down a pocket and holding it on the screw while the servo goes in;
open, each pad slides in under its ear after the servo is resting in the
window.

## Not structural

Pure compression between the tab plate and the pad. The tab screw passes
through the slot without touching it — the tabs locate the servo, never this.
The material beside the slot is reported rather than asserted against
MIN_WALL for that reason: a wall carrying nothing is a printability question,
and at 0.80 mm tall it prints as three perimeters.
