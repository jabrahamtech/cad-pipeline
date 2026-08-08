---
name: revise-part
description: Change an existing part safely — parameter-only edits with a before/after diagnostics diff. Use when the user reports a dimension change, board revision, fit problem, or asks to tweak an existing model.
---

# Revise part workflow

The failure mode this prevents: regenerating from scratch and silently
drifting dimensions that were correct (eval S6).

## 1. Capture BEFORE
Build the current model and record diagnostics: volume, bbox, solid count,
and the positions of interface features (holes, bosses) from the spec.

## 2. Change parameters, not geometry
- A dimension change should be a parameter default change (or call-site
  value) — if it requires rewriting geometry code, the model wasn't
  parametric enough: fix that first, verify identical output, THEN change
  the value.
- Touch only the parameters the revision names. Update the spec's
  Interfaces table in the same edit.

## 3. Diff AFTER against BEFORE
Rebuild, diff diagnostics. Every delta must be explained by the requested
change; an unexplained delta means a coupling bug — stop and fix it.
State the diff in the summary ("bbox X +5 mm as expected; volume +4.1 cm³;
all hole positions relative to board edge unchanged").

## 4. Gate and version
1. `.venv/bin/pytest tests/ -v` must pass.
2. Export as `_v{n+1}` — never overwrite a version that may have been
   printed. Note in `docs/<project>/README.md` which version is current.

## Fit problems specifically
If the revision is "it doesn't fit": suspect ASSUMED spec values first,
then clearance rules. If a calibrated clearance in `lib/design_rules.py`
is wrong, that's a calibration event — measure, update the rule with the
user's confirmation, and record it in `calibration/`.
