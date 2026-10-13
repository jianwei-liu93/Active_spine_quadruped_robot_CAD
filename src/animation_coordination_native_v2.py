"""Bounded native spring/cable tessellation for the larger v2 trajectory."""
import json,time
from animation_coordination_v2 import trajectory,paper_descriptor_context
from animation_pose_export import ROOT,snapshot,serial,digest,shape_hash,matrix

def run(native):
    import FreeCAD as App
    import leg_motion_r07 as motion
    doc=App.openDocument(str(native));before=snapshot(doc);start=time.monotonic()
    baseline=json.loads((ROOT/'animation/motion/ax01_r10.json').read_text())
    config=json.loads((ROOT/'parameters/assembly_r10.json').read_text())
    folder=ROOT/'animation/geometry/r10/procedural_examples_v2';folder.mkdir(parents=True,exist_ok=True)
    records=[];cache={}
    for i in (15,165):
        theta,angles,wheel=trajectory('coordinated_spine_legs',i/60,baseline['frames'][0]['leg_angles_rad'])
        with paper_descriptor_context():
            plan=motion.descriptor(doc,theta,angles,wheel,config)
            generated=motion.regenerate_sources(plan,cache)
        for name in ('foreL_compression_Spring','foreL_extension_Spring','hindL_compression_Spring','hindL_extension_Spring','HindTendon_L_Cable'):
            shape=generated.get(name,doc.getObject(name).LinkedObject.Shape)
            frozen=shape_hash(shape);vertices,triangles=shape.copy().tessellate(.03)
            assert frozen==shape_hash(shape)
            path=folder/(name+'_'+str(i)+'.json')
            path.write_bytes(serial({'vertices_m':[[v.x*.001,v.y*.001,v.z*.001] for v in vertices],'triangles':[list(t) for t in triangles],'local_units':'m'}))
            records.append({'instance_id':'instance:'+name,'sample_index':i,'path':str(path.relative_to(ROOT)),'sha256':digest(path.read_bytes()),'local_shape_sha256':frozen,'transform_mm':matrix(plan['placements'][name]),'is_valid':shape.isValid(),'solid_count':len(shape.Solids)})
        print('V2_NATIVE_EXAMPLE',i,flush=True)
    assert before==snapshot(doc)
    report={'status':'NATIVE_EXAMPLES_EXPORTED','examples':records,'sample_indices':[15,165],'document_unchanged':True,'elapsed_seconds':time.monotonic()-start,'profile_sha256':digest((ROOT/'animation/coordination_paper_profile_v2.json').read_bytes())}
    (folder/'manifest.json').write_bytes(serial(report));App.closeDocument(doc.Name);return report
