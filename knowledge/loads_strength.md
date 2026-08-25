# Loads & strength — sizing FDM parts that don't break

Read when: the part carries load, transmits torque, gets dropped, or
cantilevers anything. Numbers: `lib/design_rules.py` (Z_TENSILE_FACTOR,
SAFETY_FACTOR, MIN_FILLET_LOADED_MM — HANDBOOK).

## The anisotropy law (everything follows from this)

An FDM part is a laminate: **~100% strength within layers, ~50% across
them** (Z_TENSILE_FACTOR = 0.5; brittle failure, no yield warning).
Consequences, in order of importance:

1. Orient so tension and bending stress run WITHIN layers. If two load
   paths disagree, split the part (assembly_decomposition.md) — that's a
   legitimate split reason.
2. A load that MUST cross layers gets: 2× the section, a through-bolt
   bypassing the plastic, or a redesign. Never just "more infill".
3. Screws in pull-out along Z are the classic hidden violation
   (fasteners_inserts.md).

## Reason about load paths before geometry

For each external force, trace: entry point → structure → reaction point.
At each section ask what it carries — tension, compression, bending,
shear, or torsion:

- **Bending dominates printed failures.** Stress ∝ M·c/I: doubling depth
  (in the bending plane) is 4× stiffer and ~4× stronger; doubling width is
  only 2×. Put material FAR from the neutral axis: two flanges + web (I/C
  sections, box sections) beat solid rectangles at half the mass.
- **Cantilevers:** moment = force × arm. Halve the arm before adding any
  plastic. Support the free end if the design allows (a strut is worth
  10× its mass in wall thickening).
- **Torsion:** closed sections only — an open C-section in torsion is a
  spring. Close the box, even with a screwed-on lid that bridges it.
- **Compression/buckling:** slender printed columns buckle before they
  crush; keep unbraced length < 10× the smallest section dimension or add
  a rib.

## Local design rules

- **Fillet every loaded junction:** ≥ 2 mm radius (MIN_FILLET_LOADED_MM)
  at rib roots, boss roots, arm-to-hub transitions. A sharp internal
  corner is a crack starter with a ~2–3× stress concentration — on the
  layer-adhesion axis it's where the part WILL split.
- **Ribs and gussets before thickness:** a 45° gusset pair at a joint
  outperforms doubling wall mass. Rib thickness ≈ wall thickness; rib
  height ≤ 5× thickness before it needs its own support or a flange.
- **Holes in stressed zones:** keep 2× hole Ø of material around any hole;
  never place a hole at the max-bending fiber (move it to the neutral
  axis side).
- **Infill is not strength strategy:** walls carry the load. For
  structural parts: 4+ perimeters, then 25–40% infill
  (INFILL_DEFAULT["structural"]). Adding infill beyond 50% buys grams,
  not much strength.

## Time-dependent failure (the sneaky ones)

- **Creep:** PLA under sustained load (clamps, preloaded brackets, spring
  arms) relaxes in days–weeks, faster when warm. Anything loaded 24/7 →
  PETG minimum, ABS/ASA/PA better; or design so a steel screw/bolt holds
  the preload, plastic only locates.
- **Fatigue:** cyclic joints (gears, snap arms used daily, linkage pins)
  fail at ~30–50% of static strength after 10⁴–10⁵ cycles. Use
  SAFETY_FACTOR["cyclic"] = 4 on cyclic members and put steel at pivots.
- **Impact:** PLA shatters; PETG bends; ABS/ASA absorb. Drop-prone or
  crash-prone (drones) → SAFETY_FACTOR["impact"] = 5 and a ductile
  material; design a sacrificial fuse part where crash energy goes
  (cheap reprintable arm tip, not the core frame).

## Safety factors (HANDBOOK — on estimated loads)

static 2.0 · cyclic 4.0 · impact 5.0 · anything a person's weight or
safety rides on 6.0 — and say in the summary WHICH load estimate the
factor was applied to. When the load is unknown, state the assumed load
in the spec (Loads section) — an ASSUMED load is flagged exactly like an
ASSUMED dimension.

## Verifying without FEA

No FEA in this loop — use it honestly: estimate the worst-case moment,
compute the section at the weakest point from the model (script-measure
the real cross-section), apply σ = M·c/I against ~35 MPa (PLA/PETG
in-plane) × 0.5 if across layers ÷ safety factor. One paragraph of this
arithmetic in the summary beats "made it chunky". When the number is
marginal → physical test plan: print, clamp, load with known weights to
failure, record in calibration/ (that's a strength calibration, same loop
as fits).
