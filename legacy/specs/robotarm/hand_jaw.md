# hand_jaw — spec

Project: `models/robotarm/fusion/hand_jaw.py` (Fusion MCP authored)
Status: DRAFT (2026-08-24)

Supersedes `hand_finger`. **Print one**, not two.

## Function
The single moving jaw. Bolts straight to the grip SG90's cross horn on
`hand_body`'s upright and swings a flat pad onto the body's fixed anvil.
No gears, no linkage, no idler — one servo, one moving part.

## Interfaces — the dimensions that matter
| Interface | Value | Source |
|---|---|---|
| Horn mount | SG90 cross-horn pocket, 4-arm, 32.4 × 7.4 × 1.8, BLIND in the −Y face | lib/servo.horn_pocket |
| Horn screw access | Ø6.0 bore through the root, from +Y | lib/servo |
| Root radius | 18.0 — set by the 32 mm horn span, not by taste | `_hand` ROOT_R |
| Reach | R = 30.0, pivot to the pad face | design |
| Thickness | 4.5, at y 15.1..19.6 | `_hand` FINGER_T |
| Pad | 14 long × 4.5, shallow V 120° included; bisector normal −X at θ = 55° | ASSUMED |
| Grip grooves | 3 × 1.2 mm Vs across the pad | `_hand` GRIP_GROOVE |
| Sweep | θ = 0° (closed, pad on the anvil at x = −17) → 110° (open) | design |
| Opening | 30.0 × (1 − cos θ): 0 → 40.26 mm | derived |
| Grip force | 1.8 kg·cm ÷ 3.0 cm = 0.60 kgf stall, 0.30 at 50 % duty | derived |

## Why the pocket is blind, not a through-cut
`hand_finger` had to be cut right through because finger R was finger L
turned over. There is only ONE jaw here, so the pocket can be a blind recess
in the −Y face — which means no washer under the horn screw, and a stiffer
root.

## What a rotating jaw costs, said plainly
The pad is on the end of a lever, so its face is square to the anvil at ONE
opening only — everywhere else it is rotated by (θ − 55°), up to 55° at
either extreme. This matters much less than it did on the two-servo claw,
because only ONE side moves: the object is always pinched between a flat
plane and whichever part of the pad reaches it first, rather than between
two arcs rolling past each other.

Two things keep it honest. The pad is set square at θ = 55°, mid-travel
(≈ 12.8 mm opening), so the error is split either side instead of piled at
one end. And the face is a shallow 120° V rather than flat, so a round
object seats on two lines and cannot squirt sideways out of the jaw when
the pad is at an angle.

A parallel four-bar removes the error entirely, for five more printed parts
and eight pivots.

## Loads & environment
0.60 kgf at the pad at stall. The blade is 4.5 thick and 30 long, loaded in
its own plane — bending is about the strong axis and the load lies within
print layers. Indoor, static.

## Print plan
PETG · flat on its side face (the 4.5 mm thickness is the Z height) · the
horn pocket's roof is a 7.4 mm bridge · no support · 40 % infill, 4 walls.

## ASSUMED — first suspects if it does not fit
- pad length 14, the 120° V, and the θ = 55° square setting
- R = 30.0 and the 110° sweep, both inherited from `hand_body.md`

## Acceptance
- [ ] invariant tests pass
- [ ] seats on the horn at all four 90° orientations
- [ ] pad V is square to the anvil at θ ≈ 55°
- [ ] jaw reaches the anvil at θ = 0 with no gap at the pad's leading edge
- [ ] sweeps clear of the upright, the disc and the servo case
- [ ] printed and verified — date, measured result, deviations
