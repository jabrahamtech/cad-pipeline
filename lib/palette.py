"""lib/palette - which part is which colour, in ONE place.

Seventeen part files each carried their own APPEARANCE_HINTS. Changing the
scheme meant editing seventeen files and hoping you found them all - the
exact "a datum only one file reads is a decoration, not a contract" trap
this project has now hit five times (shaft_from_end, lead_bundle_dia, the
horn widths, the gauge constants, and the lead datum itself). The colour is
cosmetic, so the cost of getting it wrong is only an ugly render - but the
SHAPE of the mistake is the expensive one, so it is fixed the same way.

THE SCHEME, 2026-08-29: forest green and white, mapped straight off the
colours the parts already had.

    yellow -> GREEN      the links and the shells: the arm and the hand
    black  -> WHITE      the joints, hubs, gears, blades and the turret

That is the split the design already used, so it keeps whatever reasoning
went into it. It is NOT the base-vs-moving split I picked first - that was
me inventing a scheme when one existed.

base_lid is the odd one: it had no appearance at all and rendered default
grey. It was never yellow, so it goes white with the rest of the untinted
parts.

Fusion's stock libraries have no "forest green", so HINTS resolves to the
nearest stock plastic and RGB carries the exact colour for anything that
wants to tint it properly later. Nothing prints in these colours - filament
is filament - so this drives renders and the assembly diagrams only.
"""

# the parts that were YELLOW: the links and the shells
# forearm was split into three printed pieces on 2026-09-03; they are the
# same link and stay the same colour. 'forearm' itself is now only the
# assembled reference and is never printed, but it is kept here so the
# reference body renders in the right colour in the assembly.
GREEN = ('forearm', 'forearm_px', 'forearm_nx', 'forearm_rail',
         'upper_arm', 'gripper_shell', 'gripper_rack_jaw',
         'pruner_shell', 'grip_shell')

# DARK, 2026-09-28: the base and the turret. A plain white O190 puck was the
# first thing anyone saw in the renders and it read as a cake tin. Dark plinth,
# green links, white joints and gears - the industrial-robot convention, and
# the heaviest, widest part stops competing with the arm for attention.
DARK = ('base_platter', 'base_lid', 'turntable_ring', 'turntable_stator',
        'turret_shroud', 'j1_hub')

# forest green #228B22, white #F5F5F5 - the exact values, for a tinted
# appearance. HINTS is the fallback that finds a stock Fusion appearance by
# substring, which is how every part file already looks one up.
# THE ACTUAL COLOUR. Fusion's stock 'Plastic - Glossy (Green)' is a bright
# mid green and Jonathan's filament is much deeper, so the stock appearance
# is only the STARTING POINT - tint() below copies it and overwrites its
# albedo with these values. Change them here and nothing else needs touching.
RGB = {'green': (18, 77, 40), 'white': (242, 242, 242), 'dark': (36, 38, 42)}
TINT_NAME = {'green': 'robotarm_deep_green', 'white': 'robotarm_white',
             'dark': 'robotarm_charcoal'}
HINTS = {
    'green': [('plastic', 'green'), ('paint', 'green'), ('green',),
              ('plastic',)],
    'white': [('plastic', 'white'), ('paint', 'white'), ('white',),
              ('plastic',)],
    'dark': [('plastic', 'black'), ('paint', 'black'), ('black',),
             ('plastic',)],
}


def colour_of(part_name):
    """green for the links, dark for the base and turret, white for the rest."""
    if part_name in GREEN:
        return 'green'
    return 'dark' if part_name in DARK else 'white'


def hints_for(part_name):
    """The substring hint list a part file feeds its appearance lookup."""
    return HINTS[colour_of(part_name)]


def tint(app, design, colour):
    """A design-local appearance in the exact RGB above.

    Fusion library appearances are read-only, so this copies the nearest
    stock plastic into the design and overwrites its albedo. Cached by name:
    calling it repeatedly returns the same appearance rather than piling up
    copies, which is what a naive version does and why documents end up with
    forty near-identical materials.
    """
    name = TINT_NAME[colour]
    local = design.appearances.itemByName(name)
    if local is None:
        src = None
        for hint in HINTS[colour]:
            for i in range(app.materialLibraries.count):
                aps = app.materialLibraries.item(i).appearances
                for j in range(aps.count):
                    a = aps.item(j)
                    if all(w.lower() in a.name.lower() for w in hint):
                        src = a
                        break
                if src:
                    break
            if src:
                break
        assert src is not None, 'no stock appearance matched %r' % colour
        local = design.appearances.addByCopy(src, name)
    prop = local.appearanceProperties.itemById('opaque_albedo')
    assert prop is not None, (
        '%s has no opaque_albedo to tint - the stock appearance this was '
        'copied from is not the plastic shader it was assumed to be' % name)
    r, g, b = RGB[colour]
    import adsk.core
    prop.value = adsk.core.Color.create(r, g, b, 255)
    return local
