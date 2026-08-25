---
name: plan-assembly
description: Decompose a complex model (machine, mechanism, enclosure with electronics, anything multi-piece) into printable pieces with joint contracts, assembly order, and a fit-check plan — BEFORE any part is modelled. Use whenever the user asks for a device, product, robot, mechanism, or any model that won't be one printed piece.
---

# Plan assembly workflow

**Order of record: `workflows/02_assembly.md`** — this skill is the
trigger and summary; on step order and gates, the workflow file wins.

Read `knowledge/assembly_decomposition.md` first — this skill is its
executable form. The failure it prevents: modeling a monolith (or pieces
with no interface contract) and discovering at print time that it doesn't
fit the envelope, can't be assembled, or binds.

## 1. Decompose
Split at natural interfaces for a stated reason per split: envelope,
layer-orientation conflict, support elimination, material mix, service
access, iteration cost. Each piece = one component `<project>_<piece>` =
one script = one spec.

## 2. Contract the interfaces
Create `specs/<project>/_assembly.md` from `specs/_assembly_template.md`:
- piece tree with print mode / material / orientation per piece
- every piece-to-piece joint: type + clearance from `JOINT_FIT_MM`
  (knowledge/joints_tolerances.md), fastening, and the SHARED dimensions —
  which become identically named user parameters used by both scripts
- locate with pin + slot, never four tight pins; fasteners clamp, they
  don't locate

## 3. Walk the assembly order
Number the steps. At each: insertion path clear, every fastener's driver
axis reachable IN THAT STATE (knowledge/fasteners_inserts.md), cables
connected before their channel closes (knowledge/cable_management.md).
Fix the design, not the instructions, when a step needs three hands.

## 4. Gauge the riskiest joint first
Before any full piece prints, extract the riskiest inter-piece joint into
a 10–20 minute two-piece sample. Record the result in `calibration/`.

## 5. Then build parts normally
Each piece goes through the new-part skill (spec → script → verify). When
all pieces rebuild in one document, write
`models/<project>/_check_fit.py`: interference across every mating pair,
every contracted clearance measured (at motion extremes for moving
joints), per-piece envelope — zero unexpected interference before ANY
piece exports. `tests/` enforces that multi-part projects carry an
_assembly.md.
