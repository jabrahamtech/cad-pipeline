"""robotarm/_export_plates - every piece, oriented and packed onto plates.

ONE 3MF PER PLATE. Fusion writes a single-plate 3MF; multi-plate project
files are a slicer format, not something Fusion exports. So "one file" means
one per plate, with the parts already turned the right way up and arranged.

WHAT THIS DOES THAT DRAGGING FILES INTO A SLICER DOES NOT: it applies each
part's PRINT ORIENTATION from its own docstring, which for four of them is
not a preference:

  gripcut_finger  TOP FACE DOWN. Layers must lie ALONG the leaf or the
                  flexure is a fatigue crack waiting. Printed flat the wrong
                  way it looks identical and breaks.
  pruner_rack     BACK FACE DOWN, not teeth down - teeth down needs support
                  under the drive pin.
  turntable_stator  base down, and SUPPORTS OFF: the stub axle bridge is
                  load-bearing and support scars it.
  wrist_roll      OUTER FACE DOWN, and it is printed TWICE with the second
                  copy MIRRORED. See THE WRIST CLAMSHELL below - it is the
                  only part here that is not one body per printed piece.

THE PACKING IS CHECKED, NOT EYEBALLED. Every placed rectangle is asserted
inside the plate and against every other rectangle for overlap, and every
placed body is re-measured in Fusion afterwards for bounds and for sitting
on z = 0. Two orientation bugs have already shipped on this project in one
day - both mine, both caught by Jonathan looking at a picture - so nothing
here is trusted because it looks right.

BED: Bambu Lab X2D, 256 x 256. MARGIN keeps parts off the edge; GAP is the
space between them. Neither is a slicer setting - re-check brims yourself,
base_lid wants one and a brim is 5-8 mm of extra footprint.

===========================================================================
THE WRIST CLAMSHELL: TWO COPIES OF ONE DESIGN, THE SECOND ONE MIRRORED
===========================================================================
wrist_roll was split on x = 0 - the YZ plane through the J4 pitch axis -
and is now ONE printed design used as BOTH halves, the second one mirrored
in x. There is deliberately no wrist_roll_cap.py; a second script would
have to re-declare that file's 30-parameter servo block, which is the
failure lib/joints.py exists to stop. specs/robotarm/_printability.md
carries the whole argument.

This packer had never placed two copies of one part, let alone a mirrored
one, so three things are new here and all three are asserted rather than
eyeballed:

  1. MIRRORED names the parts whose copies are not identical. Copy 0 is the
     part as drawn; copy 1 is its mirror image. They are DIFFERENT SOLIDS
     and only one of each assembles on a given side.

  2. A MIRROR IS NOT A 180 DEG TURN, and the two are easy to confuse because
     on this part they produce silhouettes that look alike from above. A
     rotation preserves handedness (determinant +1); a reflection inverts it
     (determinant -1). So the determinant of the matrix actually handed to
     addExistingComponent is asserted, per piece, against what that piece is
     supposed to be. A 180 deg turn cannot pass that assert, which is the
     entire point of writing it.

  3. BOTH COPIES STILL OBEY THE PART'S PRINT ORIENTATION: outer side face
     (x = wro_half_x) on the bed, built along -X toward the split face.
     NOT split-face-down. wrist_roll.py's docstring is unambiguous about
     why: split-face-down re-roofs the servo bay as a 618 mm2 ceiling on a
     22.9 mm bridge, re-roofs both tab slots and the keyway, and turns the
     rotator half bore into an arch over 50 deg. Outer-face-down opens
     every cavity at the TOP of the build and leaves exactly one bridge.

     The mirror is applied in the BED's frame, after the print rotation, in
     x - which is what a slicer's "mirror" button does. That is not a
     convenience: a mirror in global x moves nothing in z, so it cannot
     change which face is on the bed, and the orientation rule holds for
     the mirrored copy BY CONSTRUCTION rather than by luck. It is also
     exactly the half that is wanted, because

         MIRROR_X(global) . R_y(90)  ==  R_y(-90) . MIRROR_X(local)

     and the right-hand side is, literally, "reflect the part in its own
     split plane, then stand the result on its outer face". Both sides of
     that identity map local +X to global -Z, which is the assert.

     (Any reflection of a solid is congruent to any other by a rigid
     motion, so WHICH plane is reflected in does not change what comes off
     the bed - only the handedness does. That is why the determinant is the
     complete test and the mirror plane is not something this file has to
     get right twice.)

===========================================================================
A NAMED SUBSET IS A PLATE KEY, NOT A SECOND MECHANISM
===========================================================================
PLATE_OF has always been the one place the grouping is decided. Its values
are now plate KEYS rather than only plate numbers, and ONLY_PLATES names
which of those keys to build. So "give me just the wrist plate" is

    # SPLIT THE SELECTED PLATES BY FILAMENT COLOUR. Jonathan prints this arm in
# two colours - forest green for the links and shells, white for the joints,
# hubs and gears (lib/palette.py) - so a plate that mixes them is a plate he
# has to stop and swap filament in the middle of.
#
# THE COLOUR IS READ OFF THE BUILT BODY, NOT FROM palette.colour_of(). Those
# two disagree: j3_servo_cap.py calls hints_for('forearm') on purpose, because
# the cap IS part of the forearm and prints with it - but its own name is not
# in palette.GREEN, so colour_of() calls it white. The body knows what it will
# actually print as; the name table does not.
SPLIT_BY_COLOUR = True
ONLY_PLATES = 'armstack'

and the parts, the grouping, the note and the exported filename all come
from the same table the full build uses. Nothing is re-listed anywhere.
ONLY still filters by PART NAME, for the finer case of some of a plate
already being on the bench; the two compose.

===========================================================================
THE LEDGER IS STALE FOR wrist_roll, AND THIS FILE WILL SAY SO LOUDLY
===========================================================================
specs/robotarm/_volumes.json still holds 13352.026 mm3 for wrist_roll,
which is the MONOLITH - the ledger has not been rewritten since the part
was split, because the Fusion add-in dropped out before anything could be
built. The volume assert below will therefore FAIL on wrist_roll until
_check_wrist / _check_ledger BATCH 1 has been re-run and _volumes.json
rewritten from a run someone has actually read.

That failure is CORRECT and it is not to be worked around here. The assert
is the only thing standing between this file and exporting geometry the
gates never saw; a plate exported past it would be a photograph of a part
nobody has checked. _volumes.json is not this file's to edit.
"""

import json
import math
import os

import adsk.core
import adsk.fusion

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
SRC_DIR = os.path.join(REPO, 'exports', 'robotarm', 'print')
OUT_DIR = os.path.join(REPO, 'exports', 'robotarm', 'plates')
LEDGER = os.path.join(REPO, 'specs', 'robotarm', '_volumes.json')
# 7, not 6: wrist_roll is a different part than the one v6 was cut from, and
# wrist_rotator is the other way up. Reusing the version would leave two
# files with the same name meaning two different things.
VERSION = 8
BED_X, BED_Y = 256.0, 256.0
MARGIN, GAP = 6.0, 4.0
# A BRIM IS FOOTPRINT. base_lid is 171.75 across, 3 thick, and warps without
# one - so it needs a brim, and a brim is 5-8 mm of extra plastic all round
# that the packer has to know about or the neighbours land on top of it. The
# part is placed CENTRED in its padded slot, so the pad is real space.
# forearm_rail stands 24.8 mm tall on ~69 mm2 - the smallest footprint
# in the project by a wide margin, and the only part here that could
# actually tip. 5.0 of brim is not optional on it.
BRIM_PAD = {'base_lid': 5.0, 'forearm_rail': 5.0}

# SETTINGS THAT CANNOT SHARE A PLATE. forearm is the only part that wants
# supports; turntable_stator is a part they would RUIN - its stub axle bridge
# is load-bearing and support scars the underside. Putting them together
# means one per-object override stands between you and a wrecked axle, so
# they go on different plates and the packer enforces it rather than a note
# in a document hoping to be read.
# forearm is gone (see ORIENT); nothing left in this project asks for
# support, so the pairing it existed to prevent cannot arise.
NEVER_TOGETHER = []

# PARTS PRINTED AS A MIRRORED PAIR - one design, two copies, the second one
# a MIRROR IMAGE of the first. Not a turn-over: gripper_shell and
# pruner_shell are clamshells whose two halves are the same solid rotated,
# and they are NOT in here. wrist_roll's silhouette has a keel below and a
# crest above, so it is chiral, and the second half only exists as a
# reflection.
#
# Qty for these is asserted to be exactly 2 below. A part that needs three
# copies of which one is mirrored is not a thing this project has, and
# guessing at what index the mirror would fall on is how a wrong part gets
# printed.
MIRRORED = {'wrist_roll'}

# PLATES ARE ASSIGNED, NOT PACKED INTO. Letting a bin-packer choose was the
# wrong objective and it showed: sorting for density put forearm (supports)
# beside turntable_stator (supports would ruin it), and sorting for height
# put the 76 mm shoulder_bracket in the middle of twelve small parts, where
# if it lets go it ploughs through all of them.
#
# So the grouping is a decision, and the packer only arranges within it:
#
#   1      THE J1 ANSWER, and everything that needs no supports and no brim.
#          Print this one first: "does the turret turn" is the riskiest open
#          claim in the project and this plate settles it. Uniform settings -
#          supports OFF, no brim - so there is no per-object override to
#          forget.
#   2      The long parts and the big thin one. base_lid wants a brim,
#          forearm wants supports, and neither can hurt the other. Nothing on
#          this plate is short enough to be shadowed by upper_arm's 151 mm of
#          travel.
#   wrist  THE WHOLE WRIST, five pieces. It used to be three pieces riding on
#          plate 1; the clamshell split turned wrist_roll into two and the
#          wrist became a sub-assembly you can print, build and hang off the
#          forearm on its own. Giving it its own key is what makes a
#          wrist-only export possible at all, and it also takes 1795 mm2
#          of new footprint off plate 1, which had no room for it.

# SPLIT THE SELECTED PLATES BY FILAMENT COLOUR. Jonathan prints this arm in
# two colours - forest green for the links and shells, white for the joints,
# hubs and gears (lib/palette.py) - so a plate that mixes them is a plate he
# has to stop and swap filament in the middle of.
#
# THE COLOUR IS READ OFF THE BUILT BODY, NOT FROM palette.colour_of(). Those
# two disagree: j3_servo_cap.py calls hints_for('forearm') on purpose, because
# the cap IS part of the forearm and prints with it - but its own name is not
# in palette.GREEN, so colour_of() calls it white. The body knows what it will
# actually print as; the name table does not.
SPLIT_BY_COLOUR = True
ONLY_PLATES = 'armstack'
PLATE_OF = {
    'turntable_stator': 1, 'turntable_ring': 1, 'shoulder_bracket': 1,
    'shoulder_hub': 1, 'pruner_shell': 1, 'gripper_pinion': 1,
    'gripcut_finger': 1,
    # the flat ones ride in the 58 mm strip beside base_lid, which is
    # otherwise dead space - plate 1 has no room for them and this costs
    # nothing
    'pruner_blade': 2, 'pruner_rack': 2,
    'base_lid': 2, 'upper_arm': 2,
    # EVERYTHING FROM THE J2 OUTPUT UP TO THE WRIST, as one build. This is
    # the assembly Jonathan can add now: the MG995 shoulder is working, so
    # this plate is shoulder_hub -> upper_arm -> the elbow drive -> the
    # three forearm pieces. It stops AT the wrist: wrist_hub is the first
    # part of the next assembly and is not here.
    'shoulder_hub': 'armstack', 'upper_arm': 'armstack',
    'j3_gear': 'armstack', 'j3_pinion': 'armstack',
    'j3_axle': 'armstack', 'j3_servo_cap': 'armstack',
    'forearm_px': 'armstack', 'forearm_nx': 'armstack',
    'forearm_rail': 'armstack',
    'wrist_roll': 'wrist', 'wrist_hub': 'wrist', 'wrist_rotator': 'wrist',
}
# WHICH PLATES TO BUILD. None is every key in PLATE_OF. Otherwise a key or a
# sequence of keys from PLATE_OF - 'wrist', 1, (1, 2) - and only those parts
# are measured, packed and exported. Every name is checked against PLATE_OF,
# so a mistyped key is an assert and not a silently empty plate.
# SPLIT THE SELECTED PLATES BY FILAMENT COLOUR. Jonathan prints this arm in
# two colours - forest green for the links and shells, white for the joints,
# hubs and gears (lib/palette.py) - so a plate that mixes them is a plate he
# has to stop and swap filament in the middle of.
#
# THE COLOUR IS READ OFF THE BUILT BODY, NOT FROM palette.colour_of(). Those
# two disagree: j3_servo_cap.py calls hints_for('forearm') on purpose, because
# the cap IS part of the forearm and prints with it - but its own name is not
# in palette.GREEN, so colour_of() calls it white. The body knows what it will
# actually print as; the name table does not.
SPLIT_BY_COLOUR = True
ONLY_PLATES = 'armstack'
# A SUBSET BY PART NAME, when some of a plate is already on the bench. Empty
# means everything ONLY_PLATES selected. Parts not named in PLATE_OF land in
# a bucket that opens new plates as it fills, instead of asserting - the
# deliberate grouping is for the full build and does not apply to whatever
# happens to be left.
ONLY = []
AUTO_SPLIT = False

PLATE_NOTE = {
    1: 'THE J1 ANSWER + the effector. Supports OFF, no brim - uniform settings.',
    2: 'The long parts. base_lid BRIM, forearm SUPPORTS, nothing else.',
    'wrist': ('THE WHOLE WRIST - J4 pitch and J5 roll, five pieces. Supports '
              'OFF, no brim, one profile. The two wrist_roll bodies are A '
              'MIRRORED PAIR: see specs/robotarm/_wrist_plate.md before you '
              'pick them off the bed.'),
    99: 'Whatever was left over - no deliberate grouping applies.',
}

# Parts whose height makes them the thing that gets knocked off. A tall part
# is placed at the BACK, so the toolhead crosses it less on its way to
# everything else, and a detached part does not then plough through the rest.
TALL_MM = 40.0
PETG, SOLID = 1.27, 0.65

# name, qty, (rotation axis, degrees) to put the print face DOWN, why
ORIENT = [
    ('base_lid',         1, None,        'flat 3 mm plate, BRIM'),
    ('upper_arm',        1, ('y', -90),  'built along X, 125 mm across the bed'),
    # forearm IS NO LONGER A PRINTED PART. It was split into forearm_px,
    # forearm_nx and two forearm_rail, because the bench called it impossible
    # to print and it was: 2802 mm2 of flat 90 deg ceiling, 918 of it a slab
    # floating 43 mm up on two rails. The split takes that to 760 mm2, and
    # the rails come out at ZERO. Each plate now prints INNER FACE DOWN, so
    # every former roof opens upward and all four bores stay vertical.
    # This row said "SUPPORTS under +X wall and lobes" - the only row in the
    # file that ever asked for support. Routing it now would export a body
    # nothing builds.
    # THE ELBOW DRIVE. Orientations are each part's own docstring, quoted:
    #   j3_gear      "GEAR FACE ON THE BED, built -Z" - its stem runs to
    #                z -11.70, so this is a flip, not a no-op.
    #   j3_pinion    "TOOTH FACE ON THE BED, bore vertical" - already z 0 up.
    #   j3_axle      "HEX FACE ON THE BED, built +Z" - already z 0 up.
    #   j3_servo_cap "FLAT, seating face on the bed" - already z 0 up.
    ('j3_gear',          1, ('x', 180),  'gear face down, built -Z'),
    ('j3_pinion',        1, None,        'tooth face down, bore vertical'),
    ('j3_axle',          1, None,        'hex face down, built +Z'),
    ('j3_servo_cap',     1, None,        'flat, seating face down'),
    ('forearm_px',       1, ('y', -90),  'inner face down, no support'),
    ('forearm_nx',       1, ('y',  90),  'inner face down, no support'),
    # QTY 2, and NOT in MIRRORED: the second rail is the first turned 180 deg
    # about Y, which is a rotation - same solid, no handedness - so two
    # identical copies are correct and there is nothing to tell apart on the
    # bed. ORIENT is ('y', 90) and not None: the rail is a prism along X with
    # a CURVED cross-section (it is cut from the link outline), so laid flat
    # it would rest on a curve. Stood on an end face the whole part is one
    # extrusion up the build axis - zero overhang, zero bridge - at the cost
    # of a 24.8 mm tower on ~69 mm2, which is what the brim below is for.
    ('forearm_rail',     2, ('y',  90),  'end face down, prism, brim'),
    # WAS ('x', 90) - 'back face down, built +Y' - and that was the MONOLITH's
    # orientation, left behind when the part became a clamshell. ('y', 90)
    # puts local +X down, and the outer side face is the +X face at
    # wro_half_x, so this is "outer face on the bed, built -X". Asserted
    # against wro_half_x itself further down rather than believed.
    ('wrist_roll',       2, ('y', 90),   'OUTER face (x wro_half_x) on the bed, built -X. TWO, SECOND MIRRORED'),
    ('turntable_stator', 1, None,        'base down, cheeks up. SUPPORTS OFF'),
    ('turntable_ring',   1, None,        'annulus. Do not sand the bore'),
    ('shoulder_bracket', 1, ('y', -90),  '-X face down, journal bores vertical'),
    ('pruner_shell',     2, None,        'split face down. TWO'),
    ('pruner_rack',      2, ('x', 180),  'BACK face down - teeth down needs support'),
    ('pruner_blade',     2, None,        'inner face down. TWO'),
    # WAS None - 'back face down' - which stands the part on the Oe10.5 hub
    # for about 64 mm2 of bed contact. wrist_rotator.py was TURNED OVER and
    # this row never followed it: front face down makes the Oe36 disc the
    # first layer (~950 mm2), and every cross-section then shrinks going up.
    # The four M3 insert holes open at the bed and print as 4.0 mm bridges
    # under 0.50 mm of skin, which is the stated price of the flip.
    ('wrist_rotator',    1, ('x', 180),  'FRONT face down - the Oe36 disc is the first layer'),
    # the part's own printability gate calls this "flange face on the bed,
    # built +Z"; the flange is the widest thing on it and the outboard flange
    # face is the minimum in local z, so the identity matrix already does it
    ('wrist_hub',        2, None,        'flange face down, hex up. TWO'),
    ('shoulder_hub',     1, None,        'collar face down'),
    ('gripper_pinion',   1, None,        'flat'),
    ('gripcut_finger',   2, ('x', 180),  'TOP FACE DOWN - the flexure rule. TWO'),
]


# ---- MATRICES, WRITTEN OUT RATHER THAN COMPOSED BY THE LIBRARY -------------
# Fusion's a.transformBy(b) means a := b * a, which is the opposite of how it
# reads - models/robotarm/_preview_arm.py says exactly that at its own mul().
# This file used transformBy once, for the yaw, and had the order backwards:
#
#     yz = Rz ; yz.transformBy(rot)   ->   rot * Rz
#
# which applies the yaw in the PART's frame BEFORE the print rotation. That is
# precisely what the yaw comment promises does not happen ("does not change
# which face is on the bed"), and for a part with a 90 deg spec it turns the
# yaw into a barrel roll and lands a different face on the bed. Nothing here
# could have seen it: the re-measure at the end checks that a part sits ON the
# bed and INSIDE it, never which of its faces is down.
#
# That would have been the third orientation bug on this project. So every
# composition is done here in plain arithmetic, where the order is written out
# in one place, and the result is ASSERTED below rather than trusted. 3x3 only
# - translation is applied separately, at the end, where it cannot interact
# with any of this.
IDENT3 = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
# A REFLECTION IN THE BED's x. Applied AFTER the print rotation, so it is the
# slicer's "mirror in X" and nothing more. It leaves z alone, so it cannot
# move a part off the face it was stood on.
MIRROR_X3 = [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
DOWN3 = [0.0, 0.0, -1.0]
EPS = 1e-9


def _mul3(a, b):
    """a * b - the transform that applies b FIRST, then a."""
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def _apply3(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def _t3(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def _det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def _rot3(axis, deg):
    """Right-handed rotation about a BED axis, degrees. Written out because a
    sign convention read off a library is a sign convention nobody checked."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    if axis == 'x':
        return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]
    if axis == 'y':
        return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]
    assert axis == 'z', 'unknown rotation axis %r' % (axis,)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def orient3(spec):
    """The part's own print orientation, from its docstring, and nothing else."""
    return IDENT3 if spec is None else _rot3(spec[0], spec[1])


def place3(spec, mirror, yaw):
    """The full linear part of a piece's placement, in the order it happens:
    stand the part on its print face, then (if this is the second half of a
    mirrored pair) reflect it in the bed's x, then (if the packer asked) yaw
    it 90 deg about the bed's z. Both of the last two are BED-frame moves
    applied after the print rotation, which is what makes them free."""
    m = orient3(spec)
    if mirror:
        m = _mul3(MIRROR_X3, m)
    if yaw:
        m = _mul3(_rot3('z', 90.0), m)
    return m


def check3(name, spec, mirror, yaw, m):
    """Prove the matrix that is about to be used, rather than the one intended.

    Three separate things, because they fail separately:

    RIGID. m . mT == I, so m is a rotation or a reflection and not a squash.
    Everything below assumes lengths are preserved; if they are not, the
    footprint the packer reserved is fiction.

    HANDEDNESS. det +1 is a rotation, det -1 is a reflection. This is the
    whole mirrored-pair check and it is the reason the pair is trustworthy: a
    180 deg turn about ANY axis has det +1 and cannot pass as the mirror, and
    a reflection cannot pass as the unmirrored copy. The two halves of
    wrist_roll are different solids and only one of them assembles on a given
    side of the wrist, so getting this backwards is a wasted print at best.

    BED FACE. Whatever face the print orientation put down has to still be
    down after the mirror and the yaw. Derived as orient3(spec)^-1 applied to
    straight-down - orient3 is orthonormal so the inverse is the transpose -
    and then pushed back through the FINAL matrix. This is the assert the old
    yaw composition fails, and it is the one that would have caught the two
    orientation bugs that already shipped."""
    prod = _mul3(m, _t3(m))
    for i in range(3):
        for j in range(3):
            assert abs(prod[i][j] - IDENT3[i][j]) < EPS, (
                '%s: placement matrix is not rigid - it scales or shears, so '
                'the packed footprint is not the printed one' % name)
    det = _det3(m)
    want = -1.0 if mirror else 1.0
    assert abs(det - want) < EPS, (
        '%s: placement determinant is %+.6f and this copy is supposed to be '
        '%s (%+.0f). A rotation PRESERVES handedness and a reflection INVERTS '
        'it, so a 180 deg turn scores +1 here and can never pass as the '
        'mirror. These are two different solids and only one of them '
        'assembles.' % (name, det, 'MIRRORED' if mirror else 'as drawn', want))
    down_local = _apply3(_t3(orient3(spec)), DOWN3)
    got = _apply3(m, down_local)
    assert max(abs(got[i] - DOWN3[i]) for i in range(3)) < EPS, (
        '%s: the face the print orientation put on the bed now points %s, not '
        'straight down. mirror=%s yaw=%s - a mirror in the bed\'s x and a yaw '
        'about the bed\'s z both leave z alone, so if this fails the '
        'composition order is wrong, not the geometry.'
        % (name, tuple(round(g, 4) for g in got), mirror, yaw))


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    M3 = adsk.core.Matrix3D.create
    V3 = adsk.core.Vector3D.create
    _TB = adsk.fusion.TemporaryBRepManager.get()

    comps = {}
    for occ in root.occurrences:
        n = occ.component.name
        if n.startswith('robotarm_') and n not in comps:
            comps[n] = occ.component
    with open(LEDGER) as fh:
        ledger = json.load(fh)

    def measure(body, lin):
        """Footprint and low corner of a body under a linear placement, in mm.

        Fusion is in cm and this whole file is in mm, so the conversion
        happens here, once, on the way in - the eight corners are the only
        geometry that crosses the boundary."""
        bb = body.boundingBox
        xs, ys, zs = [], [], []
        for cx in (bb.minPoint.x, bb.maxPoint.x):
            for cy in (bb.minPoint.y, bb.maxPoint.y):
                for cz in (bb.minPoint.z, bb.maxPoint.z):
                    q = _apply3(lin, [cx * 10.0, cy * 10.0, cz * 10.0])
                    xs.append(q[0])
                    ys.append(q[1])
                    zs.append(q[2])
        return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs),
                (min(xs), min(ys), min(zs)))

    def mat3d(lin, tx, ty, tz):
        """A Fusion Matrix3D carrying exactly `lin` and a translation in mm.

        Built with setCell rather than an array, so nothing here depends on
        whether asArray is row-major, and read back AFTER the translation is
        set - if the translation had landed in the wrong cells it would have
        overwritten part of the rotation, which is a silently wrong
        orientation rather than an error."""
        m = M3()
        for r in range(3):
            for c in range(3):
                m.setCell(r, c, lin[r][c])
        m.translation = V3(tx / 10.0, ty / 10.0, tz / 10.0)
        for r in range(3):
            for c in range(3):
                assert abs(m.getCell(r, c) - lin[r][c]) < EPS, (
                    'Matrix3D did not keep the linear part it was given - '
                    'cell (%d, %d) is %.6f, not %.6f'
                    % (r, c, m.getCell(r, c), lin[r][c]))
        return m

    # ---- what to build -----------------------------------------------------
    # ONLY_PLATES names plate KEYS out of PLATE_OF. Checking them against the
    # table's own values is what turns a typo into an assert instead of an
    # empty plate that exports 1.7 KB and looks like a success.
    keys = None
    if ONLY_PLATES is not None:
        want = ([ONLY_PLATES] if isinstance(ONLY_PLATES, (int, str))
                else list(ONLY_PLATES))
        for k in want:
            if SPLIT_BY_COLOUR and any(
                    str(v) == k or str(v).startswith(k + '_')
                    for v in PLATE_OF.values()):
                continue
            assert k in set(PLATE_OF.values()), (
                'ONLY_PLATES names plate %r, which is not a key in PLATE_OF. '
                'The plates are %s.'
                % (k, sorted(set(PLATE_OF.values()), key=str)))
        keys = set(want)
    for nm in ONLY:
        assert any(nm == row[0] for row in ORIENT), (
            'ONLY names %r, which is not a part in ORIENT - it would have been '
            'silently dropped' % nm)

    # ---- measure every piece in its PRINT orientation ----------------------
    pieces = []
    for name, qty, spec, note in ORIENT:
        if keys is not None:
            _k = str(PLATE_OF.get(name))
            if not (_k in keys or any(_k.startswith(str(w) + '_') for w in keys)):
                continue
        if ONLY and name not in ONLY:
            continue
        assert name not in MIRRORED or qty == 2, (
            '%s is a mirrored pair but ORIENT asks for %d copies. The mirror '
            'is copy 1 of exactly 2; any other count and which copy is the '
            'mirror becomes a guess.' % (name, qty))
        full = 'robotarm_' + name
        assert full in comps, '%s not in this document' % full
        comp = comps[full]
        if SPLIT_BY_COLOUR:
            _b = comp.bRepBodies.item(0)
            _ap = (_b.appearance.name if _b.appearance else '')
            _col = 'green' if 'green' in _ap.lower() else 'white'
            PLATE_OF[name] = '%s_%s' % (PLATE_OF[name], _col)
        assert comp.bRepBodies.count == 1, '%s is not one body' % name
        body = comp.bRepBodies.item(0)
        vol = body.volume * 1000.0
        # THE LEDGER IS THE GATE'S SIGNATURE ON THIS GEOMETRY. If a part has
        # been redesigned since _volumes.json was last written - wrist_roll
        # has, it is a clamshell half now and the ledger still holds the
        # monolith - this fails, and the fix is to re-run _check_ledger and
        # read the numbers, NOT to relax the tolerance here. A plate exported
        # past this assert is a photograph of a part no gate has seen.
        assert abs(vol - ledger[name]) <= 1.0, (
            '%s is %.3f but the ledger says %.3f - this is not the geometry '
            'the gates passed. Re-run models/robotarm/_check_ledger.py and '
            'rewrite specs/robotarm/_volumes.json before exporting.'
            % (name, vol, ledger[name]))
        pad = BRIM_PAD.get(name, 0.0)
        for k in range(qty):
            # COPY 1 OF A MIRRORED PAIR IS A DIFFERENT SOLID, not a second
            # print of the same one. Everything downstream carries the flag,
            # and check3 proves it on the matrix that actually gets used.
            mirror = name in MIRRORED and k == 1
            lin = place3(spec, mirror, False)
            check3(name, spec, mirror, False, lin)
            if name == 'wrist_roll':
                # THE PART'S OWN RULE, ANCHORED TO ITS OWN PARAMETER. The
                # outer side face is the +X face at wro_half_x and the split
                # face is at x = 0, so "outer face on the bed, built -X" is
                # exactly "local +X maps to straight down". Read half_x out of
                # the document rather than typing 12.0, because the day it
                # stops being positive this assert is the thing that notices.
                #
                # Getting this wrong is not cosmetic. Split-face-down re-roofs
                # the servo bay as a 618 mm2 ceiling on a 22.9 mm bridge, puts
                # roofs back on both tab slots and the keyway, and turns the
                # rotator half bore into an arch over MAX_OVERHANG_DEG - which
                # is the print the bench has already rejected twice.
                ph = ups.itemByName('wro_half_x')
                assert ph is not None, (
                    'wro_half_x is not in this document - wrist_roll.py has '
                    'not been run here, so nothing can confirm which face is '
                    'the outer one')
                assert ph.value > 0, (
                    'wro_half_x is %.4f: this half is not on +X any more and '
                    'the orientation below is pointing the wrong way'
                    % ph.value)
                built = _apply3(lin, [1.0, 0.0, 0.0])
                assert max(abs(built[i] - DOWN3[i]) for i in range(3)) < EPS, (
                    'wrist_roll copy %d: local +X - the OUTER face at '
                    'wro_half_x - points %s, not straight down. This is '
                    'split-face-down or worse, and split-face-down re-roofs '
                    'the servo bay.'
                    % (k, tuple(round(b, 4) for b in built)))
            w, d, h, lo = measure(body, lin)
            pieces.append(dict(name=name, comp=comp, body=body, spec=spec,
                               mirror=mirror, note=note,
                               w=w + 2 * pad, d=d + 2 * pad, h=h, vol=vol,
                               pad=pad, raw=(w, d), yaw=False, lo=lo, idx=k))

    # ---- arrange WITHIN each assigned plate --------------------------------
    # DEEPEST first, tallest as the tie-break. Sorting by height first read
    # better but packed badly: turntable_ring is 100 x 100 and only 4 mm tall,
    # so it sorted to the end and missed the shelf its identically-sized twin
    # turntable_stator had already opened. Shelf packing wants like depths
    # adjacent; height only decides ties.
    #
    # The shelf pass keeps every shelf open and tries them all - including
    # both ways round - before opening a new one. The first version was a
    # single forward pass and it cost a whole plate: base_lid is 171.8 deep,
    # so its row owned the bed and the 256 x 68 strip left underneath was
    # never revisited. Still simple enough to read, which matters more than
    # optimal: a packer nobody can check is a packer nobody should trust.
    groups = {}
    for pc in pieces:
        if AUTO_SPLIT:
            groups.setdefault(99, []).append(pc)
            continue
        assert pc['name'] in PLATE_OF, '%s has no plate assigned' % pc['name']
        groups.setdefault(PLATE_OF[pc['name']], []).append(pc)

    plates = []
    # ints before names, each in its own order - sorted() will not compare an
    # int with a str, and 'wrist' is a plate key now
    for key in sorted(groups, key=lambda k: (isinstance(k, str), str(k))):
        items = sorted(groups[key], key=lambda p: (-p['d'], -p['h'], -p['w']))
        shelves, items_done, for_key = [], [], []
        for pc in items:
            assert (pc['w'] <= BED_X - 2 * MARGIN
                    and pc['d'] <= BED_Y - 2 * MARGIN), (
                '%s is %.1f x %.1f and does not fit a %.0f x %.0f bed'
                % (pc['name'], pc['w'], pc['d'], BED_X, BED_Y))
            # YAW IS FREE. Turning a part 90 deg about the BED's z does not
            # change which face is on the bed, so it costs nothing in print
            # quality and it is the difference between this fitting and not.
            # (Free only because the yaw is composed AFTER the print rotation
            # - see place3. Composed before it, in the part's own frame, it is
            # a barrel roll and it is not free at all.) Try both ways round on
            # every shelf before opening a new one.
            done = False
            for sh in shelves:
                for yaw in (False, True):
                    w, d = (pc['d'], pc['w']) if yaw else (pc['w'], pc['d'])
                    if (d <= sh['d'] + 1e-9
                            and sh['x'] + w <= BED_X - MARGIN + 1e-9):
                        pc['yaw'] = yaw
                        pc['w'], pc['d'] = w, d
                        pc['x'], pc['y'] = sh['x'], sh['y']
                        sh['x'] += w + GAP
                        done = True
                        break
                if done:
                    break
            if done:
                # BOOK IT ONTO THE PLATE. Missing this line placed the part
                # correctly and then dropped it from the plate's own list:
                # the run reported '12 pieces' and exported five, because
                # everything that shared an existing shelf was positioned and
                # then forgotten.
                items_done.append(pc)
                continue
            top = MARGIN
            for sh in shelves:
                top = max(top, sh['y'] + sh['d'] + GAP)
            # opening a shelf: take whichever way round is SHALLOWER, since
            # shelf depth is what runs the plate out of room
            if pc['d'] > pc['w'] and top + pc['w'] <= BED_Y - MARGIN + 1e-9:
                pc['yaw'] = True
                pc['w'], pc['d'] = pc['d'], pc['w']
            if top + pc['d'] > BED_Y - MARGIN + 1e-9:
                if AUTO_SPLIT:
                    for_key.append(items_done)
                    items_done, shelves = [], []
                    top = MARGIN
                else:
                    raise AssertionError(
                        'plate %r is full: %s (%.1f x %.1f) will not fit. Move '
                        'something to another plate in PLATE_OF rather than '
                        'letting a packer decide - the grouping is deliberate.'
                        % (key, pc['name'], pc['w'], pc['d']))
            sh = dict(y=top, d=pc['d'], x=MARGIN)
            pc['x'], pc['y'] = sh['x'], sh['y']
            sh['x'] += pc['w'] + GAP
            shelves.append(sh)
            items_done.append(pc)
        for_key.append(items_done)
        # A key normally makes one plate. Only the AUTO_SPLIT bucket can
        # overflow into more, and then the label carries the sequence so two
        # files never claim the same name.
        for seq, plate in enumerate(for_key):
            label = str(key) if len(for_key) == 1 else '%s_%d' % (key, seq + 1)
            plates.append((key, label, plate))

    # the conflict rule is now structural, but assert it anyway - a future
    # edit to PLATE_OF is exactly the kind of thing that quietly breaks it
    for key, label, plate in plates:
        here = set(p['name'] for p in plate)
        for a, b in NEVER_TOGETHER:
            assert not (a in here and b in here), (
                'plate %s has both %s and %s, whose settings are '
                'incompatible' % (label, a, b))

    # ---- prove the packing before building anything ------------------------
    # Two copies of one part are two rectangles here like any others - the
    # mirrored half gets the same treatment as everything else, and there is
    # no branch it can take that skips this.
    for key, label, plate in plates:
        for a in range(len(plate)):
            pa = plate[a]
            assert pa['x'] >= MARGIN - 1e-6 and pa['y'] >= MARGIN - 1e-6, (
                'plate %s: %s starts off the bed' % (label, pa['name']))
            assert pa['x'] + pa['w'] <= BED_X - MARGIN + 1e-6, (
                'plate %s: %s runs off in X' % (label, pa['name']))
            assert pa['y'] + pa['d'] <= BED_Y - MARGIN + 1e-6, (
                'plate %s: %s runs off in Y' % (label, pa['name']))
            for b in range(a + 1, len(plate)):
                pb = plate[b]
                gap_x = (pa['x'] + pa['w'] <= pb['x'] + 1e-6
                         or pb['x'] + pb['w'] <= pa['x'] + 1e-6)
                gap_y = (pa['y'] + pa['d'] <= pb['y'] + 1e-6
                         or pb['y'] + pb['d'] <= pa['y'] + 1e-6)
                assert gap_x or gap_y, (
                    'plate %s: %s and %s overlap'
                    % (label, pa['name'], pb['name']))

    # ---- build and export --------------------------------------------------
    os.makedirs(OUT_DIR, exist_ok=True)
    STALE = 'robotarm_plate'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c.name.startswith(STALE):
            c.name = STALE + '_stale_' + str(i)
    for o in list(root.occurrences):
        if o.component.name.startswith(STALE + '_stale_'):
            o.deleteMe()

    made = []
    for key, label, plate in plates:
        pocc = root.occurrences.addNewComponent(M3())
        pocc.component.name = '%s_%s' % (STALE, label)
        pc = pocc.component
        pending = []
        for p in plate:
            # REBUILT, NOT PATCHED. The placement is composed once more from
            # the same three facts - print orientation, mirror, yaw - so the
            # matrix that gets used is the matrix that gets checked, and the
            # yaw is not a fix-up applied to a matrix measured without it.
            lin = place3(p['spec'], p['mirror'], p['yaw'])
            check3(p['name'], p['spec'], p['mirror'], p['yaw'], lin)
            w, d, h, lo = measure(p['body'], lin)
            # THE RESERVED RECTANGLE HAS TO BE THE PRINTED ONE. The packer
            # reserved w x d by swapping the unyawed pair; if the yaw did
            # anything other than swap them - which is exactly what a yaw
            # composed in the part's own frame does - the overlap proof above
            # was proving something about rectangles that do not exist.
            assert (abs(w - (p['w'] - 2 * p['pad'])) < 1e-6
                    and abs(d - (p['d'] - 2 * p['pad'])) < 1e-6), (
                'plate %s: %s was packed as %.2f x %.2f but places as %.2f x '
                '%.2f - the yaw is not a yaw'
                % (label, p['name'], p['w'] - 2 * p['pad'],
                   p['d'] - 2 * p['pad'], w, d))
            assert abs(h - p['h']) < 1e-6, (
                'plate %s: %s was measured %.2f tall and places %.2f tall'
                % (label, p['name'], p['h'], h))
            m = mat3d(lin,
                      p['x'] + p['pad'] - lo[0],
                      p['y'] + p['pad'] - lo[1],
                      0.0 - lo[2])
            # A MIRRORED PIECE CANNOT BE AN OCCURRENCE. This line was
            # `pc.occurrences.addExistingComponent(p['comp'], m)` and it threw
            # "3 : invalid argument transform" on the wrist plate, every time,
            # because wrist_roll's second copy is a MIRROR - determinant -1 -
            # and Fusion will not hang an occurrence off a matrix that turns
            # the world inside out. The armstack plates never hit it; the
            # wrist plate could not be exported at all.
            #
            # TemporaryBRepManager DOES take a det -1 matrix, verified against
            # this part: a 12.00 x 30.70 x 35.90 half at X 0..12 comes back at
            # X -12..0 with its 6609.201 mm3 intact. So every piece is placed
            # as a transformed BODY under one BaseFeature instead, which is
            # one code path for both handednesses rather than a special case
            # that only the mirrored parts exercise.
            copy = _TB.copy(p['body'])
            assert _TB.transform(copy, m), (
                'plate %s: the transform was refused for %s' % (label, p['name']))
            pending.append((p['name'], copy))
        bf = pc.features.baseFeatures.add()
        bf.startEdit()
        for nm, tb_body in pending:
            pc.bRepBodies.add(tb_body, bf).name = nm
        bf.finishEdit()

        # RE-MEASURE what was actually built, do not trust the arithmetic
        for k in range(pc.bRepBodies.count):
            o = pc.bRepBodies.item(k)
            if True:
                bb = o.boundingBox
                assert bb.minPoint.z * 10 > -0.01, (
                    'plate %s: %s sits below the bed at z %.3f'
                    % (label, o.name, bb.minPoint.z * 10))
                assert bb.minPoint.z * 10 < 0.01, (
                    'plate %s: %s floats %.3f above the bed'
                    % (label, o.name, bb.minPoint.z * 10))
                assert (bb.minPoint.x * 10 > -0.01
                        and bb.maxPoint.x * 10 < BED_X + 0.01
                        and bb.minPoint.y * 10 > -0.01
                        and bb.maxPoint.y * 10 < BED_Y + 0.01), (
                    'plate %s: %s lands outside the bed'
                    % (label, o.name))
        assert pc.bRepBodies.count == len(plate), (
            'plate %s: %d pieces were packed and %d bodies were placed'
            % (label, len(plate), pc.bRepBodies.count))
        # A HIDDEN OCCURRENCE EXPORTS AS AN EMPTY FILE. Lighting the plate
        # itself is not enough - each child occurrence inside it carries its
        # own state, and it inherits whatever the source occurrence had when
        # it was added. Any earlier script that toggled bulbs for a render
        # leaves them off, and the export comes back as a 1.7 KB header.
        pocc.isLightBulbOn = True
        for k in range(pc.bRepBodies.count):
            pc.bRepBodies.item(k).isLightBulbOn = True
        lit = sum(1 for k in range(pc.bRepBodies.count)
                  if pc.bRepBodies.item(k).isLightBulbOn)
        assert lit == pc.bRepBodies.count, (
            'plate %s: only %d of %d parts are visible - the export would be '
            'short' % (label, lit, pc.bRepBodies.count))
        path = os.path.join(OUT_DIR, 'plate_%s_v%d.3mf' % (label, VERSION))
        assert not os.path.exists(path), '%s exists - bump VERSION' % path
        em = design.exportManager
        em.execute(em.createC3MFExportOptions(pc, path))
        size = os.path.getsize(path)
        assert size > 50000, 'plate %s exported %d bytes' % (label, size)
        made.append((key, label, plate, path, size))

    def grams(vol_mm3):
        return vol_mm3 * PETG * SOLID / 1000.0

    print('=== %d plate(s), %.0f x %.0f bed, %.0f margin / %.0f gap ==='
          % (len(plates), BED_X, BED_Y, MARGIN, GAP))
    print('SELECTION: plates %s | parts %s'
          % ('ALL' if keys is None else sorted(keys, key=str),
             'ALL' if not ONLY else ONLY))
    print('MASS: solid mm3 x %.2f g/cm3 x %.2f packing / 1000. Solid volume is '
          'MEASURED off the body;' % (PETG, SOLID))
    print('  the %.2f is the usual walls-and-infill factor for this project '
          'and is ASSUMED.' % SOLID)
    print('')
    total_g = 0.0
    for key, label, plate, path, size in made:
        g = sum(grams(p['vol']) for p in plate)
        total_g += g
        tall = max(p['h'] for p in plate)
        used = sum(p['w'] * p['d'] for p in plate)
        span_x = (min(p['x'] for p in plate),
                  max(p['x'] + p['w'] for p in plate))
        span_y = (min(p['y'] for p in plate),
                  max(p['y'] + p['d'] for p in plate))
        needs = sorted(set(p['name'] for p in plate if p['name'] == 'forearm'))
        brims = sorted(set(p['name'] for p in plate if p['pad']))
        print('PLATE %s - %d pieces, %.1f g, tallest %.1f mm, %.0f%% of the bed'
              % (label, len(plate), g, tall,
                 100.0 * used / (BED_X * BED_Y)))
        print('  footprint used: X %.1f..%.1f  Y %.1f..%.1f  (%.1f x %.1f mm)'
              % (span_x[0], span_x[1], span_y[0], span_y[1],
                 span_x[1] - span_x[0], span_y[1] - span_y[0]))
        # PLATE_NOTE describes the grouping in PLATE_OF. ONLY_PLATES selects
        # whole plates so the note still describes what is there; ONLY does
        # not, and on a part-level subset the note would be describing a plate
        # that does not exist - it once read 'forearm SUPPORTS' on a plate
        # with no forearm on it.
        if not ONLY:
            print('  %s' % PLATE_NOTE.get(key, ''))
        print('  supports: %s | brim: %s'
              % (', '.join(needs) if needs else 'NONE - leave them off',
                 ', '.join(brims) if brims else 'none'))
        for p in plate:
            if p['h'] >= TALL_MM:
                mid = p['y'] + p['d'] / 2.0
                where = ('back' if mid > 2 * BED_Y / 3 else
                         'front' if mid < BED_Y / 3 else 'middle')
                print('  TALL: %s, %.0f mm, sitting %s (y centre %.0f). It is '
                      'the knock-off risk on this plate.'
                      % (p['name'], p['h'], where, mid))
        pairs = sorted(set(p['name'] for p in plate if p['mirror']))
        for nm in pairs:
            print('  MIRRORED PAIR: %s. The two bodies on this plate are NOT '
                  'interchangeable - one is the mirror image of the other and '
                  'only one goes on each side.' % nm)
        print('  %s  (%d bytes)' % (os.path.basename(path), size))
        for p in sorted(plate, key=lambda q: (q['x'], q['y'])):
            extra = ' (+%.0f brim)' % p['pad'] if p['pad'] else ''
            print('    %-15s%-9s %6.1f x %-6.1f h %-5.1f %6.2f g  at (%5.1f,'
                  ' %5.1f)%s  %s'
                  % (p['name'], ' MIRRORED' if p['mirror'] else '',
                     p['raw'][0], p['raw'][1], p['h'], grams(p['vol']),
                     p['x'] + p['pad'], p['y'] + p['pad'], extra,
                     p['note'] if p['idx'] == 0 else ''))
        print('')
    print('%d pieces, %.1f g of PETG total' % (len(pieces), total_g))
    print('')
    _sup = sorted(set(p['name'] for _k, _l, pl, _p, _s in made for p in pl
                      if p['name'] == 'forearm'))
    print('SUPPORTS: %s. OFF everywhere else - on turntable_stator that is'
          % (', '.join(_sup) if _sup else 'NONE on these plates'))
    print('  not a preference, the axle bridge is load-bearing.')
    print('BRIM: base_lid. Budget 5-8 mm of extra footprint for it.')
    print('Orientations are BAKED IN. If you auto-arrange in the slicer, keep')
    print('  rotation locked, and NEVER let it "optimise" a mirrored pair -')
    print('  gripcut_finger and pruner_rack will flip, and a wrist_roll half')
    print('  un-mirrored is a part that does not go on the wrist at all.')
