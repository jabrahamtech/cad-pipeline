# robotarm — project overview

5-DOF desktop robotic arm with a swappable end effector (two-finger gripper
or a scissor cradle) and the electronics in a rounded base. Exported as ONE multi-plate Bambu 3MF via `lib/plate_export.py`
(`models/robotarm/plates.py`), plates grouped by size and print orientation.

Shared geometry lives in `models/robotarm/_frame.py` — every part derives its
heights and radii from there. Servo dimensions live in `lib/servo.py`,
bearings in `lib/bearings.py`.

## Joint layout (revised 2026-08-22 after a static torque check)
| Joint | Servo | Stall | Worst-case demand | Notes |
|---|---|---|---|---|
| Base yaw | MG90S | 2.2 kg·cm | inertia only | vertical axis on a 3×608ZZ turntable |
| Shoulder | MG995 | 11 kg·cm | 2.31 kg·cm (21 %) | case centred on the turntable |
| Elbow | MG90S | 2.2 kg·cm | 1.17 kg·cm (53 %) | |
| Wrist pitch | SG90 | 1.8 kg·cm | ~0.4 kg·cm | |
| Effector | 2 × SG90 | 1.8 kg·cm | grip force only | one per jaw |
| spare | 1 × SG90 | | | not mounted |

**Why the MG995 is at the shoulder, not the base.** The shoulder is the only
joint where gravity acts on the whole arm at the longest moment arm: at
150 mm reach with a 50 g payload it needs 2.31 kg·cm, and an MG90S stalls at
2.2 — it could not hold the arm horizontal at all, and even empty it would sit
at 60 % of stall. The base turns about a vertical axis, so gravity does no
work there, and the 608ZZ rollers take the overturning moment off the shaft;
the base servo only fights inertia and friction, a few percent of an MG90S.

An MG90S shoulder would have forced the arm down to ~85 mm reach and a 25 g
payload. Full working numbers are reproducible from the masses in
`docs/robotarm/README.md`.

Payload: 30 g rated (33 g hard limit, set by the elbow), ~150 mm
shoulder-to-wrist reach. The two-servo hand costs payload versus the
single-servo pincer it replaced — 33 g against 46 g — because it puts
another 9 g servo at the very tip.

## Bearings — 6 × 608ZZ available, 5 used
Three 608ZZ run on horizontal M8 axles in `turret_cap`, bearing on the flat
underside of `shoulder_bracket`'s disc at r = 36 mm. They take the arm's
weight and overturning moment; the base servo's horn is left transmitting
torque only. That is what makes a micro servo viable at the base at all —
without the rollers the arm's whole tipping moment would land on its gears.

Deliberately NOT used in the arm joints: a 608 is Ø22 × 7 and ~10 g of steel,
which is a lot of mass to hang 150 mm from an MG90S shoulder. Those joints use
a printed Ø8 stub axle in double shear instead. 3 bearings stay spare.

## Electronics (in the base)
ESP32 on a 400-pt breadboard in the bay, toggle switch + DC power cable on the
rim, 2 × Ø5 LED holes in the rim. Bay dimensions from MEASURED values
(85.5 × 55.5 board footprint, 16.1 mm stack height with the ESP32 fitted).

The base is Ø176, not smaller: the breadboard has to sit tangentially outside
the servo column, which puts its far corners at r = 79.5.

## Joint enclosure — the drum-and-skirt contract
Defined in `models/robotarm/_frame.py`, generators in `_shell.py`.

The member holding a servo's CASE carries a **drum** (a cylinder concentric
with the joint axis, sized to swallow the case). The member driven by the
HORN carries a **skirt** (an annulus lapping over that drum with a running
clearance). Both are concentric, so the joint reads closed at every angle and
neither sweeps anything new.

This is not a styling choice bolted on afterwards — it is the only geometry
that CAN enclose these joints. A flat cover inside a joint's sweep radius
jams at every angle; measured, a cover screwed to a link could only ever close
about 25 % of it.

| Joint | Drum on | Skirt on | Drum r |
|---|---|---|---|
| Shoulder | shoulder_bracket | upper_arm near end | 35.5 |
| Elbow | upper_arm far end | forearm near end | 21.0 |
| Wrist | forearm far end | wrist_bracket | 21.0 |

Each drum's far cap carries the idler bore, so enclosing the joints also puts
the elbow into double shear — it was hanging off the servo shaft before.

## The wrist ROLLS, on a bolt-on bracket
`wrist_mount` is a saddle that slips over the forearm's tip and takes two M3
straight through it and both of the link's side plates. It holds the wrist
servo with its shaft pointing forward down the arm; `wrist_rotator` turns on
that shaft and the effector bolts to it.

It used to pitch, which needed a yoke straddling a drum, an idler stub, a
608ZZ and a twin-lug clevis. The roll joint is also far cheaper to carry:
gravity does almost no work about a roll axis, so the wrist servo runs at 3 %
of stall instead of 11 %, and 40 g came off the very tip of the arm.

Bracket rather than built-in because the wrist is the piece most likely to
change, and it leaves the forearm's tip a plain channel — two walls and a
floor, no drum, no flange, no servo pocket. That took the link from 28.3 cm³
to 19.4 cm³.

## End effectors — two, sharing one interface
Both bolt to `wrist_rotator` on the same four M3, Ø22 bolt circle at
45/135/225/315°, so they swap without reprinting the arm. Every dimension
comes from the `EFFECTOR_*` block in `_frame.py`.

The scissor path is **incomplete**: the cradle bolts on correctly, but the
effector SG90 lost its mount when the wrist was rebuilt, and re-siting it is
blocked on measuring the real scissors. See
`specs/robotarm/scissor_cradle.md`.

- **claw** (default): TWO SERVOS, one per finger, each finger bolted
  straight to its own horn. No gears, no rack, no linkage — two printed
  designs for the whole hand. Opens 0–43.3 mm over 35° of travel, 0.25 kgf
  per finger at the duty limit.
  The two fingers are ONE printed part: finger R is finger L **turned over**,
  which is why its horn pocket has to be a through-cut and why the horn screw
  needs a washer.
  Cost, stated plainly: the fingers rotate, so their faces only meet flush at
  one opening and roll off anything wider or narrower. Shorten the reach for
  more force and less opening.
- **scissors**: `scissor_cradle` + `effector_lever` strap a pair of scissors in
  and squeeze one handle. All scissor dimensions are ASSUMED.

## Parts and plates
| Part | File | Plate |
|---|---|---|
| base_platter | models/robotarm/base_platter.py | 1 (Ø176, alone) |
| base_lid | models/robotarm/base_lid.py | 2 (Ø171.8, flat) |
| turret_cap | models/robotarm/turret_cap.py | 3 |
| shoulder_bracket | models/robotarm/shoulder_bracket.py | 3 |
| upper_arm | models/robotarm/upper_arm.py | 4 |
| forearm | models/robotarm/forearm.py | 4 |
| wrist_bracket | models/robotarm/wrist_bracket.py | 5 |
| hand_base | models/robotarm/hand_base.py | 5 |
| hand_link_driven ×2 | models/robotarm/hand_link_driven.py | 5 |
| hand_link_idler ×2 | models/robotarm/hand_link_idler.py | 5 |
| hand_jaw ×2 | models/robotarm/hand_jaw.py | 5 |
| scissor_cradle | models/robotarm/scissor_cradle.py | 6 (optional) |
| effector_lever | models/robotarm/effector_lever.py | 6 (optional) |

Each plate is its own file, `robotarm_p<n>_<slug>_v1.3mf`. Plate 6 is only
needed if you want the scissor effector.

Material: PETG throughout (functional, warm-tolerant, tougher than PLA at the
joints). Every part prints with no support material.

## Bought parts
| Item | Qty | Note |
|---|---|---|
| 608ZZ bearing | 3 | user already has 6 |
| M8 × 30 bolt + M8 nyloc nut | 3 | roller axles |
| M3 heat-set insert | 7 | 3 cap bolts + 4 lid screws |
| M3 × 8 / M3 × 10 screw | 7 | cap and lid |
| M3 × 12 + insert | 2 | effector to wrist_bracket |
| M3 × 10 self-tapper + washer | 2 | gripper finger retention |
| Servo screws | — | use the ones supplied with each servo |

## Servo envelope dimensions (DATASHEET — see lib/servo.py)
| Servo | Case L×W×H | Tab span | Hole pattern |
|---|---|---|---|
| SG90 / MG90S | 22.8 × 12.2 × 22.5 | 32.5 | 2 × Ø2.2 @ 27.8 |
| MG995 | 40.7 × 19.7 × 42.9 | 54.5 | 4 × Ø4.5 @ 49.5 × 10 |
