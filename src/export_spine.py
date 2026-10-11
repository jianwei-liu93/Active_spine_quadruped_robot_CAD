"""Export the source-reconciled spine through the FreeCAD assembly exporter."""
from pathlib import Path
import Import,Part,json

def run(doc,root):
    root=Path(root);out=root/'exports/step/r02';out.mkdir(parents=True,exist_ok=True)
    instances=[o for o in doc.Objects if o.TypeId=='App::Link']
    # Part.export silently drops App::Link assemblies in this FreeCAD build.
    Import.export(instances,str(out/'flexor_r02_spine.step'))
    for side,label in [('LumbarIntegrated1','left'),('LumbarIntegrated_1','right')]:
        Part.export([doc.getObject(side).LinkedObject],str(out/f'lumbar_frame_{label}_r02.step'))
    shape=Part.read(str(out/'flexor_r02_spine.step'));expected=sum(o.Shape.Volume for o in instances)
    error=None if shape.isNull() else abs(shape.Volume-expected)/expected
    result={'status':'PASS' if not shape.isNull() and shape.isValid() and len(shape.Solids)==len(instances) and error<1e-6 else 'FAIL',
            'step_solids':len(shape.Solids),'expected_instances':len(instances),'volume_relative_error':error,
            'scope':'corrected spine only; provisional manufacturing interfaces'}
    (root/'reports/verification/r02_step_export.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result);return result
