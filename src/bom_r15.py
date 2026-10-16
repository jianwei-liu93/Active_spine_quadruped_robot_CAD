"""Source-definition quantities and stable physical IDs from verified AX0/AX1."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'animation/motion/ax01_r15.json';data=json.loads(path.read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert data['source']['cad_sha256']==sha(ROOT/'cad/flexor_r15_robot.FCStd')
rows=data['instances'];assert len(rows)==455 and len({r['instance_id'] for r in rows})==455
counts=Counter((r['source_object_name'],r['part_number']) for r in rows)
assert len(counts)==108 and sum(counts.values())==455
assert counts[('FRM_LUMBAR_COMPACT_CAGE_r12','FRM_LUMBAR_COMPACT_CAGE_r15')]==1
folder=ROOT/'bom';folder.mkdir(exist_ok=True)
with (folder/'bom_r15.csv').open('w',newline='') as f:
    writer=csv.writer(f,lineterminator='\n');writer.writerow(['source_object','part_number','quantity'])
    writer.writerows((source,number,n) for (source,number),n in sorted(counts.items()))
with (folder/'instances_r15.csv').open('w',newline='') as f:
    writer=csv.writer(f,lineterminator='\n');keys=['instance_id','freecad_object_name','source_object_name','part_number','group','geometry_kind']
    writer.writerow(keys);writer.writerows([r[k] for k in keys] for r in rows)
report={'status':'PASS_SOURCE_INVENTORY_BOM','native_sha256':data['source']['cad_sha256'],'ax01_sha256':sha(path),
        'physical_instances':455,'source_definition_rows':108,'summed_quantities':455,
        'files':{str(p.relative_to(ROOT)):sha(p) for p in (folder/'bom_r15.csv',folder/'instances_r15.csv')},
        'limits':'Native source-definition inventory; not a supplier purchasing list, mass qualification or fabrication release.'}
(ROOT/'reports/verification/r15_bom.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'])
