# base_platter — MEASURED interface

Status: **PRINTED AND IN HAND.** Not ours to change.

Everything below was read off `legacy/exports/robotarm/base_platter_v1.step`
by face analysis in Fusion, not copied from `legacy/specs/robotarm/base_platter.md`.
**The spec and the part disagree** — trust this file.

| | spec says | the STEP says |
|---|---|---|
| Overall Ø | 176 | **185.6** over the protruding features, Ø176 at the wall |
| Rim height | 30 | **42.00** |
| Lid shelf | z 27 | **z 39.00** |
| Turret bosses | r 45, "3 × M3 heat-set" | **confirmed: r 45.0, az 120/180/240** |

## What the top face presents

| Feature | Value |
|---|---|
| **Rim top / datum** | **z = 42.00** — everything above is ours |
| Lid recess | Ø172.0 wall, shelf at z 39.00, so a 3.0 lid finishes flush at 42.00 |
| Lid screws | 4 × M3 insert Ø4.0, r 78.0, az ±45/±135, top face z 39.00 |
| **Turret mount** | **3 × M3 insert Ø4.0 × 8 deep, r 45.0, az 120/180/240, top face z 42.00** |
| Turret posts | Ø8.8 columns carrying those inserts, standing from z 8.00 |
| Column opening in the lid | Ø60 (from the lid spec) — the base servo hangs through it |

## The base servo

The platter has a rectangular column at its centre for the yaw servo. Its
walls are not extracted here (a rectangular pocket has no cylindrical face to
read), so these come from the legacy spec and are **UNVERIFIED**:

- inner section **12.45 × 23.05**
- the case hangs down into it; the legacy design put the flange at z 42.00
  and the case bottom at z 26.1

**An SG90 does not obviously fit.** `lib/servo.py` has SG90 `case_w` = 12.6
against a 12.45 pocket — 0.15 mm interference. MG90S is 12.5, also over. Both
our MG90S are spoken for at J3/J4, so J1 must be an SG90 and the column may
need a pass with a file. Measure the printed column before assuming.

## What this means for the turntable

The datum is z = 42.00 and the only fixing is **three M3 on a Ø90 circle at
az 120/180/240**. That is the whole interface. Anything can be built on it.

The legacy `turret_cap` and `turntable_clip` that used to sit here are
**superseded** — a 12 mm solid Ø104 plate, three M8 axle bolts with nylocs,
and three separate radial clips on three more heat-set inserts, to do a job
that wants far less hardware.
