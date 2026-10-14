"""Movie S2-inspired r14 presentation; consumes the exported CAD cycle unchanged."""
from pathlib import Path
import json,math,hashlib,time
import bpy
from mathutils import Matrix,Vector,Quaternion
from build_scenes import read_cycle,bake_channel,linear_keys,point_camera,text,visibility,choose_mat
ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'animation/coordination_s2_style_r14.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mat(name,color,metal=0,rough=.4,emission=False):
    m=bpy.data.materials.new('S2 '+name);m.use_nodes=True
    tree=m.node_tree;tree.nodes.clear();out=tree.nodes.new('ShaderNodeOutputMaterial')
    node=tree.nodes.new('ShaderNodeEmission' if emission else 'ShaderNodeBsdfPrincipled')
    if emission:node.inputs[0].default_value=(*color,1)
    else:
        node.inputs['Base Color'].default_value=(*color,1)
        node.inputs['Metallic'].default_value=metal;node.inputs['Roughness'].default_value=rough
    tree.links.new(node.outputs[0],out.inputs['Surface']);return m

def bounds_world(objects):
    points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    return [min(p[a] for p in points) for a in range(3)],[max(p[a] for p in points) for a in range(3)]
def corners(lo,hi):return [Vector((x,y,z)) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
def polish_caption(scene,white,dark):
    """Keep the kinematic qualification readable over intentional detail crops."""
    caption=next(o for o in scene.objects if o.type=='FONT' and o.data.body.startswith('ILLUSTRATIVE KINEMATICS'))
    caption.data.materials.clear();caption.data.materials.append(white)
    mesh=bpy.data.meshes.new('S2 kinematic caption background')
    mesh.from_pydata([(0,-.011,0),(.38,-.011,0),(.38,.011,0),(0,.011,0)],[],[(0,1,2,3)])
    box=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(box);box.parent=scene.camera;mesh.materials.append(dark)
    for f in range(1,scene.frame_end+1):
        scene.frame_set(f);w=scene.camera.data.ortho_scale
        box.location=(-.466*w,-.248*w,-.0035);box.scale=(w,w,1)
        box.keyframe_insert('location',frame=f);box.keyframe_insert('scale',frame=f)
    linear_keys(box)
def tag(scene,cam,body,target,width,start,end,mats,x=-.43,y=.22):
    # Compact white labels on charcoal tags; all geometry is camera-local.
    label=text(scene,cam,body,x*width,y*width,.010*width,mats['white'])
    length=(len(body)*.006+ .018)*width;height=.023*width
    mesh=bpy.data.meshes.new(body+' tag');mesh.from_pydata([(0,0,0),(length,0,0),(length,height,0),(0,height,0)],[],[(0,1,2,3)])
    box=bpy.data.objects.new(body+' tag',mesh);scene.collection.objects.link(box);box.parent=cam
    box.location=(x*width-.006*width,y*width-.0115*width,-.0035);mesh.materials.append(mats['tag'])
    mesh=bpy.data.meshes.new(body+' leader');mesh.from_pydata([(0,0,0)]*3,[],[(0,1,2)])
    line=bpy.data.objects.new(body+' leader',mesh);scene.collection.objects.link(line);line.parent=cam;mesh.materials.append(mats['white'])
    line.shape_key_add(name='Basis');keys=mesh.shape_keys;keys.use_relative=False
    for f in range(start,end+1):
        scene.frame_set(f);bpy.context.view_layer.update()
        center=sum((Vector(v) for v in target.bound_box),Vector())/8
        tip=cam.matrix_world.inverted()@(target.matrix_world@center)
        a=Vector((x*width+length,y*width,-.003));p=Vector((tip.x,tip.y,-.003));d=p-a
        side=Vector((-d.y,d.x,0)).normalized()*width*.00035
        key=line.shape_key_add(name=str(f));key.interpolation='KEY_LINEAR'
        for v,co in zip(key.data,(a-side,a+side,p)):v.co=co
        keys.eval_time=(f-start+1)*10;keys.keyframe_insert('eval_time',frame=f)
    linear_keys(keys)
    for o in (label,box,line):visibility(o,[(1,False),(start,True),(end+1,False)])

def build():
    cfg=json.loads(CONFIG.read_text());name=cfg['scene'];count=cfg['frame_count'];stride=cfg['sample_stride']
    source=ROOT/cfg['source_scene'];source_sha=sha(source)
    if name in bpy.data.scenes:
        old=bpy.data.scenes[name]
        for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(old)
    with bpy.data.libraries.load(str(source),link=False) as (available,loaded):loaded.scenes=['spine_leg_coordination_r14']
    scene=loaded.scenes[0];assert scene is not None;scene.name=name
    if bpy.context.window:bpy.context.window.scene=scene
    objects={o['instance_id']:o for o in scene.objects if 'instance_id' in o}
    for o in list(scene.objects):
        if 'instance_id' not in o:bpy.data.objects.remove(o,do_unlink=True)
    data=json.loads((ROOT/cfg['source_manifest']).read_text());frames=read_cycle(data,'coordinated_spine_legs');order=data['instance_order']
    assert set(objects)==set(order) and len(objects)==455
    assert data['source']['cad_revision']=='r14'
    assert scene.get('source_manifest')==cfg['source_manifest']
    assert scene.get('source_manifest_sha256')==sha(ROOT/cfg['source_manifest'])
    assert scene.get('source_cad_sha256')==data['source']['cad_sha256']
    assert scene.get('source_timeline_sha256')==data['production']['timelines']['coordinated_spine_legs']['sha256']
    assert sha(ROOT/data['source']['cad_path'])==data['source']['cad_sha256']
    assert sha(ROOT/data['production']['timelines']['coordinated_spine_legs']['path'])==data['production']['timelines']['coordinated_spine_legs']['sha256']
    assert len({item['source_object_name'] for item in data['instances']})==108
    assert all(o.parent is None for o in objects.values())
    assert sum(item['geometry_kind']!='rigid' for item in data['instances'])==10
    assert count==1500 and cfg['fps']==60 and stride==3
    assert abs(cfg['display_frequency_hz']-.6)<1e-12
    scene.frame_start=1;scene.frame_end=count;scene.render.fps=cfg['fps']
    scene['source_manifest']=cfg['source_manifest'];scene['presentation_manifest']='animation/motion/presentation_coordination_s2_r14.json'
    scene['source_cad_sha256']=data['source']['cad_sha256']
    scene['physical_instances']=455;scene['presentation_only_body_motion']=True
    root=bpy.data.objects.new('FLEXOR S2 r14 illustrative body root',None);scene.collection.objects.link(root);root.rotation_mode='QUATERNION'
    for i,iid in enumerate(order):
        o=objects[iid];o.animation_data_clear();o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4);o.rotation_mode='QUATERNION'
        sample_indices=[((f-1)*stride)%300 for f in range(1,count+1)]
        for axis in range(3):bake_channel(o,'location',axis,[frames[j]['transforms_m'][i][axis][3] for j in sample_indices])
        quats=[]
        for j in sample_indices:
            q=list(frames[j]['quaternions_wxyz'][i])
            if quats and sum(a*b for a,b in zip(q,quats[-1]))<0:q=[-v for v in q]
            quats.append(q)
        for axis in range(4):bake_channel(o,'rotation_quaternion',axis,[q[axis] for q in quats])
        if o.data.shape_keys:
            keys=o.data.shape_keys;keys.animation_data_clear();bake_channel(keys,'eval_time',0,[keys.key_blocks[j+1].frame for j in sample_indices])
    # One rigid presentation transform surrounds the complete CAD assembly.
    feet=[o for iid,o in objects.items() if iid.endswith(('_Foot','_FootPad'))]
    root_cycle=[]
    for f in range(1,101):
        scene.frame_set(f);root.location=(0,0,0);phase=math.tau*(f-1)/100
        pitch=math.radians(cfg['pitch_half_excursion_deg'])*math.sin(phase-math.pi/3)
        root.rotation_quaternion=Quaternion((0,1,0),pitch);bpy.context.view_layer.update()
        lowest=min((o.matrix_world@v.co).z for o in feet for v in o.data.vertices)
        gap=cfg['base_floor_clearance_m']+cfg['flight_gap_max_m']*max(0,math.sin(phase-.2*math.pi))**2
        root.location=(cfg['fore_aft_half_excursion_m']*math.sin(phase),0,gap-lowest)
        bpy.context.view_layer.update();root_cycle.append((root.location.copy(),root.rotation_quaternion.copy(),gap))
    for axis in range(3):bake_channel(root,'location',axis,[root_cycle[(f-1)%100][0][axis] for f in range(1,count+1)])
    for axis in range(4):bake_channel(root,'rotation_quaternion',axis,[root_cycle[(f-1)%100][1][axis] for f in range(1,count+1)])
    # Separate render materials; no native meshes or source scenes are edited.
    palette={'frame':mat('graphite polymer',(.025,.027,.029),0,.4),'link':mat('ivory links',(.76,.76,.73),.12,.32),'metal':mat('brushed steel',(.42,.43,.42),.75,.28),'copper':mat('gold liners',(.65,.48,.14),.55,.32),'board':mat('electronics',(.055,.075,.07),.15,.45),'accent':mat('dark drive hardware',(.09,.095,.09),.6,.3),'route':mat('cable routing guides',(.52,.25,.07),.35,.4),'white':mat('white text',(1,1,.97),emission=True),'tag':mat('charcoal label',(.14,.15,.16),emission=True)}
    for item in data['instances']:
        o=objects[item['instance_id']]
        meta=data['production']['component_metadata'][item['freecad_object_name']]
        # Source geometry shares mesh data but uses OBJECT-linked materials.
        o.material_slots[0].link='OBJECT';o.material_slots[0].material=choose_mat(item,meta,palette)
    world=bpy.data.worlds.new(name+' warm studio');scene.world=world;world.use_nodes=True
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.56,.52,.46,1);bg.inputs[1].default_value=.45
    floor_mat=mat('warm studio floor',(.55,.51,.46),0,.65)
    floor_bsdf=next(n for n in floor_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    floor_bsdf.inputs['Emission Color'].default_value=(.55,.51,.46,1)
    floor_bsdf.inputs['Emission Strength'].default_value=.3
    mesh=bpy.data.meshes.new('studio floor');mesh.from_pydata([(-5,-5,0),(5,-5,0),(5,5,0),(-5,5,0)],[],[(0,1,2,3)])
    floor=bpy.data.objects.new('S2 r14 studio floor',mesh);scene.collection.objects.link(floor);mesh.materials.append(floor_mat);floor['presentation_floor']='r14'
    for i,(loc,power,size,color) in enumerate([((.1,-.3,.5),1.5,.5,(1,.92,.82)),((-.3,-.05,.25),.5,.4,(.86,.92,1)),((.05,.35,.38),1.5,.35,(1,.98,.90))]):
        d=bpy.data.lights.new('S2 softbox '+str(i),'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
        o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.08))-o.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=15
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    if hasattr(scene.render,'use_motion_blur'):scene.render.use_motion_blur=False
    camera_data=bpy.data.cameras.new('S2 studio camera');cam=bpy.data.objects.new(camera_data.name,camera_data);scene.collection.objects.link(cam);scene.camera=cam
    camera_data.type='ORTHO';camera_data.clip_start=.001;camera_data.clip_end=20
    groups={'overview':set(o['group'] for o in objects.values()),'spine':{'spine'},'hind':{'hindR','torso:hind','HindTendon'},'fore':{'foreR','torso:fore'}}
    directions={'overview':Vector((.23,-1,.22)),'spine':Vector((.10,-1,.16)),'hind':Vector((-.65,-1,.26)),'fore':Vector((.45,-1,.24))}
    # Each shot uses the union over a complete cycle; no camera chases the toes.
    shot_info={}
    for shot,selected in groups.items():
        # Leg macros deliberately focus on the actuators/springs and ankle
        # connection. Toe crops are intentional here; overview shows all feet.
        subset=[o for iid,o in objects.items() if o['group'] in selected and not (shot in ('hind','fore') and iid.endswith(('_Foot','_FootPad')))];lo=[1e6]*3;hi=[-1e6]*3
        for f in range(1,101):
            scene.frame_set(f);bpy.context.view_layer.update();a,b=bounds_world(subset)
            lo=[min(x,y) for x,y in zip(lo,a)];hi=[max(x,y) for x,y in zip(hi,b)]
        target=(Vector(lo)+Vector(hi))/2;direction=directions[shot].normalized();rotation=(-direction).to_track_quat('-Z','Y');view=rotation.to_matrix().inverted()
        projected=[view@(p-target) for p in corners(lo,hi)]
        width=max((max(p.x for p in projected)-min(p.x for p in projected))/.88,(max(p.y for p in projected)-min(p.y for p in projected))*1920/1080/.72)
        shot_info[shot]={'target':target,'direction':direction,'width':width,'ids':[o['instance_id'] for o in subset]}
    rows=[]
    for f in range(1,count+1):
        t=(f-1)/cfg['fps'];shot=next(s for a,b,s in cfg['shots'] if a<=t<b);info=shot_info[shot]
        point_camera(cam,info['target']+info['direction']*.7,info['target'],info['width'])
        cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f);camera_data.keyframe_insert('ortho_scale',frame=f)
        scene.frame_set(f);bpy.context.view_layer.update()
        rows.append({'frame':f,'source_sample':((f-1)*stride)%300,'root_transform_m':[[float(v) for v in r] for r in root.matrix_world],'floor_gap_m':root_cycle[(f-1)%100][2],'shot':shot,'target_groups':sorted(groups[shot]),'framing_instance_ids':info['ids']})
    linear_keys(cam);linear_keys(camera_data)
    # HUD is restrained and explicitly identifies the added presentation motion.
    header=text(scene,cam,'FLEXOR r14  /  SPINE–LEG SYNERGY',0,0,.003,palette['tag'])
    caption=text(scene,cam,'ILLUSTRATIVE KINEMATICS  |  Prescribed body motion; no dynamics',0,0,.0025,palette['tag'])
    for f in range(1,count+1):
        shot=rows[f-1]['shot'];w=shot_info[shot]['width']
        for o,xy,size in [(header,(-.46,.245),.014),(caption,(-.46,-.248),.010)]:
            o.location=(xy[0]*w,xy[1]*w,-.003);o.scale=(w/.30,)*3;o.keyframe_insert('location',frame=f);o.keyframe_insert('scale',frame=f)
    for o in (header,caption):linear_keys(o)
    labels=[('Spine servo','instance:SpineMotor1','spine',.19),('Spine linkages','instance:Link1_L2_1','spine',.10),('Winding wheel','instance:HindTendon_Wheel','hind',.20),('Tension spring','instance:hindR_extension_Spring','hind',.11),('Compression spring','instance:hindR_compression_Spring','hind',.02),('Fore torso','instance:Torso_fore','fore',.19),('Tension spring','instance:foreR_extension_Spring','fore',.10),('Compression spring','instance:foreR_compression_Spring','fore',.01)]
    for body,iid,shot,y in labels:
        if iid not in objects:continue
        a,b,_=next(row for row in cfg['shots'] if row[2]==shot)
        tag(scene,cam,body,objects[iid],shot_info[shot]['width'],int(a*cfg['fps'])+1,int(b*cfg['fps']),palette,y=y)
    polish_caption(scene,palette['white'],palette['tag'])
    presentation={'version':'presentation-root-transform-r14-v1','source_manifest_path':cfg['source_manifest'],'source_manifest_sha256':sha(ROOT/cfg['source_manifest']),'source_timeline_path':data['production']['timelines']['coordinated_spine_legs']['path'],'source_timeline_sha256':data['production']['timelines']['coordinated_spine_legs']['sha256'],'source_scene_path':cfg['source_scene'],'source_scene_sha256':source_sha,'source_cad_sha256':data['source']['cad_sha256'],'style_config_path':str(CONFIG.relative_to(ROOT)),'style_config_sha256':sha(CONFIG),'builder_path':str(Path(__file__).relative_to(ROOT)),'builder_sha256':sha(__file__),'sample_stride':stride,'frame_count':count,'fps':cfg['fps'],'transform_convention':'render_world_m = presentation_root_m @ verified_CAD_world_m; mesh remains source-local','root_motion_provenance':cfg['root_motion_provenance'],'floor_z_m':0.,'frames':rows}
    presentation['helper_files_sha256']={path:sha(ROOT/path) for path in ('animation/blender/build_scenes.py','animation/blender/procedural_geometry.py','animation/blender/build_coordination_r14.py')}
    (ROOT/scene['presentation_manifest']).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/scene['presentation_manifest']).write_text(json.dumps(presentation,separators=(',',':'))+'\n')
    scene.frame_set(1);path=ROOT/'animation/scenes'/(name+'.blend');path.parent.mkdir(parents=True,exist_ok=True);bpy.data.libraries.write(str(path),{scene},fake_user=True,compress=True)
    assert sha(source)==source_sha
    print('S2_SCENE_BUILT',json.dumps({'path':str(path),'physical_instances':len(objects),'frames':count,'shot_widths':{k:v['width'] for k,v in shot_info.items()},'source_scene_unchanged':True}),flush=True)
    return scene


if __name__ == '__main__':
    build()
