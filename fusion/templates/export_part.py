"""Export one component as STEP + 3MF to exports/<project>/<part>_v{n}.*

TEMPLATE — run through fusion_mcp_execute after the part passes its
printability check. Replace COMPONENT / EXPORT_DIR / VERSION. Never
overwrite a version that may have been printed — bump VERSION instead.

Note: export options class names have shifted between Fusion releases;
if a createXxxExportOptions call fails, query fusion_mcp_read
apiDocumentation for 'ExportOptions' and adjust.
"""

import os

import adsk.core
import adsk.fusion

COMPONENT = '<project>_<part>'
EXPORT_DIR = os.path.expanduser(
    '~/Documents/GitHub/cad-pipeline/exports/<project>')
VERSION = 1


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    comp = None
    for occ in root.occurrences:
        if occ.component.name == COMPONENT:
            comp = occ.component
            break
    assert comp is not None, f'component {COMPONENT} not found'

    os.makedirs(EXPORT_DIR, exist_ok=True)
    base = os.path.join(EXPORT_DIR, f'{COMPONENT.split("_", 1)[1]}_v{VERSION}')
    assert not os.path.exists(base + '.step'), \
        f'{base}.step exists — bump VERSION, never overwrite a printed part'

    em = design.exportManager

    step_opts = em.createSTEPExportOptions(base + '.step', comp)
    em.execute(step_opts)

    mf_opts = em.createC3MFExportOptions(comp, base + '.3mf')
    em.execute(mf_opts)

    print('exported:', base + '.step')
    print('exported:', base + '.3mf')
    print('sizes:', os.path.getsize(base + '.step'), os.path.getsize(base + '.3mf'))
