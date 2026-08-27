"""The load model, as pure arithmetic. No Fusion, no geometry kernel.

`models/robotarm/_check_loads.py` harvests real mass properties out of Fusion
and hands them here; this file turns them into joint moments and section
stresses and says whether anything is over its limit. Split that way on
purpose: the measuring needs Fusion and cannot be tested, the arithmetic needs
nothing and is tested by `tests/test_arm_loads.py`.

WHAT THIS REPLACES
------------------
`_assembly.md` has promised `_check_loads.py` since it was written, and until
now `lib/arm_budget.py` stood in for it. arm_budget is a good parametric model
with one honest weakness it states itself: its link masses are back-calculated
from two volumes and its cluster masses are the ESTIMATED figures out of
_assembly.md's table. This reads every mass off the built body instead.

It does NOT replace arm_budget. arm_budget answers "what would L1=70 cost?" -
a question about geometry that does not exist yet. This one answers "what does
the arm on disk actually weigh, and does it hold" - a question about geometry
that does. Both are wanted; they validate against each other.

THE MODEL, AND ITS ONE BIG ASSUMPTION
-------------------------------------
Everything outboard of a joint is a set of point masses at fixed radii from
that joint's axis, in the worst pose: **arm laid straight out horizontal,
payload gripped**. Gravity is perpendicular to every link, so each item's
moment is simply m x r and they sum.

The assumption inherited from arm_budget, and still an assumption here: the
outboard CLUSTER's offsets are rigid. Shortening L2 translates the whole
cluster inboard rather than rescaling it. True for the built parts. If a new
head changes where the wrist stack sits, these offsets move and nothing here
will notice.

UNITS. Masses in GRAMS, lengths in MILLIMETRES, moments in g.mm internally and
reported in both g.cm and kg.cm. arm_budget works in g.cm and reported the arm
at 873 % of duty the first time it mixed the two. Every name here carries its
unit and nothing is compared across units without a conversion on the line.
"""

import math

# --- what a gram of printed plastic actually weighs -------------------------
# Identical to lib/arm_budget.py, deliberately: if these two files disagree
# about density then one of them is lying about every mass it prints.
FUSION_PET_DENSITY = 1.541      # g/cm3 - Fusion's 'PET Plastic'
PETG_FILAMENT_DENSITY = 1.27    # g/cm3 - real filament
REAL_INFILL = 0.65              # measured off the gauge_fits v4 slice
SOLID_TO_PRINTED = PETG_FILAMENT_DENSITY * REAL_INFILL / 1000.0
#   volume_mm3 * SOLID_TO_PRINTED = printed grams

# --- servo duty -------------------------------------------------------------
# Duty limit = stall x 0.5 (knowledge/motion_mechanisms.md: stall is a PEAK
# rating; held above half of it they run hot, buzz and strip).
STALL_KGCM = {'J1': 1.6, 'J2': 9.4, 'J3': 2.0, 'J4': 2.0, 'J5': 1.6}
DUTY_FRACTION = 0.5
DUTY_KGCM = {k: v * DUTY_FRACTION for k, v in STALL_KGCM.items()}

# --- material, for the section checks ---------------------------------------
# knowledge/loads_strength.md "Verifying without FEA": sigma = M.c/I against
# ~35 MPa in-plane, x Z_TENSILE_FACTOR if the load crosses layers, / safety.
PETG_SIGMA_MPA = 35.0           # HANDBOOK, in-plane
Z_TENSILE_FACTOR = 0.5          # design_rules - layer adhesion vs in-plane
SAFETY_STATIC = 2.0             # design_rules SAFETY_FACTOR['static']

G_MM_PER_S2 = 9806.65           # gravity, mm/s2 - only for N conversions


def printed_g(volume_mm3):
    """Volume of a built body -> what it weighs printed, in grams."""
    return volume_mm3 * SOLID_TO_PRINTED


def to_newtons(grams):
    return grams / 1000.0 * G_MM_PER_S2 / 1000.0


class Item(object):
    """One point mass at a radius from the joint being summed about."""

    def __init__(self, name, mass_g, radius_mm, source):
        assert source in ('MEASURED', 'BOUGHT', 'ESTIMATED', 'PAYLOAD'), source
        self.name = name
        self.mass_g = float(mass_g)
        self.radius_mm = float(radius_mm)
        self.source = source

    @property
    def moment_gmm(self):
        return self.mass_g * self.radius_mm

    @property
    def moment_gcm(self):
        return self.moment_gmm / 10.0


def joint_moment(items):
    """Sum of m x r, in g.cm. Worst pose: everything horizontal."""
    return sum(i.moment_gcm for i in items)


def duty_report(joint, items):
    """What this joint is asked for, against what its servo will hold."""
    assert joint in DUTY_KGCM, 'no duty figure for %s' % joint
    required_gcm = joint_moment(items)
    duty_gcm = DUTY_KGCM[joint] * 1000.0
    frac = required_gcm / duty_gcm if duty_gcm else float('inf')
    return {
        'joint': joint,
        'required_gcm': required_gcm,
        'required_kgcm': required_gcm / 1000.0,
        'duty_kgcm': DUTY_KGCM[joint],
        'stall_kgcm': STALL_KGCM[joint],
        'fraction': frac,
        'margin': (duty_gcm / required_gcm) if required_gcm else float('inf'),
        'over': frac > 1.0,
        'estimated_items': [i.name for i in items if i.source == 'ESTIMATED'],
    }


# --- section checks ---------------------------------------------------------

def rect_section_modulus_mm3(width_mm, height_mm):
    """Z = I/c for a solid rectangle bent about its width axis."""
    return width_mm * height_mm ** 2 / 6.0


def annulus_section_modulus_mm3(d_out_mm, d_in_mm):
    """Z for a round tube. d_in 0 gives a solid rod."""
    r_o, r_i = d_out_mm / 2.0, d_in_mm / 2.0
    i_mm4 = math.pi / 4.0 * (r_o ** 4 - r_i ** 4)
    return i_mm4 / r_o


def bending_stress_mpa(moment_nmm, section_modulus_mm3):
    assert section_modulus_mm3 > 0, 'zero section modulus'
    return moment_nmm / section_modulus_mm3


def stress_check(name, moment_nmm, section_modulus_mm3, across_layers,
                 safety=SAFETY_STATIC):
    """sigma against the allowable, with the layer direction stated.

    ACROSS LAYERS IS NOT A DETAIL. An FDM part is a laminate at roughly half
    strength across the layer boundaries, so the same section is twice as
    strong depending only on which way it was printed. Every caller states it.
    """
    sigma = bending_stress_mpa(moment_nmm, section_modulus_mm3)
    allow = PETG_SIGMA_MPA * (Z_TENSILE_FACTOR if across_layers else 1.0)
    allow_with_safety = allow / safety
    return {
        'name': name,
        'sigma_mpa': sigma,
        'allowable_mpa': allow,
        'allowable_with_safety_mpa': allow_with_safety,
        'utilisation': sigma / allow_with_safety,
        'across_layers': across_layers,
        'safety': safety,
        'over': sigma > allow_with_safety,
    }


def roller_share(total_rotating_g, n_rollers=3):
    """Load per 608 when the turret's whole rotating mass sits on them.

    Evenly split is the OPTIMISTIC case and it is what this returns. Three
    points on a circle carrying an arm that reaches out to one side do not
    share evenly - the roller under the reach takes more. `worst_roller_g`
    below is the number to design to.
    """
    return total_rotating_g / float(n_rollers)


def worst_roller_g(total_rotating_g, overturning_gmm, roller_r_mm,
                   n_rollers=3):
    """The loaded roller's share when the arm reaches out over one of them.

    TAKES THE REAL OVERTURNING MOMENT, not mass x reach. The first version of
    this multiplied the WHOLE rotating mass by the FULL reach, which put the
    47 g shoulder bracket - sitting on the yaw axis, at zero radius - out at
    178 mm with everything else. It reported one roller carrying 1038 g under
    a 219 g arm: 4.7x the entire load above it, on one of three supports.
    A reaction larger than the total applied load is not conservatism, it is
    a wrong answer, and it would have been believed because it was labelled
    conservative. Pass sum(m.r), which is what the joint budget already has.

    For n supports equally spaced on radius R under a moment M, the reactions
    vary as cos(theta) and the largest is 2M/(nR). At n=3 that is M/(1.5R),
    and it ADDS to that support's share of the dead weight.
    """
    dead_share = total_rotating_g / float(n_rollers)
    transfer = 2.0 * overturning_gmm / (n_rollers * roller_r_mm)
    return dead_share + transfer
