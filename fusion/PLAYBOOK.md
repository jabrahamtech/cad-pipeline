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
