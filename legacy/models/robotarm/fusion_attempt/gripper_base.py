"""robotarm/gripper_base — Fusion MCP generating script (v3, clamshell).

Rebuilds `robotarm_gripper_base` (idempotent; occurrence at z = 52.6 on the
roll horn). Local frame: roll axis = Z through origin, plate bottom z = 0.

v3 (Jonathan: "it's more like a clam shell"): the stationary piece is one
part that does all three jobs — wrist connection (roll-horn interface under
the plate), motor mount (servo wall, grip SG90 shaft = the clam hinge axis
at (0, 30)), and the FIXED clamshell half: an annular shell r 27..30 about
the hinge, sweeping −85°..−2° from the plate up to the mouth, 21 wide,
with a foot joining it to the plate. The moving shell (gripper_jaws.py)
mirrors it above and closes rim-to-rim.

Shell arcs are 5°-faceted polygons for robustness; smooth with real arcs
in the finish pass if the facets bother the print.

Spec: specs/robotarm/gripper_base.md
"""

import math

import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    def allprofs(sk):
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    for occ in list(root.occurrences):
        if occ.component.name == 'robotarm_gripper_base':
            occ.deleteMe()
    tr = adsk.core.Matrix3D.create()
    tr.translation = adsk.core.Vector3D.create(0, 0, 5.26)
    occ = root.occurrences.addNewComponent(tr)
    gp = occ.component
    gp.name = 'robotarm_gripper_base'

    def extrude(profs, op, start, dist):
        ext = gp.features.extrudeFeatures
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start))
        inp.setDistanceExtent(False, V(dist))
        return ext.add(inp)

    def mptXY(sk_, x, y):
        return sk_.modelToSketchSpace(P3(x, y, 0))

    def mptXZ(sk_, x, z):
        return sk_.modelToSketchSpace(P3(x, 0, z))

    def polygonXZ(sk_, pts):
        lines = sk_.sketchCurves.sketchLines
        n = len(pts)
        for i in range(n):
            a = mptXZ(sk_, pts[i][0], pts[i][1])
            b = mptXZ(sk_, pts[(i + 1) % n][0], pts[(i + 1) % n][1])
            lines.addByTwoPoints(a, b)

    def shell_pts(a0, a1, r_in=2.7, r_out=3.0, cx=0.0, cz=3.0):
        pts = []
        steps = max(4, int(abs(a1 - a0) / 5))
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.append((cx + r_out * math.cos(a), cz + r_out * math.sin(a)))
        for i in range(steps + 1):
            a = math.radians(a1 + (a0 - a1) * i / steps)
            pts.append((cx + r_in * math.cos(a), cz + r_in * math.sin(a)))
        return pts

    # plate + roll-horn interface (the wrist connection)
    sk = gp.sketches.add(gp.xYConstructionPlane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(mptXY(sk, -2.3, -1.7), mptXY(sk, 2.3, 1.7))
    extrude(allprofs(sk), NEW, '0.0 mm', '4.0 mm')
    sk2 = gp.sketches.add(gp.xYConstructionPlane)
    sk2.sketchCurves.sketchLines.addTwoPointRectangle(mptXY(sk2, -1.62, -0.37), mptXY(sk2, 1.62, 0.37))
    sk2.sketchCurves.sketchLines.addTwoPointRectangle(mptXY(sk2, -0.37, -1.62), mptXY(sk2, 0.37, 1.62))
    extrude(allprofs(sk2), CUT, '0.0 mm', '1.8 mm')
    sk3 = gp.sketches.add(gp.xYConstructionPlane)
    sk3.sketchCurves.sketchCircles.addByCenterRadius(mptXY(sk3, 0, 0), 0.45)
    for x, y in ((0.7, 0), (-0.7, 0), (0, 0.7), (0, -0.7)):
        sk3.sketchCurves.sketchCircles.addByCenterRadius(mptXY(sk3, x, y), 0.11)
    extrude(allprofs(sk3), CUT, '0.0 mm', '4.0 mm')

    # motor mount: wall with the grip servo's shaft = hinge axis at (0, 30)
    sk4 = gp.sketches.add(gp.xYConstructionPlane)
    sk4.sketchCurves.sketchLines.addTwoPointRectangle(mptXY(sk4, -2.3, -0.2), mptXY(sk4, 2.3, 0.2))
    extrude(allprofs(sk4), JOIN, '4.0 mm', '36.0 mm')
    sk5 = gp.sketches.add(gp.xZConstructionPlane)
    sk5.sketchCurves.sketchCircles.addByCenterRadius(mptXZ(sk5, 0.0, 3.0), 0.65)
    sk5.sketchCurves.sketchCircles.addByCenterRadius(mptXZ(sk5, -0.84, 3.0), 0.09)
    sk5.sketchCurves.sketchCircles.addByCenterRadius(mptXZ(sk5, 1.94, 3.0), 0.09)
    extrude(allprofs(sk5), CUT, '-2.0 mm', '4.0 mm')

    # fixed clamshell half + foot to the plate
    sk6 = gp.sketches.add(gp.xZConstructionPlane)
    polygonXZ(sk6, shell_pts(-85.0, -2.0))
    extrude(allprofs(sk6), JOIN, '-4.0 mm', '21.0 mm')
    sk7 = gp.sketches.add(gp.xYConstructionPlane)
    sk7.sketchCurves.sketchLines.addTwoPointRectangle(mptXY(sk7, 0.05, -0.4), mptXY(sk7, 0.45, 1.7))
    extrude(allprofs(sk7), JOIN, '0.0 mm', '6.0 mm')

    b = gp.bRepBodies.item(0)
    print('bodies:', gp.bRepBodies.count, 'vol mm3:', round(b.volume * 1000), 'valid:', b.isValid)
