"""Single source of truth for printer limits and design rules.

Provenance discipline:
- CALIBRATED — measured on THIS Bambu Lab X2D via gauge prints recorded in
  calibration/. Never change without a test print.
- HANDBOOK — standard FDM guidance seeded 2026-08-25. Trust for first
  prints of non-critical fits; for any critical fit, verify with a gauge
  print and promote to CALIBRATED with a calibration/ entry.

CLAUDE.md "Design rules" mirrors the headline values; the topic files in
knowledge/ explain how to APPLY these numbers. Scripts mirror the values
they use as Fusion user parameters with a provenance comment.
"""

# --- printability minimums (0.4 mm nozzle) -------------------------------
MIN_WALL_MM = 1.6                  # CALIBRATED
MIN_FEATURE_MM = 0.8               # CALIBRATED — smallest positive feature
MIN_PIN_DIA_MM = 3.0               # HANDBOOK — standalone printed pin; below
                                   # this use a steel pin / screw as the axle
MIN_EMBOSS_MM = 0.6                # HANDBOOK — text/logo relief width & depth
MAX_OVERHANG_DEG = 50.0            # steeper needs support (aux nozzle)
MAX_BRIDGE_MM = 40.0               # HANDBOOK — longest clean unsupported bridge
ELEPHANT_FOOT_CHAMFER_MM = 0.4     # CALIBRATED — bottom edges

# --- X2D print envelopes (W, D, H) in mm ---------------------------------
ENVELOPE_SINGLE = (256.0, 256.0, 260.0)
ENVELOPE_DUAL = (235.5, 256.0, 256.0)   # when the support nozzle is used

# --- fits: diametral clearance in mm, by JOINT TYPE ----------------------
# The two calibrated anchors (kept as named constants for existing code):
PRESS_FIT_CLEARANCE_MM = 0.15      # CALIBRATED
SLIDING_FIT_CLEARANCE_MM = 0.25    # CALIBRATED

# Every interface in a spec names one of these joint types; the clearance
# comes from here, never invented per-part. knowledge/joints_tolerances.md
# explains selection, direction, and orientation effects.
JOINT_FIT_MM = {
    "press":       0.15,  # CALIBRATED — assembled once, by force, stays put
    "locational":  0.20,  # HANDBOOK — locates precisely, hand assembly,
                          #            removable (lids that register, caps)
    "sliding":     0.25,  # CALIBRATED — translates along an axis in service
    "rotating":    0.35,  # HANDBOOK — printed-on-printed pivot; slow/light
                          #            duty ONLY, else use a bearing
    "free":        0.40,  # HANDBOOK — must never bind (covers, swing doors)
    "bearing_pocket": 0.05,  # HANDBOOK — printed pocket gripping a bearing
                             # outer race; verify by gauge before a big part
}

# Vertical holes print undersize (extrusion bulge). Add this to the DESIGNED
# diameter of Z-axis holes < ~10 mm when the fit matters and the clearance
# above hasn't already absorbed it. XY-facing holes: prefer teardrop/slot.
HOLE_DIA_COMP_MM = 0.2             # HANDBOOK

# --- fasteners (mm) ------------------------------------------------------
# clearance = free through-hole; insert = heat-set hole; pilot = self-tap.
# knowledge/fasteners_inserts.md holds the decision tree and boss recipes.
FASTENER_MM = {          # clearance, insert_hole, pilot, boss_od, nut_af
    "M2":   {"clearance": 2.4, "insert": 3.2, "pilot": 1.8, "boss_od": 6.0, "nut_af": 4.0},
    "M2.5": {"clearance": 2.9, "insert": 3.5, "pilot": 2.2, "boss_od": 7.0, "nut_af": 5.0},
    "M3":   {"clearance": 3.4, "insert": 4.0, "pilot": 2.6, "boss_od": 8.8, "nut_af": 5.5},
    "M4":   {"clearance": 4.5, "insert": 5.6, "pilot": 3.4, "boss_od": 11.0, "nut_af": 7.0},
    "M5":   {"clearance": 5.5, "insert": 6.4, "pilot": 4.3, "boss_od": 12.5, "nut_af": 8.0},
}
# M3 insert values are CALIBRATED (Ø4.0 hole, boss wall >= 2.4); the rest
# are HANDBOOK. Nut pocket: nut_af + 0.2 across flats, nut thickness + 0.4
# deep. Printed threads only at M8+ and coarse — smaller means an insert.
M3_INSERT_HOLE_DIA_MM = 4.0        # CALIBRATED (kept for existing code)
M3_INSERT_BOSS_WALL_MM = 2.4       # CALIBRATED
INSERT_BOSS_WALL_MM = 2.4          # CALIBRATED — min wall around any insert
NUT_POCKET_AF_CLEARANCE_MM = 0.2   # HANDBOOK
PRINTED_THREAD_MIN_DIA_MM = 8.0    # HANDBOOK — below M8, use an insert

# --- structure: strength, stack-up, infill -------------------------------
# knowledge/loads_strength.md, knowledge/tolerance_stackup.md,
# knowledge/dfm_optimization.md explain application. All HANDBOOK.
Z_TENSILE_FACTOR = 0.5             # layer-adhesion strength vs in-plane
SAFETY_FACTOR = {                  # applied to the ESTIMATED worst-case load
    "static": 2.0,
    "cyclic": 4.0,                 # >1e4 cycles (gears, daily-use joints)
    "impact": 5.0,                 # drops, crashes (drones)
    "human_load": 6.0,             # a person's weight/safety rides on it
}
MIN_FILLET_LOADED_MM = 2.0         # root fillet at every loaded junction
DIM_TOL_MM = 0.15                  # per printed dim, in-plane (stack-up math)
DIM_TOL_Z_MM = 0.25                # per printed dim across layers/large parts
INFILL_DEFAULT = {                 # + 4 perimeters on structural parts
    "cosmetic": 0.15,
    "functional": 0.25,
    "structural": 0.40,
}

# --- gears & drives ------------------------------------------------------
# knowledge/gears_drives.md: buy first; printed gears are for low load.
GEAR_MIN_MODULE_MM = 1.0           # HANDBOOK — absolute floor at 0.4 nozzle
GEAR_PREFERRED_MODULE_MM = 1.5     # HANDBOOK — for anything carrying torque
GEAR_BACKLASH_MM = 0.2             # HANDBOOK — added at the centre distance
GEAR_MIN_FACE_WIDTH_FACTOR = 5.0   # HANDBOOK — face width >= 5 x module

# --- cables --------------------------------------------------------------
# knowledge/cable_management.md: routing, strain relief, connector pockets.
CABLE_CHANNEL_FACTOR = 1.5         # HANDBOOK — channel dia >= 1.5 x bundle dia
CABLE_BEND_RADIUS_FACTOR = 4.0     # HANDBOOK — min bend >= 4 x cable dia
ZIP_TIE_SLOT_MM = (4.0, 2.0)       # HANDBOOK — width x height for 2.5 mm ties
