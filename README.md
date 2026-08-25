# cad-pipeline

CAD as code, Fusion edition: 3D-printable mechanical parts (enclosures,
mounts, frames, jigs) authored as **Fusion API Python scripts driven through
the [Fusion MCP](https://www.autodesk.com/products/fusion-360/blog/introducing-the-fusion-mcp-opening-fusion-to-ai-powered-workflows/)**,
with specs, a static script lint, and a calibration loop that feeds measured
print results back into shared design rules. No click-modeling — every part
is reviewable, diffable, and regenerable from its script. The Fusion document
is never the source of truth; the script that rebuilds it is.

An earlier build123d incarnation of this pipeline is frozen under `legacy/`.

## How a part gets made

1. **Spec first** — `specs/<project>/<part>.md` (from `specs/_template.md`):
   function, an interface table of every dimension that matters (each tagged
   MEASURED / DATASHEET / ASSUMED), loads, and a print plan. No geometry until
   the interface table is filled.
2. **Script** — `models/<project>/<part>.py`: an idempotent Fusion API script
   (`def run(_context)`) run via the MCP's `fusion_mcp_execute`. Every
   dimension is a Fusion **user parameter** with a provenance comment, so the
   part stays editable in the Fusion UI and magic numbers stay out of feature
   dialogs. Patterns and gotchas live in `fusion/PLAYBOOK.md`; new scripts
   start from `fusion/templates/part_scaffold.py`.
3. **Verify numerically** — scripts print bbox, volume, body count, and
   validity; phases are verified before the next one is added. Screenshots
   only for questions numbers can't answer.
4. **Lint** — `tests/test_fusion_scripts.py` statically enforces the script
   contract (entry point, user parameters target component, no try/except,
   printed diagnostics, no legacy imports).
5. **Printability gate** — overhangs, minimum walls, bridges, build envelope
   (Bambu Lab X2D), then scripted export of versioned 3MF + STEP to
   `exports/<project>/<part>_v{n}`.
6. **Close the loop** — printed parts get measured with calipers; fit
   deviations are recorded in `calibration/` and update
   `lib/design_rules.py`. Every print makes the next one more accurate.

## Layout

```
fusion/       PLAYBOOK.md (calibrated Fusion API patterns + gotchas),
              templates/ (part scaffold, export script)
lib/          design_rules.py (single numeric source for printer-calibrated
              fits/limits), bearings.py (COTS data), mesh_paint.py
specs/        one spec per part (template: _template.md)
models/       one folder per project; <part>.py is the Fusion generating script
exports/      generated 3MF/STEP, versioned in the filename — never hand-edit
calibration/  dated gauge prints + measured results
docs/         per-project BOM, print settings, assembly notes
tests/        static fusion-script lint + mesh tooling tests
legacy/       frozen pre-Fusion build123d pipeline (models, lib, tests)
```

## Using Claude to drive this repo

`CLAUDE.md` is the system prompt: it encodes the Fusion MCP workflow, the
printer's real limits, and the design rules. What makes the difference is how
you prompt it:

### 1. Start from the real object, not an idea

Give measurements, not vibes. "Design a mount for this board — outline
65.2 × 30.1 mm measured with calipers, holes Ø3.2 on a 58 × 24 grid" produces
a part that fits. The workflow forces this: the agent must fill the spec's
interface table before modeling, and anything it can't get from you is marked
**ASSUMED** — in the spec AND as a comment on the Fusion user parameter —
those are the first suspects when a print doesn't fit.

### 2. Print gauges before parts — the single biggest filament saver

Before printing any large part, ask for **just the risky interface as a tiny
test gauge**: the thread, the clamp jaw, the snap profile, the saddle radius —
a few grams and 10–20 minutes instead of a full part. Report the result
("the 28.7 thread fits snug, 29.1 is loose") and it lands in `calibration/`,
updating `lib/design_rules.py` for every future part. Worked examples from
the build123d era live in `legacy/models/` with their measurements in
`calibration/`.

### 3. Iterate on numbers, not screenshots

Ask for diagnostics — volume, bounding box, an interference check between two
components — instead of renders. "What's the wall thickness around the insert
boss?" gets a checkable answer; "does it look right?" doesn't.

### 4. Change parameters, not geometry

For revisions ("the board is actually 66.1 wide", "the fit is too tight"),
the agent changes a user-parameter expression, re-runs the idempotent script,
and shows a before/after diagnostics diff. Because dimensions are Fusion user
parameters, you can also nudge them yourself in the Fusion UI — but the
script is the source of truth, so lasting changes go back into it.

### 5. Let it say no

`CLAUDE.md` instructs the agent to refuse bad prints honestly: parts that
should be bought, materials the printer can't do, geometry that will fail on
layer lines. If it says "buy this instead," that's the pipeline working.

## Running it

Fusion side: Autodesk Fusion with the MCP Server add-in enabled
(Preferences → General → API), connected to Claude. The repo lint runs
headlessly:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
```

Printer profile: Bambu Lab X2D, 0.4 mm dual nozzle. Calibrated fits and
limits live in `lib/design_rules.py` — recalibrate with your own gauge prints
before trusting them on a different machine.
