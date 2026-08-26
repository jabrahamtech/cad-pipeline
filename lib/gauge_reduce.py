"""Turn _gauge_slim measurements into design numbers.

Edit MEASURED below with what came off the calipers, then run:

    python3 lib/gauge_reduce.py

WHAT CHANGED FROM THE _gauge_fits VERSION
-----------------------------------------
The old plate swept eight fits three ways each, so this script only had to
report which variant won. The slim plate sweeps only what a caliper cannot
answer and COLLAPSES the rest to one feature - so deriving those values is
now this script's job, not the plate's.

That moves the risk. The old plate could be read even if the bias reading
was rubbish, because every fit had its own sweep to fall back on. This one
cannot: if the truth row is wrong, every collapsed station is wrong with it
and nothing on the plate would tell you. So the truth row is now three bores
and two bosses spanning :4 to :20, and the FIRST thing this script does is
check whether the bias is consistent enough to interpolate along. If it is
not, it says so and refuses to derive, rather than printing a confident
number built on a straight line through points that were never straight.

Re-run after any change of material, nozzle or layer height. A stack
budgeted in one PETG does not transfer to another (knowledge/materials.md).
"""

import math

# ---------------------------------------------------------------------------
# EDIT THIS BLOCK. None = not measured yet; the report says so rather than
# quietly inventing a number.
# ---------------------------------------------------------------------------
MEASURED = {
    # --- Step 1: TRUTH. Everything below is read through these. -------------
    # Caliper each twice, 90 deg apart, and average.
    'boss': {20.00: None, 8.00: None},          # D20, D8   - outside features
    'bore': {20.00: None, 8.00: None, 4.00: None},   # B20, B8, B4 - inside
    'block_x': None,                             # nominal 20.00
    'block_y': None,                             # nominal 10.00
    'block_z': None,                             # nominal  5.00
    # The plate's OWN outline. Exactly 96.000 x 150.000 and nothing reaches
    # outside it, so these are two free long outside references - and they are
    # the only thing here that can separate a constant offset from a scale
    # error. Caliper across the plate, twice each way, avoiding any corner
    # that lifted.
    'plate_x': None,                             # nominal  96.00
    'plate_y': None,                             # nominal 150.00

    # --- Step 2: HEX. Tip travel in mm at the four sockets. -----------------
    'lever_af': None,                            # nominal 15.80
    'tip_travel': {0.10: None, 0.20: None, 0.30: None, 0.40: None},

    # --- Step 3: SEATS. Does a real 608 SPIN on it? True / False. -----------
    'seat_spins': {10.0: None, 11.0: None, 12.0: None},
    'flat_bare_d': None,        # caliper the lying-down bare stub, nominal 7.90
    'flat_seat_spins': None,    # does a 608 spin on the lying-down 11.0 seat?

    # --- Step 4: PILOTS. Which took the screw without splitting? ------------
    'm3_pilot_best': None,      # one of 2.4 / 2.5 / 2.6 / 2.8
    'm2_pilot_best': None,      # one of 1.6 / 1.7 / 1.8 / 2.0
}

# What the slim plate actually printed, per station.
#   dia       the DRAWN size of the printed feature
#   side      which side of the fit is PRINTED - 'bore' (a hole) or 'boss'
#   drawn     the nominal clearance as drawn
#   rule      which entry in design_rules.JOINT_FIT_MM it is meant to satisfy
#   mate      'printed' if the other half is also printed, 'bought' if it is a
#             bearing, a servo horn or a brass insert
#
# The `mate` column is not decoration. A printed bore on a printed shaft
# carries BOTH biases and they partly cancel; a printed bore on a bought
# 608 carries only its own, because steel does not shrink to suit us. The
# first version of this file applied both to everything and reported the
# stub axle - a printed boss into a bought bore - as binding by 0.25 when
# the real figure was half that.
COLLAPSED = {
    'journal bore': dict(dia=20.35, side='bore', drawn=0.35,
                         rule='rotating', mate='printed'),
    'slide slot':   dict(dia=10.25, side='bore', drawn=0.25,
                         rule='sliding', mate='printed'),
    '608 pocket':   dict(dia=22.05, side='bore', drawn=0.05,
                         rule='bearing_pocket', mate='bought'),
    'MG995 horn':   dict(dia=12.15, side='bore', drawn=0.15,
                         rule='press', mate='bought'),
    'SG90 horn':    dict(dia=7.15,  side='bore', drawn=0.15,
                         rule='press', mate='bought'),
    'M3 insert':    dict(dia=4.00,  side='bore', drawn=0.00,
                         rule='insert', mate='bought'),
    'stub axle':    dict(dia=7.90,  side='boss', drawn=0.10,
                         rule='rotating', mate='bought'),
}

# What the REAL clearance has to land between for each rule to have been met.
# A press fit is drawn with positive clearance in this project and relies on
# the printer eating it, so "real, near zero" is success and a positive real
# clearance is the failure - the opposite of how the rotating rows read.
ACCEPT = {
    'press':          (-0.12, 0.04),
    'insert':         (-0.18, 0.04),
    'bearing_pocket': (-0.03, 0.09),
    'sliding':        (0.10, 0.35),
    'rotating':       (0.15, 0.50),
}

LEVER_TIP_R = 63.0           # mm, hex axis to the tip corner - see _gauge_slim
HEX_LEVER_AF = 15.80
TODAY = {'hex': 0.20, 'journal': 0.35, 'seat': 11.0}
ARMS = {'J2 shoulder': 268.0, 'J3 elbow': 190.0, 'J4 wrist': 105.0}
SERVO_GEAR_DEG = 1.0         # ASSUMPTION, not a measurement
# Community-reported bands for Bambu X-series / PETG / 0.4 nozzle / 0.2 mm.
# See knowledge/materials.md "Expected dimensional bias - the PRIOR" for the
# sources and the caveats. These are NOT design values. Their only job is to
# answer one question: is this reading normal for this class of machine, or is
# something misconfigured? A bias outside the band chased in CAD buries the
# problem instead of fixing it.
PRIOR = {
    'boss': {20.00: (-0.20, 0.10), 8.00: (-0.20, 0.10)},
    'bore': {20.00: (-0.15, 0.00), 8.00: (-0.25, -0.05), 4.00: (-0.40, -0.15)},
}

LINEARITY_TOL = 0.05         # mm of slope disagreement before we stop trusting
                             # the interpolation. See interp() below.


def rule(title):
    print('')
    print(title)
    print('-' * len(title))


def interp(points, d):
    """Piecewise-linear through measured (diameter, bias) points, clamped at
    the ends. Deliberately NOT a least-squares line: with three points a fit
    would smooth away exactly the curvature we printed the extra bores to
    detect."""
    xs = sorted(points)
    if d <= xs[0]:
        d = xs[0]
    if d >= xs[-1]:
        d = xs[-1]
    for a, b in zip(xs, xs[1:]):
        if a <= d <= b:
            t = 0.0 if b == a else (d - a) / (b - a)
            return points[a] + t * (points[b] - points[a])
    return points[xs[-1]]


def collect(kind):
    """The measured biases for one side, as {nominal: bias}."""
    out = {}
    for nom, meas in MEASURED[kind].items():
        if meas is not None:
            out[nom] = meas - nom
    return out


def hex_backlash_deg(a_af, b_af):
    """Inner hex across-flats `a` in a socket across-flats `b`. Rotation until
    a vertex of the inner meets a flat of the socket."""
    if a_af >= b_af:
        # NOT zero backlash - an interference fit. Returning 0.0 here reads as
        # a perfect joint on the report, which is the one wrong answer that
        # would look like the right one.
        return float('nan')
    r_vertex = a_af / math.sqrt(3.0)
    r_socket = b_af / 2.0
    if r_vertex >= r_socket / math.cos(math.radians(30.0)):
        return float('nan')          # will not assemble
    return 30.0 - math.degrees(math.acos(min(1.0, r_socket / r_vertex)))


def check_prior(boss, bore):
    """Is this reading NORMAL for this class of machine? Not a design check -
    a configuration check. knowledge/materials.md carries the bands."""
    outliers = []
    for kind, pts in (('boss', boss), ('bore', bore)):
        for nom, bias in sorted(pts.items()):
            band = PRIOR[kind].get(nom)
            if band is None:
                continue
            lo, hi = band
            if bias < lo:
                outliers.append((kind, nom, bias, lo, hi, 'UNDER'))
            elif bias > hi:
                outliers.append((kind, nom, bias, lo, hi, 'OVER'))
    if not (boss or bore):
        return
    print('')
    if not outliers:
        print('  All measured biases fall inside the published band for this')
        print('  class of machine (knowledge/materials.md). Normal - carry on.')
        return
    print('  OUTSIDE THE PUBLISHED BAND:')
    for kind, nom, bias, lo, hi, way in outliers:
        print('    %-5s :%-6.2f bias %+.3f is %s the expected %+.2f..%+.2f'
              % (kind, nom, bias, way, lo, hi))
    print('')
    print('  This is a CONFIGURATION signal, not a design one. Before changing')
    print('  a single value in lib/design_rules.py, check:')
    boss_out = [o for o in outliers if o[0] == 'boss']
    bore_out = [o for o in outliers if o[0] == 'bore']
    if boss_out and all(o[5] == 'UNDER' for o in boss_out):
        print('    - every outside feature is small -> shrinkage under-')
        print('      compensated. Bambu Studio filament "Shrinking"; users land')
        print('      near 99.6 for PETG. Fix this FIRST - it moves everything.')
    if boss_out and all(o[5] == 'OVER' for o in boss_out):
        print('    - every outside feature is large -> flow rate high, or the')
        print('      elephant-foot chamfer is not doing its job. Run a flow')
        print('      calibration before reading anything else on this plate.')
    if bore_out and all(o[5] == 'UNDER' for o in bore_out):
        print('    - every bore is small beyond the band -> flow high, or an')
        print('      X-Y hole compensation is set NEGATIVE. Note that Bambu')
        print('      Studio takes that value as a RADIUS, not a diameter.')
    if bore_out and all(o[5] == 'OVER' for o in bore_out):
        print('    - bores running large is unusual -> an X-Y hole compensation')
        print('      is probably already set. It halves the value you enter')
        print('      (radius, not diameter), so overcorrection is common.')
    print('    - nozzle wear, and whether this spool is the one the arm will use')
    print('')
    print('  If the cause is found and fixed, REPRINT the plate. Everything')
    print('  below is derived from these numbers.')


def report_truth():
    """Returns (boss_bias, bore_bias, trustworthy) - the two curves and
    whether they may be interpolated along."""
    rule('1. MACHINE TRUTH - the whole plate is read through this')
    boss = collect('boss')
    bore = collect('bore')

    for label, got, want in (('boss', boss, MEASURED['boss']),
                             ('bore', bore, MEASURED['bore'])):
        for nom in sorted(want):
            if nom in got:
                print('  %-5s %6.2f   measured %6.2f   bias %+.3f'
                      % (label, nom, want[nom], got[nom]))
            else:
                print('  %-5s %6.2f   NOT MEASURED' % (label, nom))

    for k, nom in (('block_x', 20.00), ('block_y', 10.00), ('block_z', 5.00)):
        v = MEASURED[k]
        if v is None:
            print('  %-5s %6.2f   NOT MEASURED' % (k[-1].upper(), nom))
        else:
            print('  %-5s %6.2f   measured %6.2f   bias %+.3f'
                  % (k[-1].upper(), nom, v, v - nom))

    check_prior(boss, bore)

    if len(boss) < 2 or len(bore) < 2:
        print('')
        print('  STOP. The slim plate collapsed seven stations to one feature')
        print('  each on the promise that this row would let us derive them.')
        print('  With fewer than two bosses and two bores there is no curve to')
        print('  derive along, and nothing below section 2 is safe to use.')
        return boss, bore, False

    # Is the bias actually consistent across diameter? This is the check that
    # the old plate did not need and this one cannot do without.
    trustworthy = True
    print('')
    for label, pts in (('boss', boss), ('bore', bore)):
        xs = sorted(pts)
        slopes = []
        for a, b in zip(xs, xs[1:]):
            slopes.append((pts[b] - pts[a]) / (b - a) * 10.0)   # per 10 mm
        spread = max(pts.values()) - min(pts.values())
        print('  %-5s bias runs %+.3f at :%.0f to %+.3f at :%.0f  (spread %.3f)'
              % (label, pts[xs[0]], xs[0], pts[xs[-1]], xs[-1], spread))
        if spread > LINEARITY_TOL:
            print('        -> NOT constant. Small features carry a different')
            print('           bias from large ones here, which is normal and is')
            print('           exactly why the extra bores are on the plate.')
        if label == 'bore' and len(xs) > 2:
            # holes lose more as they shrink; the reverse means a measurement
            # slipped or the plate is not flat
            if not all(pts[a] <= pts[b] + 1e-9 for a, b in zip(xs, xs[1:])):
                print('        -> REVERSED: a larger bore is further under')
                print('           nominal than a smaller one. That is backwards')
                print('           for FDM. Re-measure before trusting anything.')
        if len(slopes) > 1 and abs(slopes[0] - slopes[-1]) > LINEARITY_TOL:
            print('        -> and the trend is NOT straight either (%.3f vs %.3f'
                  % (slopes[0], slopes[-1]))
            print('           per 10 mm). Interpolated values below are')
            print('           indicative; re-gauge any fit that matters.')
            trustworthy = False
    return boss, bore, trustworthy


def report_scale(boss):
    """Offset or scale? The truth-row bosses span 8..20 mm, which is far too
    short a baseline to tell the difference - and the difference decides where
    the fix belongs. Published outside error on these machines is
    shrinkage-dominated and therefore PROPORTIONAL (20 -> 0.1, 100 -> 0.4),
    which a two-point 8..20 reading reads as a small constant."""
    rule('1b. OFFSET OR SCALE - what the plate outline says')
    px, py = MEASURED['plate_x'], MEASURED['plate_y']
    if px is None and py is None:
        print('  plate outline NOT MEASURED. It is two caliper readings on a')
        print('  part already in your hand, and it is the only measurement here')
        print('  that can tell a constant offset from a scale error.')
        return
    if not boss:
        print('  Needs the truth-row bosses.')
        return
    ref = sorted(boss)[-1]                 # the largest measured boss
    ref_bias = boss[ref]
    print('  reference: the :%.0f boss, bias %+.3f' % (ref, ref_bias))
    print('')
    print('  %-10s %9s %10s %12s %11s' % (
        'edge', 'nominal', 'measured', 'if OFFSET', 'if SCALE'))
    verdicts = []
    for tag, meas, nom in (('plate X', px, 96.00), ('plate Y', py, 150.00)):
        if meas is None:
            print('  %-10s %9.2f %10s' % (tag, nom, 'NOT MEASURED'))
            continue
        bias = meas - nom
        pred_offset = ref_bias
        pred_scale = ref_bias / ref * nom
        print('  %-10s %9.2f %10.2f %+12.3f %+11.3f   actual %+.3f'
              % (tag, nom, meas, pred_offset, pred_scale, bias))
        verdicts.append((abs(bias - pred_offset), abs(bias - pred_scale)))
    if not verdicts:
        return
    off_err = sum(v[0] for v in verdicts)
    scl_err = sum(v[1] for v in verdicts)
    print('')
    if off_err <= scl_err:
        print('  OFFSET wins. The error is roughly the same absolute size at')
        print('  96 mm as at 20 mm, so it lands entirely on FITS and barely at')
        print('  all on the length of an arm link. Fix it in lib/design_rules,')
        print('  which is where fits live.')
    else:
        pct = 100.0 * sum(
            (m - n) / n for m, n in ((px, 96.0), (py, 150.0)) if m is not None
        ) / len([m for m in (px, py) if m is not None])
        print('  SCALE wins: %+.3f %% across the plate.' % pct)
        print('  This is shrinkage, and it behaves the opposite way round to an')
        print('  offset - almost invisible on a 12 mm press fit, and %.2f mm on'
              % (abs(pct) / 100.0 * 200))
        print('  a 200 mm arm link, where it moves a joint centre.')
        print('  Fix it with the slicer\'s filament "Shrinking" percentage, NOT')
        print('  in design_rules - a scale error is not a clearance error, and')
        print('  correcting it as one would wreck every fit on the plate.')
        print('  Then REPRINT and re-read: a scale change moves the fits too.')
    print('')


def report_derived(boss, bore, trustworthy):
    rule('2. THE COLLAPSED STATIONS - derived, not printed')
    if len(boss) < 2 or len(bore) < 2:
        print('  Needs section 1.')
        return
    print('  Each station carries the bias of ITS OWN diameter on ITS OWN')
    print('  side - and only its own side when the other half is bought.')
    print('')
    print('  %-14s %6s %8s %8s %9s %s' % (
        'station', 'dia', 'mate', 'drawn', 'real', 'verdict'))
    rows = sorted(COLLAPSED.items(), key=lambda kv: -kv[1]['dia'])
    for name, c in rows:
        d = c['dia']
        if c['side'] == 'bore':
            shift = interp(bore, d) - (interp(boss, d) if c['mate'] == 'printed' else 0.0)
        else:
            shift = -interp(boss, d) + (interp(bore, d) if c['mate'] == 'printed' else 0.0)
        real = c['drawn'] + shift
        lo, hi = ACCEPT[c['rule']]
        if real < lo:
            verdict = 'TIGHT  (%s wants %+.2f..%+.2f)' % (c['rule'], lo, hi)
        elif real > hi:
            verdict = 'LOOSE  (%s wants %+.2f..%+.2f)' % (c['rule'], lo, hi)
        else:
            verdict = 'ok     (%s)' % c['rule']
        print('  %-14s %6.2f %8s %8.2f %+9.3f  %s'
              % (name, d, c['mate'], c['drawn'], real, verdict))
    print('')
    if not trustworthy:
        print('  READ THESE AS INDICATIVE. Section 1 says the bias is not')
        print('  straight across diameter, so the interpolation is doing real')
        print('  work and the small-diameter rows carry most of it.')
    print('  Nothing here was printed as a variant. If a row above matters')
    print('  enough to be wrong about, print that ONE feature three ways -')
    print('  a 10-minute print, not a 2-hour one.')


def report_hex():
    rule('3. THE HEX DRIVE - swept, because backlash is an angle')
    lever = MEASURED['lever_af'] if MEASURED['lever_af'] is not None else HEX_LEVER_AF
    if MEASURED['lever_af'] is None:
        print('  lever not measured - assuming the drawn %.2f' % HEX_LEVER_AF)
    else:
        print('  lever measured %.2f af (drawn %.2f, bias %+.3f)'
              % (lever, HEX_LEVER_AF, lever - HEX_LEVER_AF))
    print('')
    print('  %-10s %10s %12s %12s %12s' % (
        'designed', 'socket af', 'tip travel', 'backlash', 'predicted'))
    best = None
    today_deg = None
    for clr in sorted(MEASURED['tip_travel']):
        socket = HEX_LEVER_AF + clr
        pred = hex_backlash_deg(lever, socket)
        t = MEASURED['tip_travel'][clr]
        pred_s = 'JAM' if math.isnan(pred) else '%.2f' % pred
        if t is None:
            print('  %-10.2f %10.2f %12s %12s %12s' % (clr, socket, '-', '-', pred_s))
            continue
        deg = math.degrees(t / LEVER_TIP_R)
        flag = '  <- today' if abs(clr - TODAY['hex']) < 1e-9 else ''
        print('  %-10.2f %10.2f %12.2f %12.2f %12s%s'
              % (clr, socket, t, deg, pred_s, flag))
        if abs(clr - TODAY['hex']) < 1e-9:
            today_deg = deg
        # a socket that jammed is not a candidate, however little it rocked
        if t > 0.05 and (best is None or deg < best[1]):
            best = (clr, deg)
    return best, today_deg


def report_cost(best, today_deg):
    if best is None:
        return
    rule('4. WHAT THE HEX COSTS AT THE BLADES')
    rows = []
    if today_deg is not None:
        rows.append(('as it ships', 'clearance %.2f' % TODAY['hex'], today_deg))
    rows.append(('tightest that assembled', 'clearance %.2f' % best[0], best[1]))
    for tag, label, deg in rows:
        worst = sq = 0.0
        for arm in ARMS.values():
            mm_ = math.radians(deg + SERVO_GEAR_DEG) * arm
            worst += mm_
            sq += mm_ * mm_
        print('  %-24s %-18s hex %.2f deg + servo %.2f'
              % (tag, label, deg, SERVO_GEAR_DEG))
        print('  %-24s worst case %5.1f mm | RSS %5.1f mm'
              % ('', worst, math.sqrt(sq)))
    print('')
    print('  Servo gearbox backlash is an ASSUMPTION (%.2f deg). It is now the'
          % SERVO_GEAR_DEG)
    print('  largest unmeasured term left in this budget.')


def report_bearings():
    rule('5. THE BEARING SEATS - swept, because "does it spin" is a hand test')
    spins = MEASURED['seat_spins']
    any_measured = any(v is not None for v in spins.values())
    for d in sorted(spins):
        v = spins[d]
        tag = 'NOT TESTED' if v is None else ('SPINS' if v else 'DRAGS')
        flag = '  <- turntable_stator uses this' if abs(d - TODAY['seat']) < 1e-9 else ''
        print('  seat %-5.1f  %-11s%s' % (d, tag, flag))
    if any_measured:
        good = [d for d, v in spins.items() if v]
        if not good:
            print('')
            print('  NONE of them spin. That is not a seat-diameter problem -')
            print('  suspect the axle, the shoulder squareness, or elephant foot')
            print('  on the first layer of the seat. Check the FLAT result below')
            print('  before changing any seat diameter.')
        else:
            print('')
            print('  Widest that spins: %.1f. Anything wider is reaching over the'
                  % max(good))
            print('  gap toward the ZZ shield, which is fixed to the OUTER race.')
            if max(good) < TODAY['seat']:
                print('  turntable_stator ships %.1f and that DRAGS -> change it.'
                      % TODAY['seat'])

    print('')
    if MEASURED['flat_bare_d'] is None:
        print('  lying-down stub: NOT MEASURED. This is the one that matters -')
        print('  turntable_stator prints its roller axles horizontally and their')
        print('  undersides droop with nothing to bridge onto.')
    else:
        d = MEASURED['flat_bare_d']
        print('  lying-down stub measured %.2f against 7.90 drawn (%+.3f).'
              % (d, d - 7.90))
        if d > 8.00:
            print('  It will not enter a 608 bore (8.00) at all - the axles in')
            print('  turntable_stator need to be drawn UNDER size by this much.')
    fs = MEASURED['flat_seat_spins']
    if fs is None:
        print('  lying-down seat spin test: NOT TESTED')
    else:
        print('  lying-down seat: %s' % ('SPINS' if fs else 'DRAGS'))
        if not fs and any(MEASURED['seat_spins'].get(11.0, False) for _ in [0]):
            print('  Standing up it spins and lying down it does not: the droop')
            print('  is the problem, not the seat diameter.')


def report_pilots():
    rule('6. THE PILOTS - swept, because the test destroys the hole')
    for key, label, today_val in (('m3_pilot_best', 'M3 self-tap pilot', 2.5),
                                  ('m2_pilot_best', 'M2 servo pilot', 1.8)):
        v = MEASURED[key]
        if v is None:
            print('  %-22s NOT MEASURED' % label)
            continue
        moved = '' if abs(v - today_val) < 1e-9 else \
            '   CHANGED from %.2f -> update lib/design_rules.py' % today_val
        print('  %-22s %.2f%s' % (label, v, moved))


def report_targets(boss, bore, trustworthy):
    rule('7. DESIGNING TO A TARGET ON THIS PRINTER')
    if len(boss) < 2 or len(bore) < 2:
        print('  Needs section 1.')
        return
    print('  To get a REAL clearance of X at diameter d, draw X - shift(d).')
    print('  The shift is diameter-dependent, which is the whole reason the')
    print('  truth row has three bores instead of one.')
    print('')
    print('  %8s %10s %10s %10s %10s' % ('dia', 'shift', 'real 0.05',
                                         'real 0.20', 'real 0.35'))
    for d in (4.0, 8.0, 12.0, 20.0, 22.0):
        shift = interp(bore, d) - interp(boss, d)
        print('  %8.1f %+10.3f %10.3f %10.3f %10.3f'
              % (d, shift, 0.05 - shift, 0.20 - shift, 0.35 - shift))
    print('')
    if not trustworthy:
        print('  Section 1 flagged the bias as non-linear - the :4 and :22 rows')
        print('  above are extrapolations off the ends of the measured range.')
    print('  Then re-run models/robotarm/_check_ledger.py: a shared fit value')
    print('  touches all thirteen parts, and the ledger is what proves that')
    print('  changing one did not quietly reshape another.')
    print('')


def main():
    boss, bore, trustworthy = report_truth()
    report_scale(boss)
    report_derived(boss, bore, trustworthy)
    best, today_deg = report_hex()
    report_cost(best, today_deg)
    report_bearings()
    report_pilots()
    report_targets(boss, bore, trustworthy)


if __name__ == '__main__':
    main()
