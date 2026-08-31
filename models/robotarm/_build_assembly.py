"""robotarm/_build_assembly - driver. Builds the saved arm assembly document.

Saves `robotarm/assemblies/robotarm_arm`.

THIS IS A MONOLITHIC ASSEMBLY, NOT A REFERENCED ONE, AND THAT IS A COMPROMISE
WORTH NAMING. Real Fusion practice is an assembly that INSERTS each saved part
as an external reference, so editing robotarm_forearm updates the arm. This
document instead rebuilds every part inside itself.

WHY. _preview_arm.py - which owns every joint transform in this project - reads
19 document USER PARAMETERS to place things (gv() asserts on each). User
parameters are document-scoped and do NOT travel with an external reference,
so an assembly built from references has no fa_*, ua_*, ts_* to pose from. The
fix is to move those 19 datums into lib/, which is where CLAUDE.md says shared
datums belong; until then an external-reference assembly could be inserted but
not positioned, and an arm in a heap is worse than no arm.

So: the parts are rebuilt here from the same scripts that built the saved part
files, which means the geometry is identical by construction - both come from
models/robotarm/<part>.py. What is lost is the link, not the truth.

Rebuild it whenever a part script changes. Nothing here is hand-modelled.
"""

import os
import sys

import adsk.core
import adsk.fusion

PROJECT = 'robotarm'
FOLDER = 'assemblies'
DOC = 'robotarm_arm'

# _preview_arm.py's `need` list, in an order that satisfies the sibling
# parameter reads documented in _build_parts.DEPS.
PARTS = [
    'forearm', 'upper_arm', 'j3_gear', 'j3_pinion', 'j3_axle', 'j3_servo_cap',
    'turntable_stator', 'turntable_ring', 'shoulder_bracket', 'shoulder_hub',
    'wrist_hub', 'wrist_roll', 'wrist_rotator',
    'pruner_shell', 'pruner_rack', 'pruner_blade', 'gripper_pinion',
    # SECOND PASS ON upper_arm, and it is not a typo. upper_arm reads jg_* and
    # ja_*; j3_axle reads ua_*. That cycle has no build order, so the first
    # pass above gives j3_axle its ua_* and this one gives upper_arm the
    # jg_/ja_ it could not see the first time. Without it the part builds but
    # prints "Screw length not stated - jg_face, jg_bolt_head_d, jg_collar_l,
    # ja_tap_l not in this document", i.e. it silently stops telling you what
    # M3 to buy for the elbow. Two passes is a fixed point, not a fix - the
    # fix is to move that interface into lib/ (see _build_parts.DEPS).
    'upper_arm',
]

POSE = True   # run _preview_arm to pose everything and write docs/robotarm/*.png


def _folder(app):
    hub = app.data.activeHub
    proj = None
    for i in range(hub.dataProjects.count):
        if hub.dataProjects.item(i).name == PROJECT:
            proj = hub.dataProjects.item(i)
            break
    if proj is None:
        raise RuntimeError('no hub project %r' % PROJECT)
    root = proj.rootFolder
    for i in range(root.dataFolders.count):
        if root.dataFolders.item(i).name == FOLDER:
            return root.dataFolders.item(i)
    raise RuntimeError('no folder %r in %r' % (FOLDER, PROJECT))


def _exec(name, repo):
    """Run a script into the active document. Nothing caught, nothing muffled
    - tests/test_fusion_scripts.py bans try/except and it is right to."""
    path = os.path.join(repo, 'models', 'robotarm', name + '.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    ns = {'__name__': name, '__file__': path}
    exec(compile(open(path).read(), path, 'exec'), ns)
    ns['run']('')


def run(_context: str):
    app = adsk.core.Application.get()
    repo = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
    if repo not in sys.path:
        sys.path.insert(0, repo)
    folder = _folder(app)

    existing = None
    for i in range(folder.dataFiles.count):
        if folder.dataFiles.item(i).name == DOC:
            existing = folder.dataFiles.item(i)
            break
    doc = (app.documents.open(existing) if existing is not None
           else app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType))
    doc.activate()

    for part in PARTS:
        _exec(part, repo)

    design = adsk.fusion.Design.cast(app.activeProduct)
    vol, nb = 0.0, 0
    for c in design.allComponents:
        for j in range(c.bRepBodies.count):
            vol += c.bRepBodies.item(j).physicalProperties.volume * 1000.0
            nb += 1
    print('built %d parts, %d bodies, %.1f mm3 of solid' % (len(PARTS), nb, vol))

    if POSE:
        _exec('_preview_arm', repo)

    if existing is not None:
        doc.save('rebuilt by models/robotarm/_build_assembly.py')
    else:
        doc.saveAs(DOC, folder, 'the whole arm, posed - see the module '
                                'docstring for why it is monolithic', '')
    print('saved %s/%s/%s' % (PROJECT, FOLDER, doc.name))
