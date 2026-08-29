"""lib/palette - which part is which colour, in ONE place.

Seventeen part files each carried their own APPEARANCE_HINTS. Changing the
scheme meant editing seventeen files and hoping you found them all - the
exact "a datum only one file reads is a decoration, not a contract" trap
this project has now hit five times (shaft_from_end, lead_bundle_dia, the
horn widths, the gauge constants, and the lead datum itself). The colour is
cosmetic, so the cost of getting it wrong is only an ugly render - but the
SHAPE of the mistake is the expensive one, so it is fixed the same way.

THE SCHEME, 2026-08-29: forest green and white.

Green goes on the base and the turret because Jonathan's platter is ALREADY
printed in green - so the fixed half of the machine matches what exists, and
everything that moves is white. That also happens to read well: the eye
follows the moving parts, which is what you want when you are watching a
mechanism you are debugging.

Fusion's stock libraries have no "forest green", so HINTS resolves to the
nearest stock plastic and RGB carries the exact colour for anything that
wants to tint it properly later. Nothing prints in these colours - filament
is filament - so this drives renders and the assembly diagrams only.
"""

# what the eye should read as FIXED (the base and turret)
GREEN = ('turntable_stator', 'turntable_ring', 'base_lid', 'shoulder_bracket')

# forest green #228B22, white #F5F5F5 - the exact values, for a tinted
# appearance. HINTS is the fallback that finds a stock Fusion appearance by
# substring, which is how every part file already looks one up.
RGB = {'green': (34, 139, 34), 'white': (245, 245, 245)}
HINTS = {
    'green': [('plastic', 'green'), ('paint', 'green'), ('green',),
              ('plastic',)],
    'white': [('plastic', 'white'), ('paint', 'white'), ('white',),
              ('plastic',)],
}


def colour_of(part_name):
    """'green' for the fixed half, 'white' for everything that moves."""
    return 'green' if part_name in GREEN else 'white'


def hints_for(part_name):
    """The substring hint list a part file feeds its appearance lookup."""
    return HINTS[colour_of(part_name)]
