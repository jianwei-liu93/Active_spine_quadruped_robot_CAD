"""Bounded read-only r14 changed-part screen; lead calls run in FreeCADCmd.

Nine finite v2 cycle phases only. No source/pose/native writes, fit exceptions,
full motion campaign, continuous-clearance or fabrication-release claim.
"""
import json
import math
import time
from pathlib import Path

from animation_coordination_v2 import PROFILE, PROFILE_PATH, trajectory, paper_descriptor_context
from animation_pose_export import ROOT, digest, serial, snapshot, shape_hash

NATIVE_SHA256 = '7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87'
PHASES = (0, 18, 90, 135, 180, 198, 240, 270, 330)
VOLUME_TOL = 1e-5
BBOX_PAD = 1e-6


def run(native_path):
    """Open exact saved r14 privately; inspect detached world BReps and close."""
    import FreeCAD as App
    import leg_motion_r07 as motion
    from verify_motion_package_r08 import DEPENDENCIES
    from verify_changed_revision_r10 import _native_state_guard
    from verify_frame_revision_r09 import _bbox
    start = time.monotonic(); native = Path(native_path).resolve()
    out = ROOT/'reports/animation/coordination_r14_changed_clearance.json'
    identity_path = ROOT/'reports/verification/r14_identity.json'
    axpath = ROOT/'animation/motion/ax01_r14.json'
    config_path = ROOT/'parameters/assembly_r14.json'
    sources = set(DEPENDENCIES) | {Path(__file__).name, 'animation_coordination_v2.py',
        'animation_pose_export.py', 'animation_production_export.py', 'animation_production_validate.py',
        'animation_manifest_validate.py', 'verify_changed_revision_r10.py', 'verify_frame_revision_r09.py'}
    baseline = json.loads(axpath.read_text())
    paths = [ROOT/'src'/n for n in sorted(sources)] + [identity_path, axpath, config_path, PROFILE_PATH]
    paths += [ROOT/p for p in baseline['source']['parameter_files_sha256']]
    # The adapter may read a qualified compression BRep; freeze those inputs too.
    paths += sorted((ROOT/'reports/tmp/spring_kernel_escalation/qualified_shapes').glob('*'))
    paths = [p for p in paths if p.is_file()]
    hashes = {str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in paths}
    report = {'status':'RUNNING', 'native_sha256':digest(native.read_bytes()),
        'profile':PROFILE, 'profile_sha256':hashes[str(PROFILE_PATH.relative_to(ROOT))],
        'input_files_sha256':hashes, 'phase_samples_deg':list(PHASES), 'records':[],
        'overlaps':[], 'errors':[], 'pair_count_per_phase':32032, 'occ_checks':0,
        'scope':'Every unordered pair with at least one of 77 r14 affected IDs among 455 actual physical instances, at nine finite v2 cycle phases only',
        'continuous_clearance':False, 'full_campaign':False, 'loaded_equilibrium':False,
        'fabrication_release':False, 'prior_r10_full_campaign_certifies_new_path':False,
        'unchanged_geometry_evidence':'Prior v2 leg-pair evidence used the same nine phases; unchanged/unchanged pairs are outside this screen',
        'volume_tolerance_mm3':VOLUME_TOL, 'bbox_padding_mm':BBOX_PAD}
    def write():
        report['elapsed_seconds'] = time.monotonic()-start
        out.parent.mkdir(parents=True, exist_ok=True)
        temporary = out.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n'); temporary.replace(out)
    doc = None; before = None; source_before = None
    try:
        write()
        assert native == (ROOT/'cad/flexor_r14_robot.FCStd').resolve(), 'Expected canonical r14 input'
        assert report['native_sha256'] == NATIVE_SHA256, 'Frozen native SHA differs'
        assert json.loads(PROFILE_PATH.read_text()) == PROFILE, 'Imported v2 profile differs'
        identity = json.loads(identity_path.read_text()); affected = set(identity['affected'])
        assert identity['status'] == 'PASS_IDENTITY_ONLY' and len(affected) == 77
        assert identity['pair_count'] == 32032 and identity['unchanged_count'] == 378
        assert all(hashes[p] == sha for p,sha in baseline['source']['parameter_files_sha256'].items()), 'AX01 parameter drift'
        config = json.loads(config_path.read_text())
        assert baseline['source']['cad_sha256'] == NATIVE_SHA256 and config['revision'] == 'r14'
        neutral = baseline['frames'][0]['leg_angles_rad']
        doc = App.openDocument(str(native)); before = snapshot(doc)
        source_before = {o.Name:shape_hash(o.Shape) for o in doc.Objects if o.TypeId == 'PartDesign::Body'}
        report['native_state_guard'] = _native_state_guard(doc)
        report['snapshot_before_sha256'] = digest(serial(before))
        report['source_shapes_before_sha256'] = source_before
        names = sorted(o.Name for o in doc.Objects if o.TypeId == 'App::Link')
        assert len(names) == 455 and affected <= set(names)
        pairs = [(a,b) for i,a in enumerate(names) for b in names[i+1:] if a in affected or b in affected]
        assert len(pairs) == 32032
        report.update(affected_instances=sorted(affected), pair_manifest_sha256=digest(serial(pairs)))
        for degree in PHASES:
            theta, angles, wheel = trajectory('coordinated_spine_legs', degree/(360*.2), neutral)
            with paper_descriptor_context():
                shapes, plan = motion.copied_shapes(doc, theta, angles, wheel, config)
            assert set(shapes) == set(names), 'Actual copied-shape coverage differs'
            procedural = {n for n in names if n.endswith(('_Spring','_Cable'))}
            assert len(procedural) == 10 and set(plan['shape_requests']) == procedural, 'All eight springs and both cables must regenerate'
            for name, shape in shapes.items():
                assert shape.isValid() and len(shape.Solids) == 1, 'Invalid physical solid: '+name
                assert math.isfinite(float(shape.Volume)) and shape.Volume > 0, 'Invalid volume: '+name
            bounds = {n:_bbox(shapes[n]) for n in names}
            row = {'phase_deg':degree, 'input_sha256':digest(serial([theta,angles,wheel])),
                'theta_rad':theta, 'leg_angles_rad':angles, 'wheel_angle_rad':wheel,
                'physical_instances':len(shapes), 'valid_single_finite_solids':len(shapes),
                'regenerated_instances':sorted(plan['shape_requests']), 'guide_warnings':plan['guide_warnings'],
                'pairs_checked':0, 'bbox_excluded':0, 'occ_checks':0, 'overlaps':[], 'status':'RUNNING'}
            report['records'].append(row); write()
            for a,b in pairs:
                A,B = bounds[a],bounds[b]
                if any(min(A[k+1],B[k+1])+2*BBOX_PAD < max(A[k],B[k]) for k in (0,2,4)):
                    row['bbox_excluded'] += 1
                else:
                    common = shapes[a].common(shapes[b])
                    assert common.isNull() or common.isValid(), 'Invalid OCC common: '+a+'/'+b
                    volume = float(common.Volume)
                    assert math.isfinite(volume) and volume >= 0, 'Invalid intersection volume: '+a+'/'+b
                    row['occ_checks'] += 1; report['occ_checks'] += 1
                    if volume > VOLUME_TOL:
                        hit = {'phase_deg':degree, 'a':a, 'b':b, 'intersection_mm3':volume}
                        row['overlaps'].append(hit); report['overlaps'].append(hit)
                row['pairs_checked'] += 1
                if row['pairs_checked'] % 4000 == 0: write()
            assert row['pairs_checked'] == row['bbox_excluded']+row['occ_checks'] == len(pairs)
            row['status'] = 'FAIL' if row['overlaps'] or row['guide_warnings'] else 'PASS'
            write(); print('R14_COORDINATION_SCREEN',degree,row['status'],row['pairs_checked'],flush=True)
            if row['status'] == 'FAIL': break  # Finish this phase's raw ledger, then stop.
        report['status'] = 'PASS_BOUNDED_CHANGED_PAIRS' if len(report['records']) == len(PHASES) and all(r['status']=='PASS' for r in report['records']) else 'FAIL'
    except Exception as error:
        report['errors'].append(repr(error)); report['status'] = 'FAIL'
    finally:
        report['native_file_unchanged'] = digest(native.read_bytes()) == report['native_sha256']
        report['input_files_unchanged'] = all((ROOT/p).is_file() and digest((ROOT/p).read_bytes())==sha for p,sha in hashes.items())
        if doc is not None and before is not None:
            after = snapshot(doc)
            source_after = {o.Name:shape_hash(o.Shape) for o in doc.Objects if o.TypeId == 'PartDesign::Body'}
            report.update(snapshot_after_sha256=digest(serial(after)), document_unchanged=before==after,
                          source_shapes_unchanged=source_before==source_after)
        if not all(report.get(k,False) for k in ('native_file_unchanged','input_files_unchanged','document_unchanged','source_shapes_unchanged')):
            report['status'] = 'FAIL'; report['errors'].append('Read-only input/document/source preservation guard failed')
        report['phases_completed'] = sum(r['status'] != 'RUNNING' for r in report['records'])
        report['total_pairs_checked'] = sum(r['pairs_checked'] for r in report['records'])
        write()
        if doc is not None: App.closeDocument(doc.Name)
    return report


if __name__ == '__main__':
    import sys
    run(sys.argv[1] if len(sys.argv)>1 else ROOT/'cad/flexor_r14_robot.FCStd')
