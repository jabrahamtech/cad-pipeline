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

from lib.gears import J3_PAIR as _J3_PAIR

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

# --- joint reductions -------------------------------------------------------
# A SERVO DOES NOT ALWAYS DRIVE ITS JOINT 1:1, AND THIS FILE USED TO ASSUME IT
# DID. J3 has run through a printed 2:1 spur pair since 2026-08-30 - three
# parts, a gate and a forearm rework - and none of it was visible here, so
# this model would have gone on reporting the elbow at 87 % of duty while the
# hardware was at half that. That is the project's recurring failure in its
# usual shape: a datum that only the files which CUT it ever read.
#
# The ratio is imported, not typed. If someone changes J3_PAIR's tooth counts
# the number here moves with them or the import fails.
#
# EFFICIENCY IS ASSUMED, AND IT IS THE WEAK NUMBER IN THIS BLOCK. 0.90 for a
# single printed spur mesh, PETG on PETG, running dry. A machined steel pair
# would be 0.97-0.99; printed plastic is rougher, and this has NOT been
# measured on the bench. It is deliberately pessimistic - if the real pair is
# better, the joint has more margin than reported, which is the direction an
# unmeasured number should err in.
MESH_EFFICIENCY = 0.90

REDUCTION = {
    'J3': {'ratio': _J3_PAIR.ratio,
           'efficiency': MESH_EFFICIENCY,
           'what': 'printed %dT/%dT spur pair, lib/gears.py J3_PAIR'
                   % (_J3_PAIR.z_pinion, _J3_PAIR.z_gear)},
}


def joint_reduction(joint):
    """(ratio, efficiency) between a joint's servo and the joint itself."""
    r = REDUCTION.get(joint)
    return (r['ratio'], r['efficiency']) if r else (1.0, 1.0)


def duty_at_joint_kgcm(joint):
    """What the servo will HOLD at the joint, after any reduction.

    Torque multiplies by the ratio and is spent by the mesh; TRAVEL divides
    by the ratio, which is the other half of the same trade and is reported
    alongside so nobody reads the torque win without the travel cost.
    """
    ratio, eff = joint_reduction(joint)
    return DUTY_KGCM[joint] * ratio * eff


def travel_at_joint_deg(joint, servo_travel_deg=180.0):
    ratio, _ = joint_reduction(joint)
    return servo_travel_deg / ratio

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
    ratio, eff = joint_reduction(joint)
    duty_gcm = duty_at_joint_kgcm(joint) * 1000.0
    frac = required_gcm / duty_gcm if duty_gcm else float('inf')
    return {
        'joint': joint,
        'required_gcm': required_gcm,
        'required_kgcm': required_gcm / 1000.0,
        'duty_kgcm': duty_at_joint_kgcm(joint),
        'servo_duty_kgcm': DUTY_KGCM[joint],
        'stall_kgcm': STALL_KGCM[joint],
        'ratio': ratio,
        'efficiency': eff,
        'reduction': REDUCTION.get(joint, {}).get('what', 'direct drive'),
        'travel_deg': travel_at_joint_deg(joint),
        'fraction': frac,
        'margin': (duty_gcm / required_gcm) if required_gcm else float('inf'),
        'over': frac > 1.0,
        'estimated_items': [i.name for i in items if i.source == 'ESTIMATED'],
    }


# --- J1 yaw: the one joint gravity does not load ----------------------------
# _assembly.md has rated J1 as "inertia + friction only" since it was written
# and NOTHING EVER COMPUTED IT. That is an assertion, not a number, and the
# question "should J1 be geared" cannot be answered without it - a reduction
# there costs yaw travel 1:1, so it has to be bought with something real.
#
# Gravity produces no moment about a vertical axis, so the load is:
#   inertia   I * alpha, with I = sum(m r^2) about the yaw axis
#   friction  three 608ZZ under the rotating weight, plus seal drag
#
# THE MOMENT ARM IS NOT THE SAME ONE THE PITCH JOINTS USE. About J2 an item's
# arm is its distance along the arm; about J1 it is its HORIZONTAL distance
# from the yaw axis. With the arm straight out and J2 sitting on the yaw axis
# those coincide, which is the worst case and the one used here. Fold the arm
# and I falls; that is why this is computed straight out.

# Rolling friction of a deep-groove ball bearing under light load. HANDBOOK
# range is 0.0010-0.0015 for 608-class; the top of it is taken.
BEARING_ROLLING_MU = 0.0015
# ZZ shields drag. ASSUMED - not measured, and it is the weak number here.
# Small against the inertia term, which is what this calculation is for.
SHIELD_DRAG_NMM_EACH = 0.15


def yaw_inertia_gmm2(items):
    """Second moment of the rotating mass about the yaw axis, in g.mm^2.

    Takes the same Item list the pitch joints use. Their radius_mm is the
    horizontal distance from the axis when the arm is straight out, which is
    exactly what is wanted here.
    """
    return sum(i.mass_g * i.radius_mm ** 2 for i in items)


def yaw_slew_report(items, sweep_deg=90.0, seconds=1.0, roller_r_mm=27.0,
                    n_rollers=3):
    """What J1 must produce to slew `sweep_deg` in `seconds`, and hold.

    Triangular velocity profile - accelerate for half the move, decelerate
    for the other half - so peak alpha = 4 * theta / t^2. That is the
    textbook worst case for a point-to-point move and it needs no guess
    about the servo's internal profile.
    """
    I_gmm2 = yaw_inertia_gmm2(items)
    I_kgm2 = I_gmm2 * 1e-9
    theta = math.radians(sweep_deg)
    alpha = 4.0 * theta / (seconds ** 2)            # rad/s^2
    t_inertia_nm = I_kgm2 * alpha

    mass_g = sum(i.mass_g for i in items)
    weight_n = to_newtons(mass_g)
    roll_nm = (BEARING_ROLLING_MU * weight_n * (roller_r_mm / 1000.0))
    drag_nm = n_rollers * SHIELD_DRAG_NMM_EACH / 1000.0
    t_friction_nm = roll_nm + drag_nm

    total_nm = t_inertia_nm + t_friction_nm
    return {
        'inertia_gmm2': I_gmm2,
        'mass_g': mass_g,
        'alpha_rad_s2': alpha,
        'inertia_kgcm': t_inertia_nm / 9.80665 * 100.0,
        'friction_kgcm': t_friction_nm / 9.80665 * 100.0,
        'inertia_nm': t_inertia_nm,
        'friction_nm': t_friction_nm,
        'total_nm': total_nm,
        'total_kgcm': total_nm / 9.80665 * 100.0,
        'duty_kgcm': duty_at_joint_kgcm('J1'),
        'fraction': (total_nm / 9.80665 * 100.0) / duty_at_joint_kgcm('J1'),
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
