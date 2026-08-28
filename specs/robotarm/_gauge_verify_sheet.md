# gauge_verify v2 - bench sheet

`exports/robotarm/gauge_verify_v2.3mf` | 96 x 130 x 8.4 mm | ~29 g at 65 %

**v2 supersedes v1. Do not print v1.** In v1 every servo window had four
notches - two long walls x two ends - which is why they read as a capital I.
The cable does not leave a long wall. It leaves the SHORT END FACE, the one
the output shaft is nearest, dead centre across the width. v2 has ONE notch
per window, in that end wall.
PETG, 0.2 layers, 3 walls, **support OFF**, engraved face UP.

This plate replaces gauge_flange v3 and gauge_horn v3. Ten of their fifteen
stations were already answered on the bench with calipers, or gate nothing.
These five are the ones that are both **untested** and **blocking a part**.

Print one. Do not print the two v3 plates.

## What each station is for

| Station | What it is | What a PASS means |
|---|---|---|
| MG995 | the corrected 20.4 window + END-wall lead notch + four tab slots | the shoulder bracket's MG995 pocket takes the servo *with its cable on* |
| SG90 | the 22.9 x 12.4 window + END-wall notch + 2.6 tab recess | wrist_roll / turntable_stator / gripper_shell all take an SG90 |
| MG90S 27.5 | the forearm lobe at 1:1 - pad + base = `fa_lobe_t` 5.50, END-wall notch | the lobe takes an MG90S, **and** the derived 27.5 tab pitch is real |
| CROSS | the turret horn pocket, tapered 6.04 at r 6.5 -> 4.84 at the trim line | the micro cross horn drops in - the constant-width version could not |
| FLEX | 1.2 x 6.0 hairpin leaf with 0, 2.5, 4.5 mm marks | the gripcut finger's leaf lands in the 68-101 g band |

## How to test, in order

1. **Three servo windows.** Take each servo with its cable still attached.
   Each window has ONE notch, on one short end. **Insert with the output
   shaft toward the notch** - MG995 and SG90 shaft to the left, MG90S shaft
   toward the bottom of the plate. The cable lies in the notch and runs out
   to the plate edge. It must go in without forcing and without the cable
   being pinched. Report for each: *drops in* / *needs a push* / *will not go*.
   If one will not go, say **which direction it jams** - the case on the long
   side, the case on the short side, or the cable.

   The notch is 3.6 mm wide on the micro servos and 4.4 on the MG995, and it
   runs 7.4-10.8 mm past the window. If the cable will not sit in it, say so -
   that means the bundle is fatter than the 3.4 / 4.2 mm in `lib/servo.py`,
   and five parts are sized off that number.
2. **MG90S pilots.** Offer an MG90S up to the lobe station and look through
   the two Ø1.8 holes at its mounting-tab holes. There are two pairs of
   engraved sight slits beside them: the inner pair is 27.5, the outer is
   29.0. Report which pair the servo's tab holes line up with. This is the
   last derived number in the project.
3. **SG90 tab recess.** With the SG90 seated, its mounting tabs should sit
   in the shallow recess and the case should not rock. Report: *flat* /
   *rocks* / *tabs sit proud*.
4. **MG995 tab slots.** The four slots should take the MG995's tabs with the
   case down on the bed. Report whether all four engage.
5. **CROSS.** Press the micro cross horn (the four-arm one) into the pocket,
   hub into the centre relief. Report: *drops in* / *tight* / *will not seat*,
   and if it is tight, whether it binds **near the hub** or **near the tips**.
6. **FLEX.** Hold the plate flat, hook a small kitchen scale or a known
   weight under the coupon's tip and pull until the tip reaches each engraved
   line. Report the grams at the 2.5 line and at the 4.5 line. Expect roughly
   68 g and 101 g. Anything outside 50-130 g means the leaf thickness or the
   PETG modulus is off and the finger needs re-sizing.

## Not on this plate, and why

| Left off | Why |
|---|---|
| micro hub sweep, MG995 hub sweep | calipered: 6.8 and 8.7 |
| blade comb, arm comb, tab comb | calipered: 2.0 / 2.2 blade, taper measured |
| pin pairs | nothing structural reads a horn hole pitch |
| WRIST replica, MG995 STACK replica | both now derive from measured values - they would confirm arithmetic, not discover anything |
| stale HUB row | superseded by the calipered hub diameters |

## What this plate does NOT settle

`forearm.py` now cuts the notch in the end wall, derived to reach the lobe
edge. The other four consumers - `wrist_roll`, `turntable_stator`,
`gripper_shell`, `pruner_shell` - still notch the wrong wall, and
`wrist_roll` has a second fault behind it: its purpose-built `lead_ch`
channel routes to the FAR end, which under the corrected datum is also the
wrong end. Those are not fixed by measuring this plate. They need
`_check_leads` repaired first - it is the gate that exists to catch exactly
this, and it is currently marked INVALID.

## Still model-grade after this plate

Hub **heights** - micro 3.0, MG995 3.8. Nothing on this plate measures them.
They set `sh_horn_hub_depth` and the turret pocket floor. Caliper them off the
horn directly when convenient; no print needed.
