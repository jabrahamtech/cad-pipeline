"""Single source of truth for printer limits and design rules.

Calibrated on the Bambu Lab X2D — never change without a test print.
CLAUDE.md "Design rules" section mirrors these values for the model's
benefit; this file is what code and tests import.
"""

# --- printability minimums (0.4 mm nozzle)
MIN_WALL_MM = 1.6
MIN_FEATURE_MM = 0.8          # smallest printable positive feature

# --- X2D print envelopes (W, D, H) in mm
ENVELOPE_SINGLE = (256.0, 256.0, 260.0)
ENVELOPE_DUAL = (235.5, 256.0, 256.0)   # when the support nozzle is used

# --- calibrated fits and features
PRESS_FIT_CLEARANCE_MM = 0.15
SLIDING_FIT_CLEARANCE_MM = 0.25
M3_INSERT_HOLE_DIA_MM = 4.0
M3_INSERT_BOSS_WALL_MM = 2.4
ELEPHANT_FOOT_CHAMFER_MM = 0.4
