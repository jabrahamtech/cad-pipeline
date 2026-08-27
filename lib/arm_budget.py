"""Parametric moment budget for the arm. What do L1, L2 and the head cost?

    python3 lib/arm_budget.py

WHY THIS EXISTS
---------------
specs/robotarm/_assembly.md has carried a J3 duty figure since the arm was
laid out, and every version of it was arithmetic done by hand against one
fixed pair of link lengths. When Jonathan asked to match the reference arm's
proportions - shorter, chunkier links - there was no way to answer "what does
that buy" without redoing the whole table by hand again.

This does it parametrically, and it is validated: with the CURRENT numbers it
must reproduce the 873.7 g.cm that _assembly.md reports, or it is wrong and
says so.

THE MODEL
---------
Everything outboard of the elbow is one rigid cluster whose parts sit at
FIXED offsets from the wrist end of the forearm. Shortening L2 therefore
translates the entire cluster inboard by that amount - it does not rescale
it. That is the single most important property here and it is why shortening
buys so much: the head is 49 % of the elbow moment and it moves 1:1 with L2.

The links themselves are beams of roughly constant section, so their mass
scales with length and their centre of mass sits at a fixed FRACTION of it.

DENSITY - read this before trusting any mass
--------------------------------------------
Every mass in _assembly.md was computed as 0.6 x Fusion's 'PET Plastic'
density, which is 1.541 g/cm3. PETG FILAMENT is ~1.27, and the real solid
fraction measured off an actual slice is 0.65, not 0.60. So the shipped
figures used 1.541 x 0.60 = 0.925 where the truth is 1.27 x 0.65 = 0.826 -
they are 12 % HIGH on every printed part. Servos and payload are unaffected
because they are bought, not printed. Both are reported below.
"""

# --- what a gram of printed plastic actually weighs -------------------------
FUSION_PET = 1.541      # g/cm3, what _assembly.md's masses were computed with
FUSION_INFILL = 0.60
PETG = 1.27             # g/cm3, real filament
REAL_INFILL = 0.65      # measured off the gauge_fits v4 slice
MASS_CORRECTION = (PETG * REAL_INFILL) / (FUSION_PET * FUSION_INFILL)

# --- servo duty, from lib/servo.py: duty limit = stall x 0.5 ---------------
DUTY_KGCM = {'J2': 9.4 * 0.5, 'J3': 2.0 * 0.5, 'J4': 2.0 * 0.5}
# EVERYTHING ELSE IN THIS FILE IS IN g.cm. Mixing the two is how the first
# run of this script reported the arm at 873 % of duty and refused to find a
# link section that fitted. Convert once, here, and never compare the two.
DUTY = {k: v * 1000.0 for k, v in DUTY_KGCM.items()}          # g.cm

# --- the outboard cluster, as built. offset_mm is measured from the WRIST
#     end of the forearm, i.e. r = L2 + offset. Masses are the _assembly.md
#     figures, which are Fusion-density and get corrected below.
#     bought=True means the mass is real and carries no density error.
CLUSTER = [
    # name,            mass_g, offset_mm, bought
    ('wrist_hub x2',      5.2,    0.0,   False),
    ('wrist_roll',       12.2,    2.3,   False),
    ('wrist_rotator',     5.3,   19.8,   False),
    ('MG90S J4',         13.4,   -6.0,   True),
    ('SG90 J5 roll',      9.0,    0.0,   True),
    ('SG90 effector',     9.0,   32.0,   True),
]
HEAD_OFFSET_MM = 47.0        # head centre of mass, past the wrist end

# --- the links -------------------------------------------------------------
# mass per mm of length at the CURRENT section, back-calculated from the
# built parts: forearm 20.6 g over 65 mm, upper arm from its own volume.
# MEASURED off the built bodies 2026-08-26, at Fusion density so the
# correction below still applies: forearm 15720 mm3 over 45 mm,
# upper_arm 30891 mm3 over 65 mm. Neither is an estimate any more.
FOREARM_G_PER_MM = 15719.949 * 0.0009246 / 45.0
UPPERARM_G_PER_MM = 30890.567 * 0.0009246 / 65.0
FOREARM_COM_FRAC = 2.84 / 6.5        # 0.437, from the _assembly.md table
UPPERARM_COM_FRAC = 0.50             # ESTIMATE

# --- two different arms, and they must never be paired -----------------------
# BUILT is the arm ON DISK TODAY. VALIDATION is the arm _assembly.md's
# published 873.7 g.cm was computed for, which is the one BEFORE the
# 2026-08-26 link change. They sat adjacent as `BUILT` and `BUILT_J3_TARGET`
# with nothing saying they belonged to different geometries, and pairing them
# gives a 33 % error - 658 g.cm against a 873.7 target. Caught 2026-08-26 by
# tests/test_arm_loads.py doing exactly that.
BUILT = dict(l1=65.0, l2=45.0, head_g=38.3, section=1.0)
VALIDATION = dict(l1=85.0, l2=65.0, head_g=38.3, section=1.0)
VALIDATION_J3_TARGET = 873.7         # g.cm, _assembly.md, at VALIDATION's L2
VALIDATION_TOL = 1.0


def validate():
    """Reproduce _assembly.md's published figure, or say so and stop.

    This was a printed row that a human had to eyeball, which is not a
    mechanism. It is an assertion now, and main() runs it before printing
    anything - a table derived from a broken model is worse than no table.
    """
    got = j3_moment(VALIDATION['l2'], VALIDATION['head_g'],
                    VALIDATION['section'], correct_density=False)[0]
    assert abs(got - VALIDATION_J3_TARGET) <= VALIDATION_TOL, (
        'arm_budget no longer reproduces _assembly.md: %.2f against %.1f g.cm '
        'at L2 %.0f. Fix this before trusting any row below it.'
        % (got, VALIDATION_J3_TARGET, VALIDATION['l2']))
    return got


def j3_moment(l2, head_g, section=1.0, correct_density=False):
    """Elbow moment, arm horizontal. `section` scales the LINK mass only -
    it is how a chunkier link gets priced."""
    k = MASS_CORRECTION if correct_density else 1.0
    total = 0.0
    rows = []
    fa = FOREARM_G_PER_MM * l2 * section * k
    rows.append(('forearm', fa, FOREARM_COM_FRAC * l2 / 10.0))
    for name, m, off, bought in CLUSTER:
        mm = m if bought else m * k
        rows.append((name, mm, (l2 + off) / 10.0))
    rows.append(('head', head_g * k, (l2 + HEAD_OFFSET_MM) / 10.0))
    for _, m, r in rows:
        total += m * r
    return total, rows


def j2_moment(l1, l2, head_g, section=1.0, correct_density=False):
    """Shoulder carries everything the elbow does, at L1 further out, plus
    the elbow servo and the upper arm."""
    k = MASS_CORRECTION if correct_density else 1.0
    j3, rows = j3_moment(l2, head_g, section, correct_density)
    mass_outboard = sum(m for _, m, _ in rows)
    total = j3 + mass_outboard * l1 / 10.0
    ua = UPPERARM_G_PER_MM * l1 * section * k
    total += ua * UPPERARM_COM_FRAC * l1 / 10.0
    total += 13.4 * l1 / 10.0            # the J3 MG90S sits at the elbow
    return total


# _assembly.md quotes ~300 mm from the yaw axis to the jaw faces at
# L1 85 / L2 65, where L1 + L2 = 150. So everything outside the two links -
# the yaw-to-shoulder offset plus wrist-to-jaws - is a fixed 150 mm.
FIXED_REACH_MM = 150.0


def reach(l1, l2):
    """Shoulder axis to wrist axis. This is the figure _assembly.md calls
    'reach' and it is just L1 + L2."""
    return l1 + l2


def working_reach(l1, l2):
    """Yaw axis to the jaw faces - what it can actually get to."""
    return l1 + l2 + FIXED_REACH_MM


def solve_section(l2, head_g, cap=0.90, correct=True):
    """Biggest link-section multiplier that keeps J3 at or under `cap`."""
    lo, hi = 0.1, 12.0
    if j3_moment(l2, head_g, lo, correct)[0] > DUTY['J3'] * cap:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if j3_moment(l2, head_g, mid, correct)[0] <= DUTY['J3'] * cap:
            lo = mid
        else:
            hi = mid
    return lo


def row(tag, l1, l2, head_g, section=1.0, correct=True):
    j3, _ = j3_moment(l2, head_g, section, correct)
    j2 = j2_moment(l1, l2, head_g, section, correct)
    return ('  %-30s %4.0f %4.0f %6.1f %6.2fx %7.1f %5.0f%% %7.1f %5.0f%% %6.0f'
            % (tag, l1, l2, head_g, section, j3, 100.0 * j3 / DUTY['J3'],
               j2, 100.0 * j2 / DUTY['J2'], reach(l1, l2)))


def main():
    _v = validate()
    print('')
    print('  validated: L2 %.0f reproduces _assembly.md at %.2f g.cm '
          '(target %.1f)' % (VALIDATION['l2'], _v, VALIDATION_J3_TARGET))
    hdr = ('  %-30s %4s %4s %6s %7s %7s %6s %7s %6s %6s'
           % ('scenario', 'L1', 'L2', 'head', 'section', 'J3 g.cm', 'J3', 'J2 g.cm', 'J2', 'reach'))
    print('')
    print('MOMENT BUDGET   (duty limit = stall x 0.5: J3 = %.2f, J2 = %.2f kg.cm)'
          % (DUTY_KGCM['J3'], DUTY_KGCM['J2']))
    print('=' * len(hdr))
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    print(row('as built, as SHIPPED figures', 85, 65, 38.3, 1.0, False))
    print(row('as built, density CORRECTED', 85, 65, 38.3, 1.0, True))
    print('')
    print('  full match to the reference, pruner head as built:')
    print(row('L1 65 / L2 45', 65, 45, 38.3, 1.0, True))
    print('')
    print('  full match, grip-and-cut head - what can it weigh?')
    for h in (45.0, 50.0, 55.0, 60.0, 65.0):
        print(row('head %.0f g, links as built' % h, 65, 45, h, 1.0, True))
    print('')
    print('  and then how CHUNKY can the links get, at 90 %% J3?')
    for h in (45.0, 50.0, 55.0, 60.0):
        s = solve_section(45.0, h)
        if s is None:
            print('  head %.0f g: no section fits' % h)
            continue
        print(row('head %.0f g, links x%.2f' % (h, s), 65, 45, h, s))
    print('')
    print('  for comparison, the same question at the CURRENT length:')
    s = solve_section(65.0, 38.3)
    if s is None:
        print('  L2 65 with the pruner head cannot reach 90 % at any section.')
    else:
        print(row('L2 65, pruner head, links x%.2f' % s, 85, 65, 38.3, s))
    print('')
    print('  RECOMMENDED:')
    for sec in (2.0, 2.5, 3.0):
        print(row('head 55 g, links x%.1f' % sec, 65, 45, 55.0, sec))
    print('')
    print('  working reach (yaw axis -> jaw faces): %.0f mm, against %.0f mm'
          % (working_reach(65, 45), working_reach(85, 65)))
    print('')
    print('  section x2.0 means twice the link MASS, not twice the size - at')
    print('  constant length that is roughly 1.4x the cross-section in both')
    print('  directions, which is the difference between a waisted 18 mm rib')
    print('  and a 25 mm slab. That is the reference arm\'s proportion.')
    print('')


if __name__ == '__main__':
    main()
