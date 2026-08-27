# gripcut_finger — the flexure that holds the cutting

Decision 2026-08-27 (Jonathan): **separate flipped pair.** One flat part,
printed twice, the second flipped over — the same trick the blade carriers
use. Chosen over the gravity cradle and the finger-vs-other-nose anvil after
the packaging analysis in `gripcut.md`.

## Function

Leads the blade it rides by `lead` = 2.0 mm, touches the stem ~14° of blade
rotation early, and keeps 0.67–0.99 N of grip on the severed piece while the
blades finish. Sizing authority: `lib/gripcut_finger.py` (lead 2.0, t 1.2,
w 6.0, L ≈ 29 folded, strain ≤ 1.0 %).

## The topology that survived — above-stack couple grip

The straddling face (z −3.0…+3.0, the only band the `(x,y,z)→(−x,y,−z)`
copy maps onto itself) was the FIRST design, and `_check_gripcut`'s
deflected-pose sweep killed it, then its two repairs:

1. The straddling face collides with the other carrier's Ø12 hub disc, and
   its below-plane half fights the blade bodies, which sweep the ±3.55 band
   during closure. The space is spoken for.
2. Clipping the hub left the deflection fault: the stem pushes the finger
   back toward its OWN blade — 0.1 mm of room against 4.5 mm of travel.
3. So the face lives **entirely above the blade stack, z 3.65…9.55** (0.1 mm
   air over the carrier top), where deflection sweeps over the nose tops
   through open sky.

**The grip is a couple on one carrier**: the finger presses the piece
sideways from above the stack, and the piece's lower end leans on the
carrier's own nose edge face below — two opposed contacts, offset in z,
riding the same blade, exactly how real cut-and-hold secateurs hold. The
flipped copy grips the stump side the same way, harmlessly; opening the
head releases both. On empty close the two fingers **bypass** — disjoint z
bands, like the blades; nothing meets, nothing needs a stop. Only a stem
loads the leaf.

The grip face corner stays inside the throat crossing radius (r 6.48…8.34
< 8.5) so the couple lands over the throat, where the nose edge below can
take the counter-contact. Asserted in the script.

Swept in `robotarm_gripcut_gate` (2026-08-27): finger^blade 0.00 and
finger^finger 0.00 at every pose, deflected and empty, θ 0…24.3°; the
deflected poses peak at 4.50 mm of the 4.7 mm budget; the boss's rigid-pose
anchor shear is bucketed and capped at the boss volume. GATE PASS.

## Interfaces

| interface | joint | value |
|---|---|---|
| pivot bore | on the existing M3 pivot screw, clearance | Ø3.2 (`FASTENER_MM`) |
| carrier outer face | rests on z 3.55 | flat |
| key boss → carrier pocket | locational 0.20 | boss 4.0 × 3.0 × 1.4 at (0, −8) |
| grip face | works the stem | plane x = 1.5 (= `edge_off` − `lead`) |

The key pocket is the **one extra feature per carrier** — a revision to
`pruner_blade.py`, cut into the outer face where 2.1 mm of wall remains.

## Print

Top face down (z +9.55 on the bed): ring, key tab, leaf and grip flag all
start at the bed — no cantilever, no support. Layers lie along the leaf —
bending stress in-plane, the flexure's one hard rule. PETG, same spool as
everything.

## ASSUMED / open

Leaf force from the folded path is taken as the solver's straight-beam L —
approximate; the flexure coupon on the next gauge plate calibrates it. Strain
limit 1.0 % and µ 0.4 are HANDBOOK. Shell clearance above the leaf (z to
9.55) is checked by sweep, not by arithmetic.
