# Workflow 02 — Assembly (anything that isn't one printed piece)

Entry: routed by 00_intake for machines, mechanisms, enclosures with
guts. Skill `plan-assembly` is the trigger; THIS file is the order.
Knowledge core: assembly_decomposition.md · motion_mechanisms.md ·
tolerance_stackup.md.

## Phase A — architecture (no geometry allowed yet)

1. **Function & DOF** — write what the assembly does; count needed
   degrees of freedom; every actuated joint listed
   (motion_mechanisms.md). For each: duty (cycles/day) and load class.
   *Gate: DOF count = joint count; no "we'll see" joints.*

2. **Torque/load budget** — the table from motion_mechanisms.md for every
   actuator (worst pose, arm, mass incl. downstream, T_req vs T_avail
   derated). Structural members get the loads_strength.md load-path
   paragraph.
   *Gate: every margin ≥ 1, or the design changes NOW (shorter arms,
   counterweight, bigger servo) — not after printing.*

3. **Decompose** — piece tree with a stated reason per split (envelope /
   orientation / support / material / service / iteration). COTS pass:
   everything buyable named with source (bearings, fasteners, servos,
   belts).
   *Gate: each piece fits its envelope mode; each piece has ONE best
   print orientation serving its loads.*

4. **Contract the interfaces** — `specs/<project>/_assembly.md` from the
   template: joint table (type + clearance from JOINT_FIT_MM, fastening,
   shared `asm_` parameters), stack-up lines for every alignment crossing
   ≥ 3 dims (tolerance_stackup.md — loop, WC/RSS, fix applied), cable
   plan (cable_management.md — route through moving joints along axes).
   *Gate: every piece-to-piece contact has a row; every row's clearance
   traces to design_rules; stack-ups pass both directions.*

5. **Walk the assembly order** — numbered; per step: insertion path,
   driver access in THAT state, cables before channels close, end stops
   reachable. Fix the design where the walk fails.
   *Gate: complete walked order written in _assembly.md.*

## Phase B — build (iterate pieces, riskiest first)

6. **Gauge the riskiest joint** — two-piece sample of the scariest
   contract (uncalibrated fit, tightest stack) exported and printed
   BEFORE any full piece. Result → 04_calibration → update the contract.

7. **Per-piece loop** — run workflows/01_new_part.md for each piece,
   riskiest/most-coupled first; all scripts rebuild into ONE document;
   shared dims ONLY via the `asm_` parameters (defining them identically
   is part of each script's step 4).

8. **Fit check** — `models/<project>/_check_fit.py` prints: interference
   for every mating pair (expected contact only), every contracted
   clearance measured present — at motion extremes and worst mid-pose for
   moving joints (sweep per motion_mechanisms.md), per-piece envelope.
   *Gate: zero unexpected interference, zero missing clearance —
   BEFORE any piece exports. A coupling bug is fixed in the parameter
   contract, never by nudging one piece.*

9. **Export set** — pieces via 01 step 9; _assembly.md's proven-together
   table records the version set.

## Phase C — integrate

10. **Print plan** — per-piece order that lets assembly start early
    (gauges → small coupled pieces → long prints); materials & plates per
    materials.md.

11. **Docs** — `docs/<project>/README.md`: piece table (version, material,
    orientation), full BOM with sources, assembly order (from step 5,
    now proven), cable/label notes.

12. **After physical assembly** — measured deviations, slop at the tip
    (motion_mechanisms.md stack), torque reality vs budget → 
    04_calibration entries; failures → 05_failure. _assembly.md Status
    advances DRAFT → CONTRACTED (after 4) → FIT-CHECKED (after 8) →
    ASSEMBLED.

## Exit criteria
Version-consistent export set, clean _check_fit output on record, docs
README complete, and the next physical step (what to print first) stated.
