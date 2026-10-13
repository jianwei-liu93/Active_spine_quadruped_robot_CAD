"""Conservative all-frame physical bounds check against the presentation HUD."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
s=bpy.data.scenes['spine_leg_coordination'];bpy.context.window.scene=s
objects=[o for o in s.objects if 'instance_id' in o]
worst=[1.,1.,0.,0.];violations=[]
for f in range(1,s.frame_end+1):
    s.frame_set(f);deps=bpy.context.evaluated_depsgraph_get()
    cam=s.camera;inv=cam.matrix_world.inverted();width=cam.data.ortho_scale
    height=width*s.render.resolution_y/s.render.resolution_x
    bounds=[1.,1.,0.,0.]
    for obj in objects:
        evaluated=obj.evaluated_get(deps);transform=inv@evaluated.matrix_world
        for v in evaluated.bound_box:
            p=transform@Vector(v);x=.5+p.x/width;y=.5+p.y/height
            bounds=[min(bounds[0],x),min(bounds[1],y),max(bounds[2],x),max(bounds[3],y)]
    worst=[min(worst[0],bounds[0]),min(worst[1],bounds[1]),max(worst[2],bounds[2]),max(worst[3],bounds[3])]
    if bounds[0]<.03 or bounds[1]<.16 or bounds[2]>.97 or bounds[3]>.82:
        violations.append({'frame':f,'normalized_bounds':bounds})
report={'status':'PASS' if not violations else 'FAIL','blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'physical_instances':len(objects),'frames':s.frame_end,'screen_bounds_min_x_min_y_max_x_max_y':worst,'safe_rectangle':[.03,.16,.97,.82],'scope':'Conservative projected evaluated object bounding boxes; camera framing only, no geometry or clearance claim','violations':violations}
(ROOT/'reports/animation/coordination_v2_framing.json').write_text(json.dumps(report,indent=2)+'\n')
print('COORDINATION_FRAMING',json.dumps(report),flush=True)
assert not violations
