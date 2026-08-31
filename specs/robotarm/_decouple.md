# Decoupling the robotarm part scripts — migration plan

**Status:** `lib/joints.py` is written and imports clean. **No consumer has
been changed yet.** This file is the ordered instruction set for changing
them. Written 2026-08-31.

**Nothing here has been built in Fusion.** Every number below was verified
statically, by reproducing the part scripts' own arithmetic in Python. The
claim being made is "these two expressions are equal", not "this printed".

---

## 1. Why

Five part scripts read another part's Fusion **user parameters** out of a
document they happened to share:

| consumer | reads | producer |
|---|---|---|
| `gripcut_finger` | `pb_edge_off` | `pruner_blade` |
| `j3_gear` | `fa_bore_d`, `fa_plate_t` | `forearm` |
| `j3_servo_cap` | `fa_cap_*`, `fa_lobe_*`, `fa_j3_centre`, `fa_l2`, `fa_wall` | `forearm` |
| `j3_axle` | `ua_socket_d` | `upper_arm` |
| `upper_arm` | `fa_elbow_clear`, `jg_bolt_clear`, `ja_socket_d`, `jg_face`, `jg_bolt_head_d`, `jg_collar_l`, `wr_reach`, `ja_tap_l` | `forearm`, `j3_gear`, `j3_axle` |

`upper_arm ↔ j3_axle` is **circular**. Only `j3_servo_cap` asserts when the
interface is absent; the other four fall back to a hardcoded literal and
print nothing, which is CLAUDE.md's named failure mode — *a datum only one
file reads is a decoration, not a contract*.

Two costs, both already written down in the drivers:

1. `_build_parts.DEPS` rebuilds each dependency **inside the consumer's own
   part document** and then deletes its body, so the parameters exist. Every
   DEPS entry is a to-do. Empty is the goal.
2. `_build_assembly.py` cannot build a **referenced** Fusion assembly:
   external references do not carry document user parameters, so
   `_preview_arm.py` would have nothing to pose from. The arm assembly is
   monolithic because of this. `PARTS` also lists `upper_arm` **twice** —
   a fixed point for the cycle, not a fix.

Not a single one of these reads survives contact with the question *where
does this number actually come from?*

---

## 2. The audit — every cross-part datum

Grades: **MEASURED** / **DATASHEET** / **DERIVED** / **ASSUMED**.

### 2.1 Already derivable from an existing lib module — delete the read

| datum | what it really is | verdict |
|---|---|---|
| `pb_edge_off` | `lib/pruner_linkage.CHOSEN.edge_offset` (3.5). `gripcut_finger` **already imports CHOSEN** and computes `gf_af = edge_offset − 2.0` three lines above the read. The assert compares a number with itself by a longer route. | DERIVED — delete |
| `fa_bore_d` | `wr_hub_d + rot` = 20.0 + 0.35 = 20.35. Both terms are the shared pivot contract + `design_rules`. | DERIVED — `HEX_PIVOT.bore_d` |
| `fa_plate_t` | `wr_journal + wr_flange_t + fa_cbore_extra` = 5.0 + 2.0 + 0.5 = 7.5. `j3_gear` carries it as a literal `7.5` and asserts against the forearm's derivation. | DERIVED — `HEX_PIVOT.plate_t` |
| `jg_bolt_clear` | `FASTENER_MM['M3']['clearance']`. **Both sides already read `design_rules`** — the cross-document assert compares `design_rules` with itself. | DERIVED — delete |
| `jg_face` | `lib.gears.J3_PAIR.face` | DERIVED |
| `jg_collar_l` | `plate_t + free` | DERIVED — `ELBOW_BOLT.gear_collar_l()` |
| `jg_bolt_head_d` | M3 socket-head counterbore depth 3.2 | DATASHEET — `M3_SOCKET_HEAD_CBORE_MM` |
| `wr_reach` | `gap + socket_d` = 0.4 + 3.4. Typed as the literal `3.8` in six scripts. | DERIVED — `HEX_PIVOT.reach` |
| `fa_j3_centre` | `lib.gears.J3_PAIR.centre_distance` | DERIVED |
| `fa_l2` | the forearm's own link length. `j3_servo_cap` reads it **only** to subtract `y_pin = −l2 + centre` and get back into the servo's frame. State the contract in servo-local and it drops out. | not an interface — delete |
| `fa_wall` | `design_rules.MIN_WALL_MM` | DERIVED — delete |

### 2.2 Genuinely shared — they now live in `lib/joints.py`

| datum | grade | note |
|---|---|---|
| `wr_pivot_af` 16.0 | ASSUMED | extracted from `wrist_hub.py` |
| `wr_straddle` 24.0 | ASSUMED | extracted from `wrist_roll.py` — it is the roll housing's own width; see §6 |
| `wr_sweep_r` 25.4 | ASSUMED | extracted from `wrist_roll.py` |
| `wr_hub_d` 20.0 | DERIVED | must exceed the hex across corners, 18.24 |
| `wr_journal` 5.0, `wr_flange_d` 24.0, `wr_flange_t` 2.0 | ASSUMED | extracted from `wrist_hub.py` |
| `ua_socket_d` / `ja_socket_d` 3.4 | ASSUMED | extracted from `upper_arm.py` — **the primitive behind `wr_reach`** |
| `ua_drum_r` 13.0 / `fa_elbow_clear` 13.4 | ASSUMED | **one number with two names** — see §2.3 |
| `ja_tap_l` 9.0 | ASSUMED | extracted from `j3_axle.py` |
| `ja_collar_d` 11.0 | DERIVED | inside the 608 inner race with 0.5 of margin |
| `ja_press` / `fa_brg_press` 0.02 | ASSUMED | same figure applied to a shaft fit and a housing fit; neither gauged |
| `fa_lobe_pad` 3.5, `fa_lobe_over` 1.0, `fa_cap_margin` 0.1 | ASSUMED | extracted from `forearm.py` |
| `fa_lobe_radius_j3` 4.5 | MEASURED | probed against the built body — a **ceiling**, not a preference |
| `fa_cap_head_d` 6.0 | DATASHEET | ISO 4762 M3 socket head; `design_rules.FASTENER_MM` has no head column |
| `fa_cap_screw_y/_z`, `fa_cap_reach`, `fa_cap_t`, `fa_lobe_z` | DERIVED | **solved**, not chosen — `servo_pad()` reproduces the forearm's own solve exactly |

### 2.3 The circular dependency, named

`upper_arm.py` sets `ua_drum_r = 13.0` and says *"NOT FREE: the forearm cuts
its own clearance at fa_elbow_clear = 13.4"*. `forearm.py` sets
`fa_elbow_clear = 13.4` and says *"ua_drum_r drives it and that is now
13.0"*. Each names the other as the authority; `upper_arm` then reads
`fa_elbow_clear` to assert on it, **falling back to `drum_r + 0.4`** — the
very number it was checking. The assert cannot fail on its own fallback.

It is not a cycle. It is one number with two names, and the drum radius is
the primitive. `lib/joints.ELBOW` owns it; `clearance_r` is `drum_r + FREE`,
derived. `ELBOW.floor_r()` states what actually bounds it below (a 16.0 af
socket needs r ≥ 11.24), so 13.0 is visibly above the floor **for section,
not for fit** — which is the fact the two comments were circling.

---

## 3. What `lib/joints.py` owns

| object | replaces |
|---|---|
| `HEX_PIVOT` (`J3_PIVOT` / `J4_PIVOT`) | the whole `wr_*` block, in 6 scripts, plus the fork-plate derivations (`plate_t`, `bore_d`, `cbore_d`, `boss_r`, `plate_in/out`, `reach`, `hex_af`, `hex_across_corners`) |
| `ELBOW` | `ua_drum_r` ↔ `fa_elbow_clear` |
| `ELBOW_BOLT` | `jg_bolt_clear`/`ua_bolt_clear`, `jg_bolt_head*`, `jg_collar_l`, `ja_tap_l`, and `buy_mm()` — the M3 length `upper_arm` prints from five sibling parameters |
| `J3_BEARING` | who touches which **race** at the 608ZZ: `ja_collar_d`, `ja_journal_*`, `fa_brg_pocket_d`, `fa_brg_bore`, `fa_brg_shoulder` |
| `J3_PAD` / `servo_pad()` | the entire `fa_cap_*` + `fa_lobe_*` interface, in the **servo's own frame** |
| `J3_STANDOFF` | `fa_j3_standoff` |
| `GRIPCUT_KEY` | `pb_thk`/`pb_gap`/`pb_hub_r`/`pb_key_*` ↔ `gf_mount_z`/`gf_ring_od`/`gf_key_*` |
| `pad_x_to_link_y()` | the only place `fa_l2` is still needed — in `forearm.py`, which owns it |
| `LOC` / `ROT` / `FREE`, `M3_SOCKET_HEAD_*` | the fit literals retyped in every script |

Every derivation is pinned by an assert against the number the part builds
**today**, so adopting this is a refactor and not a redesign. If one of those
asserts fires, a consumer in `models/` has drifted and the import fails
loudly instead of a part printing wrong.

---

## 4. The migration, in order

Line numbers are as of **2026-08-31** and four agents are editing these files
concurrently — **anchor every edit on the parameter name, not the line**.

Each script keeps mirroring its numbers as Fusion user parameters (CLAUDE.md:
*"parametric or it didn't happen"*). What changes is where the **expression**
comes from: `lib/joints`, not a literal and not another part's document.

### Step 0 — `lib/joints.py` lands (done)

Verify: `python3 -c "import sys;sys.path.insert(0,'.');import lib.joints"`.

### Step 1 — `gripcut_finger.py` + `pruner_blade.py` (isolated, zero risk)

**`models/robotarm/gripcut_finger.py`**

- add `from lib.joints import GRIPCUT_KEY, GRIPCUT_FACE_OFFSET` beside the
  existing `from lib.pruner_linkage import CHOSEN`
- **L102** `param('lead', '2.0 mm', …)` → `'%.3f mm' % GRIPCUT_KEY.lead`
- **L103** `param('af', '%.3f mm' % (CHOSEN.edge_offset - 2.0), …)` →
  `'%.3f mm' % GRIPCUT_FACE_OFFSET`; keep the comment, add
  *"lib/joints.GRIPCUT_KEY.face_offset — the blade's edge equation with a
  smaller number"*
- **L111** `mount_z '3.55 mm'` → `'%.3f mm' % GRIPCUT_KEY.mount_z`
- **L113** `bore_d '3.2 mm'` → `'%.3f mm' % GRIPCUT_KEY.pivot_bore_d`
  (**see §6 — this is 3.2 and `design_rules` says M3 clearance is 3.4**)
- **L114** `ring_od '12.0 mm'` → `'%.3f mm' % GRIPCUT_KEY.ring_od`
- **L115–L119** `key_w/key_l/key_h/key_y` → `GRIPCUT_KEY.boss_w/.boss_l/
  .boss_h/.boss_y`
- **L154–L158** — **DELETE the whole `pb_edge = ups.itemByName('pb_edge_off')`
  block.** It is the assert `pb_edge_off − gf_lead == gf_af` and both sides
  now come from the same object. Replace with nothing: `lib/joints.py`
  already asserts `GRIPCUT_FACE_OFFSET == 1.5` at import.

**`models/robotarm/pruner_blade.py`**

- add `from lib.joints import GRIPCUT_KEY`
- **L125** `thk '3.5 mm'` → `GRIPCUT_KEY.carrier_thk`
- **L126** `gap '0.05 mm'` → `GRIPCUT_KEY.half_gap` (keep the prose — it is
  the argument for the number)
- **L134** `hub_r '6.0 mm'` → `GRIPCUT_KEY.hub_r`
- **L138** `pivot_d '3.2 mm'` → `GRIPCUT_KEY.pivot_bore_d`, and **fix the
  comment**: it currently says *"M3 clearance — design_rules FASTENER_MM"*
  and that table says 3.4
- **L166–L169** `key_w 4.2 / key_l 3.2 / key_d 1.4 / key_y −7.9` →
  `GRIPCUT_KEY.pocket_w / .pocket_l / .pocket_d / .boss_y`. Delete the
  comments that name `gf_key_*`: a comment is not a contract, and after this
  there is one object to name instead.
- **L130** `edge_off` — **leave it**. It already reads `CHOSEN.edge_offset`.

Then: delete `'gripcut_finger': ['pruner_blade']` from `_build_parts.DEPS`.

### Step 2 — `j3_gear.py`

- add `from lib.joints import HEX_PIVOT, ELBOW_BOLT, M3_SOCKET_HEAD_DIA_MM, M3_SOCKET_HEAD_CBORE_MM`
- **L101–L103** the `wrist(...)` block → `HEX_PIVOT.pivot_af`,
  `HEX_PIVOT.hub_d`, `HEX_PIVOT.reach` (see Step 3 — do all six scripts in
  one commit)
- **L122** `plate_t '7.5 mm'` → `'%.4f mm' % HEX_PIVOT.plate_t`; the comment
  *"ASSERTED equal to fa_plate_t when that parameter exists"* becomes
  *"derived in lib/joints.HEX_PIVOT — the forearm reads the same object"*
- **L125** `collar_l` → `'%.4f mm' % ELBOW_BOLT.gear_collar_l(HEX_PIVOT)`,
  or keep it as the Fusion expression `jg_plate_t + jg_free` (equivalent)
- **L132** `bolt_head '6.0 mm'` → `M3_SOCKET_HEAD_DIA_MM`
- **L133** `bolt_head_d '3.2 mm'` → `M3_SOCKET_HEAD_CBORE_MM`. **Rename it**
  while you are there: `bolt_head_d` is a *depth* and `bolt_head` is a
  *diameter*, which is exactly backwards from how they read (§6)
- **L314–L320** the `fa_bore_d` block → drop the `itemByName`; assert
  unconditionally against `HEX_PIVOT.bore_d`:
  - `J3_PAIR.r_tip(z_gear) * 2 > HEX_PIVOT.bore_d` (the disc cannot pass)
  - `HEX_PIVOT.hub_d < HEX_PIVOT.bore_d` (the journal fits)
- **L321–L326** the `fa_plate_t` block → **delete**. Both sides are now
  `HEX_PIVOT.plate_t`; `lib/joints.py` asserts it equals 7.5 at import.

Then: delete `'j3_gear': ['forearm']` from DEPS.

### Step 3 — the `wr_*` block, all six scripts, ONE commit

`wrist_hub.py` (L100–L118), `wrist_roll.py` (L107–L117), `forearm.py`
(L141–L152), `upper_arm.py` (L100–L101), `j3_gear.py` (L101–L103),
`j3_pinion.py` (L115–L117), `j3_axle.py` (L96–L97).

Every one of these becomes `'%.4f mm' % HEX_PIVOT.<field>`. **The values do
not move** — `lib/joints.py` asserts `reach == 3.8`, `plate_t == 7.5`,
`bore_d == 20.35`, `boss_r == 13.775` at import, which are the numbers these
scripts build today. This is a mechanical substitution and it must be atomic:
a document holding two definitions of `wr_reach` is the bug being removed.

Delete every *"SHARED, defined identically in …"* comment. Replace with one
line: `# lib/joints.HEX_PIVOT — change it there`.

`wr_reach` in particular stops being typed: it is `gap + socket_d`.

### Step 4 — `upper_arm.py` + `j3_axle.py` — **this breaks the cycle**

**`upper_arm.py`**

- add `from lib.joints import HEX_PIVOT, ELBOW, ELBOW_BOLT`
- **L117** `socket_d '3.4 mm'` → `HEX_PIVOT.socket_d`
- **L123** `drum_r '13.0 mm'` → `'%.4f mm' % ELBOW.drum_r`; rewrite the
  comment — it no longer points at the forearm, it points at
  `lib/joints.ELBOW`, and `ELBOW.floor_r()` is what bounds it below
- **L413–L421** the `fa_elbow_clear` read + fallback → **delete the
  `itemByName`**. `_allow` becomes `ELBOW.clearance_r`. The assert stays and
  becomes meaningful for the first time: it is no longer checking a fallback
  against itself. Delete the `[fa not in doc - allowance ASSUMED]` branch
  from the print.
- **L432–L437** the `jg_bolt_clear` block → **delete**. Both sides read
  `FASTENER_MM['M3']['clearance']`.
- **L438–L444** the `ja_socket_d` block → **delete**. Both sides are
  `HEX_PIVOT.socket_d`.
- **L449–L470** the screw-length block that reads `jg_face`,
  `jg_bolt_head_d`, `jg_collar_l`, `wr_reach`, `ja_tap_l` → replace the whole
  `_need`/`else` structure with `ELBOW_BOLT.buy_mm(HEX_PIVOT)` and
  `ELBOW_BOLT.bottoms_mm(HEX_PIVOT)`. It **always** prints now, instead of
  silently stopping when the siblings are absent. Verified statically:
  head-to-hex 18.5, across 17.2, to-tap 35.7, **buy M3 × 45**, bottoms at
  44.7 — identical to what the two-pass build prints today.

**`j3_axle.py`**

- add `from lib.joints import HEX_PIVOT, J3_BEARING, ELBOW_BOLT`
- **L96–L97** the `wr_` block → `HEX_PIVOT` (Step 3)
- **L111** `press '0.02 mm'` → `J3_BEARING.shaft_press`
- **L116** `socket_d '3.4 mm'` → `HEX_PIVOT.socket_d`; the comment *"upper
  arm hex socket depth — ua_socket_d. ASSERTED against it below"* is now
  *"lib/joints.HEX_PIVOT.socket_d — the same object the upper arm cuts"*
- **L118** `gap '0.4 mm'` → `HEX_PIVOT.gap`
- **L119** `collar_d '11.0 mm'` → `J3_BEARING.collar_d`
- **L124/L126** `journal_d` / `journal_l` → `J3_BEARING.journal_d` /
  `.journal_l` (or keep the Fusion expressions — same value)
- **L133** `tap_l '9.0 mm'` → `ELBOW_BOLT.tap_l`
- **L286–L290** the `ua_socket_d` block → **delete**

Then: delete `'j3_axle'` and `'upper_arm'` from DEPS, **and delete the second
`'upper_arm'` entry from `_build_assembly.PARTS`** with its comment. The
cycle is gone, so the fixed point is not needed.

### Step 5 — `forearm.py` + `j3_servo_cap.py` — the servo pad

**`forearm.py`**

- add `from lib.joints import HEX_PIVOT, ELBOW, J3_BEARING, J3_PAD, J3_STANDOFF, pad_x_to_link_y`
- **L185/L187** `plate_t` / `bore_d` — keep as Fusion expressions (they are
  already derived), but source their inputs from `HEX_PIVOT`
- **L220** `elbow_clear '13.4 mm'` → `'%.4f mm' % ELBOW.clearance_r`, comment
  → *"derived: ua_drum_r + free, lib/joints.ELBOW"*
- **L239/L245/L246/L247** `lobe_t` / `lobe_z` / `lobe_pad` /
  `lobe_radius_j3` → `J3_PAD.pad_t`, `J3_PAD.half_z`, the `pad_pad` argument,
  `J3_PAD.corner_r`. Keep the probe history on `lobe_radius_j3` — it is a
  measured ceiling and the prose is the evidence.
- **L270/L273** `lead_key_d` / `lead_key_l` → `J3_PAD.lead_key_d` /
  `.lead_key_l`
- **L306** `j3_standoff` → `'%.5f mm' % J3_STANDOFF`
- **L320–L331** the `brg_*` block → `J3_BEARING.pocket_d`,
  `.shoulder_bore_d`, `.shoulder_t`, `.housing_press`
- **L341** `cap_head_d '6.0 mm'` → `M3_SOCKET_HEAD_DIA_MM`
- **L575–L616** — **this is the big one.** The whole in-`run()` solve
  (`_win_y1`, `_head_r`, `cap_screw_z`, `_y_win`, `_sep`, `_y_pilot`,
  `cap_screw_y`, `cap_margin`, `cap_reach` and the four asserts that follow)
  is replaced by reading `J3_PAD` and converting with `pad_x_to_link_y`:
  - `cap_screw_z` ← `J3_PAD.fix_z`
  - `cap_screw_y` ← `pad_x_to_link_y(J3_PAD.fix_x, val('l2'))`
  - `cap_reach`  ← `pad_x_to_link_y(J3_PAD.x_hi, val('l2'))`
  The asserts move with the solve — `servo_pad()` already runs all of them
  and raises with the same messages. Verified statically: `fix_z` 4.2,
  `fix_x` 22.70106 (= `cap_screw_y` **4.90106** in the link frame),
  `x_hi` 27.40106 (= `cap_reach` **9.60106**) — **exactly** the numbers this
  file builds today.
  - **while you are in there, see §6**: L575 solves against a window edge
    computed with `fa_loc` (0.2) while L799 *cuts* the window at
    `fa_srv_clear` (1.0). `servo_pad()` uses the clearance that is actually
    cut. It does not change the answer today (the tab pilot governs by
    0.80 mm) but the contradiction goes.
- **L335** `cap_t` — keep as `fa_lobe_t`; it is the same object now

**`j3_servo_cap.py`**

- add `from lib.joints import J3_PAD, J3_STANDOFF, M3_SOCKET_HEAD_DIA_MM, M3_SOCKET_HEAD_CBORE_MM`
- **L112–L137** — **delete the entire `fa()` helper and every call to it.**
  This is the change that matters: the cap works in the **servo's own frame**
  and stops needing the forearm at all. `y_pin`, `l2` and `centre` disappear
  with it.
  - `t` ← `J3_PAD.pad_t` · `half_z` ← `J3_PAD.half_z`
  - `x_lo` ← `J3_PAD.x_lo` · `x_hi` ← `J3_PAD.x_hi`
  - `case_x0/x1/z` ← `J3_PAD.case_x0/.case_x1/.case_z`
  - `screw_a/b` ← `J3_PAD.tab_x_lo/.tab_x_hi`
  - `fix_x` ← `J3_PAD.fix_x` (**no longer `screw_y − y_pin`**) ·
    `fix_z` ← `J3_PAD.fix_z`
  - `wall` ← `MIN_WALL_MM` from `design_rules`
- **L159/L163** `lead_key_d` / `lead_key_l` → `J3_PAD.lead_key_d` /
  `.lead_key_l`
- **L175–L176** the `fa_lobe_radius_j3` read with its `else 4.5` fallback →
  `J3_PAD.corner_r`. **This silent 4.5 fallback is the most dangerous line in
  the five files**: it is the one place a *measured ceiling* is defaulted.
- keep the docstring's argument that the cap is a MATING part — it is still
  true, the mate is just no longer a document lookup.

Then: delete `'j3_servo_cap': ['forearm']` from DEPS. **DEPS is now `{}`.**

### Step 6 — the drivers

- `_build_parts.py`: `DEPS = {}`. Rewrite the docstring section *"THE
  DEPENDENCY MAP IS A BUG BEING WORKED AROUND"* to record that it was fixed
  and how; keep the DEPS machinery, since an empty map is the assertion.
- `_build_assembly.py`: remove the second `upper_arm` pass (Step 4).

---

## 5. What still blocks the REFERENCED assembly

Step 6 does **not** on its own let `_build_assembly.py` insert external
references. `_preview_arm.py` poses the arm from **19 document user
parameters** via `gv()`, and those still do not travel across a reference.

Six of the nineteen are now derivable from `lib/joints.py` + `lib/gears.py`:
`fa_plate_in`, `fa_plate_out`, `fa_j3_standoff`, `fa_j3_centre`,
`ua_half_x`, `ua_socket_d`. The remaining thirteen are turntable
(`tt_race_z`, `tt_roller_r`, `tt_axle_z`, `tt_roller_od`), shoulder
(`sb_plate_in`), wrist (`wro_y_front`), pruner (`pb_tail_r`, `pr_pin_y`,
`pr_tooth_lead`, `pr_rack_teeth`, `pr_pitch`), gripper (`gr_offset`,
`gr_face`, `gr_r_pitch`) and link (`ua_l1`, `fa_l2`) datums.

**That is a second pass, and it wants the same treatment**: a `lib/pose.py`
(or an extension of `lib/joints.py`) holding the joint transforms, so
`_preview_arm` computes the pose instead of reading it out of a document.
Out of scope here; named so it is not lost.

---

## 6. Found while auditing — reported, NOT fixed

Four other agents are editing these files concurrently. None of these were
touched.

1. **`pb_pivot_d` / `gf_bore_d` are 3.2 and both call it "M3 clearance".**
   `design_rules.FASTENER_MM['M3']['clearance']` is **3.4**. Two parts share
   one screw at a bore 0.2 under the table they cite. 3.2 is what is built,
   so `GRIPCUT_KEY.pivot_bore_d` records 3.2 rather than silently correcting
   it — changing a pivot bore is a design decision with a fit behind it.
   **Needs Jonathan's call.**

2. **`forearm.py` cuts its servo window at one clearance and solves against
   another.** L799 cuts at `fa_srv_clear` (1.0, `SERVO_CASE_CLEARANCE_MM`);
   L575 computes `_win_y1` from `fa_loc` (0.2). The assert at L619 therefore
   checks the screw head against an edge 0.4 mm inboard of the one actually
   cut. Latent only — the tab pilot governs by 0.80 mm — but it is the same
   class of bug `SERVO_CASE_CLEARANCE_MM` was created to kill.

3. **`lib/servo.py`'s frame docstring contradicts its own corrected lead
   datum.** It says *"+X runs along the case length away from the shaft,
   **toward the lead end**"*, but `lead_x = −shaft_from_end` is **negative**
   — the lead end is −X. The numbers are right; the prose is stale from
   before the 2026-08-28 correction. Given that this exact block already
   caused five parts to notch the wrong wall, the sentence is worth fixing.

4. **`jg_bolt_head` / `jg_bolt_head_d` are named backwards.** `bolt_head` is
   the head **diameter** (6.0); `bolt_head_d` is the counterbore **depth**
   (3.2). `upper_arm.py`'s screw-length maths uses `jg_bolt_head_d` as a
   depth and is arithmetically correct, which means the names are a trap that
   has not sprung yet.

5. **`fa_brg_shoulder` is 0.50 mm**, floored at 0.4 rather than at
   `MIN_WALL_MM` 1.6. Defensible — it is an annular lip in pure compression,
   not a spanning wall — but it is the thinnest feature in the elbow and it
   is one extrusion pair. `lib/joints.py` records the 0.4 floor and the
   reasoning; if `plate_t` ever comes down, this goes first.

6. **`lib/gears.J3_MOUNT` is documented as deletable** ("kept above ONLY
   because forearm.py still reads its seat_z"). `J3_STANDOFF` in
   `lib/joints.py` reads `J3_MOUNT.seat_z` for exactly that reason, and
   `gears.py` already asserts `J3_HUB.seat_z == J3_MOUNT.seat_z`. When
   `J3_MOUNT` goes, `J3_STANDOFF` switches to `J3_HUB.seat_z` and the value
   does not move.

7. **`tests/test_mesh_paint.py` cannot be collected** — `lib/mesh_paint.py`
   imports `scipy`, which is not installed, so a bare `pytest tests/ -q`
   aborts at collection and runs *no* lint at all. `pytest tests/ -q
   --ignore=tests/test_mesh_paint.py` reports 20 pre-existing failures in
   `models/robotarm/` (mostly `test_no_magic_numbers_in_geometry`) — none of
   them in `lib/`, which the lint does not cover.
