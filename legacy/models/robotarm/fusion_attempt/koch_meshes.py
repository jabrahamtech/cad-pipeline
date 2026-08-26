"""robotarm/koch_meshes — driver script for the imported Koch concept meshes.

Part roles (per Jonathan, 2026-08-24 — supersedes my earlier guess):
- part_object_id_6 (WHITE) = the WRIST: slides INTO the printed arm shell's
  35 mm slot; two 4-hole pads 32.5 mm apart pierce its prongs — pad A is
  the pitch pivot (horn one side, bearing the other), pad B is where the
  gripper bolts on.
- part_object_id_3 (GREEN) = gripper body, mounts to the wrist at pad B;
  servo window ~12.3 wide (SG90-compatible as-is); four Ø5 base mounts;
  Ø3.1 hinge hole pair top-rear on both walls.
- part_object_id_4 (PINK) = the clamping jaw, hinged on green's Ø3.1 pair;
  its lug holes are Ø2.4 at local (−17.76, ·, −2.63), lug gap 26.2.

Scales applied (about each component origin):
- WHITE: uniform ×1.568 → 34.5 across, sliding fit in the 35 slot.
- PINK: local-Y ×1.137 net → lug gap 26.2 → 29.8, straddles green's 29.5
  outer walls. (History: an erroneous ×1.559 was applied first, then
  ×0.7293 to net 1.137 — a fresh doc needs only ×1.137.)
- GREEN: unscaled.

World transforms (row-major 4×4, cm; occurrence.transform2 IS the world
transform — set directly, don't compose with parents, the import
transforms are slightly denormalized and composition gets rejected):
- WHITE: [0,1,0,0, 0,0,-1,0.855, -1,0,0,2.266, 0,0,0,1]
    pad-A axis = wrist pitch axis (model X through origin); pad B forward.
- GREEN: [0,0,1,0, 1,0,0,0, 0,1,0,8.02, 0,0,0,1]
    base mounts land at pad B (z ≈ 50.9); long axis forward +Z.
- PINK:  [0,0,1,1.703, 0,1,0,0, -1,0,0,3.284, 0,0,0,1]
    lug holes on green's hinge axis (model Y at x 14.4, z 50.6).

Still to do once the arrangement is approved: mesh→BRep conversion, then
re-drill pad A (M2 horn pattern one side, Ø8.2 for the M8/bearing on the
other), SG90 fit-check of green's window, hinge hardware (M3), clearance
sweep of pink about the hinge, export.
"""

import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    def find(name):
        def walk(occs):
            for occ in occs:
                if occ.name.startswith(name):
                    return occ
                r = walk(occ.childOccurrences)
                if r:
                    return r
            return None
        return walk(root.occurrences)

    def scale_uniform(occ, s):
        body = occ.component.meshBodies.item(0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        sf = occ.component.features.scaleFeatures
        inp = sf.createInput(coll, occ.component.originConstructionPoint,
                             adsk.core.ValueInput.createByReal(s))
        sf.add(inp)

    def scale_y(occ, sy):
        body = occ.component.meshBodies.item(0)
        coll = adsk.core.ObjectCollection.create()
        coll.add(body)
        sf = occ.component.features.scaleFeatures
        inp = sf.createInput(coll, occ.component.originConstructionPoint,
                             adsk.core.ValueInput.createByReal(1.0))
        inp.setToNonUniform(adsk.core.ValueInput.createByReal(1.0),
                            adsk.core.ValueInput.createByReal(sy),
                            adsk.core.ValueInput.createByReal(1.0))
        sf.add(inp)

    def set_world(occ, rows):
        W = adsk.core.Matrix3D.create()
        W.setWithArray(rows)
        occ.transform2 = W

    for occ in root.occurrences:
        if occ.component.name in ('robotarm_wrist_yoke', 'robotarm_gripper_base', 'robotarm_jaw_moving'):
            occ.isLightBulbOn = False

    wh, gr, pk = find('part_object_id_6'), find('part_object_id_3'), find('part_object_id_4')

    def yspan(occ):
        dm = occ.component.meshBodies.item(0).displayMesh
        ys = dm.nodeCoordinatesAsDouble[1::3]
        return (max(ys) - min(ys)) * 10

    if yspan(wh) < 30.0:
        scale_uniform(wh, 1.568)
    if yspan(pk) < 39.0:
        scale_y(pk, 1.137)

    set_world(wh, [0, 1, 0, 0, 0, 0, -1, 0.855, -1, 0, 0, 2.266, 0, 0, 0, 1])
    set_world(gr, [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 8.02, 0, 0, 0, 1])
    set_world(pk, [0, 0, 1, 1.703, 0, 1, 0, 0, -1, 0, 0, 3.284, 0, 0, 0, 1])
    print('Koch meshes: white=wrist, green=gripper body, pink=clamp — scaled and placed')
