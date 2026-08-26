"""robotarm/_preview - save viewport images to docs/ (helper, not a part).

Named view directions rather than whatever the camera happened to be on, so
the images are reproducible. Run AFTER _check_fit.py has placed the pieces.
"""

import math
import os

import adsk.core
import adsk.fusion

OUT = os.path.expanduser('~/Documents/GitHub/cad-pipeline/docs/robotarm')
W, H = 1600, 1100

# name -> (eye direction from target, up vector)
VIEWS = {
    'gripper_iso': ((1.0, -1.0, 0.7), (0.0, 0.0, 1.0)),
    'gripper_front': ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    'gripper_top': ((0.0, -0.001, 1.0), (0.0, 1.0, 0.0)),
}


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    vp = app.activeViewport
    # PET Plastic renders translucent, which turns a five-piece assembly into
    # a wireframe soup. Shaded-with-edges is what makes the picture readable.
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    os.makedirs(OUT, exist_ok=True)

    bb = design.rootComponent.boundingBox
    cx = (bb.minPoint.x + bb.maxPoint.x) / 2
    cy = (bb.minPoint.y + bb.maxPoint.y) / 2
    cz = (bb.minPoint.z + bb.maxPoint.z) / 2
    span = max(bb.maxPoint.x - bb.minPoint.x,
               bb.maxPoint.y - bb.minPoint.y,
               bb.maxPoint.z - bb.minPoint.z)
    dist = span * 4

    written = []
    for name, (d, up) in VIEWS.items():
        norm = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        cam = vp.camera
        cam.target = adsk.core.Point3D.create(cx, cy, cz)
        cam.eye = adsk.core.Point3D.create(
            cx + d[0] / norm * dist, cy + d[1] / norm * dist, cz + d[2] / norm * dist)
        cam.upVector = adsk.core.Vector3D.create(up[0], up[1], up[2])
        cam.isFitView = True
        vp.camera = cam
        vp.fit()                 # isFitView alone does not frame a set eye/target
        vp.refresh()
        path = os.path.join(OUT, name + '.png')
        ok = vp.saveAsImageFile(path, W, H)
        written.append((name, ok, os.path.getsize(path) if os.path.exists(path) else 0))

    for name, ok, size in written:
        print('%-16s saved=%s bytes=%d' % (name, ok, size))
