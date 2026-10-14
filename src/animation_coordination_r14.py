"""Read-only r14 geometry and paper-informed coordination handoff.

The lead runs ``run(App.ActiveDocument)`` inside connected FreeCAD. Reuses the
frozen v2 trajectory and AX2 frame/procedural serializers without changing their
files. Exports only the 20-second coordination timeline; no native pose, source
geometry, parameters, old motion package, or canonical file is written.
"""
from pathlib import Path
import gzip
import json
import math
import time
from zipfile import ZipFile
from xml.etree import ElementTree

import animation_production_export as base
import animation_coordination_v2 as coordination
from animation_pose_export import ROOT, digest, serial, shape_hash, snapshot
from animation_manifest_validate import load_and_validate
from animation_production_validate import validate_frame, validate


REVISION = 'r14'
NATIVE_SHA256 = '7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87'
NAME = 'coordinated_spine_legs'
FPS = 60
DURATION = 20
CANONICAL = ROOT/'cad/flexor_r14_robot.FCStd'
DISPOSABLE = ROOT/'reports/tmp/r14_animation/flexor_r14_robot.FCStd'


def _source_identity(doc, baseline):
    """Compare all sources to saved canonical BReps with strict native gates.

    Raw export hashes are recorded separately from geometric acceptance. Both
    comparison operands have private geometry and no display triangulation.
    The original AX01 serialization hashes remain untouched.
    """
    import Part
    from verify_frame_revision_r09 import _strict_shape_identity
    assert digest(CANONICAL.read_bytes()) == NATIVE_SHA256
    records = {}
    with ZipFile(CANONICAL) as archive:
        xml = ElementTree.fromstring(archive.read('Document.xml'))
        objects = {o.attrib['name']:o for o in xml.findall('./ObjectData/Object')}
        for i, row in enumerate(baseline['meshes']):
            name = row['mesh_id'].removeprefix('mesh:')
            entry = objects[name].find("./Properties/Property[@name='Shape']/Part")
            assert entry is not None and entry.attrib['file'], 'Missing saved BRep: '+name
            brep = archive.read(entry.attrib['file'])
            saved = Part.Shape()
            saved.importBrepFromString(brep.decode('utf-8'))
            assert saved.Placement.isIdentity(), 'Saved source is not source-local: '+name
            current = doc.getObject(name).Shape
            current_sha = shape_hash(current)
            saved_sha = shape_hash(saved)
            proof = _strict_shape_identity(
                saved.copy(copyGeom=True,copyMesh=False),
                current.copy(copyGeom=True,copyMesh=False),name+' canonical saved/current')
            assert shape_hash(current) == current_sha, 'Identity check mutated source: '+name
            records[row['mesh_id']] = {
                'source_object_name':name,'ax01_geometry_hash':row['geometry_hash'],
                'current_native_geometry_sha256':current_sha,
                'canonical_saved_geometry_sha256':saved_sha,
                'canonical_saved_brep_entry':entry.attrib['file'],
                'canonical_saved_brep_sha256':digest(brep),
                'raw_serialization_differs_from_ax01':current_sha != row['geometry_hash'],
                'comparison_geometry':'Both operands copyGeom=True/copyMesh=False; strict gates unchanged',
                'strict_identity':proof}
            if (i+1) % 12 == 0:
                print('COORDINATION_R14_SOURCE_IDENTITY',i+1,len(baseline['meshes']),flush=True)
    assert len(records) == 108
    assert digest(CANONICAL.read_bytes()) == NATIVE_SHA256
    return {'status':'PASS','canonical_cad_path':str(CANONICAL.relative_to(ROOT)),
            'canonical_cad_sha256':NATIVE_SHA256,'sources_compared':len(records),
            'raw_serialization_drift_source_count':sum(r['raw_serialization_differs_from_ax01'] for r in records.values()),
            'raw_serialization_drift_interpretation':'Observed serialization differences; no cause inferred. Acceptance requires strict saved/current native geometry identity.',
            'sources':records}


def _inputs(doc):
    """Fail closed on revision, source, instance, grounding or AX01 drift."""
    native = Path(doc.FileName).resolve()
    assert native in (CANONICAL.resolve(),DISPOSABLE.resolve()), 'Expected canonical r14 or fixed disposable copy'
    axpath = ROOT/'animation/motion/ax01_r14.json'
    auditpath = ROOT/'reports/animation/ax01_r14.json'
    baseline = load_and_validate(axpath)
    audit = json.loads(auditpath.read_text())
    assert audit['AX0'] == audit['AX1'] == 'PASS'
    assert baseline['source']['cad_revision'] == audit['cad_revision'] == REVISION
    assert baseline['source']['cad_path'] == str(CANONICAL.relative_to(ROOT))
    assert digest(native.read_bytes()) == digest(CANONICAL.read_bytes()) == baseline['source']['cad_sha256'] == audit['native_sha256'] == NATIVE_SHA256
    assert digest(axpath.read_bytes()) == audit['output_sha256']
    assert digest((ROOT/'src/animation_pose_export.py').read_bytes()) == audit['exporter_source_sha256']
    for module, sha in audit['generator_source_sha256'].items():
        assert digest((ROOT/'src'/module).read_bytes()) == sha, 'AX01 source drift: '+module
    grounding_path = ROOT/'animation/schema/grounded_instances_r14.json'
    assert digest(grounding_path.read_bytes()) == audit['grounding_sha256']
    grounding = json.loads(grounding_path.read_text())
    assert grounding['cad_sha256'] == NATIVE_SHA256
    original_motion = json.loads(doc.PoseController.MotionMap)
    assert original_motion == audit['authoritative_motion_map']
    assert digest(doc.PoseController.MotionMap.encode()) == baseline['source']['motion_map_sha256']
    links = {o.Name:o for o in doc.Objects if o.TypeId == 'App::Link'}
    assert len(links) == len(baseline['instances']) == audit['physical_instances'] == 455
    assert len(baseline['meshes']) == audit['source_definitions'] == 108
    assert set(links) == {row['freecad_object_name'] for row in baseline['instances']}
    assert {'instance:'+n for n in links} == set(baseline['instance_order'])
    absent = sorted(set(links)-set(original_motion))
    assert absent == grounding['grounded_names'] == audit['reviewed_explicit_grounded_instances']
    effective = {n:row['motion'] for n,row in audit['component_metadata'].items()}
    assert set(effective) == set(links)
    expected = dict(original_motion)
    expected.update({n:{'kind':'fixed','grounding':'reviewed lumbar datum'} for n in absent})
    assert effective == expected, 'Effective motion metadata differs from reviewed grounding'
    meshes = {row['mesh_id']:row for row in baseline['meshes']}
    for row in baseline['instances']:
        obj = links[row['freecad_object_name']]
        src = obj.LinkedObject
        assert src.Name == row['source_object_name']
        assert row['mesh_id'] == 'mesh:'+src.Name
        assert str(src.PartNumber) == row['part_number']
        assert row['motion_kind'] == effective[obj.Name]['kind']
        assert not obj.LinkTransform and abs(float(getattr(obj,'Scale',1))-1) < 1e-12
        assert src.Placement.isIdentity() and src.Shape.Placement.isIdentity()
        assert meshes[row['mesh_id']]['local_units'] == 'mm'
    paths = set(baseline['source']['parameter_files_sha256'])
    paths.update('src/'+module for module in base.SOURCE_MODULES)
    paths.update('src/'+module for module in audit['generator_source_sha256'])
    paths.update(('src/animation_coordination_r14.py','src/animation_coordination_v2.py',
                  'src/verify_frame_revision_r09.py','src/adaptive_volume_r07.py',
                  'src/occt_adaptive_volume_r07.cpp',
                  'parameters/assembly_r07.json',str(coordination.PROFILE_PATH.relative_to(ROOT)),
                  str(grounding_path.relative_to(ROOT)),str(axpath.relative_to(ROOT)),
                  str(auditpath.relative_to(ROOT))))
    hashes = {p:digest((ROOT/p).read_bytes()) for p in sorted(paths)}
    for p, sha in baseline['source']['parameter_files_sha256'].items():
        assert hashes[p] == sha, 'AX01 parameter drift: '+p
    assert json.loads(coordination.PROFILE_PATH.read_text()) == coordination.PROFILE, 'Imported profile is stale'
    assert coordination.PROFILE['loaded_dynamics'] is False
    assert coordination.PROFILE['presentation_frequency_hz'] == .2
    config = json.loads((ROOT/'parameters/assembly_r14.json').read_text())
    return native, axpath, baseline, audit, effective, config, hashes


def _geometry(doc, baseline, folder, identity):
    """Tessellate private copies; shared native shapes keep their BRep hashes."""
    folder.mkdir(parents=True, exist_ok=True)
    rigid_ids = {row['mesh_id'] for row in baseline['instances'] if row['geometry_kind'] == 'rigid'}
    rows = []
    for old in baseline['meshes']:
        row = dict(old)
        src = doc.getObject(row['mesh_id'].removeprefix('mesh:'))
        assert src is not None and src.Placement.isIdentity() and src.Shape.Placement.isIdentity()
        frozen_hash = shape_hash(src.Shape)
        proof = identity['sources'][row['mesh_id']]
        assert frozen_hash == proof['current_native_geometry_sha256']
        row.update(proof)
        if row['mesh_id'] not in rigid_ids:
            row.update(asset_status='PROCEDURAL_DOWNSTREAM',
                       local_geometry_status='native reference retained; per-frame generator records authoritative')
        else:
            vertices, triangles = src.Shape.copy(copyGeom=True,copyMesh=False).tessellate(.03)
            assert shape_hash(src.Shape) == frozen_hash, 'Tessellation mutated source: '+src.Name
            assert vertices and triangles
            payload = {'schema_version':'1.0','mesh_id':row['mesh_id'],'local_units':'m',
                       'vertices_m':[[float(v.x)*.001,float(v.y)*.001,float(v.z)*.001] for v in vertices],
                       'triangles':[list(t) for t in triangles]}
            path = folder/(src.Name+'.json')
            path.write_bytes(serial(payload))
            row.update(path=str(path.relative_to(ROOT)),sha256=digest(path.read_bytes()),local_units='m',
                       asset_status='EXPORTED',tessellation_tolerance_mm=.03,
                       local_geometry_status='native source-local tessellation; identity placement',
                       vertex_count=len(vertices),triangle_count=len(triangles))
        rows.append(row)
    return rows


def run(doc):
    """Export r14 source-local assets and one 1201-sample coordination stream."""
    start = time.monotonic()
    native, axpath, baseline, audit, effective, config, hashes = _inputs(doc)
    before = snapshot(doc)
    before_sha = digest(serial(before))
    identity = _source_identity(doc,baseline)
    assert digest(serial(snapshot(doc))) == before_sha, 'Source identity check mutated document'
    geomdir = ROOT/'animation/geometry/r14'
    meshrows = _geometry(doc, baseline, geomdir, identity)
    order = baseline['instance_order']
    instances = {row['instance_id']:row for row in baseline['instances']}
    assert list(instances) == order
    neutral = baseline['frames'][0]['leg_angles_rad']
    path = ROOT/'animation/motion/coordinated_spine_legs_r14.jsonl.gz'
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = first = None
    worst_anchor = 0.
    original_trajectory = base.trajectory
    # _frame has one trajectory callback. Scope the same v2 override to this
    # exclusive lead-only export and restore both overrides on all exit paths.
    base.trajectory = coordination.trajectory
    try:
        with coordination.paper_descriptor_context():
            with path.open('wb') as raw:
                with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as stream:
                    for i in range(DURATION*FPS+1):
                        frame = base._frame(doc,NAME,i,FPS,neutral,effective,order,previous,config)
                        worst_anchor = max(worst_anchor,validate_frame(frame,instances,previous))
                        stream.write(serial(frame)+b'\n')
                        if first is None:
                            first = frame
                        previous = frame
                        if i % 120 == 0:
                            print('COORDINATION_R14_SAMPLE',i,DURATION*FPS,round(time.monotonic()-start,1),flush=True)
    finally:
        base.trajectory = original_trajectory
    loop = max(abs(a-b) for M,N in zip(first['transforms_mm'],previous['transforms_mm'])
               for r,s in zip(M,N) for a,b in zip(r,s))
    assert loop < 1e-7
    after_sha = digest(serial(snapshot(doc)))
    assert before_sha == after_sha, 'Document mutated'
    assert digest(native.read_bytes()) == NATIVE_SHA256, 'Canonical native file changed'
    assert digest(CANONICAL.read_bytes()) == NATIVE_SHA256, 'Canonical provenance file changed'
    for rel, sha in hashes.items():
        assert digest((ROOT/rel).read_bytes()) == sha, 'Input changed during export: '+rel
    timeline = {'path':str(path.relative_to(ROOT)),'sha256':digest(path.read_bytes()),
                'fps':FPS,'duration_s':DURATION,'sample_count':DURATION*FPS+1,
                'render_frame_count':DURATION*FPS,'render_first_frame':1,
                'sample_index_for_render_frame':'frame-1','endpoint_sample':'diagnostic only',
                'frequency_hz':.2,'cycles':4,'spine_phase':'2*pi*0.2*t + paper profile phase origin',
                'loop_matrix_max_error':loop,'anchor_max_error_mm':worst_anchor,
                'leg_motion':'Existing paper-informed v2: hip +/-0.6rad about assumed CAD means; separately prescribed knees +/-10deg',
                'amplitude_deg':coordination.AMPLITUDE_DEG,
                'hip_full_excursion_deg':coordination.PROFILE['hip_full_excursion_deg'],
                'fore_hind_knee_offset_rad':coordination.PROFILE['fore_phase_offset_rad'],
                'offset_provenance':'Existing v2 profile; hind backswing lag pi/10; fore phase and CAD means are assumptions',
                'wheel_motion':'45+45*cos(cycle-lag) degrees; independent prescribed 0..90 degree take-up',
                'clearance_evidence':'NOT_RUN for r14 coordination trajectory; AX01 covers only its three original poses',
                'motion_blur':False,'loaded_equilibrium':False,'body_translation':'none; suspended central datum'}
    data = dict(baseline)
    data['meshes'] = meshrows
    data['production'] = {
        'extension_version':'AX2-3-coordination-r14','ax01_path':str(axpath.relative_to(ROOT)),
        'ax01_sha256':digest(axpath.read_bytes()),'source_files_sha256':hashes,
        'component_metadata':audit['component_metadata'],'timelines':{NAME:timeline},
        'source_geometry_identity':identity,
        'input_document_path':str(native.relative_to(ROOT)),
        'input_document_is_disposable_copy':native != CANONICAL.resolve(),
        'paper_motion_profile':coordination.PROFILE,
        'trajectory_regression':{'status':'REUSED_PAPER_INFORMED_V2_TRAJECTORY',
                                 'trajectory_source':'src/animation_coordination_v2.py:trajectory',
                                 'prior_full_campaign_reused_for_new_combined_path':False},
        'physical_motors':7,'commanded_coordinates':6,'prescribed_knees':4,
        'procedural_native_examples':'NOT_RUN for r14; per-frame spring/cable records exported',
        'document_unchanged':True,'native_file_unchanged':True,
        'snapshot_before_sha256':before_sha,'snapshot_after_sha256':after_sha,
        'limitations':['Prescribed kinematics; no loaded gait, dynamic locomotion, or r14 coordination clearance claim.',
                       'Slack cable routes are schematic routing guides, not solved slack shapes.',
                       'Paper hip excursion is approximate; CAD means, fore phase and knees remain assumptions.',
                       'Historical native procedural examples and clearance evidence are not r14 validation.']}
    out = ROOT/'animation/motion/production_coordination_r14.json'
    out.write_bytes(serial(data))
    report = validate(out)
    assert digest(serial(snapshot(doc))) == before_sha, 'Document changed during validation'
    assert digest(native.read_bytes()) == NATIVE_SHA256
    assert digest(CANONICAL.read_bytes()) == NATIVE_SHA256
    report.update(elapsed_seconds=time.monotonic()-start,manifest=str(out.relative_to(ROOT)),
                  geometry_directory=str(geomdir.relative_to(ROOT)),native_sha256=NATIVE_SHA256,
                  amplitude_deg=coordination.AMPLITUDE_DEG,
                  hip_full_excursion_deg=coordination.PROFILE['hip_full_excursion_deg'],
                  document_unchanged=True,native_file_unchanged=True,
                  snapshot_before_sha256=before_sha,snapshot_after_sha256=after_sha,
                  source_geometry_identity=identity,
                  input_document_path=str(native.relative_to(ROOT)),
                  input_document_is_disposable_copy=native != CANONICAL.resolve(),
                  clearance='NOT_RUN for r14 coordination trajectory',loaded_equilibrium=False)
    dest = ROOT/'reports/animation/production_coordination_r14.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print('COORDINATION_R14_PASS',json.dumps({k:v for k,v in report.items() if k != 'source_geometry_identity'}),
          'strict_sources',identity['sources_compared'],
          'serialization_drift_sources',identity['raw_serialization_drift_source_count'],flush=True)
    return report
