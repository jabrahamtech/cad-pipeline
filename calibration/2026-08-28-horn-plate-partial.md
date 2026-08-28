# Horn plate v1 — bench session, PARTIAL (2026-08-28, Jonathan)

Plate: `gauge_horn_v1.3mf`, PETG, printed. Servos/horns: the bench clones.
Status: CROSS station done, MG995 stations BLOCKED on what horns the big
servo actually ships with. Everything below is MEASURED unless said otherwise.

## CROSS station — FAILED, and the failure is the point

The SG90 4-arm cross horn does not enter the rotor cross pocket at all.
Reported as "shape doesn't match"; the caliper says it is WIDTH, and the
shape reads as a mismatch because nothing seats.

| what | model said | MEASURED | delta |
|---|---|---|---|
| long axis, tip to tip | 33.5 | **34.4** | +0.9 |
| short axis, tip to tip | 16.0 | **17 (16–18)** | ~+1 |
| long-arm width at the hub (first hole) | 5.5 | **5.7** | +0.2 |
| long-arm width at the tip (last hole) | 3.0 | **4.0** | **+1.0** |

**The arm is 4.0 wide at its NARROWEST.** The turret slot is `tt_horn_w`
3.4 (= the old 3.0 + 0.4 clearance). A 4.0 arm cannot enter a 3.4 slot,
anywhere along its length — so the horn sits on the pad and the station
reads as "doesn't fit at all". The photo-derived estimate (~4.7–5.0 at
the tip) agreed in direction; the community model's 3.0 was the wrong
number, and it was the one everything downstream trusted.

Photo cross-check, scaled off the pad's own Ø6.0 screw bore: long span
~39.6 (caliper 34.4 — the photo is off ~15 %, oblique angle and the horn
sitting proud of the scale plane, so the CALIPER governs); short span and
the width taper agreed within ~0.5.

### What this changes (not yet applied)

- `tt_horn_w` 3.4 → **4.4** (4.0 + 0.4), and the pocket span/root relief
  re-checked against a 34.4 long axis and 5.7 roots.
- micro `horn_arm_w` 5.65 → **5.85** (5.7 + 0.15): at 5.65 the slot is
  0.05 UNDER the real arm — interference, not a press fit. Affects
  wrist_hub, wrist_rotator, gripper_pinion.
- `MICRO_HORN_ARM_W_OUTER` 3.0 → 4.0, `MICRO_HORN_ARM_W_AT_6` 5.5 → 5.7,
  `MICRO_HORN_CROSS_LONG` 33.5 → 34.4, `_CROSS_SHORT` 16.0 → 17.0 in
  lib/servo.py, all promoted MODEL → MEASURED.

## MG995 stations — NOT MEASURED

Blocked: unclear what horns came with the MG995. Question outstanding —
does that servo's bag contain horns at all, and is the "round horn"
Jonathan mentions the Ø22 disc type or something else. shoulder_hub's
whole interface (hub Ø14.2 bore, 6.65 slots, the 2.0 J2 standoff) rests
on this and MUST NOT PRINT until it is answered.

## Not yet run
HUB sweeps, BLADE comb, PIN pairs, and every flange-plate station.
