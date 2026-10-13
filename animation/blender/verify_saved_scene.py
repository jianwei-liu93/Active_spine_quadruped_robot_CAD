"""Fresh-process checks of immutable .blend playback vs CAD pose manifest."""
import bpy,sys,json,gzip,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
kind=sys.argv[sys.argv.index('--')+1];scene=bpy.data.scenes[kind];bpy.context.window.scene=scene
manifest=json.loads((ROOT/scene.get('source_manifest','animation/motion/production_r10.json')).read_text())
objects={o['instance_id']:o for o in scene.objects if 'instance_id' in o};assert set(objects)==set(manifest['instance_order'])
frames={};timeline='active_spine_mechanism' if kind=='active_spine_mechanism' else 'coordinated_spine_legs'
if kind!='exploded_assembly':
 with gzip.open(ROOT/manifest['production']['timelines'][timeline]['path'],'rt') as stream:
  for i,line in enumerate(stream):
   if i in {0,1,74,149,299,300,scene.frame_end-1}:frames[i+1]=json.loads(line)
else:frames={1:manifest['frames'][0],720:manifest['frames'][0]}
meshes={m['mesh_id']:json.loads((ROOT/m['path']).read_text()) for m in manifest['meshes'] if m['asset_status']=='EXPORTED'}
maxpoint=maxaxis=0.;samples=0;changed=set();first=None
for frame,sample in frames.items():
 scene.frame_set(frame);bpy.context.view_layer.update();current={}
 for i,item in enumerate(manifest['instances']):
  obj=objects[item['instance_id']];M=sample['transforms_m'][i];current[item['instance_id']]=[[float(value) for value in row] for row in obj.matrix_world]
  for col in range(3):
   actual=Vector(obj.matrix_world[r][col] for r in range(3));expected=Vector(M[r][col] for r in range(3));maxaxis=max(maxaxis,math.atan2(actual.cross(expected).length,actual.dot(expected)))
  if item['geometry_kind']=='rigid':
   raw=meshes[item['mesh_id']]
   for v in raw['vertices_m'][::max(1,len(raw['vertices_m'])//12)]:
    actual=obj.matrix_world@Vector(v);expected=Matrix(M)@Vector(v)
    maxpoint=max(maxpoint,(actual-expected).length*1000);samples+=1
  else:
   assert len(obj.data.shape_keys.key_blocks)==301 if kind!='exploded_assembly' else obj.data.shape_keys is None
   if kind!='exploded_assembly':assert abs(obj.data.shape_keys.eval_time-10*((frame-1)%300+1))<1e-4
  if first and any(abs(obj.matrix_world[r][c]-first[item['instance_id']][r][c])>1e-7 for r in range(4) for c in range(4)):changed.add(item['instance_id'])
 if first is None:first=current
assert maxpoint<=.02 and maxaxis<=1e-4
if kind!='exploded_assembly':
 expected_changed={manifest['instance_order'][i] for i in range(len(objects)) if any(max(abs(sample['transforms_m'][i][r][c]-frames[1]['transforms_m'][i][r][c]) for r in range(4) for c in range(4))>1e-5 for sample in frames.values())}
 assert expected_changed<=changed and len(changed)>100, (len(expected_changed),len(changed),expected_changed-changed)
report={'status':'PASS','scene':kind,'blender':bpy.app.version_string,'reopened_in_fresh_process':True,'physical_instances':len(objects),'frames_checked':list(frames),'selected_world_vertex_checks':samples,'max_imported_world_vertex_error_mm':maxpoint,'max_axis_angle_error_rad':maxaxis,'changing_physical_instances_observed':len(changed),'procedural_shape_keys_per_instance':301 if kind!='exploded_assembly' else 0,'handlers_needed':False,'freecad_needed':False,'blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()}
(ROOT/'reports/animation'/(kind+'_readback.json')).write_text(json.dumps(report,indent=2)+'\n');print('SCENE_READBACK_PASS',json.dumps(report))
