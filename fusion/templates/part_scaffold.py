"""<project>/<part> — Fusion MCP generating script.

Rebuilds `<project>_<part>` (idempotent). Local frame: <describe axes and
origin>. Spec: specs/<project>/<part>.md — ASSUMED there: <list or 'none'>.

TEMPLATE — copy to models/<project>/<part>.py and replace every <...>.
Reminders: API-internal units are cm; ValueInput.createByString takes mm
expressions and user-parameter math. No try/except. Every sketch
coordinate derives from val('<param>') — never a bare number. Name every
entity, group the timeline by phase, assign the material, print
diagnostics last. See knowledge/fusion_modeling_craft.md; the lint in
tests/ enforces all of it.
"""

import adsk.core
import adsk.fusion

COMPONENT = '<project>_<part>'
BODY_NAME = '<part>'
PREFIX = '<pp>_'                 # short unique user-parameter prefix
MATERIAL_NAME = 'PET Plastic'    # PETG; ABS Plastic / Nylon 6 / Plastic (PLA)


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    # ---- parameters: every dimension, tagged with provenance -------------
    def param(name, expr, comment=''):
        p = ups.itemByName(PREFIX + name)
        if p is None:
            ups.add(PREFIX + name, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(PREFIX + name).value      # internal units: cm

    param('wall', '1.6 mm', 'minimum wall - design_rules')
    # param('<name>', '<value> mm', '<what> - MEASURED|DATASHEET|design_rules|ASSUMED')
    # derived values stay expressions so the chain updates in the UI:
    # param('<name>', '<other>/2 + <another>', 'derived - edit the sources')

    # ---- idempotent rebuild ----------------------------------------------
    for occ in list(root.occurrences):
        if occ.component.name == COMPONENT:
            occ.deleteMe()
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = COMPONENT
    ext = comp.features.extrudeFeatures

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    # ---- helpers ----------------------------------------------------------
    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        if expected is not None:
            assert sk.profiles.count == expected, (
                f'{sk.name}: expected {expected} profile(s), got {sk.profiles.count}')
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr, name):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        f = ext.add(inp)
        f.name = name
        return f

    def group(start_index, name):
        if design.timeline.count > start_index:
            g = design.timeline.timelineGroups.add(start_index, design.timeline.count - 1)
            g.name = name

    def mpt(sk, x_cm, y_cm):     # model coords (cm) -> sketch space
        return sk.modelToSketchSpace(P3(x_cm, y_cm, 0))

    # ---- phase 1: base shape ----------------------------------------------
    t0 = design.timeline.count
    # sk_base = sketch(comp.xYConstructionPlane, 'sk_base')
    # sk_base.sketchCurves.sketchLines.addTwoPointRectangle(
    #     mpt(sk_base, -val('w') / 2, -val('d') / 2),
    #     mpt(sk_base, val('w') / 2, val('d') / 2))
    # extrude(profiles(sk_base, expected=1), NEW, '0.0 mm', PREFIX + 'wall', 'base')
    group(t0, 'base shape')

    # ---- phase 2: features -------------------------------------------------
    t1 = design.timeline.count
    group(t1, 'features')

    # ---- phase 3: finish (fillets, chamfers, lead-ins) ---------------------
    # Required, not optional — knowledge/design_review.md fails a part with
    # no elephant-foot chamfer or no fillet at a loaded junction. Select
    # edges by geometry, never by blind index.
    t2 = design.timeline.count
    group(t2, 'finish')

    # ---- identity: body name + material ------------------------------------
    assert comp.bRepBodies.count == 1, f'expected 1 body, got {comp.bRepBodies.count}'
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break

    # ---- diagnostics (always last) ------------------------------------------
    bb = body.boundingBox
    groups = [design.timeline.timelineGroups.item(i).name
              for i in range(design.timeline.timelineGroups.count)]
    print(f'body: {body.name!r} | material: {body.material.name}')
    print(f'bbox mm: X {bb.minPoint.x*10:.2f}..{bb.maxPoint.x*10:.2f}'
          f'  Y {bb.minPoint.y*10:.2f}..{bb.maxPoint.y*10:.2f}'
          f'  Z {bb.minPoint.z*10:.2f}..{bb.maxPoint.z*10:.2f}')
    print(f'volume: {body.volume*1000:.0f} mm3'
          f' | mass: {body.physicalProperties.mass*1000:.1f} g'
          f' | valid: {body.isValid}')
    print(f'bodies: {comp.bRepBodies.count} | sketches: {comp.sketches.count}'
          f' | user params: {ups.count}')
    print(f'timeline groups: {groups}')
