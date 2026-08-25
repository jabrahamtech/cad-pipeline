"""<project>/<part> — Fusion MCP generating script.

Rebuilds `<project>_<part>` (idempotent). Local frame: <describe axes and
origin>. Spec: specs/<project>/<part>.md — ASSUMED there: <list or 'none'>.

TEMPLATE — copy to models/<project>/<part>.py and replace every <...>.
Reminders: API-internal units are cm; ValueInput.createByString takes mm
expressions and user-parameter math. No try/except. Print diagnostics last.
"""

import adsk.core
import adsk.fusion

COMPONENT = '<project>_<part>'
PREFIX = '<pp>_'  # short unique user-parameter prefix for this part


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    # --- user parameters: every dimension, tagged with provenance ---------
    def param(name, expr, comment=''):
        p = ups.itemByName(PREFIX + name)
        if p is None:
            ups.add(PREFIX + name, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value  # internal units: cm

    param('wall', '1.6 mm', 'minimum wall - design_rules')
    # param('<name>', '<value> mm', '<what it is> - MEASURED|DATASHEET|design_rules|ASSUMED')

    # --- idempotent rebuild ----------------------------------------------
    for occ in list(root.occurrences):
        if occ.component.name == COMPONENT:
            occ.deleteMe()
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = COMPONENT

    # --- helpers ----------------------------------------------------------
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def allprofs(sk):
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr):
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        return ext.add(inp)

    def mpt(sk_, x_cm, y_cm):  # model coords (cm) -> sketch space
        return sk_.modelToSketchSpace(P3(x_cm, y_cm, 0))

    # --- phase 1: base shape ---------------------------------------------
    # sk = comp.sketches.add(comp.xYConstructionPlane)
    # sk.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk, ..., ...), mpt(sk, ..., ...))
    # extrude(allprofs(sk), NEW, '0.0 mm', PREFIX + 'wall')

    # --- diagnostics (always last) ---------------------------------------
    b = comp.bRepBodies.item(0)
    bb = b.boundingBox
    print('bodies:', comp.bRepBodies.count)
    print(f'bbox mm: X {bb.minPoint.x*10:.2f}..{bb.maxPoint.x*10:.2f}'
          f'  Y {bb.minPoint.y*10:.2f}..{bb.maxPoint.y*10:.2f}'
          f'  Z {bb.minPoint.z*10:.2f}..{bb.maxPoint.z*10:.2f}')
    print(f'volume: {b.volume*1000:.0f} mm3, valid: {b.isValid}')
