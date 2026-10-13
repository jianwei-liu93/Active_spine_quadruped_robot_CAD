"""Presentation-only shot edits; no modification of CAD or mechanism poses."""
import bpy, math
from mathutils import Vector
from build_scenes import point_camera, text, visibility, linear_keys

def callout(scene,cam,body,target,x,y,width,mats,visible):
    label=text(scene,cam,body,x,y,width*.012,mats['ink'])
    mesh=bpy.data.meshes.new(body+' leader');mesh.from_pydata([(0,0,0)]*3,[],[(0,1,2)])
    obj=bpy.data.objects.new(body+' leader',mesh);scene.collection.objects.link(obj);obj.parent=cam;mesh.materials.append(mats['accent'])
    obj.shape_key_add(name='Basis');keys=mesh.shape_keys;keys.use_relative=False
    for f in range(1,scene.frame_end+1):
        scene.frame_set(f);bpy.context.view_layer.update()
        center=sum((Vector(v) for v in target.bound_box),Vector())/8
        tip=cam.matrix_world.inverted()@(target.matrix_world@center)
        p=Vector((tip.x,tip.y,-.004));a=Vector((x+width*.14,y,-.004));vec=p-a
        side=Vector((-vec.y,vec.x,0)).normalized()*width*.0005
        key=obj.shape_key_add(name='Leader frame '+str(f));key.interpolation='KEY_LINEAR'
        for dest,v in zip(key.data,(a-side,a+side,p)):dest.co=v
        keys.eval_time=f*10;keys.keyframe_insert('eval_time',frame=f)
    linear_keys(keys)
    for o in (label,obj):visibility(o,visible)


def apply(scene,objects,mats):
    cam=scene.camera;name=scene.name
    # Move phase indicator into a clear left margin below the assembly.
    if name!='exploded_assembly':
        width=.30
        rail=next(o for o in scene.objects if o.name.startswith(name+' phase rail'))
        rail.data.splines[0].points[0].co=(-width*.46,-width*.175,-.003,1)
        rail.data.splines[0].points[1].co=(-width*.26,-width*.175,-.003,1)
        for o in scene.objects:
            if o.type=='FONT' and o.data.body=='CRANK PHASE  0° → 360°':
                o.data.body='CRANK  0° → 360°';o.location.y=-width*.15
        marker=next(o for o in scene.objects if o.type=='FONT' and o.data.body=='●')
        marker.animation_data_clear();marker.location.y=-width*.175
        for f in range(1,scene.frame_end+1):
            marker.location.x=-width*.46+width*.20*((f-1)%300)/300;marker.keyframe_insert('location',frame=f)
        linear_keys(marker)
    if name=='active_spine_mechanism':
        for iid,obj in objects.items():
            if iid.startswith('instance:HindTendon'):
                visibility(obj,[(1,True),(121,False),(721,True)])
        callout(scene,cam,'COMMON CRANK',objects['instance:DirectCrank_1'],-.138,.033,.30,mats,[(1,False),(121,True),(721,False)])
        callout(scene,cam,'UPPER SLIDER',objects['instance:ThroughC1'],-.138,.021,.30,mats,[(1,False),(121,True),(721,False)])
        callout(scene,cam,'LOWER SLIDER',objects['instance:ThroughC2'],-.138,.009,.30,mats,[(1,False),(121,True),(721,False)])
    if name=='spine_leg_coordination':
        # Hind-end view reveals the winding wheel whose axis is longitudinal.
        for f,loc,target in [(840,(-.36,-.22,.10),(-.035,0,-.012)),(1020,(-.36,-.22,.10),(-.035,0,-.012))]:
            point_camera(cam,loc,target,.30);cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
        callout(scene,cam,'HIND WINDING WHEEL',objects['instance:HindTendon_Wheel'],-.138,.025,.30,mats,[(1,False),(840,True),(1021,False)])
    if name=='exploded_assembly':
        # Keep both hind legs and the tendon route in one intact subassembly.
        for iid,obj in objects.items():
            if obj['group'] in ('hindL','hindR'):
                action=obj.animation_data.action
                for layer in action.layers:
                    for strip in layer.strips:
                        for bag in strip.channelbags:
                            for curve in bag.fcurves:
                                if curve.data_path=='location' and curve.array_index==1:
                                    y=obj.location.y
                                    for key in curve.keyframe_points:key.co[1]=y
        # Distinct views of representative fore/hind modules during the hold.
        for obj in objects.values():
            g=obj['group'];fore=g in ('foreL','foreR','torso:fore');hind=g in ('hindL','hindR','torso:hind','HindTendon')
            visibility(obj,[(1,True),(391,fore),(437,True),(466,hind),(512,True)])
        poses=[(1,(.25,-.38,.20),(0,0,-.008),.43),(361,(.25,-.38,.20),(0,0,-.008),.43),
               (391,(.32,-.30,.12),(.116,0,-.025),.32),(436,(.32,-.30,.12),(.116,0,-.025),.32),
               (466,(-.35,-.25,.12),(-.121,0,-.024),.32),(511,(-.35,-.25,.12),(-.121,0,-.024),.32),
               (541,(.25,-.38,.20),(0,0,-.008),.43),(720,(.25,-.38,.20),(0,0,-.008),.43)]
        overlays=[o for o in scene.objects if o.parent==cam]
        original={o.name:o.location.copy() for o in overlays}
        for f,loc,target,width in poses:
            point_camera(cam,loc,target,width);cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f);cam.data.keyframe_insert('ortho_scale',frame=f)
            for o in overlays:
                factor=width/.43;o.location=original[o.name]*factor;o.location.z=-.003;o.scale=(factor,)*3;o.keyframe_insert('location',frame=f);o.keyframe_insert('scale',frame=f)
        for body,window in [('FORELEG MODULE  /  Intact elastic linkage',[(1,False),(391,True),(437,False)]),('HIND MODULE  /  Common wheel + tendon guides',[(1,False),(466,True),(512,False)])]:
            o=text(scene,cam,body,-.110,.034,.003,mats['ink']);visibility(o,window)
    scene.frame_set(1)
