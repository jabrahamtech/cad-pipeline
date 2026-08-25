"""robotarm/wrist_yoke — Fusion MCP generating script (clip-over, powered roll).

Rebuilds the `robotarm_wrist_yoke` component from scratch (idempotent:
deletes any existing occurrence of that name first). All dimensions are
Fusion user parameters (wr_*); edit those, re-run, done.

The yoke CLIPS OVER the printed arm shell from outside: left ear screws
flat onto the wrist SG90's horn (4 x M2 on a Ø14 circle, Ø9 hub bore),
right ear reaches a Ø7.9 stub inward into the 608ZZ in the far wall.

Roll joint is a TOP CRADLE (kit style): an open box on the bridge's front
face holds the roll SG90 shaft-up on the arm centreline, tabs screwed to
the end wall tops, lead notches in both side walls. The gripper bolts to
the horn above. Arm below, servo in the middle, gripper on top.

Frame: pitch axis = X through the origin; +Z = forward.
Spec: specs/robotarm/wrist_yoke.md — ASSUMED there: 608ZZ, horn standoff
4.0, ear end radius 18.0, axis-to-front-face 22.0.

NOTE (Fusion API quirk observed): sketches on yZConstructionPlane map
sketch (u, v) -> model (-Z, Y); sketches on xYConstructionPlane extrude +Z.
"""

import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString

    def param(name, expr, comment=''):
        p = ups.itemByName(name)
        if p is None:
            ups.add(name, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    param('wr_gap', '35.0 mm', 'shell OUTER width across flats - USER')
    param('wr_slide', '0.25 mm', 'sliding fit - design_rules')
    param('wr_horn_standoff', '4.0 mm', 'ASSUMED shell outer face to horn underside (servo boss)')
    param('wr_horn_t', '1.6 mm', 'SG90 horn thickness - DATASHEET')
    param('wr_hub_bore_d', '9.0 mm', 'clears horn hub + screw head')
    param('wr_screw_bcd', '14.0 mm', 'M2 screws into horn arm holes')
    param('wr_screw_d', '2.2 mm', 'M2 through-hole')
    param('wr_bolt_hole_d', '8.2 mm', 'M8 bolt clearance - bolt rides the 608 bore')
    param('wr_end_r', '18.0 mm', 'ASSUMED ear end radius about pivot')
    param('wr_axis_face', '22.0 mm', 'ASSUMED pivot axis to yoke front face (must clear shell end)')
    param('wr_plate_t', '4.0 mm', 'ear thickness')
    param('wr_front_t', '6.0 mm', 'bridge thickness')
    param('wr_halfh', '15.0 mm', 'ear half-height at the front')
    param('wr_x_left', '-(wr_gap/2 + wr_horn_standoff + wr_horn_t)',
          'left ear INNER face = horn top plane')
    param('wr_x_right', 'wr_gap/2 + wr_slide', 'right ear INNER face')
    param('wr_bridge_halfh', '15.0 mm', 'bridge half-height')
    param('sv_case_l', '22.8 mm', 'SG90 case length')
    param('sv_case_w', '12.2 mm', 'SG90 case width')
    param('sv_below_flange', '15.9 mm', 'case below mounting tabs')
    param('sv_shaft_off', '5.5 mm', 'case centre is +5.5 from shaft along L')
    param('sv_pilot_d', '1.8 mm', 'pilot for supplied self-tapper')
    param('wr_cradle_wall', '2.4 mm', 'cradle side wall')
    param('wr_cradle_endwall', '4.0 mm', 'cradle end wall (tab screws land here)')

    def val(name):
        return ups.itemByName(name).value  # internal units (cm)

    for occ in list(root.occurrences):
        if occ.component.name == 'robotarm_wrist_yoke':
            occ.deleteMe()
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = 'robotarm_wrist_yoke'
    ext = comp.features.extrudeFeatures
    P3 = adsk.core.Point3D.create

    def allprofs(sk):
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def extrude(profs, op, start_expr, dist_expr):
        inp = ext.createInput(profs, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V(start_expr))
        inp.setDistanceExtent(False, V(dist_expr))
        return ext.add(inp)

    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    # ears: rounded about the pivot axis, front edge at +Z
    sk = comp.sketches.add(comp.yZConstructionPlane)
    sk.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0), val('wr_end_r'))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        P3(-val('wr_axis_face'), -val('wr_halfh'), 0),
        P3(0, val('wr_halfh'), 0))
    extrude(allprofs(sk), NEW, 'wr_x_left - wr_plate_t', 'wr_plate_t')
    extrude(allprofs(sk), JOIN, 'wr_x_right', 'wr_plate_t')

    # bridge - taller than the ears so the boss ring lands on solid face
    sk2 = comp.sketches.add(comp.yZConstructionPlane)
    sk2.sketchCurves.sketchLines.addTwoPointRectangle(
        P3(-val('wr_axis_face'), -val('wr_bridge_halfh'), 0),
        P3(-(val('wr_axis_face') - val('wr_front_t')), val('wr_bridge_halfh'), 0))
    extrude(allprofs(sk2), JOIN, 'wr_x_left - wr_plate_t',
            'wr_x_right + wr_plate_t - (wr_x_left - wr_plate_t)')

    # left ear: hub clearance bore + 4x M2 on the bolt circle
    sk3 = comp.sketches.add(comp.yZConstructionPlane)
    sk3.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0), val('wr_hub_bore_d') / 2)
    r = val('wr_screw_bcd') / 2
    for u, v in ((r, 0), (-r, 0), (0, r), (0, -r)):
        sk3.sketchCurves.sketchCircles.addByCenterRadius(P3(u, v, 0), val('wr_screw_d') / 2)
    extrude(allprofs(sk3), CUT, 'wr_x_left - wr_plate_t', 'wr_plate_t')

    # bearing side: plain Ø8.2 through-hole — M8 bolt + washer replaces the
    # printed stub (kills the worst overhang, and the yoke drops together:
    # no interference to flex over, bolt goes in last from outside)
    sk5 = comp.sketches.add(comp.yZConstructionPlane)
    sk5.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0), val('wr_bolt_hole_d') / 2)
    extrude(allprofs(sk5), CUT, 'wr_x_right', 'wr_plate_t')

    # roll-servo cradle on the bridge top: shaft axis = arm centreline (+Z)
    # model coords in cm: case pocket X -0.603..1.703, Y +/-0.6225; walls outside
    def rings(sk_):
        c = adsk.core.ObjectCollection.create()
        for i in range(sk_.profiles.count):
            if sk_.profiles.item(i).profileLoops.count == 2:
                c.add(sk_.profiles.item(i))
        return c

    # FULL-WIDTH cradle block (flush with the ears — Jonathan preferred the look);
    # pocket unchanged, so the fit checks still hold
    sk7 = comp.sketches.add(comp.xYConstructionPlane)

    def mpt(sk_, x, y):
        return sk_.modelToSketchSpace(P3(x, y, 0))

    sk7.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk7, -2.71, -0.8625), mpt(sk7, 2.175, 0.8625))
    sk7.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk7, -0.603, -0.6225), mpt(sk7, 1.703, 0.6225))
    extrude(rings(sk7), JOIN, 'wr_axis_face', 'sv_below_flange')

    # tab screw pilots in the end wall tops (holes at -8.4 / +19.4 from shaft)
    sk8 = comp.sketches.add(comp.xYConstructionPlane)
    sk8.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk8, -0.84, 0), val('sv_pilot_d') / 2)
    sk8.sketchCurves.sketchCircles.addByCenterRadius(mpt(sk8, 1.94, 0), val('sv_pilot_d') / 2)
    extrude(allprofs(sk8), CUT, 'wr_axis_face + sv_below_flange - 6.0 mm', '6.0 mm')

    # lead notches, both side walls, 9 up from the cradle floor (room for the
    # servo lead to thread out sideways with slack)
    sk9 = comp.sketches.add(comp.xYConstructionPlane)
    sk9.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk9, 0.2, 0.6), mpt(sk9, 0.9, 0.88))
    sk9.sketchCurves.sketchLines.addTwoPointRectangle(mpt(sk9, 0.2, -0.88), mpt(sk9, 0.9, -0.6))
    extrude(allprofs(sk9), CUT, 'wr_axis_face', '9.0 mm')

    body = comp.bRepBodies.item(0)
    bb = body.boundingBox
    print('bodies:', comp.bRepBodies.count)
    print(f'bbox mm: X {bb.minPoint.x*10:.2f}..{bb.maxPoint.x*10:.2f}'
          f'  Y {bb.minPoint.y*10:.2f}..{bb.maxPoint.y*10:.2f}'
          f'  Z {bb.minPoint.z*10:.2f}..{bb.maxPoint.z*10:.2f}')
    print(f'volume: {body.volume*1000:.0f} mm3, valid: {body.isValid}')
