"""robotarm/_export_turret - export the J1 turret for printing.

Three parts: turntable_stator, turntable_ring, base_lid. The rotor is
shoulder_bracket and is NOT here - it is J2's fork as well, and it does not
print until the MG995 in hand has been measured (two vendor drawings disagree
on the tab pitch and the horn hub, and either would force a rebuild).

WHY THESE THREE, AND WHY NOW. Their gate passes on geometry: _check_j1 sweeps
-90..+90 in 15 deg steps at 0.000 mm3 of interference, _check_loads puts the
roller stub at 4 % of allowable, and they sit on a platter that is already
printed and in hand. They settle the riskiest open claim in the project - that
J1 turns at all - for about 2 hours of plastic instead of after a full build.

THE RISK THIS PRINT IS BUYING AN ANSWER TO, stated up front so a failure is a
result rather than a surprise: the ring's 0.40 mm of daylight over the rotor
rim is built from two printed Z surfaces at DIM_TOL_Z 0.25 each. Stack them
the wrong way and the ring clamps the rotor and J1 will not turn. The
mitigation is designed in - sand or shim at the three posts.

Never overwrite a version that may have been printed; bump VERSION instead.
v1: first export, 2026-08-27 morning. v2: the flange audit narrowed the
SG90 pocket (ts_case_w 12.6 -> 12.2, case_l 22.7). v3, same day: the HORN
audit - hub 3.0 (was 3.8), blade 2.0 (was 1.5) raised the deck 1.4 and
recut the rotor cross pocket 32.8 x 3.4 x 2.4 with a Ø13 root relief, and
a lead groove in the plate underside keeps the (now higher) lead clear.
v4, 2026-08-28: the horn plate went to the bench and the arms are 4.0 wide
at their NARROWEST against a 3.4 slot - the cross pocket never accepted the
horn. Slots are now TAPERED to the measured arm (6.04 at r 6.5 -> 4.84 at
the trim line). v5, same day: the hub sweeps overshot too - the micro horn hub measures
6.8, not the modelled 8.0 (and the PRE-audit 7.0 was closer). The rotor's
screw bore and the stator deck follow it. PRINT v5. v1-v3 have a cross
pocket no real horn enters; v4 has the taper but the old hub.
"""

import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
EXPORT_DIR = os.path.join(REPO, 'exports', 'robotarm')
VERSION = 5

# name, print orientation, note
PARTS = [
    ('turntable_stator', 'FLAT, base down, cheeks and posts UP',
     'the stub axles then grow sideways off the cheeks as horizontal '
     'cylinders - the one real overhang, and short enough to bridge. '
     'SUPPORTS OFF: that bridge is load-bearing and support scars it.'),
    ('turntable_ring', 'FLAT - it is an annulus, there is no second option',
     'no support anywhere. The bore is the J1 journal: do not sand it.'),
    ('base_lid', 'FLAT, 3 mm plate',
     'brim ON - it is 171.75 across and 3 thick, and it will warp without '
     'one. No support.'),
]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    comps = {}
    occs = {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in comps:
            comps[n] = occ.component
            occs[n] = occ

    os.makedirs(EXPORT_DIR, exist_ok=True)
    em = design.exportManager
    written = []
    total_mm3 = 0.0

    for name, orientation, note in PARTS:
        full = 'robotarm_' + name
        assert full in comps, (
            '%s is not in this document - build it first' % full)
        comp = comps[full]
        assert comp.bRepBodies.count == 1, (
            '%s has %d bodies; an export must be one solid'
            % (name, comp.bRepBodies.count))
        body = comp.bRepBodies.item(0)
        assert body.isValid, '%s is not a valid body' % name
        # A HIDDEN OCCURRENCE EXPORTS AS AN EMPTY FILE. Fusion's STEP/3MF
        # export silently skips occurrences whose light bulb is off, and the
        # gates toggle bulbs while posing - the first v2 export shipped three
        # 3.7 KB headers this way. Force it visible; the old 1000-byte floor
        # below let the empty files through, hence the tighter one.
        if not occs[full].isLightBulbOn:
            occs[full].isLightBulbOn = True
        assert occs[full].isLightBulbOn, '%s stays hidden - export would be empty' % name

        base = os.path.join(EXPORT_DIR, '%s_v%d' % (name, VERSION))
        # NEVER overwrite a version that may have been printed.
        assert not os.path.exists(base + '.step'), (
            '%s.step exists - bump VERSION rather than overwrite a part that '
            'may already be on a bed' % base)
        assert not os.path.exists(base + '.3mf'), (
            '%s.3mf exists - bump VERSION' % base)

        em.execute(em.createSTEPExportOptions(base + '.step', comp))
        em.execute(em.createC3MFExportOptions(comp, base + '.3mf'))

        vol = body.volume * 1000.0
        total_mm3 += vol
        # A 3MF that came out tiny means the export took an empty component.
        step_b = os.path.getsize(base + '.step')
        mf_b = os.path.getsize(base + '.3mf')
        assert step_b > 20000 and mf_b > 20000, (
            '%s exported %d / %d bytes - that is an empty file, not a part'
            % (name, step_b, mf_b))
        written.append((name, vol, step_b, mf_b, orientation, note))

    print('=== J1 turret, exported v%d ===' % VERSION)
    print('')
    for name, vol, step_b, mf_b, orientation, note in written:
        print('%s_v%d' % (name, VERSION))
        print('  %.0f mm3 solid | %.1f g printed PETG at 1.27 x 0.65'
              % (vol, vol * 1.27 * 0.65 / 1000.0))
        print('  STEP %d bytes | 3MF %d bytes' % (step_b, mf_b))
        print('  ORIENT: %s' % orientation)
        print('  %s' % note)
        print('')
    print('total %.0f mm3 = %.1f g of PETG'
          % (total_mm3, total_mm3 * 1.27 * 0.65 / 1000.0))
    print('')
    print('PRINT SETTINGS - the same profile the gauge was printed on, or the')
    print('  fits stop meaning anything: PETG, 0.2 layers, 3 walls, 15-20%')
    print('  infill, SUPPORTS OFF on all three.')
    print('')
    print('BOUGHT PARTS NEEDED TO ASSEMBLE THIS:')
    print('  3 x 608ZZ            (have 6)')
    print('  1 x SG90             (have 3)')
    print('  3 x M3 x 40 socket   ring -> post -> platter insert. LONGER THAN')
    print('                       A TYPICAL ASSORTMENT HOLDS - check first.')
    print('  3 x M3 x 12          the roller axle screws')
    print('  3 x printed washer   roller_cap, on the gauge plate. A standard')
    print('                       M3 washer is Ø7 and falls THROUGH a 608 bore.')
    print('')
    print('WHAT THIS PRINT IS TESTING, in order of what would bite:')
    print('  1. the ring\'s 0.40 daylight over the rim - two printed Z faces')
    print('     at 0.25 tolerance each. If the ring clamps the rotor, sand or')
    print('     shim at the three posts. MOST LIKELY SINGLE FAILURE.')
    print('  2. whether a 608 sits on the stub at all - the plate says the')
    print('     printed 7.9 runs LOOSE in an 8.0 bore.')
    print('  3. whether the SG90 horn hub clears tt_screw_bore Ø6.00. That')
    print('     diameter is the one invented number in the J1 gate.')
    print('  4. the platter column, 12.45 x 23.05 UNVERIFIED against a 12.20')
    print('     SG90 case. Caliper it before pressing the servo in.')
