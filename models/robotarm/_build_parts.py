"""robotarm/_build_parts - driver. Builds part scripts into SAVED part files.

Jonathan, 2026-08-31: "change some settings to make sure you are working in
saved part files and using saved projects for the actual arm or whatever the
convension is - and then use fusion to build all of it out".

WHAT THE CONVENTION NOW IS. Fusion hub project `robotarm`, three folders:

    robotarm/parts/       one saved design per part, named robotarm_<part>
    robotarm/assemblies/  designs that INSERT those parts as external refs
    robotarm/gates/       the _check_*/_preview_* documents

Before this, every part was a component inside one scratch document
(`robotarm_parts` in Default Project) plus a handful of loose gate documents.
That is fine for a sketchpad and wrong for a machine you intend to build:
there is no per-part version history, no way to reference a part from an
assembly, and no way to tell which parts are current.

CLAUDE.md still says "Fusion documents are NOT the source of truth - the
script that rebuilds it is", and that stays true. These files are BUILD
OUTPUT. Nothing is hand-modelled in them and anything typed into one is lost
on the next rebuild. What changes is only that the output now has a home.

THE DEPENDENCY MAP IS A BUG BEING WORKED AROUND, NOT A FEATURE.
Five parts read another part's user parameters out of the document they were
sharing:

    gripcut_finger -> pb_   (pruner_blade)
    j3_gear        -> fa_   (forearm)
    j3_servo_cap   -> fa_   (forearm)
    j3_axle        -> ua_   (upper_arm)
    upper_arm      -> fa_, ja_, jg_

upper_arm <-> j3_axle is CIRCULAR. That only ever worked because everything
lived in one document and whatever ran last won. j3_servo_cap is the only one
that asserts when the interface is absent; the others fall back silently,
which is the failure CLAUDE.md names - a datum only one file reads is a
decoration, not a contract. The right fix is to move each shared interface
into lib/ so both sides read it from one place. Until that is done, DEPS
below rebuilds the dependency inside the part's own document so the
parameters exist, then DELETES its body, because a part file holds one part.

Anything in DEPS is therefore a to-do, not a design. The list shrinking to
empty is the goal.
"""

import io
import os
import sys

# NEVER REASSIGN sys.stdout IN A FUSION SCRIPT. 2026-09-03, and it cost a
# working session. A loader did `sys.stdout = StringIO()` to quieten 23 parts'
# chatter, the build raised partway through, and the restore line never ran. The
# add-in binds its own capture object to sys.stdout ONCE at load and calls
# `resetContent()` on it after every script, so from that moment every call -
# including ones that never touch stdout - died with
# 
#     '_io.StringIO' object has no attribute 'resetContent'
# 
# There is no way to repair it from inside a script; the capture object is not
# reachable from sys.modules. The only fix is to Stop and Run the add-in in
# Utilities > ADD-INS > Scripts and Add-Ins, which reloads its interpreter.
# 
# If a script is too chatty, quieten the SCRIPT. Do not redirect the stream.
#

import adsk.core
import adsk.fusion

PROJECT = 'robotarm'
FOLDER = 'parts'

# See the docstring: every entry here is an interface that belongs in lib/.
DEPS = {
    'gripcut_finger': ['pruner_blade'],
    'j3_gear': ['forearm'],
    'j3_servo_cap': ['forearm'],
    'j3_axle': ['forearm', 'upper_arm'],
    'upper_arm': ['forearm'],
}

# Every non-driver script in models/robotarm/, in an order that satisfies DEPS.
ALL_PARTS = [
    'forearm', 'upper_arm', 'j3_gear', 'j3_pinion', 'j3_axle', 'j3_servo_cap',
    'horn_adapter', 'shoulder_hub', 'shoulder_bracket', 'turntable_stator',
    'j1_hub',
    'turntable_ring', 'base_lid', 'wrist_hub', 'wrist_roll', 'wrist_rotator',
    'gripper_shell', 'gripper_pinion', 'gripper_rack_jaw', 'gripcut_finger',
    'pruner_shell', 'pruner_rack', 'pruner_blade', 'servo_adapter',
]

# Set by the caller before run(). Empty means ALL_PARTS.
PARTS = []


def _folder(app):
    hub = app.data.activeHub
    proj = None
    for i in range(hub.dataProjects.count):
        if hub.dataProjects.item(i).name == PROJECT:
            proj = hub.dataProjects.item(i)
            break
    if proj is None:
        raise RuntimeError('no hub project %r - create it first' % PROJECT)
    root = proj.rootFolder
    for i in range(root.dataFolders.count):
        if root.dataFolders.item(i).name == FOLDER:
            return root.dataFolders.item(i)
    raise RuntimeError('no folder %r in project %r' % (FOLDER, PROJECT))


def _exec(part, repo):
    """Run a part script into the active document.

    NOTHING IS CAUGHT AND NOTHING IS MUFFLED. tests/test_fusion_scripts.py
    bans try/except in Fusion scripts - "the traceback is the debugging
    signal" - and a batch builder is the exact place the temptation is
    strongest and the rule matters most. A build that stops dead on the
    first broken part, with its traceback, beats one that prints 23 tidy
    one-line summaries and hides where it went wrong.
    """
    path = os.path.join(repo, 'models', 'robotarm', part + '.py')
    for m in [m for m in list(sys.modules) if m == 'lib' or m.startswith('lib.')]:
        del sys.modules[m]
    ns = {'__name__': part, '__file__': path}
    # ENCODING IS EXPLICIT AND THAT IS NOT PEDANTRY. Fusion's embedded Python
    # resolved open() to the ASCII codec and died on the first Oe in a
    # docstring: "UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3".
    # 23 files in this repo carry Oe, em dashes or +/- signs, most of them for
    # years, so this fails on whichever file it reaches first and looks like a
    # fault in that file rather than in the reader.
    _src = io.open(path, encoding='utf-8').read()
    exec(compile(_src, path, 'exec'), ns)
    ns['run']('')


def build(app, folder, part, repo):
    name = 'robotarm_' + part
    existing = None
    for i in range(folder.dataFiles.count):
        if folder.dataFiles.item(i).name == name:
            existing = folder.dataFiles.item(i)
            break
    doc = (app.documents.open(existing) if existing is not None
           else app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType))
    doc.activate()

    deps = DEPS.get(part, [])
    for dep in deps:
        _exec(dep, repo)
    _exec(part, repo)

    design = adsk.fusion.Design.cast(app.activeProduct)
    # A PART FILE HOLDS ONE PART. The dependencies were built only so their
    # user parameters exist to be read; their bodies do not belong in here.
    for dep in deps:
        for o in list(design.rootComponent.occurrences):
            if o.component.name == 'robotarm_' + dep:
                o.deleteMe()

    vol, nb = 0.0, 0
    for c in design.allComponents:
        for j in range(c.bRepBodies.count):
            vol += c.bRepBodies.item(j).physicalProperties.volume * 1000.0
            nb += 1

    if existing is not None:
        doc.save('rebuilt from models/robotarm/%s.py' % part)
    else:
        doc.saveAs(name, folder, 'built by models/robotarm/%s.py' % part, '')
    return nb, vol, deps


def run(_context: str):
    app = adsk.core.Application.get()
    repo = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
    if repo not in sys.path:
        sys.path.insert(0, repo)
    folder = _folder(app)
    todo = PARTS or ALL_PARTS
    done = []
    for part in todo:
        nb, vol, deps = build(app, folder, part, repo)
        done.append('  %-20s bodies %d  vol %9.1f mm3  deps %s'
                    % (part, nb, vol, ','.join(deps) if deps else '-'))
    print('=== %d/%d built into %s/%s ===' % (len(done), len(todo), PROJECT, FOLDER))
    for line in done:
        print(line)
