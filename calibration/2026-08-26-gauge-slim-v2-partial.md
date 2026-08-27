# 2026-08-26 — gauge_slim_v2, PARTIAL

**This session did not complete the sheet.** It is recorded anyway because two
of its findings are load-bearing and one of them retires a hypothesis.

Plate: `exports/robotarm/gauge_slim_v2.3mf`. Material: **PETG**, confirmed by
Jonathan. Supports: **OFF**, confirmed — the `FLAT` / `S11FLAT` stubs bridged
in air, so their droop is real.

**Spool and print profile were NOT recorded.** Every number below is therefore
tied to an unidentified spool. Note them before the next entry or this one
cannot be compared against anything.

## THE INSTRUMENT IS THE LIMIT, AND IT IS WHY THIS IS PARTIAL

The caliper used **does not resolve below 0.1 mm**. The fits this plate exists
to settle are 0.15 press / 0.25 sliding / 0.35 rotating — the entire
difference between a press fit and a sliding fit is 0.10, which is one count
on that instrument. Every station whose answer is a *dimension* is therefore
unmeasurable here, and `gauge_reduce` section 2 was never run: it needs two
bosses and two bores to fit a curve and correctly refuses without them.

**A 0.01 mm caliper is the blocking purchase for this project.** Nothing in
the fit table can be promoted from HANDBOOK to CALIBRATED until there is one.

## What was established

| | Reading | Grade |
|---|---|---|
| Plate X, nominal 96.00 | **95.6 – 95.8** | MEASURED, ±0.1 |
| Plate Y, nominal 150.00 | **149.7 – 150.0** | MEASURED, ±0.1 |
| Lever hex across flats, nominal 15.80 | **15.8** | MEASURED, ±0.1 |
| Hex socket `10` (0.10 clearance) | **accepts the lever, slight play** | OBSERVED, qualitative |

### The printer is dimensionally healthy — hypothesis retired

Plate X is **0.2–0.4 %** under nominal and Plate Y **0.0–0.2 %**. Both are
normal-to-low for PETG. The lever's 15.80 hex reads at nominal.

Earlier in the session a shrinkage of **~1.25 %** was inferred from small-feature
readings (D20 19.7, D8 7.8, B20 19.8) and a reprint was nearly recommended on
the strength of it. **That inference was wrong.** Those three readings were
rounded to 0.1 mm and are inconsistent with the plate's own edges: at the
measured shrinkage D20 should read ≈ 19.94, not 19.7. The likely cause is a
caliper zero offset or a reading taken across a chamfer. **They are discarded
and nothing derives from them.**

Do not read the X-vs-Y difference as axis asymmetry. At 0.1 mm resolution on a
96 and a 150 mm edge, that gap is inside the noise.

### The hex socket sweep — one real result

Socket `10` — a **0.10 mm** clearance on the 15.80 hex — **accepts the lever
and has slight play**. It was described as the tightest of the four that still
gives. Sockets `20`, `30` and `40` were not swept; the tip-travel method was
not run, so there is no quantified backlash figure for any socket.

The arm currently ships **0.20** (`wr_*` hex sockets at 16.00 on a 15.80 hub)
in `upper_arm` ×4, both wrist hubs and `shoulder_hub`.

**What this does and does not support.** It supports the claim that 0.10 is
assemblable in PETG at 3.4 mm socket depth. It does **not** quantify how much
slop 0.20 actually has, because that measurement was not taken. Tightening the
shared hex fit on this evidence would be acting on one qualitative observation
of one socket on one plate, with no repeat — so it is proposed, not applied.

## Not measured

Bearing seats `S10`/`S11`/`S12` (finger-spin, needs no caliper — this was the
cheapest remaining test and is still open), the `FLAT` / `S11FLAT` stubs, both
pilot rows, and every collapsed station in step 5.

`S11` is worth doing on its own: it is the seat `turntable_stator` ships, and
whether a 608 spins on an 11.0 collar is a yes/no question needing no
instrument at all.

## Still owed, unrelated to the plate

- **SG90 horn hub diameter** — the only invented dimension in the J1 gate,
  modelled at Ø6.30 against `tt_screw_bore` Ø6.00.
- **Platter servo column**, 12.45 × 23.05 UNVERIFIED, against a 12.60 SG90.

Neither is on this plate; both need a servo in hand and a caliper.

## design_rules.py

**Unchanged.** Nothing here meets the bar CLAUDE.md sets for promoting a value
to CALIBRATED.
