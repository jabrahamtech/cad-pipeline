"""robotarm/_retheme - apply the palette's EXACT colours to what is built.

The part files pick the nearest stock Fusion appearance, which is as far as
a substring hint can get you: 'Plastic - Glossy (Green)' is a bright mid
green and the filament is much deeper. This pass walks every robotarm_
component in the document and repaints it in lib/palette.RGB.

Separate from the part files on purpose. Colour is not geometry, it does not
belong in a rebuild, and putting it here means a re-theme costs one run
instead of seventeen edits and a four-batch rebuild.
"""

import os
import sys

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    for m in [k for k in list(sys.modules) if k == 'lib' or k.startswith('lib.')]:
        del sys.modules[m]
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from lib.palette import colour_of, tint, RGB

    done, counts = [], {}
    for occ in root.occurrences:
        n = occ.component.name
        if not n.startswith('robotarm_'):
            continue
        part = n.replace('robotarm_', '')
        if part in counts:
            continue
        c = colour_of(part)
        ap = tint(app, design, c)
        for i in range(occ.component.bRepBodies.count):
            occ.component.bRepBodies.item(i).appearance = ap
        counts[part] = c
        done.append((part, c))

    print('=== retheme ===')
    for c in ('green', 'white'):
        print('%s  rgb%s' % (c.upper(), RGB[c]))
        for part, k in sorted(done):
            if k == c:
                print('    %s' % part)
    print('')
    print('%d components repainted' % len(done))
    print('Colours are RENDER ONLY - filament is filament.')
