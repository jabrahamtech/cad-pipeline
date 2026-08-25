# Workflow 00 — Intake & triage (every request starts here)

Classify before acting; the wrong workflow wastes a session. This takes
one minute and is mostly silent — only step 4 talks to Jonathan.

## Steps

1. **Classify the request** (first match wins):

   | Request looks like | Go to |
   |---|---|
   | machine / mechanism / enclosure-with-guts / "build me a ..." (multi-piece) | workflows/02_assembly.md |
   | one printable piece (mount, bracket, jig, shim, gauge) | workflows/01_new_part.md |
   | change/fix an EXISTING part ("doesn't fit", "board changed", "tweak") | workflows/03_revision.md |
   | a printed part BROKE / wore / warped / loosened | workflows/05_failure.md |
   | print-result report ("28.7 fits snug"), new material, gauge results | workflows/04_calibration.md |
   | imported mesh (Meshy, scan) to make printable | 01 with the mesh-driver variant (CLAUDE.md imported-mesh rules) |
   | pure question / review / BOM / docs | answer directly, no workflow |

2. **COTS gate.** If the requested THING is a buyable component (bearing,
   thread, rail, gearbox — CLAUDE.md Standard components), stop and say
   so, naming the part. Only its HOUSING/interface continues to a
   workflow.

3. **Context sweep** (read, don't ask): existing `specs/<project>/`,
   `models/<project>/`, `docs/<project>/README.md`, open Fusion document
   (`fusion_mcp_read` document list), relevant `calibration/` entries.
   A returning project continues its assembly spec — never start a
   parallel one.

4. **One batched question round** if anything blocks the chosen workflow's
   step 1 (missing dimensions per knowledge/dimensioning.md, unclear
   duty/loads, material preference, private vs public placement).
   Batch EVERYTHING; don't drip. If unattended, proceed on explicit
   stated assumptions, all marked ASSUMED.

5. **Declare the plan**: one line — workflow chosen, project name, pieces
   expected, and where outputs will land. Then execute that workflow
   top to bottom.

## Exit criteria
A named workflow is running with its step 1 satisfied, or the request was
answered/redirected (COTS, question) with no geometry touched.
