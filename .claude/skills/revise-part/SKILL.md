---
name: revise-part
description: Change an existing part safely through the Fusion MCP — parameter-only edits with a before/after diagnostics diff. Use when the user reports a dimension change, board revision, fit problem, or asks to tweak an existing model.
---

# Revise part workflow (Fusion MCP)

**Order of record: `workflows/03_revision.md`** — this skill is the
trigger and summary; on step order and gates, the workflow file wins.
Broken/worn parts route to `workflows/05_failure.md` instead.

The failure mode this prevents: regenerating from scratch and silently
drifting dimensions that were correct (eval S6).

## 1. Capture BEFORE
Re-run the part's script from `models/<project>/<part>.py` (idempotent, so
this is safe) and record its printed diagnostics: volume, bbox, body count,
plus the positions of interface features (holes, bosses) from the spec —
measured via a read-only script if needed.

## 2. Change parameters, not geometry
- A dimension change should be a user-parameter expression change in the
  script — if it requires rewriting geometry code, the model wasn't
  parametric enough: fix that first, re-run, verify identical diagnostics,
  THEN change the value.
- Touch only the parameters the revision names. Update the spec's
  Interfaces table in the same edit.
- Recover from a half-worked run with `fusion_mcp_update` undo + re-run,
  never with a corrective follow-up script.

## 3. Diff AFTER against BEFORE
Re-run, diff diagnostics. Every delta must be explained by the requested
change; an unexplained delta means a coupling bug — stop and fix it.
State the diff in the summary ("bbox X +5 mm as expected; volume +4.1 cm³;
all hole positions relative to board edge unchanged").

## 4. Gate and version
1. Commit the updated script; `.venv/bin/pytest tests/ -q` must pass.
2. Export as `_v{n+1}` (fusion/templates/export_part.py) — never overwrite
   a version that may have been printed. Note in `docs/<project>/README.md`
   which version is current.

## Fit problems specifically
If the revision is "it doesn't fit": suspect ASSUMED user parameters first
(they carry an ASSUMED comment in the script and spec), then clearance
rules. If a calibrated clearance in `lib/design_rules.py` is wrong, that's
a calibration event — measure, update the rule with the user's
confirmation, and record it in `calibration/`.
