# gauge_flange v2 — measurement sheet

Print `exports/robotarm/gauge_flange_v2.3mf` (PETG, 0.2 layers, 3 walls,
supports OFF, same profile as every gauge). One plate, ~30 g. Every station
is a drop test with one of the bench servos or their horns — no caliper
needed except where marked. Record results in `calibration/` as a dated
note, then promote the matching lib/servo.py values and re-run the gates.

v1 (printed or not) is superseded: v2 adds the horn stations after the
2026-08-27 horn audit and re-brackets the hub sweep around Ø8.0.

## Stations, and what each answer changes

**MG995 bed** (top). Set the MG995 into the window (rails locate its 20.2
width, the end stop its far end) and look through the four tab holes.
Daylight in all four slots = `shoulder_bracket` bolts up as drawn. A miss
names its direction: which slot, which way. → sb tab slots, MG995 tab
numbers in lib/servo.py.

**SG90 seat**. Drop an SG90 in, case first. It should pass the window and
sit FLUSH, tabs fully in the 2.6 recess. Proud tabs → tab_thk over 2.4;
case refuses the window → case_w 12.2 optimistic; tabs refuse the recess →
span 32.3 tight. Sight lines under the tab holes mark the 27.8 pitch. →
wrist_roll, pruner_shell, turntable_stator, gripper_shell pockets.

**MG90S lobe**. The plate stack here IS the forearm lobe (5.5). Drop an
MG90S in and look through the tab holes: the Ø1.8 pilots sit at the
DERIVED 27.5 pitch, side lines mark 27.5 and the old 29.0. Pilots visible
→ the derivation holds, drive the screws (destructive, that is the test)
and the forearm can print. → fa_tab_pitch, and the MG90S block in
lib/servo.py.

**TAB comb** (2.0 / 2.4 / 2.5 / 2.6 / 2.8). Slide a micro tab in edgewise;
tightest slot that accepts = tab thickness. The 2.0 slot doubles as the
horn BLADE thickness check (audit says 2.0, old CAD said 1.5). → wrist_roll
tab slots, every horn arm-slot depth.

**HUB bores** (7.2 / 8.0 / 8.8). Push an SG90/MG90S horn in hub-first.
Smallest bore that takes it = hub Ø. The J1 gate's last ASSUMED number,
and the press pockets in wrist_hub / wrist_rotator / gripper_pinion (all
cut at 8.15 = 8.0 + press). CALIPER the winner if it is between bores.

**ARM comb** (4.5 / 5.0 / 5.5 / 6.0). Slide a micro horn ARM in edgewise
about 6 mm from the hub — where the wrist parts trim it. Tightest
accepting slot = arm width at the trim radius (audit: 5.5). → horn_arm_w
5.65 in wrist_hub / wrist_rotator / gripper_pinion.

**FLEX coupon** (bottom right). The gripcut finger's own hairpin leaf,
same t 1.2 / w 6.0 / fold / return, printed in the same in-plane-bending
orientation. Push the tip sideways to the 2.5 mark, then 4.5: the solver
says that range carries 0.67–0.99 N (68–101 g on a kitchen scale pressed
against the tip). Within ~±30 % → the finger's grip force stands; far off
→ lib/gripcut_finger.py gets a measured correction factor before the
fingers print.

## Still bench-blocked after this plate

MG995 horn (hub Ø, arm width, blade) — `shoulder_hub` is BLOCKED on the
horn-mounting decision (see `_assembly.md`, horn audit); this plate's
combs and bores are micro-horn sized. The 0.01 mm caliper purchase stands
for everything the drop tests bracket but cannot pin.
