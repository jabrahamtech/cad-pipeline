# robotarm — design language

Status: ACTIVE. Applies to **every** piece in the project. A part that
ignores this is a revision, not a style preference.

Reference: Jonathan's photo of a 5-DOF desktop arm — light faceted body,
dark joints, thick chamfered volumes. The look is industrial-robot, not
consumer-product: **cut planes, not soft radii.**

## The six rules

**1. Facets, not fillets — `sty_facet` = 4.0 mm at 45°.**
Every outer edge that is not a mating, sliding or bed face gets a 4 mm
chamfer. This is the single biggest lever and it is nearly free: on a 48 mm
wide part a 4 mm bevel reads as a deliberate cut plane from across the room,
where a 1 mm one reads as a deburr. Functional faces keep the 0.4 mm
elephant-foot chamfer instead (`sty_ef`) — a mating face must stay flat.

**The facet scales with the volume it bevels**: `sty_facet × h / h_primary`.
A 4 mm cut on a 16 mm block is a quarter of its height and reads as
intended; the same 4 mm on a 10 mm block eats it, and Fusion often refuses
to compute it at all. Keep the ratio, not the number.

**2. Corners are `sty_radius` = 6.0 mm in plan.**
No square vertical corner anywhere on an outside surface. Applied as a
fillet on the vertical edges of the outer form, BEFORE any internal cut —
fewer edges, cleaner selection, and the fillet never catches a pocket.

**The radius must EXCEED the facet.** A 4 mm chamfer running into a 4 mm
corner radius does not just look wrong, it fails to compute: Fusion returns
`ASM_BL_CAP_COMPLEX — the fillet/chamfer could not be created at the
requested size`. 6 mm against 4 mm is the ratio this project uses; keep at
least 1.5×.

**3. Volumes taper into their joints.**
A link is widest at mid-span and narrows to 0.75–0.8 × that where it meets
the next piece. A part that is the same width end to end reads as stock, not
as a designed object. The taper is also where the mass should come off.

**4. The split line is a feature, not an accident.**
Where a piece is a mirrored pair, the parting plane is the widest line of
the form and both halves bevel away from it. The assembled piece then reads
as one faceted volume with a crisp centre line — the same trick that makes
the reference arm's links look machined rather than glued.

**4b. Lobed flanges, not plain discs — `turntable_ring` has 12.**
The reference arm's base flange is a cog, and it is the single most
recognisable thing in the photo. The lobe count MUST divide into the fixing
pattern: the three M3 posts sit at az 120/180/240, so the spacing has to
divide 60° — 12 works, 6 works and reads coarse, 9 does not contain 180.
Every fixing lands on a lobe, never in a notch, and `turntable_ring.py`
asserts it rather than trusting the arithmetic.

**EXCEPTION — a flange that is a JOURNAL stays round.** `wr_flange_d` (Ø24 on
both hubs) runs inside a Ø24.35 counterbore as a rotating fit — `fa_cbore_d`
is literally `wr_flange_d + rotating 0.35`. Lobe it and a 0.35 mm running
surface becomes a few points of contact. Those two flanges are also completely
buried, so there is nothing to gain. **The rule is about flanges you can see.**

**And where the fixing pattern is not rotationally symmetric, the notches go
in the GAPS.** `wrist_rotator`'s four inserts sit on a rectangle — ±11.0 by
±9.0, az 39.29 / 140.71 / 219.29 / 320.71 — so the gaps alternate 101.42° and
78.58° and *no* uniform lobe count lands on all four. Putting four notches at
0/90/180/270 puts every insert on a lobe by construction instead. Eight was
tried and fails: a notch at az 45 sits 5.71° from the insert at 39.29 and
breaks into its boss. The assertion in `wrist_rotator.py` is what caught it.

**5. Two-tone by PART, never by added panels.**
`sty_light` (mustard/cream) for bodies and links; `sty_dark` (charcoal) for
drums, servo bays, the base and anything that reads as a joint. The X2D's
second nozzle does it in one print. Cosmetic skins over a structural core
were considered and rejected: they are truer to the photo but put 8–12 g at
the end of the arm, and the elbow MG90S is already at 91 % of its duty
limit (see `_assembly.md`). **The styling may not cost payload.**

**6. Round forms are 12-gons — `lib/facets.py`.** (2026-09-29)
Jonathan: *"I like arms that are more circular with poliagonal lines for
texture."* The base platter, the turret and the grip head were already
12-sided; every other round form you can see follows: the drums at the ends
of `upper_arm`, the forearm's link outline and bosses (`forearm`,
`forearm_px`, `forearm_nx`, `forearm_rail`), the upper arm's side panels,
`shoulder_bracket`'s two pivot bosses and the `wrist_rotator` disc.
Where a boss runs tangent into a straight column (the bracket cheeks) or a
notch has to land mid-flat (the rotator's scallops), turn the grid 15° so a
FLAT sits on the axis (`FLAT_ON_AXIS_DEG`).
Servo housings stay boxy (`wrist_roll`, the forearm lobes, `j3_servo_cap`):
they are shaped by a rectangular servo and every wall is already at MIN_WALL.
A vertex sits on the local +axis and every 30° from it, so it lines up with
the hex sockets (every 60°). Pick which side of the circle the polygon sits:
- **inside** (vertices on the circle) where a running clearance is cut round
  it — `ua_drum_r` against `fa_elbow_clear`
- **outside** (flats on the circle) where a wall is measured to it —
  `fa_boss_r` against the counterbore and the 608 pocket
The same exception as 4b: bores, journals, counterbores and anything that
turns in something else stay round.

## Shared parameters

Defined identically in every script that uses them.

| Parameter | Value | Meaning |
|---|---|---|
| `sty_facet` | 4.0 mm | 45° chamfer on outer edges |
| `sty_radius` | 6.0 mm | plan-view corner radius — must exceed `sty_facet` |
| `sty_ef` | 0.4 mm | elephant-foot chamfer, functional faces — design_rules |
| `sty_gap` | 1.2 mm | shadow line where a light part meets a dark one |

## Applying it — the order that works

1. Build the **outer form first**, as one shaped solid: plan polygon →
   extrude → fillet the vertical edges (`sty_radius`) → chamfer the top
   perimeter (`sty_facet`).
2. **Then** cut the internals into it.
3. Finish with `sty_ef` on the bed/mating faces only.

Doing it the other way round — cutting the mechanism first and chamfering
afterwards — means the chamfer selection catches every pocket edge, and the
result is a slab with rounded holes rather than a shaped object.

## What this does NOT license

Styling that eats structure. Every facet still has to leave `MIN_WALL_MM`
behind it, every taper still has to clear the mechanism at its motion
extremes, and `_check_fit.py` is still the gate. If a facet would thin a
wall below 1.6 mm, the FORM grows to make room — the facet does not shrink.
