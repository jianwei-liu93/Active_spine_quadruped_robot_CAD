"""Lead-executed native positive cable clamps; all dimensions DESIGN_ASSUMPTION.

No automatic execution/save/schema writes. apply() replaces existing eye, wheel,
cable and journal definitions in place; only new physical clamp hardware adds
links. terminated_route() is the pose/source regeneration contract.
"""
import copy
import json
import math

RADIUS=5.5
BEND_RADIUS=.3
TERMINAL_NORMAL=-1 # both blocks on outboard -X face; motor interface preserved
TAIL_PHASE=math.atan(BEND_RADIUS/RADIUS)
TAIL_RADIUS=math.hypot(RADIUS,BEND_RADIUS)


def terminated_route(route):
    """Real axial terminal tail + R.3 quarter bend, exact old groove contact.

    Input primitives/frames must be torso-local, with wheel axis local+X.
    Captured neutral groove phase is retained. The offset axial hole is at
    theta+atan(.3/5.5), radiushypot(5.5,.3); terminal and bend rotate with wheel.
    Existing CW wrap and fixed guide primitives remain intact at every u>=0.
    Ankle terminates at radial2.1 rather than old radial1.5.
    """
    from tendon_r03 import _line, _arc
    r=copy.deepcopy(route)
    if math.dist(r['wheel']['axis'],(1,0,0))>1e-9:
        raise ValueError('Terminal routing requires torso-local wheel axis+X')
    if not 0<=r['wheel_angle_rad']<=math.pi/2:
        raise ValueError('Positive terminal routing supports wheel u in [0,pi/2]')
    if r.get('r07_positive_terminals'):
        if r['r07_positive_terminals'].get('terminal_outward_axis_x')!=TERMINAL_NORMAL:
            raise ValueError('Stale terminal packaging marker; regenerate from baseline route')
        return r
    side=r['side'];w=r['wheel'];W=w['axle_center'];T=w['hole'];a=w['hole_angle_rad']
    n=(float(TERMINAL_NORMAL),0.,0.);t=(0.,math.sin(a),-math.cos(a))
    C=tuple(v+BEND_RADIUS*k for v,k in zip(T,n))
    start=tuple(v-BEND_RADIUS*k for v,k in zip(C,t))
    outer=(W[0]+TERMINAL_NORMAL*2.,start[1],start[2])
    mid=tuple(c-BEND_RADIUS*(x+y)/math.sqrt(2) for c,x,y in zip(C,t,n))
    axis=(0.,TERMINAL_NORMAL*t[2],-TERMINAL_NORMAL*t[1]) # t cross n
    r['primitives']=[_line('terminal_axial_tail',outer,start),
                     _arc('terminal_Rp3_bend',start,T,mid,C,axis,BEND_RADIUS,math.pi/2)]+r['primitives']
    last=r['primitives'][-1];A=r['virtual_ankle_axis'];P=last['start']
    length=math.dist(A,P);unit=tuple((p-a)/length for p,a in zip(P,A))
    end=tuple(a+2.1*k for a,k in zip(A,unit))
    r['primitives'][-1]=_line('hip_to_ankle',P,end)
    r['ankle_anchor']=end;r['ankle_eye_radius_mm']=2.1
    r['length_mm']=sum(p['length_mm'] for p in r['primitives'])
    r['r07_positive_terminals']={'bend_radius_mm':BEND_RADIUS,'tail_phase_offset_rad':TAIL_PHASE,
        'tail_pitch_radius_mm':TAIL_RADIUS,'terminal_outward_axis_x':TERMINAL_NORMAL,'axial_tail_start':outer,'provenance':'DESIGN_ASSUMPTION'}
    return r


def _sketch(b,body,label,placement=None):
    sk=b.doc.addObject('Sketcher::SketchObject',body.Name+'_'+label);body.addObject(sk)
    if placement is not None:sk.Placement=placement
    return sk


def _feature(b,body,sk,kind,label,length,reversed=False):
    old=body.Tip
    f=body.newObject('PartDesign::'+kind,body.Name+'_'+label);f.Profile=sk;f.Length=length;f.Reversed=reversed
    b.doc.recompute();sk.Visibility=False
    if old:old.Visibility=False
    if f.Shape.isNull() or not f.Shape.isValid() or len(f.Shape.Solids)!=1:
        raise RuntimeError(body.Name+': invalid/disconnected '+label)
    return f


def _register(b,body,pn):
    body.Revision='r07';body.Process='DESIGN_ASSUMPTION native positive cable clamp; thread crests/strength/load qualification unresolved'
    b.library.addObject(body);b.sources[pn]=body
    return body


def _socket(b,body,z,af=.6,depth=.5):
    import FreeCAD as App, Part, Sketcher
    sk=_sketch(b,body,'HexSocket');sk.Placement.Base.z=z
    rr=af/math.sqrt(3);pts=[App.Vector(rr*math.cos(i*math.pi/3),rr*math.sin(i*math.pi/3),0) for i in range(6)]
    for i in range(6):
        g=sk.addGeometry(Part.LineSegment(pts[i],pts[(i+1)%6]),False)
        sk.addConstraint(Sketcher.Constraint('Block',g))
    _feature(b,body,sk,'Pocket','SocketPocket',depth)


def _grub(b,length,pn):
    body=b.ring(pn,1.1,0,length)
    _socket(b,body,length)
    if 'NominalThread' not in body.PropertiesList:body.addProperty('App::PropertyString','NominalThread')
    body.NominalThread='M1.4 DESIGN_ASSUMPTION; Ø1.1 minor core modeled; thread crests omitted'
    body.Revision='r07';body.Process='DESIGN_ASSUMPTION flat-tip grub, native .6AF socket, unverified thread/strength'
    return body


def _eye(b,side):
    import FreeCAD as App
    import cad_common as cc
    pn='LEG_r07_ANKLE_CLAMP_'+('L' if side==1 else 'R')+'_OD6_ID2p05_T2p4'
    if pn in b.sources:return b.sources[pn]
    body=b.ring(pn,6,2.05,2.4)
    # Standard plane_placement source+Z points -Y on both sides.
    z=1.8 if side==1 else .6
    sk=_sketch(b,body,'RadialBlindBore',App.Placement(App.Vector(3,0,z),App.Rotation(App.Vector(0,1,0),App.Vector(0,0,1),App.Vector(1,0,0),'ZXY')))
    cc.circle(sk,0,0,.2);_feature(b,body,sk,'Pocket','RadialPocket',1.2)
    sk=_sketch(b,body,'M1p4Tap');sk.Placement.Base.z=0 if side==1 else 2.4
    cc.circle(sk,2.1,0,.55);_feature(b,body,sk,'Pocket','TapPocket',1.85,reversed=(side==1))
    body.Revision='r07';body.Process='DESIGN_ASSUMPTION steel swivel; radialØ.4 blind1.2; M1.4 minorØ1.1 axialtap; no threadcrests'
    return body


def _journal(b,side):
    import cad_common as cc
    pn='LEG_r07_ANKLE_JOURNAL_'+('L' if side==1 else 'R')+'_D1p9_L15p05'
    if pn in b.sources:return b.sources[pn]
    body=b.ring(pn,1.9,0,15.05)
    for i,z in enumerate((.9,14.85) if side==1 else (.8,14.75)):
        sk=_sketch(b,body,'RetainingGroove'+str(i));sk.Placement.Base.z=z
        cc.circle(sk,0,0,1.05);cc.circle(sk,0,0,.85)
        _feature(b,body,sk,'Pocket','GroovePocket'+str(i),.6)
    body.Revision='r07';body.Process='DESIGN_ASSUMPTION anklejournal absY44.75..59.8; clipcenters45.25/59.2; no strengthqualification'
    return body


def _terminal(b):
    import FreeCAD as App
    import cad_common as cc
    pn='TENDON_r07_STEEL_KEYED_CLAMP_R3p3_6p4_T1p4'
    if pn in b.sources:return b.sources[pn]
    body=b.doc.addObject('PartDesign::Body',pn);cc.metadata(body,pn,'steel','DESIGN_ASSUMPTION keyed bolted clamp')
    sk=_sketch(b,body,'Block');cc.rectangle(sk,3.3,-1.1,3.1,2.2);_feature(b,body,sk,'Pad','BlockPad',1.4)
    sk=_sketch(b,body,'Key');cc.rectangle(sk,3.8,-.45,1.,.9);_feature(b,body,sk,'Pad','KeyPad',.5,reversed=True)
    sk=_sketch(b,body,'AxialHoles');sk.Placement.Base.z=1.4
    cc.circle(sk,TAIL_RADIUS,0,.2);cc.circle(sk,4.2,0,.4);_feature(b,body,sk,'Pocket','AxialHolePocket',1.9)
    sk=_sketch(b,body,'CrossTap',App.Placement(App.Vector(0,1.1,.8),App.Rotation(App.Vector(1,0,0),App.Vector(0,0,-1),App.Vector(0,1,0),'ZXY')))
    cc.circle(sk,TAIL_RADIUS,0,.55);_feature(b,body,sk,'Pocket','CrossTapPocket',1.25)
    return _register(b,body,pn)


def _anchor_bolt(b):
    import cad_common as cc
    pn='TENDON_r07_M1_ANCHOR_BOLT_COREp75_L2p2_HEAD1p6'
    if pn in b.sources:return b.sources[pn]
    body=b.ring(pn,.75,0,2.2)
    sk=_sketch(b,body,'Head');sk.Placement.Base.z=2.2;cc.circle(sk,0,0,.8);_feature(b,body,sk,'Pad','HeadPad',.5)
    _socket(b,body,2.7,af=.6,depth=.3)
    body.Revision='r07';body.Process='DESIGN_ASSUMPTION M1coreØ.75+headØ1.6; threadcrests omitted'
    return body


def _wheel(b,routes):
    import FreeCAD as App
    import cad_common as cc
    from build_tendon_r03 import _groove
    angles=[routes[s]['wheel']['neutral_hole_angle_rad']+TAIL_PHASE for s in (-1,1)]
    pn='TENDON_r07_WHEEL_OD13_KEYED_POSITIVE_TERMINALS'
    if pn in b.sources:
        if getattr(b.sources[pn],'AxialAnchorAnglesRad','')!=json.dumps(angles):
            raise ValueError('Cached r07 wheel has different captured anchor phases')
        return b.sources[pn]
    body=b.doc.addObject('PartDesign::Body',pn);cc.metadata(body,pn,'PA12','DESIGN_ASSUMPTION winding wheel; native keyed positive anchors')
    body.addProperty('App::PropertyString','AxialAnchorAnglesRad');body.AxialAnchorAnglesRad=json.dumps(angles)
    sk=_sketch(b,body,'Section');cc.circle(sk,0,0,6.5);cc.d_profile(sk,0,0,1.025,.85);_feature(b,body,sk,'Pad','WheelPad',2.4)
    for i,z in enumerate((.6,1.8)):_groove(b,body,z,6.6,5.35,.5,'CableGroove'+str(i))
    sk=_sketch(b,body,'AnchorBores');sk.Placement.Base.z=2.4
    for a in angles:cc.circle(sk,TAIL_RADIUS*math.cos(a),TAIL_RADIUS*math.sin(a),.2)
    _feature(b,body,sk,'Pocket','AnchorPocket',2.4)
    # Source wheelXY maps torsoYZ, sourceZ→torsoX.
    for side in (-1,1):
        a=routes[side]['wheel']['neutral_hole_angle_rad']+TAIL_PHASE
        # face-local X radial, Y tangential, Z outward. Right-handed.
        rot=App.Rotation(App.Vector(math.cos(a),math.sin(a),0),App.Vector(math.sin(a),-math.cos(a),0),App.Vector(0,0,-1),'ZXY')
        face=App.Placement(App.Vector(0,0,0),rot)
        sk=_sketch(b,body,'KeySeat'+str(side),face);cc.rectangle(sk,3.8,-.45,1.,.9);_feature(b,body,sk,'Pocket','KeyPocket'+str(side),.5)
        sk=_sketch(b,body,'AnchorBolt'+str(side),face);cc.circle(sk,4.2,0,.4);_feature(b,body,sk,'Pocket','BoltPocket'+str(side),1.)
        # Relief contains the real quarter bend, centered on original contactθ;
        # ysign follows CW outgoing tangent relative to the outward frame.
        reliefrot=App.Rotation(App.Vector(math.cos(a),math.sin(a),0),App.Vector(-side*math.sin(a),side*math.cos(a),0),App.Vector(0,0,side),'ZXY')
        reliefface=App.Placement(App.Vector(0,0,2.4 if side==1 else 0),reliefrot)
        sk=_sketch(b,body,'BendRelief'+str(side),reliefface)
        cc.rectangle(sk,TAIL_RADIUS-.23,-.65 if side==1 else -.02,.46,.67)
        _feature(b,body,sk,'Pocket','BendReliefPocket'+str(side),1.1 if side==1 else .8)
    return _register(b,body,pn)


def _capture(local,**kw):
    return dict(kind='torso_r04_rigid',torso='hind',wheel_angle_rad=0,
        local_placement_json=json.dumps({'base_xyz_mm':tuple(local.Base),'rotation_xyzw':tuple(local.Rotation.Q)}),
        provenance='DESIGN_ASSUMPTION',**kw)


def apply(b):
    """Upgrade an existing r05/r06 builder in place, retaining every old link.

    Frozen neutral configuration only; caller finalizes/persists MotionMap and
    uses terminated_route for every later cable source regeneration.
    """
    import FreeCAD as App
    import cad_common as cc
    from build_tendon_r03 import cable_shape
    V=lambda p:App.Vector(*p)
    initial={o.Name for o in b.doc.Objects if o.TypeId=='App::Link'}
    if any(n.endswith('_AnkleGrub') for n in initial):raise ValueError('r07 clamps already applied')
    cables={m['side']:(n,m) for n,m in b.motion.items() if m['kind']=='tendon_r03_cable'}
    if set(cables)!={-1,1}:raise ValueError('Expected exactly two hind cable links')
    captured={s:copy.deepcopy(m['route_local']) for s,(n,m) in cables.items()}
    if any(abs(r['wheel_angle_rad'])>1e-12 for r in captured.values()):raise ValueError('Clamp integration requires neutral wheel')
    wheel_links=[o for o in b.doc.Objects if o.TypeId=='App::Link' and b.motion.get(o.Name,{}).get('kind')=='tendon_r03_wheel']
    if len(wheel_links)!=1:raise ValueError('Expected one winding wheel')
    wheel=wheel_links[0];wp=wheel.LinkPlacement;W=captured[1]['wheel']['axle_center']
    # Actual current wheel placement supplies torso transform without schema assumptions.
    base=App.Rotation(V((0,1,0)),V((0,0,1)),V((1,0,0)),'ZXY')
    parent=wp.Rotation.multiply(base.inverted())
    origin=wp.Base-parent.multVec(V((W[0]-1.2,W[1],W[2])))
    def world(local):return App.Placement(origin+parent.multVec(local.Base),parent.multiply(local.Rotation))
    added=[];modified=[]
    def add(src,name,local,**desc):
        m=_capture(local,**desc);o=b.add(src,name,world(local),'Tendons',m);added.append(o.Name);return o
    def replace(name,src,local,m=None):
        o=b.doc.getObject(name);o.setLink(src);o.LinkPlacement=world(local);modified.append(name)
        if m is not None:b.motion[name]=m
        return o
    eye_grub=_grub(b,1.65,'LEG_r07_M1p4_ANKLE_GRUB_CORE1p1_L1p65')
    block=_terminal(b);wheel_grub=_grub(b,.95,'TENDON_r07_M1p4_TERMINAL_GRUB_CORE1p1_Lp95');bolt=_anchor_bolt(b)
    wheel.setLink(_wheel(b,captured));modified.append(wheel.Name)
    routes={s:terminated_route(r) for s,r in captured.items()}
    for side in (-1,1):
        label='L' if side==1 else 'R';tag='HindTendon_'+label;route=routes[side];A=route['geometry']['A'];anchor=route['ankle_anchor'];axis=route['virtual_ankle_axis']
        angle=math.atan2(anchor[2]-axis[2],anchor[0]-axis[0]);u=V((math.cos(angle),0,math.sin(angle)))
        eye_local=cc.plane_placement(A,side*57.6+1.2,angle)
        replace(tag+'_AnkleEye',_eye(b,side),eye_local,_capture(eye_local,component='ankle_eye',side=side))
        n=V((0,side,0));rot=App.Rotation(u,n.cross(u),n,'ZXY')
        local=App.Placement(V((A[0],side*57.15,A[1]))+u*2.1,rot)
        add(eye_grub,tag+'_AnkleGrub',local,component='ankle_grub',side=side)
        for name,m in list(b.motion.items()):
            if m.get('leg_type')!='hind' or m.get('side')!=side or m.get('point')!='A':continue
            if name.endswith('A_Journal'):
                local=cc.hardware_place(A,side*52.275,15.05);m.update(y=side*52.275,length=15.05);replace(name,_journal(b,side),local)
            elif 'A_Clip' in name and abs(m.get('y',0))>50:
                local=cc.hardware_place(A,side*59.2,.6);m.update(y=side*59.2,length=.6);b.doc.getObject(name).LinkPlacement=world(local);modified.append(name)
        cn,cm=cables[side];src=b.doc.addObject('PartDesign::Feature','TENDON_r07_'+label+'_CABLE')
        cc.metadata(src,src.Name,'cable','DESIGN_ASSUMPTION Ø.3 continuous positive-terminal cable; bendstrengthunverified',role='CABLE');src.Shape=cable_shape(route);b.library.addObject(src);b.sources[src.Name]=src
        cm.update(route_local=route,rebuild_from_route=True,termination_generator='cable_clamps_r07.terminated_route')
        b.doc.getObject(cn).setLink(src);modified.append(cn)
        # Blocks rotate with the wheel; source localZ points outboard −X for both branches.
        a=captured[side]['wheel']['neutral_hole_angle_rad']+TAIL_PHASE
        rad=V((0,math.cos(a),math.sin(a)));normal=V((TERMINAL_NORMAL,0,0));tangent=normal.cross(rad)
        rot=App.Rotation(rad,tangent,normal,'ZXY');face=V((W[0]+TERMINAL_NORMAL*1.2,W[1],W[2]))
        add(block,tag+'_WheelClamp',App.Placement(face,rot),component='wheel_clamp',side=side,wheel_center=W)
        add(bolt,tag+'_WheelAnchorBolt',App.Placement(face+rad*4.2-normal*.8,rot),component='wheel_anchor_bolt',side=side,wheel_center=W)
        # Grub pad axis +localY, flat-tip contact y=.15 at cablecrosssection.
        grot=App.Rotation(rad,-normal,tangent,'ZXY')
        add(wheel_grub,tag+'_WheelClampGrub',App.Placement(face+rad*TAIL_RADIUS+tangent*.15+normal*.8,grot),component='wheel_clamp_grub',side=side,wheel_center=W)
    b.doc.recompute()
    final={o.Name for o in b.doc.Objects if o.TypeId=='App::Link'}
    if not initial<=final:raise RuntimeError('Clamp integration removed existing physical links')
    return {'added_instances':added,'modified_instances':modified,'retained_original_link_count':len(initial),
            'new_link_count':len(final)-len(initial),'routes':routes,'tail_phase_offset_rad':TAIL_PHASE,
            'tail_radius_mm':TAIL_RADIUS,'bend_radius_mm':BEND_RADIUS,'terminal_outward_axis_x':TERMINAL_NORMAL,'wheel_axial_cable_bore_diameter_mm':.4,
            'neutral_groove_contact_angles_rad':{s:captured[s]['wheel']['neutral_hole_angle_rad'] for s in (-1,1)},
            'neutral_axial_anchor_angles_rad':{s:captured[s]['wheel']['neutral_hole_angle_rad']+TAIL_PHASE for s in (-1,1)},
            'provenance':'DESIGN_ASSUMPTION','limitations':['Threadcrests omitted; load/strength/bendfatigue unverified','Lead must run nativeclearance and posechecks; no fabricationrelease']}
