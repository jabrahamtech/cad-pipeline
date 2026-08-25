# DFM & optimization — print time, mass, cost, and surfaces that look bought

Read when: a part is slow, heavy, ugly, or wasteful; before committing any
print > 3 hours; when the request says "make it nicer / lighter / faster".

## What actually drives print time (attack in this order)

1. **Height in the print orientation** — layers are serial. A part printed
   lying down at 40 mm beats the same part standing at 180 mm by hours.
   Orientation is strength-first (loads_strength.md), but between equal
   orientations, pick the shorter.
2. **Support volume** — the aux nozzle makes support CHEAP but not free
   (time + the dual envelope). A 45° chamfer under a boss deletes its
   support for zero cost; design self-supporting where it's free
   (CLAUDE.md rule), spend support where geometry earns it.
3. **Solid mass** — walls & infill (below).
4. **Travel/detail** — many tiny islands per layer (perforated patterns,
   fine text everywhere) slow disproportionately. Batch cosmetics onto one
   face.

## Mass & infill discipline

- INFILL_DEFAULT (design_rules): cosmetic 15% · functional 25% ·
  structural 40% + 4 walls. State infill in every export summary.
- Lightening that works: pockets in low-stress zones (keep flanges &
  load paths — loads_strength.md tells you which is which), thinner
  DEEP sections rather than thinner walls, holes at the neutral axis.
- Lightening that doesn't: dropping perimeters on structural parts;
  lattice-for-the-look; sub-1.6 walls anywhere (MIN_WALL is a floor).
- Mass targets go IN THE SPEC when they matter (drones: the mini3 frame
  budget pattern — model volume × density vs budget, printed as a
  diagnostic).

## Part count & consolidation

- Consolidate when: pieces share an orientation and material, the joint
  between them exists only because "that's how it'd be machined", or the
  assembly step adds fasteners with no service value. Printing does
  compound curves and internal ribs for free — use it.
- Do NOT consolidate across: different best orientations, wear parts
  (keep them replaceable — motion_mechanisms.md), iteration hot spots
  (the piece still being tuned stays separate until ACCEPTED), envelope.
- The tie-breaker is iteration cost: a consolidated 8-hour part that's
  wrong twice costs more than 5 fasteners ever will.

## Surface & appearance (functional parts can still look bought)

- **Face assignment first:** decide the SHOW faces before orientation is
  final — top surfaces (ironed) and vertical walls look best; the support
  side and first layer are the back. Put the logo where the printer is
  good, not where CAD is convenient.
- Chamfers > fillets on top/bottom edges (a bottom fillet is a support
  or elephant-foot magnet; 45° chamfers print clean). Vertical-edge
  fillets are free — use them everywhere for the injection-molded look.
- Uniform wall impression: consistent 2.0–2.4 walls with ribs hidden
  inside read as "product"; lumpy solid blobs read as "printed".
- Text: emboss/deboss ≥ MIN_EMBOSS on show faces per enclosure notes;
  recessed text survives handling better than proud text.
- Seam: note "seam to rear edge" in the print plan for cylindrical show
  parts; a designed seam groove (0.4 × 0.4 V) makes it invisible.

## Cost & batch sanity

- Filament cost ≈ volume × density × ~$25/kg — print cost is almost
  always TIME and FAILURE RISK, not grams. The expensive print is the
  6-hour one that fails at hour 5: split risk out (gauge the risky
  interface first — the standing rule), and prefer two 2-hour pieces
  over one 5-hour piece when a joint is cheap.
- Plate batching: parts wanted in multiples (feet, clips, spacers) get a
  small-N test print first, then batch; one bad parameter × 20 copies is
  the classic waste.
- Reprint economics beat repair: design consumable/wear pieces cheap and
  fast (< 30 min) so replacing them is the maintenance plan.
