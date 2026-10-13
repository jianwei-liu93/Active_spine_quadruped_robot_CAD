"""Persistent r10 Blender scenes. Lead executes through installed Blender MCP.

No handlers, drivers, FreeCAD connection, script trust or external assets are
needed for playback. Mechanical samples are baked at every rendered frame.
"""
from pathlib import Path
import json, gzip, math, hashlib, time
import bpy
from mathutils import Matrix, Vector
from procedural_geometry import spring_mesh, cable_mesh
ROOT=Path(__file__).resolve().parents[2]
SCENES=ROOT/'animation/scenes'
REPORTS=ROOT/'reports/animation'


def load_manifest(path='animation/motion/production_r10.json'):
    return json.loads((ROOT/path).read_text())


def linear_keys(data):
    # Blender 5 uses layered action channelbags.
    action=data.animation_data.action if data.animation_data else None
    if not action:return
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'


def material(name,color,metal=0.,rough=.45):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF') or m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Metallic'].default_value=metal;node.inputs['Roughness'].default_value=rough
    if 'text' in name:
        m.node_tree.nodes.clear();em=m.node_tree.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(*color,1);em.inputs[1].default_value=1
        out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
    return m


def materials():
    return {'frame':material('FLEXOR charcoal polymer',(.055,.075,.095)),
            'link':material('FLEXOR light link',(.69,.75,.79),.35,.38),
            'metal':material('FLEXOR satin hardware',(.40,.47,.53),.7,.3),
            'copper':material('FLEXOR guide liner',(.58,.35,.10),.55),
            'board':material('FLEXOR controller',(.04,.21,.27)),
            'accent':material('FLEXOR driver teal',(.025,.38,.43),.3),
            'route':material('FLEXOR schematic cable orange',(.9,.31,.035),.1),
            'ink':material('FLEXOR text',(.025,.055,.075)),
            'muted':material('FLEXOR secondary text',(.07,.12,.16))}


def choose_mat(item,meta,mats):
    n=item['freecad_object_name']; text=(n+' '+item['part_number']).lower()
    mat=meta.get('material','').lower()
    if item['motion_kind']=='tendon_r03_cable':return mats['route']
    if 'controller'==item['group']:return mats['board']
    if 'copper' in mat:return mats['copper']
    if n.startswith('DirectCrank') or 'InputHorn' in n:return mats['accent']
    if n.startswith('Link'):return mats['link']
    if 'pa12' in mat or 'motor' in text or 'torso' in text or 'frame' in text:return mats['frame']
    return mats['metal']


def add_mesh(name,vertices,faces):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    # Preserve sharp CAD boundaries; small curved surfaces have sufficient facets.
    return mesh


def pose_object(obj,M):
    obj.matrix_world=Matrix(M)
    obj.rotation_mode='QUATERNION'


def camera(scene):
    c=bpy.data.cameras.new(scene.name+' camera');o=bpy.data.objects.new(c.name,c)
    scene.collection.objects.link(o);scene.camera=o;c.type='ORTHO';c.lens=50
    c.clip_start=.001;c.clip_end=10
    return o


def point_camera(cam,location,target,scale):
    cam.location=location;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale


def text(scene,cam,body,x,y,size,mat):
    d=bpy.data.curves.new(body[:40],'FONT');d.body=body;d.size=size;d.align_y='CENTER';d.extrude=0
    obj=bpy.data.objects.new(body[:40],d);scene.collection.objects.link(obj)
    obj.parent=cam;obj.location=(x,y,-.003);d.materials.append(mat)
    # Text uses emission for stable contrast under scene lighting.
    return obj


def hud(scene,cam,title,caption,mats,width):
    # Units are metres in camera coordinates, orthographic width fixed per shot.
    text(scene,cam,'FLEXOR  /  '+title,-width*.46,width*.225,width*.022,mats['ink'])
    text(scene,cam,caption,-width*.46,width*.19,width*.012,mats['muted'])
    text(scene,cam,'r10 CAD reconstruction  |  Geometry and kinematics from FreeCAD',-width*.46,-width*.23,width*.011,mats['muted'])


def stage(scene):
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=15
    scene.render.film_transparent=False
    if hasattr(scene.render,'use_motion_blur'):scene.render.use_motion_blur=False
    if hasattr(scene,'eevee'):
        if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    w=bpy.data.worlds.new(scene.name+' studio');scene.world=w;w.use_nodes=True
    w.node_tree.nodes['Background'].inputs[0].default_value=(.80,.85,.90,1)
    w.node_tree.nodes['Background'].inputs[1].default_value=.65
    for idx,(loc,power,size) in enumerate([((.10,-.18,.23),.3,.22),((-.18,-.03,.12),.15,.18),((.02,.17,.18),.4,.14)]):
        d=bpy.data.lights.new(scene.name+' softbox '+str(idx),'AREA');d.energy=power;d.shape='DISK';d.size=size
        o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=loc
        o.rotation_euler=(Vector((0,0,-.01))-o.location).to_track_quat('-Z','Y').to_euler()


def import_robot(scene,data,mats):
    meshes={}
    for row in data['meshes']:
        if row['asset_status']!='EXPORTED':continue
        path=ROOT/row['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        d=json.loads(path.read_text());meshes[row['mesh_id']]=add_mesh(row['mesh_id'],d['vertices_m'],d['triangles'])
    groups={};objects={};neutral=data['frames'][0]
    records={r['instance_id']:r for r in neutral['procedural_shapes']}
    for i,item in enumerate(data['instances']):
        group=item['group'];col=groups.get(group)
        if col is None:
            col=bpy.data.collections.new(scene.name+'/'+group);scene.collection.children.link(col);groups[group]=col
        if item['geometry_kind']=='rigid':mesh=meshes[item['mesh_id']]
        else:
            rec=records[item['instance_id']];v,f=(spring_mesh(rec) if rec['generator']=='spring' else cable_mesh(rec))
            mesh=add_mesh(scene.name+'/'+item['instance_id'],v,f)
        # Mesh data may be shared, object materials are instance-local slots.
        obj=bpy.data.objects.new(item['instance_id'],mesh);col.objects.link(obj)
        obj['instance_id']=item['instance_id'];obj['source_id']=item['source_object_name'];obj['part_number']=item['part_number']
        obj['motion_kind']=item['motion_kind'];obj['geometry_kind']=item['geometry_kind'];obj['group']=group
        obj['cad_sha256']=data['source']['cad_sha256'];obj['world_convention']='X forward Y left Z up; metres'
        meta=data['production']['component_metadata'][item['freecad_object_name']]
        if len(mesh.materials)==0:mesh.materials.append(mats['metal'])
        obj.material_slots[0].link='OBJECT';obj.material_slots[0].material=choose_mat(item,meta,mats)
        pose_object(obj,neutral['transforms_m'][i]);objects[item['instance_id']]=obj
    assert len(objects)==len(data['instance_order'])
    return objects


def read_cycle(data,timeline):
    frames=[]
    with gzip.open(ROOT/data['production']['timelines'][timeline]['path'],'rt') as stream:
        for i,line in enumerate(stream):
            frames.append(json.loads(line))
            if i==300:break
    assert len(frames)==301
    return frames


def bake_channel(data,path,index,values):
    if not data.animation_data:data.animation_data_create()
    if not data.animation_data.action:
        a=bpy.data.actions.new(data.name+' exact sampled motion');data.animation_data.action=a
        slot=a.slots.new(id_type='KEY' if isinstance(data,bpy.types.Key) else 'OBJECT',name=data.name);data.animation_data.action_slot=slot
        layer=a.layers.new('Exact frame samples');strip=layer.strips.new(type='KEYFRAME');strip.channelbag(slot,ensure=True)
    a=data.animation_data.action;bag=a.layers[0].strips[0].channelbag(data.animation_data.action_slot)
    curve=bag.fcurves.new(data_path=path,index=index);curve.keyframe_points.add(len(values))
    curve.keyframe_points.foreach_set('co',[x for f,v in enumerate(values,1) for x in (f,v)])
    for k in curve.keyframe_points:k.interpolation='LINEAR'
    curve.update()


def bake_mechanics(scene,data,objects,frames,count):
    start=time.monotonic();order=data['instance_order']
    # 5 s cycle is exact; retain all rigid transforms for every rendered time.
    for i,iid in enumerate(order):
        obj=objects[iid];obj.rotation_mode='QUATERNION'
        for axis in range(3):
            bake_channel(obj,'location',axis,[frames[(f-1)%300]['transforms_m'][i][axis][3] for f in range(1,count+1)])
        continuous_quaternions=[]
        for f in range(1,count+1):
            q=list(frames[(f-1)%300]['quaternions_wxyz'][i])
            if continuous_quaternions and sum(a*b for a,b in zip(q,continuous_quaternions[-1]))<0:q=[-x for x in q]
            continuous_quaternions.append(q)
        for axis in range(4):
            bake_channel(obj,'rotation_quaternion',axis,[q[axis] for q in continuous_quaternions])
    # Absolute shape keys bake each source-local procedural pose. One full
    # 300-sample cycle is reused; no transient handlers are needed on reopen.
    for iid in [i['instance_id'] for i in data['instances'] if i['geometry_kind']!='rigid']:
        obj=objects[iid];obj.shape_key_add(name='Basis');keys=obj.data.shape_keys;keys.use_relative=False
        for k,frame in enumerate(frames[:300]):
            row=next(r for r in frame['procedural_shapes'] if r['instance_id']==iid)
            verts,faces=spring_mesh(row) if row['generator']=='spring' else cable_mesh(row)
            assert len(verts)==len(obj.data.vertices) and len(faces)==len(obj.data.polygons)
            key=obj.shape_key_add(name='Exact sampled pose '+str(k));key.interpolation='KEY_LINEAR'
            key.data.foreach_set('co',[c for v in verts for c in v])
        for f in range(1,count+1):
            keys.eval_time=10*((f-1)%300+1);keys.keyframe_insert('eval_time',frame=f)
        linear_keys(keys)
        obj['procedural_policy']='native generator centerlines; fixed wire diameter; baked source-local shape keys'
        if 'Cable' in iid:obj['representation']='schematic dashed routing guide; physical slack shape unresolved'
    print('MECHANICS_BAKED',scene.name,count,round(time.monotonic()-start,1))


def visibility(obj,values):
    for frame,visible in values:
        obj.hide_render=not visible;obj.keyframe_insert('hide_render',frame=frame)
    action=obj.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    if curve.data_path=='hide_render':
                        for k in curve.keyframe_points:k.interpolation='CONSTANT'


def save_scene(scene):
    scene.frame_set(1);SCENES.mkdir(parents=True,exist_ok=True)
    path=SCENES/(scene.name+'.blend')
    bpy.data.libraries.write(str(path),{scene},fake_user=True,compress=True)
    return str(path.relative_to(ROOT))


def build(kind,manifest_path='animation/motion/production_r10.json'):
    data=load_manifest(manifest_path);mats=materials()
    if kind in bpy.data.scenes:
        old=bpy.data.scenes[kind];assert old.get('source_manifest','').startswith('animation/motion/production')
        bpy.data.scenes.remove(old)
    scene=bpy.data.scenes.new(kind)
    bpy.context.window.scene=scene;stage(scene);cam=camera(scene);objects=import_robot(scene,data,mats)
    scene['source_manifest']=manifest_path;scene['source_cad_sha256']=data['source']['cad_sha256']
    scene['motion_provenance']='PRESCRIBED_KINEMATIC; no passive loads simulated';scene['motion_blur']=False
    scene['physical_instances']=len(objects);scene.frame_start=1
    if kind=='exploded_assembly':
        scene.render.fps=30;scene.frame_end=720;width=.43
        point_camera(cam,(.25,-.38,.20),(0,0,-.008),width)
        hud(scene,cam,'EXPLODED ASSEMBLY','Presentation overview  |  Frozen valid pose  |  Not an assembly instruction',mats,width)
        text(scene,cam,'Front + hind modules  /  linkage layers  /  drives + hardware',-width*.46,-width*.205,width*.012,mats['muted'])
        neutral=data['frames'][0]
        for i,item in enumerate(data['instances']):
            obj=objects[item['instance_id']];n=item['freecad_object_name'];g=item['group']
            sign=1 if 'fore' in g else -1
            displacement=Vector((0,0,0));start=2;duration=3
            if g.startswith(('fore','hind','torso:')) or g=='HindTendon':
                sign=1 if ('fore' in g) else -1;displacement.x=sign*.065
                if g in ('foreL','hindL'):displacement.y=.023
                if g in ('foreR','hindR'):displacement.y=-.023
            if n.startswith(('Link','DirectCrank','Slider','Cshaft','Ashaft','Bshaft','Dshaft')):
                displacement.y=.048 if neutral['transforms_m'][i][1][3]>=0 else -.048;start=6;duration=3
            if 'Motor' in n and g=='spine':displacement.z=.055;start=10;duration=2
            if n.startswith('CentralE'):
                displacement.y=.055 if ('Retainer' in n) else -.055;start=5;duration=2
            # One representative leg moved intact; no spring stretched across
            # subassemblies. Tendon and all its owners stay with hind module.
            M=Matrix(neutral['transforms_m'][i]);base=M.translation.copy()
            for f in range(1,721):
                t=(f-1)/30;u=max(0,min(1,(t-start)/duration));s=u*u*(3-2*u)
                if t>17:
                    u=max(0,min(1,(t-17)/5));s*=1-u*u*(3-2*u)
                obj.location=base+s*displacement;obj.keyframe_insert('location',frame=f)
            linear_keys(obj)
        # Frozen spring/cable meshes move intact with their named leg/torso.
        for f in (1,720):
            scene.frame_set(f);bpy.context.view_layer.update()
            for i,iid in enumerate(data['instance_order']):
                assert max(abs(objects[iid].matrix_world[r][c]-neutral['transforms_m'][i][r][c]) for r in range(4) for c in range(4))<1e-6
    else:
        is_spine=kind=='active_spine_mechanism';scene.render.fps=60;scene.frame_end=900 if is_spine else 1200;width=.30
        timeline='active_spine_mechanism' if is_spine else 'coordinated_spine_legs'
        frames=read_cycle(data,timeline);scene['phase_origin_rad']=frames[0]['commanded_rad'][0];bake_mechanics(scene,data,objects,frames,scene.frame_end)
        point_camera(cam,(.20,-.36,.13),(0,0,-.008),width)
        hud(scene,cam,'ACTIVE SPINE' if is_spine else 'SPINE + LEG COORDINATION',
            'Two redundant drives  /  One coupled spine coordinate' if is_spine else ('Paper-informed hip cycle (~69 deg) — passive loads not simulated' if 'paper_motion_profile' in data['production'] else 'Prescribed kinematic demonstration — passive loads not simulated'),mats,width)
        if is_spine:
            text(scene,cam,'Continuous crank  /  Captured sliders  /  Coupled torso outputs',-width*.46,-width*.205,width*.012,mats['muted'])
            # Isolate spine after whole robot introduction; all components
            # remain separate and animated in the saved scene.
            for item in data['instances']:
                if item['group'] in ('foreL','foreR','hindL','hindR','HindTendon'):
                    visibility(objects[item['instance_id']],[(1,True),(121,False),(721,True)])
        else:
            text(scene,cam,('0.2 Hz display  |  Hind backswing lags extension by 18 deg  |  Dashed tendon guides' if 'paper_motion_profile' in data['production'] else '0.2 Hz illustrative cycle  |  Orange dashed: routing guide; slack shape unresolved'),-width*.46,-width*.205,width*.011,mats['muted'])
        # Side explanatory shot then return to three-quarter. Camera transitions
        # may ease; mechanical parts stay exact linear baked per-frame samples.
        poses=[(1,(.20,-.36,.13),(0,0,-.008)),(121,(.0,-.40,.025),(0,0,-.008)),(480,(.0,-.40,.025),(0,0,-.008)),(600,(.20,-.36,.13),(0,0,-.008)),(scene.frame_end,(.20,-.36,.13),(0,0,-.008))]
        if not is_spine:
            poses=[(1,(0,-.4,.025),(0,0,-.01)),(360,(0,-.4,.025),(0,0,-.01)),(480,(.2,-.36,.13),(0,0,-.008)),(780,(.2,-.36,.13),(0,0,-.008)),(840,(-.16,-.32,.09),(-.05,0,-.01)),(1020,(-.16,-.32,.09),(-.05,0,-.01)),(1140,(.2,-.36,.13),(0,0,-.008)),(1200,(.2,-.36,.13),(0,0,-.008))]
        for f,loc,target in poses:
            point_camera(cam,loc,target,width);cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
        # Phase indicator is baked from exactly the trajectory's unwrapped phase.
        d=bpy.data.curves.new(kind+' phase indicator','CURVE');d.dimensions='3D';d.bevel_depth=width*.003;d.bevel_resolution=2
        sp=d.splines.new('POLY');sp.points.add(1);sp.points[0].co=(-width*.15,-width*.165,-.003,1);sp.points[1].co=(width*.15,-width*.165,-.003,1)
        o=bpy.data.objects.new(kind+' phase rail',d);scene.collection.objects.link(o);o.parent=cam;d.materials.append(mats['muted'])
        marker=text(scene,cam,'●',0,-width*.165,width*.022,mats['accent'])
        text(scene,cam,'CRANK PHASE  0° → 360°',-width*.46,-width*.165,width*.011,mats['muted'])
        for f in range(1,scene.frame_end+1):
            phase=frames[(f-1)%300]['commanded_rad'][0];marker.location.x=-width*.15+width*.30*((phase/math.tau)%1);marker.keyframe_insert('location',frame=f)
        linear_keys(marker)
    scene.frame_set(1)
    from presentation_shots import apply as apply_presentation
    apply_presentation(scene,objects,mats)
    path=save_scene(scene)
    report={'scene':kind,'path':path,'physical_instances':len(objects),'native_sha256':data['source']['cad_sha256'],'blender':bpy.app.version_string,'engine':scene.render.engine,'frame_count':scene.frame_end,'fps':scene.render.fps,'resolution':[1920,1080],'persistent_bake':True,'handlers_required':False,'mechanical_source':'existing r03/r07 descriptor, source-local meshes and versioned production timeline','render_status':'NOT_RUN'}
    REPORTS.mkdir(exist_ok=True);(REPORTS/(kind+'_scene.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('SCENE_SAVED',json.dumps(report));return scene
