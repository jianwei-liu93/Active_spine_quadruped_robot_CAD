"""Generate source/instance BOM tables from the verified r15b manifest."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run():
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    path=ROOT/'animation/motion/ax01_r15b.json';data=json.loads(path.read_text())
    assert data['source']['cad_sha256']==sha(ROOT/'cad/flexor_r15b_robot.FCStd')
    rows=data['instances'];assert len(rows)==len({r['instance_id'] for r in rows})==455
    counts=Counter((r['source_object_name'],r['part_number']) for r in rows)
    assert len(counts)==108 and sum(counts.values())==455
    folder=ROOT/'bom';folder.mkdir(exist_ok=True)
    with (folder/'bom_r15b.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['source_object','part_number','quantity'])
        writer.writerows((source,number,n) for (source,number),n in sorted(counts.items()))
    with (folder/'instances_r15b.csv').open('w',newline='') as f:
        keys=['instance_id','freecad_object_name','source_object_name','part_number','group','geometry_kind']
        writer=csv.writer(f,lineterminator='\n');writer.writerow(keys)
        writer.writerows([r[k] for k in keys] for r in rows)
    report={'status':'PASS_SOURCE_INVENTORY_BOM','native_sha256':data['source']['cad_sha256'],
            'physical_instances':455,'source_definition_rows':108,'summed_quantities':455,
            'files':{str(p.relative_to(ROOT)):sha(p) for p in (folder/'bom_r15b.csv',folder/'instances_r15b.csv')},
            'limits':'Source definition inventory; supplier purchasing/fit/strength qualification outstanding.'}
    (ROOT/'reports/verification/r15b_bom.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__': print(run()['status'])
