"""Lead-only native candidate knee-case cage and fixed cable-guide supports.

Torso-local XYZ, mm. Integrates additive features into the existing hind
carrier: no new moving linkage. All mounting/fastener dimensions are design
assumptions. Does not invent a manufacturer case screw pattern.
"""
import math,json

def case_clearances(b,body,routes):
    """Remove obsolete upper torso tie; drill complete rear bolt stack."""
    import FreeCAD as App
    import cad_common as cc
    V=App.Vector
    ties=b.doc.getObject('hindCrossTiesProfile')
    for i in reversed(range(ties.GeometryCount)):
        if ties.Geometry[i].Center.y>0:ties.delGeometry(i)
    rear=routes[-1]['wheel']['axle_center'][0]+27.4
    if b.doc.getObject('KneeLockThroughBores'):return
    old=body.Tip
    sk=b.doc.addObject('Sketcher::SketchObject','KneeLockThroughBores');body.addObject(sk)
    # Sketch x=-torsoZ,y=torsoY, normal+torsoX, mapped into source coordinates.
    sk.Placement=App.Placement(V(rear+1.2,0,16),App.Rotation(V(0,-1,0),V(0,0,-1),V(1,0,0),'ZXY'))
    for side in (-1,1):cc.circle(sk,-15,side*12.8,1.1)
    pk=body.newObject('PartDesign::Pocket','KneeLockThroughBorePocket');pk.Profile=sk;pk.Length=4.8
    b.doc.recompute();sk.Visibility=False;old.Visibility=False


def apply(b,routes,transform=None):
    import FreeCAD as App
    import cad_common as cc
    from refine_flexor import rect,disk,sketch_face
    from tendon_r03 import _transformers
    V=App.Vector
    body=b.doc.getObject('TORSO_HIND_CAGE_r03')
    if body is None:raise ValueError('Build hind torso before its tendon mounts')
    if b.doc.getObject('KneeCageRearBridge'):raise ValueError('Mounts already installed')
    dx=routes[-1]['wheel']['axle_center'][0]+37
    # Existing torso source coordinates (x,z,16-y) map to local XYZ.
    xyz=lambda p:V(p[0],p[2],16-p[1])
    vec=lambda p:V(p[0],p[2],-p[1])
    def pad(name,face,origin,normal,length):
        old=body.Tip
        sk=sketch_face(b.doc,body,name+'Profile',face)
        if abs(normal[1])==1:
            rot=App.Rotation(vec((1,0,0)),vec((0,0,-normal[1])),vec(normal),'ZXY')
        elif abs(normal[0])==1:
            rot=App.Rotation(vec((0,0,-normal[0])),vec((0,1,0)),vec(normal),'ZXY')
        else:rot=App.Rotation(V(0,0,1),vec(normal))
        sk.Placement=App.Placement(xyz(origin),rot)
        p=body.newObject('PartDesign::Pad',name);p.Profile=sk;p.Length=length
        b.doc.recompute();sk.Visibility=False;old.Visibility=False
        if not p.Shape.isValid() or len(p.Shape.Solids)!=1:raise RuntimeError(name+' not a connected valid native pad')
        return p
    def rod(name,P,Q,r):
        d=V(*Q)-V(*P);pad(name,disk(0,0,r),P,tuple(d/d.Length),d.Length)
    # Bridges first connect the future central cage to existing E-H cheeks.
    for side in (-1,1):
        pad('KneeCarrierBridge'+str(side).replace('-','R'),rect(-9.6+dx,-2.5,5,5),
            (0,side*15.0,0),(0,-side,0),6.5)
    # Profiles at X planes: orientation gives sketch x=-Z, y=Y for +X.
    # Symmetric Y sections allow this mapping to be explicit and inspectable.
    outer=rect(-29,-12,38,24)
    window=rect(-27.4,-10.4,34.8,20.8)
    pad('KneeCageRearBridge',outer.cut(window),(-9.6+dx,0,0),(1,0,0),1.2)
    for y in (-11.2,11.2):
        for z in (-8.2,28.2):rod('KneeCageRail_'+str(y).replace('-','R').replace('.','p')+'_'+str(z).replace('-','R').replace('.','p'),(-9.0+dx,y,z),(-36.2+dx,y,z),.65)
    # Front rim captures case sides; clear the wheel and provisional output.
    front=outer.cut(rect(-27.4,-8.8,34.8,17.6))
    # Outgoing cable crosses the side rim at Z~6mm. Open both side bands
    # through Z4.5..8.5; preserve the remaining front case capture faces.
    for y in (-12.5,8.8):front=front.cut(rect(-8.5,y,4,3.7))
    pad('KneeCageFrontRim',front,(-36.8+dx,0,0),(1,0,0),1.2)
    # Removable rear case lock, held by through screws and separate nuts.
    # Case insertion is from the large rear window before fitting this lock.
    rear=-9.6+dx
    for side in (-1,1):
        pad('KneeLockBoltBoss'+('L' if side==1 else 'R'),
            disk(-15,side*12.8,2.5).cut(disk(-15,side*12.8,1.1)),
            (rear-3.6,0,0),(1,0,0),4.8)
    case_clearances(b,body,routes)
    def source_pad(src,name,face,z,length,reverse=False):
        old=src.Tip;sk=sketch_face(b.doc,src,name+'Profile',face,z)
        p=src.newObject('PartDesign::Pad',name);p.Profile=sk;p.Length=length;p.Reversed=reverse
        b.doc.recompute();sk.Visibility=False
        if old:old.Visibility=False
        return p
    lock=b.doc.addObject('PartDesign::Body','KNEE_r05_REMOVABLE_REAR_LOCK')
    cc.metadata(lock,lock.Name,'PA12','ASSUMED case-face lock with M2 through bolts; exact case datum/access/load unverified')
    f=rect(-15.3,13,30.6,4)
    for y in (-12.8,12.8):f=f.cut(disk(y,15,1.1))
    source_pad(lock,'KneeRearLockPlate',f,0,1.2)
    source_pad(lock,'KneeRearLockContactRib',rect(-8,14,16,2),0,1.2,True)
    bolt=b.ring('KNEE_r05_M2_CORE_D1p65_L8p8',1.65,0,8.8)
    source_pad(bolt,'KneeBoltHead',disk(0,0,1.75),8.8,1.6)
    # Hex socket provides an explicit driver access feature.
    import Part
    old=bolt.Tip
    hp=[V((1.5/math.sqrt(3))*math.cos(i*math.pi/3),(1.5/math.sqrt(3))*math.sin(i*math.pi/3),0) for i in range(6)]
    hs=sketch_face(b.doc,bolt,'KneeBoltHexSocketProfile',Part.Face(Part.makePolygon(hp+[hp[0]])),10.4)
    hc=bolt.newObject('PartDesign::Pocket','KneeBoltHexSocket');hc.Profile=hs;hc.Length=.8
    b.doc.recompute();hs.Visibility=False;old.Visibility=False
    # Hex nut has an explicit minor bore; cosmetic threads are omitted.
    nut=b.doc.addObject('PartDesign::Body','KNEE_r05_M2_HEX_NUT_AF4_T2p8')
    cc.metadata(nut,nut.Name,'steel','ASSUMED M2 nut envelope/minor bore; supplier thread/strength unverified',role='HARDWARE')
    pts=[V((4/math.sqrt(3))*math.cos(i*math.pi/3),(4/math.sqrt(3))*math.sin(i*math.pi/3),0) for i in range(6)]
    nf=Part.Face(Part.makePolygon(pts+[pts[0]])).cut(disk(0,0,.85))
    source_pad(nut,'KneeNutPad',nf,0,2.8)
    for src in (lock,nut):b.library.addObject(src);b.sources[src.Name]=src
    tf,tv=_transformers(transform)
    rotation=App.Rotation(V(*tv((0,1,0))),V(*tv((0,0,1))),V(*tv((1,0,0))),'ZXY')
    localrot=App.Rotation(V(0,1,0),V(0,0,1),V(1,0,0),'ZXY')
    def add(src,name,origin):
        desc={'kind':'torso_r04_rigid','torso':'hind','local_placement_json':json.dumps({'base_xyz_mm':origin,'rotation_xyzw':tuple(localrot.Q)})}
        b.add(src,name,App.Placement(V(*tf(origin)),rotation),'Tendons',desc)
    add(lock,'HindTendon_RearCaseLock',(rear+1.2,0,0))
    for side in (-1,1):
        label='L' if side==1 else 'R'
        add(bolt,'HindTendon_CaseLockBolt'+label,(rear-6.4,side*12.8,15))
        add(nut,'HindTendon_CaseLockNut'+label,(rear-6.4,side*12.8,15))
    # Two fixed guide support trees, routed above/behind the proximal drive.
    # Each body is fused into the torso; support dimensions are not source facts.
    for side in (-1,1):
        label='L' if side==1 else 'R'
        P=(-31,side*42.6,10.5);Q=(-31,side*55.2,10.5)
        rod('GuideBridge'+label,P,Q,1.2)
        rod('HipGuideRearPost'+label,Q,(-31,side*55.2,0),1.2)
        for name in ('shell_guide','hip_guide'):
            q=routes[side][name];C=q['center'];a=q['axis']
            if a[1]*side<0:a=tuple(-v for v in a)
            back=tuple(c-1.8*v for c,v in zip(C,a))
            mid=tuple(c-1.25*v for c,v in zip(C,a))
            # Approach the hub radially from behind, outside the cable arc.
            radial=(-1,0,0) if name=='hip_guide' else (0,1 if side==1 else -1,0)
            dot=sum(x*y for x,y in zip(radial,a))
            radial=tuple(x-dot*y for x,y in zip(radial,a));n=math.sqrt(sum(x*x for x in radial));radial=tuple(x/n for x in radial)
            edge=tuple(c-2.0*v+2.3*r for c,v,r in zip(C,a,radial))
            start=(-31,side*55.2,0) if name=='hip_guide' else Q
            rod('GuideStrut'+label+name,start,edge,.6)
            # Hub is connected radially; the approach clears its headed journal.
            pad('GuideJournalBoss'+label+name,disk(0,0,2.5).cut(disk(0,0,.975)),back,a,1.1)
    body.addProperty('App::PropertyString','TendonMountProvenance','Tendon')
    body.TendonMountProvenance='DESIGN_ASSUMPTION integral case cage and guide supports; removable rear lock; case datum/fits/access/load unverified'
    b.doc.recompute()
    return body
