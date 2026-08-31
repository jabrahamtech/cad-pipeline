# robotarm — printability audit: the three wrist parts

Written 2026-08-31 against `wrist_roll.py`, `wrist_hub.py`,
`wrist_rotator.py` as they stand after the spline migration.

## Why this file exists

Jonathan, from the bench, having actually printed the wrist:

> can you make sure things like the wrist piece are easy to print because
> that piece came out with the worst supports and its just impossible to
> clean

That is a **measurement**, and it outranks every rule in this repo,
including the ones below. It is treated here as the requirement.

Two of the three scripts carried the sentence **"No support."** in their
docstrings. Neither had ever been checked. One of them was wrong by about
900 mm², and it was wrong on the part with the smallest bed contact in the
arm. That is what this audit found and what the edits fix.

`specs/robotarm/_print_plan.md` lists `wrist_roll` (#6) and
`wrist_rotator` (#7) with **no orientation note at all** — they are not in
its "Orientations that are not obvious" section — so whoever sliced them
took whatever the slicer defaulted to. Three rows need adding there; that
file was out of scope for this pass. **Adding them is the single cheapest
thing left to do.**

## Conventions

Angles are measured **from the build axis**: a face parallel to it is 0°, a
face square across it is 90°. `lib/design_rules.MAX_OVERHANG_DEG` = **50.0**
is the limit for a face that hangs off one edge.

A 90° face anchored on **both** sides is not an overhang, it is a **bridge**,
and it answers to `MAX_BRIDGE_MM` = **40.0** instead. That distinction does
most of the work below: almost every flat ceiling in these parts is a
bridge, and the ones that are not are the ones that ruined the print.

**None of this has been near a slicer or a printer.** No Fusion, no
Bambu Studio, no test print was available in this pass. Every angle and
span is computed from the polygons the scripts draw. What the geometry
implies is stated; what a slicer will actually do with it is not.

---

## 1. `wrist_roll` — the suspect

**Orientation: BACK FACE (y = −14.0) ON THE BED, built +Y. UNCHANGED —
re-derived, and it is correct.** Build height 31.0 mm. The
`bed_face_chamfer` is cut at `wro_y_back`, so the code already agreed with
the docstring; the docstring's `y = -y_back` sign slip is fixed.

Every planar face of the slab, the servo bay, the tab slots and the lead
keyway is parallel to +Y, so all of them print at 0°. The rotator bore runs
**down the build axis**, so it is a vertical hole and wants no teardrop.
The three rejected alternatives, worked rather than waved off:

| turn it | what it buys | what it costs |
|---|---|---|
| front face down (−Y) | deletes the bay ceiling outright | `wro_keel_front` starts **76.8 mm² of solid in mid-air** 8.4 mm up, and cannot be bevelled back — the lower tab slot needs full material out to y 8.6 down to z −21.5. Trades a legal bridge for an illegal 90° overhang. |
| top face down (−Z) | — | turns the bay **floor** into a 315 mm² ceiling; the keel bevel stops helping |
| keel down (+Z) | — | stands a 24 × 31 slab on a 16 × 16 keel; the whole slab underside is a 90° ceiling 4.8 mm up |
| side face down (X) | shortest build (24 mm); hex sockets become vertical | bay blind end becomes a **582 mm² ceiling on a 22.9 mm span**; the Ø11 rotator bore becomes horizontal and needs a teardrop |

### Before

| surface | angle | span / area | verdict |
|---|---|---|---|
| slab, bay, tab-slot and keyway walls | 0° | — | OK |
| keel back bevel | **45.0°** | 6.5 mm drop | OK — the reason this orientation works |
| **servo bay blind end**, y = 11.4 | **90°** | **12.4 mm bridge, 189 mm²**, at the far end of a 25.4 mm hole that opens **only at the bed** | bridge is legal — **but this is the one ceiling on the part that no tool can reach afterwards** |
| upper tab-slot roof, y = 7.1, z 6.2…10.84 | 90° | 12.4 mm bridge, 57.5 mm² | bridge, 31 % of limit |
| lower tab-slot roof, y = 7.1, z −21.5…−16.7 | 90° | 12.4 mm bridge, 59.5 mm², 1.5 mm of keel above | bridge, 31 % of limit |
| lead keyway blind end, y = −7.2 | 90° | 3.6 mm bridge, 16.7 mm² | trivial |
| **J4 hex socket roofs**, ×4 facets | **60.0°** | 9.24 mm facet × 3.4 deep, 125.6 mm² total | **over the 50° limit** |
| Ø11 rotator bore | axis ∥ build | — | OK, no teardrop needed |

### After

| surface | angle | span / area | verdict |
|---|---|---|---|
| **bay blind end — now a truncated gable** | **45.0°** flanks, rising `wro_bay_roof` 2.40 mm | then a `wro_bay_crown` **7.60 mm** flat, **98 mm²** | 90° area **189 → 98 mm²**, span **12.4 → 7.6 mm**, and the sharp internal corner an overhang detector latches onto is gone |
| keel back bevel | 45.0° | 6.5 mm | OK, now **asserted** from the drawn polygon |
| upper / lower tab-slot roofs | 90° | 12.4 mm bridges | unchanged — see below |
| lead keyway blind end | 90° | 3.6 mm bridge | unchanged |
| J4 hex socket roofs | 60.0° | 3.4 mm deep | unchanged — see below |

**Why the gable is truncated and not a full 45° roof.** A full gable over a
12.4 mm bay needs 6.2 mm of rise. There are only 5.6 mm between the bay end
(11.4) and the front face (17.0), and the last `wro_front_wall` = 3.2 mm of
those are wall — `wrist_rotator` seats on that face and the whole hand hangs
off it, so it is not allowed to thin to the MIN_WALL floor. 2.40 mm of rise
is what is left, and it is **derived from the wall, not chosen**. The cost
is real and is stated: the front wall goes 5.6 → 3.2 mm over a 7.6 mm band,
which is still 2 × MIN_WALL, and it is asserted in the script.

The bay end is a **clearance** face, not a datum — the servo is located
axially by its tabs in `wro_tab_slots` — which is why opening it up moves no
servo and touches no interface.

### Still needs support / still over the line

- **J4 hex socket roofs, 60°, 3.4 mm deep, 4 facets.** *Not fixable here.*
  A vertex-up hexagon roofs at 60° **by definition** — that is the shape.
  Rotating it 30° gives a **flat** top: 90° over the full 16.0 across
  flats, strictly worse. A self-supporting relief above the apex would need
  the roof to climb from z = ±8.0 to a peak at y ≈ 12.6, which is above
  `wro_z_top` (10.84) — it breaks out of the top face. There is exactly
  **1.60 mm** of wall above the apex (`z_top` is *derived* as apex + wall),
  so nothing fits. Mitigation, not a fix: the apex is a **clearance corner**
  — `wrist_hub`'s hex carries the 0.20 locational clearance on across-flats
  and indexes on the flats, so a small droop at the apex costs nothing that
  is loaded. If it ever does matter, the cheapest real fix is to raise
  `wro_z_top` by ~3.4 mm and cut a 45° relief; the sweep budget can take it
  (worst corner would go 24.98 → ~25.2 against `wr_sweep_r` 25.4), but it
  costs height and mass on a part hanging off a 1.0 kg·cm elbow. **Declared,
  not gated** — the script prints it as OVER on every rebuild.
- **Two 12.4 mm tab-slot bridges.** *Not fixable here.* The lower one has
  only 1.5 mm of keel above it, so there is nowhere to put a gable. The
  upper one could take one, but gabling it would hollow out the roof block
  between the bay and the top face for no rule benefit — 12.4 mm is 31 % of
  `MAX_BRIDGE_MM`. Left as bridges, declared.
- Everything above is a **bridge except the hex roofs**. Slice this part
  **with support off**; if the slicer insists on the bay, the crown is the
  only thing it can be reacting to and it is now 7.6 mm.

### Should `wrist_roll` be split? **No.**

The obvious split is a bolt-on front cap, which would delete the bay ceiling
entirely. It fails on the interface, not on the idea:

- The cap would carry **the entire effector moment** — the rotator bore and
  the J5 output end are both in that wall — through its fasteners.
- **There is nowhere to put them.** Beside the bay there are 5.8 mm of wall
  per side, of which 3.4 is the J4 hex socket, leaving **2.40 mm** (this is
  already asserted in the script as `socket_wall`). An M2 boss wants 6.0.
  Above the bay there are 4.64 mm in z, already occupied by the lead keyway
  and the upper tab slot; below it, 1.6 mm.
- A clamshell split on the XZ mid-plane instead puts the seam through **both
  hex sockets and the servo bay**, and runs the J4 torque across the seam in
  the Z-tensile direction (`Z_TENSILE_FACTOR` 0.5).

The interface cost is therefore two new faces, a locating feature, and
fasteners that do not fit, to remove a **7.6 mm bridge** — a fifth of what
the rules allow. Not worth it. The fork this part is *named* for lives in
`forearm.py`, which is where a split would actually pay; that part is
already flagged in `_print_plan.md` as needing support under the +X wall and
both lobes, and it was out of scope for this pass.

---

## 2. `wrist_rotator` — the one that was actually wrong

**Orientation: FRONT FACE ON THE BED (z = `wrt_disc_t` = 6.0), built −Z.
CHANGED.** Build height 10.0 mm. This is the largest single support saving
in the wrist.

The docstring said *"BACK FACE ON THE BED, built +Z … no bridged floor
anywhere. No support."* Read the two solids the script draws: the back hub
is Ø10.5 running z −4.0…0, and the disc is Ø36.0 starting at z = 0.

### Before — hub face on the bed

| surface | angle | span / area | verdict |
|---|---|---|---|
| **disc underside**, z = 0 | **90°** | **895 mm²** (931 gross, less the four scallop bites), hanging **4.0 mm** above the bed on a Ø10.5 post | **not a bridge — nothing anchors the far side.** Full raft, and it comes off against the face the effector bolts to |
| bed contact | — | **64 mm²** (the hub end annulus) | ~900 mm² of part standing on 64 mm² — a knock-off and warp risk in its own right |
| bore step Ø5.40 → Ø4.65, z = −0.20 | 90° | 0.375 mm annulus | fine |
| scallop walls, insert holes | 0° / axial | — | fine |

### After — front face on the bed

| surface | angle | span / area | verdict |
|---|---|---|---|
| disc → hub step, z = 0 | up-facing annulus | — | **self-supporting by construction** |
| outer profile | 0° | — | cross-section only ever shrinks going up. **Now asserted** (`hub_d <= disc_d`), not described |
| bed contact | — | **~896 mm²** (Ø36 face less scallops, insert mouths, access bore) | 14× the old contact |
| bore step Ø6.65 → Ø4.65, z = +2.30 | 90° | **1.00 mm** annular reach, anchored all round | printed, no support |
| **4 × Ø4.0 insert roofs** | 90° | 4.0 mm bridge each, under **0.50 mm** of disc skin | **NEW — this is what the flip costs** |
| scallop walls | 0° | — | OK |

**What the flip costs, stated plainly.** The four M3 insert holes are cut
from the front face, so they now open *at the bed* and are blind at the top.
`wrt_disc_t − wrt_insert_depth` = **0.50 mm** of disc skin roofs each one —
two layers, bridging 4.0 mm. That skin used to print as a floor. It is
**below MIN_WALL**, so it is deliberately **not asserted**: it is declared
here and printed by the script. Anything that shortens the disc or deepens
the inserts makes it thinner, and at that point the insert holes should
become through-holes. Four 4 mm bridges no slicer will flag, in exchange for
a 895 mm² raft against the effector mating face, is not a close call.

The inserts are unaffected otherwise: they still go in down a **vertical
hole**, which is the orientation heat-set inserts want, and the bed-face
chamfer now doubles as their lead-in.

Only the docstring and the two chamfer **names** changed — both faces were
already being chamfered at `sty_ef`, so the elephant-foot chamfer follows
the bed for free. **No dimension moved.**

---

## 3. `wrist_hub` — correct already, described wrongly

**Orientation: THE FLANGE'S OUTBOARD FACE ON THE BED (z = −7.0), built +Z.
UNCHANGED.** Build height 10.8 mm.

The docstring said *"COLLAR FACE ON THE BED"*. The bed face is the **Ø24.0
flange** face at −(`wr_journal` + `wr_flange_t`) — the one that looks at the
servo, and the one `bed_face_chamfer` is already cut on. The collar is the
Ø20.0 face 2.0 mm further up and is the only one of the three touching
nothing. The code was right; the word was wrong.

| surface | angle | span / area | verdict |
|---|---|---|---|
| Ø24 flange → Ø20 collar → 15.80 af hex | up-facing annular steps | — | **stack narrows all the way up.** Now asserted (`hub_d <= flange_d`) |
| all outer walls | 0° | — | OK |
| **bore step Ø6.40 → Ø4.75**, z = −1.40 | **90°** | **0.83 mm** inward annular reach, anchored all round | printed, no support. The only face on the part over air |
| bore step Ø4.75 → Ø6.75, z = +2.60 | widening | — | free |
| bed contact | — | 420 mm² | good |

The other docstring correction: *"the bores step DOWN in diameter as they go
up, so there is no bridged floor"* has the sign backwards. A bore that
**narrows** going up grows material inward over air; one that **widens**
cannot overhang at all. This stack does both, and the narrowing step is the
0.83 mm annulus above.

Turned over onto the hex, both annular steps invert into 90° ceilings (2.00
and 0.88 mm of reach) and bed contact drops 420 → 216 mm². Flange-down is
right and stays.

---

## Summary

| part | orientation | changed? | still over 50° | longest bridge |
|---|---|---|---|---|
| `wrist_roll` | back face (y −14.0) down, +Y | no — confirmed | J4 hex socket roofs, 60°, 4 × 31.4 mm² | 12.4 mm (tab slots); bay crown now 7.6 |
| `wrist_rotator` | **front face (z 6.0) down, −Z** | **yes** | none | 4.0 mm (insert roofs) |
| `wrist_hub` | flange face (z −7.0) down, +Z | no — confirmed | none (0.83 mm annular step) | — |

All three: **slice with support off.**

## Open, and not fixed here

- **`_print_plan.md` has no orientation rows for these three parts.** Adding
  them is the cheapest remaining action and it is what actually reaches the
  printer. Outside this pass's file scope.
- **`wro_rot_seat` vs `_check_wrist.place_rotator`.** The check script places
  `wrist_rotator` at `wro_y_front` = 17.0 with local +Z → model +Y, which
  puts the rotator's seating face at y = 17.0 − `wrt_hub_h` = **13.00**.
  `wro_rot_seat` says **11.70**. Those disagree by 1.30 mm, and at 11.70 the
  Ø36 disc's back face lands 1.3 mm *inside* the housing's front face. One of
  the two is stale after the horn → spline migration. **This is an interface,
  so it was written up rather than moved** — `wro_rot_seat` is described in
  `wrist_roll.py` as the datum the whole effector is positioned by. It wants
  a decision before anything is printed, and it is unrelated to support.
- Nothing here has been through a slicer. The claims are what the geometry
  implies; the spans and angles are computed, the *behaviour* is not
  verified. Slice all three with support off and look at the preview before
  committing filament.
