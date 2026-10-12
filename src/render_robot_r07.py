"""Source-facing real CAD captures; lead-only GUI, no geometry/native save.

Opposite-Y oblique views expose both sagittal cheeks and perpendicular
crosswalls. Source comparison anchors: Movie S1 51.5 s and 52.7 s; captures
remain CAD evidence requiring the lead's visual comparison with those frames.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def render(doc, root=None, revision='r07'):
    """Capture actual links, including both bare-lumbar faces, then restore UI.

    Output: reports/views/<revision>_*.png and capture manifest. Neither camera
    choice establishes source fidelity; inspect both faces and real geometry.
    """
    import FreeCAD as App
    import FreeCADGui as Gui
    from pivy import coin
    revision = str(revision)
    if not re.fullmatch(r'r[0-9]+', revision):
        raise ValueError('Revision must be r followed by digits')
    root = Path(root).resolve() if root is not None else ROOT
    out = root/'reports/views'
    out.mkdir(parents=True, exist_ok=True)
    App.setActiveDocument(doc.Name)
    view = Gui.activeDocument().activeView()
    camera = view.getCamera()
    instances = [o for o in doc.Objects if o.TypeId == 'App::Link']
    visibility = [(o, o.Visibility) for o in doc.Objects if hasattr(o, 'Visibility')]
    records = []

    def capture(suffix, predicate, front=False, y_side=1, normal_xyz=None):
        box = App.BoundBox()
        selected = []
        for obj in instances:
            obj.Visibility = bool(predicate(obj)) and not getattr(obj, 'NonphysicalClearance', False)
            if obj.Visibility:
                box.add(obj.Shape.BoundBox)
                selected.append(obj.Name)
        if not selected:
            raise ValueError('No actual links selected for '+suffix)
        if front:
            view.viewFront()
            normal = None
        else:
            normal = App.Vector(*(normal_xyz or (-.3, y_side, .22)))
            normal.normalize()
            right = App.Vector(0, 0, 1).cross(normal)
            right.normalize()
            up = normal.cross(right)
            rotation = App.Rotation(right, up, normal, 'ZXY')
            view.getCameraNode().orientation.setValue(coin.SbRotation(*rotation.Q))
        Gui.updateGui()
        rotation = view.getCameraOrientation()
        node = view.getCameraNode()
        node.position.setValue(*tuple(box.Center+rotation.multVec(App.Vector(0, 0, 300))))
        node.nearDistance.setValue(1)
        node.farDistance.setValue(1000)
        node.focalDistance.setValue(300)
        # Fit the actual projected bounding-box corners at the output aspect.
        right = rotation.multVec(App.Vector(1, 0, 0))
        up = rotation.multVec(App.Vector(0, 1, 0))
        corners = [App.Vector(x, y, z)-box.Center
                   for x in (box.XMin, box.XMax) for y in (box.YMin, box.YMax)
                   for z in (box.ZMin, box.ZMax)]
        width = max(p.dot(right) for p in corners)-min(p.dot(right) for p in corners)
        height = max(p.dot(up) for p in corners)-min(p.dot(up) for p in corners)
        node.height.setValue(max(height, width/(1600/1100), 1)*1.2)
        path = out/(revision+'_'+suffix+'.png')
        view.saveImage(str(path), 1600, 1100, 'White')
        if not path.exists() or not path.stat().st_size:
            raise IOError('Missing CAD capture '+str(path))
        records.append({'path':str(path.relative_to(root)), 'links':selected,
                        'view':'front' if front else 'oblique',
                        'normal_xyz':list(normal) if normal is not None else None,
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

    try:
        for obj in doc.PartsLibrary.Group:
            obj.Visibility = False
        doc.PartsLibrary.Visibility = False
        for obj in doc.Objects:
            if getattr(obj, 'NonphysicalClearance', False):
                obj.Visibility = False
        lumbar = lambda o: o.Name.startswith('LumbarIntegrated')
        capture('bare_lumbar', lumbar)
        capture('bare_lumbar_pos_y_oblique', lumbar, y_side=1)
        capture('bare_lumbar_neg_y_oblique', lumbar, y_side=-1)
        capture('bare_lumbar_crosswall_neg_x',lumbar,normal_xyz=(-1,.55,.35))
        capture('bare_lumbar_crosswall_pos_x',lumbar,normal_xyz=(1,.55,.35))
        capture('lumbar_motors_crosswall',lambda o:o.Name.startswith(('LumbarIntegrated','SpineMotor','GuideLiner','FixedLumbarTie')),normal_xyz=(-1,.55,.35))
        capture('spine_source_facing', lambda o: o.Name.startswith(
            ('LumbarIntegrated', 'Torso_', 'Link', 'SyncB', 'Through', 'DirectCrank', 'HornAdapter'))
            or getattr(o.LinkedObject, 'MaterialName', '') == 'copper' or 'Capture' in o.Name)
        capture('robot_side', lambda o: True, front=True)
        capture('robot_assembled', lambda o: True)
    finally:
        for obj, value in visibility:
            obj.Visibility = value
        view.setCamera(camera)
        Gui.updateGui()
    report = {'revision':revision, 'status':'PASS_CAPTURED_RESTORED', 'captures':records,
              'source_comparison_anchors':'Movie S1 51.5 s and 52.7 s',
              'visual_review':'NOT_RUN - inspect both Y views for solid upper sagittal cheeks and broad windowed perpendicular crosswalls',
              'saved_document':False}
    (out/(revision+'_capture_manifest.json')).write_text(json.dumps(report, indent=2)+'\n')
    return report
