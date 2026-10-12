"""Lead-GUI final drawing presentation/save; never changes part geometry."""
import hashlib
import json
from pathlib import Path

SHA = 'd90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9'


def run(doc, root):
    root = Path(root).resolve()
    digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    native = root/'cad/flexor_r10_robot.FCStd'
    if digest(native) != SHA:
        raise RuntimeError('Canonical source changed')
    path = root/'drawings/r10/drawing_manifest_r10.json'
    manifest = json.loads(path.read_text())
    if manifest['sheet_count'] != 77 or manifest['dimension_count'] != 321:
        raise RuntimeError('Unexpected drawing inventory')
    geometry = {o.Name:(o.Shape.Volume,tuple(o.Shape.BoundBox.__getattribute__(k)
                for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')))
                for o in doc.Objects if o.TypeId == 'PartDesign::Body'}
    measured = {}
    for row in manifest['sheets']:
        if row.get('layout',{}).get('status') != 'PASS_NATIVE_REFS_VALUES_UNCHANGED':
            raise RuntimeError('Apply GUI layout to every sheet first')
        for rec in row['dimensions']:
            dim = doc.getObject(rec['object'])
            measured[dim.Name]=(repr(dim.References2D),repr(dim.References3D),float(dim.getRawValue()))
            if dim.Arbitrary or abs(float(dim.getRawValue())-rec['expected_mm'])>1e-6:
                raise RuntimeError('Native dimension changed')
    template = root/'drawings/r10/templates/A4_r10_editable.svg'
    text = template.read_text()
    if '| r07 |' not in text and '| r10 |' not in text:
        raise RuntimeError('Unexpected template revision text')
    template.write_text(text.replace('| r07 |','| r10 |'))
    for row in manifest['sheets']:
        page = doc.getObject(row['page'])
        fields = dict(page.Template.EditableTexts)
        fields['Sheet'] = 'SHEET %03d / %03d' % (row['sheet'],len(manifest['sheets']))
        fields['Title'] = row['part_number']
        # Reload the actual external SVG, then restore its editable content.
        page.Template.Template = ''
        page.Template.Template = str(template)
        page.Template.EditableTexts = fields
        row['export_layout_status']='STALE_AFTER_TEMPLATE_REVISION'
    doc.recompute()
    for name,(refs2,refs3,value) in measured.items():
        dim = doc.getObject(name)
        if (repr(dim.References2D),repr(dim.References3D)) != (refs2,refs3) or abs(float(dim.getRawValue())-value)>1e-6 or dim.Arbitrary:
            raise RuntimeError('Presentation changed native measurement')
    for name,(volume,bounds) in geometry.items():
        shape = doc.getObject(name).Shape
        actual = tuple(getattr(shape.BoundBox,k) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
        if abs(shape.Volume-volume)>1e-7 or max(abs(a-b) for a,b in zip(actual,bounds))>1e-7:
            raise RuntimeError('Presentation changed source geometry')
    target = root/'cad/flexor_r10_drawings.FCStd'
    doc.saveAs(str(target))
    manifest.update(native_companion=str(target),native_companion_sha256=digest(target),
                    source_sha256=SHA,native_sha256=SHA,
                    pdf_exports='PARTIAL_OR_STALE',visual_review='NOT_RUN',
                    template_sha256=digest(template),presentation_source_geometry_unchanged=True)
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    if digest(native)!=SHA:
        raise RuntimeError('Canonical source bytes changed')
    return {'saved_companion':str(target),'sha256':digest(target),'sheets':77,'dimensions':321}
