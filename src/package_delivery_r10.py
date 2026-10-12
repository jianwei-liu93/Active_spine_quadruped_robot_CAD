"""Fail-closed inventory of accepted frozen r10 deliverables; never mutates CAD.

Prepare first; lead calls run() only after final artifacts/reviews exist.
run(write_inventory=False) validates without writing or deleting inventory.
PDF/final-review evidence contracts are documented in the preparation review.
"""
from __future__ import annotations
import csv
from collections import Counter
import hashlib
import json
import math
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_NATIVE_SHA256 = None  # Calculated from the current saved canonical at validation entry.
PACKAGE_STATUS = 'EXPORTS_AND_STEP_ROUNDTRIP_VALIDATED_NO_FABRICATION_RELEASE'
OUTPUT = 'reports/delivery_manifest_r10.json'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def path(value):
    p = Path(value)
    p = (ROOT / p).resolve() if not p.is_absolute() else p.resolve()
    require(p.is_relative_to(ROOT.resolve()), 'Artifact outside project: ' + str(p))
    require(p.is_file() and p.stat().st_size > 0, 'Missing/empty artifact: ' + str(p))
    return p


def digest(value):
    h = hashlib.sha256()
    with path(value).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def path_with_digest(value, expected_sha=None):
    """Read-only artifact check for the manual's shared evidence gates."""
    artifact = path(value)
    if expected_sha is not None:
        require(digest(artifact) == expected_sha, 'Artifact digest mismatch: ' + str(artifact))
    return artifact


def read(value):
    return json.loads(path(value).read_text(encoding='utf-8'))


def native_match(record, label):
    values = [record[k] for k in ('native_sha256', 'canonical_robot_sha256', 'source_sha256', 'final_canonical_sha256') if k in record]
    require(values and all(v == FROZEN_NATIVE_SHA256 for v in values), label + ': missing/stale frozen native SHA')


def page_count(value):
    p = path(value)
    try:
        from pypdf import PdfReader
    except ImportError:
        result = subprocess.run(['pdfinfo', str(p)], capture_output=True, text=True, check=True)
        counts = [int(line.split(':', 1)[1]) for line in result.stdout.splitlines() if line.startswith('Pages:')]
        require(len(counts) == 1, 'Cannot determine PDF pages: ' + str(p))
        return counts[0]
    return len(PdfReader(str(p)).pages)



def json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def collect_motion_readonly(partitions):
    """Exact collect-equivalent; validates files without publishing summary.json."""
    import verify_changed_revision_r10 as verifier
    OUT, FREEZE, IDENTITY, WHOLE_Y = verifier.OUT, verifier.FREEZE, verifier.IDENTITY, verifier.WHOLE_Y
    _bounds_gate, manifest = verifier._bounds_gate, verifier.manifest
    _sha, _digest = verifier._sha, verifier._digest
    _decision_masks_complete = verifier._decision_masks_complete
    _baseline_gate, validate_freeze = verifier._baseline_gate, verifier.validate_freeze
    VOLUME_TOL = verifier.VOLUME_TOL
    if not isinstance(partitions,int) or not 1<=partitions<=24:
        raise ValueError('Expected1..24 partitions')
    freeze,proof,bounds = _bounds_gate();plan = manifest()
    indexed = [(i,json.loads(p.read_text())) for i in range(partitions)
               for p in [OUT/('part_'+str(i)+'.json')] if p.exists()]
    reports = [p for i,p in indexed];records = [r for p in reports for r in p['records']]
    expected = {s['sample_id']:s for s in plan['states']};completed = [r['sample_id'] for r in records]
    coherent = all(p['partition']==i and p['partitions']==partitions and
                   p['freeze_sha256']==_sha(FREEZE) and p['identity_sha256']==_sha(IDENTITY) and
                   p['whole_y_sha256']==_sha(WHOLE_Y) and p['manifest_sha256']==plan['sha256'] and
                   p['native_sha256']==freeze['native_sha256'] and p['dependency_sha256']==freeze['dependency_sha256'] and
                   p['pair_sha256']==bounds['pair_sha256'] and p['pair_count']==9996 and
                   p['expected_sample_ids']==[s['sample_id'] for s in plan['states'][i::partitions]]
                   for i,p in indexed)
    whole_mask = sum(1<<i for i in bounds['whole_cycle_disjoint_pair_indices'])
    pair_list = bounds['pairs']
    def narrow_ledger_ok(row):
        bits = 0
        for item in row['narrowphase']:
            i = item['pair_index']
            if not 0<=i<9996 or bits&(1<<i) or [item['a'],item['b']]!=pair_list[i]:
                return False
            if item['actual_solid'] is not True or not math.isfinite(item['intersection_mm3']) or not 0<=item['intersection_mm3']<=VOLUME_TOL:
                return False
            bits |= 1<<i
        return (bits==int(row['pair_decision_masks']['actual_boolean'],16) and
                int(row['pair_decision_masks']['whole_cycle_y'],16)==whole_mask)
    records_ok = all(r['status']=='PASS_CHANGED_PAIRS_ONLY' and r['pair_count']==9996 and
                     r['sample_id'] in expected and _digest(r['input'])==_digest(expected[r['sample_id']]) and
                     r['input_sha256']==expected[r['sample_id']]['input_sha256'] and
                     _decision_masks_complete(r['pair_decision_masks']) and narrow_ledger_ok(r) for r in records)
    complete = (len(reports)==partitions and len(completed)==1346 and len(set(completed))==1346 and set(completed)==set(expected))
    changed_pass = complete and coherent and records_ok and all(p['status']=='PASS_CHANGED_PAIRS_ONLY' and p['document_unchanged'] and p['native_unchanged'] and not p['overlaps'] and not p['errors'] for p in reports)
    baseline_pass,baseline_hashes = _baseline_gate(proof)
    result = {'status':'PASS' if baseline_pass and changed_pass else 'INCOMPLETE_OR_FAIL',
              'scope':'Finite-sample raw collision reuse only; primary native/S9/AX and engineering gates remain separate',
              'baseline_r08_full985_coarse105_cage361_pass':baseline_pass,'strict466_identity_pass':True,
              'changed_pair1346_pass':changed_pass,'affected_pair_count':9996,'hash_coherence':coherent,
              'expected_sample_ids':list(expected),'completed_sample_ids':completed,
              'missing_sample_ids':sorted(set(expected)-set(completed)),
              'duplicate_sample_ids':sorted(n for n in set(completed) if completed.count(n)>1),
              'freeze_sha256':_sha(FREEZE),'identity_sha256':_sha(IDENTITY),'whole_y_sha256':_sha(WHOLE_Y),
              'manifest_sha256':plan['sha256'],'baseline_summary_sha256':baseline_hashes,
              'continuous_clearance':False,'loaded_equilibrium':False,'fabrication_release':False}
    validate_freeze()
    return result


def validate_inherited_motion(evidence, add, native_sha, native_links):
    import verify_changed_revision_r10 as verifier
    prefix = 'reports/verification/r10_changed_partitions/'
    freeze = evidence(prefix + 'freeze.json')
    identity = evidence(prefix + 'identity.json')
    bounds = evidence(prefix + 'whole_cycle_y.json')
    summary = evidence(prefix + 'summary.json')
    require(path(freeze['native_path']) == path('cad/flexor_r10_robot.FCStd') and
            freeze['native_sha256'] == native_sha, 'Changed-pair native freeze mismatch')
    require(set(identity['all_instance_names']) == native_links and len(identity['all_instance_names']) == 487 and
            set(identity['affected_instances']) == set(verifier.AFFECTED) and
            len(identity['unchanged_instances']) == len(set(identity['unchanged_instances'])) == 466 and
            set(identity['unchanged_instances']) == native_links - set(verifier.AFFECTED) and
            identity.get('existing_motion_and_parameters_exact') is True and not identity.get('errors'),
            'Strict466 unchanged/21 affected identity ledger incomplete')
    require(identity.get('native_state_guard', {}).get('r10', {}).get('status') == 'PASS_NATIVE_STATE_ONLY' and
            identity['native_state_guard']['r10'].get('body_count') == 95 and
            identity['native_state_guard']['r10'].get('invalid_or_error_count') == 0,
            'Native Body/member state guard missing or failed')
    rows = identity.get('records', [])
    require(len(rows) == 466 and {r['instance'] for r in rows} == set(identity['unchanged_instances']),
            'Strict identity per-instance records incomplete')
    for row in rows:
        require(row.get('placement_exact') is True, 'Identity neutral placement differs')
        for key in ('source_geometry', 'placed_geometry'):
            proof = row[key]
            if proof.get('method') == 'exact_brep':
                require(proof.get('old_sha256') and proof['old_sha256'] == proof.get('new_sha256'), 'Identity BRep mismatch')
            else:
                require(proof.get('method') == 'strict_boolean_adaptive_bbox' and
                        len(proof.get('bidirectional_difference_mm3', [])) == 2 and
                        all(math.isfinite(x) and 0 <= x <= 1e-5 for x in proof['bidirectional_difference_mm3']),
                        'Identity strict Boolean proof incomplete')
                check_geometry(proof['adaptive_comparison'], 1, 'Identity strict adaptive proof')
    require(bounds['pairs'] == [list(p) for p in verifier.affected_pairs(native_links)], 'Changed-pair ledger mismatch')
    first = evidence(prefix + 'part_0.json')
    partitions = first.get('partitions')
    actual = collect_motion_readonly(partitions)
    require(actual == summary and actual['status'] == 'PASS', 'Current read-only motion aggregation differs or failed')
    for i in range(partitions):
        part = first if i == 0 else evidence(prefix + 'part_' + str(i) + '.json')
        require(part.get('native_state_guard', {}).get('status') == 'PASS_NATIVE_STATE_ONLY' and
                part['native_state_guard'].get('invalid_or_error_count') == 0,
                'Partition native-state guard missing/failed')
    for name, sha in freeze['dependency_sha256'].items():
        add('src/' + name, sha)
    for value, sha in freeze['baseline_evidence_sha256'].items():
        add(value, sha)
    add('reports/tmp/motion_package_r08/cage_partition_driver.py', freeze['baseline_cage_driver_sha256'])
    old = evidence('reports/verification/r08_motion_partitions/freeze.json')
    add('cad/flexor_r08_robot.FCStd', old['native_sha256'])
    add('parameters/assembly_r08.json', freeze['config_r08_sha256'])
    add('parameters/assembly_r10.json', freeze['config_r10_sha256'])
    add('reports/verification/r08_motion_partitions/full_manifest.json', freeze['original_full_manifest_file_sha256'])
    return {'method': 'INHERITED_R08_FULL985_COARSE105_CAGE361_PLUS_STRICT466_IDENTITY_PLUS_9996_PAIRS_AT1346',
            'current_native_sha256': native_sha, 'identity_sha256': digest(prefix + 'identity.json'),
            'summary_sha256': digest(prefix + 'summary.json'), 'affected_pairs': 9996, 'samples': 1346,
            'continuous_clearance': False, 'loaded_equilibrium': False, 'fabrication_release': False}



def validate_native_state_report(check, native_links, native_bodies):
    native_match(check, 'Native check')
    require(check.get('status') == 'PASS' and check.get('canonical_reopened_recomputed') is True and
            check.get('invalid_native_features') == [] and check.get('fully_constrained_sketches') is True,
            'Native reopen/recompute, state and constrained-sketch gates incomplete')
    rows = check.get('parts', [])
    require(len(rows) == len(native_links) == 487 and {r['instance'] for r in rows} == native_links and
            check.get('editable_bodies') == native_bodies == 95 and
            all(r.get('valid') is True and r.get('solid_count') == 1 and
                math.isfinite(r['volume_mm3']) and r['volume_mm3'] > 0 for r in rows),
            'Native physical solid/body ledger incomplete')


def check_geometry(record, count, label):
    rows = record.get('one_to_one_placed_solids', [])
    require(len(rows) == count and {r['step_solid_index'] for r in rows} == set(range(count)),
            label + ': one-to-one solid ledger incomplete')
    for row in rows:
        require(row.get('status') == 'PASS' and math.isfinite(row['volume_relative_error']) and
                0 <= row['volume_relative_error'] <= row['estimated_margin_upper_relative_difference'] and
                all(math.isfinite(row[k]['volume_mm3']) and row[k]['volume_mm3'] > 0 for k in ('native_measurement','step_measurement')) and
                math.isfinite(row['estimated_margin_upper_relative_difference']) and
                0 <= row['estimated_margin_upper_relative_difference'] <= 1e-6 and
                math.isfinite(row['maximum_bbox_absolute_error_mm']) and 0 <= row['maximum_bbox_absolute_error_mm'] <= 1e-5,
                label + ': strict local volume/bounds failed')



def validate_native_preview(evidence, add, instance_count):
    """Native CAD frame sequence is visual evidence, separate from AX/clearance."""
    from PIL import Image
    report = evidence('reports/motion/r10/capture_manifest.json')
    native_match(report, 'Native motion preview')
    require(report.get('revision') == 'r10' and report.get('status') == 'PASS_CAPTURED_RESTORED' and
            report.get('native_file_unchanged') is True and report.get('pose_restored') is True and
            report.get('visibility_restored') is True and report.get('pose_provenance') == 'PRESCRIBED_KINEMATIC',
            'Native preview source/prescribed pose/restoration evidence incomplete')
    frames = report.get('frames', [])
    require(len(frames) == 24 and [r['frame'] for r in frames] == list(range(24)) and
            [r['spine_phase_deg'] for r in frames] == list(range(0,360,15)), 'Native frame sequence incomplete')
    for row in frames:
        p = add(row['path'], row['sha256'])
        require(p.is_relative_to((ROOT/'reports/motion/r10').resolve()), 'Native preview frame outside r10')
        with Image.open(p) as image:
            image.verify()
        with Image.open(p) as image:
            require(image.format == 'PNG' and image.width > 0 and image.height > 0, 'Native preview PNG invalid')
    matched = report.get('matched_flex_extend', {})
    require(type(matched.get('flex_frame')) is int and type(matched.get('extend_frame')) is int and
            0 <= matched['flex_frame'] < 24 and 0 <= matched['extend_frame'] < 24 and
            matched['flex_frame'] != matched['extend_frame'] and matched.get('same_camera') is True and
            matched.get('fixed_leg_wheel_state') is True, 'Matched flex/extend visual evidence incomplete')
    animation = report.get('animation')
    if animation:
        require(animation.get('actual_cad_capture') is True and animation.get('frames') == 24 and
                animation.get('format') == 'GIF', 'Optional native GIF provenance incomplete')
        p = add(animation['path'], animation['sha256'])
        require(p.is_relative_to((ROOT/'reports/motion/r10').resolve()), 'Native GIF outside r10')
        with Image.open(p) as image:
            require(image.format == 'GIF' and image.n_frames == 24, 'Native GIF frame count invalid')
    return {'frames': 24, 'matched_flex_extend': matched, 'pose_provenance': 'PRESCRIBED_KINEMATIC',
            'clearance_proof': False, 'Blender': 'NOT_RUN', 'physical_instances': instance_count}

def validate_ax01(evidence, add, native_sha, native_links, native_xml):
    from animation_manifest_validate import validate_manifest
    report = evidence('reports/animation/ax01_r10.json')
    native_match(report, 'AX0/AX1')
    require(report.get('cad_revision') == 'r10' and report.get('AX0') == report.get('AX1') == 'PASS' and
            report.get('document_unchanged') is True and report.get('native_file_unchanged') is True and
            report.get('physical_instances') == report.get('effective_motion_coverage') == len(native_links),
            'AX0/AX1 actual inventory/read-only gate failed')
    payload_path = 'animation/motion/ax01_r10.json'
    require(report.get('output') == payload_path, 'AX0/AX1 output path mismatch')
    add(payload_path, report['output_sha256'])
    payload = read(payload_path)
    validate_manifest(payload)
    require(payload['source']['cad_sha256'] == native_sha and payload['source']['cad_revision'] == 'r10' and
            payload['source']['cad_path'] == 'cad/flexor_r10_robot.FCStd', 'AX0/AX1 payload source stale')
    for value, sha in payload['source']['parameter_files_sha256'].items():
        add(value, sha)
    require('parameters/assembly_r10.json' in payload['source']['parameter_files_sha256'], 'AX assembly parameters missing')
    add('src/animation_pose_export.py', report['exporter_source_sha256'])
    require(report.get('generator_source_sha256') and 'animation_manifest_validate.py' in report['generator_source_sha256'], 'AX source hashes missing')
    for name, sha in report['generator_source_sha256'].items():
        add('src/' + name, sha)
    schema = evidence('animation/schema/pose_manifest_v1.schema.json')
    require(schema['properties']['schema_version']['const'] == payload['schema_version'] == '1.0', 'AX schema version mismatch')
    ground_path = 'animation/schema/grounded_instances_r10.json'
    add(ground_path, report['grounding_sha256'])
    ground = read(ground_path)
    require(ground.get('schema_version') == '1.0' and ground.get('cad_sha256') == native_sha and
            (ground.get('review_status') == 'REVIEWED_EXPLICIT_GROUND' or
             (ground.get('cad_revision') == 'r10' and bool(ground.get('provenance')))), 'AX ground supplement stale/unreviewed')
    names = {r['freecad_object_name'] for r in payload['instances']}
    objects = {o.get('name'): o for o in native_xml.findall('.//Object') if o.find('Properties') is not None}
    for row in payload['instances']:
        source = objects[row['freecad_object_name']].find(".//Property[@name='LinkedObject']/XLink")
        require(source is not None and source.get('name') == row['source_object_name'], 'AX native source mapping mismatch')
        pn = objects[row['source_object_name']].find(".//Property[@name='PartNumber']/String")
        require(pn is not None and pn.get('value') == row['part_number'], 'AX native PN mapping mismatch')
    require(names == native_links and len(payload['instances']) == len(native_links) and
            report.get('source_definitions') == len(payload['meshes']), 'AX physical/source inventory mismatch')
    motion_properties = native_xml.findall(".//Property[@name='MotionMap']/String")
    require(len(motion_properties) == 1, 'Native MotionMap missing/ambiguous')
    raw_map = motion_properties[0].get('value')
    original = json.loads(raw_map)
    require(report.get('authoritative_motion_map') == original and
            hashlib.sha256(raw_map.encode()).hexdigest() == payload['source']['motion_map_sha256'], 'AX authoritative MotionMap mismatch')
    grounded = sorted(names - set(original))
    require(ground.get('grounded_names') == report.get('reviewed_explicit_grounded_instances') == grounded and
            report.get('native_motion_entries') == len(original), 'AX ground coverage mismatch')
    metadata = report.get('component_metadata', {})
    require(set(metadata) == names, 'AX component metadata incomplete')
    for name, row in metadata.items():
        require(all(k in row for k in ('label', 'material', 'release_status', 'source_local_origin_mm', 'source_local_axes', 'parent_frame', 'motion')),
                'AX metadata fields missing: ' + name)
        require(row['source_local_origin_mm'] == [0,0,0] and row['source_local_axes'] == 'native right-handed XYZ' and row['parent_frame'], 'AX local-frame metadata mismatch')
        expected = original.get(name, {'kind': 'fixed', 'grounding': 'reviewed lumbar datum'})
        require(row['motion'] == expected, 'AX metadata motion/grounding mismatch: ' + name)
    coupling = report.get('command_coupling', {})
    require(coupling.get('physical_motors') == 7 and coupling.get('commanded_coordinates') == 6 and
            coupling.get('prescribed_knees') == 4 and coupling.get('loaded_passive_motion') == 'NOT_SOLVED', 'AX actuator/passive provenance mismatch')
    checks = report.get('frame_checks', [])
    require([r.get('frame_id') for r in checks] == ['neutral_v1', 'smoke_1', 'smoke_2'], 'AX three actual pose checks missing')
    for row in checks:
        require(row.get('instances') == len(names) and row.get('source_vertex_tests', 0) > 0 and not row.get('guide_warnings'), 'AX actual pose coverage incomplete')
        for key, limit in (('local_to_world_max_error_mm', .02), ('neutral_native_vertex_max_error_mm', .02),
                           ('native_link_bore_center_max_error_mm', .02), ('native_link_axis_angle_max_error_rad', .001),
                           ('spine_closure_max_residual_mm', 1e-5), ('leg_loop_max_residual_mm', 1e-5),
                           ('procedural_owner_anchor_max_reprojection_mm', .02)):
            require(math.isfinite(row[key]) and 0 <= row[key] <= limit, 'AX actual pose residual failed: ' + key)
    for frame in payload['frames']:
        require(Counter(r['generator'] for r in frame['procedural_shapes']) == {'spring': 8, 'cable': 2},
                'AX must regenerate eight springs and two cables in each pose')
        for row in frame['procedural_shapes']:
            for name, sha in row['generator_source_sha256'].items():
                add('src/' + name, sha)
    return {'AX0': 'PASS', 'AX1': 'PASS', 'AX2_AX4': 'NOT_RUN', 'Blender': 'NOT_RUN',
            'payload_sha256': digest(payload_path), 'report_sha256': digest('reports/animation/ax01_r10.json'),
            'schema_sha256': digest('animation/schema/pose_manifest_v1.schema.json'),
            'grounding_sha256': digest(ground_path), 'component_metadata_sha256': json_digest(metadata),
            'physical_instances': len(names), 'source_definitions': len(payload['meshes']), 'poses': 3}

def run(write_inventory=True, expected_native_sha256=None):
    """Validate all final gates, write inventory, and return its absolute Path.

    Default final mode writes only delivery_manifest_r10.json on success and
    removes an existing stale inventory on failure. write_inventory=False
    performs the same checks without writing or deleting any inventory.
    """
    target = ROOT / OUTPUT
    if write_inventory:
        target.unlink(missing_ok=True)
    files = set()
    file_hashes = {}

    def add(value, expected_sha=None):
        p = path(value)
        require(p != target.resolve(), 'Delivery manifest cannot inventory itself')
        actual_sha = digest(p)
        if expected_sha is not None:
            require(actual_sha == expected_sha, 'Artifact digest mismatch: ' + str(p))
        if p in file_hashes:
            require(file_hashes[p] == actual_sha, 'Artifact changed during validation: ' + str(p))
        file_hashes[p] = actual_sha
        files.add(p)
        return p

    def evidence(value):
        add(value)
        return read(value)

    global FROZEN_NATIVE_SHA256
    native = add('cad/flexor_r10_robot.FCStd')
    FROZEN_NATIVE_SHA256 = digest(native)
    require(FROZEN_NATIVE_SHA256 == expected_native_sha256, 'Supply matching lead-frozen canonical SHA')
    with zipfile.ZipFile(native) as archive:
        native_xml = ET.fromstring(archive.read('Document.xml'))
    native_links = {o.get('name') for o in native_xml.findall('.//Object') if o.get('type') == 'App::Link'}
    native_bodies = sum(o.get('type') == 'PartDesign::Body' for o in native_xml.findall('.//Object'))
    require(len(native_links) == 487, 'Frozen r10 must contain487 physical instances')
    objects = {o.get('name'): o for o in native_xml.findall('.//Object') if o.find('Properties') is not None}
    types = {o.get('name'): o.get('type') for o in native_xml.findall('.//Object') if o.get('type')}
    native_sources = {}
    native_pns = {}
    for name in native_links:
        linked = objects[name].find(".//Property[@name='LinkedObject']/XLink")
        require(linked is not None and not linked.get('file'), 'Native source is missing/external: ' + name)
        source = linked.get('name')
        require(source in objects, 'Native source definition missing: ' + name)
        pn = objects[source].find(".//Property[@name='PartNumber']/String")
        require(pn is not None and pn.get('value'), 'Native source PN missing: ' + name)
        native_sources[name] = source
        native_pns[name] = pn.get('value')
    frame_source = 'FRM_LUMBAR_MONOLITHIC_CAGE_r09'
    frame_features = [name for name, kind in types.items() if name.startswith(frame_source) and kind in ('PartDesign::Pad','PartDesign::Pocket')]
    require(native_sources.get('LumbarIntegrated1') == frame_source and types.get(frame_source) == 'PartDesign::Body' and
            native_pns.get('LumbarIntegrated1') == 'FRM_LUMBAR_MONOLITHIC_CAGE_r10' and len(frame_features) == 52 and
            'LumbarIntegrated_1' not in native_links and not any(n.startswith(('FixedLumbarTie','FixedTieScrew')) for n in native_links),
            'r10 one-piece52-feature frame identity/retirement mismatch')
    check = evidence('reports/verification/r10_native_checks.json')
    native_match(check, 'Native check')
    validate_native_state_report(check, native_links, native_bodies)

    motion_evidence = validate_inherited_motion(evidence, add, FROZEN_NATIVE_SHA256, native_links)

    exports = evidence('reports/package_manifest_r10.json')
    require(exports.get('revision') == 'r10' and exports.get('status') == PACKAGE_STATUS, 'Exports not accepted')
    require(exports['native_document']['sha256'] == FROZEN_NATIVE_SHA256 and exports.get('native_file_unchanged') is True,
            'Export source stale')
    require(exports.get('physical_link_count') == len(native_links), 'Export instance count mismatch')
    require(path(exports['native_document']['path']) == native and exports['native_document']['bytes'] == native.stat().st_size,
            'Export native path/byte count mismatch')
    check_geometry(exports['assembly_geometry_check'], len(native_links), 'Assembly export')
    settings = exports['export_settings']
    require(settings.get('volume_relative_tolerance') == 1e-6 and settings.get('bbox_absolute_tolerance_mm') == 1e-5 and
            settings.get('write_surfacecurve_mode') == 1, 'Export strict limits/pcurve setting changed')
    require(exports['clean_document_roundtrip'].get('closed_without_save') is True and
            exports['clean_document_roundtrip'].get('solid_count') == len(native_links), 'Clean STEP roundtrip incomplete')
    export_sources = {p['native_source'] for p in exports['parts']}
    require(len(export_sources) == len(exports['parts']) == exports.get('unique_used_definition_count') == 107, 'Export source count/uniqueness mismatch')
    with add('bom/bom_r10.csv').open(newline='') as stream:
        bom_rows = list(csv.DictReader(stream))
    with add('bom/instances_r10.csv').open(newline='') as stream:
        instance_rows = list(csv.DictReader(stream))
    require(len(instance_rows) == len(native_links) and {r['instance_name'] for r in instance_rows} == native_links,
            'BOM actual physical inventory mismatch')
    require(all(native_sources[r['instance_name']] == r['source_name'] and native_pns[r['instance_name']] == r['part_number'] for r in instance_rows),
            'BOM source/PN mapping differs from actual saved native')
    require(len(bom_rows) == len({r['part_number'] for r in bom_rows}) and
            {r['source_name'] for r in instance_rows} == export_sources, 'BOM PN/source inventory mismatch')
    pn_counts = Counter(r['part_number'] for r in instance_rows)
    require({r['part_number']: int(r['quantity']) for r in bom_rows} == dict(pn_counts), 'BOM quantity reconciliation failed')
    source_counts = Counter(r['source_name'] for r in instance_rows)
    pa12 = {r['source_name'] for r in instance_rows if r['material_name'].casefold() == 'pa12'}
    for part in exports['parts']:
        require(part['quantity'] == source_counts[part['native_source']] and
                {r['part_number'] for r in instance_rows if r['source_name'] == part['native_source']} == {part['part_number']},
                'Part export source/PN/quantity mismatch')
        check_geometry(part['step_geometry_check'], 1, 'Unique part export')
        require(sum(v.endswith('.step') for v in part['files']) == 1 and
                sum(v.endswith('.stl') for v in part['files']) == int(part['native_source'] in pa12), 'Unique STEP/PA12 STL coverage mismatch')
        require(set(part.get('file_geometry_checks', {})) == {v for v in part['files'] if v.endswith('.stl')}, 'STL per-file geometry evidence missing')
        for mesh in part.get('file_geometry_checks', {}).values():
            topology = mesh.get('topology_check', {})
            require(mesh.get('watertight') is True and mesh.get('facet_count', 0) > 0 and
                    math.isfinite(mesh.get('serialized_mesh_volume_relative_error', math.inf)) and
                    0 <= mesh['serialized_mesh_volume_relative_error'] <= 1e-6 and
                    all(topology.get(k) == 0 for k in ('boundary_edge_count','inconsistently_oriented_edge_count','nonmanifold_edge_count')),
                    'PA12 serialized mesh validation failed')
    for record in [exports['assembly_step']] + exports['bom_and_mass_files']:
        add(record['path'], record['sha256'])
    for part in exports['parts']:
        for value in part['files']:
            require(value.startswith(('exports/step/r10/', 'exports/print/r10/')), 'Export path outside accepted r10 scope')
            add(value, part['sha256'][value])
    add('exports/step/r10/README_volume_validation.md')

    drawings = evidence('drawings/r10/drawing_manifest_r10.json')
    native_match(drawings, 'Drawings')
    require(drawings.get('revision') == 'r10' and drawings.get('status') == 'PASS_NATIVE_DIMENSIONS' and
            drawings.get('visual_review') == 'PASS' and drawings.get('pdf_exports') == 'COMPLETE' and not drawings.get('errors'),
            'Drawing acceptance incomplete')
    sheets = drawings['sheets']
    dimensions = sum(len(s['dimensions']) for s in sheets)
    require(sheets and dimensions > 0 and drawings['sheet_count'] == len(sheets) and
            drawings['dimension_count'] == dimensions, 'Drawing actual counts disagree')
    require(len({s['sheet'] for s in sheets}) == len(sheets), 'Duplicate drawing sheets')
    companion = add('cad/flexor_r10_drawings.FCStd', drawings['native_companion_sha256'])
    add('drawings/templates/A4_candidate.svg')
    editable_template = add('drawings/r10/templates/A4_r10_editable.svg')
    with zipfile.ZipFile(companion) as archive:
        document_xml = ET.fromstring(archive.read('Document.xml'))
    template_files = [node.find('String').get('value') for node in document_xml.findall('.//Property')
                      if node.get('name') == 'Template' and node.get('type') == 'App::PropertyFile'
                      and node.find('String') is not None]
    require(len(template_files) == len(sheets), 'Companion template/sheet count mismatch')
    for value in template_files:
        require(path(value) == editable_template, 'Companion template does not resolve to repository r10 template')
    for sheet in sheets:
        require(not sheet.get('errors') and sheet.get('export_layout_status') == 'EXPORTED_CURRENT_NATIVE_LAYOUT', 'Drawing sheet incomplete')
        require(set(sheet.get('export_sha256', {})) >= {'svg', 'pdf'}, 'Drawing sheet export hashes missing')
        for kind in ('svg', 'pdf'):
            p = add(sheet['exports'][kind], sheet['export_sha256'][kind])
            require(p.is_relative_to((ROOT/'drawings/r10').resolve()), 'Drawing outside r10 directory')

    profiles = evidence('exports/profiles/r10/profile_manifest_r10.json')
    native_match(profiles, 'Profiles')
    require(profiles.get('revision') == 'r10' and profiles.get('status') == 'PASS_EXACT_PROFILE_READBACK' and
            profiles.get('source_file_unchanged') is True and not profiles.get('errors'), 'Profiles not accepted')
    require(profiles.get('profile_count') == len(profiles['profiles']) == 3, 'Profile count mismatch')
    for profile in profiles['profiles']:
        require(profile['readback']['status'] == 'PASS', 'Profile readback failed')
        add(profile['path'], profile['sha256'])
    reproduction = evidence('reports/verification/r10_source_reproduction.json')
    native_match(reproduction, 'Source reproduction')
    require(reproduction.get('status') == 'PASS' and reproduction.get('native_file_unchanged') is True and
            reproduction.get('instances') == len(native_links) and reproduction.get('part_numbers_match') is True and
            reproduction.get('source_partdesign_bodies') == native_bodies, 'Source reproduction failed/counts stale')
    check_geometry(reproduction['comparison'], len(native_links), 'Source reproduction')
    require({r['native_label'] for r in reproduction['comparison']['one_to_one_placed_solids']} == native_links,
            'Source reproduction physical identity ledger incomplete')

    capture = evidence('reports/views/r10_capture_manifest.json')
    native_match(capture, 'Image capture review')
    require(capture.get('revision') == 'r10' and capture.get('status') == 'PASS_CAPTURED_RESTORED' and
            capture.get('visual_review') == 'PASS', 'Image capture visual review incomplete')
    require(capture.get('captures'), 'No reviewed image captures')
    for record in capture['captures']:
        add(record['path'], record['sha256'])
    fidelity = evidence('reports/reviews/r10_source_fidelity.json')
    require(fidelity.get('revision') == 'r10' and
            bool(fidelity.get('disposition')) and
            not fidelity.get('required_morphology_corrections'), 'Principal source-fidelity correction not accepted')
    fidelity_hashes = fidelity.get('artifacts_sha256', {})
    required_fidelity = {'cad/flexor_r10_robot.FCStd', 'src/spine_frame_r10.py', 'src/torso_attachment_r10.py',
                         'src/spine_bar_profile_r10.py', 'src/central_joint_hardware_r10.py', 'docs/21_reference_fidelity_r10.md',
                         'parameters/assembly_r10.json'}
    require(required_fidelity <= set(fidelity_hashes), 'Source-fidelity native/source/parameter evidence incomplete')
    require(any(k.startswith('reports/views/r10_') for k in fidelity_hashes), 'Source-fidelity image evidence missing')
    require(fidelity_hashes['cad/flexor_r10_robot.FCStd'] == FROZEN_NATIVE_SHA256, 'Source-fidelity native SHA stale')
    for value, sha in fidelity_hashes.items():
        add(value, sha)
    for value in fidelity.get('source_evidence', []):
        candidate = Path(value)
        candidate = (ROOT / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        # External clipboard files remain recorded provenance in fidelity JSON;
        # only existing repository source images are delivery artifacts.
        if candidate.is_relative_to(ROOT.resolve()) and candidate.is_file():
            add(candidate)

    preview_evidence = validate_native_preview(evidence, add, len(native_links))

    ax_evidence = validate_ax01(evidence, add, FROZEN_NATIVE_SHA256, native_links, native_xml)
    require(ax_evidence['source_definitions'] == len(export_sources), 'AX/export/native source definition counts disagree')

    mass = evidence('reports/verification/r10_mass_envelope.json')
    engineering = evidence('reports/verification/r10_engineering_screen.json')
    require(mass.get('revision') == 'r10' and mass.get('status') == 'COMPUTED_FROM_DOCUMENT' and
            mass.get('instance_count') == len(native_links) and mass.get('part_number_count') == len(bom_rows), 'Mass/BOM counts or calculation incomplete')
    require(engineering.get('native_document') == str(native) and engineering.get('physical_link_count') == len(native_links),
            'Engineering screen source/count mismatch')
    for record, name in ((mass, 'Mass'), (engineering, 'Engineering')):
        native_match(record, name)
    require(math.isclose(mass['known_mass_sum_g'], engineering['known_mass']['mass_g'], rel_tol=1e-10), 'Mass reports disagree')
    require(mass['unknown_mass_instance_count'] == len(mass['unknown_mass_instances']), 'Unknown mass count mismatch')
    for name in ('neutral', 'actuators', 'native_edit_restore', 'native_geometry_report'):
        record = evidence('reports/verification/r10_' + name + '.json')
        native_match(record, name)
        require(str(record.get('status', '')).startswith('PASS'), name + ' verification incomplete')

    manufacture = evidence('reports/reviews/r10_manufacturability.json')
    native_match(manufacture, 'Manufacturability review')
    require(manufacture.get('revision') == 'r10' and manufacture.get('status') == 'PASS_CANDIDATE_WITH_RELEASE_BLOCKERS' and
            manufacture.get('fabrication_release') == 'BLOCKED' and manufacture.get('release_blockers') and
            manufacture.get('reviewed_files'), 'Manufacturability candidate review incomplete')
    manufacturing_files = {r['path']: r['sha256'] for r in manufacture['reviewed_files']}
    require({'cad/flexor_r10_robot.FCStd','reports/package_manifest_r10.json','drawings/r10/drawing_manifest_r10.json',
             'exports/profiles/r10/profile_manifest_r10.json'} <= set(manufacturing_files), 'Manufacturability artifact coverage incomplete')
    for value, sha in manufacturing_files.items():
        add(value, sha)

    pdf_review = evidence('reports/reviews/r10_pdf_visual_review.json')
    native_match(pdf_review, 'PDF visual review')
    require(pdf_review.get('status') == 'PASS', 'PDF visual review incomplete')
    reviewed_pdfs = {r['path']: r for r in pdf_review['documents']}
    pdf_counts = {}
    for value in ('docs/flexor_r10_assembly_calibration.pdf', 'drawings/flexor_r10_drawing_book.pdf'):
        require(value in reviewed_pdfs, 'Missing final PDF visual review: ' + value)
        record = reviewed_pdfs[value]
        p = add(value, record['sha256'])
        pages = page_count(p)
        require(record.get('visual_review') == 'PASS' and record.get('page_count') == pages and pages > 0,
                'PDF hash/page/visual acceptance mismatch: ' + value)
        pdf_counts[value] = pages
    require(pdf_counts['drawings/flexor_r10_drawing_book.pdf'] == len(sheets), 'Drawing book page count mismatch')

    # Reproducible source may intentionally include historical dependency module
    # names. Old generated CAD/report/export assets are never globbed in.
    for pattern in ('src/*.py', 'src/*.cpp', 'tests/*.py', 'macros/*.FCMacro', 'parameters/*.json', 'docs/*.md'):
        for p in ROOT.glob(pattern):
            add(p)
    for value in ('README.md', 'AGENTS.md', '.gitattributes', 'macros/Rebuild_r10.FCMacro'):
        add(value)
    for value in ('reports/reviews/r10_delivery_adapter.md',):
        add(value)

    review_path = path('reports/reviews/r10_final_review.json')
    review = read(review_path)
    native_match(review, 'Final independent review')
    require(review.get('status') == 'PASS_CANDIDATE_WITH_RELEASE_BLOCKERS' and
            review.get('independent_review') is True, 'Final independent review incomplete')
    reviewed = {path(r['path']): r['sha256'] for r in review['reviewed_files']}
    critical_names = (
        'cad/flexor_r10_robot.FCStd', 'cad/flexor_r10_drawings.FCStd',
        'drawings/flexor_r10_drawing_book.pdf', 'docs/flexor_r10_assembly_calibration.pdf',
        'reports/package_manifest_r10.json',
        'reports/verification/r10_changed_partitions/summary.json',
        'reports/verification/r10_changed_partitions/identity.json',
        'reports/verification/r10_changed_partitions/freeze.json',
        'reports/verification/r08_motion_partitions/full_summary.json',
        'exports/profiles/r10/profile_manifest_r10.json',
        'reports/verification/r10_source_reproduction.json',
        'reports/verification/r10_native_checks.json',
        'bom/bom_r10.csv', 'bom/instances_r10.csv',
        'reports/verification/r10_mass_envelope.json',
        'reports/verification/r10_engineering_screen.json',
        'reports/views/r10_capture_manifest.json',
        'reports/reviews/r10_source_fidelity.json',
        'reports/animation/ax01_r10.json', 'animation/motion/ax01_r10.json',
        'animation/schema/grounded_instances_r10.json', 'animation/schema/pose_manifest_v1.schema.json',
        'src/animation_pose_export.py', 'src/animation_manifest_validate.py',
        'reports/reviews/r10_manufacturability.json', 'reports/motion/r10/capture_manifest.json',
        'src/package_delivery_r10.py', 'src/manual_pdf_r10.py', 'src/build_robot_r10.py', 'src/spine_frame_r10.py', 'src/torso_attachment_r10.py',
        'src/spine_bar_profile_r10.py', 'src/central_joint_hardware_r10.py', 'src/verify_changed_revision_r10.py',
        'reports/verification/r10_changed_partitions/whole_cycle_y.json', 'parameters/assembly_r10.json', 'macros/Rebuild_r10.FCMacro',
        'reports/reviews/r10_pdf_visual_review.json',
        'drawings/r10/drawing_manifest_r10.json')
    critical = {path(value) for value in critical_names}
    require(critical <= set(reviewed), 'Final independent review does not cover complete critical package')
    for p in critical:
        require(reviewed[p] == digest(p), 'Artifact changed after final independent review: ' + str(p))
    add(review_path)
    for p, sha in file_hashes.items():
        require(digest(p) == sha, 'Artifact changed during delivery validation: ' + str(p))
    records = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(files)]
    output = {'status': 'CAD_PACKAGE_VERIFIED', 'revision': 'r10', 'native_sha256': FROZEN_NATIVE_SHA256,
              'physical_instances': len(native_links), 'native_custom_bodies': native_bodies, 'source_definitions': len(export_sources), 'frame_native_features': len(frame_features), 'bom_part_numbers': len(bom_rows),
              'drawing_sheets': len(sheets), 'native_dimensions': dimensions,
              'inherited_r08_full_motion_samples': 985, 'r10_changed_pair_samples': 1346, 'r10_affected_pairs': 9996,
              'motion_acceptance': motion_evidence, 'animation_AX0_AX1': ax_evidence, 'native_visual_preview': preview_evidence,
              'AX2_AX4': 'NOT_RUN', 'Blender': 'NOT_RUN', 'pdf_page_counts': pdf_counts,
              'mass_summary': {k: mass[k] for k in ('known_mass_sum_g', 'known_purchased_mass_g',
                  'all_geometry_mass_estimate_g', 'unknown_mass_instance_count', 'unknown_mass_instances',
                  'actual_assembled_bbox_mm', 'reference_envelope_mm', 'actual_minus_reference_mm', 'mass_limitations')},
              'engineering_summary': {k: engineering[k] for k in ('known_mass', 'assumed_loaded_sensitivity', 'separate_assumptions', 'limitations')},
              'scope': 'Reviewable editable CAD candidate; exact finite sample coverage only',
              'fabrication_release': 'BLOCKED', 'physical_validation': 'NOT_RUN', 'continuous_clearance': 'NOT_RUN',
              'file_count': len(records), 'files': records,
              'inventory_limit': 'Only accepted r10 generated artifacts and reproducible source/tests/docs/parameters; no failed diagnostic, transient, historical generated asset or self hash.'}
    require(digest(native) == FROZEN_NATIVE_SHA256, 'Canonical changed during delivery validation')
    if not write_inventory:
        return output
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return target


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-sha256', required=True)
    parser.add_argument('--read-only', action='store_true')
    args = parser.parse_args()
    print(run(write_inventory=not args.read_only, expected_native_sha256=args.native_sha256))
