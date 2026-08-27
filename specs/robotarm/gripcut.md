# gripcut — the finger that holds the cutting

Status: **SOLVED, NOT BUILT.** `lib/gripcut_finger.py` is the authority;
this file is its reasoning. Nothing is modelled yet.

Jonathan asked for a "gripper/cutter". The built head (`pruner.md`) is a
bypass shear that only cuts, so the severed piece drops on the floor. This
is the addition that holds it.

## The constraint that shapes everything

The servo inventory is **exactly used** — 1 × MG995, 2 × MG90S, 3 × SG90, no
spare. Grip and cut must therefore come off **one** SG90 that is already
fully committed to driving the blades, with no travel to spare: the blades
use 21.8 mm of a 21.8 mm rack stroke.

That rules out any sequenced mechanism with its own input — no second servo,
no lost-motion slot stealing stroke, no cam with a dwell. What is left is a
finger that **rides the blade it is bolted to**, leads it, and is compliant
enough to keep holding while the blade travels the rest of the way.

## The finger is the blade equation with a smaller number

`pruner_linkage`'s blades are two lines each offset `a` = 3.5 from a common
pivot, so their gap at radius r and blade angle θ is

    gap(r, θ) = 2 (a − r sin θ) / cos θ

A finger bolted to the same carrier at a **smaller** offset `a − lead` is
that same equation with a smaller numerator. It therefore closes on any
given stem earlier, by exactly the lead, **and needs no separate linkage at
all**. No new pivot, no new pin, no new slot. One extra feature per carrier.

The finger sits offset in **+Z**, above the cutting plane, so it grips the
length of stem that is about to become the cutting rather than the stump.
The blades are already offset in Z to bypass each other, so this Z structure
exists.

## Why a printed flexure and not a spring

There are no springs in the inventory. Adding one means a BOM line, a
retention feature, and a part that can fall out inside a moving head. A PETG
cantilever costs nothing, cannot escape, and is sized rather than guessed.
The trade is fatigue, and the strain limit is what buys it.

**It must be printed with its layers running along the leaf**, so bending
stress is in-plane. Across layers this is a fatigue crack waiting to happen.

## Chosen

| | |
|---|---|
| lead | **2.0 mm** |
| leaf thickness | **1.2 mm** |
| leaf width | 6.0 mm |
| leaf length | **29.1 mm**, folded |
| grip force | 0.67 N on a 2 mm stem → 0.99 N on a 5 mm |
| strain at full deflection | 1.0 % — the design limit |

**A 20 g cutting at µ 0.4 needs 0.25 N per finger.** Every candidate cleared
that by 2.5–6×, which is why force is not what picks the winner.

## What picks the winner: the finger fights the blade

Both push on the same stem at the same radius, so the flexure force
**subtracts directly** from the cutting force — it is not a second-order
loss. That is the constraint that makes the solver worth running; without it
every row passes and the tool tells you nothing.

| | stem capacity at the throat |
|---|---|
| bare blades | 6.3 mm |
| **with the chosen finger** | **5.9 mm (−6 %)** |
| with a 2.0 mm leaf | 5.4 mm (−14 %) |

A thicker leaf is worse twice over — more force stolen, *and* a longer leaf
to keep the strain down. That is why the choice went the other way, to 1.2.

**1.2 mm is below `design_rules.MIN_WALL_MM` of 1.6, deliberately.** That
rule is about structure; this is a flexure. At a 0.4 nozzle it is still three
full extrusions wide. Recorded here as a departure, with its reason, the way
`pruner.md` records the 0.7 × stall derate.

## What it costs the arm

**1.0 g for the pair.** They are thin leaves, not a mechanism — the budget
set aside 16.7 g and the design needs a sixteenth of it.

Head: 38.3 g as shipped → 34.2 g once the density error in `_assembly.md` is
corrected → **35.2 g with the fingers**. At L1 65 / L2 45 that puts J3 at
**61 %** with the current links and **69 %** at four times the link section.
The arm sits at 80 % today.

## Sequence, at lead 2.0 on a 5 mm stem

1. Fingers touch the stem **14.2° of blade rotation early** — over a third of
   the 40° sweep. The stem is held before the edges arrive.
2. Blades close; flexures deflect 4.69 mm each; grip force climbs to 0.99 N,
   firmest exactly when the cut happens.
3. Cut completes. Grip holds. The cutting stays in the head.
4. Arm moves; head opens; the cutting is released where you want it.

## THE PACKAGING PROBLEM — found 2026-08-27, blocks the CAD

The solver sized the leaf in one dimension and it is right. Taking it to 3D
exposes a topology conflict the spec never resolved, and it is why the CAD
stops here pending a decision.

**The two carriers are ONE design, TWO copies, the second turned over**
(`(x,y,z) → (−x,y,−z)`). Any finger feature not symmetric about the cutting
plane therefore lands on OPPOSITE sides of it on the two blades: blade A's
finger sits above the plane, blade B's below. The two grip faces never share
a z band — and after the cut, the severed piece (entirely on one side of the
plane) is touched by ONE finger pressing against nothing. It falls, which is
the exact failure the finger exists to prevent.

Every escape runs into another wall:

- **Grip faces symmetric about the plane** (band z ±3, which is exactly the
  6.0 leaf width — probably what the solver imagined): identical parts work,
  the fingers meet face-to-face on empty close and simply deflect each other
  (2.2 mm, within budget). But the tip then hangs 3 mm BELOW the carrier's
  inner face, which is the print bed. Unprintable flat; the no-support
  orientation dies.
- **Handed integrated fingers, both above the plane**: blade B's finger must
  rise from below its inner face — same unprintable overhang, plus the
  identical-pair contract breaks.
- **Separate finger parts, flipped for the second copy**: flipping a flat
  part mirrors it in z, so the tips land on opposite sides again. Both tips
  above the plane requires a genuinely handed PAIR, and blade B's needs a
  riser column climbing from its outer face (z −3.55) past the whole carrier
  stack, dodging blade A's ±80° relative sweep AND the shell walls.
- **Single flexure against the OTHER blade's nose as anvil**: attractive —
  the other nose is rigid and exactly where the cutting is — but on empty
  close the finger face crosses the closing EDGE's path. A flexure that
  presses toward an arriving steel edge gets cut on every empty cycle unless
  the landing zone is proven to stay behind the flat. Needs its own sweep
  gate before it is credible.

## Not yet answered

- **Release.** The head must open to drop the cutting, which it does — but
  nothing has checked the cutting will not wedge in the throat.
- **The strain limit is HANDBOOK.** 1.0 % is the usual cyclic-flexure
  allowance for PETG; it has never been gauged on this spool. A flexure
  coupon belongs on the next gauge plate.
- **µ = 0.4** for printed PETG against a green stem is a guess. Serrating the
  tips would help and has not been sized.
- Fatigue life is unquantified. At one cut per operation this is thousands of
  cycles, not millions, which is the only reason it is not the top risk.
