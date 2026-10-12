"""Validate actual read-only spine-sweep partitions; never simulate evidence."""
import argparse
import json
import math
from pathlib import Path


_MATCH_FIELDS=('revision','document_sha256','motion_map_sha256','volume_tolerance_mm3',
               'bbox_overlap_tolerance_mm','reprojection_tolerance_mm','leg_angles_rad',
               'motion_kinds','instances')

def aggregate(paths,output=None):
    paths=[Path(p) for p in paths]
    if not paths:raise ValueError('No actual partition reports supplied')
    reports=[json.loads(p.read_text()) for p in paths]
    reference=reports[0];coverage=set();sample_count=0
    def inventory(r):
        return sorted(r['parts'],key=lambda row:row['instance'])
    baseline=inventory(reference)
    for field in ('document_sha256','motion_map_sha256'):
        v=reference.get(field)
        if not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v):
            raise ValueError('Missing/invalid native evidence SHA: '+field)
    for path,r in zip(paths,reports):
        if r.get('status')!='PASS':raise ValueError(str(path)+': partition status is not PASS')
        if r.get('errors') or r.get('raw_overlaps') or r.get('raw_overlap_pairs')!=0:
            raise ValueError(str(path)+': errors or raw intersection hits')
        for key in _MATCH_FIELDS:
            if key not in r or r[key]!=reference.get(key):raise ValueError('Inconsistent partition '+key)
        if inventory(r)!=baseline:raise ValueError('Inconsistent native inventory')
        if not baseline or len(baseline)!=r['instances'] or len({p['instance'] for p in baseline})!=len(baseline):
            raise ValueError('Invalid native inventory cardinality')
        if not r.get('native_shapes_valid_one_solid') or not all(p['valid'] and p['solids']==1 and math.isfinite(p['volume_mm3']) and p['volume_mm3']>0 for p in baseline):
            raise ValueError('Invalid native shapes')
        neutral=r.get('neutral',{});reprojection=r.get('neutral_reprojection',{})
        if neutral.get('phase_deg')!=0 or neutral.get('raw_overlaps') or reprojection.get('status')!='PASS':
            raise ValueError('Neutral checks missing/failed')
        if reprojection.get('saved_phase_rad')!=reference.get('neutral_reprojection',{}).get('saved_phase_rad'):
            raise ValueError('Inconsistent saved native phase')
        for key in ('identity_world_copy_max_bound_error_mm','saved_phase_descriptor_max_bound_error_mm'):
            value=reprojection.get(key)
            if value is None or not math.isfinite(value) or value>r['reprojection_tolerance_mm']:
                raise ValueError('Native reprojection exceeds threshold')
        pc=r.get('pair_coverage',{})
        if not pc.get('neutral_all_pairs_once') or pc.get('pair_samples_covered_including_cache')!=pc.get('pair_samples_expected'):
            raise ValueError('Incomplete native pair coverage')
        if pc.get('all_pairs')!=r['instances']*(r['instances']-1)//2:
            raise ValueError('Native all-pairs inventory coverage disagrees')
        phases=r.get('sample_degrees',[])
        if not phases or phases[0]!=0 or phases!=sorted(set(phases)):
            raise ValueError('Actual phase list must be sorted unique with neutral first')
        if r.get('actual_sample_degrees')!=phases or r.get('samples_total')!=len(phases) or r.get('samples_completed')!=len(phases):
            raise ValueError('Incomplete/inconsistent actual samples')
        requested=r.get('requested_phase_values_deg')
        if requested is not None and (requested!=sorted(set(requested)) or phases!=sorted(set([0]+requested)) or r.get('requested_samples_total')!=len(requested)):
            raise ValueError('Requested and actual partition phases disagree')
        if any(not math.isfinite(v) or not 0<=v<=360 or not float(v).is_integer() for v in phases):
            raise ValueError('Aggregate requires actual integer-degree poses in [0,360]')
        if pc.get('pair_samples_expected')!=pc.get('all_pairs',-1)*len(phases):
            raise ValueError('Incorrect expected pair samples')
        sample_count+=len(phases);coverage.update(int(v) for v in phases)
    missing=sorted(set(range(361))-coverage)
    if missing:raise ValueError('Missing actual phase degrees: '+repr(missing))
    result={'revision':'r05','status':'PASS','scope':'Actual native partition evidence covering every integer degree 0..360; fixed saved leg/wheel states; sampled raw intersection checks only',
            'sample_degrees':sorted(coverage),'samples_total':len(coverage),'samples_completed':len(coverage),
            'actual_partition_sample_count':sample_count,'duplicate_phase_samples':sample_count-len(coverage),
            'partition_reports':[str(p.resolve()) for p in paths],'partitions':len(paths),
            'native_inventory':baseline,'raw_overlaps':[],'errors':[],
            **{k:reference[k] for k in _MATCH_FIELDS if k!='revision'},
            'limits':['Finite samples; no continuous clearance certificate.','Leg/wheel states fixed; no gait, load or elastic equilibrium certification.']}
    if output:
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('partitions',nargs='+',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    try:result=aggregate(args.partitions,args.output)
    except (ValueError,KeyError,TypeError) as exc:parser.exit(1,'REJECTED: '+str(exc)+'\n')
    print(json.dumps({'status':result['status'],'samples_completed':result['samples_completed'],'partitions':result['partitions']}))
    return 0

if __name__=='__main__':raise SystemExit(main())
