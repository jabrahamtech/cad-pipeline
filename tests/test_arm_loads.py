"""Headless tests for lib/arm_loads.py.

The Fusion half of the load gate cannot be tested - it needs adsk. The
arithmetic half is why lib/arm_loads.py exists as a separate module, and this
is the payment for that split.

The important test is test_reproduces_assembly_md_figure. lib/arm_budget.py
earns its trust by reproducing _assembly.md's published 873.7 g.cm to within
0.5; this module has to agree with arm_budget on the same inputs, or the two
files are modelling different arms and at least one of them is wrong.
"""

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from lib import arm_loads as al          # noqa: E402


def test_density_matches_arm_budget():
    """If these two disagree, every mass in the project is wrong somewhere."""
    from lib import arm_budget as ab
    assert al.PETG_FILAMENT_DENSITY == ab.PETG
    assert al.REAL_INFILL == ab.REAL_INFILL
    assert al.FUSION_PET_DENSITY == ab.FUSION_PET


def test_printed_g_against_a_known_part():
    """shoulder_bracket is 57260 mm3 and its script prints ~52.9 g at Fusion
    density x 0.6. At real PETG x 0.65 it must come out ~12 % LIGHTER."""
    g = al.printed_g(57260.0)
    assert 46.0 < g < 49.0, g
    fusion_figure = 57260.0 * al.FUSION_PET_DENSITY * 0.60 / 1000.0
    assert g / fusion_figure == pytest.approx(0.893, abs=0.01)


def test_moment_is_mass_times_radius():
    i = al.Item('x', 10.0, 100.0, 'MEASURED')
    assert i.moment_gmm == 1000.0
    assert i.moment_gcm == 100.0


def test_duty_limit_is_half_stall():
    for k in al.STALL_KGCM:
        assert al.DUTY_KGCM[k] == al.STALL_KGCM[k] * 0.5


def test_duty_report_flags_over():
    """An MG90S at J4 holds 1.0 kg.cm DIRECT. 1.5 must report OVER."""
    items = [al.Item('lump', 150.0, 100.0, 'ESTIMATED')]   # 1500 g.cm
    r = al.duty_report('J4', items)
    assert r['required_kgcm'] == pytest.approx(1.5)
    assert r['over'] is True
    assert r['estimated_items'] == ['lump']


# --- the J3 reduction. These exist because the model did NOT know about it --
# for three commits after the gear train was built and gated, and would have
# gone on reporting the elbow at 87 % of duty while the hardware sat at half
# that. A ratio that only the parts CUT FROM it ever read is not a contract.

def test_direct_drive_joints_are_untouched():
    for j in ('J1', 'J2', 'J4', 'J5'):
        assert al.joint_reduction(j) == (1.0, 1.0)
        assert al.duty_at_joint_kgcm(j) == pytest.approx(al.DUTY_KGCM[j])
        assert al.travel_at_joint_deg(j) == pytest.approx(180.0)


def test_j3_ratio_comes_from_the_gear_pair_not_a_typed_number():
    from lib.gears import J3_PAIR
    ratio, eff = al.joint_reduction('J3')
    assert ratio == pytest.approx(J3_PAIR.ratio)
    assert ratio == pytest.approx(J3_PAIR.z_gear / float(J3_PAIR.z_pinion))
    assert 0.0 < eff <= 1.0


def test_j3_reduction_multiplies_duty_and_spends_it_on_the_mesh():
    ratio, eff = al.joint_reduction('J3')
    assert al.duty_at_joint_kgcm('J3') == pytest.approx(
        al.DUTY_KGCM['J3'] * ratio * eff)
    # and it is strictly better than direct drive, or it is not worth having
    assert al.duty_at_joint_kgcm('J3') > al.DUTY_KGCM['J3']


def test_the_reduction_costs_travel_and_says_so():
    ratio, _ = al.joint_reduction('J3')
    assert al.travel_at_joint_deg('J3') == pytest.approx(180.0 / ratio)
    assert al.travel_at_joint_deg('J3') < 180.0


def test_a_load_over_duty_direct_is_within_duty_geared():
    """The whole point of the elbow reduction, as one assertion.

    1.5 kg.cm is over an MG90S driving direct - see the J4 case above - and
    within it through the J3 pair. If this ever stops being true the pair is
    not earning the travel it costs.
    """
    items = [al.Item('lump', 150.0, 100.0, 'MEASURED')]     # 1500 g.cm
    assert al.duty_report('J4', items)['over'] is True
    r = al.duty_report('J3', items)
    assert r['over'] is False
    assert r['ratio'] == pytest.approx(2.0)
    assert 'spur pair' in r['reduction']


def test_duty_report_surfaces_estimated_items():
    """A budget built on estimates must SAY so - the whole point of the
    source tag is that a measured-looking table cannot hide a guess."""
    items = [al.Item('real', 10.0, 10.0, 'MEASURED'),
             al.Item('guess', 10.0, 10.0, 'ESTIMATED')]
    assert al.duty_report('J3', items)['estimated_items'] == ['guess']


def test_rect_section_modulus():
    assert al.rect_section_modulus_mm3(6.0, 10.0) == pytest.approx(100.0)


def test_annulus_reduces_to_solid_rod():
    d = 8.0
    z = al.annulus_section_modulus_mm3(d, 0.0)
    assert z == pytest.approx(math.pi * d ** 3 / 32.0)


def test_across_layers_halves_the_allowable():
    """The anisotropy law, and it must actually bite."""
    inp = dict(name='x', moment_nmm=100.0, section_modulus_mm3=10.0)
    within = al.stress_check(across_layers=False, **inp)
    across = al.stress_check(across_layers=True, **inp)
    assert across['allowable_mpa'] == within['allowable_mpa'] * 0.5
    assert across['utilisation'] == within['utilisation'] * 2.0


def test_stress_check_applies_safety_factor():
    s = al.stress_check('x', 100.0, 10.0, across_layers=False, safety=2.0)
    assert s['sigma_mpa'] == pytest.approx(10.0)
    assert s['allowable_with_safety_mpa'] == pytest.approx(17.5)
    assert s['over'] is False


def test_worst_roller_exceeds_even_share():
    """The whole reason worst_roller_g exists. If it ever returns the even
    share, the overturning term has been lost and the turret is being
    designed to the optimistic case."""
    even = al.roller_share(300.0)
    worst = al.worst_roller_g(300.0, overturning_gmm=16500.0, roller_r_mm=27.0)
    assert worst > even
    assert worst == pytest.approx(100.0 + 2.0 * 16500.0 / (3 * 27.0))


def test_worst_roller_cannot_exceed_total_load():
    """The bug this signature was changed to prevent. One of three supports
    reacting more than the entire applied load is arithmetically impossible;
    the first version reported 1038 g under a 219 g arm because it was handed
    mass x full-reach instead of sum(m.r)."""
    total_g = 219.4
    # every gram at the very tip - the most extreme real case there is
    overturning = total_g * 178.0
    worst = al.worst_roller_g(total_g, overturning, roller_r_mm=27.0)
    assert worst > total_g, 'a tip-loaded arm does overload one roller'
    # and with a REALISTIC distribution it must be a fraction of the total
    realistic = al.worst_roller_g(total_g, 16500.0, roller_r_mm=27.0)
    assert realistic < total_g * 3.0, realistic


def test_reproduces_assembly_md_figure():
    """Cross-check against lib/arm_budget.py on the arm as built.

    arm_budget validates itself against _assembly.md's published 873.7 g.cm.
    Both files sum m x r over the same cluster in the same pose, so on the
    same inputs they must agree. They are allowed to differ by the density
    correction and nothing else.
    """
    from lib import arm_budget as ab

    # arm_budget's own gate first. VALIDATION is the OLD geometry the
    # published figure belongs to - NOT BUILT, which is today's arm. Pairing
    # those two is a 33 % error and is what this test caught.
    ab_moment = ab.validate()

    ref = ab.VALIDATION
    items = []
    for name, mass_g, offset_mm, bought in ab.CLUSTER:
        items.append(al.Item(name, mass_g, ref['l2'] + offset_mm,
                             'BOUGHT' if bought else 'MEASURED'))
    # the HISTORICAL head offset, for exactly the reason spelled out three
    # lines down about the COM fraction: this test compares two
    # IMPLEMENTATIONS on identical inputs, and validate() computes with the
    # historical constants. Feeding one side today's 45.5 and the other 47.0
    # makes them disagree about the arm rather than about the arithmetic.
    items.append(al.Item('head', ref['head_g'],
                         ref['l2'] + ab.VALIDATION_HEAD_OFFSET_MM, 'MEASURED'))
    # the HISTORICAL fraction, matching what validate() computes with. Using
    # the live constant here would make this test fail the moment a COM is
    # measured, which is the opposite of what it is for.
    items.append(al.Item('forearm', ab.FOREARM_G_PER_MM * ref['l2'],
                         ref['l2'] * ab.VALIDATION_FOREARM_COM_FRAC,
                         'MEASURED'))
    al_moment = al.joint_moment(items)

    assert al_moment == pytest.approx(ab_moment, rel=0.001), (
        'arm_loads and arm_budget disagree on the same cluster: %.2f vs '
        '%.2f g.cm - they are modelling different arms'
        % (al_moment, ab_moment))


def test_measured_com_fracs_differ_from_the_historical_one():
    """The upgrade itself, pinned. FOREARM_COM_FRAC is now measured and must
    NOT silently fall back to the table figure the published moment used."""
    from lib import arm_budget as ab
    assert ab.FOREARM_COM_FRAC != ab.VALIDATION_FOREARM_COM_FRAC
    assert ab.FOREARM_COM_FRAC == pytest.approx(0.4686, abs=0.001)
    assert ab.UPPERARM_COM_FRAC == pytest.approx(0.5000, abs=0.001)


def test_validate_ignores_the_live_com_frac():
    """validate() proves the ARITHMETIC reproduces the published table. If it
    read the live constants it would break every time a mass is measured -
    punishing exactly the work it exists to protect."""
    from lib import arm_budget as ab
    before = ab.FOREARM_COM_FRAC
    ab.FOREARM_COM_FRAC = 0.9          # nonsense, deliberately
    try:
        ab.validate()                  # must still pass
    finally:
        ab.FOREARM_COM_FRAC = before


def test_built_and_validation_are_different_arms():
    """The trap itself, pinned. If someone re-pairs BUILT with the published
    figure these must not silently agree."""
    from lib import arm_budget as ab
    assert ab.BUILT['l2'] != ab.VALIDATION['l2']
    built_moment = ab.j3_moment(ab.BUILT['l2'], ab.BUILT['head_g'],
                                ab.BUILT['section'], correct_density=False)[0]
    assert abs(built_moment - ab.VALIDATION_J3_TARGET) > 100.0, (
        'BUILT now reproduces the OLD published figure, which means either '
        'the links changed back or the target was updated without its '
        'geometry')
