# J3 and J4 : MG90S → SG90

**Jonathan, 2026-09-03: _"both the motors will be sg90"_.** The hardware is in
hand. This is a statement about the machine, not a proposal about it.

Both motors is the **upper-arm-to-wrist pair**: **J3 elbow** and **J4 wrist
pitch**. Nothing else on the arm changes — J1, J5 and the effector were
already SG90 and J2 is still the MG995.

---

## 1. Where "which servo drives which joint" now lives

`lib/joints.py` → **`JOINT_SERVO`**, one dict, six rows, read by everything.

```
J1 SG90 · J2 MG995 · J3 SG90 · J4 SG90 · J5 SG90 · J6 SG90
```

with `servo_for(joint)`, `servo_name_for(joint)`, `stall_kgcm(joint)` and
`stall_nm(joint)` beside it.

**It replaced eleven copies of one sentence.** Before this pass the answer
was typed into `lib/gears.py` twice (`_SERVOS['MG90S']`), `lib/joints.py`
once, `lib/arm_loads.STALL_KGCM` as five bare torques, `_check_leads.MOUNTS`
as a `servo=` column, and six part scripts as `CATALOG['MG90S']`. Every one
of them agreed with the others only by inspection.

That is this project's named failure — *a datum in a shared library which
only one file reads is a decoration, not a contract* — and a servo swap is
the change that finds every copy at once, because it moves a case dimension,
a spline, a stall torque and a seat height **together**. A consumer still
holding its own copy would build to the old servo while every gate reported
green. Worse: an MG90S is **larger in every dimension that matters**, so a
stale copy errs toward *clear*. That is the shape of failure that survives a
gate.

### What reads it now

| consumer | what it takes |
|---|---|
| `lib/gears.py` | `J3_SERVO`, `J3_INPUT_STALL_NM`, `J3_MOUNT`, `J3_HUB`, the engagement floor |
| `lib/arm_loads.py` | `STALL_KGCM` and `SERVO_AT`, so **every duty percentage in the arm** |
| `lib/joints.py` | `J3_PAD`, and so the whole `fa_cap_*` interface |
| `forearm.py` | both lobe envelopes, the flange recess, the lead keyway, the tab pilots |
| `j3_servo_cap.py` | the cap window, keyway and pilots |
| `j3_pinion.py` | the spline stack and its diagnostics |
| `wrist_hub.py` | the J4 spline stack and its engagement floor |
| `_check_leads.py` | the `servo` column **and** the J3/J4 shaft stations |
| `_check_servo_fit.py`, `_check_motor_clearance.py` | **transitively** — both import `_check_leads.MOUNTS` and take the servo from it |
| `forearm_px.py`, `forearm_nx.py` | **transitively** — every station is `fa_*` out of the document |

### Copies that still exist, and why

| file | copy | verdict |
|---|---|---|
| `servo_body.py` | `SERVO = 'MG90S'` | **Leave it.** It is not a copy of the mapping, it is a *substitution anchor*: both gates rewrite that exact literal to build whichever servo solid they need. Changing it breaks them. |
| `_check_loads.py` | `BOUGHT_G['MG90S J3'/'MG90S J4'] = 13.4` | **STALE AND WRONG.** An SG90 is **9.0 g**. The load model is carrying 4.4 g too much at each of J3 and J4. Gate file, not mine to edit — see §5. |
| `lib/arm_budget.py` | `('MG90S J4', 13.4, …)`, and `13.4 * l1` for the elbow servo | Same 4.4 g error, in the parametric model. Not in my scope. |
| `turntable_stator.py`, `shoulder_bracket.py`, `j1_hub.py` | comments reading *"2.50 is all an SG90 has (the MG90S has 4.00)"* | Prose only, no geometry. Now says "the other micro servo" is 2.50 too — harmless but no longer a contrast. |
| `servo_adapter.py`, `horn_adapter.py` | `SERVO = 'MG90S'` | Standalone utility parts, not on the arm's load path. |

---

## 2. Every datum that moved

### The servo itself (`lib/servo.py`, DATASHEET)

| | MG90S | SG90 | Δ |
|---|---|---|---|
| stall | 2.0 kg·cm | **1.6** | −20 % |
| mass | 13.4 g | **9.0** | −4.4 g |
| case l × w × h | 22.8 × 12.4 × 24.0 | **22.7 × 12.2 × 23.7** | smaller in all three |
| `tab_below_top` | 3.00 | **4.30** | **+1.30** — the number that drives most of the rest |
| `tab_thk` | 2.50 (ASSUMED) | **2.40** (drawing) | −0.10, and better provenance |
| `tab_hole_pitch` | 27.50 (**DERIVED**, no drawing) | **27.80** (drawing-stated) | +0.30, and **better provenance** |
| `tab_span` | 32.10 | **32.30** | +0.20 |
| `boss` Ø × h | 6.0 × 6.0 | **5.0 × 4.2** | smaller *and* shorter |
| `spline` Ø × h | 5.0 × **4.0** | **4.9 × 2.5** | **the engagement, halved** |

### Derived, in the parts

| datum | MG90S | SG90 | note |
|---|---|---|---|
| `fa_lobe_t` = `fa_cap_t` = `sc_t` | 5.50 | **6.70** | +1.20, straight from `tab_below_top` |
| `fa_j4_lobe_t` = `wh_seat_z` = `jp_seat_z` = `J3_MOUNT.seat_z` | 5.90 | **7.10** | +1.20 — **arm width at the wrist** |
| `fa_lobe_z` = `sc_half_z` | 8.80 | **8.70** | −0.10, from the narrower case |
| `fa_seat_z` | 7.20 | **7.10** | follows `lobe_z` |
| `fa_seat_y_max` | 10.59767 | **10.67992** | boss circle falls to a shorter lobe later |
| `fa_win_z` | 13.40 | **13.20** | case window and flange recess height |
| `fa_recess_l` | 32.60 | **32.80** | wider flange |
| `fa_lobe_pad` | 4.15 | **4.10** | derived from the recess |
| `fa_lead_key_l` / `sc_lead_key_l` | 7.50 | **7.65** | wider tab pitch, shorter case |
| `fa_cap_screw_z` / `sc_fix_z` | 4.20 | **4.10** | follows `lobe_z` |
| `fa_cap_screw_y` | 4.90106 | **5.01606** | **the tab pilot governs it**, see §4 |
| `fa_cap_reach` / `sc_x_hi` | 9.60106 / 27.40110 | **9.71606 / 27.51610** | one head, one wall, one margin past the screw |
| `wh_boss_bore_d` / `jp_boss_bore_d` | 6.40 | **5.40** | smaller boss to clear |
| `wh_boss_bore_h` | 5.60 | **3.80** | shorter boss — **1.80 mm less of the hub wasted on clearance** |
| `wh_broach_d` / `jp_broach_d` | 4.75 | **4.65** | |
| `wh_broach_to` | 9.60 | **6.30** | now ends *inside* the collar, not in the hex |
| `wh_engaged` / `jp_engaged` | **4.00** | **2.50** | §3 |
| `wh_washer_d` / `access_d` | 6.35 / 6.75 | **6.25 / 6.65** | |
| `J3_HUB.min_gear_root_r` | 4.80 | **4.30** | §4 |
| pinion root stress | 7.053 MPa | **5.642 MPa** | −20 %, tracking stall |
| `_check_leads` J3 `shaft.z` | 5.50 | **6.70** | now derived |
| `_check_leads` J4 `shaft.x` | 25.80 | **27.00** | now derived |
| duty at the J3 **joint** (×2 ×0.90) | 1.800 kg·cm | **1.440** | −20 % |
| duty at the J4 joint | 1.000 kg·cm | **0.800** | −20 % |
| J3 utilisation | ~52 % | **~65 %** | measured figures ×1.25 |
| J4 utilisation | ~36 % | **~45 %** | |

### What deliberately did **not** move

`fa_j3_standoff` **10.80**, and this is arithmetic rather than luck:
`seat_z` is the case top plus one running gap and `fa_lobe_t` **is** the case
top, so the two cancel and the standoff is `free + face + case_gap` for any
micro servo in the catalogue. `lib/joints.j3_standoff()` states the
cancellation and `forearm.py` now **asserts its own expression against it**.

With it, unchanged: `fa_j3_band` 10.80, `fa_j3_gear_clear` 19.40,
`fa_j3_pin_clear` 10.40, `fa_j3_centre` 27.20, `fa_cap_pilot_depth` 8.00,
the whole `fa_seam_*` block, `fa_plate_*`, both lobe corner radii, and the
entire `forearm_rail` piece. **The standoff web does not move.**

---

## 3. The 2.5 mm engagement — the number to argue about

J3 drives the whole forearm, wrist and head through a 2:1, and it will now do
it through **2.50 mm of broached PETG** where it had 4.00.

### The torque arithmetic

The broach is a round bore the steel spline cuts its own form into, so the
torque is carried in **shear on the cylindrical surface**:

```
F   = T / (d/2) = 2T/d          A = π·d·L          τ = 2T / (π·d²·L)
L  ≥ 2T / (π·d²·τ_allow)
```

`τ_allow` = `PETG_TENSILE_MPA` 35.0 × `PETG_SHEAR_FACTOR` 0.6 ÷
`SAFETY_FACTOR['cyclic']` 4.0 = **5.25 MPa** — the same allowable the tooth
roots are checked against. **In-plane is correct here:** the pinion prints
tooth-face-on-the-bed with the bore vertical, so this shear runs *within*
each layer, not across layer boundaries.

| | MG90S | SG90 |
|---|---|---|
| T at the spline | 196.13 N·mm | **156.91** |
| bore Ø | 4.75 | **4.65** |
| engaged L | 4.00 | **2.50** |
| sheared area | 59.69 mm² | **36.52** |
| **τ** | 1.384 MPa | **1.848 MPa** |
| utilisation of 5.25 MPa | 26 % | **35 %** |
| L the torque needs | 1.054 mm | **0.880 mm** |
| margin on that | ×3.79 | **×2.84** |

### The verdict, plainly

**Shear is not what binds, and it is not close.** 2.50 mm is **2.8×** the
length the torque actually needs, at **35 % of an allowable that already
carries a safety factor of 4**. The swap raises the stress in this joint by
34 % and it remains comfortable.

The 20 % lower stall is doing real work: **the spline sees the servo's
torque, not the joint's.** The 2:1 that multiplies the elbow's output is
entirely *downstream* of this interface.

**What binds is a manufacturing floor, not a stress.** `spline_hub()`'s
`engage_min` used to default to 2.00 and carry this silently. It is now
passed in and derived — `lib/gears.J3_ENGAGE_FLOOR_MM` is
`max(shear floor 0.880, forming floor 2.000)`. The forming floor wins:
2.00 mm is how much broached bore the steel needs to cut a usable tooth trace
in PETG rather than skive a short lip. **2.50 clears it by 0.50 mm — 25 %.**

### So: is it enough? Yes — with two things said out loud

1. **The margin cannot be bought.** `engaged = min(hub top, spline top) −
   boss top`, and with a 10.00 face the hub top is far above the spline, so
   **`engaged` *is* `spline_h`** — the whole spline and not a micron more. A
   thicker pinion buys nothing; only a different servo would. That is a
   change of kind from the MG90S, where 4.00 was a choice with room behind it.

2. **The exposure is provenance, not stress.** `spline_h` 2.50 is DATASHEET
   for a cheap servo, and `lib/servo.py`'s own docstring rates that grade
   **weak**. A spline 0.5 mm shorter than the drawing puts this joint *on* the
   floor with nothing in reserve. **CALIPER THE SPLINE before the pinion
   prints.** `_gauge_broach_sheet.md` is the print that settles both this and
   the ASSUMED 0.25 broach interference; it has not been run.

**Marginal in one further respect, and it is worth knowing:** the hub's
guided length falls from 10.00 mm to **6.30 mm** in a 10.00 mm face
(3.80 of boss clearance + 2.50 of broach). The mesh force acts at mid-face,
5.00 — still **inside** the guided span, so the pinion is *not* overhung, but
it sits at 79 % of the span instead of dead centre. The tilting couple into
the servo's own output bearing rises. It is the same couple in the same
direction it already was, and it is the load `lib/servo_hub.py`'s docstring
already names (the goBILDA ServoBlock argument); it is not made new here,
only slightly worse.

---

## 4. J3_PAIR survived — and is more comfortable than before

**Yes.** m 1.00, 18T/36T, centre 27.20, gear Ø38.0: **unchanged.**

The binding constraint on the pinion is that its **root radius must clear the
boss bore**, and the SG90's boss is *smaller*:

| | boss Ø | bore Ø | root floor | 18T roots at | clearance |
|---|---|---|---|---|---|
| MG90S | 6.0 | 6.40 | 4.80 | 7.75 | 2.95 |
| **SG90** | **5.0** | **5.40** | **4.30** | 7.75 | **3.45** |

`lib/gears.py` asserts it rather than trusting this table. **The swap makes
the compact gears more comfortable, not less** — and the root stress falls
7.053 → 5.642 MPa against an 8.75 allowable, 64 % of it.

Two other things the SG90's shorter boss buys:

- `wh_boss_bore_h` 5.60 → 3.80, so **1.80 mm less of the wrist hub is spent
  just getting past the collar**.
- The hub's minimum height falls 7.60 → 5.80, so the 7.00 collar now clears
  it **alone**. On the MG90S the collar was 0.60 short and `wr_reach` had to
  make up the difference — *"at `wr_reach` < 0.60 the hub stops being able to
  drive a servo"*. **That dependency is gone**, not merely satisfied.

---

## 5. What I could not fix, and what to build

### Outside my files — needs a decision

1. **`_check_loads.py` `BOUGHT_G` is stale.** `'MG90S J3'` and `'MG90S J4'`
   are 13.4 g; an SG90 is 9.0 g. The elbow and wrist moments are being
   computed with **8.8 g of servo that is not on the arm**. This partly
   *offsets* the duty loss — but by an unknown amount until the keys are
   fixed. Same in `lib/arm_budget.py`. Both should read `servo_for()` and
   `.mass_g`.
2. **`tests/test_arm_loads.py::test_a_load_over_duty_direct_is_within_duty_geared`
   now fails**, and it is a true report rather than a bug. It probes at
   1.5 kg·cm, chosen to sit between direct drive (1.00) and geared (1.80).
   Geared is now **1.44**, so 1.5 falls outside on both sides. The probe load
   wants lowering to ~1.2 kg·cm. Tests are not in my file list.
3. **`specs/robotarm/_assembly.md`, `_state.md`, `forearm.md`, `_flange.md`,
   `_build.md`, `wrist_hub.md`, `_gauge_broach_sheet.md`** all still say J3
   and J4 are MG90S, and `_assembly.md` still claims the inventory is used
   exactly. **It is not**: this layout wants **5 × SG90** against the 3 that
   `lib/servo.INVENTORY` records. Jonathan says he has them;
   `lib/joints.SERVOS_REQUIRED` computes the real requirement so the two can
   be compared when `INVENTORY` is updated.

### Stale measurements — re-run, do not trust

- **GATE `servo_fit`'s 195.75 mm³** of flange interference was measured
  against an **MG90S**. The two-cut fix is unchanged and correct; the band
  moves outboard with `fa_j4_lobe_t` 5.90 → 7.10. The number quoted in five
  docstrings is now historical.
- **GATE `motor_clearance` J3 STRIKE 17.0 mm³ / J4 TIGHT 0.00 mm.** Both were
  measured with the old servo. The SG90 is smaller in every case dimension
  (−0.1 l, −0.2 w, −0.3 h) but sits **1.20 mm further out** at both joints. I
  have not tried to fix the strike and have not knowingly made it worse — but
  **I cannot claim it is unchanged**, because the case moved. Re-gate.

### A latent inconsistency I did not introduce and did not fix

`lib/joints.servo_pad()` computes `x_lo` from a `pad_pad` default of 3.50,
while `forearm.py`/`j3_servo_cap.py` use the derived `fa_lobe_pad` (4.10).
So `J3_PAD.x_lo` is −12.15 and `sc_x_lo` is −12.75. Nothing asserts one
against the other, so nothing is wrong today — but it is the only number in
that interface where the library and the part disagree, and it predates this
change (MG90S: −11.85 vs −12.80).

### Build and gate, in this order

```
forearm  →  forearm_px, forearm_nx, forearm_rail
         →  wrist_hub, j3_pinion, j3_servo_cap
```

then the gates: **`servo_fit`** (was 7/7 — it must stay 7/7, and it is now
driving SG90 solids because `MOUNTS` derives), **`motor_clearance`**,
**`leads`**, **`elbow`**, **`loads`** (expect J3 ≈ 65 %, J4 ≈ 45 %, and note
the mass error in §5.1), **`ledger`**.

### Verified statically only

Every parameter table and every pre-geometry assert in `forearm`,
`forearm_px`, `forearm_nx`, `wrist_hub`, `j3_pinion` and `j3_servo_cap` was
executed against a stubbed Fusion and a shared parameter document, in build
order, and all of them resolve. **No geometry was built and nothing here is a
claim that it will.**

That dry run earned its keep once: `fa_cap_screw_y` is *solved* to sit
exactly `_sep` from the servo's own tab pilot, and writing it to five decimal
places rounds it — the MG90S rounded **up** and passed, the SG90 rounds
**down** by 4.1e-7 mm and the assert fired. The design is identical either
way; the check was measuring the `printf`. Both `forearm.py` and
`j3_servo_cap.py` now carry `PARAM_ROUND_MM` and compare against the
precision the station is actually written to. Anything short by more than
that is still a real collision and still fires.
