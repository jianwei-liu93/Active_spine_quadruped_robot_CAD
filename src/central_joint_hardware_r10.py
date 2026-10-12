"""Real separate central E journal/washer/clip instances; lead-run only."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def apply(b):
    import FreeCAD as App,Part,Sketcher
    import cad_common as cc
    from refine_flexor import rect,disk,sketch_face
    from kinematics import spine
    doc=b.doc;c=json.loads((ROOT/'parameters/assembly_r10.json').read_text())['central_attachment_r10']
    if any(o.Name.startswith('CentralE') for o in doc.Objects):raise ValueError('Central hardware already exists')
    if abs(doc.PoseController.SpinePhaseRad)>1e-12:raise ValueError('Integrate at neutral only')
    def register(o):
        b.library.addObject(o);b.sources[o.Name]=o;o.Revision='r10';return o
    def ring(name,od,id_,length):
        o=cc.ring(doc,name,od,id_,length,'steel',name)
        o.Process='DESIGN_ASSUMPTION central E stack; supplier fits, material/spring temper and retention capacity UNVERIFIED'
        return register(o)
    def cut(o,label,face,z,depth):
        old=o.Tip;sk=sketch_face(doc,o,o.Name+'_'+label+'Sketch',face,z)
        f=o.newObject('PartDesign::Pocket',o.Name+'_'+label);f.Profile=sk;f.Length=depth
        doc.recompute();sk.Visibility=False;old.Visibility=False
        if not sk.FullyConstrained or not f.Shape.isValid() or len(f.Shape.Solids)!=1:raise RuntimeError('Invalid central hardware feature '+label)
    length=c['pin_length_mm'];pin=ring('CENTRAL_E_GROOVED_PIN_r10',c['pin_diameter_mm'],0,length)
    for i,yy in enumerate((-c['pin_groove_center_abs_y_mm'],c['pin_groove_center_abs_y_mm'])):
        z=length/2+yy+c['pin_groove_width_mm']/2
        cut(pin,'Groove'+str(i),disk(0,0,1.2).cut(disk(0,0,c['pin_groove_root_diameter_mm']/2)),z,c['pin_groove_width_mm'])
    washer=ring('CENTRAL_E_THRUST_WASHER_r10',c['washer_od_mm'],c['washer_id_mm'],c['washer_thickness_mm'])
    clip=ring('CENTRAL_E_SPLIT_RETAINER_r10',c['retainer_od_mm'],c['retainer_id_mm'],c['retainer_thickness_mm'])
    w=c['retainer_slot_width_mm'];cut(clip,'RadialOpening',rect(-w/2,0,w,c['retainer_od_mm']),c['retainer_thickness_mm'],c['retainer_thickness_mm'])
    bearing=doc.getObject('BRG_2x4x1p2_PROVISIONAL')
    if bearing is None:raise ValueError('Existing provisional bearing source missing')
    instances=[];grounded=[]
    def add(source,name,placement,torso=None,E=None):
        o=cc.instance(doc,source,name,placement);doc.getObject('SpineHardware').addObject(o);instances.append(o.Name)
        if torso:
            base=placement.Base-App.Vector(E[0],0,E[1])
            b.motion[o.Name]={'kind':'torso_r04_rigid','torso':torso,
                'local_placement_json':json.dumps({'base_xyz_mm':list(base),'rotation_xyzw':list(placement.Rotation.Q)}),
                'interface':'existing_E_pitch_axis_no_new_DOF','provenance':'DESIGN_ASSUMPTION central pin stack'}
        else:grounded.append(o.Name)
        return o
    s=spine(0,b.p)
    for i,torso in ((1,'hind'),(2,'fore')):
        E=s['E'+str(i)];prefix='CentralE'+str(i)
        add(pin,prefix+'_Pin',cc.hardware_place(E,0,length),torso,E)
        for j,y in enumerate(c['bearing_y_centers_mm']):add(bearing,prefix+'_Bearing'+str(j),cc.hardware_place(E,y,1.2))
        for j,y in enumerate(c['washer_y_centers_mm']):add(washer,prefix+'_Washer'+str(j),cc.hardware_place(E,y,c['washer_thickness_mm']),torso,E)
        for j,y in enumerate(c['retainer_y_centers_mm']):add(clip,prefix+'_Retainer'+str(j),cc.hardware_place(E,y,c['retainer_thickness_mm']),torso,E)
    doc.PoseController.MotionMap=json.dumps(b.motion);doc.recompute()
    return {'new_instances':instances,'grounded_bearings':grounded,'physical_additions':len(instances),
            'moving_hardware_owner':'existing torso E output; fixed bearings owned by integrated lumbar frame',
            'nominal_lug_to_washer_gap_mm':0.2,'nominal_washer_to_clevis_gap_mm':0.0,
            'nominal_clevis_to_retainer_gap_mm':0.1,'pin_axial_insertion':'before motors/cables, along transverseY through open clevis; service-access check pending',
            'limits':'Supplier bearing/retainer, pin fits and printed bore/stack tolerances unverified; no strength qualification'}
