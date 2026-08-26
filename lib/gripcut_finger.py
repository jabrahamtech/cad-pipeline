"""The grip-and-cut finger: hold the cutting so it does not fall.

Jonathan asked for a "gripper/cutter". The built head is a bypass shear that
only cuts, so the severed piece drops. This sizes the addition that holds it.

THE CONSTRAINT THAT SHAPES EVERYTHING
-------------------------------------
The servo inventory is exactly used - 1 x MG995, 2 x MG90S, 3 x SG90, no
spare (specs/robotarm/_assembly.md). So grip and cut must come off ONE SG90,
already fully committed to driving the blades. There is no second actuator
and no travel to spare: the blades use 21.8 mm of a 21.8 mm rack stroke.

That rules out any sequenced mechanism with its own input. What is left is a
finger that rides the blade it is bolted to, leads it, and is compliant
enough to keep holding while the blade travels the rest of the way.

WHY A PRINTED FLEXURE AND NOT A SPRING
--------------------------------------
There are no springs in the inventory and adding one means a BOM line, a
retention feature and a part that can fall out inside a moving head. A PETG
cantilever costs nothing, cannot escape, and is sized here rather than
guessed. The trade is fatigue, and the strain limit below is what buys it.

THE GEOMETRY, WHICH IS THE SAME GEOMETRY AS THE BLADE
-----------------------------------------------------
pruner_linkage's blades are two lines each offset `edge_offset` = a from a
common pivot, so their gap at radius r and angle theta is

    gap(r, theta) = 2 (a - r sin theta) / cos theta

A finger bolted to the same carrier, at a SMALLER offset a_f, is the same
equation with a smaller numerator - so it closes on any given stem EARLIER,
by exactly the lead (a - a_f), and needs no separate linkage at all. The
finger sits offset in +Z, above the cutting plane, so it grips the length of
stem that is about to become the cutting rather than the stump.

Everything below is that one substitution, taken to its consequences.
"""

from __future__ import annotations

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pruner_linkage import CHOSEN            # noqa: E402

# --- material. PETG, and the flexure MUST be printed with its layers running
#     along the length so the bending stress is in-plane. Across layers this
#     is a fatigue crack waiting to happen (knowledge/materials.md).
E_PETG_MPA = 2000.0
STRAIN_LIMIT = 0.010        # HANDBOOK. PETG yields near 0.04-0.05; a tenth of
                            # that is the usual cyclic-flexure allowance. This
                            # has NOT been gauged on this spool.

# --- what the grip has to do ----------------------------------------------
STEM_RANGE_MM = (2.0, 5.0)  # what the head can actually cut - pruner.md
CUTTING_MASS_G = 20.0       # a generous house-plant cutting
FRICTION = 0.4              # printed PETG tooth against green stem, HANDBOOK
G = 9.807


def grip_force_needed_n(mass_g=CUTTING_MASS_G, mu=FRICTION):
    """Normal force per finger to hold the cutting against gravity."""
    weight_n = mass_g / 1000.0 * G
    return weight_n / (2.0 * mu)          # two fingers share it


def theta_cut(r):
    """Blade angle at which the edges cross at radius r - the cut is done."""
    return math.asin(min(1.0, CHOSEN.edge_offset / r))


def deflection_mm(stem_d, lead, r=None):
    """How far each finger must give, from first touching the stem to the
    moment the blade finishes the cut."""
    r = CHOSEN.throat_r if r is None else r
    th = theta_cut(r)
    # nominal finger gap at full cut, with offset a_f = a - lead
    nominal = 2.0 * ((CHOSEN.edge_offset - lead) - r * math.sin(th)) / math.cos(th)
    return (stem_d - nominal) / 2.0


def flexure(t, delta, w, strain=STRAIN_LIMIT):
    """Cantilever sized to swallow `delta` without exceeding `strain`.
    Returns (length_mm, force_N, strain_actual)."""
    L = math.sqrt(3.0 * t * delta / (2.0 * strain))
    F = E_PETG_MPA * w * t ** 3 * delta / (4.0 * L ** 3)
    return L, F, strain


# The finger resists the blade it is bolted to. Both push on the same stem at
# the same radius, so the flexure force subtracts DIRECTLY from the cutting
# force - it is not a second-order loss. pruner.md quotes 31.5 N at the throat
# radius of 8.5 mm, and ~10 N per mm of stem for a sharp bypass blade, taken
# at the pessimistic x2 scissor progression.
CUT_FORCE_AT_THROAT_N = 31.5
STEM_N_PER_MM = 10.0
PROGRESSION = 2.0


def stem_capacity_mm(finger_force_n):
    """What the head can still cut with two fingers pushing back."""
    net = CUT_FORCE_AT_THROAT_N - 2.0 * finger_force_n
    return max(0.0, net * PROGRESSION / STEM_N_PER_MM)


def solve(w=6.0, need=None):
    """Smallest flexure that grips the whole stem range without over-straining
    on the biggest. The BIG stem sets the length; the SMALL one sets whether
    there is still enough force left to hold anything."""
    need = grip_force_needed_n() if need is None else need
    out = []
    for lead in (0.5, 1.0, 1.5, 2.0):
        for t in (1.2, 1.6, 2.0):
            d_big = deflection_mm(STEM_RANGE_MM[1], lead)
            d_small = deflection_mm(STEM_RANGE_MM[0], lead)
            if d_small <= 0:
                continue        # finger never reaches the small stem
            L, F_big, _ = flexure(t, d_big, w)
            F_small = F_big * d_small / d_big
            cap = stem_capacity_mm(F_big)
            out.append(dict(lead=lead, t=t, L=L, d_big=d_big, d_small=d_small,
                            F_big=F_big, F_small=F_small, cap=cap,
                            ok=(F_small >= need
                                and cap >= STEM_RANGE_MM[1]
                                and t >= 1.2)))
    return out, need


def main():
    print('')
    print('GRIP-AND-CUT FINGER')
    print('=' * 74)
    print('  blade pivot offset a = %.2f, throat r = %.2f, cut at theta = %.1f deg'
          % (CHOSEN.edge_offset, CHOSEN.throat_r,
             math.degrees(theta_cut(CHOSEN.throat_r))))
    need = grip_force_needed_n()
    print('  a %.0f g cutting at mu %.2f needs %.2f N per finger'
          % (CUTTING_MASS_G, FRICTION, need))
    print('')
    print('  no-finger stem capacity at the throat: %.1f mm'
          % stem_capacity_mm(0.0))
    print('')
    print('  %-6s %5s %7s %7s %8s %8s %7s %s'
          % ('lead', 't', 'L', 'F@5mm', 'F@2mm', 'stem cap', 'lost', ''))
    print('  ' + '-' * 70)
    rows, _ = solve()
    base = stem_capacity_mm(0.0)
    for r in rows:
        why = 'ok'
        if r['F_small'] < need:
            why = 'too soft'
        elif r['cap'] < STEM_RANGE_MM[1]:
            why = 'eats the cut'
        print('  %-6.1f %5.1f %7.1f %8.2f %8.2f %8.1f %6.0f%% %s'
              % (r['lead'], r['t'], r['L'], r['F_big'], r['F_small'],
                 r['cap'], 100 * (base - r['cap']) / base, why))
    print('')
    good = [r for r in rows if r['ok']]
    if not good:
        print('  NOTHING FITS. Either the strain limit or the friction')
        print('  assumption has to move, and both are HANDBOOK.')
        return
    # force is not scarce and length is, so rank on the most LEAD that still
    # leaves the full stem range cuttable - lead is what buys grip before the
    # blade arrives, and that is the whole point of the finger.
    best = max(good, key=lambda r: (r['lead'], -r['L']))
    print('  CHOSEN: lead %.1f, t %.1f, L %.1f mm, %.2f-%.2f N,'
          % (best['lead'], best['t'], best['L'], best['F_small'], best['F_big']))
    print('          still cuts %.1f mm (%.0f %% of the %.1f mm it manages bare)'
          % (best['cap'], 100 * best['cap'] / base, base))
    print('')
    print('  t = %.1f is BELOW design_rules MIN_WALL_MM of 1.6, deliberately.'
          % best['t'])
    print('  That rule is about structure; this is a flexure, where a thicker')
    print('  leaf is worse twice over - more force stolen from the cut, and a')
    print('  longer leaf to keep the strain down. At 0.4 nozzle it is still')
    print('  three full extrusions wide.')
    print('')
    print('  The lead is what buys grip BEFORE the cut: at lead %.1f the finger'
          % best['lead'])
    print('  touches a %.0f mm stem %.1f deg of blade rotation early.'
          % (STEM_RANGE_MM[1],
             math.degrees(theta_cut(CHOSEN.throat_r))
             - math.degrees(math.asin(min(1.0, (CHOSEN.edge_offset - best['lead'])
                                          / CHOSEN.throat_r)))))
    print('')
    print('  PACKAGING: the blade spans y 22 (tip) to y 16 (drive pin) through')
    print('  the pivot at y 42, so ~50 mm of carrier is available - but only')
    print('  %.1f mm separates the pivot from the throat. A %.0f mm straight'
          % (CHOSEN.throat_r, best['L']))
    print('  cantilever does not fit forward of the pivot and has to fold.')
    print('')


if __name__ == '__main__':
    main()
