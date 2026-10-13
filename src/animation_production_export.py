"""Read-only AX2 geometry/timeline handoff extending the existing AX01 schema.

Run inside the connected FreeCAD interpreter (lead only):
    import animation_production_export as export
    report = export.run(App.ActiveDocument)

The descriptor is evaluated at EVERY 60fps sample; no BRep regeneration occurs
in the timeline loop. gzip JSONL bounds memory to one frame. Endpoint samples
are diagnostic and excluded from the 900/1200 rendered frames. Optional native
procedural examples are a separate, potentially slow bounded operation.
"""
from pathlib import Path
import gzip
import json
import math
import time
from animation_pose_export import ROOT, TAGS, COMMANDS, digest, serial, matrix, shape_hash, snapshot, _spring_record, _cable_record
from animation_production_validate import validate_frame, validate


SOURCE_MODULES = ('animation_pose_export.py','animation_manifest_validate.py',
                  'animation_production_export.py','animation_production_validate.py',
                  'robot_pose_r03.py','leg_motion_r07.py','kinematics.py','verify_motion_package_r07.py',
                  'leg_geometry_r02.py','tendon_r03.py','leg_mechanics.py',
                  'spring_wire_r03.py','compression_spring_r07.py',
                  'spring_normalization_r07.py','build_tendon_r03.py','cable_clamps_r07.py')


def trajectory(name, t, neutral):
    """Versioned illustrative state, deliberately not a loaded gait solution."""
    phase = math.tau*.2*t
    if name == 'active_spine_mechanism':
        return phase, {tag:list(q) for tag,q in neutral.items()}, 0.
    # Reuse accepted combined_spine_gait inputs exactly, including the existing
    # hind knee phase convention. This is prescribed geometry, not loaded gait.
    signal = math.sin(phase)
    angles = {tag:[q[0]+math.radians(5)*signal,
                   q[1]+math.radians(5)*math.sin(phase+(math.pi if tag.startswith('hind') else 0))]
              for tag,q in neutral.items()}
    wheel = math.radians(45+45*signal)
    return phase, angles, wheel


def trajectory_regression(neutral):
    """Pure offline comparison with every accepted full integer-phase sample."""
    from verify_motion_package_r07 import manifest
    accepted=manifest('full')
    rows=[r for r in accepted['states'] if r['trajectory']=='combined_spine_gait']
    assert len(rows)==361
    worst=0.
    for row in rows:
        theta,angles,wheel=trajectory('coordinated_spine_legs',row['theta']/(math.tau*.2),neutral)
        worst=max(worst,abs(theta-row['theta']),abs(wheel-row['wheel_angle']),
                  *(abs(a-b) for tag in TAGS for a,b in zip(angles[tag],row['leg_angles'][tag])))
    assert worst<=1e-12, 'Accepted combined_spine_gait input drift'
    return {'status':'PASS','accepted_trajectory':'combined_spine_gait',
            'accepted_manifest_source':'src/verify_motion_package_r07.py:manifest(full)',
            'accepted_manifest_sha256':accepted['sha256'],'integer_phase_samples':len(rows),
            'max_input_error_rad':worst,'tolerance_rad':1e-12,
            'scope':'Input equivalence only; no new clearance campaign or loaded gait claim'}


def _frame(doc, name, i, fps, neutral, effective, order, previous, config):
    import leg_motion_r07 as motion
    import robot_pose_r03 as pose
    from kinematics import spine, residuals
    t = i/fps
    theta, angles, wheel = trajectory(name,t,neutral)
    plan = motion.descriptor(doc,theta,angles,wheel,config=config)
    assert set(plan['placements']) == {iid.removeprefix('instance:') for iid in order}
    frame_id = name+':'+str(i)
    mm=[]; metres=[]; quats=[]; procedural=[]
    for j,iid in enumerate(order):
        objname = iid.removeprefix('instance:')
        placement = plan['placements'][objname]
        M = matrix(placement); B = [r[:] for r in M]
        for r in range(3):B[r][3] *= .001
        mm.append(M);metres.append(B)
        x,y,z,w = placement.Rotation.Q
        q=[w,x,y,z]; norm=math.sqrt(sum(v*v for v in q)); q=[v/norm for v in q]
        if previous and sum(a*b for a,b in zip(q,previous['quaternions_wxyz'][j]))<0:q=[-v for v in q]
        quats.append(q)
        m = effective[objname]
        if m['kind']=='leg_r02_spring':
            row=_spring_record(doc,objname,m,plan,frame_id)
            row.update(wire_diameter_mm=.5,coil_radius_mm=1.75,
                       active_turns=12 if m['spring']=='compression' else round((row['free_length_mm']-4)/.5),
                       end_geometry='closed seat rings' if m['spring']=='compression' else 'native closed eyes and outward hooks',
                       local_shape_status='NOT_REGENERATED; downstream procedural geometry')
        elif m['kind']=='tendon_r03_cable':
            row=_cable_record(objname,m,plan,frame_id)
            row.update(wire_diameter_mm=.3,slack_display_policy='schematic routing guide when state is slack; no solved slack shape',
                       local_shape_status='NOT_REGENERATED; downstream route curves')
        else:continue
        row['shape_parameters_sha256']=digest(serial(plan['shape_requests'].get(objname,row)))
        modules=('build_tendon_r03.py','tendon_r03.py','cable_clamps_r07.py') if row['generator']=='cable' else (row['generator_module']+'.py',)
        row['generator_source_sha256']={module:digest((ROOT/'src'/module).read_bytes()) for module in modules}
        procedural.append(row)
    state = spine(theta,pose._parameters(doc))
    checks={'spine_closure_max_residual_mm':max(abs(v) for v in residuals(state,pose._parameters(doc))),
            'leg_loop_max_residual_mm':max(abs(v) for leg in plan['state']['legs'].values() for v in leg['geometry']['loop_residuals_mm'].values()),
            'spine_min_branch_margin_mm':min(state['margins_mm']),'guide_warnings':plan['guide_warnings']}
    return {'frame_id':frame_id,'time_s':t,'commanded_order':list(COMMANDS),
            'commanded_rad':[theta]+[float(plan['leg_angles_rad'][tag][0]) for tag in TAGS]+[wheel],
            'prescribed_knees_rad':{tag:float(plan['leg_angles_rad'][tag][1]) for tag in TAGS},
            'leg_angles_rad':{tag:list(plan['leg_angles_rad'][tag]) for tag in TAGS},
            'passive_provenance':'PRESCRIBED_KINEMATIC','transforms_mm':mm,'transforms_m':metres,
            'quaternions_wxyz':quats,'procedural_shapes':procedural,'validation':checks,
            'output_angles_rad':{kind:pose.torso_angle(theta,kind,pose._parameters(doc)) for kind in ('fore','hind')}}


def run(doc, output=None):
    """Write source-local meshes, two full sample streams and production manifest."""
    from animation_manifest_validate import load_and_validate
    start=time.monotonic()
    native=Path(doc.FileName).resolve(); revision=native.stem.removeprefix('flexor_').removesuffix('_robot')
    axpath=ROOT/'animation/motion'/('ax01_'+revision+'.json')
    baseline=load_and_validate(axpath)
    audit=json.loads((ROOT/'reports/animation'/('ax01_'+revision+'.json')).read_text())
    assert digest(native.read_bytes()) == baseline['source']['cad_sha256'] == audit['native_sha256']
    assert digest(axpath.read_bytes()) == audit['output_sha256']
    for module,sha in audit['generator_source_sha256'].items():
        assert digest((ROOT/'src'/module).read_bytes()) == sha, 'AX01 source drift: '+module
    before=snapshot(doc)
    source_paths=set(baseline['source']['parameter_files_sha256'])
    source_paths.add('parameters/assembly_r07.json')
    source_paths.update('src/'+module for module in SOURCE_MODULES)
    source_paths.add('animation/schema/grounded_instances_'+revision+'.json')
    source_hashes={p:digest((ROOT/p).read_bytes()) for p in sorted(source_paths)}
    for p,h in baseline['source']['parameter_files_sha256'].items():assert source_hashes[p]==h
    assert digest(doc.PoseController.MotionMap.encode())==baseline['source']['motion_map_sha256']
    links={o.Name:o for o in doc.Objects if o.TypeId=='App::Link'}
    assert {'instance:'+n for n in links}==set(baseline['instance_order'])
    effective={n:row['motion'] for n,row in audit['component_metadata'].items()}
    neutral=baseline['frames'][0]['leg_angles_rad']
    trajectory_check=trajectory_regression(neutral)
    config=json.loads((ROOT/'parameters'/('assembly_'+revision+'.json')).read_text())
    geomdir=ROOT/'animation/geometry'/revision; geomdir.mkdir(parents=True,exist_ok=True)
    meshrows=[]
    rigid_ids={row['mesh_id'] for row in baseline['instances'] if row['geometry_kind']=='rigid'}
    for old in baseline['meshes']:
        mesh_id=old['mesh_id']; src=doc.getObject(mesh_id.removeprefix('mesh:'))
        assert src is not None and src.Placement.isIdentity() and src.Shape.Placement.isIdentity()
        assert shape_hash(src.Shape)==old['geometry_hash']
        row=dict(old)
        if mesh_id not in rigid_ids:
            row.update(asset_status='PROCEDURAL_DOWNSTREAM',local_geometry_status='native reference retained; generator records authoritative')
        else:
            # OCC tessellation attaches triangulation caches to its shape.
            # Never mesh the document-owned source: isolate geometry and caches.
            frozen_hash=shape_hash(src.Shape)
            export_shape=src.Shape.copy()
            vertices,triangles=export_shape.tessellate(.03)
            assert shape_hash(src.Shape)==frozen_hash, 'Tessellation mutated source: '+src.Name
            payload={'schema_version':'1.0','mesh_id':mesh_id,'local_units':'m',
                     'vertices_m':[[float(v.x)*.001,float(v.y)*.001,float(v.z)*.001] for v in vertices],
                     'triangles':[list(t) for t in triangles]}
            assert vertices and triangles
            path=geomdir/(src.Name+'.json');path.write_bytes(serial(payload))
            row.update(path=str(path.relative_to(ROOT)),sha256=digest(path.read_bytes()),local_units='m',
                       asset_status='EXPORTED',local_geometry_status='native source-local tessellation; identity placement',
                       tessellation_tolerance_mm=.03,vertex_count=len(vertices),triangle_count=len(triangles))
        meshrows.append(row)
    for obj in links.values():
        assert not obj.LinkTransform and abs(float(getattr(obj,'Scale',1))-1)<1e-12
    instances={row['instance_id']:row for row in baseline['instances']}
    timelines={}
    for name,duration in (('active_spine_mechanism',15),('coordinated_spine_legs',20)):
        path=ROOT/'animation/motion'/(name+'_'+revision+'.jsonl.gz')
        previous=first=None; worst_anchor=0.
        # mtime=0 makes the gzip container reproducible on unchanged input.
        with path.open('wb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as stream:
                for i in range(duration*60+1):
                    frame=_frame(doc,name,i,60,neutral,effective,baseline['instance_order'],previous,config)
                    worst_anchor=max(worst_anchor,validate_frame(frame,instances,previous))
                    stream.write(serial(frame)+b'\n')
                    if first is None:first=frame
                    previous=frame
                    if i%120==0:print('ANIMATION_SAMPLE',name,i,duration*60,round(time.monotonic()-start,1),flush=True)
        loop=max(abs(a-b) for M,N in zip(first['transforms_mm'],previous['transforms_mm']) for r,s in zip(M,N) for a,b in zip(r,s))
        assert loop<1e-7
        timelines[name]={'path':str(path.relative_to(ROOT)),'sha256':digest(path.read_bytes()),'fps':60,
                         'duration_s':duration,'sample_count':duration*60+1,'render_frame_count':duration*60,
                         'render_first_frame':1,'sample_index_for_render_frame':'frame-1','endpoint_sample':'diagnostic only',
                         'frequency_hz':.2,'cycles':duration*.2,'spine_phase':'unwrapped 2*pi*0.2*t',
                         'loop_matrix_max_error':loop,'anchor_max_error_mm':worst_anchor,
                         'leg_motion':'fixed neutral' if duration==15 else 'accepted combined_spine_gait: all hips +5deg*sin(phi); fore knees +5deg*sin(phi), hind knees +5deg*sin(phi+pi)',
                         'fore_hind_knee_offset_rad':0. if duration==15 else math.pi,
                         'offset_provenance':'Existing prescribed combined_spine_gait; fore/hind knee phase pi; no paper event-delay claim',
                         'wheel_motion':'fixed zero' if duration==15 else 'accepted independent 45+45*sin(2*pi*0.2*t) degrees',
                         'motion_blur':False,'loaded_equilibrium':False,'body_translation':'none; suspended central datum'}
    assert before==snapshot(doc), 'Document mutated'
    assert digest(native.read_bytes())==baseline['source']['cad_sha256']
    data=dict(baseline);data['meshes']=meshrows
    data['production']={'extension_version':'AX2-1','ax01_path':str(axpath.relative_to(ROOT)),
                        'ax01_sha256':digest(axpath.read_bytes()),'source_files_sha256':source_hashes,
                        'component_metadata':audit['component_metadata'],'timelines':timelines,
                        'trajectory_regression':trajectory_check,
                        'static_exploded_pose':'frames[0] neutral_v1; display displacements downstream only',
                        'physical_motors':7,'commanded_coordinates':6,'prescribed_knees':4,
                        'procedural_native_examples':'NOT_RUN; run_native_examples separately',
                        'document_unchanged':True,'native_file_unchanged':True,
                        'limitations':['Prescribed geometry; no loaded gait or clearance claim.','Slack routes are schematic guides, not solved physical slack cable shapes.']}
    out=Path(output) if output else ROOT/'animation/motion'/('production_'+revision+'.json')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(serial(data))
    report=validate(out)
    report.update(elapsed_seconds=time.monotonic()-start,manifest=str(out.relative_to(ROOT)),
                  geometry_directory=str(geomdir.relative_to(ROOT)),document_unchanged=True,native_file_unchanged=True)
    dest=ROOT/'reports/animation'/('production_'+revision+'.json');dest.write_text(json.dumps(report,indent=2)+'\n')
    print('ANIMATION_PRODUCTION_PASS',json.dumps(report),flush=True)
    return report


def run_native_examples(doc, sample_indices=(0,75,150)):
    """Optional bounded examples: regenerate only requested procedural BReps.

    Three samples (maximum) in the coordinated timeline, never whole-robot
    copied shapes. Writes private source-local meshes for downstream comparison.
    Native kernel runtime can be substantial; run separately from run(doc).
    """
    import leg_motion_r07 as motion
    assert 1<=len(sample_indices)<=3 and all(0<=i<=1200 for i in sample_indices)
    before=snapshot(doc);start=time.monotonic()
    native=Path(doc.FileName);revision=native.stem.removeprefix('flexor_').removesuffix('_robot')
    baseline=json.loads((ROOT/'animation/motion'/('ax01_'+revision+'.json')).read_text())
    config=json.loads((ROOT/'parameters'/('assembly_'+revision+'.json')).read_text())
    folder=ROOT/'animation/geometry'/revision/'procedural_examples';folder.mkdir(parents=True,exist_ok=True)
    records=[];cache={}
    for i in sample_indices:
        theta,angles,wheel=trajectory('coordinated_spine_legs',i/60,baseline['frames'][0]['leg_angles_rad'])
        plan=motion.descriptor(doc,theta,angles,wheel,config=config)
        generated=motion.regenerate_sources(plan,cache)
        procedural_names=[r['freecad_object_name'] for r in baseline['instances'] if r['geometry_kind']=='length_route_dependent']
        for name in procedural_names:
            shape=generated.get(name,doc.getObject(name).LinkedObject.Shape)
            frozen_hash=shape_hash(shape)
            vertices,triangles=shape.copy().tessellate(.03)
            assert shape_hash(shape)==frozen_hash, 'Example tessellation mutated native source: '+name
            path=folder/(name+'_'+str(i)+'.json')
            path.write_bytes(serial({'vertices_m':[[v.x*.001,v.y*.001,v.z*.001] for v in vertices],
                                     'triangles':[list(t) for t in triangles],'local_units':'m'}))
            records.append({'instance_id':'instance:'+name,'sample_index':i,'path':str(path.relative_to(ROOT)),
                            'sha256':digest(path.read_bytes()),'local_shape_sha256':shape_hash(shape),
                            'shape_request':plan['shape_requests'].get(name,{'generator':'spring','state':'unchanged native reference'}),'transform_mm':matrix(plan['placements'][name]),
                            'is_valid':shape.isValid(),'solid_count':len(shape.Solids)})
    assert before==snapshot(doc)
    report={'status':'NATIVE_EXAMPLES_EXPORTED; downstream comparison pending','examples':records,
            'elapsed_seconds':time.monotonic()-start,'document_unchanged':True}
    (folder/'manifest.json').write_bytes(serial(report))
    return report
