# Fusion modeling craft — a model someone else can open and edit

Read when: writing or reviewing ANY Fusion generating script. Geometry
that measures correctly but arrives as `Body1` built from `Sketch7` in a
flat 40-item timeline is a failed deliverable — the numbers are right and
the model is unusable. This file is the difference between output and
work product. Enforced by `tests/test_fusion_scripts.py`.

## 1. Name everything the script creates

Nothing keeps its default name. Every one of these is one line:

| Entity | Convention | Example |
|---|---|---|
| Component | `<project>_<part>` | `robotarm_wrist_yoke` |
| Body | function, not number | `wrist_yoke`, `gasket_ring` |
| Sketch | `sk_<what it draws>` | `sk_ears`, `sk_tab_pilots` |
| Feature | `<what it does>` | `bridge`, `bearing_bore_cut` |
| Construction plane/axis | `pl_`/`ax_` + purpose | `pl_cradle_floor` |
| Timeline group | the build phase | `roll cradle` |
| User parameter | `<prefix>_<name>` + provenance comment | `wr_gap` |

The test: someone opens the browser tree cold and can name every item's
purpose without clicking it.

## 2. Group the timeline by build phase

The phases from the workflow (base shape → features → finish) are the
groups. Capture the timeline index before a phase, group it after:

```python
start = design.timeline.count
... features for this phase ...
if design.timeline.count > start:
    g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
    g.name = 'roll cradle'
```

A group cannot contain another group. Group AFTER the features exist,
never mid-phase.

## 3. No magic numbers in geometry — the rule with teeth

CLAUDE.md says dimensions come from parameters. The violation that hides:
feature inputs use nice `ValueInput.createByString('4.0 mm')` expressions
while **sketch coordinates are raw centimetre literals** hand-derived
from those same parameters (`addTwoPointRectangle(mpt(sk, -0.603,
-0.6225), ...)`). The part looks parametric, the Fusion UI shows tidy
parameters, and editing `sv_case_w` moves nothing — the pocket was baked.

Rules:
- Every sketch coordinate is arithmetic on `val('<param>')`, never a
  literal. The only bare numbers allowed are `0`, `2` (as `/2` for a
  half-dimension), and loop counters.
- Every parameter the script declares must be USED. A declared-but-unused
  parameter is worse than none: it advertises an edit point that does
  nothing. The lint fails on both.
- A value that genuinely has no derivation still becomes a named
  parameter with a comment saying so — that's what makes it editable.

## 4. Select profiles deterministically

`allprofs(sketch)` extrudes whatever the sketch happened to produce. When
a construction line or an unintended intersection adds a profile, the
feature silently does the wrong thing. Instead:

- Assert the count you expect: `assert sk.profiles.count == 2, ...`
- Or filter by a property that encodes intent — loop count for a ring
  (`profileLoops.count == 2`), area for the largest face, centroid
  position for "the one on the left".

Same for edge/face selection in fillets and chamfers: never index blindly
into `body.faces`; find by geometry (normal direction, area, centroid) so
the script survives a parameter change that reorders the B-rep.

## 5. Assign a material

`body.material = <material>` from `app.materialLibraries`, chosen to match
the spec's print plan. It costs one line and buys real mass properties —
which is what the torque budget in knowledge/motion_mechanisms.md and the
mass targets in knowledge/dfm_optimization.md consume. Print the mass in
the diagnostics.

Closest stock matches in the Fusion Material Library:

| Print material | Fusion material | Note |
|---|---|---|
| PETG | `PET Plastic` | closest stock analogue |
| ABS / ASA | `ABS Plastic` | ASA has no stock entry |
| PA6 / PA-CF | `Nylon 6` | CF variants are stiffer than this |
| PLA | `Plastic` | generic; no stock PLA in the base library |

Look it up by name across libraries rather than hard-coding an id.

## 6. Real geometry, not faceted stand-ins

A 5°-faceted polygon standing in for an arc is acceptable while roughing
a shape and must not survive to export: it bloats the B-rep, prints
visible flats, and makes fillets fail. Use `sketchArcs` /
`sketchCircles`, or a revolve. If a facet approximation ships, the
docstring says why and the design review records it.

## 7. Sketch discipline

- One sketch, one purpose — don't accumulate unrelated geometry in a
  sketch because the plane was already there.
- Prefer `sk.modelToSketchSpace(Point3D.create(x, y, z))` over reasoning
  about the plane's u/v axes (PLAYBOOK has the observed mappings).
- Sketches on named construction planes beat sketches on origin planes
  with offset extrudes when the plane itself is a design intent
  ("cradle floor"), because the plane then moves with its parameter.

## 8. Finish features are part of the job

Fillets at loaded junctions (≥ `MIN_FILLET_LOADED_MM`), chamfers on
mating and bottom edges (elephant's foot), lead-ins on insertions. A
model with zero fillets/chamfers is unfinished, not minimal — and the
design review will fail it (knowledge/design_review.md, structure
section). Add them as their own timeline group so they can be rolled back
without disturbing the shape.

## 9. Diagnostics that prove the model, not just its size

The closing print block reports: body count, body NAME, bbox in mm,
volume in mm³, mass in g (needs §5), `isValid`, user-parameter count, and
the timeline group names. That block is what a reviewer reads instead of
opening Fusion — make it say something.
