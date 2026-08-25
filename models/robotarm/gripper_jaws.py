"""robotarm/gripper_jaws — Fusion MCP generating script (v3, clamshell).

Rebuilds `robotarm_jaw_moving` (idempotent; occurrence at z = 52.6, sharing
robotarm_gripper_base's frame). The MOVING clamshell half: an annular shell
r 27..30 about the hinge axis (the grip SG90's shaft at (0, 30)), sweeping
+2°..+85° as modelled (closed pose), 21 wide, carried by a hub on the horn
plus a web arm along 45°. Rims meet the fixed shell's at the mouth (~2 mm
gap as modelled); the servo swings it open. Cross-horn recess 1.8 deep +
Ø6 screw bore retain it on the horn.

Shell arcs are 5°-faceted polygons; smooth in the finish pass if desired.

Spec: specs/robotarm/gripper_jaws.md
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
        if occ.component.name == 'robotarm_jaw_moving':
            occ.deleteMe()
    tr = adsk.core.Matrix3D.create()
    tr.translation = adsk.core.Vector3D.create(0, 0, 5.26)
    occ = root.occurrences.addNewComponent(tr)
    mv = occ.component
    mv.name = 'robotarm_jaw_moving'

    def extrude(profs, op, start, dist):
        ext = mv.features.extrudeFeatures
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start))
        inp.setDistanceExtent(False, V(dist))
        return ext.add(inp)

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

    # hub on the horn plane
    sk8 = mv.sketches.add(mv.xZConstructionPlane)
    sk8.sketchCurves.sketchCircles.addByCenterRadius(mptXZ(sk8, 0.0, 3.0), 1.0125)
    extrude(allprofs(sk8), NEW, '10.2 mm', '6.0 mm')

    # web arm hub -> shell along 45deg
    sk9 = mv.sketches.add(mv.xZConstructionPlane)
    d = math.radians(45.0)
    dx, dz = math.cos(d), math.sin(d)
    px, pz = -math.sin(d), math.cos(d)
    w = 0.75
    pts = [(0.8 * dx + w * px, 3.0 + 0.8 * dz + w * pz),
           (2.85 * dx + w * px, 3.0 + 2.85 * dz + w * pz),
           (2.85 * dx - w * px, 3.0 + 2.85 * dz - w * pz),
           (0.8 * dx - w * px, 3.0 + 0.8 * dz - w * pz)]
    polygonXZ(sk9, pts)
    extrude(allprofs(sk9), JOIN, '10.2 mm', '6.0 mm')

    # moving shell half
    sk10 = mv.sketches.add(mv.xZConstructionPlane)
    polygonXZ(sk10, shell_pts(2.0, 85.0))
    extrude(allprofs(sk10), JOIN, '-4.0 mm', '21.0 mm')

    # cross-horn recess + screw bore
    sk11 = mv.sketches.add(mv.xZConstructionPlane)
    sk11.sketchCurves.sketchLines.addTwoPointRectangle(mptXZ(sk11, -1.62, 2.63), mptXZ(sk11, 1.62, 3.37))
    sk11.sketchCurves.sketchLines.addTwoPointRectangle(mptXZ(sk11, -0.37, 1.38), mptXZ(sk11, 0.37, 4.62))
    extrude(allprofs(sk11), CUT, '10.2 mm', '1.8 mm')
    sk12 = mv.sketches.add(mv.xZConstructionPlane)
    sk12.sketchCurves.sketchCircles.addByCenterRadius(mptXZ(sk12, 0.0, 3.0), 0.3)
    extrude(allprofs(sk12), CUT, '10.2 mm', '6.0 mm')

    b = mv.bRepBodies.item(0)
    print('bodies:', mv.bRepBodies.count, 'vol mm3:', round(b.volume * 1000), 'valid:', b.isValid)
