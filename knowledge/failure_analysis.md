# Failure analysis — turning broken parts into better rules

Read when: a printed part broke, wore, warped, crept, or came loose — in
testing or in service. The point: identify the MODE first; the fix
follows from the mode, and the lesson lands in a rule file so the system
never pays for it twice. (Fit problems that are about dimensions, not
damage → revise-part flow / joints_tolerances.md instead.)

## Step 1 — read the fracture (ask for a photo of the broken faces)

| What you see | Mode | It means |
|---|---|---|
| Clean split ALONG a layer plane, glassy faces | layer-adhesion tension/peel | load crossed layers — orientation or design wrong, not "weak filament" |
| Break across layers, rough/whitened faces | in-plane overload | genuinely under-sized section — do the loads_strength.md arithmetic |
| Crack STARTING at a corner, hole, or rib root | stress concentration | missing fillet (MIN_FILLET_LOADED_MM) or a hole in the wrong fiber |
| Slow bend that stayed bent, no crack | creep | sustained load on PLA (or warm PETG) — materials.md |
| Broke after weeks of working fine, small cycles | fatigue | cyclic member without the ×4 factor; steel belongs at that pivot |
| Shattered on impact, many fragments | brittle impact | PLA in a drop/crash role — ductile material + sacrificial fuse part |
| Boss cracked around an insert | hoop stress | insert hole undersized / boss wall < 2.4 / insert set crooked |
| Thread stripped, screw spins | pull-out | screw in Z pull-out, or pilot too big, or torque spec ignored |
| Mating surfaces powdered/grooved | wear/galling | printed-on-printed service motion — motion_mechanisms.md friction rules |
| Part warped off the plate / banana'd later | residual stress | material shrink (ABS/PA without chamber discipline) or annealing by environment |
| Loose over time, no damage | preload loss | plastic in the clamp path relaxing — put steel in the bolt path |

## Step 2 — locate it in the model

Reproduce the failure location in Fusion: script-measure the section at
the break (area, I, distance to the load), recompute the stress with the
REAL load if now known. State whether the arithmetic predicted it —
if it didn't, the load model was wrong (record the corrected load in the
spec), if it did, the safety factor was ignored (record that too).

## Step 3 — fix by mode, not by instinct

The reflex "make it thicker" is correct only for in-plane overload.
Otherwise: layer split → reorient or split the part; concentration →
fillet/relocate the hole; creep → material or steel preload path;
fatigue → steel pivot / bigger factor; impact → ductile material +
crumple part; insert/boss → FASTENER_MM numbers; wear → bearing/bushing.
One mode, one fix, re-run the design review lines that mode touches.

## Step 4 — feed the system (mandatory, same commit as the fix)

- `calibration/YYYY-MM-DD-<project>-<part>-failure.md`: photo note, mode,
  load estimate, section numbers, fix applied.
- If a HANDBOOK value was implicated → correct it and promote/adjust with
  the measured evidence.
- If a knowledge/ rule was missing or wrong → edit that file NOW (that's
  how this file grows teeth).
- Spec of the part: Loads section updated with the real-world load; Status
  back to MODELED until the reprint passes.
- If the same mode appears twice across projects → propose a design_rules
  constant or a lint check so it can't recur silently.

## Chronic-failure escalation

Third failure of the same function = the concept is wrong, not the
sizing. Stop iterating thickness; change the mechanism (different joint
type, bought part, different material system) — bring Jonathan the
honest options per CLAUDE.md Honesty rules.
