"""Native candidate seventh actuator, winding wheel, guides and cable, mm/rad.

Only build() invokes FreeCAD. Native pads/pockets define wheel and guides;
actual route primitives define continuous circular-wire sweeps. All dimensions,
D coupling, axial anchor holes and retention are DESIGN_ASSUMPTION. Vendor
mount/spline pattern, securing knots, guide supports, ankle eye clearance and
load capacity remain unresolved. No live CAD validation is claimed here.
Externally supplied routes must be TORSO-LOCAL (not already transformed).
Cable planes can be changed by the caller in those route primitives/frames.
"""
import math
from tendon_r03 import tendon_route, _transformers


def _groove(b,body,z,outer,root,width,label):
    import FreeCAD as App
    import cad_common as cc
    old=body.Tip
    sk=b.doc.addObject('Sketcher::SketchObject',body.Name+'_'+label);body.addObject(sk)
    sk.Placement.Base.z=z+width/2
    cc.circle(sk,0,0,outer);cc.circle(sk,0,0,root)
    cut=body.newObject('PartDesign::Pocket',body.Name+'_'+label+'Pocket');cut.Profile=sk;cut.Length=width
    b.doc.recompute();sk.Visibility=False;old.Visibility=False


def _wheel(b,routes):
    import FreeCAD as App
    import cad_common as cc
    # Include neutral anchor angles in identity; never mutate a shared source.
    angles=tuple(routes[s]['wheel']['neutral_hole_angle_rad'] for s in (-1,1))
    pn='TENDON_r03_WHEEL_OD13_'+('_'.join(str(round(a,7)).replace('.','p').replace('-','m') for a in angles))
    if pn in b.sources:return b.sources[pn]
    body=b.doc.addObject('PartDesign::Body',pn)
    cc.metadata(body,pn,'PA12','ASSUMED winding wheel; native two grooves/D bore/axial anchor holes; knot and spline UNVERIFIED')
    sk=b.doc.addObject('Sketcher::SketchObject',pn+'_Section');body.addObject(sk)
    cc.circle(sk,0,0,6.5);cc.d_profile(sk,0,0,1.025,.85)
    pad=body.newObject('PartDesign::Pad',pn+'_Pad');pad.Profile=sk;pad.Length=2.4
    b.doc.recompute();sk.Visibility=False
    for i,z in enumerate((.6,1.8)):_groove(b,body,z,6.6,5.35,.5,'CableGroove'+str(i))
    old=body.Tip;holes=b.doc.addObject('Sketcher::SketchObject',pn+'_AxialAnchors');body.addObject(holes);holes.Placement.Base.z=2.4
    for a in angles:cc.circle(holes,5.5*math.cos(a),5.5*math.sin(a),.2)
    cut=body.newObject('PartDesign::Pocket',pn+'_AnchorPocket');cut.Profile=holes;cut.Length=2.4
    b.doc.recompute();holes.Visibility=False;old.Visibility=False
    b.library.addObject(body);b.sources[pn]=body
    return body


def _guide(b):
    pn='TENDON_r04_GUIDE_OD5p4_ID2p05_L1p2'
    if pn not in b.sources:
        body=b.ring(pn,5.4,2.05,1.2,'PA12')
        _groove(b,body,.6,2.8,2.35,.5,'CenterGroove')
        body.Process='ASSUMED finite guide pitch R2.5; mounting journal/support UNVERIFIED'
    return b.sources[pn]


def _shaft(b):
    pn='TENDON_r04_HEADED_GUIDE_SHAFT_D1p9_L3p6'
    if pn not in b.sources:
        body=b.ring(pn,1.9,0,3.6)
        _groove(b,body,3.15,1.05,.85,.6,'OuterRetainingGroove')
        import cad_common as cc
        old=body.Tip
        sk=b.doc.addObject('Sketcher::SketchObject',pn+'_InnerHeadSketch');body.addObject(sk)
        cc.circle(sk,0,0,1.6)
        head=body.newObject('PartDesign::Pad',pn+'_InnerHead');head.Profile=sk;head.Length=.3;head.Reversed=True
        b.doc.recompute();sk.Visibility=False;old.Visibility=False
        body.Process='ASSUMED headed fixed guide journal; mounting support unresolved'
    return b.sources[pn]


def cable_shape(route):
    """Sweep one continuous Ø.3 wire; fallback fuses actual segment sweeps.

    Raises on invalid/multisolid output; never substitutes straight decorative
    geometry. Arc primitives >pi are split to retain the specified directed
    circle branch (including multirevolution diagnostic routes).
    """
    import FreeCAD as App, Part
    V=lambda p:App.Vector(*p)
    edges=[]
    for p in route['primitives']:
        if p['length_mm']<1e-10:continue
        if p['type']=='line':edges.append(Part.makeLine(V(p['start']),V(p['end'])))
        else:
            C=V(p['center']);axis=V(p['axis']);start=V(p['start'])-C
            n=max(1,math.ceil(p['sweep_rad']/(math.pi/2)))
            def point(a):return C+App.Rotation(axis,math.degrees(a)).multVec(start)
            for i in range(n):
                a=p['sweep_rad']*i/n;z=p['sweep_rad']*(i+1)/n
                edges.append(Part.Arc(point(a),point((a+z)/2),point(z)).toShape())
    if not edges:raise ValueError('empty tendon route')
    def pipe(es):
        path=Part.Wire(es);edge=es[0];tangent=edge.tangentAt(edge.FirstParameter)
        section=Part.Wire([Part.makeCircle(.15,edge.Vertexes[0].Point,tangent)])
        return path.makePipeShell([section],True,False)
    try:solid=pipe(edges)
    except Exception:solid=None
    if solid is None or not solid.isValid() or len(solid.Solids)!=1:
        pieces=[pipe([edge]) for edge in edges];solid=pieces[0]
        for piece in pieces[1:]:solid=solid.fuse(piece)
        solid=solid.removeSplitter()
    if not solid.isValid() or len(solid.Solids)!=1:
        raise RuntimeError('Tendon sweep must form one valid continuous solid')
    return solid


def build(b,transform=None,routes=None,u=0,tag='HindTendon'):
    """Build neutral/candidate instances; returns explicit pose integration data.

    routes may be {−1:local_route,+1:local_route}. Native rigid components are
    instanced; cables must be rebuilt at pose updates from route primitives.
    transform is the same proper XZ torso transform accepted by tendon_route.
    """
    import FreeCAD as App, Part
    import cad_common as cc
    from retain_flexor import clip_source
    V=lambda p:App.Vector(*p)
    tf,tv=_transformers(transform)
    routes=routes or {side:tendon_route(side,u) for side in (-1,1)}
    for r in routes.values():
        if not r.get('assembly_compatible',False):raise ValueError('Cable assembly requires u in [0,pi/2]')
        if abs(r['wheel_angle_rad']-u)>1e-9:raise ValueError('Route wheel angle disagrees with build u')
    names=[];source_names=[];motion={}
    def add(src,suffix,placement,desc,group='Tendons'):
        src.Revision='r03';d=dict(desc,tag=tag,torso='hind')
        o=b.add(src,tag+'_'+suffix,placement,group,d)
        names.append(o.Name);source_names.append(src.Name);motion[o.Name]=d
    def axial(center,axis,length,spin=0):
        # Source XY is perpendicular to local +Z; center is its axial midpoint.
        z=V(tv(axis));rot=App.Rotation(V((0,0,1)),z)
        rot=App.Rotation(z,math.degrees(spin)).multiply(rot)
        return App.Placement(V(tf(center))-z*(length/2),rot)
    W=tuple(routes[-1]['wheel']['axle_center'])
    if math.dist(W,routes[1]['wheel']['axle_center'])>1e-9:raise ValueError('Branches must share one wheel axle center')
    wheel_start=(W[0]-1.2,W[1],W[2]);motor_center=(W[0]+14.4,W[1],W[2])
    # Wheel native XY -> local YZ with +Z pad axis -> +X.
    wheel=_wheel(b,routes)
    base=App.Rotation(V(tv((0,1,0))),V(tv((0,0,1))),V(tv((1,0,0))),'ZXY')
    rot=App.Rotation(V(tv((1,0,0))),math.degrees(u)).multiply(base)
    add(wheel,'Wheel',App.Placement(V(tf(wheel_start)),rot),
        {'kind':'tendon_r03_wheel','center':W,'axis':(1,0,0),'angle_rad':u,'source_start_x':wheel_start[0]})
    pn='ENV_TENDON_XC330_M181_r03'
    if pn not in b.sources:
        src=cc.simple_shape(b.doc,pn,Part.makeBox(20,26,34,V((-10,-13,-7))),'motor','manufacturer envelope; output/mount datum UNVERIFIED',role='PURCHASED')
        src.PartNumber='DYNAMIXEL_XC330_M181_T';src.Label='XC330-M181-T shared hind-knee motor envelope';src.addProperty('App::PropertyString','PaperDesignation');src.PaperDesignation='XC-M181-T';src.addProperty('App::PropertyFloat','PurchasedMass_g');src.PurchasedMass_g=23
        b.library.addObject(src);b.sources[pn]=src
    torso=App.Rotation(V(tv((1,0,0))),V(tv((0,1,0))),V(tv((0,0,1))),'ZXY')
    add(b.sources[pn],'KneeMotor',App.Placement(V(tf(motor_center)),torso.multiply(App.Rotation(V((0,0,1)),90))),
        {'kind':'torso_r03_offset','point':motor_center,'rotation_local_axis':(0,0,1),'rotation_deg':90},'Actuators')
    guide=_guide(b);shaft=_shaft(b);clip=clip_source(b)
    washer=b.ring('TENDON_r03_GUIDE_WASHER_OD3p6_ID2p05_Tp2',3.6,2.05,.2)
    frames={}
    for side,r in routes.items():
        label='L' if side==1 else 'R';frames[side]={}
        for name in ('shell_guide','hip_guide'):
            q=r[name];C=q['center'];axis=q['axis']
            # Hardware can face outward; cable arc direction is unchanged.
            if axis[1]*side<0:axis=tuple(-a for a in axis)
            frames[side][name]={'center':tf(C),'axis':tv(axis),'cable_arc_axis':tv(q['axis'])}
            desc={'kind':'tendon_r03_guide','side':side,'guide':name,'center':C,'axis':axis,'mount_support':'UNRESOLVED'}
            add(guide,label+'_'+name,axial(C,axis,1.2),desc)
            add(shaft,label+'_'+name+'_Shaft',axial(C,axis,3.6),dict(desc,component='journal'))
            def offset(d):return tuple(c+d*a for c,a in zip(C,axis))
            add(washer,label+'_'+name+'_Washer',axial(offset(.8),axis,.2),dict(desc,component='washer',axial_offset_mm=.8))
            add(clip,label+'_'+name+'_Clip',axial(offset(1.35),axis,.6),dict(desc,component='outer_clip',axial_offset_mm=1.35))
        pn='TENDON_r03_'+tag+'_'+label+'_CABLE_u'+str(round(u,8)).replace('.','p')
        src=cc.simple_shape(b.doc,pn,cable_shape(r),'cable','ASSUMED Ø.3 continuous cable sweep; securing/eye/wear unresolved',role='CABLE')
        b.library.addObject(src);b.sources[pn]=src
        add(src,label+'_Cable',App.Placement(V(tf((0,0,0))),torso),
            {'kind':'tendon_r03_cable','side':side,'rebuild_from_route':True,'wheel_angle_rad':u,'route_local':r})
    b.doc.recompute()
    return {'instances':tuple(names),'sources':tuple(dict.fromkeys(source_names)),'motion':motion,'guide_frames':frames,
            'operating_interval_rad':(0,math.pi/2),'limitations':('CAD validity/interference NOT_RUN by worker','Motor coupling/anchor knots/guide mounting supports unresolved','Ankle cable eye and compression seat clearance unresolved')}
