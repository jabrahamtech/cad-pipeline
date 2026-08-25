# Joints & tolerances — picking the fit, not guessing it

Read when: any two parts touch — printed-to-printed, printed-to-COTS, or
piece-to-piece in a split assembly.

## The rule

Every interface in a spec names a **joint type**; the clearance comes from
`lib/design_rules.py` `JOINT_FIT_MM`, never invented per part. The Fusion
user parameter carrying it says so in its comment
(`'0.25 mm', 'sliding fit - design_rules'`).

| Joint type | When | Clearance (diametral) |
|---|---|---|
| press | assembled once by force, never moves (inserts, pins, bearing on shaft) | 0.15 CALIBRATED |
| locational | registers precisely, hand-assembled, removable (lids, caps, keyed covers) | 0.20 HANDBOOK |
| sliding | translates in service (drawers, rails, plungers) | 0.25 CALIBRATED |
| rotating | printed-on-printed pivot, slow + light only | 0.35 HANDBOOK |
| free | must never bind, alignment doesn't matter (swing covers, loose links) | 0.40 HANDBOOK |
| bearing_pocket | printed pocket gripping a bearing outer race | 0.05 HANDBOOK — gauge it |

HANDBOOK values get a gauge print before any critical or large part, then a
`calibration/` entry promotes them to CALIBRATED.

## Direction and orientation — where tolerance actually goes

- Grow the HOLE, shrink nothing: apply clearance to the printed negative
  space; keep the positive part (or the COTS part) nominal.
- Z-axis (vertical) holes print undersize: add `HOLE_DIA_COMP_MM` (0.2) for
  Ø < 10 mm where fit matters. XY-facing holes sag into ovals: use a
  teardrop or design the bore vertical.
- A fit that was calibrated in XY is NOT calibrated in Z. Say which
  orientation a clearance was proven in when logging calibration.
- Long flat mates warp at the ends: add 0.1 mm extra clearance per 100 mm
  of mating length, or relieve the middle so only pads touch.

## Constraint discipline — don't overconstrain

- Locate a part with at most: one pin (position) + one slot (rotation).
  Four tight corner pins WILL fight print tolerance and bind — make one
  hole tight, one a slot, the rest clearance.
- One joint carries the load, the others locate. If two features both try
  to control the same degree of freedom, one of them is a tolerance fight.

## Lead-ins — every mating edge

- Chamfer every insertion edge: 0.5–1.0 mm × 45° on the male part, plus the
  0.4 mm elephant-foot chamfer on every bottom edge (CALIBRATED).
- Blind pockets get a visible depth stop; through-fits get a lead taper.

## Snap fits (use sparingly — layer adhesion is the enemy)

- Cantilever snaps must flex WITHIN layers: print the arm flat, never
  standing. Arm length ≥ 8× thickness; interference 0.4–0.6 mm; 45° lead
  ramp, 80–90° retention face. PETG/ABS flex better than PLA.
- If a snap would flex across layers, redesign: screw, magnet, or a
  full-perimeter lip instead.

## Gauge-first (the standing rule)

Any interface that is (a) on an ASSUMED dimension, (b) using a HANDBOOK
clearance, or (c) expensive to reprint → extract it into a 10–20 minute
gauge part first. Stepped gauges (three candidate values in one print)
answer a question in one go — see `legacy/models/vergemax/thread_gauge.py`
and `calibration/` for worked examples.
