"""robotarm/wrist_yoke — Fusion MCP generating script (clip-over, powered roll).

Rebuilds the `robotarm_wrist_yoke` component from scratch (idempotent:
deletes any existing occurrence of that name first). Every dimension is a
Fusion user parameter (wr_* / sv_*); edit those in the UI, re-run, done.

The yoke CLIPS OVER the printed arm shell from outside: left ear screws
flat onto the wrist SG90's horn (4 × M2 on a Ø14 circle, Ø9 hub bore),
right ear takes an M8 bolt running in the 608ZZ in the far wall.

Roll joint is a TOP CRADLE (kit style): an open box on the bridge's front
face holds the roll SG90 shaft-up on the arm centreline, tabs screwed to
the end wall tops, lead notches in both side walls. The gripper bolts to
the horn above. Arm below, servo in the middle, gripper on top.

Frame: pitch axis = X through the origin; +Z = forward.
Spec: specs/robotarm/wrist_yoke.md — ASSUMED there: 608ZZ, horn standoff
4.0, ear end radius 18.0, axis-to-front-face 22.0.

2026-08-25 rework (knowledge/fusion_modeling_craft.md): the cradle
geometry used hand-derived centimetre literals, so sv_case_l / sv_case_w /
sv_shaft_off / wr_cradle_wall were declared but dead — editing them moved
nothing. Every sketch coordinate now derives from a parameter, the pocket
and block bounds are named derived parameters, and bodies / sketches /
features / timeline groups are named. wr_cradle_endwall was removed: the
cradle block spans the full ear width, so it never controlled a wall.
Geometry is otherwise unchanged (hand-rounding of the pocket ends at
0.005 mm/side is now exact).

NOTE (Fusion API quirk observed): sketches on yZConstructionPlane map
sketch (u, v) -> model (-Z, Y); sketches on xYConstructionPlane extrude +Z.
"""

import adsk.core
import adsk.fusion

COMPONENT = 'robotarm_wrist_yoke'
BODY_NAME = 'wrist_yoke'
MATERIAL_NAME = 'PET Plastic'   # PETG per the spec's print plan


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    ups = design.userParameters
    V = adsk.core.ValueInput.createByString
    P3 = adsk.core.Point3D.create

    # ---- parameters: every dimension, with provenance -------------------
    def param(name, expr, comment=''):
        p = ups.itemByName(name)
        if p is None:
            ups.add(name, V(expr), 'mm', comment)
        else:
            p.expression = expr
            p.comment = comment

    def val(name):
        return ups.itemByName(name).value        # internal units: cm

    # interfaces
    param('wr_gap', '35.0 mm', 'shell OUTER width across flats - USER')
    param('wr_slide', '0.25 mm', 'sliding fit - design_rules')
    param('wr_horn_standoff', '4.0 mm', 'ASSUMED shell outer face to horn underside (servo boss)')
    param('wr_horn_t', '1.6 mm', 'SG90 horn thickness - DATASHEET')
    param('wr_hub_bore_d', '9.0 mm', 'clears horn hub + screw head')
    param('wr_screw_bcd', '14.0 mm', 'M2 screws into horn arm holes')
    param('wr_screw_d', '2.2 mm', 'M2 through-hole - design_rules FASTENER_MM')
    param('wr_bolt_hole_d', '8.2 mm', 'M8 bolt clearance - bolt rides the 608 bore')
    # structure
    param('wr_end_r', '18.0 mm', 'ASSUMED ear end radius about pivot')
    param('wr_axis_face', '22.0 mm', 'ASSUMED pivot axis to yoke front face (must clear shell end)')
    param('wr_plate_t', '4.0 mm', 'ear thickness')
    param('wr_front_t', '6.0 mm', 'bridge thickness')
    param('wr_halfh', '15.0 mm', 'ear half-height at the front')
    param('wr_bridge_halfh', '15.0 mm', 'bridge half-height')
    # roll servo (SG90)
    param('sv_case_l', '22.8 mm', 'SG90 case length - DATASHEET')
    param('sv_case_w', '12.2 mm', 'SG90 case width - DATASHEET')
    param('sv_below_flange', '15.9 mm', 'case below mounting tabs - DATASHEET')
    param('sv_shaft_off', '5.5 mm', 'case centre is +5.5 from shaft along L - DATASHEET')
    param('sv_tab_spacing', '27.8 mm', 'SG90 mounting tab hole spacing - DATASHEET')
    param('sv_pilot_d', '1.8 mm', 'pilot for supplied self-tapper')
    param('wr_cradle_wall', '2.4 mm', 'cradle side wall - design_rules boss wall')
    param('wr_tab_pilot_depth', '6.0 mm', 'pilot depth into the end wall tops')
    # lead notches
    param('wr_notch_x0', '2.0 mm', 'notch start, from the shaft along +X')
    param('wr_notch_len', '7.0 mm', 'notch length along X')
    param('wr_notch_h', '9.0 mm', 'notch height up from the cradle floor')
    param('wr_notch_y_in', '6.0 mm', 'notch inner edge - bites through the pocket wall')
    param('wr_notch_break', '0.2 mm', 'notch outer edge past the block face - clean break-through')
    # derived: ear planes and cradle bounds (edit the sources, not these)
    param('wr_x_left', '-(wr_gap/2 + wr_horn_standoff + wr_horn_t)',
          'left ear INNER face = horn top plane')
    param('wr_x_right', 'wr_gap/2 + wr_slide', 'right ear INNER face')
    param('wr_block_x0', 'wr_x_left - wr_plate_t', 'cradle block / left ear outer face')
    param('wr_block_x1', 'wr_x_right + wr_plate_t', 'cradle block / right ear outer face')
    param('wr_pocket_x0', 'sv_shaft_off - sv_case_l/2 - wr_slide/2', 'servo pocket, -X end')
    param('wr_pocket_x1', 'sv_shaft_off + sv_case_l/2 + wr_slide/2', 'servo pocket, +X end')
    param('wr_pocket_y', 'sv_case_w/2 + wr_slide/2', 'servo pocket half-width')
    param('wr_cradle_y', 'sv_case_w/2 + wr_slide/2 + wr_cradle_wall', 'cradle block half-width')

    dead = [p for p in ('wr_cradle_endwall',) if ups.itemByName(p)]
    for name in dead:
        ups.itemByName(name).deleteMe()          # never controlled a wall

    # ---- idempotent rebuild ---------------------------------------------
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

    # ---- helpers ---------------------------------------------------------
    def sketch(plane, name):
        sk = comp.sketches.add(plane)
        sk.name = name
        return sk

    def profiles(sk, expected=None):
        """All profiles, with the count asserted where it is predictable."""
        if expected is not None:
            assert sk.profiles.count == expected, (
                f'{sk.name}: expected {expected} profile(s), got {sk.profiles.count}')
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            c.add(sk.profiles.item(i))
        return c

    def rings(sk):
        """Only closed-ring profiles (outer loop + inner loop) — the walls."""
        c = adsk.core.ObjectCollection.create()
        for i in range(sk.profiles.count):
            if sk.profiles.item(i).profileLoops.count == 2:
                c.add(sk.profiles.item(i))
        assert c.count == 1, f'{sk.name}: expected 1 ring profile, got {c.count}'
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

    def mpt(sk, x, y):          # model coords (cm) -> sketch space
        return sk.modelToSketchSpace(P3(x, y, 0))

    # ---- phase 1: ears + bridge ------------------------------------------
    t0 = design.timeline.count

    sk_ears = sketch(comp.yZConstructionPlane, 'sk_ears')
    sk_ears.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0, 0), val('wr_end_r'))
    sk_ears.sketchCurves.sketchLines.addTwoPointRectangle(
        P3(-val('wr_axis_face'), -val('wr_halfh'), 0),
        P3(0, val('wr_halfh'), 0))
    # circle and rectangle overlap, so Fusion splits them into regions;
    # every region is wanted (their union is the ear outline)
    extrude(profiles(sk_ears), NEW, 'wr_block_x0', 'wr_plate_t', 'ear_left')
    extrude(profiles(sk_ears), JOIN, 'wr_x_right', 'wr_plate_t', 'ear_right')

    sk_bridge = sketch(comp.yZConstructionPlane, 'sk_bridge')
    sk_bridge.sketchCurves.sketchLines.addTwoPointRectangle(
        P3(-val('wr_axis_face'), -val('wr_bridge_halfh'), 0),
        P3(-(val('wr_axis_face') - val('wr_front_t')), val('wr_bridge_halfh'), 0))
    # taller than the ears so the cradle block lands on a solid face
    extrude(profiles(sk_bridge, expected=1), JOIN,
            'wr_block_x0', 'wr_block_x1 - wr_block_x0', 'bridge')

    group(t0, 'ears + bridge')

    # ---- phase 2: wrist interface (horn side, bearing side) --------------
    t1 = design.timeline.count

    sk_horn = sketch(comp.yZConstructionPlane, 'sk_horn_interface')
    sk_horn.sketchCurves.sketchCircles.addByCenterRadius(
        P3(0, 0, 0), val('wr_hub_bore_d') / 2)
    r = val('wr_screw_bcd') / 2
    for u, v in ((r, 0), (-r, 0), (0, r), (0, -r)):
        sk_horn.sketchCurves.sketchCircles.addByCenterRadius(
            P3(u, v, 0), val('wr_screw_d') / 2)
    extrude(profiles(sk_horn, expected=5), CUT,
            'wr_block_x0', 'wr_plate_t', 'horn_interface_cut')

    # bearing side: plain Ø8.2 through-hole — an M8 bolt + washers replaces
    # a printed stub (kills the worst overhang, and the yoke drops together:
    # no interference to flex over, bolt goes in last from outside)
    sk_bore = sketch(comp.yZConstructionPlane, 'sk_bearing_bore')
    sk_bore.sketchCurves.sketchCircles.addByCenterRadius(
        P3(0, 0, 0), val('wr_bolt_hole_d') / 2)
    extrude(profiles(sk_bore, expected=1), CUT,
            'wr_x_right', 'wr_plate_t', 'bearing_bore_cut')

    group(t1, 'wrist interface')

    # ---- phase 3: roll cradle --------------------------------------------
    t2 = design.timeline.count

    # full-width block (flush with the ears) with the servo pocket inside
    sk_cradle = sketch(comp.xYConstructionPlane, 'sk_cradle')
    sk_cradle.sketchCurves.sketchLines.addTwoPointRectangle(
        mpt(sk_cradle, val('wr_block_x0'), -val('wr_cradle_y')),
        mpt(sk_cradle, val('wr_block_x1'), val('wr_cradle_y')))
    sk_cradle.sketchCurves.sketchLines.addTwoPointRectangle(
        mpt(sk_cradle, val('wr_pocket_x0'), -val('wr_pocket_y')),
        mpt(sk_cradle, val('wr_pocket_x1'), val('wr_pocket_y')))
    extrude(rings(sk_cradle), JOIN,
            'wr_axis_face', 'sv_below_flange', 'cradle_walls')

    sk_tabs = sketch(comp.xYConstructionPlane, 'sk_tab_pilots')
    for sign in (-1, 1):
        sk_tabs.sketchCurves.sketchCircles.addByCenterRadius(
            mpt(sk_tabs, val('sv_shaft_off') + sign * val('sv_tab_spacing') / 2, 0),
            val('sv_pilot_d') / 2)
    extrude(profiles(sk_tabs, expected=2), CUT,
            'wr_axis_face + sv_below_flange - wr_tab_pilot_depth',
            'wr_tab_pilot_depth', 'tab_pilot_cut')

    # lead notches, both side walls, up from the cradle floor: the servo
    # lead threads out sideways with slack instead of over the pocket rim
    sk_notch = sketch(comp.xYConstructionPlane, 'sk_lead_notches')
    x0, x1 = val('wr_notch_x0'), val('wr_notch_x0') + val('wr_notch_len')
    y_in, y_out = val('wr_notch_y_in'), val('wr_cradle_y') + val('wr_notch_break')
    for sign in (1, -1):
        sk_notch.sketchCurves.sketchLines.addTwoPointRectangle(
            mpt(sk_notch, x0, sign * y_in), mpt(sk_notch, x1, sign * y_out))
    extrude(profiles(sk_notch, expected=2), CUT,
            'wr_axis_face', 'wr_notch_h', 'lead_notch_cut')

    group(t2, 'roll cradle')

    # ---- identity: body name + material ----------------------------------
    assert comp.bRepBodies.count == 1, f'expected 1 body, got {comp.bRepBodies.count}'
    body = comp.bRepBodies.item(0)
    body.name = BODY_NAME
    for i in range(app.materialLibraries.count):
        m = app.materialLibraries.item(i).materials.itemByName(MATERIAL_NAME)
        if m:
            body.material = m
            break

    # ---- diagnostics -----------------------------------------------------
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
          f' | user params: {ups.count} | removed dead params: {dead or "none"}')
    print(f'timeline groups: {groups}')
