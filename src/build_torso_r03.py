"""Monolithic native torso cages, positively located by both E and D.
All unreported geometry is a candidate engineering assumption.
"""
import FreeCAD as App,Part,Sketcher,math,json
import cad_common as cc
from refine_flexor import pill_face,disk,rect,sketch_face
from retain_flexor import grooves,clip_source
from kinematics import spine
V=App.Vector

def native_pad(b,body,name,face,z,length,reverse=False):
    sk=sketch_face(b.doc,body,name+'Profile',face,z)
    old=body.Tip
    pd=body.newObject('PartDesign::Pad',name);pd.Profile=sk;pd.Length=length;pd.Reversed=reverse
    b.doc.recompute();sk.Visibility=False
    if old and old!=pd:old.Visibility=False
    return pd

def torso_angle(theta,kind,p):
    i=1 if kind=='hind' else 2
    a=spine(theta,p)[f'beta{i}']-spine(0,p)[f'beta{i}']
    return math.atan2(math.sin(a),math.cos(a))

class Transform:
    def __init__(self,E,angle):self.E=E;self.angle_rad=angle
    def __call__(self,P):
        c,s=math.cos(self.angle_rad),math.sin(self.angle_rad)
        return (self.E[0]+c*P[0]-s*P[1],self.E[1]+s*P[0]+c*P[1])

def build_torso(b,kind):
    from leg_geometry_r02 import leg_geometry
    p=b.p;s=spine(0,p);i=1 if kind=='hind' else 2
    E=s[f'E{i}'];D=(s[f'D{i}'][0]-E[0],s[f'D{i}'][1]-E[1]);H=leg_geometry(kind)['H']
    angle=-math.pi/2 if kind=='hind' else 0
    def rotate(P):return (H[0]+math.cos(angle)*P[0]-math.sin(angle)*P[1],math.sin(angle)*P[0]+math.cos(angle)*P[1])
    zmin=-16 if kind=='hind' else -9
    cage=rect(-12,zmin,24,38).cut(rect(-10.4,zmin+1.6,20.8,34.8));cage.rotate(V(),V(0,0,1),math.degrees(angle));cage.translate(V(H[0],0,0))
    body=b.doc.addObject('PartDesign::Body','TORSO_'+kind.upper()+'_CAGE_r03')
    cc.metadata(body,body.Name,'PA12','SLS cage; inner E/D carrier; outboard motor cases and outer H support; provisional fits');body.Revision='r03'
    def make_cheek(suffix,z,outer=False):
        thickness=1.2 if outer else 1.6
        face=cage
        if outer and kind=='hind':face=cage.cut(rect(H[0]+20.4,-15,6,30))
        native_pad(b,body,kind+'Cage'+suffix,face,z,thickness)
        bars=[(rotate((-11.2,0)),rotate((11.2,0)),5)] if outer else [((0,0),D,5),((0,0),H,5),(D,H,5),(rotate((-11.2,0)),rotate((11.2,0)),5)]
        for j,(P,Q,W) in enumerate(bars):native_pad(b,body,kind+'Web'+suffix+str(j),pill_face(P,Q,W),z,thickness)
        sk=b.doc.addObject('Sketcher::SketchObject',kind+'OutputBores'+suffix);body.addObject(sk);sk.Placement.Base.z=z+thickness
        for P in ([H] if outer else [(0,0),D,H]):cc.circle(sk,*P,2.025)
        old=body.Tip;cut=body.newObject('PartDesign::Pocket',kind+'OutputBorePocket'+suffix);cut.Profile=sk;cut.Length=thickness
        b.doc.recompute();sk.Visibility=False;old.Visibility=False
    make_cheek('Left',0)
    sections=None
    # Rear cage uses only its rear corner ties so the central knee servo
    # fits between the two outboard hip motors, as in FigS6.
    corners=[rotate((x,z)) for x in [-11.2,11.2] for z in ([-15.2] if kind=='hind' else [-8.2,28.2])]
    for P in corners:
        f=disk(*P,.65);sections=f if sections is None else sections.fuse(f)
    native_pad(b,body,kind+'CrossTies',sections,1.6,28.8)
    make_cheek('Right',30.4)
    # Four axial corner rails surround each case, with no tube through its
    # internal output axis. The external H bearing sits in the outer face.
    allcorners=None
    for x in [-11.2,11.2]:
        for z in ([-15.2,21.2] if kind=='hind' else [-8.2,28.2]):
            f=disk(*rotate((x,z)),.65);allcorners=f if allcorners is None else allcorners.fuse(f)
    native_pad(b,body,kind+'CaseRailsLeft',allcorners,0,26,True)
    # Outer face is built forward along local +Z, meeting the rail at z=-26.
    make_cheek('OuterLeft',-27.2,True)
    native_pad(b,body,kind+'CaseRailsRight',allcorners,32,26)
    make_cheek('OuterRight',58,True)
    b.library.addObject(body);b.sources[body.Name]=body
    b.add(body,'Torso_'+kind,cc.plane_placement(E,16),'TorsoFrames',{'kind':'torso_r03','torso':kind,'local_y':16})
    clip=clip_source(b)
    for side in [-1,1]:
        for pt in [f'E{i}',f'D{i}']:
            key=pt+'_'+str(side).replace('-','_');old=b.doc.getObject(key+'_Pin')
            source=b.ring('TORSO_OUTPUT_JOURNAL_D1p9_L25p8',1.9,0,25.8);grooves(b,source,25.8)
            source.PartNumber='TORSO_OUTPUT_JOURNAL_D1p9_L25p8_GROOVED';source.Revision='r03'
            old.setLink(source);old.LinkPlacement=cc.hardware_place(s[pt],side*26.5,25.8)
            if old.Name in b.motion:b.motion[old.Name].update(y=side*26.5,length=25.8)
            for end,y in enumerate([14.1,38.9]):
                o=b.doc.getObject(key+'_Retainer'+str(end if side==1 else 1-end));o.setLink(clip);o.LinkPlacement=cc.hardware_place(s[pt],side*y,.6)
                if o.Name in b.motion:b.motion[o.Name].update(y=side*y,length=.6)
            brg=b.ring('BRG_2x4x1p2_PROVISIONAL',4,2,1.2)
            b.add(brg,key+'_TorsoBearing',cc.hardware_place(s[pt],side*15.2,1.2),'SpineHardware',
                  {'kind':'point','point':pt,'y':side*15.2,'length':1.2} if pt.startswith('D') else None)
            hi=35.4 if pt.startswith('D') else 27.0;lo=16.0;gap=hi-lo
            src=b.ring('TORSO_OUTPUT_SPACER_L'+str(round(gap,1)),3,2.05,gap)
            b.add(src,key+'_TorsoSpacer',cc.hardware_place(s[pt],side*(lo+hi)/2,gap),'SpineHardware',
                  {'kind':'point','point':pt,'y':side*(lo+hi)/2,'length':gap} if pt.startswith('D') else None)
        name='Link'+str(i)+'_L6_'+str(side).replace('-','_');old=b.doc.getObject(name)
        if old:b.motion.pop(old.Name,None);b.doc.removeObject(old.Name)
    pn='ENV_XC330_M181_'+kind.upper()+'_DATUM_r03'
    if pn not in b.sources:
        src=cc.simple_shape(b.doc,pn,Part.makeBox(20,26,34,V(-10,-13,-14 if kind=='hind' else -7)),'motor','manufacturer envelope; output/mount datum UNVERIFIED',role='PURCHASED')
        src.PartNumber='DYNAMIXEL_XC330_M181_T';src.Revision='r03';src.addProperty('App::PropertyFloat','PurchasedMass_g');src.PurchasedMass_g=p['XC_mass_g'];b.library.addObject(src);b.sources[pn]=src
    for side in [-1,1]:
        b.add(b.sources[pn],kind+'_ProximalMotor_'+str(side),App.Placement(V(E[0]+H[0],side*29,0),App.Rotation(V(0,-1,0),math.degrees(angle))),'Actuators',
              {'kind':'torso_offset_r03','torso':kind,'point':H,'y':side*29,'angle':angle})
    return Transform(E,0)
