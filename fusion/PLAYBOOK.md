# Fusion MCP Playbook

Calibrated API patterns and gotchas for authoring parts through the Fusion
MCP. Read this before writing any script; append new quirks when you learn
them the hard way (with the date and the part that taught you).

## The tool surface (official Autodesk Fusion MCP add-in)

| Tool | What it does |
|---|---|
| `fusion_mcp_execute` `featureType=script` | Runs a Python script in the active design. Entry point MUST be `def run(_context: str)`. `print()` output is returned; uncaught exceptions come back as tracebacks — that's the debugging signal, so never catch them. |
| `fusion_mcp_execute` `featureType=document` | open / close / save documents by fileId. Save only when Jonathan asks. |
| `fusion_mcp_read` `queryType=apiDocumentation` | Live Fusion API docs. `searchPattern` is a regex; `apiCategory` = class / member / description / all; `filter` narrows namespace (e.g. `adsk.fusion.ExtrudeFeatures`). Query BEFORE writing unfamiliar API calls. |
| `fusion_mcp_read` `queryType=screenshot` | PNG of the viewport. Use `direction` (front, top, iso-top-left, ...) rather than the current camera. Only when numbers can't answer the question. |
| `fusion_mcp_read` `queryType=document/projects/activeCommand` | Search/list documents and projects, list open docs (`isActive`, `isModified`). |
| `fusion_mcp_update` | undo / redo the last transaction. THE recovery tool: a half-worked script gets undone and re-run fixed — never patched with a corrective follow-up script. |
| `fusion_mcp_electronics_read` | Read-only schematic/board/library data when an Electronics document is active (pads, holes, board outline — useful for enclosure cutouts). |

## Script contract (enforced by `tests/test_fusion_scripts.py`)

Every `models/<project>/<part>.py`:

1. Module docstring: what it rebuilds, the local frame, which spec, and any
   ASSUMED values carried in.
2. `def run(_context: str)` — exactly one argument.
3. Imports `adsk.core` / `adsk.fusion`; never build123d, never `legacy.*`.
4. **No try/except.** The traceback is the signal.
5. **Idempotent:** delete any existing occurrence of its component by name,
   then rebuild. Component named `<project>_<part>`.
6. Dimensions come from **user parameters** the script creates (see below).
7. Ends by printing diagnostics: body count, bbox in mm, volume in mm³,
   `isValid`.

Start new scripts from `fusion/templates/part_scaffold.py`.

## Units — the #1 footgun

The Fusion API's internal unit is **centimetres**. Two safe patterns:

- Expression strings: `adsk.core.ValueInput.createByString('4.0 mm')` —
  readable, unit-explicit, and can reference user parameters
  (`'wr_gap/2 + wr_slide'`). Prefer this for feature inputs.
- Raw geometry (`Point3D.create`, sketch points, matrices): values are **cm**.
  A 23 mm rectangle is `2.3`. Say so in a comment when a block works in cm.

`userParameter.value` returns internal units (cm) even if the expression is
in mm. Bounding boxes and volumes come back in cm / cm³ — multiply by 10 /
1000 for mm / mm³ when printing diagnostics.

## Sketch-space mapping

Sketch (u, v) axes are NOT model (x, y) in general:

- Use `sk.modelToSketchSpace(Point3D.create(x, y, z))` to place sketch
  geometry at model coordinates — this removes the guesswork.
- Observed: sketches on `yZConstructionPlane` map sketch (u, v) → model
  (−Z, Y); sketches on `xYConstructionPlane` extrude toward +Z.
- Extrude from an offset start with
  `OffsetStartDefinition.create(ValueInput.createByString('4.0 mm'))`.

## User parameters pattern

```python
ups = design.userParameters
V = adsk.core.ValueInput.createByString

def param(name, expr, comment=''):
    p = ups.itemByName(name)
    if p is None:
        ups.add(name, V(expr), 'mm', comment)
    else:
        p.expression = expr
        p.comment = comment

param('wr_gap', '35.0 mm', 'shell OUTER width across flats - MEASURED')
param('wr_slide', '0.25 mm', 'sliding fit - design_rules')
param('wr_end_r', '18.0 mm', 'ASSUMED ear end radius about pivot')
```

- Prefix per part (`wr_`, `gb_`, ...) to avoid collisions in shared docs.
- The comment carries the provenance tag from the spec: `- MEASURED`,
  `- DATASHEET`, `- design_rules`, `- ASSUMED`. ASSUMED params are the first
  suspects when a print doesn't fit.
- Derived values as expressions (`'-(wr_gap/2 + wr_horn_standoff)'`) so
  editing one number in the Fusion UI updates the chain.
- `val = lambda n: ups.itemByName(n).value` for raw-cm sketch math.

## Idempotent rebuild pattern

```python
for occ in list(root.occurrences):
    if occ.component.name == 'robotarm_wrist_yoke':
        occ.deleteMe()
occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
comp = occ.component
comp.name = 'robotarm_wrist_yoke'
```

**Gotcha (2026-08-25, robotarm gripper): deleting an occurrence does not
release its component's NAME.** If the component is recreated in the same
script run, Fusion silently names it `robotarm_gripper_rack_jaw (1)` and
every later lookup by name misses it - the part looks built, and the
assembly checker reports the piece as absent. Rename the outgoing component
before deleting it, then assert the new one got the name:

```python
for occ in list(root.occurrences):
    if occ.component.name == COMPONENT or occ.component.name.startswith(COMPONENT + ' ('):
        occ.deleteMe()
for i in range(design.allComponents.count):      # components outlive occurrences
    c = design.allComponents.item(i)
    if c.name == COMPONENT or c.name.startswith(COMPONENT + ' ('):
        c.name = COMPONENT + '_stale_' + str(i)
occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
comp = occ.component
comp.name = COMPONENT
assert comp.name == COMPONENT, 'stale component still holds the name: ' + comp.name
```

**Gotcha (2026-08-25): setting `occurrence.transform2` more than once in a
parametric design CORRUPTS the assembly-context body proxies.** Each
assignment adds a Move feature; a stack of them leaves bodies whose
`boundingBox` collapses to a single point and whose
`measureMinimumDistance` to everything returns 0.000. Nothing errors - a
sweep just quietly reports that every part touches every other part. Build
each pose from fresh occurrences instead, handing the transform to
`addExistingComponent(component, matrix)`, measure, then delete them; and
assert the bbox is non-degenerate before trusting any measurement.

**Gotcha (2026-08-25), the worst one: an extrude CUT with no
`participantBodies` eats every other component in the document.** Feature
operations default to taking part with everything they intersect, across
component boundaries. In a shared assembly document - which is exactly what
this pipeline builds - one part's pocket silently hollows out its
neighbours. In the robotarm gripper the shell's rack channel and pinion
recess took the pinion from 1630 mm3 to 88 and the rack from 6362 to **0**,
with `isValid` still True and no error raised. Worse, the fit check then
reported ZERO INTERFERENCE, because the parts had been carved to fit each
other. Scope every non-NewBody operation:

```python
if op != NEW:
    inp.participantBodies = [comp.bRepBodies.item(i)
                             for i in range(comp.bRepBodies.count)]
```

The tell is a diagnostics block that looked right when the part was built
alone and wrong once a later script ran. Print volume per part in check
scripts and compare against what the part script itself reported.

**Gotcha (2026-08-25): a rolled-back timeline marker makes bodies measure
as HALF-BUILT, silently.** Deleting occurrences or features can leave the
marker part-way down the history; `boundingBox` then reports the body as it
was at the marker. Seen in the robotarm gripper: the pinion measured with
half its teeth cut, and a rack collapsed to a single point at (5, 5, 5) mm
while `isValid` stayed True. Call `design.timeline.moveToEnd()` before any
measurement in a check script, and assert the bounding box is non-degenerate
before trusting a number. A hidden occurrence (`isLightBulbOn = False`) also
reports an empty box - hide things only after measuring.

**Gotcha: two joined volumes that TOUCH exactly are non-manifold.** A block
whose face lands precisely on another block's face unions into a body that
shares an edge, and any later fillet or chamfer fails with
`ASM_BL_NON_MAN_EDVERT`. Make joined volumes overlap by a wall thickness -
never butt them. (robotarm wrist_fork, 2026-08-25.)

**Gotcha: a timeline group needs at least 2 features.** `timelineGroups.add`
raises `Create Group Feature Error: At least 2 features needed for a group`
on a one-feature phase. Guard with `if design.timeline.count - start > 1`.

**Gotcha: `userParameter.deleteMe()` fails silently while another parameter's
expression still references it.** Delete derived parameters before the ones
they are derived from, and re-check rather than trusting the call.

Place the part in the assembly by giving `addNewComponent` a transform (or
set `occ.transform2` with a row-major 4×4 in cm). For imported occurrences
with denormalized transforms, SET `transform2` to the world transform
directly — composing with parents gets rejected.

## Verification snippets

```python
b = comp.bRepBodies.item(0)
bb = b.boundingBox
print('bodies:', comp.bRepBodies.count)
print(f'bbox mm: X {bb.minPoint.x*10:.2f}..{bb.maxPoint.x*10:.2f}'
      f'  Y {bb.minPoint.y*10:.2f}..{bb.maxPoint.y*10:.2f}'
      f'  Z {bb.minPoint.z*10:.2f}..{bb.maxPoint.z*10:.2f}')
print(f'volume: {b.volume*1000:.0f} mm3, valid: {b.isValid}')
```

- Fit checks between parts: `design.createInterferenceInput(...)` /
  `analyzeInterference` (query apiDocumentation for the exact signature
  in the running Fusion version before use).
- Point-to-point / entity measurements: `app.measureManager`.
- Mesh extents (imported concepts): `meshBody.displayMesh
  .nodeCoordinatesAsDouble` — stride 3, cm.

## Export pattern

Export via script, never the UI — `comp.parentDesign` → `exportManager`;
`createSTEPExportOptions(path)` for STEP and `createC3MFExportOptions
(body_or_comp, path)` for 3MF (verify exact names via apiDocumentation —
they have shifted between releases). Write to
`exports/<project>/<part>_v{n}.step|.3mf`. Version bumps only at export;
never overwrite a version that may have been printed.

## Working style (what fails, from real sessions and Autodesk's own guidance)

- **Small steps win.** Complexity compounds fast when features stack without
  testing intermediate results. One phase per script run; verify; continue.
- **Faceted stand-ins are fine mid-design** (5°-faceted arcs as polygons for
  robustness); smooth with real arcs in the finish pass.
- **Performance:** big loops of sketch entities are slow in-session — batch
  geometry where possible, and test with realistic input sizes early.
- **Dialogs block everything.** Never call UI methods that pop modal dialogs
  (`ui.messageBox`, command dialogs) — the MCP call hangs until a human
  dismisses them. Print instead.
- **Start read-only** in any unfamiliar document; screenshot + query before
  the first mutation. Save is Jonathan's call.
- **What the MCP is strong at:** scripted geometry, batch renames/exports,
  parameter sweeps, inspection/reporting, screenshots for review.
  **Weak at:** one-shot complex organic models, giant assemblies, anything
  needing human judgment about "right" — that's the spec's job.

## Sources

- Autodesk: [Introducing the Fusion MCP](https://www.autodesk.com/products/fusion-360/blog/introducing-the-fusion-mcp-opening-fusion-to-ai-powered-workflows/)
- Autodesk: [Build Your Own Fusion Add-ins with the Fusion MCP](https://www.autodesk.com/products/fusion-360/blog/build-your-own-fusion-add-ins-with-the-fusion-mcp/)
- Autodesk: [Improve Your Fusion Workflow with the Claude Desktop Connector](https://www.autodesk.com/products/fusion-360/blog/how-to-improve-your-fusion-workflow-with-the-claude-desktop-connector/)
- [MCP Server for Autodesk Fusion — App Store](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100&ln=en&os=Win32_64)
- Community bridges for comparison: [ndoo/fusion360-mcp-bridge](https://github.com/ndoo/fusion360-mcp-bridge)
- Plus the live tool schemas of the installed add-in (execute / read /
  update / electronics_read) and this repo's own session history
  (`models/robotarm/*.py`).

## Rename the outgoing component BEFORE deleting its occurrences

The delete-then-rename order works right up until the occurrence you delete
is the component's **last** one. At that moment the component is orphaned:
it drops straight out of `design.allComponents` while still reserving its
name, so the rename loop that follows cannot reach it, and `addNewComponent`
is handed `robotarm_x (1)`. Every later lookup by name misses.

It hides well, because a part script run on its own always has a keeper
occurrence left by the previous run. It only fires after a check script has
placed extra occurrences and then cleaned them up — i.e. on the second run
of an assembly gate, never on the first.

```python
STALE = COMPONENT + '_stale_'
for i in range(design.allComponents.count):      # rename while still reachable
    c = design.allComponents.item(i)
    if c.name == COMPONENT or c.name.startswith(COMPONENT + ' ('):
        c.name = STALE + str(i)
for occ in list(root.occurrences):               # then drop the occurrences
    if occ.component.name.startswith(STALE):
        occ.deleteMe()
```

Keep the `assert comp.name == COMPONENT` after `addNewComponent` regardless.
It is the only thing that turns this from a silent wrong answer into a stop.

## analyzeInterference returns Occurrences OR BRepBodies

`InterferenceResult.entityOne` is an `Occurrence` when each component has a
single occurrence and a `BRepBody` when it has several — same call, same
inputs, different type. Reaching straight for `.component` works until the
day you place a part twice, then throws `AttributeError` in the middle of a
sweep. Resolve the name defensively:

```python
comp = getattr(entity, 'component', None) or getattr(entity, 'parentComponent', None)
```

## A clearance disc is not enough where the neighbour continues through

Subtracting a cylinder about a joint axis is the right way to guarantee
swing clearance — it cannot go stale the way a drawn outline can. But it
only models a neighbour that **swings**. A neighbour that swings AND
continues past the joint (a link's far end, an upper arm at an elbow) needs
the disc plus the half-space behind it. Cutting only the disc leaves the
fork webbed shut, and it looks entirely plausible in the diagnostics: right
volume, one body, every assertion green. Nothing but a render caught it.

If a part has an opening that must stay open, assert it: measure the
material on the axis between the prongs and require it to be zero.

## Fusion keeps ONE Python session, so `sys.modules` is stale by default

Every script run shares one interpreter. A part script that imports shared
repo code — a solver in `lib/`, a catalogue, anything — gets whatever was
imported the FIRST time that session, no matter how many times the file has
been edited since.

Today's symptom was an honest `ImportError: cannot import name ARM_CLEAR_MM`,
because the constant was new. That is the lucky case. The normal case is that
the constant already existed and merely changed value: the rebuild then runs
against yesterday's numbers, every assertion passes, every diagnostic line
prints a plausible figure, and the CAD and the solver have silently diverged.

Purge before importing, in the part script itself so it cannot be forgotten:

```python
for _stale in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
    del sys.modules[_stale]
from lib.something import CONSTANT
```

`importlib.reload` is not enough on its own — it does not re-run the parent
package or pick up a module that was imported under a different name.

## val() is centimetres, createByString() is millimetres

`userParameter.value` returns Fusion's INTERNAL unit — centimetres — while
`ValueInput.createByString` parses a bare number in the DOCUMENT's unit,
which for these models is millimetres. Compute something in Python from
`val()` and hand it straight back as `'%.4f' % x` and the feature is built
**ten times too small**, at a tenth of the intended offset.

There is no error. The script runs, the body is valid, the diagnostics print
numbers that look plausible because they are printed from the same wrong
value. The pruner's drive tie came out 0.35 mm thick instead of 3.5, sitting
on the pitch line rather than above the tooth roots, and ate 8.6 mm³ out of
the pinion. It took a profile-by-profile comparison against a known-good
part to find, because every obvious suspect — phase angle, tooth geometry,
transform — was provably identical.

Either keep every extent as a parameter EXPRESSION (`'gr_rack_back'`,
`'pr_pin_y + pr_pin_d'`), which is preferable anyway because it stays
parametric, or funnel Python-computed lengths through one helper:

```python
def mm(cm):
    return '%.4f mm' % (cm * 10.0)
```

and assert no bare numeric format string survives in the file.

## Redefining a SHARED user parameter reshapes every part already built

`turntable_clip.py` is a small part, so it set the shared silhouette radius to
something sensible for a small part:

```python
style('radius', '3.0 mm', "clip corner radius - smaller than the arm's 6.0")
```

`sty_radius` is shared. A `FilletFeature` created with
`addConstantRadiusEdgeSet(col, ValueInput.createByString('sty_radius'), True)`
stores a **live reference** to that parameter, not the number it had at the
time. Changing it re-cut every fillet in every part already in the document:

| part | before | after | delta |
|---|---|---|---|
| `pruner_shell` | 13937 | 15289 | **+1352** |
| `forearm` | 22226 | 22435 | +209 |
| `shoulder_bracket` | 24497 | 24717 | +220 |

Nothing errored. Every body still reported `isValid True`. Every part's own
script still printed its own correct volume, because each one prints
immediately after building, *before* the next script moves the parameter. The
damage is only visible if you re-read an earlier part after a later one runs —
which is exactly what nothing was doing.

Note the direction: the volumes went **UP**. A rogue CUT makes parts smaller
and is easy to suspect; a rogue *parameter* made them bigger, which reads like
a missing cut and sends you hunting in the wrong file.

**Rule: a file may define a shared parameter only with the value every other
file gives it.** If this part needs a different number, it is not that shared
parameter — give it a local one under the file's own prefix:

```python
style('radius', '6.0 mm', '... SHARED, do not change it here ...')
param('radius', '3.0 mm', "THIS part's corner radius, deliberately local")
...
f_inp.addConstantRadiusEdgeSet(col, V(PREFIX + 'radius'), True)
```

This applies to every shared block — `wr_`, `tt_`, `sty_` — and to any value a
feature references by NAME rather than by number.

The general defence is a ledger: rebuild every part from its committed script
into one fresh document and compare all the volumes at the END, not as you go.
`models/robotarm/_check_ledger.py` does that. It is the only gate that can see
a part being changed by a file that does not mention it.

## Units in ASSERTIONS - the bug that keeps coming back

**Five times now.** `val()` and `tval()` return Fusion's internal
CENTIMETRES. Every dimension a human writes in these scripts is MILLIMETRES.
An assertion that compares one against the other does not fail loudly - it
fails on geometry that is perfectly good, which sends you looking for a
modelling fault that is not there.

The four:

- `upper_arm`: `overlap >= 1.5` fired on a good 3.8 mm overlap
- `forearm`: `disc_r - journal_r >= 1.5` fired on a good 4.0 mm wall
- `arm_budget.py`: g.cm compared against kg.cm - reported the arm at 873 % of
  duty and then refused to find any link section that fitted
- `turntable_ring`: `reach_in > boss_d / 2 + 1.6` treated the 1.6 mm wall as
  16 mm and rejected a 47 mm scallop over a 34 mm bore
- `base_lid`: passed CENTIMETRES to an `xy_arc` helper that feeds `pt()`, and
  `pt()` is the one that divides by ten. The slot was built at r 1.3 mm and
  cut nothing. **It threw no error** - the tell was the body volume coming
  back byte-identical to the run before the feature was added. When a CUT
  changes nothing, the cut is in the wrong place; assert on the volume drop.

**The rule: convert once, at the top of the block, into `_mm` names. Never
compare a `val()` against a bare literal.** If a comparison has no `_mm` in
it and a number on the right, it is wrong until proven otherwise.

A comment saying "these are centimetres" has now failed to prevent this four
times. The naming convention is the mechanism.

## A fault that does not move under a sweep is in the FIXED half

`_check_j1` found four things and every one of them read **identically at all
thirteen yaw poses**. The instinct built up on `_check_shoulder` is the
opposite — there, a constant interference across a sweep was the tell that the
*placement* was wrong (the 49 mm³ that turned out to be a static horn, the
9.7 mm³ that turned out to be a square boss). Both readings are available from
the same number, and the way to tell them apart is cheap:

- **constant, and between two parts that both rotate** → suspect the placement
- **constant, and between two parts that are both fixed** → it is real, and
  the sweep is not what found it; the sweep is what finally put the two bodies
  in one document

The J1 rollers foul the stator's own base plate at every angle because the
base plate does not turn. No amount of sweeping was going to make that number
move, and no amount of staring at the viewport was going to show it either —
the bearing is a bought part that appears in no model file, so until a gate
built it as an envelope there was nothing there to collide with.

**A bought part that no script models is a hole in every check you have.**
The MG995 at J2, the 608ZZ at J1, the SG90 horn — each one had to be built as
a scratch envelope before any gate could see it. If a joint's load path runs
through something the repo does not model, that joint has not been checked.

## An assertion on SIZE is not an assertion on POSITION

`base_lid` asserts its opening against the stator's servo well:

```python
assert ox_mm >= STATOR_WELL_X + 1.0 and oy_mm >= STATOR_WELL_Y + 1.0
```

Both sides are **extents**. The opening is 26.0 long, the well is 22.8 long,
the assertion passes with 3.2 to spare — and the opening is cut about the
origin while the well sits at y +5.20, so the lid masks 3.60 of it. The
constants were even honestly labelled *"MEASURED off the built
turntable_stator"*: they measured how big it is and not where it is.

This is the shaft-offset bug's third victim, and the first one a size-only
check let through. **Where a feature clears another part, assert on the
INTERVAL — `lo <= other_lo and hi >= other_hi` — not on the length.** A
length comparison cannot see an offset, and offsets are exactly what gets
added late.
