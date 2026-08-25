# upper_arm_cover — spec

Project: `models/robotarm/upper_arm_cover.py`
Status: MODELED (2026-08-22)

## Function
Gable shell closing the upper arm's channel between the shoulder and elbow
drums, hiding the servo wiring that runs along the link.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Sits on | the link's plate tops at z = plate height | _link contract |
| Flank widths | match the link's outer faces so they sit flush | _link contract |
| Span | from LINK_WEB_CLEAR_R outward — see below | derived |
| Flank angle | 45°, the steepest fully self-supporting slope | design_rules |
| Skin | 2.0 mm | design |
| Fixing | 2 × M3 self-tappers through the link's −Y plate into internal bosses | design |

## Why it starts where it does
A cover bridges the channel, so it obeys the same sweep rule as the link's
web: inside `LINK_WEB_CLEAR_R` of the shoulder axis it would jam the joint at
every angle. That is why the JOINTS are closed by concentric drums and only
the straight run between them gets a gable. Measured, a cover attached to a
link can never close more than about a quarter of it — the rest is joint.

## Loads & environment
None. Cosmetic and a wire guard; indoor.

## Print plan
PETG · gable UP, open side down on the bed · no support (45° flanks, narrow
crown) · 3 walls, 12 % infill.

## Acceptance
- [ ] invariant tests pass
- [ ] clips over the channel without fouling the servo or the wiring loom
- [ ] printed and verified
