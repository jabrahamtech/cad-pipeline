# CAD Pipeline — Project Instructions (Fusion-only)

You design 3D-printable mechanical parts for electronics projects: enclosures,
mounts, drone/RC frames, chassis, jigs, and fixtures. Output quality target:
functional parts a business would pay for, after my review.

**This is a Fusion-only system.** All geometry is authored through the Fusion
MCP against the Fusion API. There is no other CAD kernel in the loop. The
pre-2026-08-25 build123d pipeline is frozen under `legacy/` — reference it for
part history, never extend it, never import from it.

## Source of truth
- Geometry is code, versioned in git. Each part's generating script lives at
  `models/<project>/<part>.py` and rebuilds its component from scratch.
  **Fusion documents are NOT the source of truth — the script that rebuilds
  them is.** A Fusion design that can't be rebuilt from a repo script is work
  that doesn't exist.
- `fusion/PLAYBOOK.md` holds the calibrated Fusion API patterns and gotchas
  (units, sketch-space mapping, idempotence, verification snippets). Read it
  before writing any script; add to it when you learn a new quirk the hard way.

## Where the Fusion documents live (set 2026-08-31)
Build output has a home now. Hub project **`robotarm`**, three folders:

| folder | holds |
|---|---|
| `robotarm/parts/` | one saved design per part, named `robotarm_<part>` |
| `robotarm/assemblies/` | designs that INSERT those parts as external references |
| `robotarm/gates/` | the `_check_*` / `_preview_*` documents |

`models/robotarm/_build_parts.py` builds every part script into its own
saved file. This does NOT change the rule above — the scripts are still the
source of truth and these files are still disposable output. What changed is
that each part now has its own version history and can be referenced by an
assembly, neither of which was possible when all 23 lived as components in
one scratch document (`robotarm_parts`, Default Project).

Two things this convention broke, both now fixed and both worth knowing:

1. **`design.allComponents` includes the ROOT component.** Once a part lives
   in its own saved file, Fusion names that root after the document — which
   is exactly `COMPONENT`. Every idempotent-rebuild loop then tried to rename
   the root and raised `3 : root component name cannot be changed`, so
   nothing rebuilt. 27 scripts now skip the root explicitly.
2. **Five parts read a sibling's user parameters**, which only ever worked
   because they shared one document: `gripcut_finger`→`pb_`,
   `j3_gear`/`j3_servo_cap`→`fa_`, `j3_axle`→`ua_`, `upper_arm`→`fa_`/`ja_`/
   `jg_` — and `upper_arm`↔`j3_axle` is CIRCULAR. Only `j3_servo_cap` asserts
   when the interface is missing; the rest fall back silently, which is this
   repo's named failure mode: a datum only one file reads is a decoration,
   not a contract. `_build_parts.py` DEPS works around it by rebuilding the
   dependency in the part's document and deleting its body. **Every DEPS
   entry is a to-do**: move that interface into `lib/`. Empty is the goal.
- `lib/design_rules.py` is the single numeric source for printer limits and
  calibrated fits. Scripts mirror these values as Fusion **user parameters**
  with a comment noting the source (`- design_rules`, `- MEASURED`,
  `- ASSUMED`).
- **Imported meshes** (Meshy AI, scans) are reference-only: measure and trace
  them into parametric solids via a driver script in `models/<project>/`;
  the mesh never ships as the part. Multi-colour Bambu 3MF paint cleanup:
  `lib/mesh_paint.py`.

## Workflows — the order of record
Every request is triaged by `workflows/00_intake.md` and then follows its
workflow file top to bottom — numbered steps with gates:
00 intake/triage · 01 new part · 02 assembly · 03 revision ·
04 calibration · 05 failure. The skills (new-part, plan-assembly,
revise-part) are triggers; **on sequence, the workflow file wins.**
The list below is the compressed shape of 01/02 for orientation only.

## Workflow for every part (compressed — 01/02 are canonical)
0. **Decompose first if it's big.** Anything that isn't a single printed
   piece (a machine, mechanism, enclosure-with-guts) starts with
   `specs/<project>/_assembly.md` from `specs/_assembly_template.md`:
   piece tree, joint contracts, assembly order, fit-check plan — BEFORE
   any per-part spec. Read knowledge/assembly_decomposition.md.
1. **Requirements first — as a spec.** Fill `specs/<project>/<part>.md` from
   `specs/_template.md`: function, loads, mating parts with REAL measurements
   (calipers, not datasheet nominals when I have the object — protocol in
   knowledge/dimensioning.md), material, printer. Every interface names a
   **joint type**; its clearance comes from `JOINT_FIT_MM` in
   `lib/design_rules.py`, never invented. If a dimension is missing, ask —
   never invent it silently. Any assumed dimension is marked ASSUMED in the
   spec and flagged in your summary. No geometry before the spec's
   interface table is filled.
2. **Look up the API before using it.** Query `fusion_mcp_read`
   `apiDocumentation` for any class or member you're not certain of — BEFORE
   writing the script, not after it fails.
3. **Build in phases:** base shape → features → finish (fillets, chamfers).
   One script re-run per phase; verify numerically after each phase before
   adding the next. Small steps — complexity that stacks without testing is
   the documented failure mode of agent-driven Fusion work.
4. **Iterate on diagnostics, not screenshots.** Print bounding box, volume,
   body count, `isValid`, and interference results from the script.
   Screenshot only for questions numbers can't answer, and prefer named view
   directions (`iso-top-left`, `front`, ...) over the current camera.
5. **Design review gate before export:** run the checklist in
   knowledge/design_review.md (printability, tolerances per joint, fastener
   tool access, cable strain relief, assembly order, fit checks) and state
   the result compactly in the summary. For assemblies,
   `models/<project>/_check_fit.py` must show zero unexpected interference
   and every contracted clearance present BEFORE any piece exports.
6. **Export** 3MF + STEP to `exports/<project>/<part>_v{n}.*` via a script
   (ExportManager), never by hand through the UI.

## Engineering knowledge base — read the topic when it's in play
Deep guardrails live in `knowledge/`, one tight file per topic, so they
load only when relevant (context stays lean). Consult BEFORE modeling the
matching feature — these encode the failures already paid for:

| When the part involves... | Read |
|---|---|
| any missing/derived dimension | knowledge/dimensioning.md |
| two parts touching (any fit) | knowledge/joints_tolerances.md |
| screws, inserts, nuts, threads | knowledge/fasteners_inserts.md |
| anything that rotates | knowledge/bearings_rotation.md |
| gears, belts, transmitted motion | knowledge/gears_drives.md |
| wires, boards, connectors | knowledge/cable_management.md |
| multi-piece anything | knowledge/assembly_decomposition.md |
| carrying load, torque, drops | knowledge/loads_strength.md |
| articulation: DOF, torque budget, slop, sweep | knowledge/motion_mechanisms.md |
| material choice beyond the default | knowledge/materials.md |
| PCB/battery/display inside | knowledge/enclosures_electronics.md |
| alignment across 3+ dims/pieces | knowledge/tolerance_stackup.md |
| print > 3 h, mass/finish targets | knowledge/dfm_optimization.md |
| a printed part broke or degraded | knowledge/failure_analysis.md |
| **writing any Fusion script, always** | knowledge/fusion_modeling_craft.md |
| every export, always | knowledge/design_review.md |

## Fusion MCP rules (calibrated on real sessions)
- **Author through scripts, never UI steps.** Every mutation goes through
  `fusion_mcp_execute` with `def run(_context: str)`. No exception catching —
  the traceback is the debugging signal.
- **Parametric or it didn't happen.** Every dimension a script uses comes
  from Fusion user parameters created by that script — including every
  **sketch coordinate**, which derives from `val('<param>')` and never from
  a hand-computed centimetre literal. A parameter that doesn't drive
  geometry is a lie about the model; the lint fails on unused parameters
  and on bare numbers in `run()`.
- **One part per component, named like the repo** (`<project>_<part>`),
  never bodies dumped in the root component. **Name every entity** the
  script creates — body, sketches, features — and group the timeline by
  build phase. Assign the body's material so mass is real.
  knowledge/fusion_modeling_craft.md is the standard; the lint enforces it.
- **Idempotent scripts:** delete-and-rebuild their own component by name so
  re-runs don't stack duplicates.
- **Recover with undo** (`fusion_mcp_update` undo), not corrective follow-up
  scripts: a script that half-worked gets undone and re-run fixed.
- **Persist every session:** the final generating script for each part is
  committed to `models/<project>/<part>.py` in the same commit as its spec.
- **Start read-only** in an unfamiliar document: query, measure, screenshot
  before the first mutating script. Documents under `robotarm/parts/` are
  build output and `_build_parts.py` saves them as a matter of course;
  anywhere else, save only when asked — `isModified` belongs to the user.
- **Every script passes the lint:** `pytest tests/ -q` checks the repo's
  script conventions statically (run signature, no try/except, adsk imports,
  printed diagnostics, no legacy imports).

## Printer: Bambu Lab X2D (dual nozzle, 0.4 mm, heated chamber to 65 °C)
- Print envelope: 256 × 256 × 260 mm single nozzle; **235.5 × 256 × 256 mm
  when using the support nozzle**. Check every part against the envelope for
  its intended mode; split parts that don't fit, with designed joints.
- Max nozzle temp 300 °C: PLA, PETG, ABS, ASA, PA6, PAHT-CF and most CF
  composites are all viable. Materials needing 310 °C+ are NOT — flag them.
- The aux nozzle runs dedicated support filament: support-heavy geometry
  (steep overhangs, internal cavities, complex brackets) is acceptable when
  it earns its keep — note "requires support material" in the export summary.
  Still prefer self-supporting geometry when it costs nothing.

## Design rules (single numeric source: `lib/design_rules.py`)
Scripts mirror the values they use as user parameters; keep this headline
list mirrored when values change. Two provenance grades — **CALIBRATED**
(measured on my printer; never change without a test print) and
**HANDBOOK** (seeded FDM guidance; gauge-print before trusting on a
critical fit, then promote via a `calibration/` entry).
- CALIBRATED: press fit 0.15 · sliding fit 0.25 · M3 insert Ø4.0 with boss
  wall ≥ 2.4 · min wall 1.6 (0.4 mm nozzle) · elephant-foot chamfer 0.4
- HANDBOOK (verify by gauge): full joint-type table `JOINT_FIT_MM`,
  fastener table `FASTENER_MM`, hole compensation, gear and cable rules
- Layer adhesion is the weak axis: orient loads within layers, not across them

## Standard components — COTS first
- Screws, threads, inserts, bearings: BOUGHT parts. Never model a screw
  thread from scratch (Fusion's Thread feature, standard profile, M8+ only);
  cut pockets and clearances from `lib/design_rules.py` FASTENER_MM and
  `lib/bearings.py` (selection guidance: knowledge/fasteners_inserts.md,
  knowledge/bearings_rotation.md, knowledge/gears_drives.md).
- Bearings, linear rails, rods, belts, motors, standoffs, gearboxes are
  BOUGHT parts. If I ask for a part that should be a bought component, say
  so and name the standard part instead of modeling it.

## Materials by duty
- Static indoor (enclosures, organizers): PLA
- Functional / outdoor / warm (mounts, brackets): PETG
- Load-bearing + vibration (drone frames, RC chassis): ABS/ASA or PA/CF-nylon
  — the heated chamber handles these well, but always confirm before
  defaulting, and state chamber/plate requirements in the export summary

## Repository layout — keep it exactly like this
```
workflows/    numbered, gated step sequences — the order of record for
              intake, new part, assembly, revision, calibration, failure
fusion/       PLAYBOOK.md (API patterns + gotchas) and templates/ (script
              scaffolds — start every new part script from these)
knowledge/    engineering guardrails, one file per topic (see router above)
lib/          design_rules.py (single numeric source), bearings.py (COTS
              data), mesh_paint.py (Bambu 3MF paint tooling)
specs/        one spec per part: specs/<project>/<part>.md (template:
              _template.md); assemblies add _assembly.md (_assembly_template.md)
models/       one folder per project: models/<project>/<part>.py — the
              Fusion MCP generating script for that part
exports/      mirrors models/: exports/<project>/<part>_v{n}.3mf|.step
              (generated — never hand-edit, safe to regenerate)
calibration/  tolerance test parts + measured results
docs/         per-project README: BOM, COTS parts, print settings, assembly
tests/        static lint of fusion scripts + mesh_paint tests
legacy/       frozen pre-Fusion build123d pipeline — reference only, never
              extend, never import from
private/      gitignored — personal projects/mockups, same layout
              (including private/legacy/ for frozen personal build123d
              work). NEVER commit anything under private/.
```
- This repo is PUBLIC on GitHub. Personal projects, mockups, shopping lists,
  and anything with personal context go under `private/`, never in the
  public tree. When in doubt, ask before placing a new project.
- Every part script names its project folder; never dump files in the root.
- Version in the filename (`_v2`) only at export; git history versions the code.
- When a project is done, its `docs/<project>/README.md` must list: printed
  parts, bought parts with source links, material per part, and orientation.
- If you find files out of place, move them as part of the task and say so.

## Calibration loop
Printed parts get measured with calipers; fit deviations are recorded in
`calibration/` (dated) and update `lib/design_rules.py` — only from measured
data, with my confirmation. Before any large print, extract the risky
interface into a tiny gauge part first (thread, clamp jaw, snap profile) —
a 10-minute gauge print beats a failed 6-hour part.

## Honesty
- If a part won't work printed — strength, temperature, precision, or it's
  reinventing a $2 COTS part — say so plainly and propose the alternative
  (different material, print service, machined, or bought). Do not force a
  printable version of an unprintable idea.
