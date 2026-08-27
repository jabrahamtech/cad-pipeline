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

## The topology that survives the turn-over

The grip face straddles the cutting plane symmetrically — **z −3.0…+3.0
global** — because that is the only band the `(x,y,z)→(−x,y,−z)` copy maps
onto itself. Consequences, all accepted:

- On empty close the two faces meet at the centreline and deflect each other
  ~2.1 mm each. Within the 4.7 mm budget; no stop needed.
- After the cut the faces pinch the cutting AND the stump. Release is a
  perpendicular pull: the stump (a stiff cantilever off the plant) levers out
  of a ~1 N grip; the severed piece has no anchor and stays held.
- The tip must stay **inside the crossing radius** (face span r 6.6…8.35
  < throat 8.5), because beyond it the other carrier's nose crosses the
  centreline at closure and would strike the below-plane half of the tip.
  Asserted in the script.

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

Top face down (z +9.55 on the bed): ring, leaf and riser all start at the
bed; the face slab's 4.3 mm reach off the riser carries a 45° gusset on its
print-underside. Layers lie along the leaf — bending stress in-plane, the
flexure's one hard rule. PETG, same spool as everything.

## ASSUMED / open

Leaf force from the folded path is taken as the solver's straight-beam L —
approximate; the flexure coupon on the next gauge plate calibrates it. Strain
limit 1.0 % and µ 0.4 are HANDBOOK. Shell clearance above the leaf (z to
9.55) is checked by sweep, not by arithmetic.
