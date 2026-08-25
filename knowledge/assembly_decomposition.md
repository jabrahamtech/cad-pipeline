# Assembly decomposition — how big models become buildable ones

Read when: the request is a machine, mechanism, enclosure-with-guts, or
anything that won't be a single printed piece. THE core guardrail for
complex models: decompose first, contract the interfaces, verify the fits
— never model a monolith and carve it up after.

## 1. Decompose before modeling

Split a design into pieces when any of these hold, and split at natural
interfaces (flat mating planes, joint axes, function boundaries):

- Envelope: piece exceeds the X2D envelope for its print mode.
- Orientation conflict: two load paths need different layer orientations —
  each piece gets its OWN best orientation (the #1 strength lever).
- Support elimination: a split turns an internal cavity or steep overhang
  into two self-supporting halves.
- Material mix: rigid frame + TPU grommet + clear window = separate pieces.
- Iteration cost: the risky interface lives in a small piece that reprints
  in 20 minutes, not embedded in a 6-hour body.
- Service: what must open later (lids, hatches, trays) is its own piece.

Output of this step — BEFORE any geometry — is `specs/<project>/_assembly.md`
(template: `specs/_assembly_template.md`): the piece tree, every
piece-to-piece joint with type + clearance from `JOINT_FIT_MM`, the
assembly order, and the fit-check plan. Parts then follow the normal
per-part spec/script workflow, one component each (`<project>_<piece>`).

## 2. Interface contracts

- Each inter-piece joint is a row: joint type, clearance, the SHARED
  dimensions both scripts must use. Shared dimensions become identically
  named Fusion user parameters (one `param()` definition, same prefix,
  e.g. `asm_`) so both parts move together when a value changes.
- Locate with pin + slot, not four tight pins (joints_tolerances.md).
  Alignment features (chamfered pins, dovetails, tongue-and-groove) carry
  position; fasteners carry clamp — don't make screws do the locating.
- Every joint states its fastening: screws into inserts (repeated
  assembly), trapped nuts (high load), snap (light, serviceable), glue
  only when Jonathan approves a permanent bond.

## 3. Assembly ORDER — prove it on paper

Write the numbered order in _assembly.md and walk it: at each step, does
the next piece physically reach its place (swept path clear)? Is every
screw's driver axis clear IN THAT STATE (fasteners_inserts.md)? Do cables
get connected before their channel closes (cable_management.md)? An
assembly that only goes together in zero gravity with three hands is a
redesign. The classic failure: last lid screw hidden under the board that
went in at step 2.

## 4. Fit checks in Fusion — before ANY piece exports

All piece scripts rebuild into ONE document (each idempotent), placed by
their real transforms. Then a check script at
`models/<project>/_check_fit.py` (underscore = helper) that PRINTS:

- Interference analysis across every mating occurrence pair — expected
  contact only, zero unexpected overlap volume.
- Critical gaps measured (`measureManager.measureMinimumDistance`):
  each clearance in _assembly.md verified to be present, in the modelled
  pose AND at motion extremes for moving joints.
- Envelope per piece (its own print mode), bbox each.

Every unexplained interference or missing clearance is a coupling bug —
fix the parameter contract, don't nudge geometry locally. Worked examples
of the pattern: `legacy/models/robotarm/_check_*.py`.

## 5. Piece bookkeeping

- Piece = component = script = spec (or a row in _project.md for trivial
  pieces); print settings per piece (material, orientation, mode) live in
  _assembly.md and land in docs/<project>/README.md at close-out.
- Gauge the riskiest inter-piece joint first (a 2-piece corner sample),
  not after both full pieces are printed.
- Version pieces independently at export; _assembly.md records which
  versions are proven together.
