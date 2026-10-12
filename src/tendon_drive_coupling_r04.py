"""Provisional keyed winding-wheel adapter; lead-only native CAD execution.

Shaft/washer/clip dimensions are DESIGN_ASSUMPTION. The shaft ends flush at
candidate motor exterior face Wx+1.4 and never enters the motor envelope.
Manufacturer spline, output screw and internal axial capture are UNKNOWN;
this candidate cannot certify the purchased actuator interface or torque.
No pose/schema edits, live CAD calls, automatic apply or document saves.
"""
import json
import math


def apply(b,W=(-37,0,0),u=0,transform=None,tag='HindTendon'):
    """Create native D shaft and separate outer clip/washer/root shim.

    W and captured local placements use torso-local XYZ. transform maps XZ
    once, leaving Y unchanged. Motion descriptors capture local Placement JSON
    for lead integration; they do not install or modify pose-controller logic.
    Repeated application to the same tag is rejected before adding anything.
    """
    import FreeCAD as App
    import cad_common as cc
    from retain_flexor import clip_source
    from tendon_r03 import _transformers
    if len(W)!=3 or not all(math.isfinite(v) for v in (*W,u)):
        raise ValueError('W must contain three finite coordinates and u must be finite')
    if not 0<=u<=math.pi/2:raise ValueError('Candidate assembled wheel interval is [0, pi/2]')
    names=[tag+'_DriveDshaft',tag+'_DriveOuterClip',tag+'_DriveOuterWasher',tag+'_DriveRootShim']
    if any(b.doc.getObject(name) for name in names):raise ValueError('Wheel coupling already applied for '+tag)
    tf,tv=_transformers(transform);V=lambda p:App.Vector(*p)
    pn='TENDON_r04_D_DRIVE_Rp95_Fp8_L3p7'
    if pn not in b.sources:
        body=b.doc.addObject('PartDesign::Body',pn)
        cc.metadata(body,pn,'steel','DESIGN_ASSUMPTION D adapter; manufacturer spline/output screw/axial coupling UNKNOWN',role='HARDWARE')
        body.Revision='r04'
        sk=b.doc.addObject('Sketcher::SketchObject',pn+'_DSection');body.addObject(sk)
        cc.d_profile(sk,0,0,.95,.8)
        pad=body.newObject('PartDesign::Pad',pn+'_Pad');pad.Profile=sk;pad.Length=3.7
        b.doc.recompute();sk.Visibility=False
        groove=b.doc.addObject('Sketcher::SketchObject',pn+'_RetainingGroove');body.addObject(groove);groove.Placement.Base.z=3.5
        cc.circle(groove,0,0,1.05);cc.circle(groove,0,0,.85)
        cut=body.newObject('PartDesign::Pocket',pn+'_GroovePocket');cut.Profile=groove;cut.Length=.6
        b.doc.recompute();groove.Visibility=False;pad.Visibility=False
        for key,value in [('ManufacturerInterface','UNKNOWN spline/output screw/axial capture; provisional exterior adapter'),('Provenance','DESIGN_ASSUMPTION')]:
            body.addProperty('App::PropertyString',key,'Coupling');setattr(body,key,value)
        b.library.addObject(body);b.sources[pn]=body
    shaft=b.sources[pn];clip=clip_source(b)
    washer=b.ring('TENDON_r04_DRIVE_OUTER_WASHER_OD3p6_ID2p05_Tp2',3.6,2.05,.2)
    shim=b.ring('TENDON_r04_DRIVE_ROOT_SHIM_OD3_ID2p05_Tp2',3,2.05,.2)
    # Source X -> torso +Y, source Y -> torso -Z, source Z -> torso -X.
    # Rotation about +X by u keeps the flat aligned with the winding wheel.
    local_base=App.Rotation(V((0,1,0)),V((0,0,-1)),V((-1,0,0)),'ZXY')
    local_rot=App.Rotation(V((1,0,0)),math.degrees(u)).multiply(local_base)
    torso_rot=App.Rotation(V(tv((1,0,0))),V(tv((0,1,0))),V(tv((0,0,1))),'ZXY')
    def local_origin(x):return (W[0]+x,W[1],W[2])
    components=[(shaft,names[0],local_origin(1.4),3.7,'D_shaft'),
                (clip,names[1],local_origin(-1.8+.3),.6,'outer_clip'),
                (washer,names[2],local_origin(-1.4+.1),.2,'outer_washer'),
                (shim,names[3],local_origin(1.3+.1),.2,'root_shim')]
    instances=[];motion={}
    for source,name,origin,length,component in components:
        local=App.Placement(V(origin),local_rot)
        placement=App.Placement(V(tf(origin)),torso_rot.multiply(local_rot))
        captured={'base_xyz_mm':tuple(local.Base),'rotation_xyzw':tuple(local.Rotation.Q)}
        desc={'kind':'torso_r04_rigid','torso':'hind','tag':tag,'component':component,
              'local_placement_json':json.dumps(captured),'wheel_angle_rad':u,
              'axis_local':(-1,0,0),'axial_length_mm':length,'provenance':'DESIGN_ASSUMPTION'}
        obj=b.add(source,name,placement,'Tendons',desc);instances.append(obj.Name);motion[obj.Name]=desc
    b.doc.recompute()
    return {'instances':tuple(instances),'motion':motion,
            'shaft_local_x_bounds_mm':(W[0]-2.3,W[0]+1.4),
            'motor_face_x_mm':W[0]+1.4,'clip_center_x_mm':W[0]-1.8,
            'limitations':('CAD BRep/collision NOT_RUN by worker','Manufacturer spline/output screw/axial capture UNKNOWN','D adapter torque capacity and retainer fits unverified')}
