"""Pure-Python validation/merge of frozen finite r14 motion evidence.

No CAD imports or document access. Importing this module performs no work.
The CLI validates without writing by default; --write explicitly publishes the
final report only after every gate passes and source bytes are rechecked.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NATIVE = '7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87'
PREFIX_RUNNER = '40472b333cd672e7787fd6dd699a41dd9dcb20f074d220e2b085cc46868834c2'
PAIR_COUNT = 32032


class MergeError(ValueError):
    """Missing, incomplete, inconsistent or changed evidence."""


def require(condition, message):
    if not condition:
        raise MergeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: '+key)
        result[key] = value
    return result


def read(path):
    raw = Path(path).read_bytes()
    def invalid(value):
        raise MergeError('Nonfinite JSON constant: '+value)
    data = json.loads(raw, object_pairs_hook=_object, parse_constant=invalid)
    # Also catches valid JSON numeric literals overflowing Python floats.
    json.dumps(data, allow_nan=False)
    return data, hashlib.sha256(raw).hexdigest()


def _hex(value, label):
    require(isinstance(value, str) and len(value) == 64 and
            all(c in '0123456789abcdef' for c in value), label+': invalid SHA256')


def validate(plan, prefix, partitions, root=ROOT):
    """Return a merged report in memory; never write or import CAD code.

    prefix is the exact fifteen completed records of the interrupted first job.
    Only that prefix may lack final unchanged flags and retain its pinned old
    runner hash. Its frozen native/dependency files are independently rehashed.
    """
    root = Path(root).resolve()
    json.dumps([plan,prefix,partitions],allow_nan=False)
    states = plan['states']; ids = [s['sample_id'] for s in states]
    require(len(states) == 91 and len(set(ids)) == 91, 'Plan must contain91 unique states')
    require(plan['native_sha256'] == EXPECTED_NATIVE, 'Plan native freeze differs')
    require(plan['pair_count'] == PAIR_COUNT, 'Plan affected pair count differs')
    affected = plan['affected']
    require(len(affected) == 77 and affected == sorted(set(affected)), 'Plan affected IDs differ')
    first = states[0]
    require(set(first['leg_angles']) == {'foreL','foreR','hindL','hindR'}, 'Plan neutral leg IDs differ')
    for degree, state in zip(range(0,361,4), states):
        require(state['sample_id'] == 'r14_spine_'+str(degree).zfill(3), 'Plan phase ID differs')
        require(state['theta'] == math.radians(degree), 'Plan phase differs')
        require(state['leg_angles'] == first['leg_angles'] and state['wheel_angle'] == 0.,
                'Plan must retain neutral legs and wheel0')
        require(state['input_sha256'] == digest({k:state[k] for k in ('theta','leg_angles','wheel_angle')}),
                state['sample_id']+': plan input SHA differs')
    require(len(partitions) == 4, 'Exactly four final partitions required')
    require(prefix['status'] == 'INTERRUPTED_COMPLETED_PREFIX_ONLY', 'Wrong prefix status')
    require(prefix.get('remaining_inputs_not_claimed') is True, 'Prefix must disclaim uncompleted inputs')
    require(prefix.get('runner_sha256') == PREFIX_RUNNER, 'Historical prefix runner differs')
    require(prefix.get('all_requested_pair_decisions_complete') is False, 'Prefix must remain explicitly incomplete')
    require([r['sample_id'] for r in prefix['records']] == ids[:15], 'Prefix must contain exactly first15 states')
    require(prefix['expected_sample_ids'] == ids and prefix['manifest_sha256'] == digest(states),
            'Prefix requested manifest differs from complete plan')
    ref = prefix
    require(ref['identity']['status'] == 'PASS_IDENTITY_ONLY', 'Identity did not pass')
    require(ref['identity']['affected'] == affected and ref['identity']['pair_count'] == PAIR_COUNT,
            'Identity affected IDs/pairs differ from plan')
    require(ref['identity']['unchanged_count'] == 378 and ref['identity']['new_count'] == 8 and
            len(ref['identity']['changed_existing']) == 69 and len(ref['identity']['retired']) == 40,
            'Physical migration identity differs')
    native_paths = {str(root/'cad/flexor_r14_robot.FCStd'),str(root/'cad/flexor_r10_robot.FCStd')}
    require(set(ref['native_sha256']) == native_paths, 'Expected exact current/baseline native inputs')
    require(ref['native_sha256'][str(root/'cad/flexor_r14_robot.FCStd')] == EXPECTED_NATIVE,
            'Native report freeze differs')
    require(bool(ref['dependency_sha256']), 'Empty dependency freeze')
    require('src/verify_compact_revision_r12.py' in ref['dependency_sha256'], 'Verifier not frozen')
    require('parameters/assembly_r14.json' in ref['dependency_sha256'], 'r14 config not frozen')
    _hex(ref['pair_sha256'], 'Affected pair hash')
    runner_now = sha(root/'src/verify_candidate_r14_cli.py')
    stable = ('assembly_revision','configuration_path','identity','pair_count','pair_sha256',
              'native_sha256','dependency_sha256','lead_frozen_sha256','tolerances',
              'changed_existing_count','new_instance_count','retired_instance_count','section_screen','s9')
    records = {}; origins = {}; counts = {'bbox':0,'occ':0,'cached':0}
    remaining = states[15:]
    for index, report in enumerate([prefix]+list(partitions)):
        label = 'prefix' if index == 0 else 'part_'+str(index-1)
        require(report['assembly_revision'] == 'r14' and report['configuration_path'] == 'parameters/assembly_r14.json',
                label+': wrong assembly/configuration')
        require(report['lead_frozen_sha256'] == EXPECTED_NATIVE, label+': lead freeze differs')
        for key in stable:
            require(report[key] == ref[key], label+': inconsistent '+key)
        for key in ('collisions','errors','exceptions','adaptive_intersections'):
            require(report.get(key) == [], label+': nonempty '+key)
        require(report.get('continuous_clearance') is False and report.get('fabrication_release') is False,
                label+': unsupported release/continuous claim')
        require(report['section_screen']['status'] == 'PASS_BOUNDED_LOCAL_PROBES_ONLY', label+': section gate missing')
        require(report['s9']['status'] == 'PASS_ACTUAL_NEUTRAL_CYLINDRICAL_AXES_ONLY', label+': actual axis gate missing')
        expected_states = states if index == 0 else remaining[index-1::4]
        expected_ids = [s['sample_id'] for s in expected_states]
        if index:
            require(report['status'] == 'PASS_AFFECTED_FINITE_ONLY', label+': not a completed finite PASS')
            require(report.get('partition') == index-1 and report.get('partitions') == 4, label+': partition metadata differs')
            require(report.get('disk_inputs_unchanged') is True and report.get('dependencies_unchanged') is True,
                    label+': final unchanged gates missing/failed')
            require(report.get('runner_sha256') == runner_now, label+': runner changed')
            require(report.get('all_requested_pair_decisions_complete') is True, label+': incomplete decisions')
            require(report['manifest_sha256'] == digest(expected_states), label+': exact partition manifest differs')
            require(len(report['records']) == 19, label+': expected19 completed states')
        else:
            for key in ('disk_inputs_unchanged','dependencies_unchanged'):
                require(key not in report or report[key] is True, 'Prefix explicitly failed '+key)
        require(report['expected_sample_ids'] == expected_ids, label+': requested sample IDs differ')
        require(report['requested_sample_count'] == len(expected_states) and
                report['expected_pair_decisions'] == len(expected_states)*PAIR_COUNT, label+': request totals differ')
        require(report['samples_completed'] == len(report['records']), label+': completed sample count differs')
        completed = 0
        for row in report['records']:
            sample = row['sample_id']
            require(sample in expected_ids and sample not in records, label+': extra or duplicate sample '+sample)
            state = states[ids.index(sample)]
            require(row['input_sha256'] == state['input_sha256'], sample+': actual input differs')
            require(row['pair_count'] == PAIR_COUNT, sample+': pair coverage differs')
            require(row.get('guide_warnings') == [], sample+': guide warnings')
            _hex(row['decision_sha256'], sample+' decision hash')
            require(set(row['counts']) == set(counts), sample+': decision categories differ')
            require(all(type(v) is int and v >= 0 for v in row['counts'].values()), sample+': invalid decision count')
            require(sum(row['counts'].values()) == PAIR_COUNT, sample+': incomplete decision coverage')
            for key in counts:counts[key] += row['counts'][key]
            completed += PAIR_COUNT; records[sample] = row; origins[sample] = label
        require(report['completed_pair_decisions'] == completed, label+': completed decision total differs')
        require([r['sample_id'] for r in report['records']] == (ids[:15] if not index else expected_ids),
                label+': completed record ordering/coverage differs')
    require(set(records) == set(ids) and len(records) == 91, 'Union is not exactly91 unique complete states')
    for path, frozen in ref['native_sha256'].items():
        _hex(frozen, path);require(sha(path) == frozen, 'Native input changed: '+path)
    for relative, frozen in ref['dependency_sha256'].items():
        path = (root/relative).resolve()
        require(path.is_relative_to(root) and not Path(relative).is_absolute(), 'Dependency path escapes project')
        _hex(frozen, relative);require(sha(path) == frozen, 'Dependency changed: '+relative)
    return {'status':'PASS_AFFECTED_FINITE_ONLY','assembly_revision':'r14',
        'configuration_path':'parameters/assembly_r14.json','identity':ref['identity'],
        'manifest_sha256':digest(states),'native_sha256':ref['native_sha256'],
        'dependency_sha256':ref['dependency_sha256'],'lead_frozen_sha256':EXPECTED_NATIVE,
        'pair_count':PAIR_COUNT,'pair_sha256':ref['pair_sha256'],'affected':affected,
        'requested_sample_count':91,'expected_sample_ids':ids,'samples_completed':91,
        'records':[records[i] for i in ids],'record_sources':origins,
        'expected_pair_decisions':91*PAIR_COUNT,'completed_pair_decisions':sum(counts.values()),
        'counts':counts,'occ_checks':counts['occ'],'cached_pair_checks':counts['cached'],
        'counting_rule':'Only decision counts attached to91 unique complete records are summed; raw job counters are preserved in source_reports and are not added to completed-record totals.',
        'all_requested_pair_decisions_complete':True,'disk_inputs_unchanged':True,'dependencies_unchanged':True,
        'collisions':[],'errors':[],'exceptions':[],'continuous_clearance':False,'fabrication_release':False,
        'section_screen':ref['section_screen'],'s9':ref['s9'],'tolerances':ref['tolerances'],
        'coverage_scope':'91 inclusive spine phases0..360deg at4deg, stored neutral legs and wheel0; affected pairs only',
        'limitations':ref['limitations'],
        'prefix_exception':{'status':'ACCEPTED_COMPLETED_RECORDS_ONLY','completed_samples':15,
            'explanation':'The first job was intentionally interrupted after15 complete published records. It never finalized its unchanged flags or completed the full91 requested inputs. Only those15 records are counted. All76 remaining states must independently pass four final19-state partitions. Frozen native/dependency bytes are rehashed at merge time.',
            'historical_runner_sha256':PREFIX_RUNNER,'current_partition_runner_sha256':runner_now,
            'runner_note':'The prefix predates addition of the independent partition entrypoint; its exact historical runner hash is pinned. All partition runner hashes must equal the current runner. Geometry/verifier dependency hashes must agree across every source report.'}}


def merge(root=ROOT, write=False):
    """Read stable snapshots, validate, optionally atomically write final evidence."""
    root = Path(root).resolve();folder = root/'reports/verification'
    paths = [folder/'r14_motion_plan_91.json',folder/'r14_motion_prefix.json']+[
        folder/'r14_motion_partitions'/('part_'+str(i)+'.json') for i in range(4)]
    loaded = [read(p) for p in paths]
    result = validate(loaded[0][0],loaded[1][0],[x[0] for x in loaded[2:]],root)
    result['source_reports'] = {str(p.relative_to(root)):{'sha256':h,'raw_report':d}
                                for p,(d,h) in zip(paths,loaded)}
    result['merger_sha256'] = sha(Path(__file__))
    require(all(sha(p) == item[1] for p,item in zip(paths,loaded)), 'Source report changed during merge')
    # Recheck runtime inputs as well as reports immediately before publication.
    for path,frozen in result['native_sha256'].items():
        require(sha(path) == frozen, 'Native changed before publication: '+path)
    for relative,frozen in result['dependency_sha256'].items():
        require(sha(root/relative) == frozen, 'Dependency changed before publication: '+relative)
    if write:
        output = folder/'r14_motion_91.json';temporary = output.with_suffix('.json.merge.tmp')
        text = json.dumps(result,indent=2,allow_nan=False)+'\n'
        temporary.write_text(text);temporary.replace(output)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Publish only after all strict gates pass')
    args = parser.parse_args()
    try:
        result = merge(write=args.write)
    except (MergeError,KeyError,OSError,ValueError,TypeError) as error:
        parser.exit(1,'MERGE_REFUSED: '+str(error)+'\n')
    print(result['status'],result['samples_completed'],result['completed_pair_decisions'],
          'written' if args.write else 'validated; no output written')


if __name__ == '__main__':
    main()
