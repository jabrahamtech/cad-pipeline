"""robotarm/pcb_keeper - Fusion MCP generating script.

Rebuilds `robotarm_pcb_keeper` (idempotent). PRINT FOUR.

Spec: specs/robotarm/pcb_keeper.md

THE CLIP THAT STOPS THE ESP32 BOARD RATTLING OUT OF ITS BAY. base_platter
seats the 70 x 50 carrier on four corner ledges inside four L fences, with
1.0 of insertion play (Jonathan: "leave tolerance to put it in"). Play is
what lets it go in by hand, and it is also what lets it walk when J1
reverses. Nothing held it down. The carrier has cables off BOTH faces, so
there is no room for a screw boss under it and no guarantee of mounting
holes - which is why the base grips the CORNERS, and why this does too.

HOW IT HOLDS. An L-shaped cap pushed straight down over each corner fence:

    plate    1.6 over the fence top
    sleeve   1.6 down the fence's OUTER face - PRESS 0.15 against the boss
    boss     down the fence's INNER face, into the 0.5 play gap, and on
             over the board edge by the tongue (1.5) to the board's top face

The fence is clamped between sleeve and boss with the calibrated 0.15 press
(design_rules JOINT_FIT_MM['press']), so the keeper stays where it is put
and levers off with a fingernail. The boss is modelled 0.2 INTO the board
top (preload, ASSUMED), so it bears on the board whatever the PCB's real
thickness - if the board is 0.2 thicker, the keeper just sits 0.2 high on
its press.

WHAT IT COSTS THE BOARD: the outer 1.5 x 2.5 of each corner, top face. A
carrier PCB's corners are normally mounting-hole or bare copper. If Jonathan's
board has a part there, shorten KEEPER_TONGUE_MM in lib/esp_bay.

SYMMETRIC ABOUT THE CORNER DIAGONAL on purpose: every leg is the short-leg
length, so one part fits all four corners (a mirror image of it is a
rotation of it). The gate places it that way.

Print orientation: plate DOWN on the bed, sleeve and boss up. No support.

Frame: origin on the board corner, board in +X +Y, z 0 the board's TOP face.
"""

import os
import sys

REPO = os.path.expanduser('~/Documents/GitHub/cad-pipeline')
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import adsk.core  # noqa: E402
import adsk.fusion  # noqa: E402

from lib.design_rules import JOINT_FIT_MM as _FIT  # noqa: E402
from lib.design_rules import MIN_WALL_MM  # noqa: E402
from lib.esp_bay import (  # noqa: E402
    ESP_CLEAR_MM, FENCE_T_MM, FENCE_OVER_MM, LEDGE_MM,
    KEEPER_TONGUE_MM, KEEPER_PRELOAD_MM,
)
from lib.palette import hints_for  # noqa: E402

MATERIAL_NAME = 'PET Plastic'
COMPONENT = 'robotarm_pcb_keeper'
BODY_NAME = 'pcb_keeper'
PREFIX = 'pk_'
APPEARANCE_HINTS = hints_for('base_platter')

PH_PLATE = 'plate'
PH_GRIP = 'sleeve and boss'
PHASES = [PH_PLATE, PH_GRIP]
TOL = 1e-9                     # comparison epsilon, not a dimension
QTY = 4                        # one per board corner


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def param(name, expr, comment=''):
        full = PREFIX + name
        p = ups.itemByName(full)
        if p is None:
            ups.add(full, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value

    # --- the fence it grips: lib/esp_bay, the numbers base_platter cut ---
    param('fence_t', '%.2f mm' % FENCE_T_MM, 'lib/esp_bay.FENCE_T_MM')
    param('play', '%.2f mm' % (ESP_CLEAR_MM / 2), 'lib/esp_bay.ESP_CLEAR_MM / 2 - board edge to fence')
    param('fence_over', '%.2f mm' % FENCE_OVER_MM, 'lib/esp_bay.FENCE_OVER_MM - fence top above board top')
    param('reach', '%.2f mm' % LEDGE_MM,
          'lib/esp_bay.LEDGE_MM - the SHORT leg\'s run past the board corner;\n'
          '           both legs of the keeper stop here, so it fits every corner')
    # --- the keeper ---
    param('press', '%.2f mm' % _FIT['press'], 'design_rules JOINT_FIT_MM press - total, on the fence')
    param('preload', '%.2f mm' % KEEPER_PRELOAD_MM, 'lib/esp_bay - modelled bite into the board top')
    param('tongue', '%.2f mm' % KEEPER_TONGUE_MM, 'lib/esp_bay - lap onto the board top')
    param('plate_t', '%.2f mm' % MIN_WALL_MM, 'MIN_WALL')
    param('sleeve_t', '%.2f mm' % MIN_WALL_MM, 'MIN_WALL')
    param('grip', PREFIX + 'fence_over', 'sleeve depth down the fence - the whole fence height')

    f_in = -val('play')                         # fence inner face
    f_out = f_in - val('fence_t')               # fence outer face
    s_in = f_out + val('press') / 2             # sleeve inner face
    s_out = f_out - val('sleeve_t')             # the keeper's outer corner
    b_out = f_in - val('press') / 2             # boss face, into the fence
    reach = val('reach')
    tongue = val('tongue')

    assert tongue < reach - TOL, 'the tongue is as long as the arms - no L left'
    assert tongue - b_out >= MIN_WALL_MM / 10 - TOL, (
        'the boss is %.2f thick - MIN_WALL %.2f' % ((tongue - b_out) * 10, MIN_WALL_MM))
    assert val('tongue') * 10 <= LEDGE_MM + TOL, (
        'the tongue reaches past the ledge under the board - it would press '
        'the board where nothing holds it up')
    assert val('grip') <= val('fence_over') + TOL, 'the sleeve is deeper than the fence'

    # ---- idempotent rebuild: RENAME FIRST, THEN DELETE --------------------
    STALE = COMPONENT + '_stale_'
    for i in range(design.allComponents.count):
        c = design.allComponents.item(i)
        if c == design.rootComponent:
            continue
        if c.name == COMPONENT or c.name.startswith(COMPONENT + ' ('):
            c.name = STALE + str(i)
    for occ in list(root.occurrences):
        if occ.component.name.startswith(STALE):
            occ.deleteMe()
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = COMPONENT
    assert comp.name == COMPONENT, 'a stale component still holds the name'
    ext = comp.features.extrudeFeatures
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation

    def ell(name, a, w, z0_expr, dz_expr, op):
        """An L about the corner: [a, reach] x [a, w] U [a, w] x [a, reach]."""
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'sk_' + name
        pts = [(a, a), (reach, a), (reach, w), (w, w), (w, reach), (a, reach)]
        lines = sk.sketchCurves.sketchLines
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            lines.addByTwoPoints(P3(x0, y0, 0.0), P3(x1, y1, 0.0))
        assert sk.profiles.count == 1, '%s made %d profiles' % (sk.name, sk.profiles.count)
        inp = ext.createInput(sk.profiles.item(0), op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(z0_expr))
        inp.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(V(dz_expr)),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        if op == JOIN:
            inp.participantBodies = [comp.bRepBodies.item(0)]
        f = ext.add(inp)
        f.name = name
        return f

    def group(start, name):
        if design.timeline.count - start > 1:
            g = design.timeline.timelineGroups.add(start, design.timeline.count - 1)
            g.name = name

    t0 = design.timeline.count
    ell('plate', s_out, tongue, PREFIX + 'fence_over', PREFIX + 'plate_t', NEW)
    group(t0, PH_PLATE)

    t1 = design.timeline.count
    ell('sleeve', s_out, s_in, PREFIX + 'fence_over - ' + PREFIX + 'grip',
        PREFIX + 'grip', JOIN)
    ell('boss', b_out, tongue, '-' + PREFIX + 'preload',
        PREFIX + 'fence_over + ' + PREFIX + 'preload', JOIN)
    group(t1, PH_GRIP)

    assert comp.bRepBodies.count == 1, 'the keeper came out in %d pieces' % comp.bRepBodies.count
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break
    used_appearance = 'none'
    for want in APPEARANCE_HINTS:
        for i in range(app.materialLibraries.count):
            apps = app.materialLibraries.item(i).appearances
            for j in range(apps.count):
                a = apps.item(j)
                if all(w.lower() in a.name.lower() for w in want):
                    body.appearance = a
                    used_appearance = a.name
                    break
            if used_appearance != 'none':
                break
        if used_appearance != 'none':
            break

    props = body.physicalProperties
    bb = body.boundingBox
    print("body: '%s' | appearance: %s | PRINT FOUR, plate down"
          % (body.name, used_appearance))
    print('grips a %.2f fence in a %.2f slot (press %.2f); tongue %.2f onto the '
          'board, %.2f preload' % (val('fence_t') * 10, (b_out - s_in) * 10,
                                   val('press') * 10, tongue * 10, val('preload') * 10))
    print('   keep the outer %.1f x %.1f of each board corner clear on top'
          % (tongue * 10, reach * 10))
    print('bbox mm: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
          % (bb.minPoint.x * 10, bb.maxPoint.x * 10,
             bb.minPoint.y * 10, bb.maxPoint.y * 10,
             bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print('volume mm3: %.3f | mass g: %.2f (x4 = %.2f) | valid: %s'
          % (props.volume * 1000, props.mass * 1000, QTY * props.mass * 1000, body.isValid))
    print('timeline groups: %r' % (PHASES,))
