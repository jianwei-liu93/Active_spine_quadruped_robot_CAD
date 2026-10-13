"""Supplemental isolated finite screen after installed-MCP native construction.

The MCP headless helper cannot read its cache script in this snap runtime.
This runner never changes or saves a document. Canonical inspection and CAD
construction remain with the lead in installed FreeCAD MCP.
"""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]

def main(expected_sha=None):
    import FreeCAD as App
    import verify_compact_revision_r12 as verify
    native=ROOT/'cad/flexor_r14_robot.FCStd'
    sha=hashlib.sha256(native.read_bytes()).hexdigest()
    if expected_sha is not None and expected_sha!=sha:
        raise RuntimeError('Lead supplied native SHA differs')
    old=App.openDocument(str(ROOT/'cad/flexor_r10_robot.FCStd'))
    current=App.openDocument(str(native))
    prepared=verify.prepare(current,old,expected_native_sha256=sha)
    print('PREPARED_R14',sha,len(prepared['states']),flush=True)
    result=verify.run(prepared,progress_path=ROOT/'reports/verification/r14_motion_91.json')
    result['execution']='Supplemental isolated FreeCADCmd; source construction/primary native inspection through installed MCP'
    result['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (ROOT/'reports/verification/r14_motion_91.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT_R14',result['status'],len(result['records']),len(result['collisions']),result['errors'],flush=True)
    App.closeDocument(current.Name);App.closeDocument(old.Name)

if __name__=='__main__':main()


def run_partition(partition, count, expected_sha):
    """Independent process, distinct report file, no shared FreeCAD session."""
    import FreeCAD as App
    import verify_compact_revision_r12 as verify
    prefix=json.loads((ROOT/'reports/verification/r14_motion_prefix.json').read_text())
    completed={r['sample_id'] for r in prefix['records']}
    native=ROOT/'cad/flexor_r14_robot.FCStd'
    if hashlib.sha256(native.read_bytes()).hexdigest()!=expected_sha:raise RuntimeError('Native changed')
    old=App.openDocument(str(ROOT/'cad/flexor_r10_robot.FCStd'));current=App.openDocument(str(native))
    prepared=verify.prepare(current,old,expected_native_sha256=expected_sha)
    indices=[i for i,s in enumerate(prepared['states']) if s['sample_id'] not in completed]
    indices=indices[partition::count]
    prepared['states']=[prepared['states'][i] for i in indices]
    prepared['descriptors']=[prepared['descriptors'][i] for i in indices]
    prepared['manifest_sha256']=verify.base._digest(prepared['states'])
    prepared['coverage_scope']='Exact remaining r14 4deg spine inputs; partition '+str(partition)+' of '+str(count)
    folder=ROOT/'reports/verification/r14_motion_partitions';folder.mkdir(exist_ok=True)
    output=folder/('part_'+str(partition)+'.json')
    print('PREPARED_PART',partition,len(indices),flush=True)
    report=verify.run(prepared,progress_path=output)
    report.update(partition=partition,partitions=count,runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  execution='Isolated read-only FreeCADCmd partition; all CAD construction through installed MCP')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT_PART',partition,report['status'],len(report['records']),len(report['collisions']),report['errors'],flush=True)
    App.closeDocument(current.Name);App.closeDocument(old.Name)
